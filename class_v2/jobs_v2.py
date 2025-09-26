#coding: utf-8
# +-------------------------------------------------------------------
# | aaPanel
# +-------------------------------------------------------------------
# | Copyright (c) 2015-2099 aaPanel(www.aapanel.com) All rights reserved.
# +-------------------------------------------------------------------
# | Author: hwliang <hwl@aapanel.com>
# +-------------------------------------------------------------------
import time,public,db,os,sys,json,re,shutil
os.chdir('/www/server/panel')

def control_init():
    public.chdck_salt()
    rep_websocket_conf()
    clear_other_files()
    sql_pacth()
    #disable_putenv('putenv')
    #clean_session()
    #set_crond()
    clean_max_log('/www/server/panel/plugin/rsync/lsyncd.log')
    clean_max_log('/var/log/rsyncd.log',1024*1024*10)
    clean_max_log('/root/.pm2/pm2.log',1024*1024*20)
    remove_tty1()
    clean_hook_log()
    run_new()
    clean_max_log('/www/server/cron',1024*1024*5,20)
    clean_max_log("/www/server/panel/plugin/webhook/script",1024*1024*1)
    #check_firewall()
    check_dnsapi()
    clean_php_log()
    files_set_mode()
    set_pma_access()
    # public.set_open_basedir()
    clear_fastcgi_safe()
    update_py37()
    run_script()
    set_php_cli_env()
    check_enable_php()
    #sync_node_list()
    check_default_curl_file()
    null_html()
    remove_other()
    deb_bashrc()
    upgrade_gevent()
    upgrade_polkit()
    #hide_docker()
    rep_pyenv_link()
    rm_apache_cgi_test()

def rm_apache_cgi_test():
    '''
        @name 删除apache测试cgi文件
        @author hwliang
        @return void
    '''
    test_cgi_file = '/www/server/apache/cgi-bin/test-cgi'
    if os.path.exists(test_cgi_file):
        os.remove(test_cgi_file)

def rep_pyenv_link():
    '''
        @name 修复pyenv环境软链
        @author hwliang
        @return void
    '''

    pyenv_bin = '/www/server/panel/pyenv/bin/python3'
    btpython_bin = '/usr/bin/btpython'
    pip_bin = '/www/server/panel/pyenv/bin/pip3'
    btpip_bin = '/usr/bin/btpip'

    # 检查btpython软链接
    if not os.path.exists(pyenv_bin): return
    if not os.path.exists(btpython_bin):
        public.ExecShell("ln -sf {} {}".format(pyenv_bin,btpython_bin))

    # 检查btpip软链接
    if not os.path.exists(pip_bin): return
    if not os.path.exists(btpip_bin):
        public.ExecShell("ln -sf {} {}".format(pip_bin,btpip_bin))

def hide_docker():
    '''
        @name 隐藏docker菜单
        @author hwliang
        @return void
    '''
    tip_file = '{}/data/hide_docker.pl'.format(public.get_panel_path())
    if os.path.exists(tip_file): return

    # 正在使用docker-compose的用户不隐藏
    docker_compose = "/usr/bin/docker-compose"
    if os.path.exists(docker_compose): return

    # 获取隐藏菜单配置
    menu_key = 'memuDocker'
    hide_menu_json = public.read_config('hide_menu')
    if not isinstance(hide_menu_json,list):
        hide_menu_json = []
    if menu_key in hide_menu_json: return

    # 保存隐藏菜单配置
    hide_menu_json.append(menu_key)
    public.save_config('hide_menu',hide_menu_json)
    public.writeFile(tip_file,'True')


def rep_websocket_conf():
    """
        @name 修复websocket配置文件
        @return void
    """
    conf = '''map $http_upgrade $connection_upgrade {
    default upgrade;
    ''  close;
}'''

    conf_file = '{}/vhost/nginx/0.websocket.conf'.format(public.get_panel_path())
    if os.path.exists(conf_file):
        conf_body = public.readFile(conf_file)
        if conf_body.find('map $http_upgrade $connection_upgrade') != -1: return

    public.writeFile(conf_file,conf)
    setupPath = public.get_setup_path()
    result = public.ExecShell('ulimit -n 8192 ; ' + setupPath + '/nginx/sbin/nginx -t -c ' + setupPath + '/nginx/conf/nginx.conf')
    if 'connection_upgrade' in result[1]:
        if os.path.exists(conf_file): os.remove(conf_file)


def upgrade_polkit():
    '''
        @name 修复polkit提权漏洞(CVE-2021-4034)
        @author hwliang
        @return void
    '''
    upgrade_log_file = '{}/logs/upgrade_polkit.log'.format(public.get_panel_path())
    tip_file = '{}/data/upgrade_polkit.pl'.format(public.get_panel_path())
    if os.path.exists(tip_file): return
    os.system("nohup {} {}/script/polkit_upgrade.py &> {}".format(public.get_python_bin(),public.get_panel_path(),upgrade_log_file))

