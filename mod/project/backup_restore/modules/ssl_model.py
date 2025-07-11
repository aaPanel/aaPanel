# coding: utf-8
# -------------------------------------------------------------------
# aapanel
# -------------------------------------------------------------------
# Copyright (c) 2015-2099 aapanel(http://www.aapanel.com) All rights reserved.
# -------------------------------------------------------------------

import os
import sys
import time
from pathlib import Path

if "/www/server/panel/class" not in sys.path:
    sys.path.insert(0, "/www/server/panel/class")
if "/www/server/panel/class_v2" not in sys.path:
    sys.path.insert(0, "/www/server/panel/class_v2")
if "/www/server/panel" not in sys.path:
    sys.path.insert(0, "/www/server/panel")
import public
from public.hook_import import hook_import

hook_import()
from BTPanel import app
from ssl_domainModelV2.api import DomainObject
from ssl_domainModelV2.service import CertHandler
from ssl_domainModelV2.config import UserFor
from ssl_domainModelV2.model import DnsDomainSSL, DnsDomainProvider
from mod.project.backup_restore.data_manager import DataManager


class SSLModel(DataManager):
    def __init__(self):
        super().__init__()
        self.base_path = '/www/backup/backup_restore'
        self.bakcup_task_json = self.base_path + '/backup_task.json'

    def get_ssl_backup_conf(self, timestamp: int = None) -> dict:
        """
        Get SSL certificate and DNS API provider backup configuration
        """
        ssl_list = [
            {
                **ssl.as_dict(),
                "data_type": "backup",
                "status": 0,
                "msg": None,
            } for ssl in DnsDomainSSL.objects.filter(is_order=0)  # 过滤商业证书
        ]
        provider_list = [
            {
                **x.as_dict(),
                # 与备份的 status 字段冲突, 使用 account status
                "account_status": x.status,
                "data_type": "backup",
                "status": 0,
                "msg": None,
            } for x in DnsDomainProvider.objects.all()
        ]
        res = {
            "ssl_list": ssl_list,
            "provider_list": provider_list,
        }
        return res

    def backup_ssl_data(self, timestamp) -> None:
        """
        Backup domain management center
        """
        # 总配置
        data_list = self.get_backup_data_list(timestamp)
        if not data_list:
            return None

        data_backup_path = data_list.get("backup_path")
        ssl_backup_path = Path(data_backup_path) / "ssl"
        ssl_backup_path.mkdir(parents=True, exist_ok=True)
        self.print_log("==================================", "backup")
        self.print_log(public.lang("Start backing up SSL certificate information"), "backup")

        for ssl in data_list['data_list']['ssl'].get("ssl_list", []):  # SSL in the general configuration
            try:
                if not ssl.get("path") or not os.path.exists(ssl.get("path")):
                    err = public.lang("{} {} Certificate file does not exist ✗").format(
                        ssl['info'].get("issuer_O", ""), ssl['dns']
                    )
                    self.print_log(err, "backup")
                    ssl["status"] = 3
                    ssl["msg"] = err
                    continue
                if ssl.get("not_after_ts") < time.time() * 1000:
                    err = public.lang("{} [{}] Certificate has expired ✗").format(
                        ssl['info'].get("issuer_O", ""), str(ssl['dns'])
                    )
                    self.print_log(err, "backup")
                    ssl["status"] = 3
                    ssl["msg"] = err
                    continue
                domian_path = ssl_backup_path / ssl.get("hash")
                CertHandler.make_last_info(domian_path, force=True)
                public.ExecShell(f"\cp -rpa {ssl['path']} {domian_path}")
                ssl["status"] = 2
                self.print_log(public.lang("{} {} ✓").format(
                    ssl['info'].get("issuer_O", ""), ssl['dns']
                ), "backup")
            except Exception as e:
                err = public.lang("{} {} Backup failed: {} ✗").format(
                    ssl['info'].get('issuer_O', ''), ssl['dns'], str(e)
                )
                ssl["status"] = 3
                ssl["msg"] = err
                self.print_log(err, "backup")
                continue

        new_provider_info = [
            {**x, "status": 2} for x in data_list['data_list']['ssl'].get("provider_list", [])
        ]
        data_list['data_list']['ssl']['provider_list'] = new_provider_info
        self.print_log(public.lang("DNS API provider information backup completed"), "backup")

        self.update_backup_data_list(timestamp, data_list)
        self.print_log(public.lang("SSL certificate information backup completed"), "backup")

    def _rebuild_deploy(self, ssl_obj: DnsDomainSSL, backup_ssl: dict) -> None:
        try:
            def r_log(log_str: str, new_log: str):
                self.replace_log(log_str, new_log, "restore")

            used = backup_ssl.get("user_for", {})
            if not ssl_obj or not used:
                return

            # pre clear
            for other_ssl in DnsDomainSSL.objects.filter(hash__ne=ssl_obj.hash):
                is_change = False

                for site_name in used.get(UserFor.sites, []):
                    if site_name in other_ssl.sites_uf:
                        other_ssl.sites_uf.remove(site_name)
                        is_change = True

                for mail_name in used.get(UserFor.mails, []):
                    if mail_name in other_ssl.mails_uf:
                        other_ssl.mails_uf.remove(mail_name)
                        is_change = True

                for panel_name in used.get(UserFor.panel, []):
                    if panel_name in other_ssl.panel_uf:
                        other_ssl.panel_uf = []
                        is_change = True

                if is_change:
                    other_ssl.save()

            if used.get(UserFor.sites):
                log_str = public.lang("Restoring deployment sites for certificate {}...").format(backup_ssl['subject'])
                self.print_log(log_str, "restore")
                build_sites = ssl_obj.deploy_sites(
                    site_names=used[UserFor.sites], replace=True
                )
                r_log(log_str, public.lang("Restored deployment sites for certificate {}: {}").format(
                    backup_ssl['subject'], build_sites.get('msg')
                ))

            if used.get(UserFor.mails):
                log_str = public.lang("Restoring deployment mailboxes for certificate {}...").format(
                    backup_ssl['subject'])
                self.print_log(log_str, "restore")
                build_mails = ssl_obj.deploy_mails(
                    mail_names=used[UserFor.mails]
                )
                r_log(log_str, public.lang("Restored deployment mailboxes for certificate {}: {}").format(
                    backup_ssl['subject'], build_mails.get('msg')
                ))

            if used.get(UserFor.panel):
                log_str = public.lang("Restoring deployment panel for certificate {}...").format(backup_ssl['subject'])
                self.print_log(log_str, "restore")
                build_panel = ssl_obj.deploy_panel(
                    recover=0
                )
                r_log(log_str, public.lang("Restored deployment panel for certificate {}: {}").format(
                    backup_ssl['subject'], build_panel.get('msg')
                ))
        except Exception as e:
            public.print_log("rebuild deploy error: {}".format(str(e)))

    def _restore_ssl(self, backup_ssl: dict, pem: str, key: str) -> None:
        exist_obj = DnsDomainSSL.objects.filter(
            hash=CertHandler.get_hash(cert_pem=pem)
        ).first()
        if exist_obj:
            if not self.overwrite:
                return
            # overwrite
            # exist_obj.provider_id = backup_ssl["provider_id"]
            # exist_obj.not_after = backup_ssl["not_after"]
            # exist_obj.not_after_ts = backup_ssl["not_after_ts"]
            exist_obj.user_for = backup_ssl["user_for"]
            exist_obj.info = backup_ssl["info"]
            exist_obj.alarm = backup_ssl["alarm"]
            exist_obj.auto_renew = backup_ssl["auto_renew"]
            exist_obj.auth_info = backup_ssl["auth_info"]
            exist_obj.log = backup_ssl["log"]
            exist_obj.save()
            # ssl_obj = exist_obj
        else:
            try:
                insert = CertHandler().save_by_data(
                    cert_pem=pem,
                    private_key=key,
                    new_auth_info=backup_ssl["auth_info"],
                )
                if not insert:
                    raise Exception(public.lang("Certificate insertion failed, please check the log"))
            except Exception as e:
                raise Exception(public.lang(f"Certificate Restore Failed: {str(e)}"))

            # ssl_obj = DnsDomainSSL.objects.filter(hash=insert["hash"]).first()

        # if ssl_obj:
        #     # it will update the ssl field 'user_for'
        #     self._rebuild_deploy(
        #         ssl_obj=ssl_obj,
        #         backup_ssl=backup_ssl,
        #     )

    def _restore_provider(self, provider: dict):
        if_exist = DnsDomainProvider.objects.filter(
            name=provider["name"],
            api_user=provider.get("api_user", ""),
            api_key=provider["api_key"],
        ).first()
        if if_exist:
            if self.overwrite:
                return
            return

        res = DomainObject().create_dns_api(
            public.to_dict_obj({
                "name": provider["name"],
                "api_user": provider.get("api_user", ""),
                "api_key": provider["api_key"],
                "status": provider.get("account_status", 1),
                "permission": provider.get("permission", "-"),
                "alias": provider["alias"],
                "ps": provider["ps"],
            })
        )
        if res.get("status", 0) != 0:
            raise Exception(public.lang(
                f"Restore DNS API provider failed: {res.get('message', 'create dns api error')}"
            ))

    def restore_ssl_data(self, timestamp: int) -> None:
        """ Restore domain management center """
        self.print_log("====================================================", "restore")
        self.print_log(public.lang("Start restoring domain SSL certificate configuration"), "restore")
        restore_data = self.get_restore_data_list(timestamp)
        if not restore_data:
            self.print_log(public.lang("No restore data found"), "restore")
            return
        ssl_cert_path = Path(restore_data.get("backup_path")) / "ssl"
        if not ssl_cert_path.exists():
            self.print_log(
                public.lang("Backup directory {} does not exist, unable to restore SSL certificate information").format(
                    ssl_cert_path
                ), "restore")
            return
        ssl_info = restore_data["data_list"].get("ssl", {})
        with app.app_context():
            # ======================= ssl =============================
            for ssl in ssl_info.get("ssl_list", []):
                log_str = public.lang("Restoring {} Subject: {}").format(
                    ssl['info'].get('issuer_O'), ssl['subject']
                )
                try:
                    self.print_log(log_str, "restore")
                    ssl["restore_status"] = 1
                    ssl_path = ssl_cert_path / ssl["hash"]
                    if not ssl_path.exists():
                        raise Exception(public.lang("Certificate file does not exist"))
                    pem = ssl_path / "fullchain.pem"
                    key = ssl_path / "privkey.pem"
                    if not pem.exists() or not key.exists():
                        raise Exception(public.lang("Missing certificate or private key file"))
                    self._restore_ssl(
                        backup_ssl=ssl,
                        pem=public.readFile(str(pem)),
                        key=public.readFile(str(key)),
                    )
                    ssl["restore_status"] = 2
                    self.replace_log(
                        log_str,
                        public.lang(f"Restored {ssl['info'].get('issuer_O')} Subject: {ssl['subject']} ✓ "),
                        "restore"
                    )
                except Exception as e:
                    err_msg = public.lang(
                        f"Restoring {ssl['info'].get('issuer_O', '')} Subject: {ssl['subject']} failed: {str(e)}"
                    )
                    ssl["restore_status"] = 3
                    ssl["msg"] = str(e)
                    self.replace_log(log_str, err_msg, "restore")

                self.update_restore_data_list(timestamp, restore_data)

            # ======================= dns provider =============================
            for provider in ssl_info.get("provider_list", []):
                log_str = public.lang(f"Restoring DNS API {provider['name']}: {provider['alias']}...")
                try:
                    self.print_log(log_str, "restore")
                    self._restore_provider(provider)
                    time.sleep(1)
                    provider["restore_status"] = 2
                    self.replace_log(
                        log_str,
                        public.lang(f"Restored DNS API {provider['name']}: {provider['alias']} ✓ "),
                        "restore"
                    )
                except Exception as e:
                    err_msg = public.lang(f"Restoring DNS API provider: {provider['name']} failed: {str(e)}")
                    provider["restore_status"] = 3
                    provider["msg"] = str(e)
                    self.replace_log(log_str, err_msg, "restore")
                    self.update_restore_data_list(timestamp, restore_data)

                self.update_restore_data_list(timestamp, restore_data)

        self.print_log(public.lang("SSL certificate information restoration completed"), "restore")


if __name__ == '__main__':
    if len(sys.argv) < 3:
        print("Usage: btpython backup_manager.py <method> <timestamp>")
        sys.exit(1)
    method_name = sys.argv[1]
    timestamp = sys.argv[2]
    database_module = SSLModel()
    if hasattr(database_module, method_name):
        method = getattr(database_module, method_name)
        method(timestamp)
    else:
        print(f"Error: method '{method_name}' not found")
