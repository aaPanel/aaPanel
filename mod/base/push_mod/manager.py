import json
import os
import sys
import time
from typing import Union, Optional

from mod.base import json_response
from .mods import TaskTemplateConfig, TaskConfig, SenderConfig, TaskRecordConfig
from .system import PushSystem

sys.path.insert(0, "/www/server/panel/class/")
import public


class PushManager:
    def __init__(self):
        self.template_conf = TaskTemplateConfig()
        self.task_conf = TaskConfig()
        self.send_config = SenderConfig()
        self._send_conf_cache = {}

    def _get_sender_conf(self, sender_id):
        if sender_id in self._send_conf_cache:
            return self._send_conf_cache[sender_id]
        tmp = self.send_config.get_by_id(sender_id)
        self._send_conf_cache[sender_id] = tmp
        return tmp

    def normalize_task_config(self, task, template) -> Union[dict, str]:
        result = {}
        sender = task.get("sender", None)
        if sender is None:
            return "No alarm channel is configured"
        if not isinstance(sender, list):
            return "The alarm channel is incorrect"

        new_sender = []
        for i in sender:
            sender_conf = self._get_sender_conf(i)
            if not sender_conf:
                continue
            else:
                new_sender.append(i)

            if sender_conf["sender_type"] == "sms":
                return "SMS alerts are not supported"
            
            allowed = template.get("send_type_list", [])
            if allowed != "ALL" and sender_conf["sender_type"] not in allowed:
                return "Unsupported alerting methods:{}".format(sender_conf['data']["title"])
            
            if not sender_conf["used"]:
                return "Closed alert mode:{}".format(sender_conf['data']["title"])

        result["sender"] = new_sender

        if "default" in template and template["default"]:
            task_data = task.get("task_data", {})
            for k, v in template["default"].items():
                if k not in task_data:
                    task_data[k] = v

            result["task_data"] = task_data
        # 避免default为空时，无数据
        else:
            result["task_data"] = task.get("task_data", {})

        if "task_data" not in result:
            result["task_data"] = {}

        time_rule = task.get("time_rule", {})

        if "send_interval" in time_rule:
            if not isinstance(time_rule["send_interval"], int):
                return "The minimum interval is set incorrectly"
            if time_rule["send_interval"] < 0:
                return "The minimum interval is set incorrectly"

        if "time_range" in time_rule:
            if not isinstance(time_rule["time_range"], list):
                return "The time range is set incorrectly"
            if not len(time_rule["time_range"]) == 2:
                del time_rule["time_range"]
            else:
                time_range = time_rule["time_range"]
                if not (isinstance(time_range[0], int) and isinstance(time_range[1], int) and
                        0 <= time_range[0] < time_range[1] <= 60 * 60 * 24):
                    return "The time range is set incorrectly"

        result["time_rule"] = time_rule

        number_rule = task.get("number_rule", {})
        if "day_num" in number_rule:
            if not (isinstance(number_rule["day_num"], int) and number_rule["day_num"] >= 0):
                return "The minimum number of times per day is set incorrectly"

        if "total" in number_rule:
            if not (isinstance(number_rule["total"], int) and number_rule["total"] >= 0):
                return "The maximum number of alarms is set incorrectly"

        result["number_rule"] = number_rule

        if "status" not in task:
            result["status"] = True
        if "status" in task:
            if isinstance(task["status"], bool):
                result["status"] = task["status"]

        return result

    def set_task_conf_data(self, push_data: dict) -> Optional[str]:
        task_id = push_data.get("task_id", None)
        template_id = push_data.get("template_id")
        task = push_data.get("task_data")

        target_task_conf = None
        if task_id is not None:
            tmp = self.task_conf.get_by_id(task_id)
            if tmp is None:
                target_task_conf = tmp

        template = self.template_conf.get_by_id(template_id)

        if not template:
            # 如果没有找到模板，则尝试加载默认的安全推送模板
            from mod.project.push.taskMod import TEMPLATE_DIR
            safe_temp = os.path.join(TEMPLATE_DIR, "safe_mod_push_template.json")
            if not os.path.exists(safe_temp):
                return "No alarm template was found"
            from .mods import load_task_template_by_file
            load_task_template_by_file(safe_temp)
            self.template_conf = TaskTemplateConfig()
            template = self.template_conf.get_by_id(template_id)
            if not template:
                return "No alarm template was found"

        if template["unique"] and not target_task_conf:
            for i in self.task_conf.config:
                if i["template_id"] == template["id"]:
                    target_task_conf = i
                    break

        task_obj = PushSystem().get_task_object(template_id, template["load_cls"])
        if not task_obj:
            return "Loading task type error, you can try to fix the panel"

        res = self.normalize_task_config(task, template)
        if isinstance(res, str):
            return res

        task_data = task_obj.check_task_data(res["task_data"])
        if isinstance(task_data, str):
            return task_data

        number_rule = task_obj.check_num_rule(res["number_rule"])
        if isinstance(number_rule, str):
            return number_rule

        time_rule = task_obj.check_time_rule(res["time_rule"])
        if isinstance(time_rule, str):
            return time_rule

        res["task_data"] = task_data
        res["number_rule"] = number_rule
        res["time_rule"] = time_rule

        res["keyword"] = task_obj.get_keyword(task_data)
        res["source"] = task_obj.source_name
        res["title"] = task_obj.get_title(task_data)

        if not target_task_conf:
            tmp = self.task_conf.get_by_keyword(res["source"], res["keyword"])
            if tmp:
                target_task_conf = tmp

        if not target_task_conf:
            res["id"] = self.task_conf.nwe_id()
            res["template_id"] = template_id
            res["status"] = True
            res["pre_hook"] = {}
            res["after_hook"] = {}
            res["last_check"] = 0
            res["last_send"] = 0
            res["number_data"] = {}
            res["create_time"] = time.time()
            res["record_time"] = 0
            self.task_conf.config.append(res)
            task_obj.task_config_create_hook(res)
        else:
            target_task_conf.update(res)
            target_task_conf["last_check"] = 0
            target_task_conf["number_data"] = {}  # 次数控制数据置空
            task_obj.task_config_update_hook(target_task_conf)

        self.task_conf.save_config()
        return None

    def update_task_status(self, get):
        # 先调用 set_task_conf 修改任务配置
        set_conf_response = self.set_task_conf(get)

        if set_conf_response['status'] != 0:
            return set_conf_response  # 返回错误信息

        # 读取任务数据
        file_path = '{}/data/mod_push_data/task.json'.format(public.get_panel_path())
        try:
            with open(file_path, 'r') as file:
                tasks = json.load(file)
        except (IOError, json.JSONDecodeError):
            return json_response(status=False, msg=public.lang("Unable to read task data."))
        # 查找对应的 task_id
        task_title = get.title.strip()  # 假设 get 中有 title 参数
        task_id = None

        for task in tasks:
            if task.get('title') == task_title:
                task_id = task.get('id')
                break

        if not task_id:
            return json_response(status=False, msg=public.lang("The task has not been found."))

        # 调用 change_task_conf 修改任务状态
        get.task_id = task_id
        return self.change_task_conf(get)

    def set_task_conf(self, get):
        task_id = None
        try:
            if hasattr(get, "task_id"):
                task_id = get.task_id.strip()
                if not task_id:
                    task_id = None
                else:
                    self.remove_task_conf(get)
            template_id = get.template_id.strip()
            task = json.loads(get.task_data.strip())
        except (AttributeError, json.JSONDecodeError, TypeError, ValueError):
            return json_response(status=False, msg="The parameter is incorrect")
        push_data = {
            "task_id": task_id,
            "template_id": template_id,
            "task_data": task,
        }
        res = self.set_task_conf_data(push_data)
        if res:
            return json_response(status=False, msg=res)
        return json_response(status=True, msg="The alarm task is saved successfully")

    def change_task_conf(self, get):
        try:
            task_id = get.task_id.strip()
            status = int(get.status)  # 获取status字段并转换为整数
        except (AttributeError, ValueError):
            return json_response(status=False, msg="Parameter error")

        if status not in [0, 1]:
            return json_response(status=False, msg="Invalid status value")

        tmp = self.task_conf.get_by_id(task_id)
        if tmp is None:
            return json_response(status=True, msg="No alarm task was queried")

        tmp["status"] = bool(status)  # 将status转换为布尔值并设置

        self.task_conf.save_config()
        return json_response(status=True, msg="operate successfully")

    def change_task(self, task_id, status):
        tmp = self.task_conf.get_by_id(task_id)
        tmp["status"] = bool(status)  # 将status转换为布尔值并设置
        self.task_conf.save_config()

    def remove_task_conf(self, get):
        try:
            task_id = get.task_id.strip()
        except AttributeError:
            return json_response(status=False, msg="The parameter is incorrect")

        tmp = self.task_conf.get_by_id(task_id)
        if tmp is None:
            return json_response(status=True, msg="No alarm task was queried")

        self.task_conf.config.remove(tmp)

        self.task_conf.save_config()
        template = self.template_conf.get_by_id(tmp["template_id"])
        if template:
            task_obj = PushSystem().get_task_object(template["id"], template["load_cls"])
            if task_obj:
                task_obj.task_config_remove_hook(tmp)

        return json_response(status=True, msg="operate successfully")

    @staticmethod
    def clear_task_record_by_task_id(task_id):
        tr_conf = TaskRecordConfig(task_id)
        if os.path.exists(tr_conf.config_file_path):
            os.remove(tr_conf.config_file_path)
