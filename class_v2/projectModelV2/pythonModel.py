# coding: utf-8
# -------------------------------------------------------------------
# aaPanel
# -------------------------------------------------------------------
# Copyright (c) 2014-2099 aaPanel(www.aapanel.com) All rights reserved.
# -------------------------------------------------------------------
# Author: aapanel
# -------------------------------------------------------------------
# ------------------------------
# Python Model app
# ------------------------------

import json
import os
import re
import shlex
import subprocess
import sys
import time
from typing import Union, Dict, TextIO, Optional, Tuple, List, Set, Callable

import psutil

if "/www/server/panel" not in sys.path:
    sys.path.insert(0, "/www/server/panel")

import public

public.sys_path_append("/class_v2")

from public.exceptions import HintException
from public.validate import Param
from ssh_terminal_v2 import ssh_terminal
from projectModelV2.base import projectBase
from mod.project.python.pyenv_tool import EnvironmentManager, PythonEnvironment, EnvironmentReporter
from urllib3.util import parse_url

try:
    from BTPanel import cache
    from class_v2.projectModelV2.btpyvm import PYVM
except:
    PYVM = None
    pass

try:
    import requirements
except ImportError:
    public.ExecShell("btpip install requirements-parser")


def check_pyvm_exists(func):
    def wpper(self, get):
        if not os.path.exists(f"{public.get_panel_path()}/class_v2/projectModelV2/btpyvm.py"):
            raise HintException(
                public.lang("Python Manager is Lost, Please Go To Homepage Fix The Panel")
            )
        return func(self, get)

    return wpper


def _init_ln_gvm() -> None:
    panel_path = "/www/server/panel"
    pyvm_path = "/usr/bin/pyvm"
    bt_py_project_env_path = "/usr/bin/py-project-env"
    try:
        if not os.path.exists(pyvm_path):
            real_path = '{}/class_v2/projectModel/btpyvm.py'.format(panel_path)
            os.chmod(real_path, mode=0o755)
            os.symlink(real_path, pyvm_path)

        if not os.path.exists(bt_py_project_env_path):
            real_path = '{}/script/btpyprojectenv.sh'.format(panel_path)
            os.chmod(real_path, mode=0o755)
            os.symlink(real_path, bt_py_project_env_path)
    except Exception:
        pass


try:
    _init_ln_gvm()
    del _init_ln_gvm
except Exception:
    pass


