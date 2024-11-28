#coding: utf-8
#-------------------------------------------------------------------
# aaPanel
#-------------------------------------------------------------------
# Copyright (c) 2015-2017 aaPanel(www.aapanel.com) All rights reserved.
#-------------------------------------------------------------------
# Author: zhwen <zhw@aapanel.com>
#-------------------------------------------------------------------

#------------------------------
# 站点目录密码保护
#------------------------------
import public,re,os,json,shutil
from public.validate import Param

class SiteDirAuth:
    # 取目录加密状态
    def __init__(self):
        self.setup_path = public.GetConfigValue('setup_path')
        self.conf_file = self.setup_path + "/panel/data/site_dir_auth.json"
    # 读取配置
    def _read_conf(self):
        conf = public.readFile(self.conf_file)
        if not conf:
            conf = {}
            public.writeFile(self.conf_file,json.dumps(conf))
            return conf
        try:
            conf = json.loads(conf)
            if not isinstance(conf,dict):
                conf = {}
                public.writeFile(self.conf_file, json.dumps(conf))
        except:
            conf = {}
            public.writeFile(self.conf_file, json.dumps(conf))
        return conf

    def _write_conf(self,conf,site_name):
        c = self._read_conf()
        if not c or site_name not in c:
            c[site_name] = [conf]
        else:
            if site_name in c:
                c[site_name].append(conf)
        public.writeFile(self.conf_file,json.dumps(c))

    def _check_site_authorization(self,site_name):
        webserver=public.get_webserver()
        conf_file = "{setup_path}/panel/vhost/{webserver}/{site_name}.conf".format(
                setup_path=self.setup_path, site_name=site_name,webserver=webserver)
        if "Authorization" in public.readFile(conf_file):
            return True


    # 设置目录加密
    def set_dir_auth(self,get):
        '''
        get.name        auth_name
        get.site_dir         auth_dir
        get.username    username
        get.password    password
        get.id          site id
        :param get:
        :return:
        '''
        # 校验参数
        try:
            get.validate([
                Param('site_dir').String(),
                Param('name').String(),
                Param('username').String(),
                Param('password').String(),
                Param('id').Integer(),
            ], [
                public.validate.trim_filter(),
            ])
        except Exception as ex:
            public.print_log("error info: {}".format(ex))
            return public.return_message(-1, 0, str(ex))
        # if len(get.username) < 3 or len(get.password) < 3:
        #     return public.return_msg_gettext(False, public.lang("Username or password cannot be less than 3 characters"))
        # name = get.name
        param = self.__check_param(get)
        if param['status']==-1:
            return param
        param = param['message']
        password = param['password']
        username = param['username']
        name = param['name']
        site_dir = get.site_dir
        if public.get_webserver() == "openlitespeed":
            return public.return_message(-1, 0, public.lang("OpenLiteSpeed is currently not supported"))
        # if not hasattr(get,"password") or not get.password or not hasattr(get,"username") or not get.username:
        #     return public.return_msg_gettext(False, public.lang("Please enter an account or password"))
        if not get.site_dir:
            return public.return_message(-1, 0, public.lang("Please enter the directory to be protected"))
        if not get.name:
            return public.return_message(-1, 0, public.lang("Please enter the Name"))
        passwd = public.hasPwd(password)
        site_info = self.get_site_info(get.id)
        site_name = site_info["site_name"]
        if self._check_site_authorization(site_name):
            return public.return_message(-1, 0, public.lang("Site password protection has been set, please cancel and then set. Site directory --> Password access"))
        if self._check_dir_auth(site_name, name,site_dir):
            return public.return_message(-1, 0, public.lang("Directory has been protected"))
        auth = "{user}:{passwd}".format(user=username,passwd=passwd)
        auth_file = '{setup_path}/pass/{site_name}'.format(setup_path=self.setup_path,site_name=site_name)
        if not os.path.exists(auth_file):
            os.makedirs(auth_file)
        auth_file = auth_file+"/{}.pass".format(name)
        public.writeFile(auth_file,auth)
        # 配置独立认证文件
        self.set_dir_auth_file(site_info["site_path"],site_name,name,username,site_dir,auth_file)
        # 配置站点主文件
        result = self.set_conf(site_name,"create")
        if result:
            return public.return_message(0,0,result)
        # 检查配置
        webserver = public.get_webserver()
        result=self.check_site_conf(webserver,site_name,name)
        if result:
            return public.return_message(0,0,result)
        # 写配置
        conf = {"name":name,"site_dir":get.site_dir,"auth_file":auth_file}
        self._write_conf(conf,site_name)
        public.serviceReload()
        return public.return_message(0, 0, public.lang("Successfully created"))

    # 检查配置是否存在
    def _check_dir_auth(self, site_name, name,site_dir):
        conf = self._read_conf()
        if not conf:
            return False
        if site_name in conf:
            for i in conf[site_name]:
                if name in i.values() or site_dir == i["site_dir"]:
                    return True

    # 获取当前站点php版本
    def get_site_php_version(self,siteName):
        try:
            conf = public.readFile(self.setup_path + '/panel/vhost/'+public.get_webserver()+'/'+siteName+'.conf');
            if public.get_webserver() == 'nginx':
                rep = r"enable-php-(\w{2,5})\.conf"
                tmp = re.search(rep,conf)
                if not tmp:
                    rep = r"enable-php-(\d+-wpfastcgi).conf"
                    re.search(rep, conf)
            else:
                rep = r"php-cgi-(\w{2,5})\.sock"
            tmp = re.search(rep,conf).groups()
            if tmp:
                return tmp[0]
            else:
                return ""
        except:
            return public.return_msg_gettext(False, public.lang("Apache2.2 does NOT support MultiPHP!"))

    # 获取站点名
    def get_site_info(self,id):
        site_info = public.M('sites').where('id=?', (id,)).field('name,path').find()
        return {"site_name":site_info["name"],"site_path":site_info["path"]}

    def change_dir_auth_file_nginx_phpver(self,site_name,phpv,auth_name):
        file_path = "{setup_path}/panel/vhost/nginx/dir_auth/{site_name}/{auth_name}.conf".format(
            setup_path=self.setup_path,site_name=site_name,auth_name=auth_name)
        conf = public.readFile(file_path)
        if not conf:
            return False

        if phpv == 'other':
            php_conf = "include /www/server/panel/vhost/other_php/{}/enable-php-other.conf;".format(site_name)
        else:
            php_conf = 'include enable-php-{}.conf;'.format(phpv)

        rep = r"include\s+(enable-php-\w+|/www/server/panel/vhost/other_php/{}/enable-php-other)\.conf;".format(site_name)
        conf = re.sub(rep,php_conf,conf)

        public.writeFile(file_path,conf)

    # 设置独立认证文件
    def set_dir_auth_file(self,site_path,site_name,name,username,site_dir,auth_file):
        php_ver = self.get_site_php_version(site_name)
        php_conf = ""
        if php_ver:
            if php_ver == 'other':
                php_conf = "include /www/server/panel/vhost/other_php/{}/enable-php-{}.conf;".format(site_name,php_ver)
            else:
                php_conf = "include enable-php-{}.conf;".format(php_ver)

        for i in ["nginx","apache"]:
            file_path = "{setup_path}/panel/vhost/{webserver}/dir_auth/{site_name}"
            if i == "nginx":
                # 设置nginx
                conf = '''location ~* ^%s* {
    #AUTH_START
    auth_basic "Authorization";
    auth_basic_user_file %s;
    %s
    #AUTH_END
}''' % (site_dir,auth_file,php_conf)
            else:
            # 设置apache
                conf = '''<Directory "{site_path}{site_dir}">
    #AUTH_START
    AuthType basic
    AuthName "Authorization "
    AuthUserFile {auth_file}
    Require user {username}
    #AUTH_END
    SetOutputFilter DEFLATE
    Options FollowSymLinks
    AllowOverride All
    #Require all granted
        DirectoryIndex index.php index.html index.htm default.php default.html default.htm
</Directory>'''.format(site_path=site_path,site_dir=site_dir,auth_file=auth_file,username=username,site_name=site_name)
            conf_file = file_path.format(setup_path=self.setup_path,site_name=site_name,webserver=i)
            if not os.path.exists(conf_file):
                os.makedirs(conf_file)
            conf_file = conf_file + '/{}.conf'.format(name)
            public.writeFile(conf_file,conf)

    # 设置apache配置
    def set_conf(self,site_name,act):
        for i in ["nginx", "apache"]:
            dir_auth_file = "%s/panel/vhost/%s/dir_auth/%s/*.conf" % (self.setup_path,i,site_name,)
            file = self.setup_path + "/panel/vhost/{}/".format(i) + site_name + ".conf"
            shutil.copyfile(file, '/tmp/{}_file_bk.conf'.format(i))

            if os.path.exists(file):
                conf = public.readFile(file)
                if i == "apache":
                    if act == "create":
                        rep = "IncludeOptional.*\\/dir_auth\\/.*conf(\n|.)+<\\/VirtualHost>"
                        rep1 = "</VirtualHost>"
                        if not re.search(rep, conf):
                            conf = conf.replace(rep1,
                                                "\n\t#Directory protection rules, do not manually delete\n\tIncludeOptional {}\n</VirtualHost>".format(
                                                    dir_auth_file))
                    else:
                        rep = "\n*#Directory protection rules, do not manually delete\n+\\s+IncludeOptional[\\s\\w\\/\\.\\*]+"
                        conf = re.sub(rep, '', conf)
                    public.writeFile(file, conf)
                else:
                    if act == "create":
                        rep = "#SSL-END(\n|.)+include.*\\/dir_auth\\/.*conf;"
                        rep1 = "#SSL-END"
                        if not re.search(rep,conf):
                            conf = conf.replace(rep1, rep1 + "\n\t#Directory protection rules, do not manually delete\n\tinclude {};".format(dir_auth_file))
                    else:
                        rep = "\n*#Directory protection rules, do not manually delete\n+\\s+include[\\s\\w\\/\\.\\*]+;"
                        conf = re.sub(rep, '', conf)
                    public.writeFile(file, conf)

    # 验证站点配置
    def check_site_conf(self,webserver,site_name,name):
        isError = public.checkWebConfig()
        auth_file = "{setup_path}/panel/vhost/{webserver}/dir_auth/{site_name}/{name}.conf".format(setup_path=self.setup_path,webserver=webserver,site_name=site_name,name=name)
        if (isError != True):
            os.remove(auth_file)
            # a_conf = self._read_conf()
            # for i in range(len(a_conf)-1,-1,-1):
            #     if site_name == a_conf[i]["sitename"] and a_conf[i]["proxyname"]:
            #         del a_conf[i]
            return public.return_msg_gettext(False, public.lang('ERROR: %s<br><a style="color:red;">' % public.lang("Configuration ERROR") + isError.replace("\n", '<br>') + '</a>'))

    # 删除密码保护
    def delete_dir_auth(self,get):
        '''
        get.id
        get.name
        :param get:
        :return:
        '''
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

        name = get.name
        site_info = self.get_site_info(get.id)
        site_name = site_info["site_name"]
        conf = self._read_conf()
        if site_name not in conf:
            return public.return_message(-1,0,"The website does not exist in the configuration：{}",(site_name,))
        for i in range(len(conf[site_name])):
            if name in conf[site_name][i].values():
                print(conf[site_name][i])
                del(conf[site_name][i])
                if not conf[site_name]:
                    del(conf[site_name])
                break
        public.writeFile(self.conf_file,json.dumps(conf))
        for i in ["nginx", "apache"]:
            file_path = "{setup_path}/panel/vhost/{webserver}/dir_auth/{site_name}/{name}.conf".format(webserver=i,
                                                                                                       setup_path=self.setup_path,
                                                                                                       site_name=site_name,
                                                                                                       name=name)
            os.remove(file_path)
        if not conf:
            self.set_conf(site_name,"delete")
        if not hasattr(get,'multiple'):
            public.serviceReload()
        return public.return_message(0, 0, public.lang("Successfully deleted!"))

    # 修改目录保护密码
    def modify_dir_auth_pass(self,get):
        '''
        get.id
        get.name
        get.username
        get.password
        :param get:
        :return:
        '''
        # 校验参数
        try:
            get.validate([
                Param('name').String(),
                Param('username').String(),
                Param('password').String(),
                Param('id').Integer(),

            ], [
                public.validate.trim_filter(),
            ])
        except Exception as ex:
            public.print_log("error info: {}".format(ex))
            return public.return_message(-1, 0, str(ex))

        # if not hasattr(get,"password") or not get.password or not hasattr(get,"username") or not get.username:
        #     return public.return_msg_gettext(False, public.lang("Username or password cannot be less than 3 characters"))
        param = self.__check_param(get)
        if param['status']==-1:
            return param
        param = param['message']
        password = param['password']
        username = param['username']
        name = get.name
        site_info = self.get_site_info(get.id)
        site_name = site_info["site_name"]
        passwd = public.hasPwd(get.password)
        auth = "{user}:{passwd}".format(user=get.username,passwd=passwd)
        auth_file = '{setup_path}/pass/{site_name}/{name}.pass'.format(setup_path=self.setup_path,site_name=site_name,name=name)
        public.writeFile(auth_file,auth)
        public.serviceReload()
        return public.return_message(0, 0, public.lang("Setup successfully!"))

    # 获取目录保护列表
    def get_dir_auth(self,get):
        '''
        get.id
        get.sitename
        :param get:
        :return:
        '''
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
            site_info = self.get_site_info(get.id)
            site_name = site_info["site_name"]
        else:
            site_name = get.siteName
        conf = self._read_conf()
        if site_name in conf:
            return public.return_message(0,0,{site_name:conf[site_name]})
        return public.return_message(0,0,{})

    def __check_param(self, get):
        values = {}
        if hasattr(get, "password"):
            if not get.password:
                return public.return_message(-1, 0, public.lang("Please enter password!"))
            password = get.password.strip()
            if len(password) < 3:
                return public.return_message(-1, 0, public.lang("Password cannot be less than 3 characters"))
            if re.search(r'\s', password):
                return public.return_message(-1, 0, public.lang("Password cannot contain spaces"))
            values['password'] = password

        if hasattr(get, "username"):
            if not get.username:
                return public.return_message(-1, 0, public.lang("Please enter username!"))
            username = get.username.strip()
            if len(username) < 3:
                return public.return_message(-1, 0, public.lang("Username cannot be less than 3 characters"))
            if re.search(r'\s', username):
                return public.return_message(-1, 0, public.lang("Username cannot contain spaces"))
            values['username'] = username

        if hasattr(get, "name"):
            if not get.name:
                return public.return_message(-1, 0, public.lang("Please enter a name!"))
            name = get.name.strip()
            if len(name) < 3:
                return public.return_message(-1, 0, public.lang("Name cannot be less than 3 characters"))
            if re.search(r'\s', name):
                return public.return_message(-1, 0, public.lang("Name cannot contain spaces"))
            if re.search('[\\/\"\'\\!@#$%^&*()+={}\\[\\]\\:\\;\\?><,./\\\\]+', name):
                return public.return_message(-1, 0, public.lang("Name format must be [ aaa_bbb ]"))
            values['name'] = name

        return public.return_message(0,0, values)
