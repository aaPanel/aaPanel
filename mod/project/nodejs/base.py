# coding: utf-8
# -------------------------------------------------------------------
# aapanel
# -------------------------------------------------------------------
# Copyright (c) 2015-2099 aapanel(http://www.aapanel.com) All rights reserved.
# -------------------------------------------------------------------
# Author: wzz <wzz@aapanel.com>
# -------------------------------------------------------------------
# ------------------------------
# nodejs模型 - 通用基类
# ------------------------------
import json
import os
import re
import shutil
import sys
import time
from typing import Union

import psutil
from sqlalchemy.sql.operators import truediv

if "/www/server/panel/class" not in sys.path:
    sys.path.insert(0, "/www/server/panel/class")

import public

try:
    import idna
except:
    public.ExecShell('btpip install idna')
    import idna

try:
    from BTPanel import cache
except:
    pass


class NodeJs():

    def __init__(self):
        self.pm2_cmd = None
        self.pack_cmd = None
        self._pids = None
        self.get = None
        self.def_name = None
        self.nodejs_plugin_path = public.get_plugin_path('nodejs')
        self.panel_path = public.get_panel_path()
        self.vhost_path = '{}/vhost'.format(self.panel_path)
        self.npm_exec_log = '{}/logs/npm-exec.log'.format(self.panel_path)
        self._is_nginx_http3 = None
        self.nodejs_path = '{}/nodejs'.format(public.get_setup_path())
        self.log_name = 'Website - Node Project'
        self.node_logs_path = "/www/wwwlogs/nodejs"
        self.pm2_logs_path = "/www/wwwlogs/pm2"
        self.install_logs_path = "/www/wwwlogs/nodejs/install_logs"
        self.node_logs = '{}/vhost/logs'.format(self.nodejs_path)
        self.install_logs_file = None
        self.container_id = None
        self.manager = "npm"
        self.projectModel = None
        self.nodejs_bin = None
        self.nodejs_version = None
        self.set_strict_ssl = None
        self.node_pid_path = '{}/vhost/pids'.format(self.nodejs_path)
        self.node_run_scripts = '{}/vhost/scripts'.format(self.nodejs_path)
        self.pm2_config_path = '{}/vhost/pm2_configs'.format(self.nodejs_path)
        self.www_home = '/home/www'
        self.project_structure = {
            "nodejs": "NodeJS project",
            "pm2": "PM2 Project",
            "general": "Traditional Node project",
        }
        if not os.path.exists(self.node_run_scripts):
            os.makedirs(self.node_run_scripts, 493)
        if not os.path.exists(self.node_pid_path):
            os.makedirs(self.node_pid_path, 493)
        if not os.path.exists(self.node_logs_path):
            os.makedirs(self.node_logs_path, 493)
        if not os.path.exists(self.www_home):
            os.makedirs(self.www_home, 493)
            public.set_own(self.www_home, 'www')
        if not os.path.exists(self.install_logs_path):
            os.makedirs(self.install_logs_path, 493)
        if not os.path.exists(self.pm2_config_path):
            os.makedirs(self.pm2_config_path, 493)
        if not os.path.exists(self.pm2_logs_path):
            os.makedirs(self.pm2_logs_path, 493)

    def set_pack_cmd(self, nodejs_version):
        pack_path = "{}/{}/lib/node_modules/{}/bin".format(self.nodejs_path, nodejs_version, self.manager)
        if os.path.exists(pack_path) and os.path.isdir(pack_path):
            self.pack_cmd = pack_path
        return self

    def set_pm2_cmd(self, nodejs_version):
        pm2_path = "{}/{}/lib/node_modules/pm2/bin".format(self.nodejs_path, nodejs_version)
        if os.path.exists(pm2_path) and os.path.isdir(pm2_path):
            self.pm2_cmd = "{}/{}/bin/pm2".format(self.nodejs_path, nodejs_version)
        return self

    def set_self_get(self, get):
        self.get = get
        return self

    def set_install_logs(self, project_name: str) -> 'NodeJs':
        self.install_logs_file = os.path.join(self.install_logs_path, "{}_install.log".format(project_name))
        return self

    def get_strict_ssl(self) -> 'NodeJs':
        # self.set_strict_ssl = ["{}/{}".format(self.nodejs_bin, self.manager), "config", "set", "strict-ssl", "false"]
        self.set_strict_ssl = "{}/{} config set strict-ssl false".format(self.nodejs_bin, self.manager)
        return self

    def set_nodejs_bin(self) -> 'NodeJs':
        self.nodejs_bin = os.path.join(self.nodejs_path, self.nodejs_version, "bin")
        return self

    def set_nodejs_version(self, nodejs_version: str) -> 'NodeJs':
        self.nodejs_version = nodejs_version
        return self

    def set_def_name(self, def_name: str) -> 'NodeJs':
        self.def_name = def_name
        return self

    def wsResult(self, status: bool = True, msg: str = "", data: any = None, timestamp: int = None, code: int = 0,
                 args: any = None):
        rs = public.returnResult(status=status,msg=msg, data=data, timestamp=timestamp, code=code, args=args)
        rs["def_name"] = self.def_name
        return rs

    # 2024/6/25 下午2:40 获取日志类型的websocket返回值
    def exec_logs(self, get, command, cwd=None, write_log=False):
        '''
            @name 获取日志类型的websocket返回值
            @author wzz <2024/6/25 下午2:41>
            @param "data":{"参数名":""} <数据类型> 参数描述
            @return dict{"status":True/False,"msg":"提示信息"}
        '''
        if self.def_name is None: self.set_def_name(get.def_name)
        from subprocess import Popen, PIPE, STDOUT

        p = Popen(command, stdout=PIPE, stderr=STDOUT, cwd=cwd)

        while True:
            if p.poll() is not None:
                break

            line = p.stdout.readline()  # 非阻塞读取
            if line:
                try:
                    if hasattr(get, '_ws'):
                        get._ws.send(json.dumps(self.wsResult(
                            True,
                            "{}".format(line.decode('utf-8').rstrip()),
                        )))

                    if write_log:
                        public.WriteFile(self.install_logs_file, line.decode('utf-8').rstrip() + "\n", "a+")
                except:
                    continue
            else:
                break

    def get_install_cmd(self, package_name: str = None, is_global: bool = False, force: bool = False,
                        check_update: bool = False, *args, **kwargs) -> list:
        cmd = ["{}/{}".format(self.nodejs_bin, self.manager), "install"]
        if package_name is not None:
            cmd.append("{}".format(package_name))
        if is_global:
            cmd.append("-g")
        if force:
            cmd.append("--force")
        if check_update:
            cmd.append("npm-check-updates")
        for arg in args:
            cmd.append("{}".format(arg))
        for key in kwargs:
            cmd.append("--{} {}".format(key, kwargs[key]))
        return cmd

    def set_project_model(self, projectModel: str = None) -> 'NodeJs':
        if projectModel is None:
            self.projectModel = None
        elif projectModel == "nodejs":
            from mod.project.nodejs.nodeMod import main as nodeMod
            self.projectModel = nodeMod()
        elif projectModel == "pm2":
            from mod.project.nodejs.pm2Mod import main as pm2Mod
            self.projectModel = pm2Mod()
        elif projectModel == "general":
            from mod.project.nodejs.generalMod import main as generalMod
            self.projectModel = generalMod()
        else:
            self.projectModel = None
        return self

    def set_manager(self, manager: str) -> 'NodeJs':
        self.manager = manager
        return self

    # 2024/7/10 下午4:56 设置nodejs版本路径
    def set_nodejs_path(self, nodejs_path: str) -> 'NodeJs':
        self.nodejs_path = nodejs_path
        return self

    # 2024/7/10 下午4:56 获取已安装的nodejs版本列表
    def get_nodejs_version(self, get) -> list:
        try:
            from projectModel.nodejsModel import main
            return main().get_nodejs_version(get)
        except:
            return []

    # =========================================================
    # 版本运行时管理 - 扫描/汇总系统与NVM安装的node（插件不感知）
    # 机制：来源后缀软链目录 /www/server/nodejs/{version}-{source}
    # =========================================================
    _EXTRA_NODE_FLAG = '.aapanel-node-extra'

    def _probe_profile_env_nodes(self):
        '''
            @name 加载 /etc/profile 与 /root/.bashrc 后探测其暴露的 node / NVM_DIR
            背景: 面板守护进程不含用户 shell 启动环境, 仅靠 .bashrc/.profile 注入
            PATH 或 NVM_DIR 才可见的 node(nvm 自定义目录、/opt 等)常规 which 扫不到。
            必须以 bash -i(交互)执行, 否则 .bashrc 顶部 `case $- in *i*)` 非交互守卫
            会提前 return, nvm 安装器追加在文件末尾的 export 段不会执行。
            @return dict {nodes: list[str], nvm_dir: str, ok: bool}
        '''
        ret = {'nodes': [], 'nvm_dir': '', 'ok': False}
        script = (
            'export HOME="${HOME:-/root}"\n'
            'source /etc/profile >/dev/null 2>&1\n'
            '[ -f /root/.bashrc ] && source /root/.bashrc >/dev/null 2>&1\n'
            '[ -n "$HOME" ] && [ -f "$HOME/.bashrc" ] && source "$HOME/.bashrc" >/dev/null 2>&1\n'
            'printf "__BTP_NVM_DIR__=%s\\n" "$NVM_DIR"\n'
            'printf "__BTP_NODE_BEGIN__\\n"\n'
            'which -a node 2>/dev/null\n'
            'printf "__BTP_NODE_END__\\n"\n'
        )
        # 外层单引号包裹保证 /etc/profile、.bashrc 内 $HOME/$NVM_DIR 不提前被 sh 展开
        cmd = 'timeout 20 bash -ic \'' + script + '\' </dev/null 2>/dev/null'
        out = ''
        try:
            r = public.ExecShell(cmd, timeout=25)
            if isinstance(r, (tuple, list)):
                out = (r[0] or '')
        except:
            out = ''
        if out:
            nvm_dir = ''
            nodes = []
            in_nodes = False
            for line in out.splitlines():
                line = line.strip()
                if line.startswith('__BTP_NVM_DIR__='):
                    nvm_dir = line.split('=', 1)[1].strip()
                elif line == '__BTP_NODE_BEGIN__':
                    in_nodes = True
                elif line == '__BTP_NODE_END__':
                    in_nodes = False
                elif in_nodes and line:
                    nodes.append(line)
            ret['nvm_dir'] = nvm_dir
            ret['nodes'] = nodes
            ret['ok'] = bool(nodes) or bool(nvm_dir)
        return ret

    def _collect_extra_nodes(self):
        '''
            @name 扫描系统与NVM安装的node版本（不含面板安装的）
            @return list [{version, source, node_path, npm_path, npx_path,
                          yarn_path, pnpm_path, pm2_path, lib_path}]
        '''
        candidates = []
        # PATH 中全部 node(面板进程自身环境)
        try:
            which_nodes = public.ExecShell('which -a node 2>/dev/null')[0].strip()
            candidates.extend([p.strip() for p in which_nodes.split('\n') if p.strip()])
        except:
            pass

        # 加载 /etc/profile 与 /root/.bashrc 后可见的 node(面板进程环境不含这些)
        profile_env = self._probe_profile_env_nodes()
        candidates.extend(profile_env.get('nodes') or [])
        profile_nvm_dir = profile_env.get('nvm_dir') or ''

        # nvm 常见目录 + profile 暴露的自定义 NVM_DIR
        nvm_dirs = [os.path.expanduser('~/.nvm'),
                    '/usr/local/nvm',
                    '/root/.nvm']
        if profile_nvm_dir:
            profile_nvm_dir = profile_nvm_dir.strip()
            bad_chars = {"\n", "\r", ";", "|", "&", "`", "$"}
            if any(c in profile_nvm_dir for c in bad_chars):
                profile_nvm_dir = ""
            else:
                profile_nvm_dir = os.path.normpath(profile_nvm_dir)

        if profile_nvm_dir and profile_nvm_dir not in nvm_dirs:
            nvm_dirs.append(profile_nvm_dir)
        for nvm_root in nvm_dirs:
            nvm_dir = os.path.join(nvm_root, "versions", "node")
            if not os.path.isdir(nvm_dir):
                continue
            for version_name in os.listdir(nvm_dir):
                node_path = os.path.join(nvm_dir, version_name, 'bin', 'node')
                if os.path.exists(node_path):
                    candidates.append(node_path)
        candidates.extend(['/usr/local/bin/node', '/usr/bin/node', '/usr/bin/nodejs'])

        # 去重 + 过滤面板目录 + 解析版本
        nodes = {}
        for cand in candidates:
            if not cand or not os.path.exists(cand):
                continue
            real_path = os.path.realpath(cand)
            # 过滤已通过面板管理的版本
            if real_path.startswith(self.nodejs_path):
                continue
            if real_path in nodes:
                continue
            version = self._get_extra_node_version(real_path)
            if not version:
                continue
            # 来源分类：路径含nvm视为NVM安装，否则视为系统安装
            source = 'nvm' if real_path.find('nvm') != -1 else 'system'
            # owner：nvm 来源推断所属用户（第一版仅 root，为多用户 NVM 预留）
            owner = self._infer_node_owner(real_path)
            nodes[real_path] = {
                'version': version,
                'source': source,
                'owner': owner,
                'node_path': real_path,
                'npm_path': '',
                'npx_path': '',
                'yarn_path': '',
                'pnpm_path': '',
                'pm2_path': '',
                'lib_path': '',
            }

        # 补充 npm/npx/yarn/pnpm/pm2 与全局模块目录
        for item in nodes.values():
            node_bin_dir = os.path.dirname(item['node_path'])
            for cmd in ('npm', 'npx', 'yarn', 'pnpm', 'pm2'):
                cmd_path = os.path.join(node_bin_dir, cmd)
                if os.path.exists(cmd_path):
                    item['{}_path'.format(cmd)] = os.path.realpath(cmd_path)
                    continue
                try:
                    which_res = public.ExecShell('which {} 2>/dev/null'.format(cmd))[0].strip()
                    if which_res and os.path.exists(which_res):
                        item['{}_path'.format(cmd)] = os.path.realpath(which_res)
                except:
                    pass
            item['lib_path'] = self._get_extra_node_lib(item)
        return list(nodes.values())

    def _infer_node_owner(self, node_path):
        '''
            @name 从真实路径推断 node 所属用户
            /home/{user}/... -> {user}（nvm 或用户自装 node 均适用）
            其余（/usr/bin、/usr/local、/root/.nvm 等）视为系统级 root
        '''
        m = re.search(r'/home/([^/]+)/', str(node_path or ''))
        if m:
            return m.group(1)
        return 'root'

    def _get_extra_node_version(self, node_path):
        '''
            @name 解析node真实路径的版本号
        '''
        try:
            result = public.ExecShell('"{}" -v 2>/dev/null'.format(node_path))[0]
            result = result.strip().replace('v', '')
            if re.match(r'^\d+\.\d+\.\d+', result):
                return 'v{}'.format(result)
        except:
            pass
        return ''

    def _get_extra_node_lib(self, item):
        '''
            @name 获取真实全局 node_modules 目录
        '''
        npm_path = item.get('npm_path') or item.get('node_path')
        if npm_path:
            try:
                npm_bin_dir = os.path.dirname(npm_path)
                cmd = 'PATH="{}:$PATH" "{}" root -g --userconfig=/dev/null 2>/dev/null'.format(
                    npm_bin_dir, npm_path)
                lib = public.ExecShell(cmd)[0].strip()
                if lib and os.path.isdir(lib):
                    return os.path.realpath(lib)
            except:
                pass
        # 同目录下的 lib/node_modules 或 node_modules
        base_dir = os.path.dirname(item['node_path'])
        for lib in ('{}/lib/node_modules'.format(base_dir),
                    '{}/node_modules'.format(base_dir)):
            if os.path.isdir(lib):
                return os.path.realpath(lib)
        return ''

    def _ensure_extra_node_link(self, item):
        '''
            @name 幂等创建系统/NVM版本的软链目录
            @param item dict _collect_extra_nodes
            @return dict {version, source, created, skip_reason?}
        '''
        version = item['version']
        source = item['source']
        owner = item.get('owner', 'root')
        # 目录名统一带 owner：{version}-{source}-{owner}  避免同版本多来源/多属主撞名
        node_dir = '{}/{}-{}-{}'.format(self.nodejs_path, version, source, owner)
        if os.path.exists(node_dir):
            return {'version': version, 'source': source, 'created': False,
                    'skip_reason': 'exists',
                    'node_path': item.get('node_path', '')}
        bin_dir = os.path.join(node_dir, 'bin')
        try:
            os.makedirs(bin_dir, 493)
            for cmd in ('node', 'npm', 'npx', 'yarn', 'pnpm', 'pm2'):
                cmd_path = item.get('{}_path'.format(cmd))
                if not cmd_path or not os.path.exists(cmd_path):
                    continue
                os.symlink(cmd_path, os.path.join(bin_dir, cmd))
            # lib/node_modules 软链指向真实全局模块目录
            if item.get('lib_path'):
                lib_dir = os.path.join(node_dir, 'lib')
                os.makedirs(lib_dir, 493)
                os.symlink(item['lib_path'], os.path.join(lib_dir, 'node_modules'))
            # 标记文件
            flag = {
                'source': source,
                'owner': item.get('owner', 'root'),
                'node_version': version,
                'real_path': item.get('node_path', ''),
                'npm_path': item.get('npm_path', ''),
                'lib_path': item.get('lib_path', ''),
                'scan_time': time.strftime('%Y-%m-%d %H:%M:%S'),
            }
            public.writeFile(os.path.join(node_dir, self._EXTRA_NODE_FLAG),
                             json.dumps(flag))
        except Exception as ex:
            return {'version': version, 'source': source, 'created': False,
                    'error': str(ex),
                    'node_path': item.get('node_path', '')}
        return {'version': version, 'source': source, 'created': True,
                'node_path': item.get('node_path', '')}

    def _system_node_notes(self):
        '''
            @name 扫描未发现系统node时的诊断说明
        '''
        notes = []
        nodejs_path = self.nodejs_path
        # 1) 常见系统 node 路径是否被面板软链接管
        covered = []
        for p in ('/usr/bin/node', '/usr/bin/nodejs', '/usr/local/bin/node'):
            try:
                if os.path.islink(p):
                    real = os.path.realpath(p)
                    if real.startswith(nodejs_path):
                        covered.append('{} -> {}'.format(p, real))
            except:
                pass
        # 2) 包管理器是否装了系统 nodejs（dpkg 优先，rpm 兜底）
        pkg_ver = ''
        try:
            pkg_line = public.ExecShell('dpkg -l nodejs 2>/dev/null | grep "^ii "')[0].strip()
            if pkg_line:
                parts = pkg_line.split()
                if len(parts) >= 3:
                    pkg_ver = parts[2]
        except:
            pass
        if not pkg_ver:
            try:
                rpm_line = public.ExecShell('rpm -q nodejs --qf "%{VERSION}" 2>/dev/null')[0].strip()
                if rpm_line:
                    pkg_ver = rpm_line
            except:
                pass
        if covered:
            if pkg_ver:
                head = 'System Node not detected: nodejs {} package is installed in system'.format(pkg_ver)
            else:
                head = 'System Node not detected'
            notes.append('{}, but its executable path is managed by aaPanel default version symlink ({}), '
                         'the real system binary has been replaced and removed, so it will not be included. '
                         'To restore system Node, unset the default version in panel and reinstall nodejs via system package manager.'.format(
                head, ';'.join(covered)))
        elif pkg_ver:
            notes.append('System Node not detected: nodejs {} package is installed in system, '
                         'but no valid executable found under common paths (/usr/bin/node, /usr/bin/nodejs, /usr/local/bin/node).'.format(
                pkg_ver))

        return notes

    def _write_scan_info(self, source, scan_ret):
        '''
            @name 统一记录最近一次扫描元数据到 {nodejs_path}/.scan_info.json
            @param source string 触发来源：manual | after_install
            @param scan_ret dict _scan_system_nodes_internal 返回值 {created, skipped}
        '''
        try:
            info = {
                'last_scan_time': int(time.time()),
                'last_scan_source': source,
                'last_scan': {
                    'created': scan_ret.get('created', 0),
                    'skipped': scan_ret.get('skipped', 0),
                },
            }
            public.writeFile('{}/.scan_info.json'.format(self.nodejs_path), json.dumps(info))
        except:
            pass

    def _scan_system_nodes_internal(self, source='manual'):
        '''
            @name 扫描系统与NVM node并挂载到面板版本目录（幂等）
            @param source string 触发来源：manual | after_install
            @return dict {data, created, skipped}
        '''
        collected = self._collect_extra_nodes()
        result = []
        created = 0
        skipped = 0
        for item in collected:
            res = self._ensure_extra_node_link(item)
            if res.get('created'):
                created += 1
            else:
                skipped += 1
            result.append(res)
        ret = {
            'data': result,
            'created': created,
            'skipped': skipped,
        }
        self._write_scan_info(source, ret)
        return ret

    def scan_system_nodes(self, get):
        '''
            @name 扫描系统与NVM安装的node版本并入面板管理
            @param get<dict_obj>
            @return dict {data, created, skipped, notice?}
        '''
        ret = self._scan_system_nodes_internal()
        # 未扫到系统来源版本时，附加诊断说明（如被面板默认版本软链覆盖）
        # if not any(i.get('source') == 'system' for i in ret['data']):
        #     notes = self._system_node_notes()
        #     if notes:
        #         ret['notice'] = notes

        return public.return_message(0, 0, public.lang("Scan completed"))

    # =========================================================
    # System NVM 环境管理
    # 第一版只管理 root 用户的 NVM（/root/.nvm）
    # 下载源等配置持久化到 {nodejs_path}/.nvm_env.json
    # 下载日志 {nodejs_path}/.nvm_install_status.json
    # =========================================================
    _NVM_ENV_FILE = '.nvm_env.json'
    _NVM_SOURCE_URLS = {
        'npmmirror': 'https://npmmirror.com/mirrors/node',
        'official': 'https://nodejs.org/dist', # todo 换源
    }

    def _nvm_env_config(self):
        '''
            @name 读取 NVM 环境配置（下载源等）
            @return dict {nvm_dir, source, custom_url}
        '''
        cfg = {'nvm_dir': '/root/.nvm', 'source': 'npmmirror', 'custom_url': ''}
        try:
            cfg_file = '{}/{}'.format(self.nodejs_path, self._NVM_ENV_FILE)
            if os.path.exists(cfg_file):
                data = json.loads(public.readFile(cfg_file))
                if isinstance(data, dict):
                    cfg.update(data)
        except:
            pass
        return cfg

    def _nvm_save_config(self, cfg):
        cfg_file = '{}/{}'.format(self.nodejs_path, self._NVM_ENV_FILE)
        public.writeFile(cfg_file, json.dumps(cfg))
        return True

    def _nvm_root_dir(self):
        '''
            @name 检测 root 用户 NVM 目录（存在 nvm.sh 才认定有效）
            @return string 目录路径，未检测到返回 ''
        '''
        for cand in ('/root/.nvm', '/usr/local/nvm', os.path.expanduser('~/.nvm')):
            if os.path.isfile('{}/nvm.sh'.format(cand)):
                return cand
        return ''

    def _nvm_installed_versions(self, nvm_dir):
        '''
            @name 列出 NVM 已安装版本目录名
            @return list[str] ['v22.14.0', ...]
        '''
        versions = []
        node_versions_dir = '{}/versions/node'.format(nvm_dir)
        if os.path.isdir(node_versions_dir):
            for v in os.listdir(node_versions_dir):
                if v.startswith('v') and os.path.exists('{}/{}/bin/node'.format(node_versions_dir, v)):
                    versions.append(v)
        return sorted(versions, key=lambda v: tuple(map(int, re.findall(r'\d+', v))))

    def _nvm_installed_with_binding(self, nvm_dir):
        '''
            @name 列出 NVM 已安装版本，并附带面板侧绑定的版本目录名
            @param nvm_dir string NVM 根目录
            @return list[dict] [{value: 'v25.9.0', source: 'v25.9.0-nvm-root'}, ...]
            value   NVM 原版本号（versions/node 目录名）
            source  系统扫描挂载到面板的版本目录名（{version}-nvm-{owner}），未挂载为空字符串
        '''
        installed = self._nvm_installed_versions(nvm_dir)
        # 一次性扫描面板 nodejs 目录，建立 nvm 来源：版本号 -> 目录名 映射
        binding = {}
        if os.path.isdir(self.nodejs_path):
            for d in os.listdir(self.nodejs_path):
                if d[0] != 'v' or d.find('.') == -1:
                    continue
                flag_file = os.path.join(self.nodejs_path, d, self._EXTRA_NODE_FLAG)
                if not os.path.isfile(flag_file):
                    continue
                try:
                    flag = json.loads(public.readFile(flag_file))
                    if isinstance(flag, dict) and flag.get('source') == 'nvm':
                        ver = flag.get('node_version') or d.split('-')[0]
                        binding.setdefault(ver, d)
                except:
                    pass
        return [{'value': v, 'source': binding.get(v, '')} for v in installed]

    def _nvm_current_version(self, nvm_dir):
        '''
            @name 读取 NVM 当前默认版本（nvm alias default 落盘在 alias/default）
            @return string 版本号，未设置返回 ''
        '''
        alias_file = '{}/alias/default'.format(nvm_dir)
        if os.path.exists(alias_file):
            ver = public.readFile(alias_file).strip()
            if ver:
                return ver
        return ''

    def _nvm_source_url(self, source, custom_url=''):
        if source == 'custom' and custom_url:
            return custom_url
        return self._NVM_SOURCE_URLS.get(source, self._NVM_SOURCE_URLS['npmmirror'])

    def _nvm_platform_filename(self):
        '''
            @name 获取当前系统适用的 Node 平台标识
            @return string 如 'linux-x64'
        '''
        try:
            import platform
            sysname = (os.uname().sysname if hasattr(os, 'uname') else platform.system()).lower()
            machine = os.uname().machine if hasattr(os, 'uname') else platform.machine()
            if machine == 'x86_64':
                return '{}-x64'.format(sysname)
            if machine == 'i686':
                return '{}-x86'.format(sysname)
            if machine == 'aarch64':
                return '{}-arm64'.format(sysname)
            if machine == 'armv7l':
                return '{}-armv7l'.format(sysname)
            if machine == 'armv6l':
                return '{}-armv6l'.format(sysname)
            if machine == 'armv5l':
                return '{}-armv5l'.format(sysname)
            return sysname
        except:
            return 'linux-x64'

    def get_nvm_online_versions(self, get):
        '''
            @name 获取 NVM 可安装版本列表（来自已配置下载源的 index.json）
            每个大版本只保留最新一个稳定版本
            @param get<dict_obj> {force?: '1'}
            @return list [{version, status, lts, npm}]
        '''

        # 固定版本提示 其他版本默认"status": "Eol"
        status_list = [
            {
                "version": "v26.8.1",
                "status": "Current"
            },
            {
                "version": "v24.20.0",
                "status": "LTS"
            },
            {
                "version": "v22.23.2",
                "status": "LTS"
            },
        ]


        cfg = self._nvm_env_config()
        source = cfg.get('source', 'npmmirror')
        source_url = self._nvm_source_url(source, cfg.get('custom_url', ''))
        index_url = source_url.rstrip('/') + '/index.json'
        namex = self._nvm_platform_filename()
        data = None
        try:
            if get.get('force') != '1':
                # 5 分钟缓存
                cache_file = '{}/.nvm_versions_cache.json'.format(self.nodejs_path)
                if os.path.exists(cache_file) and os.stat(cache_file).st_mtime + 300 > time.time():
                    try:
                        data = json.loads(public.readFile(cache_file))
                    except:
                        data = None
            if not data:
                http_json = public.httpGet(index_url, timeout=10)
                if http_json:
                    try:
                        data = json.loads(http_json)
                        public.writeFile('{}/.nvm_versions_cache.json'.format(self.nodejs_path), http_json)
                    except:
                        data = None
        except:
            data = None
        if not isinstance(data, list) or data is None:
            return public.return_message(-1, 0, public.lang(
                'Failed to fetch the NVM installable version list from the download source ({}). '
                'Please check the download source or network.'.format(index_url)))
        # 每个大版本只留最新一个稳定版本：大版本号 → 版本项
        latest_by_major = {}
        for v in data:
            if not isinstance(v, dict) or not v.get('version'):
                continue
            version = v['version']
            # 跳过 prerelease（带 - 后缀，如 v22.0.0-rc.1）
            # if '-' in version:
            #     continue

            # 过滤不支持当前平台的版本（files 为裸平台标识，如 linux-x64）
            if 'files' in v and isinstance(v['files'], list):
                if namex not in v['files']:
                    continue
            nums = tuple(map(int, re.findall(r'\d+', version)))
            if len(nums) < 2:
                continue
            major = nums[0]
            cur = latest_by_major.get(major)
            if cur is None or nums > cur['nums']:
                status = 'Eol'
                for item in status_list:
                    if item['version'] == version:
                        status = item['status']
                        break
                latest_by_major[major] = {
                    'nums': nums,
                    'version': version,
                    'status': status,
                    'lts': v.get('lts') or '',
                    'npm': v.get('npm', ''),
                }
        result = [latest_by_major[m] for m in sorted(latest_by_major.keys(), reverse=True)]
        for item in result:
            item.pop('nums', None)
        return public.return_message(0, 0, result)


    def get_nvm_env_info(self, get):
        '''
            @name 获取 System NVM 环境信息（路径/当前版本/已装版本/下载源）
            @param get<dict_obj>
            @return dict {nvm_dir, current_version, installed, source, source_url,
                          last_scan_time, last_scan_time_ts, last_scan_source, last_scan_result}
            nvm_dir 为空时表示未检测到 root 用户 NVM；
            installed 为对象列表 [{value, source}]：value 为 NVM 原版本号，source 为系统扫描挂载到面板的
            版本目录名（{version}-nvm-{owner}，未挂载时为空字符串），前端可用 source 传 get_package_manager_info；
            last_scan_time 为最近一次扫描（手动 scan_system_nodes 或安装后自动扫描）时间，无记录为空
        '''
        cfg = self._nvm_env_config()
        nvm_dir = self._nvm_root_dir()
        data = {
            'nvm_dir': nvm_dir,
            'current_version': '',
            'installed': [],
            'source': cfg.get('source', 'npmmirror'),
            'custom_url': cfg.get('custom_url', ''),
            'source_url': self._nvm_source_url(cfg.get('source', 'npmmirror'), cfg.get('custom_url', '')),
            'last_scan_time': '',
            'last_scan_time_ts': 0,
        }
        if nvm_dir:
            data['current_version'] = self._nvm_current_version(nvm_dir)
            data['installed'] = self._nvm_installed_with_binding(nvm_dir)
        # 最近一次扫描元数据
        try:
            f = '{}/.scan_info.json'.format(self.nodejs_path)
            if os.path.exists(f):
                info = json.loads(public.readFile(f))
                if isinstance(info, dict):
                    ts = int(info.get('last_scan_time') or 0)
                    data['last_scan_time_ts'] = ts
                    if ts:
                        data['last_scan_time'] = time.strftime(
                            '%Y-%m-%d %H:%M:%S', time.localtime(ts))
        except:
            pass
        return public.return_message(0, 0, data)

    def _nvm_set_default_alias(self, nvm_dir, version):
        '''
            @name 写 NVM alias/default（即 nvm alias default） 只影响新会话
            @param nvm_dir string NVM 根目录
            @param version string 如 v22.18.0
        '''
        alias_file = '{}/alias/default'.format(nvm_dir)
        if not os.path.isdir(os.path.dirname(alias_file)):
            os.makedirs(os.path.dirname(alias_file), 493)
        public.writeFile(alias_file, version)
        return True

    def switch_nvm_default_version(self, get):
        '''
            @name 切换 NVM 环境默认版本（nvm alias default） /root/.nvm/alias/default
            只写 NVM 的 alias/default 文件，影响新会话；不碰 /usr/bin/node、不重启项目
            @param get<dict_obj> {version: 'v22.14.0'}
        '''
        version = get.get('version', '')
        if not version:
            return public.return_message(-1, 0, public.lang('The "version" parameter cannot be left blank.'))
        nvm_dir = self._nvm_root_dir()
        if not nvm_dir:
            return public.return_message(-1, 0, public.lang(
                'No root NVM environment detected, unable to switch the environment version.'))
        installed = self._nvm_installed_versions(nvm_dir)
        if version not in installed:
            return public.return_message(-1, 0, public.lang(
                'The version "{}" is not installed in NVM ({}). Installed: {}'.format(
                    version, nvm_dir, ', '.join(installed) or 'none')))
        self._nvm_set_default_alias(nvm_dir, version)
        return public.return_message(0, 0, public.lang(
            'The NVM environment version has been switched to: {}'.format(version)))

    def set_nvm_config(self, get):
        '''
            @name 设置 NVM 下载源（npmmirror/official/custom）和 NVM 环境默认版本
            @param get<dict_obj> {source: 'npmmirror', custom_url: 'https://...', version?: 'v22.18.0'}
            @return dict {source, source_url, version?, switched?}
        '''
        source = get.get('source', '')
        if source not in ('npmmirror', 'official', 'custom'):
            return public.return_message(-1, 0, public.lang(
                'The "source" parameter is invalid. Support: npmmirror, official, custom.'))
        # 可选 同时切换 NVM 环境默认版本
        version = get.get('version', '').strip()

        nvm_dir = ''
        if version:
            nvm_dir = self._nvm_root_dir()
            if not nvm_dir:
                return public.return_message(-1, 0, public.lang(
                    'No root NVM environment detected, unable to switch the environment version.'))
            installed = self._nvm_installed_versions(nvm_dir)
            if version not in installed:
                return public.return_message(-1, 0, public.lang(
                    'The version "{}" is not installed in NVM ({}). Installed: {}'.format(
                        version, nvm_dir, ', '.join(installed) or 'none')))
        cfg = self._nvm_env_config()
        cfg['source'] = source
        if source == 'custom':
            custom_url = get.get('custom_url', '').strip()
            if not custom_url.startswith('http'):
                return public.return_message(-1, 0, public.lang(
                    'Custom source must start with http(s).'))
            cfg['custom_url'] = custom_url
        else:
            cfg['custom_url'] = ''
        if version:
            self._nvm_set_default_alias(nvm_dir, version)

        self._nvm_save_config(cfg)
        return public.return_message(0, 0, public.lang('Saved successfully'))


    # ---- NVM 异步安装（后台线程执行，装完自动扫描挂载）----
    def _write_nvm_install_status(self, status):
        try:
            public.writeFile('{}/.nvm_install_status.json'.format(self.nodejs_path),
                             json.dumps(status, ensure_ascii=False))
        except:
            pass

    def _do_nvm_install(self, nvm_dir, version, mirror, switch_nvm=False):
        '''
            @name 执行 nvm install 成功后自动扫描挂载到面板
            @param nvm_dir string NVM 根目录
            @param version string 如 v22.18.0
            @param mirror string 下载源 URL
            @param switch_nvm bool 安装成功后是否同时切换 NVM 环境默认版本
        '''
        # 并发锁：同一时间只允许一个 nvm 安装任务
        # 锁内记录本线程 ID 线程结束自动失效
        if not public.progress_acquire_lock('/tmp/nvm_install.lock'):
            self._write_nvm_install_status({
                'status': 'failed', 'version': version,
                'message': 'Another NVM installation task is running. Please wait!',
                'started_at': int(time.time()), 'finished_at': int(time.time())})
            return
        status = {'status': 'running', 'version': version, 'message': 'installing...',
                  'started_at': int(time.time())}
        self._write_nvm_install_status(status)
        from subprocess import Popen, PIPE, STDOUT
        import threading

        log_lines = []

        def _append_log(line):
            log_lines.append(line)
            # message 记录安装日志，保留最近 300 行避免状态文件膨胀
            status['message'] = '\n'.join(log_lines[-300:])
            self._write_nvm_install_status(status)

        try:
            cmd = '''export NVM_DIR="{}"
[ -s "$NVM_DIR/nvm.sh" ] && . "$NVM_DIR/nvm.sh"
export NVM_NODEJS_ORG_MIRROR="{}"
nvm install {}
'''.format(nvm_dir, mirror, version)
            p = Popen(cmd, shell=True, stdout=PIPE, stderr=STDOUT,
                      universal_newlines=True, encoding='utf-8', errors='replace')

            def _reader():
                for line in iter(p.stdout.readline, ''):
                    if line:
                        _append_log(line.rstrip())
            reader = threading.Thread(target=_reader, daemon=True)
            reader.start()
            try:
                p.wait(timeout=900)
            except Exception:
                try:
                    p.kill()
                except:
                    pass
            reader.join(timeout=3)
            stdout = '\n'.join(log_lines)
            installed = os.path.exists('{}/versions/node/{}/bin/node'.format(nvm_dir, version))
            if installed or 'is already installed' in stdout:
                status['status'] = 'success'
                status['message'] = (stdout + '\n' if stdout else '') + \
                    'NVM install success: {}'.format(version)
                # 安装成功（含已安装）→ 自动触发扫描挂载 + 可选切换环境默认版本
                try:
                    self._scan_system_nodes_internal('after_install')
                except Exception as ex:
                    # 仅扫描失败记录
                    status['scan'] = {'error': str(ex)}
                if switch_nvm:
                    self._nvm_set_default_alias(nvm_dir, version)
                    status['switched'] = True
                    status['message'] += '\nNVM environment version switched to: {}'.format(version)
            else:
                status['status'] = 'failed'
                status['message'] = (stdout + '\n' if stdout else '') + \
                    'NVM install failed (check the log above)'
        except Exception as ex:
            status['status'] = 'failed'
            status['message'] = (status.get('message') or '') + '\n{}'.format(ex)
        status['finished_at'] = int(time.time())
        self._write_nvm_install_status(status)

    def install_nvm_node(self, get):
        '''
            @name 异步通过 root NVM 安装新版本 node
            只调用目标 NVM 环境执行 nvm install 不修改面板版本目录
            @param get<dict_obj> {version: 'v22.18.0', switch_nvm?: '1'} switch_nvm=1 安装成功同时切换 NVM 环境默认版本
            @return dict {status, version, message}
        '''
        version = get.get('version', '').strip()
        if not version:
            return public.return_message(-1, 0, public.lang('The "version" parameter cannot be left blank.'))
        if not re.match(r'^v\d+\.\d+\.\d+$', version):
            return public.return_message(-1, 0, public.lang(
                'The version format is incorrect, e.g. v22.18.0: {}'.format(version)))
        # 自动切换 NVM 环境默认版本
        switch_nvm = get.get('switch_nvm', '') == '1'
        # 已有安装任务在进行时拒绝重复提交
        try:
            f = '{}/.nvm_install_status.json'.format(self.nodejs_path)
            if os.path.exists(f):
                prev = json.loads(public.readFile(f))
                if isinstance(prev, dict) and prev.get('status') == 'running':
                    return public.return_message(-1, 0, public.lang(
                        'Another NVM installation task is running. Please wait!'))
        except:
            pass
        nvm_dir = self._nvm_root_dir()
        if not nvm_dir:
            return public.return_message(-1, 0, public.lang(
                'No root NVM environment detected, cannot install. NVM is not managed by the panel.'))
        # 下载源
        source = get.get('source', '')
        if not source:
            cfg = self._nvm_env_config()
            source = cfg.get('source', 'npmmirror')
            custom_url = cfg.get('custom_url', '')
        else:
            custom_url = get.get('custom_url', '')
        mirror = self._nvm_source_url(source, custom_url)
        # 后台线程执行
        from concurrent.futures import ThreadPoolExecutor
        thread = ThreadPoolExecutor(max_workers=1)
        thread.submit(self._do_nvm_install, nvm_dir, version, mirror, switch_nvm)
        return public.return_message(0, 0, {
            'status': 'running',
            'version': version,
            'switch_nvm': switch_nvm,
            'message': 'NVM installation started in the background.',
        })

    def get_nvm_install_status(self, get):
        '''
            @name 查询 NVM 异步安装任务状态
            @param get<dict_obj>
            @return dict {status: idle|running|success|failed, version, message, scan?, started_at, finished_at}
            message 记录安装过程日志（nvm install 实时输出，保留最近 300 行）；
            status 判断结果，scan 仅 success 时存在，switched 仅 switch_nvm=1 成功时存在
        '''
        status = {'status': 'idle', 'version': '', 'message': ''}
        try:
            f = '{}/.nvm_install_status.json'.format(self.nodejs_path)
            if os.path.exists(f):
                data = json.loads(public.readFile(f))
                if isinstance(data, dict):
                    status = data
        except:
            pass
        return public.return_message(0, 0, status)


    def get_node_runtime_list(self, get):
        '''
            @name 汇总已管理版本（面板安装 + 系统/NVM）
            @param get<dict_obj>
            @return dict {data: [{version, source, owner, path, node_path}]}
        '''
        version_list = []
        if os.path.exists(self.nodejs_path):
            for v in os.listdir(self.nodejs_path):
                if v[0] != 'v' or v.find('.') == -1:
                    continue
                node_bin = '{}/{}/bin/node'.format(self.nodejs_path, v)
                if not os.path.exists(node_bin):
                    continue
                flag_file = os.path.join(self.nodejs_path, v, self._EXTRA_NODE_FLAG)
                source = 'panel'
                owner = ''
                node_path = node_bin
                if os.path.exists(flag_file):
                    try:
                        flag = json.loads(public.readFile(flag_file))
                        source = flag.get('source', 'system')
                        owner = flag.get('owner', 'root')
                        node_path = flag.get('real_path') or node_bin
                    except:
                        source = 'system'
                version_list.append({
                    'version': v,
                    'source': source,
                    'owner': owner,
                    'path': '{}/{}/bin/node'.format(self.nodejs_path, v),
                    'node_path': node_path,
                })

        # 排序
        # 1. 面板在前,后缀版本在后
        # 2. 同分组内部 版本号从高到低降序
        def _version_sort_key(item):
            # panel组返回0,其他返回1, 0排在前面
            group = 0 if item["source"] == "panel" else 1
            # 提取版本数字 v22.14.0‑rc1 → [22,14,0]
            ver_nums = re.findall(r'\d+', item['version'])
            ver_tuple = tuple(map(int, ver_nums)) if ver_nums else (0, 0, 0)
            # 返回元组，sort升序, -ver_tuple实现版本降序
            return (group, tuple(-x for x in ver_tuple))

        version_list.sort(key=_version_sort_key)

        # 默认版本标记:以 which node 当前实际命中的版本为准
        # 取不到（无 node / 命中的不是本目录管理的版本）时，把版本号最高的版本标记为默认
        default_version = self._get_current_default_node_version()
        for item in version_list:
            item['is_default'] = 0
        if not default_version or not any(item['version'] == default_version for item in version_list):
            if version_list:
                newest_item = max(
                    version_list,
                    key=lambda it: tuple(int(x) for x in re.findall(r'\d+', it['version'])))
                default_version = newest_item['version']
        for item in version_list:
            if item['version'] == default_version:
                item['is_default'] = 1

        return public.return_message(0, 0, version_list)

    def _get_current_default_node_version(self):
        '''
            @name 判定命令行当前默认 node（which node）对应的受管版本目录
            按以下优先级判定：
            1) /etc/profile 中 BT-NODE-ENV 前缀（面板/插件"设为默认"写入处，登录 shell 的
               which node 据此命中）的最后一行版本，最后一行 = 最新一次设置；
            2) 否则按面板环境 command -v node 命中路径 realpath 归一匹配受管版本；
            3) 否则按 /usr/bin/node 软链 realpath 归一匹配受管版本；
            全部未命中返回 ''（调用方兜底标最高版本）
            @return string 默认版本目录名，未命中返回 ''
        '''
        # 1) /etc/profile BT-NODE-ENV 前缀
        default_version = ''
        try:
            profile_body = public.readFile('/etc/profile')
            if profile_body:
                for line in profile_body.splitlines():
                    m = re.search(r'nodejs/(v[0-9][A-Za-z0-9_.\-]*)/bin', line)
                    if m:
                        default_version = m.group(1)
        except:
            default_version = ''
        if default_version and os.path.exists(
                '{}/{}/bin/node'.format(self.nodejs_path, default_version)):
            return default_version
        # 2) / 3) realpath 归一匹配
        target = ''
        try:
            target = public.ExecShell('command -v node 2>/dev/null')[0].strip() or ''
        except:
            target = ''
        if not target or not os.path.exists(target):
            target = '/usr/bin/node'
        return self._match_node_version_by_realpath(target)

    def _match_node_version_by_realpath(self, target):
        '''
            @name 把命令路径 realpath 归一到受管 node 版本目录名
            target 可为面板安装版本 bin/node、/usr/bin 软链或 NVM 真实 node 路径，
            三者 realpath 归一后与该版本 bin/node 的 realpath 相等即命中
            @param target string node 可执行文件路径
            @return string 版本目录名，未命中返回 ''
        '''
        try:
            real = os.path.realpath(target)
        except:
            real = ''
        if not real:
            return ''
        try:
            for v in os.listdir(self.nodejs_path):
                if v[0] != 'v' or v.find('.') == -1:
                    continue
                try:
                    if os.path.realpath('{}/{}/bin/node'.format(self.nodejs_path, v)) == real:
                        return v
                except:
                    continue
        except:
            pass
        return ''

    def set_default_node_version(self, get):
        '''
            @name 切换命令行默认 node（which node）到指定版本
            重建 /usr/bin 下 node/npm/npx 软链指向该版本，并把 /etc/profile 的
            BT-NODE-ENV PATH 前缀改到该版本 bin，使新登录 shell 的 which node 命中该版本
            @param get<dict_obj> {version: 'v24.15.0' | 'v22.14.0-nvm-root'}
            @return dict
        '''
        version = str(get.get('version', '') or '').strip()
        if not version:
            return public.return_message(-1, 0, public.lang('The "version" parameter cannot be left blank.'))
        node_dir = '{}/{}'.format(self.nodejs_path, version)
        src_node_bin = '{}/bin/node'.format(node_dir)
        if not os.path.exists(src_node_bin):
            return public.return_message(-1, 0, public.lang(
                'This version does not exist: {}'.format(version)))
        # 重建 /usr/bin 下 node/npm/npx 软链。
        # 软链目标保留 {nodejs_path}/{version}/bin/<cmd>（挂载版本 bin 下本身是软链，链到链即可），
        # 保持路径落在 nodejs_path 内，兼容插件 get_default_env 的"/usr/bin/node 指向面板目录"判定；
        # realpath 穿透两层软链仍能解析到真实 node，不影响 _match_node_version_by_realpath 命中
        for name in ('node', 'npm', 'npx'):
            src_bin = '{}/bin/{}'.format(node_dir, name)
            if not os.path.exists(src_bin):
                continue
            env_bin = '/usr/bin/{}'.format(name)
            try:
                if os.path.islink(env_bin) or os.path.exists(env_bin):
                    os.remove(env_bin)
                os.symlink(src_bin, env_bin)
            except Exception as ex:
                return public.return_message(-1, 0, 'Failed to set /usr/bin/{}: {}'.format(name, ex))
        # 更新 /etc/profile 的 BT-NODE-ENV 前缀，保证登录 shell 的 which node 命中该版本 bin
        profile = '/etc/profile'
        try:
            if os.path.exists(profile):
                public.ExecShell("sed -i '/BT-NODE-ENV/d' {}".format(profile))
                body = public.readFile(profile)
                if body is not False:
                    body = body.strip()
                    body += "\nPATH={}/bin:$PATH # BT-NODE-ENV\n".format(node_dir)
                    body += "export PATH # BT-NODE-ENV\n".format(node_dir)
                    public.writeFile(profile, body)
        except Exception as ex:
            return public.return_message(-1, 0, 'Failed to update {}: {}'.format(profile, ex))
        public.WriteLog(self.log_name, 'Switch default node version to {}'.format(version))
        return public.return_message(0, 0, public.lang(
            'The default Node.js version has been switched to: {}'.format(version)))

    def remove_extra_node(self, get):
        '''
            @name 卸载系统/NVM版本（仅删软链目录，不影响真实node）
            @param get<dict_obj> {version: 'v24.19.0-system'}
            @return dict
        '''
        version = get.get('version', '')
        if not version:
            return public.return_message(-1, 0, public.lang('The "version" parameter cannot be left blank.'))
        node_dir = '{}/{}'.format(self.nodejs_path, version)
        flag_file = os.path.join(node_dir, self._EXTRA_NODE_FLAG)
        if not os.path.exists(flag_file):
            return public.return_message(-1, 0, public.lang(
                'Only the system/NVM managed version can be uninstalled here: {}'.format(version)))
        if not os.path.exists(node_dir):
            return public.return_message(-1, 0, public.lang('This version does not exist.'))
        public.ExecShell('rm -rf "{}"'.format(node_dir))
        return public.return_message(0, 0, public.lang(
            'The system/NVM Node.js version link has been removed: {}'.format(version)))


    # 2024/7/10 下午5:02 将node版本转成元祖
    def version_key(self, version):
        return tuple(map(int, re.findall(r'\d+', version)))

    # 2024/7/10 下午5:12 获取指定的nodejs版本允许使用的包管理器
    def package_managers(self, nodejs_versions) -> list:
        package_managers = []
        top_version = int(nodejs_versions[0].split('.')[0].split('v')[-1])
        if top_version >= 14:
            package_managers.append("pnpm")
        if top_version >= 8:
            package_managers.append("yarn")
        package_managers.append("npm")

        return package_managers

    # 2024/7/10 下午9:10 获取可以使用的用户列表
    def get_system_user_list(self, get):
        '''
            @name 获取可以使用的用户列表
        '''
        from projectModel.base import projectBase
        return projectBase().get_system_user_list(get)

    # 2024/7/12 上午9:12
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
                if int(project_config['port']) == port:
                    return True
            except:
                continue
        if sock: return False
        return public.check_tcp('127.0.0.1', port)

    # 2024/7/12 上午9:06 创建网站
    def create_site(self, get):
        '''
            @name
        '''
        try:
            get.project_args = get.get("project_args", "")
            get.project_script = get.get("project_script", "")
            get.pkg_manager = get.get("pkg_manager", "")
            get.env = get.get("env", "")
            get.project_file = get.get("project_file", "")
            get.config_file = get.get("config_file", "")
            get.config_body = get.get("config_body", "")
            get.project_type = get.get("project_type", "")
            get.pm2_name = get.get("pm2_name", "")
            get.watch = get.get("watch", False)
            get.cluster = get.get("cluster/d", 1)
            get.add_type = get.get("add_type", None)
            get.bind_extranet = 1 if len(get.domains) > 0 else 0
            pdata = {
                'name': get.project_name,
                'path': get.project_cwd,
                'ps': get.project_ps,
                'status': 1,
                'type_id': 0,
                'project_type': 'Node',
                'project_config': json.dumps({
                    'project_name': get.project_name,
                    'pm2_name': get.pm2_name,
                    'add_type': get.add_type,
                    'watch': get.watch,
                    'cluster': get.cluster,
                    'project_cwd': get.project_cwd,
                    'project_file': get.project_file,
                    'project_script': get.project_script,
                    'project_args': get.project_args,
                    'project_type': get.project_type,
                    'config_file': get.config_file,
                    'config_body': get.config_body,
                    'env': get.env,
                    'bind_extranet': get.bind_extranet,
                    'domains': [],
                    'is_power_on': get.is_power_on,
                    'run_user': get.run_user,
                    'max_memory_limit': get.max_memory_limit,
                    'nodejs_version': get.nodejs_version,
                    'port': int(get.port) if get.port != "" else None,
                    'log_path': self.node_logs_path,
                    'pkg_manager': get.pkg_manager}),
                'addtime': public.getDate()
            }

            project_id = public.M('sites').insert(pdata)
            if get.bind_extranet == 1:
                format_domains = []
                for domain in get.domains:
                    if domain.find(':') == -1: domain += ':80'
                    format_domains.append(domain)
                get.domains = format_domains
                self.project_add_domain(get)
            if project_id:
                public.WriteLog(self.log_name,
                                'Add{}【{}】'.format(self.project_structure[get.project_type], get.project_name))
                return project_id
        except:
            pass

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
        project_find = self.get_project_find(get.project_name)
        if not project_find:
            return public.return_message(-1 , 0, 'The specified project does not exist.')
        project_id = project_find['id']

        domains = get.domains
        flag = False
        res_domains = []
        for domain in domains:
            domain = domain.strip()
            if not domain: continue
            domain_arr = domain.rsplit(':', 1)
            domain_arr[0] = self.check_domain(domain_arr[0])
            if domain_arr[0] is False:
                res_domains.append({"name": domain, "status": False, "msg": 'Incorrect domain name format'})
                continue
            if len(domain_arr) == 1:
                domain_arr.append("")
            if domain_arr[1] == "":
                domain_arr[1] = 80
                domain += ':80'
            try:
                if not (0 < int(domain_arr[1]) < 65535):
                    res_domains.append({"name": domain, "status": False, "msg": 'Incorrect domain name format'})
                    continue
            except ValueError:
                res_domains.append({"name": domain, "status": False, "msg": 'Incorrect domain name format'})
                continue
            if int(domain_arr[1]) == 443:
                res_domains.append({"name": domain, "status": False, "msg": 'Port 443 is not allowed for Node.js projects'})
                continue
            if not public.M('domain').where('name=? and port=?', (domain_arr[0], domain_arr[1])).count():
                public.M('domain').add('name,pid,port,addtime',
                                       (domain_arr[0], project_id, domain_arr[1], public.getDate()))
                if not domain in project_find['project_config']['domains']:
                    project_find['project_config']['domains'].append(domain)
                public.WriteLog(self.log_name, 'Successfully added domain {} to project {}'.format(domain, get.project_name))
                res_domains.append({"name": domain_arr[0], "status": True, "msg": 'Added successfully'})
                flag = True
            else:
                public.WriteLog(self.log_name, 'Error in adding domain name. The domain name {} already exists.'.format(domain))
                res_domains.append(
                    {"name": domain_arr[0], "status": False, "msg": 'Error added: The domain name {} already exists.'.format(domain)})
        if flag:
            public.M('sites').where('id=?', (project_id,)).save('project_config',
                                                                json.dumps(project_find['project_config']))
            self.set_config(get.project_name)

        return self._ckeck_add_domain(get.project_name, res_domains)

    def _ckeck_add_domain(self, site_name, domains):
        from panelSite import panelSite
        ssl_data = panelSite().GetSSL(type("get", tuple(), {"siteName": site_name})())
        if not ssl_data["status"] or not ssl_data.get("cert_data", {}).get("dns", None):
            return {"domains": domains}
        domain_rep = []
        for i in ssl_data["cert_data"]["dns"]:
            if i.startswith("*"):
                _rep = "^[^\.]+\." + i[2:].replace(".", "\.")
            else:
                _rep = "^" + i.replace(".", "\.")
            domain_rep.append(_rep)
        no_ssl = []
        for domain in domains:
            if not domain["status"]: continue
            for _rep in domain_rep:
                if re.search(_rep, domain["name"]):
                    break
            else:
                no_ssl.append(domain["name"])
        if no_ssl:
            return {"domains": domains, "not_ssl": no_ssl,
                    "tip": "This site has enabled SSL certificate. However, the domain name {} added this time cannot be matched with the current certificate. If you need it, please apply for a new certificate.".format(
                        str(no_ssl))}
        return {"domains": domains}

    def get_project_find(self, project_name):
        '''
            @name 获取指定项目配置
            @author hwliang<2021-08-09>
            @param project_name<string> 项目名称
            @return dict
        '''
        project_info = public.M('sites').where('project_type=? AND name=?', ('Node', project_name)).find()
        if isinstance(project_info, str):
            raise public.PanelError('Database query error:' + project_info)
        if not project_info: return False
        project_info['project_config'] = json.loads(project_info['project_config'])
        return project_info

    # 2024/7/12 上午9:59
    def _update_project(self, project_name, project_info):
        # 检查是否需要更新
        # 移动日志文件
        # 保存
        target_file = self.node_logs_path + "/" + project_name + ".log"
        if "log_path" in project_info['project_config']:
            return
        log_file = "{}/{}.log".format(self.node_logs, project_name)

        if os.path.exists(log_file):
            self._move_logs(log_file, target_file)
            if not os.path.exists(target_file):
                return
            else:
                os.remove(log_file)

        project_info['project_config']["log_path"] = self.node_logs_path
        pdata = {
            'name': project_name,
            'project_config': json.dumps(project_info['project_config'])
        }
        public.M('sites').where('name=?', (project_name,)).update(pdata)

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
            pid_file = "{}/{}.pid".format(self.node_pid_path, project_name)
            public.writeFile(pid_file, str(all_pids[0]))
            return all_pids
        return False

    def get_project_pids(self, get=None, pid=None):
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
            other_pids += self.get_project_pids(pid=i)
        if os.path.exists('/proc/{}'.format(pid)):
            project_pids.append(pid)

        all_pids = list(set(project_pids + other_pids))
        if not all_pids:
            all_pids = self.get_other_pids(pid)
        return sorted(all_pids)

    def get_other_pids(self, pid):
        '''
            @name 获取其他进程pid列表
            @author hwliang<2021-08-10>
            @param pid: string<项目pid>
            @return list
        '''
        project_name = None
        for pid_name in os.listdir(self.node_pid_path):
            pid_file = '{}/{}'.format(self.node_pid_path, pid_name)
            # s_pid = int(public.readFile(pid_file))
            data = public.readFile(pid_file)
            if isinstance(data, str):
                try:
                    s_pid = int(data)
                except:
                    return []
            else:
                return []
            if pid == s_pid:
                project_name = pid_name[:-4]
                break
        project_find = self.get_project_find(project_name)
        if not project_find: return []
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
        return all_pids

    def _move_logs(self, s_file, target_file):
        if os.path.getsize(s_file) > 3145928:
            res = public.GetNumLines(s_file, 3000)
            public.WriteFile(target_file, res)
        else:
            shutil.copyfile(s_file, target_file)

    def check_domain(self, domain: str) -> Union[str, bool]:
        domain = self.domain_to_puny_code(domain)
        # 判断通配符域名格式
        if domain.find('*') != -1 and domain.find('*.') == -1:
            return False

        # 判断域名格式
        reg = "^([\w\-\*]{1,100}\.){1,24}([\w\-]{1,24}|[\w\-]{1,24}\.[\w\-]{1,24})$"
        if not re.match(reg, domain):
            return False
        return domain

    @staticmethod
    def domain_to_puny_code(domain):
        match = re.search(u"[^u\0000-u\001f]+", domain)
        if not match:
            return domain
        try:
            if domain.startswith("*."):
                return "*." + idna.encode(domain[2:]).decode("utf8")
            else:
                return idna.encode(domain).decode("utf8")
        except:
            return domain

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
        public.serviceReload()
        return True

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

    def is_nginx_http3(self):
        """判断nginx是否可以使用http3"""
        if getattr(self, "_is_nginx_http3", None) is None:
            _is_nginx_http3 = public.is_nginx_http3()
            setattr(self, "_is_nginx_http3", _is_nginx_http3)
        return self._is_nginx_http3
    def ng_ssl_early_data_enabled(self):
        """判断nginx是否可以使用http3"""
        if getattr(self, "_ng_ssl_early_data_enabled", None) is None:
            _ng_ssl_early_data_enabled = public.ng_ssl_early_data_enabled()
            setattr(self, "_ng_ssl_early_data_enabled", _ng_ssl_early_data_enabled)
        return self._ng_ssl_early_data_enabled

    @staticmethod
    def _replace_nginx_conf(config_file, mut_config: dict) -> bool:
        """尝试替换"""
        data: str = public.readFile(config_file)
        tab_spc = "    "
        rep_list = [( r"([ \f\r\t\v]*listen[^;\n]*;\n(\s*http2\s+on\s*;[^\n]*\n)?)+", mut_config["listen_ports"] + "\n"),
                    (r"[ \f\r\t\v]*root [ \f\r\t\v]*/[^;\n]*;", "    root {};".format(mut_config["site_path"])),
                    (r"[ \f\r\t\v]*server_name [ \f\r\t\v]*[^\n;]*;",
                     "   server_name {};".format(mut_config["domains"])), (
                        r"[ \f\r\t\v]*location */ *\{ *\n *proxy_pass[^\n;]*;\n *proxy_set_header *Host",
                        "{}location / {{\n{}proxy_pass {};\n{}proxy_set_header Host".format(tab_spc, tab_spc * 2,
                                                                                            mut_config["url"],
                                                                                            tab_spc * 2, )),
                    ("[ \f\r\t\v]*#SSL-START(.*\n){2,15}[ \f\r\t\v]*#SSL-END",
                     "{}#SSL-START SSL-related configuration\n{}#error_page 404/404.html;\n{}{}\n{}#SSL-END".format(
                         tab_spc, tab_spc, tab_spc, mut_config["ssl_config"],
                         tab_spc))]
        for rep, info in rep_list:
            if re.search(rep, data):
                data = re.sub(rep, info, data, 1)
            else:
                return False

        public.writeFile(config_file, data)
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
        is_ssl, is_force_ssl = self.exists_nginx_ssl(project_name)
        listen_ports_list = []
        for p in ports:
            listen_ports_list.append("    listen {};".format(p))
            if listen_ipv6:
                listen_ports_list.append("    listen [::]:{};".format(p))

        ssl_config = ''
        if is_ssl:
            http3_header = ""
            if self.is_nginx_http3():
                http3_header = '''\n    add_header Alt-Svc 'quic=":443"; h3=":443"; h3-29=":443"; h3-27=":443";h3-25=":443"; h3-T050=":443"; h3-Q050=":443";h3-Q049=":443";h3-Q048=":443"; h3-Q046=":443"; h3-Q043=":443"';'''
                http3_header += "\n    quic_retry on;\n    quic_gso on;"
                if self.ng_ssl_early_data_enabled():
                    http3_header += "\n    ssl_early_data on;"

            nginx_ver = public.nginx_version()
            if nginx_ver:
                port_str = ["443"]
                if listen_ipv6:
                    port_str.append("[::]:443")
                use_http2_on = False
                for p in port_str:
                    listen_str = "    listen {} ssl".format(p)
                    if nginx_ver < [1, 9, 5]:
                        listen_str += ";"
                    elif [1, 9, 5] <= nginx_ver < [1, 25, 1]:
                        listen_str += " http2;"
                    else:  # >= [1, 25, 1]
                        listen_str += ";"
                        use_http2_on = True
                    listen_ports_list.append(listen_str)

                    if self.is_nginx_http3():
                        listen_ports_list.append("    listen {} quic;".format(p))
                if use_http2_on:
                    listen_ports_list.append("    http2 on;")
                if self.is_nginx_http3():
                    listen_ports_list.append("    http3 on;")

            else:
                listen_ports_list.append("    listen 443 ssl;")

            ssl_config = '''ssl_certificate    {vhost_path}/cert/{priject_name}/fullchain.pem;
    ssl_certificate_key    {vhost_path}/cert/{priject_name}/privkey.pem;
    ssl_protocols TLSv1.1 TLSv1.2 TLSv1.3;
    ssl_ciphers EECDH+CHACHA20:EECDH+CHACHA20-draft:EECDH+AES128:RSA+AES128:EECDH+AES256:RSA+AES256:EECDH+3DES:RSA+3DES:!MD5;
    ssl_prefer_server_ciphers on;
    ssl_session_cache shared:SSL:10m;
    ssl_session_timeout 10m;
    add_header Strict-Transport-Security "max-age=31536000";{http3_header}
    error_page 497  https://$host$request_uri;'''.format(vhost_path=self.vhost_path, priject_name=project_name,
                                                         http3_header=http3_header)

            if is_force_ssl:
                ssl_config += '''
    #HTTP_TO_HTTPS_START
    if ($server_port !~ 443){
        rewrite ^(/.*)$ https://$host$1 permanent;
    }
    #HTTP_TO_HTTPS_END'''

        config_file = "{}/nginx/node_{}.conf".format(self.vhost_path, project_name)
        template_file = "{}/template/nginx/node_http.conf".format(self.vhost_path)
        listen_ports = "\n".join(listen_ports_list).strip()

        config_body = public.readFile(template_file)
        mut_config = {"site_path": project_find['path'], "domains": ' '.join(domains),
                      "url": 'http://127.0.0.1:{}'.format(project_find['project_config']['port']),
                      "ssl_config": ssl_config,
                      "listen_ports": listen_ports}
        config_body = config_body.format(site_path=mut_config["site_path"], domains=mut_config["domains"],
                                         project_name=project_name, panel_path=self.panel_path,
                                         log_path=public.get_logs_path(),
                                         url=mut_config["url"], host='$host', listen_ports=listen_ports,
                                         ssl_config=ssl_config)

        # # 恢复旧的SSL配置
        # ssl_config = self.get_nginx_ssl_config(project_name)
        # if ssl_config:
        #     config_body.replace('#error_page 404/404.html;',ssl_config)

        rewrite_file = "{panel_path}/vhost/rewrite/node_{project_name}.conf".format(panel_path=self.panel_path,
                                                                                    project_name=project_name)
        if not os.path.exists(rewrite_file):
            public.writeFile(rewrite_file, '# Please fill in the pseudo-static rules or custom NGINX configuration here.\n')
        if not os.path.exists("/www/server/panel/vhost/nginx/well-known"):
            os.makedirs("/www/server/panel/vhost/nginx/well-known", 0o600)
        apply_check = "{}/vhost/nginx/well-known/{}.conf".format(self.panel_path, project_name)
        if not os.path.exists(apply_check):
            public.writeFile(apply_check, '')
        from mod.base.web_conf import ng_ext
        config_body = ng_ext.set_extension_by_config(project_name, config_body)
        if not os.path.exists(config_file):
            public.writeFile(config_file, config_body)
        else:
            if not self._replace_nginx_conf(config_file, mut_config):
                public.writeFile(config_file, config_body)
        return True

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

        config_file = "{}/apache/node_{}.conf".format(self.vhost_path, project_name)
        template_file = "{}/template/apache/node_http.conf".format(self.vhost_path)
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

            # 生成vhost主体配置
            apache_config_body += config_body.format(site_path=project_find['path'],
                                                     server_name='{}.{}'.format(p, project_name),
                                                     domains=' '.join(domains), log_path=public.get_logs_path(),
                                                     server_admin='admin@{}'.format(project_name),
                                                     url='http://127.0.0.1:{}'.format(
                                                         project_find['project_config']['port']), port=p,
                                                     ssl_config=ssl_config,
                                                     project_name=project_name)
            apache_config_body += "\n"

            # 添加端口到主配置文件
            if not p in [80]:
                s.apacheAddPort(p)

        # 写.htaccess
        rewrite_file = "{}/.htaccess".format(project_find['path'])
        if not os.path.exists(rewrite_file): public.writeFile(rewrite_file,
                                                              '# Please fill in the pseudo-static rules or custom Apache configuration here\n')

        # 写配置文件
        public.writeFile(config_file, apache_config_body)
        return True

    def get_node_bin(self, nodejs_version):
        '''
            @name 获取指定node版本的node路径
            @author hwliang<2021-08-10>
            @param nodejs_version<string> nodejs版本
            @return string
        '''
        node_path = '{}/{}/bin/node'.format(self.nodejs_path, nodejs_version)
        if not os.path.exists(node_path): return False
        return node_path

    def get_npm_bin(self, nodejs_version):
        '''
            @name 获取指定node版本的npm路径
            @author hwliang<2021-08-10>
            @param nodejs_version<string> nodejs版本
            @return string
        '''
        npm_path = '{}/{}/bin/npm'.format(self.nodejs_path, nodejs_version)
        if not os.path.exists(npm_path): return False
        return npm_path

    def get_last_env(self, nodejs_version, project_cwd=None):
        '''
            @name 获取前置环境变量
            @author hwliang<2021-08-25>
            @param nodejs_version<string> Node版本
            @return string
        '''
        nodejs_bin_path = '{}/{}/bin'.format(self.nodejs_path, nodejs_version)
        if project_cwd:
            _bin = '{}/node_modules/.bin'.format(project_cwd)
            if os.path.exists(_bin):
                nodejs_bin_path = _bin + ':' + nodejs_bin_path

        last_env = '''PATH={nodejs_bin_path}:/bin:/sbin:/usr/bin:/usr/sbin:/usr/local/bin:/usr/local/sbin:~/bin
export PATH
'''.format(nodejs_bin_path=nodejs_bin_path)
        return last_env

    @staticmethod
    def start_by_user(project_id):
        file_path = "{}/data/push/tips/project_stop.json".format(public.get_panel_path())
        if not os.path.exists(file_path):
            data = {}
        else:
            data_content = public.readFile(file_path)
            try:
                data = json.loads(data_content)
            except json.JSONDecodeError:
                data = {}
        data[str(project_id)] = False
        public.writeFile(file_path, json.dumps(data))

    def kill_pids(self, get=None, pids=None):
        '''
            @name 结束进程列表
            @author hwliang<2021-08-10>
            @param pids: string<进程pid列表>
            @return dict
        '''
        if get: pids = get.pids
        if not pids: return public.return_data(True, 'No process')
        pids = sorted(pids, reverse=True)
        for i in pids:
            try:
                p = psutil.Process(i)
                p.terminate()
            except:
                pass
        return public.return_data(True, 'All processes have been completed.')

    @staticmethod
    def stop_by_user(project_id):
        file_path = "{}/data/push/tips/project_stop.json".format(public.get_panel_path())
        if not os.path.exists(file_path):
            data = {}
        else:
            data_content = public.readFile(file_path)
            try:
                data = json.loads(data_content)
            except json.JSONDecodeError:
                data = {}
        data[str(project_id)] = True
        public.writeFile(file_path, json.dumps(data))

    # 2024/7/12 下午12:40 websocket错误退出函数
    def ws_err_exit(self, status: bool = True,
                    msg: str = "",
                    data: any = None,
                    timestamp: int = None,
                    code: int = 0,
                    args: any = None):
        '''
            @name websocket错误退出函数
        '''
        self.get._ws.send(json.dumps(self.wsResult(status, msg, data, timestamp, code, args)))
        self.get._ws.close()

    # 2024/7/12 下午5:45 删除node项目
    def remove_project(self, get):
        '''
            @name 删除node项目
        '''
        get.pm2_name = get.get("pm2_name", "")
        if get.pm2_name != "":
            from mod.project.nodejs.pm2Mod import main
            main().delete(mode="cluster_mode", name=get.pm2_name)

        from projectModel.nodejsModel import main
        remove_result = main().remove_project(get)
        from mod.base.web_conf.redirect import Redirect
        Redirect().remove_redirect_by_project_name(get.project_name)
        if not remove_result["status"]:
            return public.return_message(-1,0, public.lang(remove_result["error_msg"]))
        return public.return_message(0,0, public.lang('Operation successful.'))

    # 2024/7/13 上午10:22 检测环境变量是否有误，并返回构造好的环境变量
    def get_run_env(self, get):
        '''
            @name 检测环境变量是否有误，并返回构造好的环境变量
        '''
        get.env = "\n".join(map(lambda x: "{}".format(x), get.env))

    # 2024/7/12 上午10:40 检测node版本是否符合要求
    def check_node_version(self, get):
        '''
            @name 判断是否存在"engines"，并且判断 get.nodejs_version 是否在大于等于"engines"中的node版本
        '''
        if "engines" in get.package_info:
            if "node" in get.package_info["engines"]:
                # 2024/7/12 上午10:24 获取engines的数学符号
                get_nodejs_version = self.version_key(get.nodejs_version)
                if ">=" in get.package_info["engines"]["node"]:
                    engines_node_version = get.package_info["engines"]["node"].replace(">=", "v").strip()
                    engines_node_version = self.version_key(engines_node_version)
                    if get_nodejs_version < engines_node_version:
                        self.ws_err_exit(False, 'The current project [{}] requires the use of node version [{}] or above.'.format(
                            get.project_name,
                            "v" + ".".join(map(str, engines_node_version))), code=2)
                elif ">" in get.package_info["engines"]["node"]:
                    engines_node_version = get.package_info["engines"]["node"].replace(">", "v").strip()
                    engines_node_version = self.version_key(engines_node_version)
                    if get_nodejs_version <= engines_node_version:
                        self.ws_err_exit(False, 'The current project [{}] requires the use of node version [{}] or above.'.format(
                            get.project_name,
                            "v" + ".".join(map(str, engines_node_version))), code=2)
                elif "<=" in get.package_info["engines"]["node"]:
                    engines_node_version = get.package_info["engines"]["node"].replace("<=", "v").strip()
                    engines_node_version = self.version_key(engines_node_version)
                    if get_nodejs_version > engines_node_version:
                        self.ws_err_exit(False, 'The current project [{}] requires the use of node version [{}].'.format(
                            get.project_name,
                            "v" + ".".join(map(str, engines_node_version))), code=2)
                elif "<" in get.package_info["engines"]["node"]:
                    engines_node_version = get.package_info["engines"]["node"].replace("<", "v").strip()
                    engines_node_version = self.version_key(engines_node_version)
                    if get_nodejs_version >= engines_node_version:
                        self.ws_err_exit(False, 'The current project [{}] requires the use of node version [{}].'.format(
                            get.project_name,
                            "v" + ".".join(map(str, engines_node_version))), code=2)
                elif "==" in get.package_info["engines"]["node"]:
                    engines_node_version = get.package_info["engines"]["node"].replace("==", "v").strip()
                    engines_node_version = self.version_key(engines_node_version)
                    if get_nodejs_version != engines_node_version:
                        self.ws_err_exit(False, 'The current project ["{}"] requires the use of the node version of ["{}"]'.format(
                            get.project_name,
                            "v" + ".".join(map(str, engines_node_version))), code=2)

    def replace_or_add_field(self, config_body, regex, field):
        if regex.search(config_body):
            return regex.sub("       " + field, config_body)
        else:
            match = re.search(r'(apps\s*:\s*\[.*?\{)', config_body, re.DOTALL)
            if match:
                insert_position = match.end()
                return config_body[:insert_position] + "\n            " + field + config_body[insert_position:]
            # match = re.search(r'(apps:\s*\[.*\{)', config_body, re.DOTALL)
            # if match:
            #     insert_position = match.end()
            #     return config_body[:insert_position] + "\n            " + field + config_body[insert_position:]
        return config_body

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
        pid_file = "{}/{}.pid".format(self.node_pid_path, project_name)
        if not os.path.exists(pid_file): return False
        data = public.readFile(pid_file)
        if isinstance(data, str) and data:
            pid = int(data)
            pids = self.get_project_pids(pid=pid)
        else:
            return self.get_project_state_by_cwd(project_name)
        if not pids: return self.get_project_state_by_cwd(project_name)
        return True

    def get_process_cpu_time(self, cpu_times):
        cpu_time = 0.00
        for s in cpu_times: cpu_time += s
        return cpu_time

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
            status_ps = {'sleeping': 'Sleep', 'running': 'Run'}
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
        pid_file = "{}/{}.pid".format(self.node_pid_path, project_name)
        if not os.path.exists(pid_file): return load_info
        data = public.readFile(pid_file)
        if isinstance(data, str) and data:
            pid = int(data)
            pids = self.get_project_pids(pid=pid)
        else:
            return load_info
        if not pids: return load_info
        for i in pids:
            process_info = self.get_process_info_by_pid(i)
            if process_info: load_info[i] = process_info
        return load_info

    def get_ssl_end_date(self, project_name):
        '''
            @name 获取SSL信息
            @author hwliang<2021-08-09>
            @param project_name <string> 项目名称
            @return dict
        '''
        from data import data
        return data().get_site_ssl_info('node_{}'.format(project_name))

    def get_project_stat(self, project_info):
        '''
            @name 获取项目状态信息
            @author hwliang<2021-08-09>
            @param project_info<dict> 项目信息
            @return list
        '''
        project_info['project_config'] = json.loads(project_info['project_config'])
        if ("pm2_name" in project_info['project_config'] and
            "project_type" in project_info['project_config'] and
            project_info['project_config']["project_type"] == "pm2") or "pm2" in project_info['project_config']['project_script']:
            from mod.project.nodejs.pm2Mod import main
            pm2_list = main().get_jlist()
            project_info['run'] = False
            for pm2_info in pm2_list:
                if pm2_info.get("name") in ("pm2-sysmonit", "pm2-logrotate"):
                    continue

                project_info['run'] = pm2_info.get("pm2_env").get("status") == "online"
                if project_info['run']:
                    project_info['load_info'] = pm2_info
                    break
        else:
            project_info['run'] = self.get_project_run_state(project_name=project_info['name'])
        project_info['load_info'] = {}
        if project_info['run']:
            project_info['load_info'] = self.get_project_load_info(project_name=project_info['name'])
        project_info['ssl'] = self.get_ssl_end_date(project_name=project_info['name'])
        project_info['listen'] = []
        project_info['listen_ok'] = True
        if project_info['load_info']:
            for pid in project_info['load_info'].keys():
                if not 'connections' in project_info['load_info'][pid]:
                    project_info['load_info'][pid]['connections'] = []
                for conn in project_info['load_info'][pid]['connections']:
                    if not conn['status'] == 'LISTEN': continue
                    if not conn['local_port'] in project_info['listen']:
                        project_info['listen'].append(conn['local_port'])
            if project_info['listen']:
                if project_info['project_config']['port'] is None:
                    project_info['project_config']['port'] = project_info['listen'][0]
                project_info['listen_ok'] = project_info['project_config']['port'] in project_info['listen']

        return project_info

    def is_install_nodejs(self, get):
        '''
            @name 是否安装nodejs版本管理器
            @author hwliang<2021-08-09>
            @param get<dict_obj> 请求数据
            @return bool
        '''
        return os.path.exists(self.nodejs_plugin_path)

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
            self.get_last_env(nodejs_version) + "cd {} && {} rebuild &>> {}".format(project_find['path'], npm_bin,
                                                                                    self.npm_exec_log))
        return True
