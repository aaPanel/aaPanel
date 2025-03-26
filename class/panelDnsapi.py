# coding: utf-8
# +-------------------------------------------------------------------
# | aaPanel
# +-------------------------------------------------------------------
# | Copyright (c) 2015-2099 aaPanel(www.aapanel.com) All rights reserved.
# +-------------------------------------------------------------------
# | Author: 沐落 <cjx@aapanel.com>
# +-------------------------------------------------------------------
import base64
import json
import os
import re
import sys
import time

import public

if sys.version_info[0] == 2:  # python2
    # noinspection PyUnresolvedReferences
    from urlparse import urljoin
    import urllib2
else:  # python3
    from urllib.parse import urljoin
import hmac

try:
    import requests
except:
    public.ExecShell('btpip install requests')
    import requests

import random
import datetime
from hashlib import sha1
from uuid import uuid4
from itertools import chain
from typing import Set, List, Optional, Union, Dict, Tuple

os.chdir("/www/server/panel")
if 'class/' not in sys.path:
    sys.path.insert(0, 'class/')

import public

caa_value = '0 issue "letsencrypt.org"'


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
        raise ValueError(
            "Error {dns_name}: status_code={status_code} response={response}".format(
                dns_name=self.dns_provider_name,
                status_code=response.status_code,
                response=self.log_response(response),
            )
        )


# 未验证
# noinspection PyUnresolvedReferences
class TencentCloudDns(BaseDns):
    dns_provider_name = "tencentcloud"
    _type = 0

    def __init__(self, secret_id, secret_key):
        self.secret_id = secret_id
        self.secret_key = secret_key
        self.endpoint = "dnspod.tencentcloudapi.com"

        super(TencentCloudDns, self).__init__()

    def __client(self):
        from tencentcloud.common import credential
        from tencentcloud.dnspod.v20210323 import dnspod_client
        from tencentcloud.common.profile.client_profile import ClientProfile
        from tencentcloud.common.profile.http_profile import HttpProfile

        cred = credential.Credential(self.secret_id, self.secret_key)
        httpProfile = HttpProfile()
        httpProfile.endpoint = self.endpoint
        clientProfile = ClientProfile()
        clientProfile.httpProfile = httpProfile
        client = dnspod_client.DnspodClient(cred, "", clientProfile)

        return client

    def create_dns_record(self, domain_name, domain_dns_value):
        from tencentcloud.common.exception.tencent_cloud_sdk_exception import TencentCloudSDKException
        from tencentcloud.dnspod.v20210323 import models

        domain_name = domain_name
        domain_dns_value = domain_dns_value
        record_type = 'TXT'
        record_line = '默认'

        domain_name, _, sub_domain = extract_zone(domain_name)

        client = self.__client()
        try:
            req = models.CreateRecordRequest()
            params = {
                "Domain": domain_name,
                "SubDomain": sub_domain,
                "RecordType": record_type,
                "RecordLine": record_line,
                "Value": domain_dns_value,
            }

            req.from_json_string(json.dumps(params))
            client.CreateRecord(req)
            return public.returnMsg(True, public.lang('add succeeded'))
        except TencentCloudSDKException as err:
            return public.returnMsg(False, public.lang('add fail, msg: {}'.format(err)))


# 未验证
# noinspection PyUnresolvedReferences
class HuaweiCloudDns(BaseDns):
    dns_provider_name = "huaweicloud"
    _type = 0

    def __init__(self, ak, sk, project_id):
        self.ak = ak
        self.sk = sk
        self.project_id = project_id
        self.region = "cn-south-1"

        super(HuaweiCloudDns, self).__init__()

    def __client(self):
        from huaweicloudsdkcore.auth.credentials import BasicCredentials
        from huaweicloudsdkdns.v2.region.dns_region import DnsRegion
        from huaweicloudsdkdns.v2 import DnsClient

        credentials = BasicCredentials(self.ak, self.sk, self.project_id)
        client = DnsClient.new_builder() \
            .with_credentials(credentials) \
            .with_region(DnsRegion.value_of(self.region)) \
            .build()
        return client

    def create_dns_record(self, domain_name, domain_dns_value):
        from huaweicloudsdkdns.v2 import (CreateRecordSetWithLineRequest,
                                          CreateRecordSetWithLineRequestBody)

        record_type = 'TXT'

        if record_type == 'TXT':
            domain_dns_value = "\"{}\"".format(domain_dns_value)

        root_domain, _, sub_domain = extract_zone(domain_name)

        try:
            client = self.__client()
            zone_dic = self.get_zoneid_dict(client)
            request = CreateRecordSetWithLineRequest()
            request.zone_id = zone_dic[root_domain]
            request.body = CreateRecordSetWithLineRequestBody(
                records=[domain_dns_value],
                type=record_type,
                name="_acme-challenge.{}".format(domain_name)
            )
            client.create_record_set_with_line(request)
            return public.returnMsg(True, public.lang('add succeeded'))
        except Exception as e:
            return public.returnMsg(False, public.lang('add fail, msg: {}'.format(err)))

    def get_zoneid_dict(self, client):
        from huaweicloudsdkdns.v2 import ListPublicZonesRequest
        """
        获取所有域名对应id
        """
        request = ListPublicZonesRequest()
        response = client.list_public_zones(request).to_dict()
        data = {i["name"][:-1]: i["id"] for i in response["zones"]}

        return data


