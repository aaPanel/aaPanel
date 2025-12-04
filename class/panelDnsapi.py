# coding: utf-8
# +-------------------------------------------------------------------
# | aaPanel
# +-------------------------------------------------------------------
# | Copyright (c) 2015-2099 aaPanel(www.aapanel.com) All rights reserved.
# +-------------------------------------------------------------------
# | Author: aaPanel
# +-------------------------------------------------------------------
import ipaddress
import os
import re
import sys
import time
from datetime import datetime
from typing import Optional
from urllib.parse import urljoin

import requests

os.chdir("/www/server/panel")
sys.path.insert(0, "class/")
sys.path.insert(0, "class_v2/")

import public
from public.exceptions import HintException

__all__ = [
    "aaPanelDns",
    "NameSiloDns",
    "NameCheapDns",
    "CloudFlareDns",
    "PorkBunDns",
    "GodaddyDns",
]


class ExtractZoneTool(object):
    def __call__(self, domain_name):
        root, zone = public.split_domain_sld(domain_name)
        if not zone:
            acme_txt = "_acme-challenge"
        else:
            acme_txt = "_acme-challenge.%s" % zone
        return root, zone, acme_txt


extract_zone = ExtractZoneTool()


def sync_log(body, mode="a"):
    dns_sync_log = os.path.join(public.get_panel_path(), "logs/dns_sync.log")
    body += "\n"
    with open(dns_sync_log, mode) as f:
        f.write(body)


def white_kwargs(body: dict, kw_prefix: dict, kwargs: dict) -> dict:
    """
    kwargs:  create 从 kw获取, update 从 new_record 获取
    """
    # when create or update
    if kwargs.get("priority") and kwargs.get("priority") != -1:  # 接受其他关键参数
        if kw_prefix.get("priority"):
            body[kw_prefix.get("priority")] = int(kwargs.get("priority"))
    return body


class BaseDns(object):
    def __init__(self):
        self.dns_provider_name = self.__class__.__name__
        self.api_user = ""
        self.api_key = ""

    def log_response(self, response: requests.Response):
        try:
            log_body = response.json()
        except ValueError:
            log_body = response.content
        return log_body

    # =============== acme ======================
    def create_dns_record(self, domain_name: str, domain_dns_value: str) -> None:
        raise NotImplementedError("create_dns_record method must be implemented.")

    def delete_dns_record(self, domain_name: str, domain_dns_value: str) -> None:
        raise NotImplementedError("delete_dns_record method must be implemented.")

    # =============== 域名管理同步信息 =====================
    def get_domains(self, **kwargs) -> list:
        raise NotImplementedError("get_domains method must be implemented.")

    def get_dns_record(self, domain_name: str) -> list:
        raise NotImplementedError("get_dns_record method must be implemented.")

    def create_org_record(
            self, domain_name: str, record: str, record_value: str, record_type: str, ttl: int, **kwargs
    ) -> Optional[dict]:
        raise NotImplementedError("create_org_record method must be implemented.")

    def remove_record(self, domain_name: str, record: str, record_type: str, **kwargs) -> Optional[dict]:
        raise NotImplementedError("remove_record method must be implemented.")

    def update_record(self, domain_name: str, record: dict, new_record: dict, **kwargs) -> Optional[dict]:
        raise NotImplementedError("update_record method must be implemented.")

    def raise_resp_error(self, response: requests.Response):
        raise HintException(
            "Error {dns_name}: status_code={status_code} response={response}".format(
                dns_name=self.dns_provider_name,
                status_code=response.status_code,
                response=self.log_response(response),
            )
        )

    def verify(self) -> Optional[bool]:
        try:
            self.get_domains()
        except Exception:
            raise HintException("Verify fail, please check your Api Account and Password")
        return True


