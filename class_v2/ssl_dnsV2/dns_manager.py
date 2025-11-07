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
import os
import sys
import time
from typing import Optional

sys.path.insert(0, '/www/server/panel/class_v2')
import public
from .helper import DnsParser
from .conf import ZONES, ZONES_DIR, record_pattern
from public.exceptions import HintException
from ssl_domainModelV2.service import DomainValid, SyncService
from ssl_domainModelV2.model import DnsDomainProvider

PANEL_PATH = public.get_panel_path()


def backup_file(path: str, suffix: str = None) -> None:
    """创建 pdns的备份文件"""
    if not os.path.exists(path):
        return
    if suffix is None:
        if path == ZONES:
            suffix = "bak"
        elif path.startswith(ZONES_DIR):
            suffix = "def"
        else:
            suffix = "bak"
    backup_path = f"{path}_{suffix}"
    public.ExecShell(f"cp -a {path} {backup_path}")


def pdns_rollback(path: str) -> None:
    """根据 pdns文件路径回滚自己得备份文件"""
    if path.startswith(ZONES_DIR):
        suffix = "def"
    else:
        suffix = "bak"
    backup_path = f"{path}_{suffix}"
    if os.path.exists(backup_path):
        public.ExecShell(f"cp -a {backup_path} {path}")


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
        ttl = str(kwargs.get("ttl", "600"))
        priority = str(kwargs.get("priority", "10"))
        r_type = "A" if ":" not in ip else "AAAA"
        serial = time.strftime("%Y%m%d", time.localtime()) + "01"

        template = f"""$TTL 86400
{domain}.      IN SOA  {soa}     admin.{domain}. (
                                        {serial}       ; serial
                                        7200      ; refresh
                                        3600      ; retry
                                        1209600      ; expire
                                        180 )    ; minimum
{domain}.            86400     IN      NS        {ns1}.
{domain}.            86400     IN      NS        {ns2}.
{domain}.            {ttl}     IN      {r_type}        {ip}
{domain}.            {ttl}     IN      MX {priority}      mail.{domain}.
{domain}.            {ttl}     IN      CAA        0 issue "letsencrypt.org"
www             {ttl}     IN      {r_type}        {ip}
mail            {ttl}     IN      {r_type}        {ip}
ns1             {ttl}     IN      {r_type}        {ip}
ns2             {ttl}     IN      {r_type}        {ip}
"""
        public.writeFile(os.path.join(ZONES_DIR, f"{domain}.zone"), template)
        return template


