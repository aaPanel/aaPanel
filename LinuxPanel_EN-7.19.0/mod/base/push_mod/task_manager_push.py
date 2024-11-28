import json
import os
import sys
import threading
import time
from datetime import datetime, timedelta
from importlib import import_module
from typing import Tuple, Union, Optional, List

import psutil

from .send_tool import WxAccountMsg
from .base_task import BaseTask
from .mods import PUSH_DATA_PATH, TaskTemplateConfig
from .util import read_file, write_file, get_config_value, GET_CLASS


class _ProcessInfo:

    def __init__(self):
        self.data = None
        self.last_time = 0

    def __call__(self) -> list:
        if self.data is not None and time.time() - self.last_time < 60:
            return self.data

        try:
            import PluginLoader
            get_obj = GET_CLASS()
            get_obj.sort = "status"
            p_info = PluginLoader.plugin_run("task_manager", "get_process_list", get_obj)
        except:
            return []

        if isinstance(p_info, dict) and "process_list" in p_info and isinstance(
                p_info["process_list"], list):
            self._process_info = p_info["process_list"]
            self.last_time = time.time()
            return self._process_info
        else:
            return []


get_process_info = _ProcessInfo()


def have_task_manager_plugin():
    """
    通过文件判断是否有进程管理器
    """
    return os.path.exists("/www/server/panel/plugin/task_manager/task_manager_push.py")


def load_task_manager_template():
    if TaskTemplateConfig().get_by_id("60"):
        return None

    from .mods import load_task_template_by_config
    load_task_template_by_config([
        {
            "id": "60",
            "ver": "1",
            "used": True,
            "source": "task_manager_cpu",
            "title": "Task Manager CPU usage alarm",
            "load_cls": {
                "load_type": "path",
                "cls_path": "mod.base.push_mod.task_manager_push",
                "name": "TaskManagerCPUTask"
            },
            "template": {
                "field": [
                    {
                        "attr": "project",
                        "name": "project name",
                        "type": "select",
                        "items": {
                            "url": "plugin?action=a&name=task_manager&s=get_process_list_to_push"
                        }
                    },
                    {
                        "attr": "count",
                        "name": "Occupancy exceeded",
                        "type": "number",
                        "unit": "%",
                        "suffix": "trigger an alarm",
                        "default": 80,
                        "err_msg_prefix": "CPU occupancy"
                    },
                    {
                        "attr": "interval",
                        "name": "Interval",
                        "type": "number",
                        "unit": "second(s)",
                        "suffix": "monitor the detection conditions again",
                        "default": 600
                    }
                ],
                "sorted": [
                    [
                        "project"
                    ],
                    [
                        "count"
                    ],
                    [
                        "interval"
                    ]
                ],
            },
            "default": {
                "project": '',
                "count": 80,
                "interval": 600
            },
            "advanced_default": {
                "number_rule": {
                    "day_num": 3
                }
            },
            "send_type_list": [
                "dingding",
                "feishu",
                "mail",
                "weixin",
                "webhook",
                "tg",
            ],
            "unique": False
        },
        {
            "id": "61",
            "ver": "1",
            "used": True,
            "source": "task_manager_mem",
            "title": "Task Manager memory usage alarm",
            "load_cls": {
                "load_type": "path",
                "cls_path": "mod.base.push_mod.task_manager_push",
                "name": "TaskManagerMEMTask"
            },
            "template": {
                "field": [
                    {
                        "attr": "project",
                        "name": "project name",
                        "type": "select",
                        "items": {
                            "url": "plugin?action=a&name=task_manager&s=get_process_list_to_push"
                        }
                    },
                    {
                        "attr": "count",
                        "name": "The occupancy is more than",
                        "type": "number",
                        "unit": "MB",
                        "suffix": "trigger an alarm",
                        "default": None,
                        "err_msg_prefix": "Occupancy"
                    },
                    {
                        "attr": "interval",
                        "name": "Interval",
                        "type": "number",
                        "unit": "second(s)",
                        "suffix": "monitor the detection conditions again",
                        "default": 600
                    }
                ],
                "sorted": [
                    [
                        "project"
                    ],
                    [
                        "count"
                    ],
                    [
                        "interval"
                    ]
                ],
            },
            "default": {
                "project": '',
                "count": 80,
                "interval": 600
            },
            "advanced_default": {
                "number_rule": {
                    "day_num": 3
                }
            },
            "send_type_list": [
                "dingding",
                "feishu",
                "mail",
                "weixin",
                "webhook",
                "tg",
            ],
            "unique": False
        },
        {
            "id": "62",
            "ver": "1",
            "used": True,
            "source": "task_manager_process",
            "title": "Task Manager Process Overhead Alert",
            "load_cls": {
                "load_type": "path",
                "cls_path": "mod.base.push_mod.task_manager_push",
                "name": "TaskManagerProcessTask"
            },
            "template": {
                "field": [
                    {
                        "attr": "project",
                        "name": "project name",
                        "type": "select",
                        "items": {
                            "url": "plugin?action=a&name=task_manager&s=get_process_list_to_push"
                        }
                    },
                    {
                        "attr": "count",
                        "name": "Number of processes exceeds",
                        "type": "number",
                        "unit": "of them",
                        "suffix": "trigger an alarm",
                        "default": 20,
                        "err_msg_prefix": "NumberOfProcesses"
                    },
                    {
                        "attr": "interval",
                        "name": "Interval",
                        "type": "number",
                        "unit": "second(s)",
                        "suffix": "monitor the detection conditions again",
                        "default": 600
                    }
                ],
                "sorted": [
                    [
                        "project"
                    ],
                    [
                        "count"
                    ],
                    [
                        "interval"
                    ]
                ],
            },
            "default": {
                "project": '',
                "count": 80,
                "interval": 600
            },
            "advanced_default": {
                "number_rule": {
                    "day_num": 3
                }
            },
            "send_type_list": [
                "dingding",
                "feishu",
                "mail",
                "weixin",
                "webhook",
                "tg",
            ],
            "unique": False
        }
    ])


