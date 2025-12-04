# coding: utf-8
# -------------------------------------------------------------------
# aaPanel
# -------------------------------------------------------------------
# Copyright (c) 2014-2099 aaPanel(www.aapanel.com) All rights reserved.
# -------------------------------------------------------------------
# Author: aapanel
# -------------------------------------------------------------------
# ------------------------------
# aaDNS app
# ------------------------------
import json
import os
import random
import sys
import time
from dataclasses import dataclass, fields
from functools import wraps
from typing import Optional, Type, TypeVar, List

sys.path.insert(0, '/www/server/panel/class')
sys.path.insert(0, '/www/server/panel/class_v2')
import public
from public.hook_import import hook_import

hook_import()
try:
    from BTPanel import cache
except:
    pass
from ssl_dnsV2.model import DnsResolve
from ssl_dnsV2.helper import DnsParser
from ssl_dnsV2.conf import *
from public.exceptions import HintException
from ssl_domainModelV2.service import DomainValid, SyncService
from ssl_domainModelV2.model import DnsDomainProvider, dns_logger

PANEL_PATH = public.get_panel_path()

S = TypeVar("S", bound="Soa")

TIMEOUT = 1  # 用于验证ns超时


def backup_file(path: str, suffix: str = None) -> None:
    """创建 pdns的备份文件"""
    if not os.path.exists(path):
        return
    if suffix is None:
        if path == ZONES:
            suffix = "aabak"  # 主配置
        elif path.startswith(ZONES_DIR):
            suffix = "aadef"  # 区域文件
        else:
            suffix = "bak"
    backup_path = f"{path}_{suffix}"
    public.ExecShell(f"cp -a {path} {backup_path}")


def pdns_rollback(path: str) -> None:
    """根据 pdns文件路径回滚自己得备份文件"""
    if path.startswith(ZONES_DIR):
        suffix = "aadef"
    else:
        suffix = "aabak"
    backup_path = f"{path}_{suffix}"
    if os.path.exists(backup_path):
        public.ExecShell(f"cp -a {backup_path} {path}")


def clean_record_cache(func):
    # 对记录操作后强清缓存
    @wraps(func)
    def wrapper(self, *args, **kwargs):
        result = func(self, *args, **kwargs)
        try:
            domain = kwargs.get("domain")
            if not domain and args:
                domain = args[0]
            if domain and self.aapanel_dns_obj and cache:
                key = f"aaDomain_{self.aapanel_dns_obj.id}_{domain}"
                cache.delete(key)
        except Exception:
            pass
        return result

    return wrapper


@dataclass(slots=True)
class Soa:
    domain: str
    nameserver: str
    admin_mail: str
    refresh: int
    retry: int
    expire: int
    minimum: int

    @classmethod
    def from_dict(cls: Type[S], data: dict) -> S:
        class_fields = {f.name for f in fields(cls)}
        filtered_data = {k: v for k, v in data.items() if k in class_fields}
        return cls(**filtered_data)


class Templater:
    @staticmethod
    def generate_zone(domain: str) -> str:
        template = """
zone "%s" IN {
        type master;
        file "/var/named/chroot/var/named/%s.zone";
        allow-update { none; };
};
""" % (domain, domain)
        public.writeFile(ZONES, template, "a+")
        return template

    @staticmethod
    def generate_record(domain: str, ns1: str, ns2: str, soa: str, ip: str, **kwargs) -> str:
        # 确保FQDN格式
        for k in [ns1, ns2, soa]:
            if not k.endswith("."):
                k += "."
        ttl = str(kwargs.get("ttl", "14400"))
        priority = str(kwargs.get("priority", "10"))
        r_type = "A" if ":" not in ip else "AAAA"
        serial = time.strftime("%Y%m%d", time.localtime()) + "01"

        template = f"""$TTL 86400
{domain}.      IN SOA  {soa}     admin.{domain}. (
                                        {serial}       ; serial
                                        3600      ; refresh
                                        1800      ; retry
                                        1209600      ; expire
                                        1800 )    ; minimum
{domain}.            86400     IN      NS        {ns1}
{domain}.            86400     IN      NS        {ns2}
{domain}.            {ttl}     IN      {r_type}        {ip}
{domain}.            {ttl}     IN      MX {priority}      mail.{domain}.
www             {ttl}     IN      {r_type}        {ip}
mail            {ttl}     IN      {r_type}        {ip}
ns1             {ttl}     IN      {r_type}        {ip}
ns2             {ttl}     IN      {r_type}        {ip}
"""
        public.writeFile(os.path.join(ZONES_DIR, f"{domain}.zone"), template)
        return template


