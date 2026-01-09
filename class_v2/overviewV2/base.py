# coding: utf-8
# -------------------------------------------------------------------
# aaPanel
# -------------------------------------------------------------------
# Copyright (c) 2014-2099 aaPanel(www.aapanel.com) All rights reserved.
# -------------------------------------------------------------------
# Author: aapanel
# -------------------------------------------------------------------

# ------------------------------
# overview app base
# ------------------------------
import json
import os
import time
from datetime import datetime, timedelta, date

import public

public.sys_path_append("class_v2/")

COLORS = {
    "red": "text-error",
    "gray": "text-desc",
    "green": "text-primary",
    "orange": "text-warning",
}

DISPLAY = {
    "sites": {
        "icon": "i-dashicons:admin-site-alt3",
        "desc": public.lang("Manage and monitor the status of your website")
    },
    "ftps": {
        "icon": "i-carbon:ibm-cloud-direct-link-1-dedicated",
        "desc": public.lang("Monitor FTP accounts and transfer status")
    },
    "databases": {
        "icon": "i-carbon:data-base",
        "desc": public.lang("Monitor database operation and performance metrics")
    },
    "security": {
        "icon": "i-carbon:security",
        "desc": public.lang("View the current security threats and risks of the system")
    },
    "monitor": {
        "icon": "i-carbon:meter",
        "desc": public.lang("Comprehensive resource usage monitoring overview")
    },
    "btwaf": {
        "icon": " i-hugeicons:firewall",
        "desc": public.lang("WAF firewall interception and protection details")
    },
    "tamper_core": {
        "icon": "i-carbon:locked",
        "desc": public.lang("Prevent core operation and protection status")
    },
    "ssh_log": {
        "icon": "i-carbon:terminal",
        "desc": public.lang("Monitor SSH login attempts and security status")
    },
    "ssl": {
        "icon": "i-carbon:certificate",
        "desc": public.lang("SSL certificate status")
    },
    "cron": {
        "icon": "i-carbon:time",
        "desc": public.lang("Scheduled task status")
    },
    "alarm_logs": {
        "icon": "i-carbon:reminder",
        "desc": public.lang("Real-time monitoring and alarm tasks")
    },
}


