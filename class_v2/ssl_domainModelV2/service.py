# coding: utf-8
import json
import os
import re
import time
from typing import List, Tuple

import public
from BTPanel import app
from acme_v2 import acme_v2
from mod.base.msg import SenderManager
from mod.base.push_mod.manager import PushManager, TaskConfig
from panelDnsapi import extract_zone
from public.aaModel import Q
from ssl_domainModelV2.config import DNS_MAP, DnsTask
from ssl_domainModelV2.model import (
    DnsDomainProvider,
    DnsDomainRecord,
    DnsDomainTask,
    DnsDomainSSL,
)

os.chdir('/www/server/panel')

RUNNING = os.path.join(public.get_panel_path(), "class_v2/ssl_domainModelV2/sync_running.pl")
# init status to 0
public.writeFile(RUNNING, "0", "w")


def init_sites_dns(domain_list: list):
    """
    添加网站dns初始化
    """
    make_suer_renew_task()
    if not domain_list:
        return
    # flask app上下文
    with app.app_context():
        root_zero, _, _ = extract_zone(domain_list[0].get("domain"))
        # 是否同域
        for domain in domain_list:
            root, _, _ = extract_zone(domain.get("domain"))
            if root_zero != root_zero:
                public.print_log("domain not the same, not support now")
                return

        flag = True
        ssl_obj = DnsDomainSSL.objects.find_one(hash=domain_list[0].get("hash", ""))
        provider = DnsDomainProvider.objects.filter(id=ssl_obj.provider_id).first()

        for domain in domain_list:
            # ================== record part =======================
            root, zone, _ = extract_zone(domain.get("domain"))
            # zone 为空时, 则为主域名, 否则添加任意子域名
            domain_value = "@" if zone == "" else zone
            proxy = 0 if "cf_proxy" not in domain.get("support", []) else 1
            # 直接进行记录创建
            body = {
                "domain": root,
                "record": domain_value,
                "record_value": public.GetLocalIp(),
                "record_type": "A",
                "ttl": 1,
                "proxy": proxy,
            }
            try:
                if provider:
                    provider.model_create_dns_record(body)
            except Exception:
                import traceback
                public.print_log(traceback.format_exc())

            # ================== domain part=======================
            if ssl_obj and not DomainValid.match_ssl_dns(domain.get("domain", ""), ssl_obj.dns):
                flag = False

        # ================== cert part =======================
        new_domains = [x.get("domain", "") for x in domain_list]
        if not flag:
            try:
                if ssl_obj.provider_id == 0:  # 可能是上传的证书
                    # todo
                    return
                else:  # legal provider
                    provider = DnsDomainProvider.objects.filter(id=ssl_obj.provider_id).first()
                    if provider:
                        provider.model_apply_cert(new_domains)
                        new_ssl = DnsDomainSSL.objects.filter(dns=new_domains).first()
                        if new_ssl:
                            # deploy and update user_for
                            new_ssl.deploy_sites(new_domains)
            except Exception as e:
                import traceback
                public.print_log(f"Sites Init Cert new apply error: {e}")
                public.print_log(traceback.format_exc())
                return

        else:
            # suitable
            try:
                # deploy and append user_for
                ssl_obj.deploy_sites(new_domains)
            except Exception as e:
                import traceback
                public.print_log(f"Sites Init Cert deploy sites error: {e}")
                public.print_log(traceback.format_exc())
                return


def init_dns_process(dns_info: dict):
    """
    api添加后, 初始化厂商
    """
    make_suer_renew_task()
    SyncService(dns_info.get("id")).main(force=True)  # sync base info
    dns_obj = DnsDomainProvider.objects.filter(id=dns_info.get("id")).first()  # reload
    if not dns_obj:
        return
    if not dns_obj._before_save():
        return
    ready_init_apply: List[list] = [[f"*.{x}", x] for x in dns_obj.domains]
    for domain_list in ready_init_apply:
        ssl_obj = DnsDomainSSL.objects.filter(dns=domain_list).first()
        if not ssl_obj:
            dns_obj.model_apply_cert()
        else:
            # update ssl link to new provider
            ssl_obj.provider_id = dns_obj.id
            ssl_obj.save()


