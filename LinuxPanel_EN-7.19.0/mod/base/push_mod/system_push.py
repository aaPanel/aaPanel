
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
from .mods import PUSH_DATA_PATH
from .util import read_file, write_file, get_config_value


from .system import WAIT_TASK_LIST

try:
    if "/www/server/panel/class" not in sys.path:
        sys.path.insert(0, "/www/server/panel/class")
    from panel_msg.collector import SitePushMsgCollect, SystemPushMsgCollect
except ImportError:
    SitePushMsgCollect = None
    SystemPushMsgCollect = None


def _get_panel_name() -> str:
    data = get_config_value("title")  # 若获得别名，则使用别名
    if data == "":
        data = "aaPanel"
    return data


class PanelSysDiskTask(BaseTask):

    def __init__(self):
        super().__init__()
        self.source_name = "system_disk"
        self.template_name = "Home disk alerts"
        self.title = "Home disk alerts"

        self.wx_msg = ""

    def get_title(self, task_data: dict) -> str:
        return "Home disk alerts -- Mount directory[{}]".format(task_data["project"])

    def check_task_data(self, task_data: dict) -> Union[dict, str]:
        if task_data["project"] not in [i[0] for i in self._get_disk_name()]:
            return "The specified disk does not exist"
        if not (isinstance(task_data['cycle'], int) and task_data['cycle'] in (1, 2)):
            return "The type parameter is incorrect"
        if not (isinstance(task_data['count'], int) and task_data['count'] >= 1):
            return "The threshold parameter is incorrect"
        if task_data['cycle'] == 2 and task_data['count'] >= 100:
            return "The threshold parameter is incorrect, and the set check range is incorrect"
        task_data['interval'] = 600
        return task_data

    @staticmethod
    def _get_disk_name() -> list:
        """获取硬盘挂载点"""
        if "/www/server/panel" not in sys.path:
            sys.path.insert(0, "/www/server/panel")

        system_modul = import_module('.system', package="class")
        system = getattr(system_modul, "system")

        disk_info = system.GetDiskInfo2(None, human=False)

        return [(d.get("path"), d.get("size")[0]) for d in disk_info]

    @staticmethod
    def _get_disk_info() -> list:
        """获取硬盘挂载点"""
        if "/www/server/panel" not in sys.path:
            sys.path.insert(0, "/www/server/panel")

        system_modul = import_module('.system', package="class")
        system = getattr(system_modul, "system")

        disk_info = system.GetDiskInfo2(None, human=False)

        return disk_info

    def get_keyword(self, task_data: dict) -> str:
        return task_data["project"]

    def get_push_data(self, task_id: str, task_data: dict) -> Optional[dict]:
        disk_info = self._get_disk_info()
        unsafe_disk_list = []

        for d in disk_info:
            if task_data["project"] != d["path"]:
                continue
            free = int(d["size"][2]) / 1048576
            proportion = int(d["size"][3] if d["size"][3][-1] != "%" else d["size"][3][:-1])

            if task_data["cycle"] == 1 and free < task_data["count"]:
                unsafe_disk_list.append(
                    "The remaining capacity of the disk mounted on {} is {}G, which is less than the alarm value {}G.".format(
                        d["path"], round(free, 2), task_data["count"])
                )
                self.wx_msg = "The remaining capacity is less than {}G".format(task_data["count"])

            elif task_data["cycle"] == 2 and proportion > task_data["count"]:
                unsafe_disk_list.append(
                    "The used capacity of the disk mounted on {} is {}%, which is greater than the alarm value {}%.".format(
                        d["path"], round(proportion, 2), task_data["count"])
                )
                self.wx_msg = "Occupancy greater than {}%".format(task_data["count"])

        if len(unsafe_disk_list) == 0:
            return None

        return {
            "msg_list": [
                ">Notification type: Disk Balance Alert",
                ">Alarm content:\n" + "\n".join(unsafe_disk_list)
            ]
        }

    def filter_template(self, template: dict) -> Optional[dict]:
        for (path, total_size) in self._get_disk_name():
            template["field"][0]["items"].append({
                "title": "[{}] disk".format(path),
                "value": path,
                "count_default": round((int(total_size) * 0.2) / 1024 / 1024, 1)
            })
        return template

    def to_sms_msg(self, push_data: dict, push_public_data: dict) -> Tuple[str, dict]:
        return 'machine_exception|Disk Balance Alert', {
            'name': _get_panel_name(),
            'type': "Insufficient disk space",
        }

    def to_wx_account_msg(self, push_data: dict, push_public_data: dict) -> WxAccountMsg:
        msg = WxAccountMsg.new_msg()
        msg.thing_type = "Home disk alerts"
        if len(self.wx_msg) > 20:
            self.wx_msg = self.wx_msg[:17] + "..."
        msg.msg = self.wx_msg
        return msg


