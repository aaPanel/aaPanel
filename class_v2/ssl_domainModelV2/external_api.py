# coding: utf-8
# ------------------------------
# 对外接口
# ------------------------------
import json
from datetime import datetime

import public
from panelDnsapi import extract_zone
from public.validate import Param
from .model import DnsDomainProvider, DnsDomainSSL, DnsDomainRecord


class SubPanelApi:
    date_format = "%Y-%m-%d"

    @staticmethod
    def _end_time(data_str: str) -> int:
        try:
            if not data_str:
                return 0
            today = datetime.today().date()
            end_date = datetime.strptime(data_str, SubPanelApi.date_format).date()
            return (end_date - today).days if today <= end_date else 0
        except ValueError:
            return 0

    def account_create_record(self, get):
        try:
            get.validate([
                Param("body").String().Require(),
            ], [
                public.validate.trim_filter(),
            ])
            body = json.loads(get.body)
        except json.JSONDecodeError:
            body = get.body
        except Exception as ex:
            return public.fail_v2(str(ex))

        domain = body.pop("domain", None)
        if not domain:
            return public.fail_v2("Domain not found!")

        root, zone, _ = extract_zone(domain)
        if not root:
            return public.fail_v2("Domain not valid!")

        # body = {
        #     "domain": "example.com",
        #     "record": "record",
        #     "record_value": "record_value",
        #     "record_type": "A",
        #     "ttl" : 1, # AUTO
        #     "proxied": 0不代理 , 1 代理,
        #     "priority": 10, 邮件参数, 按需要传入
        # }
        sys_name = "Sub aaPanel"
        body["domain_name"] = root
        p = DnsDomainProvider.objects.filter(domains__contains=root).first()
        if p:
            dns_obj = p.dns_obj
            if body.get("record_type") == "TXT" and "v=spf" in body.get("record_value"):
                # 处理spf记录
                db_record = body.get("domain") if body.get("record") == "@" else body.get("record")
                for item in DnsDomainRecord.objects.filter(
                    domain=body.get("domain"),
                    record__startswith=db_record,
                    record_type="TXT",
                    record_value__like="v=spf",
                ):
                    try:
                        item.delete_record(sys_name)
                    except:
                        continue

            try:
                res = dns_obj.create_org_record(**body)
            except Exception as e:
                return public.fail_v2(f"Failed! {str(e)}")
            msg_body = (f'{sys_name} account Create Dns Record ['
                       f'domain={domain}, '
                       f'record={body.get("record")}, '
                       f'type={body.get("record_type")}, '
                       f'value={body.get("record_value")}'
                       f'] ')
            if res.get("status"):
                msg_body += "Successfully!"
                public.WriteLog("DnsSSLManager", msg_body)
                return public.success_v2("Successfully!")
            else:
                msg_body += f"Failed!, error: {res.get('msg')}"
                public.WriteLog("DnsSSLManager", msg_body)
                return public.fail_v2(res.get("msg", "Failed!"))
        else:
            return public.fail_v2("Provider account not found!")

    def account_list_ssl_info(self, get):
        """
        证书列表
        """
        try:
            get.validate([
                Param("p").Integer(),
                Param("limit").String(),
                Param("domain").String(),
            ], [
                public.validate.trim_filter(),
            ])
        except Exception as ex:
            public.print_log("error info: {}".format(ex))
            return public.return_message(-1, 0, str(ex))
        page = int(getattr(get, "p", 1))
        limit = int(getattr(get, "limit", 100))
        ssl_obj = DnsDomainSSL.objects.all()
        if hasattr(get, "domain") and get.domain:
            ssl_obj = ssl_obj.filter(subject__like=get.domain)

        total = ssl_obj.count()
        ssl_obj.limit(limit).offset((page - 1) * limit)
        res = []
        for ssl in ssl_obj:
            if ssl.provider_id:
                provider = DnsDomainProvider.objects.filter(id=ssl.provider_id).fields(
                    "name", "api_user", "api_key", "permission", "domains"
                ).first()
                if provider:
                    provider = provider.as_dict()
            else:
                provider = {}

            data = {
                "provider": provider,
                "ssl_info": ssl.info,
                "end_time": self._end_time(ssl.not_after),
                "end_date": ssl.not_after,
                "last_apply_time": ssl.create_time,
                "cert": {
                    "csr": public.readFile(ssl.path + "/fullchain.pem"),  # 证书
                    "key": public.readFile(ssl.path + "/privkey.pem"),  # 密钥
                },
            }
            res.append(data)
        return public.success_v2({"data": res, "total": total})

    def account_domain_provider(self, get):
        try:
            get.validate([
                Param("domain").String().Require(),
            ], [
                public.validate.trim_filter(),
            ])
        except Exception as ex:
            public.print_log("error info: {}".format(ex))
            return public.return_message(-1, 0, str(ex))

        res = {}
        for p in DnsDomainProvider.objects.all():
            if get.domain in p.domains:
                res = p.as_dict()
                break
        return public.success_v2(res)
