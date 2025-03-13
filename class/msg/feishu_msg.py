#coding: utf-8
# +-------------------------------------------------------------------
# | aaPanel
# +-------------------------------------------------------------------
# | Copyright (c) 2015-2020 aaPanel(www.aapanel.com) All rights reserved.
# +-------------------------------------------------------------------
# | Author: lx
# | 消息通道飞书通知模块
# +-------------------------------------------------------------------

import os, sys, public, json, requests
import sys, os
panelPath = '/www/server/panel'
os.chdir(panelPath)
sys.path.insert(0,panelPath + "/class/")
import public, json, requests
from requests.packages import urllib3
# 关闭警告

urllib3.disable_warnings()
import socket
import requests.packages.urllib3.util.connection as urllib3_cn
class feishu_msg:

    conf_path = 'data/feishu.json'
    __feishu_info = None

    __module_name = None
    __default_pl = "{}/data/default_msg_channel.pl".format(panelPath)

    def __init__(self):
        try:
            self.__feishu_info = json.loads(public.readFile(self.conf_path))
            if not 'feishu_url' in self.__feishu_info or not 'isAtAll' in self.__feishu_info or not 'user' in self.__feishu_info:
                self.__feishu_info = None
        except :
            self.__feishu_info = None

        self.__module_name = self.__class__.__name__.replace('_msg','')

    def get_version_info(self,get):
        """
        获取版本信息
        """
        data = {}
        data['ps'] = 'Feishu is used to receive panel message push'
        data['version'] = '1.2'
        data['date'] = '2022-08-10'
        data['author'] = 'aaPanel'
        data['title'] = 'Feishu'
        data['help'] = 'http://www.aapanel.com'
        return data


    def __get_default_channel(self):
        """
        @获取默认消息通道
        """
        try:
            if public.readFile(self.__default_pl) == self.__module_name:
                return True
        except:pass
        return False

    def get_config(self,get):
        """
        获取飞书配置
        """
        data = {}
        if self.__feishu_info :
            data = self.__feishu_info

            if not 'list' in data: data['list'] = {}

            title = 'Default'
            if 'title' in data: title = data['title']

            data['list']['default'] = {'title':title,'data':data['feishu_url']}

            data['default'] = self.__get_default_channel()

        return data

    def set_config(self,get):
        """
        设置飞书配置
        @url 飞书URL
        @atall 默认@全体成员
        @user
        """
        if not hasattr(get, 'url'):
            return public.returnMsg(False, public.lang("Please fill in the complete information"))

        isAtAll = True
        if hasattr(get, "atall"):
            if get.atall.lower() == "false":
                isAtAll = False

        title = 'Default'
        if hasattr(get, 'title'):
            title = get.title
            if len(title) > 7:
                return public.returnMsg(False, public.lang("Note name cannot exceed 7 characters"))

        self.__feishu_info  = {"feishu_url": get.url.strip(), "isAtAll": isAtAll, "user":1,"title":title}
        ret = self.send_msg('aaPanel alarm test')
        if ret['status']:
            if 'default' in get and get['default']:
                public.writeFile(self.__default_pl, self.__module_name)

            if ret['success'] <= 0:
                return public.returnMsg(False, public.lang("Failed to add, please check whether the URL is correct"))

            public.writeFile(self.conf_path, json.dumps(self.__feishu_info))
            return public.returnMsg(True, public.lang("successfully set"))
        else:
            return public.returnMsg(False, public.lang("Failed to add, please check whether the URL is correct"))


    def get_send_msg(self,msg):
        """
        @name 处理md格式
        """
        try:
            import re
            title = 'aaPanel warning notification'
            if msg.find("####") >= 0:
                try:
                    title = re.search(r"####(.+)", msg).groups()[0]
                except:pass

                msg = msg.replace("####",">").replace("\n\n","\n").strip()
                s_list = msg.split('\n')

                if len(s_list) > 3:
                    s_title = s_list[0].replace(" ","")
                    s_list = s_list[1:]
                    s_list.insert(0,s_title)
                    msg = '\n'.join(s_list)

            reg = '<font.+>(.+)</font>'
            tmp = re.search(reg,msg)
            if tmp:
                tmp = tmp.groups()[0]
                msg = re.sub(reg,tmp,msg)
        except:pass
        return msg,title

    def send_msg(self,msg,to_user = 'default'):
        """
        飞书发送信息
        @msg 消息正文
        """
        if not self.__feishu_info :
            return public.returnMsg(False, public.lang("Feishu information is not configured correctly."))

        msg,title = self.get_send_msg(msg)
        if self.__feishu_info["isAtAll"]:
            msg += "<at userid='all'>Everyone</at>"

        data = {
            "msg_type": "text",
            "content": {
                "text": msg
            }
        }
        headers = {'Content-Type': 'application/json'}
        res = {}

        error,success = 0,0
        conf = self.get_config(None)['list']

        for to_key in to_user.split(','):
            if not to_key in conf: continue
            try:

                allowed_gai_family_lib=urllib3_cn.allowed_gai_family
                def allowed_gai_family():
                    family = socket.AF_INET
                    return family
                urllib3_cn.allowed_gai_family = allowed_gai_family
                rdata = requests.post(url = conf[to_key]['data'], data = json.dumps(data),verify=False, headers=headers,timeout=10).json()
                urllib3_cn.allowed_gai_family=allowed_gai_family_lib

                # x = requests.post(url = conf[to_key]['data'], data=json.dumps(data), headers=headers,verify=False,timeout=10)
                # rdata = x.json()

                if "StatusCode" in rdata and rdata["StatusCode"] == 0:
                    success += 1
                    res[conf[to_key]['title']] = 1
                else:
                    error += 1
                    res[conf[to_key]['title']] = 0
            except:
                public.print_log(public.get_error_info())
                error += 1
                res[conf[to_key]['title']] = 0

        try:
            public.write_push_log(self.__module_name,title,res)
        except:pass

        ret = public.returnMsg(True,'Send completed, send successfully {}, send failed {}.'.format(success,error))
        ret['success'] = success
        ret['error'] = error

        return ret

    def push_data(self,data):
        return self.send_msg(data['msg'])

    def uninstall(self):
        if os.path.exists(self.conf_path):
            os.remove(self.conf_path)