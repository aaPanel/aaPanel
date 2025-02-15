#!/usr/bin/python
#coding: utf-8
# -------------------------------------------------------------------
# aapanel
# -------------------------------------------------------------------
# Copyright (c) 2015-2099 宝塔软件(http://bt.cn) All rights reserved.
# -------------------------------------------------------------------
# Author: hwliang <hwl@bt.cn> a
# -------------------------------------------------------------------

# -------------------------------------------------------------------
# ACME v2客户端
# -------------------------------------------------------------------
import re
import fcntl
import datetime
import binascii
import hashlib
import base64
import json
import shutil
import time
import os
import sys
os.chdir('/www/server/panel')
if not 'class/' in sys.path:
    sys.path.insert(0,'class/')
import http_requests as requests
import public

try:
    import OpenSSL
except:
    public.ExecShell("btpip install pyopenssl")
    import OpenSSL
try:
    import dns.resolver
except:
    public.ExecShell("btpip install dnspython")
    import dns.resolver

####
# auth to 格式说明
# 旧版 auth to 格式：
# 文件验证：/www/server/xxxx/xxxx
# DNS->手动：dns  DNS->api: CloudFlareDns|XXXXXXXX|XXXXXXXXX
#
# 新版 auth to 格式：
# DNS->手动：dns DNS->api: dns#@api

