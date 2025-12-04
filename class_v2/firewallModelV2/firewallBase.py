# coding: utf-8
# -------------------------------------------------------------------
# aapanel
# -------------------------------------------------------------------
# Copyright (c) 2014-2099 aapanel(http://bt.cn) All rights reserved.
# -------------------------------------------------------------------
# Author: wzz <wzz@bt.cn>
# -------------------------------------------------------------------

# ------------------------------
# 系统防火墙模型 - 基类
# ------------------------------

import os
import re
from typing import Dict, Union, Any

import public


class Base(object):
    def __init__(self):
        self.config_path = "{}/class_v2/firewallModelV2/config".format(public.get_panel_path())
        self.m_time_file = "/www/server/panel/data/firewall/geoip_mtime.pl"
        self._isUfw = False
        self._isFirewalld = False
        self._isIptables = False
        if os.path.exists('/usr/sbin/firewalld') or os.path.exists('/etc/redhat-release'):
            self._isFirewalld = True
            from firewallModelV2.app.firewalld import Firewalld
            self.firewall = Firewalld()
        elif os.path.exists('/usr/bin/apt-get'):
            self._isUfw = True
            from firewallModelV2.app.ufw import Ufw
            self.firewall = Ufw()
        elif not self._isUfw and not self._isFirewalld:
            self._isIptables = True
            from firewallModelV2.app.iptables import Iptables
            self.firewall = Iptables()
        _months = {'Jan': '01', 'Feb': '02', 'Mar': '03', 'Apr': '04', 'May': '05', 'Jun': '06', 'Jul': '07',
                   'Aug': '08', 'Sep': '09', 'Sept': '09', 'Oct': '10', 'Nov': '11', 'Dec': '12'}

    # 2024/3/14 上午 11:27 获取防火墙运行状态
    def get_firewall_status(self) -> bool:
        """
            @name 获取防火墙运行状态
            @author wzz <2024/3/14 上午 11:27>
            @param
            @return bool True/False
        """
        if self._isUfw:
            res = public.ExecShell("systemctl is-active ufw")[0]
            if res == "active": return True
            res = public.ExecShell("systemctl list-units | grep ufw")[0]
            if res.find('active running') != -1: return True
            res = public.ExecShell('/lib/ufw/ufw-init status')[0]
            if res.find("Firewall is not running") != -1: return False
            res = public.ExecShell('ufw status verbose')[0]
            if res.find('inactive') != -1: return False
            return True
        if self._isFirewalld:
            res = public.ExecShell("ps -ef|grep firewalld|grep -v grep")[0]
            if res: return True
            res = public.ExecShell("systemctl is-active firewalld")[0]
            if res == "active": return True
            res = public.ExecShell("systemctl list-units | grep firewalld")[0]
            if res.find('active running') != -1: return True
            return False
        else:
            res = public.ExecShell("/etc/init.d/iptables status")[0]
            if res.find('not running') != -1: return False
            res = public.ExecShell("systemctl is-active iptables")[0]
            if res == "active": return True
            return True

    # 2024/3/14 上午 11:30 设置禁ping
    def set_ping(self, get) -> dict:
        """
            @name 设置禁ping
            @author wzz <2024/3/14 上午 11:31>
            @param "data":{"参数名":""} <数据类型> 参数描述
            @return dict{"status":True/False,"msg":"提示信息"}
        """
        get.status = get.get("status", "1")
        get.status = str(get.status) if str(get.status) in ['0', '1'] else '1'

        filename = '/etc/sysctl.conf'
        conf = public.readFile(filename)
        if conf.find('net.ipv4.icmp_echo') != -1:
            rep = r"net\.ipv4\.icmp_echo.*"
            conf = re.sub(rep, 'net.ipv4.icmp_echo_ignore_all=' + get.status + "\n", conf)
        else:
            conf += "\nnet.ipv4.icmp_echo_ignore_all=" + get.status + "\n"

        if public.writeFile(filename, conf):
            public.ExecShell('sysctl -p')
            return public.return_message(0, 0, public.lang("SUCCESS"))
        else:
            return public.return_message(-1, 0,
                                         '<a style="color:red;">Error: Setting failed, sysctl.conf is not writable! </a><br>'
                                         '1. If aApanel [System Hardening] is installed, please close it first<br>'
                                         '2. If Cloud Lock is installed, please turn off the [System Collagen] function<br>'
                                         '3. If a security dog is installed, please turn off the [System Protection] function<br>'
                                         '4. If you use other security software, please uninstall it first<br>'
                                         )

    # 2024/3/14 上午 11:37 获取网站日志目录的大小
    def get_www_logs_size(self, get) -> Dict[str, Union[str, Any]]:
        """
            @name 获取网站日志目录的大小
            @author wzz <2024/3/14 上午 11:37>
            @param
            @return dict{"status":True/False,"msg":"提示信息"}
        """
        log_path = "/www/wwwlogs"
        if not os.path.exists(log_path):
            return public.return_message(0, 0, {"log_path": log_path, "size": "0B"})

        path_size = public.to_size(public.get_path_size(log_path))
        size = path_size if path_size else "0B"
        return public.return_message(0, 0, {"log_path": log_path, "size": size})

    # 2024/3/25 上午 10:50 获取防火墙类型，firewall或ufw
    def _get_firewall_type(self) -> str:
        """
            @name 获取防火墙类型，firewall或ufw
            @return str firewall/ufw
        """
        import os
        if os.path.exists('/usr/sbin/ufw'):
            return 'ufw'
        if os.path.exists('/usr/sbin/firewalld'):
            return 'firewall'
        return 'iptables'

    # 2024/3/26 下午 5:01 获取指定域名的A记录
    def get_a_ip(self, domain: str) -> str:
        """
            @name 获取指定域名的A记录
            @param domain: 域名
            @return str
        """
        try:
            import socket
            return socket.gethostbyname(domain)
        except Exception as e:
            return ""

    # 2024/3/26 下午 5:40 检查是否已添加计划任务，如果没有则添加
    def check_resolve_crontab(self):
        """
            @name 检查是否已添加计划任务
            @author wzz <2024/3/26 下午 5:41>
            @param "data":{"参数名":""} <数据类型> 参数描述
            @return dict{"status":True/False,"msg":"提示信息"}
        """
        python_path = "{}/pyenv/bin/python".format(public.get_panel_path())

        if not public.M('crontab').where(
                'name=?',
                ('[Do not delete] system firewall domain name resolution detection tasks',)
        ).count():
            cmd = '{} {}'.format(python_path, '/www/server/panel/script/firewall_domain.py')
            args = {
                "name": "[Do not delete] system firewall domain name resolution detection tasks",
                "type": 'minute-n',
                "where1": '5',
                "hour": '',
                "minute": '',
                "sName": "",
                "sType": 'toShell',
                "notice": '',
                "notice_channel": '',
                "save": '',
                "save_local": '1',
                "backupTo": '',
                "sBody": cmd,
                "urladdress": ''
            }
            import crontab
            res = crontab.crontab().AddCrontab(args)
            if res and "id" in res.keys():
                return True
            return False
        return True

    # 2024/3/26 下午 11:37 当没有域名解析时，删除域名解析的计划任务
    def remove_resolve_crontab(self):
        """
            @name 当没有域名解析时，删除域名解析的计划任务
            @author wzz <2024/3/26 下午 11:37>
            @param "data":{"参数名":""} <数据类型> 参数描述
            @return dict{"status":True/False,"msg":"提示信息"}
        """

        if not public.M('firewall_domain').count():
            pdata = public.M('crontab').where(
                'name=?',
                '[Do not delete] system firewall domain name resolution detection tasks'
            ).select()
            if pdata:
                import crontab
                for i in pdata:
                    args = {"id": i['id']}
                    crontab.crontab().DelCrontab(args)

    # 2024/3/26 下午 6:22 端口扫描
    def CheckPort(self, port, protocol):
        """
            @name 端口扫描
            @author wzz <2024/3/26 下午 6:22>
            @param "data":{"参数名":""} <数据类型> 参数描述
            @return dict{"status":True/False,"msg":"提示信息"}
        """
        import socket
        localIP = '127.0.0.1'
        temp = {}
        temp['port'] = port
        temp['local'] = True

        try:
            if 'tcp' in protocol.lower():
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                s.settimeout(0.01)
                s.connect((localIP, port))
                s.close()
            if 'udp' in protocol.lower():
                s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                s.settimeout(0.01)
                s.sendto(b'', (localIP, port))
                s.close()
        except:
            temp['local'] = False

        result = 0
        if temp['local']: result += 2
        return result

    # 2024/12/18 11:06 构造返回的分页数据
    def return_page(self, data, get):
        """
            @name 构造返回的分页数据
        """
        count = len(data)
        if count == 0:
            return {'data': [], 'count': 0, 'p': 1, 'row': int(get.row)}

        result = public.get_page(count, int(get.p), int(get.row))
        result['data'] = data[(int(get.p) - 1) * int(get.row):(int(get.p)) * int(get.row)]

        return result
