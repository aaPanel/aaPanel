import json
from typing import Tuple, Union, Optional, Dict, List

from . import WxAccountMsg
from .mods import TaskConfig
from .base_task import BaseTask, BaseTaskViewMsg
from .site_push import web_info
from .util import get_db_by_file, DB, GET_CLASS, read_file, write_file
from .manager import PushManager
from .system import push_by_task_keyword



class SiteMonitorViolationWordTask(BaseTask):  # 网站违规词告警检查
    DB_FILE = "/www/server/panel/class/projectModel/content/content.db"

    def __init__(self):
        super().__init__()
        self.source_name: str = 'site_monitor_violation_word'
        self.title: str = 'Website violation keyword alert'
        self.template_name: str = 'Website violation keyword alert'

    def check_task_data(self, task_data: dict) -> Union[dict, str]:
        """
        检查设置的告警参数（是否合理）
        @param task_data: 传入的告警参数，提前会经过默认值处理（即没有的字段添加默认值）
        @return: 当检查无误时，返回一个 dict 当做后续的添加和修改的数据，
                当检查有误时， 直接返回错误信息的字符串
        """
        if "interval" in task_data:
            task_data.pop("interval")
        if "mvw_id" in task_data and not task_data["mvw_id"]:
            task_data.pop("mvw_id")
        if "site_name" in task_data and not task_data["site_name"]:
            task_data.pop("site_name")
        return task_data

    def get_push_data(self, task_id: str, task_data: dict) -> Optional[dict]:
        return None

    def get_title(self, task_data: dict) -> str:
        return "Violation keyword check on website {}".format(task_data["site_name"])

    def get_keyword(self, task_data: dict) -> str:
        return "site_mvw_{}".format(task_data.get("mvw_id", 0))

    def filter_template(self, template: dict) -> Optional[dict]:
        """
        过滤 和 更改模板中的信息, 返回空表是当前无法设置该任务
        @param template: 任务的模板信息
        @return:
        """
        _, items_type = web_info(project_types=("PHP",))
        template["field"][0]["items"].extend(items_type["PHP"])
        return template

    def task_config_create_hook(self, task: dict) -> Optional[str]:
        task_data = task["task_data"]
        if "mvw_id" not in task_data or not task_data["mvw_id"]:
            return "No corresponding website violation word scanning task, unable to add alert"
        if "site_name" not in task_data or not task_data["site_name"]:
            return "No corresponding website violation word scanning task, unable to add alert"

    def task_config_update_hook(self, task: dict) -> Optional[str]:
        task_data = task["task_data"]
        if "mvw_id" not in task_data or not task_data["mvw_id"]:
            return "No corresponding website violation word scanning task, unable to add alert"
        if "site_name" not in task_data or not task_data["site_name"]:
            return "No corresponding website violation word scanning task, unable to add alert"

        db_obj = get_db_by_file(self.DB_FILE)
        if not db_obj:
            return "Website violation word scanning task database file does not exist"
        pdata = {
            "send_msg": int(task["status"]),
            "send_type": ",".join(task["sender"])
        }
        try:
            db_obj.table("monitor_site").where("id=?", task_data["mvw_id"]).update(pdata)
            db_obj.close()
        except:
            return "Website violation word scanning task update failed"
        # 保障keyword的id正确
        task["keyword"] = self.get_keyword(task_data)

    def task_config_remove_hook(self, task: dict) -> None:
        task_data = task["task_data"]
        if "mvw_id" not in task_data or not task_data["mvw_id"]:
            return
        db_obj = get_db_by_file(self.DB_FILE)
        if not db_obj:
            return
        try:
            db_obj.table("monitor_site").where("id=?", task_data["mvw_id"]).update({"send_msg": 0})
            db_obj.close()
        except:
            return

    @classmethod
    def set_push_task(cls, mvw_id: int, site_name: str, status: bool, sender: list):
        task_conf = TaskConfig()
        old_task = task_conf.get_by_keyword("site_monitor_violation_word", "site_mvw_{}".format(mvw_id))
        if not old_task:
            push_data = {
                "template_id": "121",
                "task_data": {
                    "status": True,
                    "sender": sender,
                    "task_data": {
                        "site_name": site_name,
                        "mvw_id": mvw_id,
                    }
                }
            }
            from .manager import PushManager
            PushManager().set_task_conf_data(push_data)
        else:
            old_task["sender"] = sender
            old_task["status"] = status
            task_conf.save_config()

    @classmethod
    def remove_push_task(cls, mvw_id: int):
        task_conf = TaskConfig()
        old_task = task_conf.get_by_keyword("site_monitor_violation_word", "site_mvw_{}".format(mvw_id))
        if old_task:
            task_conf.config.remove(old_task)

        task_conf.save_config()


