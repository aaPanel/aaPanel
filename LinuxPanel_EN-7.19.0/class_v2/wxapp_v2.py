# coding: utf-8
# +-------------------------------------------------------------------
# | aaPanel
# +-------------------------------------------------------------------
# | Copyright (c) 2015-2019 aaPanel(www.aapanel.com) All rights reserved.
# +-------------------------------------------------------------------
# | Author: hwliang <hwl@aapanel.com>
# +-------------------------------------------------------------------
import os
import sys
if not 'class/' in sys.path:
    sys.path.insert(0,'class/')
import public
import json
import time
import uuid
from BTPanel import session,cache,request

class wxapp():

    def __init__(self):
        self.app_path = '/www/server/panel/data/'
        self.app_path_p = '/www/server/panel/plugin/app/'

    def _check(self, get):
        if get['fun'] in ['set_login', 'is_scan_ok', 'login_qrcode']:
            return True
        return public.returnMsg(False, public.lang("Unauthorized"))

    # 验证是否扫码成功
    def is_scan_ok(self, get):
        if os.path.exists(self.app_path+"app_login_check.pl"):
            try:
                key, init_time, tid, status = public.readFile(self.app_path+'app_login_check.pl').split(':')
                if time.time() - float(init_time) > 60:
                    return public.returnMsg(False, public.lang("QR code expired"))
                session_id = public.get_session_id()
                if cache.get(session_id) == public.md5(uuid.UUID(int=uuid.getnode()).hex):
                    return public.returnMsg(True, public.lang("Scan QRCORE successfully"))
            except:
                os.remove(self.app_path + "app_login_check.pl")
                return public.returnMsg(False, public.lang(""))
        return public.returnMsg(False, public.lang(""))

    # 返回二维码地址
    def login_qrcode(self, get):
        tid = public.GetRandomString(32)
        qrcode_str = 'https://app.bt.cn/app.html?&panel_url='+public.getPanelAddr()+'&v=' + public.GetRandomString(3)+'?login&tid=' + tid
        data = public.get_session_id() + ':' + str(time.time()) + ':' + tid + ':' + tid
        public.writeFile(self.app_path + "app_login_check.pl", data)
        cache.set(tid,public.get_session_id(),360)
        cache.set(public.get_session_id(),tid,360)
        return public.returnMsg(True, qrcode_str)

    # 设置登录状态
    def set_login(self, get):
        session_id = public.get_session_id()
        if cache.get(session_id):
            if cache.get(session_id) == public.md5(uuid.UUID(int=uuid.getnode()).hex):
                return self.check_app_login(get)
            else:
                cache.delete(cache.get(session_id))
                cache.delete(session_id)
                return public.returnMsg(False, public.lang("Login failed 2"))
        return public.returnMsg(False, public.lang("Login failed 1"))

     #验证APP是否登录成功
    def check_app_login(self,get):
        #判断是否存在绑定
        btapp_info = json.loads(public.readFile('/www/server/panel/config/api.json'))
        if not btapp_info:return public.returnMsg(False, public.lang("Unbound!"))
        if not btapp_info['open']:return public.returnMsg(False, public.lang("API is not turned on"))
        if not 'apps' in btapp_info:return public.returnMsg(False, public.lang("Unbound phone"))
        if not btapp_info['apps']:return public.returnMsg(False, public.lang("Unbound phone"))
        try:
            session_id=public.get_session_id()
            if not os.path.exists(self.app_path+'app_login_check.pl'):return public.returnMsg(False, public.lang("Waiting for APP scan code login 1"))
            data = public.readFile(self.app_path+'app_login_check.pl')
            public.ExecShell('rm ' + self.app_path+"app_login_check.pl")
            secret_key, init_time, tid, status = data.split(':')
            if len(session_id)!=64:return public.returnMsg(False, public.lang("Waiting for APP scan code login 2"))
            if len(secret_key)!=64:return public.returnMsg(False, public.lang("Waiting for APP scan code login 2"))
            if  session_id != secret_key:
                    return public.returnMsg(False, public.lang("QR code expired"))
            if time.time() - float(init_time) > 60:
                return public.returnMsg(False, public.lang("Waiting for APP scan code login"))
            import uuid
            if status != uuid.UUID(int=uuid.getnode()).hex[-12:]: return public.returnMsg(False, public.lang("当前二维码失效222"))
            cache.delete(session_id)
            cache.delete(tid)
            userInfo = public.M('users').where("id=?",(1,)).field('id,username').find()
            session['login'] = True
            session['username'] = userInfo['username']
            session['tmp_login'] = True
            public.WriteLog('Login','APP scan code login, account: {}, login IP: {}'.format(userInfo['username'],public.GetClientIp()+ ":" + str(request.environ.get('REMOTE_PORT'))))
            cache.delete('panelNum')
            cache.delete('dologin')
            session['session_timeout'] = time.time() + public.get_session_timeout()
            login_type = 'data/app_login.pl'
            self.set_request_token()
            import config
            config.config().reload_session()
            public.writeFile(login_type,'True')
            public.login_send_body("aaPanel Mobile",userInfo['username'],public.GetClientIp(),str(request.environ.get('REMOTE_PORT')))
            return public.returnMsg(True, public.lang("login successful!"))
        except:
            return public.returnMsg(False, public.lang("Login failed 2"))
    #生成request_token
    def set_request_token(self):
        session['request_token_head'] = public.GetRandomString(48)
