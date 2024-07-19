import json
import os
import time
from typing import Union, Optional

from .mods import TaskTemplateConfig, TaskConfig, SenderConfig, TaskRecordConfig
from .system import PushSystem
from mod.base import json_response


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
            return "未设置告警通道"
        if not isinstance(sender, list):
            return "告警通道设置错误"

        new_sender = []
        for i in sender:
            sender_conf = self._get_sender_conf(i)
            if not sender_conf:
                continue
            else:
                new_sender.append(i)
            if sender_conf["sender_type"] not in template["send_type_list"]:
                if sender_conf["sender_type"] == "sms":
                    return "不支持短信告警"
                return "不支持的告警方式:{}".format(sender_conf['data']["title"])
            if not sender_conf["used"]:
                if sender_conf["sender_type"] == "sms":
                    return "短信告警通道已关闭"
                return "已关闭的告警方式:{}".format(sender_conf['data']["title"])

        result["sender"] = new_sender

        if "default" in template and template["default"]:
            task_data = task.get("task_data", {})
            for k, v in template["default"].items():
                if k not in task_data:
                    task_data[k] = v

            result["task_data"] = task_data

        if "task_data" not in result:
            result["task_data"] = {}

        time_rule = task.get("time_rule", {})

        if "send_interval" in time_rule:
            if not isinstance(time_rule["send_interval"], int):
                return "最小间隔时间设置错误"
            if time_rule["send_interval"] < 0:
                return "最小间隔时间设置错误"

        if "time_range" in time_rule:
            if not isinstance(time_rule["time_range"], list):
                return "时间范围设置错误"
            if not len(time_rule["time_range"]) == 2:
                del time_rule["time_range"]
            else:
                time_range = time_rule["time_range"]
                if not (isinstance(time_range[0], int) and isinstance(time_range[1], int) and
                        0 <= time_range[0] < time_range[1] <= 60 * 60 * 24):
                    return "时间范围设置错误"

        result["time_rule"] = time_rule

        number_rule = task.get("number_rule", {})
        if "day_num" in number_rule:
            if not (isinstance(number_rule["day_num"], int) and number_rule["day_num"] >= 0):
                return "每日最小次数设置错误"

        if "total" in number_rule:
            if not (isinstance(number_rule["total"], int) and number_rule["total"] >= 0):
                return "最大告警次数设置错误"

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
            return "未查询到告警模板"

        if template["unique"] and not target_task_conf:
            for i in self.task_conf.config:
                if i["template_id"] == template["id"]:
                    target_task_conf = i
                    break

        task_obj = PushSystem().get_task_object(template_id, template["load_cls"])
        if not task_obj:
            return "加载任务类型错误，您可以尝试修复面板"

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
            return json_response(status=False, msg="参数错误")
        push_data = {
            "task_id": task_id,
            "template_id": template_id,
            "task_data": task,
        }
        res = self.set_task_conf_data(push_data)
        if res:
            return json_response(status=False, msg=res)
        # target_task_conf = None
        # if task_id is not None:
        #     tmp = self.task_conf.get_by_id(task_id)
        #     if tmp is None:
        #         target_task_conf = tmp
        #
        # template = self.template_conf.get_by_id(template_id)
        # if not template:
        #     return json_response(status=False, msg="为查询到告警模板")
        #
        # if template["unique"] and not target_task_conf:
        #     for i in self.task_conf.config:
        #         if i["template_id"] == template["id"]:
        #             target_task_conf = i
        #             break
        #
        # task_obj = PushSystem().get_task_object(template_id, template["load_cls"])
        # if not task_obj:
        #     return json_response(status=False, msg="加载任务类型错误，您可以尝试修复面板")
        #
        # res = self.normalize_task_config(task, template)
        # if isinstance(res, str):
        #     return json_response(status=True, msg=res)
        #
        # task_data = task_obj.check_task_data(res["task_data"])
        # if isinstance(task_data, str):
        #     return json_response(status=True, msg=task_data)
        #
        # number_rule = task_obj.check_num_rule(res["number_rule"])
        # if isinstance(number_rule, str):
        #     return json_response(status=True, msg=number_rule)
        #
        # time_rule = task_obj.check_time_rule(res["time_rule"])
        # if isinstance(time_rule, str):
        #     return json_response(status=True, msg=time_rule)
        #
        # res["task_data"] = task_data
        # res["number_rule"] = number_rule
        # res["time_rule"] = time_rule
        #
        # res["keyword"] = task_obj.get_keyword(task_data)
        # res["source"] = task_obj.source_name
        # res["title"] = task_obj.get_title(task_data)
        #
        # if not target_task_conf:
        #     tmp = self.task_conf.get_by_keyword(res["source"], res["keyword"])
        #     if tmp:
        #         target_task_conf = tmp
        #
        # if not target_task_conf:
        #     res["id"] = self.task_conf.nwe_id()
        #     res["template_id"] = template_id
        #     res["status"] = True
        #     res["pre_hook"] = {}
        #     res["after_hook"] = {}
        #     res["last_check"] = 0
        #     res["last_send"] = 0
        #     res["number_data"] = {}
        #     res["create_time"] = time.time()
        #     res["record_time"] = 0
        #     self.task_conf.config.append(res)
        #     task_obj.task_config_create_hook(res)
        # else:
        #     target_task_conf.update(res)
        #     target_task_conf["last_check"] = 0
        #     target_task_conf["number_data"] = {}  # 次数控制数据置空
        #     task_obj.task_config_update_hook(target_task_conf)
        #
        # self.task_conf.save_config()
        return json_response(status=True, msg="告警任务保存成功")

    def change_task_conf(self, get):
        try:
            task_id = get.task_id.strip()
        except AttributeError:
            return json_response(status=False, msg="参数错误")

        tmp = self.task_conf.get_by_id(task_id)
        if tmp is None:
            return json_response(status=True, msg="为查询到告警任务")

        tmp["status"] = not tmp["status"]

        self.task_conf.save_config()
        return json_response(status=True, msg="操作成功")

    def remove_task_conf(self, get):
        try:
            task_id = get.task_id.strip()
        except AttributeError:
            return json_response(status=False, msg="参数错误")

        tmp = self.task_conf.get_by_id(task_id)
        if tmp is None:
            return json_response(status=True, msg="为查询到告警任务")

        self.task_conf.config.remove(tmp)

        self.task_conf.save_config()
        template = self.template_conf.get_by_id(tmp["template_id"])
        if template:
            task_obj = PushSystem().get_task_object(template["id"], template["load_cls"])
            if task_obj:
                task_obj.task_config_remove_hook(tmp)

        return json_response(status=True, msg="操作成功")

    @staticmethod
    def clear_task_record_by_task_id(task_id):
        tr_conf = TaskRecordConfig(task_id)
        if os.path.exists(tr_conf.config_file_path):
            os.remove(tr_conf.config_file_path)
