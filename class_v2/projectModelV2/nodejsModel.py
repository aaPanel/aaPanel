# coding: utf-8
# -------------------------------------------------------------------
# aaPanel
# -------------------------------------------------------------------
# Copyright (c) 2015-2099 aaPanel(www.aapanel.com) All rights reserved.
# -------------------------------------------------------------------
# Author: hwliang <hwl@aapanel.com>
# -------------------------------------------------------------------

# ------------------------------
# node.js模型
# ------------------------------
import os, sys, re, json, shutil, psutil, time, hashlib
from time import process_time_ns
from urllib.parse import urlparse

from projectModelV2.base import projectBase
import public
from public.validate import Param

try:
    from BTPanel import cache
except:
    pass


class main(projectBase):
    _panel_path = public.get_panel_path()
    _nodejs_plugin_path = public.get_plugin_path('nodejs')
    _nodejs_path = '{}/nodejs'.format(public.get_setup_path())
    _log_name = 'Project management'
    _npm_exec_log = '{}/logs/npm-exec.log'.format(_panel_path)
    _node_pid_path = '{}/vhost/pids'.format(_nodejs_path)
    _node_logs_path = '{}/vhost/logs'.format(_nodejs_path)
    _node_run_scripts = '{}/vhost/scripts'.format(_nodejs_path)
    _pids = None
    _mount_cache = None          # 系统/NVM node 挂载结果缓存（类级，跨请求生效）
    _mount_cache_time = 0        # 缓存时间戳
    _vhost_path = '{}/vhost'.format(_panel_path)
    _www_home = '/home/www'
    _node_logs = '{}/vhost/logs'.format(_nodejs_path)

    def __init__(self):
        if not os.path.exists(self._node_run_scripts):
            os.makedirs(self._node_run_scripts, 493)

        if not os.path.exists(self._node_pid_path):
            os.makedirs(self._node_pid_path, 493)

        if not os.path.exists(self._node_logs_path):
            os.makedirs(self._node_logs_path, 493)

        if not os.path.exists(self._www_home):
            os.makedirs(self._www_home, 493)
            public.set_own(self._www_home, 'www')

    def get_exec_logs(self, get):
        '''
            @name 获取执行日志
            @author hwliang<2021-08-09>
            @param get<dict_obj>
            @return string
        '''
        if not os.path.exists(self._npm_exec_log): return public.returnMsg(False, 'NODE_NOT_EXISTS')
        return public.return_message(0, 0, public.GetNumLines(self._npm_exec_log, 20))

    def get_project_list(self, get):
        '''
            @name 获取项目列表（支持全局流量排序）
        '''
        try:
            get.validate([
                Param('search').String(),
                Param('limit').Integer(),
                Param('p').Integer(),
            ], [
                public.validate.trim_filter(),
            ])
        except Exception as ex:
            public.print_log("error info: {}".format(ex))
            return public.return_message(-1, 0, str(ex))

        p = int(get.get('p', 1))
        limit = int(get.get('limit', 20))
        search_word = get.get('search', '').strip()
        re_order = get.get('re_order', '')  # 流量排序专用
        order_str = get.get('order', 'id desc')

        where_str = "project_type=?"
        where_args = ["Node"]

        if search_word:
            where_str += " AND (name LIKE ? OR ps LIKE ?)"
            search_pattern = "%{}%".format(search_word)
            where_args.extend([search_pattern, search_pattern])

        all_data = public.M('sites').where(where_str, tuple(where_args)).order(order_str).select()

        if not all_data:
            return public.return_message(0, 0, {'data': [], 'page': ''})

        # 获取流量数据
        re_data = None
        if re_order:
            import data_v2
            res = data_v2.data().get_site_request(public.to_dict_obj({'site_type': 'Node'}))
            if res.get('status') == 0:
                re_data = res.get('message')

        for i in range(len(all_data)):
            all_data[i] = self.get_project_stat(all_data[i])

            all_data[i]['re_total'] = 0
            if re_data and all_data[i]['name'] in re_data:
                all_data[i]['re_total'] = re_data[all_data[i]['name']]['total']['request']

        # 批量获取备份信息
        site_ids = [item['id'] for item in all_data]
        if site_ids:
            backup_info_map = {
                j['pid']: j for j in
                public.S('backup').where_in('pid', site_ids).where('type=?', ('0',))
                .group('pid').field('pid,count(*) as cnt,max(addtime) as last_backup_time').select()
            }
            for item in all_data:
                info = backup_info_map.get(item['id'], {})
                item['backup_count'] = info.get('cnt', 0)
                item['last_backup_time'] = info.get('last_backup_time', '')

        if re_order:
            is_reverse = True if re_order == 'desc' else False
            all_data = sorted(all_data, key=lambda x: x.get('re_total', 0), reverse=is_reverse)

        count = len(all_data)
        start = (p - 1) * limit
        end = start + limit
        paged_data = all_data[start:end]

        data = public.get_page(count, p, limit, get.get('callback', ''))
        data['data'] = paged_data

        return public.return_message(0, 0, data)

    def get_ssl_end_date(self, project_name):
        '''
            @name 获取SSL信息
            @author hwliang<2021-08-09>
            @param project_name <string> 项目名称
            @return dict
        '''
        import data
        return data.data().get_site_ssl_info('node_{}'.format(project_name))

    def is_install_nodejs(self, get):
        '''
            @name 是否安装nodejs版本管理器
            @author hwliang<2021-08-09>
            @param get<dict_obj> 请求数据
            @return bool
        '''
        return_message = os.path.exists(self._nodejs_plugin_path)
        return public.return_message(0, 0, return_message)

    def _is_install_nodejs(self, get):
        '''
            @name 是否安装nodejs版本管理器
            @author hwliang<2021-08-09>
            @param get<dict_obj> 请求数据
            @return bool
        '''
        return os.path.exists(self._nodejs_plugin_path)

    def get_nodejs_version(self, get):
        '''
            @name 获取已安装的nodejs版本
            @author hwliang<2021-08-09>
            @param get<dict_obj> 请求数据
            @return list
        '''
        nodejs_list = []
        if not os.path.exists(self._nodejs_path): return public.return_message(0, 0, nodejs_list)
        for v in os.listdir(self._nodejs_path):
            if v[0] != 'v' or v.find('.') == -1: continue
            node_path = os.path.join(self._nodejs_path, v)
            node_bin = '{}/bin/node'.format(node_path)
            if not os.path.exists(node_bin):
                if os.path.exists(node_path + '/bin'):
                    public.ExecShell('rm -rf {}'.format(node_path))
                continue
            nodejs_list.append(v)
        # 排序:面板版本在前，系统/NVM后缀版本在后（顺带稳定默认版本选取）
        nodejs_list.sort(key=lambda v: (1 if '-' in v else 0,
                                        tuple(map(int, re.findall(r'\d+', v)))))
        return public.return_message(0, 0, nodejs_list)

    # 版本运行时管理（系统/NVM node 扫描与汇总）
    # 插件 nodejs 只管理面板安装版本 系统/NVM 版本由面板侧统一管理
    def scan_system_nodes(self, get):
        '''
            @name 扫描系统与NVM安装的node版本并入面板管理
            @param get<dict_obj>
            @return dict {data, created, skipped}
        '''
        from mod.project.nodejs.base import NodeJs
        res = NodeJs().scan_system_nodes(get)
        # 主动扫描 = 最新结果，刷新挂载缓存
        main._mount_cache = res
        main._mount_cache_time = time.time()
        public.set_module_logs("node_site_nvm", "scan_system_nodes")
        return res

    def _ensure_node_runtime_mounted(self):
        '''
            @name 确保系统/NVM node 已挂载 60s缓存
            node -v / which / npm root -g 等慢操作
        '''
        if main._mount_cache_time and time.time() - main._mount_cache_time < 60:
            return main._mount_cache
        try:
            from mod.project.nodejs.base import NodeJs
            res = NodeJs().scan_system_nodes(public.to_dict_obj({}))
        except:
            res = None
        main._mount_cache = res
        main._mount_cache_time = time.time()
        return res

    def get_node_runtime_list(self, get):
        '''
            @name 汇总已管理版本（面板安装 + 系统/NVM）
            @param get<dict_obj>
            @return dict {data: [{version, source, path}]}
        '''
        from mod.project.nodejs.base import NodeJs
        return NodeJs().get_node_runtime_list(get)

    def set_default_node_version(self, get):
        '''
            @name 切换命令行默认 node（which node）到指定版本
            @param get<dict_obj> {version: 'v24.15.0' | 'v22.14.0-nvm-root'}
            @return dict
        '''
        from mod.project.nodejs.base import NodeJs
        public.set_module_logs("node_site", "set_default_node_version")
        return NodeJs().set_default_node_version(get)

    def remove_extra_node(self, get):
        '''
            @name 卸载系统/NVM版本（仅删软链目录，不影响真实node）
            @param get<dict_obj> {version: 'v24.19.0-system'}
            @return dict
        '''
        from mod.project.nodejs.base import NodeJs
        return NodeJs().remove_extra_node(get)

    def get_nvm_env_info(self, get):
        '''
            @name 获取 System NVM 环境信息
            @param get<dict_obj>
            @return dict {nvm_dir, current_version, installed, source, source_url}
        '''
        from mod.project.nodejs.base import NodeJs
        public.set_module_logs("node_site_nvm", "get_nvm_env_info")
        return NodeJs().get_nvm_env_info(get)

    def switch_nvm_default_version(self, get):
        '''
            @name 切换 NVM 环境默认版本
            @param get<dict_obj> {version: 'v22.14.0'}
            @return dict
        '''
        from mod.project.nodejs.base import NodeJs
        public.set_module_logs("node_site_nvm", "switch_nvm_default_version")
        return NodeJs().switch_nvm_default_version(get)

    def set_nvm_config(self, get):
        '''
            @name 设置 NVM 下载源（可选 version 同时切换环境默认版本）
            @param get<dict_obj> {source: 'npmmirror', custom_url: '', version?: 'v22.18.0'}
            @return dict
        '''
        from mod.project.nodejs.base import NodeJs
        public.set_module_logs("node_site_nvm", "set_nvm_config")
        return NodeJs().set_nvm_config(get)

    def install_nvm_node(self, get):
        '''
            @name 异步通过 root NVM 安装新版本 node
            @param get<dict_obj> {version: 'v22.18.0', source?: '', custom_url?: '', switch_nvm?: '1'}
            switch_nvm=1 安装成功同时切换 NVM 环境默认版本
            @return dict
        '''
        from mod.project.nodejs.base import NodeJs
        public.set_module_logs("node_site_nvm", "install_nvm_node")
        return NodeJs().install_nvm_node(get)

    def get_nvm_online_versions(self, get):
        '''
            @name 获取 NVM 可安装版本列表（来自下载源 index.json，每个大版本只留最新稳定版）
            @param get<dict_obj> {force?: '1'}
            @return list [{version, lts, npm}]
        '''
        from mod.project.nodejs.base import NodeJs
        return NodeJs().get_nvm_online_versions(get)

    def get_nvm_install_status(self, get):
        '''
            @name 查询 NVM 异步安装任务状态（安装完成后自动触发扫描）
            @param get<dict_obj>
            @return dict {status: idle|running|success|failed, version, message, scan?, started_at, finished_at}
        '''
        from mod.project.nodejs.base import NodeJs
        return NodeJs().get_nvm_install_status(get)

    def get_package_manager_info(self, get):
        '''
            @name 获取指定 node 版本下各包管理器的实际版本与存在状态
            @param get<dict_obj> {nodejs_version: 'v22.14.0-nvm-root'}
            @return dict {data: [{name, version, detected, path}]}
            detected 表示该版本 bin 下是否存在此包管理器（软链也算，跟随真实路径）
            面板版本直接探测 bin 下命令；系统/NVM 版本探测其 bin 软链（指向真实 npm/pnpm/yarn）
        '''
        nodejs_version = get.get('nodejs_version', '')
        if not nodejs_version:
            return public.return_message(-1, 0, public.lang(
                'The "nodejs_version" parameter cannot be left blank.'))
        node_dir = '{}/{}'.format(self._nodejs_path, nodejs_version)
        if not os.path.exists(node_dir):
            return public.return_message(-1, 0, public.lang(
                'This version does not exist: {}'.format(nodejs_version)))
        bin_dir = os.path.join(node_dir, 'bin')
        result = []
        for name in ('pnpm', 'yarn','npm'):
            pkg_bin = os.path.join(bin_dir, name)
            version = ''
            if os.path.exists(pkg_bin):
                # PATH 前缀让 npm/pnpm/yarn 由其所属 node 解释（系统 npm 依赖该系统 node）
                try:
                    ver_out = public.ExecShell(
                        'PATH="{}:$PATH" "{}" -v 2>/dev/null'.format(bin_dir, pkg_bin))[0].strip()
                    if ver_out:
                        version = ver_out
                except:
                    pass
            result.append({
                'name': name,
                'version': version,
                'detected': bool(version),
                'path': pkg_bin if os.path.exists(pkg_bin) else '',
            })
        return public.return_message(0, 0, result)

    def get_run_list(self, get):
        '''
            @name 获取node项目启动列表
            @author hwliang<2021-08-10>
            @param get<dict_obj>{
                project_cwd: string<项目目录>
            }
        '''  # 校验参数
        try:
            get.validate([
                Param('project_cwd').String(),
            ], [
                public.validate.trim_filter(),
            ])
        except Exception as ex:
            public.print_log("error info: {}".format(ex))
            return public.return_message(-1, 0, str(ex))

        project_cwd = get.project_cwd.strip()
        if not os.path.exists(project_cwd):
            return_message = public.return_error(public.lang('The project directory does not exist!'))
            del return_message['status']
            return public.return_message(-1, 0, return_message)
        package_file = '{}/package.json'.format(project_cwd)
        if not os.path.exists(package_file): return public.return_message(0, 0, {})

        package_content = public.readFile(package_file)
        if not package_content:
            return public.return_message(0, 0, {})

        try:
            package_info = json.loads(package_content)
        except json.JSONDecodeError:
            return public.return_message(0, 0, {})

        # package_info = json.loads(public.readFile(package_file))

        if not 'scripts' in package_info: return public.return_message(0, 0, {})
        if not package_info['scripts']: return public.return_message(0, 0, {})
        return public.return_message(0, 0, package_info['scripts'])

    def get_npm_bin(self, nodejs_version):
        '''
            @name 获取指定node版本的npm路径
            @author hwliang<2021-08-10>
            @param nodejs_version<string> nodejs版本
            @return string
        '''
        npm_path = '{}/{}/bin/npm'.format(self._nodejs_path, nodejs_version)
        if not os.path.exists(npm_path): return False
        return npm_path

    def get_yarn_bin(self, nodejs_version):
        '''
            @name 获取指定node版本的yarn路径
            @author hwliang<2021-08-28>
            @param nodejs_version<string> nodejs版本
            @return string
        '''
        yarn_path = '{}/{}/bin/yarn'.format(self._nodejs_path, nodejs_version)
        if not os.path.exists(yarn_path): return False
        return yarn_path

    def get_pnpm_bin(self, nodejs_version):
        '''
            @name 获取指定node版本的pnpm路径
            @param nodejs_version<string> nodejs版本
            @return string
        '''
        pnpm_path = '{}/{}/bin/pnpm'.format(self._nodejs_path, nodejs_version)
        if not os.path.exists(pnpm_path): return False
        return pnpm_path

    def get_node_bin(self, nodejs_version):
        '''
            @name 获取指定node版本的node路径
            @author hwliang<2021-08-10>
            @param nodejs_version<string> nodejs版本
            @return string
        '''
        node_path = '{}/{}/bin/node'.format(self._nodejs_path, nodejs_version)
        if not os.path.exists(node_path): return False
        return node_path

    def get_last_env(self, nodejs_version, project_cwd=None):
        '''
            @name 获取前置环境变量
            @author hwliang<2021-08-25>
            @param nodejs_version<string> Node版本
            @return string
        '''
        nodejs_bin_path = '{}/{}/bin'.format(self._nodejs_path, nodejs_version)
        if project_cwd:
            _bin = '{}/node_modules/.bin'.format(project_cwd)
            if os.path.exists(_bin):
                nodejs_bin_path = _bin + ':' + nodejs_bin_path

        last_env = '''PATH={nodejs_bin_path}:/bin:/sbin:/usr/bin:/usr/sbin:/usr/local/bin:/usr/local/sbin:~/bin
export PATH
'''.format(nodejs_bin_path=nodejs_bin_path)
        return last_env

    def install_packages(self, get):
        '''
            @name 安装指定项目的依赖包
            @author hwliang<2021-08-10>
            @param get<dict_obj>{
                project_name: string<项目名称>
            }
            return dict
        '''
        # 校验参数
        try:
            get.validate([
                Param('project_name').String(),
            ], [
                public.validate.trim_filter(),
            ])
        except Exception as ex:
            public.print_log("error info: {}".format(ex))
            return public.return_message(-1, 0, str(ex))

        project_find = self.get_project_find(get.project_name)
        if not project_find:
            return_message = public.return_error(public.lang('The specified item does not exist!'))
            del return_message['status']
            return public.return_message(-1, 0, return_message)
        if not os.path.exists(project_find['path']):
            return_message = public.return_error(public.lang('The project directory does not exist!'))
            del return_message['status']
            return public.return_message(-1, 0, return_message)
        package_file = '{}/package.json'.format(project_find['path'])
        if not os.path.exists(package_file):
            return_message = public.return_error(
                public.lang('The package.json configuration file was not found in the project directory!'))
            del return_message['status']
            return public.return_message(-1, 0, return_message)
        nodejs_version = project_find['project_config']['nodejs_version']

        package_lock_file = '{}/package-lock.json'.format(project_find['path'])
        node_modules_path = '{}/node_modules'.format(project_find['path'])

        # 已经安装过的依赖包的情况下，可能存在不同node版本导致的问题，可能需要重新构建依赖包
        rebuild = False
        if os.path.exists(package_lock_file) and os.path.exists(node_modules_path):
            rebuild = True

        npm_bin = self.get_npm_bin(nodejs_version)
        yarn_bin = self.get_yarn_bin(nodejs_version)
        if not npm_bin and not yarn_bin:
            return_message = public.return_error(public.lang('The specified nodejs version does not exist!'))
            del return_message['status']
            return public.return_message(-1, 0, return_message)
        public.writeFile(self._npm_exec_log, "Installing dependencies...\n")
        public.writeFile(self._npm_exec_log, "Downloading dependency package, please wait...\n")
        if yarn_bin:
            if os.path.exists(package_lock_file):
                os.remove(package_lock_file)
            public.ExecShell(
                self.get_last_env(nodejs_version) + "cd {} && {} install >> {} 2>&1".format(project_find['path'],
                                                                                            yarn_bin,
                                                                                            self._npm_exec_log))
        else:
            public.ExecShell(
                self.get_last_env(nodejs_version) + "cd {} && {} install >> {} 2>&1".format(project_find['path'],
                                                                                            npm_bin,
                                                                                            self._npm_exec_log))
        public.writeFile(self._npm_exec_log, "|-Successify --- Command executed! ---", 'a+')
        public.WriteLog(self._log_name,
                        'Node project: {}, the installation of the dependency package is complete!'.format(
                            project_find['name']))
        if rebuild:  # 重新构建已安装模块
            self.rebuild_project(get.project_name)
        return_message = public.return_data(True, 'The dependency package is installed successfully!')
        del return_message['status']
        return public.return_message(0, 0, return_message)

    def update_packages(self, get):
        '''
            @name 更新指定项目的依赖包
            @author hwliang<2021-08-10>
            @param get<dict_obj>{
                project_name: string<项目名称>
            }
            return dict
        '''
        project_find = self.get_project_find(get.project_name)
        if not project_find:
            return_message = public.return_error(public.lang('The specified item does not exist!'))
            del return_message['status']
            return public.return_message(-1, 0, return_message)
        if not os.path.exists(project_find['path']):
            return_message = public.return_error(public.lang('The project directory does not exist!'))
            del return_message['status']
            return public.return_message(-1, 0, return_message)
        package_file = '{}/package.json'.format(project_find['path'])
        if not os.path.exists(package_file):
            return_message = public.return_error(
                public.lang('The package.json configuration file was not found in the project directory!'))
            del return_message['status']
            return public.return_message(-1, 0, return_message)
        package_lock_file = '{}/package-lock.json'.format(project_find['path'])
        if not os.path.exists(package_lock_file):
            return_message = public.return_error(public.lang('Please install the dependency package first!'))
            del return_message['status']
            return public.return_message(-1, 0, return_message)
        nodejs_version = project_find['project_config']['nodejs_version']
        npm_bin = self.get_npm_bin(nodejs_version)
        if not npm_bin:
            return_message = public.return_error(public.lang('The specified nodejs version does not exist!'))
            del return_message['status']
            return public.return_message(-1, 0, return_message)

        public.ExecShell(
            self.get_last_env(nodejs_version) + "cd {} && {} update &> {}".format(project_find['path'], npm_bin,
                                                                                  self._npm_exec_log))
        public.WriteLog(self._log_name, 'Project [{}] update all dependent packages'.format(get.project_name))
        return_message = public.return_data(True, 'Dependent package updated successfully!')
        del return_message['status']
        return public.return_message(0, 0, return_message)

    def reinstall_packages(self, get):
        '''
            @name 重新安装指定项目的依赖包
            @author hwliang<2021-08-10>
            @param get<dict_obj>{
                project_name: string<项目名称>
            }
            return dict
        '''

        project_find = self.get_project_find(get.project_name)
        if not project_find:
            return_message = public.return_error(public.lang('The specified item does not exist!'))
            del return_message['status']
            return public.return_message(-1, 0, return_message)
        if not os.path.exists(project_find['path']):
            return_message = public.return_error(public.lang('The project directory does not exist!'))
            del return_message['status']
            return public.return_message(-1, 0, return_message)
        package_file = '{}/package.json'.format(project_find['path'])
        if not os.path.exists(package_file):
            return_message = public.return_error(
                public.lang('The package.json configuration file was not found in the project directory!'))
            del return_message['status']
            return public.return_message(-1, 0, return_message)

        package_lock_file = '{}/package-lock.json'.format(project_find['path'])
        if os.path.exists(package_lock_file): os.remove(package_lock_file)
        package_path = '{}/node_modules'
        if os.path.exists(package_path): shutil.rmtree(package_path)
        nodejs_version = project_find['project_config']['nodejs_version']
        npm_bin = self.get_npm_bin(nodejs_version)
        if not npm_bin:
            return_message = public.return_error(public.lang('The specified nodejs version does not exist!'))
            del return_message['status']
            return public.return_message(-1, 0, return_message)
        public.WriteLog(self._log_name, 'Node project: {}, all dependent packages have been reinstalled')
        public.ExecShell(
            self.get_last_env(nodejs_version) + "cd {} && {} install &> {}".format(project_find['path'], npm_bin,
                                                                                   self._npm_exec_log))
        return_message = public.return_data(True, 'Dependent package reinstalled successfully!')
        del return_message['status']
        return public.return_message(0, 0, return_message)

    def get_project_modules(self, get):
        '''
            @name 获取指定项目的依赖包列表
            @author hwliang<2021-08-10>
            @param get<dict_obj>{
                project_name: string<项目名称>
                project_cwd: string<项目目录> 可选
            }
            return list
        '''
        # 校验参数
        try:
            get.validate([
                Param('project_name').String(),
                Param('project_cwd').String(),
            ], [
                public.validate.trim_filter(),
            ])
        except Exception as ex:
            public.print_log("error info: {}".format(ex))
            return public.return_message(-1, 0, str(ex))

        if not 'project_cwd' in get:
            project_find = self.get_project_find(get.project_name)
            if not project_find:
                return_message = public.return_error(public.lang('The specified item does not exist!'))
                del return_message['status']
                return public.return_message(-1, 0, return_message)
            project_cwd = project_find['path']
        else:
            project_cwd = get.project_cwd
        mod_path = os.path.join(project_cwd, 'node_modules')
        modules = []
        if not os.path.exists(mod_path): return public.return_message(0, 0, modules)
        for mod_name in os.listdir(mod_path):
            try:
                mod_pack_file = os.path.join(mod_path, mod_name, 'package.json')
                if not os.path.exists(mod_pack_file): continue
                mod_pack_info = json.loads(public.readFile(mod_pack_file))
                pack_info = {
                    "name": mod_name,
                    "version": mod_pack_info['version'],
                    "description": mod_pack_info['description'],
                    "license": mod_pack_info['license'] if 'license' in mod_pack_info else 'NULL',
                    "homepage": mod_pack_info['homepage']
                }
                modules.append(pack_info)
            except:
                continue
        return public.return_message(0, 0, modules)

    def install_module(self, get):
        '''
            @name 安装指定模块
            @author hwliang<2021-08-10>
            @param get<dict_obj>{
                project_name: string<项目名称>
                mod_name: string<模块名称>
            }
            @return dict
        '''

        project_find = self.get_project_find(get.project_name)
        if not project_find:
            return_message = public.return_error(public.lang('The specified item does not exist!'))
            del return_message['status']
            return public.return_message(-1, 0, return_message)
        project_cwd = project_find['path']

        mod_name = get.mod_name
        filename = '{}/node_modules/{}/package.json'.format(project_cwd, mod_name)
        if os.path.exists(filename):
            return_message = public.return_error(public.lang('The specified module has been installed!'))
            del return_message['status']
            return public.return_message(-1, 0, return_message)

        nodejs_version = project_find['project_config']['nodejs_version']
        npm_bin = self.get_npm_bin(nodejs_version)
        yarn_bin = self.get_yarn_bin(nodejs_version)

        if not npm_bin and not yarn_bin:
            return_message = public.return_error(public.lang('The specified nodejs version does not exist!'))
            del return_message['status']
            return public.return_message(-1, 0, return_message)
        if yarn_bin:
            public.ExecShell(
                self.get_last_env(nodejs_version) + "cd {} && {} add {} &> {}".format(project_find['path'], yarn_bin,
                                                                                      mod_name, self._npm_exec_log))
        else:
            public.ExecShell(
                self.get_last_env(nodejs_version) + "cd {} && {} install {} &> {}".format(project_find['path'], npm_bin,
                                                                                          mod_name, self._npm_exec_log))
        if not os.path.exists(filename):
            return_message = public.return_error(public.lang('Failed to install the specified module!'))
            del return_message['status']
            return public.return_message(-1, 0, return_message)
        public.WriteLog(self._log_name,
                        'Node project {}, {} module installation is complete!'.format(get.project_name, mod_name))
        return_message = public.return_data(True, 'Successful installation!')
        del return_message['status']
        return public.return_message(0, 0, return_message)

    def uninstall_module(self, get):
        '''
            @name 卸载指定模块
            @author hwliang<2021-04-08>
            @param get<dict_obj>{
                project_name: string<项目名称>
                mod_name: string<模块名称>
            }
            @return dict
        '''
        # 校验参数
        try:
            get.validate([
                Param('project_name').String(),
                Param('mod_name').String(),
            ], [
                public.validate.trim_filter(),
            ])
        except Exception as ex:
            public.print_log("error info: {}".format(ex))
            return public.return_message(-1, 0, str(ex))

        project_find = self.get_project_find(get.project_name)
        if not project_find:
            return_message = public.return_error(public.lang('The specified item does not exist!'))
            del return_message['status']
            return public.return_message(-1, 0, return_message)
        project_cwd = project_find['path']

        mod_name = get.mod_name
        filename = '{}/node_modules/{}/package.json'.format(project_cwd, mod_name)
        if not os.path.exists(filename):
            return_message = public.return_error(public.lang('The specified module is not installed!'))
            del return_message['status']
            return public.return_message(-1, 0, return_message)

        nodejs_version = project_find['project_config']['nodejs_version']
        npm_bin = self.get_npm_bin(nodejs_version)
        yarn_bin = self.get_yarn_bin(nodejs_version)
        if not npm_bin and not yarn_bin:
            return_message = public.return_error(public.lang('The specified nodejs version does not exist!'))
            del return_message['status']
            return public.return_message(-1, 0, return_message)
        if yarn_bin:
            result = public.ExecShell(
                self.get_last_env(nodejs_version) + "cd {} && {} remove {}".format(project_find['path'], yarn_bin,
                                                                                   mod_name))
        else:
            result = public.ExecShell(
                self.get_last_env(nodejs_version) + "cd {} && {} uninstall {}".format(project_find['path'], npm_bin,
                                                                                      mod_name))
        if os.path.exists(filename):
            result = "\n".join(result)
            if result.find('looking for funding') != -1:
                return_message = public.return_error(
                    public.lang("This module is dependent on other installed modules and cannot be uninstalled!"))
                del return_message['status']
                return public.return_message(-1, 0, return_message)
            return_message = public.return_error(public.lang("Unable to uninstall this module!"))
            del return_message['status']
            return public.return_message(-1, 0, return_message)

        public.WriteLog(self._log_name,
                        'Node project {}, {} module uninstallation completed!'.format(get.project_name, mod_name))
        return_message = public.return_data(True, 'Module unloaded successfully!')
        del return_message['status']
        return public.return_message(0, 0, return_message)

    def upgrade_module(self, get):
        '''
            @name 更新指定模块
            @author hwliang<2021-08-10>
            @param get<dict_obj>{
                project_name: string<项目名称>
                mod_name: string<模块名称>
            }
            @return dict
        '''
        # 校验参数
        try:
            get.validate([
                Param('project_name').String(),
                Param('mod_name').String(),
            ], [
                public.validate.trim_filter(),
            ])
        except Exception as ex:
            public.print_log("error info: {}".format(ex))
            return public.return_message(-1, 0, str(ex))

        project_find = self.get_project_find(get.project_name)
        if not project_find:
            return_message = public.return_error(public.lang('The specified item does not exist!'))
            del return_message['status']
            return public.return_message(-1, 0, return_message)
        project_cwd = project_find['path']

        mod_name = get.mod_name
        filename = '{}/node_modules/{}/package.json'.format(project_cwd, mod_name)
        if not os.path.exists(filename):
            return_message = public.return_error(public.lang('The specified module is not installed!'))
            del return_message['status']
            return public.return_message(-1, 0, return_message)
        nodejs_version = project_find['project_config']['nodejs_version']
        npm_bin = self.get_npm_bin(nodejs_version)

        if not npm_bin:
            return_message = public.return_error(public.lang('The specified nodejs version does not exist!'))
            del return_message['status']
            return public.return_message(-1, 0, return_message)
        public.ExecShell(
            self.get_last_env(nodejs_version) + "cd {} && {} update {} &> {}".format(project_find['path'], npm_bin,
                                                                                     mod_name, self._npm_exec_log))
        public.WriteLog(self._log_name,
                        'Node project {}, {} module update completed!'.format(get.project_name, mod_name))
        return_message = public.return_data(True, 'Module updated successfully!')
        del return_message['status']
        return public.return_message(0, 0, return_message)

    def _nodejs_error(self, msg):
        return_message = public.return_error(msg)
        if 'status' in return_message: del return_message['status']
        return public.return_message(-1, 0, return_message)

    def _parse_domain_list(self, domains):
        if isinstance(domains, str):
            domains = domains.strip()
            if not domains: return []
            try:
                domains = json.loads(domains)
            except:
                domains = [i.strip() for i in domains.split(',') if i.strip()]
        if not isinstance(domains, list): return []
        return domains

    def _format_and_validate_domains(self, bind_extranet, domains, port=0, require_domains=True):
        try:
            bind_extranet = int(bind_extranet)
        except:
            bind_extranet = 0
        if bind_extranet != 1: return [], ''
        try:
            port = int(port or 0)
        except:
            port = 0
        if port == 0:
            return [], public.lang('Please set the running port for the project first.')
        domains = self._parse_domain_list(domains)
        if require_domains and not domains:
            return [], public.lang('Please add at least one domain name in the [Domain Management] option')
        format_domains = []
        for domain in domains:
            domain = str(domain).strip()
            if not domain:
                return [], public.lang('Domain name cannot be empty')
            if domain.find(':') == -1:
                domain += ':80'
            domain_arr = domain.split(':')
            if len(domain_arr) < 2 or not domain_arr[1]:
                domain = '{}:80'.format(domain_arr[0])
                domain_arr = domain.split(':')
            if domain_arr[1] == '443':
                return [], public.lang('Do not use system ports 443')
            if public.M('domain').where('name=?', (domain_arr[0],)).count():
                return [], 'Domain name already exists: {}'.format(domain)
            format_domains.append(domain)
        return format_domains, ''

    def _get_node_version_owner(self, nodejs_version):
        '''
            @name 读取 node 版本目录的属主（用于 run_user 权限校验）
            优先读标记文件 owner；读不到时从目录名 {version}-{source}-{owner} 解析
            @param nodejs_version<string> 版本目录名，如 v22.14.0-nvm-root
            @return string 属主用户，未知时返回 ''
        '''
        try:
            flag_file = os.path.join(self._nodejs_path, nodejs_version, '.aapanel-node-extra')
            if os.path.exists(flag_file):
                flag = json.loads(public.readFile(flag_file))
                if flag.get('owner'):
                    return str(flag['owner'])
            # 目录名尾段即 owner：v22.14.0-nvm-root -> root
            if '-' in nodejs_version:
                return str(nodejs_version.rsplit('-', 1)[-1])
        except:
            pass
        return ''

    def _normalize_package_manager(self, pkg_manager):
        pkg_manager = str(pkg_manager or 'npm').strip().lower()
        if pkg_manager not in ('npm', 'pnpm', 'yarn'): return 'npm'
        return pkg_manager

    def _get_package_manager_bin(self, nodejs_version, pkg_manager):
        pkg_manager = self._normalize_package_manager(pkg_manager)
        if pkg_manager == 'pnpm': return self.get_pnpm_bin(nodejs_version)
        if pkg_manager == 'yarn': return self.get_yarn_bin(nodejs_version)
        return self.get_npm_bin(nodejs_version)

    def _get_package_manager_run_cmd(self, nodejs_version, pkg_manager, project_script):
        pkg_manager = self._normalize_package_manager(pkg_manager)
        pkg_bin = self._get_package_manager_bin(nodejs_version, pkg_manager)
        if not pkg_bin: return False
        return '{} run {}'.format(pkg_bin, project_script)

    def _normalize_project_name(self, name, pid=0):
        name = str(name or '').strip()
        if name.startswith('@'): name = name[1:]
        name = name.replace('/', '_').replace('\\', '_')
        name = re.sub(r'[^0-9A-Za-z_]+', '_', name)
        name = re.sub(r'_+', '_', name).strip('_')
        if not name:
            name = 'node_project_{}'.format(pid) if pid else 'node_project'
        return name

    def _make_unique_project_name(self, name, existing_names=None, pid=0):
        if existing_names is None: existing_names = set()
        base_name = self._normalize_project_name(name, pid)
        project_name = base_name
        index = 1
        while project_name in existing_names or public.M('sites').where('name=?', (project_name,)).count():
            project_name = '{}_{}'.format(base_name, index)
            index += 1
        return project_name

    def _read_proc_cwd(self, pid):
        try:
            cwd_link = '/proc/{}/cwd'.format(pid)
            if os.path.islink(cwd_link):
                return os.path.realpath(os.readlink(cwd_link))
        except:
            pass
        return ''

    def _read_proc_exe(self, pid):
        try:
            exe_link = '/proc/{}/exe'.format(pid)
            if os.path.islink(exe_link):
                return os.path.realpath(os.readlink(exe_link))
        except:
            pass
        return ''

    def _read_proc_cmdline(self, pid):
        try:
            cmdline_file = '/proc/{}/cmdline'.format(pid)
            if not os.path.exists(cmdline_file): return []
            with open(cmdline_file, 'rb') as fp:
                data = fp.read()
            if not data: return []
            return self._clean_cmdline([i.decode('utf-8', 'ignore') for i in data.split(b'\0') if i])
        except:
            return []

    def _uid_to_username(self, uid):
        try:
            import pwd
            return pwd.getpwuid(int(uid)).pw_name
        except:
            pass
        return str(uid) if uid not in [None, ''] else 'www'

    def _read_proc_status(self, pid):
        status_info = {}
        try:
            status_file = '/proc/{}/status'.format(pid)
            if not os.path.exists(status_file): return status_info
            with open(status_file, 'r') as fp:
                for line in fp:
                    if ':' not in line: continue
                    key, value = line.split(':', 1)
                    status_info[key.strip()] = value.strip()
        except:
            pass
        return status_info

    def _read_process_basic_from_proc(self, pid):
        try:
            if not os.path.exists('/proc/{}'.format(pid)): return {}
            cmdline = self._read_proc_cmdline(pid)
            if not cmdline: return {}
            status_info = self._read_proc_status(pid)
            uid = ''
            if status_info.get('Uid'):
                uid = status_info['Uid'].split()[0]
            return {
                'pid': int(pid),
                'ppid': int(status_info.get('PPid', '0').split()[0]),
                'name': status_info.get('Name', ''),
                'cmdline': cmdline,
                'cwd': self._read_proc_cwd(pid),
                'exe': self._read_proc_exe(pid),
                'user': self._uid_to_username(uid)
            }
        except:
            return {}

    def _read_process_basic(self, pid):
        try:
            p = psutil.Process(int(pid))
            if p.status() == 'zombie': return {}
            with p.oneshot():
                cmdline = self._clean_cmdline(p.cmdline())
                if not cmdline: return {}
                try:
                    cwd = p.cwd()
                except:
                    cwd = self._read_proc_cwd(pid)
                try:
                    exe = p.exe()
                except:
                    exe = self._read_proc_exe(pid)
                return {
                    'pid': int(pid),
                    'ppid': p.ppid(),
                    'name': p.name(),
                    'cmdline': cmdline,
                    'cwd': os.path.realpath(cwd) if cwd else '',
                    'exe': os.path.realpath(exe) if exe else '',
                    'user': p.username()
                }
        except:
            pass
        return self._read_process_basic_from_proc(pid)

    def _clean_cmdline(self, cmdline):
        result = []
        for arg in cmdline:
            arg = str(arg or '').strip()
            if arg:
                result.append(arg)
        return result

    def _detect_package_manager(self, cmdline):
        cmdline = self._normalize_cmdline_args(cmdline)
        manager_map = {
            'npm': ('npm', 'npm-cli', 'npm-cli.js', 'npm.cmd'),
            'pnpm': ('pnpm', 'pnpm.cjs', 'pnpm.js', 'pnpm.cmd'),
            'yarn': ('yarn', 'yarn.js', 'yarnpkg', 'yarnpkg.js', 'yarn.cmd')
        }
        for index, arg in enumerate(cmdline):
            base_name = os.path.basename(str(arg)).lower()
            for manager, names in manager_map.items():
                if base_name in names:
                    return manager, index
        return '', -1

    def _normalize_cmdline_args(self, cmdline):
        result = []
        manager_names = ('npm', 'pnpm', 'yarn', 'node', 'nodejs', 'npm-cli.js', 'pnpm.cjs', 'yarn.js', 'yarnpkg')
        for arg in cmdline:
            arg = str(arg or '').strip()
            if not arg: continue
            parts = arg.split()
            if len(parts) > 1 and os.path.basename(parts[0]).lower() in manager_names:
                result += parts
            else:
                result.append(arg)
        return result

    def _command_args_after_manager(self, cmdline, manager_index):
        cmdline = self._normalize_cmdline_args(cmdline)
        args = [str(i) for i in cmdline[manager_index + 1:]]
        if '--' in args:
            args = args[:args.index('--')]
        options_need_value = ('--prefix', '--userconfig', '--cache', '--registry', '--workspace', '-w', '--dir', '-C')
        index = 0
        while index < len(args):
            arg = args[index]
            if not arg.startswith('-'):
                return args[index:]
            if arg in options_need_value and index + 1 < len(args):
                index += 2
                continue
            index += 1
        return []

    def _parse_package_command(self, cmdline, scripts=None):
        manager, manager_index = self._detect_package_manager(cmdline)
        result = {
            'manager': manager,
            'manager_index': manager_index,
            'args': [],
            'script': ''
        }
        if not manager: return result
        args = self._command_args_after_manager(cmdline, manager_index)
        result['args'] = args
        if not isinstance(scripts, dict) or not scripts or not args:
            return result
        command = args[0]
        if command in ('run', 'run-script') and len(args) > 1:
            script_name = args[1]
            result['script'] = script_name if script_name in scripts else ''
        elif manager in ('pnpm', 'yarn') and command in scripts:
            result['script'] = command
        elif manager == 'npm' and command in ('start', 'test', 'restart', 'stop') and command in scripts:
            result['script'] = command
        return result

    def _find_package_root(self, cwd, max_depth=8):
        if not cwd: return ''
        path = os.path.realpath(cwd)
        for _ in range(max_depth + 1):
            if os.path.exists('{}/package.json'.format(path)):
                return path
            parent = os.path.dirname(path)
            if not parent or parent == path: break
            path = parent
        return ''

    def _read_package_json(self, project_cwd):
        package_file = '{}/package.json'.format(project_cwd)
        if not os.path.exists(package_file): return {}
        package_content = public.readFile(package_file)
        if not package_content: return {}
        try:
            package_info = json.loads(package_content)
            return package_info if isinstance(package_info, dict) else {}
        except:
            return {}

    def _collect_child_pids(self, pid):
        try:
            p = psutil.Process(int(pid))
            pids = [int(pid)]
            for child in p.children(recursive=True):
                try:
                    if child.status() != 'zombie':
                        pids.append(child.pid)
                except:
                    continue
            return sorted(list(set(pids)))
        except:
            if os.path.exists('/proc/{}'.format(pid)): return [int(pid)]
        return []

    def _get_listen_info_by_pids(self, pids):
        listen_info = {}
        listen_status = getattr(psutil, 'CONN_LISTEN', 'LISTEN')
        for pid in pids:
            try:
                p = psutil.Process(int(pid))
                try:
                    connects = p.connections(kind='inet')
                except TypeError:
                    connects = p.connections()
                for conn in connects:
                    if conn.status != listen_status and conn.status != 'LISTEN': continue
                    laddr = conn.laddr
                    if not laddr: continue
                    local_addr = getattr(laddr, 'ip', None)
                    local_port = getattr(laddr, 'port', None)
                    if local_addr is None:
                        try:
                            local_addr = laddr[0]
                            local_port = laddr[1]
                        except:
                            continue
                    if not local_port: continue
                    listen_info[int(local_port)] = {
                        'pid': int(pid),
                        'local_addr': local_addr,
                        'port': int(local_port)
                    }
            except:
                continue
        return [listen_info[i] for i in sorted(listen_info.keys())]

    def _get_primary_listen(self, listen_info):
        if not listen_info: return {}
        for item in listen_info:
            if item.get('local_addr') in ('0.0.0.0', '::', '*'):
                return item
        return listen_info[0]

    def _is_pm2_cmdline(self, cmdline):
        cmd_text = ' '.join([str(i).lower() for i in cmdline])
        return cmd_text.find('pm2') != -1

    def _is_docker_process(self, pid):
        try:
            cgroup_file = '/proc/{}/cgroup'.format(pid)
            if not os.path.exists(cgroup_file): return False
            cgroup = public.readFile(cgroup_file)
            if not cgroup: return False
            cgroup = cgroup.lower()
            for key in ('docker', 'kubepods', 'containerd', 'libpod'):
                if key in cgroup: return True
        except:
            pass
        return False

    def _extract_nodejs_version_from_path(self, path):
        path = str(path or '').replace('\\', '/')
        # 面板目录（含来源后缀软链目录）：/www/server/nodejs/v22.14.0-nvm-root/bin/node
        match = re.search(r'/nodejs/(v\d+(?:\.\d+){1,3}[\w-]*)(?:/|$)', path)
        if match:
            return match.group(1)
        # NVM 真实目录：/root/.nvm/versions/node/v22.14.0/bin/node
        # 识别出版本后映射回面板软链目录名（v22.14.0-nvm-root），保证 get_node_bin 命中
        match = re.search(r'/([^/]*\.nvm[^/]*)/versions/node/(v\d+(?:\.\d+){1,3})(?:/|$)', path)
        if match:
            return self._resolve_nvm_version(match.group(2), match.group(1))
        # 真实 node 可执行文件（系统自装如 /usr/local/node-v24.20.0/bin/node） 正则匹配不到
        # 用 realpath 与已挂载版本目录 bin/node 比对，命中返回挂载目录名（如 v24.20.0-system-root），
        # 保证进程真实解释器能映射到 get_node_bin 可用的目录
        try:
            if not os.path.exists(path): return ''
            real = os.path.realpath(path)
            if not real or os.path.basename(real) not in ('node', 'nodejs'): return ''
            if os.path.isdir(self._nodejs_path):
                for v in os.listdir(self._nodejs_path):
                    if not v.startswith('v') or '-' not in v: continue
                    try:
                        if os.path.realpath('{}/{}/bin/node'.format(self._nodejs_path, v)) == real:
                            return v
                    except:
                        continue
        except:
            pass
        return ''

    def _resolve_nvm_version(self, nvm_version, nvm_dir=''):
        '''
            @name 将 NVM 真实版本号映射为面板侧软链目录名
            /root/.nvm/versions/node/v22.14.0/bin/node
                -> v22.14.0-nvm-root（当 /www/server/nodejs/ 下已扫描生成软链目录时）
            找不到唯一目录（未扫描 / 多用户歧义）时返回原版本号
        '''
        try:
            if not hasattr(self, '_nvm_resolve_cache'):
                self._nvm_resolve_cache = {}
            if nvm_version in self._nvm_resolve_cache:
                return self._nvm_resolve_cache[nvm_version]
            matched = []
            if os.path.isdir(self._nodejs_path):
                for v in os.listdir(self._nodejs_path):
                    if not v.startswith(nvm_version + '-'):
                        continue
                    flag_file = os.path.join(self._nodejs_path, v, '.aapanel-node-extra')
                    if not os.path.exists(flag_file):
                        continue
                    try:
                        flag = json.loads(public.readFile(flag_file))
                    except:
                        flag = {}
                    if flag.get('source') == 'nvm':
                        matched.append(v)
            resolved = matched[0] if len(matched) == 1 else nvm_version
            self._nvm_resolve_cache[nvm_version] = resolved
            return resolved
        except:
            return nvm_version

    def _append_nodejs_version_candidate(self, candidates, source, path, pid=0):
        version = self._extract_nodejs_version_from_path(path)
        if not version: return
        item = {
            'source': source,
            'version': version,
            'path': str(path or '')
        }
        try:
            pid = int(pid or 0)
            if pid: item['pid'] = pid
        except:
            pass
        for candidate in candidates:
            if candidate.get('source') == item.get('source') and candidate.get('path') == item.get(
                    'path') and candidate.get('pid', 0) == item.get('pid', 0):
                return
        candidates.append(item)

    def _detect_nodejs_version_detail(self, process_info, pids=None, listen_info=None):
        if pids is None: pids = []
        if listen_info is None: listen_info = []
        pid = 0
        cmdline = []
        if isinstance(process_info, dict):
            pid = int(process_info.get('pid', 0) or 0)
            cmdline = [str(i) for i in process_info.get('cmdline', [])]
        else:
            cmdline = [str(i) for i in process_info]

        listen_pids = []
        for item in listen_info:
            try:
                item_pid = int(item.get('pid', 0) or 0)
                if item_pid: listen_pids.append(item_pid)
            except:
                continue

        candidates = []

        # If the command uses an absolute version-manager binary, it is the strongest signal.
        for item in cmdline:
            self._append_nodejs_version_candidate(candidates, 'cmdline', item, pid)

        if isinstance(process_info, dict):
            self._append_nodejs_version_candidate(candidates, 'process_exe', process_info.get('exe', ''), pid)

        checked_pids = []
        for item_pid in [pid] + listen_pids + [int(i) for i in pids if i]:
            if not item_pid or item_pid in checked_pids: continue
            checked_pids.append(item_pid)
            exe = self._read_proc_exe(item_pid)
            source = 'proc_exe'
            if item_pid in listen_pids:
                source = 'listen_proc_exe'
            elif pid and item_pid != pid:
                source = 'child_proc_exe'
            self._append_nodejs_version_candidate(candidates, source, exe, item_pid)

        try:
            if pid:
                env_path = psutil.Process(int(pid)).environ().get('PATH', '')
                for item in env_path.split(':'):
                    self._append_nodejs_version_candidate(candidates, 'env_path', item, pid)
        except:
            pass

        if candidates:
            result = candidates[0].copy()
            versions = []
            for item in candidates:
                if item.get('version') not in versions:
                    versions.append(item.get('version'))
            result['candidates'] = candidates
            if len(versions) > 1:
                result['conflict_versions'] = versions
            return result

        default_version = self._get_default_nodejs_version()
        return {
            'source': 'default',
            'version': default_version,
            'path': '',
            'candidates': []
        }

    def _detect_nodejs_version(self, process_info, pids=None, listen_info=None):
        return self._detect_nodejs_version_detail(process_info, pids, listen_info).get('version', '')

    def _version_key(self, version):
        nums = re.findall(r'\d+', str(version))
        return tuple([int(i) for i in nums[:4]]) if nums else (0,)

    def _get_default_nodejs_version(self):
        try:
            res = self.get_nodejs_version(public.to_dict_obj({}))
            nodejs_list = res.get('message', []) if isinstance(res, dict) else []
            if nodejs_list:
                return sorted(nodejs_list, key=self._version_key, reverse=True)[0]
        except:
            pass
        return ''

    def _get_existing_node_scan_targets(self):
        existing_names = set()
        existing_paths = set()
        try:
            project_list = public.M('sites').where('project_type=?', ('Node',)).field(
                'name,path,project_config').select() or []
            for project in project_list:
                if project.get('name'): existing_names.add(project['name'])
                if project.get('path'): existing_paths.add(os.path.realpath(project['path']))
                try:
                    project_config = json.loads(project.get('project_config', '{}'))
                    if project_config.get('project_cwd'):
                        existing_paths.add(os.path.realpath(project_config['project_cwd']))
                except:
                    pass
        except:
            pass
        return existing_paths, existing_names

    def _inspect_package_manager_process(self, pid, existing_paths=None, existing_names=None, check_existing=True):
        if existing_paths is None: existing_paths = set()
        if existing_names is None: existing_names = set()
        process_info = self._read_process_basic(pid)
        if not process_info: return None, 'unreadable'
        package_command = self._parse_package_command(process_info['cmdline'])
        manager = package_command['manager']
        if not manager: return None, 'not_package_manager'
        if self._is_pm2_cmdline(process_info['cmdline']): return None, 'unsupported'
        if self._is_docker_process(pid): return None, 'unsupported'
        project_cwd = self._find_package_root(process_info.get('cwd', ''))
        if not project_cwd: return None, 'no_package_json'
        project_cwd = os.path.realpath(project_cwd)
        if check_existing and project_cwd in existing_paths:
            return None, 'already_imported'
        package_info = self._read_package_json(project_cwd)
        scripts = package_info.get('scripts', {})
        if not isinstance(scripts, dict) or not scripts:
            return None, 'no_script_match'
        package_command = self._parse_package_command(process_info['cmdline'], scripts)
        project_script = package_command['script']
        if not project_script:
            return None, 'no_script_match'
        pids = self._collect_child_pids(pid)
        listen_info = self._get_listen_info_by_pids(pids)
        primary_listen = self._get_primary_listen(listen_info)
        raw_name = package_info.get('name') or os.path.basename(project_cwd)
        project_name = self._make_unique_project_name(raw_name, existing_names, pid)
        normalized_name = self._normalize_project_name(raw_name, pid)
        warnings = []
        if project_name != raw_name:
            warnings.append('Project name normalized from [{}] to [{}].'.format(raw_name, project_name))
        if not primary_listen:
            warnings.append('No listening port was detected, please confirm manually.')
        scan_source = '{}:{}:{}:{}'.format(pid, project_cwd, manager, project_script)
        version_detail = self._detect_nodejs_version_detail(process_info, pids, listen_info)
        candidate = {
            'scan_id': hashlib.sha1(scan_source.encode('utf-8')).hexdigest()[:16],
            'pid': int(pid),
            'pids': pids,
            'ppid': process_info.get('ppid', 0),
            'process_name': process_info.get('name', ''),
            'process_cwd': process_info.get('cwd', ''),
            'cmdline': process_info.get('cmdline', []),
            'detected_command': ' '.join(process_info.get('cmdline', [])),
            'project_cwd': project_cwd,
            'project_name': project_name,
            'raw_project_name': raw_name,
            'normalized_project_name': normalized_name,
            'package_manager': manager,
            'pkg_manager': manager,
            'project_script': project_script,
            'start_command': '{} run {}'.format(manager, project_script),
            'script_source': 'package.json scripts.{}'.format(project_script),
            'port': int(primary_listen.get('port', 0)) if primary_listen else 0,
            'ports': [i['port'] for i in listen_info],
            'listen_addr': primary_listen.get('local_addr', '') if primary_listen else '',
            'listen_info': listen_info,
            'run_user': process_info.get('user', 'www') or 'www',
            'nodejs_version': version_detail.get('version', ''),
            'status': 'importable' if primary_listen else 'need_confirm',
            # 'confidence': 90 if primary_listen else 75,
            'warnings': warnings,
            'start_type': 'package_script'
        }
        return candidate, ''

    def scan_import_projects(self, get):
        '''
            @name 扫描可导入的Node项目
            @return dict
        '''
        # 先挂载系统/NVM node（幂等，60s 内重复扫描直接取缓存）：
        # 保证用真实 NVM 路径启动的项目 nodejs_version 能映射出软链目录名
        # （如 v22.14.0-nvm-root），否则只识别出纯版本号导致无法导入
        self._ensure_node_runtime_mounted()
        existing_paths, existing_names = self._get_existing_node_scan_targets()
        skipped = {
            'unsupported': 0,
            'no_package_json': 0,
            'no_script_match': 0,
            'already_imported': 0,
            'unreadable': 0,
            'duplicated': 0
        }
        candidates = []
        seen_keys = set()
        matched_processes = 0
        try:
            pids = psutil.pids()
        except:
            pids = []
        for pid in pids:
            candidate, reason = self._inspect_package_manager_process(pid, existing_paths, existing_names, True)
            if reason == 'not_package_manager':
                continue
            if not candidate:
                if reason in skipped:
                    skipped[reason] += 1
                else:
                    skipped['unsupported'] += 1
                continue
            matched_processes += 1
            scan_key = '{}|{}|{}'.format(candidate['project_cwd'], candidate['package_manager'],
                                         candidate['project_script'])
            if scan_key in seen_keys:
                skipped['duplicated'] += 1
                continue
            seen_keys.add(scan_key)
            existing_names.add(candidate['project_name'])
            candidates.append(candidate)
        data = {
            'total': len(candidates),
            'matched_processes': matched_processes,
            'skipped': skipped,
            'supported_package_managers': ['npm', 'pnpm', 'yarn'],
            'data': candidates
        }
        public.set_module_logs('node_site', 'scan_import_projects')
        return public.return_message(0, 0, data)

    def create_scan_import_project(self, get):
        '''
            @name 导入扫描到的Node项目
            @param get<dict_obj>{
                pid: int<扫描到的主进程PID>
                project_cwd: string<项目目录>
                project_name: string<项目名称>
                package_manager: string<包管理器 npm/pnpm/yarn>
                project_script: string<项目脚本>
                port: int<项目实际监听端口>
                run_user: string<运行用户>
                nodejs_version: string<nodejs版本>
                bind_extranet: int<是否绑定外网> 1:是 0:否
                domains: list<域名列表> ["domain1:80","domain2:80"]  // 在bind_extranet=1时，需要填写
            }
            @return dict
        '''
        if not isinstance(get, public.dict_obj):
            get = public.to_dict_obj(get)
        try:
            pid = int(get.get('pid', 0))
        except:
            pid = 0
        if pid <= 0 or not os.path.exists('/proc/{}'.format(pid)):
            return self._nodejs_error('The scanned process no longer exists, please rescan.')
        candidate, reason = self._inspect_package_manager_process(pid, set(), set(), False)
        if not candidate:
            return self._nodejs_error(
                'The scanned process is no longer a supported npm/pnpm/yarn project: {}'.format(reason))
        project_cwd = os.path.realpath(str(get.get('project_cwd', candidate['project_cwd'])).strip())
        if project_cwd != os.path.realpath(candidate['project_cwd']):
            return self._nodejs_error(
                'The project directory does not match the current running process, please rescan.')
        package_info = self._read_package_json(project_cwd)
        scripts = package_info.get('scripts', {})
        if not isinstance(scripts, dict) or not scripts:
            return self._nodejs_error('No scripts were found in package.json.')
        project_script = str(get.get('project_script', candidate['project_script'])).strip()
        if not project_script:
            return self._nodejs_error(public.lang('Start command cannot be empty'))
        if project_script not in scripts:
            return self._nodejs_error('The startup script does not exist in package.json: {}'.format(project_script))
        if not re.match(r'^[0-9A-Za-z_:\-\.\/]+$', project_script):
            return self._nodejs_error(
                'The startup script name contains unsupported characters: {}'.format(project_script))
        pkg_manager = self._normalize_package_manager(
            get.get('package_manager', get.get('pkg_manager', candidate['package_manager'])))
        try:
            port = int(str(get.get('port', candidate.get('port', 0)) or 0).strip())
        except:
            return self._nodejs_error('The project port is invalid: {}'.format(get.get('port', '')))
        if port < 0 or port > 65535:
            return self._nodejs_error('The project port is invalid: {}'.format(port))
        if port == 443:
            return self._nodejs_error(public.lang('Do not use system ports 443.'))
        if port and self.check_port_is_used(port, True):
            return self._nodejs_error('This port is already occupied by an aaPanel Node project, port: {}'.format(port))
        existing_paths, existing_names = self._get_existing_node_scan_targets()
        if project_cwd in existing_paths:
            return self._nodejs_error('The project directory has already been imported: {}'.format(project_cwd))
        project_name = self._make_unique_project_name(get.get('project_name', candidate['project_name']),
                                                      existing_names, pid)
        run_user = str(get.get('run_user', candidate.get('run_user', 'www')) or 'www').strip()
        nodejs_version = str(get.get('nodejs_version', candidate.get('nodejs_version', '')) or '').strip()
        if not nodejs_version:
            nodejs_version = self._get_default_nodejs_version()
        if not nodejs_version:
            return self._nodejs_error('Please install or select a Node.js version first.')
        # # 无后缀版本需要检查插件安装
        # if '-' not in nodejs_version and not self._is_install_nodejs(get):
        #     return self._nodejs_error(public.lang('Please install nodejs version manager first'))
        if not self.get_node_bin(nodejs_version):
            return self._nodejs_error(public.lang('The specified nodejs version does not exist!'))
        try:
            bind_extranet = int(get.get('bind_extranet', 0) or 0)
        except:
            bind_extranet = 0
        try:
            is_power_on = int(get.get('is_power_on', 0) or 0)
        except:
            is_power_on = 0
        try:
            max_memory_limit = int(get.get('max_memory_limit', 0) or 0)
        except:
            max_memory_limit = 0
        format_domains, error_msg = self._format_and_validate_domains(bind_extranet, get.get('domains', []), port)
        if error_msg: return self._nodejs_error(error_msg)
        project_config = {
            'project_name': project_name,
            'project_cwd': project_cwd,
            'project_script': project_script,
            'project_type': 'nodejs',
            'start_type': 'package_script',
            'import_source': 'scan',
            'pkg_manager': pkg_manager,
            'package_manager': pkg_manager,
            'bind_extranet': bind_extranet,
            'domains': [],
            'is_power_on': is_power_on,
            'run_user': run_user,
            'max_memory_limit': max_memory_limit,
            'nodejs_version': nodejs_version,
            'port': port,
            'scan_pid': pid,
            'scan_pids': candidate.get('pids', []),
            'scan_time': public.getDate()
        }
        pdata = {
            'name': project_name,
            'path': project_cwd,
            'ps': str(get.get('project_ps', get.get('ps', 'Scan-Imported')) or 'Scan-Imported'),
            'status': 1,
            'type_id': 0,
            'project_type': 'Node',
            'project_config': json.dumps(project_config),
            'addtime': public.getDate()
        }
        project_id = public.M('sites').insert(pdata)
        pid_file = "{}/{}.pid".format(self._node_pid_path, project_name)
        public.writeFile(pid_file, str(pid))
        if bind_extranet:
            get.project_name = project_name
            get.domains = format_domains
            self.project_add_domain(get)
        public.WriteLog(self._log_name, 'Import scanned Node.js project {}'.format(project_name))
        return_message = public.return_data(True, 'Imported project successfully', project_id)
        return_message['project_name'] = project_name
        return_message['pid'] = pid
        if 'status' in return_message: del return_message['status']
        public.set_module_logs('node_site', 'create_scan_import_project')
        return public.return_message(0, 0, return_message)

    def create_project(self, get):
        '''
            @name 创建新的项目
            @author hwliang<2021-08-09>
            @param get<dict_obj>{
                project_name: string<项目名称>
                project_cwd: string<项目目录>
                project_script: string<项目脚本>
                project_ps: string<项目备注信息>
                bind_extranet: int<是否绑定外网> 1:是 0:否
                domains: list<域名列表> ["domain1:80","domain2:80"]  // 在bind_extranet=1时，需要填写
                is_power_on: int<是否开机启动> 1:是 0:否
                run_user: string<运行用户>
                max_memory_limit: int<最大内存限制> // 超出此值项目将被强制重启
                nodejs_version: string<nodejs版本>
            }
            @return dict
        '''
        # 校验参数
        try:
            get.validate([
                Param('project_cwd').String(),
                Param('project_name').String(),
                Param('project_script').String(),
                Param('port').String(),
                Param('run_user').String(),
                Param('nodejs_version').String(),
                Param('project_ps').String(),
                # Param('domains').List(),
                Param('project_env').String(),
                Param('bind_extranet').Integer(),
                Param('is_power_on').Integer(),
                Param('max_memory_limit').Integer(),

            ], [
                public.validate.trim_filter(),
            ])
        except Exception as ex:
            public.print_log("error info: {}".format(ex))
            return public.return_message(-1, 0, str(ex))

        # public.set_module_logs('node_site_nodejs', 'create_app', 1)
        public.set_module_logs('node_site', 'create_app', 1)

        if not isinstance(get, public.dict_obj):
            return_message = public.return_error(public.lang('The parameter type is wrong, need dict obj object'))
            del return_message['status']
            return public.return_message(-1, 0, return_message)
        project_name = get.project_name.strip()
        if not re.match(r"^\w+$", project_name):
            return_message = public.return_error(public.lang(
                'The project name format is incorrect and supports letters, numbers, underscores, and expressions: ^[0-9A-Za-z_]$'))
            del return_message['status']
            return public.return_message(-1, 0, return_message)

        if public.M('sites').where('name=?', (get.project_name,)).count():
            return_message = public.return_error(
                'The specified project name already exists: {}'.format(get.project_name))
            del return_message['status']
            return public.return_message(-1, 0, return_message)
        get.project_cwd = get.project_cwd.strip()
        if not os.path.exists(get.project_cwd):
            return_message = public.return_error('The project directory does not exist: {}'.format(get.project_cwd))
            del return_message['status']
            return public.return_message(-1, 0, return_message)

        # 端口占用检测
        if get.get('port') == '443':
            return_message = public.return_error(public.lang('Do not use system ports 443.'))
            del return_message['status']
            return public.return_message(-1, 0, return_message)
        if self.check_port_is_used(get.get('port/port')):
            return_message = public.return_error(
                'This port is already occupied, please modify your project port, port: {}'.format(get.port))
            del return_message['status']
            return public.return_message(-1, 0, return_message)

        format_domains, error_msg = self._format_and_validate_domains(get.bind_extranet, get.get('domains', []),
                                                                      get.port)
        if error_msg: return self._nodejs_error(error_msg)

        # 系统/NVM 版本与运行用户权限校验：
        # NVM 版本属于某个 Linux 用户（/root/.nvm -> root、/home/xxx/.nvm -> xxx），
        # 项目运行用户必须与版本属主一致，否则启动时无权访问该用户 home 下 nvm
        nodejs_version = get.nodejs_version.strip()
        # # 无后缀版本需要检查插件安装
        # if '-' not in nodejs_version and not self._is_install_nodejs(get):
        #     return self._nodejs_error(public.lang('Please install nodejs version manager first'))
        if '-nvm-' in nodejs_version:
            version_owner = self._get_node_version_owner(nodejs_version)
            run_user = get.run_user.strip()
            if version_owner and version_owner != run_user:
                return self._nodejs_error(
                    'The NVM Node.js version "{}" belongs to user "{}", but the project runs as user "{}". '
                    'Please switch the runtime or the run user.'.format(
                        nodejs_version, version_owner, run_user))

        pdata = {
            'name': get.project_name,
            'path': get.project_cwd,
            'ps': get.project_ps,
            'status': 1,
            'type_id': 0,
            'project_type': 'Node',
            'project_config': json.dumps(
                {
                    'project_name': get.project_name,
                    'project_cwd': get.project_cwd,
                    'project_script': get.project_script,
                    'bind_extranet': int(get.bind_extranet),
                    'domains': [],
                    'is_power_on': int(get.get('is_power_on', 0)),
                    'run_user': get.run_user,
                    'max_memory_limit': get.max_memory_limit,
                    'nodejs_version': get.nodejs_version,
                    'pkg_manager': self._normalize_package_manager(
                        get.get('pkg_manager', get.get('package_manager', 'npm'))),
                    'port': int(get.port)
                }
            ),
            'addtime': public.getDate()
        }

        project_id = public.M('sites').insert(pdata)
        if int(get.bind_extranet) == 1:
            get.domains = format_domains
            self.project_add_domain(get)
        self.set_config(get.project_name)
        public.WriteLog(self._log_name, 'Add Node.js project {}'.format(get.project_name))
        self.install_packages(get)
        self.start_project(get)
        return_message = public.return_data(True, 'Added project successfully', project_id)

        # ================ git start ======================
        try:
            _deploy_type = get.get('deploy_type', '')
            _auth_type = get.get('auth_type', '')
            _has_git = bool(_auth_type) or _deploy_type in ['ssh', 'github']
            if _has_git:
                if not _auth_type:
                    _auth_type = {'ssh': 'ssh_key', 'github': 'github'}.get(_deploy_type, _deploy_type)
                from git_tools import GitTools
                git_obj = GitTools()

                # 已clone项目，使用.git导入
                res = git_obj.get_git_directory(public.to_dict_obj({"site_id": project_id}))
                if res['status'] != 0:
                    return public.return_message(-1, 0, res['message'])
                git_info = res['message'] or {}
                if not git_info.get('repo'):
                    return public.return_message(-1, 0, "Failed to read Git information from the cloned repository")
                res = git_obj.import_existing_repository(
                    public.to_dict_obj({
                        "site_id": project_id,
                        "repo": git_info['repo'],
                        "branch": git_info['branch'],
                        "key_path": git_info.get('key_path', ''),
                        "auth_type": _auth_type,
                        "username": get.get('username', ''),
                        "token": get.get('token', ''),
                        "project_type": 'node',
                    }))
                if res['status'] != 0:
                    return public.return_message(-1, 0, res['message'])
        except Exception as e:
            print(e)
            # 失败不删除项目
            return public.return_message(-1, 0, public.lang("There was an error while configuring Git tools!"))
        # ================ git end ======================

        del return_message['status']
        return public.return_message(0, 0, return_message)

    def modify_project(self, get):
        '''
            @name 修改指定项目
            @author hwliang<2021-08-09>
            @param get<dict_obj>{
                project_name: string<项目名称>
                project_cwd: string<项目目录>
                project_script: string<项目脚本>
                project_ps: string<项目备注信息>
                is_power_on: int<是否开机启动> 1:是 0:否
                run_user: string<运行用户>
                max_memory_limit: int<最大内存限制> // 超出此值项目将被强制重启
                nodejs_version: string<nodejs版本>
            }
            @return dict
        '''
        # 校验参数
        try:
            get.validate([
                Param('project_cwd').String(),
                Param('project_name').String(),
                Param('project_script').String(),
                Param('port').String(),
                Param('run_user').String(),
                Param('nodejs_version').String(),
                Param('project_ps').String(),
                Param('domains').String(),
                Param('bind_extranet').Integer(),
                Param('is_power_on').Integer(),

            ], [
                public.validate.trim_filter(),
            ])
        except Exception as ex:
            public.print_log("error info: {}".format(ex))
            return public.return_message(-1, 0, str(ex))

        if not isinstance(get, public.dict_obj):
            return_message = public.return_error(public.lang('The parameter type is wrong, need dict obj'))
            del return_message['status']
            return public.return_message(-1, 0, return_message)
        if not self._is_install_nodejs(get):
            return_message = public.return_error(
                public.lang('Please install nodejs version manager before installing at least one nodejs'))
            del return_message['status']
            return public.return_message(-1, 0, return_message)
        project_find = self.get_project_find(get.project_name)
        if not project_find:
            return_message = public.return_error('Item does not exist: {}'.format(get.project_name))
            del return_message['status']
            return public.return_message(-1, 0, return_message)

        if not os.path.exists(get.project_cwd):
            return_message = public.return_error('The project directory does not exist: {}'.format(get.project_cwd))
            del return_message['status']
            return public.return_message(-1, 0, return_message)
        rebuild = False
        if hasattr(get, 'port'):
            if int(project_find['project_config']['port']) != int(get.port):
                if self.check_port_is_used(get.get('port/port'), True):
                    return_message = public.return_error(
                        'The port is already occupied, please modify your port, port: {}'.format(get.port))
                    del return_message['status']
                    return public.return_message(-1, 0, return_message)
                project_find['project_config']['port'] = int(get.port)
        if hasattr(get, 'project_cwd'): project_find['project_config']['project_cwd'] = get.project_cwd
        if hasattr(get, 'project_script'):
            if not get.project_script.strip():
                return_message = public.return_error(public.lang('Start command cannot be empty'))
                del return_message['status']
                return public.return_message(-1, 0, return_message)
            project_find['project_config']['project_script'] = get.project_script.strip()
        if hasattr(get, 'is_power_on'): project_find['project_config']['is_power_on'] = get.is_power_on
        if hasattr(get, 'run_user'): project_find['project_config']['run_user'] = get.run_user
        if hasattr(get, 'max_memory_limit'): project_find['project_config']['max_memory_limit'] = get.max_memory_limit
        if hasattr(get, 'nodejs_version'):
            if project_find['project_config']['nodejs_version'] != get.nodejs_version:
                rebuild = True
                project_find['project_config']['nodejs_version'] = get.nodejs_version
        pdata = {
            'path': get.project_cwd,
            'ps': get.project_ps,
            'project_config': json.dumps(project_find['project_config'])
        }

        public.M('sites').where('name=?', (get.project_name,)).update(pdata)
        self.set_config(get.project_name)
        public.WriteLog(self._log_name, 'Modify Node.js project {}'.format(get.project_name))
        if rebuild:
            self.rebuild_project(get.project_name)
        return_message = public.return_data(True, 'Modify the project successfully')
        del return_message['status']
        return public.return_message(0, 0, return_message)

    def rebuild_project(self, project_name):
        '''
            @name 重新构建指定项目
            @author hwliang<2021-08-26>
            @param project_name: string<项目名称>
            @return bool
        '''
        project_find = self.get_project_find(project_name)
        if not project_find: return False
        nodejs_version = project_find['project_config']['nodejs_version']
        npm_bin = self.get_npm_bin(nodejs_version)

        public.ExecShell(
            self.get_last_env(nodejs_version) + "cd {} && {} rebuild >> {} 2>&1".format(project_find['path'], npm_bin,
                                                                                        self._npm_exec_log))
        return True

    def remove_project(self, get):
        '''
            @name 删除指定项目
            @author hwliang<2021-08-09>
            @param get<dict_obj>{
                project_name: string<项目名称>
            }
            @return dict
        '''
        # 校验参数
        try:
            get.validate([
                Param('project_name').String(),
            ], [
                public.validate.trim_filter(),
            ])
        except Exception as ex:
            public.print_log("error info: {}".format(ex))
            return public.return_message(-1, 0, str(ex))

        project_find = self.get_project_find(get.project_name)
        if not project_find:
            return_message = public.return_error('The specified item does not exist: {}'.format(get.project_name))
            del return_message['status']
            return public.return_message(-1, 0, return_message)

        self.stop_project(get)
        self.clear_config(get.project_name)
        public.M('domain').where('pid=?', (project_find['id'],)).delete()
        public.M('sites').where('name=?', (get.project_name,)).delete()

        pid_file = "{}/{}.pid".format(self._node_pid_path, get.project_name)
        if os.path.exists(pid_file): os.remove(pid_file)
        script_file = '{}/{}.sh'.format(self._node_run_scripts, get.project_name)
        if os.path.exists(script_file): os.remove(script_file)
        log_file = '{}/{}.log'.format(self._node_logs_path, get.project_name)
        if os.path.exists(log_file): os.remove(log_file)
        # 清理定时重启任务，避免项目删除后残留
        self._del_crontab_by_name(
            '[Do Not Delete] Scheduled Restart nodejs Project {}'.format(get.project_name)
        )
        public.WriteLog(self._log_name, 'Delete Node.js project {}'.format(get.project_name))
        return_message = public.return_data(True, 'Successfully deleted item')
        del return_message['status']
        return public.return_message(0, 0, return_message)

    # 批量操作项目
    def batch_operation_project(self, get):
        '''
            @name 批量操作项目
            @param project_names []
            @return dict
        '''
        try:
            get.validate([
                Param('project_names'),
                Param('operation_type'),

            ])
            project_names = json.loads(get.get('project_names', []))
            operation_type = get.get('operation_type')
        except Exception as ex:
            public.print_log("error info: {}".format(ex))
            return public.return_message(-1, 0, str(ex))

        if not project_names:
            return public.return_message(-1, 0, public.lang('The project list is empty.'))

        if operation_type not in ['delete', 'start', 'stop', 'restart']:
            return public.return_message(-1, 0, public.lang('Operation type is empty！'))

        project_list = public.S('sites').where_in("name", project_names, 'OR').select()
        if not project_list:
            return public.return_message(-1, 0, public.lang('The project list is empty.'))

        success_count = 0
        msg_list = []
        from mod.project.nodejs import comMod
        for project in project_list:
            try:
                project['project_config'] = json.loads(project['project_config'])
                p_type = 'pm2' if project['project_config'].get('pm2_name') else 'nodejs'
                if operation_type == 'delete':
                    temp_get = public.to_dict_obj({'project_name': project['name'], 'project_type': p_type,
                                                   'pm2_name': project['project_config'].get('pm2_name')})
                    res = comMod.main().delete(temp_get)
                elif operation_type in ['start', 'stop', 'restart']:
                    res = comMod.main().set_project_status(public.to_dict_obj(
                        {"project_name": project['name'], "project_type": p_type, "status": operation_type,
                         "pm2_name": project['project_config'].get('pm2_name'),
                         "run_user": project['project_config'].get('run_user')}))

                if res['status'] != 0:
                    msg_list.append({'name': project['name'], 'status': False, 'msg': res['message']['result']})
                else:
                    success_count += 1
                    msg_list.append({'name': project['name'], 'status': True, 'msg': res['message']['result']})

                    if operation_type == 'delete':
                        # 删除git
                        from git_tools import GitTools
                        GitTools().del_site_git(public.to_dict_obj({'site_id': project['id']}))

            except Exception as e:
                msg_list.append({'name': project['name'], 'status': False, 'msg': str(e)})

        msg = f"Successfully {success_count} items.Failed on {len(project_names) - success_count} projects."
        return public.return_message(0, 0, {"msg": msg, "msg_list": msg_list})

    def project_get_domain(self, get):
        '''
            @name 获取指定项目的域名列表
            @author hwliang<2021-08-09>
            @param get<dict_obj>{
                project_name: string<项目名称>
            }
            @return dict
        '''

        project_id = public.M('sites').where('name=?', (get.project_name,)).getField('id')
        if not project_id:
            return public.return_message(0, 0, [])
        domains = public.M('domain').where('pid=?', (project_id,)).order('id desc').select()
        return public.return_message(0, 0, domains)

    def project_add_domain(self, get):
        '''
            @name 为指定项目添加域名
            @author hwliang<2021-08-09>
            @param get<dict_obj>{
                project_name: string<项目名称>
                domains: list<域名列表>
            }
            @return dict
        '''
        # 校验参数
        try:
            get.validate([
                Param('project_name').String(),
                # Param('domains').List(),
            ], [
                public.validate.trim_filter(),
            ])
        except Exception as ex:
            public.print_log("error info: {}".format(ex))
            return public.return_message(-1, 0, str(ex))

        project_find = self.get_project_find(get.project_name)
        if not project_find:
            return_message = public.return_error(public.lang('The specified item does not exist'))
            del return_message['status']
            return public.return_message(-1, 0, return_message)
        project_id = project_find['id']

        domains = get.domains
        success_list = []
        error_list = []
        for domain in domains:
            domain = domain.strip()
            if not domain:
                return_message = public.return_error(public.lang('Domain name cannot be empty'))
                del return_message['status']
                return public.return_message(-1, 0, return_message)
            domain_arr = domain.split(':')
            if len(domain_arr) == 1:
                domain_arr.append(80)
                domain += ':80'
            else:
                if domain_arr[1] == '443':
                    error_list.append(domain)
                    continue
            if not public.M('domain').where('name=?', (domain_arr[0],)).count():
                public.M('domain').add('name,pid,port,addtime',
                                       (domain_arr[0], project_id, domain_arr[1], public.getDate()))
                if not domain in project_find['project_config']['domains']:
                    project_find['project_config']['domains'].append(domain)
                public.WriteLog(self._log_name, 'Successfully added the domain [{}] to the project [{}]'.format(domain,
                                                                                                                get.project_name))
                success_list.append(domain)
            else:
                public.WriteLog(self._log_name, 'Domain [{}] already exists'.format(domain))
                error_list.append(domain)

        if success_list:
            public.M('sites').where('id=?', (project_id,)).save('project_config',
                                                                json.dumps(project_find['project_config']))
            self.set_config(get.project_name)
            return_message = public.return_data(True, "[{}] domain names added successfully, [{}] failed!".format(
                len(success_list), len(error_list)), error_msg=error_list)
            del return_message['status']
            return public.return_message(0, 0, return_message)
        return_message = public.return_data(False, "[{}] domain names added successfully, [{}] failed!".format(
            len(success_list), len(error_list)), error_msg=error_list)
        del return_message['status']
        return public.return_message(-1, 0, return_message)

    def project_remove_domain(self, get):
        '''
            @name 为指定项目删除域名
            @author hwliang<2021-08-09>
            @param get<dict_obj>{
                project_name: string<项目名称>
                domain: string<域名>
            }
            @return dict
        '''
        # 校验参数
        try:
            get.validate([
                Param('project_name').String(),
                Param('domain').String(),
            ], [
                public.validate.trim_filter(),
            ])
        except Exception as ex:
            public.print_log("error info: {}".format(ex))
            return public.return_message(-1, 0, str(ex))

        project_find = self.get_project_find(get.project_name)
        if not project_find:
            return_message = public.return_error(public.lang('The specified item does not exist'))
            del return_message['status']
            return public.return_message(-1, 0, return_message)
        last_domain = get.domain
        domain_arr = get.domain.split(':')
        if len(domain_arr) == 1:
            domain_arr.append(80)

        project_id = public.M('sites').where('name=?', (get.project_name,)).getField('id')
        if project_find['project_config']['bind_extranet']:
            domain_count = public.M('domain').where('pid=?', (project_id,)).count()
            if domain_count <= 1:
                return_message = public.return_error(
                    public.lang('At least one domain name is required for the mapped project'))
                del return_message['status']
                return public.return_message(-1, 0, return_message)
        domain_id = public.M('domain').where('name=? AND pid=?', (domain_arr[0], project_id)).getField('id')
        if not domain_id:
            return_message = public.return_error(public.lang('The specified domain name does not exist'))
            del return_message['status']
            return public.return_message(-1, 0, return_message)
        public.M('domain').where('id=?', (domain_id,)).delete()

        if get.domain in project_find['project_config']['domains']:
            project_find['project_config']['domains'].remove(get.domain)
        if get.domain + ":80" in project_find['project_config']['domains']:
            project_find['project_config']['domains'].remove(get.domain + ":80")

        # 处理端口残留
        domains = []
        for domain in project_find['project_config']['domains']:
            if get.domain == domain.split(':')[0]:
                continue
            domains.append(domain)
        project_find['project_config']['domains'] = domains

        public.M('sites').where('id=?', (project_id,)).save('project_config',
                                                            json.dumps(project_find['project_config']))
        public.WriteLog(self._log_name,
                        'From project: [{}], delete domain name [{}]'.format(get.project_name, get.domain))
        self.set_config(get.project_name)
        return_message = public.return_data(True, 'Domain name deleted successfully')
        del return_message['status']
        return public.return_message(0, 0, return_message)

    def bind_extranet(self, get):
        '''
            @name 绑定外网
            @author hwliang<2021-08-09>
            @param get<dict_obj>{
                project_name: string<项目名称>
            }
            @return dict
        '''
        # 校验参数
        try:
            get.validate([
                Param('project_name').String(),
                # Param('domains').List(),
            ], [
                public.validate.trim_filter(),
            ])
        except Exception as ex:
            public.print_log("error info: {}".format(ex))
            return public.return_message(-1, 0, str(ex))

        project_name = get.project_name.strip()
        project_find = self.get_project_find(project_name)
        if not project_find:
            return_message = public.return_error(public.lang('Item does not exist'))
            del return_message['status']
            return public.return_message(-1, 0, return_message)
        if not project_find['project_config']['domains']:
            return_message = public.return_error(
                public.lang('Please add at least one domain name in the [Domain Management] option'))
            del return_message['status']
            return public.return_message(-1, 0, return_message)
        if not project_find['project_config'].get('port'):
            return_message = public.return_error(public.lang('Please set the running port for the project first.'))
            del return_message['status']
            return public.return_message(-1, 0, return_message)
        project_find['project_config']['bind_extranet'] = 1
        public.M('sites').where("id=?", (project_find['id'],)).setField('project_config',
                                                                        json.dumps(project_find['project_config']))
        self.set_config(project_name)
        public.WriteLog(self._log_name, 'Node project{}, enable mapping'.format(project_name))
        return_message = public.return_data(True, 'Enable the mapping successfully')
        del return_message['status']
        return public.return_message(0, 0, return_message)

    def set_config(self, project_name):
        '''
            @name 设置项目配置
            @author hwliang<2021-08-09>
            @param project_name: string<项目名称>
            @return bool
        '''
        project_find = self.get_project_find(project_name)
        if not project_find: return False
        if not project_find['project_config']: return False
        if not project_find['project_config']['bind_extranet']: return False
        if not project_find['project_config']['domains']: return False
        self.set_nginx_config(project_find)
        self.set_apache_config(project_find)
        self.set_ols_config(project_find)
        public.serviceReload()
        return True

    def clear_config(self, project_name):
        '''
            @name 清除项目配置
            @author hwliang<2021-08-09>
            @param project_name: string<项目名称>
            @return bool
        '''
        project_find = self.get_project_find(project_name)
        if not project_find: return False
        self.clear_nginx_config(project_find)
        self.clear_apache_config(project_find)
        self.clear_ols_config(project_find)
        public.serviceReload()
        return True

    def clear_ols_config(self, project_find):
        '''
            @name 删除OLS配置
            @param project_find: dict<项目信息>
            @return bool
        '''
        project_name = project_find['name']

        vhost_dir = public.get_panel_path() + '/vhost/openlitespeed/'
        detail_file = vhost_dir + 'detail/' + project_name + '.conf'
        main_conf_file = vhost_dir + project_name + '.conf'
        listen_dir = vhost_dir + 'listen/'
        listen_list = [listen_dir + '80.conf', listen_dir + '443.conf']

        # 删除虚拟主机配置文件
        if os.path.exists(main_conf_file):
            os.remove(main_conf_file)
        if os.path.exists(detail_file):
            os.remove(detail_file)

        # 清理监听器中的映射 (Map) 关系
        if os.path.exists(listen_dir):
            for conf_name in listen_list:
                content = public.readFile(conf_name)
                if content:
                    pattern = r"^\s*map\s+{}\s+.*?\n".format(re.escape(project_name))
                    if re.search(pattern, content, flags=re.M):
                        new_content = re.sub(pattern, "", content, flags=re.M)
                        public.writeFile(conf_name, new_content)

        return public.return_message(0, 0, True)

    def clear_apache_config(self, project_find):
        '''
            @name 清除apache配置
            @author hwliang<2021-08-09>
            @param project_find: dict<项目信息>
            @return bool
        '''
        project_name = project_find['name']
        config_file = "{}/apache/node_{}.conf".format(self._vhost_path, project_name)
        if os.path.exists(config_file):
            os.remove(config_file)
        return True

    def clear_nginx_config(self, project_find):
        '''
            @name 清除nginx配置
            @author hwliang<2021-08-09>
            @param project_find: dict<项目信息>
            @return bool
        '''
        project_name = project_find['name']
        config_file = "{}/nginx/node_{}.conf".format(self._vhost_path, project_name)
        if os.path.exists(config_file):
            os.remove(config_file)
        rewrite_file = "{panel_path}/vhost/rewrite/node_{project_name}.conf".format(panel_path=self._panel_path,
                                                                                    project_name=project_name)
        if os.path.exists(rewrite_file):
            os.remove(rewrite_file)
        return True

    def set_nginx_config(self, project_find):
        '''
            @name 设置Nginx配置
            @author hwliang<2021-08-09>
            @param project_find: dict<项目信息>
            @return bool
        '''
        project_name = project_find['name']
        ports = []
        domains = []

        for d in project_find['project_config']['domains']:
            domain_tmp = d.split(':')
            if len(domain_tmp) == 1: domain_tmp.append(80)
            if not int(domain_tmp[1]) in ports:
                ports.append(int(domain_tmp[1]))
            if not domain_tmp[0] in domains:
                domains.append(domain_tmp[0])
        listen_ipv6 = public.listen_ipv6()
        listen_ports = ''
        for p in ports:
            listen_ports += "    listen {};\n".format(p)
            if listen_ipv6:
                listen_ports += "    listen [::]:{};\n".format(p)
        listen_ports = listen_ports.strip()

        is_ssl, is_force_ssl = self.exists_nginx_ssl(project_name)
        ssl_config = ''
        if is_ssl:
            http3_header = ""
            if self.is_nginx_http3():
                http3_header = '''\n    add_header Alt-Svc 'quic=":443"; h3=":443"; h3-29=":443"; h3-27=":443";h3-25=":443"; h3-T050=":443"; h3-Q050=":443";h3-Q049=":443";h3-Q048=":443"; h3-Q046=":443"; h3-Q043=":443"';'''
                http3_header += "\n    quic_retry on;\n    quic_gso on;"
                if self.ng_ssl_early_data_enabled():
                    http3_header += "\n    ssl_early_data on;"

            listen_ports += "\n    listen 443 ssl;"
            if listen_ipv6: listen_ports += "\n    listen [::]:443 ssl;"

            ssl_config = '''ssl_certificate    {vhost_path}/cert/{priject_name}/fullchain.pem;
    ssl_certificate_key    {vhost_path}/cert/{priject_name}/privkey.pem;
    ssl_protocols TLSv1.1 TLSv1.2 TLSv1.3;
    ssl_ciphers EECDH+CHACHA20:EECDH+CHACHA20-draft:EECDH+AES128:RSA+AES128:EECDH+AES256:RSA+AES256:EECDH+3DES:RSA+3DES:!MD5;
    ssl_prefer_server_ciphers on;
    ssl_session_cache shared:SSL:10m;
    ssl_session_timeout 10m;
    add_header Strict-Transport-Security "max-age=31536000";{http3_header}
    error_page 497  https://$host$request_uri;'''.format(vhost_path=self._vhost_path, priject_name=project_name,
                                                         http3_header=http3_header)

            if is_force_ssl:
                ssl_config += '''
    #HTTP_TO_HTTPS_START
    if ($server_port !~ 443){
        rewrite ^(/.*)$ https://$host$1 permanent;
    }
    #HTTP_TO_HTTPS_END'''

        config_file = "{}/nginx/node_{}.conf".format(self._vhost_path, project_name)
        template_file = "{}/template/nginx/node_http.conf".format(self._vhost_path)

        config_body = public.readFile(template_file)
        config_body = config_body.format(
            site_path=project_find['path'],
            domains=' '.join(domains),
            project_name=project_name,
            panel_path=self._panel_path,
            log_path=public.get_logs_path(),
            url='http://127.0.0.1:{}'.format(project_find['project_config']['port']),
            host='$host',
            listen_ports=listen_ports,
            ssl_config=ssl_config
        )

        # # 恢复旧的SSL配置
        # ssl_config = self.get_nginx_ssl_config(project_name)
        # if ssl_config:
        #     config_body.replace('#error_page 404/404.html;',ssl_config)

        rewrite_file = "{panel_path}/vhost/rewrite/node_{project_name}.conf".format(panel_path=self._panel_path,
                                                                                    project_name=project_name)
        if not os.path.exists(rewrite_file): public.writeFile(rewrite_file,
                                                              '# Please fill in the URLrewrite or custom NGINX config here\n')
        public.writeFile(config_file, config_body)
        return True

    def get_nginx_ssl_config(self, project_name):
        '''
            @name 获取项目Nginx SSL配置
            @author hwliang<2021-08-09>
            @param project_name: string<项目名称>
            @return string
        '''
        result = ''
        config_file = "{}/nginx/node_{}".format(self._vhost_path, project_name)
        if not os.path.exists(config_file):
            return result

        config_body = public.readFile(config_file)
        if not config_body:
            return result
        if config_body.find('ssl_certificate') == -1:
            return result

        ssl_body = re.search("#SSL-START(.|\n)+#SSL-END", config_body)
        if not ssl_body: return result
        result = ssl_body.group()
        return result

    def exists_nginx_ssl(self, project_name):
        '''
            @name 判断项目是否配置Nginx SSL配置
            @author hwliang<2021-08-09>
            @param project_name: string<项目名称>
            @return tuple
        '''
        config_file = "{}/nginx/node_{}.conf".format(public.get_vhost_path(), project_name)
        if not os.path.exists(config_file):
            return False, False

        config_body = public.readFile(config_file)
        if not config_body:
            return False, False

        is_ssl, is_force_ssl = False, False
        if config_body.find('ssl_certificate') != -1:
            is_ssl = True
        if config_body.find('HTTP_TO_HTTPS_START') != -1:
            is_force_ssl = True
        return is_ssl, is_force_ssl

    def exists_apache_ssl(self, project_name):
        '''
            @name 判断项目是否配置Apache SSL配置
            @author hwliang<2021-08-09>
            @param project_name: string<项目名称>
            @return bool
        '''
        config_file = "{}/apache/node_{}.conf".format(public.get_vhost_path(), project_name)
        if not os.path.exists(config_file):
            return False, False

        config_body = public.readFile(config_file)
        if not config_body:
            return False, False

        is_ssl, is_force_ssl = False, False
        if config_body.find('SSLCertificateFile') != -1:
            is_ssl = True
        if config_body.find('HTTP_TO_HTTPS_START') != -1:
            is_force_ssl = True
        return is_ssl, is_force_ssl

    def set_apache_config(self, project_find):
        '''
            @name 设置Apache配置
            @author hwliang<2021-08-09>
            @param project_find: dict<项目信息>
            @return bool
        '''
        project_name = project_find['name']

        # 处理域名和端口
        ports = []
        domains = []
        for d in project_find['project_config']['domains']:
            domain_tmp = d.split(':')
            if len(domain_tmp) == 1: domain_tmp.append(80)
            if not int(domain_tmp[1]) in ports:
                ports.append(int(domain_tmp[1]))
            if not domain_tmp[0] in domains:
                domains.append(domain_tmp[0])

        config_file = "{}/apache/node_{}.conf".format(self._vhost_path, project_name)
        template_file = "{}/template/apache/node_http.conf".format(self._vhost_path)
        config_body = public.readFile(template_file)
        apache_config_body = ''

        # 旧的配置文件是否配置SSL
        is_ssl, is_force_ssl = self.exists_apache_ssl(project_name)
        if is_ssl:
            if not 443 in ports: ports.append(443)

        from panelSite import panelSite
        s = panelSite()

        # 根据端口列表生成配置
        for p in ports:
            # 生成SSL配置
            ssl_config = ''
            if p == 443 and is_ssl:
                ssl_key_file = "{vhost_path}/cert/{project_name}/privkey.pem".format(project_name=project_name,
                                                                                     vhost_path=public.get_vhost_path())
                if not os.path.exists(ssl_key_file): continue  # 不存在证书文件则跳过
                ssl_config = '''#SSL
    SSLEngine On
    SSLCertificateFile {vhost_path}/cert/{project_name}/fullchain.pem
    SSLCertificateKeyFile {vhost_path}/cert/{project_name}/privkey.pem
    SSLCipherSuite EECDH+CHACHA20:EECDH+CHACHA20-draft:EECDH+AES128:RSA+AES128:EECDH+AES256:RSA+AES256:EECDH+3DES:RSA+3DES:!MD5
    SSLProtocol All -SSLv2 -SSLv3 -TLSv1
    SSLHonorCipherOrder On'''.format(project_name=project_name, vhost_path=public.get_vhost_path())
            else:
                if is_force_ssl:
                    ssl_config = '''#HTTP_TO_HTTPS_START
    <IfModule mod_rewrite.c>
        RewriteEngine on
        RewriteCond %{SERVER_PORT} !^443$
        RewriteRule (.*) https://%{SERVER_NAME}$1 [L,R=301]
    </IfModule>
    #HTTP_TO_HTTPS_END'''

            # 多服务下切换端口
            if public.get_multi_webservice_status() and str(p) in ['80', '443']:
                if str(p) == '80':
                    p = 8288
                else:
                    p = 8290

            # 生成vhost主体配置
            apache_config_body += config_body.format(
                site_path=project_find['path'],
                server_name='{}.{}'.format(p, project_name),
                domains=' '.join(domains),
                log_path=public.get_logs_path(),
                server_admin='admin@{}'.format(project_name),
                url='http://127.0.0.1:{}'.format(project_find['project_config']['port']),
                port=p,
                ssl_config=ssl_config,
                project_name=project_name
            )
            apache_config_body += "\n"

            # 添加端口到主配置文件
            if not p in [80] and not public.get_multi_webservice_status():
                s.apacheAddPort(p)

        # 写.htaccess
        rewrite_file = "{}/.htaccess".format(project_find['path'])
        if not os.path.exists(rewrite_file): public.writeFile(rewrite_file,
                                                              '# Please fill in the URLrewrite rules or custom Apache config here\n')

        # 写配置文件
        public.writeFile(config_file, apache_config_body)
        return True

    def set_ols_config(self, project_find):
        project_name = project_find['name']
        project_port = project_find['project_config']['port']
        domains = project_find['project_config']['domains']

        # 路径与基础检查
        vhost_dir = public.get_panel_path() + '/vhost/openlitespeed/'
        detail_dir = vhost_dir + 'detail/'
        listen_dir = vhost_dir + 'listen/'
        for path in [detail_dir, listen_dir]:
            if not os.path.exists(path): os.makedirs(path)

        # 生成虚拟主机
        vhost_main_file = vhost_dir + project_name + '.conf'
        vhost_main_body = """virtualhost {name} {{
        vhRoot {path}
        configFile {detail_dir}{name}.conf
        allowSymbolLink 1
        enableScript 1
        restrained 1
        setUIDMode 0
    }}""".format(name=project_name, path=project_find['path'], detail_dir=detail_dir)
        public.writeFile(vhost_main_file, vhost_main_body)

        # 生成Host
        detail_file = detail_dir + project_name + '.conf'
        conf_body = '''docRoot                   $VH_ROOT
    vhDomain                  $VH_NAME
    adminEmails               admin@{name}
    enableGzip                1

    errorlog /www/wwwlogs/{name}_ols.error_log {{
      useServer               0
      logLevel                ERROR
      rollingSize             10M
    }}

    accesslog /www/wwwlogs/{name}_ols.access_log {{
      useServer               0
      logFormat               '%{{X-Forwarded-For}}i %h %l %u %t "%r" %>s %b "%{{Referer}}i" "%{{User-Agent}}i"'
      logHeaders              5
      rollingSize             10M
      keepDays                10
    }}

    extprocessor {name}_proxy {{
      type                    proxy
      address                 127.0.0.1:{node_port}
      maxConns                100
      pcKeepAliveTimeout      60
      initTimeout             60
      retryTimeout            0
      respBuffer              0
    }}

    context / {{
      type                    proxy
      handler                 {name}_proxy
      addDefaultCharset       off
    }}

    rewrite  {{
      enable                  1
      autoLoadHtaccess        1
    }}
    '''.format(name=project_name, node_port=project_port)
        public.writeFile(detail_file, conf_body)

        # 处理监听器映射
        # 提取端口和对应的域名
        port_map = {}
        for d in domains:
            tmp = d.split(':')
            p = tmp[1] if len(tmp) > 1 else "80"
            if p not in port_map: port_map[p] = []
            port_map[p].append(tmp[0])

        # 检查 SSL 状态 (参考原 Apache 逻辑)
        is_ssl, _ = self.exists_apache_ssl(project_name)
        if is_ssl and "443" not in port_map:
            # 如果有证书但域名列表没写443，默认把所有域名映射到443
            port_map["443"] = [d.split(':')[0] for d in domains]

        for p, ds in port_map.items():
            listen_file = "{}{}.conf".format(listen_dir, p)
            if not os.path.exists(listen_file): continue

            content = public.readFile(listen_file)

            # 构造映射行：map 项目名 域名1,域名2
            domain_str = ",".join(ds)
            map_line = "\tmap\t{}\t{}\n".format(project_name, domain_str)

            # 如果该项目已在 map 中，先正则替换或跳过，这里采用简单判断
            if "map\t{}\t".format(project_name) in content:
                import re
                content = re.sub(r"map\t{}\t.*?\n".format(project_name), map_line, content)
            else:
                # 插入到最后一个花括号之前
                last_brace_index = content.rfind('}')
                if last_brace_index != -1:
                    content = content[:last_brace_index] + map_line + content[last_brace_index:]

            public.writeFile(listen_file, content)

        return public.return_message(0, 0, True)

    def unbind_extranet(self, get):
        '''
            @name 解绑外网
            @author hwliang<2021-08-09>
            @param get<dict_obj>{
                project_name: string<项目名称>
            }
            @return dict
        '''
        # 校验参数
        try:
            get.validate([
                Param('project_name').String(),
            ], [
                public.validate.trim_filter(),
            ])
        except Exception as ex:
            public.print_log("error info: {}".format(ex))
            return public.return_message(-1, 0, str(ex))

        project_name = get.project_name.strip()
        self.clear_config(project_name)
        public.serviceReload()
        project_find = self.get_project_find(project_name)
        project_find['project_config']['bind_extranet'] = 0
        public.M('sites').where("id=?", (project_find['id'],)).setField('project_config',
                                                                        json.dumps(project_find['project_config']))
        public.WriteLog(self._log_name, 'Node project {}, disable the mapping'.format(project_name))
        return_message = public.return_data(True, 'Disabled successfully')
        del return_message['status']
        return public.return_message(0, 0, return_message)

    def get_project_pids(self, get=None, pid=None, without_request=False):
        '''
            @name 获取项目进程pid列表
            @author hwliang<2021-08-10>
            @param pid: string<项目pid>
            @return list
        '''
        if get: pid = int(get.pid)
        if not self._pids: self._pids = psutil.pids()
        project_pids = []

        for i in self._pids:
            try:
                p = psutil.Process(i)
                if p.status() == "zombie":
                    continue
                if p.ppid() == pid:
                    if i in project_pids:
                        continue
                    project_pids.append(i)
            except:
                continue

        other_pids = []
        for i in project_pids:
            other_pids += self.get_project_pids(pid=i)['message']
        if os.path.exists('/proc/{}'.format(pid)):
            project_pids.append(pid)

        all_pids = list(set(project_pids + other_pids))
        if not all_pids:
            all_pids = self.get_other_pids(pid)['message']

        # public.print_log("all_pids -- {}".format(all_pids))
        def convert_to_int(item):
            try:
                return int(item)
            except ValueError:
                return item

        # 将所有元素转换为整数后进行排序
        sorted_pids = sorted(all_pids, key=convert_to_int)

        if without_request:
            return sorted_pids

        return public.return_message(0, 0, sorted_pids)

    def get_other_pids(self, pid):
        '''
            @name 获取其他进程pid列表
            @author hwliang<2021-08-10>
            @param pid: string<项目pid>
            @return list
        '''
        project_name = None
        for pid_name in os.listdir(self._node_pid_path):
            pid_file = '{}/{}'.format(self._node_pid_path, pid_name)
            # s_pid = int(public.readFile(pid_file))
            data = public.readFile(pid_file)
            if isinstance(data, str) and data:
                data = data.strip()
                if not data.isdigit():
                    return public.return_message(0, 0, [])
                s_pid = int(data)
            else:
                return public.return_message(0, 0, [])
            if pid == s_pid:
                project_name = pid_name[:-4]
                break
        project_find = self.get_project_find(project_name)
        if not project_find: return public.return_message(0, 0, [])
        if not self._pids: self._pids = psutil.pids()
        all_pids = []
        for i in self._pids:
            try:
                p = psutil.Process(i)
                if p.cwd() == project_find['path']:
                    pname = p.name()
                    if pname in ['node', 'npm', 'pm2', 'yarn'] or pname.find('node ') == 0:
                        cmdline = ','.join(p.cmdline())
                        if cmdline.find('God Daemon') != -1: continue
                        env_list = p.environ()
                        if 'name' in env_list:
                            if not env_list['name'] == project_name: continue
                        if 'NODE_PROJECT_NAME' in env_list:
                            if not env_list['NODE_PROJECT_NAME'] == project_name: continue
                        all_pids.append(i)
            except:
                continue
        return public.return_message(0, 0, all_pids)

    def get_project_state_by_cwd(self, project_name):
        '''
            @name 通过cwd获取项目状态
            @author hwliang<2022-01-17>
            @param project_name<string> 项目名称
            @return bool or list
        '''
        project_find = self.get_project_find(project_name)
        self._pids = psutil.pids()
        if not project_find: return []
        all_pids = []
        for i in self._pids:
            try:
                p = psutil.Process(i)
                if p.cwd() == project_find['path']:
                    pname = p.name()
                    if pname in ['node', 'npm', 'pm2', 'yarn'] or pname.find('node ') == 0:
                        cmdline = ','.join(p.cmdline())
                        if cmdline.find('God Daemon') != -1: continue
                        env_list = p.environ()
                        if 'name' in env_list:
                            if not env_list['name'] == project_name: continue
                        if 'NODE_PROJECT_NAME' in env_list:
                            if not env_list['NODE_PROJECT_NAME'] == project_name: continue
                        all_pids.append(i)
            except:
                continue
        if all_pids:
            pid_file = "{}/{}.pid".format(self._node_pid_path, project_name)
            public.writeFile(pid_file, str(all_pids[0]))
            return all_pids
        return False

    def kill_pids(self, get=None, pids=None):
        '''
            @name 结束进程列表
            @author hwliang<2021-08-10>
            @param pids: string<进程pid列表>
            @return dict
        '''
        if get: pids = get.pids
        if not pids:
            return_message = public.return_data(True, 'No process')
            del return_message['status']
            return public.return_message(0, 0, return_message)
        pids = sorted(pids, reverse=True)
        for i in pids:
            try:
                p = psutil.Process(i)
                p.kill()
            except:
                pass
        return_message = public.return_data(True, 'The process has all ended')
        del return_message['status']
        return public.return_message(0, 0, return_message)

    def start_project(self, get):
        '''
            @name 启动项目
            @author hwliang<2021-08-09>
            @param get<dict_obj>{
                project_name: string<项目名称>
            }
            @return dict
        '''
        # 校验参数
        try:
            get.validate([
                Param('project_name').String(),
            ], [
                public.validate.trim_filter(),
            ])
        except Exception as ex:
            public.print_log("error info: {}".format(ex))
            return public.return_message(-1, 0, str(ex))

        pid_file = "{}/{}.pid".format(self._node_pid_path, get.project_name)
        if os.path.exists(pid_file):
            self.stop_project(get)

        project_find = self.get_project_find(get.project_name)
        if not project_find:
            return_message = public.return_error(public.lang('Item does not exist'))
            del return_message['status']
            return public.return_message(-1, 0, return_message)

        if not os.path.exists(project_find['path']):
            error_msg = 'Startup failed, Nodejs project {}, running directory {} does not exist!'.format(
                get.project_name, project_find['path'])
            public.WriteLog(self._log_name, error_msg)
            return_message = public.return_error(error_msg)
            del return_message['status']
            return public.return_message(-1, 0, return_message)

        # 是否安装依赖模块？
        package_file = "{}/package.json".format(project_find['path'])
        package_info = {}
        if os.path.exists(package_file):
            node_modules_path = "{}/node_modules".format(project_find['path'])
            if not os.path.exists(node_modules_path):
                return_message = public.return_error(public.lang(
                    'Please go to the [Module] and click [One-key install] to install the module dependencies!'))
                del return_message['status']
                return public.return_message(-1, 0, return_message)
            package_info = json.loads(public.readFile(package_file))
        if not package_info: package_info['scripts'] = {}
        if 'scripts' not in package_info: package_info['scripts'] = {}
        try:
            scripts_keys = package_info['scripts'].keys()
        except:
            scripts_keys = []

        # 前置准备
        nodejs_version = project_find['project_config']['nodejs_version']
        node_bin = self.get_node_bin(nodejs_version)
        pkg_manager = self._normalize_package_manager(project_find['project_config'].get('pkg_manager', project_find[
            'project_config'].get('package_manager', 'npm')))
        project_script = project_find['project_config']['project_script'].strip().replace('  ', ' ')
        if project_script[:3] == 'pm2':  # PM2启动方式处理
            project_script = project_script.replace('pm2 ', 'pm2 -u {} -n {} '.format(
                project_find['project_config']['run_user'], get.project_name))
            project_find['project_config']['run_user'] = 'root'
        log_file = "{}/{}.log".format(self._node_logs_path, get.project_name)
        if not project_script:
            return_message = public.return_error(public.lang('No startup script configured'))
            del return_message['status']
            return public.return_message(-1, 0, return_message)

        last_env = self.get_last_env(nodejs_version, project_find['path'])
        project_port = project_find['project_config'].get('port', '')
        port_export = 'export PORT="{}"\n'.format(project_port) if project_port else ''

        # 生成启动脚本
        if os.path.exists(project_script):
            start_cmd = '''{last_env}
export NODE_PROJECT_NAME="{project_name}"
{port_export}cd {project_cwd}
nohup {node_bin} {project_script} >> {log_file} 2>&1 &
echo $! > {pid_file}
'''.format(
                project_cwd=project_find['path'],
                node_bin=node_bin,
                project_script=project_script,
                log_file=log_file,
                pid_file=pid_file,
                last_env=last_env,
                project_name=get.project_name,
                port_export=port_export
            )
        elif project_script in scripts_keys:
            package_run_cmd = self._get_package_manager_run_cmd(nodejs_version, pkg_manager, project_script)
            if not package_run_cmd:
                return_message = public.return_error(
                    'The specified package manager is not available: {}'.format(pkg_manager))
                del return_message['status']
                return public.return_message(-1, 0, return_message)
            start_cmd = '''{last_env}
export NODE_PROJECT_NAME="{project_name}"
{port_export}cd {project_cwd}
nohup {package_run_cmd} >> {log_file} 2>&1 &
echo $! > {pid_file}
'''.format(
                project_cwd=project_find['path'],
                package_run_cmd=package_run_cmd,
                pid_file=pid_file,
                log_file=log_file,
                last_env=last_env,
                project_name=get.project_name,
                port_export=port_export
            )
        else:
            start_cmd = '''{last_env}
export NODE_PROJECT_NAME="{project_name}"
{port_export}cd {project_cwd}
nohup {project_script} >> {log_file} 2>&1 &
echo $! > {pid_file}
'''.format(
                project_cwd=project_find['path'],
                project_script=project_script,
                pid_file=pid_file,
                log_file=log_file,
                last_env=last_env,
                project_name=get.project_name,
                port_export=port_export
            )

        script_file = "{}/{}.sh".format(self._node_run_scripts, get.project_name)

        # 写入启动脚本
        public.writeFile(script_file, start_cmd)
        if os.path.exists(pid_file): os.remove(pid_file)

        # 处理前置权限
        public.ExecShell("chown -R {user}:{user} {project_cwd}".format(user=project_find['project_config']['run_user'],
                                                                       project_cwd=project_find['path']))
        public.ExecShell("chown -R www:www {}/vhost".format(self._nodejs_path))
        public.ExecShell("chmod 755 {} {} {}".format(self._nodejs_path, public.get_setup_path(), '/www'))
        public.set_own(script_file, project_find['project_config']['run_user'],
                       project_find['project_config']['run_user'])
        public.set_mode(script_file, 755)

        p = public.ExecShell("bash {}".format(script_file), user=project_find['project_config']['run_user'])

        time.sleep(1)
        n = 0
        while n < 5:
            if self.get_project_state_by_cwd(get.project_name): break
            n += 1
        if not os.path.exists(pid_file):
            p = '\n'.join(p)
            public.writeFile(log_file, p, "a+")
            if p.find('[Errno 0]') != -1:
                if os.path.exists('{}/bt_security'.format(public.get_plugin_path())):
                    return_message = public.return_error(
                        'The start command was intercepted by [Fort Tower Defense Privilege], please turn off {} user protection'.format(
                            project_find['project_config']['run_user']))
                    del return_message['status']
                    return public.return_message(-1, 0, return_message)
                return_message = public.return_error(public.lang(
                    'The startup command was intercepted by unknown security software, please check the installation software log'))
                del return_message['status']
                return public.return_message(-1, 0, return_message)
            return_message = public.return_error('failed to activate<pre>{}</pre>'.format(p))
            del return_message['status']
            return public.return_message(-1, 0, return_message)

        # 获取PID
        try:
            pid = int(public.readFile(pid_file))
        except:
            return public.return_error('Startup failed <br>{}'.format(public.GetNumLines(log_file, 20)))

        pids = self.get_project_pids(pid=pid, without_request=True)

        if not pids:
            if os.path.exists(pid_file): os.remove(pid_file)
            return_message = public.return_error('failed to activate<br>{}'.format(public.GetNumLines(log_file, 20)))
            del return_message['status']
            return public.return_message(-1, 0, return_message)
        return_message = public.return_data(True, 'Successfully started', pids)
        del return_message['status']
        return public.return_message(0, 0, return_message)

    def stop_project(self, get):
        '''
            @name 停止项目
            @author hwliang<2021-08-09>
            @param get<dict_obj>{
                project_name: string<项目名称>
                is_power_on: boolean<<UNK>> #标记是否自动关闭自动重启
            }
            @return dict
        '''
        project_find = self.get_project_find(get.project_name)
        if not project_find:
            return_message = public.return_error(public.lang('Project does not exist'))
            del return_message['status']
            return public.return_message(-1, 0, return_message)
        project_script = project_find['project_config']['project_script'].strip().replace('  ', ' ')
        pid_file = "{}/{}.pid".format(self._node_pid_path, get.project_name)
        if project_script.find('pm2 start') != -1:  # 处理PM2启动的项目
            nodejs_version = project_find['project_config']['nodejs_version']
            last_env = self.get_last_env(nodejs_version, project_find['path'])
            project_script = project_script.replace('pm2 start', 'pm2 stop')
            public.ExecShell('''{}
cd {}
{}'''.format(last_env, project_find['path'], project_script))
        else:
            pid_file = "{}/{}.pid".format(self._node_pid_path, get.project_name)
            if not os.path.exists(pid_file):
                return_message = public.return_error(public.lang('Project did not start'))
                del return_message['status']
                return public.return_message(-1, 0, return_message)
            data = public.readFile(pid_file)
            if isinstance(data, str) and data:
                pid = int(data)
                pids = self.get_project_pids(pid=pid, without_request=True)
            else:
                return_message = public.return_error(public.lang('Project did not start'))
                del return_message['status']
                return public.return_message(-1, 0, return_message)
            if not pids:
                return_message = public.return_error(public.lang('Project did not start'))
                del return_message['status']
                return public.return_message(-1, 0, return_message)
            self.kill_pids(pids=pids)
        if os.path.exists(pid_file): os.remove(pid_file)
        time.sleep(0.5)
        pids = self.get_project_state_by_cwd(get.project_name)
        if pids: self.kill_pids(pids=pids)

        # 停用项目自启
        if get.get('is_power_on') in ['True', 'true', 1, '1']:
            data = project_find['project_config']
            data = {
                "project_cwd": data['project_cwd'],
                "project_name": data['project_name'],
                "project_script": data['project_script'],
                "port": str(data['port']),
                "run_user": data['run_user'],
                "nodejs_version": data['nodejs_version'],
                "project_ps": project_find['ps'],
                "is_power_on": 0
            }
            self.modify_project(public.to_dict_obj(data))
        return_message = public.return_data(True, 'Stopped successfully')
        del return_message['status']
        return public.return_message(0, 0, return_message)

    def restart_project(self, get):
        '''
            @name 重启项目
            @author hwliang<2021-08-09>
            @param get<dict_obj>{
                project_name: string<项目名称>
            }
            @return dict
        '''
        # 校验参数
        try:
            get.validate([
                Param('project_name').String(),
            ], [
                public.validate.trim_filter(),
            ])
        except Exception as ex:
            public.print_log("error info: {}".format(ex))
            return public.return_message(-1, 0, str(ex))

        res = self.stop_project(get)
        if res['status'] == -1: return res
        res = self.start_project(get)
        if res['status'] == -1: return res
        return_message = public.return_data(True, 'Successful restart')
        del return_message['status']
        return public.return_message(0, 0, return_message)

    # xss 防御
    def xsssec(self, text):
        return text.replace('<', '&lt;').replace('>', '&gt;')

    def get_project_log(self, get):
        '''
            @name 获取项目日志
            @author hwliang<2021-08-09>
            @param get<dict_obj>{
                project_name: string<项目名称>
            }
            @return dict
        '''
        # 校验参数
        try:
            get.validate([
                Param('project_name').String(),
            ], [
                public.validate.trim_filter(),
            ])
        except Exception as ex:
            public.print_log("error info: {}".format(ex))
            return public.return_message(-1, 0, str(ex))

        project_find = self.get_project_find(get.project_name)
        if not project_find: return public.returnMsg(False, '项目不存在')
        if "log_path" not in project_find['project_config']:
            log_file = "{}/{}.log".format(self._node_logs, project_find["name"])
        else:
            log_file = "{}/{}.log".format(project_find['project_config']["log_path"], project_find["name"])

        if not os.path.exists(log_file):
            return public.return_message(-1, 0, public.lang("The log file does not exist."))
        return public.return_message(0, 0, self.xsssec(public.GetNumLines(log_file, 200)))

    def get_project_load_info(self, get=None, project_name=None):
        '''
            @name 获取项目负载信息
            @author hwliang<2021-08-12>
            @param get<dict_obj>{
                project_name: string<项目名称>
            }
            @return dict
        '''
        if get: project_name = get.project_name.strip()
        load_info = {}
        pid_file = "{}/{}.pid".format(self._node_pid_path, project_name)
        if not os.path.exists(pid_file):
            return public.return_message(0, 0, load_info)
        data = public.readFile(pid_file)
        if isinstance(data, str) and data:
            pid = int(data)
            pids = self.get_project_pids(pid=pid)['message']
        else:
            return public.return_message(0, 0, load_info)
        if not pids:
            return public.return_message(0, 0, load_info)
        for i in pids:
            process_info = self.get_process_info_by_pid(i)
            if process_info: load_info[i] = process_info
        return public.return_message(0, 0, load_info)

    def object_to_dict(self, obj):
        '''
            @name 将对象转换为字典
            @author hwliang<2021-08-09>
            @param obj<object>
            @return dict
        '''
        result = {}
        for name in dir(obj):
            value = getattr(obj, name)
            if not name.startswith('__') and not callable(value) and not name.startswith('_'): result[name] = value
        return result

    def list_to_dict(self, data):
        '''
            @name 将列表转换为字典
            @author hwliang<2021-08-09>
            @param data<list>
            @return dict
        '''
        result = []
        for s in data:
            result.append(self.object_to_dict(s))
        return result

    def get_connects(self, pid):
        '''
            @name 获取进程连接信息
            @author hwliang<2021-08-09>
            @param pid<int>
            @return dict
        '''
        connects = 0
        try:
            if pid == 1: return connects
            tp = '/proc/' + str(pid) + '/fd/'
            if not os.path.exists(tp): return connects
            for d in os.listdir(tp):
                fname = tp + d
                if os.path.islink(fname):
                    l = os.readlink(fname)
                    if l.find('socket:') != -1: connects += 1
        except:
            pass
        return connects

    def format_connections(self, connects):
        '''
            @name 获取进程网络连接信息
            @author hwliang<2021-08-09>
            @param connects<pconn>
            @return list
        '''
        result = []
        for i in connects:
            raddr = i.raddr
            if not i.raddr:
                raddr = ('', 0)
            laddr = i.laddr
            if not i.laddr:
                laddr = ('', 0)
            result.append({
                "fd": i.fd,
                "family": i.family,
                "local_addr": laddr[0],
                "local_port": laddr[1],
                "client_addr": raddr[0],
                "client_rport": raddr[1],
                "status": i.status
            })
        return result

    def get_process_info_by_pid(self, pid):
        '''
            @name 获取进程信息
            @author hwliang<2021-08-12>
            @param pid: int<进程id>
            @return dict
        '''
        process_info = {}
        try:
            if not os.path.exists('/proc/{}'.format(pid)): return process_info
            p = psutil.Process(pid)
            status_ps = {'sleeping': 'Sleeping', 'running': 'Running'}
            with p.oneshot():
                p_mem = p.memory_full_info()
                if p_mem.uss + p_mem.rss + p_mem.pss + p_mem.data == 0: return process_info
                p_state = p.status()
                if p_state in status_ps: p_state = status_ps[p_state]
                # process_info['exe'] = p.exe()
                process_info['name'] = p.name()
                process_info['pid'] = pid
                process_info['ppid'] = p.ppid()
                process_info['create_time'] = int(p.create_time())
                process_info['status'] = p_state
                process_info['user'] = p.username()
                process_info['memory_used'] = p_mem.uss
                process_info['cpu_percent'] = self.get_cpu_precent(p)
                process_info['io_write_bytes'], process_info['io_read_bytes'] = self.get_io_speed(p)
                process_info['connections'] = self.format_connections(p.connections())
                process_info['connects'] = self.get_connects(pid)
                process_info['open_files'] = self.list_to_dict(p.open_files())
                process_info['threads'] = p.num_threads()
                process_info['exe'] = ' '.join(p.cmdline())
                return process_info
        except:
            return process_info

    def get_io_speed(self, p):
        '''
            @name 获取磁盘IO速度
            @author hwliang<2021-08-12>
            @param p: Process<进程对像>
            @return list
        '''

        skey = "io_speed_{}".format(p.pid)
        old_pio = cache.get(skey)
        if not hasattr(p, 'io_counters'): return 0, 0
        pio = p.io_counters()
        if not old_pio:
            cache.set(skey, [pio, time.time()], 3600)
            # time.sleep(0.1)
            old_pio = cache.get(skey)
            pio = p.io_counters()

        old_write_bytes = old_pio[0].write_bytes
        old_read_bytes = old_pio[0].read_bytes
        old_time = old_pio[1]

        new_time = time.time()
        write_bytes = pio.write_bytes
        read_bytes = pio.read_bytes

        cache.set(skey, [pio, new_time], 3600)

        write_speed = int((write_bytes - old_write_bytes) / (new_time - old_time))
        read_speed = int((read_bytes - old_read_bytes) / (new_time - old_time))

        return write_speed, read_speed

    def get_cpu_precent(self, p):
        '''
            @name 获取进程cpu使用率
            @author hwliang<2021-08-09>
            @param p: Process<进程对像>
            @return dict
        '''
        skey = "cpu_pre_{}".format(p.pid)
        old_cpu_times = cache.get(skey)

        process_cpu_time = self.get_process_cpu_time(p.cpu_times())
        if not old_cpu_times:
            cache.set(skey, [process_cpu_time, time.time()], 3600)
            # time.sleep(0.1)
            old_cpu_times = cache.get(skey)
            process_cpu_time = self.get_process_cpu_time(p.cpu_times())

        old_process_cpu_time = old_cpu_times[0]
        old_time = old_cpu_times[1]
        new_time = time.time()
        cache.set(skey, [process_cpu_time, new_time], 3600)
        percent = round(100.00 * (process_cpu_time - old_process_cpu_time) / (new_time - old_time) / psutil.cpu_count(),
                        2)
        return percent

    def get_process_cpu_time(self, cpu_times):
        cpu_time = 0.00
        for s in cpu_times: cpu_time += s
        return cpu_time

    def get_project_run_state(self, get=None, project_name=None):
        '''
            @name 获取项目运行状态
            @author hwliang<2021-08-12>
            @param get<dict_obj>{
                project_name: string<项目名称>
            }
            @param project_name<string> 项目名称
            @return bool
        '''
        if get: project_name = get.project_name.strip()
        pid_file = "{}/{}.pid".format(self._node_pid_path, project_name)
        if not os.path.exists(pid_file):
            return public.return_message(0, 0, False)
        data = public.readFile(pid_file)
        if isinstance(data, str) and data:
            if not data.isdigit():
                return public.return_message(0, 0, False)
            pid = int(data)
            pids = self.get_project_pids(pid=pid, without_request=True)
        else:
            return public.return_message(0, 0, self.get_project_state_by_cwd(project_name))
        if not pids:
            return self.get_project_state_by_cwd(project_name)
        return public.return_message(0, 0, True)

    def _get_project_run_state(self, get=None, project_name=None):
        '''
            @name 获取项目运行状态
            @author hwliang<2021-08-12>
            @param get<dict_obj>{
                project_name: string<项目名称>
            }
            @param project_name<string> 项目名称
            @return bool
        '''
        if get: project_name = get.project_name.strip()
        pid_file = "{}/{}.pid".format(self._node_pid_path, project_name)
        if not os.path.exists(pid_file):
            return False
        data = public.readFile(pid_file)
        if isinstance(data, str) and data:
            pid = int(data)
            pids = self.get_project_pids(pid=pid)['message']
        else:
            return self.get_project_state_by_cwd(project_name)

        if not pids:
            return self.get_project_state_by_cwd(project_name)

        return True

    def get_project_find(self, project_name):
        '''
            @name 获取指定项目配置
            @author hwliang<2021-08-09>
            @param project_name<string> 项目名称
            @return dict
        '''
        project_info = public.M('sites').where('project_type=? AND name=?', ('Node', project_name)).find()
        if not project_info: return False
        project_info['project_config'] = json.loads(project_info['project_config'])
        return project_info

    def get_project_info(self, get):
        '''
            @name 获取指定项目信息
            @author hwliang<2021-08-09>
            @param get<dict_obj>{
                project_name: string<项目名称>
            }
            @return dict
        '''
        # 校验参数
        try:
            get.validate([
                Param('project_name').String(),
            ], [
                public.validate.trim_filter(),
            ])
        except Exception as ex:
            public.print_log("error info: {}".format(ex))
            return public.return_message(-1, 0, str(ex))
        project_info = public.M('sites').where('project_type=? AND name=?', ('Node', get.project_name)).find()
        if not project_info:
            return_message = public.return_error(public.lang('The specified item does not exist!'))
            del return_message['status']
            return public.return_message(-1, 0, return_message)
        project_info = self.get_project_stat(project_info)
        return public.return_message(0, 0, project_info)

    def get_project_stat(self, project_info):
        '''
            @name 获取项目状态信息
            @author hwliang<2021-08-09>
            @param project_info<dict> 项目信息
            @return list
        '''
        project_info['project_config'] = json.loads(project_info['project_config'])
        project_info['load_info'] = {}
        if ("pm2_name" in project_info['project_config'] and
            "project_type" in project_info['project_config'] and
            project_info['project_config']["project_type"] == "pm2") or "pm2" in project_info['project_config'][
            'project_script']:
            from mod.project.nodejs import pm2Mod
            pm2_list = pm2Mod.main().get_jlist()
            project_info['run'] = False
            pm2_name = project_info['project_config'].get("pm2_name", project_info['name'])
            pm2_pids = []
            project_info['project_config']['watch'] = True if project_info['project_config'].get('watch', False) in [
                'True', 'true', True] else False

            for pm2_info in pm2_list:
                if pm2_info.get("name") in ("pm2-sysmonit", "pm2-logrotate"):
                    continue
                env_projectname = ""
                if "pm2_env" in pm2_info and "NODE_PROJECT_NAME" in pm2_info["pm2_env"]:
                    env_projectname = pm2_info["pm2_env"]["NODE_PROJECT_NAME"]
                if pm2_name != pm2_info.get("name") and pm2_name != env_projectname:
                    continue
                project_info['run'] = pm2_info.get("pm2_env").get("status") == "online"
                if project_info['run']:
                    pm2_pids.append(pm2_info.get("pid"))
                    break
            project_info['load_info'] = self.get_pm2_load_info_new(pm2_pids)
        else:
            project_info['run'] = self._get_project_run_state(project_name=project_info['name'])
            if project_info['run']:
                project_info['load_info'] = self.get_project_load_info(project_name=project_info['name'])['message']

        project_info['ssl'] = self.get_ssl_end_date(project_name=project_info['name'])
        project_info['listen'] = []
        project_info['listen_ok'] = True
        if project_info['load_info']:
            for pid in project_info['load_info'].keys():
                if not pid: continue
                if not 'connections' in project_info['load_info'][pid]:
                    project_info['load_info'][pid]['connections'] = []
                for conn in project_info['load_info'][pid]['connections']:
                    if not conn['status'] == 'LISTEN': continue
                    if not conn['local_port'] in project_info['listen']:
                        project_info['listen'].append(conn['local_port'])
            if project_info['listen']:
                if project_info['project_config']['port'] is None:
                    # 端口回填
                    project_info['project_config']['port'] = project_info['listen'][0]
                    try:
                        update_data = {
                            'project_config': json.dumps(project_info['project_config'])
                        }
                        public.M('sites').where('name=?', (project_info['name'],)).update(update_data)
                    except:
                        pass
                project_info['listen_ok'] = project_info['project_config']['port'] in project_info['listen']

        return project_info

    def get_pm2_load_info_new(self, pids: list):
        '''
            @name 获取项目负载信息
            @author hwliang<2021-08-12>
            @param get<dict_obj>{
                project_name: string<项目名称>
            }
            @return dict
        '''
        load_info = {}
        for i in pids:
            process_info = self.get_process_info_by_pid(i)
            if process_info: load_info[i] = process_info
        return load_info

    # 获取项目状态，支持PM2/node
    def get_project_run(self, project_name, project_type):
        try:
            if project_type == 'node':
                return self._get_project_run_state(project_name=project_name)
            else:
                from mod.project.nodejs import pm2Mod
                pm2_list = pm2Mod.main().get_jlist()
                pm2_name = project_name
                for pm2_info in pm2_list:
                    if pm2_info.get("name") in ("pm2-sysmonit", "pm2-logrotate"):
                        continue
                    env_projectname = ""
                    if "pm2_env" in pm2_info and "NODE_PROJECT_NAME" in pm2_info["pm2_env"]:
                        env_projectname = pm2_info["pm2_env"]["NODE_PROJECT_NAME"]
                    if pm2_name != pm2_info.get("name") and pm2_name != env_projectname:
                        continue
                    return pm2_info.get("pm2_env").get("status") == "online"
                return False
        except Exception as e:
            return False

    def get_project_state(self, project_name):
        '''
            @name 获取项目状态
            @author hwliang<2021-08-09>
            @param project_name: string<项目名称>
            @return dict
        '''
        project_info = public.M('sites').where('project_type=? AND name=?', ('Node', project_name)).find()
        if not project_info: return False
        return project_info['status']

    def get_project_listen(self, project_name):
        '''
            @name 获取项目监听端口
            @author hwliang<2021-08-09>
            @param project_name: string<项目名称>
            @return dict
        '''
        project_config = json.loads(public.M('sites').where('name=?', project_name).getField('project_config'))
        if 'listen_port' in project_config:
            return project_config['listen_port']
        return False

    def set_project_listen(self, get):
        '''
            @name 设置项目监听端口（请设置与实际端口相符的，仅在自动获取不正确时使用）
            @author hwliang<2021-08-09>
            @param get<dict_obj>{
                project_name: string<项目名称>
                port: int<端口>
            }
            @return dict
        '''
        project_config = json.loads(public.M('sites').where('name=?', get.project_name).getField('project_config'))
        project_config['listen_port'] = get.port
        public.M('sites').where('name=?', get.project_name).save('project_config', json.dumps(project_config))
        public.WriteLog(self._log_name,
                        'Modify the port of the project [' + get.project_name + '] to [' + get.port + ']')
        return_message = public.return_data(True, 'Set successfully')
        del return_message['status']
        return public.return_message(0, 0, return_message)

    def set_project_nodejs_version(self, get):
        '''
            @name 设置nodejs版本
            @author hwliang<2021-08-09>
            @param get<dict_obj>{
                project_name: string<项目名称>
                nodejs_version: string<nodejs版本>
            }
            @return dict
        '''

        project_config = json.loads(public.M('sites').where('name=?', get.project_name).getField('project_config'))
        project_config['nodejs_version'] = get.nodejs_version
        public.M('sites').where('name=?', get.project_name).save('project_config', json.dumps(project_config))
        public.WriteLog(self._log_name,
                        'Modify the nodejs version of the project [' + get.project_name + '] to [' + get.nodejs_version + ']')
        return_message = public.return_data(True, 'Set successfully')
        del return_message['status']
        return public.return_message(0, 0, return_message)

    def get_project_nodejs_version(self, project_name):
        '''
            @name 获取nodejs版本
            @author hwliang<2021-08-09>
            @param project_name: string<项目名称>
            @return string
        '''

        project_config = json.loads(public.M('sites').where('name=?', project_name).getField('project_config'))
        if 'nodejs_version' in project_config: return project_config['nodejs_version']
        return False

    def check_port_is_used(self, port, sock=False):
        '''
            @name 检查端口是否被占用
            @author hwliang<2021-08-09>
            @param port: int<端口>
            @return bool
        '''
        if not isinstance(port, int): port = int(port)
        if port == 0: return False
        project_list = public.M('sites').where('status=? AND project_type=?', (1, 'Node')).field(
            'name,path,project_config').select()
        for project_find in project_list:
            project_config = json.loads(project_find['project_config'])
            if not 'port' in project_config: continue
            try:
                if int(project_config['port']) == port: return True
            except:
                pass
        if sock: return False
        return public.check_tcp('127.0.0.1', port)

    def get_project_run_state_byaotu(self, project_name):
        '''
            @name 获取项目运行状态
            @author hwliang<2021-08-09>
            @param project_name: string<项目名称>
            @return dict
        '''
        pid_file = "{}/{}.pid".format(self._node_pid_path, project_name)
        if not os.path.exists(pid_file): return False
        pid = public.readFile(pid_file)
        pids = self.get_project_pids(pid=pid, without_request=True)
        if not pids: return False
        return True

    # 废弃，重定向于script/project_daemon.py
    def auto_run(self):
        '''
            @name 自动启动所有项目
            @author hwliang<2021-08-09>
            @return bool
        '''
        project_list = public.M('sites').where('project_type=?', ('Node',)).field('name,path,project_config').select()
        get = public.dict_obj()
        success_count = 0
        error_count = 0
        for project_find in project_list:
            try:
                project_config = json.loads(project_find['project_config'])
                if project_config['is_power_on'] in [0, False, '0', None]: continue
                project_name = project_find['name']
                project_state = self._get_project_run_state(project_name=project_name)
                if not project_state:
                    get.project_name = project_name
                    result = self.start_project(get)['message']
                    if result['status'] == -1:
                        error_count += 1
                        error_msg = 'Automatically start Nodej project [' + project_name + '] failed!'
                        public.WriteLog(self._log_name, error_msg)
                        public.print_log(error_msg + ", " + result['error_msg'], 'ERROR')
                    else:
                        success_count += 1
                        success_msg = 'Automatically start the Nodej project [' + project_name + '] successfully!'
                        public.WriteLog(self._log_name, success_msg)
                        public.print_log(success_msg, 'INFO')
            except:
                error_count += 1
                public.print_log(public.get_error_info(), 'ERROR')
        if (success_count + error_count) < 1: return False
        dene_msg = 'A total of {} Nodejs projects need to be started, {} successfully and {} failed'.format(
            success_count + error_count, success_count, error_count)
        public.WriteLog(self._log_name, dene_msg)
        public.print_log(dene_msg, 'INFO')
        return True
