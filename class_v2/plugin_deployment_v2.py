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

    #获取列表
    def GetList(self,get):
        self.GetCloudList(get)
        jsonFile = self.__panelPath + '/data/deployment_list.json'
        if not os.path.exists(jsonFile): return public.returnMsg(False, public.lang("Profile does not exist!"))
        data = {}
        data = self.get_input_list(json.loads(public.readFile(jsonFile)))

        if not hasattr(get,'type'):
            get.type = 0
        else:
            get.type = int(get.type)
        if not hasattr(get,'search'):
            search = None
            m = 0
        else:
            if sys.version_info[0] == 2:
                search = get.search.encode('utf-8').lower()
            else:
                search = get.search.lower()
            m = 1

        tmp = []
        for d in data['list']:
            i=0
            if get.type > 0:
                if get.type == d['type']: i+=1
            else:
                i+=1
            if search:
                if d['name'].lower().find(search) != -1: i+=1
                if d['title'].lower().find(search) != -1: i+=1
                if d['ps'].lower().find(search) != -1: i+=1
                if get.type > 0 and get.type != d['type']: i -= 1

            if i>m:
                del(d['versions'][0]['download'])
                del(d['versions'][0]['md5'])
                d = self.get_icon(d)
                tmp.append(d)

        data['list'] = tmp
        return data

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
        data = {}
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

    #从云端获取列表
    def GetCloudList(self,get):
        try:
            jsonFile = self.__setupPath + '/deployment_list.json'
            if not 'package' in session or not os.path.exists(jsonFile) or hasattr(get,'force'):
                downloadUrl = 'http://www.bt.cn/api/panel/get_deplist'
                pdata = public.get_pdata()
                tmp = json.loads(public.httpPost(downloadUrl,pdata,30))
                if not tmp: return public.returnMsg(False, public.lang("Failed to get from the cloud!"))
                public.writeFile(jsonFile,json.dumps(tmp))
                session['package'] = True
                return public.returnMsg(True, public.lang("Update completed!"))
            return public.returnMsg(True, public.lang("No need to update!"))
        except:
            return public.returnMsg(False, public.lang("Failed to get from the cloud!"))



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
            self.WriteLogs(json.dumps({'name':'Download File','total':0,'used':0,'pre':0,'speed':0}))
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
            speed = {'name':'Download File','total':totalSize,'used':used,'pre':self.pre,'speed':dspeed}
            self.WriteLogs(json.dumps(speed))
            self.pre = pre1

    #写输出日志
    def WriteLogs(self,logMsg):
        fp = open(self.logPath,'w+')
        fp.write(logMsg)
        fp.close()

    #一键安装网站程序
    #param string name 程序名称
    #param string site_name 网站名称
    #param string php_version PHP版本
    def SetupPackage(self,get):
        name = get.dname
        site_name = get.site_name
        php_version = get.php_version
        #取基础信息
        find = public.M('sites').where('name=?',(site_name,)).field('id,path,name').find()
        if not  'path' in find:
            return public.returnMsg(False, public.lang("Site not exist!"))
        path = find['path']
        if path.replace('//','/') == '/': return public.returnMsg(False, public.lang("Dangerous website root directory!"))
        #获取包信息
        pinfo = self.GetPackageInfo(name)
        id = pinfo['id']
        if not pinfo: return public.returnMsg(False, public.lang("The specified package does not exist.!"))

        #检查本地包
        self.WriteLogs(json.dumps({'name':'Verifying package...','total':0,'used':0,'pre':0,'speed':0}))
        pack_path = self.__panelPath + '/package'
        if not os.path.exists(pack_path): os.makedirs(pack_path,384)
        packageZip =  pack_path + '/'+ name + '.zip'
        isDownload = False
        if os.path.exists(packageZip):
            md5str = self.GetFileMd5(packageZip)
            if md5str != pinfo['versions'][0]['md5']: isDownload = True
        else:
            isDownload = True

        #下载文件
        if isDownload:
            self.WriteLogs(json.dumps({'name':'Downloading file ...','total':0,'used':0,'pre':0,'speed':0}))
            if pinfo['versions'][0]['download']: self.DownloadFile('http://www.bt.cn/api/Pluginother/get_file?fname=' + pinfo['versions'][0]['download'], packageZip)

        if not os.path.exists(packageZip): return public.returnMsg(False,'File download failed!' + packageZip)

        pinfo = self.set_temp_file(packageZip,path)
        if not pinfo: return public.returnMsg(False, public.lang("Cannot find [aaPanel Auto Deployment Configuration File] in the installation package"))

        #设置权限
        self.WriteLogs(json.dumps({'name':'Setting permissions','total':0,'used':0,'pre':0,'speed':0}))
        public.ExecShell('chmod -R 755 ' + path)
        public.ExecShell('chown -R www.www ' + path)
        if pinfo['chmod']:
            for chm in pinfo['chmod']:
                public.ExecShell('chmod -R ' + str(chm['mode']) + ' ' + (path + '/' + chm['path']).replace('//','/'))

        #安装PHP扩展
        self.WriteLogs(json.dumps({'name':'Install the necessary PHP extensions','total':0,'used':0,'pre':0,'speed':0}))
        import files
        mfile = files.files();
        if type(pinfo['php_ext']) != list : pinfo['php_ext'] = pinfo['php_ext'].strip().split(',')
        for ext in pinfo['php_ext']:
            if ext == 'pathinfo':
                import config
                con = config.config()
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
        self.WriteLogs(json.dumps({'name':'Execute extra SHELL','total':0,'used':0,'pre':0,'speed':0}))
        if os.path.exists(path+'/install.sh'):
            public.ExecShell('cd '+path+' && bash ' + 'install.sh ' + find['name'] + " &> install.log")
            public.ExecShell('rm -f ' + path+'/install.sh')

        #是否执行Composer
        if os.path.exists(path + '/composer.json'):
            self.WriteLogs(json.dumps({'name':'Execute Composer','total':0,'used':0,'pre':0,'speed':0}))
            if not os.path.exists(path + '/composer.lock'):
                execPHP = '/www/server/php/' + php_version +'/bin/php'
                if execPHP:
                    if public.get_url().find('125.88'):
                        public.ExecShell('cd ' +path+' && '+execPHP+' /usr/bin/composer config repo.packagist composer https://packagist.phpcomposer.com')
                    import panelSite
                    phpini = '/www/server/php/' + php_version + '/etc/php.ini'
                    phpiniConf = public.readFile(phpini)
                    phpiniConf = phpiniConf.replace('proc_open,proc_get_status,','')
                    public.writeFile(phpini,phpiniConf)
                    public.ExecShell('nohup cd '+path+' && '+execPHP+' /usr/bin/composer install -vvv > /tmp/composer.log 2>&1 &')

        #写伪静态
        self.WriteLogs(json.dumps({'name':'Set URL rewrite','total':0,'used':0,'pre':0,'speed':0}))
        swfile = path + '/nginx.rewrite'
        if os.path.exists(swfile):
            rewriteConf = public.readFile(swfile)
            dwfile = self.__panelPath + '/vhost/rewrite/' + site_name + '.conf'
            public.writeFile(dwfile,rewriteConf)

        swfile = path + '/.htaccess'
        if os.path.exists(swfile):
            swpath = (path + '/'+ pinfo['run_path'] + '/.htaccess').replace('//','/')
            if pinfo['run_path'] != '/' and not os.path.exists(swpath):
                public.writeFile(swpath, public.readFile(swfile))

                
        #删除伪静态文件
        public.ExecShell("rm -f " + path + '/*.rewrite')

        #删除多余文件
        rm_file = path + '/index.html'
        if os.path.exists(rm_file):
            rm_file_body = public.readFile(rm_file)
            if rm_file_body.find('panel-heading') != -1: os.remove(rm_file)

        #设置运行目录
        self.WriteLogs(json.dumps({'name':'Set the run directory','total':0,'used':0,'pre':0,'speed':0}))
        if pinfo['run_path'] != '/':
            import panelSite
            siteObj = panelSite.panelSite()
            mobj = obj()
            mobj.id = find['id']
            mobj.runPath = pinfo['run_path']
            siteObj.SetSiteRunPath(mobj)

        #导入数据
        self.WriteLogs(json.dumps({'name':'Import database','total':0,'used':0,'pre':0,'speed':0}))
        if os.path.exists(path+'/import.sql'):
            databaseInfo = public.M('databases').where('pid=?',(find['id'],)).field('username,password').find()
            if databaseInfo:
                public.ExecShell('/www/server/mysql/bin/mysql -u' + databaseInfo['username'] + ' -p' + databaseInfo['password'] + ' ' + databaseInfo['username'] + ' < ' + path + '/import.sql')
                public.ExecShell('rm -f ' + path + '/import.sql')
                siteConfigFile = (path + '/' + pinfo['db_config']).replace('//','/')
                if os.path.exists(siteConfigFile):
                    siteConfig = public.readFile(siteConfigFile)
                    siteConfig = siteConfig.replace('BT_DB_USERNAME',databaseInfo['username'])
                    siteConfig = siteConfig.replace('BT_DB_PASSWORD',databaseInfo['password'])
                    siteConfig = siteConfig.replace('BT_DB_NAME',databaseInfo['username'])
                    public.writeFile(siteConfigFile,siteConfig)

        #清理文件和目录
        self.WriteLogs(json.dumps({'name':'清理多余的文件','total':0,'used':0,'pre':0,'speed':0}))
        if type(pinfo['remove_file']) == str : pinfo['remove_file'] = pinfo['remove_file'].strip().split(',')
        print(pinfo['remove_file'])
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
        if id: self.depTotal(id)
        self.WriteLogs(json.dumps({'name':'Ready to deploy','total':0,'used':0,'pre':0,'speed':0}))
        return public.returnMsg(True,pinfo)


    #处理临时文件
    def set_temp_file(self,filename,path):
        public.ExecShell("rm -rf " + self.__tmp + '/*')
        self.WriteLogs(json.dumps({'name':'Unpacking the package...','total':0,'used':0,'pre':0,'speed':0}))
        public.ExecShell('unzip -o '+filename+' -d ' + self.__tmp)
        auto_config = 'auto_install.json'
        p_info = self.__tmp + '/' + auto_config
        p_tmp = self.__tmp
        p_config = None
        if not os.path.exists(p_info):
            d_path = None
            for df in os.walk(self.__tmp):
                if len(df[2]) < 3: continue
                if not auto_config in df[2]: continue
                if not os.path.exists(df[0] + '/' + auto_config): continue
                d_path = df[0]
            if d_path:
                tmp_path = d_path
                auto_file = tmp_path + '/' + auto_config
                if os.path.exists(auto_file):
                    p_info = auto_file
                    p_tmp = tmp_path
        if os.path.exists(p_info):
            try:
                p_config = json.loads(public.readFile(p_info))
                os.remove(p_info)
                i_ndex_html = path + '/index.html'
                if os.path.exists(i_ndex_html): os.remove(i_ndex_html)
                if not self.copy_to(p_tmp,path): public.ExecShell((r"\cp -arf " + p_tmp + '/. ' + path + '/').replace('//','/'))
            except: pass
        public.ExecShell("rm -rf " + self.__tmp + '/*')
        return p_config


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


    #提交安装统计  todo 改提交aapanel
    def depTotal(self,id):
        import panelAuth
        p = panelAuth.panelAuth()
        pdata = p.create_serverid(None);
        pdata['pid'] = id;
        p_url = 'http://www.bt.cn/api/pluginother/create_order_okey'
        public.httpPost(p_url,pdata)

    #获取进度
    def GetSpeed(self,get):
        try:
            if not os.path.exists(self.logPath):return public.returnMsg(False, public.lang("There are currently no deployment tasks!"))
            return json.loads(public.readFile(self.logPath))
        except:
            return {'name':'Ready to deploy','total':0,'used':0,'pre':0,'speed':0}

    #获取包信息
    def GetPackageInfo(self,name):
        data = self.GetDepList(None)
        if not data: return False
        for info in data['list']:
            if info['name'] == name:
                return info
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
            json.dumps({'name': "Verifying package...", 'total': 0, 'used': 0, 'pre': 0, 'speed': 0}))
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
                json.dumps({'name': "Download", 'total': 0, 'used': 0, 'pre': 0, 'speed': 0}))
            self.DownloadFile(pinfo['download'], packageZip)

        if not os.path.exists(packageZip):
            return public.returnMsg(False, public.lang("File download failed!"))

        self.WriteLogs(json.dumps({'name': "Unpacking the package...", 'total': 0, 'used': 0, 'pre': 0, 'speed': 0}))
        public.ExecShell('unzip -o ' + packageZip + ' -d ' + path + '/')


        # 设置权限
        self.WriteLogs(
            json.dumps({'name': public.GetMsg("SET_PERMISSION"), 'total': 0, 'used': 0, 'pre': 0, 'speed': 0}))
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
            json.dumps({'name': public.GetMsg("EXECUTE_EXTRA_SHELL"), 'total': 0, 'used': 0, 'pre': 0, 'speed': 0}))
        if os.path.exists(path + '/install.sh'):
            public.ExecShell('cd ' + path + ' && bash ' + 'install.sh')
            public.ExecShell('rm -f ' + path + '/install.sh')



        # 是否执行Composer
        if os.path.exists(path + '/composer.json'):
            self.WriteLogs(json.dumps({'name': 'Execute Composer', 'total': 0, 'used': 0, 'pre': 0, 'speed': 0}))
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
            json.dumps({'name': public.GetMsg("SET_URL_REWRITE"), 'total': 0, 'used': 0, 'pre': 0, 'speed': 0}))
        swfile = path + '/nginx.rewrite'
        if os.path.exists(swfile):
            rewriteConf = public.readFile(swfile)
            dwfile = self.__panelPath + '/vhost/rewrite/' + site_name + '.conf'
            public.writeFile(dwfile, rewriteConf)

        # 删除伪静态文件
        public.ExecShell("rm -f " + path + '/*.rewrite')

        # 设置运行目录
        self.WriteLogs(json.dumps({'name': public.GetMsg("SET_RUN_DIR"), 'total': 0, 'used': 0, 'pre': 0, 'speed': 0}))
        if pinfo['run'] != '/':
            import panelSite
            siteObj = panelSite.panelSite()
            mobj = obj()
            mobj.id = find['id']
            mobj.runPath = pinfo['run']
            # return find['id']
            siteObj.SetSiteRunPath(mobj)

        # 导入数据
        self.WriteLogs(json.dumps({'name': public.GetMsg("IMPORT_DB"), 'total': 0, 'used': 0, 'pre': 0, 'speed': 0}))

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
            json.dumps({'name': public.GetMsg("READY_DEPLOY"), 'total': 0, 'used': 0, 'pre': 0, 'speed': 0}))

        return public.returnMsg(True, pinfo)