class VulnerabilityScanningTask(BaseTask):

    def __init__(self):
        super().__init__()
        self.source_name: str = 'vulnerability_scanning'
        self.title: str = 'Website vulnerability alert'
        self.template_name: str = 'Website vulnerability alert'

    def check_task_data(self, task_data: dict) -> Union[dict, str]:
        """
        检查设置的告警参数（是否合理）
        @param task_data: 传入的告警参数，提前会经过默认值处理（即没有的字段添加默认值）
        @return: 当检查无误时，返回一个 dict 当做后续的添加和修改的数据，
                当检查有误时， 直接返回错误信息的字符串
        """
        if "cycle" not in task_data or not task_data["cycle"] or not isinstance(task_data["cycle"], int):
            return "Cycle cannot be empty"

        return {"interval": 60*60*24 * (task_data["cycle"] + 1), "cycle": task_data["cycle"]}

    def get_keyword(self, task_data: dict) -> str:
        """
        返回一个关键字，用于后续查询或执行任务时使用， 例如：防篡改告警，可以根据其规则id生成一个关键字，
        后续通过规则id和来源tamper 查询并使用
        @param task_data: 通过check_args后生成的告警参数字典
        @return: 返回一个关键词字符串
        """
        return "vulnerability_scanning"

    def get_title(self, task_data: dict) -> str:
        """
        返回一个标题
        @param task_data: 通过check_args后生成的告警参数字典
        @return: 返回一个关键词字符串
        """
        return 'Website vulnerability alert'

    def get_push_data(self, task_id: str, task_data: dict) -> Optional[dict]:
        """
        判断这个任务是否需要返送
        @param task_id: 任务id
        @param task_data: 任务的告警参数
        @return: 如果触发了告警，返回一个dict的原文，作为告警信息，否则应当返回None表示未触发
                返回之中应当包含一个 msg_list 的键（值为List[str]类型），将主要的信息返回
                用于以下信息的自动序列化包含[dingding, feishu, mail, weixin, web_hook]
                短信和微信公众号由于长度问题，必须每个任务手动实现
        """
        return None

    def filter_template(self, template: dict) -> Optional[dict]:
        """
        过滤 和 更改模板中的信息, 返回空表是当前无法设置该任务
        @param template: 任务的模板信息
        @return:
        """
        return template

    @classmethod
    def set_push_task(cls, status: bool, day: int, sender: list):
        push_data = {
            "template_id": "122",
            "task_data": {
                "status": status,
                "sender": sender,
                "task_data": {
                    "cycle": day,
                }
            }
        }
        return PushManager().set_task_conf_data(push_data)

    @staticmethod
    def del_crontab():
        """
        @name 删除项目定时清理任务
        @auther hezhihong<2022-10-31>
        @return
        """
        cron_name = '[Do not delete] Vulnerability scanning scheduled task'
        cron_list = DB('crontab').where("name=?", (cron_name,)).select()

        if cron_list:
            for i in cron_list:
                if not i:
                    continue
                args = {"id": i['id']}
                import crontab
                crontab.crontab().DelCrontab(args)

    def add_crontab(self, day, channel):
        """
        @name 构造计划任务
        """
        cron_name = '[Do not delete] Vulnerability scanning scheduled task'
        cron_list = DB('crontab').where("name=?", (cron_name,)).select()
        if cron_list:
            self.del_crontab()
        if not DB('crontab').where('name=?',(cron_name,)).count():
            args = {
                "name": cron_name,
                "type": 'day-n',
                "where1": day,
                "hour": '10',
                "minute": '30',
                "sName": "",
                "sType": 'toShell',
                "notice": '0',
                "notice_channel": channel,
                "save": '',
                "save_local": '1',
                "backupTo": '',
                "sBody": 'btpython /www/server/panel/script/cron_scaning.py {}'.format(channel),
                "urladdress": '',
                "user": 'root'
            }
            import crontab
            res = crontab.crontab().AddCrontab(args)
            if res and "id" in res.keys():
                return True
            return False
        return True

    def task_config_create_hook(self, task: dict) -> Optional[str]:
        return self.task_config_update_hook(task)

    def task_config_update_hook(self, task: dict) -> Optional[str]:
        if task["status"]:
            day = task['task_data']['cycle']
            channel = ",".join(task['sender'])
            if self.add_crontab(day, channel):
                return None
            return "Failed to add scheduled task"
        else:
            self.del_crontab()

    def task_config_remove_hook(self, task: dict) -> None:
        self.del_crontab()