def clear_other_files():
    dirPath = '/www/server/phpmyadmin/pma'
    if os.path.exists(dirPath):
        public.ExecShell("rm -rf {}".format(dirPath))
    dirPath = '/www/server/nginx/waf'
    if os.path.exists(dirPath):
        public.ExecShell("rm -rf {}".format(dirPath))
        public.ExecShell("/etc/init.d/nginx reload")
        public.ExecShell("/etc/init.d/nginx start")

    # dirPath = '/www/server/adminer'
    # if os.path.exists(dirPath):
    #     public.ExecShell("rm -rf {}".format(dirPath))
    #
    # dirPath = '/www/server/panel/adminer'
    # if os.path.exists(dirPath):
    #     public.ExecShell("rm -rf {}".format(dirPath))

    filename = '/www/server/nginx/off'
    if os.path.exists(filename): os.remove(filename)
    filename = "{}/vhost/nginx/waf.conf".format(public.get_panel_path())
    if os.path.exists(filename):
        os.remove(filename)
        public.ExecShell("/etc/init.d/nginx reload")
        public.ExecShell("/etc/init.d/nginx start")
    c = public.to_string([99, 104, 97, 116, 116, 114, 32, 45, 105, 32, 47, 119, 119, 119, 47,
                          115, 101, 114, 118, 101, 114, 47, 112, 97, 110, 101, 108, 47, 99,
                          108, 97, 115, 115, 47, 42])
    try:
        init_file = '/etc/init.d/bt'
        src_file = '/www/server/panel/init.sh'
        md51 = public.md5(init_file)
        md52 = public.md5(src_file)
        if md51 != md52:
            import shutil
            shutil.copyfile(src_file,init_file)
            if os.path.getsize(init_file) < 10:
                public.ExecShell("chattr -i " + init_file)
                public.ExecShell(r"\cp -arf %s %s" % (src_file,init_file))
                public.ExecShell("chmod +x %s" % init_file)
    except:pass
    public.writeFile('/var/bt_setupPath.conf','/www')
    public.ExecShell(c)
    p_file = 'class/plugin2.so'
    if os.path.exists(p_file): public.ExecShell("rm -f class/*.so")
    public.ExecShell("chmod -R  600 /www/server/panel/data;chmod -R  600 /www/server/panel/config;chmod -R  700 /www/server/cron;chmod -R  600 /www/server/cron/*.log;chown -R root:root /www/server/panel/data;chown -R root:root /www/server/panel/config;chown -R root:root /www/server/phpmyadmin;chmod -R 755 /www/server/phpmyadmin")
    if os.path.exists("/www/server/mysql"):
        public.ExecShell("chown mysql:mysql /etc/my.cnf;chmod 600 /etc/my.cnf")
    public.ExecShell("rm -rf /www/server/panel/temp/*")
    stop_path = '/www/server/stop'
    if not os.path.exists(stop_path):
        os.makedirs(stop_path)
    public.ExecShell("chown -R root:root {path};chmod -R 755 {path}".format(path=stop_path))
    public.ExecShell('chmod 755 /www;chmod 755 /www/server')
    if os.path.exists('/www/server/phpmyadmin/pma'):
        public.ExecShell("rm -rf /www/server/phpmyadmin/pma")
    if os.path.exists("/www/server/adminer"):
        public.ExecShell("rm -rf /www/server/adminer")
    if os.path.exists("/www/server/panel/adminer"):
        public.ExecShell("rm -rf /www/server/panel/adminer")
    if os.path.exists('/dev/shm/session.db'):
        os.remove('/dev/shm/session.db')

    node_service_bin = '/usr/bin/nodejs-service'
    node_service_src = '/www/server/panel/script/nodejs-service.py'
    if os.path.exists(node_service_src): public.ExecShell("chmod 700 " + node_service_src)
    if not os.path.exists(node_service_bin):
        if os.path.exists(node_service_src):
            public.ExecShell("ln -sf {} {}".format(node_service_src,node_service_bin))


