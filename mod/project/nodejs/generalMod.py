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
# node通用项目功能模型
# ------------------------------
import sys
import time
import datetime

if "/www/server/panel/class" not in sys.path:
    sys.path.insert(0, "/www/server/panel/class")

os.chdir("/www/server/panel")
import public

if "/www/server/panel" not in sys.path:
    sys.path.insert(0, "/www/server/panel")
from mod.project.nodejs.base import NodeJs


class main(NodeJs):

    def __init__(self):
        super(main, self).__init__()

    # 2024/7/11 下午2:44 创建项目
    def create_project(self, get):
        '''
            @name 创建项目
            @param get: dict_obj {}
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
        self.set_self_get(get)
        self.set_def_name(get.def_name)
        get.project_cwd = get.get("project_cwd", None)
        get.project_file = get.get("project_file", None)
        if get.project_cwd is None:
            self.ws_err_exit(False, 'The "project_cwd" parameter cannot be left blank.', code=2)
        if not os.path.exists(get.project_cwd):
            self.ws_err_exit(False, '{} The specified project directory does not exist.'.format(get.project_cwd), code=2)
        if not os.path.isdir(get.project_cwd):
            self.ws_err_exit(False, '{} The specified project path is not a directory.'.format(get.project_cwd), code=2)
        if get.project_file is None:
            self.ws_err_exit(False, 'The "project_file" parameter cannot be left blank.', code=2)
        if not os.path.exists(get.project_file):
            self.ws_err_exit(False, '{} The specified project startup file does not exist.'.format(get.project_file), code=2)
        if not os.path.isfile(get.project_file):
            self.ws_err_exit(False, '{} The specified project startup file is not a file.'.format(get.project_file), code=2)
        get.project_name = get.get("project_name", None)
        if get.project_name is None:
            self.ws_err_exit(False, 'The "project_name" parameter cannot be left blank.', code=2)
        get.project_name = public.xssencode2(get.project_name)
        get.project_type = get.get("project_type", None)
        if get.project_type is None:
            self.ws_err_exit(False, 'The "project_type" parameter cannot be left blank.', code=2)
        if get.project_type != "general":
            self.ws_err_exit(False, 'This model only supports general projects.', code=2)
        get.project_args = get.get("project_args", "")
        get.run_user = get.get("run_user", "www")
        get.env = get.get("env", "")
        if get.env != "":
            get.env = get.env.split("\n")
            for env in get.env:
                if not "=" in env:
                    self.ws_err_exit(False, "Environment variable: {} format error, please re-enter for example: key=value".format(env), code=2)
            self.get_run_env(get)

        get.nodejs_version = get.get("nodejs_version", None)
        if get.nodejs_version is None:
            self.ws_err_exit(False, 'The "nodejs_version" parameter cannot be left blank.', code=2)
        get.release_firewall = get.get("release_firewall", False)
        get.is_power_on = get.get("is_power_on", True)
        get.max_memory_limit = get.get("max_memory_limit", 4096)

        get._ws.send(json.dumps(self.wsResult(True, "Constructing startup script...", code=0)))
        self.structure_start_script(get)
        get._ws.send(json.dumps(self.wsResult(True, "Startup script construction completed.", code=0)))
        get._ws.send(json.dumps(self.wsResult(True, "Writing necessary project configuration files...", code=1)))
        project_id = self.create_site(get)
        if project_id is None:
            self.ws_err_exit(False, 'Failed to create the website, unable to write to the database normally. Please try adding it again!', code=2)
        self.set_config(get.project_name)
        get._ws.send(json.dumps(self.wsResult(True, "Configuration file writing completed.\r\nStarting the project...", code=1)))
        start_result = self.start_project(get)
        if not start_result["status"]:
            self.ws_err_exit(False, start_result["msg"] if "msg" in start_result else start_result["error_msg"], code=5)
        get._ws.send(json.dumps(self.wsResult(True, "Project created successfully!", code=-1)))
        get._ws.close()

    # 2024/7/13 上午10:21 构造传统项目的启动脚本
    def structure_start_script(self, get):
        '''
            @name 构造传统项目的启动脚本
        '''
        last_env = self.get_last_env(get.nodejs_version)
        node_bin = self.get_node_bin(get.nodejs_version)
        env = "\n".join(["export {}".format(x) for x in get.env.split('\n')])
        command = '''{last_env}
{run_env}
export NODE_PROJECT_NAME="{project_name}"
cd {project_cwd}
nohup {node_bin} {project_file} {project_args} &>> {log_file} &
echo $! > {pid_file}
'''.format(
            last_env=last_env,
            run_env=env,
            project_cwd=get.project_cwd,
            node_bin=node_bin,
            project_file=get.project_file,
            project_args=get.project_args,
            log_file="{}/{}.log".format(self.node_logs_path, get.project_name),
            pid_file="{}/{}.pid".format(self.node_pid_path, get.project_name),
            project_name=get.project_name
        )

        public.writeFile(os.path.join(get.project_cwd, "{}_start.sh".format(get.project_name)), command)
        get.project_script = command

    # 2024/7/13 上午10:12 启动项目
    def start_project(self, get):
        '''
            @name Start project
        '''
        pid_file = "{}/{}.pid".format(self.node_pid_path, get.project_name)
        if os.path.exists(pid_file):
            self.stop_project(get)

        project_find = self.get_project_find(get.project_name)
        if not project_find: return public.return_message(-1, 0, public.lang( "The project does not exist"))

        project_find = self.get_project_find(get.project_name)
        if project_find['edate'] != "0000-00-00" and project_find['edate'] < datetime.datetime.today().strftime("%Y-%m-%d"):
            return public.return_message(-1, 0, public.lang( "The current project has expired. Please reset the project expiration date"))

        self._update_project(get.project_name, project_find)
        if not os.path.exists(project_find['path']):
            error_msg = 'Failed to start, Nodejs project {}, the running directory {} does not exist!'.format(get.project_name, project_find['path'])
            public.WriteLog(self.log_name, error_msg)
            return public.return_message(-1, 0, error_msg)

        # Preparations
        nodejs_version = project_find['project_config']['nodejs_version']
        node_bin = self.get_node_bin(nodejs_version)
        project_script = project_find['project_config']['project_script'].strip().replace('  ', ' ')
        log_file = "{}/{}.log".format(project_find['project_config']["log_path"], project_find["name"])
        if not project_script: return public.return_message(-1, 0, public.lang( "No startup script configured"))

        last_env = self.get_last_env(nodejs_version, project_find['path'])
        public.writeFile(log_file, '')
        public.ExecShell('chmod 777 {}'.format(log_file))
        # 生成启动脚本
        if os.path.exists(project_script):
            start_cmd = '''{last_env}
