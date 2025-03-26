# coding: utf-8
import json
import os
from hashlib import md5
from typing import Optional, List

import public
from acme_v2 import acme_v2
from panelDnsapi import BaseDns
from public.aaModel import *
from ssl_domainModelV2.config import DNS_MAP, DnsTask, UseFor


def generate_log(body_str: str) -> str:
    try:
        md5_obj = md5()
        md5_obj.update(body_str.encode("utf-8"))
        log_path = f"{public.get_panel_path()}/logs/dns_domain_logs"
        if not os.path.exists(log_path):
            os.makedirs(log_path)
        log = f"{log_path}/{md5_obj.hexdigest()}.log"
        if not os.path.exists(log):
            os.mknod(log)
        return log
    except Exception as e:
        public.print_log(e)
        return ""


class DnsDomainProvider(aaModel):
    id = IntField(primary_key=True)
    name = StrField(default="", ps="品牌名")
    api_user = StrField(default="", ps="api user账号")
    api_key = StrField(default="", ps="api token密钥")
    status = IntField(default=1, ps="状态")
    permission = StrField(default="-", ps="api权限, 仅限CF")
    domains = ListField(default=[], ps="拥有域名")
    alias = StrField(default="", ps="别名")
    ps = StrField(default="", ps="备注")
    create_time = DateTimeStrField(auto_now_add=True, ps="创建时间")
    update_time = DateTimeStrField(auto_now=True, ps="更新时间")

    def _before_save(self) -> bool:
        import PluginLoader
        if PluginLoader.get_auth_state() > 0:
            return True
        if DnsDomainProvider.objects.all().count() < 1:
            return True
        return False

    @property
    def dns_obj(self) -> Optional[BaseDns]:
        dns_obj = DNS_MAP.get(self.name)
        if not dns_obj:
            return None
        limit = False if self.permission == "global" else True
        return dns_obj(self.api_user, self.api_key, limit=limit)

    def get_ssl_log(self, domains: list = None) -> str:
        if not domains:
            domains = self.domains
        body = f"{self.name}{self.api_user}{self.api_key}{domains}"
        return generate_log(body)

    @staticmethod
    def dns_logger(msg):
        public.WriteLog("DnsSSLManager", msg)

    def model_create_dns_record(self, body: dict) -> dict:
        if not body:
            return {"status": False, "msg": "record info is empty"}

        if self.name == "CloudFlareDns":  # 处理cf
            if body.get("proxy") not in [0, 1]:
                body["proxy"] = 0
            if not body.get("record", "").endswith(f'.{body.get("domain")}'):
                body["record"] = f'{body.get("record")}.{body.get("domain")}'

        dns_obj = self.dns_obj
        if not dns_obj:
            return {"status": False, "msg": "not supported provider"}
        try:
            res = dns_obj.create_org_record(
                domain_name=body.get("domain", ""),
                record=body.get("record", ""),
                record_value=body.get("record_value", public.GetLocalIp()),
                record_type=body.get("record_type", "A"),
                ttl=body.get("ttl", 1),
                proxied=body["proxy"],
            )
            if res.get("status"):
                body["provider_id"] = self.id
                body["provider_name"] = self.name
                body["api_user"] = self.api_user
                DnsDomainRecord(**body).save()
                self.dns_logger(f'Create Dns Record ['
                                f'domain={body.get("domain")}, '
                                f'record={body.get("record")}, '
                                f'type={body.get("record_type")}, '
                                f'value={body.get("record_value")}'
                                f'] Successfully!')
                return {"status": True, "msg": "Create Successfully!"}
            else:
                return {"status": False, "msg": res.get("msg")}
        except Exception as e:
            public.print_log("create dns record error %s " % e)
            return {"status": False, "msg": "create dns record error %s " % e}

    def model_delete_dns_record(self, record_id: int) -> dict:
        dns_obj = self.dns_obj
        if not dns_obj:
            return {"status": False, "msg": "not supported provider"}
        try:
            target = DnsDomainRecord.objects.filter(id=record_id).first()
            if not target:
                return {"status": False, "msg": "Record not found"}
            res = dns_obj.remove_record(
                domain_name=target.domain,
                record=target.record,
                record_type=target.record_type,
            )
            if res.get("status"):
                del_obj = DnsDomainRecord.objects.filter(id=record_id).first()
                self.dns_logger(f"Delete Dns Record ["
                                f"domain={del_obj.domain}, "
                                f"record={del_obj.record}, "
                                f"type={del_obj.record_type}, "
                                f"value={del_obj.record_value}"
                                f"] Successfully!")
                del_obj.delete()
                return {"status": True, "msg": "Delete Successfully!"}
            else:
                return {"status": False, "msg": res.get("msg")}
        except Exception as e:
            import traceback
            public.print_log(traceback.format_exc())
            public.print_log("delete dns record error %s" % e)
            return {"status": False, "msg": "delete dns record error %s " % str(e)}

    def model_edit_dns_record(self, record_id: int, body: dict) -> dict:
        if not body:
            return {"status": False, "msg": "record info is empty"}
        if self.name == "CloudFlareDns" and body.get("proxy") not in [0, 1]:
            body["proxy"] = 0

        dns_obj = self.dns_obj
        if not dns_obj:
            return {"status": False, "msg": "not supported provider"}
        try:
            record = DnsDomainRecord.objects.filter(id=record_id).first()
            if not record:
                return {"status": False, "msg": "Record not found"}
            update = dns_obj.update_record(
                domain_name=record.domain,
                record=record.as_dict(),
                new_record=body
            )
            if update.get("status"):
                DnsDomainRecord.objects.filter(id=record_id).update(body)
                self.dns_logger(
                    f'Update Dns Record ['
                    f'domain={body.get("domain")},'
                    f' record={body.get("record")},'
                    f' type={body.get("record_type")},'
                    f' value={body.get("record_value")}'
                    f'] Successfully!'
                )
                return {"status": True, "msg": "Update Successfully!"}
            else:
                return {"status": False, "msg": update.get("msg")}
        except Exception as e:
            import traceback
            public.print_log(traceback.format_exc())
            public.print_log("update dns record error %s" % e)
            return {"status": False, "msg": "update dns record error %s " % str(e)}

    def model_apply_cert(self, domains: list = None, auto_wildcard: bool = False):
        """
        domains       指定域名
        auto_wildcard 自动构造通配符
        """

        if domains:
            # 指定域名 1,续签 2,新建任意
            targets: List[list] = [domains]
        else:
            # 账号初始化申请
            targets: List[list] = [[x] for x in self.domains]
            auto_wildcard = True

        for t in targets:
            if not self.api_key or not self.name:
                self.dns_logger(f"Apply SSL Certificate Error: please check your dns provider account")
                break
            task_obj = self.create_task(
                {"task_name": DnsTask.apply_ssl.value, "task_log": self.get_ssl_log(targets)}
            )
            try:
                t.sort()
                res = acme_v2().apply_cert_dns_domain(
                    domains=t,
                    auth_to=f"{self.name}|{self.api_user}|{self.api_key}",
                    task_obj=task_obj,
                    auto_wildcard=auto_wildcard,
                )
                if res.get("status"):
                    self.dns_logger(f"domain [{', '.join(t)}] Apply SSL certificate Successfully!")
                else:
                    try:
                        self.dns_logger(f"domain [{', '.join(t)}] Apply SSL certificate Error: {res.get('msg')[0]}")
                    except IndexError:
                        self.dns_logger(f"domain [{', '.join(t)}] Apply SSL certificate Error: {res.get('msg')}")

                task_obj.task_done()
            except Exception as e:
                if task_obj:
                    task_obj.task_done()
                import traceback
                public.print_log(traceback.format_exc())
                self.dns_logger(f"domain [{', '.join(t)}] Apply SSL certificate Error: {str(e)}")
                continue

    def create_task(self, task: dict) -> Optional["DnsDomainTask"]:
        try:
            task = {
                "provider_id": self.id,
                "task_log": self.get_ssl_log(),
                **task,
            }
            return DnsDomainTask(**task).save()
        except Exception as e:
            public.print_log("create task error %s " % e)
            return None