def sql_pacth():
    sql = db.Sql().dbfile('system')
    if not sql.table('sqlite_master').where('type=? AND name=?', ('table', 'load_average')).count():
        csql = '''CREATE TABLE IF NOT EXISTS `load_average` (
`id` INTEGER PRIMARY KEY AUTOINCREMENT,
`pro` REAL,
`one` REAL,
`five` REAL,
`fifteen` REAL,
`addtime` INTEGER
)'''
        sql.execute(csql,())
    if not public.M('sqlite_master').where('type=? AND name=? AND sql LIKE ?', ('table', 'sites','%type_id%')).count():
        public.M('sites').execute("alter TABLE sites add type_id integer DEFAULT 0",())

    if not public.M('sqlite_master').where('type=? AND name=? AND sql LIKE ?', ('table', 'database_servers','%db_type%')).count():
        public.M('databases').execute("alter TABLE database_servers add db_type REAL DEFAULT 'mysql'",())

    if not public.M('sqlite_master').where('type=? AND name=? AND sql LIKE ?', ('table', 'sites','%edate%')).count():
        public.M('sites').execute("alter TABLE sites add edate integer DEFAULT '0000-00-00'",())

    if not public.M('sqlite_master').where('type=? AND name=? AND sql LIKE ?', ('table', 'sites','%project_type%')).count():
        public.M('sites').execute("alter TABLE sites add project_type STRING DEFAULT 'PHP'",())

    if not public.M('sqlite_master').where('type=? AND name=? AND sql LIKE ?', ('table', 'sites','%project_config%')).count():
        public.M('sites').execute("alter TABLE sites add project_config STRING DEFAULT '{}'",())

    if not public.M('sqlite_master').where('type=? AND name=? AND sql LIKE ?', ('table', 'backup','%ps%')).count():
        public.M('backup').execute("alter TABLE backup add ps STRING DEFAULT 'No'",())

    if not public.M('sqlite_master').where('type=? AND name=? AND sql LIKE ?', ('table', 'databases','%db_type%')).count():
        public.M('databases').execute("alter TABLE databases add db_type integer DEFAULT '0'",())

    if not public.M('sqlite_master').where('type=? AND name=? AND sql LIKE ?', ('table', 'databases','%conn_config%')).count():
        public.M('databases').execute("alter TABLE databases add conn_config STRING DEFAULT '{}'",())

    if not public.M('sqlite_master').where('type=? AND name=? AND sql LIKE ?', ('table', 'databases','%sid%')).count():
        public.M('databases').execute("alter TABLE databases add sid integer DEFAULT 0",())

    ndb = public.M('databases').order("id desc").field('id,pid,name,username,password,accept,ps,addtime,type').select()
    if type(ndb) == str: public.M('databases').execute("alter TABLE databases add type TEXT DEFAULT MySQL",())

    # 计划任务表处理
    if not public.M('sqlite_master').where('type=? AND name=? AND sql LIKE ?', ('table', 'crontab','%status%')).count():
        public.M('crontab').execute("ALTER TABLE 'crontab' ADD 'status' INTEGER DEFAULT 1",())
    if not public.M('sqlite_master').where('type=? AND name=? AND sql LIKE ?', ('table', 'crontab','%save%')).count():
        public.M('crontab').execute("ALTER TABLE 'crontab' ADD 'save' INTEGER DEFAULT 3",())
    if not public.M('sqlite_master').where('type=? AND name=? AND sql LIKE ?', ('table', 'crontab','%backupTo%')).count():
        public.M('crontab').execute("ALTER TABLE 'crontab' ADD 'backupTo' TEXT DEFAULT off",())
    if not public.M('sqlite_master').where('type=? AND name=? AND sql LIKE ?', ('table', 'crontab','%sName%')).count():
        public.M('crontab').execute("ALTER TABLE 'crontab' ADD 'sName' TEXT",())
    if not public.M('sqlite_master').where('type=? AND name=? AND sql LIKE ?', ('table', 'crontab','%sBody%')).count():
        public.M('crontab').execute("ALTER TABLE 'crontab' ADD 'sBody' TEXT",())
    if not public.M('sqlite_master').where('type=? AND name=? AND sql LIKE ?', ('table', 'crontab','%sType%')).count():
        public.M('crontab').execute("ALTER TABLE 'crontab' ADD 'sType' TEXT",())
    if not public.M('sqlite_master').where('type=? AND name=? AND sql LIKE ?', ('table', 'crontab','%urladdress%')).count():
        public.M('crontab').execute("ALTER TABLE 'crontab' ADD 'urladdress' TEXT",())
    if not public.M('sqlite_master').where('type=? AND name=? AND sql LIKE ?', ('table', 'crontab','%save_local%')).count():
        public.M('crontab').execute("ALTER TABLE 'crontab' ADD 'save_local' INTEGER DEFAULT 0",())
    if not public.M('sqlite_master').where('type=? AND name=? AND sql LIKE ?', ('table', 'crontab','%notice%')).count():
        public.M('crontab').execute("ALTER TABLE 'crontab' ADD 'notice' INTEGER DEFAULT 0",())
    if not public.M('sqlite_master').where('type=? AND name=? AND sql LIKE ?', ('table', 'crontab','%notice_channel%')).count():
        public.M('crontab').execute("ALTER TABLE 'crontab' ADD 'notice_channel' TEXT DEFAULT ''",())

    sql = db.Sql()
    if not sql.table('sqlite_master').where('type=? AND name=?', ('table', 'site_types')).count():
        csql = '''CREATE TABLE IF NOT EXISTS `site_types` (
`id` INTEGER PRIMARY KEY AUTOINCREMENT,
`name` REAL,
`ps` REAL
)'''

        sql.execute(csql,())

    if not sql.table('sqlite_master').where('type=? AND name=?', ('table', 'download_token')).count():
        csql = '''CREATE TABLE IF NOT EXISTS `download_token` (
`id` INTEGER PRIMARY KEY AUTOINCREMENT,
`token` REAL,
`filename` REAL,
`total` INTEGER DEFAULT 0,
`expire` INTEGER,
`password` REAL,
`ps` REAL,
`addtime` INTEGER
)'''
        sql.execute(csql,())


    if not sql.table('sqlite_master').where('type=? AND name=?', ('table', 'messages')).count():
        csql = '''CREATE TABLE IF NOT EXISTS `messages` (
`id` INTEGER PRIMARY KEY AUTOINCREMENT,
`level` TEXT,
`msg` TEXT,
`state` INTEGER DEFAULT 0,
`expire` INTEGER,
`addtime` INTEGER
)'''
        sql.execute(csql,())

    if not sql.table('sqlite_master').where('type=? AND name=?', ('table', 'temp_login')).count():
        csql = '''CREATE TABLE IF NOT EXISTS `temp_login` (
`id` INTEGER PRIMARY KEY AUTOINCREMENT,
`token` REAL,
`salt` REAL,
`state` INTEGER,
`login_time` INTEGER,
`login_addr` REAL,
`logout_time` INTEGER,
`expire` INTEGER,
`addtime` INTEGER
)'''
        sql.execute(csql,())

    if not sql.table('sqlite_master').where('type=? AND name=?', ('table', 'database_servers')).count():
        csql = '''CREATE TABLE IF NOT EXISTS `database_servers` (
`id` INTEGER PRIMARY KEY AUTOINCREMENT,
`db_host` REAL,
`db_port` REAL,
`db_user` INTEGER,
`db_password` INTEGER,
`ps` REAL,
`addtime` INTEGER
)'''
        sql.execute(csql,())

    if not sql.table('sqlite_master').where('type=? AND name=?', ('table', 'security')).count():
        csql = '''CREATE TABLE IF NOT EXISTS `security` (
    `id` INTEGER PRIMARY KEY AUTOINCREMENT,
    `type` TEXT,
    `log` TEXT,
    `addtime` INTEGER DEFAULT 0
    )'''
        sql.execute(csql, ())


    test_ping()
    if not public.M('sqlite_master').where('type=? AND name=? AND sql LIKE ?', ('table', 'logs','%username%')).count():
        public.M('logs').execute("alter TABLE logs add uid integer DEFAULT '1'",())
        public.M('logs').execute("alter TABLE logs add username TEXT DEFAULT 'system'",())

    if not public.M('sqlite_master').where('type=? AND name=? AND sql LIKE ?', ('table', 'crontab','%status%')).count():
        public.M('crontab').execute("ALTER TABLE 'crontab' ADD 'status' INTEGER DEFAULT 1",())
        public.M('crontab').execute("ALTER TABLE 'crontab' ADD 'save' INTEGER DEFAULT 3",())
        public.M('crontab').execute("ALTER TABLE 'crontab' ADD 'backupTo' TEXT DEFAULT off",())
        public.M('crontab').execute("ALTER TABLE 'crontab' ADD 'sName' TEXT",())
        public.M('crontab').execute("ALTER TABLE 'crontab' ADD 'sBody' TEXT",())
        public.M('crontab').execute("ALTER TABLE 'crontab' ADD 'sType' TEXT",())
        public.M('crontab').execute("ALTER TABLE 'crontab' ADD 'urladdress' TEXT",())

    public.M('users').where('email=? or email=?',('287962566@qq.com','amw_287962566@qq.com')).setField('email','test@message.com')

    if not public.M('sqlite_master').where('type=? AND name=? AND sql LIKE ?', ('table', 'users','%salt%')).count():
        public.M('users').execute("ALTER TABLE 'users' ADD 'salt' TEXT",())


    if not public.M('sqlite_master').where('type=? AND name=? AND sql LIKE ?', ('table', 'messages','%retry_num%')).count():
        public.M('messages').execute("alter TABLE messages add send integer DEFAULT 0",())
        public.M('messages').execute("alter TABLE messages add retry_num integer DEFAULT 0",())


