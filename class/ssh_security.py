#coding: utf-8
#-------------------------------------------------------------------
# 宝塔Linux面板
#-------------------------------------------------------------------
# Copyright (c) 2015-2017 宝塔软件(http:#bt.cn) All rights reserved.
#-------------------------------------------------------------------
# Author: lkqiang <lkq@bt.cn>
#-------------------------------------------------------------------
# SSH 安全类
#------------------------------
import public,os,re,send_mail,json
from datetime import datetime

class ssh_security:
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

    def __init__(self):
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


    def check_files(self):
        try:
            json.loads(public.ReadFile(self.__ClIENT_IP))
        except:
            public.WriteFile(self.__ClIENT_IP, json.dumps([]))

    def get_ssh_port(self):
        conf = public.readFile(self.__SSH_CONFIG)
        if not conf: conf = ''
        rep = "#*Port\s+([0-9]+)\s*\n"
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
                        print(valuse)
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
                            print(valuse)
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
    def send_mail_data(self,title,body,type='mail'):
        if type=='mail':
            if self.__mail_config['user_mail']['user_name']:
                if len(self.__mail_config['user_mail']['mail_list'])>=1:
                    for i in self.__mail_config['user_mail']['mail_list']:
                        self.__mail.qq_smtp_send(i, title, body)
        elif type=='dingding':
            if self.__mail_config['dingding']['dingding']:
                self.__mail.dingding_send(title+body)
        return True

    #检测非UID为0的账户
    def check_user(self):
        data=public.ExecShell('''cat /etc/passwd | awk -F: '($3 == 0) { print $1 }'|grep -v '^root$'  ''')
        data=data[0]
        if re.search("\w+",data):
            self.send_mail_data(public.GetLocalIp()+'There are backdoor users on the server',public.GetLocalIp()+'There are backdoor users on the server'+data+'Check the /etc/passwd file')
            return True
        else:
            return False

    #记录root 的登陆日志

    #返回登陆IP
    def return_ip(self,get):
        self.check_files()
        return public.returnMsg(True, self.__ip_data)

    #添加IP白名单
    def add_return_ip(self, get):
        self.check_files()
        if get.ip.strip() in self.__ip_data:
            return public.returnMsg(False, "Already exists")
        else:
            self.__ip_data.append(get.ip.strip())
            public.writeFile(self.__ClIENT_IP, json.dumps(self.__ip_data))
            return public.returnMsg(True, "Added successfully")

    def del_return_ip(self, get):
        self.check_files()
        if get.ip.strip() in self.__ip_data:
            self.__ip_data.remove(get.ip.strip())
            public.writeFile(self.__ClIENT_IP, json.dumps(self.__ip_data))
            return public.returnMsg(True, "Successfully deleted")
        else:
            return public.returnMsg(False, "IP does not exist")

    #取登陆的前50个条记录
    def login_last(self):
        self.check_files()
        data=public.ExecShell('last -n 50')
        data=re.findall("(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)",data[0])
        if data>=1:
            data2=list(set(data))
            for i in data2:
                if not i in self.__ip_data:
                    self.__ip_data.append(i)
            public.writeFile(self.__ClIENT_IP, json.dumps(self.__ip_data))
        return self.__ip_data

    #获取ROOT当前登陆的IP
    def get_ip(self):
        data = public.ExecShell(''' echo $SSH_CLIENT |awk ' { print $1 }' ''')
        data = re.findall("(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)",data[0])
        return data

    def get_logs(self, args):
        if 'p' in args: p = int(args.p)
        rows = 10
        if 'rows' in args: rows = int(args.rows)
        count = public.M('logs').where('type=?', ('SSH security',)).count()
        data = public.get_page(count, int(args.p), int(rows))
        data['data'] = public.M('logs').where('type=?', ('SSH security',)).limit(data['shift'] + ',' + data['row']).order(
            'addtime desc').select()
        return data

    def get_server_ip(self):
        if os.path.exists('/www/server/panel/data/iplist.txt'):
            data=public.ReadFile('/www/server/panel/data/iplist.txt')
            return data.strip()
        else:return '127.0.0.1'


    #登陆的情况下
    def login(self):
        self.check_files()
        if not self.__mail_config['user_mail']['user_name']:return False
        self.check_user()
        self.__ip_data = json.loads(public.ReadFile(self.__ClIENT_IP))
        ip=self.get_ip()
        if not ip:
            ip = ["127.0.0.1"]
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

    #开启监控
    def start_jian(self,get):
        data=public.ReadFile('/etc/bashrc')
        if not re.search('{}\/www\/server\/panel\/class\/ssh_security.py'.format(".*python\s+"),data):
            public.WriteFile('/etc/bashrc',data.strip()+'\n{} /www/server/panel/class/ssh_security.py login\n'.format(self.__pyenv))
            return public.returnMsg(True, 'Open successfully')
        return public.returnMsg(False, 'Open failed')

    #关闭监控
    def stop_jian(self,get):
        data = public.ReadFile('/etc/bashrc')
        if re.search('{}\/www\/server\/panel\/class\/ssh_security.py'.format(".*python\s+"), data):
            public.WriteFile('/etc/bashrc',data.replace('python /www/server/panel/class/ssh_security.py login',''))
            return public.returnMsg(True, 'Closed successfully')
        else:
            return public.returnMsg(True, 'Closed successfully')

    #监控状态
    def get_jian(self,get):
        data = public.ReadFile('/etc/bashrc')
        if re.search('{}\/www\/server\/panel\/class\/ssh_security.py\s+login'.format(".*python\s+"), data):
            return public.returnMsg(True, '1')
        else:
            return public.returnMsg(False, '1')

    def set_password(self, get):
        '''
        开启密码登陆
        get: 无需传递参数
        '''
        ssh_password = '\n#?PasswordAuthentication\s\w+'
        file = public.readFile(self.__SSH_CONFIG)
        if len(re.findall(ssh_password, file)) == 0:
            file_result = file + '\nPasswordAuthentication yes'
        else:
            file_result = re.sub(ssh_password, '\nPasswordAuthentication yes', file)
        self.wirte(self.__SSH_CONFIG, file_result)
        self.restart_ssh()
        return public.returnMsg(True, 'Open successfully')

    def set_sshkey(self, get):
        '''
        设置ssh 的key
        参数 ssh=rsa&type=yes
        '''
        type_list = ['rsa', 'dsa','ed25519']
        ssh_type = ['yes', 'no']
        ssh = get.ssh
        if not ssh in ssh_type: return public.returnMsg(False, 'ssh option failed')
        type = get.type
        if not type in type_list: return public.returnMsg(False, 'Wrong encryption method')
        file = ['/root/.ssh/id_rsa.pub', '/root/.ssh/id_rsa', '/root/.ssh/authorized_keys']
        for i in file:
            if os.path.exists(i):
                os.remove(i)
        os.system("ssh-keygen -t %s -P '' -f ~/.ssh/id_rsa |echo y" % type)
        if os.path.exists(file[0]):
            public.ExecShell('cat %s >%s && chmod 600 %s' % (file[0], file[-1], file[-1]))
            rec = '\n#?RSAAuthentication\s\w+'
            rec2 = '\n#?PubkeyAuthentication\s\w+'
            file = public.readFile(self.__SSH_CONFIG)
            if len(re.findall(rec, file)) == 0: file = file + '\nRSAAuthentication yes'
            if len(re.findall(rec2, file)) == 0: file = file + '\nPubkeyAuthentication yes'
            file_ssh = re.sub(rec, '\nRSAAuthentication yes', file)
            file_result = re.sub(rec2, '\nPubkeyAuthentication yes', file_ssh)
            if ssh == 'no':
                ssh_password = '\n#?PasswordAuthentication\s\w+'
                if len(re.findall(ssh_password, file_result)) == 0:
                    file_result = file_result + '\nPasswordAuthentication no'
                else:
                    file_result = re.sub(ssh_password, '\nPasswordAuthentication no', file_result)
            self.wirte(self.__SSH_CONFIG, file_result)
            self.restart_ssh()
            return public.returnMsg(True, 'Open successfully')
        else:
            return public.returnMsg(False, 'Open failed')

    def stop_key(self, get):
        '''
        关闭key
        无需参数传递
        '''
        file = ['/root/.ssh/id_rsa.pub', '/root/.ssh/id_rsa', '/root/.ssh/authorized_keys']
        rec = '\n#?RSAAuthentication\s\w+'
        rec2 = '\n#?PubkeyAuthentication\s\w+'
        file = public.readFile(self.__SSH_CONFIG)
        file_ssh = re.sub(rec, '\n#RSAAuthentication no', file)
        file_result = re.sub(rec2, '\n#PubkeyAuthentication no', file_ssh)
        self.wirte(self.__SSH_CONFIG, file_result)
        self.set_password(get)
        self.restart_ssh()
        return public.returnMsg(True, 'Closed successfully')

    def get_config(self, get):
        '''
        获取配置文件
        无参数传递
        '''
        result = {}
        file = public.readFile(self.__SSH_CONFIG)
        rec = '\n#?RSAAuthentication\s\w+'
        pubkey = '\n#?PubkeyAuthentication\s\w+'
        ssh_password = '\nPasswordAuthentication\s\w+'
        ret = re.findall(ssh_password, file)
        if not ret:
            result['password'] = 'no'
        else:
            if ret[-1].split()[-1] == 'yes':
                result['password'] = 'yes'
            else:
                result['password'] = 'no'
        pubkey = re.findall(pubkey, file)
        if not pubkey:
            result['pubkey'] = 'no'
        else:
            if pubkey[-1].split()[-1] == 'no':
                result['pubkey'] = 'no'
            else:
                result['pubkey'] = 'yes'
        rsa_auth = re.findall(rec, file)
        if not rsa_auth:
            result['rsa_auth'] = 'no'
        else:
            if rsa_auth[-1].split()[-1] == 'no':
                result['rsa_auth'] = 'no'
            else:
                result['rsa_auth'] = 'yes'
        return result

    def stop_password(self, get):
        '''
        关闭密码访问
        无参数传递
        '''
        file = public.readFile(self.__SSH_CONFIG)
        ssh_password = '\n#?PasswordAuthentication\s\w+'
        file_result = re.sub(ssh_password, '\nPasswordAuthentication no', file)
        self.wirte(self.__SSH_CONFIG, file_result)
        self.restart_ssh()
        return public.returnMsg(True, 'Closed successfully')

    def get_key(self, get):
        '''
        获取key 无参数传递
        '''
        file = '/root/.ssh/id_rsa'
        if not os.path.exists(file): return public.returnMsg(True, '')
        ret = public.readFile(file)
        return public.returnMsg(True, ret)

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
