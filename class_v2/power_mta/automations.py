import time
import os.path
import typing
import json
import public
import threading
import logging
from power_mta.maillog_stat import query_maillog_with_time_section, last_maillog_time
from public.regexplib import match_email


class Trigger:
    # 触发器类型
    TYPE_SUBSCRIBER_ADDED = 'subscriber_added'
    TYPE_SUBSCRIBED = 'subscribed'
    TYPE_OPENED = 'opened'
    TYPE_CLICKED = 'clicked'
    TYPE_UNSUBSCRIBED = 'unsubscribed'

    __slots__ = ['type', '__attributes']

    def __init__(self, trigger_dict: typing.Dict):
        self.__attributes: typing.Dict = {}

        for k, v in trigger_dict.items():
            if k.startswith('_'):
                continue

            if k in self.__slots__:
                self.__setattr__(k, v)
                continue

            self.__attributes[k] = v

    def get_attribute(self, attribute: typing.Optional[str] = None, default: typing.Any = None):
        # 返回所有attribute
        if attribute is None:
            return self.__attributes

        return self.__attributes.get(attribute, default)

    def to_dict(self):
        d = {}

        for k in self.__slots__:
            if not hasattr(self, k) or k.startswith('_'):
                continue

            d[k] = getattr(self, k)

        d.update(self.__attributes)

        return d


class Triggers:
    __slots__ = ['triggers']

    def __init__(self, triggers: typing.List[typing.Dict]):
        self.triggers: typing.List[Trigger] = []

        for trigger_dict in triggers:
            self.triggers.append(Trigger(trigger_dict))

    def match(self, trigger_type: str, group_ids: typing.Union[int, typing.List[int]] = 0) -> bool:
        trigger_type = trigger_type.strip()
        for trigger in self.triggers:
            if trigger.type == trigger_type:
                if trigger_type in (Trigger.TYPE_SUBSCRIBED, Trigger.TYPE_SUBSCRIBER_ADDED):
                    if group_ids == 0:
                        return True

                    if isinstance(group_ids, (int, str)):
                        group_ids = [int(group_ids)]

                    for group_id in group_ids:
                        if int(group_id) in trigger.get_attribute('group_ids', []):
                            return True

                    continue

                return True
        return False

    def complete_check(self) -> bool:
        for trigger in self.triggers:
            if trigger.type in (Trigger.TYPE_SUBSCRIBED, Trigger.TYPE_SUBSCRIBER_ADDED):
                # 检查订阅触发器
                if len(trigger.get_attribute('group_ids', [])) == 0:
                    return False
            elif trigger.type == Trigger.TYPE_OPENED:
                # 检查打开邮件触发器
                pass
            elif trigger.type == Trigger.TYPE_CLICKED:
                # 检查点击邮件触发器
                pass
            elif trigger.type == Trigger.TYPE_UNSUBSCRIBED:
                # 检查取消订阅触发器
                pass

        return True

    def to_list(self):
        return list(map(lambda x: x.to_dict(), self.triggers))

    def json_dumps(self):
        return json.dumps(self.to_list())