class DnsDomainSSL(aaModel):
    id = IntField(primary_key=True)
    provider_id = IntField(default=0, ps="account")
    hash = StrField(default="", ps="证书hash")
    path = StrField(default="", ps="证书路径")
    dns = ListField(default=[], ps="证书")
    subject = StrField(default="", ps="顶级域名")
    info = DictField(default={}, ps="证书信息")
    not_after = StrField(default="", ps="过期时间")
    not_after_ts = IntField(default=0, ps="过期时间戳")
    alarm = IntField(default=0, ps="是否告警")
    auto_renew = IntField(default=1, ps="是否自动续签")
    user_for_panel = IntField(default=0, ps="是否用于panel")
    user_for = DictField(default={}, ps="用于")
    auth_info = DictField(default={}, ps="认证信息")
    log = StrField(default="", ps="日志路径")
    create_time = DateTimeStrField(auto_now_add=True, ps="创建时间")
    update_time = DateTimeStrField(auto_now=True, ps="更新时间")

    def get_ssl_log(self) -> str:
        auth = self.auth_info.get("auth_to", "")
        if not auth:
            return ""
        dns, user, key = auth.split("|")
        body = f"{dns}{user}{key}{self.dns}"
        return generate_log(body)

    def get_cert(self) -> dict:
        data = {
            "privkey": public.readFile(os.path.join(self.path, "privkey.pem")),
            "fullchain": public.readFile(os.path.join(self.path, "fullchain.pem")),
        }
        return data

    def deploy_sites(self, site_names: list) -> dict:
        try:
            # all cancel
            if not site_names:
                self.user_for[UseFor.sites.value] = []
                self.save()
                return {"status": True, "msg": "Deploy Successfully!"}

            from panel_ssl_v2 import panelSSL
            get = public.dict_obj()
            get.BatchInfo = json.dumps([
                {
                    "certName": self.subject,
                    "siteName": x,
                    "ssl_hash": self.hash,
                } for x in site_names
            ])
            batch_deploy = panelSSL().SetBatchCertToSite(get)

            # cover update sites use for
            new_use_for = [
                x.get("siteName") for x in batch_deploy.get("successList", [])
                if x.get("siteName") in site_names
            ]
            self.user_for[UseFor.sites.value] = new_use_for
            self.save()

            # remove domain which is link to other ssl
            for other_ssl in DnsDomainSSL.objects.filter(hash__ne=self.hash):
                current = other_ssl.user_for.get(UseFor.sites.value, [])
                for new in new_use_for:
                    if new in current:
                        current.remove(new)
                other_ssl.user_for[UseFor.sites.value] = current
                other_ssl.save()

            # generate msg
            if batch_deploy.get("faild") != 0:
                msg = ""
                if batch_deploy.get("successList"):
                    msg += f'Success : {[x.get("siteName") for x in batch_deploy.get("successList")]}, '
                if batch_deploy.get("faildList"):
                    msg += f'Faild : {[x.get("siteName") for x in batch_deploy.get("faildList")]}'
                return {"status": False, "msg": msg}

            return {"status": True, "msg": "Deploy Successfully!"}
        except Exception as e:
            import traceback
            public.print_log(traceback.format_exc())
            return {"status": False, "msg": str(e)}

    class _Meta:
        table_name = "dns_domain_ssl"
        index = [
            "subject",
        ]


