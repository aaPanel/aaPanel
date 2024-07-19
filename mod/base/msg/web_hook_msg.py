# coding: utf-8
# +-------------------------------------------------------------------
# | 宝塔Linux面板
# +-------------------------------------------------------------------
# | Copyright (c) 2015-2020 宝塔软件(http://www.bt.cn) All rights reserved.
# +-------------------------------------------------------------------
# | Author: baozi <baozi@bt.cn>
# | 消息通道HOOK模块
# +-------------------------------------------------------------------


import requests
from typing import Optional, Union
from urllib3.util import parse_url

from .util import write_push_log, get_test_msg
import json

# config = {
#     "name": "default",
#     "url": "https://www.bt.cn",
#     "query": {
#         "aaa": "111"
#     },
#     "header": {
#         "AAA": "BBBB",
#     },
#     "body_type": ["json", "form_data", "null"],
#     "custom_parameter": {
#         "rrr": "qqqq"
#     },
#     "method": ["GET", "POST", "PUT", "PATCH"],
#     "ssl_verify": [True, False]
# }
# #
# # 1.自动解析Query参数，拼接并展示给用户  # 可不做
# # 2.自定义Header头 # 必做
# # 3.Body中的内容是: type:str="首页磁盘告警", time:int=168955427, data:str="xxxxxx"  # ？
# # 4.自定义参数: key=value 添加在Body中  # 可不做
# # 5.请求类型自定义 # 必做
# # 以上内容需要让用户可测试--!


class WebHookMsg(object):
    DEFAULT_HEADERS = {
        "User-Agent": "BT-Panel",
    }

    def __init__(self, hook_data: dict):
        self.id = hook_data["id"]
        self.config = hook_data["data"]

    def _replace_and_parse(self, value, real_data):
        """替换占位符并递归解析JSON字符串"""
        if isinstance(value, str):
            value = value.replace("$1", json.dumps(real_data, ensure_ascii=False))
        elif isinstance(value, dict):
            for k, v in value.items():
                value[k] = self._replace_and_parse(v, real_data)
        return value

    def send_msg(self, msg: str, title:str, push_type:str) -> Optional[str]:
        the_url = parse_url(self.config['url'])

        ssl_verify = self.config.get("ssl_verify", None)
        if ssl_verify is None:
            ssl_verify = the_url.scheme == "https"

        real_data = {
            "title": title,
            "msg": msg,
            "type": push_type,
        }
        # 处理custom_parameter，将$1替换为real_data内容并递归解析
        custom_data = {}
        for k, v in self.config.get("custom_parameter", {}).items():
            custom_data[k] = self._replace_and_parse(v, real_data)

        if custom_data:
            real_data = custom_data


        data = None
        json_data = None
        headers = self.DEFAULT_HEADERS.copy()
        if self.config["body_type"] == "json":
            json_data = real_data
        elif self.config["body_type"] == "form_data":
            data = real_data

        for k, v in self.config.get("headers", {}).items():
            if not isinstance(v, str):
                v = str(v)
            headers[k] = v

        status = False
        error = None
        timeout = 10
        if data:
            for k, v in data.items():
                if isinstance(v, str):
                    continue
                else:
                    data[k]=json.dumps(v)   

        for i in range(3):
            try:
                if json_data is not None:
                    res = requests.request(
                        method=self.config["method"],
                        url=str(the_url),
                        json=json_data,
                        headers=headers,
                        timeout=timeout,
                        verify=ssl_verify,
                    )
                else:
                    res = requests.request(
                        method=self.config["method"],
                        url=str(the_url),
                        data=data,
                        headers=headers,
                        timeout=timeout,
                        verify=ssl_verify,
                    )

                if res.status_code == 200:
                    status = True
                    break
                else:
                    status = False
                    return res.text
            except (requests.exceptions.Timeout, requests.exceptions.ConnectionError):
                timeout += 5
                continue
            except requests.exceptions.RequestException as e:
                error = str(e)
                break

        write_push_log("Web Hook", status, title)
        return error

    @classmethod
    def check_args(cls, args) -> Union[str, dict]:
        """配置hook"""
        try:
            title = args['title']
            url = args["url"]
            query = args.get("query", {})
            headers = args.get("headers", {})
            body_type = args.get("body_type", "json")
            custom_parameter = args.get("custom_parameter", {})
            method = args.get("method", "POST")
            ssl_verify = args.get("ssl_verify", None)  # null Ture
        except (ValueError, KeyError):
            return "参数错误"

        the_url = parse_url(url)
        if the_url.scheme is None or the_url.host is None:
            return"url解析错误，这可能不是一个合法的url"

        for i in (query, headers, custom_parameter):
            if not isinstance(i, dict):
                return "参数格式错误"

        if body_type not in ('json', 'form_data', 'null'):
            return "body_type必须为json,form_data或者null"

        if method not in ('GET', 'POST', 'PUT', 'PATCH'):
            return "发送方式选择错误"

        if ssl_verify not in (True, False, None):
            return "是否验证ssl选项错误"

        title = title.strip()
        if title == "":
            return"名称不能为空"

        data = {
            "title": title,
            "url": url,
            "query": query,
            "headers": headers,
            "body_type": body_type,
            "custom_parameter": custom_parameter,
            "method": method,
            "ssl_verify": ssl_verify,
            "status": True
        }

        test_obj = cls({"data": data, "id": None})
        test_msg = {
            "msg_list": ['>配置状态：成功\n\n']
        }

        test_task = get_test_msg("消息通道配置提醒")

        res = test_obj.send_msg(
            test_task.to_web_hook_msg(test_msg, test_task.the_push_public_data()),
            "消息通道配置提醒",
            "消息通道配置提醒"
        )
        if res is None:
            return data

        return res

    def test_send_msg(self) -> Optional[str]:
        test_msg = {
            "msg_list": ['>配置状态：<font color=#20a53a>成功</font>\n\n']
        }
        test_task = get_test_msg("消息通道配置提醒")
        res = self.send_msg(
            test_task.to_web_hook_msg(test_msg, test_task.the_push_public_data()),
            "消息通道配置提醒",
            "消息通道配置提醒"
        )
        if res is None:
            return None
        return res