class Node:
    TYPE_DELAY = 'delay'
    TYPE_EMAIL = 'email'
    TYPE_CONDITION = 'condition'
    TYPE_ACTION = 'action'
    TYPE_WEBHOOK = 'webhook'
    TYPE_ABTEST = 'abtest'

    CONDITION_LOGIC_AND = 'and'
    CONDITION_LOGIC_OR = 'or'

    CONDITION_BRANCH_YES = 'yes'
    CONDITION_BRANCH_NO = 'no'

    DELAY_UNIT_DAYS = 'days'
    DELAY_UNIT_HOURS = 'hours'
    DELAY_UNIT_MINUTES = 'minutes'
    DELAY_UNIT_SECONDS = 'seconds'

    ACTION_ADD_TO_SUBSCRIBERS = 'add_to_subscribers'
    ACTION_REMOVE_FROM_SUBSCRIBERS = 'remove_from_subscribers'
    ACTION_MARK_AS_UNSUBSCRIBE = 'mark_as_unsubscribe'
    ACTION_MOVE_TO_STEP = 'move_to_step'

    __slots__ = ['id', 'parent_id', 'broken', 'complete', 'type', 'attributes', 'create_time', 'update_time',
                 '__attributes', '__next', '__yes', '__no', '__branches']

    __int_bool_converts = ('complete', 'broken')

    __ignore_props = ('id',)

    def __init__(self, node_dict: typing.Dict, parent_id: int = -1):
        self.id = node_dict.get('id', 0)
        self.parent_id = 0

        if self.id == 0:
            self.id = public.snow_flake()

        self.type = ''
        self.complete = False
        self.broken = False
        self.__attributes: typing.Dict = {}
        self.__next: typing.Optional[Node] = None
        self.__yes: typing.Optional[Node] = None
        self.__no: typing.Optional[Node] = None
        self.__branches: typing.List[Node] = []

        for k, v in node_dict.items():
            if k.startswith('_') or k in self.__ignore_props:
                continue

            if k == 'next':
                if isinstance(v, dict):
                    self.set_next(Node(v, self.id))

                continue

            if k in (self.CONDITION_BRANCH_YES, self.CONDITION_BRANCH_NO) and isinstance(v, dict):
                v['condition_branch'] = k
                self.set_next(Node(v, self.id))
                continue

            if k in self.__slots__:
                if k in self.__int_bool_converts:
                    v = bool(v)
                self.__setattr__(k, v)
                continue

            self.__attributes[k] = v

        if parent_id > -1:
            self.parent_id = parent_id

        if hasattr(self, 'attributes'):
            try:
                m = json.loads(self.attributes)
                if isinstance(m, dict):
                    m.update(self.__attributes)
                    self.__attributes = m
            except:
                pass

        self.attributes = json.dumps(self.__attributes, ensure_ascii=False)

        self.complete_check()
        self.broken_check()

        cur_time = int(time.time())

        self.update_time = cur_time

        if not hasattr(self, 'create_time'):
            self.create_time = cur_time

    def to_tree_dict(self):
        root = {}

        for k in self.__slots__:
            if not hasattr(self, k) or k.startswith('_') or k == 'attributes':
                continue

            root[k] = getattr(self, k)

        for k, v in self.get_attribute().items():
            root[k] = v

        if self.type == self.TYPE_CONDITION:
            if isinstance(self.__yes, Node):
                root['yes'] = self.__yes.to_tree_dict()

            if isinstance(self.__no, Node):
                root['no'] = self.__no.to_tree_dict()
        elif self.type == self.TYPE_ABTEST:
            root['branches'] = []
            for branch in self.__branches:
                root['branches'].append(branch.to_tree_dict())

        root['next'] = None if self.next() is None else self.next().to_tree_dict()

        return root

    def next(self, attribute_or_index: typing.Optional[typing.Union[str, int]] = None, default: typing.Any = None):
        if attribute_or_index is not None:
            if isinstance(attribute_or_index, str):
                if attribute_or_index == 'yes':
                    return self.__yes
                elif attribute_or_index == 'no':
                    return self.__no
                elif attribute_or_index == 'branches':
                    return self.__branches

                return default
            elif isinstance(attribute_or_index, int):
                return self.__branches[attribute_or_index]

        return self.__next

    def set_next(self, node):
        if self.type == self.TYPE_CONDITION:

            if node.get_attribute('condition_branch') == self.CONDITION_BRANCH_YES:
                self.__yes = node
            elif node.get_attribute('condition_branch') == self.CONDITION_BRANCH_NO:
                self.__no = node

            return

        if self.type == self.TYPE_ABTEST:
            pass

        self.__next = node

    def get_attribute(self, attribute: typing.Optional[str] = None, default: typing.Any = None):
        # 返回所有attribute
        if attribute is None:
            return self.__attributes

        return self.__attributes.get(attribute, default)

    def set_attribute(self, name: str, value: typing.Any):
        self.__attributes[name] = value
        self.attributes = json.dumps(self.__attributes, ensure_ascii=False)
        return self

    def to_dict(self):
        d = {}

        for k in self.__slots__:
            if not hasattr(self, k) or k.startswith('_'):
                continue

            d[k] = getattr(self, k)

        return d

    def complete_check(self):
        if self.type == self.TYPE_DELAY:
            self.complete = self.get_attribute('value', 0) > 0 and self.get_attribute('unit', '') in ('days', 'hours', 'minutes', 'seconds')
        elif self.type == self.TYPE_EMAIL:
            try:
                public.to_dict_obj(self.get_attribute()).validate([
                    public.Param('email_id').Require().Integer('>', 0),
                    public.Param('campaign_id').Require().Integer('>', 0),
                    public.Param('name').Require().string('>', 0),
                    public.Param('subject').Require().string('>', 0),
                    public.Param('from').Require().Email(),
                    public.Param('get_attribute').Require().String('>', 0),
                ])
            except:
                return

            self.complete = True
        elif self.type == self.TYPE_CONDITION:
            self.complete = len(self.get_attribute('rules', [])) > 0
        elif self.type == self.TYPE_ACTION:
            self.complete = self.get_attribute('action', '') != ''
        elif self.type == self.TYPE_WEBHOOK:
            try:
                public.to_dict_obj(self.get_attribute()).validate([
                    public.Param('url').Require().Url(),
                    public.Param('secret').Require().string('>', 0),
                ])
            except:
                return

            self.complete = True
        elif self.type == self.TYPE_ABTEST:
            self.complete = self.get_attribute('name', '') != '' and len(self.get_attribute('branches', [])) > 0

    def broken_check(self):
        return

    def base_validate(self):
        # node转换成dict_obj对象，方便校验数据结构
        node_obj = public.to_dict_obj(self.to_dict())

        # node基本数据结构验证
        node_obj.validate([
            public.Param('id').Filter(int),
            public.Param('parent_id').Filter(int),
            public.Param('type').Require().String('in', [Node.TYPE_DELAY, Node.TYPE_EMAIL, Node.TYPE_CONDITION, Node.TYPE_ACTION, Node.TYPE_ABTEST, Node.TYPE_WEBHOOK]),
            public.Param('next').Require(),
            public.Param('broken').Require().Bool(),
            public.Param('complete').Require().Bool(),
        ])

        # 根据node_type再次验证专属数据结构
        if node_obj.type == Node.TYPE_EMAIL:
            # email节点数据结构验证
            node_obj.validate([
                public.Param('email_id').Filter(int),
                public.Param('campaign_id').Filter(int),
                public.Param('name').Require(),
                public.Param('subject').Require(),
                public.Param('from').Require(),
                public.Param('from_name').Require(),
                public.Param('track_opens').Require().Bool(),
                public.Param('track_clicks').Require().Bool(),
                public.Param('track_unsubscribe').Require().Bool(),
            ])
        elif node_obj.type == Node.TYPE_DELAY:
            # delay节点数据结构验证
            node_obj.validate([
                public.Param('value').Require().Filter(int),
                public.Param('unit').Require().String('in', [Node.DELAY_UNIT_DAYS, Node.DELAY_UNIT_HOURS, Node.DELAY_UNIT_MINUTES, Node.DELAY_UNIT_SECONDS]),
                public.Param('description').Require(),
            ])
        elif node_obj.type == Node.TYPE_CONDITION:
            # condition节点数据结构验证
            node_obj.validate([
                public.Param('rules').Require().List(),
                public.Param('logic_type').Require().String('in', [Node.CONDITION_LOGIC_AND, Node.CONDITION_LOGIC_OR]),
                public.Param('yes').Require(),
                public.Param('no').Require(),
                public.Param('description').Require(),
            ])
        elif node_obj.type == Node.TYPE_WEBHOOK:
            # webhook节点数据结构验证
            node_obj.validate([
                public.Param('url').Require(),
                public.Param('secret').Require(),
            ])
        elif node_obj.type == Node.TYPE_ACTION:
            # action节点数据结构验证
            node_obj.validate([
                public.Param('action').Require(),
                public.Param('group_ids').Require().List(),
                public.Param('groups').List(),
                public.Param('description').Require(),
            ])
        elif node_obj.type == Node.TYPE_ABTEST:
            # abtest节点数据结构验证
            node_obj.validate([
                public.Param('name').Require(),
                public.Param('branches').Require().List(),
            ])
        elif node_obj.get('abtestbranch', False):
            # abtestfbranch节点数据结构验证
            node_obj.validate([
                public.Param('label').Require(),
                public.Param('path').Require().String('in', ['a', 'b', 'c']),
                public.Param('percentage').Require().Integer('between', [1, 100]),
            ])
        else:
            raise public.HintException(public.lang('Invalid node type: {}', self.type))


class ConditionRule:
    TYPE_CAMPAIGN = 'campaign'
    TYPE_WORKFLOW = 'workflow'
    TYPE_RECIPIENT = 'recipient'

    __slots__ = ['type', 'action', '__attributes']

    def __init__(self, condition_rule_dict: typing.Dict):
        self.type = ''
        self.action = ''
        self.__attributes: typing.Dict = {}

        for k, v in condition_rule_dict.items():
            if k.startswith('_'):
                continue

            if k in self.__slots__:
                self.__setattr__(k, v)
                continue

            self.__attributes[k] = v

    def get_attribute(self, attribute: typing.Optional[str] = None, default: typing.Any = None):
        # 返回所有attribute
        if attribute is None:
            return self.__attributes

        return self.__attributes.get(attribute, default)


