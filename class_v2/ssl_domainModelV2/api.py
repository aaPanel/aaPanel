# coding: utf-8
# ------------------------------
# 域名管理
# ------------------------------
import ipaddress
import json
import os.path
import shutil
import threading
import time
import sys
from datetime import datetime
from typing import Tuple, Dict

if not "class/" in sys.path:
    sys.path.insert(0, "class/")
if not "class_v2/" in sys.path:
    sys.path.insert(0, "class_v2/")

import public

try:
    import dns.resolver
except ImportError:
    try:
        public.ExecShell("btpip install dnspython")
        import dns.resolver
    except ImportError:
        public.print_log("install dnspython fail.")

from acme_v2 import acme_v2
from config_v2 import config
from panelDnsapi import extract_zone
from panel_site_v2 import panelSite
from public.aaModel import Q
from public.exceptions import HintException
from public.validate import Param
from .config import (
    DNS_MAP,
    WorkFor,
    UserFor,
    PANEL_DOMAIN,
    PANEL_LIMIT_DOMAIN,
    MANUAL_APPLY_PL,
)
from .model import (
    DnsDomainProvider,
    DnsDomainRecord,
    DnsDomainSSL,
    DnsDomainTask,
    apply_cert,
)
from ssl_dnsV2.model import DnsResolve
from .service import (
    init_panel_http,
    init_panel_dns,
    generate_panel_task,
    SyncService,
    DomainValid,
    make_suer_alarm_task,
    generate_sites_task,
    find_site_with_domain,
    CertHandler,
    RecordCache,
    check_legal,
    init_aaDns,
    make_suer_renew_task,
    get_mail_record,
)


def fix_log(ssl: DnsDomainSSL, log: str) -> None:
    if not ssl or not log:
        return
    if not ssl.log or ssl.log != log:
        ssl.log = log
        ssl.save()


