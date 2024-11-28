import json
import os
import re
from datetime import datetime, timedelta
from typing import Tuple, Union, Optional, Iterator

from .send_tool import WxAccountMsg
from .base_task import BaseTask
from .mods import TaskTemplateConfig
from .util import read_file


def rsync_ver_is_38() -> Optional[bool]:
    """
    检查rsync的版本是否为3.8。
    该函数不接受任何参数。
    返回值：
    - None: 如果无法确定rsync的版本或文件不存在。
    - bool: 如果版本确定为3.8，则返回True；否则返回False。
    """
    push_file = "/www/server/panel/plugin/rsync/rsync_push.py"
    if not os.path.exists(push_file):
        return None
    ver_info_file = "/www/server/panel/plugin/rsync/info.json"
    if not os.path.exists(ver_info_file):
        return None
    try:
        info = json.loads(read_file(ver_info_file))
    except (json.JSONDecodeError, TypeError):
        return None
    ver = info["versions"]
    ver_tuples = [int(i) for i in ver.split(".")]
    if len(ver_tuples) < 3:
        ver_tuples = ver_tuples.extend([0] * (3 - len(ver_tuples)))
    if ver_tuples[0] < 3:
        return None
    if ver_tuples[1] <= 8 and ver_tuples[0] == 3:
        return True

    return False


class Rsync38Task(BaseTask):

    def __init__(self):
        super().__init__()
        self.source_name = "rsync_push"
        self.template_name = "File synchronization alarm"
        self.title = "File synchronization alarm"

    def check_task_data(self, task_data: dict) -> Union[dict, str]:
        if "interval" not in task_data or not isinstance(task_data["interval"], int):
            task_data["interval"] = 600
        return task_data

    def get_keyword(self, task_data: dict) -> str:
        return "rsync_push"

    def get_push_data(self, task_id: str, task_data: dict) -> Optional[dict]:
        has_err = self._check(task_data.get("interval", 600))
        if not has_err:
            return None

        return {
            "msg_list": [
                ">Notification type: File synchronization alarm",
                ">Content of alarm: <font color=#ff0000>If an error occurs during file synchronization, please pay attention to the file synchronization situation and handle it in a timely manner.</font> ",
            ]
        }

    @staticmethod
    def _check(interval: int) -> bool:
        if not isinstance(interval, int):
            return False
        start_time = datetime.now() - timedelta(seconds=interval * 1.2)
        log_file = "{}/plugin/rsync/lsyncd.log".format("/www/server/panel")
        if not os.path.exists(log_file):
            return False
        return LogChecker(log_file=log_file, start_time=start_time)()

    def check_time_rule(self, time_rule: dict) -> Union[dict, str]:
        if "send_interval" not in time_rule or not isinstance(time_rule["interval"], int):
            time_rule["send_interval"] = 3 * 60
        if time_rule["send_interval"] < 60:
            time_rule["send_interval"] = 60
        return time_rule

    def filter_template(self, template: dict) -> Optional[dict]:
        res = rsync_ver_is_38()
        if res is None:
            return None
        if res:
            return template
        else:
            return None

    def to_sms_msg(self, push_data: dict, push_public_data: dict) -> Tuple[str, dict]:
        return '', {}

    def to_wx_account_msg(self, push_data: dict, push_public_data: dict) -> WxAccountMsg:
        msg = WxAccountMsg.new_msg()
        msg.thing_type = "File synchronization alarm"
        msg.msg = "There was an error in the synchronization. Please keep an eye on the synchronization"
        return msg


class Rsync39Task(BaseTask):

    def __init__(self):
        super().__init__()
        self.source_name = "rsync_push"
        self.template_name = "File synchronization alarm"
        self.title = "File synchronization alarm"

    def check_task_data(self, task_data: dict) -> Union[dict, str]:
        if "interval" not in task_data or not isinstance(task_data["interval"], int):
            task_data["interval"] = 600
        return task_data

    def get_keyword(self, task_data: dict) -> str:
        return "rsync_push"

    def get_push_data(self, task_id: str, task_data: dict) -> Optional[dict]:
        """
        不返回数据，以实时触发为主
        """
        return None

    def check_time_rule(self, time_rule: dict) -> Union[dict, str]:
        if "send_interval" not in time_rule or not isinstance(time_rule["send_interval"], int):
            time_rule["send_interval"] = 3 * 60
        if time_rule["send_interval"] < 60:
            time_rule["send_interval"] = 60
        return time_rule

    def filter_template(self, template: dict) -> Optional[dict]:
        res = rsync_ver_is_38()
        if res is None:
            return None
        if res is False:
            return template
        else:
            return None

    def to_sms_msg(self, push_data: dict, push_public_data: dict) -> Tuple[str, dict]:
        return '', {}

    def to_wx_account_msg(self, push_data: dict, push_public_data: dict) -> WxAccountMsg:
        task_name = push_data.get("task_name", None)
        msg = WxAccountMsg.new_msg()
        msg.thing_type = "File synchronization alarm"
        if task_name:
            msg.msg = "An error occurred on file synchronization task {}".format(task_name)
        else:
            msg.msg = "There was an error in the synchronization. Please keep an eye on the synchronization"
        return msg