class ConditionRules:
    __slots__ = ['rules', 'logic']

    def __init__(self, rules: typing.List[typing.Dict], logic: str = Node.CONDITION_LOGIC_AND):
        self.rules: typing.List[ConditionRule] = []
        self.logic: str = logic

        for rule_dict in rules:
            self.rules.append(ConditionRule(rule_dict))

    def match(self) -> bool:
        for rule in self.rules:
            if rule.type in (ConditionRule.TYPE_CAMPAIGN, ConditionRule.TYPE_WORKFLOW):
                continue

            if rule.type == ConditionRule.TYPE_RECIPIENT:
                continue

            return False

        return True


class Workflow:

    __db_path = '/www/vmail/mail_automation_workflows'

    def __init__(self, automation_id: int):
        self.__automation_id = automation_id
        self.__create_tables()

    def __create_tables(self):
        if not os.path.exists(self.__db_path):
            os.makedirs(self.__db_path, 0o700)

        with public.S(None, '{}/workflow_{}'.format(self.__db_path, self.__automation_id)) as query:
            query.execute_script('''-- 开启wal模式
PRAGMA journal_mode = wal;

-- 关闭同步
PRAGMA synchronous = 0;

-- 开启事务
begin;

-- 节点表
create table if not exists `nodes` (
    `id` integer primary key,
    `parent_id` integer not null default 0,
    `broken` integer not null default 0,
    `complete` integer not null default 0,
    `create_time` integer not null default (strftime('%s')),
    `update_time` integer not null default (strftime('%s')),
    `type` text not null default '',
    `attributes` text not null default '{}'
);

create index if not exists `node_parentId` on `nodes` (`parent_id`);

-- 工作流程进行表
create table if not exists `schedules` (
    `id` integer primary key autoincrement,
    `node_id` integer not null default 0,
    `status` integer not null default 0,
    `create_time` integer not null default (strftime('%s')),
    `update_time` integer not null default (strftime('%s')),
    `subscriber_email` text not null default ''
);

create index if not exists `schedule_subscriberEmail_status` on `schedules` (`subscriber_email`, `status`);

-- 提交事务
commit;
''')

    def query(self, table_name: str):
        return public.S(table_name, '{}/workflow_{}'.format(self.__db_path, self.__automation_id))

    def __get_node_map(self) -> typing.Dict[int, Node]:
        with self.query('nodes') as query:
            nodes = [Node(node_dict) for node_dict in query.select()]

        node_map = {}

        for node in nodes:
            node_map[node.id] = node

        return node_map

    def load_workflow_tree(self):
        return self.build_workflow_tree(self.__get_node_map())

    def set_nodes(self, root: typing.Optional[typing.Dict]) -> typing.Optional[Node]:
        if root is None:
            # 清空节点树
            with self.query('nodes') as query:
                query.delete()

            return None

        insert_data = []
        node_map = {}

        # 解析nodes
        for node in self.walk_node(root):
            # 处理特殊节点
            if node.type == Node.TYPE_EMAIL:
                # 邮件发送任务节点
                pass
            elif node.type == Node.TYPE_CONDITION:
                # 条件分支节点
                pass
            elif node.type == Node.TYPE_ABTEST:
                # AB测试节点
                pass
            elif node.get_attribute('abtestbranch', False):
                # AB测试子节点根节点
                pass

            insert_data.append(node.to_dict())
            node_map[node.id] = node

        # 将节点数据写入数据库
        if len(insert_data) > 0:
            with self.query('nodes') as query:
                query.insert_all(insert_data, option='REPLACE')

                # 删除无效节点
                query.where_not_in('id', list(node_map.keys())).delete()

        # 生成新的节点树并返回
        return self.build_workflow_tree(node_map)

    def build_workflow_tree(self, node_map: typing.Dict[int, Node], root_id: int = 0) -> typing.Optional[Node]:
        root = None

        for node_id, node in node_map.items():
            # 检查是否root节点
            if node.parent_id == 0 or node.id == root_id:
                root = node
                continue

            if node.parent_id not in node_map:
                continue

            node_map[node.parent_id].set_next(node)

        return root

    def walk_node(self, node_or_dict: typing.Union[typing.Dict, Node], p_node: typing.Optional[Node] = None):
        # node_dict转换成Node对象，方便校验数据结构
        if isinstance(node_or_dict, Node):
            node = node_or_dict
        else:
            node = Node(node_or_dict, p_node.id if p_node is not None else 0)

        # 返回节点信息
        yield node

        # 处理特殊节点
        if node.type == Node.TYPE_CONDITION:
            if node.next('yes'):
                yield from self.walk_node(node.next('yes'), node)
            if node.next('no'):
                yield from self.walk_node(node.next('no'), node)
        elif node.type == Node.TYPE_ABTEST:
            for abtestbranch in node.next('branches', []):
                yield from self.walk_node(abtestbranch, node)

        if node.next():
            yield from self.walk_node(node.next(), node)

    def walk_node_for_schedule(self, root_id: int = 0):
        with self.query('nodes') as query:
            query.where('parent_id', root_id)

            if root_id > 0:
                query.where_or('id', root_id)

            nodes = [Node(node_dict) for node_dict in query.select()]

        if len(nodes) == 0:
            return

        # 生成新的节点树并返回
        workflow_tree = self.build_workflow_tree({node.id: node for node in nodes}, root_id)

        if workflow_tree is None:
            return

        yield from self.walk_node(workflow_tree)

    def walk_node_with_database(self):
        yield from self.walk_node(self.load_workflow_tree())


