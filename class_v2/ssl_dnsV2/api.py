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

from public.exceptions import HintException
from public.validate import Param
from ssl_domainModelV2.service import DomainValid
from .dns_manager import DnsManager
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
        log = f"{public.get_panel_path()}/logs/install_pdns.log"
        if os.path.exists(log):
            public.ExecShell(f"rm -f {log}")
        install_script = os.path.join(
            os.path.dirname(os.path.abspath(__file__)), "pdns_script.sh"
        )
        public.ExecShell("chmod +x {}".format(install_script))
        public.ExecShell("nohup bash {} install >>{} 2>&1 &".format(install_script, log))
        return public.success_v2(public.lang("Installing..."))

    def get_status(self, get):
        config_obj = aaDnsConfig()
        service_name = config_obj.service_path.get("service_name")
        a = False
        if service_name:
            a, e = public.ExecShell(f"ps -ef | grep '{service_name}' | grep -v grep")
        return public.success_v2({
            "service": config_obj.install_service,
            "status": True if a else False
        })

    @staticmethod
    def check_base_params(func):
        def wrapper(self, get):
            # domain
            check_domain = ["domain", "ns1domain", "ns2domain", "soa"]
            for key in check_domain:
                if hasattr(get, key) and getattr(get, key) and not DomainValid.is_valid_domain(getattr(get, key)):
                    raise HintException("invalid {}: {}".format(key, getattr(get, key)))
            # ip
            check_ip = ["ip", "domain_ip"]
            for key2 in check_ip:
                if hasattr(get, key2) and getattr(get, key2):
                    if not DomainValid.is_ip4(getattr(get, key2)) and not DomainValid.is_ip6(getattr(get, key2)):
                        raise HintException("invalid ip address: {}".format(getattr(get, key2)))
            # ttl, priority
            check_int_type = ["ttl", "priority"]
            for key3 in check_int_type:
                if hasattr(get, key3) and getattr(get, key3):
                    try:
                        int(getattr(get, key3))
                    except:
                        raise HintException("{} must be an digit.".format(key3))
            return func(self, get)

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
        domain = get.domain
        ns1 = "ns1.{}".format(domain)
        ns2 = "ns2.{}".format(domain)
        soa = "ns1.{}".format(domain)
        ip = "127.0.0.1"

        if hasattr(get, "ns1") and get.ns1:
            ns1 = get.ns1
        if hasattr(get, "ns2") and get.ns2:
            ns2 = get.ns2
        if hasattr(get, "soa") and get.soa:
            soa = get.soa
        if hasattr(get, "domain_ip") and get.domain_ip:
            ip = get.domain_ip

        DnsManager().add_zone(domain, ns1, ns2, soa, ip)
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
        DnsManager().delete_zone(get.domain)
        return public.success_v2(public.lang("Successfully deleted zone."))

    # 不用
    @check_base_params
    def resolve_record(self, get):
        """操作解析记录"""
        try:
            get.validate([
                Param("domain").String().Require(),
                Param("act").String("in", ["create", "update", "delete"]).Require(),
                Param("type").String().Require(),
                Param("host").String().Require(),
                Param("ttl").String().Require(),
                Param("value").String().Require(),
                Param("priority").String(),
            ], [
                public.validate.trim_filter(),
            ])
        except Exception as ex:
            public.print_log("error info: {}".format(ex))
            return public.fail_v2(str(ex))

        kw = {
            "name": get.host,
            "type": get.type.upper(),
            "value": get.value,
            "ttl": get.ttl if hasattr(get, "ttl") and get.ttl else 600,
        }
        if hasattr(get, "priority") and get.priority:
            kw["priority"] = get.priority

        manager = DnsManager()
        if get.act == "create":
            manager.add_record(get.domain, **kw)
        elif get.act == "update":
            manager.update_record(get.domain, **kw)
        elif get.act == "delete":
            manager.delete_record(get.domain, **kw)

        return public.success_v2(public.lang("Successfully!"))

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

    # 不用
    def get_zones_records(self, get):
        """获取zones信息记录列表"""
        try:
            get.validate([
                Param("domain").String().Require(),
            ], [
                public.validate.trim_filter(),
            ])
        except Exception as ex:
            public.print_log("error info: {}".format(ex))
            return public.fail_v2(str(ex))
        domain = get.domain
        zone_dict_list = DnsParser().get_zones_records(domain=domain)
        return public.success_v2(zone_dict_list.get(domain, []))

    def restart_service(self, get):
        try:
            get.validate([
                Param("service_name").String("in", ["bind", "pdns"]),
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
        DnsManager().reload_service()
        return public.success_v2(public.lang("Successfully restarted aaDNS service."))

    def set_nameserver(self, get):
        ...

    def dns_logger(self, get):
        ...
