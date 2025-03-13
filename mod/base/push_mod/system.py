import datetime
import time
from threading import Thread
from typing import Optional, List, Tuple, Dict, Type, Union

import public
from .base_task import BaseTask
from .compatible import rsync_compatible
from .mods import TaskTemplateConfig, TaskConfig, TaskRecordConfig, SenderConfig
from .send_tool import sms_msg_normalize
from .tool import load_task_cls_by_path, load_task_cls_by_function, T_CLS
from .util import get_server_ip, get_network_ip, format_date, get_config_value

WAIT_TASK_LIST: List[Thread] = []


class PushSystem:
    def __init__(self):
        self.task_cls_cache: Dict[str, Type[T_CLS]] = {}
        self._today_zero: Optional[datetime.datetime] = None
        self._sender_type_class: Optional[dict] = {}
        self.sd_cfg = SenderConfig()

    def sender_cls(self, sender_type: str):
        if not self._sender_type_class:
            from mod.base.msg import WeiXinMsg, MailMsg, WebHookMsg, FeiShuMsg, DingDingMsg, SMSMsg, TgMsg
            self._sender_type_class = {
                "weixin": WeiXinMsg,
                "mail": MailMsg,
                "webhook": WebHookMsg,
                "feishu": FeiShuMsg,
                "dingding": DingDingMsg,
                "sms": SMSMsg,
                # "wx_account": WeChatAccountMsg,
                "tg": TgMsg,
            }
        return self._sender_type_class[sender_type]

    @staticmethod
    def can_run_task_list():
        result = []
        result_template = {}
        for task in TaskConfig().config:  # all task
            if not task["status"]:
                continue
            # 间隔检测时间未到跳过
            if "interval" in task["task_data"] and isinstance(task["task_data"]["interval"], int):
                if time.time() < task["last_check"] + task["task_data"]["interval"]:
                    continue
            result.append(task)
            for template in TaskTemplateConfig().config:  # task's template
                if template.get("id") == task["template_id"] and template.get("used"):
                    result_template.update({task["id"]: template})
                    break
        return result, result_template

    def get_task_object(self, template_id, load_cls_data: dict) -> Optional[BaseTask]:
        if template_id in self.task_cls_cache:
            return self.task_cls_cache[template_id]()
        if "load_type" not in load_cls_data:
            return None
        if load_cls_data["load_type"] == "func":
            cls = load_task_cls_by_function(
                name=load_cls_data["name"],
                func_name=load_cls_data["func_name"],
                is_model=load_cls_data.get("is_model", False),
                model_index=load_cls_data.get("is_model", ''),
                args=load_cls_data.get("args", None),
                sub_name=load_cls_data.get("sub_name", None),
            )
        else:
            cls_path = load_cls_data["cls_path"]
            cls = load_task_cls_by_path(cls_path, load_cls_data["name"])

        if not cls:
            return None
        self.task_cls_cache[template_id] = cls
        return cls()

    def run(self):
        rsync_compatible()
        task_list, task_template = self.can_run_task_list()
        try:
            for t in task_list:
                template = task_template[t["id"]]
                print(PushRunner(t, template, self)())
        except Exception as e:
            import traceback
            public.print_log(f"run task error %s", e)
            public.print_log(traceback.format_exc())

        global WAIT_TASK_LIST
        if WAIT_TASK_LIST:  # 有任务启用子线程的，要等到这个线程结束，再结束主线程
            for i in WAIT_TASK_LIST:
                i.join()

    def get_today_zero(self) -> datetime.datetime:
        if self._today_zero is None:
            t = datetime.datetime.today()
            t_zero = datetime.datetime.combine(t, datetime.time.min)
            self._today_zero = t_zero
        return self._today_zero