class Automation:

    __db_path = '/www/vmail'

    def __init__(self):
        self.__IS_INIT = False
        self.__create_tables()

    def is_init(self) -> bool:
        self.__create_tables()
        return self.__IS_INIT

    def __create_tables(self):
        if self.__IS_INIT:
            return

        if not os.path.exists(self.__db_path):
            return

        self.__IS_INIT = True

        with self.query() as query:
            query.execute_script('''-- 开启wal模式
PRAGMA journal_mode = wal;

-- 关闭同步
PRAGMA synchronous = 0;

-- 开启事务
begin;

-- 任务表
create table if not exists `automations` (
    `id` integer primary key autoincrement,
    `status` integer not null default 0,
    `sent` integer not null default 0,
    `delivered` integer not null default 0,
    `opened` integer not null default 0,
    `clicked` integer not null default 0,
    `create_time` integer not null default (strftime('%s')),
    `update_time` integer not null default (strftime('%s')),
    `last_stat_time` integer not null default 0,
    `name` text not null default '',
    `triggers` text not null default '[]'
);

-- 提交事务
commit;
''')

    def query(self):
        self.__create_tables()
        return public.S('automations', '{}/automations'.format(self.__db_path))

    # 获取自动化任务列表
    def get_tasks(self, args: public.dict_obj):
        args.validate([
            public.Param('p').Integer('>', 0),
            public.Param('p_size').Integer('>', 0),
            public.Param('keyword').Xss(),
        ])

        with self.query() as query:
            query.where_in('status', [0, 1])\
                .field('id', 'status', 'name', 'create_time', 'update_time', 'sent', 'delivered', 'ifnull(round(1.0 * opened / sent * 100, 2), 0) as `opened`', 'ifnull(round(1.0 * clicked / sent * 100, 2), 0) as `clicked`')

            if 'keyword' in args and args.keyword != '':
                query.where('`name` like ?', '%{}%'.format(args.keyword))

            ret = {
                'total': query.fork().count(),
                'list': query.order('id', 'desc').skip((args.get('p', 1) - 1) * args.get('p_size', 20)).limit(args.get('p_size', 20)).select(),
            }

        return ret

    # 创建/编辑邮件自动化任务
    def set(self, args: public.dict_obj):
        args.validate([
            public.Param('id').Integer('>', 0),
            public.Param('name').String('>', 0),
            public.Param('triggers').Require().List(),
            public.Param('root').Require(),
        ])

        triggers = Triggers(args.triggers)

        with self.query() as query:
            if 'id' in args:
                automation_id = args.id

                if not query.where('id', automation_id).exists():
                    raise public.HintException(public.lang('Invalid automation'))

                if query.where('id', automation_id).where('status', 1).exists():
                    raise public.HintException(public.lang('Cannot edit automation in running state.'))

                update_data = {
                    'triggers': triggers.json_dumps(),
                }

                if 'name' in args:
                    update_data['name'] = args.name

                query.where('id', automation_id).update(update_data)
            else:
                insert_data = {
                    'triggers': triggers.json_dumps(),
                }

                if 'name' in args:
                    insert_data['name'] = args.name

                automation_id = query.insert(insert_data)

        wf = Workflow(automation_id)

        root = wf.set_nodes(args.root)

        return {
            'id': automation_id,
            'triggers': triggers.to_list(),
            'root': root.to_tree_dict() if root is not None else None,
        }

    # 更新任务名称
    def set_name(self, args: public.dict_obj):
        args.validate([
            public.Param('id').Require().Integer('>', 0),
            public.Param('name').Require().String('>', 0),
        ])

        with self.query() as query:
            query.where('id', args.id).update({
                'name': args.name
            })

        return public.lang('Success')

    # 获取节点树
    def get_workflow(self, args: public.dict_obj):
        args.validate([
            public.Param('id').Require().Integer('>', 0),
        ])

        with self.query() as query:
            triggers_str = query.where('id', args.id).value('triggers')

            if triggers_str is None:
                raise public.HintException(public.lang('Invalid automation_id: {}', args.id))

            try:
                triggers = Triggers(json.loads(triggers_str))
            except:
                raise public.HintException(public.lang('Invalid automation: failed to load triggers'))

        wf = Workflow(args.id)

        return {
            'id': args.id,
            'triggers': triggers.to_list(),
            'root': wf.load_workflow_tree().to_tree_dict(),
        }

    # 启停邮件自动化任务
    def set_status(self, args: public.dict_obj):
        args.validate([
            public.Param('id').Require().Integer('>', 0),
            public.Param('status').Require().Integer('in', [0, 1]),
        ])

        # 启动任务时检查所有节点是否配置
        if args.status == 1:
            # 检查triggers是否配置
            with self.query() as query:
                try:
                    triggers = Triggers(json.loads(query.where('id', args.id).value('triggers')))
                except:
                    raise public.HintException(public.lang('Invalid automation: failed to load triggers'))

            if not triggers.complete_check():
                raise public.HintException(public.lang('Invalid automation: incomplete triggers'))

            task = Task()
            wf = Workflow(args.id)
            for node in wf.walk_node_with_database():
                if not node.complete:
                    raise public.HintException(public.lang('You must complete workflow'))

                # 为Email节点创建邮件任务
                if node.type == Node.TYPE_EMAIL:
                    # 更新邮件任务
                    node.set_attribute('campaign_id', task.set_email_campaign(node))
                    with wf.query('nodes') as query:
                        query.where('id', node.id).update(node.to_dict())

        with self.query() as query:
            query.where('id', args.id).update({
                'status': args.status,
            })

        return public.lang('Success')

    # 删除邮件自动化任务
    def remove(self, args: public.dict_obj):
        args.validate([
            public.Param('id').Require().Integer('>', 0),
        ])

        with self.query() as query:
            # 标记软删除
            query.where('id', args.id).update({
                'status': 2,
            })

        return public.lang('Success')


class ScheduleNode:
    STATUS_WAITING = 0
    STATUS_PROCESSING = 1
    STATUS_COMPLETED = 2
    STATUS_BROKEN = 3

    __slots__ = ['id', 'node_id', 'status', 'subscriber_email', 'update_time']

    def __init__(self, node_dict: typing.Dict):
        self.id = 0
        self.node_id = 0
        self.status = self.STATUS_WAITING
        self.subscriber_email = ''

        for k in self.__slots__:
            if k not in node_dict:
                continue

            self.__setattr__(k, node_dict[k])

        if not hasattr(self, 'update_time'):
            self.update_time = int(time.time())

    def to_dict(self):
        d = {}

        for k in self.__slots__:
            if not hasattr(self, k) or k.startswith('_'):
                continue

            d[k] = getattr(self, k)

        return d


