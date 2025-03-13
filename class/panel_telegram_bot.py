# coding: utf-8
# +-------------------------------------------------------------------
# | aaPanel x3
# +-------------------------------------------------------------------
# | Copyright (c) 2015-2017 aaPanel(www.aapanel.com) All rights reserved.
# +-------------------------------------------------------------------
# | Author: zhw <zhw@aapanel.com>
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
        return public.returnMsg(True, public.lang("Setup successfully"))

    # 删除tg机器人
    def del_tg_bot(self,get):
        if os.path.exists(self.__tg_conf_file):
            os.remove(self.__tg_conf_file)
        return public.returnMsg(True, public.lang("Remove successfully"))

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
        character = ['\\', '_', '*', '[', ']', '(', ')', '~', '`', '>', '#', '+', '-', '=', '|', '{', '}', '.', '!']
        for c in character:
            content = content.replace(c, '\\' + c)
        return content


    # 使用tg机器人发送消息
    def send_by_tg_bot(self,content,parse_mode=None):
        """
        @author hezhihong
        """
        
        "parse_mode 消息格式  html/markdown/markdownv2"
        
        # content = self.process_character(content)
        conf = self.get_tg_conf()
        try:
            result= self.send_message(conf['bot_token'],conf['my_id'],content)
            if not result['status']:
                return False
            return True
        except:
            return False
            
            
    def send_message(self, bot_token, chat_id, msg):
        """
        tg发送信息
        @msg 消息正文
        @author hezhihong
        """
        msg = self.process_character(msg)
        url = 'https://api.telegram.org/bot{}/sendMessage'.format(bot_token)
        data = {
            'chat_id': chat_id,
            'text': msg,
            'parse_mode':'MarkdownV2',
        }
        try:
            import requests
            response = requests.post(url, json=data)
            if response.status_code == 200:
                return public.returnMsg(True,0,response.json())
            else:
                return public.returnMsg(False,json.loads(response.text))
        except Exception as e:
            return public.returnMsg(False,str(e))
