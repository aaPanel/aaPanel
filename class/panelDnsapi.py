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
    "ClouDns",
    "SpaceShipDNS",
    "AmazonRoute53Dns",
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

    def __init__(self, api_user: str = None, api_key: str = None, **kwargs):  # noqa
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
        if self.limit:
            return {"Authorization": "Bearer " + self.api_key}
        else:  # api limit False, is global permissions
            return {"X-Auth-Email": self.api_user, "X-Auth-Key": self.api_key}

    def find_dns_zone(self, domain_name):
        domain = domain_name.lstrip("*.")
        url = self.cf_base_url + "zones?status=active&per_page=20"
        headers = self._get_auth_headers()
        page = 1

        while True:
            paginated_url = url + f"&page={page}"
            find_dns_zone_response = requests.get(paginated_url, headers=headers, timeout=self.time_out)
            if find_dns_zone_response.status_code != 200:
                raise HintException(
                    "Error find cloudflare dns zone, please check your Api Account and Password:"
                    " status_code={status_code} response={response}".format(
                        status_code=find_dns_zone_response.status_code,
                        response=self.log_response(find_dns_zone_response),
                    )
                )
            result = find_dns_zone_response.json()["result"]

            matched_zones = [
                x for x in result if domain == x.get("name") or domain.endswith("." + x.get("name"))
            ]
            if matched_zones:
                # 优先最长匹配, max时len相等, 即eq, not eq时max为最精确
                best_match = max(matched_zones, key=lambda x: len(x.get("name", "")))
                self.cf_zone_id = best_match.get("id")
                return

            if len(result) < 20:
                break
            page += 1

        raise HintException(
            "Error unable to get DNS zone for domain={domain}".format(
                domain=domain
            )
        )

    # =============== acme ======================

    @staticmethod
    def _build_cf_value(record_type: str, record_value: str, priority: int = -1) -> dict:
        """
        A/AAAA/CNAME/NS/TXT -> {"content": value}
        MX -> {"data": {"priority": N, "target": value}}
        CAA -> {"data": {"flags": N, "tag": tag, "value": value}}
        """
        record_type = str(record_type or "").upper()

        if record_type == "MX":
            pref = priority if str(priority) not in {"", "-1", "None"} else 10
            return {"data": {"priority": pref, "target": record_value}}

        if record_type == "CAA":
            parts = str(record_value or "").strip().split(None, 2)
            if len(parts) == 3:
                flag_str, tag, caa_val = parts
                try:
                    flags = int(flag_str)
                except ValueError:
                    flags = 0
                return {"data": {"flags": flags, "tag": tag, "value": caa_val}}
            return {"content": record_value}

        return {"content": record_value}

    @staticmethod
    def _parse_cf_value(record_type: str, item: dict) -> str:
        """从返回的记录中解析值"""
        record_type = str(record_type or "").upper()
        data = item.get("data")
        if record_type == "MX" and data:
            return str(data.get("target", ""))
        if record_type == "CAA" and data:
            flags = data.get("flags", 0)
            tag = data.get("tag", "")
            val = data.get("value", "")
            return f"{flags} {tag} {val}"
        return str(item.get("content", ""))

    @staticmethod
    def _parse_cf_priority(record_type: str, item: dict) -> int:
        """提取优先级: MX -> data.priority 或顶层 priority"""
        if str(record_type or "").upper() == "MX":
            data = item.get("data", {})
            pref = data.get("priority", item.get("priority", -1))
        else:
            pref = item.get("priority", -1)
        try:
            return int(pref)
        except (TypeError, ValueError):
            return -1

    def create_dns_record(self, domain_name, domain_dns_value):
        # acme 调用
        domain_name = domain_name.lstrip("*.")
        self.find_dns_zone(domain_name)
        # CloudFlare 的 acme 记录名称是 _acme-challenge.{完整域名}
        acme_txt = "_acme-challenge." + domain_name
        url = urljoin(
            self.cf_base_url,
            "zones/{0}/dns_records".format(self.cf_zone_id),
        )
        headers = self._get_auth_headers()
        body = {
            "type": "TXT",
            "name": acme_txt,
            "content": str(domain_dns_value),
        }

        create_cloudflare_dns_record_response = requests.post(
            url, headers=headers, json=body, timeout=self.time_out
        )
        if create_cloudflare_dns_record_response.status_code != 200:
            raise HintException(
                "Error creating cloudflare dns record: status_code={status_code} response={response}".format(
                    status_code=create_cloudflare_dns_record_response.status_code,
                    response=self.log_response(create_cloudflare_dns_record_response),
                )
            )

    def delete_dns_record(self, domain_name, domain_dns_value):
        # 移除挑战值
        domain_name = domain_name.lstrip("*.")
        self.find_dns_zone(domain_name)
        # CloudFlare 的 acme 记录名称是 _acme-challenge.{完整域名}
        acme_txt = "_acme-challenge." + domain_name
        self.remove_record(domain_name, acme_txt, "TXT", record_value=domain_dns_value)

    # =============== 域名管理 ====================

    def get_domains(self) -> list:
        url = self.cf_base_url + "zones?status=active&order=name"
        headers = self._get_auth_headers()
        domains = []
        page = 1
        per_page = 50
        fail_count = 0
        while True:
            params = {"page": page, "per_page": per_page}
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
                domains.extend([i.get("name", "") for i in result])
                if len(result) < per_page:
                    break
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
                    url, headers=self._get_auth_headers(), params=params, timeout=self.time_out
                )
                data = response.json()
                if data.get("success"):
                    records = data.get("result", [])
                    for i in records:
                        r_type = i.get("type", "").upper()
                        # 跳过 SOA 和根 NS 记录
                        if r_type == "SOA":
                            continue
                        r_value = self._parse_cf_value(r_type, i)
                        priority = self._parse_cf_priority(r_type, i)
                        result.append({
                            "record": i.get("name", ""),
                            "record_value": r_value,
                            "record_type": r_type,
                            "proxy": i.get("proxied", False),
                            "priority": priority,
                            "ttl": i.get("ttl", 1),
                        })
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
        ttl_val = 600 if int(ttl) == 1 else int(ttl)
        priority = kwargs.get("priority", -1)

        body = {"name": record, "type": record_type, "ttl": ttl_val, "proxied": proxied}
        body.update(self._build_cf_value(record_type, record_value, priority))
        body = white_kwargs(body, self.kw_prefix, kwargs)

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
        if list_dns_response.status_code != 200:
            return {"status": False, "msg": f"HTTP {list_dns_response.status_code}: {list_dns_response.text}"}
        try:
            results = list_dns_response.json().get("result", [])
            if not results:
                return {"status": True, "msg": "Dns Record is empty."}

            # 如果提供了record_value，需要匹配正确的记录
            record_value = kwargs.get("record_value")
            if record_value:
                # 解析记录值以进行匹配
                for item in results:
                    parsed_value = self._parse_cf_value(record_type, item)
                    if parsed_value == record_value:
                        dns_record_id = item["id"]
                        url = self.cf_base_url + f"zones/{self.cf_zone_id}/dns_records/{dns_record_id}"
                        remove_res = requests.delete(url, headers=headers, timeout=self.time_out)
                        remove_res = remove_res.json()
                        if remove_res.get("success"):
                            return {"status": True, "msg": remove_res}
                        return {"status": False, "msg": str(remove_res.get("errors"))}
                # 没有找到匹配的记录
                return {"status": False, "msg": "Dns Record not found with specified value"}
            else:
                # 没有提供record_value，删除第一条匹配的记录
                dns_record_id = results[0]["id"]
                url = self.cf_base_url + f"zones/{self.cf_zone_id}/dns_records/{dns_record_id}"
                remove_res = requests.delete(url, headers=headers, timeout=self.time_out)
                remove_res = remove_res.json()
                if remove_res.get("success"):
                    return {"status": True, "msg": remove_res}
                return {"status": False, "msg": str(remove_res.get("errors"))}
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
            get_response = requests.get(get_url, headers=self._get_auth_headers(), timeout=self.time_out)
            get_result = get_response.json()
            if get_result.get("success") and get_result.get("result"):
                record_id = get_result["result"][0]["id"]
                update_url = self.cf_base_url + f"zones/{self.cf_zone_id}/dns_records/{record_id}"

                new_type = new_record.get("record_type", record_type)
                new_value = new_record.get("record_value", "")
                new_ttl = int(new_record.get("ttl", 600))
                if new_ttl == 1:
                    new_ttl = 600
                proxied = True if new_record.get("proxy") == 1 else False
                priority = new_record.get("priority", -1)

                body = {
                    "type": new_type,
                    "name": new_record.get("record"),
                    "ttl": new_ttl,
                    "proxied": proxied,
                }
                body.update(self._build_cf_value(new_type, new_value, priority))
                body = white_kwargs(body, self.kw_prefix, new_record)

                update_response = requests.put(update_url, headers=self._get_auth_headers(), json=body,
                                               timeout=self.time_out)
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
                # 如果没有任何记录，porkbun可能会返回错误
                if "domain not found" in res.get("message", "").lower():
                    return []
                raise HintException("get record fail")
            return res.get("records", [])
        except Exception as err:
            raise HintException(err)

    def _get_sub_domain(self, root: str, record: str) -> str:
        """
        标准化子域名处理：将record 转换为子域名部分
        例如: root="example.com", record="www.example.com" -> 返回 "www"
        例如: root="example.com", record="example.com" -> 返回 ""
        """
        if not record or record == root:
            return ""
        if record.endswith("." + root):
            return record[:-(len(root) + 1)]
        return record

    def _get_fqdn(self, root: str, record: str) -> str:
        """
        标准化为完整域名，用于匹配 retrieve 返回的结果
        """
        sub = self._get_sub_domain(root, record)
        return f"{sub}.{root}" if sub else root

    # =============== acme ======================
    def create_dns_record(self, domain_name, domain_dns_value) -> None:
        if domain_name.startswith("*."):
            domain_name = domain_name[2:]
        root, _, acme_txt = extract_zone(domain_name)
        self.create_org_record(
            domain_name=root,
            record=acme_txt,
            record_value=domain_dns_value,
            record_type="TXT",
        )

    def delete_dns_record(self, domain_name, domain_dns_value) -> None:
        if domain_name.startswith("*."):
            domain_name = domain_name[2:]
        root, _, acme_txt = extract_zone(domain_name)
        fqdn = f"{acme_txt}.{root}" if acme_txt else root
        self.remove_record(root, fqdn, "TXT")

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
            if d.get("expireDate") and d.get("expireDate") < datetime.now().strftime("%Y-%m-%d %H:%M:%S") and \
                    d.get("expireDate") != "0000-00-00 00:00:00":
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
                    "record": x.get("name"),  # Porkbun 返回的是 FQDN
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
        root, _, _ = extract_zone(domain_name)
        sub_name = self._get_sub_domain(root, record)

        url = self.base_url + f"/dns/create/{root}"
        data = self._json_data()
        data.update({
            "name": sub_name,
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
        try:
            root, _, _ = extract_zone(domain_name)
            # 无论输入,都标准化为 FQDN 进行匹配
            target_fqdn = self._get_fqdn(root, record).lower()
            res = {"status": "False", "msg": "Dns Record is Not Found."}
            for r in self._retrieve_record_by_domain(domain_name):
                if r.get("name", "").lower() == target_fqdn and r.get("type", "").lower() == record_type.lower():
                    url = self.base_url + f"/dns/delete/{root}/{int(r.get('id'))}"
                    response = requests.post(url, json=self._json_data(), timeout=self.timeout)
                    res = response.json()
                    break

            if res.get("status") != "SUCCESS":
                return {"status": False, "msg": res.get("message", "Fail, please try again later.")}
            return {"status": True, "msg": res.get("status", "SUCCESS")}

        except Exception as err:
            public.print_log(f"{self.dns_provider_name} remove record error {err}")
            return {"status": False, "msg": err}

    def update_record(self, domain_name, record: dict, new_record: dict, **kwargs):
        try:
            root, _, _ = extract_zone(domain_name)
            # 无论输入,都标准化为 FQDN 进行匹配
            old_fqdn = self._get_fqdn(root, record.get("record")).lower()

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
                    r.get("name", "").lower() == old_fqdn,
                    r.get("type", "").lower() == record.get("record_type", "").lower(),
                    r.get("content") == record.get("record_value"),
                ]):
                    url = self.base_url + f"/dns/edit/{root}/{int(r.get('id'))}"
                    response = requests.post(url, json=data, timeout=self.timeout)
                    res = response.json()
                    break

            if res.get("status") != "SUCCESS":
                return {"status": False, "msg": res.get("message", "Fail, please try again later.")}
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

    def __init__(self, api_user, api_key, **kwargs):  # noqa
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
                "agreedAt": datetime.utcnow().isoformat() + "Z"  # noqa
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
            all_domains = []
            limit = 300
            endpoint = f"/v1/domains?limit={limit}"
            while 1:
                res = self._make_request("GET", endpoint).json()
                if not res:
                    break
                for domain in res:
                    if domain.get("status") != "ACTIVE":
                        sync_log(f"|-- warning: [{domain.get('domain')}] is Not ACTIVE, Skip It...")
                        continue
                    if domain.get("expires") and domain.get("expires") < datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ"):
                        sync_log(f"|-- warning: [{domain.get('domain')}] is Expired, Skip It...")
                        continue
                    all_domains.append(domain.get("domain"))

                if len(res) < limit:
                    break

                last_domain = res[-1]["domain"]
                endpoint = f"/v1/domains?limit={limit}&marker={last_domain}"
                time.sleep(1)  # 限流

            all_domains.sort()
            return all_domains
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