class Scheduler:
    def __init__(self, automation_id: int):
        # 参数格式验证
        public.to_dict_obj({
            'automation_id': automation_id,
        }).validate([
            public.Param('automation_id').Integer('>', 0),
        ])

        self.automation_id: int = automation_id
        self.automation: Automation = Automation()
        self.workflow: Workflow = Workflow(automation_id)

    def schedule(self, subscriber: typing.Optional[str] = None):
        if subscriber is None:
            self.__schedule_all()
            return

        # 参数格式验证
        public.to_dict_obj({
            'subscriber': subscriber
        }).validate([
            public.Param('subscriber').Email(),
        ])

        with self.workflow.query('schedules') as query:
            schedule_node = query.where('subscriber_email', subscriber)\
                .order('id', 'desc')\
                .field('id', 'node_id', 'subscriber_email', 'status', 'update_time')\
                .find()

        cur_time = int(time.time())

        # 任务首次调度
        if schedule_node is None:
            schedule_node = ScheduleNode({
                'id': 0,
                'node_id': 0,
                'subscriber_email': subscriber,
                'status': ScheduleNode.STATUS_WAITING,
                'update_time': cur_time,
            })
        else:
            schedule_node = ScheduleNode(schedule_node)

        self.__schedule_one(schedule_node, cur_time)

    def schedule_async(self, subscriber: typing.Union[str, typing.List[str]]):
        if isinstance(subscriber, str):
            subscriber = [subscriber]

        # 过滤邮件
        subscriber = list(filter(lambda x: match_email.match(x), subscriber))

        if len(subscriber) == 0:
            return

        cur_time = int(time.time())

        with self.workflow.query('schedules') as query:
            exists_emails = query.where_in('subscriber_email', subscriber).field('distinct `subscriber_email`').column('subscriber_email')

            insert_data = []

            for email in subscriber:
                if email in exists_emails:
                    continue

                insert_data.append({
                    'node_id': 0,
                    'status': ScheduleNode.STATUS_WAITING,
                    'subscriber_email': email,
                    'create_time': cur_time,
                    'update_time': cur_time,
                })

            if len(insert_data) > 0:
                query.insert_all(insert_data)

    def schedule_email_sending(self):
        cur_time = int(time.time())

        # Add timeout threshold for stuck processing tasks (e.g., 1 hour)
        processing_timeout = 120

        for node in self.workflow.walk_node_with_database():
            if node.type not in (Node.TYPE_EMAIL,):
                continue

            logging.debug('schedule node: {} {}'.format(node.id, node.get_attribute('campaign_id', 0)))

            with self.workflow.query('schedules') as query:
                schedules = query.where('node_id', node.id).where_in('status', [
                ScheduleNode.STATUS_WAITING,
                ScheduleNode.STATUS_PROCESSING
            ]).field('id', 'subscriber_email', 'status', 'update_time').select()

            if len(schedules) == 0:
                continue

            campaign_id = int(node.get_attribute('campaign_id', 0))
            schedule_ids = set()
            emails = set()

            for schedule in schedules:
                # Only process waiting tasks and stuck processing tasks
                if schedule['status'] == ScheduleNode.STATUS_PROCESSING and (
                        cur_time - schedule['update_time'] < processing_timeout):
                    continue  # Skip tasks that are still being processed within timeout

                schedule_ids.add(schedule['id'])
                emails.add(schedule['subscriber_email'])

            if len(schedule_ids) == 0:
                continue

            if campaign_id < 1:
                query.where_in('id', list(schedule_ids)).update({
                    'status': ScheduleNode.STATUS_BROKEN,
                    'update_time': cur_time,
                })
                continue

            with public.S('email_task', '/www/vmail/postfixadmin') as query:
                if not query.where('id', campaign_id).where('type', 1).exists():
                    with self.workflow.query('scheduels') as query2:
                        query2.where_in('id', list(schedule_ids)).update({
                            'status': ScheduleNode.STATUS_BROKEN,
                            'update_time': cur_time,
                        })
                        continue

                campaign = query.where('id', campaign_id).where('type', 1).field(
                    'task_process').find()

                # 邮件任务执行中，等待一次调度
                if int(campaign['task_process']) == 1:
                    continue

                recipient_file = '{}/data/mail/in_bulk/recipient/{}_verify_{}'.format(public.get_panel_path(),
                                                                                      public.Md5(str(node.id)),
                                                                                      campaign_id)

                recipient_dict = {
                    'gmail.com': {"count": 0, "info": list(emails)},
                    'googlemail.com': {"count": 0, "info": []},
                    'hotmail.com': {"count": 0, "info": []},
                    'outlook.com': {"count": 0, "info": []},
                    'yahoo.com': {"count": 0, "info": []},
                    'icloud.com': {"count": 0, "info": []},
                    'other': {"count": 0, "info": []},
                }

                with open(recipient_file, 'w') as fp:
                    fp.write(json.dumps(recipient_dict))

                query.where('id', campaign_id).update({
                    'task_process': 0,
                    'recipient': recipient_file,
                })

            db_dir = '/www/vmail/bulk'
            db_path = '{}/task_{}.db'.format(db_dir, campaign_id)

            if os.path.exists(db_path):
                insert_data = []

                for email in emails:
                    insert_data.append({
                        'recipient': email,
                        'is_sent': 0,
                        'mail_provider': email.split('@')[1],
                        'sent_time': 0,
                        'created': cur_time,
                    })

                with public.S('recipient_info', db_path) as query:
                    query.insert_all(insert_data, option='IGNORE')

            logging.debug('sending emails with automation: {}'.format(list(emails)))

            with self.workflow.query('schedules') as query:
                query.where_in('id', list(schedule_ids)).update({
                    'status': ScheduleNode.STATUS_PROCESSING,
                    'update_time': cur_time,
                })

            ret = public.run_plugin('mail_sys', 'check_task_status_new', public.to_dict_obj({
                'task_id': node.get_attribute('campaign_id', 0),
            }))

            logging.debug(ret)

            if not isinstance(ret, dict):
                logging.debug('check_task_status_new failed: {}'.format(ret))
                continue

            with self.workflow.query('schedules') as query:
                query.where_in('id', list(schedule_ids)).update({
                    'status': ScheduleNode.STATUS_COMPLETED,
                    'update_time': cur_time,
                })

    def sync_maillog_stat(self):
        logging.debug('sync automation-{} maillog statistics'.format(self.automation_id))

        cur_time = int(time.time())

        with self.automation.query() as query:
            last_stat_time = query.where('id', self.automation_id).value('case when `last_stat_time` > 0 then `last_stat_time` else `create_time` end as `last_stat_time`')

        start_time = int(last_stat_time)
        end_time = cur_time
        msgids = set()

        msgid_sent_file = '{}/data/mail/in_bulk/recipient/sent_recipient/msgid_{}.sent'.format(public.get_panel_path(), self.automation_id)
        msgid_sent_set = set()

        if os.path.exists(msgid_sent_file):
            with open(msgid_sent_file, 'r') as fp:
                for msgid in fp:
                    msgid = msgid.strip().strip('<>')
                    if msgid == '':
                        continue
                    msgid_sent_set.add(msgid)

        msgid_opened_file = '{}/data/mail/in_bulk/recipient/sent_recipient/msgid_{}.opened'.format(public.get_panel_path(), self.automation_id)
        msgid_opened_set = set()

        if os.path.exists(msgid_opened_file):
            with open(msgid_opened_file, 'r') as fp:
                for msgid in fp:
                    msgid = msgid.strip().strip('<>')
                    if msgid == '':
                        continue
                    msgid_opened_set.add(msgid)

        msgid_clicked_file = '{}/data/mail/in_bulk/recipient/sent_recipient/msgid_{}.clicked'.format(public.get_panel_path(), self.automation_id)
        msgid_clicked_set = set()

        if os.path.exists(msgid_clicked_file):
            with open(msgid_clicked_file, 'r') as fp:
                for msgid in fp:
                    msgid = msgid.strip().strip('<>')
                    if msgid == '':
                        continue
                    msgid_clicked_set.add(msgid)

        for node in self.workflow.walk_node_with_database():
            if node.type not in (Node.TYPE_EMAIL,):
                continue

            campaign_id = int(node.get_attribute('campaign_id', 0))
            msgid_file = '{}/data/mail/in_bulk/recipient/sent_recipient/msgid_{}.log'.format(public.get_panel_path(), campaign_id)

            if campaign_id < 1 or not os.path.exists(msgid_file):
                continue

            with open(msgid_file, 'r') as fp:
                for msgid in fp:
                    msgid = msgid.strip().strip('<>')
                    if msgid == '':
                        continue
                    msgids.add(msgid)

        # Check if there's anything new to process
        not_sent = msgids - msgid_sent_set
        not_opened = msgids - msgid_opened_set
        not_clicked = msgids - msgid_clicked_set

        if len(not_sent) + len(not_opened) + len(not_clicked) == 0:
            logging.debug('sync automation-{} maillog statistics >>> no data for update'.format(self.automation_id))
            with self.automation.query() as query:
                query.where('id', self.automation_id).update({
                    'last_stat_time': int(last_maillog_time()),
                    'update_time': cur_time,
                })
            return

        with self.automation.query() as query:
            automation_info = query.where('id', self.automation_id).field('sent', 'delivered', 'opened', 'clicked').find()

        stat_data = {
            'sent': len(msgids),
            'delivered': int(automation_info['delivered']),
            'opened': int(automation_info['opened']),
            'clicked': int(automation_info['clicked']),
            'last_stat_time': int(last_maillog_time()),
            'update_time': cur_time,
        }

        if len(not_sent) > 0:
            with public.S('message_ids') as query:
                query.alias('mi').prefix('')
                query.inner_join('send_mails sm', 'mi.postfix_message_id=sm.postfix_message_id')
                query.where('sm.log_time > ?', start_time - 1)
                query.where('sm.log_time < ?', end_time + 1)
                query.where('sm.status', 'sent')
                query.where('sm.dsn like ?', '2.%')
                query.where_in('mi.message_id', list(not_sent))
                query.field('mi.message_id')

                ret = query_maillog_with_time_section(query, start_time, end_time)

            msgid_sent_add = set()

            for item in ret:
                msgid_sent_add.add(item['message_id'])
                stat_data['delivered'] += int(item['message_id'] not in msgid_sent_set)

            if len(msgid_sent_add) > 0:
                with open(msgid_sent_file, 'a') as fp:
                    fp.write('{}\n'.format('\n'.join(msgid_sent_add)))

        if len(not_opened) > 0:
            with public.S('opened') as query:
                query.alias('o').prefix('')
                query.where('o.log_time > ?', start_time - 1)
                query.where('o.log_time < ?', end_time + 1)
                query.where_in('o.message_id', list(not_opened))
                query.group('o.message_id')
                query.field('o.message_id')

                ret = query_maillog_with_time_section(query, start_time, end_time)

            msgid_opened_add = set()

            for item in ret:
                msgid_opened_add.add(item['message_id'])
                stat_data['opened'] += int(item['message_id'] not in msgid_opened_set)

            if len(msgid_opened_add) > 0:
                with open(msgid_opened_file, 'a') as fp:
                    fp.write('{}\n'.format('\n'.join(msgid_opened_add)))

        if len(not_clicked) > 0:
            with public.S('clicked') as query:
                query.alias('c').prefix('')
                query.where('c.log_time > ?', start_time - 1)
                query.where('c.log_time < ?', end_time + 1)
                query.where_in('c.message_id', list(not_clicked))
                query.group('c.message_id')
                query.field('c.message_id')

                ret = query_maillog_with_time_section(query, start_time, end_time)

            msgid_clicked_add = set()

            for item in ret:
                msgid_clicked_add.add(item['message_id'])
                stat_data['clicked'] += int(item['message_id'] not in msgid_clicked_set)

            if len(msgid_clicked_add) > 0:
                with open(msgid_clicked_file, 'a') as fp:
                    fp.write('{}\n'.format('\n'.join(msgid_clicked_add)))

        with self.automation.query() as query:
            query.where('id', self.automation_id).update(stat_data)

        logging.debug('sync automation-{} maillog statistics >>> OK'.format(self.automation_id))

    def __schedule_one(self, schedule_node: ScheduleNode, cur_time: int = 0):
        if int(schedule_node.status) == ScheduleNode.STATUS_BROKEN:
            return

        if cur_time < 1:
            cur_time = int(time.time())

        schedule_id = int(schedule_node.id)
        root_id = int(schedule_node.node_id)

        for node in self.workflow.walk_node_for_schedule(root_id):
            # 处理当前节点
            if node.id == root_id:
                # 当前节点正在处理中，等待下一次调度
                if schedule_node.status == ScheduleNode.STATUS_PROCESSING:
                    break

                # 当前节点已处理完成，可以跳转到下一流程
                if schedule_node.status == ScheduleNode.STATUS_COMPLETED:
                    continue

                if node.type == Node.TYPE_DELAY:
                    logging.debug('schedule delay node - {} {} {}'.format(node.id, node.get_attribute('value', 0), node.get_attribute('unit', Node.DELAY_UNIT_SECONDS)))

                    # delay节点
                    seconds = int(node.get_attribute('value', 0))

                    if node.get_attribute('unit', Node.DELAY_UNIT_SECONDS) == Node.DELAY_UNIT_MINUTES:
                        seconds *= 60
                    elif node.get_attribute('unit', Node.DELAY_UNIT_SECONDS) == Node.DELAY_UNIT_HOURS:
                        seconds *= 3600
                    elif node.get_attribute('unit', Node.DELAY_UNIT_SECONDS) == Node.DELAY_UNIT_DAYS:
                        seconds *= 86400

                    # 当前任务未到可执行下一步的时间
                    if schedule_node.update_time + seconds > cur_time:
                        return

                    # 更新Delay节点已完成
                    with self.workflow.query('schedules') as query:
                        query.where('id', schedule_id).update({
                            'status': ScheduleNode.STATUS_COMPLETED,
                            'update_time': cur_time,
                        })

                    continue

            schedule_node.node_id = node.id
            schedule_node.status = ScheduleNode.STATUS_PROCESSING
            schedule_node.update_time = cur_time

            # 更新当前任务正在进行节点
            if schedule_id == 0:
                with self.workflow.query('schedules') as query:
                    schedule_id = query.insert(schedule_node.to_dict())
            else:
                with self.workflow.query('schedules') as query:
                    query.where('id', schedule_id).update(schedule_node.to_dict())

            logging.debug('schedule node: {} {} {}'.format(node.type, node.id, schedule_node.status))

            # 处理子节点
            if node.type == Node.TYPE_CONDITION:
                # Condition节点
                condition_rules = ConditionRules(node.get_attribute('rules', []),
                                                 node.get_attribute('logic_type', Node.CONDITION_LOGIC_AND))
                condition_matched = condition_rules.match()
                for sub_node in self.workflow.walk_node_for_schedule(node.id):
                    if sub_node.id == node.id:
                        continue

                    if condition_matched and node.get_attribute('condition_branch', '') == Node.CONDITION_BRANCH_YES:
                        # Yes分支
                        # 更新当前任务正在进行节点
                        with self.workflow.query('schedules') as query:
                            query.where('id', schedule_id).update({
                                'node_id': sub_node.id,
                                'status': ScheduleNode.STATUS_WAITING,
                                'update_time': cur_time,
                            })
                        break

                    if not condition_matched and node.get_attribute('condition_branch', '') == Node.CONDITION_BRANCH_NO:
                        # No分支
                        # 更新当前任务正在进行节点
                        with self.workflow.query('schedules') as query:
                            query.where('id', schedule_id).update({
                                'node_id': sub_node.id,
                                'status': ScheduleNode.STATUS_WAITING,
                                'update_time': cur_time,
                            })
                        break
                break
            elif node.type == Node.TYPE_ABTEST:
                # TODO Abtest节点（留到下一次迭代）
                pass
            elif node.type == Node.TYPE_EMAIL:
                # Email节点
                if schedule_node.status in (ScheduleNode.STATUS_WAITING,):
                    break

                with self.workflow.query('schedules') as query:
                    query.where('id', schedule_id).update({
                        'status': ScheduleNode.STATUS_WAITING,
                    })

                logging.debug('update Email node status to waiting')

                # Task().send_email_with_campaign(node, schedule_node.subscriber_email)
                break
            elif node.type == Node.TYPE_WEBHOOK:
                # Webhook节点
                # 发送请求
                logging.debug('send request to {}'.format(node.get_attribute('url')))
                threading.Thread(target=public.HttpPost, args=(node.get_attribute('url'), {
                    'secret': node.get_attribute('secret', ''),
                    'subscriber': schedule_node.subscriber_email,
                })).start()
            elif node.type == Node.TYPE_ACTION:
                # Action节点
                if node.get_attribute('action', '') == Node.ACTION_ADD_TO_SUBSCRIBERS:
                    # TODO 将订阅者邮箱添加到指定用户组中
                    pass
                elif node.get_attribute('action', '') == Node.ACTION_REMOVE_FROM_SUBSCRIBERS:
                    # TODO 将订阅者邮箱从指定用户组中移除
                    pass
                elif node.get_attribute('action', '') == Node.ACTION_MARK_AS_UNSUBSCRIBE:
                    # TODO 将订阅者邮箱标记为 “已退订”
                    pass
                elif node.get_attribute('action', '') == Node.ACTION_MOVE_TO_STEP:
                    if node.get_attribute('next_node_id', 0) > 0:
                        # 更新当前任务正在进行的节点
                        with self.workflow.query('schedules') as query:
                            query.where('id', schedule_id).update({
                                'node_id': node.get_attribute('next_node_id', 0),
                                'status': ScheduleNode.STATUS_WAITING,
                                'update_time': cur_time,
                            })
                        break
            elif node.type == Node.TYPE_DELAY:
                # Delay节点
                if schedule_node.status in (ScheduleNode.STATUS_WAITING,):
                    break

                with self.workflow.query('schedules') as query:
                    query.where('id', schedule_id).update({
                        'status': ScheduleNode.STATUS_WAITING,
                    })

                logging.debug('update Delay node status to waiting')

                break

            # 更新该阶段的处理已完成
            with self.workflow.query('schedules') as query:
                query.where('id', schedule_id).update({
                    'status': ScheduleNode.STATUS_COMPLETED,
                    'update_time': cur_time,
                })

    def __schedule_all(self):
        with self.workflow.query('schedules') as query:
            schedule_nodes = query.order('id', 'desc') \
                .field('id', 'node_id', 'subscriber_email', 'status', 'update_time') \
                .select()

        if len(schedule_nodes) == 0:
            return

        for schedule_node in schedule_nodes:
            self.__schedule_one(ScheduleNode(schedule_node))


