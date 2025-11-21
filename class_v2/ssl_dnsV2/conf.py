# coding: utf-8
# -------------------------------------------------------------------
# aaPanel
# -------------------------------------------------------------------
# Copyright (c) 2014-2099 aaPanel(www.aapanel.com) All rights reserved.
# -------------------------------------------------------------------
# Author: aapanel
# -------------------------------------------------------------------
# aaDNS config
# ------------------------------
import json

import os
import re
import sys

if not "class_v2" in sys.path:
    sys.path.append("class_v2")

__all__ = [
    "aaDnsConfig",
    "zone_pattern",
    "file_pattern",
    "record_pattern",
    "ZONES_DIR",
    "ZONES",
    "APP_DIR",
    "SERVICE_INSTALL_NAME",
    "PUBLIC_SERVER",
    "DNS_AUTH_LOCK",
    "aaDNS_CONF",
]

zone_pattern = re.compile(r'zone\s+"[^"]+"\s*(?:IN)?\s*\{[\s\S]*?};', re.MULTILINE)
file_pattern = re.compile(r'file\s+"([^"]+)"')
record_pattern = re.compile(r'^(\S+)\s+(?:(\d+)\s+)?(?:(IN)\s+)?(\S+)\s+(.*)$')

ZONES_DIR = "/var/named/chroot/var/named/"
ZONES = "/var/named/chroot/etc/named.rfc1912.zones"

APP_DIR = os.path.dirname(os.path.abspath(__file__))
SERVICE_INSTALL_NAME = f"{APP_DIR}/aadns.pl"
aaDNS_CONF = os.path.join(APP_DIR, "aaDns_conf.json")
DNS_AUTH_LOCK = f"{APP_DIR}/dns_auth.pl"

PUBLIC_SERVER = [
    ("Google", ["8.8.8.8"]),
    ("Cloudflare", ["1.1.1.1"]),
    ("Quad9", ["9.9.9.9"]),
    ("OpenDNS", ["208.67.222.222"]),
    ("DNS.Watch", ["84.200.69.80"]),
    ("Comodo Secure DNS", ["8.26.56.26"]),
    ("AdGuard DNS", ["94.140.14.14"]),
    ("CleanBrowsing", ["185.228.168.9"]),
    ("Neustar DNS", ["207.177.68.4"]),
    ("Freenom World", ["83.145.86.7"]),
]



class aaDnsConfig:
    if os.path.exists("/etc/redhat-release"):
        os_type = "redhat"
        package = "yum"
    else:
        os_type = "ubuntu"
        package = "apt"

    def __init__(self):
        self.install_service = None
        self.ns_server = None
        self.bind_service_name = "named"
        self.pnds_service_name = "pdns"
        self._init_env()

    def _init_env(self):
        # RHEL/CentOS，检查 bind-chroot 服务具体名称
        if os.path.exists("/usr/lib/systemd/system/named-chroot.service"):
            self.bind_service_name = "named-chroot"

        if os.path.exists(SERVICE_INSTALL_NAME):
            with open(SERVICE_INSTALL_NAME, "r") as f:
                self.install_service = f.read().strip()
            if self.install_service not in ["bind", "pdns"]:
                try:
                    os.remove(SERVICE_INSTALL_NAME)
                except:
                    pass
                self.install_service = None

        if os.path.exists(aaDNS_CONF):
            try:
                with open(aaDNS_CONF, "r") as f:
                    content = f.read().strip()
                    self.ns_server = json.loads(content) if content else None
            except:
                pass

    @property
    def pdns_paths(self):
        if self.os_type == "ubuntu":  # debian
            return {
                "config": "/etc/powerdns/pdns.conf",
                "zones": ZONES,
                "zone_dir": ZONES_DIR,
                "service_name": self.pnds_service_name,
                "package_name": "pdns-server",
            }
        else:  # redhat, centos
            return {
                "config": "/etc/pdns/pdns.conf",
                "zones": ZONES,
                "zone_dir": ZONES_DIR,
                "service_name": self.pnds_service_name,
                "package_name": "bind-chroot" if self.os_type == "redhat" else "bind9",
                "main": "/var/named/chroot/etc/named.conf",
            }

    @property
    def bind_paths(self):
        return {
            "config": "/var/named/chroot/etc/named.conf",
            "zones": "/var/named/chroot/etc/named.conf.local",
            "zone_dir": ZONES_DIR,
            "service_name": self.bind_service_name,
            "package_name": "bind-chroot" if self.os_type == "redhat" else "bind9",
            "main": "/var/named/chroot/etc/named.conf",
        }

    @property
    def service_path(self):
        if self.install_service == "bind":
            return self.bind_paths
        elif self.install_service == "pdns":
            return self.pdns_paths
        else:
            return {}
