# coding: utf-8
# -------------------------------------------------------------------
# aaPanel
# -------------------------------------------------------------------
# Copyright (c) 2015-2017 aaPanel(www.aapanel.com) All rights reserved.
# -------------------------------------------------------------------
# Author: hwliang <hwl@aapanel.com>
# -------------------------------------------------------------------

# ------------------------------
# 网站管理类
# ------------------------------
import re, public, os, sys, shutil, json, hashlib, socket, time
from public.hook_import import hook_import
hook_import()

try:
    import OpenSSL
except:
    os.system("btpip install pyOpenSSL -I")
    import OpenSSL
import base64

try:
    from BTPanel import session
except:
    pass
from panel_redirect_v2 import panelRedirect
import site_dir_auth_v2 as site_dir_auth
from public.validate import Param


class panelSite(panelRedirect):
    siteName = None  # 网站名称
    sitePath = None  # 根目录
    sitePort = None  # 端口
    phpVersion = None  # PHP版本
    setupPath = None  # 安装路径
    isWriteLogs = None  # 是否写日志
    nginx_conf_bak = '/tmp/backup_nginx.conf'
    apache_conf_bak = '/tmp/backup_apache.conf'
    is_ipv6 = False
    conf_dir = '{}/vhost/config'.format(public.get_panel_path())  # 防盗链配置

    def __init__(self):
        self._is_nginx_http3 = None
        self.setupPath = public.get_setup_path()
        path = self.setupPath + '/panel/vhost/nginx'
        if not os.path.exists(path): public.ExecShell("mkdir -p " + path + " && chmod -R 644 " + path)
        path = self.setupPath + '/panel/vhost/apache'
        if not os.path.exists(path): public.ExecShell("mkdir -p " + path + " && chmod -R 644 " + path)
        path = self.setupPath + '/panel/vhost/rewrite'
        if not os.path.exists(path): public.ExecShell("mkdir -p " + path + " && chmod -R 644 " + path)
        path = self.setupPath + '/stop'
        if not os.path.exists(path + '/index.html'):
            public.ExecShell('mkdir -p ' + path)
            public.ExecShell('wget -O ' + path + '/index.html ' + public.get_url() + '/stop_en.html &')
        self.__proxyfile = '{}/data/proxyfile.json'.format(public.get_panel_path())
        self.OldConfigFile()
        if os.path.exists(self.nginx_conf_bak): os.remove(self.nginx_conf_bak)
        if os.path.exists(self.apache_conf_bak): os.remove(self.apache_conf_bak)
        self.is_ipv6 = os.path.exists(self.setupPath + '/panel/data/ipv6.pl')
        sys.setrecursionlimit(1000000)
        try:
            if not os.path.isdir(self.conf_dir):
                os.makedirs(self.conf_dir, 0o755)
        except PermissionError as e:
            public.WriteLog('Access to Information', "{} err: {}".format(self.conf_dir, str(e)))

    # 默认配置文件
    def check_default(self):
        nginx = self.setupPath + '/panel/vhost/nginx'
        httpd = self.setupPath + '/panel/vhost/apache'
        httpd_default = '''<VirtualHost *:80>
    ServerAdmin webmaster@example.com
    DocumentRoot "/www/server/apache/htdocs"
    ServerName bt.default.com
    <Directory "/www/server/apache/htdocs">
        SetOutputFilter DEFLATE
        Options FollowSymLinks
        AllowOverride All
        Order allow,deny
        Allow from all
        DirectoryIndex index.html
    </Directory>
</VirtualHost>'''

        listen_ipv6 = ''
        if self.is_ipv6: listen_ipv6 = "\n    listen [::]:80;"
        nginx_default = '''server
{
    listen 80;%s
    server_name _;
    index index.html;
    root /www/server/nginx/html;
}''' % listen_ipv6
        if not os.path.exists(httpd + '/0.default.conf') and not os.path.exists(
                httpd + '/default.conf'): public.writeFile(httpd + '/0.default.conf', httpd_default)
        if not os.path.exists(nginx + '/0.default.conf') and not os.path.exists(
                nginx + '/default.conf'): public.writeFile(nginx + '/0.default.conf', nginx_default)

    # 添加apache端口
    def apacheAddPort(self, port):
        port = str(port)
        filename = self.setupPath + '/apache/conf/extra/httpd-ssl.conf'
        if os.path.exists(filename):
            ssl_conf = public.readFile(filename)
            if ssl_conf:
                if ssl_conf.find('Listen 443') != -1:
                    ssl_conf = ssl_conf.replace('Listen 443', '')
                    public.writeFile(filename, ssl_conf)

        filename = self.setupPath + '/apache/conf/httpd.conf'
        if not os.path.exists(filename): return
        allConf = public.readFile(filename)
        rep = r"Listen\s+([0-9]+)\n"
        tmp = re.findall(rep, allConf)
        if not tmp: return False
        for key in tmp:
            if key == port: return False

        listen = "\nListen " + tmp[0] + "\n"
        listen_ipv6 = ''
        # if self.is_ipv6: listen_ipv6 = "\nListen [::]:" + port
        allConf = allConf.replace(listen, listen + "Listen " + port + listen_ipv6 + "\n")
        public.writeFile(filename, allConf)
        return True

    # 添加到apache
    def apacheAdd(self):
        import time
        listen = ''
        if self.sitePort != '80': self.apacheAddPort(self.sitePort)
        acc = public.md5(str(time.time()))[0:8]
        try:
            httpdVersion = public.readFile(self.setupPath + '/apache/version.pl').strip()
        except:
            httpdVersion = ""
        if httpdVersion == '2.2':
            vName = ''
            if self.sitePort != '80' and self.sitePort != '443':
                vName = "NameVirtualHost  *:" + self.sitePort + "\n"
            phpConfig = ""
            apaOpt = r"Order allow,deny\n\t\tAllow from all"
        else:
            port_conf = self.sitePort
            # 2.4版本 添加多服务处理
            if public.get_multi_webservice_status() and self.sitePort in ['80','443']:
                port_conf = '8288' if self.sitePort == '80' else '8290'

            vName = ""
            phpConfig = '''
    #PHP
    <FilesMatch \\.php$>
            SetHandler "proxy:%s"
    </FilesMatch>
    ''' % (public.get_php_proxy(self.phpVersion, 'apache'),)
            apaOpt = 'Require all granted'

        conf = r'''%s<VirtualHost *:%s>
    ServerAdmin webmaster@example.com
    DocumentRoot "%s"
    ServerName %s.%s
    ServerAlias %s
    #errorDocument 404 /404.html
    ErrorLog "%s-error_log"
    CustomLog "%s-access_log" combined

    #DENY FILES
     <Files ~ (\.user.ini|\.htaccess|\.git|\.env|\.svn|\.project|LICENSE|README.md)$>
       Order allow,deny
       Deny from all
    </Files>
    %s
    #PATH
    <Directory "%s">
        SetOutputFilter DEFLATE
        Options FollowSymLinks
        AllowOverride All
        %s
        DirectoryIndex index.php index.html index.htm default.php default.html default.htm
    </Directory>
</VirtualHost>''' % (vName, port_conf, self.sitePath, acc, self.siteName, self.siteName,
                     public.GetConfigValue('logs_path') + '/' + self.siteName,
                     public.GetConfigValue('logs_path') + '/' + self.siteName, phpConfig, self.sitePath, apaOpt)

        htaccess = self.sitePath + '/.htaccess'
        if not os.path.exists(htaccess): public.writeFile(htaccess, ' ')
        public.ExecShell('chmod -R 644 ' + htaccess)
        public.ExecShell('chown -R www:www ' + htaccess)

        filename = self.setupPath + '/panel/vhost/apache/' + self.siteName + '.conf'
        public.writeFile(filename, conf)
        return True

    # 添加到nginx
    def nginxAdd(self):
        listen_ipv6 = ''
        if self.is_ipv6: listen_ipv6 = "\n    listen [::]:%s;" % self.sitePort

        conf = r'''server
{{
    listen {listen_port};{listen_ipv6}
    server_name {site_name};
    index index.php index.html index.htm default.php default.htm default.html;
    root {site_path};

    #SSL-START {ssl_start_msg}
    #error_page 404/404.html;
    #SSL-END

    #ERROR-PAGE-START  {err_page_msg}
    error_page 404 /404.html;
    error_page 502 /502.html;
    #ERROR-PAGE-END

    #PHP-INFO-START  {php_info_start}
    include enable-php-{php_version}.conf;
    #PHP-INFO-END

    #REWRITE-START {rewrite_start_msg}
    include {setup_path}/panel/vhost/rewrite/{site_name}.conf;
    #REWRITE-END

    {description}
    location ~ ^/(\.user.ini|\.htaccess|\.git|\.env|\.svn|\.project|LICENSE|README.md)
    {{
        return 404;
    }}

    {description1}
    location ~ \.well-known{{
        allow all;
    }}

    #Prohibit putting sensitive files in certificate verification directory
    if ( $uri ~ "^/\.well-known/.*\.(php|jsp|py|js|css|lua|ts|go|zip|tar\.gz|rar|7z|sql|bak)$" ) {{
        return 403;
    }}

    location ~ .*\.(gif|jpg|jpeg|png|bmp|swf)$
    {{
        expires      30d;
        error_log /dev/null;
        access_log /dev/null;
    }}

    location ~ .*\.(js|css)?$
    {{
        expires      12h;
        error_log /dev/null;
        access_log /dev/null; 
    }}
    access_log  {log_path}/{site_name}.log;
    error_log  {log_path}/{site_name}.error.log;
}}'''.format(
            listen_port=self.sitePort,
            listen_ipv6=listen_ipv6,
            site_path=self.sitePath,
            ssl_start_msg=public.get_msg_gettext(
                'SSL related configuration, do NOT delete or modify the next line of commented-out 404 rules'),
            err_page_msg=public.get_msg_gettext(
                'Error page configuration, allowed to be commented, deleted or modified'),
            php_info_start=public.get_msg_gettext(
                'PHP reference configuration, allowed to be commented, deleted or modified'),
            php_version=self.phpVersion,
            setup_path=self.setupPath,
            rewrite_start_msg=public.get_msg_gettext(
                'URL rewrite rule reference, any modification will invalidate the rewrite rules set by the panel'),
            description=("# Forbidden files or directories"),
            description1=public.get_msg_gettext(
                '# Directory verification related settings for one-click application for SSL certificate'),
            log_path=public.GetConfigValue('logs_path'),
            site_name=self.siteName
        )

        # 写配置文件
        filename = self.setupPath + '/panel/vhost/nginx/' + self.siteName + '.conf'
        public.writeFile(filename, conf)

        # 生成伪静态文件
        urlrewritePath = self.setupPath + '/panel/vhost/rewrite'
        urlrewriteFile = urlrewritePath + '/' + self.siteName + '.conf'
        if not os.path.exists(urlrewritePath): os.makedirs(urlrewritePath)
        open(urlrewriteFile, 'w+').close()
        if not os.path.exists(urlrewritePath):
            public.writeFile(urlrewritePath, '')
        return True

    # 重新生成nginx配置文件
    def rep_site_config(self, get):
        self.siteName = get.siteName
        siteInfo = public.M('sites').where('name=?', (self.siteName,)).field('id,path,port').find()
        siteInfo['domains'] = public.M('domains').where('pid=?', (siteInfo['id'],)).field('name,port').select()
        siteInfo['binding'] = public.M('binding').where('pid=?', (siteInfo['id'],)).field('domain,path').select()

    # openlitespeed
    def openlitespeed_add_site(self, get, init_args=None):
        # 写主配置httpd_config.conf
        # 操作默认监听配置
        if not self.sitePath:
            return_message = public.return_msg_gettext(False, "Not specify parameter [sitePath]")
            del return_message['status']
            return public.return_message(-1, 0, return_message['msg'])
        if init_args:
            self.siteName = init_args['sitename']
            self.phpVersion = init_args['phpv']
            self.sitePath = init_args['rundir']
        conf_dir = self.setupPath + '/panel/vhost/openlitespeed/'
        if not os.path.exists(conf_dir):
            os.makedirs(conf_dir)
        file = conf_dir + self.siteName + '.conf'

        v_h = """
#VHOST_TYPE BT_SITENAME START
virtualhost BT_SITENAME {
vhRoot BT_RUN_PATH
configFile /www/server/panel/vhost/openlitespeed/detail/BT_SITENAME.conf
allowSymbolLink 1
enableScript 1
restrained 1
setUIDMode 0
}
#VHOST_TYPE BT_SITENAME END
"""
        self.old_name = self.siteName
        if hasattr(get, "dirName"):
            self.siteName = self.siteName + "_" + get.dirName
            # sub_dir = self.sitePath + "/" + get.dirName
            v_h = v_h.replace("VHOST_TYPE", "SUBDIR")
            v_h = v_h.replace("BT_SITENAME", self.siteName)
            v_h = v_h.replace("BT_RUN_PATH", self.sitePath)
            # extp_name = self.siteName + "_" + get.dirName
        else:
            self.openlitespeed_domain(get)
            v_h = v_h.replace("VHOST_TYPE", "VHOST")
            v_h = v_h.replace("BT_SITENAME", self.siteName)
            v_h = v_h.replace("BT_RUN_PATH", self.sitePath)
            # extp_name = self.siteName
        public.writeFile(file, v_h, "a+")
        # 写vhost
        conf = '''docRoot                   $VH_ROOT
vhDomain                  $VH_NAME
adminEmails               example@example.com
enableGzip                1
enableIpGeo               1

index  {
  useServer               0
  indexFiles index.php,index.html
}

errorlog /www/wwwlogs/$VH_NAME_ols.error_log {
  useServer               0
  logLevel                ERROR
  rollingSize             10M
}

accesslog /www/wwwlogs/$VH_NAME_ols.access_log {
  useServer               0
  logFormat               '%{X-Forwarded-For}i %h %l %u %t "%r" %>s %b "%{Referer}i" "%{User-Agent}i"'
  logHeaders              5
  rollingSize             10M
  keepDays                10  compressArchive         1
}

scripthandler  {
  add                     lsapi:BT_EXTP_NAME php
}

extprocessor BTSITENAME {
  type                    lsapi
  address                 UDS://tmp/lshttpd/BT_EXTP_NAME.sock
  maxConns                20
  env                     LSAPI_CHILDREN=20
  initTimeout             600
  retryTimeout            0
  persistConn             1
  pcKeepAliveTimeout      1
  respBuffer              0
  autoStart               1
  path                    /usr/local/lsws/lsphpBTPHPV/bin/lsphp
  extUser                 www
  extGroup                www
  memSoftLimit            2047M
  memHardLimit            2047M
  procSoftLimit           400
  procHardLimit           500
}

phpIniOverride  {
php_admin_value open_basedir "/tmp/:BT_RUN_PATH"
}

expires {
    enableExpires           1
    expiresByType           image/*=A43200,text/css=A43200,application/x-javascript=A43200,application/javascript=A43200,font/*=A43200,application/x-font-ttf=A43200
}

rewrite  {
  enable                  1
  autoLoadHtaccess        1
  include /www/server/panel/vhost/openlitespeed/proxy/BTSITENAME/urlrewrite/*.conf
  include /www/server/panel/vhost/apache/redirect/BTSITENAME/*.conf
  include /www/server/panel/vhost/openlitespeed/redirect/BTSITENAME/*.conf
}
include /www/server/panel/vhost/openlitespeed/proxy/BTSITENAME/*.conf
'''
        open_base_path = self.sitePath
        if self.sitePath[-1] != '/':
            open_base_path = self.sitePath + '/'
        conf = conf.replace('BT_RUN_PATH', open_base_path)
        conf = conf.replace('BT_EXTP_NAME', self.siteName)
        conf = conf.replace('BTPHPV', self.phpVersion)
        conf = conf.replace('BTSITENAME', self.siteName)

        # 写配置文件
        conf_dir = self.setupPath + '/panel/vhost/openlitespeed/detail/'
        if not os.path.exists(conf_dir):
            os.makedirs(conf_dir)
        file = conf_dir + self.siteName + '.conf'
        # if hasattr(get,"dirName"):
        #     file = conf_dir + self.siteName +'_'+get.dirName+ '.conf'
        public.writeFile(file, conf)

        # 生成伪静态文件
        # urlrewritePath = self.setupPath + '/panel/vhost/rewrite'
        # urlrewriteFile = urlrewritePath + '/' + self.siteName + '.conf'
        # if not os.path.exists(urlrewritePath): os.makedirs(urlrewritePath)
        # open(urlrewriteFile, 'w+').close()
        return public.return_message(0, 0, True)

    # 上传CSV文件
    # def upload_csv(self, get):
    #     import files
    #     f = files.files()
    #     get.f_path = '/tmp/multiple_website.csv'
    #     result = f.upload(get)
    #     return result

    # 处理CSV内容
    def __process_cvs(self, key):
        import csv
        with open('/tmp/multiple_website.csv') as f:
            f_csv = csv.reader(f)
            # result = [i for i in f_csv]
            return [dict(zip(key, i)) for i in [i for i in f_csv if "FTP" not in i]]

    # 批量创建网站
    def __create_website_mulitiple(self, websites_info, site_path, get):
        create_successfully = {}
        create_failed = {}
        for data in websites_info:
            if not data:
                continue
            try:
                domains = data['website'].split(',')
                website_name = domains[0].split(':')[0]
                data['port'] = '80' if len(domains[0].split(':')) < 2 else domains[0].split(':')[1]
                get.webname = json.dumps({"domain": website_name, "domainlist": domains[1:], "count": 0})
                get.path = data['path'] if 'path' in data and data['path'] != '0' and data[
                    'path'] != '1' else site_path + '/' + website_name
                get.version = data['version'] if 'version' in data and data['version'] != '0' else '00'
                get.ftp = 'true' if 'ftp' in data and data['ftp'] == '1' else 'false'
                get.sql = 'true' if 'sql' in data and data['sql'] == '1' else 'false'
                get.port = data['port'] if 'port' in data else '80'
                get.codeing = 'utf8'
                get.type = 'PHP'
                get.type_id = '0'
                get.ps = ''
                create_other = {}
                create_other['db_status'] = False
                create_other['ftp_status'] = False
                if get.sql == 'true':
                    create_other['db_pass'] = get.datapassword = public.gen_password(16)
                    create_other['db_user'] = get.datauser = website_name.replace('.', '_')
                    create_other['db_status'] = True
                if get.ftp == 'true':
                    create_other['ftp_pass'] = get.ftp_password = public.gen_password(16)
                    create_other['ftp_user'] = get.ftp_username = website_name.replace('.', '_')
                    create_other['ftp_status'] = True
                result = self.AddSite(get, multiple=1)
                if result['status'] == -1:
                    create_failed[domains[0]] = result['message']
                    continue
                create_successfully[domains[0]] = create_other
            except:
                create_failed[domains[0]] = public.lang("There was an error creating, please try again.")
        return_message = {
            'msg': public.get_msg_gettext('Create the website [ {} ] successfully', (','.join(create_successfully),)),
            'error': create_failed,
            'success': create_successfully}
        return public.return_message(0, 0, return_message)

    # 批量创建网站
    def create_website_multiple(self, get):
        '''
            @name 批量创建网站
            @author zhwen<2020-11-26>
            @param create_type txt/csv  txt格式为 “网站名|网站路径|是否创建FTP|是否创建数据库|PHP版本” 每个网站一行
                                                 "aaa.com:88,bbb.com|/www/wwwserver/aaa.com/或1|1/0|1/0|0/73"
                                        csv格式为 “网站名|网站端口|网站路径|PHP版本|是否创建数据库|是否创建FTP”
            @param websites_content     "[[aaa.com|80|/www/wwwserver/aaa.com/|1|1|73]...."
        '''
        # 校验参数
        try:
            get.validate([
                Param('create_type').String(),
                Param('websites_content').String(),

            ], [
                public.validate.trim_filter(),
            ])
        except Exception as ex:
            public.print_log("error info: {}".format(ex))
            return public.return_message(-1, 0, str(ex))

        key = ['website', 'path', 'ftp', 'sql', 'version']
        site_path = public.M('config').getField('sites_path')
        if get.create_type == 'txt':
            websites_info = [dict(zip(key, i)) for i in
                             [i.strip().split('|') for i in json.loads(get.websites_content)]]
        else:
            websites_info = self.__process_cvs(key)
        res = self.__create_website_mulitiple(websites_info, site_path, get)
        public.serviceReload()
        return res

    # 检测enable-php-00.conf
    def check_php_conf(self):
        try:
            file = '/www/server/nginx/conf/enable-php.conf'
            if public.get_webserver() != "nginx":
                return
            if os.path.exists(file):
                return
            php_v = os.listdir('/www/server/php')
            if not php_v:
                return
            conf = public.readFile('/www/server/nginx/conf/enable-php-{}.conf'.format(php_v[0]))
            public.writeFile(file, conf)
        except:
            pass

    # 旧版添加站点，保留
    def AddSite(self, get, multiple=None):
        # 校验参数
        try:
            if not hasattr(get, 'is_create_default_file'):
                get.is_create_default_file = True

            get.validate([
                Param('webname').String(),
                Param('type').String(),
                Param('ps').String(),
                Param('path').String(),
                Param('version').String(),
                Param('sql').String(),
                Param('datapassword').String(),
                Param('codeing').String(),
                Param('port').Integer(),
                Param('type_id').Integer(),
                Param('set_ssl').Integer(),
                Param('force_ssl').Integer(),
                Param('ftp').Bool(),
                Param('is_create_default_file').Bool(),
                Param('parse_list').String(),  # dns auto
            ], [
                public.validate.trim_filter(),
            ])
        except Exception as ex:
            public.print_log("error info: {}".format(ex))
            return public.return_message(-1, 0, str(ex))

        # git部署，测试连接
        if get.get('deploy_type') == 'ssh':
            get.is_create_default_file = False
            from git_tools import GitTools
            git = GitTools()
            # 关闭ssh测试
            # repo = get.get('repo')
            # if not git.test_ssh(repo):
            #     return public.return_message(-1, 0, public.lang('Failed to connect to the remote repository. Please make sure the key is configured correctly!'))

            ok, msg = git.check_webhook_install()
            if not ok:
                return public.return_message(-1, 0, msg)

        parse_list = []
        main_domain = {}
        if hasattr(get, "parse_list"):
            import json
            parse_list = json.loads(get.parse_list)
            if not len(parse_list):
                return public.fail_v2("domain names not found")
            main_domain = parse_list.pop(0)
            get.webname = json.dumps({
                "domain": main_domain.get("domain").strip(),
                "domainlist": [x.get("domain", "") for x in parse_list],
                "count": len(parse_list),
            })

        if get.get('ftp', False):
            # 校验参数
            try:
                get.validate([
                    Param('ftp_username').String(),
                    Param('ftp_password').String(),
                ], [
                    public.validate.trim_filter(),
                ])
            except Exception as ex:
                public.print_log("error info: {}".format(ex))
                return public.return_message(-1, 0, str(ex))

        if not get.path:
            return_message = public.return_msg_gettext(False, "Please fill in the website path")
            del return_message['status']
            return public.return_message(-1, 0, return_message['msg'])
        if get.path == "/":
            return_message = public.return_msg_gettext(False, "The website path cannot be the root directory [/]")
            del return_message['status']
            return public.return_message(-1, 0, return_message['msg'])
        rep_email = r"[\w!#$%&'*+/=?^_`{|}~-]+(?:\.[\w!#$%&'*+/=?^_`{|}~-]+)*@(?:[\w](?:[\w-]*[\w])?\.)+[\w](?:[\w-]*[\w])?"
        if hasattr(get, 'email'):
            if not re.search(rep_email, get.email):
                return_message = public.return_msg_gettext(False, "Please check if the [Email] format correct")
                del return_message['status']
                return public.return_message(-1, 0, return_message['msg'])
        if hasattr(get, 'password') and hasattr(get, 'pw_weak'):
            l = public.check_password(get.password)
            if l == 0 and get.pw_weak == 'off':
                return_message = public.return_msg_gettext(False,
                                                           'Password very weak, if you are sure to use it, please tick [ Allow weak passwords ]')
                del return_message['status']
                return public.return_message(-1, 0, return_message['msg'])
            # 判断Mysql PHP 没有安装不能继续
            if not os.path.exists("/www/server/mysql") or not os.path.exists("/www/server/php"):
                return_message = public.return_msg_gettext(False,
                                                           'Please install Mysql and PHP first!')
                del return_message['status']
                return public.return_message(-1, 0, return_message['msg'])

        self.check_default()

        self.check_php_conf()

        isError = public.checkWebConfig()
        if isError != True:
            return_message = public.return_msg_gettext(False,
                                                       'ERROR: %s<br><br><a style="color:red;">' % public.get_msg_gettext(
                                                           'An error was detected in the configuration file. Please solve it before proceeding') + isError.replace(
                                                           "\n", '<br>') + '</a>')
            del return_message['status']
            return public.return_message(-1, 0, return_message['msg'])

        import json

        get.path = self.__get_site_format_path(get.path)
        if not public.check_site_path(get.path):
            a, c = public.get_sys_path()
            return_message = public.return_msg_gettext(False,
                                                       'Please do not set the website root directory to the system main directory:<br> {}'.format(
                                                           "<br>".join(a + c)))
            del return_message['status']
            return public.return_message(-1, 0, return_message['msg'])

        try:
            siteMenu = json.loads(get.webname)
        except:
            return_message = public.return_msg_gettext(False,
                                                       'The format of the webname parameter is incorrect, it should be a parseable JSON string')
            del return_message['status']
            return public.return_message(-1, 0, return_message['msg'])

        self.siteName = self.ToPunycode(siteMenu['domain'].strip().split(':')[0]).strip().lower()
        self.sitePath = self.ToPunycodePath(self.GetPath(get.path.replace(' ', ''))).strip()
        self.sitePort = get.port.strip().replace(' ', '')

        if self.sitePort == "": get.port = "80"
        if not public.checkPort(self.sitePort):
            return_message = public.return_msg_gettext(False, 'The port is occupied or the port range is incorrect! It should be between 100 and 65535')
            del return_message['status']
            return public.return_message(-1, 0, return_message['msg'])

        for domain in siteMenu['domainlist']:
            if not len(domain.split(':')) == 2:
                continue
            if not public.checkPort(domain.split(':')[1]):
                return_message = public.return_msg_gettext(False,
                                                           'The port is occupied or the port range is incorrect! It should be between 100 and 65535')
                del return_message['status']
                return public.return_message(-1, 0, return_message['msg'])

        if hasattr(get, 'version'):
            self.phpVersion = get.version.replace(' ', '')
        else:
            self.phpVersion = '00'

        if not self.phpVersion: self.phpVersion = '00'

        php_version = self.GetPHPVersion(get, False)
        is_phpv = False
        for php_v in php_version:
            if self.phpVersion == php_v['version']:
                is_phpv = True
                break
        if not is_phpv:
            return_message = public.return_msg_gettext(False, 'Requested PHP version does NOT exist!')
            del return_message['status']
            return public.return_message(-1, 0, return_message['msg'])

        domain = None
        # if siteMenu['count']:
        #    domain            = get.domain.replace(' ','')
        # 表单验证
        if not self.__check_site_path(self.sitePath):
            return_message = public.return_msg_gettext(False,
                                                       'System critical directory cannot be used as site directory')
            del return_message['status']
            return public.return_message(-1, 0, return_message['msg'])
        if len(self.phpVersion) < 2:
            return_message = public.return_msg_gettext(False, 'PHP version cannot be empty')
            del return_message['status']
            return public.return_message(-1, 0, return_message['msg'])
        reg = r"^([\w\-\*]{1,100}\.){1,24}([\w\-]{1,24}|[\w\-]{1,24}\.[\w\-]{1,24})$"
        if not re.match(reg, self.siteName):
            return_message = public.return_msg_gettext(False, 'Format of primary domain is incorrect')
            del return_message['status']
            return public.return_message(-1, 0, return_message['msg'])
        if self.siteName.find('*') != -1:
            return_message = public.return_msg_gettext(False, 'Primary domain cannot be wildcard DNS record')
            del return_message['status']
            return public.return_message(-1, 0, return_message['msg'])
        if self.sitePath[-1] == '.':
            return_message = public.return_msg_gettext(False, 'DIR_END_WITH', ("'.'",))
            del return_message['status']
            return public.return_message(-1, 0, return_message['msg'])

        if not domain: domain = self.siteName

        # 是否重复
        sql = public.M('sites')
        if sql.where("name=?", (self.siteName,)).count():
            return_message = public.return_msg_gettext(False, 'The site you tried to add already exists!')
            del return_message['status']
            return public.return_message(-1, 0, return_message['msg'])

        opid = public.M('domain').where("name=?", (self.siteName,)).getField('pid')

        if opid:
            if public.M('sites').where('id=?', (opid,)).count():
                return_message = public.return_msg_gettext(False, 'The domain you tried to add already exists!')
                del return_message['status']
                return public.return_message(-1, 0, return_message['msg'])

            public.M('domain').where('pid=?', (opid,)).delete()

        if public.M('binding').where('domain=?', (self.siteName,)).count():
            return_message = public.return_msg_gettext(False, 'The domain you tried to add already exists!')
            del return_message['status']
            return public.return_message(-1, 0, return_message['msg'])

        # 创建根目录
        if not os.path.exists(self.sitePath):
            try:
                os.makedirs(self.sitePath)
            except Exception as ex:
                return_message = public.return_msg_gettext(False, 'Failed to create site document root, {}', (ex,))
                del return_message['status']
                return public.return_message(-1, 0, return_message['msg'])
            public.ExecShell('chmod -R 755 ' + self.sitePath)
            public.ExecShell('chown -R www:www ' + self.sitePath)

        # 创建basedir
        self.DelUserInI(self.sitePath)
        userIni = self.sitePath + '/.user.ini'
        if not os.path.exists(userIni):
            public.writeFile(userIni, 'open_basedir=' + self.sitePath + '/:/tmp/')
            public.ExecShell('chmod 644 ' + userIni)
            public.ExecShell('chown root:root ' + userIni)
            public.ExecShell('chattr +i ' + userIni)

        ngx_open_basedir_path = self.setupPath + '/panel/vhost/open_basedir/nginx'
        if not os.path.exists(ngx_open_basedir_path):
            os.makedirs(ngx_open_basedir_path, 384)
        ngx_open_basedir_file = ngx_open_basedir_path + '/{}.conf'.format(self.siteName)
        ngx_open_basedir_body = '''set $bt_safe_dir "open_basedir";
    set $bt_safe_open "{}/:/tmp/";'''.format(self.sitePath)
        public.writeFile(ngx_open_basedir_file, ngx_open_basedir_body)

        # 判断是否需要生成默认文件
        if get.is_create_default_file in [True, 'true', 1, '1']:
            # 创建默认文档
            index = self.sitePath + '/index.html'
            if not os.path.exists(index):
                public.writeFile(index, public.readFile('data/defaultDoc.html'))
                public.ExecShell('chmod -R 644 ' + index)
                public.ExecShell('chown -R www:www ' + index)

            # 创建自定义404页
            doc404 = self.sitePath + '/404.html'
            if not os.path.exists(doc404):
                public.writeFile(doc404, public.readFile('data/404.html'))
                public.ExecShell('chmod -R 644 ' + doc404)
                public.ExecShell('chown -R www:www ' + doc404)

            # 创建自定义502页面
            doc502 = self.sitePath + '/502.html'
            if not os.path.exists(doc502) and os.path.exists('data/502.html'):
                public.writeFile(doc502, public.readFile('data/502.html'))
                public.ExecShell('chmod -R 644 ' + doc502)
                public.ExecShell('chown -R www:www ' + doc502)

        # 写入配置
        result = self.nginxAdd()
        result = self.apacheAdd()
        result = self.openlitespeed_add_site(get)

        # 检查处理结果
        if not result:
            return_message = public.return_msg_gettext(False, 'Failed to add, write configuraton ERROR!')
            del return_message['status']
            return public.return_message(-1, 0, return_message['msg'])
        ps = public.xssencode2(get.ps)
        # 添加放行端口
        if self.sitePort != '80':
            import firewalls
            get.port = self.sitePort
            get.ps = self.siteName
            firewalls.firewalls().AddAcceptPort(get)

        if not hasattr(get, 'type_id'): get.type_id = 0
        if not hasattr(get, 'project_type'): get.project_type = "PHP"
        public.check_domain_cloud(self.siteName)

        # 统计wordpress安装次数
        if get.project_type == 'WP':
            public.count_wp()

        # 写入数据库
        get.pid = sql.table('sites').add('name,path,status,ps,type_id,addtime,project_type', (
            self.siteName, self.sitePath, '1', ps, get.type_id, public.getDate(), get.project_type))
        data = {}
        data['siteId'] = get.pid
        try:
            # 添加更多域名
            for domain in siteMenu['domainlist']:
                get.domain = domain
                get.webname = self.siteName
                get.id = str(get.pid)
                self.AddDomain(get, multiple)

            sql.table('domain').add('pid,name,port,addtime', (get.pid, self.siteName, self.sitePort, public.getDate()))
            data['siteStatus'] = True

            # 添加FTP
            data['ftpStatus'] = False
            if 'ftp' not in get:
                get.ftp = False
            if get.ftp == 'true':
                import ftp
                get.ps = self.siteName
                result = ftp.ftp().AddUser(get)
                if result['status']:
                    data['ftpStatus'] = True
                    data['ftpUser'] = get.ftp_username
                    data['ftpPass'] = get.ftp_password
            # 添加数据库
            data['databaseStatus'] = False
            if 'sql' not in get:
                get.sql = 'false'
            if get.sql == 'true' or get.sql == 'MySQL':
                import database
                # if len(get.datauser) > 16: get.datauser = get.datauser[:16]  # 取消长度限制，由上游控制

                # 生成不重复的数据库用户名
                if get.get('is_clone', False):
                    db_name = get.datauser
                else:
                    db_name = public.ensure_unique_db_name(get.datauser)

                get.name = db_name
                get.db_user = db_name
                get.password = get.datapassword
                get.address = '127.0.0.1'
                get.ps = self.siteName
                result = database.database().AddDatabase(get)
                if result['status']:
                    data['databaseStatus'] = True
                    data['databaseUser'] = get.datauser
                    data['databasePass'] = get.datapassword
                    data['d_id'] = str(public.M('databases').where('pid=?', (get.pid,)).field('id').find()['id'])
                else:
                    # 已经存在数据库 用之前数据库 修改pid public.print_log("存在 更新pid   ---{}".format(result))
                    if result['msg'].find('Database exists') != -1:
                        datauser = get['name'].strip().lower()
                        public.M('databases').where('name=?', (datauser,)).update({"pid": get.pid})
                    data['databaseErrorMsg'] = result['msg']
            if not multiple:
                public.serviceReload()
            data = self._set_ssl(get, data, siteMenu)
            data = self._set_redirect(get, data['message'])
            public.set_module_logs("sys_domain", "AddSite_Manual", 1)
            public.write_log_gettext('Site manager', 'Successfully added site [{}]!', (self.siteName,))
            # ================ dns domain  =======================
            if hasattr(get, "parse_list"):
                try:
                    import threading
                    from ssl_domainModelV2.service import init_sites_dns, generate_sites_task
                    # 添加申请证书, 解析,代理
                    new_list = [main_domain] + parse_list
                    task_obj = generate_sites_task(main_domain, get.pid)
                    task = threading.Thread(
                        target=init_sites_dns,
                        args=(new_list, task_obj)
                    )
                    task.start()
                    public.set_module_logs("sys_domain", "AddSite_Auto", 1)
                except Exception as e:
                    # 删除站点
                    if get.pid is not None:
                        from public import websitemgr
                        websitemgr.remove_site(get.pid)

            # ================ git satrt ======================
            if data['status'] == 0 and get.get('deploy_type') in ['ssh', 'github']:
                dict_obj = {
                    'site_id': data['message']['siteId'],
                    'site_path': get.path,
                    'branch': get.get('branch'),
                    'repo': get.get('repo'),
                    'coverage_data': True,
                    'deploy_script': get.get('deploy_script', ''),
                }
                if get.get('deploy_type') == 'ssh':
                    # 校验目录文件
                    dir_contents = os.listdir(get.path)
                    if not (len(dir_contents) == 2 and '.user.ini' in dir_contents):
                        self.DeleteSite(public.to_dict_obj({'id': dict_obj.get('site_id'), 'webname': self.siteName,'database':1,'path':1,'ftp':1}))
                        return public.return_message(-1,0,'The directory is not empty')

                    data = git.add_key_repository(public.to_dict_obj(dict_obj))
                    # 删除网站
                    if data['status'] != 0 and dict_obj.get('site_id'):
                        self.DeleteSite(public.to_dict_obj({'id': dict_obj.get('site_id'), 'webname': self.siteName,'database':1,'path':1,'ftp':1}))
            # ================ git end ======================

            return data
        except Exception as e:
            return data


    # 添加站点
    def add_sites(self, get, app=None, multiple=None):
        import json
        task_status = os.path.join('/tmp', 'wp_aapanel_deploy.log')
        lock_file = os.path.join('/tmp', 'wp_aapanel_deploy.lock')

        progress_log = {
            "status": 0,
            "parameter_verification": {"ps": public.lang("Verification is underway....."),
                                       "status": 0, "error": '',
                                       "title": public.lang("Parameter verification")},
            "create_website": {"ps": public.lang("{} The website is being created....", get.get('weblog_title', '')),
                               "status": 2, "error": '',
                               "title": public.lang("Create website")},
            "optional_configurations": {"ps": public.lang("Add optional configurations: Database, FTP"),
                                        "status": 2, "error": '',
                                        "title": public.lang("Add optional configurations")},
            "initialize_wp_website": {"ps": public.lang("The wordpress website is being deployed...."),
                                        "status": 2, "error": '',
                                        "title": public.lang("Deploy wordpress")},
        }

        public.writeFile(task_status, json.dumps(progress_log))

        # 校验参数
        try:
            # 获取线程id写进锁文件
            import threading
            thread_id = threading.get_ident()
            with open(lock_file, 'w') as f:
                f.write(str(thread_id))

            # =========wp创建==========
            if get.get('project_type', '') == 'WP2':
                args = get
                main_domain = {}
                if hasattr(get, "wp_parse_list"):
                    wp_parse_list = json.loads(args.wp_parse_list)
                    if not len(wp_parse_list):
                        raise ValueError("domain names not found")
                    main_domain = wp_parse_list.pop(0)
                    get.webname = json.dumps({
                        "domain": main_domain.get("domain").strip(),
                        "domainlist": [x.get("domain", "") for x in wp_parse_list],
                        "count": len(wp_parse_list),
                    })

                from copy import deepcopy
                get = public.to_dict_obj(deepcopy(get.get_items()))
            # ===========================================

            if not hasattr(get, 'is_create_default_file'):
                get.is_create_default_file = True

            get.validate([
                Param('webname').String(),
                Param('type').String(),
                Param('ps').String(),
                Param('path').String(),
                Param('version').String(),
                Param('sql').String(),
                Param('datapassword').String(),
                Param('codeing').String(),
                Param('port').Integer(),
                Param('type_id').Integer(),
                Param('set_ssl').Integer(),
                Param('force_ssl').Integer(),
                Param('ftp').Bool(),
                Param('is_create_default_file').Bool(),
                Param('parse_list').String(),  # dns auto
            ], [
                public.validate.trim_filter(),
            ])

                # parse_list = []
                # main_domain = {}
                # if hasattr(get, "parse_list"):
                #     parse_list = json.loads(get.parse_list)
                #     if not len(parse_list):
                #         raise ValueError("domain names not found")
                #
                #     main_domain = parse_list.pop(0)
                #     get.webname = json.dumps({
                #         "domain": main_domain.get("domain").strip(),
                #         "domainlist": [x.get("domain", "") for x in parse_list],
                #         "count": len(parse_list),
                #     })

            if get.get('ftp', False):
                # 校验参数
                get.validate([
                    Param('ftp_username').String(),
                    Param('ftp_password').String(),
                ], [
                    public.validate.trim_filter(),
                ])

            if not get.path:
                raise ValueError("Please fill in the website path")

            if get.path == "/":
                raise ValueError("The website path cannot be the root directory [/]")

            rep_email = r"[\w!#$%&'*+/=?^_`{|}~-]+(?:\.[\w!#$%&'*+/=?^_`{|}~-]+)*@(?:[\w](?:[\w-]*[\w])?\.)+[\w](?:[\w-]*[\w])?"

            if hasattr(get, 'email'):
                if not re.search(rep_email, get.email):
                    raise ValueError("Please check if the [Email] format correct")

            if hasattr(get, 'password') and hasattr(get, 'pw_weak'):
                l = public.check_password(get.password)
                if l == 0 and get.pw_weak == 'off':
                    raise ValueError(
                        'Password very weak, if you are sure to use it, please tick [ Allow weak passwords ]')

                # 判断Mysql PHP 没有安装不能继续
                if not os.path.exists("/www/server/mysql") or not os.path.exists("/www/server/php"):
                    raise ValueError('Please install Mysql and PHP first!')

            self.check_default()

            self.check_php_conf()

            isError = public.checkWebConfig()
            if isError != True:
                raise ValueError('The website configuration detection failed')

            get.path = self.__get_site_format_path(get.path)
            if not public.check_site_path(get.path):
                a, c = public.get_sys_path()
                raise ValueError(
                    'Please do not set the website root directory to the system main directory:<br> {}'.format(
                        "<br>".join(a + c)))

            try:
                siteMenu = json.loads(get.webname)
            except:
                raise ValueError(
                    'The format of the webname parameter is incorrect, it should be a parseable JSON string')

            self.siteName = self.ToPunycode(siteMenu['domain'].strip().split(':')[0]).strip().lower()
            self.sitePath = self.ToPunycodePath(self.GetPath(get.path.replace(' ', ''))).strip()
            self.sitePort = get.port.strip().replace(' ', '')

            if self.sitePort == "": get.port = "80"
            if not public.checkPort(self.sitePort):
                raise ValueError('The port is occupied or the port range is incorrect! It should be between 100 and 65535')

            for domain in siteMenu['domainlist']:
                if not len(domain.split(':')) == 2:
                    continue
                if not public.checkPort(domain.split(':')[1]):
                    raise ValueError('The port is occupied or the port range is incorrect! It should be between 100 and 65535')

            if hasattr(get, 'version'):
                self.phpVersion = get.version.replace(' ', '')
            else:
                self.phpVersion = '00'

            if not self.phpVersion: self.phpVersion = '00'

            php_version = self.GetPHPVersion(get, False)
            is_phpv = False
            for php_v in php_version:
                if self.phpVersion == php_v['version']:
                    is_phpv = True
                    break
            if not is_phpv:
                raise ValueError('Requested PHP version does NOT exist!')

            domain = None
            # if siteMenu['count']:
            #    domain            = get.domain.replace(' ','')
            # 表单验证
            if not self.__check_site_path(self.sitePath):
                raise ValueError('System critical directory cannot be used as site directory')

            if len(self.phpVersion) < 2:
                raise ValueError('PHP version cannot be empty')

            reg = r"^([\w\-\*]{1,100}\.){1,24}([\w\-]{1,24}|[\w\-]{1,24}\.[\w\-]{1,24})$"
            if not re.match(reg, self.siteName):
                raise ValueError('Format of primary domain is incorrect')

            if self.siteName.find('*') != -1:
                raise ValueError('Primary domain cannot be wildcard DNS record')

            if self.sitePath[-1] == '.':
                raise ValueError('Incorrect website path')

            if not domain: domain = self.siteName

            # 是否重复
            sql = public.M('sites')
            if sql.where("name=?", (self.siteName,)).count():
                raise ValueError('The site you tried to add already exists!')

            opid = public.M('domain').where("name=?", (self.siteName,)).getField('pid')

            if opid:
                if public.M('sites').where('id=?', (opid,)).count():
                    raise ValueError('The domain you tried to add already exists!')

                public.M('domain').where('pid=?', (opid,)).delete()

            if public.M('binding').where('domain=?', (self.siteName,)).count():
                raise ValueError('The domain you tried to add already exists!')

        except Exception as e:
            progress_log['parameter_verification']['ps'] = public.lang('Parameter verification failed')
            progress_log['parameter_verification']['status'] = -1
            progress_log['parameter_verification']['error'] = public.lang('Parameter verification failed: {}', e)
            progress_log['status'] = 1
            public.writeFile(task_status, json.dumps(progress_log))
            public.progress_release_lock(lock_file)
            return

        with app.app_context():
            try:
                progress_log['parameter_verification']['ps'] = public.lang('Parameter verification successful')
                progress_log['parameter_verification']['status'] = 1
                progress_log['create_website']['status'] = 0
                public.writeFile(task_status, json.dumps(progress_log))

                # 创建根目录
                if not os.path.exists(self.sitePath):
                    try:
                        os.makedirs(self.sitePath)
                    except Exception as ex:
                        raise ValueError(f'Failed to create site document root,{ex}')

                    public.ExecShell('chmod -R 755 ' + self.sitePath)
                    public.ExecShell('chown -R www:www ' + self.sitePath)

                # 创建basedir
                self.DelUserInI(self.sitePath)
                userIni = self.sitePath + '/.user.ini'
                if not os.path.exists(userIni):
                    public.writeFile(userIni, 'open_basedir=' + self.sitePath + '/:/tmp/')
                    public.ExecShell('chmod 644 ' + userIni)
                    public.ExecShell('chown root:root ' + userIni)
                    public.ExecShell('chattr +i ' + userIni)

                ngx_open_basedir_path = self.setupPath + '/panel/vhost/open_basedir/nginx'
                if not os.path.exists(ngx_open_basedir_path):
                    os.makedirs(ngx_open_basedir_path, 384)
                ngx_open_basedir_file = ngx_open_basedir_path + '/{}.conf'.format(self.siteName)
                ngx_open_basedir_body = '''set $bt_safe_dir "open_basedir";
            set $bt_safe_open "{}/:/tmp/";'''.format(self.sitePath)
                public.writeFile(ngx_open_basedir_file, ngx_open_basedir_body)

                # 判断是否需要生成默认文件
                if get.is_create_default_file in [True, 'true', 1, '1']:
                    # 创建默认文档
                    index = self.sitePath + '/index.html'
                    if not os.path.exists(index):
                        public.writeFile(index, public.readFile('data/defaultDoc.html'))
                        public.ExecShell('chmod -R 644 ' + index)
                        public.ExecShell('chown -R www:www ' + index)

                    # 创建自定义404页
                    doc404 = self.sitePath + '/404.html'
                    if not os.path.exists(doc404):
                        public.writeFile(doc404, public.readFile('data/404.html'))
                        public.ExecShell('chmod -R 644 ' + doc404)
                        public.ExecShell('chown -R www:www ' + doc404)

                    # 创建自定义502页面
                    doc502 = self.sitePath + '/502.html'
                    if not os.path.exists(doc502) and os.path.exists('data/502.html'):
                        public.writeFile(doc502, public.readFile('data/502.html'))
                        public.ExecShell('chmod -R 644 ' + doc502)
                        public.ExecShell('chown -R www:www ' + doc502)

                # 写入配置
                result = self.nginxAdd()
                result = self.apacheAdd()
                result = self.openlitespeed_add_site(get)

                # 检查处理结果
                if not result:
                    raise ValueError('Failed to add, write configuraton ERROR!')

                ps = public.xssencode2(get.ps)

                # 添加放行端口
                if self.sitePort != '80':
                    import firewalls
                    get.port = self.sitePort
                    get.ps = self.siteName
                    firewalls.firewalls().AddAcceptPort(get)

                if not hasattr(get, 'type_id'): get.type_id = 0
                if not hasattr(get, 'project_type'): get.project_type = "PHP"
                public.check_domain_cloud(self.siteName)
                # 统计wordpress安装次数
                if get.project_type == 'WP':
                    public.count_wp()
                # 写入数据库
                get.pid = sql.table('sites').add('name,path,status,ps,type_id,addtime,project_type', (
                    self.siteName, self.sitePath, '1', ps, get.type_id, public.getDate(), get.project_type))

                # 添加更多域名
                for domain in siteMenu['domainlist']:
                    get.domain = domain
                    get.webname = self.siteName
                    get.id = str(get.pid)
                    self.AddDomain(get, multiple)

                sql.table('domain').add('pid,name,port,addtime',
                                        (get.pid, self.siteName, self.sitePort, public.getDate()))

                data = {}
                data['siteStatus'] = True
                data['siteId'] = get.pid
            except Exception as e:
                # 删除站点
                if get.pid is not None:
                    from public import websitemgr
                    websitemgr.remove_site(get.pid)
                progress_log['create_website']['ps'] = public.lang('Failed to create the website')
                progress_log['create_website']['status'] = -1
                progress_log['create_website']['error'] = public.lang('Failed to create the website: {}', e)
                progress_log['status'] = 1
                public.writeFile(task_status, json.dumps(progress_log))
                public.progress_release_lock(lock_file)
                return

            try:
                progress_log['create_website']['ps'] = public.lang('The website was successfully created')
                progress_log['create_website']['status'] = 1
                progress_log['optional_configurations']['status'] = 0
                public.writeFile(task_status, json.dumps(progress_log))

                # 添加FTP
                data['ftpStatus'] = False
                if 'ftp' not in get:
                    get.ftp = False
                if get.ftp == 'true':
                    import ftp
                    get.ps = self.siteName
                    result = ftp.ftp().AddUser(get)
                    if result['status']:
                        data['ftpStatus'] = True
                        data['ftpUser'] = get.ftp_username
                        data['ftpPass'] = get.ftp_password

                # 添加数据库
                data['databaseStatus'] = False
                if 'sql' not in get:
                    get.sql = 'false'
                if get.sql == 'true' or get.sql == 'MySQL':
                    import database
                    if len(get.datauser) > 16: get.datauser = get.datauser[:16]

                    # 生成不重复的数据库用户名
                    db_name = public.ensure_unique_db_name(get.datauser)

                    get.name = db_name
                    get.db_user = db_name
                    get.password = get.datapassword
                    get.address = '127.0.0.1'
                    get.ps = self.siteName
                    result = database.database().AddDatabase(get)
                    if result['status']:
                        data['databaseStatus'] = True
                        data['databaseUser'] = get.datauser
                        data['databasePass'] = get.datapassword
                        data['d_id'] = str(public.M('databases').where('pid=?', (get.pid,)).field('id').find()['id'])
                    else:
                        # 已经存在数据库 用之前数据库 修改pid public.print_log("存在 更新pid   ---{}".format(result))
                        if result['msg'].find('Database exists') != -1:
                            datauser = get['name'].strip().lower()
                            public.M('databases').where('name=?', (datauser,)).update({"pid": get.pid})
                        data['databaseErrorMsg'] = result['msg']

                if not multiple:
                    public.serviceReload()
                data = self._set_ssl(get, data, siteMenu)
                data = self._set_redirect(get, data['message'])
                public.set_module_logs("sys_domain", "AddSite_Manual", 1)
                public.write_log_gettext('Site manager', 'Successfully added site [{}]!', (self.siteName,))
                if get.get('project_type', '') == 'WP2':

                    if int(data.get('status', 0)) == 0:
                        data = data.get('message', {})

                        if int(data.get('databaseStatus')) != 1:
                            raise ValueError(public.lang("Database creation failed. Please check mysql running status and try again. {}".format(data.get('databaseErrorMsg', ''))))

                # # ================ dns domain  =======================
                #
                # if hasattr(get, "parse_list"):
                #     try:
                #         import threading
                #         from ssl_domainModelV2.service import init_sites_dns, generate_sites_task
                #         # 添加申请证书, 解析,代理
                #         new_list = [main_domain] + parse_list
                #         task_obj = generate_sites_task(main_domain, get.pid)
                #         task = threading.Thread(
                #             target=init_sites_dns,
                #             args=(new_list, task_obj)
                #         )
                #         task.start()
                #         public.set_module_logs("sys_domain", "AddSite_Auto", 1)
                #     except Exception as e:
                #         import traceback
                #         public.print_log(e)

                # ====================================wp创建======================================
            except Exception as e:
                # 删除站点
                if get.pid is not None:
                    from public import websitemgr
                    websitemgr.remove_site(get.pid)
                progress_log['optional_configurations']['ps'] = public.lang(
                    'Failed to create an optional configuration')
                progress_log['optional_configurations']['status'] = -1
                progress_log['optional_configurations']['error'] = public.lang('Failed: {}', e)
                progress_log['status'] = 1
                public.writeFile(task_status, json.dumps(progress_log))
                public.progress_release_lock(lock_file)
                return data

            try:
                progress_log['optional_configurations']['ps'] = public.lang('Added successfully')
                progress_log['optional_configurations']['status'] = 1
                progress_log['initialize_wp_website']['status'] = 0
                public.writeFile(task_status, json.dumps(progress_log))
                if get.get('project_type', '') == 'WP2':
                        result = self.deploy_wp(public.to_dict_obj({
                            'domain': json.loads(args.webname).get('domain', ''),
                            'weblog_title': args.weblog_title,
                            'language': args.get('language', ''),
                            'php_version': args.version,
                            'user_name': args.user_name,
                            'admin_password': args.password,
                            'pw_weak': args.pw_weak,
                            'admin_email': args.email,
                            'prefix': args.prefix,
                            'enable_cache': args.enable_cache,
                            'd_id': data.get('d_id', 0),
                            's_id': data.get('siteId', 0),
                            'enable_whl': args.get('enable_whl', 0),
                            'whl_page': args.get('whl_page', 'login'),
                            'whl_redirect_admin': args.get('whl_redirect_admin', '404'),
                            'package_version': args.get('package_version', None),
                        }))
                        if result['status'] == -1:
                            raise ValueError(result['message']['result'])

                        # ==================== domain dns ======================
                        if hasattr(args, "wp_parse_list") and result.get("status", 0) == 0:
                            try:
                                import threading
                                from ssl_domainModelV2.service import init_sites_dns, generate_sites_task
                                site_id = data.get("siteId", 0)
                                task_obj = generate_sites_task(main_domain, site_id)
                                task = threading.Thread(
                                    target=init_sites_dns,
                                    args=([main_domain], task_obj)
                                )
                                task.start()
                                public.set_module_logs("sys_domain", "AddSite_Auto", 1)
                            except Exception as e:
                                import traceback
                                public.print_log(e)
                                public.print_log(f"error, {e}")
                # ==============================================================================

                #多服务下默认为ols
                if public.get_multi_webservice_status():
                    dict_obj = public.to_dict_obj({'site_id' : data.get('siteId', 0),'service_type' : 'openlitespeed'})
                    self.switch_webservice(dict_obj)

                progress_log['initialize_wp_website']['ps'] = public.lang('Success')
                progress_log['initialize_wp_website']['status'] = 1
                progress_log['status'] = 1
                public.writeFile(task_status, json.dumps(progress_log))
                public.progress_release_lock(lock_file)
                return data
            except Exception as e:
                # 删除站点
                if get.pid is not None:
                    from public import websitemgr
                    websitemgr.remove_site(get.pid)
                progress_log['initialize_wp_website']['ps'] = public.lang('wordpress initialization failed')
                progress_log['initialize_wp_website']['status'] = -1
                progress_log['initialize_wp_website']['error'] = public.lang('Failed: {}', e)
                progress_log['status'] = 1
                public.writeFile(task_status, json.dumps(progress_log))
                public.progress_release_lock(lock_file)
                return data


    # 添加WP站点
    def AddWPSite(self, args: public.dict_obj):
        # 参数验证
        try:
            args.validate([
                Param('webname').String(),
                Param('type').String(),
                Param('ps').String(),
                Param('path').String(),
                Param('version').String(),
                Param('sql').String(),
                Param('datauser').String(),
                Param('datapassword').String(),
                Param('codeing').String(),
                Param('port').Integer(),
                Param('type_id').Integer(),
                Param('set_ssl').Integer(),
                Param('force_ssl').Integer(),
                Param('ftp').Bool(),
                Param('weblog_title').Require().Xss(),
                Param('language').Require(),
                Param('user_name').Require().Xss(),
                Param('email').Require().Email(),
                Param('pw_weak').Require().String('in', ['on', 'off']),
                Param('password').Require(),
                Param('prefix').Require().Xss(),
                Param('enable_cache').Require().Integer(),
                Param('enable_whl').Integer(),
                Param('whl_page').SafePath(),
                Param('whl_redirect_admin').SafePath(),
                Param('package_version').String(),
                Param('wp_parse_list').String(),  # dns auto
            ], [
                public.validate.trim_filter(),
            ])
        except Exception as ex:
            public.print_log("error info: {}".format(ex))
            return public.return_message(-1, 0, str(ex))

        from flask import Flask
        app = Flask(__name__)

        lock_file = os.path.join('/tmp', 'wp_aapanel_deploy.lock')

        if not public.progress_acquire_lock(lock_file):
            return public.return_message(-1, 0, public.lang(
                'Other sites are being deployed. Please wait for the task to complete!'))

        from concurrent.futures import ThreadPoolExecutor

        # 创建单线程池
        thread = ThreadPoolExecutor(max_workers=1)
        thread.submit(self.add_sites, args, app)

        return public.return_message(0, 0, public.lang('Successful startup!'))

    def _set_redirect(self, get, data):
        try:
            if not hasattr(get, 'redirect') and not get.redirect:
                data['redirect'] = False
                return public.return_message(0, 0, data)
            import panel_redirect_v2 as panelRedirect
            get.redirectdomain = json.dumps([get.redirect])
            get.sitename = get.webname
            get.redirectname = 'Default'
            get.redirecttype = '301'
            get.holdpath = '1'
            get.type = '1'
            get.domainorpath = 'domain'
            get.redirectpath = ''
            if data['ssl']:
                get.tourl = 'https://{}'.format(get.tourl)
            else:
                get.tourl = 'http://{}'.format(get.tourl)
            panelRedirect.panelRedirect().CreateRedirect(get)
            data['redirect'] = True
        except:
            data['redirect'] = str(public.get_error_info())
            data['redirect'] = True
        return public.return_message(0, 0, data)

    def _set_ssl(self, get, data, siteMenu):
        try:
            if get.set_ssl != '1':
                data['ssl'] = False
                return public.return_message(0, 0, data)
            import acme_v2
            ssl_domain = siteMenu['domainlist']
            ssl_domain.append(self.siteName)
            get.id = str(get.pid)
            get.auth_to = str(get.pid)
            get.auth_type = 'http'
            get.auto_wildcard = ''
            get.domains = json.dumps(ssl_domain)
            result = acme_v2.acme_v2().apply_cert_api(get)
            get.type = '1'
            get.siteName = self.siteName
            get.key = result['private_key']
            get.csr = result['cert'] + result['root']
            self.SetSSL(get)
            data['ssl'] = True
            if hasattr(get, 'force_ssl') and get.force_ssl == '1':
                get.siteName = self.siteName
                self.HttpToHttps(get)
        except:
            data['ssl'] = str(public.get_error_info())
        return public.return_message(0, 0, data)

    def __get_site_format_path(self, path):
        path = path.replace('//', '/')
        if path[-1:] == '/':
            path = path[:-1]
        return path

    def __check_site_path(self, path):
        path = self.__get_site_format_path(path)
        other_path = public.M('config').where("id=?", ('1',)).field('sites_path,backup_path').find()
        if path == other_path['sites_path'] or path == other_path['backup_path']: return False
        return True

    def delete_website_multiple(self, get):
        '''
            @name 批量删除网站
            @author zhwen<2020-11-17>
            @param sites_id "1,2"
            @param ftp 0/1
            @param database 0/1
            @param  path 0/1
        '''
        sites_id = get.sites_id.split(',')
        del_successfully = []
        del_failed = {}
        for site_id in sites_id:
            get.id = site_id
            get.webname = public.M('sites').where("id=?", (site_id,)).getField('name')
            if not get.webname:
                continue
            try:
                self.DeleteSite(get, multiple=1)
                del_successfully.append(get.webname)
            except:
                del_failed[get.webname] = public.lang("There was an error deleting, please try again.")
                pass
        public.serviceReload()
        return_message = {
            'msg': public.get_msg_gettext('Delete website [{}] successfully', (','.join(del_successfully),)),
            'error': del_failed,
            'success': del_successfully}

        return public.return_message(0, 0, return_message)

    # 删除站点
    def DeleteSite(self, get, multiple=None):
        # 校验参数
        try:
            get.validate([
                Param('webname').String(),
                Param('id').Integer(),
                Param('ftp').Integer(),
                Param('database').Integer(),
                Param('path').Integer(),

            ], [
                public.validate.trim_filter(),
            ])
        except Exception as ex:
            public.print_log("error info: {}".format(ex))
            return public.return_message(-1, 0, str(ex))

        proxyconf = self.__read_config(self.__proxyfile)
        id = get.id
        if public.M('sites').where('id=?', (id,)).count() < 1:
            return_message = public.return_msg_gettext(False, 'Specified site does NOT exist')
            del return_message['status']
            return public.return_message(0, 0, return_message['msg'])
        siteName = get.webname
        get.siteName = siteName
        self.CloseTomcat(get)
        # 删除反向代理
        for i in range(len(proxyconf) - 1, -1, -1):
            if proxyconf[i]["sitename"] == siteName:
                del proxyconf[i]
        self.__write_config(self.__proxyfile, proxyconf)

        m_path = self.setupPath + '/panel/vhost/nginx/proxy/' + siteName
        if os.path.exists(m_path): public.ExecShell("rm -rf %s" % m_path)

        m_path = self.setupPath + '/panel/vhost/apache/proxy/' + siteName
        if os.path.exists(m_path): public.ExecShell("rm -rf %s" % m_path)

        # 删除目录保护
        _dir_aith_file = "%s/panel/data/site_dir_auth.json" % self.setupPath
        _dir_aith_conf = public.readFile(_dir_aith_file)
        if _dir_aith_conf:
            try:
                _dir_aith_conf = json.loads(_dir_aith_conf)
                if siteName in _dir_aith_conf:
                    del (_dir_aith_conf[siteName])
            except:
                pass
        self.__write_config(_dir_aith_file, _dir_aith_conf)

        dir_aith_path = self.setupPath + '/panel/vhost/nginx/dir_auth/' + siteName
        if os.path.exists(dir_aith_path): public.ExecShell("rm -rf %s" % dir_aith_path)

        dir_aith_path = self.setupPath + '/panel/vhost/apache/dir_auth/' + siteName
        if os.path.exists(dir_aith_path): public.ExecShell("rm -rf %s" % dir_aith_path)

        # 删除重定向
        __redirectfile = "%s/panel/data/redirect.conf" % self.setupPath
        redirectconf = self.__read_config(__redirectfile)
        for i in range(len(redirectconf) - 1, -1, -1):
            if redirectconf[i]["sitename"] == siteName:
                del redirectconf[i]
        self.__write_config(__redirectfile, redirectconf)
        m_path = self.setupPath + '/panel/vhost/nginx/redirect/' + siteName
        if os.path.exists(m_path): public.ExecShell("rm -rf %s" % m_path)
        m_path = self.setupPath + '/panel/vhost/apache/redirect/' + siteName
        if os.path.exists(m_path): public.ExecShell("rm -rf %s" % m_path)

        # 删除配置文件
        confPath = self.setupPath + '/panel/vhost/nginx/' + siteName + '.conf'
        if os.path.exists(confPath): os.remove(confPath)

        # 删除多服务切换备份文件
        conf_bar= self.setupPath + '/panel/vhost/nginx/' + siteName + '.conf.bar.bar'
        if os.path.exists(conf_bar): os.remove(conf_bar)

        confPath = self.setupPath + '/panel/vhost/apache/' + siteName + '.conf'
        if os.path.exists(confPath): os.remove(confPath)
        open_basedir_file = self.setupPath + '/panel/vhost/open_basedir/nginx/' + siteName + '.conf'
        if os.path.exists(open_basedir_file): os.remove(open_basedir_file)

        # 删除openlitespeed配置
        vhost_file = "/www/server/panel/vhost/openlitespeed/{}.conf".format(siteName)
        if os.path.exists(vhost_file):
            public.ExecShell('rm -f {}*'.format(vhost_file))
        vhost_detail_file = "/www/server/panel/vhost/openlitespeed/detail/{}.conf".format(siteName)
        if os.path.exists(vhost_detail_file):
            public.ExecShell('rm -f {}*'.format(vhost_detail_file))
        vhost_ssl_file = "/www/server/panel/vhost/openlitespeed/detail/ssl/{}.conf".format(siteName)
        if os.path.exists(vhost_ssl_file):
            public.ExecShell('rm -f {}*'.format(vhost_ssl_file))
        vhost_sub_file = "/www/server/panel/vhost/openlitespeed/detail/{}_sub.conf".format(siteName)
        if os.path.exists(vhost_sub_file):
            public.ExecShell('rm -f {}*'.format(vhost_sub_file))
        vhost_redirect_file = "/www/server/panel/vhost/openlitespeed/redirect/{}".format(siteName)
        if os.path.exists(vhost_redirect_file):
            public.ExecShell('rm -rf {}*'.format(vhost_redirect_file))
        vhost_proxy_file = "/www/server/panel/vhost/openlitespeed/proxy/{}".format(siteName)
        if os.path.exists(vhost_proxy_file):
            public.ExecShell('rm -rf {}*'.format(vhost_proxy_file))

        # 删除免费版监控报表站点配置文件
        site_total_dir = "/www/server/panel/vhost/nginx/extension/{}".format(siteName)
        if os.path.exists(site_total_dir):
            public.ExecShell('rm -rf {}'.format(site_total_dir))

        # 删除openlitespeed监听配置
        self._del_ols_listen_conf(siteName)

        # 删除伪静态文件
        # filename = confPath+'/rewrite/'+siteName+'.conf'
        filename = '/www/server/panel/vhost/rewrite/' + siteName + '.conf'
        if os.path.exists(filename):
            os.remove(filename)
            public.ExecShell("rm -f " + confPath + '/rewrite/' + siteName + "_*")

        # 删除日志文件
        filename = public.GetConfigValue('logs_path') + '/' + siteName + '*'
        public.ExecShell("rm -f " + filename)

        # 删除证书
        # crtPath = '/etc/letsencrypt/live/'+siteName
        # if os.path.exists(crtPath):
        #    import shutil
        #    shutil.rmtree(crtPath)

        # 删除日志
        public.ExecShell("rm -f " + public.GetConfigValue('logs_path') + '/' + siteName + "-*")

        # 删除备份
        # public.ExecShell("rm -f "+session['config']['backup_path']+'/site/'+siteName+'_*')

        # 删除根目录
        if 'path' in get:
            if get.path == '1':
                import files_v2 as files
                get.path = self.__get_site_format_path(public.M('sites').where("id=?", (id,)).getField('path'))
                if self.__check_site_path(get.path):
                    if public.M('sites').where("path=?", (get.path,)).count() < 2:
                        files.files().DeleteDir(get)
                get.path = '1'

        # 重载配置
        if not multiple:
            public.serviceReload()

        # 从数据库删除
        public.M('sites').where("id=?", (id,)).delete()
        public.M('binding').where("pid=?", (id,)).delete()
        public.M('domain').where("pid=?", (id,)).delete()
        public.M('wordpress_onekey').where("s_id=?", (id,)).delete()
        # 删除git数据
        from git_tools import GitTools
        GitTools().del_site_git(public.to_dict_obj({'site_id': id}))
        public.write_log_gettext('Site manager', 'Successfully deleted site {}!', (siteName,))

        # 是否删除关联数据库
        if hasattr(get, 'database'):
            if get.database == '1':
                find = public.M('databases').where("pid=?", (id,)).field('id,name').find()
                if find:
                    import database_v2 as database
                    get.name = find['name']
                    get.id = find['id']
                    database.database().DeleteDatabase(get)

        # 是否删除关联FTP
        if hasattr(get, 'ftp'):
            if get.ftp == '1':
                find = public.M('ftps').where("pid=?", (id,)).field('id,name').find()
                if find:
                    import ftp_v2 as ftp
                    get.username = find['name']
                    get.id = find['id']
                    ftp.ftp().DeleteUser(get)
        return_message = public.return_msg_gettext(True, 'Successfully deleted site!')
        del return_message['status']
        return public.return_message(0, 0, return_message['msg'])

    def _del_ols_listen_conf(self, sitename):
        conf_dir = '/www/server/panel/vhost/openlitespeed/listen/'
        if not os.path.exists(conf_dir):
            return False
        for i in os.listdir(conf_dir):
            file_name = conf_dir + i
            if os.path.isdir(file_name):
                continue
            conf = public.readFile(file_name)
            if not conf:
                continue
            map_rep = r'map\s+{}.*'.format(sitename)
            conf = re.sub(map_rep, '', conf)
            if "map" not in conf:
                public.ExecShell('rm -f {}*'.format(file_name))
                continue
            public.writeFile(file_name, conf)

    # 域名编码转换
    def ToPunycode(self, domain):
        import re
        if sys.version_info[0] == 2: domain = domain.encode('utf8')
        tmp = domain.split('.')
        newdomain = ''
        for dkey in tmp:
            if dkey == '*': continue
            # 匹配非ascii字符
            match = re.search(u"[\x80-\xff]+", dkey)
            if not match: match = re.search(u"[\u4e00-\u9fa5]+", dkey)
            if not match:
                newdomain += dkey + '.'
            else:
                if sys.version_info[0] == 2:
                    newdomain += 'xn--' + dkey.decode('utf-8').encode('punycode') + '.'
                else:
                    newdomain += 'xn--' + dkey.encode('punycode').decode('utf-8') + '.'
        if tmp[0] == '*': newdomain = "*." + newdomain
        return newdomain[0:-1]

    # 中文路径处理
    def ToPunycodePath(self, path):
        if sys.version_info[0] == 2: path = path.encode('utf-8')
        if os.path.exists(path): return path
        import re
        match = re.search(u"[\x80-\xff]+", path)
        if not match: match = re.search(u"[\u4e00-\u9fa5]+", path)
        if not match: return path
        npath = ''
        for ph in path.split('/'):
            npath += '/' + self.ToPunycode(ph)
        return npath.replace('//', '/')

    def export_domains(self, args):
        '''
            @name 导出域名列表
            @author hwliang<2020-10-27>
            @param args<dict_obj>{
                siteName: string<网站名称>
            }
            @return string
        '''

        pid = public.M('sites').where('name=?', args.siteName).getField('id')
        domains = public.M('domain').where('pid=?', pid).field('name,port').select()
        text_data = []
        for domain in domains:
            text_data.append("{}:{}".format(domain['name'], domain['port']))
        data = "\n".join(text_data)
        return public.send_file(data, '{}_domains'.format(args.siteName))

    def import_domains(self, args):
        '''
            @name 导入域名
            @author hwliang<2020-10-27>
            @param args<dict_obj>{
                siteName: string<网站名称>
                domains: string<域名列表> 每行一个 格式： 域名:端口
            }
            @return string
        '''

        domains_tmp = args.domains.split("\n")
        get = public.dict_obj()
        get.webname = args.siteName
        get.id = public.M('sites').where('name=?', args.siteName).getField('id')
        domains = []
        for domain in domains_tmp:
            if public.M('domain').where('name=?', domain.split(':')[0]).count():
                continue
            domains.append(domain)

        get.domain = ','.join(domains)
        return self.AddDomain(get)

        # 添加域名

    def AddDomain(self, get, multiple=None):
        # 校验参数
        try:
            get.validate([
                Param('webname').String(),
                Param('domain').String(),
                Param('id').Integer(),

            ], [
                public.validate.trim_filter(),
            ])
        except Exception as ex:
            public.print_log("error info: {}".format(ex))
            return public.return_message(-1, 0, str(ex))

        # 检查配置文件
        isError = public.checkWebConfig()
        if isError != True:
            return public.return_message(-1, 0, 'ERROR: %s<br><br><a style="color:red;">' % public.get_msg_gettext(
                'An error was detected in the configuration file. Please solve it before proceeding') + isError.replace(
                "\n", '<br>') + '</a>')

        if not 'domain' in get: return public.return_message(-1, 0, public.lang("Please enter the host domain name"))
        if len(get.domain) < 3: return public.return_message(-1, 0, public.lang("Domain cannot be empty!"))
        domains = get.domain.replace(' ', '').split(',')

        for domain in domains:
            if domain == "": continue
            domain = domain.strip().split(':')
            get.domain = self.ToPunycode(domain[0]).lower()
            get.port = '80'
            # 判断通配符域名格式
            if get.domain.find('*') != -1 and get.domain.find('*.') == -1:
                return public.return_message(-1, 0, public.lang("Domain name format is incorrect!"))

            # 判断域名格式
            reg = r"^([\w\-\*]{1,100}\.){1,24}([\w\-]{1,24}|[\w\-]{1,24}\.[\w\-]{1,24})$"
            if not re.match(reg, get.domain): return public.return_message(-1, 0, public.lang("Format of domain is invalid!"))

            # 获取自定义端口
            if len(domain) == 2:
                get.port = domain[1]
            if get.port == "": get.port = "80"

            # 判断端口是否合法
            if not public.checkPort(get.port):
                if get.port in ['21', '25', '443', '8080', '888', '999', '8888', '8443', '7800', '8188', '8189', '8288', '8289', '8290']:
                    return public.return_message(-1, 0, public.lang("Do not use the ports of the panel service!"))
                return public.return_message(-1, 0, public.lang("The port is occupied or the port range is incorrect! It should be between 100 and 65535"))
            # 检查域名是否存在
            sql = public.M('domain')
            opid = sql.where("name=? AND (port=? OR pid=?)", (get.domain, get.port, get.id)).getField('pid')
            if opid:
                siteName = public.M('sites').where('id=?', (opid,)).getField('name')
                if siteName:
                    return public.return_message(-1, 0,
                                                 'The specified domain name has been bound by the website [{}]'.format(
                                                     siteName))
                sql.where('pid=?', (opid,)).delete()
            opid = public.M('binding').where('domain=?', (get.domain,)).getField('pid')
            if opid:
                siteName = public.M('sites').where('id=?', (opid,)).getField('name')
                return public.return_message(-1, 0,
                                             'The specified domain name has been bound by a subdirectory of the website [{}]!'.format(
                                                 siteName))

            # 写配置文件
            self.NginxDomain(get)
            try:
                self.ApacheDomain(get)
                self.openlitespeed_domain(get)
                if self._check_ols_ssl(get.webname):
                    get.port = '443'
                    self.openlitespeed_domain(get)
                    get.port = '80'
            except:
                pass

            # 检查实际端口
            if len(domain) == 2: get.port = domain[1]

            # 添加放行端口
            if get.port != '80':
                import firewalls
                get.ps = get.domain
                firewalls.firewalls().AddAcceptPort(get)

            # 重载webserver服务
            if not multiple:
                public.serviceReload()
            full_domain = get.domain
            if not get.port in ['80', '443']: full_domain += ':' + get.port
            public.check_domain_cloud(full_domain)
            public.write_log_gettext('Site manager', 'Site [{}] added domain [{}] successfully!',
                                     (get.webname, get.domain))
            sql.table('domain').add('pid,name,port,addtime', (get.id, get.domain, get.port, public.getDate()))

        return public.return_message(0, 0, public.lang("Successfully added site!"))

    # 判断ols_ssl是否已经设置
    def _check_ols_ssl(self, webname):
        conf = public.readFile('/www/server/panel/vhost/openlitespeed/listen/443.conf')
        if conf and webname in conf:
            return True
        return False

    # 添加openlitespeed 80端口监听
    def openlitespeed_set_80_domain(self, get, conf):
        rep = r'map\s+{}.*'.format(get.webname)
        domains = get.webname.strip().split(',')
        if conf:
            map_tmp = re.search(rep, conf)
            if map_tmp:
                map_tmp = map_tmp.group()
                domains = map_tmp.strip().split(',')
                if not public.inArray(domains, get.domain):
                    new_map = '{},{}'.format(conf, get.domain)
                    conf = re.sub(rep, new_map, conf)
            else:
                map_tmp = '\tmap\t{d} {d}\n'.format(d=domains[0])
                listen_rep = r"secure\s*0"
                conf = re.sub(listen_rep, "secure 0\n" + map_tmp, conf)
            return public.return_message(0, 0, conf)

        else:
            rep_default = 'listener\\s+Default\\{(\n|[\\s\\w\\*\\:\\#\\.\\,])*'
            tmp = re.search(rep_default, conf)
            # domains = get.webname.strip().split(',')
            if tmp:
                tmp = tmp.group()
                new_map = '\tmap\t{d} {d}\n'.format(d=domains[0])
                tmp += new_map
                conf = re.sub(rep_default, tmp, conf)
        return public.return_message(0, 0, conf)

    # openlitespeed写域名配置
    def openlitespeed_domain(self, get):
        listen_dir = '/www/server/panel/vhost/openlitespeed/listen/'
        if not os.path.exists(listen_dir):
            os.makedirs(listen_dir)
        listen_file = listen_dir + get.port + ".conf"
        listen_conf = public.readFile(listen_file)
        try:
            get.webname = json.loads(get.webname)
            get.domain = str(get.webname['domain']).replace('\r', '').lower()
            get.webname = str(get.domain) + "," + ",".join(map(lambda x: str(x).lower(), list(get.webname["domainlist"])))
            if get.webname[-1] == ',':
                get.webname = get.webname[:-1]
        except:
            pass
        if listen_conf:
            # 添加域名
            rep = r'map\s+{}.*'.format(get.webname)
            map_tmp = re.search(rep, listen_conf)
            if map_tmp:
                map_tmp = map_tmp.group()
                domains = map_tmp.strip().split(',')
                if not public.inArray(domains, get.domain):
                    new_map = '{},{}'.format(map_tmp, get.domain)
                    listen_conf = re.sub(rep, new_map, listen_conf)
            else:
                domains = get.webname.strip().split(',')
                map_tmp = '\tmap\t{d} {d}'.format(d=domains[0])
                listen_rep = r"secure\s*0"
                listen_conf = re.sub(listen_rep, "secure 0\n" + map_tmp, listen_conf)
        else:
            Default_port = get.port
            listen_conf = """
listener Default%s{
    address *:%s
    secure 0
    map %s %s
}
""" % (Default_port, get.port, get.webname, get.domain)
        # 保存配置文件
        public.writeFile(listen_file, listen_conf)

        # 多服务下仅添加80
        if public.get_multi_webservice_status() and get.port != '80':
            if os.path.exists(listen_file):
                shutil.move(listen_file, listen_file + '.barduo')
                get.port = '80'
                self.openlitespeed_domain(get) # 插入80端口
        return public.return_message(0, 0, True)

    # Nginx写域名配置
    def NginxDomain(self, get):
        file = self.setupPath + '/panel/vhost/nginx/' + get.webname + '.conf'
        conf = public.readFile(file)
        if not conf: return public.return_message(-1, 0, 'domains file not exists:' + file)
        # 添加域名
        rep = r"server_name\s*(.*);"
        tmp = re.search(rep, conf).group()
        domains = tmp.replace(';', '').strip().split(' ')
        if not public.inArray(domains, get.domain):
            newServerName = tmp.replace(';', ' ' + get.domain + ';')
            conf = conf.replace(tmp, newServerName)

        # 添加端口
        rep = r"listen\s+[\[\]\:]*([0-9]+).*;"
        tmp = re.findall(rep, conf)
        if not public.inArray(tmp, get.port):
            listen = re.search(rep, conf).group()
            listen_ipv6 = ''
            if self.is_ipv6: listen_ipv6 = "\n\t\tlisten [::]:" + get.port + ';'
            conf = conf.replace(listen, listen + "\n\t\tlisten " + get.port + ';' + listen_ipv6)
        # 保存配置文件
        public.writeFile(file, conf)
        return public.return_message(0, 0, True)

    # Apache写域名配置
    def ApacheDomain(self, get):
        file = self.setupPath + '/panel/vhost/apache/' + get.webname + '.conf'
        conf = public.readFile(file)
        if not conf: return public.return_message(-1, 0, 'domains file not exists:' + file)
        ssl_port = 443
        port = get.port
        siteName = get.webname
        newDomain = get.domain
        find = public.M('sites').where("id=?", (get.id,)).field('id,name,path,service_type').find()
        sitePath = find['path']
        siteIndex = 'index.php index.html index.htm default.php default.html default.htm'
        webservice_status = public.get_multi_webservice_status()

        # 开启多服务后, 兼容端口
        if port == '80' and webservice_status:
            port = '8288'

        if webservice_status and port == '443':
            ssl_port = '8290'

        # 添加域名
        if conf.find('<VirtualHost *:' + port + '>') != -1:
            repV = r"<VirtualHost\s+\*\:" + port + ">(.|\n)*</VirtualHost>"
            domainV = re.search(repV, conf).group()
            rep = r"ServerAlias\s*(.*)\n"
            tmp = re.search(rep, domainV).group(0)
            domains = tmp.strip().split(' ')
            if not public.inArray(domains, newDomain):
                rs = tmp.replace("\n", "")
                newServerName = rs + ' ' + newDomain + "\n"
                myconf = domainV.replace(tmp, newServerName)
                conf = re.sub(repV, myconf, conf)

            if conf.find(f'<VirtualHost *:{ssl_port}>') != -1:
                repV = fr"<VirtualHost\s+\*\:{ssl_port}>(.|\n)*</VirtualHost>"
                domainV = re.search(repV, conf).group()
                rep = r"ServerAlias\s*(.*)\n"
                tmp = re.search(rep, domainV).group(0)
                domains = tmp.strip().split(' ')
                if not public.inArray(domains, newDomain):
                    rs = tmp.replace("\n", "")
                    newServerName = rs + ' ' + newDomain + "\n"
                    myconf = domainV.replace(tmp, newServerName)
                    conf = re.sub(repV, myconf, conf)
        else:
            try:
                httpdVersion = public.readFile(self.setupPath + '/apache/version.pl').strip()
            except:
                httpdVersion = ""
            if httpdVersion == '2.2':
                vName = ''
                if self.sitePort != '80' and self.sitePort != '443':
                    vName = "NameVirtualHost  *:" + port + "\n"
                phpConfig = ""
                apaOpt = "Order allow,deny\n\t\tAllow from all"
            else:
                vName = ""
                # rep = r"php-cgi-([0-9]{2,3})\.sock"
                # version = re.search(rep,conf).groups()[0]
                version = public.get_php_version_conf(conf)
                if len(version) < 2:
                    return_message = public.return_msg_gettext(False, 'Failed to get PHP version!')
                    del return_message['status']
                    return public.return_message(0, 0, return_message['msg'])
                phpConfig = '''
    #PHP
    <FilesMatch \\.php$>
            SetHandler "proxy:%s"
    </FilesMatch>
    ''' % (public.get_php_proxy(version, 'apache'),)
                apaOpt = 'Require all granted'

            # 判断是否是多服务状态
            if webservice_status:
                port = '8288'
            newconf = r'''<VirtualHost *:%s>
    ServerAdmin webmaster@example.com
    DocumentRoot "%s"
    ServerName %s.%s
    ServerAlias %s
    #errorDocument 404 /404.html
    ErrorLog "%s-error_log"
    CustomLog "%s-access_log" combined
    %s

    #DENY FILES
     <Files ~ (\.user.ini|\.htaccess|\.git|\.env|\.svn|\.project|LICENSE|README.md)$>
       Order allow,deny
       Deny from all
    </Files>

    #PATH
    <Directory "%s">
        SetOutputFilter DEFLATE
        Options FollowSymLinks
        AllowOverride All
        %s
        DirectoryIndex %s
    </Directory>
</VirtualHost>''' % (port, sitePath, siteName, get.port, newDomain, public.GetConfigValue('logs_path') + '/' + siteName,
                     public.GetConfigValue('logs_path') + '/' + siteName, phpConfig, sitePath, apaOpt, siteIndex)
            conf += "\n\n" + newconf

        # 添加端口
        if port != '80' and port != '888' and not webservice_status: self.apacheAddPort(get.port)

        # 保存配置文件
        public.writeFile(file, conf)
        return public.return_message(0, 0, True)

    def delete_domain_multiple(self, get):
        '''
            @name 批量删除网站
            @author zhwen<2020-11-17>
            @param id "1"
            @param domains_id 1,2,3
        '''
        domains_id = get.domains_id.split(',')
        get.webname = public.M('sites').where("id=?", (get.id,)).getField('name')
        del_successfully = []
        del_failed = {}
        for domain_id in domains_id:
            get.domain = public.M('domain').where("id=? and pid=?", (domain_id, get.id)).getField('name')
            get.port = str(public.M('domain').where("id=? and pid=?", (domain_id, get.id)).getField('port'))
            if not get.webname:
                continue
            try:
                result = self.DelDomain(get, multiple=1)
                tmp = get.domain + ':' + get.port
                if result['status'] == -1:
                    del_failed[tmp] = result['msg']
                    continue
                del_successfully.append(tmp)
            except:
                tmp = get.domain + ':' + get.port
                del_failed[tmp] = public.lang("There was an error deleting, please try again.")
                pass
        public.serviceReload()
        return_message = {
            'msg': public.get_msg_gettext('Delete domain [{}] successfully', (','.join(del_successfully),)),
            'error': del_failed,
            'success': del_successfully}
        return public.return_message(0, 0, return_message)

    # 删除域名
    def DelDomain(self, get, multiple=None):
        # 校验参数
        try:
            get.validate([
                Param('webname').String(),
                Param('domain').String(),
                Param('id').Integer(),
                Param('port').Integer(),

            ], [
                public.validate.trim_filter(),
            ])
        except Exception as ex:
            public.print_log("error info: {}".format(ex))
            return public.return_message(-1, 0, str(ex))


        sql = public.M('domain')
        id = get.id
        port = str(get.port)
        domain_data = sql.where("pid=? AND name=?", (get.id, get.domain)).field('id,name').find()

        if isinstance(domain_data, list):
            if not domain_data:
                return public.return_message(-1, 0, public.lang("Domain record not found"))
            domain_data = domain_data[0]
        if not isinstance(domain_data, dict) or not domain_data.get('id'):
            return public.return_message(-1, 0, public.lang("Domain record not found"))
        domain_count = sql.table('domain').where("pid=?", (id,)).count()

        if domain_count <= 1: return public.return_message(-1, 0, public.lang("Last domain cannot be deleted!"))

        # nginx
        file = self.setupPath + '/panel/vhost/nginx/' + get['webname'] + '.conf'
        conf = public.readFile(file)
        if conf:
            # 删除域名
            rep = r"server_name\s+(.+);"
            match = re.search(rep, conf)
            if match:
                tmp = match.group()
                newServerName = tmp.replace(' ' + get['domain'] + ';', ';')
                newServerName = newServerName.replace(' ' + get['domain'] + ' ', ' ')
                conf = conf.replace(tmp, newServerName)
            else:
                public.WriteLog("Site manager", f"No server_name found in the Nginx configuration, the domain {get.domain} is only removed from the database")


            # 删除端口
            rep = r"listen.*[\s:]+(\d+).*;"
            tmp = re.findall(rep, conf)
            port_count = sql.table('domain').where('pid=? AND port=?', (get.id, get.port)).count()
            if public.inArray(tmp, port) == True and port_count < 2:
                rep = r"\n*\s+listen.*[\s:]+" + port + r"\s*;"
                conf = re.sub(rep, '', conf)
            # 保存配置
            public.writeFile(file, conf)

        # apache
        if  public.get_multi_webservice_status():
            get.port = '8188'
            port = '8288'
            self._del_apache_domain(get)
        else:
            file = self.setupPath + '/panel/vhost/apache/' + get['webname'] + '.conf'
            conf = public.readFile(file)
            if conf:
                # 删除域名
                try:
                    rep = r"\n*<VirtualHost \*\:" + port + ">(.|\n)*</VirtualHost>"
                    tmp = re.search(rep, conf).group()

                    rep1 = "ServerAlias\\s+(.+)\n"
                    tmp1 = re.findall(rep1, tmp)
                    tmp2 = tmp1[0].split(' ')
                    if len(tmp2) < 2:
                        conf = re.sub(rep, '', conf)
                        rep = r"NameVirtualHost.+\:" + port + "\n"
                        conf = re.sub(rep, '', conf)
                    else:
                        newServerName = tmp.replace(' ' + get['domain'] + "\n", "\n")
                        newServerName = newServerName.replace(' ' + get['domain'] + ' ', ' ')
                        conf = conf.replace(tmp, newServerName)
                    # 保存配置
                    public.writeFile(file, conf.strip())
                except:
                    pass

        # openlitespeed
        self._del_ols_domain(get)

        sql.table('domain').where("id=?", (domain_data['id'],)).delete()
        public.write_log_gettext('Site manager', 'Site [{}] deleted domain [{}] successfully!',
                                 (get.webname, get.domain))
        if not multiple:
            public.serviceReload()
        return public.return_message(0, 0, public.lang("Successfully deleted"))

    # apache根据域名删除指定域名
    def _del_apache_domain(self, get):
        file = f"{self.setupPath}/panel/vhost/apache/{get['webname']}.conf"
        conf = public.readFile(file)
        if not conf:
            return False

        vhost_pattern = r'<VirtualHost.*?</VirtualHost>'
        rep = "ServerAlias\\s+(.+)\n"
        vhost_list = re.findall(vhost_pattern, conf, re.DOTALL | re.MULTILINE)
        if vhost_list:
            conf = ''
            for i in range(len(vhost_list)):
                if get['domain'] in vhost_list[i]:
                    tmp1 = re.findall(rep, vhost_list[i])
                    tmp = tmp1[0].split(' ')
                    if len(tmp) < 2:
                        vhost_list[i] = ''
                    else:
                        newServerName = vhost_list[i].replace(' ' + get['domain'] + "\n", "\n")
                        newServerName = newServerName.replace(' ' + get['domain'] + ' ', ' ')
                        vhost_list[i] = newServerName.replace(vhost_list[i], newServerName)
                conf += vhost_list[i] + '\n\n'
        public.writeFile(file, conf)
        return True

    # openlitespeed删除域名
    def _del_ols_domain(self, get):
        conf_dir = '/www/server/panel/vhost/openlitespeed/listen/'
        if not os.path.exists(conf_dir):
            return public.return_message(-1, 0, 'directory not exists:' + conf_dir)
        for i in os.listdir(conf_dir):
            file_name = conf_dir + i
            if os.path.isdir(file_name):
                continue
            conf = public.readFile(file_name)
            map_rep = r'map\s+{}\s+(.*)'.format(get.webname)
            domains = re.search(map_rep, conf)
            if domains:
                domains = domains.group(1).split(',')
                if get.domain in domains:
                    domains.remove(get.domain)
                if len(domains) == 0:
                    os.remove(file_name)
                    continue
                else:
                    domains = ",".join(domains)
                    map_c = "map\t{} ".format(get.webname) + domains
                    conf = re.sub(map_rep, map_c, conf)
            public.writeFile(file_name, conf)
        return public.return_message(0, 0, public.lang("Setup successfully!"))

    # 检查域名是否解析
    def CheckDomainPing(self, get):
        try:
            epass = public.GetRandomString(32)
            spath = get.path + '/.well-known/pki-validation'
            if not os.path.exists(spath): public.ExecShell("mkdir -p '" + spath + "'")
            public.writeFile(spath + '/fileauth.txt', epass)
            result = public.httpGet(
                'http://' + get.domain.replace('*.', '') + '/.well-known/pki-validation/fileauth.txt')
            if result == epass: return public.return_message(0, 0, public.lang(""))
            return public.return_message(-1, 0, public.lang(""))
        except:
            return public.return_message(-1, 0, public.lang(""))

    # 保存第三方证书
    def SetSSL(self, get):
        # 校验参数
        try:
            get.validate([
                Param('siteName').String(),
                Param('key').String(),
                Param('csr').String(),
                Param('type').Integer(),

            ], [
                public.validate.trim_filter(),
            ])
        except Exception as ex:
            public.print_log("error info: {}".format(ex))
            return public.return_message(-1, 0, str(ex))

        siteName = get.siteName
        path = '/www/server/panel/vhost/cert/' + siteName
        csrpath = path + "/fullchain.pem"
        keypath = path + "/privkey.pem"

        if (get.key.find('KEY') == -1):
            return public.return_message(-1, 0, public.lang('Private Key ERROR, please check!'))
        if (get.csr.find('CERTIFICATE') == -1):
            return public.return_message(-1, 0, public.lang('Certificate ERROR, please check!'))
        public.writeFile('/tmp/cert.pl', get.csr)
        if not public.CheckCert('/tmp/cert.pl'):
            return public.return_message(-1, 0, public.lang('Error getting certificate'))
        backup_cert = '/tmp/backup_cert_' + siteName

        import shutil
        if os.path.exists(backup_cert): shutil.rmtree(backup_cert)
        if os.path.exists(path): shutil.move(path, backup_cert)
        if os.path.exists(path): shutil.rmtree(path)

        public.ExecShell('mkdir -p ' + path)
        public.writeFile(keypath, get.key)
        public.writeFile(csrpath, get.csr)

        # 写入配置文件
        result = self.SetSSLConf(get)
        if result['status'] == -1:
            return result
        isError = public.checkWebConfig()

        if (type(isError) == str):
            if os.path.exists(path): shutil.rmtree(backup_cert)
            shutil.move(backup_cert, path)
            return public.return_message(-1, 0, 'ERROR: <br><a style="color:red;">' + isError.replace("\n",'<br>') + '</a>')
        public.serviceReload()

        if os.path.exists(path + '/partnerOrderId'): os.remove(path + '/partnerOrderId')
        if os.path.exists(path + '/certOrderId'): os.remove(path + '/certOrderId')
        p_file = '/etc/letsencrypt/live/' + get.siteName
        if os.path.exists(p_file): shutil.rmtree(p_file)
        public.write_log_gettext('Site manager', 'Certificate saved!')

        # 清理备份证书
        if os.path.exists(backup_cert): shutil.rmtree(backup_cert)
        return public.return_message(0, 0, public.lang('Certificate saved!'))

    # 获取运行目录
    def GetRunPath(self, get):
        if not hasattr(get, 'id'):
            if hasattr(get, 'siteName'):
                get.id = public.M('sites').where('name=?', (get.siteName,)).getField('id')
            else:
                get.id = public.M('sites').where('path=?', (get.path,)).getField('id')
        if not get.id: return False
        if type(get.id) == list: get.id = get.id[0]['id']
        result = self.GetSiteRunPath(get)['message']
        if 'runPath' in result:
            return public.return_message(0, 0, result['runPath'])
        return public.return_message(-1, 0, public.lang(""))

    # 创建Let's Encrypt免费证书
    def CreateLet(self, get):

        domains = json.loads(get.domains)
        if not len(domains):
            return_message = public.return_msg_gettext(False, 'Please choose a domain name')
            del return_message['status']
            return public.return_message(-1, 0, return_message['msg'])

        file_auth = True
        if hasattr(get, 'dnsapi'):
            file_auth = False

        if not hasattr(get, 'dnssleep'):
            get.dnssleep = 10

        email = public.M('users').getField('email')
        if hasattr(get, 'email'):
            if get.email.find('@') == -1:
                get.email = email
            else:
                get.email = get.email.strip()
                public.M('users').where('id=?', (1,)).setField('email', get.email)
        else:
            get.email = email

        for domain in domains:
            if public.checkIp(domain): continue
            if domain.find('*.') >= 0 and file_auth:
                return_message = public.return_msg_gettext(False,
                                                           'A generic domain name cannot be used to apply for a certificate using [File Validation]!')
                del return_message['status']
                return public.return_message(-1, 0, return_message['msg'])

        if file_auth:
            get.sitename = get.siteName
            if self.GetRedirectList(get):
                return_message = public.return_msg_gettext(False,
                                                           'Your site has 301 Redirect on，Please turn it off first!')
                del return_message['status']
                return public.return_message(-1, 0, return_message['msg'])
            if self.GetProxyList(get):
                return_message = public.return_msg_gettext(False,
                                                           'Sites that have reverse proxy turned on cannot request SSL!')
                del return_message['status']
                return public.return_message(-1, 0, return_message['msg'])
            data = self.get_site_info(get.siteName)
            get.id = data['id']
            runPath = self.GetRunPath(get)['message']['result']
            if runPath != '/':
                if runPath[:1] != '/': runPath = '/' + runPath
            else:
                runPath = ''
            get.site_dir = data['path'] + runPath

        else:
            dns_api_list = self.GetDnsApi(get)
            get.dns_param = None
            for dns in dns_api_list:
                if dns['name'] == get.dnsapi:
                    param = []
                    if not dns['data']: continue
                    for val in dns['data']:
                        param.append(val['value'])
                    get.dns_param = '|'.join(param)
            n_list = ['dns', 'dns_bt']
            if not get.dnsapi in n_list:
                if len(get.dns_param) < 16:
                    return_message = public.return_msg_gettext(False, 'No valid DNSAPI key information found',
                                                               (get.dnsapi,))
                    del return_message['status']
                    return public.return_message(-1, 0, return_message['msg'])
            if get.dnsapi == 'dns_bt':
                if not os.path.exists('plugin/dns/dns_main.py'):
                    return_message = public.return_msg_gettext(False,
                                                               'Please go to the software store to install [Cloud Resolution] and complete the domain name NS binding.')
                    del return_message['status']
                    return public.return_message(-1, 0, return_message['msg'])

        self.check_ssl_pack()
        try:
            import panel_lets_v2 as panelLets
            public.mod_reload(panelLets)
        except Exception as ex:
            if str(ex).find('No module named requests') != -1:
                public.ExecShell("pip install requests &")
                return_message = public.return_msg_gettext(False,
                                                           'Missing requests component, please try to repair the panel!')
                del return_message['status']
                return public.return_message(-1, 0, return_message['msg'])
            return_message = public.return_msg_gettext(False, str(ex))
            del return_message['status']
            return public.return_message(-1, 0, return_message['msg'])

        lets = panelLets.panelLets()
        result = lets.apple_lest_cert(get)
        if result['status'] and not 'code' in result:
            get.onkey = 1
            path = '/www/server/panel/cert/' + get.siteName
            if os.path.exists(path + '/certOrderId'): os.remove(path + '/certOrderId')
            result = self.SetSSLConf(get)
        return result

    def get_site_info(self, siteName):
        data = public.M("sites").where('name=?', siteName).field('id,path,name').find()
        return data

    # 检测依赖库
    def check_ssl_pack(self):
        try:
            import requests
        except:
            public.ExecShell('btpip install requests')
        try:
            import OpenSSL
        except:
            public.ExecShell('btpip install pyOpenSSL')

    # 判断DNS-API是否设置
    def Check_DnsApi(self, dnsapi):
        dnsapis = self.GetDnsApi(None)
        for dapi in dnsapis:
            if dapi['name'] == dnsapi:
                if not dapi['data']: return True
                for d in dapi['data']:
                    if d['key'] == '': return False
        return True

    # 获取DNS-API列表
    def GetDnsApi(self, get):
        api_path = './config/dns_api.json'
        api_init = './config/dns_api_init.json'
        if not os.path.exists(api_path):
            if os.path.exists(api_init):
                import shutil
                shutil.copyfile(api_init, api_path)
        apis = json.loads(public.ReadFile(api_path))

        path = '/root/.acme.sh'
        if not os.path.exists(path + '/account.conf'): path = "/.acme.sh"
        account = public.readFile(path + '/account.conf')
        if not account: account = ''
        is_write = False
        for i in range(len(apis)):
            if not apis[i]['data']: continue
            for j in range(len(apis[i]['data'])):
                if apis[i]['data'][j]['value']: continue
                search_str = apis[i]['data'][j]['key'] + r"\s*=\s*'(.+)'"
                match = re.search("" + apis[i]['data'][j]['key'] + r"\s*=\s*'(.+)'", account)
                if match: apis[i]['data'][j]['value'] = match.groups()[0]
                if apis[i]['data'][j]['value']: is_write = True
        if is_write: public.writeFile('./config/dns_api.json', json.dumps(apis))
        result = []
        for i in apis:
            if i['title'] == 'CloudFlare':
                if os.path.exists('/www/server/panel/data/cf_limit_api.pl'):
                    i['API_Limit'] = True
                else:
                    i['API_Limit'] = False
            result.insert(0, i)
        return public.return_message(0, 0, result)

    # 设置DNS-API
    def SetDnsApi(self, get):
        pdata = json.loads(get.pdata)
        cf_limit_api = "/www/server/panel/data/cf_limit_api.pl"
        if 'API_Limit' in pdata and pdata['API_Limit'] == True and not os.path.exists(cf_limit_api):
            os.mknod(cf_limit_api)
        if 'API_Limit' in pdata and pdata['API_Limit'] == False:
            if os.path.exists(cf_limit_api): os.remove(cf_limit_api)
        apis = json.loads(public.ReadFile('./config/dns_api.json'))
        is_write = False
        for key in pdata.keys():
            for i in range(len(apis)):
                if not apis[i]['data']: continue
                for j in range(len(apis[i]['data'])):
                    if apis[i]['data'][j]['key'] != key: continue
                    apis[i]['data'][j]['value'] = pdata[key]
                    is_write = True

        if is_write: public.writeFile('./config/dns_api.json', json.dumps(apis))
        return_message = public.return_msg_gettext(True, 'Setup successfully!')
        del return_message['status']
        return public.return_message(0, 0, return_message['msg'])

    # 获取站点所有域名
    def GetSiteDomains(self, get):
        data = {}
        domains = public.M('domain').where('pid=?', (get.id,)).field('name,id').select()
        binding = public.M('binding').where('pid=?', (get.id,)).field('domain,id').select()
        if type(binding) == str: return public.return_message(0, 0, binding)
        for b in binding:
            tmp = {}
            tmp['name'] = b['domain']
            tmp['id'] = b['id']
            tmp['binding'] = True
            domains.append(tmp)
        data['domains'] = domains
        data['email'] = public.M('users').where('id=?', (1,)).getField('email')
        if data['email'] == '287962566@qq.com': data['email'] = ''
        return public.return_message(0, 0, data)

    def GetFormatSSLResult(self, result):
        try:
            import re
            rep = "\\s*Domain:.+\n\\s+Type:.+\n\\s+Detail:.+"
            tmps = re.findall(rep, result)

            statusList = []
            for tmp in tmps:
                arr = tmp.strip().split('\n')
                status = {}
                for ar in arr:
                    tmp1 = ar.strip().split(':')
                    status[tmp1[0].strip()] = tmp1[1].strip()
                    if len(tmp1) > 2:
                        status[tmp1[0].strip()] = tmp1[1].strip() + ':' + tmp1[2]
                statusList.append(status)
            return statusList
        except:
            return None

    # 获取TLS1.3标记
    def get_tls13(self):
        nginx_bin = '/www/server/nginx/sbin/nginx'
        nginx_v = public.ExecShell(nginx_bin + ' -V 2>&1')[0]
        nginx_v_re = re.findall(r"nginx/(\d\.\d+).+OpenSSL\s+(\d\.\d+)", nginx_v, re.DOTALL)
        if nginx_v_re:
            if nginx_v_re[0][0] in ['1.8', '1.9', '1.7', '1.6', '1.5', '1.4']:
                return ''
            if float(nginx_v_re[0][0]) >= 1.15 and float(nginx_v_re[0][-1]) >= 1.1:
                return ' TLSv1.3'
        else:
            _v = re.search(r'nginx/1\.1(5|6|7|8|9).\d', nginx_v)
            if not _v:
                _v = re.search(r'nginx/1\.2\d\.\d', nginx_v)
            openssl_v = public.ExecShell(nginx_bin + ' -V 2>&1|grep OpenSSL')[0].find('OpenSSL 1.1.') != -1
            if _v and openssl_v:
                return ' TLSv1.3'
        return ''

    # 获取apache反向代理
    def get_apache_proxy(self, conf):
        rep = "\n*#Referenced reverse proxy rule, if commented, the configured reverse proxy will be invalid\n+\\s+IncludeOptiona.*"
        proxy = re.search(rep, conf)
        if proxy:
            return proxy.group()
        return ""

    def _get_site_domains(self, sitename):
        site_id = public.M('sites').where('name=?', (sitename,)).field('id').find()
        domains = public.M('domain').where('pid=?', (site_id['id'],)).field('name').select()
        domains = [d['name'] for d in domains]
        return domains

    # 设置OLS ssl
    def set_ols_ssl(self, get, siteName):
        listen_conf = self.setupPath + '/panel/vhost/openlitespeed/listen/443.conf'
        conf = public.readFile(listen_conf)
        ssl_conf = """
        vhssl {
          keyFile                 /www/server/panel/vhost/cert/BTDOMAIN/privkey.pem
          certFile                /www/server/panel/vhost/cert/BTDOMAIN/fullchain.pem
          certChain               1
          sslProtocol             24
          ciphers                 EECDH+AESGCM:EDH+AESGCM:AES256+EECDH:AES256+EDH:ECDHE-RSA-AES128-GCM-SHA384:ECDHE-RSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA128:DHE-RSA-AES128-GCM-SHA384:DHE-RSA-AES128-GCM-SHA256:DHE-RSA-AES128-GCM-SHA128:ECDHE-RSA-AES128-SHA384:ECDHE-RSA-AES128-SHA128:ECDHE-RSA-AES128-SHA:ECDHE-RSA-AES128-SHA:DHE-RSA-AES128-SHA128:DHE-RSA-AES128-SHA128:DHE-RSA-AES128-SHA:DHE-RSA-AES128-SHA:ECDHE-RSA-DES-CBC3-SHA:EDH-RSA-DES-CBC3-SHA:AES128-GCM-SHA384:AES128-GCM-SHA128:AES128-SHA128:AES128-SHA128:AES128-SHA:AES128-SHA:DES-CBC3-SHA:HIGH:!aNULL:!eNULL:!EXPORT:!DES:!MD5:!PSK:!RC4
          enableECDHE             1
          renegProtection         1
          sslSessionCache         1
          enableSpdy              15
          enableStapling           1
          ocspRespMaxAge           86400
        }
        """
        ssl_dir = self.setupPath + '/panel/vhost/openlitespeed/detail/ssl/'
        if not os.path.exists(ssl_dir):
            os.makedirs(ssl_dir)
        ssl_file = ssl_dir + '{}.conf'.format(siteName)
        if not os.path.exists(ssl_file):
            ssl_conf = ssl_conf.replace('BTDOMAIN', siteName)
            public.writeFile(ssl_file, ssl_conf, "a+")
        include_ssl = '\ninclude {}'.format(ssl_file)
        detail_file = self.setupPath + '/panel/vhost/openlitespeed/detail/{}.conf'.format(siteName)
        public.writeFile(detail_file, include_ssl, 'a+')
        if not conf:
            # 判断是否启用多服务
            prot = '443'
            if public.get_multi_webservice_status():
                prot = '8190'

            conf = """
listener SSL443 {{
  map                     BTSITENAME BTDOMAIN
  address                 *:{prot}
  secure                  1
  keyFile                 /www/server/panel/vhost/cert/BTSITENAME/privkey.pem
  certFile                /www/server/panel/vhost/cert/BTSITENAME/fullchain.pem
  certChain               1
  sslProtocol             24
  ciphers                 EECDH+AESGCM:EDH+AESGCM:AES256+EECDH:AES256+EDH:ECDHE-RSA-AES128-GCM-SHA384:ECDHE-RSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA128:DHE-RSA-AES128-GCM-SHA384:DHE-RSA-AES128-GCM-SHA256:DHE-RSA-AES128-GCM-SHA128:ECDHE-RSA-AES128-SHA384:ECDHE-RSA-AES128-SHA128:ECDHE-RSA-AES128-SHA:ECDHE-RSA-AES128-SHA:DHE-RSA-AES128-SHA128:DHE-RSA-AES128-SHA128:DHE-RSA-AES128-SHA:DHE-RSA-AES128-SHA:ECDHE-RSA-DES-CBC3-SHA:EDH-RSA-DES-CBC3-SHA:AES128-GCM-SHA384:AES128-GCM-SHA128:AES128-SHA128:AES128-SHA128:AES128-SHA:AES128-SHA:DES-CBC3-SHA:HIGH:!aNULL:!eNULL:!EXPORT:!DES:!MD5:!PSK:!RC4
  enableECDHE             1
  renegProtection         1
  sslSessionCache         1
  enableSpdy              15
  enableStapling           1
  ocspRespMaxAge           86400
}}
""".format(prot=prot)

        else:
            rep = r'listener\s*SSL443\s*{'
            map = '\n  map {s} {s}'.format(s=siteName)
            conf = re.sub(rep, 'listener SSL443 {' + map, conf)
        domain = ",".join(self._get_site_domains(siteName))
        conf = conf.replace('BTSITENAME', siteName).replace('BTDOMAIN', domain)
        public.writeFile(listen_conf, conf)

    def _get_ap_static_security(self, ap_conf):
        if not ap_conf: return ''
        ap_static_security = re.search('#SECURITY-START(.|\n)*#SECURITY-END', ap_conf)
        if ap_static_security:
            return ap_static_security.group()
        return ''

    # 添加SSL配置
    def SetSSLConf(self, get):
        """
        @name 兼容批量设置
        @auther hezhihong
        """
        siteName = get.siteName
        if not 'first_domain' in get: get.first_domain = siteName
        if 'isBatch' in get and siteName != get.first_domain: get.first_domain = siteName

        # Nginx配置
        file = self.setupPath + '/panel/vhost/nginx/' + siteName + '.conf'

        # Node项目
        if not os.path.exists(file):  file = self.setupPath + '/panel/vhost/nginx/node_' + siteName + '.conf'
        # if not os.path.exists(file):  file = self.setupPath + '/panel/vhost/nginx/java_' + siteName + '.conf'
        # if not os.path.exists(file):  file = self.setupPath + '/panel/vhost/nginx/go_' + siteName + '.conf'
        # if not os.path.exists(file):  file = self.setupPath + '/panel/vhost/nginx/other_' + siteName + '.conf'
        # if not os.path.exists(file):  file = self.setupPath + '/panel/vhost/nginx/python_' + siteName + '.conf'
        # if not os.path.exists(file):  file = self.setupPath + '/panel/vhost/nginx/net_' + siteName + '.conf'
        # if not os.path.exists(file):  file = self.setupPath + '/panel/vhost/nginx/html_' + siteName + '.conf'
        ng_file = file
        ng_conf = public.readFile(file)
        have_nginx_conf = ng_conf is not False
        # 是否为子目录设置SSL
        # if hasattr(get,'binding'):
        #    allconf = conf;
        #    conf = re.search("#BINDING-"+get.binding+"-START(.|\n)*#BINDING-"+get.binding+"-END",conf).group()
        try:
            if ng_conf:
                if ng_conf.find('ssl_certificate') == -1:
                    http3_header = '''\n    add_header Alt-Svc 'quic=":443"; h3=":443"; h3-29=":443"; h3-27=":443";h3-25=":443"; h3-T050=":443"; h3-Q050=":443";h3-Q049=":443";h3-Q048=":443"; h3-Q046=":443"; h3-Q043=":443"';'''
                    if not self.is_nginx_http3():
                        http3_header = ""
                    sslStr = """#error_page 404/404.html;
        ssl_certificate    /www/server/panel/vhost/cert/%s/fullchain.pem;
        ssl_certificate_key    /www/server/panel/vhost/cert/%s/privkey.pem;
        ssl_protocols %s;
        ssl_ciphers EECDH+CHACHA20:EECDH+CHACHA20-draft:EECDH+AES128:RSA+AES128:EECDH+AES256:RSA+AES256:EECDH+3DES:RSA+3DES:!MD5;
        ssl_prefer_server_ciphers on;
        ssl_session_tickets on;
        ssl_session_cache shared:SSL:10m;
        ssl_session_timeout 10m;
        add_header Strict-Transport-Security "max-age=31536000";%s
        error_page 497  https://$host$request_uri;
    """ % (get.first_domain, get.first_domain, self.get_tls_protocol(self.get_tls13(), is_apache=False), http3_header)
                    if (ng_conf.find('ssl_certificate') != -1):
                        if 'isBatch' not in get:
                            public.serviceReload()
                            return public.return_message(0, 0, public.lang("SSL turned on!"))
                        else:
                            return True

                    if ng_conf.find('#error_page 404/404.html;') == -1:
                        return public.returnMsg(False, "can found【#error_page 404/404.html;】，"
                                                       "Unable to determine the location to add SSL configuration."
                                                       " Please try manually adding a marker or restoring the configuration file.")

                    ng_conf = ng_conf.replace('#error_page 404/404.html;', sslStr)
                    conf = re.sub(r"\s+\#SSL\-END", "\n\t\t#SSL-END", ng_conf)

                    # 添加端口
                    rep = r"listen.*[\s:]+(\d+).*;"
                    tmp = re.findall(rep, ng_conf)
                    if not public.inArray(tmp, '443'):
                        listen_re = re.search(rep, ng_conf)
                        if not listen_re:
                            ng_conf = re.sub(r"server\s*{\s*", "server\n{\n\t\tlisten 80;\n\t\t", ng_conf)
                            listen_re = re.search(rep, ng_conf)
                        listen = listen_re.group()
                        nginx_ver = public.nginx_version()
                        default_site = ''
                        if ng_conf.find('default_server') != -1:
                            default_site = ' default_server'

                        listen_add_str = []
                        if nginx_ver:
                            port_str = ["443"]
                            if self.is_ipv6:
                                port_str.append("[::]:443")
                            use_http2_on = False
                            for p in port_str:
                                listen_add_str.append("\n    listen {} ssl".format(p))
                                if nginx_ver < [1, 9, 5]:
                                    listen_add_str.append(default_site + ";")
                                elif [1, 9, 5] <= nginx_ver < [1, 25, 1]:
                                    listen_add_str.append(" http2 " + default_site + ";")
                                else:  # >= [1, 25, 1]
                                    listen_add_str.append(default_site + ";")
                                    use_http2_on = True

                                if self.is_nginx_http3():
                                    listen_add_str.append("\n    listen {} quic;".format(p))
                            if use_http2_on:
                                listen_add_str.append("\n    http2 on;")

                        else:
                            listen_add_str.append("\n    listen 443 ssl " + default_site + ";")
                        listen_add_str_data = "".join(listen_add_str)
                        ng_conf = ng_conf.replace(listen, listen + listen_add_str_data)
        except Exception as ng_err:
            public.print_log(f"set nginx conf error: {ng_err}")
        # ================================ Apache ========================================
        # Apache配置
        try:
            file = self.setupPath + '/panel/vhost/apache/' + siteName + '.conf'
            other_project = ""
            if not os.path.exists(file):
                file = self.setupPath + '/panel/vhost/apache/node_' + siteName + '.conf'
                other_project = "node"

            # if not os.path.exists(file):
            #     file = self.setupPath + '/panel/vhost/apache/java_' + siteName + '.conf'
            #     other_project = "java"
            #
            # if not os.path.exists(file):
            #     file = self.setupPath + '/panel/vhost/apache/go_' + siteName + '.conf'
            #     other_project = "go"
            #
            # if not os.path.exists(file):
            #     file = self.setupPath + '/panel/vhost/apache/other_' + siteName + '.conf'
            #     other_project = "other"
            #
            # if not os.path.exists(file):
            #     file = self.setupPath + '/panel/vhost/apache/python_' + siteName + '.conf'
            #     other_project = "python"
            #
            # if not os.path.exists(file):
            #     other_project = "net"
            #     file = self.setupPath + '/panel/vhost/apache/net_' + siteName + '.conf'
            #
            # if not os.path.exists(file):
            #     other_project = "html"
            #     file = self.setupPath + '/panel/vhost/apache/html_' + siteName + '.conf'

            ap_conf = public.readFile(file)
            have_apache_conf = ap_conf is not False
            ap_static_security = self._get_ap_static_security(ap_conf)
            if ap_conf:
                ap_proxy = self.get_apache_proxy(ap_conf)
                if ap_conf.find('SSLCertificateFile') == -1 and ap_conf.find('VirtualHost') != -1:
                    find = public.M('sites').where("name=?", (siteName,)).field('id,path,service_type').find()
                    tmp = public.M('domain').where('pid=?', (find['id'],)).field('name').select()
                    domains = ''
                    for key in tmp:
                        domains += key['name'] + ' '
                    path = (find['path'] + '/' + self.GetRunPath(get)["message"]["result"]).replace('//', '/')
                    index = 'index.php index.html index.htm default.php default.html default.htm'
                    ssl_prot = '8290' if public.get_multi_webservice_status()  else '443'  # 多服务端口

                    try:
                        httpdVersion = public.readFile(self.setupPath + '/apache/version.pl').strip()
                    except:
                        httpdVersion = ""
                    if httpdVersion == '2.2':
                        vName = ""
                        phpConfig = ""
                        apaOpt = "Order allow,deny\n\t\tAllow from all"
                    else:
                        vName = ""
                        # rep = r"php-cgi-([0-9]{2,3})\.sock"
                        # version = re.search(rep, conf).groups()[0]
                        version = public.get_php_version_conf(ap_conf)
                        if len(version) < 2:
                            if 'isBatch' not in get:
                                return public.returnMsg(False, 'PHP_GET_ERR')
                            else:
                                return False
                        phpConfig = '''
        #PHP
        <FilesMatch \\.php$>
                SetHandler "proxy:%s"
        </FilesMatch>
        ''' % (public.get_php_proxy(version, 'apache'),)
                        apaOpt = 'Require all granted'

                    sslStr = fr'''%s<VirtualHost *:%s>
        ServerAdmin webmaster@example.com
        DocumentRoot "%s"
        ServerName SSL.%s
        ServerAlias %s
        #errorDocument 404 /404.html
        ErrorLog "%s-error_log"
        CustomLog "%s-access_log" combined
        %s
        #SSL
        SSLEngine On
        SSLCertificateFile /www/server/panel/vhost/cert/%s/fullchain.pem
        SSLCertificateKeyFile /www/server/panel/vhost/cert/%s/privkey.pem
        SSLCipherSuite EECDH+CHACHA20:EECDH+CHACHA20-draft:EECDH+AES128:RSA+AES128:EECDH+AES256:RSA+AES256:EECDH+3DES:RSA+3DES:!MD5:ALL:!ADH:!EXPORT56:RC4+RSA:+HIGH:+MEDIUM:+LOW:+SSLv2:+EXP:+eNULL
        SSLProtocol All -SSLv2 -SSLv3 %s
        SSLHonorCipherOrder On
        %s
        %s
    
        #DENY FILES
         <Files ~ (\.user.ini|\.htaccess|\.git|\.env|\.svn|\.project|LICENSE|README.md)$>
           Order allow,deny
           Deny from all
        </Files>
    
        #PATH
        <Directory "%s">
            SetOutputFilter DEFLATE
            Options FollowSymLinks
            AllowOverride All
            %s
            DirectoryIndex %s
        </Directory>
    </VirtualHost>''' % (vName, ssl_prot, path, siteName, domains, public.GetConfigValue('logs_path') + '/' + siteName,
                         public.GetConfigValue('logs_path') + '/' + siteName, ap_proxy,
                         get.first_domain, get.first_domain, self.get_tls_protocol(is_apache=True),
                         ap_static_security, phpConfig, path, apaOpt, index)
                    ap_conf = ap_conf + "\n" + sslStr
                    self.apacheAddPort(ssl_prot)
                    shutil.copyfile(file, self.apache_conf_bak)
                    public.writeFile(file, ap_conf)
                    if other_project == "node":  # 兼容Nodejs项目
                        from projectModel.nodejsModel import main
                        m = main()
                        project_find = m.get_project_find(siteName)
                        m.set_apache_config(project_find)
                    # if other_project == "java":  # 兼容Java项目
                    #     try:
                    #         from mod.project.java.java_web_conf import JavaApacheTool
                    #         from mod.project.java.projectMod import main
                    #         JavaApacheTool().set_apache_config_for_ssl(main().get_project_find(siteName))
                    #     except:
                    #         from projectModel.javaModel import main
                    #         m = main()
                    #         project_find = m.get_project_find(siteName)
                    #         m.set_apache_config(project_find)
                    # if other_project == "go":  # 兼容Go项目
                    #     from projectModel.goModel import main
                    #     m = main()
                    #     project_find = m.get_project_find(siteName)
                    #     m.set_apache_config(project_find)
                    # if other_project == "other":  # 兼容其他项目
                    #     from projectModel.otherModel import main
                    #     m = main()
                    #     project_find = m.get_project_find(siteName)
                    #     m.set_apache_config(project_find)
                    # if other_project == "python":  # 兼容python项目
                    #     from projectModel.pythonModel import main
                    #     m = main()
                    #     project_find = m.get_project_find(siteName)
                    #     m.set_apache_config(project_find)
                    # if other_project == "net":
                    #     from projectModel.netModel import main
                    #     m = main()
                    #     project_find = m.get_project_find(siteName)
                    #     m.set_apache_config(project_find)
                    #
                    # if other_project == "html":
                    #     from projectModel.htmlModel import main
                    #     m = main()
                    #     project_find = m.get_project_find(siteName)
                    #     m.set_apache_config(project_find)

            if not have_nginx_conf and not have_apache_conf:
                return public.returnMsg(False, 'No server configuration file. '
                                               'Please check if port forwarding has been enabled!')

            if ng_conf:  # 因为未查明原因，Apache配置过程中会删除掉nginx备份文件（估计是重复调用了本类中的init操作导致的）
                shutil.copyfile(ng_file, self.nginx_conf_bak)
                public.writeFile(ng_file, ng_conf)
        except Exception as ap_err:
            public.print_log(f"set apache conf error: {ap_err}")
        # ============================= OLS ==================================
        try:
            self.set_ols_ssl(get, siteName)
            isError = public.checkWebConfig()
            if (isError != True):
                if os.path.exists(self.nginx_conf_bak): shutil.copyfile(self.nginx_conf_bak, ng_file)
                if os.path.exists(self.apache_conf_bak): shutil.copyfile(self.apache_conf_bak, file)
                public.ExecShell("rm -f /tmp/backup_*.conf")
                return public.returnMsg(False,
                                        'ssl cert wrong: <br><a style="color:red;">' + isError.replace("\n", '<br>') + '</a>')

            # sql = public.M('firewall')
            # import firewalls
            # get.port = ssl_prot
            # get.ps = 'HTTPS'
            # if 'isBatch' not in get: firewalls.firewalls().AddAcceptPort(get)
            # if 'isBatch' not in get: public.serviceReload()
            self.save_cert(get)
            public.WriteLog('Site manager', 'Site [{}] turned on SSL successfully!'.format(siteName))

        except Exception as ols_err:
            public.print_log(f"set ols conf error: {ols_err}")

        result = public.returnMsg(True, 'SITE_SSL_OPEN_SUCCESS')
        result['csr'] = public.readFile('/www/server/panel/vhost/cert/' + get.siteName + '/fullchain.pem')
        result['key'] = public.readFile('/www/server/panel/vhost/cert/' + get.siteName + '/privkey.pem')
        if 'isBatch' not in get:
            return result
        else:
            return True

    def save_cert(self, get):
        # try:
        import panel_ssl_v2 as panelSSL
        ss = panelSSL.panelSSL()
        get.keyPath = '/www/server/panel/vhost/cert/' + get.siteName + '/privkey.pem'
        get.certPath = '/www/server/panel/vhost/cert/' + get.siteName + '/fullchain.pem'
        return ss.SaveCert(get)
        # return public.return_message(0, 0, public.lang(""))
        # except:
        # return False;

    # HttpToHttps
    def HttpToHttps(self, get):
        # 校验参数
        try:
            get.validate([
                Param('siteName').String(),
            ], [
                public.validate.trim_filter(),
            ])
        except Exception as ex:
            public.print_log("error info: {}".format(ex))
            return public.return_message(-1, 0, str(ex))

        siteName = get.siteName
        # Nginx配置
        file = self.setupPath + '/panel/vhost/nginx/' + siteName + '.conf'
        if not os.path.exists(file):
            file = self.setupPath + '/panel/vhost/nginx/node_' + siteName + '.conf'
        conf = public.readFile(file)
        if conf:
            if conf.find('ssl_certificate') == -1:
                return_message = public.return_msg_gettext(False, 'SSL is NOT currently enabled')
                del return_message['status']
                return public.return_message(-1, 0, return_message['msg'])
            to = """#error_page 404/404.html;
    #HTTP_TO_HTTPS_START
    if ($server_port !~ 443){
        rewrite ^(/.*)$ https://$host$1 permanent;
    }
    #HTTP_TO_HTTPS_END"""
            conf = conf.replace('#error_page 404/404.html;', to)
            public.writeFile(file, conf)

        # 多服务下不添加apache与ols配置
        if not public.get_multi_webservice_status():
            file = self.setupPath + '/panel/vhost/apache/' + siteName + '.conf'
            if not os.path.exists(file):
                file = self.setupPath + '/panel/vhost/apache/node_' + siteName + '.conf'
            conf = public.readFile(file)
            if conf:
                httpTohttos = '''combined
        #HTTP_TO_HTTPS_START
        <IfModule mod_rewrite.c>
            RewriteEngine on
            RewriteCond %{SERVER_PORT} !^443$
            RewriteRule (.*) https://%{SERVER_NAME}$1 [L,R=301]
        </IfModule>
        #HTTP_TO_HTTPS_END'''
                conf = re.sub('combined', httpTohttos, conf, 1)
                public.writeFile(file, conf)
            # OLS
            conf_dir = '{}/panel/vhost/openlitespeed/redirect/{}/'.format(self.setupPath, siteName)
            if not os.path.exists(conf_dir):
                os.makedirs(conf_dir)
            file = conf_dir + 'force_https.conf'
            ols_force_https = '''
    #HTTP_TO_HTTPS_START
    <IfModule mod_rewrite.c>
        RewriteEngine on
        RewriteCond %{SERVER_PORT} !^443$
        RewriteRule (.*) https://%{SERVER_NAME}$1 [L,R=301]
    </IfModule>
    #HTTP_TO_HTTPS_END'''
            public.writeFile(file, ols_force_https)
        public.serviceReload()
        return_message = public.return_msg_gettext(True, 'Setup successfully!')
        del return_message['status']
        return public.return_message(0, 0, return_message['msg'])

    # CloseToHttps
    def CloseToHttps(self, get):
        # 校验参数
        try:
            get.validate([
                Param('siteName').String(),
            ], [
                public.validate.trim_filter(),
            ])
        except Exception as ex:
            public.print_log("error info: {}".format(ex))
            return public.return_message(-1, 0, str(ex))

        siteName = get.siteName
        file = self.setupPath + '/panel/vhost/nginx/' + siteName + '.conf'
        if not os.path.exists(file):
            file = self.setupPath + '/panel/vhost/nginx/node_' + siteName + '.conf'
        conf = public.readFile(file)
        if conf:
            rep = "\n\\s*#HTTP_TO_HTTPS_START(.|\n){1,300}#HTTP_TO_HTTPS_END"
            conf = re.sub(rep, '', conf)
            rep = "\\s+if.+server_port.+\n.+\n\\s+\\s*}"
            conf = re.sub(rep, '', conf)
            public.writeFile(file, conf)

        file = self.setupPath + '/panel/vhost/apache/' + siteName + '.conf'
        conf = public.readFile(file)
        if conf:
            rep = "\n\\s*#HTTP_TO_HTTPS_START(.|\n){1,300}#HTTP_TO_HTTPS_END"
            conf = re.sub(rep, '', conf)
            public.writeFile(file, conf)
        # OLS
        file = '{}/panel/vhost/openlitespeed/redirect/{}/force_https.conf'.format(self.setupPath, siteName)
        public.ExecShell('rm -f {}*'.format(file))
        public.serviceReload()
        return_message = public.return_msg_gettext(True, 'Setup successfully!')
        del return_message['status']
        return public.return_message(0, 0, return_message['msg'])

    # 是否跳转到https
    def IsToHttps(self, siteName):
        file = self.setupPath + '/panel/vhost/nginx/' + siteName + '.conf'
        if not os.path.exists(file):
            file = self.setupPath + '/panel/vhost/nginx/node_' + siteName + '.conf'
            if not os.path.exists(file): return False
        conf = public.readFile(file)
        if conf:
            if conf.find('HTTP_TO_HTTPS_START') != -1: return True
            if conf.find('$server_port !~ 443') != -1: return True
        return False

    # 清理SSL配置
    def CloseSSLConf(self, get):
        # 校验参数
        try:
            get.validate([
                Param('siteName').String(),
                Param('updateOf').Integer(),
                Param('reload').Integer(),
            ], [
                public.validate.trim_filter(),
            ])
            if not hasattr(get, "reload"):
                get.reload = 1
            else:
                get.reload = int(get.reload)
        except Exception as ex:
            public.print_log("error info: {}".format(ex))
            return public.return_message(-1, 0, str(ex))

        siteName = get.siteName

        file = self.setupPath + '/panel/vhost/nginx/' + siteName + '.conf'
        if not os.path.exists(file):
            file = self.setupPath + '/panel/vhost/nginx/node_' + siteName + '.conf'
        conf = public.readFile(file)
        if conf:
            rep = "\n\\s*#HTTP_TO_HTTPS_START(.|\n){1,300}#HTTP_TO_HTTPS_END"
            conf = re.sub(rep, '', conf)
            rep = r"\s+ssl_certificate\s+.+;\s+ssl_certificate_key\s+.+;"
            conf = re.sub(rep, '', conf)
            rep = "\\s+ssl_protocols\\s+.+;\n"
            conf = re.sub(rep, '', conf)
            rep = "\\s+ssl_ciphers\\s+.+;\n"
            conf = re.sub(rep, '', conf)
            rep = "\\s+ssl_prefer_server_ciphers\\s+.+;\n"
            conf = re.sub(rep, '', conf)
            rep = "\\s+ssl_session_cache\\s+.+;\n"
            conf = re.sub(rep, '', conf)
            rep = "\\s+ssl_session_timeout\\s+.+;\n"
            conf = re.sub(rep, '', conf)
            rep = "\\s+ssl_ecdh_curve\\s+.+;\n"
            conf = re.sub(rep, '', conf)
            rep = "\\s+ssl_session_tickets\\s+.+;\n"
            conf = re.sub(rep, '', conf)
            rep = "\\s+ssl_stapling\\s+.+;\n"
            conf = re.sub(rep, '', conf)
            rep = "\\s+ssl_stapling_verify\\s+.+;\n"
            conf = re.sub(rep, '', conf)
            rep = "\\s+add_header\\s+.+;\n"
            conf = re.sub(rep, '', conf)
            rep = "\\s+add_header\\s+.+;\n"
            conf = re.sub(rep, '', conf)
            rep = r"\s+ssl\s+on;"
            conf = re.sub(rep, '', conf)
            rep = r"\s+error_page\s497.+;"
            conf = re.sub(rep, '', conf)
            rep = "\\s+if.+server_port.+\n.+\n\\s+\\s*}"
            conf = re.sub(rep, '', conf)
            rep = r"\s+listen\s+443.*;"
            conf = re.sub(rep, '', conf)
            rep = r"\s+listen\s+\[::\]:443.*;"
            conf = re.sub(rep, '', conf)
            rep = r"\s+http2\s+on;"
            conf = re.sub(rep, '', conf)
            public.writeFile(file, conf)

        file = self.setupPath + '/panel/vhost/apache/' + siteName + '.conf'
        if not os.path.exists(file):
            file = self.setupPath + '/panel/vhost/apache/node_' + siteName + '.conf'
        conf = public.readFile(file)
        if conf:
            rep = "\n<VirtualHost \\*\\:443>(.|\n)*<\\/VirtualHost>"
            conf = re.sub(rep, '', conf)
            rep = "\n\\s*#HTTP_TO_HTTPS_START(.|\n){1,250}#HTTP_TO_HTTPS_END"
            conf = re.sub(rep, '', conf)
            rep = "NameVirtualHost  *:443\n"
            conf = conf.replace(rep, '')
            public.writeFile(file, conf)

        # OLS
        ssl_file = self.setupPath + '/panel/vhost/openlitespeed/detail/ssl/{}.conf'.format(siteName)
        detail_file = self.setupPath + '/panel/vhost/openlitespeed/detail/' + siteName + '.conf'
        force_https = self.setupPath + '/panel/vhost/openlitespeed/redirect/' + siteName
        string = 'rm -f {}/force_https.conf*'.format(force_https)
        public.ExecShell(string)
        detail_conf = public.readFile(detail_file)
        if detail_conf:
            detail_conf = detail_conf.replace('\ninclude ' + ssl_file, '')
            public.writeFile(detail_file, detail_conf)
        public.ExecShell('rm -f {}*'.format(ssl_file))

        self._del_ols_443_domain(siteName)
        partnerOrderId = '/www/server/panel/vhost/cert/' + siteName + '/partnerOrderId'
        if os.path.exists(partnerOrderId): public.ExecShell('rm -f ' + partnerOrderId)
        p_file = '/etc/letsencrypt/live/' + siteName + '/partnerOrderId'
        if os.path.exists(p_file): public.ExecShell('rm -f ' + p_file)

        public.write_log_gettext('Site manager', 'Site [{}] turned off SSL successfully!', (siteName,))
        if hasattr(get, "reload") and int(get.reload) == 1:
            public.serviceReload()
        # ================== domian ssl v2 part =========================
        try:
            from ssl_domainModelV2.model import DnsDomainSSL
            for ssl in DnsDomainSSL.objects.all():
                if get.siteName in ssl.sites_uf:
                    ssl.sites_uf.remove(get.siteName)
                    ssl.user_for["sites"] = ssl.sites_uf
                    ssl.save()
                    break
        except:
            pass

        return public.return_message(0, 0, public.lang("SSL turned off!"))

    def _del_ols_443_domain(self, sitename):
        file = "/www/server/panel/vhost/openlitespeed/listen/443.conf"
        conf = public.readFile(file)
        if conf:
            rep = '\n\\s*map\\s*{}.*'.format(sitename)
            conf = re.sub(rep, '', conf)
            if not "map " in conf:
                public.ExecShell('rm -f {}*'.format(file))
                return
            public.writeFile(file, conf)

    # 取SSL状态
    def GetSSL(self, get):
        # 校验参数
        try:
            get.validate([
                Param('siteName').String(),
            ], [
                public.validate.trim_filter(),
            ])
        except Exception as ex:
            public.print_log("error info: {}".format(ex))
            return public.return_message(-1, 0, str(ex))

        siteName = get.siteName
        path = os.path.join('/www/server/panel/vhost/cert/', siteName)
        if not os.path.isfile(os.path.join(path, "fullchain.pem")) and not os.path.isfile(
                os.path.join(path, "privkey.pem")):
            path = os.path.join('/etc/letsencrypt/live/', siteName)
        type = 0
        if os.path.exists(path + '/README'):  type = 1
        if os.path.exists(path + '/partnerOrderId'):  type = 2
        if os.path.exists(path + '/certOrderId'):  type = 3
        csrpath = path + "/fullchain.pem"  # 生成证书路径
        keypath = path + "/privkey.pem"  # 密钥文件路径
        key = public.readFile(keypath)
        csr = public.readFile(csrpath)
        file = self.setupPath + '/panel/vhost/' + public.get_webserver() + '/' + siteName + '.conf'

        # 是否为node项目
        if not os.path.exists(file):
            file = self.setupPath + '/panel/vhost/' + public.get_webserver() + '/node_' + siteName + '.conf'

        if not os.path.exists(file):
            file = self.setupPath + '/panel/vhost/' + public.get_webserver() + '/java_' + siteName + '.conf'

        if not os.path.exists(file):
            file = self.setupPath + '/panel/vhost/' + public.get_webserver() + '/go_' + siteName + '.conf'

        if not os.path.exists(file):
            file = self.setupPath + '/panel/vhost/' + public.get_webserver() + '/other_' + siteName + '.conf'

        if not os.path.exists(file):
            file = self.setupPath + '/panel/vhost/' + public.get_webserver() + '/python_' + siteName + '.conf'

        if not os.path.exists(file):
            file = self.setupPath + '/panel/vhost/' + public.get_webserver() + '/net_' + siteName + '.conf'

        if not os.path.exists(file):
            file = self.setupPath + '/panel/vhost/' + public.get_webserver() + '/html_' + siteName + '.conf'

        if public.get_webserver() == "openlitespeed":
            file = self.setupPath + '/panel/vhost/' + public.get_webserver() + '/detail/' + siteName + '.conf'

        conf = public.readFile(file)
        if not conf:
            return public.fail_v2(public.lang("The specified website profile does not exist"))
        if public.get_webserver() == 'nginx':
            keyText = 'ssl_certificate'
        elif public.get_webserver() == 'apache':
            keyText = 'SSLCertificateFile'
        else:
            keyText = 'openlitespeed/detail/ssl'

        status = True
        if conf.find(keyText) == -1:
            status = False
            type = -1

        toHttps = self.IsToHttps(siteName)
        id = public.M('sites').where("name=?", (siteName,)).getField('id')
        domains = public.M('domain').where("pid=?", (id,)).field('name').select()
        email = public.M('users').where('id=?', (1,)).getField('email')
        if email == '287962566@qq.com': email = ''
        index = ''
        auth_type = 'http'
        if status is True:
            if type != 1:
                import acme_v2
                acme = acme_v2.acme_v2()
                index = acme.check_order_exists(csrpath)
                if index:
                    if index.find('/') == -1:
                        auth_type = acme._config['orders'][index]['auth_type']
                    type = 1
            else:
                crontab_file = 'vhost/cert/crontab.json'
                tmp = public.readFile(crontab_file)
                if tmp:
                    crontab_config = json.loads(tmp)
                    if siteName in crontab_config:
                        if 'dnsapi' in crontab_config[siteName]:
                            auth_type = 'dns'

            if os.path.exists(path + '/certOrderId'):  type = 3
        oid = -1
        if type == 3:
            oid = int(public.readFile(path + '/certOrderId'))

        # ================== domian ssl v2 part =========================
        try:
            from ssl_domainModelV2.service import CertHandler
            from ssl_domainModelV2.model import DnsDomainSSL
            ssl = None
            for s in DnsDomainSSL.objects.filter(user_for__like=f"%{siteName}%").fields("auto_renew"):
                if siteName in s.sites_uf:
                    ssl = s
                    break
            res = {
                'status': status,
                'oid': oid,
                'domain': domains,
                'key': key,
                'csr': csr,
                'type': type,
                'httpTohttps': toHttps,
                'cert_data': CertHandler.get_cert_info(cert_file_path=csrpath),
                'email': email,
                "index": index,
                'auth_type': auth_type,
                'tls_versions': self.get_ssl_protocol(get),
                'push': self.get_site_push_status(None, siteName, 'ssl'),
                'hash': CertHandler.get_hash(cert_pem=csr),
                'auto_renew': ssl.auto_renew if ssl else 0,
            }
        except Exception as e:
            return public.fail_v2(e)

        return public.success_v2(res)

    def get_site_push_status(self, get, siteName=None, stype=None):
        """
        @获取网站ssl告警通知状态
        @param get:
        @param siteName 网站名称
        @param stype 类型 ssl
        """
        import panel_push_v2 as panelPush
        if get:
            siteName = get.siteName
            stype = get.stype

        result = {}
        result['status'] = False
        try:
            data = {}
            try:
                data = json.loads(public.readFile('{}/class/push/push.json'.format(public.get_panel_path())))
            except:
                pass

            if not 'site_push' in data:
                return result

            ssl_data = data['site_push']
            for key in ssl_data.keys():
                if ssl_data[key]['type'] != stype:
                    continue

                project = ssl_data[key]['project']
                if project in [siteName, 'all']:
                    ssl_data[key]['id'] = key
                    ssl_data[key]['s_module'] = 'site_push'

                    if project == siteName:
                        result = ssl_data[key]
                        break

                    if project == 'all':
                        result = ssl_data[key]
        except:
            pass

        p_obj = panelPush.panelPush()
        return public.return_message(0, 0, p_obj.get_push_user(result))

    def set_site_status_multiple(self, get):
        '''
            @name 批量设置网站状态
            @author zhwen<2020-11-17>
            @param sites_id "1,2"
            @param status 0/1
        '''
        sites_id = get.sites_id.split(',')
        sites_name = []
        errors = {}
        day_time = time.time()
        for site_id in sites_id:
            get.id = site_id
            find = public.M('sites').where("id=?", (site_id,)).find()
            get.name = find['name']

            if get.status == '1':
                if find['edate'] != '0000-00-00' and public.to_date("%Y-%m-%d", find['edate']) < day_time:
                    errors[get.name] = "failed, site has expired"
                    continue
            sites_name.append(get.name)
            if get.status == '1':
                self.SiteStart(get, multiple=1)
            else:
                self.SiteStop(get, multiple=1)
        public.serviceReload()
        if get.status == '1':
            return_message = {
                'msg': public.get_msg_gettext('Enable website [{}] successfully', (','.join(sites_name),)),
                'error': {}, 'success': sites_name}
            return public.return_message(0, 0, return_message)
        else:
            return_message = {
                'msg': public.get_msg_gettext('Disable website [{}] successfully', (','.join(sites_name),)),
                'error': {}, 'success': sites_name}
            return public.return_message(0, 0, return_message)

    # 启动站点
    def SiteStart(self, get, multiple=None):
        # 校验参数
        try:
            get.validate([
                Param('name').String(),
                Param('id').Integer(),
            ], [
                public.validate.trim_filter(),
            ])
        except Exception as ex:
            public.print_log("error info: {}".format(ex))
            return public.return_message(-1, 0, str(ex))

        id = get.id
        Path = self.setupPath + '/stop'
        sitePath = public.M('sites').where("id=?", (id,)).getField('path')

        # nginx
        file = self.setupPath + '/panel/vhost/nginx/' + get.name + '.conf'
        conf = public.readFile(file)
        if conf:
            conf = conf.replace(Path, sitePath)
            conf = conf.replace("#include", "include")
            public.writeFile(file, conf)
        # apache
        file = self.setupPath + '/panel/vhost/apache/' + get.name + '.conf'
        conf = public.readFile(file)
        if conf:
            conf = conf.replace(Path, sitePath)
            conf = conf.replace("#IncludeOptional", "IncludeOptional")
            public.writeFile(file, conf)

        # OLS
        file = self.setupPath + '/panel/vhost/openlitespeed/' + get.name + '.conf'
        conf = public.readFile(file)
        if conf:
            rep = r'vhRoot\s*{}'.format(Path)
            new_content = 'vhRoot {}'.format(sitePath)
            conf = re.sub(rep, new_content, conf)
            public.writeFile(file, conf)

        public.M('sites').where("id=?", (id,)).setField('status', '1')
        if not multiple:
            public.serviceReload()
        public.write_log_gettext('Site manager', 'Site [{}] started!', (get.name,))
        return_message = public.return_msg_gettext(True, 'Site started')
        del return_message['status']
        return public.return_message(0, 0, return_message['msg'])

    def _process_has_run_dir(self, website_name, website_path, stop_path):
        '''
            @name 当网站存在允许目录时停止网站需要做处理
            @author zhwen<2020-11-17>
            @param site_id 1
            @param names test,baohu
        '''
        conf = public.readFile(self.setupPath + '/panel/vhost/nginx/' + website_name + '.conf')
        if not conf:
            return False
        try:
            really_path = re.search(r'root\s+(.*);', conf).group(1)
            tmp = stop_path + '/' + really_path.replace(website_path + '/', '')
            public.ExecShell('mkdir {t} && ln -s {s}/index.html {t}/index.html'.format(t=tmp, s=stop_path))
        except:
            pass

    # 停止站点
    def SiteStop(self, get, multiple=None):
        path = self.setupPath + '/stop'
        id = get.id
        site_status = public.M('sites').where("id=?", (id,)).getField('status')
        if str(site_status) != '1':
            return public.return_message(0, 0, public.lang("Site stopped"))
        if not os.path.exists(path):
            os.makedirs(path)
            public.downloadFile('https://node.aapanel.com/stop_en.html', path + '/index.html')

        # if 'This site has been closed by administrator' not in public.readFile(path + '/index.html'):
        #     public.downloadFile('http://download.bt.cn/stop_en.html', path + '/index.html')

        binding = public.M('binding').where('pid=?', (id,)).field('id,pid,domain,path,port,addtime').select()
        for b in binding:
            bpath = path + '/' + b['path']
            if not os.path.exists(bpath):
                public.ExecShell('mkdir -p ' + bpath)
                public.ExecShell('ln -sf ' + path + '/index.html ' + bpath + '/index.html')

        sitePath = public.M('sites').where("id=?", (id,)).getField('path')
        self._process_has_run_dir(get.name, sitePath, path)
        # nginx
        file = self.setupPath + '/panel/vhost/nginx/' + get.name + '.conf'
        conf = public.readFile(file)
        if conf:
            src_path = 'root ' + sitePath
            dst_path = 'root ' + path
            if conf.find(src_path) != -1:
                conf = conf.replace(src_path, dst_path)
            else:
                conf = conf.replace(sitePath, path)
            conf = conf.replace("include", "#include")
            public.writeFile(file, conf)

        # apache
        file = self.setupPath + '/panel/vhost/apache/' + get.name + '.conf'
        conf = public.readFile(file)
        if conf:
            conf = conf.replace(sitePath, path)
            conf = conf.replace("IncludeOptional", "#IncludeOptional")
            public.writeFile(file, conf)
        # OLS
        file = self.setupPath + '/panel/vhost/openlitespeed/' + get.name + '.conf'
        conf = public.readFile(file)
        if conf:
            rep = r'vhRoot\s*{}'.format(sitePath)
            new_content = 'vhRoot {}'.format(path)
            conf = re.sub(rep, new_content, conf)
            public.writeFile(file, conf)

        public.M('sites').where("id=?", (id,)).setField('status', '0')

        # 添加清除站点缓存,仅wp2
        project_type = public.M('sites').where("id=?", (id,)).getField('project_type')
        if project_type == 'WP2':
            self.purge_all_cache(public.to_dict_obj({'s_id': id}))

        if not multiple:
            public.serviceReload()
        public.write_log_gettext('Site manager', 'Site [{}] stopped!', (get.name,))
        return_message = public.return_msg_gettext(True, 'Site stopped')
        del return_message['status']
        return public.return_message(0, 0, return_message['msg'])

    # 取流量限制值
    def GetLimitNet(self, get):
        # 校验参数
        try:
            get.validate([
                Param('id').Integer(),

            ], [
                public.validate.trim_filter(),
            ])
        except Exception as ex:
            public.print_log("error info: {}".format(ex))
            return public.return_message(-1, 0, str(ex))

        id = get.id

        # 取回配置文件
        siteName = public.M('sites').where("id=?", (id,)).getField('name')
        filename = self.setupPath + '/panel/vhost/nginx/' + siteName + '.conf'

        # 站点总并发
        data = {}
        conf = public.readFile(filename)
        try:
            rep = r"\s+limit_conn\s+perserver\s+([0-9]+);"
            tmp = re.search(rep, conf).groups()
            data['perserver'] = int(tmp[0])

            # IP并发限制
            rep = r"\s+limit_conn\s+perip\s+([0-9]+);"
            tmp = re.search(rep, conf).groups()
            data['perip'] = int(tmp[0])

            # 请求并发限制
            rep = r"\s+limit_rate\s+([0-9]+)\w+;"
            tmp = re.search(rep, conf).groups()
            data['limit_rate'] = int(tmp[0])
        except:
            data['perserver'] = 0
            data['perip'] = 0
            data['limit_rate'] = 0

        return public.return_message(0, 0, data)

    # 设置流量限制
    def SetLimitNet(self, get):
        # 校验参数
        try:
            get.validate([
                Param('id').Integer(),
                Param('perserver').Integer(),
                Param('perip').Integer(),
                Param('limit_rate').Integer(),

            ], [
                public.validate.trim_filter(),
            ])
        except Exception as ex:
            public.print_log("error info: {}".format(ex))
            return public.return_message(-1, 0, str(ex))

        if (public.get_webserver() != 'nginx'): return public.return_message(-1, 0, public.lang("Site Traffic Control only supports Nginx Web Server!"))

        id = get.id
        if int(get.perserver) < 1 or int(get.perip) < 1 or int(get.perip) < 1:
            return public.return_message(-1, 0, public.lang("Concurrency restrictions, IP restrictions, traffic restrictions must be greater than 0"))
        perserver = 'limit_conn perserver ' + get.perserver + ';'
        perip = 'limit_conn perip ' + get.perip + ';'
        limit_rate = 'limit_rate ' + get.limit_rate + 'k;'

        # 取回配置文件
        siteName = public.M('sites').where("id=?", (id,)).getField('name')
        filename = self.setupPath + '/panel/vhost/nginx/' + siteName + '.conf'
        conf = public.readFile(filename)

        # 设置共享内存
        oldLimit = self.setupPath + '/panel/vhost/nginx/limit.conf'
        if (os.path.exists(oldLimit)): os.remove(oldLimit)
        limit = self.setupPath + '/nginx/conf/nginx.conf'
        nginxConf = public.readFile(limit)
        limitConf = "limit_conn_zone $binary_remote_addr zone=perip:10m;\n\t\tlimit_conn_zone $server_name zone=perserver:10m;"
        nginxConf = nginxConf.replace("#limit_conn_zone $binary_remote_addr zone=perip:10m;", limitConf)
        public.writeFile(limit, nginxConf)

        if (conf.find('limit_conn perserver') != -1):
            # 替换总并发
            rep = r"limit_conn\s+perserver\s+([0-9]+);"
            conf = re.sub(rep, perserver, conf)

            # 替换IP并发限制
            rep = r"limit_conn\s+perip\s+([0-9]+);"
            conf = re.sub(rep, perip, conf)

            # 替换请求流量限制
            rep = r"limit_rate\s+([0-9]+)\w+;"
            conf = re.sub(rep, limit_rate, conf)
        else:
            conf = conf.replace('#error_page 404/404.html;',
                                "#error_page 404/404.html;\n    " + perserver + "\n    " + perip + "\n    " + limit_rate)

        import shutil
        shutil.copyfile(filename, self.nginx_conf_bak)
        public.writeFile(filename, conf)
        isError = public.checkWebConfig()
        if (isError != True):
            if os.path.exists(self.nginx_conf_bak): shutil.copyfile(self.nginx_conf_bak, filename)
            return public.return_message(-1, 0,
                                         public.lang('ERROR: <br><a style="color:red;">' + isError.replace("\n", '<br>') + '</a>'))

        public.serviceReload()
        public.write_log_gettext('Site manager', 'Site [{}] traffic control turned on!', (siteName,))
        return public.return_message(0, 0, public.lang("Setup successfully!"))

    # 关闭流量限制
    def CloseLimitNet(self, get):
        id = get.id
        # 取回配置文件
        siteName = public.M('sites').where("id=?", (id,)).getField('name')
        filename = self.setupPath + '/panel/vhost/nginx/' + siteName + '.conf'
        conf = public.readFile(filename)
        # 清理总并发
        rep = r"\s+limit_conn\s+perserver\s+([0-9]+);"
        conf = re.sub(rep, '', conf)

        # 清理IP并发限制
        rep = r"\s+limit_conn\s+perip\s+([0-9]+);"
        conf = re.sub(rep, '', conf)

        # 清理请求流量限制
        rep = r"\s+limit_rate\s+([0-9]+)\w+;"
        conf = re.sub(rep, '', conf)
        public.writeFile(filename, conf)
        public.serviceReload()
        public.write_log_gettext('Site manager', 'Site Traffic Control has been turned off!', (siteName,))
        return_message = public.return_msg_gettext(True, 'Site Traffic Control has been turned off!')
        del return_message['status']
        return public.return_message(0, 0, return_message['msg'])

    # 取301配置状态
    def Get301Status(self, get):
        siteName = get.siteName
        result = {}
        domains = ''
        id = public.M('sites').where("name=?", (siteName,)).getField('id')
        tmp = public.M('domain').where("pid=?", (id,)).field('name').select()
        node = public.M('sites').where('id=? and project_type=?', (id, 'Node')).count()
        if node:
            node = 'node_'
        else:
            node = ''
        for key in tmp:
            domains += key['name'] + ','
        try:
            if (public.get_webserver() == 'nginx'):
                conf = public.readFile(self.setupPath + '/panel/vhost/nginx/' + node + siteName + '.conf')
                if conf.find('301-START') == -1:
                    result['domain'] = domains[:-1]
                    result['src'] = ""
                    result['status'] = False
                    result['url'] = "http://"
                    return public.return_message(0, 0, result)
                rep = r"return\s+301\s+((http|https)\://.+);"
                arr = re.search(rep, conf).groups()[0]
                rep = r"'\^(([\w-]+\.)+[\w-]+)'"
                tmp = re.search(rep, conf)
                src = ''
                if tmp: src = tmp.groups()[0]
            elif public.get_webserver() == 'apache':
                conf = public.readFile(self.setupPath + '/panel/vhost/apache/' + node + siteName + '.conf')
                if conf.find('301-START') == -1:
                    result['domain'] = domains[:-1]
                    result['src'] = ""
                    result['status'] = False
                    result['url'] = "http://"
                    return public.return_message(0, 0, result)
                rep = r"RewriteRule\s+.+\s+((http|https)\://.+)\s+\["
                arr = re.search(rep, conf).groups()[0]
                rep = r"\^((\w+\.)+\w+)\s+\[NC"
                tmp = re.search(rep, conf)
                src = ''
                if tmp: src = tmp.groups()[0]
            else:
                conf = public.readFile(
                    self.setupPath + '/panel/vhost/openlitespeed/redirect/{s}/{s}.conf'.format(s=siteName))
                if not conf:
                    result['domain'] = domains[:-1]
                    result['src'] = ""
                    result['status'] = False
                    result['url'] = "http://"
                    return result
                rep = r"RewriteRule\s+.+\s+((http|https)\://.+)\s+\["
                arr = re.search(rep, conf).groups()[0]
                rep = r"\^((\w+\.)+\w+)\s+\[NC"
                tmp = re.search(rep, conf)
                src = ''
                if tmp: src = tmp.groups()[0]
        except:
            src = ''
            arr = 'http://'

        result['domain'] = domains[:-1]
        result['src'] = src.replace("'", '')
        result['status'] = True
        if (len(arr) < 3): result['status'] = False
        result['url'] = arr

        return public.return_message(0, 0, result)

    # 设置301配置
    def Set301Status(self, get):
        siteName = get.siteName
        srcDomain = get.srcDomain
        toDomain = get.toDomain
        type = get.type
        rep = r"(http|https)\://.+"
        if not re.match(rep, toDomain):
            return_message = public.return_msg_gettext(False, 'URL address is invalid!')
            del return_message['status']
            return public.return_message(-1, 0, return_message['msg'])

        # nginx
        filename = self.setupPath + '/panel/vhost/nginx/' + siteName + '.conf'
        mconf = public.readFile(filename)
        if mconf == False:
            return_message = public.return_msg_gettext(False, 'Configuration file not exist')
            del return_message['status']
            return public.return_message(-1, 0, return_message['msg'])
        if (srcDomain == 'all'):
            conf301 = "\t#301-START\n\t\treturn 301 " + toDomain + "$request_uri;\n\t#301-END"
        else:
            conf301 = "\t#301-START\n\t\tif ($host ~ '^" + srcDomain + "'){\n\t\t\treturn 301 " + toDomain + "$request_uri;\n\t\t}\n\t#301-END"
        if type == '1':
            mconf = mconf.replace("#error_page 404/404.html;", "#error_page 404/404.html;\n" + conf301)
        else:
            rep = "\\s+#301-START(.|\n){1,300}#301-END"
            mconf = re.sub(rep, '', mconf)
        public.writeFile(filename, mconf)

        # apache
        filename = self.setupPath + '/panel/vhost/apache/' + siteName + '.conf'
        mconf = public.readFile(filename)
        if mconf == False:
            return_message = public.return_msg_gettext(False, 'Configuration file not exist')
            del return_message['status']
            return public.return_message(-1, 0, return_message['msg'])
        if type == '1':
            if (srcDomain == 'all'):
                conf301 = "\n\t#301-START\n\t<IfModule mod_rewrite.c>\n\t\tRewriteEngine on\n\t\tRewriteRule ^(.*)$ " + toDomain + "$1 [L,R=301]\n\t</IfModule>\n\t#301-END\n"
            else:
                conf301 = "\n\t#301-START\n\t<IfModule mod_rewrite.c>\n\t\tRewriteEngine on\n\t\tRewriteCond %{HTTP_HOST} ^" + srcDomain + " [NC]\n\t\tRewriteRule ^(.*) " + toDomain + "$1 [L,R=301]\n\t</IfModule>\n\t#301-END\n"
            rep = "combined"
            mconf = mconf.replace(rep, rep + "\n\t" + conf301)
        else:
            rep = "\n\\s+#301-START(.|\n){1,300}#301-END\n*"
            mconf = re.sub(rep, '\n\n', mconf, 1)
            mconf = re.sub(rep, '\n\n', mconf, 1)

        public.writeFile(filename, mconf)

        # OLS
        conf_dir = self.setupPath + '/panel/vhost/openlitespeed/redirect/{}/'.format(siteName)
        if not os.path.exists(conf_dir):
            os.makedirs(conf_dir)
        file = conf_dir + siteName + '.conf'
        if type == '1':
            if (srcDomain == 'all'):
                conf301 = "#301-START\nRewriteEngine on\nRewriteRule ^(.*)$ " + toDomain + "$1 [L,R=301]#301-END\n"
            else:
                conf301 = "#301-START\nRewriteEngine on\nRewriteCond %{HTTP_HOST} ^" + srcDomain + " [NC]\nRewriteRule ^(.*) " + toDomain + "$1 [L,R=301]\n#301-END\n"
            public.writeFile(file, conf301)
        else:
            public.ExecShell('rm -f {}*'.format(file))

        isError = public.checkWebConfig()
        if (isError != True):
            return_message = public.return_msg_gettext(False,
                                                       'ERROR: <br><a style="color:red;">' + isError.replace("\n",
                                                                                                             '<br>') + '</a>')
            del return_message['status']
            return public.return_message(-1, 0, return_message['msg'])

        public.serviceReload()
        return_message = public.return_msg_gettext(True, 'Setup successfully!')
        del return_message['status']
        return public.return_message(0, 0, return_message['msg'])

    # 取子目录绑定
    def GetDirBinding(self, get):
        # 校验参数
        try:
            get.validate([
                Param('id').Integer(),
            ], [
                public.validate.trim_filter(),
            ])
        except Exception as ex:
            public.print_log("error info: {}".format(ex))
            return public.return_message(-1, 0, str(ex))

        path = public.M('sites').where('id=?', (get.id,)).getField('path')
        if isinstance(path, str) and path.startswith('/'):
            if not os.path.exists(path):
                checks = ['/', '/usr', '/etc']
                if path in checks:
                    data = {}
                    data['dirs'] = []
                    data['binding'] = []
                    return data
                public.ExecShell('mkdir -p ' + path)
                public.ExecShell('chmod 755 ' + path)
                public.ExecShell('chown www:www ' + path)
                get.path = path
                self.SetDirUserINI(get)
                siteName = public.M('sites').where('id=?', (get.id,)).getField('name')
                public.write_log_gettext('Site manager', "Site [{}], document root [{}] does NOT exist, recreated!",
                                         (siteName, path))
        dirnames = []
        # 取运行目录
        run_path = self.GetRunPath(get)['message']['result']
        if run_path: path += run_path
        # 遍历目录
        if os.path.exists(path):
            for filename in os.listdir(path):
                try:
                    json.dumps(filename)
                    if sys.version_info[0] == 2:
                        filename = filename.encode('utf-8')
                    else:
                        filename.encode('utf-8')
                    filePath = path + '/' + filename
                    if os.path.islink(filePath): continue
                    if os.path.isdir(filePath):
                        dirnames.append(filename)
                except:
                    pass
        data = {}
        data['run_path'] = run_path  # 运行目录
        data['dirs'] = dirnames
        data['binding'] = public.M('binding').where('pid=?', (get.id,)).field(
            'id,pid,domain,path,port,addtime').select()
        # 标记子目录是否存在
        for dname in data['binding']:
            _path = os.path.join(path, dname['path'])
            if not os.path.exists(_path):
                _path = _path.replace(run_path, '')
                if not os.path.exists(_path):
                    dname['path'] += '<a style="color:red;"> >> error: directory does not exist</a>'
                else:
                    dname['path'] = '../' + dname['path']

        return public.return_message(0, 0, data)

    # 添加子目录绑定
    def AddDirBinding(self, get):
        import shutil
        id = get.id
        tmp = get.domain.split(':')
        domain = tmp[0].lower()
        # 中文域名转码
        domain = public.en_punycode(domain)
        port = '80'
        version = ''
        if len(tmp) > 1: port = tmp[1]
        if not hasattr(get, 'dirName'):
            return_message = public.return_msg_gettext(False, 'Directory cannot be empty!')
            del return_message['status']
            return public.return_message(-1, 0, return_message['msg'])
        dirName = get.dirName
        reg = r"^([\w\-\*]{1,100}\.){1,4}([\w\-]{1,100}|[\w\-]{1,100}\.[\w\-]{1,100})$"
        if not re.match(reg, domain):
            return_message = public.return_msg_gettext(False, 'Format of primary domain is incorrect')
            del return_message['status']
            return public.return_message(-1, 0, return_message['msg'])
        siteInfo = public.M('sites').where("id=?", (id,)).field('id,path,name,service_type').find()
        # 实际运行目录
        root_path = siteInfo['path']
        run_path = self.GetRunPath(get)['message']['result']
        if run_path: root_path += run_path

        webdir = root_path + '/' + dirName
        webdir = webdir.replace('//', '/').strip()
        if not os.path.exists(webdir):  # 如果在运行目录找不到指定子目录，尝试到根目录查找
            root_path = siteInfo['path']
            webdir = root_path + '/' + dirName
            webdir = webdir.replace('//', '/').strip()

        sql = public.M('binding')
        if sql.where("domain=?", (domain,)).count() > 0:
            return_message = public.return_msg_gettext(False, 'The domain you tried to add already exists!')
            del return_message['status']
            return public.return_message(-1, 0, return_message['msg'])
        if public.M('domain').where("name=?", (domain,)).count() > 0:
            return_message = public.return_msg_gettext(False,
                                                       'The domain you tried to add already exists!')
            del return_message['status']
            return public.return_message(-1, 0, return_message['msg'])

        filename = self.setupPath + '/panel/vhost/nginx/' + siteInfo['name'] + '.conf'
        nginx_conf_file = filename
        conf = public.readFile(filename)
        if conf:
            listen_ipv6 = ''
            if self.is_ipv6: listen_ipv6 = "\n    listen [::]:%s;" % port
            try:
                rep = r"enable-php-(\w{2,5})\.conf"
                tmp = re.search(rep, conf)
                if not tmp:
                    rep = r"enable-php-(\d+-wpfastcgi).conf"
                    tmp = re.search(rep, conf)
            except:
                return public.return_message(-1, 0, public.lang("Get enable php config failed!"))
            tmp = tmp.groups()
            version = tmp[0]

            if public.get_multi_webservice_status() and siteInfo['service_type'] in ['openlitespeed', 'apache']:
                port_p = '8188' if siteInfo['service_type'] == 'openlitespeed' else '8288'
                bindingConf = r'''
#BINDING-%s-START
server
{
    listen %s;%s
    server_name %s;
    index index.php index.html index.htm default.php default.htm default.html;
    root %s;

    # include enable-php-%s.conf;
    include %s/panel/vhost/rewrite/%s.conf;
    %s
    location ~ ^/(\.user.ini|\.htaccess|\.git|\.env|\.svn|\.project|LICENSE|README.md)
    {
        return 404;
    }

    %s
    location ~ \.well-known{
        allow all;
        root %s;
        try_files $uri =404;
    }
    location / {
        proxy_pass http://127.0.0.1:%s;

        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_set_header REMOTE-HOST $remote_addr;
        proxy_set_header SERVER_PROTOCOL $server_protocol;
        proxy_set_header HTTPS $https;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $connection_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header REMOTE_ADDR $remote_addr;
        proxy_set_header REMOTE_PORT $remote_port;
        add_header Cache-Control no-cache;
    }
    #Prohibit putting sensitive files in certificate verification directory
    if ( $uri ~ "^/\.well-known/.*\.(php|jsp|py|js|css|lua|ts|go|zip|tar\.gz|rar|7z|sql|bak)$" ) {
        return 403;
    }

    # Forbidden files or directories
    location ~ ^/(\.user.ini|\.htaccess|\.git|\.env|\.svn|\.project|LICENSE|README.md)
    {
        return 404;
    }
    access_log %s.log;
    error_log  %s.error.log;
}
#BINDING-%s-END''' % (domain, port, listen_ipv6, domain, webdir, version, self.setupPath,
                      siteInfo['name'],
                      ("# Forbidden files or directories"), public.get_msg_gettext(
    '# Directory verification related settings for one-click application for SSL certificate'),webdir,port_p,
                      public.GetConfigValue('logs_path') + '/' + siteInfo['name'],
                      public.GetConfigValue('logs_path') + '/' + siteInfo['name'], domain)
            else:
                bindingConf = r'''
    #BINDING-%s-START
    server
    {
        listen %s;%s
        server_name %s;
        index index.php index.html index.htm default.php default.htm default.html;
        root %s;
    
        include enable-php-%s.conf;
        include %s/panel/vhost/rewrite/%s.conf;
        %s
        location ~ ^/(\.user.ini|\.htaccess|\.git|\.env|\.svn|\.project|LICENSE|README.md)
        {
            return 404;
        }
    
        %s
        location ~ \.well-known{
            allow all;
        }
    
        location ~ .*\\.(gif|jpg|jpeg|png|bmp|swf)$
        {
            expires      30d;
            error_log /dev/null;
            access_log /dev/null; 
        }
        location ~ .*\\.(js|css)?$
        {
            expires      12h;
            error_log /dev/null;
            access_log /dev/null; 
        }
        access_log %s.log;
        error_log  %s.error.log;
    }
    #BINDING-%s-END''' % (domain, port, listen_ipv6, domain, webdir, version, self.setupPath, siteInfo['name'],
                          ("# Forbidden files or directories"), public.get_msg_gettext(
                    '# Directory verification related settings for one-click application for SSL certificate'),
                          public.GetConfigValue('logs_path') + '/' + siteInfo['name'],
                          public.GetConfigValue('logs_path') + '/' + siteInfo['name'], domain)

            conf += bindingConf
            shutil.copyfile(filename, self.nginx_conf_bak)
            public.writeFile(filename, conf)

        filename = self.setupPath + '/panel/vhost/apache/' + siteInfo['name'] + '.conf'
        conf = public.readFile(filename)
        if conf:
            try:
                try:
                    httpdVersion = public.readFile(self.setupPath + '/apache/version.pl').strip()
                except:
                    httpdVersion = ""
                if httpdVersion == '2.2':
                    phpConfig = ""
                    apaOpt = "Order allow,deny\n\t\tAllow from all"
                else:
                    # rep = r"php-cgi-([0-9]{2,3})\.sock"
                    # tmp = re.search(rep,conf).groups()
                    # version = tmp[0]
                    version = public.get_php_version_conf(conf)
                    phpConfig = '''
    #PHP     
    <FilesMatch \\.php>
        SetHandler "proxy:%s"
    </FilesMatch>
    ''' % (public.get_php_proxy(version, 'apache'),)
                    apaOpt = 'Require all granted'
                port_apache = port
                if public.get_multi_webservice_status():
                    port_apache = '8288'

                bindingConf = r'''

#BINDING-%s-START
<VirtualHost *:%s>
    ServerAdmin webmaster@example.com
    DocumentRoot "%s"
    ServerAlias %s
    #errorDocument 404 /404.html
    ErrorLog "%s-error_log"
    CustomLog "%s-access_log" combined
    %s

    #DENY FILES
     <Files ~ (\.user.ini|\.htaccess|\.git|\.env|\.svn|\.project|LICENSE|README.md)$>
       Order allow,deny
       Deny from all
    </Files>

    #PATH
    <Directory "%s">
        SetOutputFilter DEFLATE
        Options FollowSymLinks
        AllowOverride All
        %s
        DirectoryIndex index.php index.html index.htm default.php default.html default.htm
    </Directory>
</VirtualHost>
#BINDING-%s-END''' % (domain, port_apache, webdir, domain, public.GetConfigValue('logs_path') + '/' + siteInfo['name'],
                      public.GetConfigValue('logs_path') + '/' + siteInfo['name'], phpConfig, webdir, apaOpt, domain)

                conf += bindingConf
                shutil.copyfile(filename, self.apache_conf_bak)
                public.writeFile(filename, conf)
            except:
                pass
        get.webname = siteInfo['name']
        get.port = port
        self.phpVersion = version
        self.siteName = siteInfo['name']
        self.sitePath = webdir
        listen_file = self.setupPath + "/panel/vhost/openlitespeed/listen/80.conf"
        listen_conf = public.readFile(listen_file)
        if listen_conf:
            rep = r'secure\s*0'
            map = '\tmap {}_{} {}'.format(siteInfo['name'], dirName, domain)
            listen_conf = re.sub(rep, 'secure 0\n' + map, listen_conf)
            public.writeFile(listen_file, listen_conf)
        self.openlitespeed_add_site(get)

        # 检查配置是否有误
        isError = public.checkWebConfig()
        if isError != True:
            if os.path.exists(self.nginx_conf_bak): shutil.copyfile(self.nginx_conf_bak, nginx_conf_file)
            if os.path.exists(self.apache_conf_bak): shutil.copyfile(self.apache_conf_bak, filename)
            return_message = public.return_msg_gettext(False,
                                                       'ERROR: <br><a style="color:red;">' + isError.replace("\n",
                                                                                                             '<br>') + '</a>')
            del return_message['status']
            return public.return_message(-1, 0, return_message['msg'])

        public.M('binding').add('pid,domain,port,path,addtime', (id, domain, port, dirName, public.getDate()))
        public.serviceReload()
        public.write_log_gettext('Site manager', 'Site [{}] subdirectory [{}] bound to [{}]',
                                 (siteInfo['name'], dirName, domain))
        return_message = public.return_msg_gettext(True, 'Successfully added')
        del return_message['status']
        return public.return_message(0, 0, return_message['msg'])

    def delete_dir_bind_multiple(self, get):
        '''
            @name 批量删除网站
            @author zhwen<2020-11-17>
            @param bind_ids 1,2,3
        '''
        bind_ids = get.bind_ids.split(',')
        del_successfully = []
        del_failed = {}
        for bind_id in bind_ids:
            get.id = bind_id
            domain = public.M('binding').where("id=?", (get.id,)).getField('domain')
            if not domain:
                continue
            try:
                self.DelDirBinding(get, multiple=1)
                del_successfully.append(domain)
            except:
                del_failed[domain] = public.lang("There was an error deleting, please try again.")
                pass
        public.serviceReload()
        return_message = {'msg': public.get_msg_gettext('Delete [{}] subdirectory binding successfully',
                                                        (','.join(del_successfully),)),
                          'error': del_failed,
                          'success': del_successfully}
        return public.return_message(0, 0, return_message)

    # 删除子目录绑定
    def DelDirBinding(self, get, multiple=None):
        id = get.id
        binding = public.M('binding').where("id=?", (id,)).field('id,pid,domain,path').find()
        siteName = public.M('sites').where("id=?", (binding['pid'],)).getField('name')

        # nginx
        filename = self.setupPath + '/panel/vhost/nginx/' + siteName + '.conf'
        conf = public.readFile(filename)
        if conf:
            rep = r"\s*.+BINDING-" + binding['domain'] + "-START(.|\n)+BINDING-" + binding['domain'] + "-END"
            conf = re.sub(rep, '', conf)
            public.writeFile(filename, conf)

        # apache
        filename = self.setupPath + '/panel/vhost/apache/' + siteName + '.conf'
        conf = public.readFile(filename)
        if conf:
            rep = r"\s*.+BINDING-" + binding['domain'] + "-START(.|\n)+BINDING-" + binding['domain'] + "-END"
            conf = re.sub(rep, '', conf)
            public.writeFile(filename, conf)

        # openlitespeed
        filename = self.setupPath + '/panel/vhost/openlitespeed/' + siteName + '.conf'
        conf = public.readFile(filename)
        rep = "#SUBDIR\\s*{s}_{d}\\s*START(\n|.)+#SUBDIR\\s*{s}_{d}\\s*END".format(s=siteName, d=binding['path'])
        if conf:
            conf = re.sub(rep, '', conf)
            public.writeFile(filename, conf)
        # 删除域名，前端需要传域名
        get.webname = siteName
        get.domain = binding['domain']
        self._del_ols_domain(get)

        # 清理子域名监听文件
        listen_file = self.setupPath + "/panel/vhost/openlitespeed/listen/80.conf"
        listen_conf = public.readFile(listen_file)
        if listen_conf:
            map_reg = r'\s*map\s*{}_{}.*'.format(siteName, binding['path'])
            listen_conf = re.sub(map_reg, '', listen_conf)
            public.writeFile(listen_file, listen_conf)
        # 清理detail文件
        detail_file = "{}/panel/vhost/openlitespeed/detail/{}_{}.conf".format(self.setupPath, siteName, binding['path'])
        public.ExecShell("rm -f {}*".format(detail_file))

        # 从数据库删除绑定
        public.M('binding').where("id=?", (id,)).delete()

        # 如果没有其它域名绑定同一子目录，则删除该子目录的伪静态规则
        if not public.M('binding').where("path=? AND pid=?", (binding['path'], binding['pid'])).count():
            filename = self.setupPath + '/panel/vhost/rewrite/' + siteName + '_' + binding['path'] + '.conf'
            if os.path.exists(filename): public.ExecShell('rm -rf %s' % filename)
        # 是否需要重载服务
        if not multiple:
            public.serviceReload()
        public.write_log_gettext('Site manager', 'Deleted site [{}] subdirectory [{}] binding',
                                 (siteName, binding['path']))
        return_message = public.return_msg_gettext(True, 'Successfully deleted')
        del return_message['status']
        return public.return_message(0, 0, return_message['msg'])

    # 取子目录Rewrite
    def GetDirRewrite(self, get):
        id = get.id
        find = public.M('binding').where("id=?", (id,)).field('id,pid,domain,path').find()
        site = public.M('sites').where("id=?", (find['pid'],)).field('id,name,path,service_type').find()
        # 兼容多服务
        webserver = public.get_webserver()
        if public.get_multi_webservice_status():
            webserver = site['service_type'] if site['service_type'] else 'nginx'

        if (webserver != 'nginx'):
            filename = site['path'] + '/' + find['path'] + '/.htaccess'
        else:
            filename = self.setupPath + '/panel/vhost/rewrite/' + site['name'] + '_' + find['path'] + '.conf'

        if hasattr(get, 'add'):
            public.writeFile(filename, '')
            if webserver == 'nginx':
                file = self.setupPath + '/panel/vhost/nginx/' + site['name'] + '.conf'
                conf = public.readFile(file)
                domain = find['domain']
                rep = "\n#BINDING-" + domain + "-START(.|\n)+BINDING-" + domain + "-END"
                match = re.search(rep, conf)
                if match:
                    tmp = match.group()
                    dirConf = tmp.replace(
                        'rewrite/' + site['name'] + '.conf;',
                        'rewrite/' + site['name'] + '_' + find['path'] + '.conf;'
                    )
                    conf = conf.replace(tmp, dirConf)
                    public.writeFile(file, conf)
                else:
                    public.WriteLog('Site manager', f"Subdirectory binding tag missing: {domain}, unable to automatically update rewrite references")
        data = {}
        return_status = -1
        if os.path.exists(filename):
            return_status = 0
            data['data'] = public.readFile(filename)
            data['rlist'] = ['0.default']
            if webserver == "openlitespeed":
                webserver = "apache"
            for ds in os.listdir('rewrite/' + webserver):
                if ds == 'list.txt': continue
                data['rlist'].append(ds[0:len(ds) - 5])
            data['filename'] = filename
        return public.return_message(return_status, 0, data)

    # 取默认文档
    def GetIndex(self, get):
        # 校验参数
        try:
            get.validate([
                Param('id').Integer(),
            ], [
                public.validate.trim_filter(),
            ])
        except Exception as ex:
            public.print_log("error info: {}".format(ex))
            return public.return_message(-1, 0, str(ex))

        id = get.id
        Name = public.M('sites').where("id=?", (id,)).getField('name')
        file = self.setupPath + '/panel/vhost/' + public.get_webserver() + '/' + Name + '.conf'
        if public.get_webserver() == 'openlitespeed':
            file = self.setupPath + '/panel/vhost/' + public.get_webserver() + '/detail/' + Name + '.conf'
        conf = public.readFile(file)
        if conf == False: return public.return_message(-1, 0, public.lang("Configuration file not exist"))
        if public.get_webserver() == 'nginx':
            rep = r"\s+index\s+(.+);"
        elif public.get_webserver() == 'apache':
            rep = "DirectoryIndex\\s+(.+)\n"
        else:
            rep = "indexFiles\\s+(.+)\n"
        if re.search(rep, conf):
            tmp = re.search(rep, conf).groups()
            if public.get_webserver() == 'openlitespeed':
                return public.return_message(0, 0, tmp[0])
            return public.return_message(0, 0, tmp[0].replace(' ', ','))
        return public.return_message(-1, 0, public.lang("Failed to get, there is no default document in the configuration file"))

    # 设置默认文档
    def SetIndex(self, get):
        # 校验参数
        try:
            get.validate([
                Param('id').Integer(),
                Param('Index').String(),
            ], [
                public.validate.trim_filter(),
            ])
        except Exception as ex:
            public.print_log("error info: {}".format(ex))
            return public.return_message(-1, 0, str(ex))

        id = get.id

        Index = get.Index.replace(' ', '')
        Index = Index.replace(',,', ',').strip()
        if not Index: return public.return_message(-1, 0, public.lang("Default index file cannot be empty"))
        if get.Index.find('.') == -1: return public.return_message(-1, 0, public.lang("Default Document Format is invalid, e.g., index.html"))

        if len(Index) < 3: return public.return_message(-1, 0, public.lang("Default Document cannot be empty!"))

        Name = public.M('sites').where("id=?", (id,)).getField('name')
        # 准备指令
        Index_L = Index.replace(",", " ")

        # nginx
        file = self.setupPath + '/panel/vhost/nginx/' + Name + '.conf'
        conf = public.readFile(file)
        if conf:
            rep = r"\s+index\s+.+;"
            conf = re.sub(rep, "\n\tindex " + Index_L + ";", conf)
            public.writeFile(file, conf)

        # apache
        file = self.setupPath + '/panel/vhost/apache/' + Name + '.conf'
        conf = public.readFile(file)
        if conf:
            rep = "DirectoryIndex\\s+.+\n"
            conf = re.sub(rep, 'DirectoryIndex ' + Index_L + "\n", conf)
            public.writeFile(file, conf)

        # openlitespeed
        file = self.setupPath + '/panel/vhost/openlitespeed/detail/' + Name + '.conf'
        conf = public.readFile(file)
        if conf:
            rep = "indexFiles\\s+.+\n"
            Index = Index.split(',')
            Index = [i for i in Index if i]
            Index = ",".join(Index)
            conf = re.sub(rep, 'indexFiles ' + Index + "\n", conf)
            public.writeFile(file, conf)

        public.serviceReload()
        public.write_log_gettext('Site manager', 'Defualt document of site [{}] is [{}]', (Name, Index_L))
        return public.return_message(0, 0, public.lang("Setup successfully!"))

    # 修改物理路径
    def SetPath(self, get):
        # 校验参数
        try:
            get.validate([
                Param('name').String(),
                Param('id').Integer(),
                Param('path').String(),

            ], [
                public.validate.trim_filter(),
            ])
        except Exception as ex:
            public.print_log("error info: {}".format(ex))
            return public.return_message(-1, 0, str(ex))

        id = get.id
        Path = self.GetPath(get.path)
        if Path == "" or id == '0': return public.return_message(-1, 0, public.lang("Directory cannot be empty!"))

        if not self.__check_site_path(Path): return public.return_message(-1, 0, public.lang("System critical directory cannot be used as site directory"))
        if not public.check_site_path(Path):
            a, c = public.get_sys_path()
            return public.return_message(-1, 0,
                                         'Please do not set the website root directory to the system main directory: <br>{}'.format(
                                             "<br>".join(a + c)))

        SiteFind = public.M("sites").where("id=?", (id,)).field('path,name').find()
        if SiteFind["path"] == Path: return public.return_message(-1, 0, public.lang("Same as original path, no need to change!"))
        Name = SiteFind['name']
        file = self.setupPath + '/panel/vhost/nginx/' + Name + '.conf'
        conf = public.readFile(file)
        if conf:
            conf = conf.replace(SiteFind['path'], Path)
            public.writeFile(file, conf)

        file = self.setupPath + '/panel/vhost/apache/' + Name + '.conf'
        conf = public.readFile(file)
        if conf:
            rep = "DocumentRoot\\s+.+\n"
            conf = re.sub(rep, 'DocumentRoot "' + Path + '"\n', conf)
            rep = "<Directory\\s+.+\n"
            conf = re.sub(rep, '<Directory "' + Path + "\">\n", conf)
            public.writeFile(file, conf)

        # OLS
        file = self.setupPath + '/panel/vhost/openlitespeed/' + Name + '.conf'
        conf = public.readFile(file)
        if conf:
            reg = 'vhRoot.*'
            conf = re.sub(reg, 'vhRoot ' + Path, conf)
            public.writeFile(file, conf)

        # 创建basedir
        userIni = Path + '/.user.ini'
        if os.path.exists(userIni): public.ExecShell("chattr -i " + userIni)
        public.writeFile(userIni, 'open_basedir=' + Path + '/:/tmp/')
        public.ExecShell('chmod 644 ' + userIni)
        public.ExecShell('chown root:root ' + userIni)
        public.ExecShell('chattr +i ' + userIni)
        public.set_site_open_basedir_nginx(Name)

        public.serviceReload()
        public.M("sites").where("id=?", (id,)).setField('path', Path)
        public.write_log_gettext('Site manager', 'Successfully changed directory of site [{}]!', (Name,))
        self.CheckRunPathExists(id)
        return public.return_message(0, 0, public.lang("Successfully set"))

    def CheckRunPathExists(self, site_id):
        '''
            @name 检查站点运行目录是否存在
            @author hwliang
            @param site_id int 站点ID
            @return bool
        '''

        site_info = public.M('sites').where('id=?', (site_id,)).field('name,path').find()
        if not site_info: return False
        args = public.dict_obj()
        args.id = site_id
        run_path = self.GetRunPath(args)['message']['result']
        site_run_path = site_info['path'] + '/' + run_path
        if os.path.exists(site_run_path): return True
        args.runPath = '/'
        self.SetSiteRunPath(args)
        public.WriteLog('Site manager',
                        'Due to modifying the root directory of the website [{}], the original running directory [.{}] does not exist, and the directory has been automatically switched to [./]'.format(
                            site_info['name'], run_path))
        return False

    # 取当前可用PHP版本
    def GetPHPVersion(self, get, is_http=True):
        # 校验参数--无参数，暂不需要添加校验

        phpVersions = public.get_php_versions()
        phpVersions.insert(0, 'other')
        phpVersions.insert(0, '00')
        httpdVersion = ""
        filename = self.setupPath + '/apache/version.pl'
        if os.path.exists(filename): httpdVersion = public.readFile(filename).strip()

        if httpdVersion == '2.2': phpVersions = ('00', '52', '53', '54')
        if httpdVersion == '2.4':
            if '52' in phpVersions: phpVersions.remove('52')
        if os.path.exists('/www/server/nginx/sbin/nginx'):
            cfile = '/www/server/nginx/conf/enable-php-00.conf'
            if not os.path.exists(cfile): public.writeFile(cfile, '')

        s_type = getattr(get, 's_type', 0)
        data = []
        for val in phpVersions:
            tmp = {}
            checkPath = self.setupPath + '/php/' + val + '/bin/php'
            if val in ['00', 'other']: checkPath = '/etc/init.d/bt'
            if httpdVersion == '2.2': checkPath = self.setupPath + '/php/' + val + '/libphp5.so'
            if os.path.exists(checkPath):
                tmp['version'] = val
                tmp['name'] = 'PHP-' + val
                if val == '00':
                    tmp['name'] = public.lang("Static")

                if val == 'other':
                    if s_type:
                        tmp['name'] = 'Customize'
                    else:
                        continue
                data.append(tmp)
        if is_http:
            return public.return_message(0, 0, data)
        return data

    # 取指定站点的PHP版本
    def GetSitePHPVersion(self, get):
        # 校验参数
        try:
            get.validate([
                Param('siteName').String(),
            ], [
                public.validate.trim_filter(),
            ])
        except Exception as ex:
            public.print_log("error info: {}".format(ex))
            return public.return_message(-1, 0, str(ex))

        try:
            siteName = get.siteName
            data = {}
            data['phpversion'] = public.get_site_php_version(siteName)
            conf = public.readFile(self.setupPath + '/panel/vhost/' + public.get_webserver() + '/' + siteName + '.conf')
            data['tomcat'] = conf.find('#TOMCAT-START')
            data['tomcatversion'] = public.readFile(self.setupPath + '/tomcat/version.pl')
            data['nodejsversion'] = public.readFile(self.setupPath + '/node.js/version.pl')
            data['php_other'] = ''
            if data['phpversion'] == 'other':
                other_file = '/www/server/panel/vhost/other_php/{}/enable-php-other.conf'.format(siteName)
                if os.path.exists(other_file):
                    conf = public.readFile(other_file)
                    data['php_other'] = re.findall(r"fastcgi_pass\s+(.+);", conf)[0]

            # ols PHP检验
            site_webserver = public.M('sites').where('name=?', (siteName,)).getField('service_type')
            if (public.get_multi_webservice_status() and site_webserver == 'openlitespeed')  or public.get_webserver() == 'openlitespeed':
                ols_php_path = os.path.join('/usr/local/lsws','lsphp' + data['phpversion'])
                if not os.path.exists(ols_php_path) and '00' not in data['phpversion']:
                    return public.return_message(-1, 0, public.lang("Warning: {} version has not been installed yet, "
                                                                    "which may affect website access to the ols service. Please try reinstalling this version or switching to the PHP version!",
                                                                    'PHP'+data['phpversion']))

            return public.return_message(0, 0, data)
        except:
            return public.return_message(-1, 0, public.lang("Apache2.2 does NOT support MultiPHP!,{}", public.get_error_info()))

    def set_site_php_version_multiple(self, get):
        '''
            @name 批量设置PHP版本
            @author zhwen<2020-11-17>
            @param sites_id "1,2"
            @param version 52...74
        '''
        # 校验参数
        try:
            get.validate([
                Param('version').String(),
                Param('sites_id').String(),

            ], [
                public.validate.trim_filter(),
            ])
        except Exception as ex:
            public.print_log("error info: {}".format(ex))
            return public.return_message(-1, 0, str(ex))

        sites_id = get.sites_id.split(',')
        set_phpv_successfully = []
        set_phpv_failed = {}
        for site_id in sites_id:
            get.id = site_id
            get.siteName = public.M('sites').where("id=?", (site_id,)).getField('name')
            if not get.siteName:
                continue
            try:
                result = self.SetPHPVersion(get, multiple=1)
                if result['status'] == -1:
                    set_phpv_failed[get.siteName] = result['message']
                    continue
                set_phpv_successfully.append(get.siteName)
            except:
                set_phpv_failed[get.siteName] = public.lang("There was an error setting, please try again.")
                pass
        public.serviceReload()
        return_message = {'msg': public.get_msg_gettext(
            'Set up website [{}] PHP version successfully'.format(','.join(set_phpv_successfully), )),
            'error': set_phpv_failed,
            'success': set_phpv_successfully}
        return public.return_message(0, 0, return_message)

    # 设置指定站点的PHP版本
    def SetPHPVersion(self, get, multiple=None):
        # 校验参数
        try:
            get.validate([
                Param('siteName').String(),
                Param('version').String(),
                Param('other').String(),
            ], [
                public.validate.trim_filter(),
            ])
        except Exception as ex:
            public.print_log("error info: {}".format(ex))
            return public.return_message(-1, 0, str(ex))

        siteName = get.siteName
        version = get.version
        if version == 'other' and not public.get_webserver() in ['nginx', 'tengine']:
            return public.return_message(-1, 0, public.lang("Custom PHP configuration only supports Nginx"))
        try:
            # nginx
            file = self.setupPath + '/panel/vhost/nginx/' + siteName + '.conf'
            conf = public.readFile(file)
            if conf:
                wp00 = "/www/server/nginx/conf/enable-php-00-wpfastcgi.conf"
                if not os.path.exists(wp00):
                    public.writeFile(wp00, '')
                other_path = '/www/server/panel/vhost/other_php/{}'.format(siteName)
                if not os.path.exists(other_path): os.makedirs(other_path)
                other_rep = "{}/enable-php-other.conf".format(other_path)

                if version == 'other':
                    dst = other_rep
                    get.other = get.other.strip()

                    if not get.other:
                        return public.return_message(-1, 0, public.lang("The PHP connection configuration cannot be empty when customizing the version!"))

                    if not re.match(r"^(\d+\.\d+\.\d+\.\d+:\d+|unix:[\w/\.-]+)$", get.other):
                        return public.return_message(-1, 0, public.lang("The PHP connection configuration format is incorrect, please refer to the example!"))

                    other_tmp = get.other.split(':')
                    if other_tmp[0] == 'unix':
                        if not os.path.exists(other_tmp[1]):
                            return public.return_message(-1, 0, 'The specified unix socket [{}] does not exist!'.format(
                                other_tmp[1]))
                    else:
                        if not public.check_tcp(other_tmp[0], int(other_tmp[1])):
                            return public.return_message(-1, 0,
                                                         'Unable to connect to [{}], please check whether the machine can connect to the target server'.format(
                                                             get.other))

                    other_conf = r'''location ~ [^/]\.php(/|$)
{{
    try_files $uri =404;
    fastcgi_pass  {};
    fastcgi_index index.php;
    include fastcgi.conf;
    include pathinfo.conf;
}}'''.format(get.other)
                    public.writeFile(other_rep, other_conf)
                    conf = conf.replace(other_rep, dst)
                    rep = r"include\s+enable-php-(\w{2,5})\.conf"
                    tmp = re.search(rep, conf)
                    if tmp: conf = conf.replace(tmp.group(), 'include ' + dst)
                elif re.search(r"enable-php-\d+-wpfastcgi.conf", conf):
                    dst = 'enable-php-{}-wpfastcgi.conf'.format(version)
                    conf = conf.replace(other_rep, dst)
                    rep = r"enable-php-\d+-wpfastcgi.conf"
                    tmp = re.search(rep, conf)
                    if tmp: conf = conf.replace(tmp.group(), dst)
                else:
                    dst = 'enable-php-' + version + '.conf'
                    conf = conf.replace(other_rep, dst)
                    rep = r"enable-php-(\w{2,5})\.conf"
                    tmp = re.search(rep, conf)
                    if tmp: conf = conf.replace(tmp.group(), dst)
                public.writeFile(file, conf)
                try:
                    import site_dir_auth_v2 as site_dir_auth
                    site_dir_auth_module = site_dir_auth.SiteDirAuth()
                    auth_list = site_dir_auth_module.get_dir_auth(get)
                    if auth_list:
                        for i in auth_list[siteName]:
                            auth_name = i['name']
                            auth_file = "{setup_path}/panel/vhost/nginx/dir_auth/{site_name}/{auth_name}.conf".format(
                                setup_path=self.setupPath, site_name=siteName, auth_name=auth_name)
                            if os.path.exists(auth_file):
                                site_dir_auth_module.change_dir_auth_file_nginx_phpver(siteName, version, auth_name)
                except:
                    pass

            # apache
            file = self.setupPath + '/panel/vhost/apache/' + siteName + '.conf'
            conf = public.readFile(file)
            if conf and version != 'other':
                rep = r"(unix:/tmp/php-cgi-(\w{2,5})\.sock\|fcgi://localhost|fcgi://127.0.0.1:\d+)"
                tmp = re.search(rep, conf).group()
                conf = conf.replace(tmp, public.get_php_proxy(version, 'apache'))
                public.writeFile(file, conf)
            # OLS
            if version != 'other':
                file = self.setupPath + '/panel/vhost/openlitespeed/detail/' + siteName + '.conf'
                conf = public.readFile(file)
                if conf:
                    rep = r'lsphp\d+'
                    tmp = re.search(rep, conf)
                    if tmp:
                        conf = conf.replace(tmp.group(), 'lsphp' + version)
                        public.writeFile(file, conf)
            if not multiple:
                public.serviceReload()
            public.write_log_gettext("Site manager",
                                     'Successfully changed PHP Version of site [{}] to PHP-{}'.format(siteName,
                                                                                                      version))
            return public.return_message(0, 0,
                                         'Successfully changed PHP Version of site [{}] to PHP-{}'.format(siteName,
                                                                                                          version))
        except:
            return public.get_error_info()
            return public.return_message(-1, 0, public.lang("Setup failed, no enable-php-xx related configuration items were found in the website configuration file!"))

    # 是否开启目录防御
    def GetDirUserINI(self, get):
        # 校验参数
        try:
            get.validate([
                Param('path').String(),
                Param('id').Integer(),

            ], [
                public.validate.trim_filter(),
            ])
        except Exception as ex:
            public.print_log("error info: {}".format(ex))
            return public.return_message(-1, 0, str(ex))

        path = get.path + self.GetRunPath(get)['message']['result']
        if not path: return public.return_message(-1, 0, public.lang("Requested directory does not exist"))
        id = get.id
        get.name = public.M('sites').where("id=?", (id,)).getField('name')
        data = {}
        data['logs'] = self.GetLogsStatus(get)['message']
        data['userini'] = False
        user_ini_file = path + '/.user.ini'
        user_ini_conf = public.readFile(user_ini_file)
        if user_ini_conf and "open_basedir" in user_ini_conf:
            data['userini'] = True
        tmp_run_path = self.GetSiteRunPath(get)
        if "result" in tmp_run_path:
            data['runPath'] = tmp_run_path['message']['result']
        else:
            data['runPath'] = tmp_run_path['message']
        data['pass'] = self.GetHasPwd(get)['message']
        return public.return_message(0, 0, data)

    # 清除多余user.ini
    def DelUserInI(self, path, up=0):
        useriniPath = path + '/.user.ini'
        if os.path.exists(useriniPath):
            public.ExecShell('chattr -i ' + useriniPath)
            try:
                os.remove(useriniPath)
            except:
                pass

        for p1 in os.listdir(path):
            try:
                npath = path + '/' + p1
                if not os.path.isdir(npath): continue
                useriniPath = npath + '/.user.ini'
                if os.path.exists(useriniPath):
                    public.ExecShell('chattr -i ' + useriniPath)
                    os.remove(useriniPath)
                if up < 3: self.DelUserInI(npath, up + 1)
            except:
                continue
        return True

    # 设置目录防御
    def SetDirUserINI(self, get):
        # 校验参数
        try:
            get.validate([
                Param('path').String(),
                Param('id').Integer(),
            ], [
                public.validate.trim_filter(),
            ])
        except Exception as ex:
            public.print_log("error info: {}".format(ex))
            return public.return_message(-1, 0, str(ex))

        path = get.path
        runPath = self.GetRunPath(get)['message']['result']
        filename = path + runPath + '/.user.ini'
        siteName = public.M('sites').where('path=?', (get.path,)).getField('name')
        conf = public.readFile(filename)
        try:
            self._set_ols_open_basedir(get)
            public.ExecShell("chattr -i " + filename)
            if conf and "open_basedir" in conf:
                rep = "\n*open_basedir.*"
                conf = re.sub(rep, "", conf)
                if not conf:
                    os.remove(filename)
                else:
                    public.writeFile(filename, conf)
                    public.ExecShell("chattr +i " + filename)
                public.set_site_open_basedir_nginx(siteName)
                return public.return_message(0, 0, public.lang("Base directory turned off!"))

            if conf and "session.save_path" in conf:
                rep = r"session.save_path\s*=\s*(.*)"
                s_path = re.search(rep, conf).groups(1)[0]
                public.writeFile(filename, conf + '\nopen_basedir={}/:/tmp/:{}'.format(path, s_path))
            else:
                public.writeFile(filename, 'open_basedir={}/:/tmp/'.format(path))
            public.ExecShell("chattr +i " + filename)
            public.set_site_open_basedir_nginx(siteName)
            public.serviceReload()
            return public.return_message(0, 0, public.lang("Base directory turned on!"))
        except Exception as e:
            public.ExecShell("chattr +i " + filename)
            return public.return_message(-1, 0, str(e))

    def _set_ols_open_basedir(self, get):
        # 设置ols
        try:
            sitename = public.M('sites').where("id=?", (get.id,)).getField('name')
            # sitename = path.split('/')[-1]
            f = "/www/server/panel/vhost/openlitespeed/detail/{}.conf".format(sitename)
            c = public.readFile(f)
            if not c: return public.return_message(-1, 0, public.lang(""))
            if f:
                rep = '\nphp_admin_value\\s*open_basedir.*'
                result = re.search(rep, c)
                s = 'on'
                if not result:
                    s = 'off'
                    rep = '\n#php_admin_value\\s*open_basedir.*'
                    result = re.search(rep, c)
                result = result.group()
                if s == 'on':
                    c = re.sub(rep, '\n#' + result[1:], c)
                else:
                    result = result.replace('#', '')
                    c = re.sub(rep, result, c)
                public.writeFile(f, c)
        except:
            pass
        return public.return_message(0, 0, public.lang(""))

    # 读配置
    def __read_config(self, path):
        if not os.path.exists(path):
            public.writeFile(path, '[]')
        upBody = public.readFile(path)
        if not upBody: upBody = '[]'
        return json.loads(upBody)

        # 写配置

    def __write_config(self, path, data):
        return public.writeFile(path, json.dumps(data))

        # 取某个站点某条反向代理详情

    def GetProxyDetals(self, get):
        proxyUrl = self.__read_config(self.__proxyfile)
        sitename = get.sitename
        proxyname = get.proxyname
        for i in proxyUrl:
            if i["proxyname"] == proxyname and i["sitename"] == sitename:
                return public.return_message(0, 0, i)

    # 取某个站点反向代理列表
    def GetProxyList(self, get):
        # 校验参数
        try:
            get.validate([
                Param('sitename').String(),
            ], [
                public.validate.trim_filter(),
            ])
        except Exception as ex:
            public.print_log("error info: {}".format(ex))
            return public.return_message(-1, 0, str(ex))

        n = 0
        for w in ["nginx", "apache"]:
            conf_path = "%s/panel/vhost/%s/%s.conf" % (self.setupPath, w, get.sitename)
            old_conf = ""
            if os.path.exists(conf_path):
                old_conf = public.readFile(conf_path)
            rep = "(#PROXY-START(\n|.)+#PROXY-END)"
            url_rep = r"proxy_pass (.*);|ProxyPass\s/\s(.*)|Host\s(.*);"
            host_rep = r"Host\s(.*);"
            if re.search(rep, old_conf):
                # 构造代理配置
                if w == "nginx":
                    get.todomain = str(re.search(host_rep, old_conf).group(1))
                    get.proxysite = str(re.search(url_rep, old_conf).group(1))
                else:
                    get.todomain = ""
                    get.proxysite = str(re.search(url_rep, old_conf).group(2))
                get.proxyname = public.lang("Old proxy")
                get.type = 1
                get.proxydir = "/"
                get.advanced = 0
                get.cachetime = 1
                get.cache = 0
                get.keepuri = 1
                get.subfilter = "[{\"sub1\":\"\",\"sub2\":\"\"},{\"sub1\":\"\",\"sub2\":\"\"},{\"sub1\":\"\",\"sub2\":\"\"}]"
                get.keepuri=1
                get.rewritedir="[{\"dir1\":\"\",\"dir2\":\"\"},{\"dir1\":\"\",\"dir2\":\"\"},{\"dir1\":\"\",\"dir2\":\"\"}]"

                # proxyname_md5 = self.__calc_md5(get.proxyname)
                # 备份并替换老虚拟主机配置文件
                public.ExecShell("cp %s %s_bak" % (conf_path, conf_path))
                conf = re.sub(rep, "", old_conf)
                public.writeFile(conf_path, conf)
                if n == 0:
                    self.CreateProxy(get)
                n += 1
                # 写入代理配置
                # proxypath = "%s/panel/vhost/%s/proxy/%s/%s_%s.conf" % (
                # self.setupPath, w, get.sitename, proxyname_md5, get.sitename)
                # proxycontent = str(re.search(rep, old_conf).group(1))
                # public.writeFile(proxypath, proxycontent)
            if n == "1":
                public.serviceReload()
        proxyUrl = self.__read_config(self.__proxyfile)
        sitename = get.sitename
        proxylist = []
        # webserver=public.GetWebServer()
        for i in proxyUrl:
            i["advancedfeature"]=0
            try:
                for j in i["rewritedir"]:
                    if j:
                        i["advancedfeature"]=1
                        break
            except:pass
            for j in i["subfilter"]:
                if j:
                    i["advancedfeature"]=1
                    break
            if "rewritedir" not in i:
                i["rewritedir"] = []
            if i["sitename"] == sitename:
                proxylist.append(i)
        return public.return_message(0, 0, proxylist)

    def check_proxy_pass_ending(self,config_content):
        """
        检查Nginx配置中proxy_pass的结尾格式
        
        参数:
            config_content: 包含Nginx配置的字符串
            
        返回:
            str: 可能的结果包括:
                - "以 /; 结束"
                - "以 ; 结束（非 /;）"
                - "未找到 proxy_pass 配置"
        """
        # 正则表达式匹配 proxy_pass 行，捕获结尾部分
        # 匹配规则：
        # - 匹配 proxy_pass 开头
        # - 中间允许任意字符（非贪婪模式）
        # - 捕获结尾的 ; 或 /;
        pattern = r'proxy_pass\s+.*?(/?);'
        
        # 在配置内容中查找匹配
        match = re.search(pattern, config_content, re.IGNORECASE)
        
        if not match:
            return 0
        
        # 获取捕获的结尾部分（/; 或 ;）
        ending = match.group(1) + ';'
        
        if ending == '/;':
            return 1
        else:
            return 0

    def del_proxy_multiple(self, get):
        '''
            @name 批量网站到期时间
            @author zhwen<2020-11-20>
            @param site_id 1
            @param proxynames ces,aaa
        '''
        proxynames = get.proxynames.split(',')
        del_successfully = []
        del_failed = {}
        get.sitename = public.M('sites').where("id=?", (get.site_id,)).getField('name')
        for proxyname in proxynames:
            if not proxyname:
                continue
            get.proxyname = proxyname
            try:
                resule = self.RemoveProxy(get, multiple=1)
                if resule['status'] == -1:
                    del_failed[proxyname] = resule['msg']
                del_successfully.append(proxyname)
            except:
                del_failed[proxyname] = public.lang("There was an error deleting, please try again.")
                pass
        return_message = {'msg': public.get_msg_gettext('Delete [ {} ] proxy successfully', (','.join(del_failed),)),
                          'error': del_failed,
                          'success': del_successfully}
        return public.return_message(0, 0, return_message)

    # 删除反向代理
    def RemoveProxy(self, get, multiple=None):
        # 校验参数
        try:
            get.validate([
                Param('proxyname').String(),
                Param('sitename').String(),
            ], [
                public.validate.trim_filter(),
            ])
        except Exception as ex:
            public.print_log("error info: {}".format(ex))
            return public.return_message(-1, 0, str(ex))

        conf = self.__read_config(self.__proxyfile)
        sitename = get.sitename
        proxyname = get.proxyname
        for i in range(len(conf)):
            c_sitename = conf[i]["sitename"]
            c_proxyname = conf[i]["proxyname"]
            if c_sitename == sitename and c_proxyname == proxyname:
                proxyname_md5 = self.__calc_md5(c_proxyname)
                for w in ["apache", "nginx", "openlitespeed"]:
                    p = "{sp}/panel/vhost/{w}/proxy/{s}/{m}_{s}.conf*".format(sp=self.setupPath, w=w, s=c_sitename,
                                                                              m=proxyname_md5)

                    public.ExecShell('rm -f {}'.format(p))
                p = "{sp}/panel/vhost/openlitespeed/proxy/{s}/urlrewrite/{m}_{s}.conf*".format(sp=self.setupPath,
                                                                                               m=proxyname_md5,
                                                                                               s=get.sitename)
                public.ExecShell('rm -f {}'.format(p))
                del conf[i]
                self.__write_config(self.__proxyfile, conf)
                self.SetNginx(get)
                self.SetApache(get.sitename)
                if not multiple:
                    public.serviceReload()
                return_message = public.return_msg_gettext(True, 'Successfully deleted')
                del return_message['status']
                return public.return_message(0, 0, return_message['msg'])

    # 检查代理是否存在
    def __check_even(self, get, action=""):
        conf_data = self.__read_config(self.__proxyfile)
        for i in conf_data:
            if i["sitename"] == get.sitename:
                if action == "create":
                    if i["proxydir"] == get.proxydir or i["proxyname"] == get.proxyname:
                        return public.return_message(0, 0, i)
                else:
                    if i["proxyname"] != get.proxyname and i["proxydir"] == get.proxydir:
                        return public.return_message(0, 0, i)

    # 检测全局代理和目录代理是否同时存在
    def __check_proxy_even(self, get, action=""):
        conf_data = self.__read_config(self.__proxyfile)
        n = 0
        if action == "":
            for i in conf_data:
                if i["sitename"] == get.sitename:
                    n += 1
            if n == 1:
                return public.return_message(0, 0, public.lang(""))
        for i in conf_data:
            if i["sitename"] == get.sitename:
                if i["proxydir"]=="/":i["advanced"]=0
                else:i["advanced"]=1
                if i["advanced"] != int(get.advanced):
                    return public.return_message(-1, 0, i)
        return public.return_message(0, 0, public.lang(""))

    # 计算proxyname md5
    def __calc_md5(self, proxyname):
        md5 = hashlib.md5()
        md5.update(proxyname.encode('utf-8'))
        return md5.hexdigest()

    # 检测URL是否可以访问
    def __CheckUrl(self, get):
        sk = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sk.settimeout(5)
        rep = r"(https?)://([\w\.\-]+):?([\d]+)?"
        h = re.search(rep, get.proxysite).group(1)
        d = re.search(rep, get.proxysite).group(2)
        try:
            p = re.search(rep, get.proxysite).group(3)
        except:
            p = ""
        try:
            if p:
                sk.connect((d, int(p)))
            else:
                if h == "http":
                    sk.connect((d, 80))
                else:
                    sk.connect((d, 443))
        except:
            return_message = public.return_msg_gettext(False, 'Can NOT get target URL')
            del return_message['status']
            return public.return_message(-1, 0, return_message['msg'])

    # 基本设置检查
    def __CheckStart(self, get, action=""):
        isError = public.checkWebConfig()
        if isinstance(isError, str):
            if isError.find('/proxy/') == -1:  # 如果是反向代理配置文件本身的错误，跳过
                return public.return_message(-1, 0, public.lang("An error was detected in the configuration file. Please solve it before proceeding"))
        if action == "create":
            if sys.version_info.major < 3:
                if len(get.proxyname) < 3 or len(get.proxyname) > 40:
                    return public.return_message(-1, 0, public.lang("Database name cannot be more than 40 characters!"))
            else:
                if len(get.proxyname.encode("utf-8")) < 3 or len(get.proxyname.encode("utf-8")) > 40:
                    return public.return_message(-1, 0, public.lang("Database name cannot be more than 40 characters!"))
        if self.__check_even(get, action):
            return public.return_message(-1, 0, public.lang("Specified reverse proxy name or proxy folder already exists"))
        # 判断代理，只能有全局代理或目录代理
        check_proxy_even = self.__check_proxy_even(get, action)
        if check_proxy_even['status'] == -1:
            return public.return_message(-1, 0, public.lang("Cannot set both directory and global proxies"))
        # 判断cachetime类型
        if get.cachetime:
            try:
                int(get.cachetime)
            except:
                return public.return_message(-1, 0, public.lang("Please enter number"))

        rep = r"http(s)?\:\/\/"
        # repd = r"http(s)?\:\/\/([a-zA-Z0-9][-a-zA-Z0-9]{0,62}\.)+([a-zA-Z0-9][a-zA-Z0-9]{0,62})+.?"
        tod = "[a-zA-Z]+$"
        repte = "[\\?\\=\\[\\]\\)\\(\\*\\&\\^\\%\\$\\#\\@\\!\\~\\`{\\}\\>\\<\\,\',\"]+"
        # 检测代理目录格式
        if re.search(repte, get.proxydir):
            return public.return_message(-1, 0, "PROXY_DIR_ERR", ("?,=,[,],),(,*,&,^,%,$,#,@,!,~,`,{,},>,<,\\,',\"]",))
        # 检测发送域名格式
        if get.todomain:
            if re.search("[\\}\\{\\#\\;\"\']+", get.todomain):
                return public.return_message(-1, 0, public.lang("Sent Domain format error :' + get.todomain + '<br>The following special characters cannot exist [ }  { # ; \" \' ] "))
        if public.get_webserver() != 'openlitespeed' and not get.todomain:
            get.todomain = "$host"

        # 检测目标URL格式
        if not re.match(rep, get.proxysite):
            return public.return_message(-1, 0, 'Sent domain format ERROR {}', (get.proxysite,))
        if re.search(repte, get.proxysite):
            return public.return_message(-1, 0, "PROXY_URL_ERR", ("?,=,[,],),(,*,&,^,%,$,#,@,!,~,`,{,},>,<,\\,',\"]",))
        # 检测目标url是否可用
        # if re.match(repd, get.proxysite):
        #     if self.__CheckUrl(get):
        #         return public.returnMsg(False, public.lang("The target URL cannot be accessed"))
        subfilter = json.loads(get.subfilter)
        # 检测替换内容
        if subfilter:
            for s in subfilter:
                if not s["sub1"]:
                    if s["sub2"]:
                        return public.return_message(-1, 0, public.lang("Please enter the content to be replaced"))
                elif s["sub1"] == s["sub2"]:
                    return public.return_message(-1, 0, public.lang("The content to replace cannot be the same as the content to be replaced"))

    # 设置Nginx配置
    def SetNginx(self, get):
        ng_proxyfile = "%s/panel/vhost/nginx/proxy/%s/*.conf" % (self.setupPath, get.sitename)
        ng_file = self.setupPath + "/panel/vhost/nginx/" + get.sitename + ".conf"
        p_conf = self.__read_config(self.__proxyfile)
        cureCache = ''

        if public.get_webserver() == 'nginx':
            shutil.copyfile(ng_file, '/tmp/ng_file_bk.conf')

        # if os.path.exists('/www/server/nginx/src/ngx_cache_purge'):
        cureCache += '''
    location ~ /purge(/.*) {
        proxy_cache_purge cache_one $host$1$is_args$args;
        #access_log  /www/wwwlogs/%s_purge_cache.log;
    }''' % (get.sitename)
        if os.path.exists(ng_file):
            self.CheckProxy(get)
            ng_conf = public.readFile(ng_file)
            if not p_conf:
                # rep = "%s[\\w\\s\\~\\/\\(\\)\\.\\*\\{\\}\\;\\$\n\\#]+.{1,66}[\\s\\w\\/\\*\\.\\;]+include enable-php-" % public.GetMsg(
                #     "CLEAR_CACHE")
                rep = "%s[\\w\\s\\~\\/\\(\\)\\.\\*\\{\\}\\;\\$\n\\#]+.*\n.*" % ("#Clear cache")
                # ng_conf = re.sub(rep, 'include enable-php-', ng_conf)
                ng_conf = re.sub(rep, '', ng_conf)
                oldconf = '''location ~ .*\\.(gif|jpg|jpeg|png|bmp|swf)$
    {
        expires      30d;
        error_log /dev/null;
        access_log /dev/null;
    }
    location ~ .*\\.(js|css)?$
    {
        expires      12h;
        error_log /dev/null;
        access_log /dev/null;
    }'''
                if "(gif|jpg|jpeg|png|bmp|swf)$" not in ng_conf:
                    ng_conf = re.sub(r'access_log\s*/www', oldconf + "\n\taccess_log /www", ng_conf)
                public.writeFile(ng_file, ng_conf)
                return public.return_message(0, 0, public.lang(""))
            sitenamelist = []
            for i in p_conf:
                sitenamelist.append(i["sitename"])

            if get.sitename in sitenamelist:
                rep = r"include.*\/proxy\/.*\*.conf;"
                if not re.search(rep, ng_conf):
                    rep = "location.+\\(gif[\\w\\|\\$\\(\\)\n\\{\\}\\s\\;\\/\\~\\.\\*\\\\\\?]+access_log\\s+/"
                    ng_conf = re.sub(rep, 'access_log  /', ng_conf)
                    ng_conf = ng_conf.replace("include enable-php-", "%s\n" % public.get_msg_gettext(
                        "#Clear cache") + cureCache + "\n\t%s\n\t" % public.get_msg_gettext(
                        "#Referenced reverse proxy rule, if commented, the configured reverse proxy will be invalid") + "include " + ng_proxyfile + ";\n\n\tinclude enable-php-")
                    public.writeFile(ng_file, ng_conf)

            else:
                # rep = "%s[\\w\\s\\~\\/\\(\\)\\.\\*\\{\\}\\;\\$\n\\#]+.{1,66}[\\s\\w\\/\\*\\.\\;]+include enable-php-" % public.GetMsg(
                #     "CLEAR_CACHE")
                rep = "%s[\\w\\s\\~\\/\\(\\)\\.\\*\\{\\}\\;\\$\n\\#]+.*\n.*" % ("#Clear cache")
                # ng_conf = re.sub(rep, 'include enable-php-', ng_conf)
                ng_conf = re.sub(rep, '', ng_conf)
                oldconf = '''location ~ .*\\.(gif|jpg|jpeg|png|bmp|swf)$
    {
        expires      30d;
        error_log /dev/null;
        access_log /dev/null;
    }
    location ~ .*\\.(js|css)?$
    {
        expires      12h;
        error_log /dev/null;
        access_log /dev/null;
    }'''
                if "(gif|jpg|jpeg|png|bmp|swf)$" not in ng_conf:
                    ng_conf = re.sub(r'access_log\s*/www', oldconf + "\n\taccess_log  /www", ng_conf)
                public.writeFile(ng_file, ng_conf)
        return public.return_message(0, 0, public.lang(""))

        # 设置apache配置

    def SetApache(self, sitename):
        ap_proxyfile = "%s/panel/vhost/apache/proxy/%s/*.conf" % (self.setupPath, sitename)
        ap_file = self.setupPath + "/panel/vhost/apache/" + sitename + ".conf"
        p_conf = public.readFile(self.__proxyfile)

        if public.get_webserver() == 'apache':
            shutil.copyfile(ap_file, '/tmp/ap_file_bk.conf')

        if os.path.exists(ap_file):
            ap_conf = public.readFile(ap_file)
            if p_conf == "[]":
                rep = "\n*%s\n+\\s+IncludeOptiona[\\s\\w\\/\\.\\*]+" % public.get_msg_gettext(
                    '#Referenced reverse proxy rule, if commented, the configured reverse proxy will be invalid')
                ap_conf = re.sub(rep, '', ap_conf)
                public.writeFile(ap_file, ap_conf)
                return
            if sitename in p_conf:
                rep = "combined(\n|.)+IncludeOptional.*\\/proxy\\/.*conf"
                rep1 = "combined"
                if not re.search(rep, ap_conf):
                    ap_conf = ap_conf.replace(rep1, rep1 + "\n\t%s\n\t" % public.get_msg_gettext(
                        '#Referenced reverse proxy rule, if commented, the configured reverse proxy will be invalid') + "\n\tIncludeOptional " + ap_proxyfile)
                    public.writeFile(ap_file, ap_conf)
            else:
                # rep = "\n*#引用反向代理(\n|.)+IncludeOptional.*\\/proxy\\/.*conf"
                rep = "\n*%s\n+\\s+IncludeOptiona[\\s\\w\\/\\.\\*]+" % public.get_msg_gettext(
                    '#Referenced reverse proxy rule, if commented, the configured reverse proxy will be invalid')
                ap_conf = re.sub(rep, '', ap_conf)
                public.writeFile(ap_file, ap_conf)

    # 设置OLS
    def _set_ols_proxy(self, get):
        # 添加反代配置
        proxyname_md5 = self.__calc_md5(get.proxyname)
        dir_path = "%s/panel/vhost/openlitespeed/proxy/%s/" % (self.setupPath, get.sitename)
        if not os.path.exists(dir_path):
            os.makedirs(dir_path)
        file_path = "{}{}_{}.conf".format(dir_path, proxyname_md5, get.sitename)
        reverse_proxy_conf = """
extprocessor %s {
  type                    proxy
  address                 %s
  maxConns                1000
  pcKeepAliveTimeout      600
  initTimeout             600
  retryTimeout            0
  respBuffer              0
}
""" % (get.proxyname, get.proxysite)
        public.writeFile(file_path, reverse_proxy_conf)
        # 添加urlrewrite
        dir_path = "%s/panel/vhost/openlitespeed/proxy/%s/urlrewrite/" % (self.setupPath, get.sitename)
        if not os.path.exists(dir_path):
            os.makedirs(dir_path)
        file_path = "{}{}_{}.conf".format(dir_path, proxyname_md5, get.sitename)
        reverse_urlrewrite_conf = """
RewriteRule ^%s(.*)$ http://%s/$1 [P,E=Proxy-Host:%s]
""" % (get.proxydir, get.proxyname, get.todomain)
        public.writeFile(file_path, reverse_urlrewrite_conf)
        return public.return_message(0, 0, public.lang(""))

    # 检查伪静态、主配置文件是否有location冲突
    def CheckLocation(self, get):
        # 伪静态文件路径
        rewriteconfpath = "%s/panel/vhost/rewrite/%s.conf" % (self.setupPath, get.sitename)
        # 主配置文件路径
        nginxconfpath = "%s/nginx/conf/nginx.conf" % (self.setupPath)
        # vhost文件
        vhostpath = "%s/panel/vhost/nginx/%s.conf" % (self.setupPath, get.sitename)

        rep = "location\\s+/[\n\\s]+{"

        for i in [rewriteconfpath, nginxconfpath, vhostpath]:
            conf = public.readFile(i)
            if re.findall(rep, conf):
                return public.return_message(-1, 0, public.lang("A global reverse proxy already exists in the rewrite/nginx master configuration/vhost file"))
        return public.return_message(0, 0, public.lang(""))

    #检测重写路径
    def CheckRewriteDirArgs(self, get):
        #检测重写路径
        rewritedir=json.loads(get.rewritedir)
        check_dirs=[]
        for i in rewritedir:
            if (i.get('dir1', None) and not i.get('dir2', None)) or (not i.get('dir1', None) and i.get('dir2', None)):
                return public.lang("Rewrite source directory and rewrite target directory must be filled in at the same time")
            #检测路径是否相同
            if i.get('dir1', None) and i.get('dir2', None) and i.get('dir1', None) == i.get('dir2', None):
                return public.lang("Rewrite source directory and rewrite target directory cannot be the same")
            #检测重写的路径是否存在
            if i.get('dir1', None):
                check_dirs.append(i.get('dir1', None))

            #检测路径是否以/开头
            if i.get('dir1', None) and not i.get('dir1', None).startswith('/'):
                return public.lang("Rewrite source directory must start with /")
            if i.get('dir2', None) and not i.get('dir2', None).startswith('/'):
                return public.lang("Rewrite target directory must start with /")
        #检测重写路径是否重复
        if len(check_dirs) != len(set(check_dirs)):
            return public.lang("Rewrite source directory and rewrite target directory cannot be the same")
        return ""


    # 创建反向代理
    def CreateProxy(self, get):
        # 校验参数
        try:
            get.validate([
                Param('proxyname').String(),
                Param('proxydir').String(),
                Param('proxysite').String(),
                Param('todomain').String(),
                Param('sitename').String(),
                Param('subfilter').String(),
                Param('rewritedir').String(),
                Param('type').Integer(),
                Param('cache').Integer(),
                Param('advanced').Integer(),
                Param('cachetime').Integer(),
                Param('keepuri').Integer(),
                
            ], [
                public.validate.trim_filter(),
            ])
        except Exception as ex:
            public.print_log("error info: {}".format(ex))
            return public.return_message(-1, 0, str(ex))

        try:
            nocheck = get.nocheck
        except:
            nocheck = ""
        if not get.get('proxysite', None):
            return public.return_message(-1, 0, public.lang("Destination URL cannot be empty"))

        #检测重写路径
        checkRewriteDirArgs=self.CheckRewriteDirArgs(get)
        if checkRewriteDirArgs !="":
            return public.return_message(-1, 0, checkRewriteDirArgs)

        if not nocheck:
            #检测参数
            get.advanced = 0 if get.proxydir=="/" else 1
            ret = self.__CheckStart(get, "create")
            if ret is not None and int(ret.get('status', 0)) != 0:
                return ret
        site = public.M('sites').where("name=?", (get.sitename,)).field('id,service_type').find()
        if public.get_webserver() == 'nginx' and site['service_type'] not in ['apache','openlitespeed']:
            ret = self.CheckLocation(get)
            if ret is not None and int(ret.get('status', 0)) != 0:
                return ret

        if not get.proxysite.split('//')[-1]:
            return public.return_message(-1, 0, public.lang("The target URL cannot be [http:// or https://], please fill in the full URL, such as: https://aapanel.com"))
        # project_type = public.M('sites').where('name=?', (get.sitename,)).field('project_type').find()['project_type']
        # if project_type == 'WP':
        #     return public.return_msg_gettext(False, public.lang("Reverse proxies are not currently available for Wordpress sites that use one-click deployment"))
        
        proxyUrl = self.__read_config(self.__proxyfile)
        proxyUrl.append({
            "proxyname": get.proxyname,
            "sitename": get.sitename,
            "proxydir": get.proxydir,
            "proxysite": get.proxysite,
            "todomain": get.todomain,
            "type": int(get.type),
            "cache": int(get.cache),
            "subfilter": json.loads(get.subfilter),
            "advanced": int(get.advanced),
            "cachetime": int(get.cachetime),
            "keepuri": int(get.keepuri),
            "rewritedir": json.loads(get.rewritedir),

        })
        self.__write_config(self.__proxyfile, proxyUrl)

        # 多服务下
        if public.get_multi_webservice_status():
            if not site['service_type'] or site['service_type'] == 'nginx':
                self.SetNginx(get)
                status = self.SetProxy(get)
                if status["status"] == -1:
                    return status
            else:
                if get.proxydir == '/':
                    return public.return_message(-1, 0, 'Under Multi-WebServer Hosting, global [/] reverse proxies are not allowed to be added')
                self.SetNginx(get)
                self.SetApache(get.sitename)
                self._set_ols_proxy(get)
                status = self.SetProxy(get)
                if status["status"] == -1:
                    return status
        else:
            self.SetNginx(get)
            self.SetApache(get.sitename)
            self._set_ols_proxy(get)
            status = self.SetProxy(get)
            if status["status"] == -1:
                return status


        if get.proxydir == '/':
            get.version = '00'
            get.siteName = get.sitename
            self.SetPHPVersion(get)
        public.serviceReload()
        return public.return_message(0, 0, public.lang("Setup successfully!"))

    # 取代理配置文件
    def GetProxyFile(self, get):
        # 校验参数
        try:
            get.validate([
                Param('proxyname').String(),
                Param('sitename').String(),
                Param('webserver').String(),
            ], [
                public.validate.trim_filter(),
            ])
        except Exception as ex:
            public.print_log("error info: {}".format(ex))
            return public.return_message(-1, 0, str(ex))

        import files_v2 as files
        conf = self.__read_config(self.__proxyfile)
        sitename = get.sitename
        proxyname = get.proxyname
        proxyname_md5 = self.__calc_md5(proxyname)
        get.path = "%s/panel/vhost/%s/proxy/%s/%s_%s.conf" % (
            self.setupPath, get.webserver, sitename, proxyname_md5, sitename)
        for i in conf:
            if proxyname == i["proxyname"] and sitename == i["sitename"] and i["type"] != 1:
                return public.return_message(-1, 0, public.lang("Proxy suspended"))
        f = files.files()
        return_message = f.GetFileBody(get)
        return_message['message']['file'] = get.path
        return return_message

    # 保存代理配置文件
    def SaveProxyFile(self, get):
        # 校验参数
        try:
            get.validate([
                Param('path').String(),
                Param('data').String(),
                Param('encoding').String(),
            ], [
                public.validate.trim_filter(),
            ])
        except Exception as ex:
            public.print_log("error info: {}".format(ex))
            return public.return_message(-1, 0, str(ex))

        import files_v2 as files
        f = files.files()
        return f.SaveFileBody(get)
        #	return public.returnMsg(True, public.lang("Saved successfully"))

    # 检查是否存在#Set Nginx Cache
    def check_annotate(self, data):
        rep = "\n\\s*#Set\\s*Nginx\\s*Cache"
        if re.search(rep, data):
            return True

    def old_proxy_conf(self, conf, ng_conf_file, get):
        rep = r'location\s*\~\*.*gif\|png\|jpg\|css\|js\|woff\|woff2\)\$'
        if not re.search(rep, conf):
            return public.return_message(0, 0, conf)

        self.RemoveProxy(get)
        self.CreateProxy(get)
        return public.return_message(0, 0, public.readFile(ng_conf_file))

    def replace_nginx_rewrite(self,nginx_config):
        # 1. 将配置按行分割，保留每行的原始缩进和格式
        config_lines = nginx_config.split('\n')
        # 标记是否已添加过 #rewritedir（确保只保留一个）
        has_rewritedir = False
        # 存储处理后的配置行
        processed_lines = []

        for line in config_lines:
            # 2. 去除行首尾空白，判断是否为 rewrite 行（避免误判注释中的 rewrite）
            stripped_line = line.strip()
            if stripped_line.startswith('rewrite '):
                # 3. 只保留第一个 rewrite 对应的 #rewritedir
                if not has_rewritedir:
                    # 保留原 rewrite 行的缩进，替换内容为 #rewritedir
                    indent = line[:len(line) - len(line.lstrip())]  # 提取缩进（如空格、制表符）
                    processed_lines.append(f"{indent}#Set Rewrite Dir")
                    has_rewritedir = True  # 标记已添加，后续 rewrite 行跳过
            else:
                # 4. 非 rewrite 行直接保留原格式
                processed_lines.append(line)

        # 5. 将处理后的行重新拼接为完整配置字符串
        nginx_config = '\n'.join(processed_lines)
        if nginx_config.find('#Set Rewrite Dir') == -1:
            #将proxy_pass 替换为"\n\t#Set Rewrite Dir \n\tproxy_pass "
            nginx_config = nginx_config.replace('proxy_pass', '\t#Set Rewrite Dir \n\tproxy_pass')
        # 6. 去除连接两个的换行符
        nginx_config = nginx_config.replace('\n\n', '\n')
        return nginx_config


    #去除所有连接两个两行的空行
    def remove_consecutive_blank_lines_from_string(self,nginx_config_str):
        """
        对指定的 Nginx 配置字符串去除连续空行（保留单个空行）
        
        参数:
            nginx_config_str (str): 原始 Nginx 配置字符串
        返回:
            str: 处理后去除连续空行的 Nginx 配置字符串
        """
        # 1. 将字符串按行拆分，保留每行的换行符（splitlines(True) 保留换行符）
        lines = nginx_config_str.splitlines(True)
        
        # 2. 过滤连续空行
        filtered_lines = []
        prev_line_blank = False  # 标记前一行是否为空行（初始为 False）

        for line in lines:
            # 判断当前行是否为空行（仅含空格/制表符或完全空白）
            # strip() 去除所有空白字符（空格、制表符、换行符），长度为0则为空行
            current_line_blank = len(line.strip()) == 0

            # 保留规则：
            # - 非空行 → 必须保留
            # - 空行 → 仅当前一行非空时保留（避免连续空行）
            if not current_line_blank or not prev_line_blank:
                filtered_lines.append(line)
            
            # 更新“前一行是否为空”的状态，为下一行判断做准备
            prev_line_blank = current_line_blank

        # 3. 将过滤后的行列表重新拼接为字符串
        cleaned_config = ''.join(filtered_lines)
        return cleaned_config

    # 修改反向代理
    def ModifyProxy(self, get):
        # 校验参数
        try:
            get.validate([
                Param('proxyname').String().Require(),
                Param('proxydir').String().Require(),
                Param('proxysite').String().Require(),
                Param('todomain').String().Require(),
                Param('sitename').String().Require(),
                Param('subfilter').String().Require(),
                Param('rewritedir').String().Require(),
                Param('type').Integer().Require(),
                Param('cache').Integer().Require(),
                Param('advanced').Integer().Require(),
                Param('cachetime').Integer().Require(),
                Param('keepuri').Integer().Require(),
            ], [
                public.validate.trim_filter(),
            ])
        except Exception as ex:
            public.print_log("error info: {}".format(ex))
            return public.return_message(-1, 0, str(ex))


        #检测重写路径
        checkRewriteDirArgs=self.CheckRewriteDirArgs(get)
        if checkRewriteDirArgs !="":
            return public.return_message(-1, 0, checkRewriteDirArgs)
        proxyname_md5 = self.__calc_md5(get.proxyname)
        ap_conf_file = "{p}/panel/vhost/apache/proxy/{s}/{n}_{s}.conf".format(
            p=self.setupPath, s=get.sitename, n=proxyname_md5)
        ng_conf_file = "{p}/panel/vhost/nginx/proxy/{s}/{n}_{s}.conf".format(
            p=self.setupPath, s=get.sitename, n=proxyname_md5)
        ols_conf_file = "{p}/panel/vhost/openlitespeed/proxy/{s}/urlrewrite/{n}_{s}.conf".format(
            p=self.setupPath, s=get.sitename, n=proxyname_md5)
        #检测参数
        get.advanced = 0 if get.proxydir=="/" else 1
        if self.__CheckStart(get):
            return self.__CheckStart(get)
            
        conf = self.__read_config(self.__proxyfile)
        random_string = public.GetRandomString(8)
        for i in range(len(conf)):
            if conf[i]["proxyname"] == get.proxyname and conf[i]["sitename"] == get.sitename:
                if int(get.type) != 1:
                    if not os.path.exists(ng_conf_file):
                        return public.return_message(-1, 0, public.lang("Please enable the reverse proxy before editing!"))
                    public.ExecShell("mv {f} {f}_bak".format(f=ap_conf_file))
                    public.ExecShell("mv {f} {f}_bak".format(f=ng_conf_file))
                    public.ExecShell("mv {f} {f}_bak".format(f=ols_conf_file))
                    conf[i]["type"] = int(get.type)
                    self.__write_config(self.__proxyfile, conf)
                    public.serviceReload()
                    return public.return_message(0, 0, public.lang("Setup successfully!"))
                else:
                    if os.path.exists(ap_conf_file + "_bak"):
                        public.ExecShell("mv {f}_bak {f}".format(f=ap_conf_file))
                        public.ExecShell("mv {f}_bak {f}".format(f=ng_conf_file))
                        public.ExecShell("mv {f}_bak {f}".format(f=ols_conf_file))
                    ng_conf = public.readFile(ng_conf_file)
                    if not ng_conf or not isinstance(ng_conf, str):
                        return public.return_message(-1, 0, public.lang("Failed to read Nginx config file"))

                    ng_conf = self.old_proxy_conf(ng_conf, ng_conf_file, get)['message']['result']
                    # 修改nginx配置
                    # 如果代理URL后缀带有URI则删除URI，正则匹配不支持proxypass处带有uri
                    proxy_site=get.proxysite
                    if int(get.keepuri) == 0:
                        proxy_site+="/"
                        
                    php_pass_proxy = get.proxysite
                    if get.proxysite[-1] == '/' or get.proxysite.count('/') > 2 or '?' in get.proxysite:
                        match = re.search(r'(https?\:\/\/[\w\.]+)', get.proxysite)
                        if match:
                            php_pass_proxy = match.group(0)


                    ng_conf = re.sub(r"location\s+[\^\~]*\s?%s" % conf[i]["proxydir"], "location ^~ " + get.proxydir,
                                     ng_conf)
                    
                    ng_conf = re.sub(r"proxy_pass\s+%s" % conf[i]["proxysite"], "proxy_pass " + proxy_site, ng_conf)
                    ng_conf = re.sub(r"proxy_pass\s+%s" % conf[i]["proxysite"]+"/", "proxy_pass " + proxy_site, ng_conf)
                    ng_conf = re.sub("location\\s+\\~\\*\\s+\\\\.\\(php.*\n\\{\\s*proxy_pass\\s+%s.*" % (php_pass_proxy),
                                     "location ~* \\.(php|jsp|cgi|asp|aspx)$\n{\n\tproxy_pass %s;" % php_pass_proxy,
                                     ng_conf)
                    ng_conf = re.sub("location\\s+\\~\\*\\s+\\\\.\\(gif.*\n\\{\\s*proxy_pass\\s+%s.*" % (php_pass_proxy),
                                     "location ~* \\.(gif|png|jpg|css|js|woff|woff2)$\n{\n\tproxy_pass %s;" % php_pass_proxy,
                                     ng_conf)

                    backslash = ""
                    if "Host $host" in ng_conf:
                        backslash = "\\"
                    ng_conf = re.sub(r"\sHost\s+%s" % backslash + conf[i]["todomain"], " Host " + get.todomain, ng_conf)
                    cache_rep = r"proxy_cache_valid\s+200\s+304\s+301\s+302\s+\d+m;((\n|.)+expires\s+\d+m;)*"
                    if int(get.cache) == 1:
                        if re.search(cache_rep, ng_conf):
                            expires_rep = "\\{\n\\s+expires\\s+12h;"
                            ng_conf = re.sub(expires_rep, "{", ng_conf)
                            ng_conf = re.sub(cache_rep, "proxy_cache_valid 200 304 301 302 {0}m;".format(get.cachetime),
                                             ng_conf)
                        else:
                            #                         ng_cache = """
                            # proxy_ignore_headers Set-Cookie Cache-Control expires;
                            # proxy_cache cache_one;
                            # proxy_cache_key $host$uri$is_args$args;
                            # proxy_cache_valid 200 304 301 302 %sm;""" % (get.cachetime)
                            ng_cache = r"""
    if ( $uri ~* "\.(gif|png|jpg|css|js|woff|woff2)$" )
    {
        expires 1m;
    }
    proxy_ignore_headers Set-Cookie Cache-Control expires;
    proxy_cache cache_one;
    proxy_cache_key $host$uri$is_args$args;
    proxy_cache_valid 200 304 301 302 %sm;""" % (get.cachetime)
                            if self.check_annotate(ng_conf):
                                cache_rep = '\n\\s*#Set\\s*Nginx\\s*Cache(.|\n)*no-cache;\\s*\n*\\s*\\}'
                                ng_conf = re.sub(cache_rep, '\n\t#Set Nginx Cache\n' + ng_cache, ng_conf)
                            else:
                                # cache_rep = r'#proxy_set_header\s+Connection\s+"upgrade";'
                                cache_rep = r"proxy_set_header\s+REMOTE-HOST\s+\$remote_addr;"
                                ng_conf = re.sub(cache_rep,
                                                 r"\n\tproxy_set_header\s+REMOTE-HOST\s+\$remote_addr;\n\t#Set Nginx Cache" + ng_cache,
                                                 ng_conf)
                    else:
                        no_cache = r"""
    #Set Nginx Cache
    set $static_file%s 0;
    if ( $uri ~* "\.(gif|png|jpg|css|js|woff|woff2)$" )
    {
        set $static_file%s 1;
        expires 1m;
    }
    if ( $static_file%s = 0 )
    {
        add_header Cache-Control no-cache;
    }
}
#PROXY-END/""" % (random_string, random_string, random_string)
                        if self.check_annotate(ng_conf):
                            rep = r'\n\s*#Set\s*Nginx\s*Cache(.|\n)*'
                            # ng_conf = re.sub(rep,
                            #                  "\n\t#Set Nginx Cache\n\tproxy_ignore_headers Set-Cookie Cache-Control expires;\n\tadd_header Cache-Control no-cache;",
                            #                  ng_conf)
                            ng_conf = re.sub(rep, no_cache, ng_conf)
                        else:
                            rep = r"\s+proxy_cache\s+cache_one.*[\n\s\w\_\";\$]+m;"
                            # ng_conf = re.sub(rep,
                            #                  r"\n\t#Set Nginx Cache\n\tproxy_ignore_headers Set-Cookie Cache-Control expires;\n\tadd_header Cache-Control no-cache;",
                            #                  ng_conf)
                            ng_conf = re.sub(rep, no_cache, ng_conf)

                    sub_rep = "sub_filter"
                    subfilter = json.loads(get.subfilter)
                    if str(conf[i]["subfilter"]) != str(subfilter) or ng_conf.find('sub_filter_once') == -1:
                        if re.search(sub_rep, ng_conf):
                            sub_rep = "\\s+proxy_set_header\\s+Accept-Encoding(.|\n)+off;"
                            ng_conf = re.sub(sub_rep, "", ng_conf)

                        # 构造替换字符串
                        ng_subdata = ''
                        ng_sub_filter = '''
    proxy_set_header Accept-Encoding "";%s
    sub_filter_once off;'''
                        if subfilter:
                            for s in subfilter:
                                if not s["sub1"]:
                                    continue
                                if '"' in s["sub1"]:
                                    s["sub1"] = s["sub1"].replace('"', '\\"')
                                if '"' in s["sub2"]:
                                    s["sub2"] = s["sub2"].replace('"', '\\"')
                                ng_subdata += '\n\tsub_filter "%s" "%s";' % (s["sub1"], s["sub2"])
                        if ng_subdata:
                            ng_sub_filter = ng_sub_filter % (ng_subdata)
                        else:
                            ng_sub_filter = ''
                        sub_rep = r'#Set\s+Nginx\s+Cache'
                        ng_conf = re.sub(sub_rep, '#Set Nginx Cache\n' + ng_sub_filter, ng_conf)

                        #replace_nginx_rewrite
                        rewriteconf=self.setRewritedir(get)
                        ng_conf=self.replace_nginx_rewrite(ng_conf)
                        ng_conf = ng_conf.replace('#Set Rewrite Dir', rewriteconf)
                        ng_conf=self.remove_consecutive_blank_lines_from_string(ng_conf)

                    # 修改apache配置
                    ap_conf = public.readFile(ap_conf_file)
                    ap_conf = re.sub(r"ProxyPass\s+%s\s+%s" % (conf[i]["proxydir"], conf[i]["proxysite"]),
                                     "ProxyPass %s %s" % (get.proxydir, get.proxysite), ap_conf)
                    ap_conf = re.sub(r"ProxyPassReverse\s+%s\s+%s" % (conf[i]["proxydir"], conf[i]["proxysite"]),
                                     "ProxyPassReverse %s %s" % (get.proxydir, get.proxysite), ap_conf)
                    # 修改OLS配置
                    p = "{p}/panel/vhost/openlitespeed/proxy/{s}/{n}_{s}.conf".format(p=self.setupPath, n=proxyname_md5,
                                                                                      s=get.sitename)
                    c = public.readFile(p)
                    if c:
                        rep = r'address\s+(.*)'
                        new_proxysite = 'address\t{}'.format(get.proxysite)
                        c = re.sub(rep, new_proxysite, c)
                        public.writeFile(p, c)

                    # p = "{p}/panel/vhost/openlitespeed/proxy/{s}/urlrewrite/{n}_{s}.conf".format(p=self.setupPath,n=proxyname_md5,s=get.sitename)
                    c = public.readFile(ols_conf_file)
                    if c:
                        rep = r'RewriteRule\s*\^{}\(\.\*\)\$\s+http://{}/\$1\s*\[P,E=Proxy-Host:{}\]'.format(
                            conf[i]["proxydir"], get.proxyname, conf[i]["todomain"])
                        new_content = 'RewriteRule ^{}(.*)$ http://{}/$1 [P,E=Proxy-Host:{}]'.format(get.proxydir,
                                                                                                     get.proxyname,
                                                                                                     get.todomain)
                        c = re.sub(rep, new_content, c)
                        public.writeFile(ols_conf_file, c)

                    conf[i]["proxydir"] = get.proxydir
                    conf[i]["proxysite"] = get.proxysite
                    conf[i]["todomain"] = get.todomain
                    conf[i]["type"] = int(get.type)
                    conf[i]["cache"] = int(get.cache)
                    conf[i]["subfilter"] = json.loads(get.subfilter)
                    conf[i]["advanced"] = int(get.advanced)
                    conf[i]["cachetime"] = int(get.cachetime)
                    conf[i]["keepuri"] = int(get.keepuri)
                    conf[i]["rewritedir"] =  json.loads(get.rewritedir)

                    public.writeFile(ng_conf_file, ng_conf)
                    public.writeFile(ap_conf_file, ap_conf)
                    self.__write_config(self.__proxyfile, conf)
                    self.SetNginx(get)
                    self.SetApache(get.sitename)
                    # self.SetProxy(get)

                    # if int(get.type) != 1:
                    #     os.system("mv %s %s_bak" % (ap_conf_file, ap_conf_file))
                    #     os.system("mv %s %s_bak" % (ng_conf_file, ng_conf_file))
                    if not hasattr(get, 'notreload'):
                        public.serviceReload()
                    return public.return_message(0, 0, public.lang("Setup successfully!"))
    
    # ## 修改重定向
    # def setRewritedir(self, get):
    #     rewriteconf = ""
    #     if get.rewritedir:
    #         for d in json.loads(get.rewritedir):
    #             if not d["dir1"] or not d["dir2"] or d["dir1"] == d["dir2"] or d["dir1"] == "/":
    #                 continue
    #             rewriteconf += '\n\t\trewrite \^{0}/(\.\*)$ {1}\/$1 break;'.format(d["dir1"], d["dir2"])
    #     return rewriteconf
    ## 修改重定向
    def setRewritedir(self, get):
        rewriteconf = ""
        if "rewritedir" not in get:
            return rewriteconf
        for d in json.loads(get.rewritedir):
            if not d["dir1"] or not d["dir2"] or d["dir1"] == d["dir2"] or d["dir1"] == "/":
                continue
            rewriteconf += '\trewrite ^{0}/(.*)$ {1}/$1 break;'.format(d["dir1"], d["dir2"])
        return rewriteconf

        # 设置反向代理
    def SetProxy(self, get):
        sitename = get.sitename  # 站点名称
        advanced = int(get.advanced)
        type = int(get.type)
        cache = int(get.cache)
        cachetime = int(get.cachetime)
        proxysite = get.proxysite
        keepuri= int(get.keepuri)
        proxydir = get.proxydir
        ng_file = self.setupPath + "/panel/vhost/nginx/" + sitename + ".conf"
        ap_file = self.setupPath + "/panel/vhost/apache/" + sitename + ".conf"
        p_conf = self.__read_config(self.__proxyfile)
        random_string = public.GetRandomString(8)

        # websocket前置map
        map_file = self.setupPath + "/panel/vhost/nginx/0.websocket.conf"
        if not os.path.exists(map_file):
            map_body = '''map $http_upgrade $connection_upgrade {
    default upgrade;
    ''  close;
}
'''
            public.writeFile(map_file, map_body)

        # 配置Nginx
        # 构造清理缓存连接

        #构造重写url
        rewriteconf=self.setRewritedir(get)
        # if get.rewritedir:
        #     for d in json.loads(get.rewritedir):
        #         if not d["dir1"] or not d["dir2"] or d["dir1"] == d["dir2"] or d["dir1"] == "/":
        #             continue
        #         rewriteconf += '\n\trewrite \^{0}/(\.\*)$ {1}\/$1 break;'.format(d["dir1"], d["dir2"])
        
            

        # 构造缓存配置
        ng_cache = r"""
    if ( $uri ~* "\.(gif|png|jpg|css|js|woff|woff2)$" )
    {
    	expires 1m;
    }
    proxy_ignore_headers Set-Cookie Cache-Control expires;
    proxy_cache cache_one;
    proxy_cache_key $host$uri$is_args$args;
    proxy_cache_valid 200 304 301 302 %sm;""" % (cachetime)
        no_cache = r"""
    set $static_file%s 0;
    if ( $uri ~* "\.(gif|png|jpg|css|js|woff|woff2)$" )
    {
    	set $static_file%s 1;
    	expires 1m;
        }
    if ( $static_file%s = 0 )
    {
    add_header Cache-Control no-cache;
    }""" % (random_string, random_string, random_string)
        # rep = r"(https?://[\w\.]+)"
        # proxysite1 = re.search(rep,get.proxysite).group(1)
        ng_proxy = '''
#PROXY-START%s

location %s
{
    %s
    proxy_pass %s;
    proxy_set_header Host %s;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header REMOTE-HOST $remote_addr;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection $connection_upgrade;
    proxy_http_version 1.1;
    # proxy_hide_header Upgrade;
    %s

    add_header X-Cache $upstream_cache_status;

    #Set Nginx Cache
    %s
    %s
}

#PROXY-END%s'''
        ng_proxy_cache = ''
        proxyname_md5 = self.__calc_md5(get.proxyname)
        ng_proxyfile = "%s/panel/vhost/nginx/proxy/%s/%s_%s.conf" % (self.setupPath, sitename, proxyname_md5, sitename)
        ng_proxydir = "%s/panel/vhost/nginx/proxy/%s" % (self.setupPath, sitename)
        if not os.path.exists(ng_proxydir):
            public.ExecShell("mkdir -p %s" % ng_proxydir)

        # 构造替换字符串
        ng_subdata = ''
        ng_sub_filter = '''
    proxy_set_header Accept-Encoding "";%s
    sub_filter_once off;'''
        if get.subfilter:
            for s in json.loads(get.subfilter):
                if not s["sub1"]:
                    continue
                if '"' in s["sub1"]:
                    s["sub1"] = s["sub1"].replace('"', '\\"')
                if '"' in s["sub2"]:
                    s["sub2"] = s["sub2"].replace('"', '\\"')
                ng_subdata += '\n\tsub_filter "%s" "%s";' % (s["sub1"], s["sub2"])
        if ng_subdata:
            ng_sub_filter = ng_sub_filter % (ng_subdata)
        else:
            ng_sub_filter = ''
        # 构造反向代理
        # 如果代理URL后缀带有URI则删除URI，正则匹配不支持proxypass处带有uri
        # php_pass_proxy = get.proxysite
        # if get.proxysite[-1] == '/' or get.proxysite.count('/') > 2 or '?' in get.proxysite:
        #     php_pass_proxy = re.search(r'(https?\:\/\/[\w\.]+)', get.proxysite).group(0)
        if keepuri==1: # 保留URI
            if proxysite[-1] == '/':
                proxysite = proxysite[:-1]
        else: # 删除URI
            proxysite = '{}/'.format(proxysite)
        if advanced == 1:
            if proxydir[-1] != '/':
                proxydir = '{}/'.format(proxydir)
            # if proxysite[-1] != '/':
            #     proxysite = '{}/'.format(proxysite)
            if type == 1 and cache == 1:
                ng_proxy_cache += ng_proxy % (
                    proxydir, proxydir,rewriteconf, proxysite, get.todomain,
                    ("#Persistent connection related configuration"), ng_sub_filter, ng_cache,
                    get.proxydir)
            if type == 1 and cache == 0:
                ng_proxy_cache += ng_proxy % (
                    get.proxydir, get.proxydir,rewriteconf, proxysite, get.todomain,
                    ("#Persistent connection related configuration"), ng_sub_filter, no_cache,
                    get.proxydir)
        else:
            if type == 1 and cache == 1:
                ng_proxy_cache += ng_proxy % (
                    get.proxydir, get.proxydir,rewriteconf, proxysite, get.todomain,
                    ("#Persistent connection related configuration"), ng_sub_filter, ng_cache,
                    get.proxydir)
            if type == 1 and cache == 0:
                ng_proxy_cache += ng_proxy % (
                    get.proxydir, get.proxydir,rewriteconf, proxysite, get.todomain,
                    ("#Persistent connection related configuration"), ng_sub_filter, no_cache,
                    get.proxydir)
        public.writeFile(ng_proxyfile, ng_proxy_cache)

        # APACHE
        # 反向代理文件
        ap_proxyfile = "%s/panel/vhost/apache/proxy/%s/%s_%s.conf" % (
            self.setupPath, get.sitename, proxyname_md5, get.sitename)
        ap_proxydir = "%s/panel/vhost/apache/proxy/%s" % (self.setupPath, get.sitename)
        if not os.path.exists(ap_proxydir):
            public.ExecShell("mkdir -p %s" % ap_proxydir)
        ap_proxy = ''
        if type == 1:
            ap_proxy += '''#PROXY-START%s
<IfModule mod_proxy.c>
    ProxyRequests Off
    SSLProxyEngine on
    ProxyPass %s %s/
    ProxyPassReverse %s %s/
    </IfModule>
#PROXY-END%s''' % (get.proxydir, get.proxydir, get.proxysite, get.proxydir,
                   get.proxysite, get.proxydir)
        public.writeFile(ap_proxyfile, ap_proxy)
        isError = public.checkWebConfig()
        if (isError != True):
            if public.get_webserver() == "nginx":
                shutil.copyfile('/tmp/ng_file_bk.conf', ng_file)
            else:
                shutil.copyfile('/tmp/ap_file_bk.conf', ap_file)
            for i in range(len(p_conf) - 1, -1, -1):
                if get.sitename == p_conf[i]["sitename"] and p_conf[i]["proxyname"]:
                    del p_conf[i]
            self.RemoveProxy(get)
            return public.return_message(-1, 0, 'ERROR: %s<br><a style="color:red;">' % public.get_msg_gettext(
                'Configuration ERROR') + isError.replace("\n",
                                                         '<br>') + '</a>')
        return public.return_message(0, 0, public.lang("Setup successfully!"))

    # 开启缓存
    def ProxyCache(self, get):
        if public.get_webserver() != 'nginx':
            return_message = public.return_msg_gettext(False, 'Currently only support Nginx')
            del return_message['status']
            return public.return_message(-1, 0, return_message['msg'])
        file = self.setupPath + "/panel/vhost/nginx/" + get.siteName + ".conf"
        conf = public.readFile(file)
        if conf.find('proxy_pass') == -1:
            return_message = public.return_msg_gettext(False, 'Failed to set')
            del return_message['status']
            return public.return_message(-1, 0, return_message['msg'])
        if conf.find('#proxy_cache') != -1:
            conf = conf.replace('#proxy_cache', 'proxy_cache')
            conf = conf.replace('#expires 12h', 'expires 12h')
        else:
            conf = conf.replace('proxy_cache', '#proxy_cache')
            conf = conf.replace('expires 12h', '#expires 12h')

        public.writeFile(file, conf)
        public.serviceReload()
        return_message = public.return_msg_gettext(True, 'Setup successfully!')
        del return_message['status']
        return public.return_message(0, 0, return_message['msg'])

    # 检查反向代理配置
    def CheckProxy(self, get):
        if public.get_webserver() != 'nginx': return public.return_message(0, 0, public.lang(""))
        file = self.setupPath + "/nginx/conf/proxy.conf"
        if not os.path.exists(file):
            conf = '''proxy_temp_path %s/nginx/proxy_temp_dir;
    proxy_cache_path %s/nginx/proxy_cache_dir levels=1:2 keys_zone=cache_one:10m inactive=1d max_size=5g;
    client_body_buffer_size 512k;
    proxy_connect_timeout 60;
    proxy_read_timeout 60;
    proxy_send_timeout 60;
    proxy_buffer_size 32k;
    proxy_buffers 4 64k;
    proxy_busy_buffers_size 128k;
    proxy_temp_file_write_size 128k;
    proxy_next_upstream error timeout invalid_header http_500 http_503 http_404;
    proxy_cache cache_one;''' % (self.setupPath, self.setupPath)
            public.writeFile(file, conf)

        file = self.setupPath + "/nginx/conf/nginx.conf"
        conf = public.readFile(file)
        if (conf.find('include proxy.conf;') == -1):
            rep = r"include\s+mime.types;"
            conf = re.sub(rep, "include mime.types;\n\tinclude proxy.conf;", conf)
            public.writeFile(file, conf)
        return public.return_message(0, 0, public.lang(""))

    def get_project_find(self, project_name):
        '''
            @name 获取指定项目配置
            @author hwliang<2021-08-09>
            @param project_name<string> 项目名称
            @return dict
        '''
        project_info = public.M('sites').where('project_type=? AND name=?', ('Java', project_name)).find()
        if not project_info: False
        project_info['project_config'] = json.loads(project_info['project_config'])
        return project_info

    # 取伪静态规则应用列表
    def GetRewriteList(self, get):
        # 校验参数
        try:
            get.validate([
                Param('siteName').String(),
            ], [
                public.validate.trim_filter(),
            ])
        except Exception as ex:
            public.print_log("error info: {}".format(ex))
            return public.return_message(-1, 0, str(ex))

        if get.siteName.find('node_') == 0:
            get.siteName = get.siteName.replace('node_', '')
        rewriteList = {}

        # 处理多服务
        if public.get_multi_webservice_status():
            service = public.M('sites').where("name=?", (get.siteName,)).field('id,service_type').find()
            if not service:
                return public.return_message(-1, 0, 'The website does not exist.')
            get.id = service['id']
            ws = service['service_type'] if service['service_type'] else 'nginx'
        else:
            ws = public.get_webserver()
        if ws == "openlitespeed":
            ws = "apache"
        if ws == 'apache':
            get.id = public.M('sites').where("name=?", (get.siteName,)).getField('id')
            runPath = self.GetSiteRunPath(get).get('message', {})
            if runPath.get('runPath', '').find('/www/server/stop') != -1:
                runPath['runPath'] = runPath['runPath'].replace('/www/server/stop', '')
            rewriteList['sitePath'] = public.M('sites').where("name=?", (get.siteName,)).getField('path') + runPath.get(
                'runPath', '')

        rewriteList['rewrite'] = []
        rewriteList['rewrite'].append('0.' + "Current")
        for ds in os.listdir('rewrite/' + ws):
            if ds == 'list.txt': continue
            rewriteList['rewrite'].append(ds[0:len(ds) - 5])
        rewriteList['rewrite'] = sorted(rewriteList['rewrite'])
        return public.return_message(0, 0, rewriteList)

    # 保存伪静态模板
    def SetRewriteTel(self, get):
        # 校验参数
        try:
            get.validate([
                Param('name').String(),
                Param('data').String(),
            ], [
                public.validate.trim_filter(),
            ])
        except Exception as ex:
            public.print_log("error info: {}".format(ex))
            return public.return_message(-1, 0, str(ex))

        ws = public.get_webserver()
        if public.get_multi_webservice_status() and get.get('site_id',''):
            service_type = public.M('sites').where('id = ?',get.site_id).field('service_type').find()
            if service_type:
                ws = service_type['service_type'] if service_type['service_type'] else 'nginx'

        if not get.name:
            return_message = public.return_msg_gettext(True, 'Please enter a template name')
            del return_message['status']
            return public.return_message(0, 0, return_message['msg'])
        if ws == "openlitespeed":
            ws = "apache"
        if sys.version_info[0] == 2: get.name = get.name.encode('utf-8')
        filename = 'rewrite/' + ws + '/' + get.name + '.conf'
        public.writeFile(filename, get.data)
        return_message = public.return_msg_gettext(True, 'New URL rewrite rule has been saved!')
        del return_message['status']
        return public.return_message(0, 0, return_message['msg'])

    # 打包
    def ToBackup(self, get):
        # 校验参数
        try:
            get.validate([
                Param('id').Integer(),
            ], [
                public.validate.trim_filter(),
            ])
        except Exception as ex:
            public.print_log("error info: {}".format(ex))
            return public.return_message(-1, 0, str(ex))

        id = get.id
        find = public.M('sites').where("id=?", (id,)).field('name,path,id').find()
        import time
        fileName = find['name'] + '_' + time.strftime('%Y%m%d_%H%M%S', time.localtime()) + '.zip'
        backupPath = session['config']['backup_path'] + '/site'
        zipName = backupPath + '/' + fileName
        if not (os.path.exists(backupPath)): os.makedirs(backupPath)
        tmps = '/tmp/panelExec.log'
        execStr = "cd '" + find['path'] + "' && zip '" + zipName + "' -x .user.ini -r ./ > " + tmps + " 2>&1"
        public.ExecShell(execStr)
        sql = public.M('backup').add('type,name,pid,filename,size,addtime',
                                     (0, fileName, find['id'], zipName, 0, public.getDate()))
        public.write_log_gettext('Site manager', 'Backup site [{}] succeed!', (find['name'],))
        return_message = public.return_msg_gettext(True, 'Backup Succeeded!')
        del return_message['status']
        return public.return_message(0, 0, return_message['msg'])

    # 删除备份文件
    def DelBackup(self, get):
        # 校验参数
        try:
            get.validate([
                Param('id').Integer(),
            ], [
                public.validate.trim_filter(),
            ])
        except Exception as ex:
            public.print_log("error info: {}".format(ex))
            return public.return_message(-1, 0, str(ex))

        id = get.id
        where = "id=?"
        backup_info = public.M('backup').where(where, (id,)).find()
        filename = backup_info['filename']
        if os.path.exists(filename): os.remove(filename)
        name = ''
        if filename == 'qiniu':
            name = backup_info['name']
            public.ExecShell(
                public.get_python_bin() + " " + self.setupPath + '/panel/script/backup_qiniu.py delete_file ' + name)

        pid = backup_info['pid']
        site_name = public.M('sites').where('id=?', (pid,)).getField('name')
        public.write_log_gettext('Site manager', 'Successfully deleted backup [{}] of site [{}]!',
                                 (site_name, filename))
        public.M('backup').where(where, (id,)).delete()
        return_message = public.return_msg_gettext(True, 'Successfully deleted')
        del return_message['status']
        return public.return_message(0, 0, return_message['msg'])

    # 旧版本配置文件处理
    def OldConfigFile(self):
        # 检查是否需要处理
        moveTo = 'data/moveTo.pl'
        if os.path.exists(moveTo): return

        # 处理Nginx配置文件
        filename = self.setupPath + "/nginx/conf/nginx.conf"
        if os.path.exists(filename):
            conf = public.readFile(filename)
            if conf.find('include vhost/*.conf;') != -1:
                conf = conf.replace('include vhost/*.conf;', 'include ' + self.setupPath + '/panel/vhost/nginx/*.conf;')
                public.writeFile(filename, conf)

        self.moveConf(self.setupPath + "/nginx/conf/vhost", self.setupPath + '/panel/vhost/nginx', 'rewrite',
                      self.setupPath + '/panel/vhost/rewrite')
        self.moveConf(self.setupPath + "/nginx/conf/rewrite", self.setupPath + '/panel/vhost/rewrite')

        # 处理Apache配置文件
        filename = self.setupPath + "/apache/conf/httpd.conf"
        if os.path.exists(filename):
            conf = public.readFile(filename)
            if conf.find('IncludeOptional conf/vhost/*.conf') != -1:
                conf = conf.replace('IncludeOptional conf/vhost/*.conf',
                                    'IncludeOptional ' + self.setupPath + '/panel/vhost/apache/*.conf')
                public.writeFile(filename, conf)

        self.moveConf(self.setupPath + "/apache/conf/vhost", self.setupPath + '/panel/vhost/apache')

        # 标记处理记录
        public.writeFile(moveTo, 'True')
        public.serviceReload()

    # 移动旧版本配置文件
    def moveConf(self, Path, toPath, Replace=None, ReplaceTo=None):
        if not os.path.exists(Path): return
        import shutil

        letPath = '/etc/letsencrypt/live'
        nginxPath = self.setupPath + '/nginx/conf/key'
        apachePath = self.setupPath + '/apache/conf/key'
        for filename in os.listdir(Path):
            # 准备配置文件
            name = filename[0:len(filename) - 5]
            filename = Path + '/' + filename
            conf = public.readFile(filename)

            # 替换关键词
            if Replace: conf = conf.replace(Replace, ReplaceTo)
            ReplaceTo = letPath + name
            Replace = 'conf/key/' + name
            if conf.find(Replace) != -1: conf = conf.replace(Replace, ReplaceTo)
            Replace = 'key/' + name
            if conf.find(Replace) != -1: conf = conf.replace(Replace, ReplaceTo)
            public.writeFile(filename, conf)

            # 提取配置信息
            if conf.find('server_name') != -1:
                self.formatNginxConf(filename)
            elif conf.find('<Directory') != -1:
                # self.formatApacheConf(filename)
                pass

            # 移动文件
            shutil.move(filename, toPath + '/' + name + '.conf')

            # 转移证书
            self.moveKey(nginxPath + '/' + name, letPath + '/' + name)
            self.moveKey(apachePath + '/' + name, letPath + '/' + name)

        # 删除多余目录
        shutil.rmtree(Path)
        # 重载服务
        public.serviceReload()

    # 从Nginx配置文件获取站点信息
    def formatNginxConf(self, filename):

        # 准备基础信息
        name = os.path.basename(filename[0:len(filename) - 5])
        if name.find('.') == -1: return
        conf = public.readFile(filename)
        # 取域名
        rep = r"server_name\s+(.+);"
        tmp = re.search(rep, conf)
        if not tmp: return
        domains = tmp.groups()[0].split(' ')

        # 取根目录
        rep = r"root\s+(.+);"
        tmp = re.search(rep, conf)
        if not tmp: return
        path = tmp.groups()[0]

        # 提交到数据库
        self.toSiteDatabase(name, domains, path)

    # 从Apache配置文件获取站点信息
    def formatApacheConf(self, filename):
        # 准备基础信息
        name = os.path.basename(filename[0:len(filename) - 5])
        if name.find('.') == -1: return
        conf = public.readFile(filename)

        # 取域名
        rep = "ServerAlias\\s+(.+)\n"
        tmp = re.search(rep, conf)
        if not tmp: return
        domains = tmp.groups()[0].split(' ')

        # 取根目录
        rep = u"DocumentRoot\\s+\"(.+)\"\n"
        tmp = re.search(rep, conf)
        if not tmp: return
        path = tmp.groups()[0]

        # 提交到数据库
        self.toSiteDatabase(name, domains, path)

    # 添加到数据库
    def toSiteDatabase(self, name, domains, path):
        if public.M('sites').where('name=?', (name,)).count() > 0: return
        public.M('sites').add('name,path,status,ps,addtime',
                              (name, path, '1', public.lang("Please enter a note"), public.getDate()))
        pid = public.M('sites').where("name=?", (name,)).getField('id')
        for domain in domains:
            public.M('domain').add('pid,name,port,addtime', (pid, domain, '80', public.getDate()))

    # 移动旧版本证书
    def moveKey(self, srcPath, dstPath):
        if not os.path.exists(srcPath): return
        import shutil
        os.makedirs(dstPath)
        srcKey = srcPath + '/key.key'
        srcCsr = srcPath + '/csr.key'
        if os.path.exists(srcKey): shutil.move(srcKey, dstPath + '/privkey.pem')
        if os.path.exists(srcCsr): shutil.move(srcCsr, dstPath + '/fullchain.pem')

    # 路径处理
    def GetPath(self, path):
        if path[-1] == '/':
            return path[0:-1]
        return path

    # 日志开关
    def logsOpen(self, get):
        # 校验参数
        try:
            get.validate([
                Param('id').Integer(),

            ], [
                public.validate.trim_filter(),
            ])
        except Exception as ex:
            public.print_log("error info: {}".format(ex))
            return public.return_message(-1, 0, str(ex))

        get.name = public.M('sites').where("id=?", (get.id,)).getField('name')
        # APACHE
        filename = public.GetConfigValue('setup_path') + '/panel/vhost/apache/' + get.name + '.conf'
        if os.path.exists(filename):
            conf = public.readFile(filename)
            # if conf.find('#ErrorLog') != -1:
            #     conf = conf.replace("#ErrorLog", "ErrorLog").replace('#CustomLog', 'CustomLog')
            # else:
            #     conf = conf.replace("ErrorLog", "#ErrorLog").replace('CustomLog', '#CustomLog')

            if conf and conf.find('CustomLog') > -1:
                regex_obj = re.compile(r'(?:# *)?(CustomLog(?: +\S+){0,2})[^\r\n]*')
                # 检查环境变量dontlog是否存在
                if conf.find('SetEnvIf Request_URI ".*" dontlog') > -1:
                    # 启用Access日志
                    conf = regex_obj.sub(r'\1', conf)
                    conf = conf.replace('SetEnvIf Request_URI ".*" dontlog\n', '')
                else:
                    # 禁用Access日志
                    conf = regex_obj.sub(r'SetEnvIf Request_URI ".*" dontlog{}\1 env=!dontlog'.format('\n\t'), conf)

                public.writeFile(filename, conf)

        # NGINX
        filename = public.GetConfigValue('setup_path') + '/panel/vhost/nginx/' + get.name + '.conf'
        if os.path.exists(filename):
            conf = public.readFile(filename)
            rep = public.GetConfigValue('logs_path') + "/" + get.name + ".log"
            # if conf.find(rep) != -1:
            #     conf = conf.replace(rep, "/dev/null")
            # else:
            #     # conf = re.sub('}\n\\s+access_log\\s+off', '}\n\taccess_log  ' + rep, conf)
            #     conf = conf.replace('access_log  /dev/null', 'access_log  ' + rep)

            if conf:
                regex_obj = re.compile(r'(?:# *)?(access_log +(?:{}|off; # Disable with aapanel))(?: *;)?'.format(rep.replace('.', r'\.')))
                if conf.find('access_log {}'.format(rep)) > -1:
                    # 禁用Access日志
                    conf = regex_obj.sub('access_log off; # Disable with aapanel'.format(rep), conf)
                else:
                    # 启用Access日志
                    conf = regex_obj.sub('access_log {};'.format(rep), conf)

                public.writeFile(filename, conf)

        # OLS
        filename = public.GetConfigValue('setup_path') + '/panel/vhost/openlitespeed/detail/' + get.name + '.conf'
        conf = public.readFile(filename)
        # if conf:
        #     rep = "\nerrorlog(.|\n)*compressArchive\\s*1\\s*\n}"
        #     tmp = re.search(rep, conf)
        #     s = 'on'
        #     if not tmp:
        #         s = 'off'
        #         rep = "\n#errorlog(.|\n)*compressArchive\\s*1\\s*\n#}"
        #         tmp = re.search(rep, conf)
        #     tmp = tmp.group()
        #     if tmp:
        #         result = ''
        #         if s == 'on':
        #             for l in tmp.strip().splitlines():
        #                 result += "\n#" + l
        #         else:
        #             for l in tmp.splitlines():
        #                 result += "\n" + l[1:]
        #         conf = re.sub(rep, "\n" + result.strip(), conf)
        #         public.writeFile(filename, conf)

        if conf:
            regex_obj = 'accesslog +(.+?) +\\{(?:.|\n)*?}\n'
            m = re.search(regex_obj, conf)
            if m:
                regex_obj_2 = re.compile('LogLevel +(.+)\n')
                m2 = re.search(regex_obj_2, m.group())
                if m2:
                    # 启用Access日志
                    s = regex_obj_2.sub('', m.group())
                    conf = conf.replace(m.group(), s)
                else:
                    # 禁用Access日志
                    s = m.group().replace('}', '\tLogLevel NONE # Disable with aapanel\n}')
                    conf = conf.replace(m.group(), s)

            public.writeFile(filename, conf)

        public.serviceReload()
        return public.return_message(0, 0, public.lang("Setup successfully!"))

    # 取日志状态
    def GetLogsStatus(self, get):
        if not hasattr(get, 'name') or not get.name:
            return public.return_message(-1, 0, "Missing site name")
        if isinstance(get.name, list):
            site_name = get.name[0] if get.name else ''
        elif isinstance(get.name, str):
            site_name = get.name
        else:
            site_name = str(get.name)
        site_name = site_name.strip()
        if not site_name:
            return public.return_message(0, 0, True)
        filename = public.GetConfigValue('setup_path') + '/panel/vhost/' + public.get_webserver() + '/' + get.name + '.conf'
        if public.get_webserver() == 'openlitespeed':
            filename = public.GetConfigValue('setup_path') + '/panel/vhost/' + public.get_webserver() + '/detail/' + get.name + '.conf'
        conf = public.readFile(filename)

        if not conf:
            return public.return_message(0, 0, True)

        # Nginx
        if conf.find('access_log off; # Disable with aapanel') > -1:
            return public.return_message(0, 0, False)

        # Apache
        if conf.find('SetEnvIf Request_URI ".*" dontlog') > -1:
            return public.return_message(0, 0, False)

        # OpenLiteSpeed
        if conf.find('LogLevel NONE # Disable with aapanel') > -1:
            return public.return_message(0, 0, False)

        # 兼容旧方式
        if conf.find('#ErrorLog') != -1:
            return public.return_message(0, 0, False)

        if conf.find("access_log  /dev/null") != -1:
            return public.return_message(0, 0, False)

        if re.search('\n#accesslog', conf):
            return public.return_message(0, 0, False)

        return public.return_message(0, 0, True)

    # 取目录加密状态
    def GetHasPwd(self, get):
        if not hasattr(get, 'siteName'):
            get.siteName = public.M('sites').where('id=?', (get.id,)).getField('name')
            if not get.siteName:
                return public.return_message(-1, 0, False)
            get.configFile = self.setupPath + '/panel/vhost/nginx/' + get.siteName + '.conf'
        conf = public.readFile(get.configFile)
        if type(conf) == bool: return public.return_message(0, 0, False)
        if conf.find('#AUTH_START') != -1: return public.return_message(0, 0, True)
        return public.return_message(0, 0, False)

    # 设置目录加密
    def SetHasPwd(self, get):
        # 校验参数
        try:
            get.validate([
                Param('username').String(),
                Param('password').String(),
                Param('id').Integer(),
            ], [
                public.validate.trim_filter(),
            ])
        except Exception as ex:
            public.print_log("error info: {}".format(ex))
            return public.return_message(-1, 0, str(ex))

        if public.get_webserver() == 'openlitespeed':
            return public.return_message(-1, 0, public.lang("The current web server is openlitespeed. This function is not supported yet."))
        if len(get.username.strip()) < 3 or len(get.password.strip()) < 3: return public.return_message(-1, 0, public.lang("Username or password cannot be less than 3 digits!"))

        if not hasattr(get, 'siteName'):
            get.siteName = public.M('sites').where('id=?', (get.id,)).getField('name')

        self.CloseHasPwd(get)
        filename = public.GetConfigValue('setup_path') + '/pass/' + get.siteName + '.pass'
        try:
            passconf = get.username + ':' + public.hasPwd(get.password)
        except:
            return public.return_message(-1, 0, public.lang("The password fomart is wrong, please do not use special symbols for the first two digits!"))

        if get.siteName == 'phpmyadmin':
            get.configFile = self.setupPath + '/nginx/conf/nginx.conf'
            if os.path.exists(self.setupPath + '/panel/vhost/nginx/phpmyadmin.conf'):
                get.configFile = self.setupPath + '/panel/vhost/nginx/phpmyadmin.conf'
                conf = public.readFile(get.configFile)
                rep = r"\n\s*#AUTH_START(.|\n){1,200}#AUTH_END"
                conf = re.sub(rep, '', conf)
                public.writeFile(get.configFile, conf)

        else:
            get.configFile = self.setupPath + '/panel/vhost/nginx/' + get.siteName + '.conf'

        # 处理Nginx配置
        conf = public.readFile(get.configFile)
        if conf:
            rep = '#error_page   404   /404.html;'
            if conf.find(rep) == -1: rep = '#error_page 404/404.html;'
            data = '''
    #AUTH_START
    auth_basic "Authorization";
    auth_basic_user_file %s;
    #AUTH_END''' % (filename,)
            conf = conf.replace(rep, rep + data)
            public.writeFile(get.configFile, conf)

        if get.siteName == 'phpmyadmin':
            get.configFile = self.setupPath + '/apache/conf/extra/httpd-vhosts.conf'
            if os.path.exists(self.setupPath + '/panel/vhost/apache/phpmyadmin.conf'):
                get.configFile = self.setupPath + '/panel/vhost/apache/phpmyadmin.conf'
        else:
            get.configFile = self.setupPath + '/panel/vhost/apache/' + get.siteName + '.conf'

        conf = public.readFile(get.configFile)
        if conf:
            # 处理Apache配置
            rep = 'SetOutputFilter'
            if conf.find(rep) != -1:
                data = '''#AUTH_START
        AuthType basic
        AuthName "Authorization "
        AuthUserFile %s
        Require user %s
        #AUTH_END
        ''' % (filename, get.username)
                conf = conf.replace(rep, data + rep)
                conf = conf.replace(' Require all granted', " #Require all granted")
                public.writeFile(get.configFile, conf)

        # 写密码配置
        passDir = public.GetConfigValue('setup_path') + '/pass'
        if not os.path.exists(passDir): public.ExecShell('mkdir -p ' + passDir)
        public.writeFile(filename, passconf)
        public.serviceReload()
        public.write_log_gettext("Site manager", "Set site [{}] to password authentication required!", (get.siteName,))
        return public.return_message(0, 0, public.lang("Setup successfully!"))

    # 取消目录加密
    def CloseHasPwd(self, get):
        # 校验参数
        try:
            get.validate([
                Param('id').Integer(),

            ], [
                public.validate.trim_filter(),
            ])
        except Exception as ex:
            public.print_log("error info: {}".format(ex))
            return public.return_message(-1, 0, str(ex))

        if not hasattr(get, 'siteName'):
            get.siteName = public.M('sites').where('id=?', (get.id,)).getField('name')

        if get.siteName == 'phpmyadmin':
            get.configFile = self.setupPath + '/nginx/conf/nginx.conf'
            # 2025/6/4 修复php额外密码访问
            if os.path.exists('/www/server/panel/vhost/nginx/phpmyadmin.conf'):
                conf = public.readFile('/www/server/panel/vhost/nginx/phpmyadmin.conf')
                rep = r"\n\s*#AUTH_START(.|\n){1,200}#AUTH_END"
                conf = re.sub(rep, '', conf)
                public.writeFile('/www/server/panel/vhost/nginx/phpmyadmin.conf', conf)
        else:
            get.configFile = self.setupPath + '/panel/vhost/nginx/' + get.siteName + '.conf'

        if os.path.exists(get.configFile):
            conf = public.readFile(get.configFile)
            rep = "\n\\s*#AUTH_START(.|\n){1,200}#AUTH_END"
            conf = re.sub(rep, '', conf)
            public.writeFile(get.configFile, conf)

        if get.siteName == 'phpmyadmin':
            get.configFile = self.setupPath + '/apache/conf/extra/httpd-vhosts.conf'
            # 2025/6/4 修复php额外密码访问
            if os.path.exists(self.setupPath + '/panel/vhost/apache/phpmyadmin.conf'):
                get.configFile = self.setupPath + '/panel/vhost/apache/phpmyadmin.conf'
        else:
            get.configFile = self.setupPath + '/panel/vhost/apache/' + get.siteName + '.conf'

        if os.path.exists(get.configFile):
            conf = public.readFile(get.configFile)
            rep = "\n\\s*#AUTH_START(.|\n){1,200}#AUTH_END"
            conf = re.sub(rep, '', conf)
            conf = conf.replace(' #Require all granted', " Require all granted")
            public.writeFile(get.configFile, conf)
        public.serviceReload()
        public.write_log_gettext("Site manager", "Cleared password authentication for site [{}]!", (get.siteName,))
        return public.return_message(0, 0, public.lang("Setup successfully!"))

    # 启用tomcat支持
    def SetTomcat(self, get):
        siteName = get.siteName
        name = siteName.replace('.', '_')

        rep = r"^(\d{1,3}\.){3,3}\d{1,3}$"
        if re.match(rep, siteName):
            return_message = public.return_msg_gettext(False, 'ERROR, primary domain cannot be IP address!')
            del return_message['status']
            return public.return_message(-1, 0, return_message['msg'])

        # nginx
        filename = self.setupPath + '/panel/vhost/nginx/' + siteName + '.conf'
        if os.path.exists(filename):
            conf = public.readFile(filename)
            if conf.find('#TOMCAT-START') != -1: return self.CloseTomcat(get)
            tomcatConf = r'''#TOMCAT-START
    location /
    {
        proxy_pass "http://%s:8080";
        proxy_set_header Host %s;
        proxy_set_header X-Forwarded-For $remote_addr;
    }
    location ~ .*\.(gif|jpg|jpeg|bmp|png|ico|txt|js|css)$
    {
        expires      12h;
    }

    location ~ .*\.war$
    {
        return 404;
    }
    #TOMCAT-END
    ''' % (siteName, siteName)
            rep = 'include enable-php'
            conf = conf.replace(rep, tomcatConf + rep)
            public.writeFile(filename, conf)

        # apache
        filename = self.setupPath + '/panel/vhost/apache/' + siteName + '.conf'
        if os.path.exists(filename):
            conf = public.readFile(filename)
            if conf.find('#TOMCAT-START') != -1: return self.CloseTomcat(get)
            tomcatConf = '''#TOMCAT-START
    <IfModule mod_proxy.c>
        ProxyRequests Off
        SSLProxyEngine on
        ProxyPass / http://%s:8080/
        ProxyPassReverse / http://%s:8080/
        RequestHeader unset Accept-Encoding
        ExtFilterDefine fixtext mode=output intype=text/html cmd="/bin/sed 's,:8080,,g'"
        SetOutputFilter fixtext
    </IfModule>
    #TOMCAT-END
    ''' % (siteName, siteName)

            rep = '#PATH'
            conf = conf.replace(rep, tomcatConf + rep)
            public.writeFile(filename, conf)
        path = public.M('sites').where("name=?", (siteName,)).getField('path')
        import tomcat
        tomcat.tomcat().AddVhost(path, siteName)
        public.serviceReload()
        public.ExecShell('/etc/init.d/tomcat stop')
        public.ExecShell('/etc/init.d/tomcat start')
        public.ExecShell('echo "127.0.0.1 ' + siteName + '" >> /etc/hosts')
        public.write_log_gettext('Site manager', 'Turned on Tomcat supporting for site [{}]!', (siteName,))
        return public.return_msg_gettext(True, public.lang("Succeeded, please test JSP program!"))

    # 关闭tomcat支持
    def CloseTomcat(self, get):
        if not os.path.exists('/etc/init.d/tomcat'): return public.return_message(-1, 0, public.lang(""))
        siteName = get.siteName
        name = siteName.replace('.', '_')

        # nginx
        filename = self.setupPath + '/panel/vhost/nginx/' + siteName + '.conf'
        if os.path.exists(filename):
            conf = public.readFile(filename)
            rep = "\\s*#TOMCAT-START(.|\n)+#TOMCAT-END"
            conf = re.sub(rep, '', conf)
            public.writeFile(filename, conf)

        # apache
        filename = self.setupPath + '/panel/vhost/apache/' + siteName + '.conf'
        if os.path.exists(filename):
            conf = public.readFile(filename)
            rep = "\\s*#TOMCAT-START(.|\n)+#TOMCAT-END"
            conf = re.sub(rep, '', conf)
            public.writeFile(filename, conf)
        public.ExecShell('rm -rf ' + self.setupPath + '/panel/vhost/tomcat/' + name)
        try:
            import tomcat
            tomcat.tomcat().DelVhost(siteName)
        except:
            pass
        public.serviceReload()
        public.ExecShell('/etc/init.d/tomcat restart')
        public.ExecShell("sed -i '/" + siteName + "/d' /etc/hosts")
        public.write_log_gettext('Site manager', 'Turned off Tomcat supporting for site [{}]!', (siteName,))
        return_message = public.return_msg_gettext(True, 'Tomcat mapping closed!')
        del return_message['status']
        return public.return_message(0, 0, return_message['msg'])

    # 取当站点前运行目录
    def GetSiteRunPath(self, get):
        site = public.M('sites').where('id=?', (get.id,)).field('name,path,service_type').find()
        if not site:
            return public.return_message(-1, 0, public.lang("The website does not exist"))

        siteName = site['name']
        sitePath = site['path']
        serviceType = site['service_type']
        if not siteName:
            return public.return_message(0, 0, {"runPath": "/", 'dirs': []})
        if sitePath and os.path.isfile(sitePath):
            return public.return_message(0, 0, {"runPath": "/", 'dirs': []})
        path = sitePath

        # 添加多服务识别
        webserver = public.get_webserver()
        if public.get_multi_webservice_status():
            if not serviceType or serviceType == 'nginx':
                webserver = 'nginx'
            else:
                webserver = serviceType

        if webserver == 'nginx':
            filename = self.setupPath + '/panel/vhost/nginx/' + siteName + '.conf'
            if os.path.exists(filename):
                conf = public.readFile(filename)
                rep = r'\s*root\s+(.+);'
                path = re.search(rep, conf)
                if not path:
                    return_message = public.return_msg_gettext(False, 'Get Site run path false')
                    del return_message['status']
                    return public.return_message(-1, 0, return_message['msg'])
                path = path.groups()[0]
        elif webserver == 'apache':
            filename = self.setupPath + '/panel/vhost/apache/' + siteName + '.conf'
            if os.path.exists(filename):
                conf = public.readFile(filename)
                rep = '\\s*DocumentRoot\\s*"(.+)"\\s*\n'
                path = re.search(rep, conf)
                if not path:
                    return_message = public.return_msg_gettext(False, 'Get Site run path false')
                    del return_message['status']
                    return public.return_message(-1, 0, return_message['msg'])
                path = path.groups()[0]
        else:
            filename = self.setupPath + '/panel/vhost/openlitespeed/' + siteName + '.conf'
            if os.path.exists(filename):
                conf = public.readFile(filename)
                rep = r"vhRoot\s*(.*)"
                path = re.search(rep, conf)
                if not path:
                    return_message = public.return_msg_gettext(False, 'Get Site run path false')
                    del return_message['status']
                    return public.return_message(-1, 0, return_message['msg'])
                path = path.groups()[0]
        data = {}
        if sitePath == path:
            data['runPath'] = '/'
        else:
            data['runPath'] = path.replace(sitePath, '')

            if data['runPath'] == path:
                data['runPath'] = '/'

        dirnames = []
        dirnames.append('/')
        if not os.path.exists(sitePath):
            os.makedirs(sitePath, exist_ok=True)
        for filename in os.listdir(sitePath):
            try:
                json.dumps(filename)
                if sys.version_info[0] == 2:
                    filename = filename.encode('utf-8')
                else:
                    filename.encode('utf-8')
                filePath = sitePath + '/' + filename
                if not os.path.exists(filePath): continue
                if os.path.islink(filePath): continue
                if os.path.isdir(filePath):
                    dirnames.append('/' + filename)
            except:
                pass

        data['dirs'] = dirnames
        return public.return_message(0, 0, data)

    # 设置当前站点运行目录
    def SetSiteRunPath(self, get):
        # 校验参数
        try:
            get.validate([
                Param('runPath').String(),
                Param('id').Integer(),
            ], [
                public.validate.trim_filter(),
            ])
        except Exception as ex:
            public.print_log("error info: {}".format(ex))
            return public.return_message(-1, 0, str(ex))

        siteName = public.M('sites').where('id=?', (get.id,)).getField('name')
        sitePath = public.M('sites').where('id=?', (get.id,)).getField('path')
        old_run_path = self.GetRunPath(get)['message']['result']
        # 处理Nginx
        filename = self.setupPath + '/panel/vhost/nginx/' + siteName + '.conf'
        if os.path.exists(filename):
            conf = public.readFile(filename)
            if conf:
                rep = r'\s*root\s+(.+);'
                tmp = re.search(rep, conf)
                if tmp:
                    path = tmp.groups()[0]
                    conf = conf.replace(path, sitePath + get.runPath)
                    public.writeFile(filename, conf)

        # 处理Apache
        filename = self.setupPath + '/panel/vhost/apache/' + siteName + '.conf'
        if os.path.exists(filename):
            conf = public.readFile(filename)
            if conf:
                rep = '\\s*DocumentRoot\\s*"(.+)"\\s*\n'
                tmp = re.search(rep, conf)
                if tmp:
                    path = tmp.groups()[0]
                    conf = conf.replace(path, sitePath + get.runPath)
                    public.writeFile(filename, conf)
        # 处理OLS
        self._set_ols_run_path(sitePath, get.runPath, siteName)
        # self.DelUserInI(sitePath)
        # get.path = sitePath;
        # self.SetDirUserINI(get);
        s_path = sitePath + old_run_path + "/.user.ini"
        d_path = sitePath + get.runPath + "/.user.ini"
        if s_path != d_path:
            public.ExecShell("chattr -i {}".format(s_path))
            public.ExecShell("mv {} {}".format(s_path, d_path))
            public.ExecShell("chattr +i {}".format(d_path))

        public.serviceReload()
        return_message = public.return_msg_gettext(True, public.lang('Setup successfully!'))
        del return_message['status']
        return public.return_message(0, 0, return_message['msg'])

    def _set_ols_run_path(self, site_path, run_path, sitename):
        ols_conf_file = "{}/panel/vhost/openlitespeed/{}.conf".format(self.setupPath, sitename)
        ols_conf = public.readFile(ols_conf_file)
        if not ols_conf:
            return
        reg = '#VHOST\\s*{s}\\s*START(.|\n)+#VHOST\\s*{s}\\s*END'.format(s=sitename)
        tmp = re.search(reg, ols_conf)
        if not tmp:
            return
        reg = r"vhRoot\s*(.*)"
        # tmp = re.search(reg,tmp.group())
        # if not tmp:
        #     return
        tmp = "vhRoot " + site_path + run_path
        ols_conf = re.sub(reg, tmp, ols_conf)
        public.writeFile(ols_conf_file, ols_conf)

    # 设置默认站点
    def SetDefaultSite(self, get):
        # 校验参数
        try:
            get.validate([
                Param('name').String(),
            ], [
                public.validate.trim_filter(),
            ])
        except Exception as ex:
            public.print_log("error info: {}".format(ex))
            return public.return_message(-1, 0, str(ex))

        import time
        if public.GetWebServer() in ['openlitespeed']:
            return public.return_message(-1, 0, public.lang("OpenLiteSpeed does not support setting the default site"))
        default_site_save = 'data/defaultSite.pl'
        # 清理旧的
        defaultSite = public.readFile(default_site_save)
        http2 = ''
        versionStr = public.readFile('/www/server/nginx/version.pl')
        if versionStr:
            if versionStr.find('1.8.1') == -1 and versionStr.find('1.25') == -1 and versionStr.find('1.26') == -1: http2 = ' http2'
        if defaultSite:
            path = self.setupPath + '/panel/vhost/nginx/' + defaultSite + '.conf'
            if os.path.exists(path):
                conf = public.readFile(path)
                rep = r"listen\s+80.+;"
                conf = re.sub(rep, 'listen 80;', conf, 1)
                rep = r"listen\s+\[::\]:80.+;"
                conf = re.sub(rep, 'listen [::]:80;', conf, 1)
                rep = r"listen\s+443.+;"
                conf = re.sub(rep, 'listen 443 ssl' + http2 + ';', conf, 1)
                rep = r"listen\s+\[::\]:443.+;"
                conf = re.sub(rep, 'listen [::]:443 ssl' + http2 + ';', conf, 1)
                public.writeFile(path, conf)

            path = self.setupPath + '/apache/htdocs/.htaccess'
            if os.path.exists(path): os.remove(path)

        if get.name == '0':
            if os.path.exists(default_site_save): os.remove(default_site_save)
            public.serviceReload()
            return_message = public.return_msg_gettext(True, 'Setup successfully!')
            del return_message['status']
            return public.return_message(0, 0, return_message['msg'])

        # 处理新的
        path = self.setupPath + '/apache/htdocs'
        if os.path.exists(path):
            conf = '''<IfModule mod_rewrite.c>
  RewriteEngine on
  RewriteCond %{HTTP_HOST} !^127.0.0.1 [NC] 
  RewriteRule (.*) http://%s/$1 [L]
</IfModule>'''
            conf = conf.replace("%s", get.name)
            if get.name == 'off': conf = ''
            public.writeFile(path + '/.htaccess', conf)

        path = self.setupPath + '/panel/vhost/nginx/' + get.name + '.conf'
        if os.path.exists(path):
            conf = public.readFile(path)
            rep = r"listen\s+80\s*;"
            conf = re.sub(rep, 'listen 80 default_server;', conf, 1)
            rep = r"listen\s+\[::\]:80\s*;"
            conf = re.sub(rep, 'listen [::]:80 default_server;', conf, 1)
            rep = r"listen\s+443\s*ssl\s*\w*\s*;"
            conf = re.sub(rep, 'listen 443 ssl' + http2 + ' default_server;', conf, 1)
            rep = r"listen\s+\[::\]:443\s*ssl\s*\w*\s*;"
            conf = re.sub(rep, 'listen [::]:443 ssl' + http2 + ' default_server;', conf, 1)
            public.writeFile(path, conf)

        path = self.setupPath + '/panel/vhost/nginx/default.conf'
        if os.path.exists(path): public.ExecShell('rm -f ' + path)
        public.writeFile(default_site_save, get.name)
        public.serviceReload()
        return_message = public.return_msg_gettext(True, 'Setup successfully!')
        del return_message['status']
        return public.return_message(0, 0, return_message['msg'])

    # 取默认站点
    def GetDefaultSite(self, get):
        data = {}
        data['sites'] = public.M('sites').where('project_type=? OR project_type=?', ('PHP', 'WP')).field('name').order(
            'id desc').select()
        data['defaultSite'] = public.readFile('data/defaultSite.pl')
        return public.return_message(0, 0, data)

    # 扫描站点
    def CheckSafe(self, get):
        import db, time
        isTask = '/tmp/panelTask.pl'
        if os.path.exists(self.setupPath + '/panel/class/panelSafe.py'):
            import py_compile
            py_compile.compile(self.setupPath + '/panel/class/panelSafe.py')
        get.path = public.M('sites').where('id=?', (get.id,)).getField('path')
        execstr = "cd " + public.GetConfigValue(
            'setup_path') + "/panel/class && " + public.get_python_bin() + " panelSafe.pyc " + get.path
        sql = db.Sql()
        sql.table('tasks').add('id,name,type,status,addtime,execstr', (
            None, '%s [' % public.lang("Scan directory") + get.path + ']', 'execshell', '0',
            time.strftime('%Y-%m-%d %H:%M:%S'),
            execstr))
        public.writeFile(isTask, 'True')
        public.write_log_gettext('Installer', 'Added trojan scan task for directory [{}]!', (get.path,))
        return_message = public.return_msg_gettext(True, 'Scan Task has in the queue!')
        del return_message['status']
        return public.return_message(0, 0, return_message['msg'])

    # 获取结果信息
    def GetCheckSafe(self, get):
        get.path = public.M('sites').where('id=?', (get.id,)).getField('path')
        path = get.path + '/scan.pl'
        result = {}
        result['data'] = []
        result['phpini'] = []
        result['userini'] = result['sshd'] = True
        result['scan'] = False
        result['outime'] = result['count'] = result['error'] = 0
        if not os.path.exists(path): return result
        import json
        return public.return_message(0, 0, json.loads(public.readFile(path)))

    # 更新病毒库
    def UpdateRulelist(self, get):
        try:
            conf = public.httpGet(public.getUrl() + '/install/ruleList.conf')
            if conf:
                public.writeFile(self.setupPath + '/panel/data/ruleList.conf', conf)
                return_message = public.return_msg_gettext(True, 'Update Succeeded!')
                del return_message['status']
                return public.return_message(0, 0, return_message['msg'])
            return_message = public.return_msg_gettext(False, 'Failed to connect server!')
            del return_message['status']
            return public.return_message(-1, 0, return_message['msg'])
        except:
            return_message = public.return_msg_gettext(False, 'Failed to connect server!')
            del return_message['status']
            return public.return_message(-1, 0, return_message['msg'])

    def set_site_etime_multiple(self, get):
        '''
            @name 批量网站到期时间
            @author zhwen<2020-11-17>
            @param sites_id "1,2"
            @param edate 2020-11-18
        '''
        sites_id = get.sites_id.split(',')
        set_edate_successfully = []
        set_edate_failed = {}
        for site_id in sites_id:
            get.id = site_id
            site_name = public.M('sites').where("id=?", (site_id,)).getField('name')
            if not site_name:
                continue
            try:
                self.SetEdate(get)
                set_edate_successfully.append(site_name)
            except:
                set_edate_failed[site_name] = 'There was an error setting, please try again.'
                pass
        return_message = {'msg': public.get_msg_gettext('Set the website [{}] expiration time successfully',
                                                        (','.join(set_edate_successfully),)),
                          'error': set_edate_failed,
                          'success': set_edate_successfully}
        return public.return_message(0, 0, return_message)

    # 设置到期时间
    def SetEdate(self, get):
        # 校验参数
        try:
            get.validate([
                Param('edate').String(),
                Param('id').Integer(),
            ], [
                public.validate.trim_filter(),
            ])
        except Exception as ex:
            public.print_log("error info: {}".format(ex))
            return public.return_message(-1, 0, str(ex))

        result = public.M('sites').where('id=?', (get.id,)).setField('edate', get.edate)
        siteName = public.M('sites').where('id=?', (get.id,)).getField('name')
        public.write_log_gettext('Site manager', 'Set expired date to [{}] for site[{}]!', (get.edate, siteName))
        return_message = public.return_msg_gettext(True,
                                                   'Successfully set, the site will stop automatically when expires!')
        del return_message['status']
        return public.return_message(0, 0, return_message['msg'])

    # 获取防盗链状态
    def GetSecurity(self, get):
        # 校验参数
        try:
            get.validate([
                Param('name').String(),
                Param('id').Integer(),
            ], [
                public.validate.trim_filter(),
            ])
        except Exception as ex:
            public.print_log("error info: {}".format(ex))
            return public.return_message(-1, 0, str(ex))

        file = '/www/server/panel/vhost/nginx/' + get.name + '.conf'
        conf = public.readFile(file)
        data = {}

        # 检查配置文件是否读取成功
        if not isinstance(conf, str) or not conf.strip():
            return public.return_message(-1, 0, public.lang("Reading configuration file failed!"))

        if type(conf) == bool: return public.return_message(-1, 0, public.lang("Reading configuration file failed!"))
        if conf.find('SECURITY-START') != -1:
            rep = "#SECURITY-START(\n|.)+#SECURITY-END"
            tmp = re.search(rep, conf)
            if not tmp:
                return public.return_message(-1, 0, public.lang("The configuration file parsing failed. Please check if the configuration is correct."))

            tmp = tmp.group()
            content = re.search(r"\(.+\)\$", tmp)
            if content:
                data['fix'] = content.group().replace('(', '').replace(')$', '').replace('|', ',')
            else:
                data['fix'] = ''
            try:
                data['domains'] = ','.join(list(set(re.search(r"valid_referers\s+none\s+blocked\s+(.+);\n", tmp).groups()[0].split())))
            except:
                data['domains'] = ','.join(list(set(re.search(r"valid_referers\s+(.+);\n", tmp).groups()[0].split())))
            data['status'] = True
            data['http_status'] = tmp.find('none blocked') != -1
            try:
                data['return_rule'] = re.findall(r'(return|rewrite)\s+.*(\d{3}|(/.+)\s+(break|last));', conf)[0][
                    1].replace('break', '').strip()
            except:
                data['return_rule'] = '404'
        else:
            conf_file = self.conf_dir + '/{}_door_chain.json'.format(get.name)
            data = {
                'fix': 'jpg,jpeg,gif,png,js,css',
                'domains': '',
                'return_rule': '404',
                'status': False,
                'http_status': False
            }
            # 尝试读取 JSON 配置
            json_content = public.readFile(conf_file)
            if isinstance(json_content, str) and json_content.strip():
                try:
                    json_data = json.loads(json_content)
                    if isinstance(json_data, dict):
                        data.update({
                            'fix': json_data.get('fix', data['fix']),
                            'status': json_data.get('status', False) is True or json_data.get('status') == "true",
                            'http_status': json_data.get('http_status', False),
                            'return_rule': str(json_data.get('return_rule', '404')).strip() or '404'
                        })
                except Exception as e:
                    pass

            try:

                domains = public.M('domain').where('pid=?', (get.id,)).field('name').select()
                if isinstance(domains, list):
                    domain_names = []
                    for item in domains:
                        if isinstance(item, dict) and 'name' in item:
                            name = item['name'].strip()
                            if name:
                                domain_names.append(name)
                    data['domains'] = ','.join(sorted(set(domain_names)))
            except Exception as e:
                data['domains'] = ''

        return public.return_message(0, 0, data)

    # 设置防盗链
    def SetSecurity(self, get):
        # 校验参数
        try:
            get.validate([
                Param('name').String(),
                Param('fix').String(),
                Param('domains').String(),
                Param('return_rule').String(),
                Param('id').Integer(),
                Param('status').Bool(),
                Param('http_status').Bool(),

            ], [
                public.validate.trim_filter(),
            ])
        except Exception as ex:
            public.print_log("error info: {}".format(ex))
            return public.return_message(-1, 0, str(ex))

        if len(get.fix) < 2: return public.return_message(-1, 0, public.lang("URL suffix cannot be empty!"))
        if len(get.domains) < 3: return public.return_message(-1, 0, public.lang("Anti-theft chain domain name cannot be empty!"))
        try:
            conf_file = self.conf_dir + '/{}_door_chain.json'.format(get.name)
        except Exception as ee:
            public.print_log('ee:{}'.format(ee))
        data = {
            "name": get.name,
            "fix": get.fix,
            "domains": get.domains,
            "status": get.status,
            "http_status": get.http_status,
            "return_rule": get.return_rule,
        }
        public.writeFile(conf_file, json.dumps(data))

        site = public.M('sites').where('name=?', (get.name,)).field('id,service_type').find()
        if not site:
            return public.return_message(-1, 0,'site is not found!')

        # nginx
        file = '/www/server/panel/vhost/nginx/' + get.name + '.conf'
        if os.path.exists(file):
            conf = public.readFile(file)
            if conf.find('SECURITY-START') != -1:
                # 先替换域名部分，防止域名过多导致替换失败
                rep = r"\s+valid_referers.+"
                conf = re.sub(rep, '', conf)
                # 再替换配置部分
                rep = "\\s+#?#SECURITY-START(\n|.){1,500}#SECURITY-END\n?"
                conf = re.sub(rep, '\n', conf)
            if get.status == 'false':
                public.write_log_gettext('Site manager', "Hotlink Protection for site [{}] disabled!", (get.name,))
                public.writeFile(file, conf)
            elif get.status == 'true':
                if conf.find('SECURITY-START') == -1:
                    return_rule = 'return 404'
                    if 'return_rule' in get:
                        get.return_rule = get.return_rule.strip()
                        if get.return_rule in ['404', '403', '200', '301', '302', '401', '201']:
                            return_rule = 'return {}'.format(get.return_rule)
                        else:
                            if get.return_rule[0] != '/':
                                return public.return_message(-1, 0, public.lang("Response resources should use URI path or HTTP status code, such as: /test.png or 404"))
                            return_rule = 'rewrite /.* {} break'.format(get.return_rule)
                    # 处理多服务PHP版本
                    s = ''
                    if site['service_type'] in ['apache', 'openlitespeed']:
                        s = '#'
                    rconf = r'''#SECURITY-START Hotlink protection configuration
    location ~ .*\.(%s)$
    {
        expires      30d;
        access_log /dev/null;
        valid_referers %s;
        if ($invalid_referer){
           %s;
        }
    }
    #SECURITY-END
    %sinclude enable-php-''' % (
                        get.fix.strip().replace(',', '|'), get.domains.strip().replace(',', ' '), return_rule,s)

                    conf = re.sub(r"include\s+enable-php-", rconf, conf)
                    public.write_log_gettext('Site manager', "Hotlink Protection for site [{}] enabled!", (get.name,))

                r_key = 'valid_referers none blocked'
                d_key = 'valid_referers'
                if get.http_status == 'true' and conf.find(r_key) == -1:
                    conf = conf.replace(d_key, r_key)
                elif get.http_status == 'false' and conf.find(r_key) != -1:
                    conf = conf.replace(r_key, d_key)
                public.writeFile(file, conf)

        # apache
        file = '/www/server/panel/vhost/apache/' + get.name + '.conf'
        if os.path.exists(file):
            conf = public.readFile(file)
            if conf.find('SECURITY-START') != -1:
                rep = "#SECURITY-START(\n|.){1,500}#SECURITY-END\n"
                conf = re.sub(rep, '', conf)
            if get.status == "false":
                public.writeFile(file, conf)
            elif get.status == 'true':
                if conf.find('SECURITY-START') == -1:
                    return_rule = '/404.html [R=404,NC,L]'
                    if 'return_rule' in get:
                        get.return_rule = get.return_rule.strip()
                        if get.return_rule in ['404', '403', '200', '301', '302', '401', '201']:
                            return_rule = '/{s}.html [R={s},NC,L]'.format(s=get.return_rule)
                        else:
                            if get.return_rule[0] != '/':
                                return public.return_message(-1, 0, public.lang("Response resources should use URI path or HTTP status code, such as: /test.png or 404"))
                            return_rule = '{}'.format(get.return_rule)

                    tmp = "    RewriteCond %{HTTP_REFERER} !{DOMAIN} [NC]"
                    tmps = []
                    for d in get.domains.split(','):
                        tmps.append(tmp.replace('{DOMAIN}', d))
                    domains = "\n".join(tmps)
                    rconf = "combined\n    #SECURITY-START Hotlink protection configuration\n    RewriteEngine on\n" + domains + "\n    RewriteRule .(" + get.fix.strip().replace(
                        ',', '|') + ") " + return_rule + "\n    #SECURITY-END"
                    conf = conf.replace('combined', rconf)

                r_key = '#SECURITY-START Hotlink protection configuration\n    RewriteEngine on\n    RewriteCond %{HTTP_REFERER} !^$ [NC]\n'
                d_key = '#SECURITY-START Hotlink protection configuration\n    RewriteEngine on\n'
                if get.http_status == 'true' and conf.find(r_key) == -1:
                    conf = conf.replace(d_key, r_key)
                elif get.http_status == 'false' and conf.find(r_key) != -1:
                    if conf.find('SECURITY-START') == -1: public.return_message(-1, 0,
                                                                                'Please activate the anti-theft chain first!')
                    conf = conf.replace(r_key, d_key)
                public.writeFile(file, conf)
        # OLS
        cond_dir = '/www/server/panel/vhost/openlitespeed/prevent_hotlink/'
        if not os.path.exists(cond_dir):
            os.makedirs(cond_dir)
        file = cond_dir + get.name + '.conf'
        if get.http_status == 'true':
            conf = r"""
RewriteCond %{HTTP_REFERER} !^$
RewriteCond %{HTTP_REFERER} !BTDOMAIN_NAME [NC]
RewriteRule \.(BTPFILE)$    /404.html   [R,NC]
"""
            conf = conf.replace('BTDOMAIN_NAME', get.domains.replace(',', ' ')).replace('BTPFILE',
                                                                                        get.fix.replace(',', '|'))
        else:
            conf = r"""
RewriteCond %{HTTP_REFERER} !BTDOMAIN_NAME [NC]
RewriteRule \.(BTPFILE)$    /404.html   [R,NC]
"""
            conf = conf.replace('BTDOMAIN_NAME', get.domains.replace(',', ' ')).replace('BTPFILE',
                                                                                        get.fix.replace(',', '|'))
        public.writeFile(file, conf)
        if get.status == "false":
            if os.path.exists(file): os.remove(file)
        public.serviceReload()
        return public.return_message(0, 0, public.lang("Setup successfully!"))

    # xss 防御
    def xsssec(self, text):
        replace_list = {
            "<": "＜",
            ">": "＞",
            "'": "＇",
            '"': "＂",
        }
        for k, v in replace_list.items():
            text = text.replace(k, v)
        return public.xssencode2(text)

    # 取网站日志
    def GetSiteLogs(self, get):
        # 校验参数
        try:
            get.validate([
                Param('siteName').String(),
            ], [
                public.validate.trim_filter(),
            ])
        except Exception as ex:
            public.print_log("error info: {}".format(ex))
            return public.return_message(-1, 0, str(ex))

        serverType = public.get_webserver()
        if serverType == "nginx":
            logPath = '/www/wwwlogs/' + get.siteName + '.log'
        elif serverType == 'apache':
            logPath = '/www/wwwlogs/' + get.siteName + '-access_log'
        else:
            logPath = '/www/wwwlogs/' + get.siteName + '_ols.access_log'
        if not os.path.exists(logPath):
            return_message = public.return_msg_gettext(False, 'Log is empty')
            del return_message['status']
            return public.return_message(-1, 0, return_message['msg'])
        # return public.return_msg_gettext(True, self.xsssec(public.GetNumLines(logPath, 1000)))
        return_message = public.return_msg_gettext(True, self.xsssec(public.GetNumLines(logPath, 100))) # 暂时限制行数，后期加分页
        del return_message['status']
        return public.return_message(0, 0, return_message['msg'])
        # if not os.path.exists(logPath): return public.return_message(-1, 0, public.lang("Log is empty"))
        # return public.return_message(0,0, self.xsssec(public.GetNumLines(logPath, 1000)))

    # 取网站日志
    def get_site_err_log(self, get):
        # 校验参数
        try:
            get.validate([
                Param('siteName').String(),
            ], [
                public.validate.trim_filter(),
            ])
        except Exception as ex:
            public.print_log("error info: {}".format(ex))
            return public.return_message(-1, 0, str(ex))

        return_status = 0
        serverType = public.get_webserver()
        if serverType == "nginx":
            logPath = '/www/wwwlogs/' + get.siteName + '.error.log'
        elif serverType == 'apache':
            logPath = '/www/wwwlogs/' + get.siteName + '-error_log'
        else:
            logPath = '/www/wwwlogs/' + get.siteName + '_ols.error_log'
        if not os.path.exists(logPath):
            return_message = public.return_msg_gettext(False, 'Log is empty')
            del return_message['status']
            return public.return_message(-1, 0, return_message['msg'])
        return_message = public.return_msg_gettext(True, self.xsssec(public.GetNumLines(logPath, 1000)))
        del return_message['status']
        return public.return_message(0, 0, return_message['msg'])

    # 取网站分类
    def get_site_types(self, get):
        data = public.M("site_types").field("id,name").order("id asc").select()
        if not isinstance(data, list):
            data = []
        data.insert(0, {"id": 0, "name": public.lang("Default category")})
        for i in data:
            i['name'] = public.xss_version(i['name'])
        return public.return_message(0, 0, data)

    # 取网站列表
    def get_site_list(self, get):
        sql = public.M('sites')
        if hasattr(get, 'search'):
            sql = sql.where("project_type !='Node' and name like ? ",('%{search}%'.format(search=get.search),))
        data = sql.field("id,name").order("id asc").select()
        return public.return_message(0, 0, data)

    # 添加网站分类
    def add_site_type(self, get):
        # 校验参数
        try:
            get.validate([
                Param('name').String(),
            ], [
                public.validate.trim_filter(),
            ])
        except Exception as ex:
            public.print_log("error info: {}".format(ex))
            return public.return_message(-1, 0, str(ex))

        get.name = get.name.strip()
        if not get.name:
            return_message = public.return_msg_gettext(False, 'Category name cannot be empty')
            del return_message['status']
            return public.return_message(-1, 0, return_message['msg'])
        if len(get.name) > 16:
            return_message = public.return_msg_gettext(False, 'Category name cannot exceed 16 letters')
            del return_message['status']
            return public.return_message(-1, 0, return_message['msg'])
        type_sql = public.M('site_types')
        if type_sql.count() >= 10:
            return_message = public.return_msg_gettext(False, 'Add up to 10 categories!')
            del return_message['status']
            return public.return_message(-1, 0, return_message['msg'])
        if type_sql.where('name=?', (get.name,)).count() > 0:
            return_message = public.return_msg_gettext(False, 'Specified category name already exists!')
            del return_message['status']
            return public.return_message(-1, 0, return_message['msg'])
        type_sql.add("name", (public.xssencode2(get.name),))
        return_message = public.return_msg_gettext(True, 'Setup successfully!')
        del return_message['status']
        return public.return_message(0, 0, return_message['msg'])

    # 删除网站分类
    def remove_site_type(self, get):
        # 校验参数
        try:
            get.validate([
                Param('id').Integer(),
            ], [
                public.validate.trim_filter(),
            ])
        except Exception as ex:
            public.print_log("error info: {}".format(ex))
            return public.return_message(-1, 0, str(ex))

        type_sql = public.M('site_types')
        if type_sql.where('id=?', (get.id,)).count() == 0:
            return_message = public.return_msg_gettext(False, 'Specified category does NOT exist!')
            del return_message['status']
            return public.return_message(-1, 0, return_message['msg'])
        type_sql.where('id=?', (get.id,)).delete()
        public.M("sites").where("type_id=?", (get.id,)).save("type_id", (0,))
        return_message = public.return_msg_gettext(True, 'Category deleted!')
        del return_message['status']
        return public.return_message(0, 0, return_message['msg'])

    # 修改网站分类名称
    def modify_site_type_name(self, get):
        # 校验参数
        try:
            get.validate([
                Param('name').String(),
                Param('id').Integer(),
            ], [
                public.validate.trim_filter(),
            ])
        except Exception as ex:
            public.print_log("error info: {}".format(ex))
            return public.return_message(-1, 0, str(ex))

        get.name = get.name.strip()
        if not get.name:
            return_message = public.return_msg_gettext(False, 'Category name cannot be empty')
            del return_message['status']
            return public.return_message(-1, 0, return_message['msg'])
        if len(get.name) > 16:
            return_message = public.return_msg_gettext(False, 'Category name cannot exceed 16 letters')
            del return_message['status']
            return public.return_message(-1, 0, return_message['msg'])
        type_sql = public.M('site_types')
        if type_sql.where('id=?', (get.id,)).count() == 0:
            return_message = public.return_msg_gettext(False, 'Specified category does NOT exist!')
            del return_message['status']
            return public.return_message(-1, 0, return_message['msg'])
        type_sql.where('id=?', (get.id,)).setField('name', get.name)
        return_message = public.return_msg_gettext(True, 'Successfully modified')
        del return_message['status']
        return public.return_message(0, 0, return_message['msg'])

    # 设置指定站点的分类
    def set_site_type(self, get):
        site_ids = json.loads(get.site_ids)
        site_sql = public.M("sites")
        for s_id in site_ids:
            site_sql.where("id=?", (s_id,)).setField("type_id", get.id)
        return public.return_message(0, 0, public.lang("Setup successfully!"))

    # 设置目录保护
    def set_dir_auth(self, get):
        sd = site_dir_auth.SiteDirAuth()
        return sd.set_dir_auth(get)

    def delete_dir_auth_multiple(self, get):
        '''
            @name 批量目录保护
            @author zhwen<2020-11-17>
            @param site_id 1
            @param names test,baohu
        '''
        # 校验参数
        try:
            get.validate([
                Param('name').String(),
                Param('id').Integer(),
            ], [
                public.validate.trim_filter(),
            ])
        except Exception as ex:
            public.print_log("error info: {}".format(ex))
            return public.return_message(-1, 0, str(ex))

        names = get.names.split(',')
        del_successfully = []
        del_failed = {}
        for name in names:
            get.name = name
            get.id = get.site_id
            try:
                get.multiple = 1
                result = self.delete_dir_auth(get)
                if not result['status']:
                    del_failed[name] = result['msg']
                    continue
                del_successfully.append(name)
            except:
                del_failed[name] = public.lang("There was an error deleting, please try again.")
        public.serviceReload()
        return_message = {
            'msg': public.get_msg_gettext('Delete [ {} ] dir auth successfully', (','.join(del_successfully),)),
            'error': del_failed,
            'success': del_successfully}
        return public.return_message(0, 0, return_message)

    # 删除目录保护
    def delete_dir_auth(self, get):
        sd = site_dir_auth.SiteDirAuth()
        return sd.delete_dir_auth(get)

    # 获取目录保护列表
    def get_dir_auth(self, get):
        sd = site_dir_auth.SiteDirAuth()
        return sd.get_dir_auth(get)

    # 修改目录保护密码
    def modify_dir_auth_pass(self, get):
        sd = site_dir_auth.SiteDirAuth()
        return sd.modify_dir_auth_pass(get)

    def _check_path_total(self, path, limit):
        """
        根据路径获取文件/目录大小
        @path 文件或者目录路径
        return int
        """

        if not os.path.exists(path): return 0;
        if not os.path.isdir(path): return os.path.getsize(path)
        size_total = 0
        for nf in os.walk(path):
            for f in nf[2]:
                filename = nf[0] + '/' + f
                if not os.path.exists(filename): continue;
                if os.path.islink(filename): continue;
                size_total += os.path.getsize(filename)
                if size_total >= limit: return limit
        return size_total

    def get_average_num(self, slist):
        """
        @获取平均值
        """
        count = len(slist)
        limit_size = 1 * 1024 * 1024
        if count <= 0: return limit_size
        print(slist)
        if len(slist) > 1:
            slist = sorted(slist)
            limit_size = int((slist[0] + slist[-1]) / 2 * 0.85)
        return limit_size

    def check_del_data(self, get):
        """
        @删除前置检测
        @ids = [1,2,3]
        """
        # 校验参数
        try:
            get.validate([
                Param('ids').String(),
            ], [
                public.validate.trim_filter(),
            ])
        except Exception as ex:
            public.print_log("error info: {}".format(ex))
            return public.return_message(-1, 0, str(ex))

        ids = json.loads(get['ids'])
        slist = {}
        result = []

        import database_v2 as database
        db_data = database.database().get_database_size(ids, True)
        limit_size = 50 * 1024 * 1024
        f_list_size = [];
        db_list_size = []
        for id in ids:
            data = public.M('sites').where("id=?", (id,)).field('id,name,path,addtime').find();
            if not data: continue

            addtime = public.to_date(times=data['addtime'])

            data['st_time'] = addtime
            data['limit'] = False
            data['backup_count'] = public.M('backup').where("pid=? AND type=?", (data['id'], '0')).count()
            f_size = self._check_path_total(data['path'], limit_size)
            data['total'] = f_size;
            data['score'] = 0

            # 目录太小不计分
            if f_size > 0:
                f_list_size.append(f_size)

                # 10k 目录不参与排序
                if f_size > 10 * 1024: data['score'] = int(time.time() - addtime) + f_size

            if data['total'] >= limit_size: data['limit'] = True
            data['database'] = False

            find = public.M('databases').field('id,pid,name,ps,addtime').where('pid=?', (data['id'],)).find()
            if find:
                db_addtime = public.to_date(times=find['addtime'])

                data['database'] = db_data[find['name']]
                data['database']['st_time'] = db_addtime

                db_score = 0
                db_size = data['database']['total']

                if db_size > 0:
                    db_list_size.append(db_size)
                    if db_size > 50 * 1024: db_score += int(time.time() - db_addtime) + db_size

                data['score'] += db_score
            result.append(data)

        slist['data'] = sorted(result, key=lambda x: x['score'], reverse=True)
        slist['file_size'] = self.get_average_num(f_list_size)
        slist['db_size'] = self.get_average_num(db_list_size)
        return public.return_message(0, 0, slist)

    def get_https_mode(self, get=None):
        '''
            @name 获取https模式
            @author hwliang<2022-01-14>
            @return bool False.宽松模式 True.严格模式
        '''
        web_server = public.get_webserver()
        if web_server not in ['nginx', 'apache']:
            return public.return_message(0, 0, False)

        if web_server == 'nginx':
            default_conf_file = "{}/nginx/0.default.conf".format(public.get_vhost_path())
        else:
            default_conf_file = "{}/apache/0.default.conf".format(public.get_vhost_path())

        if not os.path.exists(default_conf_file): return public.return_message(0, 0, False)
        default_conf = public.readFile(default_conf_file)
        if not default_conf: return False

        if default_conf.find('DEFAULT SSL CONFI') != -1: return public.return_message(0, 0, True)
        return public.return_message(0, 0, False)

    def write_ngx_default_conf_by_ssl(self):
        '''
            @name 写nginx默认配置文件（含SSL配置）
            @author hwliang<2022-01-14>
            @return bool
        '''
        http2 = ''
        versionStr = public.readFile('/www/server/nginx/version.pl')
        if versionStr:
            if versionStr.find('1.8.1') == -1:
                http2 = ' http2'
        default_conf_body = '''server
{{
    listen 80;
    listen 443 ssl{http2};
    server_name _;
    index index.html;
    root /www/server/nginx/html;

    # DEFAULT SSL CONFIG
    ssl_certificate    /www/server/panel/vhost/cert/0.default/fullchain.pem;
    ssl_certificate_key    /www/server/panel/vhost/cert/0.default/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers EECDH+CHACHA20:EECDH+CHACHA20-draft:EECDH+AES128:RSA+AES128:EECDH+AES256:RSA+AES256:EECDH+3DES:RSA+3DES:!MD5;
    ssl_prefer_server_ciphers off;
    ssl_session_cache shared:SSL:10m;
    ssl_session_timeout 10m;
    add_header Strict-Transport-Security "max-age=31536000";
}}'''.format(http2=http2)
        ngx_default_conf_file = "{}/nginx/0.default.conf".format(public.get_vhost_path())
        self.create_default_cert()
        return public.writeFile(ngx_default_conf_file, default_conf_body)

    def write_ngx_default_conf(self):
        '''
            @name 写nginx默认配置文件
            @author hwliang<2022-01-14>
            @return bool
        '''
        default_conf_body = '''server
{
    listen 80;
    server_name _;
    index index.html;
    root /www/server/nginx/html;
}'''
        ngx_default_conf_file = "{}/nginx/0.default.conf".format(public.get_vhost_path())
        return public.writeFile(ngx_default_conf_file, default_conf_body)

    def write_apa_default_conf_by_ssl(self):
        '''
            @name 写nginx默认配置文件（含SSL配置）
            @author hwliang<2022-01-14>
            @return bool
        '''
        default_conf_body = '''<VirtualHost *:80>
    ServerAdmin webmaster@example.com
    DocumentRoot "/www/server/apache/htdocs"
    ServerName bt.default.com
    <Directory "/www/server/apache/htdocs">
        SetOutputFilter DEFLATE
        Options FollowSymLinks
        AllowOverride All
        Order allow,deny
        Allow from all
        DirectoryIndex index.html
    </Directory>
</VirtualHost>
<VirtualHost *:443>
    ServerAdmin webmaster@example.com
    DocumentRoot "/www/server/apache/htdocs"
    ServerName ssl.default.com

    # DEFAULT SSL CONFIG
    SSLEngine On
    SSLCertificateFile /www/server/panel/vhost/cert/0.default/fullchain.pem
    SSLCertificateKeyFile /www/server/panel/vhost/cert/0.default/privkey.pem
    SSLCipherSuite EECDH+CHACHA20:EECDH+CHACHA20-draft:EECDH+AES128:RSA+AES128:EECDH+AES256:RSA+AES256:EECDH+3DES:RSA+3DES:!MD5
    SSLProtocol All -SSLv2 -SSLv3 -TLSv1
    SSLHonorCipherOrder On

    <Directory "/www/server/apache/htdocs">
        SetOutputFilter DEFLATE
        Options FollowSymLinks
        AllowOverride All
        Order allow,deny
        Allow from all
        DirectoryIndex index.html
    </Directory>
</VirtualHost>'''
        apa_default_conf_file = "{}/apache/0.default.conf".format(public.get_vhost_path())
        self.create_default_cert()
        return public.writeFile(apa_default_conf_file, default_conf_body)

    def write_apa_default_conf(self):
        '''
            @name 写apache默认配置文件
            @author hwliang<2022-01-14>
            @return bool
        '''
        default_conf_body = '''<VirtualHost *:80>
            ServerAdmin webmaster@example.com
            DocumentRoot "/www/server/apache/htdocs"
            ServerName bt.default.com
            <Directory "/www/server/apache/htdocs">
                SetOutputFilter DEFLATE
                Options FollowSymLinks
                AllowOverride All
                Order allow,deny
                Allow from all
                DirectoryIndex index.html
            </Directory>
        </VirtualHost>
        <VirtualHost *:443>
            ServerAdmin webmaster@example.com
            DocumentRoot "/www/server/apache/htdocs"
            ServerName ssl.default.com

            # DEFAULT SSL CONFIG
            SSLEngine On
            SSLCertificateFile /www/server/panel/vhost/cert/0.default/fullchain.pem
            SSLCertificateKeyFile /www/server/panel/vhost/cert/0.default/privkey.pem
            SSLCipherSuite EECDH+CHACHA20:EECDH+CHACHA20-draft:EECDH+AES128:RSA+AES128:EECDH+AES256:RSA+AES256:EECDH+3DES:RSA+3DES:!MD5
            SSLProtocol All -SSLv2 -SSLv3 -TLSv1
            SSLHonorCipherOrder On

            <Directory "/www/server/apache/htdocs">
                SetOutputFilter DEFLATE
                Options FollowSymLinks
                AllowOverride All
                Order allow,deny
                Allow from all
                DirectoryIndex index.html
            </Directory>
        </VirtualHost>'''
        apa_default_conf_file = "{}/apache/0.default.conf".format(public.get_vhost_path())
        return public.writeFile(apa_default_conf_file, default_conf_body)

    def set_https_mode(self, get=None):
        '''
            @name 设置https模式
            @author hwliang<2022-01-14>
            @return dict
        '''
        web_server = public.get_webserver()
        if web_server not in ['nginx', 'apache']:
            return_message = public.return_msg_gettext(False, 'This function only supports Nginx/Apache')
            del return_message['status']
            return public.return_message(-1, 0, return_message['msg'])

        ngx_default_conf_file = "{}/nginx/0.default.conf".format(public.get_vhost_path())
        apa_default_conf_file = "{}/apache/0.default.conf".format(public.get_vhost_path())
        ngx_default_conf = public.readFile(ngx_default_conf_file)
        apa_default_conf = public.readFile(apa_default_conf_file)
        status = False
        if ngx_default_conf:
            if ngx_default_conf.find('DEFAULT SSL CONFIG') != -1:
                status = False
                self.write_ngx_default_conf()
                self.write_apa_default_conf()
            else:
                status = True
                self.write_ngx_default_conf_by_ssl()
                self.write_apa_default_conf_by_ssl()
        else:
            status = True
            self.write_ngx_default_conf_by_ssl()
            self.write_apa_default_conf_by_ssl()

        public.serviceReload()
        status_msg = {True: 'Open', False: 'Close'}
        msg = public.gettext_msg('Has {} HTTPS strict mode', (status_msg[status],))
        public.write_log_gettext('WebSite manager', msg)
        return_message = public.return_msg_gettext(True, msg)
        del return_message['status']
        return public.return_message(0, 0, return_message['msg'])

    def create_default_cert(self):
        '''
            @name 创建默认SSL证书
            @author hwliang<2022-01-14>
            @return bool
        '''
        cert_pem = '/www/server/panel/vhost/cert/0.default/fullchain.pem'
        cert_key = '/www/server/panel/vhost/cert/0.default/privkey.pem'
        if os.path.exists(cert_pem) and os.path.exists(cert_key): return True
        cert_path = os.path.dirname(cert_pem)
        if not os.path.exists(cert_path): os.makedirs(cert_path)
        import OpenSSL
        key = OpenSSL.crypto.PKey()
        key.generate_key(OpenSSL.crypto.TYPE_RSA, 2048)
        cert = OpenSSL.crypto.X509()
        cert.set_serial_number(0)
        # cert.get_subject().CN = ''
        cert.set_issuer(cert.get_subject())
        cert.gmtime_adj_notBefore(0)
        cert.gmtime_adj_notAfter(86400 * 3650)
        cert.set_pubkey(key)
        cert.sign(key, 'md5')
        cert_ca = OpenSSL.crypto.dump_certificate(OpenSSL.crypto.FILETYPE_PEM, cert)
        private_key = OpenSSL.crypto.dump_privatekey(OpenSSL.crypto.FILETYPE_PEM, key)
        if len(cert_ca) > 100 and len(private_key) > 100:
            public.writeFile(cert_pem, cert_ca, 'wb+')
            public.writeFile(cert_key, private_key, 'wb+')
            return True
        return False

    def get_upload_ssl_list(self, get):
        """
        @获取上传证书列表
        @siteName string 网站名称
        """
        siteName = get['siteName']
        path = '{}/vhost/upload_ssl/{}'.format(public.get_panel_path(), siteName)
        if not os.path.exists(path): os.makedirs(path)

        res = []
        for filename in os.listdir(path):
            try:
                filename = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(int(filename)))
                res.append(filename)
            except:
                pass
        return public.return_message(0, 0, res)

    # 获取指定证书基本信息
    def get_cert_init(self, cert_data, ssl_info=None):
        """
        @获取指定证书基本信息
        @cert_data string 证书数据
        @ssl_info dict 证书信息
        """
        try:
            result = {}
            if ssl_info and ssl_info['ssl_type'] == 'pfx':
                x509 = self.__check_pfx_pwd(cert_data, ssl_info['pwd'])[0]
            else:
                x509 = OpenSSL.crypto.load_certificate(OpenSSL.crypto.FILETYPE_PEM, cert_data)
            # 取产品名称
            issuer = x509.get_issuer()
            result['issuer'] = ''
            if hasattr(issuer, 'CN'):
                result['issuer'] = issuer.CN
            if not result['issuer']:
                is_key = [b'0', '0']
                issue_comp = issuer.get_components()
                if len(issue_comp) == 1:
                    is_key = [b'CN', 'CN']
                for iss in issue_comp:
                    if iss[0] in is_key:
                        result['issuer'] = iss[1].decode()
                        break
            # 取到期时间
            result['notAfter'] = self.strf_date(
                bytes.decode(x509.get_notAfter())[:-1])
            # 取申请时间
            result['notBefore'] = self.strf_date(
                bytes.decode(x509.get_notBefore())[:-1])
            # 取可选名称
            result['dns'] = []
            for i in range(x509.get_extension_count()):
                s_name = x509.get_extension(i)
                if s_name.get_short_name() in [b'subjectAltName', 'subjectAltName']:
                    s_dns = str(s_name).split(',')
                    for d in s_dns:
                        result['dns'].append(d.split(':')[1])
            subject = x509.get_subject().get_components()

            # 取主要认证名称
            if len(subject) == 1:
                result['subject'] = subject[0][1].decode()
            else:
                if len(result['dns']) > 0:
                    result['subject'] = result['dns'][0]
                else:
                    result['subject'] = '';
            return result
        except:
            return False

    def strf_date(self, sdate):
        """
        @转换证书时间
        """
        return time.strftime('%Y-%m-%d', time.strptime(sdate, '%Y%m%d%H%M%S'))

    def check_ssl_endtime(self, data, ssl_info=None):
        """
        @检查证书是否有效(证书最高有效期不超过1年)
        @data string 证书数据
        @ssl_info dict 证书信息
        """
        info = self.get_cert_init(data, ssl_info)
        if info:
            end_time = time.mktime(time.strptime(info['notAfter'], "%Y-%m-%d"))
            start_time = time.mktime(time.strptime(info['notBefore'], "%Y-%m-%d"))

            days = int((end_time - start_time) / 86400)
            if days < 400:  # 1年有效期+1个月续签时间
                return data
        return False

    # 证书转为pkcs12
    def dump_pkcs12(self, key_pem=None, cert_pem=None, ca_pem=None, friendly_name=None):
        """
        @证书转为pkcs12
        @key_pem string 私钥数据
        @cert_pem string 证书数据
        @ca_pem string 可选的CA证书数据
        @friendly_name string 可选的证书名称
        """
        p12 = OpenSSL.crypto.PKCS12()
        if cert_pem:
            x509 = OpenSSL.crypto.load_certificate(OpenSSL.crypto.FILETYPE_PEM, cert_pem.encode())
            p12.set_certificate(x509)
        if key_pem:
            p12.set_privatekey(OpenSSL.crypto.load_privatekey(
                OpenSSL.crypto.FILETYPE_PEM, key_pem.encode()))
        if ca_pem:
            p12.set_ca_certificates((OpenSSL.crypto.load_certificate(
                OpenSSL.crypto.FILETYPE_PEM, ca_pem.encode()),))
        if friendly_name:
            p12.set_friendlyname(friendly_name.encode())
        return p12

    def download_cert(self, get):
        """
        @下载证书
        @get dict 请求参数
            siteName string 网站名称
            ssl_type string 证书类型
            key string 密钥
            pem string 证书数据
            pwd string 证书密码
        """
        pem = get['pem']
        siteName = get['siteName']
        ssl_type = get['ssl_type']

        rpath = '{}/temp/ssl/'.format(public.get_panel_path())
        if os.path.exists(rpath): shutil.rmtree(rpath)

        ca_list = []
        path = '{}/{}_{}'.format(rpath, siteName, int(time.time()))
        if ssl_type == 'pfx':
            res = self.__check_pfx_pwd(base64.b64decode(pem), get['pwd'])
            p12 = res[1];
            x509 = res[0];
            get['pwd'] = res[2]
            print(get['pwd'])
            ca_list = []
            for x in p12.get_ca_certificates():
                ca_list.insert(0, OpenSSL.crypto.dump_certificate(OpenSSL.crypto.FILETYPE_PEM, x).decode().strip())
            ca_cert = '\n'.join(ca_list)
            key = OpenSSL.crypto.dump_privatekey(OpenSSL.crypto.FILETYPE_PEM, p12.get_privatekey()).decode().strip()
            domain_cert = OpenSSL.crypto.dump_certificate(OpenSSL.crypto.FILETYPE_PEM, x509).decode().strip()
        else:
            key = get['key']
            domain_cert = pem.split('-----END CERTIFICATE-----')[0] + "-----END CERTIFICATE-----\n"
            ca_cert = pem.replace(domain_cert, '')

            p12 = self.dump_pkcs12(key, '{}\n{}'.format(domain_cert.strip(), ca_cert), ca_cert)

        for x in ['IIS', 'Apache', 'Nginx', 'Other']:
            d_file = '{}/{}'.format(path, x)
            if not os.path.exists(d_file): os.makedirs(d_file)

            if x == 'IIS':
                public.writeFile2(d_file + '/fullchain.pfx', p12.export(), 'wb+')
                public.writeFile(d_file + '/password.txt', get['pwd'])
            elif x == 'Apache':
                public.writeFile(d_file + '/privkey.key', key)
                public.writeFile(d_file + '/root_bundle.crt', ca_cert)
                public.writeFile(d_file + '/domain.crt', domain_cert)
            else:
                public.writeFile(d_file + '/privkey.key', key)
                public.writeFile(d_file + '/fullchain.pem', '{}\n{}'.format(domain_cert.strip(), ca_cert))

        flist = []
        public.get_file_list(path, flist)

        zfile = '{}/{}.zip'.format(rpath, os.path.basename(path))
        import zipfile
        f = zipfile.ZipFile(zfile, 'w', zipfile.ZIP_DEFLATED)
        for item in flist:
            s_path = item.replace(path, '')
            if s_path: f.write(item, s_path)
        f.close()

        return public.return_message(0, 0, zfile);

    def check_ssl_info(self, get):
        """
        @解析证书信息
        @get dict 请求参数
            path string 上传文件路径
        """
        path = get['path']
        if not os.path.exists(path):
            return public.return_message(-1, 0, public.lang("Query failed, does not exist address"))

        info = {'root': '', 'cert': '', 'pem': '', 'key': ''}
        ssl_info = {'pwd': None, 'ssl_type': None}
        for filename in os.listdir(path):
            filepath = '{}/{}'.format(path, filename)
            ext = filename[-4:]
            if ext == '.pfx':
                ssl_info['ssl_type'] = 'pfx'

                f = open(filepath, 'rb')  # pfx为二进制文件
                info['pem'] = f.read()

            else:
                data = public.readFile(filepath)
                if filename.find('password') >= 0:  # 取pfx密码
                    ssl_info['pwd'] = re.search('([a-zA-Z0-9]+)', data).groups()[0]
                    continue

                if len(data) < 1024:
                    continue

                if data.find('PRIVATE KEY') >= 0:
                    info['key'] = data  # 取key

                if ext == '.pem':
                    if self.check_ssl_endtime(data):
                        info['pem'] = data
                else:
                    if data.find('BEGIN CERTIFICATE') >= 0:
                        if not info['root']:
                            info['root'] = data
                        else:
                            info['cert'] = data

        if ssl_info['ssl_type'] == 'pfx':
            info['pem'] = self.check_ssl_endtime(info['pem'], ssl_info)
            if info['pem']:
                info['pem'] = base64.b64encode(info['pem'])
                info['key'] = True
        else:
            if not info['pem']:
                # 确认ca证书和域名证书顺序
                info['pem'] = self.check_ssl_endtime(info['root'] + "\n" + info['cert'], ssl_info)
                if not info['pem']:
                    info['pem'] = self.check_ssl_endtime(info['cert'] + "\n" + info['root'], ssl_info)

        if info['key'] and info['pem']:
            return_message = {'key': info['key'], 'pem': info['pem'], 'ssl_type': ssl_info['ssl_type'],
                              'pwd': ssl_info['pwd']}
            return public.return_message(0, 0, return_message)
        return public.return_message(0, 0, False)

    def __check_pfx_pwd(self, data, pwd):
        """
        @检测pfx证书密码
        @data string pfx证书内容
        @pwd string 密码
        """
        try:
            p12 = OpenSSL.crypto.load_pkcs12(data, pwd)
            x509 = p12.get_certificate()
        except:
            pwd = re.search('([a-zA-Z0-9]+)', pwd).groups()[0]
            p12 = OpenSSL.crypto.load_pkcs12(data, pwd)
            x509 = p12.get_certificate()
        return [x509, p12, pwd]

    def auto_restart_rph(self, get):
        # 设置申请或续签SSL时自动停止反向代理、重定向、http to https，申请完成后自动开启
        conf_file = '{}/data/stop_rp_when_renew_ssl.pl'.format(public.get_panel_path())
        conf = public.readFile(conf_file)
        if not conf:
            public.writeFile(conf_file, json.dumps([get.sitename]))
        try:
            conf = json.loads(conf)
            if get.sitename not in conf:
                conf.append(get.sitename)
                public.writeFile(conf_file, json.dumps(conf))
        except:
            return public.return_message(0, 0, public.lang("Error parsing configuration file"))
        return public.return_message(0, 0, public.lang("Setup successfully"))

    def remove_auto_restart_rph(self, get):
        # 设置申请或续签SSL时自动停止反向代理、重定向、http to https，申请完成后自动开启
        conf_file = '{}/data/stop_rp_when_renew_ssl.pl'.format(public.get_panel_path())
        conf = public.readFile(conf_file)
        if not conf:
            return public.return_message(-1, 0, public.lang("Website [proxy,redirect,http to https]  are not set to restart automatically"))
        try:
            conf = json.loads(conf)
            conf.remove(get.sitename)
            public.writeFile(conf_file, json.dumps(conf))
        except:
            return public.return_message(-1, 0, public.lang("Configuration file parsing error"))
        return public.return_message(0, 0, public.lang("Setup successfully"))

    def get_auto_restart_rph(self, get):
        # 校验参数
        try:
            get.validate([
                Param('sitename').String(),
            ], [
                public.validate.trim_filter(),
            ])
        except Exception as ex:
            public.print_log("error info: {}".format(ex))
            return public.return_message(-1, 0, str(ex))

        # 设置申请或续签SSL时自动停止反向代理、重定向、http to https，申请完成后自动开启
        conf_file = '{}/data/stop_rp_when_renew_ssl.pl'.format(public.get_panel_path())
        conf = public.readFile(conf_file)
        if not conf:
            return public.return_message(-1, 0, public.lang("Website [proxy,redirect,http to https]  are not set to restart automatically"))
        try:
            conf = json.loads(conf)
            if get.sitename in conf:
                return public.return_message(0, 0, public.lang("This website has turn on [proxy,redirect,http to https] auto restart"))
            return public.return_message(-1, 0, public.lang("Website has turn off auto restart"))
        except:
            return public.return_message(-1, 0, public.lang("Configuration file parsing error"))

    # *********** WP Toolkit --Begin-- *************

    # 重置Wordpress管理员账号密码
    def reset_wp_password(self, get):
        import one_key_wp_v2 as one_key_wp
        return one_key_wp.one_key_wp().reset_wp_password(get)

    # 检查Wordpress版本更新
    def is_update(self, get):
        import one_key_wp_v2 as one_key_wp
        return one_key_wp.one_key_wp().is_update(get)

    # 清除Wordpress Nginx fastcgi cache
    def purge_all_cache(self, get):
        import one_key_wp_v2 as one_key_wp
        return one_key_wp.one_key_wp().purge_all_cache(get)

    # 设置Wordpress Nginx fastcgi cache
    def set_fastcgi_cache(self, get):
        import one_key_wp_v2 as one_key_wp
        return one_key_wp.one_key_wp().set_fastcgi_cache(get)

    # 更新Wordpress到最新版本
    def update_wp(self, get):
        import one_key_wp_v2 as one_key_wp
        return one_key_wp.one_key_wp().update_wp(get)

    # 获取可用的语言列表
    def get_language(self, get):
        import one_key_wp_v2 as one_key_wp
        return one_key_wp.one_key_wp().get_language(get)

    # 获取可用的WP安装版本
    def get_wp_versions(self, get):
        import one_key_wp_v2 as one_key_wp
        return one_key_wp.one_key_wp().get_wp_available_versions(get)

    # 获取WP Toolkit配置信息
    def get_wp_configurations(self, args):
        import one_key_wp_v2 as one_key_wp
        return one_key_wp.one_key_wp().get_wp_configurations(args)

    # 保存WP Toolkit配置
    def save_wp_configurations(self, args):
        import one_key_wp_v2 as one_key_wp
        return one_key_wp.one_key_wp().save_wp_configurations(args)

    # 批量设置wp网站类型
    def set_wp_site_type(self, args):
        site_ids = json.loads(args.site_ids)
        if not args.get('site_type',''):
            return public.return_message(-1, 0, "Type parameter is missing!")
        site_type_sql = public.M("wp_site_types").where("id=?", (args.site_type,)).find()

        if not site_type_sql:
            return public.return_message(-1, 0, "Type ID does not exist!")

        site_sql = public.M("wordpress_onekey")
        for s_id in site_ids:
            site_sql.where("s_id=?", (s_id,)).setField("site_type", site_type_sql['name'])

        return public.return_message(0, 0,"Setup successfully!")

    # 添加wp网站类型
    def add_wp_site_type(self, args):
        try:
            args.validate([
                Param('name').String(),
            ], [
                public.validate.trim_filter(),
            ])
        except Exception as ex:
            public.print_log("error info: {}".format(ex))
            return public.return_message(-1, 0, str(ex))

        args.name = args.name.strip()
        if not args.name:
            return_message = public.return_msg_gettext(False, 'Category name cannot be empty')
            del return_message['status']
            return public.return_message(-1, 0, return_message['msg'])
        if len(args.name) > 16:
            return_message = public.return_msg_gettext(False, 'Category name cannot exceed 16 letters')
            del return_message['status']
            return public.return_message(-1, 0, return_message['msg'])
        type_sql = public.M('wp_site_types')
        if type_sql.count() >= 10:
            return_message = public.return_msg_gettext(False, 'Add up to 10 categories!')
            del return_message['status']
            return public.return_message(-1, 0, return_message['msg'])
        if type_sql.where('name=?', (args.name,)).count() > 0:
            return_message = public.return_msg_gettext(False, 'Specified category name already exists!')
            del return_message['status']
            return public.return_message(-1, 0, return_message['msg'])
        type_sql.add("name", (args.name))
        return_message = public.return_msg_gettext(True, 'Setup successfully!')
        del return_message['status']
        return public.return_message(0, 0, return_message['msg'])

    # 编辑wp网站类型
    def edit_wp_site_type(self, args):
        try:
            args.validate([
                Param('id').Integer(),
                Param('name').String()
            ], [
                public.validate.trim_filter()
            ])
        except Exception as ex:
            return public.return_message(-1, 0, str(ex))

        args.name = args.name.strip()
        if not args.name:
            return_message = public.return_msg_gettext(False, 'Category name cannot be empty')
            del return_message['status']
            return public.return_message(-1, 0, return_message['msg'])

        if len(args.name) > 16:
            return_message = public.return_msg_gettext(False, 'Category name cannot exceed 16 letters')
            del return_message['status']
            return public.return_message(-1, 0, return_message['msg'])

        if args.id == 1:
            return_message = public.return_msg_gettext(False, 'Default value does not support modification')
            del return_message['status']
            return public.return_message(-1, 0, return_message['msg'])

        type_sql = public.M('wp_site_types')

        # 检查ID是否存在
        site_type = type_sql.where('id=?', (args.id,)).find()
        if not site_type:
            return_message = public.return_msg_gettext(False, 'Category does not exist!')
            del return_message['status']
            return public.return_message(-1, 0, return_message['msg'])

        # 检查新名称是否已存在(排除自身)
        if type_sql.where('name=?', (args.name,)).count() > 0:
            return_message = public.return_msg_gettext(False, 'Specified category name already exists!')
            del return_message['status']
            return public.return_message(-1, 0, return_message['msg'])

        # 更新分类，不使用外键约束
        type_sql.where('id=?', (args.id,)).setField('name', args.name)

        # 更新所有相关网站的分类
        public.M('wordpress_onekey').where('site_type=?', (site_type['name'],)).setField('site_type', args.name)
        return_message = public.return_msg_gettext(True, 'Update successfully!')
        del return_message['status']
        return public.return_message(0, 0, return_message['msg'])

    # 删除wp网站类型
    def del_wp_site_type(self, args):
        try:
            args.validate([
                Param('id').Integer(),
            ], [
                public.validate.trim_filter(),
            ])
        except Exception as ex:
            public.print_log("error info: {}".format(ex))
            return public.return_message(-1, 0, str(ex))

        if args.id in [1,'1']:
            return_message = public.return_msg_gettext(False, 'Default value does not support modification')
            del return_message['status']
            return public.return_message(-1, 0, return_message['msg'])

        type_sql = public.M('wp_site_types')

        # 获取旧类型
        old_type = type_sql.where('id=?', (args.id,)).find()
        if not old_type:
            return_message = public.return_msg_gettext(False, 'Specified category does NOT exist!')
            del return_message['status']
            return public.return_message(-1, 0, return_message['msg'])
        type_sql.where('id=?', (args.id,)).delete()
        res = public.M("wordpress_onekey").where("site_type=?", (old_type['name'],)).update({
            'site_type': 'Default category',
        })
        return_message = public.return_msg_gettext(True, 'Category deleted!')
        del return_message['status']
        return public.return_message(0, 0, return_message['msg'])

    # 获取wp 安全模块配置
    def get_wp_security_info(self, get):
        from wp_toolkit import wp_security

        # 去安全模块获取配置信息
        try:
            result = {}
            security = wp_security().get_security_info(get)
            if security['status'] != 0:
                return public.return_message(-1, 0, security['message'])
            result = security['message']
        except Exception as e:
            result['firewall_status'] = 0
            result['firewall_count'] = 0

        # 更新防盗链状态
        get.name = get.site_name
        hotlink = self.GetSecurity(get)
        if hotlink['status'] != 0:
            return public.return_message(-1, 0, hotlink['message'])
        result['hotlink_status'] = 1 if hotlink['message']['status'] else 0

        # 获取病毒扫描状态
        get.path = get.path[:-1]
        scan_status = self.get_auth_scan_status(get)
        if scan_status['status'] != 0:
            return public.return_message(-1, 0, scan_status['message'])
        result['virus_scanning'] = 1 if scan_status['message']['result'] in ['True', 'true', True] else 0
        return public.return_message(0, 0, result)

    # 获取wp安全图标状态
    def get_wp_security_status(self, get):
        domain_list = public.S('sites').where_in('project_type', 'WP2').field('id,name,path').select()
        data = []
        for i in domain_list:
            info = public.to_dict_obj(i)
            info.site_name = info.name

            # try:
            #     res = self.get_wp_security_info(info)
            #     if not res["status"] == 0:
            #         data.append({i['name']: False})
            #         continue
            #
            #     if res['message']["file_status"] == 1 and res['message']["firewall_status"] == 1:
            #         data.append({i['name']: True})
            #         continue
            #
            #     data.append({i['name']: False})
            #
            # except Exception as e:
            #     data.append({i['name']: False})

            # 获取防火墙状态
            firewall_status = 0
            try:
                result = public.run_plugin('btwaf', 'get_site_config_byname',
                                           public.to_dict_obj({'siteName': info.site_name}))
                if result['open']:
                    firewall_status = 1
            except:
                pass

            # 新增获取病毒扫描状态
            scan_status = self.get_auth_scan_status(info)
            if scan_status['status'] != 0:
                return public.return_message(-1, 0, scan_status['message'])
            virus_scanning = 1 if scan_status['message']['result'] in ['True', 'true', True] else 0

            # 判断网站安全图标状态
            if virus_scanning == 1 and firewall_status == 1:
                data.append({i['name']: True})
            else:
                data.append({i['name']: False})

        return public.return_message(0, 0, data)

    # 开启WP 文件防护
    def open_wp_file_protection(self, get):
        from wp_toolkit import wp_security
        return wp_security().open_file_protection(get)

    # 关闭WP 文件防护
    def close_wp_file_protection(self, get):
        from wp_toolkit import wp_security
        return wp_security().close_file_protection(get)

    # 获取WP 文件防护
    def get_wp_file_info(self, get):
        from wp_toolkit import wp_security
        return wp_security().get_file_info(get)

    # 开启WP 防火墙防护
    def open_wp_firewall_protection(self, get):
        from wp_toolkit import wp_security
        return wp_security().open_firewall_protection(get)

    # 关闭WP 防火墙防护
    def close_wp_firewall_protection(self, get):
        from wp_toolkit import wp_security
        return wp_security().close_firewall_protection(get)

    def deploy_wp(self, get):
        import one_key_wp_v2 as one_key_wp
        return one_key_wp.one_key_wp().deploy_wp(get)

    def get_wp_username(self, get):
        import one_key_wp_v2 as one_key_wp
        return one_key_wp.one_key_wp().get_wp_username(get)

    def reset_wp_db(self, get):
        import one_key_wp_v2 as one_key_wp
        return one_key_wp.one_key_wp().reset_wp_db(get)

    # 备份WP站点
    def wp_backup(self, args: public.dict_obj):
        # 参数校验
        args.validate([
            public.Param('s_id').Require().Integer('>', 0),
            public.Param('bak_type').Require().Integer('>', 0),
        ])

        from wp_toolkit import wpbackup

        bak_obj = wpbackup(args.s_id)
        bak_type = int(args.bak_type)

        if bak_type == 1:
            ok, msg = bak_obj.backup_files()
        elif bak_type == 2:
            ok, msg = bak_obj.backup_database()
        elif bak_type == 3:
            ok, msg = bak_obj.backup_full()
        else:
            return public.fail_v2('Invalid backup type {}', (bak_type,))

        if not ok:
            return public.fail_v2(msg)

        return public.success_v2(msg)

    # 还原WP站点
    def wp_restore(self, args: public.dict_obj):
        # 参数校验
        args.validate([
            public.Param('bak_id').Require().Integer('>', 0),
        ])

        from wp_toolkit import wpbackup

        bak_id = int(args.bak_id)
        bak_obj = wpbackup(wpbackup.retrieve_site_id_with_bak_id(bak_id))
        ok, msg = bak_obj.restore_with_backup(bak_id)

        if not ok:
            return public.fail_v2(msg)

        return public.success_v2(msg)

    # WP备份列表
    def wp_backup_list(self, args: public.dict_obj):
        # 参数校验
        args.validate([
            public.Param('s_id').Require().Integer('>', 0),
            public.Param('p').Integer('>', 0),
            public.Param('limit').Integer('>', 0),
            public.Param('tojs').Regexp(r"^[\w\.\-]+$"),
            public.Param('result').Regexp(r"^[\d\,]+$"),
        ])

        from wp_toolkit import wpbackup

        bak_obj = wpbackup(args.s_id)

        return public.success_v2(bak_obj.backup_list(args))

    # 删除WP站点备份
    def wp_remove_backup(self, args: public.dict_obj):
        # 参数校验
        args.validate([
            public.Param('bak_id').Require().Integer('>', 0),
        ])

        from wp_toolkit import wpbackup

        bak_id = int(args.bak_id)
        bak_obj = wpbackup(wpbackup.retrieve_site_id_with_bak_id(bak_id))
        ok, msg = bak_obj.remove_backup(bak_id)

        if not ok:
            return public.fail_v2(msg)

        return public.success_v2(msg)

    # 从 [网站管理] 迁移到 [WP Toolkit]
    def wp_migrate_from_website_to_wptoolkit(self, args: public.dict_obj):
        sites_list = json.loads(args.get('sites_list','[]'))

        if not sites_list:
            return public.fail_v2('There are no websites that can be migrated')

        from wp_toolkit import wpmigration
        ok, msg = wpmigration.migrate_aap_from_website_to_wptoolkit(sites_list)

        if not ok:
            return public.fail_v2(msg)

        return public.success_v2(msg)

    # 查询可从 [网站管理] 迁移到 [WP Toolkit] 的网站列表
    def wp_can_migrate_from_website_to_wptoolkit(self, args: public.dict_obj):
        from wp_toolkit import wpmigration
        return public.success_v2(wpmigration.can_migrations_of_aap_website())

    # 从用户手动备份中创建WP站点
    def wp_create_with_manual_bak(self, args: public.dict_obj):
        from wp_toolkit import wpbackup
        args.backup_type = 'manual'
        ok, msg = wpbackup.wp_backup_deploy(args)

        if not ok:
            return public.fail_v2(msg)
        return public.success_v2(msg)

    # 从aapanel WP备份中创建WP站点
    def wp_create_with_aap_bak(self, args: public.dict_obj):
        from wp_toolkit import wpbackup

        args.backup_type = 'aapanel'
        ok, msg = wpbackup.wp_backup_deploy(args)

        if not ok:
            return public.fail_v2(msg)

        return public.success_v2(msg)

    # 从plesk/cpanel WP备份中创建WP站点
    def wp_create_with_plesk_or_cpanel_bak(self, args: public.dict_obj):
        from wp_toolkit import wpbackup
        args.backup_type = 'cpanel'
        ok, msg = wpbackup.wp_backup_deploy(args)

        if not ok:
            return public.fail_v2(msg)

        return public.success_v2(msg)

    # 克隆WP站点
    def wp_clone(self, args: public.dict_obj):
        # 参数校验
        args.validate([
            public.Param('s_id').Require().Integer('>', 0),
        ])

        from wp_toolkit import wpbackup

        ok, msg = wpbackup(args.s_id).clone(args)

        if not ok:
            return public.fail_v2(msg)

        return public.success_v2(msg)

    # Wordpress完整性校验
    def wp_integrity_check(self, args: public.dict_obj):
        # 参数校验
        args.validate([
            public.Param('s_id').Require().Integer('>', 0),
        ])

        from wp_toolkit import wpmgr

        ok, msg = wpmgr(args.s_id).integrity_check()

        if not ok:
            return public.fail_v2(msg)

        return public.success_v2(msg)

    # 重新下载并安装Wordpress（仅限框架文件，不会删除新文件）
    def wp_reinstall_files(self, args: public.dict_obj):
        # 参数校验
        args.validate([
            public.Param('s_id').Require().Integer('>', 0),
        ])

        from wp_toolkit import wpmgr

        ok, msg = wpmgr(args.s_id).reinstall_package()

        if not ok:
            return public.fail_v2(msg)

        return public.success_v2(msg)

    # 获取可安装的插件列表
    def wp_plugin_list(self, args: public.dict_obj):
        # 参数校验
        args.validate([
            public.Param('s_id').Integer('>', 0).Filter(int),
            public.Param('keyword'),
            public.Param('p').Integer('>', 0).Filter(int),
            public.Param('p_size').Integer('>', 0).Filter(int),
            public.Param('set_id').Integer('>', 0).Filter(int),
        ])

        from wp_toolkit import wpmgr

        if 's_id' in args:
            ok, msg = wpmgr(args.s_id).search_plugins(args.get('keyword', ''), args.get('p', 1), args.get('p_size', 20))
        else:
            ok, msg = wpmgr.query_plugins(args.get('keyword', ''), args.get('p', 1), args.get('p_size', 20), args.get('set_id', None))

        if not ok:
            return public.fail_v2(msg)

        return public.success_v2(msg)
    
    @staticmethod
    def get_tls_protocol(tls1_3: str = "TLSv1.3", is_apache=False):
        """获取使用的协议
        @author baozi <202-04-18>
        @param:
        @return
        """
        protocols = {
            "TLSv1": False,
            "TLSv1.1": True,
            "TLSv1.2": True,
            "TLSv1.3": False,
        }
        file_path = public.get_panel_path() + "/data/ssl_protocol.json"
        if os.path.exists(file_path):
            data = public.readFile(file_path)
            if data is not False:
                protocols = json.loads(data)
                if protocols["TLSv1.3"] and tls1_3 == "":
                    protocols["TLSv1.3"] = False
                if is_apache is False:
                    return " ".join([p for p, v in protocols.items() if v is True])
                else:
                    return " ".join(["-" + p for p, v in protocols.items() if v is False])
        else:
            if tls1_3 != "":
                protocols["TLSv1.3"] = True
            if is_apache is False:
                return " ".join([p for p, v in protocols.items() if v is True])
            else:
                return " ".join(["-" + p for p, v in protocols.items() if v is False])

    @staticmethod
    def get_ssl_protocol(get):
        """ 获取全局TLS版本
        @author baozi <202-04-18>
        @param:
        @return
        """
        protocols = {
            "TLSv1": False,
            "TLSv1.1": True,
            "TLSv1.2": True,
            "TLSv1.3": False,
        }
        file_path = public.get_panel_path() + "/data/ssl_protocol.json"
        if os.path.exists(file_path):
            data = public.readFile(file_path)
            if data is not False:
                protocols = json.loads(data)
                return protocols

        return protocols

    # 安装插件
    def wp_install_plugin(self, args: public.dict_obj):
        # 参数校验
        args.validate([
            public.Param('s_id').Require().Integer('>', 0),
            public.Param('slug').Require().SafePath(),
        ])

        from wp_toolkit import wpmgr
        wpmgr_obj = wpmgr(args.s_id)
        site_path = wpmgr_obj.retrieve_wp_root_path()
        is_maintenance = self.check_maintenance_mode(site_path)


        ok, msg = wpmgr_obj.install_plugin(args.slug)

        if is_maintenance:
            self.restore_maintenance_mode(site_path)

        if not ok:
            return public.fail_v2(msg)

        return public.success_v2(msg)

    # 已安装插件列表
    def wp_installed_plugins(self, args: public.dict_obj):
        # 参数校验
        args.validate([
            public.Param('s_id').Require().Integer('>', 0),
            public.Param('force_check_updates').Integer('in', [0, 1]),
        ])

        from wp_toolkit import wpmgr

        return public.success_v2(wpmgr(args.s_id).installed_plugins(bool(int(args.get('force_check_updates', 0)))))

    # 更新插件
    def wp_update_plugin(self, args: public.dict_obj):
        # 参数校验
        args.validate([
            public.Param('s_id').Require().Integer('>', 0),
            public.Param('plugin_file').Require().SafePath(),
        ])

        from wp_toolkit import wpmgr
        wpmgr_obj = wpmgr(args.s_id)

        # 校验是否开启维护模式
        site_path = wpmgr_obj.retrieve_wp_root_path()
        is_maintenance = self.check_maintenance_mode(site_path)

        ok, msg = wpmgr_obj.update_plugin(args.plugin_file)

        if is_maintenance:
            self.restore_maintenance_mode(site_path)

        if not ok:
            return public.fail_v2(msg)

        return public.success_v2('Success')

    # 开启/关闭插件自动更新
    def wp_set_plugin_auto_update(self, args: public.dict_obj):
        # 参数校验
        args.validate([
            public.Param('s_id').Require().Integer('>', 0),
            public.Param('plugin_file').Require().SafePath(),
            public.Param('enable').Require().Integer('in', [0, 1]),
        ])

        from wp_toolkit import wpmgr

        wpmgr_obj = wpmgr(args.s_id)

        # 校验是否开启维护模式
        site_path = wpmgr_obj.retrieve_wp_root_path()
        is_maintenance = self.check_maintenance_mode(site_path)

        if int(args.enable) == 1:
            fn = wpmgr_obj.enable_plugin_auto_update
        else:
            fn = wpmgr_obj.disable_plugin_auto_update

        ok, msg = fn(args.plugin_file)

        if is_maintenance:
            self.restore_maintenance_mode(site_path)

        if not ok:
            return public.fail_v2(msg)

        return public.success_v2('Success')

    # 激活/禁用插件
    def wp_set_plugin_status(self, args: public.dict_obj):
        # 参数校验
        args.validate([
            public.Param('s_id').Require().Integer('>', 0),
            public.Param('plugin_file').Require().SafePath(),
            public.Param('activate').Require().Integer('in', [0, 1]),
        ])

        from wp_toolkit import wpmgr

        wpmgr_obj = wpmgr(args.s_id)
        site_path = wpmgr_obj.retrieve_wp_root_path()
        is_maintenance = self.check_maintenance_mode(site_path)

        if int(args.activate) == 1:
            fn = wpmgr_obj.activate_plugins
            errmsg = public.lang("Activate plugin failed, please try again later.")
        else:
            fn = wpmgr_obj.deactivate_plugins
            errmsg = public.lang("Deactivate plugin failed, please try again later.")

        res = fn(args.plugin_file)

        if is_maintenance:
            self.restore_maintenance_mode(site_path)

        if not res:
            return public.fail_v2(errmsg)

        return public.success_v2('Success')

    # 卸载插件
    def wp_uninstall_plugin(self, args: public.dict_obj):
        # 参数校验
        args.validate([
            public.Param('s_id').Require().Integer('>', 0),
            public.Param('plugin_file').Require().SafePath(),
        ])

        from wp_toolkit import wpmgr
        wpmgr_obj = wpmgr(args.s_id)
        site_path = wpmgr_obj.retrieve_wp_root_path()
        is_maintenance = self.check_maintenance_mode(site_path)

        ok, msg = wpmgr_obj.uninstall_plugin(args.plugin_file)

        if is_maintenance:
            self.restore_maintenance_mode(site_path)

        # 处理手动上传的插件
        if 'Could not fully remove the plugin' in msg:
            file_path = args.get('plugin_file').split('/')[0]  # 插件
            plugins_path = os.path.join(site_path,'wp-content','plugins',file_path)
            # 删除插件
            if os.path.exists(plugins_path):
                shutil.rmtree(plugins_path, ignore_errors=True)
            return public.success_v2('Success')
        elif not ok:
            return public.fail_v2(msg)

        return public.success_v2('Success')

    # 获取可安装的主题列表
    def wp_theme_list(self, args: public.dict_obj):
        # 参数校验
        args.validate([
            public.Param('s_id').Integer('>', 0).Filter(int),
            public.Param('keyword'),
            public.Param('p').Integer('>', 0).Filter(int),
            public.Param('p_size').Integer('>', 0).Filter(int),
            public.Param('set_id').Integer('>', 0).Filter(int),
        ])

        from wp_toolkit import wpmgr

        if 's_id' in args:
            ok, msg = wpmgr(args.s_id).search_themes(args.get('keyword', ''), args.get('p', 1), args.get('p_size', 20))
        else:
            ok, msg = wpmgr.query_themes(args.get('keyword', ''), args.get('p', 1), args.get('p_size', 20), args.get('set_id', None))

        if not ok:
            return public.fail_v2(msg)

        return public.success_v2(msg)

    # 安装主题
    def wp_install_theme(self, args: public.dict_obj):
        # 参数校验
        args.validate([
            public.Param('s_id').Require().Integer('>', 0),
            public.Param('slug').Require(),
        ])

        from wp_toolkit import wpmgr
        wpmgr_obj = wpmgr(args.s_id)

        # 校验是否开启维护模式
        site_path = wpmgr_obj.retrieve_wp_root_path()
        is_maintenance = self.check_maintenance_mode(site_path)

        ok, msg = wpmgr_obj.install_theme(args.slug)

        if is_maintenance:
            self.restore_maintenance_mode(site_path)

        if not ok:
            return public.fail_v2(msg)

        return public.success_v2(msg)

    # 已安装主题列表
    def wp_installed_themes(self, args: public.dict_obj):
        # 参数校验
        args.validate([
            public.Param('s_id').Require().Integer('>', 0),
            public.Param('force_check_updates').Integer('in', [0, 1]),
        ])

        from wp_toolkit import wpmgr

        return public.success_v2(wpmgr(args.s_id).installed_themes(bool(int(args.get('force_check_updates', 0)))))

    # 更新主题
    def wp_update_theme(self, args: public.dict_obj):
        # 参数校验
        args.validate([
            public.Param('s_id').Require().Integer('>', 0),
            public.Param('stylesheet').Require(),
        ])

        from wp_toolkit import wpmgr

        wpmgr_obj = wpmgr(args.s_id)

        # 校验是否开启维护模式
        site_path = wpmgr_obj.retrieve_wp_root_path()
        is_maintenance = self.check_maintenance_mode(site_path)

        ok, msg = wpmgr(args.s_id).update_theme(args.stylesheet)

        if is_maintenance:
            self.restore_maintenance_mode(site_path)

        if not ok:
            return public.fail_v2(msg)

        return public.success_v2('Success')

    # 开启/关闭主题自动更新
    def wp_set_theme_auto_update(self, args: public.dict_obj):
        # 参数校验
        args.validate([
            public.Param('s_id').Require().Integer('>', 0),
            public.Param('stylesheet').Require(),
            public.Param('enable').Require().Integer('in', [0, 1]),
        ])

        from wp_toolkit import wpmgr

        wpmgr_obj = wpmgr(args.s_id)

        # 校验是否开启维护模式
        site_path = wpmgr_obj.retrieve_wp_root_path()
        is_maintenance = self.check_maintenance_mode(site_path)

        if int(args.enable) == 1:
            fn = wpmgr_obj.enable_theme_auto_update
        else:
            fn = wpmgr_obj.disable_theme_auto_update

        ok, msg = fn(args.stylesheet)

        if is_maintenance:
            self.restore_maintenance_mode(site_path)

        if not ok:
            return public.fail_v2(msg)

        return public.success_v2('Success')

    # 切换主题
    def wp_switch_theme(self, args: public.dict_obj):
        # 参数校验
        args.validate([
            public.Param('s_id').Require().Integer('>', 0),
            public.Param('stylesheet').Require(),
        ])

        from wp_toolkit import wpmgr
        wpmgr_obj = wpmgr(args.s_id)
        # 校验是否开启维护模式
        site_path = wpmgr_obj.retrieve_wp_root_path()
        is_maintenance = self.check_maintenance_mode(site_path)

        res = wpmgr_obj.switch_theme(args.stylesheet)

        if is_maintenance:
            self.restore_maintenance_mode(site_path)

        if not res:
            return public.fail_v2('Switch theme failed, please try again later.')

        return public.success_v2('Success')

    # 卸载主题
    def wp_uninstall_theme(self, args: public.dict_obj):
        # 参数校验
        args.validate([
            public.Param('s_id').Require().Integer('>', 0),
            public.Param('stylesheet').Require(),
        ])

        from wp_toolkit import wpmgr
        wpmgr_obj = wpmgr(args.s_id)
        # 校验是否开启维护模式
        site_path = wpmgr_obj.retrieve_wp_root_path()
        is_maintenance = self.check_maintenance_mode(site_path)

        ok, msg = wpmgr_obj.uninstall_theme(args.stylesheet)

        if is_maintenance:
            self.restore_maintenance_mode(site_path)

        # 处理手动上传的主题
        if 'Could not fully remove the theme' in msg:
            file_path = args.get('stylesheet')
            plugins_path = os.path.join(site_path,'wp-content','themes',file_path)
            # 删除主题
            if os.path.exists(plugins_path):
                shutil.rmtree(plugins_path, ignore_errors=True)
            return public.success_v2('Success')
        elif not ok:
            return public.fail_v2(msg)

        return public.success_v2('Success')

    # 获取所有WP站点
    def wp_all_sites(self, args: public.dict_obj):
        from wp_toolkit import wpmgr
        return public.success_v2(wpmgr.all_sites())

    # 获取WP整合包列表
    def wp_set_list(self, args: public.dict_obj):
        # 校验参数
        args.validate([
            public.Param('keyword'),
            public.Param('p').Filter(int),
            public.Param('p_size').Filter(int),
        ])

        from wp_toolkit import wp_sets
        return public.success_v2(wp_sets().fetch_list(args.get('keyword', ''), args.get('p', 1), args.get('p_size', 20)))

    # 新建WP整合包
    def wp_create_set(self, args: public.dict_obj):
        # 校验参数
        args.validate([
            public.Param('name').Require(),
        ])

        from wp_toolkit import wp_sets

        if wp_sets().create_set(args.name) < 1:
            raise public.HintException(public.lang("The theme package already exists!"))

        return public.success_v2('Success')

    # 删除WP整合包
    def wp_remove_set(self, args: public.dict_obj):
        # 校验参数
        args.validate([
            public.Param('set_id').Require().Regexp(r'^\d+(?:,\d+)*$'),
        ])

        from wp_toolkit import wp_sets

        if not wp_sets().remove_set(list(map(lambda x: int(x), str(args.set_id).split(',')))):
            raise public.HintException(public.lang("Failed to remove Sets"))

        return public.success_v2('Success')
    
    # 获取WP整合包中的插件列表or主题列表
    def wp_get_items_from_set(self, args: public.dict_obj):
        # 校验参数
        args.validate([
            public.Param('set_id').Require().Integer('>', 0).Filter(int),
            public.Param('type').Require().Integer('in', [1, 2]).Filter(int),
        ])

        from wp_toolkit import wp_sets

        return public.success_v2(wp_sets().get_items(args.set_id, args.type))

    # 添加插件or主题到WP整合包中
    def wp_add_items_to_set(self, args: public.dict_obj):
        # 校验参数
        args.validate([
            public.Param('set_id').Require().Integer('>', 0).Filter(int),
            public.Param('items').Require().Array(),
            public.Param('type').Require().Integer('in', [1, 2]).Filter(int),
        ])

        from wp_toolkit import wp_sets

        typ = int(args.type)

        # 添加插件
        if typ == 1:
            ok, msg = wp_sets().add_plugins(int(args.set_id), json.loads(args.items))

        # 添加主题
        elif typ == 2:
            ok, msg = wp_sets().add_themes(int(args.set_id), json.loads(args.items))

        # 无效类型
        else:
            raise public.HintException(public.lang("Invalid type of Set items"))

        if not ok:
            raise public.HintException(msg)

        return public.success_v2('Success')

    # 将插件or主题从WP整合包中移除
    def wp_remove_items_from_set(self, args: public.dict_obj):
        # 校验参数
        args.validate([
            public.Param('item_ids').Require().Regexp(r'^\d+(?:,\d+)*$'),
            public.Param('type').Require().Integer('in', [1, 2]).Filter(int),
        ])

        from wp_toolkit import wp_sets

        item_ids = list(map(lambda x: int(x), str(args.item_ids).split(',')))
        typ = int(args.type)

        # 删除插件
        if typ == 1:
            ok = wp_sets().remove_plugins(item_ids)

        # 删除主题
        elif typ == 2:
            ok = wp_sets().remove_themes(item_ids)

        # 无效类型
        else:
            raise public.HintException(public.lang("Invalid type of Set items"))

        if not ok:
            raise public.HintException(public.lang("Failed to remove items from Set"))

        return public.success_v2('Success')

    # 上传插件或主题到WP整合包
    def wp_manual_upload(self, args: public.dict_obj):
        # 校验参数
        args.validate([
            public.Param('set_id').Require().Integer('>', 0),
            public.Param('path').String(),
            public.Param('type').String(),
        ])

        from wp_toolkit import wp_sets

        ok, msg = wp_sets().manual_upload(args)

        if not ok:
            raise public.HintException(msg)

        return public.success_v2(msg)

    # 更改WP整合包中插件or主题的激活状态
    def wp_update_item_state_with_set(self, args: public.dict_obj):
        # 校验参数
        args.validate([
            public.Param('item_ids').Require().Regexp(r'^\d+(?:,\d+)*$'),
            public.Param('state').Require().Integer('in', [0, 1]),
            public.Param('type').Require().Integer('in', [1, 2]).Filter(int),
        ])

        from wp_toolkit import wp_sets

        item_ids = list(map(lambda x: int(x), str(args.item_ids).split(',')))
        state = int(args.state)
        typ = int(args.type)

        # 删除插件
        if typ == 1:
            ok = wp_sets().update_plugins_state(state, item_ids)

        # 删除主题
        elif typ == 2:
            ok = wp_sets().update_theme_state(state, item_ids[0])

        # 无效类型
        else:
            raise public.HintException(public.lang("Invalid type of Set items"))

        if not ok:
            raise public.HintException(public.lang("Failed to change items state from Set"))

        return public.success_v2('Success')

    # 通过WP整合包安装插件&主题
    def wp_install_with_set(self, args: public.dict_obj):
        # 校验参数
        args.validate([
            public.Param('set_id').Require().Integer('>', 0),
            public.Param('site_ids').Require().Regexp(r'^\d+(?:,\d+)*$'),
        ])

        from wp_toolkit import wp_sets

        set_id = int(args.set_id)
        site_ids = list(map(lambda x: int(x), str(args.site_ids).split(',')))

        ok, msg = wp_sets().install(set_id, site_ids)

        if not ok:
            raise public.HintException(msg)

        return public.success_v2(msg)

    # WP工具页
    def set_wp_tool(self, args: public.dict_obj):
        # 校验参数
        args.validate([
            public.Param('set_id').Require().Integer('>', 0),
        ])

        from wp_toolkit import wpmgr

        ok, msg = wpmgr(args.set_id).set_wp_tool(args)

        if not ok:
            raise public.HintException(msg)

        return public.success_v2(msg)

    # 获取工具页数据
    def get_wp_tool(self, args: public.dict_obj):
        # 校验参数
        args.validate([
            public.Param('set_id').Require().Integer('>', 0),
        ])
        from wp_toolkit import wpmgr

        ok, msg = wpmgr(args.set_id).get_wp_tool()

        if not ok:
            raise public.HintException(msg)

        return public.success_v2(msg)

    # 获取wp调试模式debug日志
    def get_wp_debug_log(self, args: public.dict_obj):
        # 校验参数
        args.validate([
            public.Param('set_id').Require().Integer('>', 0),
            public.Param('lines')
        ])
        from wp_toolkit import wpmgr

        ok, msg = wpmgr(args.set_id).get_wp_debug_log(args.get('lines', 100))

        if not ok:
            raise public.HintException(msg)
        return public.success_v2(msg)

    # 数据复制
    def wp_copy_data(self,args: public.dict_obj):
        # 校验参数
        args.validate([
            public.Param('target_id').Require().Integer('>', 0),
            public.Param('source_id').Require().Integer('>', 0),
            public.Param('is_backup'),
            public.Param('cp_data_tables'),
            public.Param('data_tables'),
            public.Param('cp_files'),
        ])
        from wp_toolkit import wpmigration

        ok, msg = wpmigration().thread_copy_data(args)
        if not ok:
            raise public.HintException(msg)

        return public.success_v2('Replicating Success')

    # 获取wp网站数据（简化版，不使用getData通用接口）
    def get_wp_sites(self, args: public.dict_obj):
        wp_sites = []
        try:
            wp_sites = public.M('sites').where('project_type=?', ('WP2',)).field('id,name,path').select()
        except Exception as e:
            pass

        return public.success_v2(wp_sites)

    # 获取源网站数据表
    def get_source_tables(self, args: public.dict_obj):
        args.validate([
            public.Param('set_id').Require().Integer('>', 0),
        ])
        try:
            from wp_toolkit import wpmgr

            source_conn, _ = wpmgr(args.set_id)._get_db_connection()
            res = []

            with source_conn.cursor() as source_cursor:
                source_cursor.execute("""
                                      SELECT table_name
                                      FROM information_schema.tables
                                      WHERE table_schema = DATABASE()
                                      ORDER BY table_name
                                      """)
                tables = source_cursor.fetchall()

                if tables:
                    for row in tables:
                        table_name = row.get('table_name') or row.get('TABLE_NAME')
                        if table_name:
                            res.append(table_name)

            return public.success_v2(res)
        except Exception as e:
            raise public.HintException(public.lang('Database connection failed, please check the database status!'))

    # 获取wp复制进度
    def get_wp_progress(self, args: public.dict_obj):
        """
            兼容备份部署与数据复制
        """
        from pathlib import Path
        import threading
        try:
            # 进度类型区分
            if args.get('progress_type', '') == 'backup_deploy':
                task_status = Path('/tmp') / 'wp_aapanel_deploy.log'
                lock_file = Path('/tmp') / 'wp_aapanel_deploy.lock'
            elif args.get('progress_type', '') == 'wp_copy':
                task_status = Path("/tmp") / "wp_copy_status.log"  # 进度文件
                lock_file = Path("/tmp") / "wp_copy_lock.lock"  # 锁文件
            else:
                raise public.HintException('Progress type error')

            # 检查进度文件是否存在，不存在直接返回status:1
            if not task_status.exists():
                return public.success_v2({'status': 1})

            # 检查锁文件是否存在
            if lock_file.exists():
                try:
                    # 读取锁文件中的线程ID
                    with open(lock_file, 'r') as f:
                        thread_id_str = f.read().strip()

                    if not thread_id_str:
                        # 线程ID为空，清理锁文件和进度文件
                        lock_file.unlink(missing_ok=True)
                        task_status.unlink()
                        return public.success_v2({'status': 1})

                    # 转换线程ID为整数
                    thread_id = int(thread_id_str)

                    # 检查线程是否存在且活跃
                    thread_exists = False
                    for thread in threading.enumerate():
                        if hasattr(thread, '_ident') and thread._ident == thread_id:
                            thread_exists = True
                            break

                    if not thread_exists:
                        # 线程不存在，清理文件
                        lock_file.unlink(missing_ok=True)
                        task_status.unlink()
                        return public.success_v2({'status': 1})

                except (ValueError, IOError) as e:
                    # 处理线程ID转换错误或文件读取错误，清理异常状态
                    lock_file.unlink(missing_ok=True)
                    if os.path.exists(task_status):
                        os.remove(task_status)
                    return public.success_v2({'status': 1})

            # 线程存在且正常，读取并返回进度信息
            with open(task_status, 'r') as f:
                res = json.loads(f.read())
                return public.success_v2(res)
        except Exception as e:
            raise public.HintException('Failed to retrieve replication progress:' + str(e))

    # *********** WP Toolkit --End-- *************


    # *********** WP Toolkit Remote --Begin-- *************

    # TODO 新增远程WP站点
    def wp_remote_add(self, args: public.dict_obj):
        # 校验参数
        args.validate([
            public.Param('login_url').Require().Url(),
            public.Param('username').Require(),
            public.Param('password').Require(),
        ])

        from wp_toolkit import wpmgr_remote
        wpmgr_remote().add(args.login_url, args.username, args.password)

        return public.success_v2('Success')

    def wp_remote_add_manually(self, args: public.dict_obj):
        # 校验参数
        args.validate([
            public.Param('login_url').Require().Url(),
            public.Param('security_key').Require(),
            public.Param('security_token').Require(),
        ])

        from wp_toolkit import wpmgr_remote
        wpmgr_remote().add_manually(args.login_url, args.security_key, args.security_token)

        return public.success_v2('Success')

    def wp_remote_remove(self, args: public.dict_obj):
        # 校验参数
        args.validate([
            public.Param('remote_id').Require().Integer('>', 0),
        ])

        from wp_toolkit import wpmgr_remote
        if not wpmgr_remote(args.remote_id).remove():
            raise public.HintException(public.lang('Remove wordpress remote site failed'))

        return public.success_v2('Success')

    def wp_remote_sites(self, args: public.dict_obj):
        # 校验参数
        args.validate([
            public.Param('keyword'),
            public.Param('p').Filter(int),
            public.Param('p_size').Filter(int),
        ])

        from wp_toolkit import wpmgr_remote
        return public.success_v2(wpmgr_remote().list(args.get('keyword', ''), args.get('p', 1), args.get('p_size', 20)))

    def wp_add_onekey_database(self, args: public.dict_obj):
        args.validate([
            public.Param('s_id').Require(),
            public.Param('d_id').Require(),
            public.Param('prefix').Require(),
            public.Param('user_name').Require(),
            public.Param('admin_password').Require(),
        ])
        from one_key_wp_v2 import one_key_wp
        db_info = {
            's_id': args.s_id,
            'd_id': args.d_id,
            'prefix': args.prefix,
            'user_name': args.user_name,
            'admin_password': args.admin_password,
        }
        one_key_wp().write_db(**db_info)
        return public.success_v2('Success')

    # *********** WP Toolkit Remote --End-- *************

    @staticmethod
    def test_domains_api(get):
        try:
            domains = json.loads(get.domains.strip())
        except (json.JSONDecodeError, AttributeError, KeyError):
            return public.return_message(-1, 0, public.lang("参数错误"))
        try:
            # from panel_dns_api_v2 import DnsMager
            public.print_log("开始测试域名解析---- {}")
            # public.print_log("开始测试域名解析---- {}".format(domains[0]))

            return DnsMager().test_domains_api(domains)
        except:
            pass
        public.return_message(0, 0, "")

    def site_rname(self, get):
        try:
            if not (hasattr(get, "id") and hasattr(get, "rname")):
                return public.return_message(-1, 0, public.lang("parameter error"))
            id = get.id
            rname = get.rname
            data = public.M('sites').where("id=?", (id,)).select()
            if not data:
                return public.return_message(-1, 0, public.lang("The site does not exist!"))
            data = data[0]
            name = data['rname'] if 'rname' in data.keys() and data.get('rname', '') else data['name']
            if 'rname' not in data.keys():
                public.M('sites').execute("ALTER TABLE 'sites' ADD 'rname' text DEFAULT ''", ())
            public.M('sites').where('id=?', data['id']).update({'rname': rname})
            # public.write_log_gettext('Site manager', 'Website [{}] renamed: [{}]'.format(name, rname))
            return public.return_message(0, 0, public.lang("Website [{}] renamed: [{}]", name, rname))
        except:
            return public.return_message(-1, 0, traceback.format_exc())


    # Wordpress 漏洞扫描
    def wordpress_vulnerabilities_scan(self, get):
        from wp_toolkit import wordpress_scan
        if 'path' not in get:public.return_message(0, 0, public.lang("Parameter error"))
        return public.return_message(0,0,wordpress_scan.wordpress_scan().scan(get.path))
    def wordpress_vulnerabilities_time(self, get):
        from wp_toolkit import wordpress_scan
        return public.return_message(0,0,wordpress_scan.wordpress_scan().get_vlu_time())

    def ignore_vuln(self,get):
        from wp_toolkit import wordpress_scan
        return wordpress_scan.wordpress_scan().ignore_vuln(get)

    def get_ignore_vuln(self,get):
        from wp_toolkit import wordpress_scan
        return wordpress_scan.wordpress_scan().get_ignore_vuln(get)

    def set_auth_scan(self,get):
        if 'path' not in get: public.return_message(0, 0, public.lang("Parameter error"))
        from wp_toolkit import wordpress_scan
        return wordpress_scan.wordpress_scan().set_auth_scan(get.path)

    def get_auth_scan_status(self,get):
        if 'path' not in get: public.return_message(0, 0, public.lang("Parameter error"))
        from wp_toolkit import wordpress_scan
        return wordpress_scan.wordpress_scan().get_auth_scan_status(get.path)


    def set_status(self, get):
        try:
            get.validate([
                Param('status').Integer().Require(),
                Param('name').String().Require(),
            ], [
                public.validate.trim_filter(),
            ])
        except Exception as e:
            public.print_log("error, %s" % e)
            return public.fail_v2("parameter error %s" % e)

        import sys
        sys.path.append("..")  # 添加上一级目录到系统路径
        from script.restart_services import SERVICES_MAP
        if get.name not in SERVICES_MAP.keys():
            return public.fail_v2("service not support now")
        import crontab
        p = crontab.crontab()
        try:
            task_name = f'[Do not delete] {get.name.capitalize()} Daemon'
            data = {"id": public.M('crontab').where("name=?", (task_name,)).getField('id')}
            return p.set_cron_status(public.to_dict_obj(data))
        except Exception as e:
            public.print_log("error, %s" % e)
            return public.fail_v2("set status error %s" % e)

    def is_nginx_http3(self):
        if getattr(self, "_is_nginx_http3", None) is None:
            _is_nginx_http3 = public.ExecShell("nginx -V 2>&1| grep 'http_v3_module'")[0] != ''
            setattr(self, "_is_nginx_http3", _is_nginx_http3)
        return self._is_nginx_http3

    def set_restart_task(self, get):
        """
        设置重启任务开关
        """
        try:
            get.validate([
                Param('status').Integer().Require(),
                Param('name').String().Require(),
            ], [
                public.validate.trim_filter(),
            ])
        except Exception as e:
            public.print_log("error, %s" % e)
            return public.fail_v2("parameter error %s" % e)
        sys.path.append("..")  # 添加上一级目录到系统路径
        from script.restart_services import SERVICES_MAP, DaemonManager
        if get.name not in SERVICES_MAP.keys():
            return public.fail_v2("service not support now")
        try:
            if int(get.status) == 1:
                DaemonManager.add_daemon(get.name)
            elif int(get.status) == 0:
                DaemonManager.remove_daemon(get.name)
            else:
                raise Exception("status error")
        except Exception as e:
            return public.fail_v2("Settings fail!" + str(e))

        return public.success_v2("success")

    def get_restart_task(self, get):
        """
        获取重启任务状态
        """
        try:
            get.validate([
                Param('name').String().Require(),
            ], [
                public.validate.trim_filter(),
            ])
        except Exception as e:
            public.print_log("error, %s" % e)
            return public.fail_v2("parameter error %s" % e)
        sys.path.append("..")  # 添加上一级目录到系统路径
        from script.restart_services import DaemonManager
        try:
            daemon_info = DaemonManager.safe_read()
            if get.name in daemon_info:
                status = {"status": 1}
            else:
                status = {"status": 0}
            return public.success_v2(status)
        except Exception as e:
            return public.fail_v2("get fail" + str(e))

    # ======================面板漏洞扫描 start======================== #
    def get_cron_scanin_info(self, get):
        """获取漏洞扫描定时任务信息"""
        if "/www/server/panel" not in sys.path:
            sys.path.insert(0, '/www/server/panel')

        from mod.base.push_mod import TaskConfig
        res = TaskConfig().get_by_keyword("vulnerability_scanning", "vulnerability_scanning")
        if not res:
            return public.return_message(0,0,{"cycle": 1, "channel": "", "status": 0})
        else:
            return public.return_message(0,0,{
                "cycle": res['task_data']["cycle"],
                "channel": ",".join(res['sender']),
                "status": int(res['status'])
            })


    @classmethod
    def set_push_task(self,status: bool, day: int, sender: list):
        """构造告警推送模板"""
        push_data = {
            "template_id": "122",
            "task_data": {
                "status": status,
                "sender": sender,
                "task_data": {
                    "cycle": day,
                }
            }
        }
        from mod.base.push_mod.manager import PushManager
        return PushManager().set_task_conf_data(push_data)


    def set_cron_scanin_info(self, get):
        """设置漏洞扫描定时任务
        @param get: 请求参数对象
        @return: dict 设置结果
        """
        try:
            # 参数处理部分
            try:
                status = bool(int(get.get("status", 0)))
            except (ValueError, TypeError):
                status = False

            channel = get.get("channel", "")
            if not isinstance(channel, str):
                channel = str(channel)

            try:
                # 先尝试转换为浮点数，再向下取整
                day_float = float(get.get("day", 0))
                day = int(day_float)  # 浮点数向下取整
            except (ValueError, TypeError):
                day = 1

            # 确保参数在有效范围内
            if day < 0:
                day = 1

            try:

                # 处理channel参数
                if isinstance(channel, str):
                    channel_list = channel.split(",") if channel else []
                elif isinstance(channel, list):
                    channel_list = channel
                else:
                    channel_list = []

                # 设置推送任务
                res = self.set_push_task(status, day, channel_list)
                if not res:
                    return public.return_message(0,0, 'Setting successful')
                else:
                    return public.return_message(-1,0, res)
            except ImportError as e:
                return public.return_message(-1,0, f"No relevant module found, please confirm system integrity,{e}")
            except Exception as e:
                return public.return_message(-1,0, "Error setting task: {}".format(str(e)))

        except Exception as e:
            # 捕获所有可能的异常，确保API不会崩溃
            return public.return_message(-1,0, 'Setting failed: {}'.format(str(e)))

    def get_Scan(self, get):
        try:
            res = self.startScan(get)
            return res
        except Exception as e:
            print(e)
        return {}


    def startScan(self, get):
        '''
        @name 开始扫描
        @author lkq<2022-3-30>
        @param get
        '''
        self.__cachekey = public.Md5('vulnerability_scanning' + time.strftime('%Y-%m-%d'))
        self.__config_file = '/www/server/panel/config/vulnerability_scanning.json'
        result22 = []
        time_info = int(time.time())
        webInfo = self.getWebInfo(None)
        config = self.get_config()
        for web in webInfo:
            for cms in config:
                data = cms
                if 'cms_name' in web:
                    if web['cms_name'] != cms['cms_name']:
                        if not web['cms_name'] in cms['cms_list']: continue
                if self.getCmsType(web, data):
                    if not 'cms' in web:
                        web['cms'] = []
                        web['cms'].append(cms)
                    else:
                        web['cms'].append(cms)
                else:
                    if not 'cms' in web:
                        web['cms'] = []
            if not 'is_vufix' in web:
                web['is_vufix'] = False
        for i in webInfo:
            if i['is_vufix']:
                result22.append(i)
        result = {"info": [], "time": time_info}
        loophole_num = sum([len(i['cms']) for i in result22])
        result['loophole_num'] = loophole_num
        result['site_num'] = len(webInfo)
        return result

    def getWebInfo(self, get):
        '''
        @name 获取网站的信息
        @author lkq<2022-3-30>
        @param get
        '''
        return public.M('sites').where('project_type=?', ('PHP')).select()

    def get_config(self):
        '''
        @name 获取配置文件
        @author lkq<2022-3-23>
        @return
        '''
        result = [
            {"cms_list": [], "dangerous": "2", "cms_name": "XunruiCMS",
             "ps": "The XunruiCMS version is too low",
             "name": "The XunruiCMS version is too low",
             "determine": ["dayrui/My/Config/Version.php"],
             "version": {"type": "file", "file": "dayrui/My/Config/Version.php",
                         "regular": r"version.+'(\d+.\d+.\d+)'", "regular_len": 0,
                         "vul_version": "3.2.0~4.5.4", "ver_type": "range"},
             "repair_file": {"type": "file",
                             "file": [{"file": "dayrui/My/Config/Version.php",
                                       "regular": ''' if (preg_match('/(php|jsp|asp|exe|sh|cmd|vb|vbs|phtml)/i', $value)) {'''}]},
             },
            {"cms_list": [], "dangerous": "3", "cms_name": "pbootcms",
             "ps": "pbootcms 3.0.0~3.0.4 There are multiple high-severity vulnerabilities CNVD-2020-48981,CNVD-2020-48677,CNVD-2020-48469,CNVD-2020-57593,CNVD-2020-56006,CNVD-2021-00794,CNVD-2021-30081,CNVD-2021-30113,CNVD-2021-32163",
             "name": "pbootcms 2.0.0~2.0.8 There are multiple high-severity vulnerabilities CNVD-2020-48981,CNVD-2020-48677,CNVD-2020-48469,CNVD-2020-57593,CNVD-2020-56006,CNVD-2021-00794,CNVD-2021-30081,CNVD-2021-30113,CNVD-2021-32163",
             "determine": ["apps/common/version.php", "core/basic/Config.php",
                           "apps/admin/view/default/js/mylayui.js",
                           "apps/api/controller/ContentController.php"],
             "version": {"type": "file", "file": "apps/common/version.php",
                         "regular": r"app_version.+'(\d+.\d+.\d+)'", "regular_len": 0,
                         "vul_version": "3.0.0~3.0.4", "ver_type": "range"},
             "repair_file": {"type": "file",
                             "file": [{"file": "apps/admin/controller/system/ConfigController.php",
                                       "regular": ''' if (preg_match('/(php|jsp|asp|exe|sh|cmd|vb|vbs|phtml)/i', $value)) {'''}]},
             }
            , {"cms_list": [], "dangerous": "3", "cms_name": "pbootcms",
               "ps": "pbootcms 2.0.0~2.0.8 There are multiple high-severity vulnerabilities CNVD-2020-04104,CNVD-2020-13536,CNVD-2020-24744,CNVD-2020-32198,CNVD-2020-32180,CNVD-2020-32177,CNVD-2020-31495,CNVD-2019-43060",
               "name": "pbootcms 2.0.0~2.0.8 There are multiple high-severity vulnerabilities CNVD-2020-04104,CNVD-2020-13536,CNVD-2020-24744,CNVD-2020-32198,CNVD-2020-32180,CNVD-2020-32177,CNVD-2020-31495,CNVD-2019-43060",
               "determine": ["apps/common/version.php", "core/basic/Config.php",
                             "apps/admin/view/default/js/mylayui.js",
                             "apps/api/controller/ContentController.php"],
               "version": {"type": "file", "file": "apps/common/version.php",
                           "regular": r"app_version.+'(\d+.\d+.\d+)'", "regular_len": 0,
                           "vul_version": "2.0.0~2.0.8", "ver_type": "range"},
               "repair_file": {"type": "file",
                               "file": [{"file": "apps/home/controller/ParserController.php",
                                         "regular": r''' if (preg_match('/(\$_GET\[)|(\$_POST\[)|(\$_REQUEST\[)|(\$_COOKIE\[)|(\$_SESSION\[)|(file_put_contents)|(file_get_contents)|(fwrite)|(phpinfo)|(base64)|(`)|(shell_exec)|(eval)|(assert)|(system)|(exec)|(passthru)|(print_r)|(urldecode)|(chr)|(include)|(request)|(__FILE__)|(__DIR__)|(copy)/i', $matches[1][$i]))'''}]},
               }
            ,
            {"cms_list": [], "dangerous": "3", "cms_name": "pbootcms",
             "ps": "pbootcms 1.3.0~1.3.8 There are multiple high-severity vulnerabilities CNVD-2018-26355,CNVD-2018-24253,CNVD-2018-26938,CNVD-2019-14855,CNVD-2019-27743,CNVD-2020-23841",
             "name": "pbootcms 1.3.0~1.3.8 There are multiple high-severity vulnerabilities CNVD-2018-26355,CNVD-2018-24253,CNVD-2018-26938,CNVD-2019-14855,CNVD-2019-27743,CNVD-2020-23841",
             "determine": ["apps/common/version.php", "core/basic/Config.php",
                           "apps/admin/view/default/js/mylayui.js",
                           "apps/api/controller/ContentController.php"],
             "version": {"type": "file", "file": "apps/common/version.php",
                         "regular": r"app_version.+'(\d+.\d+.\d+)'", "regular_len": 0,
                         "vul_version": "1.3.0~1.3.8", "ver_type": "range"},
             "repair_file": {"type": "file",
                             "file": [{"file": "apps/admin/controller/system/ConfigController.php",
                                       "regular": r'''$config = preg_replace('/(\'' . $key . '\'([\s]+)?=>([\s]+)?)[\w\'\"\s,]+,/', '${1}\'' . $value . '\',', $config);'''}]},
             }
            , {"cms_list": [], "dangerous": "3", "cms_name": "pbootcms",
               "ps": "pbootcms 1.2.0~1.2.2 There are multiple high-severity vulnerabilities CNVD-2018-21503,CNVD-2018-19945,CNVD-2018-22854,CNVD-2018-22142,CNVD-2018-26780,CNVD-2018-24845",
               "name": "pbootcms 1.0.1~1.2.2 There are multiple high-severity vulnerabilities CNVD-2018-21503,CNVD-2018-19945,CNVD-2018-22854,CNVD-2018-22142,CNVD-2018-26780,CNVD-2018-24845",
               "determine": ["apps/common/version.php", "core/basic/Config.php",
                             "apps/admin/view/default/js/mylayui.js",
                             "apps/api/controller/ContentController.php"],
               "version": {"type": "file", "file": "apps/common/version.php",
                           "regular": r"app_version.+'(\d+.\d+.\d+)'", "regular_len": 0,
                           "vul_version": ["1.2.0", "1.2.1", "1.2.2"], "ver_type": "list"},
               "repair_file": {"type": "file",
                               "file": [{"file": "apps/admin/controller/system/DatabaseController.php",
                                         "regular": r'''if ($value && ! preg_match('/(^|[\s]+)(drop|truncate|set)[\s]+/i', $value)) {'''}]},
               },
            {"cms_list": [], "dangerous": "3", "cms_name": "pbootcms",
             "ps": "pbootcms 1.1.9  an SQL injection vulnerability exists CNVD-2018-18069",
             "name": "pbootcms 1.1.9  an SQL injection vulnerability exists CNVD-2018-18069",
             "determine": ["apps/common/version.php", "core/basic/Config.php",
                           "apps/admin/view/default/js/mylayui.js",
                           "apps/api/controller/ContentController.php"],
             "version": {"type": "file", "file": "apps/common/version.php",
                         "regular": r"app_version.+'(\d+.\d+.\d+)'", "regular_len": 0,
                         "vul_version": ["1.1.9"], "ver_type": "list"},
             "repair_file": {"type": "file",
                             "file": [{"file": "core/function/handle.php",
                                       "regular": '''if (Config::get('url_type') == 2 && strrpos($indexfile, 'index.php') !== false)'''}]},
             },
            {"cms_list": [], "dangerous": "4", "cms_name": "pbootcms",
             "ps": "pbootcms 1.1.6~1.1.8 There are foreground code execution vulnerabilities and multiple SQL injection vulnerabilities CNVD-2018-17412,CNVD-2018-17741,CNVD-2018-17747,CNVD-2018-17750,CNVD-2018-17751,CNVD-2018-17752,CNVD-2018-17753,CNVD-2018-17754",
             "name": "pbootcms 1.1.6~1.1.8  There are foreground code execution vulnerabilities and multiple SQL injection vulnerabilities CNVD-2018-17412,CNVD-2018-17741,CNVD-2018-17747,CNVD-2018-17750,CNVD-2018-17751,CNVD-2018-17752,CNVD-2018-17753,CNVD-2018-17754",
             "determine": ["apps/common/version.php", "core/basic/Config.php",
                           "apps/admin/view/default/js/mylayui.js",
                           "apps/api/controller/ContentController.php"],
             "version": {"type": "file", "file": "apps/common/version.php",
                         "regular": r"app_version.+'(\d+.\d+.\d+)'", "regular_len": 0,
                         "vul_version": ["1.1.6", "1.1.7", "1.1.8"], "ver_type": "list"},
             "repair_file": {"type": "file",
                             "file": [{"file": "core/function/handle.php",
                                       "regular": '''if (is_array($string)) { 
                foreach ($string as $key => $value) {
                    $string[$key] = decode_slashes($value);
                }'''}]},
             },
            {"cms_list": [], "dangerous": "3", "cms_name": "pbootcms",
             "ps": "pbootcms 1.1.4 an SQL injection vulnerability exists CNVD-2018-13335,CNVD-2018-13336",
             "name": "pbootcms 1.1.4 an SQL injection vulnerability exists CNVD-2018-13335,CNVD-2018-13336",
             "determine": ["apps/common/version.php", "core/basic/Config.php",
                           "apps/admin/view/default/js/mylayui.js",
                           "apps/api/controller/ContentController.php"],
             "version": {"type": "file", "file": "apps/common/version.php",
                         "regular": r"app_version.+'(\d+.\d+.\d+)'", "regular_len": 0,
                         "vul_version": ["1.1.4"], "ver_type": "list"},
             "repair_file": {"type": "file",
                             "file": [{"file": "core/extend/ueditor/php/controller.php",
                                       "regular": '''if (! ini_get('session.auto_start') && ! isset($_SESSION)'''}]},
             }
            , {"cms_list": [], "dangerous": "3", "cms_name": "maccms10",
               "ps": "maccms10 <=2022.1000.3025 ssrf and xss vulnerabilities exist",
               "name": "maccms10 <=2022.1000.3025 ssrf and xss vulnerabilities exist",
               "determine": ["application/extra/version.php", "application/api/controller/Wechat.php",
                             "thinkphp/library/think/Route.php",
                             "application/admin/controller/Upload.php"],
               "version": {"type": "file", "file": "application/extra/version.php",
                           "regular": r"code.+'(\d+.\d+.\d+)'", "regular_len": 0,
                           "vul_version": ["2022.1000.3025", "2022.1000.3005", "2022.1000.3024", "2022.1000.3020",
                                           "2022.1000.3023",
                                           "2022.1000.3002", "2022.1000.1099", "2021.1000.1081"], "ver_type": "list"},
               "repair_file": {"type": "file",
                               "file": [{"file": "application/common/model/Actor.php",
                                         "regular": '''$data[$filter_field] = mac_filter_xss($data[$filter_field]);'''}]},
               }
            ,
            {"cms_list": [], "dangerous": "3", "cms_name": "maccms10",
             "ps": "maccms10 <=2022.1000.3024 There are vulnerabilities in which any user in the foreground logs in, the background session verification is bypassed, any file is written in the background, and any file is deleted",
             "name": "maccms10 <=2022.1000.3024 There are vulnerabilities in which any user in the foreground logs in, the background session verification is bypassed, any file is written in the background, and any file is deleted",
             "determine": ["application/extra/version.php", "application/api/controller/Wechat.php",
                           "thinkphp/library/think/Route.php",
                           "application/admin/controller/Upload.php"],
             "version": {"type": "file", "file": "application/extra/version.php",
                         "regular": r"code.+'(\d+.\d+.\d+)'", "regular_len": 0,
                         "vul_version": ["2022.1000.3005", "2022.1000.3024", "2022.1000.3020", "2022.1000.3023",
                                         "2022.1000.3002", "2022.1000.1099", "2021.1000.1081"], "ver_type": "list"},
             "repair_file": {"type": "file",
                             "file": [{"file": "application/common/model/Annex.php",
                                       "regular": '''if (stripos($v['annex_file'], '../') !== false)'''}]},
             }
            , {"cms_list": [], "dangerous": "3", "cms_name": "eyoucms",
               "ps": "eyoucms 1.5.5~1.5.7 There are multiple security vulnerabilities",
               "name": "eyoucms 1.5.1~1.5.4 There are multiple security vulnerabilities",
               "determine": ["data/conf/version.txt", "application/api/controller/Uploadify.php",
                             "application/extra/extra_cache_key.php",
                             "application/admin/controller/Uploadify.php"],
               "version": {"type": "file", "file": "data/conf/version.txt",
                           "regular": r"(\d+.\d+.\d+)", "regular_len": 0,
                           "vul_version": "1.5.5~1.5.7", "ver_type": "range"},
               "repair_file": {"type": "file",
                               "file": [{"file": "application/common.php",
                                         "regular": '''$login_errnum_key = 'adminlogin_'.md5('login_errnum_'.$admin_info['user_name']);'''}]},
               }
            ,
            {"cms_list": [], "dangerous": "4", "cms_name": "eyoucms",
             "ps": "eyoucms 1.5.1~1.5.4 There are multiple high-risk security vulnerabilities,CNVD-2021-82431,CNVD-2021-82429,CNVD-2021-72772,CNVD-2021-51838,CNVD-2021-51836,CNVD-2021-41520,CNVD-2021-24745,,CNVD-2021-26007,CNVD-2021-26099,CNVD-2021-41520",
             "name": "eyoucms 1.5.1~1.5.4 There are multiple high-risk security vulnerabilities ,CNVD-2021-82431,CNVD-2021-82429,CNVD-2021-72772,CNVD-2021-51838,CNVD-2021-51836,CNVD-2021-41520,CNVD-2021-24745,,CNVD-2021-26007,CNVD-2021-26099,CNVD-2021-41520",
             "determine": ["data/conf/version.txt", "application/api/controller/Uploadify.php",
                           "application/extra/extra_cache_key.php",
                           "application/admin/controller/Uploadify.php"],
             "version": {"type": "file", "file": "data/conf/version.txt",
                         "regular": r"(\d+.\d+.\d+)", "regular_len": 0,
                         "vul_version": "1.5.1~1.5.4", "ver_type": "range"},
             "repair_file": {"type": "file",
                             "file": [{"file": "application/common.php",
                                       "regular": '''$citysite_db->where(['domain'=>$s_arr[0]])->cache(true, EYOUCMS_CACHE_TIME, 'citysite')->count()'''}]},
             },
            {"cms_list": [], "dangerous": "4", "cms_name": "eyoucms",
             "ps": "eyoucms 1.4.7 There are multiple high-risk security vulnerabilities ,CNVD-2020-46317,CNVD-2020-49065,CNVD-2020-44394,CNVD-2020-44392,CNVD-2020-44391,CNVD-2020-47671,CNVD-2020-50721",
             "name": "eyoucms 1.4.7 There are multiple high-risk security vulnerabilities ,CNVD-2020-46317,CNVD-2020-49065,CNVD-2020-44394,CNVD-2020-44392,CNVD-2020-44391,CNVD-2020-47671,CNVD-2020-50721",
             "determine": ["data/conf/version.txt", "application/api/controller/Uploadify.php",
                           "application/extra/extra_cache_key.php",
                           "application/admin/controller/Uploadify.php"],
             "version": {"type": "file", "file": "data/conf/version.txt",
                         "regular": r"(\d+.\d+.\d+)", "regular_len": 0,
                         "vul_version": "1.4.7~1.4.7", "ver_type": "range"},
             "repair_file": {"type": "file",
                             "file": [{"file": "application/common.php",
                                       "regular": '''function GetTagIndexRanking($limit = 5, $field = 'id, tag')'''}]},
             },
            {"cms_list": [], "dangerous": "4", "cms_name": "eyoucms",
             "ps": "eyoucms 1.4.6 There are multiple high-risk security vulnerabilities ,CNVD-2020-44116,CNVD-2020-32622,CNVD-2020-28132,CNVD-2020-28083,CNVD-2020-28064,CNVD-2020-33104",
             "name": "eyoucms 1.4.6 There are multiple high-risk security vulnerabilities ,CNVD-2020-44116,CNVD-2020-32622,CNVD-2020-28132,CNVD-2020-28083,CNVD-2020-28064,CNVD-2020-33104",
             "determine": ["data/conf/version.txt", "application/api/controller/Uploadify.php",
                           "application/extra/extra_cache_key.php",
                           "application/admin/controller/Uploadify.php"],
             "version": {"type": "file", "file": "data/conf/version.txt",
                         "regular": r"(\d+.\d+.\d+)", "regular_len": 0,
                         "vul_version": "1.4.6~1.4.6", "ver_type": "range"},
             "repair_file": {"type": "file",
                             "file": [{"file": "application/common.php",
                                       "regular": r'''preg_replace('#^(/[/\w]+)?(/uploads/|/public/static/)#i'''}]},
             }
            , {"cms_list": [], "dangerous": "4", "cms_name": "eyoucms",
               "ps": "eyoucms 1.3.9~1.4.4  There are multiple security vulnerabilities CNVD-2020-02271,CNVD-2020-02824,CNVD-2020-18735,CNVD-2020-18677,CNVD-2020-23229,CNVD-2020-23805,CNVD-2020-23820",
               "name": "eyoucms 1.3.9~1.4.4  There are multiple security vulnerabilities CNVD-2020-02271,CNVD-2020-02824,CNVD-2020-18735,CNVD-2020-18677,CNVD-2020-23229,CNVD-2020-23805,CNVD-2020-23820",
               "determine": ["data/conf/version.txt", "application/api/controller/Uploadify.php",
                             "application/extra/extra_cache_key.php",
                             "application/admin/controller/Uploadify.php"],
               "version": {"type": "file", "file": "data/conf/version.txt",
                           "regular": r"(\d+.\d+.\d+)", "regular_len": 0,
                           "vul_version": "1.3.9~1.4.4", "ver_type": "range"},
               "repair_file": {"type": "file",
                               "file": [{"file": "application/common.php",
                                         "regular": '''$TimingTaskRow = model('Weapp')->getWeappList('TimingTask');'''}]},
               },
            {"cms_list": [], "dangerous": "4", "cms_name": "eyoucms", "ps": "eyoucms 1.4.1 There is a command execution vulnerability",
             "name": "eyoucms 1.4.1 There is a command execution vulnerability",
             "determine": ["data/conf/version.txt", "application/api/controller/Uploadify.php",
                           "application/extra/extra_cache_key.php",
                           "application/admin/controller/Uploadify.php"],
             "version": {"type": "file", "file": "data/conf/version.txt",
                         "regular": r"(\d+.\d+.\d+)", "regular_len": 0,
                         "vul_version": "1.4.1~1.4.1", "ver_type": "range"},
             "repair_file": {"type": "file",
                             "file": [{"file": "application/route.php",
                                       "regular": '''$weapp_route_file = 'plugins/route.php';'''}]},
             },
            {"cms_list": [], "dangerous": "3", "cms_name": "eyoucms", "ps": "eyoucms<=1.3.8 There are SQL injection and plug-in upload vulnerabilities",
             "name": "eyoucms<=1.3.8 There are SQL injection and plug-in upload vulnerabilities",
             "determine": ["data/conf/version.txt", "application/api/controller/Uploadify.php",
                           "application/extra/extra_cache_key.php",
                           "application/admin/controller/Uploadify.php"],
             "version": {"type": "file", "file": "data/conf/version.txt",
                         "regular": r"(\d+.\d+.\d+)", "regular_len": 0,
                         "vul_version": "1.0.0~1.3.8", "ver_type": "range"},
             "repair_file": {"type": "file",
                             "file": [{"file": "core/library/think/template/taglib/Eyou.php",
                                       "regular": '''$notypeid  = !empty($tag['notypeid']) ? $tag['notypeid'] : '';'''}]},
             },
            {"cms_list": [], "dangerous": "3", "cms_name": "eyoucms", "ps": "eyoucms<=1.3.4 There is a background file upload vulnerability",
             "name": "eyoucms<=1.3.4 There is a background file upload vulnerability",
             "determine": ["data/conf/version.txt", "application/api/controller/Uploadify.php",
                           "application/extra/extra_cache_key.php",
                           "application/admin/controller/Uploadify.php"],
             "version": {"type": "file", "file": "data/conf/version.txt",
                         "regular": r"(\d+.\d+.\d+)", "regular_len": 0,
                         "vul_version": "1.0.0~1.3.4", "ver_type": "range"},
             "repair_file": {"type": "file",
                             "file": [{"file": "application/common.php",
                                       "regular": '''include_once EXTEND_PATH."function.php";'''}]},
             },
            {"cms_list": [], "dangerous": "3", "cms_name": "eyoucms", "ps": "eyoucms 1.0 There is a vulnerability in uploading arbitrary files",
             "name": "eyoucms 1.0 There is a vulnerability in uploading arbitrary files",
             "determine": ["data/conf/version.txt", "application/api/controller/Uploadify.php",
                           "application/extra/extra_cache_key.php",
                           "application/admin/controller/Uploadify.php"],
             "version": {"type": "file", "file": "data/conf/version.txt",
                         "regular": r"(\d+.\d+.\d+)", "regular_len": 0,
                         "vul_version": "1.0.0~1.1.0", "ver_type": "range"},
             "repair_file": {"type": "file",
                             "file": [{"file": "application/api/controller/Uploadify.php",
                                       "regular": '''not api '''}]},
             },
            {"cms_list": [], "dangerous": "2", "cms_name": "Marine CMS", "ps": "Marine CMSVersion too low",
             "name": "Marine CMSVersion too low",
             "determine": ["data/admin/ver.txt", "include/common.php", "include/main.class.php",
                           "detail/index.php"],
             "version": {"type": "file", "file": "data/admin/ver.txt",
                         "regular": r"(\d+.\d+?|\d+)", "regular_len": 0,
                         "vul_version": ["6.28", "6.54", "7.2", "8.4", "8.5", "8.6", "8.7", "8.8", "8.9", "9", "9.1",
                                         "9.2", "9.3", "9.4", "9.5", "9.6", "9.7", "9.8", "9.9", "9.91", "9.92", "9.93",
                                         "9.94", "9.96", "9.97", "9.98", "9.99", "10", "10.1", "10.2", "10.3", "10.4",
                                         "10.5", "10.6", "10.7", "10.8", "10.9", "11", "11.1", "11.2", "11.3", "11.4",
                                         "11.5"], "ver_type": "list"},
             "repair_file": {"type": "version", "file": []},
             },
            {"cms_list": [], "dangerous": "3", "cms_name": "Marine CMS", "ps": "Marine CMS <=9.95 Existence of front-end RCE",
             "name": "Marine CMS <=9.95 Existence of front-end RCE",
             "determine": ["data/admin/ver.txt", "include/common.php", "include/main.class.php",
                           "detail/index.php"],
             "version": {"type": "file", "file": "data/admin/ver.txt",
                         "regular": r"(\d+.\d+?|\d+)", "regular_len": 0,
                         "vul_version": ["6.28", "6.54", "7.2", "8.4", "8.5", "8.6", "8.7", "8.8", "8.9", "9", "9.1",
                                         "9.2", "9.3", "9.4", "9.5", "9.6", "9.7", "9.8", "9.9", "9.91", "9.92", "9.93",
                                         "9.94"], "ver_type": "list"},
             "repair_file": {"type": "file",
                             "file": [{"file": "include/common.php",
                                       "regular": ''''$jpurl='//'.$_SERVER['SERVER_NAME']'''}]},
             },
            {"cms_list": [], "dangerous": "3", "cms_name": "ThinkCMF", "ps": "ThinkCMF CVE-2019-6713漏洞",
             "name": "ThinkCMF CVE-2019-6713",
             "determine": ["public/index.php", "app/admin/hooks.php", "app/admin/controller/NavMenuController.php",
                           "simplewind/cmf/hooks.php"],
             "version": {"type": "file", "file": "public/index.php",
                         "regular": r"THINKCMF_VERSION.+'(\d+.\d+.\d+)'", "regular_len": 0,
                         "vul_version": ["5.0.190111", "5.0.181231", "5.0.181212", "5.0.180901", "5.0.180626",
                                         "5.0.180525", "5.0.180508"], "ver_type": "list"},
             "repair_file": {"type": "file",
                             "file": [{"file": "app/admin/validate/RouteValidate.php",
                                       "regular": '''protected function checkUrl($value, $rule, $data)'''}]},
             },
            {"cms_list": [], "dangerous": "3", "cms_name": "ThinkCMF", "ps": "ThinkCMF templateFile  Remote code execution vulnerability",
             "name": "ThinkCMF templateFile Remote code execution vulnerability",
             "determine": ["simplewind/Core/ThinkPHP.php", "index.php",
                           "data/conf/db.php", "application/Admin/Controller/NavcatController.class.php",
                           "application/Comment/Controller/WidgetController.class.php"],
             "version": {"type": "file", "file": "index.php",
                         "regular": r"THINKCMF_VERSION.+(\d+.\d+.\d+)'", "regular_len": 0,
                         "vul_version": "1.6.0~2.2.2", "ver_type": "range"},
             "repair_file": {"type": "file",
                             "file": [{"file": "application/Comment/Controller/WidgetController.class.php",
                                       "regular": '''protected function display('''}]},
             },
            {"cms_list": [], "dangerous": "3", "cms_name": "zfaka", "ps": "zfaka an SQL injection vulnerability exists ", "name": "zfaka an SQL injection vulnerability exists ",
             "determine": ["application/init.php", "application/function/F_Network.php",
                           "application/controllers/Error.php", "application/modules/Admin/controllers/Profiles.php"],
             "version": {"type": "file", "file": "application/init.php",
                         "regular": r"VERSION.+'(\d+.\d+.\d+)'", "regular_len": 0,
                         "vul_version": "1.0.0~1.4.4", "ver_type": "range"},
             "repair_file": {"type": "file", "file": [{"file": "application/function/F_Network.php",
                                                       "regular": '''if(filter_var($ip, FILTER_VALIDATE_IP, FILTER_FLAG_IPV4'''}]},
             }
            ,
            {"cms_list": [], "dangerous": "3", "cms_name": "dedecms", "ps": "dedecms 20210719  Security Update",
             "name": "dedecms 20210719 Security Update",
             "determine": ["data/admin/ver.txt", "data/common.inc.php",
                           "dede/shops_operations_userinfo.php", "member/edit_space_info.php"],
             "version": {"type": "file", "file": "data/admin/ver.txt",
                         "regular": r"(\d+)", "regular_len": 0,
                         "vul_version": ["20180109"], "ver_type": "list"},
             "repair_file": {"type": "file", "file": [{"file": "include/dedemodule.class.php",
                                                       "regular": r'''if(preg_match("#[^a-z]+(eval|assert)[\s]*[(]#i"'''}]},
             }
            ,
            {"cms_list": [], "dangerous": "3", "cms_name": "dedecms", "ps": "dedecms 20220125 Security Update",
             "name": "dedecms 20220125 Security Update",
             "determine": ["data/admin/ver.txt", "data/common.inc.php",
                           "dede/shops_operations_userinfo.php", "member/edit_space_info.php"],
             "version": {"type": "file", "file": "data/admin/ver.txt",
                         "regular": r"(\d+)", "regular_len": 0,
                         "vul_version": ["20180109", "20220325", "20210201", "20210806"], "ver_type": "list"},
             "repair_file": {"type": "file", "file": [{"file": "include/downmix.inc.php",
                                                       "regular": '''上海卓卓网络科技有限公司'''}]},
             }
            ,
            {"cms_list": [], "dangerous": "3", "cms_name": "dedecms", "ps": "dedecms 20220218 Security Update",
             "name": "dedecms 20220218 Security Update",
             "determine": ["data/admin/ver.txt", "data/common.inc.php",
                           "dede/shops_operations_userinfo.php", "member/edit_space_info.php"],
             "version": {"type": "file", "file": "data/admin/ver.txt",
                         "regular": r"(\d+)", "regular_len": 0,
                         "vul_version": ["20180109", "20220325", "20210201", "20210806"], "ver_type": "list"},
             "repair_file": {"type": "file", "file": [{"file": "dede/file_manage_control.php",
                                                       "regular": '''phpinfo,eval,assert,exec,passthru,shell_exec,system,proc_open,popen'''}]},
             }
            , {"cms_list": [], "dangerous": "3", "cms_name": "dedecms", "ps": "dedecms 20220310 Security Update",
               "name": "dedecms 20220310 Security Update",
               "determine": ["data/admin/ver.txt", "data/common.inc.php",
                             "dede/shops_operations_userinfo.php", "member/edit_space_info.php"],
               "version": {"type": "file", "file": "data/admin/ver.txt",
                           "regular": r"(\d+)", "regular_len": 0,
                           "vul_version": ["20180109", "20220325", "20210201", "20210806"], "ver_type": "list"},
               "repair_file": {"type": "file", "file": [{"file": "dede/file_manage_control.php",
                                                         "regular": '''phpinfo,eval,assert,exec,passthru,shell_exec,system,proc_open,popen'''}]},
               },
            {"cms_list": [], "dangerous": "3", "cms_name": "dedecms", "ps": "dedecms 20220325 Security Update",
             "name": "dedecms 20220325 Security Update",
             "determine": ["data/admin/ver.txt", "data/common.inc.php",
                           "dede/shops_operations_userinfo.php", "member/edit_space_info.php"],
             "version": {"type": "file", "file": "data/admin/ver.txt",
                         "regular": r"(\d+)", "regular_len": 0,
                         "vul_version": ["20180109", "20220325", "20210201", "20210806"], "ver_type": "list"},
             "repair_file": {"type": "file", "file": [{"file": "plus/mytag_js.php",
                                                       "regular": '''phpinfo,eval,assert,exec,passthru,shell_exec,system,proc_open,popen'''}]},
             },
            {"cms_list": [], "dangerous": "2", "cms_name": "dedecms", "ps": "dedecms The member registration function has been enabled",
             "name": "dedecms The member registration function has been enabled",
             "determine": ["data/admin/ver.txt", "data/common.inc.php",
                           "dede/shops_operations_userinfo.php", "member/edit_space_info.php"],
             "version": {"type": "file", "file": "data/admin/ver.txt",
                         "regular": r"(\d+)", "regular_len": 0,
                         "vul_version": ["20180109", "20220325", "20210201", "20210806"], "ver_type": "list"},
             "repair_file": {"type": "phpshell", "file": [{"file": "member/get_user_cfg_mb_open.php",
                                                           "phptext": '''<?php require_once(dirname(__FILE__).'/../include/common.inc.php');echo 'start'.$cfg_mb_open.'end';?>''',
                                                           "regular": r'''start(\w)end''', "reulst_type": "str",
                                                           "result": "startYend"}]},
             }
            , {"cms_list": [], "dangerous": "3", "cms_name": "MetInfo", "ps": "MetInfo 7.5.0 an SQL injection vulnerability exists ",
               "name": "MetInfo7.5.0 an SQL injection vulnerability exists ",
               "determine": ["cache/config/config_metinfo.php", "app/system/entrance.php",
                             "app/system/databack/admin/index.class.php", "cache/config/app_config_metinfo.php"],
               "version": {"type": "file", "file": "cache/config/config_metinfo.php",
                           "regular": r"value.+'(\d+.\d+.\d+)'", "vul_version": "7.5.0~7.5.0", "ver_type": "range"},
               "repair_file": {"type": "version", "file": []},
               },
            {"cms_list": [], "dangerous": "3", "cms_name": "MetInfo", "ps": "MetInfo 7.3.0 an SQL injection vulnerability exists ",
             "name": "MetInfo 7.3.0 an SQL injection vulnerability exists ",
             "determine": ["app/system/entrance.php", "app/system/admin/admin/index.class.php",
                           "app/system/admin/admin/templates/admin_add.php"],
             "version": {"type": "file", "file": "app/system/entrance.php",
                         "regular": r"SYS_VER.+'(\d+.\d+.\d+)'", "vul_version": "7.3.0~7.3.0", "ver_type": "range"},
             "repair_file": {"type": "version", "file": []},
             },
            {"cms_list": [], "dangerous": "3", "cms_name": "MetInfo", "ps": "MetInfo 7.2.0 an SQL injection vulnerability exists ",
             "name": "MetInfo 7.2.0 an SQL injection vulnerability exists",
             "determine": ["app/system/entrance.php", "app/system/admin/admin/index.class.php",
                           "app/system/admin/admin/templates/admin_add.php"],
             "version": {"type": "file", "file": "app/system/entrance.php",
                         "regular": r"SYS_VER.+'(\d+.\d+.\d+)'", "vul_version": "7.2.0~7.2.0", "ver_type": "range"},
             "repair_file": {"type": "version", "file": []},
             },
            {"cms_list": [], "dangerous": "3", "cms_name": "MetInfo", "ps": "MetInfo 7.1.0 There are file upload vulnerabilities, SQL injection vulnerabilities, and XSS vulnerabilities present",
             "name": "MetInfo 7.1.0 There are file upload vulnerabilities, SQL injection vulnerabilities, and XSS vulnerabilities present",
             "determine": ["app/system/entrance.php", "app/system/admin/admin/index.class.php",
                           "app/system/admin/admin/templates/admin_add.php"],
             "version": {"type": "file", "file": "app/system/entrance.php",
                         "regular": r"SYS_VER.+'(\d+.\d+.\d+)'", "vul_version": "7.1.0~7.1.0", "ver_type": "range"},
             "repair_file": {"type": "version", "file": []},
             },
            {"cms_list": [], "dangerous": "3", "cms_name": "MetInfo", "ps": "MetInfo 7.0.0  an SQL injection vulnerability exists ",
             "name": "MetInfo7.0.0 an SQL injection vulnerability exists ",
             "determine": ["app/system/entrance.php", "app/system/admin/admin/index.class.php",
                           "app/system/admin/admin/templates/admin_add.php"],
             "version": {"type": "file", "file": "app/system/entrance.php",
                         "regular": r"SYS_VER.+'(\d+.\d+.\d+)'", "vul_version": "7.0.0~7.0.0", "ver_type": "range"},
             "repair_file": {"type": "version", "file": []},
             },
            {"cms_list": [], "dangerous": "3", "cms_name": "MetInfo", "ps": "MetInfo 6.1.2 an SQL injection vulnerability exists ",
             "name": "MetInfo 6.1.2 an SQL injection vulnerability exists ",
             "determine": ["app/system/entrance.php", "app/system/admin/admin/templates/admin_add.php"],
             "version": {"type": "file", "file": "app/system/entrance.php",
                         "regular": r"SYS_VER.+'(\d+.\d+.\d+)'", "vul_version": "6.1.2~6.1.2", "ver_type": "range"},
             "repair_file": {"type": "version", "file": []},
             },
            {"cms_list": [], "dangerous": "3", "cms_name": "MetInfo", "ps": "MetInfo 6.1.1 There is a known backend permission that can exploit the webshell vulnerability",
             "name": "MetInfo 6.1.1 There is a known backend permission that can exploit the webshell vulnerability",
             "determine": ["app/system/entrance.php", "app/system/admin/admin/templates/admin_add.php"],
             "version": {"type": "file", "file": "app/system/entrance.php",
                         "regular": r"SYS_VER.+'(\d+.\d+.\d+)'", "vul_version": "6.1.1~6.1.1", "ver_type": "range"},
             "repair_file": {"type": "version", "file": []},
             },
            {"cms_list": [], "dangerous": "2", "cms_name": "emlog", "ps": "EMlog version is too low. It is recommended to upgrade to Pro version",
             "name": "EMlog version is too low. It is recommended to upgrade to Pro version",
             "determine": ["include/lib/option.php", "admin/views/template_install.php",
                           "include/lib/checkcode.php", "include/controller/author_controller.php"],
             "version": {"type": "file", "file": "include/lib/option.php",
                         "regular": r"EMLOG_VERSION.+'(\d+.\d+.\d+)'", "vul_version": "5.3.1~6.0.0",
                         "ver_type": "range"},
             "repair_file": {"type": "version", "file": []},
             },
            {"cms_list": [], "dangerous": "1", "cms_name": "Empire CMS", "ps": "EmpireCMs7.0  Backend XSS vulnerability ",
             "name": "EmpireCMs7.0 Backend XSS vulnerability ",
             "determine": ["e/class/EmpireCMS_version.php", "e/search/index.php",
                           "e/member/EditInfo/index.php", "e/ViewImg/index.html"],
             "version": {"type": "file", "file": "e/class/EmpireCMS_version.php",
                         "regular": r"EmpireCMS_VERSION.+'(\d+.\d+)'", "vul_version": "7.0~7.0", "ver_type": "range"},
             "repair_file": {"type": "version", "file": []},
             },
            {"cms_list": [], "dangerous": "2", "cms_name": "Empire CMS", "ps": "EmpireCMs6.0~7.5 Backend code execution",
             "name": "EmpireCMs6.0~7.5 Backend code execution",
             "determine": ["e/class/EmpireCMS_version.php", "e/search/index.php",
                           "e/member/EditInfo/index.php", "e/ViewImg/index.html"],
             "version": {"type": "file", "file": "e/class/EmpireCMS_version.php",
                         "regular": r"EmpireCMS_VERSION.+'(\d+.\d+)'", "vul_version": "6.0~7.5", "ver_type": "range"},
             "repair_file": {"type": "version", "file": []},
             },
            {"cms_list": [], "dangerous": "2", "cms_name": "Empire CMS", "ps": "EmpireCMs6.0~7.5 Backend import model code execution",
             "name": "EmpireCMs6.0~7.5 Backend import model code execution",
             "determine": ["e/class/EmpireCMS_version.php", "e/search/index.php",
                           "e/member/EditInfo/index.php", "e/ViewImg/index.html"],
             "version": {"type": "file", "file": "e/class/EmpireCMS_version.php",
                         "regular": r"EmpireCMS_VERSION.+'(\d+.\d+)'", "vul_version": "6.0~7.5", "ver_type": "range"},
             "repair_file": {"type": "version", "file": []},
             },
            {"cms_list": [], "dangerous": "2", "cms_name": "discuz", "ps": "Discuz utility Component external access",
             "name": "Discuz utility Component external access",
             "determine": ["uc_client/client.php", "uc_server/lib/uccode.class.php",
                           "uc_server/model/version.php", "source/discuz_version.php"],
             "version": {"type": "single_file", "file": "utility/convert/index.php",
                         "regular": r"DISCUZ_RELEASE.+'(\d+)'", "regular_len": 0,
                         "vul_version": ["1"], "ver_type": "list"},
             "repair_file": {"type": "single_file", "file": [{"file": "utility/convert/index.php",
                                                              "regular": '''$source = getgpc('source') ? getgpc('source') : getgpc('s');'''}]},
             },
            {"cms_list": [], "dangerous": "2", "cms_name": "discuz", "ps": "Discuz Email authentication entrance CSRF and time limit can bypass vulnerabilities",
             "name": "Discuz Email authentication entrance CSRF and time limit can bypass vulnerabilities",
             "determine": ["uc_client/client.php", "uc_server/lib/uccode.class.php",
                           "uc_server/model/version.php", "source/discuz_version.php"],
             "version": {"type": "file", "file": "source/discuz_version.php",
                         "regular": r"DISCUZ_RELEASE.+'(\d+)'", "regular_len": 0,
                         "vul_version": ["20210816",
                                         "20210630", "20210520", "20210320", "20210119", "20200818", "20191201",
                                         "20190917"], "ver_type": "list"},
             "repair_file": {"type": "file", "file": [{"file": "source/admincp/admincp_setting.php",
                                                       "regular": '''showsetting('setting_permissions_mailinterval', 'settingnew[mailinterval]', $setting['mailinterval'], 'text');'''}]},
             },
            {"cms_list": [], "dangerous": "3", "cms_name": "discuz", "ps": "Discuz Error injection SQL", "name": "Discuz Error injection SQL",
             "determine": ["uc_client/client.php", "uc_server/lib/uccode.class.php",
                           "uc_server/model/version.php", "source/discuz_version.php"],
             "version": {"type": "file", "file": "source/discuz_version.php",
                         "regular": r"DISCUZ_RELEASE.+'(\d+)'", "regular_len": 0,
                         "vul_version": ["20211124", "20211022", "20210926", "20210917", "20210816",
                                         "20210630", "20210520", "20210320", "20210119", "20200818", "20191201",
                                         "20190917"], "ver_type": "list"},
             "repair_file": {"type": "file", "file": [
                 {"file": "api/uc.php",
                  "regular": r'''if($len > 22 || $len < 3 || preg_match("/\s+|^c:\\con\\con|[%,\*\"\s\<\>\&\(\)']/is", $get['newusername']))'''}]},
             }
            , {"cms_list": [], "dangerous": "3", "cms_name": "discuz", "ps": "Discuz Backup and recovery function execution arbitrary SQL vulnerability",
               "name": "Discuz Backup and recovery function execution arbitrary SQL vulnerability",
               "determine": ["uc_client/client.php", "uc_server/lib/uccode.class.php", "uc_server/model/version.php",
                             "source/discuz_version.php"],
               "version": {"type": "file", "file": "source/discuz_version.php", "regular": r"DISCUZ_RELEASE.+'(\d+)'",
                           "regular_len": 0,
                           "vul_version": ["20211231", "20211124", "20211022", "20210926", "20210917", "20210816",
                                           "20210630", "20210520", "20210320", "20210119", "20200818", "20191201",
                                           "20190917"], "ver_type": "list"},
               "repair_file": {"type": "file", "file": [
                   {"file": "api/db/dbbak.php",
                    "regular": r'''if(!preg_match('/^backup_(\d+)_\w+$/', $get['sqlpath']) || !preg_match('/^\d+_\w+\-(\d+).sql$/', $get['dumpfile']))'''}]},
               },
            {"cms_list": ["maccms10"], "dangerous": "4", "cms_name": "Thinkphp", "ps": "thinkphp5.0.X loophole",
             "name": "Thinkphp5.X code execution",
             "determine": ["thinkphp/base.php", "thinkphp/library/think/App.php", "thinkphp/library/think/Request.php"],
             "version": {"type": "file", "file": "thinkphp/base.php", "regular": r"THINK_VERSION.+(\d+.\d+.\d+)",
                         "vul_version": "5.0.0~5.0.24", "ver_type": "range"},
             "repair_file": {"type": "file", "file": [
                 {"file": "thinkphp/library/think/App.php", "regular": r'''(!preg_match('/^[A-Za-z](\w|\.)*$/'''},
                 {"file": "thinkphp/library/think/Request.php",
                  "regular": '''if (in_array($method, ['GET', 'POST', 'DELETE', 'PUT', 'PATCH']))'''}]},
             },
            {"cms_list": ["maccms10"], "dangerous": "3", "cms_name": "Thinkphp", "ps": "Thinkphp5.0.15 sql injection ",
             "name": "Thinkphp5.0.15 sql injection ",
             "determine": ["thinkphp/base.php", "thinkphp/library/think/App.php",
                           "thinkphp/library/think/Request.php"],
             "version": {"type": "file", "file": "thinkphp/base.php", "regular": r"THINK_VERSION.+(\d+.\d+.\d+)",
                         "vul_version": "5.0.13~5.0.15", "ver_type": "range"},
             "repair_file": {"type": "file", "file": [
                 {"file": "thinkphp/library/think/db/Builder.php",
                  "regular": '''if ($key == $val[1]) {
                                $result[$item] = $this->parseKey($val[1]) . '+' . floatval($val[2]);
                            }'''}]},
             },
            {"cms_list": ["maccms10"], "dangerous": "3", "cms_name": "Thinkphp", "ps": "Thinkphp5.0.10 sql injection ",
             "name": "Thinkphp5.0.10 sql injection ",
             "determine": ["thinkphp/base.php", "thinkphp/library/think/App.php",
                           "thinkphp/library/think/Request.php"],
             "version": {"type": "file", "file": "thinkphp/base.php", "regular": r"THINK_VERSION.+(\d+.\d+.\d+)",
                         "vul_version": "5.0.10~5.0.10", "ver_type": "range"},
             "repair_file": {"type": "file", "file": [
                 {"file": "thinkphp/library/think/Request.php",
                  "regular": '''preg_match('/^(EXP|NEQ|GT|EGT|LT|ELT|OR|XOR|LIKE|NOTLIKE|NOT LIKE|NOT BETWEEN|NOTBETWEEN|BETWEEN|NOTIN|NOT IN|IN)$/i'''}]},
             },
            {"cms_list": ["maccms10"], "dangerous": "3", "cms_name": "Thinkphp",
             "ps": "Thinkphp5.0.0 ~ Thinkphp5.0.21 sql injection ", "name": "Thinkphp5.0.21 sql injection ",
             "determine": ["thinkphp/base.php", "thinkphp/library/think/App.php",
                           "thinkphp/library/think/Request.php"],
             "version": {"type": "file", "file": "thinkphp/base.php", "regular": r"THINK_VERSION.+(\d+.\d+.\d+)",
                         "vul_version": "5.0.0~5.0.21", "ver_type": "range"},
             "repair_file": {"type": "file", "file": [
                 {"file": "thinkphp/library/think/db/builder/Mysql.php",
                  "regular":r'''if ($strict && !preg_match('/^[\w\.\*]+$/', $key))'''}]},
             },
            {"cms_list": ["maccms10"], "dangerous": "3", "cms_name": "Thinkphp", "ps": "Thinkphp5.0.18 The file contains vulnerabilities",
             "name": "Thinkphp5.0.18 The file contains vulnerabilities",
             "determine": ["thinkphp/base.php", "thinkphp/library/think/App.php",
                           "thinkphp/library/think/Request.php"],
             "version": {"type": "file", "file": "thinkphp/base.php", "regular": r"THINK_VERSION.+(\d+.\d+.\d+)",
                         "vul_version": "5.0.0~5.0.18", "ver_type": "range"},
             "repair_file": {"type": "file", "file": [
                 {"file": "thinkphp/library/think/template/driver/File.php",
                  "regular": '''$this->cacheFile = $cacheFile;'''}]},
             },
            {"cms_list": ["maccms10"], "dangerous": "4", "cms_name": "Thinkphp", "ps": "Thinkphp5.0.10 remote code execution",
             "name": "Thinkphp5.0.10 remote code execution",
             "determine": ["thinkphp/base.php", "thinkphp/library/think/App.php",
                           "thinkphp/library/think/Request.php"],
             "version": {"type": "file", "file": "thinkphp/base.php", "regular": r"THINK_VERSION.+(\d+.\d+.\d+)",
                         "vul_version": "5.0.0~5.0.10", "ver_type": "range"},
             "repair_file": {"type": "file", "file": [
                 {"file": "thinkphp/library/think/App.php",
                  "regular": '''$data   = "<?php\n//" . sprintf('%012d', $expire) . "\n exit();?>;'''}]},
             },
            {"cms_list": [], "dangerous": "3", "cms_name": "Wordpress", "ps": "CVE-2022–21661 Wordpress sql injection",
             "name": "CVE-2022–21661 Wordpress sql injection",
             "determine": ["wp-includes/version.php", "wp-settings.php", "wp-comments-post.php",
                           "wp-includes/class-wp-hook.php"],
             "version": {"type": "file", "file": "wp-includes/version.php", "regular": r"wp_version.+(\d+.\d+.\d+)",
                         "vul_version": "4.1.0~5.8.2", "ver_type": "range"},
             "repair_file": {"type": "file", "file": [{"file": "wp-includes/class-wp-tax-query.php",
                                                       "regular": '''if ( 'slug' === $query['field'] || 'name' === $query['field'] )'''}]}}
        ]
        return result

    def getCmsType(self, webinfo, cmsinfo):
        '''
        @name 确定CMS类型
        @author lkq<2022-3-30>
        @param webinfo   网站信息
        @param cmsinfo   CMS信息
        '''

        for i in cmsinfo['determine']:
            path = webinfo['path'] + '/' + i
            if not os.path.exists(path):
                return False

        # 获取cms 的版本
        if 'cms_name' in webinfo:
            if webinfo['cms_name'] != cmsinfo['cms_name']:
                if not cmsinfo['cms_name'] in cmsinfo['cms_list']: return False

        version = self.getCmsVersion(webinfo, cmsinfo)
        if not version: return False
        webinfo['version_info'] = version
        # 判断是否在漏洞版本中
        if not self.getVersionInfo(version, cmsinfo['version']): return False
        webinfo['cms_name'] = cmsinfo['cms_name']
        # 判断该网站是否修复了
        is_vufix = self.getCmsVersionVulFix(webinfo, cmsinfo)
        if not is_vufix: return False
        webinfo['is_vufix'] = True
        return True

    def getCmsVersion(self, webinfo, cmsinfo):
        '''
        @name 获取CMS版本号
        @author lkq<2022-3-30>
        @param get
        '''

        version = cmsinfo["version"]
        if 'regular_len' in version:
            info = version['regular_len']
        else:
            info = 0
        if version['type'] == 'file':
            path = webinfo['path'] + '/' + version['file']
            # public.print_log(path)
            if os.path.exists(path):
                path_info = public.ReadFile(path)
                if path_info and re.search(version['regular'], path_info):
                    if not 'cms_name' in webinfo:
                        webinfo['cms_name'] = cmsinfo['cms_name']
                    return re.findall(version['regular'], path_info)[info]
        elif version['type'] == 'single_file':
            return "1"
        elif version["type"] == 'is_file':
            path = webinfo['path'] + '/' + version['file']
            if os.path.exists(path):
                return "1"
        return False

    def getVersionInfo(self, version, versionlist):
        '''
        @name 判断当前版本在不在受影响的版本列表中
        @author lkq<2022-3-30>
        @param version 版本号
        @param versionlist 版本号列表
        '''
        if versionlist['ver_type'] == 'range':
            try:
                versionlist = versionlist['vul_version']
                start, end = versionlist.split('~')
                if version.split('.')[0] >= start.split('.')[0] and version.split('.')[0] <= end.split('.')[0]:
                    start = ''.join(start.split('.'))
                    end = ''.join(end.split('.'))
                    version = ''.join(version.split('.'))
                    if version >= start and version <= end:
                        return True
                return False
            except:
                return False
        elif versionlist['ver_type'] == 'list':
            if version in versionlist['vul_version']:
                return True
            return False

    def getCmsVersionVulFix(self, webinfo, cmsinfo):
        '''
        @name 判断漏洞是否修复
        @author lkq<2022-3-30>
        @param get
        '''
        repair_file = cmsinfo['repair_file']
        if repair_file['type'] == 'file':
            for i in repair_file['file']:
                path = webinfo['path'] + '/' + i['file']
                if os.path.exists(path):
                    path_info = public.ReadFile(path)
                    if not i['regular'] in path_info:
                        return True
        elif repair_file['type'] == 'single_file':
            for i in repair_file['file']:
                path = webinfo['path'] + '/' + i['file']
                if os.path.exists(path):
                    path_info = public.ReadFile(path)
                    if i['regular'] in path_info:
                        return True
        elif repair_file['type'] == 'version':
            return True
        elif repair_file['type'] == 'is_file':
            for i in repair_file['file']:
                path = webinfo['path'] + '/' + i['file']
                if os.path.exists(path):
                    return True
        elif repair_file['type'] == 'phpshell':
            for i in repair_file['file']:
                try:
                    path = webinfo['path'] + '/' + i['file']
                    public.WriteFile(path, i['phptext'])
                    dir_name = os.path.dirname(path)
                    getname = os.path.basename(path)
                    data = public.ExecShell("cd %s && php %s" % (dir_name, getname))
                    if len(data) <= 0: return False
                    if i['result'] in data[0]:
                        os.remove(path)
                        return True
                    else:
                        os.remove(path)
                except:
                    continue
        return False
    # ======================面板漏洞扫描 end======================= #

    # ======================wp 维护模式 start======================= #
    # 获取wp维护模式配置
    def get_wp_maintenance(self, args: public.dict_obj):
        # 校验参数
        args.validate([
            public.Param('set_id').Require().Integer('>', 0),
        ])
        from wp_toolkit import wpmgr

        ok, msg = wpmgr(args.set_id).get_maintenance_config()

        if not ok:
            raise public.HintException(msg)
        return public.success_v2(msg)

    # 设置wp维护模式配置
    def set_wp_maintenance(self, args: public.dict_obj):
        # 校验参数
        args.validate([
            public.Param('set_id').Require().Integer('>', 0),
        ])
        from wp_toolkit import wpmgr

        ok, msg = wpmgr(args.set_id).set_maintenance_config(args)

        if not ok:
            raise public.HintException(msg)

        return public.success_v2(msg)

    # 获取网站维护模式配置页
    def get_site_maintenance(self, args: public.dict_obj):
        # 校验参数
        args.validate([
            public.Param('set_id').Require().Integer('>', 0),
        ])

        # 获取网站根目录
        sites = public.M('sites').where('id=?', (args.get('set_id'),)).field('path,name').find()
        if not sites:
            raise ValueError("Website ID does not exist!")
        site_path = sites['path']

        # 读取维护模式配置，三个服务使用同一配置文件
        maintenance_config_path = os.path.join(site_path, 'aapanel-maintenance' , 'sites_maintenance_config.json')
        # print(os.path.exists(maintenance_config_path))
        data = {}
        if not os.path.exists(maintenance_config_path):
            data['maintenance'] = 'false'
            data['maintenance_title'] = 'Regular maintenance'
            data['maintenance_big_text'] = 'The website is undergoing maintenance!'
            data['maintenance_small_text'] = 'Sorry for any inconvenience caused. The website will soon return to normal.\n Please come back later!'
            data['social_network_links'] = [{"title": "", "value": ""}]
            data['times'] = ''
            data['template_upload'] = ''
            data['background_upload'] = ''
            return public.success_v2(data)
        else:
            with open(maintenance_config_path, 'r') as f:
                maintenance_config = json.load(f)
                data['maintenance'] = 'true' if maintenance_config.get('maintenance') in ['true', 'True'] else 'false'
                data['maintenance_title'] = maintenance_config.get('maintenance_title', '')
                data['maintenance_big_text'] = maintenance_config.get('maintenance_big_text','')
                data['maintenance_small_text'] = maintenance_config.get('maintenance_small_text','')
                data['social_network_links'] = maintenance_config.get('social_network_links',[])
                data['times'] = maintenance_config.get('times', '')
                data['template_upload'] = maintenance_config.get('template_upload', '')
                data['background_upload'] = maintenance_config.get('background_upload', '')
        return public.success_v2(data)

    # 设置网站维护模式
    def set_site_maintenance(self, args: public.dict_obj):
        # 校验参数
        args.validate([
            public.Param('set_id').Require().Integer('>', 0),
            public.Param('maintenance'),
        ])
        maintenance = args.get('maintenance', 'false')
        title = args.get('maintenance_title', '')
        big_text = args.get('maintenance_big_text', '')
        small_text = args.get('maintenance_small_text', '')
        social_links = json.loads(args.get('social_network_links', '[]'))
        times = args.get('times', '')
        maintenance = args.get('maintenance', '')
        background_upload = args.get('background_upload', '')
        template_upload = args.get('template_upload', '')

        try:
            # 获取服务类型
            service_type = public.get_webserver()

            # 获取网站根目录
            sites = public.M('sites').where('id=?', (args.get('set_id'),)).field('path,name').find()
            if not sites:
                raise ValueError("Website ID does not exist!")
            site_path = sites['path']

            maintenance_dir = os.path.join(site_path, 'aapanel-maintenance') # 维护目录
            maintenance_page = os.path.join(site_path, 'aapanel-maintenance.html') # 维护页
            template_file = os.path.join(site_path, 'aapanel-maintenance', 'maintenance-template.html') # 模板页
            template_dir = os.path.join(public.get_panel_path(), 'data', 'aapanel-maintenance') # 面板静态文件
            BG = os.path.join(site_path,'aapanel-maintenance' , 'assets' , 'bg.png')   # 背景文件

            # 兼容nginx，apache，openLiteSpeed
            if service_type == 'nginx':
                # 获取当前网站的nginx配置文件路径
                config_path = f'/www/server/panel/vhost/nginx/{sites["name"]}.conf'
                if not os.path.exists(config_path):
                    raise ValueError('Nginx configuration file does not exist!')

                if maintenance in ['true', 'True']:
                    # 判断用户是否上传了模板文件
                    if template_upload:
                        if not os.path.exists(template_upload):
                            raise ValueError('Template file does not exist!')

                        if ' ' in template_upload.strip() or template_upload[:-1] == '/':
                            raise ValueError('File paths cannot have Spaces or end with /!')

                        ok ,msg =  self.update_nginx_maintenance_block(config_path, template_upload, site_path)
                        if not ok:
                            raise ValueError(msg)

                        # 重启服务并记录配置参数
                        ok, msg = self.restart_record_config(site_path, {
                                "maintenance" : 'true',
                                "maintenance_title": title,
                                "maintenance_big_text": big_text,
                                "maintenance_small_text": small_text,
                                "social_network_links": social_links,
                                "times": times,
                                "template_upload": template_upload,
                                "background_upload": background_upload
                            },'nginx')

                        if not ok:
                            raise ValueError(msg)

                        return public.success_v2('Setting successful')

                    else:
                        # 未上传模板，默认使用系统模板
                        ok ,msg = self.update_nginx_maintenance_block(config_path, maintenance_page, site_path)
                        if not ok:
                            raise ValueError(msg)

                else:
                    # 维护模式关闭，删除配置块
                    self.remove_nginx_maintenance_block(config_path)
                    ok, msg = self.restart_record_config(site_path, {
                        "maintenance": 'false',
                        "maintenance_title": title,
                        "maintenance_big_text": big_text,
                        "maintenance_small_text": small_text,
                        "social_network_links": social_links,
                        "times": times,
                        "template_upload": template_upload,
                        "background_upload": background_upload
                    }, 'nginx')
                    if not ok:
                        raise ValueError(msg)

                    return public.success_v2('Setting successful')

            elif service_type in ['apache', 'openlitespeed']:
                # 修改.htaccess配置文件
                config_path = os.path.join(site_path,'.htaccess')

                # 检查配置块是否存在
                status = self.is_maintenance_enabled(config_path)

                if maintenance in ['true', 'True']:
                    # 存在即先删除配置块再写入
                    if status:
                        self.remove_maintenance_block(config_path)

                    # 判断用户是否上传了模板文件
                    if template_upload:
                        if not os.path.exists(template_upload):
                            raise ValueError('Template file does not exist!')

                        if ' ' in template_upload.strip() or template_upload[:-1] == '/':
                            raise ValueError('File paths cannot have Spaces or end with /!')

                        self.add_maintenance_block(config_path, template_upload)

                        ok, msg = self.restart_record_config(site_path, {
                            "maintenance": 'true',
                            "maintenance_title": title,
                            "maintenance_big_text": big_text,
                            "maintenance_small_text": small_text,
                            "social_network_links": social_links,
                            "times": times,
                            "template_upload": template_upload,
                            "background_upload": background_upload
                        }, service_type)
                        if not ok:
                            raise ValueError(msg)

                        return public.success_v2('Setting successful')

                    else:
                        # 未上传模板，默认使用系统模板
                        self.add_maintenance_block(config_path, maintenance_page)

                else:
                    if status:
                        self.remove_maintenance_block(config_path)

                    ok, msg = self.restart_record_config(site_path, {
                        "maintenance": 'false',
                        "maintenance_title": title,
                        "maintenance_big_text": big_text,
                        "maintenance_small_text": small_text,
                        "social_network_links": social_links,
                        "times": times,
                        "template_upload": template_upload,
                        "background_upload": background_upload
                    }, service_type)
                    if not ok:
                        raise ValueError(msg)

                    return public.success_v2('Setting successful!')

            # 校验模板文件是否正确
            if not os.path.exists(template_file):
                if os.path.exists(maintenance_dir):
                    os.remove(maintenance_dir)

                if not os.path.exists(template_dir):
                    raise ValueError('The default template does not exist')

                public.ExecShell(f'cp -r {template_dir} {site_path}')

            # # 读取配置参数
            with open(template_file, 'r', encoding='utf-8') as f:
                template_content = f.read()

            # 替换模板内容
            content = template_content.replace("{{TITLE}}", title)
            content = content.replace("{{BIG_TEXT}}", big_text)
            content = content.replace("{{SMALL_TEXT}}", small_text.replace("\n", "<br>"))
            content = content.replace("{{TIMES}}", times)

            # 判断用户是否上传图片
            if background_upload:
                if os.path.exists(background_upload):
                    bg_data = public.image_to_base64(background_upload)
                    content = content.replace("{{BG}}", bg_data)
                else:
                    return False, 'Background file does not exist!'
            else:
                # 使用系统默认背景图
                bg_data = public.image_to_base64(BG)
                content = content.replace("{{BG}}", bg_data)

            # social_html = ""
            # for link in social_links:
            #     if link['title'] and link['value']:
            #         social_html += f'<a href="{link['value']}" target="_blank"> {link['title']} </a>\n'
            #     elif  link['title'] and not link['value']:
            #         social_html += f'<a" target="_blank"> {link['title']} </a>\n'

            # 优化字符格式化，兼容python3.6+
            social_html = ""
            for link in social_links:
                if link['title'] and link['value']:
                    social_html += f"<a href='{link['value']}' target='_blank'> {link['title']} </a>\n"
                elif link['title'] and not link['value']:
                    social_html += f"<a target='_blank'> {link['title']} </a>\n"

            content = content.replace("{{SOCIAL_LINKS}}", social_html)

            with open(maintenance_page, 'w', encoding='utf-8') as f:
                f.write(content)

            # 记录配置
            ok, msg = self.restart_record_config(site_path, {
                "maintenance": 'true',
                "maintenance_title": title,
                "maintenance_big_text": big_text,
                "maintenance_small_text": small_text,
                "social_network_links": social_links,
                "times": times,
                "template_upload": template_upload,
                "background_upload": background_upload
            }, service_type)
            if not ok:
                raise ValueError(msg)

            return public.success_v2('Setting successful')
        except Exception as e:
            raise public.HintException(f"Set error: {e}")

    # 检测apache与openLiteSpeed维护模式配置块是否存在
    def is_maintenance_enabled(self, htaccess_path: str)-> bool:
        """
        简化判断：检测维护模式配置块是否存在
        :param htaccess_path: .htaccess文件路径
        :return: True（存在配置块，视为开启）/False（不存在配置块，视为关闭）
        """
        if not os.path.exists(htaccess_path):
            return False

        # 读取.htaccess内容
        with open(htaccess_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()

        # 匹配维护模式的开始和结束标记
        start_pattern = r'# ========== maintenance mode start============='
        end_pattern = r'# ========== maintenance mode end============='

        # 同时存在开始和结束标记，且开始标记在结束标记之前，视为配置块存在
        has_start = re.search(start_pattern, content) is not None
        has_end = re.search(end_pattern, content) is not None

        # 确保开始标记在结束标记之前
        if has_start and has_end:
            start_pos = re.search(start_pattern, content).start()
            end_pos = re.search(end_pattern, content).start()
            return start_pos < end_pos

        return False

    # 添加apache与openLiteSpeed维护模式配置块
    def add_maintenance_block(self, htaccess_path: str, template_path: str)-> bool:
        """
        向.htaccess添加维护模式配置块
        :param htaccess_path: .htaccess文件路径
        :param template_path: 模板路径
        :return: True（添加成功）/False（已存在配置块）
        """
        with open(htaccess_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()

        # 构建维护模式配置块内容
        maintenance_block = f"""# ========== maintenance mode start=============
    # #Newly added or modified configurations between the start and end of maintenance mode will be overwritten.
    RewriteEngine On
    RewriteCond %{{REQUEST_URI}} !^{template_path}$
    RewriteCond %{{REQUEST_URI}} !\\.(css|js|png|jpg|jpeg|gif|ico|svg|webp)$
    RewriteRule ^(.*)$ {template_path}
    <Files "maintenance.html">
        Require all granted
        Header set Cache-Control "no-store, no-cache, must-revalidate"
        Header set Pragma "no-cache"
    </Files>
    # ========== maintenance mode end=============

    """

        # 将配置块添加到文件开头（也可根据需要添加到末尾）
        new_content = maintenance_block + content

        # 写回文件
        with open(htaccess_path, 'w', encoding='utf-8', errors='ignore') as f:
            f.write(new_content)

        return True

    # 删除apache与openLiteSpeed维护模式配置块
    def remove_maintenance_block(self, htaccess_path: str) -> tuple[bool,str]:
        """
        删除.htaccess中的维护模式配置块（包括开始和结束标记）
        :param htaccess_path: .htaccess文件路径
        :return: True（删除成功）/False（文件不存在或无配置块）
        """
        try:
            if os.path.exists(htaccess_path):

                # 读取文件内容
                with open(htaccess_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()

                # 正则匹配整个维护模式配置块（包括开始和结束标记）
                block_pattern = re.compile(
                    r'# ========== maintenance mode start=============.*?'
                    r'# ========== maintenance mode end=============.*?\n',
                    re.DOTALL  # 匹配换行符
                )

                # 检查是否存在配置块
                if not block_pattern.search(content):
                    return False  # 无配置块，无需删除

                # 移除配置块
                new_content = block_pattern.sub('', content)

                # 写回文件
                with open(htaccess_path, 'w', encoding='utf-8', errors='ignore') as f:
                    f.write(new_content)
            return True, 'success'
        except Exception as e:
            return False,str(e)

    # 删除nginx维护模式配置块
    def remove_nginx_maintenance_block(self, nginx_conf_path: str) -> tuple[bool, str]:
        """
        简单删除开始标记到结束标记之间的所有内容（包括标记本身）
        :param nginx_conf_path: Nginx配置文件路径
        :return: 元组 (是否成功, 处理后的内容/错误信息)
        """
        start_marker = "# ========== maintenance mode start============="
        end_marker = "# ========== maintenance mode end============="

        # 读取文件内容
        try:
            with open(nginx_conf_path, 'r', encoding='utf-8', errors='ignore') as f:
                lines = f.readlines()  # 按行读取，方便处理
        except FileNotFoundError:
            return False, f"Error: File {nginx_conf_path} not found"
        except Exception as e:
            return False, f"Read error: {str(e)}"

        # 查找开始和结束标记的位置
        start_idx = None
        end_idx = None
        for i, line in enumerate(lines):
            if start_marker in line:
                start_idx = i
            if end_marker in line:
                end_idx = i

        # 检查块块不存在的情况
        if start_idx is None or end_idx is None or start_idx >= end_idx:
            return True, "No maintenance block found, nothing to delete"

        # 删除从开始标记到结束标记的所有行（包括标记行）
        del lines[start_idx:end_idx + 1]

        # 合并行并清理空行
        new_content = ''.join(lines)
        new_content = re.sub(r'\n{3,}', '\n\n', new_content).strip() + '\n'

        # 写回文件
        try:
            with open(nginx_conf_path, 'w', encoding='utf-8') as f:
                f.write(new_content)
            return True, "Maintenance block removed successfully"
        except Exception as e:
            return False, f"Write error: {str(e)}"

    # 更新nginx维护配置
    def update_nginx_maintenance_block(self, nginx_conf_path: str, template_path: str, site_root: str) -> tuple[bool, str]:
        """
        更新Nginx配置文件中的维护模式配置块（先删除再添加）
        :param nginx_conf_path: Nginx配置文件路径
        :param template_path: 维护页面模板路径（相对于网站根目录）
        :param site_root: 网站根目录绝对路径
        :return: True（操作成功）/False（操作失败）
        """
        try:
            # 先删除现有配置块
            self.remove_nginx_maintenance_block(nginx_conf_path)

            # 如果是首次添加，result就是原始内容；如果是更新，result是删除后的内容
            with open(nginx_conf_path, 'r', encoding='utf-8', errors='ignore') as f:
                content =  f.read()

            # 构建新的维护模式配置块内容
            start_marker = "# ========== maintenance mode start============="
            end_marker = "# ========== maintenance mode end============="
            maintenance_block = fr"""    {start_marker}
    error_page 503 @maintenance;
    location @maintenance {{
        root {site_root};
        
        try_files /{template_path.split('/')[-1]} =503;
        
    }}
    
    location / {{

        if ($request_uri !~ ^/{template_path.split('/')[-1]}$) {{
            return 503;
        }}

        if ($request_filename ~* ^{site_root}/.*\.(css|js|png|jpg|jpeg|gif|ico|svg|webp)$) {{
            root /;  
            break;
        }}
        return 503;
    }}

    location = /maintenance.enable {{
        deny all;
        return 403;
    }}
    {end_marker}

        """
            maintenance_core1 = fr"""
    {start_marker}
    if ($request_uri !~ ^/{template_path.split('/')[-1]}$) {{
        return 503;
    }}

    if ($request_filename ~* ^{site_root}/.*\.(css|js|png|jpg|jpeg|gif|ico|svg|webp)$) {{
        root /;  
        break;
    }}
    return 503;
    {end_marker}
            """
            maintenance_core2 = fr"""     {start_marker}
    error_page 503 @maintenance;
    location @maintenance {{
        root {site_root};
        
        try_files /{template_path.split('/')[-1]} =503;
        
    }}
    {end_marker}
    """
            root_pattern = r'(root\s+[^;]+;)'
            root_matches = re.finditer(root_pattern, content)
            match = next(root_matches, None)
            location_pattern = r'(location\s+/\s*\{)'
            location_match = re.search(location_pattern, content, re.IGNORECASE)

            # 判断是否存在location /配置块
            if location_match:
                location_start = location_match.group(0)

                # 查找location /块中的第一个{后的位置，插入维护规则
                replacement = f"{location_start}\n{maintenance_core1.strip()}"

                # 替换原location /块
                location_content = re.sub(
                    location_pattern,
                    replacement,
                    content,
                    flags=re.IGNORECASE
                )
                content = location_content
                maintenance_block = maintenance_core2

            if match:
                root_line = match.group(0)
                new_content = content.replace(
                    root_line,
                    f"{root_line}\n\n{maintenance_block}",
                    1
                )
            else:
                if re.search(r'server\s*\{', content, re.IGNORECASE):
                    new_content = re.sub(
                        r'(server\s*\{)',
                        f'\\1\n{maintenance_block}',
                        content,
                        count=1,
                        flags=re.IGNORECASE
                    )
                else:
                    return False, "Error: Nginx configuration file does not contain a valid server block"

        # 写回配置文件
            with open(nginx_conf_path, 'w', encoding='utf-8') as f:
                f.write(new_content)
            return True, f"Updated successfully"
        except Exception as e:
            return False, f"Error: {e}"

    # 重启服务与记录配置参数
    def restart_record_config(self,site_path : str, config: dict,  service_name = None) ->  tuple[bool, str]:
        import system_v2
        server_restart = system_v2.system()

        # 记录配置
        maintenance_config_path = os.path.join(site_path, 'aapanel-maintenance', 'sites_maintenance_config.json')

        if not os.path.exists(maintenance_config_path):
            template_dir = os.path.join(public.get_panel_path(), 'data', 'aapanel-maintenance')
            if not os.path.exists(template_dir):
                raise ValueError('The default template does not exist')

            public.ExecShell(f'cp -r {template_dir} {site_path}')

        with open(maintenance_config_path, 'w') as f:
            f.write(json.dumps(config))

        # 重启服务
        get = public.to_dict_obj({
            'name': service_name,
            'type': 'restart'
        })
        ok = server_restart.ServiceAdmin(get)
        if ok.get('status') == -1:
            return False, f"Failed to restart the service, please check the configuration file and try manually restarting!"

        return True, 'Setting successful!'

    # 校验是否开启维护模式，开启即关闭
    def check_maintenance_mode(self,site_path: str) -> bool:
        maintenance_file = os.path.join(site_path, '.maintenance')
        if os.path.exists(maintenance_file):
            os.rename(maintenance_file, maintenance_file + '.bak.bak')
            return True
        return False

    # 恢复维护模式
    def restore_maintenance_mode(self, site_path: str) -> bool:
        bak_file = os.path.join(site_path, '.maintenance.bak.bak')
        if os.path.exists(bak_file):
            os.rename(bak_file, os.path.join(site_path, '.maintenance'))

        return True

    # ======================wp 维护模式 end======================= #

    # ======================网站多服务 start======================= #
    # 获取网站多服务状态
    def get_multi_webservice_status(self, args: public.dict_obj):
        from panelModelV2.publicModel import main
        public_obj = main()
        data = {
            'nginx': False,
            'openlitespeed': False,
            'apache': False,
            'status':False
        }
        for service in ['openlitespeed', 'apache', 'nginx']:
            args = public.to_dict_obj({'name': service})
            res = public_obj.get_soft_status(args)

            if res['status'] == 0:
                data[service] = res['message']['s_status']

        data['status'] = public.get_multi_webservice_status()
        return public.return_message(0, 0, data)

    # 切换多服务状态
    def switch_multi_webservice_status(self, args: public.dict_obj):
        try:
            status = args.get('status', '')
            reserve = args.get('reserve', '')
            multi_webservice_status = public.get_multi_webservice_status()
        except:
            return public.return_message(-1, 0, 'Parameter error')

        if status not in ['enable', 'disable']:
            return public.return_message(-1, 0, 'Parameter error')

        # 切换服务
        if status == 'enable':
            # if multi_webservice_status:
            #     return public.return_message(-1, 0, public.lang('The multi-service of the website has been enabled. '
            #                                                     'If a service is unavailable, please try to disable it and then re-enable it.'))

            ok, msg = self.enable_multi_webservice()
            if not ok:
                return public.return_message(-1, 0, f'Error: {msg}')

        else:
            if not reserve:
                return public.return_message(-1, 0, public.lang('Please select the retained service'))
            elif not multi_webservice_status:
                return public.return_message(-1, 0, public.lang('Please enable multiple services first'))

            ok, msg = self.disable_multi_webservice(reserve)

        if not ok:
            return public.return_message(-1, 0, f'Error: {msg}')

        return public.return_message(0, 0, msg)

    # 开启多服务
    def enable_multi_webservice(self) -> tuple[bool, str]:
        from panel_plugin_v2 import panelPlugin
        from panelModelV2.publicModel import main
        from files_v2 import files
        plugin = panelPlugin()
        files_obj = files()
        public_obj = main()

        # 获取当前服务
        current_status = public.get_webserver()

        # 当前服务若为nginx，检查是否为openresty版本
        if current_status == 'nginx':
            args = public.to_dict_obj({'name': 'nginx'})
            nginx_version = public_obj.get_soft_status(args)

            if nginx_version.get('status', -1) == -1:
                return False, public.lang('Error in obtaining nginx version information')

            if 'openresty' in nginx_version['message'].get('version', ''):
                return False, public.lang('Currently, openresty is not supported')

        if files_obj.GetTaskSpeed(None)['status'] != -1:
            return False, public.lang('There is already an installation task. Please wait for it to complete first!')

        try:
            # 校验服务是否都成功安装
            if len(public.get_multi_webservice_list()) != 3:
                raise ValueError(public.lang('Service installation failed. Please try again!'))

            # 停止nginx
            public.webservice_operation('nginx','stop')

            # 关闭全部网站的强制Https，避免重定向
            try:
                sites = public.M('sites').field('name').select()
                for site in sites:
                    obj = public.to_dict_obj({'siteName': site['name']})
                    ssl_data = self.GetSSL(obj)
                    if ssl_data['status'] == 0 and ssl_data['message']['httpTohttps'] in ['true', True]:
                        self.CloseToHttps(obj)
            except Exception as e:
                public.print_log(str(e))

            # 解决自定义端口冲突
            self.cheak_port_conflict('enable')

            # 修改配置
            ok, msg = self.ols_update_config('enable')
            if not ok:
                raise ValueError(msg)

            ok, msg = self.apache_update_config('enable')
            if not ok:
                raise ValueError(msg)

            # 重启nginx
            public.webservice_operation('nginx')

            # 检查服务状态
            for service in ['openlitespeed', 'apache', 'nginx']:
                args = public.to_dict_obj({'name': service})
                res = public_obj.get_soft_status(args)
                if res['status'] != 0:
                    raise ValueError(public.lang("Service startup failed: {}", service))

            if os.path.exists('/tmp/multi_service_install.log'):
                os.remove('/tmp/multi_service_install.log')
            public.write_log_gettext('Site manager', 'Successfully activated the Multi-WebServer Hosting!')
            public.set_module_logs(f'Multi-WebServer', 'enable_multi_webservice')
            return True, public.lang('The multi-service mode has been successfully enabled')
        except Exception as e:
            if os.path.exists('/tmp/multi_service_install.log'):
                os.remove('/tmp/multi_service_install.log')
            try:
                # 开启失败，关闭服务
                self.disable_multi_webservice(current_status)
            except:
                pass
            return False, str(e)

    # 关闭多服务, 保留指定服务，卸载其他
    def disable_multi_webservice(self, reserve: str) -> tuple[bool, str]:
        from panel_plugin_v2 import panelPlugin
        from panelModelV2.publicModel import main
        public_obj = main()
        plugin = panelPlugin()
        service_list = ['nginx', 'apache', 'openlitespeed']
        service_list.remove(reserve)  # 移除保留服务

        # 卸载服务
        for service in service_list:
            args = public.to_dict_obj({'name': service})
            service_status = public_obj.get_soft_status(args)

            if service_status['status'] == 0:
                args = public.to_dict_obj({'sName': service_status['message']['name'],
                                           'version': service_status['message']['version']})
                res = plugin.uninstall_plugin(args)

                if res.get('status', -1) == -1:
                    return False, public.lang("Failed to uninstall {} service. Please try again!",service)

        # 恢复端口
        self.cheak_port_conflict('d')

        # 恢复配置
        self.apache_update_config('disable', False)

        self.ols_update_config('disable', False)

        # 统一恢复nginx配置文件
        sites = public.M('sites').where('service_type = ? or service_type = ?', ('apache','openlitespeed')).field('id,name,path,service_type').select()
        for site in sites:
            config_path = os.path.join(public.get_panel_path(), 'vhost', 'nginx', site['name'] + '.conf')
            self.nginx_update_config('nginx', config_path, site['service_type'], site['name'], site['path'], site['id'])
        public.M('sites').where('service_type = ? or service_type = ?', ('apache', 'openlitespeed')).update({'service_type': ''})

        # 处理ols 7080端口遗留
        if reserve != 'openlitespeed':
            process_id = public.ExecShell('lsof -t -i:7080')[0]
            if process_id:
                id_list = process_id.split('\n')
                for id in id_list:
                    public.ExecShell(f'kill -9 {id}')

        # 重启指定服务
        ok = public.webservice_operation(reserve)
        if not ok:
            return False, public.lang("The {} service failed to restart. Please try a manual restart or check the configuration file.",reserve)

        public.write_log_gettext('Site manager	', 'Successfully shut down the Multi-WebServer Hosting and retain [{}]!',
                                 (reserve,))
        return True, public.lang('The multi-service mode has been successfully disable')

    # ols 修改多服务配置文件
    def ols_update_config(self, status, is_restart=True) -> tuple[bool, str]:
        """
            端口关系：
                8188:80
                8190:443
        """
        listen_dir = os.path.join(public.get_panel_path(), 'vhost', 'openlitespeed')
        listen_main = os.path.join(listen_dir, 'listen', '80.conf')  # 主监听
        listen_ssl = os.path.join(listen_dir, 'listen', '443.conf')

        phpmyadmin = [
            os.path.join(listen_dir, 'listen', '887.conf'),
            os.path.join(listen_dir, 'listen', '888.conf'),
            os.path.join(listen_dir, 'phpmyadmin.conf'),
            os.path.join(listen_dir, 'detail', 'phpmyadmin.conf')
        ]
        pattern = '*:80'
        pattern_ANY = '[ANY]:80'
        pattern_ssl = '*:443'
        pattern_ssl_ANY = '[ANY]:443'

        if status == 'enable':
            if os.path.exists(listen_main):
                content = public.readFile(listen_main)
                content = content.replace(pattern, '*:8188')
                content = content.replace(pattern_ANY, '[ANY]:8188')
                public.writeFile(listen_main, content)

            if os.path.exists(listen_ssl):
                content = public.readFile(listen_ssl)
                content = content.replace(pattern_ssl, '*:8190')
                content = content.replace(pattern_ssl_ANY, '[ANY]:8190')
                public.writeFile(listen_ssl, content)

            # 取消监听phpmyadmin
            for path in phpmyadmin:
                if os.path.exists(path):
                    shutil.move(path, path + '.bar')

        elif status == 'disable':
            pattern = '*:8188'
            pattern_ANY = '[ANY]:8188'
            pattern_ssl = '*:8190'
            pattern_ssl_ANY = '[ANY]:8190'

            # 恢复服务
            if os.path.exists(listen_main):
                content = public.readFile(listen_main)
                content = content.replace(pattern, '*:80')
                content = content.replace(pattern_ANY, '[ANY]:80')
                public.writeFile(listen_main, content)

            if os.path.exists(listen_ssl):
                content = public.readFile(listen_ssl)
                content = content.replace(pattern_ssl, '*:443')
                content = content.replace(pattern_ssl_ANY, '[ANY]:443')
                public.writeFile(listen_ssl, content)

            for path in phpmyadmin:
                if os.path.exists(path + '.bar'):
                    shutil.move(path + '.bar', path)

            # 处理用户添加的端口恢复
            listen_custom_dir = os.path.join(listen_dir, 'listen')
            if os.path.exists(listen_custom_dir):
                for filename in os.listdir(listen_custom_dir):
                    file = filename.split('.')[0]
                    if file not in ['80', '443', '887', '888']:
                        content = public.readFile(os.path.join(listen_custom_dir,filename))
                        if not content:
                            continue
                        content = content.replace(pattern, '*:'+file)
                        content = content.replace(pattern_ANY, '*:'+file)
                        public.writeFile(os.path.join(listen_custom_dir,filename), content)

        # 重启ols
        if is_restart:
            ok = public.webservice_operation('openlitespeed')

            if not ok:
                return False, public.lang(
                    "The service restart failed. Please check the openlitespeed configuration file!")

        return True, "The ols configuration modification was successful！"

    # apache 修改多服务配置文件
    def apache_update_config(self, status, is_restart=True) -> tuple[bool, str]:
        """
            端口关系：
                8288:80
                8289:888
                8290:443
        """
        main_config = '/www/server/apache/conf/httpd.conf'  # 主配置文件
        httpd_vhosts = '/www/server/apache/conf/extra/httpd-vhosts.conf'
        httpd_ssl = '/www/server/apache/conf/extra/httpd-ssl.conf'
        phpadmin = os.path.join(public.get_panel_path() , 'vhost' ,'apache','phpmyadmin.conf')
        from adminer import config
        ols_adminer = config.OLS_CONF_PATH
        apache_adminer = config.APC_CONF_PATH
        bar_list = [phpadmin,ols_adminer,apache_adminer]

        port_80 = '80'
        new_port_80 = '8288'
        port_888 = '888'
        new_port_888 = '8289'
        port_443 = '443'
        new_port_443 = '8290'

        if status == 'disable':
            port_80 = '8288'
            new_port_80 = '80'
            port_888 = '8289'
            new_port_888 = '888'
            port_443 = '8290'
            new_port_443 = '443'

            # 恢复配置文件
            for bar in bar_list:
                if os.path.exists(bar + '.bar'):
                    shutil.move(bar + '.bar', bar)
        else:
            # 使配置文件无效
            for bar in bar_list:
                if os.path.exists(bar):
                    shutil.move(bar, bar + '.bar')

        # 修改虚拟主机端口配置，匹配所有网站配置文件，避免漏网之鱼
        site_path_list = self.get_apache_site_conf()
        for path in site_path_list:
            if os.path.exists(path):
                content = public.readFile(path)
                content = content.replace(f'*:{port_80}', f'*:{new_port_80}')
                content = content.replace(f'*:{port_443}', f'*:{new_port_443}')
                content = content.replace(f'[::]:{port_80}', f'[::]:{new_port_80}')
                content = content.replace(f'[::]:{port_443}', f'[::]:{new_port_443}')
                public.writeFile(path, content)

        # 处理node
        site_name = public.M('sites').where('project_type = ?','Node').field('name').select()
        for name in site_name:
            self.check_node_project(name, status)

            # path = os.path.join(public.get_panel_path(), 'vhost', 'apache', name['name'] + '.conf')
        #     if os.path.exists(path):
        #         content = public.readFile(path)
        #         content = content.replace(f'*:{port_80}', f'*:{new_port_80}')
        #         content = content.replace(f'*:{port_443}', f'*:{new_port_443}')
        #         public.writeFile(path, content)

        if os.path.exists(main_config):
            content = public.readFile(main_config)
            content = content.replace(f'Listen {port_80}', f'Listen {new_port_80}')
            content = content.replace(f'Listen {port_443}', f'Listen {new_port_443}')
            content = content.replace(f'ServerName 0.0.0.0:{port_80}', f'ServerName 0.0.0.0:{new_port_80}')
            public.writeFile(main_config, content)

        if os.path.exists(httpd_vhosts):
            content = public.readFile(httpd_vhosts)
            content = content.replace(f'Listen {port_888}', f'Listen {new_port_888}')
            content = content.replace(f'*:{port_888}', f'*:{new_port_888}')
            content = content.replace(f'*:{port_80}', f'*:{new_port_80}')
            content = content.replace(f'[::]:{port_888}', f'[::]:{new_port_888}')
            content = content.replace(f'[::]:{port_80}', f'[::]:{new_port_80}')
            public.writeFile(httpd_vhosts, content)

        if os.path.exists(httpd_ssl):
            content = public.readFile(httpd_ssl)
            content = content.replace(f'{port_443}', f'{new_port_443}')
            public.writeFile(httpd_ssl, content)

        if is_restart:
            ok = public.webservice_operation('apache')

            if not ok:
                return False, public.lang("The service restart failed. Please check the apache configuration file!")
        return True, ' '

    # nginx 修改多服务配置文件
    def nginx_update_config(self, service_type, config_path, old_type, site_name, site_path, site_id) -> bool:
        ssl_port = '443'
        listen_port = '80'

        content = public.readFile(config_path)
        if not content:
            return False

        # 备份原nginx配置文件
        shutil.copy2(config_path, config_path + '.bar.bar')

        # 匹配服务名称，索引文件，PHP配置块，日志文件等
        patterns = {
            'server_name': r'(server_name\s+[^;]+\s*;)',
            'ssl': r'#SSL-START.*?\n(.*?)#SSL-END',
            'Monitor' : r'#Monitor-Config-Start.*?#Monitor-Config-End',
            'include_php': r'#PHP-INFO-START.*?\n(.*?)#PHP-INFO-END',
            'listen' : r'^\s*listen\b.*?;.*$',
            'rert_apply_check': r'#CERT-APPLY-CHECK--START.*?\n(.*?)#CERT-APPLY-CHECK--END',
            'begin_deny' :  r'(\s*#BEGIN_DENY_(\w+)\s*\n.*?#END_DENY_\2\s*\n)',
            'default_document' : r'(index\s+[^;]+\s*;)',
        }

        res = {}
        for key, pattern in patterns.items():
            # 特殊处理生成类配置
            if key in ['rert_apply_check','ssl','include_php']:
                match = re.search(pattern, content, re.DOTALL)
                res[key] = match.group(1).strip() if (match and match.group(1)) else ''

                # 处理php版本, 代理后注释原nginx的php版本
                if key == 'include_php' and res[key] != '\n' and service_type == 'nginx':
                    matches = re.findall(r'^\s*#include enable-.*$', res[key], re.MULTILINE)
                    if matches:
                        if matches[0].lstrip().startswith('#'):
                            res[key] = res[key].replace(matches[0].lstrip(), matches[0].lstrip()[1:])
                elif key == 'include_php' and res[key] != '\n' and service_type != 'nginx':
                    matches = re.findall(r'^\s*include enable-.*$', res[key], re.MULTILINE)
                    if matches:
                        if not matches[0].lstrip().startswith('#'):
                            res[key] = res[key].replace(matches[0].lstrip(), '#' + matches[0].lstrip())

            elif key == 'Monitor' or key == 'rert_apply_check' :
                match = re.findall(pattern, content, re.DOTALL)
                res[key] = match[0] if match else '\n'

            elif key == 'listen' or key == 'default_document':
                matches = re.findall(pattern, content, re.MULTILINE)
                unique_matches = list(set(matches))
                res[key] = ''
                if unique_matches:
                    for m in unique_matches:
                        res[key] += '\t\t' + m.strip() + '\n'

            elif key == 'begin_deny':
                matches = re.findall(pattern, content, re.DOTALL)
                blocks = '\n'.join([match[0].strip() for match in matches])
                res[key] =blocks if blocks else ''
            else:
                matches = re.findall(pattern, content)
                if matches:
                    res[key] = f"{matches[0]}\n"
                else:
                    return False

        # 检查是否存在重定向
        res['referenced_redirect'] = ''
        if "#referenced redirect rule" in content:
            res['referenced_redirect']= f"""
    #referenced redirect rule, if comented, the configured redirect rule will be invalid
    include /www/server/panel/vhost/nginx/redirect/{site_name}/*.conf;
"""

        log_path = public.GetConfigValue('logs_path') + '/' + site_name
        # 获取运行目录
        dict_obj = public.to_dict_obj({'id': site_id })
        run_path = self.GetSiteRunPath(dict_obj)
        if run_path['status'] == 0:
            site_path = site_path + run_path['message']['runPath']

        # 切换到nginx
        if service_type == 'nginx':
            # 构建配置块
            conf = r'''server
 {{
{listen}
    {server_name}
{default_document}
    root {site_path};

    #SSL-START SSL related configuration, do NOT delete or modify the next line of commented-out 404 rules
    {ssl}
    #SSL-END
    
    {rert_apply_check}

    #ERROR-PAGE-START  Error page configuration, allowed to be commented, deleted or modified
    error_page 404 /404.html;
    error_page 502 /502.html;
    #ERROR-PAGE-END
    {begin_deny}
    
    #PHP-INFO-START PHP reference configuration, allowed to be commented, deleted or modified
    {include_php}
    #PHP-INFO-END
    {referenced_redirect}
    #REWRITE-START URL rewrite rule reference, any modification will invalidate the rewrite rules set by the panel
    include /www/server/panel/vhost/rewrite/{site_name}.conf;
    #REWRITE-END

    # Forbidden files or directories
    location ~ ^/(\.user.ini|\.htaccess|\.git|\.env|\.svn|\.project|LICENSE|README.md)
    {{
        return 404;
    }}

    # Directory verification related settings for one-click application for SSL certificate'
    location ~ \.well-known{{
        allow all;
    }}

    #Prohibit putting sensitive files in certificate verification directory
    if ( $uri ~ "^/\.well-known/.*\.(php|jsp|py|js|css|lua|ts|go|zip|tar\.gz|rar|7z|sql|bak)$" ) {{
        return 403;
    }}

    access_log {_log}.log;
    error_log  {_log}.error.log;  
    
    {Monitor}
}}'''.format(server_name=res['server_name'], include_php=res['include_php'], Monitor=res['Monitor'],rert_apply_check=res['rert_apply_check'],
             listen_port=listen_port, site_name=site_name, site_path=site_path, ssl=res['ssl'],listen=res['listen'],begin_deny=res['begin_deny'],
             _log=log_path,default_document=res['default_document'],referenced_redirect=res['referenced_redirect'])

            public.writeFile(config_path, conf)
            wp_path = os.path.join(site_path, 'wp-config.php')
            if old_type == 'apache' and os.path.exists(wp_path):
                self.wp_https_conf(wp_path, 'delete')
            return True

        # 构建apache/ols的nginx配置块
        if service_type == 'apache':
            ssl_port = '8290'
            listen_port = '8288'
        elif service_type == 'openlitespeed':
            ssl_port = '8190'
            listen_port = '8188'

        new_block = r"""server 
{{
{listen}
    {server_name}
{default_document} 
    root {site_path};   
    {rert_apply_check}

    #PHP-INFO-START\s+PHP reference configuration, allowed to be commented, deleted or modified
    {include_php}
    #PHP-INFO-END

    #SSL-START SSL related configuration, do NOT delete or modify the next line of commented-out 404 rules
    {ssl}
    #SSL-END
    {referenced_redirect}
    #REWRITE-START URL rewrite rule reference, any modification will invalidate the rewrite rules set by the panel
    # include /www/server/panel/vhost/rewrite/{site_name}.conf;
    #REWRITE-END

    #ERROR-PAGE-START  Error page configuration, allowed to be commented, deleted or modified
    #error_page 404 /404.html;
    #error_page 502 /502.html;
    #ERROR-PAGE-END
    {begin_deny}

    location / {{
        proxy_pass http://127.0.0.1:{listen_port};

        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_set_header REMOTE-HOST $remote_addr;
		proxy_set_header SERVER_PROTOCOL $server_protocol;
        proxy_set_header HTTPS $https;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $connection_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header REMOTE_ADDR $remote_addr;
        proxy_set_header REMOTE_PORT $remote_port;
        add_header Cache-Control no-cache;
    }}

    # Forbidden files or directories
    location ~ ^/(\.user.ini|\.htaccess|\.git|\.env|\.svn|\.project|LICENSE|README.md)
    {{
        return 404;
    }}

    location ~ \.well-known{{
        allow all;
        root {site_path};
        try_files $uri =404;
    }}

    #Prohibit putting sensitive files in certificate verification directory
    if ( $uri ~ "^/\.well-known/.*\.(php|jsp|py|js|css|lua|ts|go|zip|tar\.gz|rar|7z|sql|bak)$" ) {{
        return 403;
    }}
    
    access_log {_log}.log;
    error_log  {_log}.error.log;  

    {Monitor}
}} """.format(server_name=res['server_name'], include_php=res['include_php'],rert_apply_check=res['rert_apply_check'],
                   listen_port=listen_port, ssl_port=ssl_port, ssl=res['ssl'],Monitor=res['Monitor'],begin_deny=res['begin_deny'],
                   site_name=site_name, site_path=site_path,listen=res['listen'],_log=log_path,default_document=res['default_document'],
              referenced_redirect=res['referenced_redirect'])
        public.writeFile(config_path, new_block)

        # 处理apache配置ssl后，强制重定向
        wp_path = os.path.join(site_path, 'wp-config.php')
        if service_type == 'apache' and os.path.exists(wp_path):
            self.wp_https_conf(wp_path)
        elif old_type == 'apache' and os.path.exists(wp_path):
            self.wp_https_conf(wp_path,'delete')
        return True

    # 添加wp https识别
    def wp_https_conf(self,file_path, action='add'):
        start_comment = r'/\*\* Make WordPress correctly recognize HTTPS\. start \*/'
        end_comment = r'/\*\* Make WordPress correctly recognize HTTPS\. end \*/'
        code_block = f'{start_comment}.*?{end_comment}'
        pattern = re.compile(code_block, re.DOTALL)
        try:
            content = public.readFile(file_path)
            if not content:
                return  False

            if action == 'delete':
                new_content = pattern.sub('', content)
                public.writeFile(file_path, new_content)

            elif action == 'add':
                if pattern.search(content):
                    return True

                # 插入
                insert_marker = re.compile(r'/\* That\'s all, stop editing! Happy publishing\. \*/', re.IGNORECASE)
                match = insert_marker.search(content)

                if match:
                    code_to_add = """
/** Make WordPress correctly recognize HTTPS. start */
if (isset($_SERVER['HTTP_X_FORWARDED_PROTO']) && strtolower($_SERVER['HTTP_X_FORWARDED_PROTO']) === 'https') {
    $_SERVER['HTTPS'] = 'on';
    $_SERVER['SERVER_PORT'] = 443; 
}
/** Make WordPress correctly recognize HTTPS. end */
"""
                    new_content = content[:match.start()] + code_to_add + content[match.start():]

                    public.writeFile(file_path,new_content)
            return  True
        except:
            return  False

    # 切换网站服务
    def switch_webservice(self, args: public.dict_obj):
        try:
            site_id = args.get('site_id', '')
            site_list = json.loads(args.get('site_list', '[]'))
            service_type = args.get('service_type', '')
        except Exception as e :
            return public.return_message(-1, 0, public.lang('Parameter error'))

        if (not site_id and not site_list) or not service_type:
            return public.return_message(-1, 0, public.lang('Parameter error'))

        if service_type not in ['nginx', 'apache', 'openlitespeed']:
            return public.return_message(-1, 0, public.lang('The specified service type does not exist'))

        # 批量切换
        if site_list:
            ok , res = self.batch_switch_website_services(site_list, service_type)
            if not ok:
                return public.return_message(-1, 0, public.lang('An error occurred when switching services in batches!'))
            return public.return_message(0, 0, res)

        site = public.M('sites').where('id = ?', (site_id,)).field('id,name,path,project_type,service_type').find()

        if not site:
            return public.return_message(-1, 0, public.lang('Website ID does not exist'))

        if site['service_type'] == service_type or (not site['service_type'] and service_type == 'nginx'):
            return public.return_message(-1, 0, public.lang('The current website service is already {}', service_type))

        old_type = site['service_type'] if site['service_type'] else 'nginx'
        config_path = os.path.join(public.get_panel_path(), 'vhost', 'nginx', site['name'] + '.conf')

        # 检测是否与用户配置的反向代理冲突
        ok, msg = self.check_switch_service(site['name'], site['id'],site['service_type'],site['project_type'])
        if not ok:
            return public.return_message(-1, 0, public.lang('{}',msg))

        # 切换服务,apache需同步修改虚拟主机端口
        if service_type == 'apache':
            path = os.path.join(public.get_panel_path(), 'vhost', 'apache', site['name'] + '.conf')
            if os.path.exists(path):
                content = public.readFile(path)
                content = content.replace(f'*:80', f'*:8288')
                content = content.replace(f'*:443', f'*:443')
                public.writeFile(path, content)

        # 修改nginx代理, 若是回滚操作则不修改配置，直接恢复备份
        if not args.get('website_rollback', False):
            ok = self.nginx_update_config(service_type, config_path, old_type, site['name'], site['path'], site['id'])
            if not ok:
                return public.return_message(-1, 0, public.lang('The configuration modification failed.'
                                                               ' Please ensure that the website configuration is correct or try switching to the nginx service before using it.'))

        # 更新服务
        public.M('sites').where('id = ?', (site_id,)).update({"service_type": service_type})

        # 重启与重载服务，避免重启后配置仍不生效
        if args.get('is_reload', True):
            public.webservice_operation('nginx', 'reload')
            public.webservice_operation(service_type, 'reload')

        public.write_log_gettext('Site manager	', 'Successfully switched the website [{}] from [{}] service to [{}]!',
                                 (site['name'],old_type,service_type))
        # 统计次数
        public.set_module_logs('Multi-WebServer', f'switch_webservice-{site['project_type']}')
        return public.return_message(0, 0, public.lang('Successfully switched to {}', service_type))

    # 获取当前网站服务类型
    def get_current_webservice(self, args: public.dict_obj):
        try:
            if not public.get_multi_webservice_status():
                return public.return_message(0, 0, public.get_webserver())

            service_type = public.M('sites').where('id = ?', (args.site_id,)).field('service_type').find()

            if not service_type['service_type']:
                return public.return_message(0, 0, 'nginx')

            return public.return_message(0, 0, service_type['service_type'])
        except Exception as e:
            return public.return_message(-1, 0, public.lang('The type of website service obtained is incorrect'))

    # 多服务检查与修复
    def multi_service_check_repair(self, args=None):
        from panelModelV2.publicModel import main
        public_obj = main()

        if not public.get_multi_webservice_status():
            return public.return_message(-1,0,'Please enable Multi-WebEngine Hosting first')

        try:
            # 尝试重新修改配置
            self.cheak_port_conflict('enable')

            ok, msg = self.ols_update_config('enable')
            if not ok:
                raise ValueError(msg)

            ok, msg = self.apache_update_config('enable')
            if not ok:
                raise ValueError(msg)

            public.webservice_operation('nginx')

            # 检查服务状态
            for service in ['openlitespeed', 'apache', 'nginx']:
                args = public.to_dict_obj({'name': service})
                res = public_obj.get_soft_status(args)
                if res['status'] != 0:
                    raise ValueError(public.lang("Service startup failed: {}", service))
                if not res['message']['s_status']:
                    raise ValueError(public.lang("Service startup failed: {}", service))

            return public.return_message(0, 0, public.lang('Repaired successfully'))
        except Exception as e:
            print(e)
            return public.return_message(-1,0,public.lang('An error occurred in multi-service and the repair failed. Please try to close multi-service and then reopen it!:{}',str(e)))

    # 批量切换网站服务
    def batch_switch_website_services(self, site_list, service_type):
        try:
            res = []
            for site_id in site_list:
                site = public.M('sites').where('id = ?', (site_id,)).field('id,name,path,project_type,service_type').find()

                if not site:
                    continue

                if site['service_type'] == service_type or (not site['service_type'] and service_type == 'nginx'):
                    res.append({site['name'] : public.lang('The current website service is already {}', service_type)})
                    continue

                old_type = site['service_type'] if site['service_type'] else 'nginx'
                config_path = os.path.join(public.get_panel_path(), 'vhost', 'nginx', site['name'] + '.conf')

                # 检测是否与用户配置的反向代理冲突
                ok, msg= self.check_switch_service(site['name'],site['id'],site['service_type'],site['project_type'])
                if not ok:
                    res.append({site['name'] : msg })
                    continue

                # 切换服务,apache需同步修改虚拟主机端口
                if service_type == 'apache':
                    path = os.path.join(public.get_panel_path(), 'vhost', 'apache', site['name'] + '.conf')
                    if os.path.exists(path):
                        content = public.readFile(path)
                        content = content.replace(f'*:80', f'*:8288')
                        content = content.replace(f'*:443', f'*:443')
                        public.writeFile(path, content)
                    else:
                        res.append({site['name']: public.lang('Theconfiguration file does not exist')})
                        continue

                ok = self.nginx_update_config(service_type, config_path, old_type, site['name'], site['path'], site['id'])
                if not ok:
                    res.append({site['name']: public.lang('The configuration modification failed.')})
                    continue

                # 更新服务
                public.M('sites').where('id = ?', (site_id,)).update({"service_type": service_type})
                res.append({site['name']: 'Success'})
                # 统计次数
                public.set_module_logs('Multi-WebServer', f'switch_webservice-{site['project_type']}')

            # 重启与重载服务，避免重启后配置仍不生效
            public.webservice_operation('nginx', 'reload')
            public.webservice_operation(service_type, 'reload')

            return True, res
        except Exception as e:
            return True, e

    # 检测是否存在反向代理冲突
    def cheak_reverse_proxy(self,name):
        dict_obj = public.to_dict_obj({'sitename': name})
        proxy = self.GetProxyList(dict_obj)
        proxy_list = proxy["message"] if proxy['status'] == 0 else []

        for proxy in proxy_list:
            if proxy['proxydir'] in ['/', '/*']:
                # dict_obj = public.to_dict_obj({'sitename': name,'proxyname': proxy['proxyname']})
                # self.RemoveProxy(dict_obj)
                return False
        return True

    # 判断是否存在子目录绑定
    def cheak_dirbinding(self,site_id):
        try:
            obj = public.to_dict_obj({'id':site_id})
            dir_data = self.GetDirBinding(obj)
            if dir_data['status'] != 0:
                return

            dir = dir_data['message']['binding']
            if dir:
                for i in dir:
                    obj_dir = public.to_dict_obj({'id':i['id']})
                    self.DelDirBinding(obj_dir)
            return
        except Exception as e:
            return

    # 检测node项目，多服务下默认走nginx
    def check_node_project(self, site_name, is_ = 'enable'):
        conf = os.path.join(public.get_panel_path(),'vhost', 'apache', f'node_{site_name}.conf')

        # 使多服务下apache文件不生效
        if is_ == 'enable':
            if os.path.exists(conf):
                shutil.move(conf, conf + '.barduo')
        else:
            if os.path.exists(conf + '.barduo'):
                shutil.move(conf + '.barduo', conf )
        return True

    # 网站回滚
    def website_rollback(self, get):
        try:
            get.validate([
                Param('site_id').String(),
            ], [
                public.validate.trim_filter(),
            ])
        except Exception as ex:
            return public.return_message(-1, 0, str(ex))

        site = public.M('sites').where('id = ?', (get.site_id,)).field('id,name,path,service_type').find()
        if not site:
            return public.return_message(-1, 0, 'The website does not exist.')

        conf_path = os.path.join(public.get_panel_path(),'vhost','nginx',site['name']+'.conf')
        if not os.path.exists(conf_path + '.bar.bar'):
            return public.return_message(-1, 0, public.lang('The backed-up configuration file does not exist: {}',site['name']))

        # 判断上一次服务类型
        conf_bar = public.readFile(conf_path + '.bar.bar')
        if ':8188' in conf_bar:
            service_type = 'openlitespeed'
        elif ':8288' in conf_bar:
            service_type = 'apache'
        else:
            service_type = 'nginx'

        res  = self.switch_webservice(public.to_dict_obj({'site_id': get.site_id, 'service_type': service_type, 'website_rollback': True}))
        if res['status'] != 0:
            return public.return_message(-1, 0, res['message'])

        # 写入备份文件
        public.writeFile(conf_path, conf_bar)
        return public.return_message(0, 0, public.lang('Successful recovery'))

    # 服务安装统计
    def service_install_count(self, get):
        if get.get('type', '') == 'multi':
            public.set_module_logs('WebServer-install', f'multi_service_install_count')
        elif get.get('type', '') == 'single':
            public.set_module_logs('WebServer-install', f'service_install_count')
        return public.return_message(0, 0,'')

    # 切换服务检测
    def check_switch_service(self, site_name, site_id, service_type,p_type):
        try:
            # 检测nginx配置冲突
            ok = self.CheckLocation(public.to_dict_obj({'sitename': site_name}))
            if ok['status'] != 0 and service_type not in ['apache', 'openlitespeed'] and p_type != 'WP2' :
                raise ValueError( public.lang('There are global proxy or url rewriting conflicts on the website. Please delete it and try again!'))

            # 检测是否存在反向代理冲突
            dict_obj = public.to_dict_obj({'sitename': site_name})
            proxy = self.GetProxyList(dict_obj)
            proxy_list = proxy["message"] if proxy['status'] == 0 else []

            if proxy_list :
                raise ValueError(
                    public.lang('This website has a reverse proxy. Please delete it and try again!'))

            # for proxy in proxy_list:
            #     if proxy['proxydir'] in ['/', '/*']:
            #         # dict_obj = public.to_dict_obj({'sitename': name,'proxyname': proxy['proxyname']})
            #         # self.RemoveProxy(dict_obj)
            #         raise ValueError( public.lang('The website has configured a global reverse proxy. Please cancel it first!'))

            # 检测子目录冲突
            obj = public.to_dict_obj({'id':site_id})
            dir_data = self.GetDirBinding(obj)
            if dir_data['status'] != 0:
                raise  ValueError('Subdirectory detection error')

            dir = dir_data['message']['binding']
            if dir:
                raise  ValueError(public.lang('The website is configured with subdirectory domain name binding. Please cancel it first!'))
                # for i in dir:
                #     obj_dir = public.to_dict_obj({'id':i['id']})
                #     self.DelDirBinding(obj_dir)

            return True,''
        except Exception as e:
            return False, str(e)

    # 处理网站自定义端口冲突
    def cheak_port_conflict(self,status='enable'):
        apache_path = os.path.join(public.get_panel_path(), 'vhost', 'apache')
        ols_path = os.path.join(public.get_panel_path(), 'vhost', 'openlitespeed','listen')
        sites_port = public.M('domain').where('port <> ?', (80)).field('pid,name,port').select()
        apache_port = '8288'

        for site_port in sites_port:
            site_name = public.M('sites').where('id = ?', (site_port['pid'],)).getField('name')

            # 处理apache占用
            apache_conf_path = os.path.join(apache_path, site_name+'.conf')
            if os.path.exists(apache_conf_path):
                if status =='enable':
                    content = public.readFile(apache_conf_path)
                    content = content.replace(f'*:{site_port['port']}', f'*:{apache_port}')
                    content = content.replace(f'[::]:{site_port['port']}', f'[::]:{apache_port}')
                    public.writeFile(apache_conf_path, content)
                else:
                    content = public.readFile(apache_conf_path)
                    vhost_pattern = r'<VirtualHost.*?</VirtualHost>'
                    vhost_list = re.findall(vhost_pattern, content, re.DOTALL | re.MULTILINE)
                    if vhost_list:
                        conf = ''
                        for i in range(len(vhost_list)):
                            if site_name+'.'+ str(site_port['port']) in vhost_list[i]:
                                vhost_list[i] = vhost_list[i].replace(f'*:{apache_port}', f'*:{site_port['port']}')
                                vhost_list[i] = vhost_list[i].replace(f'[::]:{apache_port}', f'[::]:{site_port['port']}')
                            conf += vhost_list[i] + '\n\n'
                        public.writeFile(apache_conf_path, conf)

            # 处理ols占用
            ols_conf_path = os.path.join(ols_path, str(site_port['port']) +'.conf')
            ols_80conf = os.path.join(ols_path, '80.conf')

            if status == 'enable':
                if os.path.exists(ols_conf_path):
                    shutil.move(ols_conf_path, ols_conf_path + '.barduo')

                    # 插入80端口
                    get_obj = public.to_dict_obj({'port':'80','webname': site_name,'domain':site_port['name']})
                    self.openlitespeed_domain(get_obj)
            else:
                if os.path.exists(ols_conf_path + '.barduo'):
                    shutil.move(ols_conf_path + '.barduo', ols_conf_path )

                # 删除80.conf中的自定义端口
                if os.path.exists(ols_80conf):
                    conf = public.readFile(ols_80conf)
                    map_pattern = r'map\s+{}\s+(.*)'.format(re.escape(site_name))
                    match = re.search(map_pattern, conf)

                    if match:
                        domains = match.group(1).split(',')
                        if site_port['name'] in domains:
                            domains.remove(site_port['name'])
                            new_domains_str = ",".join(domains)
                            new_map_line = f"map\t{site_name} {new_domains_str}"
                            updated_conf = re.sub(map_pattern, new_map_line, conf)

                            public.writeFile(ols_80conf, updated_conf)

        # 取消主配置文件的端口监听
        self.cheak_apache_httpconf(status)
        return True

    # 检测apache主配置文件端口监听
    def cheak_apache_httpconf(self,status):
        config_path = '/www/server/apache/conf/httpd.conf'
        if os.path.exists(config_path):
            listen_pattern = r'(?i)^\s*listen\b.*$'  # 开启匹配
            listen_d = r'(?i)^\s*#listen\b.*$'      # 关闭匹配

            content = public.readFile(config_path)
            if status == 'enable':
                port_listen  = re.findall(listen_pattern, content, re.MULTILINE)
                for port in port_listen:
                    if port not in ['Listen 80','Listen 443','Listen 8288','Listen 8290'] and ':' not in port:  # 不处理手动自定义端口号
                        content = content.replace(port, '#' + port)
                public.writeFile(config_path, content)
            else:
                port_listen  = re.findall(listen_d, content, re.MULTILINE)
                for port in port_listen:
                    if port not in ['Listen 80','Listen 443'] and ':' not in port:
                        content = content.replace(port, port[1:])
                public.writeFile(config_path, content)

        return True

    # 获取apache所有网站配置文件
    def get_apache_site_conf(self):
        pata =os.path.join(public.get_panel_path() , 'vhost' ,'apache')
        if not os.path.exists(pata):
            return []

        conf_files = []
        for entry in os.listdir(pata):
            full_path = os.path.join(pata, entry)

            if os.path.isfile(full_path) and entry.endswith('.conf'):
                conf_files.append(full_path)

        return conf_files
    # ======================网站多服务 end==============================

    # ========================网站全局设置 start=========================
    # 获取网站全局设置
    def get_site_global(self, get):
        status = {}
        cdn_ip_conf_file = "{}/vhost/nginx/real_cdn_ip.conf".format(public.get_panel_path())


        # 获取cdn状态, 非nginx或多服务下默认为false
        if public.get_webserver() in ['apache', 'openlitespeed']:
            status = {"cdn_status": False, "white_ips": "", "header_cdn": "", "cdn_recursive": False}
        else:
            cdn_conf = public.readFile(cdn_ip_conf_file)
            if not cdn_conf:
                # 判断主配置中存在自定义
                cdn_status = False
                nginx_path = public.GetConfigValue('setup_path') + '/nginx/conf/nginx.conf'
                config = public.readFile(nginx_path)
                if config:
                    if 'real_ip_header' in config and 'set_real_ip_from' in config:
                        cdn_status = True

                status = {"cdn_status": cdn_status, "white_ips": "", "header_cdn": "", "cdn_recursive": False}
            else:
                status['cdn_status'] = True
                status['cdn_recursive'] = False
                status['header_cdn'] = ""
                status['white_ips'] = ""
                try:
                    if cdn_conf:
                        white_ips = ""
                        for line in cdn_conf.split('\n'):
                            dat = line.strip().strip(";")
                            if dat.startswith("set_real_ip_from"):
                                white_ips += dat.split()[1] + "\n"
                            elif dat.startswith("real_ip_header"):
                                status['header_cdn'] = dat.split()[1]
                            elif dat.startswith("real_ip_recursive"):
                                status['cdn_recursive'] = True
                        if white_ips:
                            status['white_ips'] = white_ips.strip("\n")
                except:
                    return public.return_message(-1, 0, public.lang("An error occurred when parsing the {} configuration file. Please check if the format is normal.",cdn_ip_conf_file))

        # ===

        return public.return_message(0, 0,status)

    # 设置全局配置
    def set_site_global(self, get):
        # 设置CDN
        if public.get_webserver() in ['apache', 'openlitespeed'] and get.get('cdn_switch', 0) in [1,'1']:
            return public.return_message(-1,0,public.lang("CDN Settings only support nginx mode!") )

        ok, msg = self. set_cdn_status(get)
        if not ok:
            return public.return_message(-1,0, f"CDN setup failed: {msg}" )

        return public.return_message(0, 0 ,public.lang("The overall success of the website"))

    # 设置CDN代理状态
    def set_cdn_status(self, get):
        try:
            cdn_switch = int(get.get('cdn_switch', 0))
            header_cdn = get.get("header_cdn").strip()
            if not header_cdn and cdn_switch == 1:
                return False,public.lang("CDN header cannot be empty！")

            white_ips = get.get("white_ips", "")
            recursive = get.get("recursive", True)

            # 处理nginx访问日志ip
            white_ip_list = []
            if white_ips:
                import ipaddress
                for ip in white_ips.split("\n"):
                    ip = ip.strip()
                    try:
                        ipaddress.ip_address(ip)
                        white_ip_list.append(ip)
                    except:
                        try:
                            ipaddress.ip_network(ip)
                            white_ip_list.append(ip)
                        except:
                            continue
            white_ip_list = ["0.0.0.0/0", "::/0"] if not white_ip_list else white_ip_list

            if re.search(r"\s+", header_cdn):
                return False, public.lang("The request header cannot contain Spaces")

            cdn_ip_conf_file = "{}/vhost/nginx/real_cdn_ip.conf".format(public.get_panel_path())
            if not os.path.isfile(cdn_ip_conf_file):
                public.writeFile(cdn_ip_conf_file, '')
                nginx_conf_file = public.GetConfigValue('setup_path') + '/nginx/conf/nginx.conf'
                config = public.readFile(nginx_conf_file)
                if not config:
                    return False, public.lang('The nginx configuration file does not exist')

                data_list = []
                for line in config.split('\n'):
                    if 'real_ip_header' in line or 'set_real_ip_from' in line:
                        continue
                    data_list.append(line)
                public.writeFile(nginx_conf_file, '\n'.join(data_list))
                if public.checkWebConfig() is not True:
                    return False, public.lang('There is an error in the configuration file. Please check it!')
                else:
                    public.webservice_operation('nginx', 'reload')
            if cdn_switch in (1, '1'):
                real_ip_from = ""
                for white_ip in white_ip_list:
                    real_ip_from += "set_real_ip_from {};\n".format(white_ip)
                public.WriteFile(cdn_ip_conf_file, """
            {}real_ip_header {};{}
            """.format(real_ip_from, header_cdn, "" if recursive not in ['true', True] else "\nreal_ip_recursive on;"))
                public.webservice_operation('nginx','reload')

            else:
                public.writeFile(cdn_ip_conf_file, '')
                public.webservice_operation('nginx','reload')
            return True, ''
        except Exception as e:
            return False, str(e)

    # 获取常用CDN 预设模板
    def get_cdn_ip(self, get):
        import requests
        header_cdn = get.get("header_cdn", "")

        if not header_cdn:
            return public.return_message(-1, 0, "The request header cannot be empty")

        all_ips = []

        # 获取cloudflare IP 段
        if header_cdn == 'Cf-Connecting-IP':
            url_v4 = "https://www.cloudflare.com/ips-v4"
            url_v6 = "https://www.cloudflare.com/ips-v6"
            try:
                # 获取 IPv4 地址段
                response_v4 = requests.get(url_v4, timeout=10)
                if response_v4.status_code == 200:
                    ips_v4 = [ip.strip() for ip in response_v4.text.splitlines() if ip.strip()]
                    all_ips.extend(ips_v4)

                # 获取 IPv6 地址段
                response_v6 = requests.get(url_v6, timeout=10)
                if response_v6.status_code == 200:
                    ips_v6 = [ip.strip() for ip in response_v6.text.splitlines() if ip.strip()]
                    all_ips.extend(ips_v6)

            except Exception as e:
                pass
        # 默认返回
        if not all_ips:
            all_ips = ["0.0.0.0/0", "::/0"]

        return public.return_message(0, 0, "\n".join(all_ips))
    # ========================网站全局设置 end=========================
