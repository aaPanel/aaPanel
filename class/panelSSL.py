#coding: utf-8
#-------------------------------------------------------------------
# 宝塔Linux面板
#-------------------------------------------------------------------
# Copyright (c) 2015-2016 宝塔软件(http:#bt.cn) All rights reserved.
#-------------------------------------------------------------------
# Author: hwliang <hwl@bt.cn>
#-------------------------------------------------------------------

#------------------------------
# SSL接口
#------------------------------
import public,os,sys,binascii,urllib,json,time,datetime,re
from Crypto import Random
from Crypto.PublicKey import RSA
from Crypto.Cipher import PKCS1_v1_5 as PKCS1_cipher
import base64
try:
    from BTPanel import cache,session
except:
    pass
class panelSSL:
    __APIURL = 'https://www.aapanel.com/api/user'
    __APIURL2 = 'http://www.bt.cn/api/Cert'
    __UPATH = 'data/userInfo.json'
    __PUBKEY = 'data/public.key'
    __userInfo = None
    __PDATA = None
    _check_url = None
    #构造方法
    def __init__(self):
        if os.path.exists(self.__UPATH):
            my_tmp = public.readFile(self.__UPATH)
            if my_tmp:
                try:
                    self.__userInfo = json.loads(my_tmp)
                except:
                    self.__userInfo = {}
            else:
                self.__userInfo = {}
    
    def en_code_rsa(self, data):
        pk = public.readFile(self.__PUBKEY)
        if not pk:
            return False
        pub_k = RSA.importKey(pk)
        cipher = PKCS1_cipher.new(pub_k)
        rsa_text = base64.b64encode(cipher.encrypt(bytes(data.encode("utf8"))))
        return str(rsa_text,encoding='utf-8')

    # 获取Token
    def GetToken(self, get):
        rtmp = ""
        data = {}
        data['identification'] = self.en_code_rsa(get.username)
        data['password'] = self.en_code_rsa(get.password)
        data['from_panel'] = self.en_code_rsa('1')
        try:
            rtmp = public.httpPost(self.__APIURL + '/login', data)
            result = json.loads(rtmp)
            if result['success']:
                bind = 'data/bind.pl'
                if os.path.exists(bind): os.remove(bind)
                userinfo = result['res']['user_data']
                userinfo['token'] = result['res']['access_token']
                public.writeFile(self.__UPATH, json.dumps(userinfo))
                session['focre_cloud'] = True
                return public.return_msg_gettext(True,'Bind successfully')
            else:
                return public.return_msg_gettext(False,'Invalid username or email or password! please check and try again!')
        except Exception as ex:
            bind = 'data/bind.pl'
            if os.path.exists(bind): os.remove(bind)
            return public.return_msg_gettext(False, '%s<br>%s' % (public.get_msg_gettext('Failed to connect server!'), str(rtmp)))

    #删除Token
    def DelToken(self,get):
        uinfo = public.readFile(self.__UPATH)
        try:
            uinfo = json.loads(uinfo)
            public.writeFile(self.__UPATH,json.dumps({'server_id':uinfo['server_id']}))
        except:
            public.ExecShell("rm -f " + self.__UPATH)
        session['focre_cloud'] = True

        return public.return_msg_gettext(True,'Unbound!')
    
    #获取用户信息
    def GetUserInfo(self,get):
        result = {}
        try:
            if self.__userInfo:
                userTmp = {}
                userTmp['username'] = self.__userInfo['email'][0:3]+'****'+self.__userInfo['email'][-4:]
                result['status'] = True
                result['msg'] = public.get_msg_gettext('Got successfully!')
                result['data'] = userTmp
            else:
                userTmp = {}
                userTmp['username'] = public.get_msg_gettext('Please bind your account!')
                result['status'] = False
                result['msg'] = public.get_msg_gettext('Please bind your account!')
                result['data'] = userTmp
        except:
            userTmp = {}
            userTmp['username'] = public.get_msg_gettext('Please bind your account!')
            result['status'] = False
            result['msg'] = public.get_msg_gettext('Please bind your account!')
            result['data'] = userTmp
        return result

    #获取产品列表
    def get_product_list(self,get):
        result = self.request('get_product_list')
        return result

    #获取商业证书订单列表
    def get_order_list(self,get):
        result = self.request('get_order_list')
        return result

    #获指定商业证书订单
    def get_order_find(self,get):
        self.__PDATA['data']['oid'] = get.oid
        result = self.request('get_order_find')
        return result

    #下载证书
    def download_cert(self,get):
        self.__PDATA['data']['oid'] = get.oid
        result = self.request('download_cert')
        return result

    #部署指定商业证书
    def set_cert(self,get):
        siteName = get.siteName
        certInfo = self.get_order_find(get)
        path = '/www/server/panel/vhost/cert/' + siteName
        if not os.path.exists(path):
            public.ExecShell('mkdir -p ' + path)
        csrpath = path+"/fullchain.pem"
        keypath = path+"/privkey.pem"
        pidpath = path+"/certOrderId"

        other_file = path + '/partnerOrderId'
        if os.path.exists(other_file): os.remove(other_file)
        other_file = path + '/README'
        if os.path.exists(other_file): os.remove(other_file)

        public.writeFile(keypath,certInfo['privateKey'])
        public.writeFile(csrpath,certInfo['certificate']+"\n"+certInfo['caCertificate'])
        public.writeFile(pidpath,get.oid)
        import panelSite
        panelSite.panelSite().SetSSLConf(get)
        public.serviceReload()
        return public.return_msg_gettext(True,'Setup successfully!')

    #生成商业证书支付订单
    def apply_order_pay(self,args):
        self.__PDATA['data'] = json.loads(args.pdata)
        result = self.request('apply_cert_order')
        return result

    #检查商业证书支付状态
    def get_pay_status(self,args):
        self.__PDATA['data']['oid'] = args.oid
        result = self.request('get_pay_status')
        return result

    #提交商业证书订单到CA
    def apply_order(self,args):
        self.__PDATA['data']['oid'] = args.oid
        result = self.request('apply_cert')
        if result['status'] == True:
            self.__PDATA['data'] = {}
            result['verify_info'] = self.get_verify_info(args)
        return result

    #获取商业证书验证信息
    def get_verify_info(self,args):
        self.__PDATA['data']['oid'] = args.oid
        verify_info = self.request('get_verify_info')
        is_file_verify = 'fileName' in verify_info
        verify_info['paths'] = []
        verify_info['hosts'] = []
        for domain in verify_info['domains']:
            if is_file_verify:
                siteRunPath = self.get_domain_run_path(domain)
                if not siteRunPath:
                    if domain[:4] == 'www.': domain = domain[:4]
                    verify_info['paths'].append(verify_info['path'].replace('example.com',domain))
                    continue
                verify_path = siteRunPath + '/.well-known/pki-validation'
                if not os.path.exists(verify_path):
                    os.makedirs(verify_path)
                verify_file = verify_path + '/' + verify_info['fileName']
                if os.path.exists(verify_file): continue
                public.writeFile(verify_file,verify_info['content'])
            else:
                if domain[:4] == 'www.': domain = domain[:4]
                verify_info['hosts'].append(verify_info['host'] + '.' + domain)
        return verify_info

    #处理验证信息
    def set_verify_info(self,args):
        verify_info = self.get_verify_info(args)
        is_file_verify = 'fileName' in verify_info
        verify_info['paths'] = []
        verify_info['hosts'] = []
        for domain in verify_info['domains']:
            if domain[:2] == '*.': domain = domain[2:]
            if is_file_verify:
                siteRunPath = self.get_domain_run_path(domain)
                if not siteRunPath:
                    if domain[:4] == 'www.': domain = domain[4:]
                    verify_info['paths'].append(verify_info['path'].replace('example.com',domain))
                    continue
                verify_path = siteRunPath + '/.well-known/pki-validation'
                if not os.path.exists(verify_path):
                    os.makedirs(verify_path)
                verify_file = verify_path + '/' + verify_info['fileName']
                if os.path.exists(verify_file): continue
                public.writeFile(verify_file,verify_info['content'])
            else:
                if domain[:4] == 'www.': domain = domain[4:]
                verify_info['hosts'].append(verify_info['host'] + '.' + domain)
        return verify_info


    #获取指定域名的PATH
    def get_domain_run_path(self,domain):
        pid = public.M('domain').where('name=?',(domain,)).getField('pid')
        if not pid: return False
        return self.get_site_run_path(pid)


    def get_site_run_path(self,pid):
        '''
            @name 获取网站运行目录
            @author hwliang<2020-08-05>
            @param pid(int) 网站标识
            @return string
        '''
        siteInfo = public.M('sites').where('id=?',(pid,)).find()
        siteName = siteInfo['name']
        sitePath = siteInfo['path']
        webserver_type = public.get_webserver()
        setupPath = '/www/server'
        path = None
        if webserver_type == 'nginx':
            filename = setupPath + '/panel/vhost/nginx/' + siteName + '.conf'
            if os.path.exists(filename):
                conf = public.readFile(filename)
                rep = r'\s*root\s+(.+);'
                tmp1 = re.search(rep,conf)
                if tmp1: path = tmp1.groups()[0]

        elif webserver_type == 'apache':
            filename = setupPath + '/panel/vhost/apache/' + siteName + '.conf'
            if os.path.exists(filename):
                conf = public.readFile(filename)
                rep = r'\s*DocumentRoot\s*"(.+)"\s*\n'
                tmp1 = re.search(rep,conf)
                if tmp1: path = tmp1.groups()[0]
        else:
            filename = setupPath + '/panel/vhost/openlitespeed/' + siteName + '.conf'
            if os.path.exists(filename):
                conf = public.readFile(filename)
                rep = r"vhRoot\s*(.*)"
                path = re.search(rep,conf)
                if not path:
                    path = None
                else:
                    path = path.groups()[0]

        if not path:
            path = sitePath
        return path

    #验证URL是否匹配
    def check_url_txt(self,args):
        url = args.url
        content = args.content

        import http_requests
        res = http_requests.get(url,s_type='curl',timeout=6,verify=False)
        result = res.text
        if not result: return 0

        if result.find('11001') != -1 or result.find('curl: (6)') != -1: return -1
        if result.find('curl: (7)') != -1 or res.status_code in [403,401]: return -5
        if result.find('Not Found') != -1 or result.find('not found') != -1 or res.status_code in [404]:return -2
        if result.find('timed out') != -1:return -3
        if result.find('301') != -1 or result.find('302') != -1 or result.find('Redirecting...') != -1 or res.status_code in [301,302]:return -4
        if result == content:return 1
        return 0

    #更换验证方式
    def again_verify(self,args):
        self.__PDATA['data']['oid'] = args.oid
        self.__PDATA['data']['dcvMethod'] = args.dcvMethod
        result = self.request('again_verify')
        return result

    #获取商业证书验证结果
    def get_verify_result(self,args):
        self.__PDATA['data']['oid'] = args.oid
        verify_info = self.request('get_verify_result')
        if verify_info['status'] in ['COMPLETE',False]: return verify_info
        is_file_verify = 'CNAME_CSR_HASH' != verify_info['data']['dcvList'][0]['dcvMethod']
        verify_info['paths'] = []
        verify_info['hosts'] = []
        if verify_info['data']['application']['status'] == 'ongoing':
            return public.return_msg_gettext(False,'订单出现问题，CA正在人工验证，若24小时内依然出现此提示，请联系宝塔')
        for dinfo in verify_info['data']['dcvList']:
            is_https = dinfo['dcvMethod'] == 'HTTPS_CSR_HASH'
            if is_https:
                is_https = 's'
            else:
                is_https = ''
            domain = dinfo['domainName']
            if domain[:2] == '*.': domain = domain[2:]
            dinfo['domainName'] = domain
            if is_file_verify:
                siteRunPath = self.get_domain_run_path(domain)
                if domain[:4] == 'www.': domain = domain[4:]

                status = 0
                url = 'http'+ is_https +'://'+ domain +'/.well-known/pki-validation/' + verify_info['data']['DCVfileName']
                get = public.dict_obj()
                get.url = url
                get.content = verify_info['data']['DCVfileContent']
                status = self.check_url_txt(get)

                verify_info['paths'].append({'url':url,'status':status})
                if not siteRunPath: continue

                verify_path = siteRunPath + '/.well-known/pki-validation'
                if not os.path.exists(verify_path):
                    os.makedirs(verify_path)
                verify_file = verify_path + '/' + verify_info['data']['DCVfileName']
                if os.path.exists(verify_file): continue
                public.writeFile(verify_file,verify_info['data']['DCVfileContent'])
            else:
                if domain[:4] == 'www.': domain = domain[4:]
                verify_info['hosts'].append(verify_info['data']['DCVdnsHost'] + '.' + domain)

        return verify_info

    #取消订单
    def cancel_cert_order(self,args):
        self.__PDATA['data']['oid'] = args.oid
        result = self.request('cancel_cert_order')
        return result

    #发送请求
    def request(self,dname):
        self.__PDATA['data'] = json.dumps(self.__PDATA['data'])
        result= public.return_msg_gettext(False,'The request failed, please try again later!')
        try:
            result = public.httpPost(self.__APIURL2 + '/' + dname,self.__PDATA)
            result = json.loads(result)
        except:
            pass
        return result
    #获取订单列表
    def GetOrderList(self,get):
        if hasattr(get,'siteName'):
            path =   '/etc/letsencrypt/live/'+ get.siteName + '/partnerOrderId'
            if os.path.exists(path):
                self.__PDATA['data']['partnerOrderId'] = public.readFile(path)
            else:
                path = '/www/server/panel/vhost/cert/' + get.siteName + '/partnerOrderId'
                if os.path.exists(path):
                    self.__PDATA['data']['partnerOrderId'] = public.readFile(path)

        self.__PDATA['data'] = self.De_Code(self.__PDATA['data'])
        rs = public.httpPost(self.__APIURL + '/GetSSLList',self.__PDATA)
        try:
            result = json.loads(rs)
        except: return public.return_msg_gettext(False,'Failed to get, please try again later!')

        result['data'] = self.En_Code(result['data'])
        for i in range(len(result['data'])):
            result['data'][i]['endtime'] =   self.add_months(result['data'][i]['createTime'],result['data'][i]['validityPeriod'])
        return result
    
    #计算日期增加(月)
    def add_months(self,dt,months):
        import calendar
        dt = datetime.datetime.fromtimestamp(dt/1000)
        month = dt.month - 1 + months
        year = dt.year + month // 12
        month = month % 12 + 1

        day = min(dt.day,calendar.monthrange(year,month)[1])
        return (time.mktime(dt.replace(year=year, month=month, day=day).timetuple()) + 86400) * 1000
    
    
    #申请证书
    def GetDVSSL(self,get):
        get.id = public.M('domain').where('name=?',(get.domain,)).getField('pid')
        if hasattr(get,'siteName'):
            get.path = public.M('sites').where('id=?',(get.id,)).getField('path')
        else:
            get.siteName = public.M('sites').where('id=?',(get.id,)).getField('name')
        
        #当申请二级域名为www时，检测主域名是否绑定到同一网站
        if get.domain[:4] == 'www.':
            if not public.M('domain').where('name=? AND pid=?',(get.domain[4:],get.id)).count():
                return public.return_msg_gettext(False,"Apply for [{}] certificate to verify [{}] Please bind [{}] and resolve to the site!",(get.domain,get.domain[4:],get.domain[4:]))

        #检测是否开启强制HTTPS
        if not self.CheckForceHTTPS(get.siteName):
            return public.return_msg_gettext(False,'[Force HTTPS] is enabled on the current website, please turn off this function before applying for an SSL certificate!')

        #获取真实网站运行目录
        runPath = self.GetRunPath(get)
        if runPath != False and runPath != '/': get.path +=  runPath


        #提前模拟测试验证文件值是否正确
        authfile = get.path + '/.well-known/pki-validation/fileauth.txt'
        if not self.CheckDomain(get):
            if not os.path.exists(authfile):
                return public.return_msg_gettext(False,'Cannot create [{}]',(authfile,))
            else:
                msg = '''{err_msg}<br><a class="btlink" href="{c_url}" target="_blank">{c_url}</a> <br><br>
                <p></b>{err_msg1}</b></p>
                {err_msg2}<br>
                {err_msg3}<br>
                {err_msg4}'''.format(c_url = self._check_url,
                                    err_msg=public.get_msg_gettext('Cannot access verification file correctly'),
                                    err_msg1=public.get_msg_gettext('Possible reason:'),
                                    err_msg2=public.get_msg_gettext('1. The resolution is not correct, or the resolution is not effective [Please resolve the domain name correctly, or wait for the resolution to take effect and try again]'),
                                    err_msg3=public.get_msg_gettext('2. Check if there is 301/302 redirection set up [please temporarily turn off the redirection related configuration]'),
                                    err_msg4=public.get_msg_gettext('3. Check whether the website is set to force HTTPS [please turn off the force HTTPS function temporarily]'))
                return public.return_msg_gettext(False,msg)
        
        action = 'GetDVSSL'
        if hasattr(get,'partnerOrderId'):
            self.__PDATA['data']['partnerOrderId'] = get.partnerOrderId
            action = 'ReDVSSL'
        
        self.__PDATA['data']['domain'] = get.domain
        self.__PDATA['data'] = self.De_Code(self.__PDATA['data'])
        result = public.httpPost(self.__APIURL + '/' + action,self.__PDATA)
        try:
            result = json.loads(result)
        except: return result
        result['data'] = self.En_Code(result['data'])

        try:
            if 'authValue' in result['data'].keys():
                public.writeFile(authfile,result['data']['authValue'])
        except:
            try:
                public.writeFile(authfile,result['data']['authValue'])
            except:
                return result

        return result

    #检测是否强制HTTPS
    def CheckForceHTTPS(self,siteName):
        conf_file = '/www/server/panel/vhost/nginx/{}.conf'.format(siteName)
        if not os.path.exists(conf_file):
            return True

        conf_body = public.readFile(conf_file)
        if not conf_body: return True
        if conf_body.find('HTTP_TO_HTTPS_START') != -1:
            return False
        return True
    
    #获取运行目录
    def GetRunPath(self,get):
        if hasattr(get,'siteName'):
            get.id = public.M('sites').where('name=?',(get.siteName,)).getField('id')
        else:
            get.id = public.M('sites').where('path=?',(get.path,)).getField('id')
        if not get.id: return False
        import panelSite
        result = panelSite.panelSite().GetSiteRunPath(get)
        return result['runPath']


    #检查域名是否解析
    def CheckDomain(self,get):
        try:
            #创建目录
            spath = get.path + '/.well-known/pki-validation'
            if not os.path.exists(spath): public.ExecShell("mkdir -p '" + spath + "'")

            #生成并写入检测内容
            epass = public.GetRandomString(32)
            public.writeFile(spath + '/fileauth.txt',epass)

            #检测目标域名访问结果
            if get.domain[:4] == 'www.':   #申请二级域名为www时检测主域名
                get.domain = get.domain[4:]

            import http_requests
            self._check_url = 'http://127.0.0.1/.well-known/pki-validation/fileauth.txt'
            result = http_requests.get(self._check_url,s_type='curl',timeout=6,headers={"host":get.domain}).text
            self.__test = result
            if result == epass: return True
            self._check_url = self._check_url.replace('127.0.0.1', get.domain)
            return False
        except:
            self._check_url = self._check_url.replace('127.0.0.1', get.domain)
            return False
    
    #确认域名
    def Completed(self,get):
        self.__PDATA['data']['partnerOrderId'] = get.partnerOrderId
        self.__PDATA['data'] = self.De_Code(self.__PDATA['data'])
        if hasattr(get,'siteName'):
            get.path = public.M('sites').where('name=?',(get.siteName,)).getField('path')
            runPath = self.GetRunPath(get)
            if runPath != False and runPath != '/': get.path +=  runPath
            tmp = public.httpPost(self.__APIURL + '/SyncOrder',self.__PDATA)
            try:
                sslInfo = json.loads(tmp)
            except:
                return public.return_msg_gettext(False,tmp)

            sslInfo['data'] = self.En_Code(sslInfo['data'])
            try:
                spath = get.path + '/.well-known/pki-validation'
                if not os.path.exists(spath): public.ExecShell("mkdir -p '" + spath + "'")
                public.writeFile(spath + '/fileauth.txt',sslInfo['data']['authValue'])
            except:
                return public.return_msg_gettext(False,'Verification error!')
        try:
            result = json.loads(public.httpPost(self.__APIURL + '/Completed',self.__PDATA))
            if 'data' in result:
                result['data'] = self.En_Code(result['data'])
        except:
            result = public.return_msg_gettext(True,'Checking...')
        n = 0;
        my_ok = False
        while True:
            if n > 5: break
            time.sleep(5)
            rRet = json.loads(public.httpPost(self.__APIURL + '/SyncOrder',self.__PDATA))
            n +=1
            rRet['data'] = self.En_Code(rRet['data'])
            try:
                if rRet['data']['stateCode'] == 'COMPLETED': 
                    my_ok = True
                    break
            except: return public.get_error_info()
        if not my_ok: return result
        return rRet
    
    #同步指定订单
    def SyncOrder(self,get):
        self.__PDATA['data']['partnerOrderId'] = get.partnerOrderId
        self.__PDATA['data'] = self.De_Code(self.__PDATA['data'])
        result = json.loads(public.httpPost(self.__APIURL + '/SyncOrder',self.__PDATA))
        result['data'] = self.En_Code(result['data'])
        return result
    
    #获取证书
    def GetSSLInfo(self,get):
        self.__PDATA['data']['partnerOrderId'] = get.partnerOrderId
        self.__PDATA['data'] = self.De_Code(self.__PDATA['data'])
        time.sleep(3)
        result = json.loads(public.httpPost(self.__APIURL + '/GetSSLInfo',self.__PDATA))
        result['data'] = self.En_Code(result['data'])
        if not 'privateKey' in result['data']: return result
        
        #写配置到站点
        if hasattr(get,'siteName'):
            try:
                siteName = get.siteName
                path = '/www/server/panel/vhost/cert/' + siteName
                if not os.path.exists(path):
                    public.ExecShell('mkdir -p ' + path)
                csrpath = path+"/fullchain.pem"
                keypath = path+"/privkey.pem"
                pidpath = path+"/partnerOrderId"
                #清理旧的证书链
                public.ExecShell('rm -f ' + keypath)
                public.ExecShell('rm -f ' + csrpath)
                public.ExecShell('rm -rf ' + path + '-00*')
                public.ExecShell('rm -rf /etc/letsencrypt/archive/' + get.siteName)
                public.ExecShell('rm -rf /etc/letsencrypt/archive/' + get.siteName + '-00*')
                public.ExecShell('rm -f /etc/letsencrypt/renewal/'+ get.siteName + '.conf')
                public.ExecShell('rm -f /etc/letsencrypt/renewal/'+ get.siteName + '-00*.conf')
                public.ExecShell('rm -f ' + path + '/README')
                public.ExecShell('rm -f ' + path + '/certOrderId')

                public.writeFile(keypath,result['data']['privateKey'])
                public.writeFile(csrpath,result['data']['cert']+result['data']['certCa'])
                public.writeFile(pidpath,get.partnerOrderId)
                import panelSite
                panelSite.panelSite().SetSSLConf(get)
                public.serviceReload()
                return public.return_msg_gettext(True,'Setup successfully!')
            except:
                return public.return_msg_gettext(False,'Failed to set')
        result['data'] = self.En_Code(result['data'])
        return result
    
    #部署证书夹证书
    def SetCertToSite(self,get):
        try:
            result = self.GetCert(get)
            if not 'privkey' in result: return result
            siteName = get.siteName
            path = '/www/server/panel/vhost/cert/' + siteName
            if not os.path.exists(path):
                public.ExecShell('mkdir -p ' + path)
            csrpath = path+"/fullchain.pem"
            keypath = path+"/privkey.pem"
            
            #清理旧的证书链
            public.ExecShell('rm -f ' + keypath)
            public.ExecShell('rm -f ' + csrpath)
            public.ExecShell('rm -rf ' + path + '-00*')
            public.ExecShell('rm -rf /etc/letsencrypt/archive/' + get.siteName)
            public.ExecShell('rm -rf /etc/letsencrypt/archive/' + get.siteName + '-00*')
            public.ExecShell('rm -f /etc/letsencrypt/renewal/'+ get.siteName + '.conf')
            public.ExecShell('rm -f /etc/letsencrypt/renewal/'+ get.siteName + '-00*.conf')
            public.ExecShell('rm -f ' + path + '/README')
            if os.path.exists(path + '/certOrderId'): os.remove(path + '/certOrderId')

            public.writeFile(keypath,result['privkey'])
            public.writeFile(csrpath,result['fullchain'])
            import panelSite
            panelSite.panelSite().SetSSLConf(get)
            public.serviceReload()
            return public.return_msg_gettext(True,'Setup successfully!')
        except Exception as ex:
            return public.return_msg_gettext(False,'Failed to set \n{}',(public.get_error_info(),))
    
    #获取证书列表
    def GetCertList(self,get):
        try:
            vpath = '/www/server/panel/vhost/ssl'
            if not os.path.exists(vpath): public.ExecShell("mkdir -p " + vpath)
            data = []
            for d in os.listdir(vpath):
                mpath = vpath + '/' + d + '/info.json'
                if not os.path.exists(mpath): continue
                tmp = public.readFile(mpath)
                if not tmp: continue
                tmp1 = json.loads(tmp)
                data.append(tmp1)
            return data
        except:
            return []
    
    #删除证书
    def RemoveCert(self,get):
        try:
            vpath = '/www/server/panel/vhost/ssl/' + get.certName.replace("*.",'')
            if not os.path.exists(vpath): return public.return_msg_gettext(False,'Certificate does NOT exist!')
            public.ExecShell("rm -rf " + vpath)
            return public.return_msg_gettext(True,'Certificate deleted!')
        except:
            return public.return_msg_gettext(False,'Failed to delete!')
    
    #保存证书
    def SaveCert(self,get):
        try:
            certInfo = self.GetCertName(get)
            if not certInfo: return public.return_msg_gettext(False,'Certificate parsing failed')
            vpath = '/www/server/panel/vhost/ssl/' + certInfo['subject']
            vpath=vpath.replace("*.",'')
            if not os.path.exists(vpath):
                public.ExecShell("mkdir -p " + vpath)
            public.writeFile(vpath + '/privkey.pem',public.readFile(get.keyPath))
            public.writeFile(vpath + '/fullchain.pem',public.readFile(get.certPath))
            public.writeFile(vpath + '/info.json',json.dumps(certInfo))
            return public.return_msg_gettext(True,'Successfully saved certificate!')
        except:
            return public.return_msg_gettext(False,'Failed to save certificate!')
    
    #读取证书
    def GetCert(self,get):
        vpath = os.path.join('/www/server/panel/vhost/ssl' , get.certName.replace("*.",''))
        if not os.path.exists(vpath): return public.return_msg_gettext(False,'Certificate does NOT exist!')
        data = {}
        data['privkey'] = public.readFile(vpath + '/privkey.pem')
        data['fullchain'] = public.readFile(vpath + '/fullchain.pem')
        return data;
    
    #获取证书名称
    def GetCertName(self,get):
        return self.get_cert_init(get.certPath)
        # try:
        #     openssl = '/usr/local/openssl/bin/openssl'
        #     if not os.path.exists(openssl): openssl = 'openssl'
        #     result = public.ExecShell(openssl + " x509 -in "+get.certPath+" -noout -subject -enddate -startdate -issuer")
        #     tmp = result[0].split("\n")
        #     data = {}
        #     data['subject'] = tmp[0].split('=')[-1]
        #     data['notAfter'] = self.strfToTime(tmp[1].split('=')[1])
        #     data['notBefore'] = self.strfToTime(tmp[2].split('=')[1])
        #     if tmp[3].find('O=') == -1:
        #         data['issuer'] = tmp[3].split('CN=')[-1]
        #     else:
        #         data['issuer'] = tmp[3].split('O=')[-1].split(',')[0]
        #     if data['issuer'].find('/') != -1: data['issuer'] = data['issuer'].split('/')[0]
        #     result = public.ExecShell(openssl + " x509 -in "+get.certPath+" -noout -text|grep DNS")
        #     data['dns'] = result[0].replace('DNS:','').replace(' ','').strip().split(',')
        #     return data
        # except:
        #     print(public.get_error_info())
        #     return None


    # 获取指定证书基本信息
    def get_cert_init(self, pem_file):
        if not os.path.exists(pem_file):
            return None
        try:
            import OpenSSL
            result = {}
            x509 = OpenSSL.crypto.load_certificate(
                OpenSSL.crypto.FILETYPE_PEM, public.readFile(pem_file))
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
            if not result['issuer']:
                if hasattr(issuer, 'O'):
                    result['issuer'] = issuer.O

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
                if not result['dns']:
                    for sub in subject:
                        if sub[0] == b'CN':
                            result['subject'] = sub[1].decode()
                            break
                    # result['dns'].append(result['subject'])
                    if 'subject' in result:
                        result['dns'].append(result['subject'])

                else:
                    result['subject'] = result['dns'][0]
            return result
        except:
            return None
    

    # 转换时间
    def strf_date(self, sdate):
        return time.strftime('%Y-%m-%d', time.strptime(sdate, '%Y%m%d%H%M%S'))

    #转换时间
    def strfToTime(self,sdate):
        import time
        return time.strftime('%Y-%m-%d',time.strptime(sdate,'%b %d %H:%M:%S %Y %Z'))
        
    
    #获取产品列表
    def GetSSLProduct(self,get):
        self.__PDATA['data'] = self.De_Code(self.__PDATA['data'])
        result = json.loads(public.httpPost(self.__APIURL + '/GetSSLProduct',self.__PDATA))
        result['data'] = self.En_Code(result['data'])
        return result
    
    #加密数据
    def De_Code(self,data):
        if sys.version_info[0] == 2:
            import urllib
            pdata = urllib.urlencode(data)
            return binascii.hexlify(pdata)
        else:
            import urllib.parse
            pdata = urllib.parse.urlencode(data)
            if type(pdata) == str: pdata = pdata.encode('utf-8')
            return binascii.hexlify(pdata).decode()
    
    #解密数据
    def En_Code(self,data):
        if sys.version_info[0] == 2:
            import urllib
            result = urllib.unquote(binascii.unhexlify(data))
        else:
            import urllib.parse
            if type(data) == str: data = data.encode('utf-8')
            tmp = binascii.unhexlify(data)
            if type(tmp) != str: tmp = tmp.decode('utf-8')
            result = urllib.parse.unquote(tmp)

        if type(result) != str: result = result.decode('utf-8')
        return json.loads(result)

    # 手动一键续签
    def renew_lets_ssl(self, get):
        if not os.path.exists('vhost/cert/crontab.json'):
            return public.return_msg_gettext(False,'There are currently no certificates to renew!')

        old_list = json.loads(public.ReadFile("vhost/cert/crontab.json"))
        cron_list = old_list
        if hasattr(get, 'siteName'):
            if not get.siteName in old_list:
                return public.return_msg_gettext(False,'There is no certificate that can be renewed on the current website..')
            cron_list = {}
            cron_list[get.siteName] = old_list[get.siteName]

        import panelLets
        lets = panelLets.panelLets()

        result = {}
        result['status'] = True
        result['sucess_list']  = []
        result['err_list'] = []
        for siteName in cron_list:
            data = cron_list[siteName]
            ret = lets.renew_lest_cert(data)
            if ret['status']:
                result['sucess_list'].append(siteName)
            else:
                result['err_list'].append({"siteName":siteName,"msg":ret['msg']})
        return result
