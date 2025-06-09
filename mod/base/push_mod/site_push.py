import glob
import hashlib
import json
import os
import re
import sys
import time
from datetime import datetime
from importlib import import_module
from typing import Tuple, Union, Optional, List

import psutil

from mod.base.web_conf import RealSSLManger
from script.restart_services import manual_flag
from ssl_domainModelV2.model import DnsDomainSSL
from .base_task import BaseTask
from .mods import PUSH_DATA_PATH, TaskConfig, SenderConfig
from .send_tool import WxAccountMsg, WxAccountLoginMsg
from .util import read_file, DB, write_file, check_site_status, GET_CLASS, ExecShell, get_config_value, \
    public_get_cache_func, \
    public_set_cache_func, get_network_ip, public_get_user_info, public_http_post, panel_version

import public
import public.PluginLoader as plugin_loader
class _WebInfo:

    def __init__(self):
        self.last_time = 0
        self._items = None
        self._items_by_type = None

    def __call__(self):
        if self._items is not None and self.last_time > time.time() - 300:
            return self._items, self._items_by_type

        items = []
        items_by_type = [[], [], [], [], []]

        res_list = DB('sites').field('id,name,project_type,project_config').select()

        for i in res_list:
            if not check_site_status(i):
                continue
            items.append({
                "title": i["name"] + "[" + i["project_type"] + "]",
                "value": i["name"]
            })

            if i["project_type"] == "PHP" or i["project_type"] == "proxy":
                continue
            idx: int = ProjectStatusTask._to_project_id(i["project_type"])
            if idx is None:
                continue
            items_by_type[idx].append({
                "title": i["name"],
                "value": i["id"]
            })

        self._items = items
        self._items_by_type = items_by_type
        return items, items_by_type


web_info = _WebInfo()


class SSLCertificateTask(BaseTask):
    def __init__(self):
        super().__init__()
        self.source_name = "SSL"
        self.title = "SSL Certificate expiration"
        self.template_name = "Certificate (SSL) Expiration"
        self._task_config = TaskConfig()
        self.task_id = None

    def get_keyword(self, task_data: dict) -> str:
        return task_data["project"]

    def get_push_data(self, task_id: str, task_data: dict) -> Optional[dict]:
        try:
            days = int(task_data.get("cycle", 15))
        except Exception:
            days = 15

        # 过滤要告警的对象
        msg_list = []

        domain_list = []  # 域名模块
        mail_list = []  # 邮件模块

        # ============= domain ssl manager ================
        after_ts = (time.time() + 86400 * days) * 1000
        ssl_obj = DnsDomainSSL.objects.filter(not_after_ts__lt=after_ts)
        for ssl in ssl_obj:
            if ssl:
                domain_list.append(ssl.subject)

        # =============  mail ssl  ========================
        # 有插件 已开启 即将过期
        mail_database_path = '/www/vmail/postfixadmin.db'
        vmail_ssl_map = '/etc/postfix/vmail_ssl.map'
        if os.path.exists(mail_database_path) and os.path.exists(vmail_ssl_map):
            ssl_conf = public.readFile(vmail_ssl_map)
            if ssl_conf:
                try:
                    with public.S("domain", mail_database_path) as obj:

                        if public.check_field_exists(obj, "domain", "ssl_alarm"):
                            domains = obj.where('ssl_alarm', 1).select()
                            mail_domain_list = [i['domain'] for i in domains]
                            if mail_domain_list:
                                for domain in mail_domain_list:
                                
                                    cert_path = '/www/server/panel/plugin/mail_sys/cert/{}/fullchain.pem'.format(domain)
                                    if not os.path.exists(cert_path):
                                        continue

                                    if domain not in ssl_conf:
                                        continue

                                    # ssl
                                    main = plugin_loader.get_module('{}/plugin/mail_sys/mail_sys_main.py'.format(public.get_panel_path()))
                                    mail_sys_main = main.mail_sys_main
                                    ssl_info = mail_sys_main().get_ssl_info(domain)
                                    endtime = ssl_info.get('endtime', None)
                                    
                                    if endtime and endtime <= 15:
                                        mail_list.append(domain)
                except:
                    pass

        # =================================================

        if domain_list:
            msg_list.append(f"> Domain SSL {domain_list} certificate expired\n")
        if mail_list:
            msg_list.append(f"> Mail Server SSL {mail_list} certificate expired\n")

        return {"msg_list": msg_list} if msg_list else None

    def filter_template(self, template) -> dict:
        # 前端模板展示选项
        return template

    def check_task_data(self, task_data: dict) -> Union[dict, str]:
        # 校验保存更改配置的合法性
        task_data["interval"] = 60 * 60 * 24  # 默认检测间隔时间 1 天
        if not (isinstance(task_data['cycle'], int) and task_data['cycle'] >= 1):
            return "The remaining time parameter is incorrect, at least 1 day"
        return task_data

    def get_title(self, task_data: dict) -> str:
        return "SSL Certificate expiration"

    def check_num_rule(self, num_rule: dict) -> Union[dict, str]:
        num_rule["get_by_func"] = "can_send_by_num_rule"
        return num_rule

    def to_sms_msg(self, push_data: dict, push_public_data: dict) -> Tuple[str, dict]:
        # 构造sms特殊消息体
        return 'ssl_end|aaPanel SSL Expiration Reminder', {
            "name": push_public_data["ip"],
            # "domain": self.ssl_list[0]['domain'],
            'time': self.ssl_list[0]["notAfter"],
            'total': len(self.ssl_list)
        }

    def to_wx_account_msg(self, push_data: dict, push_public_data: dict) -> WxAccountMsg:
        # 构造wx特殊消息体
        msg = WxAccountMsg.new_msg()
        msg.thing_type = "SSL expiration reminder"
        msg.msg = "There are {} domains whose certificates will expire, affecting access".format(len(self.ssl_list))
        msg.next_msg = "Please login to the aaPanel and renew in the certificates"
        return msg

    # 不需要额外hook


