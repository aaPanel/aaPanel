# coding: utf-8
import json
import os
import pwd
import re
from typing import Union, Optional, Tuple, List

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


class _ProjectSiteType:
    _CONFIG_FILE = "{}/config/project_site.json".format(public.get_panel_path())
    allow_type = {"go", "java", "net", "nodejs", "other", "python", "proxy", "html"}

    def __init__(self):
        self._config = None

    @classmethod
    def read_conf_file(cls):
        default_conf = {
            "go": {},
            "java": {},
            "net": {},
            "nodejs": {},
            "other": {},
            "python": {},
            "proxy": {},
            "html": {},
        }

        if not os.path.isfile(cls._CONFIG_FILE):
            public.writeFile(cls._CONFIG_FILE, json.dumps(default_conf))
            return default_conf

        conf_data = public.readFile(cls._CONFIG_FILE)
        if not isinstance(conf_data, str):
            public.writeFile(cls._CONFIG_FILE, json.dumps(default_conf))
            return default_conf

        try:
            conf = json.loads(conf_data)
        except json.JSONDecodeError:
            conf = None
        if not isinstance(conf, dict):
            public.writeFile(cls._CONFIG_FILE, json.dumps(default_conf))
            return default_conf
        return conf

    @property
    def config(self):
        if self._config is not None:
            return self._config
        self._config = self.read_conf_file()
        return self._config

    def save_config_to_file(self):
        if self._config:
            public.writeFile(self._CONFIG_FILE, json.dumps(self._config))

    def get_next_id(self, p_type: str) -> int:
        all_ids = [
            i["id"] for i in self.config[p_type].values()
        ]
        return max(all_ids + [0]) + 1

    def add(self, p_type: str, name: str, ps: str) -> Tuple[bool, str]:
        if p_type not in self.allow_type:
            return False, "not support type"

        if p_type not in self.config:
            self.config[p_type] = {}

        for t_info in self.config[p_type].values():
            if t_info["name"] == name:
                return False, "name exists"

        next_id = self.get_next_id(p_type)
        self.config[p_type][str(next_id)] = {
            "id": next_id,
            "name": name,
            "ps": ps
        }
        self.save_config_to_file()
        return True, ""

    def modify(self, p_type: str, t_id: int, name: str, ps: str) -> bool:
        if p_type not in self.config:
            return False

        if str(t_id) not in self.config[p_type]:
            return False

        self.config[p_type][str(t_id)] = {
            "id": t_id,
            "name": name,
            "ps": ps
        }
        self.save_config_to_file()
        return True

    def remove(self, p_type: str, t_id: int) -> bool:
        if p_type not in self.config:
            return False

        if str(t_id) not in self.config[p_type]:
            return False

        del self.config[p_type][str(t_id)]

        self.save_config_to_file()
        return True

    def find(self, p_type: str, t_id: int) -> Optional[dict]:
        if p_type not in self.config:
            return None

        if str(t_id) not in self.config[p_type]:
            return None

        return self.config[p_type][str(t_id)]

    def list_by_type(self, p_type: str) -> List[dict]:
        if p_type not in self.config:
            return []
        return [
            i for i in self.config[p_type].values()
        ]


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
        setup_path = public.get_setup_path()
        ng_path = setup_path + '/nginx/sbin/nginx'
        ap_path = setup_path + '/apache/bin/apachectl'
        op_path = '/usr/local/lsws/bin/lswsctrl'
        if not os.path.exists(ng_path) and not os.path.exists(ap_path) and not os.path.exists(op_path):
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

        if getattr(get, "release_firewall", None) in ("0", '', None, False, 0):
            return False, public.lang("PS: port not released in firewall, local access only")

        port = getattr(get, "port", None)
        if port is None:
            return True, ""
        project_name = getattr(get, "name", "") or getattr(get, "pjname", "") or getattr(get, "project_name", "")
        brief = f"Site Project: {public.xsssec(project_name)} release port "
        fw_body = {
            "protocol": "tcp",
            "port": str(port),
            "choose": "all",
            "domain": "",
            "types": "accept",
            "strategy": "accept",
            "chain": "INPUT",
            "brief": brief,
            "operation": "add",
        }
        try:
            from firewallModelV2.comModel import main as firewall
            try:
                ports_exist = firewall().port_rules_list(public.to_dict_obj({
                    "chain": "ALL",
                    "query": brief,
                }))
                # 尝试移除被该项目占用的旧端口
                for old_port in public.find_value_by_key(ports_exist, "data", []):
                    old_port_str = str(old_port.get("Port", ""))
                    if not old_port_str:
                        continue
                    if old_port_str == "80":
                        continue
                    if self.IsOpen(old_port):
                        continue
                    if old_port.get("Port"):
                        fw_body["port"] = str(old_port.get("Port", ""))
                        fw_body["operation"] = "remove"
                        firewall().set_port_rule(public.to_dict_obj(fw_body))
            except:
                pass
            # add
            fw_body["port"] = str(port)
            set_res = firewall().set_port_rule(public.to_dict_obj(fw_body))
            if set_res.get("status") == 0:
                return True, ""
        except Exception as e:
            import traceback
            public.print_log(traceback.format_exc())
            public.print_log("_release_firewall error: {}".format(e))
        return False, public.lang("PS: port not released in firewall, local access only")

    # todo 废弃
    def set_daemon_time(self):
        """设置守护进程重启检测时间"""
        pass

    # todo 废弃
    def get_daemon_time(self):
        """获取守护进程重启检测时间"""
        pass

    # todo 废弃
    def _project_mod_type(self) -> Optional[str]:
        mod_name = self.__class__.__module__

        # "projectModel/javaModel.py" 的格式
        if "/" in mod_name:
            mod_name = mod_name.rsplit("/", 1)[1]
        if mod_name.endswith(".py"):
            mod_name = mod_name[:-3]

        # "projectModel.javaModel" 的格式
        if "." in mod_name:
            mod_name = mod_name.rsplit(".", 1)[1]

        if mod_name.endswith("Model"):
            return mod_name[:-5]
        return mod_name

    # todo移除到site通用
    def project_site_types(self, get=None):
        p_type = self._project_mod_type()
        res = _ProjectSiteType().list_by_type(p_type)
        res_data = [
                       {"id": 0, "name": "Default category", "ps": ""},
                   ] + res
        return public.success_v2(res_data)

    # todo移除到site通用
    def add_project_site_type(self, get):
        try:
            type_name = get.type_name.strip()
            ps = get.ps.strip()
        except AttributeError:
            return public.fail_v2("params error")
        if not type_name:
            return public.fail_v2("name can not be empty")
        if len(type_name) > 16:
            return public.fail_v2("please do not enter more than 16 characters for the name")

        p_type = self._project_mod_type()

        flag, msg = _ProjectSiteType().add(p_type, type_name, ps)
        if not flag:
            return public.fail_v2(msg)
        return public.success_v2("Add success")

    # todo移除到site通用
    def modify_project_site_type(self, get):
        try:
            type_name = get.type_name.strip()
            ps = get.ps.strip()
            type_id = int(get.type_id.strip())
        except (AttributeError, ValueError, TypeError):
            return public.fail_v2("params error")
        if not type_name or not type_id:
            return public.fail_v2("type_name, type_id can not be empty")
        if len(type_name) > 16:
            return public.fail_v2("please do not enter more than 16 characters for the name")

        p_type = self._project_mod_type()
        flag = _ProjectSiteType().modify(p_type, type_id, type_name, ps)
        if not flag:
            return public.fail_v2("modify error")
        return public.success_v2("Modify success")

    # todo移除到site通用
    def remove_project_site_type(self, get):
        try:
            type_id = int(get.type_id.strip())
        except (AttributeError, ValueError, TypeError):
            return public.fail_v2("params error")

        p_type = self._project_mod_type()
        project_type_map = {
            "go": "Go",
            "java": "Java",
            "net": "net",
            "nodejs": "Node",
            "other": "Other",
            "python": "Python",
            "proxy": "proxy",
            "html": "html",
        }
        if p_type not in project_type_map:
            return public.fail_v2("params error")

        flag = _ProjectSiteType().remove(p_type, type_id)
        if not flag:
            return public.fail_v2("Delete error")

        p_t = project_type_map[p_type]
        query_str = 'project_type=? AND type_id=?'
        projects = public.M('sites').where(query_str, (p_t, type_id)).field("id").select()
        if not projects:
            return public.success_v2("Delete success")

        project_ids = [i["id"] for i in projects]
        update_str = 'project_type=? AND id in ({})'.format(",".join(["?"] * len(project_ids)))
        public.M('sites').where(update_str, (p_t, *project_ids)).update({"type_id": 0})

        return public.success_v2("Delete success")

    # todo移除到site通用
    def find_project_site_type(self, type_id: int):
        if isinstance(type_id, str):
            try:
                type_id = int(type_id)
            except (AttributeError, ValueError, TypeError):
                return None
        if type_id == 0:
            return {
                "id": 0,
                "name": "Default category",
                "ps": ""
            }
        p_type = self._project_mod_type()
        return _ProjectSiteType().find(p_type, type_id)

    # todo移除, 使用batch
    def set_project_site_type(self, get):
        try:
            type_id = int(get.type_id.strip())
            if isinstance(get.site_ids, str):
                site_ids = json.loads(get.site_ids.strip())
            else:
                site_ids = get.site_ids
        except (AttributeError, ValueError, TypeError):
            return public.fail_v2("params error")

        if not isinstance(site_ids, list):
            return public.fail_v2("params error")

        p_type = self._project_mod_type()
        project_type_map = {
            "go": "Go",
            "java": "Java",
            "net": "net",
            "nodejs": "Node",
            "other": "Other",
            "python": "Python",
            "proxy": "proxy",
            "html": "html",
        }
        if p_type not in project_type_map:
            return public.fail_v2("params error")

        if not self.find_project_site_type(type_id):
            return public.fail_v2("project site type not exists")

        p_t = project_type_map[p_type]
        query_str = 'project_type=? AND id in ({})'.format(",".join(["?"] * len(site_ids)))
        projects = public.M('sites').where(query_str, (p_t, *site_ids)).field("id").select()
        if not projects:
            return public.fail_v2("no project found")

        project_ids = [i["id"] for i in projects]

        update_str = 'project_type=? AND id in ({})'.format(",".join(["?"] * len(project_ids)))
        public.M('sites').where(update_str, (p_t, *project_ids)).update({"type_id": type_id})
        return public.success_v2("Set success")

    # todo移除废弃
    def batch_set_site_type(self, get):
        """
            @name 批量设置网站分类
        """
        # v2 site api -> batch_set_site_type
        pass
