# coding: utf-8
import os
import sys

sys.path.insert(0, os.path.abspath("/www/server/panel"))

if "/www/server/panel/class" not in sys.path:
    sys.path.insert(0, "/www/server/panel/class")
if "/www/server/panel/class_v2" not in sys.path:
    sys.path.insert(0, "/www/server/panel/class_v2")

from .config import (
    SPECIAL_PROJECT_TYPE
)
from .model import (
    generate_log,
    get_site_name,
    apply_cert,
    DnsDomainProvider,
    DnsDomainSSL,
    DnsDomainTask,
    DnsDomainRecord,
)
from .service import (
    sync_user_for,
    SiteHelper,
    CertHandler,
    DomainValid,
)

__all__ = [
    # config
    "SPECIAL_PROJECT_TYPE",

    # model.py
    "generate_log",
    "get_site_name",
    "apply_cert",
    "DnsDomainProvider",
    "DnsDomainSSL",
    "DnsDomainTask",
    "DnsDomainRecord",

    # service.py
    "sync_user_for",
    "SiteHelper",
    "CertHandler",
    "DomainValid",
]