# todo 即将弃置
class SSLTask(BaseTask):

    def __init__(self):
        super().__init__()
        self.source_name = "site_ssl"
        self.template_name = "Site Certificate (SSL) expiration"
        # self.title = "Site Certificate (SSL) expiration"
        self._tip_file = "{}/site_ssl.tip".format(PUSH_DATA_PATH)
        self._tip_data: Optional[dict] = None
        self._task_config = TaskConfig()

        # 每次任务使用
        self.ssl_list = []
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
        panelPath = '/www/server/panel/'
        os.chdir(panelPath)
        sys.path.insert(0, panelPath)
        # 过滤单独设置提醒的网站
        not_push_web = [i["task_data"]["project"] for i in self._task_config.config if i["source"] == self.source_name]
        sql = DB("sites")
        total = self._task_config.get_by_id(task_id).get("number_rule", {}).get("total", 1)
        if "all" in not_push_web:
            not_push_web.remove("all")

        need_check_list = []
        if task_data["project"] == "all":
            # 所有正常网站
            web_list = sql.where('status=1', ()).select()
            for web in web_list:
                if web['name'] in not_push_web:
                    continue
                if web['project_type'] != "PHP":
                    if not check_site_status(web):
                        continue

                if self.tips.get(task_id, {}).get(web['name'], 0) > total:
                    continue

                if not web['project_type'].lower() in ['php', 'proxy']:
                    project_type = web['project_type'].lower() + '_'
                else:
                    project_type = ''

                need_check_list.append((web['name'], project_type))

        else:
            find = sql.where('name=? and status=1', (task_data['project'],)).find()
            if not find:
                return None

            if find['project_type'] != "PHP":
                if not check_site_status(find):
                    return None

            if not find['project_type'].lower() in ['php', 'proxy']:
                project_type = find['project_type'].lower() + '_'
            else:
                project_type = ''

            need_check_list.append((find['name'], project_type))

        for name, project_type in need_check_list:
            info = self._check_ssl_end_time(name, task_data['cycle'], project_type)
            if isinstance(info, dict):  # 返回的是详情，说明需要推送了
                info['site_name'] = name
                self.push_keys.append(name)
                self.ssl_list.append(info)

        if len(self.ssl_list) == 0:
            return None

        s_list = ['>About to expire: <font color=#ff0000>{} </font>'.format(len(self.ssl_list))]
        for x in self.ssl_list:
            s_list.append(">Website: {} Expiration: {}".format(x['site_name'], x['notAfter']))

        self.task_id = task_id
        self.title = self.get_title(task_data)
        return {"msg_list": s_list}

    @staticmethod
    def _check_ssl_end_time(site_name, limit, prefix) -> Optional[dict]:
        info = RealSSLManger(conf_prefix=prefix).get_site_ssl_info(site_name)
        if info is not None:
            end_time = datetime.strptime(info['notAfter'], '%Y-%m-%d')
            if int((end_time.timestamp() - time.time()) / 86400) <= limit:
                return info
        return None

    def get_title(self, task_data: dict) -> str:
        if task_data["project"] == "all":
            return "Site Certificate (SSL) expiration -- All"
        return "Site Certificate (SSL) expiration -- Website [{}]".format(task_data["project"])

    def to_sms_msg(self, push_data: dict, push_public_data: dict) -> Tuple[str, dict]:
        return 'ssl_end|aaPanel SSL Expiration Reminder', {
            "name": push_public_data["ip"],
            "website": self.ssl_list[0]['site_name'],
            'time': self.ssl_list[0]["notAfter"],
            'total': len(self.ssl_list)
        }

    def to_wx_account_msg(self, push_data: dict, push_public_data: dict) -> WxAccountMsg:
        msg = WxAccountMsg.new_msg()
        msg.thing_type = "Website SSL expiration reminder"
        msg.msg = "There are {} sites whose certificates will expire, affecting access".format(len(self.ssl_list))
        msg.next_msg = "Please login to the aaPanel and renew in the [Website]"
        return msg

    def check_task_data(self, task_data: dict) -> Union[dict, str]:
        task_data["interval"] = 60 * 60 * 24  # 默认检测间隔时间 1 天
        if not (isinstance(task_data['cycle'], int) and task_data['cycle'] >= 1):
            return "The remaining time parameter is incorrect, at least 1 day"
        return task_data

    def filter_template(self, template) -> dict:
        items, _ = web_info()
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


