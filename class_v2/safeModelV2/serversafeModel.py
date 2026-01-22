# coding: utf-8
# -------------------------------------------------------------------
# aaPanel
# -------------------------------------------------------------------
# Copyright (c) 2014-2099 aaPanel(www.aapanel.com) All rights reserved.
# -------------------------------------------------------------------
# Author: aapanel
# -------------------------------------------------------------------

# ------------------------------
# server safe app
# ------------------------------
import json
import os
import re
from copy import deepcopy
from typing import Callable

import public
from public.exceptions import HintException
from public.validate import Param

public.sys_path_append("class_v2/")
from ssh_security_v2 import ssh_security
from config_v2 import config


class main:
    def __init__(self):
        # {name:安全项名称,desc:描述,
        # suggest:修复建议,check:检查函数,repair:修复函数,value:获取当前值函数,status:状态}
        self.config = [
            {
                "name": "Default SSH Port",
                "desc": public.lang("Modify the default SSH port to improve server security"),
                "suggest": public.lang("Use a high port other than 22"),
                "check": self.check_ssh_port,
            },
            {
                "name": "Password Complexity Policy",
                "desc": public.lang("Enable password complexity check to ensure password security"),
                "suggest": public.lang("Use a level greater than 3"),
                "check": self.check_ssh_minclass,
                "repair": self.repair_ssh_minclass,
            },
            {
                "name": "Password Length Limit",
                "desc": public.lang("Set minimum password length requirement"),
                "suggest": public.lang("Use a password of 9-20 characters"),
                "check": self.check_ssh_security,
                "repair": self.repair_ssh_passwd_len,
            },
            {
                "name": "SSH Login Alert",
                "desc": public.lang("Send alert notification upon SSH login"),
                "suggest": public.lang("Enable SSH login alert"),
                "check": self.check_ssh_login_sender,
            },
            {
                "name": "Root Login Settings",
                "desc": public.lang("It is recommended to allow key-based login only"),
                "suggest": public.lang("Allow only SSH key-based login"),
                "check": self.check_ssh_login_root_with_key,
            },
            {
                "name": "SSH Brute-force",
                "desc": public.lang("Prevent SSH brute-force attacks"),
                "suggest": public.lang("Enable SSH brute-force protection"),
                "check": self.check_ssh_fail2ban_brute,
            },
            {
                "name": "Panel Login Alert",
                "desc": public.lang("Send alert notification upon panel login"),
                "suggest": public.lang("Enable panel login alert"),
                "check": self.check_panel_swing,
            },
            {
                "name": "Panel Google Authenticator login",
                "desc": public.lang("Enable TOTP for enhanced security"),
                "suggest": public.lang("Enable OTP authentication"),
                "check": self.check_panel_login_2fa,
            },
            {
                "name": "UnAuth Response Status Code",
                "desc": public.lang("Set the HTTP response status code for unauthenticated access"),
                "suggest": public.lang("Set 404 as the response code"),
                "check": self.check_panel_not_auth_code,
            },
            {
                "name": "Panel SSL",
                "desc": public.lang("Enable HTTPS encrypted transmission (after setting will restart the panel)"),
                "suggest": public.lang("Enable panel HTTPS"),
                "check": self.check_panel_ssl,
            }
        ]
        self.ssh_security_obj = ssh_security()
        self.config_obj = config()

    def get_security_info(self, get=None):
        """
        获取安全评分
        """
        new_list = deepcopy(self.config)
        for idx, module in enumerate(new_list):
            if isinstance(module.get("check"), Callable):
                try:
                    module["id"] = int(idx) + 1
                    check_status = module["check"]()
                    module["status"] = check_status.get("status", False)
                    module["value"] = check_status.get("value")
                except:
                    module["status"] = False
                    module["value"] = None

            if "check" in module and isinstance(module["check"], Callable):
                del module["check"]
            if "repair" in module and isinstance(module["repair"], Callable):
                del module["repair"]
            if "value" not in module:
                module["value"] = None

        total_score = 100  # 总分
        score = total_score / len(new_list)  # 每条的分数
        missing_count = 0  # 缺少的条数
        for module in new_list:
            if module["status"] is False:
                missing_count += 1
        # 计算总分
        security_score = total_score - (missing_count * score)
        security_score = round(security_score, 2)

        # 计算得分文本
        if security_score >= 90:
            score_text = public.lang("Secure")
        elif security_score >= 70:
            score_text = public.lang("Relatively Secure")
        elif security_score >= 50:
            score_text = public.lang("Average Security")
        else:
            score_text = public.lang("Insecure")

        public.set_module_logs("server_secury", "get_security_info", 1)
        return public.success_v2({
            "security_data": new_list,
            "total_score": total_score,
            "score_text": score_text,
            "score": int(security_score)
        })

    def install_fail2ban(self, get):
        from panel_plugin_v2 import panelPlugin
        public.set_module_logs("server_secury", "install_fail2ban", 1)
        return panelPlugin().install_plugin(get)

    def repair_security(self, get):
        """
        @name   修复安全项
        @parma  {"name":"","args":{}}
        """
        try:
            get.validate([
                Param("name").String().Require(),
                Param("args").Dict().Require(),
            ], [public.validate.trim_filter()])
        except Exception as ex:
            public.print_log("error info: {}".format(ex))
            return public.fail_v2(str(ex))

        for security in self.config:
            if security.get("name") == get.name and isinstance(security.get("repair"), Callable):
                return security["repair"](public.to_dict_obj(get.args))
        raise HintException(public.lang(f"Security Repair Item [{get.name}] Not Found!"))

    @staticmethod
    def _find_pwquality_conf_with_keyword(re_search: str) -> str:
        """
        读取ssh密码复杂度配置
        @param re_search: 正则表达式
        """
        try:
            if not re_search:
                raise HintException("required parameter re_search")
            p_file = '/etc/security/pwquality.conf'
            p_body = public.readFile(p_file)
            if not p_body:
                return ""  # 无配置文件时
            tmp = re.findall(re_search, p_body, re.M)
            if not tmp:
                return ""  # 未设置minclass
            find = tmp[0].strip()
            return find
        except:
            return ""  # 异常时认为无

    # =================== 检查函数 ===================
    def check_ssh_port(self) -> dict:
        """
        @name 检查SSH端口是否为默认端口22
        """
        current_port = public.get_ssh_port()
        return {"status": current_port != 22, "value": current_port}

    def check_ssh_minclass(self) -> dict:
        """
        @name 检查SSH密码复杂度策略
        """
        re_pattern = r"\n\s*minclass\s+=\s+(.+)"
        find = self._find_pwquality_conf_with_keyword(re_pattern)
        if not find:
            return {"status": False, "value": None}  # 未设置minclass
        minclass_value = int(find)
        return {"status": minclass_value >= 3, "value": minclass_value}

    def check_ssh_security(self) -> dict:
        """
        @name 检查SSH密码长度限制
        """
        re_pattern = r"\s*minlen\s+=\s+(.+)"
        find = self._find_pwquality_conf_with_keyword(re_pattern)
        if not find:
            return {"status": True, "value": None}  # 未设置minlen时认为无风险
        minlen_value = int(find)
        return {"status": minlen_value >= 9, "value": minlen_value}

    def check_panel_swing(self) -> dict:
        """
        @name 检查面板登录告警是否开启
        """
        tip_files = [
            "panel_login_send.pl", "login_send_type.pl", "login_send_mail.pl", "login_send_dingding.pl"
        ]
        enabled_files = []
        for fname in tip_files:
            filename = "data/" + fname
            if os.path.exists(filename):
                enabled_files.append(fname)
                break

        is_enabled = len(enabled_files) > 0
        value = None
        if not is_enabled:
            return {"status": False, "value": value}

        task_file_path = "/www/server/panel/data/mod_push_data/task.json"
        sender_file_path = "/www/server/panel/data/mod_push_data/sender.json"
        task_data = {}
        try:
            with open(task_file_path, "r") as file:
                tasks = json.load(file)
            # 读取发送者配置文件
            with open(sender_file_path, "r") as file:
                senders = json.load(file)
            sender_dict = {
                sender["id"]: sender for sender in senders
            }
            # 查找特定的告警任务
            for task in tasks:
                if task.get("keyword") == "panel_login":
                    task_data = task
                    sender_types = set()  # 使用集合来保证类型的唯一性
                    # 对应sender的ID，获取sender_type，并保证唯一性
                    for sender_id in task.get("sender", []):
                        if sender_id in sender_dict:
                            sender_types.add(sender_dict[sender_id]["sender_type"])
                    # 将唯一的通道类型列表转回列表格式，添加到告警数据中
                    task_data["channels"] = list(sender_types)
                    break
        except:
            pass
        value = task_data
        return {"status": value.get("status", False), "value": value}

    def check_ssh_login_sender(self) -> dict:
        """
        @name 检查SSH登录告警是否启用
        """
        result = self.ssh_security_obj.get_login_send(None)
        res = public.find_value_by_key(
            result, "result", "error"
        )
        return {"status": res != "error", "value": res}

    def check_ssh_login_root_with_key(self) -> dict:
        """
        @name 检查SSH是否仅允许密钥登录root
        """
        parsed = self.ssh_security_obj.paser_root_login()
        current_policy = None
        try:
            current_policy = parsed[1]
        except Exception as e:
            import traceback
            public.print_log("error info: {}".format(traceback.format_exc()))
        return {"status": current_policy == "without-password", "value": current_policy}

    def check_ssh_fail2ban_brute(self) -> dict:
        """
        @name 检查SSH防爆破是否启用
        """
        from safeModelV2.sshModel import main as sshmod
        cfg = sshmod._get_ssh_fail2ban() or {}
        current_value = cfg.get("status", 0)
        return {"status": current_value == 1, "value": current_value}

    def check_panel_login_2fa(self) -> dict:
        """
        @name 检查面板登录动态口令认证是否启用
        """
        current_value = self.config_obj.check_two_step(None)
        res = public.find_value_by_key(
            current_value, "result", False
        )
        return {"status": bool(res), "value": res}

    def check_panel_not_auth_code(self) -> dict:
        """
        @name 检查面板未登录响应状态码是否设置为 400+
        """
        current_code = self.config_obj.get_not_auth_status()
        return {"status": current_code != 0, "value": current_code}

    def check_panel_ssl(self):
        """
        @name 检查面板是否开启SSL
        """
        enabled = os.path.exists("data/ssl.pl")
        return {"status": bool(enabled), "value": enabled}

    # =================== 修复函数 ===================
    def repair_ssh_minclass(self, get):
        """
        @name 修复SSH密码复杂度
        @param {"minclass":9}
        """
        try:
            get.validate([
                Param("minclass").Integer(">", 0).Require(),
            ], [public.validate.trim_filter()])
        except Exception as ex:
            public.print_log("error info: {}".format(ex))
            return public.fail_v2(str(ex))

        minclass = int(get.minclass)
        file = "/etc/security/pwquality.conf"
        result = {
            "status": False, "msg": public.lang("Failed to set SSH password complexity, "
                                                "please disable system hardening or set it manually")
        }
        if not os.path.exists(file):
            public.ExecShell("apt install libpam-pwquality -y")
        if os.path.exists(file):
            f_data = public.readFile(file)
            if re.findall("\n\s*minclass\s*=\s*\d*", f_data):
                file_result = re.sub("\n\s*minclass\s*=\s*\d*", "\nminclass = {}".format(minclass), f_data)
            else:
                file_result = f_data + "\nminclass = {}".format(minclass)
            public.writeFile(file, file_result)
            f_data = public.readFile(file)
            if f_data.find("minclass = {}".format(minclass)) != -1:
                result["status"] = True
                result["msg"] = public.lang("SSH minimum password complexity has been set")
        return public.return_message(0 if result["status"] else 1, 0, result["msg"])

    def repair_ssh_passwd_len(self, get):
        """
        @name SSH密码最小长度设置
        @param {"len":9}
        """
        try:
            get.validate([
                Param("len").Integer(">", 0).Require(),
            ], [public.validate.trim_filter()])
        except Exception as ex:
            public.print_log("error info: {}".format(ex))
            return public.fail_v2(str(ex))

        pwd_len = int(get.len)
        file = "/etc/security/pwquality.conf"
        result = {
            "status": False, "msg": public.lang("Failed to set SSH minimum password length, please set it manually")
        }
        if not os.path.exists(file):
            public.ExecShell("apt install libpam-pwquality -y")
        if os.path.exists(file):
            f_data = public.readFile(file)
            ssh_minlen = "\n#?\s*minlen\s*=\s*\d*"
            file_result = re.sub(ssh_minlen, "\nminlen = {}".format(pwd_len), f_data)
            public.writeFile(file, file_result)
            f_data = public.readFile(file)
            if f_data.find("minlen = {}".format(pwd_len)) != -1:
                result["status"] = True
                result["msg"] = "SSH minimum password length has been set to {}".format(pwd_len)
        return public.return_message(0 if result["status"] else 1, 0, result["msg"])