def upgrade_gevent():
    '''
        @name 升级gevent
        @author hwliang
        @return void
    '''
    tip_file = '{}/data/upgrade_gevent.lock'.format(public.get_panel_path())
    upgrade_script_file = '{}/script/upgrade_gevent.sh'.format(public.get_panel_path())
    if os.path.exists(upgrade_script_file) and not os.path.exists(tip_file):
        public.writeFile(tip_file,'1')
        os.system("bash {}".format(upgrade_script_file))
        if os.path.exists(tip_file): os.remove(tip_file)


def deb_bashrc():
    '''
        @name 针对debian/ubuntu未调用bashrc导致的问题
        @author hwliang
        @return void
    '''
    bashrc = '/root/.bashrc'
    bash_profile = '/root/.bash_profile'
    apt_get = '/usr/bin/apt-get'
    if not os.path.exists(apt_get): return
    if not os.path.exists(bashrc): return
    if not os.path.exists(bash_profile): return

    profile_body = public.readFile(bash_profile)
    if not isinstance(profile_body,str): return
    if profile_body.find('.bashrc') == -1:
        public.writeFile(bash_profile,'source ~/.bashrc\n' + profile_body.strip() + "\n")



def remove_other():
    rm_files = [
        "class/pluginAuth.so",
        "class/pluginAuth.cpython-310-x86_64-linux-gnu.so",
        "class/pluginAuth.cpython-310-aarch64-linux-gnu.so",
        "class/pluginAuth.cpython-37m-i386-linux-gnu.so",
        "class/pluginAuth.cpython-37m-loongarch64-linux-gnu.so",
        "class/pluginAuth.cpython-37m-aarch64-linux-gnu.so",
        "class/pluginAuth.cpython-37m-x86_64-linux-gnu.so",
        "class/pluginAuth.cpython-37m.so",
        "class/libAuth.loongarch64.so",
        "class/libAuth.x86.so",
        "class/libAuth.x86-64.so",
        "class/libAuth.glibc-2.14.x86_64.so",
        "class/libAuth.aarch64.so",
        "script/check_files.py"
    ]

    for f in rm_files:
        if os.path.exists(f):
            os.remove(f)



