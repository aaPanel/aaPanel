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
import shutil
import sys
import time
import warnings

if "/www/server/panel/class" not in sys.path:
    sys.path.insert(0, "/www/server/panel/class")
if "/www/server/panel/class_v2" not in sys.path:
    sys.path.insert(0, "/www/server/panel/class_v2")
if "/www/server/panel" not in sys.path:
    sys.path.insert(0, "/www/server/panel")

import public
from public.hook_import import hook_import

hook_import()
from wp_toolkit import wpbackup
import db
from BTPanel import app
import panel_site_v2 as panelSite
from mod.project.backup_restore.data_manager import DataManager

warnings.filterwarnings("ignore", category=SyntaxWarning)


class SiteModule(DataManager):
    def __init__(self):
        super().__init__()
        self.base_path = '/www/backup/backup_restore'
        self.bakcup_task_json = self.base_path + '/backup_task.json'
        self.site_dir_auth_path = "/www/server/panel/data/site_dir_auth.json"
        self.redirect_conf_path = "/www/server/panel/data/redirect.conf"
        self.proxy_conf_path = "/www/server/panel/data/proxyfile.json"

    @staticmethod
    def copy_directory(src: str, dst: str, overwrite: bool = False) -> None:
        """
        site 复制文件夹
        src:   源路径
        dst:   目标路径
        overwrite:  是否覆盖
        """
        if not src or not dst:
            return
        if src == dst:
            return
        if isinstance(overwrite, int):
            overwrite = False if overwrite == 0 else True

        def _copy2(src_file: str, dst_file: str):
            if overwrite or not os.path.exists(dst_file):
                try:
                    shutil.copy2(src_file, dst_file)
                except:
                    try:
                        public.ExecShell("chattr -i {}".format(dst_file))
                        shutil.copy2(src_file, dst_file)
                    except:
                        pass

        # 如果源路径不存在，直接返回
        if not os.path.exists(src):
            return

        # 确保目标目录存在
        if not os.path.exists(dst):
            os.makedirs(dst, 0o755, exist_ok=True)

        # 复制源目录下的所有内容到目标目录
        for item in os.listdir(src):
            src_item = os.path.join(src, item)
            dst_item = os.path.join(dst, item)

            if os.path.isdir(src_item):
                # 递归调用自身来复制子目录内容
                SiteModule.copy_directory(src_item, dst_item, overwrite)
            else:
                # 复制文件
                _copy2(src_item, dst_item)

    @staticmethod
    def _db_cp(source_db: str, target_db: str, tables: list = None) -> None:
        """
        指定表复制到新db中
        source_db: 源db路径
        target_db: 目标db路径
        tables:    要复制的表列表, None时复制所有
        """
        if not source_db:
            return
        source_db = f"'{source_db}'"
        target_db = f"'{target_db}'"
        if not tables:
            public.ExecShell(f"sqlite3 {source_db} .dump | sqlite3 {target_db}")
            return

        for table in tables:
            public.ExecShell(f"sqlite3 {target_db} 'DROP TABLE IF EXISTS {table};'")

        tables_for_dump = " ".join(tables)
        tables_cmd = f"sqlite3 {source_db} '.dump {tables_for_dump}'"

        tables_for_sql_in = ", ".join([f"'{t}'" for t in tables])
        triggers_cmd = f"""sqlite3 {source_db} \"
        SELECT sql || ';' FROM sqlite_master WHERE type='trigger' AND tbl_name IN ({tables_for_sql_in}) AND sql IS NOT NULL;\"
        """
        res_cmd = f"({tables_cmd}; {triggers_cmd}) | sqlite3 {target_db}"
        public.ExecShell(res_cmd)

        public.ExecShell(f"sqlite3 {target_db} '.dump' | sqlite3 {target_db}")

    @staticmethod
    def chmod_dir_file(path: str, dir_mode: int = 0o755, file_mode: int = 0o644):
        if not path:
            return
        for root, dirs, files in os.walk(path):
            for d in dirs:
                try:
                    os.chmod(os.path.join(root, d), dir_mode)
                except:
                    continue
            for f in files:
                try:
                    os.chmod(os.path.join(root, f), file_mode)
                except:
                    continue
        if os.path.isdir(path):
            try:
                os.chmod(path, dir_mode)
            except:
                pass
        elif os.path.isfile(path):
            try:
                os.chmod(path, file_mode)
            except:
                pass

    def get_site_backup_conf(self, timestamp=None):
        # todo node, 待优化
        site_data = public.M('sites').where("project_type != ?", "Node").field('name,path,project_type,id,ps').select()
        domian_data = public.M('domain').field('name,id,pid,id,port').select()
        wp_onekey = public.M('wordpress_onekey').field('s_id,prefix,user,pass').select()

        filtered_sites = [site for site in site_data]
        filtered_domain = [name for name in domian_data]

        pid_map = {}
        for domain in filtered_domain:
            pid = domain["pid"]
            if pid not in pid_map:
                pid_map[pid] = []

            pid_map[pid].append(
                {
                    "name": domain["name"],
                    "port": domain["port"],
                }
            )

        for site in filtered_sites:
            # domain
            site_id = site["id"]
            if site_id in pid_map:
                site["domains"] = pid_map[site_id]

            # wp prefix
            hit = False
            for p in wp_onekey:
                try: # wp may be not exist
                    if p["s_id"] == site["id"] and p.get('prefix'):
                        site["wp_onekey"] = {
                            "prefix": p['prefix'],
                            "user": p.get('user', ''),
                            "pass": p.get('pass', ''),
                        }
                        hit = True
                        break
                except:
                    pass
            if not hit:
                site["wp_onekey"] = {}

            site["data_type"] = "backup"
            site["status"] = 0
            site["msg"] = None

        return filtered_sites

    def backup_site_data(self, timestamp):
        data_list = self.get_backup_data_list(timestamp)
        if not data_list:
            return None
        data_backup_path = data_list['backup_path']
        site_backup_path = data_backup_path + '/site/'
        if not os.path.exists(site_backup_path):
            public.ExecShell('mkdir -p {}'.format(site_backup_path))
        self.print_log("====================================================", 'backup')
        self.print_log(public.lang("Start backing up site data"), 'backup')

        self.backup_site_config(site_backup_path)

        site_sql = db.Sql()
        site_sql.table('sites')
        domain_sql = db.Sql()
        domain_sql.table('domain')

        for site in data_list['data_list']['site']:
            # 备份db数据库数据
            site_id = site['id']
            site_db_record = site_sql.where('id=?', (site_id,)).find()
            site['site_db_record'] = site_db_record

            # 备份网站数据
            site['path'] = str(site['path']).rstrip('/')
            last_path = os.path.basename(site['path'])
            site["last_path"] = last_path
            site_path = site_backup_path + last_path

            if site["project_type"] == "PHP":
                try:
                    site["php_ver"] = panelSite.panelSite().GetSitePHPVersion(
                        public.to_dict_obj({'siteName': site['name']})
                    )['phpversion']
                except:
                    site["php_ver"] = None

            site['status'] = 1
            log_str = public.lang("Backing up {} project: {}").format(site['project_type'], site['name'])
            self.print_log(log_str, "backup")
            self.update_backup_data_list(timestamp, data_list)

            # 备份网站项目
            public.ExecShell("cp -rpa {} {}".format(site['path'], site_path))
            site_zip = site_backup_path + last_path + ".zip"
            public.ExecShell("cd {} && zip -r {}.zip {}".format(site_backup_path, last_path, last_path))
            if os.path.exists(site_zip):
                site_zip_size = public.ExecShell("du -sb {}".format(site_zip))[0].split("\t")[0]
                site['data_file_name'] = site_zip
                site['size'] = site_zip_size
                site['zip_sha256'] = self.get_file_sha256(site_zip)

            # 创建配置文件备份目录
            webserver_conf_path = ["apache", "cert", "config", "nginx", "open_basedir",
                                   "openlitespeed", "other_php", "rewrite", "ssl",
                                   "ssl_saved", "template", "tomcat"]
            conf_backup_path = site_backup_path + site['name'] + "_conf/"
            public.ExecShell(f"mkdir -p '{conf_backup_path}'")

            # 创建子目录
            for wpath in webserver_conf_path:
                web_conf_backup_path = conf_backup_path + wpath
                public.ExecShell(f"mkdir -p '{web_conf_backup_path}'")

            # 备份网站配置文件
            self.backup_web_conf(site['name'], conf_backup_path)

            # 打包网站配置文件
            site_name = site['name']
            site_conf_zip = site_backup_path + site_name + "_conf.zip"
            public.ExecShell("cd {} && zip -r {}_conf.zip {}_conf".format(site_backup_path, site_name, site_name))
            if os.path.exists(site_conf_zip):
                site['conf_file_name'] = site_conf_zip
                site['zip_sha256'] = self.get_file_sha256(site_conf_zip)
                site['conf_sha256'] = self.get_file_sha256(site_conf_zip)

            site['status'] = 2
            format_backup_file_size = self.format_size(int(site['size']))
            new_log_str = public.lang("{} project {} ✓ ({})").format(
                site['project_type'], site['name'], format_backup_file_size
            )
            self.replace_log(log_str, new_log_str, 'backup')

            self.update_backup_data_list(timestamp, data_list)

        self.print_log(public.lang("Site data backup completed"), 'backup')

    def backup_site_config(self, site_backup_path):
        public.ExecShell(
            "\cp -rpa /www/server/panel/data/default.db {site_backup_path}default.db".format(
                site_backup_path=site_backup_path
            )
        )

        # 备份加密访问配置文件
        if os.path.exists("/www/server/panel/data/site_dir_auth.json"):
            public.ExecShell(
                "\cp -rpa /www/server/panel/data/site_dir_auth.json {site_backup_path}site_dir_auth.json".format(
                    site_backup_path=site_backup_path
                )
            )
        # 备份加密密码
        if os.path.exists("/www/server/pass/"):
            public.ExecShell(
                "\cp -rpa /www/server/pass/ {site_backup_path}pass/".format(
                    site_backup_path=site_backup_path
                )
            )

        # 备份反代配置
        if os.path.exists("/www/server/proxy_project/sites"):
            public.ExecShell("mkdir -p {site_backup_path}proxy_project/".format(site_backup_path=site_backup_path))
            public.ExecShell(
                "\cp -rpa /www/server/proxy_project/sites {site_backup_path}proxy_project/sites/".format(
                    site_backup_path=site_backup_path
                )
            )

        # 备份重定向配置
        if os.path.exists("/www/server/panel/data/redirect.conf"):
            public.ExecShell(
                "\cp -rpa /www/server/panel/data/redirect.conf {site_backup_path}redirect.conf".format(
                    site_backup_path=site_backup_path
                )
            )

        if os.path.exists("/www/server/panel/data/proxyfile.json"):
            public.ExecShell(
                "\cp -rpa /www/server/panel/data/proxyfile.json {site_backup_path}proxyfile.json".format(
                    site_backup_path=site_backup_path
                )
            )

        # 备份wp加速配置文件
        if os.path.exists("/www/server/nginx/conf/"):
            nginx_conf_list = os.listdir("/www/server/nginx/conf/")
            for nginx_conf_name in nginx_conf_list:
                if "wpfastcgi" in nginx_conf_name:
                    public.ExecShell(
                        "\cp -rpa /www/server/nginx/conf/{nginx_conf_name} {site_backup_path}{nginx_conf_name}".format(
                            nginx_conf_name=nginx_conf_name, site_backup_path=site_backup_path
                        )
                    )

        # 备份well-known文件
        if os.path.exists("/www/server/panel/vhost/nginx/well-known"):
            public.ExecShell(
                "\cp -rpa /www/server/panel/vhost/nginx/well-known {site_backup_path}/well-known".format(
                    site_backup_path=site_backup_path
                )
            )

        public.ExecShell("mkdir -p {site_backup_path}/monitor_conf/".format(site_backup_path=site_backup_path))
        public.ExecShell(
            "\cp -rpa /www/server/panel/vhost/nginx/0.monitor*.conf {site_backup_path}/monitor_conf/".format(
                site_backup_path=site_backup_path
            )
        )

    def restore_site_config(self, backup_path):
        default_db_file = backup_path + "default.db"
        dir_auth_file = backup_path + "site_dir_auth.json"
        pass_path = backup_path + "pass"
        proxy_project_path = backup_path + "proxy_project"
        redirect_file = backup_path + "redirect.conf"
        proxyfile_file = backup_path + "proxyfile.json"
        if os.path.exists(default_db_file) and self.overwrite:
            panel_current = public.S("users").find()
            public.ExecShell(f"\cp  -rpa {default_db_file} /www/server/panel/data/default.db")
            os.chmod("/www/server/panel/data/default.db", 0o600)
            if "id" in panel_current:
                del panel_current["id"]
            public.S("users").where("id=?", (1,)).update(panel_current)
        if os.path.exists(pass_path):
            self.copy_directory(
                src=pass_path,
                dst="/www/server/pass",
                overwrite=self.overwrite,
            )
            self.chmod_dir_file("/www/server/pass", file_mode=0o644)

        if os.path.exists(proxy_project_path):
            target = "/www/server/proxy_project"
            self.copy_directory(
                src=proxy_project_path,
                dst=target,
                overwrite=self.overwrite,
            )
            self.chmod_dir_file(target, file_mode=0o644)

        if os.path.exists(dir_auth_file):
            target = "/www/server/panel/data/site_dir_auth.json"
            if not os.path.exists(target) or self.overwrite:
                public.ExecShell(f"\cp  -rpa {dir_auth_file} /www/server/panel/data/site_dir_auth.json")
                self.chmod_dir_file(target, file_mode=0o600)

        if os.path.exists(redirect_file):
            target = "/www/server/panel/data/redirect.conf"
            if not os.path.exists(target) or self.overwrite:
                public.ExecShell(f"\cp  -rpa {redirect_file} /www/server/panel/data/redirect.conf")
                self.chmod_dir_file(target, file_mode=0o600)

        if os.path.exists(proxyfile_file):
            target = "/www/server/panel/data/proxyfile.json"
            if not os.path.exists(target) or self.overwrite:
                public.ExecShell(f"\cp  -rpa {proxyfile_file} /www/server/panel/data/proxyfile.json")
                self.chmod_dir_file(target, file_mode=0o600)

        public.ExecShell(f"\cp -rpa {backup_path}/*wpfastcgi.conf /www/server/nginx/conf/")
        self.chmod_dir_file("/www/server/nginx/conf", file_mode=0o644)

        if os.path.exists(backup_path + "well-known"):
            target = "/www/server/panel/vhost/nginx/well-known"
            if not os.path.exists(target):
                public.ExecShell(f"mkdir -p {target}")
            public.ExecShell(f"\cp -rpa {backup_path}well-known/* /www/server/panel/vhost/nginx/well-known/")
            self.chmod_dir_file(target, dir_mode=0o600, file_mode=0o600)

        public.ExecShell(f"\cp -rpa {backup_path}monitor_conf/* /www/server/panel/vhost/nginx/")
        self.chmod_dir_file("/www/server/panel/vhost/nginx", dir_mode=0o600, file_mode=0o600)

    def restore_site_python_env(self, timestamp):
        self.print_log("================================================", "restore")
        self.print_log(public.lang("Starting to restore site Python dependencies..."), 'restore')
        restore_data = self.get_restore_data_list(timestamp)
        site_data = restore_data['data_list']['site']
        for site in site_data:
            if site['project_type'] == 'Python':
                python_site_config = site['site_db_record']['project_config']
                requirement_path = json.loads(python_site_config)['requirement_path']
                vpath = json.loads(python_site_config)['vpath']
                if requirement_path:
                    pip3_path = vpath + "/bin/pip3"
                    pip2_path = vpath + "/bin/pip2"
                    pip_install_cmd = None
                    if os.path.exists(pip3_path):
                        pip_install_cmd = "{} install -r {}".format(pip3_path, requirement_path)
                    elif os.path.exists(pip2_path):
                        pip_install_cmd = "{} install -r {}".format(pip2_path, requirement_path)

                    if pip_install_cmd:
                        public.ExecShell(pip_install_cmd)
        self.print_log(public.lang("Site Python dependencies restoration completed"), 'restore')

    def backup_web_conf(self, site_name: str, conf_backup_path: str) -> None:
        """备份网站配置文件
        
        Args:
            site_name: 网站名称
            conf_backup_path: 配置文件备份路径
        """
        # 定义需要备份的配置文件和路径映射
        conf_paths = {
            'cert': "/www/server/panel/vhost/cert/{site_name}".format(site_name=site_name),
            'rewrite': "/www/server/panel/vhost/rewrite/{site_name}.conf".format(site_name=site_name),
            'nginx': {
                'main': "/www/server/panel/vhost/nginx/{site_name}.conf".format(site_name=site_name),
                'redirect': "/www/server/panel/vhost/nginx/redirect/{site_name}".format(site_name=site_name),
                'proxy': "/www/server/panel/vhost/nginx/proxy/{site_name}".format(site_name=site_name),
                'dir_auth': "/www/server/panel/vhost/nginx/dir_auth/{site_name}".format(site_name=site_name)
            },
            'apache': {
                'main': "/www/server/panel/vhost/apache/{site_name}.conf".format(site_name=site_name),
                'redirect': "/www/server/panel/vhost/apache/redirect/{site_name}".format(site_name=site_name),
                'proxy': "/www/server/panel/vhost/apache/proxy/{site_name}".format(site_name=site_name),
                'dir_auth': "/www/server/panel/vhost/apache/dir_auth/{site_name}".format(site_name=site_name)
            },

            'openlitespeed': {
                'main': '/www/server/panel/vhost/openlitespeed',
                'detail': '/www/server/panel/vhost/openlitespeed/detail',
                'listen': '/www/server/panel/vhost/openlitespeed/listen',
                'ssl': '/www/server/panel/vhost/openlitespeed/detail/ssl',
            },
        }

        # 备份证书
        if os.path.exists(conf_paths['cert']):
            public.ExecShell(f"mkdir -p {conf_backup_path}cert/")
            public.ExecShell(f"\cp -rpa {conf_paths['cert']} {conf_backup_path}cert/")

        # 备份伪静态
        if os.path.exists(conf_paths['rewrite']):
            public.ExecShell(f"\cp -rpa {conf_paths['rewrite']} {conf_backup_path}rewrite")

        rewrite_file_list = os.listdir("/www/server/panel/vhost/rewrite/")
        for rewrite_file in rewrite_file_list:
            if rewrite_file.endswith(".conf"):
                if site_name in rewrite_file:
                    public.ExecShell(
                        f"\cp -rpa /www/server/panel/vhost/rewrite/{rewrite_file} {conf_backup_path}rewrite"
                    )

        # 备份nginx配置
        nginx_paths = conf_paths['nginx']
        if os.path.exists(nginx_paths['main']):
            public.ExecShell(f"\cp -rpa {nginx_paths['main']} {conf_backup_path}nginx/")

        if not os.path.exists(nginx_paths['main']):
            web_conf_list = os.listdir("/www/server/panel/vhost/nginx/")
            for web_conf_name in web_conf_list:
                if web_conf_name.endswith(".conf"):
                    if site_name in web_conf_name:
                        public.ExecShell(
                            f"\cp -rpa /www/server/panel/vhost/nginx/{web_conf_name} {conf_backup_path}nginx/"
                        )

        if os.path.exists(nginx_paths['redirect']):
            public.ExecShell(f"mkdir -p {conf_backup_path}nginx/redirect/{site_name}/")
            public.ExecShell(f"\cp -rpa {nginx_paths['redirect']}/* {conf_backup_path}nginx/redirect/{site_name}/")

        if os.path.exists(nginx_paths['proxy']):
            public.ExecShell(f"mkdir -p {conf_backup_path}nginx/proxy/{site_name}/")
            public.ExecShell(f"\cp -rpa {nginx_paths['proxy']}/* {conf_backup_path}nginx/proxy/{site_name}/")

        if os.path.exists(nginx_paths['dir_auth']):
            public.ExecShell(f"mkdir -p {conf_backup_path}nginx/dir_auth/{site_name}/")
            public.ExecShell(f"\cp -rpa {nginx_paths['dir_auth']}/* {conf_backup_path}nginx/dir_auth/{site_name}/")

        # 备份apache配置
        apache_paths = conf_paths['apache']
        if os.path.exists(apache_paths['main']):
            public.ExecShell(f"\cp -rpa {apache_paths['main']} {conf_backup_path}apache/")

        if not os.path.exists(apache_paths['main']):
            web_conf_list = os.listdir("/www/server/panel/vhost/apache/")
            for web_conf_name in web_conf_list:
                if web_conf_name.endswith(".conf"):
                    if site_name in web_conf_name:
                        public.ExecShell(
                            f"\cp -rpa /www/server/panel/vhost/apache/{web_conf_name} {conf_backup_path}apache/"
                        )

        if os.path.exists(apache_paths['redirect']):
            public.ExecShell(f"mkdir -p {conf_backup_path}apache/redirect/{site_name}/")
            public.ExecShell(f"\cp -rpa {apache_paths['redirect']}/* {conf_backup_path}apache/redirect/{site_name}/")

        if os.path.exists(apache_paths['proxy']):
            public.ExecShell(f"mkdir -p {conf_backup_path}apache/proxy/{site_name}/")
            public.ExecShell(f"\cp -rpa {apache_paths['proxy']}/* {conf_backup_path}apache/proxy/{site_name}/")

        if os.path.exists(apache_paths['dir_auth']):
            public.ExecShell(f"mkdir -p {conf_backup_path}apache/dir_auth/{site_name}/")
            public.ExecShell(f"\cp -rpa {apache_paths['dir_auth']}/* {conf_backup_path}apache/dir_auth/{site_name}/")

        # 备份openlitespeed配置
        ols_paths = conf_paths['openlitespeed']
        if os.path.exists(ols_paths['main']):
            for web_conf_name in os.listdir(ols_paths['main']):
                if site_name in web_conf_name:
                    public.ExecShell(
                        f"\cp -rpa /www/server/panel/vhost/openlitespeed/{web_conf_name} {conf_backup_path}openlitespeed/"
                    )

        if os.path.exists(conf_paths['openlitespeed']['detail']):
            public.ExecShell(f"mkdir -p {conf_backup_path}openlitespeed/detail")
            for detail in os.listdir(conf_paths['openlitespeed']['detail']):
                if site_name in detail:
                    public.ExecShell(
                        f"\cp -rpa {ols_paths['main']}/detail/{detail} {conf_backup_path}openlitespeed/detail/"
                    )

        if os.path.exists(conf_paths['openlitespeed']['listen']):
            public.ExecShell(
                f"cp -rpa {conf_paths['openlitespeed']['listen']} {conf_backup_path}openlitespeed/listen"
            )

        if os.path.exists(conf_paths['openlitespeed']['ssl']):
            public.ExecShell(f"mkdir -p {conf_backup_path}openlitespeed/detail/ssl")
            for ssl in os.listdir(conf_paths['openlitespeed']['ssl']):
                if site_name in ssl:
                    public.ExecShell(
                        f"cp -rpa {conf_paths['openlitespeed']['ssl']}/{ssl} {conf_backup_path}openlitespeed/detail/ssl/{ssl}"
                    )

    def restore_web_conf(self, site_name: str, conf_backup_path: str) -> None:
        """还原网站配置文件
        
        Args:
            site_name: 网站名称
            conf_backup_path: 配置文件备份路径
        """
        # 定义需要还原的配置文件和路径映射
        conf_paths = {
            'cert': "/www/server/panel/vhost/cert/{site_name}".format(site_name=site_name),
            'rewrite': "/www/server/panel/vhost/rewrite/{site_name}.conf".format(site_name=site_name),
            'nginx': {
                'main': "/www/server/panel/vhost/nginx/{site_name}.conf".format(site_name=site_name),
                'redirect': "/www/server/panel/vhost/nginx/redirect/{site_name}".format(site_name=site_name),
                'proxy': "/www/server/panel/vhost/nginx/proxy/{site_name}".format(site_name=site_name)
            },
            'apache': {
                'main': "/www/server/panel/vhost/apache/{site_name}.conf".format(site_name=site_name),
                'redirect': "/www/server/panel/vhost/apache/redirect/{site_name}".format(site_name=site_name),
                'proxy': "/www/server/panel/vhost/apache/proxy/{site_name}".format(site_name=site_name)
            },
            'openlitespeed': {
                'main': '/www/server/panel/vhost/openlitespeed',
                'detail': '/www/server/panel/vhost/openlitespeed/detail',
                'listen': '/www/server/panel/vhost/openlitespeed/listen',
                'ssl': '/www/server/panel/vhost/openlitespeed/detail/ssl',
            },
        }

        # 还原证书
        if os.path.exists(f"{conf_backup_path}cert"):
            public.ExecShell(f"\cp -rpa {conf_backup_path}cert {conf_paths['cert']}")

        # 还原伪静态
        if os.path.exists(f"{conf_backup_path}rewrite"):
            public.ExecShell(f"\cp -rpa {conf_backup_path}rewrite {conf_paths['rewrite']}")

        # 还原nginx配置
        if os.path.exists(f"{conf_backup_path}nginx"):
            public.ExecShell(f"\cp -rpa {conf_backup_path}nginx {conf_paths['nginx']['main']}")
        if os.path.exists(f"{conf_backup_path}nginx/redirect"):
            public.ExecShell(f"\cp -rpa {conf_backup_path}nginx/redirect {conf_paths['nginx']['redirect']}")
        if os.path.exists(f"{conf_backup_path}nginx/proxy"):
            public.ExecShell(f"\cp -rpa {conf_backup_path}nginx/proxy {conf_paths['nginx']['proxy']}")

        # 还原apache配置
        if os.path.exists(f"{conf_backup_path}apache"):
            public.ExecShell(f"\cp -rpa {conf_backup_path}apache {conf_paths['apache']['main']}")
        if os.path.exists(f"{conf_backup_path}apache/redirect"):
            public.ExecShell(f"\cp -rpa {conf_backup_path}apache/redirect {conf_paths['apache']['redirect']}")
        if os.path.exists(f"{conf_backup_path}apache/proxy"):
            public.ExecShell(f"\cp -rpa {conf_backup_path}apache/proxy {conf_paths['apache']['proxy']}")

        # 还原openlitespeed配置
        if os.path.exists(f"{conf_backup_path}openlitespeed"):
            for web_cf_name in os.listdir(f"{conf_backup_path}openlitespeed"):
                if site_name in web_cf_name:
                    public.ExecShell(
                        f"\cp -rpa {conf_backup_path}openlitespeed/{web_cf_name} {conf_paths['openlitespeed']['main']}/{web_cf_name}"
                    )

            detail_path = f"{conf_backup_path}openlitespeed/detail"
            if os.path.exists(detail_path):
                if not os.path.exists(conf_paths['openlitespeed']['detail']):
                    public.ExecShell(f"mkdir -p {conf_paths['openlitespeed']['detail']}")
                for detail in os.listdir(detail_path):
                    if site_name in detail:
                        public.ExecShell(
                            f"\cp -rpa {detail_path}/{detail} {conf_paths['openlitespeed']['detail']}/{detail}"
                        )

            listen_path = f"{conf_backup_path}openlitespeed/listen"
            if os.path.exists(listen_path):
                public.ExecShell(
                    f"\cp -rpa {listen_path} {conf_paths['openlitespeed']['listen']}/listen"
                )

            ssl_path = f"{conf_backup_path}openlitespeed/detail/ssl"
            if os.path.exists(ssl_path):
                if not os.path.exists(conf_paths['openlitespeed']['ssl']):
                    public.ExecShell(f"mkdir -p {conf_paths['openlitespeed']['ssl']}")
                for ssl in os.listdir(ssl_path):
                    if site_name in ssl:
                        public.ExecShell(
                            f"\cp -rpa {ssl_path}/{ssl} {conf_paths['openlitespeed']['ssl']}/{ssl}"
                        )

    def _restore_site_db_data(self, site_db_record: dict) -> int:
        sql = db.Sql()
        sql.table('sites')
        if 'id' in site_db_record:
            del site_db_record['id']
        # SQL关键字字段
        if 'index' in site_db_record:
            del site_db_record['index']
        if_exist = sql.where(
            'name=? AND project_type=?',
            (site_db_record['name'], site_db_record['project_type'])
        ).find()
        if if_exist:
            return if_exist['id']

        # insert db record
        try:
            new_id = sql.insert(site_db_record)
            return new_id
        except Exception as e:
            raise public.lang("Site database insert failed: {}").format(str(e))

    def _restore_site_domian_db_data(self, pid: int, domains: list) -> None:
        domain_sql = db.Sql()
        domain_sql.table('domain')
        for domain in domains:
            try:
                if not domain_sql.where('name=?', (domain['name'],)).count():
                    domain_sql.add(
                        'pid, name, port, addtime',
                        (pid, domain['name'], int(domain['port']), public.getDate())
                    )
            except Exception as e:
                public.print_log("Domain database insert failed: {}".format(str(e)))
                continue

    def _backup_site(self, site: dict, backupPath: str) -> None:
        try:
            if site.get("project_type", "").lower() == "php":
                find = public.M('sites').where("id=?", (site['id'],)).field('name,path,id').find()
                fileName = find['name'] + '_' + time.strftime(
                    '%Y%m%d_%H%M%S', time.localtime()
                ) + '.zip'
                zipName = backupPath + '/' + fileName
                if not (os.path.exists(backupPath)):
                    os.makedirs(backupPath)
                tmps = '/tmp/panelExec.log'
                execStr = f"cd '{find['path']}' && zip '{zipName}' . -x .user.ini > {tmps} 2>&1"
                public.ExecShell(execStr)
                public.M('backup').add(
                    'type,name,pid,filename,size,addtime',
                    (0, fileName, find['id'], zipName, 0, public.getDate())
                )
            elif "wp" in site.get("project_type", "").lower():
                bak_obj = wpbackup(int(site['id']))
                bak_obj.backup_full()
        except:
            pass

    def restore_site_data(self, timestamp: str) -> None:
        """还原站点数据
        Args:
            timestamp: 备份时间戳
        """
        restore_data = self.get_restore_data_list(timestamp)
        site_backup_path = self.base_path + "/{timestamp}_backup/site/".format(timestamp=timestamp)
        # 还原site环境配置, 全局配置
        self.restore_site_config(site_backup_path)

        if not os.path.exists(site_backup_path):
            self.print_log(public.lang("Site backup directory does not exist: {}").format(site_backup_path), 'restore')
            return
        self.print_log("====================================================", "restore")
        self.print_log(public.lang("Start restoring site data"), 'restore')

        backupPath = public.M('config').where('id=?', (1,)).getField('backup_path')
        backupPath = backupPath + '/site/' if backupPath else "/www/backup/site/"
        with app.app_context():
            for site in restore_data['data_list']['site']:
                log_str = public.lang("Restoring {} project: {}").format(site.get("project_type"), site.get("name"))
                try:
                    site_name = site['name']
                    site['restore_status'] = 1
                    self.update_restore_data_list(timestamp, restore_data)
                    self.print_log(log_str, 'restore')
                    if self.overwrite:
                        # site backup if overwrite
                        self._backup_site(site, backupPath)

                    # data
                    if not self.overwrite and 'site_db_record' in site:
                        site_id = self._restore_site_db_data(site['site_db_record'])
                        if site_id and 'domains' in site:
                            # 还原域名记录
                            self._restore_site_domian_db_data(site_id, site['domains'])

                    # site file
                    site_path = str(site['path']).rstrip('/')
                    last_path: str = os.path.basename(site_path) if site['last_path'] == '' else site['last_path']  # site name
                    # site abs path
                    site_zip = site_backup_path + last_path + ".zip"

                    if os.path.exists(site_zip):
                        public.ExecShell(f"cd {site_backup_path} && unzip -o {last_path}.zip")

                    site_data_path = site_backup_path + last_path  # site unzip file
                    if os.path.exists(site_data_path):
                        site_parent_path = os.path.dirname(site_path)  # /www/wwwroot
                        if not os.path.exists(site_parent_path):
                            public.ExecShell("mkdir -p {}".format(site_parent_path))
                        public.ExecShell("chown -R www:www {}".format(site_parent_path))
                        public.ExecShell("chmod -R 755 {}".format(site_parent_path))

                        src_site = os.path.join(site_backup_path, last_path)
                        dst_site = os.path.join(site_parent_path, last_path)

                        public.print_log('copying site directory from {} to {}'.format(src_site, dst_site))

                        self.copy_directory(
                            src=src_site,
                            dst=dst_site,
                            overwrite=self.overwrite,
                        )
                        try:
                            shutil.rmtree(src_site)
                        except Exception as e:
                            public.print_log(public.lang("Failed to delete source site directory: {}").format(str(e)))

                        # makesure
                        public.ExecShell(f"chown -R www:www {dst_site}")
                        user_ini = dst_site + "/.user.ini"
                        if not os.path.exists(user_ini) or self.overwrite:
                            public.writeFile(user_ini, f"open_basedir={site_parent_path}/:/tmp/")
                        public.ExecShell("chmod 644 " + user_ini)
                        public.ExecShell("chown root:root " + user_ini)
                        public.ExecShell("chattr +i " + user_ini)

                    # site config
                    site_conf_zip = site_backup_path + site_name + "_conf.zip"
                    if os.path.exists(site_conf_zip):
                        public.ExecShell(
                            "cd {site_backup_path} && unzip -o {site_name}_conf.zip".format(
                                site_backup_path=site_backup_path, site_name=site_name
                            )
                        )
                        public.ExecShell(
                            "cd {site_backup_path} && \cp -rpa {site_name}_conf/*  /www/server/panel/vhost".format(
                                site_backup_path=site_backup_path, site_name=site_name
                            )
                        )

                    new_log_str = public.lang("{} project: {} ✓").format(site['project_type'], site['name'])
                    self.replace_log(log_str, new_log_str, 'restore')
                    site['restore_status'] = 2
                    self.update_restore_data_list(timestamp, restore_data)
                except Exception as e:
                    site['restore_status'] = 3
                    self.update_restore_data_list(timestamp, restore_data)
                    new_log_str = public.lang(f"{site['project_type']} project: {site['name']} Reason: {str(e)}")
                    self.replace_log(log_str, new_log_str, 'restore')
                    continue

        self.print_log(public.lang("Site data restoration completed"), 'restore')
        # 还原site 所有Python环境
        # self.restore_site_python_env(timestamp)

    def backup_site_dir_auth(self, site_name: str):
        if os.path.exists(self.site_dir_auth_path):
            site_dir_auth_data = json.loads(public.ReadFile(self.site_dir_auth_path))
            if site_name in site_dir_auth_data:
                result = {site_name: site_dir_auth_data[site_name]}
                return result
        return False

    def restore_site_dir_auth(self, site_name: str, backup_data_path: str):
        if os.path.exists(backup_data_path):
            dir_auth_backup_data = json.loads(public.ReadFile(backup_data_path))
            if os.path.exists(self.site_dir_auth_path):
                site_dir_auth_data = json.loads(public.ReadFile(self.site_dir_auth_path))
                site_dir_auth_data[site_name] = dir_auth_backup_data[site_name]
                public.WriteFile(self.site_dir_auth_path, json.dumps(site_dir_auth_data))

    def backup_dir_pass(self, site_name: str, backup_data_path: str):
        if os.path.exists(self.site_dir_auth_path):
            site_dir_auth_data = json.loads(public.ReadFile(self.site_dir_auth_path))
            if site_name in site_dir_auth_data:
                result = {site_name: site_dir_auth_data[site_name]}
                return result
        return {}

    def backup_redirect_conf(self, site_name: str):
        if os.path.exists(self.redirect_conf_path):
            redirect_conf_data = json.loads(public.ReadFile(self.redirect_conf_path))
            for item in redirect_conf_data:
                if site_name in item['sitename']:
                    return item
        return False

    def restore_redirect_conf(self, site_name: str, backup_data_path: str):
        if os.path.exists(backup_data_path):
            redirect_conf_data = json.loads(public.ReadFile(backup_data_path))
            local_redirect_conf_data = []
            if os.path.exists(self.redirect_conf_path):
                local_redirect_conf_data = json.loads(public.ReadFile(self.redirect_conf_path))
            data_exists = None
            for item in local_redirect_conf_data:
                if item['sitename'] == redirect_conf_data['sitename']:
                    data_exists = True
            if not data_exists:
                local_redirect_conf_data.append(redirect_conf_data)
            public.WriteFile(self.redirect_conf_path, json.dumps(local_redirect_conf_data))
        return False

    def backup_proxy_conf(self, site_name: str):
        if os.path.exists(self.proxy_conf_path):
            proxy_conf_data = json.loads(public.ReadFile(self.proxy_conf_path))
            for item in proxy_conf_data:
                if site_name in item['sitename']:
                    return item
        return False

    def restore_proxy_conf(self, site_name: str, backup_data_path: str):
        if os.path.exists(backup_data_path):
            proxy_conf_data = json.loads(public.ReadFile(backup_data_path))
            local_proxy_conf_data = []
            if os.path.exists(self.proxy_conf_path):
                local_proxy_conf_data = json.loads(public.ReadFile(self.proxy_conf_path))
            data_exists = None
            for item in local_proxy_conf_data:
                if item['sitename'] == proxy_conf_data['sitename']:
                    data_exists = True
            if not data_exists:
                local_proxy_conf_data.append(proxy_conf_data)
            public.WriteFile(self.proxy_conf_path, json.dumps(local_proxy_conf_data))
        return False


if __name__ == '__main__':
    # 获取命令行参数
    if len(sys.argv) < 3:
        print("Usage: btpython backup_manager.py <method> <timestamp>")
        sys.exit(1)
    method_name = sys.argv[1]  # 方法名
    timestamp = sys.argv[2]  # IP地址
    site_module = SiteModule()  # 实例化对象
    if hasattr(site_module, method_name):  # 检查方法是否存在
        method = getattr(site_module, method_name)  # 获取方法
        method(timestamp)  # 调用方法
    else:
        print(f"Error: Method '{method_name}' 'does not exist'")