class main(projectBase):
    _panel_path = public.get_panel_path()
    _project_path = '/www/server/python_project'
    _log_name = 'Python Manager'
    _pyv_path = '/www/server/pyporject_evn'
    _tmp_path = '/var/tmp'
    _logs_path = '{}/vhost/logs'.format(_project_path)
    _script_path = '{}/vhost/scripts'.format(_project_path)
    _pid_path = '{}/vhost/pids'.format(_project_path)
    _env_path = '{}/vhost/env'.format(_project_path)
    _prep_path = '{}/prep'.format(_project_path)
    _activate_path = '{}/active_shell'.format(_project_path)
    _project_logs = '/www/wwwlogs/python'
    _vhost_path = '{}/vhost'.format(_panel_path)
    _pip_source = "https://mirrors.aliyun.com/pypi/simple/"
    __log_split_script_py = public.get_panel_path() + '/script/run_log_split.py'
    _project_conf = {}
    _pids = None
    _split_cron_name_temp = "[Do not delete]Python Project [{}] log split task"
    _restart_cron_name = "[Do Not Delete] Scheduled Restart python Project {}"
    pip_source_dict = {
        "pypi": "https://pypi.org/simple/",  # PyPI 官方
        "fastly": "https://pypi.python.org/simple/",  # Fastly CDN
        "rackspace": "https://pypi.mirror.rackspace.com/simple/",  # Rackspace CDN
        "aliyun": "https://mirrors.aliyun.com/pypi/simple/",  # 阿里云
        "tsinghua": "https://pypi.tuna.tsinghua.edu.cn/simple",  # 清华大学
        "ustc": "https://pypi.mirrors.ustc.edu.cn/simple/",  # 中国科技大学
        "tencent": "https://mirrors.cloud.tencent.com/pypi/simple",  # 腾讯云
        "huaweicloud": "https://mirrors.huaweicloud.com/repository/pypi/simple",  # 华为云
    }

    def __init__(self):
        super().__init__()
        if not os.path.exists(self._project_path):
            os.makedirs(self._project_path, mode=0o755)

        if not os.path.exists(self._logs_path):
            os.makedirs(self._logs_path, mode=0o777)

        if not os.path.exists(self._project_logs):
            os.makedirs(self._project_logs, mode=0o777)

        if not os.path.exists(self._pyv_path):
            os.makedirs(self._pyv_path, mode=0o755)

        if not os.path.exists(self._script_path):
            os.makedirs(self._script_path, mode=0o755)

        if not os.path.exists(self._pid_path):
            os.makedirs(self._pid_path, mode=0o777)

        if not os.path.exists(self._prep_path):
            os.makedirs(self._prep_path, mode=0o755)

        if not os.path.exists(self._env_path):
            os.makedirs(self._env_path, mode=0o755)

        if not os.path.exists(self._activate_path):
            os.makedirs(self._activate_path, mode=0o755)
        self._pids = None
        self._pyvm_tool = None
        self._environment_manager: Optional[EnvironmentManager] = None

    @property
    def pyvm(self) -> Optional[PYVM]:
        if PYVM is None:
            return None
        if self._pyvm_tool is None:
            self._pyvm_tool = PYVM()
        return self._pyvm_tool

    @property
    def environment_manager(self) -> EnvironmentManager:
        if self._environment_manager is None:
            self._environment_manager = EnvironmentManager()
        return self._environment_manager

    def need_update_project(self, update_name: str) -> bool:
        tip_file = "{}/{}.pl".format(self._project_path, update_name)
        if os.path.exists(tip_file):
            return True
        return False

    def RemovePythonV(self, get):
        """卸载面板安装的Python
        @author baozi <202-02-22>
        @param:
            get  ( dict ):  请求信息，包含要删除的版本信息
        @return  msg : 是否删除成功
        """
        v = get.version.split()[0]
        if "is_pypy" in get and get.is_pypy in ("1", "true", 1, True):
            path = '{}/pypy_versions'.format(self._pyv_path)
        else:
            path = '{}/versions'.format(self._pyv_path)
        if not os.path.exists(path):
            return public.success_v2(public.lang("Python Version Uninstall Successfully"))
        python_bin = "{}/{}/bin/python".format(path, v)
        if not os.path.exists(python_bin):
            python_bin = "{}/{}/bin/python3".format(path, v)
        if not os.path.exists(python_bin):
            return public.fail_v2(public.lang("Python Version Not Found! "))

        res = EnvironmentManager().multi_remove_env(os.path.realpath(python_bin))
        for r in res:
            if r.get("status"):
                return public.success_v2(public.lang("Python Version Uninstall Successfully"))
            return public.fail_v2(r.get("msg", public.lang("Failed to uninstall Python Version")))

        return public.success_v2(public.lang("Python Version Uninstall Successfully"))

    def _get_project_conf(self, name_id) -> Union[Dict, bool]:
        """获取项目的配置信息
        @author baozi <202-02-22>
        @param:
            name_id  ( str|id ):  项目名称或者项目id
        @return dict_onj: 项目信息
        """
        if isinstance(name_id, int):
            _id = name_id
            _name = None
        else:
            _id = None
            _name = name_id
        data = public.M('sites').where('project_type=? AND (name = ? OR id = ?)', ('Python', _name, _id)).field(
            'name,path,status,project_config').find()
        if not data:
            return False
        project_conf = json.loads(data['project_config'])
        if "env_list" not in project_conf:
            project_conf["env_list"] = []
        if "env_file" not in project_conf:
            project_conf["env_file"] = ""
        if "call_app" not in project_conf:
            project_conf["call_app"] = ""
        if not os.path.exists(data["path"]):
            self.__stop_project(project_conf)
        return project_conf

    def _get_vp_pip(self, vpath) -> str:
        """获取虚拟环境下的pip
        @author baozi <202-02-22>
        @param:
            vpath  ( str ):  虚拟环境位置
        @return  str : pip 位置
        """
        if os.path.exists('{}/bin/pip'.format(vpath)):
            return '{}/bin/pip'.format(vpath)
        else:
            return '{}/bin/pip3'.format(vpath)

    def _get_vp_python(self, vpath) -> str:
        """获取虚拟环境下的python解释器
        @author baozi <202-02-22>
        @param:
            vpath  ( str ):  虚拟环境位置
        @return  str : python解释器 位置
        """
        if os.path.exists('{}/bin/python'.format(vpath)):
            return '{}/bin/python'.format(vpath)
        else:
            return '{}/bin/python3'.format(vpath)

    def list_system_user(self, get=None):  # NOQA
        return public.success_v2(self.get_system_user_list())

    @staticmethod
    def _check_port(port: str) -> Tuple[bool, str]:
        """检查端口是否合格
        @author baozi <202-02-22>
        @param
            port  ( str ):  端口号
        @return   [bool,msg]: 结果 + 错误信息
        """
        try:
            if 0 < int(port) < 65535:
                data = public.ExecShell("ss  -nultp|grep ':%s '" % port)[0]
                if data:
                    return False, public.lang("prot is used")
                else:
                    return True, ""
            else:
                return False, public.lang("please enter correct port range 1 < port < 65535")
        except ValueError:
            return False, public.lang("please enter correct port range 1 < port < 65535")

    @staticmethod
    def _check_project_exist(project_name) -> bool:
        """检查项目是否存在
        @author baozi <202-02-22>
        @param:
            pjname  ( str ):  项目名称
            path  ( str ):  项目路径
        @return  bool : 返回验证结果
        """
        data = public.M('sites').where('name=?', (project_name,)).field('id').find()
        if data and isinstance(data, dict):
            return True
        return False

    @staticmethod
    def _check_project_path_exist(path=None) -> bool:
        """检查项目地址是否存在
        @author baozi <202-02-22>
        @param:
            pjname  ( str ):  项目名称
            path  ( str ):  项目路径
        @return  bool : 返回验证结果
        """
        data = public.M('sites').where('path=? ', (path,)).field('id').find()
        if data and isinstance(data, dict) and os.path.exists(path):
            return True
        return False

    @staticmethod
    def __check_feasibility(values) -> Optional[str]:
        """检查用户部署方式的可行性
        @author baozi <202-02-22>
        @param:
            values  ( dict ):  用户输入参数的规范化数据
        @return  msg
        """
        re_v = re.compile(r"\s+(?P<ver>[23]\.\d+(\.\d+)?)\s*")
        version_res = re_v.search(values["version"])
        if not version_res:
            return None
        version = version_res.group("ver")
        xsgi = values["xsgi"]
        framework = values["framework"]
        stype = values["stype"]
        if framework == "sanic" and [int(i) for i in version.split('.')[:2]] < [3, 7]:
            return public.lang("sanic not support python version below 3.7")
        if xsgi == "asgi" and stype == "uwsgi":
            return public.lang("uWsgi Service Not Support Asgi Protocol")
        return None

    def _get_fastest_pip_source(self, call_log) -> str:
        """测速选择最快的 pip 源"""
        import concurrent.futures
        import urllib.request
        import math
        default_source = "https://pypi.org/simple"

        def test_speed(name_url):
            name, url = name_url
            try:
                start = time.time()
                req = urllib.request.Request(url, headers={"User-Agent": "pip/21.0"})
                with urllib.request.urlopen(req, timeout=5) as resp:
                    resp.read(512)
                elapsed = time.time() - start
                return elapsed, url
            except Exception:
                return float("inf"), url

        try:
            sources = list(self.pip_source_dict.items())
            with concurrent.futures.ThreadPoolExecutor(max_workers=len(sources)) as executor:
                results = list(executor.map(test_speed, sources))
            valid_results = [
                (t, url) for t, url in results if not math.isinf(t)
            ]
            call_log("\n|- Pip Source Speed Test Results:\n")
            call_log("\n".join([f"  {name}: {t:.2f}s" for (t, url), (name, u) in zip(results, sources)]))
            if not valid_results:
                return default_source
            fastest_time, fastest_url = min(valid_results, key=lambda x: x[0])
            call_log(f"\n|- Fastest Pip Source: {fastest_url} ({fastest_time:.2f}s)\n")
            return fastest_url
        except Exception:
            return default_source

    def _fallback_install_requirement(self, values: dict, pyenv: PythonEnvironment, call_log: Callable[[str], None]):
        if "requirement_path" in values and values["requirement_path"] is not None:
            call_log("\n|- Start Install Python Project's Requirement....\n")
            requirement_data = public.read_rare_charset_file(values['requirement_path'])
            if not isinstance(requirement_data, str):
                call_log("\n|- Requirement Not Found!\n")
            list_sh = []
            list_normative_pkg = []
            for i in requirement_data.split("\n"):
                tmp_data = i.strip()
                if not tmp_data or tmp_data.startswith("#"):
                    continue
                if re.search(r"-e\s+\.{0,2}/", tmp_data):  # 本地库依赖且为可编辑模式的不安装
                    continue
                tmp_env = ""
                if tmp_data.find("-e") != -1:
                    tmp_env += "cd {}\n".format(values["path"])
                if tmp_data.find("git+") != -1:
                    tmp_sh = tmp_env + "{} install {}".format(pyenv.pip_bin(), tmp_data)
                    rep_name_list = [re.compile(r"#egg=(?P<name>\S+)"), re.compile(r"/(?P<name>\S+\.git)")]
                    name = tmp_data
                    for tmp_rep in rep_name_list:
                        tmp_name = tmp_rep.search(tmp_data)
                        if tmp_name:
                            name = tmp_name.group("name")
                            break
                    list_sh.append((name, tmp_sh))

                elif tmp_data.find("file:") != -1:
                    tmp_sh = tmp_env + "{} install {}".format(pyenv.pip_bin(), tmp_data)

                    list_sh.append((tmp_data.split("file:", 1)[1], tmp_sh))
                else:
                    if tmp_data.find("==") != -1:
                        pkg_name, pkg_version = tmp_data.split("==")
                    elif tmp_data.find(">=") != -1:
                        pkg_name, pkg_version = tmp_data.split(">=")
                    else:
                        pkg_name, pkg_version = tmp_data, ""
                    list_normative_pkg.append((pkg_name, pkg_version))

            length = len(list_sh) + len(list_normative_pkg)
            for idx, (name, tmp_sh) in enumerate(list_sh):
                call_log(f"\n|- ({idx + 1}/{length}) Start Install [{name}]...\n")
                pyenv.exec_shell(tmp_sh, call_log=call_log)

            for idx, (name, pkg_version) in enumerate(list_normative_pkg):
                call_log(f"\n|- ({idx + len(list_sh) + 1}/{length}) Start Install [{name}]...\n")
                pyenv.pip_install(name, pkg_version, call_log=call_log)
            call_log("\n|- Install Requirement Success, Finished....\n")

    def install_requirement(self, values: dict, pyenv: PythonEnvironment, call_log: Callable[[str], None]):
        if "requirement_path" not in values or values["requirement_path"] is None:
            call_log("\n|- No Requirement To Install.\n")
            return
        call_log("\n|- Checking Faster PIP Source...\n")
        faster_pip_url = self._get_fastest_pip_source(call_log)
        new_pip = None
        for name, url in self.pip_source_dict.items():
            if url == faster_pip_url:
                new_pip = name
                call_log(f"\n|- Fastest PIP Source: {name} ({url})\n")
                break
        if new_pip:
            call_log(f"\n|- Switch PIP Source To {new_pip} For Faster Installation...\n")
            pyenv.set_pip_source(faster_pip_url)

        call_log("\n|- Start Install Python Project's Requirement....\n")
        requirement_data = public.read_rare_charset_file(values['requirement_path'])
        if not isinstance(requirement_data, str):
            call_log("\n|- Requirement Not Found!\n")
            return

        try:
            import requirements
        except ImportError:
            call_log("\n|- Install Requirement Parser...\n")
            public.ExecShell("btpip install requirements-parser")
            try:
                import requirements # noqa
            except Exception as e:
                public.print_log(f"Failed to import requirements module: {e}")
                self._fallback_install_requirement(values, pyenv, call_log)
                return

        list_sh = []
        list_normative_pkg = []
        try:
            import io
            for req in requirements.parse(io.StringIO(requirement_data)):
                # 跳过本地可编辑路径依赖如 -e ./ 或 -e ../
                if req.local_file and req.editable:
                    continue
                if req.vcs:
                    # git+ 等 VCS 依赖
                    vcs_url = "{}+{}@{}#egg={}".format(
                        req.vcs, req.uri, req.revision, req.name
                    ) if req.revision else "{}+{}#egg={}".format(req.vcs, req.uri, req.name)
                    tmp_env = ""
                    if req.editable:
                        tmp_env = "cd {}\n".format(values["path"])
                        vcs_url = "-e " + vcs_url
                    tmp_sh = tmp_env + "{} install {}".format(pyenv.pip_bin(), vcs_url)
                    list_sh.append((req.name or vcs_url, tmp_sh))
                elif req.local_file:
                    # file: 本地文件依赖
                    tmp_sh = "{} install {}".format(pyenv.pip_bin(), req.uri or req.name)
                    list_sh.append((req.name or req.uri, tmp_sh))
                else:
                    # 普通包，提取版本号仅取 == 的版本，其余空让pip自动
                    pkg_name = req.name
                    if not pkg_name:
                        continue
                    pkg_version = ""
                    for spec_op, spec_ver in (req.specs or []):
                        if spec_op == "==":
                            pkg_version = spec_ver
                            break
                    list_normative_pkg.append((pkg_name, pkg_version))

            length = len(list_sh) + len(list_normative_pkg)
            for idx, (name, tmp_sh) in enumerate(list_sh):
                call_log(f"\n|- ({idx + 1}/{length}) Start Install [{name}]...\n")
                if new_pip and " install " in tmp_sh:
                    tmp_sh = tmp_sh.replace(" install ", f" install -i {faster_pip_url} ", 1)
                pyenv.exec_shell(tmp_sh, call_log=call_log)

            for idx, (name, pkg_version) in enumerate(list_normative_pkg):
                call_log(f"\n|- ({idx + len(list_sh) + 1}/{length}) Start Install [{name}]...\n")
                pyenv.pip_install(name, pkg_version, call_log=call_log)

            call_log("\n|- Install Requirement Success, Finished....\n")
        except Exception as e:
            call_log(f"\n|- requirements-parser parse error: {e}, fallback to line-by-line parse\n")
            public.print_log(f"Failed to parse requirements file: {e}")
            self._fallback_install_requirement(values, pyenv, call_log)
            return

    def re_prep_env(self, get: public.dict_obj):
        name = get.name.strip()
        project_info = self.get_project_find(name)
        if not project_info:
            return public.fail_v2("Project Not Found!")
        project_conf = project_info['project_config']

        prep_status = self.prep_status(project_conf)
        if prep_status == "complete":
            return public.success_v2("Project Preparation Completed, No Need To Prepare Again")
        if prep_status == "running":
            return public.fail_v2("Project Is Preparing, Please Wait For A While")
        self.run_simple_prep_env(project_info["id"], project_conf)
        time.sleep(0.5)
        return public.success_v2("Project Re-Preparation Started, Please Wait For Completion")

    @staticmethod
    def exec_shell(sh_str: str, out: TextIO, timeout=None, user=None):
        if user:
            import pwd
            res = pwd.getpwnam(user)
            uid = res.pw_uid
            gid = res.pw_gid

            def preexec_fn():
                os.setgid(gid)
                os.setuid(uid)
        else:
            preexec_fn = None

        p = subprocess.Popen(sh_str, stdout=out, stderr=out, shell=True, preexec_fn=preexec_fn)
        p.wait(timeout=timeout)
        return

    def simple_prep_env(self, values: dict) -> Optional[bool]:
        """
        准备python虚拟环境和服务器应用
        """
        log_path: str = f"{self._logs_path}/{values['pjname']}.log"
        fd = open(log_path, 'w')
        fd.flush()
        py_env = EnvironmentManager().get_env_py_path(values.get("python_bin", ""))
        if not py_env:
            fd.write("|- Env Not Found. Stop Init Python")
            fd.flush()
            fd.close()
            return False

        def call_log(log: str) -> None:
            if log[-1] != "\n":
                log += "\n"
            fd.write(log)
            fd.flush()

        try:
            # 安装服务器依赖
            call_log("\n|- Start Intall Requirement.\n")
            py_env.init_site_server_pkg(call_log=call_log)
            py_env.use2project(values['pjname'])
            # 安装第三方依赖
            self.install_requirement(values, py_env, call_log=call_log)
            self.__prepare_start_conf(values, pyenv=py_env)
            call_log("\n|- Config file Generate Success.\n")
            initialize = values.get("initialize", '')
            if initialize:
                call_log("\n|- Start excute initialize command.......\n")
                if values.get("env_list", None) or values.get("env_file", None):
                    env_file = f"{self._env_path}/{values["pjname"]}.env"
                    initialize = f"source {env_file} \n{initialize}"

                chdir_prefix = f"cd {values["path"]}\n"
                initialize = chdir_prefix + initialize
                py_env.exec_shell(initialize, call_log=call_log, user=values.get("user", "root"))
                call_log("\n|- Python Project initialize Finished.......\n")

            # 先尝试启动
            conf = self._get_project_conf(values['pjname'])
            call_log("\n|- Try To Start Project\n")
            self.__start_project(conf)
            for k, v in values.items():  # 更新配置文件
                if k not in conf:
                    conf[k] = v

            pdata = {
                "project_config": json.dumps(conf)
            }
            public.M('sites').where('name=?', (values['pjname'].strip(),)).update(pdata)
            call_log(f"\n|- Python Project [{values['pjname']}] Initialize Finished.\n")
        except:
            import traceback
            if not fd.closed:
                fd.write(traceback.format_exc())
                fd.write("\n|- Environment initialize Failed\n")
        finally:
            if fd:
                fd.close()
        return True

    def run_simple_prep_env(self, project_id: int, project_conf: dict) -> Tuple[bool, str]:
        prep_pid_file = "{}/{}.pid".format(self._prep_path, project_conf["pjname"])
        if os.path.exists(prep_pid_file):
            pid = public.readFile(prep_pid_file)
            try:
                ps = psutil.Process(int(pid))
                if ps.is_running():
                    return False, "Project Is Preparing, Please Wait For A While"
            except:
                pass
            try:
                os.remove(prep_pid_file)
            except:
                pass
        # simple_prep_env()
        tmp_sh = "nohup {}/pyenv/bin/python3 {}/script/py_project_env.py {} &> /dev/null & \necho $! > {}".format(
            self._panel_path, self._panel_path, project_id, prep_pid_file
        )
        public.ExecShell(tmp_sh)
        return True, ""

    def prep_status(self, project_conf: dict) -> str:
        try:
            prep_pid_file = f"{self._prep_path}/{project_conf["pjname"]}.pid"
            if os.path.exists(prep_pid_file):
                pid = public.readFile(prep_pid_file)
                if isinstance(pid, str):
                    ps = psutil.Process(int(pid))
                    if ps.is_running() and os.path.samefile(ps.exe(), "/www/server/panel/pyenv/bin/python3") and \
                            any("script/py_project_env.py" in tmp for tmp in ps.cmdline()):
                        return "running"
        except:
            pass
        v_path = project_conf["vpath"]
        v_pip: str = self._get_vp_pip(v_path)
        v_python: str = self._get_vp_python(v_path)
        if not os.path.exists(v_path) or not os.path.exists(v_python) or not os.path.exists(v_pip):
            return "failure"
        return "complete"

    # 检查输入参数
    def __check_args(self, get) -> dict:
        """检查输入的参数
        @author baozi <202-02-22>
        @param:
            get  ( dict ):   创建Python项目时的请求
        @return  dict : 规范化的请求参数
        参数列表：
            pjname
            port
            stype
            path
            user
            requirement_path
            env_list
            env_file
            framework

            可能有：
               # venv_path
               # version

               venv_path 和 version 替换为 python_bin

               initialize

               project_cmd

               xsgi
               rfile
               call_app

               is_pypy
               logpath
               auto_run
        """

        project_cmd = ""
        xsgi = "wsgi"
        rfile = ""
        call_app = "app"
        user = "root"
        initialize = ""
        try:
            if public.get_webserver() == "openlitespeed":
                raise HintException(
                    public.lang("OpenLiteSpeed Not Support Python Project Now. Please Use Nginx or Apache")
                )
            pjname = get.pjname.strip()
            port = get.port
            stype = get.stype.strip()
            path = get.path.strip().rstrip("/")
            python_bin = get.get("python_bin/s", "")
            if not python_bin or not os.path.exists(python_bin):
                raise HintException(public.lang("Python Environment Not Found"))
            if "user" in get and get.user.strip():
                user = get.user.strip()
            if "requirement_path" in get and get.requirement_path:
                requirement_path = get.requirement_path.strip()
            else:
                requirement_path = None
            if "env_list" in get and get.env_list:
                if isinstance(get.env_list, str):
                    env_list = json.loads(get.env_list.strip())
                else:
                    env_list = get.env_list
            else:
                env_list = []
            if "env_file" in get and get.env_file:
                env_file = get.env_file.strip()
            else:
                env_file = None
            if "framework" in get and get.framework:
                framework = get.framework.strip()
            else:
                framework = 'python'
            if "project_cmd" in get and get.project_cmd:
                project_cmd = get.project_cmd.strip()
            if "xsgi" in get and get.xsgi:
                if get.xsgi.strip() not in ("wsgi", "asgi"):
                    xsgi = "wsgi"
                else:
                    xsgi = get.xsgi.strip()
            if "rfile" in get and get.rfile:
                rfile = get.rfile.strip()
                if not os.path.exists:
                    raise HintException(public.lang("Project Start File Not Found"))
            if "call_app" in get and get.call_app:
                call_app = get.call_app.strip()
            if "initialize" in get and get.initialize:
                initialize = get.initialize.strip()
        except Exception as e:
            import traceback
            public.print_log(f"Parameter Error: {traceback.format_exc()}")
            raise HintException(public.lang(e))

        danger_cmd_list = [
            'rm', 'rmi', 'kill', 'init', 'shutdown', 'reboot', 'chmod', 'chown', 'dd', 'fdisk', 'killall', 'mkfs',
            'mkswap', 'mount', 'swapoff', 'swapon', 'umount', 'userdel', 'usermod', 'passwd', 'groupadd', 'groupdel',
            'groupmod', 'chpasswd', 'chage', 'usermod', 'useradd', 'userdel', 'pkill'
        ]

        name_rep = re.compile(r"""[\\/:*<|>"'#&$^)(]+""")
        if name_rep.search(pjname):
            raise HintException(public.lang("Project Name [{}] Cannot Contain Special Characters".format(name_rep)))
        # 命令行启动跳过端口检测
        flag, msg = (True, "") if stype == "command" and port == "" else self._check_port(port)
        if not flag:
            raise HintException(msg)
        if stype not in ("uwsgi", "gunicorn", "command"):
            raise HintException(public.lang("Run Method Selection [{}] Error".format(stype)))
        if not os.path.isdir(path):
            raise HintException(public.lang("Project Path [{}] Not Found".format(path)))
        if user not in self.get_system_user_list():
            raise HintException(public.lang("Project User [{}] Not Found from system".format(user)))
        if not isinstance(env_list, list):
            raise HintException(public.lang("Environment Variable Format Error: {}".format(env_list)))
        if env_file and not os.path.isfile(env_file):
            raise HintException(public.lang("Environment Variable File Not Found: {}".format(env_file)))

        if initialize:
            for d_cmd in danger_cmd_list:
                if re.search(r"\s+%s\s+" % d_cmd, project_cmd):
                    raise HintException(
                        public.lang("Current initialization operation contains dangerous command:{}".format(d_cmd))
                    )

        is_pypy = False
        if "is_pypy" in get:
            is_pypy = get.is_pypy in ("1", "true", 1, True, "True")

        em = EnvironmentManager()
        env = em.get_env_py_path(python_bin)
        if not env:
            raise HintException(public.lang("Python Environment Not Found"))
        # 拦截直接使用面板环境pyenv的情况, 以防破坏面板环境
        if env.bin_path and env.bin_path.startswith(f"{self._panel_path}/pyenv"):
            raise HintException(public.lang(
                "Please Create a Virtual Environment Based on The Panel Environment and Use It to Create Project"
            ))
        auto_run = False
        if "auto_run" in get:
            auto_run = get.auto_run in ("1", "true", 1, True, "True")

        if "logpath" not in get or not get.logpath.strip():
            logpath = os.path.join(self._project_logs, pjname)
        else:
            logpath = get.logpath.strip()
            if not os.path.exists(logpath):
                logpath = os.path.join(self._project_logs, pjname)

        # 对run_file 进行检查
        if stype == "command":
            if not project_cmd:
                raise HintException(public.lang("Missing Required Startup Command"))
        else:
            if not xsgi or not rfile or not call_app:
                raise HintException(public.lang("Missing Required Server Hosting Startup Parameters"))

        if requirement_path and not os.path.isfile(requirement_path):
            raise HintException(public.lang("Requirement File Not Found: {}".format(requirement_path)))

        if self._check_project_exist(pjname):
            raise HintException(public.lang("Project [{}] Already Exists".format(pjname)))
        if self._check_project_path_exist(path):
            raise HintException(public.lang("The Path [{}] Already Exists Other Project".format(path)))

        return {
            "pjname": pjname,
            "port": port,
            "stype": stype,
            "path": path,
            "user": user,
            "requirement_path": requirement_path,
            "env_list": env_list,
            "env_file": env_file,
            "framework": framework,
            "vpath": os.path.dirname(os.path.dirname(env.bin_path)),
            "version": env.version,
            "python_bin": env.bin_path,
            "project_cmd": project_cmd,
            "xsgi": xsgi,
            "rfile": rfile,
            "call_app": call_app,
            "auto_run": auto_run,
            "logpath": logpath,
            "is_pypy": is_pypy,
            "initialize": initialize,
        }

    def CreateProject(self, get):
        """创建Python项目
        @author baozi <202-02-22>
        @param:
            get  ( dict ):  请求信息
        @return  test : 创建情况
        """
        # 检查输入参数
        values = self.__check_args(get)
        public.set_module_logs("create_python_project", "create")
        # 检查服务器部署的可行性
        msg = self.__check_feasibility(values)
        if msg:
            return public.fail_v2(msg)

        # 默认不开启映射，不绑定外网
        values["domains"], values["bind_extranet"] = [], 0
        # 默认进程数与线程数
        values["processes"], values["threads"] = 4, 2
        # 默认日志等级info
        values["loglevel"] = "info"
        # 默认uwsgi使用http
        values['is_http'] = "is_http"

        p_data = {
            "name": values["pjname"],
            "path": values["path"],
            "ps": values["pjname"],
            "status": 1,
            'type_id': 0,
            "project_type": "Python",
            "addtime": public.getDate(),
            "project_config": json.dumps(values)
        }
        res = public.M("sites").insert(p_data)
        if isinstance(res, str) and res.startswith("error"):
            return public.fail_v2(public.lang("Project Record Failed, Please Contact Official"))

        self.run_simple_prep_env(res, values)
        time.sleep(0.5)
        public.WriteLog(self._log_name, "Create Python Project [{}]".format(values["pjname"]))
        get.release_firewall = True
        flag, tip = self._release_firewall(get)
        tip = "" if flag else "<br>" + tip
        return public.success_v2(public.lang("Create Project Successfully" + tip))

    def __prepare_start_conf(self, values, force=False, pyenv: Optional[PythonEnvironment] = None):
        """准备启动的配置文件, python运行不需要, uwsgi和gunicorn需要
        @author baozi <202-02-22>
        @param:
            values  ( dict ):  用户传入的参数
        @return   :
        """
        # 加入默认配置
        if pyenv is None:
            pyenv = EnvironmentManager().get_env_py_path(values.get("python_bin", values.get("vpath")))
        if not pyenv:
            return
        values["user"] = values['user'] if 'user' in values else 'root'
        values["processes"] = values['processes'] if 'processes' in values else 4
        values["threads"] = values['threads'] if 'threads' in values else 2
        if not os.path.isdir(values['logpath']):
            os.makedirs(values['logpath'], mode=0o777)

        env_file = f"{self._env_path}/{values["pjname"]}.env"
        self._build_env_file(env_file, values)

        self.__prepare_uwsgi_start_conf(values, pyenv, force)
        self.__prepare_gunicorn_start_conf(values, pyenv, force)
        if "project_cmd" not in values:
            values["project_cmd"] = ''
        self.__prepare_cmd_start_conf(values, pyenv, force)
        self.__prepare_python_start_conf(values, pyenv, force)

    @staticmethod
    def _get_callable_app(project_config: dict):
        callable_app = "application" if project_config['framework'] == "django" else "app"
        data = public.read_rare_charset_file(project_config.get("rfile", ""))
        if isinstance(data, str):
            re_list = (
                re.compile(r"\s*(?P<app>\w+)\s*=\s*(make|create)_?app(lication)?", re.M | re.I),
                re.compile(r"\s*(?P<app>app|application)\s*=\s*", re.M | re.I),
                re.compile(r"\s*(?P<app>\w+)\s*=\s*(Flask\(|flask\.Flask\()", re.M | re.I),
                re.compile(r"\s*(?P<app>\w+)\s*=\s*(Sanic\(|sanic\.Sanic\()", re.M | re.I),
                re.compile(r"\s*(?P<app>\w+)\s*=\s*get_wsgi_application\(\)", re.M | re.I),
                re.compile(r"\s*(?P<app>\w+)\s*=\s*(FastAPI\(|fastapi\.FastAPI\()", re.M | re.I),
                re.compile(r"\s*(?P<app>\w+)\s*=\s*.*web\.Application\(", re.M | re.I),
                re.compile(r"\s*(?P<app>server|service|web|webserver|web_server|http_server|httpserver)\s*=\s*",
                           re.M | re.I),
            )
            for i in re_list:
                res = i.search(data)
                if not res:
                    continue
                callable_app = res.group("app")
                break

        return callable_app

    def __prepare_uwsgi_start_conf(self, values, pyenv: PythonEnvironment, force=False):
        # uwsgi
        if not values["rfile"]:
            return
        uwsgi_file = "{}/uwsgi.ini".format(values['path'])
        cmd_file = "{}/{}_uwsgi.sh".format(self._script_path, values["pjname"])
        if not force and os.path.exists(uwsgi_file) and os.path.exists(cmd_file):
            return

        template_file = "{}/template/python_project/uwsgi_conf.conf".format(self._vhost_path)
        values["is_http"] = values["is_http"] if "is_http" in values else True
        env_file = "{}/{}.env".format(self._env_path, values["pjname"])

        if "call_app" not in values or not values["call_app"]:
            callable_app = self._get_callable_app(values)
        else:
            callable_app = values["call_app"]
        if not os.path.exists(uwsgi_file):
            config_body: str = public.readFile(template_file)
            config_body = config_body.format(
                path=values["path"],
                rfile=values["rfile"],
                processes=values["processes"],
                threads=values["threads"],
                is_http="" if values["is_http"] else "#",
                is_socket="#" if values["is_http"] else "",
                port=values["port"],
                user=values["user"],
                logpath=values['logpath'],
                app=callable_app,
            )
            public.writeFile(uwsgi_file, config_body)
        pid_file = "{}/{}.pid".format(self._pid_path, values["pjname"])

        _sh = "%s -d --ini %s/uwsgi.ini --pidfile='%s'" % (pyenv.uwsgi_bin() or "uwsgi", values['path'], pid_file)
        values["start_sh"] = _sh

        self._create_cmd_file(
            cmd_file=cmd_file,
            v_ptah_bin=os.path.dirname(self._get_vp_python(values['vpath'])),
            project_path=values["path"],
            command=_sh,
            log_file="{}/uwsgi.log".format(values["logpath"]),
            pid_file="/dev/null",
            env_file=env_file,
            activate_sh=pyenv.activate_shell(),
            evn_name=public.Md5(values["pjname"]),
        )

    def __prepare_gunicorn_start_conf(self, values, pyenv: PythonEnvironment, force=False):
        # gunicorn
        if not values["rfile"]:
            return
        gconf_file = "{}/gunicorn_conf.py".format(values['path'])
        cmd_file = "{}/{}_gunicorn.sh".format(self._script_path, values["pjname"])
        if not force and os.path.exists(gconf_file) and os.path.exists(cmd_file):
            return

        worker_class = "sync" if values["xsgi"] == "wsgi" else 'uvicorn.workers.UvicornWorker'
        template_file = "{}/template/python_project/gunicorn_conf.conf".format(self._vhost_path)
        values["loglevel"] = values["loglevel"] if "loglevel" in values else "info"
        if not os.path.exists(gconf_file):
            config_body: str = public.readFile(template_file)
            config_body = config_body.format(
                path=values["path"],
                processes=values["processes"],
                threads=values["threads"],
                user=values["user"],
                worker_class=worker_class,
                port=values["port"],
                logpath=values['logpath'],
                loglevel=values["loglevel"]
            )
            public.writeFile(gconf_file, config_body)

        error_log = '{}/gunicorn_error.log'.format(values["logpath"])
        access_log = '{}/gunicorn_acess.log'.format(values["logpath"])
        if not os.path.isfile(error_log):
            public.writeFile(error_log, "")
        if not os.path.isfile(access_log):
            public.writeFile(access_log, "")
        self._pass_dir_for_user(values["logpath"], values["user"])
        public.set_own(error_log, values["user"])
        public.set_own(access_log, values["user"])
        _app = values['rfile'].replace((values['path'] + "/"), "")[:-3]
        _app = _app.replace("/", ".")
        if "call_app" not in values or not values["call_app"]:
            callable_app = self._get_callable_app(values)
        else:
            callable_app = values["call_app"]
        _app += ":" + callable_app
        _sh = "%s -c %s/gunicorn_conf.py %s " % (pyenv.gunicorn_bin() or "gunicorn", values['path'], _app)

        values["start_sh"] = _sh
        pid_file = "{}/{}.pid".format(self._pid_path, values["pjname"])
        env_file = "{}/{}.env".format(self._env_path, values["pjname"])
        self._create_cmd_file(
            cmd_file=cmd_file,
            v_ptah_bin=os.path.dirname(self._get_vp_python(values['vpath'])),
            project_path=values["path"],
            command=_sh,
            log_file=error_log,
            pid_file=pid_file,
            env_file=env_file,
            activate_sh=pyenv.activate_shell(),
            evn_name=public.Md5(values["pjname"]),
        )

    def __prepare_cmd_start_conf(self, values, pyenv: PythonEnvironment, force=False):
        if "project_cmd" not in values or not values["project_cmd"]:
            return
        cmd_file = "{}/{}_cmd.sh".format(self._script_path, values["pjname"])
        if not force and os.path.exists(cmd_file):
            return
        pid_file = "{}/{}.pid".format(self._pid_path, values["pjname"])
        log_file = values['logpath'] + "/error.log"
        env_file = "{}/{}.env".format(self._env_path, values["pjname"])

        self._create_cmd_file(
            cmd_file=cmd_file,
            v_ptah_bin=os.path.dirname(self._get_vp_python(values['vpath'])),
            project_path=values["path"],
            command=values["project_cmd"],
            log_file=log_file,
            pid_file=pid_file,
            env_file=env_file,
            activate_sh=pyenv.activate_shell(),
            evn_name=public.Md5(values["pjname"]),
        )

        values["start_sh"] = values["project_cmd"]

    def __prepare_python_start_conf(self, values, pyenv: PythonEnvironment, force=False):
        if not values["rfile"]:
            return
        cmd_file = "{}/{}_python.sh".format(self._script_path, values["pjname"])
        if not force and os.path.exists(cmd_file):
            return
        pid_file = "{}/{}.pid".format(self._pid_path, values["pjname"])
        env_file = "{}/{}.env".format(self._env_path, values["pjname"])
        self._build_env_file(env_file, values)

        log_file = (values['logpath'] + "/error.log").replace("//", "/")
        v_python = self._get_vp_python(values['vpath'])
        command = "{vpath} -u {run_file} {parm} ".format(
            vpath=v_python,
            run_file=values['rfile'],
            parm=values.get("parm", "")
        )
        self._create_cmd_file(
            cmd_file=cmd_file,
            v_ptah_bin=os.path.dirname(v_python),
            project_path=values["path"],
            command=command,
            log_file=log_file,
            pid_file=pid_file,
            env_file=env_file,
            activate_sh=pyenv.activate_shell(),
            evn_name=public.Md5(values["pjname"]),
        )

        values["start_sh"] = command

    @staticmethod
    def _build_env_file(env_file: str, values: dict):
        env_body_list = []
        if "env_file" in values and values["env_file"] and os.path.isfile(values["env_file"]):
            env_body_list.append(f"source {values["env_file"]}\n")

        if "env_list" in values:
            for tmp in values["env_list"]:
                if "k" not in tmp or "v" not in tmp:
                    continue
                env_body_list.append(f"export {tmp["k"]}={tmp["v"]}\n")

        public.writeFile(env_file, "".join(env_body_list))

    @staticmethod
    def _create_cmd_file(cmd_file, v_ptah_bin, project_path, command, log_file, pid_file, env_file, activate_sh='',
                         evn_name=""):
        """command, gunicorn, python(wtf), uwsgi"""

        if "nohup" in command:
            command = command.replace("nohup", "").strip()

        start_cmd = '''#!/bin/bash
PATH={v_ptah_bin}:{project_path}:/bin:/sbin:/usr/bin:/usr/sbin:/usr/local/bin:/usr/local/sbin:~/bin
export PATH
export BT_PYTHON_SERVICE_SID={sid}
{activate_sh}
source {env_file}
cd {project_path}
nohup {command} &>> {log_file} &
echo $! > {pid_file}'''.format(
            v_ptah_bin=v_ptah_bin,
            activate_sh=activate_sh,
            project_path=project_path,
            command=command,
            log_file=log_file,
            pid_file=pid_file,
            env_file=env_file,
            sid=evn_name,
        )
        public.writeFile(cmd_file, start_cmd)

    def _get_cmd_file(self, project_conf):
        cmd_file_map = {
            "python": "_python.sh",
            "uwsgi": "_uwsgi.sh",
            "gunicorn": "_gunicorn.sh",
            "command": "_cmd.sh",
        }
        cmd_file = f"{self._script_path}/{project_conf["pjname"]}{cmd_file_map[project_conf["stype"]]}"
        if project_conf["stype"] == "uwsgi":
            data = public.readFile(cmd_file)
            if data and "--pidfile" not in data:
                os.remove(cmd_file)
        return cmd_file

    @staticmethod
    def get_project_pids(pid):
        """
            @name 获取项目进程pid列表
            @author baozi<2021-08-10>
            @param pid: int 主进程pid
            @return list
        """
        try:
            p = psutil.Process(pid)
            return [p.pid] + [c.pid for c in p.children(recursive=True) if p.status() != psutil.STATUS_ZOMBIE]
        except:
            return []

    def get_project_run_state(self, project_name) -> list:
        """
            @name 获取项目运行状态
            @author hwliang<2021-08-12>
            @param project_name<string> 项目名称
            @return list
        """
        pid_file = "{}/{}.pid".format(self._pid_path, project_name)
        project_data = self.get_project_find(project_name)
        if not project_data:
            return []

        def _read_pid() -> int:
            pid_str = public.readFile(pid_file)
            if not isinstance(pid_str, str):
                return 0
            try:
                pid = int(pid_str.strip())
            except Exception:
                return 0
            return pid if pid > 0 else 0

        def _is_alive(pid: int) -> bool:
            if pid <= 0:
                return False
            if not psutil.pid_exists(pid):
                return False
            try:
                p = psutil.Process(pid)
                return p.is_running() and p.status() != psutil.STATUS_ZOMBIE
            except Exception:
                return False

        pid = _read_pid()
        if not _is_alive(pid):
            # find with SID hash value from os env, find with cmd
            pid = self._get_pid_by_env_name(project_data) or self._get_pid_by_command(project_data) or 0
            if not _is_alive(pid):
                return []
            try:  # update pid file
                public.writeFile(pid_file, str(pid))
            except Exception:
                pass

        pids = self.get_project_pids(pid=pid)
        return pids or []

    @staticmethod
    def other_service_pids(project_data: dict) -> Set[int]:
        from mod.project.python.serviceMod import ServiceManager
        s_mgr = ServiceManager(project_data["name"], project_data["project_config"])
        return s_mgr.other_service_pids()

    def _get_pid_by_command(self, project_data: dict) -> Optional[int]:
        project_config = project_data["project_config"]
        v_path = project_config['vpath']
        runfile = project_config['rfile']
        path = project_config['path']
        stype = project_config["stype"]
        pids = []
        try:
            if stype == "python":
                for i in psutil.process_iter(['pid', 'exe', 'cmdline']):
                    try:
                        if i.status() == "zombie":
                            continue
                        if v_path in i.exe() and runfile in " ".join(i.cmdline()):
                            pids.append(i.pid)
                    except:
                        pass

            elif stype in ("uwsgi", "gunicorn"):
                for i in psutil.process_iter(['pid', 'exe', 'cmdline']):
                    try:
                        if i.status() == "zombie":
                            continue
                        if v_path in i.exe() and stype in i.exe() and \
                                path in " ".join(i.cmdline()) and stype in " ".join(i.cmdline()):
                            pids.append(i.pid)
                    except:
                        pass
            elif stype == "command":
                for i in psutil.process_iter(['pid', 'exe']):
                    try:
                        if i.status() == "zombie":
                            continue
                        if v_path in i.exe() and i.cwd().startswith(path.rstrip("/")):
                            pids.append(i.pid)
                    except:
                        pass
            else:
                return None
        except:
            return None

        running_pid = []
        other_service_pids = self.other_service_pids(project_data)
        for pid in pids:
            if pid in psutil.pids() and pid not in other_service_pids:
                running_pid.append(pid)

        if len(running_pid) == 1:
            pid_file = "{}/{}.pid".format(self._pid_path, project_data["name"])
            public.writeFile(pid_file, str(running_pid[0]))
            return running_pid[0]

        main_pid = []
        for pid in running_pid:
            try:
                p = psutil.Process(pid)
                if p.ppid() not in running_pid:
                    main_pid.append(pid)
            except:
                pass

        if len(main_pid) == 1:
            pid_file = "{}/{}.pid".format(self._pid_path, project_data["name"])
            public.writeFile(pid_file, str(main_pid[0]))
            return main_pid[0]

        return None

    def _get_pid_by_env_name(self, project_data: dict):
        """通过sid hash值找pid"""
        env_key = "BT_PYTHON_SERVICE_SID={}".format(public.Md5(project_data["name"]))
        pid_file = "{}/{}.pid".format(self._pid_path, project_data["name"])
        target_list = []
        for p in psutil.pids():
            try:
                data: str = public.readFile("/proc/{}/environ".format(p))
                if data.rfind(env_key) != -1:
                    target_list.append(p)
            except:
                continue

        main_pid = 0
        for i in target_list:
            try:
                p = psutil.Process(i)
                if p.ppid() not in target_list:
                    main_pid = i
            except:
                continue
        if main_pid:
            public.writeFile(pid_file, str(main_pid))
            return main_pid

        return None

    def __start_project(self, project_conf, reconstruction=False):
        """启动 项目
        @author baozi <202-02-22>
        @param:
            project_conf  ( dict ):  站点配置
            reconstruction  ( bool ):  是否重写启动指令
        @return  bool : 是否启动成功
        """
        if self.get_project_run_state(project_name=project_conf["pjname"]):
            return True
        uwsgi_file = "{}/uwsgi.ini".format(project_conf['path'])
        gconf_file = "{}/gunicorn_conf.py".format(project_conf['path'])
        cmd_file = self._get_cmd_file(project_conf)
        # reconstruction?
        if not os.path.exists(cmd_file) or not os.path.exists(uwsgi_file) or not os.path.exists(gconf_file):
            self.__prepare_start_conf(project_conf)
        pid_file = f"{self._pid_path}/{project_conf["pjname"]}.pid"
        if os.path.exists(pid_file):
            os.remove(pid_file)
        run_user = project_conf["user"]
        public.ExecShell("chown -R {}:{} {}".format(run_user, run_user, project_conf["path"]))
        public.set_mode(cmd_file, 755)
        public.set_mode(self._pid_path, 777)
        public.set_own(cmd_file, run_user)

        # 处理日志文件
        log_file = self._project_logfile(project_conf)
        if not os.path.exists(log_file):
            public.ExecShell("touch  {}".format(log_file))
        public.ExecShell("chown  {}:{} {}".format(run_user, run_user, log_file))
        self._pass_dir_for_user(os.path.dirname(log_file), run_user)  # 让进程至少可以访问到日志文件
        self._pass_dir_for_user(os.path.dirname(project_conf["path"]), run_user)  # 让进程至少可以访问到程序文件

        # 执行脚本文件
        if project_conf["stype"] in ("uwsgi", "gunicorn"):
            public.ExecShell("{}".format(cmd_file), env=os.environ.copy())
        else:
            public.ExecShell("{}".format(cmd_file), user=run_user, env=os.environ.copy())
        time.sleep(1)

        if self._pids:
            self._pids = None  # 清理缓存重新检查
        if self.get_project_run_state(project_name=project_conf["pjname"]):
            return True
        return False

    def only_start_main_project(self, project_name):
        """启动项目api接口
        @author baozi <202-02-22>
        @param:
            get  ( dict ):  请求信息，包含name
        @return   msg: 启动情况信息
        """
        project_conf = self._get_project_conf(name_id=project_name)
        if not project_conf:
            raise HintException(public.lang("No Such Project, Please Try to Refresh the Page"))
        if self.prep_status(project_conf) == "running":
            raise HintException(
                public.lang("Project Environment Installation in Progress.....<br>Please Do Not Operate")
            )
        if "port" in project_conf and project_conf["port"]:
            flag, msg = self._check_port(project_conf["port"])
            if not flag:
                return public.fail_v2(msg)
        if not os.path.exists(project_conf["path"]):
            return public.fail_v2(public.lang("Project File Missing, Unable to Start"))
        flag = self.__start_project(project_conf)
        pdata = {
            "project_config": json.dumps(project_conf)
        }
        public.M('sites').where('name=?', (project_name,)).update(pdata)
        if flag:
            self.start_by_user(self.get_project_find(project_name)["id"])
            return public.success_v2(public.lang("Project Started Successfully"))
        else:
            return public.fail_v2(public.lang("Project Start Failed"))

    def StartProject(self, get):
        project_name = None
        if hasattr(get, "name"):
            project_name = get.name.strip()
        if hasattr(get, "project_name"):
            project_name = get.project_name.strip()
        if not project_name:
            return public.fail_v2("'project_name' is empty")

        project_find = self.get_project_find(project_name)
        # 2024.4.3 修复项目过期时间判断不对
        mEdate = time.strftime('%Y-%m-%d', time.localtime())
        if project_find['edate'] != "0000-00-00" and project_find['edate'] < mEdate:
            return public.fail_v2("Current project has expired, please reset the project expiration date")

        from mod.project.python.serviceMod import ServiceManager

        s_mgr = ServiceManager.new_mgr(project_name)
        if isinstance(s_mgr, str):
            return public.fail_v2(s_mgr)

        s_mgr.start_project()
        return public.success_v2("Start command has been executed, please check the log")

    def start_project(self, get):
        get.name = get.project_name
        return self.StartProject(get)

    def __stop_project(self, project_conf, reconstruction=False):
        """停止项目
        @author baozi <202-02-22>
        @param:
            project_conf  ( dict ):  站点配置
        @return  bool : 是否停止成功
        """
        project_name = project_conf["pjname"]
        if not self.get_project_run_state(project_name):
            return True
        pid_file = "{}/{}.pid".format(self._pid_path, project_conf["pjname"])
        pid = int(public.readFile(pid_file))
        pids = self.get_project_pids(pid=pid)
        if not pids:
            return True
        self.kill_pids(pids=pids)
        if os.path.exists(pid_file):
            os.remove(pid_file)
        return True

    @staticmethod
    def kill_pids(pids=None):
        """
            @name 结束进程列表
            @author hwliang<2021-08-10>
            @param pids: string<进程pid列表>
            @return None
        """
        if not pids:
            return
        pids = sorted(pids, reverse=True)
        for i in pids:
            try:
                p = psutil.Process(i)
                p.terminate()
            except:
                pass

        for i in pids:
            try:
                p = psutil.Process(i)
                p.kill()
            except:
                pass
        return

    def StopProject(self, get):
        project_name = None
        if hasattr(get, "name"):
            project_name = get.name.strip()
        if hasattr(get, "project_name"):
            project_name = get.project_name.strip()
        if not project_name:
            return public.fail_v2(public.lang("Please Select the Project to Stop"))
        project_find = self.get_project_find(project_name)
        # 2024.4.3 修复项目过期时间判断不对
        mEdate = time.strftime('%Y-%m-%d', time.localtime())
        if project_find['edate'] != "0000-00-00" and project_find['edate'] < mEdate:
            return public.fail_v2(public.lang('Current project has expired, please reset the project expiration date'))

        from mod.project.python.serviceMod import ServiceManager

        s_mgr = ServiceManager.new_mgr(project_name)
        if isinstance(s_mgr, str):
            return public.fail_v2(s_mgr)

        s_mgr.stop_project()
        return public.success_v2(public.lang("Stop command has been executed, please check the log"))

    def only_stop_main_project(self, project_name):
        """停止项目的api接口
        @author baozi <202-02-22>
        @param:
            get  ( dict ):  请求信息
        @return  msg : 返回停止操作的结果
        """
        project_find = self.get_project_find(project_name)
        project_conf = project_find["project_config"]
        if self.prep_status(project_conf) == "running":
            return public.fail_v2(
                public.lang("Project Environment Installation in Progress.....<br>Please Do Not Operate"))
        res = self.__stop_project(project_conf)
        pdata = {
            "project_config": json.dumps(project_conf)
        }
        public.M('sites').where('name=?', (project_name,)).update(pdata)
        if res:
            self.stop_by_user(self.get_project_find(project_name)["id"])
            return public.success_v2(public.lang("Project Stopped Successfully"))
        else:
            return public.fail_v2(public.lang("Project Stop Failed"))

    def restart_project(self, get):
        get.name = get.project_name
        return self.RestartProject(get)

    def RestartProject(self, get):
        if hasattr(get, "name"):
            name = get.name.strip()
        elif hasattr(get, "project_name"):
            name = get.project_name.strip()
        else:
            return public.fail_v2(public.lang("Please Select the Project to Restart"))
        project_find = self.get_project_find(name)
        # 2024.4.3 修复项目过期时间判断不对
        mEdate = time.strftime('%Y-%m-%d', time.localtime())
        if project_find['edate'] != "0000-00-00" and project_find['edate'] < mEdate:
            return public.fail_v2(public.lang('Current project has expired, please reset the project expiration date'))
        conf = project_find["project_config"]
        if self.prep_status(conf) == "running":
            raise HintException(
                public.lang("Project Environment Installation in Progress.....<br>Please Do Not Operate")
            )
        from mod.project.python.serviceMod import ServiceManager
        s_mgr = ServiceManager.new_mgr(name)
        if isinstance(s_mgr, str):
            return public.fail_v2(s_mgr)
        s_mgr.stop_project()
        s_mgr.start_project()
        return public.success_v2(public.lang("Project Restart command has been executed, please check the log"))

    def stop_project(self, get):
        get.name = get.project_name
        return self.StopProject(get)

    def remove_project(self, get):
        get.name = get.project_name
        get.remove_env = True
        return self.RemoveProject(get)

    def RemoveProject(self, get):
        """删除项目接口
        @author baozi <202-02-22>
        @param:
            get  ( dict ):  请求信息对象
        @return  msg : 是否删除成功
        """
        name = get.name.strip()
        project = self.get_project_find(name)
        conf = project.get("project_config")
        if not conf:
            return public.fail_v2(public.lang("Project's project_config Not Found"))
        if self.prep_status(conf) == "running":
            return public.fail_v2(
                public.lang("Project Environment Installation in Progress.....<br>Please Do Not Operate")
            )
        pid = self.get_project_run_state(name)
        if pid:
            self.StopProject(get)

        self._del_crontab_by_name(self._split_cron_name_temp.format(name))
        self._del_crontab_by_name(self._restart_cron_name.format(name))
        self.remove_redirect_by_project_name(get.name)
        self.clear_config(get.name)

        logfile = self._logs_path + "/%s.log" % conf["pjname"]
        # if hasattr(get, "remove_env") and get.remove_env not in (1, "1", "true", True):
        #     if os.path.basename(conf["vpath"]).find(project["name"]) == -1:
        #         try:
        #             shutil.move(conf["vpath"], self._pyv_path + '/' + project["name"] + "_venv")
        #         except:
        #             pass
        # elif os.path.exists(conf["vpath"]) and self._check_venv_path(conf["vpath"], project["id"]):
        #     shutil.rmtree(conf["vpath"])

        try:
            em = EnvironmentManager()
            python_bin = conf.get("python_bin", "")
            if not python_bin:
                python_bin_data = em.get_env_py_path(conf["vpath"])
                if python_bin_data:
                    python_bin = python_bin_data.bin_path
            if python_bin:
                em.multi_remove_env(python_bin)
        except Exception:
            pass

        if os.path.exists(logfile):
            os.remove(logfile)
        if os.path.exists(conf["path"] + "/uwsgi.ini"):
            os.remove(conf["path"] + "/uwsgi.ini")
        if os.path.exists(conf["path"] + "/gunicorn_conf.py"):
            os.remove(conf["path"] + "/gunicorn_conf.py")

        for suffix in ("_python.sh", "_uwsgi.sh", "_gunicorn.sh", "_cmd.sh"):
            cmd_file = os.path.join("{}/{}{}".format(self._script_path, conf["pjname"], suffix))
            if os.path.exists(cmd_file):
                os.remove(cmd_file)
        from mod.base.web_conf import remove_sites_service_config
        remove_sites_service_config(get.name, "python_")
        public.M('domain').where('pid=?', (project['id'],)).delete()
        public.M('sites').where('name=?', (name,)).delete()
        public.WriteLog(self._log_name, 'Delete Python Project [{}]'.format(name))
        return public.success_v2(public.lang("Project Deleted Successfully"))

    @staticmethod
    def _check_venv_path(v_path: str, project_id) -> bool:
        site_list = public.M('sites').where('project_type=?', ('Python',)).select()
        if not isinstance(site_list, list):
            return True
        for site in site_list:
            conf = json.loads(site["project_config"])
            if conf["vpath"] == v_path and site["id"] != project_id:
                return False
        return True

    @staticmethod
    def xsssec(text):
        return text.replace('<', '&lt;').replace('>', '&gt;')

    @staticmethod
    def last_lines(filename, lines=1):
        block_size = 3145928
        block = ''
        nl_count = 0
        start = 0
        fsock = open(filename, 'r')
        try:
            fsock.seek(0, 2)
            curpos = fsock.tell()
            while curpos > 0:
                curpos -= (block_size + len(block))
                if curpos < 0: curpos = 0
                fsock.seek(curpos)
                try:
                    block = fsock.read()
                except:
                    continue
                nl_count = block.count('\n')
                if nl_count >= lines: break
            for n in range(nl_count - lines + 1):
                start = block.find('\n', start) + 1
        finally:
            fsock.close()
        return block[start:]

    @staticmethod
    def _project_logfile(project_conf):
        if project_conf["stype"] in ("python", "command"):
            log_file = project_conf["logpath"] + "/error.log"
        elif project_conf["stype"] == "gunicorn":
            log_file = project_conf["logpath"] + "/gunicorn_error.log"
        else:
            log_file = project_conf["logpath"] + "/uwsgi.log"
        return log_file

    def GetProjectLog(self, get):
        """获取项目日志api
        @author baozi <202-02-22>
        @param:
            get  ( dict ):  请求信息，需要包含项目名称
        @return  msg : 日志信息
        """
        project_conf = self._get_project_conf(get.name.strip())
        if not project_conf:
            raise HintException(public.lang("Project Not Found"))
        log_file = self._project_logfile(project_conf)
        if not os.path.exists(log_file):
            raise HintException(public.lang("Log File Not Found"))
        log_file_size = os.path.getsize(log_file)
        if log_file_size > 3145928:
            log_data = self.last_lines(log_file, 3000)
        else:
            log_data = public.GetNumLines(log_file, 3000)
        return public.success_v2({
            "path": log_file,
            "data": self.xsssec(log_data),
            "size": public.to_size(log_file_size)
        })

    def GetProjectList(self, get):
        """获取项目列表（重构版：支持流量排序）
        @author baozi <202-02-22>
        @modified Gemini <2026-02-26>
        """
        if not self.need_update_project("mod"):
            self.update_all_project()

        p = int(get.get('p', 1))
        limit = int(get.get('limit', 20))
        callback = get.get('callback', '')
        order_str = get.get('order', 'id desc')
        re_order = get.get('re_order', '')
        search_word = get.get('search', '').strip() if 'search' in get else ''

        where_str = "project_type=?"
        where_args = ["Python"]

        if "type_id" in get and get.type_id:
            try:
                where_str += " AND type_id=?"
                where_args.append(int(get.type_id))
            except:
                pass

        if search_word:
            search_pattern = "%{}%".format(search_word)
            where_str += " AND (name LIKE ? OR ps LIKE ?)"
            where_args.extend([search_pattern, search_pattern])

        sql = public.M('sites').where(where_str, tuple(where_args))

        all_data = sql.order(order_str).select()

        if isinstance(all_data, str) and all_data.startswith("error"):
            raise public.PanelError("db query error:" + all_data)
        if not all_data:
            return public.success_v2({'data': [], 'page': ''})

        re_data = None
        if re_order:
            import data_v2
            res = data_v2.data().get_site_request(public.to_dict_obj({'site_type': 'Python'}))
            if res.get('status') == 0:
                re_data = res.get('message')

        for item in all_data:
            item["ssl"] = self.get_ssl_end_date(item["name"])
            self._get_project_state(item)

            item['re_total'] = 0
            if re_data and item['name'] in re_data:
                item['re_total'] = re_data[item['name']]['total']['request']

        if re_order:
            is_reverse = (re_order == 'desc')
            all_data = sorted(all_data, key=lambda x: x.get('re_total', 0), reverse=is_reverse)

        count = len(all_data)
        start = (p - 1) * limit
        end = start + limit
        paged_data = all_data[start:end]

        import page
        pg = page.Page()
        info = {
            'count': count,
            'row': limit,
            'p': p,
            'return_js': callback,
            'uri': ''
        }
        # 尝试获取 URI 以维持分页链接
        try:
            from flask import request
            info['uri'] = public.url_encode(request.full_path)
        except:
            pass

        return_data = {
            'data': paged_data,
            'page': pg.GetPage(info)
        }

        return public.success_v2(return_data)

    def _get_project_state(self, project_info):
        """获取项目详情信息
        @author baozi <202-02-22>
        @param:
            project_info  ( dict ):  项目详情
        @return   : 项目详情的列表
        """
        if not isinstance(project_info['project_config'], dict):
            project_info['project_config'] = json.loads(project_info['project_config'])

        pyenv = self.environment_manager.get_env_py_path(
            project_info['project_config'].get("python_bin", project_info['project_config']["vpath"])
        )
        if pyenv:
            project_info["shell_active"] = self.get_active_shell(project_info["name"], pyenv)
            project_info["pyenv_data"] = pyenv.to_dict()
        else:
            project_info["shell_active"] = ""
            project_info["pyenv_data"] = {}

        project_info["project_config"]["prep_status"] = self.prep_status(project_info['project_config'])
        if project_info["project_config"]["stype"] == "python":
            project_info["config_file"] = None
        elif project_info["project_config"]["stype"] == "uwsgi":
            project_info["config_file"] = '{}/uwsgi.ini'.format(project_info["project_config"]["path"])
        else:
            project_info["config_file"] = '{}/gunicorn_conf.py'.format(project_info["project_config"]["path"])
        pids = self.get_project_run_state(project_info["name"])
        if not pids:
            project_info['run'], project_info['status'], project_info["project_config"]["status"] = False, 0, 0
            project_info["listen"] = []
        else:
            project_info['run'], project_info['status'], project_info["project_config"]["status"] = True, 1, 1
            mem, cpu = self.get_mem_and_cpu(pids)
            project_info.update({"cpu": cpu, "mem": mem})
            project_info["listen"] = self._list_listen(pids)

        project_info["pids"] = pids
        for i in ("start_sh", "stop_sh", "check_sh"):
            if i in project_info["project_config"]:
                project_info["project_config"].pop(i)

    def get_active_shell(self, p_name, pyenv) -> str:
        pyenv.use2project(p_name)
        os.makedirs(self._activate_path, mode=0o755, exist_ok=True)
        env_file = os.path.join(self._env_path, f"{p_name}.env")
        if pyenv.env_type == "conda":
            script_path = os.path.join(self._activate_path, f"{p_name}.sh")
            public.writeFile(script_path, f"{pyenv.activate_shell()}\nsource {env_file}\n")
            return "source {}".format(shlex.quote(script_path))
        else:
            return (
                f"unset _BT_PROJECT_ENV && "
                f"source {self._panel_path}/script/btpyprojectenv.sh {shlex.quote(p_name)} && "
                f"source {shlex.quote(env_file)}"
            )

    @staticmethod
    def _list_listen(pids: List[int]) -> List[int]:
        res = set()
        if not pids:
            return []
        for i in pids:
            try:
                p = psutil.Process(i)
                for conn in p.net_connections() if hasattr(p, "net_connections") else p.connections():  # noqa
                    if conn.status == "LISTEN":
                        res.add(conn.laddr.port)
            except:
                continue
        return list(res)

    def ChangeProjectConf(self, get):
        """修改项目配置信息
        @author baozi <202-02-22>
        @param:
            get  ( dict ):  用户请求信息 包含name，data
        @return
        """
        if not hasattr(get, "name") or not hasattr(get, "data"):
            return public.fail_v2(public.lang("Invalid Parmas"))
        conf = self._get_project_conf(get.name.strip())
        if not conf:
            return public.fail_v2(public.lang("Project Not Found"))
        if self.prep_status(conf) == "running":
            return public.fail_v2(
                public.lang("Project Environment Installation in Progress.....<br>Please Do Not Operate"))
        if not os.path.exists(conf["path"]):
            return public.fail_v2(public.lang("Project File Missing, Unable to Modify Configuration"))
        if "is_http" in get.data and get.data["is_http"] is False:
            web_server = public.get_webserver()
            if web_server == "apache":
                return public.fail_v2(
                    "uwsgi socket mode is not supported with Apache now.\n"
                    "Please switch to Nginx."
                )
        data: dict = get.data
        change_values = {}
        if "call_app" in data and data["call_app"] != conf["call_app"]:
            conf["call_app"] = data["call_app"]
            change_values["call_app"] = data["call_app"]

        try:
            if "env_list" in data and isinstance(data["env_list"], str):
                conf["env_list"] = json.loads(data["env_list"])
        except:
            return public.fail_v2(public.lang("Environment Variable Format Error"))

        if "env_list" in data and isinstance(data["env_list"], list):
            conf["env_list"] = data["env_list"]

        if "env_file" in data and isinstance(data["env_file"], str) and data["env_file"] != conf["env_file"]:
            conf["env_file"] = data["env_file"]

        # stype
        if "stype" in data and data["stype"] != conf["stype"]:
            if data["stype"] not in ("uwsgi", "gunicorn", "python", "command"):
                return public.fail_v2(public.lang("Startup Method Selection Error"))
            else:
                self.__stop_project(conf)
                conf["stype"] = data["stype"]

        if "xsgi" in data and data["xsgi"] != conf["xsgi"]:
            if data["xsgi"] not in ("wsgi", "asgi"):
                return public.fail_v2(public.lang("Network Protocol Selection Error"))
            else:
                conf["xsgi"] = data["stype"]
                change_values["xsgi"] = data["stype"]
        # 检查服务器部署的可行性
        msg = self.__check_feasibility(conf)
        if msg:
            return public.fail_v2(msg)
        # rfile
        if "rfile" in data and data["rfile"] != conf["rfile"]:
            if not data["rfile"].startswith(conf["path"]):
                return public.fail_v2(public.lang("Startup file is not under the project directory"))
            change_values["rfile"] = data["rfile"]
            conf["rfile"] = data["rfile"]
        # parm
        if conf["stype"] == "python":
            conf["parm"] = data["parm"] if "parm" in data else conf["parm"]
        # project_cmd
        if conf["stype"] == "command":
            project_cmd = conf.get("project_cmd", "")
            if "project_cmd" in data:
                project_cmd = data.get("project_cmd", "")
            if not project_cmd:
                return public.fail_v2(public.lang("Project Startup Command Not Found"))
            else:
                conf["project_cmd"] = project_cmd

        # processes and threads
        try:
            if "processes" in data and int(data["processes"]) != int(conf["processes"]):
                change_values["processes"], conf["processes"] = int(data["processes"]), int(data["processes"])
            if "threads" in data and int(data["threads"]) != int(conf["threads"]):
                change_values["threads"], conf["threads"] = int(data["threads"]), int(data["threads"])
        except ValueError:
            return public.fail_v2(public.lang("Thread or Process Number Format Error"))

        # port 某些情况下可以关闭
        if "port" in data and data["port"] != conf["port"] and data["port"]:
            # flag, msg = self._check_port(data["port"])
            # if not flag:
            #     return public.returnMsg(False, msg)
            change_values["port"] = data["port"]
            conf["port"] = data["port"]

        # user
        if "user" in data and data["user"] != conf["user"]:
            if data["user"] in self.get_system_user_list():
                change_values["user"] = data["user"]
                conf["user"] = data["user"]

        # auto_run
        if "auto_run" in data and data["auto_run"] != conf["auto_run"]:
            if isinstance(data["auto_run"], bool):
                conf["auto_run"] = data["auto_run"]

        # logpath
        if "logpath" in data and data["logpath"].strip() and data["logpath"] != conf["logpath"]:
            data["logpath"] = data["logpath"].rstrip("/")
            if os.path.isfile(data["logpath"]):
                return public.fail_v2(public.lang("Log path should not be a file"))
            if '\n' in data["logpath"].strip():
                return public.fail_v2(public.lang("Log path cannot contain new lines"))
            change_values["logpath"] = data["logpath"]
            conf["logpath"] = data["logpath"]

        # 特殊 uwsgi和gunicorn 不需要修改启动的脚本，只需要修改配置文件
        if conf["stype"] == "gunicorn":
            if "loglevel" in data and data["loglevel"] != conf["loglevel"]:
                if data["loglevel"] in ("debug", "info", "warning", "error", "critical"):
                    change_values["loglevel"] = data["loglevel"]
                    conf["loglevel"] = data["loglevel"]
            gunc_conf = os.path.join(conf["path"], "gunicorn_conf.py")
            config_file = public.readFile(gunc_conf)
            if config_file:
                config_file = self.__change_gunicorn_config_to_file(change_values, config_file)
                public.writeFile(gunc_conf, config_file)

        if conf["stype"] == "uwsgi":
            if "is_http" in data and isinstance(data["is_http"], bool):
                change_values["is_http"] = data["is_http"]
                conf["is_http"] = data["is_http"]
            if "port" not in change_values:
                change_values["port"] = conf["port"]
            uws_conf = os.path.join(conf["path"], "uwsgi.ini")
            config_file = public.readFile(uws_conf)
            if config_file:
                config_file = self.__change_uwsgi_config_to_file(change_values, config_file)
                public.writeFile(uws_conf, config_file)

        self.__prepare_start_conf(conf, force=True)
        # 尝试重启项目
        error_msg = ''
        if not self.__stop_project(conf, reconstruction=True):
            error_msg = public.lang("modify success, but failed to stop the project when trying to restart")
        if not self.__start_project(conf, reconstruction=True):
            error_msg = public.lang("modify success, but failed to start the project when trying to restart")
        pdata = {
            "project_config": json.dumps(conf)
        }
        public.M('sites').where('name=?', (get.name.strip(),)).update(pdata)
        public.WriteLog(self._log_name, 'Python Project [{}], modify project config'.format(get.name.strip()))

        # 放开防火墙
        if conf.get("is_http") and conf.get("stype") in ("uwsgi", "gunicorn"):
            args = public.dict_obj()
            args.release_firewall = True
            args.name = conf["pjname"]
            args.port = conf["port"]
            self._release_firewall(args)

        # 如果开了映射, 重置映射
        if int(conf.get("bind_extranet", "")) == 1:
            self.clear_config(conf["pjname"])
            self.set_config(conf["pjname"])  # 带web重启
        else:  # 确保重启web
            public.serviceReload()
        if error_msg:
            return public.fail_v2(error_msg)
        return public.success_v2(public.lang("Project Configuration Modified Successfully. Py Project Restart."))

    @staticmethod
    def __change_uwsgi_config_to_file(changes, config_file):
        """修改配置信息
        @author baozi <202-03-08>
        @param:
            changes  ( dict ):  改变的项和值
            config_file  ( string ):  需要改变的文件
        @return
        """
        reps = {
            "rfile": (
                r'wsgi-file\s{0,3}=\s{0,3}[^#\n]*\n', lambda x: f"wsgi-file={x.strip()}\n"
            ),
            "processes": (
                r'processes\s{0,3}=\s{0,3}[\d]*\n', lambda x: f"processes={x.strip()}\n"
            ),
            "threads": (
                r'threads\s{0,3}=\s{0,3}[\d]*\n', lambda x: f"threads={x.strip()}\n"
            ),
            "user": (
                r'uid\s{0,3}=\s{0,3}[^\n]*\ngid\s{0,3}=\s{0,3}[^\n]*\n',
                lambda x: f"uid={x.strip()}\ngid={x.strip()}\n"
            ),
            "logpath": (
                r'daemonize\s{0,3}=\s{0,3}.*\n', lambda x: f"daemonize={x.strip().rstrip('/')}/uwsgi.log\n"
            ),
            "call_app": (
                r'callable\s*=\s{0,3}.*\n', lambda x: f"callable={x.strip()}\n"
            )
        }
        if "logpath" in changes and not os.path.exists(changes['logpath']):
            os.makedirs(changes['logpath'], mode=0o777)
        for k, (rep, fun) in reps.items():
            if k not in changes: continue
            config_file = re.sub(rep, fun(str(changes[k])), config_file)

        if "port" in changes:
            # 被用户关闭了预设的通信方式
            if config_file.find("\n#http") != -1 and config_file.find("\n#socket") != -1:
                pass
            elif "is_http" in changes:
                # 按照预设的方式修改
                rep = r"\n#?http\s{0,3}=\s{0,3}((\d{0,3}\.){3}\d{0,3})?:\d{2,5}\n#?socket\s{0,3}=\s{0,3}((\d{0,3}\.){3}\d{0,3})?:\d{2,5}\n"
                is_http, is_socket = ("", "#") if changes["is_http"] else ("#", "")
                new = f"\n{is_http}http=0.0.0.0:{changes["port"]}\n{is_socket}socket=0.0.0.0:{changes["port"]}\n"
                config_file = re.sub(rep, new, config_file)
            else:
                rpe_h = r'http\s{0,3}=\s{0,3}((\d{0,3}\.){3}\d{0,3})?:\d{2,5}\n'
                config_file = re.sub(rpe_h, f"http=0.0.0.0:{changes['port']}\n", config_file)
                rpe_s = r'socket\s{0,3}=\s{0,3}((\d{0,3}\.){3}\d{0,3})?:\d{2,5}\n'
                config_file = re.sub(rpe_s, f"socket=0.0.0.0:{changes['port']}\n", config_file)

        return config_file

    @staticmethod
    def __prevent_re(test_str):
        # 防正则转译
        re_char = ['$', '(', ')', '*', '+', '.', '[', ']', '{', '}', '?', '^', '|', '\\']
        res = ""
        for i in test_str:
            if i in re_char:
                res += "\\" + i
            else:
                res += i
        return res

    def __get_uwsgi_config_from_file(self, config_file, conf) -> dict:
        """检查并从修改的配置信息获取必要信息
        @author baozi <202-03-08>
        @param:
            changes  ( dict ):  改变的项和值
            config_file  ( string ):  需要改变的文件
        @return
        """
        # 检查必要项目
        check_reps = [
            (
                r"\n\s?chdir\s{0,3}=\s{0,3}" + self.__prevent_re(conf["path"]) + r"[^\n]*\n",
                public.lang("Cannot modify project path")
            ),
            (
                r"\n\s?pidfile\s{0,3}=\s{0,3}" + self.__prevent_re(conf["path"] + "/uwsgi.pid") + r"[^\n]*\n",
                public.lang("Cannot modify project pidfile location")
            ),
            (
                r"\n\s?master\s{0,3}=\s{0,3}true[^\n]*\n",
                public.lang("Cannot modify master process related configuration")
            ),
        ]
        for rep, msg in check_reps:
            if not re.search(rep, config_file):
                raise HintException(msg)

        get_reps = {
            "rfile": (r'\n\s?wsgi-file\s{0,3}=\s{0,3}(?P<target>[^#\n]*)\n', None),
            "module": (r'\n\s?module\s{0,3}=\s{0,3}(?P<target>[^\n/:])*:[^\n]*\n', None),
            "processes": (r'\n\s?processes\s{0,3}=\s{0,3}(?P<target>[\d]*)\n', None),
            "threads": (r'\n\s?threads\s{0,3}=\s{0,3}(?P<target>[\d]*)\n', None),
            "logpath": (
                r'\n\s?daemonize\s{0,3}=\s{0,3}(?P<target>[^\n]*)\n',
                public.lang("Log path configuration not found, please check your modification")
            ),
        }
        changes = {}
        for k, (rep, msg) in get_reps.items():
            res = re.search(rep, config_file)
            if not res and msg:
                raise HintException(msg)
            elif res:
                changes[k] = res.group("target").strip()
        if "module" in changes:
            _rfile = conf["path"] + changes["module"].replace(".", "/") + ".py"
            if os.path.isfile(_rfile):
                changes["rfile"] = _rfile
            changes.pop("module")

        if "logpath" in changes:
            if not os.path.exists(changes['logpath']):
                os.makedirs(changes['logpath'], mode=0o777)
            if "/" in changes["logpath"]:
                _path, filename = changes["logpath"].rsplit("/", 1)
                if filename != "uwsgi.log":
                    raise HintException(public.lang(
                        "For easy log management, please use 'uwsgi.log' as the log file name"
                    ))
                else:
                    changes["logpath"] = _path
            else:
                if changes["logpath"] != "uwsgi.log":
                    raise HintException(public.lang(
                        "For easy log management, please use 'uwsgi.log' as the log file name"
                    ))
                else:
                    changes["logpath"] = conf["path"]

        # port 相关查询
        rep_h = r'\n\s{0,3}http\s{0,3}=\s{0,3}((\d{0,3}\.){3}\d{0,3})?:(?P<target>\d{2,5})[^\n]*\n'
        rep_s = r'\n\s{0,3}socket\s{0,3}=\s{0,3}((\d{0,3}\.){3}\d{0,3})?:(?P<target>\d{2,5})[^\n]*\n'
        res_http = re.search(rep_h, config_file)
        res_socket = re.search(rep_s, config_file)
        if res_http:
            changes["port"] = res_http.group("target").strip()
        elif res_socket:
            changes["port"] = res_socket.group("target").strip()
        else:
            # 被用户关闭了预设的通信方式
            changes["port"] = ""

        return changes

    @staticmethod
    def __change_gunicorn_config_to_file(changes, config_file):
        """修改配置信息
        @author baozi <202-03-08>
        @param:
            changes  ( dict ):  改变的项和值
            config_file  ( string ):  需要改变的文件
        @return
        """
        reps = {
            "processes": (r'workers\s{0,3}=\s{0,3}[^\n]*\n', lambda x: f"workers = {x.strip()}\n"),
            "threads": (r'threads\s{0,3}=\s{0,3}[\d]*\n', lambda x: f"threads = {x.strip()}\n"),
            "user": (r'user\s{0,3}=\s{0,3}[^\n]*\n', lambda x: f"user = '{x.strip()}'\n"),
            "loglevel": (r'loglevel\s{0,3}=\s{0,3}[^\n]*\n', lambda x: f"loglevel = '{x.strip()}'\n"),
            "port": (r'bind\s{0,3}=\s{0,3}[^\n]*\n', lambda x: f"bind = '0.0.0.0:{x.strip()}'\n"),
        }
        for k, (rep, fun) in reps.items():
            if k not in changes: continue
            config_file = re.sub(rep, fun(str(changes[k])), config_file)
        if "logpath" in changes:
            if not os.path.exists(changes['logpath']):
                os.makedirs(changes['logpath'], mode=0o777)
            rpe_accesslog = r'''accesslog\s{0,3}=\s{0,3}['"](/[^/\n]*)*['"]\n'''
            config_file = re.sub(
                rpe_accesslog,
                "accesslog = '{}/gunicorn_acess.log'\n".format(changes['logpath']),
                config_file
            )
            rpe_errorlog = r'''errorlog\s{0,3}=\s{0,3}['"](/[^/\n]*)*['"]\n'''
            config_file = re.sub(
                rpe_errorlog,
                "errorlog = '{}/gunicorn_error.log'\n".format(changes['logpath']),
                config_file
            )

        return config_file

    def __get_gunicorn_config_from_file(self, config_file, conf) -> dict:
        """修改配置信息
        @author baozi <202-03-08>
        @param:
            config_file  ( dict ):  被改变的文件
            conf  ( string ):  项目原配置
        @return
        """
        # 检查必要项目
        check_reps = [
            (
                r'''\n\s?chdir ?= ?["']''' + self.__prevent_re(conf["path"]) + '''["']\n''',
                public.lang("Cannot modify project path")
            ),
            (
                r'''\n\s?pidfile\s{0,3}=\s{0,3}['"]''' + self.__prevent_re(
                    conf["path"] + "/gunicorn.pid") + r'''['"][^\n]*\n''',
                public.lang("Cannot modify project pidfile location")
            ),
            (
                r'''\n\s?worker_class\s{0,3}=\s{0,3}((['"]sync['"])|(['"]uvicorn\.workers\.UvicornWorker['"]))[^\n]*\n''',
                public.lang("Cannot modify worker class related configuration")
            ),
        ]
        for rep, msg in check_reps:
            if not re.findall(rep, config_file):
                raise HintException(msg)

        get_reps = {
            "port": (
                r'''\n\s?bind\s{0,3}=\s{0,3}['"]((\d{0,3}\.){3}\d{0,3})?:(?P<target>\d{2,5})['"][^\n]*\n''',
                public.lang("Cannot find 'bind' configuration, please check your modification")
            ),
            "processes": (
                r'\n\s?workers\s{0,3}=\s{0,3}(?P<target>[^\n]*)[^\n]*\n', None
            ),
            "threads": (
                r'\n\s?threads\s{0,3}=\s{0,3}(?P<target>[\d]*)[^\n]*\n', None
            ),
            "logpath": (
                r'''\n\s?errorlog\s{0,3}=\s{0,3}['"](?P<target>[^"'\n]*)['"][^\n]*\n''',
                public.lang("Cannot find 'errorlog' configuration, please check your modification")
            ),
            "loglevel": (
                r'''\n\s?loglevel\s{0,3}=\s{0,3}['"](?P<target>[^'"\n]*)['"][^\n]*\n''',
                public.lang("Cannot find 'loglevel' configuration, please check your modification")
            )
        }
        changes: Dict[str, str] = {}
        for k, (rep, msg) in get_reps.items():
            res = re.search(rep, config_file)
            if not res and msg:
                raise HintException(msg)
            elif res:
                changes[k] = str(res.group("target").strip())

        if "logpath" in changes:
            if not os.path.exists(changes['logpath']):
                os.makedirs(changes['logpath'], mode=0o777)
            if "/" in changes["logpath"]:
                _path, filename = changes["logpath"].rsplit("/", 1)
                if filename != "gunicorn_error.log":
                    raise HintException(public.lang(
                        "please use 'gunicorn_error.log' as the log file name for easier log management"
                    ))
                else:
                    changes["logpath"] = _path
            else:
                if changes["logpath"] != "gunicorn_error.log":
                    raise HintException(public.lang(
                        "please use 'gunicorn_error.log' as the log file name for easier log management")
                    )
                else:
                    changes["logpath"] = conf["path"]
            rep_accesslog = r'''\n\s?accesslog\s{0,3}=\s{0,3}['"]''' + self.__prevent_re(
                changes["logpath"] + "/gunicorn_acess.log") + r'''['"][^\n]*\n'''
            if not re.search(rep_accesslog, config_file):
                raise HintException(public.lang("please set the access log (accesslog) to the same file path "
                                                "as the error log (errorlog) for easier log management"))

        if "loglevel" in changes:
            if not changes["loglevel"] in ("debug", "info", "warning", "error", "critical"):
                raise HintException(public.lang("Log level configuration error"))
        return changes

    @staticmethod
    def get_ssl_end_date(project_name):
        """
            @name 获取SSL信息
            @author hwliang<2021-08-09>
            @param project_name <string> 项目名称
            @return dict
        """
        import data_v2
        return data_v2.data().get_site_ssl_info('python_{}'.format(project_name))

    def GetProjectInfo(self, get):
        """获取项目所有信息
        @author baozi <202-03-08>
        @param:
            get  ( dict ):  请求信息，站点名称name
        @return
        """
        project = self.get_project_find(get.name.strip())
        if self.prep_status(project["project_config"]) == "running":
            return public.fail_v2(
                public.lang("Project Environment Installation in Progress.....<br>Please Do Not Operate")
            )
        self._get_project_state(project)
        project_conf = project["project_config"]
        if project_conf["stype"] == "python":
            return public.success_v2(project)

        project_conf["processes"] = project_conf["processes"] if "processes" in project_conf else 4
        project_conf["threads"] = project_conf["threads"] if "threads" in project_conf else 2
        if project_conf["stype"] != "python":
            project_conf["is_http"] = bool(project_conf.get("is_http", True))

        project["ssl"] = self.get_ssl_end_date(get.name.strip())
        return public.success_v2(project)

    # 取文件配置
    def GetConfFile(self, get):
        """获取项目配置文件信息
        @author baozi <202-03-08>
        @param:
            get  ( dict ):  用户请求信息 包含name
        @return 文件信息
        """
        project_conf = self._get_project_conf(get.name.strip())
        if not project_conf:
            return public.fail_v2("Project config Not Found")

        if project_conf["stype"] in ("python", "command"):
            return public.fail_v2("No configuration file to modify for Python or custom command startup methods")
        elif project_conf["stype"] == "gunicorn":
            get.path = project_conf["path"] + "/gunicorn_conf.py"
        else:
            get.path = project_conf["path"] + "/uwsgi.ini"
        import files_v2
        f = files_v2.files()
        return f.GetFileBody(get)

    # 保存文件配置
    def SaveConfFile(self, get):
        """修改项目配置文件信息
        @author baozi <202-03-08>
        @param:
            get  ( dict ):  用户请求信息 包含name,data,encoding
        @return 文件信息
        """
        project_conf = self._get_project_conf(get.name.strip())
        if not project_conf:
            return public.fail_v2("Project config Not Found")

        data = get.data
        if project_conf["stype"] == "python":
            return public.fail_v2("No configuration file to modify for Python startup methods")
        elif project_conf["stype"] == "gunicorn":
            get.path = os.path.join(project_conf["path"], "gunicorn_conf.py")
            changes = self.__get_gunicorn_config_from_file(data, project_conf)
        else:
            get.path = os.path.join(project_conf["path"], "uwsgi.ini")
            changes = self.__get_uwsgi_config_from_file(data, project_conf)

        project_conf.update(changes)
        import files_v2
        f = files_v2.files()
        get.encoding = "utf-8"
        result = f.SaveFileBody(get)
        if not result["status"]:
            return public.fail_v2(result.get("message", "Save Failed"))

        # 尝试重启项目
        error_msg = ''
        if not self.__stop_project(project_conf, reconstruction=True):
            error_msg = public.lang("modify success, but failed to stop the project when trying to restart")
        if not self.__start_project(project_conf, reconstruction=True):
            error_msg = public.lang("modify success, but failed to start the project when trying to restart")

        pdata = {
            "project_config": json.dumps(project_conf)
        }
        public.M('sites').where('name=?', (get.name.strip(),)).update(pdata)
        public.WriteLog(self._log_name, 'Python Project [{}], modify project config file'.format(get.name.strip()))

        if error_msg:
            return public.fail_v2(error_msg)
        return public.success_v2(public.lang("Project Configuration Modified Successfully"))

    # ———————————————————————————————————————————
    #   Nginx 与 Apache 相关的设置内容(包含SSL)  |
    # ———————————————————————————————————————————

    def exists_nginx_ssl(self, project_name) -> tuple:
        """
            @name 判断项目是否配置Nginx SSL配置
            @author hwliang<2021-08-09>
            @param project_name: string<项目名称>
            @return tuple
        """
        config_file = "{}/nginx/python_{}.conf".format(public.get_vhost_path(), project_name)
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

    def exists_apache_ssl(self, project_name) -> tuple:
        """
            @name 判断项目是否配置Apache SSL配置
            @author hwliang<2021-08-09>
            @param project_name: string<项目名称>
            @return bool
        """
        config_file = "{}/apache/python_{}.conf".format(public.get_vhost_path(), project_name)
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

    def set_apache_config(self, project, proxy_port=None) -> bool:
        """
            @name 设置Apache配置
            @author hwliang<2021-08-09>
            @param project: dict<项目信息>
            @param proxy_port: int<强制指定代理端口>
            @return bool
        """
        project_name = project['name']
        webservice_status = public.get_multi_webservice_status()
        # 处理域名和端口
        ports = []
        domains = []
        for d in project['project_config']['domains']:
            domain_tmp = d.rsplit(':', 1)
            if len(domain_tmp) == 1:
                domain_tmp.append(80)
            if not int(domain_tmp[1]) in ports:
                ports.append(int(domain_tmp[1]))
            if not domain_tmp[0] in domains:
                domains.append(domain_tmp[0])
        config_file = "{}/apache/python_{}.conf".format(self._vhost_path, project_name)
        template_file = "{}/template/apache/python_http.conf".format(self._vhost_path)
        config_body = public.readFile(template_file)
        apache_config_body = ''

        # 旧的配置文件是否配置SSL
        is_ssl, is_force_ssl = self.exists_apache_ssl(project_name)
        if is_ssl:
            if not 443 in ports:
                ports.append(443)

        stype = project['project_config'].get('stype', '')
        p_port = proxy_port if proxy_port else project['project_config']['port']
        if stype not in ("uwsgi", "gunicorn"):
            # command/原生py, 进程探测监听端口
            args = public.dict_obj()
            args.project_name = project_name
            detected = public.find_value_by_key(
                self.get_port_status(args), "port", default=None
            )
            if detected:
                p_port = detected
                # 放开防火墙端口, 同时清理旧的放开记录
                self._release_firewall(public.to_dict_obj({
                    "release_firewall": 1,
                    "project_name": project_name,
                    "port": str(p_port),
                }))
            else:
                # command 模式未探测到端口, 不生成代理 URL
                p_port = None

        from panel_site_v2 import panelSite
        s = panelSite()

        # 根据端口列表生成配置
        for p in ports:
            listen_port = p
            if webservice_status:
                if p == 443:
                    listen_port = 8290
                else:
                    listen_port = 8288

            # 生成SSL配置
            ssl_config = ''
            if p == 443 and is_ssl:
                ssl_key_file = f"{public.get_vhost_path()}/cert/{project_name}/privkey.pem"
                if not os.path.exists(ssl_key_file):
                    continue  # 不存在证书文件则跳过
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

            # 有端口则生成代理 URL, 否则留空
            proxy_url = 'http://127.0.0.1:{}'.format(p_port) if p_port else ''

            # 生成vhost主体配置
            apache_config_body += config_body.format(
                site_path=project['path'],
                server_name='{}.{}'.format(project_name, p),
                domains=' '.join(domains),
                log_path=public.get_logs_path(),
                server_admin='admin@{}'.format(project_name),
                url=proxy_url,
                port=listen_port,  # 写入 VirtualHost *:端口
                ssl_config=ssl_config,
                project_name=project_name
            )
            apache_config_body += "\n"

            # 添加端口到主配置文件
            if listen_port not in [80]:
                s.apacheAddPort(listen_port)

        # 写.htaccess
        rewrite_file = "{}/.htaccess".format(project['path'])
        if not os.path.exists(rewrite_file):
            public.writeFile(rewrite_file, "# rewrite rules or custom Apache configurations here\n")

        from mod.base.web_conf import ap_ext
        apache_config_body = ap_ext.set_extension_by_config(project_name, apache_config_body)
        # 写配置文件
        public.writeFile(config_file, apache_config_body)
        return True

    def set_nginx_config(self, project, is_modify=False, proxy_port=None) -> bool:
        """
            @name 设置Nginx配置
            @author hwliang<2021-08-09>
            @param project: dict<项目信息>
            @return bool
        """
        project_name = project['name']
        ports = []
        domains = []

        for d in project['project_config']['domains']:
            domain_tmp = d.rsplit(':', 1)
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
    error_page 497  https://$host$request_uri;'''.format(vhost_path=self._vhost_path, priject_name=project_name,
                                                         http3_header=http3_header)

            if is_force_ssl:
                ssl_config += '''
    #HTTP_TO_HTTPS_START
    if ($server_port !~ 443){
        rewrite ^(/.*)$ https://$host$1 permanent;
    }
    #HTTP_TO_HTTPS_END'''

        config_file = "{}/nginx/python_{}.conf".format(self._vhost_path, project_name)
        template_file = "{}/template/nginx/python_http.conf".format(self._vhost_path)
        listen_ports = "\n".join(listen_ports_list).strip()

        p_port = proxy_port if proxy_port else project['project_config']['port']
        stype = project['project_config'].get('stype', '')
        if stype not in ("uwsgi", "gunicorn"):
            # 如果是command或者py原生启动, 则project['project_config']['port']已经不准确
            # 尝试找占用端口
            args = public.dict_obj()
            args.project_name = project_name
            p_port = public.find_value_by_key(
                self.get_port_status(args), "port", default=p_port
            )
            if p_port:  # 同时放开端口, 关闭此项目之前旧的放开的端口
                self._release_firewall(public.to_dict_obj({
                    "release_firewall": 1,
                    "project_name": project_name,
                    "port": str(p_port),
                }))

        uwsgi_mode = 'http'  # 默认
        if stype == 'uwsgi':
            uwsgi_ini = os.path.join(project['project_config']['path'], 'uwsgi.ini')
            ini_content = public.readFile(uwsgi_ini) or ''
            if re.search(r'^\s*socket\s*=', ini_content, re.M):
                uwsgi_mode = 'socket'
            elif re.search(r'^\s*http-socket\s*=', ini_content, re.M):
                uwsgi_mode = 'http-socket'

        proxy_content = "# proxy"

        # if is_modify != "close" and (is_modify or stype != "command"):
        # 如果找到ports, 尝试添加
        if is_modify != "close" and (is_modify or stype != "command" or p_port):
            if not p_port:
                # 确保端口存在, 避免 nginx 语法错误
                proxy_content = ""

            elif stype == 'uwsgi' and uwsgi_mode == 'socket':
                proxy_content = '''# proxy
    location / {{
        include uwsgi_params;
        uwsgi_pass 127.0.0.1:{p_port};
        proxy_set_header Host 127.0.0.1:$server_port;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }}'''.format(p_port=p_port)

            else:
                proxy_content = '''# proxy
    location / {{
        proxy_pass http://127.0.0.1:{p_port};
        proxy_set_header Host {host}:$server_port;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header REMOTE-HOST $remote_addr;
        add_header X-Cache $upstream_cache_status;
        proxy_set_header X-Host $host:$server_port;
        proxy_set_header X-Scheme $scheme;
        proxy_connect_timeout 30s;
        proxy_read_timeout 86400s;
        proxy_send_timeout 30s;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }}'''.format(p_port=p_port, host="127.0.0.1")

        config_body = public.readFile(template_file)
        mut_config = {
            "site_path": project['path'],
            "domains": ' '.join(domains),
            "ssl_config": ssl_config,
            "listen_ports": listen_ports,
            "proxy": proxy_content  # 添加代理内容替换
        }
        config_body = config_body.format(
            site_path=project['path'],
            domains=mut_config["domains"],
            project_name=project_name,
            panel_path=self._panel_path,
            log_path=public.get_logs_path(),
            host='127.0.0.1',
            listen_ports=listen_ports,
            ssl_config=ssl_config,
            proxy=mut_config["proxy"]  # 添加代理替换
        )

        rewrite_file = f"{self._panel_path}/vhost/rewrite/python_{project_name}.conf"
        if not os.path.exists(rewrite_file):
            public.writeFile(rewrite_file, '# rewrite rules or custom NGINX configurations here\n')
        if not os.path.exists("/www/server/panel/vhost/nginx/well-known"):
            os.makedirs("/www/server/panel/vhost/nginx/well-known", 0o600)

        apply_check = f"{self._panel_path}/vhost/nginx/well-known/{project_name}.conf"
        from mod.base.web_conf import ng_ext
        config_body = ng_ext.set_extension_by_config(project_name, config_body)
        if not os.path.exists(apply_check):
            public.writeFile(apply_check, '')

        if not os.path.exists(config_file):
            public.writeFile(config_file, config_body)
        else:
            if not self._replace_nginx_conf(config_file, mut_config):
                public.writeFile(config_file, config_body)
        return True

    @staticmethod
    def _replace_nginx_conf(config_file, mut_config: dict) -> bool:
        """尝试替换"""
        data: str = public.readFile(config_file)
        tab_spc = "    "
        rep_list = [
            (
                r"([ \f\r\t\v]*listen[^;\n]*;\n(\s*http2\s+on\s*;[^\n]*\n)?)+",
                mut_config["listen_ports"] + "\n"
            ),
            (
                r"[ \f\r\t\v]*root [ \f\r\t\v]*/[^;\n]*;",
                "    root {};".format(mut_config["site_path"])
            ),
            (
                r"[ \f\r\t\v]*server_name [ \f\r\t\v]*[^\n;]*;",
                "   server_name {};".format(mut_config["domains"])
            ),
            (
                r"(location / {)(.*?)(})",
                mut_config["proxy"].strip()
            ),
            (
                "[ \f\r\t\v]*#SSL-START SSL related configuration(.*\n){2,15}[ \f\r\t\v]*#SSL-END",
                "{}#SSL-START SSL related configuration\n{}#error_page 404/404.html;\n{}{}\n{}#SSL-END".format(
                    tab_spc, tab_spc, tab_spc, mut_config["ssl_config"], tab_spc
                )
            )
        ]
        for rep, info in rep_list:
            if re.search(rep, data):
                data = re.sub(rep, info, data, 1)
            else:
                return False
        public.writeFile(config_file, data)
        return True

    def clear_nginx_config(self, project) -> bool:
        """
            @name 清除nginx配置
            @author hwliang<2021-08-09>
            @param project: dict<项目信息>
            @return bool
        """
        project_name = project['name']
        config_file = "{}/nginx/python_{}.conf".format(self._vhost_path, project_name)
        if os.path.exists(config_file):
            os.remove(config_file)
        rewrite_file = "{panel_path}/vhost/rewrite/python_{project_name}.conf".format(
            panel_path=self._panel_path, project_name=project_name
        )
        if os.path.exists(rewrite_file):
            os.remove(rewrite_file)
        return True

    def clear_apache_config(self, project):
        """
            @name 清除apache配置
            @author hwliang<2021-08-09>
            @param project_find: dict<项目信息>
            @return bool
        """
        project_name = project['name']
        config_file = "{}/apache/python_{}.conf".format(self._vhost_path, project_name)
        if os.path.exists(config_file):
            os.remove(config_file)
        return True

    def get_project_find(self, project_name) -> Union[dict]:
        """
            @name 获取指定项目配置
            @author hwliang<2021-08-09>
            @param project_name<string> 项目名称
            @return dict
        """
        project_info = public.M('sites').where('project_type=? AND name=?', ('Python', project_name)).find()
        if not isinstance(project_info, dict):
            raise HintException("Python Site Not Found!")
        try:
            project_info['project_config'] = json.loads(project_info['project_config'])
        except Exception as e:
            return public.fail_v2("Python Project Config Error, {}".format(str(e)))

        if "env_list" not in project_info['project_config']:
            project_info['project_config']["env_list"] = []
        if "env_file" not in project_info['project_config']:
            project_info['project_config']["env_file"] = ""
        return project_info

    def clear_config(self, project_name):
        """
            @name 清除项目配置
            @author hwliang<2021-08-09>
            @param project_name: string<项目名称>
            @return bool
        """
        try:
            project_find = self.get_project_find(project_name)
        except (HintException, Exception):
            project_find = {}
        if project_find:
            # todo
            self.clear_nginx_config(project_find)
            self.clear_apache_config(project_find)
            from ssl_domainModelV2 import sync_user_for
            sync_user_for()
        public.serviceReload()
        return True

    def set_config(self, project_name, is_modify=False, proxy_port=None) -> bool:
        """
            @name 设置项目配置
            @author hwliang<2021-08-09>
            @param project_name: string<项目名称>
            @return bool
        """
        try:
            project_find = self.get_project_find(project_name)
        except (HintException, Exception):
            public.print_log(f"set config for project {project_name} failed, project not found")
            return False
        if not project_find.get("project_config"):
            public.print_log(f"set config for project {project_name} failed, project_config not found")
            return False
        if not project_find.get("project_config", {}).get("bind_extranet"):
            public.print_log(f"set config for project {project_name} failed, bind_extranet not found")
            return False
        if not project_find.get("project_config", {}).get("domains"):
            public.print_log(f"set config for project {project_name} failed, domains not found")
            return False
        self.set_nginx_config(project_find, is_modify, proxy_port)
        self.set_apache_config(project_find, proxy_port)
        # todo ols
        public.serviceReload()
        return True

    def BindExtranet(self, get):
        """
            @name 绑定外网
            @author hwliang<2021-08-09>
            @param get<dict_obj>{
                name: string<项目名称>
            }
            @return dict
        """
        self._check_webserver()
        project_name = get.name.strip()
        project_find = self.get_project_find(project_name)
        if self.prep_status(project_find["project_config"]) == "running":
            return public.fail_v2(public.lang("Python Project Env Installing, Please Wait ..."))
        if not project_find['project_config'].get("domains"):
            return public.fail_v2(public.lang("Please add at least one domain name"))
        project_find['project_config']['bind_extranet'] = 1
        public.M('sites').where("id=?", (project_find['id'],)).setField(
            'project_config', json.dumps(project_find['project_config'])
        )
        self.set_config(project_name)
        public.WriteLog(
            self._log_name, 'Python Project [{}], Enable Extranet Mapping for Internet'.format(project_name)
        )
        return public.success_v2(public.lang("Bind Extranet Successful"))

    def unBindExtranet(self, get):
        """
            @name 解绑外网
            @author hwliang<2021-08-09>
            @param get<dict_obj>{
                name: string<项目名称>
            }
            @return dict
        """
        project_name = get.name.strip()
        self.clear_config(project_name)
        public.serviceReload()
        project_find = self.get_project_find(project_name)
        project_find['project_config']['bind_extranet'] = 0
        public.M('sites').where("id=?", (project_find['id'],)).setField(
            'project_config', json.dumps(project_find['project_config']))
        public.WriteLog(
            self._log_name, 'Python Project [{}], Disable Extranet Mapping for Internet'.format(project_name)
        )
        return public.success_v2(public.lang("unBind Extranet Successfully"))

    def GetProjectDomain(self, get):
        """
            @name 获取指定项目的域名列表
            @author hwliang<2021-08-09>
            @param get<dict_obj>{
                name: string<项目名称>
            }
            @return dict
        """
        project_name = get.name.strip()
        project_id = public.M('sites').where('name=?', (project_name,)).getField('id')
        if not project_id:
            return public.fail_v2("Site Not Found")
        domains = public.M('domain').where('pid=?', (project_id,)).order('id desc').select()
        return public.success_v2(domains)

    def RemoveProjectDomain(self, get):
        """
            @name 为指定项目删除域名
            @author hwliang<2021-08-09>
            @param get<dict_obj>{
                name: string<项目名称>
                domain: string<域名>
            }
            @return dict
        """
        project_name = get.name.strip()
        project_find = self.get_project_find(project_name)
        if not project_find:
            return public.fail_v2("Site Not Found")
        domain_arr = get.domain.rsplit(':', 1)
        if len(domain_arr) == 1:
            domain_arr.append(80)

        # 从域名配置表中删除
        project_id = public.M('sites').where('name=?', (project_name,)).getField('id')
        if len(project_find['project_config']['domains']) == 1:
            if int(project_find['project_config']['bind_extranet']):
                return public.fail_v2(
                    public.lang("Project Must Have At Least One Domain When Extranet Mapping Is Enabled")
                )
        domain_id = public.M('domain').where(
            'name=? AND port=? AND pid=?',
            (domain_arr[0], domain_arr[1], project_id)
        ).getField('id')
        public.print_log("Trying to remove domain {}, domain_id: {}".format(get.domain, domain_id))
        if not domain_id:
            return public.fail_v2(public.lang("Domain Not Found"))
        public.M('domain').where('id=?', (domain_id,)).delete()

        # 从 project_config 中删除
        try:
            if get.domain in project_find['project_config']['domains']:
                project_find['project_config']['domains'].remove(get.domain)
            if get.domain + ":80" in project_find['project_config']['domains']:
                project_find['project_config']['domains'].remove(get.domain + ":80")
        except Exception as e:
            return public.fail_v2("Remove Domain From Config Failed: {}".format(str(e)))

        public.M('sites').where('id=?', (project_id,)).save(
            'project_config', json.dumps(project_find['project_config'])
        )
        public.WriteLog(self._log_name, 'Python Project: [{}]，Remove Domain:{}'.format(project_name, get.domain))
        self.set_config(project_name)
        return public.success_v2(public.lang("Domain Deleted Successfully"))

    def MultiRemoveProjectDomain(self, get):
        """
            @name 为指定项目删除域名
            @author hwliang<2021-08-09>
            @param get<dict_obj>{
                name: string<项目名称>
                domain: string<域名>
            }
            @return dict
        """
        project_name = get.name.strip()
        project_find = self.get_project_find(project_name)
        domain_ids: list = get.domain_ids

        try:
            if isinstance(domain_ids, str):
                domain_ids = json.loads(domain_ids)
            for i in range(len(domain_ids)):
                domain_ids[i] = int(domain_ids[i])
        except:
            return public.fail_v2("Domain IDs Format Error")

        # 获取正确的IDS
        project_id = public.M('sites').where('name=?', (project_name,)).getField('id')
        _all_id = public.M('domain').where('pid=?', (project_id,)).field("id,name,port").select()
        if not isinstance(_all_id, list):
            return public.fail_v2("Site Domain Data Error")
        all_id = {
            i["id"]: (i["name"], i["port"]) for i in _all_id
        }
        # 从域名配置表中删除
        for i in domain_ids:
            if i not in all_id:
                return public.fail_v2("Domain Not Found from Site")
        is_all = len(domain_ids) == len(all_id)
        not_del = None
        if is_all:
            domain_ids.sort(reverse=True)
            domain_ids, not_del = domain_ids[:-1], domain_ids[-1]
        if not_del:
            not_del = {
                "id": not_del, "name": all_id[not_del][0], "port": all_id[not_del][1]
            }

        public.M('domain').where(f'id IN ({",".join(["?"] * len(domain_ids))})', domain_ids).delete()

        del_domains = []
        for i in domain_ids:
            # 从 project_config 中删除
            d_n, d_p = all_id[i]
            del_domains.append(d_n + ':' + str(d_p))
            if d_n in project_find['project_config']['domains']:
                project_find['project_config']['domains'].remove(d_n)
            if d_n + ':' + str(d_p) in project_find['project_config']['domains']:
                project_find['project_config']['domains'].remove(d_n + ':' + str(d_p))

        public.M('sites').where('id=?', (project_id,)).save(
            'project_config', json.dumps(project_find['project_config'])
        )
        public.WriteLog(self._log_name, 'Python Project: [{}]，Mulit Delete Domian:'.format(project_name, del_domains))
        self.set_config(project_name)

        if isinstance(not_del, dict):
            error_data = {not_del["name"]: "Project Must Have At Least One Domain"}
        else:
            error_data = {}
        return public.success_v2({
            "success": "Delete Success :{}".format(del_domains),
            "error": error_data,
        })

    def AddProjectDomain(self, get):
        """
            @name 为指定项目添加域名
            @author hwliang<2021-08-09>
            @param get<dict_obj>{
                name: string<项目名称>
                domains: list<域名列表>
            }
            @return dict
        """
        project_name = get.name.strip()
        project_find = self.get_project_find(project_name)
        project_id = project_find['id']
        domains = get.domains
        if not isinstance(domains, list):
            try:
                domains = json.loads(domains)
            except Exception as e:
                return public.fail_v2("Domains Format Error: {}".format(str(e)))
        check_cloud = False
        flag = False
        res_domains = []
        for domain in domains:
            domain = domain.strip()
            if not domain:
                continue
            if "[" in domain and "]" in domain:  # IPv6格式特殊处理
                if "]:" in domain:
                    domain_arr = domain.rsplit(":", 1)
                else:
                    domain_arr = [domain]
            else:
                domain_arr = domain.split(':')
            domain_arr[0] = self.check_domain(domain_arr[0])
            if domain_arr[0] is False:
                res_domains.append(
                    {"name": domain, "status": False, "msg": 'Invalid Domain'}
                )
                continue
            if len(domain_arr) == 1:
                domain_arr.append("")
            if domain_arr[1] == "":
                domain_arr[1] = 80
                domain += ':80'
            try:
                if not (0 < int(domain_arr[1]) < 65535):
                    res_domains.append({"name": domain, "status": False, "msg": 'Invalid Domain'})
                    continue
            except ValueError:
                res_domains.append({"name": domain, "status": False, "msg": 'Invalid Domain'})
                continue
            if not public.M('domain').where('name=? AND port=?', (domain_arr[0], domain_arr[1])).count():
                public.M('domain').add(
                    'name,pid,port,addtime',
                    (domain_arr[0], project_id, domain_arr[1], public.getDate())
                )
                if not domain in project_find['project_config']['domains']:
                    project_find['project_config']['domains'].append(domain)
                public.WriteLog(self._log_name, 'Add Domian "{}" to [{}]'.format(domain, project_name))
                res_domains.append({"name": domain_arr[0], "status": True, "msg": 'success'})
                if not check_cloud:
                    public.check_domain_cloud(domain_arr[0])
                    check_cloud = True
                self._release_firewall(public.to_dict_obj({
                    "release_firewall": 1,
                    "project_name": project_name,
                    "port": domain_arr[1],
                }))
                flag = True
            else:
                public.WriteLog(self._log_name, 'Add Domian Failed，domain [{}] is exist'.format(domain))
                res_domains.append(
                    {
                        "name": domain_arr[0],
                        "status": False,
                        "msg": 'Add Domian Failed，domain [{}] is exist'.format(domain)
                    }
                )
        if flag:
            public.M('sites').where('id=?', (project_id,)).save(
                'project_config', json.dumps(project_find['project_config'])
            )

            self.set_config(project_name)
        public.set_module_logs('python_project', 'add_domain', 1)
        return public.success_v2(self._check_add_domain(project_name, res_domains))

    def auto_run(self):
        """
        @name 开机自动启动
        """
        # 获取数据库信息
        project_list = public.M('sites').where('project_type=?', ('Python',)).field('name,path,project_config').select()
        get = public.dict_obj()
        success_count = 0
        error_count = 0
        for project in project_list:
            try:
                project_config = json.loads(project['project_config'])
                if project_config['auto_run'] in [0, False, '0', None]:
                    continue
                project_name = project['name']
                project_state = self.get_project_run_state(project_name=project_name)
                if not project_state:
                    get.name = project_name
                    result = self.StartProject(get)
                    if not result['status']:
                        error_count += 1
                        error_msg = "Auto Start Python Project [{}] Failed: {}".format(
                            project_name, result['msg']
                        )
                        public.WriteLog(self._log_name, error_msg)
                    else:
                        success_count += 1
                        success_msg = "Auto Start Python Project [{}] Succeed".format(project_name)
                        public.WriteLog(self._log_name, success_msg)
            except (HintException, Exception):
                error_count += 1
                error_msg = "Auto Start Python Project [{}] Failed".format(project['name'])
                public.WriteLog(self._log_name, error_msg)

        if (success_count + error_count) < 1:
            return False
        done_msg = "Auto Start Python Projects Completed, Result: {} Succeed, {} Failed".format(
            success_count, error_count
        )
        public.WriteLog(self._log_name, done_msg)
        return True

    # 移除cron
    def _del_crontab_by_name(self, cron_name):
        try:
            cron_path = public.GetConfigValue('setup_path') + '/cron/'
            cron_list = public.M('crontab').where("name=?", (cron_name,)).select()
            if cron_list and isinstance(cron_list, list):
                for i in cron_list:
                    if not i: continue
                    cron_echo = public.M('crontab').where("id=?", (i['id'],)).getField('echo')
                    args = {"id": i['id']}
                    import crontab_v2
                    crontab_v2.crontab().DelCrontab(args)
                    del_cron_file = cron_path + cron_echo
                    public.ExecShell("crontab -u root -l| grep -v '{}'|crontab -u root -".format(del_cron_file))
        except Exception as e:
            public.print_log("Delete crontab {} failed: {}".format(cron_name, str(e)))

    # —————————————
    #  日志切割   |
    # —————————————
    def del_crontab(self, name):
        """
        @name 删除项目日志切割任务
        @auther hezhihong<2022-10-31>
        @return
        """
        cron_name = self._split_cron_name_temp.format(name)
        self._del_crontab_by_name(cron_name)

    def add_crontab(self, name, log_conf, python_path):
        """
        @name 构造站点运行日志切割任务
        """
        cron_name = self._split_cron_name_temp.format(name)
        if not public.M('crontab').where('name=?', (cron_name,)).count():
            cmd = '{pyenv} {script_path} {name}'.format(
                pyenv=python_path,
                script_path=self.__log_split_script_py,
                name=name
            )
            args = {
                "name": cron_name,
                "type": 'day' if log_conf["log_size"] == 0 else "minute-n",
                "where1": "" if log_conf["log_size"] == 0 else log_conf["minute"],
                "hour": log_conf["hour"],
                "minute": log_conf["minute"],
                "sName": name,
                "sType": 'toShell',
                "notice": '0',
                "notice_channel": '',
                "save": str(log_conf["num"]),
                "save_local": '1',
                "backupTo": '',
                "sBody": cmd,
                "urladdress": ''
            }
            import crontab_v2
            res = crontab_v2.crontab().AddCrontab(args).get("message", {})
            if res and "id" in res.keys():
                return True, "Add Success"
            return False, res["msg"]
        return True, "Add Success"

    def change_cronta(self, name, log_conf) -> tuple[bool, str]:
        """
        @name 更改站点运行日志切割任务
        """
        python_path = "/www/server/panel/pyenv/bin/python3"
        if not python_path:
            return False, ""
        cron_name = self._split_cron_name_temp.format(name)
        cronInfo = public.M('crontab').where('name=?', (cron_name,)).find()
        if not cronInfo:
            return self.add_crontab(name, log_conf, python_path)
        import crontab_v2
        recrontabMode = crontab_v2.crontab()
        id = cronInfo['id']
        del (cronInfo['id'])
        del (cronInfo['addtime'])
        cronInfo['sBody'] = '{pyenv} {script_path} {name}'.format(
            pyenv=python_path,
            script_path=self.__log_split_script_py,
            name=name
        )
        cronInfo['where_hour'] = log_conf['hour']
        cronInfo['where_minute'] = log_conf['minute']
        cronInfo['save'] = log_conf['num']
        cronInfo['type'] = 'day' if log_conf["log_size"] == 0 else "minute-n"
        cronInfo['where1'] = '' if log_conf["log_size"] == 0 else log_conf['minute']

        columns = 'where_hour,where_minute,sBody,save,type,where1'
        values = (
            cronInfo['where_hour'], cronInfo['where_minute'], cronInfo['sBody'],
            cronInfo['save'], cronInfo['type'], cronInfo['where1']
        )
        recrontabMode.remove_for_crond(cronInfo['echo'])
        if cronInfo['status'] == 0:
            return False, "this Cron Job is Disabled, please open the status first"
        sync_res = recrontabMode.sync_to_crond(cronInfo)
        if not sync_res:
            return False, "Sync to crond Failed, please try again"
        public.M('crontab').where('id=?', (id,)).save(columns, values)
        public.WriteLog(public.lang('crontab tasks'),
                        public.lang('Successfully modified plan task [' + cron_name + ']'))
        return True, 'Modify Success'

    def mamger_log_split(self, get):
        """管理日志切割任务
        @author baozi <202-02-27>
        @param:
            get  ( dict ):  包含name, mode, hour, minute
        @return
        """
        name = get.name.strip()
        project_conf = self._get_project_conf(name_id=name)
        if not project_conf:
            return public.fail_v2("Project config not found, please try to refresh the page")
        try:
            _log_size = float(get.log_size) if float(get.log_size) >= 0 else 0
            _hour = get.hour.strip() if 0 <= int(get.hour) < 24 else "2"
            _minute = get.minute.strip() if 0 <= int(get.minute) < 60 else '0'
            _num = int(get.num) if 0 < int(get.num) <= 1800 else 180
            _compress = False
            if "compress" in get:
                _compress = bool(get.compress in [1, "1", True, "true", "True"])
        except (ValueError, AttributeError) as e:
            public.print_log(f"e = {e}")
            _log_size = 0
            _hour = "2"
            _minute = "0"
            _num = 180
            _compress = False

        if _log_size != 0:
            _log_size = _log_size * 1024 * 1024
            _hour = 0
            _minute = 5

        log_conf = {
            "log_size": _log_size,
            "hour": _hour,
            "minute": _minute,
            "num": _num,
            "compress": _compress,
        }
        flag, msg = self.change_cronta(name, log_conf)
        if flag:
            conf_path = '{}/data/run_log_split.conf'.format(public.get_panel_path())
            if os.path.exists(conf_path):
                try:
                    data = json.loads(public.readFile(conf_path))
                except:
                    data = {}
            else:
                data = {}
            data[name] = {
                "stype": "size" if bool(_log_size) else "day",
                "log_size": _log_size,
                "limit": _num,
                "compress": _compress,
            }
            public.writeFile(conf_path, json.dumps(data))
            project_conf["log_conf"] = log_conf
            pdata = {
                "project_config": json.dumps(project_conf)
            }
            public.M('sites').where('name=?', (name,)).update(pdata)
        return public.return_message(0 if flag else -1, 0, msg)

    def set_log_split(self, get):
        """设置日志计划任务状态
        @author baozi <202-02-27>
        @param:
            get  ( dict ):  包含项目名称name
        @return  msg : 操作结果
        """
        name = get.name.strip()
        project_conf = self._get_project_conf(name_id=name)
        if not project_conf:
            return public.fail_v2("Project config not found, please try to refresh the page")
        cron_name = self._split_cron_name_temp.format(name)
        cronInfo = public.M('crontab').where('name=?', (cron_name,)).find()
        if not cronInfo:
            return public.fail_v2("Project log split Cron Job not found")

        status_msg = ['Disabel', 'Enable']
        status = 1
        import crontab_v2
        recrontabMode = crontab_v2.crontab()

        if cronInfo['status'] == status:
            status = 0
            recrontabMode.remove_for_crond(cronInfo['echo'])
        else:
            cronInfo['status'] = 1
            sync_res = recrontabMode.sync_to_crond(cronInfo)
            if not sync_res:
                return public.fail_v2("Sync to crond Failed, please try again")
        public.M('crontab').where('id=?', (cronInfo["id"],)).setField('status', status)
        public.WriteLog(public.lang('crontab tasks'),
                        public.lang(
                            'Successfully modified plan task [' + cron_name + '] status to [' + status_msg[
                                status] + ']')
                        )
        return public.success_v2(public.lang("Set Successfully"))

    def get_log_split(self, get):
        """获取站点的日志切割任务
        @author baozi <202-02-27>
        @param:
            get  ( dict ):   name
        @return msg : 操作结果
        """

        name = get.name.strip()
        project_conf = self._get_project_conf(name_id=name)
        if not project_conf:
            return public.fail_v2(public.lang("No Such Project, Please Try To Refresh The Page"))
        cron_name = self._split_cron_name_temp.format(name)
        cronInfo = public.M('crontab').where('name=?', (cron_name,)).find()
        if not cronInfo:
            return public.fail_v2("Project does not have a log split Cron Job set")

        if "log_conf" not in project_conf:
            return public.fail_v2("Log split configuration is missing, please try to reset")
        if "log_size" in project_conf["log_conf"] and project_conf["log_conf"]["log_size"] != 0:
            project_conf["log_conf"]["log_size"] = project_conf["log_conf"]["log_size"] / (1024 * 1024)
        res = project_conf["log_conf"]
        res["status"] = cronInfo["status"]
        return public.success_v2(res)

    # ——————————————————————————————————————————————
    #   对用户的项目目录进行预先读取， 获取有效信息   |
    # ——————————————————————————————————————————————

    def _get_requirements_by_readme_file(self, path) -> Optional[str]:
        readme_rep = re.compile("^[Rr][Ee][Aa][Dd][Mm][Ee]")
        readme_files = self.__search_file(readme_rep, path, this_type="file")
        if not readme_files:
            return None

        # 从README找安装依赖包文件
        target_path = None
        requirements_rep = re.compile(r'pip\s+install\s+-r\s+(?P<target>[A-z0-9_/.]*)')
        for i in readme_files:
            file_data = public.read_rare_charset_file(i)
            if not isinstance(file_data, str):
                continue
            target = re.search(requirements_rep, file_data)
            if target:
                requirements_path = os.path.join(path, target.group("target"))
                if os.path.exists(requirements_path) and os.path.isfile(requirements_path):
                    target_path = str(requirements_path)
                    break
        if not target_path:
            return None
        return target_path

    def _get_requirements_file_by_name(self, path) -> Optional[str]:
        requirements_rep = re.compile(r"^[rR]equirements\.txt$")
        requirements_path = self.__search_file(requirements_rep, path, this_type="file")
        if not requirements_path:
            requirements_rep2 = re.compile(r"^[Rr]equirements?")
            requirements_dir = self.__search_file(requirements_rep2, path, this_type="dir")
            if requirements_dir:
                for i in requirements_dir:
                    tmp = self._get_requirements_file_by_name(i)
                    if tmp:
                        return tmp
            return None
        return requirements_path[0]

    def get_requirements_file(self, path: str) -> Optional[str]:
        requirement_path = self._get_requirements_file_by_name(path)
        if not requirement_path:
            requirement_path = self._get_requirements_by_readme_file(path)
        return requirement_path

    @staticmethod
    def _get_framework_by_requirements(requirements_path: str) -> Optional[str]:
        file_body = public.read_rare_charset_file(requirements_path)
        if not isinstance(file_body, str):
            return None
        rep_list = [
            (r"[Dd]jango(\s*==|\s*\n)", "django"),
            (r"[Ff]lask(\s*==|\s*\n)", "flask"),
            (r"[Ss]anic(\s*==|\s*\n)", "sanic"),
            (r"[Ff]ast[Aa]pi(\s*==|\s*\n)", "fastapi"),
            (r"[Tt]ornado(\s*==|\s*\n)", "tornado"),
            (r"aiohttp(\s*==|\s*\n)", "aiohttp"),
        ]
        frameworks = set()
        for rep_str, framework in rep_list:
            if re.search(rep_str, file_body):
                frameworks.add(framework)
        if "aiohttp" in frameworks and len(frameworks) == 2:
            frameworks.remove("aiohttp")
            return frameworks.pop()

        if len(frameworks) == 1:
            return frameworks.pop()
        return None

    @staticmethod
    def _check_runfile_framework_xsgi(
            runfile_list: List[str],
            framework: str = None
    ) -> Tuple[Optional[str], Optional[str], Optional[str]]:

        if not runfile_list:
            return None, None, None
        framework_check_dict = {
            "django": [
                (re.compile(r"from\s+django\.core\.asgi\s+import\s+get_asgi_application"), "asgi"),
                (re.compile(r"get_asgi_application\(\)"), "asgi"),
                (re.compile(r"from\s+django\.core\.wsgi\s+import\s+get_wsgi_application"), "wsgi"),
                (re.compile(r"get_wsgi_application\(\)"), "wsgi"),
            ],
            "flask": [
                (re.compile(r"from\s+flask\s+import(.*)Flask"), "wsgi"),
                (re.compile(r"\s*=\s*Flask\(.*\)"), "wsgi"),
                (re.compile(r"from\s+flask\s+import"), "wsgi"),
            ],
            "fastapi": [
                (re.compile(r"from\s+fastapi\s+import(.*)FastAPI"), "asgi"),
                (re.compile(r"\s*=\s*FastAPI\(.*\)"), "asgi"),
                (re.compile(r"from\s+fastapi\s+import"), "asgi"),
            ],
            "sanic": [
                (re.compile(r"from\s+sanic\s+import\s+Sanic"), "asgi"),
                (re.compile(r"\s*=\s*Sanic\(.*\)c"), "asgi"),
                (re.compile(r"from\s+sanic\s+import"), "asgi"),
            ],
            "tornado": [
                (re.compile(r"import\s+tornado"), None),
            ],

        }
        if framework and framework in framework_check_dict:
            framework_check_dict = {framework: framework_check_dict[framework]}
        for i in runfile_list:
            file_data = public.read_rare_charset_file(i)
            if not isinstance(file_data, str):
                continue
            for tmp_framework, check_list in framework_check_dict.items():
                for tmp_rep, xwgi in check_list:
                    if re.search(tmp_rep, file_data):
                        return i, tmp_framework, xwgi
        if framework:
            return runfile_list[0], framework, None
        if runfile_list:
            return runfile_list[0], None, None
        return None, None, None

    def _get_run_file_list(self, path, search_sub=False) -> List[str]:
        """
        常用的名称： manager，wsgi，asgi，app，main，run, server
        """
        runfile_rep = re.compile(r"^(wsgi|asgi|app|main|manager|run|server)\.py$")
        maybe_runfile = self.__search_file(runfile_rep, path, this_type="file")

        if maybe_runfile:
            return maybe_runfile
        elif not search_sub:
            return []

        for i in os.listdir(path):
            tmp_path = os.path.join(path, i)
            if os.path.isdir(tmp_path):
                maybe_runfile = self._get_run_file_list(tmp_path, search_sub=False)
                if maybe_runfile:
                    return maybe_runfile
        return []

    def get_info(self, get):
        """ 对用户的项目目录进行预先读取， 获取有效信息
        @author baozi <202-03-10>
        @param:
            get  ( dict ):  请求信息，包含path，路径
        @return  _type_ : _description_
        """
        if "path" not in get:
            return public.fail_v2(public.lang("No Project Path Info Selected"))

        path = get.path.strip().rstrip("/")
        if not os.path.exists(path):
            return public.fail_v2(public.lang("Project Directory Does Not Exist"))

        # 找requirement文件
        requirement_path = self.get_requirements_file(path)
        maybe_runfile_list = self._get_run_file_list(path, search_sub=True)
        framework = None
        if requirement_path:
            framework = self._get_framework_by_requirements(requirement_path)

        runfile, framework, xsgi = self._check_runfile_framework_xsgi(maybe_runfile_list, framework)

        call_app = "app"
        if framework and runfile:
            values = {
                "framework": framework,
                "rfile": runfile,
            }
            call_app = self._get_callable_app(values)

        return public.success_v2({
            "framework": framework,
            "requirement_path": requirement_path,
            "runfile": runfile,
            "xsgi": xsgi,
            "call_app": call_app
        })

    @staticmethod
    def __search_file(name_rep: re.Pattern, path: str, this_type="file", exclude=None) -> List[str]:
        target_names = []
        for f_name in os.listdir(path):
            f_name.encode('utf-8')
            target_name = name_rep.search(f_name)
            if target_name:
                target_names.append(f_name)

        res = []
        for i in target_names:
            if exclude and i.find(exclude) != -1:
                continue
            _path = os.path.join(path, i)
            if this_type == "file" and os.path.isfile(_path):
                res.append(_path)
                continue
            if this_type == "dir" and not os.path.isfile(_path):
                res.append(_path)
                continue

        return res

    def get_info_by_runfile(self, get):
        """ 通过运行文件对用户的项目预先读取， 获取有效信息
        @author baozi <202-03-10>
        @param:
            get  ( dict ):  请求信息，包含path，路径
        @return  _type_ : _description_
        """
        if "runfile" not in get:
            return public.fail_v2(public.lang("No Project Run File Info Selected"))
        runfile = get.runfile.strip()
        if not os.path.isfile(runfile):
            return False, public.lang("Project Run File Does Not Exist (or not a File)")

        runfile, framework, xsgi = self._check_runfile_framework_xsgi([runfile])
        if runfile is None:
            return public.success_v2({
                "framework": None,
                "xsgi": None,
                "call_app": None
            })

        values = {
            "framework": framework,
            "rfile": runfile,
        }

        call_app = self._get_callable_app(values)

        return public.success_v2({
            "framework": framework,
            "xsgi": xsgi,
            "call_app": call_app
        })

    def for_split(self, logsplit: Callable, project: dict):
        """日志切割方法调用
        @author baozi <202-03-20>
        @param:
            logsplit  ( LogSplit ):  日志切割方法，传入 pjanme:项目名称 sfile:日志文件路径 log_prefix:产生的日志文件前缀
            project  ( dict ):  项目内容
        @return
        """
        if project['project_config']["stype"] == "uwsgi":  # uwsgi 启动
            log_file = project['project_config']["logpath"] + "/uwsgi.log"
            logsplit(project["name"], log_file, project["name"])
        elif project['project_config']["stype"] == "gunicorn":  # gunicorn 启动
            log_file = project['project_config']["logpath"] + "/gunicorn_error.log"
            logsplit(project["name"], log_file, project["name"] + "_error")
            log_file2 = project['project_config']["logpath"] + "/gunicorn_acess.log"
            logsplit(project["name"], log_file2, project["name"] + "_acess")
        else:  # 命令行启动或原本的python启动
            log_file = project['project_config']["logpath"] + "/error.log"
            logsplit(project["name"], log_file, project["name"])

    @staticmethod
    def _check_add_domain(site_name, domains) -> dict:
        from panel_site_v2 import panelSite
        ssl_data = panelSite().GetSSL(type("get", tuple(), {"siteName": site_name})())
        if not ssl_data["status"] or not ssl_data.get("cert_data", {}).get("dns", None):
            return {"domains": domains}
        domain_rep = []
        for i in ssl_data["cert_data"]["dns"]:
            if i.startswith("*"):
                _rep = r"^[^\.]+\." + i[2:].replace(".", r"\.")
            else:
                _rep = r"^" + i.replace(".", r"\.")
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
            return {
                "domains": domains,
                "not_ssl": no_ssl,
                "tio": "This site has enabled SSL certificate, but the added domain(s): {} "
                       "cannot match the current certificate. If needed, please reapply for the certificate.".format(
                    str(no_ssl)
                ),
            }
        return {"domains": domains}

    def get_mem_and_cpu(self, pids: list) -> tuple[int, float]:
        mem, cpusum = 0, 0
        for pid in pids:
            res = self.get_process_info_by_pid(pid)
            if "memory_used" in res:
                mem += res["memory_used"]
            if "cpu_percent" in res:
                cpusum += res["cpu_percent"]
        return mem, cpusum

    @staticmethod
    def get_proc_rss(pid) -> int:
        status_path = '/proc/' + str(pid) + '/status'
        if not os.path.exists(status_path):
            return 0
        status_file = public.readFile(status_path)
        if not status_file:
            return 0
        rss = 0
        try:
            rss = int(re.search(r'VmRSS:\s*(\d+)\s*kB', status_file).groups()[0])
        except:
            pass
        rss = int(rss) * 1024
        return rss

    def get_process_info_by_pid(self, pid) -> dict:
        process_info = {}
        try:
            if not os.path.exists('/proc/{}'.format(pid)):
                return process_info
            p = psutil.Process(pid)
            with p.oneshot():
                process_info['memory_used'] = self.get_proc_rss(pid)
                process_info['cpu_percent'] = self.get_cpu_precent(p)
                return process_info
        except:
            return process_info

    def get_cpu_precent(self, p: psutil.Process) -> float:
        """
            @name 获取进程cpu使用率
            @author hwliang<2021-08-09>
            @param p: Process<进程对像>
            @return
        """
        skey = "cpu_pre_{}".format(p.pid)
        old_cpu_times = cache.get(skey)

        process_cpu_time = self.get_process_cpu_time(p.cpu_times())
        if not old_cpu_times:
            cache.set(skey, [process_cpu_time, time.time()], 3600)
            old_cpu_times = cache.get(skey)
            process_cpu_time = self.get_process_cpu_time(p.cpu_times())

        old_process_cpu_time = old_cpu_times[0]
        old_time = old_cpu_times[1]
        new_time = time.time()
        cache.set(skey, [process_cpu_time, new_time], 3600)
        percent = round(
            100.00 * (process_cpu_time - old_process_cpu_time) / (new_time - old_time) / psutil.cpu_count(),
            2
        )
        return percent

    @staticmethod
    def get_process_cpu_time(cpu_times):
        cpu_time = 0.00
        for s in cpu_times:
            cpu_time += s
        return cpu_time

    def get_project_status(self, project_id):
        # 仅使用在项目停止告警中
        project_info = public.M('sites').where('project_type=? AND id=?', ('Python', project_id)).find()
        if not project_info:
            return None, ""
        if self.is_stop_by_user(project_id):
            return True, project_info.get("name", "")
        res = self.get_project_run_state(project_name=project_info.get("name", ""))
        return bool(res), project_info.get("name", "")

    @staticmethod
    def _serializer_of_list(s: list, installed: List[str]) -> List[Dict]:
        return [{
            "version": v.version,
            "type": "stable",
            "installed": True if v.version in installed else False
        } for v in s]

    @check_pyvm_exists
    def list_py_version(self, get: public.dict_obj):
        """
        获取已安装的sdk，可安装的sdk
        """
        force = False
        if "force" in get and get.force in ("1", "true"):
            force = True
        self.pyvm.async_version = True
        res = self.pyvm.python_versions(force)
        install_data = public.M("tasks").where("status in (0, -1) and name LIKE ?", ("install [Python%",)).select()
        install_version = []
        for i in install_data:
            install_version.append(i["name"].replace("Install [Python-", "").replace("]", ""))

        for i in res.get("sdk", {}).get("all", []):
            if i["version"] in install_version:
                i["is_install"] = True
            else:
                i["is_install"] = False

        for i in res.get("sdk", {}).get("streamline", []):
            if i["version"] in install_version:
                i["is_install"] = True
            else:
                i["is_install"] = False

        res.get("sdk", {}).get("all", []).sort(key=lambda x: (x["installed"], x["is_install"]), reverse=True)
        res.get("sdk", {}).get("streamline", []).sort(key=lambda x: (x["installed"], x["is_install"]), reverse=True)
        return public.success_v2(res)

    @staticmethod
    def _parser_version(version: str) -> Optional[str]:
        v_rep = re.compile(r"(?P<target>\d+\.\d{1,2}(\.\d{1,2})?)")
        v_res = v_rep.search(version)
        if v_res:
            return v_res.group("target")
        return None

    @check_pyvm_exists
    def install_py_version(self, get: public.dict_obj) -> Dict:
        """
        安装一个版本的sdk
        """
        version = self._parser_version(getattr(get, "version", ''))
        if version is None:
            return public.fail_v2(public.lang("Version parameter information error"))

        is_pypy = False
        if "is_pypy" in get and get.is_pypy in ("1", "true"):
            is_pypy = True
        log_path = os.path.join(self._logs_path, "py.log")
        out_err = None
        flag = False
        msg = ""
        try:
            out_err = open(log_path, "w")
            self.pyvm.set_std(out_err, out_err)
            self.pyvm.is_pypy = is_pypy
            flag, msg = self.pyvm.api_install(version)
            self.pyvm.set_std(sys.stdout, sys.stderr)
            time.sleep(0.1)
        except:
            pass
        finally:
            if out_err:
                out_err.close()
        return public.return_message(
            0 if flag else -1,
            0,
            public.lang("Install Success") if flag else (msg or public.lang(f"Install Fail, Please Try Again"))
        )

    @check_pyvm_exists
    def async_install_py_version(self, get: public.dict_obj) -> Dict:
        version = self._parser_version(getattr(get, "version", ''))
        if version is None:
            return public.fail_v2(public.lang("Version parameter information error"))

        if os.path.exists("{}/versions/{}".format(self._pyv_path, version)):
            return public.fail_v2(public.lang("The Version is Already Installed"))

        if public.M("tasks").where("status in (0, -1) and name=?", ("Install [Python-{}]".format(version),)).find():
            return public.success_v2(
                public.lang("The install version has been added to the task queue, please wait for completion")
            )
        extended = getattr(get, "extended", '')
        sh_str = "{}/pyenv/bin/python3 {}/class_v2/projectModelV2/btpyvm.py install {} --extend='{}'".format(
            public.get_panel_path(), public.get_panel_path(), version, extended
        )

        if not os.path.exists("/tmp/panelTask.pl"):  # 如果当前任务队列并未执行，就把日志清空
            public.writeFile('/tmp/panelExec.log', '')
        public.M('tasks').add(
            'id,name,type,status,addtime,execstr',
            (None, 'Install [Python-{}]'.format(version), 'execshell', '0', time.strftime('%Y-%m-%d %H:%M:%S'), sh_str)
        )
        public.set_module_logs('python_project', 'async_install_python', 1)
        return public.success_v2(public.lang("The task has been added to the task queue"))

    @check_pyvm_exists
    def uninstall_py_version(self, get: public.dict_obj) -> Dict:
        """
        卸载一个指定版本的sdk
        """
        version = self._parser_version(getattr(get, "version", ''))
        if version is None:
            return public.fail_v2("Version parameter information error")

        is_pypy = False
        if "is_pypy" in get and get.is_pypy in ("1", "true"):
            is_pypy = True

        self.pyvm.is_pypy = is_pypy
        flag, msg = self.pyvm.api_uninstall(version)
        return public.return_message(
            0 if flag else -1,
            0,
            msg if flag else public.lang("Uninstall Fail, Please Try Again")
        )

    def update_all_project(self):
        all_project = public.M('sites').where('project_type=?', ('Python',)).select()
        if not isinstance(all_project, list):
            return
        for p in all_project:
            project_config = json.loads(p["project_config"])
            if project_config["stype"] == "python":
                project_config["project_cmd"] = "{vpath} -u {run_file} {parm} ".format(
                    vpath=self._get_vp_python(project_config["vpath"]),
                    run_file=project_config['rfile'],
                    parm=project_config['parm']
                )
                project_config["stype"] = "command"
                public.M("sites").where("id=?", (p["id"],)).update({"project_config": json.dumps(project_config)})

    @staticmethod
    def _read_requirement_file(requirement_path):
        requirement_dict = {}
        requirement_data = public.read_rare_charset_file(requirement_path)
        if isinstance(requirement_data, str):
            for i in requirement_data.split("\n"):
                tmp_data = i.strip()
                if not tmp_data or tmp_data.startswith("#"):
                    continue
                if re.search(r"-e\s+\.{0,2}/", tmp_data):  # 本地库依赖且为可编辑模式的不安装
                    continue
                if tmp_data.find("git+") != -1:
                    rep_name_list = [re.compile(r"#egg=(?P<name>\S+)"), re.compile(r"/(?P<name>\S+\.git)")]
                    name = tmp_data
                    for tmp_rep in rep_name_list:
                        tmp_name = tmp_rep.search(tmp_data)
                        if tmp_name:
                            name = tmp_name.group("name")
                            break
                    ver = tmp_data
                    for tmp_i in tmp_data.split():
                        if "git+" in tmp_i:
                            ver = tmp_i
                    requirement_dict[name] = ver

                elif tmp_data.find("file:") != -1:
                    file = tmp_data.split("file:", 1)[1]
                    name = os.path.basename(file)
                    requirement_dict[name] = file
                else:
                    if tmp_data.find("==") != -1:
                        n, v = tmp_data.split("==", 1)
                        requirement_dict[n.strip()] = v.strip()
                    else:
                        requirement_dict[tmp_data] = "--"
        return requirement_dict

    # def _read_requirement_file_new(self, requirement_path):
    #     requirement_dict = {}
    #     try:
    #         import requirements # noqa
    #         with open(requirement_path, "r", encoding="utf-8", errors="ignore") as f:
    #             for req in requirements.parse(f):
    #                 if req.name:
    #                     specs_str = ",".join("{}{}".format(op, ver) for op, ver in req.specs) if req.specs else "*"
    #                     requirement_dict[req.name] = specs_str
    #     except ImportError:
    #         # 降级到原始解析方式
    #         requirement_dict = self._read_requirement_file(requirement_path)
    #     except Exception as e:
    #         public.print_log("_read_requirement_file error: {}".format(e))
    #     return requirement_dict

    def get_env_info(self, get):
        try:
            get.validate([
                Param("project_name").String().Require(),
            ], [
                public.validate.trim_filter(),
            ])
            force = False
            if getattr(get, "force", False) in ("1", "true"):
                force = True
            search = getattr(get, "search", "").strip()
            project_name = get.project_name.strip()
        except Exception as ex:
            public.print_log("error info: {}".format(ex))
            return public.fail_v2(str(ex))

        project_info = self.get_project_find(project_name)
        conf = project_info["project_config"]
        pyenv = EnvironmentManager().get_env_py_path(conf.get("python_bin", conf.get("vpath")))
        python_version = pyenv.version
        requirement_path = conf.get("requirement_path", "")
        if requirement_path and os.path.isfile(requirement_path):
            requirement_dict = self._read_requirement_file(requirement_path)
        else:
            requirement_dict = {}
        source_active = pyenv.activate_shell()
        pip_list_data = pyenv.pip_list(force)
        pip_list = []
        for p, v in pip_list_data:
            if p in requirement_dict:
                pip_list.append({"name": p, "version": v, "requirement": requirement_dict.pop(p)})
            else:
                pip_list.append({"name": p, "version": v, "requirement": "--"})

        for k, v in requirement_dict.items():
            pip_list.append({"name": k, "version": "--", "requirement": v})

        if search:
            pip_list = [
                p for p in pip_list if p["name"].lower().find(search.lower()) != -1
            ]
        return public.success_v2({
            "python_version": python_version,
            "requirement_path": requirement_path,
            "pip_list": pip_list,
            "pip_source": self.pip_source_dict,
            "source_active": source_active,
        })

    def modify_requirement(self, get):
        try:
            get.validate([
                Param("project_name").String().Require(),
                Param("requirement_path").String().Require(),
            ], [
                public.validate.trim_filter(),
            ])
            project_name = get.project_name.strip()
            requirement_path = get.requirement_path.rstrip("/")
        except Exception as ex:
            public.print_log("error info: {}".format(ex))
            return public.fail_v2(str(ex))

        project_info = self.get_project_find(project_name)
        conf = project_info["project_config"]
        if not os.path.isfile(requirement_path):
            return public.fail_v2(f"[{project_name}] requirement.txt Not Found!")

        conf["requirement_path"] = requirement_path
        public.M("sites").where("id=?", (project_info["id"],)).update(
            {"project_config": json.dumps(conf)}
        )
        return public.success_v2(public.lang("Set Success"))

    def manage_package(self, get):
        """安装与卸载虚拟环境模块"""
        requirement_path = ""
        package_name = ''
        package_version = ''
        pip_source = "aliyun"
        active = "install"
        try:
            project_name = get.project_name.strip()
            if "package_name" in get and get.package_name:
                package_name = get.package_name.strip()
            if "package_version" in get and get.package_version:
                package_version = get.package_version.strip()
            if "requirements_path" in get and get.requirements_path:
                requirement_path = get.requirements_path.strip()
            if "active" in get and get.active:
                active = get.active.strip()
            if "pip_source" in get and get.pip_source:
                pip_source = get.pip_source.strip()
                if pip_source not in self.pip_source_dict:
                    return public.fail_v2("pip source error")
        except Exception as e:
            return public.fail_v2(f"parameter error: {e}")
        log_file = "{}/pip_{}.log".format(self._logs_path, project_name)
        conf = self._get_project_conf(project_name)
        if not isinstance(conf, dict):
            return public.fail_v2("Project Not Found, Please Try To Refresh The Page")

        pyenv = EnvironmentManager().get_env_py_path(conf.get("python_bin", conf.get("vpath", "")))
        if not pyenv:
            return public.fail_v2("Python environment Not Found")
        public.writeFile(log_file, "")
        if self.prep_status(conf) == "running":
            return public.fail_v2(
                public.lang("Project Environment Installation in Progress.....<br>Please Do Not Operate")
            )
        if not (package_name or requirement_path):
            return public.fail_v2("Parameter Error, package_name or requirement_path is empty")

        if requirement_path:
            if not os.path.isfile(requirement_path):
                return public.fail_v2("requirement.txt Not Found")

        if active not in ("install", "uninstall"):
            return public.fail_v2("active parameter error, must be in ['install', 'uninstall']")

        real_pip_source = self.pip_source_dict[pip_source]
        pyenv.set_pip_source(real_pip_source)
        log_file = "{}/pip_{}.log".format(self._logs_path, project_name)
        log_fd = open(log_file, "w")

        def call_log(log: str) -> None:
            if not log.endswith("\n"):
                log += "\n"
            log_fd.write(log)
            log_fd.flush()

        if requirement_path:
            conf["requirement_path"] = requirement_path
            public.M("sites").where("name=?", (project_name,)).update({"project_config": json.dumps(conf)})
            self.install_requirement(conf, pyenv, call_log)
            log_fd.write("|- Install Finished\n")
            log_fd.close()
            return public.success_v2("Install Finished")

        if active == "install":
            res = pyenv.pip_install(package_name, version=package_version, call_log=call_log)
            log_fd.write("|- Install Finished\n")
            log_fd.close()
            if res is None:
                return public.success_v2("Install Success")
            else:
                return public.fail_v2(f"Install Fail, {res}")
        else:
            if package_name == "pip":
                return public.fail_v2("PIP cannot be uninstalled....")
            res = pyenv.pip_uninstall(package_name, call_log=call_log)
            log_fd.write("|- Uninstall Finished\n")
            log_fd.close()
            if res is None:
                return public.success_v2("Uninstall Success")
            else:
                return public.fail_v2(f"Uninstall Fail, {res}")

    # ————————————————————————————————————
    #              虚拟终端               |
    # ————————————————————————————————————

    def set_export(self, project_name) -> tuple[bool, str]:
        conf = self._get_project_conf(project_name)
        if not conf:
            return False, "Project Not Found!\r\n"
        v_path_bin = conf["vpath"] + "/bin"
        if not os.path.exists(conf["path"]):
            return False, "Project File is Missing!\r\n"
        if not os.path.exists(v_path_bin):
            return False, "Python Virtual Environment is Missing!\r\n"
        pre_v_path_bin = self.__prevent_re(v_path_bin)
        msg = "Virtual Environment is Ready!\r\n"
        _cd_sh = "clear\ncd %s\n" % conf["path"]
        _sh = 'if [[ "$PATH" =~ "^%s:.*" ]]; then { echo "%s"; } else { export PATH="%s:${PATH}"; echo "%s"; } fi\n' % (
            pre_v_path_bin, msg, v_path_bin, msg
        )
        return True, _sh + _cd_sh

    def get_port_status(self, get):
        try:
            conf = self.get_project_find(get.project_name.strip())
            if not conf:
                return public.fail_v2("Project Not Found")
        except:
            return public.fail_v2("Parameter Error")

        pids = self.get_project_run_state(get.project_name.strip())
        if not pids:
            return public.fail_v2(public.lang("Project Not Started"))
        ports = []
        pro_port = str(conf["project_config"]["port"])
        pro_stype = conf["project_config"]["stype"]
        for pid in pids:
            try:
                p = psutil.Process(pid)
                for i in p.connections() if hasattr(p, "connections") else p.net_connections():
                    if pro_stype != "command" and str(i.laddr.port) != pro_port:
                        continue
                    if i.status == "LISTEN" and i.laddr.port not in ports:
                        ports.append(str(i.laddr.port))
            except Exception as e:
                public.print_log(f"Error getting port for pid {pid}: {e}")
                continue
        if not ports:
            return public.success_v2([])
        # 初始化结果字典
        res: Dict[str, Dict] = {
            str(i): {
                "port": i,
                "fire_wall": None,
                "nginx_proxy": None,
            } for i in ports
        }
        # 获取端口规则列表
        from firewallModelV2.comModel import main
        port_list = main().port_rules_list(get)['message']['data']
        # 更新防火墙信息
        for i in port_list:
            if str(i["Port"]) in res:
                res[str(i["Port"])]['fire_wall'] = i
        try:
            # 读取配置文件
            file_path = "{}/nginx/python_{}.conf".format(self._vhost_path, get.project_name)
            config_file = public.readFile(file_path)
            if not config_file:
                public.print_log(f"config_file {file_path} is empty")
                return public.success_v2(list(res.values()))
            # 匹配 location 块
            rep_location = re.compile(r"\s*location\s+([=*~^]*\s+)?/\s*{")
            tmp = rep_location.search(config_file)
            if not tmp:
                public.print_log(f"location bolck not found in config file")
                return public.success_v2(list(res.values()))
            # 找到 location 块结束位置
            end_idx = self.find_nginx_block_end(config_file, tmp.end() + 1)
            if not end_idx:
                public.print_log(f"location end bolck not found in config file")
                return public.success_v2(res)

            block = config_file[tmp.start():end_idx]
            # 获取 proxy_pass 配置
            res_pass = re.compile(r"proxy_pass\s+(?P<pass>\S+)\s*;", re.M)
            res_pass_res = res_pass.search(block)
            if not res_pass_res:
                res_pass_socket = re.compile(r"uwsgi_pass\s+(?P<pass>\S+)\s*;", re.M)
                res_pass_res = res_pass_socket.search(block)
            # 解析端口信息
            res_url = parse_url(res_pass_res.group("pass"))
            # 更新 nginx_proxy 信息
            for i in res:
                if i == str(res_url.port):
                    res[i]['nginx_proxy'] = {
                        "proxy_dir": "/",
                        "status": True,
                        "site_name": get.project_name,
                        "proxy_port": i
                    }
            return public.success_v2(list(res.values()))
        except Exception:
            import traceback
            public.print_log(f"Error {traceback.format_exc()}")
            return public.success_v2(list(res.values()))

    @staticmethod
    def _project_domain_list(project_id: int):
        return public.M('domain').where('pid=?', (project_id,)).select()

    # 添加代理
    def add_server_proxy(self, get):
        if not hasattr(get, "site_name") or not get.site_name.strip():
            return public.fail_v2("site_name Parameter Error")

        project_data = self.get_project_find(get.site_name)
        if not hasattr(get, "proxy_port"):
            return public.fail_v2("proxy_port Parameter Error")
        else:
            if 65535 < int(get.proxy_port) < 0:
                return public.fail_v2("Please enter the correct port range")
        if not hasattr(get, "status"):
            return public.fail_v2("status Parameter Error")

        file_path = "{}/nginx/python_{}.conf".format(self._vhost_path, get.site_name)
        config_file = public.readFile(file_path)
        if not isinstance(config_file, str):
            return public.fail_v2("Project config Not Found")
        project_conf = project_data["project_config"]

        if self.prep_status(project_conf) == "running":
            raise HintException(
                public.lang("Project Environment Installation in Progress.....<br>Please Do Not Operate")
            )

        if int(get.status):
            res = self.ChangeProjectConf(public.to_dict_obj({
                "name": get.site_name,
                "data": {
                    "pjname": get.site_name,
                    "port": get.proxy_port,
                }
            }))
            if res.get("status") != 0:
                return public.fail_v2("Failed to update proxy configuration, please try again")
            # self.set_config(get.site_name, is_modify=True)
        else:
            is_modify = "close" if project_data["project_config"]["stype"] != "command" else False
            self.set_config(get.site_name, is_modify=is_modify)
        return public.success_v2("Proxy configuration updated successfully")

    @staticmethod
    def find_nginx_block_end(data: str, start_idx: int) -> Optional[int]:
        if len(data) < start_idx + 1:
            return None

        level = 1
        line_start = 0
        for i in range(start_idx + 1, len(data)):
            if data[i] == '\n':
                line_start = i + 1
            if data[i] == '{' and line_start and data[line_start: i].find("#") == -1:  # 没有注释的下一个{
                level += 1
            elif data[i] == '}' and line_start and data[line_start: i].find("#") == -1:  # 没有注释的下一个}
                level -= 1
            if level == 0:
                return i

        return None