# 未验证
class DNSPodDns(BaseDns):
    dns_provider_name = "dnspod"
    _type = 0  # 0:lest 1：锐成

    def __init__(self, DNSPOD_ID, DNSPOD_API_KEY, DNSPOD_API_BASE_URL="https://dnsapi.cn/"):
        self.DNSPOD_ID = DNSPOD_ID
        self.DNSPOD_API_KEY = DNSPOD_API_KEY
        self.DNSPOD_API_BASE_URL = DNSPOD_API_BASE_URL
        self.HTTP_TIMEOUT = 65  # seconds
        self.DNSPOD_LOGIN = "{0},{1}".format(self.DNSPOD_ID, self.DNSPOD_API_KEY)

        if DNSPOD_API_BASE_URL[-1] != "/":
            self.DNSPOD_API_BASE_URL = DNSPOD_API_BASE_URL + "/"
        else:
            self.DNSPOD_API_BASE_URL = DNSPOD_API_BASE_URL
        super(DNSPodDns, self).__init__()

    def create_dns_record(self, domain_name, domain_dns_value):
        domain_name, _, subd = extract_zone(domain_name)
        if self._type == 1:
            self.add_record(domain_name, subd.replace('_acme-challenge.', ''), domain_dns_value, 'CNAME')
        else:
            self.add_record(domain_name, subd, domain_dns_value, 'TXT')

    def add_record(self, domain_name, subd, domain_dns_value, s_type):
        url = urljoin(self.DNSPOD_API_BASE_URL, "Record.Create")
        body = {
            "record_type": s_type,
            "domain": domain_name,
            "sub_domain": subd,
            "value": domain_dns_value,
            "record_line_id": "0",
            "format": "json",
            "login_token": self.DNSPOD_LOGIN,
        }
        create_dnspod_dns_record_response = requests.post(
            url, data=body, timeout=self.HTTP_TIMEOUT
        ).json()
        if create_dnspod_dns_record_response["status"]["code"] != "1":
            raise ValueError(
                "Error creating dnspod dns record: status_code={status_code} response={response}".format(
                    status_code=create_dnspod_dns_record_response["status"]["code"],
                    response=create_dnspod_dns_record_response["status"]["message"],
                )
            )

    def remove_record(self, domain_name, subd, s_type):
        url = urljoin(self.DNSPOD_API_BASE_URL, "Record.List")
        rootdomain = domain_name
        body = {
            "login_token": self.DNSPOD_LOGIN,
            "format": "json",
            "domain": rootdomain,
            "subdomain": subd,
            "record_type": s_type,
        }

        list_dns_response = requests.post(url, data=body, timeout=self.HTTP_TIMEOUT).json()
        for i in range(0, len(list_dns_response["records"])):
            if list_dns_response["records"][i]['name'] != subd:
                continue
            rid = list_dns_response["records"][i]["id"]
            urlr = urljoin(self.DNSPOD_API_BASE_URL, "Record.Remove")
            bodyr = {
                "login_token": self.DNSPOD_LOGIN,
                "format": "json",
                "domain": rootdomain,
                "record_id": rid,
            }
            requests.post(
                urlr, data=bodyr, timeout=self.HTTP_TIMEOUT
            ).json()

    def delete_dns_record(self, domain_name, domain_dns_value):
        try:
            domain_name, _, subd = extract_zone(domain_name)
            self.remove_record(domain_name, subd, 'TXT')
            self.remove_record(domain_name, '_acme-challenge', 'CNAME')
        except:
            pass

    def add_record_for_creat_site(self, domain, server_ip):
        domain_name, zone, _ = extract_zone(domain)
        self.add_record(domain_name, zone, server_ip, "A")