def make_suer_org_ssl():
    """
    确保合法的账号下默认泛域名证书存在, 6小时间隔
    """
    org_domain_ssl_pl = os.path.join(
        public.get_panel_path(), "class_v2/ssl_domainModelV2/org_domain_ssl.pl"
    )
    if not os.path.exists(org_domain_ssl_pl):
        public.writeFile(org_domain_ssl_pl, str(round(time.time())), "w")
    last_time = public.readFile(org_domain_ssl_pl)
    if not last_time:
        public.writeFile(org_domain_ssl_pl, str(round(time.time())), "w")
    # every 6 hours
    if last_time and int(last_time) + 3600 * 6 < time.time():
        for provider in DnsDomainProvider.objects.filter(status=1):
            # all domains
            for domain in provider.domains:
                # org ssl exists?
                if DnsDomainSSL.objects.filter(
                        Q(dns=[f"*.{domain}", domain]) | Q(dns=[domain, f"*.{domain}"])
                ).count() == 0:
                    try:
                        provider.model_apply_cert(domains=[domain], auto_wildcard=True)
                    except Exception as e:
                        public.print_log(f"make sure org ssl error : {e}")
                        continue
        public.writeFile(org_domain_ssl_pl, str(round(time.time())), "w")


def make_suer_alarm_task() -> Tuple[bool, str]:
    """
    确保告警推送服务存在, 适用于开关的地方
    """
    # check current task
    task = TaskConfig().get_by_keyword(source="SSL", keyword="all")
    if task:
        return True, "SSL Task Exists"
    # check sender exists
    senders_id = None
    sender_list = SenderManager.get_sender_list(get=None)
    if sender_list.get("status") == 0:
        senders_id = [
            x.get("id") for x in sender_list.get("message", []) if x.get("sender_type") != "sms"
        ]
    if not senders_id:
        return False, "please go to Alarm Settings add some senders"
    # add new task
    get = public.dict_obj()
    get.template_id = "1"
    get.task_data = json.dumps({
        "task_data": {
            "tid": "1",
            "type": "ssl",
            "title": "Certificate (SSL) expiration",
            "status": True,
            "count": 0,
            "interval": 600,
            "project": "all",
            "cycle": 15,
        },
        "sender": senders_id,
        "number_rule": {"day_num": 2, "total": 30},
        "time_rule": {"send_interval": 600, "time_range": [0, 86399]}
    })
    res = PushManager().set_task_conf(get)
    if res.get("status") == 0:
        return True, "SSL Task Created"
    else:
        return False, res.get("msg", "create ssl task error")


def make_suer_renew_task() -> Tuple[bool, str]:
    """
    确保续签服务存在, 适用于开关的地方
    """
    acme_v2().set_crond_v2()
    return True, "Renew task created"