class ClouDns(BaseDns):
    dns_provider_name = "cloudns"
    kw_prefix = {
        "priority": "priority"
    }

    def __init__(self, api_user, api_key, **kwargs):  # noqa
        super().__init__()
        self.api_user = str(api_user or "").strip()
        self.api_key = str(api_key or "").strip()
        self.timeout = 30
        self.base_url = "https://api.cloudns.net/dns/"

    def _auth_params(self) -> dict:
        if self.api_user.isdigit():  # 接受 api auth id
            return {
                "auth-id": self.api_user,
                "auth-password": self.api_key,
            }
        # 回退账号策略
        return {
            "auth-user": self.api_user,
            "auth-password": self.api_key,
        }

    def _make_request(self, endpoint: str, payload: dict = None, method: str = "GET"):
        params = self._auth_params()
        if payload:
            params.update(payload)
        url = urljoin(self.base_url, endpoint)
        response = requests.request(method, url, params=params, timeout=self.timeout)
        if response.status_code != 200:
            self.raise_resp_error(response)

        try:
            data = response.json()
        except ValueError:
            raise HintException(f"Cloudns API returned invalid JSON: {response.text}")

        if isinstance(data, dict):
            status = str(data.get("status", "")).lower()
            if status in {"failed", "failure", "error"}:
                raise HintException(data.get("statusDescription") or data.get("status") or str(data))
            if str(data.get("result", "")).lower() in {"failed", "failure", "error"}:
                raise HintException(data.get("statusDescription") or data.get("message") or str(data))
        return data

    @staticmethod
    def _normalize_host(domain_name: str, record: str) -> str:
        record = (record or "@").strip().rstrip(".")
        if not record or record == "@":
            return "@"

        if record == domain_name:
            return "@"

        suffix = f".{domain_name}"
        if record.endswith(suffix):
            host = record[:-len(suffix)]
            return host or "@"
        return record

    def _normalize_zone_domain(self, domain_name: str) -> str:
        domain = str(domain_name or "").strip().rstrip(".").lstrip("*.")
        if not domain:
            raise HintException("Missing domain-name")

        root, _, _ = extract_zone(domain)
        domain = (root or domain).strip().rstrip(".")
        if not domain:
            raise HintException("Missing domain-name")
        return domain

    def _find_record_id(self, domain_name: str, record: str, record_type: str, record_value: str = None):
        host = self._normalize_host(domain_name, record)
        try:
            for item in self.get_dns_record(domain_name):
                if item.get("record_type", "").upper() != record_type.upper():
                    continue
                if self._normalize_host(domain_name, item.get("record")) != host:
                    continue
                if record_value is not None and item.get("record_value") != record_value:
                    continue
                return item.get("record_id")
        except Exception as e:
            public.print_log(f"{self.dns_provider_name} find record id error {e}")
        return None

    def _build_acme_record(self, domain_name: str) -> tuple[str, str]:
        domain = str(domain_name or "").strip().rstrip(".").lstrip("*.")
        zone_domain = self._normalize_zone_domain(domain)
        suffix = f".{zone_domain}"
        if domain == zone_domain:
            acme_host = "_acme-challenge"
        elif domain.endswith(suffix):
            sub = domain[:-len(suffix)]
            acme_host = f"_acme-challenge.{sub}"
        else:
            acme_host = "_acme-challenge"
        return zone_domain, acme_host

    @staticmethod
    def _parse_caa_value(record_value: str) -> tuple[int, str, str]:
        parts = str(record_value or "").strip().split(None, 2)
        if len(parts) != 3:
            raise HintException("CAA record_value format error, expected: '<flag> <type> <value>'")

        flag_raw, caa_type, caa_value = parts
        if not caa_type or not caa_value:
            raise HintException("CAA record_value format error, expected: '<flag> <type> <value>'")

        # Accept UI-style quoted values such as: 0 issue "letsencrypt.org"
        if (caa_value.startswith('"') and caa_value.endswith('"')) or (
                caa_value.startswith("'") and caa_value.endswith("'")
        ):
            caa_value = caa_value[1:-1].strip()
        if caa_value == "":
            raise HintException("CAA record_value format error, expected: '<flag> <type> <value>'")

        try:
            caa_flag = int(flag_raw)
        except Exception:
            raise HintException("CAA flag must be integer")
        return caa_flag, caa_type, caa_value

    def _build_record_payload(self, domain_name: str, record: str, record_value: str, record_type: str,
                              ttl: int, extra: dict) -> dict:
        record_type = str(record_type or "").upper()
        payload = {
            "host": self._normalize_host(domain_name, record),
            "record-type": record_type,
            "ttl": 600 if int(ttl) == 1 else int(ttl),
        }

        if record_type == "CAA":
            # Match get_dns_record output format: "flag type value".
            caa_flag, caa_type, caa_value = self._parse_caa_value(record_value)
            payload.update({
                "caa_flag": caa_flag,
                "caa_type": caa_type,
                "caa_value": caa_value,
            })
            return payload

        payload["record"] = record_value
        if record_type == "MX":
            priority = extra.get("priority", -1)
            if str(priority) not in {"", "-1", "None"}:
                payload["priority"] = int(priority)
        return payload

    # =============== acme ======================
    def create_dns_record(self, domain_name: str, domain_dns_value: str) -> None:
        zone_domain, acme_txt = self._build_acme_record(domain_name)
        res = self.create_org_record(
            domain_name=zone_domain,
            record=acme_txt,
            record_value=domain_dns_value,
            record_type="TXT",
            ttl=600,
        )
        if not res.get("status"):
            raise HintException(res.get("msg") or "create dns record failed")

    def delete_dns_record(self, domain_name: str, domain_dns_value: str) -> None:
        zone_domain, acme_txt = self._build_acme_record(domain_name)
        res = self.remove_record(zone_domain, acme_txt, "TXT", record_value=domain_dns_value)
        if not res.get("status"):
            raise HintException(res.get("msg") or "delete dns record failed")

    # =============== 域名管理 ====================
    def get_domains(self, verify: bool = False, page: int = 1, per_page: int = 100) -> list | bool:
        try:
            domains = []
            current_page = max(int(page), 1)
            page_size = max(int(per_page), 1)

            def _is_active_domain(item: dict) -> str:
                name = str(item.get("name", "")).strip().rstrip(".")
                zone = str(item.get("zone", "")).strip().lower()
                status = str(item.get("status", "")).strip().lower()
                type = str(item.get("type", "")).strip().lower()
                if zone != "domain":
                    return ""
                if status not in {"1", "active", "true"}:
                    return ""
                if not name or name.endswith(".arpa"):
                    return ""
                if type != "master":
                    return ""
                return name

            while 1:
                payload = {
                    "page": current_page,
                    "rows-per-page": page_size,
                }
                data = self._make_request("list-zones.json", payload)
                if verify:
                    return True

                page_domains = []
                if not isinstance(data, list):
                    raise HintException(f"list-zones response type error: {type(data).__name__}")

                raw_count = len(data)
                for item in data:
                    if isinstance(item, dict):
                        domain = _is_active_domain(item)
                        if domain:
                            page_domains.append(domain)

                if raw_count == 0:
                    break

                domains.extend(page_domains)
                if raw_count < page_size:
                    break

                current_page += 1
                time.sleep(1)  # 限流

            return sorted(set(domains))
        except Exception as e:
            raise HintException(f"get domains error {e}")

    def get_dns_record(self, domain_name: str) -> list:
        domain_name = self._normalize_zone_domain(domain_name)
        try:
            data = self._make_request("records.json", {"domain-name": domain_name})
            items = []
            if isinstance(data, dict):
                items = [v for v in data.values() if isinstance(v, dict)]
            elif isinstance(data, list):
                items = [v for v in data if isinstance(v, dict)]

            result = []
            for x in items:
                try:
                    status = str(x.get("status", "")).strip().lower()
                    if status not in {"1", "active", "true"}:
                        continue

                    record_type = str(x.get("type", "")).strip().upper()
                    host = str(x.get("host", "")).strip()
                    host = host if host else "@"

                    # CAA style "flag type value", default flag=0 when missing.
                    if record_type == "CAA":
                        caa_type = str(x.get("caa_type", "")).strip()
                        caa_value = str(x.get("caa_value", "")).strip()
                        if not caa_type or caa_value == "":
                            continue
                        caa_flag = str(x.get("caa_flag", "0")).strip() or "0"
                        record_value = f"{caa_flag} {caa_type} {caa_value}"
                    else:
                        record_value = x.get("record", "")

                    ttl = int(x.get("ttl", 1))
                    priority = x.get("priority", -1)
                    result.append({
                        "record": host,
                        "record_value": record_value,
                        "record_type": record_type,
                        "ttl": ttl,
                        "priority": int(priority) if str(priority) not in {"", "0", "-1", "None"} else -1,
                        "proxy": -1,
                        "record_id": x.get("id") or x.get("record_id"),
                    })
                except Exception:
                    continue
            return result
        except Exception as e:
            raise HintException(e)

    def create_org_record(self, domain_name, record, record_value, record_type, ttl=1, **kwargs):
        domain_name = self._normalize_zone_domain(domain_name)
        try:
            payload = {
                "domain-name": domain_name,
                **self._build_record_payload(
                    domain_name=domain_name,
                    record=record,
                    record_value=record_value,
                    record_type=record_type,
                    ttl=ttl,
                    extra=kwargs,
                ),
            }
            res = self._make_request("add-record.json", payload, method="POST")
            return {"status": True, "msg": res}
        except Exception as e:
            return {"status": False, "msg": str(e)}

    def remove_record(self, domain_name, record, record_type="TXT", **kwargs) -> dict:
        domain_name = self._normalize_zone_domain(domain_name)
        try:
            record_id = kwargs.get("record_id") or self._find_record_id(
                domain_name,
                record,
                record_type,
                kwargs.get("record_value"),
            )
            if not record_id:
                return {"status": True, "msg": "Dns Record is empty."}

            payload = {
                "domain-name": domain_name,
                "record-id": int(record_id),
            }
            res = self._make_request("delete-record.json", payload, method="POST")
            return {"status": True, "msg": res}
        except Exception as e:
            return {"status": False, "msg": str(e)}

    def update_record(self, domain_name, record: dict, new_record: dict, **kwargs):
        domain_name = self._normalize_zone_domain(domain_name)
        try:
            record_id = record.get("record_id") or self._find_record_id(
                domain_name,
                record.get("record"),
                record.get("record_type", ""),
                record.get("record_value"),
            )
            if not record_id:
                return {"status": False, "msg": "Dns Record Not Found!"}

            payload = {
                "domain-name": domain_name,
                "record-id": int(record_id),
                **self._build_record_payload(
                    domain_name=domain_name,
                    record=new_record.get("record"),
                    record_value=new_record.get("record_value"),
                    record_type=new_record.get("record_type", ""),
                    ttl=new_record.get("ttl", 1),
                    extra=new_record,
                ),
            }
            res = self._make_request("mod-record.json", payload, method="POST")
            return {"status": True, "msg": res}
        except Exception as e:
            return {"status": False, "msg": str(e)}

    def verify(self) -> Optional[bool]:
        try:
            self.get_domains(verify=True)
        except Exception as e:
            public.print_log(f"e = {e}")
            if "You don't have access to the HTTP API. Check your plan." in str(e):
                raise HintException(public.lang(
                    "Cloudns API have been rejected, "
                    "Free accounts (Free plan) don't have access to API, Please upgrade your plan."
                ))
            raise HintException(public.lang(f"Verify fail, please check your Api Account and Password: {e}"))
        return True


