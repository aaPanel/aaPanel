# coding: utf-8
# ------------------------------
# 域名管理
# ------------------------------
import json
import os.path
import shutil
import threading
import time
from datetime import datetime

import public
from BTPanel import cache
from panelDnsapi import extract_zone
from panel_site_v2 import panelSite
from public.aaModel import Q
from public.validate import Param
from .config import DNS_MAP, UseFor, DnsTask
from .model import (
    DnsDomainProvider,
    DnsDomainRecord,
    DnsDomainSSL,
    DnsDomainTask,
)
from .service import (
    init_dns_process,
    SyncService,
    DomainValid,
    make_suer_alarm_task,
    make_suer_renew_task,
)


# noinspection PyUnusedLocal
class DomainObject:
    date_format = "%Y-%m-%d"
    vhost = os.path.join(public.get_panel_path(), "vhost")
    sender_task = os.path.join(
        public.get_panel_path(), "data/mod_push_data/sender.json"
    )

    def __init__(self):
        self.supports = list(DNS_MAP.keys())

    @staticmethod
    def _end_time(data_str: str) -> int:
        if not data_str:
            return 0
        today = datetime.today().date()
        end_date = datetime.strptime(data_str, DomainObject.date_format).date()
        return (end_date - today).days if today <= end_date else 0

    @staticmethod
    def _hide_account(data: dict, key: str = "api_user") -> dict:
        if len(data.get(key, "")) > 0:
            data[key] = data[key][:len(data[key]) // 2] + "***"
        return data

    @staticmethod
    def _add_ssl_info(data: dict) -> dict:
        new_domains = []
        domains = data.get("domains", [])
        for domain in domains:
            ssl_obj = DnsDomainSSL.objects.filter(
                Q(provider_id=data.get("id", 0)) & (Q(subject=domain) | Q(subject=f"*.{domain}"))
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
            provider_id=data.get("id", 0), task_status__lt=100
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
        running = SyncService().get_lock()
        if running is False:
            task = threading.Thread(target=SyncService(target_id).process)
            task.start()
        return public.success_v2("success")

    def list_dns_api(self, get):
        """
        dns api 列表
        """
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
        try:
            one_hours = 1000 * 60 * 60
            out_time = round(time.time() * 1000) - one_hours
            DnsDomainTask.objects.filter(create_time__lte=out_time).delete()
        except Exception:
            pass

        page = int(getattr(get, "p", 1))
        limit = int(getattr(get, "limit", 100))
        obj = DnsDomainProvider.objects.all()
        if hasattr(get, "pid"):
            obj = DnsDomainProvider.objects.filter(id=get.pid)
        total = obj.count()
        result = obj.limit(limit).offset((page - 1) * limit).as_list()
        for r in result:
            r = self._hide_account(r)
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
            return public.fail_v2("'*' Symbols that are not allowed")
        if hasattr(get, "status"):
            get.status = int(get.status)
        if get.name not in self.supports:
            return public.fail_v2(f"Provider not support! Support DNS provider :{self.supports}")
        if get.name == "CloudFlareDns":
            if not hasattr(get, "permission") or get.permission not in ["limit", "global"]:
                return public.fail_v2("CloudFlareDns Permission must be 'limit' or 'global'!")
        else:
            get.permission = "-"
        try:
            dns_obj = DnsDomainProvider(**get.get_items()).save()
            if dns_obj:
                init_task = threading.Thread(
                    target=init_dns_process, args=(dns_obj.as_dict(),)
                )
                init_task.start()
            else:
                return public.fail_v2("Please Upgrade PRO Version!")
        except Exception as ex:
            import traceback
            public.print_log(traceback.format_exc())
            return public.fail_v2(str(ex))
        return public.success_v2("Save Successfully!")

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
        DnsDomainProvider.objects.filter(id=int(get.id)).delete()
        return public.success_v2("Delete Successfully!")

    def edit_dns_api(self, get):
        if not hasattr(get, "id"):
            return public.fail_v2("id is required")
        if hasattr(get, "status"):
            get.status = int(get.status)
        if hasattr(get, "name") and get.name == "CloudFlareDns":
            if not hasattr(get, "permission") or get.permission not in ["limit", "global"]:
                return public.fail_v2("CloudFlareDns Permission must be 'limit' or 'global'")
        if hasattr(get, "user") and "*" in get.api_user:
            return public.fail_v2("'*' symbols that are not allowed")

        try:
            DnsDomainProvider.objects.filter(id=get.id).update(get.get_items())
        except Exception as ex:
            return public.fail_v2(str(ex))
        return public.success_v2("Save Successfully!")

    # =========== dns 记录 ===========
    def list_dns_record(self, get):
        try:
            get.validate([
                Param("p").Integer(),
                Param("limit").Integer(),
                Param("search_pid").Integer().Require(),
                Param("domain").String(),
                Param("search").String(),
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
            return public.fail_v2("Provider not found!")
        if hasattr(get, "domain"):
            domain_name = get.domain
        else:
            domain_name = provider.domains[0] if provider.domains else ""

        cache_expire = False
        key = f"aaDomain_{provider.id}_{domain_name}"
        if cache:  # 1min cache
            cache_data = cache.get(key)
            cache_expire = True if cache_data is None else False
        if cache_expire:  # refresh data
            SyncService().records_process(
                provider_obj=provider, all_domains=[domain_name]
            )
            cache.set(key, "1", 60)

        if not hasattr(get, "search"):
            obj = DnsDomainRecord.objects.filter(provider_id=pid, domain=domain_name)
        else:
            obj = DnsDomainRecord.objects.filter(
                Q(provider_id=pid, domain=domain_name) & (
                        Q(record__like=get.search) | Q(record_value__like=get.search)
                )
            )

        total = obj.count()
        result = obj.limit(limit).offset((page - 1) * limit).as_list()
        data = []
        for r in result:
            r = self._hide_account(r)
            data.append(r)
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
        }
        if hasattr(get, "ps"):
            body["ps"] = get.ps
        response = provider.model_create_dns_record(body)
        if not response.get("status"):
            return public.fail_v2(response.get("msg"))
        return public.success_v2("Save Successfully!")

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
            return public.fail_v2("DNS record Not Found!")
        provider = DnsDomainProvider.objects.find_one(id=record.provider_id)
        if not provider:
            return public.fail_v2("DNS Provider Not Found!")
        response = provider.model_delete_dns_record(int(get.id))
        if not response.get("status"):
            return public.fail_v2(response.get("msg"))
        return public.success_v2("Delete Successfully!")

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
            return public.fail_v2("DNS Provider Not Found!")
        target = DnsDomainRecord.objects.find_one(id=record_id)
        if not target:
            return public.fail_v2("DNS Record Not Found!")
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
            "ps": ps,
        }
        if any([
            target.record != get.record,
            target.record_type != get.record_type,
            target.record_value != get.record_value,
            target.ttl != int(get.ttl),
            target.proxy != int(get.proxy),
        ]):
            real_change = True
        if not real_change:
            DnsDomainRecord.objects.filter(id=record_id).update(new_body)
            return public.success_v2("Update Successfully!")
        # real change
        try:
            update = provider.model_edit_dns_record(record_id, new_body)
            if update.get("status"):
                return public.success_v2("Update Successfully!")
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
            return public.fail_v2("DNS Provider Not Found!")
        data = self._add_ssl_info(provider.as_dict())
        data = data.get("domains", [])
        if hasattr(get, "domain"):  # filter domain
            data = [x for x in data if get.domain in x.get("name", "")]

        for d in data:
            d["records"] = DnsDomainRecord.objects.filter(
                domain=d.get("name", ""), provider_id=int(get.id)
            ).count()
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
            ], [
                public.validate.trim_filter(),
            ])
        except Exception as ex:
            public.print_log("error info: {}".format(ex))
            return public.return_message(-1, 0, str(ex))
        page = int(getattr(get, "p", 1))
        limit = int(getattr(get, "limit", 100))
        ssl_obj = DnsDomainSSL.objects.all()
        total = ssl_obj.count()
        ssl_obj.limit(limit).offset((page - 1) * limit)
        data = [
            self._add_task_info(
                data={
                    "hash": ssl.hash,
                    "provider": ssl.info.get("issuer_O", "unknown"),
                    "issuer": ssl.info.get("issuer", "unknown"),
                    "verify_domains": list(set(ssl.dns + [ssl.subject])),
                    "end_time": self._end_time(ssl.not_after),
                    "end_date": ssl.not_after,
                    "auto_renew": ssl.auto_renew,
                    "last_apply_time": ssl.create_time,
                    "cert": {
                        "csr": public.readFile(ssl.path + "/fullchain.pem"),  # 证书
                        "key": public.readFile(ssl.path + "/privkey.pem"),  # 密钥
                    },
                    "log": ssl.get_ssl_log(),
                    "use_for": ssl.user_for,
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
            return public.fail_v2("SSL Certificate  Not Found!")

        download_path = os.path.join(self.vhost, f"/ssl_saved/download")
        if not os.path.exists(download_path):
            os.makedirs(download_path)

        output_path = os.path.join(download_path, f"{get.hash}")
        if os.path.exists(f"{output_path}.zip"):
            return public.success_v2(f"{output_path}.zip")
        try:
            shutil.make_archive(output_path, "zip", file_path)
        except Exception as e:
            return public.fail_v2(f"error: {str(e)}")
        return public.success_v2(f"{output_path}.zip")

    def renew_cert(self, get):
        """
        续签
        """
        try:
            get.validate([
                Param("hash").String(),
            ], [
                public.validate.trim_filter(),
            ])
        except Exception as ex:
            public.print_log("error info: {}".format(ex))
            return public.return_message(-1, 0, str(ex))

        if hasattr(get, "hash"):
            ssl_obj = DnsDomainSSL.objects.filter(hash=get.hash)
        else:
            ts_month = 30 * 24 * 60 * 60 * 1000
            ssl_obj = DnsDomainSSL.objects.filter(not_after_ts__lt=int(time.time() * 1000) + ts_month)

        log = None
        for ssl in ssl_obj:
            provider = DnsDomainProvider.objects.find_one(id=ssl.provider_id)
            if not provider:
                return public.fail_v2("DNS Provider Not Found!")
            log = provider.get_ssl_log(ssl.dns)
            renew_task = threading.Thread(target=provider.model_apply_cert, args=(ssl.dns,))
            renew_task.start()

        if hasattr(get, "hash"):
            return public.success_v2(log)
        else:
            return public.success_v2("Successfully Renewed!")

    def apply_new_ssl(self, get):
        """
        申请证书
        """
        try:
            get.validate([
                Param("domains").String().Require(),
            ], [
                public.validate.trim_filter(),
            ])
            get.domains = json.loads(get.domains)
        except Exception as ex:
            public.print_log("error info: {}".format(ex))
            return public.return_message(-1, 0, str(ex))

        targets = []
        provider = None
        for d in get.domains:
            if not targets:
                root, _, _ = extract_zone(d)
                provider = DnsDomainProvider.objects.find_one(domains__has_element=root)
                if not provider:
                    return public.fail_v2(f"DNS Provider Not Found! for {root}")
                targets = provider.domains
            temp_root, _, _ = extract_zone(d)
            if temp_root not in targets:
                return public.fail_v2("domains do not belong to the same DNS Provider Account. Please verify.")
        apply_domains = list(set(get.domains))
        log = provider.get_ssl_log(apply_domains)
        apply_task = threading.Thread(
            target=provider.model_apply_cert, args=(apply_domains,)
        )
        apply_task.start()
        return public.success_v2(log)

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
        from ssl_manage import SSLManger
        try:
            data = SSLManger().save_by_data(get.cert, get.key)
            if data:
                # 再次检测, 兼容被跳过的情况
                ssl = DnsDomainSSL.objects.filter(hash=data.get("hash")).first()
                if not ssl:
                    del data["id"]
                    del data["create_time"]
                    # 从auth中尝试匹配现有api
                    provider, account, token = data.get("auth_info").get("auth_to", "||").split("|")
                    p_obj = DnsDomainProvider.objects.filter(
                        name=provider, api_user=account, api_key=token
                    ).first()
                    pid = p_obj.id if p_obj and provider != "" else 0
                    data["provider_id"] = pid
                    DnsDomainSSL(**data).save()
        except Exception as ex:
            public.print_log("error info: {}".format(ex))
            return public.fail_v2(str(ex))
        return public.success_v2("success")

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
            return public.fail_v2("SSL Certificate Not Found!")
        # vhost/ssl为site ssl证书存放目录
        vpath = os.path.join(self.vhost, "ssl", ssl_obj.subject)
        if os.path.exists(vpath):
            public.ExecShell("rm -rf " + vpath)

        try:
            from ssl_manage import ssl_db as old_ssl_db
            old_ssl_db.connection().where("hash=?", (get.hash,)).delete()
            public.S("ssl_info").where("hash=?", (get.hash,)).delete()
            ssl_obj.delete()
        except Exception as ex:
            public.print_log("error info: {}".format(ex))
            return public.fail_v2(str(ex))
        return public.success_v2("success")

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
            return public.fail_v2("SSL Certificate Not Found!")
        if ssl_obj.auto_renew == 1:
            ssl_obj.auto_renew = 0
        else:
            make_suer_renew_task()  # make suer corn task
            ssl_obj.auto_renew = 1
        ssl_obj.save()
        return public.success_v2("Setting Successfully!")

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
            return public.fail_v2("SSL Not Found!")
        alarm = int(get.alarm)
        if alarm == 1:  # open
            res, msg = make_suer_alarm_task()  # make suer alarm task
            if res:
                ssl_obj.alarm = alarm
                ssl_obj.save()
                return public.success_v2("Setting Successfully!")
            else:
                return public.fail_v2(msg)
        else:  # close
            ssl_obj.alarm = alarm
            ssl_obj.save()
            return public.success_v2("Setting Successfully!")

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
            return public.fail_v2("SSL Certificate Not Found!")
        sites = public.S("sites").field(
            "id", "name", "path", "status", "type_id", "project_type",
        ).select()
        for s in sites:
            dns = ssl_obj.dns
            for sub in dns:
                if sub.startswith("*."):
                    sub = sub[2:]
                if sub in s.get("name", ""):
                    s["match"] = 1
                    break
        data = {
            "sites": sites,
            "mails": [],
            "accounts": [],
        }
        return public.success_v2(data)

    def cert_deploy_sites(self, get):
        """
        部署到sites, 包含取消
        """
        try:
            get.validate([
                Param("hash").String().Require(),
                Param("domains").String().Require(),
            ], [
                public.validate.trim_filter(),
            ])
        except Exception as ex:
            public.print_log("error info: {}".format(ex))
            return public.return_message(-1, 0, str(ex))
        try:
            get.domains = json.loads(get.domains)
        except json.decoder.JSONDecodeError as js_err:
            public.print_log("error info: {}".format(js_err))
            return public.return_message(-1, 0, str(js_err))

        ssl_obj = DnsDomainSSL.objects.find_one(hash=get.hash)
        if not ssl_obj:
            return public.fail_v2("SSL Certificate Not Found!")

        # 当前得域名
        user_for = ssl_obj.user_for.get(UseFor.sites.value, [])
        # 不同的元素
        diff = list(set(user_for).symmetric_difference(set(get.domains)))
        # 1, 需要移除的sites
        for remove in [x for x in diff if x in set(user_for)]:
            new_get = public.dict_obj()
            new_get.siteName = remove
            new_get.updateOf = 1
            remove_res = panelSite().CloseSSLConf(new_get)
        # 2, 移除diff之后, 部署
        result = ssl_obj.deploy_sites(get.domains)
        if result.get("status"):
            return public.success_v2("Setup successfully!")
        else:
            return public.fail_v2(result.get("msg", "Deploy Faild..."))

    # todo
    def cert_deploy_mails(self, get):
        # ssl_obj.user_for[UseFor.mails.value] = []
        # ssl_obj.save()
        pass

    # todo
    def cert_deploy_panel(self, get):
        # ssl_obj.user_for[UseFor.panel.value] = []
        # ssl_obj.save()
        pass

    # =========== add Site ===========
    def add_site_check(self, get):
        """
        检测域名支持服务
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
            "support": [],
        }
        for ssl in DnsDomainSSL.objects.all():
            if DomainValid.domain_valid(ssl, get.domain):
                result = {
                    "hash": ssl.hash,
                    "domain": get.domain,
                    "support": ["auto", "ssl_cert"],
                }
                if bool("CloudFlareDns" in ssl.auth_info.get("auth_to", "")):
                    result.update({"cf_proxy": 1})
                    result["support"].append("cf_proxy")
                return public.success_v2(result)
        return public.success_v2(result)


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
