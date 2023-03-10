#coding: utf-8
# +-------------------------------------------------------------------
# | 宝塔Linux面板
# +-------------------------------------------------------------------
# | Copyright (c) 2015-2099 宝塔软件(http:#bt.cn) All rights reserved.
# +-------------------------------------------------------------------
# | Author: hwliang <hwl@bt.cn>
# +-------------------------------------------------------------------

import public,os,sys,db,time,json,re
from BTPanel import session,cache,json_header
from flask import request,redirect,g

class userlogin:
    limit_expire_time = 0
    def request_post(self,post):
        if not hasattr(post, 'username') or not hasattr(post, 'password'):
            return public.returnJson(False,'User name or password cannot be empty!'),json_header
        
        self.error_num(False)
        if self.limit_address('?') < 1: return public.returnJson(False,'You have failed to log in many times。 Please wait for {} seconds and try again!'.format(int(self.limit_expire_time - time.time()))),json_header
        # if self.limit_address('?') < 1: return public.returnJson(False,'You cannot login now because login failed too many times!'),json_header
        post.username = post.username.strip()

        # 核验用户名密码格式
        if len(post.username) != 32: return public.return_msg_gettext(False,'Disk inode has been exhausted, the panel has attempted to release the inode. Please try again ...'),json_header
        if len(post.password) != 32: return public.return_msg_gettext(False,'Disk inode has been exhausted, the panel has attempted to release the inode. Please try again ...'),json_header
        if not re.match(r"^\w+$",post.username): return public.return_msg_gettext(False,'Disk inode has been exhausted, the panel has attempted to release the inode. Please try again ...'),json_header
        if not re.match(r"^\w+$",post.password): return public.return_msg_gettext(False,'Disk inode has been exhausted, the panel has attempted to release the inode. Please try again ...'),json_header
        last_login_token = session.get('last_login_token',None)
        if not last_login_token:
            public.write_log_gettext('Login','Verification code error, account number: {}, verification code: {}, login IP: {}',('****','****',public.GetClientIp()))
            return public.returnJson(False,"Verification failed, please refresh the page and log in again!"),json_header

        public.chdck_salt()
        sql = db.Sql()
        userInfo = None
        user_plugin_file = '{}/users_main.py'.format(public.get_plugin_path('users'))
        if os.path.exists(user_plugin_file):
            user_list = sql.table('users').field('id,username,password,salt').select()
            for u_info in user_list:
                if public.md5(public.md5(u_info['username'] + last_login_token)) == post.username:
                    userInfo = u_info
        else:
            userInfo = sql.table('users').where('id=?',1).field('id,username,password,salt').find()


        if 'code' in session:
            if session['code'] and not 'is_verify_password' in session:
                if not hasattr(post, 'code'): return public.returnJson(False,'Verification code can not be empty!'),json_header
                if not re.match(r"^\w+$",post.code): return public.returnJson(False,'Verification code is incorrect, please try again!'),json_header
                if not public.checkCode(post.code):
                    public.write_log_gettext('Login','Verification code is incorrect, Username:{}, Verification Code:{}, Login IP:{}',('****','****',public.GetClientIp()))
                    return public.returnJson(False,'Verification code is incorrect, please try again!'),json_header
        try:
            if not userInfo:
                public.write_log_gettext('Login','Wrong password, account: {}, password: {}, login IP: {}',('****','******',public.GetClientIp()))
                num = self.limit_address('+')
                if not num: return public.returnJson(False,'You have failed to log in many times, please wait {} seconds and try again!'.format(int(self.limit_expire_time - time.time()))),json_header
                return public.returnJson(False,'Username or password is wrong, <span style="color:red;">Please refresh the page and try again</span>, you can try again [{}] times'.format(num)),json_header

            if userInfo and not userInfo['salt']:
                public.chdck_salt()
                userInfo = sql.table('users').where('id=?',(userInfo['id'],)).field('id,username,password,salt').find()

            password = public.md5(post.password.strip() + userInfo['salt'])
            s_username = public.md5(public.md5(userInfo['username'] + last_login_token))
            if s_username != post.username or userInfo['password'] != password:
                public.write_log_gettext('Login','Password is incorrect, Username:{}, Password:{}, Login IP:{}',('****','******',public.GetClientIp()))
                num = self.limit_address('+')
                if not num: return public.returnJson(False,'You have failed to log in many times, please wait {} seconds and try again!'.format(int(self.limit_expire_time - time.time()))),json_header
                return public.returnJson(False,'Invalid username or password. You have [{}] times left to try!',(str(num),)),json_header
            _key_file = "/www/server/panel/data/two_step_auth.txt"

            # 密码过期检测
            if sys.path[0] != 'class/': sys.path.insert(0,'class/')
            if not public.password_expire_check():
                session['password_expire'] = True

            # public.login_send_body("Userinfo",userInfo['username'],public.GetClientIp(),str(request.environ.get('REMOTE_PORT')))
            if hasattr(post,'vcode'):
                if not re.match(r"^\d+$",post.vcode): return public.returnJson(False,'Incorrect format of verification code'),json_header
                if self.limit_address('?',v="vcode") < 1: return public.returnJson(False,'You have failed verification many times, forbidden for 10 minutes'),json_header
                import pyotp
                secret_key = public.readFile(_key_file)
                if not secret_key:
                    return public.returnJson(False, "Did not find the key, please close Google verification on the command line and trun on again"),json_header
                t = pyotp.TOTP(secret_key)
                result = t.verify(post.vcode)
                if not result:
                    if public.sync_date(): result = t.verify(post.vcode)
                    if not result:
                        num = self.limit_address('++',v="vcode")
                        return public.returnJson(False, 'Invalid Verification code. You have [{}] times left to try!'.format(num)), json_header
                now = int(time.time())
                # public.run_thread(public.login_send_body,("account",userInfo['username'],public.GetClientIp(),str(int(request.environ.get('REMOTE_PORT')))))
                public.writeFile("/www/server/panel/data/dont_vcode_ip.txt",json.dumps({"client_ip":public.GetClientIp(),"add_time":now}))
                self.limit_address('--',v="vcode")
                self.set_cdn_host(post)
                return self._set_login_session(userInfo)

            acc_client_ip = self.check_two_step_auth()

            if not os.path.exists(_key_file) or acc_client_ip:
                # public.run_thread(public.login_send_body,("account",userInfo['username'],public.GetClientIp(),str(int(request.environ.get('REMOTE_PORT')))))
                self.set_cdn_host(post)
                return self._set_login_session(userInfo)
            self.limit_address('-')
            session['is_verify_password'] = True
            return "1"
        except Exception as ex:
            stringEx = str(ex)
            if stringEx.find('unsupported') != -1 or stringEx.find('-1') != -1: 
                public.ExecShell("rm -f /tmp/sess_*")
                public.ExecShell("rm -f /www/wwwlogs/*log")
                public.ServiceReload()
                return public.returnJson(False,'USER_INODE_ERR'),json_header
            public.write_log_gettext('Login','Password is incorrect, Username:{}, Password:{}, Login IP:{}',('****','******',public.GetClientIp()))
            num = self.limit_address('+')
            if not num: return public.returnJson(False,'You have failed to log in many times, please wait {} seconds and try again!'.format(int(self.limit_expire_time - time.time()))),json_header
            return public.returnJson(False,'Invalid username or password. You have [{}] times left to try!',(str(num),)),json_header

    def request_tmp(self,get):
        try:
            if not hasattr(get,'tmp_token'): return public.returnJson(False,'Parameter ERROR!'),json_header
            if len(get.tmp_token) == 48:
                return self.request_temp(get)
            if len(get.tmp_token) != 64: return public.returnJson(False,'Parameter ERROR!'),json_header
            if not re.match(r"^\w+$",get.tmp_token):return public.returnJson(False,'Parameter ERROR!'),json_header
            save_path = '/www/server/panel/config/api.json'
            data = json.loads(public.ReadFile(save_path))
            if not 'tmp_token' in data or not 'tmp_time' in data: return public.returnJson(False,'Verification failed'),json_header
            if (time.time() - data['tmp_time']) > 120: return public.returnJson(False,'Expired Token'),json_header
            if get.tmp_token != data['tmp_token']: return public.returnJson(False,'Invalid Token!'),json_header
            userInfo = public.M('users').where("id=?",(1,)).field('id,username').find()
            session['login'] = True
            session['username'] = userInfo['username']
            session['tmp_login'] = True
            session['uid'] = userInfo['id']
            ids = public.write_log_gettext('Login','Login success',(userInfo['username'],public.GetClientIp()+ ":" + str(request.environ.get('REMOTE_PORT'))))
            public.cache_set(public.GetClientIp() + ":" + str(request.environ.get('REMOTE_PORT')), ids)
            self.limit_address('-')
            cache.delete('panelNum')
            cache.delete('dologin')
            session['session_timeout'] = time.time() + public.get_session_timeout()
            del(data['tmp_token'])
            del(data['tmp_time'])
            public.writeFile(save_path,json.dumps(data))
            self.set_request_token()
            self.login_token()
            self.set_cdn_host(get)
            return redirect('/')
        except:
            return public.returnJson(False,'Login failed,' + public.get_error_info()),json_header


    def request_temp(self,get):
        try:
            if len(get.__dict__.keys()) > 2: return public.get_msg_gettext('Parameter ERROR!')
            if not hasattr(get,'tmp_token'): return public.get_msg_gettext('Parameter ERROR!')
            if len(get.tmp_token) != 48: return public.get_msg_gettext('Parameter ERROR!')
            if not re.match(r"^\w+$",get.tmp_token):return public.get_msg_gettext('Parameter ERROR!')
            skey = public.GetClientIp() + '_temp_login'
            if not public.get_error_num(skey,10): return public.get_msg_gettext('10 consecutive authentication failures are prohibited for 1 hour')
            s_time = int(time.time())
            if public.M('temp_login').where('state=? and expire>?',(0,s_time)).field('id,token,salt,expire').count()==0:
                public.set_error_num(skey)
                return public.get_msg_gettext('Verification failed')

            data = public.M('temp_login').where('state=? and expire>?',(0,s_time)).field('id,token,salt,expire').find()
            if not data:
                public.set_error_num(skey)
                return public.get_msg_gettext('Verification failed')
            if not isinstance(data,dict):
                public.set_error_num(skey)
                return public.get_msg_gettext('Verification failed')
            r_token = public.md5(get.tmp_token + data['salt'])
            if r_token != data['token']:
                public.set_error_num(skey)
                return public.get_msg_gettext('Verification failed')
            public.set_error_num(skey,True)
            userInfo = public.M('users').where("id=?",(1,)).field('id,username').find()
            session['login'] = True
            session['username'] = public.get_msg_gettext('TEMPORARY_ID',(data['id'],))
            session['tmp_login'] = True
            session['tmp_login_id'] = str(data['id'])
            session['tmp_login_expire'] = time.time() + 3600
            session['uid'] = data['id']
            sess_path = 'data/session'
            if not os.path.exists(sess_path):
                os.makedirs(sess_path,384)
            public.writeFile(sess_path + '/' + str(data['id']),'')
            login_addr = public.GetClientIp()+ ":" + str(request.environ.get('REMOTE_PORT'))
            ids = public.write_log_gettext('Login','Login succeed, Username: {}, Login IP: {}',(userInfo['username'],login_addr))
            public.cache_set(public.GetClientIp()+ ":" + str(request.environ.get('REMOTE_PORT')),ids)
            public.M('temp_login').where('id=?',(data['id'],)).update({"login_time":s_time,'state':1,'login_addr':login_addr})
            self.limit_address('-')
            cache.delete('panelNum')
            cache.delete('dologin')
            session['session_timeout'] = time.time() + public.get_session_timeout()
            self.set_request_token()
            self.login_token()
            self.set_cdn_host(get)
            public.run_thread(public.login_send_body("Temporary authorization",userInfo['username'],public.GetClientIp(),str(request.environ.get('REMOTE_PORT'))))
            return redirect('/')
        except:
            return public.get_msg_gettext('Login failed')


    def login_token(self):
        import config
        config.config().reload_session()

    def request_get(self,get):
        '''
            @name 验证登录页面请求权限
            @author hwliang
            @return False | Response
        '''
        # 获取标题
        if not 'title' in session: session['title'] = public.getMsg('NAME')

        # 验证是否使用限制的域名访问
        domain_check = public.check_domain_panel()
        if domain_check: return domain_check

        # 验证是否使用限制的IP地址访问
        ip_check = public.check_ip_panel()
        if ip_check: return ip_check

        # 验证是否已经登录
        if 'login' in session:
            if session['login'] == True:
                return redirect('/')
        
        # 复位验证码
        if not 'code' in session:
            session['code'] = False

        # 记录错误次数
        self.error_num(False)

    #生成request_token
    def set_request_token(self):
        html_token_key = public.get_csrf_html_token_key()
        session[html_token_key] = public.GetRandomString(48)
        session[html_token_key.replace("https_","")] = public.GetRandomString(48)


    def set_cdn_host(self,get):
        try:
            if not 'cdn_url' in get: return True
            plugin_path = 'plugin/static_cdn'
            if not os.path.exists(plugin_path): return True
            cdn_url = public.get_cdn_url()
            if not cdn_url or cdn_url == get.cdn_url: return True
            public.set_cdn_url(get.cdn_url)
        except:
            return False

    #防暴破
    def error_num(self,s = True):
        nKey = 'panelNum'
        num = cache.get(nKey)
        if not num:
            cache.set(nKey,1)
            num = 1
        if s: cache.inc(nKey,1)
        if num > 6: session['code'] = True

    #IP限制
    def limit_address(self,type,v=""):
        clientIp = public.GetClientIp()
        numKey = 'limitIpNum_' + v + clientIp
        limit = 5
        outTime = 300
        try:
            #初始化
            num1 = cache.get(numKey)
            if not num1:
                cache.set(numKey,0,outTime)
                num1 = 0

            self.limit_expire_time = cache.get_expire_time(numKey)

            #计数
            if type == '+':
                cache.inc(numKey,1)
                self.error_num()
                session['code'] = True
                return limit - (num1+1)

            #计数验证器
            if type == '++':
                cache.inc(numKey,1)
                self.error_num()
                session['code'] = False
                return limit - (num1+1)

            #清空
            if type == '-':
                cache.delete(numKey)
                session['code'] = False
                return 1

            #清空验证器
            if type == '--':
                cache.delete(numKey)
                session['code'] = False
                return 1
            return limit - num1
        except:
            return limit

    # 登录成功设置session
    def _set_login_session(self,userInfo):
        try:
            session['login'] = True
            session['username'] = userInfo['username']
            session['uid'] = userInfo['id']
            session['login_user_agent'] = public.md5(request.headers.get('User-Agent',''))
            ids = public.write_log_gettext('Login','Login succeed, Username: {}, Login IP: {}',(userInfo['username'],public.GetClientIp()+ ":" + str(request.environ.get('REMOTE_PORT'))))
            public.cache_set(public.GetClientIp()+ ":" + str(request.environ.get('REMOTE_PORT')),ids)
            self.limit_address('-')
            cache.delete('panelNum')
            cache.delete('dologin')
            session['session_timeout'] = time.time() + public.get_session_timeout()
            if 'last_login_token' in session: del(session['last_login_token'])
            self.set_request_token()
            self.login_token()
            login_type = 'data/app_login.pl'
            if os.path.exists(login_type):
                os.remove(login_type)
            try:
                default_pl = "{}/default.pl".format(public.get_panel_path())
                public.writeFile(default_pl,"********")
                public.run_thread(public.login_send_body, (
                "Userinfo", userInfo['username'], public.GetClientIp(), str(request.environ.get('REMOTE_PORT'))))
            except:
                pass
            return public.returnJson(True,'Login succeeded, loading...'),json_header
        except Exception as ex:
            stringEx = str(ex)
            if stringEx.find('unsupported') != -1 or stringEx.find('-1') != -1:
                public.ExecShell("rm -f /tmp/sess_*")
                public.ExecShell("rm -f /www/wwwlogs/*log")
                public.ServiceReload()
                return public.returnJson(False,'Disk inode has been exhausted, the panel has attempted to release the inode. Please try again ...'),json_header
            public.write_log_gettext('Login','Password is incorrect, Username:{}, Password:{}, Login IP:{}',('****','******',public.GetClientIp()))
            num = self.limit_address('+')
            return public.returnJson(False,'Invalid username or password. You have [{}] times left to try!',(str(num),)),json_header


    # 检查是否需要进行二次验证
    def check_two_step_auth(self):
        dont_vcode_ip_info = public.readFile("/www/server/panel/data/dont_vcode_ip.txt")
        acc_client_ip = False
        if dont_vcode_ip_info:
            dont_vcode_ip_info = json.loads(dont_vcode_ip_info)
            ip = dont_vcode_ip_info["client_ip"] == public.GetClientIp()
            now = int(time.time())
            v_time = now - int(dont_vcode_ip_info["add_time"])
            if ip and v_time < 86400:
                acc_client_ip = True
        return acc_client_ip

    # 清理多余SESSION数据
    def clear_session(self):
        try:
            session_file = '/dev/shm/session.db'
            if not os.path.exists(session_file): return False
            s_size = os.path.getsize(session_file)
            if s_size < 1024 * 512: return False
            if s_size > 1024 * 1024 * 10:
                from BTPanel import sdb
                if os.path.exists(session_file): os.remove(session_file)
                sdb.create_all()
                if not os.path.exists(session_file):
                    public.writeFile('/www/server/panel/data/reload.pl','True')
                    return False
            return True
        except:
            return False

