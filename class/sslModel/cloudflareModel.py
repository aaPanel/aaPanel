from sslModel.base import sslBase
import requests
from urllib.parse import urlparse
from urllib.parse import urljoin
import public


class main(sslBase):
    dns_provider_name = "cloudflare"
    _type = 0  # 0:lest 1：锐成

    def __init__(self):
        super().__init__()

    def __init_data(self, data):
        self.CLOUDFLARE_EMAIL = data['E-Mail']
        self.CLOUDFLARE_API_KEY = data['API Key']
        self.CLOUDFLARE_API_BASE_URL = 'https://api.cloudflare.com/client/v4/'
        self.HTTP_TIMEOUT = 65  # seconds

        self.headers = {
            "X-Auth-Email": self.CLOUDFLARE_EMAIL,
            "X-Auth-Key": self.CLOUDFLARE_API_KEY
        }

    def get_dns_record(self, get):
        domain_name = get.domain_name
        dns_id = get.dns_id
        self.__init_data(self.get_dns_data(None)[dns_id])

        root_domain, _, sub_domain = self.extract_zone(domain_name)
        data = {}
        try:
            zone_dic = self.get_zoneid_dic(get)
            zone_id = zone_dic[root_domain]
            url = urljoin(self.CLOUDFLARE_API_BASE_URL, "zones/{}/dns_records".format(zone_id))
            response = requests.get(url, headers=self.headers, timeout=self.HTTP_TIMEOUT).json()
            data = {
                "info": {
                    'record_total': response['result_info']['total_count']
                },
                "list": [
                    {
                        "RecordId": i["id"],
                        "name": i["name"],
                        "domain_name": i["name"],
                        "value": i["content"],
                        "line": "默认",
                        "ttl": i["ttl"],
                        "type": i["type"],
                        "status": "启用",
                        "mx": i.get("priority") or 0,
                        "updated_on": i["modified_on"],
                        "remark": i.get("comment") or "",
                    }
                    for i in response["result"]
                ]
            }

        except Exception as e:
            pass
        self.set_record_data({domain_name: data})
        return data

    def create_dns_record(self, get):
        domain_name = get.domain_name
        dns_id = get.dns_id
        record_type = get.record_type
        domain_dns_value = get.domain_dns_value

        self.__init_data(self.get_dns_data(None)[dns_id])

        root_domain, sub_domain, _ = self.extract_zone(domain_name)
        body = {
            "content": get.domain_dns_value,
            "name": sub_domain or '@',
            "type": get.record_type if 'record_type' in get else 'TXT'
        }
        # CAA记录特殊处理
        if record_type == 'CAA':
            values = domain_dns_value.split(' ')
            if len(values) != 3 or values[1] not in ("issue", "issuewild", "iodef"):
                return public.returnMsg(False, '解析记录格式错误，请检查后重试')
            body["data"] = {
                    "flags": values[0],
                    "tag": values[1],
                    "value": values[2].replace('"', ''),
                }

        try:
            zone_dic = self.get_zoneid_dic(get)
            zone_id = zone_dic.get(root_domain)
            if not zone_id:
                return public.returnMsg(False, '此域名配置的dns账号不正确')
            url = urljoin(self.CLOUDFLARE_API_BASE_URL, "zones/{}/dns_records".format(zone_id))
            response = requests.post(url, headers=self.headers, json=body, timeout=self.HTTP_TIMEOUT)
            if response.status_code == 200:
                return public.returnMsg(True, '添加成功')
            else:
                return public.returnMsg(False, '添加失败，{}'.format(self.get_error(response.text)))
        except Exception as e:
            return public.returnMsg(False, '添加失败，msg：{}'.format(e))

    def delete_dns_record(self, get):
        domain_name = get.domain_name
        dns_id = get.dns_id
        RecordId = get.RecordId

        self.__init_data(self.get_dns_data(None)[dns_id])

        root_domain, sub_domain, _ = self.extract_zone(domain_name)

        try:
            zone_dic = self.get_zoneid_dic(get)
            zone_id = zone_dic.get(root_domain)
            if not zone_id:
                return public.returnMsg(False, '此域名配置的dns账号不正确')
            url = urljoin(self.CLOUDFLARE_API_BASE_URL, "zones/{}/dns_records/{}".format(zone_id, RecordId))
            response = requests.delete(url, headers=self.headers, timeout=self.HTTP_TIMEOUT)
            if response.status_code == 200:
                return public.returnMsg(True, '删除成功')
            else:
                return public.returnMsg(False, self.get_error(response.text))
        except Exception as e:
            return public.returnMsg(False, '删除失败，msg：{}'.format(e))

    def get_zoneid_dic(self, get):
        dns_id = get.dns_id
        self.__init_data(self.get_dns_data(None)[dns_id])

        url = urljoin(self.CLOUDFLARE_API_BASE_URL, "zones?status=active&per_page=1000")
        try:
            response = requests.get(url, headers=self.headers, timeout=self.HTTP_TIMEOUT)
            data = response.json()
            return {i["name"]: i["id"] for i in data["result"]}
        except:
            return {}

    def update_dns_record(self, get):
        domain_name = get.domain_name
        RecordId = get.RecordId
        domain_dns_value = get.domain_dns_value
        record_type = get.record_type
        dns_id = get.dns_id

        self.__init_data(self.get_dns_data(None)[dns_id])

        root_domain, sub_domain, _ = self.extract_zone(domain_name)

        body = {
            "content": get.domain_dns_value,
            "name": sub_domain or '@',
            "type": get.record_type,
        }

        # CAA记录特殊处理
        if record_type == 'CAA':
            values = domain_dns_value.split(' ')
            if len(values) != 3:
                return public.returnMsg(False, '解析记录格式错误，请检查后重试')
            body["data"] = {
                    "flags": values[0],
                    "tag": values[1],
                    "value": values[2].replace('"', ''),
                }
        try:
            zone_dic = self.get_zoneid_dic(get)
            zone_id = zone_dic.get(root_domain)
            if not zone_id:
                return public.returnMsg(False, '此域名配置的dns账号不正确')
            url = urljoin(self.CLOUDFLARE_API_BASE_URL, "zones/{}/dns_records/{}".format(zone_id, RecordId))
            response = requests.patch(url, headers=self.headers, json=body, timeout=self.HTTP_TIMEOUT)
            if response.status_code == 200:
                return public.returnMsg(True, '修改成功')
            else:
                return public.returnMsg(False, '修改失败，{}'.format(self.get_error(response.text)))
        except Exception as e:
            return public.returnMsg(False, '修改失败，msg：{}'.format(e))

    def get_error(self, error):
        if "Record does not exist" in error:
            return "解析记录不存在"
        elif "Content for A record must be a valid IPv4 address" in error:
            return "【A】记录的解析值必须为IPv4地址"
        elif "Content for CNAME record is invalid" in error:
            return "请正确填写【CNAME】类型的解析值"
        elif "DNS record type is invalid" in error:
            return "解析记录类型无效"
        elif "A record with the same settings already exists" in error:
            return "已存在相同的解析记录"
        elif "Error unable to get DNS zone for domain_name" in error:
            return "这个cloudflare账户下面不存在这个域名，请检查dns接口配置后重试"
        else:
            return error