class FileDetectTask(BaseTask):
    def __init__(self):
        super().__init__()
        self.source_name: str = 'file_detect'
        self.title: str = 'System file integrity reminder'
        self.template_name: str = 'System file integrity reminder'

    def check_task_data(self, task_data: dict) -> Union[dict, str]:
        """
        检查设置的告警参数（是否合理）
        @param task_data: 传入的告警参数，提前会经过默认值处理（即没有的字段添加默认值）
        @return: 当检查无误时，返回一个 dict 当做后续的添加和修改的数据，
                当检查有误时， 直接返回错误信息的字符串
        """
        if not isinstance(task_data["hour"], int) or not isinstance(task_data["minute"], int):
            return "Hours and minutes must be integers"

        if task_data["hour"] < 0 or task_data["hour"] > 23:
            return "The hour must be an integer between 0 and 23"

        if task_data["minute"] < 0 or task_data["minute"] > 59:
            return "Minutes must be an integer between 0 and 59"

        return {
            "interval": 60 * 60 * 24,
            "hour": task_data["hour"],
            "minute": task_data["minute"],
        }

    def get_keyword(self, task_data: dict) -> str:
        """
        返回一个关键字，用于后续查询或执行任务时使用， 例如：防篡改告警，可以根据其规则id生成一个关键字，
        后续通过规则id和来源tamper 查询并使用
        @param task_data: 通过check_args后生成的告警参数字典
        @return: 返回一个关键词字符串
        """
        return "file_detect"

    def get_title(self, task_data: dict) -> str:
        """
        返回一个标题
        @param task_data: 通过check_args后生成的告警参数字典
        @return: 返回一个关键词字符串
        """
        return 'System file integrity reminder'

    def get_push_data(self, task_id: str, task_data: dict) -> Optional[dict]:
        return None

    def filter_template(self, template: dict) -> Optional[dict]:
        """
        过滤 和 更改模板中的信息, 返回空表是当前无法设置该任务
        @param template: 任务的模板信息
        @return:
        """
        return template

    def add_crontab(self, hour, minute, channel):
        """
        @name 构造计划任务
        """
        cron_name = '[Do not delete] File integrity monitoring scheduled task'
        cron_list = DB('crontab').where("name=?", (cron_name,)).select()

        if cron_list:
            self.del_crontab()
        if not DB('crontab').where('name=?', (cron_name,)).count():
            args = {
                "name": cron_name,
                "type": 'day',
                "where1": '',
                "hour": hour,
                "minute": minute,
                "sName": "",
                "sType": 'toShell',
                "notice": '0',
                "notice_channel": channel,
                "save": '',
                "save_local": '1',
                "backupTo": '',
                "sBody": 'btpython /www/server/panel/script/cron_file.py {}'.format(channel),
                "urladdress": ''
            }
            import crontab
            res = crontab.crontab().AddCrontab(args)
            if res and "id" in res.keys():
                return True
            return False
        return True

    # 删除项目定时清理任务
    @staticmethod
    def del_crontab():
        cron_name = '[Do not delete] File integrity monitoring scheduled task'
        cron_list = DB('crontab').where("name=?", (cron_name,)).select()
        if cron_list:
            for i in cron_list:
                if not i: continue
                args = {"id": i['id']}
                import crontab
                crontab.crontab().DelCrontab(args)

    def task_config_create_hook(self, task: dict) -> Optional[str]:
        return self.task_config_update_hook(task)

    def task_config_update_hook(self, task: dict) -> Optional[str]:
        if task["status"]:
            hour = task['task_data']['hour']
            minute = task['task_data']['minute']
            channel = ",".join(task['sender'])
            if self.add_crontab(hour, minute, channel):
                return None
            return "Failed to add scheduled task"
        else:
            self.del_crontab()

    def task_config_remove_hook(self, task: dict) -> None:
        self.del_crontab()

    @classmethod
    def set_push_task(cls, status: bool, hour: int, minute: int, sender: list):
        push_data = {
            "template_id": "123",
            "task_data": {
                "status": status,
                "sender": sender,
                "task_data": {
                    "hour": hour,
                    "minute": minute,
                }
            }
        }
        from .manager import PushManager
        return PushManager().set_task_conf_data(push_data)


