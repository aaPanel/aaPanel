import json
import time

from datetime import datetime
from typing import Tuple, Union, Optional

from .send_tool import WxAccountMsg
from .base_task import BaseTask
from .mods import PUSH_DATA_PATH, TaskConfig, PANEL_PATH
from .util import read_file, DB, write_file
from mod.base.web_conf import RealSSLManger
import public

class DomainEndTimeTask(BaseTask):

    def __init__(self):
        super().__init__()
        self.source_name = "domain_endtime"
        self.template_name = "Domain expiration"
        # self.title = "Domain expiration"
        self._tip_file = "{}/domain_endtime.tip".format(PUSH_DATA_PATH)
        self._tip_data: Optional[dict] = None
        self._task_config = TaskConfig()

        # 每次任务使用
        self.domain_list = []
        self.push_keys = []
        self.task_id = None

    @property
    def tips(self) -> dict:
        if self._tip_data is not None:
            return self._tip_data
        try:
            self._tip_data = json.loads(read_file(self._tip_file))
        except:
            self._tip_data = {}
        return self._tip_data

    def save_tip(self):
        write_file(self._tip_file, json.dumps(self.tips))

    def get_keyword(self, task_data: dict) -> str:
        return task_data["project"]

    def get_push_data(self, task_id: str, task_data: dict) -> Optional[dict]:
        self.title = self.get_title(task_data)
        # 过滤单独设置提醒的域名
        not_push_web = [i["task_data"]["project"] for i in self._task_config.config if i["source"] == self.source_name]

        sql = DB("ssl_domains")
        total = self._task_config.get_by_id(task_id).get("number_rule", {}).get("total", 1)
        if "all" in not_push_web:
            not_push_web.remove("all")
        # need_check_list = []
        if task_data["project"] == "all":
            # 所有域名
            domain_list = sql.select()
            for domain in domain_list:
                if domain['domain'] in not_push_web:
                    continue
                if self.tips.get(task_id, {}).get(domain['domain'], 0) > total:
                    continue
                end_time = datetime.strptime(domain['endtime'], '%Y-%m-%d')
                if int((end_time.timestamp() - time.time()) / 86400) <= task_data['cycle']:
                    self.push_keys.append(domain['domain'])
                    self.domain_list.append(domain)
                # need_check_list.append(domain['domain'])

        else:
            find = sql.where('domain=?', (task_data['project'],)).find()
            if not find:
                return None

            end_time = datetime.strptime(find['endtime'], '%Y-%m-%d')
            if int((end_time.timestamp() - time.time()) / 86400) <= task_data['cycle']:
                self.push_keys.append(find['domain'])
                self.domain_list.append(find)

            # need_check_list.append((find['domain']))

        # for name, project_type in need_check_list:
        #     info = self._check_end_time(name, task_data['cycle'], project_type)
        #     if isinstance(info, dict):  # 返回的是详情，说明需要推送了
        #         info['site_name'] = name
        #         self.push_keys.append(name)
        #         self.domain_list.append(info)

        if len(self.domain_list) == 0:
            return None

        s_list = ['>About to expire:  <font color=#ff0000>{} </font>'.format(len(self.domain_list))]
        for x in self.domain_list:
            s_list.append(">Domain: {} Expiration:{}".format(x['domain'], x['endtime']))

        self.task_id = task_id
        return {"msg_list": s_list}

    @staticmethod
    def _check_end_time(site_name, limit, prefix) -> Optional[dict]:
        info = RealSSLManger(conf_prefix=prefix).get_site_ssl_info(site_name)
        if info is not None:
            end_time = datetime.strptime(info['notAfter'], '%Y-%m-%d')
            if int((end_time.timestamp() - time.time()) / 86400) <= limit:
                return info
        return None

    def get_title(self, task_data: dict) -> str:
        if task_data["project"] == "all":
            return "Domain expiration -- All"
        return "Domain expiration -- [{}]".format(task_data["project"])

    def to_sms_msg(self, push_data: dict, push_public_data: dict) -> Tuple[str, dict]:
        return 'domain_end|Domain expiration reminders', {
            "name": push_public_data["ip"],
            "domain": self.domain_list[0]['domain'],
            'time': self.domain_list[0]["endtime"],
            'total': len(self.domain_list)
        }

    def to_wx_account_msg(self, push_data: dict, push_public_data: dict) -> WxAccountMsg:
        msg = WxAccountMsg.new_msg()
        msg.thing_type = "Domain expiration reminders"
        msg.msg = "There are {} domain names that will expire and will affect access".format(len(self.domain_list))
        return msg

    def check_task_data(self, task_data: dict) -> Union[dict, str]:
        task_data["interval"] = 60 * 60 * 24  # 默认检测间隔时间 1 天
        if not (isinstance(task_data['cycle'], int) and task_data['cycle'] > 1):
            return "The remaining time parameter is incorrect, at least 1 day"
        return task_data

    def filter_template(self, template) -> dict:
        domain_list = DB("ssl_domains").select()

        items = [{"title": i["domain"], "value": i["domain"]}for i in domain_list]

        template["field"][0]["items"].extend(items)
        return template


    def check_num_rule(self, num_rule: dict) -> Union[dict, str]:
        num_rule["get_by_func"] = "can_send_by_num_rule"
        return num_rule

    # 实际的次数检查已在 get_push_data 其他位置完成
    def can_send_by_num_rule(self, task_id: str, task_data: dict, number_rule: dict, push_data: dict) -> Optional[str]:
        return None

    def task_run_end_hook(self, res) -> None:
        if not res["do_send"]:
            return
        if self.task_id:
            if self.task_id not in self.tips:
                self.tips[self.task_id] = {}

            for w in self.push_keys:
                if w in self.tips[self.task_id]:
                    self.tips[self.task_id][w] += 1
                else:
                    self.tips[self.task_id][w] = 1

            self.save_tip()

    def task_config_update_hook(self, task: dict) -> None:
        if task["id"] in self.tips:
            self.tips.pop(task["id"])
            self.save_tip()

    def task_config_remove_hook(self, task: dict) -> None:
        if task["id"] in self.tips:
            self.tips.pop(task["id"])
            self.save_tip()


