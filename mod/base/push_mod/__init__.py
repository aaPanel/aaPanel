import json
import os
from typing import Dict, Union

from .mods import TaskConfig, TaskTemplateConfig, TaskRecordConfig, SenderConfig, load_task_template_by_config, \
    load_task_template_by_file, UPDATE_MOD_PUSH_FILE, UPDATE_VERSION_FILE, PUSH_DATA_PATH
from .base_task import BaseTask
from .send_tool import WxAccountMsg, WxAccountLoginMsg, WxAccountMsgBase
from .system import PushSystem, get_push_public_data, push_by_task_keyword, push_by_task_id
from .manager import PushManager
from .util import read_file, write_file


__all__ = [
    "TaskConfig",
    "TaskTemplateConfig",
    "TaskRecordConfig",
    "SenderConfig",
    "load_task_template_by_config",
    "load_task_template_by_file",
    "BaseTask",
    "WxAccountMsg",
    "WxAccountLoginMsg",
    "WxAccountMsgBase",
    "PushSystem",
    "get_push_public_data",
    "PushManager",
    "push_by_task_keyword",
    "push_by_task_id",
    "UPDATE_MOD_PUSH_FILE",
    "update_mod_push_system",
    "UPDATE_VERSION_FILE",
    "PUSH_DATA_PATH",
    "get_default_module_dict",
]


def update_mod_push_system():
    if os.path.exists(UPDATE_MOD_PUSH_FILE):
        return

    # 只将已有的告警任务("site_push", "system_push", "database_push") 移动

    try:
        push_data = json.loads(read_file("/www/server/panel/class/push/push.json"))
    except:
        return

    if not isinstance(push_data, dict):
        return
    pmgr = PushManager()
    default_module_dict = get_default_module_dict()
    for key, value in push_data.items():
        if key == "site_push":
            _update_site_push(value, pmgr, default_module_dict)
        elif key == "system_push":
            _update_system_push(value, pmgr, default_module_dict)
        elif key == "database_push":
            _update_database_push(value, pmgr, default_module_dict)
        elif key == "rsync_push":
            _update_rsync_push(value, pmgr, default_module_dict)
        elif key == "load_balance_push":
            _update_load_push(value, pmgr, default_module_dict)
        elif key == "task_manager_push":
            _update_task_manager_push(value, pmgr, default_module_dict)

    write_file(UPDATE_MOD_PUSH_FILE, "")


def get_default_module_dict():
    res = {}
    # wx_account_list = []
    for data in SenderConfig().config:
        if not data["used"]:
            continue
        if data.get("original", False):
            res[data["sender_type"]] = data["id"]

        if data["sender_type"] == "webhook":
            res[data["data"].get("title")] = data["id"]

        # if data["sender_type"] == "wx_account":
        #     wx_account_list.append(data)

    # wx_account_list.sort(key=lambda x: x.get("data", {}).get("create_time", ""))
    # if wx_account_list:
    #     res["wx_account"] = wx_account_list[0]["id"]

    return res


