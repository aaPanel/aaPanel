# coding: utf-8
# -------------------------------------------------------------------
# aapanel
# -------------------------------------------------------------------
# Copyright (c) 2015-2017 aapanel(http:#bt.cn) All rights reserved.
# -------------------------------------------------------------------
# Author: baozi <baozi@bt.cn>
# -------------------------------------------------------------------
# 新告警的所有数据库操作
# ------------------------------
import json
import os
import types
from typing import Any, Dict, Optional, List
from threading import Lock
from uuid import uuid4

import fcntl

from .util import Sqlite, write_log, read_file, write_file

_push_db_lock = Lock()


# 代替 class/db.py 中， 离谱的两个query函数
def msg_db_query_func(self, sql, param=()):
    # 执行SQL语句返回数据集
    self._Sql__GetConn()
    try:
        return self._Sql__DB_CONN.execute(sql, self._Sql__to_tuple(param))
    except Exception as ex:
        return "error: " + str(ex)


def get_push_db():
    db_file = "/www/server/panel/data/db/mod_push.db"
    if not os.path.isdir(os.path.dirname(db_file)):
        os.makedirs(os.path.dirname(db_file))

    db = Sqlite()
    setattr(db, "_Sql__DB_FILE", db_file)
    setattr(db, "query", types.MethodType(msg_db_query_func, db))
    return db


def get_table(table_name: str):
    db = get_push_db()
    db.table = table_name
    return db


def lock_push_db():
    with open("/www/server/panel/data/db/mod_push.db", mode="rb") as msg_fd:
        fcntl.flock(msg_fd.fileno(), fcntl.LOCK_EX)
        _push_db_lock.locked()


def unlock_push_db():
    with open("/www/server/panel/data/db/mod_push.db", mode="rb") as msg_fd:
        fcntl.flock(msg_fd.fileno(), fcntl.LOCK_UN)
        _push_db_lock.acquire()


def push_db_locker(func):
    def inner_func(*args, **kwargs):
        lock_push_db()
        try:
            res = func(*args, **kwargs)
        except Exception as e:
            unlock_push_db()  # 即使 报错了 也先解锁再操作
            raise e
        else:
            unlock_push_db()
        return res

    return inner_func


DB_INIT_ERROR = False

PANEL_PATH = "/www/server/panel"
PUSH_DATA_PATH = "{}/data/mod_push_data".format(PANEL_PATH)
UPDATE_VERSION_FILE = "{}/update_panel.pl".format(PUSH_DATA_PATH)
UPDATE_MOD_PUSH_FILE = "{}/update_mod.pl".format(PUSH_DATA_PATH)


class BaseConfig:
    config_file_path = ""
    # config_file_path = "/www/server/panel/data/mod_push_data/task.json"
    # /www/server/panel/data/mod_push_data/sender.json

    def __init__(self):
        if not os.path.exists(PUSH_DATA_PATH):
            os.makedirs(PUSH_DATA_PATH)
        self._config: Optional[List[Dict[str, Any]]] = None

    @property
    def config(self) -> List[Dict[str, Any]]:
        if self._config is None:

            try:
                self._config = json.loads(read_file(self.config_file_path))
            except:
                self._config = []
        return self._config

    def save_config(self) -> None:
        write_file(self.config_file_path, json.dumps(self.config))

    @staticmethod
    def nwe_id() -> str:
        return uuid4().hex[::2]

    def get_by_id(self, target_id: str) -> Optional[Dict[str, Any]]:
        for i in self.config:
            if i.get("id", None) == target_id:
                return i


class TaskTemplateConfig(BaseConfig):
    config_file_path = "{}/task_template.json".format(PUSH_DATA_PATH)


class TaskConfig(BaseConfig):
    config_file_path = "{}/task.json".format(PUSH_DATA_PATH)

    def get_by_keyword(self, source: str, keyword: str) -> Optional[Dict[str, Any]]:
        for i in self.config:
            if i.get("source", None) == source and i.get("keyword", None) == keyword:
                return i


class TaskRecordConfig(BaseConfig):
    config_file_path_fmt = "%s/task_record_{}.json" % PUSH_DATA_PATH

    def __init__(self, task_id: str):
        super().__init__()
        self.config_file_path = self.config_file_path_fmt.format(task_id)


class SenderConfig(BaseConfig):
    config_file_path = "{}/sender.json".format(PUSH_DATA_PATH)

    def __init__(self):
        super(SenderConfig, self).__init__()
        if not os.path.exists(self.config_file_path):
            write_file(self.config_file_path, json.dumps([{
                "id": self.nwe_id(),
                "used": True,
                "sender_type": "sms",
                "data": {},
                "original": True
            }]))