class aaPanelDns(BaseDns):
    """
    遵循 ssl v2入参, 转发dnsmanager
    """
    dns_provider_name = "aapanel"
    kw_prefix = {
        "priority": "priority"
    }

    def __init__(self, api_user: str = None, api_key: str = None, **kwargs):
        super().__init__()
        self.api_user = api_user
        self.api_key = api_key
        from ssl_dnsV2.dns_manager import DnsManager
        self.manager = DnsManager()

    # ============== acme ======================
    def create_dns_record(self, domain_name, domain_dns_value):
        domain_name = domain_name.lstrip("*.")
        _, _, acme_txt = extract_zone(domain_name)
        self.create_org_record(
            domain_name=domain_name,
            record=acme_txt,
            record_value=domain_dns_value,
            record_type="TXT",
            ttl=600,
        )

    def delete_dns_record(self, domain_name, domain_dns_value) -> None:
        domain_name = domain_name.lstrip("*.")
        root, _, acme_txt = extract_zone(domain_name)
        self.remove_record(root, acme_txt, "TXT", record_value=domain_dns_value)

    # =============== 域名管理 ====================
    def get_domains(self) -> list:
        return self.manager.get_domains()

    def get_dns_record(self, domain_name: str) -> list:
        records = []
        for x in self.manager.parser.get_zones_records(domain_name):
            try:
                # todo 更多类型特俗处理
                if x.get("type") == "SOA":
                    continue
                if x.get("type") == "MX":
                    priority = re.findall(r"^\s*(\d+)\s+", x.get("value"))
                    if priority:
                        x["priority"] = int(priority[0])
                record = {
                    "record": x.get("name"),
                    "record_type": x.get("type"),
                    "record_value": x.get("value"),
                    "ttl": x.get("ttl"),
                    "proxy": x.get("proxy", -1),
                    "priority": x.get("priority", -1),
                }
                records.append(record)
            except Exception as e:
                public.print_log(f"aaPanelDns get_dns_record error: {e}")
                continue
        return records

    def create_org_record(self, domain_name, record, record_value, record_type, ttl=600, **kwargs):
        root, _, _ = extract_zone(domain_name)
        body = {
            "name": record,
            "type": record_type.upper(),
            "value": record_value,
            "ttl": ttl,
            "proxy": kwargs.get("proxy", -1),
            "priority": kwargs.get("priority", -1),
        }
        body = white_kwargs(body, self.kw_prefix, kwargs)
        try:
            self.manager.add_record(
                domain=root, **body
            )
            return {"status": True, "msg": "Success"}
        except HintException as he:
            return {"status": False, "msg": str(he)}
        except Exception as e:
            return {"status": False, "msg": str(e)}

    def remove_record(self, domain_name, record, record_type="TXT", **kwargs) -> dict:
        root, _, _ = extract_zone(domain_name)
        body = {
            "name": record,
            "type": record_type.upper(),
        }
        if kwargs.get("record_value"):
            body["value"] = kwargs.get("record_value")
        try:
            self.manager.delete_record(
                domain=root, **body
            )
            return {"status": True, "msg": "Success"}
        except HintException as he:
            return {"status": False, "msg": str(he)}
        except Exception as e:
            return {"status": False, "msg": str(e)}

    def update_record(self, domain_name: str, record: dict, new_record: dict, **kwargs):
        domain, _, _ = extract_zone(domain_name)
        body = {
            "name": record.get("record"),
            "type": record.get("record_type").upper(),
            "value": record.get("record_value"),
            "ttl": record.get("ttl", 600),
            "priority": record.get("priority", 10),
            "proxy": record.get("proxy", -1),
            "new_record": {
                "name": new_record.get("record"),
                "type": new_record.get("record_type").upper(),
                "value": new_record.get("record_value"),
                "ttl": new_record.get("ttl", 600),
                "proxy": new_record.get("proxy", -1),
                "priority": new_record.get("priority", -1),
            }
        }
        try:
            self.manager.update_record(
                domain=domain, **body
            )
            return {"status": True, "msg": "Success"}
        except HintException as he:
            return {"status": False, "msg": str(he)}
        except Exception as e:
            return {"status": False, "msg": str(e)}

    def verify(self) -> bool:
        if os.path.exists(public.get_panel_path() + "/class_v2/ssl_dnsV2/aadns.pl"):
            return True
        return False