# noinspection PyUnusedLocal
class OverViewBase:
    __db_objs = {}

    def _base(self, name: str, params_list: list) -> list:
        if not params_list:
            params_list = []

        value_list = []
        if name == "sites":
            for params in params_list:
                where = ""
                if params["source"] != "all":
                    where = "LOWER(project_type)=LOWER('{}')".format(params["source"])
                if where:
                    start_num = public.M("sites").where(where + " and status='1'", ()).count()
                    stop_num = public.M("sites").where(where + " and status='0'", ()).count()
                else:
                    start_num = public.M("sites").where("status='1'", ()).count()
                    stop_num = public.M("sites").where("status='0'", ()).count()
                value_list = [
                    {
                        "desc": public.lang("Running"),
                        "data": start_num,
                        "color": COLORS["green"]
                    },
                    {
                        "desc": public.lang("Stopped"),
                        "data": stop_num,
                        "color": COLORS["red"]
                    },
                    {
                        "desc": public.lang("ALL"),
                        "data": public.M("sites").where(where, ()).count(),
                        "color": COLORS["gray"]
                    }
                ]

        elif name == "ftps":
            data = public.M("ftps").count()
            if not isinstance(data, int):
                data = 0
            value_list = [{
                "desc": public.lang("Accounts"),
                "data": data,
                "color": COLORS["green"]
            }]

        elif name == "databases":
            for params in params_list:
                if params["source"] != "redis":
                    if params["source"] == "all":
                        data = public.M("databases").count()
                    else:
                        data = public.M("databases").where(
                            "LOWER(type)=LOWER(?)", (params["source"],)
                        ).count()
                else:
                    from databaseModelV2.redisModel import panelRedisDB
                    data = panelRedisDB().get_options(None).get("databases", 16)
                value_list = [
                    {
                        "desc": params["name"],
                        "data": data,
                        "color": COLORS["green"]
                    }
                ]

        else:
            value_list = []
        return value_list

    def _corn(self, name: str, params_list: list) -> list:
        return []

    def _security(self, name: str, params_list: list) -> list:
        from projectModelV2.safecloudModel import main
        cloud_safe_info = main().get_pending_alarm_trend(None)
        if cloud_safe_info.get("status") != 0:
            return []

        trend_list = public.find_value_by_key(
            cloud_safe_info, "trend_list", default=[]
        )
        last_scan_ts = ""
        if trend_list:
            last_scan_ts = trend_list[-1].get("timestamp", "")
        last_scan_time = time.strftime(
            "%Y/%m/%d %H:%M:%S", time.localtime(last_scan_ts)
        ) if last_scan_ts else public.lang("Never Scanned")

        try:
            last_total = public.find_value_by_key(cloud_safe_info, "total", default=0)
        except:
            last_total = 0
        return [
            {
                "desc": public.lang("Security Risk"),
                "data": last_total,
                "color": COLORS["gray"] if last_total == 0 else COLORS["red"]
            },
            {
                "desc": public.lang("Last Scan"),
                "data": last_scan_time,
                "color": COLORS["gray"]
            }
        ]

    def _btwaf(self, name: str, params_list: list) -> list:
        default = [
            {
                "desc": public.lang("Today Intercept"),
                "data": 0,
                "color": COLORS["orange"]
            },
            {},
            {
                "desc": public.lang("Yesterday Intercept"),
                "data": 0,
                "color": COLORS["orange"]
            }
        ]
        waf_db_path = "/www/server/btwaf/totla_db/totla_db.db"
        if not os.path.exists(waf_db_path):
            return default

        today_time = int(datetime.now().replace(hour=0, minute=0, second=0, microsecond=0).timestamp())
        yesterday_time = today_time - 86400
        result = []
        try:
            today_data = public.M("totla_log").dbfile(waf_db_path).field('time').where(
                "time>=?", (today_time,)
            ).order('id desc').count()
            if not isinstance(today_data, int):
                raise Exception
        except Exception as e:
            public.print_log("Failed to get WAF today intercept data")
            today_data = 0

        result.append({
            "desc": public.lang("Today Intercept"),
            "data": 0,
            "color": COLORS["orange"]
        })
        result.append({})
        try:
            yesterday_data = public.M("totla_log").dbfile(waf_db_path).field('time').where(
                "time>=? and time<=?", (yesterday_time, today_time)
            ).order('id desc').count()
            if not isinstance(yesterday_data, int):
                raise Exception
        except Exception:
            yesterday_data = 0

        result.append({
            "desc": public.lang("Yesterday Intercept"),
            "data": yesterday_data,
            "color": COLORS["orange"]
        })
        return result if result else default

    def _tamper_core(self, name: str, params_list: list) -> list:
        tamper_core_dir = "/www/server/tamper/total"
        default = [
            {
                "desc": public.lang("Today Intercept"),
                "data": 0,
                "color": COLORS["gray"]
            },
            {},
            {
                "desc": public.lang("Yesterday Intercept"),
                "data": 0,
                "color": COLORS["gray"]
            }
        ]
        if not os.path.exists(tamper_core_dir):
            return default
        result = []
        today_time = date.today()
        yesterday_time = today_time - timedelta(days=1)
        listdirs = os.listdir(tamper_core_dir)

        if not listdirs:
            return default

        for p_name in os.listdir(tamper_core_dir):
            dir_path = os.path.join(tamper_core_dir, str(p_name))
            today_path = os.path.join(dir_path, "{}.json".format(today_time))
            if os.path.isfile(today_path):
                today_info = public.readFile(today_path)
                today_info = json.loads(today_info)
                for info in today_info.values():
                    result.append({
                        "desc": public.lang("Today Intercept"),
                        "data": sum(info.values()),
                        "color": COLORS["orange"]
                    })
            else:
                result.append({
                    "desc": public.lang("Today Intercept"),
                    "data": 0,
                    "color": COLORS["gray"]
                })
            result.append({})
            yesterday_path = os.path.join(dir_path, "{}.json".format(yesterday_time))
            if os.path.isfile(yesterday_path):
                yesterday_info = public.readFile(yesterday_path)
                yesterday_info = json.loads(yesterday_info)
                for info in yesterday_info.values():
                    result.append({
                        "desc": public.lang("Yesterday Intercept"),
                        "data": sum(info.values()),
                        "color": COLORS["orange"]
                    })
            else:
                result.append({
                    "desc": public.lang("Yesterday Intercept"),
                    "data": 0,
                    "color": COLORS["gray"]
                })

        for r in result:
            if int(r.get("data", 0)) > 0:
                r["color"] = COLORS["orange"]
            elif int(r.get("data", 0)) == 0:
                r["color"] = COLORS["gray"]
        return result if result else default

    def _ssh_log(self, name: str, params_list: list) -> list:
        try:
            params_map = {
                "all": "all",
                "Accepted": "success",
                "Failed": "error"
            }
            from mod.project.ssh.comMod import main
            params = public.find_value_by_key(params_list, "source", default="all")
            params = params_map.get(params, "all")
            ssh_info = main().get_ssh_intrusion(None)
            if ssh_info.get("status") != 0:
                return []
            ssh = ssh_info.get("message", {})
            error = int(ssh.get("today_error", 0))
            success = int(ssh.get("today_success", 0))
            if params == "error":
                return [
                    {
                        "desc": public.lang("Failed"),
                        "data": error,
                        "color": COLORS["gray"] if error == 0 else COLORS["red"]
                    }
                ]
            elif params == "success":
                return [
                    {
                        "desc": public.lang("Success"),
                        "data": success,
                        "color": COLORS["green"]
                    }
                ]
            else:
                return [
                    {
                        "desc": public.lang("Success"),
                        "data": success,
                        "color": COLORS["green"]
                    },
                    {
                        "desc": public.lang("Failed"),
                        "data": error,
                        "color": COLORS["gray"] if error == 0 else COLORS["red"]
                    },
                    {
                        "desc": public.lang("ALL"),
                        "data": error + success,
                        "color": COLORS["gray"]
                    }
                ]
        except Exception:
            public.print_log("Failed to get SSH log information")
            return []

    def _monitor(self, name: str, params_list: list) -> list:
        try:
            params_data = {
                "pv": "SUM(pv_number) as pv",
                "uv": "SUM(uv_number) as uv",
                "ip": "SUM(ip_number) as ip",
                "spider": "SUM(spider_count) as spider",
            }
            params_desc = {
                "pv": public.lang("Page Views"),
                "uv": public.lang("Visitors"),
                "ip": public.lang("IPs"),
                "spider": public.lang("Spiders"),
            }
            site_name = params_list[0]['source']
            param = params_list[1]['source']
            run_path = "{}/monitor".format(public.get_setup_path())
            db_file = "{}/data/dbs/{}/{}.db".format(run_path, site_name, "request_total")
            if db_file not in self.__db_objs:
                if not os.path.exists(db_file) or os.path.getsize(db_file) == 0:
                    return [
                        {
                            "desc": site_name,
                        },
                        {},
                        {
                            "desc": f'{public.lang("Today")}',
                            "data": 0,
                            "color": COLORS["gray"]
                        },
                        {
                            "desc": f'{public.lang("Yesterday")}',
                            "data": 0,
                            "color": COLORS["gray"]
                        }
                    ]
                else:
                    import db
                    db_obj = db.Sql()
                    db_obj._Sql__DB_FILE = db_file
                    self.__db_objs[db_file] = db_obj
            else:
                db_obj = self.__db_objs[db_file]

            now_time = datetime.now().strftime('%Y%m%d')
            last_time = (datetime.now() - timedelta(days=1)).strftime('%Y%m%d')
            result = [
                {
                    "desc": site_name,
                },
                {},
            ]
            for i in [now_time, last_time]:
                sql = f'select {params_data[param]} from request_total where date="{i}";'
                data = db_obj.table("request_total").query(sql)
                try:
                    data = data[0][0]
                    if data is None:
                        data = 0
                except:
                    data = 0

                desc = public.lang("Today") if i == now_time else public.lang("Yesterday")
                result.append(
                    {
                        "desc": f"{desc}",
                        "data": data,
                        "color": COLORS["gray"]
                    }
                )
            return result
        except Exception as e:
            import traceback
            public.print_log(traceback.format_exc())
        return []

    def _alarm_logs(self, name: str, params_list: list) -> list:
        today = datetime.now().strftime("%Y-%m-%d 00:00:00")
        task_logs = public.M("logs").where(
            "type=? AND addtime >=?", ("Alarm notification", today)
        ).count()
        return [
            {
                "desc": public.lang("Today"),
                "data": task_logs,
                "color": COLORS["gray"] if task_logs == 0 else COLORS["orange"]
            }
        ]

    def _base_ssl(self, select: str) -> list:
        from ssl_domainModelV2.model import DnsDomainSSL, Q
        f_fields = ("hash", "subject", "not_after", "not_after_ts")
        data = []
        now = round((time.time() + 86400 * 30) * 1000)
        ip_ts = round((time.time() + 86400 * 3) * 1000)
        ip = public.GetLocalIp()
        if select == "normal":
            # 上次续签为成功, 且证书未过期
            data = DnsDomainSSL.objects.filter(
                Q(renew_status=1) & (
                        Q(subject__ne=ip, not_after_ts__gt=now) | Q(subject=ip, not_after_ts__gt=ip_ts)
                )
            ).fields(*f_fields).as_list()

        elif select == "expirin_soon":
            # 上次续签为成功, 但证书即将过期
            data = DnsDomainSSL.objects.filter(
                Q(renew_status=1) & (
                        Q(subject__ne=ip, not_after_ts__lte=now) | Q(subject=ip, not_after_ts__lte=ip_ts)
                )
            ).fields(*f_fields).as_list()

        elif select == "renew_fail":
            # 上次续签为失败
            data = DnsDomainSSL.objects.filter(
                renew_status=0
            ).fields(*f_fields).as_list()

        data = [{**d, "tag": select} for d in data]
        return data

    def _ssl(self, name: str, params_list: list) -> list:
        try:
            from ssl_domainModelV2.model import DnsDomainSSL
            expirin_soon = len(self._base_ssl("expirin_soon")) or 0
            renew_fail = len(self._base_ssl("renew_fail")) or 0
            return [
                {
                    "desc": public.lang("Expirin Soon"),
                    "data": expirin_soon,
                    "color": COLORS["orange"] if expirin_soon > 0 else COLORS["gray"]
                },
                {
                    "desc": public.lang("Renew Fail"),
                    "data": renew_fail,
                    "color": COLORS["red"] if renew_fail > 0 else COLORS["gray"]
                },
                {
                    "desc": public.lang("ALL"),
                    "data": DnsDomainSSL.objects.all().count() or 0,
                    "color": COLORS["gray"]
                }
            ]
        except Exception:
            import traceback
            public.print_log("Failed to get SSL information: {}".format(traceback.format_exc()))
        return []