def init_db():
    global DB_INIT_ERROR
    # id  模板id 必须唯一, 后端开发需要协商
    # ver  模板版本号， 用于更新
    # used  是否在使用用
    # source  来源， 如Waf, rsync
    # title  标题
    # load_cls  要加载的类，或者从那种调用方法中获取到任务处理对象
    # template  给前端，用于展示的数据
    # default  默认数据，用于数据过滤， 和默认值
    # unique  是否仅可唯一设置
    # create_time 创建时间
    create_task_template_sql = (
        "CREATE TABLE IF NOT EXISTS 'task_template' ("
        "'id' INTEGER PRIMARY KEY AUTOINCREMENT, "
        "'ver' TEXT NOT NULL DEFAULT '1.0.0', "
        "'used' INTEGER NOT NULL DEFAULT 1, "
        "'source' TEXT NOT NULL DEFAULT 'site_push', "
        "'title' TEXT NOT NULL DEFAULT '', "
        "'load_cls' TEXT NOT NULL DEFAULT '{}', "
        "'template' TEXT NOT NULL DEFAULT '{}', "
        "'default' TEXT NOT NULL DEFAULT '{}', "
        "'send_type_list' TEXT NOT NULL DEFAULT '[]', "
        "'unique' INTEGER NOT NULL DEFAULT 0, "
        "'create_time' INTEGER NOT NULL DEFAULT (strftime('%s'))"
        ");"
    )
    # source 来源， 例如waf(防火墙), rsync(文件同步)
    # keyword 关键词， 不同的来源在使用中可以以此查出具体的任务，需要每个来源自己约束
    # task_data 任务数据字典，字段可以自由设计
    # sender 告警通道信息，为字典，可通过get_by_func字段指定从某个函数获取，用于发送
    # time_rule 告警的时间规则，包含 间隔时间(send_interval), (time-range)
    # number_rule 告警的次数规则，包含 每日次数(day_num), 总次数(total), 通过函数判断(get_by_func)
    # status 状态是否开启
    # pre_hook, after_hook 前置处理和后置处理
    # record_time, 告警记录存储时间， 默认为0， 认为长时间储存
    # last_check, 上次执行检查的时间
    # last_send, 上次次发送时间
    # number_data, 发送次数信息
    create_task_sql = (
        "CREATE TABLE IF NOT EXISTS 'task' ("
        "'id' INTEGER PRIMARY KEY AUTOINCREMENT, "
        "'template_id' INTEGER NOT NULL DEFAULT 0, "
        "'source' TEXT NOT NULL DEFAULT '', "
        "'keyword' TEXT NOT NULL DEFAULT '', "
        "'title' TEXT NOT NULL DEFAULT '', "
        "'task_data' TEXT NOT NULL DEFAULT '{}', "
        "'sender' TEXT NOT NULL DEFAULT '[]', "
        "'time_rule' TEXT NOT NULL DEFAULT '{}', "
        "'number_rule' TEXT NOT NULL DEFAULT '{}', "
        "'status' INTEGER NOT NULL DEFAULT 1, "
        "'pre_hook' TEXT NOT NULL DEFAULT '{}', "
        "'after_hook' TEXT NOT NULL DEFAULT '{}', "
        "'last_check' INTEGER NOT NULL DEFAULT 0, "
        "'last_send' INTEGER NOT NULL DEFAULT 0, "
        "'number_data' TEXT NOT NULL DEFAULT '{}', "
        "'create_time' INTEGER NOT NULL DEFAULT (strftime('%s')), "
        "'record_time' INTEGER NOT NULL DEFAULT 0"
        ");"
    )

    create_task_record_sql = (
        "CREATE TABLE IF NOT EXISTS 'task_record' ("
        "'id' INTEGER PRIMARY KEY AUTOINCREMENT, "
        "'template_id' INTEGER NOT NULL DEFAULT 0, "
        "'task_id' INTEGER NOT NULL DEFAULT 0, "
        "'do_send' TEXT NOT NULL DEFAULT '{}', "
        "'send_data' TEXT NOT NULL DEFAULT '{}', "
        "'result' TEXT NOT NULL DEFAULT '{}', "
        "'create_time' INTEGER NOT NULL DEFAULT (strftime('%s'))"
        ");"
    )

    create_send_record_sql = (
        "CREATE TABLE IF NOT EXISTS 'send_record' ("
        "'id' INTEGER PRIMARY KEY AUTOINCREMENT, "
        "'record_id' INTEGER NOT NULL DEFAULT 0, "
        "'sender_name' TEXT NOT NULL DEFAULT '', "
        "'sender_id' INTEGER NOT NULL DEFAULT 0, "
        "'sender_type' TEXT NOT NULL DEFAULT '', "
        "'send_data' TEXT NOT NULL DEFAULT '{}', "
        "'result' TEXT NOT NULL DEFAULT '{}', "
        "'create_time' INTEGER NOT NULL DEFAULT (strftime('%s'))"
        ");"
    )

    create_sender_sql = (
        "CREATE TABLE IF NOT EXISTS 'sender' ("
        "'id' INTEGER PRIMARY KEY AUTOINCREMENT, "
        "'used' INTEGER NOT NULL DEFAULT 1, "
        "'sender_type' TEXT NOT NULL DEFAULT '', "
        "'name' TEXT NOT NULL DEFAULT '', "
        "'data' TEXT NOT NULL DEFAULT '{}', "
        "'create_time' INTEGER NOT NULL DEFAULT (strftime('%s'))"
        ");"
    )

    lock_push_db()
    with get_push_db() as db:
        db.execute("pragma journal_mode=wal")

        res = db.execute(create_task_template_sql)
        if isinstance(res, str) and res.startswith("error"):
            write_log("warning system", "task_template Data table creation error:" + res)
            DB_INIT_ERROR = True
            return

        res = db.execute(create_task_sql)
        if isinstance(res, str) and res.startswith("error"):
            write_log("warning system", "task Data table creation error:" + res)
            DB_INIT_ERROR = True
            return

        res = db.execute(create_task_record_sql)
        if isinstance(res, str) and res.startswith("error"):
            write_log("warning system", "task_recorde Data table creation error:" + res)
            DB_INIT_ERROR = True
            return

        res = db.execute(create_send_record_sql)
        if isinstance(res, str) and res.startswith("error"):
            write_log("warning system", "send_record Data table creation error:" + res)
            DB_INIT_ERROR = True
            return

        res = db.execute(create_sender_sql)
        if isinstance(res, str) and res.startswith("error"):
            write_log("warning system", "sender Data table creation error:" + res)
            DB_INIT_ERROR = True
            return

        db.execute(
            "INSERT INTO 'sender' (id, sender_type, data) VALUES (?,?,?)",
            (1, 'sms', json.dumps({"count": 0, "total": 0}))
        )  # 插入短信

        unlock_push_db()

        init_template_file = "/www/server/panel/config/mod_push_init.json"
        err = load_task_template_by_file(init_template_file)
        if err:
            write_log("warning system", "task template data table initial data load failed:" + res)