# noinspection PyUnusedLocal
class NameCheapDns(BaseDns):
    dns_provider_name = "namecheap"
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
        ip = public.GetLocalIp()
        if isinstance(ipaddress.ip_address(ip), ipaddress.IPv6Address):
            raise HintException("Namecheap Api does not support IPv6")
        return ip

    def _get_hosts(self, domain_name) -> list:
        time.sleep(2)  # 限流
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
    def create_dns_record(self, domain_name: str, domain_dns_value: str) -> None:
        # acme 调用
        domain_name = domain_name.lstrip("*.")
        _, _, acme_txt = extract_zone(domain_name)
        self.create_org_record(
            domain_name=domain_name,
            record=acme_txt,
            record_value=domain_dns_value,
            record_type="TXT",
        )

    def delete_dns_record(self, domain_name, dns_value=None) -> None:
        # 移除挑战值
        _, _, dns_name = extract_zone(domain_name)
        self.remove_record(domain_name, dns_name, "TXT")

    # =============== 域名管理 ====================
    @staticmethod
    def _generate_xml_tree(resp_body: str, findall: str):
        import xml.etree.ElementTree as EtTree
        from xml.etree.ElementTree import ParseError as ETParseError
        # noinspection HttpUrlsUsage
        tree_root = resp_body.replace('xmlns="http://api.namecheap.com/xml.response"', '')
        try:
            targets = EtTree.fromstring(tree_root).findall(findall)
            return targets
        except ETParseError:
            raise HintException("Error parsing XML response from Namecheap API")
        except Exception as e:
            raise HintException(e)

    def get_domains(self, verify: bool = False) -> list | bool:
        # 获取账号下所有域名, 判断域名nameserver归属, 并且所有返回均为xml
        domains = []
        page = 1
        while 1:
            params = {
                "ApiUser": self.api_user,
                "ApiKey": self.api_key,
                "UserName": self.api_user,
                "Command": "namecheap.domains.getList",  # returns a list of domains for the particular user
                "ClientIp": self._get_local_ip(),
                "Page": page,
                "PageSize": 100,
                "SortBy": "NAME",
            }
            resp = requests.get(url=self.base_url, params=params, timeout=self.timeout)
            if "API Key is invalid or API access has not been enabled" in resp.text:
                raise HintException("API Key is invalid or API access has not been enabled")

            if "ERROR" in resp.text:
                try:
                    err_msg = re.search(r"<Errors>(.*?)</Errors>", resp.text, re.DOTALL).group(1)
                except:
                    err_msg = resp.text
                raise HintException(err_msg)

            if verify:
                return True

            try:
                temp_domains = self._generate_xml_tree(resp.text, ".//Domain")
            except HintException as hit:
                public.print_log(hit)
                continue

            if not temp_domains:
                break

            time.sleep(3)  # 限流
            domains.extend(temp_domains)
            page += 1

        for expired in [d.get("Name", "") for d in domains if d.get("IsExpired") == "true"]:
            sync_log(f"|-- warning: [{expired}] is Expired, Skip It...")

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

                time.sleep(3)  # 限流
                for t in self._generate_xml_tree(resp.text, ".//DomainDNSGetListResult"):
                    if t.get("Domain") == d:
                        if t.get("IsUsingOurDNS") == "true":
                            res.append(d)
                            break
                        else:
                            sync_log(
                                f"|-- warning: [{t.get('Domain')}] is Not Using NameCheap DNS, Skip It..."
                            )
                            break
            except Exception as e:
                public.print_log(f"get_domains error {e}")
                continue
        return res

    # nc 所有record 不带域名
    def get_dns_record(self, domain_name: str):
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
        # nc 单独处理
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
        return self.__set_hosts_with_params(domain_name, params)

    # 删除record
    def remove_record(self, domain_name, record, record_type="TXT", **kwargs) -> dict:
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
    def update_record(self, domain_name: str, record: dict, new_record: dict, **kwargs):
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
                    host[f"{self.kw_prefix.get("priority")}{index + 1}"] = new_record.get("priority")
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


