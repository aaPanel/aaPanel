# coding: utf-8
# +-------------------------------------------------------------------
# | 宝塔Linux面板 x3
# +-------------------------------------------------------------------
# | Copyright (c) 2015-2017 宝塔软件(http://bt.cn) All rights reserved.
# +-------------------------------------------------------------------
# | Author: zhw <zhw@bt.cn>
# +-------------------------------------------------------------------

import public
import json
import os

py_bin = public.get_python_bin()
pip = public.get_pip_bin()

try:
    import telegram
except:
    public.ExecShell('{} install python-telegram-bot'.format(pip))
    import telegram

class panel_telegram_bot:
    panel_path = public.get_panel_path()
    __tg_conf_file = '{}/data/tg_bot.json'.format(panel_path)

    # 设置tg机器人
    def set_tg_bot(self,get):
        """
        bot_token:12345677:CCCCCCCC-a0VUo2jjrCCfffaaaaCCDDD
        my_id:1234567890
        """
        data = {"setup":True,"bot_token":get.bot_token,"my_id":get.my_id}
        public.writeFile(self.__tg_conf_file,json.dumps(data))
        return public.returnMsg(True,"Setup successfully")

    # 删除tg机器人
    def del_tg_bot(self,get):
        if os.path.exists(self.__tg_conf_file):
            os.remove(self.__tg_conf_file)
        return public.returnMsg(True, "Remove successfully")

    # 获取tg机器人信息
    def get_tg_conf(self,get=None):
        conf = public.readFile(self.__tg_conf_file)
        if not conf:
            return {"setup":False,"bot_token":"","my_id":""}
        try:
            return json.loads(conf)
        except:
            return {"setup":False,"bot_token":"","my_id":""}

    def process_character(self,content):
        character = ['.',',','!',':','%','[',']','\/','_','-','>']
        for c in character:
            if c in content and '\\{}'.format(c) not in content:
                content = content.replace(c,'\\'+c)
        return content


    # 使用tg机器人发送消息
    def send_by_tg_bot(self,content,parse_mode=None):
        "parse_mode 消息格式  html/markdown/markdownv2"
        content = self.process_character(content)
        conf = self.get_tg_conf()
        bot = telegram.Bot(conf['bot_token'])
        result = bot.send_message(text=content, chat_id=int(conf['my_id']), parse_mode="MarkdownV2")
        return result