def _update_site_push(old_data: Dict[str, Dict[str, Union[str, int, float, list]]],
                      pmgr: PushManager,
                      df_mdl: Dict[str, str]):

    for k, v in old_data.items():
        sender_list = [df_mdl[i.strip()] for i in v.get("module", "").split(",") if i.strip() in df_mdl]
        if v["type"] == "ssl":
            push_data = {
                "template_id": "1",
                "task_data": {
                    "status": bool(v.get("status", True)),
                    "sender": sender_list,
                    "task_data": {
                        "project": v.get("project", "all"),
                        "cycle": v.get("cycle", 15)
                    },
                    "number_rule": {
                        "total": v.get("push_count", 1)
                    }
                }
            }
            pmgr.set_task_conf_data(push_data)

        elif v["type"] == "site_endtime":
            push_data = {
                "template_id": "2",
                "task_data": {
                    "status": bool(v.get("status", True)),
                    "sender": sender_list,
                    "task_data": {
                        "cycle": v.get("cycle", 7)
                    },
                    "number_rule": {
                        "total": v.get("push_count", 1)
                    }
                }
            }
            pmgr.set_task_conf_data(push_data)

        elif v["type"] == "panel_pwd_endtime":
            push_data = {
                "template_id": "3",
                "task_data": {
                    "status": bool(v.get("status", True)),
                    "sender": sender_list,
                    "task_data": {
                        "cycle": v.get("cycle", 15),
                        "interval": 600
                    },
                    "number_rule": {
                        "total": v.get("push_count", 1)
                    }
                }
            }
            pmgr.set_task_conf_data(push_data)

        elif v["type"] == "ssh_login_error":
            push_data = {
                "template_id": "4",
                "task_data": {
                    "status": bool(v.get("status", True)),
                    "sender": sender_list,
                    "task_data": {
                        "cycle": v.get("cycle", 30),
                        "count": v.get("count", 3),
                        "interval": v.get("interval", 600)
                    },
                    "number_rule": {
                        "day_num": v.get("day_limit", 3)
                    }
                }
            }
            pmgr.set_task_conf_data(push_data)

        elif v["type"] == "services":
            push_data = {
                "template_id": "5",
                "task_data": {
                    "status": bool(v.get("status", True)),
                    "sender": sender_list,
                    "task_data": {
                        "project": v.get("project", "nginx"),
                        "count": v.get("count", 3),
                        "interval": v.get("interval", 600)
                    },
                    "number_rule": {
                        "day_num": v.get("day_limit", 3)
                    }
                }
            }
            pmgr.set_task_conf_data(push_data)

        elif v["type"] == "panel_safe_push":
            push_data = {
                "template_id": "6",
                "task_data": {
                    "status": bool(v.get("status", True)),
                    "sender": sender_list,
                    "task_data": {},
                    "number_rule": {
                        "day_num": v.get("day_limit", 3)
                    }
                }
            }
            pmgr.set_task_conf_data(push_data)

        elif v["type"] == "ssh_login":
            push_data = {
                "template_id": "7",
                "task_data": {
                    "status": bool(v.get("status", True)),
                    "sender": sender_list,
                    "task_data": {},
                    "number_rule": {}
                }
            }
            pmgr.set_task_conf_data(push_data)

        elif v["type"] == "panel_login":
            push_data = {
                "template_id": "8",
                "task_data": {
                    "status": bool(v.get("status", True)),
                    "sender": sender_list,
                    "task_data": {},
                    "number_rule": {}
                }
            }
            pmgr.set_task_conf_data(push_data)

        elif v["type"] == "project_status":
            push_data = {
                "template_id": "9",
                "task_data": {
                    "status": bool(v.get("status", True)),
                    "sender": sender_list,
                    "task_data": {
                        "cycle": v.get("cycle", 1),
                        "project": v.get("project", 0),
                        "count": v.get("count", 2) if v.get("count", 2) not in (1, 2) else 2,
                        "interval": v.get("interval", 600)
                    },
                    "number_rule": {
                        "day_num": v.get("push_count", 3)
                    }
                }
            }
            pmgr.set_task_conf_data(push_data)

        elif v["type"] == "panel_update":
            push_data = {
                "template_id": "10",
                "task_data": {
                    "status": bool(v.get("status", True)),
                    "sender": sender_list,
                    "task_data": {},
                    "number_rule": {
                        "day_num": 1
                    }
                }
            }
            pmgr.set_task_conf_data(push_data)

    send_type = None
    login_send_type_conf = "/www/server/panel/data/panel_login_send.pl"
    if os.path.exists(login_send_type_conf):
        send_type = read_file(login_send_type_conf).strip()
    else:
        # user_info["server_id"]之前的
        if os.path.exists("/www/server/panel/data/login_send_type.pl"):
            send_type = read_file("/www/server/panel/data/login_send_type.pl")
        else:
            if os.path.exists('/www/server/panel/data/login_send_mail.pl'):
                send_type = "mail"
            if os.path.exists('/www/server/panel/data/login_send_dingding.pl'):
                send_type = "dingding"

    if isinstance(send_type, str):
        sender_list = [df_mdl[i.strip()] for i in send_type.split(",") if i.strip() in df_mdl]
        push_data = {
            "template_id": "8",
            "task_data": {
                "status": True,
                "sender": sender_list,
                "task_data": {},
                "number_rule": {}
            }
        }
        pmgr.set_task_conf_data(push_data)

    login_send_type_conf = "/www/server/panel/data/ssh_send_type.pl"
    if os.path.exists(login_send_type_conf):
        ssh_send_type = read_file(login_send_type_conf).strip()
        if isinstance(ssh_send_type, str):
            sender_list = [df_mdl[i.strip()] for i in ssh_send_type.split(",") if i.strip() in df_mdl]
            push_data = {
                "template_id": "7",
                "task_data": {
                    "status": True,
                    "sender": sender_list,
                    "task_data": {},
                    "number_rule": {}
                }
            }
            pmgr.set_task_conf_data(push_data)
    return