# noinspection PyUnusedLocal
class CloudFlareDns(BaseDns):
    dns_provider_name = "cloudflare"
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
            if i["name"] == domain_name:  # 完全匹配
                setattr(self, "cf_zone_id", i["id"])
                return

        if self.cf_zone_id is None:
            raise HintException(
                "Error unable to get DNS zone for domain_name={domain_name} "
                ", please check your Api Account and Password: status_code={status_code} response={response}".format(
                    domain_name=domain_name,
                    status_code=find_dns_zone_response.status_code,
                    response=self.log_response(find_dns_zone_response),
                )
            )

    # =============== acme ======================

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
        domain_name, _, acme_txt = extract_zone(domain_name)
        acme_txt = acme_txt + "." + domain_name
        self.remove_record(domain_name, acme_txt, "TXT")

    # =============== 域名管理 ====================

    def get_domains(self) -> list:
        url = self.cf_base_url + "zones?status=active&order=name"
        headers = self._get_auth_headers()
        domains = []
        page = 1
        count = 1
        fail_count = 0
        while count != 0:
            params = {"page": page, "per_page": 50}
            try:
                res = requests.get(url, headers=headers, params=params, timeout=self.time_out)
                time.sleep(1)  # 限流
                resp = res.json()
                if not resp.get("success"):
                    fail_count += 1
                    if fail_count >= 3:
                        raise HintException("get domains fail")
                    else:
                        time.sleep(1)
                        continue
                result = resp.get("result", [])
                count = resp.get("result_info", {}).get("count", 0)
                domains.extend([i.get("name", "") for i in result])
                page += 1
            except Exception as e:
                public.print_log(f"cloudflare get_domains error {e}")
                raise HintException(e)
        return domains

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
                public.print_log(f"get_dns_record error {e}")
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
        body = white_kwargs(body, self.kw_prefix, kwargs)  # 接受其他关键参数

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
    def remove_record(self, domain_name, record, record_type="TXT", **kwargs) -> dict:
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
                body = white_kwargs(body, self.kw_prefix, new_record)

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