class SiteEndTimeTask(BaseTask):

    def __init__(self):
        super().__init__()
        self.source_name = "site_end_time"
        self.template_name = "Site expiration reminders"
        self.title = "Site expiration reminders"
        self._tip_file = "{}/site_end_time.tip".format(PUSH_DATA_PATH)
        self._tip_data: Optional[dict] = None
        self._task_config = TaskConfig()

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

    def check_task_data(self, task_data: dict) -> Union[dict, str]:
        task_data["interval"] = 60 * 60 * 24  # 默认检测间隔时间 1 天
        if not (isinstance(task_data['cycle'], int) and task_data['cycle'] >= 1):
            return "The remaining time parameter is incorrect, at least 1 day"
        return task_data

    def get_keyword(self, task_data: dict) -> str:
        return "site_end_time"

    def get_push_data(self, task_id: str, task_data: dict) -> Optional[dict]:
        m_end_date = time.strftime('%Y-%m-%d', time.localtime(time.time() + 86400 * int(task_data['cycle'])))
        web_list = DB('sites').where(
            'edate>? AND edate<? AND (status=? OR status=?)',
            ('0000-00-00', m_end_date, 1, u'正在运行')
        ).field('id,name, edate').select()
        if not (isinstance(web_list, list) and len(web_list) >= 1):
            return None

        total = self._task_config.get_by_id(task_id).get("number_rule", {}).get("total", 1)
        s_list = ['>Number of expiring sites: <font color=#ff0000>{} </font>'.format(len(web_list))]
        for x in web_list:
            if self.tips.get(x['name'], 0) >= total:
                continue
            self.push_keys.append(x['name'])
            s_list.append(">Website: {} Expiration: {}".format(x['name'], x['edate']))

        if not self.push_keys:
            return None

        self.task_id = task_id
        self.title = self.get_title(task_data)
        return {
            "msg_list": s_list
        }

    def check_num_rule(self, num_rule: dict) -> Union[dict, str]:
        num_rule["get_by_func"] = "can_send_by_num_rule"
        return num_rule

    # 实际的次数检查已在 get_push_data 其他位置完成
    def can_send_by_num_rule(self, task_id: str, task_data: dict, number_rule: dict, push_data: dict) -> Optional[str]:
        return None

    def filter_template(self, template) -> dict:
        return template

    def to_sms_msg(self, push_data: dict, push_public_data: dict) -> Tuple[str, dict]:
        return '', {}

    def to_wx_account_msg(self, push_data: dict, push_public_data: dict) -> WxAccountMsg:
        msg = WxAccountMsg.new_msg()
        msg.thing_type = "Website expiration reminders"
        msg.msg = "There are {} sites that are about to expire and may affect site visits".format(len(self.push_keys))
        msg.next_msg = "Please log in to the aaPanel and check the details on the website"
        return msg

    def task_run_end_hook(self, res) -> None:
        if not res["do_send"]:
            return
        if self.push_keys:
            for w in self.push_keys:
                if w in self.tips:
                    self.tips[w] += 1
                else:
                    self.tips[w] = 1
            self.save_tip()

    def task_config_update_hook(self, task: dict) -> None:
        if os.path.exists(self._tip_file):
            os.remove(self._tip_file)

    def task_config_remove_hook(self, task: dict) -> None:
        if os.path.exists(self._tip_file):
            os.remove(self._tip_file)


class PanelPwdEndTimeTask(BaseTask):

    def __init__(self):
        super().__init__()
        self.source_name = "panel_pwd_end_time"
        self.template_name = "aaPanel password expiration date"
        self.title = "aaPanel password expiration date"

        self.limit_days = 0

    def check_task_data(self, task_data: dict) -> Union[dict, str]:
        task_data["interval"] = 60 * 60 * 24  # 默认检测间隔时间 1 天
        if not (isinstance(task_data['cycle'], int) and task_data['cycle'] >= 1):
            return "The remaining time parameter is incorrect, at least 1 day"
        return task_data

    def get_keyword(self, task_data: dict) -> str:
        return "pwd_end_time"

    def get_push_data(self, task_id: str, task_data: dict) -> Optional[dict]:
        if "/www/server/panel/class" not in sys.path:
            sys.path.insert(0, "/www/server/panel/class")
        import config
        c_obj = config.config()
        res = c_obj.get_password_config(None)
        if res['expire'] > 0 and res['expire_day'] < task_data['cycle']:
            self.limit_days = res['expire_day']

            s_list = [">Alarm Type: The login password is about to expire",
                      ">Days Remaining: <font color=#ff0000>{} </font>".format(res['expire_day'])]

            return {
                'msg_list': s_list
            }
        self.title = self.get_title(task_data)
        return None

    def filter_template(self, template) -> dict:
        return template

    def to_sms_msg(self, push_data: dict, push_public_data: dict) -> Tuple[str, dict]:
        return '', dict()

    def to_wx_account_msg(self, push_data: dict, push_public_data: dict) -> WxAccountMsg:
        msg = WxAccountMsg.new_msg()
        msg.thing_type = "aaPanel password expiration reminder"
        msg.msg = "The login password will expire after {} days".format(self.limit_days)
        msg.next_msg = "Log in to the panel and change your password in Settings"
        return msg


class PanelLoginTask(BaseTask):
    push_tip_file = "/www/server/panel/data/panel_login_send.pl"

    def __init__(self):
        # import public
        # public.print_log("panel_login")
        super().__init__()
        self.source_name = "panel_login"
        self.template_name = "aaPanel login alarm"
        self.title = "aaPanel login alarm"

    def check_task_data(self, task_data: dict) -> Union[dict, str]:
        return {}

    def get_keyword(self, task_data: dict) -> str:
        return "panel_login"

    def get_push_data(self, task_id: str, task_data: dict) -> Optional[dict]:
        return None

    def filter_template(self, template) -> dict:
        return template

    def to_sms_msg(self, push_data: dict, push_public_data: dict) -> Tuple[str, dict]:
        return "login_panel|aaPanel login reminders", {
            'name': '[' + push_data.get("ip") + ']',
            'time': time.strftime('%Y-%m-%d %X', time.localtime()),
            'type': '[' + push_data.get("is_type") + ']',
            'user': push_data.get("username")
        }

    def to_wx_account_msg(self, push_data: dict, push_public_data: dict) -> WxAccountMsg:
        msg = WxAccountLoginMsg.new_msg()
        msg.thing_type = "aaPanel login reminders"
        msg.login_name = push_data.get("username")
        msg.login_ip = push_data.get("login_ip")
        msg.login_type = push_data.get("is_type")
        msg.address = push_data.get("login_ip_area")
        return msg

    def task_config_update_hook(self, task: dict) -> None:
        # import public
        # public.print_log(4444444444444)
        sender = task["sender"]
        if len(sender) > 0:
            send_id = sender[0]
        else:
            return

        sender_data = SenderConfig().get_by_id(send_id)
        if sender_data:
            write_file(self.push_tip_file, sender_data["sender_type"])

    def task_config_create_hook(self, task: dict) -> None:
        # import public
        # public.print_log(444444433333)
        sender = task["sender"]
        if len(sender) > 0:
            send_id = sender[0]
        else:
            return

        sender_data = SenderConfig().get_by_id(send_id)
        if sender_data:
            write_file(self.push_tip_file, sender_data["sender_type"])

    def task_config_remove_hook(self, task: dict) -> None:
        # import public
        # public.print_log(33333333333333333333333)
        if os.path.exists(self.push_tip_file):
            os.remove(self.push_tip_file)