export NODE_PROJECT_NAME="{project_name}"
cd {project_cwd}
nohup {node_bin} {project_script} &>> {log_file} &
echo $! > {pid_file}
'''.format(
                project_cwd=project_find['path'],
                node_bin=node_bin,
                project_script=project_script,
                log_file=log_file,
                pid_file=pid_file,
                last_env=last_env,
                project_name=get.project_name
            )
        else:
            get.nodejs_version = project_find['project_config']['nodejs_version']
            get.env = project_find['project_config']['env']
            get.project_cwd = project_find['project_config']['project_cwd']
            get.project_file = project_find['project_config']['project_file']
            get.project_args = project_find['project_config']['project_args']
            self.structure_start_script(get)
            start_cmd = get.project_script
        script_file = "{}/{}.sh".format(self.node_run_scripts, get.project_name)
        # 写入启动脚本
        public.writeFile(script_file, start_cmd)
        if os.path.exists(pid_file): os.remove(pid_file)

        # 处理前置权限
        public.ExecShell("chown -R {user}:{user} {project_cwd}".format(
            user=project_find['project_config']['run_user'],
            project_cwd=project_find['path']))
        public.ExecShell("chown -R www:www {}/vhost".format(self.nodejs_path))
        public.ExecShell("chmod 755 {} {} {}".format(self.nodejs_path, public.get_setup_path(), '/www'))
        public.set_own(script_file, project_find['project_config']['run_user'],
                       project_find['project_config']['run_user'])
        public.set_mode(script_file, 755)

        # 执行脚本文件
        p = public.ExecShell("bash {}".format(script_file),
                             user=project_find['project_config']['run_user'],
                             env=os.environ.copy())

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
                    return public.return_message(-1, 0, public.lang( 'The startup command was blocked by [BT Security]. Please disable the protection for the {} user.',
                        project_find['project_config']['run_user']))
                return public.return_message(-1, 0, public.lang('The startup command was blocked by unknown security software. Please check the installation software logs.'))
            return public.return_message(-1, 0, public.lang(
                                       'Failed to start{}<script>setTimeout(function(){{$(".layui-layer-msg").css("width","800px");}},100)</script>',
                                           p))

        if p[-1]:
            public.return_message(-1, 0, public.lang( 'Failed to start{}', p[-1]))

        # Get PID
        try:
            pid = int(public.readFile(pid_file))
        except:
            return public.return_message(-1, 0, public.lang( 'Failed to start{}', public.GetNumLines(log_file, 20)))
        pids = self.get_project_pids(pid=pid)
        if not pids:
            if os.path.exists(pid_file): os.remove(pid_file)
            return public.return_message(-1, 0, public.lang( 'Failed to start{}', public.GetNumLines(log_file, 20)))

        self.start_by_user(project_find["id"])
        return public.return_message(0, 0, public.lang( 'Started successfully'))

    # 2024/7/12 上午9:58 停止项目
    def stop_project(self, get):
        '''
            @name Stop project
            @author hwliang<2021-08-09>
            @param get<dict_obj>{
                project_name: string<Project name>
            }
            @return dict
        '''
        project_find = self.get_project_find(get.project_name)
        if not project_find: return public.return_message(-1, 0, public.lang( 'The project does not exist'))
        project_find = self.get_project_find(get.project_name)
        if project_find['edate'] != "0000-00-00" and project_find['edate'] < datetime.datetime.today().strftime("%Y-%m-%d"):
            return public.return_message(-1, 0, public.lang( 'The current project has expired. Please reset the project expiration date'))
        project_script = project_find['project_config']['project_script'].strip().replace('  ', ' ')
        pid_file = "{}/{}.pid".format(self.node_pid_path, get.project_name)
        if project_script.find('pm2 start') != -1:  # Handle PM2 started projects
            nodejs_version = project_find['project_config']['nodejs_version']
            last_env = self.get_last_env(nodejs_version, project_find['path'])
            project_script = project_script.replace('pm2 start', 'pm2 stop')
            public.ExecShell('''{}
