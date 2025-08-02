# coding: utf-8
# -------------------------------------------------------------------
# aapanel
# -------------------------------------------------------------------
# Copyright (c) 2015-2099 aapanel(http://www.aapanel.com) All rights reserved.
# -------------------------------------------------------------------
# Author: miku <miku@bt.cn>
# -------------------------------------------------------------------
import json
import os
import re
import sys
import warnings

if "/www/server/panel/class" not in sys.path:
    sys.path.insert(0, "/www/server/panel/class")
if "/www/server/panel/class_v2" not in sys.path:
    sys.path.insert(0, "/www/server/panel/class_v2")
if "/www/server/panel" not in sys.path:
    sys.path.insert(0, "/www/server/panel")

import public
from BTPanel import app
from mod.project.backup_restore.base_util import BaseUtil
from mod.project.backup_restore.config_manager import ConfigManager

warnings.filterwarnings("ignore", category=SyntaxWarning)

OFFICIAL_URL = public.OfficialDownloadBase()


class SoftModule(BaseUtil, ConfigManager):
    def __init__(self):
        super().__init__()
        self.base_path = '/www/backup/backup_restore'
        self.bakcup_task_json = self.base_path + '/backup_task.json'
        self.packet = False

    def get_install_type(self):
        if os.path.exists("/usr/bin/yum") or os.path.exists("/usr/bin/dnf") or os.path.exists("/usr/sbin/yum"):
            return 1
        elif os.path.exists(
                "/usr/bin/apt"
        ) or os.path.exists(
            "/usr/sbin/apt-get"
        ) or os.path.exists(
            "/usr/bin/apt-get"
        ):
            return 4
        else:
            return 0

    def get_web_server(self):
        if os.path.exists("/www/server/nginx/sbin/nginx"):
            nginx_version = public.ExecShell("nginx -v 2>&1")[0].replace("\n", "")
            version_match = re.search(r'nginx/(\d+\.\d+)', nginx_version)
            if version_match:
                nginx_version = version_match.group(1)

            result = {
                "name": "nginx",
                "version": nginx_version,
                "size": BaseUtil().get_file_size("/www/server/nginx/"),
                "status": 2,
            }
            self.print_log("nginx {} ✓".format(nginx_version), 'backup')
            return result

        if os.path.exists("/www/server/apache/bin/httpd"):
            apache_version = public.ExecShell("httpd -v 2>&1")[0].replace("\n", "")
            version_match = re.search(r'Apache/(\d+\.\d+)', apache_version)
            if version_match:
                apache_version = version_match.group(1)

            result = {
                "name": "apache",
                "version": apache_version,
                "size": BaseUtil().get_file_size("/www/server/apache/"),
                "status": 2,
            }
            self.print_log("apache {} ✓".format(apache_version), 'backup')
            return result

        if os.path.exists("/usr/local/lsws/bin/openlitespeed"):
            openlitespeed_version = public.ExecShell(
                "/usr/local/lsws/bin/openlitespeed -v 2>&1")[0].replace("\n", "")
            version_match = re.search(r'LiteSpeed/(\d+\.\d+\.\d+) Open', openlitespeed_version)
            if version_match:
                openlitespeed_version = version_match.group(1)

            result = {
                "name": "openlitespeed",
                "version": openlitespeed_version,
                "size": BaseUtil().get_file_size("/usr/local/lsws/"),
                "status": 2,
            }
            self.print_log("openlitespeed {} ✓".format(openlitespeed_version), 'backup')
            return result

    def get_php_server(self):
        php_dir = "/www/server/php"
        if os.path.exists(php_dir):
            phplist = []
            for dir_name in os.listdir(php_dir):
                dir_path = dir_path = os.path.join(php_dir, dir_name)
                if os.path.isdir(dir_path) and os.path.exists(os.path.join(dir_path, 'bin/php')):
                    phplist.append(int(dir_name))

            result = []
            for php_ver in phplist:
                php_ext = public.ExecShell("/www/server/php/{}/bin/php -m".format(php_ver))[0].split("\n")
                filtered_data = [item for item in php_ext if item not in ('[PHP Modules]', '[Zend Modules]', '')]
                php_result = {
                    "name": "php",
                    "version": php_ver,
                    "php_ext": filtered_data,
                    "size": BaseUtil().get_file_size("/www/server/php/{}".format(php_ver)),
                    "status": 2,
                }
                # 将PHP版本号转换为带小数点的格式
                if isinstance(php_ver, (int, str)) and len(str(php_ver)) == 2:
                    # 例如：54 -> 5.4, 70 -> 7.0
                    php_result['version'] = f"{str(php_ver)[0]}.{str(php_ver)[1]}"
                elif isinstance(php_ver, (int, str)) and len(str(php_ver)) == 3:
                    # 例如：82 -> 8.2
                    php_result['version'] = f"{str(php_ver)[0]}.{str(php_ver)[1:]}"
                result.append(php_result)
                self.print_log("php {} ✓".format(php_result['version']), 'backup')
            return result
        return None

    def get_mysql_server(self):
        if os.path.exists("/www/server/mysql/bin/mysql"):
            mysql_version = None
            if os.path.exists("/www/server/mysql/version.pl"):
                mysql_version = public.ReadFile("/www/server/mysql/version.pl").replace("\n", "")
            elif os.path.exists("/www/server/mysql/version_check.pl"):
                mysql_version = public.ExecShell("/www/server/mysql/version_check.pl")[0].replace("\n", "")

            match = re.search(r'10\.\d+', mysql_version)
            if match:
                version = match.group()
                type = "mariadb"
                mysql_version = version
            else:
                type = "mysql"
                mysql_version = mysql_version[0:3]
            result = {
                "type": type,
                "version": mysql_version,
                "size": BaseUtil().get_file_size("/www/server/mysql/"),
                "status": 2,
            }
            self.print_log("mysql {} ✓".format(mysql_version), 'backup')
            return result
        else:
            return False

    def get_ftp_server(self, get=None):
        if os.path.exists("/www/server/pure-ftpd/bin/pure-pw"):
            size = BaseUtil().get_file_size("/www/server/pure-ftpd/")
            try:
                pure_ftp_port = \
                    public.ExecShell("cat /www/server/pure-ftpd/etc/pure-ftpd.conf | grep Bind|awk '{print $2}'")[
                        0].replace("\n", "").replace("0.0.0.0,", "")
                pure_ftp_port = int(pure_ftp_port)
            except:
                pure_ftp_port = 21
            self.print_log("pure-ftpd {} ✓".format(pure_ftp_port), 'backup')
            return {
                "name": "pure-ftpd",
                "version": "1.0.49",
                "size": size,
                "port": int(pure_ftp_port),
                "status": 2,
            }
        else:
            return None

    def get_node_list(self, timestamp):
        node_dir = "/www/server/nodejs"
        if not os.path.exists(node_dir):
            return None
        node_list = []

        result = []
        for dir_name in os.listdir(node_dir):
            if re.match(r"^v[1-9]\d*(\.\d+)*$", dir_name):
                node_list.append(dir_name)

        for node_ver in node_list:
            node_ver_path = os.path.join(node_dir, node_ver)
            node_mod_path = os.path.join(node_ver_path, "lib", "node_modules")
            if os.path.isdir(node_mod_path):
                mod_list = os.listdir(node_mod_path)
            else:
                mod_list = []
            node_result = {
                "name": "node",
                "version": node_ver,
                "mod_list": mod_list,
                "size": BaseUtil().get_file_size("/www/server/nodejs/{}".format(node_ver)),
                "status": 2,
            }
            result.append(node_result)
            self.print_log("node {} ✓".format(node_ver), 'backup')

        if result and self.packet:
            backup_path = os.path.join(self.base_path, f"{timestamp}_backup/plugin")
            public.ExecShell(f"\cp -rpa /www/server/nodejs/* {backup_path}/nodejs/*")
        return result

    def get_redis_server(self):
        if os.path.exists("/www/server/redis/src/redis-server") and os.path.exists("/www/server/redis/version.pl"):
            redis_version = public.ReadFile("/www/server/redis/version.pl")
            size = BaseUtil().get_file_size("/www/server/redis/")
            self.print_log("redis {} ✓".format(redis_version[0:3]), 'backup')
            return {
                "name": "redis",
                "version": redis_version[0:3],
                "size": size,
                "status": 2,
            }
        else:
            return None

    def get_memcached_server(self):
        if os.path.exists("/usr/local/memcached/bin/memcached"):
            size = BaseUtil().get_file_size("/usr/local/memcached/")
            self.print_log("memcached {} ✓".format("1.6.12"), 'backup')
            return {
                "name": "memcached",
                "version": "1.6.12",
                "size": size,
                "status": 2,
            }
        else:
            return None

    def get_mongodb_server(self):
        if os.path.exists("/www/server/mongodb/version.pl"):
            mongod = "/www/server/mongodb/bin/mongod"
            mongo = "/www/server/mongodb/bin/mongo"
            if os.path.exists(mongod) or os.path.exists(mongo):
                mongodb_version = public.ReadFile("/www/server/mongodb/version.pl")
                size = BaseUtil().get_file_size("/www/server/mongodb/")
                self.print_log("mongodb {} ✓".format(mongodb_version[0:3]), 'backup')
                return {
                    "name": "mongodb",
                    "version": mongodb_version[0:3],
                    "size": size,
                    "status": 2,
                }
        else:
            return None

    def get_pgsql_server(self):
        if os.path.exists("/www/server/pgsql/bin/pg_config"):
            pgsql_version = \
                public.ExecShell("/www/server/pgsql/bin/pg_config --version")[0].replace("\n", "").split(" ")[1]
            size = BaseUtil().get_file_size("/www/server/pgsql/")
            self.print_log("pgsql {} ✓".format(pgsql_version), 'backup')
            return {
                "name": "pgsql",
                "version": pgsql_version,
                "size": size,
                "status": 2,
            }
        else:
            return None

    def get_phpmyadmin_version(self):
        if os.path.exists("/www/server/phpmyadmin/version.pl"):
            phpmyadmin_version = public.ReadFile("/www/server/phpmyadmin/version.pl").replace("\n", "")
            size = BaseUtil().get_file_size("/www/server/phpmyadmin/")
            self.print_log("phpmyadmin {} ✓".format(phpmyadmin_version), 'backup')
            return {
                "name": "phpmyadmin",
                "version": phpmyadmin_version,
                "size": size,
                "status": 2,
            }
        else:
            return None

    def get_soft_data(self, timestamp=None, packet: bool = False):
        self.print_log("====================================================", "backup")
        self.print_log(public.lang("Start backing up software information"), "backup")
        self.packet = packet
        result = {
            "web_server": self.get_web_server(),
            "php_server": self.get_php_server(),
            "mysql_server": self.get_mysql_server(),
            "ftp_server": self.get_ftp_server(),
            # "node_list": self.get_node_list(timestamp),
            "redis_server": self.get_redis_server(),
            "memcached_server": self.get_memcached_server(),
            "mongodb_server": self.get_mongodb_server(),
            "pgsql_server": self.get_pgsql_server(),
            "phpmyadmin_version": self.get_phpmyadmin_version(),
        }
        public.WriteFile("/root/soft.json", json.dumps(result))
        self.print_log(public.lang("Software information backup completed"), 'backup')
        return result

    # ======================== install software ========================
    def install_web_server(self, timestamp):
        restore_data = self.get_restore_data_list(timestamp)
        web_server = restore_data['data_list']['soft']['web_server']
        install_type = self.get_install_type()
        log_str = public.lang("Start installing nginx-{}").format(web_server.get('version', 'latest'))
        try:
            result = None
            if web_server['name'] == 'nginx':
                self.print_log(log_str, "restore")
                web_server['restore_status'] = 1
                web_server['msg'] = None
                self.update_restore_data_list(timestamp, restore_data)
                result = public.ExecShell(
                    "cd /www/server/panel/install && wget -O nginx.sh {}/install/{}/nginx.sh && bash nginx.sh install {}".format(
                        OFFICIAL_URL, install_type, web_server['version']
                    )
                )
            elif web_server['name'] == 'apache':
                self.print_log(public.lang("Start installing apache service"), "restore")
                web_server['restore_status'] = 1
                web_server['msg'] = None
                self.update_restore_data_list(timestamp, restore_data)
                result = public.ExecShell(
                    "cd /www/server/panel/install && wget -O apache.sh {}/install/{}/apache.sh && bash apache.sh install {}".format(
                        OFFICIAL_URL, install_type, web_server['version']
                    )
                )
            if web_server['name'] == 'nginx' and os.path.exists("/www/server/nginx/sbin/nginx"):
                new_log_str = "{}-{} ✓".format(web_server['name'], web_server['version'])
                self.replace_log(log_str, new_log_str, "restore")
                web_server['restore_status'] = 2
                web_server['msg'] = None
                self.update_restore_data_list(timestamp, restore_data)
            elif web_server['name'] == 'apache' and os.path.exists("/www/server/apache/bin/httpd"):
                new_log_str = "{}-{} ✓".format(web_server['name'], web_server['version'])
                self.replace_log(log_str, new_log_str, "restore")
                web_server['restore_status'] = 2
                web_server['msg'] = None
                self.update_restore_data_list(timestamp, restore_data)
            else:
                combined_output = (result[0] + result[1]).splitlines()
                err_msg = '\n'.join(combined_output[-10:])
                new_log_str = public.lang(
                    "{}-{} ✗ Installation failed Reason: {} \n Please try to reinstall the web server in the software store after the restore task ends").format(
                    web_server['name'], web_server['version'], err_msg
                )
                self.replace_log(log_str, new_log_str, "restore")
                web_server['restore_status'] = 3
                web_server['msg'] = new_log_str
                self.update_restore_data_list(timestamp, restore_data)
        except Exception as e:
            err_msg = public.lang(
                "{}-{} ✗ Installation failed Reason: {} \n Please try to reinstall the web server in the software store after the restore task ends").format(
                web_server['name'], web_server['version'], str(e)
            )
            web_server['restore_status'] = 3
            web_server['msg'] = err_msg
            self.update_restore_data_list(timestamp, restore_data)

        self.print_log(public.lang("Web server installation completed"), "restore")

    def install_php_server(self, timestamp):
        restore_data = self.get_restore_data_list(timestamp)
        php_server = restore_data['data_list']['soft']['php_server']
        install_type = self.get_install_type()
        for php in php_server:
            php_ver = php['version']
            self.update_restore_data_list(timestamp, restore_data)
            log_str = public.lang("Start installing php-{}").format(php_ver)
            self.print_log(log_str, "restore")
            path_ver = php_ver.replace('.', '')
            if os.path.exists("/www/server/php/{}".format(path_ver)):
                new_log_str = "php-{} ✓".format(php_ver)
                self.replace_log(log_str, new_log_str, "restore")
                continue

            result = public.ExecShell(
                "cd /www/server/panel/install && wget -O php.sh {}/install/{}/php.sh && bash php.sh install {}".format(
                    OFFICIAL_URL, install_type, php_ver
                )
            )
            if not os.path.exists("/www/server/php/{}".format(path_ver)):
                combined_output = (result[0] + result[1]).splitlines()
                err_msg = '\n'.join(combined_output[-10:])
                new_log_str = public.lang(
                    "php-{} ✗ Installation failed Reason: {} \n Please try to reinstall php in the software store after the restore task ends").format(
                    php_ver,
                    err_msg)
                php["restore_status"] = 3
                php["msg"] = err_msg
                self.replace_log(log_str, new_log_str, "restore")
            else:
                php["restore_status"] = 2
                php["msg"] = "success"
                new_log_str = "php-{} ✓".format(php_ver)
                self.replace_log(log_str, new_log_str, "restore")

            self.update_restore_data_list(timestamp, restore_data)

    def install_node(self, timestamp):
        restore_data = self.get_restore_data_list(timestamp)
        node_list = restore_data['data_list']['soft']['node_list']
        for node_data in node_list:
            node_ver = node_data['version']
            log_str = public.lang("Start installing node-{}").format(node_ver)
            self.print_log(log_str, "restore")
            if os.path.exists("/www/server/nodejs/{}".format(node_ver)):
                new_log_str = "node-{} ✓".format(node_ver)
                self.replace_log(log_str, new_log_str, "restore")
                continue
            result = public.ExecShell(
                "cd /www/server/panel/install && wget -O node_plugin_install.sh {}/install/0/node_plugin_install.sh && bash node_plugin_install.sh {}".format(
                    OFFICIAL_URL, node_ver
                )
            )

            for mod_list in node_data['mod_list']:
                mod_name = mod_list
                mod_shell = '''
export PATH
export HOME=/root
export NODE_PATH="/www/server/nodejs/{node_ver}/etc/node_modules"
/www/server/nodejs/{node_ver}//bin/npm config set registry https://registry.npmmirror.com/
/www/server/nodejs/{node_ver}//bin/npm config set prefix /www/server/nodejs/{node_ver}/
/www/server/nodejs/{node_ver}//bin/npm config set cache /www/server/nodejs/{node_ver}//cache
/www/server/nodejs/{node_ver}//bin/npm config set strict-ssl false
/www/server/nodejs/{node_ver}//bin/yarn config set registry https://registry.npmmirror.com/
/www/server/nodejs/{node_ver}/bin/npm install {mod_name} -g &> /www/server/panel/plugin/nodejs/exec.log           
                '''.format(node_ver=node_ver, mod_name=mod_name)
                result = public.ExecShell(mod_shell)
                if os.path.exists("/www/server/nodejs/{}".format(node_ver)):
                    new_log_str = "node-{} ✓".format(node_ver)
                    self.replace_log(log_str, new_log_str, "restore")
                    node_data["restore_status"] = 2
                    node_data["msg"] = None
                else:
                    combined_output = (result[0] + result[1]).splitlines()
                    err_msg = '\n'.join(combined_output[-10:])
                    new_log_str = public.lang(
                        "node-{} ✗ Installation failed Reason: {} \n Please try to reinstall node in the software store after the restore task ends").format(
                        node_ver, err_msg)
                    self.replace_log(log_str, new_log_str, "restore")
                    node_data["restore_status"] = 3
                    node_data["msg"] = err_msg
        self.update_restore_data_list(timestamp, restore_data)

    def install_mysql_server(self, timestamp):
        restore_data = self.get_restore_data_list(timestamp)
        mysql_server = restore_data['data_list']['soft']['mysql_server']
        install_type = self.get_install_type()
        if mysql_server['type'] == 'mariadb':
            log_str = public.lang("Start installing mariadb-{}").format(mysql_server['version'])
            self.print_log(log_str, "restore")
            if os.path.exists("/www/server/mysql/bin/mysql"):
                new_log_str = "mariadb-{} ✓".format(mysql_server['version'])
                self.replace_log(log_str, new_log_str, "restore")
                return
            result = public.ExecShell(
                "cd /www/server/panel/install && wget -O mysql.sh {}/install/{}/mysql.sh && bash mysql.sh install {}".format(
                    OFFICIAL_URL, install_type, f"mariadb_{mysql_server['version']}"
                )
            )
            if os.path.exists("/www/server/mysql/bin/mysql"):
                new_log_str = "mariadb-{} ✓".format(mysql_server['version'])
                self.replace_log(log_str, new_log_str, "restore")
                mysql_server["restore_status"] = 2
                mysql_server["msg"] = None
            else:
                combined_output = (result[0] + result[1]).splitlines()
                err_msg = '\n'.join(combined_output[-10:])
                new_log_str = public.lang(
                    "mariadb-{} ✗ Installation failed Reason: {} \n Please try to reinstall mariadb in the software store after the restore task ends").format(
                    mysql_server['version'], err_msg
                )
                self.replace_log(log_str, new_log_str, "restore")
                mysql_server["restore_status"] = 3
                mysql_server["msg"] = err_msg
            self.update_restore_data_list(timestamp, restore_data)
            return

        if mysql_server['type'] == 'mysql':
            log_str = public.lang("Start installing mysql-{}").format(mysql_server['version'])
            self.print_log(log_str, "restore")
            if os.path.exists("/www/server/mysql/bin/mysql"):
                new_log_str = "mysql-{} ✓".format(mysql_server['version'])
                self.replace_log(log_str, new_log_str, "restore")
                return
            result = public.ExecShell(
                "cd /www/server/panel/install && wget -O mysql.sh {}/install/{}/mysql.sh && bash mysql.sh install {}".format(
                    OFFICIAL_URL, install_type, mysql_server['version']
                )
            )
            if os.path.exists("/www/server/mysql/bin/mysql"):
                new_log_str = "mysql-{} ✓".format(mysql_server['version'])
                self.replace_log(log_str, new_log_str, "restore")
                mysql_server["restore_status"] = 2
                mysql_server["msg"] = None
            else:
                combined_output = (result[0] + result[1]).splitlines()
                err_msg = '\n'.join(combined_output[-10:])
                new_log_str = public.lang(
                    "mysql-{} ✗ Installation failed Reason: {} \n Please try to reinstall mysql in the software store after the restore task ends").format(
                    mysql_server['version'], err_msg
                )
                self.replace_log(log_str, new_log_str, "restore")
                mysql_server["restore_status"] = 3
                mysql_server["msg"] = err_msg
            self.update_restore_data_list(timestamp, restore_data)

    def install_mongodb_server(self, timestamp):
        restore_data = self.get_restore_data_list(timestamp)
        mongodb_server = restore_data['data_list']['soft']['mongodb_server']
        # install_type = self.get_install_type()
        log_str = public.lang("Start installing mongodb-{}").format(mongodb_server['version'])
        self.print_log(log_str, "restore")
        mongo = "/www/server/mongodb/bin/mongo"
        mongod = "/www/server/mongodb/bin/mongod"
        if (os.path.exists(mongo) or os.path.exists(mongod)) and os.path.exists("/www/server/mongodb/version.pl"):
            new_log_str = "mongodb-{} ✓".format(mongodb_server['version'])
            self.replace_log(log_str, new_log_str, "restore")
            return

        result = public.ExecShell(
            "cd /www/server/panel/install && wget -O mongodb.sh {}/install/0/mongodb.sh && bash mongodb.sh install {}".format(
                OFFICIAL_URL, mongodb_server['version']
            )
        )
        if os.path.exists(mongo) or os.path.exists(mongod):
            new_log_str = "mongodb-{} ✓".format(mongodb_server['version'])
            self.replace_log(log_str, new_log_str, "restore")
            mongodb_server["restore_status"] = 2
            mongodb_server["msg"] = None
        else:
            combined_output = (result[0] + result[1]).splitlines()
            err_msg = '\n'.join(combined_output[-10:])
            new_log_str = public.lang(
                "mongodb-{} ✗ Installation failed Reason: {} \n Please try to reinstall mongodb in the software store after the restore task ends").format(
                mongodb_server['version'], err_msg)
            self.replace_log(log_str, new_log_str, "restore")
            mongodb_server["restore_status"] = 3
            mongodb_server["msg"] = err_msg

        self.update_restore_data_list(timestamp, restore_data)

    def install_memcached_server(self, timestamp):
        restore_data = self.get_restore_data_list(timestamp)
        memcached_server = restore_data['data_list']['soft']['memcached_server']
        # install_type = self.get_install_type()
        log_str = public.lang("Start installing memcached-{}").format(memcached_server['version'])
        self.print_log(log_str, "restore")
        if os.path.exists("/usr/local/memcached/bin/memcached"):
            new_log_str = "memcached-{} ✓".format(memcached_server['version'])
            self.replace_log(log_str, new_log_str, "restore")
            return
        result = public.ExecShell(
            f"cd /www/server/panel/install && wget -O memcached.sh {OFFICIAL_URL}/install/0/memcached.sh && bash memcached.sh install"
        )
        if os.path.exists("/usr/local/memcached/bin/memcached"):
            new_log_str = "memcached-{} ✓".format(memcached_server['version'])
            self.replace_log(log_str, new_log_str, "restore")
            memcached_server["restore_status"] = 2
            memcached_server["msg"] = None
        else:
            combined_output = (result[0] + result[1]).splitlines()
            err_msg = '\n'.join(combined_output[-10:])
            new_log_str = public.lang(
                "memcached-{} ✗ Installation failed Reason: {} \n Please try to reinstall memcached in the software store after the restore task ends").format(
                memcached_server['version'], err_msg)
            self.replace_log(log_str, new_log_str, "restore")
            memcached_server["restore_status"] = 3
            memcached_server["msg"] = err_msg

        self.update_restore_data_list(timestamp, restore_data)

    def install_redis_server(self, timestamp):
        restore_data = self.get_restore_data_list(timestamp)
        redis_server = restore_data['data_list']['soft']['redis_server']
        # install_type = self.get_install_type()
        log_str = public.lang("Start installing redis-{}").format(redis_server['version'])
        self.print_log(log_str, "restore")
        if os.path.exists("/www/server/redis/src/redis-server") and os.path.exists("/www/server/redis/version.pl"):
            new_log_str = "redis-{} ✓".format(redis_server['version'])
            self.replace_log(log_str, new_log_str, "restore")
            return
        result = public.ExecShell(
            "cd /www/server/panel/install && wget -O redis.sh {}/install/0/redis.sh && bash redis.sh install {}".format(
                OFFICIAL_URL, redis_server['version']
            )
        )
        if os.path.exists("/www/server/redis/src/redis-cli"):
            new_log_str = "redis-{} ✓".format(redis_server['version'])
            self.replace_log(log_str, new_log_str, "restore")
            redis_server["restore_status"] = 2
            redis_server["msg"] = None
        else:
            combined_output = (result[0] + result[1]).splitlines()
            err_msg = '\n'.join(combined_output[-10:])
            new_log_str = "redis-{} ✗ {}".format(redis_server['version'], err_msg)
            self.replace_log(log_str, new_log_str, "restore")
            redis_server["restore_status"] = 3
            redis_server["msg"] = err_msg

        self.update_restore_data_list(timestamp, restore_data)

    def install_pgsql_server(self, timestamp):
        restore_data = self.get_restore_data_list(timestamp)
        pgsql_server = restore_data['data_list']['soft']['pgsql_server']
        log_str = public.lang("Start installing pgsql-{}").format(pgsql_server['version'])
        self.print_log(log_str, "restore")
        if os.path.exists("/www/server/pgsql/bin/pg_config"):
            new_log_str = "pgsql-{} ✓".format(pgsql_server['version'])
            self.replace_log(log_str, new_log_str, "restore")
            return
        self.update_restore_data_list(timestamp, restore_data)

        down_file = "postgresql-{pgsql_version}.tar.gz".format(pgsql_version=pgsql_server['version'])
        down_url = "{}/src/postgresql-{}.tar.gz".format(
            OFFICIAL_URL, pgsql_server['version']
        )

        result = public.ExecShell(
            "cd /www/server/panel/install && wget -O pgsql_install.sh {}/install/0/pgsql_install.sh && bash pgsql_install.sh {} {}".format(
                OFFICIAL_URL, down_file, down_url
            )
        )
        if os.path.exists("/www/server/pgsql/bin/psql"):
            new_log_str = "pgsql-{} ✓".format(pgsql_server['version'])
            self.replace_log(log_str, new_log_str, "restore")
            pgsql_server["restore_status"] = 2
            pgsql_server["msg"] = None
        else:
            combined_output = (result[0] + result[1]).splitlines()
            err_msg = '\n'.join(combined_output[-10:])
            new_log_str = "pgsql-{} ✗ {}".format(pgsql_server['version'], err_msg)
            self.replace_log(log_str, new_log_str, "restore")
            pgsql_server["restore_status"] = 3
            pgsql_server["msg"] = err_msg

        self.update_restore_data_list(timestamp, restore_data)

    def install_phpmyadmin(self, timestamp):
        restore_data = self.get_restore_data_list(timestamp)
        phpmyadmin_server = restore_data['data_list']['soft']['phpmyadmin_version']
        log_str = public.lang("Start installing phpmyadmin-{}").format(phpmyadmin_server['version'])
        self.print_log(log_str, "restore")
        result = public.ExecShell(
            "cd /www/server/panel/install && wget -O phpmyadmin.sh {}/install/0/phpmyadmin.sh && bash phpmyadmin.sh install {}".format(
                OFFICIAL_URL, phpmyadmin_server['version']
            )
        )
        if os.path.exists("/www/server/phpmyadmin/version.pl"):
            phpmyadmin_server["restore_status"] = 2
            phpmyadmin_server["msg"] = None
            new_log_str = "phpmyadmin-{} ✓".format(phpmyadmin_server['version'])
            self.replace_log(log_str, new_log_str, "restore")
        else:
            combined_output = (result[0] + result[1]).splitlines()
            err_msg = '\n'.join(combined_output[-10:])
            new_log_str = public.lang(
                "phpmyadmin-{} ✗ Installation failed Reason: {} \n Please try to reinstall phpmyadmin in the software store after the restore task ends").format(
                phpmyadmin_server['version'], err_msg
            )
            self.replace_log(log_str, new_log_str, "restore")
            phpmyadmin_server["restore_status"] = 3
            phpmyadmin_server["msg"] = err_msg

        self.update_restore_data_list(timestamp, restore_data)

    def install_ftp_server(self, timestamp):
        restore_data = self.get_restore_data_list(timestamp)
        ftp_server = restore_data['data_list']['soft']['ftp_server']
        log_str = public.lang("Start installing ftp-{}").format(ftp_server['version'])
        self.print_log(log_str, "restore")

        if os.path.exists("/www/server/pure-ftpd/bin/pure-pw"):
            new_log_str = "ftp-{} ✓".format(ftp_server['version'])
            self.replace_log(log_str, new_log_str, "restore")
            ftp_server["restore_status"] = 2
            ftp_server["msg"] = None
            self.update_restore_data_list(timestamp, restore_data)
            return

        result = public.ExecShell(
            f"cd /www/server/panel/install && wget -O pureftpd.sh {OFFICIAL_URL}/install/0/pureftpd.sh && bash pureftpd.sh install"
        )
        public.ExecShell("rm -f /www/server/pure-ftpd/etc/pureftpd.passwd")
        public.ExecShell("rm -f /www/server/pure-ftpd/etc/pureftpd.pdb")
        if not os.path.exists("/www/server/pure-ftpd/bin/pure-pw"):
            combined_output = (result[0] + result[1]).splitlines()
            err_msg = '\n'.join(combined_output[-10:])
            new_log_str = public.lang(
                "ftp-{} ✗ Installation failed Reason: {} \nPlease try to reinstall ftp in the software store after the restore task ends").format(
                ftp_server['version'], err_msg)
            self.replace_log(log_str, new_log_str, "restore")
            ftp_server["restore_status"] = 3
            ftp_server["msg"] = err_msg
        else:
            new_log_str = "ftp-{} ✓".format(ftp_server['version'])
            self.replace_log(log_str, new_log_str, "restore")
            ftp_server["restore_status"] = 2
            ftp_server["msg"] = None

        self.update_restore_data_list(timestamp, restore_data)

        import ftp
        if ftp_server['port'] != 21:
            with app.app_context():
                args = public.dict_obj()
                args.port = str(ftp_server['port'])
                ftp.ftp().setPort(args)

    def restore_env(self, timestamp):
        self.print_log("==================================", "restore")
        self.print_log(public.lang("Start restoring panel running environment"), "restore")
        self.print_log(public.lang("Will skip installation if the same environment exists"), "restore")
        restore_data = self.get_restore_data_list(timestamp)
        self.update_restore_data_list(timestamp, restore_data)

        soft_json_data = restore_data['data_list']['soft']
        try:
            if soft_json_data['web_server']:
                self.install_web_server(timestamp)
        except Exception as e:
            import traceback
            public.print_log(traceback.format_exc())
            public.print_log("Error installing web server: {}".format(str(e)))
            pass

        try:
            if soft_json_data['php_server']:
                self.install_php_server(timestamp)
        except Exception as e:
            import traceback
            public.print_log(traceback.format_exc())
            public.print_log("Error installing PHP server: {}".format(str(e)))
            pass

        try:
            if soft_json_data['mysql_server']:
                self.install_mysql_server(timestamp)
        except Exception as e:
            import traceback
            public.print_log(traceback.format_exc())
            public.print_log("Error installing MySQL server: {}".format(str(e)))
            pass

        try:
            if soft_json_data['ftp_server']:
                self.install_ftp_server(timestamp)
        except Exception as e:
            import traceback
            public.print_log(traceback.format_exc())
            public.print_log("Error installing FTP server: {}".format(str(e)))
            pass

        # try:
        #     if soft_json_data['node_list']:
        #         self.install_node(timestamp)
        # except Exception as e:
        #     import traceback
        #     public.print_log(traceback.format_exc())
        #     public.print_log("Error installing Node.js: {}".format(str(e)))
        #     pass

        try:
            if soft_json_data['redis_server']:
                self.install_redis_server(timestamp)
        except Exception as e:
            import traceback
            public.print_log(traceback.format_exc())
            public.print_log("Error installing Redis server: {}".format(str(e)))
            pass

        try:
            if soft_json_data['memcached_server']:
                self.install_memcached_server(timestamp)
        except Exception as e:
            import traceback
            public.print_log(traceback.format_exc())
            public.print_log("Error installing Memcached server: {}".format(str(e)))
            pass

        try:
            if soft_json_data['mongodb_server']:
                self.install_mongodb_server(timestamp)
        except Exception as e:
            import traceback
            public.print_log(traceback.format_exc())
            public.print_log("Error installing MongoDB server: {}".format(str(e)))
            pass

        try:
            if soft_json_data['pgsql_server']:
                self.install_pgsql_server(timestamp)
        except Exception as e:
            import traceback
            public.print_log(traceback.format_exc())
            public.print_log("Error installing PostgreSQL server: {}".format(str(e)))
            pass

        try:
            if soft_json_data['phpmyadmin_version']:
                self.install_phpmyadmin(timestamp)
        except Exception as e:
            import traceback
            public.print_log(traceback.format_exc())
            public.print_log("Error installing phpMyAdmin: {}".format(str(e)))
            pass


if __name__ == '__main__':
    # 获取命令行参数
    if len(sys.argv) < 2:
        print("Usage: btpython backup_manager.py <method> <timestamp>")
        sys.exit(1)
    method_name = sys.argv[1]  # 方法名  p
    timestamp = sys.argv[2]
    soft_manager = SoftModule()  # 实例化对象
    if hasattr(soft_manager, method_name):  # 检查方法是否存在
        method = getattr(soft_manager, method_name)  # 获取方法
        method(timestamp)  # 调用方法
    else:
        print(f"Error: {public.lang('Method')} '{method_name}' {public.lang('does not exist')}")
