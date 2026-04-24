#coding: utf-8
# +-------------------------------------------------------------------
# | aaPanel
# +-------------------------------------------------------------------
# | Copyright (c) 2015-2099 aaPanel(www.aapanel.com) All rights reserved.
# +-------------------------------------------------------------------
# | Author: hwliang <hwl@aapanel.com>
# +-------------------------------------------------------------------

#+--------------------------------------------------------------------
#|   自动部署网站
#+--------------------------------------------------------------------

import public,json,os,time,sys,re
from BTPanel import session,cache
class obj: id=0
class plugin_deployment:
    # __setupPath = 'data'
    __panelPath = '/www/server/panel'
    __setupPath = '{}/data'.format(__panelPath)
    logPath = 'data/deployment_speed.json'
    __tmp = '/www/server/panel/temp/'
    timeoutCount = 0
    oldTime = 0
    _speed_key = 'dep_download_speed'

    # 获取PHP一键部署列表
    def GetList(self, get):
        jsonFile = self.__setupPath + '/deployment_list.json'
        if not os.path.exists(jsonFile):
            return public.returnMsg(False, 'Configuration file not exist')

        try:
            data = json.loads(public.readFile(jsonFile))
        except:
            return public.returnMsg(False, 'Configuration file not exist')

        if 'type' in get and get.get('type', 0) in ['1', '2', '3', '4', '5']:
            php_type = int(get.get('type', 0))
            type_data = []
            for i in data['list']:
                if i['type']  == php_type:
                    type_data.append(i)
            data['list'] = type_data

        return public.return_message(0,0, data)

    #获取图标
    def get_icon(self,pinfo):
        path = '/www/server/panel/BTPanel/static/img/dep_ico'
        if not os.path.exists(path): os.makedirs(path,384)
        filename = "%s/%s.png" %  (path, pinfo['name'])
        m_uri = pinfo['min_image']
        pinfo['min_image'] = '/static/img/dep_ico/%s.png' % pinfo['name']
        if sys.version_info[0] == 2: filename = filename.encode('utf-8')
        if os.path.exists(filename):
            if os.path.getsize(filename) > 100: return pinfo
        public.ExecShell("wget -O " + filename + ' https://www.bt.cn' + m_uri + " &")
        return pinfo

    #获取插件列表
    def GetDepList(self,get):
        jsonFile = self.__setupPath + '/deployment_list.json'
        if not os.path.exists(jsonFile): return public.returnMsg(False, public.lang("Profile does not exist!"))
        data = json.loads(public.readFile(jsonFile))
        return self.get_input_list(data)

    #获取本地导入的插件
    def get_input_list(self,data):
        try:
            jsonFile = self.__setupPath + '/deployment_list_other.json'
            if not os.path.exists(jsonFile): return data
            i_data = json.loads(public.readFile(jsonFile))
            for d in i_data:
                data['list'].append(d)
            return data
        except:return data

    #导入程序包
    def AddPackage(self,get):
        jsonFile = self.__setupPath + '/deployment_list_other.json'
        if not os.path.exists(jsonFile):
            public.writeFile(jsonFile,'[]')
        pinfo = {}
        pinfo['name'] = get.name
        pinfo['title'] = get.title
        pinfo['version'] = get.version
        pinfo['php'] = get.php
        pinfo['ps'] = get.ps
        pinfo['official'] = '#'
        pinfo['sort'] = 1000
        pinfo['min_image'] = ''
        pinfo['id'] = 0
        pinfo['type'] = 100
        pinfo['enable_functions'] = get.enable_functions
        pinfo['author'] = 'Import from local'
        from werkzeug.utils import secure_filename
        from flask import request
        f = request.files['dep_zip']
        s_path = self.__panelPath + '/package'
        if not os.path.exists(s_path): os.makedirs(s_path,384)
        s_file = s_path + '/' + pinfo['name'] + '.zip'
        if os.path.exists(s_file): os.remove(s_file)
        f.save(s_file)
        os.chmod(s_file,384)
        pinfo['versions'] = []
        version = {"cpu_limit": 1,
                "dependnet": "",
                "m_version":pinfo['version'],
                "mem_limit": 32,
                "os_limit": 0,
                "size": os.path.getsize(s_file),
                "version": "0",
                "download":"",
                "version_msg": "test2"}
        version['md5'] = self.GetFileMd5(s_file)
        pinfo['versions'].append(version)
        data = json.loads(public.readFile(jsonFile))
        is_exists = False
        for i in range(len(data)):
            if data[i]['name'] == pinfo['name']:
                data[i] = pinfo
                is_exists = True

        if not is_exists: data.append(pinfo)

        public.writeFile(jsonFile,json.dumps(data))
        return public.returnMsg(True, public.lang("Import Success!"))

    #取本地包信息
    def GetPackageOther(self,get):
        p_name = get.p_name
        jsonFile = self.__setupPath + '/deployment_list_other.json'
        if not os.path.exists(jsonFile): public.returnMsg(False,'could not find [%s]' % p_name)
        data = json.loads(public.readFile(jsonFile))
        
        for i in range(len(data)):
            if data[i]['name'] == p_name: return data[i]
        return public.returnMsg(False,'could not find  [%s]' % p_name)


    #删除程序包
    def DelPackage(self,get):
        jsonFile = self.__setupPath + '/deployment_list_other.json'
        if not os.path.exists(jsonFile): return public.returnMsg(False, public.lang("Profile does not exist!"))

        data = {}
        data = json.loads(public.readFile(jsonFile))

        tmp = []
        for d in data:
            if d['name'] == get.dname:
                s_file = self.__panelPath + '/package/' + d['name'] + '.zip'
                if os.path.exists(s_file): os.remove(s_file)
                continue
            tmp.append(d)

        data = tmp
        public.writeFile(jsonFile,json.dumps(data))
        return public.returnMsg(True, public.lang("Successfully deleted!"))

    #下载文件
    def DownloadFile(self,url,filename):
        try:
            path = os.path.dirname(filename)
            if not os.path.exists(path): os.makedirs(path)
            import urllib,socket
            socket.setdefaulttimeout(20)
            self.pre = 0
            self.oldTime = time.time()
            if sys.version_info[0] == 2:
                urllib.urlretrieve(url,filename=filename,reporthook= self.DownloadHook)
            else:
                urllib.request.urlretrieve(url,filename=filename,reporthook= self.DownloadHook)
            self.WriteLogs(json.dumps({'name':'Download File','total':0,'used':0,'pre':0,'speed':0, 'status': 0}))
        except:
            if self.timeoutCount > 5: return
            self.timeoutCount += 1
            time.sleep(5)
            self.DownloadFile(url,filename)

    #下载文件进度回调
    def DownloadHook(self,count, blockSize, totalSize):
        used = count * blockSize
        pre1 = int((100.0 * used / totalSize))
        if self.pre != pre1:
            dspeed = used / (time.time() - self.oldTime)
            speed = {'name':'Download File','total':totalSize,'used':used,'pre':self.pre,'speed':dspeed,'status': 0}
            self.WriteLogs(json.dumps(speed))
            self.pre = pre1

    #写输出日志
    def WriteLogs(self,logMsg):
        fp = open(self.logPath,'w+')
        fp.write(logMsg)
        fp.close()

    #一键安装网站程序
    def SetupPackage(self, get):
        """
            一键部署网站
        """
        self.WriteLogs(
            json.dumps({'name': 'Create a new website...', 'total': 0, 'used': 0, 'pre': 0, 'speed': 0, 'status': 0}))
        # 检查项目目录
        path = get.get('path')
        try:
            if os.path.isdir(path):
                with os.scandir(path) as it:
                    if any(it):
                        return public.return_message(-1, 0, public.lang("The directory is not empty."))
        except PermissionError:
            return public.return_message(-1, 0, public.lang("You do not have access to this directory."))

        from panel_site_v2 import panelSite
        site_obj = panelSite()
        res = site_obj.AddSite(get, multiple=1)
        if res['status'] != 0:
            self.WriteLogs(json.dumps(
                {'name': f'Website creation failed: {res['message']}', 'total': 0, 'used': 0, 'pre': 0, 'speed': 0,
                 'status': 1}))
            return public.return_message(-1, 0, res['message'])

        try:
            res_data = {}
            res_data['databaseStatus'] = res['message']['databaseStatus']

            # 检查数据库是否安装
            if not os.path.exists(public.get_setup_path() +'/mysql/bin/mysql'):
                res_data['databaseStatus'] = False
                res['message']['databaseErrorMsg'] = public.lang("The MYSQL database has not been installed. Please add the database manually!")

            if res_data['databaseStatus']:
                res_data['databaseUser'] = res['message']['databaseUser']
                res_data['databasePass'] = res['message']['databasePass']
                res_data['databaseName'] = res['message']['databaseUser']
            else:
                res_data['databaseErrorMsg'] = res['message']['databaseErrorMsg']
                res_data['databaseUser'] = ''
                res_data['databasePass'] = ''
                res_data['databaseName'] = ''

            # 取基础信息
            name = get.dname
            site_id = res['message']['siteId']
            php_version = get.version
            find = public.M('sites').where('id=?', (site_id,)).field('id,path,name').find()
            if not find:
                self.WriteLogs(json.dumps({'name':f'Website creation failed.','total':0,'used':0,'pre':0,'speed':0,'status': 1}))
                raise ValueError( public.lang('Website creation failed.'))

            path = find['path']
            pk_version = get.get('pk_version')
            if path.replace('//','/') == '/': raise ValueError( public.lang("Dangerous website root directory!"))

            if not get.get('pk_version'): raise ValueError( public.lang("Missing template version parameter!"))

            #获取包信息
            pinfo = self.GetPackageInfo(name, pk_version)
            if not pinfo: raise ValueError( public.lang("The specified package does not exist.!"))

            # PHP 版本
            if get.version not in pinfo['php']:
                raise ValueError( f"Unsupported PHP version! Support: [{pinfo['php']}]")

            #检查本地包
            self.WriteLogs(json.dumps({'name':'Verifying package...','total':0,'used':0,'pre':0,'speed':0, 'status': 0}))
            pack_path = self.__panelPath + '/package'
            if not os.path.exists(pack_path): os.makedirs(pack_path,384)
            packageZip =  pack_path + '/'+ name + '.zip'
            isDownload = False
            if os.path.exists(packageZip):
                md5str = self.GetFileMd5(packageZip)
                if md5str != pinfo['md5']: isDownload = True
            else:
                isDownload = True

            #下载文件
            if isDownload:
                self.WriteLogs(json.dumps({'name':'Downloading file ...','total':0,'used':0,'pre':0,'speed':0, 'status': 0}))
                if pinfo['download']: self.DownloadFile(pinfo['download'], packageZip)

            if not os.path.exists(packageZip): raise ValueError('File download failed!' + packageZip)
            ok = self.set_temp_file(packageZip,path)
            if not ok: raise ValueError( public.lang("Cannot find [aaPanel Auto Deployment Configuration File] in the installation package"))

            #设置权限
            self.WriteLogs(json.dumps({'name':'Setting permissions','total':0,'used':0,'pre':0,'speed':0, 'status': 0}))
            public.ExecShell('chmod -R 755 ' + path)
            public.ExecShell('chown -R www.www ' + path)
            if pinfo['chmod']:
                for chm in pinfo['chmod']:
                    public.ExecShell('chmod -R ' + str(chm['mode']) + ' ' + (path + '/' + chm['path']).replace('//','/'))

            #安装PHP扩展
            self.WriteLogs(json.dumps({'name':'Install the necessary PHP extensions','total':0,'used':0,'pre':0,'speed':0, 'status': 0}))
            import files_v2
            mfile = files_v2.files()
            if type(pinfo['ext']) != list : pinfo['ext'] = pinfo['ext'].strip().split(',')
            if pinfo['ext']:
                pinfo['install_msg'] = "Please wait for the PHP extension installation to be completed.\n" + pinfo['install_msg']
            for ext in pinfo['ext']:
                if ext == 'pathinfo':
                    import config_v2
                    con = config_v2.config()
                    get.version = php_version
                    get.type = 'on'
                    con.setPathInfo(get)
                else:
                    get.name = ext
                    get.version = php_version
                    get.type = '1'
                    mfile.InstallSoft(get)

            #解禁PHP函数
            if 'enable_functions' in pinfo:
                try:
                    if type(pinfo['enable_functions']) == str : pinfo['enable_functions'] = pinfo['enable_functions'].strip().split(',')
                    php_f = public.GetConfigValue('setup_path') + '/php/' + php_version + '/etc/php.ini'
                    php_c = public.readFile(php_f)
                    rep = "disable_functions\\s*=\\s{0,1}(.*)\n"
                    tmp = re.search(rep,php_c).groups()
                    disable_functions = tmp[0].split(',')
                    for fun in pinfo['enable_functions']:
                        fun = fun.strip()
                        if fun in disable_functions: disable_functions.remove(fun)
                    disable_functions = ','.join(disable_functions)
                    php_c = re.sub(rep, 'disable_functions = ' + disable_functions + "\n", php_c)
                    public.writeFile(php_f,php_c)
                    public.phpReload(php_version)
                except:pass

            #执行额外shell进行依赖安装
            self.WriteLogs(json.dumps({'name':'Execute extra SHELL','total':0,'used':0,'pre':0,'speed':0, 'status': 0}))
            if os.path.exists(path+'/install.sh'):
                public.ExecShell('cd '+path+' && bash ' + 'install.sh ' + find['name'] + " &> /tmp/dep_install.log")
                public.ExecShell('rm -f ' + path+'/install.sh')

            #是否执行Composer
            if os.path.exists(path + '/composer.json'):
                self.WriteLogs(json.dumps({'name':'Execute Composer','total':0,'used':0,'pre':0,'speed':0, 'status': 0}))
                if not os.path.exists(path + '/composer.lock'):
                    execPHP = '/www/server/php/' + php_version +'/bin/php'
                    if execPHP:
                        phpini = '/www/server/php/' + php_version + '/etc/php.ini'
                        phpiniConf = public.readFile(phpini)
                        phpiniConf = phpiniConf.replace('proc_open,proc_get_status,','')
                        public.writeFile(phpini,phpiniConf)
                        public.ExecShell('nohup cd '+path+' && '+execPHP+' /usr/bin/composer install -vvv > /tmp/composer.log 2>&1 &')

            #写伪静态
            self.WriteLogs(json.dumps({'name':'Set URL rewrite','total':0,'used':0,'pre':0,'speed':0, 'status': 0}))
            swfile = path + '/nginx.rewrite'
            if os.path.exists(swfile):
                rewriteConf = public.readFile(swfile)
                dwfile = self.__panelPath + '/vhost/rewrite/' + find['name'] + '.conf'
                public.writeFile(dwfile,rewriteConf)

            swfile = path + '/.htaccess'
            if os.path.exists(swfile):
                swpath = (path + '/'+ pinfo['run'] + '/.htaccess').replace('//','/')
                if pinfo['run'] != '/' and not os.path.exists(swpath):
                    public.writeFile(swpath, public.readFile(swfile))

            #删除伪静态文件
            public.ExecShell("rm -f " + path + '/*.rewrite')

            #删除多余文件
            rm_file = path + '/index.html'
            if os.path.exists(rm_file):
                rm_file_body = public.readFile(rm_file)
                if rm_file_body.find('panel-heading') != -1: os.remove(rm_file)

            #设置运行目录
            self.WriteLogs(json.dumps({'name':'Set the run directory','total':0,'used':0,'pre':0,'speed':0, 'status': 0}))
            if pinfo['run'] != '/':
                site_obj.SetSiteRunPath(public.to_dict_obj({"id":find['id'],"runPath":pinfo['run']}))

            #导入数据
            self.WriteLogs(json.dumps({'name':'Import database','total':0,'used':0,'pre':0,'speed':0, 'status': 0}))
            if os.path.exists(path+'/import.sql'):
                databaseInfo = public.M('databases').where('pid=?',(find['id'],)).field('username,password').find()
                if databaseInfo:
                    public.ExecShell('/www/server/mysql/bin/mysql -u' + databaseInfo['username'] + ' -p' + databaseInfo['password'] + ' ' + databaseInfo['username'] + ' < ' + path + '/import.sql')
                    public.ExecShell('rm -f ' + path + '/import.sql')
                    siteConfigFile = (path + '/' + pinfo['config']).replace('//','/')
                    if os.path.exists(siteConfigFile):
                        siteConfig = public.readFile(siteConfigFile)
                        siteConfig = siteConfig.replace('BT_DB_USERNAME',databaseInfo['username'])
                        siteConfig = siteConfig.replace('BT_DB_PASSWORD',databaseInfo['password'])
                        siteConfig = siteConfig.replace('BT_DB_NAME',databaseInfo['username'])
                        public.writeFile(siteConfigFile,siteConfig)

            #清理文件和目录
            if 'remove_file' in pinfo:
                self.WriteLogs(json.dumps({'name':'Delete unnecessary files','total':0,'used':0,'pre':0,'speed':0, 'status': 0}))
                if type(pinfo['remove_file']) == str : pinfo['remove_file'] = pinfo['remove_file'].strip().split(',')

                for f_path in pinfo['remove_file']:
                    if not f_path: continue
                    filename = (path + '/' + f_path).replace('//','/')
                    if os.path.exists(filename):
                        if not os.path.isdir(filename):
                            if f_path.find('.user.ini') != -1:
                                public.ExecShell("chattr -i " + filename)
                            os.remove(filename)
                        else:
                            public.ExecShell("rm -rf " + filename)

            public.serviceReload()

            res_data['dname'] = name
            res_data['php_version'] = php_version
            res_data['site_path'] = path
            res_data['site_name'] = find['name']
            res_data['install_msg'] = pinfo['install_msg'] if pinfo['install_msg'] else ''

            # 埋点
            public.set_module_logs("one_deployment",f"one_deployment_{name}")
            public.set_module_logs("one_deployment","one_deployment_total")
            self.WriteLogs(json.dumps({'name':'Deployment completed','total':0,'used':0,'pre':0,'speed':0,'status': 1}))
            return public.return_message(0, 0, res_data)
        except Exception as e:
            # 回滚删除网站
            try:
                site_obj.DeleteSite(public.to_dict_obj({'id': site_id,'webname':find['name'],'ftp':1,'database':1,'path':1}))
            except:
                pass
            self.WriteLogs(json.dumps({'name':f'Deployment failed：{e}','total':0,'used':0,'pre':0,'speed':0,'status': 1}))
            return public.return_message(-1, 0, str(e))


    # 处理临时文件并解压
    def set_temp_file(self, filename, path):
        check_res = public.ExecShell('unzip -t ' + filename)
        if check_res[1].find('errors detected') != -1 or check_res[1].find('cannot find') != -1:
            self.WriteLogs(json.dumps(
                {'name': 'Error: The compressed file is damaged or not a valid ZIP file.', 'total': 0, 'used': 0, 'pre': 0, 'speed': 0,'status': 0}))
            return False

        self.WriteLogs(json.dumps({'name': 'The file is being decompressed and saved to the target directory....', 'total': 0, 'used': 0, 'pre': 0, 'speed': 0,'status': 0}))

        if not os.path.exists(path):
            os.makedirs(path)

        unzip_cmd = 'unzip -o ' + filename + ' -d ' + path
        public.ExecShell(unzip_cmd)

        if os.path.exists(path):
            self.WriteLogs(json.dumps({'name': 'Compression completed', 'total': 100, 'used': 100, 'pre': 100, 'speed': 0,'status': 0}))
            return True
        else:
            return False

    def copy_to(self,src,dst):
        try:
            if src[-1] == '/': src = src[:-1]
            if dst[-1] == '/': dst = dst[:-1]
            if not os.path.exists(src): return False
            if not os.path.exists(dst): os.makedirs(dst)
            import shutil
            for p_name in os.listdir(src):
                f_src = src + '/' + p_name
                f_dst = dst + '/' + p_name
                if os.path.isdir(f_src):
                    print(shutil.copytree(f_src,f_dst))
                else:
                    print(shutil.copyfile(f_src,f_dst))
            return True
        except: return False

    #获取进度
    def GetSpeed(self,get):
        try:
            if not os.path.exists(self.logPath):return public.returnMsg(False, public.lang("There are currently no deployment tasks!"))
            return json.loads(public.readFile(self.logPath))
        except:
            return {'name':'Ready to deploy','total':0,'used':0,'pre':0,'speed':0, 'status': 1}

    #获取包信息
    def GetPackageInfo(self,name, version):
        data = self.GetDepList(None)
        if not data: return False
        downUrl = public.get_url() + '/install/package'
        for info in data['list']:
            if info['name'] == name:
                for v in info['version_list']:
                    if version == v['version']:
                        v['download'] = v['download'].replace('{Download}', downUrl)
                        return v
        return False

    #检查指定包是否存在
    def CheckPackageExists(self,name):
        data = self.GetDepList(None)
        if not data: return False
        for info in data['list']:
            if info['name'] == name: return True

        return False

    #文件的MD5值
    def GetFileMd5(self,filename):
        if not os.path.isfile(filename): return False
        import hashlib
        myhash = hashlib.md5()
        f = open(filename,'rb')
        while True:
            b = f.read(8096)
            if not b :
                break
            myhash.update(b)
        f.close()
        return myhash.hexdigest()

    #获取站点标识
    def GetSiteId(self,get):
        return public.M('sites').where('name=?',(get.webname,)).getField('id')

    # 邮局插件安装roundcube调用  目录放到 'plugin/mail_sys';
    def SetupPackage_roundcube(self, get):
        name = get.dname
        site_name = get.site_name
        php_version = get.php_version
        # 取基础信息
        find = public.M('sites').where('name=?', (site_name,)).field('id,path').find()
        path = find['path']

        pinfo = {
            "username": "",
            "ps": "Free and Open Source Webmail Software",
            "php": "72,73,74,80",
            "run": "",
            "name": "roundcube",
            "title": "Roundcube",
            "type": 6,
            "chmod": "",
            "ext": "pathinfo,exif",
            "version": "1.6.11",
            "install": "",
            "download": "https://node.aapanel.com/install/package/roundcubemail.zip",
            "password": "",
            "config": "/config/config.inc.php",
            "md5": "785660db6540692b5c0eb240b41816e9"
        }

        # 检查本地包
        self.WriteLogs(
            json.dumps({'name': "Verifying package...", 'total': 0, 'used': 0, 'pre': 0, 'speed': 0,'status': 0}))
        # 安装包
        packageZip = 'plugin/mail_sys/' + name + '.zip'

        isDownload = False
        if os.path.exists(packageZip):
            md5str = self.GetFileMd5(packageZip)
            if md5str != pinfo['md5']:
                isDownload = True
        else:
            isDownload = True

        # 删除多余文件
        rm_file = path + '/index.html'
        if os.path.exists(rm_file):
            os.remove(rm_file)

        # 下载文件
        if isDownload:
            self.WriteLogs(
                json.dumps({'name': "Download", 'total': 0, 'used': 0, 'pre': 0, 'speed': 0,'status': 0}))
            self.DownloadFile(pinfo['download'], packageZip)

        if not os.path.exists(packageZip):
            return public.returnMsg(False, public.lang("File download failed!"))

        self.WriteLogs(json.dumps({'name': "Unpacking the package...", 'total': 0, 'used': 0, 'pre': 0, 'speed': 0,'status': 0}))
        public.ExecShell('unzip -o ' + packageZip + ' -d ' + path + '/')


        # 设置权限
        self.WriteLogs(
            json.dumps({'name': public.GetMsg("SET_PERMISSION"), 'total': 0, 'used': 0, 'pre': 0, 'speed': 0,'status': 0}))
        public.ExecShell('chmod -R 755 ' + path)
        public.ExecShell('chown -R www.www ' + path)

        if pinfo['chmod'] != "":
            access = pinfo['chmod'].split(',')
            for chm in access:
                tmp = chm.split('|')
                if len(tmp) != 2: continue;
                public.ExecShell('chmod -R ' + tmp[0] + ' ' + path + '/' + tmp[1])

        # # 安装PHP扩展
        # self.WriteLogs(json.dumps(
        #     {'name': public.GetMsg("INSTALL_NECESSARY_PHP_EXT"), 'total': 0, 'used': 0, 'pre': 0, 'speed': 0}))
        # if pinfo['ext'] != '':
        #     exts = pinfo['ext'].split(',')
        #     import files
        #     mfile = files.files()
        #     for ext in exts:
        #         if ext == 'pathinfo':
        #             import config
        #             con = config.config()
        #             get.version = php_version
        #             get.type = 'on'
        #             con.setPathInfo(get)
        #         else:
        #             get.name = ext
        #             get.version = php_version
        #             get.type = '1'
        #             mfile.InstallSoft(get)

        # 执行额外shell进行依赖安装
        self.WriteLogs(
            json.dumps({'name': public.GetMsg("EXECUTE_EXTRA_SHELL"), 'total': 0, 'used': 0, 'pre': 0, 'speed': 0,'status': 0}))
        if os.path.exists(path + '/install.sh'):
            public.ExecShell('cd ' + path + ' && bash ' + 'install.sh')
            public.ExecShell('rm -f ' + path + '/install.sh')



        # 是否执行Composer
        if os.path.exists(path + '/composer.json'):
            self.WriteLogs(json.dumps({'name': 'Execute Composer', 'total': 0, 'used': 0, 'pre': 0, 'speed': 0,'status': 0}))
            if not os.path.exists(path + '/composer.lock'):
                execPHP = '/www/server/php/' + php_version + '/bin/php'
                if execPHP:
                    if public.get_url().find('125.88'):
                        public.ExecShell(
                            'cd ' + path + ' && ' + execPHP + ' /usr/bin/composer config repo.packagist composer https://packagist.phpcomposer.com')
                    import panelSite
                    phpini = '/www/server/php/' + php_version + '/etc/php.ini'
                    phpiniConf = public.readFile(phpini)
                    phpiniConf = phpiniConf.replace('proc_open,proc_get_status,', '')
                    public.writeFile(phpini, phpiniConf)
                    public.ExecShell(
                        'nohup cd ' + path + ' && ' + execPHP + ' /usr/bin/composer install -vvv > /tmp/composer.log 2>&1 &')

        # 写伪静态
        self.WriteLogs(
            json.dumps({'name': public.GetMsg("SET_URL_REWRITE"), 'total': 0, 'used': 0, 'pre': 0, 'speed': 0,'status': 0}))
        swfile = path + '/nginx.rewrite'
        if os.path.exists(swfile):
            rewriteConf = public.readFile(swfile)
            dwfile = self.__panelPath + '/vhost/rewrite/' + site_name + '.conf'
            public.writeFile(dwfile, rewriteConf)

        # 删除伪静态文件
        public.ExecShell("rm -f " + path + '/*.rewrite')

        # 设置运行目录
        self.WriteLogs(json.dumps({'name': public.GetMsg("SET_RUN_DIR"), 'total': 0, 'used': 0, 'pre': 0, 'speed': 0,'status': 0}))
        if pinfo['run'] != '/':
            import panelSite
            siteObj = panelSite.panelSite()
            mobj = obj()
            mobj.id = find['id']
            mobj.runPath = pinfo['run']
            # return find['id']
            siteObj.SetSiteRunPath(mobj)

        # 导入数据
        self.WriteLogs(json.dumps({'name': public.GetMsg("IMPORT_DB"), 'total': 0, 'used': 0, 'pre': 0, 'speed': 0,'status': 0}))

        if os.path.exists(path + '/import.sql'):
            databaseInfo = public.M('databases').where('pid=?', (find['id'],)).field('username,password').find()

            if databaseInfo:
                public.ExecShell('/www/server/mysql/bin/mysql -u' + databaseInfo['username'] + ' -p' + databaseInfo[
                    'password'] + ' ' + databaseInfo['username'] + ' < ' + path + '/import.sql')

                public.ExecShell('rm -f ' + path + '/import.sql')

                # /www/wwwroot/moyumao.top + '/' + /config/config.inc.php
                siteConfigFile = path + '/' + pinfo['config']
                if os.path.exists(siteConfigFile):

                    siteConfig = public.readFile(siteConfigFile)
                    siteConfig = siteConfig.replace('BT_DB_USERNAME', databaseInfo['username'])
                    siteConfig = siteConfig.replace('BT_DB_PASSWORD', databaseInfo['password'])
                    siteConfig = siteConfig.replace('BT_DB_NAME', databaseInfo['username'])
                    # public.print_log("写入数据库文件  ---{}".format(siteConfigFile))
                    public.writeFile(siteConfigFile, siteConfig)


        public.serviceReload()
        # 提交安装统计
        import threading
        import requests
        threading.Thread(target=requests.post, kwargs={
            'url': '{}/api/panel/panel_count_daily'.format(public.OfficialApiBase()),
            'data': {
                'name': 'webmail_Roundcube',
            }}).start()

        self.WriteLogs(
            json.dumps({'name': public.GetMsg("READY_DEPLOY"), 'total': 0, 'used': 0, 'pre': 0, 'speed': 0,'status': 1}))

        return public.returnMsg(True, pinfo)