class SpaceShipDNS(BaseDns):
    dns_provider_name = "spaceshipdns"
    kw_prefix = {
        "priority": "priority"
    }

    def __init__(self, api_user, api_key, **kwargs):  # noqa
        super().__init__()
        self.api_user = str(api_user or "").strip()  # API Key
        self.api_key = str(api_key or "").strip()  # API Secret
        self.timeout = 30
        self.base_url = "https://spaceship.dev/api/v1"

    def _get_auth_headers(self) -> dict:
        return {
            "X-Api-Key": self.api_user,
            "X-Api-Secret": self.api_key,
            "Accept": "application/json",
            "Content-Type": "application/json",
        }

    def _make_request(self, method: str, endpoint: str, payload=None, params=None):
        url = f"{self.base_url}{endpoint}"
        headers = self._get_auth_headers()
        response = requests.request(
            method, url, headers=headers, json=payload, params=params, timeout=self.timeout
        )
        if response.status_code not in (200, 201, 204):
            self.raise_resp_error(response)
        if response.status_code == 204 or not response.text.strip():
            return {}
        try:
            return response.json()
        except ValueError:
            raise HintException(f"Spaceship API returned invalid JSON: {response.text}")

    def _normalize_zone_domain(self, domain_name: str) -> str:
        domain = str(domain_name or "").strip().rstrip(".").lstrip("*.")
        if not domain:
            raise HintException("Missing domain-name")
        root, _, _ = extract_zone(domain)
        domain = (root or domain).strip().rstrip(".")
        if not domain:
            raise HintException("Missing domain-name")
        return domain

    @staticmethod
    def _get_sub_domain(root: str, record: str) -> str:
        """
        标准化子域名
        root="example.com", record="www.example.com" -> "www"
        root="example.com", record="example.com" -> ""
        root="example.com", record="www" -> "www"
        """
        record = str(record or "").strip().rstrip(".")
        if not record or record == root or record == "@":
            return ""
        suffix = f".{root}"
        if record.endswith(suffix):
            return record[:-len(suffix)]
        return record

    @staticmethod
    def _parse_record_value(item: dict) -> str:
        """从返回记录中解析值, 各类型字段不同
        A/AAAA  -> address
        CNAME   -> target
        MX      -> exchange
        NS      -> host
        TXT     -> value
        CAA     -> "flag tag value"
        """
        record_type = str(item.get("type", "")).upper()
        if record_type in ("A", "AAAA"):
            return str(item.get("address", ""))
        if record_type == "CNAME":
            return str(item.get("cname", ""))
        if record_type == "MX":
            return str(item.get("exchange", ""))
        if record_type == "NS":
            return str(item.get("nameserver", ""))
        if record_type == "CAA":
            flag = item.get("flag", 0)
            tag = item.get("tag", "")
            value = item.get("value", "")
            return f"{flag} {tag} {value}"
        return str(item.get("value", ""))

    @staticmethod
    def _parse_record_priority(item: dict) -> int:
        """提取优先级: MX -> preference"""
        record_type = str(item.get("type", "")).upper()
        if record_type == "MX":
            pref = item.get("preference", -1)
        else:
            pref = item.get("priority", -1)
        try:
            pref = int(pref)
        except (TypeError, ValueError):
            pref = -1
        return pref if str(pref) not in {"", "-1", "None"} else -1

    def _build_record_body(self, zone_domain: str, record: str, record_value: str,
                           record_type: str, ttl: int, extra: dict) -> dict:
        """
        构造PUT创建记录的单条 body
        各类型使用不同值字段:
          A/AAAA -> address,
          CNAME -> target,
          MX -> exchange+preference
          NS -> host,
          TXT -> value,
          CAA -> flag+tag+value
        """
        record_type = str(record_type or "").upper()
        name = self._get_sub_domain(zone_domain, record) or record
        ttl_val = 600 if int(ttl) == 1 else int(ttl)

        if record_type in ("A", "AAAA"):
            body = {"type": record_type, "name": name, "address": record_value, "ttl": ttl_val}

        elif record_type == "CNAME":
            body = {"type": record_type, "name": name, "cname": record_value, "ttl": ttl_val}

        elif record_type == "NS":
            body = {"type": record_type, "name": name, "nameserver": record_value, "ttl": ttl_val}

        elif record_type == "MX":
            body = {
                "type": record_type,
                "name": name,
                "exchange": record_value,
                "preference": int(extra.get("priority", 10)),
                "ttl": ttl_val,
            }

        elif record_type == "CAA":
            parts = str(record_value).strip().split(None, 2)
            if len(parts) == 3:
                body = {
                    "type": record_type, "name": name,
                    "flag": int(parts[0]), "tag": parts[1],
                    "value": parts[2].strip('"').strip("'"),
                    "ttl": ttl_val,
                }
            else:
                body = {"type": record_type, "name": name, "value": record_value, "ttl": ttl_val}
        else:
            # TXT 及其他
            body = {"type": record_type, "name": name, "value": record_value, "ttl": ttl_val}
        return body

    def _build_delete_body(self, zone_domain: str, record: str, record_type: str, **kwargs) -> dict:
        """构造DELETE单条记录匹配 body, 各类型值字段不同"""
        record_type = str(record_type or "").upper()
        name = self._get_sub_domain(zone_domain, record) or record
        val = kwargs.get("record_value") or ""

        if record_type in ("A", "AAAA"):
            body = {"type": record_type, "name": name, "address": val}

        elif record_type == "CNAME":
            body = {"type": record_type, "name": name, "cname": val}

        elif record_type == "NS":
            body = {"type": record_type, "name": name, "nameserver": val}

        elif record_type == "MX":
            body = {
                "type": record_type, "name": name,
                "exchange": val,
                "preference": int(kwargs.get("priority", 0)),
            }

        elif record_type == "CAA":
            parts = str(val).strip().split(None, 2)
            if len(parts) == 3:
                body = {
                    "type": record_type, "name": name,
                    "flag": int(parts[0]), "tag": parts[1],
                    "value": parts[2].strip('"').strip("'"),
                }
            else:
                body = {"type": record_type, "name": name, "value": val}

        else:
            # TXT / 其他
            body = {"type": record_type, "name": name, "value": val}
        return body

    # =============== acme ======================
    def create_dns_record(self, domain_name: str, domain_dns_value: str) -> None:
        _, _, acme_txt = extract_zone(domain_name)
        res = self.create_org_record(
            domain_name=domain_name,
            record=acme_txt,
            record_value=domain_dns_value,
            record_type="TXT",
            ttl=600,
        )
        if not res.get("status"):
            raise HintException(res.get("msg") or "create dns record failed")

    def delete_dns_record(self, domain_name: str, domain_dns_value: str) -> None:
        _, _, acme_txt = extract_zone(domain_name)
        res = self.remove_record(domain_name, acme_txt, "TXT", record_value=domain_dns_value)
        if not res.get("status"):
            raise HintException(res.get("msg") or "delete dns record failed")

    # =============== 域名管理 ====================
    def get_domains(self, verify: bool = False) -> list:
        try:
            domains = []
            skip = 0
            take = 100
            while True:
                params = {"take": take, "skip": skip}
                data = self._make_request("GET", "/domains", params=params)
                if verify:
                    return []

                items = data.get("items", [])
                if not items:
                    break

                for item in items:
                    if not isinstance(item, dict):
                        continue
                    name = str(item.get("name", "")).strip().rstrip(".")
                    if not name:
                        continue
                    status = str(item.get("status", "")).strip().lower()
                    if status not in {"active", "1", "true", ""}:
                        sync_log(f"|-- warning: [{name}] is Not ACTIVE, Skip It...")
                        continue
                    domains.append(name)

                if len(items) < take:
                    break
                skip += take
                time.sleep(1)  # 限流

            return sorted(set(domains))
        except HintException:
            raise
        except Exception as e:
            raise HintException(f"get domains error {e}")

    def get_dns_record(self, domain_name: str) -> list:
        zone_domain = self._normalize_zone_domain(domain_name)
        try:
            result = []
            skip = 0
            take = 100
            while True:
                params = {"take": take, "skip": skip}
                data = self._make_request("GET", f"/dns/records/{zone_domain}", params=params)
                items = data.get("items", [])
                if not items:
                    break

                for x in items:
                    if not isinstance(x, dict):
                        continue
                    try:
                        record_type = str(x.get("type", "")).strip().upper()
                        host = str(x.get("name", "")).strip() or "@"
                        record_value = self._parse_record_value(x)
                        ttl = int(x.get("ttl", 1))
                        priority = self._parse_record_priority(x)
                        result.append({
                            "record": host,
                            "record_value": record_value,
                            "record_type": record_type,
                            "ttl": ttl,
                            "priority": priority,
                            "proxy": -1,
                        })
                    except Exception:
                        continue

                if len(items) < take:
                    break
                skip += take
                time.sleep(1)  # 限流

            return result
        except HintException:
            raise
        except Exception as e:
            raise HintException(f"get dns record error {e}")

    def create_org_record(self, domain_name, record, record_value, record_type, ttl=1, **kwargs):
        """PUT /dns/records/{domain} + {"items": [...]} 创建记录"""
        zone_domain = self._normalize_zone_domain(domain_name)
        try:
            body = self._build_record_body(zone_domain, record, record_value, record_type, ttl, kwargs)
            res = self._make_request("PUT", f"/dns/records/{zone_domain}", payload={"items": [body]})
            return {"status": True, "msg": res}
        except Exception as e:
            return {"status": False, "msg": str(e)}

    def remove_record(self, domain_name, record, record_type="TXT", **kwargs) -> dict:
        """DELETE /dns/records/{domain} + 裸数组 [...] 删除记录"""
        zone_domain = self._normalize_zone_domain(domain_name)
        try:
            body = self._build_delete_body(zone_domain, record, record_type, **kwargs)
            res = self._make_request("DELETE", f"/dns/records/{zone_domain}", payload=[body])
            return {"status": True, "msg": res}
        except Exception as e:
            return {"status": False, "msg": str(e)}

    def update_record(self, domain_name, record: dict, new_record: dict, **kwargs):
        """无原生更新支持, 先 delete 再 create 复用"""
        zone_domain = self._normalize_zone_domain(domain_name)
        try:
            # 1. 删除旧记录
            del_body = self._build_delete_body(
                zone_domain,
                record.get("record", ""),
                record.get("record_type", ""),
                **record,
            )
            self._make_request("DELETE", f"/dns/records/{zone_domain}", payload=[del_body])

            # 2. 创建新记录
            new_body = self._build_record_body(
                zone_domain,
                new_record.get("record", ""),
                new_record.get("record_value", ""),
                new_record.get("record_type", ""),
                new_record.get("ttl", 600),
                new_record,
            )
            res = self._make_request("PUT", f"/dns/records/{zone_domain}", payload={"items": [new_body]})
            return {"status": True, "msg": res}
        except Exception as e:
            return {"status": False, "msg": str(e)}

    def verify(self) -> Optional[bool]:
        try:
            self.get_domains(verify=True)
        except Exception as e:
            raise HintException(f"Verify fail, please check your Api Key and Secret: {e}")
        return True