class SyncService(object):
    """
    同步域名,记录
    """
    dns_sync_log = os.path.join(public.get_panel_path(), "logs/dns_sync.log")
    if not os.path.exists(dns_sync_log):
        public.writeFile(dns_sync_log, "")

    def __init__(self, target_id: int = None):
        self.obj = None
        self.target_id = target_id
        if not os.path.exists(RUNNING):
            public.writeFile(RUNNING, "0", "w")

    def write_log(self, body, mode="a"):
        body += "\n"
        with open(self.dns_sync_log, mode) as f:
            f.write(body)

    def get_lock(self) -> bool:
        running = public.readFile(RUNNING)
        if running == "1":
            return True
        else:
            return False

    def _change_lock(self, body: str = "0"):
        public.writeFile(RUNNING, body, "w")

    def process(self):
        make_suer_renew_task()
        self.sync_dns_domains()  # 同步域名, 记录
        self.write_log("SyncService Done!")

    def generate_auth_config(self, obj: DnsDomainProvider, auth: dict) -> dict:
        if obj.name == "CloudFlareDns":
            limit = True if obj.permission == "limit" else False
            config = {**auth, "limit": limit}
        else:
            config = auth
        return config

    def records_process(
            self, provider_obj: DnsDomainProvider,
            all_domains: list,
            task_obj: DnsDomainTask = None
    ):
        if not provider_obj or not provider_obj.dns_obj or not all_domains:
            return
        # 同步每个域名底下的记录值
        for domain in all_domains:
            if task_obj:
                self.write_log(f"|-- Scanning {provider_obj.name} [{domain}] records...")
            # 清理数据
            DnsDomainRecord.objects.filter(provider_id=provider_obj.id, domain=domain).delete()
            res = provider_obj.dns_obj.get_dns_record(domain)
            if not res:
                if task_obj:
                    self.write_log("|-- Not found records, skip...")
                continue
            try:
                res = [
                    {
                        "provider_id": provider_obj.id,
                        "provider_name": provider_obj.name,
                        "api_user": provider_obj.api_user,
                        "domain": domain,
                        "record": r.get("record", ""),
                        "record_type": r.get("record_type", ""),
                        "record_value": r.get("record_value", ""),
                        "ttl": r.get("ttl", 1),
                        "proxy": r.get("proxy", -1),
                    } for r in res
                ]
                res.sort(key=lambda x: x["record_type"])
                DnsDomainRecord.objects.insert_many(res)
            except Exception as e:
                public.print_log(f"DnsDomainRecord insert error {e}")
                continue
            if task_obj:
                task_obj.task_transfer(add=round(100 / len(all_domains)))
                self.write_log(f"|-- [{domain}] Records Update Successfully")

    def sync_dns_domains(self):
        # 获取当前时间转字符
        from datetime import datetime
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.write_log(f"\n=== SyncService Start at {now} ===\n"
                       f"please wait...if task do not start all the time please restart the panel")
        if not self.target_id:
            targets = DnsDomainProvider.objects.filter(status=1)
        else:
            targets = DnsDomainProvider.objects.filter(id=self.target_id)
        for i in targets:
            self.write_log("=" * 68)
            self.write_log(f"| {i.name} {i.api_user}")
            auth = {"api_user": i.api_user, "api_key": i.api_key}
            dns_obj = DNS_MAP.get(i.name)
            if not dns_obj:
                self.write_log(f"|- not support {i.name}")
                continue
            dns_obj = dns_obj(
                **self.generate_auth_config(i, auth)
            )
            task_obj = i.create_task(
                {"task_name": DnsTask.sync_dns.value, "task_log": self.dns_sync_log}
            )
            try:
                time.sleep(1)
                all_domains = dns_obj.get_domains()
                if not all_domains:
                    task_obj.task_done("Verify Fail or Not Found domains, skip...")
                    self.write_log(f"|-- Verify Fail or Not Found domains, skip...")
                    continue
                self.write_log(f"|-- Domains: {', '.join(all_domains)}")
                DnsDomainProvider.objects.filter(id=i.id).update(domains=all_domains)
                task_obj.task_transfer(set_status=30)
                self.write_log(f"|-- {i.name} Update Domains Successfully")
                # 更新域名下的所有记录
                self.records_process(i, all_domains, task_obj)
                task_obj.task_done()
            except Exception:
                if task_obj:
                    task_obj.task_done(f"{i.name} {i.api_user} verify error, skip...")
                self.write_log(f"{i.name} {i.api_user} verify error, skip...")
                public.print_log(f"{i.name} {i.api_user} verify error, skip...")
                continue

    def main(self, force: bool = False):
        if force:
            self.process()
        else:
            # running lock
            self._change_lock("1")
            self.process()
            self._change_lock("0")


class DomainValid:
    """
    简单判断合法可适用的域名
    """

    @staticmethod
    def is_valid_domain(domain: str) -> bool:
        """
        验证域名的格式标准规范
        1. 总长度不超过253个字符
        2. 至少包含两个标签（即至少一个点分隔）
        3. 每个标签长度1~63字符
        4. 标签由字母/数字/连字符组成
        5. 标签不以连字符开头或结尾
        6. 顶级域名（最后一个标签）非纯数字且长度≥2
        """
        # 基础检查
        if not domain or len(domain) > 253:
            return False
        # 分割标签并验证数量
        labels = domain.split(".")
        if len(labels) < 2:
            return False
        # 正则表达式验证每个标签, 不管中文
        label_pattern = r"^[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?$"
        for label in labels:
            if not re.match(label_pattern, label):
                return False
        # 验证顶级域名
        tld = labels[-1]
        if len(tld) < 2 or tld.isdigit():
            return False
        return True

    @staticmethod
    def domain_valid(ssl_obj: DnsDomainSSL, new_domain: str) -> bool:
        """
        校验同域,合法
        """
        for domain in list(set(ssl_obj.dns + [ssl_obj.subject])):
            if DomainValid.is_valid_domain(new_domain):
                valid_domain_root, _, _ = extract_zone(domain)
                new_domain_root, _, _ = extract_zone(new_domain)
                if valid_domain_root == new_domain_root:
                    return True
        return False

    @staticmethod
    def match_ssl_dns(domain: str, valid_dns: str):
        """
        校验证书适用
        """
        if domain in valid_dns:  # 是否精确匹配列表中的某个
            return True
        for dns in valid_dns:
            if dns.startswith("*."):
                base_domain = dns[2:]
                if domain.endswith(base_domain):
                    sub_domain = domain[:-len(base_domain)]
                    sub_domain = sub_domain.rstrip('.')
                    # 是否仍然包含"."
                    if "." not in sub_domain and sub_domain:
                        return True
        return False


if __name__ == "__main__":
    SyncService().main()