class PanelSysCPUTask(BaseTask):

    def __init__(self):
        super().__init__()
        self.source_name = "system_cpu"
        self.template_name = "Home CPU alarms"
        self.title = "Home CPU alarms"

        self.cpu_count = 0

        self._tip_file = "{}/system_cpu.tip".format(PUSH_DATA_PATH)
        self._tip_data: Optional[List[Tuple[float, float]]] = None

    @property
    def cache_list(self) -> List[Tuple[float, float]]:
        if self._tip_data is not None:
            return self._tip_data
        try:
            self._tip_data = json.loads(read_file(self._tip_file))
        except:
            self._tip_data = []
        return self._tip_data

    def save_cache_list(self):
        write_file(self._tip_file, json.dumps(self.cache_list))

    def check_task_data(self, task_data: dict) -> Union[dict, str]:
        if not (isinstance(task_data['cycle'], int) and task_data['cycle'] >= 1):
            return "The time parameter is incorrect"
        if not (isinstance(task_data['count'], int) and task_data['count'] >= 1):
            return "Threshold parameter error, at least 1%"
        task_data['interval'] = 60
        return task_data

    def get_keyword(self, task_data: dict) -> str:
        return "system_cpu"

    def get_push_data(self, task_id: str, task_data: dict) -> Optional[dict]:
        expiration = datetime.now() - timedelta(seconds=task_data["cycle"] * 60 + 10)
        for i in range(len(self.cache_list) - 1, -1, -1):
            data_time, _ = self.cache_list[i]
            if datetime.fromtimestamp(data_time) < expiration:
                del self.cache_list[i]

        # 记录下次的
        def thread_get_cpu_data():
            self.cache_list.append((time.time(), psutil.cpu_percent(10)))
            self.save_cache_list()

        thread_active = threading.Thread(target=thread_get_cpu_data, args=())
        thread_active.start()
        WAIT_TASK_LIST.append(thread_active)

        if len(self.cache_list) < task_data["cycle"]:  # 小于指定次数不推送
            return None

        if len(self.cache_list) > 0:
            avg_data = sum(i[1] for i in self.cache_list) / len(self.cache_list)
        else:
            avg_data = 0

        if avg_data < task_data["count"]:
            return None
        else:
            self.cache_list.clear()
        self.cpu_count = round(avg_data, 2)
        s_list = [
            ">Notification type: High CPU usage alarm",
            ">Content of alarm: The average CPU usage of the machine in the last {} minutes is {}%, which is higher than the alarm value {}%.".format(
                task_data["cycle"], round(avg_data, 2), task_data["count"]),
        ]

        return {
            "msg_list": s_list,
        }

    def filter_template(self, template: dict) -> Optional[dict]:
        return template

    def to_sms_msg(self, push_data: dict, push_public_data: dict) -> Tuple[str, dict]:
        return 'machine_exception|High CPU usage alarm', {
            'name': _get_panel_name(),
            'type': "High CPU usage",
        }

    def to_wx_account_msg(self, push_data: dict, push_public_data: dict) -> WxAccountMsg:
        msg = WxAccountMsg.new_msg()
        msg.thing_type = "Home CPU alarms"
        msg.msg = "The CPU usage of the host is exceeded:{}%".format(self.cpu_count)
        msg.next_msg = "Please log in to the panel to view the host status"
        return msg


class PanelSysLoadTask(BaseTask):

    def __init__(self):
        super().__init__()
        self.source_name = "system_load"
        self.template_name = "Home load alerts"
        self.title = "Home load alerts"

        self.avg_data = 0

    def check_task_data(self, task_data: dict) -> Union[dict, str]:
        if not (isinstance(task_data['cycle'], int) and task_data['cycle'] >= 1):
            return "The time parameter is incorrect"
        if not (isinstance(task_data['count'], int) and task_data['count'] >= 1):
            return "Threshold parameter error, at least 1%"
        task_data['interval'] = 60 * task_data['cycle']
        return task_data

    def get_keyword(self, task_data: dict) -> str:
        return "system_load"

    def get_push_data(self, task_id: str, task_data: dict) -> Optional[dict]:
        now_load = os.getloadavg()
        cpu_count = psutil.cpu_count()
        now_load = [i / (cpu_count * 2) * 100 for i in now_load]
        need_push = False
        avg_data = 0
        if task_data["cycle"] == 15 and task_data["count"] < now_load[2]:
            avg_data = now_load[2]
            need_push = True
        elif task_data["cycle"] == 5 and task_data["count"] < now_load[1]:
            avg_data = now_load[1]
            need_push = True
        elif task_data["cycle"] == 1 and task_data["count"] < now_load[0]:
            avg_data = now_load[0]
            need_push = True

        if need_push is False:
            return None

        self.avg_data = avg_data

        return {
            "msg_list": [
                ">Notification type: Alarm when the load exceeds the standard",
                ">Content of alarm: The average load factor of the machine in the last {} minutes is {}%, which is higher than the alarm value of {}%.".format(
                    task_data["cycle"], round(avg_data, 2), task_data["count"]),
            ]
        }

    def filter_template(self, template: dict) -> Optional[dict]:
        return template

    def to_sms_msg(self, push_data: dict, push_public_data: dict) -> Tuple[str, dict]:
        return 'machine_exception|Alarm when the load exceeds the standard', {
            'name': _get_panel_name(),
            'type': "The average load is too high",
        }

    def to_wx_account_msg(self, push_data: dict, push_public_data: dict) -> WxAccountMsg:
        msg = WxAccountMsg.new_msg()
        msg.thing_type = "Home load alerts"
        msg.msg = "The host load exceeds:{}%".format(round(self.avg_data, 2))
        msg.next_msg = "Please log in to the panel to view the host status"
        return msg


