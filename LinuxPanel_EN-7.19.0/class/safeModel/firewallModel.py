# coding: utf-8
# -------------------------------------------------------------------
# aaPanel
# -------------------------------------------------------------------
# Copyright (c) 2015-2099 aaPanel(www.aapanel.com) All rights reserved.
# -------------------------------------------------------------------
# Author: hwliang <hwl@aapanel.com>
# -------------------------------------------------------------------

# 系统防火墙
# ------------------------------
import sys, os, json, re, time, sqlite3
import contextlib
import traceback
from types import coroutine
from xml.etree.ElementTree import ElementTree, Element
from safeModel.base import safeBase
from flask import send_file, abort

os.chdir("/www/server/panel")
sys.path.append("class/")
import public


class main(safeBase):
    __isFirewalld = False
    __isUfw = False
    __firewall_obj = None
    _add_sid = 0
    _ip_list = []
    _port_list = []
    _ufw_default = '/etc/default/ufw'
    _ufw_sysctl = '/etc/ufw/sysctl.conf'
    _ufw_before = '/etc/ufw/before.rules'

    _trans_status = "/www/server/panel/plugin/firewall/status.json"
    _rule_path = "/www/server/panel/plugin/firewall/"
    _ips_path = "/www/server/panel/plugin/firewall/ips.txt"
    _country_path = "/www/server/panel/plugin/firewall/country.txt"
    _white_list_file = "/www/server/panel/plugin/firewall/whitelist.txt"  # 证书验证IP

    _white_list = []
    _firewall_create_tip = '{}/data/firewall_sqlite.pl'.format(
        public.get_panel_path())

    def __init__(self):
        self.__firewall_obj = firewalld()
        if os.path.exists('/usr/sbin/firewalld') and os.path.exists('/usr/bin/yum'):
            self.__isFirewalld = True
        if os.path.exists('/usr/sbin/ufw') and os.path.exists('/usr/bin/apt-get'):
            self.__isUfw = True
            # self.__ufw = '/usr/sbin/ufw'
        self.get_old_rule()

        if not os.path.exists(self._trans_status):
            ret = {"status": "close"}
            public.writeFile(self._trans_status, json.dumps(ret))

        if not os.path.exists(self._firewall_create_tip):
            Sqlite()
            public.writeFile(self._firewall_create_tip, '')

    def get_old_rule(self):
        """
        @兼容防火墙插件规则
        """

        self._rule_path = self._rule_path.replace('plugin', 'data')
        if not os.path.exists(self._rule_path): os.makedirs(self._rule_path)

        if os.path.exists(self._trans_status):
            n_path = self._trans_status.replace('plugin', 'data')
            if not os.path.exists(n_path):
                public.writeFile(n_path, public.readFile(self._trans_status))

        if os.path.exists(self._ips_path):
            n_path = self._ips_path.replace('plugin', 'data')
            if not os.path.exists(n_path):
                public.writeFile(n_path, public.readFile(self._ips_path))

        if os.path.exists(self._white_list_file):
            n_path = self._white_list_file.replace('plugin', 'data')
            if not os.path.exists(n_path):
                public.writeFile(n_path,
                                 public.readFile(self._white_list_file))

        if os.path.exists(self._country_path):
            n_path = self._country_path.replace('plugin', 'data')
            if not os.path.exists(n_path):
                public.writeFile(n_path, public.readFile(self._country_path))

        self._white_list_file = self._white_list_file.replace('plugin', 'data')
        self._country_path = self._country_path.replace('plugin', 'data')
        self._ips_path = self._ips_path.replace('plugin', 'data')
        self._trans_status = self._trans_status.replace('plugin', 'data')

    def install_sys_firewall(self, get):
        """
        @安装系统防火墙
        """

        res = public.install_sys_firewall()
        if res:
            return public.returnMsg(True, public.lang("Successful installation"))
        return public.returnMsg(False, public.lang("installation failed"))

    def get_firewall_info(self, get):
        """
        @name 获取防火墙统计
        """
        data = {}
        data['port'] = public.M('firewall_new').count()
        data['ip'] = public.M('firewall_ip').count()
        data['trans'] = public.M('firewall_trans').count()
        data['country'] = public.M('firewall_country').count()

        isPing = True
        try:
            file = '/etc/sysctl.conf'
            conf = public.readFile(file)
            rep = r"#*net\.ipv4\.icmp_echo_ignore_all\s*=\s*([0-9]+)\n"
            tmp = re.search(rep, conf).groups(0)[0]
            if tmp == '1': isPing = False
        except:
            isPing = True

        data['ping'] = isPing
        data['status'] = self.get_firewall_status()
        return data

    # 服务状态获取
    def get_firewall_status(self):
        if self.__isUfw:
            res = public.ExecShell("systemctl is-active ufw")[0]
            if res == "active":
                return True

            res = public.ExecShell("systemctl list-units | grep ufw")[0]
            if res.find('active running') != -1:
                return True

            res = public.ExecShell('/lib/ufw/ufw-init status')[0]
            if res.find("Firewall is not running") != -1:
                return False

            res = public.ExecShell('ufw status verbose')[0]
            if res.find('inactive') != -1:
                return False

            return True

        if self.__isFirewalld:
            res = public.ExecShell("ps -ef|grep firewalld|grep -v grep")[0]
            if res:
                return True

            res = public.ExecShell("systemctl is-active firewalld")[0]
            if res == "active":
                return True

            res = public.ExecShell("systemctl list-units | grep firewalld")[0]
            if res.find('active running') != -1:
                return True
            return False

        else:
            res = public.ExecShell("/etc/init.d/iptables status")[0]
            if res.find('not running') != -1:
                return False

            res = public.ExecShell("systemctl is-active iptables")[0]
            if res == "active": return True
            return True


    def SetPing(self, get):
        if get.status == '1':
            get.status = '0'
        else:
            get.status = '1'
        filename = '/etc/sysctl.conf'
        conf = public.readFile(filename)
        if conf.find('net.ipv4.icmp_echo') != -1:
            rep = r"net\.ipv4\.icmp_echo.*"
            conf = re.sub(rep, 'net.ipv4.icmp_echo_ignore_all=' + get.status + "\n", conf)
        else:
            conf += "\nnet.ipv4.icmp_echo_ignore_all=" + get.status + "\n"

        if public.writeFile(filename, conf):
            public.ExecShell('sysctl -p')
            return public.returnMsg(True, public.lang("SUCCESS"))
        else:
            return public.returnMsg(
                False,
                # '<a style="color:red;">错误：设置失败，sysctl.conf不可写!</a><br>'
                # '1、如果安装了[宝塔系统加固]，请先关闭<br>'
                # '2、如果安装了云锁，请关闭[系统加固]功能<br>'
                # '3、如果安装了安全狗，请关闭[系统防护]功能<br>'
                # '4、如果使用了其它安全软件，请先卸载<br>'
                '<a style="color:red;">Error: Setting failed, sysctl.conf is not writable!</a><br>'
                '1. If [System Hardening] is installed, please close it first<br>'
                '2. If Cloud Lock is installed, please turn off the [System Hardening] function<br>'
                '3. If a security dog is installed, please turn off the [System Protection] function<br>'
                '4. If you use other security software, please uninstall it first<br>'
            )


    # 服务状态控制
    def firewall_admin(self, get):
        order = ['reload', 'restart', 'stop', 'start']
        if not get.status in order:
            return public.returnMsg(False, public.lang("unknown control command!"))
        names = ["reload", "restart", "stop", "start"]
        result = dict(zip(order, names))
        if self.__isUfw:
            if get.status == "stop":
                public.ExecShell('/usr/sbin/ufw disable')
            elif get.status == "start":
                public.ExecShell('echo y|/usr/sbin/ufw enable')
            elif get.status == "reload":
                public.ExecShell('/usr/sbin/ufw reload')
            elif get.status == "restart":
                public.ExecShell('/usr/sbin/ufw disable && /usr/sbin/ufw enable')

            # ufw防火墙启动时重载一次sysctl
            # 解决deian系统启动ufw后禁ping失1效 by wzz/2023-06-14
            filename = '/etc/sysctl.conf'
            conf = public.readFile(filename)
            if conf.find('net.ipv4.icmp_echo') != -1:
                public.ExecShell("sysctl -p")
            public.WriteLog("system firewall", "firewall {}".format(result[get.status]))
            return public.returnMsg(True, public.lang("firewall has {}", result[get.status]))
        if self.__isFirewalld:
            public.ExecShell('systemctl {} firewalld'.format(get.status))
            public.WriteLog("system firewall", "firewall {}".format(result[get.status]))
            return public.returnMsg(True, public.lang("firewall has {}", result[get.status]))
        else:
            public.ExecShell('service iptables {}'.format(get.status))
        public.WriteLog("system firewall", "firewall {}".format(result[get.status]))
        return public.returnMsg(True, public.lang("firewall has {}", result[get.status]))


    # 重载防火墙配置
    def FirewallReload(self):
        if self.__isUfw:
            public.ExecShell('/usr/sbin/ufw reload')  # 兼容安装了多个防火墙的情况 hezhihong  # return
            # 解决deian系统启动ufw后禁ping失1效 by wzz/2023-06-14
            filename = '/etc/sysctl.conf'
            conf = public.readFile(filename)
            if conf.find('net.ipv4.icmp_echo') != -1:
                public.ExecShell("sysctl -p")
        if self.__isFirewalld:
            public.ExecShell('firewall-cmd --reload')
        else:
            public.ExecShell('/etc/init.d/iptables save')
            public.ExecShell('/etc/init.d/iptables restart')


    # 端口扫描
    def CheckPort(self, port, protocol):
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


    # 查询入栈规则
    def get_rules_list(self, args):

        if self.__isFirewalld:
            self.__firewall_obj = firewalld()
            self.GetList()
        else:
            self.get_ufw_list()
        try:
            p = 1
            limit = 15
            if 'p' in args: p = args.p
            if 'limit' in args: limit = args.limit

            where = '1=1'
            sql = public.M('firewall_new')

            if hasattr(args, 'query'):
                where = " ports like '%{search}%' or brief like '%{search}%' or address like '%{search}%'".format(
                    search=args.query)

            count = sql.where(where, ()).count()
            data = public.get_page(count, int(p), int(limit))

            data['data'] = sql.where(where, ()).limit('{},{}'.format(data['shift'], data['row'])).order('addtime desc').select()
            res_data = data['data']
            for i in range(len(res_data)):
                if not 'ports' in res_data[i]:
                    res_data[i]['status'] = -1
                    continue
                d = res_data[i]
                _port = d['ports']
                _protocol = d['protocol']
                if _port.find(':') != -1 or _port.find('.') != -1 or _port.find(
                        '-') != -1:
                    d['status'] = -1
                else:
                    d['status'] = self.CheckPort(int(_port), _protocol)
            for i in res_data:
                if 'brief' in i:
                    i['brief'] = public.xsssec(i['brief'])
            return res_data
        except:
            return []


    def check_firewall_rule(self, args):
        """
            @检测防火墙规则
            """
        port = args['port']
        find = public.M('firewall_new').where('ports=?', (str(port),)).find()
        if find:
            return True
        return False


    # 端口检查
    def check_port(self, port_list):
        rep1 = r"^\d{1,5}(:\d{1,5})?$"
        # rep1 = r'^[0-9]|[1-9]\d{1,3}|[1-5]\d{4}|6[0-4]\d{3}|65[0-4]\d{2}|655[0-2]\d|6553[0-5]$'
        for port in port_list:
            if port.find('-') != -1:
                ports = port.split('-')
                if not re.search(rep1, ports[0]):
                    return public.returnMsg(False, public.lang("Port range is incorrect!"))
                if not re.search(rep1, ports[1]):
                    return public.returnMsg(False, public.lang("Port range is incorrect!"))
            elif port.find(':') != -1:
                ports = port.split(':')
                if not re.search(rep1, ports[0]):
                    return public.returnMsg(False, public.lang("Port range is incorrect!"))
                if not re.search(rep1, ports[1]):
                    return public.returnMsg(False, public.lang("Port range is incorrect!"))
            else:
                if not re.search(rep1, port):
                    return public.returnMsg(False, public.lang("Port range is incorrect!"))


    def parse_ip_interval(self, ip_str):
        """解析区间IP

            author: lx
            date: 2022/10/25

            Returns:
                list : IP列表
            """
        ips = []
        try:
            rep2 = r"^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}(\/\d{1,2})?$"
            searchor = re.compile(rep2)
            if ip_str.find("-") != -1:
                pre_ip, end_ip = ip_str.split("-")
                if searchor.search(pre_ip) and searchor.search(end_ip):
                    ips.append(pre_ip)
                    pinx = pre_ip.rfind(".") + 1
                    einx = end_ip.rfind(".") + 1
                    pre = pre_ip[0:pinx]
                    end = end_ip[0:einx]
                    if pre == end:
                        start_num = int(pre_ip[pinx:])
                        end_num = min(int(end_ip[einx:]), 255)
                        for i in range(start_num + 1, end_num):
                            new_ip = pre + str(i)
                            if searchor.search(new_ip):
                                ips.append(new_ip)
                        end_ip = end + str(end_num)
                    ips.append(end_ip)
        except:
            pass
        return ips


    # 判断是否为ipv6网段
    @staticmethod
    def is_ipv6_network_segment_or_ipv6_address(ip_datas: str) -> bool:
        from ipaddress import IPv6Network, IPv6Address
        try:
            tmp_data = IPv6Network(ip_datas)
        except:
            try:
                tmp_data = IPv6Address(ip_datas)
            except:
                return False
        return True


    # 添加入栈规则
    def create_rules2(self, get):
        '''
            get 里面 有  protocol port type address brief   五个参数
            protocol == ['tcp','udp']
            port = 端口
            types == [accept、drop] # 放行和禁止
            address  地址，允许放行的ip，如果全部就是：0.0.0.0/0;另外可以包含“,"或者"-"
            表示区间IP
            brief   备注说明
            '''
        protocol = get.protocol
        ports = get.ports.strip()
        types = get.types
        address = get.source.strip()
        port_list = ports.split(',')
        result = self.check_port(port_list)  # 检测端口
        if result: return result

        allow_ips = []
        if address:
            sources = [
                sip.strip() for sip in address.split(",") if sip.strip()
            ]
            rep2 = r"^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}(\/\d{1,2})?$"
            _ips = []
            for source_ip in sources:
                if source_ip.find("-") != -1:
                    _ips += self.parse_ip_interval(source_ip)
                else:
                    _ips.append(source_ip)

            for source_ip in _ips:
                if not re.search(rep2, source_ip) and not self.is_ipv6_network_segment_or_ipv6_address(source_ip):
                    return public.returnMsg(False, public.lang("IP address you've input is illegal!"))
                allow_ips.append(source_ip)
        if not allow_ips:
            allow_ips.append("")
        for source_ip in allow_ips:
            if self.__isUfw:
                for port in port_list:
                    if port.find('-') != -1:
                        port = port.replace('-', ':')
                    self.add_ufw_rule(source_ip, protocol, port, types)
            else:
                if self.__isFirewalld:
                    for port in port_list:
                        if port.find(':') != -1:
                            port = port.replace(':', '-')
                        self.add_firewall_rule(source_ip, protocol, port,
                                               types)
                else:
                    for port in port_list:
                        self.add_iptables_rule(source_ip, protocol, port, types)


    # 添加入栈规则
    def create_rules(self, get):
        '''
            get 里面 有  protocol port type address brief   五个参数
            protocol == ['tcp','udp']
            port = 端口
            types == [accept、drop] # 放行和禁止
            address  地址，允许放行的ip，如果全部就是：0.0.0.0/0;另外可以包含“,"或者"-"
            表示区间IP
            brief   备注说明
            '''
        protocol = get.protocol
        ports = get.ports.strip()
        types = get.types
        address = get.source.strip()
        brief = get.brief.strip()
        port_list = ports.split(',')
        is_add = 2 if 'add' not in get else get.add
        domain_total = '' if ("domain" not in get or not get.domain) else get.domain.strip()
        domain = '' if ("domain" not in get or not get.domain) else get.domain.strip() + '|' + address
        result = self.check_port(port_list)  # 检测端口
        if result: return result

        allow_ips = []
        if address:
            sources = [sip.strip() for sip in address.split(",") if sip.strip()]
            rep2 = r"^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}(\/\d{1,2})?$"
            _ips = []
            for source_ip in sources:
                if source_ip.find("-") != -1:
                    _ips += self.parse_ip_interval(source_ip)
                else:
                    _ips.append(source_ip)

            for source_ip in _ips:
                if not re.search(rep2, source_ip) and not self.is_ipv6_network_segment_or_ipv6_address(source_ip):
                    return public.returnMsg(False, public.lang("IP address you've input is illegal!"))
                query_result = public.M('firewall_new').where(
                    'ports=? and address=? and protocol=? and types=?',
                    (ports, source_ip, protocol, types,)
                ).count()
                if query_result > 0:
                    continue
                allow_ips.append(source_ip)
        if not allow_ips:
            allow_ips.append("")
        # 忽略的列表
        ignore_list = []
        addtime = time.strftime('%Y-%m-%d %X', time.localtime())
        for source_ip in allow_ips:
            for port in port_list:
                if is_add == 1: continue
                # 检测端口是否已经添加过
                query_result = public.M('firewall_new').where(
                    'ports=? and address=? and protocol=? and types=?',
                    (port, source_ip, protocol, types,)
                ).find()
                firewall_rules = self.get_sys_firewall_rules()
                if query_result:
                    new_query_result = {"ports": query_result["ports"], "address": query_result["address"],
                                        "protocol": query_result["protocol"], "types": query_result["types"]}
                    for firewall_rule in firewall_rules:
                        if new_query_result == firewall_rule:
                            ignore_list.append(port)
                            break

                self._add_firewall_rules(source_ip, protocol, port, types)

                if not query_result:
                    self._add_sid = public.M('firewall_new').add(
                        'ports,brief,protocol,address,types,addtime,domain,sid',
                        (port, public.xsssec(brief), protocol, source_ip, types, addtime, domain, 0)
                    )

                if domain:
                    domain_sid = public.M('firewall_domain').add(
                        'types,domain,port,address,brief,addtime,sid,protocol,domain_total',
                        (types, domain, ports, address, public.xsssec(brief), addtime, self._add_sid, protocol,
                         domain_total)
                    )
                    public.M('firewall_new').where("id=?", (self._add_sid,)).save('sid', domain_sid)
        if len(allow_ips) > 0:
            self.FirewallReload()
        if not get.source.strip():
            log_ip = "All IPs"
        else:
            log_ip = get.source.strip()
        strategy = ''
        if types == 'accept':
            strategy = "accept"
        elif types == 'drop':
            strategy = "drop"
        public.WriteLog("system firewall",
                        "Add port rules: Protocol:{}, Port:{}, Policy:{}, IP:{}".format(protocol, ports, strategy, log_ip))
        # 如果有忽略的端口，返回忽略的端口
        if ignore_list:
            return public.returnMsg(True,
                                    'Added successfully, {} The same rule exists for the port and has been skipped'.format(
                                        ', '.join(ignore_list)))
        return public.returnMsg(True, public.lang("Added successfully!"))


    # 删除入栈规则
    def remove_rules(self, get):
        '''
            get 里面有  id protocol port type address    五个参数
            protocol == ['tcp','udp']
            port = 端口
            types == [accept、drop] # 放行和禁止
            address  地址，允许放行的ip
            '''
        # 检测是否开启防火墙 hezhihong
        if not self.get_firewall_status():
            return public.returnMsg(False, public.lang("Please enable the firewall before proceeding."))

        id = get.id
        address = get.address
        protocol = get.protocol
        ports = get.ports
        types = get.types
        self._del_firewall_rules(address, protocol, ports, types)
        public.M('firewall_new').where("id=?", (id,)).delete()
        self.FirewallReload()
        if not get.address:
            log_ip = "All IPs"
        else:
            log_ip = get.address
        if types == 'accept':
            strategy = "accept"
        elif types == 'drop':
            strategy = "drop"
        public.WriteLog("system firewall",
                        "Delete port rules: Protocol:{}, Port:{}, Policy:{}, IP:{}".format(get.protocol, get.ports, types,
                                                                                           log_ip))
        return public.returnMsg(True, public.lang("Delete successfully!"))


    # 修改入栈规则
    def modify_rules(self, get, addtime=None):
        '''
            get 里面有  id protocol port type address    五个参数
            protocol == ['tcp','udp']
            port = 端口
            types==['reject','accept'] # 放行和禁止
            address  地址，允许放行的ip，如果全部就是：0.0.0.0/0
            '''
        # 检测是否开启防火墙 hezhihong
        if not self.get_firewall_status():
            return public.returnMsg(False, public.lang("Please enable the firewall before proceeding."))
        id = get.id
        protocol = get.protocol
        ports = get.ports.strip()
        types = get.types
        address = get.source.strip()
        brief = get.brief.strip()
        domain = '' if 'domain' not in get else get.domain
        domain_total = domain.split('|')[0]
        sid = 0 if 'sid' not in get else get.sid
        if address:
            rep = r"^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}(\/\d{1,2})?$"
            if not re.search(rep, get.source) and self.is_ipv6_network_segment_or_ipv6_address(get.source):
                return public.returnMsg(False, public.lang("IP address you've input is illegal!"))
        data = public.M('firewall_new').where('id=?', (id,)).field(
            'id,address,protocol,ports,types,brief,addtime,domain'
        ).find()
        if data:
            _address = data.get("address", "")
            _protocol = data.get("protocol", "")
            _port = data.get("ports", "")
            _type = data.get("types", "")
        else:
            _address = _protocol = _port = _type = ""
        self._modify_firewall_rules(_address, _protocol, _port, _type, address, protocol, ports, types)
        addtime = time.strftime('%Y-%m-%d %X', time.localtime())
        public.M('firewall_new').where('id=?', id).update({
            'address': address,
            'protocol': protocol,
            'ports': ports,
            'types': types,
            'brief': brief,
            'addtime': addtime,
            'sid': sid,
            'domain': domain
        }
        )
        if domain:
            public.M('firewall_domain').where("id=?", (sid,)).save(
                'sid,types,brief,protocol,domain_total',
                (id, types, brief, protocol, domain_total)
            )

        with contextlib.suppress(Exception):
            if int(ports) == 22: self.delete_service()
        self.FirewallReload()
        if not address:
            log_ip = "All IPs"
        else:
            log_ip = address
        if get.types == 'accept':
            strategy = "accept"
        elif get.types == 'drop':
            strategy = "drop"
        public.WriteLog("system firewall",
                        "Modify port rules： Protocol:{}, Port:{}, Policy:{}, IP:{}".format(get.protocol, get.ports.strip(), get.types,
                                                                                log_ip))
        return public.returnMsg(True, public.lang("Added successfully!"))


    # firewall端口规则添加
    def add_firewall_rule(self, address, protocol, ports, types):
        if not address:
            if protocol.find('/') != -1:
                if types == "accept":
                    public.ExecShell(
                        'firewall-cmd --permanent --zone=public --add-port=' +
                        ports + '/tcp')
                    public.ExecShell(
                        'firewall-cmd --permanent --zone=public --add-port=' +
                        ports + '/udp')
                else:
                    public.ExecShell(
                        'firewall-cmd --permanent --add-rich-rule="rule family=ipv4 port protocol="tcp" port="%s" drop"'
                        % ports
                    )
                    public.ExecShell(
                        'firewall-cmd --permanent --add-rich-rule="rule family=ipv4 port protocol="udp" port="%s" drop"'
                        % ports
                    )
            else:
                if types == "accept":
                    public.ExecShell(
                        'firewall-cmd --permanent --zone=public --add-port=' +
                        ports + '/' + protocol + '')
                else:
                    public.ExecShell(
                        'firewall-cmd --permanent --add-rich-rule="rule family=ipv4 port protocol="%s" port="%s" drop"'
                        % (protocol, ports))
            return True
        if self.is_ipv6_network_segment_or_ipv6_address(address):
            if protocol.find('/') != -1:
                public.ExecShell(
                    'firewall-cmd --permanent '
                    '--add-rich-rule="rule family=ipv6 source address="%s" port protocol="tcp" port="%s" %s"'
                    % (address, ports, types))
                public.ExecShell(
                    'firewall-cmd --permanent '
                    '--add-rich-rule="rule family=ipv6 source address="%s" port protocol="udp" port="%s" %s"'
                    % (address, ports, types))
            else:
                public.ExecShell(
                    'firewall-cmd --permanent '
                    '--add-rich-rule="rule family=ipv6 source address="%s" port protocol="%s" port="%s" %s"'
                    % (address, protocol, ports, types))
        else:
            if protocol.find('/') != -1:
                public.ExecShell(
                    'firewall-cmd --permanent '
                    '--add-rich-rule="rule family=ipv4 source address="%s" port protocol="tcp" port="%s" %s"'
                    % (address, ports, types))
                public.ExecShell(
                    'firewall-cmd --permanent '
                    '--add-rich-rule="rule family=ipv4 source address="%s" port protocol="udp" port="%s" %s"'
                    % (address, ports, types))
            else:
                public.ExecShell(
                    'firewall-cmd --permanent '
                    '--add-rich-rule="rule family=ipv4 source address="%s" port protocol="%s" port="%s" %s"'
                    % (address, protocol, ports, types))
        return True


    # firewall端口规则删除
    def del_firewall_rule(self, address, protocol, ports, types):
        if not address:
            if protocol.find('/') != -1:
                if types == "accept":
                    public.ExecShell(
                        'firewall-cmd --permanent --zone=public --remove-port='
                        + ports + '/tcp')
                    public.ExecShell(
                        'firewall-cmd --permanent --zone=public --remove-port='
                        + ports + '/udp')
                else:
                    public.ExecShell(
                        'firewall-cmd --permanent '
                        '--remove-rich-rule="rule family=ipv4 port protocol="tcp" port="%s" drop"'
                        % ports
                    )
                    public.ExecShell(
                        'firewall-cmd --permanent '
                        '--remove-rich-rule="rule family=ipv4 port protocol="udp" port="%s" drop"'
                        % ports
                    )
            else:
                if types == "accept":
                    public.ExecShell(
                        'firewall-cmd --permanent --zone=public --remove-port='
                        + ports + '/' + protocol + '')
                else:
                    public.ExecShell(
                        'firewall-cmd --permanent '
                        '--remove-rich-rule="rule family=ipv4 port protocol="%s" port="%s" drop"'
                        % (protocol, ports))
            self.update_panel_data(ports)
            return True
        if self.is_ipv6_network_segment_or_ipv6_address(address):
            if protocol.find('/') != -1:
                public.ExecShell(
                    'firewall-cmd --permanent '
                    '--remove-rich-rule="rule family="ipv6" source address="%s" port protocol="tcp" port="%s" %s"'
                    % (address, ports, types))
                public.ExecShell(
                    'firewall-cmd --permanent '
                    '--remove-rich-rule="rule family="ipv6" source address="%s" port protocol="udp" port="%s" %s"'
                    % (address, ports, types))
            else:
                public.ExecShell(
                    'firewall-cmd --permanent '
                    '--remove-rich-rule="rule family="ipv6" source address="%s" port protocol="%s" port="%s" %s"'
                    % (address, protocol, ports, types))
        else:
            if protocol.find('/') != -1:
                public.ExecShell(
                    'firewall-cmd --permanent '
                    '--remove-rich-rule="rule family="ipv4" source address="%s" port protocol="tcp" port="%s" %s"'
                    % (address, ports, types))
                public.ExecShell(
                    'firewall-cmd --permanent '
                    '--remove-rich-rule="rule family="ipv4" source address="%s" port protocol="udp" port="%s" %s"'
                    % (address, ports, types))
            else:
                public.ExecShell(
                    'firewall-cmd --permanent '
                    '--remove-rich-rule="rule family="ipv4" source address="%s" port protocol="%s" port="%s" %s"'
                    % (address, protocol, ports, types))
        return True


    # firewall端口规则编辑
    def edit_firewall_rule(self, _address, _protocol, _port, _type, address,
                           protocol, ports, types):
        if not _address:
            if _protocol.find('/') != -1:
                if _type == "accept":
                    public.ExecShell(
                        'firewall-cmd --permanent --zone=public --remove-port='
                        + _port + '/tcp')
                    public.ExecShell(
                        'firewall-cmd --permanent --zone=public --remove-port='
                        + _port + '/udp')
                else:
                    public.ExecShell(
                        'firewall-cmd --permanent '
                        '--remove-rich-rule="rule family=ipv4 port protocol="tcp" port="%s" drop"'
                        % ports
                    )
                    public.ExecShell(
                        'firewall-cmd --permanent '
                        '--remove-rich-rule="rule family=ipv4 port protocol="udp" port="%s" drop"'
                        % ports
                    )
            else:
                if _type == "accept":
                    public.ExecShell(
                        'firewall-cmd --permanent --zone=public --remove-port='
                        + _port + '/' + _protocol + '')
                else:
                    public.ExecShell(
                        'firewall-cmd --permanent '
                        '--remove-rich-rule="rule family=ipv4 port protocol="%s" port="%s" drop"'
                        % (protocol, ports))
        else:
            if self.is_ipv6_network_segment_or_ipv6_address(address):
                if _protocol.find('/') != -1:
                    public.ExecShell(
                        'firewall-cmd --permanent '
                        '--remove-rich-rule="rule family="ipv6" source address="%s" port protocol="tcp" port="%s" %s"'
                        % (_address, _port, _type))
                    public.ExecShell(
                        'firewall-cmd --permanent '
                        '--remove-rich-rule="rule family="ipv6" source address="%s" port protocol="udp" port="%s" %s"'
                        % (_address, _port, _type))
                else:
                    public.ExecShell(
                        'firewall-cmd --permanent '
                        '--remove-rich-rule="rule family="ipv6" source address="%s" port protocol="%s" port="%s" %s"'
                        % (_address, _protocol, _port, _type))
            else:
                if _protocol.find('/') != -1:
                    public.ExecShell(
                        'firewall-cmd --permanent '
                        '--remove-rich-rule="rule family="ipv4" source address="%s" port protocol="tcp" port="%s" %s"'
                        % (_address, _port, _type))
                    public.ExecShell(
                        'firewall-cmd --permanent '
                        '--remove-rich-rule="rule family="ipv4" source address="%s" port protocol="udp" port="%s" %s"'
                        % (_address, _port, _type))
                else:
                    public.ExecShell(
                        'firewall-cmd --permanent '
                        '--remove-rich-rule="rule family="ipv4" source address="%s" port protocol="%s" port="%s" %s"'
                        % (_address, _protocol, _port, _type))
        if not address:
            if protocol.find('/') != -1:
                if types == "accept":
                    public.ExecShell(
                        'firewall-cmd --permanent --zone=public --add-port=' +
                        ports + '/tcp')
                    public.ExecShell(
                        'firewall-cmd --permanent --zone=public --add-port=' +
                        ports + '/udp')
                else:
                    public.ExecShell(
                        'firewall-cmd --permanent '
                        '--add-rich-rule="rule family=ipv4 port protocol="tcp" port="%s" drop"'
                        % ports
                    )
                    public.ExecShell(
                        'firewall-cmd --permanent '
                        '--add-rich-rule="rule family=ipv4 port protocol="udp" port="%s" drop"'
                        % ports
                    )
            else:
                if types == "accept":
                    public.ExecShell(
                        'firewall-cmd --permanent --zone=public --add-port=' +
                        ports + '/' + protocol + '')
                else:
                    public.ExecShell(
                        'firewall-cmd --permanent '
                        '--add-rich-rule="rule family=ipv4 port protocol="%s" port="%s" drop"'
                        % (protocol, ports))
        else:
            if self.is_ipv6_network_segment_or_ipv6_address(address):
                if protocol.find('/') != -1:
                    public.ExecShell(
                        'firewall-cmd --permanent '
                        '--add-rich-rule="rule family=ipv6 source address="%s" port protocol="tcp" port="%s" %s"'
                        % (address, ports, types))
                    public.ExecShell(
                        'firewall-cmd --permanent '
                        '--add-rich-rule="rule family=ipv6 source address="%s" port protocol="udp" port="%s" %s"'
                        % (address, ports, types))
                else:
                    public.ExecShell(
                        'firewall-cmd --permanent '
                        '--add-rich-rule="rule family=ipv6 source address="%s" port protocol="%s" port="%s" %s"'
                        % (address, protocol, ports, types))
            else:
                if protocol.find('/') != -1:
                    public.ExecShell(
                        'firewall-cmd --permanent '
                        '--add-rich-rule="rule family=ipv4 source address="%s" port protocol="tcp" port="%s" %s"'
                        % (address, ports, types))
                    public.ExecShell(
                        'firewall-cmd --permanent '
                        '--add-rich-rule="rule family=ipv4 source address="%s" port protocol="udp" port="%s" %s"'
                        % (address, ports, types))
                else:
                    public.ExecShell(
                        'firewall-cmd --permanent '
                        '--add-rich-rule="rule family=ipv4 source address="%s" port protocol="%s" port="%s" %s"'
                        % (address, protocol, ports, types))
        return True


    # ufw 端口规则添加
    def add_ufw_rule(self, address, protocol, ports, types):
        rule = "allow" if types == "accept" else "deny"
        if address == "":
            if protocol.find('/') != -1:
                # public.ExecShell('ufw ' + rule + ' ' + ports + '/tcp')
                # public.ExecShell('ufw ' + rule + ' ' + ports + '/udp')
                public.ExecShell('ufw ' + rule + ' ' + ports)
            else:
                public.ExecShell('ufw ' + rule + ' ' + ports + '/' + protocol + '')
        else:
            if protocol.find('/') != -1:
                # public.ExecShell('ufw ' + rule + ' proto tcp from ' + address + ' to any port ' + ports + '')
                # public.ExecShell('ufw ' + rule + ' proto udp from ' + address + ' to any port ' + ports + '')
                public.ExecShell('ufw ' + rule + ' from ' + address + ' to any port ' + ports + '')
            else:
                public.ExecShell(
                    'ufw ' + rule + ' proto ' + protocol + ' from ' + address + ' to any port ' + ports + '')


    # ufw 端口规则删除
    def del_ufw_rule(self, address, protocol, ports, types):
        rule = "allow" if types == "accept" else "deny"
        if address == "":
            if protocol.find('/') != -1:
                public.ExecShell('ufw delete ' + rule + ' ' + ports + '/tcp')
                public.ExecShell('ufw delete ' + rule + ' ' + ports + '/udp')
                public.ExecShell('ufw delete ' + rule + ' ' + ports)
            else:
                public.ExecShell('ufw delete ' + rule + ' ' + ports + '/' + protocol + '')
        else:
            if protocol.find('/') != -1:
                public.ExecShell('ufw delete ' + rule + ' proto tcp from ' + address + ' to any port ' + ports + '')
                public.ExecShell('ufw delete ' + rule + ' proto udp from ' + address + ' to any port ' + ports + '')
                public.ExecShell('ufw delete ' + rule + ' from ' + address + ' to any port ' + ports)
            else:
                public.ExecShell(
                    'ufw delete ' + rule + ' proto ' + protocol + ' from ' + address + ' to any port ' + ports + ''
                )
        self.update_panel_data(ports)


    # ufw 端口规则修改
    def edit_ufw_rule(self, _address, _protocol, _port, _type, address,
                      protocol, ports, types):
        _rule = "allow" if _type == "accept" else "deny"
        rules = "allow" if types == "accept" else "deny"
        if _address == "":
            if _protocol.find('/') != -1:
                public.ExecShell('ufw delete ' + _rule + ' ' + _port + '/tcp')
                public.ExecShell('ufw delete ' + _rule + ' ' + _port + '/udp')
                public.ExecShell('ufw delete ' + _rule + ' ' + _port)
            else:
                public.ExecShell('ufw delete ' + _rule + ' ' + _port + '/' + _protocol + '')
        else:
            if _protocol.find('/') != -1:
                public.ExecShell('ufw delete ' + _rule + ' proto tcp from ' + _address + ' to any port ' + _port + '')
                public.ExecShell('ufw delete ' + _rule + ' proto udp from ' + _address + ' to any port ' + _port + '')
                public.ExecShell('ufw delete ' + _rule + ' from ' + _address + ' to any port ' + _port)
            else:
                public.ExecShell(
                    'ufw delete ' + _rule + ' proto ' + _protocol + ' from ' + _address + ' to any port ' + _port + ''
                )
        if address == "":
            if protocol.find('/') != -1:
                # public.ExecShell('ufw ' + rules + ' ' + ports + '/tcp')
                # public.ExecShell('ufw ' + rules + ' ' + ports + '/udp')
                public.ExecShell('ufw ' + rules + ' ' + ports)
            else:
                public.ExecShell('ufw ' + rules + ' ' + ports + '/' + protocol + '')
        else:
            if protocol.find('/') != -1:
                # public.ExecShell('ufw ' + rules + ' proto tcp from ' + address + ' to any port ' + ports + '')
                # public.ExecShell('ufw ' + rules + ' proto udp from ' + address + ' to any port ' + ports + '')
                public.ExecShell('ufw ' + rules + ' from ' + address + ' to any port ' + ports)
            else:
                public.ExecShell(
                    'ufw ' + rules + ' proto ' + protocol + ' from ' + address + ' to any port ' + ports + ''
                )


    # iptables端口规则添加
    def add_iptables_rule(self, address, protocol, ports, types):
        rule = "ACCEPT" if types == "accept" else "DROP"
        if not address:
            if protocol.find('/') != -1:
                public.ExecShell(
                    'iptables -I INPUT -p tcp -m state --state NEW -m tcp --dport '
                    + ports + ' -j ' + rule + '')
                public.ExecShell(
                    'iptables -I INPUT -p tcp -m state --state NEW -m udp --dport '
                    + ports + ' -j ' + rule + '')
            else:
                public.ExecShell(
                    'iptables -I INPUT -p tcp -m state --state NEW -m ' +
                    protocol + ' --dport ' + ports + ' -j ' + rule + '')
        else:
            if protocol.find('/') != -1:
                public.ExecShell('iptables -I INPUT -s ' + address +
                                 ' -p tcp --dport ' + ports + ' -j ' + rule +
                                 '')
                public.ExecShell('iptables -I INPUT -s ' + address +
                                 ' -p udp --dport ' + ports + ' -j ' + rule +
                                 '')
            else:
                public.ExecShell('iptables -I INPUT -s ' + address + ' -p ' +
                                 protocol + ' --dport ' + ports + ' -j ' +
                                 rule + '')
        return True


    # iptables端口规则删除
    def del_iptables_rule(self, address, protocol, ports, types):
        rule = "ACCEPT" if types == "accept" else "DROP"
        if not address:
            if protocol.find('/') != -1:
                public.ExecShell(
                    'iptables -D INPUT -p tcp -m state --state NEW -m tcp --dport '
                    + ports + ' -j ' + rule + '')
                public.ExecShell(
                    'iptables -D INPUT -p tcp -m state --state NEW -m udp --dport '
                    + ports + ' -j ' + rule + '')
            else:
                public.ExecShell(
                    'iptables -D INPUT -p tcp -m state --state NEW -m ' +
                    protocol + ' --dport ' + ports + ' -j ' + rule + '')
        else:
            if protocol.find('/') != -1:
                public.ExecShell('iptables -D INPUT -s ' + address +
                                 ' -p tcp --dport ' + ports + ' -j ' + rule +
                                 '')
                public.ExecShell('iptables -D INPUT -s ' + address +
                                 ' -p udp --dport ' + ports + ' -j ' + rule +
                                 '')
            else:
                public.ExecShell('iptables -D INPUT -s ' + address + ' -p ' +
                                 protocol + ' --dport ' + ports + ' -j ' +
                                 rule + '')
        return True


    # iptables端口规则编辑
    def edit_iptables_rule(self, _address, _protocol, _port, _type, address,
                           protocol, ports, types):
        rule1 = "ACCEPT" if _type == "accept" else "DROP"
        rule2 = "ACCEPT" if types == "accept" else "DROP"
        if not _address:
            if _protocol.find('/') != -1:
                public.ExecShell(
                    'iptables -D INPUT -p tcp -m state --state NEW -m tcp --dport '
                    + _port + ' -j ' + rule1 + '')
                public.ExecShell(
                    'iptables -D INPUT -p tcp -m state --state NEW -m udp --dport '
                    + _port + ' -j ' + rule1 + '')
            else:
                public.ExecShell(
                    'iptables -D INPUT -p tcp -m state --state NEW -m ' +
                    _protocol + ' --dport ' + _port + ' -j ' + rule1 + '')
        else:
            if _protocol.find('/') != -1:
                public.ExecShell('iptables -D INPUT -s ' + _address +
                                 ' -p tcp --dport ' + _port + ' -j ' + rule1 +
                                 '')
                public.ExecShell('iptables -D INPUT -s ' + _address +
                                 ' -p udp --dport ' + _port + ' -j ' + rule1 +
                                 '')
            else:
                public.ExecShell('iptables -D INPUT -s ' + _address + ' -p ' +
                                 _protocol + ' --dport ' + _port + ' -j ' +
                                 rule1 + '')
        if not address:
            if protocol.find('/') != -1:
                public.ExecShell(
                    'iptables -I INPUT -p tcp -m state --state NEW -m tcp --dport '
                    + ports + ' -j ' + rule2 + '')
                public.ExecShell(
                    'iptables -I INPUT -p tcp -m state --state NEW -m udp --dport '
                    + ports + ' -j ' + rule2 + '')
            else:
                public.ExecShell(
                    'iptables -I INPUT -p tcp -m state --state NEW -m ' +
                    protocol + ' --dport ' + ports + ' -j ' + rule2 + '')
        else:
            if protocol.find('/') != -1:
                public.ExecShell('iptables -I INPUT -s ' + address +
                                 ' -p tcp --dport ' + ports + ' -j ' + rule2 +
                                 '')
                public.ExecShell('iptables -I INPUT -s ' + address +
                                 ' -p udp --dport ' + ports + ' -j ' + rule2 +
                                 '')
            else:
                public.ExecShell('iptables -I INPUT -s ' + address + ' -p ' +
                                 protocol + ' --dport ' + ports + ' -j ' +
                                 rule2 + '')
        return True


    # 修改面板数据
    def update_panel_data(self, ports):
        res = public.M('firewall').where("port=?", (ports,)).delete()


    # 查询IP规则
    def get_ip_rules_list(self, args):
        p = 1
        limit = 15
        if 'p' in args: p = args.p
        if 'limit' in args: limit = args.limit

        where = '1=1'
        sql = public.M('firewall_ip')

        if hasattr(args, 'query'):
            where = " address like '%{search}%' or brief like '%{search}%' ".format(
                search=args.query)

        count = sql.where(where, ()).count()
        data = public.get_page(count, int(p), int(limit))
        data['data'] = sql.where(where, ()).limit('{},{}'.format(
            data['shift'], data['row'])).order('addtime desc').select()

        data['data'] = public.return_area(data['data'], 'address')
        return data


    def check_a_ip(self, address):
        """
            @name 检测A记录是否为域名
            @author hezhihong
            """
        if address:
            if public.is_ipv4(address) or public.is_ipv6(address):
                return address
            if address[-1] == '.':
                address = address[:-1]
            if public.is_domain(address): return self.get_a_ip(address)
        return address


    def get_a_ip(self, hostname):
        '''
            @name 检测主机名是否有A记录
            @author hezhihong
            :param hostname:
            :return:
            '''
        if not self.install_dnspython():
            return public.returnMsg(False, public.lang("Please install dnspython module first: btpip install dnspython"))
        import dns.resolver
        # 尝试3次
        a_ip = []
        for i in range(3):
            try:
                resolver = dns.resolver.Resolver()
                resolver.timeout = 1
                try:
                    result = resolver.query(hostname, 'A')
                except:
                    result = resolver.resolve(hostname, 'A')
                for i in result.response.answer:
                    for j in i.items:
                        try:
                            A_ip = str(j).strip()
                            if A_ip[-1] == '.':
                                A_ip = A_ip[:-1]
                        except:
                            pass

                        if A_ip not in a_ip:
                            a_ip.append(A_ip)

            except:
                pass

        # 去除域名
        if len(a_ip) > 1:
            for i2 in a_ip:
                if public.is_ipv4(i2) or public.is_ipv6(i2):
                    continue
                if public.is_domain(i2):
                    a_ip.remove(i2)
        return a_ip


    def install_dnspython(self):
        """
            @name 安装dnspython模块
            @author hezhihong
            """
        # 检测dns解析
        try:
            import dns.resolver
            return True
        except:
            if os.path.exists('/www/server/panel/pyenv'):
                public.ExecShell('/www/server/panel/pyenv/bin/pip install dnspython')
            else:
                public.ExecShell('pip3 install dnspython')
            try:
                import dns.resolver
                return True
            except:
                return False


    def del_domain_ip(self, args):
        """
            @name 删除域名设置
            @author hezhihong
            """

        if 'id' not in args or not args.id or 'sid' not in args:
            return public.returnMsg(False, public.lang("Parameter error"))
        domain_id = int(args.sid)

        # 删除IP规则
        if domain_id > 0:
            # 删除域名解析
            public.M('firewall_domain').where('id=?', (str(domain_id),)).delete()
        # 删除端口规则
        if 'ports' in args:
            self.remove_rules(args)
        # 删除IP规则
        else:
            self.remove_ip_rules(args)

        # 当没有域名解析时，删除计划任务
        if not public.M('firewall_domain').count():
            pdata = public.M('crontab').where('name=?',
                                              '[Do not delete] System firewall domain name resolution detection task').select()
            if pdata:
                for i in pdata:
                    args = {"id": i['id']}
                    import crontab
                    crontab.crontab().DelCrontab(args)

        return public.returnMsg(True, public.lang("successfully deleted"))


    def add_crontab(self):
        """
            @name 构造日志切割任务
            @author hezhihong
            """
        python_path = ''
        try:
            python_path = public.ExecShell('which btpython')[0].strip("\n")
        except:
            try:
                python_path = public.ExecShell('which python')[0].strip("\n")
            except:
                pass
        if not python_path: return False
        if not public.M('crontab').where('name=?', (
        '[Do not delete] System firewall domain name resolution detection task',)).count():
            cmd = '{} {}'.format(python_path, '/www/server/panel/script/firewall_domain.py')
            args = {"name": "[Do not delete] System firewall domain name resolution detection task", "type": 'minute-n',
                    "where1": '5', "hour": '',
                    "minute": '', "sName": "",
                    "sType": 'toShell', "notice": '', "notice_channel": '', "save": '', "save_local": '1',
                    "backupTo": '', "sBody": cmd,
                    "urladdress": ''}
            import crontab
            res = crontab.crontab().AddCrontab(args)
            if res and "id" in res.keys():
                return True
            return False
        return True


    def __check_auth(self):
        try:
            from pluginAuth import Plugin
            plugin_obj = Plugin(False)
            plugin_list = plugin_obj.get_plugin_list()
            if int(plugin_list['ltd']) > time.time():
                return True
            return False
        except:
            return False


    def set_domain_ip2(self, args):
        """
            @name 设置域名规则
            @author hezhihong
            """
        pay = self.__check_auth()
        if not pay: return public.returnMsg(False, public.lang("Current features are exclusive to the professional version"))
        if not args.domain: return public.returnMsg(False, public.lang("Please enter domain name"))
        ports = ''
        if 'ports' in args and args.ports: ports = args.ports
        ip = args.source

        # 添加计划任务
        self.add_crontab()
        # 添加端口规则
        # {"protocol":"tcp","ports":"819","choose":"point","address":"125.93.252.236","types":"accept","brief":"","source":"125.93.252.236"}
        args.address = ip
        args.source = ip
        if ports:
            if public.is_ipv6(ip):
                return public.returnMsg(False, public.lang("The domain name is resolved to an IPv6 address and port rules are not supported."))
            self.create_rules2(args)
        # 添加IP规则
        else:
            # return 333
            self.create_ip_rules(args)

        return public.returnMsg(True, public.lang("Domain name {} resolution added successfully", args.domain))


    def set_domain_ip(self, args):
        """
            @name 设置域名规则
            @author hezhihong
            """
        pay = self.__check_auth()
        if not pay: return public.returnMsg(False, public.lang("Current features are exclusive to the professional version"))
        if not args.domain: return public.returnMsg(False, public.lang("Please enter domain name"))
        ports = ''
        if 'ports' in args and args.ports: ports = args.ports
        protocol = '' if 'protocol' not in args else args.protocol
        a_ip = self.get_a_ip(args.domain)
        # return a_ip
        if a_ip and len(a_ip) < 2 and public.is_domain(a_ip[0]):
            # return 111
            a_ip = [self.check_a_ip(a_ip[0])]
        # return a_ip
        if not a_ip:
            return public.returnMsg(False, public.lang("The domain name resolution has not been resolved or the resolution has not taken effect. If it has been resolved, please try again after 10 minutes."))
        if public.M('firewall_domain').where("domain=? and types=? and port=? and protocol=?",
                                             (args.domain, args.types, ports, protocol,)).count():
            return public.returnMsg(False, public.lang("Domain name {} already exists", args.domain))

        # 添加计划任务
        self.add_crontab()
        # 添加端口规则
        # {"protocol":"tcp","ports":"819","choose":"point","address":"125.93.252.236","types":"accept","brief":"","source":"125.93.252.236"}
        for ip in a_ip:
            args.address = ip
            args.source = ip
            if ports:
                if public.is_ipv6(ip):
                    return public.returnMsg(False, public.lang("The domain name is resolved to an IPv6 address and port rules are not supported."))
                self.create_rules(args)
            # 添加IP规则
            else:
                # return 333
                self.create_ip_rules(args)

        return public.returnMsg(True, public.lang("Domain name {} resolution added successfully", args.domain))


    def modify_domain_ip(self, args):
        """
            @name 修改域名规则(当修改为指定域名或从指定域名修改为其他时，需要调用此方法)
            @name hezhihong
            """
        pay = self.__check_auth()
        if not pay: return public.returnMsg(False, public.lang("Current features are exclusive to the professional version"))

        # 检测是否开启防火墙 hezhihong
        if not self.get_firewall_status():
            return public.returnMsg(False, public.lang("Please enable the firewall before proceeding."))

        modify_args = public.dict_obj()
        modify_args.id = args.id
        modify_args.types = args.types
        modify_args.brief = args.brief
        modify_args.address = args.address
        modify_args.sid = 0 if 'sid' not in args else args.sid
        ports = '' if 'ports' not in args else args.ports
        domain = '' if 'domain' not in args else args.domain
        if ports: modify_args.ports = ports
        choose = '' if 'choose' not in args else args.choose
        pdata = {}
        if int(args.sid) > 0:
            pdata = public.M('firewall_domain').where('id=?', (args.sid,)).find()
        # 修改端口规则
        if ports:
            modify_args.protocol = args.protocol
            # 已经指定域名
            if int(args.sid) > 0:
                # 当修改为指定域名时
                if choose == 'domain':
                    # 当修改为不同域名时
                    if domain != pdata['domain']:
                        self.del_domain_ip(args)
                        self.set_domain_ip(args)
                    # 当修改为相同域名时
                    else:
                        pdata['protocol'] = args.protocol
                        pdata['types'] = args.types
                        pdata['brief'] = public.xsssec(args.brief)
                        addtime = time.strftime('%Y-%m-%d %X', time.localtime())
                        pdata['addtime'] = addtime
                        public.M('firewall_domain').where('id=?', pdata['id']).update(pdata)
                        self.modify_rules(args)
                    return public.returnMsg(True, public.lang("Successfully modified"))
                else:
                    args.domain = ''
                    self.del_domain_ip(args)
                    self.create_rules(args)
                    return public.returnMsg(True, public.lang("Successfully modified"))
            # 当未指定域名时
            else:
                # 修改为指定域名
                if domain:
                    self.remove_rules(args)
                    self.set_domain_ip(args)
                    return public.returnMsg(True, public.lang("Successfully modified"))
        # 修改IP规则
        else:
            if int(args.sid) > 0:
                modify_args.address = pdata['address']
                modify_args.domain = pdata['domain']
            return self.modify_ip_rules(modify_args)


    # IP地址检测
    def check_ip(self, address_list):
        rep = r"^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}(\/\d{1,2})?$"
        for address in address_list:
            address = address.split('/')[0]
            if address.find('-') != -1:
                addresses = address.split('-')
                if addresses[0] >= addresses[1]:
                    return public.returnMsg(False, public.lang("IP address you've input is illegal!"))
                s_ips = addresses[0].split(".")
                e_ips = addresses[1].split(".")
                head_s_ip = s_ips[0] + "." + s_ips[1] + "." + s_ips[2] + "."
                head_e_ip = e_ips[0] + "." + e_ips[1] + "." + e_ips[2] + "."
                if head_s_ip != head_e_ip:
                    return public.returnMsg(False, public.lang("IP address you've input is illegal!"))
                if not re.search(rep, addresses[0]):
                    return public.returnMsg(False, public.lang("IP address you've input is illegal!"))
                if not re.search(rep, addresses[1]):
                    return public.returnMsg(False, public.lang("IP address you've input is illegal!"))
            else:
                if not re.search(rep, address) and not public.is_ipv6(address):
                    return public.returnMsg(False, public.lang("IP address you've input is illegal!"))


    # 获取IP范围
    def get_ip(self, address):
        result = []
        arrys = address.split("-")
        s_ips = arrys[0].split(".")
        e_ips = arrys[1].split(".")
        head_s_ip = s_ips[0] + "." + s_ips[1] + "." + s_ips[2] + "."
        region = int(e_ips[-1]) - int(s_ips[-1])
        for num in range(0, region + 1):
            result.append(head_s_ip + str(num + int(s_ips[-1])))
        return result


    def handle_firewall_ip(self, address, types):
        ip_list = self.get_ip(address)
        if isinstance(ip_list, dict):
            return
        public.ExecShell(
            'firewall-cmd --permanent --zone=public --new-ipset=' + address +
            ' --type=hash:net')
        xml_path = "/etc/firewalld/ipsets/%s.xml" % address
        tree = ElementTree()
        tree.parse(xml_path)
        root = tree.getroot()
        for ip in ip_list:
            entry = Element("entry")
            entry.text = ip
            root.append(entry)
        self.format(root)
        tree.write(xml_path, 'utf-8', xml_declaration=True)
        # public.ExecShell('firewall-cmd --permanent --zone=public --add-rich-rule=\'rule source ipset="'+ address +'" accept\'')
        public.ExecShell(
            'firewall-cmd --permanent --zone=public --add-rich-rule=\'rule source ipset="'
            + address + '" ' + types + '\'')


    def handle_ufw_ip(self, address, types):
        ip_list = self.get_ip(address)
        if isinstance(ip_list, dict):
            return
        public.ExecShell('ipset create ' + address + ' hash:net')
        for ip in ip_list:
            public.ExecShell('ipset add ' + address + ' ' + ip)
        public.ExecShell('iptables -I INPUT -m set --match-set ' + address +
                         ' src -j ' + types.upper())


    # 检查IP地址是否在范围内
    def ip_in_range(self, ip, ip_range):
        import ipaddress
        # 2024/1/3 下午 7:59 兼容192.168.0.0/24这种形式
        if ip_range.find('/') != -1:
            return ipaddress.ip_address(ip) in ipaddress.ip_network(ip_range)

        ip_range = ip_range.split('-')
        if len(ip_range) == 1:  # 如果只有一个IP地址
            return ipaddress.ip_address(ip) == ipaddress.ip_address(ip_range[0])
        else:  # 如果是一个IP范围
            start_ip, end_ip = ip_range
            ip_networks = ipaddress.summarize_address_range(ipaddress.ip_address(start_ip), ipaddress.ip_address(end_ip))
            return any(ipaddress.ip_address(ip) in net for net in ip_networks)


    # 添加IP规则
    def create_ip_rules(self, get):
        from flask import request
        user_ip = request.remote_addr
        _address = get.address.strip()
        original_types = get.types
        brief = get.brief
        domain_total = '' if ('domain' not in get or not get.domain) else get.domain.strip()
        domain = '' if ('domain' not in get or not get.domain) else get.domain.strip() + '|' + _address
        address_list = _address.split(',')
        # public.print_log('############ ip接口 {}'.format(address_list))
        result = self.check_ip(address_list)

        if result:
            return result

        # 先处理用户的IP地址
        old_login_ip = public.M('firewall_ip').where("brief=?", ("IP that allows users to log in",)).field(
            'id, address').select()
        # public.print_log('############  ip接口user_ip {}'.format(user_ip))
        for ip_range in address_list:

            if self.ip_in_range(user_ip, ip_range):

                if old_login_ip and old_login_ip[0][' address'] != user_ip:
                    address = old_login_ip[0][' address']
                    public.M('firewall_ip').where("address=?", (address,)).delete()

                    self.update_panel_data(address)  # 删除面板自带防火墙的表数据

                self.add_rule(user_ip, "accept", "IP that allows users to log in", domain, domain_total)

                break

        # 然后处理其他的IP地址
        for address in address_list:
            self.add_rule(address, original_types, brief, domain, domain_total)

        self.FirewallReload()

        public.WriteLog("system firewall", "Add IP rules: IP: {}, policy: {}".format(_address, original_types))

        return public.returnMsg(True, public.lang("Added successfully!"))


    # 添加单个IP规则
    def add_rule(self, address, types, brief, domain, domain_total):
        if public.M('firewall_ip').where("address=? and types=? and domain=?", (address, types, domain)).count() > 0:
            return
        if self.__isUfw:
            # public.print_log('############ ip接口 1')
            _rule = "allow" if types == "accept" else "deny"
            if address.find('-') != -1:
                # public.print_log('############!!! ip接口 2')
                self.handle_ufw_ip(address, types)
            else:
                # public.print_log('############!!! ip接口 3')
                is_debian = True if public.get_os_version().lower().find("debian") != -1 else False
                if not is_debian:
                    if _rule == "allow":
                        if public.is_ipv6(address):
                            public.ExecShell('ufw ' + _rule + ' from ' + address + ' to any')
                        else:
                            public.ExecShell('ufw insert 1 ' + _rule + ' from ' + address + ' to any')
                    else:
                        public.ExecShell('ufw ' + _rule + ' from ' + address + ' to any')
                else:
                    public.ExecShell('iptables -I INPUT -s ' + address + ' -j ' + types.upper())
        else:
            # public.print_log('############!!! ip接口 4')
            if self.__isFirewalld:
                # public.print_log('############ ip接口 6')
                if address.find('-') != -1:
                    self.handle_firewall_ip(address, types)
                else:
                    if types == "accept":
                        public.ExecShell('firewall-cmd --permanent --add-source=' + address + ' --zone=trusted')
                    else:
                        if public.is_ipv6(address):
                            public.ExecShell(
                                'firewall-cmd --permanent --add-rich-rule=\'rule family=ipv6 source address="' + address + '" ' + types + '\'')
                        else:
                            public.ExecShell(
                                'firewall-cmd --permanent --add-rich-rule=\'rule family=ipv4 source address="' + address + '" ' + types + '\'')
            else:
                # public.print_log('############ ip接口 7')
                if address.find('-') != -1:
                    self.handle_ufw_ip(address, types)
                else:
                    public.ExecShell('iptables -I INPUT -s ' + address + ' -j ' + types.upper())
        addtime = time.strftime('%Y-%m-%d %X', time.localtime())
        self._add_sid = public.M('firewall_ip').add('address,types,brief,addtime,domain,sid',
                                                    (address, types, public.xsssec(brief), addtime, domain, 0,))
        # public.print_log('############ ip接口 8{}'.format(self._add_sid))
        if domain:
            # public.print_log('############ ip接口9{}'.format(domain))
            domain_sid = public.M('firewall_domain').add(
                'types,domain,port,address,brief,addtime,sid,protocol,domain_total', (
                    types, domain, '', address, public.xsssec(brief), addtime, self._add_sid, '', domain_total))

            public.M('firewall_ip').where("id=?", (self._add_sid,)).save('sid', domain_sid)


    # 删除All IPs规则
    def remove_all_ip_rules(self, get):
        ip_list = public.M('firewall_ip').select()
        for ip in ip_list:
            id = ip["id"]
            address = ip["address"]
            types = ip["types"]
            if self.__isUfw:
                _rule = "allow" if types == "accept" else "deny"
                if address.find('-') != -1:
                    public.ExecShell('iptables -D INPUT -m set --match-set ' +
                                     address + ' src -j ' + types.upper())
                    public.ExecShell('ipset destroy ' + address)
                else:
                    is_debian = True if public.get_os_version().lower().find(
                        "debian") != -1 else False
                    if not is_debian:
                        public.ExecShell('ufw delete ' + _rule + ' from ' + address + ' to any')
                    else:
                        public.ExecShell("iptables -D INPUT -s " + address +
                                         " -j " + types.upper())
            else:
                if self.__isFirewalld:
                    if address.find('-') != -1:
                        public.ExecShell(
                            'firewall-cmd --permanent --zone=public --remove-rich-rule=\'rule source ipset="'
                            + address + '" ' + types + '\'')
                        public.ExecShell(
                            'firewall-cmd --permanent --zone=public --delete-ipset='
                            + address)
                    else:
                        public.ExecShell(
                            'firewall-cmd --permanent --remove-source=' +
                            address + ' --zone=trusted')
                        if public.is_ipv6(address):
                            public.ExecShell(
                                'firewall-cmd --permanent --remove-rich-rule=\'rule family=ipv6 source address="'
                                + address + '" ' + types + '\'')
                        else:
                            public.ExecShell(
                                'firewall-cmd --permanent --remove-rich-rule=\'rule family=ipv4 source address="'
                                + address + '" ' + types + '\'')
                else:
                    if address.find('-') != -1:
                        public.ExecShell(
                            'iptables -D INPUT -m set --match-set ' + address +
                            ' src -j ' + types.upper())
                        public.ExecShell('ipset destroy ' + address)
                    else:
                        public.ExecShell('iptables -D INPUT -s ' + address +
                                         ' -j ' + types.upper())
            public.M('firewall_ip').where("id=?", (id,)).delete()
            self.update_panel_data(address)  # 删除面板自带防火墙的表数据
        self.FirewallReload()
        return public.returnMsg(True, public.lang("All IP rules have been removed."))


    # 删除IP规则
    def remove_ip_rules(self, get):
        id = get.id
        address = get.address
        types = get.types
        if self.__isUfw:
            _rule = "allow" if types == "accept" else "deny"
            if address.find('-') != -1:
                public.ExecShell('iptables -D INPUT -m set --match-set ' +
                                 address + ' src -j ' + types.upper())
                public.ExecShell('ipset destroy ' + address)
            else:
                is_debian = True if public.get_os_version().lower().find(
                    "debian") != -1 else False
                if not is_debian:
                    public.ExecShell('ufw delete ' + _rule + ' from ' + address + ' to any')
                else:
                    public.ExecShell('ufw delete ' + _rule + ' from ' + address + ' to any')
                    public.ExecShell("iptables -D INPUT -s " + address +
                                     " -j " + types.upper())
        else:
            if self.__isFirewalld:
                if address.find('-') != -1:
                    public.ExecShell(
                        'firewall-cmd --permanent --zone=public --remove-rich-rule=\'rule source ipset="'
                        + address + '" ' + types + '\'')
                    public.ExecShell(
                        'firewall-cmd --permanent --zone=public --delete-ipset='
                        + address)
                else:
                    public.ExecShell(
                        'firewall-cmd --permanent --remove-source=' + address +
                        ' --zone=trusted')
                    if public.is_ipv6(address):
                        public.ExecShell(
                            'firewall-cmd --permanent --remove-rich-rule=\'rule family=ipv6 source address="'
                            + address + '" ' + types + '\'')
                    else:
                        public.ExecShell(
                            'firewall-cmd --permanent --remove-rich-rule=\'rule family=ipv4 source address="'
                            + address + '" ' + types + '\'')
            else:
                if address.find('-') != -1:
                    public.ExecShell('iptables -D INPUT -m set --match-set ' +
                                     address + ' src -j ' + types.upper())
                    public.ExecShell('ipset destroy ' + address)
                else:
                    public.ExecShell('iptables -D INPUT -s ' + address +
                                     ' -j ' + types.upper())
        public.M('firewall_ip').where("id=?", (id,)).delete()
        self.update_panel_data(address)  # 删除面板自带防火墙的表数据
        self.FirewallReload()
        strategy = ''
        if get.types == 'accept':
            strategy = "accept"
        elif get.types == 'drop':
            strategy = "drop"
        public.WriteLog("system firewall", "Delete IP rules: IP:{}, policy:{}".format(get.address, strategy))
        return public.returnMsg(True, public.lang("Delete successfully!"))


    # 修改IP规则
    def modify_ip_rules(self, get):
        id = get.id
        address = get.address.strip()
        types = get.types
        brief = get.brief
        result = self.check_ip([address])
        sid = 0 if 'sid' not in get else get.sid
        domain = '' if 'domain' not in get else get.domain
        domain_total = domain.split('|')[0]
        # return 22
        if result:
            return result
        data = public.M('firewall_ip').where(
            'id=?', (id,)).field('id,address,types,brief,addtime').find()
        _address = data.get("address", "")
        _type = data.get("types", "")
        if self.__isUfw:
            rule1 = "allow" if _type == "accept" else "deny"
            if _address.find('-') != -1:
                public.ExecShell('iptables -D INPUT -m set --match-set ' +
                                 _address + ' src -j ' + _type.upper())
                public.ExecShell('ipset destroy ' + _address)
            else:
                is_debian = True if public.get_os_version().lower().find(
                    "debian") != -1 else False
                if not is_debian:
                    public.ExecShell('ufw delete ' + rule1 + ' from ' + address + ' to any')
                else:
                    cmd = "iptables -D INPUT -s " + address + " -j " + _type.upper(
                    )
                    public.ExecShell(cmd)
                # public.ExecShell('ufw delete ' + rule1 + ' from ' + _address + ' to any')
            rule2 = "allow" if types == "accept" else "deny"
            if address.find('-') != -1:
                self.handle_ufw_ip(address, types)
            else:
                is_debian = True if public.get_os_version().lower().find(
                    "debian") != -1 else False
                if not is_debian:
                    if rule2 == "allow":
                        if public.is_ipv6(address):
                            public.ExecShell('ufw ' + rule2 + ' from ' + address + ' to any')
                        else:
                            public.ExecShell('ufw insert 1 ' + rule2 + ' from ' + address + ' to any')
                    else:
                        public.ExecShell('ufw ' + rule2 + ' from ' + address + ' to any')
                else:
                    public.ExecShell('iptables -I INPUT -s ' + address +
                                     ' -j ' + types.upper())
        else:
            if self.__isFirewalld:
                if _address.find('-') != -1:
                    public.ExecShell(
                        'firewall-cmd --permanent --zone=public --remove-rich-rule=\'rule source ipset="'
                        + _address + '" ' + _type + '\'')
                    public.ExecShell(
                        'firewall-cmd --permanent --zone=public --delete-ipset='
                        + _address)
                else:
                    public.ExecShell(
                        'firewall-cmd --permanent --remove-source=' +
                        _address + ' --zone=trusted')
                    if public.is_ipv6(address):
                        public.ExecShell(
                            'firewall-cmd --permanent --remove-rich-rule=\'rule family=ipv6 source address="'
                            + _address + '" ' + _type + '\'')
                    else:
                        public.ExecShell(
                            'firewall-cmd --permanent --remove-rich-rule=\'rule family=ipv4 source address="'
                            + _address + '" ' + _type + '\'')
                if address.find('-') != -1:
                    brief = address
                    self.handle_firewall_ip(address, types)
                else:
                    if types == "accept":
                        public.ExecShell(
                            'firewall-cmd --permanent --add-source=' +
                            address + ' --zone=trusted')
                    else:
                        if public.is_ipv6(address):
                            public.ExecShell(
                                'firewall-cmd --permanent --add-rich-rule=\'rule family=ipv6 source address="'
                                + address + '" ' + types + '\'')
                        else:
                            public.ExecShell(
                                'firewall-cmd --permanent --add-rich-rule=\'rule family=ipv4 source address="'
                                + address + '" ' + types + '\'')
            else:
                if _address.find('-') != -1:
                    public.ExecShell('iptables -D INPUT -m set --match-set ' +
                                     _address + ' src -j ' + types.upper())
                    public.ExecShell('ipset destroy ' + _address)
                else:
                    public.ExecShell('iptables -D INPUT -s ' + _address +
                                     ' -j ' + _type.upper())
                if address.find('-') != -1:
                    self.handle_ufw_ip(address, types)
                else:
                    public.ExecShell('iptables -I INPUT -s ' + address +
                                     ' -j ' + types.upper())
        addtime = time.strftime('%Y-%m-%d %X', time.localtime())
        public.M('firewall_ip').where('id=?', id).update(
            {'address': address, 'types': types, 'brief': brief, 'addtime': addtime, 'sid': sid, 'domain': domain})
        if domain:
            public.M('firewall_domain').where('id=?', (sid,)).save('sid,types,brief,domain_total',
                                                                   (id, types, brief, domain_total))
        self.FirewallReload()
        old_strategy = ''
        if types == 'accept':
            old_strategy = "accept"
        elif types == 'drop':
            old_strategy = "drop"
        if get.types == 'accept':
            strategy = "accept"
        elif get.types == 'drop':
            strategy = "drop"
        public.WriteLog("system firewall",
                        "修改规则, IP:{}, 策略:{} -> IP:{}, 策略:{}".format(_address, old_strategy, get.address.strip(),
                                                                            get.types))
        return public.returnMsg(True, public.lang("Successful operation"))


    # 查看端口转发状态
    def trans_status(self):
        content = dict()
        with open(self._trans_status, 'r') as fr:
            content = json.loads(fr.read())
            if content["status"] == "open":
                return True
            self.open_forward()
            content["status"] = "open"
            with open(self._trans_status, 'w') as fw:
                fw.write(json.dumps(content))
        return True


    # 查询端口转发
    def get_forward_list(self, args):
        result = self.trans_status()

        p = 1
        limit = 15
        if 'p' in args: p = args.p
        if 'limit' in args: limit = args.limit

        where = '1=1'
        sql = public.M('firewall_trans')

        if hasattr(args, 'query'):
            where = " start_port like '%{search}%'".format(search=args.query)

        count = sql.where(where, ()).count()
        data = public.get_page(count, int(p), int(limit))
        data['data'] = sql.where(where, ()).limit('{},{}'.format(
            data['shift'], data['row'])).order('addtime desc').select()
        return data


    # 添加端口转发
    def create_forward(self, get):
        s_port = get.s_ports.strip()  # 起始端口
        d_port = get.d_ports.strip()  # 目的端口
        d_ip = get.d_address.strip()  # 目的ip
        protocol = get.protocol
        rep1 = r"^\d{1,5}(:\d{1,5})?$"
        if not re.search(rep1, s_port):
            return public.returnMsg(False, public.lang("Port range is incorrect!"))
        if not re.search(rep1, d_port):
            return public.returnMsg(False, public.lang("Port range is incorrect!"))
        rep = r"^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}(\/\d{1,2})?$"
        if d_ip:
            if not re.search(rep, get.d_address) and not public.is_ipv6(
                    get.d_address):
                return public.returnMsg(False, public.lang("IP address you've input is illegal!"))
            if d_ip in ["127.0.0.1", "localhost"]:
                d_ip = ""
        if public.M('firewall_trans').where("start_port=?",
                                            (s_port,)).count() > 0:
            return public.returnMsg(False, public.lang("This port already exists, please do not add it again!"))
        if self.__isUfw:
            content = self.ufw_handle_add(s_port, d_port, d_ip, protocol)
            self.save_profile(self._ufw_before, content)
        else:
            if self.__isFirewalld:
                self.firewall_handle_add(s_port, d_port, d_ip, protocol)
            else:
                self.iptables_handle_add(s_port, d_port, d_ip, protocol)
        addtime = time.strftime('%Y-%m-%d %X', time.localtime())
        public.M('firewall_trans').add(
            'start_port, ended_ip, ended_port, protocol, addtime',
            (s_port, d_ip, d_port, protocol, addtime))
        self.FirewallReload()
        public.WriteLog("system firewall",
                        "Add port forwarding rules: Start port: {}, Destination port: {}, Destination IP: {}".format(s_port,
                                                                                                                     d_port,
                                                                                                                     d_ip))
        return public.returnMsg(True, public.lang("Added successfully!"))


    # 删除端口转发
    def remove_forward(self, get):
        id = get.id
        s_port = get.s_port
        d_port = get.d_port
        d_ip = get.d_ip
        protocol = get.protocol
        if self.__isUfw:
            content = self.ufw_handle_del(s_port, d_port, d_ip, protocol)
            self.save_profile(self._ufw_before, content)
        else:
            if self.__isFirewalld:
                self.firewall_handle_del(s_port, d_port, d_ip, protocol)
            else:
                self.iptables_handle_del(s_port, d_port, d_ip, protocol)
        public.M('firewall_trans').where("id=?", (id,)).delete()
        self.FirewallReload()
        public.WriteLog("system firewall",
                        "Delete port forwarding rules: Start port: {}, Destination port: {}, Destination IP: {}".format(
                            s_port, d_port, d_ip))
        return public.returnMsg(True, public.lang("Delete successfully!"))


    # 修改端口转发
    def modify_forward(self, get):
        id = get.id
        s_port = get.s_ports.strip()
        d_port = get.d_ports.strip()
        d_ip = get.d_address.strip()
        pool = get.protocol
        rep1 = r"^\d{1,5}(:\d{1,5})?$"
        if not re.search(rep1, s_port):
            return public.returnMsg(False, public.lang("Port range is incorrect!"))
        if not re.search(rep1, d_port):
            return public.returnMsg(False, public.lang("Port range is incorrect!"))
        data = public.M('firewall_trans').where('id=?', (id,)).field(
            'id,start_port,ended_ip,ended_port,protocol,addtime').find()
        start_port = data.get("start_port", "")
        ended_ip = data.get("ended_ip", "")
        ended_port = data.get("ended_port", "")
        protocol = data.get("protocol", "")
        if d_ip:
            rep = r"^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}(\/\d{1,2})?$"
            if not re.search(rep, get.d_address) and not public.is_ipv6(
                    get.d_address):
                return public.returnMsg(False, public.lang("IP address you've input is illegal!"))
            if d_ip in ["127.0.0.1", "localhost"]:
                d_ip = ""
        if self.__isUfw:
            content = self.ufw_handle_update(start_port, ended_ip, ended_port,
                                             protocol, s_port, d_ip, d_port,
                                             pool)
            self.save_profile(self._ufw_before, content)
        else:
            if self.__isFirewalld:
                self.firewall_handle_update(start_port, ended_ip, ended_port,
                                            protocol, s_port, d_ip, d_port,
                                            pool)
            else:
                self.iptables_handle_update(start_port, ended_ip, ended_port,
                                            protocol, s_port, d_ip, d_port,
                                            pool)
        addtime = time.strftime('%Y-%m-%d %X', time.localtime())
        public.M('firewall_trans').where('id=?', id).update(
            {'start_port': s_port, "ended_ip": d_ip, "ended_port": d_port, "protocol": pool})
        self.FirewallReload()
        public.WriteLog("system firewall",
                        "Modify port forwarding rules: Start port: {}, Destination port: {}, Destination IP: {} -> Start port: {}, Destination port: {}, Destination IP: {}".format(
                            start_port, ended_port, ended_ip, s_port, d_port, d_ip))
        return public.returnMsg(True, public.lang("Successful operation."))


    # 处理ufw的端口转发添加
    def ufw_handle_add(self, s_port, d_port, d_ip, protocol):
        content = self.get_profile(self._ufw_before)
        if content.find('*nat') == -1:
            content = "*nat\n" + ":PREROUTING ACCEPT [0:0]\n" + ":POSTROUTING ACCEPT [0:0]\n" + "COMMIT\n" + content
        array = content.split('\n')
        result = array.index(":POSTROUTING ACCEPT [0:0]")
        if d_ip == "":
            if protocol.find('/') != -1:
                _string = "-A PREROUTING -p tcp --dport {1} -j REDIRECT --to-port {2}\n".format(
                    s_port, d_port)
                _string = _string + "-A PREROUTING -p udp --dport {1} -j REDIRECT --to-port {2}".format(
                    s_port, d_port)
            else:
                _string = "-A PREROUTING -p {0} --dport {1} -j REDIRECT --to-port {2}".format(
                    protocol, s_port, d_port)
        else:
            _string = "-A PREROUTING -p {0} --dport {1} -j DNAT --to-destination {2}:{3}\n".format(
                protocol, s_port, d_ip,
                d_port) + "-A POSTROUTING -d {0} -j MASQUERADE".format(d_ip)
        array.insert(result + 1, _string)
        return '\n'.join(array)


    # 处理ufw的端口转发删除
    def ufw_handle_del(self, s_port, d_port, d_ip, protocol):
        content = self.get_profile(self._ufw_before)
        if d_ip == "":
            _string = "-A PREROUTING -p {0} --dport {1} -j REDIRECT --to-port {2}\n".format(
                protocol, s_port, d_port)
        else:
            _string = "-A PREROUTING -p {0} --dport {1} -j DNAT --to-destination {2}:{3}\n".format(
                protocol, s_port, d_ip,
                d_port) + "-A POSTROUTING -d {0} -j MASQUERADE\n".format(d_ip)
        content = content.replace(_string, "")
        return content


    # 处理ufw的端口转发修改
    def ufw_handle_update(self, start_port, ended_ip, ended_port, protocol,
                          s_port, d_ip, d_port, pool):
        content = self.get_profile(self._ufw_before)
        if ended_ip == "":
            s_string = "-A PREROUTING -p {0} --dport {1} -j REDIRECT --to-port {2}\n".format(
                protocol, start_port, ended_port)
        else:
            s_string = "-A PREROUTING -p {0} --dport {1} -j DNAT --to-destination {2}:{3}\n".format(
                protocol, start_port, ended_ip, ended_port
            ) + "-A POSTROUTING -d {0} -j MASQUERADE\n".format(ended_ip)
        if d_ip == "":
            d_string = "-A PREROUTING -p {0} --dport {1} -j REDIRECT --to-port {2}\n".format(
                pool, s_port, d_port)
        else:
            d_string = "-A PREROUTING -p {0} --dport {1} -j DNAT --to-destination {2}:{3}\n".format(
                pool, s_port, d_ip,
                d_port) + "-A POSTROUTING -d {0} -j MASQUERADE\n".format(d_ip)
        content = content.replace(s_string, d_string)
        return content


    # 处理firewall的端口转发添加
    def firewall_handle_add(self, s_port, d_port, d_ip, protocol):
        if protocol.find('/') != -1:
            public.ExecShell(
                "firewall-cmd --permanent --zone=public --add-forward-port=port="
                + s_port + ":proto=tcp:toaddr=" + d_ip + ":toport=" + d_port +
                "")
            public.ExecShell(
                "firewall-cmd --permanent --zone=public --add-forward-port=port="
                + s_port + ":proto=udp:toaddr=" + d_ip + ":toport=" + d_port +
                "")
        else:
            cmd = "firewall-cmd --permanent --zone=public --add-forward-port=port=" + s_port + ":proto=" + protocol + ":toaddr=" + d_ip + ":toport=" + d_port + ""
            public.ExecShell(cmd)


    # 处理firewall的端口转发删除
    def firewall_handle_del(self, s_port, d_port, d_ip, protocol):
        if protocol.find('/') != -1:
            public.ExecShell(
                "firewall-cmd --permanent --zone=public --remove-forward-port=port="
                + s_port + ":proto=tcp:toaddr=" + d_ip + ":toport=" + d_port +
                "")
            public.ExecShell(
                "firewall-cmd --permanent --zone=public --remove-forward-port=port="
                + s_port + ":proto=udp:toaddr=" + d_ip + ":toport=" + d_port +
                "")
        else:
            public.ExecShell(
                "firewall-cmd --permanent --zone=public --remove-forward-port=port="
                + s_port + ":proto=" + protocol + ":toaddr=" + d_ip +
                ":toport=" + d_port + "")


    # 处理firewall的端口转发修改
    def firewall_handle_update(self, start_port, ended_ip, ended_port,
                               protocol, s_port, d_ip, d_port, pool):
        if protocol.find('/') != -1:
            public.ExecShell(
                "firewall-cmd --permanent --zone=public --remove-forward-port=port="
                + start_port + ":proto=tcp:toaddr=" + ended_ip + ":toport=" +
                ended_port + "")
            public.ExecShell(
                "firewall-cmd --permanent --zone=public --remove-forward-port=port="
                + start_port + ":proto=udp:toaddr=" + ended_ip + ":toport=" +
                ended_port + "")
        else:
            public.ExecShell(
                "firewall-cmd --permanent --zone=public --remove-forward-port=port="
                + start_port + ":proto=" + protocol + ":toaddr=" + ended_ip +
                ":toport=" + ended_port + "")
        if pool.find('/') != -1:
            public.ExecShell(
                "firewall-cmd --permanent --zone=public --add-forward-port=port="
                + s_port + ":proto=tcp:toaddr=" + d_ip + ":toport=" + d_port +
                "")
            public.ExecShell(
                "firewall-cmd --permanent --zone=public --add-forward-port=port="
                + s_port + ":proto=udp:toaddr=" + d_ip + ":toport=" + d_port +
                "")
        else:
            public.ExecShell(
                "firewall-cmd --permanent --zone=public --add-forward-port=port="
                + s_port + ":proto=" + pool + ":toaddr=" + d_ip + ":toport=" +
                d_port + "")


    # 处理iptables的端口转发添加
    def iptables_handle_add(self, s_port, d_port, d_ip, protocol):
        if d_ip == "":
            if protocol.find('/') != -1:
                public.ExecShell(
                    "iptables -t nat -A PREROUTING -p tcp --dport " + s_port +
                    " -j REDIRECT --to-port " + d_port + '')
                public.ExecShell(
                    "iptables -t nat -A PREROUTING -p udp --dport " + s_port +
                    " -j REDIRECT --to-port " + d_port + '')
            else:
                public.ExecShell("iptables -t nat -A PREROUTING -p " +
                                 protocol + " --dport " + s_port +
                                 " -j REDIRECT --to-port " + d_port + '')
        else:
            if protocol.find('/') != -1:
                public.ExecShell(
                    "iptables -t nat -A PREROUTING -p tcp --dport " + s_port +
                    " -j DNAT --to-destination " + d_ip + ":" + d_port + '')
                public.ExecShell(
                    "iptables -t nat -A PREROUTING -p udp --dport " + s_port +
                    " -j DNAT --to-destination " + d_ip + ":" + d_port + '')
                public.ExecShell(
                    "iptables -t nat -A POSTROUTING -j MASQUERADE")
            else:
                public.ExecShell(
                    "iptables -t nat -A PREROUTING -p " + protocol + " --dport " + s_port + " -j DNAT --to-destination " + d_ip + ":" + d_port + '')
                public.ExecShell("iptables -t nat -A POSTROUTING -j MASQUERADE")
        return True


    # 处理iptables的端口转发删除
    def iptables_handle_del(self, s_port, d_port, d_ip, protocol):
        if d_ip == "":
            if protocol.find('/') != -1:
                public.ExecShell(
                    "iptables -t nat -D PREROUTING -p tcp --dport " + s_port +
                    " -j REDIRECT --to-port " + d_port + '')
                public.ExecShell(
                    "iptables -t nat -D PREROUTING -p udp --dport " + s_port +
                    " -j REDIRECT --to-port " + d_port + '')
            else:
                public.ExecShell("iptables -t nat -D PREROUTING -p " +
                                 protocol + " --dport " + s_port +
                                 " -j REDIRECT --to-port " + d_port + '')
        else:
            if protocol.find('/') != -1:
                public.ExecShell(
                    "iptables -t nat -D PREROUTING -p tcp --dport " + s_port + " -j DNAT --to-destination " + d_ip + ":" + d_port + '')
                public.ExecShell(
                    "iptables -t nat -D PREROUTING -p udp --dport " + s_port + " -j DNAT --to-destination " + d_ip + ":" + d_port + '')
                public.ExecShell("iptables -t nat -D POSTROUTING -j MASQUERADE")
            else:
                public.ExecShell(
                    "iptables -t nat -D PREROUTING -p " + protocol + " --dport " + s_port + " -j DNAT --to-destination " + d_ip + ":" + d_port + '')
                public.ExecShell("iptables -t nat -D POSTROUTING -j MASQUERADE")
        return True


    # 处理iptables的端口转发删除
    def iptables_handle_update(self, start_port, ended_ip, ended_port,
                               protocol, s_port, d_ip, d_port, pool):
        if ended_ip == "":
            if protocol.find('/') != -1:
                public.ExecShell(
                    "iptables -t nat -D PREROUTING -p tcp --dport " + s_port +
                    " -j REDIRECT --to-port " + d_port + '')
                public.ExecShell(
                    "iptables -t nat -D PREROUTING -p udp --dport " + s_port +
                    " -j REDIRECT --to-port " + d_port + '')
            else:
                public.ExecShell("iptables -t nat -D PREROUTING -p " +
                                 protocol + " --dport " + s_port +
                                 " -j REDIRECT --to-port " + d_port + '')
        else:
            if protocol.find('/') != -1:
                public.ExecShell(
                    "iptables -t nat -D PREROUTING -p tcp --dport " + s_port + " -j DNAT --to-destination " + d_ip + ":" + d_port + '')
                public.ExecShell(
                    "iptables -t nat -D PREROUTING -p udp --dport " + s_port + " -j DNAT --to-destination " + d_ip + ":" + d_port + '')
                public.ExecShell("iptables -t nat -D POSTROUTING -j MASQUERADE")
            else:
                public.ExecShell(
                    "iptables -t nat -D PREROUTING -p " + protocol + " --dport " + s_port + " -j DNAT --to-destination " + d_ip + ":" + d_port + '')
                public.ExecShell("iptables -t nat -D POSTROUTING -j MASQUERADE")
        if d_ip == "":
            if pool.find('/') != -1:
                public.ExecShell(
                    "iptables -t nat -A PREROUTING -p tcp --dport " + s_port +
                    " -j REDIRECT --to-port " + d_port + '')
                public.ExecShell(
                    "iptables -t nat -A PREROUTING -p udp --dport " + s_port +
                    " -j REDIRECT --to-port " + d_port + '')
            else:
                public.ExecShell("iptables -t nat -A PREROUTING -p " +
                                 protocol + " --dport " + s_port +
                                 " -j REDIRECT --to-port " + d_port + '')
        else:
            if pool.find('/') != -1:
                public.ExecShell(
                    "iptables -t nat -A PREROUTING -p tcp --dport " + s_port + " -j DNAT --to-destination " + d_ip + ":" + d_port + '')
                public.ExecShell(
                    "iptables -t nat -A PREROUTING -p udp --dport " + s_port + " -j DNAT --to-destination " + d_ip + ":" + d_port + '')
                public.ExecShell("iptables -t nat -A POSTROUTING -j MASQUERADE")
            else:
                public.ExecShell(
                    "iptables -t nat -A PREROUTING -p " + protocol + " --dport " + s_port + " -j DNAT --to-destination " + d_ip + ":" + d_port + '')
                public.ExecShell("iptables -t nat -A POSTROUTING -j MASQUERADE")
        return True


    # 开启端口转发
    def open_forward(self):
        if self.__isUfw:
            content1 = self.get_profile(self._ufw_default)
            content2 = self.get_profile(self._ufw_sysctl)
            content1 = content1.replace('DEFAULT_FORWARD_POLICY="DROP"',
                                        'DEFAULT_FORWARD_POLICY="ACCEPT"')
            content2 = content2.replace('#net/ipv4/ip_forward=1',
                                        'net/ipv4/ip_forward=1')
            self.save_profile(self._ufw_default, content1)
            self.save_profile(self._ufw_sysctl, content2)
            self.FirewallReload()
            return True
        if self.__isFirewalld:
            public.ExecShell(
                'echo "\nnet.ipv4.ip_forward=1" >> /etc/sysctl.conf')
            public.ExecShell('firewall-cmd --add-masquerade --permanent')
            self.FirewallReload()
        else:
            public.ExecShell(
                'echo "\nnet.ipv4.ip_forward=1" >> /etc/sysctl.conf')
            public.ExecShell('sysctl -p /etc/sysctl.conf')
            self.FirewallReload()
        return True


    # 开启或关闭端口转发
    def open_close_forward(self, get):
        if not get.status in ["open", "close"]:
            return public.returnMsg(False, public.lang("Unknown control command!"))
        if self.__isUfw:
            content1 = self.get_profile(self._ufw_default)
            content2 = self.get_profile(self._ufw_sysctl)
            if get.status == 'open':
                content1 = content1.replace('DEFAULT_FORWARD_POLICY="DROP"',
                                            'DEFAULT_FORWARD_POLICY="ACCEPT"')
                content2 = content2.replace('#net/ipv4/ip_forward=1',
                                            'net/ipv4/ip_forward=1')
            else:
                content1 = content1.replace('DEFAULT_FORWARD_POLICY="ACCEPT"',
                                            'DEFAULT_FORWARD_POLICY="DROP"')
                content2 = content2.replace('net/ipv4/ip_forward=1',
                                            '#net/ipv4/ip_forward=1')
            self.save_profile(self._ufw_default, content1)
            self.save_profile(self._ufw_sysctl, content2)
            self.FirewallReload()
            return public.returnMsg(True,
                                    public.lang('Enable' if get.status == "open" else "Disable"))
        if self.__isFirewalld:
            if get.status == 'open':
                public.ExecShell('firewall-cmd --add-masquerade --permanent')
            else:
                public.ExecShell(
                    'firewall-cmd --remove-masquerade --permanent')
            self.FirewallReload()
        else:
            public.ExecShell(
                'echo "net.ipv4.ip_forward=1" >> /etc/sysctl.conf')
            public.ExecShell('sysctl -p /etc/sysctl.conf')
        return public.returnMsg(True, public.lang("Turn off port forwarding"))


    def get_host_ip(self):
        """
            查询本机ip地址
            :return:
            """
        try:
            import socket
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(('8.8.8.8', 80))
            ip = s.getsockname()[0]
        finally:
            s.close()

        return ip


    def load_white_list(self):
        try:
            if not self._white_list:
                ip_data = self.get_profile(self._white_list_file)
                white_list_ips = json.loads(ip_data)
                white_list = []
                for ip_obj in white_list_ips:
                    white_list += ip_obj["ips"]
                self._white_list = white_list
                # public.WriteLog("firewall_debug", str(white_list))
            return self._white_list
        except Exception as e:
            public.WriteLog("firewall", "Failed to load whitelist！")
        return []


    def verify_ip(self, ip_entry):
        """检查规则IP是否和内网IP重叠"""
        try:
            try:
                import IPy
            except:
                ipy_tips = '/tmp/bt_ipy.pl'
                if not os.path.exists(ipy_tips):
                    os.system("nohup btpip install IPy &>/dev/null &")
                    public.WriteFile(ipy_tips, 'True')

            release_ips = [
                IPy.IP("127.0.0.1"),
                IPy.IP("172.16.1.1"),
                IPy.IP("10.0.0.1"),
                IPy.IP("192.168.0.0"),
                IPy.IP(self.get_host_ip())
            ]

            white_list = self.load_white_list()

            release_ips += white_list

            ip = IPy.IP(ip_entry, make_net=True)
            for rip_obj in release_ips:
                overlap = ip.overlaps(rip_obj)
                if overlap > 0:
                    return False
            return True
        except:
            return False


    def handle_firewall_country(self, brief, ip_list, types, port_list):
        try:
            public.ExecShell(
                'firewall-cmd --permanent --zone=public --new-ipset=' + brief +
                ' --type=hash:net')
            xml_path = "/etc/firewalld/ipsets/%s.xml" % brief
            tree = ElementTree()
            tree.parse(xml_path)
            root = tree.getroot()
            for ip in ip_list:
                if self.verify_ip(ip):
                    entry = Element("entry")
                    entry.text = ip
                    root.append(entry)
            self.format(root)
            tree.write(xml_path, 'utf-8', xml_declaration=True)
            if port_list:
                for port in port_list:
                    public.ExecShell(
                        'firewall-cmd --permanent --zone=public --add-rich-rule=\'rule source ipset="'
                        + brief + '" port port="' + port + '" protocol=tcp ' +
                        types + '\'')
            else:
                public.ExecShell(
                    'firewall-cmd --permanent --zone=public --add-rich-rule=\'rule source ipset="'
                    + brief + '" ' + types + '\'')
        except Exception as e:
            return {"status": "error", "msg": e}


    def handle_ufw_country(self, brief, ip_list, types, port_list):
        tmp_path = '/tmp/firewall_tmp.sh'
        tmp_file = open(tmp_path, 'w')
        _string = "#!/bin/bash\n"
        for ip in ip_list:
            if self.verify_ip(ip):
                _string = _string + 'ipset add ' + brief + ' ' + ip + '\n'
        tmp_file.write(_string)
        tmp_file.close()
        public.ExecShell('ipset create ' + brief +
                         ' hash:net; /bin/bash /tmp/firewall_tmp.sh')
        if port_list:
            for port in port_list:
                public.ExecShell('iptables -I INPUT -m set --match-set ' +
                                 brief + ' src -p tcp --destination-port ' +
                                 port + ' -j ' + types.upper())
        else:
            public.ExecShell('iptables -I INPUT -m set --match-set ' + brief +
                             ' src -j ' + types.upper())


    # 查询区域规则
    def get_country_list(self, args):
        p = 1
        limit = 15
        if 'p' in args: p = args.p
        if 'limit' in args: limit = args.limit

        where = '1=1'
        sql = public.M('firewall_country')

        if hasattr(args, 'query'):
            where = " country like '%{search}%' or brief like '%{search}%'".format(
                search=args.query)

        count = sql.where(where, ()).count()
        data = public.get_page(count, int(p), int(limit))
        data['data'] = sql.where(where, ()).limit('{},{}'.format(
            data['shift'], data['row'])).order('addtime desc').select()
        return data


    def create_countrys(self, get):
        try:
            if not hasattr(get, 'country'):
                return public.returnMsg(False, public.lang("Please enter the country name!"))
            input_country = get.country
            countrys = self.get_countrys(None)
            countrys = countrys[1:]

            # 2024/1/6 下午 5:00 获取防火墙状态，如果没有启动则启动防火墙
            if not self.get_firewall_status():
                get.status = "start"
                self.firewall_admin(get)

            if "Except China" in input_country:
                input_country = [i['CH'] for i in countrys if not "China" in i['CH']]
                countrys_dict = {i['CH']: i['brief'] for i in countrys}
                content = self.get_profile(self._ips_path)

                for i in input_country:
                    get.brief = countrys_dict.get(i, None)
                    get.country = i
                    self.create_country(get, True, content)
            else:
                countrys_dict = {i['CH']: i['brief'] for i in countrys}
                if isinstance(input_country, str):
                    input_country = [input_country]
                for i in input_country:
                    get.brief = countrys_dict.get(i, None)
                    get.country = i
                    self.create_country(get, True)
            get.status = "restart"
            self.firewall_admin(get)
            return public.returnMsg(True, public.lang("Added successfully"))
        except:
            print(traceback.format_exc())
            return public.returnMsg(False, public.lang("Add failed"))


    # 添加区域规则
    def create_country(self, get, is_mutil=False, _ips_paths=None):
        brief = get.brief
        types = get.types  # types in [accept, drop]
        ports = get.ports
        country = get.country
        rep = r"^\d{1,5}(:\d{1,5})?$"
        port_list = []

        # 检测该区域是否已添加过全部端口规则 hezhihong
        add_list = public.M('firewall_country').where("country=?", (country,)).field('ports').select()

        for add in add_list:
            if not add['ports']:
                return public.returnMsg(False, public.lang("This area has already been added, please do not add it again!"))

        if ports:
            port_list = ports.split(',')
            for port in port_list:
                if not re.search(rep, port):
                    return public.returnMsg(False, public.lang("Port range is incorrect!"))
                if public.M('firewall_country').where(
                        "country=? and ports=?", (country, port)).count() > 0:
                    public.print_log('############ 地区接口8{}'.format(port))
                    return public.returnMsg(False, public.lang("This area has already been added, please do not add it again!"))
        self.get_os_info()
        if _ips_paths is None:
            content = self.get_profile(self._ips_path)
        else:
            content = _ips_paths
        result = json.loads(content)
        ip_list = []
        for r in result:
            if brief == r["brief"]:
                ip_list = r["ips"]
                break
        if not ip_list:
            public.print_log('############ 地区接口7'.format())
            return public.returnMsg(True, public.lang("Please enter the correct area name!"))
        if self.__isUfw:
            self.handle_ufw_country(brief, ip_list, types, port_list)
        else:
            if self.__isFirewalld:
                result = self.handle_firewall_country(brief, ip_list, types,
                                                      port_list)
                if result:
                    public.print_log('############ 地区接口6{}'.format(result))
                    return result
            else:
                self.handle_ufw_country(brief, ip_list, types, port_list)
        addtime = time.strftime('%Y-%m-%d %X', time.localtime())
        if port_list:
            for port in port_list:
                public.M('firewall_country').add(
                    'country,types,brief,ports,addtime',
                    (country, types, brief, port, addtime))
        else:
            public.M('firewall_country').add(
                'country,types,brief,ports,addtime',
                (country, types, brief, '', addtime))
        if is_mutil is False:
            # self.FirewallReload()
            get.status = "restart"
            self.firewall_admin(get)
        if not get.ports:
            log_port = "All ports"
        else:
            log_port = get.ports
        # strategy = ''
        # if get.types == 'accept':
        #     strategy = "accept"
        # elif get.types == 'drop':
        #     strategy = "drop"
        public.print_log('############ 地区接口5'.format())
        public.WriteLog("system firewall",
                        "Add regional rules: Region:{}, Policy:{}, Port:{}".format(get.country, get.types, log_port))
        return public.returnMsg(True, public.lang("Added successfully!"))


    # 删除区域规则
    def remove_country(self, get):
        id = get.id
        types = get.types
        brief = get.brief
        ports = get.ports
        country = get.country
        reload = True
        if "not_reload" in get:
            reload = get.not_reload.lower() == "true"
        public.M('firewall_country').where("id=?", (id,)).delete()
        if self.__isUfw:
            if not ports:
                public.ExecShell('iptables -D INPUT -m set --match-set ' +
                                 brief + ' src -j ' + types.upper())
            else:
                public.ExecShell('iptables -D INPUT -m set --match-set ' +
                                 brief + ' src -p tcp --destination-port ' +
                                 ports + ' -j ' + types.upper())
            if not public.M('firewall_country').where("country=?",
                                                      (country,)).count() > 0:
                public.ExecShell('ipset destroy ' + brief)
        else:
            if self.__isFirewalld:
                if not ports:
                    public.ExecShell(
                        'firewall-cmd --permanent --zone=public --remove-rich-rule=\'rule source ipset="'
                        + brief + '" ' + types + '\'')
                else:
                    public.ExecShell(
                        'firewall-cmd --permanent --zone=public --remove-rich-rule=\'rule source ipset="'
                        + brief + '" port port="' + ports + '" protocol=tcp ' +
                        types + '\'')
                if not public.M('firewall_country').where(
                        "country=?", (country,)).count() > 0:
                    public.ExecShell(
                        'firewall-cmd --permanent --zone=public --delete-ipset='
                        + brief)
            else:
                if not ports:
                    public.ExecShell('iptables -D INPUT -m set --match-set ' +
                                     brief + ' src -j ' + types.upper())
                else:
                    public.ExecShell('iptables -D INPUT -m set --match-set ' +
                                     brief +
                                     ' src -p tcp --destination-port ' +
                                     ports + ' -j ' + types.upper())
                if not public.M('firewall_country').where(
                        "country=?", (country,)).count() > 0:
                    public.ExecShell('ipset destroy ' + brief)
        if reload:
            get.status = "restart"
            self.firewall_admin(get)
        if not get.ports:
            log_port = "All ports"
        else:
            log_port = get.ports
        strategy = ''
        if get.types == 'accept':
            strategy = "accept"
        elif get.types == 'drop':
            strategy = 'drop'
        public.WriteLog("system firewall",
                        "Delete zone rules: Region:{}, Policy:{}, Port:{}".format(get.country, strategy, log_port))
        return public.returnMsg(True, public.lang("Delete successfully!"))


    # 编辑区域规则
    def modify_country(self, get):
        # 2022/11/24 修复编辑地区端口规则问题 lx
        id = get.id
        # types = get.types
        # brief = get.brief
        # country = get.country
        data = public.M('firewall_country').where(
            'id=?',
            (id,)).field('id,country,types,brief,ports,addtime').find()
        ori_get = public.dict_obj()
        ori_get.id = id
        ori_get.types = data.get("types", "")
        ori_get.brief = data.get("brief", "")
        ori_get.country = data.get("country", "")
        ori_get.ports = data.get("ports", "")
        ori_get.not_reload = "true"
        rm_res = self.remove_country(ori_get)
        if rm_res["status"]:
            create_res = self.create_country(get)
            if create_res["status"]:
                return public.returnMsg(True, public.lang("Successful operation"))
        return public.returnMsg(False, public.lang("operation failed"))


    # 获取服务端列表：centos
    def GetList(self):
        try:
            result, arry = self.__Obj.GetAcceptPortList()
            addtime = time.strftime('%Y-%m-%d %X', time.localtime())
            for i in range(len(result)):
                if "address" not in result[i].keys(): continue
                tmp = self.check_db_exists(result[i]['ports'],
                                           result[i]['address'],
                                           result[i]['types'])
                protocol = result[i]['protocol']
                ports = result[i]['ports']
                types = result[i]['types']
                address = result[i]['address']
                if not tmp:
                    if ports:
                        public.M('firewall_new').add(
                            'ports,protocol,address,types,brief,addtime',
                            (ports, protocol, address, types, '', addtime))
                    else:
                        public.M('firewall_ip').add(
                            'address,types,brief,addtime',
                            (address, types, '', addtime))
            for i in range(len(arry)):
                if arry[i]['port']:
                    tmp = self.check_trans_data(arry[i]['port'])
                    protocol = arry[i]['protocol']
                    s_port = arry[i]['port']
                    d_port = arry[i]['to-port']
                    address = arry[i]['address']
                    if not tmp:
                        public.M('firewall_trans').add(
                            'start_port,ended_ip,ended_port,protocol,addtime',
                            (s_port, address, d_port, protocol, addtime))
        except Exception as e:
            file = open('error.txt', 'w')
            return public.returnMsg(False, e)


    # 获取服务端列表：ufw
    def get_ufw_list(self):
        data = public.M('firewall').field('id,port,ps,addtime').select()
        if type(data) != list: return
        try:
            for dt in data:
                port = dt['port']
                brief = dt['ps']
                addtime = dt['addtime']
                if port.find('.') != -1:
                    tmp = self.check_db_exists('', port, 'drop')
                    if not tmp:
                        public.M('firewall_ip').add('address,types,brief,addtime',
                                                    (port, 'drop', '', addtime))
                else:
                    tmp = self.check_db_exists(port, '', 'accept')
                    if not tmp:
                        public.M('firewall_new').add(
                            'ports,brief,protocol,address,types,addtime',
                            (port, brief, 'tcp/udp', '', 'accept', addtime))
        except:
            pass


    # 检查数据库是否存在
    def check_db_exists(self, ports, address, types):
        if ports:
            data = public.M('firewall_new').field(
                'id,ports,protocol,address,types,brief,addtime').select()
            for dt in data:
                if dt['ports'] == ports: return dt
            return False
        else:
            data = public.M('firewall_ip').field(
                'id,address,types,brief,addtime').select()
            for dt in data:
                if dt["address"] == address and dt["types"] == types: return dt
            return False


    def check_trans_data(self, ports):
        data = public.M('firewall_trans').field(
            'id,start_port,ended_ip,ended_port,protocol,addtime').select()
        for dt in data:
            if dt['start_port'] == ports: return dt
        return False


    # 规则导出：服务器
    def export_rules(self, get):
        rule_name = get.rule_name
        arry = []
        data_list = None
        filename = ''
        if rule_name == "port_rule":
            filename = self._rule_path + "port.json"
            data_list = public.M('firewall_new').order("id desc").select()
        elif rule_name == "ip_rule":
            filename = self._rule_path + "ip.json"
            data_list = public.M('firewall_ip').order("id desc").select()
        elif rule_name == "trans_rule":
            filename = self._rule_path + "forward.json"
            data_list = public.M('firewall_trans').order("id desc").select()
        elif rule_name == "country_rule":
            filename = self._rule_path + "country.json"
            data_list = public.M('firewall_country').order("id desc").select()
        if not data_list:
            data_list = []
        # 将数据格式换成以|分割的字符串 hezhihong
        write_string = ""
        if data_list:
            for i in data_list:
                for v in i.keys():
                    if v == 'domain': i[v] = i[v].replace('|', '#')
                    write_string += str(i[v]) + "|"
                write_string += '\n'
        public.writeFile(filename, write_string)
        public.WriteLog("system firewall", "Export port rules")
        return public.returnMsg(True, filename)


    # 规则导出：本地
    def get_file(self, args):
        filename = args.filename
        mimetype = "application/octet-stream"
        if not os.path.exists(filename): return abort(404)
        return send_file(filename,
                         mimetype=mimetype,
                         as_attachment=True,
                         attachment_filename=os.path.basename(filename),
                         cache_timeout=0)


    # 规则导入：json
    def import_rules(self, get):
        try:
            rule_name = get.rule_name  # 规则名:[port_rule, ip_rule, trans_rule, country_rule]
            file_name = get.file_name  # 文件命:[port.json, ip.json, trans.json, country.json]
            file_path = "{0}{1}".format(self._rule_path, file_name)
            data_list = self.get_profile(file_path)
            pay = self.__check_auth()
            not_pay_list = []
            tmp_data = []
            # |分隔符格式文件导入 hezhihong
            if data_list and isinstance(data_list, str):

                if data_list.find('|') != -1:
                    data_list = data_list.split('\n')
                    for data in data_list:
                        if not data: continue
                        split_data = data.split('|')
                        data_dict = {}
                        data_dict['id'] = split_data[0]
                        if rule_name == 'port_rule':
                            if not pay and split_data[7].find('#') != -1:
                                not_pay_list.append(data)
                                continue
                            data_dict['protocol'] = split_data[1]
                            data_dict['ports'] = split_data[2]
                            data_dict['types'] = split_data[3]
                            data_dict['address'] = split_data[4]
                            data_dict['brief'] = split_data[5]
                            data_dict['addtime'] = split_data[6]
                            data_dict['domain'] = split_data[7]
                        elif rule_name == 'ip_rule':
                            if not pay and split_data[6].find('#') != -1:
                                not_pay_list.append(data)
                                continue
                            data_dict['types'] = split_data[1]
                            data_dict['address'] = split_data[2]
                            data_dict['brief'] = split_data[3]
                            data_dict['addtime'] = split_data[4]
                            data_dict['domain'] = split_data[6]
                        elif rule_name == 'trans_rule':
                            data_dict['start_port'] = split_data[1]
                            data_dict['ended_ip'] = split_data[2]
                            data_dict['ended_port'] = split_data[3]
                            data_dict['protocol'] = split_data[4]
                            data_dict['addtime'] = split_data[5]
                        elif rule_name == 'country_rule':
                            data_dict['types'] = split_data[1]
                            data_dict['country'] = split_data[2]
                            data_dict['brief'] = split_data[3]
                            data_dict['addtime'] = split_data[4]
                            data_dict['ports'] = split_data[5]
                        tmp_data.append(data_dict)
            data_list = tmp_data
            # 一行一条规则格式文件导入 hezhihong
            if data_list and isinstance(data_list, str):
                data_list = data_list.strip()
            if isinstance(data_list, str) and data_list.find('\n') != -1:
                data_list = data_list.split('\n')
                try:
                    data_list.remove('')
                except:
                    pass
            if isinstance(data_list, str):
                try:
                    data_list = json.loads(data_list)
                except:
                    if os.path.exists(file_path):
                        os.remove(file_path)
                    return public.ReturnMsg(False, "The file content is incorrect!！")
            if data_list:
                if isinstance(data_list, dict):
                    data_list = [data_list]
                if not isinstance(data_list, list):
                    if os.path.exists(file_path):
                        os.remove(file_path)
                    return public.ReturnMsg(False, "The file content is incorrect!！")
                if len(data_list) == 0:
                    return public.ReturnMsg(False, "The file is empty!")
                result = self.hand_import_rules(rule_name, data_list)
            os.remove(file_path)
            if not_pay_list:
                not_pay_list = ("<br/>" + "-" * 20 + "<br/>").join(not_pay_list)
                return public.ReturnMsg(
                    result["status"],
                    "{}<br/>The designated domain name function is exclusive to the Enterprise Edition, and the following rules are not imported:<br/>{}".format(
                        result["msg"], not_pay_list)
                )
            public.WriteLog("system firewall", "Import port rules")
            return public.ReturnMsg(result["status"], result["msg"])
        except Exception:
            return public.ReturnMsg(False,
                                    "The import failed. The format of the rules is wrong. Please try again according to the format of the export rules!")


    # 处理规则导入，读取json文件内容
    def hand_import_rules(self, rule_name, data_list):
        table_head = []
        try:
            if rule_name == "port_rule":
                table_head = ["id", "protocol", "ports", "types", "address", "brief", "addtime", "domain", ]
                for data in data_list:
                    # 兼容一行一条规则格式文件导入 hezhihong
                    try:
                        data = json.loads(data)
                    except:
                        pass

                    res = all([field in data.keys() for field in table_head])
                    if not res or len(table_head) != len(data.keys()):
                        return {"status": False, "msg": "The data format is incorrect!"}
                    get = public.dict_obj()
                    get.protocol = data["protocol"]
                    get.ports = data["ports"]
                    get.types = data["types"]
                    get.source = data["address"]
                    get.brief = data["brief"]
                    # 兼容域名导入 hezhihong
                    if 'domain' in data.keys() and data['domain']:
                        get.domain = data['domain'].split('#')[0]
                        get.source = data['domain'].split('#')[1]
                    result = self.create_rules(get)
                    if not result["status"]:
                        continue
            elif rule_name == "ip_rule":
                table_head = ["id", "types", "address", "brief", "addtime"]
                for data in data_list:
                    # 兼容一行一条规则格式文件导入 hezhihong
                    try:
                        data = json.loads(data)
                    except:
                        pass
                    res = all([field in data.keys() for field in table_head])
                    if not res:
                        return {"status": False, "msg": "The data format is incorrect!"}
                    get = public.dict_obj()
                    get.types = data["types"]
                    get.address = data["address"]
                    get.brief = data["brief"]
                    # 兼容域名导入 hezhihong
                    if 'domain' in data.keys() and data['domain']:
                        get.domain = data['domain'].split('#')[0]
                        get.source = data['domain'].split('#')[1]
                    result = self.create_ip_rules(get)
                    if not result["status"]:
                        continue
            elif rule_name == "trans_rule":
                table_head = [
                    "id", "start_port", "ended_ip", "ended_port", "protocol",
                    "addtime"
                ]
                for data in data_list:
                    # 兼容一行一条规则格式文件导入 hezhihong
                    try:
                        data = json.loads(data)
                    except:
                        pass
                    res = all([field in data.keys() for field in table_head])
                    if not res:
                        return {"status": False, "msg": "The data format is incorrect!"}
                    get = public.dict_obj()
                    get.s_ports = data["start_port"]
                    get.d_address = data["ended_ip"]
                    get.d_ports = data["ended_port"]
                    get.protocol = data["protocol"]
                    result = self.create_forward(get)
                    if not result["status"]:
                        continue
            elif rule_name == "country_rule":
                table_head = ["id", "types", "country", "brief", "addtime", "ports"]
                for data in data_list:
                    # 兼容一行一条规则格式文件导入 hezhihong
                    try:
                        data = json.loads(data)
                    except:
                        pass
                    res = all([field in data.keys() for field in table_head])
                    if not res:
                        return {"status": False, "msg": "The data format is incorrect!"}
                    get = public.dict_obj()
                    get.types = data["types"]
                    get.ports = data["ports"]
                    get.brief = data["brief"]
                    get.country = data["country"]
                    result = self.create_country(get)
                    if not result["status"]:
                        continue
        except:
            return {"status": False, "msg": "Import failed!"}
        return {"status": True, "msg": "Imported successfully!"}


    def get_countrys(self, get):
        result = []
        content = self.get_profile(self._country_path)
        result = json.loads(content)
        result = sorted(result, key=lambda x: x['CH'], reverse=True);

        if isinstance(result, list):
            result.insert(0, {"CH": "Except China", "brief": "OTHER"})
        return result


    # 读取配置文件
    def get_profile(self, path):
        if not os.path.exists(path):
            b_path = os.path.dirname(path)
            if not os.path.exists(b_path): os.makedirs(b_path)

            if path in [
                self._ips_path, self._country_path, self._white_list_file
            ]:
                public.downloadFile(
                    'https://download.bt.cn/install/lib/{}'.format(
                        os.path.basename(path)), path)

        content = ""
        with open(path, "r") as fr:
            content = fr.read()
        return content


    # 保存配置文件
    def save_profile(self, path, data):
        with open(path, "w") as fw:
            fw.write(data)


    # 读取配置文件
    def update_profile(self, path):
        import files
        f = files.files()
        return f.GetFileBody(path)


    # 获取端口规则列表
    def get_port_rules(self, get):
        rule_list = public.M('firewall_new').order("id desc").select()
        return public.returnMsg(True, rule_list)


    # 整理配置文件格式
    def format(self, em, level=0):
        i = "\n" + level * "  "
        if len(em):
            if not em.text or not em.text.strip():
                em.text = i + "  "
            for e in em:
                self.format(e, level + 1)
            if not e.tail or not e.tail.strip():
                e.tail = i
        if level and (not em.tail or not em.tail.strip()):
            em.tail = i


    def check_table(self):
        if public.M('sqlite_master').where('type=? AND name=?',
                                           ('table', 'firewall_new')).count():
            if public.M('sqlite_master').where(
                    'type=? AND name=?', ('table', 'firewall_ip')).count():
                if public.M('sqlite_master').where(
                        'type=? AND name=?',
                        ('table', 'firewall_trans')).count():
                    if public.M('sqlite_master').where(
                            'type=? AND name=?',
                            ('table', 'firewall_country')).count():
                        return True
        return Sqlite()


    def delete_service(self):
        if self.__isUfw:
            public.ExecShell('ufw delete allow ssh')
        else:
            if self.__isFirewalld:
                public.ExecShell(
                    'firewall-cmd --zone=public --remove-service=ssh --permanent'
                )
            else:
                pass
        return True


    # 获取系统类型(具体到哪个版本)
    def get_os_info(self):
        tmp = {"osname": "", "version": ""}
        if os.path.exists('/etc/redhat-release'):
            sys_info = public.ReadFile('/etc/redhat-release')
        elif os.path.exists('/usr/bin/yum'):
            sys_info = public.ReadFile('/etc/issue')
        elif os.path.exists('/etc/issue'):
            sys_info = public.ReadFile('/etc/issue')
        try:
            tmp['osname'] = sys_info.split()[0]
            tmp['version'] = re.search(r'\d+(\.\d*)*', sys_info).group()
        except:
            os_result = public.ExecShell(". /etc/os-release && echo $ID")[0]
            if "amzn" == os_result:
                tmp['osname'] = 'CentOS'
                tmp['version'] = '8'
        if tmp["osname"] == "CentOS":
            if tmp["version"].startswith("8"):
                content = self.get_profile("/etc/firewalld/firewalld.conf")
                content = content.replace("FirewallBackend=nftables", "FirewallBackend=iptables")
                self.save_profile("/etc/firewalld/firewalld.conf", content)
                public.ExecShell("systemctl restart firewalld")
        return True


    # 新加代码----- start

    def sync_must_ports(self, get):
        '''
            同步必须放行的端口
            @param get:
            @return:
            '''
        protocol = "tcp"
        ports = get.ports.strip()
        print(ports)
        if not ports: return public.returnMsg(False, public.lang("Port cannot be empty!"))
        port_list = ports.split(",") if ports.find(",") != -1 else [ports]
        types = "accept"
        check_result = self.check_port(port_list)
        if check_result: return check_result

        firewall_type = 'iptables'
        if self.__isFirewalld: firewall_type = 'firewalld'
        if self.__isUfw: firewall_type = 'ufw'

        try:
            # 2024/1/6 下午 5:00 获取防火墙状态，如果没有启动则启动防火墙
            if not self.get_firewall_status():
                get = public.dict_obj()
                get.status = 1
                self.firewall_admin(get)

            for port in port_list:
                if firewall_type == 'firewalld':
                    if port.find(':') != -1: port = port.replace(':', '-')
                    self.add_firewall_rule("", protocol, port, types)
                elif firewall_type == 'ufw':
                    if port.find('-') != -1: port = port.replace('-', ':')
                    self.add_ufw_rule("", protocol, port, types)
                else:
                    self.add_iptables_rule("", protocol, port, types)

                query_result = public.M('firewall_new').where(
                    'ports=? and address=? and protocol=? and types=?',
                    (port, "", protocol, types)
                ).find()
                print(query_result)
                if query_result: continue

                addtime = time.strftime('%Y-%m-%d %X', time.localtime())
                self._add_sid = public.M('firewall_new').add(
                    'ports,brief,protocol,address,types,addtime,domain,sid',
                    (port, "", protocol, "", types, addtime, "", 0)
                )
            return public.returnMsg(True, public.lang("Added successfully!"))
        except Exception:
            print(traceback.format_exc())
            return public.returnMsg(False, public.lang("Failed to add"))


    def _get_webserver(self):
        '''
            获取web服务器类型
            @return:
            '''
        webserver = ''
        if os.path.exists('/www/server/nginx/sbin/nginx'):
            webserver = 'nginx'
        elif os.path.exists('/www/server/apache/bin/httpd'):
            webserver = 'apache'
        elif os.path.exists('/usr/local/lsws/bin/lswsctrl'):
            webserver = 'lswsctrl'
        return webserver


    def get_port_info(self, get):
        '''
            获取面板防火墙关键服务端口放行状态信息
            判断服务是否存在,能读取文件就读取文件,配置文件不大不会影响性能,这种方式能最大缩短接口响应时间,公网测试80ms
            @param get:
            @return:
            '''
        ports_list = []
        result_list = [{"name": "FTP passive port", "status": 0, "port": "39000-40000"}]

        webserver = self._get_webserver()
        if webserver in ['nginx', 'apache', 'lswsctrl']:
            result_list.append({"name": "website port", "status": 0, "port": "80"})
            ports_list.append("80")

        port_443, _ = public.ExecShell("fuser -n tcp 443")
        if port_443:
            result_list.append({"name": "HTTPS port", "status": 0, "port": "443"})
            ports_list.append("443")

        _panel_port_file = '/www/server/panel/data/port.pl'
        panel_port = public.readFile(_panel_port_file).strip(" ").strip("\n")

        cmd = "cat /www/server/pure-ftpd/etc/pure-ftpd.conf |grep Bind|awk -F ',' '{print $2}'"
        ftp_port = public.ExecShell(cmd)[0].strip(" ").strip("\n").strip("\r")

        cmd = "cat /etc/ssh/sshd_config |grep -E '^Port'|awk '{print $2}'|awk 'NR == 1'"
        ssh_port = public.ExecShell(cmd)[0].strip(" ").strip("\n")

        if ssh_port == "": ssh_port = "22"
        ports_list.append(panel_port)
        result_list.append({"name": "panel", "status": 0, "port": panel_port})
        ports_list.append(ftp_port)
        result_list.append({"name": "FTP active port", "status": 0, "port": ftp_port})
        ports_list.append(ssh_port)
        result_list.append({"name": "SSH", "status": 0, "port": ssh_port})
        ports_list.append("39000-40000")

        if self.__isUfw:
            return self._get_ufw_port_status(ports_list, result_list)
        if self.__isFirewalld:
            return self._get_firewall_port_status(ports_list, result_list)
        return {}


    def _get_firewall_port_status(self, ports_list, result_list):
        '''
            获取firewalld防火墙端口状态
            @param ports_list:
            @param result_list:
            @return:
            '''
        with contextlib.suppress(Exception):
            _firewalld_ports, _ = self.__firewall_obj.GetAcceptPortList()
            # print("_firewalld_ports: ", _firewalld_ports)
            for firewalld_port in _firewalld_ports:
                if firewalld_port['ports'] in ports_list:
                    for result in result_list:
                        if result['port'] == firewalld_port['ports']:
                            result['status'] = 1
                            break
        return result_list


    def _get_ufw_port_status(self, ports_list, result_list):
        '''
            获取ufw防火墙端口状态
            @param ports_list:
            @param result_list:
            @return:
            '''
        with contextlib.suppress(Exception):
            rules_result = self._get_ufw_port_info()
            # print("rules_result: ", rules_result)
            ports_set = set(ports_list)  # 将要查找的端口列表转换成集合，以便进行高效查找

            for rule in rules_result:
                if 'tcp' in rule['protocol'] and rule['ports'] in ports_set:
                    for result in result_list:
                        if result['port'] == rule['ports']:
                            result['status'] = 1
                            ports_set.remove(rule['ports'])
                            break

                if not ports_set: break
        return result_list


    def _get_ufw_port_info(self):
        '''
            获取ufw防火墙端口信息
            @return:
            '''
        with open('/etc/ufw/user.rules', 'r') as f:
            content = f.read()
            start_index = content.find('### RULES ###')
            end_index = content.find('### END RULES ###')
            result = content[start_index + 15:end_index]
        sys_rules = [rule for rule in result.split('\n') if rule != '' and '###' in rule]
        # 将sys_rules列表中的每个元素拆分出来,并且去掉空格,元素为字符串,例如:'### tuple ### allow tcp 20 0.0.0.0/0 any 0.0.0.0/0 in'
        # 拆分后的列表元素为:{'protocol': 'tcp', 'ports': '20', 'types': 'allow', 'address': '0.0.0.0'}
        rules = []
        for rule in sys_rules:
            rule = rule.split(' ')
            rule = [i for i in rule if i != '']
            rules.append({
                'protocol': rule[4] if rule[4] != 'any' else 'tcp/udp',
                'ports': rule[5] if rule[5].find(':') == -1 else rule[5].replace(':', '-'),
                'types': 'accept' if rule[3] == 'allow' else 'drop',
                'address': rule[8] if rule[8] != '0.0.0.0/0' else ''
            })

        unique_set = set(tuple(sorted(item.items())) for item in rules)
        rules = [dict(item) for item in unique_set]
        return rules


    @staticmethod
    def get_listening_processes(get: public.dict_obj):
        '''
            获取指定端口的进程信息
            @param get:
            @return:
            '''
        if 'port' not in get.get_items().keys(): return public.returnMsg(False, public.lang("Parameter passing error, please pass the port field"))
        if len(get.port) == 0: return public.returnMsg(False, public.lang("Port cannot be empty"))
        if get.port.find('-') != -1 or get.port.find(':') != -1: return public.returnMsg(False, public.lang("Range ports not supported"))
        if not get.port.isdigit(): return public.returnMsg(False, public.lang("Port must be numeric"))
        if int(get.port) < 1 or int(get.port) > 65535: return public.returnMsg(False, public.lang("The port range is 1-65535"))

        process_name = ''
        process_pid = ''
        process_cmd = ''

        cmd = "lsof -i:{}|grep LISTEN|grep -v COMMAND".format(get.port) + "|awk '{print $1,$2}'"
        info_list = public.ExecShell(cmd)[0].split("\n")[0].split(" ")
        if len(info_list) == 2:
            process_name = info_list[0]
            process_pid = info_list[1]
            cmd_ps = "ps aux|grep {}|grep -v grep".format(process_pid)
            cmd_awk = "|awk '{print $11,$12,$13,$14}'"
            process_cmd = public.ExecShell(cmd_ps + cmd_awk)[0].split("\n")[0].strip(" ")

        return {
            "process_name": process_name,
            "process_pid": process_pid,
            "process_cmd": process_cmd
        }


    def get_diff_panel_firewall_rules(self, get):
        '''
            对比面板防火墙规则数据库和防火墙配置文件,取出差异的规则
            @return:
            '''
        # 获取面板防火墙规则数据库
        panel_firewall_rules = self.get_panel_firewall_rules()
        # 获取防火墙配置文件
        firewall_rules = self.get_sys_firewall_rules()
        # 取出差异的规则
        diff_rules = self._get_diff_rules(panel_firewall_rules, firewall_rules)
        return diff_rules


    def get_panel_firewall_rules(self):
        '''
            获取面板防火墙规则数据库
            @return:
            '''
        all_ports = public.M('firewall_new').field('protocol,ports,types,address').order('addtime desc').select()
        unique_set = set(tuple(sorted(item.items())) for item in all_ports)
        new_ports = [dict(item) for item in unique_set]
        return new_ports


    def get_sys_firewall_rules(self):
        '''
            获取防火墙配置文件
            @return:
            '''
        if self.__isUfw: return self._get_ufw_port_info()
        if self.__isFirewalld: return self.__firewall_obj.recombine_rules()
        return []


    def _diff_dict_list(self, list1, list2):
        '''
            比较两个dict类型的list,返回list1中有,而list2中没有的元素
            @param list1:
            @param list2:
            @return:
            '''
        list1_not_in_list2 = []
        for item1 in list1:
            found = False
            try:
                for item2 in list2:
                    # 对比'protocol,ports,types,address'是否相同
                    if all(item1[key] == item2[key] for key in ('protocol', 'ports', 'types', 'address')):
                        found = True
                        break
            except KeyError:
                continue
            if not found: list1_not_in_list2.append(item1)
        return list1_not_in_list2


    def _get_diff_rules(self, panel_firewall_rules, firewall_rules):
        '''
            取出差异的规则
            @param panel_firewall_rules:
            @param firewall_rules:
            @return:
            '''
        firewall_diff_rules_name = 'firewall_diff_rules'
        firewall_diff_rules = {}
        if os.path.isfile("config/{}.json".format(firewall_diff_rules_name)):
            firewall_diff_rules = public.read_config(firewall_diff_rules_name)
        if not firewall_diff_rules:
            data = {
                "panel_not_in_sys_fw_diff_list": self._diff_dict_list(panel_firewall_rules, firewall_rules),
                "sys_not_in_panel_fw_diff_list": self._diff_dict_list(firewall_rules, panel_firewall_rules),
                "panel_exclude": [],
                "sys_exclude": []
            }
            public.save_config(firewall_diff_rules_name, data)
            return data

        panel_not_in_sys_fw_diff_list = self._diff_dict_list(panel_firewall_rules, firewall_rules)
        sys_not_in_panel_fw_diff_list = self._diff_dict_list(firewall_rules, panel_firewall_rules)

        # 如果firewall_diff_rules的panel_exclude和sys_exclude中有值,则将其从panel_not_in_sys_fw_diff_list和sys_not_in_panel_fw_diff_list中去掉
        if firewall_diff_rules['panel_exclude']:
            for key in firewall_diff_rules['panel_exclude']:
                if key in panel_not_in_sys_fw_diff_list:
                    panel_not_in_sys_fw_diff_list.remove(key)
        if firewall_diff_rules['sys_exclude']:
            for key in firewall_diff_rules['sys_exclude']:
                # panel_not_in_sys_fw_diff_list是list，如果key在panel_not_in_sys_fw_diff_list中,则将其从panel_not_in_sys_fw_diff_list中去掉
                if key in sys_not_in_panel_fw_diff_list:
                    sys_not_in_panel_fw_diff_list.remove(key)

        # 将差异规则写入文件并返回
        firewall_diff_rules['panel_not_in_sys_fw_diff_list'] = panel_not_in_sys_fw_diff_list
        firewall_diff_rules['sys_not_in_panel_fw_diff_list'] = sys_not_in_panel_fw_diff_list
        public.save_config(firewall_diff_rules_name, firewall_diff_rules)
        return firewall_diff_rules


    def exclude_diff_rules(self, get):
        '''
            排除firewall_diff_rules的规则，并写入配置文件
            @param get:
            @return:
            '''
        try:
            panel_excludes = get.panel_exclude if "panel_exclude" in get.get_items().keys() else {}
            sys_excludes = get.sys_exclude if "sys_exclude" in get.get_items().keys() else {}
            status = get.status if "status" in get.get_items().keys() else {}
            # print("panel_excludes: ", panel_excludes)

            if status == 'add':
                return self._add_exclude(panel_excludes, sys_excludes)
            elif status == 'del':
                return self._del_exclude(panel_excludes, sys_excludes)
        except Exception as e:
            # print(e)
            return public.returnMsg(False, public.lang("Ignore rule failed,{}!", e))


    def _add_exclude(self, panel_excludes, sys_excludes):
        '''
            添加排除规则
            @param panel_exclude:
            @param sys_exclude:
            @return:
            '''
        firewall_diff_rules_name = 'firewall_diff_rules'
        firewall_diff_rules = {}
        if os.path.isfile("config/{}.json".format(firewall_diff_rules_name)):
            firewall_diff_rules = public.read_config(firewall_diff_rules_name)

        if not firewall_diff_rules['panel_exclude']:
            firewall_diff_rules['panel_exclude'] = panel_excludes
        else:
            for exclude in panel_excludes:
                if exclude not in firewall_diff_rules['panel_exclude']:
                    firewall_diff_rules['panel_exclude'].append(exclude)

        if not firewall_diff_rules['sys_exclude']:
            firewall_diff_rules['sys_exclude'] = sys_excludes
        else:
            for exclude in sys_excludes:
                if exclude not in firewall_diff_rules['sys_exclude']:
                    firewall_diff_rules['sys_exclude'].append(exclude)
        public.save_config(firewall_diff_rules_name, firewall_diff_rules)
        return public.returnMsg(True, public.lang("Ignore rules successfully!"))


    def _del_exclude(self, panel_excludes, sys_excludes):
        '''
            删除排除规则
            @param panel_excludes:
            @param sys_excludes:
            @return:
            '''
        firewall_diff_rules_name = 'firewall_diff_rules'
        firewall_diff_rules = {}
        if os.path.isfile("config/{}.json".format(firewall_diff_rules_name)):
            firewall_diff_rules = public.read_config(firewall_diff_rules_name)

        new_panel_exclude = []
        new_sys_exclude = []

        for exclude in firewall_diff_rules['panel_exclude']:
            if exclude not in panel_excludes:
                new_panel_exclude.append(exclude)
        for exclude in firewall_diff_rules['sys_exclude']:
            if exclude not in sys_excludes:
                new_sys_exclude.append(exclude)

        firewall_diff_rules['panel_exclude'] = new_panel_exclude
        firewall_diff_rules['sys_exclude'] = new_sys_exclude
        public.save_config(firewall_diff_rules_name, firewall_diff_rules)
        return public.returnMsg(True, public.lang("Cancel ignore rule successfully!"))


    def _add_firewall_rules(self, source_ip, protocol, port, types):
        '''
            添加防火墙规则
            @param source_ip:
            @param protocol:
            @param port:
            @param types:
            @return:
            '''
        if self.__isUfw:
            if port.find('-') != -1:
                port = port.replace('-', ':')
            self.add_ufw_rule(source_ip, protocol, port, types)
        elif self.__isFirewalld:
            if port.find(':') != -1:
                port = port.replace(':', '-')
            self.add_firewall_rule(source_ip, protocol, port, types)
        else:
            self.add_iptables_rule(source_ip, protocol, port, types)


    def _del_firewall_rules(self, source_ip, protocol, port, types):
        '''
            删除防火墙规则
            @param source_ip:
            @param protocol:
            @param port:
            @param types:
            @return:
            '''
        if self.__isUfw:
            self.del_ufw_rule(source_ip, protocol, port, types)
        elif self.__isFirewalld:
            self.del_firewall_rule(source_ip, protocol, port, types)
        else:
            self.del_iptables_rule(source_ip, protocol, port, types)


    def _modify_firewall_rules(self, address, protocol, port, type, source_ip, source_protocol, ports, types):
        '''
            修改防火墙规则1
            @param address:
            @param protocol:
            @param port:
            @param type:
            @param source_ip:
            @param source_protocol:
            @param ports:
            @param types:
            @return:
            '''
        if self.__isUfw:
            self.edit_ufw_rule(address, protocol, port, type, source_ip, source_protocol, ports, types)
        elif self.__isFirewalld:
            self.edit_firewall_rule(address, protocol, port, type, source_ip, source_protocol, ports, types)
        else:
            self.edit_iptables_rule(address, protocol, port, type, source_ip, source_protocol, ports, types)


    # 新加代码----- end

    # 端口防扫描 --- start
    def _get_server_lists_scan(self):
        """
            @name 获取服务器常用端口
            @return:
            """
        return {
            "sshd": "{}".format(public.get_sshd_port()),
            "mysql": "{}".format(public.get_mysql_info()["port"]),
            "ftpd": "21",
            "dovecot": "110,143",
            "postfix": "25,465,587",
        }


    def get_anti_scan_logs(self, get):
        """
            @name 获取防扫描日志
            @param get:
            @return:
            """
        get = public.dict_obj()
        server_lists = self._get_server_lists_scan()
        result_dict = {
            "currently_failed": 0,
            "total_failed": 0,
            "currently_banned": 0,
            "total_banned": 0,
            "banned_ip_list": []
        }

        import PluginLoader
        for key in server_lists:
            get.mode = key

            logs_result = PluginLoader.plugin_run('fail2ban', 'get_status', get)
            if type(logs_result['msg']) is dict:
                result_dict["currently_failed"] += int(logs_result["msg"]["currently_failed"])
                result_dict["total_failed"] += int(logs_result["msg"]["total_failed"])
                result_dict["currently_banned"] += int(logs_result["msg"]["currently_banned"])
                result_dict["total_banned"] += int(logs_result["msg"]["total_banned"])
                result_dict["banned_ip_list"] += logs_result["msg"]["banned_ip_list"]

        return result_dict


    def get_anti_scan_status(self, get):
        """
            @name 获取端口防扫描
            @return:
            """
        plugin_path = "/www/server/panel/plugin/fail2ban"
        result_data = {"status": 0, "installed": 1}
        if not os.path.exists("{}".format(plugin_path)):
            result_data['installed'] = 0
            return result_data

        sock = "{}/fail2ban.sock".format(plugin_path)
        if not os.path.exists(sock):
            return result_data

        server_lists = self._get_server_lists_scan()
        s_file = '{}/plugin/fail2ban/config.json'.format(public.get_panel_path())
        if os.path.exists(s_file):
            try:
                data = json.loads(public.readFile(s_file))
                if len(data) == 0:
                    return result_data

                for key in server_lists:
                    if key in data:
                        if data[key]['act'] != 'true':
                            result_data['status'] = 0
                            return result_data

                result_data['status'] = 1
                return result_data
            except:
                pass

        return result_data


    def set_anti_scan_status(self, get):
        """
        @name 设置常用端口防扫描
        @param get:
        @return:
        """
        scan_status = get.status if "status" in get else 0
        param_dict = {
            'type': 'edit',
            'act': 'true' if scan_status == 1 else 'false',
            'maxretry': '30',
            'findtime': '300',
            'bantime': '600',
            'port': '',
            'mode': ''
        }
        server_lists = self._get_server_lists_scan()
        _set_up_path = "/www/server/panel/plugin/fail2ban"
        _config = _set_up_path + "/config.json"
        if not os.path.exists(_set_up_path + "/fail2ban_main.py"):
            return public.returnMsg(False, public.lang("fail2ban plugin is not installed"))

        if os.path.exists(_config):
            try:
                _conf_data = json.loads(public.ReadFile(_config))
            except:
                _conf_data = {}
        else:
            _conf_data = {}

        import PluginLoader

        # if scan_status == "1" and PluginLoader.plugin_run('fail2ban', 'get_fail2ban_status', get) is False:
        #     get.type = "start"
        #     PluginLoader.plugin_run('fail2ban', 'set_fail2ban_status', get)

        for key in server_lists:
            tmp = param_dict.copy()
            tmp["port"] = server_lists[key]
            tmp["mode"] = key

            if key not in _conf_data:
                tmp["type"] = "add"
            else:
                tmp["maxretry"] = _conf_data[key]["maxretry"]
                tmp["findtime"] = _conf_data[key]["findtime"]
                tmp["bantime"] = _conf_data[key]["bantime"]

            tmp = public.to_dict_obj(tmp)

            PluginLoader.plugin_run('fail2ban', 'set_anti', tmp)
            del tmp

        # if scan_status == "0":
        #     get.type = "stop"
        #     PluginLoader.plugin_run('fail2ban', 'set_fail2ban_status', get)

        public.WriteLog("Port Scanning Prevention", "[Security]-[System Firewall]-[Set Port Scanning Prevention]")
        return public.returnMsg(True, public.lang("Setup successful!"))


    def del_ban_ip(self, get):
        """
        删除封锁IP
        @param get:
        @return:
        """
        get.ip = get.ip
        import PluginLoader
        server_lists = self._get_server_lists_scan()
        for key in server_lists:
            get.mode = key
            PluginLoader.plugin_run('fail2ban', 'ban_ip_release', get)

        return public.returnMsg(True, public.lang("Unlocked successfully"))


