# coding: utf-8
# +-------------------------------------------------------------------
# | aaPanel
# +-------------------------------------------------------------------
# | Copyright (c) 2015-2099 aaPanel(www.aapanel.com) All rights reserved.
# +-------------------------------------------------------------------
# | Author: 沐落 <cjx@aapanel.com>
# +-------------------------------------------------------------------
import ipaddress
import json
import os
import sys
import time
from urllib.parse import urljoin

import requests

os.chdir("/www/server/panel")
sys.path.insert(0, 'class/')

import public
from public.exceptions import HintException


class ExtractZoneTool(object):

    def __init__(self):
        self.top_domain_list = [
            '.ac.cn', '.ah.cn', '.bj.cn', '.com.cn', '.cq.cn', '.fj.cn', '.gd.cn',
            '.gov.cn', '.gs.cn', '.gx.cn', '.gz.cn', '.ha.cn', '.hb.cn', '.he.cn',
            '.hi.cn', '.hk.cn', '.hl.cn', '.hn.cn', '.jl.cn', '.js.cn', '.jx.cn',
            '.ln.cn', '.mo.cn', '.net.cn', '.nm.cn', '.nx.cn', '.org.cn']
        top_domain_list_data = public.readFile('{}/config/domain_root.txt'.format(public.get_panel_path()))
        if top_domain_list_data:
            self.top_domain_list = set(top_domain_list_data.strip().split('\n'))

    def __call__(self, domain_name):
        domain_name = domain_name.lstrip("*.")
        old_domain_name = domain_name
        top_domain = "." + ".".join(domain_name.rsplit('.')[-2:])
        new_top_domain = "." + top_domain.replace(".", "")
        is_tow_top = False
        if top_domain in self.top_domain_list:
            is_tow_top = True
            domain_name = domain_name[:-len(top_domain)] + new_top_domain

        if domain_name.count(".") <= 1:
            zone = ""
            root = old_domain_name
            acme_txt = "_acme-challenge"
        else:
            zone, middle, last = domain_name.rsplit(".", 2)
            acme_txt = "_acme-challenge.%s" % zone
            if is_tow_top:
                last = top_domain[1:]
            root = ".".join([middle, last])
        return root, zone, acme_txt


extract_zone = ExtractZoneTool()


def white_kwargs(kwargs: dict):
    white_list = ["priority"]
    return {k: v for k, v in kwargs.items() if k in white_list}


class BaseDns(object):
    def __init__(self):
        self.dns_provider_name = self.__class__.__name__
        self.api_user = ""
        self.api_key = ""

    def log_response(self, response):
        try:
            log_body = response.json()
        except ValueError:
            log_body = response.content
        return log_body

    def create_dns_record(self, domain_name, domain_dns_value):
        raise NotImplementedError("create_dns_record method must be implemented.")

    def delete_dns_record(self, domain_name, domain_dns_value):
        raise NotImplementedError("delete_dns_record method must be implemented.")

    def add_record_for_creat_site(self, domain, server_ip):
        raise NotImplementedError("add_record_for_creat_site method must be implemented.")

    # =============== 域名管理同步信息 =====================
    def get_domains(self):
        raise NotImplementedError("get_domains method must be implemented.")

    def get_dns_record(self, domain_name):
        raise NotImplementedError("get_dns_record method must be implemented.")

    def create_org_record(self, domain_name, record, record_value, record_type, ttl, **kwargs):
        raise NotImplementedError("create_org_record method must be implemented.")

    def remove_record(self, domain_name, record, record_type):
        raise NotImplementedError("remove_record method must be implemented.")

    def update_record(self, domain_name, record, new_record, ttl=1, **kwargs):
        raise NotImplementedError("update_record method must be implemented.")

    def raise_resp_error(self, response: requests.Response):
        raise HintException(
            "Error {dns_name}: status_code={status_code} response={response}".format(
                dns_name=self.dns_provider_name,
                status_code=response.status_code,
                response=self.log_response(response),
            )
        )

    def verify(self):
        try:
            self.get_domains()
        except Exception:
            raise HintException("Verify fail, please check your Api Account and Password")
        return True