def null_html():
    null_files = ['/www/server/nginx/html/index.html','/www/server/apache/htdocs/index.html','/www/server/panel/data/404.html']
    null_new_body='''<html>
<head><title>404 Not Found</title></head>
<body>
<center><h1>404 Not Found</h1></center>
<hr><center>nginx</center>
</body>
</html>'''
    for null_file in null_files:
        if not os.path.exists(null_file): continue

        null_body = public.readFile(null_file)
        if not null_body: continue
        if null_body.find('没有找到站点') != -1 or null_body.find('您请求的文件不存在') != -1:
            public.writeFile(null_file,null_new_body)


def check_default_curl_file():
    default_file = '{}/data/default_curl.pl'.format(public.get_panel_path())
    if os.path.exists(default_file):
        default_curl_body = public.readFile(default_file)
        if default_curl_body:
            public.WriteFile(default_file,default_curl_body.strip())

def set_php_cli_env():
    '''
        @name 设置php-cli环境变量
        @author hwliang<2021-09-07>
        @return void
    '''
    php_path = '/www/server/php'
    bashrc = '/root/.bashrc'
    if not os.path.exists(php_path): return
    if not os.path.exists(bashrc): return
    # 清理所有别名
    public.ExecShell('sed -i "/alias php/d" {}'.format(bashrc))
    bashrc_body = public.readFile(bashrc)
    if not bashrc_body: return

    # 设置默认环境变量版本别名
    env_php_bin = '/usr/bin/php'
    if os.path.exists(env_php_bin):
        if os.path.islink(env_php_bin):
            php_cli_ini = "/etc/php-cli.ini"
            if os.path.exists(php_cli_ini):
                bashrc_body += "alias php='php -c {}'\n".format(php_cli_ini)


    # 设置所有已安装的PHP版本环境变量和别名
    php_versions_list = public.get_php_versions()
    for php_version in php_versions_list:
        php_ini = "{}/{}/etc/php.ini".format(php_path,php_version)
        php_cli_ini = "{}/{}/etc/php-cli.ini".format(php_path,php_version)
        env_php_bin = "/usr/bin/php{}".format(php_version)
        php_bin = "{}/{}/bin/php".format(php_path,php_version)
        php_ize = '/usr/bin/php{}-phpize'.format(php_version)
        php_ize_src = "{}/{}/bin/phpize".format(php_path,php_version)
        php_fpm = '/usr/bin/php{}-php-fpm'.format(php_version)
        php_fpm_src = "{}/{}/sbin/php-fpm".format(php_path,php_version)
        php_pecl = '/usr/bin/php{}-pecl'.format(php_version)
        php_pecl_src = "{}/{}/bin/pecl".format(php_path,php_version)
        php_pear = '/usr/bin/php{}-pear'.format(php_version)
        php_pear_src = "{}/{}/bin/pear".format(php_path,php_version)

        if os.path.exists(php_bin):
            # 设置每个版本的环境变量
            if not os.path.exists(env_php_bin): os.symlink(php_bin,env_php_bin)
            if not os.path.exists(php_ize) and os.path.exists(php_ize_src): os.symlink(php_ize_src,php_ize)
            if not os.path.exists(php_fpm) and os.path.exists(php_fpm_src): os.symlink(php_fpm_src,php_fpm)
            if not os.path.exists(php_pecl) and os.path.exists(php_pecl_src): os.symlink(php_pecl_src,php_pecl)
            if not os.path.exists(php_pear) and os.path.exists(php_pear_src): os.symlink(php_pear_src,php_pear)
            public.ExecShell(r"\cp -f {} {}".format(php_ini,php_cli_ini)) # 每次复制新的php.ini到php-cli.ini
            public.ExecShell('sed -i "/disable_functions/d" {}'.format(php_cli_ini)) # 清理禁用函数
            bashrc_body += "alias php{}='php{} -c {}'\n".format(php_version,php_version,php_cli_ini) # 设置别名
        else:
            # 清理已卸载的环境变量
            if os.path.exists(env_php_bin): os.remove(env_php_bin)
            if os.path.exists(php_ize): os.remove(php_ize)
            if os.path.exists(php_fpm): os.remove(php_fpm)
            if os.path.exists(php_pecl): os.remove(php_pecl)
            if os.path.exists(php_pear): os.remove(php_pear)
    public.writeFile(bashrc,bashrc_body)


def check_enable_php():
    '''
        @name 检查nginx下的php配置文件
    '''
    php_versions = public.get_php_versions()
    ngx_php_conf = public.get_setup_path() + '/nginx/conf/enable-php-00.conf'
    public.writeFile(ngx_php_conf,'')
    for php_v in php_versions:
        ngx_php_conf = public.get_setup_path() + '/nginx/conf/enable-php-{}.conf'.format(php_v)
        if os.path.exists(ngx_php_conf): continue
        enable_conf = r'''
    location ~ [^/]\.php(/|$)
	{{
		try_files $uri =404;
		fastcgi_pass  unix:/tmp/php-cgi-{}.sock;
		fastcgi_index index.php;
		include fastcgi.conf;
		include pathinfo.conf;
	}}
    '''.format(php_v)
        public.writeFile(ngx_php_conf,enable_conf)



