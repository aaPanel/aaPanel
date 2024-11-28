# coding: utf-8
# +-------------------------------------------------------------------
# | aapanel
# +-------------------------------------------------------------------
# | Copyright (c) 2015-2020 aapanel(http://www.aapanel.com) All rights reserved.
# +-------------------------------------------------------------------
# | Author: baozi <baozi@bt.cn>
# | 消息通道邮箱模块
# +-------------------------------------------------------------------

import re
import json
import requests
import traceback
import socket
import public

import requests.packages.urllib3.util.connection as urllib3_cn
from requests.packages import urllib3
from typing import Optional, Union

from .util import write_push_log, get_test_msg

# 关闭警告
urllib3.disable_warnings()


class WeiXinMsg:

    def __init__(self, weixin_data):
        self.id = weixin_data["id"]
        self.config = weixin_data["data"]

    @classmethod
    def check_args(cls, args: dict) -> Union[dict, str]:
        if "url" not in args or "title" not in args:
            return public.lang('Incomplete information')

        title = args["title"]
        if len(title) > 15:
            return public.lang('Note names cannot be longer than 15 characters')

        data = {
            "url": args["url"],
            "title": title,
        }

        test_obj = cls({"data": data, "id": None})
        test_msg = {
            "msg_list": ['>configuration state: <font color=#20a53a> Success </font>\n']
        }

        test_task = get_test_msg("Message channel configuration reminders")

        res = test_obj.send_msg(
            test_task.to_weixin_msg(test_msg, test_task.the_push_public_data()),
            "Message channel configuration reminders"
        )
        if res is None:
            return data

        return res

    def send_msg(self, msg: str, title: str) -> Optional[str]:
        """
        @name 微信发送信息
        @msg string 消息正文(正文内容，必须包含
                1、服务器名称
                2、IP地址
                3、发送时间
            )
        @to_user string 指定发送人
        """
        if not self.config:
            return public.lang('WeChat information is not configured correctly')

        reg = '<font.+>(.+)</font>'
        tmp = re.search(reg, msg)
        if tmp:
            tmp = tmp.groups()[0]
            msg = re.sub(reg, tmp, msg)

        data = {
            "msgtype": "markdown",
            "markdown": {
                "content": msg
            }
        }
        headers = {'Content-Type': 'application/json'}

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

        write_push_log("weixin", status, title)
        return error

    def test_send_msg(self) -> Optional[str]:
        test_msg = {
            "msg_list": ['>configuration state: <font color=#20a53a> Success </font>\n\n']
        }
        test_task = get_test_msg("Message channel configuration reminders")
        res = self.send_msg(
            test_task.to_weixin_msg(test_msg, test_task.the_push_public_data()),
            "Message channel configuration reminders",
        )
        if res is None:
            return None
        return res