class SSHLoginErrorTask(BaseTask):
    _months = {'Jan': '01', 'Feb': '02', 'Mar': '03', 'Apr': '04', 'May': '05', 'Jun': '06', 'Jul': '07', 'Aug': '08',
               'Sep': '09', 'Sept': '09', 'Oct': '10', 'Nov': '11', 'Dec': '12'}

    def __init__(self):
        super().__init__()
        self.source_name = "ssh_login_error"
        self.template_name = "SSH login failure alarm"
        self.title = "SSH login failure alarm"

    def check_task_data(self, task_data: dict) -> Union[dict, str]:
        if not (isinstance(task_data['cycle'], int) and task_data['cycle'] >= 1):
            return "The duration parameter is incorrect, at least 1 minute"
        if not (isinstance(task_data['count'], int) and task_data['count'] >= 1):
            return "The quantity parameter is incorrect, at least 1 time"
        if not (isinstance(task_data['interval'], int) and task_data['interval'] >= 60):
            return "The interval time parameter is incorrect, at least 60 seconds"
        return task_data

    def get_keyword(self, task_data: dict) -> str:
        return "ssh_login_error"

    def get_push_data(self, task_id: str, task_data: dict) -> Optional[dict]:
        import PluginLoader
        args = GET_CLASS()
        args.model_index = 'safe'
        args.count = task_data['count']
        args.p = 1
        res = PluginLoader.module_run("syslog", "get_ssh_error", args)
        if 'status' in res:
            return None

        last_info = res[task_data['count'] - 1]
        if self.to_date(times=last_info['time']) >= time.time() - task_data['cycle'] * 60:
            s_list = [">Notification type: SSH login failure alarm",
                      ">Content of alarm: <font color=#ff0000> Login failed more than {} times in {} minutes</font> ".format(
                          task_data['cycle'], task_data['count'])]

            return {
                'msg_list': s_list,
                'count': task_data['count']
            }

        return None

    @staticmethod
    def to_date(times, fmt_str="%Y-%m-%d %H:%M:%S"):
        if times:
            if isinstance(times, int):
                return times
            if isinstance(times, float):
                return int(times)
            if re.match(r"^\d+$", times):
                return int(times)
        else:
            return 0
        ts = time.strptime(times, fmt_str)
        return time.mktime(ts)

    def filter_template(self, template) -> dict:
        return template

    def to_sms_msg(self, push_data: dict, push_public_data: dict) -> Tuple[str, dict]:
        return '', dict()

    def to_wx_account_msg(self, push_data: dict, push_public_data: dict) -> WxAccountMsg:
        msg = WxAccountMsg.new_msg()
        msg.thing_type = "SSH login failure alarm"
        msg.msg = "More than {} login failures".format(push_data['count'])
        msg.next_msg = "Log in to the panel to view the SSH login logs"
        return msg