def _check_fields(template: dict) -> bool:
    if not isinstance(template, dict):
        return False

    fields = ("id", "ver", "used", "source", "title", "load_cls", "template", "default", "unique", "create_time")
    for field in fields:
        if field not in template:
            return False
    return True


def load_task_template_by_config(templates: List[Dict]) -> None:
    """
    通过 传入的配置信息 执行一次模板更新操作
    @param templates: 模板内容，为一个数据列表
    @return: 报错信息，如果返回None则表示执行成功
    """

    task_template_config = TaskTemplateConfig()
    add_list = []
    for template in templates:
        tmp = task_template_config.get_by_id(template['id'])
        if tmp is not None:
            tmp.update(template)
        else:
            add_list.append(template)

    task_template_config.config.extend(add_list)
    task_template_config.save_config()

    # with get_table('task_template') as table:
    #     for template in templates:
    #         if not _check_fields(template):
    #             continue
    #         res = table.where("id = ?", (template['id'])).field('ver').select()
    #         if isinstance(res, str):
    #             return "数据库损坏：" + res
    #         if not res:  # 没有就插入
    #             table.insert(template)
    #         else:
    #             # 版本不一致就更新版本
    #             if res['ver'] != template['ver']:
    #                 template.pop("id")
    #                 table.where("id = ?", (template['id'])).update(template)
    #


def load_task_template_by_file(template_file: str) -> Optional[str]:
    """
    执行一次模板更新操作
    @param template_file: 模板文件路径
    @return: 报错信息，如果返回None则表示执行成功
    """
    if not os.path.isfile(template_file):
        return "The template file does not exist and the update fails"

    if DB_INIT_ERROR:
        return "An error is reported during database initialization and cannot be updated"

    res = read_file(template_file)
    if not isinstance(res, str):
        return "Data read failed"

    try:
        templates = json.loads(res)
    except (json.JSONDecoder, TypeError, ValueError):
        return "Only JSON data is supported"

    if not isinstance(templates, list):
        return "The data is in the wrong format and should be a list"

    return load_task_template_by_config(templates)