# 端口防扫描 --- end111


class firewalld:
    __TREE = None
    __ROOT = None
    __CONF_FILE = '/etc/firewalld/zones/public.xml'

    # 初始化配置文件XML对象
    def __init__(self):
        if self.__TREE: return
        if not os.path.exists(self.__CONF_FILE): return
        self.__TREE = ElementTree()
        self.__TREE.parse(self.__CONF_FILE)
        self.__ROOT = self.__TREE.getroot()

    # 获取规则列表
    def GetAcceptPortList(self):
        try:
            mlist = self.__ROOT.getchildren()
        except:
            mlist = []
        data, arry = [], []

        if len(mlist) < 1:
            return data, arry

        data, arry = [], []
        for p in mlist:
            tmp = {}
            if p.tag == 'port':
                tmp["protocol"] = p.attrib['protocol']
                tmp['ports'] = p.attrib['port']
                tmp['types'] = 'accept'
                tmp['address'] = ''
            elif p.tag == 'forward-port':
                tmp["protocol"] = p.attrib['protocol']
                tmp["port"] = p.attrib['port']
                tmp["address"] = p.attrib.get('to-addr', '')
                tmp["to-port"] = p.attrib['to-port']
                arry.append(tmp)
                continue
            elif p.tag == 'rule':
                tmp["types"] = 'accept'
                tmp['ports'] = ''
                tmp['protocol'] = ''
                ch = p.getchildren()
                for c in ch:
                    if c.tag == 'port':
                        tmp['protocol'] = c.attrib['protocol']
                        tmp['ports'] = c.attrib['port']
                    elif c.tag == 'drop':
                        tmp['types'] = 'drop'
                    elif c.tag == 'reject':
                        tmp['types'] = 'reject'
                    elif c.tag == 'source':
                        if "address" in c.attrib.keys():
                            tmp['address'] = c.attrib['address']
                    if "address" not in tmp:
                        tmp['address'] = ''
            else:
                continue
            if tmp:
                data.append(tmp)
        return data, arry

    def recombine_rules(self):
        '''
        重组防火墙规则,将tcp和udp端口相同的规则合并111111
        @return:
        '''
        firewalld_rules = self.GetAcceptPortList()[0]
        tcp_rules = []
        udp_rules = []
        for rule in firewalld_rules:
            if rule['protocol'] == 'tcp':
                tcp_rules.append(rule)
            elif rule['protocol'] == 'udp':
                udp_rules.append(rule)

        result_rules = []

        for tcp_rule in tcp_rules:
            for udp_rule in udp_rules:
                if tcp_rule['ports'] == udp_rule['ports']:
                    if tcp_rule['types'] == udp_rule['types']:
                        if tcp_rule['address'] == udp_rule['address']:
                            if tcp_rule['protocol'] != udp_rule['protocol']:
                                tcp_rule['protocol'] = 'tcp/udp'
                                udp_rules.remove(udp_rule)
                                break
            result_rules.append(tcp_rule)
        result_rules.extend(udp_rules)
        return result_rules


