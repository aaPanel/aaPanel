# coding: utf-8
# ------------------------------
# business ssl
# ------------------------------
import json
import os
import re
import threading
import time

import public
from BTPanel import app
from acme_v2 import acme_v2
from public.validate import Param
from ssl_domainModelV2.api import DomainObject
from ssl_domainModelV2.model import DnsDomainProvider, DnsDomainSSL, DnsDomainRecord
from ssl_domainModelV2.service import CertHandler, SyncService
from panelDnsapi import extract_zone


# noinspection PyUnusedLocal
class BusinessSSL(object):
    __BINDURL = f"{public.OfficialApiBase()}/api/user"  # 获取token 获取官网token
    __APIURL = f"{public.OfficialApiBase()}/api"

    __CODEURL = "https://wafapi.aapanel.com/Auth/GetBindCode"  # 获取绑定验证码
    __UPATH = "data/userInfo.json"
    __PUBKEY = "data/public.key"

    __userInfo = {}
    __PDATA = None
    _check_url = None

    def __init__(self):
        pdata = {
            "access_key": "test",
            "secret_key": "123456",
        }
        data = {
            "access_key": "test",
            "secret_key": "123456",
        }  # 存放调用接口的参数
        if os.path.exists(self.__UPATH):
            my_tmp = public.readFile(self.__UPATH)
            if my_tmp:
                try:
                    self.__userInfo = json.loads(my_tmp)
                except:
                    pass
            try:
                if self.__userInfo:
                    pdata["access_key"] = self.__userInfo["access_key"]
                    data["secret_key"] = self.__userInfo["secret_key"]
            except:
                pass
        pdata["data"] = data
        self.__PDATA = pdata

    # 校验域名是否有适配的dns
    def check_domain_suitable(self, get):
        """
        校验域名是否符合
        """
        if not hasattr(get, "domains"):
            return public.fail_v2("Domain name cannot be empty")
        domains = str(get.domains).strip()
        if not domains:
            return public.fail_v2("Domain name cannot be empty")
        domains = domains.split(",")
        if len(domains) == 0:
            return public.fail_v2("Domain name cannot be empty")

        auto = []
        for d in domains:
            if not d:
                continue
            root, _, _ = extract_zone(d)
            obj = DnsDomainProvider.objects.filter(
                domains__contains=root, status=1
            ).fields("id", "name", "alias").first()
            if obj:
                auto.append({"domain": d, **obj.as_dict()})

        res = {"auto": auto}
        return public.success_v2(res)

    # 发送请求
    def request(self, dname):
        try:
            temp = json.dumps(self.__PDATA.get("data"))
        except:
            temp = self.__PDATA.get("data")

        self.__PDATA["data"] = temp
        if not self.__userInfo.get("token"):
            raise public.HintException("Please Login First")
        url_headers = {
            "authorization": "bt {}".format(self.__userInfo["token"])
        }
        try:
            response_data = public.httpPost(self.__APIURL + "/" + dname, data=self.__PDATA, headers=url_headers)
        except Exception as ex:
            raise public.error_conn_cloud(str(ex))
        try:
            return json.loads(response_data)
        except:
            return public.return_msg_gettext(
                False, "Failed to connect to the official website, please try again later!"
            )

    # 获取证书管理员信息
    def get_cert_admin(self, get):
        result = self.request("cert/user/administrator")
        return public.success_v2(result.get("res"))

    # 获取产品列表
    def get_product_list(self, get):
        result = self.request("cert/product/list")
        return public.success_v2(result.get("res"))

    # 获取商业证书
    def get_order_find(self, get):
        self.__PDATA["uc_id"] = get.uc_id
        result = self.request('cert/user/info')
        return public.success_v2(result.get("res"))

    # 生成商业证书支付订单
    def apply_cert_order_pay(self, args):
        pdata = json.loads(args.pdata)
        self.__PDATA["data"] = pdata
        result = self.request("cert/order/create")
        return public.success_v2(result.get("res"))

    # 单独购买人工安装服务
    def apply_cert_install_pay(self, args):
        """
            @name 单独购买人工安装服务
            @param args<dict_obj>{
                'uc_id'<int> 订单ID
            }
        """
        self.__PDATA['uc_id'] = args.uc_id
        result = self.request('cert/order/deployment_assistance')
        return result

    # 商业证书订单列表
    def get_order_list(self, get=None):
        result = self.request("cert/user/list")
        if result.get("success") is False:
            return public.fail_v2(public.lang("Failed to get order list, please try again later!"))
        return public.success_v2(result.get("res"))

    # 获取网站运行目录
    def _get_site_run_path(self, pid):
        """
            @name 获取网站运行目录
            @author hwliang<2020-08-05>
            @param pid(int) 网站标识
            @return string
        """
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

    # 获取指定域名的PATH
    def _get_domain_run_path(self, domain):
        pid = public.M('domain').where('name=?', (domain,)).getField('pid')
        if not pid: return False
        return self._get_site_run_path(pid)

    def check_ssl_caa(self, domains, clist: list = None):
        """
            @name 检查CAA记录是否正确
            @param domains 域名列表
            @param clist 正确的记录值关键词
            @return bool
        """
        if clist is None:
            clist = ["sectigo.com", "digicert.com", "comodoca.com"]
        try:
            data = {}
            for domain in domains:
                root, zone = public.get_root_domain(domain)
                for d in [
                    domain, root, f"_acme-challenge.{root}", f"_acme-challenge.{domain}"
                ]:
                    ret = public.query_dns(d, "CAA")
                    if not ret:
                        continue
                    slist = []
                    for val in ret:
                        if val['value'] in clist:
                            return False
                        slist.append(val)

                    if len(slist) > 0:
                        data[d] = slist
            if data:
                return {
                    "status": False,
                    "msg": "error: There is a CAA record in the DNS resolution "
                           "of the domain name. Please delete it and apply again ",
                    "data": json.dumps(data),
                    "caa_list": data,
                }
        except:
            pass
        return False

    # 完善资料CA, 提交资料 (前提支付接口完成)
    def apply_order_ca(self, args):
        """
        auto = [
          {
            "domain": "testwpsite.aapanel.org",
            "id": 13,
            "name": "CloudFlareDns",
            "alias": "a"
          },
          {
            "domain": "testphp22.aapanel.org",
            "id": 14,
            "name": "CloudFlareDns",
            "alias": "b"
          }
        ]
        """
        pdata = json.loads(args.pdata)
        result = self.check_ssl_caa(pdata['domains'])
        if result:
            return public.fail_v2(result)
        auto: list = pdata.pop("auto")
        uc_id = pdata.pop("uc_id")

        self.__PDATA["data"] = pdata
        result = self.request("cert/user/update_profile")  # submit
        if result.get("success") is False:
            return public.fail_v2(result.get("res", "Failed to submit data, please try again later!"))

        if not auto or not uc_id:
            return public.success_v2(result.get("res"))

        task = threading.Thread(target=self._auto_dns, args=(auto, uc_id))
        task.start()
        return public.success_v2(result.get("res"))

    # 修改验证方式
    def again_verify(self, args):
        try:
            args.validate([
                Param("uc_id").String().Require(),
                Param("dcv_method").String().Require(),
            ], [
                public.validate.trim_filter(),
            ])
        except Exception as ex:
            public.print_log("error info: {}".format(ex))
            return public.return_message(-1, 0, str(ex))

        self.__PDATA['uc_id'] = args.uc_id
        self.__PDATA['dcv_method'] = args.dcv_method
        result = self.request('cert/user/update_dcv')
        if result.get("success"):
            return public.success_v2(result.get("res"))
        return public.fail_v2(result.get("res"))

    # dns auto parsed
    def _auto_dns(self, auto: list, uc_id: int) -> None:
        with app.app_context():
            # makesure pending
            count = 0
            while count <= 999:
                new_get = public.dict_obj()
                new_get.uc_id = uc_id
                res = self.get_verify_result(new_get)
                if res.get("status") == 0:
                    v_msg = res.get("message")
                    if v_msg.get("code") == 1 and v_msg.get("certStatus") == "PENDING":
                        verify_data = v_msg.get("data")
                        break
                count += 1
                time.sleep(10)

            for a in auto:
                if not a.get("id"):
                    continue
                if not a.get("domain"):
                    continue
                if not a.get("name"):
                    continue

                provider = DnsDomainProvider.objects.filter(id=a.get("id")).first()
                if provider:
                    boyd = {
                        "provider_id": provider.id,
                        "provider_name": provider.name,
                        "api_user": provider.api_user,
                        "domain": verify_data.get("dcvList")[0].get("domainName"),
                        "record": verify_data.get("DCVdnsHost"),
                        "record_value": verify_data.get("DCVdnsValue"),
                        "record_type": verify_data.get("DCVdnsType"),
                        "ttl": 1,
                        "proxy": 0 if a.get("name") == "CloudFlareDns" else -1,
                        "priority": -1,
                    }
                    provider.model_create_dns_record(boyd)

    # 验证通过后移除CNAME
    def _remove_caname(self, uc_id: int, ssl_info: dict) -> None:
        with app.app_context():
            provider = DnsDomainProvider.objects.filter(id=ssl_info.get("provider_id")).first()
            if provider and uc_id:
                get = public.dict_obj()
                get.uc_id = uc_id
                order = self.get_verify_result(get)
                if order.get("status") != 0:
                    public.print_log("remove caname error: order status not 0")
                    return
                if order.get("message").get("status") != "COMPLETE":
                    public.print_log("remove caname error: order status not complete")
                    return
                data = order.get("message").get("data")
                try:
                    DCVdnsHost = data.get("DCVdnsHost")
                    DCVdnsType = data.get("DCVdnsType")
                    domainName = data.get("dcvList")[0].get("domainName")
                    root, _ = public.get_root_domain(domainName)
                except Exception as e:
                    public.print_log(f"error: {e}")

                if not DCVdnsHost or not DCVdnsType or not root:
                    public.print_log(
                        f"remove caname error: "
                        f"DCVdnsHost={DCVdnsHost}, DCVdnsType={DCVdnsType}, domainName root={root}"
                    )
                    return
                SyncService().records_process(provider_obj=provider, all_domains=[root])
                record = DnsDomainRecord.objects.filter(
                    provider_id=provider.id,
                    domain=root,
                    record=DCVdnsHost,
                    record_type=DCVdnsType,
                ).first()
                if record:
                    provider.model_delete_dns_record(record.id)

    @staticmethod
    def _replace_all_cert(ssl_info: dict):
        try:
            acme_v2().sub_all_cert(
                key_file=os.path.join(ssl_info["path"], "privkey.pem"),
                pem_file=os.path.join(ssl_info["path"], "fullchain.pem"),
            )
        except Exception as e:
            public.print_log("replace business cert error: {}".format(e))

    # 验证URL是否匹配
    def check_url_txt(self, args):
        try:
            args.validate([
                Param("url").String().Require(),
                Param("content").String().Require(),
            ], [
                public.validate.trim_filter(),
            ])
        except Exception as ex:
            public.print_log("error info: {}".format(ex))
            return public.return_message(-1, 0, str(ex))

        url = args.url
        content = args.content

        import http_requests
        res = http_requests.get(url, s_type='curl', timeout=5)
        result = res.text
        status = 0
        if not result:
            status = 0
        if result.find('11001') != -1 or result.find('curl: (6)') != -1:
            status = -1
        if result.find('curl: (7)') != -1 or res.status_code in [403, 401]:
            status = -5
        if result.find('Not Found') != -1 or result.find('not found') != -1 or res.status_code in [404]:
            status = -2
        if result.find('timed out') != -1:
            status = -3
        if result.find('301') != -1 or result.find('302') != -1 or result.find(
                'Redirecting...') != -1 or res.status_code in [301, 302]:
            status = -4
        if result == content:
            status = 1
        if status == 1:
            return public.success_v2({"status": status})
        else:
            return public.fail_v2({"status": status})

    # 获取商业证书验证结果, 包含验证信息
    def get_verify_result(self, args):
        try:
            self.__PDATA['uc_id'] = args.uc_id
            res = self.request('cert/user/validate')
            if res.get("success", False) is False:
                return public.fail_v2(
                    res.get("res", "Failed to get verification result, please try again later!")
                )
            verify_info = res['res']

            if verify_info['status'] in ['COMPLETE', False]:
                return public.success_v2(verify_info)

            is_file_verify = 'CNAME_CSR_HASH' != verify_info['data']['dcvList'][0]['dcvMethod']
            verify_info['paths'] = []
            verify_info['hosts'] = []
            if verify_info['data']['application']['status'] == 'ongoing':
                return public.fail_v2(
                    public.lang("In verification, please contact aaPanel if the audit still fails after 24 hours")
                )

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
                    valid_path = "/.well-known/pki-validation"
                    siteRunPath = self._get_domain_run_path(domain)
                    url = 'http' + is_https + '://' + domain + valid_path + '/' + verify_info['data']['DCVfileName']
                    get = public.dict_obj()
                    get.url = url
                    get.content = verify_info['data']['DCVfileContent']
                    status = self.check_url_txt(get)["message"].get("status")
                    verify_info['paths'].append({'url': url, 'status': status})
                    if not siteRunPath:
                        continue

                    verify_path = siteRunPath + valid_path
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
                    if verify_info['data'].get('DCVdnsHost'):
                        verify_info['hosts'].append(verify_info['data']['DCVdnsHost'] + '.' + domain)

            return public.success_v2(verify_info)
        except Exception as e:
            return public.fail_v2("Failed to get verification result, please try again later!")

    # 下载证书
    def download_cert(self, get):
        self.__PDATA["uc_id"] = get.uc_id
        result = self.request("cert/user/download")
        return result

    # 商业证书入库
    def _save_ssl(self, order: dict) -> None:
        """
        阻塞型更新入库
        """
        if DnsDomainSSL.objects.filter(cert_id=order.get("certId")).first():
            return
        try:
            new_get = public.dict_obj()
            new_get.uc_id = order.get("uc_id")
            cert = self.get_order_find(new_get)
            cert = cert.get("message")
            cert_private = cert.get("private_key")
            cert_pem = cert.get("certificate") + "\n" + cert.get("ca_certificate")
            handler = CertHandler()
            hash_ = handler.get_hash(cert_pem)
            # cert maybe uploaded to the free pages, resave.
            DnsDomainSSL.objects.filter(hash=hash_).delete()
            # 入库, 继承user_for
            ssl_info = handler.save_by_data(
                cert_pem=cert_pem,
                private_key=cert_private,
                order={
                    "cert_id": order.get("certId"),
                    "order_info": order,
                }
            )
            if ssl_info:
                try:  # 首次入库替换证书
                    self._replace_all_cert(ssl_info)
                except Exception as e1:
                    public.print_log(f"replace business cert error: {e1}")
                try:  # 首次入库尝试移除caname
                    task = threading.Thread(
                        target=self._remove_caname,
                        args=(order.get("uc_id"), ssl_info,)
                    )
                    task.start()
                except Exception as err:
                    public.print_log(f"remove business ssl caname error: {err}")
        except Exception as e:
            public.print_log(f"update business ssl error: {e}")
            return

    @staticmethod
    def find_next_cert(cert_id: str):
        if not cert_id:
            return None
        try:
            while 1:
                time.sleep(3)
                order_list = BusinessSSL().get_order_list().get("message", [])
                for o in order_list:
                    if o.get("p_certId") == cert_id:
                        return o
        except Exception as e:
            public.print_log(f"find_cert error: {e}")
            raise Exception(f"Failed to find cert for {cert_id}, please try again later!")

    # 商业续签
    def renew_cert_order(self, get, cert_id: str):
        """
        @name 商业证书续签
        首次续签请求续签然后verify轮询
        cert_id 续签得cert_id, 可能会被不断重签, 需要不断轮询获取最新的cert_id去验证
        """

        self.__PDATA['uc_id'] = get.uc_id
        result = self.request('cert/user/renew')
        count = 99
        try:
            new_order = None
            cur_cert_id = cert_id
            while count >= 0:
                count -= 1
                if not new_order:
                    new_order = self.find_next_cert(cur_cert_id)
                # 验证 new_order 订单
                args = public.dict_obj
                args.uc_id = new_order.get("uc_id")
                time.sleep(3)
                verify = self.get_verify_result(args)
                if verify.get("status") == 0:
                    if verify.get("message").get("status") == "REISSUED":
                        # new_order has been REISSUED, update cur_cert_id, reset new_order
                        cur_cert_id = new_order['certId']
                        new_order = None
                        continue

                    if verify.get("message").get("status") == "COMPLETE":
                        return public.success_v2("success")
        except Exception as e:
            return public.fail_v2("Failed to renew certificate, please try again later: {}".format(e))

        finally:
            # it will renew db cert
            self.list_business_ssl(public.to_dict_obj({"p": 1, "limit": "10"}))

        return public.fail_v2("failed to verify certificate")

    # 商业证书列表
    def list_business_ssl(self, get=None):
        try:
            if get:
                get.validate([
                    Param("p").Integer(),
                    Param("limit").String(),
                ], [
                    public.validate.trim_filter(),
                ])
        except Exception as ex:
            public.print_log("error info: {}".format(ex))
            return public.return_message(-1, 0, str(ex))

        org_orders = self.get_order_list()
        if org_orders.get("status") != 0:
            return public.fail_v2("Failed To Get Order List, Please Try Again Later")
        if not isinstance(org_orders.get("message"), list):
            return public.fail_v2("Failed to get order list, please try again later!")

        msg = "Get Business SSL Order Successfully"
        if len(org_orders.get("message")) == 0:
            DnsDomainSSL.objects.filter(is_order=1).delete()
            return public.success_v2({"data": [], "total": 0, "msg": msg})

        res = []
        org_orders["message"].sort(key=lambda i: i.get("uc_id"))
        for o in org_orders["message"]:
            if o.get("order_status") == "COMPLETE" and o.get("certId"):
                if bool([x for x in org_orders["message"] if x.get("p_certId") == o.get("certId")]):
                    continue
                self._save_ssl(o)
            else:
                DnsDomainSSL.objects.filter(
                    order_info__pid=o.get("pid"),
                    order_info__uc_id=o.get("uc_id"),
                    order_info__oid=o.get("oid"),
                ).delete()
                if o.get("order_status") == "REISSUED":
                    continue
                res.append({"order_info": o})

        page = int(getattr(get, "p", 1))
        limit = int(getattr(get, "limit", 100))
        ssl_obj = DnsDomainSSL.objects.filter(is_order=1)
        total = ssl_obj.count()
        ssl_obj.offset((page - 1) * limit).limit(limit)
        res.extend([
            {
                "hash": ssl.hash,
                "provider": ssl.info.get("issuer_O", "unknown"),
                "issuer": ssl.info.get("issuer", "unknown"),
                "verify_domains": list(set(ssl.dns + [ssl.subject])),
                "end_time": DomainObject._end_time(ssl.not_after),
                "end_date": ssl.not_after,
                "last_apply_time": ssl.info.get("notBefore", ""),
                "auto_renew": ssl.auto_renew,
                "cert": {
                    "csr": public.readFile(ssl.path + "/fullchain.pem"),  # 证书
                    "key": public.readFile(ssl.path + "/privkey.pem"),  # 密钥
                },
                "order_info": ssl.order_info,
                "user_for": ssl.user_for,
                "alarm": ssl.alarm,
            } for ssl in ssl_obj
        ])
        return public.success_v2({"data": res, "total": total, "msg": msg})