class MailManager:
    def __init__(self, domain: str = None):
        self.domain = domain
        self.dns_manager = DnsManager()

    def _get_provider(self, provider: DnsDomainProvider = None) -> DnsDomainProvider:
        if not provider:
            provider = self.dns_manager.aapanel_dns_obj
            if provider:
                return provider
            raise HintException("DNS provider 'aaPanelDns' not found.")
        return provider

    def _get_records(self) -> list:
        return self.dns_manager.parser.get_zones_records(self.domain)

    def __append_spf_record(self, spf_record: dict, new_spf_ip: str) -> None:
        parts = spf_record["value"].strip('"').split()
        all_index = -1
        for i, part in enumerate(parts):
            if part.endswith("all"):
                all_index = i
                break
        if all_index != -1:
            parts.insert(all_index, f"+{new_spf_ip}")
        else:
            parts.append(f"+{new_spf_ip}")

        new_spf_value = " ".join(parts)
        self.dns_manager.update_record(
            domain=self.domain,
            name=spf_record["name"],
            type="TXT",
            value=spf_record["value"],
            new_record={
                "name": spf_record["name"],
                "type": "TXT",
                "ttl": spf_record["ttl"],
                "value": f'"{new_spf_value}"',
            }
        )

    def add_dmarc(self, policy: str = "none", provider: DnsDomainProvider = None, **kwargs) -> bool:
        """
        添加 DMARC 记录
        DMARC 策略 "none" (接受) "quarantine" (隔离) 或 "reject" (拒绝)
        """
        if policy not in ["none", "quarantine", "reject"]:
            raise HintException("Invalid DMARC policy specified.")

        for record in self._get_records():
            if record.get("name") == "_dmarc" and record.get("type") == "TXT":
                dns_logger(f"domain [{self.domain}] has DMARC record, skipping addition.")
                return True

        dmarc_value = f'"v=DMARC1; p={policy}; rua=mailto:admin@{self.domain}"'
        body = {
            "domain": self.domain,
            "record": "_dmarc",
            "record_type": "TXT",
            "record_value": dmarc_value,
            "ttl": kwargs.get("ttl", 600),
            "ps": "Auto DMARC Record",
        }
        self._get_provider(provider).model_create_dns_record(body)
        return True

    def add_spf(self, provider: DnsDomainProvider = None, **kwargs) -> bool:
        records = self._get_records()
        server_ip = public.GetLocalIp()
        new_spf_ip = f"ip4:{server_ip}" if DomainValid.is_ip4(server_ip) else f"ip6:{server_ip}"
        spf_record = None
        for record in records:
            if all([
                record.get("type") == "TXT",
                record.get("name") == "@" or record.get("name") == self.domain,
                record.get("value", "").startswith("v=spf1") or record.get("value", "").startswith('"v=spf1'),
            ]):
                if spf_record is not None:
                    dns_logger(
                        f"domain [{self.domain}] has multiple SPF records, it will auto fix it,"
                        f" keep the first one."
                    )
                    # 多个spf记录异常
                    self.dns_manager.delete_record(
                        domain=self.domain, name=record["name"], type="TXT", value=record["value"]
                    )
                else:
                    spf_record = record
        # 存在spf
        if spf_record:
            if new_spf_ip not in spf_record.get("value", ""):
                self.__append_spf_record(spf_record, new_spf_ip)
                dns_logger(
                    f"domain [{self.domain}] SPF record updated to include server IP: [{server_ip}]."
                    f"Current SPF: {spf_record.get('value', '')}"
                )
                return True
            else:
                dns_logger(f"domain [{self.domain}] has SPF record with server IP, skipping addition.")
                return True
        # 不存在SPF记录
        body = {
            "domain": self.domain,
            "record": "@",
            "record_type": "TXT",
            "record_value": f"v=spf1 +mx +a +{new_spf_ip} -all",
            "ttl": kwargs.get("ttl", 600),
            "ps": "Auto SPF Record",
        }
        self._get_provider(provider).model_create_dns_record(body)

        return True

    def add_dkim(self, provider: DnsDomainProvider = None, **kwargs) -> bool:
        dkim_name = "default._domainkey"
        records = self._get_records()
        for record in records:
            if record.get("name") == dkim_name and record.get("type") == "TXT":
                dns_logger(f"domain [{self.domain}] has DKIM record, skipping addition.")
                return True
        try:
            plugin_path = "/www/server/panel/plugin/mail_sys"
            if os.path.exists(plugin_path) and plugin_path not in sys.path:
                sys.path.insert(0, plugin_path)
            from plugin.mail_sys.mail_sys_main import mail_sys_main
            dkim_value = mail_sys_main()._get_dkim_value(self.domain)
            if dkim_value == "":
                mail_sys_main().set_rspamd_dkim_key(self.domain)
                dkim_value = mail_sys_main()._get_dkim_value(self.domain)
        except ImportError:
            dns_logger(f"domain [{self.domain}] Mail System Plugin ImportError, not installed...")
            raise HintException("Mail System Plugin ImportError, not installed.")
        except Exception:
            dns_logger(f"domain [{self.domain}] Failed to retrieve DKIM value from mail system.")
            raise HintException("Failed to retrieve DKIM value from mail system.")

        if not dkim_value:
            dns_logger(f"domain [{self.domain}] DKIM value is empty, cannot add record.")
            raise HintException("DKIM value is empty, cannot add record.")

        body = {
            "domain": self.domain,
            "record": dkim_name,
            "record_type": "TXT",
            "record_value": f'"{dkim_value}"',
            "ttl": kwargs.get("ttl", 600),
            "ps": "Auto SPF Record",
        }
        self._get_provider(provider).model_create_dns_record(body)
        return True