class NameCheapDns(BaseDns):
    dns_provider_name = "namecheap"
    _type = 0  # 0:lest 1：锐成
    kw_prefix = {
        "priority": "MXPref"
    }

    def __init__(self, api_user, api_key, **kwargs):
        super().__init__()
        self.api_user = api_user
        self.api_key = api_key
        self.timeout = 30
        self.base_url = "https://api.namecheap.com/xml.response"

    def _get_local_ip(self):
        try:
            ip = public.GetLocalIp()
            ip_obj = ipaddress.ip_address(ip)
            if isinstance(ip_obj, ipaddress.IPv4Address):
                return ip
            elif isinstance(ip_obj, ipaddress.IPv6Address):
                raise HintException("Namecheap Api does not support IPv6")
        except Exception as e:
            raise HintException(e)


    def _get_hosts(self, domain_name) -> list:
        params = {
            "ApiUser": self.api_user,
            "ApiKey": self.api_key,
            "UserName": self.api_user,
            "Command": "namecheap.domains.dns.getHosts",
            "ClientIp": self._get_local_ip(),
            "SLD": domain_name.split(".")[0],
            "TLD": domain_name.split(".")[1],
        }
        resp = requests.get(url=self.base_url, params=params, timeout=self.timeout)
        if resp.status_code != 200:
            self.raise_resp_error(resp)
        hosts = []
        index = 0
        hosts_info = self._generate_xml_tree(resp.text, ".//host")
        for host in hosts_info:
            index += 1
            try:
                ttl = int(host.get("TTL", 1))
            except Exception:
                ttl = 1
            try:
                mx_pref = int(host.get("MXPref", -1))
            except Exception:
                mx_pref = -1

            hosts.append({
                f"HostName{index}": host.get("Name"),
                f"RecordType{index}": host.get("Type"),
                f"Address{index}": host.get("Address"),
                f"TTL{index}": ttl,
                f"MXPref{index}": mx_pref if host.get("Type") == "MX" else -1,
            })
        return hosts

    # =============== acme ======================

    def add_record(self, domain_name, s_type, acme_txt, dns_value):
        hosts = self._get_hosts(domain_name)
        add_index = len(hosts) + 1
        params = {
            "ApiUser": self.api_user,
            "ApiKey": self.api_key,
            "UserName": self.api_user,
            "ClientIp": self._get_local_ip(),
            "Command": "namecheap.domains.dns.setHosts",
            "SLD": domain_name.split(".")[0],
            "TLD": domain_name.split(".")[1],
            "DomainName": domain_name,
        }
        for index, host in enumerate(hosts):
            params[f"HostName{index + 1}"] = host[f"HostName{index + 1}"]
            params[f"Address{index + 1}"] = host[f"Address{index + 1}"]
            params[f"RecordType{index + 1}"] = host[f"RecordType{index + 1}"]

        params[f"HostName{add_index}"] = acme_txt
        params[f"Address{add_index}"] = dns_value
        params[f"RecordType{add_index}"] = s_type
        setHosts_resp = requests.get(url=self.base_url, params=params, timeout=self.timeout)
        if setHosts_resp.status_code != 200:
            self.raise_resp_error(setHosts_resp)

    def create_dns_record(self, domain_name, domain_dns_value):
        # acme 调用
        domain_name = domain_name.lstrip("*.")
        root, _, acme_txt = extract_zone(domain_name)
        if self._type != 0:
            s_type = "CNAME"
            acme_txt = acme_txt.replace('_acme-challenge.', '')
        else:
            s_type = "TXT"
        return self.add_record(root, s_type, acme_txt, domain_dns_value)

    def delete_dns_record(self, domain_name, dns_value=None):
        # 移除挑战值
        domain_name = domain_name.lstrip("*.")
        root, zone, _ = extract_zone(domain_name)
        value = zone if zone != "" else root
        dns_name = "_acme-challenge" + "." + value
        self.remove_record(domain_name, dns_name, 'TXT')

    # =============== 域名管理 ====================
    @staticmethod
    def _generate_xml_tree(resp_body: str, findall: str):
        import xml.etree.ElementTree as EtTree
        from xml.etree.ElementTree import ParseError as ETParseError
        tree_root = resp_body.replace('xmlns="http://api.namecheap.com/xml.response"', '')
        try:
            targets = EtTree.fromstring(tree_root).findall(findall)
            return targets
        except ETParseError:
            raise HintException("Error parsing XML response from Namecheap API")

    def get_domains(self, verify: bool = False) -> list | bool:
        # 获取账号下所有域名, 判断域名nameserver归属, 并且所有返回均为xml
        params = {
            "ApiUser": self.api_user,
            "ApiKey": self.api_key,
            "UserName": self.api_user,
            "Command": "namecheap.domains.getList",  # returns a list of domains for the particular user
            "ClientIp": self._get_local_ip(),
        }
        resp = requests.get(url=self.base_url, params=params, timeout=self.timeout)
        if 'API Key is invalid or API access has not been enabled' in resp.text:
            raise HintException("API Key is invalid")

        if resp.status_code != 200:
            raise HintException("get domians fail")

        if verify:
            return True

        try:
            domains = self._generate_xml_tree(resp.text, ".//Domain")
        except HintException:
            raise HintException("Error parsing XML response from Namecheap API")

        domains = [
            domain.get("Name") for domain in domains if domain.get("IsExpired") == "false"
        ]
        res = []
        for d in domains:
            try:
                params = {
                    "ApiUser": self.api_user,
                    "ApiKey": self.api_key,
                    "UserName": self.api_user,
                    # gets a list of DNS servers associated with the requested domain.
                    "Command": "namecheap.domains.dns.getList",
                    "ClientIp": self._get_local_ip(),
                    "SLD": d.split(".")[0],
                    "TLD": d.split(".")[1],
                }
                resp = requests.get(url=self.base_url, params=params, timeout=self.timeout)
                if resp.status_code != 200:
                    continue
                tree = self._generate_xml_tree(resp.text, ".//DomainDNSGetListResult")
                for t in tree:
                    if t.get("Domain") == d and t.get("IsUsingOurDNS") == "true":
                        res.append(d)
                        break
                time.sleep(1)
            except Exception as e:
                public.print_log(f"get_domains error {e}")
                continue
        return res

    def get_dns_record(self, domain_name):
        domain_name, _, _ = extract_zone(domain_name)
        try:
            records = self._get_hosts(domain_name)
        except Exception as e:
            public.print_log(f"get_dns_record error {e}")
            records = []
        res = []
        for r in records:
            temp = {}
            for k, v in r.items():
                if k.startswith("HostName"):
                    temp["record"] = v
                elif k.startswith("RecordType"):
                    temp["record_type"] = v
                elif k.startswith("Address"):
                    temp["record_value"] = v
                elif k.startswith("TTL"):
                    temp["ttl"] = r.get("ttl", 1)
                elif k.startswith("MXPref"):
                    temp["priority"] = v
                else:
                    temp[k] = v
            res.append(temp)
        return res

    def __set_hosts_with_params(self, domain_name: str, new_params: dict):
        try:
            setHosts_resp = requests.get(url=self.base_url, params=new_params, timeout=self.timeout)
        except Exception as e:
            return {"status": False, "msg": str(e)}
        if any([
            setHosts_resp.status_code != 200,
            f'Domain="{domain_name}" IsSuccess="true"' not in setHosts_resp.text
        ]):
            return {"status": False, "msg": setHosts_resp.text}
        return {"status": True, "msg": setHosts_resp.text}

    def __generate_new_params(self, new_params: dict, new_hosts: list) -> dict:
        for i, host in enumerate(new_hosts):
            index = i + 1
            for key in list(host.keys()):
                if key.startswith(("HostName", "Address", "RecordType", "TTL", "MXPref")):
                    base_key = ''.join([c for c in key if not c.isdigit()])
                    if base_key == "MXPref" and host[key] == -1:
                        continue
                    new_params[f"{base_key}{index}"] = host[key]
        return new_params

    # 创建record
    def create_org_record(self, domain_name, record, record_value, record_type, ttl=1, **kwargs):
        domain_name, _, _ = extract_zone(domain_name)
        hosts = self._get_hosts(domain_name)
        add_index = len(hosts) + 1
        params = {
            "ApiUser": self.api_user,
            "ApiKey": self.api_key,
            "UserName": self.api_user,
            "ClientIp": self._get_local_ip(),
            "Command": "namecheap.domains.dns.setHosts",
            "SLD": domain_name.split(".")[0],
            "TLD": domain_name.split(".")[1],
            "DomainName": domain_name,
        }
        for index, host in enumerate(hosts):
            idx = index + 1
            for field in ["HostName", "Address", "RecordType", "TTL", "MXPref"]:
                if field == "MXPref" and host[f"{field}{idx}"] == -1:
                    continue
                params[f"{field}{idx}"] = host[f"{field}{idx}"]

        params.update({
            f"HostName{add_index}": record,
            f"Address{add_index}": record_value,
            f"RecordType{add_index}": record_type,
            f"TTL{add_index}": ttl
        })
        for k, v in white_kwargs(kwargs).items():
            if self.kw_prefix.get(k):
                params[f"{self.kw_prefix.get(k)}{add_index}"] = v
        return self.__set_hosts_with_params(domain_name, params)

    # 删除record
    def remove_record(self, domain_name, record, record_type="TXT") -> dict:
        domain_name, _, _ = extract_zone(domain_name)
        hosts_info = self._get_hosts(domain_name)
        new_hosts = [
            host for host in hosts_info if not (record in host.values() and record_type in host.values())
        ]
        if not new_hosts:
            # is empty
            return {"status": True, "msg": "Dns Record is empty."}
        new_params = {
            "ApiUser": self.api_user,
            "ApiKey": self.api_key,
            "UserName": self.api_user,
            "ClientIp": self._get_local_ip(),
            "Command": "namecheap.domains.dns.setHosts",
            "SLD": domain_name.split(".")[0],
            "TLD": domain_name.split(".")[1],
            "DomainName": domain_name,
        }
        new_params = self.__generate_new_params(new_params, new_hosts)
        return self.__set_hosts_with_params(domain_name, new_params)

    # 更新record
    def update_record(self, domain_name, record: dict, new_record: dict, **kwargs):
        domain_name, _, _ = extract_zone(domain_name)
        hosts_info = self._get_hosts(domain_name)
        new_hosts = []
        for index, host in enumerate(hosts_info):
            if all([
                record.get("record") in host.values(),
                record.get("record_type") in host.values(),
                record.get("record_value") in host.values(),
            ]):
                host[f"HostName{index + 1}"] = new_record.get("record")
                host[f"RecordType{index + 1}"] = new_record.get("record_type")
                host[f"Address{index + 1}"] = new_record.get("record_value")
                host[f"TTL{index + 1}"] = kwargs.get("ttl", 1)
                if new_record.get("priority") != -1:
                    host[f"MXPref{index + 1}"] = new_record.get("priority")
                new_hosts.append(host)
            else:
                new_hosts.append(host)
        if not new_hosts:  # is empty
            return {"status": True, "msg": "Dns Record is empty."}
        new_params = {
            "ApiUser": self.api_user,
            "ApiKey": self.api_key,
            "UserName": self.api_user,
            "ClientIp": self._get_local_ip(),
            "Command": "namecheap.domains.dns.setHosts",
            "SLD": domain_name.split(".")[0],
            "TLD": domain_name.split(".")[1],
            "DomainName": domain_name,
        }
        new_params = self.__generate_new_params(new_params, new_hosts)
        return self.__set_hosts_with_params(domain_name, new_params)

    # 验证
    def verify(self):
        # namecheap token 请求时会切掉多余的str长度
        try:
            self.get_domains(verify=True)
        except HintException as e:
            raise e
        except Exception:
            raise HintException(
                "Verify fail, please check your Api Account and Password, "
                "Add the server address to the NameCheapDns API whitelist."
            )
        return True