# noinspection PyUnusedLocal
class DomainObject:
    date_format = "%Y-%m-%d"
    vhost = os.path.join(public.get_panel_path(), "vhost")
    mail_db_file = "/www/vmail/postfixadmin.db"
    manual_apply = MANUAL_APPLY_PL
    deploy_map = {
        1: UserFor.sites,
        2: UserFor.panel,
        3: UserFor.mails,
        4: UserFor.account,
    }

    def __init__(self):
        self.supports = list(DNS_MAP.keys())
        if not os.path.exists(self.manual_apply):
            public.writeFile(self.manual_apply, json.dumps({}))

    @staticmethod
    def _clear_task_force():
        # clear task, 3 hours
        try:
            one_hours = 1000 * 60 * 60 * 3
            out_time = round(time.time() * 1000) - one_hours
            DnsDomainTask.objects.filter(create_time__lte=out_time).delete()
        except Exception:
            pass

    @staticmethod
    def _end_time(data_str: str) -> int:
        try:
            if not data_str:
                return 0
            today = datetime.today().date()
            end_date = datetime.strptime(data_str, DomainObject.date_format).date()
            return max((end_date - today).days - 1 if today <= end_date else 0, 0)
        except ValueError:
            return 0

    @staticmethod
    def _process_key(data: dict, key: list = None) -> dict:
        if not key:
            return data
        if "api_user" in key:  # 隐藏api_user
            k = "api_user"
            if len(data.get(k, "")) > 0:
                data[k] = data[k][:len(data[k]) // 2] + "***"
        if "record" in key:  # 隐藏cf自带域名
            k = "record"
            endswith_str = f'.{data.get("domain", "")}'
            if data.get(k, "").endswith(endswith_str):
                data[k] = data[k].replace(endswith_str, "")
        return data

    @staticmethod
    def _add_ssl_info(data: dict) -> dict:
        new_domains = []
        domains = data.get("domains", [])
        for domain in domains:
            ssl_obj = DnsDomainSSL.objects.filter(
                provider_id=data.get("id", 0), dns__contains=domain,
            ).order_by("-create_time").first()
            if not ssl_obj:
                ssl_info = {
                    "id": 0,
                    "end_time": -1,
                    "end_date": "-",
                    "alarm": 0,
                    "auto_renew": 0,
                }
            else:
                ssl_info = {
                    "id": ssl_obj.id,
                    "end_time": DomainObject._end_time(ssl_obj.not_after),
                    "end_date": ssl_obj.not_after,
                    "alarm": ssl_obj.alarm,
                    "auto_renew": ssl_obj.auto_renew,
                }
            new_domains.append(
                {"name": domain, "ssl_info": ssl_info}
            )
        data["domains"] = new_domains
        return data

    @staticmethod
    def _add_task_info(data: dict, task_name: str = None) -> dict:
        # 初始化, 申请任意域名, 续签, 同步
        tasks_obj = DnsDomainTask.objects.filter(
            provider_id=data.get("id", -1), task_status__lt=100
        )
        if task_name:
            tasks_obj.filter(task_name=task_name)

        data["task"] = tasks_obj.order_by("-create_time").as_list()
        return data

    def get_dns_support(self, get):
        return public.success_v2(self.supports)

    # =========== 托管商 ===========
    def sync_dns_info(self, get):
        """
        对账号立即同步域名信息
        """
        target_id = get.id if hasattr(get, "id") else None
        instance = SyncService(target_id)
        task = threading.Thread(target=instance.process)
        task.start()
        return public.success_v2(public.lang("success"))

    def list_dns_api(self, get):
        """
        dns api 列表
        """
        public.set_module_logs("sys_domain", "Domain_SSL_Open", 1)
        try:
            get.validate([
                Param("p").Integer(),
                Param("limit").Integer(),
                Param("pid").Integer(),
            ], [
                public.validate.trim_filter(),
            ])
        except Exception as ex:
            public.print_log("error info: {}".format(ex))
            return public.return_message(-1, 0, str(ex))

        # clear task
        self._clear_task_force()
        check_legal()
        init_aaDns()
        page = int(getattr(get, "p", 1))
        limit = int(getattr(get, "limit", 100))
        obj = DnsDomainProvider.objects.all()
        if hasattr(get, "pid"):
            obj = DnsDomainProvider.objects.filter(id=get.pid)
        total = obj.count()
        result = obj.limit(limit).offset((page - 1) * limit).as_list()
        for r in result:
            r = self._process_key(r, key=["api_user"])
            r = self._add_ssl_info(r)
            r = self._add_task_info(r)
        return public.success_v2({"data": result, "total": total})

    def create_dns_api(self, get):
        try:
            get.validate([
                Param("name").String().Require(),
                Param("api_user").String().Require(),
                Param("api_key").String().Require(),
                Param("permission").String(),
                Param("alias").String().Require(),
                Param("status").Integer(),
            ], [
                public.validate.trim_filter(),
            ])
        except Exception as ex:
            public.print_log("error info: {}".format(ex))
            return public.return_message(-1, 0, str(ex))
        if "*" in get.api_user:
            return public.fail_v2(public.lang("'*' Symbols that are not allowed"))
        if hasattr(get, "status"):
            get.status = int(get.status)
        if get.name not in self.supports:
            return public.fail_v2(public.lang(f"Provider not support! Support DNS provider :{self.supports}"))
        if get.name == "CloudFlareDns":
            if not hasattr(get, "permission") or get.permission not in ["limit", "global"]:
                return public.fail_v2(public.lang("CloudFlareDns Permission must be 'limit' or 'global'!"))
        else:
            get.permission = "-"

        if DnsDomainProvider.objects.filter(alias=get.alias).first():
            return public.fail_v2(public.lang("Alias already exists!"))

        if DnsDomainProvider.objects.filter(
                api_user=get.api_user, api_key=get.api_key, name=get.name,
        ).first():
            return public.fail_v2(public.lang(f"Account already exists!"))

        try:
            dns = DnsDomainProvider(**get.get_items())
            if not dns.is_pro():
                return public.fail_v2(public.lang("Please Upgrade PRO Version!"))
            dns.dns_obj.verify()
            dns.save()
            dns.init_ssl_myself_thread()
            public.set_module_logs("sys_domain", "Add_Dns_Api", 1)
            return public.success_v2(public.lang("Save Successfully!"))
        except Exception as ex:
            raise ex

    def delete_dns_api(self, get):
        try:
            get.validate([
                Param("id").Integer().Require(),
            ], [
                public.validate.trim_filter(),
            ])
        except Exception as ex:
            public.print_log("error info: {}".format(ex))
            return public.return_message(-1, 0, str(ex))
        DnsDomainRecord.objects.filter(provider_id=int(get.id)).delete()
        provider = DnsDomainProvider.objects.filter(id=int(get.id)).first()
        msg = f"DNS: {provider.name} Alias: {provider.alias} , Delete Successfully!"
        provider.delete()
        public.WriteLog("DnsSSLManager", msg)
        return public.success_v2(public.lang("Delete Successfully!"))

    def edit_dns_api(self, get):
        if not hasattr(get, "id"):
            return public.fail_v2(public.lang("id is required"))
        if hasattr(get, "status"):
            get.status = int(get.status)
        if hasattr(get, "name") and get.name == "CloudFlareDns":
            if not hasattr(get, "permission") or get.permission not in ["limit", "global"]:
                return public.fail_v2(public.lang("CloudFlareDns Permission must be 'limit' or 'global'"))
        if hasattr(get, "user") and "*" in get.api_user:
            return public.fail_v2(public.lang("'*' symbols that are not allowed"))

        # alias 不允许重复
        if hasattr(get, "alias") and DnsDomainProvider.objects.filter(alias=get.alias).first():
            return public.fail_v2(public.lang("Alias already exists!"))
        try:
            dns = DnsDomainProvider.objects.filter(id=get.id).first()
            for k, v in get.get_items().items():
                if hasattr(dns, k) and k != "id":
                    setattr(dns, k, v)
            # 仅当开启时候校验
            if dns.status == 1:
                dns.dns_obj.verify()
            if dns.name != "aaPanelDns":
                DnsDomainProvider.objects.filter(id=get.id).update(dns.as_dict())
            else:  # 兼容 aaDNS 服务状态变更
                from ssl_dnsV2.dns_manager import DnsManager
                status_map = {1: "restart", 0: "stop"}
                DnsManager().change_service_status(status=status_map.get(get.status))
        except Exception as ex:
            return public.fail_v2(str(ex))
        return public.success_v2(public.lang("Save Successfully!"))

    # =========== dns 记录 ===========
    def list_dns_record(self, get):
        try:
            get.validate([
                Param("p").Integer(),
                Param("limit").Integer(),
                Param("search_pid").Integer().Require(),
                Param("domain").String(),
                Param("search").String(),
                Param("search_and").String(),
            ], [
                public.validate.trim_filter(),
            ])
        except Exception as ex:
            public.print_log("error info: {}".format(ex))
            return public.return_message(-1, 0, str(ex))
        page = int(getattr(get, "p", 1))
        limit = int(getattr(get, "limit", 100))
        pid = int(get.search_pid)
        provider = DnsDomainProvider.objects.find_one(id=pid)
        if not provider:
            return public.fail_v2(public.lang("Provider not found!"))
        if hasattr(get, "domain") and get.domain:
            domain_name = get.domain
        else:
            domain_name = provider.domains[0] if provider.domains else ""
        RecordCache.record_ensure(domain_name)

        # search_and
        if hasattr(get, "search_and"):
            try:
                search_and = json.loads(get.search_and)
            except:
                search_and = {}

            obj = DnsDomainRecord.objects.filter(
                provider_id=pid, domain=domain_name, **search_and
            )
        # no search, no search_and
        elif not hasattr(get, "search"):
            obj = DnsDomainRecord.objects.filter(provider_id=pid, domain=domain_name)

        # only search
        else:
            if hasattr(get, "search_and") and hasattr(get, "search"):
                return public.fail_v2(
                    public.lang("search_and and search can not be used at the same time")
                )

            obj = DnsDomainRecord.objects.filter(
                Q(provider_id=pid, domain=domain_name) & (
                        Q(record__like=get.search) | Q(record_value__like=get.search)
                )
            )

        try:
            total = obj.count()
            result = obj.limit(limit).offset((page - 1) * limit).as_list()
        except Exception as e:
            raise HintException(e)

        data = [
            self._process_key(x, key=["api_user", "record"]) for x in result
        ]
        data.sort(key=lambda x: (x["record_type"], x["record"]))
        return public.success_v2({"data": data, "total": total})

    def create_dns_record(self, get):
        try:
            get.validate([
                Param("pid").Integer().Require(),
                Param("domain").String().Require(),
                Param("record").String().Require(),
                Param("record_type").String().Require(),
                Param("record_value").String().Require(),
                Param("priority").Integer().Require(),
                Param("ttl").Integer().Require(),
                Param("proxy").Integer(),
                Param("ps").String(),
            ], [
                public.validate.trim_filter(),
            ])
        except Exception as ex:
            public.print_log("error info: {}".format(ex))
            return public.return_message(-1, 0, str(ex))

        provider = DnsDomainProvider.objects.filter(id=int(get.pid)).first()
        body = {
            "provider_id": provider.id,
            "provider_name": provider.name,
            "api_user": provider.api_user,
            "domain": get.domain,
            "record": get.record,
            "record_type": get.record_type,
            "record_value": get.record_value,
            "ttl": int(get.ttl),
            "proxy": int(get.proxy),
            "priority": int(get.priority),
        }
        if hasattr(get, "ps"):
            body["ps"] = get.ps
        response = provider.model_create_dns_record(body)
        if not response.get("status"):
            return public.fail_v2(response.get("msg"))
        return public.success_v2(public.lang("Save Successfully!"))

    def delete_dns_record(self, get):
        try:
            get.validate([
                Param("id").Integer().Require(),
            ], [
                public.validate.trim_filter(),
            ])
        except Exception as ex:
            public.print_log("error info: {}".format(ex))
            return public.return_message(-1, 0, str(ex))
        record = DnsDomainRecord.objects.find_one(id=int(get.id))
        if not record:
            return public.fail_v2(public.lang("DNS record Not Found!"))
        provider = DnsDomainProvider.objects.find_one(id=record.provider_id)
        if not provider:
            return public.fail_v2(public.lang("DNS Provider Not Found!"))
        response = provider.model_delete_dns_record(int(get.id))
        if not response.get("status"):
            return public.fail_v2(response.get("msg"))
        return public.success_v2(public.lang("Delete Successfully!"))

    def edit_dns_record(self, get):
        try:
            get.validate([
                Param("id").Integer().Require(),
                Param("pid").Integer().Require(),
                Param("domain").String().Require(),
                Param("record").String().Require(),
                Param("record_type").String().Require(),
                Param("record_value").String().Require(),
                Param("ttl").Integer().Require(),
                Param("proxy").Integer().Require(),
                # -1 is not MX record
                Param("priority").Integer("between", [-1, 65535]).Require(),
                Param("ps").String(),
            ], [
                public.validate.trim_filter(),
            ])
        except Exception as ex:
            public.print_log("error info: {}".format(ex))
            return public.return_message(-1, 0, str(ex))
        pid = int(get.pid)
        record_id = int(get.id)
        ps = get.ps if hasattr(get, "ps") else ""
        # check if change
        real_change = False
        provider = DnsDomainProvider.objects.find_one(id=pid)
        if not provider:
            return public.fail_v2(public.lang("DNS Provider Not Found!"))
        target = DnsDomainRecord.objects.find_one(id=record_id)
        if not target:
            return public.fail_v2(public.lang("DNS Record Not Found!"))
        new_body = {
            "provider_id": provider.id,
            "provider_name": provider.name,
            "api_user": provider.api_user,
            "domain": get.domain,
            "record": get.record,
            "record_type": get.record_type,
            "record_value": get.record_value,
            "ttl": int(get.ttl),
            "proxy": int(get.proxy),
            "priority": int(get.priority),
            "ps": ps,
        }
        if any([
            target.record != get.record,
            target.record_type != get.record_type,
            target.record_value != get.record_value,
            target.ttl != int(get.ttl),
            target.proxy != int(get.proxy),
            target.priority != int(get.priority),
        ]):
            real_change = True
        if not real_change:
            DnsDomainRecord.objects.filter(id=record_id).update(new_body)
            return public.success_v2(public.lang("Update Successfully!"))
        # real change
        try:
            update = provider.model_edit_dns_record(record_id, new_body)
            if update.get("status"):
                return public.success_v2(public.lang("Update Successfully!"))
            else:
                return public.fail_v2(update.get("msg", "Update Failed..."))
        except Exception as ex:
            return public.fail_v2(str(ex))

    # ========== 域名管理概况 SSL =======
    def list_domain_details(self, get):
        try:
            get.validate([
                Param("p").Integer(),
                Param("limit").Integer(),
                Param("id").Integer().Require(),
                Param("domain").String(),
            ], [
                public.validate.trim_filter(),
            ])
        except Exception as ex:
            public.print_log("error info: {}".format(ex))
            return public.return_message(-1, 0, str(ex))

        page = int(getattr(get, "p", 1))
        limit = int(getattr(get, "limit", 100))
        provider = DnsDomainProvider.objects.find_one(id=get.id)
        if not provider:
            return public.fail_v2(public.lang("DNS Provider Not Found!"))

        data = self._add_ssl_info(provider.as_dict())
        data = data.get("domains", [])
        if hasattr(get, "domain"):  # filter domain
            data = [x for x in data if get.domain in x.get("name", "")]

        bulitin = True if provider.name == "aaPanelDns" else False
        for d in data:
            d["records"] = DnsDomainRecord.objects.filter(
                domain=d.get("name", ""), provider_id=int(get.id)
            ).count()
            if bulitin:
                resolve = DnsResolve.objects.filter(domain=d.get("name", "")).fields(
                    "ns_resolve", "a_resolve", "tips"
                ).first()
                if not resolve:
                    d["dns_resolve"] = {"ns_resolve": 0, "a_resolve": 0, "tips": "Not Found Msg"}
                else:
                    d["dns_resolve"] = resolve.as_dict()

        total = len(data)
        start = (page - 1) * limit
        end = start + limit
        return public.success_v2({"data": data[start:end], "total": total})

    # ===========   SSL    ============
    def list_ssl_info(self, get):
        """
        证书列表
        """
        try:
            get.validate([
                Param("p").Integer(),
                Param("limit").String(),
                Param("is_order").Integer(),
                Param("search").String(),
            ], [
                public.validate.trim_filter(),
            ])
            get.is_order = 0 if not hasattr(get, "is_order") else int(get.is_order)
            if not hasattr(get, "search"):
                get.search = ""
        except Exception as ex:
            public.print_log("error info: {}".format(ex))
            return public.return_message(-1, 0, str(ex))
        page = int(getattr(get, "p", 1))
        limit = int(getattr(get, "limit", 100))
        ssl_obj = DnsDomainSSL.objects.filter(
            Q(is_order=int(get.is_order)) & (Q(dns__like=get.search) | Q(subject__like=get.search))
        ).order_by("-create_time")
        total = ssl_obj.count()
        ssl_obj.limit(limit).offset((page - 1) * limit)
        data = [
            self._add_task_info(
                data={
                    "hash": ssl.hash,
                    "provider": ssl.info.get("issuer_O", "unknown"),
                    "issuer": ssl.info.get("issuer", "unknown"),
                    "verify_domains": ssl.dns,
                    "end_time": self._end_time(ssl.not_after),
                    "end_date": ssl.not_after,
                    "auto_renew": ssl.auto_renew,
                    "last_apply_time": ssl.info.get("notBefore", ""),
                    "cert": {
                        "csr": public.readFile(ssl.path + "/fullchain.pem"),  # 证书
                        "key": public.readFile(ssl.path + "/privkey.pem"),  # 密钥
                    },
                    "log": ssl.log if ssl.log else ssl.get_ssl_log(),
                    "user_for": ssl.user_for,
                    "alarm": ssl.alarm,
                },
                # task_name=DnsTask.apply_ssl.value,
            ) for ssl in ssl_obj
        ]
        return public.success_v2({"data": data, "total": total})

    def download_cert(self, get):
        """
        下载
        """
        try:
            get.validate([
                Param("hash").String().Require(),
            ], [
                public.validate.trim_filter(),
            ])
        except Exception as ex:
            public.print_log("error info: {}".format(ex))
            return public.return_message(-1, 0, str(ex))
        file_path = "/www/server/panel/vhost" + f"/ssl_saved/{get.hash}"
        if not os.path.exists(file_path):
            return public.fail_v2(public.lang("SSL Certificate  Not Found!"))

        CertHandler.make_last_info(file_path, force=True)

        download_path = os.path.join(self.vhost, "ssl_saved/download")
        os.makedirs(download_path, exist_ok=True)
        output_path = os.path.join(download_path, f"{get.hash}")
        if os.path.exists(f"{output_path}.zip"):
            public.ExecShell(f"rm -f {output_path}.zip")
        try:
            shutil.make_archive(output_path, "zip", file_path)
        except Exception as e:
            return public.fail_v2(f"error: {str(e)}")
        return public.success_v2(f"{output_path}.zip")

    def one_cilck_renew(self, get):
        """
        一键全量续签
        """
        make_suer_renew_task()  # 确保任务存在
        echo = public.md5(public.md5("domain_ssl_renew_lets_ssl_bt"))
        task = public.S("crontab").where("echo=?", echo).find()
        if not task:
            raise HintException("Cron Domian Renew task not found, please try again later!")
        execstr = f"{public.GetConfigValue("setup_path")}/cron/{echo}"
        public.ExecShell(f"chmod +x {execstr}")
        public.ExecShell(f"nohup {execstr} start >> {execstr}.log 2>&1 &")
        return public.success_v2({"id": task["id"]})

    def renew_cert_process(self, get):
        """
        续签, 带进度, 带部署
        """
        try:
            get.validate([
                Param("hash").String().Require(),
            ], [
                public.validate.trim_filter()
            ])
        except Exception as ex:
            public.print_log("error info: {}".format(ex))
            return public.return_message(-1, 0, str(ex))

        ts_month = 31 * 24 * 60 * 60 * 1000
        months = int(time.time() * 1000) + ts_month
        invalid_msg = public.lang(
            "This Certificate auth info is invalid, cannot renew! Please Apply for a New Certificate."
            "It will be renewed for you automatically in the future"
        )
        ssl_obj = DnsDomainSSL.objects.filter(hash=get.hash).first()
        if not ssl_obj or not ssl_obj.auth_info:
            raise HintException(invalid_msg)

        debug = public.readFile("/www/server/panel/data/debug.pl") or "False"
        if debug.lower() == "false" and ssl_obj.not_after_ts > months:
            raise HintException(public.lang("SSL Certificate is less than 30 days, no need to renew!"))

        auth_type = ssl_obj.auth_info.get("auth_type")
        auth_to = ssl_obj.auth_info.get("auth_to", "").rstrip("/").replace("//", "/")
        args = public.dict_obj()
        args.domains = json.dumps(ssl_obj.dns)

        if auth_type == "http" or (auth_type == "dns" and auth_to == "dns"):
            # 明确的http方式, 或 手动认证申请的dns, 尝试http
            args.auth_type = "http"
            args.deploy = 1
            args.site_id = public.M("sites").where("path=?", (auth_to,)).getField("id") or "-1"
            return self.apply_new_ssl(args)

        elif auth_type == "dns":
            args.auth_type = "dns"
            return self.apply_new_ssl(args)

        else:
            raise HintException(invalid_msg)

    def manual_apply_vaild(self, get):
        """
        手动申请验证
        """
        try:
            get.validate([
                Param("site_id").Integer().Require(),
                Param("domains").String().Require(),
            ], [
                public.validate.trim_filter(),
            ])
            get.site_id = str(get.site_id)
            domains = [x.strip() for x in list(set(get.domains.split(",")))]
            domains.sort()
        except Exception as ex:
            public.print_log("error info: {}".format(ex))
            return public.return_message(-1, 0, str(ex))
        manual_apply: Dict[str, str] = json.loads(
            public.readFile(self.manual_apply)
        )
        domians_index = CertHandler.original_md5(domains)
        if domians_index not in manual_apply.keys():
            return public.fail_v2(public.lang("Order Not Found!"))
        new_get = public.dict_obj()
        new_get.index = manual_apply[domians_index]
        vaild = acme_v2().validate_domain(new_get)

        if vaild.get("save_path"):
            ssl_hash = CertHandler.get_hash(vaild.get("cert", "") + vaild.get("root", ""))
            ssl_obj = DnsDomainSSL.objects.filter(hash=ssl_hash).first()
            site_name = public.M("sites").where("id=?", get.site_id).getField("name")
            if site_name and ssl_obj:
                ssl_obj.deploy_sites([site_name])
            if domians_index in manual_apply.keys():
                del manual_apply[domians_index]
                public.writeFile(self.manual_apply, json.dumps(manual_apply))
            return public.success_v2(public.lang("Apply Successfully!"))

        if vaild.get("status") is True:
            if domians_index in manual_apply.keys():
                del manual_apply[domians_index]
                public.writeFile(self.manual_apply, json.dumps(manual_apply))
            return public.success_v2(public.lang("Apply Successfully!"))
        try:
            return public.fail_v2((str(vaild.get("msg", "Vaild failed! please try again"))))
        except:
            return public.fail_v2("Vaild failed! please try again")

    def manual_apply_check(self, get):
        """
        手动申请验证兜底
        """
        try:
            get.validate([
                Param("site_id").Integer().Require(),
                Param("domains").Array().Filter(json.loads)
            ], [
                public.validate.trim_filter(),
            ])
            domains = [x.strip() for x in list(set(get.domains))]
            domains.sort()
            target = CertHandler.original_md5(domains)
        except Exception as ex:
            public.print_log("error info: {}".format(ex))
            return public.return_message(-1, 0, str(ex))
        manual_apply: Dict[str, str] = json.loads(
            public.readFile(self.manual_apply)
        )
        target_detail = {}
        for k in list(manual_apply.keys()):
            new_get = public.dict_obj()
            new_get.index = manual_apply[k]
            detail = acme_v2().get_order_detail(new_get)  # loop for clean expires
            if target == k:
                target_detail = detail.get("message")
        return public.success_v2(target_detail)

    def apply_new_ssl(self, get):
        """
        申请证书
        get.domains = '["www.a.com","a.com"]'
        get.auth_type = dns/http/dns_manual
        get.auto_wildcard = 0/1  # 自动组合泛域名
        get.deploy = -1/0/ 是否需要重新部署ssl
        get.site_id = 站点id, 匹配具体的站点

        :return:
        1. dns 自动验证 2. http 文件验证
        {
            "result": success_msg,
            "task_id": task.id,
            "path": http_task.task_log,
        }
        3. dns_manual 手动验证
        返回订单详情 dict , 或者免认证期间 直接下发ssl成功消息 str
        """
        try:
            get.validate([
                Param("domains").String().Require(),
                Param("auth_type").String().Require(),
                Param("auto_wildcard").Integer(),
                Param("deploy").Integer(),
                Param("site_id").Integer(),
            ], [
                public.validate.trim_filter(),
            ])
            get.domains = json.loads(get.domains)
            if get.auth_type not in ["dns", "http", "dns_manual"]:
                return public.fail_v2(public.lang("auth_type must be 'dns', 'http' or 'dns_manual'"))
            if len(get.domains) == 0:
                return public.fail_v2(public.lang("domains is empty"))
            get.deploy = getattr(get, "deploy", -1)
            get.site_id = str(getattr(get, "site_id", "-1"))
            auto_wildcard = False if int(getattr(get, "auto_wildcard", 0)) == 0 else True
        except Exception as ex:
            public.print_log("error info: {}".format(ex))
            return public.return_message(-1, 0, str(ex))

        success_msg = "Apply Successfully! please wait for a moment"
        deploy_flag = self.deploy_map.get(int(get.deploy))
        apply_domains = [x.strip() for x in list(set(get.domains))]
        apply_domains.sort()

        for d in apply_domains:
            if not DomainValid.is_valid_domain(d.replace("*.", "")):
                return public.fail_v2(public.lang(f"Invalid domain name: {d}"))

        if get.auth_type == "dns":  # auto dns verify
            provider = None
            for d in apply_domains:
                temp_root, _, _ = extract_zone(d)
                provider = DnsDomainProvider.objects.filter(
                    domains__contains=temp_root
                ).first()
                if not provider:
                    return public.fail_v2(public.lang(
                        f"Dns01 Verify Errot, DNS Provider Not Found! for {temp_root}"
                    ))
            dns_task = generate_sites_task({}, -1)
            threading.Thread(target=provider.model_apply_cert,
                             kwargs=({
                                 "domains": apply_domains,
                                 "auto_wildcard": auto_wildcard,
                                 "deploy": deploy_flag,
                                 "task_obj": dns_task,
                             })).start()
            return public.success_v2({
                "result": public.lang(success_msg),
                "task_id": dns_task.id,
                "path": dns_task.task_log,
            })

        elif get.auth_type == "http":  # file verify
            site = find_site_with_domain(get.domains[0])
            if not site:
                return public.fail_v2(public.lang("Http01 Verify Error, but Site Not Found."))
            if site.get("status") != "1":
                return public.fail_v2(public.lang("Http01 Verify Error, but Site is Not Running"))
            if any("*." in i for i in get.domains):
                return public.fail_v2(public.lang(
                    "Http01 Verify Error: The wildcard domain name can only be verified by DNS."
                ))
            http_task = generate_sites_task({}, -1)
            threading.Thread(target=apply_cert,
                             kwargs=({
                                 "domains": apply_domains,
                                 "auth_to": site.get("path"),
                                 "auth_type": "http",
                                 "task_obj": http_task,
                                 "deploy": deploy_flag,
                             })).start()
            return public.success_v2({
                "result": public.lang(success_msg),
                "task_id": http_task.id,
                "path": http_task.task_log,
            })

        elif get.auth_type == "dns_manual":  # manual dns verify
            manual_apply: Dict[str, str] = json.loads(
                public.readFile(self.manual_apply)
            )
            domian_index = CertHandler.original_md5(apply_domains)
            if domian_index in manual_apply.keys():
                new_get = public.dict_obj()
                new_get.index = manual_apply[domian_index]
                return acme_v2().get_order_detail(new_get)

            apply_res = acme_v2().apply_cert_domain(
                domains=apply_domains,
                auth_to="dns",
                auth_type="dns",
                auto_wildcard=auto_wildcard,
            )
            if apply_res.get("save_path"):  # 免认证期间将跳过验证, 直接下发ssl, 进行部署覆盖
                ssl_hash = CertHandler.get_hash(apply_res.get("cert", "") + apply_res.get("root", ""))
                ssl_obj = DnsDomainSSL.objects.filter(hash=ssl_hash).first()
                site_name = public.M("sites").where("id=?", get.site_id).getField("name")
                deploy = {}
                if site_name and ssl_obj:
                    deploy = ssl_obj.deploy_sites([site_name])
                if domian_index in manual_apply.keys():
                    del manual_apply[domian_index]
                    public.writeFile(self.manual_apply, json.dumps(manual_apply))
                success_msg = {"result": apply_res.get("msg", "Apply Successfully!")}
                if deploy.get("status"):
                    success_msg.update({"deploy": deploy.get("status")})
                return public.success_v2(public.lang(success_msg))

            if apply_res.get("index"):  # 新申请, 返回订单详情
                manual_apply.update({domian_index: apply_res.get("index")})
                public.writeFile(self.manual_apply, json.dumps(manual_apply))
                new_get = public.dict_obj()
                new_get.index = apply_res.get("index")
                return acme_v2().get_order_detail(new_get)

            if apply_res.get("status") is False:
                return public.fail_v2(apply_res.get("msg", "Apply Failed!"))
            return public.success_v2(public.lang("Apply Successfully!"))

        return public.fail_v2(public.lang("Unknown Auth Type"))

    def upload_cert(self, get):
        """
        上传证书
        """
        try:
            get.validate([
                Param("key").String().Require(),
                Param("cert").String().Require(),
            ], [
                public.validate.trim_filter(),
            ])
        except Exception as ex:
            public.print_log("error info: {}".format(ex))
            return public.return_message(-1, 0, str(ex))
        try:
            from ssl_domainModelV2.service import CertHandler
            data = CertHandler().save_by_data(get.cert, get.key)
            if not data:
                return public.fail_v2(public.lang("update cert failed"))
            return public.success_v2(data)
        except Exception as ex:
            return public.fail_v2(str(ex))

    def remove_cert(self, get):
        """
        删除证书
        """
        try:
            get.validate([
                Param("hash").String().Require(),
            ], [
                public.validate.trim_filter(),
            ])
        except Exception as ex:
            public.print_log("error info: {}".format(ex))
            return public.return_message(-1, 0, str(ex))
        ssl_obj = DnsDomainSSL.objects.find_one(hash=get.hash)
        if not ssl_obj:
            return public.fail_v2(public.lang("SSL Certificate Not Found!"))
        # vhost/ssl为site ssl证书存放目录
        cert_name = ssl_obj.subject.replace("*.", "")
        vpath = os.path.join(self.vhost, "ssl", cert_name)
        if os.path.exists(vpath):
            public.ExecShell("rm -rf " + vpath)

        try:
            ssl_obj.delete()
        except Exception as ex:
            public.print_log("error info: {}".format(ex))
            return public.fail_v2(str(ex))

        return public.success_v2(public.lang("Remove Successfully!"))

    def switch_auto_renew(self, get):
        """
        自动续签开关
        """
        try:
            get.validate([
                Param("hash").String().Require(),
            ], [
                public.validate.trim_filter(),
            ])
        except Exception as ex:
            public.print_log("error info: {}".format(ex))
            return public.return_message(-1, 0, str(ex))

        ssl_obj = DnsDomainSSL.objects.find_one(hash=get.hash)
        if not ssl_obj:
            return public.fail_v2(public.lang("SSL Not Found!"))
        # make_suer_renew_task()  # make suer corn task
        open_map = {0: 1, 1: 0}
        ssl_obj.auto_renew = open_map.get(ssl_obj.auto_renew, 1)
        ssl_obj.save()
        return public.success_v2(public.lang("Setting Successfully!"))

    def switch_ssl_alarm(self, get):
        """
        证书告警开关
        """
        try:
            get.validate([
                Param("hash").String().Require(),
                Param("alarm").Integer().Require(),
            ], [
                public.validate.trim_filter(),
            ])
        except Exception as ex:
            public.print_log("error info: {}".format(ex))
            return public.return_message(-1, 0, str(ex))
        ssl_obj = DnsDomainSSL.objects.find_one(hash=get.hash)
        if not ssl_obj:
            return public.fail_v2(public.lang("SSL Not Found!"))

        alarm = int(get.alarm)
        if alarm == 1:  # open
            make_suer_alarm_task()  # make suer alarm task
            ssl_obj.alarm = alarm
            ssl_obj.save()
        else:  # close
            ssl_obj.alarm = alarm
            ssl_obj.save()
        return public.success_v2(public.lang("Setting Successfully!"))

    # =========== Deploy ================
    @staticmethod
    def __add_match_flag(targes: list, dns_obj: DnsDomainSSL, key_word: str = None, match_domain: str = None) -> list:
        if key_word and match_domain:  # 不能同时存在
            return targes

        for t in targes:
            temp_name = t.get(key_word, "") if key_word else match_domain
            if DomainValid.match_ssl_dns(temp_name, dns_obj):
                t["match"] = 1
        return targes

    def cert_domain_list(self, get):
        """
        证书管理列表
        """
        try:
            get.validate([
                Param("hash").String().Require(),
            ], [
                public.validate.trim_filter(),
            ])
        except Exception as ex:
            public.print_log("error info: {}".format(ex))
            return public.return_message(-1, 0, str(ex))

        ssl_obj = DnsDomainSSL.objects.find_one(hash=get.hash)
        if not ssl_obj:
            return public.fail_v2(public.lang("SSL Certificate Not Found!"))
        # ====================== sites ======================
        # 不考虑status
        sites = public.S("sites").field(
            "id", "name", "path", "status", "type_id", "project_type",
        ).select()
        sites = self.__add_match_flag(sites, ssl_obj, "name")

        # ====================== mails ======================
        mails = []
        if os.path.exists(self.mail_db_file):
            # 不考虑active
            mails = public.S("domain", self.mail_db_file).field(
                "domain", "a_record", "active"
            ).select()
            mails = self.__add_match_flag(mails, ssl_obj, "domain")

        # ====================== panel ======================
        panel = []
        panel_ssl = config().GetPanelSSL(get=None)
        if panel_ssl.get("status") == 0:
            panel = [panel_ssl.get("message")]

        current_domain = ""
        if os.path.exists(PANEL_LIMIT_DOMAIN):
            limit_domain = public.readFile(PANEL_LIMIT_DOMAIN)
            if limit_domain:  # 如果有限制域名
                current_domain = limit_domain
            else:
                if os.path.exists(PANEL_DOMAIN):  # 如果有配置过的域名
                    current_domain = public.readFile(PANEL_DOMAIN)

        if current_domain and panel:
            panel = self.__add_match_flag(panel, ssl_obj, None, current_domain)

        data = {
            "sites": sites,
            "mails": mails,
            "panel": panel,
            "accounts": [],
        }
        return public.success_v2(data)

    @staticmethod
    def __before_deploy(get: public.dict_obj) -> Tuple[DnsDomainSSL, public.dict_obj]:
        """
        证书部署前通用检查
        :return: ssl obj, get obj
        """
        try:
            get.validate([
                Param("hash").String().Require(),
                Param("domains").String(),
                Param("append").Integer(),
                Param("recover").Integer(),
            ], [
                public.validate.trim_filter(),
            ])
        except Exception as ex:
            raise ex

        if hasattr(get, "domains"):
            try:
                get.domains = json.loads(get.domains)
            except json.decoder.JSONDecodeError as js_err:
                raise HintException("json decode error: {}".format(str(js_err)))

        for k in ["recover", "append"]:
            if hasattr(get, k):
                try:
                    setattr(get, k, int(getattr(get, k)))
                except TypeError as tr:
                    raise tr

        ssl_obj = DnsDomainSSL.objects.find_one(hash=get.hash)
        if not ssl_obj:
            raise Exception("SSL Certificate Not Found!")

        return ssl_obj, get

    def cert_deploy_sites(self, get):
        """
        证书部署到 选定的 sites
        get.hash
        get.domain
        get.append=1 追加模式, 其余为替换模式
        """
        try:
            # 返回ssl对象, get对象
            ssl_obj, get = self.__before_deploy(get)
        except Exception as ex:
            public.print_log("error info: {}".format(ex))
            return public.fail_v2(str(ex))
        # 网站入口单独部署
        if hasattr(get, "append") and get.append == 1:
            result = ssl_obj.deploy_sites(site_names=get.domains)
        else:  # 域名管理批量处理
            # 不同的元素
            diff = list(set(ssl_obj.sites_uf).symmetric_difference(set(get.domains)))
            # 1, 需要移除的sites
            for remove in [x for x in diff if x in set(ssl_obj.sites_uf)]:
                new_get = public.dict_obj()
                new_get.siteName = remove
                new_get.updateOf = 1
                new_get.reload = 0
                try:
                    # close site's ssl conf
                    remove_res = panelSite().CloseSSLConf(new_get)
                except Exception as e:
                    public.print_log(f"remove site ssl error info: {str(e)}")
                    continue
            # 2, 移除diff之后, 部署
            result = ssl_obj.deploy_sites(site_names=get.domains, replace=True)
        return public.return_message(0 if result.get("status") else -1, 0, public.lang(result.get("msg")))

    def cert_deploy_mails(self, get):
        """
        证书部署到 选定的 mails
        只涉及替换全部
        """
        try:
            ssl_obj, get = self.__before_deploy(get)
        except Exception as ex:
            public.print_log("error info: {}".format(ex))
            return public.fail_v2(str(ex))

        # 不同的元素
        diff = list(set(ssl_obj.mails_uf).symmetric_difference(set(get.domains)))
        # 1, 需要移除的mails
        try:
            import sys
            if os.path.exists("/www/server/panel/plugin/mail_sys"):
                sys.path.insert(1, "/www/server/panel/plugin/mail_sys")
            from plugin.mail_sys.mail_sys_main import mail_sys_main

            for remove in [x for x in diff if x in set(ssl_obj.mails_uf)]:
                args = public.dict_obj()
                args.csr = ""
                args.key = ""
                args.domain = remove
                args.act = "delete"
                try:
                    mail_sys_main().set_mail_certificate_multiple(args)
                except:
                    continue
        except Exception as err:
            public.print_log("remove mail ssl error info: {}".format(str(err)))

        # 2, 移除diff之后, 部署
        result = ssl_obj.deploy_mails(get.domains)
        if result.get("status"):
            return public.success_v2(public.lang("Deploy Mail's SSL Successfully!"))

        return public.fail_v2(public.lang(result.get("msg", "Deploy Faild...")))

    def cert_deploy_accounts(self, get):
        """
        证书部署到 选定的 accounts
        """
        try:
            ssl_obj, get = self.__before_deploy(get)
        except Exception as ex:
            public.print_log("error info: {}".format(ex))
            return public.fail_v2(str(ex))

        return public.success_v2(public.lang("Deploy Account's SSL Successfully!"))

    def cert_deploy_panel(self, get):
        """
        指定部署到 panel 主面板, or 恢复自签证书
        """
        try:
            get.validate([
                Param("hash").String().Require(),
                Param("recover").Integer().Require(),
            ], [
                public.validate.trim_filter(),
            ])
        except Exception as ex:
            public.print_log("error info: {}".format(ex))
            return public.fail_v2(str(ex))

        ssl_obj, get = self.__before_deploy(get)
        res = ssl_obj.deploy_panel(recover=int(get.recover))
        if res.get("status"):
            return public.success_v2(public.lang("Deploy Panel's SSL Successfully!"))
        return public.fail_v2(public.lang(res.get("msg", "Deploy Panel's SSL Failed!")))

    # =========== Site ===========
    def get_sites(self, get):
        """
        获取所有网站
        """
        return public.success_v2([
            x for x in public.S("sites").field("id", "name", "project_type").select()
        ])

    def check_domain_automatic(self, get):
        """
        dns自动化的检测服务
        涵盖site, mail, panel, account等
        :return: {
            "hash": "", 适用证书
            "domain": "", 检查的域名
            "support": [
                         "auto", 自动解析
                         "ssl_cert",自动部署
                         "cf_proxy", cf代理
                       ],
        }
        """
        try:
            get.validate([
                Param("domain").String().Require(),
            ], [
                public.validate.trim_filter(),
            ])
        except Exception as ex:
            public.print_log("error info: {}".format(ex))
            return public.return_message(-1, 0, str(ex))
        result = {
            "hash": "",
            "domain": get.domain,
        }
        support = list()
        root, _, _ = extract_zone(get.domain)
        if DnsDomainProvider.objects.filter(domains__contains=root).first():
            support.append("auto")  # 自动解析功能
            support.append("ssl_cert")  # 自动部署证书

        exist = None
        for ssl in DomainValid.get_best_ssl(get.domain):
            if DomainValid.match_ssl_dns(get.domain, ssl, False):
                exist = ssl
                break

        if exist is not None:
            result["hash"] = exist.hash
            if bool("CloudFlareDns" in exist.auth_info.get("auth_to", "")):
                # ip为内网地址不可以开启代理
                try:
                    local_ip = public.GetLocalIp()
                    provate = ipaddress.IPv4Address(local_ip).is_private
                except Exception:
                    provate = True
                if not provate:
                    # 是否支持 CF 代理
                    support.append("cf_proxy")
        result["support"] = support
        return public.success_v2(result)

    def ssl_tasks_status(self, get):
        """
        获取任务状态
        """
        try:
            get.validate([
                Param("task_type").Integer(),
                Param("task_id").Integer(),
            ], [
                public.validate.trim_filter(),
            ])
        except Exception as ex:
            public.print_log("error info: {}".format(ex))
            return public.return_message(-1, 0, str(ex))

        if not hasattr(get, "task_id"):
            task_type = WorkFor.sites if not hasattr(get, "task_type") else int(get.task_type)
            data = DnsDomainTask.objects.filter(
                task_type=task_type, task_status__lt=100,
            ).as_list()
        else:
            objs = DnsDomainTask.objects.filter(id=get.task_id).first()
            data = objs.as_dict() if objs else "Task Not Found!"
        return public.success_v2(data)

    # ========== Panel ===========
    def get_panel_domain(self, get=None):
        if not os.path.exists(PANEL_DOMAIN):
            # 填充已经存在的限制domain
            if os.path.exists(PANEL_LIMIT_DOMAIN):
                limit_domain = public.readFile(PANEL_LIMIT_DOMAIN)
                if limit_domain:
                    public.writeFile(PANEL_DOMAIN, limit_domain, "w")
                else:
                    public.writeFile(PANEL_DOMAIN, "", "w")
                return public.success_v2({"domain": limit_domain})

            else:
                public.writeFile(PANEL_DOMAIN, "", "w")
                return public.success_v2({"domain": ""})

        return public.success_v2({"domain": public.readFile(PANEL_DOMAIN)})

    def set_panel_domain_ssl(self, get):
        """
        get.domain = {
            "hash": "xxx",
            "domain": "example.com",
            "support": ["auto" (自动解析), "ssl_cert" (自动部署), "cf_proxy" (开启cf代理)],
            "auth_type": "http" (http验证) or "dns" (dns验证),
        }
        """
        try:
            get.validate([
                Param("domain").String().Require(),
            ], [
                public.validate.trim_filter(),
            ])
            get.domain = json.loads(get.domain)
        except Exception as ex:
            public.print_log("error info: {}".format(ex))
            return public.return_message(-1, 0, str(ex))
        auth_type = get.domain.get("auth_type")
        domain = get.domain.get("domain", "").strip()
        if "*." in domain:
            return public.fail_v2(public.lang("Wildcard domain is not supported!"))
        if not DomainValid.is_valid_domain(domain):
            return public.fail_v2(public.lang("Domain Not Valid!"))

        get.domain["domain"] = domain
        if not domain:
            return public.fail_v2(public.lang("domain is empty"))
        if auth_type not in ["http", "dns"]:
            return public.fail_v2(public.lang("auth_type must be 'http' or 'dns'"))
        # org = public.readFile(PANEL_DOMAIN)
        # if domain == org:
        #     return public.success_v2("Set Panel's SSL Successfully!")

        # real chage
        task_obj = generate_panel_task(get.domain)
        if auth_type == "dns":
            support = get.domain.get("support")
            if "cf_proxy" in support:
                support.remove("cf_proxy")
            get.domain["support"] = support

            dns_task = threading.Thread(
                target=init_panel_dns, args=(get.domain, task_obj)
            )
            dns_task.start()
        else:
            http_task = threading.Thread(
                target=init_panel_http, args=(domain, task_obj)
            )
            http_task.start()
        return public.success_v2(
            {
                "result": "Set Panel's SSL Successfully! Please wait a few times.",
                "task_id": task_obj.id
            }
        )

    # ========== Mail check ===========
    def mail_record_check(self, get):
        """
        邮箱域名解析检查
        get.domain = "example.com"
        """
        try:
            get.validate([
                Param("domain").String().Require(),
            ], [
                public.validate.trim_filter(),
            ])
        except Exception as ex:
            public.print_log("error info: {}".format(ex))
            return public.return_message(-1, 0, str(ex))
        domain = get.domain.strip()
        if not DomainValid.is_valid_domain(domain):
            return public.fail_v2(public.lang("Domain Not Valid!"))
        domain_info = {
            'hash': '',
            'domain': domain
        }
        records = get_mail_record(domain_info)
        if isinstance(records, str):
            return public.fail_v2(public.lang(records))
        return public.success_v2(records)


def move_old_account():
    old_dns_api = os.path.join(public.get_panel_path(), "config/dns_api.json")
    read = public.readFile(old_dns_api)
    once = os.path.join(public.get_panel_path(), "config/dns_api_once.pl")
    if not os.path.exists(once):
        public.writeFile(once, "0")

    if public.readFile(once) != "0":
        return
    try:
        dnsapi_config = json.loads(read) if read else []
    except Exception:
        return
    for dns in dnsapi_config:
        try:
            if dns.get("name") == "CloudFlareDns":
                dns_name = "CloudFlareDns"
                key = ""
                account = ""
                for cf in dns.get("data", []):
                    if cf.get("key") == "SAVED_CF_MAIL" and cf.get("value") != "":
                        account = cf.get("value", "")
                    elif cf.get("key") == "SAVED_CF_KEY" and cf.get("value") != "":
                        key = cf.get("value")
                if dns_name and key:
                    try:
                        exists = DnsDomainProvider.objects.filter(
                            name=dns_name, api_user=account, api_key=key
                        ).first()
                        if not exists:
                            if os.path.exists('/www/server/panel/data/cf_limit_api.pl'):
                                limit = True
                            else:
                                limit = False
                            get = public.dict_obj()
                            get.name = dns_name
                            get.api_user = account
                            get.api_key = key
                            get.permission = "limit" if limit is True else "global"
                            get.alias = "myCloudFlareDns"
                            DomainObject().create_dns_api(get)
                    except:
                        pass
            elif dns.get("name") == "NameCheapDns":
                dns_name = "NameCheapDns"
                key = ""
                account = ""
                for nc in dns.get("data", []):
                    if nc.get("key") == "SAVED_NC_ACCOUNT" and nc.get("value") != "":
                        account = nc.get("value", "")
                    elif nc.get("key") == "SAVED_CX_APIKEY" and nc.get("value") != "":
                        key = nc.get("value")
                if dns_name and key and account:
                    try:
                        exists = DnsDomainProvider.objects.filter(
                            name=dns_name, api_user=account, api_key=key
                        ).first()
                        if not exists:
                            try:
                                get = public.dict_obj()
                                get.name = dns_name
                                get.api_user = account
                                get.api_key = key
                                get.alias = "myNameCheapDns"
                                DomainObject().create_dns_api(get)
                            except Exception:
                                import traceback
                                public.print_log(traceback.format_exc())
                    except:
                        pass
        except Exception:
            continue
    public.writeFile(once, "1")


move_old_account()
