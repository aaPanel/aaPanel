#coding: utf-8
# +-------------------------------------------------------------------
# | 宝塔Linux面板
# +-------------------------------------------------------------------
# | Copyright (c) 2015-2099 宝塔软件(http://bt.cn) All rights reserved.
# +-------------------------------------------------------------------
# | Author: 曹觉心 <314866873@qq.com>
# +-------------------------------------------------------------------
import os,sys,json,time
setup_path = '/www/server/panel'
os.chdir(setup_path)
sys.path.append("class/")
import requests,sewer,public
from OpenSSL import crypto
try:
    requests.packages.urllib3.disable_warnings()
except:pass
import BTPanel
try:
    import dns.resolver
except:
    os.system("pip install dnspython")
    try:
        import dns.resolver
    except:
        pass

class panelLets:
    let_url = "https://acme-v02.api.letsencrypt.org/directory"
    #let_url = "https://acme-staging-v02.api.letsencrypt.org/directory"

    setupPath = None #安装路径  
    server_type = None
    
    #构造方法
    def __init__(self):
        self.setupPath = public.GetConfigValue('setup_path')
        self.server_type = public.get_webserver()

    
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

    #获取根域名
    def get_root_domain(self,domain_name):
        if domain_name.count(".") != 1:  
            pos = domain_name.rfind(".", 0, domain_name.rfind("."))
            subd = domain_name[:pos]
            domain_name =  domain_name[pos + 1 :]
        return domain_name
    
    #获取acmename
    def get_acme_name(self,domain_name):
        domain_name = domain_name.lstrip("*.")
        if domain_name.count(".") > 1:
            zone, middle, last = str(domain_name).rsplit(".", 2)
            root = ".".join([middle, last])
            acme_name = "_acme-challenge.%s.%s" % (zone,root)
        else:          
            root = domain_name
            acme_name = "_acme-challenge.%s" % root
        return acme_name

    #格式化错误输出
    def get_error(self,error):

        if error.find("Max checks allowed") >= 0 :
            return "CA server verification timed out, please wait 5-10 minutes and try again."
        elif error.find("Max retries exceeded with") >= 0:
            return "The CA server connection timed out, please make sure the server network is unobstructed."
        elif error.find("The domain name belongs") >= 0:
            return "The domain name does not belong to this DNS service provider. Please ensure that the domain name is filled in correctly."
        elif error.find('login token ID is invalid') >=0:
            return 'The DNS server connection failed. Please check if the key is correct.'
        elif "too many certificates already issued for exact set of domains" in error or "Error creating new account :: too many registrations for this IP" in error:
            return '<h2>The signing failed, and the number of attempts to apply for a certificate today has reached the limit!</h2>'
        elif "DNS problem: NXDOMAIN looking up A for" in error or "No valid IP addresses found for" in error or "Invalid response from" in error:
            return '<h2>The signing failed, the domain name resolution error, or the resolution is not valid, or the domain name is not filed!</h2>'
        else:
            return error;

    #获取DNS服务器
    def get_dns_class(self,data):
        if data['dnsapi'] == 'dns_ali':
            import panelDnsapi
            dns_class = panelDnsapi.AliyunDns(key = data['dns_param'][0], secret = data['dns_param'][1])
            return dns_class
        elif data['dnsapi'] == 'dns_dp':
            dns_class = sewer.DNSPodDns(DNSPOD_ID = data['dns_param'][0] ,DNSPOD_API_KEY = data['dns_param'][1])
            return dns_class
        elif data['dnsapi'] == 'dns_cx':   
            import panelDnsapi
            dns_class = panelDnsapi.CloudxnsDns(key = data['dns_param'][0] ,secret =data['dns_param'][1])
            result = dns_class.get_domain_list()
            if result['code'] == 1:                
                return dns_class
        elif data['dnsapi'] == 'dns_bt':
            import panelDnsapi
            dns_class = panelDnsapi.Dns_com()
            return dns_class
        return False

    #续签证书
    def renew_lest_cert(self,data):  
        #续签网站
        path = self.setupPath + '/panel/vhost/cert/'+ data['siteName'];
        if not os.path.exists(path):  return public.returnMsg(False, 'The renewal failed and the certificate directory does not exist.')

        account_path = path + "/account_key.key"
        if not os.path.exists(account_path): return public.returnMsg(False, 'Renewal failed, missing account_key.')

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
         
        return public.returnMsg(True, '[%s]The certificate renewal was successful.' % data['siteName'])



    #申请证书
    def apple_lest_cert(self,get):
   
        data = {}        
        data['siteName'] = get.siteName
        data['domains'] = json.loads(get.domains)
        data['email'] = get.email
        data['dnssleep'] = get.dnssleep
             
        if len(data['domains']) <=0 : return public.returnMsg(False, 'The list of applied domain names cannot be empty.')
        
        data['first_domain'] = data['domains'][0]       
     
        path = self.setupPath + '/panel/vhost/cert/'+ data['siteName'];
        if not os.path.exists(path): os.makedirs(path)

        # 检查是否自定义证书
        partnerOrderId = path + '/partnerOrderId';
        if os.path.exists(partnerOrderId): os.remove(partnerOrderId)
        #清理续签key
        re_key = path + '/account_key.key';
        if os.path.exists(re_key): os.remove(re_key)

        re_password = path + '/password';
        if os.path.exists(re_password): os.remove(re_password)
        
        data['account_key'] = None   
        if hasattr(get, 'dnsapi'): 
            if not 'app_root' in get: get.app_root = '0'
            data['app_root'] = get.app_root   
            domain_list = data['domains']
            if data['app_root'] == '1':
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
                    #手动解析提前返回
                    result = self.crate_let_by_oper(data)
                    if 'status' in result and not result['status']:  return result

                    result['status'] = True
                    public.writeFile(domain_path, json.dumps(result))
                    result['msg'] = 'Get successful, please manually resolve the domain name'
                    result['code'] = 2;

                    return result
            elif get.dnsapi == 'dns_bt':
                data['dnsapi'] = get.dnsapi
                certificate = self.crate_let_by_dns(data)
            else:
                data['dnsapi'] = get.dnsapi
                data['dns_param'] = get.dns_param.split('|')
                certificate = self.crate_let_by_dns(data)
        else:
            #文件验证
            data['site_dir'] = get.site_dir;     
            certificate = self.crate_let_by_file(data)       

        if not certificate['status']: return public.returnMsg(False, certificate['msg'])
        
        #保存续签
        cpath = self.setupPath + '/panel/vhost/cert/crontab.json'
        config = {}
        if os.path.exists(cpath):
            config = json.loads(public.readFile(cpath))
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
        echo = public.md5(public.md5('renew_lets_ssl_bt'))
        crontab = public.M('crontab').where('echo=?',(echo,)).find()
        if not crontab:
            cronPath = public.GetConfigValue('setup_path') + '/cron/' + echo    
            shell = 'python %s/panel/class/panelLets.py renew_lets_ssl ' % (self.setupPath)
            public.writeFile(cronPath,shell)
            public.M('crontab').add('name,type,where1,where_hour,where_minute,echo,addtime,status,save,backupTo,sType,sName,sBody,urladdress',("Renew the Letter's Encrypt certificate",'day','','0','10',echo,time.strftime('%Y-%m-%d %X',time.localtime()),1,'','localhost','toShell','',shell,''))
        
        return public.returnMsg(True, 'Successful application.')





    #手动解析
    def crate_let_by_oper(self,data):
        result = {}
        result['status'] = False
        try:
            if not data['email']: data['email'] = public.M('users').getField('email')

            
            #手动解析记录值
            if not 'renew' in data:
                BTPanel.dns_client = sewer.Client(domain_name = data['first_domain'],dns_class = None,account_key = data['account_key'],domain_alt_names = data['domains'],contact_email = str(data['email']) ,ACME_AUTH_STATUS_WAIT_PERIOD = 15,ACME_AUTH_STATUS_MAX_CHECKS = 5,ACME_REQUEST_TIMEOUT = 20,ACME_DIRECTORY_URL = self.let_url)
                domain_dns_value = "placeholder"
                dns_names_to_delete = []

                BTPanel.dns_client.acme_register()
                authorizations, finalize_url = BTPanel.dns_client.apply_for_cert_issuance()
                responders = []
                for url in authorizations:
                    identifier_auth = BTPanel.dns_client.get_identifier_authorization(url)
                    authorization_url = identifier_auth["url"]
                    dns_name = identifier_auth["domain"]
                    dns_token = identifier_auth["dns_token"]
                    dns_challenge_url = identifier_auth["dns_challenge_url"]

                    acme_keyauthorization, domain_dns_value = BTPanel.dns_client.get_keyauthorization(dns_token)
                 
                    acme_name = self.get_acme_name(dns_name)
                    dns_names_to_delete.append({"dns_name": dns_name,"acme_name":acme_name, "domain_dns_value": domain_dns_value})
                    responders.append(
                        {
                            "authorization_url": authorization_url,
                            "acme_keyauthorization": acme_keyauthorization,
                            "dns_challenge_url": dns_challenge_url,
                        }
                    )
            
                dns = {}
                dns['dns_names'] = dns_names_to_delete
                dns['responders'] = responders
                dns['finalize_url'] = finalize_url
                return dns
            else:

                responders = data['dns']['responders']
                dns_names_to_delete = data['dns']['dns_names']
                finalize_url = data['dns']['finalize_url']
                for i in responders:  
                    auth_status_response = BTPanel.dns_client.check_authorization_status(i["authorization_url"])
                    if auth_status_response.json()["status"] == "pending":
                        BTPanel.dns_client.respond_to_challenge(i["acme_keyauthorization"], i["dns_challenge_url"])

                for i in responders:
                    BTPanel.dns_client.check_authorization_status(i["authorization_url"], ["valid"])

                certificate_url = BTPanel.dns_client.send_csr(finalize_url)
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
                    result['msg'] = 'Certificate acquisition failed, please try again later.'

        except Exception as e:
            print(public.get_error_info())
            result['msg'] =  self.get_error(str(e)) 
        return result

    #dns验证
    def crate_let_by_dns(self,data):
        dns_class = self.get_dns_class(data)
        if not dns_class: 
            return public.returnMsg(False, 'The DNS connection failed. Please check if the key is correct.')
     
        result = {}
        result['status'] = False
        try:
            log_level = "INFO"
            if data['account_key']: log_level = 'ERROR'
            if not data['email']: data['email'] = public.M('users').getField('email')
            client = sewer.Client(domain_name = data['first_domain'],domain_alt_names = data['domains'],account_key = data['account_key'],contact_email = str(data['email']),LOG_LEVEL = log_level,ACME_AUTH_STATUS_WAIT_PERIOD = 15,ACME_AUTH_STATUS_MAX_CHECKS = 5,ACME_REQUEST_TIMEOUT = 20, dns_class = dns_class,ACME_DIRECTORY_URL = self.let_url)
            domain_dns_value = "placeholder"
            dns_names_to_delete = []
            try:
                client.acme_register()
                authorizations, finalize_url = client.apply_for_cert_issuance()
                
                responders = []
                for url in authorizations:
                    identifier_auth = client.get_identifier_authorization(url)
                    authorization_url = identifier_auth["url"]
                    dns_name = identifier_auth["domain"]
                    dns_token = identifier_auth["dns_token"]
                    dns_challenge_url = identifier_auth["dns_challenge_url"]

                    acme_keyauthorization, domain_dns_value = client.get_keyauthorization(dns_token)
                    dns_class.create_dns_record(dns_name, domain_dns_value)
                    self.check_dns(self.get_acme_name(dns_name),domain_dns_value)
                    dns_names_to_delete.append({"dns_name": dns_name, "domain_dns_value": domain_dns_value})
                    responders.append({"authorization_url": authorization_url, "acme_keyauthorization": acme_keyauthorization,"dns_challenge_url": dns_challenge_url} )
                n = 0
                while n<2:
                    print(n+1," verification")
                    try:
                        for i in responders:
                            auth_status_response = client.check_authorization_status(i["authorization_url"])
                            r_data = auth_status_response.json()
                            if r_data["status"] == "pending":
                                client.respond_to_challenge(i["acme_keyauthorization"], i["dns_challenge_url"])

                        for i in responders: client.check_authorization_status(i["authorization_url"], ["valid"])
                        break
                    except:
                        n+=1

                certificate_url = client.send_csr(finalize_url)
                certificate = client.download_certificate(certificate_url)
                if certificate:
                    certificate = self.split_ca_data(certificate)
                    result['cert'] = certificate['cert']
                    result['ca_data'] = certificate['ca_data']
                    result['key'] = client.certificate_key
                    result['account_key'] = client.account_key
                    result['status'] = True

            except Exception as e:
                print(public.get_error_info())
                raise e
            finally:   
                try:
                    for i in dns_names_to_delete: dns_class.delete_dns_record(i["dns_name"], i["domain_dns_value"])
                except :
                    pass

        except Exception as err:  
            print(public.get_error_info())
            result['msg'] =  self.get_error(str(err)) 
        return result

    #文件验证
    def crate_let_by_file(self,data):
        result = {}
        result['status'] = False
        result['clecks'] = []
        try:
            log_level = "INFO"
            if data['account_key']: log_level = 'ERROR'
            if not data['email']: data['email'] = public.M('users').getField('email')
            client = sewer.Client(domain_name = data['first_domain'],dns_class = None,account_key = data['account_key'],domain_alt_names = data['domains'],contact_email = str(data['email']),LOG_LEVEL = log_level,ACME_AUTH_STATUS_WAIT_PERIOD = 15,ACME_AUTH_STATUS_MAX_CHECKS = 5,ACME_REQUEST_TIMEOUT = 20,ACME_DIRECTORY_URL = self.let_url)
            
            client.acme_register()
            authorizations, finalize_url = client.apply_for_cert_issuance()
            responders = []
            sucess_domains = []
            for url in authorizations:
                identifier_auth = self.get_identifier_authorization(client,url)
             
                authorization_url = identifier_auth["url"]
                http_name = identifier_auth["domain"]
                http_token = identifier_auth["http_token"]
                http_challenge_url = identifier_auth["http_challenge_url"]

                acme_keyauthorization, domain_http_value = client.get_keyauthorization(http_token)   
                acme_dir = '%s/.well-known/acme-challenge' % (data['site_dir']);
                if not os.path.exists(acme_dir): os.makedirs(acme_dir)
               
                #写入token
                wellknown_path = acme_dir + '/' + http_token               
                public.writeFile(wellknown_path,acme_keyauthorization)
                wellknown_url = "http://{0}/.well-known/acme-challenge/{1}".format(http_name, http_token)
                result['clecks'].append({'wellknown_url':wellknown_url,'http_token':http_token});
                is_check = False
                n = 0
                while n < 5:
                    print("wait_check_authorization_status")
                    try:
                        retkey = public.httpGet(wellknown_url,20)
                        if retkey == acme_keyauthorization:
                            is_check = True
                            break
                    except :
                        pass
                    n += 1
                if is_check:
                    sucess_domains.append(http_name) 
                    responders.append({"authorization_url": authorization_url, "acme_keyauthorization": acme_keyauthorization,"http_challenge_url": http_challenge_url})

            if len(sucess_domains) > 0: 
                #验证
                for i in responders:
                    auth_status_response = client.check_authorization_status(i["authorization_url"])          
                    if auth_status_response.json()["status"] == "pending":
                        client.respond_to_challenge(i["acme_keyauthorization"], i["http_challenge_url"])

                for i in responders:
                    client.check_authorization_status(i["authorization_url"], ["valid"])

                certificate_url = client.send_csr(finalize_url)
                certificate = client.download_certificate(certificate_url)
               
                if certificate:
                    certificate = self.split_ca_data(certificate)
                    result['cert'] = certificate['cert']
                    result['ca_data'] = certificate['ca_data']
                    result['key'] = client.certificate_key
                    result['account_key'] = client.account_key
                    result['status'] = True
                else:
                    result['msg'] = 'Certificate acquisition failed, please try again later.'
            else:
                result['msg'] = "The signing failed, we were unable to verify your domain name:<p>1. Check if the domain name is bound to the corresponding site.</p><p>2. Check if the domain name is correctly resolved to the server, or the resolution is not fully effective.</p><p>3. If your site has a reverse proxy set up, or if you are using a CDN, please turn it off first.</p><p>4. If your site has a 301 redirect, please turn it off first</p><p>5. If the above checks confirm that there is no problem, please try to change the DNS service provider.</p>'"
        except Exception as e:
            result['msg'] =  self.get_error(str(e)) 
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
                        print(txt_value)
                        if txt_value == value:
                            print("Successful verification：",txt_value)
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
            print("|-There are currently no certificates to renew." );
        else:
            old_list = json.loads(public.ReadFile(cpath))    
            print('=======================================================================')
            print('|-%s Total [%s] renewal of visa tasks' % (time.strftime('%Y-%m-%d %X',time.localtime()),len(old_list)))
            cron_list = self.get_renew_lets_bytimeout(old_list)

            tlist = []
            for siteName in old_list:                 
                if not siteName in cron_list: tlist.append(siteName)
            print('|-[%s]Not expired or the site does not use the Let\'s Encrypt certificate.' % (','.join(tlist)))
            print('|-%s Waiting for renewal[%s].' % (time.strftime('%Y-%m-%d %X',time.localtime()),len(cron_list)))
            
            sucess_list  = []
            err_list = []
            for siteName in cron_list:
                data = cron_list[siteName]
                ret = self.renew_lest_cert(data)
                if ret['status']:
                    sucess_list.append(siteName)
                else:
                    err_list.append({"siteName":siteName,"msg":ret['msg']})
            print("|-After the task is completed, a total of renewals are required.[%s], renewal success [%s], renewal failed [%s]. " % (len(cron_list),len(sucess_list),len(err_list)));
            if len(sucess_list) > 0:       
                print("|-Renewal success：%s" % (','.join(sucess_list)))
            if len(err_list) > 0:       
                print("|-Renewal failed：")
                for x in err_list:
                    print("    %s ->> %s" % (x['siteName'],x['msg']))

            print('=======================================================================')
            print(" ");

if __name__ == "__main__":
    if len(sys.argv) > 1:
        type = sys.argv[1]
        if type == 'renew_lets_ssl':
            panelLets().renew_lets_ssl()