class DnsManager:
    def __init__(self):
        self.parser = DnsParser()
        self.config = self.parser.config
        if self.config.install_service in ["bind", "pdns"]:
            self.makesuer_port()

    def makesuer_port(self) -> None:
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
                public.print_log("add firewall port 53 error: {}".format(e))

    def validate_with_resolver(self, action: str, domain: str, **kwargs):
        # 本地校验dns记录
        if not action:
            return
        try:
            import dns.resolver
        except ImportError:
            public.print_log("dnspython not installed, skipping DNS validation.")
            return

        record_data = kwargs
        if action == "update" and "new_record" in kwargs:
            record_data = kwargs["new_record"]

        record_type = record_data.get("type", "A").upper()
        name = record_data.get("name", "@")
        if name == "@":
            q_name = domain
        elif name.endswith("."):
            q_name = name
        else:
            q_name = f"{name}.{domain}"

        resolver = dns.resolver.Resolver()
        resolver.nameservers = ["127.0.0.1"]
        try:
            time.sleep(1)
            answers = resolver.resolve(q_name, record_type, raise_on_no_answer=False)
            if action in ["create", "update"]:
                if answers.rrset is None:
                    raise HintException(
                        f"Validation failed: Record {q_name} ({record_type}) not found after {action}."
                    )
                return

            if action == "delete":
                if answers.rrset is not None:
                    value_to_delete = kwargs.get("value")
                    for item in answers:
                        if value_to_delete in str(item):
                            raise HintException(
                                f"Validation failed: Record {q_name} ({record_type}) still exists after deletion."
                            )
                return

        except dns.resolver.NXDOMAIN:
            # 域名不存在，对于删除是正常的，对于创建/更新是失败的
            if action in ["create", "update"]:
                raise HintException(f"Validation failed: Domain {q_name} not found after {action}.")
        except Exception as e:
            # 捕获其他DNS查询异常
            raise HintException(f"DNS validation failed for {q_name}: {e}")

    def __reload_bind(self):
        # 关闭pdns服务
        a, e = public.ExecShell(f"ps -ef|grep {self.config.pdns_paths['service_name']}|grep -v grep")
        if a:
            public.ExecShell(f"systemctl stop {self.config.pdns_paths['service_name']}")
        # 验证配置文件正确性
        check_cmd = f"named-checkconf {self.config.bind_paths['main']}"
        res, err = public.ExecShell(check_cmd)
        if err:
            return public.fail_v2("Reload failed error: {}".format(err))
        # 重启bind服务
        public.ExecShell(f"systemctl restart {self.config.bind_paths["service_name"]}")
        return public.success_v2(public.lang("Successfully!"))

    def __reload_pdns(self):
        # 关闭bind服务
        a, e = public.ExecShell(f"ps -ef|grep {self.config.bind_paths['service_name']}|grep -v grep")
        if a:
            public.ExecShell(f"systemctl stop {self.config.bind_paths['service_name']}")
        # 重启pdns服务
        a, e = public.ExecShell(f"systemctl restart {self.config.pdns_paths['service_name']}")
        if a:
            raise HintException("Reload failed error: {} DNS config maybe wrong".format(a))
        if e:
            raise HintException("Reload failed error: {}".format(e))

    def __name_checkconf(self):
        a, e = public.ExecShell(f"named-checkconf {ZONES}")
        if e:
            raise Exception(f"Configuration check failed zone block: {e}")

    def reload_service(self, service_name: str = "pdns") -> bool:
        if service_name == "pdns":
            self.__reload_pdns()
            return True
        elif service_name == "bind":
            self.__reload_bind()
            return True
        return False

    def add_zone(self, domain: str, ns1: str, ns2: str, soa: str, ip: str = "127.0.0.1"):
        if domain in self.parser.get_zones():
            raise HintException("Zone Already Exists!")

        zone_file = os.path.join(ZONES_DIR, f"{domain}.zone")
        backup_file(ZONES)  # 备份主配置文件
        try:
            Templater.generate_zone(domain)  # 追加zone 配置
            Templater.generate_record(domain, ns1, ns2, soa, ip)  # 生成zone区域文件
            self.__name_checkconf()
            self.reload_service()
        except Exception as e:
            pdns_rollback(ZONES)
            if os.path.exists(zone_file):
                try:
                    os.remove(zone_file)  # 移除异常的区域文件
                    os.remove(f"{zone_file}_def")  # 移除其备份
                except:
                    pass
            self.reload_service()
            raise HintException("Add zone failed error: {}".format(e))
        finally:
            # 同步DNS服务
            provider = DnsDomainProvider.objects.filter(name="aaPanelDns").first()
            if provider:
                SyncService(provider.id).process()

    def delete_zone(self, domain: str):
        if domain not in self.parser.get_zones():
            raise HintException("Domian Not Found!")
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
            self.__name_checkconf()
            try:
                os.remove(zone_file)
                os.remove(zone_file + "_def")
            except Exception as ex:
                public.print_log(f"Error removing zone file {zone_file}: {ex}")
            self.reload_service()
        except Exception as e:
            import traceback
            public.print_log(traceback.format_exc())
            pdns_rollback(ZONES)
            pdns_rollback(zone_file)
            self.reload_service()
            raise HintException("Delete zone failed error: {}".format(e))
        finally:
            # 同步DNS服务
            provider = DnsDomainProvider.objects.filter(name="aaPanelDns").first()
            if provider:
                SyncService(provider.id).process()

    def _update_soa_serial(self, lines: list) -> bool:
        """更新SOA序列号"""
        for i, line in enumerate(lines):
            if "IN SOA" in line:  # SOA 行开始
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
                            # SOA 序列号替换
                            lines[i + j] = soa_line.replace(serial_str, new_serial, 1)
                            return True
                break
        return False

    def _build_record_line(self, domain: str, **kwargs) -> str:
        """构建DNS记录行"""

        def _get_params(kwargs):
            name = kwargs.get("name", "@")
            ttl = kwargs.get("ttl", "600")
            ttl = "600" if int(ttl) == 1 else str(ttl)
            record_type = kwargs.get("type", "A").upper()
            value = kwargs.get("value")
            priority = kwargs.get("priority", -1),
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

        elif record_type in ["CNAME", "NS"] and not DomainValid.is_valid_domain(value):
            raise HintException(f"Invalid {record_type} record value: {value}")

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
            if " " in value and not (value.startswith('"') and value.endswith('"')):
                value = f'"{value}"'

        # === 参数追加尾部作为 整体value 写入 conf ===
        elif record_type == "SRV":
            priority = kwargs.get("priority", "10")
            weight = kwargs.get("weight", "5")
            port = kwargs.get("port")
            if not port:
                raise HintException("SRV record requires a 'port'.")
            if not all(str(p).isdigit() for p in [priority, weight, port]):
                raise HintException("SRV priority, weight, and port must be integers.")
            if not DomainValid.is_valid_domain(value):
                raise HintException(f"Invalid SRV target domain: {value}")
            value = f"{priority} {weight} {port} {value}"

        record_name = name
        if record_type == "MX":
            if not DomainValid.is_valid_domain(value):
                raise HintException(f"Invalid MX record value: {value}")
            # 如果value不是完全限定域名FQDN(不以.结尾)，则补充主域名
            if not value.endswith("."):
                value = f"{value}.{domain}."

            if record_name != "@" and not record_name.endswith("."):
                record_name = f"{record_name}.{domain}"
            # record_type = f"{record_type} {kwargs.get("priority", "10")}"
            value = f"{kwargs.get('priority', '10')} {value}"

        # 构造兼容旧格式
        return f"{record_name}\t{ttl}\tIN\t{record_type}\t{value}"

    def _find_record_line_index(self, action: str, lines: list, **kwargs) -> Optional[int]:
        """查找DNS记录行索引"""
        name = kwargs.get("name", "@")
        record_type = kwargs.get("type", "A").upper()
        value = kwargs.get("value")
        for i, line in enumerate(lines):
            match = record_pattern.match(line)
            if match:
                r_name, _, _, r_type, r_value = match.groups()
                r_value = r_value.split(';', 1)[0].strip()
                # todo 更多类型的特殊处理
                if r_type == "MX":
                    try:
                        _, r_value = r_value.split(None, 1)
                    except (ValueError, IndexError):
                        pass

                if action != "delete":
                    if r_name == name and r_type.upper() == record_type and r_value == value:
                        return i
                else:  # 删除操作暂时仅判断name 和 type
                    if r_name == name and r_type.upper() == record_type:
                        return i
        return None

    def _modify_record(self, domain: str, action: str, **kwargs) -> bool:
        # C, U, D
        if domain not in self.parser.get_zones():
            raise HintException("Domian Not Found!")
        zone_file = os.path.join(ZONES_DIR, f"{domain}.zone")
        if not os.path.exists(zone_file):
            raise HintException("Zone file not found!")
        # 开事务
        backup_file(zone_file)
        try:
            content = public.readFile(zone_file)
            # 移除末尾可能存在的空行
            lines = content.rstrip("\n").split("\n") if content else []
            # 更新SOA序列号
            if not self._update_soa_serial(lines):
                raise HintException("SOA record not found, cannot update serial number.")
            modify = False
            line_index = self._find_record_line_index(action, lines, **kwargs)

            if action.lower() == "create":
                if line_index is not None:
                    public.print_log("Record already exists, skipping creation.")
                    return True

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
            raise HintException(f"Record {action} failed and was rolled back: {e}")

    def add_record(self, domain: str, **kwargs) -> bool:
        self.__apply_and_validate_change("create", domain, **kwargs)
        return True

    def delete_record(self, domain: str, **kwargs) -> bool:
        self.__apply_and_validate_change("delete", domain, **kwargs)
        return True

    def update_record(self, domain: str, **kwargs) -> bool:
        if not kwargs.get("new_record"):
            raise HintException("update record is required for update operation.")
        self.__apply_and_validate_change("update", domain, **kwargs)
        return True

    def get_domains(self) -> list:
        return self.parser.get_zones() or []