class Sqlite():
    db_file = None  # 数据库文件
    connection = None  # 数据库连接对象

    def __init__(self):
        self.db_file = "/www/server/panel/data/default.db"
        self.create_table()

    # 获取数据库对象
    def GetConn(self):
        try:
            if self.connection == None:
                self.connection = sqlite3.connect(self.db_file)
                self.connection.text_factory = str
        except Exception as ex:
            import traceback
            traceback.print_exc()
            return "error: " + str(ex)

    def create_table(self):
        # 创建firewall_new表记录端口规则
        if not public.M('sqlite_master').where(
                'type=? AND name=?', ('table', 'firewall_new')).count():
            public.M('').execute('''CREATE TABLE "firewall_new" (
                "id" INTEGER PRIMARY KEY AUTOINCREMENT,
                "protocol" TEXT DEFAULT '',
                "ports" TEXT,
                "types" TEXT,
                "address" TEXT DEFAULT '',
                "brief" TEXT DEFAULT '',
                "addtime" TEXT DEFAULT '');''')
            public.M('').execute(
                'CREATE INDEX firewall_new_port ON firewall_new (ports);')

        if public.M('firewall_new').count() < 1:
            # 写入默认数据
            if not public.M('firewall_new').where('ports=?', ('80',)).count():
                public.M('firewall_new').add(
                    'ports,brief,addtime,protocol,types',
                    ('80', 'Website default port', '0000-00-00 00:00:00', 'tcp', 'accept')
                )
            if not public.M('firewall_new').where('ports=?', ('21',)).count():
                public.M('firewall_new').add(
                    'ports,brief,addtime,protocol,types',
                    ('21', 'FTP service', '0000-00-00 00:00:00', 'tcp', 'accept')
                )
            if not public.M('firewall_new').where('ports=?', ('22',)).count():
                public.M('firewall_new').add(
                    'ports,brief,addtime,protocol,types',
                    ('22', 'SSH remote service', '0000-00-00 00:00:00', 'tcp', 'accept')
                )
            try:
                _panel_port_file = '/www/server/panel/data/port.pl'
                panel_port = public.readFile(_panel_port_file).strip(" ").strip("\n")
            except Exception:
                panel_port = '8888'

            if not public.M('firewall_new').where('ports=?', (panel_port,)).count():
                public.M('firewall_new').add(
                    'ports,brief,addtime,protocol,types',
                    (panel_port, 'panel', '0000-00-00 00:00:00', 'tcp', 'accept')
                )

        # 创建firewall_ip表记录IP规则（屏蔽或放行）
        if not public.M('sqlite_master').where(
                'type=? AND name=?', ('table', 'firewall_ip')).count():
            public.M('').execute('''CREATE TABLE "firewall_ip" (
                "id" INTEGER PRIMARY KEY AUTOINCREMENT,
                "types" TEXT,
                "address" TEXT DEFAULT '',
                "brief" TEXT DEFAULT '',
                "addtime" TEXT DEFAULT '');''')
            public.M('').execute(
                'CREATE INDEX firewall_ip_addr ON firewall_ip (address);')

        # 创建firewall_trans表记录端口转发记录
        if not public.M('sqlite_master').where(
                'type=? AND name=?', ('table', 'firewall_trans')).count():
            public.M('').execute('''CREATE TABLE firewall_trans (
                "id" INTEGER PRIMARY KEY AUTOINCREMENT,
                "start_port" TEXT,
                "ended_ip" TEXT,
                "ended_port" TEXT,
                "protocol" TEXT DEFAULT '',
                "addtime" TEXT DEFAULT '');''')
            public.M('').execute(
                'CREATE INDEX firewall_trans_port ON firewall_trans (start_port);'
            )

        # 创建firewall_country表记录IP规则（屏蔽或放行）
        if not public.M('sqlite_master').where(
                'type=? AND name=?', ('table', 'firewall_country')).count():
            public.M('').execute('''CREATE TABLE "firewall_country" (
                "id" INTEGER PRIMARY KEY AUTOINCREMENT,
                "types" TEXT,
                "country" TEXT DEFAULT '',
                "brief" TEXT DEFAULT '',
                "addtime" TEXT DEFAULT '');''')
            public.M('').execute('CREATE INDEX firewall_country_name ON firewall_country (country);')

        # 创建firewall_domain表记录域名规则（屏蔽或放行）
        if not public.M('sqlite_master').where('type=? AND name=?', ('table', 'firewall_domain')).count():
            public.M('').execute('''CREATE TABLE "firewall_domain" (
                "id" INTEGER PRIMARY KEY AUTOINCREMENT,
                "types" TEXT,
                "domain" TEXT,
                "domain_total" TEXT,
                "port" TEXT,
                "sid" int DEFAULT 0,
                "address" TEXT DEFAULT '',
                "brief" TEXT DEFAULT '',
                "protocol" TEXT DEFAULT '',
                "addtime" TEXT DEFAULT '');''')
            public.M('').execute('CREATE INDEX firewall_domain_addr ON firewall_domain (domain);')

        # 修复之前已经创建的 firewall_domain 表无 domain_total 字段的问题
        create_table_str = public.M('firewall_new').table('sqlite_master').where(
            'type=? AND name=?', ('table', 'firewall_new')).getField('sql')
        if 'domain_total' not in create_table_str:
            public.M('firewall_new').execute('ALTER TABLE "firewall_domain" ADD "domain_total" TEXT DEFAULT ""')
        # 修复之前已经创建的 firewall_new 表无 domain 字段的问题
        create_table_str = public.M('firewall_new').table('sqlite_master').where(
            'type=? AND name=?', ('table', 'firewall_new')).getField('sql')
        if 'domain' not in create_table_str:
            public.M('firewall_new').execute('ALTER TABLE "firewall_new" ADD "domain" TEXT DEFAULT ""')
        if 'sid' not in create_table_str:
            public.M('firewall_new').execute('ALTER TABLE "firewall_new" ADD "sid"  int DEFAULT 0')
        # 修复之前已经创建的 firewall_ip 表无 domain 字段的问题
        create_table_str = public.M('firewall_ip').table('sqlite_master').where(
            'type=? AND name=?', ('table', 'firewall_ip')).getField('sql')
        if 'sid' not in create_table_str:
            public.M('firewall_ip').execute('ALTER TABLE "firewall_ip" ADD "sid"  int DEFAULT 0')
        if 'domain' not in create_table_str:
            public.M('firewall_ip').execute('ALTER TABLE "firewall_ip" ADD "domain" TEXT DEFAULT ""')

        # 修复之前已经创建的 firewall_country 表无 ports 字段的问题
        create_table_str = public.M('firewall_country').table('sqlite_master').where(
            'type=? AND name=?', ('table', 'firewall_country')).getField('sql')
        if 'ports' not in create_table_str:
            public.M('firewall_country').execute('ALTER TABLE "firewall_country" ADD "ports" TEXT DEFAULT ""')


    def create_trigger(self, sql):
        self.GetConn()
        self.connection.text_factory = str
        try:
            result = self.connection.execute(sql)
            id = result.lastrowid
            self.connection.commit()
            self.rm_lock()
            return id
        except Exception as ex:
            return "error: " + str(ex)


sql = """
        CREATE TRIGGER update_port AFTER DELETE ON firewall
        when old.port!=''
        BEGIN
            delete from firewall_new where ports = old.port;
            delete from firewall_ip where address = old.port;
        END;
      """
s = Sqlite()
s.create_trigger(sql)
