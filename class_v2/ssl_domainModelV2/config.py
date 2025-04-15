# coding:
import os
from enum import Enum, auto

import public
from panelDnsapi import CloudFlareDns, NameCheapDns

APP_PATH = "class_v2/ssl_domainModelV2"

RUNNING = os.path.join(public.get_panel_path(), APP_PATH, "sync_running.pl")

# 旧的, 限制域名面板登录
PANEL_LIMIT_DOMAIN = os.path.join(public.get_panel_path(), "data/domain.conf")

# 新的, real 面板域名
PANEL_DOMAIN = os.path.join(public.get_panel_path(), "data/panel_domain.conf")

DNS_MAP = {
    "CloudFlareDns": CloudFlareDns,
    "NameCheapDns": NameCheapDns,
}


class DnsTask(Enum):
    """
    任务名字, 可用于具体过滤
    """
    sync_dns = "Sync Dns"
    apply_ssl = "Apply SSL"

    init_sites = "Site Initialize"
    init_panel = "Panel SSL Initialize"


class UseFor(Enum):
    sites = "sites"
    panel = "panel"
    mails = "mails"
    account = "account"


class WorkFor(Enum):
    sites = auto()
    panel = auto()
    mails = auto()
    account = auto()