cd {}
{}'''.format(last_env, project_find['path'], project_script))
        else:
            pid_file = "{}/{}.pid".format(self.node_pid_path, get.project_name)
            if not os.path.exists(pid_file): return public.return_message(-1, 0, public.lang( 'The project is not started'))
            data = public.readFile(pid_file)
            if isinstance(data, str) and data:
                pid = int(data)
                pids = self.get_project_pids(pid=pid)
            else:
                return public.return_message(-1, 0, public.lang( 'The project is not started'))
            if not pids: return public.return_message(-1, 0, public.lang( 'The project is not started'))
            self.kill_pids(pids=pids)
        if os.path.exists(pid_file): os.remove(pid_file)
        time.sleep(0.5)
        pids = self.get_project_state_by_cwd(get.project_name)
        if pids: self.kill_pids(pids=pids)

        self.stop_by_user(project_find["id"])
        return public.return_message(0, 0, public.lang( 'Stopped successfully'))

    # 2024/7/17 上午11:09 重启项目
    def restart_project(self, get):
        '''
            @name Restart project
            @author hwliang<2021-08-09>
            @param get<dict_obj>{
                project_name: string<Project name>
            }
            @return dict
        '''
        project_find = self.get_project_find(get.project_name)
        if project_find:
            if project_find['edate'] != "0000-00-00" and project_find['edate'] < datetime.datetime.today().strftime("%Y-%m-%d"):
                return public.return_message(-1, 0, public.lang( 'The current project has expired. Please reset the project expiration date'))
        res = self.stop_project(get)
        if not res['status']: return res
        res = self.start_project(get)
        if not res['status']: return res
        return public.return_message(0, 0, public.lang( 'Restarted successfully'))
