# coding: utf-8
# -------------------------------------------------------------------
# aaPanel
# -------------------------------------------------------------------
# Copyright (c) 2014-2099 aaPanel(www.aapanel.com) All rights reserved.
# -------------------------------------------------------------------
# Author: aapanel
# -------------------------------------------------------------------

# ------------------------------
# aaDNS config
# ------------------------------
import os
import re

__all__ = [
    "aaDnsConfig",
    "zone_pattern",
    "file_pattern",
    "record_pattern",
    "ZONES_DIR",
    "ZONES",
    "APP_DIR",
    "APP_LOG",
    "SERVICE_INSTALL_NAME",
]

zone_pattern = re.compile(r'zone\s+"[^"]+"\s*(?:IN)?\s*\{[\s\S]*?};', re.MULTILINE)
file_pattern = re.compile(r'file\s+"([^"]+)"')
record_pattern = re.compile(r'^(\S+)\s+(?:(\d+)\s+)?(?:(IN)\s+)?(\S+)\s+(.*)$')

ZONES_DIR = "/var/named/chroot/var/named/"
ZONES = "/var/named/chroot/etc/named.rfc1912.zones"
APP_DIR = os.path.dirname(os.path.abspath(__file__))
SERVICE_INSTALL_NAME = f"{APP_DIR}/aadns.pl"
APP_LOG = f"{APP_DIR}/aadns.log"


class aaDnsConfig:
    def __init__(self):
        self.os_type = None
        self.package = None
        self.install_service = None
        self.bind_service_name = "named"
        self.pnds_service_name = "pdns"
        self._check_env()

    def _check_env(self):
        if os.path.exists("/etc/redhat-release"):
            self.os_type = "redhat"  # centos
            self.package = "yum"
            # RHEL/CentOS，检查 bind-chroot 服务具体名称
            if os.path.exists("/usr/lib/systemd/system/named-chroot.service"):
                self.bind_service_name = "named-chroot"
        else:
            self.os_type = "ubuntu"  # debian
            self.package = "apt"
            self.bind_service_name = "named"

        if os.path.exists(SERVICE_INSTALL_NAME):
            with open(SERVICE_INSTALL_NAME, "r") as f:
                self.install_service = f.read().strip()
            if self.install_service not in ["bind", "pdns"]:
                try:
                    os.remove(SERVICE_INSTALL_NAME)
                except:
                    pass
                self.install_service = None

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