class CloudFlareDns(BaseDns):
    dns_provider_name = "cloudflare"
    _type = 0  # 0:lest 1：锐成
    kw_prefix = {
        "priority": "priority"
    }

    def __init__(self, api_user, api_key, limit: bool = True, **kwargs):
        super().__init__()
        self.cf_zone_id = None
        self.api_user = api_user
        self.api_key = api_key
        self.limit = limit
        self.cf_base_url = "https://api.cloudflare.com/client/v4/"
        self.time_out = 65  # seconds

    def _get_auth_headers(self) -> dict:
        if self.limit is True:
            return {"Authorization": "Bearer " + self.api_key}
        else:  # api limit False, is global permissions
            return {"X-Auth-Email": self.api_user, "X-Auth-Key": self.api_key}

    def find_dns_zone(self, domain_name):
        url = self.cf_base_url + "zones?status=active&per_page=1000"
        headers = self._get_auth_headers()
        find_dns_zone_response = requests.get(url, headers=headers, timeout=self.time_out)
        if find_dns_zone_response.status_code != 200:
            raise HintException(
                "Error find cloudflare dns zone, please check your Api Account and Password:"
                " status_code={status_code} response={response}".format(
                    status_code=find_dns_zone_response.status_code,
                    response=self.log_response(find_dns_zone_response),
                )
            )

        result = find_dns_zone_response.json()["result"]
        for i in result:
            if i["name"] in domain_name:
                setattr(self, "cf_zone_id", i["id"])
        if isinstance(self.cf_zone_id, type(None)):
            raise HintException(
                "Error unable to get DNS zone for domain_name={domain_name} "
                ", please check your Api Account and Password: status_code={status_code} response={response}".format(
                    domain_name=domain_name,
                    status_code=find_dns_zone_response.status_code,
                    response=self.log_response(find_dns_zone_response),
                )
            )

    # =============== acme ======================
    def add_record(self, domain_name, value, s_type):
        self.find_dns_zone(domain_name)
        url = urljoin(
            self.cf_base_url,
            "zones/{0}/dns_records".format(self.cf_zone_id),
        )
        headers = self._get_auth_headers()
        body = {
            "type": s_type,
            "name": domain_name,
            "content": "{0}".format(value),
        }

        create_resp = requests.post(
            url, headers=headers, json=body, timeout=self.time_out
        )
        if create_resp.status_code != 200:
            self.raise_resp_error(create_resp)

    def create_dns_record(self, domain_name, domain_dns_value):
        # acme 调用
        domain_name = domain_name.lstrip("*.")
        self.find_dns_zone(domain_name)
        url = urljoin(
            self.cf_base_url,
            "zones/{0}/dns_records".format(self.cf_zone_id),
        )
        headers = self._get_auth_headers()
        body = {
            "type": "TXT",
            "name": "_acme-challenge" + "." + domain_name + ".",
            "content": "{0}".format(domain_dns_value),
        }
        if self._type == 1:
            body['type'] = 'CNAME'
            root, _, acme_txt = extract_zone(domain_name)
            body['name'] = acme_txt.replace('_acme-challenge.', '')

        create_cloudflare_dns_record_response = requests.post(
            url, headers=headers, json=body, timeout=self.time_out
        )
        if create_cloudflare_dns_record_response.status_code != 200:
            # raise error so that we do not continue to make calls to ACME
            # server
            raise HintException(
                "Error creating cloudflare dns record: status_code={status_code} response={response}".format(
                    status_code=create_cloudflare_dns_record_response.status_code,
                    response=self.log_response(create_cloudflare_dns_record_response),
                )
            )

    def delete_dns_record(self, domain_name, domain_dns_value):
        # 移除挑战值
        domain_name = domain_name.lstrip("*.")
        dns_name = "_acme-challenge" + "." + domain_name
        self.remove_record(domain_name, dns_name, 'TXT')

    # =============== 域名管理 ====================

    def get_domains(self) -> list:
        url = self.cf_base_url + "zones?status=active&per_page=1000"
        headers = self._get_auth_headers()
        res = requests.get(url, headers=headers, timeout=self.time_out)
        try:
            if not res.json().get("success"):
                raise HintException("get domians fail")
            result = res.json().get("result", [])
        except Exception as e:
            public.print_log(f"cloudflare get_domains error {e}")
            raise HintException(e)
        return [i.get("name", "") for i in result]

    def get_dns_record(self, domain_name: str) -> list:
        domain_name, _, _ = extract_zone(domain_name)
        self.find_dns_zone(domain_name)
        url = self.cf_base_url + f"zones/{self.cf_zone_id}/dns_records"
        result = []
        page = 1
        per_page = 500
        fail_count = 0
        while True:
            params = {"page": page, "per_page": per_page}
            try:
                response = requests.get(
                    url, headers=self._get_auth_headers(), params=params
                )
                data = response.json()
                if data.get("success"):
                    records = data.get("result", [])
                    result.extend([
                        {
                            "record": i.get("name", ""),
                            "record_value": i.get("content", ""),
                            "record_type": i.get("type", ""),
                            "proxy": i.get("proxied", False),
                            "priority": i.get("priority", -1),
                            "ttl": i.get("ttl", 1),
                        } for i in records
                    ])
                    if len(records) < per_page:
                        break
                    page += 1
                else:
                    fail_count += 1
                    if fail_count >= 3:
                        break
            except requests.RequestException as e:
                print("get_dns_record error", e)
                break
        return result

    # 创建record
    def create_org_record(self, domain_name, record, record_value, record_type, ttl=1, proxied=0, **kwargs):
        domain_name, _, _ = extract_zone(domain_name)
        proxied = True if proxied == 1 else False
        self.find_dns_zone(domain_name)
        url = self.cf_base_url + f"zones/{self.cf_zone_id}/dns_records"
        headers = self._get_auth_headers()
        body = {
            "content": record_value,
            "name": record,
            "proxied": proxied,
            "ttl": ttl,
            "type": record_type
        }
        for k, v in white_kwargs(kwargs).items():  # 接受其他关键参数
            if self.kw_prefix.get(k):
                body[self.kw_prefix.get(k)] = v
        try:
            create_res = requests.post(url, headers=headers, json=body, timeout=self.time_out)
            create_res = create_res.json()
            if create_res.get("success"):
                return {"status": True, "msg": create_res}
            return {"status": False, "msg": str(create_res.get("errors"))}
        except requests.exceptions.HTTPError as http_err:
            return {"status": False, "msg": http_err}
        except Exception as e:
            return {"status": False, "msg": str(e)}

    # 删除record
    def remove_record(self, domain_name, record, record_type="TXT") -> dict:
        domain_name, _, _ = extract_zone(domain_name)
        self.find_dns_zone(domain_name)
        headers = self._get_auth_headers()
        list_dns_payload = {"type": record_type, "name": record}
        list_dns_url = self.cf_base_url + f"zones/{self.cf_zone_id}/dns_records"
        list_dns_response = requests.get(
            list_dns_url, params=list_dns_payload, headers=headers, timeout=self.time_out
        )
        try:
            for i in range(0, len(list_dns_response.json()["result"])):
                dns_record_id = list_dns_response.json()["result"][i]["id"]
                url = self.cf_base_url + f"zones/{self.cf_zone_id}/dns_records/{dns_record_id}"
                remove_res = requests.delete(url, headers=headers, timeout=self.time_out)
                remove_res = remove_res.json()
                if remove_res.get("success"):
                    return {"status": True, "msg": remove_res}
                return {"status": False, "msg": str(remove_res.get("errors"))}
            # is empty
            return {"status": True, "msg": "Dns Record is empty."}
        except requests.exceptions.HTTPError as http_err:
            return {"status": False, "msg": http_err}
        except Exception as e:
            return {"status": False, "msg": str(e)}

    # 更新record
    def update_record(self, domain_name, record: dict, new_record: dict, **kwargs):
        domain_name, _, _ = extract_zone(domain_name)
        self.find_dns_zone(domain_name)
        record_type = record.get("record_type")
        record_name = record.get("record")
        get_url = self.cf_base_url + f"zones/{self.cf_zone_id}/dns_records?type={record_type}&name={record_name}"
        try:
            # get record id
            get_response = requests.get(get_url, headers=self._get_auth_headers())
            get_result = get_response.json()
            if get_result.get("success") and get_result.get("result"):
                record_id = get_result["result"][0]["id"]
                update_url = self.cf_base_url + f"zones/{self.cf_zone_id}/dns_records/{record_id}"
                body = {
                    "type": new_record.get("record_type"),
                    "name": new_record.get("record"),
                    "content": new_record.get("record_value"),
                    "ttl": new_record.get("ttl", 1),
                    "proxied": True if new_record.get("proxy") == 1 else False,
                }
                update_response = requests.put(update_url, headers=self._get_auth_headers(), json=body)
                update_result = update_response.json()
                if update_result.get("success"):
                    return {"status": True, "msg": update_result}
                return {"status": False, "msg": str(update_result.get("errors"))}
            else:
                return {"status": False, "msg": "Dns Record Not Found!"}
        except requests.exceptions.HTTPError as http_err:
            return {"status": False, "msg": http_err}
        except Exception as err:
            return {"status": False, "msg": err}

    # 验证
    def verify(self):
        try:
            self.get_domains()
        except Exception:
            raise HintException("Verify fail, please check your Api Account and Password")
        return True