def write_run_script_log(_log,rn='\n'):
    _log_file = '/www/server/panel/logs/run_script.log'
    public.writeFile(_log_file,_log + rn,'a+')


def run_script():
    try:
        os.system("{} {}/script/run_script.py".format(public.get_python_bin(),public.get_panel_path()))
        run_tip = '/dev/shm/bt.pl'
        if os.path.exists(run_tip): return
        public.writeFile(run_tip,str(time.time()))
        uptime = float(public.readFile('/proc/uptime').split()[0])
        if uptime > 1800: return
        run_config ='/www/server/panel/data/run_config'
        script_logs = '/www/server/panel/logs/script_logs'
        if not os.path.exists(run_config):
            os.makedirs(run_config,384)
        if not os.path.exists(script_logs):
            os.makedirs(script_logs,384)

        for sname in os.listdir(run_config):
            script_conf_file = '{}/{}'.format(run_config,sname)
            if not os.path.exists(script_conf_file): continue
            script_info = json.loads(public.readFile(script_conf_file))
            exec_log_file = '{}/{}'.format(script_logs,sname)

            if not os.path.exists(script_info['script_file']) \
                or script_info['script_file'].find('/www/server/panel/plugin/') != 0 \
                    or not re.match(r'^\w+$',script_info['script_file']):
                os.remove(script_conf_file)
                if os.path.exists(exec_log_file): os.remove(exec_log_file)
                continue


            if script_info['script_type'] == 'python':
                _bin = public.get_python_bin()
            elif script_info['script_type'] == 'bash':
                _bin = '/usr/bin/bash'
                if not os.path.exists(_bin): _bin = 'bash'

            exec_script = 'nohup {} {} &> {} &'.format(_bin,script_info['script_file'],exec_log_file)
            public.ExecShell(exec_script)
            script_info['last_time'] = time.time()
            public.writeFile(script_conf_file,json.dumps(script_info))
    except:
        pass


def clear_fastcgi_safe():
    try:
        fastcgifile = '/www/server/nginx/conf/fastcgi.conf'
        if os.path.exists(fastcgifile):
            conf = public.readFile(fastcgifile)
            if conf.find('bt_safe_open') != -1:
                public.ExecShell('sed -i "/bt_safe_open/d" {}'.format(fastcgifile))
                public.ExecShell('/etc/init.d/nginx reload')
    except:
        pass

#设置文件权限
def files_set_mode():
    rr = {True:'-R',False:''}
    m_paths = [
        ["/www/server/total","/*.lua","root",755,False],
        ["/www/server/total","/*.json","root",755,False],
        ["/www/server/total/logs","","www",755,True],
        ["/www/server/total/total","","www",755,True],
        ["/www/server/speed","/*.lua","root",755,False],
        ["/www/server/speed/total","","www",755,True],
        ["/www/server/btwaf","/*.lua","root",755,False],
        ["/www/backup","","root",600,True],
        ["/www/wwwlogs","","www",700,True],
        ["/www/enterprise_backup","","root",600,True],
        ["/www/server/cron","","root",700,True],
        ["/www/server/cron","/*.log","root",600,True],
        ["/www/server/stop","","root",755,True],
        ["/www/server/redis","","redis",700,True],
        ["/www/server/redis/redis.conf","","redis",600,False],
        ["/www/server/panel/class","","root",600,True],
        ["/www/server/panel/data","","root",600,True],
        ["/www/server/panel/plugin","","root",600,False],
        ["/www/server/panel/BTPanel","","root",600,True],
        ["/www/server/panel/vhost","","root",600,True],
        ["/www/server/panel/rewrite","","root",600,True],
        ["/www/server/panel/config","","root",600,True],
        ["/www/server/panel/backup","","root",600,True],
        ["/www/server/panel/package","","root",600,True],
        ["/www/server/panel/script","","root",700,True],
        ["/www/server/panel/temp","","root",600,True],
        ["/www/server/panel/tmp","","root",600,True],
        ["/www/server/panel/ssl","","root",600,True],
        ["/www/server/panel/install","","root",600,True],
        ["/www/server/panel/logs","","root",600,True],
        ["/www/server/panel/BT-Panel","","root",700,False],
        ["/www/server/panel/BT-Task","","root",700,False],
        ["/www/server/panel","/*.py","root",600,False],
        ["/dev/shm/session.db","","root",600,False],
        ["/dev/shm/session_py3","","root",600,True],
        ["/dev/shm/session_py2","","root",600,True],
        ["/www/server/phpmyadmin","","root",755,True],
        ["/www/server/adminer", "", "root", 755, True],
        ["/www/server/coll","","root",700,True],
        ["/www/server/panel/init.sh","","root",600,False],
        ["/www/server/panel/license.txt","","root",600,False],
        ["/www/server/panel/requirements.txt","","root",600,False],
        ["/www/server/panel/update.sh","","root",600,False],
        ["/www/server/panel/default.pl","","root",600,False],
        ["/www/server/panel/hooks","","root",600,True],
        ["/www/server/panel/cache","","root",600,True],
        ["/root","","root",550,False],
        ["/root/.ssh","","root",700,False],
        ["/root/.ssh/authorized_keys","","root",600,False],
        ["/root/.ssh/id_rsa.pub","","root",644,False],
        ["/root/.ssh/id_rsa","","root",600,False],
        ["/root/.ssh/known_hosts","","root",644,False]
    ]

    recycle_list = public.get_recycle_bin_list()
    for recycle_path in recycle_list:
        m_paths.append([recycle_path,'','root',600,True])

    for m in m_paths:
        if not os.path.exists(m[0]): continue
        path = m[0] + m[1]
        public.ExecShell("chown {R} {U}:{U} {P}".format(P=path,U=m[2],R=rr[m[4]]))
        public.ExecShell("chmod {R} {M} {P}".format(P=path,M=m[3],R=rr[m[4]]))
        if m[1]:
            public.ExecShell("chown {U}:{U} {P}".format(P=m[0],U=m[2],R=rr[m[4]]))
            public.ExecShell("chmod {M} {P}".format(P=m[0],M=m[3],R=rr[m[4]]))

    # 移除面板目录下所有文件的所属组、其它用户的写权限
    public.ExecShell("chmod -R go-w /www/server/panel")

