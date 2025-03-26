# coding: utf-8
# -------------------------------------------------------------------
# aaPanel
# -------------------------------------------------------------------
# Copyright (c) 2015-2016 aaPanel(www.aapanel.com) All rights reserved.
# -------------------------------------------------------------------
# Author: hwliang <hwl@aapanel.com>
# -------------------------------------------------------------------

# ------------------------------
# SSL接口
# ------------------------------
from panelAuth import panelAuth
import public, os, sys, binascii, urllib, json, time, datetime, re
from ssl_manage import SSLManger  # 新的ssl管理

from Crypto import Random
from Crypto.PublicKey import RSA
from Crypto.Cipher import PKCS1_v1_5 as PKCS1_cipher
import base64

try:
    from BTPanel import cache, session
except:
    pass


class panelSSL:
    # __APIURL = public.GetConfigValue('home') + '/api/Auth'
    # __APIURL2 = public.GetConfigValue('home') + '/api/Cert'
    # __BINDURL = 'https://wafapi.aapanel.com/Auth/GetAuthToken'   # 获取token 获取官网token




    __BINDURL = '{}/api/user'.format(public.OfficialApiBase())  # 获取token 获取官网token
    # __BINDURL = 'http://dev.aapanel.com/api/user'  # 获取token 获取官网token

    __CODEURL = 'https://wafapi.aapanel.com/Auth/GetBindCode'  # 获取绑定验证码
    __UPATH = 'data/userInfo.json'

    # __APIURL = 'http://dev.aapanel.com/api'
    __APIURL = '{}/api'.format(public.OfficialApiBase())

    __PUBKEY = 'data/public.key'

    # 证书购买
    # __APIURL_CERT = '{}/api/cert'.format(public.OfficialApiBase())

    __userInfo = None  # 用户信息  从文件中读取的
    __PDATA = None
    _check_url = None

    # 构造方法
    def __init__(self):
        pdata = {}
        data = {}  # 存放调用接口的参数
        # 记录了用户信息
        if os.path.exists(self.__UPATH):
            my_tmp = public.readFile(self.__UPATH)
            if my_tmp:
                try:
                    self.__userInfo = json.loads(my_tmp)
                except:
                    self.__userInfo = {}
            else:
                self.__userInfo = {}

            try:
                if self.__userInfo:
                    # 记录里没有这两个key
                    pdata['access_key'] = self.__userInfo['access_key']
                    data['secret_key'] = self.__userInfo['secret_key']
                    # pdata['access_key'] = 'test'
                    # data['secret_key'] = '123456'
            except:
                # self.__userInfo = {}
                pdata['access_key'] = 'test'
                data['secret_key'] = '123456'
        else:
            pdata['access_key'] = 'test'
            data['secret_key'] = '123456'
        pdata['data'] = data
        self.__PDATA = pdata

        # public.print_log('初始化------->最后 !!!!!!!!!!!!!!!!!!!用户信息:  {}'.format(self.__userInfo))

    def en_code_rsa(self, data):
        pk = public.readFile(self.__PUBKEY)
        if not pk:
            return False
        pub_k = RSA.importKey(pk)
        cipher = PKCS1_cipher.new(pub_k)
        rsa_text = base64.b64encode(cipher.encrypt(bytes(data.encode("utf8"))))
        return str(rsa_text, encoding='utf-8')

    # 获取Token  最新
    # def GetToken(self, get):
    #     rtmp = ""
    #     data = {}
    #     data['username'] = get.username
    #     data['password'] = public.md5(get.password)
    #     data['serverid'] = panelAuth().get_serverid()
    #     pdata = {}
    #     pdata['data'] = self.De_Code(data)
    #     try:
    #         rtmp = public.httpPost(self.__BINDURL, pdata)
    #         result = json.loads(rtmp)
    #         result['data'] = self.En_Code(result['data'])
    #         if result['data']:
    #             result['data']['serverid'] = data['serverid']
    #             public.writeFile(self.__UPATH, json.dumps(result['data']))
    #             public.flush_plugin_list()
    #         del (result['data'])
    #         session['focre_cloud'] = True
    #         return result
    #     except Exception as ex:
    #         # bind = 'data/bind.pl'
    #         # if os.path.exists(bind): os.remove(bind)
    #         # return public.returnMsg(False,'连接服务器失败!<br>' + str(ex))
    #         raise public.error_conn_cloud(str(ex))
    #
    # # 删除Token 最新
    # def DelToken(self, get):
    #     if os.path.exists(self.__UPATH): os.remove(self.__UPATH)
    #     session['focre_cloud'] = True
    #     return public.returnMsg(True, public.lang("SSL_BTUSER_UN"))

    # 获取Token  todo  在用
    def GetToken(self, get):
        rtmp = ""
        data = {}
        data['identification'] = self.en_code_rsa(get.username)
        # data['username'] = self.en_code_rsa(get.username)
        data['password'] = self.en_code_rsa(get.password)
        data['from_panel'] = self.en_code_rsa('1')  # 1 代表从面板登录
        try:
            rtmp = public.httpPost(self.__APIURL + '/user/login', data)

            # public.print_log("写入用户信息  @@@@222 {}".format(self.__APIURL + '/user/login'))
            result = json.loads(rtmp)
            # public.print_log("写入用户信息  @@@@ {}".format(rtmp))
            # public.print_log("写入用户信息  @@@@ {}".format(result))
            if result['success']:
                bind = 'data/bind.pl'
                if os.path.exists(bind): os.remove(bind)
                userinfo = result['res']['user_data']
                userinfo['token'] = result['res']['access_token']
                # 用户信息写入文件
                public.writeFile(self.__UPATH, json.dumps(userinfo))
                # if bool:
                #     # public.print_log("写入用户信息  成功 {}".format(userinfo))
                # else:
                #     public.print_log("写入用户信息  失败")

                session['focre_cloud'] = True
                return public.return_msg_gettext(True, public.lang("Bind successfully"))
                # return result
            else:
                return public.return_msg_gettext(False, public.lang("Invalid username or email or password! please check and try again!"))
        except Exception as ex:
            bind = 'data/bind.pl'
            if os.path.exists(bind): os.remove(bind)
            return public.return_msg_gettext(False, '%s<br>%s' % (
                public.lang("Failed to connect server!"), str(rtmp)))

    # 删除Token  todo
    def DelToken(self, get):
        uinfo = public.readFile(self.__UPATH)
        try:
            uinfo = json.loads(uinfo)
            public.writeFile(self.__UPATH, json.dumps({'server_id': uinfo['server_id']}))
        except:
            public.ExecShell("rm -f " + self.__UPATH)
        session['focre_cloud'] = True

        return public.return_msg_gettext(True, public.lang("Unbound!"))

    # 获取用户信息  todo
    # def GetUserInfo(self, get):
    #     result = {}
    #
    #     # public.print_log("@@@@@@@@@@获取用户信息  开始----- {}".format(self.__userInfo))
    #
    #     if self.__userInfo:
    #         userTmp = {}
    #         userTmp['username'] = self.__userInfo['username'][0:3] + '****' + self.__userInfo['username'][-4:]
    #         result['status'] = True
    #         result['msg'] = public.lang("SSL_GET_SUCCESS")
    #         result['data'] = userTmp
    #     else:
    #         userTmp = {}
    #         userTmp['username'] = public.lang("SSL_NOT_BTUSER")
    #         result['status'] = False
    #         result['msg'] = public.lang("SSL_NOT_BTUSER")
    #         result['data'] = userTmp
    #     return result

    def GetUserInfo(self, get):
        result = {}
        try:
            if self.__userInfo:
                userTmp = {}
                userTmp['username'] = self.__userInfo['email'][0:3] + '****' + self.__userInfo['email'][-4:]
                result['status'] = True
                result['msg'] = public.lang("Got successfully!")
                result['data'] = userTmp
            else:
                userTmp = {}
                userTmp['username'] = public.lang("Please bind your account!")
                result['status'] = False
                result['msg'] = public.lang("Please bind your account!")
                result['data'] = userTmp
        except:
            userTmp = {}
            userTmp['username'] = public.lang("Please bind your account!")
            result['status'] = False
            result['msg'] = public.lang("Please bind your account!")
            result['data'] = userTmp
        return result

    # 获取产品列表  todo
    # def get_product_list(self, get):
    #     p_type = 'dv'
    #     if 'p_type' in get: p_type = get.p_type
    #     result = self.request('get_product_list?p_type={}'.format(p_type))
    #     return result

    # # 获取产品列表2  todo
    # def get_product_list_v2(self, get):
    #     p_type = 'dv'
    #     if 'p_type' in get: p_type = get.p_type
    #
    #     result = self.request('get_product_list_v2?p_type={}'.format(p_type))
    #     return result

    # 获取产品列表2  todo  产品列表
    def get_product_list_v2(self, get):
        result = self.request('cert/product/list')
        return result

    # 获取商业证书订单列表  todo 用户订单列表
    def get_order_list(self, get):
        result = self.request('cert/user/list')  # 获取当前登录用户的SSL证书列表
        return result


    # 下载证书 todo
    def download_cert(self, get):
        self.__PDATA['uc_id'] = get.uc_id
        result = self.request('cert/user/download')
        return result

    def batch_soft_release(self, get):
        oids = get.oid.split(',')
        finish_list = []
        for oid in oids:
            finish = {'oid': oid}
            self.__PDATA['data']['oid'] = oid
            try:
                finish.update(self.request('soft_release'))
            except:
                finish.update({'status':False,'msg':'fail'})
            finish_list.append(finish)
        return {'status': True, 'msg': "Del success!", 'finish_list': finish_list}

    # 获指定商业证书订单
    def get_order_find(self, get):
        self.__PDATA['uc_id'] = get.uc_id
        result = self.request('cert/user/info')
        return result

    # 获取证书管理员信息  todo
    def get_cert_admin(self, get):
        result = self.request('cert/user/administrator')
        return result

    # 完善资料CA(先支付接口)   todo  可能是支付后的完善信息接口
    def apply_order_ca(self, args):
        pdata = json.loads(args.pdata)

        result = self.check_ssl_caa(pdata['domains'])
        if result:
            return result

        self.__PDATA['data'] = pdata
        result = self.request('cert/user/update_profile')

        return result


    # 部署指定商业证书 todo 部署证书
    def set_cert(self, get):
        siteName = get.siteName
        certInfoall = self.get_order_find(get)

        if certInfoall["success"] is False:
            return public.return_msg_gettext(False, certInfoall["res"])
        certInfo = certInfoall["res"]
        path = '/www/server/panel/vhost/cert/' + siteName
        if not os.path.exists(path):
            public.ExecShell('mkdir -p ' + path)
        csrpath = path + "/fullchain.pem"
        keypath = path + "/privkey.pem"
        pidpath = path + "/certOrderId"

        other_file = path + '/partnerOrderId'
        if os.path.exists(other_file):
            os.remove(other_file)
        other_file = path + '/README'
        if os.path.exists(other_file):
            os.remove(other_file)

        public.writeFile(keypath, certInfo['private_key'])
        public.writeFile(csrpath, certInfo['certificate'] + "\n" + certInfo['ca_certificate'])
        # 改记录 uc_id
        public.writeFile(pidpath, get.uc_id)
        import panelSite
        panelSite.panelSite().SetSSLConf(get)
        public.serviceReload()
        return public.return_msg_gettext(True, public.lang("Setup successfully!"))

    # # 生成商业证书支付订单   暂无
    # def apply_order_pay(self, args):
    #     self.__PDATA['data'] = json.loads(args.pdata)
    #     result = self.check_ssl_caa(self.__PDATA['data']['domains'])
    #     if result: return result
    #     result = self.request('apply_cert_order')
    #     return result

    # 检查CAA记录是否正确
    def check_ssl_caa(self, domains, clist=['sectigo.com', 'digicert.com', 'comodoca.com']):
        '''
            @name 检查CAA记录是否正确
            @param domains 域名列表
            @param clist 正确的记录值关键词
            @return bool
        '''
        try:
            data = {}
            for domain in domains:
                root, zone = public.get_root_domain(domain)
                for d in [domain, root, '_acme-challenge.{}'.format(root), '_acme-challenge.{}'.format(domain)]:
                    ret = public.query_dns(d, 'CAA')
                    if not ret: continue
                    slist = []
                    for val in ret:
                        if val['value'] in clist:
                            return False
                        slist.append(val)

                    if len(slist) > 0:
                        data[d] = slist
            if data:
                result = {}
                result['status'] = False
                result[
                    'msg'] = 'error: There is a CAA record in the DNS resolution of the domain name. Please delete it and apply again '
                result['data'] = json.dumps(data)
                result['caa_list'] = data
                return result
        except:
            pass
        return False


    # 提交商业证书订单到CA
    # def apply_order(self, args):
    #     self.__PDATA['data']['oid'] = args.oid
    #     result = self.request('apply_cert')
    #     if result['status'] == True:
    #         self.__PDATA['data'] = {}
    #         result['verify_info'] = self.get_verify_info(args)
    #     return result

    # 获取证书域名验证结果 todo  暂未使用
    #  用到: 处理验证信息 set_verify_info    完善资料 apply_order_ca  续签证书 renew_cert_order
    def get_verify_info(self, args):
        self.__PDATA['uc_id'] = args.uc_id
        verify_info = self.request('cert/user/validate_domains')
        if verify_info['success']:
            return "success"
        return "error"

        # is_file_verify = 'fileName' in verify_info
        # verify_info['paths'] = []
        # verify_info['hosts'] = []
        # for domain in verify_info['domains']:
        #     if is_file_verify:
        #         siteRunPath = self.get_domain_run_path(domain)
        #         if not siteRunPath:
        #             # if domain[:4] == 'www.': domain = domain[:4]
        #             verify_info['paths'].append(verify_info['path'].replace('example.com', domain))
        #             continue
        #         verify_path = siteRunPath + '/.well-known/pki-validation'
        #         if not os.path.exists(verify_path):
        #             os.makedirs(verify_path)
        #         verify_file = verify_path + '/' + verify_info['fileName']
        #         if os.path.exists(verify_file): continue
        #         public.writeFile(verify_file, verify_info['content'])
        #     else:
        #         original_domain = domain
        #         # if domain[:4] == 'www.': domain = domain[:4]
        #         verify_info['hosts'].append(verify_info['host'] + '.' + domain)
        #         if 'auth_to' in args:
        #             root, zone = public.get_root_domain(domain)
        #             res = self.create_dns_record(args['auth_to'], verify_info['host'] + '.' + root,
        #                                          verify_info['value'], original_domain)
        #             print(res)
        # return verify_info

    # 处理验证信息  todo  如果传参 要传uc_id
    def set_verify_info(self, args):
        # self.__PDATA['uc_id'] = args.uc_id   # 新增
        verify_info = self.get_verify_info(args)
        is_file_verify = 'fileName' in verify_info
        verify_info['paths'] = []
        verify_info['hosts'] = []
        for domain in verify_info['domains']:
            if domain[:2] == '*.': domain = domain[2:]
            if is_file_verify:
                siteRunPath = self.get_domain_run_path(domain)
                if not siteRunPath:
                    # if domain[:4] == 'www.': domain = domain[4:]
                    verify_info['paths'].append(verify_info['path'].replace('example.com', domain))
                    continue
                verify_path = siteRunPath + '/.well-known/pki-validation'
                if not os.path.exists(verify_path):
                    os.makedirs(verify_path)
                verify_file = verify_path + '/' + verify_info['fileName']
                if os.path.exists(verify_file): continue
                public.writeFile(verify_file, verify_info['content'])
            else:
                original_domain = domain
                # if domain[:4] == 'www.': domain = domain[4:]
                verify_info['hosts'].append(verify_info['host'] + '.' + domain)

                if 'auth_to' in args:
                    root, zone = public.get_root_domain(domain)
                    self.create_dns_record(args['auth_to'], verify_info['host'] + '.' + root,
                                           verify_info['value'], original_domain)
        return verify_info

    # 获取指定域名的PATH
    def get_domain_run_path(self, domain):
        pid = public.M('domain').where('name=?', (domain,)).getField('pid')
        if not pid: return False
        return self.get_site_run_path(pid)

    # 获取网站运行目录
    def get_site_run_path(self, pid):
        '''
            @name 获取网站运行目录
            @author hwliang<2020-08-05>
            @param pid(int) 网站标识
            @return string
        '''
        siteInfo = public.M('sites').where('id=?', (pid,)).find()
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
                tmp1 = re.search(rep, conf)
                if tmp1: path = tmp1.groups()[0]

        elif webserver_type == 'apache':
            filename = setupPath + '/panel/vhost/apache/' + siteName + '.conf'
            if os.path.exists(filename):
                conf = public.readFile(filename)
                rep = r'\s*DocumentRoot\s*"(.+)"\s*\n'
                tmp1 = re.search(rep, conf)
                if tmp1: path = tmp1.groups()[0]
        else:
            filename = setupPath + '/panel/vhost/openlitespeed/' + siteName + '.conf'
            if os.path.exists(filename):
                conf = public.readFile(filename)
                rep = r"vhRoot\s*(.*)"
                path = re.search(rep, conf)
                if not path:
                    path = None
                else:
                    path = path.groups()[0]

        if not path:
            path = sitePath
        return path

    # 验证URL是否匹配
    def check_url_txt(self, args, timeout=5):
        url = args.url
        content = args.content

        import http_requests
        res = http_requests.get(url, s_type='curl', timeout=timeout)
        result = res.text
        if not result: return 0

        if result.find('11001') != -1 or result.find('curl: (6)') != -1: return -1
        if result.find('curl: (7)') != -1 or res.status_code in [403, 401]: return -5
        if result.find('Not Found') != -1 or result.find('not found') != -1 or res.status_code in [404]: return -2
        if result.find('timed out') != -1: return -3
        if result.find('301') != -1 or result.find('302') != -1 or result.find(
                'Redirecting...') != -1 or res.status_code in [301, 302]: return -4
        if result == content: return 1
        return 0

    # 更换验证方式  # todo? ['data']
    def again_verify(self, args):
        self.__PDATA['uc_id'] = args.uc_id
        self.__PDATA['dcv_method'] = args.dcv_method
        result = self.request('cert/user/update_dcv')
        return result

    # 获取商业证书验证结果
    def get_verify_result(self, args):
        self.__PDATA['uc_id'] = args.uc_id
        res = self.request('cert/user/validate')
        if res['success'] is False:
            return res
        verify_info = res['res']

        if verify_info['status'] in ['COMPLETE', False]:
            return verify_info

        is_file_verify = 'CNAME_CSR_HASH' != verify_info['data']['dcvList'][0]['dcvMethod']
        verify_info['paths'] = []
        verify_info['hosts'] = []
        if verify_info['data']['application']['status'] == 'ongoing':
            return public.return_msg_gettext(False, public.lang("In verification, please contact aaPanel if the audit still fails after 24 hours"))

        for dinfo in verify_info['data']['dcvList']:
            is_https = dinfo['dcvMethod'] == 'HTTPS_CSR_HASH'
            if is_https:
                is_https = 's'
            else:
                is_https = ''
            domain = dinfo['domainName']
            if domain[:2] == '*.':
                domain = domain[2:]
            dinfo['domainName'] = domain

            if is_file_verify:
                # 判断是否是Springboot 项目
                if public.M('sites').where('id=?', (
                        public.M('domain').where('name=?', (dinfo['domainName'])).getField('pid'),)).getField(
                    'project_type') == 'Java' or public.M('sites').where('id=?', (
                        public.M('domain').where('name=?', (dinfo['domainName'])).getField('pid'),)).getField(
                    'project_type') == 'Go' or public.M('sites').where('id=?', (
                        public.M('domain').where('name=?', (dinfo['domainName'])).getField('pid'),)).getField(
                    'project_type') == 'Other':
                    siteRunPath = '/www/wwwroot/java_node_ssl'
                else:
                    siteRunPath = self.get_domain_run_path(domain)
                # if domain[:4] == 'www.': domain = domain[4:]
                status = 0
                url = 'http' + is_https + '://' + domain + '/.well-known/pki-validation/' + verify_info['data'][
                    'DCVfileName']
                get = public.dict_obj()
                get.url = url
                get.content = verify_info['data']['DCVfileContent']
                status = self.check_url_txt(get)

                verify_info['paths'].append({'url': url, 'status': status})
                if not siteRunPath:
                    continue

                verify_path = siteRunPath + '/.well-known/pki-validation'
                if not os.path.exists(verify_path):
                    os.makedirs(verify_path)
                verify_file = verify_path + '/' + verify_info['data']['DCVfileName']
                if os.path.exists(verify_file):
                    continue
                public.writeFile(verify_file, verify_info['data']['DCVfileContent'])
            else:
                # if domain[:4] == 'www.': domain = domain[4:]
                domain, subb = public.get_root_domain(domain)
                dinfo['domainName'] = domain
                verify_info['hosts'].append(verify_info['data']['DCVdnsHost'] + '.' + domain)

        return verify_info

    # 取消订单  暂无
    def cancel_cert_order(self, args):
        self.__PDATA['data']['oid'] = args.oid
        result = self.request('cancel_cert_order')
        return result

    # 单独购买人工安装服务
    def apply_cert_install_pay(self, args):
        '''
            @name 单独购买人工安装服务
            @param args<dict_obj>{
                'uc_id'<int> 订单ID
            }
        '''
        self.__PDATA['uc_id'] = args.uc_id
        result = self.request('cert/order/deployment_assistance')
        return result

    # 生成商业证书支付订单  todo  生成支付订单 下单支付
    def apply_cert_order_pay(self, args):
        pdata = json.loads(args.pdata)
        self.__PDATA['data'] = pdata
        result = self.request('cert/order/create')
        return result

    # 模拟支付
    # def pay_test(self, args):
    #     out_trade_no = args.out_trade_no
    #     # /api/common/stripe/{out_trade_no}
    #     # result = self.request_test('order/pay')
    #     result = public.return_msg_gettext(False, '测试用 模拟支付!')
    #     url = "https://dev.aapanel.com/api/common/stripe/" + out_trade_no
    #     response_data = public.httpGet(url)
    #
    #     # public.print_log("******************** url: {}".format(url))
    #
    #     try:
    #         result = json.loads(response_data)
    #     except:
    #         pass
    #     return result



    # 申请证书  ???
    def ApplyDVSSL(self, get):

        """
        申请证书
        """
        if not 'orgName' in get: return public.returnMsg(False, public.lang("missing parameter: orgName"))
        if not 'orgPhone' in get: return public.returnMsg(False, public.lang("missing parameter: orgPhone"))
        if not 'orgPostalCode' in get: return public.returnMsg(False, public.lang("missing parameter: orgPostalCode"))
        if not 'orgRegion' in get: return public.returnMsg(False, public.lang("missing parameter: orgRegion"))
        if not 'orgCity' in get: return public.returnMsg(False, public.lang("missing parameter: orgCity"))
        if not 'orgAddress' in get: return public.returnMsg(False, public.lang("missing parameter: orgAddress"))
        if not 'orgDivision' in get: return public.returnMsg(False, public.lang("missing parameter: orgDivision"))

        get.id = public.M('domain').where('name=?', (get.domain,)).getField('pid')
        if hasattr(get, 'siteName'):
            get.path = public.M('sites').where('id=?', (get.id,)).getField('path')
        else:
            get.siteName = public.M('sites').where('id=?', (get.id,)).getField('name')

        # 当申请二级域名为www时，检测主域名是否绑定到同一网站
        if get.domain[:4] == 'www.':
            if not public.M('domain').where('name=? AND pid=?', (get.domain[4:], get.id)).count():
                return public.returnMsg(False,
                                        "Request for [%s] certificate requires verification [%s] Please bind and resolve [%s] to the site!" % (
                                            get.domain, get.domain[4:], get.domain[4:]))
        # 判断是否是Java项目
        if public.M('sites').where('id=?', (get.id,)).getField('project_type') == 'Java' or public.M('sites').where(
                'id=?', (get.id,)).getField('project_type') == 'Go' or public.M('sites').where('id=?',
                                                                                               (get.id,)).getField(
            'project_type') == 'Other':
            get.path = '/www/wwwroot/java_node_ssl/'
            runPath = ''
        # 判断是否是Node项目
        elif public.M('sites').where('id=?', (get.id,)).getField('project_type') == 'Node':
            get.path = public.M('sites').where('id=?', (get.id,)).getField('path')
            runPath = ''
        # 判断是否是python项目
        elif public.M('sites').where(
                'id=?', (get.id,)).getField('project_type') == 'Python':
            get.path = public.M('sites').where('id=?',
                                               (get.id,)).getField('path')
            runPath = ''
        else:
            runPath = self.GetRunPath(get)
        if runPath != False and runPath != '/': get.path += runPath
        authfile = get.path + '/.well-known/pki-validation/fileauth.txt'
        if not self.CheckDomain(get):
            if not os.path.exists(authfile):
                return public.returnMsg(False, public.lang("Unable to write validation file: {}", authfile))
            else:
                msg = '''can't correct access validation file <br><a class="btlink" href="{c_url}" target="_blank">{c_url}</a> <br><br>
                <p></b>Possible cause：</b></p>
                1、the resolution is not correct, or the resolution does not work [please resolve the domain correctly, or wait for the resolution to work and try again]<br>
                2、 check whether the 301/302 redirection is set [please temporarily turn off the redirection related configuration]<br>
                3、 Check whether the site has HTTPS deployed and set mandatory HTTPS [Please temporarily turn off mandatory HTTPS feature]<br>'''.format(
                    c_url=self._check_url)
                return public.returnMsg(False, msg)

        action = 'ApplyDVSSL'
        if hasattr(get, 'partnerOrderId'):
            self.__PDATA['data']['partnerOrderId'] = get.partnerOrderId
            action = 'ReDVSSL'

        self.__PDATA['data']['domain'] = get.domain
        self.__PDATA['data']['orgPhone'] = get.orgPhone
        self.__PDATA['data']['orgPostalCode'] = get.orgPostalCode
        self.__PDATA['data']['orgRegion'] = get.orgRegion
        self.__PDATA['data']['orgCity'] = get.orgCity
        self.__PDATA['data']['orgAddress'] = get.orgAddress
        self.__PDATA['data']['orgDivision'] = get.orgDivision
        self.__PDATA['data']['orgName'] = get.orgName
        self.__PDATA['data'] = self.De_Code(self.__PDATA['data'])
        try:
            result = public.httpPost(self.__APIURL + 'user/' + action, self.__PDATA)
        except Exception as ex:
            raise public.error_conn_cloud(str(ex))
        try:
            result = json.loads(result)
        except:
            return result
        if 'status' in result:
            if not result['status']: return result
        result['data'] = self.En_Code(result['data'])
        try:
            if not 'authPath' in result['data']: result['data']['authPath'] = '/.well-known/pki-validation/'
            authfile = get.path + result['data']['authPath'] + result['data']['authKey']
        except:
            if 'authKey' in result['data']:
                authfile = get.path + '/.well-known/pki-validation/' + result['data']['authKey']
            else:
                return public.returnMsg(False, public.lang(" Failed to get the validation file!"))

        if 'authValue' in result['data']:
            public.writeFile(authfile, result['data']['authValue'])
        return result


    # 发送请求  todo
    def request(self, dname):
        self.__PDATA['data'] = json.dumps(self.__PDATA['data'])
        url_headers = {
            "authorization": "bt {}".format(self.__userInfo['token'])
        }

        result = public.return_msg_gettext(False, 'Failed to connect to the official website, please try again later!')
        try:
            # response_data = public.httpPost(self.__APIURL + '/' + dname, self.__PDATA)
            response_data = public.httpPost(self.__APIURL + '/' + dname, data=self.__PDATA, headers=url_headers)
        except Exception as ex:
            raise public.error_conn_cloud(str(ex))
        try:
            result = json.loads(response_data)
        except:
            pass
        return result

    # # 发送请求  todo  测试购买证书
    # def request_test(self, dname):
    #     self.__PDATA['data'] = json.dumps(self.__PDATA['data'])
    #     # "Content-Type": "application/json",
    #     url_headers = {
    #         "authorization": "bt {}".format(self.__userInfo['token'])
    #     }
    #
    #     result = public.return_msg_gettext(False, '测试用 The request failed, please try again later!')
    #     try:
    #         response_data = public.httpPost(self.__APIURLtest + '/' + dname, data=self.__PDATA, headers=url_headers)
    #
    #         # public.print_log("******************** url: {}".format(self.__APIURLtest + '/' + dname))
    #
    #     except Exception as ex:
    #         raise public.error_conn_cloud(str(ex))
    #
    #
    #     try:
    #         result = json.loads(response_data)
    #     except:
    #         pass
    #     return result

    # 获取订单列表  ???
    def GetOrderList(self, get):
        if hasattr(get, 'siteName'):
            path = '/etc/letsencrypt/live/' + get.siteName + '/partnerOrderId'
            if os.path.exists(path):
                self.__PDATA['data']['partnerOrderId'] = public.readFile(path)
            else:
                path = '/www/server/panel/vhost/cert/' + get.siteName + '/partnerOrderId'
                if os.path.exists(path):
                    self.__PDATA['data']['partnerOrderId'] = public.readFile(path)

        self.__PDATA['data'] = self.De_Code(self.__PDATA['data'])
        try:
            rs = public.httpPost(self.__APIURL + 'user/GetSSLList', self.__PDATA)
        except Exception as ex:
            raise public.error_conn_cloud(str(ex))
        try:
            result = json.loads(rs)
        except:
            return public.return_msg_gettext(False, public.lang("Failed to get, please try again later!"))

        result['data'] = self.En_Code(result['data'])
        for i in range(len(result['data'])):
            result['data'][i]['endtime'] = self.add_months(result['data'][i]['createTime'],
                                                           result['data'][i]['validityPeriod'])
        return result

    # 计算日期增加(月)
    def add_months(self, dt, months):
        import calendar
        dt = datetime.datetime.fromtimestamp(dt / 1000)
        month = dt.month - 1 + months
        year = dt.year + month // 12
        month = month % 12 + 1

        day = min(dt.day, calendar.monthrange(year, month)[1])
        return (time.mktime(dt.replace(year=year, month=month, day=day).timetuple()) + 86400) * 1000

    # 申请证书
    def GetDVSSL(self, get):
        get.id = public.M('domain').where('name=?', (get.domain,)).getField('pid')
        if hasattr(get, 'siteName'):
            get.path = public.M('sites').where('id=?', (get.id,)).getField('path')
        else:
            get.siteName = public.M('sites').where('id=?', (get.id,)).getField('name')

        # 当申请二级域名为www时，检测主域名是否绑定到同一网站
        if get.domain[:4] == 'www.':
            if not public.M('domain').where('name=? AND pid=?', (get.domain[4:], get.id)).count():
                return public.return_msg_gettext(False,
                                                 "Apply for [{}] certificate to verify [{}] Please bind [{}] and resolve to the site!".format(
                                                     get.domain, get.domain[4:], get.domain[4:]))

        # 检测是否开启强制HTTPS
        if not self.CheckForceHTTPS(get.siteName):
            return public.return_msg_gettext(False, public.lang("[Force HTTPS] is enabled on the current website, please turn off this function before applying for an SSL certificate!"))

        # 获取真实网站运行目录
        runPath = self.GetRunPath(get)
        if runPath != False and runPath != '/': get.path += runPath

        # 提前模拟测试验证文件值是否正确
        authfile = get.path + '/.well-known/pki-validation/fileauth.txt'
        if not self.CheckDomain(get):
            if not os.path.exists(authfile):
                return public.return_msg_gettext(False, 'Cannot create [{}]', (authfile,))
            else:
                msg = ''''Unable to access the verification file<br><a class="btlink" href="{c_url}" target="_blank">{c_url}</a> <br><br>
                <p></b>Possible reasons：</b></p>
                1. Incorrect or ineffective DNS resolution [Please ensure correct domain name resolution or wait for the resolution to take effect and try again]<br>
                2. Check if there are any 301/302 redirects set [Temporarily disable redirect-related configurations]<br>
                3. Check if the website has enforced HTTPS [Temporarily disable the enforced HTTPS feature]<br>'''.format(
                    c_url=self._check_url)
                return public.return_msg_gettext(False, msg)

        action = 'GetDVSSL'
        if hasattr(get, 'partnerOrderId'):
            self.__PDATA['data']['partnerOrderId'] = get.partnerOrderId
            action = 'ReDVSSL'

        self.__PDATA['data']['domain'] = get.domain
        self.__PDATA['data'] = self.De_Code(self.__PDATA['data'])
        result = public.httpPost(self.__APIURL + 'user/' + action, self.__PDATA)
        try:
            result = json.loads(result)
        except:
            return result
        result['data'] = self.En_Code(result['data'])

        try:
            if 'authValue' in result['data'].keys():
                public.writeFile(authfile, result['data']['authValue'])
        except:
            try:
                public.writeFile(authfile, result['data']['authValue'])
            except:
                return result

        return result

    # 检测是否强制HTTPS
    def CheckForceHTTPS(self, siteName):
        conf_file = '/www/server/panel/vhost/nginx/{}.conf'.format(siteName)
        if not os.path.exists(conf_file):
            return True

        conf_body = public.readFile(conf_file)
        if not conf_body: return True
        if conf_body.find('HTTP_TO_HTTPS_START') != -1:
            return False
        return True

    # 获取运行目录
    def GetRunPath(self, get):
        if hasattr(get, 'siteName'):
            get.id = public.M('sites').where('name=?', (get.siteName,)).getField('id')
        else:
            get.id = public.M('sites').where('path=?', (get.path,)).getField('id')
        if not get.id: return False
        import panelSite
        result = panelSite.panelSite().GetSiteRunPath(get)
        return result['runPath']

    # 检查域名是否解析
    def CheckDomain(self, get):
        try:
            # 创建目录
            spath = get.path + '/.well-known/pki-validation'
            if not os.path.exists(spath):
                os.makedirs(spath, 0o755, True)
                # public.ExecShell("mkdir -p '" + spath + "'")

            # 生成并写入检测内容
            epass = public.GetRandomString(32)
            public.writeFile(spath + '/fileauth.txt', epass)

            # 检测目标域名访问结果
            if get.domain[:4] == 'www.':  # 申请二级域名为www时检测主域名
                get.domain = get.domain[4:]

            import http_requests
            self._check_url = 'http://127.0.0.1/.well-known/pki-validation/fileauth.txt'
            result = http_requests.get(self._check_url, s_type='curl', timeout=6, headers={"host": get.domain}).text
            self.__test = result
            if result == epass: return True
            self._check_url = self._check_url.replace('127.0.0.1', get.domain)
            return False
        except:
            self._check_url = self._check_url.replace('127.0.0.1', get.domain)
            return False

    # 确认域名
    def Completed(self, get):
        self.__PDATA['data']['partnerOrderId'] = get.partnerOrderId
        self.__PDATA['data'] = self.De_Code(self.__PDATA['data'])
        if hasattr(get, 'siteName'):
            get.path = public.M('sites').where('name=?', (get.siteName,)).getField('path')
            if public.M('sites').where('id=?',
                                       (public.M('domain').where('name=?', (get.siteName)).getField('pid'),)).getField(
                'project_type') == 'Java' or public.M('sites').where('id=?', (
                    public.M('domain').where('name=?', (get.siteName)).getField('pid'),)).getField(
                'project_type') == 'Go' or public.M('sites').where('id=?', (
                    public.M('domain').where('name=?', (get.siteName)).getField('pid'),)).getField(
                'project_type') == 'Other':
                runPath = '/www/wwwroot/java_node_ssl'
            else:
                runPath = self.GetRunPath(get)
            if runPath != False and runPath != '/': get.path += runPath
            tmp = public.httpPost(self.__APIURL + 'user/SyncOrder', self.__PDATA)
            try:
                sslInfo = json.loads(tmp)
            except:
                return public.return_msg_gettext(False, tmp)

            sslInfo['data'] = self.En_Code(sslInfo['data'])
            try:

                if public.M('sites').where('id=?', (
                        public.M('domain').where('name=?', (get.siteName)).getField('pid'),)).getField(
                    'project_type') == 'Java' or public.M('sites').where('id=?', (
                        public.M('domain').where('name=?', (get.siteName)).getField('pid'),)).getField(
                    'project_type') == 'Go' or public.M('sites').where('id=?', (
                        public.M('domain').where('name=?', (get.siteName)).getField('pid'),)).getField(
                    'project_type') == 'Other':
                    spath = '/www/wwwroot/java_node_ssl/.well-known/pki-validation'
                else:
                    spath = get.path + '/.well-known/pki-validation'
                if not os.path.exists(spath): public.ExecShell("mkdir -p '" + spath + "'")
                public.writeFile(spath + '/' + sslInfo['data']['authKey'], sslInfo['data']['authValue'])
            except:
                return public.return_msg_gettext(False, public.lang("Verification error!"))
        try:
            result = json.loads(public.httpPost(self.__APIURL + 'user/Completed', self.__PDATA))
            if 'data' in result:
                result['data'] = self.En_Code(result['data'])
        except:
            result = public.return_msg_gettext(True, 'Checking...')
        n = 0;
        my_ok = False
        while True:
            if n > 5: break
            time.sleep(5)
            rRet = json.loads(public.httpPost(self.__APIURL + 'user/SyncOrder', self.__PDATA))
            n += 1
            rRet['data'] = self.En_Code(rRet['data'])
            try:
                if rRet['data']['stateCode'] == 'COMPLETED':
                    my_ok = True
                    break
            except:
                return public.get_error_info()
        if not my_ok: return result
        return rRet

    # 同步指定订单
    def SyncOrder(self, get):
        self.__PDATA['data']['partnerOrderId'] = get.partnerOrderId
        self.__PDATA['data'] = self.De_Code(self.__PDATA['data'])
        result = json.loads(public.httpPost(self.__APIURL + 'user/SyncOrder', self.__PDATA))
        result['data'] = self.En_Code(result['data'])
        return result

    # 获取证书
    def GetSSLInfo(self, get):
        self.__PDATA['data']['partnerOrderId'] = get.partnerOrderId
        self.__PDATA['data'] = self.De_Code(self.__PDATA['data'])
        time.sleep(3)
        result = json.loads(public.httpPost(self.__APIURL + 'user/GetSSLInfo', self.__PDATA))
        result['data'] = self.En_Code(result['data'])
        if not 'privateKey' in result['data']: return result

        # 写配置到站点
        if hasattr(get, 'siteName'):
            try:
                siteName = get.siteName
                path = '/www/server/panel/vhost/cert/' + siteName
                if not os.path.exists(path):
                    public.ExecShell('mkdir -p ' + path)
                csrpath = path + "/fullchain.pem"
                keypath = path + "/privkey.pem"
                pidpath = path + "/partnerOrderId"
                # 清理旧的证书链
                public.ExecShell('rm -f ' + keypath)
                public.ExecShell('rm -f ' + csrpath)
                public.ExecShell('rm -rf ' + path + '-00*')
                public.ExecShell('rm -rf /etc/letsencrypt/archive/' + get.siteName)
                public.ExecShell('rm -rf /etc/letsencrypt/archive/' + get.siteName + '-00*')
                public.ExecShell('rm -f /etc/letsencrypt/renewal/' + get.siteName + '.conf')
                public.ExecShell('rm -f /etc/letsencrypt/renewal/' + get.siteName + '-00*.conf')
                public.ExecShell('rm -f ' + path + '/README')
                public.ExecShell('rm -f ' + path + '/certOrderId')

                public.writeFile(keypath, result['data']['privateKey'])
                public.writeFile(csrpath, result['data']['cert'] + result['data']['certCa'])
                public.writeFile(pidpath, get.partnerOrderId)
                import panelSite
                panelSite.panelSite().SetSSLConf(get)
                public.serviceReload()
                return public.return_msg_gettext(True, public.lang("Setup successfully!"))
            except:
                return public.return_msg_gettext(False, public.lang("Failed to set"))
        result['data'] = self.En_Code(result['data'])
        return result

    def GetSiteDomain(self, get):
        """
        @name 获取网站域名对应的站点名
        @param cert_list 证书域名列表
        @auther hezhihong
        return 证书域名对应的站点名字典，如证书域名未绑定则为空
        """
        all_site = []  # 所有站点名列表
        cert_list = []  # 证书域名列表
        site_list = []  # 证书域名列表对应的站点名列表
        all_domain = []  # 所有域名列表
        try:
            cert_list = json.loads(get.cert_list)
        except:
            pass
        result = {}
        # 取所有站点名和所有站点的绑定域名
        all_sites = public.M('sites').field('name').select()
        for site in all_sites:
            all_site.append(site['name'])
            if not cert_list: continue
            tmp_dict = {}
            tmp_dict['name'] = site['name']
            pid = public.M('sites').where("name=?", (site['name'],)).getField('id')
            domain_list = public.M('domain').where("pid=?", (pid,)).field('name').select()
            for domain in domain_list:
                all_domain.append(domain['name'])
        # 取证书域名所在的所有域名列表
        site_domain = []  # 证书域名对应的站点名列表
        if cert_list and all_domain:
            for cert in cert_list:
                d_cert = ''
                if re.match(r"^\*\..*", cert):
                    d_cert = cert.replace('*.', '')
                for domain in all_domain:
                    if cert == domain:
                        site_domain.append(domain)
                    else:
                        replace_str = domain.split('.')[0] + '.'
                        if d_cert and d_cert == domain.replace(replace_str, ''):
                            site_domain.append(domain)
        # 取证书域名对应的站点名
        for site in site_domain:
            site_id = public.M('domain').where("name=?", (site,)).getField('pid')
            site_name = public.M('sites').where("id=?", (site_id,)).getField('name')
            site_list.append(site_name)
        site_list = sorted(set(site_list), key=site_list.index)
        result['all'] = all_site
        result['site'] = site_list
        return result

    def SetBatchCertToSite(self, get):
        """
        @name 批量部署证书
        @auther hezhihong
        """
        ssl_list = []
        if not hasattr(get, 'BatchInfo') or not get.BatchInfo:
            return public.returnMsg(False, public.lang("parameter error"))
        else:
            ssl_list = json.loads(get.BatchInfo)
        if isinstance(ssl_list, list):
            total_num = len(ssl_list)
            resultinfo = {"total": total_num, "success": 0, "faild": 0, "successList": [], "faildList": []}
            successList = []
            faildList = []
            successnum = 0
            failnum = 0
            for Info in ssl_list:
                set_result = {}
                set_result['status'] = True
                get.certName = set_result['certName'] = Info['certName']
                get.siteName = set_result['siteName'] = str(Info['siteName'])  # 站点名称必定为字符串
                get.isBatch = True
                if "ssl_hash" in Info:
                    get.ssl_hash = Info['ssl_hash']
                result = self.SetCertToSite(get)
                if not result or result.get("status") is False:
                    set_result['status'] = False
                    failnum += 1
                    faildList.append(set_result)
                else:
                    successnum += 1
                    successList.append(set_result)
                public.writeSpeed('setssl', successnum + failnum, total_num)
            import firewalls
            get.port = '443'
            get.ps = 'HTTPS'
            firewalls.firewalls().AddAcceptPort(get)
            public.serviceReload()
            resultinfo['success'] = successnum
            resultinfo['faild'] = failnum
            resultinfo['successList'] = successList
            resultinfo['faildList'] = faildList

            if hasattr(get, "set_https_mode") and get.set_https_mode.strip() in (True, 1, "1", "true"):
                import panelSite
                sites_obj = panelSite.panelSite()
                if not sites_obj.get_https_mode():
                    sites_obj.set_https_mode()

        else:
            return public.returnMsg(False, public.lang("Parameter type error"))
        return resultinfo

    # 部署证书夹证书
    def SetCertToSite(self, get):
        """
        @name 兼容批量部署
        @auther hezhihong
        """

        try:
            result = self.GetCert(get)
            if not 'privkey' in result: return result
            siteName = get.siteName
            path = '/www/server/panel/vhost/cert/' + siteName
            if not os.path.exists(path):
                public.ExecShell('mkdir -p ' + path)
            csrpath = path + "/fullchain.pem"
            keypath = path + "/privkey.pem"

            # 清理旧的证书链
            public.ExecShell('rm -f ' + keypath)
            public.ExecShell('rm -f ' + csrpath)
            public.ExecShell('rm -rf ' + path + '-00*')
            public.ExecShell('rm -rf /etc/letsencrypt/archive/' + get.siteName)
            public.ExecShell('rm -rf /etc/letsencrypt/archive/' + get.siteName + '-00*')
            public.ExecShell('rm -f /etc/letsencrypt/renewal/' + get.siteName + '.conf')
            public.ExecShell('rm -f /etc/letsencrypt/renewal/' + get.siteName + '-00*.conf')
            public.ExecShell('rm -f ' + path + '/README')
            if os.path.exists(path + '/certOrderId'): os.remove(path + '/certOrderId')

            public.writeFile(keypath, result['privkey'])
            public.writeFile(csrpath, result['fullchain'])
            import panelSite
            panelSite.panelSite().SetSSLConf(get)
            public.serviceReload()
            return public.return_msg_gettext(True, public.lang("Setup successfully!"))
        except Exception as ex:
            import traceback
            public.print_log(traceback.format_exc())
            public.print_log(f"error : {ex}")
            if 'isBatch' in get: return False
            return public.returnMsg(False, 'SET_ERROR,' + public.get_error_info())

    # 获取证书列表
    def GetCertList(self, get):
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

    # 删除证书
    def RemoveCert(self, get):
        try:
            vpath = '/www/server/panel/vhost/ssl/' + get.certName.replace("*.", '')
            if not os.path.exists(vpath): return public.return_msg_gettext(False, public.lang("Certificate does NOT exist!"))
            public.ExecShell("rm -rf " + vpath)
            return public.return_msg_gettext(True, public.lang("Certificate deleted!"))
        except:
            return public.return_msg_gettext(False, public.lang("Failed to delete!"))

    # 保存证书
    def SaveCert(self, get):
        try:
            certInfo = self.GetCertName(get)
            if not certInfo: return public.return_msg_gettext(False, public.lang("Certificate parsing failed"))
            SSLManger().save_by_file(get.certPath, get.keyPath)
            vpath = '/www/server/panel/vhost/ssl/' + certInfo['subject']
            vpath = vpath.replace("*.", '')
            if not os.path.exists(vpath):
                public.ExecShell("mkdir -p " + vpath)
            public.writeFile(vpath + '/privkey.pem', public.readFile(get.keyPath))
            public.writeFile(vpath + '/fullchain.pem', public.readFile(get.certPath))
            public.writeFile(vpath + '/info.json', json.dumps(certInfo))
            return public.return_msg_gettext(True, public.lang("Successfully saved certificate!"))
        except:
            return public.return_msg_gettext(False, public.lang("Failed to save certificate!"))

    # 读取证书
    def GetCert(self, get):
        vpath = os.path.join('/www/server/panel/vhost/ssl', get.certName.replace("*.", ''))
        if not os.path.exists(vpath):
            return public.return_msg_gettext(False, public.lang("Certificate does NOT exist!"))
            # vpath = os.path.join('/www/server/panel/vhost/ssl_saved', get.ssl_hash)
            # if not os.path.exists(vpath):
            #     return public.return_msg_gettext(False, public.lang("Certificate does NOT exist!"))
        data = {
            'privkey': public.readFile(vpath + '/privkey.pem'),
            'fullchain': public.readFile(vpath + '/fullchain.pem'),
        }
        return data

    # 获取证书名称
    def GetCertName(self, get):
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

    def get_unixtime(self, data, format="%Y-%m-%d %H:%M:%S"):
        import time
        timeArray = time.strptime(data, format)
        timeStamp = int(time.mktime(timeArray))
        return timeStamp

    # 获取指定证书基本信息
    def get_cert_init(self, pem_file):
        if "/www/server/panel/class" not in sys.path:
            sys.path.insert(0, "/www/server/panel/class")
        import ssl_info
        return ssl_info.ssl_info().load_ssl_info(pem_file)
        # if not os.path.exists(pem_file):
        #     return None
        # try:
        #     import OpenSSL
        #     result = {}
        #     x509 = OpenSSL.crypto.load_certificate(
        #         OpenSSL.crypto.FILETYPE_PEM, public.readFile(pem_file))
        #     # 取产品名称
        #     issuer = x509.get_issuer()
        #     result['issuer'] = ''
        #     if hasattr(issuer, 'CN'):
        #         result['issuer'] = issuer.CN
        #     if not result['issuer']:
        #         is_key = [b'0', '0']
        #         issue_comp = issuer.get_components()
        #         if len(issue_comp) == 1:
        #             is_key = [b'CN', 'CN']
        #         for iss in issue_comp:
        #             if iss[0] in is_key:
        #                 result['issuer'] = iss[1].decode()
        #                 break
        #     if not result['issuer']:
        #         if hasattr(issuer, 'O'):
        #             result['issuer'] = issuer.O
        #     # 取到期时间
        #     result['notAfter'] = self.strf_date(
        #         bytes.decode(x509.get_notAfter())[:-1])
        #     # 取申请时间
        #     result['notBefore'] = self.strf_date(
        #         bytes.decode(x509.get_notBefore())[:-1])
        #     # 取可选名称
        #     result['dns'] = []
        #     for i in range(x509.get_extension_count()):
        #         s_name = x509.get_extension(i)
        #         if s_name.get_short_name() in [b'subjectAltName', 'subjectAltName']:
        #             s_dns = str(s_name).split(',')
        #             for d in s_dns:
        #                 result['dns'].append(d.split(':')[1])
        #     subject = x509.get_subject().get_components()
        #     # 取主要认证名称
        #     if len(subject) == 1:
        #         result['subject'] = subject[0][1].decode()
        #     else:
        #         if not result['dns']:
        #             for sub in subject:
        #                 if sub[0] == b'CN':
        #                     result['subject'] = sub[1].decode()
        #                     break
        #             # result['dns'].append(result['subject'])
        #             if 'subject' in result:
        #                 result['dns'].append(result['subject'])

        #         else:
        #             result['subject'] = result['dns'][0]
        #     result['endtime'] = int(
        #         int(time.mktime(time.strptime(result['notAfter'], "%Y-%m-%d")) - time.time()) / 86400)
        #     return result
        # except:
        #     return None

    # 转换时间
    def strf_date(self, sdate):
        return time.strftime('%Y-%m-%d', time.strptime(sdate, '%Y%m%d%H%M%S'))

    # 转换时间
    def strfToTime(self, sdate):
        import time
        return time.strftime('%Y-%m-%d', time.strptime(sdate, '%b %d %H:%M:%S %Y %Z'))

    # 获取产品列表
    def GetSSLProduct(self, get):
        self.__PDATA['data'] = self.De_Code(self.__PDATA['data'])
        result = json.loads(public.httpPost(self.__APIURL + 'user/GetSSLProduct', self.__PDATA))
        result['data'] = self.En_Code(result['data'])
        return result

    # 加密数据
    def De_Code(self, data):
        if sys.version_info[0] == 2:
            import urllib
            pdata = urllib.urlencode(data)
            return binascii.hexlify(pdata)
        else:
            import urllib.parse
            pdata = urllib.parse.urlencode(data)
            if type(pdata) == str: pdata = pdata.encode('utf-8')
            return binascii.hexlify(pdata).decode()

    # 解密数据
    def En_Code(self, data):
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
            return public.return_msg_gettext(False, public.lang("There are currently no certificates to renew!"))

        old_list = json.loads(public.ReadFile("vhost/cert/crontab.json"))
        cron_list = old_list
        if hasattr(get, 'siteName'):
            if not get.siteName in old_list:
                return public.return_msg_gettext(False, public.lang("There is no certificate that can be renewed on the current website.."))
            cron_list = {}
            cron_list[get.siteName] = old_list[get.siteName]

        import panelLets
        lets = panelLets.panelLets()

        result = {}
        result['status'] = True
        result['sucess_list'] = []
        result['err_list'] = []
        for siteName in cron_list:
            data = cron_list[siteName]
            ret = lets.renew_lest_cert(data)
            if ret['status']:
                result['sucess_list'].append(siteName)
            else:
                result['err_list'].append({"siteName": siteName, "msg": ret['msg']})
        return result

    # todo?
    def renew_cert_order(self, args):
        '''
            @name 续签商用证书
            @author cjx
            @version 1.0
        '''
        if not 'pdata' in args:
            return public.returnMsg(False, public.lang("The pdata parameter cannot be empty!"))
        pdata = json.loads(args.pdata)
        self.__PDATA['data'] = pdata

        result = self.request('renew_cert_order')
        if result['status'] == True:
            self.__PDATA['data'] = {}
            args['oid'] = result['oid']
            result['verify_info'] = self.get_verify_info(args)
        return result

    def GetAuthToken(self, get):
        """
        登录官网获取Token
        @get.username 官网手机号
        @get.password 官网账号密码
        """
        rtmp = ""
        data = {}
        data['username'] = public.rsa_decrypt(get.username)
        data['password'] = public.md5(public.rsa_decrypt(get.password))
        data['serverid'] = panelAuth().get_serverid()

        if 'code' in get: data['code'] = get.code
        if 'token' in get: data['token'] = get.token

        pdata = {}
        pdata['data'] = self.De_Code(data)
        try:
            rtmp = public.httpPost(self.__BINDURL, pdata)
            result = json.loads(rtmp)
            result['data'] = self.En_Code(result['data'])
            if not result['status']: return result

            if result['data']:
                if result['data']['serverid'] != data['serverid']:  # 保存新的serverid
                    public.writeFile('data/sid.pl', result['data']['serverid'])
                public.writeFile(self.__UPATH, json.dumps(result['data']))
                if os.path.exists('data/bind_path.pl'): os.remove('data/bind_path.pl')
                public.flush_plugin_list()
            del (result['data'])
            session['focre_cloud'] = True
            return result
        except Exception as ex:
            error = str(ex)
            if error.lower().find('json') >= 0:
                error = '<br>错误：连接宝塔官网异常，请按照以下方法排除问题后重试：<br>解决方法：<a target="_blank" class="btlink" href="https://www.bt.cn/bbs/thread-87257-1-1.html">https://www.bt.cn/bbs/thread-87257-1-1.html</a><br>'
                # raise public.PanelError(error)
                return public.returnMsg(False, 6)
            else:
                return public.returnMsg(False, 6)
                # raise public.error_conn_cloud(error)
            # return public.returnMsg(False, public.lang("连接服务器失败!<br>{}", rtmp))

    def GetBindCode(self, get):
        """
        获取验证码
        """
        rtmp = ""
        data = {}
        data['username'] = get.username
        data['token'] = get.token
        pdata = {}
        pdata['data'] = self.De_Code(data)
        try:
            rtmp = public.httpPost(self.__CODEURL, pdata)
            result = json.loads(rtmp)
            return result
        except Exception as ex:
            raise public.error_conn_cloud(str(ex))
            # return public.returnMsg(False,'连接服务器失败!<br>' + rtmp)

    # 解析DNSAPI信息
    def get_dnsapi(self, auth_to):
        tmp = auth_to.split('|')
        dns_name = tmp[0]
        key = "None"
        secret = "None"
        if len(tmp) < 3:
            dnsapi_config = json.loads(public.readFile('{}/config/dns_api.json'.format(public.get_panel_path())))
            for dc in dnsapi_config:
                if dc['name'] != dns_name:
                    continue
                if not dc['data']:
                    continue
                key = dc['data'][0]['value']
                secret = dc['data'][1]['value']
        else:
            key = tmp[1]
            secret = tmp[2]
        return dns_name, key, secret

    # 获取dnsapi对象
    def get_dns_class(self, auth_to):
        try:
            import panelDnsapi
            dns_name, key, secret = self.get_dnsapi(auth_to)
            dns_class = getattr(panelDnsapi, dns_name)(key, secret)
            dns_class._type = 1
            return dns_class
        except:
            return None

    # 解析域名
    def create_dns_record(self, auth_to, domain, dns_value, original_domain=None):
        # 如果为手动解析
        if auth_to == 'dns':
            return None
        from panelDnsapi import DnsMager
        dns_class = DnsMager().get_dns_obj_by_domain(original_domain)
        dns_class._type = 1
        if not dns_class:
            return public.returnMsg(False, public.lang("The operation failed. Please check that the key is correct"))

        # 申请前删除caa记录
        root, zone = public.get_root_domain(domain)
        try:
            dns_class.remove_record(public.de_punycode(root), '@', 'CAA')
        except:
            pass
        try:
            dns_class.create_dns_record(public.de_punycode(domain), dns_value)
            return public.returnMsg(True, public.lang("Added successfully"))
        except:
            return public.returnMsg(False, public.get_error_info())

    # 检测ssl验证方式
    def check_ssl_method(self, get):
        """
        @name 检测ssl验证方式
        @domain string 域名
        """

        domain = get.domain
        if public.M('sites').where('id=?', (public.M('domain').where('name=?', (domain)).getField('pid'),)).getField(
                'project_type') == 'Java':
            siteRunPath = '{}/java_node_ssl'.format(public.M("config").getField("sites_path"))
        else:
            siteRunPath = self.get_domain_run_path(domain)

        if not siteRunPath:
            return public.returnMsg(False, public.lang("Failed to get the website path. Please check if the website exists"))

        verify_path = siteRunPath + '/.well-known/pki-validation'
        if not os.path.exists(verify_path):  os.makedirs(verify_path)

        # 生成临时文件
        check_val = public.GetRandomString(16)
        verify_file = '{}/{}.txt'.format(verify_path, check_val)
        public.writeFile(verify_file, check_val)
        if not os.path.exists(verify_file):
            return public.returnMsg(False, public.lang("Failed to create the validation file. Check if the write was blocked"))

        res = {}
        msg = [' domain name [{}] validation file cannot be accessed correctly'.format(domain),
               'Probable cause',
               '1、the resolution was not correct, or the resolution did not work [Please resolve the domain correctly, or wait for the resolution to work and try again]',
               '2、check whether 301/302 redirects are set [please temporarily turn off redirects related configuration]',
               '3、check whether the site has enabled reverse proxy [please temporarily turn off reverse proxy configuration]'
               ]

        res['HTTP_CSR_HASH'] = msg
        res['HTTPS_CSR_HASH'] = msg

        # 检测HTTP/https访问
        args = public.dict_obj()
        for stype in ['http', 'https']:
            args.url = '{}://{}/.well-known/pki-validation/{}.txt'.format(stype, domain, check_val)
            args.content = check_val
            if self.check_url_txt(args, 2) == 1:
                res['{}_CSR_HASH'.format(stype).upper()] = 1

        # 检测caa记录
        result = self.check_ssl_caa([domain])
        if not result:
            res['CNAME_CSR_HASH'] = 1
        else:
            res['CNAME_CSR_HASH'] = json.loads(result['data'])

        if os.path.exists(verify_file):
            os.remove(verify_file)
        return res

    @staticmethod
    def upload_cert_to_cloud(get):
        ssl_id = None
        ssl_hash = None
        try:
            if "ssl_id" in get:
                ssl_id = int(get.ssl_id)
            if "ssl_hash" in get:
                ssl_hash = get.ssl_hash.strip()
        except (ValueError, AttributeError, KeyError):
            return public.ReturnMsg(False, "parameter error")
        from ssl_manage import SSLManger
        try:
            return SSLManger().upload_cert(ssl_id, ssl_hash)
        except ValueError as e:
            return public.returnMsg(False, str(e))
        except Exception as e:
            return public.returnMsg(False, "operation mistake：" + str(e))

    @staticmethod
    def remove_cloud_cert(get):
        ssl_id = None
        ssl_hash = None
        local = False
        try:
            if "ssl_id" in get:
                ssl_id = int(get.ssl_id)
            if "ssl_hash" in get:
                ssl_hash = get.ssl_hash.strip()

            if "local" in get and get.local.strip() in ("1", 1, True, "true"):
                local = True

        except (ValueError, AttributeError, KeyError):
            return public.ReturnMsg(False, "parameter error")
        from ssl_manage import SSLManger
        try:
            return SSLManger().remove_cert(ssl_id, ssl_hash, local=local)
        except ValueError as e:
            return public.returnMsg(False, str(e))
        except Exception as e:
            return public.returnMsg(False, "operation mistake：" + str(e))

    # 未使用
    @staticmethod
    def refresh_cert_list(get=None):
        from ssl_manage import SSLManger
        try:
            return SSLManger().get_cert_list(force_refresh=True)
        except ValueError as e:
            return public.returnMsg(False, str(e))
        except Exception as e:
            return public.returnMsg(False, "operation mistake：" + str(e))

    @staticmethod
    def get_cert_info(get):
        ssl_id = None
        ssl_hash = None
        try:
            if "ssl_id" in get:
                ssl_id = int(get.ssl_id)
            if "ssl_hash" in get:
                ssl_hash = get.ssl_hash.strip()
        except (ValueError, AttributeError, KeyError):
            return public.ReturnMsg(False, "parameter error")
        from ssl_manage import SSLManger
        try:
            ssl_mager = SSLManger()
            target = ssl_mager.find_ssl_info(ssl_id, ssl_hash)
            if target is None:
                return public.returnMsg(False, public.lang("No certificate information was obtained"))
            target.update(ssl_mager.get_cert_for_deploy(target["hash"]))
            return target
        except ValueError as e:
            return public.returnMsg(False, str(e))
        except Exception as e:
            return public.returnMsg(False, "operation mistake：" + str(e))

    @staticmethod
    def get_cert_list(get):
        """
        search_limit 0 -> 所有证书
        search_limit 1 -> 没有过期的证书
        search_limit 2 -> 有效期小于等于15天的证书 但未过期
        search_limit 3 -> 过期的证书
        search_limit 4 -> 过期时间1年以上的证书
        """
        search_name = None
        search_limit = 0
        force_refresh = False

        try:
            if "search_name" in get:
                search_name = get.search_name.strip()
            if "search_limit" in get:
                search_limit = int(get.search_limit.strip())
            if "force_refresh" in get and get.force_refresh.strip() in ("1", 1, "True", True):
                force_refresh = True

        except (ValueError, AttributeError, KeyError):
            return public.ReturnMsg(False, "parameter error")

        param = None
        if search_name is not None:
            param = ['subject LIKE ?', ["%{}%".format(search_name)]]

        now = datetime.datetime.now()
        filter_func = lambda x: True
        if search_limit == 1:
            date = now.strftime("%Y-%m-%d")
            filter_func = lambda x: x["not_after"] >= date
        elif search_limit == 2:
            date1 = now.strftime("%Y-%m-%d")
            date2 = (now + datetime.timedelta(days=15)).strftime("%Y-%m-%d")
            filter_func = lambda x: date1 <= x["not_after"] <= date2
        elif search_limit == 3:
            date = now.strftime("%Y-%m-%d")
            filter_func = lambda x: x["not_after"] < date
        elif search_limit == 4:
            date = (now + datetime.timedelta(days=366)).strftime("%Y-%m-%d")
            filter_func = lambda x: x["not_after"] > date

        from ssl_manage import SSLManger
        try:
            res_list = SSLManger().get_cert_list(param=param, force_refresh=force_refresh)
            return list(filter(filter_func, res_list))
        except ValueError as e:
            return public.returnMsg(False, str(e))
        except Exception as e:
            return public.returnMsg(False, "operation mistake：" + str(e))


    def _hash(self, cert_filename: str = None, certificate: str = None, ignore_errors: bool = False):
        if cert_filename is not None and os.path.isfile(cert_filename):
            certificate = public.readFile(cert_filename)

        if not isinstance(certificate, str) or not certificate.startswith("-----BEGIN"):
            if ignore_errors:
                return None
            raise ValueError("证书格式错误")

        md5_obj = md5()
        md5_obj.update(certificate.encode("utf-8"))
        return md5_obj.hexdigest()


    def get_exclude_hash(self, get):
        path = '{}/data/exclude_hash.json'.format(public.get_panel_path())
        if os.path.exists(path):
            try:
                data = json.loads(public.readFile(path))
                if data['version'] == "2":
                    return data
            except:
                pass

        data = {"version": "2", "exclude_hash": {}}
        try:
            _cert_data = self.get_order_list(get)
            for i in _cert_data:
                if i['orderStatus'] != 'COMPLETE':
                    continue
                try:
                    get.oid = i['oid']
                    self.__init__()
                    certInfo = self.get_order_find(get)
                    data['exclude_hash'].update(
                        {i['oid']: self._hash(certificate=certInfo['certificate'] + "\n" + certInfo['caCertificate'])}
                    )
                except Exception as e:
                    continue
            self.__init__()
            test_cert_data = self.GetOrderList(get)
            for j in test_cert_data['data']:
                if j['stateCode'] != 'COMPLETED':
                    continue
                try:
                    get.partnerOrderId = j['partnerOrderId']
                    self.__init__()
                    certInfo = self.GetSSLInfoTo(get)
                    data['exclude_hash'].update(
                        {j['partnerOrderId']: self._hash(certificate=certInfo['cert'] + certInfo['certCa'])}
                    )
                except Exception as e:
                    continue
        except:
            return data
        public.writeFile(path, json.dumps(data))
        return data


    def set_exclude_hash(self, get):
        try:
            path = '{}/data/exclude_hash.json'.format(public.get_panel_path())
            try:
                data = json.loads(public.readFile(path))
            except:
                data = self.get_exclude_hash(get)
            if 'oid' in get:
                order = get.oid
            elif 'partnerOrderId' in get:
                order = get.partnerOrderId
            data['exclude_hash'].update({order: self._hash(certificate=get.csr)})
            public.writeFile(path, json.dumps(data))
        except:
            pass