class Task:
    def __init__(self):
        self.__interval = 15
        self.__automation = Automation()

    def set_email_campaign(self, node: Node) -> int:
        if node.type != Node.TYPE_EMAIL:
            return False

        cur_time = int(time.time())

        with public.S('email_task', '/www/vmail/postfixadmin') as query:
            if node.get_attribute('campaign_id', 0) < 1 or not query.where('id', node.get_attribute('campaign_id', 0)).exists():
                task_id = query.insert({
                    'task_name': node.get_attribute('name', node.get_attribute('subject', '')),
                    'addresser': node.get_attribute('from', ''),
                    'recipient_count': 0,
                    'task_process': 0,
                    'pause': 0,
                    'temp_id': node.get_attribute('email_id', 0),
                    'is_record': 0,
                    'unsubscribe': int(node.get_attribute('track_unsubscribe', False)),
                    'threads': 0,
                    'created': cur_time,
                    'modified': cur_time,
                    'start_time': 0,
                    'remark': '',
                    'etypes': '',
                    'recipient': '',
                    'subject': node.get_attribute('subject', ''),
                    'full_name': node.get_attribute('from_name', node.get_attribute('from', '')),
                    'type': 1,
                })
            else:
                task_id = node.get_attribute('campaign_id', 0)
                query.where('id', node.get_attribute('campaign_id', 0)).update({
                    'task_name': node.get_attribute('name', node.get_attribute('subject', '')),
                    'addresser': node.get_attribute('from', ''),
                    'recipient_count': 0,
                    'task_process': 0,
                    'pause': 0,
                    'temp_id': node.get_attribute('email_id', 0),
                    'is_record': 0,
                    'unsubscribe': int(node.get_attribute('track_unsubscribe', False)),
                    'threads': 0,
                    'created': cur_time,
                    'modified': cur_time,
                    'start_time': 0,
                    'remark': '',
                    'etypes': '',
                    'recipient': '',
                    'subject': node.get_attribute('subject', ''),
                    'full_name': node.get_attribute('from_name', node.get_attribute('from', '')),
                    'type': 1,
                })

        db_dir = '/www/vmail/bulk'
        db_path = '{}/task_{}'.format(db_dir, task_id)

        if not os.path.exists(db_dir):
            os.makedirs(db_dir)
            os.system('chown -R vmail:mail /www/vmail/bulk')

        # 建表
        # 全量统计  message_id与收件人联合唯一
        sql = '''CREATE TABLE IF NOT EXISTS `task_count` (
    `id` INTEGER  PRIMARY KEY AUTOINCREMENT,
    `queue_id` varchar(320)  NOT NULL,             -- 邮件队列id
    `message_id` TEXT NOT NULL,          -- 邮件 message_id
    `created` INTEGER NOT NULL,               -- 邮件时间 时间戳
    `recipient` varchar(320) NOT NULL,        -- 收件人
    `delay` varchar(320) NOT NULL,            -- 延时
    `delays` varchar(320) NOT NULL,           -- 各阶段延时
    `dsn` varchar(320) NOT NULL,              -- dsn
    `relay` text NOT NULL,                    -- 中继服务器
    `domain` varchar(320) NOT NULL,             -- 域名
    `status` varchar(255) NOT NULL,             -- 状态
    `code` INTEGER,                           -- 状态码   250   5xx  101
    `err_info` text NOT NULL,                   -- 详情
    UNIQUE(message_id,recipient)
);

CREATE INDEX IF NOT EXISTS `message_id_recipient_index` ON `task_count` (`message_id`, `recipient`, `queue_id`);
CREATE INDEX IF NOT EXISTS `id_status_index` ON `task_count` (`id`, `status`);

CREATE TABLE IF NOT EXISTS `recipient_info` (
    `id` INTEGER  PRIMARY KEY AUTOINCREMENT,
    `recipient` varchar(320) NOT NULL,        -- 收件人
    `is_sent` tinyint(1) NOT NULL DEFAULT 0,  -- 是否发送
    `mail_provider` varchar(320) NOT NULL,     -- 邮件提供商域名
    `sent_time` INTEGER NOT NULL,               -- 发送时间 
    `created` INTEGER NOT NULL,                 -- 添加时间 
    UNIQUE(recipient)
);

create index if not exists `recipient_isSent` on `recipient_info` (`recipient`, `is_sent`);'''

        with public.S(db_name=db_path) as query:
            query.execute_script(sql)

        return task_id

    def send_email_with_campaign(self, node: Node, to: str) -> bool:
        campaign_id = node.get_attribute('campaign_id', 0)

        if campaign_id < 1:
            return False

        with public.S('email_task', '/www/vmail/postfixadmin') as query:
            campaign = query.where('id', campaign_id).where('type', 1).field('task_process').find()

            if campaign is None or int(campaign['task_process']) == 1:
                return False

            recipient_file = '{}/data/mail/in_bulk/recipient/{}_verify_{}'.format(public.get_panel_path(),
                                                                                  public.Md5(str(node.id)),
                                                                                  campaign_id)

            recipient_dict = {
                'gmail.com': {"count": 0, "info": [
                    to,
                ]},
                'googlemail.com': {"count": 0, "info": []},
                'hotmail.com': {"count": 0, "info": []},
                'outlook.com': {"count": 0, "info": []},
                'yahoo.com': {"count": 0, "info": []},
                'icloud.com': {"count": 0, "info": []},
                'other': {"count": 0, "info": []},
            }

            with open(recipient_file, 'w') as fp:
                fp.write(json.dumps(recipient_dict))

            query.where('id', campaign_id).update({
                'task_process': 0,
                'recipient': recipient_file,
            })

        ret = public.run_plugin('mail_sys', 'check_task_status_new', public.to_dict_obj({
            'task_id': campaign_id,
        }))

        logging.debug(ret)

        return True

    def walk_running_tasks(self, include_inactive=False):
        status_lst = [1]

        if include_inactive:
            status_lst.append(0)

        with self.__automation.query() as query:
            tasks = query.where_in('status', status_lst).field('id', 'triggers').select()

        for task in tasks:
            try:
                triggers = Triggers(json.loads(task['triggers']))
            except:
                continue

            yield int(task['id']), triggers

    def schedule_async(self, automation_id: int, subscriber: typing.Union[str, typing.List[str]]):
        Scheduler(automation_id).schedule_async(subscriber)

    def schedule(self, automation_id: int, subscriber: typing.Optional[str] = None):
        Scheduler(automation_id).schedule(subscriber)

    def schedule_forever(self):
        time.sleep(self.__interval)

        if self.__automation.is_init():
            for automation_id, _ in self.walk_running_tasks():
                logging.debug('schedule mail automation -- {}'.format(automation_id))
                scheduler = Scheduler(automation_id)
                scheduler.schedule()
                scheduler.schedule_email_sending()
                scheduler.sync_maillog_stat()

        self.schedule_forever()

    def fire(self, trigger_type: str, subscriber: typing.Union[str, typing.List[str]], group_ids: typing.Union[int, typing.List[int]] = 0):
        for automation_id, triggers in self.walk_running_tasks(include_inactive=True):
            if triggers.match(trigger_type, group_ids):
                try:
                    self.schedule_async(automation_id, subscriber)
                except:
                    public.print_log(public.get_error_info())

    def subscriber_added(self, subscriber: typing.Union[str, typing.List[str]], group_ids: typing.Union[int, typing.List[int]] = 0):
        self.fire(Trigger.TYPE_SUBSCRIBER_ADDED, subscriber, group_ids)

    # TODO 当订阅者通过API添加到用户组
    def subscribed(self, subscriber: str, group_ids: typing.Union[int, typing.List[int]] = 0):
        self.fire(Trigger.TYPE_SUBSCRIBED, subscriber, group_ids)

    # TODO 当订阅者打开邮件
    def opened(self, subscriber: str, group_ids: typing.Union[int, typing.List[int]] = 0):
        self.fire(Trigger.TYPE_OPENED, subscriber, group_ids)

    # TODO 当订阅者点击邮件链接
    def clicked(self, subscriber: str, group_ids: typing.Union[int, typing.List[int]] = 0):
        self.fire(Trigger.TYPE_CLICKED, subscriber, group_ids)

    # TODO 当订阅者退订邮件
    def unsubscribed(self, subscriber: str, group_ids: typing.Union[int, typing.List[int]] = 0):
        self.fire(Trigger.TYPE_UNSUBSCRIBED, subscriber, group_ids)


def schedule_automations_forever():
    Task().schedule_forever()
