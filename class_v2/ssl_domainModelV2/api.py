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
from datetime import datetime
from typing import Tuple

import public
from BTPanel import cache
from config_v2 import config
from panelDnsapi import extract_zone
from panel_site_v2 import panelSite
from public.aaModel import Q
from public.exceptions import HintException
from public.validate import Param
from .config import DNS_MAP, WorkFor, PANEL_DOMAIN, PANEL_LIMIT_DOMAIN
from .model import (
    DnsDomainProvider,
    DnsDomainRecord,
    DnsDomainSSL,
    DnsDomainTask,
)
from .service import (
    init_dns_process,
    init_panel_dns,
    generate_panel_task,
    SyncService,
    DomainValid,
    make_suer_alarm_task,
    update_ssl_link,
)


# noinspection PyUnusedLocal
class DomainObject:
    date_format = "%Y-%m-%d"
    vhost = os.path.join(public.get_panel_path(), "vhost")
    mail_db_file = "/www/vmail/postfixadmin.db"

    def __init__(self):
        self.supports = list(DNS_MAP.keys())

    @staticmethod
    def _clear_task_force():
        # clear task, 1 hours
        try:
            one_hours = 1000 * 60 * 60
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
            return (end_date - today).days if today <= end_date else 0
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
        running = SyncService().get_lock()
        if running is False:
            task = threading.Thread(target=SyncService(target_id).process)
            task.start()
        return public.success_v2("success")

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

        if DnsDomainProvider.objects.filter(alias=get.alias).first():
            return public.fail_v2("Alias already exists!")

        if DnsDomainProvider.objects.filter(
                api_user=get.api_user, api_key=get.api_key, name=get.name,
        ).first():
            return public.fail_v2(f"Account already exists!")

        try:
            dns = DnsDomainProvider(**get.get_items())
            if not dns.is_pro():
                return public.fail_v2("Please Upgrade PRO Version!")
            dns.dns_obj.verify()
            dns_save = dns.save()
            init_task = threading.Thread(
                target=init_dns_process, args=(dns_save.as_dict(),)
            )
            init_task.start()
            public.set_module_logs("sys_domain", "Add_Dns_Api", 1)
            return public.success_v2("Save Successfully!")
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

        # alias 不允许重复
        if hasattr(get, "alias") and DnsDomainProvider.objects.filter(alias=get.alias).first():
            return public.fail_v2("Alias already exists!")
        try:
            dns = DnsDomainProvider.objects.filter(id=get.id).first()
            for k, v in get.get_items().items():
                if k != "id":
                    setattr(dns, k, v)
            # 仅当开启时候校验
            if dns.status == 1:
                dns.dns_obj.verify()
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
                    "search_and and search can not be used at the same time"
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

        try:
            DnsDomainSSL.objects.filter(hash="").delete()
        except:
            pass

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
                    "log": ssl.log if ssl.log else ssl.get_ssl_log(),
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

        if hasattr(get, "hash"):  # 指定
            ssl_obj = DnsDomainSSL.objects.filter(hash=get.hash)
        else:  # 30天内的cert
            ts_month = 30 * 24 * 60 * 60 * 1000
            ssl_obj = DnsDomainSSL.objects.filter(
                not_after_ts__lt=int(time.time() * 1000) + ts_month
            )

        log = None
        for ssl in ssl_obj:
            provider = DnsDomainProvider.objects.find_one(id=ssl.provider_id)
            if provider:
                _ = provider.dns_obj
                log = provider.get_ssl_log(ssl.dns)
                renew_task = threading.Thread(
                    target=provider.model_apply_cert, args=(ssl.dns,)
                )
                renew_task.start()
            else:
                # 兜底
                log = ssl.get_ssl_log(ssl.dns)
                renew_task = threading.Thread(
                    target=ssl.try_to_apply_ssl, args=(ssl.dns,)
                )
                renew_task.start()

        if hasattr(get, "hash"):
            return public.success_v2(log)
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
                for p in DnsDomainProvider.objects.all():
                    if root in p.domains:
                        provider = p
                        break
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
                    # 尝试匹配现有api
                    DnsDomainSSL(**data).save()

            update_ssl_link()
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
            return public.fail_v2("SSL Not Found!")
        # make_suer_renew_task()  # make suer corn task
        open_map = {0: 1, 1: 0}
        ssl_obj.auto_renew = open_map.get(ssl_obj.auto_renew, 1)
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
            make_suer_alarm_task()  # make suer alarm task
            ssl_obj.alarm = alarm
            ssl_obj.save()
        else:  # close
            ssl_obj.alarm = alarm
            ssl_obj.save()
        return public.success_v2("Setting Successfully!")

    # =========== Deploy ================
    @staticmethod
    def __add_match_flag(targes: list, dns: list, key_word: str = None, match_domain: str = None) -> list:
        if key_word and match_domain:  # 不能同时存在
            return targes

        for t in targes:
            for d in dns:
                if d.startswith("*."):
                    d = d[2:]
                if key_word:
                    if d in t.get(key_word, ""):
                        t["match"] = 1
                        break
                else:
                    if d in match_domain:
                        t["match"] = 1
                        break

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
            return public.fail_v2("SSL Certificate Not Found!")
        # ====================== sites ======================
        # 不考虑status
        sites = public.S("sites").field(
            "id", "name", "path", "status", "type_id", "project_type",
        ).select()
        sites = self.__add_match_flag(sites, ssl_obj.dns, "name")

        # ====================== mails ======================
        mails = []
        if os.path.exists(self.mail_db_file):
            # 不考虑active
            mails = public.S("domain", self.mail_db_file).field(
                "domain", "a_record", "active"
            ).select()
            mails = self.__add_match_flag(mails, ssl_obj.dns, "domain")

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
            panel = self.__add_match_flag(panel, ssl_obj.dns, None, current_domain)

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
        :return: ssl obj, use_for list, get obj
        """
        try:
            get.validate([
                Param("hash").String().Require(),
                Param("domains").String(),
            ], [
                public.validate.trim_filter(),
            ])
        except Exception as ex:
            raise ex

        if hasattr(get, "domains"):
            try:
                get.domains = json.loads(get.domains)
            except json.decoder.JSONDecodeError as js_err:
                raise js_err

        if hasattr(get, "recover"):
            try:
                get.recover = int(get.recover)
            except TypeError as tr:
                raise tr

        ssl_obj = DnsDomainSSL.objects.find_one(hash=get.hash)
        if not ssl_obj:
            raise Exception("SSL Certificate Not Found!")

        return ssl_obj, get

    def cert_deploy_sites(self, get):
        """
        证书部署到 选定的 sites
        """
        try:
            get.validate([
                Param("remove").Integer(),
            ], [
                public.validate.trim_filter(),
            ])
            # 返回ssl对象, get对象
            ssl_obj, get = self.__before_deploy(get)
        except Exception as ex:
            public.print_log("error info: {}".format(ex))
            return public.fail_v2(str(ex))

        # 不同的元素
        diff = list(set(ssl_obj.sites_uf).symmetric_difference(set(get.domains)))
        public.print_log(f"diff {diff}")
        # 1, 需要移除的sites
        for remove in [x for x in diff if x in set(ssl_obj.sites_uf)]:
            new_get = public.dict_obj()
            new_get.siteName = remove
            new_get.updateOf = 1
            try:
                # close site's ssl conf
                remove_res = panelSite().CloseSSLConf(new_get)
                if hasattr(get, "remove") and int(get.remove) == 1:
                    # 尝试移除site dns记录, 异步?
                    provider = DnsDomainProvider.objects.find_one(id=ssl_obj.provider_id)
                    if provider:
                        root, zone, _ = extract_zone(remove)
                        domain_value = root if zone == "" else zone
                        # CloudFlareDns record 自带域名
                        if provider.name == "CloudFlareDns":
                            domain_value += f".{root}"
                        record = DnsDomainRecord.objects.find_one(
                            domain=root, record=domain_value, record_type="A",
                        )
                        if record:
                            res = provider.model_delete_dns_record(record.id)
            except Exception as e:
                public.print_log(f"error info: {str(e)}")
                continue

        # 2, 移除diff之后, 部署
        result = ssl_obj.deploy_sites(get.domains)
        if result.get("status"):
            return public.success_v2("Deploy Site's SSL Successfully!")
        else:
            return public.fail_v2(result.get("msg", "Deploy Faild..."))

    def cert_deploy_mails(self, get):
        """
        证书部署到 选定的 mails
        """
        try:
            ssl_obj, get = self.__before_deploy(get)
        except Exception as ex:
            public.print_log("error info: {}".format(ex))
            return public.fail_v2(str(ex))

        # 不同的元素
        diff = list(set(ssl_obj.mails_uf).symmetric_difference(set(get.domains)))
        # 1, 需要移除的sites
        for remove in [x for x in diff if x in set(ssl_obj.mails_uf)]:
            ...

        return public.success_v2("Deploy Mail's SSL Successfully!")

    def cert_deploy_accounts(self, get):
        """
        证书部署到 选定的 accounts
        """
        try:
            ssl_obj, get = self.__before_deploy(get)
        except Exception as ex:
            public.print_log("error info: {}".format(ex))
            return public.fail_v2(str(ex))

        return public.success_v2("Deploy Account's SSL Successfully!")

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
            return public.success_v2("Deploy Panel's SSL Successfully!")
        return public.fail_v2(res.get("msg", "Deploy Panel's SSL Failed!"))

    # =========== Site ===========
    def add_site_check(self, get):
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
            "support": [],
        }

        targets = DomainValid.get_best_ssl(get.domain)

        for ssl in targets:
            if DomainValid.match_ssl_dns(get.domain, ssl, False):
                result = {
                    "hash": ssl.hash,
                    "domain": get.domain,
                    "support": ["auto", "ssl_cert"],
                }
                if bool("CloudFlareDns" in ssl.auth_info.get("auth_to", "")):
                    # ip为内网地址不可以开启代理
                    try:
                        local_ip = public.GetLocalIp()
                        provate = ipaddress.IPv4Address(local_ip).is_private
                    except Exception:
                        provate = True
                    if not provate:
                        result["support"].append("cf_proxy")
                return public.success_v2(result)
        return public.success_v2(result)

    def ssl_tasks_status(self, get):
        """
        获取任务状态
        """
        try:
            get.validate([
                Param("task_type").Integer(),
            ], [
                public.validate.trim_filter(),
            ])
        except Exception as ex:
            public.print_log("error info: {}".format(ex))
            return public.return_message(-1, 0, str(ex))

        # self._clear_task_force()

        task_type = WorkFor.sites.value if not hasattr(get, "task_type") else int(get.task_type)
        # get.task_type 是否在支持的WorkFor中
        if task_type not in [x.value for x in WorkFor]:
            return public.success_v2([])

        filter_obj = DnsDomainTask.objects.filter(
            task_status__lt=100, task_type=task_type
        )
        data = [
            task.as_dict() for task in filter_obj
        ]
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

        org = public.readFile(PANEL_DOMAIN)
        if get.domain.get("domain") == org:
            return public.success_v2("Set Panel's SSL Successfully!")

        # real chage
        support = get.domain.get("support")
        if "cf_proxy" in support:
            support.remove("cf_proxy")
        get.domain["support"] = support

        task_obj = generate_panel_task(get.domain)
        task = threading.Thread(
            target=init_panel_dns,
            args=(get.domain, task_obj)
        )
        task.start()
        return public.success_v2("Set Panel's SSL Successfully! Please wait a few times.")


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
