#coding: utf-8
#-------------------------------------------------------------------
# aaPanel
#-------------------------------------------------------------------
# Copyright (c) 2015-2017 aaPanel(www.aapanel.com) All rights reserved.
#-------------------------------------------------------------------
# Author: lkqiang <lkq@aapanel.com>
#-------------------------------------------------------------------
# SSH 安全类
#------------------------------
import public,os,re,send_mail,json
from datetime import datetime
from public.validate import Param


class ssh_security:
    __type_list = ['ed25519','ecdsa','rsa', 'dsa']
    __key_type_file = '{}/data/ssh_key_type.pl'.format(public.get_panel_path())
    __key_files = ['/root/.ssh/id_ed25519','/root/.ssh/id_ecdsa','/root/.ssh/id_rsa','/root/.ssh/id_rsa_bt']
    __type_files = {
        "ed25519": "/root/.ssh/id_ed25519",
        "ecdsa": "/root/.ssh/id_ecdsa",
        "rsa": "/root/.ssh/id_rsa",
        "dsa": "/root/.ssh/id_dsa"
    }
    open_ssh_login = public.get_panel_path() + '/data/open_ssh_login.pl'

    __SSH_CONFIG='/etc/ssh/sshd_config'
    __ip_data = None
    __ClIENT_IP='/www/server/panel/data/host_login_ip.json'
    __pyenv = 'python'
    __REPAIR={"1":{"id":1,
                   "type":"file",
                   "harm":"High",
                   "repaired":"1",
                   "level":"3",
                   "name":"Make sure SSH MaxAuthTries is set between 3-6",
                   "file":"/etc/ssh/sshd_config",
                   "Suggestions":"Remove the MaxAuthTries comment symbol # in /etc/ssh/sshd_config, set the maximum number of failed password attempts 3-6 recommended 4",
                   "repair":"MaxAuthTries 4",
                   "rule":[{"re":"\nMaxAuthTries\\s*(\\d+)","check":{"type":"number","max":7,"min":3}}],
                   "repair_loophole":[{"re":"\n?#?MaxAuthTries\\s*(\\d+)","check":"\nMaxAuthTries 4"}]},
              "2":{"id":2,
                   "repaired":"1",
                   "type":"file",
                   "harm":"High",
                   "level":"3",
                   "name":"SSHD Mandatory use of V2 security protocol",
                   "file":"/etc/ssh/sshd_config",
                   "Suggestions":"Set parameters in the /etc/ssh/sshd_config file as follows",
                   "repair":"Protocol 2",
                   "rule":[{"re":"\nProtocol\\s*(\\d+)",
                            "check":{"type":"number","max":3,"min":1}}],
                   "repair_loophole":[{"re":"\n?#?Protocol\\s*(\\d+)","check":"\nProtocol 2"}]},
              "3":{"id":3,
                   "repaired":"1",
                   "type":"file",
                   "harm":"High",
                   "level":"3",
                   "name":"Set SSH idle exit time",
                   "file":"/etc/ssh/sshd_config",
                   "Suggestions":"Set ClientAliveInterval to 300 to 900 in /etc/ssh/sshd_config, which is 5-15 minutes, and set ClientAliveCountMax to 0-3",
                   "repair":"ClientAliveInterval 600  ClientAliveCountMax 2",
                   "rule":[{"re":"\nClientAliveInterval\\s*(\\d+)","check":{"type":"number","max":900,"min":300}}],
                   "repair_loophole":[{"re":"\n?#?ClientAliveInterval\\s*(\\d+)","check":"\nClientAliveInterval 600"}]},
              "4":{"id":4,
                   "repaired":"1",
                   "type":"file",
                   "harm":"High",
                   "level":"3",
                   "name":"Make sure SSH LogLevel is set to INFO",
                   "file":"/etc/ssh/sshd_config",
                   "Suggestions":"Set parameters in the /etc/ssh/sshd_config file as follows (uncomment)",
                   "repair":"LogLevel INFO",
                   "rule":[{"re":"\nLogLevel\\s*(\\w+)","check":{"type":"string","value":["INFO"]}}],
                   "repair_loophole":[{"re":"\n?#?LogLevel\\s*(\\w+)","check":"\nLogLevel INFO"}]},
              "5":{"id":5,
                   "repaired":"1",
                   "type":"file",
                   "harm":"High",
                   "level":"3",
                   "name":"Disable SSH users with empty passwords from logging in",
                   "file":"/etc/ssh/sshd_config",
                   "Suggestions":"Configure PermitEmptyPasswords to no in /etc/ssh/sshd_config",
                   "repair":"PermitEmptyPasswords no",
                   "rule":[{"re":"\nPermitEmptyPasswords\\s*(\\w+)","check":{"type":"string","value":["no"]}}],
                   "repair_loophole":[{"re":"\n?#?PermitEmptyPasswords\\s*(\\w+)","check":"\nPermitEmptyPasswords no"}]},
              "6":{"id":6,
                   "repaired":"1",
                   "type":"file",
                   "name":"SSH uses the default port 22",
                   "harm":"High",
                   "level":"3",
                   "file":"/etc/ssh/sshd_config",
                   "Suggestions":"Set Port to 6000 to 65535 in / etc / ssh / sshd_config",
                   "repair":"Port 60151",
                   "rule":[{"re":"Port\\s*(\\d+)","check":{"type":"number","max":65535,"min":22}}],
                   "repair_loophole":[{"re":"\n?#?Port\\s*(\\d+)","check":"\nPort 65531"}]}}
    __root_login_types = {'yes':'yes - keys and passwords','no':'no - no login','without-password':'without-password - only key login','forced-commands-only':'forced-commands-only - can only execute commands'}


    def __init__(self):
        if not public.M('sqlite_master').where('type=? AND name=?', ('table', 'ssh_login_record')).count():
            public.M('').execute('''CREATE TABLE ssh_login_record (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                addr TEXT,
                server_ip TEXT,
                user_agent TEXT,
                ssh_user TEXT,
                login_time INTEGER DEFAULT 0,
                close_time INTEGER DEFAULT 0,
                video_addr TEXT);''')
            public.M('').execute('CREATE INDEX ssh_login_record ON ssh_login_record (addr);')

        if not os.path.exists(self.__ClIENT_IP):
            public.WriteFile(self.__ClIENT_IP,json.dumps([]))
        self.__mail=send_mail.send_mail()
        self.__mail_config=self.__mail.get_settings()
        self._check_pyenv()
        try:
            self.__ip_data = json.loads(public.ReadFile(self.__ClIENT_IP))
        except:
            self.__ip_data=[]

    def _check_pyenv(self):
        if os.path.exists('/www/server/panel/pyenv'):
            self.__pyenv = 'btpython'

    def get_ssh_key_type(self):
        '''
        获取ssh密钥类型
        @author hwliang
        :return:
        '''
        default_type = 'rsa'
        if not os.path.exists(self.__key_type_file):
            return default_type
        new_type = public.ReadFile(self.__key_type_file)
        if new_type in self.__type_list:
            return new_type
        return default_type


    def return_python(self):
        if os.path.exists('/www/server/panel/pyenv/bin/python'):return '/www/server/panel/pyenv/bin/python'
        if os.path.exists('/usr/bin/python'):return '/usr/bin/python'
        if os.path.exists('/usr/bin/python3'):return '/usr/bin/python3'
        return 'python'


    def return_profile(self):
        if os.path.exists('/root/.bash_profile'): return '/root/.bash_profile'
        if os.path.exists('/etc/profile'): return '/etc/profile'
        fd = open('/root/.bash_profil', mode="w", encoding="utf-8")
        fd.close()
        return '/root/.bash_profil'

    def return_bashrc(self):
        if os.path.exists('/root/.bashrc'):return '/root/.bashrc'
        if os.path.exists('/etc/bashrc'):return '/etc/bashrc'
        if os.path.exists('/etc/bash.bashrc'):return '/etc/bash.bashrc'
        fd = open('/root/.bashrc', mode="w", encoding="utf-8")
        fd.close()
        return '/root/.bashrc'


    def check_files(self):
        try:
            json.loads(public.ReadFile(self.__ClIENT_IP))
        except:
            public.WriteFile(self.__ClIENT_IP, json.dumps([]))

    def get_ssh_port(self):
        conf = public.readFile(self.__SSH_CONFIG)
        if not conf: conf = ''
        rep = r"#*Port\s+([0-9]+)\s*\n"
        tmp1 = re.search(rep,conf)
        port = '22'
        if tmp1:
            port = tmp1.groups(0)[0]
        return port

    # 主判断函数
    def check_san_baseline(self, base_json):
        if base_json['type'] == 'file':
            if 'check_file' in base_json:
                if not os.path.exists(base_json['check_file']):
                    return False
            else:
                if os.path.exists(base_json['file']):
                    ret = public.ReadFile(base_json['file'])
                    for i in base_json['rule']:
                        valuse = re.findall(i['re'], ret)
                        if i['check']['type'] == 'number':
                            if not valuse: return False
                            if not valuse[0]: return False
                            valuse = int(valuse[0])
                            if valuse > i['check']['min'] and valuse < i['check']['max']:
                                return True
                            else:
                                return False
                        elif i['check']['type'] == 'string':
                            if not valuse: return False
                            if not valuse[0]: return False
                            valuse = valuse[0]
                            if valuse in i['check']['value']:
                                return True
                            else:
                                return False
                return True

    def san_ssh_security(self,get):
        data={"num":100,"result":[]}
        result = []
        ret = self.check_san_baseline(self.__REPAIR['1'])
        if not ret: result.append(self.__REPAIR['1'])
        ret = self.check_san_baseline(self.__REPAIR['2'])
        if not ret: result.append(self.__REPAIR['2'])
        ret = self.check_san_baseline(self.__REPAIR['3'])
        if not ret: result.append(self.__REPAIR['3'])
        ret = self.check_san_baseline(self.__REPAIR['4'])
        if not ret: result.append(self.__REPAIR['4'])
        ret = self.check_san_baseline(self.__REPAIR['5'])
        if not ret: result.append(self.__REPAIR['5'])
        ret = self.check_san_baseline(self.__REPAIR['6'])
        if not ret: result.append(self.__REPAIR['6'])
        data["result"]=result
        if len(result)>=1:
            data['num']=data['num']-(len(result)*10)
        return data

    ################## SSH 登陆报警设置 ####################################
    def send_mail_data(self, title, body, login_ip, type=None):
        # public.print_log(">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>")
        # public.print_log((title, body, login_ip))
        from panel_msg.collector import SitePushMsgCollect
        msg = SitePushMsgCollect.ssh_login(body)
        push_data = {
            "login_ip": "" if body.find("backdoor user") != -1 else ( login_ip if login_ip != "" else "unknown ip"),
            "msg_list": ['>Send content:' + body]
        }
        # public.print_log(push_data)
        try:
            import sys
            if "/www/server/panel" not in sys.path:
                sys.path.insert(0, "/www/server/panel")

            from mod.base.push_mod import push_by_task_keyword
            # public.print_log(push_data)
            res = push_by_task_keyword("ssh_login", "ssh_login", push_data=push_data)
            if res:
                return
        except:
            pass

        try:
            login_send_type_conf = "/www/server/panel/data/ssh_send_type.pl"
            if not os.path.exists(login_send_type_conf):
                return
                # login_type = "mail"
            else:
                login_type = public.readFile(login_send_type_conf).strip()
                if not login_type:
                    login_type = "mail"
            object = public.init_msg(login_type.strip())
            if not object:
                return False
            if login_type=="mail":
                data={}
                data['title'] = title
                data['msg'] = body
                object.push_data(data)
            elif login_type=="wx_account":
                from push.site_push import ToWechatAccountMsg
                if body.find("backdoor user") != -1:
                    msg = ToWechatAccountMsg.ssh_login("")
                else:
                    msg = ToWechatAccountMsg.ssh_login(login_ip if login_ip != "" else "unknown ip")
                object.send_msg(msg)
            else:
                msg = public.get_push_info("SSH logon alarm", ['>Send content:' + body])
                msg['push_type'] = "SSH logon alarm"
                object.push_data(msg)
        except:
            pass

    #检测非UID为0的账户
    def check_user(self):
        ret = []
        cfile = '/etc/passwd'
        if os.path.exists(cfile):
            f = open(cfile, 'r')
            for i in f:
                i = i.strip().split(":")
                if i[2] == '0' and i[3] == '0':
                    if i[0] == 'root': continue
                    ret.append(i[0])
        if ret:
            data=''.join(ret)
            public.run_thread(self.send_mail_data,args=(public.GetLocalIp()+' There is a backdoor user in the server',public.GetLocalIp()+' There is a backdoor user in the server '+data+' please check/etc/passwd',))
            return True
        else:
            return False

    #记录root 的登陆日志

    #返回登陆IP
    def return_ip(self,get):
        self.check_files()
        # return public.returnMsg(True, self.__ip_data)
        return public.return_message(0, 0, self.__ip_data)

    #添加IP白名单
    def add_return_ip(self, get):

        # 校验参数
        try:
            get.validate([
                Param('ip').Require().String().Ip(),
            ], [
                public.validate.trim_filter(),
            ])
        except Exception as ex:
            public.print_log("error info: {}".format(ex))
            return public.return_message(-1, 0, str(ex))

        self.check_files()
        if get.ip.strip() in self.__ip_data:
            # return public.returnMsg(False, public.lang("Already exists"))
            return public.return_message(-1, 0, public.lang("Already exists"))
        else:
            self.__ip_data.append(get.ip.strip())
            public.writeFile(self.__ClIENT_IP, json.dumps(self.__ip_data))
            # return public.returnMsg(True, public.lang("Added successfully"))
            return public.return_message(0, 0, public.lang("Added successfully"))

    def del_return_ip(self, get):
        # 校验参数
        try:
            get.validate([
                Param('ip').Require().Ip(),
            ], [
                public.validate.trim_filter(),
            ])
        except Exception as ex:
            public.print_log("error info: {}".format(ex))
            return public.return_message(-1, 0, str(ex))

        self.check_files()
        if get.ip.strip() in self.__ip_data:
            self.__ip_data.remove(get.ip.strip())
            public.writeFile(self.__ClIENT_IP, json.dumps(self.__ip_data))
            # return public.returnMsg(True, public.lang("Successfully deleted"))
            return public.return_message(0, 0, public.lang("Successfully deleted"))
        else:
            # return public.returnMsg(False, public.lang("IP does not exist"))
            return public.return_message(-1, 0, public.lang("IP does not exist"))

    #取登陆的前50个条记录
    def login_last(self):
        self.check_files()
        data=public.ExecShell('last -n 50')
        data=re.findall(r"(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)",data[0])
        if data>=1:
            data2=list(set(data))
            for i in data2:
                if not i in self.__ip_data:
                    self.__ip_data.append(i)
            public.writeFile(self.__ClIENT_IP, json.dumps(self.__ip_data))
        return self.__ip_data

    #获取ROOT当前登陆的IP
    def get_ip(self):
        data = public.ExecShell(''' who am i |awk ' {print $5 }' ''')
        data = re.findall(r"(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)",data[0])
        return data

    def get_logs(self, get):

        # 分页校验参数
        try:
            get.validate([
                Param('p_size').Integer(),
                Param('p').Integer(),
            ], [
                public.validate.trim_filter(),
            ])
        except Exception as ex:
            public.print_log("error info: {}".format(ex))
            return public.return_message(-1, 0, str(ex))
        import page
        page = page.Page()
        count = public.M('logs').where('type=?', ('SSH security',)).count()
        limit = 10
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
        data['data'] = public.M('logs').where('type=?', (u'SSH security',)).order('id desc').limit(
            str(page.SHIFT) + ',' + str(page.ROW)).field('log,addtime').select()
        # return data
        return public.return_message(0, 0, data)

    def get_server_ip(self):
        if os.path.exists('/www/server/panel/data/iplist.txt'):
            data=public.ReadFile('/www/server/panel/data/iplist.txt')
            return data.strip()
        else:return '127.0.0.1'


    #登陆的情况下
    def login(self):
        self.check_files()
        self.check_user()
        self.__ip_data = json.loads(public.ReadFile(self.__ClIENT_IP))
        ip=self.get_ip()
        if len(ip[0])==0:return False
        try:
            import time
            mDate = time.strftime('%Y-%m-%d %X', time.localtime())
            if ip[0] in self.__ip_data:
                if public.M('logs').where('type=? addtime', ('SSH security',mDate,)).count():return False
                public.WriteLog('SSH security', 'The server {} login IP is {}, login user is root'.format(public.GetLocalIp(),ip[0]))
                return False
            else:
                if public.M('logs').where('type=? addtime', ('SSH security', mDate,)).count(): return False
                self.send_mail_data('Server {} login alarm'.format(public.GetLocalIp()),'There is a login alarm on the server {}, the login IP is {}, the login user is root'.format(public.GetLocalIp(),ip[0]))
                public.WriteLog('SSH security','There is a login alarm on the server {}, the login IP is {}, login user is root'.format(public.GetLocalIp(),ip [0]))
                return True
        except:
            pass



    #修复bashrc文件
    def repair_bashrc(self):
        data = public.ReadFile(self.return_bashrc())
        if re.search(self.return_python() + ' /www/server/panel/class/ssh_security.py', data):
            public.WriteFile(self.return_bashrc(),data.replace(self.return_python()+' /www/server/panel/class/ssh_security.py login',''))
            #遗留的错误信息
            datassss = public.ReadFile(self.return_bashrc())
            if re.search(self.return_python(),datassss):
                public.WriteFile(self.return_bashrc(),datassss.replace(self.return_python(),''))


    #开启监控
    def start_jian(self,get):
        self.repair_bashrc()
        data = public.ReadFile(self.return_profile())
        if not re.search(self.return_python() + ' /www/server/panel/class/ssh_security.py', data):
            cmd = '''shell="%s /www/server/panel/class/ssh_security.py login"
        nohup  `${shell}` &>/dev/null &
        disown $!''' % (self.return_python())
            public.WriteFile(self.return_profile(), data.strip() + '\n' + cmd)
            return public.returnMsg(True, public.lang("Open successfully"))
        return public.returnMsg(False, public.lang("Open failed"))

    #关闭监控
    def stop_jian(self,get):
        data = public.ReadFile(self.return_profile())
        if re.search(self.return_python()+' /www/server/panel/class/ssh_security.py', data):
            cmd='''shell="%s /www/server/panel/class/ssh_security.py login"'''%(self.return_python())
            data=data.replace(cmd, '')
            cmd='''nohup  `${shell}` &>/dev/null &'''
            data=data.replace(cmd, '')
            cmd='''disown $!'''
            data=data.replace(cmd, '')
            public.WriteFile(self.return_profile(),data)
            #检查是否还存在遗留
            if re.search(self.return_python()+' /www/server/panel/class/ssh_security.py', data):
                public.WriteFile(self.return_profile(),data.replace(self.return_python()+' /www/server/panel/class/ssh_security.py login',''))
            #遗留的错误信息
            datassss = public.ReadFile(self.return_profile())
            if re.search(self.return_python(),datassss):
                public.WriteFile(self.return_profile(),datassss.replace(self.return_python(),''))

            return public.returnMsg(True, public.lang("Closed successfully"))
        else:
            return public.returnMsg(True, public.lang("Closed successfully"))

    #监控状态
    def get_jian(self,get):
        data = public.ReadFile(self.return_profile())
        #if re.search(r'{}\/www\/server\/panel\/class\/ssh_security.py\s+login'.format(r".*python\s+"), data):
        if re.search('/www/server/panel/class/ssh_security.py login', data):
            return public.returnMsg(True, public.lang("1"))
        else:
            return public.returnMsg(False, public.lang("1"))

    def set_password(self, get):
        '''
        开启密码登陆
        get: 无需传递参数
        '''
        ssh_password = r'\n#?PasswordAuthentication\s\w+'
        file = public.readFile(self.__SSH_CONFIG)
        if not file:
            return public.return_message(-1, 0, public.lang("ERROR: sshd config configuration file does not exist, cannot continue!"))
            # return public.returnMsg(False, public.lang("ERROR: sshd config configuration file does not exist, cannot continue!"))
        if len(re.findall(ssh_password, file)) == 0:
            file_result = file + '\nPasswordAuthentication yes'
        else:
            file_result = re.sub(ssh_password, '\nPasswordAuthentication yes', file)
        self.wirte(self.__SSH_CONFIG, file_result)
        self.restart_ssh()
        public.WriteLog('SSH management', 'Enable password login')
        # return public.returnMsg(True, public.lang("Open successfully"))
        return public.return_message(0, 0, public.lang("Open successfully"))

    def set_sshkey(self, get):
        '''
        设置ssh 的key
        参数 ssh=rsa&type=yes
        '''
        # 分页校验参数
        try:
            get.validate([
                Param('ssh').Require().String('in', ['yes', 'no']).Xss(),
                Param('type').Require().Xss(),
            ], [
                public.validate.trim_filter(),
            ])
        except Exception as ex:
            public.print_log("error info: {}".format(ex))
            return public.return_message(-1, 0, str(ex))

        # ssh_type = ['yes', 'no']
        ssh = get.ssh
        # if not ssh in ssh_type: return public.returnMsg(False, public.lang("ssh option failed"))
        s_type = get.type
        if not s_type in self.__type_list:
            # return public.returnMsg(False, public.lang("Wrong encryption method"))
            return public.return_message(-1, 0, public.lang("Wrong encryption method"))

        authorized_keys = '/root/.ssh/authorized_keys'
        file = ['/root/.ssh/id_{}.pub'.format(s_type), '/root/.ssh/id_{}'.format(s_type)]
        for i in file:
            if os.path.exists(i):
                public.ExecShell(r'sed -i "\~$(cat %s)~d" %s' % (file[0], authorized_keys))
                os.remove(i)
        os.system("ssh-keygen -t {s_type} -P '' -f /root/.ssh/id_{s_type} |echo y".format(s_type = s_type))
        if os.path.exists(file[0]):
            public.ExecShell('cat %s >> %s && chmod 600 %s' % (file[0], authorized_keys, authorized_keys))
            rec = r'\n#?RSAAuthentication\s\w+'
            rec2 = r'\n#?PubkeyAuthentication\s\w+'
            file = public.readFile(self.__SSH_CONFIG)
            if not file:
                # return public.returnMsg(False, public.lang("ERROR: sshd config configuration file does not exist, cannot continue!"))
                return public.return_message(-1, 0, public.lang("ERROR: sshd config configuration file does not exist"))
            if len(re.findall(rec, file)) == 0: file = file + '\nRSAAuthentication yes'
            if len(re.findall(rec2, file)) == 0: file = file + '\nPubkeyAuthentication yes'
            file_ssh = re.sub(rec, '\nRSAAuthentication yes', file)
            file_result = re.sub(rec2, '\nPubkeyAuthentication yes', file_ssh)
            if ssh == 'no':
                ssh_password = r'\n#?PasswordAuthentication\s\w+'
                if len(re.findall(ssh_password, file_result)) == 0:
                    file_result = file_result + '\nPasswordAuthentication no'
                else:
                    file_result = re.sub(ssh_password, '\nPasswordAuthentication no', file_result)
            self.wirte(self.__SSH_CONFIG, file_result)
            public.writeFile(self.__key_type_file, s_type)
            self.restart_ssh()
            public.WriteLog('SSH management', 'Set up SSH key authentication and successfully generate the key')
            # return public.returnMsg(True, public.lang("Open successfully"))
            return public.return_message(0, 0, public.lang("Open successfully"))
        else:
            public.WriteLog('SSH management', 'Failed to set SSH key authentication')
            # return public.returnMsg(False, public.lang("Open failed"))
            return public.return_message(-1, 0, public.lang("Open failed"))

        # 取SSH信息

    def get_msg_push_list(self,get):
        """
        @name 获取消息通道配置列表
        @auther: cjxin
        @date: 2022-08-16
        @
        """
        cpath = 'data/msg.json'
        try:
            if 'force' in get or not os.path.exists(cpath):
                public.downloadFile('{}/linux/panel/msg/msg.json'.format("https://node.aapanel.com"),cpath)
        except : pass

        data = {}
        if os.path.exists(cpath):
            msgs = json.loads(public.readFile(cpath))
            for x in msgs:
                x['setup'] = False
                x['info'] = False
                key = x['name']
                try:
                    obj =  public.init_msg(x['name'])
                    if obj:
                        x['setup'] = True
                        x['info'] = obj.get_version_info(None)
                except :
                    print(public.get_error_info())
                    pass
                data[key] = x
        # return data
        return public.return_message(0, 0, data)
    def _get_msg_push_list(self,get):
        """
        @name 获取消息通道配置列表
        @auther: cjxin
        @date: 2022-08-16
        @
        """
        cpath = 'data/msg.json'
        try:
            if 'force' in get or not os.path.exists(cpath):
                public.downloadFile('{}/linux/panel/msg/msg.json'.format("https://node.aapanel.com"),cpath)
        except : pass

        data = {}
        if os.path.exists(cpath):
            msgs = json.loads(public.readFile(cpath))
            for x in msgs:
                x['setup'] = False
                x['info'] = False
                key = x['name']
                try:
                    obj =  public.init_msg(x['name'])
                    if obj:
                        x['setup'] = True
                        x['info'] = obj.get_version_info(None)
                except :
                    print(public.get_error_info())
                    pass
                data[key] = x
        return data
        # return public.return_message(0, 0, data)



    #取消告警
    def clear_login_send(self,get):

        # 校验参数
        try:
            get.validate([
                Param('type').Require().String().Xss(),
            ], [
                public.validate.trim_filter(),
            ])
        except Exception as ex:
            public.print_log("error info: {}".format(ex))
            return public.return_message(-1, 0, str(ex))


        login_send_type_conf = "/www/server/panel/data/ssh_send_type.pl"
        os.remove(login_send_type_conf)
        self.stop_jian(get)
        # return public.returnMsg(True, public.lang("Successfully cancel the login alarm！"))
        return public.return_message(0, 0, public.lang("Successfully cancel the login alarm"))

    #设置告警
    def set_login_send(self,get):
        # 校验参数
        try:
            get.validate([
                Param('type').Require().String().Xss(),
            ], [
                public.validate.trim_filter(),
            ])
        except Exception as ex:
            public.print_log("error info: {}".format(ex))
            return public.return_message(-1, 0, str(ex))

        login_send_type_conf = "/www/server/panel/data/ssh_send_type.pl"
        set_type=get.type.strip()

        msg_configs = self._get_msg_push_list(get)
        # public.print_log("22222 --{}".format(msg_configs.keys()))
        if set_type not in msg_configs.keys():
            # return public.returnMsg(False, public.lang("This send type is not supported"))
            return public.return_message(-1, 0, public.lang("This send type is not supported"))

        from panelMessage import panelMessage
        pm = panelMessage()
        obj = pm.init_msg_module(set_type)
        if not obj:
            # return public.returnMsg(False, public.lang("The message channel is not installed."))
            return public.return_message(-1, 0, public.lang("The message channel is not installed"))

        public.writeFile(login_send_type_conf, set_type)
        self.start_jian(get)
        # return public.returnMsg(True, public.lang("Successfully set"))
        return public.return_message(0, 0, public.lang("Successfully set"))

    #查看告警
    def get_login_send(self, get):
        login_send_type_conf = "/www/server/panel/data/ssh_send_type.pl"
        if os.path.exists(login_send_type_conf):
            send_type = public.readFile(login_send_type_conf).strip()
        else:
            send_type ="error"
        # return public.returnMsg(True, send_type)
        return public.return_message(0, 0, send_type)

    def GetSshInfo(self, get):
        # port = public.get_ssh_port()

        pid_file = '/run/sshd.pid'
        if os.path.exists(pid_file):
            pid = int(public.readFile(pid_file))
            status = public.pid_exists(pid)
        else:
            import system
            panelsys = system.system()
            version = panelsys.GetSystemVersion()
            if os.path.exists('/usr/bin/apt-get'):
                if os.path.exists('/etc/init.d/sshd'):
                    status = public.ExecShell("service sshd status | grep -P '(dead|stop)'|grep -v grep")
                else:
                    status = public.ExecShell("service ssh status | grep -P '(dead|stop)'|grep -v grep")
            else:
                if version.find(' 7.') != -1 or version.find(' 8.') != -1 or version.find('Fedora') != -1:
                    status = public.ExecShell("systemctl status sshd.service | grep 'dead'|grep -v grep")
                else:
                    status = public.ExecShell("/etc/init.d/sshd status | grep -e 'stopped' -e '已停'|grep -v grep")

            #       return status;
            if len(status[0]) > 3:
                status = False
            else:
                status = True
        return status


    def stop_key(self, get):
        '''
        关闭key
        无需参数传递
        '''
        is_ssh_status=self.GetSshInfo(get)
        rec = r'\n\s*#?\s*RSAAuthentication\s+\w+'
        rec2 = r'\n\s*#?\s*PubkeyAuthentication\s+\w+'
        file = public.readFile(self.__SSH_CONFIG)
        if not file:
            # return public.returnMsg(False, public.lang("错误：sshd_config配置文件不存在，无法继续!"))
            return public.return_message(-1, 0, public.lang("Error: sshd config configuration file does not exist"))
        file_ssh = re.sub(rec, '\nRSAAuthentication no', file)
        file_result = re.sub(rec2, '\nPubkeyAuthentication no', file_ssh)
        self.wirte(self.__SSH_CONFIG, file_result)

        if is_ssh_status:
            self.set_password(get)
            self.restart_ssh()
        public.WriteLog('SSH management','Disable SSH key login')
        # return public.returnMsg(True, public.lang("Disable successfully"))
        return public.return_message(0, 0, public.lang("Disable successfully"))



    def get_config(self, get):
        '''
        获取配置文件
        无参数传递
        '''
        result = {}
        file = public.readFile(self.__SSH_CONFIG)
        if not file:
            # return public.returnMsg(False, public.lang("Error: sshd config does not exist"))
            return public.return_message(-1, 0, public.lang("Error: sshd config does not exist"))

        # ========   以下在2022-10-12重构  ==========
        # author : hwliang
        # 是否开启RSA公钥认证
        # 默认开启(最新版openssh已经不支持RSA公钥认证)
        # yes = 开启
        # no = 关闭
        result['rsa_auth'] = 'yes'
        rec = r'^\s*RSAAuthentication\s*(yes|no)'
        rsa_find = re.findall(rec, file, re.M|re.I)
        if rsa_find and rsa_find[0].lower() == 'no': result['rsa_auth'] = 'no'

        # 获取是否开启公钥认证
        # 默认关闭
        # yes = 开启
        # no = 关闭
        result['pubkey'] = 'no'
        if self._get_key(get)['msg']: # 先检查是否存在可用的公钥
            pubkey = r'^\s*PubkeyAuthentication\s*(yes|no)'
            pubkey_find = re.findall(pubkey, file, re.M|re.I)
            if pubkey_find and pubkey_find[0].lower() == 'yes': result['pubkey'] = 'yes'


        # 是否开启密码登录
        # 默认开启
        # yes = 开启
        # no = 关闭
        result['password'] = 'yes'
        ssh_password = r'^\s*PasswordAuthentication\s*([\w\-]+)'
        ssh_password_find = re.findall(ssh_password, file, re.M|re.I)
        if ssh_password_find and ssh_password_find[0].lower() == 'no': result['password'] = 'no'

        #是否允许root登录
        # 默认允许
        # yes = 允许
        # no = 不允许
        # without-password = 允许，但不允许使用密码登录
        # forced-commands-only = 允许，但只允许执行命令，不能使用终端
        result['root_is_login'] = 'yes'
        result['root_login_type'] = 'yes'
        root_is_login=r'^\s*PermitRootLogin\s*([\w\-]+)'
        root_is_login_find = re.findall(root_is_login, file, re.M|re.I)
        if root_is_login_find and root_is_login_find[0].lower() != 'yes':
            result['root_is_login'] = 'no'
            result['root_login_type'] = root_is_login_find[0].lower()
        result['root_login_types'] = self.__root_login_types
        result['port'] = public.get_sshd_port()
        result['key_type'] = public.ReadFile(self.__key_type_file)
        # return result
        return public.return_message(0, 0, result)


    def set_root(self, get):
        '''
        开启密码登陆
        get: 无需传递参数
        '''
        # without-password  yes no   forced-commands-only
        # 分页校验参数
        try:
            get.validate([
                Param('p_type').String('in', ['yes', 'no', 'without-password', 'forced-commands-only']).Xss(),
            ], [
                public.validate.trim_filter(),
            ])
        except Exception as ex:
            public.print_log("error info: {}".format(ex))
            return public.return_message(-1, 0, str(ex))

        p_type = 'yes'
        if 'p_type' in get: p_type = get.p_type
        if p_type not in self.__root_login_types.keys():
            # return public.returnMsg(False, public.lang("Parameter passing error!"))
            return public.return_message(-1, 0, public.lang("Parameter passing error"))
        ssh_password = r'^\s*#?\s*PermitRootLogin\s*([\w\-]+)'
        file = public.readFile(self.__SSH_CONFIG)
        src_line = re.search(ssh_password, file,re.M)
        new_line = 'PermitRootLogin {}'.format(p_type)
        if not src_line:
            file_result = file + '\n{}'.format(new_line)
        else:
            file_result = file.replace(src_line.group(),new_line)
        self.wirte(self.__SSH_CONFIG, file_result)
        self.restart_ssh()
        msg = public.lang('Set the root login method as: {}',self.__root_login_types[p_type])
        public.WriteLog('SSH management',msg)
        # return public.returnMsg(True, msg)
        return public.return_message(0, 0, msg)


    def set_root_password(self, get):
        """
        @name 设置root密码
        @param get:
        @return:
        """
        password = get.password if "password" in get else ""
        username = get.username if "username" in get else ""
        if not password: return public.return_message(-1, 0, public.lang("The password cannot be empty"))
        if len(password) < 8: return public.return_message(-1, 0, public.lang("The password cannot be less than 8 bits long"))
        if get.username not in self.get_sys_user(get)['msg']:
            return public.return_message(-1, 0, public.lang("The username already exists"))

        has_letter = bool(re.search(r'[a-zA-Z!@#$%^&*()-_+=]', password))
        has_digit_or_symbol = bool(re.search(r'[0-9!@#$%^&*()-_+=]', password))
        if not has_letter or not has_digit_or_symbol: return public.return_message(-1, 0, public.lang("The password must contain letters and numbers or symbols"))

        if username == "root":
            cmd_result, cmd_err = public.ExecShell("echo root:%s|chpasswd" % password)
        else:
            cmd_result, cmd_err = public.ExecShell("echo %s:%s|chpasswd" % (username, password))

        if cmd_err: return public.return_message(-1, 0, public.lang("Setup failure"))
        public.WriteLog("SSH", "[Security] - [SSH] - [Set %s password]" % username)
        return public.return_message(0, 0, public.lang("successfully set"))

    def get_sys_user(self, get):
        """获取所有用户名
        @param:
        @return
        """
        from collections import deque
        user_set = deque()
        with open('/etc/passwd') as fp:
            for line in fp.readlines():
                user_set.append(line.split(':', 1)[0])

        return public.returnMsg(True, list(user_set))

    def stop_root(self, get):
        '''
        开启密码登陆
        get: 无需传递参数
        '''
        ssh_password = r'\n\s*PermitRootLogin\s+\w+'
        file = public.readFile(self.__SSH_CONFIG)
        if len(re.findall(ssh_password, file)) == 0:
            file_result = file + '\nPermitRootLogin no'
        else:
            file_result = re.sub(ssh_password, '\nPermitRootLogin no', file)
        self.wirte(self.__SSH_CONFIG, file_result)
        self.restart_ssh()
        public.WriteLog('SSH management','Set the root login method to: no')
        return public.returnMsg(True, public.lang("Disable successfully"))

    def stop_password(self, get):
        '''
        关闭密码访问
        无参数传递
        '''
        file = public.readFile(self.__SSH_CONFIG)
        ssh_password = r'\n#?PasswordAuthentication\s\w+'
        file_result = re.sub(ssh_password, '\nPasswordAuthentication no', file)
        self.wirte(self.__SSH_CONFIG, file_result)
        self.restart_ssh()
        public.WriteLog('SSH management','Disable password access')
        return public.returnMsg(True, public.lang("Closed successfully"))

    def _get_key(self, get):
        '''
        获取key 无参数传递
        '''
        key_type = self.get_ssh_key_type()
        if key_type in self.__type_files.keys():
            key_file = self.__type_files[key_type]
            key = public.readFile(key_file)
            return public.returnMsg(True,key)
        return public.returnMsg(True, public.lang(""))

    def get_key(self, get):
        '''
        获取key 无参数传递
        '''
        key_type = self.get_ssh_key_type()
        if key_type in self.__type_files.keys():
            key_file = self.__type_files[key_type]
            key = public.readFile(key_file)
            return public.return_message(0, 0,key)
        return public.return_message(0, 0, public.lang(""))
    def download_key(self, get):
        '''
            @name 下载密钥
        '''
        download_file = ''
        key_type = self.get_ssh_key_type()
        if key_type in self.__type_files.keys():
            if os.path.exists(self.__type_files[key_type]):
                download_file = self.__type_files[key_type]

        else:
            for file in self.__key_files:
                if not os.path.exists(file): continue
                download_file = file
                break

        if not download_file: return public.returnMsg(False, public.lang("Key file not found!"))
        from flask import send_file
        filename = "{}_{}".format(public.GetHost(),os.path.basename(download_file))
        return send_file(download_file,download_name=filename)

    def wirte(self, file, ret):
        result = public.writeFile(file, ret)
        return result

    def restart_ssh(self):
        '''
        重启ssh 无参数传递
        '''
        version = public.readFile('/etc/redhat-release')
        act = 'restart'
        if not os.path.exists('/etc/redhat-release'):
            public.ExecShell('service ssh ' + act)
        elif version.find(' 7.') != -1 or version.find(' 8.') != -1:
            public.ExecShell("systemctl " + act + " sshd.service")
        else:
            public.ExecShell("/etc/init.d/sshd " + act)
    #检查是否设置了钉钉
    def check_dingding(self, get):
        '''
        检查是否设置了钉钉
        '''
        #检查文件是否存在
        if not os.path.exists('/www/server/panel/data/dingding.json'):return False
        dingding_config=public.ReadFile('/www/server/panel/data/dingding.json')
        if not dingding_config:return False
        #解析json
        try:
            dingding=json.loads(dingding_config)
            if dingding['dingding_url']:
                return True
        except:
            return False

    #开启SSH双因子认证
    def start_auth_method(self, get):
        '''
        开启SSH双因子认证
        '''
        #检查是否设置了钉钉
        import ssh_authentication
        ssh_class=ssh_authentication.ssh_authentication()
        return  ssh_class.start_ssh_authentication_two_factors()

    #关闭SSH双因子认证
    def stop_auth_method(self, get):
        '''
        关闭SSH双因子认证
        '''
        #检查是否设置了钉钉
        import ssh_authentication
        ssh_class=ssh_authentication.ssh_authentication()
        return ssh_class.close_ssh_authentication_two_factors()

    #获取SSH双因子认证状态
    def get_auth_method(self, get):
        '''
        获取SSH双因子认证状态
        '''
        #检查是否设置了钉钉
        import ssh_authentication
        ssh_class=ssh_authentication.ssh_authentication()
        return ssh_class.check_ssh_authentication_two_factors()

    #判断so文件是否存在
    def check_so_file(self, get):
        '''
        判断so文件是否存在
        '''
        import ssh_authentication
        ssh_class=ssh_authentication.ssh_authentication()
        return ssh_class.is_check_so()

    #下载so文件
    def get_so_file(self, get):
        '''
        下载so文件
        '''
        import ssh_authentication
        ssh_class=ssh_authentication.ssh_authentication()
        return ssh_class.download_so()

    #获取pin
    def get_pin(self, get):
        '''
        获取pin
        '''
        import ssh_authentication
        ssh_class=ssh_authentication.ssh_authentication()
        return public.returnMsg(True, ssh_class.get_pin())

    def get_login_record(self,get):
        if os.path.exists(self.open_ssh_login):

            return public.returnMsg(True, public.lang(""))
        else:
            return public.returnMsg(False, public.lang(""))
    def start_login_record(self,get):
        if os.path.exists(self.open_ssh_login):
            return public.returnMsg(True, public.lang(""))
        else:
            public.writeFile(self.open_ssh_login,"True")
            return public.returnMsg(True, public.lang(""))
    def stop_login_record(self,get):
        if os.path.exists(self.open_ssh_login):
            os.remove(self.open_ssh_login)
            return public.returnMsg(True, public.lang(""))
        else:
            return public.returnMsg(True, public.lang(""))
    # 获取登录记录列表
    def get_record_list(self, get):
        if 'limit' in get:
            limit = int(get.limit.strip())
        else:
            limit = 12
        import page
        page = page.Page()
        count = public.M('ssh_login_record').order("id desc").count()
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

        data['data'] = public.M('ssh_login_record').order('id desc').limit(
            str(page.SHIFT) + ',' + str(page.ROW)).select()

        return data

    def get_file_json(self,get):

        if os.path.exists(get.path):
            ret=json.loads(public.ReadFile(get.path))
            return  ret
        else:
            return ''

if __name__ == '__main__':
    import sys
    type = sys.argv[1]
    if type=='login':
        try:
            aa = ssh_security()
            aa.login()
        except:pass
    else:
        pass