class acme_v2:
    _url = None
    _apis = None
    _config = {}
    _dns_domains = []
    _bits = 2048
    _acme_timeout = 30
    _dns_class = None
    _user_agent = "BaoTa/1.0 (+https://www.aapanel.com)"
    _replay_nonce = None
    _verify = False
    _digest = "sha256"
    _max_check_num = 15
    _wait_time = 5
    _mod_index = {True: "Staging", False: "Production"}
    _debug = False
    _auto_wildcard = False
    _dnsapi_file = 'config/dns_api.json'
    _save_path = 'vhost/letsencrypt'
    _conf_file = 'config/letsencrypt.json'
    _conf_file_v2 = 'config/letsencrypt_v2.json'
    _request_type = 'curl'
    _stop_rp_file = '{}/data/stop_rp_when_renew_ssl.pl'.format(public.get_panel_path())

    def __init__(self):
        if not os.path.exists(self._conf_file_v2) and os.path.exists(self._conf_file):
            shutil.copyfile(self._conf_file, self._conf_file_v2)
        if self._debug:
            self._url = 'https://acme-staging-v02.api.letsencrypt.org/directory'
        else:
            self._url = 'https://acme-v02.api.letsencrypt.org/directory'
        self._config = self.read_config()
        self._nginx_cache_file_auth = {}
        self._can_use_lua = None
        self._well_known_check_cache = {}

    def can_use_lua_module(self):
        if self._can_use_lua is None:
            # 查询lua_module 不为空
            self._can_use_lua = public.ExecShell("nginx -V 2>&1 |grep lua_nginx_module")[0].strip() != ''
        return self._can_use_lua

    # 返回是否能通过lua 做了文件验证处理， 如果返回True，则表示可以处理了验证文件， 不再走之前的 if 验证方式
    def can_use_lua_for_site(self, site_name: str, site_type: str):
        if self._can_use_lua is None:
            # 查询lua_module 不为空
            self._can_use_lua = public.ExecShell("nginx -V 2>&1 |grep lua_nginx_module")[0].strip() != ''

        if not self._can_use_lua:
            return False

        if site_type.lower() in ("php", "proxy"):
            prefix = ""
        else:
            prefix = site_type.lower() + "_"

        ng_file = "{}/nginx/{}{}.conf".format(public.get_vhost_path(), prefix, site_name)
        ng_data = public.readFile(ng_file)
        if not ng_data:
            return False

        rep_well_known = re.compile(
            r"(#.*\n)?\s*include\s+/www/server/panel/vhost/nginx/well-known/.*\.conf;.*\n(#.*\n)?"
            r"(.*\n)*?\s*#error_page 404/404\.html;"
        )   # 匹配一下引入的外部配置文件，同时保证这个配置在SSL配置之前， 这样避免路由匹配问题

        if rep_well_known.search(ng_data):
            lua_file = "{}/nginx/well-known/{}.conf".format(public.get_vhost_path(), site_name)
            lua_data = public.readFile(lua_file)
            if not lua_data or "set_by_lua_block $well_known" not in lua_data:
                return False
            else:
                return True
        else:
            return False

    # 返回是否能通过if 判断方式做了文件验证处理， 如果返回True，则表示可以
    @staticmethod
    def can_use_if_for_file_check(site_name: str, site_type: str):
        if site_type.lower() in ("php", "proxy"):
            prefix = ""
        else:
            prefix = site_type.lower() + "_"

        # if 方式的文件验证必须是可重载的情况
        if public.checkWebConfig() is not True:
            return False

        ng_file = "{}/nginx/{}{}.conf".format(public.get_vhost_path(), prefix, site_name)
        ng_data = public.readFile(ng_file)
        if not ng_data:
            return False

        rep_well_known = re.compile(
            r"(#.*\n)?\s*include\s+/www/server/panel/vhost/nginx/well-known/.*\.conf;.*\n(#.*\n)?"
            r"(.*\n)*?\s*#error_page 404/404\.html;"
        )   # 匹配一下引入的外部配置文件，同时保证这个配置在SSL配置之前， 这样避免路由匹配问题

        if rep_well_known.search(ng_data):
            return True
        else:
            return False

    # 返回配置文件是否支持使用普通的文件验证
    @staticmethod
    def can_use_base_file_check(site_name: str, site_type: str):
        if site_type.lower() in ("php", "proxy", "wp", "wp2"):
            prefix = ""
        else:
            prefix = site_type.lower() + "_"

        webserver = public.get_webserver()
        if webserver == "nginx":
            ng_file = "{}/nginx/{}{}.conf".format(public.get_vhost_path(), prefix, site_name)
            ng_data = public.readFile(ng_file)
            if not ng_data:
                return False
            rep_well_known = re.compile(r"location\s+([=~^]*\s*)?/?\\?\.well-known/?\s*{")
            if rep_well_known.search(ng_data):
                return True
            else:
                return False
        elif webserver == "apache" and prefix:  # PHP 不用检查
            ap_file = "{}/apache/{}{}.conf".format(public.get_vhost_path(), prefix, site_name)
            ap_data = public.readFile(ap_file)
            if not ap_data:
                return False
            rep_well_known_list = [
                re.compile(r"<IfModule\s+alias_module>\s+Alias\s+/\.well-known/\s+\S+\s+</IfModule>"),
                re.compile(r"\s*ProxyPass\s+/\.well-known/\s+!", re.M),
            ]
            for rep_well_known in rep_well_known_list:
                if rep_well_known.search(ap_data):
                    return True
            return False
        return True

    # 取接口目录
    def get_apis(self):
        if not self._apis:
            # 尝试从配置文件中获取
            api_index = self._mod_index[self._debug]
            if not 'apis' in self._config:
                self._config['apis'] = {}
            if api_index in self._config['apis']:
                if 'expires' in self._config['apis'][api_index] and 'directory' in self._config['apis'][api_index]:
                    if time.time() < self._config['apis'][api_index]['expires']:
                        self._apis = self._config['apis'][api_index]['directory']
                        return self._apis

            # 尝试从云端获取
            res = requests.get(self._url,s_type=self._request_type)
            if not res.status_code in [200, 201]:
                result = res.json()
                if "type" in result:
                    if result['type'] == 'urn:acme:error:serverInternal':
                        raise Exception(public.get_msg_gettext(
                            'Service shutdown or internal error due to maintenance, check [ https://letsencrypt.status.io ] see for more details.'))
                raise Exception(res.content)
            s_body = res.json()
            self._apis = {}
            self._apis['newAccount'] = s_body['newAccount']
            self._apis['newNonce'] = s_body['newNonce']
            self._apis['newOrder'] = s_body['newOrder']
            self._apis['revokeCert'] = s_body['revokeCert']
            self._apis['keyChange'] = s_body['keyChange']

            # 保存到配置文件
            self._config['apis'][api_index] = {}
            self._config['apis'][api_index]['directory'] = self._apis
            self._config['apis'][api_index]['expires'] = time.time() + \
                86400  # 24小时后过期
            self.save_config()
        return self._apis

    # 获取帐户信息
    def get_account_info(self, args):
        try:
            if not 'account' in self._config:
                return {}
            k = self._mod_index[self._debug]
            if not k in self._config['account']:
                self.get_apis()
                self.get_kid()
            account = self._config['account'][k]
            account['email'] = self._config['email']
            self.set_crond()
            return account
        except Exception as ex:
            return public.return_msg_gettext(False, str(ex))

    # 设置帐户信息
    def set_account_info(self, args):
        if not 'account' in self._config:
            return public.return_msg_gettext(False, 'The specified account does not exist')
        account = json.loads(args.account)
        if 'email' in account:
            self._config['email'] = account['email']
            del (account['email'])
        self._config['account'][self._mod_index[self._debug]] = account
        self.save_config()
        return public.return_msg_gettext(True, 'Setup successfully!')

    # 获取订单列表
    def get_orders(self, args):
        if not 'orders' in self._config:
            return []
        s_orders = []
        for index in self._config['orders'].keys():
            tmp_order = self._config['orders'][index]
            tmp_order['index'] = index
            s_orders.append(tmp_order)
        return s_orders

    # 删除订单
    def remove_order(self, args):
        if not 'orders' in self._config:
            return public.return_msg_gettext(False, 'The specified order does not exist!')
        if not args.index in self._config['orders']:
            return public.return_msg_gettext(False, 'The specified order does not exist!')
        del (self._config['orders'][args.index])
        self.save_config()
        return public.return_msg_gettext(True, 'Order deleted successfully!')

    # 取指定订单数据
    def get_order_find(self, args):
        if not 'orders' in self._config:
            return public.return_msg_gettext(False, 'The specified order does not exist!')
        if not args.index in self._config['orders']:
            return public.return_msg_gettext(False, 'The specified order does not exist!')
        result = self._config['orders'][args.index]
        result['cert'] = self.get_cert_info(args.index)
        return result

    # 获取证书信息
    def get_cert_info(self, index):
        cert = {}
        path = self._config['orders'][index]['save_path']
        if not os.path.exists(path):
            self.download_cert(index)
        cert['private_key'] = public.readFile(path + "/privkey.pem")
        cert['fullchain'] = public.readFile(path + "/fullchain.pem")
        return cert

    # 更新证书压缩包
    def update_zip(self, args):
        path = self._config['orders'][args.index]['save_path']
        if not os.path.exists(path):  # 尝试重新下载证书
            self.download_cert(args.index)
        if not os.path.exists(path):
            return public.return_msg_gettext(False, 'Certificate read failed, directory does not exist!')
        import panelTask
        bt_task = panelTask.bt_task()
        zip_file = path + '/cert.zip'
        result = bt_task._zip(path, '.', path + '/cert.zip', '/dev/null', 'zip')
        if not os.path.exists(zip_file):
            return result
        return public.return_msg_gettext(True, zip_file)

    # 吊销证书
    def revoke_order(self, index):
        if type(index) != str:
            index = index.index
        if not index in self._config['orders']:
            raise Exception(public.get_msg_gettext('The specified order does not exist!'))
        cert_path = self._config['orders'][index]['save_path']
        if not os.path.exists(cert_path):
            raise Exception(public.get_msg_gettext('No certificate found for the specified order!'))
        cert = self.dump_der(cert_path)
        if not cert:
            raise Exception(public.get_msg_gettext('Certificate read failed!'))
        payload = {
            "certificate": self.calculate_safe_base64(cert),
            "reason": 4
        }
        res = self.acme_request(self._apis['revokeCert'], payload)
        if res.status_code in [200, 201]:
            if os.path.exists(cert_path):
                public.ExecShell("rm -rf {}".format(cert_path))
            del (self._config['orders'][index])
            self.save_config()
            return public.return_msg_gettext(True, "Certificate revoked!")
        return res.json()

    # 取根域名和记录值
    def extract_zone(self, domain_name):
        top_domain_list = public.readFile('{}/config/domain_root.txt'.format(public.get_panel_path()))
        if top_domain_list:
            top_domain_list = top_domain_list.strip().split('\n')
        else:
            top_domain_list = []
        old_domain_name = domain_name
        top_domain = "." + ".".join(domain_name.rsplit('.')[-2:])
        new_top_domain = "." + top_domain.replace(".", "")
        is_tow_top = False
        if top_domain in top_domain_list:
            is_tow_top = True
            domain_name = domain_name[:-len(top_domain)] + new_top_domain

        if domain_name.count(".") > 1:
            zone, middle, last = domain_name.rsplit(".", 2)
            if is_tow_top:
                last = top_domain[1:]
            root = ".".join([middle, last])
        else:
            zone = ""
            root = old_domain_name
        return root, zone

    # 自动构造通配符
    def auto_wildcard(self, domains):
        if not domains:
            return domains
        domain_list = []
        for domain in domains:
            root, zone = self.extract_zone(domain)
            tmp_list = zone.rsplit(".", 1)
            if len(tmp_list) == 1:
                if root not in domain_list:
                    domain_list.append(root)
                if not "*." + root in domain_list:
                    domain_list.append("*." + root)
            else:
                new_root = "{}.{}".format(tmp_list[1], root)
                if new_root not in domain_list:
                    domain_list.append(new_root)
                if not "*." + new_root in domain_list:
                    domain_list.append("*." + new_root)
        return domain_list

    # 构造域名列表
    def format_domains(self, domains):
        if type(domains) != list:
            return []
        # 是否自动构造通配符
        if self._auto_wildcard:
            domains = self.auto_wildcard(domains)
        wildcard = []
        tmp_domains = []
        for domain in domains:
            domain = domain.strip()
            if domain in tmp_domains:
                continue
            # 将通配符域名转为验证正则表达式
            f_index = domain.find("*.")
            if f_index not in [-1, 0]:
                continue
            if f_index == 0:
                wildcard.append(domain.replace(
                    "*", r"^[\w-]+").replace(".", r"\."))
            # 添加到申请列表
            tmp_domains.append(domain)

        # 处理通配符包含
        apply_domains = tmp_domains[:]
        for domain in tmp_domains:
            for w in wildcard:
                if re.match(w, domain):
                    apply_domains.remove(domain)

        return apply_domains

    # 创建订单
    def create_order(self, domains, auth_type, auth_to, index=None):
        domains = self.format_domains(domains)
        if not domains:
            raise Exception(public.get_msg_gettext('Need at least a domain name!'))
        # 构造标识
        identifiers = []
        for domain_name in domains:
            identifiers.append({"type": 'dns', "value": domain_name})
        payload = {"identifiers": identifiers}

        # 请求创建订单
        res = self.acme_request(self._apis['newOrder'], payload)
        if not res.status_code in [201,200]:  # 如果创建失败
            e_body = res.json()
            if 'type' in e_body:
                # 如果随机数失效
                if e_body['type'].find('error:badNonce') != -1:
                    self.get_nonce(force=True)
                    res = self.acme_request(self._apis['newOrder'], payload)

                # 如果帐户失效
                if e_body['detail'].find('KeyID header contained an invalid account URL') != -1:
                    k = self._mod_index[self._debug]
                    del (self._config['account'][k])
                    self.get_kid()
                    self.get_nonce(force=True)
                    res = self.acme_request(self._apis['newOrder'], payload)
            if not res.status_code in [201,200]:
                a_auth = res.json()

                ret_title = self.get_error(str(a_auth))
                raise StopIteration(
                        "{0} >>>> {1}".format(
                            ret_title,
                            json.dumps(a_auth)
                        )
                    )

        # 返回验证地址和验证
        s_json = res.json()
        s_json['auth_type'] = auth_type
        s_json['domains'] = domains
        s_json['auth_to'] = auth_to
        index = self.save_order(s_json, index)
        return index

    def get_site_run_path_byid(self,site_id):
        '''
            @name 通过site_id获取网站运行目录
            @author hwliang
            @param site_id<int> 网站标识
            @return None or string
        '''
        if public.M('sites').where('id=? and project_type=?', (site_id, 'PHP')).count() >= 1:
            site_path = public.M('sites').where('id=?', site_id).getField('path')
            if not site_path: return None
            if not os.path.exists(site_path): return None
            args = public.dict_obj()
            args.id = site_id
            import panelSite
            run_path = panelSite.panelSite().GetRunPath(args)
            if run_path in ['/']: run_path = ''
            if run_path:
                if run_path[0] == '/': run_path = run_path[1:]
            site_run_path = os.path.join(site_path, run_path)
            if not os.path.exists(site_run_path): return site_path
            return site_run_path
        else:
            return False

    def get_site_run_path(self,domains):
        '''
            @name 通过域名列表获取网站运行目录
            @author hwliang
            @param domains<list> 域名列表
            @return None or string
        '''
        site_id = 0
        for domain in domains:
            site_id = public.M('domain').where("name=?",domain).getField('pid')
            if site_id: break

        if not site_id: return None
        return self.get_site_run_path_byid(site_id)

    # 获取验证信息
    def get_auths(self, index):
        if not index in self._config['orders']:
            raise Exception(public.get_msg_gettext('The specified order does not exist!'))

        # 检查是否已经获取过授权信息
        if 'auths' in self._config['orders'][index]:
            # 检查授权信息是否过期
            if time.time() < self._config['orders'][index]['auths'][0]['expires']:
                return self._config['orders'][index]['auths']
        if self._config['orders'][index]['auth_type'] != 'dns':
            site_run_path = self.get_site_run_path(self._config['orders'][index]['domains'])
            if site_run_path: self._config['orders'][index]['auth_to'] = site_run_path

        #清理旧验证
        self.claer_auth_file(index)

        auths = []
        for auth_url in self._config['orders'][index]['authorizations']:
            res = self.acme_request(auth_url, "")
            if res.status_code not in [200, 201]:
                raise Exception("ACEM_AUTH_ERR", (res.json(),))

            s_body = res.json()
            if 'status' in s_body:
                if s_body['status'] in ['invalid']:
                    raise Exception('ACME_INVALID_ORDER')
                if s_body['status'] in ['valid']:  # 跳过无需验证的域名
                    continue

            s_body['expires'] = self.utc_to_time(s_body['expires'])
            identifier_auth = self.get_identifier_auth(index, auth_url, s_body)
            if not identifier_auth:
                raise Exception('ACME_V_INFO_ERR')

            acme_keyauthorization, auth_value = self.get_keyauthorization(
                identifier_auth['token'])
            identifier_auth['acme_keyauthorization'] = acme_keyauthorization
            identifier_auth['auth_value'] = auth_value
            identifier_auth['expires'] = s_body['expires']
            identifier_auth['auth_to'] = self._config['orders'][index]['auth_to']
            identifier_auth['type'] = self._config['orders'][index]['auth_type']

            # 设置验证信息
            self.set_auth_info(identifier_auth, index=index)
            auths.append(identifier_auth)
        self._config['orders'][index]['auths'] = auths
        self.save_config()
        return auths

    # 更新随机数
    def update_replay_nonce(self, res):
        replay_nonce = res.headers.get('Replay-Nonce')
        if replay_nonce:
            self._replay_nonce = replay_nonce

    # 设置验证信息
    def set_auth_info(self, identifier_auth, index=None):

        #从云端验证
        if not self.cloud_check_domain(identifier_auth['domain']):
            self.err = "Cloud verification failed!"

        # 是否手动验证DNS
        if identifier_auth['auth_to'] == 'dns':
            return None

        # 是否文件验证
        if identifier_auth['type'] in ['http', 'tls']:
            self.write_auth_file(
                identifier_auth['auth_to'], identifier_auth['token'], identifier_auth['acme_keyauthorization'], index)
        else:
            # dnsapi验证
            self.create_dns_record(
                identifier_auth['auth_to'], identifier_auth['domain'], identifier_auth['auth_value'])

    #从云端验证域名是否可访问
    def cloud_check_domain(self,domain):
        try:
            result = requests.post('https://www.aapanel.com/api/panel/checkDomain',{"domain":domain,"ssl":1},s_type=self._request_type).json()
            return result['status']
        except: return False


    #清理验证文件
    def claer_auth_file(self,index):
        if not self._config['orders'][index]['auth_type'] in ['http','tls']:
            return True
        acme_path = '{}/.well-known/acme-challenge'.format(self._config['orders'][index]['auth_to'])
        acme_path = acme_path.replace("//",'/')
        write_log(public.get_msg_gettext('|-Verify the dir：{}', (acme_path,)))
        if os.path.exists(acme_path):
            public.ExecShell("rm -f {}/*".format(acme_path))

        acme_path = '/www/server/stop/.well-known/acme-challenge'
        if os.path.exists(acme_path):
            public.ExecShell("rm -f {}/*".format(acme_path))

    def change_well_known_mod(self, path_dir: str):
        path_dir = path_dir.rstrip("/")
        if not os.path.isdir(path_dir):
            return False
        if path_dir in self._well_known_check_cache:
            return True
        else:
            self._well_known_check_cache[path_dir] = True
        import stat

        try:
            import pwd
            uid_data = pwd.getpwnam("www")
            uid = uid_data.pw_uid
            gid = uid_data.pw_gid
        except:
            return

        # 逐级给最低访问权限
        while path_dir != "/":
            path_dir_stat = os.stat(path_dir)
            if path_dir_stat.st_uid == 0 and uid != 0:
                old_mod = stat.S_IMODE(path_dir_stat.st_mode)
                if not old_mod & (1 << 3):
                    os.chmod(path_dir, old_mod + (1 << 3))  # chmod g+x
            if path_dir_stat.st_uid == uid:
                old_mod = stat.S_IMODE(path_dir_stat.st_mode)
                if not old_mod & (1 << 6):
                    os.chmod(path_dir, old_mod + (1 << 6))  # chmod u+x
            elif path_dir_stat.st_gid == gid:
                old_mod = stat.S_IMODE(path_dir_stat.st_mode)
                if not old_mod & (1 << 3):
                    os.chmod(path_dir, old_mod + (1 << 6))  # chmod g+x
            elif path_dir_stat.st_uid != uid or path_dir_stat.st_gid != gid:
                old_mod = stat.S_IMODE(path_dir_stat.st_mode)
                if not old_mod & 1:
                    os.chmod(path_dir, old_mod+1)   # chmod o+x
            path_dir = os.path.dirname(path_dir)

    # 写验证文件
    def write_auth_file(self, auth_to, token, acme_keyauthorization, index):
        if public.get_webserver() == "nginx":
            # 如果是nginx尝试使用配置文件进行验证
            self.write_ngin_authx_file(auth_to, token, acme_keyauthorization, index)

        # 尝试写文件进行验证
        try:
            acme_path = '{}/.well-known/acme-challenge'.format(auth_to)
            acme_path = acme_path.replace("//",'/')
            if not os.path.exists(acme_path):
                os.makedirs(acme_path)
                public.set_own(acme_path, 'www')
            self.change_well_known_mod(acme_path)
            wellknown_path = '{}/{}'.format(acme_path, token)
            public.writeFile(wellknown_path, acme_keyauthorization)
            public.set_own(wellknown_path, 'www')

            acme_path = '/www/server/stop/.well-known/acme-challenge'
            if not os.path.exists(acme_path):
                os.makedirs(acme_path)
                public.set_own(acme_path, 'www')
            self.change_well_known_mod(acme_path)
            wellknown_path = '{}/{}'.format(acme_path,token)
            public.writeFile(wellknown_path,acme_keyauthorization)
            public.set_own(wellknown_path, 'www')
            return True
        except:
            err = public.get_error_info()
            print(err)
            raise Exception(public.get_msg_gettext('Writing verification file failed: {}', (err,)))

    def write_ngin_authx_file(self, auth_to, token, acme_keyauthorization, index):
        site_name, project_type = self.get_site_name_by_domains(self._config["orders"][index]["domains"])
        if site_name is None:
            return

        if self.can_use_lua_for_site(site_name, project_type):
            return

        if project_type.lower() in ("php", "proxy"):
            nginx_conf_path = "{}/vhost/nginx/{}.conf".format(public.get_panel_path(), site_name)
        else:
            nginx_conf_path = "{}/vhost/nginx/{}_{}.conf".format(public.get_panel_path(), project_type.lower(), site_name)
        nginx_conf = public.readFile(nginx_conf_path)
        if nginx_conf is False:
            return

        file_check_config_path = "/www/server/panel/vhost/nginx/well-known/{}.conf".format(site_name)
        if not os.path.exists("/www/server/panel/vhost/nginx/well-known"):
            os.makedirs("/www/server/panel/vhost/nginx/well-known", 0o755)

        # 如果主配置中，没有引用则尝试添加，添加失败就跳出
        if not re.search(r"\s*include\s+/www/server/panel/vhost/nginx/well-known/.*\.conf;", nginx_conf, re.M):
            ssl_line = re.search(r"(#.*\n\s*)?#error_page 404/404\.html;", nginx_conf)
            if ssl_line is None:
                return
            default_cert_apply_check = (
                "#CERT-APPLY-CHECK--START\n"
                "    # Configuration related to file verification for SSL certificate application - Do not delete\n"
                "    include /www/server/panel/vhost/nginx/well-known/{}.conf;\n"
                "    #CERT-APPLY-CHECK--END\n    "
            ).format(site_name)
            if not os.path.exists(file_check_config_path):
                public.writeFile(file_check_config_path, "")

            new_conf = nginx_conf.replace(ssl_line.group(), default_cert_apply_check + ssl_line.group(), 1)
            public.writeFile(nginx_conf_path, new_conf)
            isError = public.checkWebConfig()
            if isError is not True:
                public.writeFile(nginx_conf_path, nginx_conf)
                return

        # 如果主配置有引用， 不再检测位置关系，因为不能保证用户的自定义配置的优先级， 直接进行文件验证的 lua 方式和 if 方式的尝试
        if self.can_use_lua_module():
            self.write_lua_file_for_site(file_check_config_path)
            return

        # 开始尝试if 验证方式
        if auth_to not in self._nginx_cache_file_auth:
            self._nginx_cache_file_auth[auth_to] = []

        self._nginx_cache_file_auth[auth_to].append((token, acme_keyauthorization))

        tmp_data = []
        for token, acme_key in self._nginx_cache_file_auth[auth_to]:
            tmp_data.append((
                'if ($request_uri ~ "^/\\.well-known/acme-challenge/{}.*"){{\n'
                '    return 200 "{}";\n'
                '}}\n'
            ).format(token, acme_key))

        public.writeFile(file_check_config_path, "\n".join(tmp_data))
        isError = public.checkWebConfig()
        if isError is True:
            public.serviceReload()
        else:
            public.writeFile(file_check_config_path, "")

    @staticmethod
    def write_lua_file_for_site(file_check_config_path: str):
        old_data = public.readFile(file_check_config_path)
        if isinstance(old_data, str) and "set_by_lua_block $well_known" in old_data:
            return

        lua_file_data = r"""
set $well_known '';
if ( $uri ~ "^/.well-known/" ) {
  set_by_lua_block $well_known { 
    --get path
    local m,err = ngx.re.match(ngx.var.uri,"/.well-known/(.*)","isjo")
    -- If the path matches
    if m then
      -- Splicing file path
      local filename = ngx.var.document_root .. m[0]
      -- Determine if the file path is legal
      if not ngx.re.find(m[1],"\\\\./","isjo") then
        -- Determine if the file exists
        local is_exists = io.open(filename, "r")
        if not is_exists then
            -- Java project?
            filename = "/www/wwwroot/java_node_ssl" ..  m[0]
        end
        -- release
        if is_exists then is_exists:close() end
        -- read file
        local fp = io.open(filename,'r')
        if fp then
          local file_body = fp:read("*a")
          fp:close()
          if file_body then
            if ngx.re.match(m[1], "\\.json$", "isjo") or 
               m[1] == "apple-app-site-association" or 
               m[1] == "apple-developer-merchantid-domain-association" then
              ngx.header['content-type'] = 'application/json'
            else
              ngx.header['content-type'] = 'text/plain'
            end
            return file_body
          end
        end
      end
    end
    return ""
  }
}

if ( $well_known != "" ) {
  return 200 $well_known;
}
"""
        public.writeFile(file_check_config_path, lua_file_data)
        isError = public.checkWebConfig()
        if isError is True:
            public.serviceReload()
        else:
            public.writeFile(file_check_config_path, old_data)

    # 解析域名
    def create_dns_record(self, auth_to, domain, dns_value):
        # 如果为手动解析
        if auth_to == 'dns' or auth_to.find('|') == -1:
            return None

        import panelDnsapi
        dns_name, key, secret = self.get_dnsapi(auth_to)
        self._dns_class = getattr(panelDnsapi, dns_name)(key, secret)
        self._dns_class.create_dns_record(public.de_punycode(domain), dns_value)
        self._dns_domains.append({"domain": domain, "dns_value": dns_value})
        return

        # # 如果为手动解析
        # if auth_to == 'dns' :
        #     return None

        # from panelDnsapi import DnsMager

        # self._dns_class = DnsMager().get_dns_obj_by_domain(domain)
        # self._dns_class.create_dns_record(public.de_punycode(domain), dns_value)
        # self._dns_domains.append({"domain": domain, "dns_value": dns_value})

    # 解析DNSAPI信息  # 不再使用的
    def get_dnsapi(self, auth_to):
        tmp = auth_to.split('|')
        dns_name = tmp[0]
        key = "None"
        secret = "None"
        if len(tmp) < 3:
            try:
                dnsapi_config = json.loads(public.readFile(self._dnsapi_file))
                for dc in dnsapi_config:
                    if dc['name'] != dns_name:
                        continue
                    if not dc['data']:
                        continue
                    key = dc['data'][0]['value']
                    secret = dc['data'][1]['value']
            except:
                raise Exception(public.get_msg_gettext('No valid DNSAPI key information found'))
        else:
            key = tmp[1]
            secret = tmp[2]
        return dns_name, key, secret

    # 删除域名解析
    def remove_dns_record(self):
        if not self._dns_class:
            return None
        for dns_info in self._dns_domains:
            try:
                self._dns_class.delete_dns_record(
                    public.de_punycode(dns_info['domain']), dns_info['dns_value'])
            except:
                pass
    # 验证域名
    def auth_domain(self, index):
        if index not in self._config['orders']:
            raise Exception(public.get_msg_gettext('The specified order does not exist!'))

        if "auths" not in self._config['orders'][index]:
            raise Exception(public.get_msg_gettext('Order verification information is missing, please try reapplying!'))

        # 开始验证
        for auth in self._config['orders'][index]['auths']:
            res = self.check_auth_status(auth['url'])  # 检查是否需要验证
            if res.json()['status'] == 'pending':
                if auth['type'] == 'dns':  # 尝试提前验证dns解析
                    self.check_dns(
                        "_acme-challenge.{}".format(
                            auth['domain'].replace('*.', '')),
                        auth['auth_value'],
                        "TXT"
                    )
                self.respond_to_challenge(auth)

        # 检查验证结果
        for i in range(len(self._config['orders'][index]['auths'])):
            self.check_auth_status(self._config['orders'][index]['auths'][i]['url'], [
                                   'valid', 'invalid'])
            self._config['orders'][index]['status'] = 'valid'

    # 检查验证状态
    def check_auth_status(self, url, desired_status=None):
        desired_status = desired_status or ["pending", "valid", "invalid"]
        number_of_checks = 0
        while True:
            if desired_status == ['valid', 'invalid']:
                write_log(public.get_msg_gettext('|-{} Query verification results..', (str(number_of_checks + 1),)))
                time.sleep(self._wait_time)
            check_authorization_status_response = self.acme_request(url, "")
            a_auth = check_authorization_status_response.json()
            authorization_status = a_auth["status"]
            number_of_checks += 1
            if authorization_status in desired_status:
                if authorization_status == "invalid":
                    write_log("|-" + public.get_msg_gettext('Verification failed'))
                    try:
                        if 'error' in a_auth['challenges'][0]:
                            ret_title = a_auth['challenges'][0]['error']['detail']
                        elif 'error' in a_auth['challenges'][1]:
                            ret_title = a_auth['challenges'][1]['error']['detail']
                        elif 'error' in a_auth['challenges'][2]:
                            ret_title = a_auth['challenges'][2]['error']['detail']
                        else:
                            ret_title = str(a_auth)
                        ret_title = self.get_error(ret_title)
                    except:
                        ret_title = str(a_auth)
                    raise StopIteration(
                        "{0} >>>> {1}".format(
                            ret_title,
                            json.dumps(a_auth)
                        )
                    )
                break

            if number_of_checks == self._max_check_num:
                raise StopIteration(
                    public.get_msg_gettext(
                        'Error: Attempted verification {} times. The maximum number of verifications is {}. The verification interval is {} seconds.',
                        (
                            str(number_of_checks),
                            str(self._max_check_num),
                            str(self._wait_time)
                        )))
        if desired_status == ['valid', 'invalid']:
            write_log(public.get_msg_gettext('|-Verification succeeded!'))
        return check_authorization_status_response

    # 格式化错误输出
    def get_error(self, error):
        write_log("error_result: " + str(error))
        if error.find("Max checks allowed") >= 0:
            return public.get_msg_gettext(
                'CA cannot verify your domain name, please check if the domain name resolution is correct, or wait 5-10 minutes and try again.')
        elif error.find("Max retries exceeded with") >= 0 or error.find('status_code=0 ') != -1:
            return public.get_msg_gettext('CA server connection timed out, please try again later.')
        elif error.find("The domain name belongs") >= 0:
            return public.get_msg_gettext(
                'The domain name does not belong to this DNS service provider, please make sure the domain name is filled in correctly.')

        elif error.find("domains in the last 168 hours") != -1 and error.find("Error creating new order") != -1:
            return public.get_msg_gettext("Issuance failed, the root domain name of domain name %s exceeds the maximum weekly issuance limit!" % re.findall(r"hours:\s+(.+?),", error))
        elif error.find('login token ID is invalid') >= 0:
            return public.get_msg_gettext('DNS server connection failed, please check if the key is correct.')
        elif error.find('Error getting validation data') != -1:
            return public.get_msg_gettext(
                'Data validation failed and the CA was unable to get the correct captcha from the authenticated connection.')
        elif "too many certificates already issued for exact set of domains" in error:
            return public.get_msg_gettext('Issuing failed, the domain {} has exceeded the limit of weekly reissues!',
                                          (str(re.findall("exact set of domains: (.+):", error)),))
        elif "Error creating new account :: too many registrations for this IP" in error:
            return public.get_msg_gettext(
                'Issuing failed, the current server IP has reached the limit of creating up to 10 accounts every 3 hours.')
        elif "DNS problem: NXDOMAIN looking up A for" in error:
            return public.get_msg_gettext(
                'Validation failed, domain name was not resolved, or resolution did not take effect!')
        elif "Invalid response from" in error:
            return public.get_msg_gettext(
                'Verification failed, domain name resolution error or verification URL cannot be accessed!')
        elif error.find('TLS Web Server Authentication') != -1:
            return public.get_msg_gettext('Connection to CA server failed, please try again later.')
        elif error.find('Name does not end in a public suffix') != -1:
            return public.get_msg_gettext('Unsupported domain name {}, please check the domain name is correct!',
                                          (str(re.findall("Cannot issue for \"(.+)\":", error)),))
        elif error.find('No valid IP addresses found for') != -1:
            return public.get_msg_gettext(
                'No resolution record was found for domain name {}, please check if the domain name resolution takes effect!',
                (str(re.findall("No valid IP addresses found for (.+)", error)),))
        elif error.find('No TXT record found at') != -1:
            return public.get_msg_gettext(
                'No valid TXT resolution record was found in the domain name {}, please check whether the TXT record is parsed correctly. If it is applied by DNSAPI, please try again in 10 minutes!',
                (str(re.findall("No TXT record found at (.+)", error)),))
        elif error.find('Incorrect TXT record') != -1:
            return public.get_msg_gettext(
                'A wrong TXT record was found on {}: {}, please check whether the TXT resolution is correct, if it is applied by DNSAPI, please try again in 10 minutes!',
                (str(re.findall("found at (.+)", error)), str(re.findall("Incorrect TXT record \"(.+)\"", error))))
        elif error.find('Domain not under you or your user') != -1:
            return public.get_msg_gettext(
                'This domain name does not exist under this dnspod account, adding resolution failed!')
        elif error.find('SERVFAIL looking up TXT for') != -1:
            return public.get_msg_gettext(
                'No valid TXT resolution record was found in the domain name {}, please check whether the TXT record is parsed correctly. If it is applied by DNSAPI, please try again in 10 minutes!',
                (str(re.findall("looking up TXT for (.+)", error)),))
        elif error.find('Timeout during connect') != -1:
            return public.get_msg_gettext(
                'The connection timed out and the CA server was unable to access your website!')
        elif error.find("DNS problem: SERVFAIL looking up CAA for") != -1:
            return public.get_msg_gettext(
                'Domain name {} is currently required to verify the CAA record, please parse the CAA record manually, or retry the application after 1 hour!',
                (str(re.findall("looking up CAA for (.+)", error)),))
        elif error.find("Read timed out.") != -1:
            return public.get_msg_gettext(
                'The verification timed out. Please check if the domain name is resolved correctly. If it is resolved correctly, the connection between the server and LetsEncrypt may be abnormal. Please try again later!')
        elif error.find('Cannot issue for') != -1:
            return public.get_msg_gettext(
                'Cannot issue a certificate for {}, cannot apply for a wildcard certificate with a domain name suffix directly!',
                (str(re.findall(r'for\s+"(.+)"', error)),))
        elif error.find('too many failed authorizations recently'):
            return public.get_msg_gettext(
                'The account has more than 5 failed orders within 1 hour, please wait 1 hour and try again!')
        elif error.find("Error creating new order") != -1:
            return public.get_msg_gettext('Order creation failed, please try again later!')
        elif error.find("Too Many Requests") != -1:
            return public.get_msg_gettext(
                'More than 5 verification failures in 1 hour, the application is temporarily banned, please try again later!')
        elif error.find('HTTP Error 400: Bad Request') != -1:
            return public.get_msg_gettext('CA server denied access, please try again later!')
        elif error.find('Temporary failure in name resolution') != -1:
            return public.get_msg_gettext(
                'The DNS of the server is faulty and the domain name cannot be resolved. Please use the Linux toolbox to check the DNS configuration')
        elif error.find('Too Many Requests') != -1:
            return public.get_msg_gettext('Too many requests for this domain name. Please try again 3 hours later')
        else:
            return error

    # 发送验证请求
    def respond_to_challenge(self, auth):
        payload = {"keyAuthorization": "{0}".format(
            auth['acme_keyauthorization'])}
        respond_to_challenge_response = self.acme_request(
            auth['dns_challenge_url'], payload)
        return respond_to_challenge_response

    # 发送CSR
    def send_csr(self, index):
        csr = self.create_csr(index)
        payload = {"csr": self.calculate_safe_base64(csr)}
        send_csr_response = self.acme_request(
            url=self._config['orders'][index]['finalize'], payload=payload)
        if send_csr_response.status_code not in [200, 201]:
            if send_csr_response.status_code == 0:
                raise ValueError(
                    "Error: [Connection reset by peer], the request process may be accidentally intercepted, if only this domain name cannot apply, then the domain name may be abnormal!")
            raise ValueError(
                "Error: Sending CSR: Response Status {status_code} Response:{response}".format(
                    status_code=send_csr_response.status_code,
                    response=send_csr_response.json(),
                )
            )
        send_csr_response_json = send_csr_response.json()
        certificate_url = send_csr_response_json["certificate"]
        self._config['orders'][index]['certificate_url'] = certificate_url
        self.save_config()
        return certificate_url

    # 获取证书到期时间
    def get_cert_timeout(self, cret_data):
        try:
            x509 = OpenSSL.crypto.load_certificate(
                OpenSSL.crypto.FILETYPE_PEM, cret_data)
            cert_timeout = bytes.decode(x509.get_notAfter())[:-1]
            return int(time.mktime(time.strptime(cert_timeout, '%Y%m%d%H%M%S')))
        except:
            return int(time.time() + (86400 * 90))

    # 下载证书
    def download_cert(self, index):
        res = self.acme_request(
            self._config['orders'][index]['certificate_url'], "")
        if res.status_code not in [200, 201]:
            raise Exception(public.get_msg_gettext('Failed to download certificate: {}', (str(res.json()),)))

        pem_certificate = res.content
        if type(pem_certificate) == bytes:
            pem_certificate = pem_certificate.decode('utf-8')
        cert = self.split_ca_data(pem_certificate)
        cert['cert_timeout'] = self.get_cert_timeout(cert['cert'])
        cert['private_key'] = self._config['orders'][index]['private_key']
        cert['domains'] = self._config['orders'][index]['domains']
        del(self._config['orders'][index]['private_key'])
        del(self._config['orders'][index]['auths'])
        del(self._config['orders'][index]['expires'])
        del(self._config['orders'][index]['authorizations'])
        del(self._config['orders'][index]['finalize'])
        del(self._config['orders'][index]['identifiers'])
        if 'cert' in self._config['orders'][index]:
            del(self._config['orders'][index]['cert'])
        self._config['orders'][index]['status'] = 'valid'
        self._config['orders'][index]['cert_timeout'] = cert['cert_timeout']
        domain_name = self._config['orders'][index]['domains'][0]
        self._config['orders'][index]['save_path'] = '{}/{}'.format(
            self._save_path, domain_name)
        cert['save_path'] = self._config['orders'][index]['save_path']
        self.save_config()
        self.save_cert(cert, index)
        return cert

    # 保存证书到文件
    def save_cert(self, cert, index):
        try:
            from ssl_manage import SSLManger
            SSLManger().save_by_data(cert['cert'] + cert['root'], cert['private_key'])

            domain_name = self._config['orders'][index]['domains'][0]
            path = self._config['orders'][index]['save_path']
            if not os.path.exists(path):
                os.makedirs(path, 384)

            # 存储证书
            key_file = path + "/privkey.pem"
            pem_file = path + "/fullchain.pem"
            public.writeFile(key_file, cert['private_key'])
            public.writeFile(pem_file, cert['cert'] + cert['root'])
            public.writeFile(path + "/cert.csr", cert['cert'])
            public.writeFile(path + "/root_cert.csr", cert['root'])

            # 转为IIS证书
            try:
                pfx_buffer = self.dump_pkcs12(
                    cert['private_key'], cert['cert'] + cert['root'], cert['root'], domain_name)
            except:
                import ssl_info
                pfx_buffer = ssl_info.ssl_info().dump_pkcs12_new(
                    cert['private_key'], cert['cert'] + cert['root'], cert['root'], domain_name)
            public.writeFile(path + "/fullchain.pfx", pfx_buffer, 'wb+')

            ps = '''Document description:
privkey.pem     Certificate private key
fullchain.pem   PEM format certificate with certificate chain (nginx/apache)
root_cert.csr   Root certificate
cert.csr        Domain name certificate
fullchain.pfx   Certificate format for IIS

How to use in the aaPanel:
privkey.pem         Paste into the key entry box
fullchain.pem       Paste into certificate input box
'''
            public.writeFile(path + '/Description.txt', ps)
            self.sub_all_cert(key_file, pem_file)
        except:
            write_log(public.get_error_info())

    # 通过域名获取网站名称
    def get_site_name_by_domains(self,domains):
        sql = public.M('domain')
        site_sql = public.M('sites')
        siteName, project_type = None, None
        for domain in domains:
            pid = sql.where('name=?',domain).getField('pid')
            if pid:
                site_data = site_sql.where('id=?', pid).field('name,project_type').find()
                siteName, project_type = site_data["name"], site_data["project_type"]
                break
        return siteName, project_type

    # 替换服务器上的同域名同品牌证书
    def sub_all_cert(self, key_file, pem_file):
        cert_init = self.get_cert_init(pem_file)  # 获取新证书的基本信息
        paths = ['/www/server/panel/vhost/cert', '/www/server/panel/vhost/ssl','/www/server/panel']
        is_panel = False
        for path in paths:
            if not os.path.exists(path):
                continue
            for p_name in os.listdir(path):
                to_path = path + '/' + p_name
                to_pem_file = to_path + '/fullchain.pem'
                to_key_file = to_path + '/privkey.pem'
                to_info = to_path + '/info.json'
                # 判断目标证书是否存在
                if not os.path.exists(to_pem_file):
                    if not p_name in ['ssl']: continue
                    to_pem_file = to_path + '/certificate.pem'
                    to_key_file = to_path + '/privateKey.pem'
                    if not os.path.exists(to_pem_file):
                        continue
                # 获取目标证书的基本信息
                to_cert_init = self.get_cert_init(to_pem_file)
                # 判断证书品牌是否一致
                try:
                    if to_cert_init['issuer'] != cert_init['issuer'] and to_cert_init['issuer'].find("Let's Encrypt") == -1 and to_cert_init['issuer'] != 'R3':
                        continue
                except: continue
                # 判断目标证书的到期时间是否较早
                if to_cert_init['notAfter'] > cert_init['notAfter']:
                    continue
                # 判断认识名称是否一致
                if len(to_cert_init['dns']) != len(cert_init['dns']):
                    continue
                is_copy = True
                for domain in to_cert_init['dns']:
                    if not domain in cert_init['dns']:
                        is_copy = False
                if not is_copy:
                    continue

                # 替换新的证书文件和基本信息
                public.writeFile(
                    to_pem_file, public.readFile(pem_file, 'rb'), 'wb')
                public.writeFile(
                    to_key_file, public.readFile(key_file, 'rb'), 'wb')
                public.writeFile(to_info, json.dumps(cert_init))
                write_log(public.get_msg_gettext(
                    '|-Detected that the certificate under {} overlaps with the certificate of this application and has an earlier expiration time, and has been replaced with a new certificate!',
                    (to_path,)))
                if path == paths[-1]: is_panel = True

        # 重载web服务
        public.serviceReload()
        # if is_panel: public.restart_panel()

    # 检查指定证书是否在订单列表
    def check_order_exists(self, pem_file):
        try:
            cert_init = self.get_cert_init(pem_file)
            if not cert_init:
                return None
            if not (cert_init['issuer'].find("Let's Encrypt") != -1 or cert_init['issuer'] == 'R3'):
                return None
            for index in self._config['orders'].keys():
                if not 'save_path' in self._config['orders'][index]:
                    continue
                for domain in self._config['orders'][index]['domains']:
                    if domain in cert_init['dns']:
                        return index
            return pem_file
        except:
            return None

    # 取证书基本信息API
    def get_cert_init_api(self, args):
        if not os.path.exists(args.pem_file):
            args.pem_file = 'vhost/cert/{}/fullchain.pem'.format(args.siteName)
            if not os.path.exists(args.pem_file):
                return public.return_msg_gettext(False, 'The specified certificate file does not exist!')
        cert_init = self.get_cert_init(args.pem_file)
        if not cert_init:
            return public.return_msg_gettext(False, 'Certificate information acquisition failed!')
        try:
            cert_init['dnsapi'] = json.loads(public.readFile(self._dnsapi_file))
        except:
            cert_init['dnsapi'] = []
        return cert_init

    # 获取指定证书基本信息
    def get_cert_init(self, pem_file):
        if not os.path.exists(pem_file):
            return None
        try:
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
                result['subject'] = result['dns'][0]
            return result
        except: return None

    # 转换时间
    def strf_date(self, sdate):
        return time.strftime('%Y-%m-%d', time.strptime(sdate, '%Y%m%d%H%M%S'))

    # 证书转为DER
    def dump_der(self, cert_path):
        cert = OpenSSL.crypto.load_certificate(
            OpenSSL.crypto.FILETYPE_PEM, public.readFile(cert_path+'/cert.csr'))
        return OpenSSL.crypto.dump_certificate(OpenSSL.crypto.FILETYPE_ASN1, cert)

    # 证书转为pkcs12
    def dump_pkcs12(self, key_pem=None, cert_pem=None, ca_pem=None, friendly_name=None):
        # from cryptography.hazmat.primitives.serialization import pkcs12

        p12 = OpenSSL.crypto.PKCS12()
        if cert_pem:
            p12.set_certificate(OpenSSL.crypto.load_certificate(
                OpenSSL.crypto.FILETYPE_PEM, cert_pem.encode()))
        if key_pem:
            p12.set_privatekey(OpenSSL.crypto.load_privatekey(
                OpenSSL.crypto.FILETYPE_PEM, key_pem.encode()))
        if ca_pem:
            p12.set_ca_certificates((OpenSSL.crypto.load_certificate(
                OpenSSL.crypto.FILETYPE_PEM, ca_pem.encode()),))
        if friendly_name:
            p12.set_friendlyname(friendly_name.encode())
        return p12.export()

    # 拆分根证书
    def split_ca_data(self,cert):
        sp_key = '-----END CERTIFICATE-----\n'
        datas = cert.split(sp_key)
        return {"cert": datas[0] + sp_key, "root": sp_key.join(datas[1:])}

    # 构造可选名称
    def get_alt_names(self, index):
        domain_name = self._config['orders'][index]['domains'][0]
        domain_alt_names = []
        if len(self._config['orders'][index]['domains']) > 1:
            domain_alt_names = self._config['orders'][index]['domains'][1:]
        return domain_name, domain_alt_names

    # 检查DNS记录
    def check_dns(self, domain, value, s_type='TXT'):
        write_log(public.get_msg_gettext(
            '|-Attempt to verify DNS records locally, domain name: {}, type: {} record value: {}',
            (domain, s_type, value)))
        time.sleep(10)
        n = 0
        while n < 20:
            n += 1
            try:
                import dns.resolver
                ns = dns.resolver.query(domain, s_type)
                for j in ns.response.answer:
                    for i in j.items:
                        txt_value = i.to_text().replace('"', '').strip()
                        write_log(
                            public.get_msg_gettext('|-Number of verifications: {}, value: {}', (str(n), txt_value)))
                        if txt_value == value:
                            write_log(public.get_msg_gettext('|-Local authentication succeeded!'))
                            return True
            except:
                try:
                    import dns.resolver
                except:
                    return False
            time.sleep(3)
        write_log(public.get_msg_gettext('|-Local authentication failed!'))
        return True

    # 创建CSR
    def create_csr(self, index):
        if 'csr' in self._config['orders'][index]:
            return self._config['orders']['csr']
        domain_name, domain_alt_names = self.get_alt_names(index)
        X509Req = OpenSSL.crypto.X509Req()
        X509Req.get_subject().CN = domain_name
        if domain_alt_names:
            SAN = "DNS:{0}, ".format(domain_name).encode("utf8") + ", ".join(
                "DNS:" + i for i in domain_alt_names
            ).encode("utf8")
        else:
            SAN = "DNS:{0}".format(domain_name).encode("utf8")

        X509Req.add_extensions(
            [
                OpenSSL.crypto.X509Extension(
                    "subjectAltName".encode("utf8"), critical=False, value=SAN
                )
            ]
        )
        pk = OpenSSL.crypto.load_privatekey(
            OpenSSL.crypto.FILETYPE_PEM, self.create_certificate_key(
                index).encode()
        )
        X509Req.set_pubkey(pk)
        try:
            X509Req.set_version(2)
        except ValueError as e:  # pyOpenSSL 新版本需要必须设置版本为0
            X509Req.set_version(0)
        X509Req.sign(pk, self._digest)
        return OpenSSL.crypto.dump_certificate_request(OpenSSL.crypto.FILETYPE_ASN1, X509Req)

    # 构造域名验证头和验证值
    def get_keyauthorization(self, token):
        acme_header_jwk_json = json.dumps(
            self.get_acme_header("GET_THUMBPRINT")["jwk"], sort_keys=True, separators=(",", ":")
        )
        acme_thumbprint = self.calculate_safe_base64(
            hashlib.sha256(acme_header_jwk_json.encode("utf8")).digest()
        )
        acme_keyauthorization = "{0}.{1}".format(token, acme_thumbprint)
        base64_of_acme_keyauthorization = self.calculate_safe_base64(
            hashlib.sha256(acme_keyauthorization.encode("utf8")).digest()
        )

        return acme_keyauthorization, base64_of_acme_keyauthorization

    # 构造验证信息
    def get_identifier_auth(self, index, url, auth_info):
        s_type = self.get_auth_type(index)
        write_log(public.get_msg_gettext('|-Verification type: {}', (s_type,)))
        domain = auth_info['identifier']['value']
        wildcard = False
        # 处理通配符
        if 'wildcard' in auth_info:
            wildcard = auth_info['wildcard']
        if wildcard:
            domain = "*." + domain

        for auth in auth_info['challenges']:
            if auth['type'] != s_type:
                continue
            identifier_auth = {
                "domain": domain,
                "url": url,
                "wildcard": wildcard,
                "token": auth['token'],
                "dns_challenge_url": auth['url'],
            }
            return identifier_auth
        return None

    # 获取域名验证方式
    def get_auth_type(self, index):
        if not index in self._config['orders']:
            raise Exception(public.get_msg_gettext('The specified order does not exist!'))
        s_type = 'http-01'
        if 'auth_type' in self._config['orders'][index]:
            if self._config['orders'][index]['auth_type'] == 'dns':
                s_type = 'dns-01'
            elif self._config['orders'][index]['auth_type'] == 'tls':
                s_type = 'tls-alpn-01'
            else:
                s_type = 'http-01'
        return s_type

    # 保存订单
    def save_order(self, order_object, index):
        if not 'orders' in self._config:
            self._config['orders'] = {}
        renew = False
        if not index:
            index = public.md5(json.dumps(order_object['identifiers']))
        else:
            renew = True
            order_object['certificate_url'] = self._config['orders'][index]['certificate_url']
            order_object['save_path'] = self._config['orders'][index]['save_path']

        order_object['expires'] = self.utc_to_time(order_object['expires'])
        self._config['orders'][index] = order_object
        self._config['orders'][index]['index'] = index
        if not renew:
            self._config['orders'][index]['create_time'] = int(time.time())
            self._config['orders'][index]['renew_time'] = 0
        self.save_config()
        return index

    # UTC时间转时间戳
    def utc_to_time(self, utc_string):
        try:
            utc_string = utc_string.split('.')[0]
            utc_date = datetime.datetime.strptime(
                utc_string, "%Y-%m-%dT%H:%M:%S")
            # 按北京时间返回
            return int(time.mktime(utc_date.timetuple())) + (3600 * 8)
        except:
            return int(time.time() + 86400 * 7)

    # 获取kid
    def get_kid(self, force=False):
        #如果配置文件中不存在kid或force = True时则重新注册新的acme帐户
        if not 'account' in self._config:
            self._config['account'] = {}
        k = self._mod_index[self._debug]
        if not k in self._config['account']:
            self._config['account'][k] = {}

        if not 'kid' in self._config['account'][k]:
            self._config['account'][k]['kid'] = self.register()
            self.save_config()
            time.sleep(3)
            self._config = self.read_config()
        return self._config['account'][k]['kid']

    # 注册acme帐户
    def register(self, existing=False):
        if not 'email' in self._config:
            self._config['email'] = 'demo@aapanel.com'
        if existing:
            payload = {"onlyReturnExisting": True}
        elif self._config['email']:
            payload = {
                "termsOfServiceAgreed": True,
                "contact": ["mailto:{0}".format(self._config['email'])],
            }
        else:
            payload = {"termsOfServiceAgreed": True}

        res = self.acme_request(url=self._apis['newAccount'], payload=payload)

        if res.status_code not in [201, 200, 409]:
            raise Exception(public.get_msg_gettext('Registration for ACME account failed: {}', (str(res.json()),)))
        kid = res.headers["Location"]
        return kid

    # 请求到ACME接口
    def acme_request(self, url, payload):
        headers = {"User-Agent": self._user_agent}
        payload = self.stringfy_items(payload)

        if payload == "":
            payload64 = payload
        else:
            payload64 = self.calculate_safe_base64(json.dumps(payload))
        protected = self.get_acme_header(url)
        protected64 = self.calculate_safe_base64(json.dumps(protected))
        signature = self.sign_message(
            message="{0}.{1}".format(protected64, payload64))  # bytes
        signature64 = self.calculate_safe_base64(signature)  # str
        data = json.dumps(
            {"protected": protected64, "payload": payload64,
                "signature": signature64}
        )
        headers.update({"Content-Type": "application/jose+json"})
        response = requests.post(
            url, data=data.encode("utf8"), timeout=self._acme_timeout, headers=headers, verify=self._verify,s_type=self._request_type
        )
        # 更新随机数
        self.update_replay_nonce(response)
        return response

    # 计算signature
    def sign_message(self, message):
        pk = OpenSSL.crypto.load_privatekey(
            OpenSSL.crypto.FILETYPE_PEM, self.get_account_key().encode())
        return OpenSSL.crypto.sign(pk, message.encode("utf8"), self._digest)

    # 系列化payload
    def stringfy_items(self, payload):
        if isinstance(payload, str):
            return payload

        for k, v in payload.items():
            if isinstance(k, bytes):
                k = k.decode("utf-8")
            if isinstance(v, bytes):
                v = v.decode("utf-8")
            payload[k] = v
        return payload

    # 获取随机数
    def get_nonce(self, force=False):
        # 如果没有保存上一次的随机数或force=True时则重新获取新的随机数
        if not self._replay_nonce or force:
            headers = {"User-Agent": self._user_agent}
            response = requests.get(
                self._apis['newNonce'],
                timeout=self._acme_timeout,
                headers=headers,
                verify=self._verify,
                s_type=self._request_type
            )
            self._replay_nonce = response.headers["Replay-Nonce"]
        return self._replay_nonce

    # 获请ACME请求头
    def get_acme_header(self, url):
        header = {"alg": "RS256", "nonce": self.get_nonce(), "url": url}
        if url in [self._apis['newAccount'], 'GET_THUMBPRINT']:
            from cryptography.hazmat.backends import default_backend
            from cryptography.hazmat.primitives import serialization
            private_key = serialization.load_pem_private_key(
                self.get_account_key().encode(),
                password=None,
                backend=default_backend(),
            )
            public_key_public_numbers = private_key.public_key().public_numbers()

            exponent = "{0:x}".format(public_key_public_numbers.e)
            exponent = "0{0}".format(exponent) if len(
                exponent) % 2 else exponent
            modulus = "{0:x}".format(public_key_public_numbers.n)
            jwk = {
                "kty": "RSA",
                "e": self.calculate_safe_base64(binascii.unhexlify(exponent)),
                "n": self.calculate_safe_base64(binascii.unhexlify(modulus)),
            }
            header["jwk"] = jwk
        else:
            header["kid"] = self.get_kid()
        return header

    # 转为无填充的Base64
    def calculate_safe_base64(self, un_encoded_data):
        if sys.version_info[0] == 3:
            if isinstance(un_encoded_data, str):
                un_encoded_data = un_encoded_data.encode("utf8")
        r = base64.urlsafe_b64encode(un_encoded_data).rstrip(b"=")
        return r.decode("utf8")

    # 获用户取密钥对
    def get_account_key(self):
        if not 'account' in self._config:
            self._config['account'] = {}
        k = self._mod_index[self._debug]
        if not k in self._config['account']:
            self._config['account'][k] = {}

        if not 'key' in self._config['account'][k]:
            self._config['account'][k]['key'] = self.create_key()
            if type(self._config['account'][k]['key']) == bytes:
                self._config['account'][k]['key'] = self._config['account'][k]['key'].decode()
            self.save_config()
        return self._config['account'][k]['key']

    # 获取证书密钥对
    def create_certificate_key(self, index):
        # 判断是否已经创建private_key
        if 'private_key' in self._config['orders'][index]:
            return self._config['orders'][index]['private_key']
        # 创建新的私钥
        private_key = self.create_key()
        if type(private_key) == bytes:
            private_key = private_key.decode()
        # 保存私钥到订单配置文件
        self._config['orders'][index]['private_key'] = private_key
        self.save_config()
        return private_key

    # 创建Key
    def create_key(self, key_type=OpenSSL.crypto.TYPE_RSA):
        key = OpenSSL.crypto.PKey()
        key.generate_key(key_type, self._bits)
        private_key = OpenSSL.crypto.dump_privatekey(
            OpenSSL.crypto.FILETYPE_PEM, key)
        return private_key

    # 写配置文件
    def save_config(self):
        fp = open(self._conf_file_v2, 'w+')
        fcntl.flock(fp, fcntl.LOCK_EX)  # 加锁
        fp.write(json.dumps(self._config))
        fcntl.flock(fp, fcntl.LOCK_UN)  # 解锁
        fp.close()
        return True

    # 读配置文件
    def read_config(self):
        if not os.path.exists(self._conf_file_v2):
            self._config['orders'] = {}
            self._config['account'] = {}
            self._config['apis'] = {}
            self._config['email'] = public.M('config').where('id=?',(1,)).getField('email')
            if self._config['email'] in [public.en_hexb('4d6a67334f5459794e545932514846784c6d4e7662513d3d')]:
                self._config['email'] = None
            self.save_config()
            return self._config
        tmp_config = public.readFile(self._conf_file_v2)
        if not tmp_config:
            return self._config
        try:
            self._config = json.loads(tmp_config)
        except:
            self.save_config()
            return self._config
        return self._config

    # 申请证书
    def apply_cert(self, domains, auth_type='dns', auth_to='Dns_com|None|None', **args):
        write_log("", "wb+")
        try:
            self.get_apis()
            index = None
            if 'index' in args:
                index = args['index']
            if not index:  # 判断是否只想验证域名
                write_log(public.get_msg_gettext('|-Creating order..'))
                index = self.create_order(domains, auth_type, auth_to)
                write_log(public.get_msg_gettext('|-Getting verification information..'))
                self.get_auths(index)
                if auth_to == 'dns' and len(self._config['orders'][index]['auths']) > 0:
                    return self._config['orders'][index]
            write_log(public.get_msg_gettext('|-Verifying domain name..'))
            self.auth_domain(index)
            self.remove_dns_record()
            write_log(public.get_msg_gettext('|-Sending CSR..'))
            self.send_csr(index)
            write_log(public.get_msg_gettext('|-Downloading certificate..'))
            cert = self.download_cert(index)
            cert['status'] = True
            cert['msg'] = public.get_msg_gettext('Application successful!')
            write_log(public.get_msg_gettext('|-Successful application, deploying to site..'))
            return cert
        except Exception as ex:
            self.remove_dns_record()
            ex = str(ex)
            if ex.find(">>>>") != -1:
                msg = ex.split(">>>>")
                msg[1] = json.loads(msg[1])
            else:
                msg = ex
                write_log(public.get_error_info())
            return public.return_msg_gettext(False, msg)

    # 申请证书 - api
    def apply_cert_api(self, args):
        """
        @name 申请证书
        @param domains: list 域名列表
        @param auth_type: str 认证方式
        @param auth_to: str 认证路径
        @param auto_wildcard: str 是否自动组合泛域名
        """
        if not 'id' in args:
            return public.return_msg_gettext(False,'Website ID cannot be empty!')

        if 'auto_wildcard' in args and args.auto_wildcard == '1':
            self._auto_wildcard = True

        find = public.M('sites').where('id=?', (args.id,)).find()
        if not find:
            return public.return_msg_gettext(False, "Website lost, unable to continue applying for certificate")

        if args.auth_type in ['http', 'tls']:
            if not self.can_use_base_file_check(find["name"], find["project_type"]):
                webserver: str = public.get_webserver()
                msg = "The service ({}) configuration file of the current project has been modified and does not support file verification. Please choose another method or restore the configuration file".format(webserver.title())
                if webserver != 'nginx':
                    return public.return_msg_gettext(False, msg)
                # nginx 检测其他两种方案的可行性
                if not self.can_use_lua_for_site(find["name"], find["project_type"]) and \
                        not self.can_use_if_for_file_check(find["name"], find["project_type"]):

                    return public.return_msg_gettext(False, msg)
        else:
            return self.apply_cert(json.loads(args.domains), args.auth_type, args.auth_to)

        # 是否为指定站点
        count = public.M('sites').where(
            'id=? and project_type in (?,?,?,?)',
            (args.id, 'Java', 'Go', 'Other', "Python")
        ).count()
        if count:
            try:
                project_info = json.loads(find['project_config'])
                if 'ssl_path' not in project_info:
                    ssl_path = '/www/wwwroot/java_node_ssl'
                else:
                    ssl_path = project_info['ssl_path']
                if not os.path.exists(ssl_path):
                    os.makedirs(ssl_path)

                args.auth_to = ssl_path
            except:
                return public.return_msg_gettext(False, 'There is an issue with the current project configuration file, please rebuild it')
        else:
            if re.match(r"^\d+$", args.auth_to):
                import panelSite
                args.auth_to = find['path'] + '/' + panelSite.panelSite().GetRunPath(args)
                args.auth_to = args.auth_to.replace("//", "/")
                if args.auth_to[-1] == '/':
                    args.auth_to = args.auth_to[:-1]

                if not os.path.exists(args.auth_to):
                    return public.return_msg_gettext(False, 'Invalid site directory, please check if the specified site exists!')
        try:
            # 检查认证环境
            check_result = self.check_auth_env(args)
            if check_result:
                return check_result

            return self.apply_cert(json.loads(args.domains), args.auth_type, args.auth_to)
        except:
            pass
        finally:
            self.turnon_redirect_proxy_httptohttps(args)


    def turnon_redirect_proxy_httptohttps(self, args):
        import panelSite
        s = panelSite.panelSite()
        if not 'siteName' in args:
            args.siteName = public.M('sites').where('id=?', (args.id,)).getField('name')
        args.sitename = args.siteName
        self.turnon_redirect(args, s)
        self.turnon_proxy(args, s)
        self.turnon_httptohttps(args, s)
        public.serviceReload()

    def turnon_httptohttps(self, args, s):
        conf_file = '{}/data/stop_httptohttps.pl'.format(public.get_panel_path())
        if os.path.exists(conf_file):
            write_log('|-Turning on http to https')
            s.HttpToHttps(args)
            try:
                os.remove(conf_file)
            except:
                pass

    def turnon_proxy(self, args, s):
        conf_file = '{}/data/stop_p_tmp.pl'.format(public.get_panel_path())
        if not os.path.exists(conf_file):
            return
        write_log('|-Turning on proxy')
        conf = json.loads(public.readFile(conf_file))
        data = s.GetProxyList(args)
        for x in data:
            if x['sitename'] not in conf:
                continue
            if x['proxyname'] not in conf[x['sitename']]:
                continue
            args.type = 1
            args.advanced = x['advanced']
            args.cache = x['cache']
            args.cachetime = x['cachetime']
            args.proxydir = x['proxydir']
            args.proxyname = x['proxyname']
            args.proxysite = x['proxysite']
            args.sitename = x['sitename']
            args.subfilter = json.dumps(x['subfilter'])
            args.todomain = x['todomain']
            s.ModifyProxy(args)
        try:
            os.remove(conf_file)
        except:
            pass

    def turnon_redirect(self, args, s):
        conf_file = '{}/data/stop_r_tmp.pl'.format(public.get_panel_path())
        if not os.path.exists(conf_file):
            return
        write_log('|-Turning on redirection')
        conf = json.loads(public.readFile(conf_file))
        data = s.GetRedirectList(args)
        for x in data:
            if x['sitename'] not in conf:
                continue
            if x['redirectname'] not in conf[x['sitename']]:
                continue
            args.type = 1
            args.sitename = x['sitename']
            args.holdpath = x['holdpath']
            args.redirectname = x['redirectname']
            args.redirecttype = x['redirecttype']
            args.domainorpath = x['domainorpath']
            args.redirectpath = x['redirectpath']
            args.redirectdomain = json.dumps(x['redirectdomain'])
            args.tourl = x['tourl']
            s.ModifyRedirect(args)
        try:
            os.remove(conf_file)
        except:
            pass

    # 检查认证环境
    def check_auth_env(self, args, check=None):
        if not check:
            return
        for domain in json.loads(args.domains):
            if public.checkIp(domain): continue
            if domain.find('*.') != -1 and args.auth_type in ['http', 'tls']:
                raise public.return_msg_gettext(False,
                                                'Pan domain names cannot apply for a certificate using [File Verification]!')
        import panelSite
        s = panelSite.panelSite()
        if args.auth_type in ['http', 'tls']:
            try:
                rp_conf = public.readFile(self._stop_rp_file)
                try:
                    if rp_conf:
                        rp_conf = json.loads(rp_conf)
                except:
                    write_log('|-Failed to parse configuration file')
                if not 'siteName' in args:
                    args.siteName = public.M('sites').where('id=?', (args.id,)).getField('name')
                args.sitename = args.siteName
                data = s.GetRedirectList(args)
                # 检查重定向是否开启
                if type(data) == list:
                    redirect_tmp = {args.sitename: []}
                    for x in data:
                        if rp_conf and x['sitename'] in rp_conf:
                            if str(x['type']) == '0':
                                continue
                            args.type = 0
                            args.sitename = x['sitename']
                            args.holdpath = x['holdpath']
                            args.redirectname = x['redirectname']
                            args.redirecttype = x['redirecttype']
                            args.domainorpath = x['domainorpath']
                            args.redirectpath = x['redirectpath']
                            args.redirectdomain = json.dumps(x['redirectdomain'])
                            args.tourl = x['tourl']
                            args.notreload = True
                            write_log("|- Turning off redirection {}".format(args.redirectname))
                            s.ModifyRedirect(args)
                            redirect_tmp[args.sitename].append(x['redirectname'])
                        else:
                            if x['type']: return public.return_msg_gettext(False,
                                                                           'Your site has 301 Redirect on，Please turn it off first!')
                    if redirect_tmp[args.sitename]:
                        public.writeFile('{}/data/stop_r_tmp.pl'.format(public.get_panel_path()),
                                         json.dumps(redirect_tmp))
                data = s.GetProxyList(args)
                # 检查反向代理是否开启
                if type(data) == list:
                    proxy_tmp = {args.sitename: []}
                    for x in data:
                        if rp_conf and x['sitename'] in rp_conf:
                            if str(x['type']) == '0':
                                continue
                            args.type = 0
                            args.advanced = x['advanced']
                            args.cache = x['cache']
                            args.cachetime = x['cachetime']
                            args.proxydir = x['proxydir']
                            args.proxyname = x['proxyname']
                            args.proxysite = x['proxysite']
                            args.sitename = x['sitename']
                            args.subfilter = json.dumps(x['subfilter'])
                            args.todomain = x['todomain']
                            args.notreload = True
                            s.ModifyProxy(args)
                            write_log("|- Turning off proxy {}".format(args.proxyname))
                            proxy_tmp[args.sitename].append(x['proxyname'])
                        else:
                            if x['type']: return public.return_msg_gettext(False,
                                                                           'Sites with reverse proxy turned on cannot apply for SSL!')
                    if proxy_tmp[args.sitename]:
                        public.writeFile('{}/data/stop_p_tmp.pl'.format(public.get_panel_path()), json.dumps(proxy_tmp))
                # 检查旧重定向是否开启
                data = s.Get301Status(args)
                if data['status']:
                    return public.return_msg_gettext(False,
                                                     'The website has been redirected, please close it before applying!')
                # 判断是否强制HTTPS
                if s.IsToHttps(args.siteName):
                    if os.path.exists(self._stop_rp_file):
                        if rp_conf and args.siteName in rp_conf:
                            write_log("|- Turning off http to https")
                            s.CloseToHttps(args)
                        public.writeFile('{}/data/stop_httptohttps.pl'.format(public.get_panel_path()), '')
                    else:
                        return public.return_msg_gettext(False,
                                                         'After configuring Force HTTPS, you cannot use [File Verification] to apply for a certificate!')
                public.serviceReload()
            except:
                return False
        else:
            if args.auth_to.find('Dns_com') != -1:
                if not os.path.exists('plugin/dns/dns_main.py'):
                    return public.return_msg_gettext(False,
                                                     'Please go to the software store to install [cloud analysis], and complete the domain name NS binding.')
        return False

    # DNS手动验证
    def apply_dns_auth(self, args):
        if not hasattr(args, "index") or not args.index:
            return public.return_msg_gettext(False, "Incomplete parameter information, no index parameter [index]")
        return self.apply_cert([], auth_type='dns', auth_to='dns', index=args.index)


    #创建计划任务
    def set_crond(self):
        try:
            echo = public.md5(public.md5('renew_lets_ssl_bt'))
            find = public.M('crontab').where('echo=?',(echo,)).find()
            cron_id = find['id'] if find else None

            import crontab
            import random
            args_obj = public.dict_obj()
            if not cron_id:
                cronPath = public.GetConfigValue('setup_path') + '/cron/' + echo
                shell = '{} -u /www/server/panel/class/acme_v2.py --renew=1'.format(sys.executable)
                public.writeFile(cronPath,shell)

                # 使用随机时间
                hour = random.randint(0, 23)
                minute = random.randint(1, 59)
                args_obj.id = public.M('crontab').add('name,type,where1,where_hour,where_minute,echo,addtime,status,save,backupTo,sType,sName,sBody,urladdress',("Renew Let's Encrypt Certificate",'day','',hour,minute,echo,time.strftime('%Y-%m-%d %X',time.localtime()),0,'','localhost','toShell','',shell,''))
                crontab.crontab().set_cron_status(args_obj)
            else:
                # 检查任务如果是0点10分执行，改为随机时间
                if find['where_hour'] == 0 and find['where_minute'] == 10:
                    # print('修改任务时间')
                    # 使用随机时间
                    hour = random.randint(0, 23)
                    minute = random.randint(1, 59)
                    public.M('crontab').where('id=?',(cron_id,)).save('where_hour,where_minute,status',(hour,minute,0))

                    # 停用任务
                    args_obj.id = cron_id
                    crontab.crontab().set_cron_status(args_obj)

                    # 启用任务
                    public.M('crontab').where('id=?',(cron_id,)).setField('status',1)
                    crontab.crontab().set_cron_status(args_obj)

                cron_path = public.get_cron_path()
                if os.path.exists(cron_path):
                    cron_s = public.readFile(cron_path)
                    if cron_s.find(echo) == -1:
                        public.M('crontab').where('id=?',(cron_id,)).setField('status',0)
                        args_obj.id = cron_id
                        crontab.crontab().set_cron_status(args_obj)
        except:pass


    # 获取当前正在使用此证书的网站目录
    def get_ssl_used_site(self,save_path):
        pkey_file =  '{}/privkey.pem'.format(save_path)
        pkey = public.readFile(pkey_file)
        if not pkey: return False
        cert_paths = 'vhost/cert'
        import panelSite
        args = public.dict_obj()
        args.siteName = ''
        for c_name in os.listdir(cert_paths):
            skey_file = '{}/{}/privkey.pem'.format(cert_paths,c_name)
            skey = public.readFile(skey_file)
            if not skey: continue
            if skey == pkey or 1==1:
                args.siteName = c_name
                site_info = public.M('sites').where('name=?', c_name).find()
                if not site_info or isinstance(site_info, str):
                    return False
                if site_info["project_type"] not in ("PHP", "proxy"):
                    if not os.path.isdir(site_info["path"]):
                        return os.path.dirname(site_info["path"])
                    else:
                        return site_info["path"]

                run_path = panelSite.panelSite().GetRunPath(args)
                if not run_path:
                    continue
                sitePath = public.M('sites').where('name=?',c_name).getField('path')
                if not sitePath:
                    continue
                to_path = "{}/{}".format(sitePath,run_path)
                to_path = to_path.replace("//", "/")
                return to_path
        return False


    def get_site_id(self, domains):
        site_ids = []
        for domain in domains:
            if '*' in domain:
                continue
            site_id = public.M('domain').where('name=?', (domain,)).field('pid').select()
            if not site_id:
                continue
            site_ids.append(site_id[0]['pid'])
        if not site_ids:
            return False
        site_ids = list(set(site_ids))
        if not len(site_ids) == 1:
            return False
        return site_ids[0]

    def find_site_stopped(self, domains):
        site_id = self.get_site_id(domains)
        if not site_id:
            return False
        site_status = public.M('sites').where('id=?', (site_id,)).field('status').select()[0]['status']
        return site_status
    def get_index(self,domains):
        '''
            @name 获取标识
            @author hwliang<2022-02-10>
            @param domains<list> 域名列表
            @return string
        '''
        identifiers = []
        for domain_name in domains:
            identifiers.append({"type": 'dns', "value": domain_name})
        return public.md5(json.dumps(identifiers))


    # 续签同品牌其它证书
    def renew_cert_other(self):
        '''
            @name 续签同品牌其它证书
            @author hwliang<2022-02-10>
            @return void
        '''
        cert_path = "{}/vhost/cert".format(public.get_panel_path())
        if not os.path.exists(cert_path): return
        new_time = time.time() + (86400 * 30)
        n=0
        if not 'orders' in self._config: self._config['orders'] = {}
        import panelSite
        siteObj = panelSite.panelSite()
        args = public.dict_obj()
        for siteName in os.listdir(cert_path):
            try:
                cert_file = '{}/{}/fullchain.pem'.format(cert_path,siteName)
                if not os.path.exists(cert_file): continue # 无证书文件
                siteInfo = public.M('sites').where('name=?',siteName).find()
                if not siteInfo: continue # 无网站信息
                cert_init = self.get_cert_init(cert_file)
                if not cert_init: continue # 无法获取证书
                end_time = time.mktime(time.strptime(cert_init['notAfter'],'%Y-%m-%d'))
                if end_time > new_time: continue # 未到期
                try:
                    if not cert_init['issuer'] in ['R3',"Let's Encrypt"] and cert_init['issuer'].find("Let's Encrypt") == -1:
                        continue # 非同品牌证书
                except: continue

                if isinstance(cert_init['dns'],str): cert_init['dns'] = [cert_init['dns']]
                index = self.get_index(cert_init['dns'])
                if index in self._config['orders'].keys(): continue # 已在订单列表

                n+=1
                write_log("|-Renewing additional certificate {}, domain name:{}..".format(n, cert_init['subject']))
                write_log("|-Creating order..")
                args.id = siteInfo['id']
                runPath = siteObj.GetRunPath(args)
                if runPath and not runPath in ['/']:
                    path = siteInfo['path'] + '/' + runPath
                else:
                    path = siteInfo['path']

                self.renew_cert_to(cert_init['dns'],'http',path.replace('//','/'))
            except:
               write_log("|-Renewal failed:")

    # 关闭强制https
    def close_httptohttps(self,siteName):
        try:

            if not siteName: siteName
            import panelSite
            site_obj = panelSite.panelSite()
            if not site_obj.IsToHttps(siteName):
                return False
            get = public.dict_obj()
            get.siteName = siteName
            site_obj.CloseToHttps(get)
            return True
        except:
            return False

    # 恢复强制https
    def rep_httptohttps(self,siteName):
        try:
            if not siteName: return False
            import panelSite
            site_obj = panelSite.panelSite()
            if not site_obj.IsToHttps(siteName):
                get = public.dict_obj()
                get.siteName = siteName
                site_obj.HttpToHttps(get)
            return True
        except:
            return False


    def renew_cert_to(self,domains,auth_type,auth_to,index = None):
        siteName = None
        cert = {}
        if os.path.exists(auth_to):
            if public.M('sites').where('path=?',auth_to).count() == 1:
                site_id = public.M('sites').where('path=?',auth_to).getField('id')
                siteName = public.M('sites').where('path=?',auth_to).getField('name')
                import panelSite
                siteObj = panelSite.panelSite()
                args = public.dict_obj()
                args.id = site_id
                runPath = siteObj.GetRunPath(args)
                if runPath and not runPath in ['/']:
                    path = auth_to + '/' + runPath
                    if os.path.exists(path): auth_to = path.replace('//','/')

            else:
                siteName, _ = self.get_site_name_by_domains(domains)

            isError = public.checkWebConfig()
            if isError is not True and public.get_webserver() == "nginx":
                write_log("|- The certificate uses the file verification method, but currently it cannot overload the nginx server configuration file and can only skip renewal.")
                write_log("|- The error message in the configuration file is as follows:")
                write_log(isError)

        is_rep = self.close_httptohttps(siteName)
        try:
            index = self.create_order(
                domains,
                auth_type,
                auth_to.replace('//','/'),
                index
            )

            write_log("|-Getting verification information..")
            self.get_auths(index)
            write_log("|-Verifying domain name..")
            self.auth_domain(index)
            write_log("|-Sending CSR..")
            self.remove_dns_record()
            self.send_csr(index)
            write_log("|-Downloading certificate..")
            cert = self.download_cert(index)
            self._config['orders'][index]['renew_time'] = int(time.time())

            # 清理失败重试记录
            self._config['orders'][index]['retry_count'] = 0
            self._config['orders'][index]['next_retry_time'] = 0

            # 保存证书配置
            self.save_config()
            cert['status'] = True
            cert['msg'] = 'Renewed successfully!'
            write_log("|-Renewed successfully!!")
        except Exception as e:

            if str(e).find('please try again later') == -1:  # 受其它证书影响和连接CA失败的的不记录重试次数
                if index:
                    # 设置下次重试时间
                    self._config['orders'][index]['next_retry_time'] = int(time.time() + (86400 * 2))
                    # 记录重试次数
                    if not 'retry_count' in self._config['orders'][index].keys():
                        self._config['orders'][index]['retry_count'] = 1
                    self._config['orders'][index]['retry_count'] += 1
                    # 保存证书配置
                    self.save_config()
            msg = str(e).split('>>>>')[0]
            write_log("|-" + msg)
            return public.returnMsg(False, msg)
        finally:
            if is_rep: self.rep_httptohttps(siteName)
        write_log("-" * 70)
        return cert


    # 续签证书
    def renew_cert(self, index):
        write_log("", "wb+")
        try:
            order_index = []
            if index:
                if type(index) != str:
                    index = index.index
                if not index in self._config['orders']:
                    raise Exception(
                        public.get_msg_gettext('The specified order number does not exist and cannot be renewed!'))
                order_index.append(index)
            else:
                s_time = time.time() + (30 * 86400)
                if not 'orders' in self._config: self._config['orders'] = {}
                for i in self._config['orders'].keys():
                    if not 'save_path' in self._config['orders'][i]:
                        continue
                    if 'cert' in self._config['orders'][i]:
                        self._config['orders'][i]['cert_timeout'] = self._config['orders'][i]['cert']['cert_timeout']
                    if not 'cert_timeout' in self._config['orders'][i]:
                        self._config['orders'][i]['cert_timeout'] = int(time.time())
                    if self._config['orders'][i]['cert_timeout'] > s_time or self._config['orders'][i]['auth_to'] == 'dns':
                        continue
                    if self.find_site_stopped(self._config['orders'][i]['domains']) == '0':
                        write_log("|-The website has been suspended, skip certificate renewal!")
                        continue

                    # 已删除的网站直接跳过续签
                    is_file_check = (self._config['orders'][i]['auth_to'].find('|') == -1 or
                                     not self._config['orders'][i]['auth_to'].startswith("dns")
                                    ) and self._config['orders'][i]['auth_to'].find('/') != -1
                    if is_file_check:
                        # if not os.path.exists(self._config['orders'][i]['auth_to']):
                        # ^^^^^^^^^^——————————这个不能判断网站已被删除的情况下，文件夹未删除时的问题
                        _auth_to = self.get_ssl_used_site(self._config['orders'][i]['save_path'])
                        if not _auth_to:
                            continue

                        # 域名不存在？
                        for domain in self._config['orders'][i]['domains']:
                            if domain.find('*') != -1:
                                break
                            if not public.M('domain').where("name=?",(domain,)).count() and not public.M('binding').where("domain=?",domain).count():
                                _auth_to = None
                                write_log("|-Skip deleted domain names: {}".format(self._config['orders'][i]['domains']))
                        if not _auth_to: continue

                        self._config['orders'][i]['auth_to'] = _auth_to

                    # 检查网站域名是否存在
                    if not public.M('domain').where('`name` IN ({})'.format(', '.join(map(lambda x: "'{}'".format(x), filter(lambda x: x.find('*') < 0, self._config['orders'][i]['domains'])))), ()).count():
                        write_log("|-Skip deleted domain names: {}".format(self._config['orders'][i]['domains']))
                        continue

                    # 是否到了允许重试的时间
                    if 'next_retry_time' in self._config['orders'][i]:
                        timeout = self._config['orders'][i]['next_retry_time'] - int(time.time())
                        if timeout > 0:
                            write_log('|-Skipping domain name: {} this time, due to last renewal failure, we need to wait {} hours before trying again'.format(self._config['orders'][i]['domains'],int(timeout / 60 / 60)))
                            continue

                    # # 是否到了最大重试次数
                    # if 'retry_count' in self._config['orders'][i]:
                    #     if self._config['orders'][i]['retry_count'] >= 5:
                    #         write_log('|-本次跳过域名:{}，因连续5次续签失败，不再续签此证书(可尝试手动续签此证书，成功后错误次数将被重置)'.format(self._config['orders'][i]['domains']))
                    #         continue

                    # 加入到续签订单
                    order_index.append(i)
            if not order_index:
                write_log(public.get_msg_gettext('|-No SSL certificate found within 30 days!'))
                self.get_apis()
                self.renew_cert_other()
                write_log("|-All tasks have been processed!")
                return
            write_log("|-A total of {} certificates need to be renewed".format(len(order_index)))
            n = 0
            self.get_apis()
            cert = None
            args = public.to_dict_obj({})
            for index in order_index:
                args.domains = json.dumps(self._config['orders'][index]['domains'])
                args.auth_type = self._config['orders'][index]['auth_type']
                args.auth_to = self._config['orders'][index]['auth_to']
                sitename = args.auth_to.split('/')[-1]
                if not sitename:
                    sitename = self._config['orders'][index]['auth_to'].split('/')[-2]
                args.siteName = sitename
                write_log('|-Renew the visa certificate and start checking the environment')
                self.check_auth_env(args, check=True)
                n += 1
                domains = _test_domains(self._config['orders'][index]['domains'], self._config['orders'][index]['auth_to'],self._config['orders'][index]['auth_type'])
                if len(domains) == 0:
                    write_log("|-The domain names under the {} certificate are all unused (these domains are: [%s]) and have been skipped.".format(n, ",".join(self._config['orders'][index]['domains'])))
                    continue
                else:
                    self._config['orders'][index]['domains'] = domains
                    write_log(public.get_msg_gettext('|-Renewing certificate number of {}，domain: {}..',
                                                     (n, str(self._config['orders'][index]['domains']))))
                    write_log(public.get_msg_gettext('|-Creating order..'))
                    cert = self.renew_cert_to(self._config['orders'][index]['domains'],self._config['orders'][index]['auth_type'],self._config['orders'][index]['auth_to'],index)
                # aapanel 用
                try:
                    self.turnon_redirect_proxy_httptohttps(args)
                except:
                    pass
            return cert

        except Exception as ex:
            self.remove_dns_record()
            ex = str(ex)
            if ex.find(">>>>") != -1:
                msg = ex.split(">>>>")
                msg[1] = json.loads(msg[1])
            else:
                msg = ex
                write_log(public.get_error_info())
            return public.return_msg_gettext(False, msg)


