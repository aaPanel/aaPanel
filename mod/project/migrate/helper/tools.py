# coding: utf-8
# -------------------------------------------------------------------
# aaPanel
# -------------------------------------------------------------------
# Copyright (c) 2014-2099 aaPanel(www.aapanel.com) All rights reserved.
# -------------------------------------------------------------------
# Author: aapanel
# -------------------------------------------------------------------

# ------------------------------
# tools app
# ------------------------------
import uuid
import sys

if "/www/server/panel" not in sys.path:
    sys.path.insert(0, "/www/server/panel")
if "/www/server/panel/class" not in sys.path:
    sys.path.insert(0, "/www/server/panel/class")
if "/www/server/panel/class_v2" not in sys.path:
    sys.path.insert(0, "/www/server/panel/class_v2")

import public
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .logger import MigrateLogger


def inject_item_ids(detail: list) -> list:
    """为业务数据注入唯一 _id"""
    for user in detail:
        data = user.get("data", {})
        if not isinstance(data, dict):
            continue
        for val in data.values():
            if isinstance(val, list):
                for item in val:
                    if isinstance(item, dict) and not item.get("_id"):
                        item["_id"] = str(uuid.uuid4())[:12]
    return detail


def format_disk_size(size_kb: int | float) -> str:
    """将磁盘块数转换为人性化单位显示"""
    size = size_kb * 1024
    units = ['B', 'KB', 'MB', 'GB', 'TB', 'PB']
    for unit in units:
        if abs(size) < 1024.0:
            return f"{size:.2f} {unit}" if unit != 'B' else f"{int(size)} {unit}"
        size /= 1024.0
    return f"{size:.2f} EB"


def humanize_to_bytes(size_str: str) -> int:
    """将人性化单位转为字节数"""
    if not size_str:
        return 0

    size_str = str(size_str).strip().upper()

    # 纯数字, 默认 MB
    if size_str.isdigit():
        return int(size_str) * 1024 * 1024

    # 提取数字和单位
    import re
    m = re.match(r'^([\d.]+)([KMGTPE]?B?)$', size_str)
    if not m:
        return 0

    num = float(m.group(1))
    unit = m.group(2)

    units = {
        'B': 1,
        'K': 1024, 'KB': 1024,
        'M': 1024 ** 2, 'MB': 1024 ** 2,
        'G': 1024 ** 3, 'GB': 1024 ** 3,
        'T': 1024 ** 4, 'TB': 1024 ** 4,
        'P': 1024 ** 5, 'PB': 1024 ** 5,
        'E': 1024 ** 6, 'EB': 1024 ** 6,
    }

    return int(num * units.get(unit, 1024 ** 2))  # 默认 MB


def verify_dns_a_records(domains: set, logger: "MigrateLogger") -> None:
    """验证域名A记录指向"""
    if not domains:
        return

    local_ip = public.get_server_ip()
    from ssl_dnsV2.dns_manager import DnsManager
    dns_mgr = DnsManager(init=False)
    public_dns_servers = dns_mgr._get_glb_ns()
    prefix = ""
    logger.info("=" * 50, prefix=prefix)
    logger.info("DNS A Record Verification", prefix=prefix)
    logger.info("=" * 50, prefix=prefix)

    for domain in domains:
        a_records = None
        for _, addr_list in public_dns_servers:
            try:
                a_records = dns_mgr.query_dns(domain, 'A', ns_server=addr_list, time_out=5)
                break
            except Exception:
                continue

        if a_records is None:
            logger.info(f"[WARN] {domain} -> DNS query failed", prefix=prefix)
        elif local_ip in a_records:
            logger.info(f"[ OK ] {domain} -> {local_ip}", prefix=prefix)
        elif a_records:
            logger.info(f"[WARN] {domain} -> {', '.join(a_records)} (expected: {local_ip})", prefix=prefix)
        else:
            logger.info(f"[WARN] {domain} -> No A record", prefix=prefix)

    logger.info("=" * 50, prefix="")