class ServicesTask(BaseTask):
    def __init__(self):
        super().__init__()
        self.source_name = "services"
        self.template_name = "Service Stop Alert"
        self.pids = None
        self.service_name = ""
        self.restart = None

    @staticmethod
    def services_list() -> list:
        """
        获取已安装的服务
        """
        res_list = []
        php_path = "/www/server/php"
        if os.path.exists(php_path) and glob.glob(php_path + "/*"):
            res_list.append({
                "title": "php-fpm service discontinued",
                "value": "php-fpm"
            })
        if os.path.exists('/etc/init.d/httpd'):
            res_list.append({
                "title": "apache service discontinued",
                "value": "apache"
            })
        if os.path.exists('/etc/init.d/nginx'):
            res_list.append({
                "title": "nginx service discontinued",
                "value": "nginx"
            })
        if os.path.exists('/etc/init.d/mysqld'):
            res_list.append({
                "title": "mysql service discontinued",
                "value": "mysql"
            })
        if os.path.exists('/etc/init.d/mongodb'):
            res_list.append({
                "title": "mysql service discontinued",
                "value": "mongodb"
            })
        if os.path.exists('/www/server/tomcat/bin'):
            res_list.append({
                "title": "tomcat service discontinued",
                "value": "tomcat"
            })
        if os.path.exists('/etc/init.d/pure-ftpd'):
            res_list.append({
                "title": "pure-ftpd service discontinued",
                "value": "pure-ftpd"
            })
        if os.path.exists('/www/server/redis'):
            res_list.append({
                "title": "redis service discontinued",
                "value": "redis"
            })
        if os.path.exists('/etc/init.d/memcached'):
            res_list.append({
                "title": "memcached service discontinued",
                "value": "memcached"
            })
        if os.path.exists('/usr/local/lsws/bin/lswsctrl'):
            res_list.append({
                "title": "openlitespeed service discontinued",
                "value": "openlitespeed"
            })
        return res_list

    def check_task_data(self, task_data: dict) -> Union[dict, str]:
        if task_data["project"] not in {
            i["value"] for i in self.services_list()
        }:
            return "The selected service does not exist"
        if task_data["count"] not in (1, 2):
            return "Auto-restart selection error"
        if not (isinstance(task_data['interval'], int) and task_data['interval'] >= 60):
            return "The interval time parameter is incorrect, at least 60 seconds"
        return task_data

    def get_keyword(self, task_data: dict) -> str:
        return task_data["project"]

    def get_push_data(self, task_id: str, task_data: dict) -> Optional[dict]:
        self.title = self.get_title(task_data)
        self.service_name = task_data.get("project")
        if self.service_name not in [v["value"] for v in self.services_list()]:
            return None
        if self.get_server_status():
            return None

        s_list = [
            "> Service Type: " + self.service_name,
            "> Service State: 【" + self.service_name + "】Service Has Been Discontinued"
        ]
        if manual_flag().get(self.service_name) == 1:
            # is manually closed
            return None
        else:
            if task_data.get("count") == 1:
                count = 0
                while count <= 1:  # retry
                    self._services_start(self.service_name)
                    count += 1
                    if not self.get_server_status():
                        self.restart = False
                        s_list[1] = "> Service State: 【" + self.service_name + "】Service Restart Failed"
                    else:
                        self.restart = True
                        s_list[1] = "> Service State: 【" + self.service_name + "】Service Restart Successfully"

                    if self.restart is True:
                        break
            return {"msg_list": s_list}

    def get_title(self, task_data: dict) -> str:
        return "Service Stop Alert --" + task_data["project"]

    def _services_start(self, service_name: str):
        if service_name == "php-fpm":
            base_path = "/www/server/php"
            if not os.path.exists(base_path):
                return None
            for p in os.listdir(base_path):
                init_file = os.path.join("/etc/init.d", "php-fpm-{}".format(p))
                if not os.path.isfile(init_file):
                    return None
                ExecShell("{} start".format(init_file))

        elif service_name == 'mysql':
            init_file = os.path.join("/etc/init.d", "mysqld")
            ExecShell("{} start".format(init_file))
            if not self.get_server_status():
                ExecShell("{} restart".format(init_file))

        elif service_name == 'apache':
            init_file = os.path.join("/etc/init.d", "httpd")
            ExecShell("{} start".format(init_file))

        elif service_name == 'openlitespeed':
            init_file = "/usr/local/lsws/bin/lswsctrl"
            ExecShell("{} start".format(init_file))
            if not self.get_server_status():
                ExecShell("{} restart".format(init_file))

        else:
            init_file = os.path.join("/etc/init.d", service_name)
            ExecShell("{} start".format(init_file))

        self.pids = psutil.pids()  # renew pids

    def get_pid_name(self, pname):
        try:
            if not self.pids:
                self.pids = psutil.pids()
            for pid in self.pids:
                if psutil.Process(pid).name() == pname: return True
            return False
        except:
            return True

    def _sock_file_check(self, sock_path: str, process_name: str):
        if os.path.exists(sock_path):
            status = False
            for proc in psutil.process_iter(['pid', 'name', 'connections']):
                try:
                    check_list = [process_name] if process_name != "mysqld" else ["mysqld", "mariadbd"]
                    for c in check_list:
                        if c in proc.info['name']:
                            # noinspection PyDeprecation
                            for conn in proc.connections(kind='unix'):
                                if conn.laddr == sock_path:
                                    status = True
                except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                    continue
            if status is True:
                return True
        return False

    def get_server_status(self) -> bool:
        time.sleep(5)
        if self.service_name == "php-fpm":
            base_path = "/www/server/php"
            if not os.path.exists(base_path):
                return False
            for p in os.listdir(base_path):
                pid_file = os.path.join(base_path, p, "var/run/php-fpm.pid")
                if os.path.exists(pid_file):
                    status = self.check_process(pid_file)
                    if status:
                        return True
            return False

        elif self.service_name == 'nginx':
            if os.path.exists('/etc/init.d/nginx'):
                pid_f = '/www/server/nginx/logs/nginx.pid'
                if os.path.exists(pid_f):
                    try:
                        return self.check_process(pid_f)
                    except:
                        pass
            return False

        elif self.service_name == 'apache':
            if os.path.exists('/etc/init.d/httpd'):
                pid_f = '/www/server/apache/logs/httpd.pid'
                if os.path.exists(pid_f):
                    return self.check_process(pid_f)
            return False

        elif self.service_name == 'mysql':
            return self._sock_file_check('/tmp/mysql.sock', 'mysqld')

        elif self.service_name == 'mongodb':
            pid_f = '/www/server/mongodb/log/configsvr.pid'
            if os.path.exists(pid_f):
                return self.check_process(pid_f)
            return False

        elif self.service_name == 'tomcat':
            status = False
            if os.path.exists('/www/server/tomcat/logs/catalina-daemon.pid'):
                if self.get_pid_name('jsvc'):
                    status = True
            if not status:
                if self.get_pid_name('java'):
                    status = True

            return status

        elif self.service_name == 'pure-ftpd':
            pid_f = '/var/run/pure-ftpd.pid'
            if os.path.exists(pid_f):
                return self.check_process(pid_f)
            return False

        elif self.service_name == 'redis':
            pid_f = '/www/server/redis/redis.pid'
            if os.path.exists(pid_f):
                return self.check_process(pid_f)
            return False

        elif self.service_name == 'memcached':
            pid_f = '/var/run/memcached.pid'
            if os.path.exists(pid_f):
                return self.check_process(pid_f)
            return False

        elif self.service_name == 'openlitespeed':
            return self._sock_file_check('/tmp/lshttpd/lsphp.sock', 'litespeed')

        return True

    def check_process(self, pid_f):
        """
        检查进程是否存在
        :param pid_f: pid文件路径
        :param name 服务名
        """
        try:
            pid = read_file(pid_f)
            if pid and int(pid) in psutil.pids():
                return True
            return False
        except Exception as e:
            print("check_process error %s", e)
            return False

    def filter_template(self, template: dict) -> Optional[dict]:
        server_list = self.services_list()
        if not server_list:
            return None
        default = None
        for i in server_list:
            if i.get("value") == "nginx":
                default = "nginx"
                break
            elif i.get("value") == "apache":
                default = "nginx"
                break
        default = server_list[0].get("value") if not default and len(server_list) != 0 else ""
        template["field"][0]["items"] = server_list
        template["field"][0]["default"] = default
        return template

    def to_sms_msg(self, push_data: dict, push_public_data: dict) -> Tuple[str, dict]:
        return "servcies|{}".format(self.title), {
            'name': '{}'.format(get_config_value('title')),
            'product': self.service_name,
            'product1': self.service_name
        }

    def to_wx_account_msg(self, push_data: dict, push_public_data: dict) -> WxAccountMsg:
        msg = WxAccountMsg.new_msg()
        if len(self.service_name) > 14:
            service_name = self.service_name[:11] + "..."
        else:
            service_name = self.service_name
        msg.thing_type = "{} service discontinued remind".format(service_name)
        if self.restart is None:
            msg.msg = "{}service has been discontinued".format(service_name)
        elif self.restart is True:
            msg.msg = "{}ervice restarted successfully".format(service_name)
        else:
            msg.msg = "{}service restart failed".format(service_name)
        return msg