class CertEndTimeTask(BaseTask):

    def __init__(self):
        super().__init__()
        self.source_name = "cert_endtime"
        self.template_name = "Certificate expiration"
        # self.title = "Certificate expiration"
        self._tip_file = "{}/cert_endtime.tip".format(PUSH_DATA_PATH)
        self._tip_data: Optional[dict] = None
        self._task_config = TaskConfig()

        # 每次任务使用
        self.cert_list = []
        self.push_keys = []
        self.task_id = None

    @property
    def tips(self) -> dict:
        if self._tip_data is not None:
            return self._tip_data
        try:
            self._tip_data = json.loads(read_file(self._tip_file))
        except:
            self._tip_data = {}
        return self._tip_data

    def save_tip(self):
        write_file(self._tip_file, json.dumps(self.tips))

    def get_keyword(self, task_data: dict) -> str:
        return task_data["project"]

    def get_push_data(self, task_id: str, task_data: dict) -> Optional[dict]:
        from .util import get_cert_list, to_dict_obj

        exclude_ids = [i["task_data"]["project"] for i in self._task_config.config if i["source"] == self.source_name]
        total = self._task_config.get_by_id(task_id).get("number_rule", {}).get("total", 1)

        if "all" in exclude_ids:
            exclude_ids.remove("all")
        data = get_cert_list(to_dict_obj({"status_id": 1}))['data']
        if task_data["project"] == "all":
            for cert in data:
                if cert["ssl_id"] in exclude_ids:
                    continue
                if self.tips.get(task_id, {}).get(cert['ssl_id'], 0) > total:
                    continue
                if not cert.get("endDay") and cert.get("endDay") != 0:
                    continue
                if cert["endDay"] <= task_data["cycle"]:
                    self.cert_list.append(cert)
        else:
            for cert in data:
                if cert["ssl_id"] != task_data["project"]:
                    continue
                if not cert.get("endDay") and cert.get("endDay") != 0:
                    continue
                if cert["endDay"] <= task_data["cycle"]:
                    self.cert_list.append(cert)
        self.title = self.get_title(task_data)
        if len(self.cert_list) == 0:
            return None

        s_list = ['>About to expire:  <font color=#ff0000>{} </font>'.format(len(self.cert_list))]
        for x in self.cert_list:
            s_list.append(
                ">Certificates: {} [{}]expire in days Websites that may be affected:{}".format("{} | {}".format(x["title"],",".join(x.get("domainName", []) or "None")), x['endDay'], ','.join(x.get('use_site', [])) or "None")
            )

        self.task_id = task_id
        return {"msg_list": s_list}

    @staticmethod
    def _check_end_time(site_name, limit, prefix) -> Optional[dict]:
        info = RealSSLManger(conf_prefix=prefix).get_site_ssl_info(site_name)
        if info is not None:
            end_time = datetime.strptime(info['notAfter'], '%Y-%m-%d')
            if int((end_time.timestamp() - time.time()) / 86400) <= limit:
                return info
        return None

    def get_title(self, task_data: dict) -> str:
        from .util import get_cert_list, to_dict_obj
        if task_data["project"] == "all":
            return "Certificate expiration -- All"
        data = get_cert_list(to_dict_obj({}))['data']
        for cert in data:
            if cert["ssl_id"] == task_data["project"]:
                return "Certificate expiration -- [{} | {}]".format(cert["title"],",".join(cert.get("domainName", []) or "None"))
        return "Domain [{}] expiration reminder".format(task_data["project"])

    def to_sms_msg(self, push_data: dict, push_public_data: dict) -> Tuple[str, dict]:
        return 'cert_end|Certificate expiration reminders', {
            "name": push_public_data["ip"],
            "cert": self.cert_list[0]['domain'],
            'time': self.cert_list[0]["endtime"],
            'total': len(self.cert_list)
        }

    def to_wx_account_msg(self, push_data: dict, push_public_data: dict) -> WxAccountMsg:
        msg = WxAccountMsg.new_msg()
        msg.thing_type = "Certificate expiration reminders"
        msg.msg = "There are {} certificates that will expire and will affect access".format(len(self.cert_list))
        return msg

    def check_task_data(self, task_data: dict) -> Union[dict, str]:
        task_data["interval"] = 60 * 60 * 24  # 默认检测间隔时间 1 天
        if not (isinstance(task_data['cycle'], int) and task_data['cycle'] > 1):
            return "The remaining time parameter is incorrect, at least 1 day"
        return task_data

    def filter_template(self, template) -> dict:
        from .util import get_cert_list, to_dict_obj

        items = [
            {"title": "{} | {}".format(i["title"],",".join(i.get("domainName", []) or "None")), "value": i["ssl_id"]}
            for i in get_cert_list(to_dict_obj({}))['data']
            if i.get("endDay")
        ]

        template["field"][0]["items"].extend(items)

        return template

    def check_num_rule(self, num_rule: dict) -> Union[dict, str]:
        num_rule["get_by_func"] = "can_send_by_num_rule"
        return num_rule

    # 实际的次数检查已在 get_push_data 其他位置完成
    def can_send_by_num_rule(self, task_id: str, task_data: dict, number_rule: dict, push_data: dict) -> Optional[str]:
        return None

    def task_run_end_hook(self, res) -> None:
        if not res["do_send"]:
            return
        if self.task_id:
            if self.task_id not in self.tips:
                self.tips[self.task_id] = {}

            for w in self.push_keys:
                if w in self.tips[self.task_id]:
                    self.tips[self.task_id][w] += 1
                else:
                    self.tips[self.task_id][w] = 1

            self.save_tip()

    def task_config_update_hook(self, task: dict) -> None:
        if task["id"] in self.tips:
            self.tips.pop(task["id"])
            self.save_tip()

    def task_config_remove_hook(self, task: dict) -> None:
        if task["id"] in self.tips:
            self.tips.pop(task["id"])
            self.save_tip()

class ViewMsgFormat(object):
    _FORMAT = {
        "1": (
            lambda x: "<span>Time remaining less than {} days {}</span>".format(
                x["task_data"].get("cycle"),
                ("(If it is not processed, it will be resent 1 time the next day for %d days)" % x.get("number_rule", {}).get("total", 0)) if x.get("number_rule", {}).get("total", 0) else ""
            )
        )
    }

    def get_msg(self, task: dict) -> Optional[str]:
        if task["template_id"] in ["70", "71"]:
            return self._FORMAT["1"](task)
        if task["template_id"] in self._FORMAT:
            return self._FORMAT[task["template_id"]](task)
        return None