class PushRunner:
    def __init__(self, task: dict, template: dict, push_system: PushSystem, custom_push_data: Optional[dict] = None):
        self._public_push_data: Optional[dict] = None
        self.result: dict = {
            "do_send": False,
            "stop_msg": "",
            "push_data": {},
            "check_res": False,
            "check_stop_on": "",
            "send_data": {},
        }  # 记录结果
        self.change_fields = set()  # 记录task变化值
        self.task_obj: Optional[BaseTask] = None
        self.task = task
        self.template = template
        self.push_system = push_system
        self._add_hook_msg: Optional[str] = None  # 记录前置钩子处理后的追加信息
        self.custom_push_data = custom_push_data

        self.tr_cfg = TaskRecordConfig(task["id"])
        self.is_number_rule_by_func = False  # 记录这个任务是否使用自定义的次数检测， 如果是，就不需要做次数更新

    def save_result(self):
        t = TaskConfig()
        tmp = t.get_by_id(self.task["id"])
        if tmp:
            for f in self.change_fields:
                tmp[f] = self.task[f]

            if self.result["do_send"]:
                tmp["last_send"] = int(time.time())
            tmp["last_check"] = int(time.time())

            t.save_config()

        if self.result["push_data"]:
            result_data = self.result.copy()
            self.tr_cfg.config.append(
                {
                    "id": self.tr_cfg.nwe_id(),
                    "template_id": self.template["id"],
                    "task_id": self.task["id"],
                    "do_send": result_data.pop("do_send"),
                    "send_data": result_data.pop("push_data"),
                    "result": result_data,
                    "create_time": int(time.time()),
                }
            )
            self.tr_cfg.save_config()

    @property
    def public_push_data(self) -> dict:
        if self._public_push_data is None:
            self._public_push_data = {
                'ip': get_server_ip(),
                'local_ip': get_network_ip(),
                'server_name': get_config_value('title')
            }
        data = self._public_push_data.copy()
        data['time'] = format_date()
        data['timestamp'] = int(time.time())
        return data

    def __call__(self):
        self.run()
        self.save_result()
        if self.task_obj:
            self.task_obj.task_run_end_hook(self.result)
        return self.result_to_return()

    def result_to_return(self) -> dict:
        return self.result

    def run(self):
        self.task_obj = self.push_system.get_task_object(self.template["id"], self.template["load_cls"])

        if not self.task_obj:
            self.result["stop_msg"] = "The task class failed to load"
            return
        if self.custom_push_data is None:
            push_data = self.task_obj.get_push_data(self.task["id"], self.task["task_data"])
            if not push_data:
                return
        else:
            push_data = self.custom_push_data

        self.result["push_data"] = push_data
        # 执行前置钩子
        if self.task["pre_hook"] and "hook_type" in self.task["pre_hook"]:
            if not self.run_hook(self.task["pre_hook"], "pre_hook"):
                return

        # 执行时间规则判断
        if not self.run_time_rule(self.task["time_rule"]):
            return

        # 执行时间规则判断
        if not self.number_rule(self.task["number_rule"]):
            return

        # 执行发送信息
        self.send_message(push_data)
        self.change_fields.add("number_data")
        if "day_num" not in self.task["number_data"]:
            self.task["number_data"]["day_num"] = 0

        if "total" not in self.task["number_data"]:
            self.task["number_data"]["total"] = 0

        self.task["number_data"]["day_num"] += 1
        self.task["number_data"]["total"] += 1
        self.task["number_data"]["time"] = int(time.time())

        # 执行后置钩子
        if self.task["after_hook"] and "hook_type" in self.task["after_hook"]:
            self.run_hook(self.task["after_hook"], "after_hook")

    # todo: 下个版本实现一些自定义的hook函数，同时实现用户脚本的hook记录在 self.result 最后统一储存
    def run_hook(self, hook_data: dict, hook_name: str) -> bool:
        """
        执行hook操作，并返回是否继续执行, 并将hook的执行结果记录
        @param hook_name: 钩子的名称，如：after_hook， pre_hook
        @param hook_data: 执行的内容
        @return:
        """
        return True

    def run_time_rule(self, time_rule: dict) -> bool:
        if "send_interval" in time_rule and time_rule["send_interval"] > 0:
            if self.task["last_send"] + time_rule["send_interval"] > time.time():
                self.result['stop_msg'] = 'If the minimum send time is less, no sending will be made'
                self.result['check_stop_on'] = "time_rule_send_interval"
                return False

        time_range = time_rule.get("time_range", None)
        if time_range and isinstance(time_range, list) and len(time_range) == 2:
            t_zero = self.push_system.get_today_zero()
            start_time = t_zero + datetime.timedelta(seconds=time_range[0])
            end_time = t_zero + datetime.timedelta(seconds=time_range[1])
            if not start_time < datetime.datetime.now() < end_time:
                self.result['stop_msg'] = 'It is not within the time frame within which the alarm can be sent'
                self.result['check_stop_on'] = "time_rule_time_range"
                return False
        return True

    def number_rule(self, number_rule: dict) -> bool:
        number_data = self.task.get("number_data", {})
        # 判断通过 自定义函数的方式确认是否达到发送次数
        if "get_by_func" in number_rule and isinstance(number_rule["get_by_func"], str):
            f = getattr(self.task_obj, number_rule["get_by_func"], None)
            if f is not None and callable(f):
                res = f(self.task["id"], self.task["task_data"], number_data, self.result["push_data"])
                if isinstance(res, str):
                    self.result['stop_msg'] = res
                    self.result['check_stop_on'] = "number_rule_get_by_func"
                    return False

            # 只要是走了使用函数检查的，不再处理默认情况 change_fields 中不添加 number_data
            return True

        if "day_num" in number_rule and isinstance(number_rule["day_num"], int) and number_rule["day_num"] > 0:
            record_time = number_data.get("time", 0)
            if record_time < self.push_system.get_today_zero().timestamp():  # 昨日触发
                self.task["number_data"]["day_num"] = record_num = 0
                self.task["number_data"]["time"] = time.time()
                self.change_fields.add("number_data")
            else:
                record_num = self.task["number_data"].get("day_num")
            if record_num >= number_rule["day_num"]:
                self.result['stop_msg'] = "Exceeding the daily limit:{}".format(number_rule["day_num"])
                self.result['check_stop_on'] = "number_rule_day_num"
                return False

        if "total" in number_rule and isinstance(number_rule["total"], int) and number_rule["total"] > 0:
            record_total = number_data.get("total", 0)
            if record_total >= number_rule["total"]:
                self.result['stop_msg'] = "The maximum number of times the limit is exceeded:{}".format(
                    number_rule["total"])
                self.result['check_stop_on'] = "number_rule_total"
                return False

        return True

    def send_message(self, push_data: dict):
        self.result["do_send"] = True
        self.result["push_data"] = push_data
        # wx_account = []
        for sender_id in self.task["sender"]:
            conf = self.push_system.sd_cfg.get_by_id(sender_id)
            if conf is None:
                continue
            if not conf["used"]:
                self.result["send_data"][sender_id] = "The alarm channel {} is closed, skip sending".format(
                    conf["data"].get("title"))
                continue
            sd_cls = self.push_system.sender_cls(conf["sender_type"])
            if conf["sender_type"] == "weixin":
                res = sd_cls(conf).send_msg(
                    self.task_obj.to_weixin_msg(push_data, self.public_push_data),
                    self.task_obj.title
                )

            elif conf["sender_type"] == "mail":
                res = sd_cls(conf).send_msg(
                    self.task_obj.to_mail_msg(push_data, self.public_push_data),
                    self.task_obj.title
                )

            elif conf["sender_type"] == "webhook":
                res = sd_cls(conf).send_msg(
                    self.task_obj.to_web_hook_msg(push_data, self.public_push_data),
                    self.task_obj.title,
                )

            elif conf["sender_type"] == "feishu":
                res = sd_cls(conf).send_msg(
                    self.task_obj.to_feishu_msg(push_data, self.public_push_data),
                    self.task_obj.title
                )
            elif conf["sender_type"] == "dingding":
                res = sd_cls(conf).send_msg(
                    self.task_obj.to_dingding_msg(push_data, self.public_push_data),
                    self.task_obj.title
                )
            elif conf["sender_type"] == "sms":
                sm_type, sm_args = self.task_obj.to_sms_msg(push_data, self.public_push_data)
                if not sm_type or not sm_args:
                    continue
                sm_args = sms_msg_normalize(sm_args)
                res = sd_cls(conf).send_msg(sm_type, sm_args)

            # elif conf["sender_type"] == "wx_account":
            #     wx_account.append(conf)
            #     continue

            elif conf["sender_type"] == "tg":
                # public.print_log("tg -- 发送数据 {}".format(self.task_obj.to_tg_msg(push_data, self.public_push_data)))
                from mod.base.msg import TgMsg
                # Home CPU alarms<br>
                # >Server:xxx<br>
                # >IPAddress: xxx.xxx.xxx.xxx(Internet) xxx.xxx.xxx.xxx(Internal)<br>
                # >SendingTime: 2024-00-00 00:00:00<br>
                # >Notification type: High CPU usage alarm<br>
                # >Content of alarm: The average CPU usage of the machine in the last 5 minutes is 3.24%, which is higher than the alarm value 1%.

                try:
                    res = sd_cls(conf).send_msg(
                        # res = TgMsg().send_msg(
                        self.task_obj.to_tg_msg(push_data, self.public_push_data),
                        self.task_obj.title
                    )
                except:
                    public.print_log(public.get_error_info())
            else:
                continue
            if isinstance(res, str) and res.find("Traceback") != -1:
                self.result["send_data"][
                    sender_id] = "An error occurred during the execution of the message transmission, and the transmission was not successful"
            if isinstance(res, str):
                self.result["send_data"][sender_id] = res
            else:
                self.result["send_data"][sender_id] = 1
        #
        # if len(wx_account) > 0:
        #     sd_cls = self.push_system.sender_cls("wx_account")
        #     res = sd_cls(*wx_account).send_msg(self.task_obj.to_wx_account_msg(push_data, self.public_push_data))
        #     for i in wx_account:
        #         if isinstance(res, str):
        #             self.result["send_data"][i["id"]] = res
        #         else:
        #             self.result["send_data"][i["id"]] = 1


