# coding: utf-8
# -------------------------------------------------------------------
# aaPanel
# -------------------------------------------------------------------
# Copyright (c) 2014-2099 aaPanel(www.aapanel.com) All rights reserved.
# -------------------------------------------------------------------
# Author: aapanel
# -------------------------------------------------------------------

# ------------------------------
# parser app
# ------------------------------
# 解析获取信息

import re

import public

def split_combined_cert(combined_content: str) -> dict:
    """分离combined中的 cert 和 key
    Args:
        combined_content
    Returns:
        dict: {'key': 私钥, 'cert': 证书}
    """
    # 私钥
    key_match = re.search(
        r'-----BEGIN(?: RSA)? PRIVATE KEY-----.*?-----END(?: RSA)? PRIVATE KEY-----',
        combined_content,
        re.DOTALL
    )
    # 证书链
    cert_matches = re.findall(
        r'-----BEGIN CERTIFICATE-----.*?-----END CERTIFICATE-----',
        combined_content,
        re.DOTALL
    )
    return {
        'key': key_match.group(0) if key_match else '',
        'cert': '\n'.join(cert_matches) if cert_matches else ''
    }


def parse_combined_ssl(combined_content: str) -> dict:
    """简单验证解析ssl"""
    if not combined_content or not isinstance(combined_content, str):
        return {}
    split_result = split_combined_cert(combined_content)
    if not split_result['key'] or not split_result['cert']:
        return {}
    import ssl_info
    return ssl_info.ssl_info().load_ssl_info_by_data(combined_content)


def parse_user_domains(content: str) -> dict:
    """
    content:
    *: nobody
    limit-mycpanel.pppcat.top: limitmycpanelppp
    mycpanel-no2.pppcat.top: mycpanelno2pppca
    mycpanel.pppcat.top: mycpanel
    mycpanel2.mycpanel.pppcat.top: mycpanel
    wpt.mycpanel.pppcat.top: mycpanel
    return: {user: [domains...]}
    """
    domain_user_map = {}
    if not content:
        return domain_user_map
    for line in content.splitlines():
        try:
            if not line or ":" not in line:
                continue
            parts = line.strip().split(":", 1)
            if len(parts) < 2:
                continue
            domain = parts[0].strip().lower()
            user = parts[1].strip()
            if domain and user and domain.startswith("*"):
                continue
            if not domain_user_map.get(user):
                domain_user_map[user] = [domain]
            else:
                domain_user_map[user].append(domain)
        except Exception:
            import traceback
            public.print_log(traceback.format_exc())
            continue
    return domain_user_map


def parse_wp_config(content: str) -> dict:
    """解析wp-config.php中的数据库信息"""
    try:
        result = {}
        patterns = {
            "DB_NAME": r"define\s*\(\s*['\"]DB_NAME['\"]\s*,\s*['\"]([^'\"]+)['\"]",
            "DB_USER": r"define\s*\(\s*['\"]DB_USER['\"]\s*,\s*['\"]([^'\"]+)['\"]",
            "DB_PASSWORD": r"define\s*\(\s*['\"]DB_PASSWORD['\"]\s*,\s*['\"]([^'\"]+)['\"]",
        }

        for key, pattern in patterns.items():
            m = re.search(pattern, content)
            if m:
                result[key] = m.group(1)
        # 表前缀
        m = re.search(r"\$table_prefix\s*=\s*['\"]([^'\"]+)['\"]", content)
        result["prefix"] = m.group(1) if m else "wp_"
        return result if len(result) >= 3 else {}
    except:
        return {}


def cpanel_cfg_parser(cpanel_userdata_content):
    """
    解析 cPanel 用户数据文件内容 (例如 /var/cpanel/userdata/<user>/main)
    提取域名、文档根目录等信息
    """
    data = {}
    lines = cpanel_userdata_content.splitlines()
    for line in lines:
        line = line.strip()
        if not line or line.startswith('#'):
            continue
        if ':' in line:
            key, val = line.split(':', 1)
            data[key.strip()] = val.strip()
    return data


def parse_cpanel_domain_info(cpanel_userdata_domain_content):
    """
    解析 /var/cpanel/userdata/<user>/<domain> 文件
    """
    return cpanel_cfg_parser(cpanel_userdata_domain_content)


def wp_htaccess_parser(htaccess_content):
    pass
