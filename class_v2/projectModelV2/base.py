# coding: utf-8
import json
import os
import pwd
import re
from typing import Union

import public
public.sys_path_append("class_v2")
from projectModelV2.common import LimitNet, Redirect
from public.exceptions import HintException

try:
    from public.hook_import import hook_import

    hook_import()
except:
    pass
try:
    import idna
except:
    public.ExecShell('btpip install idna')
    import idna


class projectBase(LimitNet, Redirect):
    def __init__(self):
        self._is_nginx_http3 = None

    def check_port(self, port):
        '''
        @name 检查端口是否被占用
        @args port:端口号
        @return: 被占用返回True，否则返回False
        @author: lkq 2021-08-28
        '''
        a = public.ExecShell("netstat -nltp|awk '{print $4}'")
        if a[0]:
            if re.search(':' + port + '\n', a[0]):
                return True
            else:
                return False
        else:
            return False

    def is_domain(self, domain):
        '''
        @name 验证域名合法性
        @args domain:域名
        @return: 合法返回True，否则返回False
        @author: lkq 2021-08-28
        '''
        import re
        domain_regex = re.compile(r'(?:[A-Z0-9_](?:[A-Z0-9-_]{0,247}[A-Z0-9])?\.)+(?:[A-Z]{2,6}|[A-Z0-9-]{2,}(?<!-))\Z',
                                  re.IGNORECASE)
        return True if domain_regex.match(domain) else False

    def generate_random_port(self):
        '''
        @name 生成随机端口
        @args
        @return: 端口号
        @author: lkq 2021-08-28
        '''
        import random
        port = str(random.randint(5000, 10000))
        while True:
            if not self.check_port(port): break
            port = str(random.randint(5000, 10000))
        return port

    def IsOpen(self, port):
        '''
        @name 检查端口是否被占用
        @args port:端口号
        @return: 被占用返回True，否则返回False
        @author: lkq 2021-08-28
        '''
        ip = '0.0.0.0'
        import socket
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            s.connect((ip, int(port)))
            s.shutdown(2)
            return True
        except:
            return False

    @staticmethod
    def get_system_user_list(get=None):
        """
        默认只返回uid>= 1000 的用户 和 root
        get中包含 sys_user 返回 uid>= 100 的用户 和 root
        get中包含 all_user 返回所有的用户
        """
        sys_user = False
        all_user = False
        if get is not None:
            if hasattr(get, "sys_user"):
                sys_user = True
            if hasattr(get, "all_user"):
                all_user = True

        user_set = set()
        try:
            for tmp_uer in pwd.getpwall():
                if tmp_uer.pw_uid == 0:
                    user_set.add(tmp_uer.pw_name)
                elif tmp_uer.pw_uid >= 1000:
                    user_set.add(tmp_uer.pw_name)
                elif sys_user and tmp_uer.pw_uid >= 100:
                    user_set.add(tmp_uer.pw_name)
                elif all_user:
                    user_set.add(tmp_uer.pw_name)
        except Exception:
            pass
        return list(user_set)

    @staticmethod
    def _pass_dir_for_user(path_dir: str, user: str):
        """
        给某个用户，对应目录的执行权限
        """
        import stat
        if not os.path.isdir(path_dir):
            return
        try:
            import pwd
            uid_data = pwd.getpwnam(user)
            uid = uid_data.pw_uid
            gid = uid_data.pw_gid
        except:
            return

        if uid == 0:
            return

        if path_dir[:-1] == "/":
            path_dir = path_dir[:-1]

        while path_dir != "/":
            path_dir_stat = os.stat(path_dir)
            if path_dir_stat.st_uid != uid or path_dir_stat.st_gid != gid:
                old_mod = stat.S_IMODE(path_dir_stat.st_mode)
                if not old_mod & 1:
                    os.chmod(path_dir, old_mod + 1)
            path_dir = os.path.dirname(path_dir)

    @staticmethod
    def start_by_user(project_id):
        file_path = "{}/data/push/tips/project_stop.json".format(public.get_panel_path())
        if not os.path.exists(file_path):
            data = {}
        else:
            data_content = public.readFile(file_path)
            try:
                data = json.loads(data_content)
            except json.JSONDecodeError:
                data = {}
        data[str(project_id)] = False
        public.writeFile(file_path, json.dumps(data))

    @staticmethod
    def stop_by_user(project_id):
        file_path = "{}/data/push/tips/project_stop.json".format(public.get_panel_path())
        if not os.path.exists(file_path):
            data = {}
        else:
            data_content = public.readFile(file_path)
            try:
                data = json.loads(data_content)
            except json.JSONDecodeError:
                data = {}
        data[str(project_id)] = True
        public.writeFile(file_path, json.dumps(data))

    @staticmethod
    def is_stop_by_user(project_id):
        file_path = "{}/data/push/tips/project_stop.json".format(public.get_panel_path())
        if not os.path.exists(file_path):
            data = {}
        else:
            data_content = public.readFile(file_path)
            try:
                data = json.loads(data_content)
            except json.JSONDecodeError:
                data = {}
        if str(project_id) not in data:
            return False
        return data[str(project_id)]

    def is_nginx_http3(self):
        """判断nginx是否可以使用http3"""
        if getattr(self, "_is_nginx_http3", None) is None:
            _is_nginx_http3 = public.ExecShell("nginx -V 2>&1| grep 'http_v3_module'")[0] != ''
            setattr(self, "_is_nginx_http3", _is_nginx_http3)
        return self._is_nginx_http3

    @staticmethod
    def _check_webserver():
        setup_path = public.GetConfigValue('setup_path')
        ng_path = setup_path + '/nginx/sbin/nginx'
        ap_path = setup_path + '/apache/bin/apachectl'
        op_path = '/usr/local/lsws/bin/lswsctrl'
        not_server = False
        if not os.path.exists(ng_path) and not os.path.exists(ap_path) and not os.path.exists(op_path):
            not_server = True
        if not not_server:
            raise HintException(public.lang("Not Found any Web Server"))

        tasks = public.M('tasks').where("status!=? AND type!=?", ('1', 'download')).field('id,name').select()
        for task in tasks:
            name = task["name"].lower()
            if name.find("openlitespeed") != -1:
                raise HintException(public.lang("Installing OpenLiteSpeed, please wait"))
            if name.find("nginx") != -1:
                raise HintException(public.lang("Installing Nginx, please wait"))
            if name.lower().find("apache") != -1:
                raise HintException(public.lang("Installing Apache, please wait"))

    # 域名编码转换
    @staticmethod
    def domain_to_puny_code(domain):
        match = re.search(u"[^u\0000-u\001f]+", domain)
        if not match:
            return domain
        try:
            if domain.startswith("*."):
                return "*." + idna.encode(domain[2:]).decode("utf8")
            else:
                return idna.encode(domain).decode("utf8")
        except:
            return domain

    # 判断域名是否有效，并返回
    def check_domain(self, domain: str) -> Union[str, bool]:
        domain = self.domain_to_puny_code(domain)
        # 判断通配符域名格式
        if domain.find('*') != -1 and domain.find('*.') == -1:
            return False
        from ssl_domainModelV2.service import DomainValid
        if not DomainValid.is_valid_domain(domain):
            return False
        return domain

    def _release_firewall(self, get) -> tuple[bool, str]:
        """尝试放行端口
        @author baozi <202-04-18>
        @param:
            get  ( dict_obj ):  创建项目的请求
        @return
        """

        release = getattr(get, "release_firewall", None)
        if release in ("0", '', None, False, 0):
            return False, public.lang("PS: port not released in firewall, local access only")
        port = getattr(get, "port", None)
        project_name = getattr(get, "name", "") or getattr(get, "pjname", "") or getattr(get, "project_name", "")
        if port is None:
            return True, ""

        new_get = public.dict_obj()
        new_get.protocol = "tcp"
        new_get.ports = str(port)
        new_get.choose = "all"
        new_get.address = ""
        new_get.domain = ""
        new_get.types = "accept"
        new_get.brief = "Site Project: " + project_name + " release port "
        new_get.source = ""
        try:
            res = None
            from safeModelV2.firewallModel import main as firewall
            firewall_obj = firewall()
            get_obj = public.dict_obj()
            get_obj.p = 1
            get_obj.limit = 99
            get_obj.query = str(port)
            res_data = firewall_obj.get_rules_list(get_obj)  # 查询是否已经有端口
            res_data = public.find_value_by_key(res_data, key="data", default=[])
            if len(res_data) == 0:
                res = firewall_obj.create_rules(new_get)
            for i in res_data:
                new_get.id = i.get("id")
                res = firewall_obj.modify_rules(new_get)

            if res.get("status"):
                return True, ""
            return False, public.lang("PS: port not released in firewall, local access only")
        except:
            return False, public.lang("PS: port not released in firewall, local access only")