#获取PMA目录
def get_pma_path():
    pma_path = '/www/server/phpmyadmin'
    if not os.path.exists(pma_path): return False
    for filename in os.listdir(pma_path):
        filepath = pma_path + '/' + filename
        if os.path.isdir(filepath):
            if filename[0:10] == 'phpmyadmin':
                return str(filepath)
    return False


#处理phpmyadmin访问权限
def set_pma_access():
    try:
        pma_path = get_pma_path()
        if not pma_path: return False
        if not os.path.exists(pma_path): return False
        pma_tmp = pma_path + '/tmp'
        if not os.path.exists(pma_tmp):
            os.makedirs(pma_tmp)

        nginx_file = '/www/server/nginx/conf/nginx.conf'
        if os.path.exists(nginx_file):
            nginx_conf = public.readFile(nginx_file)
            if nginx_conf.find('/tmp/') == -1:
                r_conf = '''/www/server/phpmyadmin;
            location ~ /tmp/ {
                return 403;
            }'''

                nginx_conf = nginx_conf.replace('/www/server/phpmyadmin;',r_conf)
                public.writeFile(nginx_file,nginx_conf)
                public.serviceReload()

        apa_pma_tmp = pma_tmp + '/.htaccess'
        if not os.path.exists(apa_pma_tmp):
            r_conf = '''order allow,deny
    deny from all'''
            public.writeFile(apa_pma_tmp,r_conf)
            public.set_mode(apa_pma_tmp,755)
            public.set_own(apa_pma_tmp,'root')

        public.ExecShell("chmod -R 700 {}".format(pma_tmp))
        public.ExecShell("chown -R www:www {}".format(pma_tmp))
        return True
    except:
        return False





#尝试升级到独立环境
def update_py37():
    pyenv='/www/server/panel/pyenv/bin/python3'
    pyenv_exists='/www/server/panel/data/pyenv_exists.pl'
    if os.path.exists(pyenv) or os.path.exists(pyenv_exists): return False
    download_url = public.get_url()
    public.ExecShell("nohup curl {}/install/update_panel_en.sh|bash &>/tmp/panelUpdate.pl &".format(download_url))
    public.writeFile(pyenv_exists,'True')
    return True

def test_ping():
    _f = '/www/server/panel/data/ping_token.pl'
    if os.path.exists(_f): os.remove(_f)
    try:
        import panelPing
        panelPing.Test().create_token()
    except:
        pass

#检查dnsapi
def check_dnsapi():
    dnsapi_file = 'config/dns_api.json'
    tmp = public.readFile(dnsapi_file)
    if not tmp: return False
    dnsapi = json.loads(tmp)
    if tmp.find('CloudFlare') == -1:
        cloudflare = {
                        "ps": "Use CloudFlare's API interface to automatically parse and apply for SSL",
                        "title": "CloudFlare",
                        "data": [{
                            "value": "",
                            "key": "SAVED_CF_MAIL",
                            "name": "E-Mail"
                        }, {
                            "value": "",
                            "key": "SAVED_CF_KEY",
                            "name": "API Key"
                        }],
                        "help": "CloudFlare Get in the background Global API Key",
                        "name": "CloudFlareDns"
                    }
        dnsapi.insert(0,cloudflare)
    check_names = {"dns_bt":"Dns_com","dns_dp":"DNSPodDns","dns_ali":"AliyunDns","dns_cx":"CloudxnsDns"}
    for i in range(len(dnsapi)):
        if dnsapi[i]['name'] in check_names:
            dnsapi[i]['name'] = check_names[dnsapi[i]['name']]

    public.writeFile(dnsapi_file,json.dumps(dnsapi))
    return True



#检测端口放行是否同步(仅firewalld)
def check_firewall():
    try:
        if not os.path.exists('/usr/sbin/firewalld'): return False
        data = public.M('firewall').field('port,ps').select()
        import firewalld,firewalls
        fs = firewalls.firewalls()
        accept_ports = firewalld.firewalld().GetAcceptPortList()

        port_list = []
        for port_info  in accept_ports:
            if port_info['port'] in port_list:
                continue
            port_list.append(port_info['port'])

        n = 0
        for p in data:
            if p['port'].find('.') != -1:
                continue
            if p['port'] in port_list:
                continue
            fs.AddAcceptPortAll(p['port'],p['ps'])
            n+=1
        #重载
        if n: fs.FirewallReload()
    except:
        pass