def _update_system_push(old_data: Dict[str, Dict[str, Union[str, int, float, list]]],
                        pmgr: PushManager,
                        df_mdl: Dict[str, str]):

    for k, v in old_data.items():
        sender_list = [df_mdl[i.strip()] for i in v.get("module", "").split(",") if i.strip() in df_mdl]
        if v["type"] == "disk":
            push_data = {
                "template_id": "20",
                "task_data": {
                    "status": bool(v.get("status", True)),
                    "sender": sender_list,
                    "task_data": {
                        "project": v.get("project", "/"),
                        "cycle": v.get("cycle", 2) if v.get("cycle", 2) not in (1, 2) else 2,
                        "count": v.get("count", 80),
                    },
                    "number_rule": {
                        "total": v.get("push_count", 3)
                    }
                }
            }
            pmgr.set_task_conf_data(push_data)

        if v["type"] == "disk":
            push_data = {
                "template_id": "21",
                "task_data": {
                    "status": bool(v.get("status", True)),
                    "sender": sender_list,
                    "task_data": {
                        "cycle": v.get("cycle", 5) if v.get("cycle", 5) not in (3, 5, 15) else 5,
                        "count": v.get("count", 80),
                    },
                    "number_rule": {
                        "total": v.get("push_count", 3)
                    }
                }
            }
            pmgr.set_task_conf_data(push_data)

        if v["type"] == "load":
            push_data = {
                "template_id": "22",
                "task_data": {
                    "status": bool(v.get("status", True)),
                    "sender": sender_list,
                    "task_data": {
                        "cycle": v.get("cycle", 5) if v.get("cycle", 5) not in (1, 5, 15) else 5,
                        "count": v.get("count", 80),
                    },
                    "number_rule": {
                        "total": v.get("push_count", 3)
                    }
                }
            }
            pmgr.set_task_conf_data(push_data)

        if v["type"] == "mem":
            push_data = {
                "template_id": "23",
                "task_data": {
                    "status": bool(v.get("status", True)),
                    "sender": sender_list,
                    "task_data": {
                        "cycle": v.get("cycle", 5) if v.get("cycle", 5) not in (3, 5, 15) else 5,
                        "count": v.get("count", 80),
                    },
                    "number_rule": {
                        "total": v.get("push_count", 3)
                    }
                }
            }
            pmgr.set_task_conf_data(push_data)

    return


def _update_database_push(old_data: Dict[str, Dict[str, Union[str, int, float, list]]],
                          pmgr: PushManager,
                          df_mdl: Dict[str, str]):

    for k, v in old_data.items():
        sender_list = [df_mdl[i.strip()] for i in v.get("module", "").split(",") if i.strip() in df_mdl]
        if v["type"] == "mysql_pwd_endtime":
            push_data = {
                "template_id": "30",
                "task_data": {
                    "status": bool(v.get("status", True)),
                    "sender": sender_list,
                    "task_data": {
                        "project": v.get("project", []),
                        "cycle": v.get("cycle", 15),
                    },
                    "number_rule": {}
                }
            }
            pmgr.set_task_conf_data(push_data)

        elif v["type"] == "mysql_replicate_status":
            push_data = {
                "template_id": "31",
                "task_data": {
                    "status": bool(v.get("status", True)),
                    "sender": sender_list,
                    "task_data": {
                        "project": v.get("project", []),
                        "count": v.get("cycle", 15),
                        "interval": v.get("interval", 600)
                    },
                    "number_rule": {}
                }
            }
            pmgr.set_task_conf_data(push_data)

    return None


def _update_rsync_push(
        old_data: Dict[str, Dict[str, Union[str, int, float, list]]],
        pmgr: PushManager,
        df_mdl: Dict[str, str]):

    for k, v in old_data.items():
        sender_list = [df_mdl[i.strip()] for i in v.get("module", "").split(",") if i.strip() in df_mdl]
        push_data = {
            "template_id": "40",
            "task_data": {
                "status": bool(v.get("status", True)),
                "sender": sender_list,
                "task_data": {
                    "interval": v.get("interval", 600)
                },
                "number_rule": {
                    "day_num": v.get("push_count", 3)
                }
            }
        }
        pmgr.set_task_conf_data(push_data)


def _update_load_push(
        old_data: Dict[str, Dict[str, Union[str, int, float, list]]],
        pmgr: PushManager,
        df_mdl: Dict[str, str]):

    for k, v in old_data.items():
        sender_list = [df_mdl[i.strip()] for i in v.get("module", "").split(",") if i.strip() in df_mdl]
        push_data = {
            "template_id": "50",
            "task_data": {
                "status": bool(v.get("status", True)),
                "sender": sender_list,
                "task_data": {
                    "project": v.get("project", ""),
                    "cycle": v.get("cycle", "200|301|302|403|404")
                },
                "number_rule": {
                    "day_num": v.get("push_count", 2)
                }
            }
        }

        pmgr.set_task_conf_data(push_data)


def _update_task_manager_push(
        old_data: Dict[str, Dict[str, Union[str, int, float, list]]],
        pmgr: PushManager,
        df_mdl: Dict[str, str]):

    for k, v in old_data.items():
        sender_list = [df_mdl[i.strip()] for i in v.get("module", "").split(",") if i.strip() in df_mdl]
        template_id_dict = {
            "task_manager_cpu": "60",
            "task_manager_mem": "61",
            "task_manager_process": "62"
        }
        if v["type"] in template_id_dict:
            push_data = {
                "template_id": template_id_dict[v["type"]],
                "task_data": {
                    "status": bool(v.get("status", True)),
                    "sender": sender_list,
                    "task_data": {
                        "project": v.get("project", ""),
                        "count": v.get("count", 80),
                        "interval": v.get("count", 600),
                    },
                    "number_rule": {
                        "day_num": v.get("push_count", 3)
                    }
                }
            }
            pmgr.set_task_conf_data(push_data)

