# coding: utf-8
# -------------------------------------------------------------------
# aaPanel
# -------------------------------------------------------------------
# Copyright (c) 2014-2099 aaPanel(www.aapanel.com) All rights reserved.
# -------------------------------------------------------------------
# Author: aapanel
# -------------------------------------------------------------------

import os
import re
from typing import Optional

import public
from .conf import *


class DnsParser:
    def __init__(self):
        self.config = aaDnsConfig()

    # ======================= bind ===============================
    def _parser_bind_config(self, conf: str) -> dict:
        """解析bind主配置"""
        if not conf:
            return {}
        conf = re.sub(r'//.*', '', conf)
        conf = re.sub(r'#.*', '', conf)
        conf = re.sub(r'/\*[\s\S]*?\*/', '', conf)
        # 匹配 directory, listen-on, listen-on-v6, allow-query
        pattern = re.compile(
            r'\s*(directory|listen-on|listen-on-v6|allow-query)\s+(\{[\s\S]*?}|"[^"]*"|[^;]+?)\s*;',
            re.MULTILINE
        )

        matches = pattern.findall(conf)
        main_config = dict()
        for key, value in matches:
            # 清理值，去除多余的空格和引号
            cleaned_value = value.strip()
            if cleaned_value.startswith('"') and cleaned_value.endswith('"'):
                cleaned_value = cleaned_value[1:-1]
            elif cleaned_value.startswith('{') and cleaned_value.endswith('}'):
                # 对于块值，进一步清理内部内容
                cleaned_value = cleaned_value[1:-1].strip()
                cleaned_value = re.sub(r'\s+', ' ', cleaned_value)

            # 如果键已存在，则将值附加到列表中
            if key in main_config:
                if isinstance(main_config[key], list):
                    main_config[key].append(cleaned_value)
                else:
                    main_config[key] = [main_config[key], cleaned_value]
            else:
                main_config[key] = cleaned_value

        return main_config

    # ======================= pdns ================================
    def _parser_pdns_config(self, conf: str):
        """解析pdns主配置"""
        if not conf:
            return {}
        main_config = {}
        for line in conf.splitlines():
            line = line.strip()
            if line and not line.startswith("#"):
                parts = line.split("=", 1)
                if len(parts) == 2:
                    key = parts[0].strip()
                    value = parts[1].strip()
                    main_config[key] = value
        return main_config

    # ======================= public method =======================
    @staticmethod
    def ttl_parse(value: str) -> Optional[int]:
        try:
            return int(value.split()[1])
        except (ValueError, IndexError):
            return None

    @staticmethod
    def soa_parse(value: str) -> dict:
        try:
            value = re.sub(r';.*', '', value)
            soa_parts = value.split()
            if len(soa_parts) >= 7:
                parsed_value = {
                    "nameserver": soa_parts[0],
                    "admin_mail": soa_parts[1],
                    "serial": int(soa_parts[2]),
                    "refresh": int(soa_parts[3]),
                    "retry": int(soa_parts[4]),
                    "expire": int(soa_parts[5]),
                    "minimum": int(soa_parts[6])
                }
                return parsed_value
        except (ValueError, IndexError):
            return {}
        return {}

    @staticmethod
    def handle_multiline_soa(lines: list, i: int, current_line: str) -> tuple[str, int]:
        """处理多行SOA记录"""
        soa_lines = [current_line.replace("(", " ")]
        while i < len(lines):
            next_line = lines[i].strip()
            i += 1
            if not next_line:
                continue
            next_line = next_line.split(';', 1)[0].strip()  # 移除注释
            if not next_line:
                continue
            soa_lines.append(next_line)
            if ")" in next_line:
                break
        line = " ".join(soa_lines).replace(")", " ")
        return line, i

    def _parse_record(self, line: str, default_ttl: Optional[int]) -> Optional[dict]:
        """解析单条DNS记录"""
        match = record_pattern.match(line)
        if not match:
            return None

        name, ttl, r_class, r_type, value = match.groups()
        if r_type.upper() == "TXT":
            value = value.strip()
            if not (value.startswith('"') and value.endswith('"')):
                # 对于没有引号的 TXT 记录或其它记录，移除注释
                value = value.split(';', 1)[0].strip()
        else:
            # 对于非 TXT 记录，保持原有的注释移除逻辑
            value = value.split(';', 1)[0].strip()

        record = {
            "name": name,
            "ttl": int(ttl) if ttl is not None else default_ttl,
            "class": r_class or "IN",
            "type": r_type,
            "value": value,
        }

        if r_type.upper() == "SOA":  # 解析特殊字段
            record.update(self.soa_parse(value))
        elif r_type.upper() == "MX":
            try:
                priority, mx_value = value.split(None, 1)
                record["priority"] = int(priority)
                record["value"] = mx_value
            except (ValueError, IndexError):
                pass
        elif r_type.upper() == "SRV":
            try:
                priority, weight, port, target = value.split(None, 3)
                record["priority"] = int(priority)
                record["weight"] = int(weight)
                record["port"] = int(port)
                record["value"] = target
            except (ValueError, IndexError):
                pass
        return record

    def parser_zone_record(self, zone_file: str, witSOA: bool = False):
        """解析zone记录"""
        zone_content = public.readFile(zone_file) or ""
        if not zone_content:
            return
        default_ttl = None
        lines = zone_content.splitlines()
        i = 0
        while i < len(lines):
            line = lines[i].strip()
            i += 1
            if not line or line.startswith(";"):
                continue

            if line.startswith("$TTL"):
                default_ttl = self.ttl_parse(line)
                continue
            try:
                if "SOA" in line and line.rstrip().endswith("("):
                    line, i = self.handle_multiline_soa(lines, i, line)
            except Exception as e:
                public.print_log("Error handling multiline SOA: {}".format(e))
                continue

            record = self._parse_record(line, default_ttl)
            if not record:
                continue

            if not witSOA and record.get("type") == "SOA":
                continue
            elif witSOA and record.get("type") == "SOA":
                yield record
                return

            yield record

    def get_config(self, service_name: str = None) -> dict:
        """"获取服务的所有配置, 默认获取当前安装的服务配置"""
        config = {}
        service = service_name or self.config.install_service
        if service == "bind":
            nick_name = "bind"
            paths = self.config.bind_paths
            parser = self._parser_bind_config
        elif service == "pdns":
            nick_name = "pdns"
            paths = self.config.pdns_paths
            parser = self._parser_pdns_config
        else:
            return {}
        conf_path = paths["config"]
        if not os.path.exists(conf_path):
            return {}
        config["service_name"] = nick_name
        config["config"] = parser(public.readFile(conf_path))
        return config

    def get_zones(self, domain: str = None) -> list:
        """获取域名列表"""
        path = self.config.pdns_paths["zones"]
        if not os.path.exists(path):
            return []
        zones_content = public.readFile(path) or ""
        zone_matches = zone_pattern.findall(zones_content)
        domains = []
        for match in zone_matches:
            zone_declaration = match.strip()
            domain_match = re.search(r'zone\s+"([^"]+)"', zone_declaration)
            if domain_match:
                if domain and domain != domain_match.group(1):
                    continue
                domains.append(domain_match.group(1))
        return domains

    def get_zones_records(self, domain: str = None, witSOA: bool = False) -> list:
        """获取domain zones信息记录列表"""
        for root, dirs, files in os.walk(self.config.pdns_paths["zone_dir"]):
            files.sort()
            for file in files:
                try:
                    if file.startswith("db.") or file.endswith(".zone"):
                        temp_domain = re.sub(r'^(db\.|zone\.)', '', str(file))
                        temp_domain = re.sub(r'\.(db|zone)$', '', temp_domain)
                        if temp_domain != domain:
                            continue
                        zone_file_path = os.path.join(root, file)
                        res = list(
                            self.parser_zone_record(
                                zone_file=str(zone_file_path), witSOA=witSOA
                            )
                        )
                        return res
                except Exception as e:
                    public.print_log("Error parsing zone file {}: {}".format(file, e))
                    continue
        return []