class PanelSafePushTask(BaseTask):
    def __init__(self):
        super().__init__()
        self.source_name = "panel_safe_push"
        self.template_name = "aaPanel safety alarm"
        self.title = "aaPanel safety alarm"

        self.msg_list = []

    def check_task_data(self, task_data: dict) -> Union[dict, str]:
        task_data["interval"] = 60
        return task_data

    def get_keyword(self, task_data: dict) -> str:
        return "panel_safe_push"

    def get_push_data(self, task_id: str, task_data: dict) -> Optional[dict]:
        s_list = []
        # 面板登录用户安全
        t_add, t_del, total = self.get_records_calc('login_user_safe', DB('users'))
        if t_add > 0 or t_del > 0:
            s_list.append(
                ">Change of logged-in user: <font color=#ff0000> Total:{}, Add:{}, Delete:{}</font>.".format(total,
                                                                                                             t_add,
                                                                                                             t_del))

        # 面板日志发生删除
        t_add, t_del, total = self.get_records_calc('panel_logs_safe', DB('logs'), 1)
        if t_del > 0:
            s_list.append(
                ">If the panel log is deleted, the number of deleted logs is as follows:<font color=#ff0000>{} </font>".format(
                    t_del))

        debug_str = 'Off'
        debug_status = 'False'
        # 面板开启开发者模式告警
        if os.path.exists('/www/server/panel/data/debug.pl'):
            debug_status = 'True'
            debug_str = 'On'

        skey = 'panel_debug_safe'
        tmp = public_get_cache_func(skey)['data']
        if not tmp:
            public_set_cache_func(skey, debug_status)
        else:
            if str(debug_status) != tmp:
                s_list.append(">Panel developer mode has changed, current state:{}".format(debug_str))
                public_set_cache_func(skey, debug_status)

        # 面板用户名和密码发生变更
        find = DB('users').where('id=?', (1,)).find()
        if find:
            skey = 'panel_user_change_safe'
            user_str = self.hash_md5(find['username']) + '|' + self.hash_md5(find['password'])
            tmp = public_get_cache_func(skey)['data']
            if not tmp:
                public_set_cache_func(skey, user_str)
            else:
                if user_str != tmp:
                    s_list.append(">The login account or password of the panel has been changed")
                    public_set_cache_func(skey, user_str)

        if len(s_list) == 0:
            return None
        self.msg_list = s_list
        return {"msg_list": s_list}

    @staticmethod
    def hash_md5(data: str) -> str:
        h = hashlib.md5()
        h.update(data.encode('utf-8'))
        return h.hexdigest()

    @staticmethod
    def get_records_calc(skey, table, stype=0):
        """
            @name 获取指定表数据是否发生改变
            @param skey string 缓存key
            @param table db 表对象
            @param stype : 0 计算总条数 1 只计算删除
            @return array
                total int 总数
        """
        total_add = 0
        total_del = 0

        # 获取当前总数和最大索引值
        u_count = table.count()
        u_max = table.order('id desc').getField('id')

        n_data = {'count': u_count, 'max': u_max}
        tmp = public_get_cache_func(skey)['data']
        if not tmp:
            public_set_cache_func(skey, n_data)
        else:
            n_data = tmp
            # 检测上一次记录条数是否被删除
            pre_count = table.where('id<=?', (n_data['max'])).count()
            if stype == 1:
                if pre_count < n_data['count']:  # 有数据被删除，记录被删条数
                    total_del += n_data['count'] - pre_count

                n_count = u_max - pre_count  # 上次记录后新增的条数
                n_idx = u_max - n_data['max']  # 上次记录后新增的索引差
                if n_count < n_idx:
                    total_del += n_idx - n_count
            else:

                if pre_count < n_data['count']:  # 有数据被删除，记录被删条数
                    total_del += n_data['count'] - pre_count
                elif pre_count > n_data['count']:
                    total_add += pre_count - n_data['count']

                t1_del = 0
                n_count = u_count - pre_count  # 上次记录后新增的条数

                if u_max > n_data['max']:
                    n_idx = u_max - n_data['max']  # 上次记录后新增的索引差
                    if n_count < n_idx: t1_del = n_idx - n_count

                # 新纪录除开删除，全部计算为新增
                t1_add = n_count - t1_del
                if t1_add > 0:
                    total_add += t1_add

                total_del += t1_del

            public_set_cache_func(skey, {'count': u_count, 'max': u_max})
        return total_add, total_del, u_count

    def filter_template(self, template: dict) -> Optional[dict]:
        return template

    def to_sms_msg(self, push_data: dict, push_public_data: dict) -> Tuple[str, dict]:
        return '', {}

    def to_wx_account_msg(self, push_data: dict, push_public_data: dict) -> WxAccountMsg:
        msg = WxAccountMsg.new_msg()
        msg.thing_type = "aaPanel security alarms"
        the_msg = []
        for d in self.msg_list:
            if d.find("Change of logged-in user"):
                the_msg.append("User Changes")
            if d.find("the panel log is deleted"):
                the_msg.append("the panel log is deleted")
            if d.find("Panel developer mode has changed"):
                the_msg.append("Panel developer mode has changed")
            if d.find("The login account or password"):
                the_msg.append("Account and Password change")

        msg.msg = "、".join(the_msg)
        if len(the_msg) > 20:
            msg.msg = msg.msg[:17] + "..."
        msg.next_msg = "Please log in to the panel to view the corresponding information"
        return msg


