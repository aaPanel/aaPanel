# coding:
import os
from enum import StrEnum, IntEnum

import public
from panelDnsapi import *

APP_PATH = os.path.dirname(__file__)

# 旧的, 限制域名面板登录
PANEL_LIMIT_DOMAIN = os.path.join(public.get_panel_path(), "data/domain.conf")

# 新的, real 面板域名
PANEL_DOMAIN = os.path.join(public.get_panel_path(), "data/panel_domain.conf")

# 源任务脚本
ORG_TASK_PL = os.path.join(APP_PATH, "org_domain_ssl.pl")
# 同步更新锁
# RUNNING = os.path.join(APP_PATH, "sync_running.pl")
# 订单锁
MANUAL_APPLY_PL = os.path.join(APP_PATH, "manual_apply.pl")

# old dns配置迁移
OLD_DNS_CONF = os.path.join(public.get_panel_path(), "class_v2/ssl_dnsV2", "aaDns_conf.json")

DNS_MAP = {
    "CloudFlareDns": CloudFlareDns,
    "NameCheapDns": NameCheapDns,
    "PorkBunDns": PorkBunDns,
    "NameSiloDns": NameSiloDns,
    "aaPanelDns": aaPanelDns,
    "GodaddyDns": GodaddyDns,
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
