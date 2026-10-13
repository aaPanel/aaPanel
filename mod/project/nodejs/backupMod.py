# coding: utf-8
# -------------------------------------------------------------------
# aapanel
# -------------------------------------------------------------------
# Copyright (c) 2015-2099 aapanel(http://www.aapanel.com) All rights reserved.
# -------------------------------------------------------------------
# Author: Fan
# -------------------------------------------------------------------
# ------------------------------
# Node.js 项目备份还原模块
# ------------------------------
import json
import os
import shutil
import sys

if "/www/server/panel/class" not in sys.path:
    sys.path.insert(0, "/www/server/panel/class")
if "/www/server/panel" not in sys.path:
    sys.path.insert(0, "/www/server/panel")

import public
from mod.project.nodejs.base import NodeJs


class NodeBackup(NodeJs):

    def __init__(self):
        super(NodeBackup, self).__init__()
        self.status_file = '/tmp/nodejs_backup.log'
        self.setup_path = '/www/server'

    # 日志
    def write_backup_log(self, status_file: str, status: int, ps: str, result_list: list) -> None:
        data = {
            "status": status, "error": "",
            "backup_website": {
                "status": status, "ps": ps, "title": public.lang("Backup_website"),
                "result_list": result_list
            }
        }
        public.writeFile(status_file, json.dumps(data))

    # 文件还原
    def do_nodejs_file_restore(self, file_name: str, site_id: int):
        # 定位备份文件
        backup_path = public.M('config').where('id=?', (1,)).getField('backup_path')
        local_file = os.path.join(backup_path, 'nodejs', file_name)
        if not os.path.exists(local_file):
            db_filename = public.M('backup').where('name=? AND pid=?', (file_name, site_id)).getField('filename')
            if db_filename and os.path.exists(db_filename):
                local_file = db_filename
        if not os.path.exists(local_file):
            return public.return_message(-1, 0, public.lang("Backup file not found: {}").format(file_name))

        # 查找目标站点
        find = public.M('sites').where("id=? AND project_type=?", (site_id, 'Node')).field('id,name,path,project_config').find()
        if not isinstance(find, dict) or not find.get('id'):
            return public.return_message(-1, 0, public.lang("Site not found, please create it first"))

        site_path = find['path']
        site_name = find['name']
        if not os.path.exists(site_path):
            os.makedirs(site_path, 0o755)

        # 解压
        if file_name.endswith('.zip'):
            public.ExecShell("cd '{}' && unzip -o '{}' > /dev/null 2>&1".format(site_path, local_file))
        else:
            public.ExecShell("tar -zxf '{}' -C '{}'".format(local_file, site_path))

        # 修复权限
        public.ExecShell('chown -R www:www "{}"'.format(site_path))

        # 检查依赖，缺失则构建
        node_modules_path = os.path.join(site_path, 'node_modules')
        package_json_path = os.path.join(site_path, 'package.json')
        if not os.path.exists(node_modules_path) and os.path.exists(package_json_path):
            try:
                from projectModelV2.nodejsModel import main as nodejsModel
                install_get = public.to_dict_obj({'project_name': site_name})
                nodejsModel().install_packages(install_get)
            except Exception as e:
                return public.return_message(-1, 0, public.lang("Dependency install failed: {}").format(str(e)))

        # 重启项目
        try:
            project_config = json.loads(find.get('project_config', '{}'))
            project_type = project_config.get('project_type', 'nodejs')
            get = public.to_dict_obj({'project_name': site_name, 'project_type': project_type})
            if project_type == 'pm2':
                from mod.project.nodejs.pm2Mod import main as pm2Mod
                pm2Mod().start_project(get)
            else:
                from projectModel.nodejsModel import main as nodeModel
                nodeModel().start_project(get)
        except Exception as e:
            return public.return_message(-1, 0, public.lang("Project restart failed: {}").format(str(e)))

        public.write_log_gettext('Node Project', 'Successfully restored Node.js project files [{}]', (site_name,))
        return public.return_message(0, 0, public.lang("File restore completed for: {}").format(site_name))

    # 全量还原
    def do_nodejs_full_restore(self, file_name: str, site_id: int, restore_type: list):
        tmp_path = public.make_panel_tmp_path()
        try:
            return self._do_nodejs_full_restore(file_name, site_id, restore_type, tmp_path)
        finally:
            if tmp_path and os.path.exists(tmp_path):
                shutil.rmtree(tmp_path, ignore_errors=True)

    def _do_nodejs_full_restore(self, file_name: str, site_id: int, restore_type: list, tmp_path: str):
        # 1. 定位备份文件
        backup_path = public.M('config').where('id=?', (1,)).getField('backup_path')
        local_file = os.path.join(backup_path, 'nodejs', file_name)
        if not os.path.exists(local_file):
            local_file = os.path.join(backup_path, 'nodejs', str(site_id), file_name)
        if not os.path.exists(local_file):
            db_filename = public.M('backup').where('name=? AND pid=?', (file_name, site_id)).getField('filename')
            if db_filename and os.path.exists(db_filename):
                local_file = db_filename
        if not os.path.exists(local_file):
            return public.return_message(-1, 0, public.lang("Backup file not found: {}").format(file_name))

        # 2. 解压到临时目录
        os.makedirs(tmp_path, exist_ok=True)
        public.ExecShell('tar -zxf "{}" -C "{}"'.format(local_file, tmp_path))

        # 3. 读取 meta.json
        meta_file = os.path.join(tmp_path, 'meta.json')
        if not os.path.exists(meta_file):
            return public.return_message(-1, 0, public.lang("meta.json not found in backup"))

        with open(meta_file, 'r', encoding='utf-8') as fp:
            meta = json.load(fp)

        site_name = meta.get('site_name', '')
        if not site_name:
            return public.return_message(-1, 0, public.lang("site_name is empty in meta.json"))

        # 4. 查找目标站点
        find = public.M('sites').where("id=? AND project_type=?", (site_id, 'Node')).field('id,name,path,project_config').find()
        if not isinstance(find, dict) or not find.get('id'):
            return public.return_message(-1, 0, public.lang("Site [{}] does not exist, please create it first").format(site_name))

        # 4.1 校验项目类型一致性
        current_config = json.loads(find.get('project_config', '{}'))
        current_type = current_config.get('project_type', 'nodejs')
        backup_type = meta.get('project_type', 'nodejs')
        if current_type != backup_type:
            type_map = {'pm2': 'PM2', 'nodejs': public.lang('Node.js'), 'general': 'General'}
            return public.return_message(-1, 0,
                public.lang("Project type mismatch: current is [{}], backup is [{}], restore not allowed").format(
                    type_map.get(current_type, current_type), type_map.get(backup_type, backup_type)))

        current_path = find.get('path', meta.get('site_path', ''))
        backup_site_path = meta.get('site_path', '')

        # 4.2 目录冲突校验
        if backup_site_path and current_path != backup_site_path:
            if os.path.exists(backup_site_path):
                return public.return_message(-1, 0,
                    public.lang("Backup source directory [{}] already exists on disk, restore aborted to prevent data conflict").format(backup_site_path))
            current_path = backup_site_path
            if not os.path.exists(current_path):
                os.makedirs(current_path, 0o755)
            public.M('sites').where('id=?', (site_id,)).update({'path': current_path})

        # 5. 还原文件
        if 'file' in restore_type:
            files_tar = os.path.join(tmp_path, 'files.tar.gz')
            if os.path.exists(files_tar):
                if not os.path.exists(current_path):
                    os.makedirs(current_path, 0o755)
                public.ExecShell('tar -zxf "{}" -C "{}"'.format(files_tar, current_path))

        # 6. 还原配置
        if 'conf' in restore_type:
            configs_dir = os.path.join(tmp_path, 'configs')
            if os.path.exists(configs_dir):
                self._restore_nodejs_configs(site_name, configs_dir, meta)

            # 还原 PM2 ecosystem 配置
            if meta.get('has_ecosystem_config') and meta.get('project_type') == 'pm2':
                eco_src = os.path.join(tmp_path, 'ecosystem.config.cjs')
                eco_dst = meta.get('config_file', '')
                if os.path.exists(eco_src) and eco_dst:
                    eco_dir = os.path.dirname(eco_dst)
                    if eco_dir and not os.path.exists(eco_dir):
                        os.makedirs(eco_dir, 0o755, exist_ok=True)
                    shutil.copy2(eco_src, eco_dst)

            # 还原域名（仅 bind_extranet=1 时触发 web 服务配置生成）
            domain_list = meta.get('domain_list', [])
            if domain_list:
                self._restore_nodejs_domains(site_id, site_name, domain_list)

            # 更新 project_config
            new_config = {
                'project_name': meta.get('project_name', site_name),
                'pm2_name': meta.get('pm2_name', ''),
                'project_type': meta.get('project_type', ''),
                'project_cwd': meta.get('project_cwd', current_path),
                'project_file': meta.get('project_file', ''),
                'project_script': meta.get('project_script', ''),
                'project_args': meta.get('project_args', ''),
                'config_file': meta.get('config_file', ''),
                'config_body': meta.get('config_body', ''),
                'env': meta.get('env', ''),
                'run_user': meta.get('run_user', 'www'),
                'port': meta.get('port'),
                'nodejs_version': meta.get('nodejs_version', ''),
                'pkg_manager': meta.get('pkg_manager', 'npm'),
                'max_memory_limit': meta.get('max_memory_limit', 4096),
                'is_power_on': meta.get('is_power_on', True),
                'watch': meta.get('watch', False),
                'cluster': meta.get('cluster', 1),
                'bind_extranet': meta.get('bind_extranet', 0),
                'domains': [d.get('name', '') + ':' + str(d.get('port', 80)) for d in domain_list],
                'log_path': meta.get('log_path', self.node_logs_path),
            }
            public.M('sites').where('id=?', (site_id,)).update({
                'path': current_path,
                'project_config': json.dumps(new_config)
            })
            self.set_config(site_name)

        # 修复权限
        public.ExecShell('chown -R www:www "{}"'.format(current_path))

        # 检查 Node.js 版本是否存在，不存在则安装
        backup_nodejs_version = meta.get('nodejs_version', '')
        if backup_nodejs_version:
            installed_versions = self.get_nodejs_version(None)
            version_installed = any(v == backup_nodejs_version for v in installed_versions)
            if not version_installed:
                #  系统/NVM 后缀版本：无法经面板插件安装，需目标服务器先扫描系统 Node
                if "-" in backup_nodejs_version:
                    return public.return_message(-1, 0,
                        public.lang("Node.js version [{}] is a system/NVM managed version and is not installed on this server. Please scan the system Node first and then restore.").format(
                            backup_nodejs_version))
                pkg_manager = meta.get('pkg_manager', 'npm')
                node_res = self._install_nodejs_with_modules(backup_nodejs_version, pkg_manager)
                if not node_res.get('status'):
                    return public.return_message(-1, 0,
                        public.lang("Node.js version [{}] installation failed: {}").format(
                            backup_nodejs_version, node_res.get('error_msg', '')))

        # 检查依赖，缺失则构建
        node_modules_path = os.path.join(current_path, 'node_modules')
        package_json_path = os.path.join(current_path, 'package.json')
        if not os.path.exists(node_modules_path) and os.path.exists(package_json_path):
            try:
                from projectModelV2.nodejsModel import main as nodejsModel
                install_get = public.to_dict_obj({'project_name': site_name})
                nodejsModel().install_packages(install_get)
            except Exception as e:
                return public.return_message(-1, 0, public.lang("Dependency install failed: {}").format(str(e)))

        # 重启项目
        try:
            get = public.to_dict_obj({'project_name': site_name, 'project_type': meta.get('project_type', 'nodejs')})
            if meta.get('project_type') == 'pm2':
                from mod.project.nodejs.pm2Mod import main as pm2Mod
                pm2Mod().start_project(get)
            else:
                from projectModel.nodejsModel import main as nodeModel
                nodeModel().start_project(get)
        except Exception as e:
            return public.return_message(-1, 0, public.lang("Project restart failed: {}").format(str(e)))

        public.write_log_gettext('Node Project', 'Successfully restored Node.js project [{}]', (site_name,))
        return public.return_message(0, 0, public.lang("Restore completed for: {}").format(site_name))

    # 配置还原
    def _restore_nodejs_configs(self, site_name: str, configs_dir: str, meta: dict = None) -> None:
        vhost = self.vhost_path

        # --- Nginx ---
        nginx_src = os.path.join(configs_dir, 'nginx', 'node_{}.conf'.format(site_name))
        if os.path.exists(nginx_src):
            nginx_dst = '{}/nginx/node_{}.conf'.format(vhost, site_name)
            shutil.copy2(nginx_src, nginx_dst)

        well_known_src = os.path.join(configs_dir, 'nginx', 'well-known', site_name)
        if os.path.exists(well_known_src):
            well_known_dst = '{}/nginx/well-known/{}'.format(vhost, site_name)
            if os.path.exists(well_known_dst):
                shutil.rmtree(well_known_dst, ignore_errors=True)
            shutil.copytree(well_known_src, well_known_dst, dirs_exist_ok=True)

        # --- Apache ---
        apache_src = os.path.join(configs_dir, 'apache', 'node_{}.conf'.format(site_name))
        if os.path.exists(apache_src):
            apache_dst = '{}/apache/node_{}.conf'.format(vhost, site_name)
            shutil.copy2(apache_src, apache_dst)

        # --- OpenLiteSpeed ---
        ols_src = os.path.join(configs_dir, 'openlitespeed', '{}.conf'.format(site_name))
        if os.path.exists(ols_src):
            ols_dst = '{}/openlitespeed/{}.conf'.format(vhost, site_name)
            shutil.copy2(ols_src, ols_dst)

        ols_detail_src = os.path.join(configs_dir, 'openlitespeed', 'detail', '{}.conf'.format(site_name))
        if os.path.exists(ols_detail_src):
            ols_detail_dst = '{}/openlitespeed/detail/{}.conf'.format(vhost, site_name)
            shutil.copy2(ols_detail_src, ols_detail_dst)

        ols_ssl_src = os.path.join(configs_dir, 'openlitespeed', 'detail', 'ssl', '{}.conf'.format(site_name))
        if os.path.exists(ols_ssl_src):
            ols_ssl_dst = '{}/openlitespeed/detail/ssl/{}.conf'.format(vhost, site_name)
            shutil.copy2(ols_ssl_src, ols_ssl_dst)

        # --- Proxy / Extension / Dir_auth ---
        for server in ['nginx', 'apache']:
            proxy_src = os.path.join(configs_dir, server, 'proxy', site_name)
            if os.path.exists(proxy_src):
                proxy_dst = '{}/{}/proxy/{}'.format(vhost, server, site_name)
                if os.path.exists(proxy_dst):
                    shutil.rmtree(proxy_dst, ignore_errors=True)
                shutil.copytree(proxy_src, proxy_dst, dirs_exist_ok=True)

            extension_src = os.path.join(configs_dir, server, 'extension', site_name)
            if os.path.exists(extension_src):
                ext_dst = '{}/{}/extension/{}'.format(vhost, server, site_name)
                if os.path.exists(ext_dst):
                    shutil.rmtree(ext_dst, ignore_errors=True)
                shutil.copytree(extension_src, ext_dst, dirs_exist_ok=True)

            dir_auth_src = os.path.join(configs_dir, server, 'dir_auth', site_name)
            if os.path.exists(dir_auth_src):
                dir_auth_dst = '{}/{}/dir_auth/{}'.format(vhost, server, site_name)
                if os.path.exists(dir_auth_dst):
                    shutil.rmtree(dir_auth_dst, ignore_errors=True)
                shutil.copytree(dir_auth_src, dir_auth_dst, dirs_exist_ok=True)

        # --- Rewrite ---
        rewrite_src = os.path.join(configs_dir, 'rewrite', 'node_{}.conf'.format(site_name))
        if os.path.exists(rewrite_src):
            rewrite_dst = '{}/rewrite/node_{}.conf'.format(vhost, site_name)
            shutil.copy2(rewrite_src, rewrite_dst)

        rewrite_dir = os.path.join(configs_dir, 'rewrite')
        if os.path.exists(rewrite_dir):
            for f in os.listdir(rewrite_dir):
                if f.endswith('.conf') and site_name in f:
                    src = os.path.join(rewrite_dir, f)
                    dst = os.path.join(vhost, 'rewrite', f)
                    shutil.copy2(src, dst)

        # --- SSL Cert ---
        cert_src = os.path.join(configs_dir, 'cert', site_name)
        if os.path.exists(cert_src):
            cert_dst = os.path.join(vhost, 'cert', site_name)
            if os.path.exists(cert_dst):
                shutil.rmtree(cert_dst, ignore_errors=True)
            shutil.copytree(cert_src, cert_dst, dirs_exist_ok=True)

        # --- Start script ---
        script_src = os.path.join(configs_dir, 'scripts', '{}.sh'.format(site_name))
        if os.path.exists(script_src):
            script_dst = '{}/vhost/scripts/{}.sh'.format(self.nodejs_path, site_name)
            script_dir = os.path.dirname(script_dst)
            if not os.path.exists(script_dir):
                os.makedirs(script_dir, 0o755, exist_ok=True)
            shutil.copy2(script_src, script_dst)
            public.set_own(script_dst, 'www', 'www')
            public.set_mode(script_dst, 755)

        public.serviceReload()

    # 域名还原
    def _restore_nodejs_domains(self, site_id: int, site_name: str, domain_list: list) -> None:
        from projectModelV2.nodejsModel import main as nodejsModel
        model = nodejsModel()

        # 预检：过滤可用域名（未被其他站点占用）
        usable_domains = []
        for info in domain_list:
            name = info.get('name', '')
            if not name:
                continue
            owner = public.M('domain').where('name=?', (name,)).field('pid').find()
            if owner and isinstance(owner, dict) and site_id != owner.get('pid'):
                continue
            usable_domains.append(info)
        if not usable_domains:
            return

        # 待添加域名集合
        to_add_set = {
            (info.get('name'), int(info.get('port', 80)))
            for info in domain_list if info.get('name')
        }

        # 1. 删除现有域名（跳过待添加列表中的）
        existing = public.M('domain').where('pid=?', (site_id,)).field('name,port').select()
        del_error = []
        if isinstance(existing, list):
            for d in existing:
                if (d['name'], int(d.get('port', 80))) in to_add_set:
                    continue
                try:
                    domain_str = '{}:{}'.format(d['name'], d.get('port', 80))
                    get = public.to_dict_obj({
                        'project_name': site_name,
                        'domain': domain_str
                    })
                    res = model.project_remove_domain(get)
                    if isinstance(res, dict) and res.get('status') == -1:
                        del_error.append({'domain': d['name'], 'port': int(d.get('port', 80))})
                except Exception:
                    del_error.append({'domain': d['name'], 'port': int(d.get('port', 80))})

        # 2. 逐个添加可用域名
        for info in usable_domains:
            name = info.get('name', '')
            if not name:
                continue
            try:
                get = public.to_dict_obj({
                    'project_name': site_name,
                    'domains': ['{}:{}'.format(name, info.get('port', 80))]
                })
                model.project_add_domain(get)
            except Exception:
                pass

        # 3. 重试删除失败的域名
        if del_error:
            for error_item in del_error:
                if (error_item['domain'], error_item['port']) not in to_add_set:
                    try:
                        domain_str = '{}:{}'.format(error_item['domain'], error_item['port'])
                        get = public.to_dict_obj({
                            'project_name': site_name,
                            'domain': domain_str
                        })
                        model.project_remove_domain(get)
                    except Exception:
                        pass

    # 安装nodejs版本并附加PM2、指定包管理器模块
    def _install_nodejs_with_modules(self, version: str, package_manager: str = 'npm') -> dict:
        """
        安装指定Node.js版本，随后安装PM2和指定包管理器并设为默认
        """
        try:
            plugin_path = '/www/server/panel/plugin/nodejs'
            if plugin_path not in sys.path:
                sys.path.insert(0, plugin_path)
            from plugin.nodejs.nodejs_main import nodejs_main
            node_obj = nodejs_main()

            get = public.dict_obj()
            get.version = version

            # 1. 安装Node.js
            install_res = node_obj.install_nodejs(get)
            if not install_res.get('status') and 'already installed' not in install_res.get('error_msg'):
                return install_res

            # 2. 安装PM2模块
            pm2_get = public.dict_obj()
            pm2_get.version = version
            pm2_get.module = 'pm2'
            pm2_res = node_obj.install_module(pm2_get)
            if not pm2_res.get('status') and 'has been installed!' not in pm2_res.get('error_msg'):
                return pm2_res

            # 3. 安装指定包管理器（npm内置，无需额外安装）
            if package_manager in ('yarn', 'pnpm'):
                mgr_get = public.dict_obj()
                mgr_get.version = version
                mgr_get.module = package_manager
                mgr_res = node_obj.install_module(mgr_get)
                if not mgr_res.get('status') and 'has been installed!' not in mgr_res.get('error_msg'):
                    return mgr_res

            # 4. 设置为默认版本
            default_get = public.dict_obj()
            default_get.version = version
            default_res = node_obj.set_default_env(default_get)
            return default_res
        except Exception as ex:
            return {'status': False, 'error_msg': str(ex), 'data': {}}
