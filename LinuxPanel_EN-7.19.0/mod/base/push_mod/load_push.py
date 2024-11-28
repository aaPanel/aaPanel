import json
import os
import time
from typing import Tuple, Union, Optional

from .mods import PUSH_DATA_PATH, TaskTemplateConfig
from .send_tool import WxAccountMsg
from .base_task import BaseTask
from .util import read_file, DB, GET_CLASS, write_file


class NginxLoadTask(BaseTask):
    def __init__(self):
        super().__init__()
        self.source_name = "nginx_load_push"
        self.template_name = "Load balancing alarm"
        # self.title = "Load balancing alarm"
        self._tip_counter = None

    @property
    def tip_counter(self) -> dict:
        if self._tip_counter is not None:
            return self._tip_counter
        tip_counter = '{}/load_balance_push.json'.format(PUSH_DATA_PATH)
        if os.path.exists(tip_counter):
            try:
                self._tip_counter = json.loads(read_file(tip_counter))
            except json.JSONDecodeError:
                self._tip_counter = {}
        else:
            self._tip_counter = {}
        return self._tip_counter

    def save_tip_counter(self):
        tip_counter = '{}/load_balance_push.json'.format(PUSH_DATA_PATH)
        write_file(tip_counter, json.dumps(self.tip_counter))

    def get_title(self, task_data: dict) -> str:
        if task_data["project"] == "all":
            return "Load balancing alarm"
        return "Load balancing alarm -- [{}] ".format(task_data["project"])

    def check_task_data(self, task_data: dict) -> Union[dict, str]:
        all_upstream_name = DB("upstream").field("name").select()
        if isinstance(all_upstream_name, str) and all_upstream_name.startswith("error"):
            return 'Alarms cannot be set without load balancing configuration'
        all_upstream_name = [i["name"] for i in all_upstream_name]
        if not bool(all_upstream_name):
            return 'Alarms cannot be set without load balancing configuration'
        if task_data["project"] not in all_upstream_name and task_data["project"] != "all":
            return 'Without this load balancer configuration, alarms cannot be set'

        cycle = []
        for i in task_data["cycle"].split("|"):
            if bool(i) and i.isdecimal():
                code = int(i)
                if 100 <= code < 600:
                    cycle.append(str(code))
        if not bool(cycle):
            return 'If no error code is specified, the alarm cannot be set'

        task_data["cycle"] = "|".join(cycle)
        return task_data

    def get_keyword(self, task_data: dict) -> str:
        return task_data["project"]

    def _check_func(self, upstream_name: str, codes: str) -> list:
        import PluginLoader
        get_obj = GET_CLASS()
        get_obj.upstream_name = upstream_name
        # 调用外部插件检查负载均衡的健康状况
        upstreams = PluginLoader.plugin_run("load_balance", "get_check_upstream", get_obj)
        access_codes = [int(i) for i in codes.split("|") if bool(i.strip())]
        res_list = []
        for upstream in upstreams:
            # 检查每个节点，返回有问题的节点信息
            res = upstream.check_nodes(access_codes, return_nodes=True)
            for ping_url in res:
                if ping_url in self.tip_counter:
                    self.tip_counter[ping_url].append(int(time.time()))
                    idx = 0
                    for i in self.tip_counter[ping_url]:
                        # 清理超过4分钟的记录
                        if time.time() - i > 60 * 4:
                            idx += 1
                    self.tip_counter[ping_url] = self.tip_counter[ping_url][idx:]
                    print("self.tip_counter[ping_url]",self.tip_counter[ping_url])
                    # 如果一个节点连续三次出现在告警列表中，则视为需要告警
                    if len(self.tip_counter[ping_url]) >= 3:
                        res_list.append(ping_url)
                        self.tip_counter[ping_url] = []
                else:
                    self.tip_counter[ping_url] = [int(time.time()), ]
        self.save_tip_counter()
        return res_list


    def get_push_data(self, task_id: str, task_data: dict) -> Optional[dict]:
        err_nodes = self._check_func(task_data["project"], task_data["cycle"])
        if not err_nodes:
            return None
        pj = "load balancing:【{}】".format(task_data["project"]) if task_data["project"] != "all" else "load balancing"
        nodes = '、'.join(err_nodes)
        self.title = self.get_title(task_data)
        return {
            "msg_list": [
                ">Notification type: Enterprise Edition load balancing alarm",
                ">Content of alarm: <font color=#ff0000>{}The node [{}] under the configuration has access error, please pay attention to the node situation in time and deal with it.</font> ".format(
                    pj, nodes),
            ],
            "pj": pj,
            "nodes": nodes
        }

    def filter_template(self, template: dict) -> Optional[dict]:
        if not os.path.exists("/www/server/panel/plugin/load_balance/load_balance_main.py"):
            return None
        all_upstream = DB("upstream").field("name").select()
        if isinstance(all_upstream, str) and all_upstream.startswith("error"):
            return None
        all_upstream_name = [i["name"] for i in all_upstream]
        if not all_upstream_name:
            return None
        for name in all_upstream_name:
            template["field"][0]["items"].append({
                "title": name,
                "value": name
            })
        return template

    def to_sms_msg(self, push_data: dict, push_public_data: dict) -> Tuple[str, dict]:
        return '', {}

    def to_wx_account_msg(self, push_data: dict, push_public_data: dict) -> WxAccountMsg:
        msg = WxAccountMsg.new_msg()
        msg.thing_type = "Load balancing alarm"
        msg.msg = "If the node is abnormal, log in to the panel"
        return msg

    def task_config_create_hook(self, task: dict) -> None:
        old_config_file = "/www/server/panel/class/push/push.json"
        try:
            old_config = json.loads(read_file(old_config_file))
        except:
            return
        if "load_balance_push" not in old_config:
            old_config["load_balance_push"] = {}
        old_data = {
            "push_count": task["number_rule"].get("day_num", 2),
            "cycle": task["task_data"].get("cycle", "200|301|302|403|404"),
            "interval": task["task_data"].get("interval", 60),
            "title": task["title"],
            "status": task['status'],
            "module": ",".join(task["sender"])
        }
        for k, v in old_config["load_balance_push"].items():
            if v["project"] == task["task_data"]["project"]:
                v.update(old_data)
        else:
            old_data["project"] = task["task_data"]["project"]
            old_config["load_balance_push"][int(time.time())] = old_data

        write_file(old_config_file, json.dumps(old_config))

    def task_config_update_hook(self, task: dict) -> None:
        return self.task_config_create_hook(task)

    def task_config_remove_hook(self, task: dict) -> None:
        old_config_file = "/www/server/panel/class/push/push.json"
        try:
            old_config = json.loads(read_file(old_config_file))
        except:
            return
        if "load_balance_push" not in old_config:
            old_config["load_balance_push"] = {}
        old_config["load_balance_push"] = {
            k: v for k, v in old_config["load_balance_push"].items()
            if v["project"] != task["task_data"]["project"]
        }


