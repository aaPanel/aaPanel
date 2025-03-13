#coding: utf-8
# +-------------------------------------------------------------------
# | aaPanel
# +-------------------------------------------------------------------
# | Copyright (c) 2015-2020 aaPanel(www.aapanel.com) All rights reserved.
# +-------------------------------------------------------------------
# | Author: 沐落 <cjx@aapanel.com>
# | Author: lx
# | 消息通道邮箱模块
# | 常用功能
#   字体加粗  **bold**  ，[这是一个链接](http://www.aapanel.com)，代码段：`code`
#   支持3种字体颜色 <font color="info">绿色</font> <font color="comment">灰色</font> <font color="warning">橙红色</font>
# +-------------------------------------------------------------------

import os, sys, public, json, requests,re
import sys, os,time
panelPath = "/www/server/panel"
os.chdir(panelPath)
sys.path.insert(0,panelPath + "/class/")
import public, json, requests
from requests.packages import urllib3
# 关闭警告

urllib3.disable_warnings()
import socket
import requests.packages.urllib3.util.connection as urllib3_cn
class weixin_msg:

    __module_name = None
    __default_pl = "{}/data/default_msg_channel.pl".format(panelPath)
    conf_path = 'data/weixin.json'
    __weixin_info = None
    def __init__(self):
        try:
            self.__weixin_info = json.loads(public.readFile(self.conf_path))
            if not 'weixin_url' in self.__weixin_info:
                self.__weixin_info = None
        except :
            self.__weixin_info = None
        self.__module_name = self.__class__.__name__.replace('_msg','')

    def get_version_info(self,get):
        """
        获取版本信息
        """
        data = {}
        data['ps'] = 'Wecom used to receive panel message push'
        data['version'] = '1.2'
        data['date'] = '2022-08-10'
        data['author'] = 'aaPanel'
        data['title'] = 'Wecom'
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
        获取微信配置
        """
        data = {}
        if self.__weixin_info :

            #全局配置开关,1开启，0关闭
            if not 'state' in self.__weixin_info:
                self.__weixin_info['state'] = 1

            data = self.__weixin_info

            if not 'list' in data: data['list'] = {}

            title = 'Default'
            if 'title' in data: title = data['title']

            data['list']['default'] = {'title':title,'data':data['weixin_url'],'state':self.__weixin_info['state']}
            data['default'] = self.__get_default_channel()
        return data

    def set_config(self,get):
        """
        设置微信配置
        @url 微信URL
        @atall 默认@全体成员
        @key 唯一标识，default=兼容之前配置
        @title string 备注
        @user
        """

        if not hasattr(get, 'url'):
            return public.returnMsg(False, public.lang("Please fill in the complete information"))

        title = 'Default'
        if hasattr(get, 'title'):
            title = get.title
            if len(title) > 7:
                return public.returnMsg(False, public.lang("Note name cannot exceed 7 characters"))

        key,status,state ='default', 1, 1
        if 'key' in get:  key = get.key
        if 'status' in get:  status = int(get.status)
        if 'state' in get:  state = int(get.state)

        if not self.__weixin_info:  self.__weixin_info = {}
        if not 'list' in self.__weixin_info: self.__weixin_info['list'] = {}

        #全局配置开关,1开启，0关闭
        self.__weixin_info['state'] = state

        #增加多个机器人
        self.__weixin_info['list'][key]  = {
            "data": get.url.strip(),
            "title":title,
            "status":status,
            "addtime":int(time.time())
        }

        #兼容旧配置只有一条url的情况
        if key == 'default':
            self.__weixin_info['weixin_url'] = get.url.strip()
            self.__weixin_info['title'] = title

        #统一格式化输出，包含主机名，ip，推送时间
        try:
            info = public.get_push_info('Message channel configuration reminder',['>configuration status: <font color=#20a53a>Success</font>\n\n'])
            ret = self.send_msg(info['msg'])
        except:
            ret = self.send_msg('aaPanel alarm test')

        if ret['status']:

            #默认消息通道
            if 'default' in get and get['default']:
                public.writeFile(self.__default_pl, self.__module_name)

            if ret['success'] <= 0:
                return public.returnMsg(False, public.lang("Failed to add, please check whether the URL is correct"))

            public.writeFile(self.conf_path, json.dumps(self.__weixin_info))
            return public.returnMsg(True, public.lang("successfully set"))
        else:
            return public.returnMsg(False, public.lang("Failed to add, please check whether the URL is correct"))

    def get_send_msg(self,msg):
        """
        @name 处理md格式
        """
        try:
            title = 'aaPanel warning notification'
            if msg.find("####") >= 0:
                msg = msg.replace("\n\n","""
                """).strip()
                try:
                    title = re.search(r"####(.+)", msg).groups()[0]
                except:pass

        except:pass
        return msg,title

    def send_msg(self,msg,to_user = 'default'):
        """
        @name 微信发送信息
        @msg string 消息正文(正文内容，必须包含
                1、服务器名称
                2、IP地址
                3、发送时间
            )
        @to_user string 指定发送人
        """
        if not self.__weixin_info :
            return public.returnMsg(False, public.lang("Information is not configured correctly."))

        if 'state' in self.__weixin_info and self.__weixin_info['state'] == 0:
            return public.returnMsg(False, public.lang("Notifications have been turned off, please turn them on and try again."))

        if msg.find('####') == -1:
            try:
                msg = public.get_push_info('Notification Configuration Reminder',['>Send Content：{}\n\n'.format(msg)])['msg']
            except:pass

        msg,title = self.get_send_msg(msg)
        data = {
            "msgtype": "markdown",
            "markdown": {
                "content": msg
            }
        }
        headers = {'Content-Type': 'application/json'}

        error,success = 0,0
        conf = self.get_config(None)['list']

        res = {}
        for to_key in to_user.split(','):
            if not to_key in conf: continue
            try:
                #x = requests.post(url = conf[to_key]['data'], data=json.dumps(data), headers=headers,verify=False,timeout=10)

                allowed_gai_family_lib=urllib3_cn.allowed_gai_family
                def allowed_gai_family():
                    family = socket.AF_INET
                    return family
                urllib3_cn.allowed_gai_family = allowed_gai_family
                x = requests.post(url = conf[to_key]['data'], data = json.dumps(data),verify=False, headers=headers,timeout=10)
                urllib3_cn.allowed_gai_family=allowed_gai_family_lib

                if x.json()["errcode"] == 0:
                    success += 1
                    res[conf[to_key]['title']] = 1
                else:
                    error += 1
                    res[conf[to_key]['title']] = 0
            except:
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
        """
        @name 统一发送接口
        @data 消息内容
            {"module":"mail","title":"提醒","msg":"提醒","to_email":"xx@qq.com","sm_type":"","sm_args":{}}
        """
        if not 'to_user' in data:
            data['to_user'] = 'default'

        return self.send_msg(data['msg'],data['to_user'])


    def _write_log(self,module,msg,res):
        """
        @name 写日志
        """
        user = '[ 默认 ] '
        # for key in res:
        #     status = '<span style="color:#20a53a;">成功</span>'
        #     if res[key] == 0: status = '<span style="color:red;">成功</span>'
        #     user += '[ {}:{} ] '.format(key,status)

        try:
            msg_obj = public.init_msg(module)
            if msg_obj: module = msg_obj.get_version_info(None)['title']
        except:pass

        log = '[{}] sent to {}, sending content: [{}]'.format(module,user,public.xsssec(msg))
        public.WriteLog('message push',log)

    def uninstall(self):
        if os.path.exists(self.conf_path):
            os.remove(self.conf_path)


