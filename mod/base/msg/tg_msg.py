# coding: utf-8
# +-------------------------------------------------------------------
# | aaPanel
# +-------------------------------------------------------------------
# | Copyright (c) 2015-2020 aaPanel(www.aapanel.com) All rights reserved.
# +-------------------------------------------------------------------
# | Author: jose <zhw@aapanel.com>
# | 消息通道电报模块
# +-------------------------------------------------------------------

import sys, os, re, asyncio, public, json, requests

try:
    import telegram
except:
    public.ExecShell("btpip install -I python-telegram-bot")
    import telegram

panelPath = "/www/server/panel"
os.chdir(panelPath)
sys.path.insert(0, panelPath + "/class/")
from requests.packages import urllib3

# 关闭警告
urllib3.disable_warnings()

import smtplib
import traceback
from email.mime.text import MIMEText
from email.utils import formataddr
from typing import Tuple, Union, Optional

from mod.base.msg.util import write_push_log, write_mail_push_log, get_test_msg


class TgMsg:
    conf_path = "{}/data/tg_bot.json".format(panelPath)
    __tg_info = None
    __module_name = None
    __default_pl = "{}/data/default_msg_channel.pl".format(panelPath)

    # def __init__(self):
    #     try:
    #         red_conf_path = public.readFile(self.conf_path)
    #
    #         self.__tg_info = json.loads(red_conf_path)
    #         if not 'bot_token' in self.__tg_info or not 'my_id' in self.__tg_info:
    #             self.__tg_info = None
    #     except:
    #         self.__tg_info = None
    #     self.__module_name = self.__class__.__name__.replace('_msg', '')

    # def __init__(self, tg_data):
    #     self.my_id = tg_data["data"]["my_id"]
    #     self.bot_token = tg_data["data"]["bot_token"]
    def __init__(self, conf):
        self.conf = conf
        self.bot_token = self.conf['data']['bot_token']
        self.my_id = self.conf['data']['my_id']

    def get_version_info(self, get):
        """
        获取版本信息
        """
        data = {}
        data['ps'] = 'Use telegram bots to send receive panel notifications'
        data['version'] = '1.0'
        data['date'] = '2022-08-10'
        data['author'] = 'aaPanel'
        data['title'] = 'Telegram'
        data['help'] = 'http://www.aapanel.com'
        return data

    def get_config(self, get):
        """
        获取tg配置
        """
        data = {}
        if self.__tg_info:
            data = self.__tg_info

            data['default'] = self.__get_default_channel()

        return data

    def set_config(self, get):
        """
        设置tg bot
        @my_id tg id
        @bot_token 机器人token
        """

        if not hasattr(get, 'my_id') or not hasattr(get, 'bot_token'):
            return public.returnMsg(False, public.lang("Please fill in the complete information"))

        title = 'Default'
        if hasattr(get, 'title'):
            title = get.title
            if len(title) > 7:
                return public.returnMsg(False, public.lang("Note name cannot exceed 7 characters"))

        self.__tg_info = {"my_id": get.my_id.strip(), "bot_token": get.bot_token, "title": title}

        try:
            info = public.get_push_info('Notification Configuration Reminder',
                                        ['>Configuration status：<font color=#20a53a>successfully</font>\n\n'])
            ret = self.send_msg(info['msg'], get.my_id.strip(), get.bot_token)
        except:
            ret = self.send_msg('aaPanel alarm test', get.my_id.strip(), get.bot_token)
        if ret:

            if 'default' in get and get['default']:
                public.writeFile(self.__default_pl, self.__module_name)

            public.writeFile(self.conf_path, json.dumps(self.__tg_info))
            return public.returnMsg(True, public.lang("successfully set"))
        else:
            return ret

    def get_send_msg(self, msg):
        """
        @name 处理md格式
        """
        try:
            title = 'aaPanel notifications'
            if msg.find("####") >= 0:
                try:
                    title = re.search(r"####(.+)", msg).groups()[0]
                except:
                    pass
            else:
                info = public.get_push_info('Notification Configuration Reminder', ['>Send Content: ' + msg])
                msg = info['msg']
        except:
            pass
        return msg, title

    async def send_msg_async(self, bot_token, chat_id, msg):
        """
        tg发送信息
        @msg 消息正文
        """

        bot = telegram.Bot(token=bot_token)

        await bot.send_message(chat_id=chat_id, text=msg, parse_mode='MarkdownV2')

    # 外部也调用
    def send_msg(self, msg, title):
        """
        tg发送信息
        @msg 消息正文
        """
        # msg, title = self.get_send_msg(msg)

        bot_token = self.bot_token
        chat_id = self.my_id

        # public.print_log("tg 消息正文-- 发送数据 {}".format(msg))
        # 去掉消息前后的空格
        msg = msg.strip()
        # 特殊字符处理
        character = ['\\', '_', '`', '*', '{', '}', '[', ']', '(', ')', '>', '#', '+', '-', '=', '.', '!']
        for c in character:
            if c in msg:
                msg = msg.replace(c, '\\' + c)

        # public.print_log("tg 消息正文-- 修改后 {}".format(msg))
        import asyncio

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        try:
            loop.run_until_complete(self.send_msg_async(bot_token, chat_id, msg))
            # ret = {'success': 1}
            # 192.168.168.162(intranet) Title：[ Notification Configuration Reminder],method to informe:[None]，recipient:[ success：Fail ]
            # Title: [], Notification: [mail], Result: [ Success ], Addressee: [ lotk1@moyumao.top ]
            # public.write_push_log(self.__module_name, title, ret)
            write_push_log("Telegram", True, title)

            public.print_log('message sent successfully!')
            loop.close()

            return None


        except Exception as e:
            public.print_log('Error 123:{}'.format(str(public.get_error_info())))

            # ret = {'success': 0}

            # public.write_push_log(self.__module_name, title, ret)
            write_push_log("Telegram", False, title)

            return public.lang("Telegram Failed to send {}",e)

    @classmethod
    def check_args(cls, args: dict) -> Union[dict, str]:

        my_id = args.get('my_id', None).strip()
        bot_token = args.get('bot_token', None)
        if not my_id or not bot_token:
            return public.lang('Incomplete information')

        title = args.get('title', 'Default')
        if len(title) > 15:
            return public.lang('Note name cannot exceed 15 characters')

        data = {
            "my_id": my_id,
            "bot_token": bot_token,
            "title": title
        }
        conf = {
            "data": data
        }

        # self.bot_token = self.conf['data']['bot_token']
        # self.my_id = self.conf['data']['my_id']
        # 调用TgMsg的方法
        tg = TgMsg(conf)
        try:
            # info = public.get_push_info('Notification Configuration Reminder',
            #                             ['>Configuration status：<font color=#20a53a>successfully</font>\n\n'])
            # public.print_log('TgMsg info 00000:{}'.format(info))

            test_msg = {
                "msg_list": ['>configuration state: <font color=#20a53a> Success </font>\n\n']
            }
            test_task = get_test_msg("Message channel configuration reminders")
            ret = tg.send_msg(
                test_task.to_tg_msg(test_msg, test_task.the_push_public_data()),
                "Message channel configuration reminders"
            )

            # ret = tg.send_msg(info['msg'], title) # 调用 send_msg 方法


        except:
            ret = tg.send_msg('aaPanel alarm test', "Message channel configuration reminders")

        # 测试失败也添加
        if ret:
            return False, ret
        else:
            return True, data

    def test_send_msg(self) -> Optional[str]:
        test_msg = {
            "msg_list": ['>configuration state: <font color=#20a53a> Success </font>\n\n']
        }
        test_task = get_test_msg("Message channel configuration reminders")
        res = self.send_msg(
            test_task.to_tg_msg(test_msg, test_task.the_push_public_data()),
            "Message channel configuration reminders"
        )
        if res is None:
            return None
        return res

    def push_data(self, data):
        """
        @name 统一发送接口
        @data 消息内容
            {"module":"mail","title":"标题","msg":"内容","to_email":"xx@qq.com","sm_type":"","sm_args":{}}
        """

        return self.send_msg(data['msg'])

    def __get_default_channel(self):
        """
        @获取默认消息通道
        """
        try:
            if public.readFile(self.__default_pl) == self.__module_name:
                return True
        except:
            pass
        return False

    def uninstall(self):
        if os.path.exists(self.conf_path):
            os.remove(self.conf_path)