# noinspection PyUnusedLocal
class PorkBunDns(BaseDns):
    dns_provider_name = "porkbun"
    kw_prefix = {
        "priority": "prio"
    }

    def __init__(self, api_user, api_key, **kwargs):
        super().__init__()
        self.api_user = api_user  # secretapikey
        self.api_key = api_key
        self.timeout = 30
        self.base_url = "https://api.porkbun.com/api/json/v3"

    def _json_data(self) -> dict:
        return {
            "secretapikey": self.api_user,
            "apikey": self.api_key,
        }

    def _retrieve_record_by_domain(self, domain_name: str) -> list:
        domain_name, _, _ = extract_zone(domain_name)
        url = self.base_url + f"/dns/retrieve/{domain_name}"
        data = self._json_data()
        try:
            response = requests.post(url, json=data, timeout=self.timeout)
            time.sleep(1)  # 限流
            res = response.json()
            if res.get("status") != "SUCCESS":
                raise HintException("get record fail")
            return res.get("records", [])
        except Exception as err:
            raise HintException(err)

    # =============== acme ======================
    def create_dns_record(self, domain_name, domain_dns_value) -> None:
        _, _, acme_txt = extract_zone(domain_name)
        self.create_org_record(
            domain_name=domain_name,
            record=acme_txt,
            record_value=domain_dns_value,
            record_type="TXT",
        )

    def delete_dns_record(self, domain_name, domain_dns_value) -> None:
        domain_name, _, acme_txt = extract_zone(domain_name)
        acme_txt = acme_txt + "." + domain_name
        self.remove_record(domain_name, acme_txt, "TXT")

    # =============== 域名管理 ====================
    def get_domains(self) -> list:
        url = self.base_url + "/domain/listAll"
        data = self._json_data()

        response = requests.post(url, json=data, timeout=self.timeout)
        res = response.json()
        if not res.get("status") == "SUCCESS":
            raise HintException("get domains fail")

        res_domains = []
        for d in res.get("domains"):
            if d.get("status") != "ACTIVE":
                sync_log(f"|-- warning: [{d.get('domain')}] is Not ACTIVE, Skip It...")
                continue

            if d.get("expireDate") and d.get("expireDate") < datetime.now().strftime("%Y-%m-%d %H:%M:%S"):
                sync_log(f"|-- warning: [{d.get('domain')}] is Expired, Skip It...")
                continue

            try:
                detail_url = self.base_url + f"/domain/getNs/{d.get('domain')}"
                detail_resp = requests.post(detail_url, json=data, timeout=self.timeout)
                detail_res = detail_resp.json()
                if not detail_res.get("status") == "SUCCESS":
                    continue

                if all("porkbun.com" in d.lower() for d in detail_res.get("ns")):
                    res_domains.append(d.get("domain"))
                else:
                    sync_log(f"|-- warning: [{d.get('domain')}] is Not Using Porkbun DNS, Skip It...")

            except Exception as err:
                public.print_log(f"{self.dns_provider_name} get domains detail error {err}")
                continue
        res_domains.sort()
        return res_domains

    def get_dns_record(self, domain_name: str) -> list:
        try:
            return [
                {
                    "record": x.get("name"),
                    "record_value": x.get("content"),
                    "record_type": x.get("type"),
                    "proxy": False,
                    "ttl": int(x.get("ttl", 1)),
                    "priority": int(x.get("prio", -1)) if x.get("prio") not in [None, "0"] else -1,
                } for x in self._retrieve_record_by_domain(domain_name)
            ]
        except Exception as err:
            public.print_log(f"{self.dns_provider_name} get_domains error {err}")
            raise HintException(err)

    def create_org_record(self, domain_name, record, record_value, record_type, ttl=1, **kwargs):
        domain_name, _, _ = extract_zone(domain_name)
        url = self.base_url + f"/dns/create/{domain_name}"
        data = self._json_data()
        data.update({
            "name": record,
            "type": record_type,
            "content": record_value,
            "ttl": 600 if ttl == 1 else int(ttl),
        })
        data = white_kwargs(data, self.kw_prefix, kwargs)  # 接受其他关键参数

        try:
            response = requests.post(url, json=data, timeout=self.timeout)
            res = response.json()
            if res.get("status") != "SUCCESS":
                return {"status": False, "msg": res.get("message")}
            return {"status": True, "msg": res.get("status")}
        except Exception as err:
            return {"status": False, "msg": err}

    def remove_record(self, domain_name, record, record_type="TXT", **kwargs) -> dict:
        # record 跟cf一样, 需要带上域名
        try:
            domain, _, _ = extract_zone(domain_name)
            res = {"status": "False", "msg": "Dns Record is Not Found."}
            for r in self._retrieve_record_by_domain(domain_name):
                if r.get("name") == record and r.get("type") == record_type:
                    url = self.base_url + f"/dns/delete/{domain}/{int(r.get('id'))}"
                    response = requests.post(url, json=self._json_data(), timeout=self.timeout)
                    res = response.json()
                    break

            if res.get("status") != "SUCCESS":
                return {"status": False, "msg": res.get("message")}
            return {"status": True, "msg": res.get("status", "SUCCESS")}

        except Exception as err:
            public.print_log(f"{self.dns_provider_name} remove record error {err}")
            return {"status": False, "msg": err}

    def update_record(self, domain_name, record: dict, new_record: dict, **kwargs):
        try:
            domain, _, _ = extract_zone(domain_name)
            res = {"status": "False", "msg": "Dns Record is Not Found."}
            data = self._json_data()
            data.update({
                "name": new_record.get("record"),
                "type": new_record.get("record_type"),
                "content": new_record.get("record_value"),
                "ttl": 600 if new_record.get("ttl") == 1 else int(new_record.get("ttl")),
            })
            data = white_kwargs(data, self.kw_prefix, new_record)  # 接受其他关键参数

            for r in self._retrieve_record_by_domain(domain_name):
                if all([
                    r.get("name") == record.get("record"),
                    r.get("type") == record.get("record_type"),
                    r.get("content") == record.get("record_value"),
                ]):
                    url = self.base_url + f"/dns/edit/{domain}/{int(r.get('id'))}"
                    response = requests.post(url, json=data, timeout=self.timeout)
                    res = response.json()
                    break

            if res.get("status") != "SUCCESS":
                return {"status": False, "msg": res.get("message")}
            return {"status": True, "msg": res.get("status", "SUCCESS")}

        except Exception as err:
            public.print_log(f"{self.dns_provider_name} remove record error {err}")
            return {"status": False, "msg": err}

    def verify(self):
        try:
            url = self.base_url + "/ping"
            data = self._json_data()
            response = requests.post(url, json=data, timeout=self.timeout)
            res = response.json()
            if res.get("status") == "SUCCESS":
                return True
        except:
            pass
        raise HintException("Verify fail, please check your Api Account and Password")


