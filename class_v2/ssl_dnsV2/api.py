# coding: utf-8
# -------------------------------------------------------------------
# aaPanel
# -------------------------------------------------------------------
# Copyright (c) 2014-2099 aaPanel(www.aapanel.com) All rights reserved.
# -------------------------------------------------------------------
# Author: aapanel
# -------------------------------------------------------------------
# ------------------------------
# aaDNS api
# ------------------------------
import json
import sys
import threading

if not "class/" in sys.path:
    sys.path.insert(0, "class/")
if not "class_v2/" in sys.path:
    sys.path.insert(0, "class_v2/")

from public.exceptions import HintException
from public.validate import Param
from ssl_domainModelV2.model import DnsDomainProvider
from ssl_domainModelV2.service import DomainValid
from .dns_manager import DnsManager, MailManager
from .helper import *


class DnsApiObject:
    def __init__(self):
        pass

    def install_bind(self, get):
        log = f"{public.get_panel_path()}/logs/install_bind.log"
        if os.path.exists(log):
            public.ExecShell(f"rm -f {log}")
        install_script = os.path.join(
            os.path.dirname(os.path.abspath(__file__)), "bind_script.sh"
        )
        public.ExecShell("chmod +x {}".format(install_script))
        public.ExecShell("nohup bash {} install >>{} 2>&1 &".format(install_script, log))
        return public.success_v2(public.lang("Installing..."))

    def install_pdns(self, get):
        try:
            get.validate([
                Param("act").String("in", ["install", "uninstall"]).Require(),
                Param("clean").Integer(),
            ], [public.validate.trim_filter(), ])
            if not hasattr(get, "clean"):
                get.clean = 1
            else:
                get.clean = int(get.clean)
        except Exception as ex:
            public.print_log("error info: {}".format(ex))
            return public.fail_v2(str(ex))
        log = f"{public.get_panel_path()}/logs/install_pdns.log"
        public.writeFile(log, f"Starting {get.act}...\n")
        install_script = os.path.join(
            os.path.dirname(os.path.abspath(__file__)), "pdns_script.sh"
        )

        public.ExecShell("chmod +x {}".format(install_script))
        public.ExecShell(f"nohup bash {install_script} {get.act} {get.clean} >>{log} 2>&1 &")
        if get.act == "install":
            public.set_module_logs(
                "sys_domain", "Install_aaPanelDns", 1
            )
        return public.success_v2(public.lang("Success!"))

    def get_status(self, get):
        config_obj = aaDnsConfig()
        service_name = config_obj.service_path.get("service_name")
        if not service_name:
            public.success_v2({
                "service": None,
                "status": False
            })
        a, e = public.ExecShell(f"ps -ef | grep '{service_name}' | grep -v grep")
        if e:
            raise HintException(f"Failed to get aaDNS service status: {e} please try again.")
        return public.success_v2({
            "service": config_obj.install_service,
            "status": True if a else False
        })

    def change_status(self, get):
        try:
            get.validate([
                Param("service_name").String("in", ["bind", "pdns"]),
                Param("status").String("in", [
                    "start", "stop", "restart", "reload"
                ]).Require(),
            ], [
                public.validate.trim_filter(),
            ])
        except Exception as ex:
            public.print_log("error info: {}".format(ex))
            return public.fail_v2(str(ex))
        if not hasattr(get, "service_name"):
            service_name = "pdns"
        else:
            service_name = get.service_name

        DnsManager().change_service_status(service_name, get.status)
        return public.success_v2(public.lang(f"Successfully {get.status} aaDNS service."))

    @staticmethod
    def check_base_params(func):
        def wrapper(self, get):
            check_domain = ["domain", "ns1domain", "ns2domain", "soa"]
            soa_params = ["nameserver", "admin_mail"]
            for key in check_domain + soa_params:
                if hasattr(get, key) and not DomainValid.is_valid_domain(getattr(get, key)):
                    raise HintException("invalid {}: {}".format(key, getattr(get, key)))
            # ip
            check_ip = ["ip", "domain_ip"]
            for key2 in check_ip:
                if hasattr(get, key2):
                    if not DomainValid.is_ip4(getattr(get, key2)) and not DomainValid.is_ip6(getattr(get, key2)):
                        raise HintException("invalid ip address: {}".format(getattr(get, key2)))
            # ttl, priority
            check_int_type = ["ttl", "priority"]
            soa_int_params = ["serial", "refresh", "retry", "expire", "minimum"]
            for key3 in check_int_type + soa_int_params:
                if hasattr(get, key3):
                    try:
                        int(getattr(get, key3))
                    except:
                        raise HintException("{} must be an digit.".format(key3))
            return func(self, get)

        return wrapper

    @staticmethod
    def init_provider(func):
        def wrapper(self, get):
            provider = DnsDomainProvider.objects.filter(name="aaPanelDns").first()
            if not provider:
                raise HintException(public.lang(
                    "aaPanelDns provider not found. Please install aaDNS first."
                ))
            return func(self, get, provider)

        return wrapper

    @check_base_params
    def add_zone(self, get):
        """添加zone信息"""
        try:
            get.validate([
                Param("domain").String().Require(),
                Param("ns1domain").String(),
                Param("ns2domain").String(),
                Param("soa").String(),
                Param("domain_ip").String(),
            ], [
                public.validate.trim_filter(),
            ])
        except Exception as ex:
            public.print_log("error info: {}".format(ex))
            return public.fail_v2(str(ex))

        manager = DnsManager()
        domain = get.domain.rstrip(".")  # 去点
        soa = "ns1.{}.".format(domain)
        ip = "127.0.0.1"
        ns1 = "ns1.{}.".format(domain)
        ns2 = "ns2.{}.".format(domain)

        if hasattr(get, "ns1") and get.ns1:
            ns1 = get.ns1
        if hasattr(get, "ns2") and get.ns2:
            ns2 = get.ns2
        if hasattr(get, "soa") and get.soa:
            soa = get.soa
        if hasattr(get, "domain_ip") and get.domain_ip:
            ip = get.domain_ip

        # 确保FQDN格式
        for k in [ns1, ns2, soa]:
            if not k.endswith("."):
                k += "."
        res = manager.add_zone(domain, ns1, ns2, soa, ip)
        if isinstance(res, str):
            return public.success_v2(res)
        return public.success_v2(public.lang("Successfully added zone."))

    @check_base_params
    def del_zone(self, get):
        try:
            get.validate([
                Param("domain").String().Require(),
            ], [
                public.validate.trim_filter(),
            ])
        except Exception as ex:
            public.print_log("error info: {}".format(ex))
            return public.fail_v2(str(ex))

        res = DnsManager().delete_zone(get.domain)
        if isinstance(res, str):
            return public.success_v2(res)
        return public.success_v2(public.lang("Successfully deleted zone."))

    @check_base_params
    def get_zones(self, get):
        """获取所有已添加的域名列表"""
        try:
            get.validate([
                Param("domain").String(),
            ], [
                public.validate.trim_filter(),
            ])
        except Exception as ex:
            public.print_log("error info: {}".format(ex))
            return public.fail_v2(str(ex))
        domains = DnsParser().get_zones(get.domain)
        return public.success_v2(domains)

    @check_base_params
    def get_nameserver(self, get):
        return public.success_v2(DnsManager().get_default_nameserver())

    @check_base_params
    def set_nameserver(self, get):
        try:
            get.validate([
                Param("ns1domain").String().Require(),
                Param("ns2domain").String().Require(),
            ], [
                public.validate.trim_filter(),
            ])
        except Exception as ex:
            public.print_log("error info: {}".format(ex))
            return public.fail_v2(str(ex))

        manager = DnsManager()
        manager.set_default_nameserver(get.ns1domain, get.ns2domain)
        return public.success_v2(public.lang("Successfully set nameserver."))

    @check_base_params
    def get_soa(self, get):
        try:
            get.validate([
                Param("domain").String().Require(),
            ], [
                public.validate.trim_filter(),
            ])
        except Exception as ex:
            public.print_log("error info: {}".format(ex))
            return public.fail_v2(str(ex))
        soa = DnsManager().get_soa(get.domain)
        return public.success_v2(soa)

    @check_base_params
    def set_soa(self, get):
        try:
            get.validate([
                Param("domain").String().Require(),
                Param("nameserver").String().Require(),
                Param("admin_mail").String().Require(),
                Param("serial").Integer().Require(),
                Param("refresh").Integer("between", [1200, 43200]).Require(),
                Param("retry").Integer("between", [120, 7200]).Require(),
                Param("expire").Integer("between", [1209600, 2419200]).Require(),
                Param("minimum").Integer("between", [180, 86400]).Require(),
            ], [
                public.validate.trim_filter(),
            ])
        except Exception as ex:
            public.print_log("error info: {}".format(ex))
            return public.fail_v2(str(ex))

        for k, v in get.__dict__.items():
            if k in ["domain", "nameserver", "admin_mail"]:
                if v.endswith("."):
                    setattr(get, k, v.rstrip("."))
        DnsManager().set_soa(**get.__dict__)
        return public.success_v2(public.lang("Successfully set SOA record."))

    def get_logger(self, get):
        try:
            get.validate([
                Param("p").Integer(),
                Param("limit").Integer(),
                Param("search").String(),
            ], [
                public.validate.trim_filter(),
            ])
        except Exception as ex:
            public.print_log("error info: {}".format(ex))
            return public.fail_v2(str(ex))
        if not hasattr(get, "p"):
            get.p = 1
        if not hasattr(get, "limit"):
            get.limit = 20
        if hasattr(get, "search") and get.search:
            search = str(get.search)
        else:
            search = None
        return public.success_v2(
            DnsManager().get_logger(int(get.p), int(get.limit), search)
        )

    def clear_logger(self, get):
        if DnsManager().clear_logger():
            return public.success_v2(public.lang("Successfully cleared logs."))
        return public.fail_v2(public.lang("Failed to clear logs."))

    @init_provider
    def add_dmarc(self, get, provider: DnsDomainProvider):
        try:
            get.validate([
                Param("policy").String("in", ["none", "quarantine", "reject"]).Require(),
            ], [
                public.validate.trim_filter(),
            ])
        except Exception as ex:
            public.print_log("error info: {}".format(ex))
            return public.fail_v2(str(ex))

        mail_manager = MailManager()
        fails = []
        for d in provider.domains:
            try:
                setattr(mail_manager, "domain", d)
                mail_manager.add_dmarc(policy=get.policy, provider=provider)
            except Exception as ex:
                public.print_log("error info: {}".format(ex))
                fails.append(f"domain: {d} error: {ex}")
                continue
        if fails:
            return public.fail_v2(", ".join(fails))
        return public.success_v2(public.lang("Successfully added DMARC record."))

    @init_provider
    def add_dkim_spf(self, get, provider: DnsDomainProvider):
        fails = []
        for d in provider.domains:
            try:
                MailManager(d).add_spf(provider)
                MailManager(d).add_dkim(provider)
            except Exception as ex:
                public.print_log("error info: {}".format(ex))
                fails.append(f"domain: {d} error: {ex}")
                continue
        if fails:
            return public.fail_v2(", ".join(fails))
        return public.success_v2(public.lang("Successfully added DKIM/SPF records."))

    @init_provider
    def dns_checker(self, get, provider: DnsDomainProvider):
        try:
            get.validate([
                Param("act").String("in", ["start", "status"]).Require(),
            ], [
                public.validate.trim_filter(),
            ])
        except Exception as ex:
            public.print_log("error info: {}".format(ex))
            return public.fail_v2(str(ex))

        status = 1 if os.path.exists(DNS_AUTH_LOCK) else 0
        if get.act == "status":
            if status:
                msg = public.lang("DNS Checker is Running. Please Wait.")
            else:
                msg = public.lang("DNS Checker is Suspend.")

        elif get.act == "start":
            if status:
                msg = public.lang("DNS Checker is Already Running. Please Wait.")
            else:
                task = threading.Thread(
                    target=DnsManager().builtin_dns_checker, args=(provider,)
                )
                task.start()
                status = 1
                msg = public.lang("DNS Checker Run Successfully.")
        else:
            raise HintException(public.lang("Invalid action."))

        return public.success_v2({
            "checker_status": status,
            "msg": msg
        })

    @check_base_params
    @init_provider
    def fix_zone(self, get, provider: DnsDomainProvider):
        manager = DnsManager()
        try:
            for i in provider.domains:
                manager.fix_zone(i)
        except Exception as ex:
            public.print_log("error info: {}".format(ex))
            return public.fail_v2(str(ex))
        return public.success_v2(public.lang("Successfully fixed all zones."))

    @check_base_params
    @init_provider
    def set_ttl_batch(self, get, provider: DnsDomainProvider):
        try:
            get.validate([
                Param("ttl").String().Require(),
                Param("domains").String().Require(),
                Param("record_type").String().Require(),
            ], [
                public.validate.trim_filter(),
            ])
            get.domains = json.loads(get.domains)
            if not get.record_type:
                raise HintException(public.lang("Record type is required."))
        except Exception as ex:
            public.print_log("error info: {}".format(ex))
            return public.fail_v2(str(ex))

        fails = []
        manager = DnsManager()
        for d in get.domains:
            if d not in provider.domains:
                fails.append(f"domain: {d} error: not found in provider domains.")
                continue
            try:
                if not manager.domian_record_type_ttl_batch_set(
                        domain=d, record_type=get.record_type, ttl=get.ttl
                ):
                    fails.append(f"domain: {d} error: failed to set ttl.")
            except Exception as ex:
                public.print_log("error info: {}".format(ex))
                fails.append(f"domain: {d} error: {ex}")
                continue
        if fails:
            return public.fail_v2(", ".join(fails))
        return public.success_v2(public.lang("Successfully set TTL for all domains."))
