# coding: utf-8
# -------------------------------------------------------------------
# aaPanel
# -------------------------------------------------------------------
# Copyright (c) 2014-2099 aaPanel(www.aapanel.com) All rights reserved.
# -------------------------------------------------------------------
# Author: aapanel
# -------------------------------------------------------------------

# WpMigrate - WordPress 站点迁移实现

import sys
import os
import time
from typing import List, Optional

if "/www/server/panel/class" not in sys.path:
    sys.path.insert(0, "/www/server/panel/class")
if "/www/server/panel/class_v2" not in sys.path:
    sys.path.insert(0, "/www/server/panel/class_v2")
import public
from public.hook_import import hook_import

hook_import()

from ..engine import MigrateCore
from ..parser import split_combined_cert


class WpMigrate(MigrateCore):
    """WordPress 迁移器"""

    D_Tag = "__"
    task_name = "wordpress"

    @property
    def current_data(self) -> list:
        return [
            s for s in self._data_list if s.get("type", "").lower() == "wp"
        ]

    def _get_local_backup_path(self, relative_path: str = None) -> Optional[str]:
        """获取本地备份路径
        本地备份文件路径: /tmp/timestamp_aa_migrate/用户名/备份类型/相对路径
        """
        username = self.detail.get('user')
        if not username:
            return None
        if relative_path:
            local_path = os.path.join(self.local_base_dir, username, self.task_name, relative_path)
            return local_path
        return None

    def validate(self) -> Optional[str]:
        """验证 WordPress 站点."""
        if not self.current_data:
            return "No WordPress sites found"
        return None

    def backup(self) -> List[str]:
        """远端备份 WordPress 站点.

        Returns:
            生成的备份文件路径列表
        """
        backup_files: List[str] = []
        wp_sites = self.current_data
        for idx, site in enumerate(wp_sites, start=1):
            domain = ''
            try:
                domain = site.get('domain', '').lower().rstrip('/').strip()
                sub_path = site.get('sub_path', '').lower().lstrip('/').strip()
                if sub_path:
                    domain = f"{domain}/{sub_path}"

                self.logger.info(f"{domain}", f"{idx}/{len(wp_sites)}")

                domain_tag = domain.replace('/', self.D_Tag)
                tar_file = f"{self.backup_dir}/{domain_tag}.tar.gz"
                sql_file = f"{self.backup_dir}/{domain_tag}_db.sql"

                # 先导出数据库, 打包时追加到包中
                self.logger.info("Dumping WordPress database...")
                status, out = self.ssh_manager.dump_db(
                    site['db_name'], site['db_user'], site['db_pass'], sql_file
                )
                if not status:
                    raise Exception(f"Failed to dump database: {out}")

                # 打包站点
                self.logger.info("Packing site files...")
                # cpanel格式meta
                meta_json = {
                    "dbPrefix": site['db_prefix'],
                    "timestamp": int(time.time()),
                    "absolutePath": site['site_path']
                }
                status, out = self.ssh_manager.pack_wp_site(
                    site['site_path'], tar_file, sql_file, meta_json
                )
                if not status:
                    raise Exception(f"Failed to pack site: {out}")

                # pack成功后更新本地路径
                relative_path = os.path.relpath(tar_file, self.backup_dir)
                local_path = self._get_local_backup_path(relative_path)
                if local_path:
                    self.update_data_item(site.get('_id'), _local_path=local_path)

                backup_files.extend([tar_file, sql_file])
            except Exception as e:
                self.logger.error(f"Failed to backup {domain or 'unknow'}: {e}")
                continue

        return backup_files

    def restore(self) -> None:
        """本地恢复 WordPress 站点."""
        wp_sites = self.current_data
        if not wp_sites:
            self.logger.info("No WordPress sites to restore")
            return
        wp_base_path = os.path.join(self.local_base_dir, self.detail.get('user', ''), self.task_name)
        if not os.path.exists(wp_base_path):
            raise Exception(f"File Not Found: '{wp_base_path}'")
        from panel_site_v2 import panelSite
        site_obj = panelSite()
        get_php = site_obj.GetPHPVersion(public.to_dict_obj({}), is_http=False)
        # php版本
        get_php = get_php[-1] if get_php and isinstance(get_php, list) else {
            "version": "00",
            "name": "Static",
            "title": ""
        }
        self.logger.info(f"Restoring {len(wp_sites)} WordPress sites...")
        for site in wp_sites:
            full_name = f"{site.get('domain', '')}/{site.get('sub_path', '')}".rstrip('/')
            try:
                body = public.to_dict_obj({
                    'bak_file': site['_local_path'],
                    'domain': site['domain'],
                    'sub_path': site['sub_path'],
                    'php_ver_short': get_php.get('version', '00'),
                    'enable_cache': '1',
                    'ssl_auto': '0',
                    'project_type': 'WP2',
                })
                if site_obj.wp_create_with_plesk_or_cpanel_bak(body).get('status') != 0:
                    time.sleep(1)
                    if site_obj.wp_create_with_plesk_or_cpanel_bak(body).get('status') != 0:
                        self.logger.error(f"Failed to restore {site.get('domain', '')}")
                        continue
                self.logger.info(f"Start restore [{full_name}]...")
                time.sleep(5)
                fail_count = 0
                # 0进行, 2等待, 1完成, -1失败
                one_status = {
                    'new_sites_add': 0,
                    'import_the_database': 0,
                    'initialize_the_website': 0,
                }
                while fail_count <= 120:
                    status_res = site_obj.get_wp_progress(
                        public.to_dict_obj({'progress_type': 'backup_deploy'})
                    )
                    if not status_res.get('status') == 0:
                        fail_count += 1
                        time.sleep(1)
                        continue
                    msg_body = status_res.get('message')
                    if not msg_body:
                        fail_count += 1
                        time.sleep(1)
                        continue

                    task_status = msg_body.get('status')
                    if task_status == 1:  # task_status=1, 完成||有错误
                        import jsonpath
                        # 第一个非空的error
                        error = jsonpath.jsonpath(msg_body, '$..error') or []
                        error = next((e for e in error if e), '')
                        if error:
                            self.logger.error(f"Failed to restore [{full_name}]: {error}")
                            break
                        success_msg = f"Successfully Restored [{full_name}]"
                        self.logger.info(success_msg)
                        self.restored_domains.add(site.get('domain', '').lower().rstrip('/').strip())
                        # 处理ssl
                        self._restore_ssl_cert(site)
                        break

                    last_step = {}
                    for key in one_status.keys():
                        # if msg_body.get(key) == 1: # 已完成
                        #     continue
                        if msg_body.get(key, {}).get('status') in [0, 2]:
                            last_step = msg_body[key]
                            # continue
                    if last_step:
                        self.logger.info(last_step.get('ps'))
                    time.sleep(1)
            except Exception:
                import traceback
                self.logger.error(f"Failed to restore [{full_name}]: {traceback.format_exc()}")
                continue

    def _restore_ssl_cert(self, site: dict) -> None:
        """恢复 SSL 证书"""
        ssl_cert_b64 = site.get('ssl_cert')
        if not ssl_cert_b64:
            return
        try:
            import base64
            from ssl_domainModelV2.service import CertHandler
            cert_content = base64.b64decode(ssl_cert_b64).decode('utf-8', errors='ignore')
            if not cert_content:
                self.logger.info(f"[SSL] Empty certificate content for {site.get('domain')}")
                return
            # 分离 cert 和 key
            cert_parts = split_combined_cert(cert_content)
            if not cert_parts['cert'] or not cert_parts['key']:
                self.logger.info(f"[SSL] Failed to split certificate for {site.get('domain')}")
                return
            # 证书
            res = CertHandler().save_by_data(
                cert_pem=cert_parts['cert'],
                private_key=cert_parts['key']
            )
            if res:
                self._apply_cert_to_domain(site['domain'], res)
        except Exception as e:
            public.print_log(e)

    def _apply_cert_to_domain(self, domain: str, cert_info: dict) -> bool:
        """证书应用到域名"""
        from ssl_domainModelV2.model import DnsDomainSSL
        ssl = DnsDomainSSL.objects.filter(id=cert_info.get('id')).first()
        if not ssl:
            return False
        ssl.deploy_sites([domain])
        return True