# noinspection PyUnusedLocal
class NameSiloDns(BaseDns):
    dns_provider_name = "namesilo"
    kw_prefix = {
        "priority": "rrdistance"
    }

    def __init__(self, api_user, api_key, **kwargs):
        super().__init__()
        self.api_user = api_user
        self.api_key = api_key
        self.timeout = 30
        self.base_url = "https://www.namesilo.com/api"
        self.ver_type_key = f"version=1&type=json&key={api_key}"

    def _remote_record(self, domain_name: str) -> list:
        try:
            url = f"{self.base_url}/dnsListRecords?{self.ver_type_key}&domain={domain_name}"
            response = requests.get(url, params={"page": 1, "pageSize": 100})
            time.sleep(1)  # 限流
            res = response.json()
            if res.get("reply").get("code") != 300:
                raise HintException(res.get("reply").get("detail"))
            return res.get("reply", {}).get("resource_record", [])
        except Exception as e:
            public.print_log(f"get_dns_record error {e}")
            raise HintException(e)

    def _find_rrid(self, domain_name: str, record: dict) -> str:
        rrid = ""
        try:
            for r in self._remote_record(domain_name):
                if all([
                    r.get("host") == record.get("record"),
                    r.get("type") == record.get("record_type"),
                ]):
                    rrid = r.get("record_id")
                    break
        except Exception as e:
            public.print_log(f"NameSilo find rrid error {e}")
        return rrid

    # =============== acme ======================
    def create_dns_record(self, domain_name, domain_dns_value) -> None:
        _, _, acme_txt = extract_zone(domain_name)
        self.create_org_record(
            domain_name=domain_name,
            record=acme_txt,
            record_value=domain_dns_value,
            record_type="TXT",
            ttl=3600,
        )

    def delete_dns_record(self, domain_name, domain_dns_value) -> None:
        domain_name, _, acme_txt = extract_zone(domain_name)
        acme_txt = acme_txt + "." + domain_name
        self.remove_record(domain_name, acme_txt, "TXT")

    # =============== 域名管理 ====================
    def get_domains(self, verify: bool = False) -> list | bool:
        url = f"{self.base_url}/listDomains?{self.ver_type_key}&withBid=1&skipExpired=1"
        page = 1
        domains = []
        fail_count = 0
        while 1:
            params = {"page": page, "pageSize": 100}
            try:
                response = requests.get(url, params=params)
                if "Invalid API Key" in response.text or "Permission denied" in response.text:
                    raise HintException("Invalid API Key, Verify fail, please check your Api Key")
                res = response.json()
                time.sleep(1)  # 限流
                if res.get("reply").get("code") != 300:
                    fail_count += 1
                    if fail_count >= 2:
                        raise HintException(res.get("reply").get("detail"))
                    else:
                        continue
                if verify:
                    return True
                temp_domains = res["reply"].get("domains")
                if not temp_domains:
                    break
                temp_domains = [temp_domains] if isinstance(temp_domains, dict) else temp_domains
                domains.extend(temp_domains)
                page += 1
            except Exception as e:
                raise HintException(f"get domains errro {e}")
        try:
            domains = sorted(domains, key=lambda x: x["domain"]["domain"])
        except:
            pass
        res_domains = []
        detail_url_pre = f"{self.base_url}/getDomainInfo?{self.ver_type_key}"
        for d in domains:
            try:
                d = d.get("domain", {})
                if d.get("expires") and d.get("expires") < datetime.now().strftime("%Y-%m-%d"):
                    sync_log(f"|-- warning: [{d.get('domain')}] is Expired, Skip It...")
                    continue
                # domain detail info
                detail_url = f"{detail_url_pre}&domain={d.get("domain")}"
                detail_resp = requests.get(detail_url)
                time.sleep(1)  # 限流
                rp = detail_resp.json()
                if rp.get("reply", {}).get("code") != 300:
                    continue
                if all(
                        "DNSOWL.COM" in n.get("nameserver", "").upper() for n in rp["reply"].get("nameservers", [])
                ):
                    res_domains.append(d.get("domain"))
                else:
                    sync_log(
                        f"|-- warning: [{d.get('domain')}] is Not Using NameSilo DNS, Skip It..."
                    )
            except Exception as err:
                public.print_log(f"{self.dns_provider_name} get domains detail error {err}")
                continue

        return res_domains

    def get_dns_record(self, domain_name: str) -> list:
        domain_name, _, _ = extract_zone(domain_name)
        try:
            records = self._remote_record(domain_name)
            return [
                {
                    "record": x.get("host"),
                    "record_value": x.get("value"),
                    "record_type": x.get("type"),
                    "proxy": False,
                    "ttl": int(x.get("ttl", 1)),
                    "priority": int(x.get("distance", -1)) if x.get("distance") not in [None, 0] else -1,
                } for x in records
            ]
        except Exception as e:
            public.print_log(f"get_dns_record error {e}")
            raise HintException(e)

    def create_org_record(self, domain_name, record, record_value, record_type, ttl=1, **kwargs):
        domain_name, _, _ = extract_zone(domain_name)
        try:
            url = f"{self.base_url}/dnsAddRecord?{self.ver_type_key}&domain={domain_name}"
            params = {
                "rrhost": record,
                "rrvalue": record_value,
                "rrtype": record_type,
                "rrttl": 7207 if int(ttl) == 1 else int(ttl),  # default is 7207
            }
            params = white_kwargs(params, self.kw_prefix, kwargs)  # 接受其他关键参数
            response = requests.get(url, params=params, timeout=self.timeout)
            resp = response.json()
            if resp.get("reply").get("code") != 300:
                return {"status": False, "msg": resp.get("reply").get("detail")}

            return {"status": True, "msg": response.json()}
        except Exception as e:
            return {"status": False, "msg": str(e)}

    def remove_record(self, domain_name: str, record: str, record_type: str, **kwargs) -> dict:
        domain_name, _, _ = extract_zone(domain_name)
        try:
            rrid = self._find_rrid(domain_name, {"record": record, "record_type": record_type})
            url = f"{self.base_url}/dnsDeleteRecord?{self.ver_type_key}&domain={domain_name}&rrid={rrid}"
            response = requests.get(url, timeout=self.timeout)
            resp = response.json()
            if resp.get("reply").get("code") != 300:
                return {"status": False, "msg": resp.get("reply").get("detail")}
            return {"status": True, "msg": resp.get("reply").get("detail")}
        except Exception as e:
            return {"status": False, "msg": str(e)}

    def update_record(self, domain_name: str, record: dict, new_record: dict, **kwargs):
        domain_name, _, _ = extract_zone(domain_name)
        try:
            rrid = self._find_rrid(domain_name, record)
            if not rrid:
                return {"status": False, "msg": "Dns Record Not Found!"}

            url = f"{self.base_url}/dnsUpdateRecord?{self.ver_type_key}&domain={domain_name}"
            params = {
                "rrid": rrid,
                "rrhost": new_record.get("record"),
                "rrvalue": new_record.get("record_value"),
                "rrtype": new_record.get("record_type"),
                "rrttl": 7207 if new_record.get("ttl") == 1 else int(new_record.get("ttl")),  # default is 7207
            }
            params = white_kwargs(params, self.kw_prefix, new_record)  # 接受其他关键参数
            response = requests.get(url, params=params, timeout=self.timeout)
            resp = response.json()
            if resp.get("reply").get("code") != 300:
                return {"status": False, "msg": resp.get("reply").get("detail")}
            return {"status": True, "msg": resp.get("reply").get("detail")}
        except Exception as e:
            return {"status": False, "msg": str(e)}

    def verify(self) -> bool:
        try:
            self.get_domains(verify=True)
        except Exception as e:
            raise HintException(e)
        return True