# 未验证
class CloudNsDns(BaseDns):
    dns_provider_name = "cloudns"
    _type = 0  # 0:lest 1：锐成
    kw_prefix = {
        "priority": "priority"
    }

    def __init__(self, api_user, api_key, **kwargs):
        super().__init__()
        self.api_user = api_user
        self.api_key = api_key
        self.timeout = 30
        self.base_url = "https://api.cloudns.net/dns/"

    def get_record_id(self, domain_name, subd, s_type):
        url = urljoin(self.base_url, "list-records.json")
        params = {
            "auth-id": self.api_user,
            "auth-password": self.api_key,
            "domain-name": domain_name,
        }
        res = requests.get(url, params=params, timeout=self.timeout)
        if res.status_code != 200:
            raise ValueError(
                "Error retrieving cloudns dns records: status_code={status_code} response={response}".format(
                    status_code=res.status_code,
                    response=self.log_response(res),
                )
            )
        records = res.json().get("records", [])
        for record in records:
            if record["host"] == subd and record["type"] == s_type:
                return record["id"]
        return None

    def add_record(self, domain_name, s_type, acme_txt, dns_value):
        url = urljoin(self.base_url, "add-record.json")
        params = {
            "auth-id": self.api_user,
            "auth-password": self.api_key,
            "domain-name": domain_name,
            "record-type": s_type,
            "host-name": acme_txt,
            "record": dns_value,
            "ttl": 1,
        }

        create_cloudns_dns_record_response = requests.post(
            url, params=params, timeout=self.timeout
        )
        if create_cloudns_dns_record_response.status_code != 200:
            raise ValueError(
                "Error creating cloudns dns record: status_code={status_code} response={response}".format(
                    status_code=create_cloudns_dns_record_response.status_code,
                    response=self.log_response(create_cloudns_dns_record_response),
                )
            )

    def remove_record(self, domain_name, subd, s_type):
        record_id = self.get_record_id(domain_name, subd, s_type)
        if not record_id:
            raise ValueError("Record not found")
        url = urljoin(self.base_url, "delete-record.json")
        params = {
            "auth-id": self.api_user,
            "auth-password": self.api_key,
            "domain-name": domain_name,
            "record-id": record_id,
        }
        remove_cloudns_dns_record_response = requests.post(
            url, params=params, timeout=self.timeout
        )
        if remove_cloudns_dns_record_response.status_code != 200:
            raise ValueError(
                "Error removing cloudns dns record: status_code={status_code} response={response}".format(
                    status_code=remove_cloudns_dns_record_response.status_code,
                    response=self.log_response(remove_cloudns_dns_record_response),
                )
            )
        return remove_cloudns_dns_record_response.json()

    def create_dns_record(self, domain_name, domain_dns_value):
        domain_name = domain_name.lstrip("*.")
        root, _, acme_txt = extract_zone(domain_name)
        if self._type != 0:
            s_type = "CNAME"
            acme_txt = acme_txt.replace('_acme-challenge.', '')
        else:
            s_type = "TXT"
        return self.add_record(root, s_type, acme_txt, domain_dns_value)

    def delete_dns_record(self, domain_name, dns_value=None):
        domain_name = domain_name.lstrip("*.")
        dns_name = "_acme-challenge" + "." + domain_name
        self.remove_record(domain_name, dns_name, 'TXT')

    def get_domains(self) -> list:
        url = urljoin(self.base_url, "list-domains.json")
        headers = {
            "X-Auth-User": self.api_user,
            "X-Auth-Key": self.api_key,
        }
        res = requests.get(url, headers=headers, timeout=self.timeout)
        if res.status_code != 200:
            return []
        try:
            result = res.json().get("domains", [])
        except Exception as e:
            public.print_log(f"cloudns get_domains error {e}")
            result = []
        return [i.get("name", "") for i in result]

    def get_dns_record(self, domain_name: str) -> list:
        url = urljoin(self.base_url, "list-records.json")
        headers = {
            "X-Auth-User": self.api_user,
            "X-Auth-Key": self.api_key,
        }
        params = {
            "domain-name": domain_name
        }
        res = requests.get(url, headers=headers, params=params, timeout=self.timeout)
        if res.status_code != 200:
            return []
        try:
            result = res.json().get("records", [])
        except Exception as e:
            public.print_log(f"cloudns get_dns_record error {e}")
            result = []
        return result

    def create_org_record(self, domain_name, record, record_value, record_type, ttl=1, **kwargs):
        url = urljoin(self.base_url, "add-record.json")
        body = {
            "domain-name": domain_name,
            "record-type": record_type,
            "host-name": record,
            "record-data": record_value,
            "ttl": ttl,
        }
        headers = {
            "X-Auth-User": self.api_user,
            "X-Auth-Key": self.api_key,
        }
        create_cloudns_dns_record_response = requests.post(
            url, json=body, headers=headers, timeout=self.timeout
        )
        if create_cloudns_dns_record_response.status_code != 200:
            raise ValueError(
                "Error creating cloudns dns record: status_code={status_code} response={response}".format(
                    status_code=create_cloudns_dns_record_response.status_code,
                    response=self.log_response(create_cloudns_dns_record_response),
                )
            )
        return create_cloudns_dns_record_response.json()

    def update_record(self, domain_name, record: dict, new_record: dict, **kwargs):
        url = urljoin(self.base_url, "edit-record.json")
        body = {
            "domain-name": domain_name,
            "record-type": record.get("record_type"),
            "host-name": record.get("record"),
            "record-data": new_record.get("record_value"),
            "ttl": new_record.get("ttl", 1),
        }
        headers = {
            "X-Auth-User": self.api_user,
            "X-Auth-Key": self.api_key,
        }
        update_cloudns_dns_record_response = requests.post(
            url, json=body, headers=headers, timeout=self.timeout
        )
        if update_cloudns_dns_record_response.status_code != 200:
            raise ValueError(
                "Error updating cloudns dns record: status_code={status_code} response={response}".format(
                    status_code=update_cloudns_dns_record_response.status_code,
                    response=self.log_response(update_cloudns_dns_record_response),
                )
            )
        return update_cloudns_dns_record_response.json()


