# coding: utf-8
# -------------------------------------------------------------------
# 宝塔Linux面板
# -------------------------------------------------------------------
# Copyright (c) 2014-2099 宝塔软件(http://bt.cn) All rights reserved.
# -------------------------------------------------------------------
# Author: wzz <wzz@bt.cn>
# -------------------------------------------------------------------
import json
import re
import time
import os

# ------------------------------
# 系统防火墙模型 - 业务接口类
# ------------------------------
import public
from firewallModelV2.firewallBase import Base


class main(Base):

    def __init__(self):
        super().__init__()
        self.check_table_column()
        self.check_table_firewall_forward()

    # 2024/3/14 下午 12:01 获取防火墙状态信息
    def get_firewall_info(self, get):
        """
        @name 获取防火墙统计
        """
        data = {}
        data['port'] = len(self.firewall.list_port())
        data['ip'] = len(self.firewall.list_address())
        data['forward'] = len(self.firewall.list_port_forward())
        data['country'] = public.M('firewall_country').count()
        data['type'] = "firewalld" if self._isFirewalld else "ufw" if self._isUfw else "iptables"
        m_time = public.readFile(self.m_time_file)
        data['update_time'] = public.format_date(times=int(m_time) if m_time else int(time.time()))

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
        return public.return_message(0, 0, data)

    # 2024/3/26 下午 3:40 获取防火墙状态
    def get_status(self, get):
        '''
            @name 获取防火墙状态
            @author wzz <2024/3/26 下午 3:40>
            @param "data":{"参数名":""} <数据类型> 参数描述
            @return dict{"status":True/False,"msg":"提示信息"}
        '''
        # return self.get_firewall_status()
        data = {"status":self.get_firewall_status()}
        return public.return_message(0, 0, data)

    # 2024/3/26 下午 3:42 设置防火墙状态
    def set_status(self, get):
        '''
            @name 设置防火墙状态
            @param "data":{"参数名":""} <数据类型> 参数描述
            @return dict{"status":True/False,"msg":"提示信息"}
        '''
        get.status = get.get('status/s', '1')
        if get.status not in ['0', '1']:
             return public.return_message(-1, 0, public.lang("The parameter is incorrect"))

        if get.status == '1':
            # return self.firewall.start()

            data = self.firewall.start()
            st = 0 if data['status'] else -1
            return public.return_message(st, 0, data['msg'])
        else:
            # return self.firewall.stop()
            data = self.firewall.stop()
            st = 0 if data['status'] else -1
            return public.return_message(st, 0, data['msg'])

    # 2024/5/13 下午3:50 检查指定端口是否已经存在，如果存在则返回False，否则返回True
    def check_port_exist(self, get):
        '''
            @name 检查指定端口是否已经存在，如果存在则返回False，否则返回True
            @author wzz <2024/5/13 下午3:51>
            @param "data":{"参数名":""} <数据类型> 参数描述
            @return dict{"status":True/False,"msg":"提示信息"}
        '''
        port_rules_list = self._port_rules_list(get)
        for item in port_rules_list:
            if item["Port"] == get.port and item["Address"] == get.address and item["Protocol"] == get.protocol and \
                    item["Strategy"] == get.strategy and item["Chain"] == get.chain:
                return False

        return True

    # 2024/5/13 下午4:13 检查指定ip规则是否已经存在，如果存在则返回False，否则返回True
    def check_ip_exist(self, get):
        '''
            @name 检查指定ip规则是否已经存在，如果存在则返回False，否则返回True
            @param "data":{"参数名":""} <数据类型> 参数描述
            @return dict{"status":True/False,"msg":"提示信息"}
        '''
        ip_rules_list = self._ip_rules_list(get)
        for item in ip_rules_list:
            if item["Address"] == get.address and item["Strategy"] == get.strategy and item["Chain"] == get.chain:
                return False

        return True

    # 2024/5/13 下午4:17 检查指定端口转发规则是否已经存在，如果存在则返回False，否则返回True
    def check_forward_exist(self, get):
        '''
            @name 检查指定端口转发规则是否已经存在，如果存在则返回False，否则返回True
            @param "data":{"参数名":""} <数据类型> 参数描述
            @return dict{"status":True/False,"msg":"提示信息"}
        '''
        forward_rules_list = self._port_forward_list(get)
        for item in forward_rules_list:
            if item["S_Address"] == get.S_Address and item["S_Port"] == get.S_Port and item["T_Address"] == get.T_Address and \
                    item["T_Port"] == get.T_Port:
                return False

        return True

    # 2024/3/26 下午 6:09 从数据库中获取端口规则列表
    def get_port_db(self, get):
        '''
            @name 从数据库中获取端口规则列表
            @author wzz <2024/3/26 下午 6:13>
            @param "data":{"参数名":""} <数据类型> 参数描述
            @return dict{"status":True/False,"msg":"提示信息"}
        '''
        try:
            where = '1=1'
            sql = public.M('firewall_new')
            data = sql.where(where, ()).select()

            domain_sql = public.M('firewall_domain')
            domain_data = domain_sql.where(where, ()).select()

            for i in range(len(data)):
                if not "ports" in data[i]:
                    data[i]['status'] = -1
                    continue

                if "brief" in data[i]:
                    data[i]['brief'] = public.xssdecode(data[i]['brief'])

                if not "chain" in data[i]:
                    data[i]['chain'] = "INPUT"
                if "chain" in data[i] and data[i]['chain'] == "":
                    data[i]['chain'] = "INPUT"

                for j in range(len(domain_data)):
                    if "domain" in domain_data[j] and data[i]['address'] in domain_data[j]['domain']:
                        data[i]['domain'] = domain_data[j]['domain']
                        break

            return data
        except Exception as e:
            # public.print_log(public.get_error_info())
            return []

    # 2024/3/26 下午 11:53 从数据库中获取ip规则列表
    def get_ip_db(self, get):
        '''
            @name 从数据库中获取ip规则列表
            @author wzz <2024/3/26 下午 11:53>
            @param "data":{"参数名":""} <数据类型> 参数描述
            @return dict{"status":True/False,"msg":"提示信息"}
        '''
        try:
            where = '1=1'
            sql = public.M('firewall_ip')

            ip_data = sql.where(where, ()).select()
            # public.print_log('数据库 -- ip{}'.format(ip_data))

            for i_data in ip_data:
                if "brief" in i_data:
                    i_data['brief'] = public.xssdecode(i_data['brief'])
                if not "chain" in i_data:
                    i_data['chain'] = "INPUT"
                if "chain" in i_data and i_data['chain'] == "":
                    i_data['chain'] = "INPUT"

            return ip_data
        except Exception as e:
            # public.print_log(public.get_error_info())
            return []

    # 2024/3/26 下午 11:58 从数据库中获取端口转发规则列表
    def get_forward_db(self, get):
        '''
            @name 从数据库中获取端口转发规则列表
            @author wzz <2024/3/26 下午 11:58>
            @param "data":{"参数名":""} <数据类型> 参数描述
            @return dict{"status":True/False,"msg":"提示信息"}
        '''
        try:
            where = '1=1'
            sql = public.M('firewall_forward')

            if hasattr(get, 'query'):
                where = " S_Address like '%{search}%' or S_Port like '%{search}%' or T_Address like '%{search}%' or T_Port like '%{search}%'".format(
                    search=get.query
                )
            res = sql.where(where, ()).select()
            if type(res) != list:
                return []
            return res
        except Exception as e:
            return []

    # 2024/3/26 下午 10:46 构造端口规则返回数据
    def structure_port_return_data(self, list_port, rule_db, query):
        '''
            @name 构造返回数据
            @author wzz <2024/3/26 下午 10:47>
            @param "data":{"参数名":""} <数据类型> 参数描述
            @return dict{"status":True/False,"msg":"提示信息"}
        '''
        new_list = []
        for j in range(len(list_port)):
            list_port[j]['id'] = 0
            list_port[j]['sid'] = 0
            list_port[j]['brief'] = ""
            list_port[j]['domain'] = ""
            if (list_port[j]['Port'].find(":") != -1 or list_port[j]['Port'].find("-") != -1 or
                    list_port[j]['Port'].find("/") != -1 or list_port[j]['Port'].find(".") != -1):
                list_port[j]['status'] = 1
            else:
                try:
                    if not ":" in list_port[j]['Port'] or not "-" in list_port[j]['Port']:
                        list_port[j]['status'] = self.CheckPort(int(list_port[j]['Port']), list_port[j]['Protocol'])
                    else:
                        list_port[j]['status'] = -1
                except:
                    list_port[j]['status'] = -1

            if "Chain" in list_port[j] and list_port[j]['Chain'] == "OUTPUT":
                list_port[j]['status'] = -1

            list_port[j]['addtime'] = "--"

            list_port[j]['Port'] = list_port[j]['Port'].replace(":", "-")

            for i in range(len(rule_db)):
                # 备注不受条件影响
                if rule_db[i]['ports'] == list_port[j]['Port']:
                    list_port[j]['brief'] = rule_db[i]['brief']

                if (rule_db[i]['ports'] == list_port[j]['Port'] and
                        rule_db[i]['protocol'] == list_port[j]['Protocol'] and
                        rule_db[i]['address'].lower() == list_port[j]['Address'].lower() and
                        rule_db[i]['types'] == list_port[j]['Strategy'] and
                        rule_db[i]['chain'] == list_port[j]['Chain']):

                    list_port[j]['id'] = rule_db[i]['id']
                    list_port[j]['sid'] = rule_db[i]['sid']
                    list_port[j]['addtime'] = rule_db[i]['addtime']

                    if "domain" in rule_db[i]:
                        list_port[j]['domain'] = rule_db[i]['domain']

                    break

            if query != "":
                if query in list_port[j]['Port'] or query in list_port[j]['brief'] or query in list_port[j]['Address']:

                    new_list.append(list_port[j])

        if len(new_list) > 0 or query != "":
            return sorted(new_list, key=lambda x: x['addtime'], reverse=True)

        return sorted(list_port, key=lambda x: x['addtime'], reverse=True)

    # 2024/3/27 上午 12:01 构造ip规则返回数据
    def structure_ip_return_data(self, list_ip, rule_db, query):
        '''
            @name 构造ip规则返回数据
            @param "data":{"参数名":""} <数据类型> 参数描述
            @return dict{"status":True/False,"msg":"提示信息"}
        '''
        new_list = []
        for j in range(len(list_ip)):
            list_ip[j]['id'] = 0
            list_ip[j]['sid'] = 0
            list_ip[j]['brief'] = ""
            list_ip[j]['domain'] = ""
            list_ip[j]['addtime'] = "--"

            for i in range(len(rule_db)):
                if (rule_db[i]['address'] == list_ip[j]['Address'] and
                        rule_db[i]['types'] == list_ip[j]['Strategy'] and
                        rule_db[i]['chain'] == list_ip[j]['Chain']):
                    list_ip[j]['id'] = rule_db[i]['id']
                    list_ip[j]['sid'] = rule_db[i]['sid']
                    list_ip[j]['brief'] = rule_db[i]['brief']
                    list_ip[j]['addtime'] = rule_db[i]['addtime']

                    if "domain" in rule_db[i]:
                        list_ip[j]['domain'] = rule_db[i]['domain']

                    break
            if query != "":
                if query in list_ip[j]['brief'] or query in list_ip[j]['Address']:
                    new_list.append(list_ip[j])

        if len(new_list) > 0 or query != "":
            # return public.return_area(sorted(new_list, key=lambda x: x['addtime'], reverse=True), "Address")
            return sorted(new_list, key=lambda x: x['addtime'], reverse=True)

        # return public.return_area(sorted(list_ip, key=lambda x: x['addtime'], reverse=True), "Address")
        return sorted(list_ip, key=lambda x: x['addtime'], reverse=True)

    # 2024/3/27 上午 12:11 构造端口转发规则返回数据
    def structure_forward_return_data(self, list_forward, rule_db, query):
        '''
            @name 构造端口转发规则返回数据
            @author wzz <2024/3/27 上午 12:11>
            @param "data":{"参数名":""} <数据类型> 参数描述
            @return dict{"status":True/False,"msg":"提示信息"}
        '''
        new_list = []
        for j in range(len(list_forward)):
            list_forward[j]['id'] = 0
            list_forward[j]['brief'] = ""
            list_forward[j]['addtime'] = "--"

            for i in range(len(rule_db)):
                if (rule_db[i]['T_Address'] == list_forward[j]['T_Address'] and
                        rule_db[i]['S_Port'] == list_forward[j]['S_Port'] and
                        rule_db[i]['T_Port'] == list_forward[j]['T_Port']):
                    list_forward[j]['id'] = rule_db[i]['id']
                    list_forward[j]['brief'] = rule_db[i]['brief']
                    list_forward[j]['addtime'] = rule_db[i]['addtime']
                    break

            if query != "":
                if (query in list_forward[j]['brief'] or query in list_forward[j]['S_Address'] or query in
                        list_forward[j]['S_Port'] or
                        query in list_forward[j]['T_Address'] or query in list_forward[j]['T_Port']):
                    new_list.append(list_forward[j])

        if len(new_list) > 0 or query != "":
            return sorted(new_list, key=lambda x: x['addtime'], reverse=True)

        return sorted(list_forward, key=lambda x: x['addtime'], reverse=True)

    # 2024/3/25 上午 11:05 获取所有端口规则列表
    def port_rules_list(self, get):
        '''
            @name 获取所有端口规则列表
            @author wzz <2024/3/25 上午 11:06>
            @param "data":{"参数名":""} <数据类型> 参数描述
            @return list[dict{}...]
        '''
        get.chain = get.get('chain/s', 'ALL')
        get.query = get.get('query/s', '')

        rule_db = self.get_port_db(get)
        if get.chain == "INPUT":
            list_port = self.firewall.list_input_port()
        elif get.chain == "OUTPUT":
            list_port = self.firewall.list_output_port()
        else:
            list_port = self.firewall.list_port()

        return public.return_message(0, 0, self.structure_port_return_data(list_port, rule_db, query=get.query))
        # return self.structure_port_return_data(list_port, rule_db, query=get.query)

    def _port_rules_list(self, get):
        '''
            @name 获取所有端口规则列表
            @author wzz <2024/3/25 上午 11:06>
            @param "data":{"参数名":""} <数据类型> 参数描述
            @return list[dict{}...]
        '''
        get.chain = get.get('chain/s', 'ALL')
        get.query = get.get('query/s', '')

        rule_db = self.get_port_db(get)

        if get.chain == "INPUT":
            list_port = self.firewall.list_input_port()
        elif get.chain == "OUTPUT":
            list_port = self.firewall.list_output_port()
        else:
            list_port = self.firewall.list_port()

        return self.structure_port_return_data(list_port, rule_db, query=get.query)

    # 2024/3/26 下午 3:17 导出规则
    def export_rules(self, get):
        '''
            @name 导出规则
            @author wzz <2024/3/26 下午 3:17>
            @param "data":{"参数名":""} <数据类型> 参数描述
            @return dict{"status":True/False,"msg":"提示信息"}
        '''
        get.rule = get.get('rule/s', 'port')
        if get.rule == "port":
            return self.export_port_rules(get)
        elif get.rule == "ip":
            return self.export_ip_rules(get)
        else:
            return self.export_port_forward(get)

    # 2024/3/26 下午 3:18 导入规则
    def import_rules(self, get):
        '''
            @name 导入规则
            @param "data":{"参数名":""} <数据类型> 参数描述
            @return dict{"status":True/False,"msg":"提示信息"}
        '''
        # 2024/4/17 下午4:47 检查防火墙状态，如果未启动则不允许设置导入规则
        if not self.get_firewall_status():
             return public.return_message(-1, 0, public.lang("Start the firewall before importing the rules!"))

        get.rule = get.get('rule/s', 'port')
        if get.rule == "port":
            return self.import_port_rules(get)
        elif get.rule == "ip":
            return self.import_ip_rules(get)
        else:
            return self.import_port_forward(get)

    # 2024/3/26 下午 2:38 导出所有端口规则
    def export_port_rules(self, get):
        '''
            @name 导出所有端口规则
            @author wzz <2024/3/26 下午 2:39>
            @param "data":{"参数名":""} <数据类型> 参数描述
            @return dict{"status":True/False,"msg":"提示信息"}
        '''
        get.chain = get.get('chain/s', 'all')

        if get.chain == "INPUT":
            file_name = "input_port_rules_{}".format(int(time.time()))
        elif get.chain == "OUTPUT":
            file_name = "output_port_rules_{}".format(int(time.time()))
        else:
            file_name = "port_rules_{}".format(int(time.time()))

        data = self._port_rules_list(get)
        if not data:
             return public.return_message(-1, 0, public.lang("No rules can be exported"))
        if not os.path.exists(self.config_path):
            os.makedirs(self.config_path, exist_ok=True)
        file_path = "{}/{}.json".format(self.config_path, file_name)

        public.writeFile(file_path, public.GetJson(data))
        public.WriteLog("system firewall", "Export port rules")
        return public.return_message(0, 0,  file_path)

    # 2024/3/26 下午 2:41 导入端口规则
    def import_port_rules(self, get):
        '''
            @name 导入端口规则
            @author wzz <2024/3/26 下午 2:58>
            @param "data":{"参数名":""} <数据类型> 参数描述
            @return dict{"status":True/False,"msg":"提示信息"}
        '''
        get.file = get.get('file/s', '')

        if not get.file:
             return public.return_message(-1, 0, public.lang("The file cannot be empty"))

        if not os.path.exists(get.file):
             return public.return_message(-1, 0, public.lang("The file does not exist"))

        try:
            data = public.readFile(get.file)
            if "|" in data and not "{" in data:
                get.rule_name = "port_rule"
                return self.import_rules_old(get)

            data = json.loads(data)
            # 2024/4/10 下午2:51 反转数据
            data.reverse()
        except:
             return public.return_message(-1, 0, public.lang("The file content is abnormal or malformed"))

        args = public.dict_obj()
        for item in data:
            args.operation = 'add'
            args.protocol = item['Protocol']
            args.port = item['Port']
            args.strategy = item['Strategy']
            args.chain = item['Chain']
            args.address = item.get('Address', 'all')
            args.brief = item.get('brief', '')
            args.reload = "0"

            self.set_port_rule(args)

        if self._isFirewalld:
            self.firewall.reload()

        return public.return_message(0, 0, public.lang("The import was successful"))

    # 2024/5/14 上午10:27 调用旧的导入规则方法
    def import_rules_old(self, get):
        '''
            @name 调用旧的导入规则方法
            @param "data":{"参数名":""} <数据类型> 参数描述
            @return dict{"status":True/False,"msg":"提示信息"}
        '''
        try:
            from safeModel.firewallModel import main as firewall
            firewall_obj = firewall()
            get.file_name = get.file.split("/")[-1]
            firewall_obj.import_rules(get)

            return public.return_message(0, 0, public.lang("The import was successful"))
        except Exception as e:
             return public.return_message(-1, 0,  str(e))

    # 2024/3/26 上午 9:30 处理多个ip以换行的方式添加/删除
    def set_nline_port_ip(self, get):
        '''
            @name 处理多个ip以换行的方式添加/删除
            @author wzz <2024/3/26 上午 9:32>
            @param "data":{"参数名":""} <数据类型> 参数描述
            @return dict{"status":True/False,"msg":"提示信息"}
        '''
        address = get.address.split("\n")
        failed_list = []
        for addr in address:
            if not public.checkIp(addr):
                 return {'status': False, 'msg':  'The destination address is in the wrong format'}

            get.address = addr
            if get.chain == "INPUT":
                result = self.input_port(get)
            else:
                result = self.output_port(get)

            if not result['status']:
                failed_list.append({
                    "address": addr,
                    "msg": result['msg']
                })
        if len(failed_list) > 0:
            return {'status': True, 'msg': 'The setting succeeds, but the following rule settings fail:{}'.format(failed_list)}

        # if self._isFirewalld:
        #     self.firewall.reload()

        return {'status': True, 'msg': 'The setup was successful'}

    # 2024/3/26 上午 9:30 处理多个ip以逗号的方式添加/删除
    def set_tline_port_ip(self, get):
        '''
            @name 处理多个ip以逗号的方式添加
            @author wzz <2024/3/26 上午 9:32>
            @param "data":{"参数名":""} <数据类型> 参数描述
            @return dict{"status":True/False,"msg":"提示信息"}
        '''
        address = get.address.split(",")
        failed_list = []
        for addr in address:
            if not public.checkIp(addr):
                 return  {'status': False, 'msg':  'The destination address is in the wrong format'}

            get.address = addr
            if get.chain == "INPUT":
                result = self.input_port(get)
            else:
                result = self.output_port(get)

            if not result['status']:
                failed_list.append({
                    "address": addr,
                    "msg": result['msg']
                })
        if len(failed_list) > 0:
            return {'status': True, 'msg':  'The setting succeeds, but the following rule settings fail::{}'.format(failed_list)}

        # if self._isFirewalld:
        #     self.firewall.reload()

        return {'status': True, 'msg':  'The setup was successful'}

    # 2024/3/26 上午 9:34 处理192.168.1.10-192.168.1.20这种范围ip的添加/删除
    def set_range_port_ip(self, get):
        '''
            @name 处理192.168.1.10-192.168.1.20这种范围ip的添加/删除
            @author wzz <2024/3/26 上午 9:35>
            @param "data":{"参数名":""} <数据类型> 参数描述
            @return dict{"status":True/False,"msg":"提示信息"}
        '''
        address = self.firewall.handle_ip_range(get.address)
        failed_list = []
        for addr in address:
            get.address = addr
            if get.chain == "INPUT":
                result = self.input_port(get)
            else:
                result = self.output_port(get)

            if not result['status']:
                failed_list.append({
                    "address": addr,
                    "msg": result['msg']
                })
        if len(failed_list) > 0:
            return {'status': True, 'msg':  'The setting succeeds, but the following rule settings fail::{}'.format(failed_list)}

        # if self._isFirewalld:
        #     self.firewall.reload()

        return {'status': True, 'msg':   'The setup was successful'}


    # 2024/3/25 下午 6:27 设置端口规则
    def set_port_rule(self, get:public.dict_obj):
        '''
            @name 设置端口规则
            @author wzz <2024/3/25 下午 6:28>
            @param "data":{"参数名":""} <数据类型> 参数描述
            @return dict{"status":True/False,"msg":"提示信息"}
        '''

        # 2024/4/17 下午4:47 检查防火墙状态，如果未启动则不允许设置端口规则
        if not self.get_firewall_status():
             return public.return_message(-1, 0, public.lang("Please activate the firewall before setting up the rules!"))
        get.operation = get.get('operation/s', 'add')
        get.protocol = get.get('protocol/s', 'tcp')
        get.address = get.get('address/s', 'all')
        get.port = get.get('port/s', '')
        get.strategy = get.get('strategy/s', 'accept')
        get.chain = get.get('chain/s', 'INPUT')
        get.reload = get.get('reload/s', "1")
        get.brief = get.get('brief/s', '')

        if get.address == "Anywhere" or get.address == "":
            get.address = "all"

        if get.protocol == "all":
            get.protocol = "tcp/udp"

        if get.port == "":
             return public.return_message(-1, 0, public.lang("The destination port cannot be empty"))

        from copy import deepcopy
        if get.address != "all" and "," in get.address:
            # args1 = copy.deepcopy(get)
            args1 = public.to_dict_obj(deepcopy(get.get_items()))
            address_list = get.address.split(",")
            for address in address_list:
                args1.address = address
                result = self.more_prot_rule(args1)
                if not result['status']:
                    return public.return_message(-1, 0, result['msg'])
        if get.address != "all" and "\n" in get.address:
            # args2 = copy.deepcopy(get)
            args2 = public.to_dict_obj(deepcopy(get.get_items()))
            address_list = get.address.split("\n")
            for address in address_list:
                args2.address = address
                result = self.more_prot_rule(args2)
                if not result['status']:
                    return public.return_message(-1, 0, result['msg'])
        else:

            result = self.more_prot_rule(get)
            if not result['status']:
                return public.return_message(-1, 0, result['msg'])

        if self._isFirewalld and get.reload == "1":
            self.firewall.reload()

        return public.return_message(0, 0, public.lang("The setup was successful"))


    # 2024/3/29 下午 4:04 处理多个ip的端口规则情况
    def more_prot_rule(self, get):
        '''
            @name 处理多个ip的端口规则情况
            @author wzz <2024/3/29 下午 4:02>
            @param "data":{"参数名":""} <数据类型> 参数描述
            @return dict{"status":True/False,"msg":"提示信息"}
        '''
        if get.port.find(",") != -1:
            from copy import deepcopy
            args = public.to_dict_obj(deepcopy(get.get_items()))
            port_list = get.port.split(",")
            for port in port_list:
                args.port = port
                result = self.exec_port_rule(args)
                if not result['status']:
                    return result
            return {'status': True, 'msg': 'The setup was successful'}
        else:
            return self.exec_port_rule(get)

    # 2024/3/28 下午 6:29 执行端口设置
    def exec_port_rule(self, get):
        '''
            @name 执行端口设置
            @author wzz <2024/3/28 下午 6:29>
            @param "data":{"参数名":""} <数据类型> 参数描述
            @return dict{"status":True/False,"msg":"提示信息"}
        '''
        if get.operation == "add" and not self.check_port_exist(get):
             return {'status': False, 'msg': 'Port {} already exists, do not add it repeatedly'.format(get.port)}
        self.set_port_db(get)

        # 2024/3/25 下午 8:23 处理多个ip的情况,例如出现每行一个ip
        if get.address != "all" and "\n" in get.address:
            return self.set_nline_port_ip(get)
        elif get.address != "all" and "-" in get.address:
            return self.set_range_port_ip(get)
        elif get.address != "all" and "," in get.address:
            return self.set_tline_port_ip(get)
        elif get.address != "all" and "/" in get.address:
            if get.chain == "INPUT":
                result = self.input_port(get)
            else:
                result = self.output_port(get)
        elif get.address != "all" and not public.checkIp(get.address) and not public.is_ipv6(get.address):
             return  {'status': False, 'msg':  'The specified IP address is in the wrong format'}
        else:
            if get.chain == "INPUT":
                result = self.input_port(get)
            else:
                result = self.output_port(get)

        return result

    # 2024/5/14 上午10:40 前置检测ip是否合法
    def _check_ips(self, get):
        '''
            @name 前置检测ip是否合法
            @author wzz <2024/5/14 上午10:40>
            @param "data":{"参数名":""} <数据类型> 参数描述
            @return dict{"status":True/False,"msg":"提示信息"}
        '''
        # public.print_log("进入检查ip--{}".format(get.address))

        if get.address != "all" and "\n" in get.address:
            address = get.address.split("\n")

            for addr in address:

                if addr != "all" and not public.checkIp(addr) and not public.is_ipv6(addr):
                    public.print_log("ip--{}".format(addr))
                    return public.returnMsg(False, public.lang("The specified IP address is in the wrong format 1"))
        elif get.address != "all" and "," in get.address:
            address = get.address.split(",")
            for addr in address:
                if addr != "all" and not public.checkIp(addr) and not public.is_ipv6(addr):
                    public.print_log("ip--{}".format(addr))
                    return public.returnMsg(False, public.lang("The specified IP address is in the wrong format2"))
        else:
            if get.address != "all" and not public.checkIp(get.address) and not public.is_ipv6(get.address):
                public.print_log("ip--{}".format(get.address))
                return public.returnMsg(False, public.lang("The specified IP address is in the wrong format 3"))

        return public.returnMsg(True, public.lang("ok"))

    def check_ips(self, get):
        '''
            @name 前置检测ip是否合法
            @author wzz <2024/5/14 上午10:40>
            @param "data":{"参数名":""} <数据类型> 参数描述
            @return dict{"status":True/False,"msg":"提示信息"}
        '''
        if get.address != "all" and "\n" in get.address:
            address = get.address.split("\n")
            for addr in address:
                if addr != "all" and not public.checkIp(addr) and not public.is_ipv6(addr):
                     return public.return_message(-1, 0, public.lang("The specified IP address is in the wrong format"))
        elif get.address != "all" and "," in get.address:
            address = get.address.split(",")
            for addr in address:
                if addr != "all" and not public.checkIp(addr) and not public.is_ipv6(addr):
                     return public.return_message(-1, 0, public.lang("The specified IP address is in the wrong format"))
        else:
            if get.address != "all" and not public.checkIp(get.address) and not public.is_ipv6(get.address):
                 return public.return_message(-1, 0, public.lang("The specified IP address is in the wrong format"))

        return public.return_message(0, 0, public.lang("ok"))
    # 2024/3/27 上午 9:37 修改端口规则
    def modify_port_rule(self, get):
        '''
            @name 修改端口规则
            @author wzz <2024/3/27 上午 9:38>
            @param "data":{"参数名":""} <数据类型> 参数描述
            @return dict{"status":True/False,"msg":"提示信息"}
        '''
        # 2024/4/17 下午4:47 检查防火墙状态，如果未启动则不允许设置规则
        if not self.get_firewall_status():
             return public.return_message(-1, 0, public.lang("Please activate the firewall before setting up the rules!"))
        get.old_data = get.get('old_data/s', '')
        get.new_data = get.get('new_data/s', '')

        if get.old_data == "":
             return public.return_message(-1, 0, public.lang("Please pass in old_data"))

        if get.new_data == "":
             return public.return_message(-1, 0, public.lang("Please pass in new_data"))

        get.old_data = json.loads(get.old_data)
        get.new_data = json.loads(get.new_data)

        # 修改address  只有指定ip才传参
        if "address" in get.new_data:
            if get.new_data['address'] != '' or get.new_data['address'] != 'Anywhere':
                get.address = get.new_data['address']
                if not self._check_ips(get)["status"]:
                     return public.return_message(-1, 0, public.lang("The modified IP address is incorrectly formatted"))

        args1 = public.dict_obj()
        args1.operation = 'remove'
        args1.port = get.old_data['Port']
        args1.protocol = get.old_data['Protocol']
        args1.address = get.old_data['Address']
        args1.strategy = get.old_data['Strategy']
        args1.chain = get.old_data['Chain']
        args1.id = get.old_data['id']
        args1.sid = get.old_data['sid']
        args1.reload = "0"
        self.set_port_rule(args1)

        args2 = public.dict_obj()
        args2.operation = 'add'
        args2.port = get.new_data['port']
        args2.protocol = get.new_data['protocol']
        args2.address = get.new_data['address'] if "address" in get.new_data else "all"
        args2.strategy = get.new_data['strategy']
        args2.chain = get.new_data['chain']
        args2.brief = get.new_data['brief'] if 'brief' in get.new_data else ""
        args2.reload = "1"
        self.set_port_rule(args2)

        return public.return_message(0, 0, public.lang("The modification was successful"))

    # 2024/3/27 下午 4:03 修改域名端口规则
    def modify_domain_port_rule(self, get):
        '''
            @name 修改域名端口规则
            @param "data":{"参数名":""} <数据类型> 参数描述
            @return dict{"status":True/False,"msg":"提示信息"}
        '''
        # 2024/4/17 下午4:47 检查防火墙状态，如果未启动则不允许设置设置规则
        if not self.get_firewall_status():
             return public.return_message(-1, 0, public.lang("Please activate the firewall before setting up the rules!"))
        get.old_data = get.get('old_data/s', '')
        get.new_data = get.get('new_data/s', '')

        if get.old_data == "":
             return public.return_message(-1, 0, public.lang("Please pass in old_data"))

        if get.new_data == "":
             return public.return_message(-1, 0, public.lang("Please pass in new_data"))

        get.old_data = json.loads(get.old_data)
        get.new_data = json.loads(get.new_data)

        address = self.get_a_ip(get.new_data['domain'])

        if address == "":
             return public.return_message(-1, 0, public.lang("Domain name: 【{}】Resolution failed", get.domain))

        args1 = public.dict_obj()
        args1.operation = 'remove'
        args1.port = get.old_data['Port']
        args1.protocol = get.old_data['Protocol']
        args1.address = get.old_data['Address']
        args1.strategy = get.old_data['Strategy']
        args1.chain = get.old_data['Chain']
        args1.id = get.old_data['id']
        args1.sid = get.old_data['sid']
        self.set_port_rule(args1)

        args2 = public.dict_obj()
        args2.operation = 'add'
        args2.port = get.new_data['port']
        args2.protocol = get.new_data['protocol']
        args2.address = address
        args2.strategy = get.new_data['strategy']
        args2.chain = get.new_data['chain']
        args2.brief = get.new_data['brief'] if "brief" in get.new_data else ""
        args2.domain = get.new_data['domain']
        self.set_port_rule(args2)

        if self._isFirewalld:
            self.firewall.reload()

        return public.return_message(0, 0, public.lang("The modification was successful"))

    # 2024/3/26 下午 5:10 设置域名端口规则
    def set_domain_port_rule(self, get):
        '''
            @name 设置域名端口规则
            @author wzz <2024/3/26 下午 5:11>
            @param "data":{"参数名":""} <数据类型> 参数描述
            @return dict{"status":True/False,"msg":"提示信息"}
        '''
        # 2024/4/17 下午4:47 检查防火墙状态，如果未启动则不允许设置规则
        if not self.get_firewall_status():
             return public.return_message(-1, 0, public.lang("Please activate the firewall before setting up the rules!"))

        get.operation = get.get('operation/s', 'add')
        get.protocol = get.get('protocol/s', 'tcp')
        get.domain = get.get('domain/s', '')
        get.port = get.get('port/s', '')
        get.strategy = get.get('strategy/s', 'accept')
        get.chain = get.get('chain/s', 'INPUT')

        if get.domain == "":
             return public.return_message(-1, 0, public.lang("The destination domain name cannot be empty"))

        if get.port == "":
             return public.return_message(-1, 0, public.lang("The destination port cannot be empty"))

        if not public.is_domain(get.domain):
             return public.return_message(-1, 0, public.lang("The destination domain name is in the wrong format"))

        if "|" in get.domain:
            get.domain = get.domain.split("|")[0]

        address = self.get_a_ip(get.domain)

        if address == "":
             return public.return_message(-1, 0, public.lang("Domain name: 【{}】Resolution failed", get.domain))

        get.address = address
        self.set_port_db(get)

        if get.chain == "INPUT":
            result = self.input_port(get)
        else:
            result = self.output_port(get)

        if result['status'] and self._isFirewalld:
            self.firewall.reload()

        return public.return_message(0, 0, result['msg'])

    # 2024/5/13 下午4:46 添加端口规则到指定数据库
    def add_port_db(self, get, protocol, addtime, domain):
        '''
            @name 添加端口规则到指定数据库
            @author wzz <2024/5/13 下午4:46>
            @param "data":{"参数名":""} <数据类型> 参数描述
            @return dict{"status":True/False,"msg":"提示信息"}
        '''
        try:
            add_sid = public.M('firewall_new').add(
                'ports,brief,protocol,address,types,addtime,domain,sid,chain',
                (
                    get.port, public.xsssec(get.brief), protocol, get.address, get.strategy, addtime, domain, 0,
                    get.chain)
            )

            if get.domain != "":
                domain_sid = public.M('firewall_domain').add(
                    'types,domain,port,address,brief,addtime,sid,protocol,domain_total',
                    (get.strategy, domain, get.port, get.address, public.xsssec(get.brief),
                     addtime, add_sid, get.protocol, get.domain)
                )
                public.M('firewall_new').where("id=?", (add_sid,)).save('sid', domain_sid)
                self.check_resolve_crontab()
        except:

            public.print_log(public.get_error_info())
    # 2024/5/13 下午4:49 从指定数据库删除端口规则
    def remove_port_db(self, get, protocol, addtime, domain):
        '''
            @name 从指定数据库删除端口规则
            @param "data":{"参数名":""} <数据类型> 参数描述
            @return dict{"status":True/False,"msg":"提示信息"}
        '''
        public.M('firewall_new').where("ports=? and protocol=? and address=? and types=? and chain=?", (
            get.port, protocol, get.address, get.strategy, get.chain
        )).delete()
        get.domain = get.get('domain/s', '')
        if get.domain != "":
            public.M('firewall_domain').where("domain=?", (get.domain)).delete()

        self.remove_resolve_crontab()

    # 2024/3/26 下午 5:52 添加/删除数据库的端口规则
    def set_port_db(self, get):
        '''
            @name 添加/删除数据库的端口规则
            @param "data":{"参数名":""} <数据类型> 参数描述
            @return dict{"status":True/False,"msg":"提示信息"}
        '''
        try:
            if get.operation == "add":
                # 检测端口是否已经添加过
                query_result = public.M('firewall_new').where(
                    'ports=? and address=? and protocol=? and types=? and chain=?',
                    (get.port, get.address, get.protocol, get.strategy, get.chain)
                ).find()
                # public.print_log("检测端口是否已经添加过---{}".format(query_result))
                if not query_result:
                    get.domain = get.get('domain/s', '')
                    domain = "{}|{}".format(get.domain, get.address) if get.domain != "" else ""
                    addtime = time.strftime('%Y-%m-%d %X', time.localtime())
                    # public.print_log("进入添加方法---{}".format(addtime))

                    if get.protocol == "tcp/udp" and self._isFirewalld:
                        self.add_port_db(get, "tcp", addtime, domain)
                        self.add_port_db(get, "udp", addtime, domain)
                    else:
                        self.add_port_db(get, get.protocol, addtime, domain)
            else:

                query_result = public.M('firewall_new').where(
                    'ports=? and address=? and protocol=? and types=? and chain=?',
                    (get.port, get.address, get.protocol, get.strategy, get.chain)
                ).find()
                if query_result:
                    if get.protocol == "tcp/udp" and self._isFirewalld:
                        self.remove_port_db(get, "tcp", query_result['addtime'], query_result['domain'])
                        self.remove_port_db(get, "udp", query_result['addtime'], query_result['domain'])
                    else:
                        self.remove_port_db(get, get.protocol, query_result['addtime'], query_result['domain'])
        except:
            public.print_log(public.get_error_info())

    # 2024/3/26 下午 11:23 添加/删除数据库的ip规则
    def set_ip_db(self, get):
        '''
            @name 添加/删除数据库的ip规则
            @author wzz <2024/3/26 下午 11:24>
            @param "data":{"参数名":""} <数据类型> 参数描述
            @return dict{"status":True/False,"msg":"提示信息"}
        '''

        if get.operation == "add":
            get.domain = get.get('domain/s', '')
            domain = "{}|{}".format(get.domain, get.address) if get.domain != "" else ""
            query_result = public.M('firewall_ip').where("address=? and types=? and domain=? and chain=?",
                                                         (get.address, get.strategy, domain, get.chain)).find()

            if not query_result:
                addtime = time.strftime('%Y-%m-%d %X', time.localtime())
                self._add_sid = public.M('firewall_ip').add(
                    'address,types,brief,addtime,domain,sid,chain',
                    (get.address, get.strategy, public.xsssec(get.brief), addtime, domain, 0, get.chain)
                )

                if get.domain != "":
                    domain_sid = public.M('firewall_domain').add(
                        'types,domain,port,address,brief,addtime,sid,protocol,domain_total',
                        (get.strategy, domain, '', get.address, public.xsssec(get.brief), addtime, self._add_sid, '',
                         get.domain)
                    )
                    public.M('firewall_ip').where("id=?", (self._add_sid,)).save('sid', domain_sid)
                    self.check_resolve_crontab()
        else:
            get.address = get.get("address/s", '')
            get.strategy = get.get("strategy/s", '')
            if get.address == "":
                 return public.return_message(-1, 0, public.lang("Please pass in id"))
            public.M('firewall_ip').where("address=? and types=? and chain=?", (get.address, get.strategy, get.chain)).delete()
            get.domain = get.get('domain/s', '')
            if get.domain != "":
                public.M('firewall_domain').where("domain=?", (get.domain)).delete()

            self.remove_resolve_crontab()



    # 2024/3/26 下午 11:40 添加/删除数据库的端口转发规则
    def set_forward_db(self, get):
        '''
            @name 添加/删除数据库的端口转发规则
            @author wzz <2024/3/26 下午 11:40>
            @param "data":{"参数名":""} <数据类型> 参数描述
            @return dict{"status":True/False,"msg":"提示信息"}
        '''
        if get.operation == "add":
            query_result = public.M('firewall_forward').where("S_Port=? and T_Address=? and T_Port=? and Protocol=?", (
                get.S_Port, get.T_Address, get.T_Port, get.protocol
            )).find()

            if not query_result:
                get.brief = get.get('brief/s', '')
                addtime = time.strftime('%Y-%m-%d %X', time.localtime())
                self._add_sid = public.M('firewall_forward').add(
                    'S_Port,T_Address,T_Port,Protocol,Family,addtime,brief',
                    (get.S_Port, get.T_Address, get.T_Port, get.protocol, "ipv4", addtime, get.brief)
                )
        else:
            public.M('firewall_forward').where(
                "S_Port=? and T_Address=? and T_Port=? and Protocol=?",
                (get.S_Port, get.T_Address, get.T_Port, get.protocol)
            ).delete()

    # 2024/3/25 下午 6:55 入站端口规则
    def input_port(self, get):
        '''
            @name 入站端口规则
            @param "data":{"参数名":""} <数据类型> 参数描述 dabao
            @return list[dict{}...]
        '''


        info = {
            "Port": get.port,
            "Protocol": get.protocol.lower(),
            "Strategy": get.strategy.lower(),
            "Family": "ipv4",
        }

        if ":" in get.address:
            info["Family"] = "ipv6"

        if get.address != "all":
            info["Address"] = get.address
            result = self.firewall.rich_rules(info=info, operation=get.operation)
        elif get.address == "all" and get.strategy == "drop":
                result = self.firewall.rich_rules(info=info, operation=get.operation)
        else:
            result = self.firewall.input_port(info=info, operation=get.operation)

        return result

    # 2024/3/25 下午 6:56 出站端口规则
    def output_port(self, get):
        '''
            @name 出站端口规则
            @author wzz <2024/3/25 下午 6:56>
            @param "data":{"参数名":""} <数据类型> 参数描述
            @return dict{"status":True/False,"msg":"提示信息"}
        '''
        info = {
            "Port": get.port,
            "Protocol": get.protocol.lower(),
            "Strategy": get.strategy.lower(),
            "Priority": "0",
            "Family": "ipv4",
        }

        if ":" in get.address:
            info["Family"] = "ipv6"

        if get.address != "all":
            info["Address"] = get.address
            result = self.firewall.output_rich_rules(info=info, operation=get.operation)
        else:
            result = self.firewall.output_port(info=info, operation=get.operation)

        return result

    # 2024/3/26 上午 9:40 处理多个ip的情况,例如出现每行一个ip
    def set_nline_ip_rule(self, get):
        '''
            @name 处理多个ip的情况,例如出现每行一个ip
            @author wzz <2024/3/26 上午 9:40>
            @param "data":{"参数名":""} <数据类型> 参数描述
            @return dict{"status":True/False,"msg":"提示信息"}
        '''
        address = get.address.split("\n")
        failed_list = []
        from copy import deepcopy
        for addr in address:
            if not public.is_ipv4(addr) and not public.is_ipv6(addr):
                continue

            # args = copy.deepcopy(get)
            args = public.to_dict_obj(deepcopy(get.get_items()))
            args.address = addr
            args.family = "ipv4" if ":" not in addr else "ipv6"

            if self.check_is_user_ip(args):
                continue

            if get.operation == "add" and not self.check_ip_exist(args):
                continue

            self.set_ip_db(args)

            info = {
                "Address": args.address,
                "Family": args.family,
                "Strategy": args.strategy,
                "Priority": args.priority,
            }

            if args.chain == "INPUT":
                result = self.firewall.rich_rules(info=info, operation=args.operation)
            else:
                result = self.firewall.output_rich_rules(info=info, operation=args.operation)

            if not result['status']:
                failed_list.append({
                    "address": addr,
                    "msg": result['msg']
                })
        if len(failed_list) > 0:
            return public.return_message(0, 0, public.lang("The setting succeeds, but the following rule settings fail::{}", failed_list))

        if self._isFirewalld:
            self.firewall.reload()

        return public.return_message(0, 0, public.lang("The setup was successful"))

    # 2024/3/26 上午 9:40 处理多个ip的情况,例如出现逗号隔开ip
    def set_tline_ip_rule(self, get):
        '''
            @name 处理多个ip的情况,例如出现逗号隔开ip
            @author wzz <2024/3/26 上午 9:40>
            @param "data":{"参数名":""} <数据类型> 参数描述
            @return dict{"status":True/False,"msg":"提示信息"}
        '''
        address = get.address.split(",")
        failed_list = []
        from copy import deepcopy
        for addr in address:
            if not public.checkIp(addr):
                 return public.return_message(-1, 0, public.lang("The destination address is in the wrong format"))

            # args = copy.deepcopy(get)
            args = public.to_dict_obj(deepcopy(get.get_items()))
            args.address = addr

            if self.check_is_user_ip(args):
                continue

            if get.operation == "add" and not self.check_ip_exist(args):
                continue

            self.set_ip_db(args)

            info = {
                "Address": args.address,
                "Family": args.family,
                "Strategy": args.strategy,
                "Priority": args.priority,
            }

            if args.chain == "INPUT":
                result = self.firewall.rich_rules(info=info, operation=args.operation)
            else:
                result = self.firewall.output_rich_rules(info=info, operation=args.operation)

            if not result['status']:
                failed_list.append({
                    "address": addr,
                    "msg": result['msg']
                })
        if len(failed_list) > 0:
            return public.return_message(0, 0, public.lang("The setting succeeds, but the following rule settings fail::{}", failed_list))

        if self._isFirewalld:
            self.firewall.reload()

        return public.return_message(0, 0, public.lang("The setup was successful"))

    # 2024/3/26 上午 9:43 处理192.168.1.10-192.168.1.20这种范围ip的添加/删除
    def set_range_ip_rule(self, get):
        '''
            @name 处理192.168.1.10-192.168.1.20这种范围ip的添加/删除
            @author wzz <2024/3/26 上午 9:43>
            @param "data":{"参数名":""} <数据类型> 参数描述
            @return dict{"status":True/False,"msg":"提示信息"}
        '''
        address = self.firewall.handle_ip_range(get.address)
        failed_list = []
        from copy import deepcopy
        for addr in address:
            # args = copy.deepcopy(get)
            args = public.to_dict_obj(deepcopy(get.get_items()))
            args.address = addr

            if self.check_is_user_ip(args):
                continue

            if get.operation == "add" and not self.check_ip_exist(args):
                continue

            self.set_ip_db(args)

            info = {
                "Address": args.address,
                "Family": args.family,
                "Strategy": args.strategy,
                "Priority": args.priority,
            }

            if args.chain == "INPUT":
                result = self.firewall.rich_rules(info=info, operation=args.operation)
            else:
                result = self.firewall.output_rich_rules(info=info, operation=args.operation)

            if not result['status']:
                failed_list.append({
                    "address": addr,
                    "msg": result['msg']
                })
        if len(failed_list) > 0:
            return public.return_message(0, 0, public.lang("The setting succeeds, but the following rule settings fail::{}", failed_list))

        if self._isFirewalld:
            self.firewall.reload()

        return public.return_message(0, 0, public.lang("The setup was successful"))

    # 2024/3/26 上午 9:46 设置带掩码的ip段
    def set_mask_ip_rule(self, get):
        '''
            @name 设置带掩码的ip段
            @author wzz <2024/3/26 上午 9:47>
            @param "data":{"参数名":""} <数据类型> 参数描述
            @return dict{"status":True/False,"msg":"提示信息"}
        '''
        if get.operation == "add" and not self.check_ip_exist(get):
             return public.return_message(-1, 0, public.lang("The destination address {} already exists, please do not add it repeatedly", get.address))

        self.set_ip_db(get)
        info = {
            "Address": get.address,
            "Family": get.family,
            "Strategy": get.strategy,
            "Priority": get.priority,
        }

        if get.chain == "INPUT":
            result = self.firewall.rich_rules(info=info, operation=get.operation)
        else:
            result = self.firewall.output_rich_rules(info=info, operation=get.operation)

        if result['status'] and self._isFirewalld:
            self.firewall.reload()

        # return result
        return public.return_message(0, 0, result['msg'])

    # 2024/4/9 下午11:31 检查是否会自己的ip，如果是则返回
    def check_is_user_ip(self, get):
        '''
            @name
            @author wzz <2024/4/9 下午11:31>
            @param "data":{"参数名":""} <数据类型> 参数描述
            @return dict{"status":True/False,"msg":"提示信息"}
        '''
        # 2024/3/26 下午 11:27 处理用户当前的远程ip，如果添加的ip与此ip一直则返回
        try:
            from flask import request
            user_ip = request.remote_addr
            if user_ip in get.address:
                return True
            return False
        except:
            return False
        
    # 2024/3/25 下午 7:16 设置ip规则
    def set_ip_rule(self, get):
        '''
            @name 设置ip规则
            @author wzz <2024/3/25 下午 7:16>
            @param "data":{"参数名":""} <数据类型> 参数描述
            @return dict{"status":True/False,"msg":"提示信息"}
        '''
        # 2024/4/17 下午4:47 检查防火墙状态，如果未启动则不允许设置规则
        if not self.get_firewall_status():
             return public.return_message(-1, 0, public.lang("Please activate the firewall before setting up the rules!"))

        get.operation = get.get('operation/s', 'add')
        get.address = get.get('address/s', '')
        get.strategy = get.get('strategy/s', 'accept')
        get.chain = get.get('chain/s', 'INPUT')
        get.family = get.get('family/s', 'ipv4')
        get.priority = get.get('priority/s', '0')
        get.reload = get.get('reload/s', "1")

        if get.address == "":
             return public.return_message(-1, 0, public.lang("The destination IP cannot be empty"))

        # 2024/3/25 下午 8:23 处理多个ip的情况,例如出现每行一个ip
        if get.address != "all" and "\n" in get.address:
            return self.set_nline_ip_rule(get)
        elif get.address != "all" and "-" in get.address:
            return self.set_range_ip_rule(get)
        elif get.address != "all" and "/" in get.address:
            return self.set_mask_ip_rule(get)
        elif get.address != "all" and "," in get.address:
            return self.set_tline_ip_rule(get)
        elif get.address != "all" and not public.checkIp(get.address) and not public.is_ipv6(get.address):
             return public.return_message(-1, 0, public.lang("The destination address is in the wrong format"))
        else:
            if get.operation == "add" and get.strategy == "drop":
                if self.check_is_user_ip(get):
                     return public.return_message(-1, 0, public.lang("You can't add your own IP"))

            if get.operation == "add" and not self.check_ip_exist(get):
                 return public.return_message(-1, 0, public.lang("The destination address {} already exists, please do not add it repeatedly", get.address))

            self.set_ip_db(get)

            info = {
                "Address": get.address,
                "Family": get.family,
                "Strategy": get.strategy.lower(),
                "Priority": get.priority.lower(),
            }

            if get.chain == "INPUT":
                result = self.firewall.rich_rules(info=info, operation=get.operation)
            else:
                result = self.firewall.output_rich_rules(info=info, operation=get.operation)

            if result['status'] and self._isFirewalld and get.reload == "1":
                self.firewall.reload()

            return public.return_message(0, 0,result['msg'])
            # return result

    # 2024/3/27 上午 9:44 修改ip规则
    def modify_ip_rule(self, get):
        '''
            @name 修改ip规则
            @param "data":{"参数名":""} <数据类型> 参数描述
            @return dict{"status":True/False,"msg":"提示信息"}
        '''
        # 2024/4/17 下午4:47 检查防火墙状态，如果未启动则不允许设置设置规则
        if not self.get_firewall_status():
             return public.return_message(-1, 0, public.lang("Please activate the firewall before setting up the rules!"))
        get.old_data = get.get('old_data/s', '')
        get.new_data = get.get('new_data/s', '')

        if get.old_data == "":
             return public.return_message(-1, 0, public.lang("Please pass in old_data"))

        if get.new_data == "":
             return public.return_message(-1, 0, public.lang("Please pass in new_data"))

        get.old_data = json.loads(get.old_data)
        get.new_data = json.loads(get.new_data)

        args1 = public.dict_obj()
        args1.operation = 'remove'
        args1.address = get.old_data['Address']
        args1.strategy = get.old_data['Strategy']
        args1.family = get.old_data['Family']
        args1.chain = get.old_data['Chain']
        args1.id = get.old_data['id']
        args1.sid = get.old_data['sid']
        args1.reload = "0"
        self.set_ip_rule(args1)

        args2 = public.dict_obj()
        args2.operation = 'add'
        args2.address = get.new_data['address']
        args2.strategy = get.new_data['strategy']
        args2.family = get.new_data['family']
        args2.chain = get.new_data['chain']
        args2.brief = get.new_data['brief']
        args2.reload = "0"
        self.set_ip_rule(args2)

        if self._isFirewalld:
            self.firewall.reload()

        return public.return_message(0, 0, public.lang("The modification was successful"))

    # 2024/3/26 下午 5:18 设置域名ip规则
    def set_domain_ip_rule(self, get):
        '''
            @name 设置域名ip规则
            @author wzz <2024/3/26 下午 5:19>
            @param "data":{"参数名":""} <数据类型> 参数描述
            @return dict{"status":True/False,"msg":"提示信息"}
        '''
        get.operation = get.get('operation/s', 'add')
        get.protocol = get.get('protocol/s', 'tcp')
        get.domain = get.get('domain/s', '')
        get.port = get.get('port/s', '')
        get.strategy = get.get('strategy/s', 'accept')
        get.chain = get.get('chain/s', 'INPUT')

        if get.domain == "":
             return public.return_message(-1, 0, public.lang("The destination domain name cannot be empty"))

        if get.port == "":
             return public.return_message(-1, 0, public.lang("The destination port cannot be empty"))

        if not public.is_domain(get.domain):
             return public.return_message(-1, 0, public.lang("The destination domain name is in the wrong format"))

        address = self.get_a_ip(get.domain)

        if address == "":
             return public.return_message(-1, 0, public.lang("Domain name: 【{}】Resolution failed", get.domain))

        if not public.checkIp(get.address):
             return public.return_message(-1, 0, public.lang("The destination address is in the wrong format"))

        info = {
            "Address": address,
            "Family": get.family,
            "Strategy": get.strategy.lower(),
            "Priority": get.priority.lower(),
        }
        if get.chain == "INPUT":
            result = self.firewall.rich_rules(info=info, operation=get.operation)
        else:
            result = self.firewall.output_rich_rules(info=info, operation=get.operation)

        if result['status'] and self._isFirewalld:
            self.firewall.reload()

        # return result
        return public.return_message(0, 0, result['msg'])

    # 2024/3/25 上午 11:18 获取所有ip规则列表
    def ip_rules_list(self, get):
        '''
            @name 获取所有ip规则列表
            @param "data":{"参数名":""} <数据类型> 参数描述
            @return list[dict{}...]
        '''
        get.chain = get.get('chain/s', 'all')
        get.query = get.get('query/s', '')
        ip_db = self.get_ip_db(get)

        if get.chain == "INPUT":
            list_address = self.firewall.list_input_address()
        elif get.chain == "OUTPUT":
            list_address = self.firewall.list_output_address()
        else:
            list_address = self.firewall.list_address()

        return public.return_message(0, 0, self.structure_ip_return_data(list_address, ip_db, query=get.query))

    def _ip_rules_list(self, get):
        '''
            @name 获取所有ip规则列表
            @param "data":{"参数名":""} <数据类型> 参数描述
            @return list[dict{}...]
        '''
        get.chain = get.get('chain/s', 'all')
        get.query = get.get('query/s', '')
        ip_db = self.get_ip_db(get)

        if get.chain == "INPUT":
            list_address = self.firewall.list_input_address()
        elif get.chain == "OUTPUT":
            list_address = self.firewall.list_output_address()
        else:
            list_address = self.firewall.list_address()

        return self.structure_ip_return_data(list_address, ip_db, query=get.query)
    # 2024/3/26 下午 3:03 导出所有ip规则
    def export_ip_rules(self, get):
        '''
            @name 导出所有ip规则
            @param "data":{"参数名":""} <数据类型> 参数描述
            @return dict{"status":True/False,"msg":"提示信息"}
        '''
        get.chain = get.get('chain/s', 'all')

        if get.chain == "INPUT":
            file_name = "input_ip_rules_{}".format(int(time.time()))
        elif get.chain == "OUTPUT":
            file_name = "output_ip_rules_{}".format(int(time.time()))
        else:
            file_name = "ip_rules_{}".format(int(time.time()))

        data = self._ip_rules_list(get)
        if not data:
             return public.return_message(-1, 0, public.lang("No rules can be exported"))
        if not os.path.exists(self.config_path):
            os.makedirs(self.config_path, exist_ok=True)
        file_path = "{}/{}.json".format(self.config_path, file_name)

        public.writeFile(file_path, public.GetJson(data))
        public.WriteLog("system firewall", "Export IP rules")
        return public.return_message(0, 0,  file_path)

    # 2024/3/26 下午 3:05 导入ip规则
    def import_ip_rules(self, get):
        '''
            @name 导入ip规则
            @param "data":{"参数名":""} <数据类型> 参数描述
            @return dict{"status":True/False,"msg":"提示信息"}
        '''
        get.file = get.get('file/s', '')

        if not get.file:
             return public.return_message(-1, 0, public.lang("The file cannot be empty"))

        if not os.path.exists(get.file):
             return public.return_message(-1, 0, public.lang("The file does not exist"))

        try:
            data = public.readFile(get.file)
            if "|" in data and not "{" in data:
                get.rule_name = "ip_rule"
                return self.import_rules_old(get)

            data = json.loads(data)
            # 2024/4/10 下午2:51 反转数据
            data.reverse()
        except:
             return public.return_message(-1, 0, public.lang("The file content is abnormal or malformed"))

        args = public.dict_obj()
        for item in data:
            args.operation = 'add'
            args.address = item['Address']
            args.strategy = item['Strategy']
            args.chain = item['Chain']
            args.family = item['Family']
            args.brief = item['brief']
            args.reload = "0"

            self.set_ip_rule(args)

        if self._isFirewalld:
            self.firewall.reload()

        return public.return_message(0, 0, public.lang("The import was successful"))

    # 2024/3/25 下午 2:34 获取端口转发列表
    def port_forward_list(self, get):
        '''
            @name 获取端口转发列表
            @param "data":{"参数名":""} <数据类型> 参数描述
            @return list[dict{}...]
        '''
        get.query = get.get('query/s', '')
        list_port_forward = self.firewall.list_port_forward()
        forward_db = self.get_forward_db(get)
        if type(list_port_forward) == list and type(forward_db) == list:
            return public.return_message(0, 0,self.structure_forward_return_data(list_port_forward, forward_db, query=get.query))
        return public.return_message(0, 0, [])
    def _port_forward_list(self, get):
        '''
            @name 获取端口转发列表
            @param "data":{"参数名":""} <数据类型> 参数描述
            @return list[dict{}...]
        '''
        get.query = get.get('query/s', '')
        list_port_forward = self.firewall.list_port_forward()
        forward_db = self.get_forward_db(get)
        if type(list_port_forward) == list and type(forward_db) == list:
            return self.structure_forward_return_data(list_port_forward, forward_db, query=get.query)
        return []

    # 2024/3/26 下午 3:08 导出所有端口转发规则
    def export_port_forward(self, get):
        '''
            @name 导出所有端口转发规则
            @param "data":{"参数名":""} <数据类型> 参数描述
            @return dict{"status":True/False,"msg":"提示信息"}
        '''
        data = self.firewall.list_port_forward()
        if not data:
             return public.return_message(-1, 0, public.lang("No rules can be exported"))
        file_name = "port_forward_{}".format(int(time.time()))
        if not os.path.exists(self.config_path):
            os.makedirs(self.config_path, exist_ok=True)
        file_path = "{}/{}.json".format(self.config_path, file_name)

        public.writeFile(file_path, public.GetJson(data))
        public.WriteLog("system firewall", "Export port forwarding rules")
        return public.return_message(0, 0,  file_path)

    # 2024/3/26 下午 3:10 导入端口转发规则
    def import_port_forward(self, get):
        '''
            @name 导入端口转发规则
            @param "data":{"参数名":""} <数据类型> 参数描述
            @return dict{"status":True/False,"msg":"提示信息"}
        '''
        get.file = get.get('file/s', '')

        if not get.file:
             return public.return_message(-1, 0, public.lang("The file cannot be empty"))

        if not os.path.exists(get.file):
             return public.return_message(-1, 0, public.lang("The file does not exist"))

        try:
            data = public.readFile(get.file)
            if "|" in data and not "{" in data:
                get.rule_name = "trans_rule"
                return self.import_rules_old(get)

            data = json.loads(data)
            # 2024/4/10 下午2:51 反转数据
            data.reverse()
        except:
             return public.return_message(-1, 0, public.lang("The file content is abnormal or malformed"))

        args = public.dict_obj()
        for item in data:
            args.operation = 'add'
            args.protocol = item['Protocol']
            args.S_Address = item['S_Address']
            args.S_Port = item['S_Port']
            args.T_Address = item['T_Address']
            args.T_Port = item['T_Port']
            args.reload = "0"

            self.set_port_forward(args)

        if self._isFirewalld:
            self.firewall.reload()

        return public.return_message(0, 0, public.lang("The import was successful"))

    # 2024/3/25 下午 3:43 设置端口转发
    def set_port_forward(self, get):
        '''
            @name 设置端口转发
            @param "data":{"参数名":""} <数据类型> 参数描述
            @return dict{"status":True/False,"msg":"提示信息"}
        '''
        # 2024/4/17 下午4:47 检查防火墙状态，如果未启动则不允许设置设置规则
        if not self.get_firewall_status():
             return public.return_message(-1, 0, public.lang("Please activate the firewall before setting up the rules!"))

        get.operation = get.get('operation/s', 'add')
        get.protocol = get.get('protocol/s', 'tcp')
        get.S_Address = get.get('S_Address/s', '')
        get.S_Port = get.get('S_Port/s', '')
        get.T_Address = get.get("T_Address/s", '')
        get.T_Port = get.get("T_Port/s", '')
        get.reload = get.get('reload/s', "1")

        if get.S_Port == "":
             return public.return_message(-1, 0, public.lang("The source port cannot be empty"))
        # if get.T_Address == "":
        #      return public.return_message(-1, 0, public.lang("目标地址不能为空"))
        if get.T_Port == "":
             return public.return_message(-1, 0, public.lang("The destination port cannot be empty"))

        # 2024/3/25 下午 5:49 前置检测
        if get.operation == "add":
            check_ip_forward = self.firewall.check_ip_forward()
            if not check_ip_forward["status"]:
                return public.return_message(-1, 0,  check_ip_forward['msg'])
            if not self.check_forward_exist(get):
                 return public.return_message(-1, 0, public.lang("If the rule already exists, do not add it repeatedly"))

        self.set_forward_db(get)

        # 2024/3/25 下午 5:50 构造传参,调用底层方法设置端口转发
        if get.protocol == "tcp/udp" or get.protocol == "all":
            info = {
                "Family": "ipv4",
                "Protocol": "tcp",
                "S_Address": get.S_Address,
                "S_Port": get.S_Port,
                "T_Address": get.T_Address,
                "T_Port": get.T_Port,
            }
            result = self.firewall.port_forward(info=info, operation=get.operation)
            if not result['status']:
                # return result
                return public.return_message(-1, 0, result['msg'])

            info = {
                "Family": "ipv4",
                "Protocol": "udp",
                "S_Address": get.S_Address,
                "S_Port": get.S_Port,
                "T_Address": get.T_Address,
                "T_Port": get.T_Port,
            }
            result = self.firewall.port_forward(info=info, operation=get.operation)

            if result['status'] and self._isFirewalld and get.reload == "1":
                self.firewall.reload()
        else:
            info = {
                "Family": "ipv4",
                "Protocol": get.protocol,
                "S_Address": get.S_Address,
                "S_Port": get.S_Port,
                "T_Address": get.T_Address,
                "T_Port": get.T_Port,
            }
            result = self.firewall.port_forward(info=info, operation=get.operation)

            # 2024/3/25 下午 5:50 如果The setup was successful才重载防火墙
            if result['status'] and self._isFirewalld and get.reload == "1":
                self.firewall.reload()

        return public.return_message(0, 0, result['msg'])
        # return result

    # 2024/3/27 上午 9:44 修改端口转发规则
    def modify_forward_rule(self, get):
        '''
            @name 修改端口转发规则
            @param "data":{"参数名":""} <数据类型> 参数描述
            @return dict{"status":True/False,"msg":"提示信息"}
        '''
        # 2024/4/17 下午4:47 检查防火墙状态，如果未启动则不允许设置规则
        if not self.get_firewall_status():
             return public.return_message(-1, 0, public.lang("Please activate the firewall before setting up the rules!"))

        get.old_data = get.get('old_data/s', '')
        get.new_data = get.get('new_data/s', '')

        if get.old_data == "":
             return public.return_message(-1, 0, public.lang("Please pass in old_data"))

        if get.new_data == "":
             return public.return_message(-1, 0, public.lang("Please pass in new_data"))

        get.old_data = json.loads(get.old_data)
        get.new_data = json.loads(get.new_data)

        args1 = public.dict_obj()
        args1.operation = 'remove'
        args1.S_Address = get.old_data['S_Address']
        args1.S_Port = get.old_data['S_Port']
        args1.T_Address = get.old_data['T_Address']
        args1.T_Port = get.old_data['T_Port']
        args1.protocol = get.old_data['Protocol']
        args1.id = get.old_data['id']
        args1.reload = "0"
        self.set_port_forward(args1)

        args2 = public.dict_obj()
        args2.operation = 'add'
        # args2.S_Address = get.new_data['S_Address']
        args2.S_Port = get.new_data['S_Port']
        args2.T_Address = get.new_data['T_Address']
        args2.T_Port = get.new_data['T_Port']
        args2.protocol = get.new_data['protocol']
        args2.brief = get.new_data['brief']
        args2.reload = "0"
        self.set_port_forward(args2)

        if self._isFirewalld:
            self.firewall.reload()

        return public.return_message(0, 0, public.lang("The modification was successful"))


    def check_table_firewall_forward(self):
        '''
            @name 检查并创建表
            @return dict{"status":True/False,"msg":"提示信息"}
        '''
        if not public.M('sqlite_master').where('type=? AND name=?', ('table', 'firewall_forward')).count():

            public.M('').execute(
            '''CREATE TABLE "firewall_forward" (`id` INTEGER PRIMARY KEY AUTOINCREMENT, `S_Address` TEXT, `S_Domain` TEXT, `S_Port` TEXT, `T_Address` TEXT, `T_Domain` TEXT, `T_Port` TEXT DEFAULT '', `Protocol` TEXT DEFAULT '', `Family` TEXT DEFAULT '', `addtime` TEXT DEFAULT '', `brief` TEXT DEFAULT '');''')



    # 检查字段是否存在 不存在创建
    def check_table_column(self, ):

        create_table_str = public.M('firewall_new').table('sqlite_master').where(
            'type=? AND name=?', ('table', 'firewall_new')).getField('sql')
        if 'sid' not in create_table_str:
            public.M('firewall_new').execute('ALTER TABLE "firewall_new" ADD "sid"  int DEFAULT 0')
        if 'domain' not in create_table_str:
            public.M('firewall_new').execute('ALTER TABLE "firewall_new" ADD "domain" TEXT DEFAULT ""')
        if 'chain' not in create_table_str:
            public.M('firewall_new').execute('ALTER TABLE "firewall_new" ADD "chain" TEXT DEFAULT ""')

        create_table_str = public.M('firewall_ip').table('sqlite_master').where(
            'type=? AND name=?', ('table', 'firewall_ip')).getField('sql')
        if 'sid' not in create_table_str:
            public.M('firewall_ip').execute('ALTER TABLE "firewall_ip" ADD "sid"  int DEFAULT 0')
        if 'domain' not in create_table_str:
            public.M('firewall_ip').execute('ALTER TABLE "firewall_ip" ADD "domain" TEXT DEFAULT ""')
        if 'chain' not in create_table_str:
            public.M('firewall_ip').execute('ALTER TABLE "firewall_ip" ADD "chain" TEXT DEFAULT ""')