class PyenvSshTerminal(ssh_terminal):
    _set_python_export = None

    def send(self):
        """
            @name 写入数据到缓冲区
            @author hwliang<2020-08-07>
            @return void
        """
        try:
            while self._ws.connected:
                if self._s_code:
                    time.sleep(0.1)
                    continue
                client_data = self._ws.receive()
                if not client_data: continue
                if client_data == '{}': continue
                if len(client_data) > 10:
                    if client_data.find('{"host":"') != -1:
                        continue
                    if client_data.find('"resize":1') != -1:
                        self.resize(client_data)
                        continue
                    if client_data.find('{"pj_name"') != -1:
                        client_data = self.__set_export(client_data)
                        if not client_data:
                            continue

                self._ssh.send(client_data)
        except Exception as ex:
            ex = str(ex)

            if ex.find('_io.BufferedReader') != -1:
                self.debug('read from websocket error, retrying')
                self.send()
                return
            elif ex.find('closed') != -1:
                self.debug('session closed')
            else:
                self.debug('write to buffer error: {}'.format(ex))

        if not self._ws.connected:
            self.debug('client websocket disconnected')
        self.close()

    def __set_export(self, client_data):
        _data = json.loads(client_data)
        flag, msg = main().set_export(_data["pj_name"])
        if not flag:
            self._ws.send(msg)
            return None
        return msg