# 未验证
class CloudxnsDns(object):
    def __init__(self, key, secret, ):
        self.key = key
        self.secret = secret
        self.APIREQUESTDATE = time.ctime()

    def get_headers(self, url, parameter=''):
        APIREQUESTDATE = self.APIREQUESTDATE
        APIHMAC = public.Md5(self.key + url + parameter + APIREQUESTDATE + self.secret)
        headers = {
            "API-KEY": self.key,
            "API-REQUEST-DATE": APIREQUESTDATE,
            "API-HMAC": APIHMAC,
            "API-FORMAT": "json"
        }
        return headers

    def get_domain_list(self):
        url = "https://www.cloudxns.net/api2/domain"
        headers = self.get_headers(url)
        req = requests.get(url=url, headers=headers, verify=False)
        req = req.json()

        return req

    def get_domain_id(self, domain_name):
        req = self.get_domain_list()
        for i in req["data"]:
            if domain_name.strip() == i['domain'][:-1]:
                return i['id']
        return False

    def create_dns_record(self, domain_name, domain_dns_value):
        root, _, acme_txt = extract_zone(domain_name)
        domain = self.get_domain_id(root)
        if not domain:
            raise ValueError('The domain name does not exist under this cloudxns user, adding parsing failed.')

        url = "https://www.cloudxns.net/api2/record"
        data = {
            "domain_id": int(domain),
            "host": acme_txt,
            "value": domain_dns_value,
            "type": "TXT",
            "line_id": 1,
        }
        parameter = json.dumps(data)
        headers = self.get_headers(url, parameter)
        req = requests.post(url=url, headers=headers, data=parameter, verify=False)
        req = req.json()

        return req

    def delete_dns_record(self, domain_name, domain_dns_value):
        root, _, acme_txt = extract_zone(domain_name)
        url = "https://www.cloudxns.net/api2/record/{}/{}".format(self.get_record_id(root, 'TXT'),
                                                                  self.get_domain_id(root))
        headers = self.get_headers(url, )
        req = requests.delete(url=url, headers=headers, verify=False)
        req = req.json()
        return req

    def get_record_id(self, domain_name, s_type='TXT'):
        url = "http://www.cloudxns.net/api2/record/{}?host_id=0&offset=0&row_num=2000".format(
            self.get_domain_id(domain_name))
        headers = self.get_headers(url, )
        req = requests.get(url=url, headers=headers, verify=False)
        req = req.json()
        for i in req['data']:
            if i['type'] == s_type:
                return i['record_id']
        return False
