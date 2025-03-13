#coding: utf-8
#-------------------------------------------------------------------
# aaPanel
#-------------------------------------------------------------------
# Copyright (c) 2015-2099 aaPanel(www.aapanel.com) All rights reserved.
#-------------------------------------------------------------------
# Author: hwliang <hwl@aapanel.com>
#-------------------------------------------------------------------

# ssh信息
#------------------------------
import json
import os
import re
import time

import public
from safeModel.base import safeBase


class main(safeBase):

    def __init__(self):
        pass


    def get_ssh_intrusion(self,get):
        """
        @获取SSH爆破次数
        @param get:
        """
        result = {'error':0,'success':0}
        if os.path.exists("/etc/debian_version"):
            version = public.readFile('/etc/debian_version').strip()
            if 'bookworm' in version or 'jammy' in version or 'impish' in version:
                version = 12
            else:
                try:
                    version = float(version)
                except:
                    version = 11
            if version >= 12:
                result['error'] = int(public.ExecShell("journalctl -u ssh --no-pager |grep -a 'Failed password for' |grep -v 'invalid' |wc -l")[0]) + int(public.ExecShell("journalctl -u ssh --no-pager|grep -a 'Connection closed by authenticating user' |grep -a 'preauth' |wc -l")[0])
                result['success'] = int(public.ExecShell("journalctl -u ssh --no-pager|grep -a 'Accepted' |wc -l")[0])
                return result
                # return public.return_message(0, 0, result)
        data = self.get_ssh_cache()
        for sfile in self.get_ssh_log_files(None):
            for stype in result.keys():
                count = 0
                if  sfile in data[stype] and not sfile in ['/var/log/auth.log','/var/log/secure']:
                    count += data[stype][sfile]
                else:
                    try:
                        if stype == 'error':
                            num1,num2 = 0,0
                            try:
                                num1 = int(public.ExecShell("cat %s|grep -a 'Failed password for' |grep -v 'invalid' |wc -l" % (sfile))[0].strip())
                            except:pass
                            try:
                                num2 += int(public.ExecShell("cat %s|grep -a 'Connection closed by authenticating user' |grep -a 'preauth' |wc -l" % (sfile))[0].strip())
                            except:pass

                            count = num1 + num2
                        else:
                            count = int(public.ExecShell("cat %s|grep -a 'Accepted' |wc -l" % (sfile))[0].strip())
                    except: pass
                    data[stype][sfile] = count

                result[stype] += count
        self.set_ssh_cache(data)
        return result
        # return public.return_message(0, 0, result)

    def get_ssh_cache(self):
        """
        @获取缓存ssh记录
        """
        file = '{}/data/ssh_cache.json'.format(public.get_panel_path())
        if not os.path.exists(file):
            public.writeFile(file,json.dumps({'success':{},'error':{}}))
        data = json.loads(public.readFile(file))

        return data

    def set_ssh_cache(self,data):
        """
        @设置ssh缓存
        """
        file = '{}/data/ssh_cache.json'.format(public.get_panel_path())
        public.writeFile(file,json.dumps(data))
        return True


    def GetSshInfo(self,get):
        """
        @获取SSH登录信息

        """
        port = public.get_sshd_port()
        status = public.get_sshd_status()
        isPing = True
        try:
            file = '/etc/sysctl.conf'
            conf = public.readFile(file)
            rep = r"#*net\.ipv4\.icmp_echo_ignore_all\s*=\s*([0-9]+)"
            tmp = re.search(rep,conf).groups(0)[0]
            if tmp == '1': isPing = False
        except:
            isPing = True

        data = {}
        data['port'] = port
        data['status'] = status
        data['ping'] = isPing
        data['firewall_status'] = self.CheckFirewallStatus()
        data['error'] = self.get_ssh_intrusion(get)
        data['fail2ban'] = self.get_ssh_fail2ban(get)
        return data


    def get_ssh_fail2ban(self,get):
        """
        @防爆破开关
        """
        data = {}
        s_file = '{}/plugin/fail2ban/config.json'.format(public.get_panel_path())
        if os.path.exists(s_file):
            try:
                data = json.loads(public.readFile(s_file))
            except: pass
        if 'sshd' in data:
            if data['sshd']['act'] == 'true':
                return 1
        return 0

    #改远程端口
    def SetSshPort(self,get):
        port = get.port
        if int(port) < 22 or int(port) > 65535: return public.returnMsg(False, public.lang("Port range must be between 22 and 65535!"))
        ports = ['21','25','80','443','8080','888','8888']
        if port in ports: return public.returnMsg(False, public.lang("Please dont use default ports for common programs!"))
        file = '/etc/ssh/sshd_config'
        conf = public.readFile(file)

        rep = r"#*Port\s+([0-9]+)\s*\n"
        conf = re.sub(rep, "Port "+port+"\n", conf)
        public.writeFile(file,conf)

        if self.__isFirewalld:
            public.ExecShell('firewall-cmd --permanent --zone=public --add-port='+port+'/tcp')
            public.ExecShell('setenforce 0')
            public.ExecShell('sed -i "s#SELINUX=enforcing#SELINUX=disabled#" /etc/selinux/config')
            public.ExecShell("systemctl restart sshd.service")
        elif self.__isUfw:
            public.ExecShell('ufw allow ' + port + '/tcp')
            public.ExecShell("service ssh restart")
        else:
            public.ExecShell('iptables -I INPUT -p tcp -m state --state NEW -m tcp --dport '+port+' -j ACCEPT')
            public.ExecShell("/etc/init.d/sshd restart")

        self.FirewallReload()
        public.M('firewall').where("ps=? or ps=? or port=?",('SSH remote management service','SSH remote service',port)).delete()
        public.M('firewall').add('port,ps,addtime',(port,'SSH remote service',time.strftime('%Y-%m-%d %X',time.localtime())))
        public.WriteLog("TYPE_FIREWALL", "FIREWALL_SSH_PORT",(port,))
        return public.returnMsg(True, public.lang("Successfully modified"))



    def SetSshStatus(self,get):
        """
        @设置SSH状态
        """
        if int(get['status'])==1:
            msg = public.getMsg('FIREWALL_SSH_STOP')
            act = 'stop'
        else:
            msg = public.getMsg('FIREWALL_SSH_START')
            act = 'start'

        public.ExecShell("/etc/init.d/sshd "+act)
        public.ExecShell('service ssh ' + act)
        public.ExecShell("systemctl "+act+" sshd")
        public.ExecShell("systemctl "+act+" ssh")

        public.WriteLog("TYPE_FIREWALL", msg)
        return public.returnMsg(True, public.lang("SUCCESS"))


