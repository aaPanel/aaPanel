#coding: utf-8
# +-------------------------------------------------------------------
# | aaPanel
# +-------------------------------------------------------------------
# | Copyright (c) 2015-2099 aaPanel(www.aapanel.com) All rights reserved.
# +-------------------------------------------------------------------
# | Author: hwliang <hwl@aapanel.com>
# +-------------------------------------------------------------------

import public,os,sys,db,time,json,re
from BTPanel import session,cache,json_header
from flask import request,redirect,g

class userlogin:
    limit_expire_time = 0

    def request_post(self,post):
        if not hasattr(post, 'username') or not hasattr(post, 'password'):
            return  public.returnJson(False,public.lang('User name or password cannot be empty!')),json_header
        self.error_num(False)
        if self.limit_address('?') < 1: return public.returnJson(False,public.lang('You have failed to log in many times, please try again in {} seconds!',int(self.limit_expire_time - time.time()))),json_header
        post.username = post.username.strip()
        format_error = 'Parameter format error'

        # 核验用户名密码格式
        post.username = public.rsa_decrypt(post.username)

        if len(post.username) != 32:
            return public.returnMsg(False,format_error+"1"),json_header
        post.password = public.rsa_decrypt(post.password)
        if len(post.password) != 32:
            return public.returnMsg(False,format_error+"2"),json_header

        if not re.match(r"^\w+$",post.username): return public.return_msg_gettext(False, public.lang("Disk inode has been exhausted, the panel has attempted to release the inode. Please try again ...")),json_header
        if not re.match(r"^\w+$",post.password): return public.return_msg_gettext(False, public.lang("Disk inode has been exhausted, the panel has attempted to release the inode. Please try again ...")),json_header
        last_login_token = session.get('last_login_token',None)
        if not last_login_token:
            public.WriteLog('TYPE_LOGIN','LOGIN_ERR_CODE',('****','****',public.GetClientIp()))
            return  public.returnJson(False,public.lang("Verification failed, please refresh the page and log in again!")),json_header

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
                if not hasattr(post, 'code'): return  public.returnJson(False,public.lang('Verification code can not be empty!')),json_header
                if not re.match(r"^\w+$",post.code): return  public.returnJson(False,public.lang('Verification code is incorrect, please try again!')),json_header
                if not public.checkCode(post.code):
                    public.write_log_gettext('Login','Verification code is incorrect, Username:{}, Verification Code:{}, Login IP:{}',('****','****',public.GetClientIp()))
                    return  public.returnJson(False,public.lang('Verification code is incorrect, please try again!')),json_header

        try:
            if not userInfo or not isinstance(userInfo, dict):
                public.WriteLog('TYPE_LOGIN','LOGIN_ERR_PASS',('****','******',public.GetClientIp()))
                num = self.limit_address('+')
                if not num: return  public.returnJson(False,public.lang('You have failed to log in many times, please try again in {} seconds!',int(self.limit_expire_time - time.time()))),json_header
                return  public.returnJson(False,public.lang('wrong user name or password，<span style="color:red;">please refresh the page and try again</span>，You can retry {} more times',num)),json_header

            if userInfo and not userInfo['salt']:
                public.chdck_salt()
                userInfo = sql.table('users').where('id=?',(userInfo['id'],)).field('id,username,password,salt').find()

            password = public.md5(post.password.strip() + userInfo['salt'])
            s_username = public.md5(public.md5(userInfo['username'] + last_login_token))
            if s_username != post.username or userInfo['password'] != password:
                public.write_log_gettext('Login','Password is incorrect, Username:{}, Password:{}, Login IP:{}',('****','******',public.GetClientIp()))
                num = self.limit_address('+')
                if not num: return  public.returnJson(False,public.lang('You failed to log in many times, please try again in {} seconds!',int(self.limit_expire_time - time.time()))),json_header
                return  public.returnJson(False,public.lang('Invalid username or password. You have [{}] times left to try!',str(num))),json_header
            _key_file = "/www/server/panel/data/two_step_auth.txt"

            area_check = public.check_area_panel()
            if area_check: return area_check

            # 密码过期检测
            if sys.path[0] != 'class/': sys.path.insert(0,'class/')
            if not public.password_expire_check():
                session['password_expire'] = True

            #登陆告警
            #public.run_thread(public.login_send_body,("账号密码",userInfo['username'],public.GetClientIp(),str(int(request.environ.get('REMOTE_PORT')))))
            # public.login_send_body("账号密码",userInfo['username'],public.GetClientIp(),str(request.environ.get('REMOTE_PORT')))
            if hasattr(post,'vcode'):
                if not re.match(r"^\d+$",post.vcode): return  public.returnJson(False,public.lang('Incorrect format of verification code')),json_header
                if self.limit_address('?',v="vcode") < 1: return  public.returnJson(False,public.lang('You have failed verification many times, forbidden for 10 minutes')),json_header
                import pyotp
                secret_key = public.readFile(_key_file)
                if not secret_key:
                    return  public.returnJson(False,public.lang( "Did not find the key, please close Google verification on the command line and trun on again")),json_header
                t = pyotp.TOTP(secret_key)
                result = t.verify(post.vcode)
                if not result:
                    if public.sync_date(): result = t.verify(post.vcode)
                    if not result:
                        num = self.limit_address('++',v="vcode")
                        return  public.returnJson(False,public.lang( 'Invalid Verification code. You have [{}] times left to try!',num)), json_header
                now = int(time.time())
                # public.run_thread(public.login_send_body,("account",userInfo['username'],public.GetClientIp(),str(int(request.environ.get('REMOTE_PORT')))))
                public.writeFile("/www/server/panel/data/dont_vcode_ip.txt",json.dumps({"client_ip":public.GetClientIp(),"add_time":now}))
                self.limit_address('--',v="vcode")
                self.set_cdn_host(post)
                return self._set_login_session(userInfo)

            acc_client_ip = self.check_two_step_auth()

            if not os.path.exists(_key_file) or acc_client_ip:
                try:
                    port_str = str(int(request.environ.get('REMOTE_PORT', 0)))
                except (ValueError, TypeError):
                    port_str = '0'
                public.run_thread(public.login_send_body,("account",userInfo['username'],public.GetClientIp(),port_str))
                self.set_cdn_host(post)
                return self._set_login_session(userInfo, acc_client_ip)

            self.limit_address('-')
            session['is_verify_password'] = True
            return "1"
        except Exception as ex:
            stringEx = str(ex)
            if stringEx.find('unsupported') != -1 or stringEx.find('-1') != -1:
                public.ExecShell("rm -f /tmp/sess_*")
                public.ExecShell("rm -f /www/wwwlogs/*log")
                public.ServiceReload()
                return  public.returnJson(False,public.lang('USER_INODE_ERR')),json_header
            public.write_log_gettext('Login','Password is incorrect, Username:{}, Password:{}, Login IP:{}',('****','******',public.GetClientIp()))
            num = self.limit_address('+')
            if not num:
                return  public.returnJson(False,public.lang('You have failed to log in many times, please wait {} seconds and try again!',int(self.limit_expire_time - time.time()))),json_header
            # return public.returnJson(False,'Invalid username or password. You have [{}] times left to try!',(str(num),)),json_header

            # 2024/1/3 下午 2:31 记录登录时捕捉不到合适的错误，记录到文件中易于排查
            import traceback
            public.writeFile(
                '/www/server/panel/data/login_err.log',
                public.getDate() + '\n' + str(traceback.format_exc() + "\n"),
                mode='a+'
            )

            # 提交错误登录信息
            _form = request.form.to_dict()
            if 'username' in _form: _form['username'] = '******'
            if 'password' in _form: _form['password'] = '******'
            if 'phone' in _form: _form['phone'] = '******'

            # 错误信息
            error_infos = {
                "REQUEST_DATE": public.getDate(),  # 请求时间
                "PANEL_VERSION": public.version(),  # 面板版本
                "OS_VERSION": public.get_os_version(),  # 操作系统版本
                "REMOTE_ADDR": public.GetClientIp(),  # 请求IP
                "REQUEST_URI": request.method + request.full_path,  # 请求URI
                "REQUEST_FORM": public.xsssec(str(_form)),  # 请求表单
                "USER_AGENT": public.xsssec(request.headers.get('User-Agent')),  # 客户端连接信息
                "ERROR_INFO": str(traceback.format_exc()),  # 错误信息
                "PACK_TIME": public.readFile("/www/server/panel/config/update_time.pl") if os.path.exists("/www/server/panel/config/update_time.pl") else public.getDate(),  # 打包时间
                "TYPE": 100,
                "ERROR_ID": str(ex)
            }
            pkey = public.Md5(error_infos["ERROR_INFO"])

            # 提交
            if not public.cache_get(pkey):
                try:
                    public.run_thread(public.httpPost, ("https://geterror.aapanel.com/bt_error/index.php", error_infos))
                    public.cache_set(pkey, 1, 1800)
                except Exception as e:
                    pass

            return (public.returnJson(
                False, 'Login error, details:【{}】'.format(stringEx)),
                    json_header)

    def request_tmp(self,get):
        try:
            if not hasattr(get,'tmp_token'): return  public.returnJson(False,public.lang('Parameter ERROR!')),json_header
            if len(get.tmp_token) == 48:
                return self.request_temp(get)
            if len(get.tmp_token) != 64: return  public.returnJson(False,public.lang('Parameter ERROR!')),json_header
            if not re.match(r"^\w+$",get.tmp_token):return  public.returnJson(False,public.lang('Parameter ERROR!')),json_header
            save_path = '/www/server/panel/config/api.json'
            data = json.loads(public.ReadFile(save_path))
            if not 'tmp_token' in data or not 'tmp_time' in data: return  public.returnJson(False,public.lang('Verification failed')),json_header
            if (time.time() - data['tmp_time']) > 120: return  public.returnJson(False,public.lang('Expired Token')),json_header
            if get.tmp_token != data['tmp_token']: return  public.returnJson(False,public.lang('Invalid Token!')),json_header
            userInfo = public.M('users').where("id=?",(1,)).field('id,username').find()
            session['login'] = True
            session['username'] = userInfo['username']
            session['tmp_login'] = True
            session['uid'] = userInfo['id']
            ids=public.WriteLog('TYPE_LOGIN','Login success',(userInfo['username'],public.GetClientIp()+ ":" + str(request.environ.get('REMOTE_PORT'))))
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
            return public.returnJson(False, public.lang('Login failed,') + public.get_error_info()),json_header


    def request_temp(self, get):
        try:
            if len(get.get_items().keys()) > 2:
                return public.lang("Parameter ERROR!")
            if not hasattr(get, 'tmp_token'):
                return public.lang("Parameter ERROR!")
            if len(get.tmp_token) != 48:
                return public.lang("Parameter ERROR!")
            if not re.match(r"^\w+$", get.tmp_token):
                return public.lang("Parameter ERROR!")

            skey = public.GetClientIp() + '_temp_login'
            if not public.get_error_num(skey, 10):
                return public.lang("10 consecutive authentication failures are prohibited for 1 hour")
            s_time = int(time.time())
            if public.M('temp_login').where('state=? and expire>?',(0, s_time)).field('id,token,salt,expire').count()==0:
                public.set_error_num(skey)
                return public.lang("Verification failed")

            data = public.M('temp_login').where('state=? and expire>?',(0,s_time)).field('id,token,salt,expire').find()
            if data is None or not isinstance(data,dict):
                public.set_error_num(skey)
                return public.lang("Verification failed")
            r_token = public.md5(get.tmp_token + data['salt'])
            if r_token != data['token']:
                public.set_error_num(skey)
                return public.lang("Verification failed")

            public.set_error_num(skey, True)
            userInfo = public.M('users').where("id=?",(1,)).field('id,username').find()
            session['login'] = True
            session['username'] = public.lang('TEMPORARY_ID({})',data['id'])
            session['tmp_login'] = True
            session['tmp_login_id'] = str(data['id'])
            session['tmp_login_expire'] = data['expire']
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
            public.run_thread(
                public.login_send_body(
                    "Temporary authorization",userInfo['username'],public.GetClientIp(),str(request.environ.get('REMOTE_PORT'))
                )
            )
            return redirect('/')
        except:
            public.print_log(public.get_error_info(),'ERROR')
            return public.lang("Login failed")


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
        #session['client_hash'] = public.get_client_hash()

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
        import time
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
    def _set_login_session(self,userInfo, acc_client_ip=None):
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
            except:
                pass

            address = public.GetClientIp()
            port =  str(request.environ.get('REMOTE_PORT'))

            login_address = '{}(unknown)'.format(address,)
            # #返回增加登录地区
            # res = public.returnMsg(True,'LOGIN_SUCCESS')
            # 返回增加登录地区
            res = public.returnMsg(True, 'LOGIN_SUCCESS') if not acc_client_ip else public.returnMsg(True,
            'Login success, your ip: [{}] has been dynamic password authentication, authentication free within 24 hours!'.format(
                                                                                                         address))

            res['login_time'] = time.time()
            res['login_time_str'] = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
            try:
                ip_info = public.get_free_ip_info(address)
                if 'city' in ip_info:
                    res['ip_info'] = ip_info
                if 'Internal network address' in ip_info['info']:
                    res['ip_info'] = ip_info
                    res['ip_info']['ip'] = address
                login_address = '{}({})'.format(address,ip_info['info'])
            except:
                print(public.get_error_info())

            last_login = {}
            last_file = 'data/last_login.pl'
            try:
                last_login = json.loads(public.readFile(last_file))
            except:pass
            public.writeFile(last_file,json.dumps(res))

            res['last_login'] = last_login
            session['login_address'] = public.xsssec(login_address)
            session['login_time'] = res['login_time']  # 记录登录时间，验证客户端时要用，不要删除
            public.record_client_info()
            return public.getJson(res),json_header
        except Exception as ex:
            stringEx = str(ex)
            if stringEx.find('unsupported') != -1 or stringEx.find('-1') != -1:
                public.ExecShell("rm -f /tmp/sess_*")
                public.ExecShell("rm -f /www/wwwlogs/*log")
                public.ServiceReload()
                return  public.returnJson(False,public.lang('Disk inode has been exhausted, the panel has attempted to release the inode. Please try again ...')),json_header
            public.write_log_gettext('Login','Password is incorrect, Username:{}, Password:{}, Login IP:{}',('****','******',public.GetClientIp()))
            num = self.limit_address('+')
            return public.returnJson(False,public.lang('Invalid username or password. You have [{}] times left to try!',str(num))),json_header


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

