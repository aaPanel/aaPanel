# coding:
import os
from enum import StrEnum, IntEnum

import public
from panelDnsapi import *

APP_PATH = "class_v2/ssl_domainModelV2"

RUNNING = os.path.join(public.get_panel_path(), APP_PATH, "sync_running.pl")

# 旧的, 限制域名面板登录
PANEL_LIMIT_DOMAIN = os.path.join(public.get_panel_path(), "data/domain.conf")

# 新的, real 面板域名
PANEL_DOMAIN = os.path.join(public.get_panel_path(), "data/panel_domain.conf")

DNS_MAP = {
    "CloudFlareDns": CloudFlareDns,
    "NameCheapDns": NameCheapDns,
    "PorkBunDns": PorkBunDns,
    "NameSiloDns": NameSiloDns,
}


class DnsTask(StrEnum):
    """
    任务名字, 可用于具体过滤
    """
    sync_dns = "Sync Dns"
    apply_ssl = "Apply SSL"

    init_sites = "Site Initialize"
    init_panel = "Panel SSL Initialize"


class UserFor(StrEnum):
    sites = "sites"
    panel = "panel"
    mails = "mails"
    account = "account"


class WorkFor(IntEnum):
    sites = 1
    panel = 2
    mails = 3
    account = 4
