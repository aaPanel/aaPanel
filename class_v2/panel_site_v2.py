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
import io, re, public, os, sys, shutil, json, hashlib, socket, time

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
            public.WriteLog('信息获取', "{}失败: {}".format(self.conf_dir, str(e)))

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
</VirtualHost>''' % (vName, self.sitePort, self.sitePath, acc, self.siteName, self.siteName,
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
            description=public.get_msg_gettext('# Forbidden files or directories'),
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
                create_failed[domains[0]] = public.get_msg_gettext('There was an error creating, please try again.')
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

    # 添加站点
    def AddSite(self, get, multiple=None):
        # 校验参数
        try:
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

            ], [
                public.validate.trim_filter(),
            ])
        except Exception as ex:
            public.print_log("error info: {}".format(ex))
            return public.return_message(-1, 0, str(ex))

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

        import json, files

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
            return_message = public.return_msg_gettext(False, 'Port range is incorrect! should be between 100-65535')
            del return_message['status']
            return public.return_message(-1, 0, return_message['msg'])

        for domain in siteMenu['domainlist']:
            if not len(domain.split(':')) == 2:
                continue
            if not public.checkPort(domain.split(':')[1]):
                return_message = public.return_msg_gettext(False,
                                                           'Port range is incorrect! should be between 100-65535')
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

        # 添加更多域名
        for domain in siteMenu['domainlist']:
            get.domain = domain
            get.webname = self.siteName
            get.id = str(get.pid)
            self.AddDomain(get, multiple)

        sql.table('domain').add('pid,name,port,addtime', (get.pid, self.siteName, self.sitePort, public.getDate()))

        data = {}
        data['siteStatus'] = True
        data['siteId'] = get.pid

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
            get.name = get.datauser
            get.db_user = get.datauser
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
                    public.M('databases').where('name=?', (datauser,)).update({"pid":get.pid})
        if not multiple:
            public.serviceReload()
        data = self._set_ssl(get, data, siteMenu)
        data = self._set_redirect(get, data['message'])
        public.write_log_gettext('Site manager', 'Successfully added site [{}]!', (self.siteName,))
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
            ], [
                public.validate.trim_filter(),
            ])
        except Exception as ex:
            public.print_log("error info: {}".format(ex))
            return public.return_message(-1, 0, str(ex))

        from copy import deepcopy
        args_dup = public.to_dict_obj(deepcopy(args.get_items()))

        data = self.AddSite(args_dup)

        if int(data.get('status', 0)) != 0:
            return data

        data = data.get('message', {})

        if int(data.get('databaseStatus', 0)) != 1:
            raise public.HintException(public.get_msg_gettext('Database creation failed. Please check mysql running status and try again.'))

        return self.deploy_wp(public.to_dict_obj({
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
                del_failed[get.webname] = public.get_msg_gettext('There was an error deleting, please try again.')
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
        public.write_log_gettext('Site manager', 'Successfully deleted site!', (siteName,))

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

        if not 'domain' in get: return public.return_message(-1, 0, 'Please enter the host domain name')
        if len(get.domain) < 3: return public.return_message(-1, 0, 'Domain cannot be empty!')
        domains = get.domain.replace(' ', '').split(',')

        for domain in domains:
            if domain == "": continue
            domain = domain.strip().split(':')
            get.domain = self.ToPunycode(domain[0]).lower()
            get.port = '80'
            # 判断通配符域名格式
            if get.domain.find('*') != -1 and get.domain.find('*.') == -1:
                return public.return_message(-1, 0, 'Domain name format is incorrect!')

            # 判断域名格式
            reg = r"^([\w\-\*]{1,100}\.){1,24}([\w\-]{1,24}|[\w\-]{1,24}\.[\w\-]{1,24})$"
            if not re.match(reg, get.domain): return public.return_message(-1, 0, 'Format of domain is invalid!')

            # 获取自定义端口
            if len(domain) == 2:
                get.port = domain[1]
            if get.port == "": get.port = "80"

            # 判断端口是否合法
            if not public.checkPort(get.port): return public.return_message(-1, 0,
                                                                            'Port range is incorrect! should be between 100-65535')
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

        return public.return_message(0, 0, 'Successfully added site!')

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
            listen_conf = """
listener Default%s{
    address *:%s
    secure 0
    map %s %s
}
""" % (get.port, get.port, get.webname, get.domain)
        # 保存配置文件
        public.writeFile(listen_file, listen_conf)
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

        port = get.port
        siteName = get.webname
        newDomain = get.domain
        find = public.M('sites').where("id=?", (get.id,)).field('id,name,path').find()
        sitePath = find['path']
        siteIndex = 'index.php index.html index.htm default.php default.html default.htm'

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
            if conf.find('<VirtualHost *:443>') != -1:
                repV = r"<VirtualHost\s+\*\:443>(.|\n)*</VirtualHost>"
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
</VirtualHost>''' % (port, sitePath, siteName, port, newDomain, public.GetConfigValue('logs_path') + '/' + siteName,
                     public.GetConfigValue('logs_path') + '/' + siteName, phpConfig, sitePath, apaOpt, siteIndex)
            conf += "\n\n" + newconf

        # 添加端口
        if port != '80' and port != '888': self.apacheAddPort(port)

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
                del_failed[tmp] = public.get_msg_gettext('There was an error deleting, please try again.')
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

        if not 'id' in get: return public.return_message(-1, 0, 'Please choose a domain name')
        if not 'port' in get: return public.return_message(-1, 0, 'Please choose a port')
        sql = public.M('domain')
        id = get['id']
        port = get.port
        find = sql.where("pid=? AND name=?", (get.id, get.domain)).field('id,name').find()
        domain_count = sql.table('domain').where("pid=?", (id,)).count()
        if domain_count == 1: return public.return_message(-1, 0, 'Last domain cannot be deleted!')

        # nginx
        file = self.setupPath + '/panel/vhost/nginx/' + get['webname'] + '.conf'
        conf = public.readFile(file)
        if conf:
            # 删除域名
            rep = r"server_name\s+(.+);"
            tmp = re.search(rep, conf).group()
            newServerName = tmp.replace(' ' + get['domain'] + ';', ';')
            newServerName = newServerName.replace(' ' + get['domain'] + ' ', ' ')
            conf = conf.replace(tmp, newServerName)

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

        sql.table('domain').where("id=?", (find['id'],)).delete()
        public.write_log_gettext('Site manager', 'Site [{}] deleted domain [{}] successfully!',
                                 (get.webname, get.domain))
        if not multiple:
            public.serviceReload()
        return public.return_message(0, 0, 'Successfully deleted')

    # openlitespeed删除域名
    def _del_ols_domain(self, get):
        conf_dir = '/www/server/panel/vhost/openlitespeed/listen/'
        if not os.path.exists(conf_dir):
            return return_message(-1, 0, 'directory not exists:' + conf_dir)
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
        return public.return_message(0, 0, 'Setup successfully!')

    # 检查域名是否解析
    def CheckDomainPing(self, get):
        try:
            epass = public.GetRandomString(32)
            spath = get.path + '/.well-known/pki-validation'
            if not os.path.exists(spath): public.ExecShell("mkdir -p '" + spath + "'")
            public.writeFile(spath + '/fileauth.txt', epass)
            result = public.httpGet(
                'http://' + get.domain.replace('*.', '') + '/.well-known/pki-validation/fileauth.txt')
            if result == epass: return public.return_message(0, 0, "")
            return public.return_message(-1, 0, "")
        except:
            return public.return_message(-1, 0, "")

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
            return_message = public.return_msg_gettext(False, 'Private Key ERROR, please check!')
            del return_message['status']
            return public.return_message(-1, 0, return_message['msg'])
        if (get.csr.find('CERTIFICATE') == -1):
            return_message = public.return_msg_gettext(False, 'Certificate ERROR, please check!')
            del return_message['status']
            return public.return_message(-1, 0, return_message['msg'])
        public.writeFile('/tmp/cert.pl', get.csr)
        if not public.CheckCert('/tmp/cert.pl'):
            return_message = public.return_msg_gettext(False, 'Error getting certificate')
            del return_message['status']
            return public.return_message(-1, 0, return_message['msg'])
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
        if result['status'] == -1: return result
        isError = public.checkWebConfig()

        if (type(isError) == str):
            if os.path.exists(path): shutil.rmtree(backup_cert)
            shutil.move(backup_cert, path)
            return_message = public.return_msg_gettext(False,
                                                       'ERROR: <br><a style="color:red;">' + isError.replace("\n",
                                                                                                             '<br>') + '</a>')
            del return_message['status']
            return public.return_message(-1, 0, return_message['msg'])
        public.serviceReload()

        if os.path.exists(path + '/partnerOrderId'): os.remove(path + '/partnerOrderId')
        if os.path.exists(path + '/certOrderId'): os.remove(path + '/certOrderId')
        p_file = '/etc/letsencrypt/live/' + get.siteName
        if os.path.exists(p_file): shutil.rmtree(p_file)
        public.write_log_gettext('Site manager', 'Certificate saved!')

        # 清理备份证书
        if os.path.exists(backup_cert): shutil.rmtree(backup_cert)
        return_message = public.return_msg_gettext(True, 'Certificate saved!')
        del return_message['status']
        return public.return_message(0, 0, return_message['msg'])

    # 获取运行目录
    def GetRunPath(self, get):
        if not hasattr(get, 'id'):
            if hasattr(get, 'siteName'):
                get.id = public.M('sites').where('name=?', (get.siteName,)).getField('id')
            else:
                get.id = public.M('sites').where('path=?', (get.path,)).getField('id')
        if not get.id: return public.return_message(-1, 0, "")
        if type(get.id) == list: get.id = get.id[0]['id']
        result = self.GetSiteRunPath(get)['message']
        if 'runPath' in result:
            return public.return_message(0, 0, result['runPath'])
        return public.return_message(-1, 0, "")

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
            conf = """
listener SSL443 {
  map                     BTSITENAME BTDOMAIN
  address                 *:443
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
}
"""

        else:
            rep = r'listener\s*SSL443\s*{'
            map = '\n  map {s} {s}'.format(s=siteName)
            conf = re.sub(rep, 'listener SSL443 {' + map, conf)
        domain = ",".join(self._get_site_domains(siteName))
        conf = conf.replace('BTSITENAME', siteName).replace('BTDOMAIN', domain)
        public.writeFile(listen_conf, conf)

    def _get_ap_static_security(self, ap_conf):
        if not ap_conf: return public.return_message(0, 0, '')
        ap_static_security = re.search('#SECURITY-START(.|\n)*#SECURITY-END', ap_conf)
        if ap_static_security:
            return public.return_message(0, 0, ap_static_security.group())
        return public.return_message(0, 0, '')

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

        ng_file = file
        conf = public.readFile(file)

        # 是否为子目录设置SSL
        # if hasattr(get,'binding'):
        #    allconf = conf;
        #    conf = re.search("#BINDING-"+get.binding+"-START(.|\n)*#BINDING-"+get.binding+"-END",conf).group()

        if conf:
            if conf.find('ssl_certificate') == -1:
                sslStr = """#error_page 404/404.html;
    ssl_certificate    /www/server/panel/vhost/cert/%s/fullchain.pem;
    ssl_certificate_key    /www/server/panel/vhost/cert/%s/privkey.pem;
    ssl_protocols TLSv1.1 TLSv1.2%s;
    ssl_ciphers EECDH+CHACHA20:EECDH+CHACHA20-draft:EECDH+AES128:RSA+AES128:EECDH+AES256:RSA+AES256:EECDH+3DES:RSA+3DES:!MD5;
    ssl_prefer_server_ciphers on;
    ssl_session_cache shared:SSL:10m;
    ssl_session_timeout 10m;
    add_header Strict-Transport-Security "max-age=31536000";
    error_page 497  https://$host$request_uri;
""" % (get.first_domain, get.first_domain, self.get_tls13())
                if (conf.find('ssl_certificate') != -1):
                    if 'isBatch' not in get:
                        public.serviceReload()
                        return_message = public.return_msg_gettext(True, 'SSL turned on!')
                        del return_message['status']
                        return public.return_message(0, 0, return_message['msg'])
                    else:
                        return public.return_message(0, 0, "")

                conf = conf.replace('#error_page 404/404.html;', sslStr)
                conf = re.sub(r"\s+\#SSL\-END", "\n\t\t#SSL-END", conf)

                # 添加端口
                rep = r"listen.*[\s:]+(\d+).*;"
                tmp = re.findall(rep, conf)
                if not public.inArray(tmp, '443'):
                    listen_re = re.search(rep, conf)
                    if not listen_re:
                        conf = re.sub(r"server\s*{\s*", "server\n{\n\t\tlisten 80;\n\t\t", conf)
                        listen_re = re.search(rep, conf)
                    listen = listen_re.group()
                    versionStr = public.readFile('/www/server/nginx/version.pl')
                    http2 = ''
                    if versionStr:
                        if versionStr.find('1.8.1') == -1: http2 = ' http2'
                    default_site = ''
                    if conf.find('default_server') != -1: default_site = ' default_server'

                    listen_ipv6 = ';'
                    if self.is_ipv6: listen_ipv6 = ";\n\t\tlisten [::]:443 ssl" + http2 + default_site + ";"
                    conf = conf.replace(listen, listen + "\n\t\tlisten 443 ssl" + http2 + default_site + listen_ipv6)
                shutil.copyfile(file, self.nginx_conf_bak)

                public.writeFile(file, conf)

        # Apache配置
        file = self.setupPath + '/panel/vhost/apache/' + siteName + '.conf'
        # if not os.path.exists(file): file = self.setupPath + '/panel/vhost/apache/node_' + siteName + '.conf'
        is_node_apache = False
        if not os.path.exists(file):
            is_node_apache = True
            file = self.setupPath + '/panel/vhost/apache/node_' + siteName + '.conf'
        conf = public.readFile(file)
        ap_static_security = self._get_ap_static_security(conf)
        if conf:
            ap_proxy = self.get_apache_proxy(conf)
            if conf.find('SSLCertificateFile') == -1 and conf.find('VirtualHost') != -1:
                find = public.M('sites').where("name=?", (siteName,)).field('id,path').find()
                tmp = public.M('domain').where('pid=?', (find['id'],)).field('name').select()
                domains = ''
                for key in tmp:
                    domains += key['name'] + ' '
                path = (find['path'] + '/' + self.GetRunPath(get))['message']['result'].replace('//', '/')
                index = 'index.php index.html index.htm default.php default.html default.htm'

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
                    version = public.get_php_version_conf(conf)
                    if len(version) < 2:
                        if 'isBatch' not in get:
                            return_message = public.return_msg_gettext(False, 'Failed to get PHP version!')
                            del return_message['status']
                            return public.return_message(-1, 0, return_message['msg'])
                        else:
                            return public.return_message(-1, 0, "")
                    phpConfig = '''
    #PHP
    <FilesMatch \\.php$>
            SetHandler "proxy:%s"
    </FilesMatch>
    ''' % (public.get_php_proxy(version, 'apache'),)
                    apaOpt = 'Require all granted'

                sslStr = r'''%s<VirtualHost *:443>
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
    SSLCipherSuite EECDH+CHACHA20:EECDH+CHACHA20-draft:EECDH+AES128:RSA+AES128:EECDH+AES256:RSA+AES256:EECDH+3DES:RSA+3DES:!MD5
    SSLProtocol All -SSLv2 -SSLv3 -TLSv1
    SSLHonorCipherOrder On
    %s
    %s

    #DENY FILES
     <Files ~ (\.user.ini|\.htaccess|\.git|\.svn|\.project|LICENSE|README.md)$>
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
</VirtualHost>''' % (vName, path, siteName, domains, public.GetConfigValue('logs_path') + '/' + siteName,
                     public.GetConfigValue('logs_path') + '/' + siteName, ap_proxy, get.first_domain, get.first_domain,
                     ap_static_security, phpConfig, path, apaOpt, index)
                conf = conf + "\n" + sslStr
                self.apacheAddPort('443')
                shutil.copyfile(file, self.apache_conf_bak)
                public.writeFile(file, conf)
                if is_node_apache:  # 兼容Nodejs项目
                    from projectModel.nodejsModel import main
                    m = main()
                    project_find = m.get_project_find(siteName)
                    m.set_apache_config(project_find)
        # OLS
        self.set_ols_ssl(get, siteName)
        isError = public.checkWebConfig()
        if (isError != True):
            if os.path.exists(self.nginx_conf_bak): shutil.copyfile(self.nginx_conf_bak, ng_file)
            if os.path.exists(self.apache_conf_bak): shutil.copyfile(self.apache_conf_bak, file)
            public.ExecShell("rm -f /tmp/backup_*.conf")
            if 'isBatch' not in get:
                return_message = public.return_msg_gettext(False,
                                                           public.get_msg_gettext(
                                                               'Certificate ERROR, please check!') + ': <br><a style="color:red;">' + isError.replace(
                                                               "\n", '<br>') + '</a>')
                del return_message['status']
                return public.return_message(-1, 0, return_message['msg'])
            else:
                return public.return_message(-1, 0, "")

        sql = public.M('firewall')
        import firewalls
        get.port = '443'
        get.ps = 'HTTPS'
        if not public.M('firewall').where('port=?', ('443',)).count():
            firewalls.firewalls().AddAcceptPort(get)
        public.serviceReload()
        if 'isBatch' not in get: firewalls.firewalls().AddAcceptPort(get)
        if 'isBatch' not in get: public.serviceReload()
        self.save_cert(get)
        public.write_log_gettext('Site manager', 'Site [{}] turned on SSL successfully!', (siteName,))
        result = public.return_msg_gettext(True, 'SSL turned on!')
        result['csr'] = public.readFile('/www/server/panel/vhost/cert/' + get.siteName + '/fullchain.pem')
        result['key'] = public.readFile('/www/server/panel/vhost/cert/' + get.siteName + '/privkey.pem')
        del result['status']
        if 'isBatch' not in get:
            return public.return_message(0, 0, result)
        else:
            return public.return_message(0, 0, "")

    def save_cert(self, get):
        # try:
        import panel_ssl_v2 as panelSSL
        ss = panelSSL.panelSSL()
        get.keyPath = '/www/server/panel/vhost/cert/' + get.siteName + '/privkey.pem'
        get.certPath = '/www/server/panel/vhost/cert/' + get.siteName + '/fullchain.pem'
        return ss.SaveCert(get)
        return public.return_message(0, 0, "")
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
        public.serviceReload()
        return public.return_message(0, 0, 'SSL turned off!')

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
        if not os.path.exists(
                file): file = self.setupPath + '/panel/vhost/' + public.get_webserver() + '/node_' + siteName + '.conf'
        if public.get_webserver() == "openlitespeed":
            file = self.setupPath + '/panel/vhost/' + public.get_webserver() + '/detail/' + siteName + '.conf'
        conf = public.readFile(file)
        if not conf: return public.return_message(-1, 0, 'The specified website profile does not exist')

        if public.get_webserver() == 'nginx':
            keyText = 'ssl_certificate'
        elif public.get_webserver() == 'apache':
            keyText = 'SSLCertificateFile'
        else:
            keyText = 'openlitespeed/detail/ssl'

        status = True
        if (conf.find(keyText) == -1):
            status = False
            type = -1

        toHttps = self.IsToHttps(siteName)
        id = public.M('sites').where("name=?", (siteName,)).getField('id')
        domains = public.M('domain').where("pid=?", (id,)).field('name').select()
        cert_data = {}
        if csr:
            get.certPath = csrpath
            import panel_ssl_v2
            cert_data = panel_ssl_v2.panelSSL().GetCertName(get)
            if not cert_data:
                cert_data = {
                    'certificate': 0
                }

        email = public.M('users').where('id=?', (1,)).getField('email')
        if email == '287962566@qq.com': email = ''
        index = ''
        auth_type = 'http'
        if status == True:
            if type != 1:
                import acme_v3
                acme = acme_v3.acme_v2()
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
        # 作者 muluo
        # return {'status': status,'oid':oid, 'domain': domains, 'key': key, 'csr': csr, 'type': type, 'httpTohttps': toHttps,'cert_data':cert_data,'email':email,"index":index,'auth_type':auth_type}
        res = {'status': status, 'oid': oid, 'domain': domains, 'key': key, 'csr': csr, 'type': type,
               'httpTohttps': toHttps, 'cert_data': cert_data, 'email': email, "index": index, 'auth_type': auth_type}
        res['push'] = self.get_site_push_status(None, siteName, 'ssl')
        return public.return_message(0, 0, res)

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
            return public.return_message(0, 0, 'SITE_STOP_SUCCESS')
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

        if (public.get_webserver() != 'nginx'): return public.return_message(-1, 0,
                                                                             'Site Traffic Control only supports Nginx Web Server!')

        id = get.id
        if int(get.perserver) < 1 or int(get.perip) < 1 or int(get.perip) < 1:
            return public.return_message(-1, 0,
                                         'Concurrency restrictions, IP restrictions, traffic restrictions must be greater than 0')
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
                                         'ERROR: <br><a style="color:red;">' + isError.replace("\n", '<br>') + '</a>')

        public.serviceReload()
        public.write_log_gettext('Site manager', 'Site [{}] traffic control turned on!', (siteName,))
        return public.return_message(0, 0, 'Setup successfully!')

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
        siteInfo = public.M('sites').where("id=?", (id,)).field('id,path,name').find()
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
                return public.return_message(-1, 0, "Get enable php config failed!")
            tmp = tmp.groups()
            version = tmp[0]
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
                      public.get_msg_gettext('# Forbidden files or directories'), public.get_msg_gettext(
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
#BINDING-%s-END''' % (domain, port, webdir, domain, public.GetConfigValue('logs_path') + '/' + siteInfo['name'],
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
                del_failed[domain] = public.get_msg_gettext('There was an error deleting, please try again.')
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
        site = public.M('sites').where("id=?", (find['pid'],)).field('id,name,path').find()

        if (public.get_webserver() != 'nginx'):
            filename = site['path'] + '/' + find['path'] + '/.htaccess'
        else:
            filename = self.setupPath + '/panel/vhost/rewrite/' + site['name'] + '_' + find['path'] + '.conf'

        if hasattr(get, 'add'):
            public.writeFile(filename, '')
            if public.get_webserver() == 'nginx':
                file = self.setupPath + '/panel/vhost/nginx/' + site['name'] + '.conf'
                conf = public.readFile(file)
                domain = find['domain']
                rep = "\n#BINDING-" + domain + "-START(.|\n)+BINDING-" + domain + "-END"
                tmp = re.search(rep, conf).group()
                dirConf = tmp.replace('rewrite/' + site['name'] + '.conf;',
                                      'rewrite/' + site['name'] + '_' + find['path'] + '.conf;')
                conf = conf.replace(tmp, dirConf)
                public.writeFile(file, conf)
        data = {}
        return_status = -1
        if os.path.exists(filename):
            return_status = 0
            data['data'] = public.readFile(filename)
            data['rlist'] = ['0.default']
            webserver = public.get_webserver()
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
        if conf == False: return public.return_message(-1, 0, 'Configuration file not exist')
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
        return public.return_message(-1, 0, 'Failed to get, there is no default document in the configuration file')

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
        if not Index: return public.return_message(-1, 0, "Default index file cannot be empty")
        if get.Index.find('.') == -1: return public.return_message(-1, 0,
                                                                   'Default Document Format is invalid, e.g., index.html')

        if len(Index) < 3: return public.return_message(-1, 0, 'Default Document cannot be empty!')

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
        return public.return_message(0, 0, 'Setup successfully!')

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
        if Path == "" or id == '0': return public.return_message(-1, 0, 'Directory cannot be empty!')

        if not self.__check_site_path(Path): return public.return_message(-1, 0,
                                                                          'System critical directory cannot be used as site directory')
        if not public.check_site_path(Path):
            a, c = public.get_sys_path()
            return public.return_message(-1, 0,
                                         'Please do not set the website root directory to the system main directory: <br>{}'.format(
                                             "<br>".join(a + c)))

        SiteFind = public.M("sites").where("id=?", (id,)).field('path,name').find()
        if SiteFind["path"] == Path: return public.return_msg_gettext(False,
                                                                      'Same as original path, no need to change!')
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
        return public.return_message(0, 0, 'Successfully set')

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
        public.WriteLog('TYPE_SITE',
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
                    tmp['name'] = public.get_msg_gettext('Static')

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
            return public.return_message(0, 0, data)
        except:
            return public.return_message(-1, 0,
                                         'Apache2.2 does NOT support MultiPHP!,{}'.format(public.get_error_info()))

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
                set_phpv_failed[get.siteName] = public.get_msg_gettext('There was an error setting, please try again.')
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
            return public.return_message(-1, 0, 'Custom PHP configuration only supports Nginx')
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
                        return public.return_message(-1, 0,
                                                     'The PHP connection configuration cannot be empty when customizing the version!')

                    if not re.match(r"^(\d+\.\d+\.\d+\.\d+:\d+|unix:[\w/\.-]+)$", get.other):
                        return public.return_message(-1, 0,
                                                     'The PHP connection configuration format is incorrect, please refer to the example!')

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
            return public.return_message(-1, 0,
                                         'Setup failed, no enable-php-xx related configuration items were found in the website configuration file!')

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
        if not path: return public.return_message(-1, 0, 'Requested directory does not exist')
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
                return public.return_message(0, 0, 'Base directory turned off!')

            if conf and "session.save_path" in conf:
                rep = r"session.save_path\s*=\s*(.*)"
                s_path = re.search(rep, conf).groups(1)[0]
                public.writeFile(filename, conf + '\nopen_basedir={}/:/tmp/:{}'.format(path, s_path))
            else:
                public.writeFile(filename, 'open_basedir={}/:/tmp/'.format(path))
            public.ExecShell("chattr +i " + filename)
            public.set_site_open_basedir_nginx(siteName)
            public.serviceReload()
            return public.return_message(0, 0, 'Base directory turned on!')
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
            if not c: return public.return_message(-1, 0, "")
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
        return public.return_message(0, 0, "")

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
                get.proxyname = public.get_msg_gettext('Old proxy')
                get.type = 1
                get.proxydir = "/"
                get.advanced = 0
                get.cachetime = 1
                get.cache = 0
                get.subfilter = "[{\"sub1\":\"\",\"sub2\":\"\"},{\"sub1\":\"\",\"sub2\":\"\"},{\"sub1\":\"\",\"sub2\":\"\"}]"

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
        for i in proxyUrl:
            if i["sitename"] == sitename:
                proxylist.append(i)
        return public.return_message(0, 0, proxylist)

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
                del_failed[proxyname] = public.get_msg_gettext('There was an error deleting, please try again.')
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
                return public.return_message(0, 0, "")
        for i in conf_data:
            if i["sitename"] == get.sitename:
                if i["advanced"] != int(get.advanced):
                    return public.return_message(-1, 0, i)
        return public.return_message(0, 0, "")

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
                return public.return_message(-1, 0,
                                             'An error was detected in the configuration file. Please solve it before proceeding')
        if action == "create":
            if sys.version_info.major < 3:
                if len(get.proxyname) < 3 or len(get.proxyname) > 40:
                    return public.return_message(-1, 0, 'Database name cannot be more than 40 characters!')
            else:
                if len(get.proxyname.encode("utf-8")) < 3 or len(get.proxyname.encode("utf-8")) > 40:
                    return public.return_message(-1, 0, 'Database name cannot be more than 40 characters!')
        if self.__check_even(get, action):
            return public.return_message(-1, 0, 'Specified reverse proxy name or proxy folder already exists')
        # 判断代理，只能有全局代理或目录代理
        check_proxy_even = self.__check_proxy_even(get, action)
        if check_proxy_even['status'] == -1:
            return public.return_message(-1, 0, 'Cannot set both directory and global proxies')
        # 判断cachetime类型
        if get.cachetime:
            try:
                int(get.cachetime)
            except:
                return public.return_message(-1, 0, 'Please enter number')

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
                return public.return_message(-1, 0,
                                             'Sent Domain format error :' + get.todomain + '<br>The following special characters cannot exist [ }  { # ; \" \' ] ')
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
        #         return public.returnMsg(False, "目标URL无法访问")
        subfilter = json.loads(get.subfilter)
        # 检测替换内容
        if subfilter:
            for s in subfilter:
                if not s["sub1"]:
                    if s["sub2"]:
                        return public.return_message(-1, 0, 'Please enter the content to be replaced')
                elif s["sub1"] == s["sub2"]:
                    return public.return_message(-1, 0,
                                                 'The content to replace cannot be the same as the content to be replaced')

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
                rep = "%s[\\w\\s\\~\\/\\(\\)\\.\\*\\{\\}\\;\\$\n\\#]+.*\n.*" % public.get_msg_gettext("#Clear cache")
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
                return public.return_message(0, 0, "")
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
                rep = "%s[\\w\\s\\~\\/\\(\\)\\.\\*\\{\\}\\;\\$\n\\#]+.*\n.*" % public.get_msg_gettext("#Clear cache")
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
        return public.return_message(0, 0, "")

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
        return public.return_message(0, 0, "")

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
                return public.return_message(-1, 0,
                                             'A global reverse proxy already exists in the rewrite/nginx master configuration/vhost file')
        return public.return_message(0, 0, "")

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
                Param('type').Integer(),
                Param('cache').Integer(),
                Param('advanced').Integer(),
                Param('cachetime').Integer(),
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
            return public.return_message(-1, 0, 'Destination URL cannot be empty')
        if not nocheck:
            if self.__CheckStart(get, "create"):
                return self.__CheckStart(get, "create")
        if public.get_webserver() == 'nginx':
            if self.CheckLocation(get)['message']['result']:
                return self.CheckLocation(get)
        if not get.proxysite.split('//')[-1]:
            return public.return_message(-1, 0,
                                         'The target URL cannot be [http:// or https://], please fill in the full URL, such as: https://aapanel.com')
        # project_type = public.M('sites').where('name=?', (get.sitename,)).field('project_type').find()['project_type']
        # if project_type == 'WP':
        #     return public.return_msg_gettext(False,'Reverse proxies are not currently available for Wordpress sites that use one-click deployment')
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
            "cachetime": int(get.cachetime)
        })
        self.__write_config(self.__proxyfile, proxyUrl)
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
        return public.return_message(0, 0, 'Setup successfully!')

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
                return public.return_message(-1, 0, 'Proxy suspended')
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
        #	return public.returnMsg(True, '保存成功')

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

    # 修改反向代理
    def ModifyProxy(self, get):
        # 校验参数
        try:
            get.validate([
                Param('proxyname').String(),
                Param('proxydir').String(),
                Param('proxysite').String(),
                Param('todomain').String(),
                Param('sitename').String(),
                Param('subfilter').String(),
                Param('type').Integer(),
                Param('cache').Integer(),
                Param('advanced').Integer(),
                Param('cachetime').Integer(),
            ], [
                public.validate.trim_filter(),
            ])
        except Exception as ex:
            public.print_log("error info: {}".format(ex))
            return public.return_message(-1, 0, str(ex))
        if not get.get('proxysite', None):
            return public.return_message(-1, 0, 'Destination URL cannot be empty')
        proxyname_md5 = self.__calc_md5(get.proxyname)
        ap_conf_file = "{p}/panel/vhost/apache/proxy/{s}/{n}_{s}.conf".format(
            p=self.setupPath, s=get.sitename, n=proxyname_md5)
        ng_conf_file = "{p}/panel/vhost/nginx/proxy/{s}/{n}_{s}.conf".format(
            p=self.setupPath, s=get.sitename, n=proxyname_md5)
        ols_conf_file = "{p}/panel/vhost/openlitespeed/proxy/{s}/urlrewrite/{n}_{s}.conf".format(
            p=self.setupPath, s=get.sitename, n=proxyname_md5)
        if self.__CheckStart(get):
            return self.__CheckStart(get)
        conf = self.__read_config(self.__proxyfile)
        random_string = public.GetRandomString(8)
        for i in range(len(conf)):
            if conf[i]["proxyname"] == get.proxyname and conf[i]["sitename"] == get.sitename:
                if int(get.type) != 1:
                    if not os.path.exists(ng_conf_file):
                        return public.return_message(-1, 0, "Please enable the reverse proxy before editing!")
                    public.ExecShell("mv {f} {f}_bak".format(f=ap_conf_file))
                    public.ExecShell("mv {f} {f}_bak".format(f=ng_conf_file))
                    public.ExecShell("mv {f} {f}_bak".format(f=ols_conf_file))
                    conf[i]["type"] = int(get.type)
                    self.__write_config(self.__proxyfile, conf)
                    public.serviceReload()
                    return public.return_message(0, 0, 'Setup successfully!')
                else:
                    if os.path.exists(ap_conf_file + "_bak"):
                        public.ExecShell("mv {f}_bak {f}".format(f=ap_conf_file))
                        public.ExecShell("mv {f}_bak {f}".format(f=ng_conf_file))
                        public.ExecShell("mv {f}_bak {f}".format(f=ols_conf_file))
                    ng_conf = public.readFile(ng_conf_file)
                    ng_conf = self.old_proxy_conf(ng_conf, ng_conf_file, get)['message']['result']
                    # 修改nginx配置
                    # 如果代理URL后缀带有URI则删除URI，正则匹配不支持proxypass处带有uri
                    php_pass_proxy = get.proxysite
                    if get.proxysite[-1] == '/' or get.proxysite.count('/') > 2 or '?' in get.proxysite:
                        php_pass_proxy = re.search(r'(https?\:\/\/[\w\.]+)', get.proxysite).group(0)
                    ng_conf = re.sub(r"location\s+[\^\~]*\s?%s" % conf[i]["proxydir"], "location ^~ " + get.proxydir,
                                     ng_conf)
                    ng_conf = re.sub(r"proxy_pass\s+%s" % conf[i]["proxysite"], "proxy_pass " + get.proxysite, ng_conf)
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
                    return public.return_message(0, 0, 'Setup successfully!')

        # 设置反向代理

    def SetProxy(self, get):
        sitename = get.sitename  # 站点名称
        advanced = int(get.advanced)
        type = int(get.type)
        cache = int(get.cache)
        cachetime = int(get.cachetime)
        proxysite = get.proxysite
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
        if advanced == 1:
            if proxydir[-1] != '/':
                proxydir = '{}/'.format(proxydir)
            if proxysite[-1] != '/':
                proxysite = '{}/'.format(proxysite)
            if type == 1 and cache == 1:
                ng_proxy_cache += ng_proxy % (
                    proxydir, proxydir, proxysite, get.todomain,
                    public.get_msg_gettext('#Persistent connection related configuration'), ng_sub_filter, ng_cache,
                    get.proxydir)
            if type == 1 and cache == 0:
                ng_proxy_cache += ng_proxy % (
                    get.proxydir, get.proxydir, proxysite, get.todomain,
                    public.get_msg_gettext('#Persistent connection related configuration'), ng_sub_filter, no_cache,
                    get.proxydir)
        else:
            if type == 1 and cache == 1:
                ng_proxy_cache += ng_proxy % (
                    get.proxydir, get.proxydir, get.proxysite, get.todomain,
                    public.get_msg_gettext('#Persistent connection related configuration'), ng_sub_filter, ng_cache,
                    get.proxydir)
            if type == 1 and cache == 0:
                ng_proxy_cache += ng_proxy % (
                    get.proxydir, get.proxydir, get.proxysite, get.todomain,
                    public.get_msg_gettext('#Persistent connection related configuration'), ng_sub_filter, no_cache,
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
        return public.return_message(0, 0, 'Setup successfully!')

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
        if public.get_webserver() != 'nginx': return public.return_message(0, 0, "")
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
        return public.return_message(0, 0, "")

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
        rewriteList['rewrite'].append('0.' + public.get_msg_gettext('Current'))
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
                              (name, path, '1', public.get_msg_gettext('Please enter a note'), public.getDate()))
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
            if conf.find('#ErrorLog') != -1:
                conf = conf.replace("#ErrorLog", "ErrorLog").replace('#CustomLog', 'CustomLog')
            else:
                conf = conf.replace("ErrorLog", "#ErrorLog").replace('CustomLog', '#CustomLog')
            public.writeFile(filename, conf)

        # NGINX
        filename = public.GetConfigValue('setup_path') + '/panel/vhost/nginx/' + get.name + '.conf'
        if os.path.exists(filename):
            conf = public.readFile(filename)
            rep = public.GetConfigValue('logs_path') + "/" + get.name + ".log"
            if conf.find(rep) != -1:
                conf = conf.replace(rep, "/dev/null")
            else:
                # conf = re.sub('}\n\\s+access_log\\s+off', '}\n\taccess_log  ' + rep, conf)
                conf = conf.replace('access_log  /dev/null', 'access_log  ' + rep)
            public.writeFile(filename, conf)

        # OLS
        filename = public.GetConfigValue('setup_path') + '/panel/vhost/openlitespeed/detail/' + get.name + '.conf'
        conf = public.readFile(filename)
        if conf:
            rep = "\nerrorlog(.|\n)*compressArchive\\s*1\\s*\n}"
            tmp = re.search(rep, conf)
            s = 'on'
            if not tmp:
                s = 'off'
                rep = "\n#errorlog(.|\n)*compressArchive\\s*1\\s*\n#}"
                tmp = re.search(rep, conf)
            tmp = tmp.group()
            if tmp:
                result = ''
                if s == 'on':
                    for l in tmp.strip().splitlines():
                        result += "\n#" + l
                else:
                    for l in tmp.splitlines():
                        result += "\n" + l[1:]
                conf = re.sub(rep, "\n" + result.strip(), conf)
                public.writeFile(filename, conf)

        public.serviceReload()
        return public.return_message(0, 0, 'Setup successfully!')

    # 取日志状态
    def GetLogsStatus(self, get):
        filename = public.GetConfigValue(
            'setup_path') + '/panel/vhost/' + public.get_webserver() + '/' + get.name + '.conf'
        if public.get_webserver() == 'openlitespeed':
            filename = public.GetConfigValue(
                'setup_path') + '/panel/vhost/' + public.get_webserver() + '/detail/' + get.name + '.conf'
        conf = public.readFile(filename)
        if not conf: return public.return_message(0, 0, True)
        if conf.find('#ErrorLog') != -1: return public.return_message(0, 0, False)
        # if re.search("}\n*\\s*access_log\\s+off", conf):
        if conf.find("access_log  /dev/null") != -1: return public.return_message(0, 0, False)
        if re.search('\n#accesslog', conf):
            return public.return_message(0, 0, False)
        return public.return_message(0, 0, True)

    # 取目录加密状态
    def GetHasPwd(self, get):
        if not hasattr(get, 'siteName'):
            get.siteName = public.M('sites').where('id=?', (get.id,)).getField('name')
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
            return public.return_message(-1, 0,
                                         'The current web server is openlitespeed. This function is not supported yet.')
        if len(get.username.strip()) < 3 or len(get.password.strip()) < 3: return public.return_message(-1, 0,
                                                                                                        'Username or password cannot be less than 3 digits!')

        if not hasattr(get, 'siteName'):
            get.siteName = public.M('sites').where('id=?', (get.id,)).getField('name')

        self.CloseHasPwd(get)
        filename = public.GetConfigValue('setup_path') + '/pass/' + get.siteName + '.pass'
        try:
            passconf = get.username + ':' + public.hasPwd(get.password)
        except:
            return public.return_message(-1, 0,
                                         "The password fomart is wrong, please do not use special symbols for the first two digits!")

        if get.siteName == 'phpmyadmin':
            get.configFile = self.setupPath + '/nginx/conf/nginx.conf'
            if os.path.exists(self.setupPath + '/panel/vhost/nginx/phpmyadmin.conf'):
                get.configFile = self.setupPath + '/panel/vhost/nginx/phpmyadmin.conf'
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
        return public.return_message(0, 0, 'Setup successfully!')

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
        else:
            get.configFile = self.setupPath + '/panel/vhost/nginx/' + get.siteName + '.conf'

        if os.path.exists(get.configFile):
            conf = public.readFile(get.configFile)
            rep = "\n\\s*#AUTH_START(.|\n){1,200}#AUTH_END"
            conf = re.sub(rep, '', conf)
            public.writeFile(get.configFile, conf)

        if get.siteName == 'phpmyadmin':
            get.configFile = self.setupPath + '/apache/conf/extra/httpd-vhosts.conf'
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
        return public.return_message(0, 0, 'Setup successfully!')

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
        public.write_log_gettext('TYPE_SITE', 'Turned on Tomcat supporting for site [{}]!', (siteName,))
        return public.return_msg_gettext(True, 'Succeeded, please test JSP program!')

    # 关闭tomcat支持
    def CloseTomcat(self, get):
        if not os.path.exists('/etc/init.d/tomcat'): return public.return_message(-1, 0, "")
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
        siteName = public.M('sites').where('id=?', (get.id,)).getField('name')
        sitePath = public.M('sites').where('id=?', (get.id,)).getField('path')
        if not siteName or os.path.isfile(sitePath): return public.return_message(0, 0, {"runPath": "/", 'dirs': []})
        path = sitePath
        if public.get_webserver() == 'nginx':
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
        elif public.get_webserver() == 'apache':
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
        if not os.path.exists(sitePath): os.makedirs(sitePath)
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
        return_message = public.return_msg_gettext(True, 'Setup successfully!')
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
            return public.return_message(-1, 0, 'OpenLiteSpeed does not support setting the default site')
        default_site_save = 'data/defaultSite.pl'
        # 清理旧的
        defaultSite = public.readFile(default_site_save)
        http2 = ''
        versionStr = public.readFile('/www/server/nginx/version.pl')
        if versionStr:
            if versionStr.find('1.8.1') == -1: http2 = ' http2'
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
            None, '%s [' % public.get_msg_gettext('Scan directory') + get.path + ']', 'execshell', '0',
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
        if type(conf) == bool: return public.return_message(-1, 0, 'Reading configuration file failed!')
        if conf.find('SECURITY-START') != -1:
            rep = "#SECURITY-START(\n|.)+#SECURITY-END"
            tmp = re.search(rep, conf).group()
            content = re.search(r"\(.+\)\$", tmp)
            if content:
                data['fix'] = content.group().replace('(', '').replace(')$', '').replace('|', ',')
            else:
                data['fix'] = ''
            try:
                data['domains'] = ','.join(
                    list(set(re.search("valid_referers\\s+none\\s+blocked\\s+(.+);\n", tmp).groups()[0].split())))
            except:
                data['domains'] = ','.join(list(set(re.search("valid_referers\\s+(.+);\n", tmp).groups()[0].split())))
            data['status'] = True
            data['http_status'] = tmp.find('none blocked') != -1
            try:
                data['return_rule'] = re.findall(r'(return|rewrite)\s+.*(\d{3}|(/.+)\s+(break|last));', conf)[0][
                    1].replace('break', '').strip()
            except:
                data['return_rule'] = '404'
        else:
            conf_file = self.conf_dir + '/{}_door_chain.json'.format(get.name)
            try:
                data = json.loads(public.readFile(conf_file))
                data['status'] = data['status'] == "true"
            except:
                data['fix'] = 'jpg,jpeg,gif,png,js,css'
                domains = public.M('domain').where('pid=?', (get.id,)).field('name').select()
                tmp = []
                for domain in domains:
                    tmp.append(domain['name'])
                data['domains'] = ','.join(tmp)
                data['return_rule'] = '404'
                data['status'] = False
                data['http_status'] = False
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

        if len(get.fix) < 2: return public.return_message(-1, 0, 'URL suffix cannot be empty!')
        if len(get.domains) < 3: return public.return_message(-1, 0, 'Anti-theft chain domain name cannot be empty!')
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
        # nginx
        file = '/www/server/panel/vhost/nginx/' + get.name + '.conf'
        if os.path.exists(file):
            conf = public.readFile(file)
            if conf.find('SECURITY-START') != -1:
                # 先替换域名部分，防止域名过多导致替换失败
                rep = r"\s+valid_referers.+"
                conf = re.sub(rep, '', conf)
                # 再替换配置部分
                rep = "\\s+#SECURITY-START(\n|.){1,500}#SECURITY-END\n?"
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
                                return public.return_message(-1, 0,
                                                             'Response resources should use URI path or HTTP status code, such as: /test.png or 404')
                            return_rule = 'rewrite /.* {} break'.format(get.return_rule)
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
    include enable-php-''' % (
                        get.fix.strip().replace(',', '|'), get.domains.strip().replace(',', ' '), return_rule)
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
                                return public.return_message(-1, 0,
                                                             'Response resources should use URI path or HTTP status code, such as: /test.png or 404')
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
        return public.return_message(0, 0, 'Setup successfully!')

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
        return_message = public.return_msg_gettext(True, self.xsssec(public.GetNumLines(logPath, 1000)))
        del return_message['status']
        return public.return_message(0, 0, return_message['msg'])
        # if not os.path.exists(logPath): return public.return_message(-1,0, 'Log is empty')
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
        data.insert(0, {"id": 0, "name": public.get_msg_gettext('Default category')})
        for i in data:
            i['name'] = public.xss_version(i['name'])
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
        return public.return_message(0, 0, "Setup successfully!")

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
                del_failed[name] = public.get_msg_gettext('There was an error deleting, please try again.')
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
        default_conf_body = '''server
{
    listen 80;
    listen 443 ssl;
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
}'''
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
            return public.return_message(-1, 0, '查询失败，不存在的地址')

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
            return public.return_message(0, 0, 'Error parsing configuration file')
        return public.return_message(0, 0, 'Setup successfully')

    def remove_auto_restart_rph(self, get):
        # 设置申请或续签SSL时自动停止反向代理、重定向、http to https，申请完成后自动开启
        conf_file = '{}/data/stop_rp_when_renew_ssl.pl'.format(public.get_panel_path())
        conf = public.readFile(conf_file)
        if not conf:
            return public.return_message(-1, 0,
                                         'Website [proxy,redirect,http to https]  are not set to restart automatically')
        try:
            conf = json.loads(conf)
            conf.remove(get.sitename)
            public.writeFile(conf_file, json.dumps(conf))
        except:
            return public.return_message(-1, 0, 'Configuration file parsing error')
        return public.return_message(0, 0, 'Setup successfully')

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
            return public.return_message(-1, 0,
                                         'Website [proxy,redirect,http to https]  are not set to restart automatically')
        try:
            conf = json.loads(conf)
            if get.sitename in conf:
                return public.return_message(0, 0,
                                             'This website has turn on [proxy,redirect,http to https] auto restart')
            return public.return_message(-1, 0, 'Website has turn off auto restart')
        except:
            return public.return_message(-1, 0, 'Configuration file parsing error')

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

    # 获取wp 安全模块配置
    def get_wp_security_info(self, get):
        from wp_toolkit import wp_security
        result = wp_security().get_security_info(get)
        get.name = get.site_name
        # 取防盗链配置
        hotlink = self.GetSecurity(get)
        try:
            result['message']['hotlink_status'] = 1 if hotlink['message']['status'] else 0
        except:
            pass
        return result

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
        from wp_toolkit import wpmigration
        ok, msg = wpmigration.migrate_aap_from_website_to_wptoolkit()

        if not ok:
            return public.fail_v2(msg)

        return public.success_v2(msg)

    # 查询可从 [网站管理] 迁移到 [WP Toolkit] 的网站列表
    def wp_can_migrate_from_website_to_wptoolkit(self, args: public.dict_obj):
        from wp_toolkit import wpmigration
        return public.success_v2(wpmigration.can_migrations_of_aap_website())

    # 从aapanel WP备份中创建WP站点
    def wp_create_with_aap_bak(self, args: public.dict_obj):
        from wp_toolkit import wpbackup
        ok, msg = wpbackup.wp_deploy_with_aap_bak(args)

        if not ok:
            return public.fail_v2(msg)

        return public.success_v2(msg)

    # 从plesk/cpanel WP备份中创建WP站点
    def wp_create_with_plesk_or_cpanel_bak(self, args: public.dict_obj):
        from wp_toolkit import wpbackup
        ok, msg = wpbackup.wp_deploy_with_plesk_or_cpanel_bak(args)

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

    # 安装插件
    def wp_install_plugin(self, args: public.dict_obj):
        # 参数校验
        args.validate([
            public.Param('s_id').Require().Integer('>', 0),
            public.Param('slug').Require().SafePath(),
        ])

        from wp_toolkit import wpmgr

        ok, msg = wpmgr(args.s_id).install_plugin(args.slug)

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

        ok, msg = wpmgr(args.s_id).update_plugin(args.plugin_file)

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

        if int(args.enable) == 1:
            fn = wpmgr_obj.enable_plugin_auto_update
        else:
            fn = wpmgr_obj.disable_plugin_auto_update

        ok, msg = fn(args.plugin_file)

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

        if int(args.activate) == 1:
            fn = wpmgr_obj.activate_plugins
            errmsg = public.get_msg_gettext('Activate plugin failed, please try again later.')
        else:
            fn = wpmgr_obj.deactivate_plugins
            errmsg = public.get_msg_gettext('Deactivate plugin failed, please try again later.')

        if not fn(args.plugin_file):
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

        ok, msg = wpmgr(args.s_id).uninstall_plugin(args.plugin_file)

        if not ok:
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

        ok, msg = wpmgr(args.s_id).install_theme(args.slug)

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

        ok, msg = wpmgr(args.s_id).update_theme(args.stylesheet)

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

        if int(args.enable) == 1:
            fn = wpmgr_obj.enable_theme_auto_update
        else:
            fn = wpmgr_obj.disable_theme_auto_update

        ok, msg = fn(args.stylesheet)

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

        if not wpmgr(args.s_id).switch_theme(args.stylesheet):
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

        ok, msg = wpmgr(args.s_id).uninstall_theme(args.stylesheet)

        if not ok:
            return public.fail_v2(msg)

        return public.success_v2('Success')

    # 获取所有WP站点
    def wp_all_sites(self, args: public.dict_obj):
        from wp_toolkit import wpmgr
        return public.success_v2(wpmgr.all_sites())

    # TODO 获取WP整合包列表
    def wp_set_list(self, args: public.dict_obj):
        # 校验参数
        args.validate([
            public.Param('keyword'),
            public.Param('p').Filter(int),
            public.Param('p_size').Filter(int),
        ])

        from wp_toolkit import wp_sets
        return public.success_v2(wp_sets().fetch_list(args.get('keyword', ''), args.get('p', 1), args.get('p_size', 20)))

    # TODO 新建WP整合包
    def wp_create_set(self, args: public.dict_obj):
        # 校验参数
        args.validate([
            public.Param('name').Require(),
        ])

        from wp_toolkit import wp_sets

        if wp_sets().create_set(args.name) < 1:
            raise public.HintException(public.get_msg_gettext('Failed to create Set'))

        return public.success_v2('Success')

    # TODO 删除WP整合包
    def wp_remove_set(self, args: public.dict_obj):
        # 校验参数
        args.validate([
            public.Param('set_id').Require().Regexp(r'^\d+(?:,\d+)*$'),
        ])

        from wp_toolkit import wp_sets

        if not wp_sets().remove_set(list(map(lambda x: int(x), str(args.set_id).split(',')))):
            raise public.HintException(public.get_msg_gettext('Failed to remove Sets'))

        return public.success_v2('Success')

    # TODO 添加插件or主题到WP整合包中
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
            raise public.HintException(public.get_msg_gettext('Invalid type of Set items'))

        if not ok:
            raise public.HintException(msg)

        return public.success_v2('Success')

    # TODO 将插件or主题从WP整合包中移除
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
            raise public.HintException(public.get_msg_gettext('Invalid type of Set items'))

        if not ok:
            raise public.HintException(public.get_msg_gettext('Failed to remove items from Set'))

        return public.success_v2('Success')

    # TODO 更改WP整合包中插件or主题的激活状态
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
            raise public.HintException(public.get_msg_gettext('Invalid type of Set items'))

        if not ok:
            raise public.HintException(public.get_msg_gettext('Failed to change items state from Set'))

        return public.success_v2('Success')

    # TODO 通过WP整合包安装插件&主题
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

    # *********** WP Toolkit --End-- *************

    @staticmethod
    def test_domains_api(get):
        try:
            domains = json.loads(get.domains.strip())
        except (json.JSONDecodeError, AttributeError, KeyError):
            return public.return_message(-1, 0, "参数错误")
        try:
            from panel_dns_api_v2 import DnsMager
            public.print_log("开始测试域名解析---- {}")
            # public.print_log("开始测试域名解析---- {}".format(domains[0]))

            return DnsMager().test_domains_api(domains)
        except:
            pass
        public.return_message(0, 0, "")

    def site_rname(self, get):
        try:
            if not (hasattr(get, "id") and hasattr(get, "rname")):
                return public.return_message(-1, 0, "parameter error")
            id = get.id
            rname = get.rname
            data = public.M('sites').where("id=?", (id,)).select()
            if not data:
                return public.return_message(-1, 0, "The site does not exist!")
            data = data[0]
            name = data['rname'] if 'rname' in data.keys() and data.get('rname', '') else data['name']
            if 'rname' not in data.keys():
                public.M('sites').execute("ALTER TABLE 'sites' ADD 'rname' text DEFAULT ''", ())
            public.M('sites').where('id=?', data['id']).update({'rname': rname})
            # public.write_log_gettext('Site manager', 'Website [{}] renamed: [{}]'.format(name, rname))
            return public.return_message(0, 0, 'Website [{}] renamed: [{}]'.format(name, rname))
        except:
            return public.return_message(-1, 0, traceback.format_exc())
