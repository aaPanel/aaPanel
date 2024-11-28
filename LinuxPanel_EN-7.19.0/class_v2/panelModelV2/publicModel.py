# coding: utf-8
# -------------------------------------------------------------------
# aaPanel
# -------------------------------------------------------------------
# Copyright (c) 2015-2099 aaPanel(www.aapanel.com) All rights reserved.
# -------------------------------------------------------------------
# Author: cjxin <cjxin@aapanel.com>
# -------------------------------------------------------------------

# 备份
# ------------------------------
import os, sys, re, json, shutil, psutil, time
from panelModelV2.base import panelBase
import public, panelTask
import config_v2 as config

try:
    from BTPanel import cache,session
except:pass

class main(panelBase):
    __table = 'task_list'
    # public.check_database_field("ssl_data.db","ssl_info")
    task_obj = panelTask.bt_task()

    def __init__(self):
        pass


    """
    @name 获取面板日志 
    """
    def get_update_logs(self,get):
        try:

            skey = 'panel_update_logs'
            res = cache.get(skey)
            if res:
                return public.return_message(0, 0, res)

            # res = public.httpPost('https://wafapi2.aapanel.com/api/getUpdateLogs?type=Linux',{})
            res = public.httpPost('https://wafapi2.aapanel.com/Api/getUpdateLogs?type=Linux',{})

            start_index = res.find('(') + 1
            end_index = res.rfind(')')
            json_data = res[start_index:end_index]

            res = json.loads(json_data)
            cache.set(skey,res,60)
        except:
            res = []

        return public.return_message(0, 0, res)

    def get_public_config(self, args):
        """
        @name 获取公共配置
        """
        _config_obj = config.config()
        data = _config_obj.get_config(args)

        data['task_list'] = self.task_obj.get_task_lists(args)
        data['task_count'] = public.M('tasks').where("status!=?", ('1',)).count()
        data['get_pd'] = self.get_pd(args)
        data['ipv6'] = ''
        if _config_obj.get_ipv6_listen(None): data['ipv6'] = 'checked'
        data['is_local'] = ''
        if public.is_local(): data['is_local'] = 'checked'

        if data['get_pd'] and data['get_pd'][2] != -1:
            time_diff = (data['get_pd'][2]-int(time.time())) % (365*86400)
            data['active_pro_time'] = int(time.time()) - (365*86400 - time_diff)
        else:
            data['active_pro_time'] = 0
        data['status_code'] = _config_obj.get_not_auth_status()
        if os.path.exists('/www/server/panel/config/api.json'):
            try:
                res = json.loads(public.readFile('/www/server/panel/config/api.json'))
                data['api'] = 'checked' if res['open'] else ''
            except:
                public.ExecShell('rm -f /www/server/panel/config/api.json')
                data['api'] = ''
        else:
            data['api'] = ''


        data['total'] = os.path.exists('/www/server/panel/plugin/total') or os.path.exists('/www/server/panel/plugin/monitor')
        data['disk_usage'] = public.get_disk_usage(public.get_panel_path())
        data['uid'] = ''
        if os.path.exists('/www/server/panel/data/userInfo.json'):
            res = public.readFile('/www/server/panel/data/userInfo.json')
            if res:
                try:
                    res = json.loads(res)
                    data['uid'] = res['uid']
                except:
                    pass
        return public.return_message(0, 0, data)


    # 获取公共配置（精简版）
    def get_public_config_simple(self, args):
        """
            @name 获取公共配置（精简版）
            @param args<dict_obj> 请求参数
            @return dict
        """
        data = {}
        data['task_count'] = public.M('tasks').where("status!=?", ('1',)).count()
        data['get_pd'] = self.get_pd(args)

        import panelSSL
        data['user_info'] = panelSSL.panelSSL().GetUserInfo(None)

        import system_v2 as system
        data['panel'] = system.system().GetPanelInfo()

        data["webname"] = public.GetConfigValue("title")

        data['menu_list'] = config.config().get_menu_list(args)['message']

        data['install_finished'] = os.path.exists('{}/data/install_finished.mark'.format(public.get_panel_path()))
        import breaking_through as breaking_through
        _breaking_through_obj = breaking_through.main()
        data['limit_login'] = _breaking_through_obj.get_login_limit()
        # 增加语言设置数据
        import config_v2
        lang = config_v2.config().get_language()
        data['language'] = lang['default']
        data['language_list'] = lang['languages']

        data['isPro'] = True if os.path.exists("/www/server/panel/data/panel_pro.pl") else False

        return public.return_message(0, 0, data)

    # 获取常用软件安装状态
    def get_public_config_setup(self, args):
        from BTPanel import session
        if 'config' not in session:
            session['config'] = public.M('config').where("id=?", ('1',)).field(
                'webserver,sites_path,backup_path,status,mysql_root').find()
        data = session['config']

        import system_v2 as system
        data.update(system.system().GetConcifInfo())

        if 'ftpPort' not in data:
            # 获取FTP端口
            if 'port' not in session:
                import re
                try:
                    file = public.GetConfigValue('setup_path') + '/pure-ftpd/etc/pure-ftpd.conf'
                    conf = public.readFile(file)
                    rep = r"\n#?\s*Bind\s+[0-9]+\.[0-9]+\.[0-9]+\.+[0-9]+,([0-9]+)"
                    port = re.search(rep, conf).groups()[0]
                except:
                    port = '21'
                session['port'] = port

            data['ftpPort'] = session['port']

        return public.return_message(0, 0, data)

    # 获取授权信息
    def get_pd(self, get):
        return public.get_pd(get)

    @staticmethod
    def set_backup_path(get):
        try:
            backup_path = get.backup_path.strip().rstrip("/")
        except AttributeError:
            return public.return_message(-1, 0, public.lang("The parameter is incorrect"))

        if not os.path.exists(backup_path):
            return public.return_message(-1, 0, public.lang("The specified directory does not exist"))

        if backup_path[-1] == "/":
            backup_path = backup_path[:-1]

        import files
        try:
            from BTPanel import session
        except:
            session = None
        fs = files.files()

        if not fs.CheckDir(get.backup_path):
            return public.return_message(-1, 0, public.lang("You cannot use the system critical directory as the default backup directory"))
        if session is not None:
            session['config']['backup_path'] = os.path.join('/', backup_path)
        db_backup = backup_path + '/database'
        site_backup = backup_path + '/site'

        if not os.path.exists(db_backup):
            try:
                os.makedirs(db_backup, 384)
            except:
                public.ExecShell('mkdir -p ' + db_backup)

        if not os.path.exists(site_backup):
            try:
                os.makedirs(site_backup, 384)
            except:
                public.ExecShell('mkdir -p ' + site_backup)

        public.M('config').where("id=?", ('1',)).save('backup_path', (get.backup_path,))
        public.WriteLog('TYPE_PANEL', 'PANEL_SET_SUCCESS', (get.backup_path,))

        public.restart_panel()
        return public.return_message(0, 0, public.lang("The setup was successful"))


    def get_soft_status(self, get):
        if not hasattr(get, 'name'): return public.return_message(-1, 0, public.lang("Parameter error"))
        s_status = False
        status = False
        setup = False
        name = get.name.strip()
        if name == 'web': name = public.get_webserver()
        version = ''
        if name == 'sqlite':
            status = True
        if name in ['mysql', 'pgsql', 'sqlserver', 'mongodb', 'redis']:
            count = public.M('database_servers').where("LOWER(db_type)=LOWER(?)", (name,)).count()
            if count > 0: status = True
        if os.path.exists('/www/server/{}'.format(name)) and len(os.listdir('/www/server/{}'.format(name))) > 2:
            if not public.M('tasks').where("name like ? and status == -1",
                                           ('安装%{}%'.format(name.replace('-', '')),)).count() > 0:
                status = True
                setup = True
        if name == 'openlitespeed':
            status = os.path.exists('/usr/local/lsws/bin/lswsctrl')
            setup = status
        if status:
            path_data = {
                "nginx": "/www/server/nginx/logs/nginx.pid",
                "mysql": "/www/server/data/localhost.localdomain.pid",
                "apache": "/www/server/apache/logs/httpd.pid",
                "pure-ftpd": "/var/run/pure-ftpd.pid",
                "redis": "/www/server/redis/redis.pid",
                "pgsql": "/www/server/pgsql/data_directory/postmaster.pid",
                "openlitespeed": "/tmp/lshttpd/lshttpd.pid"
            }
            if name == 'mysql':
                datadir = public.get_datadir()
                if datadir:
                    path_data["mysql"] = "{}/{}.pid".format(datadir, public.get_hostname())

            if name in path_data.keys():
                if os.path.exists(path_data[name]):
                    pid = public.readFile(path_data[name])
                    if pid:
                        try:
                            psutil.Process(int(pid))
                            s_status = True
                        except:
                            pass
                else:
                    # 可能会存在用户修改主机名后 找不到pid文件的情况
                    if name == 'mysql' and not s_status:
                        for proc in psutil.process_iter():
                            if proc.name() == 'mysqld':
                                s_status = True
                                public.writeFile(path_data['mysql'], str(proc.pid))
                                break
        version_data = {
            "nginx": '/www/server/nginx/version.pl',
            "mysql": "/www/server/mysql/version.pl",
            "pgsql": "/www/server/pgsql/data/PG_VERSION",
            "apache": "/www/server/apache/version.pl",
            "pure-ftpd": "/www/server/pure-ftpd/version.pl",
            "openlitespeed": "/usr/local/lsws/VERSION"
        }
        if name in version_data.keys():
            if os.path.exists(version_data[name]):
                version = public.readFile(version_data[name]).strip()
        title_data = {
            "nagix": "Nginx",
            "mysql": "MySQL",
            "pgsql": "PostgreSQL",
            "mongodb": "MongoDB",
            "redis": "Redis",
            "apache": "Apache",
            "openlitespeed": "OpenLiteSpeed",
            "pure-ftpd": "Pure-FTPd",
        }
        s_version_data = {
            'mysql': 'mysqld',
            'apache': 'httpd',
        }

        data = {
            "status": status,
            "s_status": s_status,
            "msg": '',
            "version": version,
            "name": name.replace('-', ''),
            "title": title_data.get(name, name),
            "admin": os.path.exists('/www/server/panel/plugin/' + name),
            "s_version": s_version_data.get(name, name),
            "setup": setup
        }
        return public.return_message(0, 0,data)