def _test_domains(domains, auth_to, auth_type):
    # 检查站点域名变更情况， 若有删除域名，则在续签时，删除已经不使用的域名，再执行续签任务
    # 是dns验证的跳过
    if auth_to.find("|") != -1 or auth_to.startswith("dns#@"):
        return domains
    # 是泛域名的跳过
    for domain in domains:
        if domain.find("*.") != -1:
            return domains
    sql = public.M('domain')
    site_sql = public.M('sites')
    for domain in domains:
        pid = sql.where('name=?', domain).getField('pid')
        if pid and site_sql.where('id=?',pid).find():
            site_domains = [i["name"] for i in sql.where('pid=?',(pid,)).field("name").select()]
            break
    else:
        site_id = site_sql.where('path=?', auth_to).getField('id')
        if bool(site_id) and str(site_id).isdigit():
            site_domains = [i["name"] for i in sql.where('pid=?',(site_id,)).field("name").select()]
        else:
            # 全都查询不到，认为这个站点已经被删除
            return []

    del_domains = list(set(domains) - set(site_domains))
    for i in del_domains:
        domains.remove(i)
    return domains


def echo_err(msg):
    write_log("\033[31m=" * 65)
    write_log("|-error: {}\033[0m".format(msg))
    exit()


# 写日志
def write_log(log_str, mode="ab+"):
    if __name__ == "__main__":
        print(log_str)
        return
    _log_file = 'logs/letsencrypt.log'
    f = open(_log_file, mode)
    log_str += "\n"
    f.write(log_str.encode('utf-8'))
    f.close()
    return True