class NameCheapDns(BaseDns):
    dns_provider_name = "namecheap"
    _type = 0  # 0:lest 1：锐成

    def __init__(self, api_user, api_key, **kwargs):
        super().__init__()
        self.api_user = api_user
        self.api_key = api_key
        self.timeout = 30
        self.base_url = "https://api.namecheap.com/xml.response"

    def _get_hosts(self, domain_name) -> list:
        params = {
            "ApiUser": self.api_user,
            "ApiKey": self.api_key,
            "UserName": self.api_user,
            "Command": "namecheap.domains.dns.getHosts",
            "ClientIp": public.GetLocalIp(),
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
            hosts.append({
                f"HostName{index}": host.get("Name"),
                f"RecordType{index}": host.get("Type"),
                f"Address{index}": host.get("Address"),
                f"TTL{index}": ttl,
            })
        return hosts

    def add_record(self, domain_name, s_type, acme_txt, dns_value):
        hosts = self._get_hosts(domain_name)
        add_index = len(hosts) + 1
        params = {
            "ApiUser": self.api_user,
            "ApiKey": self.api_key,
            "UserName": self.api_user,
            "ClientIp": public.GetLocalIp(),
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
        dns_name = "_acme-challenge" + "." + domain_name
        self.remove_record(domain_name, dns_name, 'TXT')

    def add_record_for_creat_site(self, domain: str, server_ip: str = None):
        server_ip = public.GetLocalIp() if not server_ip else server_ip
        root, zone, _ = extract_zone(domain)
        self.add_record(root, "A", zone, server_ip)

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
            return []

    def get_domains(self) -> list:
        # 获取账号下所有域名, 判断域名nameserver归属, 并且所有返回均为xml
        params = {
            "ApiUser": self.api_user,
            "ApiKey": self.api_key,
            "UserName": self.api_user,
            "Command": "namecheap.domains.getList",  # returns a list of domains for the particular user
            "ClientIp": public.GetLocalIp(),
        }
        resp = requests.get(url=self.base_url, params=params, timeout=self.timeout)
        if resp.status_code != 200:
            return []
        domains = self._generate_xml_tree(resp.text, ".//Domain")
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
                    "ClientIp": public.GetLocalIp(),
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

    # 创建record
    def create_org_record(self, domain_name, record, record_value, record_type, ttl=1, **kwargs):
        domain_name, _, _ = extract_zone(domain_name)
        hosts = self._get_hosts(domain_name)
        add_index = len(hosts) + 1
        params = {
            "ApiUser": self.api_user,
            "ApiKey": self.api_key,
            "UserName": self.api_user,
            "ClientIp": public.GetLocalIp(),
            "Command": "namecheap.domains.dns.setHosts",
            "SLD": domain_name.split(".")[0],
            "TLD": domain_name.split(".")[1],
            "DomainName": domain_name,
        }
        for index, host in enumerate(hosts):
            params[f"HostName{index + 1}"] = host[f"HostName{index + 1}"]
            params[f"Address{index + 1}"] = host[f"Address{index + 1}"]
            params[f"RecordType{index + 1}"] = host[f"RecordType{index + 1}"]
            params[f"TTL{index + 1}"] = host[f"TTL{index + 1}"]

        params[f"HostName{add_index}"] = record
        params[f"Address{add_index}"] = record_value
        params[f"RecordType{add_index}"] = record_type
        params[f"TTL{add_index}"] = ttl
        return self.__set_hosts_with_params(domain_name, params)

    # 删除record
    def remove_record(self, domain_name, record, record_type="TXT") -> dict:
        domain_name, _, _ = extract_zone(domain_name)
        hosts_info = self._get_hosts(domain_name)
        new_hosts = []
        for host in hosts_info:
            if record in host.values() and record_type in host.values():
                continue
            else:
                new_hosts.append(host)
        if not new_hosts:
            # is empty
            return {"status": True, "msg": "Dns Record is empty."}
        new_params = {
            "ApiUser": self.api_user,
            "ApiKey": self.api_key,
            "UserName": self.api_user,
            "ClientIp": public.GetLocalIp(),
            "Command": "namecheap.domains.dns.setHosts",
            "SLD": domain_name.split(".")[0],
            "TLD": domain_name.split(".")[1],
            "DomainName": domain_name,
        }
        for host in new_hosts:
            new_params.update(host)
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
                new_hosts.append(host)
            else:
                new_hosts.append(host)
        if not new_hosts:  # is empty
            return {"status": True, "msg": "Dns Record is empty."}
        new_params = {
            "ApiUser": self.api_user,
            "ApiKey": self.api_key,
            "UserName": self.api_user,
            "ClientIp": public.GetLocalIp(),
            "Command": "namecheap.domains.dns.setHosts",
            "SLD": domain_name.split(".")[0],
            "TLD": domain_name.split(".")[1],
            "DomainName": domain_name,
        }
        for host in new_hosts:
            new_params.update(host)
        return self.__set_hosts_with_params(domain_name, new_params)


class CloudFlareDns(BaseDns):
    dns_provider_name = "cloudflare"
    _type = 0  # 0:lest 1：锐成

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
            raise ValueError(
                "Error creating cloudflare dns record: status_code={status_code} response={response}".format(
                    status_code=find_dns_zone_response.status_code,
                    response=self.log_response(find_dns_zone_response),
                )
            )

        result = find_dns_zone_response.json()["result"]
        for i in result:
            if i["name"] in domain_name:
                setattr(self, "cf_zone_id", i["id"])
        if isinstance(self.cf_zone_id, type(None)):
            raise ValueError(
                "Error unable to get DNS zone for domain_name={domain_name}: status_code={status_code} response={response}".format(
                    domain_name=domain_name,
                    status_code=find_dns_zone_response.status_code,
                    response=self.log_response(find_dns_zone_response),
                )
            )

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
            raise ValueError(
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

    def add_record_for_creat_site(self, domain, server_ip):
        domain_name, zone, _ = extract_zone(domain)
        self.find_dns_zone(domain_name)
        self.add_record(zone, server_ip, "A")

    # =============== 域名管理 ====================

    def get_domains(self) -> list:
        url = self.cf_base_url + "zones?status=active&per_page=1000"
        headers = self._get_auth_headers()
        res = requests.get(url, headers=headers, timeout=self.time_out)
        if res.status_code != 200:
            return []
        try:
            result = res.json().get("result", [])
        except Exception as e:
            public.print_log(f"cloudflare get_domains error {e}")
            result = []
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
    def create_org_record(self, domain_name, record, record_value, record_type, ttl=1, proxied=0):
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


# 未验证
class AliyunDns(object):
    _type = 0  # 0:lest 1：锐成

    def __init__(self, key, secret, ):
        self.key = str(key).strip()
        self.secret = str(secret).strip()
        self.url = "http://alidns.aliyuncs.com"

    def sign(self, accessKeySecret, parameters):  # '''签名方法
        def percent_encode(encodeStr):
            encodeStr = str(encodeStr)
            if sys.version_info[0] == 3:
                import urllib.request
                res = urllib.request.quote(encodeStr, '')
            else:
                res = urllib2.quote(encodeStr, '')
            res = res.replace('+', '%20')
            res = res.replace('*', '%2A')
            res = res.replace('%7E', '~')
            return res

        sortedParameters = sorted(parameters.items(), key=lambda parameters: parameters[0])
        canonicalizedQueryString = ''
        for (k, v) in sortedParameters:
            canonicalizedQueryString += '&' + percent_encode(k) + '=' + percent_encode(v)
        stringToSign = 'GET&%2F&' + percent_encode(canonicalizedQueryString[1:])
        if sys.version_info[0] == 2:
            h = hmac.new(accessKeySecret + "&", stringToSign, sha1)
        else:
            h = hmac.new(bytes(accessKeySecret + "&", encoding="utf8"), stringToSign.encode('utf8'), sha1)
        signature = base64.encodestring(h.digest()).strip()
        return signature

    def create_dns_record(self, domain_name, domain_dns_value):
        root, _, acme_txt = extract_zone(domain_name)
        if self._type == 1:
            acme_txt = acme_txt.replace('_acme-challenge.', '')
            self.add_record(root, 'CNAME', acme_txt, domain_dns_value)
        else:
            try:
                self.add_record(root, 'CAA', '@', caa_value)
            except:
                pass
            self.add_record(root, 'TXT', acme_txt, domain_dns_value)

    def add_record(self, domain, s_type, host, value):
        randomint = random.randint(11111111111111, 99999999999999)
        now = datetime.datetime.utcnow()
        otherStyleTime = now.strftime("%Y-%m-%dT%H:%M:%SZ")
        paramsdata = {
            "Action": "AddDomainRecord", "Format": "json", "Version": "2015-01-09", "SignatureMethod": "HMAC-SHA1",
            "Timestamp": otherStyleTime,
            "SignatureVersion": "1.0", "SignatureNonce": str(randomint), "AccessKeyId": self.key,
            "DomainName": domain,
            "RR": host,
            "Type": s_type,
            "Value": value,
        }

        Signature = self.sign(self.secret, paramsdata)
        paramsdata['Signature'] = Signature
        req = requests.get(url=self.url, params=paramsdata)
        if req.status_code != 200:
            if req.json()['Code'] == 'IncorrectDomainUser' or req.json()['Code'] == 'InvalidDomainName.NoExist':
                raise ValueError("This domain name does not exist under this Ali cloud account. Adding parsing failed.")
            elif req.json()['Code'] == 'InvalidAccessKeyId.NotFound' or req.json()['Code'] == 'SignatureDoesNotMatch':
                raise ValueError("API key error, add parsing failed")
            else:
                raise ValueError(req.json()['Message'])

    def query_recored_items(self, host, zone=None, tipe=None, page=1, psize=200):
        randomint = random.randint(11111111111111, 99999999999999)
        now = datetime.datetime.utcnow()
        otherStyleTime = now.strftime("%Y-%m-%dT%H:%M:%SZ")
        paramsdata = {
            "Action": "DescribeDomainRecords", "Format": "json", "Version": "2015-01-09",
            "SignatureMethod": "HMAC-SHA1", "Timestamp": otherStyleTime,
            "SignatureVersion": "1.0", "SignatureNonce": str(randomint), "AccessKeyId": self.key,
            "DomainName": host,
        }
        if zone:
            paramsdata['RRKeyWord'] = zone
        if tipe:
            paramsdata['TypeKeyWord'] = tipe
        Signature = self.sign(self.secret, paramsdata)
        paramsdata['Signature'] = Signature
        req = requests.get(url=self.url, params=paramsdata)
        return req.json()

    def query_recored_id(self, root, zone, tipe="TXT"):
        record_id = None
        recoreds = self.query_recored_items(root, zone, tipe=tipe)
        recored_list = recoreds.get("DomainRecords", {}).get("Record", [])
        recored_item_list = [i for i in recored_list if i["RR"] == zone]
        if len(recored_item_list):
            record_id = recored_item_list[0]["RecordId"]
        return record_id

    def remove_record(self, domain, host, s_type='TXT'):
        record_id = self.query_recored_id(domain, host, s_type)
        if not record_id:
            msg = "Cannot find record_id for domain name: ", domain
            print(msg)
            return
        randomint = random.randint(11111111111111, 99999999999999)
        now = datetime.datetime.utcnow()
        otherStyleTime = now.strftime("%Y-%m-%dT%H:%M:%SZ")
        paramsdata = {
            "Action": "DeleteDomainRecord", "Format": "json", "Version": "2015-01-09", "SignatureMethod": "HMAC-SHA1",
            "Timestamp": otherStyleTime,
            "SignatureVersion": "1.0", "SignatureNonce": str(randomint), "AccessKeyId": self.key,
            "RecordId": record_id,
        }
        Signature = self.sign(self.secret, paramsdata)
        paramsdata['Signature'] = Signature
        req = requests.get(url=self.url, params=paramsdata)
        if req.status_code != 200:
            raise ValueError("Deleting a parse record failed")

    def delete_dns_record(self, domain_name, domain_dns_value):
        root, _, acme_txt = extract_zone(domain_name)
        self.remove_record(root, acme_txt, 'TXT')
        self.remove_record(root, '@', 'CAA')
        self.remove_record(root, '_acme-challenge', 'CNAME')

    def add_record_for_creat_site(self, domain, server_ip):
        root, zone, _ = extract_zone(domain)
        self.add_record(root, "A", zone, server_ip)


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


# 未验证
class Dns_com(object):
    _type = 0  # 0:lest 1：锐成

    def __init__(self, key, secret):
        pass

    def get_dns_obj(self):
        p_path = '/www/server/panel/plugin/dns'
        if not os.path.exists(p_path + '/dns_main.py'): return None
        sys.path.insert(0, p_path)
        # noinspection PyUnresolvedReferences
        import dns_main
        public.mod_reload(dns_main)
        return dns_main.dns_main()

    def create_dns_record(self, domain_name, domain_dns_value):
        root, _, acme_txt = extract_zone(domain_name)

        if self._type == 1:
            acme_txt = acme_txt.replace('_acme-challenge.', '')
            result = self.add_record(acme_txt + '.' + root, domain_dns_value)
        else:
            result = self.get_dns_obj().add_txt(acme_txt + '.' + root, domain_dns_value)

        if result == "False":
            raise ValueError(
                '[DNS] This domain name does not exist in the currently bound Pagoda DNS cloud resolution account. Adding parsing failed!')
        time.sleep(5)

    def delete_dns_record(self, domain_name, domain_dns_value):
        root, _, acme_txt = extract_zone(domain_name)
        self.get_dns_obj().remove_txt(acme_txt + '.' + root)


# 未验证
class DNSLADns(BaseDns):
    dns_provider_name = "dnsla"
    _type = 0  # 0:lest 1：锐成

    def __init__(self, api_id, api_secret):
        self.api_id = api_id
        self.api_secret = api_secret
        self.base_url = "https://api.dns.la"
        self.http_timeout = 65  # seconds
        self._token = None
        self.domain_list = None
        super(DNSLADns, self).__init__()

    def _get_auth_headers(self) -> dict:
        if self._token is None:
            self._token = base64.b64encode("{}:{}".format(self.api_id, self.api_secret).encode("utf-8")).decode("utf-8")
        return {"Authorization": "Basic " + self._token}

    def find_dns_zone(self, domain_name):
        url = urljoin(self.base_url, "/api/domainList?pageIndex=1&pageSize=1000")
        headers = self._get_auth_headers()
        find_dns_zone_response = requests.get(url, headers=headers, timeout=self.http_timeout)
        if find_dns_zone_response.status_code != 200:
            raise ValueError(
                "Error creating DNS.LA domains: status_code={status_code} response={response}".format(
                    status_code=find_dns_zone_response.status_code,
                    response=self.log_response(find_dns_zone_response),
                )
            )

        result = find_dns_zone_response.json()["data"]["results"]
        self.domain_list = result
        have = False
        for domain_data in result:
            if domain_data["domain"].rstrip(".") == domain_name:
                have = True
                break

        if not have:
            raise ValueError(
                (
                    "Error unable to get DNS zone for domain_name={domain_name}: "
                    "status_code={status_code} response={response}"
                ).format(
                    domain_name=domain_name,
                    status_code=find_dns_zone_response.status_code,
                    response=self.log_response(find_dns_zone_response),
                )
            )

    @staticmethod
    def _format_s_type_to_request(s_type):
        trans = {
            "A": 1,
            "NS": 2,
            "CNAME": 5,
            "MX": 15,
            "TXT": 16,
            "AAAA": 28,
            "SRV": 33,
            "CAA": 257,
            "URL": 256
        }

        if isinstance(s_type, (int, float)):
            if int(s_type) in trans.values():
                return int(s_type)

        if isinstance(s_type, str):
            if s_type in trans:
                return trans[s_type]
        return 16

    def add_record(self, domain, s_type, host, value):
        url = urljoin(self.base_url, "/api/record", )
        headers = self._get_auth_headers()

        domain_id = self._get_domain_id(domain)

        body = {
            "domainId": domain_id,
            "type": self._format_s_type_to_request(s_type),
            "host": host,
            "data": value,
            "ttl": 600,
        }

        create_dns_la_record_response = requests.post(
            url, headers=headers, json=body, timeout=self.http_timeout
        )
        if create_dns_la_record_response.status_code != 200:
            raise ValueError(
                "Error creating cloudflare dns record: status_code={status_code} response={response}".format(
                    status_code=create_dns_la_record_response.status_code,
                    response=self.log_response(create_dns_la_record_response),
                )
            )

    def create_dns_record(self, domain_name, domain_dns_value):
        domain_name = domain_name.lstrip("*.")
        root, zone, acme_txt = extract_zone(domain_name)
        self.find_dns_zone(root)

        if self._type == 1:
            return self.add_record(root, 'CNAME', acme_txt.replace('_acme-challenge.', ''), domain_dns_value)
        else:
            return self.add_record(root, 'TXT', acme_txt, domain_dns_value)

    def add_record_for_creat_site(self, domain, server_ip):
        root, zone, _ = extract_zone(domain)
        self.add_record(root, "A", zone, server_ip)

    def get_record_list(self, domain_id: str) -> list:
        url = urljoin(self.base_url, "/api/recordList?pageIndex=1&pageSize=10&domainId={}".format(domain_id))
        headers = self._get_auth_headers()
        get_record_list_response = requests.get(url, headers=headers, timeout=self.http_timeout)
        if get_record_list_response.status_code != 200:
            raise ValueError(
                "Error unable to get record list : status_code={status_code} response={response}".format(
                    status_code=get_record_list_response.status_code,
                    response=self.log_response(get_record_list_response),
                )
            )

        result = get_record_list_response.json()["data"]["results"]
        if isinstance(result, list):
            return result
        else:
            return []

    def _get_domain_id(self, domain_name: str) -> str:
        if domain_name.count('.') > 2:
            domain_name, _, _ = extract_zone(domain_name)
        if self.domain_list is None:
            self.find_dns_zone(domain_name)
        domain_id = None
        for domain_data in self.domain_list:
            if domain_data["domain"].rstrip(".") == domain_name:
                domain_id = domain_data["id"]
        if domain_id is None:
            raise ValueError(
                "Error unable to get DNS zone for domain_name={domain_name}".format(domain_name=domain_name))
        return domain_id

    def remove_record(self, domain_name, dns_name, s_type):
        domain_id = self._get_domain_id(domain_name)
        record_list = self.get_record_list(domain_id)
        trans_type = self._format_s_type_to_request(s_type)
        remove_record_id_list = []
        for record in record_list:
            if record["type"] == trans_type and (record["host"] == dns_name or record["displayHost"] == dns_name):
                remove_record_id_list.append(record["id"])

        headers = self._get_auth_headers()

        del_record_url_list = [urljoin(self.base_url, "/api/record?id={}".format(i)) for i in remove_record_id_list]

        for del_record_url in del_record_url_list:
            requests.delete(
                del_record_url, headers=headers, timeout=self.http_timeout
            )

    def delete_dns_record(self, domain_name, domain_dns_value):
        domain_name = domain_name.lstrip("*.")
        root, zone, acme_txt = extract_zone(domain_name)
        self.remove_record(root, acme_txt, 'TXT')


class DnsMager(object):
    """
    config = {
        "CloudFlareDns": [
            {
                "E-Mail": "122456944@qq.com",
                "API Key": "dsgvfcdkjausvgfkjasdfgakj",
                "ps": "xxx",
                "id": 1,
                "domains": [  # domains 可以不存在，内容是根域名
                ]
            }
        ]
        ........
    }"""

    CONF_FILE = "{}/config/dns_mager.conf".format(public.get_panel_path())
    CLS_MAP: Dict = {
        "AliyunDns": AliyunDns,
        "DNSPodDns": DNSPodDns,
        "CloudFlareDns": CloudFlareDns,
        # "GoDaddyDns": GoDaddyDns,
        "DNSLADns": DNSLADns,
        "HuaweiCloudDns": HuaweiCloudDns,
        "TencentCloudDns": TencentCloudDns,
    }
    RULE_MAP: Dict[str, List[str]] = {
        "AliyunDns": ["AccessKey", "SecretKey"],
        "DNSPodDns": ["ID", "Token"],
        "CloudFlareDns": ["E-Mail", "API Key"],
        "GoDaddyDns": ["Key", "Secret"],
        "DNSLADns": ["APIID", "API密钥"],
        "HuaweiCloudDns": ["ak", "sk", "project_id"],
        "TencentCloudDns": ["secret_id", "secret_key"],
    }

    def __init__(self):
        self._config: Optional[Dict[str, Dict[str, Union[int, str]]]] = None

    @staticmethod
    def _get_new_id() -> str:
        return uuid4().hex

    @classmethod
    def _read_config_old(cls) -> Optional[Dict[str, List[Dict[str, Union[str, list]]]]]:
        old_config_file = "{}/config/dns_api.json".format(public.get_panel_path())
        if os.path.isfile(old_config_file):
            try:
                data = json.loads(public.readFile(old_config_file))
            except json.JSONDecodeError:
                return None
            res = {}
            rule_list = ("AliyunDns", "DNSPodDns", "CloudFlareDns", "GoDaddyDns")
            if isinstance(data, list):
                for d in data:
                    if d["name"] not in rule_list:
                        continue

                    conf_data = d.get("data", None)
                    if isinstance(data, list):
                        tmp = {i["name"]: i["value"] for i in conf_data if i["value"].strip()}
                        tmp["ps"] = "default account"
                        tmp["id"] = cls._get_new_id()
                        if len(tmp) > 2:
                            res[d["name"]] = [tmp]

            if res:
                return res
        return None

    @staticmethod
    def _get_acme_dns_api() -> Dict[str, Dict[str, str]]:
        path = '/root/.acme.sh'
        if not os.path.exists(path + '/account.conf'):
            path = "/.acme.sh"
        account = public.readFile(path + '/account.conf')
        if not account:
            return {}
        rule_map: Dict[str, Dict[str, str]] = {
            "AliyunDns": {
                "AccessKey": "SAVED_Ali_Key",
                "SecretKey": "SAVED_Ali_Secret",
            },
            "DNSPodDns": {
                "ID": "SAVED_DP_Id",
                "Token": "SAVED_DP_Key"
            },
            "CloudFlareDns": {
                "E-Mail": "SAVED_CF_MAIL",
                "API Key": "SAVED_CF_KEY",
            },
            "GoDaddyDns": {
                "Key": "SAVED_GD_Key",
                "Secret": "SAVED_GD_Secret",
            },
            "DNSLADns": {
                "APIID": "SAVED_LA_Id",
                "API密钥": "SAVED_LA_Key"
            }
        }
        res = {}
        for rule_name, rule in rule_map.items():
            tmp = {}
            for r_key, r_value in rule.items():
                account_res = re.search(r_value + r"\s*=\s*'(.+)'", account)
                if account_res:
                    tmp[r_key] = account_res.groups()[0]

            if len(tmp) == len(rule):
                res[rule_name] = tmp
        return res

    @property
    def config(self) -> dict:
        if self._config is not None:
            return self._config
        change = False
        if not os.path.exists(self.CONF_FILE):
            change = True
            old_config = self._read_config_old()
            if old_config is not None:
                self._config = old_config
            else:
                self._config = {}

            l_data = self._get_config_data_from_letsencrypt_data()
            if l_data is not None:
                for tmp_conf in l_data:
                    key = tmp_conf["dns_name"]
                    if key not in self._config:
                        self._config[key] = []
                    for v in self._config[key]:
                        if all([v.get(n, None) == m for n, m in tmp_conf["conf_data"].items()]):
                            break
                    else:
                        tmp_data = {
                            "ps": "default account form config",
                            "id": self._get_new_id(),
                        }
                        tmp_data.update(tmp_conf["conf_data"])
                        self._config[key].append(tmp_data)
        else:
            try:
                config_data = json.loads(public.readFile(self.CONF_FILE))
            except json.JSONDecodeError:
                self._config = {}
            else:
                if isinstance(config_data, dict):
                    self._config = config_data
                else:
                    self._config = {}

        acme_conf = self._get_acme_dns_api()
        if acme_conf:
            for key, value in acme_conf.items():
                if key not in self._config:
                    self._config[key] = []
                for v in self._config[key]:
                    if all([v.get(n, None) == m for n, m in value.items()]):
                        break
                else:
                    change = True
                    value["ps"] = "found acme_dns"
                    value["id"] = self._get_new_id()
                    self._config[key].append(value)

        if change:
            self.save_config()

        return self._config

    def save_config(self):
        if self._config is None:
            _ = self.config
        public.writeFile(self.CONF_FILE, json.dumps(self._config))

    def get_dns_objs_by_name(self, dns_name: str) -> List[BaseDns]:
        if dns_name not in self.CLS_MAP.keys():
            raise Exception(f"{dns_name} not support")

        for key, value in self.config.items():
            if key == dns_name:
                for dns_config in value:
                    return self.CLS_MAP[key].new(dns_config)
        raise Exception("No valid DNS API key information for the domain name {} was found.".format(dns_name))

    def get_dns_obj_by_domain(self, domain) -> BaseDns:
        root, _, _ = extract_zone(domain)
        try:
            data = public.M('ssl_domains').field('dns_id').where("domain=?", (root,)).select()
            dns_id = data[0]['dns_id']
        except:
            dns_id = ''
        for key, value in self.config.items():
            for dns_config in value:
                if root in dns_config.get("domains", []) or str(dns_id) == dns_config["id"]:
                    return self.CLS_MAP[key].new(dns_config)
        raise Exception("No valid DNS API key information for the domain name {} was found.".format(domain))

    def get_dns_by_auth_string(self, auth_string: str) -> BaseDns:
        tmp = auth_string.split('|')
        dns_name = tmp[0]
        if dns_name not in self.CLS_MAP:
            raise Exception(f"{auth_string} not support")
        if len(tmp) >= 3:
            if tmp[2] == "":
                key = None
                secret = tmp[1]
            else:
                key = tmp[1]
                secret = tmp[2]
            return self.CLS_MAP.get(dns_name).new({"key": key, "secret": secret})
        else:
            config_list = self.config.get(dns_name, [])
            if len(config_list) == 0:
                raise Exception(
                    "No valid DNS API key information for the domain name {} was found.".format(auth_string)
                )
            return self.CLS_MAP.get(dns_name).new(config_list[0])

    def add_conf(self, dns_type: str, conf_data: list, ps: str, domains: list, force_domain: str):
        if dns_type not in self.CLS_MAP:
            return False, "Unsupported DNS platform"

        f, data = self._parse_data(conf_data, dns_type)
        if not f:
            return False, data

        if not isinstance(domains, list):
            return False, "The format of the domain name parameter is incorrect."

        if dns_type not in self.config:
            self.config[dns_type] = []

        for v in self.config[dns_type]:
            if all([v.get(n, None) == m for n, m in data.items()]):
                return False, "This pass credential has been added already."

        data["ps"] = ps
        data["id"] = self._get_new_id()
        root_list = self.paser_domains_list_to_root_list(domains)
        all_domains = self._get_all_root(with_out=None)
        for root in root_list:
            if root in all_domains:
                return False, "The domain name {} is already bound to another API account and cannot be added.".format(
                    root)

        if force_domain is not None and not isinstance(force_domain, str):
            return False, "The format of the domain name parameter is incorrect."
        if force_domain is not None:
            force_root = self.paser_domains_list_to_root_list([force_domain])[0]
            if force_root not in root_list:
                if force_root in all_domains:
                    self.remove_domains_by_root(force_root)

        data["domains"] = root_list
        self.config[dns_type].append(data)
        self.save_config()
        return True, "Save successfully!"

    def _parse_data(self, conf_data: List[dict], dns_type: str) -> Tuple[bool, Union[dict, str]]:
        data = {}
        if not isinstance(conf_data, list):
            return False, "wrong params"
        for conf in conf_data:
            if isinstance(conf, dict) and "name" in conf and "value" in conf:
                data[conf.get("name")] = conf.get("value")
        if not data:
            return False, "The parameter format is incorrect. No parameters were specified."
        if dns_type == "CloudFlareDns" and len(data) == 1 and "API Token" in data:
            return True, data

        for n in self.RULE_MAP[dns_type]:
            if n not in data:
                return False, "The parameter format is incorrect. The parameter name does not match the platform."

        return True, data

    def modify_conf(self, api_id: str, dns_type: str, conf_data: list, ps: str, domains: list, force_domain: str):
        # 强制添加的域名
        if dns_type not in self.CLS_MAP:
            return False, "Unsupported DNS platform"

        target_idx = -1
        if dns_type not in self.config:
            self.config[dns_type] = []

        for idx, v in enumerate(self.config[dns_type]):
            if api_id == v.get("id", None):
                target_idx = idx

        if target_idx == -1:
            return False, "account not found"

        if conf_data is not None:
            f, data = self._parse_data(conf_data, dns_type)
            if not f:
                return False, data

            self.config[dns_type][target_idx].update(**data)
            if ps is not None:
                self.config[dns_type][target_idx].update(ps=ps)

        if domains is not None and not isinstance(domains, list):
            return False, "wrong params"

        if domains is not None:
            root_list = self.paser_domains_list_to_root_list(domains)
            all_domains = self._get_all_root(with_out=self.config[dns_type][target_idx].get("domains"))
            for root in root_list:
                if root in all_domains:
                    return False, "The domain name {} is already bound to another API account and cannot be added.".format(
                        root)
            self.config[dns_type][target_idx]["domains"] = root_list

        if force_domain is not None and not isinstance(force_domain, str):
            return False, "wrong params"
        if force_domain is not None:
            root = self.paser_domains_list_to_root_list([force_domain])[0]
            self.remove_domains_by_root(root)
            if "domains" not in self.config[dns_type][target_idx]:
                self.config[dns_type][target_idx]["domains"] = []
            self.config[dns_type][target_idx]["domains"].append(root)

        self.save_config()
        return True, "Update successfully!"

    def remove_domains_by_root(self, root: str):
        for key, value in self.config.items():
            for dns_config in value:
                domains = dns_config.get("domains", None)
                if domains is not None and root in domains:
                    domains.remove(root)

    def _get_all_root(self, with_out: Optional[List[str]]) -> Set[str]:
        all_domains = set(
            chain(*[c.get("domains", []) for c in
                    chain(*[c_list for c_list in self.config.values()])]
                  )
        )
        if with_out is not None:
            return all_domains - set(with_out)
        return all_domains

    def test_domains_api(self, domains: List[str]) -> List[dict]:
        res = [{}] * len(domains)
        for idx, domain in enumerate(domains):
            root = self.paser_domains_list_to_root_list([domain])[0]
            for key, conf in self.config.items():
                for c in conf:
                    if root in c.get("domains", []):
                        res[idx] = {
                            "dns_name": key,
                            "conf": c,
                            "rooot": root,
                            "domain": domain
                        }
        return res

    def remove_conf(self, api_id: str, dns_type: str):
        if dns_type not in self.CLS_MAP:
            return False, "Unsupported DNS platform"

        if dns_type not in self.config:
            self.config[dns_type] = []
        target_idx = -1
        for idx, v in enumerate(self.config[dns_type]):
            if api_id == v.get("id", None):
                target_idx = idx

        if target_idx == -1:
            return False, "account not found"

        del self.config[dns_type][target_idx]
        self.save_config()
        return True, "Del successfully!"

    @classmethod
    def paser_auth_to(cls, auth_to_string: str) -> Tuple[Optional[str], Optional[Dict[str, str]]]:
        tmp = auth_to_string.split('|')
        dns_name = tmp[0]
        if dns_name not in cls.CLS_MAP:
            return None, None
        if len(tmp) != 3:
            return None, None

        if tmp[2] == "":
            key = None
            secret = tmp[1]
        else:
            key = tmp[1]
            secret = tmp[2]

        if dns_name == "CloudFlareDns" and key is None:
            return "CloudFlareDns", {"API Token": secret}
        elif key and secret:
            return dns_name, dict(zip(cls.RULE_MAP[dns_name], [key, secret]))
        return None, None

    @classmethod
    def paser_domains_list_to_root_list(cls, domains_list: List[str]) -> List[str]:
        res = []
        for domain in domains_list:
            root, _, _ = extract_zone(domain)
            if root in res:
                continue
            res.append(root)
        return res

    @classmethod
    def _get_config_data_from_letsencrypt_data(cls) -> Optional[List[Dict[str, Union[str, list, dict]]]]:
        conf_file = "{}/config/letsencrypt.json".format(public.get_panel_path())
        if not os.path.exists(conf_file):
            return None
        tmp_config = public.readFile(conf_file)
        try:
            orders = json.loads(tmp_config)["orders"]
        except (json.JSONDecodeError, KeyError):
            return None

        res = {}
        for order in orders:
            if 'auth_type' in order and order['auth_type'] == "dns":
                if order["auth_to"].find("|") == -1 or order["auth_to"].find("/") != -1:  # 文件验证跳过
                    continue
                if order["auth_to"] in res:
                    tmp_conf = res[order["auth_to"]]
                else:
                    dns_name, conf_dict = cls.paser_auth_to(order["auth_to"])
                    if dns_name is None:
                        continue
                    tmp_conf = {
                        "dns_name": dns_name,
                        "conf_data": conf_dict,
                        "domains": []
                    }
                    res[order["auth_to"]] = tmp_conf
                root_list = order.get("domains", [])
                for root in root_list:
                    if root not in tmp_conf["domains"]:
                        tmp_conf["domains"].append(root)

        if len(res) == 0:
            return None
        return list(res.values())
