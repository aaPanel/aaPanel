#coding: utf-8
# +-------------------------------------------------------------------
# | aaPanel
# +-------------------------------------------------------------------
# | Copyright (c) 2015-2020 aaPanel(www.aapanel.com) All rights reserved.
# +-------------------------------------------------------------------
# | Author: 沐落 <cjx@aapanel.com>
# | Author: lx
# | 消息通道邮箱模块
# +-------------------------------------------------------------------

import os, sys
import time,base64

panelPath = "/www/server/panel"
os.chdir(panelPath)
sys.path.insert(0,panelPath + "/class/")
import public, json, requests
from requests.packages import urllib3
# 关闭警告
urllib3.disable_warnings()
import socket
import requests.packages.urllib3.util.connection as urllib3_cn
class wx_account_msg:

    __module_name = None
    __default_pl = "{}/data/default_msg_channel.pl".format(panelPath)
    conf_path = '{}/data/wx_account_msg.json'.format(panelPath)
    user_info = None


    def __init__(self):
        try:
            self.user_info = json.loads(public.ReadFile("{}/data/userInfo.json".format(public.get_panel_path())))
        except:
            self.user_info=None
        self.__module_name = self.__class__.__name__.replace('_msg','')

    def get_version_info(self,get):
        """
        获取版本信息
        """
        data = {}
        data['ps'] = '宝塔微信公众号，用于接收面板消息推送'
        data['version'] = '1.0'
        data['date'] = '2022-08-15'
        data['author'] = '宝塔'
        data['title'] = '微信公众号'
        data['help'] = 'http://www.aapanel.com'
        return data

    def get_local_ip(self):
        '''获取内网IP'''

        import socket
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(('8.8.8.8', 80))
            ip = s.getsockname()[0]
            return ip
        finally:
            s.close()
        return '127.0.0.1'

    def __get_default_channel(self):
        """
        @获取默认消息通道
        """
        try:
            if public.readFile(self.__default_pl) == self.__module_name:
                return True
        except:pass
        return False

    def get_config(self, get):
        """
        微信公众号配置
        """
        if os.path.exists(self.conf_path):
            #60S内不重复加载
            start_time=int(time.time())
            if os.path.exists("data/wx_account_msg.lock"):
                lock_time= 0
                try:
                    lock_time = int(public.ReadFile("data/wx_account_msg.lock"))
                except:pass
                #大于60S重新加载
                if start_time - lock_time > 60:
                    public.run_thread(self.get_web_info2)
                    public.WriteFile("data/wx_account_msg.lock",str(start_time))
            else:
                public.WriteFile("data/wx_account_msg.lock",str(start_time))
                public.run_thread(self.get_web_info2)
            data=json.loads(public.ReadFile(self.conf_path))


            if not 'list' in data: data['list'] = {}

            title = '默认'
            if 'res' in data and 'nickname' in data['res']: title = data['res']['nickname']

            data['list']['default'] = {'title':title,'data':''}

            data['default'] = self.__get_default_channel()
            return data
        else:
            public.run_thread(self.get_web_info2)
            return {"success":False,"res":"未获取到配置信息"}

    def set_config(self,get):
        """
        @设置默认值
        """
        if 'default' in get and get['default']:
            public.writeFile(self.__default_pl, self.__module_name)

        return public.returnMsg(True, public.lang("The setup was successful"))

    def get_web_info(self,get):
        if self.user_info is None: return public.returnMsg(False, public.lang("The user binding information was not obtained"))
        url = "https://wafapi2.aapanel.com/api/v2/user/wx_web/info"
        data = {
            "uid": self.user_info["uid"],
            "access_key": 'B' * 32,
            "serverid":self.user_info["server_id"]
        }
        try:

            datas = json.loads(public.httpPost(url,data))

            if datas["success"]:
                public.WriteFile(self.conf_path,json.dumps(datas))
                return public.returnMsg(True, datas)
            else:
                public.WriteFile(self.conf_path, json.dumps(datas))
                return public.returnMsg(False, datas)
        except:
            public.WriteFile(self.conf_path, json.dumps({"success":False,"res":"The link to the cloud failed, please check the network,请检查网络"}))
            return public.returnMsg(False, public.lang("The link to the cloud failed, please check the network"))

    def get_web_info2(self):
        if self.user_info is None: return public.returnMsg(False, public.lang("The user binding information was not obtained"))
        url = "https://wafapi2.aapanel.com/api/v2/user/wx_web/info"
        data = {
            "uid": self.user_info["uid"],
            "access_key": 'B' * 32,
            "serverid":self.user_info["server_id"]
        }
        try:
            datas = json.loads(public.httpPost(url,data))
            if datas["success"]:
                public.WriteFile(self.conf_path,json.dumps(datas))
                return public.returnMsg(True, datas)
            else:
                public.WriteFile(self.conf_path, json.dumps(datas))
                return public.returnMsg(False, datas)
        except:
            public.WriteFile(self.conf_path, json.dumps({"success":False,"res":"The link to the cloud failed, please check the network"}))
            return public.returnMsg(False, public.lang("The link to the cloud failed, please check the network"))

    def get_auth_url(self,get):
        if self.user_info is None: return public.returnMsg(False, public.lang("The user binding information was not obtained"))
        url = "https://wafapi2.aapanel.com/api/v2/user/wx_web/get_auth_url"
        data = {
            "uid": self.user_info["uid"],
            "access_key": 'B' * 32,
            "serverid":self.user_info["server_id"]
        }
        try:
            datas = json.loads(public.httpPost(url,data))
            if datas["success"]:
                return public.returnMsg(True, datas)
            else:
                return public.returnMsg(False, datas)
        except:
            return public.returnMsg(False, public.lang("The link to the cloud failed, please check the network"))


    def get_send_msg(self,msg):
        """
        @name 处理md格式
        """
        try:
            import re
            title = '宝塔告警通知'
            if msg.find("####") >= 0:
                try:
                    title = re.search(r"####(.+)", msg).groups()[0]
                except:pass

                msg = msg.replace("####",">").replace("\n\n","\n").strip()
                s_list = msg.split('\n')

                if len(s_list) > 3:
                    s_title = s_list[0].replace(" ","")
                    s_list = s_list[3:]
                    s_list.insert(0,s_title)
                    msg = '\n'.join(s_list)


            s_list = []
            for msg_info in msg.split('\n'):
                reg = '<font.+>(.+)</font>'
                tmp = re.search(reg,msg_info)
                if tmp:
                    tmp = tmp.groups()[0]
                    msg_info = re.sub(reg,tmp,msg_info)
                s_list.append(msg_info)
            msg = '\n'.join(s_list)
        except:pass
        return msg,title

    def send_msg(self,msg):
        """
        微信发送信息
        @msg 消息正文
        """

        if self.user_info is None:
            return public.returnMsg(False, public.lang("No user information was obtained"))

        msg,title = self.get_send_msg(msg)
        url="https://wafapi2.aapanel.com/api/v2/user/wx_web/send_template_msg_v2"
        datassss = {
            "first": {
                "value": "堡塔主机告警",
            },
            "keyword1": {
                "value": "内网IP " + self.get_local_ip() + "\n外网IP " + self.user_info["address"] + "  \n服务器别名 " + public.GetConfigValue("title"),
            },
            "keyword2": {
                "value": "堡塔主机告警",
            },
            "keyword3": {
                "value":  msg ,
            },
            "remark": {
                "value": "如有疑问，请联系宝塔客服",
            },
        }
        data = {
            "uid": self.user_info["uid"],
            "access_key": self.user_info["access_key"],
            "data":  base64.b64encode(json.dumps(datassss).encode('utf-8')).decode('utf-8')
        }

        try:
            res = {}
            error,success = 0,0

            x = json.loads(public.httpPost(url,data))
            # public.print_log(json.dumps(x))
            conf = self.get_config(None)['list']

            #立即刷新剩余次数
            public.run_thread(self.get_web_info2)

            res[conf['default']['title']] = 0
            if x['success']:
                res[conf['default']['title']] = 1
                success += 1
            else:
                error += 1

            try:
                public.write_push_log(self.__module_name,title,res)
            except:pass

            result = public.returnMsg(True,'Send complete.Send success :{}, send failure :{}',success,error)
            result['success'] = success
            result['error'] = error
            return result
        except:
            print(public.get_error_info())
            return public.returnMsg(False, public.lang("WeChat message delivery failed. --> {}", public.get_error_info()))

    def push_data(self,data):
        return self.send_msg(data['msg'])

    def uninstall(self):
        if os.path.exists(self.conf_path):
            os.remove(self.conf_path)