class SSHLoginTask(BaseTask):
    push_tip_file = "/www/server/panel/data/ssh_send_type.pl"

    def __init__(self):
        super().__init__()
        self.source_name = "ssh_login"
        self.template_name = "SSH login alert"
        self.title = "SSH login alert"

    def check_task_data(self, task_data: dict) -> Union[dict, str]:
        return {}

    def get_keyword(self, task_data: dict) -> str:
        return "ssh_login"

    def get_push_data(self, task_id: str, task_data: dict) -> Optional[dict]:
        return None

    def filter_template(self, template) -> dict:
        return template

    def to_sms_msg(self, push_data: dict, push_public_data: dict) -> Tuple[str, dict]:
        return "", {}

    def to_wx_account_msg(self, push_data: dict, push_public_data: dict) -> WxAccountMsg:
        login_ip = push_data.get("login_ip")
        msg = WxAccountMsg.new_msg()
        msg.thing_type = "SSH login security alert"
        if len(login_ip) == 0:  # 检查后门用户时使同
            msg.msg = "The server has a backdoor user"
            msg.next_msg = "Check the '/ect/passwd' file"
            return msg

        elif len(login_ip) > 15:
            login_ip = login_ip[:12] + "..."

        msg.msg = "login ip:{}".format(login_ip)
        msg.next_msg = "Please log in to the panel and check whether the login is secure"
        return msg

    def task_config_update_hook(self, task: dict) -> None:
        if "/www/server/panel/class" not in sys.path:
            sys.path.insert(0, "/www/server/panel/class")

        from ssh_security import ssh_security
        ssh_security().start_jian(None)

        sender = task["sender"]
        if len(sender) > 0:
            send_id = sender[0]
        else:
            return

        sender_data = SenderConfig().get_by_id(send_id)
        if sender_data:
            write_file(self.push_tip_file, sender_data["sender_type"])

    def task_config_create_hook(self, task: dict) -> None:
        return self.task_config_update_hook(task)

    def task_config_remove_hook(self, task: dict) -> None:
        if os.path.exists(self.push_tip_file):
            os.remove(self.push_tip_file)


class PanelUpdateTask(BaseTask):

    def __init__(self):
        super().__init__()
        self.source_name = "panel_update"
        self.template_name = "aaPanel update reminders"
        self.title = "aaPanel update reminders"
        self.new_ver = ''

    def _get_no_user_tip(self) -> str:
        """没有用户信息的需要，写一个临时文件做标记，并尽可能保持不变"""
        tip_file = "/www/server/panel/data/no_user_tip.pl"
        if not os.path.exists(tip_file):
            data: str = get_network_ip()
            data = "Tag files when there is no user information\n" + hashlib.sha256(data.encode("utf-8")).hexdigest()
            write_file(tip_file, data)
        else:
            data = read_file(tip_file)
            if isinstance(data, bool):
                os.remove(tip_file)
                return self._get_no_user_tip()
        return data

    def user_can_request_hour(self):
        """根据哈希值，输出一个用户可查询"""
        user_info = public_get_user_info()
        if not bool(user_info):
            user_info_str = self._get_no_user_tip()
        else:
            user_info_str = json.dumps(user_info)

        hash_value = hashlib.md5(user_info_str.encode("utf-8")).digest()
        sum_value = 0
        for i in range(4):
            sum_value = sum_value + int.from_bytes(hash_value[i * 32: (i + 1) * 32], "big")

        res = sum_value % 24
        return res

    def check_task_data(self, task_data: dict) -> Union[dict, str]:
        task_data["interval"] = 60 * 60  # 默认检测间隔时间 1 小时
        return task_data

    def check_num_rule(self, num_rule: dict) -> Union[dict, str]:
        num_rule['day_num'] = 1  # 默认一天发一次
        return num_rule

    def get_keyword(self, task_data: dict) -> str:
        return "panel_update"

    def get_push_data(self, task_id: str, task_data: dict) -> Optional[dict]:
        # 不在固定时间段内，跳过
        if self.user_can_request_hour() != datetime.now().hour:
            return
        # 面板更新日志  todo 暂时隐藏  后期可改成 ajax?action=UpdatePanel 获取更新日志
        s_url = 'https://wafapi2.aapanel.com/api/panel/updateLinux'
        try:
            res = json.loads(public_http_post(s_url, {}))
            if not res:
                return None
        except:
            return None

        n_ver = res['version']
        if res['is_beta']:
            n_ver = res['beta']['version']

        self.new_ver = n_ver

        cache_key = "panel_update_cache"
        old_ver = public_get_cache_func(cache_key)['data']
        if old_ver and old_ver != n_ver:
            s_list = [">Notification type: 面板版本更新",
                      ">当前版本：{} ".format(panel_version()),
                      ">最新版本：{}".format(n_ver)]
            return {
                "msg_list": s_list
            }
        else:
            public_set_cache_func(cache_key, n_ver)
        return None

    def filter_template(self, template: dict) -> Optional[dict]:
        return template

    def to_sms_msg(self, push_data: dict, push_public_data: dict) -> Tuple[str, dict]:
        return "", {}

    def to_wx_account_msg(self, push_data: dict, push_public_data: dict) -> WxAccountMsg:
        msg = WxAccountMsg.new_msg()
        msg.thing_type = "aaPanel update reminders"
        msg.msg = "最新版:{}已发布".format(self.new_ver)
        msg.next_msg = "您可以登录面板，执行更新"
        return msg

    def task_run_end_hook(self, res: dict) -> None:
        if res["do_send"]:
            public_set_cache_func("panel_update_cache", self.new_ver)