# noinspection PyUnusedLocal
class AmazonRoute53Dns(BaseDns):
    dns_provider_name = "route53"
    kw_prefix = {
        "priority": "priority"
    }
    # DNS 记录类型中支持多值的(同一 name + type 可存多个value)
    _MULTI_VALUE_TYPES = {"TXT", "CAA", "MX"}

    def __init__(self, api_user, api_key, **kwargs):  # noqa
        super().__init__()
        self.api_user = str(api_user or "").strip()  # AWS AccessKeyId
        self.api_key = str(api_key or "").strip()  # AWS SecretAccessKey
        try:
            import boto3
            from botocore.config import Config
            from botocore.exceptions import ClientError
        except ImportError:
            os.system("btpip install boto3")
            try:
                import boto3
                from botocore.config import Config
                from botocore.exceptions import ClientError
            except ImportError:
                raise HintException("Aws SDK boto3 is not installed, please install it first: btpip install boto3")

        self.boto3 = boto3
        self.ClientError = ClientError
        self.Config = Config
        session = self.boto3.Session(
            aws_access_key_id=self.api_user,
            aws_secret_access_key=self.api_key,
            region_name="us-east-1",
        )
        config = self.Config(retries={"max_attempts": 3, "mode": "standard"})
        self.r53 = session.client("route53", config=config)
        self._hosted_zones_cache = None

    def _find_hosted_zone(self, domain_name: str) -> Optional[str]:
        """查找域名对应的Zone (最长匹配, 参考cf处理)"""
        domain = domain_name.strip().rstrip(".").lstrip("*.")
        zones = self.get_domains()
        matched = [
            z for z in zones if domain == z or domain.endswith("." + z)
        ]
        if not matched:
            return None
        return max(matched, key=lambda x: len(x))

    def _get_zone_id(self, domain_name: str) -> str:
        """获取托管区 ID"""
        domain = str(domain_name or "").strip().rstrip(".")
        if not domain.endswith("."):
            domain = domain + "."

        paginator = self.r53.get_paginator("list_hosted_zones")
        for page in paginator.paginate():
            for zone in page.get("HostedZones", []):
                zone_name = zone.get("Name", "").rstrip(".")
                if zone_name == domain.rstrip("."):
                    zone_id = zone.get("Id", "")
                    if zone_id.startswith("/hostedzone/"):
                        zone_id = zone_id[len("/hostedzone/"):]
                    return zone_id

        raise HintException(f"Hosted zone not found for domain: {domain_name}")

    @staticmethod
    def _normalize_host(domain_name: str, record: str) -> str:
        """标准化子域名

        处理输入的record可能带域名也可能不带域名的情况:
        - "test" -> "test"
        - "test.example.com" -> "test"
        - "test.example.com." -> "test"
        - "@" -> "@"
        - "example.com" -> "@"
        """
        # 标准化domain_name，去掉末尾点
        domain = str(domain_name or "").strip().rstrip(".")
        # 标准化record，去掉末尾点和空格
        record = str(record or "").strip().rstrip(".")

        if not record or record in ("@", domain):
            return "@"

        # 检查record是否包含完整域名，如果是则提取子域名部分
        suffix = f".{domain}"
        if record.endswith(suffix):
            return record[:-len(suffix)] or "@"

        # record本身就是一个子域名（不带domain后缀）
        return record

    @staticmethod
    def _parse_caa_value(value: str) -> tuple:
        """解析 CAA 值: 'flag tag value' -> (flag, tag, value)"""
        parts = str(value or "").strip().split(None, 2)
        if len(parts) != 3:
            raise HintException("CAA record_value format error, expected: '<flag> <tag> <value>'")
        flag_str, tag, caa_value = parts
        if not tag or caa_value == "":
            raise HintException("CAA record_value format error, expected: '<flag> <tag> <value>'")
        if (caa_value.startswith('"') and caa_value.endswith('"')) or (
                caa_value.startswith("'") and caa_value.endswith("'")
        ):
            caa_value = caa_value[1:-1].strip()
        if caa_value == "":
            raise HintException("CAA record_value format error, expected: '<flag> <tag> <value>'")
        try:
            flag = int(flag_str)
        except Exception:
            raise HintException("CAA flag must be integer")
        return flag, tag, caa_value

    @staticmethod
    def _format_caa_value(flag: int, tag: str, caa_value: str) -> str:
        """格式化 CAA 值为 Route53 Value: 'flag tag "value"'"""
        return f'{flag} {tag} "{caa_value}"'

    @staticmethod
    def _ensure_upper(s: str) -> str:
        """确保字符串大写"""
        return str(s or "").upper()

    @staticmethod
    def _ensure_trailing_dot(name: str) -> str:
        """确保域名以点结尾"""
        return name + "." if name and not name.endswith(".") else name

    def _build_r53_value(self, record_type: str, record_value: str, priority: int = -1) -> str:
        """构造各类型使用不同字段格式"""
        record_type = self._ensure_upper(record_type)

        if record_type == "MX":
            pref = priority if str(priority) not in {"", "-1", "None"} else 10
            return f"{pref} {record_value}"

        if record_type == "TXT":
            val = str(record_value or "")
            if (val.startswith('"') and val.endswith('"')) or (val.startswith("'") and val.endswith("'")):
                val = val[1:-1]
            return f'"{val}"'

        if record_type == "CAA":
            flag, tag, caa_val = self._parse_caa_value(record_value)
            return self._format_caa_value(flag, tag, caa_val)

        return record_value

    def _parse_r53_value(self, record_type: str, value: str) -> str:
        """解析返回的 Value 为外部格式"""
        record_type = self._ensure_upper(record_type)
        value = str(value or "")

        if record_type == "TXT":
            if (value.startswith('"') and value.endswith('"')) or (value.startswith("'") and value.endswith("'")):
                value = value[1:-1]
            return value

        if record_type == "MX":
            parts = value.strip().split(None, 1)
            return parts[1] if len(parts) > 1 else value

        if record_type == "CAA":
            parts = value.strip().split(None, 2)
            if len(parts) == 3:
                flag_str, tag, caa_val = parts
                if (caa_val.startswith('"') and caa_val.endswith('"')) or (
                        caa_val.startswith("'") and caa_val.endswith("'")):
                    caa_val = caa_val[1:-1]
                return f"{flag_str} {tag} {caa_val}"
            return value

        return value

    @staticmethod
    def _parse_priority(record_type: str, value: str) -> int:
        """提取优先级: MX 从 value 解析"""
        record_type = str(record_type or "").upper()
        if record_type == "MX":
            parts = str(value or "").strip().split(None, 1)
            try:
                return int(parts[0])
            except (ValueError, IndexError):
                return -1
        return -1

    def _get_full_name(self, domain_name: str, record: str) -> str:
        """获取完整域名 (不带末尾点)"""
        host = self._normalize_host(domain_name, record)
        return domain_name if host == "@" else f"{host}.{domain_name}"

    def _make_change(self, action: str, name: str, record_type: str,
                     ttl: int, value: str, priority: int = -1) -> dict:
        """构造单条 Change 字典, 支持 A/AAAA/MX/TXT/NS/CAA/CNAME"""
        record_type = self._ensure_upper(record_type)

        # CAA 需要特殊处理(值格式不同)
        if record_type == "CAA":
            flag, tag, caa_val = self._parse_caa_value(value)
            r53_val = self._format_caa_value(flag, tag, caa_val)
            return {
                "Action": action,
                "ResourceRecordSet": {
                    "Name": self._ensure_trailing_dot(name),
                    "Type": "CAA",
                    "TTL": ttl,
                    "ResourceRecords": [{"Value": r53_val}],
                },
            }

        # DELETE 操作使用原始值，CREATE 操作需要格式化
        r_value = value if action == "DELETE" else self._build_r53_value(record_type, value, priority)

        return {
            "Action": action,
            "ResourceRecordSet": {
                "Name": self._ensure_trailing_dot(name),
                "Type": record_type,
                "TTL": ttl,
                "ResourceRecords": [{"Value": r_value}],
            },
        }

    # =============== acme ======================
    def create_dns_record(self, domain_name: str, domain_dns_value: str) -> None:
        """ACME 挑战专用, 自动合并相同记录名的多个挑战值"""
        domain_name = domain_name.lstrip("*.")
        _, _, acme_txt = extract_zone(domain_name)
        # 优化获取现有 TXT 记录
        existing_values = []
        try:
            existing_records = self._get_acme_txt_record(domain_name, acme_txt)
            for r in existing_records:
                val = r.get("record_value", "")
                if val and val not in existing_values:
                    existing_values.append(val)
        except Exception:
            pass

        # 合并去重
        all_values = existing_values + [domain_dns_value]
        all_values = list(dict.fromkeys(all_values).keys())

        # 创建或更新记录
        if len(all_values) == 1:
            # 单值使用普通创建
            res = self.create_org_record(
                domain_name=domain_name,
                record=acme_txt,
                record_value=domain_dns_value,
                record_type="TXT",
                ttl=600,
            )
        else:
            # 多值使用UPSERT合并所有值
            res = self._upsert_dns_record_multi(
                domain_name=domain_name,
                record=acme_txt,
                record_values=all_values,
                record_type="TXT",
                ttl=600,
            )

        if not res.get("status"):
            raise HintException(res.get("msg") or "create dns record failed")

    def _make_change_multi(self, action: str, name: str, record_type: str,
                           ttl: int, values: list[str]) -> dict:
        """
        构造多值的 Change 字典
        用于一个记录名存储多个 TXT 值（ACME 多域名挑战）
        """
        record_type = self._ensure_upper(record_type)

        # 为 TXT 记录构建多个值
        resource_records = []
        for value in values:
            if record_type == "TXT":
                # TXT 记录需要带引号
                formatted_value = self._build_r53_value(record_type, value, -1)
                resource_records.append({"Value": formatted_value})
            else:
                resource_records.append({"Value": value})

        return {
            "Action": action,
            "ResourceRecordSet": {
                "Name": self._ensure_trailing_dot(name),
                "Type": record_type,
                "TTL": ttl,
                "ResourceRecords": resource_records,
            },
        }

    def _upsert_dns_record_multi(self, domain_name: str, record: str, record_values: list[str],
                                  record_type: str, ttl: int = 600) -> dict:
        """
        创建或更新 DNS 记录，支持多值（ACME 批处理）
        """
        domain_name = self._find_hosted_zone(domain_name) or domain_name
        try:
            zone_id = self._get_zone_id(domain_name)
            full_name = self._get_full_name(domain_name, record)

            ttl_val = 600 if int(ttl) == 1 else int(ttl)

            # 使用多值 Change
            change = self._make_change_multi("UPSERT", full_name, record_type, ttl_val, record_values)
            if self._change_record(zone_id, "UPSERT", [change]):
                return {"status": True, "msg": "success"}
            return {"status": False, "msg": "upsert dns record failed"}
        except HintException:
            raise
        except Exception as e:
            return {"status": False, "msg": str(e)}

    def delete_dns_record(self, domain_name: str, domain_dns_value: str) -> None:
        domain_name = domain_name.lstrip("*.")
        _, _, acme_txt = extract_zone(domain_name)
        res = self.remove_record(
            domain_name, acme_txt, "TXT", record_value=domain_dns_value
        )
        if not res.get("status"):
            raise HintException(res.get("msg") or "delete dns record failed")

    # =============== 域名管理 ====================
    def get_domains(self, verify: bool = False) -> list:
        if self._hosted_zones_cache is not None and not verify:
            return self._hosted_zones_cache

        try:
            domains = []
            paginator = self.r53.get_paginator("list_hosted_zones")
            for page in paginator.paginate():
                for zone in page.get("HostedZones", []):
                    # 私有托管区
                    if zone.get("Config", {}).get("PrivateZone", False):
                        continue
                    if verify:
                        return []
                    name = zone.get("Name", "").strip().rstrip(".")
                    if name:
                        domains.append(name)
            result = sorted(set(domains))
            if not verify:
                self._hosted_zones_cache = result
            return result
        except self.ClientError as e:
            raise HintException(f"get domains error: {e}")
        except Exception as e:
            raise HintException(f"get domains error {e}")

    def get_dns_record(self, domain_name: str) -> list:
        zone_domain = self._find_hosted_zone(domain_name)
        if not zone_domain:
            raise HintException(f"Unable to find hosted zone for domain: {domain_name}")

        try:
            zone_id = self._get_zone_id(zone_domain)
            result = []

            paginator = self.r53.get_paginator("list_resource_record_sets")
            for page in paginator.paginate(HostedZoneId=zone_id):
                for rs in page.get("ResourceRecordSets", []):
                    r_type = rs.get("Type", "").upper()
                    r_name = rs.get("Name", "").strip().rstrip(".")
                    r_ttl = rs.get("TTL", 600)
                    host = self._normalize_host(zone_domain, r_name)
                    # 跳过 SOA 记录
                    if r_type == "SOA":
                        continue
                    # 跳过zone根 NS 记录
                    if r_type == "NS" and host == "@" and zone_domain in r_name:
                        continue
                    for rr in rs.get("ResourceRecords", []):
                        r_value = rr.get("Value", "")
                        record_value = self._parse_r53_value(r_type, r_value)
                        priority = self._parse_priority(r_type, r_value)
                        result.append({
                            "record": host,
                            "record_value": record_value,
                            "record_type": r_type,
                            "ttl": r_ttl,
                            "priority": priority,
                            "proxy": -1,
                        })

            return result
        except self.ClientError as e:
            raise HintException(f"get dns record error: {e}")
        except Exception as e:
            raise HintException(f"get dns record error {e}")

    def _get_acme_txt_record(self, domain_name: str, record: str) -> list:
        """
        获取 ACME record TXT 挑战记录（ACME 专用优化快速查找）
        """
        zone_domain = self._find_hosted_zone(domain_name)
        if not zone_domain:
            return []

        try:
            zone_id = self._get_zone_id(zone_domain)
            target_host = self._normalize_host(domain_name, record)
            full_name_with_dot = self._get_full_name(domain_name, record) + "."

            paginator = self.r53.get_paginator("list_resource_record_sets")
            for page in paginator.paginate(HostedZoneId=zone_id):
                for rs in page.get("ResourceRecordSets", []):
                    r_type = rs.get("Type", "").upper()
                    r_name = rs.get("Name", "")
                    if r_type != "TXT":
                        continue
                    # 标准化记录名进行比较
                    r_name_stripped = r_name.strip().rstrip(".")
                    if r_name_stripped != full_name_with_dot.rstrip("."):
                        continue
                    # 解析值并返回
                    r_ttl = rs.get("TTL", 600)
                    result = []
                    for rr in rs.get("ResourceRecords", []):
                        r_value = rr.get("Value", "")
                        record_value = self._parse_r53_value(r_type, r_value)
                        result.append({
                            "record": target_host,
                            "record_value": record_value,
                            "record_type": r_type,
                            "ttl": r_ttl,
                            "priority": -1,
                            "proxy": -1,
                        })
                    return result
            return []
        except Exception as e:
            public.print_log(f"get acme txt record error: {e}")
            return []

    def _change_record(self, zone_id: str, action: str, changes: list) -> bool:
        """执行 Record 变更, action: CREATE/DELETE/UPSERT"""
        try:
            self.r53.change_resource_record_sets(
                HostedZoneId=zone_id,
                ChangeBatch={
                    "Changes": changes,
                },
            )
            return True
        except self.ClientError as e:
            error_code = e.response.get("Error", {}).get("Code", "")
            error_msg = e.response.get("Error", {}).get("Message", "")
            # DELETE 时记录不存在视为成功
            if action == "DELETE" and error_code == "InvalidChangeBatch" and "but it does not exist" in error_msg:
                return True
            public.print_log(f"Route53 {action} error: {error_msg}")
            return False
        except Exception as e:
            public.print_log(f"Route53 {action} error: {e}")
            return False

    def create_org_record(self, domain_name, record, record_value, record_type, ttl=1, **kwargs):
        """
        创建 DNS 记录
        - 可合并类型存在时合并新值
        - 不可合并类型存在时直接返回失败, 避免创建表数据
        - 不存在时正常创建
        """
        domain_name = self._find_hosted_zone(domain_name) or domain_name
        try:
            zone_id = self._get_zone_id(domain_name)
            full_name = self._get_full_name(domain_name, record)
            record_type_upper = self._ensure_upper(str(record_type))

            ttl_val = 600 if int(ttl) == 1 else int(ttl)
            priority = kwargs.get("priority", -1)

            if record_type_upper in self._MULTI_VALUE_TYPES:
                # 可合并类型: 查询现有值并追加
                existing_values = []
                records = self.get_dns_record(domain_name)
                target_host = self._normalize_host(domain_name, record)
                for r in records:
                    if (self._normalize_host(domain_name, r.get("record")) == target_host and
                            self._ensure_upper(r.get("record_type", "")) == record_type_upper):
                        val = r.get("record_value", "")
                        if val and val not in existing_values:
                            existing_values.append(val)

                # 追加新值(去重)
                normalized_new_value = self._parse_r53_value(
                    record_type_upper, record_value
                ) if record_type_upper in ("TXT", "CAA") else record_value

                if normalized_new_value not in existing_values:
                    existing_values.append(normalized_new_value)

                if len(existing_values) == 1:
                    change = self._make_change("UPSERT", full_name, record_type_upper,
                                               ttl_val, existing_values[0], priority)
                else:
                    change = self._make_change_multi("UPSERT", full_name, record_type_upper,
                                                     ttl_val, existing_values)

                if self._change_record(zone_id, "UPSERT", [change]):
                    return {"status": True, "msg": "success"}
                return {"status": False, "msg": "upsert record failed"}
            else:
                # 不可合并类型: 检查是否存在
                records = self.get_dns_record(domain_name)
                target_host = self._normalize_host(domain_name, record)
                for r in records:
                    if (self._normalize_host(domain_name, r.get("record")) == target_host and
                            self._ensure_upper(r.get("record_type", "")) == record_type_upper):
                        # 已存在，返回失败, 避免添加到缓存表中
                        return {"status": False, "msg": "Record already exists."}

                # 不存在，正常创建
                change = self._make_change("UPSERT", full_name, record_type_upper,
                                           ttl_val, record_value, priority)
                if self._change_record(zone_id, "UPSERT", [change]):
                    return {"status": True, "msg": "success"}
                return {"status": False, "msg": "create record failed"}
        except HintException:
            raise
        except Exception as e:
            return {"status": False, "msg": str(e)}

    def remove_record(self, domain_name, record, record_type="TXT", **kwargs) -> dict:
        """
        删除 DNS 记录
        多值类型+指定值: 仅移除该值, 保留其余
        其余情况: 删除全部匹配记录
        """
        domain_name = self._find_hosted_zone(domain_name) or domain_name
        try:
            zone_id = self._get_zone_id(domain_name)
            full_name = self._get_full_name(domain_name, record)
            record_type_upper = str(record_type).upper()

            # 查询所有记录
            records = self.get_dns_record(domain_name)
            target_host = self._normalize_host(domain_name, record)

            # 收集所有匹配的记录值
            matched_records = []
            for r in records:
                if (self._normalize_host(domain_name, r.get("record")) != target_host or
                        r.get("record_type", "").upper() != record_type_upper):
                    continue
                matched_records.append(r)

            if not matched_records:
                return {"status": True, "msg": "Dns Record not found."}

            provided_value = kwargs.get("record_value", "")
            ttl = matched_records[0].get("ttl", 600)
            priority = matched_records[0].get("priority", -1)

            # === 多值类型 + 指定了具体值 → 只删这一个值, 保留其余 ===
            if record_type_upper in self._MULTI_VALUE_TYPES and provided_value:
                # 标准化要删除的值
                compare_value = self._parse_r53_value(record_type_upper, provided_value)

                # 检查值是否存在
                if compare_value not in [r.get("record_value", "") for r in matched_records]:
                    return {"status": False, "msg": f"No matching record found with value: {provided_value}"}

                # 过滤出要保留的值
                remaining_values = [
                    r.get("record_value", "") for r in matched_records
                    if r.get("record_value", "") != compare_value
                ]

                if remaining_values:
                    # 还有剩余值 → UPSERT 保留
                    if len(remaining_values) == 1:
                        change = self._make_change("UPSERT", full_name, record_type_upper,
                                                   ttl, remaining_values[0], priority)
                    else:
                        change = self._make_change_multi("UPSERT", full_name, record_type_upper,
                                                         ttl, remaining_values)
                else:
                    # 没有剩余值 → DELETE 整个记录集
                    change = self._make_change_multi("DELETE", full_name, record_type_upper,
                                                     ttl, [r.get("record_value", "") for r in matched_records])

                if self._change_record(zone_id, change.get("Action"), [change]):
                    return {"status": True, "msg": "success"}
                return {"status": False, "msg": "delete record failed"}

            # === 其余情况: 删除全部匹配记录 ===
            change = self._make_change_multi("DELETE", full_name, record_type_upper, ttl,
                                              [r.get("record_value", "") for r in matched_records])
            if self._change_record(zone_id, "DELETE", [change]):
                return {"status": True, "msg": "success"}
            return {"status": False, "msg": "delete record failed"}
        except HintException:
            raise
        except Exception as e:
            return {"status": False, "msg": str(e)}

    def update_record(self, domain_name, record: dict, new_record: dict, **kwargs):
        """
        更新 DNS 记录
        多值类型同 name+type 时: 在值列表中替换, 保留其他值
        其余情况: 先删后建或直接 UPSERT
        """
        domain_name = self._find_hosted_zone(domain_name) or domain_name
        try:
            old_full_name = self._get_full_name(domain_name, record.get("record"))
            new_full_name = self._get_full_name(domain_name, new_record.get("record"))
            old_record_type = record.get("record_type", "TXT")
            new_record_type = new_record.get("record_type", "TXT")
            old_record_type_upper = self._ensure_upper(old_record_type)
            new_record_type_upper = self._ensure_upper(new_record_type)

            ttl_val = int(new_record.get("ttl", 600))
            if ttl_val == 1:
                ttl_val = 600

            priority = new_record.get("priority", -1)

            # === 记录名或类型变化 → 先删后建 ===
            if old_full_name != new_full_name or old_record_type_upper != new_record_type_upper:
                del_res = self.remove_record(domain_name, record.get("record"), old_record_type)
                if not del_res.get("status"):
                    return {"status": False, "msg": f"delete old record failed: {del_res.get('msg')}"}

                create_change = self._make_change(
                    "UPSERT", new_full_name, new_record_type_upper,
                    ttl_val, new_record.get("record_value", ""), priority,
                )
                if self._change_record(self._get_zone_id(domain_name), "UPSERT", [create_change]):
                    return {"status": True, "msg": "success"}
                return {"status": False, "msg": "create new record failed"}

            # === name+type 相同 ===
            if new_record_type_upper in self._MULTI_VALUE_TYPES:
                # 多值类型: 在值列表中替换指定值, 保留其他值
                records = self.get_dns_record(domain_name)
                target_host = self._normalize_host(domain_name, record.get("record"))
                existing_values = [
                    r.get("record_value", "") for r in records
                    if (self._normalize_host(domain_name, r.get("record")) == target_host and
                        self._ensure_upper(r.get("record_type", "")) == new_record_type_upper)
                ]

                old_value = record.get("record_value", "")
                new_value = new_record.get("record_value", "")

                # 找到旧值并替换
                if old_value in existing_values:
                    idx = existing_values.index(old_value)
                    existing_values[idx] = new_value
                else:
                    # 旧值不在列表中, 检查是否只是格式差异(TXT引号)
                    normalized_old = self._parse_r53_value(new_record_type_upper, old_value)
                    found = False
                    for i, v in enumerate(existing_values):
                        if v == normalized_old:
                            existing_values[i] = new_value
                            found = True
                            break
                    if not found:
                        # 找不到旧值, 视为新增
                        if new_value not in existing_values:
                            existing_values.append(new_value)

                # 去重
                existing_values = list(dict.fromkeys(existing_values))

                if len(existing_values) == 1:
                    change = self._make_change("UPSERT", new_full_name, new_record_type_upper,
                                               ttl_val, existing_values[0], priority)
                else:
                    change = self._make_change_multi("UPSERT", new_full_name, new_record_type_upper,
                                                     ttl_val, existing_values)
            else:
                # 单值类型: 直接 UPSERT 覆盖
                change = self._make_change(
                    "UPSERT", new_full_name, new_record_type_upper,
                    ttl_val, new_record.get("record_value", ""), priority,
                )

            if self._change_record(self._get_zone_id(domain_name), "UPSERT", [change]):
                return {"status": True, "msg": "success"}
            return {"status": False, "msg": "update record failed"}

        except HintException:
            raise
        except Exception as e:
            return {"status": False, "msg": str(e)}

    def verify(self) -> Optional[bool]:
        try:
            self.get_domains(verify=True)
        except Exception as e:
            raise HintException(f"Verify fail, please check your AccessKeyId and SecretAccessKey: {e}")
        return True
