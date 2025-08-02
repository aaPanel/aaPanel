# coding: utf-8
# -------------------------------------------------------------------
# aapanel
# -------------------------------------------------------------------
# Copyright (c) 2015-2099 aapanel(http://www.aapanel.com) All rights reserved.
# -------------------------------------------------------------------

import json
import os
import sys
import time
import warnings
from typing import Dict, Any

if "/www/server/panel/class" not in sys.path:
    sys.path.insert(0, "/www/server/panel/class")
if "/www/server/panel/class_v2" not in sys.path:
    sys.path.insert(0, "/www/server/panel/class_v2")
if "/www/server/panel" not in sys.path:
    sys.path.insert(0, "/www/server/panel")

import public
from public.exceptions import HintException
import db_mysql
from mod.project.backup_restore.modules.soft_module import SoftModule

warnings.filterwarnings("ignore", category=SyntaxWarning)


class DataManager(SoftModule):
    def __init__(self):
        super().__init__()
        self._init_db_connections()

    def _init_db_connections(self):
        """初始化数据库连接"""
        self.mysql_obj = db_mysql.panelMysql()

    def _get_current_site_name_by_pid(self, pid: int) -> str:
        p_site = public.M('sites').where('id=?', (pid,)).field('id,name').find()
        if p_site and not isinstance(p_site, str):
            return p_site.get('name', '')
        return ''

    def _get_current_pid_by_site_name(self, site_name: str) -> int:
        if not site_name:
            return 0
        pid = 0
        p_site = public.M('sites').where('name=?', (site_name,)).field('id').find()
        if p_site and not isinstance(p_site, str):
            pid = p_site.get('id', 0)
        return pid

    def get_data_list(self) -> dict:
        """获取所有数据列表"""

        def total_size(target: list | dict, keyword: str) -> int:
            if isinstance(target, list):
                res = 0
                for t in target:
                    if not (isinstance(t, dict) and keyword in t):
                        continue
                    try:
                        res += int(t[keyword])
                    except:
                        continue
                return res
            elif isinstance(target, dict) and keyword in target:
                try:
                    return int(target[keyword])
                except:
                    return 0
            return 0

        # 先获取所有数据列表
        soft_data = self.get_soft_list()
        site_list = self.get_site_list()
        wp_list = self.get_wp_tools_list()
        database_list = self.get_database_list()
        ssh_info = self.get_ssh_dict()
        plugin_list = self.get_plugin_list()
        vmail_info = self.get_vmail_info()

        # 计算所有数据的总大小
        data_sources = [
            (site_list, "size"),  # 累加网站大小
            (wp_list, "size"),  # 累加WP工具大小
            (database_list, "size"),  # 累加数据库大小
            (ssh_info, "ssh_size"),  # 累加SSH大小
            (ssh_info, "command_size"),  # 累加commnd大小
            (vmail_info, "size"),  # 累加mail大小
            (plugin_list, "size"),  # 累加插件大小
        ]
        disk_use = sum(
            map(lambda x: total_size(x[0], x[1]), data_sources)
        )

        # 返回所有数据
        return {
            "disk_free": self.get_free_space()['free_space'],
            "disk_use": disk_use,
            "oss_list": self.get_oss_list(),
            "soft_data": soft_data,
            "site_list": site_list,
            "wp_list": wp_list,
            "ssl_info": {
                "ssl_list": self.get_domian_ssl_list(),
                "provider_list": self.get_domian_provider_list(),
            },
            "database_list": database_list,
            "ftp_list": self.get_ftp_list(),
            "ssh_info": ssh_info,
            "crontab_list": self.get_crontab_list(),
            "firewall_info": self.get_firewall_list(),
            "plugin_list": plugin_list,
            "vmail_info": vmail_info
        }

    def get_oss_list(self):
        data = []
        configured = []
        not_configured = []
        tmp = public.readFile('data/libList.conf')
        if not tmp:
            return data
        try:
            libs = json.loads(tmp)
        except:
            public.print_log("Failed to read libList.conf file, probably because the file format is incorrect")
            libs = []

        for lib in libs:
            if not 'opt' in lib:
                continue
            filename = 'plugin/{}'.format(lib['opt'])
            if not os.path.exists(filename):
                continue
            else:
                plugin_path = '/www/server/panel/plugin/{}/aes_status'.format(lib['opt'])
                status = 0  # 默认值为0，表示未配置
                if os.path.exists(plugin_path):
                    with open(plugin_path, 'r') as f:
                        status_content = f.read().strip()
                        if status_content.lower() == 'true':
                            status = 1  # 如果 aes_status 文件内容为 'True' 则设置为1
                # todo 所有oss插件认证后aes_status=1
                # aws3
                elif public.readFile('/www/server/panel/plugin/{}/config.conf'.format(lib['opt'])):
                    status = 1
                # ftp, 未实现断点续传
                elif public.readFile("/www/server/panel/plugin/{}/ftp.config.conf".format(lib['opt'])):
                    status = 1
                if lib['opt'] == "msonedrive":
                    status = 1
            tmp = {
                'name': lib['name'],
                'value': lib['opt'],
                'status': status,
            }
            if status == 1:
                configured.append(tmp)
            # else:
            #     not_configured.append(tmp)
        # 未配置的暂时不显示
        # 先添加已配置的，再添加未配置的
        data.extend(configured)
        # data.extend(not_configured)
        return data

    def get_soft_list(self):
        soft_data = self.get_soft_data()
        simplified_soft_list = []

        # 处理Web服务器
        if 'web_server' in soft_data and soft_data['web_server']:
            simplified_soft_list.append({
                'name': soft_data['web_server'].get('name', ''),
                'version': soft_data['web_server'].get('version', ''),
                'size': soft_data['web_server'].get('size', 0)
            })

        # 处理PHP版本
        if 'php_server' in soft_data and soft_data['php_server']:
            for php in soft_data['php_server']:
                simplified_soft_list.append({
                    'name': php.get('name', ''),
                    'version': php.get('version', ''),
                    'size': php.get('size', 0)
                })

        # 处理MySQL服务器
        if 'mysql_server' in soft_data and soft_data['mysql_server']:
            simplified_soft_list.append({
                'name': soft_data['mysql_server'].get('type', 'mysql'),
                'version': soft_data['mysql_server'].get('version', ''),
                'size': soft_data['mysql_server'].get('size', 0)
            })

        # 处理FTP服务器
        if 'ftp_server' in soft_data and soft_data['ftp_server']:
            simplified_soft_list.append({
                'name': soft_data['ftp_server'].get('name', 'ftp'),
                'version': soft_data['ftp_server'].get('version', '1.0.47'),
                'size': soft_data['ftp_server'].get('size', 0)
            })

        # 处理JDK列表
        if 'jdk_list' in soft_data and soft_data['jdk_list']:
            for jdk in soft_data['jdk_list']:
                if isinstance(jdk, dict):
                    simplified_soft_list.append({
                        'name': jdk.get('name', 'jdk'),
                        'version': jdk.get('version', ''),
                        'size': jdk.get('size', 0)
                    })
                else:
                    simplified_soft_list.append({
                        'name': 'jdk',
                        'version': jdk,
                        'size': 0
                    })

        # 处理Node.js列表
        if 'node_list' in soft_data and soft_data['node_list']:
            for node in soft_data['node_list']:
                simplified_soft_list.append({
                    'name': node.get('name', ''),
                    'version': node.get('version', ''),
                    'size': node.get('size', 0)
                })

        # 处理Golang
        if 'golang_list' in soft_data and soft_data['golang_list']:
            for golang in soft_data['golang_list'] or []:
                if isinstance(golang, dict):
                    simplified_soft_list.append({
                        'name': golang.get('name', 'golang'),
                        'version': golang.get('version', ''),
                        'size': golang.get('size', 0)
                    })
                else:
                    simplified_soft_list.append({
                        'name': 'golang',
                        'version': golang,
                        'size': 0
                    })

        # 处理Tomcat
        if 'tomcat_list' in soft_data and soft_data['tomcat_list']:
            for tomcat in soft_data['tomcat_list'] or []:
                if isinstance(tomcat, dict):
                    simplified_soft_list.append({
                        'name': tomcat.get('name', 'tomcat'),
                        'version': tomcat.get('version', ''),
                        'size': tomcat.get('size', 0)
                    })
                else:
                    simplified_soft_list.append({
                        'name': 'tomcat',
                        'version': tomcat,
                        'size': 0
                    })

        # 处理Redis服务器
        if 'redis_server' in soft_data and soft_data['redis_server']:
            if isinstance(soft_data['redis_server'], dict):
                simplified_soft_list.append({
                    'name': soft_data['redis_server'].get('name', 'redis'),
                    'version': soft_data['redis_server'].get('version', ''),
                    'size': soft_data['redis_server'].get('size', 0)
                })
            else:
                simplified_soft_list.append({
                    'name': 'redis',
                    'version': soft_data['redis_server'],
                    'size': 0
                })

        # 处理Memcached服务器
        if 'memcached_server' in soft_data and soft_data['memcached_server']:
            if isinstance(soft_data['memcached_server'], dict):
                simplified_soft_list.append({
                    'name': soft_data['memcached_server'].get('name', 'memcached'),
                    'version': soft_data['memcached_server'].get('version', '1.6.12'),
                    'size': soft_data['memcached_server'].get('size', 0)
                })
            else:
                simplified_soft_list.append({
                    'name': 'memcached',
                    'version': '1.16' if not isinstance(soft_data['memcached_server'], str) else soft_data[
                        'memcached_server'],
                    'size': 0
                })

        # 处理MongoDB服务器
        if 'mongodb_server' in soft_data and soft_data['mongodb_server']:
            if isinstance(soft_data['mongodb_server'], dict):
                simplified_soft_list.append({
                    'name': soft_data['mongodb_server'].get('name', 'mongodb'),
                    'version': soft_data['mongodb_server'].get('version', ''),
                    'size': soft_data['mongodb_server'].get('size', 0)
                })
            else:
                simplified_soft_list.append({
                    'name': 'mongodb',
                    'version': soft_data['mongodb_server'],
                    'size': 0
                })

        # 处理PostgreSQL服务器
        if 'pgsql_server' in soft_data and soft_data['pgsql_server']:
            if isinstance(soft_data['pgsql_server'], dict):
                simplified_soft_list.append({
                    'name': soft_data['pgsql_server'].get('name', 'pgsql'),
                    'version': soft_data['pgsql_server'].get('version', ''),
                    'size': soft_data['pgsql_server'].get('size', 0)
                })
            else:
                simplified_soft_list.append({
                    'name': 'pgsql',
                    'version': soft_data['pgsql_server'],
                    'size': 0
                })

        # 处理phpMyAdmin
        if 'phpmyadmin_version' in soft_data and soft_data['phpmyadmin_version']:
            if isinstance(soft_data['phpmyadmin_version'], dict):
                simplified_soft_list.append({
                    'name': soft_data['phpmyadmin_version'].get('name', 'phpmyadmin'),
                    'version': soft_data['phpmyadmin_version'].get('version', ''),
                    'size': soft_data['phpmyadmin_version'].get('size', 0)
                })
            else:
                simplified_soft_list.append({
                    'name': 'phpmyadmin',
                    'version': soft_data['phpmyadmin_version'],
                    'size': 0
                })

        return simplified_soft_list

    def get_site_list(self) -> list:
        """获取网站列表"""

        result = []
        try:
            # todo 移除node项目, 项目文件有问题
            data = public.M('sites').field('name,path,project_type,id,ps').where(
                "project_type != ? AND project_type != ?", ("WP2", "Node")
            ).select()
            if isinstance(data, str):
                return []

            for site in data:
                try:
                    path_size = public.ExecShell(f"du -sb {site['path']}")[0].split("\t")[0]
                except:
                    path_size = 0
                site_data = {
                    "name": site["name"],
                    "id": site["id"],
                    "ps": site["ps"],
                    "size": path_size,
                    "type": site["project_type"]
                }

                result.append(site_data)
            return result
        except Exception as e:
            public.print_log(f"Failed to get site list: {str(e)}")
            return []

    def get_wp_tools_list(self) -> list:
        """获取网站列表"""
        result = []
        try:
            data = public.M('sites').field('name,path,project_type,id,ps').where(
                "project_type = ?", "WP2"
            ).select()
            if isinstance(data, str):
                return []
            for site in data:
                try:
                    path_size = public.ExecShell(f"du -sb {site['path']}")[0].split("\t")[0]
                except:
                    path_size = 0
                site_data = {
                    "name": site["name"],
                    "id": site["id"],
                    "ps": site["ps"],
                    "size": path_size,
                    "type": site["project_type"]
                }
                result.append(site_data)
            return result
        except Exception as e:
            public.print_log(f"Failed to get site list: {str(e)}")
            return []

    def get_domian_ssl_list(self) -> list:
        """获取SSL证书列表"""
        try:
            data = public.S("dns_domain_ssl").field("id", "subject", "info").select()
            if isinstance(data, str):
                return []
            result = []
            for i in data:
                try:
                    info = json.loads(i.get("info", "{}"))
                    name = info.get("issuer_O", "unknown")
                except:
                    name = "unknown"
                result.append({
                    "name": name,
                    "id": i['id'],
                    "ps": i['subject'],
                    "size": 0,
                })
            return result
        except Exception as e:
            public.print_log(f"Failed to get SSL certificate list: {str(e)}")
            return []

    def get_domian_provider_list(self) -> list:
        """获取SSL证书提供商列表"""
        try:
            data = public.S("dns_domain_provider").field(
                "id", "name", "api_user", "domains", "alias"
            ).select()
            if isinstance(data, str):
                return []
            result = [
                {
                    "name": x.get("alias"),
                    "id": x.get("id"),
                    "ps": x.get("name"),
                    "size": 0,
                } for x in data
            ]
            return result
        except Exception as e:
            public.print_log(f"Failed to get SSL certificate provider list: {str(e)}")
            return []

    def get_database_list(self) -> list:
        """获取db数据库列表"""
        result: list = []
        try:
            data = public.M('databases').field('name,type,id,sid,ps').select()
            for i in data:
                db_size = 0
                db_name = None
                if i['type'].lower() in ['mysql'] and i['sid'] == 0:
                    try:
                        db_name = i['name']
                        table_list = self.mysql_obj.query(f"show tables from `{db_name}`")
                        for tb_info in table_list:
                            table = self.mysql_obj.query(
                                f"show table status from `{db_name}` where name = '{tb_info[0]}'"
                            )
                            if not table:
                                continue
                            table_6 = table[0][6] or 0
                            table_7 = table[0][7] or 0
                            db_size += int(table_6) + int(table_7)
                    except:
                        db_size = self.get_file_size("/www/server/data/{}".format(db_name))
                elif i['type'].lower() in ['pgsql'] and i['sid'] == 0:
                    # todo pgsql get size
                    pass
                elif i['type'].lower() in ['mongodb'] and i['sid'] == 0:
                    # todo mg get size
                    pass

                db_data = {
                    "name": i['name'],
                    "id": i['id'],
                    "ps": i['ps'],
                    "type": i['type'],
                    "size": db_size
                }
                result.append(db_data)
            # 单独获取redis数据
            if os.path.exists("/www/server/redis/src/redis-server"):
                if os.path.exists("/www/server/redis/dump.rdb"):
                    redis_size = self.get_file_size("/www/server/redis/dump.rdb")
                elif os.path.exists("/www/server/redis/appendonly.aof"):
                    redis_size = self.get_file_size("/www/server/redis/appendonly.aof")
                else:
                    redis_size = 0
                redis_data = {
                    "name": "redis",
                    "id": 0,
                    "ps": "redis",
                    "type": "redis",
                    "size": redis_size
                }
                result.append(redis_data)
            return result
        except Exception as e:
            public.print_log("Failed to get database list: {}".format(str(e)))
            return []

    def get_ftp_list(self) -> list:
        """获取FTP列表"""
        try:
            data = public.M('ftps').field('name,id').select()
            if isinstance(data, str):
                return []
            return [{"name": i['name'], "id": i['id']} for i in data]
        except Exception as e:
            public.print_log("Failed to get FTP list: {}".format(str(e)))
            return []

    def get_ssh_dict(self) -> dict:
        """获取SSH列表"""
        result = {}
        try:
            ssh_path = "/www/server/panel/config/ssh_info"
            ssh_user_command_file = "/www/server/panel/config/ssh_info/user_command.json"
            path_size = self.get_file_size(ssh_path)
            command_size = self.get_file_size(ssh_user_command_file)
            result['ssh_size'] = int(path_size) - int(command_size)
            result['command_size'] = int(command_size)
            return result
        except Exception as e:
            public.print_log("Failed to get SSH list: {}".format(str(e)))
            return {'ssh_size': 0, 'command_size': 0}

    def get_crontab_list(self) -> list:
        try:
            data = public.M('crontab').field('name,id').select()
            if isinstance(data, str):
                return []
            return [{"name": i['name'], "id": i['id']} for i in data]
        except Exception as e:
            public.print_log("Failed to get scheduled task list: {}".format(str(e)))
            return []

    def get_firewall_list(self) -> dict:
        result = {}
        try:
            result['firewall_ip'] = public.M('firewall_ip').count()
            result['firewall_conutry'] = public.M('firewall_country').count()
            result['firewall_new'] = public.M('firewall_new').count()
            result['firewall_forward'] = public.M('firewall_forward').count()
            # result['firewall_domain'] = public.M('firewall_domain').count()
            # result['firewall_malicious_ip'] = public.M('firewall_malicious_ip').count()
            return result
        except Exception as e:
            public.print_log("Failed to get firewall list: {}".format(str(e)))
            return {}

    def get_plugin_list(self) -> list:
        plugin_list = ['btwaf', 'syssafe', 'monitor', 'tamper_core']
        result = []
        plugin_name = None
        for plugin in plugin_list:
            if os.path.exists("/www/server/panel/plugin/{}".format(plugin)):
                if plugin == "btwaf":
                    plugin_name = "btwaf"
                elif plugin == "syssafe":
                    plugin_name = "syssafe"
                elif plugin == "monitor":
                    plugin_name = "monitor"
                elif plugin == "tamper_core":
                    plugin_name = "tamper_core"
                result.append({
                    "name": plugin_name,
                    "size": self.get_file_size("/www/server/panel/plugin/{}".format(plugin))
                })
        return result

    def get_vmail_info(self) -> dict:
        result = {}
        if os.path.exists("/www/vmail"):
            result = {
                "name": "vmail data",
                "size": self.get_file_size("/www/vmail")
            }
        return result

    def get_web_status(self) -> dict:
        """获取Web服务器状态"""
        result = {}
        try:
            result['web'] = public.get_webserver()
            if result['web'] == "nginx":
                conf_result = public.ExecShell('ulimit -n 8192;nginx -t')
                if 'successful' not in conf_result[1]:
                    result['status'] = "err"
                    result['err'] = conf_result[1]
                else:
                    result['status'] = "ok"
            return result
        except Exception as e:
            public.print_log("Failed to get web status: {}".format(str(e)))
            return {'web': None, 'status': str(e)}

    def get_free_space(self) -> dict:
        """获取可用空间"""
        try:
            path = "/www"
            diskstat = os.statvfs(path)
            free_space = diskstat.f_bavail * diskstat.f_frsize
            return {'free_space': free_space}
        except Exception as e:
            public.print_log("Failed to get free space: {}".format(str(e)))
            return {'free_space': 0}

    def get_server_config(self) -> dict:
        """获取服务器配置信息"""
        result = {}
        try:
            # 获取Web服务器信息
            result['webserver'] = {}
            webserver = None
            if os.path.exists("/www/server/nginx/sbin/nginx"):
                webserver = "nginx"
            elif os.path.exists("/www/server/apache/bin/httpd"):
                webserver = "apache"
            result['webserver']['name'] = webserver
            result['webserver']['status'] = None

            # 获取PHP信息
            result['php'] = {}
            php_dir = "/www/server/php"
            for dir_name in os.listdir(php_dir):
                dir_path = os.path.join(php_dir, dir_name)
                if os.path.isdir(dir_path) and os.path.exists(os.path.join(dir_path, 'bin/php')):
                    php_ext = public.ExecShell(f"/www/server/php/{dir_name}/bin/php -m")[0].split("\n")
                    filtered_data = [item for item in php_ext if item not in ('[PHP Modules]', '[Zend Modules]', '')]
                    result['php'][dir_name] = {
                        'status': None,
                        'php_ext': filtered_data
                    }

            # 获取MySQL信息
            result['mysql'] = {}
            if os.path.exists("/www/server/mysql/bin/mysql"):
                # 添加MySQL相关信息
                pass

            return result
        except Exception as e:
            public.print_log("Failed to get server configuration: {}".format(str(e)))
            return {}

    @staticmethod
    def _generate_soft_list(backup_info: dict) -> list:
        soft_list = []
        if "soft" in backup_info['data_list']:
            soft_data = backup_info["data_list"]["soft"]

            # 处理Web服务器
            if "web_server" in soft_data and soft_data["web_server"]:
                soft_list.append({
                    "name": soft_data["web_server"].get("name", ""),
                    "version": soft_data["web_server"].get("version", ""),
                    "size": soft_data["web_server"].get("size", 0),
                    "status": soft_data["web_server"].get("status", 0),
                })

            # 处理PHP版本
            if "php_server" in soft_data and soft_data["php_server"]:
                for php in soft_data["php_server"]:
                    soft_list.append({
                        "name": php.get("name", ""),
                        "version": php.get("version", ""),
                        "size": php.get("size", 0),
                        "status": php.get("status", 0),
                    })

            # 处理MySQL服务器
            if "mysql_server" in soft_data and soft_data["mysql_server"]:
                soft_list.append({
                    "name": soft_data["mysql_server"].get("type", "mysql"),
                    "version": soft_data["mysql_server"].get("version", ""),
                    "size": soft_data["mysql_server"].get("size", 0),
                    "status": soft_data["mysql_server"].get("status", 0),
                })

            # 处理FTP服务器
            if "ftp_server" in soft_data and soft_data["ftp_server"]:
                soft_list.append({
                    "name": soft_data["ftp_server"].get("name", ""),
                    "version": soft_data["ftp_server"].get("version", ""),
                    "size": soft_data["ftp_server"].get("size", 0),
                    "status": soft_data["ftp_server"].get("status", 0),
                })

            # 处理node服务器
            if "node_list" in soft_data and soft_data["node_list"]:
                for node in soft_data["node_list"]:
                    soft_list.append({
                        "name": node.get("name", ""),
                        "version": node.get("version", ""),
                        "size": node.get("size", 0),
                        "status": node.get("status", 0),
                    })

            # 处理Redis服务器
            if "redis_server" in soft_data and soft_data["redis_server"]:
                soft_list.append({
                    "name": soft_data["redis_server"].get("name", ""),
                    "version": soft_data["redis_server"].get("version", ""),
                    "size": soft_data["redis_server"].get("size", 0),
                    "status": soft_data["redis_server"].get("status", 0),
                })

            # 处理Memcached服务器
            if "memcached_server" in soft_data and soft_data["memcached_server"]:
                soft_list.append({
                    "name": soft_data["memcached_server"].get("name", ""),
                    "version": soft_data["memcached_server"].get("version", ""),
                    "size": soft_data["memcached_server"].get("size", 0),
                    "status": soft_data["memcached_server"].get("status", 0),
                })

            # 处理MongoDB服务器
            if "mongodb_server" in soft_data and soft_data["mongodb_server"]:
                soft_list.append({
                    "name": soft_data["mongodb_server"].get("name", ""),
                    "version": soft_data["mongodb_server"].get("version", ""),
                    "size": soft_data["mongodb_server"].get("size", 0),
                    "status": soft_data["mongodb_server"].get("status", 0),
                })

            # 处理PostgreSQL服务器
            if "pgsql_server" in soft_data and soft_data["pgsql_server"]:
                soft_list.append({
                    "name": soft_data["pgsql_server"].get("name", ""),
                    "version": soft_data["pgsql_server"].get("version", ""),
                    "size": soft_data["pgsql_server"].get("size", 0),
                    "status": soft_data["pgsql_server"].get("status", 0),
                })

            # 处理phpMyAdmin
            if "phpmyadmin_version" in soft_data and soft_data["phpmyadmin_version"]:
                soft_list.append({
                    "name": soft_data["phpmyadmin_version"].get("name", ""),
                    "version": soft_data["phpmyadmin_version"].get("version", ""),
                    "size": soft_data["phpmyadmin_version"].get("size", 0),
                    "status": soft_data["phpmyadmin_version"].get("status", 0),
                })

        return soft_list

    @staticmethod
    def process_detail(backup_info: dict) -> dict:
        try:
            disk_use = int(backup_info.get("backup_file_size", 0)) * 2
        except Exception as e:
            public.print_log("Error calculating disk use: {}".format(str(e)))
            disk_use = backup_info.get("backup_file_size", 0)

        # 提取基本信息
        result = {
            "data": {
                "type": "backup",
                "done_time": backup_info.get("done_time", ""),
                "total_time": backup_info.get("total_time", 0),
                "backup_file": backup_info.get("backup_file", ""),
                "backup_file_size": backup_info.get("backup_file_size", "0"),
                "backup_file_sha256": backup_info.get("backup_file_sha256", ""),
                "disk_use": disk_use,
                "disk_free": DataManager().get_free_space()['free_space'],
                "data_status": {
                    "env_list": [],
                    "site_list": [],
                    "wp_list": [],
                    "ssl_info": {
                        "ssl_list": [],
                        "provider_list": [],
                    },
                    "ftp_list": [],
                    "database_list": [],
                    "crontab_list": [],
                    "plugin_list": [],
                    "soft_data": [],
                    "vmail_info": {},
                    "firewall_info": {},
                    "ssh_info": {},
                }
            }
        }

        # 处理软件列表
        if "soft" in backup_info['data_list']:
            soft_list = DataManager()._generate_soft_list(backup_info)
            # 添加到结果中
            result["data"]["data_status"]["soft_data"] = soft_list
            # 添加软件数据到环境列表
            result["data"]["data_status"]["env_list"] = [
                {
                    "name": soft.get("name", ""),
                    "version": soft.get("version", ""),
                    "size": soft.get("size", 0),
                    "status": soft.get("status", 2),
                    "err_msg": None
                } for soft in soft_list
            ]

        # 处理网站列表
        if "data_list" in backup_info and "site" in backup_info["data_list"]:
            for site in backup_info["data_list"].get("site", []):
                s_info = {
                    "name": site.get("name", ""),
                    "type": site.get("project_type", ""),
                    "size": site.get("size", 0),
                    "status": site.get("status", 2),
                    "err_msg": site.get("msg", None)
                }
                # wp
                if site.get("project_type", "").lower() in ["wp", "wp2"]:
                    result["data"]["data_status"]["wp_list"].append(s_info)
                # php 其他类型
                else:
                    result["data"]["data_status"]["site_list"].append(s_info)

        # 处理SSL信息
        ssl_info = backup_info["data_list"]["ssl"]
        for ssl in ssl_info.get("ssl_list", []):
            result["data"]["data_status"]["ssl_info"]["ssl_list"].append({
                "name": ", ".join(ssl.get("dns", [])),
                "type": ssl["info"].get("issuer_O", ""),
                "size": ssl.get("size", 0),
                "status": ssl.get("status", 2),
                "err_msg": ssl.get("msg", None)
            })
        for p in ssl_info.get("provider_list", []):
            result["data"]["data_status"]["ssl_info"]["provider_list"].append({
                "name": p.get("alias", ""),
                "type": p.get("name", ""),
                "size": p.get("size", 0),
                "status": p.get("status", 0),
                "err_msg": p.get("msg", None)
            })

        # 处理数据库列表
        if "data_list" in backup_info and "database" in backup_info["data_list"]:
            result["data"]["data_status"]["database_list"] = [
                {
                    "name": db.get("name", ""),
                    "type": db.get("type", ""),
                    "size": db.get("size", 0),
                    "status": db.get("status", 0),
                    "err_msg": db.get("msg", None)
                } for db in backup_info["data_list"]["database"]
            ]

        # 处理FTP列表
        if "data_list" in backup_info and "ftp" in backup_info["data_list"]:
            result["data"]["data_status"]["ftp_list"] = [
                {
                    "name": ftp.get("name", ""),
                    "size": ftp.get("size", 0),
                    "status": ftp.get("status", 0),
                    "err_msg": ftp.get("msg", None)
                } for ftp in backup_info["data_list"]["ftp"]
            ]

        # 处理计划任务
        if "data_list" in backup_info and "crontab" in backup_info["data_list"]:
            crontab_data = backup_info["data_list"]["crontab"]
            crontab_list = []
            try:
                if crontab_data.get("crontab_json") and os.path.exists(crontab_data["crontab_json"]):
                    cron_json_info = json.loads(public.ReadFile(crontab_data["crontab_json"]))
                    if cron_json_info:
                        crontab_list = [
                            {
                                "name": crontab.get("name", ""),
                                "size": crontab.get("id", 0),
                                "status": 2,
                                "err_msg": None
                            } for crontab in cron_json_info
                        ]
            except Exception as e:
                public.print_log("Error reading crontab JSON: {}".format(str(e)))

            result["data"]["data_status"]["crontab_list"] = crontab_list

        # 处理SSH列表
        if "data_list" in backup_info and "ssh" in backup_info["data_list"]:
            ssh_data = backup_info["data_list"]["ssh"]
            ssh_size = 0
            command_size = 0
            try:
                if ssh_data.get("ssh_info_path") and os.path.exists(ssh_data["ssh_info_path"] + "/ssh_info"):
                    real_path = os.path.join(ssh_data["ssh_info_path"], "ssh_info")
                    for i in os.listdir(real_path):
                        if i != "127.0.0.1" and i != "localhost":
                            ssh_size += 1
                        if i == "user_command.json" and os.path.isfile(real_path + "/" + i):
                            command_info = public.ReadFile(os.path.join(real_path, i))
                            if command_info:
                                try:
                                    command_info = json.loads(command_info)
                                except:
                                    command_info = []
                                command_size = len(command_info)
            except Exception as e:
                public.print_log("Error reading SSH info files: {}".format(str(e)))
            ssh_info: Dict[str, Any] = {
                "ssh_size": ssh_size,
                "command_size": command_size,
                "status": 2,
                "err_msg": None
            }
            result["data"]["data_status"]["ssh_info"] = ssh_info

        # 处理防火墙列表
        if "data_list" in backup_info and "firewall" in backup_info["data_list"]:
            firewall_data = backup_info["data_list"]["firewall"]
            prot_list, ip_list, forward_list, contry_list = [], [], [], []
            try:
                prot_data = public.ReadFile(firewall_data.get("port_data_path", ""))
                prot_list = json.loads(prot_data)
            except:
                pass

            try:
                ip_data = public.ReadFile(firewall_data.get("ip_data_path", ""))
                ip_list = json.loads(ip_data)
            except:
                pass

            try:
                forward_data = public.ReadFile(firewall_data.get("forward_data_path", ""))
                forward_list = json.loads(forward_data)
            except:
                pass

            try:
                contry_data = public.ReadFile(firewall_data.get("country_data_path", ""))
                contry_list = contry_data.split("\n")
            except:
                pass

            firewall_info: Dict[str, Any] = {
                "firewall_new": len(prot_list),
                "firewall_ip": len(ip_list),
                "firewall_forward": len(forward_list),
                "firewall_conutry": len(contry_list),
                "status": 2,
                "err_msg": None,
            }
            result["data"]["data_status"]["firewall_info"] = firewall_info

        # 处理插件列表
        if "data_list" in backup_info and "plugin" in backup_info["data_list"]:
            plugin_data = backup_info["data_list"]["plugin"]
            # 检查插件数据格式
            if isinstance(plugin_data, dict):
                # 新格式：{"plugin_name": {"status": x, "err_msg": y}}
                result["data"]["data_status"]["plugin_list"] = [
                    {
                        "name": plugin_name,
                        "display_name": plugin_name,
                        "size": plugin_info.get("size", 0),
                        "status": plugin_info.get("status", 2),
                        "err_msg": plugin_info.get("err_msg", None)
                    } for plugin_name, plugin_info in plugin_data.items()
                ]
            else:
                # 旧格式：[{"name": x, "size": y}]
                result["data"]["data_status"]["plugin_list"] = [
                    {
                        "name": plugin.get("name", ""),
                        "display_name": plugin.get("name", ""),
                        "size": plugin.get("size", 0),
                        "status": 2,
                        "err_msg": None
                    } for plugin in plugin_data
                ]

        # 处理邮局数据
        if "data_list" in backup_info and "vmail" in backup_info["data_list"]:
            vmail_data = backup_info["data_list"]["vmail"]
            vmail_info: Dict[str, Any] = {
                "name": "vmail",
                "size": vmail_data.get("size", 0),
                "status": 2,
                "err_msg": None
            }
            result["data"]["data_status"]["vmail_info"] = vmail_info

        return result["data"]

    def get_progress_with_type(self, my_type: str) -> dict:
        """获取备份进度"""

        def create_completed_result(backup_timestamp):
            if not backup_timestamp:
                return public.ReturnMsg(False, public.lang("Backup completed but unable to retrieve timestamp"))

            if not os.path.exists(self.bakcup_task_json):
                return public.ReturnMsg(False, public.lang("Backup configuration file does not exist"))

            backup_configs = json.loads(public.ReadFile(self.bakcup_task_json))

            success_data = next(
                (item for item in backup_configs if str(item.get('timestamp')) == str(backup_timestamp)), {}
            )
            return {
                "task_type": my_type,
                "task_status": 2,
                "backup_data": None,
                "backup_name": None,
                "data_backup_status": 2,
                "progress": 100,
                "msg": None,
                'exec_log': public.ReadFile(log_file) if os.path.exists(log_file) else "",
                'timestamp': backup_timestamp,
                'backup_file_info': success_data,
                'err_info': []
            }

        if my_type not in ["backup", "restore"]:
            raise HintException("Invalid type. Must be 'backup' or 'restore'.")

        pl_file = self.base_path + f'/{my_type}.pl'
        log_file = self.base_path + f'/{my_type}.log'
        if my_type == "backup":
            success_file = self.base_path + f'/success.pl'
        else:
            success_file = self.base_path + f'/restore_success.pl'

        count = 0
        while 1:
            count += 1
            if count >= 10:
                raise HintException(public.lang(f"{my_type} progress file not found or empty, please try again."))
            ts = public.ReadFile(pl_file)
            json_path = f"{self.base_path}/{ts}_backup/{my_type}.json"
            if not os.path.exists(pl_file):
                time.sleep(1)
                if os.path.exists(success_file):
                    success_time = int(os.path.getctime(success_file))
                    if success_time + 10 > int(time.time()):
                        try:
                            backup_timestamp = public.ReadFile(success_file).strip()
                            return public.ReturnMsg(True, create_completed_result(backup_timestamp))
                        except Exception as e:
                            public.ExecShell("rm -f {}".format(success_file))
                            raise HintException(
                                public.lang("Error retrieving backup completion information: {}").format(str(e))
                            )
                    else:
                        public.ExecShell("rm -f {}".format(success_file))

            if not os.path.exists(pl_file) or not ts or not os.path.exists(json_path):
                time.sleep(1)
                continue
            else:
                break
        ts = ts.strip()
        conf_data = json.loads(public.ReadFile(json_path))
        log_data = public.ReadFile(log_file) if os.path.exists(log_file) else ""

        # 定义备份类型及其处理逻辑
        types = [
            {
                'type': 'site',
                'data_key': 'site',
                'display_name': 'site',
                'progress': 30
            },
            {
                'type': 'database',
                'data_key': 'database',
                'display_name': 'database',
                'progress': 70
            },
            {
                'type': 'ftp',
                'data_key': 'ftp',
                'display_name': 'ftp',
                'progress': 85
            },
            {
                'type': 'ssh',
                'data_key': 'ssh',
                'display_name': 'ssh',
                'progress': 85
            },
        ]

        current_process = 0
        last_progress = 0
        current_task_info = None
        status_key = "status" if my_type == "backup" else "restore_status"

        for index, process in enumerate(types):
            items = conf_data.get("data_list", {}).get(process['data_key'], [])
            total = len(items)
            if total == 0:  # 认为已完成
                last_progress = process['progress']
                continue

            done_count = len([x for x in items if isinstance(x, dict) and x.get(status_key) == 2])
            rate = done_count / total

            progress_range = process['progress'] - (types[index - 1]['progress'] if index > 0 else 0)
            current_process = round(last_progress + progress_range * rate)
            if done_count < total:  # 如果有未完成项
                for item in items:
                    if isinstance(item, dict) and item.get(status_key) != 2:
                        current_task_info = {
                            "task_type": my_type,
                            "task_status": 1,
                            "data_type": process['type'],
                            "name": item.get("name", f"unknow {process['display_name']}"),
                            "data_backup_status": item.get("status", 0),
                            "progress": current_process if current_process > 5 else 5,
                            "msg": item.get("msg"),
                            'exec_log': log_data,
                            'timestamp': ts
                        }
                        break
                break
            # 当前类型全部完成
            last_progress = process['progress']

        if current_task_info:
            # 正在处理的任务，更新其进度并返回
            current_task_info['progress'] = current_process
            return public.ReturnMsg(True, current_task_info)

        # 检查数据打包进度
        try:
            key = "backup_status" if my_type == "backup" else "restore_status"
            backup_status = conf_data.get(key)
            if backup_status == 1:
                return public.ReturnMsg(True, {
                    "task_type": my_type,
                    "task_status": 1,
                    "data_type": "tar",
                    "name": public.lang("Data Packaging"),
                    "data_backup_status": 1,
                    "progress": 90,
                    'exec_log': log_data,
                    'timestamp': ts
                })
        except Exception as e:
            # 可能没有backup_status字段，继续处理
            pass

        # 如果没有发现进行中的任务，但有进程
        if ts:
            # 如果 current_process 已经是 types 定义的最大值，说明所有数据处理完成
            if current_process >= types[-1]['progress']:
                return public.ReturnMsg(True, {
                    "task_type": my_type,
                    "task_status": 1,
                    "data_type": "tar",
                    "name": public.lang("Data Packaging"),
                    "data_backup_status": 1,
                    "progress": 95,
                    'exec_log': log_data,
                    'timestamp': ts
                })

            return public.ReturnMsg(True, {
                "task_type": my_type,
                "task_status": 1,
                "name": public.lang("Preparing data"),
                "data_backup_status": 1,
                "progress": current_process if current_process > 5 else 5,
                'exec_log': log_data,
                'timestamp': ts
            })
        return public.ReturnMsg(False, public.lang("No ongoing tasks found. Please check"))


if __name__ == '__main__':
    # 获取命令行参数
    if len(sys.argv) < 3:
        print("Usage: btpython data_manager.py <method>")
        sys.exit(1)
    method_name = sys.argv[1]  # 方法名
    data_manager = DataManager()  # 实例化对象
    if hasattr(data_manager, method_name):  # 检查方法是否存在
        method = getattr(data_manager, method_name)  # 获取方法
        method()  # 调用方法
    else:
        print(f"Error: Method '{method_name}' does not exist")
