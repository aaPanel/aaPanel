# coding: utf-8
# +-------------------------------------------------------------------
# | aaPanel x3
# +-------------------------------------------------------------------
# | Copyright (c) 2015-2017 aaPanel(www.aapanel.com) All rights reserved.
# +-------------------------------------------------------------------
# | Author: hwliang <hwl@aapanel.com>
# +-------------------------------------------------------------------
import public, re, os, nginx, apache, json, time, ols
from public.validate import Param
try:
    import pyotp
except:
    public.ExecShell("pip install pyotp &")
try:
    from BTPanel import (
        session,
        admin_path_checks,
        g,
        request,
        cache,
    )
    import send_mail
except:
    pass


class config:
    __mail_list = []
    __weixin_user = []
    _setup_path = "/www/server/panel"
    _key_file = _setup_path + "/data/two_step_auth.txt"
    _bk_key_file = _setup_path + "/data/bk_two_step_auth.txt"
    _username_file = _setup_path + "/data/username.txt"
    _core_fle_path = _setup_path + '/data/qrcode'
    __mail_config = _setup_path + '/data/stmp_mail.json'
    __mail_list_data = _setup_path + '/data/mail_list.json'
    __dingding_config = _setup_path + '/data/dingding.json'
    __panel_asset_config = '/www/server/panel/data/panel_asset.json'


    def __init__(self):
        try:
            ssl_dir = os.path.join(self._setup_path, "ssl")
            if not os.path.exists(ssl_dir):
                os.makedirs(ssl_dir)

            self.mail = send_mail.send_mail()
            if not os.path.exists(self.__mail_list_data):
                ret = []
                public.writeFile(self.__mail_list_data, json.dumps(ret))
            else:
                try:
                    mail_data = json.loads(public.ReadFile(self.__mail_list_data))
                    self.__mail_list = mail_data
                except:
                    ret = []
                    public.writeFile(self.__mail_list_data, json.dumps(ret))
        except:
            pass

    # 返回配置邮件地址
    def return_mail_list(self, get):
        return public.return_message(0, 0, self.__mail_list)

    # 删除邮件接口
    def del_mail_list(self, get):
        emial = get.email.strip()
        if emial in self.__mail_list:
            self.__mail_list.remove(emial)
            public.writeFile(self.__mail_list_data, json.dumps(self.__mail_list))
            return public.return_message(0, 0, public.lang("Successfully deleted"))
        else:
            return public.return_message(0, 0, public.lang("Email does not exist"))

    def del_tg_info(self, get):
        import panel_telegram_bot
        return panel_telegram_bot.panel_telegram_bot().del_tg_bot(get)

    def set_tg_bot(self, get):
        import panel_telegram_bot
        return panel_telegram_bot.panel_telegram_bot().set_tg_bot(get)

    # 添加接受邮件地址
    def add_mail_address(self, get):
        if not hasattr(get, 'email'): return public.return_message(-1, 0, public.lang("Please input your email"))
        emailformat = re.compile(r'[a-zA-Z0-9.-_+%]+@[a-zA-Z0-9]+\.[a-zA-Z0-9]+')
        if not emailformat.search(get.email): return public.return_message(-1, 0, public.lang("Please enter your vaild email"))
        # 测试发送邮件
        if get.email.strip() in self.__mail_list: return public.return_message(0, 0, public.lang("Email already exists"))
        self.__mail_list.append(get.email.strip())
        public.writeFile(self.__mail_list_data, json.dumps(self.__mail_list))
        return public.return_message(0, 0, public.lang("Setup successfully!"))

    # 添加自定义邮箱地址
    def user_mail_send(self, get):
        if not (hasattr(get, 'email') or hasattr(get, 'stmp_pwd') or hasattr(get, 'hosts') or hasattr(get, 'port')):
            return public.return_message(-1, 0, public.lang("Please complete the information"))
        # 自定义邮件
        self.mail.qq_stmp_insert(get.email.strip(), get.stmp_pwd.strip(), get.hosts.strip(), get.port.strip())
        # 测试发送
        if self.mail.qq_smtp_send(get.email.strip(), public.get_msg_gettext('aaPanel Alert Test Email'),
                                  public.get_msg_gettext('aaPanel Alert Test Email')):
            if not get.email.strip() in self.__mail_list:
                self.__mail_list.append(get.email.strip())
                public.writeFile(self.__mail_list_data, json.dumps(self.__mail_list))
            return public.return_message(0, 0, public.lang("Setup successfully!"))
        else:
            ret = []
            public.writeFile(self.__mail_config, json.dumps(ret))
            return public.return_message(-1, 0, public.lang("Email sending failed, please check if the STMP password is correct or the hosts are correct"))

    # 查看自定义邮箱配置
    def get_user_mail(self, get):
        qq_mail_info = json.loads(public.ReadFile(self.__mail_config))
        if len(qq_mail_info) == 0:
            return public.return_message(-1, 0, public.lang("No Data"))
        if not 'port' in qq_mail_info: qq_mail_info['port'] = 465
        return public.return_message(0, 0, qq_mail_info)

    # 清空数据
    def set_empty(self, get):
        type = get.type.strip()
        if type == 'dingding':
            ret = []
            public.writeFile(self.__dingding_config, json.dumps(ret))
            return public.return_message(0, 0, public.lang("Empty successfully"))
        else:
            ret = []
            public.writeFile(self.__mail_config, json.dumps(ret))
            return public.return_message(0, 0, public.lang("Empty successfully"))

    # 用户自定义邮件发送
    def user_stmp_mail_send(self, get):
        if not (hasattr(get, 'email')): return public.return_message(-1, 0, public.lang("Please input your email"))
        emailformat = re.compile(r'[a-zA-Z0-9.-_+%]+@[a-zA-Z0-9]+\.[a-zA-Z0-9]+')
        if not emailformat.search(get.email): return public.return_message(-1, 0, public.lang("Please enter your vaild email"))
        # 测试发送邮件
        if not get.email.strip() in self.__mail_list: return public.return_message(0, 0, public.lang("The mailbox does not exist, please add it to the mailbox list"))
        if not (hasattr(get, 'title')): return public.return_message(-1, 0, public.lang("Please fill in the email title"))
        if not (hasattr(get, 'body')): return public.return_message(-1, 0, public.lang("Please enter the email content"))
        # 先判断是否存在stmp信息
        qq_mail_info = json.loads(public.ReadFile(self.__mail_config))
        if len(qq_mail_info) == 0:
            return public.return_message(-1, 0, public.lang("STMP information was not found, please re-add custom mail STMP information in the settings"))
        if self.mail.qq_smtp_send(get.email.strip(), get.title.strip(), get.body):
            # 发送成功
            return public.return_message(0, 0, public.lang("Sent successfully"))
        else:
            return public.return_message(-1, 0, public.lang("Failed to send"))

    # 查看能使用的告警通道
    def get_settings(self, get):
        sm = send_mail.send_mail()
        return sm.get_settings()

    def get_settings2(self, get=None):
        import panel_telegram_bot
        tg = panel_telegram_bot.panel_telegram_bot()
        tg = tg.get_tg_conf()
        conf = self.get_settings(get)
        conf['telegram'] = tg
        return conf

    # 设置钉钉报警
    def set_dingding(self, get):
        if not (hasattr(get, 'url') or hasattr(get, 'atall')):
            return public.return_message(-1, 0, public.lang("Please complete the information"))
        if get.atall == 'True' or get.atall == '1':
            get.atall = 'True'
        else:
            get.atall = 'False'
        push_url = get.url.strip()
        channel = "dingding"
        if push_url.find("weixin.qq.com") != -1:
            channel = "weixin"
        msg = ""
        try:
            from panelMessage import panelMessage
            pm = panelMessage()
            if hasattr(pm, "init_msg_module"):
                msg_module = pm.init_msg_module(channel)
                if msg_module:
                    _res = msg_module.set_config(get)
                    if _res["status"]:
                        return _res
        except Exception as e:
            msg = str(e)
            print("设置钉钉配置异常: {}".format(msg))
        if not msg:
            return public.return_message(-1, 0, public.lang("Add failed, please check if the URL is correct"))
        else:
            return public.return_message(-1, 0, msg)

    # 查看钉钉
    def get_dingding(self, get):
        sm = send_mail.send_mail()
        return sm.get_dingding()

    # 使用钉钉发送消息
    def user_dingding_send(self, get):
        qq_mail_info = json.loads(public.ReadFile(self.__dingding_config))
        if len(qq_mail_info) == 0:
            return public.return_message(-1, 0, public.lang("The configuration information of the nails you configured was not found, please add in the settings"))
        if not (hasattr(get, 'content')): return public.return_message(-1, 0, public.lang("Please enter the data you need to send"))
        if self.mail.dingding_send(get.content):
            return public.return_message(0, 0, public.lang("Sent successfully"))
        else:
            return public.return_message(-1, 0, public.lang("Failed to send"))

    def getPanelState(self, get):
        return os.path.exists(self._setup_path + '/data/close.pl')

    def reload_session(self):
        userInfo = public.M('users').where("id=?", (1,)).field('username,password').find()
        token = public.Md5(userInfo['username'] + '/' + userInfo['password'])
        public.writeFile(self._setup_path + '/data/login_token.pl', token)
        skey = 'login_token'
        cache.set(skey, token)
        sess_path = 'data/sess_files'
        if not os.path.exists(sess_path):
            os.makedirs(sess_path, 384)
        self.clean_sess_files(sess_path)
        sess_key = public.get_sess_key()
        sess_file = os.path.join(sess_path, sess_key)
        public.writeFile(sess_file, str(int(time.time() + 86400)))
        public.set_mode(sess_file, '600')
        session['login_token'] = token

    def clean_sess_files(self, sess_path):
        '''
            @name 清理过期的sess_file
            @auther hwliang<2020-07-25>
            @param sess_path(string) sess_files目录
            @return void
        '''
        s_time = time.time()
        for fname in os.listdir(sess_path):
            try:
                if len(fname) != 32: continue
                sess_file = os.path.join(sess_path, fname)
                if not os.path.isfile(sess_file): continue
                sess_tmp = public.ReadFile(sess_file)
                if not sess_tmp:
                    if os.path.exists(sess_file):
                        os.remove(sess_file)
                if s_time > int(sess_tmp):
                    os.remove(sess_file)
            except:
                pass

    def get_password_safe_file(self):
        '''
            @name 获取密码复杂度配置文件
            @auther hwliang<2021-10-18>
            @return string
        '''
        return public.get_panel_path() + '/data/check_password_safe.pl'

    def check_password_safe(self, password):
        '''
            @name 密码复杂度验证
            @auther hwliang<2021-10-18>
            @param password(string) 密码
            @return bool
        '''
        # 是否检测密码复杂度
        is_check_file = self.get_password_safe_file()
        if not os.path.exists(is_check_file): return True

        # 密码长度验证
        if len(password) < 8: return False

        num = 0
        # 密码是否包含数字
        if re.search(r'[0-9]+', password): num += 1
        # 密码是否包含小写字母
        if re.search(r'[a-z]+', password): num += 1
        # 密码是否包含大写字母
        if re.search(r'[A-Z]+', password): num += 1
        # 密码是否包含特殊字符
        if re.search(r'[^\w\s]+', password): num += 1
        # 密码是否包含以上任意3种组合
        if num < 3: return False
        return True

    def set_password_safe(self, get):
        '''
            @name 设置密码复杂度
            @auther hwliang<2021-10-18>
            @param get(string) 参数
            @return dict
        '''
        is_check_file = self.get_password_safe_file()
        if os.path.exists(is_check_file):
            os.remove(is_check_file)
            public.WriteLog('TYPE_PANEL', 'Disable password complexity verification')
            return public.return_message(0, 0, public.lang("Password complexity verification is disabled"))
        else:
            public.writeFile(is_check_file, 'True')
            public.WriteLog('TYPE_PANEL', 'Enable password complexity verification')
            return public.return_message(0, 0, public.lang("Password complexity verification has been enabled"))

    def get_password_safe(self, get):
        '''
            @name 获取密码复杂度
            @auther hwliang<2021-10-18>
            @param get(string) 参数
            @return bool
        '''
        is_check_file = self.get_password_safe_file()
        return os.path.exists(is_check_file)

    def get_password_expire_file(self):
        '''
            @name 获取密码过期配置文件
            @auther hwliang<2021-10-18>
            @return string
        '''
        return public.get_panel_path() + '/data/password_expire.pl'

    def set_password_expire(self, get):
        '''
            @name 设置密码过期时间
            @auther hwliang<2021-10-18>
            @param get<dict_obj>{
                expire: int<密码过期时间> 单位:天,
            }
            @return dict
        '''
        expire = int(get.expire)
        expire_file = self.get_password_expire_file()
        if expire <= 0:
            if os.path.exists(expire_file):
                os.remove(expire_file)
            public.WriteLog('TYPE_PANEL', 'Disable password expiration authentication')
            return public.return_message(0, 0, public.lang("Password expiration authentication is disabled"))
        min_expire = 10
        max_expire = 365 * 5
        if expire < min_expire:
            return public.return_message(-1, 0, public.lang('The password expiration period cannot be less than {} days', min_expire))
        if expire > max_expire:
            return public.return_message(-1, 0, public.lang('The password expiration period cannot be longer than {} days', max_expire))

        public.writeFile(self.get_password_expire_file(), str(expire))

        if expire > 0:
            expire_time_file = public.get_panel_path() + '/data/password_expire_time.pl'
            public.writeFile(expire_time_file, str(int(time.time()) + (expire * 86400)))

        public.WriteLog('TYPE_PANEL', 'Set the password expiration time to [{}] days'.format(expire))
        return public.return_message(0, 0, public.lang("The password expiration time is set to [{}] days", expire))

    def setlastPassword(self, get):
        public.add_security_logs("Change Password", "Successfully used last password!")
        self.reload_session()
        # 密码过期时间
        expire_time_file = public.get_panel_path() + '/data/password_expire_time.pl'
        if os.path.exists(expire_time_file): os.remove(expire_time_file)
        self.get_password_config(None)
        if session.get('password_expire', False):
            session['password_expire'] = False
        return public.return_message(0, 0, public.lang("Password changed!"))

    def get_password_config(self, get=None):
        '''
            @name 获取密码配置
            @auther hwliang<2021-10-18>
            @param get<dict_obj> 参数
            @return dict{expire:int,expire_time:int,password_safe:bool}
        '''
        expire_file = self.get_password_expire_file()
        expire = 0
        expire_time = 0
        if os.path.exists(expire_file):
            expire = public.readFile(expire_file)
            try:
                expire = int(expire)
            except:
                expire = 0

            # 检查密码过期时间文件是否存在
            expire_time_file = public.get_panel_path() + '/data/password_expire_time.pl'
            if not os.path.exists(expire_time_file) and expire > 0:
                public.writeFile(expire_time_file, str(int(time.time()) + (expire * 86400)))

            expire_time = public.readFile(expire_time_file)
            if expire_time:
                expire_time = int(expire_time)
            else:
                expire_time = 0

        data = {}
        data['expire'] = expire
        data['expire_time'] = expire_time
        data['password_safe'] = self.get_password_safe(get)
        data['ps'] = 'Password expiration configuration is not enabled. For your panel security, please consider enabling it!'
        if data['expire_time']:
            cur_time = int(time.time())
            data['expire_day'] = int((expire_time - cur_time) / 86400)
            # public.print_log(f"{expire_time}-{cur_time}   = {data['expire_day'] }天")
            if data['expire_day'] < 10:
                if data['expire_day'] <= 0:
                    data['ps'] = 'Your password has expired. In case you fail to log in next time, please change your password immediately.'
                else:
                    data['ps'] = "Your panel password will expire in <span style='color:red;'>{}</span> days, in order not to affect your normal login, please change the password as soon as possible!".format(
                        data['expire_day'])
            else:
                data['ps'] = "Your panel password has  <span style='color:green;'>{}</span> days left to expire!".format(
                    data['expire_day'])
        return public.return_message(0, 0,  data)

    def setPassword(self, get):
        if not public.M('users').where("username=?", (session['username'],)).find():
            return public.return_message(-1, 0, public.lang("Setup fail! Please try logging in again."))
        get.password1 = public.url_decode(public.rsa_decrypt(get.password1))
        get.password2 = public.url_decode(public.rsa_decrypt(get.password2))
        get.userpassword = public.url_decode(public.rsa_decrypt(get.get('userpassword','').strip()))

        if get.password1 != get.password2:
            return public.return_message(-1, 0, public.lang("The passwords entered twice are inconsistent, please try again!"))
        if len(get.password1) < 5:
            return public.return_message(-1, 0, public.lang("Password cannot be less than 5 characters!"))
        if not self.check_password_safe(get.password1):
            return public.return_message(-1, 0, public.lang("The password must be at least eight characters in length and contain at least three combinations of digits, uppercase letters, lowercase letters, and special characters"))

        # 密码校验
        userpassword1 = public.password_salt(public.md5(get.userpassword), username=session['username'])
        userpassword2 = public.M('users').where("username=?", (session['username'],)).getField('password')
        if userpassword1 != userpassword2:
            return public.return_message(-1, 0, public.lang("Password verification failed!"))

        if get.password1:
            public.M('users').where("username=?", (session['username'],)).setField(
                'password',
                public.password_salt(public.md5(get.password1.strip()), username=session['username'])
            )
        public.write_log_gettext('Panel configuration', 'Successfully modified password for user [{0}]!',
                                 (session['username'],))

        self.reload_session()

        # 密码过期时间
        expire_time_file = public.get_panel_path() + '/data/password_expire_time.pl'
        if os.path.exists(expire_time_file):
            os.remove(expire_time_file)
        self.get_password_config(None)
        if session.get('password_expire', False):
            session['password_expire'] = False
        return public.return_message(0, 0, public.lang("Setup successfully!"))

    def setUsername(self, get):
        get.username1 = public.url_decode(public.rsa_decrypt(get.username1))
        get.username2 = public.url_decode(public.rsa_decrypt(get.username2))
        if get.username1 != get.username2: return public.return_message(-1, 0, public.lang("The usernames entered twice are inconsistent, plesea try again!"))

        # 密码校验
        password = public.url_decode(public.rsa_decrypt(get.get('userpassword').strip()))

        password1 = public.password_salt(public.md5(password), username=session['username'])
        password2 = public.M('users').where("username=?", (session['username'],)).getField('password')
        if password1 != password2:
            return public.return_message(-1, 0, public.lang("Password verification failed!"))

        if len(get.username1) < 3: return public.return_message(-1, 0, public.lang("Username cannot be less than 3 characters"))
        public.M('users').where("username=?", (session['username'],)).setField('username', get.username1.strip())
        public.write_log_gettext('Panel configuration', 'Username is modified from [{}] to [{}]',
                                 (session['username'], get.username2))
        session['username'] = get.username1
        self.reload_session()
        return public.return_message(0, 0, public.lang("Setup successfully!"))

    # 取用户列表
    def get_users(self, args):
        data = public.M('users').field('id,username').select()
        return data

    # 创建新用户
    def create_user(self, args):
        args.username = public.url_decode(args.username)
        args.password = public.url_decode(args.password)
        if session['uid'] != 1: return public.return_message(-1, 0, public.lang("Permission denied!"))
        if len(args.username) < 2: return public.return_message(-1, 0, public.lang("User name must be at least 2 characters"))
        if len(args.password) < 8: return public.return_message(-1, 0, public.lang("Password must be at least 8 characters"))
        pdata = {
            "username": args.username.strip(),
            "password": public.password_salt(public.md5(args.password.strip()), username=args.username.strip())
        }

        if (public.M('users').where('username=?', (pdata['username'],)).count()):
            return public.return_message(-1, 0, public.lang("The specified username already exists!"))

        if (public.M('users').insert(pdata)):
            public.write_log_gettext('User Management', 'Create new user {}', (pdata['username'],))
            return public.return_message(0, 0, 'Create new user {} success!', (pdata['username'],))
        return public.return_message(-1, 0, public.lang("Create new user failed!"))

    # 删除用户
    def remove_user(self, args):
        if session['uid'] != 1: return public.return_message(-1, 0, public.lang("Permission denied!"))
        if int(args.id) == 1: return public.return_message(-1, 0, public.lang("Cannot delete initial default user!"))
        username = public.M('users').where('id=?', (args.id,)).getField('username')
        if not username: return public.return_message(-1, 0, public.lang("The specified username not exists!"))
        if (public.M('users').where('id=?', (args.id,)).delete()):
            public.write_log_gettext('User Management', 'Delete users [{}]', (username))
            return public.return_message(0, 0, 'Delete user {} success!', (username,))
        return public.return_message(-1, 0, public.lang("User deletion failed!"))

    # 修改用户
    def modify_user(self, args):
        if session['uid'] != 1: return public.return_message(-1, 0, public.lang("Permission denied!"))
        username = public.M('users').where('id=?', (args.id,)).getField('username')
        pdata = {}
        if 'username' in args:
            args.username = public.url_decode(args.username)
            if len(args.username) < 2: return public.return_message(-1, 0, public.lang("User name must be at least 2 characters"))
            pdata['username'] = args.username.strip()

        if 'password' in args:
            if args.password:
                args.password = public.url_decode(args.password)
                if len(args.password) < 8: return public.return_message(-1, 0, public.lang("Password must be at least 8 characters"))
                pdata['password'] = public.password_salt(public.md5(args.password.strip()), username=username)

        if (public.M('users').where('id=?', (args.id,)).update(pdata)):
            public.write_log_gettext('User Management', "Edit user {}", (username,))
            return public.return_message(0, 0, public.lang("Setup successfully!"))
        return public.return_message(-1, 0, public.lang("No changes submitted"))

    #一键清空面板备份
    def clearBackup(self, get):
        backup_path = '{}/panel'.format(public.get_backup_path())
        if not os.path.exists(backup_path): return public.return_message(-1, 0, 'The backup path is empty and cannot be cleared!')
        for f in  os.listdir(backup_path):
            if f.endswith(".zip"):
                b_file = backup_path + '/' + f
                if os.path.exists(b_file):
                    os.remove(b_file)
        public.WriteLog('TYPE_PANEL', 'Clear the panel backup data')
        return public.return_message(0, 0, 'Clear the panel backup successfully!')

    def setPanel(self, get):
        try:
            if not public.IsRestart(): return public.return_message(-1, 0, public.lang("Please run the program when all install tasks finished!"))
            backup_number = 0
            if 'backup_number' in get:
                try:
                    backup_number = int(get.backup_number)
                except:
                    return public.return_message(-1, 0, public.lang("backup_number must be an integer!"))
                if backup_number ==0:
                    return public.return_message(-1, 0, public.lang("backup_number must be greater than 0!"))
                public.writeFile('data/panel_backup_number.pl', str(backup_number))
                time_now = time.time() - (86400 * backup_number)
                b_path = '{}/panel'.format(public.get_backup_path())
                if os.path.isdir(b_path):
                    public.clear_panel_backup(b_path,backup_number)
                    public.WriteLog('TYPE_PANEL', 'Set the panel backup retention quantity to {} copies'.format(backup_number))

            if "auto_backup" in get:
                not_auto_path = 'data/not_auto_backup.pl'
                if get.auto_backup == '0':
                    public.writeFile(not_auto_path, 'True')
                    if not os.path.exists(not_auto_path):
                        return public.return_message(-1, 0, public.lang("Failed to turn off automatic backup of panel data!"))
                    public.WriteLog('TYPE_PANEL', 'Turn off automatic backup of panel data')
                else:
                    try:
                        os.remove(not_auto_path)
                    except:
                        pass
                    if os.path.exists(not_auto_path):
                        return public.return_message(-1, 0, public.lang("Failed to turn on automatic backup of panel data!"))
                    public.WriteLog('TYPE_PANEL', 'Turn on automatic backup of panel data')

            if 'limitip' in get:
                if get.limitip.find('/') != -1:
                    return public.return_message(-1, 0, public.lang("The authorized IP format is incorrect, and the subnet segment writing is not supported"))
            isReWeb = False
            sess_out_path = 'data/session_timeout.pl'
            if 'session_timeout' in get:
                try:
                    session_timeout = int(get.session_timeout)
                except:
                    return public.return_message(-1, 0, public.lang("Timeout must be an integer!"))
                s_time_tmp = public.readFile(sess_out_path)
                if not s_time_tmp: s_time_tmp = '0'
                if int(s_time_tmp) != session_timeout:
                    if session_timeout < 300 or session_timeout > 86400*30 : return public.return_message(-1, 0, public.lang("The timeout time needs to be between 300s-30days"))
                    public.writeFile(sess_out_path, str(session_timeout))
                    isReWeb = True
            # else:
            #     return public.return_message(-1, 0, public.lang("Timeout must be an integer!"))

            workers_p = 'data/workers.pl'
            if 'workers' in get:
                workers = int(get.workers)
                if int(public.readFile(workers_p)) != workers:
                    if workers < 1 or workers > 1024: return public.return_message(-1, 0,public.lang("The number of panel threads should be between 1-1024"))
                    public.writeFile(workers_p, str(workers))
                    isReWeb = True

            if get.domain:
                if re.match(r"^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$", get.domain): return public.return_message(-1, 0, public.lang("Domain cannot bind ip address"))
                reg = r"^([\w\-\*]{1,100}\.){1,4}(\w{1,10}|\w{1,10}\.\w{1,10})$"
                if not re.match(reg, get.domain): return public.return_message(-1, 0, public.lang("Format of primary domain is incorrect"))
            if get.address:
                from public.regexplib import match_ipv4, match_ipv6
                if not match_ipv4.match(get.address) and not match_ipv6.match(get.address):
                    return public.return_message(-1, 0, public.lang("Please set the correct Server IP"))
            oldPort = public.GetHost(True)
            if not 'port' in get:
                get.port = oldPort
            newPort = get.port
            if int(oldPort) != int(get.port):
                get.port = str(int(get.port))
                if self.IsOpen(get.port):
                    return public.return_message(-1, 0, public.lang('Port [{}] is in use!', get.port))
                if int(get.port) >= 65535 or int(get.port) < 100: return public.return_message(-1, 0, public.lang("Port range is incorrect! should be between 100-65535"))
                public.writeFile('data/port.pl', get.port)
                import firewalls
                get.ps = public.get_msg_gettext('New panel port')
                fw = firewalls.firewalls()
                fw.AddAcceptPort(get)
                get.port = oldPort
                get.id = public.M('firewall').where("port=?", (oldPort,)).getField('id')
                fw.DelAcceptPort(get)
                isReWeb = True
            # public.print_log("session  title 111---{} ".format(session.get('title', None)))
            if not session.get('title', None) or get.webname != session.get('title', None):
                session['title'] = public.xssencode2(get.webname)
                public.SetConfigValue('title', public.xssencode2(get.webname))

            limitip = public.readFile('data/limitip.conf')
            if get.limitip != limitip:
                public.writeFile('data/limitip.conf', get.limitip)
                cache.set('limit_ip', [])

            public.writeFile('data/domain.conf', public.xssencode2(get.domain).strip())
            public.writeFile('data/iplist.txt', get.address)

            import files
            fs = files.files()
            if not fs.CheckDir(get.backup_path): return public.return_message(-1, 0, public.lang("Cannot use system critical directory as default backup directory"))
            if not fs.CheckDir(get.sites_path): return public.return_message(-1, 0, public.lang("Cannot use system critical directory as default site directory"))
            public.M('config').where("id=?", ('1',)).save('backup_path,sites_path', (get.backup_path, get.sites_path))
            session['config']['backup_path'] = os.path.join('/', get.backup_path)
            session['config']['sites_path'] = os.path.join('/', get.sites_path)
            db_backup = get.backup_path + '/database'
            if not os.path.exists(db_backup):
                try:
                    os.makedirs(db_backup, 384)
                except:
                    public.ExecShell('mkdir -p ' + db_backup)
            site_backup = get.backup_path + '/site'
            if not os.path.exists(site_backup):
                try:
                    os.makedirs(site_backup, 384)
                except:
                    public.ExecShell('mkdir -p ' + site_backup)

            mhost = public.GetHost()
            if get.domain.strip(): mhost = get.domain
            data = {'uri': request.path, 'host': mhost + ':' + newPort, 'status': True, 'isReWeb': isReWeb,
                    'msg': public.get_msg_gettext('Saved')}
            public.write_log_gettext('Panel configuration',
                                     'Set panel port [{}], domain [{}], default backup directory [{}], default site directory [{}], server IP [{}], authorized IP [{}]!',
                                     (newPort, get.domain, get.backup_path, get.sites_path, get.address, get.limitip))
            if isReWeb: public.restart_panel()
            return public.return_message(0, 0,  public.lang("Configuration saved"))
        except Exception as ex:
            public.print_log(public.get_error_info())
            return public.return_message(-1, 0, public.lang("An exception occurred during execution {}", str(ex)))


            # 新方法 9.3 2024.9.26
    def setPanel_bt_new(self, get):
        if not public.IsRestart(): return public.return_message(-1, 0, public.lang("Please run the program when all install tasks finished!"))
        limitip_path = "{}/data/limitip.conf".format(self._setup_path)
        if not get.get('limitip') and os.path.exists(limitip_path):
            os.truncate(limitip_path, 0)

        if 'limitip' in get:
            if get.limitip.find('/') != -1:
                return public.return_message(-1, 0, public.lang(
                    "The authorized IP format is incorrect, and the subnet segment writing is not supported"))
        isReWeb = False
        sess_out_path = 'data/session_timeout.pl'
        if 'session_timeout' in get:
            try:
                session_timeout = int(get.session_timeout)
                s_time_tmp = public.readFile(sess_out_path)
                if not s_time_tmp: s_time_tmp = '0'
                if int(s_time_tmp) != session_timeout:
                    if session_timeout < 300:
                        return public.return_message(-1, 0, public.lang('The timeout period cannot be less than 300 seconds'))
                    if session_timeout > 86400 * 30:
                        return public.return_message(-1, 0, public.lang('The timeout period cannot be greater than 30 days'))
                    public.writeFile(sess_out_path, str(session_timeout))
                    isReWeb = True
            except:
                pass

        workers_p = 'data/workers.pl'
        if 'workers' in get:
            workers = int(get.workers)
            if int(public.readFile(workers_p)) != workers:
                if workers < 1 or workers > 1024:
                    return public.return_message(-1, 0,public.lang("The number of panel threads should be between 1-1024"))
                public.writeFile(workers_p, str(workers))
                isReWeb = True

        if "domain" in get and get.domain != "":
            if re.match(r"^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$", get.domain):
                return public.return_message(-1, 0, public.lang("Domain cannot bind ip address"))
            reg = r"^([\w\-\*]{1,100}\.){1,4}(\w{1,10}|\w{1,10}\.\w{1,10})$"
            if not re.match(reg, get.domain):
                return public.return_message(-1, 0, public.lang("Format of primary domain is incorrect"))
            public.writeFile('data/domain.conf', get.domain.strip())
            public.WriteLog('TYPE_PANEL', 'PANEL_SET_SUCCESS', (get.domain,))

        if get.get("domain") == "":
            if os.path.exists('data/domain.conf'): os.remove('data/domain.conf')

        if "address" in get and get.address != "":
            if not public.check_ip(get.address):
                return public.return_message(-1, 0, public.lang("Please set the correct Server IP"))
            public.writeFile('data/iplist.txt', get.address)
            public.WriteLog('TYPE_PANEL', 'PANEL_SET_SUCCESS', (get.address,))

        oldPort = public.GetHost(True)
        if not 'port' in get:
            get.port = oldPort
        newPort = get.port
        if oldPort != get.port:
            get.port = str(int(get.port))
            if self.IsOpen(get.port):
                return public.return_message(-1, 0, 'Port [{}] is in use!', (get.port,))
            if int(get.port) >= 65535 or int(get.port) < 100:
                return public.return_message(-1, 0, public.lang("Port range is incorrect! should be between 100-65535"))
            public.writeFile('data/port.pl', get.port)
            import firewalls
            get.ps = public.getMsg('PORT_CHECK_PS')
            fw = firewalls.firewalls()
            fw.AddAcceptPort(get)
            get.port = oldPort
            get.id = public.M('firewall').where("port=?", (oldPort,)).getField('id')
            fw.DelAcceptPort(get)
            isReWeb = True
            public.WriteLog('TYPE_PANEL', 'PANEL_SET_SUCCESS', (newPort,))

        if "webname" in get and get.webname != session['title']:
            if get.webname.strip() == '': get.webname = 'aaPanel Linux'
            session['title'] = public.xssencode2(get.webname)
            public.SetConfigValue('title', public.xssencode2(get.webname))
            public.WriteLog('TYPE_PANEL', 'PANEL_SET_SUCCESS', ('TITLE', get.webname))

        limitip = public.readFile('data/limitip.conf')
        if "limitip" in get and get.limitip != limitip:
            public.writeFile('data/limitip.conf', get.limitip)
            cache.set('limit_ip', [])
            public.WriteLog('TYPE_PANEL', 'PANEL_SET_SUCCESS', ('LIMIT_IP',))

        import files
        fs = files.files()
        if "backup_path" in get and get.backup_path != "":
            if not fs.CheckDir(get.backup_path):
                return public.return_message(-1, 0, public.lang('You cannot use the system critical directory as the default backup directory'))
            session['config']['backup_path'] = os.path.join('/', get.backup_path)
            db_backup = get.backup_path + '/database'
            site_backup = get.backup_path + '/site'

            if not os.path.exists(db_backup):
                try:
                    os.makedirs(db_backup, 384)
                except:
                    public.ExecShell('mkdir -p ' + db_backup)

            if not os.path.exists(site_backup):
                try:
                    os.makedirs(site_backup, 384)
                except:
                    public.ExecShell('mkdir -p ' + site_backup)

            public.M('config').where("id=?", ('1',)).save('backup_path', (get.backup_path,))
            isReWeb = True
            public.WriteLog('TYPE_PANEL', 'PANEL_SET_SUCCESS', (get.backup_path,))

        if "sites_path" in get and get.sites_path != "":
            if not fs.CheckDir(get.sites_path):
                return public.return_message(-1, 0, public.lang('You cannot use the key directory as the default directory for website building'))

            session['config']['sites_path'] = os.path.join('/', get.sites_path)
            public.M('config').where("id=?", ('1',)).save('sites_path', (get.sites_path,))
            public.WriteLog('TYPE_PANEL', 'PANEL_SET_SUCCESS', (get.sites_path,))

        mhost = public.GetHost()
        if "domain" in get and get.domain.strip(): mhost = get.domain
        data = {'uri': request.path, 'host': mhost + ':' + newPort, 'status': True, 'isReWeb': isReWeb,
                'msg': public.getMsg('PANEL_SAVE')}

        if isReWeb: public.restart_panel()
        return public.return_message(0, 0,  public.lang("Configuration saved"))

    def set_admin_path(self, get):
        get.admin_path = public.rsa_decrypt(get.admin_path.strip()).strip()
        if len(get.admin_path) < 6: return public.return_message(-1, 0, public.lang("Security Entrance cannot be less than 6 characters!"))
        if get.admin_path in admin_path_checks: return public.return_message(-1, 0, public.lang("This entrance has been used by the panel, please set another entrances!"))
        if not public.path_safe_check(get.admin_path) or get.admin_path[-1] == '.': return public.return_message(-1, 0, public.lang("Entrance address format is incorrect, e.g. /my_panel"))
        if get.admin_path[0] != '/': return public.return_message(-1, 0, public.lang("Entrance address format is incorrect, e.g. /my_panel"))
        if get.admin_path.find("//") != -1:
            return public.return_message(-1, 0, public.lang("Entrance address format is incorrect, e.g. /my_panel"))
        admin_path_file = 'data/admin_path.pl'
        admin_path = '/'
        if os.path.exists(admin_path_file): admin_path = public.readFile(admin_path_file).strip()
        if get.admin_path != admin_path:
            public.writeFile(admin_path_file, get.admin_path)
            public.restart_panel()
        return public.return_message(0, 0, public.lang("Setup successfully!"))

    def setPathInfo(self, get):
        # 设置PATH_INFO
        version = get.version
        type = get.type
        if public.get_webserver() == 'nginx':
            path = public.GetConfigValue('setup_path') + '/nginx/conf/enable-php-' + version + '.conf'
            conf = public.readFile(path)
            rep = r"\s+#*include\s+pathinfo.conf;"
            if type == 'on':
                conf = re.sub(rep, '\n\t\t\tinclude pathinfo.conf;', conf)
            else:
                conf = re.sub(rep, '\n\t\t\t#include pathinfo.conf;', conf)
            public.writeFile(path, conf)
            public.serviceReload()

        path = public.GetConfigValue('setup_path') + '/php/' + version + '/etc/php.ini'
        conf = public.readFile(path)
        rep = r"\n*\s*cgi\.fix_pathinfo\s*=\s*([0-9]+)\s*\n"
        status = '0'
        if type == 'on': status = '1'
        conf = re.sub(rep, "\ncgi.fix_pathinfo = " + status + "\n", conf)
        public.writeFile(path, conf)
        public.write_log_gettext("PHP configuration", "Set PATH_INFO module to [{}] for PHP-{}!", (version, type))
        public.phpReload(version)
        return public.return_message(0, 0, public.lang("Setup successfully!"))

    # 设置文件上传大小限制
    def setPHPMaxSize(self, get):
        version = get.version
        max = get.max
        if int(max) < 2: return public.return_message(-1, 0, public.lang("Limit of upload size cannot be less than 2 MB"))
        # 设置PHP
        path = public.GetConfigValue('setup_path') + '/php/' + version + '/etc/php.ini'
        ols_php_path = '/usr/local/lsws/lsphp{}/etc/php/{}.{}/litespeed/php.ini'.format(get.version, get.version[0],
                                                                                        get.version[1])
        if os.path.exists('/etc/redhat-release'):
            ols_php_path = '/usr/local/lsws/lsphp' + get.version + '/etc/php.ini'
        for p in [path, ols_php_path]:
            if not p:
                continue
            if not os.path.exists(p):
                continue
            conf = public.readFile(p)
            rep = r"\nupload_max_filesize\s*=\s*[0-9]+M?m?"
            conf = re.sub(rep, r'\nupload_max_filesize = ' + max + 'M', conf)
            rep = r"\npost_max_size\s*=\s*[0-9]+M?m?"
            conf = re.sub(rep, r'\npost_max_size = ' + max + 'M', conf)
            public.writeFile(p, conf)

        if public.get_webserver() == 'nginx':
            # 设置Nginx
            path = public.GetConfigValue('setup_path') + '/nginx/conf/nginx.conf'
            conf = public.readFile(path)
            rep = r"client_max_body_size\s+([0-9]+)m?M?"
            tmp = re.search(rep, conf).groups()
            if int(tmp[0]) < int(max):
                conf = re.sub(rep, 'client_max_body_size ' + max + 'm', conf)
                public.writeFile(path, conf)

        public.serviceReload()
        public.phpReload(version)
        public.write_log_gettext("PHP configuration", "Set max upload size to [{} MB] for PHP-{}!", (version, max))
        return public.return_message(0, 0, public.lang("Setup successfully!"))

    # 设置禁用函数
    def setPHPDisable(self, get):
        filename = public.GetConfigValue('setup_path') + '/php/' + get.version + '/etc/php.ini'
        ols_php_path = '/usr/local/lsws/lsphp{}/etc/php/{}.{}/litespeed/php.ini'.format(get.version, get.version[0],
                                                                                        get.version[1])
        if os.path.exists('/etc/redhat-release'):
            ols_php_path = '/usr/local/lsws/lsphp' + get.version + '/etc/php.ini'
        if not os.path.exists(filename): return public.return_message(-1, 0, public.lang("Requested PHP version does NOT exist!"))
        for file in [filename, ols_php_path]:
            if not os.path.exists(file):
                continue
            phpini = public.readFile(file)
            rep = r"disable_functions\s*=\s*.*\n"
            phpini = re.sub(rep, 'disable_functions = ' + get.disable_functions + "\n", phpini)
            public.write_log_gettext('PHP configuration', 'Modified disabled function to [{}] for PHP-{}',
                                     (get.version, get.disable_functions))
            public.writeFile(file, phpini)
            public.phpReload(get.version)
        public.serviceReload()
        return public.return_message(0, 0, public.lang("Setup successfully!"))

    # 设置PHP超时时间
    def setPHPMaxTime(self, get):
        time = get.time
        version = get.version
        if int(time) < 30 or int(time) > 86400: return public.return_message(-1, 0, public.lang("Please fill in the value between 30 and 86400!"))
        file = public.GetConfigValue('setup_path') + '/php/' + version + '/etc/php-fpm.conf'
        if not os.path.exists(file):
            return public.return_message(-1, 0, public.lang("The PHP-FPM configuration file does not exist. {}", file))
        conf = public.readFile(file)
        rep = r"request_terminate_timeout\s*=\s*([0-9]+)\n"
        conf = re.sub(rep, "request_terminate_timeout = " + time + "\n", conf)
        public.writeFile(file, conf)

        file = '/www/server/php/' + version + '/etc/php.ini'
        phpini = public.readFile(file)
        rep = r"max_execution_time\s*=\s*([0-9]+)\r?\n"
        phpini = re.sub(rep, "max_execution_time = " + time + "\n", phpini)
        rep = r"max_input_time\s*=\s*([0-9]+)\r?\n"
        phpini = re.sub(rep, "max_input_time = " + time + "\n", phpini)
        public.writeFile(file, phpini)

        if public.get_webserver() == 'nginx':
            # 设置Nginx
            path = public.GetConfigValue('setup_path') + '/nginx/conf/nginx.conf'
            if not os.path.exists(path):
                return public.return_message(-1, 0, public.lang("Nginx configuration file {} does not exist!",path))
            conf = public.readFile(path)
            if not conf:
                return public.return_message(-1, 0, public.lang("Failed to read Nginx configuration file {}",path))
            rep = r"fastcgi_connect_timeout\s+([0-9]+);"

            search_result = re.search(rep, conf)
            if search_result:
                tmp = search_result.groups()
                if int(tmp[0]) < int(time):
                    conf = re.sub(rep, 'fastcgi_connect_timeout ' + time + ';', conf)
                    rep = r"fastcgi_send_timeout\s+([0-9]+);"
                    conf = re.sub(rep, 'fastcgi_send_timeout ' + time + ';', conf)
                    rep = r"fastcgi_read_timeout\s+([0-9]+);"
                    conf = re.sub(rep, 'fastcgi_read_timeout ' + time + ';', conf)
                    public.writeFile(path, conf)
            else:
                return public.return_message(-1, 0, public.lang("Nginx configuration file {} is missing FastCGI timeout settings, please check!",path))

        public.write_log_gettext("PHP configuration", "Set maximum time of script to [{} second] for PHP-{}!",
                                 (version, time))
        public.serviceReload()
        public.phpReload(version)
        return public.return_message(0, 0, public.lang("Setup successfully!"))

    # 取FPM设置
    def getFpmConfig(self, get):
        version = get.version
        file = public.GetConfigValue('setup_path') + "/php/" + version + "/etc/php-fpm.conf"
        if not os.path.exists(file):
            return public.fail_v2("The PHP-FPM configuration file does not exist.")
        conf = public.readFile(file)
        if not conf:
            return public.fail_v2("Failed to read the PHP-FPM configuration file.")
        data = {}
        rep = r"\s*pm.max_children\s*=\s*([0-9]+)\s*"
        tmp = re.search(rep, conf)
        data['max_children'] = tmp.groups()[0] if tmp else ''

        rep = r"\s*pm.start_servers\s*=\s*([0-9]+)\s*"
        tmp = re.search(rep, conf)
        data['start_servers'] = tmp.groups()[0] if tmp else ''

        rep = r"\s*pm.min_spare_servers\s*=\s*([0-9]+)\s*"
        tmp = re.search(rep, conf)
        data['min_spare_servers'] = tmp.groups()[0] if tmp else ''

        rep = r"\s*pm.max_spare_servers \s*=\s*([0-9]+)\s*"
        tmp = re.search(rep, conf)
        data['max_spare_servers'] = tmp.groups()[0] if tmp else ''

        rep = r"\s*pm\s*=\s*(\w+)\s*"
        tmp = re.search(rep, conf)
        data['pm'] = tmp.groups()[0] if tmp else 'static'

        rep = r"\s*listen.allowed_clients\s*=\s*([\w\.,/]+)\s*"
        tmp = re.search(rep, conf)
        data['allowed'] = tmp.groups()[0] if tmp else ''

        data['unix'] = 'unix'
        data['port'] = ''
        data['bind'] = '/tmp/php-cgi-{}.sock'.format(version)

        fpm_address = public.get_fpm_address(version, True)
        if not isinstance(fpm_address, str):
            data['unix'] = 'tcp'
            data['port'] = fpm_address[1]
            data['bind'] = fpm_address[0]

        return data

    # 设置
    def setFpmConfig(self, get):
        version = get.version
        max_children = get.max_children
        start_servers = get.start_servers
        min_spare_servers = get.min_spare_servers
        max_spare_servers = get.max_spare_servers
        pm = get.pm
        if not pm in ['static', 'dynamic', 'ondemand']:
            return public.return_message(-1, 0, public.lang("Wrong operating mode"))
        file = public.GetConfigValue('setup_path') + "/php/" + version + "/etc/php-fpm.conf"
        conf = public.readFile(file)

        rep = r"\s*pm.max_children\s*=\s*([0-9]+)\s*"
        conf = re.sub(rep, "\npm.max_children = " + max_children, conf)

        rep = r"\s*pm.start_servers\s*=\s*([0-9]+)\s*"
        conf = re.sub(rep, "\npm.start_servers = " + start_servers, conf)

        rep = r"\s*pm.min_spare_servers\s*=\s*([0-9]+)\s*"
        conf = re.sub(rep, "\npm.min_spare_servers = " + min_spare_servers, conf)

        rep = r"\s*pm.max_spare_servers \s*=\s*([0-9]+)\s*"
        conf = re.sub(rep, "\npm.max_spare_servers = " + max_spare_servers + "\n", conf)

        rep = r"\s*pm\s*=\s*(\w+)\s*"
        conf = re.sub(rep, "\npm = " + pm + "\n", conf)
        if pm == 'ondemand':
            if conf.find('listen.backlog = -1') != -1:
                rep = r"\s*listen\.backlog\s*=\s*([0-9-]+)\s*"
                conf = re.sub(rep, "\nlisten.backlog = 8192\n", conf)

        if get.listen == 'unix':
            listen = '/tmp/php-cgi-{}.sock'.format(version)
        else:
            default_listen = '127.0.0.1:10{}1'.format(version)
            if 'bind_port' in get:
                if get.bind_port.find('sock') != -1:
                    listen = default_listen
                else:
                    listen = get.bind_port
            else:
                listen = default_listen

        rep = r'\s*listen\s*=\s*.+\s*'
        conf = re.sub(rep, "\nlisten = " + listen + "\n", conf)

        if 'allowed' in get:
            if not get.allowed: get.allowed = '127.0.0.1'
            rep = r"\s*listen.allowed_clients\s*=\s*([\w\.,/]+)\s*"
            conf = re.sub(rep, "\nlisten.allowed_clients = " + get.allowed + "\n", conf)

        public.writeFile(file, conf)
        public.phpReload(version)
        public.sync_php_address(version)
        public.write_log_gettext("PHP configuration",
                                 'Set concurrency of PHP-{}, max_children={}, start_servers={}, min_spare_servers={}, max_spare_servers={}',
                                 (version, max_children, start_servers, min_spare_servers, max_spare_servers))
        return public.return_message(0, 0, public.lang("Setup successfully!"))

    # 同步时间
    def syncDate(self, get):
        """
        @name 同步时间
        @author hezhihong
        """
        # 取国际标准0时时间戳
        time_str = public.HttpGet('https://wafapi2.aapanel.com'+ '/api/index/get_time')

        try:
            new_time = int(time_str) - 28800
        except:
            public.print_log(public.get_error_info())
            return public.return_message(-1, 0, public.lang("Failed to connect to the time server!"))
        if not new_time: public.returnMsg(False, 'Failed to connect to the time server!')
        # 取所在时区偏差秒数
        add_time = '+0000'
        try:
            add_time = public.ExecShell('date +"%Y-%m-%d %H:%M:%S %Z %z"')[0].replace('\n', '').strip().split()[-1]
            print(add_time)
        except:
            pass
        add_1 = False
        if add_time[0] == '+':
            add_1 = True
        add_v = int(add_time[1:-2]) * 3600 + int(add_time[-2:]) * 60
        if add_1:
            new_time += add_v
        else:
            new_time -= add_v
        # 设置所在时区时间
        date_str = public.format_date(times=new_time)
        public.ExecShell('date -s "%s"' % date_str)
        public.write_log_gettext("Panel configuration", 'Update Succeeded!')
        return public.return_message(0, 0, public.lang("Setup successfully!"))

    def IsOpen(self, port):
        # 检查端口是否占用
        import socket
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            s.connect(('127.0.0.1', int(port)))
            s.shutdown(2)
            return True
        except:
            return False

    # 设置是否开启监控
    def SetControl(self, get):
        try:
            if hasattr(get, 'day'):
                get.day = int(get.day)
                get.day = str(get.day)
                if (get.day < 1): return public.return_message(-1, 0, public.lang("Number of saving days is illegal!"))
        except:
            pass

        filename = 'data/control.conf'
        # 保存天数
        if get.type == '1':
            public.writeFile(filename, get.day)
            public.write_log_gettext("Panel configuration", 'Turned on monitory service, save for [{}] day!',
                                     (get.day,))
        elif get.type == '0':
            if os.path.exists(filename): os.remove(filename)
            public.write_log_gettext("Panel configuration", 'Monitor service turned off!')
        elif get.type == 'del':
            if not public.IsRestart(): return public.return_message(-1, 0, public.lang("Please run the program when all install tasks finished!"))
            os.remove("data/system.db")
            # public.ExecShell("/www/server/panel/BT-Task")
            # public.ExecShell("touch /www/server/panel/data/system.db")
            # public.ExecShell("chmod 777 /www/server/panel/data/system.db")
            # public.ExecShell("chmod 777 /www/server/panel/data/system.sql")
            panel_path = public.get_panel_path()
            data_path = "{}/data/sql_index.pl".format(panel_path)
            public.ExecShell("rm -f {}".format(data_path))
            import db
            sql = db.Sql()
            sql.dbfile('system').create('system')
            public.write_log_gettext("Panel configuration", 'Monitor service turned off!')
            self.check_tables()
            return public.return_message(0, 0, public.lang("Setup successfully!"))

        else:
            data = {}
            if os.path.exists(filename):
                try:
                    data['day'] = int(public.readFile(filename))
                except:
                    data['day'] = 30
                data['status'] = True
            else:
                data['day'] = 30
                data['status'] = False

            # 增加数据库大小计算机
            data['size'] = 0
            db_file = '{}/data/system.db'.format(public.get_panel_path())
            if os.path.exists(db_file):
                data['size'] = os.path.getsize(db_file)
            # 检查数据中的表是否存在
            self.check_tables()
            return public.return_message(0, 0,  data)

        return public.return_message(0, 0, public.lang("Successfully set"))

    def check_tables(self):
        import db
        db_obj = db.Sql()
        db_obj.dbfile('/www/server/panel/data/system.db')
        table_list = db_obj.query('SELECT name FROM sqlite_master WHERE type="table"')
        fail_list = [i[0] for i in table_list if len(i) > 0]
        def_table = ['cpuio', 'load_average', 'diskio', 'network', 'process_top_list']
        def_table_sql = {
            'cpuio': """CREATE TABLE `cpuio` (
  `id` INTEGER PRIMARY KEY AUTOINCREMENT,
  `pro` INTEGER,
  `mem` INTEGER,
  `addtime` INTEGER
);
""",
            'load_average': """CREATE TABLE `load_average` (
`id` INTEGER PRIMARY KEY AUTOINCREMENT,
`pro` REAL,
`one` REAL,
`five` REAL,
`fifteen` REAL,
`addtime` INTEGER
);
""",
            'diskio': """CREATE TABLE `diskio` (
  `id` INTEGER PRIMARY KEY AUTOINCREMENT,
  `read_count` INTEGER,
  `write_count` INTEGER,
  `read_bytes` INTEGER,
  `write_bytes` INTEGER,
  `read_time` INTEGER,
  `write_time` INTEGER,
  `addtime` INTEGER
);
""",
            'network': """CREATE TABLE `network` (
  `id` INTEGER PRIMARY KEY AUTOINCREMENT,
  `up` INTEGER,
  `down` INTEGER,
  `total_up` INTEGER,
  `total_down` INTEGER,
  `down_packets` INTEGER,
  `up_packets` INTEGER,
  `addtime` INTEGER
);
""",
            'process_top_list': """CREATE TABLE `process_top_list` (
  `id` INTEGER PRIMARY KEY AUTOINCREMENT,
  `cpu_top` REAL,
  `memory_top` REAL,
  `disk_top` REAL,
  `net_top` REAL,
  `all_top` REAL,
  `addtime` INTEGER
);
"""
        }
        for table in def_table:
            if table not in fail_list:
                db_obj.execute(def_table_sql[table])

    # 关闭面板
    def ClosePanel(self, get):
        filename = 'data/close.pl'
        if os.path.exists(filename):
            os.remove(filename)
            return public.return_message(0, 0, public.lang("Setup successfully!"))
        public.writeFile(filename, 'True')
        public.ExecShell("chmod 600 " + filename)
        public.ExecShell("chown root.root " + filename)
        return public.return_message(0, 0, public.lang("Setup successfully!"))

    # 设置自动更新
    def AutoUpdatePanel(self, get):
        filename = 'data/autoUpdate.pl'
        if os.path.exists(filename):
            os.remove(filename)
        else:
            public.writeFile(filename, 'True')
            public.ExecShell("chmod 600 " + filename)
            public.ExecShell("chown root.root " + filename)
        return public.return_message(0, 0, public.lang("Setup successfully!"))

    # 设置二级密码
    def SetPanelLock(self, get):
        path = 'data/lock'
        if not os.path.exists(path):
            public.ExecShell('mkdir ' + path)
            public.ExecShell("chmod 600 " + path)
            public.ExecShell("chown root.root " + path)

        keys = ['files', 'tasks', 'config']
        for name in keys:
            filename = path + '/' + name + '.pl'
            if hasattr(get, name):
                public.writeFile(filename, 'True')
            else:
                if os.path.exists(filename): os.remove(filename);

    # 设置PHP守护程序
    def Set502(self, get):
        filename = 'data/502Task.pl'
        if os.path.exists(filename):
            public.ExecShell('rm -f ' + filename)
        else:
            public.writeFile(filename, 'True')

        return public.return_message(0, 0, public.lang("Setup successfully!"))

    # 设置模板
    def SetTemplates(self, get):
        public.writeFile('data/templates.pl', get.templates)
        return public.return_message(0, 0, public.lang("Setup successfully!"))

    def is_ssl_cookie_modified(self):
        from flask import request
        # 假设当SSL启用时，会在cookie名称添加'_ssl'
        suffix = '_ssl'

        # 遍历所有cookie，检查是否有名称以'_ssl'结尾
        for cookie_name in request.cookies:
            if cookie_name.endswith(suffix):
                return True
        return False
    # 设置面板SSL
    def SetPanelSSL(self, get):
        if not os.path.exists("/www/server/panel/ssl/"):
            os.makedirs("/www/server/panel/ssl/")
        #     cert_type   1 自签证书   2 lets   3 其他证书   无参 关闭ssl
        if hasattr(get, "cert_type") and str(get.cert_type) == "2":
            # 自签
            # rep_mail = r"[\w!#$%&'*+/=?^_`{|}~-]+(?:\.[\w!#$%&'*+/=?^_`{|}~-]+)*@(?:[\w](?:[\w-]*[\w])?\.)+[\w](?:[\w-]*[\w])?"
            # if not re.search(rep_mail,get.email):
            #     return public.return_message(-1, 0, public.lang("The E-Mail format is illegal"))
            import setPanelLets
            sp = setPanelLets.setPanelLets()
            sps = sp.set_lets(get)
            status = 0 if sps['status'] else -1
            return public.return_message(status, 0, sps['msg'])
        else:
            sslConf = self._setup_path + '/data/ssl.pl'
            if os.path.exists(sslConf) and not 'cert_type' in get:
                # 关闭ssl
                public.ExecShell('rm -f ' + sslConf + '&& rm -f /www/server/panel/ssl/*')
                t_str = 'Close'
                public.write_log_gettext('Panel configuration', '{} Panel SSL', t_str)
                g.rm_ssl = True
                return public.return_message(0, 0, public.lang("SSL turned off，Please use http protocol to access the panel!"))
            else:

                public.ExecShell('btpip install cffi')
                public.ExecShell('btpip install cryptography')
                public.ExecShell('btpip install pyOpenSSL')
                if not 'cert_type' in get:
                    return public.return_message(-1, 0, public.lang("Please refresh the page and try again!"))
                if get.cert_type in [0, '0']:  # 调用保存面板证书 传参0未出现
                    result = self.SavePanelSSL(get)
                    if result['status'] == -1:
                        return result
                    public.writeFile(sslConf, 'True')
                    public.writeFile('data/reload.pl', 'True')
                # 1 自签证书   3  其他证书 ??
                try:
                    if not self.CreateSSL():
                        return public.return_message(-1, 0, public.lang("Error, unable to auto install pyOpenSSL!<p>Plesea try to manually install: pip install pyOpenSSL</p>"))
                    public.writeFile(sslConf, 'True')
                except:
                    return public.return_message(-1, 0, public.lang("Error, unable to auto install pyOpenSSL!<p>Plesea try to manually install: pip install pyOpenSSL</p>"))
                return public.return_message(0, 0, public.lang("SSL is turned on, plesea use https protocol to access the panel!"))

    # 自签证书
    # def CreateSSL(self):
    #     if os.path.exists('ssl/input.pl'): return True
    #     import OpenSSL
    #     key = OpenSSL.crypto.PKey()
    #     key.generate_key(OpenSSL.crypto.TYPE_RSA, 2048)
    #     cert = OpenSSL.crypto.X509()
    #     cert.set_serial_number(0)
    #     cert.get_subject().CN = public.GetLocalIp()
    #     cert.set_issuer(cert.get_subject())
    #     cert.gmtime_adj_notBefore( 0 )
    #     cert.gmtime_adj_notAfter(86400 * 3650)
    #     cert.set_pubkey( key )
    #     cert.sign( key, 'md5' )
    #     cert_ca = OpenSSL.crypto.dump_certificate(OpenSSL.crypto.FILETYPE_PEM, cert)
    #     private_key = OpenSSL.crypto.dump_privatekey(OpenSSL.crypto.FILETYPE_PEM, key)
    #     if len(cert_ca) > 100 and len(private_key) > 100:
    #         public.writeFile('ssl/certificate.pem',cert_ca,'wb+')
    #         public.writeFile('ssl/privateKey.pem',private_key,'wb+')
    #         return True
    #     return False
    # 自签证书

    def CreateSSL(self):
        import base64
        userInfo = public.get_user_info()
        if not userInfo:
            userInfo['uid'] = 0
            userInfo['access_key'] = 'B' * 32
        domains = self.get_host_all()
        pdata = {
            "action": "get_domain_cert",
            "company": "aapanel.com",
            "domain": ','.join(domains),
            "uid": userInfo['uid'],
            "access_key": 'B' * 32,
            "panel": 1
        }
        cert_api = 'https://api.aapanel.com/aapanel_cert'
        result = json.loads(public.httpPost(cert_api, {'data': json.dumps(pdata)}))
        if 'status' in result:
            if result['status']:
                if os.path.exists('ssl/certificate.pem'):
                    os.remove('ssl/certificate.pem')
                if os.path.exists('ssl/privateKey.pem'):
                    os.remove('ssl/privateKey.pem')
                if os.path.exists('ssl/baota_root.pfx'):
                    os.remove('ssl/baota_root.pfx')
                if os.path.exists('ssl/root_password.pl'):
                    os.remove('ssl/root_password.pl')
                public.writeFile('ssl/certificate.pem', result['cert'])
                public.writeFile('ssl/privateKey.pem', result['key'])
                public.writeFile('ssl/baota_root.pfx', base64.b64decode(result['pfx']), 'wb+')
                public.writeFile('ssl/root_password.pl', result['password'])
                return True
        if os.path.exists('ssl/input.pl'): return True
        import OpenSSL
        key = OpenSSL.crypto.PKey()
        key.generate_key(OpenSSL.crypto.TYPE_RSA, 2048)
        cert = OpenSSL.crypto.X509()
        cert.set_serial_number(0)
        cert.get_subject().CN = public.GetLocalIp()
        cert.set_issuer(cert.get_subject())
        cert.gmtime_adj_notBefore(0)
        cert.gmtime_adj_notAfter(86400 * 3650)
        cert.set_pubkey(key)
        cert.sign(key, 'md5')
        cert_ca = OpenSSL.crypto.dump_certificate(OpenSSL.crypto.FILETYPE_PEM, cert)
        private_key = OpenSSL.crypto.dump_privatekey(OpenSSL.crypto.FILETYPE_PEM, key)

        if len(cert_ca) > 100 and len(private_key) > 100:
            public.writeFile('ssl/certificate.pem', cert_ca, 'wb+')
            public.writeFile('ssl/privateKey.pem', private_key, 'wb+')
            return True
        return False

    def get_ipaddress(self):
        '''
            @name 获取本机IP地址
            @author hwliang<2020-11-24>
            @return list
        '''
        ipa_tmp = \
            public.ExecShell("ip a |grep inet|grep -v inet6|grep -v 127.0.0.1|awk '{print $2}'|sed 's#/[0-9]*##g'")[
                0].strip()
        iplist = ipa_tmp.split('\n')
        return iplist

    def get_host_all(self):
        local_ip = ['127.0.0.1', '::1', 'localhost']
        ip_list = []
        bind_ip = self.get_ipaddress()

        for ip in bind_ip:
            ip = ip.strip()
            if ip in local_ip: continue
            if ip in ip_list: continue
            ip_list.append(ip)
        net_ip = public.httpGet('{}/api/common/getClientIP'.format(public.OfficialApiBase()))

        if net_ip:
            net_ip = net_ip.strip()
            if not net_ip in ip_list:
                ip_list.append(net_ip)
        ip_list = [ip_list[-1], ip_list[0]]
        return ip_list

    # 生成Token
    def SetToken(self, get):
        data = {}
        data[''] = public.GetRandomString(24)

    # 取面板列表
    def GetPanelList(self, get):
        try:
            data = public.M('panel').field('id,title,url,username,password,click,addtime').order('click desc').select()
            if type(data) == str: data[111]
            return public.return_message(0, 0, data)
        except:
            sql = '''CREATE TABLE IF NOT EXISTS `panel` (
  `id` INTEGER PRIMARY KEY AUTOINCREMENT,
  `title` TEXT,
  `url` TEXT,
  `username` TEXT,
  `password` TEXT,
  `click` INTEGER,
  `addtime` INTEGER
);'''
            public.M('sites').execute(sql, ())
            return public.return_message(0, 0, [])

    # 添加面板资料
    def AddPanelInfo(self, get):

        # 校验是还是重复
        isAdd = public.M('panel').where('title=? OR url=?', (get.title, get.url)).count()
        if isAdd: return public.return_message(-1, 0, public.lang("Notes or panel address duplicate!"))
        import time, json
        isRe = public.M('panel').add('title,url,username,password,click,addtime', (
        public.xssencode2(get.title), public.xssencode2(get.url), public.xssencode2(get.username), get.password, 0,
        int(time.time())))
        if isRe: return public.return_message(0, 0, public.lang("Setup successfully!"))
        return public.return_message(-1, 0, public.lang("Failed to add"))

    # 修改面板资料
    def SetPanelInfo(self, get):
        # 校验是还是重复
        isSave = public.M('panel').where('(title=? OR url=?) AND id!=?', (get.title, get.url, get.id)).count()
        if isSave: return public.return_message(-1, 0, public.lang("Notes or panel address duplicate!"))
        import time, json

        # 更新到数据库
        isRe = public.M('panel').where('id=?', (get.id,)).save('title,url,username,password',
                                                               (get.title, get.url, get.username, get.password))
        if isRe: return public.return_message(0, 0, public.lang("Setup successfully!"))
        return public.return_message(-1, 0, public.lang("Failed to modify"))

    # 删除面板资料
    def DelPanelInfo(self, get):
        isExists = public.M('panel').where('id=?', (get.id,)).count()
        if not isExists: return public.return_message(-1, 0, public.lang("Requested panel info does NOT exist!"))
        public.M('panel').where('id=?', (get.id,)).delete()
        return public.return_message(0, 0, public.lang("Successfully deleted"))

    # 点击计数
    def ClickPanelInfo(self, get):
        click = public.M('panel').where('id=?', (get.id,)).getField('click')
        public.M('panel').where('id=?', (get.id,)).setField('click', click + 1)
        return True

    # 获取PHP配置参数
    def GetPHPConf(self, get):
        gets = [
            {'name': 'short_open_tag', 'type': 1, 'ps': public.get_msg_gettext('Short tag support')},
            {'name': 'asp_tags', 'type': 1, 'ps': public.get_msg_gettext('ASP tag support')},
            {'name': 'max_execution_time', 'type': 2, 'ps': public.get_msg_gettext('Max time of running script')},
            {'name': 'max_input_time', 'type': 2, 'ps': public.get_msg_gettext('Max time of input')},
            {'name': 'memory_limit', 'type': 2, 'ps': public.get_msg_gettext('Limit of script memory')},
            {'name': 'post_max_size', 'type': 2, 'ps': public.get_msg_gettext('Max size of POST data')},
            {'name': 'file_uploads', 'type': 1, 'ps': public.get_msg_gettext('Whether to allow upload file')},
            {'name': 'upload_max_filesize', 'type': 2, 'ps': public.get_msg_gettext('Max size of upload file')},
            {'name': 'max_file_uploads', 'type': 2,
             'ps': public.get_msg_gettext('Max value of simultaneously upload file')},
            {'name': 'default_socket_timeout', 'type': 2, 'ps': public.get_msg_gettext('Socket over time')},
            {'name': 'error_reporting', 'type': 3, 'ps': public.get_msg_gettext('Level of error')},
            {'name': 'display_errors', 'type': 1,
             'ps': public.get_msg_gettext('Whether to output detailed error info')},
            {'name': 'cgi.fix_pathinfo', 'type': 0, 'ps': public.get_msg_gettext('Whether to turn on pathinfo')},
            {'name': 'date.timezone', 'type': 3, 'ps': public.get_msg_gettext('Timezone')}
        ]
        phpini_file = '/www/server/php/' + get.version + '/etc/php.ini'
        if public.get_webserver() == 'openlitespeed':
            phpini_file = '/usr/local/lsws/lsphp{}/etc/php/{}.{}/litespeed/php.ini'.format(get.version, get.version[0],
                                                                                           get.version[1])
            if os.path.exists('/etc/redhat-release'):
                phpini_file = '/usr/local/lsws/lsphp' + get.version + '/etc/php.ini'
        phpini = public.readFile(phpini_file)
        if not phpini:
            return public.return_message(-1, 0, public.lang("Error reading PHP configuration file, please try to reinstall this PHP!"))
        result = []
        for g in gets:
            rep = g['name'] + r'\s*=\s*([0-9A-Za-z_&/ ~]+)(\s*;?|\r?\n)'
            tmp = re.search(rep, phpini)
            if not tmp: continue
            g['value'] = tmp.groups()[0]
            result.append(g)

        return result

    def get_php_config(self, get):
        # 取PHP配置
        get.version = get.version.replace('.', '')
        file = session['setupPath'] + "/php/" + get.version + "/etc/php.ini"
        if public.get_webserver() == 'openlitespeed':
            file = '/usr/local/lsws/lsphp{}/etc/php/{}.{}/litespeed/php.ini'.format(get.version, get.version[0],
                                                                                    get.version[1])
            if os.path.exists('/etc/redhat-release'):
                file = '/usr/local/lsws/lsphp' + get.version + '/etc/php.ini'
        phpini = public.readFile(file)
        file = session['setupPath'] + "/php/" + get.version + "/etc/php-fpm.conf"
        phpfpm = public.readFile(file)
        data = {}
        try:
            rep = r"upload_max_filesize\s*=\s*([0-9]+)M"
            tmp = re.search(rep, phpini).groups()
            data['max'] = tmp[0]
        except:
            data['max'] = '50'
        try:
            rep = r"request_terminate_timeout\s*=\s*([0-9]+)\n"
            tmp = re.search(rep, phpfpm).groups()
            data['maxTime'] = tmp[0]
        except:
            data['maxTime'] = 0

        try:
            rep = r"\n;*\s*cgi\.fix_pathinfo\s*=\s*([0-9]+)\s*\n"
            tmp = re.search(rep, phpini).groups()

            if tmp[0] == '1':
                data['pathinfo'] = True
            else:
                data['pathinfo'] = False
        except:
            data['pathinfo'] = False

        return data

    # 提交PHP配置参数
    def SetPHPConf(self, get):
        gets = ['display_errors', 'cgi.fix_pathinfo', 'date.timezone', 'short_open_tag', 'asp_tags',
                'max_execution_time', 'max_input_time', 'memory_limit', 'post_max_size', 'file_uploads',
                'upload_max_filesize', 'max_file_uploads', 'default_socket_timeout', 'error_reporting']
        filename = '/www/server/php/' + get.version + '/etc/php.ini'
        reload_str = '/etc/init.d/php-fpm-' + get.version + ' reload'
        ols_php_path = '/usr/local/lsws/lsphp{}/etc/php/{}.{}/litespeed/php.ini'.format(get.version, get.version[0],
                                                                                        get.version[1])
        if os.path.exists('/etc/redhat-release'):
            ols_php_path = '/usr/local/lsws/lsphp' + get.version + '/etc/php.ini'
        reload_ols_str = '/usr/local/lsws/bin/lswsctrl restart'
        for p in [filename, ols_php_path]:
            if not p:
                continue
            if not os.path.exists(p):
                continue
            phpini = public.readFile(p)
            for g in gets:
                try:
                    rep = g + r'\s*=\s*(.+)\r?\n'
                    val = g + ' = ' + get[g] + '\n'
                    phpini = re.sub(rep, val, phpini)
                except:
                    continue

            public.writeFile(p, phpini)
        public.ExecShell(reload_str)
        public.ExecShell(reload_ols_str)
        return public.return_message(0, 0, public.lang("Setup successfully!"))

    # 取Session缓存方式
    def GetSessionConf(self, get):
        filename = '/www/server/php/' + get.version + '/etc/php.ini'
        if public.get_webserver() == 'openlitespeed':
            filename = '/usr/local/lsws/lsphp{}/etc/php/{}.{}/litespeed/php.ini'.format(get.version, get.version[0],
                                                                                        get.version[1])
            if os.path.exists('/etc/redhat-release'):
                filename = '/usr/local/lsws/lsphp' + get.version + '/etc/php.ini'
        phpini = public.readFile(filename)
        if not isinstance(phpini, str):
            return public.return_message(-1, 0, public.lang('Failed to read PHP configuration file, it may not exist: {}',filename))


        rep = r'session.save_handler\s*=\s*([0-9A-Za-z_& ~]+)(\s*;?|\r?\n)'
        save_handler = re.search(rep, phpini)
        if save_handler:
            save_handler = save_handler.group(1)
        else:
            save_handler = "files"

        reppath = r'\nsession.save_path\s*=\s*"tcp\:\/\/([\w\.]+):(\d+).*\r?\n'
        passrep = r'\nsession.save_path\s*=\s*"tcp://[\w\.\?\:]+=(.*)"\r?\n'
        memcached = r'\nsession.save_path\s*=\s*"([\w\.]+):(\d+)"'
        save_path = re.search(reppath, phpini)
        if not save_path:
            save_path = re.search(memcached, phpini)
        passwd = re.search(passrep, phpini)
        port = ""
        if passwd:
            passwd = passwd.group(1)
        else:
            passwd = ""
        if save_path:
            port = save_path.group(2)
            save_path = save_path.group(1)

        else:
            save_path = ""
        return {"save_handler": save_handler, "save_path": save_path, "passwd": passwd, "port": port}

    # 设置Session缓存方式
    def SetSessionConf(self, get):
        import glob
        g = get.save_handler
        ip = get.ip.strip()
        port = get.port
        passwd = get.passwd
        if g != "files":
            iprep = r"(2(5[0-5]{1}|[0-4]\d{1})|[0-1]?\d{1,2})\.(2(5[0-5]{1}|[0-4]\d{1})|[0-1]?\d{1,2})\.(2(5[0-5]{1}|[0-4]\d{1})|[0-1]?\d{1,2})\.(2(5[0-5]{1}|[0-4]\d{1})|[0-1]?\d{1,2})"
            rep_domain = r"^(?=^.{3,255}$)[a-zA-Z0-9\_\-][a-zA-Z0-9\_\-]{0,62}(\.[a-zA-Z0-9\_\-][a-zA-Z0-9\_\-]{0,62})+$"
            if not re.search(iprep, ip) and not re.search(rep_domain, ip):
                if ip != "localhost":
                    return public.return_message(-1, 0, public.lang("Please enter the correct [domain or IP]!"))
            try:
                port = int(port)
                if port >= 65535 or port < 1:
                    return public.return_message(-1, 0, public.lang("Port range is incorrect! should be between 100-65535"))
            except:
                return public.return_message(-1, 0, public.lang("Port range is incorrect! should be between 100-65535"))
            prep = r"[\~\`\/\=]"
            if re.search(prep, passwd):
                return public.return_message(-1, 0, 'Please do NOT enter the following special characters {}',
                                                 ('" ~ ` / = "'))
        filename = '/www/server/php/' + get.version + '/etc/php.ini'
        filename_ols = None
        ols_exist = os.path.exists("/usr/local/lsws/bin/lswsctrl")
        if ols_exist:
            filename_ols = '/usr/local/lsws/lsphp{}/etc/php/{}.{}/litespeed/php.ini'.format(get.version, get.version[0],
                                                                                            get.version[1])
            if os.path.exists('/etc/redhat-release'):
                filename_ols = '/usr/local/lsws/lsphp' + get.version + '/etc/php.ini'
            try:
                ols_php_os_path = glob.glob("/usr/local/lsws/lsphp{}/lib/php/20*".format(get.version))[0]
            except:
                ols_php_os_path = None
            if os.path.exists("/etc/redhat-release"):
                ols_php_os_path = '/usr/local/lsws/lsphp{}/lib64/php/modules/'.format(get.version)
            ols_so_list = os.listdir(ols_php_os_path)
        else:
            ols_so_list = []
        for f in [filename, filename_ols]:
            if not f:
                continue
            phpini = public.readFile(f)
            rep = r'session.save_handler\s*=\s*(.+)\r?\n'
            val = r'session.save_handler = ' + g + '\n'
            phpini = re.sub(rep, val, phpini)
            if not ols_exist:
                if g == "memcached":
                    if not re.search("memcached.so", phpini):
                        return public.return_message(-1, 0, 'Please install the {} extension first.', (g,))
                    rep = r'\nsession.save_path\s*=\s*(.+)\r?\n'
                    val = r'\nsession.save_path = "%s:%s" \n' % (ip, port)
                    if re.search(rep, phpini):
                        phpini = re.sub(rep, val, phpini)
                    else:
                        phpini = re.sub('\n;session.save_path = "/tmp"', '\n;session.save_path = "/tmp"' + val, phpini)
                if g == "memcache":
                    if not re.search("memcache.so", phpini):
                        return public.return_message(-1, 0, 'Please install the {} extension first.', (g,))
                    rep = r'\nsession.save_path\s*=\s*(.+)\r?\n'
                    val = r'\nsession.save_path = "tcp://%s:%s"\n' % (ip, port)
                    if re.search(rep, phpini):
                        phpini = re.sub(rep, val, phpini)
                    else:
                        phpini = re.sub('\n;session.save_path = "/tmp"', '\n;session.save_path = "/tmp"' + val, phpini)
                if g == "redis":
                    if not re.search("redis.so", phpini):
                        return public.return_message(-1, 0, 'Please install the {} extension first.', (g,))
                    if passwd:
                        passwd = "?auth=" + passwd
                    else:
                        passwd = ""
                    rep = r'\nsession.save_path\s*=\s*(.+)\r?\n'
                    val = r'\nsession.save_path = "tcp://%s:%s%s"\n' % (ip, port, passwd)
                    res = re.search(rep, phpini)
                    if res:
                        phpini = re.sub(rep, val, phpini)
                    else:
                        phpini = re.sub('\n;session.save_path = "/tmp"', '\n;session.save_path = "/tmp"' + val, phpini)
                if g == "files":
                    rep = r'\nsession.save_path\s*=\s*(.+)\r?\n'
                    val = r'\nsession.save_path = "/tmp"\n'
                    if re.search(rep, phpini):
                        phpini = re.sub(rep, val, phpini)
                    else:
                        phpini = re.sub('\n;session.save_path = "/tmp"', '\n;session.save_path = "/tmp"' + val, phpini)
            else:
                if g == "memcached":
                    if "memcached.so" not in ols_so_list:
                        return public.return_message(-1, 0, 'Please install the {} extension first.', (g,))
                    rep = r'\nsession.save_path\s*=\s*(.+)\r?\n'
                    val = r'\nsession.save_path = "%s:%s" \n' % (ip, port)
                    if re.search(rep, phpini):
                        phpini = re.sub(rep, val, phpini)
                    else:
                        phpini = re.sub('\n;session.save_path = "/tmp"', '\n;session.save_path = "/tmp"' + val, phpini)
                if g == "memcache":
                    if "memcache.so" not in ols_so_list:
                        return public.return_message(-1, 0, 'Please install the {} extension first.', (g,))
                    rep = r'\nsession.save_path\s*=\s*(.+)\r?\n'
                    val = r'\nsession.save_path = "tcp://%s:%s"\n' % (ip, port)
                    if re.search(rep, phpini):
                        phpini = re.sub(rep, val, phpini)
                    else:
                        phpini = re.sub('\n;session.save_path = "/tmp"', '\n;session.save_path = "/tmp"' + val, phpini)
                if g == "redis":
                    if "redis.so" not in ols_so_list:
                        return public.return_message(-1, 0, 'Please install the {} extension first.', (g,))
                    if passwd:
                        passwd = "?auth=" + passwd
                    else:
                        passwd = ""
                    rep = r'\nsession.save_path\s*=\s*(.+)\r?\n'
                    val = r'\nsession.save_path = "tcp://%s:%s%s"\n' % (ip, port, passwd)
                    res = re.search(rep, phpini)
                    if res:
                        phpini = re.sub(rep, val, phpini)
                    else:
                        phpini = re.sub('\n;session.save_path = "/tmp"', '\n;session.save_path = "/tmp"' + val, phpini)
                if g == "files":
                    rep = r'\nsession.save_path\s*=\s*(.+)\r?\n'
                    val = r'\nsession.save_path = "/tmp"\n'
                    if re.search(rep, phpini):
                        phpini = re.sub(rep, val, phpini)
                    else:
                        phpini = re.sub('\n;session.save_path = "/tmp"', '\n;session.save_path = "/tmp"' + val, phpini)
            public.writeFile(f, phpini)
        public.ExecShell('/etc/init.d/php-fpm-' + get.version + ' reload')
        public.serviceReload()
        return public.return_message(0, 0, public.lang("Setup successfully!"))

    # 获取Session文件数量
    def GetSessionCount(self, get):
        d = ["/tmp", "/www/php_session"]

        count = 0
        for i in d:
            if not os.path.exists(i): public.ExecShell('mkdir -p %s' % i)
            list = os.listdir(i)
            for l in list:
                if os.path.isdir(i + "/" + l):
                    l1 = os.listdir(i + "/" + l)
                    for ll in l1:
                        if "sess_" in ll:
                            count += 1
                    continue
                if "sess_" in l:
                    count += 1

        s = "find /tmp -mtime +1 |grep 'sess_'|wc -l"
        old_file = int(public.ExecShell(s)[0].split("\n")[0])

        s = "find /www/php_session -mtime +1 |grep 'sess_'|wc -l"
        old_file += int(public.ExecShell(s)[0].split("\n")[0])

        return {"total": count, "oldfile": old_file}

    # 删除老文件
    def DelOldSession(self, get):
        s = "find /tmp -mtime +1 |grep 'sess_'|xargs rm -f"
        public.ExecShell(s)
        s = "find /www/php_session -mtime +1 |grep 'sess_'|xargs rm -f"
        public.ExecShell(s)
        # s = "find /tmp -mtime +1 |grep 'sess_'|wc -l"
        # old_file_conf = int(public.ExecShell(s)[0].split("\n")[0])
        old_file_conf = self.GetSessionCount(get)["oldfile"]
        if old_file_conf == 0:
            return public.return_message(0, 0, public.lang("Successfully deleted"))
        else:
            return public.return_message(0, 0, public.lang("Failed to delete"))

    # 获取面板证书
    def GetPanelSSL(self, get):
        cert = {}
        key_file = 'ssl/privateKey.pem'
        cert_file = 'ssl/certificate.pem'
        if not os.path.exists(key_file):
            self.CreateSSL()
        cert['privateKey'] = public.readFile(key_file)
        cert['certPem'] = public.readFile(cert_file)
        cert['download_root'] = False
        cert['info'] = {}
        if not cert['privateKey']:
            cert['privateKey'] = ''
            cert['certPem'] = ''
        else:
            cert['info'] = public.get_cert_data(cert_file)
            if not cert['info']:
                self.CreateSSL()
                cert['info'] = public.get_cert_data(cert_file)
            if cert['info']:
                if cert['info']['issuer'] == 'aapanel.com':
                    if os.path.exists('ssl/baota_root.pfx'):
                        cert['download_root'] = True
                        cert['root_password'] = public.readFile('ssl/root_password.pl')

        cert['rep'] = os.path.exists('ssl/input.pl')
        return public.return_message(0, 0, cert)

    # 保存面板证书
    def SavePanelSSL(self, get):
        keyPath = 'ssl/privateKey.pem'
        certPath = 'ssl/certificate.pem'
        checkCert = '/tmp/cert.pl'
        ssl_pl = 'data/ssl.pl'
        if not 'certPem' in get: return public.return_message(-1, 0, public.lang("The certPem parameter is missing!"))
        if not 'privateKey' in get: return public.return_message(-1, 0, public.lang("The privateKey parameter is missing!"))
        get.privateKey = get.privateKey.strip()
        get.certPem = get.certPem.strip()
        import ssl_info
        ssl_info = ssl_info.ssl_info()
        # 验证证书和密钥是否匹配格式是否为pem
        check_flag, check_msg = ssl_info.verify_certificate_and_key_match(get.privateKey, get.certPem)
        if not check_flag: return public.return_message(-1, 0, check_msg)
        # 验证证书链是否完整
        check_chain_flag, check_chain_msg = ssl_info.verify_certificate_chain(get.certPem)
        if not check_chain_flag: return public.return_message(-1, 0, check_chain_msg)

        public.writeFile(checkCert, get.certPem)
        if not public.CheckCert(checkCert):
            os.remove(checkCert)
            return public.return_message(-1, 0, public.lang("Certificate ERROR, please check!'"))
        if get.privateKey:
            public.writeFile(keyPath, get.privateKey)
        if get.certPem:
            public.writeFile(certPath, get.certPem)
        public.writeFile('ssl/input.pl', 'True')
        if os.path.exists(ssl_pl): public.writeFile('data/reload.pl', 'True')
        return public.return_message(0, 0, public.lang("Certificate saved!"))

    # 获取ftp端口
    def get_ftp_port(self):
        # 获取FTP端口
        if 'port' in session: return session['port']
        import re
        try:
            file = public.GetConfigValue('setup_path') + '/pure-ftpd/etc/pure-ftpd.conf'
            conf = public.readFile(file)
            rep = r"\n#?\s*Bind\s+[0-9]+\.[0-9]+\.[0-9]+\.+[0-9]+,([0-9]+)"
            port = re.search(rep, conf).groups()[0]
        except:
            port = '21'
        session['port'] = port
        return port

    #获取配置
    def get_config(self, get):
        # public.print_log('v2-get_config')
        import system_v2 as system
        data = {}
        data.update(system.system().GetConcifInfo())
        if 'config' in session:
            session['config']['distribution'] = public.get_linux_distribution()
            session['webserver'] = public.get_webserver()
            session['config']['webserver'] = session['webserver']
            if "basic_auth" in session['config'].keys():
                session['config']['basic_auth'] = self.get_basic_auth_stat(None)
            data = session['config']
        if not data:
            data = public.M('config').where("id=?", ('1',)).field(
                'webserver,sites_path,backup_path,status,mysql_root').find()
        data['webserver'] = public.get_webserver()
        data['distribution'] = public.get_linux_distribution()
        data['request_iptype'] = self.get_request_iptype()
        data['request_type'] = self.get_request_type()
        data['improvement'] = public.get_improvement()
        data['isSetup'] = True
        data['ftpPort'] = int(self.get_ftp_port())
        data['basic_auth'] = self.get_basic_auth_stat(None)
        data['recycle_bin'] = os.path.exists("data/recycle_bin.pl")
        data['recycle_db_bin'] = os.path.exists('data/recycle_bin_db.pl')
        if os.path.exists(public.GetConfigValue('setup_path') + '/nginx') == False \
                and os.path.exists(public.GetConfigValue('setup_path') + '/apache') == False \
                and os.path.exists('/usr/local/lsws/bin/lswsctrl') == False \
                and os.path.exists(public.GetConfigValue('setup_path') + '/php') == False:
            # 查询安装过或者是有正在安装的任务就不显示推荐安装
            num = public.M('tasks').where("name like ? or name like ? or name like ? or name like ? or name like ?",
                                          ('%nginx%', '%apache%', '%php%', '%mysql%', '%pureftpd%')).count()
            if not num:
                data['isSetup'] = False
        p_token = self.get_token(None)['message']

        data['app'] = {'open': p_token['open'], 'apps': p_token['apps']}

        if 'api' not in data: data['api'] = 'checked' if p_token['open'] else ''

        import panel_ssl_v2 as panelSSL
        data['user_info'] = panelSSL.panelSSL().GetUserInfo(None)['message']
        data['user'] = {}
        try:
            data['user']['username'] = public.get_user_info()['username']
        except:
            pass
        data['table_header'] = self.get_table_header(None)
        data["debug"] = "checked" if self.get_debug() else ""
        data["left_title"] = public.readFile("data/title.pl") if os.path.exists("data/title.pl") else ""

        from password import password
        data["username"] = password().get_panel_username(get)
        data["webname"] = public.GetConfigValue("title")

        sess_out_path = 'data/session_timeout.pl'
        if not os.path.exists(sess_out_path):
            public.writeFile(sess_out_path, '86400')
        s_time_tmp = public.readFile(sess_out_path)
        try:
            s_time = int(s_time_tmp)
        except:
            public.writeFile(sess_out_path, '86400')
            s_time = 86400

        data['session_timeout_source'] = s_time
        data['session_timeout'] = self.show_time_by_seconds(s_time)
        data['SSL'] = os.path.exists('data/ssl.pl')

        # 增加防篡改安装信息
        data['tamper_core'] = {}
        data['tamper_core']['setup'] = os.path.exists('/www/server/panel/plugin/tamper_core')
        # 新增 语言包设置信息
        lang = self.get_language()
        data['language'] = lang['default']
        data['language_list'] = lang['languages']
        data['waf'] = {"is_install":0,"status":0,"version":""}
        try:
            data["waf"]["is_install"] = 1 if os.path.exists('/www/server/panel/plugin/btwaf') else 0
            config_data = json.loads(public.readFile("/www/server/btwaf/config.json"))
            data["waf"]["status"] = config_data.get("open","")
            info_data = json.loads(public.readFile("/www/server/panel/plugin/btwaf/info.json"))
            data["waf"]["version"] = info_data.get("versions","")
        except:
            pass
        data['monitor'] = {"is_install":0,"status":0,"version":""}
        try:
            data["monitor"]["is_install"] = 1 if os.path.exists('/www/server/panel/plugin/monitor') else 0
            config_data = json.loads(public.readFile("/www/server/monitor/config/config.json"))
            data["monitor"]["status"] = config_data.get("open","")
            info_data = json.loads(public.readFile("/www/server/panel/plugin/monitor/info.json"))
            data["monitor"]["version"] = info_data.get("versions","")
        except:
            pass
        return data

    def get_configV1(self,get):
        from panelModelV2.publicModel import main
        main().get_public_config(public.to_dict_obj({}))
        data = {}
        if 'config' in session:
            session['config']['distribution'] = public.get_linux_distribution()
            session['webserver'] = public.get_webserver()
            session['config']['webserver'] = session['webserver']
            data = session['config']

        if not data:
            data = public.M('config').where("id=?",('1',)).field('webserver,sites_path,backup_path,status,mysql_root').find()

        # public.print_log(data)
        data['webserver'] = public.get_webserver()
        data['distribution'] = public.get_linux_distribution()
        data['request_iptype'] = self.get_request_iptype()
        data['request_type'] = self.get_request_type()
        lang = self.get_language()
        data['language'] = lang['default']
        data['language_list'] = lang['languages']
        data["debug"] = "checked" if self.get_debug() else ""
        return data

    @staticmethod
    def show_time_by_seconds(seconds: int) -> str:
        if seconds // (60 * 60 * 24) >= 4:  # 4天及以上的，使用天+小时展示
            minutes, seconds = divmod(seconds, 60)
            hours, minutes = divmod(minutes, 60)
            days, hours = divmod(hours, 24)
            if hours == 0:
                # return "%d天" % days
                return public.lang("{} Day(s)", days)
            if minutes == 0:
                # return "%d 天 %d 小时" % (days, hours)
                return public.lang("{} Day(s) {} Hour(s)", days, hours)
            hours = hours + minutes / 60
            # return "%d 天 %.1f 小时" % (days, hours)
            return public.lang("{} Day(s) {} Hour(s)", days, hours)
        elif seconds // (60 * 60) >= 1:  # 3天以内1小时以上，用小时+分钟表示
            minutes, seconds = divmod(seconds, 60)
            hours, minutes = divmod(minutes, 60)
            if minutes == 0:
                # return "%d 小时" % hours
                return public.lang("{} Hour(s)", hours)
            # return "%d 小时 %d 分钟" % (hours, minutes)
            return public.lang("{} Hour(s) {} Minute(s)", hours, minutes)
        else:  # 1小时以内，用分钟表示
            minutes, seconds = divmod(seconds, 60)
            # return "%d 分钟" % minutes
            return public.lang("{} Minute(s)", minutes)

    # 获取debug状态
    def get_debug(self):
        debug_path = 'data/debug.pl'
        return ((os.path.exists(debug_path) and (public.readFile(debug_path) == "True")))

    def get_table_header(self, get):
        """获取表头"""
        table_name = "PHP_Site"
        if hasattr(get, "table_name"):
            table_name = get.table_name
        header_file = "{}/data/table_header_conf.json".format(public.get_panel_path())
        if not os.path.exists(header_file):
            header_data = {table_name: ''}
        else:
            try:
                header_data = json.loads(public.readFile(header_file))
                if not isinstance(header_data, dict):
                    header_data = {}
                header_data = {table_name: header_data.get(table_name, '')}
            except:
                header_data = {table_name: ''}

        if header_data.get("PHP_Site", None):
            try:
                s_table = json.loads(header_data["PHP_Site"])
                for d in s_table:
                    if d["title"] == "流量":
                        if public.GetWebServer() == "openlitespeed":
                            d["disabled"] = True
                            d["value"] = False
                        else:
                            d["disabled"] = False
                header_data["PHP_Site"] = json.dumps(s_table)
            except:
                pass

        return header_data

    # 取面板错误日志
    def get_error_logs(self, get):
        return public.GetNumLines('logs/error.log', 2000)

    def is_pro(self, get):
        import panelAuth, json
        pdata = panelAuth.panelAuth().create_serverid(None)
        url = public.GetConfigValue('home') + '/api/panel/is_pro'
        pluginTmp = public.httpPost(url, pdata)
        pluginInfo = json.loads(pluginTmp)
        return pluginInfo

    def get_token(self, get):
        import panel_api_v2 as panelApi
        return panelApi.panelApi().get_token(get)

    def set_token(self, get):
        import panel_api_v2 as panelApi
        return panelApi.panelApi().set_token(get)

    def get_tmp_token(self, get):
        import panel_api_v2 as panelApi
        return panelApi.panelApi().get_tmp_token(get)

    def GetNginxValue(self, get):
        n = nginx.nginx()
        return public.success_v2(n.GetNginxValue())

    def SetNginxValue(self, get):
        try:
            get.validate([
                Param('worker_processes').Require().String(),
                Param('worker_connections').Require().Integer(),
                Param('keepalive_timeout').Require().Integer(),
                Param('gzip').Require().String(),
                Param('gzip_comp_level').Require().Integer(),
                Param('client_max_body_size').Require().Integer(),
                Param('server_names_hash_bucket_size').Require().String(),
                Param('client_header_buffer_size').Require().Integer(),
                Param('client_body_buffer_size').Require().Integer(),
            ], [
                public.validate.trim_filter(),
            ])
        except Exception as ex:
            public.print_log("error info: {}".format(ex))
            return public.return_message(-1, 0, str(ex))

        n = nginx.nginx()
        res = n.SetNginxValue(get)
        if res.get("status"):
            return public.success_v2(res.get("msg"))
        else:
            return public.fail_v2(res.get("msg"))

    def GetApacheValue(self, get):
        a = apache.apache()
        return public.success_v2(a.GetApacheValue())

    def SetApacheValue(self, get):
        try:
            get.validate([
                Param('Timeout').Require().Integer(),
                Param('KeepAlive').Require().String(),
                Param('KeepAliveTimeout').Require().Integer(),
                Param('MaxKeepAliveRequests').Require().Integer(),
                Param('StartServers').Require().Integer(),
                Param('MaxSpareThreads').Require().Integer(),
                Param('MinSpareThreads').Require().Integer(),
                Param('ThreadsPerChild').Require().Integer(),
                Param('MaxRequestWorkers').Require().Integer(),
                Param('MaxConnectionsPerChild').Require().Integer(),
            ], [
                public.validate.trim_filter(),
            ])
        except Exception as ex:
            public.print_log("error info: {}".format(ex))
            return public.return_message(-1, 0, str(ex))

        a = apache.apache()
        res =  a.SetApacheValue(get)
        if res.get("status"):
            return public.success_v2(res.get("msg"))
        else:
            return public.fail_v2(res.get("msg"))

    def get_ols_value(self, get):
        a = ols.ols()
        return public.success_v2(a.get_value(get))

    def set_ols_value(self, get):
        try:
            get.validate([
                Param('enableGzipCompress').Require().Integer(),
                Param('gzipCompressLevel').Require().Integer('between', [1, 9]),
                Param('rollingSize').Require().String(),
                Param('maxConnections').Require().Integer(),
                Param('maxSSLConnections').Require().Integer(),
                Param('connTimeout').Require().Integer(),
                Param('maxKeepAliveReq').Require().Integer(),
            ], [
                public.validate.trim_filter(),
            ])
            if not get.rollingSize.endswith("M"):
                return public.fail_v2("rollingSize should be like '10M'")
        except Exception as ex:
            public.print_log("error info: {}".format(ex))
            return public.fail_v2(str(ex))

        obj = public.dict_obj()
        obj.array = json.dumps(
            {
                "enableGzipCompress": get.enableGzipCompress,
                "gzipCompressLevel": get.gzipCompressLevel,
                "rollingSize": get.rollingSize,
                "maxConnections": get.maxConnections,
                "maxSSLConnections": get.maxSSLConnections,
                "connTimeout": get.connTimeout,
                "maxKeepAliveReq": get.maxKeepAliveReq,
            }
        )
        a = ols.ols()
        return a.set_value(obj)

    def get_ols_private_cache(self, get):
        a = ols.ols()
        return a.get_private_cache(get)

    def get_ols_static_cache(self, get):
        a = ols.ols()
        return a.get_static_cache(get)

    def set_ols_static_cache(self, get):
        a = ols.ols()
        return a.set_static_cache(get)

    def switch_ols_private_cache(self, get):
        a = ols.ols()
        return a.switch_private_cache(get)

    def set_ols_private_cache(self, get):
        a = ols.ols()
        return a.set_private_cache(get)

    def get_ols_private_cache_status(self, get):
        a = ols.ols()
        return a.get_private_cache_status(get)

    def get_ipv6_listen(self, get):
        return os.path.exists('data/ipv6.pl')

    def set_ipv6_status(self, get):
        ipv6_file = 'data/ipv6.pl'
        if self.get_ipv6_listen(get):
            os.remove(ipv6_file)
            public.write_log_gettext('Panel setting', 'Disable IPv6 compatibility of the panel!')
        else:
            public.writeFile(ipv6_file, 'True')
            public.write_log_gettext('Panel setting', 'Enable IPv6 compatibility of the panel!')
        public.restart_panel()
        return public.return_message(0, 0, public.lang("Setup successfully!"))

    # 自动补充CLI模式下的PHP版本
    def auto_cli_php_version(self, get):
        import panel_site_v2 as panelSite
        php_versions = panelSite.panelSite().GetPHPVersion(get, False)
        if not php_versions or len(php_versions) == 0:
            return public.return_message(-1, 0, public.lang('No PHP version is installed, cannot set it automatically'))
        php_bin_src = "/www/server/php/%s/bin/php" % php_versions[-1]['version']
        if not os.path.exists(php_bin_src): return public.return_message(-1, 0, public.lang("PHP is not installed"))
        get.php_version = php_versions[-1]['version']
        self.set_cli_php_version(get)
        return public.return_message(0, 0, php_versions[-1])

    # 获取CLI模式下的PHP版本
    def get_cli_php_version(self, get):
        php_bin = '/usr/bin/php'
        if not os.path.exists(php_bin) or not os.path.islink(php_bin):  return self.auto_cli_php_version(get)
        link_re = os.readlink(php_bin)
        if not os.path.exists(link_re): return self.auto_cli_php_version(get)
        import panel_site_v2 as panelSite
        php_versions = panelSite.panelSite().GetPHPVersion(get, False)
        if len(php_versions) == 0:
            return public.return_message(-1, 0, public.lang("Failed to get php version!"))
        del (php_versions[0])
        for v in php_versions:
            if link_re.find(v['version']) != -1: return public.return_message(0, 0,
                                                                              {"select": v, "versions": php_versions})
        return_message = self.auto_cli_php_version(get)
        return public.return_message(0, 0, {"select": return_message['message'], "versions": php_versions})

    # 设置CLI模式下的PHP版本
    def set_cli_php_version(self, get):
        # 校验参数
        try:
            get.validate([
                Param('php_version').String(),
            ], [
                public.validate.trim_filter(),
            ])
        except Exception as ex:
            public.print_log("error info: {}".format(ex))
            return public.return_message(-1, 0, str(ex))

        php_bin = '/usr/bin/php'
        php_bin_src = "/www/server/php/%s/bin/php" % get.php_version
        php_ize = '/usr/bin/phpize'
        php_ize_src = "/www/server/php/%s/bin/phpize" % get.php_version
        php_fpm = '/usr/bin/php-fpm'
        php_fpm_src = "/www/server/php/%s/sbin/php-fpm" % get.php_version
        php_pecl = '/usr/bin/pecl'
        php_pecl_src = "/www/server/php/%s/bin/pecl" % get.php_version
        php_pear = '/usr/bin/pear'
        php_pear_src = "/www/server/php/%s/bin/pear" % get.php_version
        php_cli_ini = '/etc/php-cli.ini'
        php_cli_ini_src = "/www/server/php/%s/etc/php-cli.ini" % get.php_version
        if not os.path.exists(php_bin_src): return public.return_message(-1, 0, public.lang("Specified PHP version not installed"))
        is_chattr = public.ExecShell('lsattr /usr|grep /usr/bin')[0].find('-i-')
        if is_chattr != -1: public.ExecShell('chattr -i /usr/bin')
        public.ExecShell(
            "rm -f " + php_bin + ' ' + php_ize + ' ' + php_fpm + ' ' + php_pecl + ' ' + php_pear + ' ' + php_cli_ini)
        public.ExecShell("ln -sf %s %s" % (php_bin_src, php_bin))
        public.ExecShell("ln -sf %s %s" % (php_ize_src, php_ize))
        public.ExecShell("ln -sf %s %s" % (php_fpm_src, php_fpm))
        public.ExecShell("ln -sf %s %s" % (php_pecl_src, php_pecl))
        public.ExecShell("ln -sf %s %s" % (php_pear_src, php_pear))
        public.ExecShell("ln -sf %s %s" % (php_cli_ini_src, php_cli_ini))
        import jobs_v2 as jobs
        jobs.set_php_cli_env()
        if is_chattr != -1:  public.ExecShell('chattr +i /usr/bin')
        public.write_log_gettext('Panel settings', 'Set the PHP-CLI version to: {}', (get.php_version,))
        return public.return_message(0, 0, public.lang("Setup successfully!"))

    # 获取BasicAuth状态
    def get_basic_auth_stat(self, get):
        path = 'config/basic_auth.json'
        is_install = True
        result = {"basic_user": "", "basic_pwd": "", "open": False, "is_install": is_install}
        if not os.path.exists(path): return result
        try:
            ba_conf = json.loads(public.readFile(path))
        except:
            os.remove(path)
            return result
        ba_conf['is_install'] = is_install
        return ba_conf

    # 设置BasicAuth
    def set_basic_auth(self, get):
        is_open = False
        if get.open == 'True': is_open = True
        tips = '_bt.cn'
        path = 'config/basic_auth.json'
        ba_conf = None
        if is_open:
            if not get.basic_user.strip() or not get.basic_pwd.strip(): return public.return_message(-1, 0, public.lang("BasicAuth authentication username and password cannot be empty!"))
        if os.path.exists(path):
            try:
                ba_conf = json.loads(public.readFile(path))
            except:
                os.remove(path)

        if not ba_conf:
            ba_conf = {"basic_user": public.md5(get.basic_user.strip() + tips),
                       "basic_pwd": public.md5(get.basic_pwd.strip() + tips), "open": is_open}
        else:
            if get.basic_user: ba_conf['basic_user'] = public.md5(get.basic_user.strip() + tips)
            if get.basic_pwd: ba_conf['basic_pwd'] = public.md5(get.basic_pwd.strip() + tips)
            ba_conf['open'] = is_open

        public.writeFile(path, json.dumps(ba_conf))
        os.chmod(path, 384)
        public.write_log_gettext('Panel settings', 'Set the BasicAuth status to: {}', (is_open,))
        public.add_security_logs('Panel settings', ' Set the BasicAuth status to: %s' % is_open)
        public.writeFile('data/reload.pl', 'True')
        return public.return_message(0, 0, public.lang("Setup successfully!"))

    # xss 防御
    def xsssec(self, text):
        return text.replace('<', '&lt;').replace('>', '&gt;')

    # 取面板运行日志
    def get_panel_error_logs(self, get):
        filename = 'logs/error.log'
        if not os.path.exists(filename): return public.return_message(-1, 0, public.lang("Logs emptied"))
        result = public.GetNumLines(filename, 2000)
        return public.return_message(0, 0, self.xsssec(result))

    # 清空面板运行日志
    def clean_panel_error_logs(self, get):
        filename = 'logs/error.log'
        public.writeFile(filename, '')
        public.write_log_gettext('Panel settings', 'Clearing log info')
        public.add_security_logs('Panel settings', 'Clearing log info')
        return public.return_message(0, 0, public.lang("Cleared!"))

    # 获取lets证书
    def get_cert_source(self, get):
        import setPanelLets
        sp = setPanelLets.setPanelLets()
        spg = sp.get_cert_source()
        return public.return_message(0, 0, spg)

    # 设置debug模式
    def set_debug(self, get):
        debug_path = 'data/debug.pl'
        if os.path.exists(debug_path):
            t_str = 'Close'
            os.remove(debug_path)
        else:
            t_str = 'Open'
            public.writeFile(debug_path, 'True')
        public.write_log_gettext('Panel configuration', '{} Developer mode(DeBug)', (t_str,))
        public.restart_panel()
        return public.return_message(0, 0, public.lang("Setup successfully!"))

    # 设置离线模式
    def set_local(self, get):
        d_path = 'data/not_network.pl'
        if os.path.exists(d_path):
            t_str = 'Close'
            os.remove(d_path)
        else:
            t_str = 'Open'
            public.writeFile(d_path, 'True')
        public.write_log_gettext('Panel configuration', '{} Offline mode', (t_str,))
        return public.return_message(0, 0, public.lang("Setup successfully!"))

    # 修改.user.ini文件
    def _edit_user_ini(self, file, s_conf, act, session_path):
        public.ExecShell("chattr -i {}".format(file))
        conf = public.readFile(file)
        if act == "1":
            if "session.save_path" in conf:
                return False
            conf = conf + ":{}/".format(session_path)
            conf = conf + "\n" + s_conf
        else:
            rep = "\n*session.save_path(.|\n)*files"
            rep1 = ":{}".format(session_path)
            conf = re.sub(rep, "", conf)
            conf = re.sub(rep1, "", conf)
        public.writeFile(file, conf)
        public.ExecShell("chattr +i {}".format(file))

    # 设置php_session存放到独立文件夹
    def set_php_session_path(self, get):
        '''
        get.id      site id
        get.act     0/1
        :param get:
        :return:
        '''
        # 校验参数
        try:
            get.validate([
                Param('id').Integer(),
                Param('act').Integer(),
            ], [
                public.validate.trim_filter(),
            ])
        except Exception as ex:
            public.print_log("error info: {}".format(ex))
            return public.return_message(-1, 0, str(ex))
        if public.get_webserver() == 'openlitespeed':
            return public.return_message(-1, 0, public.lang("The current web server is openlitespeed. This function is not supported yet."))

        site_info = public.M('sites').where('id=?', (get.id,)).field('name,path').find()
        session_path = "/www/php_session/{}".format(site_info["name"])
        if not os.path.exists(session_path):
            os.makedirs(session_path)
            public.ExecShell('chown www.www {}'.format(session_path))
        import panel_site_v2
        site_run_info = panel_site_v2.panelSite().GetSiteRunPath(get)
        if not site_run_info.get('status', False) or 'message' not in site_run_info:
            return public.return_message(-1, 0, "Site operation directory information cannot be obtained")
        run_path = site_run_info['message'].get('runPath', '')
        if not run_path:
            return public.return_message(-1, 0, "The site run directory is not set")


        run_path = panel_site_v2.panelSite().GetSiteRunPath(get)['message']["runPath"]


        user_ini_file = "{site_path}{run_path}/.user.ini".format(site_path=site_info["path"], run_path=run_path)
        conf = "session.save_path={}/\nsession.save_handler = files".format(session_path)
        if get.act == "1":
            if not os.path.exists(user_ini_file):
                public.writeFile(user_ini_file, conf)
                public.ExecShell("chattr +i {}".format(user_ini_file))
                # public.print_log("5")
                return public.return_message(0, 0, public.lang("Setup successfully!"))
            self._edit_user_ini(user_ini_file, conf, get.act, session_path)
            return public.return_message(0, 0, public.lang("Setup successfully!"))
        else:
            self._edit_user_ini(user_ini_file, conf, get.act, session_path)
            return public.return_message(0, 0, public.lang("Setup successfully!"))

    # 获取php_session是否存放到独立文件夹
    def get_php_session_path(self, get):
        # 校验参数
        try:
            get.validate([
                Param('id').Integer(),
            ], [
                public.validate.trim_filter(),
            ])
        except Exception as ex:
            public.print_log("error info: {}".format(ex))
            return public.return_message(-1, 0, str(ex))

        # import panelSite
        site_info = public.M('sites').where('id=?', (get.id,)).field('name,path').find()
        if site_info:
            import panel_site_v2
            try:
                run_path = panel_site_v2.panelSite().GetSiteRunPath(get)['message']["runPath"]
            except:
                return public.return_message(0, 0, False)
            # run_path = panelSite.panelSite().GetSiteRunPath(get)["runPath"]
            user_ini_file = "{site_path}{run_path}/.user.ini".format(site_path=site_info["path"], run_path=run_path)
            conf = public.readFile(user_ini_file)
            if conf and "session.save_path" in conf:
                return public.return_message(0, 0, True)
        return public.return_message(0, 0, False)

    def _create_key(self):
        get_token = pyotp.random_base32()  # returns a 16 character base32 secret. Compatible with Google Authenticator
        public.writeFile(self._key_file, get_token)
        username = self.get_random()
        public.writeFile(self._username_file, username)

    def get_key(self, get):
        key = public.readFile(self._key_file)
        username = public.readFile(self._username_file)
        if not key:
            return public.return_message(-1, 0, public.lang("The key does not exist. Please turn on and try again."))
        if not username:
            return public.return_message(-1, 0, public.lang("The username does not exist. Please turn on and try again."))
        return public.return_message(0, 0,{"key": key, "username": username})

    def get_random(self):
        import random
        seed = "1234567890abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"
        sa = []
        for _ in range(8):
            sa.append(random.choice(seed))
        salt = ''.join(sa)
        return salt

    def set_two_step_auth(self, get):
        if not hasattr(get, "act") or not get.act:
            return public.return_message(-1, 0, public.lang("Please enter the operation mode"))
        if get.act == "1":
            if not os.path.exists(self._core_fle_path):
                os.makedirs(self._core_fle_path)
            username = public.readFile(self._username_file)
            if not os.path.exists(self._bk_key_file):
                secret_key = public.readFile(self._key_file)
                if not secret_key or not username:
                    self._create_key()
            else:
                os.rename(self._bk_key_file, self._key_file)
            secret_key = public.readFile(self._key_file)
            username = public.readFile(self._username_file)
            local_ip = public.GetLocalIp()
            if not secret_key:
                return public.return_message(-1, 0,
                                                 "Failed to generate key or username. Please check if the hard disk space is insufficient or the directory cannot be written.[ {} ]",
                                                 (self._setup_path + "/data/",))
            try:
                try:
                    panel_name = json.loads(public.readFile(self._setup_path + '/config/config.json'))['title']
                except:
                    panel_name = 'aaPanel'
                data = pyotp.totp.TOTP(secret_key).provisioning_uri(username,
                                                                    issuer_name='{}--{}'.format(panel_name, local_ip))
                public.writeFile(self._core_fle_path + '/qrcode.txt', str(data))
                return public.return_message(0, 0, public.lang("Setup successfully!"))
            except Exception as e:
                return public.return_message(-1, 0, e)
        else:
            if os.path.exists(self._key_file):
                os.rename(self._key_file, self._bk_key_file)
            return public.return_message(0, 0, public.lang("Setup successfully!"))

    # 检测是否开启双因素验证
    def check_two_step(self, get):
        secret_key = public.readFile(self._key_file)
        if not secret_key:
            return public.return_message(0, 0, False)
        return public.return_message(0, 0, True)

    # 读取二维码data
    def get_qrcode_data(self, get):
        data = public.readFile(self._core_fle_path + '/qrcode.txt')
        if data:
            return public.return_message(0, 0,  data)
        return public.return_message(0, 0, public.lang("No QR code data, please re-open"))

    # 设置是否云控打开
    def set_coll_open(self, get):
        if not 'coll_show' in get: return public.return_message(-1, 0, public.lang("Parameter ERROR!"))
        if get.coll_show == 'True':
            session['tmp_login'] = True
        else:
            session['tmp_login'] = False
        return public.return_message(0, 0, public.lang("Setup successfully!"))

    # 是否显示软件推荐
    def show_recommend(self, get):
        pfile = 'data/not_recommend.pl'
        if os.path.exists(pfile):
            os.remove(pfile)
        else:
            public.writeFile(pfile, 'True')
        return public.return_message(0, 0, public.lang("Setup successfully!"))

    @staticmethod
    def __make_sure_enable_menu(result: list) -> list:
        if not filter(lambda x: x['id'] == 'memuA', result):
            result.append({"id": "memuA", "title": "Home", "show": True, "sort": 1})
        if not filter(lambda x: x['id'] == 'dologin', result):
            result.append({"id": "dologin", "title": "Log out", "show": True, "sort": 16})
        return result

    @staticmethod
    def __filter_users_menu(uid: int, menu_init_data: list, result: list) -> list:
        if not uid or not menu_init_data or not result:
            return []

        user_authority = public.get_user_authority_info(uid)
        if not user_authority.get('state'):
            return [
                {'id': 'dologin', 'title': 'Log out', 'show': True, 'sort': 16}
            ]

        if user_authority.get('role') != 'administrator':  # other user
            menu_dict = {x.get('id'): x.get('href') for x in menu_init_data}
            for i in result:
                try:  # "memuA" "dologin" must be enable
                    if i.get('id') == 'dologin' or i.get('id') == 'memuA':
                        i['show'] = True
                    elif menu_dict[i['id']] in user_authority['menu']:
                        i['show'] = True
                    else:
                        i['show'] = False
                except Exception as e:
                    public.print_log(f"get_menu_list error {e}")
                    i['show'] = False
            return result

        else: # admin
            return result


    # 获取菜单列表
    def get_menu_list(self, get = None) -> public.return_message:
        """
            @name 获取aapanel菜单列表
            @author hwliang<2020-08-31>
            @param get<dict_obj>
            @return list
        """
        menu_path = 'config/menu.json'
        hide_menu_file = 'config/hide_menu.json'
        menu_file = public.ReadFile(menu_path)
        menu_init_data = json.loads(menu_file) if menu_file else []
        if not os.path.exists(hide_menu_file):
            public.writeFile(hide_menu_file, '[]')
        hide_menu = public.ReadFile(hide_menu_file)
        hide_menu = json.loads(hide_menu) if hide_menu else []
        result = [
            {
                'id': d['id'],
                'title': d['title'],
                'href': d['href'],
                'class': d['class'],
                'show': not d['id'] in hide_menu,
                'sort': d['sort'],
            } for d in menu_init_data
        ]
        result = self.__make_sure_enable_menu(result)
        uid = session.get('uid', 0)

        if session.get("tmp_login"):  # template login all mune
            return public.return_message(0, 0, sorted(result, key=lambda x: x['sort']))

        if uid and uid != 1: # maybe other user
            result = self.__filter_users_menu(uid, menu_init_data, result)
            return public.return_message(0, 0, sorted(result, key=lambda x: x['sort']))
        # admin
        return public.return_message(0, 0, sorted(result, key=lambda x: x['sort']))

    # 设置隐藏菜单列表
    def set_hide_menu_list(self, get):
        '''
            @name 设置隐藏菜单列表
            @author hwliang<2020-08-31>
            @param get<dict_obj> {
                hide_list: json<list> 所有不显示的菜单ID
            }
            @return dict
        '''
        hide_menu_file = 'config/hide_menu.json'
        not_hide_id = ["dologin", "memuAconfig", "memuAsoft", "memuA"]  # 禁止隐藏的菜单

        hide_list = json.loads(get.hide_list)
        hide_menu = []
        for h in hide_list:
            if h in not_hide_id:
                continue
            hide_menu.append(h)
        public.writeFile(hide_menu_file, json.dumps(hide_menu))
        public.write_log_gettext('Panel setting', 'Successfully modify the panel menu display list')
        return public.return_message(0, 0, public.lang("Setup successfully!"))

    # 获取临时登录列表
    def get_temp_login(self, args):
        '''
            @name 获取临时登录列表
            @author hwliang<2020-09-2>
            @return dict
        '''
        if 'tmp_login_expire' in session: return public.return_message(-1, 0, public.lang("Permission denied!"))
        public.M('temp_login').where('state=? and expire<?', (0, int(time.time()))).setField('state', -1)
        callback = ''
        if 'tojs' in args:
            callback = args.tojs
        p = 1
        if 'p' in args:
            p = int(args.p)
        rows = 12
        if 'rows' in args:
            rows = int(args.rows)
        count = public.M('temp_login').count()
        data = {}
        page_data = public.get_page(count, p, rows, callback)
        data['page'] = page_data['page']
        data['data'] = public.M('temp_login').limit(page_data['shift'] + ',' + page_data['row']).order('id desc').field(
            'id,addtime,expire,login_time,login_addr,state').select()
        for i in range(len(data['data'])):
            data['data'][i]['online_state'] = os.path.exists('data/session/{}'.format(data['data'][i]['id']))
        return public.return_message(0, 0,  data)

    # 设置临时登录
    def set_temp_login(self, get):
        '''
            @name 设置临时登录
            @author hwliang<2020-09-2>
            @return dict
        '''
        s_time = int(time.time())
        expire_time = get.expire_time if "expire_time" in get else s_time + 3600
        if 'tmp_login_expire' in session: return public.return_message(-1, 0, public.lang("Permission denied!"))
        public.M('temp_login').where('state=? and expire>?', (0, s_time)).delete()
        token = public.GetRandomString(48)
        salt = public.GetRandomString(12)

        pdata = {
            'token': public.md5(token + salt),
            'salt': salt,
            'state': 0,
            'login_time': 0,
            'login_addr': '',
            'expire': int(expire_time),
            'addtime': s_time
        }

        if not public.M('temp_login').count():
            pdata['id'] = 101

        if public.M('temp_login').insert(pdata):
            public.write_log_gettext('Panel setting', 'Generate temporary connection, expiration time: {}',
                                     (public.format_date(times=pdata['expire']),))

            data = {
                'msg': public.lang("Temporary login URL has been generated"),
                'token': token,
                'expire': pdata['expire']
            }

            return public.return_message(0, 0, data)
        return public.return_message(-1, 0, public.lang("Failed to generate temporary login URL"))

    # 删除临时登录
    def remove_temp_login(self, args):
        '''
            @name 删除临时登录
            @author hwliang<2020-09-2>
            @param args<dict_obj>{
                id: int<临时登录ID>
            }
            @return dict
        '''
        if 'tmp_login_expire' in session: return public.return_message(-1, 0, public.lang("Permission denied!"))
        id = int(args.id)
        if public.M('temp_login').where('id=?', (id,)).delete():
            public.write_log_gettext('Panel setting', 'Delete temporary login URL')
            return public.return_message(0, 0, public.lang("Successfully deleted"))
        return public.return_message(-1, 0, public.lang("Failed to delete"))

    # 强制弹出指定临时登录
    def clear_temp_login(self, args):
        '''
            @name 强制登出
            @author hwliang<2020-09-2>
            @param args<dict_obj>{
                id: int<临时登录ID>
            }
            @return dict
        '''
        if 'tmp_login_expire' in session: return public.return_message(-1, 0, public.lang("Permission denied!"))
        id = int(args.id)
        s_file = 'data/session/{}'.format(id)
        if os.path.exists(s_file):
            os.remove(s_file)
            public.write_log_gettext('Panel setting', 'Force logout of temporary users:{1}', (str(id),))
            return public.return_message(0, 0, 'Temporary user has been forcibly logged out:{}', (str(id),))
        return public.return_message(-1, 0, 'The specified user is not currently logged in!')

    #设置免费网站监控报表
    def set_site_total_setup(self, args):
        '''
            @name 设置免费网站监控安装状态
            @author hwliang<2020-09-2>
            @param args<dict_obj>{
                is_install: int<安装状态>
            }
            @return dict
        '''
        site_total_install = '{}/data/site_total_install.pl'.format(public.get_panel_path())
        site_total_uninstall = '{}/data/site_total_uninstall.pl'.format(public.get_panel_path())
        if 'tmp_login_expire' in session: return public.return_message(-1, 0, public.lang("Permission denied!"))
        if public.GetWebServer() =="openlitespeed":
            return public.return_message(-1, 0, 'Only nginx and apache supports free website monitoring!')
        is_install=int(args.is_install)
        if is_install == 1:#安装免费网站监控
            if os.path.exists("/etc/systemd/system/site_total.service"):
                return public.return_message(-1, 0, 'Free website monitoring has been installed!')
            if os.path.exists(os.path.join(public.get_panel_path(),"plugin/monitor/info.json")):
                return public.return_message(-1, 0, 'website monitoring has been installed!')
            if os.path.exists(site_total_uninstall):
                os.remove(site_total_uninstall)
            public.writeFile(site_total_install, 'true')
            execstr="curl https://node.aapanel.com/site_total/install.sh|bash"
            public.ExecShell(execstr)
            if not os.path.exists("/etc/systemd/system/site_total.service"):
                return public.return_message(-1, 0, 'Free website monitoring installation failed!')
        else:#卸载免费网站监控
            if os.path.exists(site_total_install):
                os.remove(site_total_install)
            public.writeFile(site_total_uninstall, 'true')
            execstr="bash /www/server/site_total/scripts/uninstall.sh"
            public.ExecShell(execstr)
            if os.path.exists("/www/server/apache/bin/httpd"):
                public.ExecShell("rm -f /www/server/panel/vhost/apache/extension/*/site_total.conf")
                public.ExecShell('pkill -9 httpd')
                public.ExecShell('/etc/init.d/httpd start')
                time.sleep(0.5)
            if os.path.exists("/etc/systemd/system/site_total.service"):
                return public.return_message(-1, 0, "Setup failed, please manually uninstall the site_total_monitor!")

        return public.return_message(0, 0, public.lang("Setup successful!"))

    # 查看临时授权操作日志
    def get_temp_login_logs(self, args):
        '''
            @name 查看临时授权操作日志
            @author hwliang<2020-09-2>
            @param args<dict_obj>{
                id: int<临时登录ID>
            }
            @return dict
        '''
        if 'tmp_login_expire' in session:
            return public.return_message(-1, 0, public.lang("Permission denied!"))
        id = int(args.id)
        data = public.M('logs').where('uid=?', (id,)).order('id desc').select()
        return public.return_message(0, 0, data)

    def add_nginx_access_log_format(self, args):
        n = nginx.nginx()
        return n.add_nginx_access_log_format(args)

    def del_nginx_access_log_format(self, args):
        n = nginx.nginx()
        return n.del_nginx_access_log_format(args)

    def get_nginx_access_log_format(self, args):
        n = nginx.nginx()
        return public.success_v2(n.get_nginx_access_log_format(args))

    def set_format_log_to_website(self, args):
        n = nginx.nginx()
        return n.set_format_log_to_website(args)

    def get_nginx_access_log_format_parameter(self, args):
        n = nginx.nginx()
        return public.success_v2(n.get_nginx_access_log_format_parameter(args))

    def add_httpd_access_log_format(self, args):
        a = apache.apache()
        return a.add_httpd_access_log_format(args)

    def del_httpd_access_log_format(self, args):
        a = apache.apache()
        return a.del_httpd_access_log_format(args)

    def get_httpd_access_log_format(self, args):
        a = apache.apache()
        return a.get_httpd_access_log_format(args)

    def set_httpd_format_log_to_website(self, args):
        a = apache.apache()
        return a.set_httpd_format_log_to_website(args)

    def get_httpd_access_log_format_parameter(self, args):
        a = apache.apache()
        return a.get_httpd_access_log_format_parameter(args)

    def get_file_deny(self, args):
        import file_execute_deny_v2
        p = file_execute_deny_v2.FileExecuteDeny()
        return p.get_file_deny(args)

    def set_file_deny(self, args):
        import file_execute_deny_v2
        p = file_execute_deny_v2.FileExecuteDeny()
        return p.set_file_deny(args)

    def del_file_deny(self, args):
        import file_execute_deny_v2
        p = file_execute_deny_v2.FileExecuteDeny()
        return p.del_file_deny(args)

    # 查看告警
    def get_login_send(self, get):
        send_type = ""
        login_send_type_conf = "/www/server/panel/data/panel_login_send.pl"
        if os.path.exists(login_send_type_conf):
            send_type = public.ReadFile(login_send_type_conf).strip()
        else:

            if os.path.exists("/www/server/panel/data/login_send_type.pl"):
                send_type = public.readFile("/www/server/panel/data/login_send_type.pl")
            else:
                if os.path.exists('/www/server/panel/data/login_send_mail.pl'):
                    send_type = "mail"
                if os.path.exists('/www/server/panel/data/login_send_dingding.pl'):
                    send_type = "dingding"
        return public.return_message(0, 0, send_type)

    # 取消告警
    def clear_login_send(self, get):
        type = get.type.strip()
        if type == 'mail':
            if os.path.exists("/www/server/panel/data/login_send_mail.pl"):
                os.remove("/www/server/panel/data/login_send_mail.pl")
        elif type == 'dingding':
            if os.path.exists("/www/server/panel/data/login_send_dingding.pl"):
                os.remove("/www/server/panel/data/login_send_dingding.pl")

        login_send_type_conf = "/www/server/panel/data/login_send_type.pl"
        if os.path.exists(login_send_type_conf):
            os.remove(login_send_type_conf)
        login_send_type_conf = "/www/server/panel/data/panel_login_send.pl"
        if os.path.exists(login_send_type_conf):
            os.remove(login_send_type_conf)
        return public.return_message(0, 0, public.lang("Canceling the login alarm succeeded.！"))

    def get_login_area(self, get):
        """
        @获取面板登录告警
        @return
            login_status 是否开启面板登录告警
            login_area 是否开启面板异地登录告警
        """
        result = {}
        result['login_status'] = self.get_login_send(get)['msg']

        result['login_area'] = ''
        sfile = '{}/data/panel_login_area.pl'.format(public.get_panel_path())
        if os.path.exists(sfile):
            result['login_area_status'] = public.readFile(sfile)
        return result

    def set_login_area(self, get):
        """
        @name 设置异地登录告警
        @param get
        """
        sfile = '{}/data/panel_login_area.pl'.format(public.get_panel_path())
        set_type = get.type.strip()
        obj = public.init_msg(set_type)
        if not obj:
            return public.return_message(-1, 0, public.lang("The alarm module is not installed."))

        public.writeFile(sfile, set_type)
        return public.return_message(0, 0, public.lang("successfully set"))

    def get_login_area_list(self, get):
        """
        @name 获取面板常用地区登录

        """
        data = {}
        sfile = '{}/data/panel_login_area.json'.format(public.get_panel_path())
        try:
            data = json.loads(public.readFile(sfile))
        except:
            pass

        result = []
        for key in data.keys():
            result.append({'area': key, 'count': data[key]})

        result = sorted(result, key=lambda x: x['count'], reverse=True)
        return result

    def clear_login_list(self, get):
        """
        @name 清理常用登录地区
        """
        sfile = '{}/data/panel_login_area.json'.format(public.get_panel_path())
        if os.path.exists(sfile):
            os.remove(sfile)
        return public.return_message(0, 0, public.lang("Successful operation."))

    # def get_login_send(self,get):
    #     result={}
    #     import time
    #     time.sleep(0.01)
    #     if os.path.exists('/www/server/panel/data/login_send_mail.pl'):
    #         result['mail']=True
    #     else:
    #         result['mail']=False
    #     if os.path.exists('/www/server/panel/data/login_send_dingding.pl'):
    #         result['dingding']=True
    #     else:
    #         result['dingding']=False
    #     if result['mail'] or result['dingding']:
    #         return public.return_message(0, 0, result)
    #     return public.return_message(-1, 0, result)

    # 设置告警
    def set_login_send(self, get):
        login_send_type_conf = "/www/server/panel/data/panel_login_send.pl"

        set_type = get.type.strip()
        msg_configs = self.get_msg_configs(get)
        if set_type not in msg_configs.keys():
            return public.return_message(-1, 0, public.lang("This send type is not supported"))
        _conf = msg_configs[set_type]
        if "data" not in _conf or not _conf["data"]:
            return public.return_message(-1, 0, public.lang("This channel is not configured, please select again."))

        from panelMessage import panelMessage
        pm = panelMessage()
        obj = pm.init_msg_module(set_type)
        if not obj:
            return public.return_message(-1, 0, public.lang("The message channel is not installed."))

        public.writeFile(login_send_type_conf, set_type)
        return public.return_message(0, 0, public.lang("successfully set"))


    # 告警日志
    def get_login_log(self, get):
        public.create_logs()
        import page
        page = page.Page()
        count = public.M('logs2').where('type=?', (u'aapanel login reminder',)).field('log,addtime').count()
        limit = 7
        info = {}
        info['count'] = count
        info['row'] = limit
        info['p'] = 1
        if hasattr(get, 'p'):
            info['p'] = int(get['p'])
        info['uri'] = get
        info['return_js'] = ''
        if hasattr(get, 'tojs'):
            info['return_js'] = get.tojs
        data = {}
        # 获取分页数据
        data['page'] = page.GetPage(info, '1,2,3,4,5,8')
        data['data'] = public.M('logs2').where('type=?', (u'aapanel login reminder',)).field('log,addtime').order(
            'id desc').limit(
            str(page.SHIFT) + ',' + str(page.ROW)).field('log,addtime').select()
        return data

    # 白名单设置
    def login_ipwhite(self, get):
        type = get.type
        if type == 'get':
            return self.get_login_ipwhite(get)
        if type == 'add':
            return self.add_login_ipwhite(get)
        if type == 'del':
            return self.del_login_ipwhite(get)
        if type == 'clear':
            return self.clear_login_ipwhite(get)

    # 查看IP白名单
    def get_login_ipwhite(self, get):
        try:
            path = '/www/server/panel/data/send_login_white.json'
            ip_white = json.loads(public.ReadFile('/www/server/panel/data/send_login_white.json'))
            if not ip_white: return public.return_message(0, 0, [])
            return public.return_message(0, 0, ip_white)
        except:
            public.WriteFile(path, '[]')
            return public.return_message(0, 0, [])

    def add_login_ipwhite(self, get):
        ip = get.ip.strip()
        try:
            path = '/www/server/panel/data/send_login_white.json'
            ip_white = json.loads(public.ReadFile('/www/server/panel/data/send_login_white.json'))
            if not ip in ip_white:
                ip_white.append(ip)
                public.WriteFile(path, json.dumps(ip_white))
            return public.return_message(0, 0, public.lang("Setup successfully!"))
        except:
            public.WriteFile(path, json.dumps([ip]))
            return public.return_message(0, 0, public.lang("Setup successfully!"))

    def del_login_ipwhite(self, get):
        ip = get.ip.strip()
        try:
            path = '/www/server/panel/data/send_login_white.json'
            ip_white = json.loads(public.ReadFile('/www/server/panel/data/send_login_white.json'))
            if ip in ip_white:
                ip_white.remove(ip)
                public.WriteFile(path, json.dumps(ip_white))
            return public.return_message(0, 0, public.lang("Successfully deleted!"))
        except:
            public.WriteFile(path, json.dumps([]))
            return public.return_message(0, 0, public.lang("Successfully deleted!"))

    def clear_login_ipwhite(self, get):
        path = '/www/server/panel/data/send_login_white.json'
        public.WriteFile(path, json.dumps([]))
        return public.return_message(0, 0, public.lang("Successfully created"))

    def get_panel_ssl_status(self, get):
        import os
        if os.path.exists(self._setup_path + '/data/ssl.pl'):
            return public.return_message(0, 0, True)
        return public.return_message(0, 0, False)

    def set_ssl_verify(self, get):
        """
        设置双向认证
        """
        sslConf = 'data/ssl_verify_data.pl'
        status = int(get.status)
        if status:
            if not os.path.exists('data/ssl.pl'): return public.return_message(-1, 0, public.lang("The panel SSL function needs to be enabled first!"))
            public.writeFile(sslConf, 'True')
        else:
            if os.path.exists(sslConf): os.remove(sslConf)
        if 'crl' in get and 'ca' in get:
            crl = 'ssl/crl.pem'
            ca = 'ssl/ca.pem'
            if get.crl:
                public.writeFile(crl, get.crl.strip())
            if get.ca:
                public.writeFile(ca, get.ca.strip())
            return public.return_message(0, 0, public.lang("The panel two-way authentication certificate has been saved!"))
        else:
            msg = 'Enable'
            if not status: msg = 'Disable'
            return public.return_message(0, 0, public.lang("Panel two-way authentication {} succeeded!", msg))

    def get_ssl_verify(self, get):
        """
        获取双向认证
        """
        result = {'status': False, 'ca': '', 'crl': ''}
        sslConf = 'data/ssl_verify_data.pl'
        if os.path.exists(sslConf): result['status'] = True

        ca = 'ssl/ca.pem'
        crl = 'ssl/crl.pem'
        if os.path.exists(crl):
            result['crl'] = public.readFile(crl)
        if os.path.exists(crl):
            result['ca'] = public.readFile(ca)
        return result

    def set_not_auth_status(self, get):
        '''
            @name 设置未认证时的响应状态
            @author hwliang<2021-12-16>
            @param status_code<int> 状态码
            @return dict
        '''
        if not 'status_code' in get:
            return public.return_message(-1, 0, public.lang("Parameter ERROR!"))

        if re.match(r"^\d+$", get.status_code):
            status_code = int(get.status_code)
            if status_code != 0:
                if status_code < 100 or status_code > 999:
                    return public.return_message(-1, 0, public.lang("Parameter ERROR!"))
        else:
            return public.return_message(-1, 0, public.lang("Parameter ERROR!"))

        public.save_config('abort', get.status_code)
        public.write_log_gettext('Panel configuration',
                                 'Set the unauthorized response status to:{}'.format(get.status_code))
        return public.return_message(0, 0, public.lang("Setup successfully!"))

    def get_not_auth_status(self):
        '''
            @name 获取未认证时的响应状态
            @author hwliang<2021-12-16>
            @return int
        '''
        try:
            status_code = int(public.read_config('abort'))
            return status_code
        except:
            return 404

    def get_request_iptype(self, get=None):
        '''
            @name 获取云端请求线路
            @author hwliang<2022-02-09>
            @return auto/ipv4/ipv6
        '''

        v4_file = '{}/data/v4.pl'.format(public.get_panel_path())
        if not os.path.exists(v4_file): return 'auto'
        iptype = public.readFile(v4_file).strip()
        if not iptype: return 'auto'
        if iptype == '-4': return 'ipv4'
        return 'ipv6'

    def get_request_type(self, get=None):
        '''
            @name 获取云端请求方式
            @author hwliang<2022-02-09>
            @return python/curl/php
        '''
        http_type_file = '{}/data/http_type.pl'.format(public.get_panel_path())
        if not os.path.exists(http_type_file): return 'python'
        http_type = public.readFile(http_type_file).strip()
        if not http_type:
            os.remove(http_type_file)
            return 'python'
        return http_type

    def get_msg_configs(self, get):
        """
        获取消息通道配置列表
        """
        cpath = 'data/msg.json'

        # cpath = '{}/data/msg.json'.format(public.get_panel_path())
        example = 'config/examples/msg.example.json'

        if not os.path.exists(cpath) and os.path.exists(example):
            import shutil
            shutil.copy(example, cpath)
        try:
            # 配置文件异常处理
            json.loads(public.readFile(cpath))
        except:
            if os.path.exists(cpath): os.remove(cpath)
        data = {}
        if os.path.exists(cpath):
            msgs = json.loads(public.readFile(cpath))

            for x in msgs:
                x['data'] = {}
                x['setup'] = False
                x['info'] = False
                key = x['name']
                try:
                    obj = public.init_msg(x['name'])
                    if obj:
                        x['setup'] = True
                        x['data'] = obj.get_config(None)
                        x['info'] = obj.get_version_info(None)
                except:
                    pass
                data[key] = x
        return public.return_message(0, 0, data)

    def get_module_template(self, get):
        """
        获取模块模板
        """
        panelPath = public.get_panel_path()
        module_name = get.module_name
        sfile = '{}/class/msg/{}.html'.format(panelPath, module_name)
        if not os.path.exists(sfile):
            return public.return_message(-1, 0, public.lang("The template file does not exist."))

        if module_name in ["sms"]:

            obj = public.init_msg(module_name)
            if obj:
                args = public.dict_obj()
                args.reload = True
                data = obj.get_config(args)
                from flask import render_template_string
                shtml = public.readFile(sfile)
                return public.return_message(0, 0, render_template_string(shtml, data=data))
        else:
            shtml = public.readFile(sfile)
            return public.return_message(0, 0, shtml)

    def set_default_channel(self, get):
        """
        设置默认消息通道
        """
        default_channel_pl = "/www/server/panel/data/default_msg_channel.pl"

        new_channel = get.channel
        default = False
        if "default" in get:
            _default = get.default
            if not _default or _default in ["false"]:
                default = False
            else:
                default = True

        ori_default_channel = ""
        if os.path.exists(default_channel_pl):
            ori_default_channel = public.readFile(ori_default_channel)

        if default:
            # 设置为默认
            from panelMessage import panelMessage
            pm = panelMessage()
            obj = pm.init_msg_module(new_channel)
            if not obj: return public.return_message(-1, 0, public.lang("Setup failed, [{}] is not installed", new_channel))

            public.writeFile(default_channel_pl, new_channel)
            if ori_default_channel:
                return public.return_message(0, 0, 'Successfully changed [{}] to [{}] panel default notification.'.format(
                    ori_default_channel, new_channel))
            else:
                return public.return_message(0, 0, public.lang("[{}] has been set as the default notification.", new_channel))
        else:
            # 取消默认设置
            if os.path.exists(default_channel_pl):
                os.remove(default_channel_pl)
            return public.return_message(0, 0, public.lang("[{}] has been removed as panel default notification.", new_channel))

    def set_msg_config(self, get):
        """
        设置消息通道配置
        """
        from panelMessage import panelMessage
        pm = panelMessage()
        obj = pm.init_msg_module(get.name)
        if not obj: return public.return_message(-1, 0, public.lang("Setup failed, [{}] is not installed", get.name))
        result =obj.set_config(get)
        status =0 if 'status' in result and result['status'] else -1
        msg = result['msg'] if 'msg' in result else public.lang("Setup failed")
        if 'status' in result: del result['status']
        return public.return_message(status, 0, msg)

    # def install_msg_module(self,get):
    #     """
    #     安装/更新消息通道模块
    #     @name 需要安装的模块名称
    #     """
    #     module_name = ""
    #     try:
    #         module_name = get.name
    #         down_url = public.get_url()
    #
    #         local_path = '{}/class/msg'.format(public.get_panel_path())
    #         if not os.path.exists(local_path): os.makedirs(local_path)
    #
    #         import panelTask
    #         task_obj = panelTask.bt_task()
    #
    #         sfile1 = '{}/{}_msg.py'.format(local_path,module_name)
    #         down_url1 = '{}/linux/panel/msg/{}_msg.py'.format(down_url,module_name)
    #
    #         sfile2 = '{}/class/msg/{}.html'.format(public.get_panel_path(),module_name)
    #         down_url2 = '{}/linux/panel/msg/{}.html'.format(down_url,module_name)
    #
    #         public.WriteLog('Install module', 'Install [{}]'.format(module_name))
    #         task_obj.create_task('Download file', 1, down_url1, sfile1)
    #         task_obj.create_task('Download file', 1, down_url2, sfile2)
    #
    #         timeout = 0
    #         is_install = False
    #         while timeout < 5:
    #             try:
    #                 if os.path.exists(sfile1) and os.path.exists(sfile2):
    #                     msg_obj = public.init_msg(module_name)
    #                     if  msg_obj and msg_obj.get_version_info:
    #                         is_install = True
    #                         break
    #             except: pass
    #             time.sleep(0.1)
    #             is_install = True
    #
    #         if not is_install:
    #             return public.return_message(-1, 0, public.lang("Failed to install [{}] module. Please check the network.", module_name))
    #
    #         public.set_module_logs('msg_push', 'install_module', 1)
    #         return public.return_message(0, 0, public.lang("[{}] Module is installed successfully.", module_name))
    #     except:
    #         pass
    #     return public.return_message(-1, 0, public.lang("[{}] Module installation failed.", module_name))

    def install_msg_module(self, get):
        """
        aapanel 不与面板相同，不删除通道模块
        安装/更新消息通道模块
        @name 需要安装的模块名称
        """
        module_name = ""
        try:
            module_name = get.name

            local_path = '{}/class/msg'.format(public.get_panel_path())
            if not os.path.exists(local_path): os.makedirs(local_path)

            sfile1 = '{}/{}_msg.py'.format(local_path, module_name)

            if os.path.exists(sfile1):
                return public.return_message(0, 0, public.lang("[{}] Module is installed successfully.", module_name))

        except:
            return public.return_message(-1, 0, public.lang("[{}] Module installation failed.", module_name))

    # def uninstall_msg_module(self,get):
    #     """
    #     卸载消息通道模块
    #     @name 需要卸载的模块名称
    #     @is_del 是否需要删除配置文件
    #     """
    #     module_name = get.name
    #     obj = public.init_msg(module_name)
    #     if 'is_del' in get:
    #         try:
    #             obj.uninstall()
    #         except:pass
    #
    #     sfile = '{}/class/msg/{}_msg.py'.format(public.get_panel_path(),module_name)
    #     if os.path.exists(sfile): os.remove(sfile)
    #
    #     # public.print_log(sfile)
    #     default_channel_pl = "{}/data/default_msg_channel.pl".format(public.get_panel_path())
    #     default_channel = public.readFile(default_channel_pl)
    #     if default_channel and default_channel == module_name:
    #         os.remove(default_channel_pl)
    #     return public.return_message(0, 0, public.lang("[{}] Module uninstallation succeeds", module_name))

    def uninstall_msg_module(self, get):
        """
        aapanel 不与面板相同，不删除通道模块，只删除配置文件
        @module_name 是删除配置文件
        """
        module_name = get.name

        # sfile = '{}/class/msg/{}_msg.py'.format(public.get_panel_path(),module_name)
        # if os.path.exists(sfile): os.remove(sfile)

        if module_name in ["dingding", "feishu", "weixin"]:
            msg_conf_file = "{{}}/data/{}.json".format(module_name).format(public.get_panel_path())
            if os.path.exists(msg_conf_file): os.remove(msg_conf_file)
        elif module_name == "mail":
            for conf_file in ["stmp_mail", "mail_list"]:
                msg_conf_file = "{}/data/{}.json".format(public.get_panel_path(), conf_file)
                if os.path.exists(msg_conf_file): os.remove(msg_conf_file)
        elif module_name == "tg":
            msg_conf_file = "{}/data/tg_bot.json".format(public.get_panel_path())
            if os.path.exists(msg_conf_file): os.remove(msg_conf_file)

        # public.print_log(sfile)
        default_channel_pl = "{}/data/default_msg_channel.pl".format(public.get_panel_path())
        default_channel = public.readFile(default_channel_pl)
        if default_channel and default_channel == module_name:
            os.remove(default_channel_pl)
        return public.return_message(0, 0, public.lang("[{}] Module uninstallation succeeds", module_name))

    def get_msg_fun(self, get):
        """
        @获取消息模块指定方法
        @auther: cjxin
        @date: 2022-08-16
        @param: get.module_name 消息模块名称(如：sms,weixin,dingding)
        @param: get.fun_name 消息模块方法名称(如：send_sms,push_msg)
        """
        module_name = get.module_name
        fun_name = get.fun_name

        m_objs = public.init_msg(module_name)
        if not m_objs: return public.return_message(-1, 0, public.lang("Setup failed, [{}] is not installed", module_name))

        return getattr(m_objs, fun_name)(get)

    def get_msg_configs_by(self, get):
        """
        @name 获取单独消息通道配置
        @auther: cjxin
        @date: 2022-08-16
        @param: get.name 消息模块名称(如：sms,weixin,dingding)
        """
        name = get.name
        res = {}
        res['data'] = {}
        res['setup'] = False
        res['info'] = False
        try:
            obj = public.init_msg(name)
            if obj:
                res['setup'] = True
                res['data'] = obj.get_config(None)
                res['info'] = obj.get_version_info(None);
        except:
            pass
        return res

    def get_msg_push_list(self, get):
        """
        @name 获取消息通道配置列表
        @auther: cjxin
        @date: 2022-08-16
        """
        cpath = 'data/msg.json'
        try:
            if 'force' in get or not os.path.exists(cpath):
                if not 'download_url' in session: session['download_url'] = public.get_url()
                public.downloadFile('{}/linux/panel/msg/msg.json'.format(session['download_url']), cpath)
        except:
            pass

        data = {}
        if os.path.exists(cpath):
            msgs = json.loads(public.readFile(cpath))
            for x in msgs:
                x['setup'] = False
                x['info'] = False
                key = x['name']
                try:
                    obj = public.init_msg(x['name'])
                    if obj:
                        x['setup'] = True
                        x['info'] = obj.get_version_info(None)
                except:
                    print(public.get_error_info())
                    pass
                data[key] = x
        return data

    # 检查是否提交过问卷
    def check_nps(self, get):
        # 校验参数
        try:
            get.validate([
                Param('product_type').Integer(),

            ], [
                public.validate.trim_filter(),
            ])
        except Exception as ex:
            public.print_log("error info: {}".format(ex))
            return public.return_message(-1, 0, str(ex))
        if 'product_type' not in get:
            return public.return_message(-1, 0, public.lang("Parameter error"))
        ikey = 'check_nps'
        result = cache.get(ikey)
        if result:
            return public.return_message(0, 0, result)

        url = '{}/api/panel/nps/check'.format(public.OfficialApiBase())

        data = {
            'product_type': get.get('product_type', 1),
            # 'server_id':  user_info['server_id'],
        }

        try:
            user_info = json.loads(public.ReadFile("{}/data/userInfo.json".format(public.get_panel_path())))
            data['server_id'] = user_info['server_id']

        except:
            pass
        res = public.httpPost(url, data)
        try:
            res = json.loads(res)
        except:
            pass

        # 连不上官网时使用默认数据
        if not isinstance(res, dict):
            res = {
                "nonce": 0,
                "success": False,
                "res": False
            }

        # 判断运行天数
        safe_day = 0
        cur_timestamp = int(time.time())
        # if os.path.exists("data/%s_nps_time.pl" % software_name):
        if os.path.exists("/www/server/panel/data/panel_nps_time.pl"):
            try:
                # nps_time = float(public.ReadFile("/www/server/panel/data/panel_nps_time.pl"))
                nps_time = float(public.ReadFile("data/panel_nps_time.pl"))
                safe_day = int((cur_timestamp - nps_time) / 86400)

            except:
                public.WriteFile("data/panel_nps_time.pl", "%s" % cur_timestamp)
        else:
            public.WriteFile("data/panel_nps_time.pl", "%s" % cur_timestamp)

        datas = {'nonce': res.get('nonce', 0),
                 'success': res.get('success', False),
                 'res': {
                     'safe_day': safe_day,
                     'is_submit': res.get('res', False)
                 }}

        cache.set(ikey, datas, 3600)
        # if res['success']:
        # return public.return_message(0, 0, public.lang("Questionnaire has been submitted"))

        # return public.return_message(-1, 0, public.lang("No questionnaire has been submitted"))
        return public.return_message(0, 0, datas)

    def get_nps_new(self, get):
        """
        获取问卷
        """
        # 校验参数
        try:
            get.validate([
                Param('product_type').Integer(),
            ], [
                public.validate.trim_filter(),
            ])
        except Exception as ex:
            public.print_log("error info: {}".format(ex))
            return public.return_message(-1, 0, str(ex))

        try:
            # 官网接口 需替换
            url = '{}/api/panel/nps/questions'.format(public.OfficialApiBase())
            data = {
                'product_type': get.get('product_type', 1),
                # 'action': "list",
                # 'version': get.get('version', -1)
            }
            # request发送post请求并指定form_data参数
            res = public.httpPost(url, data)
            # public.print_log("获取问卷@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@   {}".format(res))
            try:
                res = json.loads(res)
            except:
                pass
            return public.return_message(0, 0, res)

        except:
            return public.return_message(-1, 0, public.lang("Failed to obtain questionnaire"))

    def write_nps_new(self, get):
        '''
            @name nps 提交
            @param rate 评分
            @param feedback 反馈内容
        '''
        # 校验参数
        try:
            get.validate([
                Param('questions').String(),
                Param('product_type').Integer(),
                Param('rate').Integer(),
                # Param('submit_entry').Integer(),
            ], [
                public.validate.trim_filter(),
            ])
        except Exception as ex:
            public.print_log("error info: {}".format(ex))
            return public.return_message(-1, 0, str(ex))

        if 'product_type' not in get:
            return public.return_message(-1, 0, public.lang("Parameter error"))
        if 'submit_entry' in get:
            #判断submit_entry值是否在501-518之间
            submit_entry=int(get.get('submit_entry', 518))
            if submit_entry < 501 or submit_entry > 518:
                return public.return_message(-1, 0, public.lang("Parameter error"))

        # if 'questions' not in get:
        #     public.returnMsg(False, '参数错误')
        if 'rate' not in get:
            return public.return_message(-1, 0, public.lang("Parameter error"))

        # try:
        # if not hasattr(get, 'software_name'):
        #     public.returnMsg(False, '参数错误')

        # software_name = get['software_name']
        # public.WriteFile("data/{}_nps.pl".format(software_name), "1")

        data = {
            # 'action': "submit",
            # 'uid': user_info['uid'],  # 用户ID
            # 'access_key': user_info['access_key'],  # 用户密钥
            # 'is_paid': get['is_paid'],  # 是否付费
            # 'phone_back': get['back_phone'],  # 是否回访
            # 'feedback': get['feedback']  # 反馈内容
            # 'reason_tags': get['reason_tags'],  # 问题标签
            'submit_entry': get.get('submit_entry', 518),  # 提交入口
            'rate': get.get('rate', 1),  # 评分  1~10
            'product_type': get.get('product_type', 1),  # 产品类型
            # 'server_id': user_info['server_id'],  # 服务器ID
            'questions': get['questions'],  # 问题列表
            'panel_version': public.version(),  # 面板版本

        }
        url_headers = {
            # "authorization": "bt {}".format(user_info['token'])
        }

        try:
            user_info = json.loads(public.ReadFile("{}/data/userInfo.json".format(public.get_panel_path())))
            data['server_id'] = user_info['server_id']
            url_headers = {
                "authorization": "bt {}".format(user_info['token'])
            }
        except:
            pass

        url = '{}/api/panel/nps/submit'.format(public.OfficialApiBase())
        if not hasattr(get, 'questions'):
            return public.return_message(-1, 0, public.lang("questions Parameter error"))
        else:
            try:
                content = json.loads(get.questions)
                for _, i in content.items():
                    if len(i) > 512:
                        # public.ExecShell("rm -f data/{}_nps.pl".format(software_name))
                        return public.return_message(-1, 0, public.lang("The submitted text is too long, please adjust and resubmit (MAX: 512)"))
            except:
                return public.return_message(-1, 0, public.lang("questions Parameter error"))
        # if not hasattr(get, 'product_type'):
        #     return public.return_message(-1, 0, public.lang("参数错误"))
        # if not hasattr(get, 'rate'):
        #     return public.return_message(-1, 0, public.lang("参数错误"))
        # if not hasattr(get, 'reason_tags'):
        #     get['reason_tags'] = "1"
        # if not hasattr(get, 'is_paid'):
        #     get['is_paid'] = 0  # 是否付费
        # if not hasattr(get, 'phone_back'):
        #     get.phone_back = 0
        # if not hasattr(get, 'phone_back'):
        #     get.feedback = ""

        res = public.httpPost(url, data=data, headers=url_headers)
        try:
            res = json.loads(res)
        except:
            pass

        # 连不上官网时使用默认数据
        if not isinstance(res, dict):
            res = {
                "nonce": 0,
                "success": False,
                "res": "The submission failed, please check to connect to the node"
            }

        if res['success']:
            return public.return_message(0, 0, public.lang("Submitted successfully"))

        return public.return_message(-1, 0, res['res'] if 'res' in res else "The submission failed, please check to connect to the node")

    # Get all translations
    def get_translations(self, args: public.dict_obj):
        from BTPanel import load_translations
        return load_translations()
    def get_login_translations(self, args: public.dict_obj):
        from BTPanel import load_translations
        return load_login_translations()
    # -------------------------------------------------------- 语言包相关接口--------------------------------------------------------------------------------------------------
    # 获取语言选项
    def get_language(self):

        settings = '{}/BTPanel/languages/settings.json'.format(public.get_panel_path())
        custom = '{}/BTPanel/static/vite/lang/my-MY'.format(public.get_panel_path())
        default_data = public.default_languages_config()

        file_content = public.readFile(settings)
        if not file_content:
            public.writeFile(settings, json.dumps(default_data))
            data = default_data
        else:
            try:
                data = json.loads(file_content)
            except json.JSONDecodeError:
                public.writeFile(settings, json.dumps(default_data))
                data = default_data

        setlang = "/www/server/panel/BTPanel/languages/language.pl"

        if os.path.exists(setlang):
            olang = public.ReadFile(setlang)
            if olang:
                data['default'] = olang

        if os.path.exists(custom):
            data['languages'].append({
                "name": "my",
                "google": "my",
                "title": "Custom",
                "cn": "自定义"
            })

        # public.print_log(data)

        return data

    # 设置语言偏好
    def set_language(self, args):

        name = args.name
        public.setLang(name)
        path = "/www/server/panel/BTPanel/languages/language.pl"
        public.WriteFile(path, name)
        public.set_module_logs('language', 'set_language', 1)
        # 前端目录更改(重启面板)
        public.restart_panel()
        return public.return_message(0, 0, 'The setup was successful')

    # --------------------------------------------- 设置ua限制------------------------------------------

    def set_ua(self, get):
        try:
            ua_file = '/www/server/panel/class/limitua.json'
            if os.path.exists(ua_file):
                with open(ua_file, 'r') as f:
                    data = json.load(f)
                # 检查 ua_list 是否为空，如果为空则设置 id 为 1，否则计算最大 id 并加 1
                if data['ua_list']:
                    id = max(ua['id'] for ua in data['ua_list']) + 1
                else:
                    id = 1
            else:
                id = 1  # 如果文件不存在，从1开始
                data = {
                    "ua_list": [],
                    "status": "0"
                }

            current_ua = {"id": id, "name": request.user_agent.string}  # 当前登录用户的UA
            if not data['ua_list'] or data['ua_list'][0]['name'] != current_ua['name']:  # 如果列表为空或者当前UA与列表中的第一个UA不同，则替换
                data['ua_list'].insert(0, current_ua)  # 将当前UA插入到列表的第一个位置

            ua_list = [{"id": id + i + 1, "name": self.process_ua(ua)} for i, ua in enumerate(get.ua_list.split('\n'))
                       if ua.strip()]  # 将字符串转换为列表并添加到ua_list，忽略空的UA
            added_uas = []  # 保存已经添加成功的UA
            for ua in ua_list:
                if ua['name'] not in [ua['name'] for ua in data['ua_list']]:  # 如果UA尚未存在于列表中，则添加
                    data['ua_list'].append(ua)
                    added_uas.append(ua['name'])

            public.writeFile('/www/server/panel/class/limitua.json', json.dumps(data))  # 将数据保存为JSON文件
            return public.return_message(0, 0,  public.lang("successfully set"))
        except Exception as e:
            return public.return_message(-1, 0,  public.lang("Setup failed! {}", str(e)))

    def process_ua(self, ua):
        # 将括号内的逗号替换为其他字符
        return re.sub(r'(\(.*?\))', lambda x: x.group(1).replace(',', ';'), ua)

    def get_limit_ua(self, get):
        try:
            ua_file = '/www/server/panel/class/limitua.json'
            if not os.path.exists(ua_file):
                return public.return_message(0, 0, {"ua_list": [], "status": '0'})
            with open(ua_file, 'r') as f:
                data = json.load(f)  # 读取JSON文件
            ua_list = data.get('ua_list', [])  # 获取ua_list字段的值
            if ua_list:
                ua_list.pop(0)  # 删除第一行的数据
            status = data.get('status', '0')  # 获取status字段的值
            return public.return_message(0, 0, {"ua_list": ua_list, "status": status})
        except Exception as e:
            return public.return_message(-1, 0,  str(e))

    # 修改UA数据
    def modify_ua(self, get):
        try:
            ua_file = '/www/server/panel/class/limitua.json'
            if not os.path.exists(ua_file):
                # 文件不存在，创建文件并初始化基本结构
                data = {'ua_list': [], 'status': False}
                with open(ua_file, 'w') as f:
                    json.dump(data, f)
            else:

                with open(ua_file, 'r') as f:
                    data = json.load(f)
            # 如果get中包含id和new_name，那么修改对应的UA
            if 'id' in get and 'new_name' in get:

                for ua in data['ua_list']:
                    if ua['id'] == int(get.id):
                        ua['name'] = get.new_name
            # 如果get中包含status，那么修改status的值
            if 'status' in get:
                data['status'] = get.status
                if len(data['ua_list']) == 1 and data['status'] == "1":
                    return public.return_message(-1, 0, "请先添加ua后再开启！")
            with open(ua_file, 'w') as f:
                json.dump(data, f)
            return public.return_message(0, 0, "修改成功！")
        except Exception as e:
            return public.return_message(-1, 0, "修改失败！" + str(e))

    # 删除UA数据
    def delete_ua(self, get):
        try:
            ua_file = '/www/server/panel/class/limitua.json'
            if not os.path.exists(ua_file):
                # 文件不存在，创建文件并初始化基本结构
                data = {'ua_list': [], 'status': False}
                with open(ua_file, 'w') as f:
                    json.dump(data, f)
            else:
                with open(ua_file, 'r') as f:
                    data = json.load(f)
                data['ua_list'] = [ua for ua in data['ua_list'] if ua['id'] != int(get.id)]
                with open(ua_file, 'w') as f:
                    json.dump(data, f)
                return public.return_message(0, 0,  "删除成功！")
        except Exception as e:
            return public.return_message(-1, 0, "删除失败！" + str(e))

    # 设置CDN代理状态
    def set_cdn_status(self, get):
        from flask import current_app
        try:
            cdn_switch = int(get.get('cdn_switch', 0))
            config_path = '/www/server/panel/config/cdn.conf'
            config_dir = os.path.dirname(config_path)

            # 确保配置目录存在
            if not os.path.exists(config_dir):
                os.makedirs(config_dir)

            # 写入配置文件
            with open(config_path, 'w') as f:
                if cdn_switch == 1:
                    current_app.config['CDN_PROXY'] = True
                    f.write('CDN_PROXY=True')
                elif cdn_switch == 0:
                    current_app.config['CDN_PROXY'] = False
                    f.write('CDN_PROXY=False')
            return public.success_v2(f"CDN proxy status updated successfully")
        except Exception as e:
            return public.fail_v2(str(e))

    # 设置自动获取图标状态
    def set_auto_favicon(self, get):
        """
            @name 设置自动获取图标状态
            1为开启，0为关闭
            关闭创建状态文件，开启删除状态文件
        """
        status = get.get('status', '1') # 默认开
        config_path = '/www/server/panel/config/auto_favicon.conf'

        if status == '1':
            if os.path.exists(config_path):
                os.remove(config_path)
        elif status == '0':
            if not os.path.exists(config_path):
                public.writeFile(config_path, '0')

                # 尝试清除已有的图标缓存
                favicon_cache_dir = '/www/server/panel/data/site_favs'
                if os.path.exists(favicon_cache_dir):
                    for file in os.listdir(favicon_cache_dir):
                        file_path = os.path.join(favicon_cache_dir, file)
                        if os.path.isfile(file_path) and file.endswith(('.ico', '.b64')):
                            try:
                                os.remove(file_path)
                            except:
                                pass

        return public.success_v2(f"Auto favicon status updated successfully")

    # 设置主题切换
    def set_theme(self, args):
        name = args.name
        path = "/www/server/panel/data/theme.pl"
        public.WriteFile(path, name)
        public.set_module_logs('theme', 'set_theme', 1)
        # # 重启面板
        # public.restart_panel()
        return public.return_message(0, 0, 'The setup was successful')

    # 设置面板界面配置
    def set_panel_asset(self, get):
        if cache:
            cache.delete("panel_asset_config")

        from BTPanel import PANEL_DEFAULT_ASSET
        # 定义允许的配置字段映射
        allowed_fields = set(PANEL_DEFAULT_ASSET.keys())
        try:
            # 收集请求中的有效配置数据
            new_data = {
                key: getattr(get, key) for key in allowed_fields if hasattr(get, key)
            }
            # 读取现有配置（如果存在）
            if os.path.exists(self.__panel_asset_config):
                existing_data = json.loads(public.readFile(self.__panel_asset_config))
                existing_data.update(new_data)
                updated_data = json.dumps(existing_data, indent=2)
            else:
                updated_data = json.dumps(new_data, indent=2)
            # 存储配置
            public.writeFile(self.__panel_asset_config, updated_data)
            return public.success_v2(public.lang("Set Asset Successfully!"))

        except Exception as e:
            return public.fail_v2(public.lang("Set Asset Failed {}", e))


    # 获取面板界面配置
    def get_panel_asset(self, get=None):
        try:
            cache_data = cache.get("panel_asset_config")
            if cache_data:
                return public.success_v2(cache_data)
        except Exception as e:
            public.print_log(f"get_panel_asset cache error: {e}")

        try:
            from BTPanel import PANEL_DEFAULT_ASSET
            # 合法的字段和默认值
            default_values = {
                k: v for k, v in PANEL_DEFAULT_ASSET.items()
            }
        except:
            default_values = {
                'favicon': '/static/favicon.ico',  # 默认网站favicon图标
                'show_login_logo': True,  # 默认不显示登录logo
                'show_login_bg_images': False,  # 默认不显示登录背景图片
                'login_logo': '/static/icons/logo-green.svg',  # 默认登录logo图片
                'login_bg_images': '',  # 默认登录背景图片
                'login_bg_images_opacity': 100,  # 默认登录背景图片透明度
                'show_main_bg_images': True,  # 默认不显示主界面背景图
                'main_bg_images': '/static/icons/main_bg.png',  # 主界面背景图
                'main_bg_images_opacity': 100,  # 主界面背景图透明度
                'main_content_opacity': 100,  # 主界面内容透明度
                'main_shadow_color': '#000000',  # 主界面阴影颜色
                'main_shadow_opacity': 5,  # 主界面阴影透明度
                'menu_logo': '/static/icons/menu_logo.png',  # 菜单栏顶部logo图标
                'menu_bg_opacity': 100,  # 默认侧边栏背景透明度
                'theme_color': '#3c444d',  # 默认主色
                'theme_name': 'default',  # 默认主题名称
                'home_state_font_size': 24,  # 首页概览字体大小
                'main_bg_images_dark': '/static/icons/main_bg_dark.png',  # 这个是用来搞黑暗模式的
            }
        # 旧字段与新字段的映射
        old_to_new = {
            'bg_images': 'login_bg_images',
            'bg_images_opacity': 'login_bg_images_opacity',
            'tab_logo': 'menu_logo',
            'main_opacity': 'main_content_opacity',
            'menu_theme_color': 'theme_color',
            'menu_theme': 'theme_name',
            'show_main_bg_image': 'show_main_bg_images',
            'main_bg_image': 'main_bg_images',
            'main_bg_image_opacity': 'main_bg_images_opacity',
        }
        if not os.path.exists(self.__panel_asset_config):
            return public.success_v2(default_values)

        # 旧配置字段替换成新key
        path_data = json.loads(public.readFile(self.__panel_asset_config))

        for old_key, new_key in old_to_new.items():
            if old_key in path_data:
                path_data[new_key] = path_data.pop(old_key)

        # 更新配置文件
        public.writeFile(self.__panel_asset_config, json.dumps(path_data, indent=2))
        try:
            result = {}
            for key, default in default_values.items():
                value = path_data.get(key, default)
                # 处理特殊情况
                if key in [
                    "login_logo", "login_bg_images", "main_bg_images", "menu_logo"
                ]:
                    # 允许空字符串，但不允许 "undefined"
                    if str(value).strip() == "undefined":
                        value = default
                if key in [
                    "login_bg_images_opacity",
                    "main_bg_images_opacity",
                    "main_content_opacity",
                    "menu_bg_opacity",
                    "main_shadow_opacity",
                    "home_state_font_size"
                ]:
                    # 转换为整数
                    try:
                        value = int(value)
                    except (ValueError, TypeError):
                        value = default

                result[key] = value
                # 将字符串的true和false转换为布尔值
                if isinstance(value, str):
                    if value.lower() == 'true':
                        result[key] = True
                    elif value.lower() == 'false':
                        result[key] = False
            if cache:
                cache.set("panel_asset_config", result)
            return public.success_v2(result)
        except:
            return public.success_v2(default_values)
