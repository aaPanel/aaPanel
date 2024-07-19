# coding: utf-8
# -------------------------------------------------------------------
# 宝塔Linux面板
# -------------------------------------------------------------------
# Copyright (c) 2015-2017 宝塔软件(http:#bt.cn) All rights reserved.
# -------------------------------------------------------------------
# Author: baozi <baozi@bt.cn>
# -------------------------------------------------------------------
# 新告警通道管理模块
# ------------------------------
import json
import traceback
import os
from mod.base import json_response

from mod.base.push_mod import PushManager, TaskConfig, TaskRecordConfig, TaskTemplateConfig, PushSystem
from mod.base.push_mod import update_mod_push_system, UPDATE_MOD_PUSH_FILE, load_task_template_by_file, \
    UPDATE_VERSION_FILE
from mod.base.msg import update_mod_push_msg
from mod.base.push_mod.rsync_push import load_rsync_template
from mod.base.push_mod.task_manager_push import load_task_manager_template
from mod.base.push_mod.load_push import load_load_template
from mod.base.push_mod import PUSH_DATA_PATH

def update_mod():
    
    if not os.path.exists(UPDATE_VERSION_FILE):
        load_task_template_by_file("/www/server/panel/mod/base/push_mod/site_push_template.json")
        load_task_template_by_file("/www/server/panel/mod/base/push_mod/system_push_template.json")
        load_task_template_by_file("/www/server/panel/mod/base/push_mod/database_push_template.json")
        with open(UPDATE_VERSION_FILE, "w") as f:
            f.write("")

    if not os.path.exists(UPDATE_MOD_PUSH_FILE):
        update_mod_push_msg()

        load_rsync_template()
        load_task_manager_template()
        load_load_template()

        update_mod_push_system()


update_mod()
del update_mod


class main(PushManager):

    def get_task_list(self, get=None):
        try:
            res = TaskConfig().config
            res.sort(key=lambda x: x["create_time"])
            for i in res:
                i['view_msg'] = self.get_view_msg_format(i)
            return json_response(status=True, data=res)
        except:
            print(traceback.format_exc())

    @staticmethod
    def get_task_record(get):
        page = 1
        size = 10
        try:
            if hasattr(get, "page"):
                page = int(get.page.strip())
            if hasattr(get, "size"):
                size = int(get.size.strip())
            task_id = get.task_id.strip()
        except (AttributeError, ValueError, TypeError):
            return json_response(status=False, msg="参数错误")

        t = TaskRecordConfig(task_id)
        t.config.sort(key=lambda x: x["create_time"])
        page = max(page, 1)
        size = max(size, 1)
        count = len(t.config)
        data = t.config[(page - 1) * size: page * size]
        return json_response(status=True, data={
            "count": count,
            "list": data,
        })

    def clear_task_record(self, get):
        try:
            task_id = get.task_id.strip()
        except (AttributeError, ValueError, TypeError):
            return json_response(status=False, msg="参数错误")
        self.clear_task_record_by_task_id(task_id)

        return json_response(status=True, msg="清除成功")

    @staticmethod
    def remove_task_records(get):
        try:
            task_id = get.task_id.strip()
            record_ids = set(json.loads(get.record_ids.strip()))
        except (AttributeError, ValueError, TypeError):
            return json_response(status=False, msg="参数错误")
        task_records = TaskRecordConfig(task_id)
        for i in range(len(task_records.config) - 1, -1, -1):
            if task_records.config[i]["id"] in record_ids:
                del task_records.config[i]

        task_records.save_config()
        return json_response(status=True, msg="清除成功")

    @staticmethod
    def get_task_template_list(get=None):
        res = []
        p_sys = PushSystem()
        for i in TaskTemplateConfig().config:
            if not i['used']:
                continue
            to = p_sys.get_task_object(i["id"], i["load_cls"])
            if not to:
                continue
            t = to.filter_template(i["template"])
            if not t:
                continue
            i["template"] = t
            res.append(i)

        return json_response(status=True, data=res)

    @staticmethod
    def get_view_msg_format(task: dict) -> str:
        from mod.base.push_mod.rsync_push import ViewMsgFormat as Rv
        from mod.base.push_mod.site_push import ViewMsgFormat as Sv
        from mod.base.push_mod.task_manager_push import ViewMsgFormat as Tv
        from mod.base.push_mod.database_push import ViewMsgFormat as Dv
        from mod.base.push_mod.system_push import ViewMsgFormat as SSv
        from mod.base.push_mod.load_push import ViewMsgFormat as Lv

        list_obj = [Rv(), Sv(), Tv(), Dv(), SSv(), Lv()]
        for i in list_obj:
            res = i.get_msg(task)
            if res is not None:
                return res
        return '<span>--</span>'
