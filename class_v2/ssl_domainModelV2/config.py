# coding:
from enum import Enum

from panelDnsapi import CloudFlareDns, NameCheapDns

DNS_MAP = {
    "CloudFlareDns": CloudFlareDns,
    "NameCheapDns": NameCheapDns,
}


class DnsTask(Enum):
    sync_dns = "Sync Dns"
    apply_ssl = "Apply SSL"


class UseFor(Enum):
    sites = "sites"
    panel = "panel"
    mails = "mails"