class TaskManagerCPUTask(BaseTask):

    def __init__(self):
        super().__init__()
        self.source_name = "task_manager_cpu"
        self.template_name = "Task Manager CPU usage alarm"
        # self.title = "Task Manager CPU usage alarm"

    def get_title(self, task_data: dict) -> str:
        return "Task Manager CPU usage alarm -- [{}]".format(task_data["project"])

    def check_task_data(self, task_data: dict) -> Union[dict, str]:
        if "interval" not in task_data or not isinstance(task_data["interval"], int):
            task_data["interval"] = 600
        if task_data["interval"] < 60:
            task_data["interval"] = 60
        if "count" not in task_data or not isinstance(task_data["count"], int):
            return "The check range is set incorrectly"
        if not 1 <= task_data["count"] < 100:
            return "The check range is set incorrectly"
        if not task_data["project"]:
            return "Please select a process"
        return task_data

    def get_keyword(self, task_data: dict) -> str:
        return task_data["project"]

    def get_push_data(self, task_id: str, task_data: dict) -> Optional[dict]:
        process_info = get_process_info()
        self.title = self.get_title(task_data)
        count = used = 0
        for p in process_info:
            if p["name"] == task_data['project']:
                used += p["cpu_percent"]
                count += 1 if "children" not in p else len(p["children"]) + 1

        if used <= task_data['count']:
            return None

        return {
            'msg_list':
                [
                    ">Notification type: Task Manager CPU usage alarm",
                    ">Alarm content:  There are {} processes with the process name [{}], and the proportion of CPU resources consumed is {}%, which is greater than the alarm threshold {}%.".format(
                        task_data['project'], count, used, task_data['count']
                    )
                ],
            "project": task_data['project'],
            "count": int(task_data['count'])
        }

    def filter_template(self, template: dict) -> Optional[dict]:
        if not have_task_manager_plugin():
            return None
        return template

    def to_sms_msg(self, push_data: dict, push_public_data: dict) -> Tuple[str, dict]:
        return '', {}

    def to_wx_account_msg(self, push_data: dict, push_public_data: dict) -> WxAccountMsg:
        msg = WxAccountMsg.new_msg()
        msg.thing_type = "Task Manager CPU usage alarm"
        if len(push_data["project"]) > 11:
            project = push_data["project"][:9] + ".."
        else:
            project = push_data["project"]

        msg.msg = "The CPU of {} exceeds {}%".format(project, push_data["count"])
        return msg


