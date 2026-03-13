# coding: utf-8
# -------------------------------------------------------------------
# aaPanel
# -------------------------------------------------------------------
# Copyright (c) 2014-2099 aaPanel(www.aapanel.com) All rights reserved.
# -------------------------------------------------------------------
# Author: aapanel
# -------------------------------------------------------------------
# ------------------------------
# Python Env app
# ------------------------------
import os.path
import sys
import json
import re

if "/www/server/panel/class" not in sys.path:
    sys.path.insert(0, "/www/server/panel/class")

if "/www/server/panel" not in sys.path:
    sys.path.insert(0, "/www/server/panel")

from mod.project.python.pyenv_tool import (
    EnvironmentReporter,
    EnvironmentManager,
    _SYS_BIN_PATH,
    python_manager_path,
    pyenv_path,
)
from mod.base import json_response
EnvironmentReporter().init_report()

class main:
    @staticmethod
    def create_python_env(get):
        try:
            venv_name = get.venv_name.strip()
            src_python_bin = get.python_bin.strip()
            if "ps" in get:
                ps = get.ps.strip()
            else:
                ps = ""
        except:
            return json_response(False, 'Invalid parameters')

        if not re.match(r'^[a-zA-Z0-9_.-]+$', venv_name):
            return json_response(False, "Virtual environment name contains invalid characters")

        ws_send = None
        if "_ws" in get:
            ws_send = lambda x: get._ws.send(json.dumps({"callback": "create_python_env", "result": {"log": x}}))
        res = EnvironmentManager().create_python_env(venv_name, src_python_bin, ps, ws_send)
        if isinstance(res, str):
            return json_response(False, res)
        try:
            import public
            public.set_module_logs('python_project_env', 'create_python_env', 1)
        except:
            pass
        return json_response(True, msg="Created successfully")

    @staticmethod
    def list_environment(get):
        if get and get.get("sort_not_use/s") in ("1", "true"):
            sort_not_use = True
        else:
            sort_not_use = False

        em = EnvironmentManager()
        all_project_map = em.all_python_project_map()
        env_map = {
            i.bin_path: i.to_dict(
                project_name=all_project_map.get(i.bin_path, []),
                can_remove=i.can_remove,
                can_create=i.can_create,
                can_set_default=i.can_set_default,
                path_name=i.path_name,
                from_panel=any((i.bin_path.startswith(x) for x in
                                (python_manager_path(), pyenv_path()))) and i.env_type == "system"
            ) for i in em.all_env
        }
        data = list(env_map.values())
        if sort_not_use:
            data.sort(key=lambda x: (
                len(x["project_name"]),
                ("venv", "conda", "system").index(x["type"]),
                any(i == os.path.dirname(x["bin_path"]) for i in _SYS_BIN_PATH)
            ))
        else:
            data.sort(key=lambda x: (
                0 - len(x["project_name"]),
                ("venv", "conda", "system").index(x["type"]),
                any(i == os.path.dirname(x["bin_path"]) for i in _SYS_BIN_PATH)
            ))
        for i in data[::-1]:
            i["name"] = i["venv_name"] or i["path_name"] or i["version"]
            if i["type"] == "venv":
                i["system_data"] = env_map[i["system_path"]]
            i["can_remove"] = False if i["project_name"] else i["can_remove"]
        now_env = em.get_default_python_env()
        if now_env:
            now_env = env_map[now_env.bin_path]
            now_env["can_set_default"] = False

        return json_response(True, data={"env_list": data, "now_env": now_env})

    @staticmethod
    def add_environment(get):
        try:
            add_type = get.add_type.strip()
            path = get.path.strip()
        except:
            return json_response(False, 'Invalid parameters')
        res = EnvironmentManager().add_python_env(add_type, path)
        if isinstance(res, str):
            return json_response(False, res)
        try:
            import public
            public.set_module_logs('python_project_env', 'add_environment', 1)
        except:
            pass
        return json_response(True, msg="Added successfully")

    @staticmethod
    def remove_environment(get):
        try:
            path_data = get.path_data.strip()
        except:
            return json_response(False, 'Invalid parameters')
        if not path_data:
            return json_response(False, 'Invalid parameters')
        em = EnvironmentManager()
        if "," in path_data:
            path_list = path_data.split(",")
            res = em.multi_remove_env(*path_list)
            status = all(x.get("status") for x in res)
            if not status:
                err_msg = "\n".join([x.get("msg", "") for x in res if not x.get("status")])
                return json_response(False, err_msg)
            return json_response(status, data=res)
        else:
            res = em.multi_remove_env(path_data)
            for r in res:
                if r.get("status"):
                    return json_response(True, msg="Removed successfully")
                return json_response(False, r.get("msg", "Failed to remove"))
            return json_response(True, msg="Removed successfully")

    @staticmethod
    def set_environment_default(get):
        try:
            path = get.path.strip()
        except:
            return json_response(False, 'Invalid parameters')
        if not path or path == "close":
            path = ""
        em = EnvironmentManager()
        res = em.set_python2env(path)
        if not path:
            if not res:
                return json_response(True, msg="Disabled successfully")
            else:
                return json_response(False, res)
        else:
            if not res:
                return json_response(True, msg="Set successfully")
            else:
                return json_response(False, res)

    @staticmethod
    def set_environment_ps(get):
        try:
            path = get.path.strip()
            ps = get.ps.strip()
        except:
            return json_response(False, 'Invalid parameters')
        if not path or not ps:
            return json_response(False, 'Invalid parameters')
        em = EnvironmentManager()
        res = em.set_python_env_ps(path, ps)
        if not res:
            return json_response(True, msg="Set successfully")
        else:
            return json_response(False, res)
