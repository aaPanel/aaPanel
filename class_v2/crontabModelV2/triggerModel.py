#coding: utf-8
#-------------------------------------------------------------------
# aapanel
#-------------------------------------------------------------------
# Copyright (c) 2015-2099 宝塔软件(http://aapanel.com) All rights reserved.
#-------------------------------------------------------------------
# Author: hwliang <hwl@aapanel.com>
#-------------------------------------------------------------------

#------------------------------
# 任务编排
#------------------------------
import db
import public
import time
import json
import os
import sys
from crontabModelV2.base import crontabBase
class main(crontabBase):

    _log_type = 'Task Scheduling - Tasks'
    _operator = ['=','!=','>','>=','<','<=','in','not in']
    _exec_script_file = 'script/crontab_task_exec.py'
    _exec_log_file = 'logs/crontab_task_exec.log'
    custom_order_path = '/www/server/panel/data/custom_order.json'
    def __init__(self) -> None:
        super().__init__()
        self._sql = db.Sql().dbfile(self.dbfile)
        self.custom_order = self._load_custom_order()

    def _load_custom_order(self):
        if os.path.exists(self.custom_order_path):
            with open(self.custom_order_path, 'r') as f:
                return json.load(f)
        return []

    def save_custom_order(self, args):
        '''
            @name 保存自定义排序
            @param args<dict_obj>{
                order_list<str> 排序后的任务ID列表 (字符串形式的 JSON 数组)
            }
            @return dict
        '''
        order_list_str = args.get('order_list')
        if not order_list_str:
            return public.returnMsg(False, '排序列表不能为空')

        try:
            # 将字符串转换为列表
            order_list = json.loads(order_list_str)
            if not isinstance(order_list, list):
                return public.returnMsg(False, '排序列表格式不正确')

            # 保存排序结果到文件
            public.writeFile(self.custom_order_path, json.dumps(order_list))
            self.custom_order = order_list
            return public.returnMsg(True, '排序保存成功')
        except Exception as e:
            return public.returnMsg(False, '排序保存失败: ' + str(e))
            
    def get_trigger_list_all(self, args=None):
        # 获取所有任务数据
        data = self._sql.table('trigger').order('trigger_id desc').select()
        
        if self.custom_order:
            # 创建任务字典
            id_to_task = {str(task['trigger_id']): task for task in data}
            
            # 根据自定义顺序重新排序任务
            sorted_data = [id_to_task[str(task_id)] for task_id in self.custom_order if str(task_id) in id_to_task]
            
            # 获取未包含在自定义排序中的任务
            remaining_tasks = [task for task in data if int(task['trigger_id']) not in self.custom_order]
            
            # 将剩余任务按照原排序顺序追加到排序后的列表中
            sorted_data.extend(remaining_tasks)
            
            # 返回重新排序后的任务列表
            return sorted_data
        
        # 如果没有自定义排序，返回原排序的任务列表
        return data

    def get_trigger_list(self,args = None):
        '''
            @name 获取任务列表
            @author hwliang
            @param args<dict_obj>{
                p<int> 分页
                rows<int> 每页数量
                search<string> 搜索关键字
            }
            @return list
        '''
        p = 1
        if args and 'p' in args: p = int(args.p)
        rows = 10
        if args and 'rows' in args: rows = int(args.rows)
        search = ''
        if args and 'search' in args: search = args.search
        tojs = ''
        if args and 'tojs' in args: tojs = args.tojs
        where = ''
        params = []
        if search:
            where = "name like ? or ps like ?"
            params.append('%' + search + '%')
            params.append('%' + search + '%')

        if 'script_id' in args:
            where = "script_id = ?"
            params.append(args.script_id)
        if 'type_id' in args and args.type_id:
            where = "type_id = ?"
            params.append(args.type_id)

        if 'status' in args:
            where = "status = ?"
            params.append(args.status)

        count = self._sql.table('trigger').where(where,tuple(params)).count()
        data = public.get_page(count,p,rows,tojs)
        data['data'] = self._sql.table('trigger').where(where,tuple(params)).order('trigger_id desc').limit(data['row'],data['shift']).select()
        # 按自定义排序顺序重新排序任务列表
        if self.custom_order:
            id_to_task = {str(task['trigger_id']): task for task in data['data']}
            # 确保每个任务ID唯一
            sorted_data = []
            seen = set()
            for task_id in self.custom_order:
                str_task_id = str(task_id)
                if str_task_id in id_to_task and str_task_id not in seen:
                    sorted_data.append(id_to_task[str_task_id])
                    seen.add(str_task_id)
            remaining_tasks = [task for task_id, task in id_to_task.items() if str(task_id) not in seen]
            data['data'] = sorted_data + remaining_tasks

        for i in data['data']:
            i['operator_where'] = self._sql.table('operator_where').where('trigger_id=?',i['trigger_id']).select()
            i['return_type'] = 'all'
            i['script_info'] = {}
            if not i['args']: i['args'] = ''
            if i['script_id']:
                i['script_info'] = self._sql.table('scripts').where('script_id=?',(i['script_id'],)).find()
                if i['script_info']:
                    i['return_type'] = i['script_info']['return_type']
                else:
                    i['script_info'] = {}
                if not i['return_type']: i['return_type'] = 'all'

            # 取上次执行时间
            i['last_exec_time'] = self._sql.table('tasks').where('trigger_id=?',(i['trigger_id'],)).order('log_id desc').getField('start_time')
            if not i['last_exec_time']:                
               i['last_exec_time']=""
        if 'order_param' in args and args.order_param:
            order_param=getattr(args,'order_param',None)
            data['data']=self._sort_triggers(data['data'],order_param)
        return public.return_message(0,0,data)

    def _sort_triggers(self, task, order_param):
        sort_key, order = order_param.split(' ')
        reverse_order = order == "desc"
        
        def safe_key(item):
            value = item[sort_key]
            # 将所有值转换为字符串进行比较
            return str(value) if not isinstance(value, str) else value
        
        return sorted(task, key=safe_key, reverse=reverse_order)

        

    def sync_crontab(self,trigger_id):
        '''
            @name 同步到计划任务
            @param trigger_id<int> 任务ID
            @return dict
        '''
        trigger_info = self._sql.table('trigger').where('trigger_id=?',(trigger_id,)).find()
        if not trigger_info:
            return public.returnMsg(False,'任务不存在')

        import crontab_v2 as crontab
        crontab_obj = crontab.crontab()
        # 检查是否使用了自定义 crontab 表达式
        if trigger_info['cycle_type'] == 'custom' and trigger_info['crontab_expression']:
            cron_config = trigger_info['crontab_expression']
        else:
            trigger_info['type'] = trigger_info['cycle_type']
            trigger_info['hour'] = trigger_info['cycle_hour']
            trigger_info['minute'] = trigger_info['cycle_minute']
            trigger_info['week'] = trigger_info['cycle_where']
            trigger_info['where1'] = trigger_info['cycle_where']
            cron_config,param,name = crontab_obj.GetCrondCycle(trigger_info)
        panel_path = public.get_panel_path()
        # start_time = trigger_info['start_time'] if 'start_time' in trigger_info and  trigger_info['start_time'] else ''
        # exec_count = trigger_info['exec_count'] if 'exec_count' in trigger_info and  trigger_info['exec_count'] else 0
        cron_line = "{} {} {}/{} {} >> {}/{}".format(cron_config,public.get_python_bin(),panel_path,self._exec_script_file,trigger_id,panel_path,self._exec_log_file)
        cron_file = crontab_obj.get_cron_file()
        if not os.path.exists(cron_file):
            public.writeFile(cron_file,'')
        cron_body = public.readFile(cron_file)
        cron_lines = cron_body.strip().split('\n')
        cron_lines.append(cron_line)
        cron_body = '\n'.join(cron_lines)
        cron_body += '\n'
        result = public.writeFile(cron_file, cron_body)
        if not result: return False
        crontab_obj.CrondReload()
        return True


    def remove_crontab(self,trigger_id):
        '''
            @name 移除计划任务
            @param trigger_id<int> 任务ID
            @return dict
        '''
        import crontab_v2 as crontab
        crontab_obj = crontab.crontab()
        cron_file = crontab_obj.get_cron_file()
        if not os.path.exists(cron_file):
            return

        cron_body = public.readFile(cron_file)
        cron_lines = cron_body.strip().split('\n')
        cron_lines_new = []
        tip_line = '{} {} >>'.format(self._exec_script_file,trigger_id)

        for cron_line in cron_lines:
            if not cron_line: continue
            if cron_line.find(tip_line) == -1:
                cron_lines_new.append(cron_line)

        cron_body = '\n'.join(cron_lines_new)
        cron_body += '\n'
        public.writeFile(cron_file,cron_body)
        crontab_obj.CrondReload()
        return True




    def get_trigger_info(self,args = None):
        '''
            @name 获取任务信息
            @author hwliang
            @param args<dict_obj>{
                trigger_id<int> 任务ID
            }
            @return dict
        '''
        if not args or not 'trigger_id' in args:
            return public.returnMsg(False,'parameter error')
        trigger_id = int(args.trigger_id)
        trigger_info = self._sql.table('trigger').where('trigger_id=?',(trigger_id,)).find()
        if not trigger_info:
            return public.returnMsg(False,'Task does not exist')

        trigger_info['operator_where'] = self._sql.table('operator_where').where('trigger_id=?',trigger_info['trigger_id']).select()
        return public.returnMsg(True,trigger_info)


    def create_trigger(self,args = None):
        '''
            @name 添加任务信息
            @author hwliang
            @param args<dict_obj>{
                name<string> 任务名称
                script_id<int> 脚本ID
                ps<string> 备注
                script_body<string> 脚本内容
                cycle_type<string> 任务类型
                cycle_where<string> 任务条件
                cycle_hour<string> 小时
                cycle_minute<string> 运行分钟
                operator_where<list>{
                    operator<string> 操作符
                    op_value<string> 值
                    run_script_id<int> 运行脚本ID
                    run_script<string> 运行脚本内容
                }
            }
            @return dict
        '''
        if not args or not hasattr(args,'name') or not hasattr(args,'script_id'):
            return public.return_message(-1,0,public.lang('parameter error'))
        if not args.name:
            return public.return_message(-1,0,public.lang('The task name cannot be empty'))

        if not args.script_id and not args.script_body:
            return public.return_message(-1,0,public.lang('Script content and script ID cannot be empty at the same time'))
        if not args.cycle_type:
            return public.return_message(-1,0,public.lang('Task type cannot be empty'))
        crontab_expression=args.crontab_expression if hasattr(args,'crontab_expression') else ''
        if args.cycle_type=="custom" and not crontab_expression:
            return public.return_message(-1,0, public.lang('Crontab expression cannot be empty'))
        # 验证 crontab 表达式
        if crontab_expression and not self.validate_crontab_expression(crontab_expression):
            return public.return_message(-1,0, public.lang('Invalid crontab expression'))

        script_args = args.get('args','')

        #检查脚本是否存在
        if args.script_id:
            script_info = self._sql.table('scripts').where('script_id=?',(args.script_id,)).find()
            if not script_info:
                return public.return_message(-1,0,public.lang('Script does not exist'))
            if 'is_args' in script_info and script_info['is_args'] == 1 and not script_args:
                return public.return_message(-1,0,public.lang('This script requires script parameters'))

        #检查任务是否存在
        if self._sql.table('trigger').where('name=?',(args.name,)).count():
            return public.return_message(-1,0,public.lang('Task already exists'))
        
        # 根据用户是否提供 crontab 表达式来决定使用哪种方式
        if crontab_expression:
            cycle_type = 'custom'
            cycle_where = ""
            cycle_hour = ''
            cycle_minute = ''
        else:
            cycle_type = args.cycle_type
            cycle_where = args.cycle_where
            cycle_hour = args.cycle_hour
            cycle_minute = args.cycle_minute
        # 获取开始执行时间和执行次数
        start_time = args.start_time if hasattr(args, 'start_time') else 0
        exec_count = args.exec_count if hasattr(args, 'exec_count') else 0
        # 获取当前时间戳
        current_time = int(time.time())
        if start_time:
            # 检查开始时间是否小于当前时间
            if start_time < current_time:
                return public.return_message(-1,0, public.lang('The set start time cannot be earlier than the current time'))


        pdata = {
            'name':args.name,
            'script_id':args.script_id,
            'ps':args.ps,
            'script_body':args.script_body,
            'args':script_args,
            'cycle_type':cycle_type,
            'cycle_where':cycle_where,
            'cycle_hour':cycle_hour,
            'cycle_minute':cycle_minute,
            'create_time': int(time.time()),
            # 'crontab_expression':crontab_expression,
            # 'start_time': start_time,
            # 'exec_count': exec_count
        }

        trigger_id = self._sql.table('trigger').insert(pdata)

        if not trigger_id:
            return public.return_message(-1,0,public.lang('Add failed'))

        result = self.sync_crontab(trigger_id)
        if not result:
            self._sql.table('trigger').where('trigger_id=?', trigger_id).delete()
            return public.return_message(-1,0, public.lang('Writing scheduled task failed, please check if the disk is writable or if system hardening is enabled!'))

        #增加任务条件
        operator_where = args.operator_where
        for op in operator_where:
            op['trigger_id'] = trigger_id
            op['create_time'] = int(time.time())
            self._sql.table('operator_where').insert(op)
        # # 更新自定义排序
        # self.custom_order.insert(0,trigger_id)
        # public.writeFile(self.custom_order_path, json.dumps(self.custom_order))
        public.set_module_logs('crontab_trigger', 'create_trigger', 1)
        public.WriteLog(self._log_type,'Task [{}] added successfully!' ,args.name,)
        return public.return_message(0,0,public.lang('Added successfully'))
    def validate_crontab_expression(self,expression):
            import re
            pattern = (
                r'^(\*|([0-5]?\d)(-\d+)?)(,(\*|([0-5]?\d)(-\d+)?))*\s+'     # Minute: *, 0-59, 0-59/step
                r'(\*|([01]?\d|2[0-3])(-\d+)?)(,(\*|([01]?\d|2[0-3])(-\d+)?))*\s+'  # Hour: *, 0-23, 0-23/step
                r'(\*|([1-9]|[12]\d|3[01])(-\d+)?)(,(\*|([1-9]|[12]\d|3[01])(-\d+)?))*\s+'  # Day of month: *, 1-31, 1-31/step
                r'(\*|([1-9]|1[0-2])(-\d+)?)(,(\*|([1-9]|1[0-2])(-\d+)?))*\s+'  # Month: *, 1-12, 1-12/step
                r'(\*|([0-7])(-\d+)?)(,(\*|([0-7])(-\d+)?))*$'  # Day of week: *, 0-7, 0-7/step
            )
            return re.match(pattern, expression.strip()) is not None


    def modify_trigger(self,args = None):
        '''
            @name 修改任务信息
            @author hwliang
            @param args<dict_obj>{
                trigger_id<int> 任务ID
                name<string> 任务名称
                script_id<int> 脚本ID
                ps<string> 备注
                script_body<string> 脚本内容
                cycle_type<string> 任务类型
                cycle_where<string> 任务条件
                cycle_hour<string> 小时
                cycle_minute<string> 运行分钟
                operator_where<list>{
                    operator<string> 操作符
                    op_value<string> 值
                    run_script_id<int> 运行脚本ID
                    run_script<string> 运行脚本内容
                }
            }
            @return dict
        '''
        if not args or not hasattr(args,'name') or not hasattr(args,'script_id'):
            return public.return_message(-1,0,public.lang('parameter error'))
        if not args.name:
            return public.return_message(-1,0,public.lang('The task name cannot be empty'))

        if not args.script_id and not args.script_body:
            return public.return_message(-1,0,public.lang('Script content and script ID cannot be empty at the same time'))
        if not args.cycle_type:
            return public.return_message(-1,0,public.lang('Task type cannot be empty'))
        crontab_expression=args.crontab_expression if hasattr(args,'crontab_expression') else ''
        if args.cycle_type=="custom" and not crontab_expression:
            return public.return_message(-1,0, public.lang('Crontab expression cannot be empty'))
        # 验证 crontab 表达式
        if crontab_expression and not self.validate_crontab_expression(crontab_expression):
            return public.return_message(-1,0, public.lang('Invalid crontab expression'))
        script_args = args.get('args','')
        #检查脚本是否存在
        if args.script_id:
            script_info = self._sql.table('scripts').where('script_id=?',(args.script_id,)).find()
            if not script_info:
                return public.return_message(-1,0,'Script does not exist')
            if 'is_args' in script_info and script_info['is_args'] and not script_args:
                return public.return_message(-1,0,public.lang('This script requires script parameters'))

        #检查任务是否存在
        trigger_info = self._sql.table('trigger').where('trigger_id=?',(args.trigger_id,)).find()
        if not trigger_info:
            return public.return_message(-1,0,public.lang('Task does not exist'))

        #检查任务是否存在
        if self._sql.table('trigger').where('name=? and trigger_id!=?',(args.name,args.trigger_id)).count():
            return public.return_message(-1,0,public.lang('Task already exists'))
        # 根据用户是否提供 crontab 表达式来决定使用哪种方式
        if crontab_expression:
            cycle_type = 'custom'
            cycle_where = ""
            cycle_hour = ''
            cycle_minute = ''
        else:
            cycle_type = args.cycle_type
            cycle_where = args.cycle_where
            cycle_hour = args.cycle_hour
            cycle_minute = args.cycle_minute
        # 获取开始执行时间和执行次数
        start_time = args.start_time if hasattr(args, 'start_time') else 0
        exec_count = args.exec_count if hasattr(args, 'exec_count') else 0
        # 获取当前时间戳
        current_time = int(time.time())
        if start_time:
            # 检查开始时间是否小于当前时间
            if start_time < current_time:
                return public.return_message(-1,0, public.lang('The set start time cannot be earlier than the current time'))


        pdata = {
            'name':args.name,
            'script_id':args.script_id,
            'ps':args.ps,
            'script_body':args.script_body,
            'args':script_args,
            'cycle_type':cycle_type,
            'cycle_where':cycle_where,
            'cycle_hour':cycle_hour,
            'cycle_minute':cycle_minute,
            # 'crontab_expression':crontab_expression,
            # 'start_time': start_time,
            # 'exec_count': exec_count
        }

        self._sql.table('trigger').where('trigger_id=?',(args.trigger_id,)).update(pdata)

        # #删除任务条件
        # self._sql.table('operator_where').where('trigger_id=?',(args.trigger_id,)).delete()

        #增加任务条件
        operator_where = args.operator_where
        for op in operator_where:
            op['trigger_id'] = args.trigger_id
            op['create_time'] = int(time.time())
            self._sql.table('operator_where').insert(op)
        self.remove_crontab(args.trigger_id)
        result = self.sync_crontab(args.trigger_id)
        if not result:
            return public.return_message(-1,0, public.lang('Writing scheduled task failed, please check if the disk is writable or if system hardening is enabled!'))
         # 删除 task_count.json 中对应的任务执行次数记录
         
        count_file = '/www/server/panel/data/task_count.json'
        if os.path.exists(count_file):
            with open(count_file, 'r') as f:
                task_counts = json.load(f)
            if str(args.trigger_id) in task_counts:
                del task_counts[str(args.trigger_id)]
                with open(count_file, 'w') as f:
                    json.dump(task_counts, f)
        # 更新数据库中的任务
        self._sql.table('trigger').where('trigger_id=?', (args.trigger_id,)).update(pdata)

        public.WriteLog(self._log_type,'Task modification [{}] successful!',args.name)
        return public.return_message(0,0,public.lang('Modified successfully'))


    def remove_trigger(self,args = None):
        '''
            @name 删除任务信息
            @author hwliang
            @param args<dict_obj>{
                trigger_id<int> 任务ID
            }
            @return dict
        '''
        if not args or not 'trigger_id' in args:
            return public.return_message(-1,0,public.lang('parameter error'))

        trigger_info = self._sql.table('trigger').where('trigger_id=?',(args.trigger_id,)).find()
        if not trigger_info:
            return public.return_message(-1,0,public.lang('Task does not exist'))

        self._sql.table('trigger').where('trigger_id=?',(args.trigger_id,)).delete()
        self._sql.table('operator_where').where('trigger_id=?',(args.trigger_id,)).delete()
        self._sql.table("tasks").where('trigger_id=? AND script_id=0',(args.trigger_id,)).delete()
        self.remove_crontab(args.trigger_id)
        # 删除 task_count.json 中对应的任务执行次数记录
        count_file = '/www/server/panel/data/task_count.json'
        if os.path.exists(count_file):
            with open(count_file, 'r') as f:
                task_counts = json.load(f)
            if str(args.trigger_id) in task_counts:
                del task_counts[str(args.trigger_id)]
                with open(count_file, 'w') as f:
                    json.dump(task_counts, f)

        # 更新自定义排序
        if args.trigger_id in self.custom_order:
            self.custom_order.remove(args.trigger_id)
            public.writeFile(self.custom_order_path, json.dumps(self.custom_order))
        public.WriteLog(self._log_type,'Task [{}] deleted successfully!',trigger_info['name'])
        return public.return_message(0,0,public.lang('Delete successfully'))


    def get_operator_where_list(self,args):
        '''
            @name 获取触发事件列表
            @author hwliang
            @param args<dict_obj>{
                trigger_id:<int>
            }
            @return list
        '''
        trigger_id = args.get('trigger_id',0)
        if not trigger_id: return public.return_message(-1,0,public.lang("Task ID cannot be empty"))
        data = self._sql.table('operator_where').where('trigger_id=?',trigger_id).select()
        for d in data:
            d['script_info'] = {}
            if d['run_script_id']:
                d['script_info'] = self._sql.table('scripts').where('script_id=?',(d['run_script_id'],)).find()
                if not d['script_info']: d['script_info'] = {}
            if not d['args']: d['args'] = ''
        return public.return_message(0,0,data)

    def create_operator_where(self,args):
        '''
            @name 创建触发事件
            @author hwliang
            @param args<dict_obj>{
                "trigger_id":<int>,  任务ID
                "operator":<string>, 运算符，支持： =,!=,>,>=,<,<=,in,not in
                "op_value":<mixed>, 比较值，如果运算符为in,not in 时，此处应当为string类型的数据； 运算符为=,!=时，可以是string/int/float类型的数据；运算符为>,>=,<,<=时，此处应当为: int/float类型的数据
                "run_script_id":<int>,  触发成功后运行的脚本ID，此参数与run_script互斥
                "run_script":<string> 触发触功后运行的脚本内容，仅支持bash脚本，此参数与run_script_id互斥
            }
            @return dict
        '''
        op = {}
        op['trigger_id'] = int(args.get('trigger_id',0))
        op['operator'] = args.get('operator','=')
        op['op_value'] = args.get('op_value','')
        op['run_script_id'] = int(args.get('run_script_id',0))
        op['run_script'] = args.get('run_script','')
        op['args'] = args.get('args','')
        if not op['run_script_id'] and not op['run_script']:
            return public.return_message(-1,0,public.lang('Run_stcript_id and run_stcript require at least one valid value'))

        if not op['operator'] in self._operator:
            return public.return_message(-1,0,public.lang('Please use one of the following operators：{}',str(self._operator)))

        trigger_info = self._sql.table('trigger').where('trigger_id=?',(op['trigger_id'],)).find()
        if not trigger_info:
            return public.return_message(-1,0,public.lang('The specified task does not exist'))

        if op['run_script_id']:
            script_info = self._sql.table('scripts').where('script_id=?',(op['run_script_id'],)).find()
            if not script_info:
                return public.return_message(-1,0,public.lang('The specified script does not exist'))
            if 'is_args' in script_info and script_info['is_args'] and not op['args']:
                return public.return_message(-1,0,public.lang('The script requires parameters, please fill in the parameters'))


        op['create_time'] = int(time.time())
        if not self._sql.table('operator_where').insert(op):
            return public.return_message(-1,0,public.lang('Failed to add trigger event'))

        public.WriteLog(self._log_type,"Added a new event for task [{}]",trigger_info['name'])
        return public.return_message(0,0,public.lang('Added successfully'))


    def modify_operator_where(self,args):
        '''
            @name 修改触发事件
            @author hwliang
            @param args<dict_obj>{
                "where_id": <int> 事件ID
                "operator":<string>, 运算符，支持： =,!=,>,>=,<,<=,in,not in
                "op_value":<mixed>, 比较值，如果运算符为in,not in 时，此处应当为string类型的数据； 运算符为=,!=时，可以是string/int/float类型的数据；运算符为>,>=,<,<=时，此处应当为: int/float类型的数据
                "run_script_id":<int>,  触发成功后运行的脚本ID，此参数与run_script互斥
                "run_script":<string> 触发触功后运行的脚本内容，仅支持bash脚本，此参数与run_script_id互斥
            }
            @return dict
        '''
        op = {}
        op['where_id'] = int(args.get('where_id',0))
        op['operator'] = args.get('operator','=')
        op['op_value'] = args.get('op_value','')
        op['run_script_id'] = args.get('run_script_id',0)
        op['run_script'] = args.get('run_script','')
        op['args'] = args.get('args','')
        if not op['where_id']:
            return public.return_message(-1,0,public.lang('Event ID cannot be empty'))

        if not op['operator'] in self._operator:
            return public.return_message(-1,0,public.lang('Please use one of the following operators：{}',str(self._operator)))

        where_info = self._sql.table('operator_where').where('where_id=?',(op['where_id'],)).find()
        if not where_info:
            return public.return_message(-1,0,public.lang('The specified event does not exist'))

        if not op['run_script_id'] and not op['run_script']:
            return public.return_message(-1,0,public.lang('Run_stcript_id and run_stcript require at least one valid value'))

        if op['run_script_id']:
            script_info = self._sql.table('scripts').where('script_id=?',(op['run_script_id'],)).find()
            if not script_info:
                return public.return_message(-1,0,public.lang('The specified script does not exist'))
            if 'is_args' in script_info and script_info['is_args'] and not op['args']:
                return public.return_message(-1,0,public.lang('The script requires parameters, please fill in the parameters'))

        if not self._sql.table('operator_where').where('where_id=?',op['where_id']).update(op):
            return public.return_message(-1,0,public.lang('Event modification successful'))

        public.WriteLog(self._log_type,"Modify Event:{} ",str(op['where_id']))
        return public.return_message(0,0,public.lang('Modified successfully'))


    def remove_operator_where(self,args):
        '''
            @name 删除指定事件
            @author hwliang
            @param args<dict_obj>{
                "where_id": <int> 事件ID
            }
            @return dict
        '''
        where_id = int(args.get('where_id',0))
        if not where_id: return public.return_message(-1,0,public.lang('Event ID cannot be empty'))
        where_info = self._sql.table('operator_where').where('where_id=?',(where_id,)).find()
        if not where_info:
            return public.return_message(-1,0,public.lang('The specified event does not exist'))

        if not self._sql.table('operator_where').where('where_id=?',where_id).delete():
            return public.return_message(-1,0,public.lang('Event deletion failed'))

        public.WriteLog(self._log_type,"Delete Event: {}",str(where_id))
        return public.return_message(0,0,public.lang('Delete successfully'))



    def exec_script(self,script_id,script_body,s_args):
        '''
            @name 执行脚本内容
            @param script_id<int> 脚本ID
            @param script_body<string> 脚本内容
            @return dict
        '''
        script_type = 'bash'
        script_exts = {'bash':'sh','python':'py','php':'php','node':'js','ruby':'rb','perl':'pl'}
        if script_id:
            script_info = self._sql.table('scripts').where('script_id=?',(script_id,)).find()
            if not script_info:
                return False
            script_body = script_info['script']
            script_type = script_info['script_type']

        if not script_body:
            return False

        if s_args: s_args = ' ' + s_args

        tmp_file = '{}/tmp/{}.{}'.format(public.get_panel_path(),public.GetRandomString(32),script_exts[script_type])
        public.writeFile(tmp_file,script_body)

        if script_type == 'bash':
            result = public.ExecShell('bash {}{}'.format(tmp_file,s_args))
        elif script_type == 'python':
            result = public.ExecShell('{} {}{}'.format(public.get_python_bin(),tmp_file,s_args))

        if os.path.exists(tmp_file):
            os.remove(tmp_file)

        return result

    def add_task_log(self,script_id,trigger_id,where_id,status,result_succ,result_err,start_time,end_time):
        '''
            @name 添加任务日志
            @param script_id<int> 脚本ID
            @param trigger_id<int> 触发器ID
            @param where_id<int> 事件ID
            @param status<int> 任务状态
            @param result_succ<string> 成功结果
            @param result_err<string> 错误结果
            @param start_time<int> 开始时间
            @param end_time<int> 结束时间
            @return bool
        '''
        return self._sql.table('tasks').add('script_id,trigger_id,where_id,status,result_succ,result_err,start_time,end_time',
            (script_id,trigger_id,where_id,status,result_succ,result_err,start_time,end_time))

    def get_trigger_logs(self,args):
        '''
            @name 获取任务执行日志
            @param args<dict_obj>{
                "trigger_id": <int> 任务ID
                "p": <int> 页码
                "rows": <int> 每页数量
            }
        '''
        trigger_id = int(args.get('trigger_id',0))
        if not trigger_id: return public.returnMsg(False,public.lang('Task ID cannot be empty'))
        p = 1
        if 'p' in args: p = int(args['p'])
        rows = 10
        if 'rows' in args: rows = int(args['rows'])
        tojs = ''
        if 'tojs' in args: tojs = args.tojs

        where = 'trigger_id=?'
        where_args = (trigger_id,)
        count = self._sql.table('tasks').where(where,where_args).count()
        page = public.get_page(count,p,rows,tojs)
        page['data'] = self._sql.table('tasks').where(where,where_args).limit(page['row'],page['shift']).order('log_id desc').select()
        return public.return_message(0,0,page)

    def get_operator_logs(self,args):
        '''
            @name 获取任务事件执行日志
            @param args<dict_obj>{
                "where_id": <int> 任务事件ID
                "p": <int> 页码
                "rows": <int> 每页数量
            }
        '''
        where_id = int(args.get('where_id',0))
        if not where_id: return public.returnMsg(False,public.lang('Task event ID cannot be empty'))
        p = 1
        if 'p' in args: p = int(args['p'])
        rows = 10
        if 'rows' in args: rows = int(args['rows'])
        tojs = ''
        if 'tojs' in args: tojs = args.tojs

        where = 'where_id=?'
        where_args = (where_id,)
        count = self._sql.table('tasks').where(where,where_args).count()
        page = public.get_page(count,p,rows,tojs)
        page['data'] = self._sql.table('tasks').where(where,where_args).limit(page['row'],page['shift']).order('log_id desc').select()
        return public.return_message(0,0,page)

    def test_trigger(self,args):
        '''
            @name 测试指定任务
            @author hwliang
            @param args<dict_obj>{
                trigger_id<int> 任务ID
            }
            @return dict
        '''
        if not args or not 'trigger_id' in args:
            return {'status': -1, "timestamp": int(time.time()), "message": {'result':public.lang('parameter error')}}


        trigger_info = self._sql.table('trigger').where('trigger_id=?',(args.trigger_id,)).find()
        if not trigger_info:
            return {'status': -1, "timestamp": int(time.time()), "message": {'result':public.lang('Task does not exist')}}
        script_body = ''
        script_type = 'bash'
        return_type = 'string'

        script_exts = {'bash':'sh','python':'py','php':'php','node':'js','ruby':'rb','perl':'pl'}
        script_args = ''
        #检查脚本是否存在
        if trigger_info['script_id']:
            script_info = self._sql.table('scripts').where('script_id=?',(trigger_info['script_id'],)).find()
            if not script_info:
                return {'status': -1, "timestamp": int(time.time()), "message": {'result':public.lang('Script does not exist')}}
            script_body = script_info['script']
            script_type = script_info['script_type']
            return_type = script_info['return_type']
            if 'args' in trigger_info and trigger_info['args']: script_args = trigger_info['args']
        else:
            script_body = trigger_info['script_body']

        trigger_start_time = int(time.time())
        result_msg = ['Executing task...']
        if script_args: script_args = ' {}'.format(script_args)

        tmp_file = '{}/tmp/trigger_{}.{}'.format(public.get_panel_path(),trigger_info['trigger_id'],script_exts[script_type])
        public.writeFile(tmp_file,script_body)

        #执行脚本
        if script_type == 'bash':
            result = public.ExecShell("bash {}{}".format(tmp_file,script_args))
        else:
            result = public.ExecShell("{} {}{}".format(public.get_python_bin(),tmp_file,script_args))

        if os.path.exists(tmp_file):
            os.remove(tmp_file)

        if not result[0]:
            self.add_task_log(trigger_info['script_id'],trigger_info['trigger_id'],0,0,result[0],result[1],trigger_start_time,int(time.time()))
            return {'status': -1, "timestamp": int(time.time()), "message": {'result':public.lang('Script execution failed with error message:\n{}',str(result[1]))}}
        result_zero=result[0]
        search_string=' local variable start_time where it is not associated with a value\n'
        if result[0].find(search_string) != -1:
            result_zero = result[0].split(search_string)[1]


        result_msg.append("The task script has been executed and returned the result:\n{}".format(result_zero))
        #检查任务事件
        operator_where = self._sql.table('operator_where').where('trigger_id=?',(args.trigger_id,)).select()
        if not operator_where:
            result_msg.append("This task has no event set, skip event check.")
            self.add_task_log(trigger_info['script_id'],trigger_info['trigger_id'],0,1,'\n'.join(result_msg),result[1],trigger_start_time,int(time.time()))
            # return public.return_message(0,0,result_msg)
            return {'status': 0, "timestamp": int(time.time()), "message": result_msg}

        if return_type in ['string','json']:
            _line = result_zero.strip()
        else:
            _line = result_zero.strip().split('\n')[-1]

        _value = _line
        if return_type == 'string':
            _value = _line
        elif return_type == 'json':
            try:
                _value = json.loads(_line)
            except:
                result_msg.append("The script returns a result that is not in JSON format, skipping event checking.")
                self.add_task_log(trigger_info['script_id'],trigger_info['trigger_id'],0,0,'\n'.join(result_msg),result[1],trigger_start_time,int(time.time()))
                return {'status': -1, "timestamp": int(time.time()), "message": result_msg}
        elif return_type == 'int':
            try:
                _value = int(_line)
            except:
                result_msg.append("The last line of the script return result is not an integer, skip event check.")
                self.add_task_log(trigger_info['script_id'],trigger_info['trigger_id'],0,0,'\n'.join(result_msg),result[1],trigger_start_time,int(time.time()))
                return {'status': -1, "timestamp": int(time.time()), "message": result_msg}
        elif return_type == 'float':
            try:
                _value = float(_line)
            except:
                result_msg.append("The last line of the script return result is not a floating-point number, skip event check.")
                self.add_task_log(trigger_info['script_id'],trigger_info['trigger_id'],0,0,'\n'.join(result_msg),result[1],trigger_start_time,int(time.time()))
                return {'status': -1, "timestamp": int(time.time()), "message": result_msg}
        result_msg.append("There are {} events that need to be processed".format(len(operator_where)))
        n = 1

        for op in operator_where:
            if return_type == 'int':
                op['op_value'] = int(op['op_value'])
            elif return_type == 'float':
                op['op_value'] = float(op['op_value'])
            _script = op['run_script_id'] if op['run_script_id'] else op['run_script']
            result_msg.append("Processing {} th event: [Execute {} when returning value {} {}]".format(n,op['operator'],op['op_value'],_script))
            op_start_time = int(time.time())
            is_true = False
            if op['operator'] in ['==','=']:
                if _value == op['op_value']:
                    is_true = True
            elif op['operator'] == '!=':
                if _value != op['op_value']:
                    is_true = True
            elif op['operator'] == '>':
                if _value > op['op_value']:
                    is_true = True
            elif op['operator'] == '>=':
                if _value >= op['op_value']:
                    is_true = True
            elif op['operator'] == '<':
                if _value < op['op_value']:
                    is_true = True
            elif op['operator'] == '<=':
                if _value <= op['op_value']:
                    is_true = True
            elif op['operator'] == 'in':
                if str(_value).find(str(op['op_value'])) != -1:
                    is_true = True
            elif op['operator'] == 'not in':
                if str(_value).find(str(op['op_value'])) == -1:
                    is_true = True

            if is_true:
                result_msg.append("Event condition met, executing script...")
                public.WriteLog('Task arrangement',"Task [{}] triggers condition [returns result {} {}], the preset script has been executed!".format(trigger_info['name'],op['operator'],op['op_value']))
                s_args = ''
                if 'args' in op and op['args']: s_args = op['args']
                result_msg.append("Event condition met, executing event script...")

                result = self.exec_script(op['run_script_id'],op['run_script'],s_args)
                if not result[0]:
                    public.WriteLog('Task arrangement',"Task [{}] triggers condition [returns result {} {}], execution of preset script fails：{} ".format(trigger_info['name'],op['operator'],op['op_value'],result[1]))
                    result_msg.append("Event script execution failed with error message:\n{}".format("\n".join(result)))
                    self.add_task_log(op['run_script_id'],0,op['where_id'],0,'\n'.join(result_msg),'\n'.join(result),op_start_time,int(time.time()))
                else:
                    self.add_task_log(op['run_script_id'],0,op['where_id'],1,result[0],result[1],op_start_time,int(time.time()))
                    result_msg.append("Event script execution successful, return result:\n{}".format(result[0]))
            else:
                result_msg.append("Event condition not met, skip execution.")

            result_msg.append("The {} th event has been processed.".format(n))
            result_msg.append("-" * 20)
            n+=1
        self.add_task_log(trigger_info['script_id'],trigger_info['trigger_id'],0,1,'\n'.join(result_msg),result[1],trigger_start_time,int(time.time()))
        return {'status': 0, "timestamp": int(time.time()), "message": {'result':public.lang("\n".join(result_msg))}}
    # 设置计划任务状态
    def set_trigger_status(self, args):
        try:
            trigger_id=args.trigger_id
            triggerInfo = self._sql.table('trigger').where('trigger_id=?',(trigger_id,)).find()
            
            if not triggerInfo:
                return public.returnMsg(False, "未找到对应任务的数据，请刷新页面查看该任务是否存在！")
            status_msg = ['停用', '启用']
            status = int(args.status)
            if status == 0:
                if not self.remove_crontab(trigger_id):
                    return public.returnMsg(False, '写入计划任务失败,请检查磁盘是否可写或是否开启了系统加固!')
                
            else:
                if not self.sync_crontab(trigger_id):
                    return public.returnMsg(False, '写入计划任务失败,请检查磁盘是否可写或是否开启了系统加固!')

            self._sql.table('trigger').where('trigger_id=?',(trigger_id,)).setField('status', status)
            return public.returnMsg(True, '处理成功')
        except :
            import traceback
            return public.returnMsg(False,traceback.format_exc())
            
    def get_trigger_types(self, args):
        data = public.M("trigger_types").field("id,name,ps").order("id asc").select()
        return {'status': True, 'msg': data}

    def add_trigger_type(self, args):
        import re
        # get.name =  html.escape(get.name.strip())
        name = public.xsssec(args.name.strip())
        if re.search('<.*?>', args.name):
            return public.returnMsg(False, "分类名称不能包含HTML语句")
        if not name:
            return public.returnMsg(False, "分类名称不能为空")
        if len(name) > 16:
            return public.returnMsg(False, "分类名称长度不能超过16位")

        trigger_type_sql = public.M('trigger_types')


        if trigger_type_sql.where('name=?', (name,)).count() > 0:
            return public.returnMsg(False, "指定分类名称已存在")

        # 添加新的计划任务分类
        trigger_type_sql.add("name", (name,))

        return public.returnMsg(True, 'Successfully added')

    def remove_trigger_type(self, args):
        trigger_type_sql = public.M('trigger_types')
        trigger_sql = public.M('trigger')
        trigger_type_id = args.id

        if trigger_type_sql.where('id=?', ( trigger_type_id,)).count() == 0:
            return public.returnMsg(False, "指定分类不存在")

        trigger_type_sql.where('id=?', (trigger_type_id,)).delete()
        try:
           trigger_sql.where('type_id=?', (trigger_type_id,)).save('type_id', (0))
        except:
            pass

        return public.returnMsg(True, "分类已删除")

    def modify_trigger_type_name(self, args):
        import re
        # get.name =  html.escape(get.name.strip())
        name = public.xsssec(args.name.strip())
        trigger_type_id = args.id
        if re.search('<.*?>', args.name):
            return public.returnMsg(False, "分类名称不能包含HTML语句")
        if not name:
            return public.returnMsg(False, "分类名称不能为空")
        if len(name) > 16:
            return public.returnMsg(False, "分类名称长度不能超过16位")

        trigger_type_sql = public.M('trigger_types')

        if trigger_type_sql.where('id=?', (trigger_type_id,)).count() == 0:
            return public.returnMsg(False, "指定分类不存在")

        if trigger_type_sql.where('name=? AND id!=?', (name, trigger_type_id)).count() > 0:
            return public.returnMsg(False, "指定分类名称已存在")

        # 修改指定的计划任务分类名称
        trigger_type_sql.where('id=?', ( trigger_type_id,)).setField('name', name)

        return public.returnMsg(True, "修改成功")

    def set_trigger_type(self, args):
        try:
            trigger_ids = json.loads(args.trigger_ids)
            trigger_type_sql = public.M('trigger_types')
            trigger_sql = public.M('trigger')

            trigger_type_id = args.id
            if trigger_type_id=="0":
                return public.returnMsg(False,"不能设置为默认分类!")
            if trigger_type_sql.where('id=?', (trigger_type_id,)).count() == 0:
                return public.returnMsg(False, "指定分类不存在")
            for s_id in trigger_ids:
                trigger_sql.where("trigger_id=?", (s_id,)).save('type_id', (trigger_type_id))

            return public.returnMsg(True, "设置成功!")
        except Exception as e:
            return public.returnMsg(False, "设置失败" + str(e))