class DnsManager:
    def __init__(self):
        self.parser = DnsParser()
        self.config = self.parser.config

    @property
    def aapanel_dns_obj(self) -> Optional[DnsDomainProvider]:
        return DnsDomainProvider.objects.filter(name="aaPanelDns").first()

    def _quotes(self, s: str) -> bool:
        if not s or not isinstance(s, str):
            return False
        if s.startswith('"') and s.endswith('"'):
            return True
        return False

    def _get_glb_ns(self) -> List[tuple]:
        """获取公共NS服务器, 打乱"""
        shuffled_servers = [x for x in PUBLIC_SERVER]
        random.shuffle(shuffled_servers)
        return shuffled_servers

    def makesuer_port(self) -> None:
        try:
            if not public.S("firewall_new").where(
                    "ports = ? AND protocol = ?", ("53", "tcp/udp")
            ).count():
                try:
                    from firewallModelV2.comModel import main as firewall_main
                    get = public.dict_obj()
                    get.protocol = "all"
                    get.port = "53"
                    get.choose = "all"
                    get.types = "accept"
                    get.strategy = "accept"
                    get.chain = "INPUT"
                    get.brief = "DNS Service Port"
                    get.operation = "add"
                    firewall_main().set_port_rule(get)
                except Exception as e:
                    dns_logger("Add Firewall Port 53 Error: {}".format(e))
                    public.print_log("add firewall port 53 error: {}".format(e))
        except Exception:
            try:
                from firewalld_v2 import firewalld
                firewalld().AddAcceptPort(53, "tcp")
            except Exception:
                pass

    def query_dns(self, q_name: str, record_type: str, ns_server: Optional[list] = None, time_out: int = None) -> list:
        """
        DNS查询
        :param q_name: 要查询的名称
        :param record_type: 记录类型
        :param ns_server: 要使用的DNS服务器列表。如果为None，则使用系统默认
        :param time_out: 超时 s
        :return: 记录值字符串的列表
        :raises: HintException 如果查询失败
        """
        try:
            import dns.resolver
        except ImportError:
            dns_logger("dnspython ImportError, not installed...")
            public.ExecShell("btpip install dnspython")
            public.print_log("dnspython not installed, skipping DNS query.")
            return []

        resolver = dns.resolver.Resolver()
        if time_out:
            resolver.timeout = time_out
            resolver.lifetime = time_out
        if ns_server:
            resolver.nameservers = ns_server
        time.sleep(0.5)

        try:
            answers = resolver.resolve(q_name, record_type)
            found_records = []
            for rdata in answers:
                record_str = str(rdata)
                # 格式化
                if record_type in ["TXT", "CAA"] and self._quotes(record_str):
                    record_str = record_str[1:-1]
                elif record_type == "MX":
                    # rdata.to_text() -> '10 mail.example.com.'
                    parts = record_str.split(" ", 1)
                    if len(parts) == 2:
                        record_str = parts[1]
                elif record_type == "SRV":
                    # rdata.to_text() -> '10 5 5060 target.example.com.'
                    parts = record_str.split(" ", 3)
                    if len(parts) == 4:
                        record_str = " ".join(parts)

                found_records.append(record_str.rstrip('.'))
            return found_records
        except (dns.resolver.Timeout, dns.resolver.LifetimeTimeout):
            raise HintException(f"DNS query for {q_name} ({record_type}) timed out.")
        except (dns.resolver.NoAnswer, dns.resolver.NXDOMAIN, dns.resolver.NoNameservers):
            # 没有找到记录
            return []
        except Exception as e:
            raise HintException(f"DNS query for {q_name} ({record_type}) failed: {e}")

    def validate_with_resolver(self, action: str, domain: str, **kwargs) -> bool:
        # 本地校验dns记录
        if not action:
            return False
        record_data = kwargs
        if action == "update" and "new_record" in kwargs:
            record_data = kwargs["new_record"]

        record_type = record_data.get("type", "A").upper()
        name = record_data.get("name", "@")
        value_to_check = record_data.get("value")

        if name == "@" or name == domain:
            q_name = f"{domain}."
        elif name.endswith("."):
            q_name = name
        else:
            q_name = f"{name}.{domain}"
        found_records = self.query_dns(
            q_name=q_name, record_type=record_type, ns_server=["127.0.0.1"]
        )
        time.sleep(1)
        if not found_records:
            if action in ["create", "update"]:  # 对于创建||更新，是失败的
                raise HintException(
                    f"Validation failed: Record {q_name} ({record_type}) not found after {action}."
                )
            if action == "delete":  # 对于删除，是成功的
                return True

        # 被花括号包围时去引号, 去尾点
        value_to_check_cleaned = value_to_check
        if self._quotes(value_to_check):
            value_to_check_cleaned = value_to_check[1:-1]
        value_to_check_cleaned = value_to_check_cleaned.rstrip(".")

        if action in ["create", "update"]:
            if value_to_check_cleaned not in found_records:
                raise HintException(
                    f"Validation failed: Record {q_name} ({record_type})"
                    f" with value '{value_to_check}' not found after {action}."
                )
            return True

        if action == "delete":
            # 宽松检查, 保持删除
            return True
            # if value_to_check_cleaned in found_records:
                # raise HintException(
                #     f"Validation failed: Record {q_name} ({record_type})"
                #     f" with value '{value_to_check}' still exists after delete."
                # )
            # return True

        return False

    def _validate_NS_A(self, ns_list: List[str], time_out: int = None) -> bool:
        """备用尝试直接验证A记录方法: 直接查询ns1和ns2的A记录"""
        time_out = int(time_out) if time_out else TIMEOUT
        server_ip = public.GetLocalIp()
        try:
            for n in ns_list:
                ns_ip = self.query_dns(
                    q_name=n, record_type="A", time_out=time_out
                )
                if server_ip not in ns_ip:
                    return False
            return True
        except Exception as e:
            public.print_log(f"Warning: DNS query to NS A record failed: {e}.")
            return False

    def _validate_NS(self, domain: str, ns_list: List[str], addr_list: list, time_out: int = None) -> bool:
        try:
            time_out = int(time_out) if time_out else TIMEOUT
            found_ns = self.query_dns(
                q_name=domain, record_type="NS", ns_server=addr_list, time_out=time_out
            )
            if found_ns:
                ns_set = {ns.rstrip(".").lower() for ns in found_ns}
                # 是否子集
                if set(ns_list).issubset(ns_set):
                    return True
            return False
        except Exception:
            # public.print_log(f"Warning: DNS query to NS record failed: {e}.")
            return False

    def _validate_any_ns_msg(self, domain: str, ns_list: List[str], serv_name: str, addr_list: list) -> Optional[str]:
        """单次验证域名的权威"""
        # NS 阶段
        if self._validate_NS(domain, ns_list, addr_list):
            return (f"Validate NameServer Success: NS records are correctly set. "
                    f"Found in Global Public DNS '{serv_name}' {addr_list}")

        # public.print_log(
        #     f"Warning: NS for {domain} are Not Found! "
        #     f"which do not match provided [{', '.join(ns_list)}]. Proceeding to fallback validation."
        # )

        # fallback 尝试直接解析NS主机的A记录
        if self._validate_NS_A(ns_list):
            return (
                f"Validate NameServer Success: NS A records point to server IP."
                f"Found in Global Public DNS '{serv_name}' {addr_list}"
            )

        return None

    def _any_ns_hit(self, domain: str, ns_list: List[str]) -> str:
        """
        any one策略
        验证域名的权威NS记录。
        1. 优先查询域名的权威NS记录是否已在公网指向ns1/ns2。
        2. 如果查询失败或不匹配（例如新域名、未设置胶水记录），则回退到备用验证。
        3. 备用验证：直接查询ns1和ns2的A记录，看它们是否指向本机IP。
        成功返回str, 失败抛异常。
        """
        ns_list = [x.rstrip(".").lower() for x in ns_list if x]
        for server_name, addr_list in self._get_glb_ns():
            try:
                any_tips = self._validate_any_ns_msg(
                    domain, ns_list, server_name, addr_list
                )
                # 返回成功信息tips
                if any_tips and isinstance(any_tips, str):
                    body = {
                        "ns_resolve": 0,
                        "a_resolve": 0,
                        "tips": any_tips,
                    }
                    if "NS records" in any_tips:
                        body["ns_resolve"] = 1
                        body["a_resolve"] = 0

                    elif "NS A records" in any_tips:
                        body["ns_resolve"] = 0
                        body["a_resolve"] = 1
                    DnsResolve.update_or_create(domain, **body)
                    return any_tips
                else:
                    continue
            except Exception as e:
                public.print_log(e)

        # for loop end, all failed
        raise HintException("Validate NameServer Failed: NS records are not correctly set.")

    def __read_zone_lines(self, zone_file: str) -> list:
        """读取zone文件返回行列表"""
        content = public.readFile(zone_file) or ""
        if not content:
            raise HintException(f"Zone file [{zone_file}] is empty.")
        # 移除末尾可能存在的空行
        lines = content.rstrip("\n").split("\n") if content else []
        if not lines:
            raise HintException(f"Zone file [{zone_file}] is empty.")
        return lines

    def _update_soa(self, lines: list, soa_obj: Optional[Soa] = None) -> bool:
        """更新SOA 必然更新序列号, 如果带了 soa_obj 参数必须全提供"""
        serial_update = False
        other_update = True if soa_obj is not None else False

        ns_admin_mail_changed = False
        refresh_changed = False
        retry_changed = False
        expire_changed = False
        minimum_changed = False

        for i, line in enumerate(lines):
            if "IN SOA" in line:  # SOA 行开始
                # ns 和 admin mail
                if soa_obj and soa_obj.nameserver and soa_obj.admin_mail:
                    new_soa_line = (
                        f"{soa_obj.domain}.      IN SOA  "
                        f"{soa_obj.nameserver}.     "
                        f"{soa_obj.admin_mail}. ("
                    )
                    lines[i] = new_soa_line
                    ns_admin_mail_changed = True
                # 剩余参数
                go_on = lines[i:]
                for j, soa_line in enumerate(go_on):
                    # '; serial' 注释结尾, (看模板)
                    if ";" in soa_line and "serial" in soa_line:
                        serial_str = soa_line.split(';')[0].strip()
                        if serial_str.isdigit():
                            today_prefix = time.strftime("%Y%m%d", time.localtime())
                            if serial_str.startswith(today_prefix):
                                new_serial = str(int(serial_str) + 1)
                            else:
                                new_serial = today_prefix + "01"
                            # SOA 序列号变更
                            lines[i + j] = soa_line.replace(serial_str, new_serial, 1)
                            serial_update = True

                    elif "; refresh" in soa_line and soa_obj and soa_obj.refresh:
                        lines[i + j] = (f"                                        "
                                        f"{soa_obj.refresh}      ; refresh")
                        refresh_changed = True

                    elif "; retry" in soa_line and soa_obj and soa_obj.retry:
                        lines[i + j] = (f"                                        "
                                        f"{soa_obj.retry}      ; retry")
                        retry_changed = True

                    elif "; expire" in soa_line and soa_obj and soa_obj.expire:
                        lines[i + j] = (f"                                        "
                                        f"{soa_obj.expire}      ; expire")
                        expire_changed = True

                    elif "; minimum" in soa_line and soa_obj and soa_obj.minimum:
                        lines[i + j] = (f"                                        "
                                        f"{soa_obj.minimum} )    ; minimum")
                        minimum_changed = True

                break

        if other_update:
            if not (ns_admin_mail_changed and refresh_changed and retry_changed
                    and expire_changed and minimum_changed):
                return False

        if serial_update:
            return True

        return False

    def _build_record_line(self, domain: str, **kwargs) -> str:
        """构建DNS记录行"""

        def _get_params(kw: dict):
            name = kw.get("name", "@")
            ttl = kw.get("ttl", "600")
            ttl = "600" if int(ttl) == 1 else str(ttl)
            record_type = kw.get("type", "A").upper()
            value = kw.get("value")
            priority = kw.get("priority", -1)
            if not value:
                raise HintException("value is required!")
            return name, record_type, ttl, value, priority

        name, record_type, ttl, value, priority = _get_params(kwargs)
        if "new_record" in kwargs:
            name, record_type, ttl, value, priority = _get_params(kwargs["new_record"])
        # === 仅校验 ===
        if record_type == "A" and not DomainValid.is_ip4(value):
            raise HintException(f"Invalid A record value: {value}")

        elif record_type == "AAAA" and not DomainValid.is_ip6(value):
            raise HintException(f"Invalid AAAA record value: {value}")


        elif record_type in ["CNAME", "NS"]:
            if not DomainValid.is_valid_domain(value):
                raise HintException(f"Invalid {record_type} record value: {value}")
            # 完全限定域名FQDN
            if not value.endswith("."):
                value = f"{value}."

        elif record_type == "CAA":
            parts = value.split(None, 2)
            if len(parts) != 3:
                raise HintException(f"Invalid CAA record format: {value}")
            flags, tag, ca_value = parts
            if not flags.isdigit() or not (0 <= int(flags) <= 255):
                raise HintException(f"Invalid CAA flags: {flags}. Must be 0-255.")
            if tag not in ["issue", "issuewild", "iodef"]:
                raise HintException(f"Invalid CAA tag: {tag}. Must be 'issue', 'issuewild', or 'iodef'.")
            ca_value = ca_value.strip('"')
            if tag == "iodef":
                if not (ca_value.startswith("mailto:") or DomainValid.is_valid_domain(ca_value)):
                    raise HintException(f"Invalid CAA iodef value: {ca_value}")
            elif not DomainValid.is_valid_domain(ca_value):
                raise HintException(f"Invalid CAA domain value: {ca_value}")

        elif record_type == "TXT":
            # TXT 记录值如果包含空格，使用引号包裹
            if " " in value and not self._quotes(value):
                value = f'"{value}"'

        # === 参数追加尾部作为 整体value 写入 conf ===
        elif record_type == "SRV":
            weight = kwargs.get("weight", "5")
            port = kwargs.get("port")
            if not port:
                raise HintException("SRV record requires a 'port'.")
            if not all(str(p).isdigit() for p in [priority, weight, port]):
                raise HintException("SRV priority, weight, and port must be integers.")
            if not DomainValid.is_valid_domain(value):
                raise HintException(f"Invalid SRV target domain: {value}")
            value = f"{priority} {weight} {port} {value}"

        if record_type == "MX":
            if not DomainValid.is_valid_domain(value):
                raise HintException(f"Invalid MX record value: {value}")
            # 如果value不是完全限定域名FQDN(不以.结尾)，则补充点
            if not value.endswith("."):
                value = f"{value}."
            value = f"{priority} {value}"

        # 最后格式化 FQDN
        record_name = name
        if record_type in ["A", "AAAA"]:
            if record_name == "@" or record_name == domain:
                record_name = f"{domain}."
            # 其他情况保持原样，不转换为FQDN
        else:
            # 其他记录类型强制保持FQDN格式
            if record_name == "@" or record_name == domain:
                record_name = f"{domain}."
            elif not record_name.endswith("."):
                record_name = f"{record_name}.{domain}."
        # 构造兼容旧格式
        return f"{record_name}\t{ttl}\tIN\t{record_type}\t{value}"

    def _find_record_line_index(self, lines: list, **kwargs) -> Optional[int]:
        """查找DNS记录行索引"""
        name = kwargs.get("name", "@")
        record_type = kwargs.get("type", "A").upper()
        value = kwargs.get("value")

        # 剥离引号
        if record_type in ["TXT", "CAA"] and value and self._quotes(value):
            value = value[1:-1]

        for i, line in enumerate(lines):
            match = record_pattern.match(line)
            if match:
                r_name, _, _, r_type, r_value_raw = match.groups()
                r_type = r_type.upper()
                r_value = r_value_raw.strip()
                if r_type in ["TXT", "CAA"]:
                    if self._quotes(r_value):
                        r_value = r_value[1:-1]  # 剥离引号
                    else:  # 如果没有引号，可能存在的注释
                        r_value = r_value.split(';', 1)[0].strip()

                elif r_type == "MX":
                    # MX格式 "优先级 目标主机"
                    try:
                        r_value = r_value.split(";", 1)[0].strip()
                        r_value_clean = r_value.split(";", 1)[0].strip()
                        _, r_value = r_value_clean.split(None, 1)
                    except Exception:
                        import traceback
                        public.print_log(f"find record error: {traceback.format_exc()}")

                if r_name == name and r_type.upper() == record_type and r_value == value:
                    return i
        return None

    def _modify_record(self, domain: str, action: str, **kwargs) -> bool:
        # C, U, D
        zone_file = os.path.join(ZONES_DIR, f"{domain}.zone")
        if not os.path.exists(zone_file):
            raise HintException("Zone file not found!")
        # 开事务
        backup_file(zone_file)
        try:
            lines = self.__read_zone_lines(zone_file)
            # 更新SOA序列号
            if not self._update_soa(lines):
                raise HintException("SOA record not found, cannot update serial number.")
            modify = False
            line_index = self._find_record_line_index(lines, **kwargs)
            if action.lower() == "create":
                if line_index is not None:
                    raise HintException("Record already exists, skipping creation.")

                new_record_line = self._build_record_line(domain, **kwargs)
                lines.append(new_record_line)
                modify = True

            elif action.lower() in ["update", "delete"]:
                if line_index is None:
                    raise HintException("Record not found!")

                if action.lower() == "delete":
                    lines.pop(line_index)
                    modify = True
                elif action.lower() == "update":
                    updated_line = self._build_record_line(domain, **kwargs)
                    lines[line_index] = updated_line
                    modify = True

            if modify:
                public.writeFile(zone_file, "\n".join(lines) + "\n")
                return True

            return False
        except Exception as e:
            pdns_rollback(zone_file)
            import traceback
            public.print_log(traceback.format_exc())
            raise HintException(e)

    def __apply_and_validate_change(self, action: str, domain: str, **kwargs) -> None:
        """配置变动和验证管理"""
        zone_file = os.path.join(ZONES_DIR, f"{domain}.zone")
        try:
            if domain not in self.parser.get_zones():
                raise HintException("Domian Not Found!")
            if not self._modify_record(domain, action, **kwargs):
                return
            self.reload_service()
            self.validate_with_resolver(action, domain, **kwargs)
            # 校验后对区域文件进行备份稳定版本
            backup_file(zone_file)
        except Exception as e:
            import traceback
            public.print_log(traceback.format_exc())
            pdns_rollback(zone_file)
            self.reload_service()
            raise HintException(f"Record {action} failed: {e}")

    # ================= script ====================

    def _generate_auth_body(self, domain: str, ns_res: list, a_res: list, shuffled_servers: list) -> dict:
        body = {
            "domain": domain,
            "ns_resolve": 0,
            "a_resolve": 0,
            "tips": "",
        }
        if not shuffled_servers:
            return body

        ns_rate = len(ns_res) / len(shuffled_servers)
        a_rate = len(a_res) / len(shuffled_servers)
        threshold = 0.3
        ns_ok = ns_rate >= threshold
        a_ok = a_rate >= threshold
        body["ns_resolve"] = 1 if ns_ok else 0
        body["a_resolve"] = 1 if a_ok else 0

        tips_parts = []
        # 前缀
        if ns_ok and a_ok:
            tips_parts.append("Validate NameServer Success: ")
        else:
            tips_parts.append("Validate NameServer Failed: ")
        # NS
        if ns_ok:
            tips_parts.append("NS records are correctly set.")
        else:
            tips_parts.append("NS records are not correctly set.")
        # A
        if a_ok:
            tips_parts.append("NS A records point to server IP.")
        else:
            tips_parts.append("NS A records do not point to server IP.")

        body["tips"] = " ".join(tips_parts)
        return body

    def builtin_dns_checker(self, dns_obj: Optional[DnsDomainProvider] = None) -> None:
        """验证域名的权威NS记录, 用于任务"""
        obj = self.aapanel_dns_obj if not dns_obj else dns_obj
        if os.path.exists(DNS_AUTH_LOCK) or not obj or obj.status == 0 or len(obj.domains) == 0:
            return
        with open(DNS_AUTH_LOCK, "w") as f:
            f.write("0")
        try:
            SyncService(obj.id).process(nohup=True)
            for domain in obj.domains:
                try:
                    ns_list = [
                        x.get("value", "").rstrip(".").lower() for x in self.parser.get_zones_records(domain)
                        if x.get("type", "").upper() == "NS"
                    ]
                    shuffled_servers = self._get_glb_ns()
                    ns_res = []
                    a_res = []
                    for server_name, addr_list in shuffled_servers:
                        try:
                            if self._validate_NS(domain, ns_list, addr_list, time_out=5):
                                ns_res.append(server_name)
                            if self._validate_NS_A(ns_list, time_out=5):
                                a_res.append(server_name)
                        except Exception:
                            continue

                    body = self._generate_auth_body(
                        domain, ns_res, a_res, shuffled_servers
                    )
                    DnsResolve.update_or_create(**body)
                    dns_logger(f"domain [{domain}] dns auth : {body.get('tips', 'Msg Not Found')}")
                except Exception as e:
                    public.print_log(f"builtin_dns_auth error : {e}")
                    continue
        except Exception as e:
            public.print_log(f"builtin_dns_auth outer error : {e}")
        finally:
            public.ExecShell(f"rm -f {DNS_AUTH_LOCK}")

    # ================= public ====================

    def change_service_status(self, service_name: str = "pdns", status: str = "restart") -> bool:
        if service_name == "pdns":
            service_packname = self.config.pdns_paths['service_name']
        elif service_name == "bind":
            service_packname = self.config.bind_paths['service_name']
        else:
            raise HintException("Unsupported service!")

        if status not in ["stop", "restart", "reload", "start"]:
            raise HintException("Invalid action specified!")

        if status != "stop":
            status = "restart"
            self.makesuer_port()
            if service_name == "pdns":  # bind 互斥
                stop_name = self.config.bind_paths['service_name']
            else:  # pdns 互斥
                stop_name = self.config.pdns_paths['service_name']
            a0, e0 = public.ExecShell(f"ps -ef|grep {stop_name}|grep -v grep")
            if a0:  # 关闭互斥服务
                public.ExecShell(f"systemctl stop {stop_name}")

        _, e = public.ExecShell(f"systemctl {status} {service_packname}")
        if e:
            raise HintException(f"{status} {service_name} service failed error: {e}")
        # 变更账号状态
        provider = self.aapanel_dns_obj
        if provider:
            status_map = {"restart": 1, "stop": 0}
            provider.status = status_map[status]
            provider.save()
        return True

    def reload_service(self, service_name: str = "pdns") -> bool:
        return self.change_service_status(service_name, "reload")

    def add_zone(self, domain: str, ns1: str, ns2: str, soa: str, ip: str = "127.0.0.1") -> Optional[str]:
        domain = domain.strip().rstrip(".")
        if domain in self.parser.get_zones():
            dns_logger(f"Add Zone Failed: zone [{domain}] Already Exists")
            raise HintException("Zone Already Exists!")

        # 权威解析
        try:
            # add zone 会更新创建首次解析记录
            ns_res_msg = str(self._any_ns_hit(domain, [ns1, ns2]))
        except HintException as he:
            ns_res_msg = f"\nHowever, {str(he)}"
            DnsResolve.update_or_create(domain, **{"ns_resolve": 0, "a_resolve": 0, "tips": ns_res_msg})
        except Exception as e:
            ns_res_msg = (f"\nHowever, An error occurred during NS validation: {e}."
                          f" Your DNS Resolution May Not be Active in the internet.")
            DnsResolve.update_or_create(domain, **{"ns_resolve": 0, "a_resolve": 0, "tips": ns_res_msg})

        zone_file = os.path.join(ZONES_DIR, f"{domain}.zone")
        backup_file(ZONES)  # 备份主配置文件
        try:
            Templater.generate_zone(domain)  # 追加zone 配置
            Templater.generate_record(domain, ns1, ns2, soa, ip)  # 生成zone区域文件
            self.reload_service()
            result_msg = f"Zone [{domain}] Added Successfully. "
            if ns_res_msg and isinstance(ns_res_msg, str):
                result_msg += ns_res_msg
            dns_logger(result_msg)
            return result_msg
        except Exception as e:
            pdns_rollback(ZONES)
            if os.path.exists(zone_file):
                try:
                    os.remove(zone_file)  # 移除异常的区域文件
                    os.remove(f"{zone_file}_aadef")  # 移除其备份
                except:
                    pass
            self.reload_service()
            dns_logger(f"Add Zone Failed: {e}")
            if isinstance(e, HintException):
                raise e
            raise HintException("Add Zone Failed Error: {}".format(e))
        finally:
            # 同步DNS服务
            provider = self.aapanel_dns_obj
            if provider:
                sync = SyncService(provider.id)
                sync.force = True
                sync.sync_dns_domains()

    def delete_zone(self, domain: str) -> Optional[str]:
        zone_file = os.path.join(ZONES_DIR, f"{domain}.zone")
        # 备份主配置文件和区域文件
        backup_file(ZONES)
        backup_file(zone_file)
        try:
            zones_content = public.readFile(ZONES) or ""
            lines = zones_content.splitlines()
            new_lines: list = []
            in_block_to_delete = False
            brace_count = 0
            for line in lines:
                stripped_line = line.strip()
                if stripped_line.startswith(f'zone "{domain}"'):
                    in_block_to_delete = True
                if in_block_to_delete:  # 配对大括号
                    brace_count += line.count("{")
                    brace_count -= line.count("}")
                    if brace_count <= 0:
                        in_block_to_delete = False
                    continue
                # 只保留一个换行
                if not stripped_line and new_lines and not new_lines[-1].strip():
                    continue
                new_lines.append(line)

            # 只保留一个换行
            while new_lines and not new_lines[-1].strip():
                new_lines.pop()
            final_content = "\n".join(new_lines)
            if final_content:
                final_content += "\n"

            public.writeFile(ZONES, final_content)
            try:
                os.remove(zone_file)
                os.remove(zone_file + "_aadef")
            except Exception as ex:
                public.print_log(f"Error removing zone file {zone_file}: {ex}")
            self.reload_service()
            msg = f"Zone [{domain}] Deleted Successfully."
            dns_logger(msg)
            DnsResolve.objects.filter(domain=domain).delete()
            return msg
        except Exception as e:
            import traceback
            public.print_log(traceback.format_exc())
            pdns_rollback(ZONES)
            pdns_rollback(zone_file)
            self.reload_service()
            dns_logger(f"Delete Zone Failed: {e}")
            raise HintException("Delete zone failed error: {}".format(e))
        finally:
            # 同步DNS服务
            provider = self.aapanel_dns_obj
            if provider:
                sync = SyncService(provider.id)
                sync.force = True
                sync.sync_dns_domains()

    @clean_record_cache
    def add_record(self, domain: str, **kwargs) -> bool:
        self.__apply_and_validate_change("create", domain, **kwargs)
        return True

    @clean_record_cache
    def delete_record(self, domain: str, **kwargs) -> bool:
        self.__apply_and_validate_change("delete", domain, **kwargs)
        return True

    @clean_record_cache
    def update_record(self, domain: str, **kwargs) -> bool:
        if not kwargs.get("new_record"):
            raise HintException("update record is required for update operation.")
        self.__apply_and_validate_change("update", domain, **kwargs)
        return True

    def get_domains(self) -> list:
        return self.parser.get_zones() or []

    def get_default_nameserver(self) -> dict:
        try:
            if os.path.exists(aaDNS_CONF):
                ns = public.readFile(aaDNS_CONF)
                return json.loads(ns) if ns else {}
            return {}
        except Exception as e:
            public.print_log("Error reading nameserver config: {}".format(e))
            return {}

    def set_default_nameserver(self, n1: str, n2: str) -> bool:
        for k in [n1, n2]:
            if not k.endswith("."):
                k += "."
        default = {"NS1": n1, "NS2": n2}
        self.config.ns_server = default
        public.writeFile(aaDNS_CONF, json.dumps(default))
        dns_logger("Default Nameserver Set To: {}".format(default))
        return True

    def get_soa(self, domain: str) -> dict:
        if not domain:
            return {}
        for record in self.parser.get_zones_records(domain=domain, witSOA=True):
            if record.get("type") == "SOA":
                return {
                    "nameserver": record.get("nameserver"),
                    "admin_mail": record.get("admin_mail"),
                    "serial": record.get("serial"),
                    "refresh": record.get("refresh"),
                    "retry": record.get("retry"),
                    "expire": record.get("expire"),
                    "minimum": record.get("minimum"),
                }
        return {}

    def set_soa(self, **kwargs) -> bool:
        soa_obj = Soa.from_dict(kwargs)
        zone_file = os.path.join(ZONES_DIR, f"{soa_obj.domain}.zone")
        if not os.path.exists(zone_file):
            raise HintException(f"Zone file for domain '{soa_obj.domain}' not found!")
        backup_file(zone_file)
        try:
            lines = self.__read_zone_lines(zone_file)
            # 更新整个SOA
            if not self._update_soa(lines, soa_obj):
                raise HintException("SOA record not found, cannot update serial number.")
            public.writeFile(zone_file, "\n".join(lines) + "\n")
        except Exception as e:
            pdns_rollback(zone_file)
            import traceback
            public.print_log(traceback.format_exc())
            raise HintException(f"Set Soa Failed: {e}")
        return True

    def get_logger(self, p: int = 1, limit: int = 20, search: str = None) -> dict:
        if search is None:
            sql = ("type = ?", ("DnsSSLManager",))
            count = public.S("logs").where(*sql).count()
        else:
            sql = ("type = ? AND log LIKE ?", ("DnsSSLManager", f"%{search}%"))
            count = public.S("logs").where(*sql).count()
        logs = public.S("logs").where(*sql).order("id", "DESC").limit(limit, (p - 1) * limit).field(
            "log, addtime"
        ).select()
        length = 150

        if logs and isinstance(logs, list):
            for log_entry in logs:
                if "log" in log_entry and len(log_entry["log"]) > length:
                    original_log = log_entry["log"]
                    chunks = [original_log[i:i + length] for i in range(0, len(original_log), length)]
                    log_entry["log"] = "\n".join(chunks)

        return {"data": logs or [], "count": count or 0}

    def clear_logger(self) -> bool:
        public.S("logs").where("type = ?", ("DnsSSLManager",)).delete()
        return True

    @clean_record_cache
    def fix_zone(self, domain: str) -> str:
        # 记录去重修复
        domain = domain.strip().rstrip(".")
        if domain not in self.parser.get_zones():
            dns_logger(f"Fix Zone Failed: zone [{domain}] Not Found!")
            raise HintException("Zone Not Found!")

        zone_file = os.path.join(ZONES_DIR, f"{domain}.zone")
        if not os.path.exists(zone_file):
            raise HintException("Zone file not found!")

        # 备份
        backup_file(zone_file)
        try:
            lines = self.__read_zone_lines(zone_file)
            org_lines_counts = len(lines)
            soa_lines = []
            record_lines = []
            soa_block = False
            find_block = 0
            # SOA块
            for line in lines:
                if "IN SOA" in line:
                    soa_block = True
                if soa_block:
                    soa_lines.append(line)
                    find_block += line.count("(")
                    find_block -= line.count(")")
                    if find_block <= 0:
                        soa_block = False
                elif line.strip() and not line.strip().startswith(('$', ';')):
                    record_lines.append(line)
            # 去重
            cleaned_records = []
            seen_records = set()
            spf_record_found = False  # spf 修复
            for line in record_lines:
                match = record_pattern.match(line)
                if match:
                    # (name, type, value) 唯一标识
                    r_name, _, _, r_type, r_value_raw = match.groups()
                    r_type = r_type.upper()
                    r_value = r_value_raw.strip().split(";", 1)[0].strip()

                    # spf 唯一性处理
                    is_spf = (
                            r_type == "TXT" and
                            (r_value.startswith('"v=spf1') or r_value.startswith('v=spf1'))
                    )
                    if is_spf:
                        # 首次次标记
                        if not spf_record_found:
                            spf_record_found = True
                        else:  # 后续丢弃
                            dns_logger(f"Fix Zone [{domain}]: Removed duplicate SPF record: {line.strip()}")
                            continue

                    record_tuple = (r_name.lower(), r_type, r_value.lower())
                    if record_tuple not in seen_records:
                        seen_records.add(record_tuple)
                        cleaned_records.append(line)
                    else:
                        dns_logger(f"Fix Zone [{domain}]: Removed duplicate record: {line.strip()}")

            if len(cleaned_records) + len(soa_lines) == org_lines_counts:
                msg = f"Zone [{domain}] is already clean. No changes made."
                dns_logger(msg)
                return msg

            # 更新
            new_lines = soa_lines + cleaned_records
            if not self._update_soa(new_lines):
                raise HintException("Failed to update SOA serial number.")

            public.writeFile(zone_file, "\n".join(new_lines) + "\n")
            self.reload_service()
            backup_file(zone_file)
            msg = f"Zone [{domain}] has been fixed successfully."
            dns_logger(msg)
            return msg
        except Exception as e:
            pdns_rollback(zone_file)
            import traceback
            public.print_log(traceback.format_exc())
            raise HintException(f"Fix Zone Failed: {e}")

    @clean_record_cache
    def domian_record_type_ttl_batch_set(self, domain: str, record_type: str, ttl: int) -> bool:
        # 批量设置单个域名的指定类型TTL
        zone_file = os.path.join(ZONES_DIR, f"{domain}.zone")
        if not os.path.exists(zone_file):
            return False
        backup_file(zone_file)
        try:
            lines = self.__read_zone_lines(zone_file)
            if not lines:
                return False
            # 批量更新
            updated = False
            for i, line in enumerate(lines):
                match = record_pattern.match(line)
                if match:
                    r_name, _, _, r_type, r_value_raw = match.groups()
                    r_type = r_type.upper()
                    public.print_log(f"r_name={r_name}, r_type={r_type}, r_value_raw={r_value_raw}")
                    if r_type == record_type.upper():
                        parts = line.split()
                        public.print_log(f"parts = {parts}")
                        if len(parts) >= 4:
                            parts[1] = str(ttl)  # 更新TTL
                            lines[i] = "\t".join(parts)
                            updated = True
            if not updated:
                return True
            # 更新SOA序列号
            if not self._update_soa(lines):
                raise HintException("Failed to update SOA serial number.")

            public.writeFile(zone_file, "\n".join(lines) + "\n")
            self.reload_service()
            backup_file(zone_file)
            return True
        except Exception as e:
            pdns_rollback(zone_file)
            import traceback
            public.print_log(traceback.format_exc())
            raise HintException(f"Set TTL Batch Failed: {e}")


if __name__ == '__main__':
    DnsManager().builtin_dns_checker()
