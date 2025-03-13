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


class tg_msg:
    conf_path = "{}/data/tg_bot.json".format(panelPath)
    __tg_info = None
    __module_name = None
    __default_pl = "{}/data/default_msg_channel.pl".format(panelPath)

    def __init__(self):
        try:
            red_conf_path = public.readFile(self.conf_path)

            self.__tg_info = json.loads(red_conf_path)
            if not 'bot_token' in self.__tg_info or not 'my_id' in self.__tg_info:
                self.__tg_info = None
        except:
            self.__tg_info = None
        self.__module_name = self.__class__.__name__.replace('_msg', '')

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

        self.__tg_info = {"my_id": get.my_id.strip(), "bot_token": get.bot_token, "title": title, "status": True}

        try:
            info = public.get_push_info('Notification Configuration Reminder',
                                        ['>Configuration status：<font color=#20a53a>successfully</font>\n\n'])
            ret = self.send_msg(info['msg'])
        except:
            ret = self.send_msg('aaPanel alarm test')
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

    def process_character(self, msg):
        """
        格式化消息
        """
        # 去掉无用的转义字符
        msg = msg.replace('\\', '')

        # 去掉 HTML 标签
        msg = re.sub(r'<[^>]+>', '', msg)

        # 去掉标题中的 ####
        msg = msg.replace('####', '')

        # > 增加空格
        msg = msg.replace('>', '> ')

        # 去掉标题两边的空格
        title = msg.split('\n')[0].strip()

        # 去掉标题后面的换行符和空行，保留消息
        msg = msg.replace(f'{title}\n\n', '')

        # 去掉消息前后的空格
        msg = msg.strip()

        character = ['\\', '_', '`', '*', '{', '}', '[', ']', '(', ')', '>', '#', '+', '-', '=', '.', '!']
        for c in character:
            if c in msg:
                msg = msg.replace(c, '\\' + c)


        # 将处理后的消息发送到Telegram
        msg = f'*{title}*\n\n{msg}'

        return msg

    async def send_msg_async(self, bot_token, chat_id, msg):
        """
        tg发送信息
        @msg 消息正文
        """

        bot = telegram.Bot(token=bot_token)

        msg = self.process_character(msg)

        public.print_log(msg)

        await bot.send_message(chat_id=chat_id, text=msg, parse_mode='MarkdownV2')

    def send_msg(self, msg):
        """
        tg发送信息
        @msg 消息正文
        """
        if not self.__tg_info:
            return public.returnMsg(False, public.lang("The telegram information is incorrectly configured."))
        if isinstance(self.__tg_info['my_id'], int):
            return public.returnMsg(False, public.lang("Telegram configuration error, please reconfigure the robot."))
        msg, title = self.get_send_msg(msg)
        # public.WriteFile("/tmp/title.tg", title)
        # public.WriteFile("/tmp/msg.tg", msg)
        # send_content = msg
        # public.WriteFile("/tmp/send_content.tg", send_content)

        # bot = telegram.Bot(self.__tg_info['bot_token'])
        bot_token = self.__tg_info['bot_token']
        chat_id = self.__tg_info['my_id']
        #text = msg
        public.print_log(msg)

        # public.print_log("bot:{}".format(self.__tg_info['bot_token']))
        # public.print_log("my_id:{}".format(self.__tg_info['my_id']))

        import asyncio

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        try:
            loop.run_until_complete(self.send_msg_async(bot_token, chat_id, msg))
            ret = {'success': 1}

            public.write_push_log(self.__module_name, title, ret)

            public.print_log('message sent successfully！')
            loop.close()

            return public.returnMsg(True, public.lang("send complete, send result: True."))

        except:
            public.print_log('Error:{}'.format(str(public.get_error_info())))

            ret = {'success': 0}

            public.write_push_log(self.__module_name, title, ret)

            return public.returnMsg(False, public.lang("send complete, send result: False."))

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

    # 获取tg机器人信息
    # def get_tg_conf(self, get=None):
    #     conf = self.__tg_info
    #
    #     if not conf:
    #         return {"setup": False, "bot_token": "", "my_id": ""}
    #     try:
    #         return self.__tg_info
    #     except:
    #         return {"setup": False, "bot_token": "", "my_id": ""}

    # def process_character(self,content):
    #     character = ['.',',','!',':','%','[',']','\/','_','-','>']
    #     for c in character:
    #         if c in content and '\\{}'.format(c) not in content:
    #             content = content.replace(c,'\\'+c)
    #     return content

    # 使用tg机器人发送消息
    # def send_by_tg_bot(self,content,parse_mode=None):
    #     "parse_mode 消息格式  html/markdown/markdownv2"
    #     #content = self.process_character(content)
    #     conf = self.__tg_info
    #
    #     confa1 = conf['my_id']
    #     public.print_log("开始检查--confa1", confa1)
    #     confa2 = conf['bot_token']
    #     public.print_log("开始检查--confa2", confa2)
    #
    #
    #     text = send_content
    #     public.WriteFile("/tmp/text.tg", text)
    #
    #     bot = telegram.Bot(conf['bot_token'])
    #     #result = bot.send_message(text=content, chat_id=int(conf['my_id']), parse_mode="MarkdownV2")
    #     result = bot.send_message( chat_id=int(conf['my_id']), text=text, parse_mode='MarkdownV2')
    #
    #     return result
