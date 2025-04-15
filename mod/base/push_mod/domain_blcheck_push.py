import glob
import hashlib
import json
import os
import re
import sys
import time

import psutil
from datetime import datetime
from importlib import import_module
from typing import Tuple, Union, Optional, List

from .send_tool import WxAccountMsg, WxAccountLoginMsg
from .base_task import BaseTask
from .mods import PUSH_DATA_PATH, TaskConfig, SenderConfig, PANEL_PATH
from .util import read_file, DB, write_file, check_site_status,GET_CLASS, ExecShell, get_config_value, public_get_cache_func, \
    public_set_cache_func, get_network_ip, public_get_user_info, public_http_post, panel_version
from mod.base.web_conf import RealSSLManger

# 邮局域名进入黑名单
class MailDomainBlcheck(BaseTask):
    push_tip_file = "/www/server/panel/data/mail_domain_blcheck_send_type.pl"

    def __init__(self):
        super().__init__()
        self.source_name = "mail_domain_black"
        self.template_name = "Your IP is on the email blacklist"
        self.title = "Your IP is on the email blacklist"

    def check_task_data(self, task_data: dict) -> Union[dict, str]:
        return {}

    def get_keyword(self, task_data: dict) -> str:
        return "mail_domain_black"

    def get_push_data(self, task_id: str, task_data: dict) -> Optional[dict]:
        return None

    def filter_template(self, template) -> dict:
        return template

    def to_sms_msg(self, push_data: dict, push_public_data: dict) -> Tuple[str, dict]:
        return "", {}

    def task_config_update_hook(self, task: dict) -> None:

        sender = task["sender"]
        if len(sender) > 0:
            send_id = sender[0]
        else:
            return

        sender_data = SenderConfig().get_by_id(send_id)
        if sender_data:
            write_file(self.push_tip_file, sender_data["sender_type"])

    def task_config_create_hook(self, task: dict) -> None:
        return self.task_config_update_hook(task)

    def task_config_remove_hook(self, task: dict) -> None:
        if os.path.exists(self.push_tip_file):
            os.remove(self.push_tip_file)

# 邮局服务异常告警
class MailServerDown(BaseTask):
    push_tip_file = "/www/server/panel/data/mail_server_down_send_type.pl"


    def __init__(self):
        super().__init__()
        self.source_name = "mail_server_status"
        self.template_name = "Your Mail Service is down"
        self.title = "Your Mail Service is down"

    def check_task_data(self, task_data: dict) -> Union[dict, str]:
        return {}

    def get_keyword(self, task_data: dict) -> str:
        return "mail_server_status"

    def get_push_data(self, task_id: str, task_data: dict) -> Optional[dict]:
        return None

    def filter_template(self, template) -> dict:
        return template

    def to_sms_msg(self, push_data: dict, push_public_data: dict) -> Tuple[str, dict]:
        return "", {}

    def task_config_update_hook(self, task: dict) -> None:

        sender = task["sender"]
        if len(sender) > 0:
            send_id = sender[0]
        else:
            return

        sender_data = SenderConfig().get_by_id(send_id)
        if sender_data:
            write_file(self.push_tip_file, sender_data["sender_type"])

    def task_config_create_hook(self, task: dict) -> None:
        return self.task_config_update_hook(task)

    def task_config_remove_hook(self, task: dict) -> None:
        if os.path.exists(self.push_tip_file):
            os.remove(self.push_tip_file)

# 邮局服务异常告警
class MailDomainQuota(BaseTask):
    push_tip_file = "/www/server/panel/data/mail_domain_quota_alert_send_type.pl"


    def __init__(self):
        super().__init__()
        self.source_name = "mail_domain_quota_alert"
        self.template_name = "Your Mail Domain Quota Alert"
        self.title = "Your Mail Domain Quota Alert"

    def check_task_data(self, task_data: dict) -> Union[dict, str]:
        return {}

    def get_keyword(self, task_data: dict) -> str:
        return "mail_domain_quota_alert"

    def get_push_data(self, task_id: str, task_data: dict) -> Optional[dict]:
        return None

    def filter_template(self, template) -> dict:
        return template

    def to_sms_msg(self, push_data: dict, push_public_data: dict) -> Tuple[str, dict]:
        return "", {}

    def task_config_update_hook(self, task: dict) -> None:

        sender = task["sender"]
        if len(sender) > 0:
            send_id = sender[0]
        else:
            return

        sender_data = SenderConfig().get_by_id(send_id)
        if sender_data:
            write_file(self.push_tip_file, sender_data["sender_type"])

    def task_config_create_hook(self, task: dict) -> None:
        return self.task_config_update_hook(task)

    def task_config_remove_hook(self, task: dict) -> None:
        if os.path.exists(self.push_tip_file):
            os.remove(self.push_tip_file)


class ViewMsgFormat(object):
    _FORMAT = {
        "1": (
            lambda x: "<span>When your MailServer domain is blacklisted, an alarm is generated</span>"
        ),
        "2": (
            lambda x: "<span>When your Mail Service is down, an alarm is generated</span>"
        ),
        "3": (
            lambda x: "<span>When your Mail domain usage exceeds quota, an alarm is generated</span>"
        )
    }

    def get_msg(self, task: dict) -> Optional[str]:
        if task["template_id"] in ["80"]:
            return self._FORMAT["1"](task)
        if task["template_id"] in ["81"]:
            return self._FORMAT["2"](task)
        if task["template_id"] in ["82"]:
            return self._FORMAT["3"](task)
        if task["template_id"] in self._FORMAT:
            return self._FORMAT[task["template_id"]](task)
        return None