class LogChecker:
    """
    排序查询并获取日志内容
    """
    rep_time = re.compile(r'(?P<target>(\w{3}\s+){2}(\d{1,2})\s+(\d{2}:?){3}\s+\d{4})')
    format_str = '%a %b %d %H:%M:%S %Y'
    err_datetime = datetime.fromtimestamp(0)
    err_list = ("error", "Error", "ERROR", "exitcode = 10", "failed")

    def __init__(self, log_file: str, start_time: datetime):
        self.log_file = log_file
        self.start_time = start_time
        self.is_over_time = None  # None:还没查到时间，未知， False: 可以继续网上查询， True:比较早的数据了，不再向上查询
        self.has_err = False  # 目前已查询的内容中是否有报错信息

    def _format_time(self, log_line) -> Optional[datetime]:
        try:
            date_str_res = self.rep_time.search(log_line)
            if date_str_res:
                time_str = date_str_res.group("target")
                return datetime.strptime(time_str, self.format_str)
        except Exception:
            return self.err_datetime
        return None

    # 返回日志内容
    def __call__(self):
        _buf = b""
        file_size, fp = os.stat(self.log_file).st_size - 1, open(self.log_file, mode="rb")
        fp.seek(-1, 2)
        while file_size:
            read_size = min(1024, file_size)
            fp.seek(-read_size, 1)
            buf: bytes = fp.read(read_size) + _buf
            fp.seek(-read_size, 1)
            if file_size > 1024:
                idx = buf.find(ord("\n"))
                _buf, buf = buf[:idx], buf[idx + 1:]
            for i in self._get_log_line_from_buf(buf):
                self._check(i)
                if self.is_over_time:
                    return self.has_err
            file_size -= read_size
        return False

    # 从缓冲中读取日志
    @staticmethod
    def _get_log_line_from_buf(buf: bytes) -> Iterator[str]:
        n, m = 0, 0
        buf_len = len(buf) - 1
        for i in range(buf_len, -1, -1):
            if buf[i] == ord("\n"):
                log_line = buf[buf_len + 1 - m: buf_len - n + 1].decode("utf-8")
                yield log_line
                n = m = m + 1
            else:
                m += 1
        yield buf[0: buf_len - n + 1].decode("utf-8")

    # 格式化并筛选查询条件
    def _check(self, log_line: str) -> None:
        # 筛选日期
        for err in self.err_list:
            if err in log_line:
                self.has_err = True

        ck_time = self._format_time(log_line)
        if ck_time:
            self.is_over_time = self.start_time > ck_time


def load_rsync_template():
    """
    加载rsync模板
    """
    if TaskTemplateConfig().get_by_id("40"):
        return None
    from .mods import load_task_template_by_config
    load_task_template_by_config(
        [{
            "id": "40",
            "ver": "1",
            "used": True,
            "source": "rsync_push",
            "title": "File synchronization alarm",
            "load_cls": {
                "load_type": "path",
                "cls_path": "mod.base.push_mod.rsync_push",
                "name": "RsyncTask"
            },
            "template": {
                "field": [
                ],
                "sorted": [
                ]
            },
            "default": {
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
            "unique": True
        }]
    )


RsyncTask = Rsync39Task
if rsync_ver_is_38() is True:
    RsyncTask = Rsync38Task


def push_rsync_by_task_name(task_name: str):
    from .system import push_by_task_keyword

    push_data = {
        "task_name": task_name,
        "msg_list": [
            ">Notification type: File synchronization alarm",
            ">Content of alarm: <font color=#ff0000>File synchronization task {} has failed during the execution, please pay attention to the file synchronization situation and deal with it.</font> ".format(
                task_name),
        ]
    }
    push_by_task_keyword("rsync_push", "rsync_push", push_data=push_data)


class ViewMsgFormat(object):

    @staticmethod
    def get_msg(task: dict) -> Optional[str]:
        if task["template_id"] == "40":
            return "<span>Push alarm information when there is an exception in file synchronization (push {} times per day and then not push)<span>".format(
                task.get("number_rule", {}).get("day_num"))
        return None
