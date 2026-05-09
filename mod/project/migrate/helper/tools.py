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