class PanelSysMEMTask(BaseTask):

    def __init__(self):
        super().__init__()
        self.source_name = "system_mem"
        self.template_name = "Home memory alarms"
        self.title = "Home memory alarms"

        self.wx_data = 0

        self._tip_file = "{}/system_mem.tip".format(PUSH_DATA_PATH)
        self._tip_data: Optional[List[Tuple[float, float]]] = None

    @property
    def cache_list(self) -> List[Tuple[float, float]]:
        if self._tip_data is not None:
            return self._tip_data
        try:
            self._tip_data = json.loads(read_file(self._tip_file))
        except:
            self._tip_data = []
        return self._tip_data

    def save_cache_list(self):
        write_file(self._tip_file, json.dumps(self.cache_list))

    def check_task_data(self, task_data: dict) -> Union[dict, str]:
        if not (isinstance(task_data['cycle'], int) and task_data['cycle'] >= 1):
            return "The number parameter is incorrect"
        if not (isinstance(task_data['count'], int) and task_data['count'] >= 1):
            return "Threshold parameter error, at least 1%"
        task_data['interval'] = task_data['cycle'] * 60
        return task_data

    def get_keyword(self, task_data: dict) -> str:
        return "system_mem"

    def get_push_data(self, task_id: str, task_data: dict) -> Optional[dict]:
        mem = psutil.virtual_memory()
        real_used: float = (mem.total - mem.free - mem.buffers - mem.cached) / mem.total
        stime = datetime.now()
        expiration = stime - timedelta(seconds=task_data["cycle"] * 60 + 10)

        self.cache_list.append((stime.timestamp(), real_used))

        for i in range(len(self.cache_list) - 1, -1, -1):
            data_time, _ = self.cache_list[i]
            if datetime.fromtimestamp(data_time) < expiration:
                del self.cache_list[i]

        avg_data = sum(i[1] for i in self.cache_list) / len(self.cache_list)

        if avg_data * 100 < task_data["count"]:
            self.save_cache_list()
            return None
        else:
            self.cache_list.clear()
            self.save_cache_list()
        self.wx_data = round(avg_data * 100, 2)
        return {
            'msg_list': [
                ">Notification type: High memory usage alarm",
                ">Content of alarm: The average memory usage of the machine in the last {} minutes is {}%, which is higher than the alarm value {}%.".format(
                    task_data["cycle"], round(avg_data * 100, 2), task_data["count"]),
            ]
        }

    def filter_template(self, template: dict) -> Optional[dict]:
        return template

    def to_sms_msg(self, push_data: dict, push_public_data: dict) -> Tuple[str, dict]:
        return 'machine_exception|High memory usage alarm', {
            'name': _get_panel_name(),
            'type': "High memory usage",
        }

    def to_wx_account_msg(self, push_data: dict, push_public_data: dict) -> WxAccountMsg:
        msg = WxAccountMsg.new_msg()
        msg.thing_type = "Home memory alarms"
        msg.msg = "Host memory usage exceeded: {}%".format(self.wx_data)
        msg.next_msg = "Please log in to the panel to view the host status"
        return msg


class ViewMsgFormat(object):
    _FORMAT = {
        "20": (
            lambda x: "<span>Triggered by {} disk mounted on {}</span>".format(
                x.get("project"),
                "The margin is less than %.1f G" % round(x.get("count"), 1) if x.get("cycle") == 1 else "ake up more than %d%%" % x.get("count"),
            )
        ),
        "21": (
            lambda x: "<span>Triggers when the average CPU usage exceeds {}% in {} minutes</span>".format(
                x.get("count"), x.get("cycle")
            )
        ),
        "22": (
            lambda x: "<span>Triggered by an average load exceeding {}% in {} minutes</span>".format(
                x.get("count"), x.get("cycle")
            )
        ),
        "23": (
            lambda x: "<span>Triggered if the memory usage exceeds {}% within {} minutes</span>".format(
                x.get("count"), x.get("cycle")
            )
        )
    }

    def get_msg(self, task: dict) -> Optional[str]:
        if task["template_id"] in self._FORMAT:
            return self._FORMAT[task["template_id"]](task["task_data"])
        return None