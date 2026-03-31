# coding: utf-8
# -------------------------------------------------------------------
# aapaenl
# -------------------------------------------------------------------
# Copyright (c) 2015-2099 aapanel(http://www.aapanel.com) All rights reserved.
# -------------------------------------------------------------------
# Author: wzz <wzz@aapanel.com>
# -------------------------------------------------------------------
import json
import os
# ------------------------------
# nodejs项目业务接口
# ------------------------------
import sys

if "/www/server/panel/class" not in sys.path:
    sys.path.insert(0, "/www/server/panel/class")

os.chdir("/www/server/panel")
import public
from mod.project.nodejs.base import NodeJs


class main(NodeJs):

    def __init__(self):
        super(main, self).__init__()

    # 2024/7/10 下午4:39 查看指定目录是否符合创建要求
    def check_path_status(self, get):
        '''
            @name 查看指定目录是否符合创建要求
        '''
        get.path = get.get("path", None)
        if get.path is None:
            return public.return_message(-1, 0, public.lang('The "path" parameter cannot be left blank.'))

        if not os.path.exists(get.path):
            return public.return_message(-1, 0, public.lang('The specified directory does not exist.'))

        package_json = True
        if not os.path.exists(os.path.join(get.path, 'package.json')):
            package_json = False

        node_modules = True
        if not os.path.exists(os.path.join(get.path, 'node_modules')):
            node_modules = False

        data = {
            "package_json": package_json,
            "node_modules": node_modules,
        }

        return public.return_message(0,0, data)

    # 2024/7/10 下午4:29 添加项目前置环境信息
    def pre_env(self, get):
        '''
            @name 添加项目前置环境信息
        '''
        nodejs_versions = self.get_nodejs_version(get)
        if not nodejs_versions:
            return public.return_message(-1, 0, public.lang( 'Node.js is not installed.'))

        nodejs_versions = sorted(nodejs_versions, key=self.version_key, reverse=True)

        # 2023/12/6 下午 4:13 获取系统内存，转成MB，为最大可用内存
        import psutil
        mem = psutil.virtual_memory()
        mem = int(mem.total / 1024 / 1024)

        data = {
            'nodejs_versions': nodejs_versions,
            'package_managers': self.package_managers(nodejs_versions),
            'user_list': sorted(self.get_system_user_list(get), reverse=True),
            'maximum_memory': mem,
        }

        return public.return_message(0,0, data)

    # 2024/7/10 下午5:14 获取指定的nodejs版本允许使用的包管理器
    def get_package_managers(self, get):
        '''
            @name 获取指定的nodejs版本允许使用的包管理器
        '''
        get.version = get.get("version", None)
        if get.version is None:
            return public.return_message(-1, 0, public.lang( 'The "version" parameter cannot be left blank.'))

        nodejs_versions = [get.version]
        package_managers = self.package_managers(nodejs_versions)
        return public.return_message(0,0, {"msg" : "success", "package_managers": package_managers})

    # 2024/7/11 下午4:26 创建项目
    def create(self, get):
        '''
            @name 创建项目
            @param get: dict_obj {}
                    nodejs项目：
                        get.project_cwd string 项目路径 /www/wwwroot/my_project 必传
                        get.project_name string 项目名称 my_project 必传
                        get.project_type string 项目类型 nodejs/pm2/general 必传
                        get.project_script string 启动脚本 start/dev/... 必传
                        get.run_user string 运行用户 www/root/... 必传
                        get.port string 端口 4001 非必传
                        get.env string 环境变量 key=value\nkey=value\n... 非必传
                        get.nodejs_version string node版本 v20.15.0 必传
                        get.pkg_manager string 包管理器 npm/yarn/pnpm/... 必传
                        get.not_install_pkg bool 是否安装依赖包 True/False 非必传
                        get.release_firewall bool 是否放行防火墙 True/False 非必传
                        get.is_power_on bool 是否开机启动 True/False 非必传
                        get.max_memory_limit int 最大内存限制 4096 非必传
                        get.bind_extranet bool 是否绑定外网 True/False 依赖于get.port 非必传
                        get.domains list 域名列表 ["www.bt.cn", "bt.cn", ...] 非必传
                        get.project_ps string 备注 ps 非必传
                    pm2项目：
                        get.project_type string 项目类型 nodejs/pm2/general 必传
                        get.project_name string 项目名称 my_project 必传
                        get.nodejs_version string node版本 v20.15.0 必传
                        get.project_file string 项目启动文件 /www/wwwroot/my_project/server.js 自定义添加时必传
                        get.project_cwd string 项目路径 /www/wwwroot/my_project 自定义添加时必传
                        get.cluster int 实例数量 1 必传，默认1
                        get.max_memory_limit int 最大内存限制 1024 必传，默认1024，mb
                        get.watch 自动重载 bool True/False 必传，默认False
                        get.pkg_manager string 包管理器 none/npm/yarn/pnpm/... 必传，默认none
                        get.not_install_pkg bool 是否安装依赖包 True/False 非必传
                        get.run_user string 运行用户 www/root/... 必传
                        get.config_file string 配置文件路径 /www/wwwroot/remix_app/ecosystem.config.cjs 配置文件方式添加时必传
                        get.config_body string 配置文件内容 非必传 可以单独传config_body，如果选了config_file，这里就是必传，也要传config_body
                        get.port string 端口 4001 非必传
                        get.release_firewall bool 是否放行防火墙 True/False 非必传
                        get.is_power_on bool 是否开机启动 True/False 非必传
                        get.bind_extranet bool 是否绑定外网 True/False 依赖于get.port 非必传
                        get.domains list 域名列表 ["www.bt.cn", "bt.cn", ...] 非必传
                        get.project_ps string 备注 ps 非必传
                    general项目：
                        get.project_type string 项目类型 nodejs/pm2/general 必传
                        get.project_name string 项目名称 my_project 必传
                        get.nodejs_version string node版本 v20.15.0 必传
                        get.project_file string 项目启动文件 /www/wwwroot/my_project/server.js 必传
                        get.project_cwd string 项目路径 /www/wwwroot/my_project 必传
                        get.project_args string 启动参数 --debug 非必传
                        get.env string 环境变量 key=value\nkey=value\n... 非必传
                        get.run_user string 运行用户 www/root/... 必传
                        get.port string 端口 4001 非必传
                        get.release_firewall bool 是否放行防火墙 True/False 非必传
                        get.is_power_on bool 是否开机启动 True/False 非必传
                        get.max_memory_limit int 最大内存限制 4096 非必传
                        get.bind_extranet bool 是否绑定外网 True/False 依赖于get.port 非必传
                        get.domains list 域名列表 ["www.bt.cn", "bt.cn", ...] 非必传
                        get.project_ps string 备注 ps 非必传
        '''
        public.set_module_logs('node_site_{}'.format(get.get("project_type", None)), 'create_app', 1)
        public.set_module_logs('node_site', 'create_app', 1)
        self.set_self_get(get)
        self.set_def_name(get.def_name)
        get.project_type = get.get("project_type", None)
        get.port = get.get('port', "")
        get.bind_extranet = get.get('bind_extranet', 0)
        if get.project_type is None:
            self.ws_err_exit(False, 'The "project_type" parameter cannot be left blank.', code=2)
        if not get.project_type in ("nodejs", "pm2", "general"):
            self.ws_err_exit(False, 'Project type: {} is not valid. Currently, it is supported by nodejs, pm2, and general.'.format(get.project_type), code=2)
        if get.port != "":
            if self.check_port_is_used(get.get('port/port')):
                self.ws_err_exit(False,
                                 'The specified port is already occupied by other applications. Please modify your project configuration to use another port, port: {}'.format(get.port),
                                 code=2)

        if public.M('sites').where('name=?',(get.project_name.strip(),)).count():
            self.ws_err_exit(False, 'The specified project name already exists: {}'.format(get.project_name), code=2)

        get.domains = get.get("domains", [])
        if type(get.domains) == str:
            get.domains = get.domains.split('\n')
        domains = get.domains
        if len(domains) > 0:
            public.check_domain_cloud(domains[0])
            if get.port == "":
                self.ws_err_exit(False, 'Binding to the external network requires specifying a port', code=2)
            get.bind_extranet = 1
            if not public.is_apache_nginx():
                self.ws_err_exit(False, 'Nginx or Apache needs to be installed to use the external network mapping function', code=3)

            from mod.base.web_conf import normalize_domain
            domains, err = normalize_domain(*domains)
            if err:
                self.ws_err_exit(False, "Domain input error", code=5)
            for domain, port in domains:
                if public.M('domain').where('name=? AND port=?', (domain, port)).count():
                    self.ws_err_exit(False, 'The specified domain already exists: {}'.format(domain), code=4)
            get.domains = ["{}:{}".format(d,p) for d, p in domains]

        get.nodejs_version = get.get("nodejs_version", None)
        if get.nodejs_version is None:
            self.ws_err_exit(False, 'The "nodejs_version" parameter cannot be left blank.', code=2)
        self.set_nodejs_version(get.nodejs_version).set_nodejs_bin()
        if not os.path.exists(self.nodejs_bin):
            self.ws_err_exit(False, 'Node.js version not installed: {}, please install it before adding the project'.format(get.nodejs_version), code=2)

        if get.project_type in ("nodejs", "pm2"):
            get.pkg_manager = get.get("pkg_manager", "npm")
            self.set_manager(get.pkg_manager)
            self.set_pack_cmd(get.nodejs_version)
            if self.pack_cmd is None or not os.path.exists(self.pack_cmd):
                get._ws.send(json.dumps(self.wsResult(True, "[node {}] does not have [{}] installed, switched to npm for creation".format(
                    get.nodejs_version, get.pkg_manager), code=5)))
                get.pkg_manager = "npm"

        get.release_firewall = get.get("release_firewall", False)
        get.project_ps = get.get("project_ps", "")

        # 设置默认nodejs命令行版本
        try:
            from plugin.nodejs.nodejs_main import nodejs_main
            nodejs_list = nodejs_main().get_online_version_list()
            default_version = next((item['version'] for item in nodejs_list if item.get('is_default') == 1), None)
            if default_version is None and nodejs_list:
                nodejs_main().set_default_env(public.to_dict_obj({"version":nodejs_list[0]['version']}))
        except:
            pass

        self.set_project_model(get.project_type)
        self.projectModel.create_project(get)
        if get.release_firewall:
            from firewallModel.comModel import main as comModel
            firewall_com = comModel()
            if get.port != "":
                firewall_com.set_port_rule(get)

    # 2024/7/12 下午5:49 删除项目
    def delete(self, get):
        '''
            @name Delete project
        '''
        get.project_type = get.get("project_type", None)
        if get.project_type is None:
            return public.return_message(-1, 0, public.lang( 'The "project_type" parameter cannot be left blank.'))
        if not get.project_type in ("nodejs", "pm2", "general"):
            return public.return_message(-1, 0, public.lang(
                                       'Project type: {} is not valid. Currently, it is supported by nodejs, pm2, and general.', get.project_type))
        get.project_name = get.get("project_name", None)
        if get.project_name is None:
            return public.return_message(-1, 0, public.lang( 'The "project_name" parameter cannot be left blank.'))

        self.set_project_model(get.project_type)
        return self.projectModel.remove_project(get)

    # 2024/7/11 下午8:07 获取pm2的监控数据
    def get_pm2_monit(self, get):
        '''
            @name 获取pm2的监控数据
        '''
        from mod.project.nodejs import pm2Mod
        return pm2Mod.main().get_pm2_monit(get)

    # 2024/7/11 下午5:43 获取指定pm2项目的日志
    def get_pm2_logs(self, get):
        '''
            @name 获取指定pm2项目的日志
            @param get: dict_obj {}
                    get.mode string fork_mode/cluster_mode 必传
                    get.id string pm2项目id 必传 mode=fork_mode
                    get.name string pm2项目名称 必传 mode=cluster_mode
                    get.log_type string 日志类型 all/out/err 非必传
        '''
        get.mode = get.get("mode", None)
        if get.mode is None:
            return public.return_message(-1, 0, public.lang( 'The "mode" parameter cannot be left blank'))
        if not get.mode in ("fork_mode", "cluster_mode"):
            return public.return_message(-1, 0, public.lang( 'Invalid "mode" parameter, only fork_mode/cluster_mode are supported'))

        get.id = get.get("id", None)
        get.name = get.get("name", None)
        if get.mode == "fork_mode" and id is None:
            return public.return_message(-1, 0, public.lang( 'The "id" parameter cannot be left blank'))
        if get.mode == "cluster_mode" and get.name is None:
            return public.return_message(-1, 0, public.lang( 'The "name" parameter cannot be left blank'))

        get.log_type = get.get("log_type", "all")
        if not get.log_type in ("all", "out", "err"):
            return public.return_message(-1, 0, public.lang( 'Invalid "log_type" parameter'))
        self.set_project_model("pm2")
        return self.projectModel.get_logs(get.mode, get.id, get.name, get.log_type)

    # 2024/7/11 下午8:06 设置指定pm2项目的状态
    def set_pm2_status(self, get):
        '''
            @name 设置指定pm2项目的状态
            @param get: dict_obj {}
                    get.mode string fork_mode/cluster_mode 必传
                    get.id string pm2项目id 必传 mode=fork_mode
                    get.name string pm2项目名称 必传 mode=cluster_mode
                    get.action string restart/stop/start 必传
        '''
        get.mode = get.get("mode", None)
        if get.mode is None:
            return public.return_message(-1, 0, public.lang( 'The "mode" parameter cannot be left blank'))
        if not get.mode in ("fork_mode", "cluster_mode"):
            return public.return_message(-1, 0, public.lang( 'Invalid "mode" parameter, only fork_mode/cluster_mode are supported'))

        get.id = get.get("id", None)
        get.name = get.get("name", None)
        if get.mode == "fork_mode" and id is None:
            return public.return_message(-1, 0, public.lang( 'The "id" parameter cannot be left blank'))
        if get.mode == "cluster_mode" and get.name is None:
            return public.return_message(-1, 0, public.lang( 'The "name" parameter cannot be left blank'))

        get.status = get.get("status", None)
        if get.status is None:
            return public.return_message(-1, 0, public.lang( 'The "action" parameter cannot be left blank'))
        if not get.status in ("restart", "stop", "start"):
            return public.return_message(-1, 0, public.lang( 'Invalid "action" parameter, only restart/stop/start are supported'))

        self.set_project_model("pm2")
        return getattr(self.projectModel, get.status)(get.mode, get.id, get.name, get.get("project_name/s", ""), get.get("run_user", "root"))

    # 2024/7/11 下午8:07 删除指定pm2项目
    def del_pm2_project(self, get):
        '''
            @name 删除指定pm2项目
            @param get: dict_obj {}
                    get.mode string fork_mode/cluster_mode 必传
                    get.id string pm2项目id 必传 mode=fork_mode
                    get.name string pm2项目名称 必传 mode=cluster_mode
        '''
        get.mode = get.get("mode", None)
        if get.mode is None:
            return public.return_message(-1, 0, public.lang( 'The "mode" parameter cannot be left blank'))
        if not get.mode in ("fork_mode", "cluster_mode"):
            return public.return_message(-1, 0, public.lang( 'Invalid "mode" parameter, only fork_mode/cluster_mode are supported'))

        get.id = get.get("id", None)
        get.name = get.get("name", None)
        if get.mode == "fork_mode" and id is None:
            return public.return_message(-1, 0, public.lang( 'The "id" parameter cannot be left blank'))
        if get.mode == "cluster_mode" and get.name is None:
            return public.return_message(-1, 0, public.lang( 'The "name" parameter cannot be left blank'))

        self.set_project_model("pm2")
        return self.projectModel.del_project(get.mode, get.id, get.name)

    # 2024/7/15 下午8:56 设置指定服务的状态
    def set_project_status(self, get):
        '''
            @name Set the status of the specified service
        '''
        get.project_type = get.get("project_type", None)
        if get.project_type is None:
            return public.return_message(-1, 0, 'The "project_type" parameter cannot be left blank')
        if not get.project_type in ("nodejs", "pm2", "general"):
            return public.return_message(-1, 0,
                                       'Project type: {} is not valid. Currently, it is supported by nodejs, pm2, and general.'.format(get.project_type),)
        get.project_name = get.get("project_name", None)
        if get.project_name is None:
            return public.return_message(-1, 0, 'The "project_name" parameter cannot be left blank')

        if get.project_type == "pm2":
            get.pm2_name = get.get("pm2_name", "")
            if get.pm2_name == "":
                return public.return_message(-1, 0, 'The "pm2_name" parameter cannot be left blank')
            get.mode = "cluster_mode"
            get.name = get.pm2_name
            return self.set_pm2_status(get)
        else:
            get.status = get.get("status", None)
            if get.status is None:
                return public.return_message(-1, 0, 'The "action" parameter cannot be left blank')
            if not get.status in ("restart", "stop", "start"):
                return public.return_message(-1, 0, 'Invalid "action" parameter, only restart/stop/start are supported')

            self.set_project_model(get.project_type)
            return getattr(self.projectModel, "{}_project".format(get.status))(get)

    # 2024/7/17 上午9:24 停止指定项目
    def stop_project(self, get):
        '''
            @name Stop the specified project
        '''
        get.project_type = get.get("project_type", None)
        if get.project_type is None:
            return public.return_message(-1, 0, public.lang( 'The "project_type" parameter cannot be left blank'))
        if not get.project_type in ("nodejs", "pm2", "general"):
            return public.return_message(-1, 0, public.lang(
                                       'Project type: {} is not valid. Currently, it is supported by nodejs, pm2, and general.',get.project_type))
        get.project_name = get.get("project_name", None)
        if get.project_name is None:
            return public.return_message(-1, 0, public.lang( 'The "project_name" parameter cannot be left blank'))

        get.status = "stop"
        if get.project_type == "pm2":
            get.pm2_name = get.get("pm2_name", "")
            if get.pm2_name == "":
                return public.return_message(-1, 0, public.lang( 'The "pm2_name" parameter cannot be left blank'))
            get.mode = "cluster_mode"
            get.name = get.pm2_name
            return self.set_pm2_status(get)
        else:
            from projectModel.nodejsModel import main
            return getattr(main(), "{}_project".format(get.status))(get)

    # 2024/7/17 上午9:24 启动指定项目
    def start_project(self, get):
        '''
            @name Start the specified project
        '''
        get.project_type = get.get("project_type", None)
        if get.project_type is None:
            return public.return_message(-1, 0, public.lang( 'The "project_type" parameter cannot be left blank'))
        if not get.project_type in ("nodejs", "pm2", "general"):
            return public.return_message(-1, 0, public.lang('Project type: {} is not valid. Currently, it is supported by nodejs, pm2, and general.',get.project_type))
        get.project_name = get.get("project_name", None)
        if get.project_name is None:
            return public.return_message(-1, 0, public.lang( 'The "project_name" parameter cannot be left blank'))

        get.status = "start"
        if get.project_type == "pm2":
            get.pm2_name = get.get("pm2_name", "")
            if get.pm2_name == "":
                return public.return_message(-1, 0, public.lang( 'The "pm2_name" parameter cannot be left blank'))
            get.mode = "cluster_mode"
            get.name = get.pm2_name
            return self.set_pm2_status(get)
        else:
            from projectModel.nodejsModel import main
            return getattr(main(), "{}_project".format(get.status))(get)

    # 2024/7/17 上午9:24 重启指定项目
    def restart_project(self, get):
        '''
            @name Restart the specified project
        '''
        get.project_type = get.get("project_type", None)
        if get.project_type is None:
            return public.return_message(-1, 0, public.lang( 'The "project_type" parameter cannot be left blank'))
        if not get.project_type in ("nodejs", "pm2", "general"):
            return public.return_message(-1, 0, public.lang(
                                       'Project type: {} is not valid. Currently, it is supported by nodejs, pm2, and general.', get.project_type))
        get.project_name = get.get("project_name", None)
        if get.project_name is None:
            return public.return_message(-1, 0, public.lang( 'The "project_name" parameter cannot be left blank'))

        get.status = "restart"
        if get.project_type == "pm2":
            get.pm2_name = get.get("pm2_name", "")
            if get.pm2_name == "":
                return public.return_message(-1, 0, public.lang( 'The "pm2_name" parameter cannot be left blank'))
            get.mode = "cluster_mode"
            get.name = get.pm2_name
            return self.set_pm2_status(get)
        else:
            from projectModel.nodejsModel import main
            return getattr(main(), "{}_project".format(get.status))(get)

    # 2024/7/15 下午9:15 获取网站列表
    def get_project_list(self, get):
        '''
            @name 获取项目列表
            @author hwliang<2021-08-09>
            @param get<dict_obj>{
                project_name: string<项目名称>
            }
            @return dict
        '''

        if not 'p' in get:  get.p = 1
        if not 'limit' in get: get.limit = 20
        if not 'callback' in get: get.callback = ''
        if not 'order' in get: get.order = 'id desc'
        type_id = None
        if "type_id" in get:
            try:
                type_id = int(get.type_id)
            except:
                type_id = None

        if 'search' in get:
            get.project_name = get.search.strip()
            search = "%{}%".format(get.project_name)
            if type_id is None:
                count = public.M('sites').where('project_type=? AND (name LIKE ? OR ps LIKE ?)',
                                                ('Node', search, search)).count()
                data = public.get_page(count, int(get.p), int(get.limit), get.callback)
                data['data'] = public.M('sites').where('project_type=? AND (name LIKE ? OR ps LIKE ?)',
                                                       ('Node', search, search)).limit(
                    data['shift'] + ',' + data['row']).order(get.order).select()
            else:
                count = public.M('sites').where('project_type=? AND (name LIKE ? OR ps LIKE ?) AND type_id = ?',
                                                ('Node', search, search, type_id)).count()
                data = public.get_page(count, int(get.p), int(get.limit), get.callback)
                data['data'] = public.M('sites').where('project_type=? AND (name LIKE ? OR ps LIKE ?) AND type_id = ?',
                                                       ('Node', search, search, type_id)).limit(
                    data['shift'] + ',' + data['row']).order(get.order).select()
        else:
            if type_id is None:
                count = public.M('sites').where('project_type=?', 'Node').count()
                data = public.get_page(count, int(get.p), int(get.limit), get.callback)
                data['data'] = public.M('sites').where('project_type=?', 'Node').limit(
                    data['shift'] + ',' + data['row']).order(get.order).select()
            else:
                count = public.M('sites').where('project_type=? AND type_id = ?', ('Node', type_id)).count()
                data = public.get_page(count, int(get.p), int(get.limit), get.callback)
                data['data'] = public.M('sites').where('project_type=? AND type_id = ?', ('Node', type_id)).limit(
                    data['shift'] + ',' + data['row']).order(get.order).select()

        if isinstance(data["data"], str) and data["data"].startswith("error"):
            raise public.PanelError("数据库查询错误：" + data["data"])

        for i in range(len(data['data'])):
            data['data'][i] = self.get_project_stat(data['data'][i])
        return data

    # 2024/7/16 上午9:47 获取指定项目的信息
    def get_project_info(self, get):
        '''
            @name Get specified project information
            @author hwliang<2021-08-09>
            @param get<dict_obj>{
                project_name: string<Project name>
            }
            @return dict
        '''
        get.project_type = get.get("project_type", None)
        if get.project_type is None:
            return public.return_message(-1, 0, public.lang( 'The "project_type" parameter cannot be left blank'))
        if not get.project_type in ("nodejs", "pm2", "general"):
            return public.return_message(-1, 0, public.lang(
                                       'Project type: {} is not valid. Currently, it is supported by nodejs, pm2, and general.', get.project_type))
        get.project_name = get.get("project_name", None)
        if get.project_name is None:
            return public.return_message(-1, 0, public.lang( 'The "project_name" parameter cannot be left blank'))

        project_info = public.M('sites').where('project_type=? AND name=?', ('Node', get.project_name)).find()
        if not project_info:
            return public.return_message(-1, 0, public.lang( 'The specified project does not exist!'))
        project_info = self.get_project_stat(project_info)
        return project_info

    # 2024/7/16 上午10:46 编辑项目
    def modify_project(self, get):
        '''
            @name Modify the specified project
            @author hwliang<2021-08-09>
            @param get<dict_obj>{
                project_name: string<Project name>
                project_cwd: string<Project directory>
                project_script: string<Project script>
                project_ps: string<Project remarks>
                is_power_on: int<Whether to start on boot> 1:Yes 0:No
                run_user: string<Running user>
                max_memory_limit: int<Maximum memory limit> // The project will be forced to restart if it exceeds this value
                nodejs_version: string<Node.js version>
            }
            @return dict
        '''
        if not isinstance(get, public.dict_obj): return public.return_error('Parameter type error, dict_obj object is required')
        if not self.is_install_nodejs(get):
            return public.return_message(-1, 0, public.lang( 'Please install the nodejs version manager and at least one node.js version first'))
        project_find = self.get_project_find(get.project_name)
        if not project_find:
            return public.return_message(-1, 0, public.lang( 'The specified project does not exist: {}', get.project_name))

        if not os.path.exists(get.project_cwd):
            return public.return_message(-1, 0, public.lang( 'Project directory does not exist: {}', get.project_cwd))

        get.project_type = get.get("project_type", None)
        if get.project_type is None:
            return public.return_message(-1, 0, public.lang( 'The "project_type" parameter cannot be left blank'))
        if not get.project_type in ("nodejs", "pm2", "general"):
            return public.return_message(-1, 0, public.lang(
                                       'Project type: {} is not valid. Currently, it is supported by nodejs, pm2, and general.', get.project_type))
        get.project_name = get.get("project_name", None)
        if get.project_name is None:
            return public.return_message(-1, 0, public.lang( 'The "project_name" parameter cannot be left blank'))

        rebuild = False
        get.project_cwd = get.get("project_cwd", "")
        if get.project_cwd == "":
            return public.return_message(-1, 0, public.lang( 'The "project_cwd" parameter cannot be left blank'))
        if not os.path.exists(get.project_cwd):
            return public.return_message(-1, 0, public.lang( '{} The specified project directory does not exist', get.project_cwd))
        if not os.path.isdir(get.project_cwd):
            return public.return_message(-1, 0, public.lang( '{} The specified project directory is not a directory', get.project_cwd))

        if hasattr(get, 'project_cwd'):
            if get.project_cwd[-1] == '/':
                get.project_cwd = get.project_cwd[:-1]
            project_find['project_config']['project_cwd'] = get.project_cwd
            project_find['project_config']['project_script'] = get.project_script.strip()

        get.project_file = get.get("project_file", "")
        get.run_user = get.get("run_user", "www")
        # if hasattr(get, 'run_user'): project_find['project_config']['run_user'] = get.run_user
        get.port = get.get("port", "")
        if hasattr(get, 'port') and get.port != "":
            if not project_find['project_config']['port'] is None:
                if int(project_find['project_config']['port']) != int(get.port):
                    if self.check_port_is_used(get.get('port/port'), True):
                        return public.return_message(-1, 0, public.lang(
                                                   'The specified port is already occupied by other applications. Please modify your project configuration to use another port, port: {}',
                                                       get.port))
                    project_find['project_config']['port'] = int(get.port)
            else:
                if self.check_port_is_used(get.get('port/port'), True):
                    return public.return_message(-1, 0, public.lang(
                                               'The specified port is already occupied by other applications. Please modify your project configuration to use another port, port: {}',
                                                   get.port))
            project_find['project_config']['port'] = int(get.port)
        if get.port == "" or get.port is None:
            project_find['project_config']['port'] = None

        get.project_args = get.get("project_args", "")
        project_find['project_config']['project_args'] = get.project_args
        get.env = get.get("env", "")
        if get.env != "":
            env = get.env.split("\n")
            for e in env:
                if not "=" in e:
                    return public.return_message(-1, 0, public.lang( "Environment variable: {} format error, please re-enter for example: key=value", e))
            project_find['project_config']['env'] = get.env

        get.nodejs_version = get.get("nodejs_version", None)
        if get.nodejs_version is None:
            return public.return_message(-1, 0, public.lang( 'The "nodejs_version" parameter cannot be left blank'))
        if hasattr(get, 'nodejs_version'):
            if project_find['project_config']['nodejs_version'] != get.nodejs_version:
                rebuild = True
                project_find['project_config']['nodejs_version'] = get.nodejs_version

        get.pkg_manager = get.get("pkg_manager", "")
        if get.pkg_manager in ("npm", "pnpm", "yarn") and project_find['project_config']['project_type'] in ("nodejs", "pm2"):
            project_find['project_config']['pkg_manager'] = get.pkg_manager
        elif project_find['project_config']['project_type'] == "general": pass
        else:
            return public.return_message(-1, 0, public.lang( 'Invalid "pkg_manager" parameter, please enter npm, pnpm, or yarn'))

        if project_find['project_config'].get('pkg_manager', "") == "pnpm":
            _v = int(project_find['project_config']['nodejs_version'].split(".", 1)[0][1:])
            if _v < 12:
                return public.return_message(-1, 0, public.lang( "pnpm does not support Node.js versions below 12"))

        get.not_install_pkg = get.get("not_install_pkg", False)
        get.release_firewall = get.get("release_firewall", False)
        get.is_power_on = get.get("is_power_on", True)
        # if hasattr(get, 'is_power_on'): project_find['project_config']['is_power_on'] = get.is_power_on
        get.max_memory_limit = get.get("max_memory_limit", 1024)
        if hasattr(get, 'max_memory_limit'): project_find['project_config']['max_memory_limit'] = get.max_memory_limit
        get.project_ps = get.get("project_ps", "")
        if get.project_type == "pm2":
            from mod.project.nodejs.pm2Mod import main
            get.config_file = get.get("config_file", "")
            get.config_body = get.get("config_body", "")
            get.watch = get.get("watch", 'false')
            get.is_power_on = get.watch
            get.cluster = get.get("cluster/d", 1)
            self.set_pm2_cmd(get.nodejs_version)
            if get.config_file != "" or get.config_body != "":
                if get.config_file != "":
                    if not os.path.exists(get.config_file):
                        return public.return_message(-1, 0, public.lang( '{} The specified project configuration file does not exist',get.config_file))
                    if not os.path.isfile(get.config_file):
                        return public.return_message(-1, 0, public.lang( '{} The specified project configuration file is not a file', get.config_file))
                if get.config_body == "":
                    if get.config_file != "":
                        get.config_body = public.readFile(get.config_file)
                    if get.config_body == "":
                        return public.return_message(-1, 0, public.lang( '{} Configuration file format error, please check', get.config_file))
                    if not "module.exports" in get.config_body and not "apps:" in get.config_body:
                        return public.return_message(-1, 0, public.lang( '{} Configuration file format error, please check', get.config_file))
            else:
                get.max_memory_restart = "{}M".format(get.max_memory_limit)
                main().structure_ecosystem(get)
                main().structure_start_script(get)

            res = main().delete_for_ecosystem(get.nodejs_version, project_find['project_config']['config_file'], project_find['project_config']['run_user'])
            if res["status"] != 0:
                return public.return_message(-1, 0, public.lang( "Failed to stop the original project: {}, please delete and re-add it and try again",res["message"]['result']))

            # 更换执行用户重新生成脚本或切换版本
            if project_find['project_config']['run_user'] != get.run_user or rebuild:
                project_find['project_config']['project_script'] = main().start_script(get)

            project_script = project_find['project_config'].get('project_script','')
            res = main().start_for_ecosystem(get.nodejs_version, get.config_file, project_script)
            if res["status"] != 0:
                return public.return_message(-1, 0, public.lang( "Failed to start the edited project: {}, please delete and re-add it and try again", res["message"]))
            project_find['project_config']['run_user'] = get.run_user
            project_find['project_config']['config_file'] = get.config_file
            project_find['project_config']['config_body'] = get.config_body
            project_find['project_config']['watch'] = get.watch
            project_find['project_config']['is_power_on'] = get.watch
            project_find['project_config']['cluster'] = get.cluster
            project_find['project_config']['project_file'] = get.project_file
            project_find['project_config']['project_cwd'] = get.project_cwd
        elif get.project_type == "general":
            from mod.project.nodejs.generalMod import main
            main().structure_start_script(get)
        else:
            if hasattr(get, 'project_script'):
                if not get.project_script.strip():
                    return public.return_message(-1, 0, public.lang( 'The startup command cannot be empty'))

        pdata = {
            'path': get.project_cwd,
            'ps': get.project_ps,
            'project_config': json.dumps(project_find['project_config'])
        }

        public.M('sites').where('name=?', (get.project_name,)).update(pdata)
        self.set_config(get.project_name)
        public.WriteLog(self.log_name, 'Modified Node.js project {}'.format(get.project_name))
        if rebuild:
            self.rebuild_project(get.project_name)

        return public.return_message(0,0, public.lang( 'Project modified successfully'))
