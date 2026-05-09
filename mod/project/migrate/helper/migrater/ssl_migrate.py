# coding: utf-8
# -------------------------------------------------------------------
# aaPanel
# -------------------------------------------------------------------
# Copyright (c) 2014-2099 aaPanel(www.aapanel.com) All rights reserved.
# -------------------------------------------------------------------
# Author: aapanel
# -------------------------------------------------------------------

# ------------------------------
# SslMigrate app
# ------------------------------
import sys
from typing import List, Optional

if "/www/server/panel/class" not in sys.path:
    sys.path.insert(0, "/www/server/panel/class")
if "/www/server/panel/class_v2" not in sys.path:
    sys.path.insert(0, "/www/server/panel/class_v2")
from public.hook_import import hook_import

hook_import()
from ..engine import MigrateCore
from ..parser import split_combined_cert


class SslMigrate(MigrateCore):
    """SSL 迁移器."""
    task_name = "ssl"

    def backup(self) -> List[str]:
        """远端备份 SSL 证书"""
        backup_files: List[str] = []
        ssl_list = self.current_data
        for idx, ssl in enumerate(ssl_list, start=1):
            try:
                if ssl.get('ssl_cert_b64') and isinstance(ssl['ssl_cert_b64'], str):
                    ssl_cert_b64 = ssl['ssl_cert_b64']
                    self.logger.info(
                        f"[{idx}/{len(ssl_list)}] back up ssl: {ssl.get('domain', 'unknown domain')}"
                    )
                    self.update_data_item(ssl.get('_id'), _ssl_cert_b64=ssl_cert_b64)
            except Exception as e:
                self.logger.error(f"[SSL] Failed to backup SSL {idx}: {e}")
        return backup_files

    def restore(self) -> None:
        """本地恢复 SSL 证书."""
        ssl_list = self.current_data
        if not ssl_list:
            self.logger.info("No SSL to restore.")
            return
        import base64
        from ssl_domainModelV2.service import CertHandler
        handler = CertHandler()
        for ssl in ssl_list:
            try:
                cert_content = base64.b64decode(ssl.get('_ssl_cert_b64')).decode('utf-8', errors='ignore')
                if not cert_content:
                    self.logger.info(f"Empty certificate content for {ssl.get('domain')}")
                    continue
                cert_parts = split_combined_cert(cert_content)
                res = handler.save_by_data(
                    cert_pem=cert_parts['cert'],
                    private_key=cert_parts['key']
                )
                if res:
                    self.logger.info(f"Restored SSL [{ssl.get('domain', 'unknown domain')}]")
            except Exception as e:
                self.logger.error(f"Failed to restore SSL for {ssl.get('domain', 'unknown domain')}: {e}")