class TaskManagerMEMTask(BaseTask):
    def __init__(self):
        super().__init__()
        self.source_name = "task_manager_mem"
        self.template_name = "Task Manager memory usage alarm"
        # self.title = "Task Manager memory usage alarm"

    def get_title(self, task_data: dict) -> str:
        return "Task Manager memory usage alarm -- [{}].".format(task_data["project"])

    def check_task_data(self, task_data: dict) -> Union[dict, str]:
        if not task_data["project"]:
            return "Please select a process"
        if "interval" not in task_data or not isinstance(task_data["interval"], int):
            task_data["interval"] = 600
        task_data["interval"] = max(60, task_data["interval"])
        if "count" not in task_data or not isinstance(task_data["count"], int):
            return "The check range is set incorrectly"
        if task_data["count"] < 1:
            return "The check range is set incorrectly"
        return task_data

    def get_keyword(self, task_data: dict) -> str:
        return task_data["project"]

    def get_push_data(self, task_id: str, task_data: dict) -> Optional[dict]:
        process_info = get_process_info()
        self.title = self.get_title(task_data)

        used = count = 0
        for p in process_info:
            if p["name"] == task_data['project']:
                used += p["memory_used"]
                count += 1 if "children" not in p else len(p["children"]) + 1

        if used <= task_data['count'] * 1024 * 1024:
            return None
        return {
            'msg_list': [
                ">Notification type: Task Manager memory usage alarm",
                ">Alarm content:  There are {} processes with process name [{}], and the memory resources consumed are {}MB, which is greater than the alarm threshold {}MB.".format(
                    task_data['project'], count, int(used / 1024 / 1024), task_data['count']
                )
            ],
            "project": task_data['project']
        }

    def filter_template(self, template: dict) -> Optional[dict]:
        if not have_task_manager_plugin():
            return None
        return template

    def to_sms_msg(self, push_data: dict, push_public_data: dict) -> Tuple[str, dict]:
        return '', {}

    def to_wx_account_msg(self, push_data: dict, push_public_data: dict) -> WxAccountMsg:
        msg = WxAccountMsg.new_msg()
        if len(push_data["project"]) > 11:
            project = push_data["project"][:9] + ".."
        else:
            project = push_data["project"]
        msg.thing_type = "Task Manager memory usage alarm"
        msg.msg = "The memory of {} exceeds the alarm value".format(project)
        return msg


class TaskManagerProcessTask(BaseTask):
    def __init__(self):
        super().__init__()
        self.source_name = "task_manager_process"
        self.template_name = "Task Manager Process Overhead Alert"
        self.title = "Task Manager Process Overhead Alert"

    def get_title(self, task_data: dict) -> str:
        return "Task Manager Process Overhead Alert [{}]".format(task_data["project"])

    def check_task_data(self, task_data: dict) -> Union[dict, str]:
        if not task_data["project"]:
            return "Please select a process"
        if "interval" not in task_data or not isinstance(task_data["interval"], int):
            task_data["interval"] = 600
        task_data["interval"] = max(60, task_data["interval"])
        if "count" not in task_data or not isinstance(task_data["count"], int):
            return "The check range is set incorrectly"
        if task_data["count"] < 1:
            return "The check range is set incorrectly"
        return task_data

    def get_keyword(self, task_data: dict) -> str:
        return task_data["project"]

    def get_push_data(self, task_id: str, task_data: dict) -> Optional[dict]:
        process_info = get_process_info()
        count = 0
        for p in process_info:
            if p["name"] == task_data['project']:
                count += 1 if "children" not in p else len(p["children"]) + 1

        if count <= task_data['count']:
            return None

        return {
            'msg_list':
                [
                    ">Notification type: Task Manager Process Overhead Alert",
                    ">Alarm content:  There are {} processes with process name {}, which is greater than the alarm threshold.".format(
                        task_data['project'], count, task_data['count']
                    )
                ],
            "project": task_data['project'],
            "count": task_data['count'],
        }

    def filter_template(self, template: dict) -> Optional[dict]:
        if not have_task_manager_plugin():
            return None
        return template

    def to_sms_msg(self, push_data: dict, push_public_data: dict) -> Tuple[str, dict]:
        return '', {}

    def to_wx_account_msg(self, push_data: dict, push_public_data: dict) -> WxAccountMsg:
        msg = WxAccountMsg.new_msg()
        msg.thing_type = "Task Manager Process Overhead Alert"
        if len(push_data["project"]) > 11:
            project = push_data["project"][:9] + ".."
        else:
            project = push_data["project"]

        if push_data["count"] > 100:  # 节省字数
            push_data["count"] = "LIMIT"

        msg.msg = "{} has more children than {}".format(project, push_data["count"])
        return msg


class ViewMsgFormat(object):
    _FORMAT = {
        "60": (
            lambda x: "<span>Process: The CPU occupation of {} is more than {}% triggered</span>".format(
                x.get("project"), x.get("count")
            )
        ),
        "61": (
            lambda x: "<span>Process: Triggered when the memory usage of {} exceeds {}MB</span>".format(
                x.get("project"), x.get("count")
            )
        ),
        "62": (
            lambda x: "<span>Process: Triggered when the number of child processes exceeds {}</span>".format(
                x.get("project"), x.get("count")
            )
        ),
    }

    def get_msg(self, task: dict) -> Optional[str]:
        if task["template_id"] in self._FORMAT:
            return self._FORMAT[task["template_id"]](task["task_data"])
        return None