def push_by_task_keyword(source: str, keyword: str, push_data: Optional[dict] = None) -> Union[str, dict]:
    """
    通过关键字查询告警任务，并发送信息
    @param push_data:
    @param source:
    @type keyword:
    @return:
    """
    push_system = PushSystem()
    target_task = None
    for i in TaskConfig().config:
        if i["source"] == source and i["keyword"] == keyword:
            target_task = i
            break
    if not target_task:
        return "The task was not found"

    target_template = TaskTemplateConfig().get_by_id(target_task["template_id"])
    if not target_template["used"]:
        return "This task type has been banned"
    if not target_task['status']:
        return "The task has been stopped"

    return PushRunner(target_task, target_template, push_system, push_data)()


def push_by_task_id(task_id: str, push_data: Optional[dict] = None):
    """
    通过任务id触发告警 并 发送信息
    @param push_data:
    @param task_id:
    @return:
    """
    push_system = PushSystem()
    target_task = TaskConfig().get_by_id(task_id)
    if not target_task:
        return "The task was not found"

    target_template = TaskTemplateConfig().get_by_id(target_task["template_id"])
    if not target_template["used"]:
        return "This task type has been banned"
    if not target_task['status']:
        return "The task has been stopped"

    return PushRunner(target_task, target_template, push_system, push_data)()


def get_push_public_data():
    data = {
        'ip': get_server_ip(),
        'local_ip': get_network_ip(),
        'server_name': get_config_value('title'),
        'time': format_date(),
        'timestamp': int(time.time())}

    return data
