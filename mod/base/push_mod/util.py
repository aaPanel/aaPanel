import sys
from typing import Optional, Callable

if "/www/server/panel/class" not in sys.path:
    sys.path.insert(0, "/www/server/panel/class")

import public
from db import Sql
import os
from sslModel import certModel


def write_file(filename: str, s_body: str, mode='w+') -> bool:
    """
    写入文件内容
    @filename 文件名
    @s_body 欲写入的内容
    return bool 若文件不存在则尝试自动创建
    """
    try:
        fp = open(filename, mode=mode)
        fp.write(s_body)
        fp.close()
        return True
    except:
        try:
            fp = open(filename, mode=mode, encoding="utf-8")
            fp.write(s_body)
            fp.close()
            return True
        except:
            return False


def read_file(filename, mode='r') -> Optional[str]:
    """
    读取文件内容
    @filename 文件名
    return string(bin) 若文件不存在，则返回None
    """
    import os
    if not os.path.exists(filename):
        return None
    fp = None
    try:
        fp = open(filename, mode=mode)
        f_body = fp.read()
    except:
        return None
    finally:
        if fp and not fp.closed:
            fp.close()
    return f_body


ExecShell: Callable = public.ExecShell

write_log: Callable = public.WriteLog

Sqlite: Callable = Sql

GET_CLASS: Callable = public.dict_obj

debug_log: Callable = public.print_log

get_config_value: Callable = public.GetConfigValue

get_server_ip: Callable = public.get_server_ip

get_network_ip: Callable = public.get_network_ip

format_date: Callable = public.format_date

public_get_cache_func: Callable = public.get_cache_func

public_set_cache_func: Callable = public.set_cache_func

public_get_user_info: Callable = public.get_user_info

public_http_post = public.httpPost

panel_version = public.version

try:
    get_cert_list = certModel.main().get_cert_list
    to_dict_obj = public.to_dict_obj

except:
    public.print_log(public.get_error_info())


def get_client_ip() -> str:
    return public.GetClientIp()


class _DB:

    def __call__(self, table: str):
        import db
        with db.Sql() as t:
            t.table(table)
            return t


DB = _DB()


def check_site_status(web):
    panelPath = '/www/server/panel/'
    os.chdir(panelPath)
    sys.path.insert(0, panelPath)

    if web['project_type'] == "Java":
        from mod.project.java.projectMod import main as java
        if not java().get_project_stat(web)['pid']:
            return None
    if web['project_type'] == "Node":
        from projectModelV2.nodejsModel import main as nodejs
        if not nodejs().get_project_run_state(project_name=web['name']):
            return None
    if web['project_type'] == "Go":
        from projectModel.goModel import main as go  # NOQA
        if not go().get_project_run_state(project_name=web['name']):
            return None
    if web['project_type'] == "Python":
        from projectModelV2.pythonModel import main as python
        if not python().get_project_run_state(project_name=web['name']):
            return None
    if web['project_type'] == "Other":
        from projectModel.otherModel import main as other  # NOQA
        if not other().get_project_run_state(project_name=web['name']):
            return None
    return True


def get_db_by_file(file: str):
    import db
    if not os.path.exists(file):
        return None
    db_obj = db.Sql()
    db_obj._Sql__DB_FILE = file
    return db_obj


def generate_fields(template: dict, add_type: str) -> dict:
    """"动态表单生成附加选项 hook"""
    if add_type not in [
        "restart", "module",
    ]:
        return template
    if add_type == "restart":
        template = generate_restart_fields(template)
    elif add_type == "module":
        template = generate_module_fields(template)
    return template


def generate_restart_fields(template: dict) -> dict:
    """动态表单生成重启服务 hook 选项"""
    from script.restart_services import SERVICES_MAP, ServicesHelper
    f = {
        "attr": "after_hook",
        "name": "After the alarm excutes",
        "suffix": "select after alarm action (Optional)",
        "type": "multiple-select",
        "items": [
            {
                "title": f"Restart {x}",
                "type": "restart",
                "value": x
            } for x in SERVICES_MAP.keys() if ServicesHelper(x).is_install
        ],
        "default": []
    }
    if "field" in template:
        template["field"].append(f)
    else:
        template["field"] = [f]

    if "sorted" in template and isinstance(template["sorted"], list):
        if ["after_hook"] not in template["sorted"]:
            template["sorted"].append(["after_hook"])
    elif "sorted" not in template:
        template["sorted"] = [["after_hook"]]
    else:
        template["sorted"] = [template["sorted"], ["after_hook"]]
    return template


def generate_module_fields(template: dict) -> dict:
    """动态表单生成模块调用 hook 选项"""
    # todo
    return template