class DnsDomainRecord(aaModel):
    id = IntField(primary_key=True)
    provider_id = IntField(default=0, ps="供应商id")
    provider_name = StrField(default="", ps="供应商名")
    api_user = StrField(default="", ps="api user账号")
    domain = StrField(default="", ps="域名")
    record = StrField(default="", ps="记录")
    record_type = StrField(default="A", ps="类型")
    record_value = StrField(default="", ps="记录值")
    ttl = IntField(default=1, ps="时间, 1为Auto遵循CF")
    proxy = IntField(default=-1, ps="代理, 仅限cloudflare")
    ps = StrField(default="aaPanel DNS Manager Sync", ps="备注")
    create_time = DateTimeStrField(auto_now_add=True, ps="创建时间")
    update_time = DateTimeStrField(auto_now=True, ps="更新时间")

    class _Meta:
        index = [
            "domain",
            "provider_id",
            "record_type",
        ]


class DnsDomainTask(aaModel):
    id = IntField(primary_key=True)
    provider_id = IntField(default=0, ps="供应商id")
    task_name = StrField(default="DnsDomainTask", ps="任务名")
    task_status = IntField(default=0, min=0, max=100, ps="任务状态")
    # task_type = StrField(default="", ps="任务类型")
    task_result = StrField(default="", ps="任务结果")
    task_log = StrField(default="", ps="任务日志")
    create_time = DateTimeStrField(auto_now_add=True, ps="创建时间")

    class _Meta:
        index = [
            "task_status",
            "task_name",
        ]

    def task_transfer(self, set_status: int = None, add: int = None, task_result: str = "running"):
        try:
            if set_status and self.task_status >= int(set_status):
                return
            if not set_status:
                if add:
                    self.task_status += int(add)
                else:
                    self.task_status += 10
            else:
                self.task_status = int(set_status)

            if self.task_status >= 100:
                self.task_status = 99
            self.task_result = task_result
            self.save()
        except Exception as e:
            public.print_log(f"task_transfer error {e}")

    def task_done(self, task_result: str = "success"):
        try:
            self.task_result = task_result
            self.task_status = int(100)
            self.save()
        except Exception as e:
            public.print_log(f"task_done error {e}")

    def task_destroy(self):
        try:
            self.delete()
        except Exception:
            pass