class GodaddyDns(BaseDns):
    dns_provider_name = "godaddy"
    kw_prefix = {
        "priority": "priority"
    }

    def __init__(self, api_user, api_key, **kwargs):
        super().__init__()
        self.api_user = api_user  # secret key
        self.api_key = api_key
        self.timeout = 30
        # self.base_url = "https://api.ote-godaddy.com"
        self.base_url = "https://api.godaddy.com"

        self.headers = {
            "Authorization": f"sso-key {api_key}:{api_user}",
            "Accept": "application/json",
            "Content-Type": "application/json",
        }

    def _make_request(self, method, endpoint, payload=None):
        url = f"{self.base_url}{endpoint}"
        response = requests.request(method, url, headers=self.headers, json=payload)
        if response.status_code in [200, 204]:
            return response
        if response.json().get("code") == "UNABLE_TO_AUTHENTICATE":
            # godaddy api 需要拥有50个域名方可调用, 官方链接说明
            # https://www.godaddy.com/zh/help/how-do-i-access-domain-related-apis-42424
            raise Exception('GoDaddy API have been rejected, '
                            'Official Documentation link:\n'
                            '"https://www.godaddy.com/zh/help/how-do-i-access-domain-related-apis-42424"')
        raise Exception(f"Godaddy API Error {response.status_code}: {response.text}")

    # =============== acme ======================
    def create_dns_record(self, domain_name, domain_dns_value):
        # acme 调用
        domain_name = domain_name.lstrip("*.")
        self.create_org_record(
            domain_name=domain_name,
            record="_acme-challenge." + domain_name,
            record_value=domain_dns_value,
            record_type="TXT",
            ttl=600,
        )

    def delete_dns_record(self, domain_name, domain_dns_value):
        # 移除挑战值
        domain_name, _, acme_txt = extract_zone(domain_name)
        acme_txt = acme_txt + "." + domain_name
        self.remove_record(domain_name, acme_txt, "TXT")

    # =============== ote test ==================
    def ote_buy_domain(self, domain_name):
        if "ote" not in self.base_url:
            raise HintException("Only support ote env")
        url = self.base_url + f"/v1/domains/purchase"
        data = {
            "domain": domain_name,
            "consent": {
                "agreementKeys": [
                    "DNRA"
                ],
                "agreedBy": "bt-dev3",
                "agreedAt": datetime.utcnow().isoformat() + "Z"
            },
            "period": 1,
            "renewAuto": False,
            "privacy": False,
            "contactRegistrant": {
                "nameFirst": "abc",
                "nameLast": "abc",
                "email": "abc@example.com",
                "phone": "+1.1234567890",
                "addressMailing": {
                    "address1": "123 Main St",
                    "city": "town",
                    "state": "AZ",
                    "postalCode": "85001",
                    "country": "US"
                }
            }
        }
        try:
            response = requests.post(url, headers=self.headers, json=data, timeout=self.timeout)
            res = response.json()
            if response.status_code != 200:
                raise HintException(res.get("message", "buy domain fail"))
            return res
        except Exception as e:
            raise HintException(e)

    # =============== 域名管理 ====================
    def get_domains(self) -> list:
        try:
            res = self._make_request("GET", "/v1/domains").json()
            domains = []
            for domain in res:
                if domain.get("status") != "ACTIVE":
                    sync_log(f"|-- warning: [{domain.get('domain')}] is Not ACTIVE, Skip It...")
                    continue
                if domain.get("expires") and domain.get("expires") < datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ"):
                    sync_log(f"|-- warning: [{domain.get('domain')}] is Expired, Skip It...")
                    continue
                domains.append(domain.get("domain"))
            domains.sort()
            return domains
        except Exception as e:
            raise HintException(f"get domains error {e}")

    def get_dns_record(self, domain_name: str) -> list:
        domain_name, _, _ = extract_zone(domain_name)
        try:
            res = self._make_request(
                "GET", f"/v1/domains/{domain_name}/records"
            ).json()
            return [
                {
                    "record": x.get("name"),
                    "record_value": x.get("data"),
                    "record_type": x.get("type"),
                    "ttl": int(x.get("ttl", 1)),
                    "priority": int(x.get("priority", -1)) if x.get("priority") not in [None, 0] else -1,
                    "proxy": -1,
                } for x in res
            ]
        except Exception as e:
            raise HintException(e)

    def create_org_record(self, domain_name, record, record_value, record_type, ttl=1, **kwargs):
        domain_name, _, _ = extract_zone(domain_name)
        body = {
            "data": record_value,
            "name": record,
            "ttl": 600 if ttl == 1 else int(ttl),
            "type": record_type
        }
        body = white_kwargs(body, self.kw_prefix, kwargs)
        try:
            self._make_request(
                "PATCH",
                f"/v1/domains/{domain_name}/records",
                payload=[body]
            )
            return {"status": True, "msg": "success"}
        except Exception as e:
            raise HintException(e)

    def remove_record(self, domain_name, record, record_type="TXT", **kwargs) -> dict:
        domain_name, _, _ = extract_zone(domain_name)
        try:
            self._make_request(
                "DELETE", f"/v1/domains/{domain_name}/records/{record_type}/{record}"
            )
            return {"status": True, "msg": "success"}
        except Exception as e:
            raise HintException(e)

    def update_record(self, domain_name, record: dict, new_record: dict, **kwargs):
        domain_name, _, _ = extract_zone(domain_name)
        try:
            body = {
                "data": new_record.get("record_value"),
                "name": new_record.get("record"),
                "ttl": 600 if new_record.get("ttl") == 1 else int(new_record.get("ttl")),
                "type": new_record.get("record_type")
            }
            body = white_kwargs(body, self.kw_prefix, new_record)
            self._make_request(
                "PUT",
                f"/v1/domains/{domain_name}/records/{record['record_type']}/{record['record']}",
                payload=[body]
            )
            return {"status": True, "msg": "success"}
        except Exception as e:
            raise HintException(e)

    def verify(self) -> Optional[bool]:
        try:
            self.get_domains()
        except Exception as e:
            raise HintException(f"Verify fail, please check your Api Key and Secret Key: {e}")
        return True