def load_load_template():
    if TaskTemplateConfig().get_by_id("50"):
        return None

    from .mods import load_task_template_by_config
    load_task_template_by_config(
        [{
            "id": "50",
            "ver": "1",
            "used": True,
            "source": "nginx_load_push",
            "title": "load balancing",
            "load_cls": {
                "load_type": "path",
                "cls_path": "mod.base.push_mod.load_push",
                "name": "NginxLoadTask"
            },
            "template": {
                "field": [
                    {
                        "attr": "project",
                        "name": "The name of the payload",
                        "type": "select",
                        "default": "all",
                        "unit": "",
                        "suffix": (
                            "<i style='color: #999;font-style: initial;font-size: 12px;margin-right: 5px'>*</i>"
                            "<span style='color:#999'>If a node fails to access a node in the selected load configuration, an alarm is triggered</span>"
                        ),
                        "items": [
                            {
                                "title": "All configured loads",
                                "value": "all"
                            }
                        ]
                    },
                    {
                        "attr": "cycle",
                        "name": "The status code of the success",
                        "type": "textarea",
                        "unit": "",
                        "suffix": (
                            "<br><i style='color: #999;font-style: initial;font-size: 12px;margin-right: 5px'>*</i>"
                            "<span style='color:#999'>Status codes are separated by vertical bars, for example:200|301|302|403|404</span>"
                        ),
                        "width": "400px",
                        "style": {
                            'height': '70px',
                        },
                        "default": "200|301|302|403|404"
                    }
                ],
                "sorted": [
                    [
                        "project"
                    ],
                    [
                        "cycle"
                    ]
                ],
            },
            "default": {
                "project": "all",
                "cycle": "200|301|302|403|404"
            },
            "advanced_default": {
                "number_rule": {
                    "day_num": 3
                }
            },
            "send_type_list": [
                "wx_account",
                "dingding",
                "feishu",
                "mail",
                "weixin",
                "webhook",
                "tg",
            ],
            "unique": False
        }]
    )


class ViewMsgFormat(object):

    @staticmethod
    def get_msg(task: dict) -> Optional[str]:
        if task["template_id"] == "50":
            return "<span>When the node access is abnormal, the alarm message is pushed (it is not pushed after {} times per day)<span>".format(
                task.get("number_rule", {}).get("day_num"))
        return None
