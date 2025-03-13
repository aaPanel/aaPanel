# coding: utf-8
# +-------------------------------------------------------------------
# | aapanel
# +-------------------------------------------------------------------
# | Copyright (c) 2015-2020 aapanel(https://www.aapanel.com) All rights reserved.
# +-------------------------------------------------------------------
# | Author: baozi <
# | 消息通道邮箱模块(新)
# +-------------------------------------------------------------------

import re
import json
import requests
import traceback
import socket

import requests.packages.urllib3.util.connection as urllib3_cn
from requests.packages import urllib3
from typing import Optional, Union

from .util import write_push_log, get_test_msg
import public

# 关闭警告
urllib3.disable_warnings()


class DingDingMsg:
    def __init__(self, dingding_data):
        self.id = dingding_data["id"]
        self.config = dingding_data["data"]

    def send_msg(self, msg: str, title) -> Optional[str]:
        """
        钉钉发送信息
        @msg 消息正文
        """
        if not self.config:
            return public.lang('DingTalk information is not correctly configured')

        # user没有时默认为空
        if "user" not in self.config:
            self.config['user'] = []

        if "isAtAll" not in self.config:
            self.config['isAtAll'] = []

        if not isinstance(self.config['url'], str):
            return public.lang('The DingTalk configuration is incorrect, please reconfigure the DingTalk robot')

        at_info = ''
        for user in self.config['user']:
            if re.match(r"^[0-9]{11}$", str(user)):
                at_info += '@' + user + ' '

        if at_info:
            msg = msg + '\n\n>' + at_info
        
        

        headers = {'Content-Type': 'application/json'}
        data = {
            "msgtype": "markdown",
            "markdown": {
                "title": "Server notifications",
                "text": msg
            },
            "at": {
                "atMobiles": self.config['user'],
                "isAtAll": self.config['isAtAll']
            }
        }
        status = False
        error = None
        try:
            def allowed_gai_family():
                family = socket.AF_INET
                return family

            allowed_gai_family_lib = urllib3_cn.allowed_gai_family
            urllib3_cn.allowed_gai_family = allowed_gai_family

            response = requests.post(
                url=self.config["url"],
                data=json.dumps(data),
                verify=False,
                headers=headers,
                timeout=10
            )

            urllib3_cn.allowed_gai_family = allowed_gai_family_lib

            if response.json()["errcode"] == 0:
                status = True
        except:
            error = traceback.format_exc()
            status = False

        write_push_log("dingding", status, title)
        return error

    @classmethod
    def check_args(cls, args: dict) -> Union[dict, str]:
        if "url" not in args or "title" not in args:
            return public.lang('Incomplete information')

        title = args["title"]
        if len(title) > 15:
            return public.lang('Note names cannot be longer than 15 characters')

        if "user" in args and isinstance(args["user"], list):
            user = args["user"]
        else:
            user = []

        if "atall" in args and isinstance(args["atall"], bool):
            atall = args["atall"]
        else:
            atall = True

        data = {
            "url": args["url"],
            "user": user,
            "title": title,
            "isAtAll": atall,
        }

        test_obj = cls({"data": data, "id": None})
        test_msg = {
            "msg_list": ['>configuration state: <font color=#20a53a> Success </font>\n\n']
        }

        test_task = get_test_msg("Message channel configuration reminders")

        res = test_obj.send_msg(
            test_task.to_dingding_msg(test_msg, test_task.the_push_public_data()),
            "Message channel configuration reminders"
        )
        if res is None:
            return data

        return res

    def test_send_msg(self) -> Optional[str]:
        
        test_msg = {
            "msg_list": ['>configuration state: <font color=#20a53a> Success </font>\n\n']
        }
        test_task = get_test_msg("Message channel configuration reminders")
        res = self.send_msg(
            test_task.to_dingding_msg(test_msg, test_task.the_push_public_data()),
            "Message channel configuration reminders"
        )
        if res is None:
            return None
        return res