#尝试启动新架构
def run_new():
    try:
        new_file = '/www/server/panel/data/new.pl'
        port_file = '/www/server/panel/data/port.pl'
        if os.path.exists(new_file): return False
        if not os.path.exists(port_file): return False
        port = public.readFile(port_file)
        if not port: return False
        cmd_line = public.ExecShell('lsof -P -i:{}|grep LISTEN|grep -v grep'.format(int(port)))[0]
        if len(cmd_line) < 20: return False
        if cmd_line.find('BT-Panel') != -1: return False
        public.writeFile('/www/server/panel/data/restart.pl','True')
        public.writeFile(new_file,'True')
        return True
    except:
        return False

#清理webhook日志
def clean_hook_log():
    path = '/www/server/panel/plugin/webhook/script'
    if not os.path.exists(path): return False
    for name in os.listdir(path):
        if name[-4:] != ".log": continue
        clean_max_log(path+'/' + name,524288)

#清理PHP日志
def clean_php_log():
    path = '/www/server/php'
    if not os.path.exists(path): return False
    php_list=public.get_php_versions()
    for name in os.listdir(path):
        if name not in php_list:continue
        filename = path +'/'+name + '/var/log/php-fpm.log'
        if os.path.exists(filename): clean_max_log(filename)
        filename = path +'/'+name + '/var/log/php-fpm-test.log'
        if os.path.exists(filename): clean_max_log(filename)
        filename =  path +'/'+name + '/var/log/slow.log'
        if os.path.exists(filename): clean_max_log(filename)

#清理大日志
def clean_max_log(log_file,max_size = 104857600,old_line = 100):
    if not os.path.exists(log_file): return False
    if os.path.getsize(log_file) > max_size:
        try:
            old_body = public.GetNumLines(log_file,old_line)
            public.writeFile(log_file,old_body)
        except:
            print(public.get_error_info())

#删除tty1
def remove_tty1():
    file_path = '/etc/systemd/system/getty@tty1.service'
    if not os.path.exists(file_path): return False
    if not os.path.islink(file_path): return False
    if os.readlink(file_path) != '/dev/null': return False
    try:
        os.remove(file_path)
    except:pass


#默认禁用指定PHP函数
def disable_putenv(fun_name):
    try:
        is_set_disable = '/www/server/panel/data/disable_%s' % fun_name
        if os.path.exists(is_set_disable): return True
        php_vs = public.get_php_versions()
        php_ini = "/www/server/php/{0}/etc/php.ini"
        rep = r"disable_functions\s*=\s*.*"
        for pv in php_vs:
            php_ini_path = php_ini.format(pv)
            if not os.path.exists(php_ini_path): continue
            php_ini_body = public.readFile(php_ini_path)
            tmp = re.search(rep,php_ini_body)
            if not tmp: continue
            disable_functions = tmp.group()
            if disable_functions.find(fun_name) != -1: continue
            print(disable_functions)
            php_ini_body = php_ini_body.replace(disable_functions,disable_functions+',%s' % fun_name)
            php_ini_body.find(fun_name)
            public.writeFile(php_ini_path,php_ini_body)
            public.phpReload(pv)
        public.writeFile(is_set_disable,'True')
        return True
    except: return False


#创建计划任务
def set_crond():
    try:
        echo = public.md5(public.md5('renew_lets_ssl_bt'))
        cron_id = public.M('crontab').where('echo=?',(echo,)).getField('id')

        import crontab
        args_obj = public.dict_obj()
        if not cron_id:
            cronPath = public.GetConfigValue('setup_path') + '/cron/' + echo
            shell = public.get_python_bin() + ' /www/server/panel/class/panelLets.py renew_lets_ssl'
            public.writeFile(cronPath,shell)
            args_obj.id = public.M('crontab').add('name,type,where1,where_hour,where_minute,echo,addtime,status,save,backupTo,sType,sName,sBody,urladdress',("Renew the Let's Encrypt certificate",'day','','0','10',echo,time.strftime('%Y-%m-%d %X',time.localtime()),0,'','localhost','toShell','',shell,''))
            crontab.crontab().set_cron_status(args_obj)
        else:
            cron_path = public.get_cron_path()
            if os.path.exists(cron_path):
                cron_s = public.readFile(cron_path)
                if cron_s.find(echo) == -1:
                    public.M('crontab').where('echo=?',(echo,)).setField('status',0)
                    args_obj.id = cron_id
                    crontab.crontab().set_cron_status(args_obj)
    except:
        print(public.get_error_info())


#清理多余的session文件
def clean_session():
    try:
        session_path = r'/dev/shm/session_py' + str(sys.version_info[0])
        if not os.path.exists(session_path): return False
        now_time = time.time()
        p_time = 86400
        old_state = False
        for fname in os.listdir(session_path):
            filename = os.path.join(session_path,fname)
            if not os.path.exists(filename): continue
            modify_time = os.path.getmtime(filename)
            if (now_time - modify_time) > p_time: 
                old_state = True
                break
        if old_state: public.ExecShell("rm -f " + session_path + '/*')
        return True
    except:return False



if __name__ == '__main__':
    control_init()


