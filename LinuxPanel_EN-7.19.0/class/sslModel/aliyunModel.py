import time

from sslModel.base import sslBase

import public
import os

from urllib.parse import urlencode, quote_plus
import hashlib
import hmac
import uuid
import pytz
import requests
from datetime import datetime



class main(sslBase):
    dns_provider_name = "aliyun"
    _type = 0

    def __init__(self):
        super().__init__()

    def __init_data(self, data):
        self.access_key_id = data["AccessKey"]
        self.access_key_secret = data["SecretKey"]
        self.endpoint = "alidns.cn-hangzhou.aliyuncs.com"
        self.ALGORITHM = "ACS3-HMAC-SHA256"
        self.x_acs_version = "2015-01-09"

    def sign_to_response(self, dns_id, action, query_param):
        self.__init_data(self.get_dns_data(None)[dns_id])

        def hmac256(key, msg):
            return hmac.new(key, msg.encode('utf-8'), hashlib.sha256).digest()

        def sha256_hex(s):
            return hashlib.sha256(s.encode('utf-8')).hexdigest()

        def percent_code(encoded_str):
            return encoded_str.replace('+', '%20').replace('*', '%2A').replace('%7E', '~')

        headers = {
            "host": self.endpoint,
            "x-acs-action": action,
            "x-acs-version": self.x_acs_version,
            "x-acs-date": datetime.now(pytz.timezone('Etc/GMT')).strftime('%Y-%m-%dT%H:%M:%SZ'),
            "x-acs-signature-nonce": str(uuid.uuid4()),
        }

        sorted_query_params = sorted(query_param.items(), key=lambda item: item[0])
        query_param = {k: v for k, v in sorted_query_params}

        # Step 1: Construct Canonical Query String and Payload Hash
        canonical_query_string = '&'.join(
            f'{percent_code(quote_plus(k))}={percent_code(quote_plus(str(v)))}' for k, v in
            query_param.items())
        hashed_request_payload = sha256_hex('')
        headers['x-acs-content-sha256'] = hashed_request_payload
        sorted_headers = sorted(headers.items(), key=lambda item: item[0])
        headers = {k: v for k, v in sorted_headers}

        # Construct Canonical Headers and Signed Headers
        canonical_headers = '\n'.join(f'{k.lower()}:{v}' for k, v in headers.items() if
                                      k.lower().startswith('x-acs-') or k.lower() in ['host', 'content-type'])
        signed_headers = ';'.join(sorted(headers.keys(), key=lambda x: x.lower()))

        canonical_request = f'GET\n/\n{canonical_query_string}\n{canonical_headers}\n\n{signed_headers}\n{hashed_request_payload}'

        # Step 2: Construct String to Sign
        hashed_canonical_request = sha256_hex(canonical_request)
        string_to_sign = f'{self.ALGORITHM}\n{hashed_canonical_request}'

        # Step 3: Compute Signature
        signature = hmac256(self.access_key_secret.encode('utf-8'), string_to_sign).hex().lower()

        # Step 4: Construct Authorization Header
        authorization = f'{self.ALGORITHM} Credential={self.access_key_id},SignedHeaders={signed_headers},Signature={signature}'
        headers['Authorization'] = authorization

        url = f'https://{self.endpoint}/'
        if query_param:
            url += '?' + urlencode(query_param, doseq=True, safe='*')
        headers = {k: v for k, v in headers.items()}

        response = requests.request(method="GET", url=url, headers=headers)
        return response


    def create_dns_record(self, get):
        domain_name = get.domain_name
        domain_dns_value = get.domain_dns_value
        record_type = 'TXT'
        if 'record_type' in get:
            record_type = get.record_type

        domain_name, sub_domain, _ = self.extract_zone(domain_name)

        if not sub_domain:
            sub_domain = '@'

        query_param = {
            "DomainName": domain_name,
            "RR": sub_domain,
            "Type": record_type,
            "Value": domain_dns_value
        }

        try:
            response = self.sign_to_response(get.dns_id, "AddDomainRecord", query_param)
            if response.status_code != 200:
                return public.returnMsg(False, self.get_error(response.text))
            return public.returnMsg(True, '添加成功')
        except Exception as e:
            return public.returnMsg(False, self.get_error(str(e)))

    def delete_dns_record(self, get):
        RecordId = get.RecordId

        try:
            response = self.sign_to_response(get.dns_id, "DeleteDomainRecord", {"RecordId":RecordId})
            if response.status_code != 200:
                return public.returnMsg(False, self.get_error(response.text))
            return public.returnMsg(True, '删除成功')
        except Exception as e:
            return public.returnMsg(False, self.get_error(str(e)))

    def get_dns_record(self, get):
        domain_name, _, sub_domain = self.extract_zone(get.domain_name)
        data = {}
        try:
            response = self.sign_to_response(get.dns_id, "DescribeDomainRecords", {"DomainName": domain_name})
            res = response.json()
            if response.status_code != 200:
                return {}
            data["list"] = [
                {
                    "RecordId": i["RecordId"],
                    "name": i["RR"] + "." + domain_name if i["RR"] != '@' else domain_name,
                    "value": i["Value"],
                    "line": i["Line"],
                    "ttl": i["TTL"],
                    "type": i["Type"],
                    "status": "启用" if i["Status"] == "ENABLE" else "暂停" if i["Status"] == "DISABLE" else i["Status"],
                    "mx": i.get("Priority") or 0,
                    "updated_on": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(i["UpdateTimestamp"] / 1000)),
                    "remark": i.get("Remark") or "",
                }
                for i in res["DomainRecords"]["Record"]
            ]
            data["info"] = {
                "record_total": res["TotalCount"]
            }

        except Exception as e:
            pass
        self.set_record_data({domain_name: data})
        return data

    def update_dns_record(self, get):
        RecordId = get.RecordId
        domain_name = get.domain_name
        domain_dns_value = get.domain_dns_value
        record_type = get.record_type

        domain_name, sub_domain, _ = self.extract_zone(domain_name)

        try:
            params = {
                "RecordId": RecordId,
                "Type": record_type,
                "Value": domain_dns_value,
                "RR": sub_domain,
            }
            response = self.sign_to_response(get.dns_id, "UpdateDomainRecord", params)
            if response.status_code != 200:
                return public.returnMsg(False, self.get_error(response.text))
            return public.returnMsg(True, "修改成功")
        except Exception as e:
            return public.returnMsg(False, self.get_error(str(e)))

    def get_error(self, error):
        if "DomainRecordConflict" in error:
            return "与其他记录冲突，不能添加"
        elif "SubDomainInvalid.Value" in error:
            return "DNS记录值无效或者格式错误"
        elif "DomainRecordDuplicate" in error:
            return "解析记录已存在"
        elif "The parameter value RR is invalid" in error:
            return "主机记录错误，请检查后重试"
        elif "InvalidDomainName.NoExist" in error:
            return "这个阿里云账户下面不存在这个域名，请检查dns接口配置后重试"
        elif "IncorrectDomainUser" in error:
            return "这个阿里云账户下面不存在这个域名，请检查dns接口配置后重试"
        elif "InvalidAccessKeyId.NotFound" in error:
            return "无效的Access Key"
        else:
            return error