class SafeCloudTask(BaseTask):
    _config_file = "/www/server/panel/data/safeCloud/config.json"
    _all_safe_type = ("webshell", )

    def __init__(self):
        super().__init__()
        self.source_name = "safe_cloud_hinge"
        self.title = "Aapanel Cloud Security Center Alarm"
        self.template_name = "Aapanel Cloud Security Center Alarm"

        self._safe_cloud_conf: Optional[dict] = None

    @property
    def safe_cloud_conf(self) -> Optional[dict]:
        """
        获取云安全配置
        :return: 云安全配置
        """
        if self._safe_cloud_conf and isinstance(self._safe_cloud_conf, dict):
            return self._safe_cloud_conf
        try:
            self._safe_cloud_conf = json.loads(read_file(self._config_file))
            return self._safe_cloud_conf
        except:
            self._init_config()
            try:
                self._safe_cloud_conf = json.loads(read_file(self._config_file))
                return self._safe_cloud_conf
            except:
                pass
        return None


    def filter_template(self, template: dict) -> Optional[dict]:
        """
        过滤模板
        :param template: 模板
        :return: 过滤后的模板
        """
        return template

    def save_safe_cloud_conf(self):
        """
        保存云安全配置
        """
        write_file(self._config_file, json.dumps(self._safe_cloud_conf))

    def check_task_data(self, task_data: dict) -> Union[dict, str]:
        """
        检查任务数据
        :param task_data: 任务数据
        :return: 检查后的任务数据
        """
        if "safe_type" in task_data:
            for i in task_data["safe_type"]:
                if i not in self._all_safe_type:
                    return "Security type error"
        else:
            task_data["safe_type"] = ["webshell"]

        task_data["interval"] = 60 * 60 * 3
        return task_data

    def check_num_rule(self, num_rule: dict) -> Union[dict, str]:
        """
        检查告警数量规则，一天只能告警20次
        :param num_rule: 告警数量规则
        :return: 检查后的告警数量规则
        """
        num_rule["day_num"] = 20
        return num_rule

    def check_time_rule(self, time_rule: dict) -> Union[dict, str]:
        """
        检查告警时间规则[写死]
        :param time_rule: 告警时间规则
        :return: 检查后的告警时间规则
        """
        # 测试数据为1秒 ，正常数据为 1200 20*60 20分钟告警一次
        time_rule["send_interval"] = 1200
        return time_rule

    def get_keyword(self, task_data: dict) -> str:
        """
        返回一个关键字，用于后续查询或执行任务时使用， 例如：防篡改告警，可以根据其规则id生成一个关键字，
        后续通过规则id和来源tamper 查询并使用
        @param task_data: 通过check_args后生成的告警参数字典
        @return: 返回一个关键词字符串
        """
        return "safe_cloud_hinge"

    def get_title(self, task_data: dict) -> str:
        """
        返回一个标题
        @param task_data: 通过check_args后生成的告警参数字典
        @return: 返回一个关键词字符串
        """
        return 'Aapanel Cloud Security Center Alarm'

    def get_push_data(self, task_id: str, task_data: dict) -> Optional[dict]:
        """
        判断这个任务是否需要返送
        @param task_id: 任务id
        @param task_data: 任务的告警参数
        @return: 如果触发了告警，返回一个dict的原文，作为告警信息，否则应当返回None表示未触发
                返回之中应当包含一个 msg_list 的键（值为List[str]类型），将主要的信息返回
                用于以下信息的自动序列化包含[dingding, feishu, mail, weixin, web_hook]
                短信和微信公众号由于长度问题，必须每个任务手动实现
        """

        return None

    def task_config_create_hook(self, task: dict) -> Optional[str]:
        return self.task_config_update_hook(task)

    def task_config_update_hook(self, task: dict) -> Optional[str]:
        """
        更新告警配置
        :param task: 任务
        :return: 更新后的任务
        """
        if not self.safe_cloud_conf:
            return "Failed to initialize configuration file, unable to add"

        alert_data = self.safe_cloud_conf["alertable"]
        alert_data["safe_type"] = task["task_data"].get("safe_type", ["webshell"])
        alert_data["interval"] = task["task_data"].get("interval", 60*60*3)
        alert_data["status"] = task["status"]
        alert_data["sender"] = task["sender"]
        alert_data["time_rule"] = task["time_rule"]
        alert_data["number_rule"] = task["number_rule"]
        self.save_safe_cloud_conf()

    def task_config_remove_hook(self, task: dict) -> Optional[str]:
        """
        删除告警配置
        :param task: 任务
        :return: 删除后的任务
        """
        if not self.safe_cloud_conf:
            return None

        alert_data = self.safe_cloud_conf["alertable"]
        alert_data["safe_type"] = task["task_data"].get("safe_type", ["webshell"])
        alert_data["interval"] = task["task_data"].get("interval", 60*60*3)
        alert_data["status"] = False
        alert_data["sender"] = []
        alert_data["time_rule"] = task["time_rule"]
        alert_data["number_rule"] = task["number_rule"]
        self.save_safe_cloud_conf()

    # 更新告警配置
    @staticmethod
    def set_push_conf(alert_data: dict) -> Optional[str]:
        """
        将告警信息设置到告警任务中去
        :param alert_data:
        :return:
        """
        pm = PushManager()
        p_data = {
            "template_id": "124",
            "task_data": {
                "status": alert_data.get("status", True),
                "sender": alert_data.get("sender", []),
                "task_data": {
                    "safe_type": alert_data.get("safe_type", ["webshell"]),
                    "interval":  alert_data.get("interval", 60*60*3),
                },
                "time_rule": alert_data.get("time_rule", {}),
                "number_rule": alert_data.get("number_rule", {}),
            }
        }
        return pm.set_task_conf_data(p_data)


    @staticmethod
    def _init_config():
        """
        初始化配置
        """
        try:
            import PluginLoader

            args = GET_CLASS()
            args.model_index = 'project'
            PluginLoader.module_run("safecloud", "init_config", args)
        except:
            pass



class ViewMsgFormat(BaseTaskViewMsg):

    def get_msg(self, task: dict) -> Optional[str]:
        if task["template_id"] == "122":
            return "Every {} days, identify and scan for vulnerabilities in common open-source CMS programs across all websites and send alerts".format(task["task_data"]["cycle"])
        if task["template_id"] == "123":
            return "Scan the critical executable files in the system daily at 【{}:{}】, and send alerts when changes are detected".format(
                task["task_data"]["hour"], task["task_data"]["minute"]
            )
        if task["template_id"] == "124":
            return "Every {} hours, scan the server files to identify abnormal situations such as high resource consumption and malicious control of the server, and send alerts".format(
                int(task["task_data"]["interval"] / 3600)
            )
        return None


SiteMonitorViolationWordTask.VIEW_MSG = VulnerabilityScanningTask.VIEW_MSG = FileDetectTask.VIEW_MSG = SafeCloudTask.VIEW_MSG = ViewMsgFormat