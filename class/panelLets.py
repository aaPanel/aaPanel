#coding: utf-8
# +-------------------------------------------------------------------
# | 宝塔Linux面板
# +-------------------------------------------------------------------
# | Copyright (c) 2015-2099 宝塔软件(http://bt.cn) All rights reserved.
# +-------------------------------------------------------------------
# | Author: 沐落 <cjx@bt.cn>
# +-------------------------------------------------------------------
import os,sys,json,time,re
setup_path = '/www/server/panel'
os.chdir(setup_path)
if not 'class/' in sys.path:
    sys.path.insert(0,'class/')
import http_requests as requests
import sewer,public
from OpenSSL import crypto
try:
    requests.packages.urllib3.disable_warnings()
except:pass
if __name__ != '__main__':
    import BTPanel
try:
    import dns.resolver
except:
    public.ExecShell("pip install dnspython")
    try:
        import dns.resolver
    except:
        pass

class panelLets:
    let_url = "https://acme-v02.api.letsencrypt.org/directory"
    #let_url = "https://acme-staging-v02.api.letsencrypt.org/directory"

    setupPath = None #安装路径  
    server_type = None
    log_file = '/www/server/panel/logs/letsencrypt.log'

    #构造方法
    def __init__(self):
        self.setupPath = public.GetConfigValue('setup_path')
        self.server_type = public.get_webserver()

    def write_log(self,log_str):

        f = open(self.log_file,'ab+')
        log_str += "\n"
        f.write(log_str.encode('utf-8'))
        f.close()
        return True

    #拆分根证书
    def split_ca_data(self,cert):
        datas = cert.split('-----END CERTIFICATE-----')
        return {"cert":datas[0] + "-----END CERTIFICATE-----\n","ca_data":datas[1] + '-----END CERTIFICATE-----\n' }

    #证书转为pkcs12
    def dump_pkcs12(self,key_pem=None,cert_pem = None, ca_pem=None, friendly_name=None):
        p12 = crypto.PKCS12()
        if cert_pem:
            ret = p12.set_certificate(crypto.load_certificate(crypto.FILETYPE_PEM, cert_pem.encode()))
            assert ret is None
        if key_pem:
            ret = p12.set_privatekey(crypto.load_privatekey(crypto.FILETYPE_PEM, key_pem.encode()))
            assert ret is None
        if ca_pem:
            ret = p12.set_ca_certificates((crypto.load_certificate(crypto.FILETYPE_PEM, ca_pem.encode()),) )
        if friendly_name:
            ret = p12.set_friendlyname(friendly_name.encode())
        return p12

    def extract_zone(self,domain_name):
        domain_name = domain_name.lstrip("*.")
        top_domain_list = ['.ac.cn', '.ah.cn', '.bj.cn', '.com.cn', '.cq.cn', '.fj.cn', '.gd.cn','.gov.cn', '.gs.cn',
                           '.gx.cn', '.gz.cn', '.ha.cn', '.hb.cn', '.he.cn','.hi.cn', '.hk.cn', '.hl.cn', '.hn.cn',
                           '.jl.cn', '.js.cn', '.jx.cn','.ln.cn', '.mo.cn', '.net.cn', '.nm.cn', '.nx.cn', '.org.cn',
                           '.my.id','.com.ac','.com.ad','.com.ae','.com.af','.com.ag','.com.ai','.com.al','.com.am',
                           '.com.an','.com.ao','.com.aq','.com.ar','.com.as','.com.as','.com.at','.com.au','.com.aw',
                           '.com.az','.com.ba','.com.bb','.com.bd','.com.be','.com.bf','.com.bg','.com.bh','.com.bi',
                           '.com.bj','.com.bm','.com.bn','.com.bo','.com.br','.com.bs','.com.bt','.com.bv','.com.bw',
                           '.com.by','.com.bz','.com.ca','.com.ca','.com.cc','.com.cd','.com.cf','.com.cg','.com.ch',
                           '.com.ci','.com.ck','.com.cl','.com.cm','.com.cn','.com.co','.com.cq','.com.cr','.com.cu',
                           '.com.cv','.com.cx','.com.cy','.com.cz','.com.de','.com.dj','.com.dk','.com.dm','.com.do',
                           '.com.dz','.com.ec','.com.ee','.com.eg','.com.eh','.com.es','.com.et','.com.eu','.com.ev',
                           '.com.fi','.com.fj','.com.fk','.com.fm','.com.fo','.com.fr','.com.ga','.com.gb','.com.gd',
                           '.com.ge','.com.gf','.com.gh','.com.gi','.com.gl','.com.gm','.com.gn','.com.gp','.com.gr',
                           '.com.gt','.com.gu','.com.gw','.com.gy','.com.hm','.com.hn','.com.hr','.com.ht','.com.hu',
                           '.com.id','.com.id','.com.ie','.com.il','.com.il','.com.in','.com.io','.com.iq','.com.ir',
                           '.com.is','.com.it','.com.jm','.com.jo','.com.jp','.com.ke','.com.kg','.com.kh','.com.ki',
                           '.com.km','.com.kn','.com.kp','.com.kr','.com.kw','.com.ky','.com.kz','.com.la','.com.lb',
                           '.com.lc','.com.li','.com.lk','.com.lr','.com.ls','.com.lt','.com.lu','.com.lv','.com.ly',
                           '.com.ma','.com.mc','.com.md','.com.me','.com.mg','.com.mh','.com.ml','.com.mm','.com.mn',
                           '.com.mo','.com.mp','.com.mq','.com.mr','.com.ms','.com.mt','.com.mv','.com.mw','.com.mx',
                           '.com.my','.com.mz','.com.na','.com.nc','.com.ne','.com.nf','.com.ng','.com.ni','.com.nl',
                           '.com.no','.com.np','.com.nr','.com.nr','.com.nt','.com.nu','.com.nz','.com.om','.com.pa',
                           '.com.pe','.com.pf','.com.pg','.com.ph','.com.pk','.com.pl','.com.pm','.com.pn','.com.pr',
                           '.com.pt','.com.pw','.com.py','.com.qa','.com.re','.com.ro','.com.rs','.com.ru','.com.rw',
                           '.com.sa','.com.sb','.com.sc','.com.sd','.com.se','.com.sg','.com.sh','.com.si','.com.sj',
                           '.com.sk','.com.sl','.com.sm','.com.sn','.com.so','.com.sr','.com.st','.com.su','.com.sy',
                           '.com.sz','.com.tc','.com.td','.com.tf','.com.tg','.com.th','.com.tj','.com.tk','.com.tl',
                           '.com.tm','.com.tn','.com.to','.com.tp','.com.tr','.com.tt','.com.tv','.com.tw','.com.tz',
                           '.com.ua','.com.ug','.com.uk','.com.uk','.com.us','.com.uy','.com.uz','.com.va','.com.vc',
                           '.com.ve','.com.vg','.com.vn','.com.vu','.com.wf','.com.ws','.com.ye','.com.za','.com.zm',
                           '.com.zw']
        old_domain_name = domain_name
        m_count = domain_name.count(".")
        top_domain = "."+".".join(domain_name.rsplit('.')[-2:])
        new_top_domain = "." + top_domain.replace(".","")
        is_tow_top = False
        if top_domain in top_domain_list:
            is_tow_top = True
            domain_name = domain_name[:-len(top_domain)] + new_top_domain

        if domain_name.count(".") > 1:
            zone, middle, last = domain_name.rsplit(".", 2)
            acme_txt = "_acme-challenge.%s" % zone
            if is_tow_top: last = top_domain[1:]
            root = ".".join([middle, last])
        else:
            zone = ""
            root = old_domain_name
            acme_txt = "_acme-challenge"
        return root, zone, acme_txt

    #获取根域名
    def get_root_domain(self,domain_name):
        d_root,tow_name,acme_txt = self.extract_zone(domain_name)
        return d_root

    #获取acmename
    def get_acme_name(self,domain_name):
        d_root,tow_name,acme_txt = self.extract_zone(domain_name)
        return acme_txt + '.' + d_root

    #格式化错误输出
    def get_error(self,error):
        if error.find("Max checks allowed") >= 0 :
            return "CA can't verify your domain name, please check if the domain name resolution is correct, or wait 5-10 minutes and try again."
        elif error.find("Max retries exceeded with") >= 0 or error.find('status_code=0 ') != -1:
            return "The CA server connection timed out, please try again later."
        elif error.find("The domain name belongs") >= 0:
            return "The domain name does not belong to this DNS service provider. Please ensure that the domain name is filled in correctly."
        elif error.find('login token ID is invalid') >=0:
            return 'The DNS server connection failed. Please check if the key is correct.'
        elif "too many certificates already issued for exact set of domains" in error:
            return 'The signing failed, the domain name %s exceeded the weekly number of repeated issuances!' % re.findall("exact set of domains: (.+):", error)
        elif "Error creating new account :: too many registrations for this IP" in error:
            return 'The signing failed, the current server IP has reached the limit of creating up to 10 accounts every 3 hours..'
        elif "DNS problem: NXDOMAIN looking up A for" in error:
            return 'The verification failed, the domain name was not resolved, or the resolution did not take effect.!'
        elif "Invalid response from" in error:
            return 'Authentication failed, domain name resolution error or verification URL could not be accessed!'
        elif error.find('TLS Web Server Authentication') != -1:
            public.restart_panel()
            return "Failed to connect to CA server, please try again later."
        elif error.find('Name does not end in a public suffix') != -1:
            return "Unsupported domain name %s, please check if the domain name is correct!" % re.findall("Cannot issue for \"(.+)\":", error)
        elif error.find('No valid IP addresses found for') != -1:
            return "The domain name %s did not find a resolution record. Please check if the domain name is resolved.!" % re.findall("No valid IP addresses found for (.+)", error)
        elif error.find('No TXT record found at') != -1:
            return "If a valid TXT resolution record is not found in the domain name %s, please check if the TXT record is correctly parsed. If it is applied by DNSAPI, please try again in 10 minutes.!" % re.findall(
                "No TXT record found at (.+)", error)
        elif error.find('Incorrect TXT record') != -1:
            return "Found the wrong TXT record on %s: %s, please check if the TXT resolution is correct. If it is applied by DNSAPI, please try again in 10 minutes.!" % (
            re.findall("found at (.+)", error), re.findall("Incorrect TXT record \"(.+)\"", error))
        elif error.find('Domain not under you or your user') != -1:
            return "This domain name does not exist under this dnspod account. Adding parsing failed.!"
        elif error.find('SERVFAIL looking up TXT for') != -1:
            return "If a valid TXT resolution record is not found in the domain name %s, please check if the TXT record is correctly parsed. If it is applied by DNSAPI, please try again in 10 minutes.!" % re.findall(
                "looking up TXT for (.+)", error)
        elif error.find('Timeout during connect') != -1:
            return "Connection timed out, CA server could not access your website!"
        elif error.find("DNS problem: SERVFAIL looking up CAA for") != -1:
            return "The domain name %s is currently required to verify the CAA record. Please manually resolve the CAA record, or try again after 1 hour.!" % re.findall("looking up CAA for (.+)", error)
        elif error.find("Read timed out.") != -1:
            return "Verification timeout, please check whether the domain name is correctly resolved. If dns is resolved, the connection between the server and Let'sEncrypt may be abnormal. Please try again later!"
        elif error.find("Error creating new order") != -1:
            return "Order creation failed, please try again later!"
        elif error.find("Too Many Requests") != -1:
            return "More than 5 verification failures in 1 hour, application is temporarily banned, please try again later!"
        elif error.find('HTTP Error 400: Bad Request') != -1:
            return "CA server denied access, please try again later!"
        else:
            return error;

    #获取DNS服务器
    def get_dns_class(self,data):
        if data['dnsapi'] == 'dns_ali':
            import panelDnsapi
            public.mod_reload(panelDnsapi)
            dns_class = panelDnsapi.AliyunDns(key = data['dns_param'][0], secret = data['dns_param'][1])
            return dns_class
        elif data['dnsapi'] == 'dns_dp':
            dns_class = sewer.DNSPodDns(DNSPOD_ID = data['dns_param'][0] ,DNSPOD_API_KEY = data['dns_param'][1])
            return dns_class
        elif data['dnsapi'] == 'dns_cx':   
            import panelDnsapi
            public.mod_reload(panelDnsapi)
            dns_class = panelDnsapi.CloudxnsDns(key = data['dns_param'][0] ,secret =data['dns_param'][1])
            result = dns_class.get_domain_list()
            if result['code'] == 1:                
                return dns_class
        elif data['dnsapi'] == 'dns_bt':
            import panelDnsapi
            public.mod_reload(panelDnsapi)
            dns_class = panelDnsapi.Dns_com()
            return dns_class
        return False

    #续签证书
    def renew_lest_cert(self,data):  
        #续签网站
        path = self.setupPath + '/panel/vhost/cert/'+ data['siteName']
        if not os.path.exists(path):  return public.returnMsg(False, 'RENEW_FAILED')

        account_path = path + "/account_key.key"
        if not os.path.exists(account_path): return public.returnMsg(False, 'RENEW_FAILED1')

        #续签
        data['account_key'] = public.readFile(account_path)

        if not 'first_domain' in data:  data['first_domain'] = data['domains'][0]

        if 'dnsapi' in data:                
            certificate = self.crate_let_by_dns(data)
        else:            
            certificate = self.crate_let_by_file(data)       

        if not certificate['status']: return public.returnMsg(False, certificate['msg'])
                 
        #存储证书
        public.writeFile(path + "/privkey.pem",certificate['key'])
        public.writeFile(path + "/fullchain.pem",certificate['cert'] + certificate['ca_data'])
        public.writeFile(path + "/account_key.key", certificate['account_key']) #续签KEY

        #转为IIS证书
        p12 = self.dump_pkcs12(certificate['key'], certificate['cert'] + certificate['ca_data'],certificate['ca_data'],data['first_domain'])
        pfx_buffer = p12.export()
        public.writeFile(path + "/fullchain.pfx",pfx_buffer,'wb+')
         
        return public.returnMsg(True, 'RENEW_SUCCESS1',(data['siteName'],))



    #申请证书
    def apple_lest_cert(self,get):
        data = {}        
        data['siteName'] = get.siteName
        data['domains'] = json.loads(get.domains)
        data['email'] = get.email
        data['dnssleep'] = get.dnssleep
        self.write_log(public.getMsg("APPLY_SSL",(data['domains'],)))
        self.write_log("="*50)
        if len(data['domains']) <=0 : return public.returnMsg(False, 'APPLY_SSL_DOMAIN_ERR')
        
        data['first_domain'] = data['domains'][0]       
     
        path = self.setupPath + '/panel/vhost/cert/'+ data['siteName']
        if not os.path.exists(path): os.makedirs(path)

        # 检查是否自定义证书
        partnerOrderId = path + '/partnerOrderId'
        if os.path.exists(partnerOrderId): os.remove(partnerOrderId)
        #清理续签key
        re_key = path + '/account_key.key'
        if os.path.exists(re_key): os.remove(re_key)

        re_password = path + '/password'
        if os.path.exists(re_password): os.remove(re_password)
        
        data['account_key'] = None   
        if hasattr(get, 'dnsapi'): 
            if not 'app_root' in get: get.app_root = '0'
            data['app_root'] = get.app_root   
            domain_list = data['domains']
            if data['app_root'] == '1':
                public.writeFile(self.log_file,'');
                domain_list = []
                data['first_domain'] = self.get_root_domain(data['first_domain'])
                for domain in data['domains']:
                    rootDoamin = self.get_root_domain(domain)
                    if not rootDoamin in domain_list: domain_list.append(rootDoamin)
                    if not "*." + rootDoamin in domain_list: domain_list.append("*." + rootDoamin)
                data['domains'] = domain_list
            if get.dnsapi == 'dns':
                domain_path = path + '/domain_txt_dns_value.json'
                if hasattr(get, 'renew'): #验证
                    data['renew'] = True
                    dns = json.loads(public.readFile(domain_path))
                    data['dns'] = dns
                    certificate = self.crate_let_by_oper(data)
                else:
                    public.writeFile(self.log_file,'');
                    #手动解析提前返回
                    result = self.crate_let_by_oper(data)
                    if 'status' in result and not result['status']:  return result
                    result['status'] = True
                    public.writeFile(domain_path, json.dumps(result))
                    result['msg'] = public.getMsg('MANUALLY_RESOLVE_DOMAIN')
                    result['code'] = 2
                    return result
            elif get.dnsapi == 'dns_bt':
                public.writeFile(self.log_file,'')
                data['dnsapi'] = get.dnsapi
                certificate = self.crate_let_by_dns(data)
            else:
                public.writeFile(self.log_file,'')
                data['dnsapi'] = get.dnsapi
                data['dns_param'] = get.dns_param.split('|')
                certificate = self.crate_let_by_dns(data)
        else:
            #文件验证
            public.writeFile(self.log_file,'')
            data['site_dir'] = get.site_dir
            certificate = self.crate_let_by_file(data)       

        if not certificate['status']: return public.returnMsg(False, certificate['msg'])
        
        #保存续签
        self.write_log(public.getMsg("SAVEING_SSL"))
        cpath = self.setupPath + '/panel/vhost/cert/crontab.json'
        config = {}
        if os.path.exists(cpath):
            try:
                config = json.loads(public.readFile(cpath))
            except:pass

        config[data['siteName']] = data
        public.writeFile(cpath,json.dumps(config))
        public.set_mode(cpath,600)

        #存储证书
        public.writeFile(path + "/privkey.pem",certificate['key'])
        public.writeFile(path + "/fullchain.pem",certificate['cert'] + certificate['ca_data'])
        public.writeFile(path + "/account_key.key",certificate['account_key']) #续签KEY

        #转为IIS证书
        p12 = self.dump_pkcs12(certificate['key'], certificate['cert'] + certificate['ca_data'],certificate['ca_data'],data['first_domain'])
        pfx_buffer = p12.export()
        public.writeFile(path + "/fullchain.pfx",pfx_buffer,'wb+')        
        public.writeFile(path + "/README","let") 
        
        #计划任务续签
        self.write_log(public.getMsg("SET_AUTORENEW"))
        self.set_crond()
        self.write_log(public.getMsg("DEPLOY_SSL_TO_SITE"))
        self.write_log("="*50)
        return public.returnMsg(True, 'APPLY_SSL_SUCCESS')

    #创建计划任务
    def set_crond(self):
        try:
            echo = public.md5(public.md5('renew_lets_ssl_bt'))
            cron_id = public.M('crontab').where('echo=?',(echo,)).getField('id')

            import crontab
            args_obj = public.dict_obj()
            if not cron_id:
                cronPath = public.GetConfigValue('setup_path') + '/cron/' + echo
                shell = public.get_python_bin() + ' %s/panel/class/panelLets.py renew_lets_ssl ' % (self.setupPath)
                public.writeFile(cronPath,shell)
                args_obj.id = public.M('crontab').add('name,type,where1,where_hour,where_minute,echo,addtime,status,save,backupTo,sType,sName,sBody,urladdress',("Renew the Letter's Encrypt certificate",'day','','0','10',echo,time.strftime('%Y-%m-%d %X',time.localtime()),0,'','localhost','toShell','',shell,''))
                crontab.crontab().set_cron_status(args_obj)
            else:
                cron_path = public.get_cron_path()
                if os.path.exists(cron_path):
                    cron_s = public.readFile(cron_path)
                    if cron_s.find(echo) == -1:
                        public.M('crontab').where('echo=?',(echo,)).setField('status',0)
                        args_obj.id = cron_id
                        crontab.crontab().set_cron_status(args_obj)
        except:pass

    #手动解析
    def crate_let_by_oper(self,data):
        result = {}
        result['status'] = False
        try:
            if not data['email']: data['email'] = public.M('users').getField('email')

            #手动解析记录值
            if not 'renew' in data:
                self.write_log(public.getMsg("INIT_ACME"))
                BTPanel.dns_client = sewer.Client(domain_name = data['first_domain'],dns_class = None,account_key = data['account_key'],domain_alt_names = data['domains'],contact_email = str(data['email']) ,ACME_AUTH_STATUS_WAIT_PERIOD = 15,ACME_AUTH_STATUS_MAX_CHECKS = 5,ACME_REQUEST_TIMEOUT = 20,ACME_DIRECTORY_URL = self.let_url)
                domain_dns_value = "placeholder"
                dns_names_to_delete = []
                self.write_log(public.getMsg("REGISTER_ACCOUNT"))
                BTPanel.dns_client.acme_register()
                authorizations, finalize_url = BTPanel.dns_client.apply_for_cert_issuance()
                responders = []
                self.write_log(public.getMsg("GET_VERIFICATION_INFO"))
                for url in authorizations:
                    identifier_auth = BTPanel.dns_client.get_identifier_authorization(url)
                    authorization_url = identifier_auth["url"]
                    dns_name = identifier_auth["domain"]
                    dns_token = identifier_auth["dns_token"]
                    dns_challenge_url = identifier_auth["dns_challenge_url"]

                    acme_keyauthorization, domain_dns_value = BTPanel.dns_client.get_keyauthorization(dns_token)
                 
                    acme_name = self.get_acme_name(dns_name)
                    dns_names_to_delete.append({"dns_name": public.de_punycode(dns_name),"acme_name":acme_name, "domain_dns_value": domain_dns_value})
                    responders.append(
                        {
                            "dns_name":dns_name,
                            "authorization_url": authorization_url,
                            "acme_keyauthorization": acme_keyauthorization,
                            "dns_challenge_url": dns_challenge_url,
                        }
                    )
            
                dns = {}
                dns['dns_names'] = dns_names_to_delete
                dns['responders'] = responders
                dns['finalize_url'] = finalize_url
                self.write_log(public.getMsg("RETURN_VERIFICATION_INFO"))
                return dns
            else:
                self.write_log(public.getMsg("SUBMIT_V_REQUEST"))
                responders = data['dns']['responders']
                dns_names_to_delete = data['dns']['dns_names']
                finalize_url = data['dns']['finalize_url']
                for i in responders:  
                    self.write_log(public.getMsg("CA_V_DOMAIN",(i['dns_name'],)))
                    auth_status_response = BTPanel.dns_client.check_authorization_status(i["authorization_url"])
                    if auth_status_response.json()["status"] == "pending":
                        BTPanel.dns_client.respond_to_challenge(i["acme_keyauthorization"], i["dns_challenge_url"])

                for i in responders:
                    self.write_log(public.getMsg("GET_CA_V_RES",(i['dns_name'],)))
                    BTPanel.dns_client.check_authorization_status(i["authorization_url"], ["valid","invalid"])
                self.write_log(public.getMsg("ALL_DOMAIN_V_PASS"))
                certificate_url = BTPanel.dns_client.send_csr(finalize_url)
                self.write_log(public.getMsg("GET_CERT_CONTENT"))
                certificate = BTPanel.dns_client.download_certificate(certificate_url)

                if certificate:
                    certificate = self.split_ca_data(certificate)
                    result['cert'] = certificate['cert']
                    result['ca_data'] = certificate['ca_data']
                    result['key'] = BTPanel.dns_client.certificate_key
                    result['account_key'] = BTPanel.dns_client.account_key
                    result['status'] = True
                    BTPanel.dns_client = None
                else:
                    result['msg'] = public.getMsg('CERT_APPLY_ERR')

        except Exception as e:
            self.write_log(public.getMsg("CERT_APPLY_ERR1",(e,)))
            self.write_log("=" * 50)
            res = str(e).split('>>>>')
            err = False
            try:
                err = json.loads(res[1])
            except: err = False
            result['msg'] =  [self.get_error(res[0]),err]

        return result

    #dns验证
    def crate_let_by_dns(self,data):
        dns_class = self.get_dns_class(data)
        if not dns_class:
            self.write_log(public.getMsg("DNS_APPLY_ERR"))
            self.write_log(public.getMsg("EXIT_APPLY_PROCESS"))
            self.write_log("="*50)
            return public.returnMsg(False, 'DNS_APPLY_ERR1')
     
        result = {}
        result['status'] = False
        try:
            log_level = "INFO"
            if data['account_key']: log_level = 'ERROR'
            if not data['email']: data['email'] = public.M('users').getField('email')
            self.write_log(public.getMsg("INIT_ACME"))
            client = sewer.Client(domain_name = data['first_domain'],domain_alt_names = data['domains'],account_key = data['account_key'],contact_email = str(data['email']),LOG_LEVEL = log_level,ACME_AUTH_STATUS_WAIT_PERIOD = 15,ACME_AUTH_STATUS_MAX_CHECKS = 5,ACME_REQUEST_TIMEOUT = 20, dns_class = dns_class,ACME_DIRECTORY_URL = self.let_url)
            domain_dns_value = "placeholder"
            dns_names_to_delete = []
            try:
                self.write_log(public.getMsg("REGISTER_ACCOUNT"))
                client.acme_register()
                authorizations, finalize_url = client.apply_for_cert_issuance()
                responders = []
                self.write_log(public.getMsg("GET_VERIFICATION_INFO"))
                for url in authorizations:
                    identifier_auth = client.get_identifier_authorization(url)
                    authorization_url = identifier_auth["url"]
                    dns_name = identifier_auth["domain"]
                    dns_token = identifier_auth["dns_token"]
                    dns_challenge_url = identifier_auth["dns_challenge_url"]
                    acme_keyauthorization, domain_dns_value = client.get_keyauthorization(dns_token)
                    self.write_log(public.getMsg("ADD_TXT_RECORD",(dns_name,domain_dns_value)))
                    dns_class.create_dns_record(public.de_punycode(dns_name), domain_dns_value)
                    dns_names_to_delete.append({"dns_name": public.de_punycode(dns_name), "domain_dns_value": domain_dns_value})
                    responders.append({"dns_name":dns_name,"domain_dns_value":domain_dns_value,"authorization_url": authorization_url, "acme_keyauthorization": acme_keyauthorization,"dns_challenge_url": dns_challenge_url} )



                try:
                    for i in responders:
                        self.write_log(public.getMsg("CHECK_TXT_RECORD",(i['dns_name'],i['domain_dns_value'])))
                        self.check_dns(self.get_acme_name(i['dns_name']),i['domain_dns_value'])
                        self.write_log(public.getMsg("CA_CHECK_RECORD",(i['dns_name'])))
                        auth_status_response = client.check_authorization_status(i["authorization_url"])
                        r_data = auth_status_response.json()
                        if r_data["status"] == "pending":
                            client.respond_to_challenge(i["acme_keyauthorization"], i["dns_challenge_url"])

                    for i in responders:
                        self.write_log(public.getMsg("CHECK_CA_RES",(i['dns_name'],)))
                        client.check_authorization_status(i["authorization_url"], ["valid","invalid"])
                except Exception as ex:
                    self.write_log(public.getMsg("APPLY_WITH_DNS_ERR",(str(ex),)))
                    for i in responders:
                        self.write_log(public.getMsg("CHECK_TXT_RECORD",(i['dns_name'],i['domain_dns_value'])))
                        self.check_dns(self.get_acme_name(i['dns_name']),i['domain_dns_value'])
                        self.write_log(public.getMsg("CA_CHECK_RECORD",(i['dns_name'])))
                        auth_status_response = client.check_authorization_status(i["authorization_url"])
                        r_data = auth_status_response.json()
                        if r_data["status"] == "pending":
                            client.respond_to_challenge(i["acme_keyauthorization"], i["dns_challenge_url"])
                    for i in responders:
                        self.write_log(public.getMsg("CHECK_CA_RES",(i['dns_name'],)))
                        client.check_authorization_status(i["authorization_url"], ["valid","invalid"])
                self.write_log(public.getMsg("ALL_DOMAIN_V_PASS"))
                certificate_url = client.send_csr(finalize_url)
                self.write_log(public.getMsg("FETCH_CERT_CONTENT"))
                certificate = client.download_certificate(certificate_url)
                if certificate:
                    certificate = self.split_ca_data(certificate)
                    result['cert'] = certificate['cert']
                    result['ca_data'] = certificate['ca_data']
                    result['key'] = client.certificate_key
                    result['account_key'] = client.account_key
                    result['status'] = True

            except Exception as e:
                raise e
            finally:   
                try:
                    for i in dns_names_to_delete:
                        self.write_log(public.getMsg("CLEAR_RESOLVE_HISTORY",(i["dns_name"])))
                        dns_class.delete_dns_record(i["dns_name"], i["domain_dns_value"])
                except :
                    pass

        except Exception as e:
            try:
                for i in dns_names_to_delete:
                    self.write_log(public.getMsg("CLEAR_RESOLVE_HISTORY",(i["dns_name"])))
                    dns_class.delete_dns_record(i["dns_name"], i["domain_dns_value"])
            except:pass
            self.write_log(public.getMsg("DNS_APPLY_ERR",(str(public.get_error_info()),)))
            self.write_log("=" * 50)
            res = str(e).split('>>>>')
            err = False
            try:
                err = json.loads(res[1])
            except: err = False
            result['msg'] =  [self.get_error(res[0]),err]
        return result

    #文件验证
    def crate_let_by_file(self,data):
        result = {}
        result['status'] = False
        result['clecks'] = []
        try:
            self.write_log(public.getMsg("INIT_ACME"))
            log_level = "INFO"
            if data['account_key']: log_level = 'ERROR'
            if not data['email']: data['email'] = public.M('users').getField('email')
            client = sewer.Client(domain_name = data['first_domain'],dns_class = None,account_key = data['account_key'],domain_alt_names = data['domains'],contact_email = str(data['email']),LOG_LEVEL = log_level,ACME_AUTH_STATUS_WAIT_PERIOD = 15,ACME_AUTH_STATUS_MAX_CHECKS = 5,ACME_REQUEST_TIMEOUT = 20,ACME_DIRECTORY_URL = self.let_url)
            self.write_log(public.getMsg("REGISTER_ACCOUNT"))
            client.acme_register()
            authorizations, finalize_url = client.apply_for_cert_issuance()
            responders = []
            sucess_domains = []
            self.write_log(public.getMsg("GET_VERIFICATION_INFO"))
            for url in authorizations:
                identifier_auth = self.get_identifier_authorization(client,url)
             
                authorization_url = identifier_auth["url"]
                http_name = identifier_auth["domain"]
                http_token = identifier_auth["http_token"]
                http_challenge_url = identifier_auth["http_challenge_url"]

                acme_keyauthorization, domain_http_value = client.get_keyauthorization(http_token)   
                acme_dir = '%s/.well-known/acme-challenge' % (data['site_dir'])
                if not os.path.exists(acme_dir): os.makedirs(acme_dir)
               
                #写入token
                wellknown_path = acme_dir + '/' + http_token
                self.write_log(public.getMsg("CREATE_V_FILE",(wellknown_path,)))
                public.writeFile(wellknown_path,acme_keyauthorization)
                wellknown_url = "http://{0}/.well-known/acme-challenge/{1}".format(http_name, http_token)

                result['clecks'].append({'wellknown_url':wellknown_url,'http_token':http_token})
                is_check = False
                n = 0
                self.write_log(public.getMsg("CHECK_FILE_CONTENT",(wellknown_url)))
                while n < 5:
                    print("wait_check_authorization_status")
                    try:
                        retkey = public.httpGet(wellknown_url,20)
                        if retkey == acme_keyauthorization:
                            is_check = True
                            self.write_log(public.getMsg("CHECK_FILE_CONTENT1",(retkey,)))
                            break
                    except :
                        pass
                    n += 1
                    time.sleep(1)
                sucess_domains.append(http_name)
                responders.append({"http_name":http_name,"authorization_url": authorization_url, "acme_keyauthorization": acme_keyauthorization,"http_challenge_url": http_challenge_url})

            if len(sucess_domains) > 0: 
                #验证
                for i in responders:
                    self.write_log(public.getMsg("CA_CHECK_RECORD",(i['http_name'],)))
                    auth_status_response = client.check_authorization_status(i["authorization_url"])
                    if auth_status_response.json()["status"] == "pending":
                        client.respond_to_challenge(i["acme_keyauthorization"], i["http_challenge_url"]).json()

                for i in responders:
                    self.write_log(public.getMsg("CHECK_CA_RES",(i['http_name'],)))
                    client.check_authorization_status(i["authorization_url"], ["valid","invalid"])

                self.write_log(public.getMsg("ALL_DOMAIN_V_PASS"))
                certificate_url = client.send_csr(finalize_url)
                self.write_log(public.getMsg("GET_CERT_CONTENT"))
                certificate = client.download_certificate(certificate_url)
               
                if certificate:
                    certificate = self.split_ca_data(certificate)
                    result['cert'] = certificate['cert']
                    result['ca_data'] = certificate['ca_data']
                    result['key'] = client.certificate_key
                    result['account_key'] = client.account_key
                    result['status'] = True

                else:
                    result['msg'] = public.getMsg('CERT_APPLY_ERR')
            else:
                result['msg'] = public.getMsg("APPLY_SSL_ERROR_MSG")
        except Exception as e:
            self.write_log(public.getMsg("DNS_APPLY_ERR",(str(public.get_error_info()),)))
            self.write_log("=" * 50)
            res = str(e).split('>>>>')
            err = False
            try:
                err = json.loads(res[1])
            except: err = False
            result['msg'] =  [self.get_error(res[0]),err]
        return result

    
    def get_identifier_authorization(self,client, url):
        
        headers = {"User-Agent": client.User_Agent}
        get_identifier_authorization_response = requests.get(url, timeout = client.ACME_REQUEST_TIMEOUT, headers=headers,verify=False)
        if get_identifier_authorization_response.status_code not in [200, 201]:
            raise ValueError("Error getting identifier authorization: status_code={status_code}".format(status_code=get_identifier_authorization_response.status_code ) )
        res = get_identifier_authorization_response.json()
        domain = res["identifier"]["value"]
        wildcard = res.get("wildcard")
        if wildcard:
            domain = "*." + domain

        for i in res["challenges"]:
            if i["type"] == "http-01":
                http_challenge = i
        http_token = http_challenge["token"]
        http_challenge_url = http_challenge["url"]
        identifier_auth = {
            "domain": domain,
            "url": url,
            "wildcard": wildcard,
            "http_token": http_token,
            "http_challenge_url": http_challenge_url,
        }
        return identifier_auth

    #检查DNS记录
    def check_dns(self,domain,value,type='TXT'):
        time.sleep(5)
        n = 0
        while n < 10:
            try:
                import dns.resolver
                ns = dns.resolver.query(domain,type)
                for j in ns.response.answer:
                    for i in j.items:
                        txt_value = i.to_text().replace('"','').strip()
                        if txt_value == value:
                            self.write_log(public.getMsg("SUCCESS_V",(domain,type,txt_value)))
                            print("Verification succeeded: %s" % txt_value)
                            return True
            except:
                try:
                    import dns.resolver
                except:
                    return False
            n+=1
            time.sleep(5)
        return True

    #获取证书哈希
    def get_cert_data(self,path):
        try:
            if path[-4:] == '.pfx':   
                f = open(path,'rb') 
                pfx_buffer = f.read() 
                p12 = crypto.load_pkcs12(pfx_buffer,'')
                x509 = p12.get_certificate()
            else:
                cret_data = public.readFile(path)
                x509 = crypto.load_certificate(crypto.FILETYPE_PEM, cret_data)
            
            buffs = x509.digest('sha1')
            hash =  bytes.decode(buffs).replace(':','')
            data = {}
            data['hash'] = hash
            data['timeout'] = bytes.decode(x509.get_notAfter())[:-1]
            return data
        except :
            return False      


    #获取快过期的证书
    def get_renew_lets_bytimeout(self,cron_list):
        tday = 30
        path = self.setupPath + '/panel/vhost/cert'      
        nlist = {}
        new_list = {}
        for siteName in cron_list:   
            spath =  path + '/' + siteName
            #验证是否存在续签KEY
            if os.path.exists(spath + '/account_key.key'):
                if public.M('sites').where("name=?",(siteName,)).count():
                    new_list[siteName] = cron_list[siteName]
                    data = self.get_cert_data(self.setupPath + '/panel/vhost/cert/' + siteName + '/fullchain.pem')
                    timeout = int(time.mktime(time.strptime(data['timeout'],'%Y%m%d%H%M%S')))
                    eday = (timeout - int(time.time())) / 86400
                    if eday < 30:
                        nlist[siteName] = cron_list[siteName]
        #清理过期配置
        public.writeFile(self.setupPath + '/panel/vhost/cert/crontab.json',json.dumps(new_list))
        return nlist

    #===================================== 计划任务续订证书 =====================================#
    #续订
    def renew_lets_ssl(self):        
        cpath = self.setupPath + '/panel/vhost/cert/crontab.json'
        if not os.path.exists(cpath):  
            print(public.getMsg("NO_ORDER_RENEW") )
        else:
            old_list = json.loads(public.ReadFile(cpath))    
            print('=======================================================================')
            print(public.getMsg('TOTAL_RENEW',(time.strftime('%Y-%m-%d %X',time.localtime()),str(len(old_list)))))
            cron_list = self.get_renew_lets_bytimeout(old_list)

            tlist = []
            for siteName in old_list:                 
                if not siteName in cron_list: tlist.append(siteName)
            print(public.getMsg('SSL_NOT_EXPIRED_OR_NOT_USE',(','.join(tlist),)))
            print(public.getMsg('WAIT_RENEW1',(time.strftime('%Y-%m-%d %X',time.localtime()),str(len(cron_list)))))
            
            sucess_list  = []
            err_list = []
            for siteName in cron_list:
                data = cron_list[siteName]
                ret = self.renew_lest_cert(data)
                if ret['status']:
                    sucess_list.append(siteName)
                else:
                    err_list.append({"siteName":siteName,"msg":ret['msg']})
            print(public.getMsg("RENEW_COMPLETED",(str(len(cron_list)),str(len(sucess_list)),str(len(err_list)))))
            if len(sucess_list) > 0:       
                print(public.getMsg("RENEW_SUCCESS2",(','.join(sucess_list),)))
            if len(err_list) > 0:       
                print(public.getMsg("RENEW_FAILED2"))
                for x in err_list:
                    print("    %s ->> %s" % (x['siteName'],x['msg']))

            print('=======================================================================')
            print(" ")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        type = sys.argv[1]
        if type == 'renew_lets_ssl':
            try:
                panelLets().renew_lets_ssl()
            except: pass
            os.system(public.get_python_bin() + " /www/server/panel/class/acme_v2.py --renew=1")
