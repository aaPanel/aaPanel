# coding: utf-8
# +-------------------------------------------------------------------
# | 宝塔Linux面板
# +-------------------------------------------------------------------
# | Copyright (c) 2015-2019 宝塔软件(http://bt.cn) All rights reserved.
# +-------------------------------------------------------------------
# | Author: hwliang <hwl@bt.cn>
# +-------------------------------------------------------------------
import os
import sys
if not 'class/' in sys.path:
    sys.path.insert(0,'class/')
import public
import json
import time
from BTPanel import session,cache,request

class wxapp():

    def __init__(self):
        self.app_path = '/www/server/panel/data/'
        self.app_path_p = '/www/server/panel/plugin/app/'

    def _check(self, get):
        if get['fun'] in ['set_login', 'is_scan_ok', 'login_qrcode']:
            return True
        return public.returnMsg(False, 'UNAUTHORIZED')

    # 验证是否扫码成功
    def is_scan_ok(self, get):
        if os.path.exists(self.app_path+"app_login_check.pl"):
            key, init_time = public.readFile(self.app_path+'app_login_check.pl').split(':')
            if time.time() - float(init_time) > 60:
                return public.returnMsg(False, 'QRCORE_EXPIRE')
            session_id = public.get_session_id()
            if cache.get(session_id) == 'True':
                return public.returnMsg(True, 'Scan QRCORE successfully')
        return public.returnMsg(False, '')

    # 返回二维码地址
    def login_qrcode(self, get):
        tid = public.GetRandomString(12)
        qrcode_str = 'https://app.bt.cn/app.html?&panel_url='+public.getPanelAddr()+'&v=' + public.GetRandomString(3)+'?login&tid=' + tid
        data = public.get_session_id() + ':' + str(time.time())
        public.writeFile(self.app_path + "app_login_check.pl", data)
        cache.set(tid,public.get_session_id(),360)
        cache.set(public.get_session_id(),tid,360)
        return public.returnMsg(True, qrcode_str)

    # 设置登录状态
    def set_login(self, get):
        session_id = public.get_session_id()
        if cache.get(session_id) == 'True':
            return self.check_app_login(get)
        return public.returnMsg(False, 'Login failed 1')

     #验证APP是否登录成功
    def check_app_login(self,get):
        #判断是否存在绑定
        btapp_info = json.loads(public.readFile('/www/server/panel/config/api.json'))
        if not btapp_info:return public.returnMsg(False,'Unbound')
        if not btapp_info['open']:return public.returnMsg(False,'API is not turned on')
        if not 'apps' in btapp_info:return public.returnMsg(False,'Unbound phone')
        if not btapp_info['apps']:return public.returnMsg(False,'Unbound phone')
        try:
            session_id=public.get_session_id()
            if not os.path.exists(self.app_path+'app_login_check.pl'):return public.returnMsg(False,'Waiting for APP scan code login 1')
            data = public.readFile(self.app_path+'app_login_check.pl')
            public.ExecShell('rm ' + self.app_path+"app_login_check.pl")
            secret_key, init_time = data.split(':')
            if len(session_id)!=64:return public.returnMsg(False,'Waiting for APP scan code login 2')
            if len(secret_key)!=64:return public.returnMsg(False,'Waiting for APP scan code login 2')
            if time.time() - float(init_time) > 60:
                return public.returnMsg(False,'Waiting for APP scan code login')
            if session_id != secret_key:
                return public.returnMsg(False,'Waiting for APP scan code login')
            cache.delete(session_id)
            userInfo = public.M('users').where("id=?",(1,)).field('id,username').find()
            session['login'] = True
            session['username'] = userInfo['username']
            session['tmp_login'] = True
            public.WriteLog('TYPE_LOGIN','APP scan code login, account: {}, login IP: {}'.format(userInfo['username'],public.GetClientIp()+ ":" + str(request.environ.get('REMOTE_PORT'))))
            cache.delete('panelNum')
            cache.delete('dologin')
            session['session_timeout'] = time.time() + public.get_session_timeout()
            login_type = 'data/app_login.pl'
            self.set_request_token()
            import config
            config.config().reload_session()
            public.writeFile(login_type,'True')
            public.login_send_body("aaPanel Mobile",userInfo['username'],public.GetClientIp(),str(request.environ.get('REMOTE_PORT')))
            return public.returnMsg(True,'login successful!')
        except:
            return public.returnMsg(False, 'Login failed 2')
    #生成request_token
    def set_request_token(self):
        session['request_token_head'] = public.GetRandomString(48)