class ProjectStatusTask(BaseTask):

    def __init__(self):
        super().__init__()
        self.source_name = "project_status"
        self.template_name = "Project stop alarm"
        # self.title = "Project stop alarm"

        self.project_name = ''
        self.restart = None

    @staticmethod
    def _to_project_type(type_id: int):
        if type_id == 1:
            return "Java"
        if type_id == 2:
            return "Node"
        if type_id == 3:
            return "Go"
        if type_id == 4:
            return "Python"
        if type_id == 5:
            return "Other"

    @staticmethod
    def _to_project_id(type_name):
        if type_name == "Java":
            return 0
        if type_name == "Node":
            return 1
        if type_name == "Go":
            return 2
        if type_name == "Python":
            return 3
        if type_name == "Other":
            return 4

    @staticmethod
    def _to_project_model(type_id: int):
        if type_id == 1:
            return "javaModel"
        if type_id == 2:
            return "nodejsModel"
        if type_id == 3:
            return "goModel"
        if type_id == 4:
            return "pythonModel"
        if type_id == 5:
            return "otherModel"

    def get_title(self, task_data: dict) -> str:
        return "Project stop alarm -- {}".format(self._get_project_name(task_data["project"]))

    def check_task_data(self, task_data: dict) -> Union[dict, str]:
        if not (isinstance(task_data["cycle"], int) and 1 <= task_data["cycle"] <= 5):
            return 'Unsupported project types.'
        sql = DB("sites")
        web_info = sql.where(
            "project_type = ? and id = ?",
            (self._to_project_type(task_data["cycle"]), task_data["project"])
        ).field("id,name").find()

        if not web_info:
            return 'If you do not have this item, you cannot set an alarm'

        if task_data["count"] not in (1, 2):
            return "Auto-restart selection error"
        if not (isinstance(task_data['interval'], int) and task_data['interval'] >= 60):
            return "The interval time parameter is incorrect, at least 60 seconds"
        return task_data

    def get_web_list(self) -> List:
        items_by_type = [[], [], [], [], []]
        res_list = DB('sites').field('id,name,project_type').select()
        for i in res_list:
            if i["project_type"] == "PHP" or i["project_type"] == "proxy":
                continue
            idx: int = self._to_project_id(i["project_type"])
            if idx is None:
                continue
            items_by_type[idx].append({
                "title": i["name"],
                "value": i["id"]
            })
        return items_by_type

    def get_keyword(self, task_data: dict) -> str:
        return "{}_{}".format(task_data["cycle"], self._get_project_name(task_data["project"]))

    @staticmethod
    def _get_project_name(project_id: int) -> str:
        data = DB('sites').where('id = ?', (project_id,)).field('id,name').find()
        if isinstance(data, dict):
            return data["name"]
        return "<unknown>"

    def get_push_data(self, task_id: str, task_data: dict) -> Optional[dict]:
        if "/www/server/panel/class" not in sys.path:
            sys.path.insert(0, "/www/server/panel/class")

        model_obj = import_module(".{}".format(self._to_project_model(task_data["cycle"])), package="projectModel")
        model_main_obj = model_obj.main()
        running, project_name = getattr(model_main_obj, "get_project_status")(task_data["project"])
        if running is not False:
            return None

        s_list = [
            ">Project type: " + self._to_project_type(task_data["cycle"]),
            ">Project name: " + project_name,
            ">Project state: The project status is stopped"]
        self.project_name = project_name

        if int(task_data["count"]) == 1:
            get_obj = GET_CLASS()
            get_obj.project_name = project_name
            result = getattr(model_main_obj, "start_project")(get_obj)
            if result["status"] is True:
                self.restart = True
                s_list[
                    2] = ">Project state: Check that the project status is stopped, and it has been restarted successfully"
            else:
                self.restart = False
                s_list[2] = ">Project state: Check that the project status is stopped, try to restart but fail"

        self.title = self.get_title(task_data)

        return {
            "msg_list": s_list,
        }

    def filter_template(self, template: dict) -> Optional[dict]:
        _, web_by_type = web_info()
        template["field"][1]["all_items"] = web_by_type
        template["field"][1]["items"] = web_by_type[0]
        if not web_by_type:
            return None
        return template

    def to_sms_msg(self, push_data: dict, push_public_data: dict) -> Tuple[str, dict]:
        return '', {}

    def to_wx_account_msg(self, push_data: dict, push_public_data: dict) -> WxAccountMsg:
        msg = WxAccountMsg.new_msg()
        if len(self.project_name) >= 14:
            project_name = self.project_name[:11] + "..."
        else:
            project_name = self.project_name
        msg.thing_type = "Project stop alarm"
        if self.restart is None:
            msg.msg = "Project {} has been stopped".format(project_name)
        elif self.restart is True:
            msg.msg = "Project {} was successfully restarted".format(project_name)
        else:
            msg.msg = "Project {} failed to restart".format(project_name)
        return msg


class ViewMsgFormat(object):
    _FORMAT = {
        "1": (
            lambda x: "<span>Time remaining less than {} days {}</span>".format(
                x["task_data"].get("cycle"),
                ("(If it is not processed, it will be resent 1 time the next day for %d days)" % x.get("number_rule",
                                                                                                       {}).get("total",
                                                                                                               0)) if x.get(
                    "number_rule", {}).get("total", 0) else ""
            )
        ),
        "2": (),
        "3": (),
        "8": (
            lambda x: "<span>Alert when the panel is logged in</span>"
        ),
        "7": (
            lambda x: "<span>When an SSH login is detected, an alarm is generated</span>"
        ),
        "4": (
            lambda
                x: "<span>Triggered by {} consecutive failed logins within {} minutes, and tested again every {} seconds</span>".format(
                x["task_data"].get("count"),
                x["task_data"].get("cycle"),
                x["task_data"].get("interval"),
            )
        ),
        "5": (
            lambda
                x: "<span>A notification is sent once when the service is stopped, and it is detected again after {} seconds</span>".format(
                x["task_data"].get("interval"))
        ),
        "9": (
            lambda
                x: "<span>A notification is sent when the item is stopped, and the test is repeated after {} seconds, {} times per day</span>".format(
                x["task_data"].get("interval"),
                x.get("number_rule", {}).get("day_num", 0))
        ),
        "6": (
            lambda
                x: "<span>Alerts are sent when dangerous operations such as user changes, panel logs are deleted, and developers are enabled</span>"
        ),
        "10": (
            lambda x: "<span>A notification is sent once when a new version is detected</span>"
        )
    }

    def get_msg(self, task: dict) -> Optional[str]:
        if task["template_id"] in ["1", "2", "3"]:
            return self._FORMAT["1"](task)
        if task["template_id"] in self._FORMAT:
            return self._FORMAT[task["template_id"]](task)
        return None