# todo：兼容控制台，目前不兼容
if __name__ == "__main__":
    import argparse
    p = argparse.ArgumentParser(usage=public.get_msg_gettext(
        'Required parameters: --domain list of domain names, multiple separated by commas!'))
    p.add_argument('--domain', default=None,
                   help=public.get_msg_gettext('Please specify the domain name to apply for a certificate'),
                   dest="domains")
    p.add_argument('--type', default=None, help=public.get_msg_gettext('Please specify verification type'),
                   dest="auth_type")
    p.add_argument('--path', default=None, help=public.get_msg_gettext('Please specify the website document root'),
                   dest="path")
    p.add_argument('--dnsapi', default=None, help=public.get_msg_gettext('Please specify DNSAPI'), dest="dnsapi")
    p.add_argument('--dns_key', default=None, help=public.get_msg_gettext('Please specify DNSAPI key'), dest="key")
    p.add_argument('--dns_secret', default=None, help=public.get_msg_gettext('Please specify DNSAPI secret'),
                   dest="secret")
    p.add_argument('--index', default=None, help=public.get_msg_gettext('Specify the order index'), dest="index")
    p.add_argument('--renew', default=None, help=public.get_msg_gettext('renew certificate'), dest="renew")
    p.add_argument('--revoke', default=None, help=public.get_msg_gettext('Revoke certificate'), dest="revoke")
    args = p.parse_args()
    cert = None
    if args.revoke:
        if not args.index:
            echo_err(
                public.get_msg_gettext('Please enter the index of the order to be revoked in the --index parameter'))
        p = acme_v2()
        result = p.revoke_order(args.index)
        write_log(result)
        exit()

    if args.renew:
        p = acme_v2()
        p.renew_cert(args.index)
    else:
        try:
            if not args.index:
                if not args.domains:
                    echo_err(public.get_msg_gettext(
                        'Please specify the domain name for which you want to apply for a certificate in the --domain parameter, multiple separated by commas (,)'))
                if not args.auth_type in ['http', 'tls', 'dns']:
                    echo_err(public.get_msg_gettext(
                        'Please specify the correct authentication type in the --type parameter, supporting dns and http'))
                auth_to = ''
                if args.auth_type in ['http', 'tls']:
                    if not args.path:
                        echo_err(
                            public.get_msg_gettext('Please specify the website document root in the --path parameter!'))
                    if not os.path.exists(args.path):
                        echo_err(public.get_msg_gettext('The specified site root does not exist, please check: {}',
                                                        (args.path,)))
                    auth_to = args.path
                else:
                    if args.dnsapi == '0':
                        auth_to = 'dns'
                    else:
                        if not args.key:
                            echo_err(public.get_msg_gettext(
                                'When applying using dnsapi, specify the dnsapi key in the --dns_key parameter!'))
                        if not args.secret:
                            echo_err(public.get_msg_gettext(
                                'When applying using dnsapi, specify the secret of dnsapi in the --dns_secret parameter!'))
                        auth_to = "{}|{}|{}".format(
                            args.dnsapi, args.key, args.secret)

                domains = args.domains.strip().split(',')
                p = acme_v2()
                cert = p.apply_cert(
                    domains, auth_type=args.auth_type, auth_to=auth_to)
                if args.dnsapi == '0':
                    acme_txt = '_acme-challenge.'
                    acme_caa = '1 issue letsencrypt.org'
                    write_log("=" * 65)
                    write_log("\033[32m" + public.get_msg_gettext(
                        '|-Manual order submission is successful, please resolve DNS records according to the following tips: ') + "\033[0m")
                    write_log("=" * 65)
                    write_log(public.get_msg_gettext('|-Order index: {}', (cert['index'],)))
                    write_log(public.get_msg_gettext('|-Retry the command') + ": ./acme_v2.py --index=\"{}\"".format(
                        cert['index']))
                    write_log(public.get_msg_gettext(
                        '|-A total of \033[36m{}\033[0m domain name records need to be resolved.',
                        (len(cert['auths']),)))
                    for i in range(len(cert['auths'])):
                        write_log('-' * 70)
                        write_log(public.get_msg_gettext(
                            '|-The \033[36m{}\033[0m domain names are: {}, please resolve the following information: ',
                            (str(i + 1), cert['auths'][i]['domain'])))
                        write_log(public.get_msg_gettext(
                            '|-Record Type: TXT Record Name: \033[41m{}\033[0m Record Value: \033[41m{}\033 [0m [Required]',
                            (acme_txt + cert['auths'][i]['domain'].replace('*.', ''), cert['auths'][i]['auth_value'])))
                        write_log(public.get_msg_gettext(
                            '|-Record type: CAA Record name: \033[41m{}\033[0m Record value: \033[41m{}\033[0m [Optional]',
                            (cert['auths'][i]['domain'].replace('*.', ''), acme_caa)))
                    write_log('-' * 70)
                    input_data = ""
                    while input_data not in ['y', 'Y', 'n', 'N']:
                        input_msg = public.get_msg_gettext(
                            'Please wait 2-3 minutes after completing the resolution and enter Y and press Enter to continue verifying the domain name: ')
                        if sys.version_info[0] == 2:
                            input_data = raw_input(input_msg)
                        else:
                            input_data = input(input_msg)
                    if input_data in ['n', 'N']:
                        write_log("=" * 65)
                        write_log(public.get_msg_gettext('|-The user abandons the application and exits the program!'))
                        exit()
                    cert = p.apply_cert(
                        [], auth_type=args.auth_type, auth_to='dns', index=cert['index'])
            else:
                # 重新验证
                p = acme_v2()
                cert = p.apply_cert([], auth_type='dns',
                                    auth_to='dns', index=args.index)
        except Exception as ex:
            write_log("|-{}".format(public.get_error_info()))
            exit()
    if not cert:
        exit()
    write_log("=" * 65)
    write_log(public.get_msg_gettext('|-Certificate obtained successfully!'))
    write_log("=" * 65)
    write_log(
        public.get_msg_gettext('Certificate expiration time: {}', (public.format_date(times=cert['cert_timeout']),)))
    write_log(public.get_msg_gettext('Certificate saved at: {}/', (cert['save_path'],)))
