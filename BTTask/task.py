#!/bin/python
# coding: utf-8
# +-------------------------------------------------------------------
# | aaPanel
# +-------------------------------------------------------------------
# | Copyright (c) 2015-2016 aaPanel(www.aapanel.com) All rights reserved.
# +-------------------------------------------------------------------
# | Author: aapanel
# +-------------------------------------------------------------------

# ------------------------------
# aa Background Schedule Task
# ------------------------------
import gc
import json
import os
import subprocess
import sys
import threading
import time
import traceback
from datetime import datetime, timedelta
from typing import Optional

import psutil

sys.path.insert(0, "/www/server/panel/class/")
from public.hook_import import hook_import

try:
    hook_import()
except:
    pass

import db
from panelTask import bt_task
from script.restart_services import RestartServices
from BTTask.brain import SimpleBrain
from BTTask.conf import (
    BASE_PATH,
    PYTHON_BIN,
    exlogPath,
    isTask,
    logger,
)


def write_file(path: str, content: str, mode='w'):
    try:
        fp = open(path, mode)
        fp.write(content)
        fp.close()
        return True
    except:
        try:
            fp = open(path, mode, encoding="utf-8")
            fp.write(content)
            fp.close()
            return True
        except:
            return False


def read_file(filename: str):
    fp = None
    try:
        fp = open(filename, "rb")
        f_body_bytes: bytes = fp.read()
        f_body = f_body_bytes.decode("utf-8", errors='ignore')
        fp.close()
        return f_body
    except Exception:
        return False
    finally:
        if fp and not fp.closed:
            fp.close()


def exec_shell(cmdstring, timeout=None, shell=True, cwd=None):
    """
        @name 执行命令
        @param cmdstring 命令 [必传]
        @param timeout 超时时间
        @param shell 是否通过shell运行
        @return 命令执行结果
    """
    try:
        result = subprocess.run(
            cmdstring,
            shell=shell,
            cwd=cwd,
            timeout=timeout,
            capture_output=True,
            text=True,  # 直接以文本模式处理输出
            encoding='utf-8',
            errors='ignore',
            env=os.environ
        )
        return result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        return 'Timed out', ''
    except Exception:
        return '', traceback.format_exc()


task_obj = bt_task()
task_obj.not_web = True
bt_box_task = task_obj.start_task_new


def task_ExecShell(fucn_name: str, **kw):
    """
    仅运行 /www/server/panel/BTTask/task_script.py 下的包装函数
    可通过 kw 参数扩展前置检查，例如:
      - kw['paths_exists']: List [str]
      (例如, 检查邮局插件是否存在, 任何一个检查不存在则不执行
      paths_exists=['/www/server/panel/plugin/mail_sys/mail_sys_main.py', '/www/vmail'])

    """
    if PYTHON_BIN in fucn_name:
        raise ValueError("valid function name required")

    if kw.get("paths_exists") and isinstance(kw["paths_exists"], list):
        for p in kw["paths_exists"]:
            try:
                if not os.path.exists(str(p)):
                    logger.debug(f"Skip task [{fucn_name}]: path not exists")
                    return
            except Exception as e:
                raise ValueError(f"Invalid path in paths_exists: '{p}', error: {e}")

    cmd = f"{PYTHON_BIN} /www/server/panel/BTTask/task_script.py {fucn_name}"
    _, err = exec_shell(cmd)
    if err:
        raise Exception(err)
    del err, cmd


# 系统监控任务
# noinspection PyUnusedLocal
def systemTask():
    cycle = 60
    control_conf = f"{BASE_PATH}/data/control.conf"

    def get_mem_used_percent() -> float:
        try:
            mem = psutil.virtual_memory()
            total = mem.total / 1024 / 1024
            free = mem.free / 1024 / 1024
            buffers = getattr(mem, "buffers", 0) / 1024 / 1024
            cached = getattr(mem, "cached", 0) / 1024 / 1024
            used = total - free - buffers - cached
            return used / (total / 100.0) if total else 1.0
        except Exception:
            return 1.0

    def get_load_average():
        one, five, fifteen = os.getloadavg()
        max_v = psutil.cpu_count() * 2
        return {
            "one": float(one),
            "five": float(five),
            "fifteen": float(fifteen),
            "max": max_v,
            "limit": max_v,
            "safe": max_v * 0.75,
        }

    def ensure_tables():
        with db.Sql() as sql:
            sql = sql.dbfile("system")
            sql.execute(
                """CREATE TABLE IF NOT EXISTS `load_average`(
                    `id` INTEGER PRIMARY KEY KEY AUTOINCREMENT,
                    `pro` REAL, `one` REAL, `five` REAL, `fifteen` REAL, `addtime` INTEGER
                )""",
                (),
            )
            sql.execute(
                """CREATE TABLE IF NOT EXISTS `network`(
                    `id` INTEGER PRIMARY KEY KEY AUTOINCREMENT,
                    `up` INTEGER, `down` INTEGER, `total_up` INTEGER, `total_down` INTEGER,
                    `down_packets` INTEGER, `up_packets` INTEGER, `addtime` INTEGER
                )""",
                (),
            )
            sql.execute(
                """CREATE TABLE IF NOT EXISTS `cpuio`(
                    `id` INTEGER PRIMARY KEY KEY AUTOINCREMENT,
                    `pro` INTEGER, `mem` INTEGER, `addtime` INTEGER
                )""",
                (),
            )
            sql.execute(
                """CREATE TABLE IF NOT EXISTS `diskio`(
                    `id` INTEGER PRIMARY KEY KEY AUTOINCREMENT,
                    `read_count` INTEGER, `write_count` INTEGER,
                    `read_bytes` INTEGER, `write_bytes` INTEGER,
                    `read_time` INTEGER, `write_time` INTEGER,
                    `addtime` INTEGER
                )""",
                (),
            )

    def read_keep_days() -> int:
        try:
            day = int(read_file(control_conf) or 30)
            return day if day >= 1 else 0
        except Exception:
            return 30

    def collect_network(net_up, net_down):
        net_io = psutil.net_io_counters(pernic=True)
        up_total = down_total = 0
        up = down = 0.0
        down_packets = {}
        up_packets = {}

        for nic, counters in net_io.items():
            sent, recv = counters[:2]
            if nic not in net_up:
                net_up[nic] = sent
                net_down[nic] = recv

            up_total += sent
            down_total += recv

            dp = round(float((recv - net_down[nic]) / 1024) / cycle, 2)
            up_p = round(float((sent - net_up[nic]) / 1024) / cycle, 2)
            down_packets[nic] = dp
            up_packets[nic] = up_p
            up += up_p
            down += dp

            net_up[nic] = sent
            net_down[nic] = recv

        return {
            "upTotal": up_total,
            "downTotal": down_total,
            "up": up,
            "down": down,
            "downPackets": down_packets,
            "upPackets": up_packets,
        }

    diskstats_exists = os.path.exists("/proc/diskstats")
    diskio_prev = None

    try:
        ensure_tables()
        import process_task
        proc_task_obj = process_task.process_task()
        net_up, net_down = {}, {}
        while True:
            if not os.path.exists(control_conf):
                time.sleep(10)
                continue
            keep_days = read_keep_days()
            if keep_days < 1:
                time.sleep(10)
                continue
            addtime = int(time.time())
            deltime = addtime - (keep_days * 86400)
            try:
                cpu_used = proc_task_obj.get_monitor_list(addtime)
                mem_used = get_mem_used_percent()
                network_info = collect_network(net_up, net_down)
                disk_info = None
                disk_ios_ok = True
                if diskstats_exists:
                    try:
                        diskio_now = psutil.disk_io_counters()
                        if diskio_prev is None:
                            diskio_prev = diskio_now
                        disk_info = {
                            "read_count": int((diskio_now.read_count - diskio_prev.read_count) / cycle),
                            "write_count": int((diskio_now.write_count - diskio_prev.write_count) / cycle),
                            "read_bytes": int((diskio_now.read_bytes - diskio_prev.read_bytes) / cycle),
                            "write_bytes": int((diskio_now.write_bytes - diskio_prev.write_bytes) / cycle),
                            "read_time": int((diskio_now.read_time - diskio_prev.read_time) / cycle),
                            "write_time": int((diskio_now.write_time - diskio_prev.write_time) / cycle),
                        }
                        diskio_prev = diskio_now
                    except Exception:
                        disk_ios_ok = False
                load_average = get_load_average()
                lpro = round((load_average["one"] / load_average["max"]) * 100, 2) if load_average["max"] else 0
                if lpro > 100:
                    lpro = 100

                with db.Sql().dbfile("system") as sql:
                    sql.table("cpuio").add("pro,mem,addtime", (cpu_used, mem_used, addtime))
                    sql.table("cpuio").where("addtime<?", (deltime,)).delete()

                    sql.table("network").add(
                        "up,down,total_up,total_down,down_packets,up_packets,addtime",
                        (
                            network_info["up"],
                            network_info["down"],
                            network_info["upTotal"],
                            network_info["downTotal"],
                            json.dumps(network_info["downPackets"]),
                            json.dumps(network_info["upPackets"]),
                            addtime,
                        ),
                    )
                    sql.table("network").where("addtime<?", (deltime,)).delete()

                    if diskstats_exists and disk_ios_ok and disk_info:
                        sql.table("diskio").add(
                            "read_count,write_count,read_bytes,write_bytes,read_time,write_time,addtime",
                            (
                                disk_info["read_count"],
                                disk_info["write_count"],
                                disk_info["read_bytes"],
                                disk_info["write_bytes"],
                                disk_info["read_time"],
                                disk_info["write_time"],
                                addtime,
                            ),
                        )
                        sql.table("diskio").where("addtime<?", (deltime,)).delete()

                    sql.table("load_average").add(
                        "pro,one,five,fifteen,addtime",
                        (lpro, load_average["one"], load_average["five"], load_average["fifteen"], addtime),
                    )
                    sql.table("load_average").where("addtime<?", (deltime,)).delete()
            except Exception:
                import traceback
                logger.error(traceback.format_exc())
            finally:
                del cpu_used, mem_used, network_info, disk_info, load_average
                gc.collect()
            time.sleep(cycle)
    except Exception:
        import traceback
        logger.error(traceback.format_exc())
    finally:
        gc.collect()


def check502Task():
    task_ExecShell("check502task")


# 服务守护
def daemon_service():
    try:
        obj = RestartServices()
        obj.main()
        del obj
    finally:
        gc.collect()


# 重启面板服务
def restart_panel():
    def service_panel(action='reload'):
        if not os.path.exists('{}/init.sh'.format(BASE_PATH)):
            os.system("curl -k https://node.aapanel.com/install/update_7.x_en.sh|bash &")
        else:
            os.system("nohup bash /www/server/panel/init.sh {} > /dev/null 2>&1 &".format(action))
        logger.info("Panel Service: {}".format(action))

    rtips = '{}/data/restart.pl'.format(BASE_PATH)
    reload_tips = '{}/data/reload.pl'.format(BASE_PATH)

    if os.path.exists(rtips):
        os.remove(rtips)
        service_panel('restart')
    if os.path.exists(reload_tips):
        os.remove(reload_tips)
        service_panel('reload')


# 定时任务去检测邮件信息
def send_mail_time():
    if not os.path.exists('/www/server/panel/plugin/mail_sys/mail_sys_main.py') or not os.path.exists('/www/vmail'):
        return
    exec_shell("{} /www/server/panel/script/mail_task.py".format(PYTHON_BIN))


# 面板消息提醒
def check_panel_msg():
    exec_shell("{} /www/server/panel/script/check_msg.py".format(PYTHON_BIN))


# 面板推送消息
def push_msg():
    def _read_file(file_path: str) -> Optional[list]:
        if not os.path.exists(file_path):
            return None
        content = read_file(file_path)
        if not content:
            return None
        try:
            return json.loads(content)
        except:
            return []

    sender_path = f"{BASE_PATH}/data/mod_push_data/sender.json"
    task_path = f"{BASE_PATH}/data/mod_push_data/task.json"
    sender_info = _read_file(sender_path) or []
    work = False
    for s in sender_info:
        # default sender_type sms data is {}
        if s.get("sender_type") != "sms" and s.get("data"):
            work = True
            break
    if not work:
        return
    if not _read_file(task_path):
        return
    exec_shell("{} /www/server/panel/script/push_msg.py".format(PYTHON_BIN))



# 检测面板授权
# noinspection PyUnboundLocalVariable
def panel_auth():
    pro_file = '/www/server/panel/data/panel_pro.pl'
    update_file = '/www/server/panel/data/now_update_pro.pl'
    if os.path.exists(pro_file):
        try:
            from BTPanel import cache
        except Exception as e:
            logger.error("Failed to import cache from BTPanel: {}".format(e))
            cache = None
        if cache:
            key = 'pro_check_sdfjslk'
            res = cache.get(key)
        if os.path.exists(update_file) or res is None:
            os.system('nohup {} /www/server/panel/script/check_auth.py > /dev/null 2>&1 &'.format(PYTHON_BIN))
            if cache:
                cache.set(key, 'sddsf', 3600)
    if os.path.exists(update_file):
        os.remove(update_file)


def count_ssh_logs():
    task_ExecShell("count_ssh_logs")


# 每天提交一次昨天的邮局发送总数
def submit_email_statistics():
    task_ExecShell(
        "submit_email_statistics",
        paths_exists=[
            "/www/server/panel/plugin/mail_sys/mail_sys_main.py",
            "/www/vmail",
        ])


# 每天一次 提交今天之前的统计数据
def submit_module_call_statistics():
    task_ExecShell("submit_module_call_statistics")


def mailsys_domain_restrictions():
    if not os.path.exists('/www/server/panel/plugin/mail_sys/mail_send_bulk.py'):
        return

    if not os.path.exists('/www/vmail'):
        return

    yesterday = datetime.now() - timedelta(days=1)
    yesterday = yesterday.strftime('%Y-%m-%d')
    cloud_yesterday_submit = '{}/data/{}_update_mailsys_domain_restrictions.pl'.format(
        BASE_PATH, yesterday
    )
    if os.path.exists(cloud_yesterday_submit):
        return

    if os.path.exists("/www/server/panel/plugin/mail_sys"):
        sys.path.insert(1, "/www/server/panel/plugin/mail_sys")

    # 检查版本 检查是否能查询额度  剩余额度
    import public.PluginLoader as plugin_loader
    bulk = plugin_loader.get_module('{}/plugin/mail_sys/mail_send_bulk.py'.format(BASE_PATH))
    SendMailBulk = bulk.SendMailBulk
    try:
        SendMailBulk()._get_user_quota()
    except:
        logger.error(traceback.format_exc())
        return

    # 添加标记
    write_file(cloud_yesterday_submit, '1')
    # 删除前天标记
    before_yesterday = datetime.now() - timedelta(days=2)
    before_yesterday = before_yesterday.strftime('%Y-%m-%d')
    cloud_before_yesterday_submit = '{}/data/{}_update_mailsys_domain_restrictions.pl'.format(
        BASE_PATH, before_yesterday
    )
    if os.path.exists(cloud_before_yesterday_submit):
        os.remove(cloud_before_yesterday_submit)
    return


def mailsys_domain_blecklisted_alarm():
    task_ExecShell(
        "mailsys_domain_blecklisted_alarm",
        paths_exists=[
            "/www/server/panel/plugin/mail_sys/mail_sys_main.py",
            "/www/vmail",
        ]
    )


def update_vulnerabilities():
    task_ExecShell("update_vulnerabilities")


# 邮件域名邮箱使用限额告警
def mailsys_quota_alarm():
    try:
        if not os.path.exists('/www/server/panel/plugin/mail_sys/mail_sys_main.py') or not os.path.exists(
                '/www/vmail'):
            return

        script = '/www/server/panel/plugin/mail_sys/script/check_quota_alerts.py'
        if not os.path.exists(script):
            return

        cmd = f"btpython {script}"
        exec_shell(cmd)
    except:
        pass


# 邮局更新域名邮箱使用量
def mailsys_update_usage():
    try:
        if not os.path.exists(
                '/www/server/panel/plugin/mail_sys/mail_sys_main.py'
        ) or not os.path.exists('/www/vmail'):
            return
        script = '/www/server/panel/plugin/mail_sys/script/update_usage.py'
        if not os.path.exists(script):
            return
        cmd = f"btpython {script}"
        exec_shell(cmd)
    except:
        pass


# 邮局自动回复
def auto_reply_tasks():
    task_ExecShell(
        "auto_reply_tasks",
        paths_exists=[
            "/www/server/panel/plugin/mail_sys/mail_sys_main.py",
            "/www/vmail",
        ]
    )


# 邮局自动扫描异常邮箱
def auto_scan_abnormal_mail():
    task_ExecShell(
        "auto_scan_abnormal_mail",
        paths_exists=[
            "/www/server/panel/plugin/mail_sys/mail_sys_main.py",
            "/www/vmail",
        ]
    )


# 每6小时aa默认ssl检查
def domain_ssl_service():
    # check 6h, inside
    task_ExecShell("make_suer_ssl_task")


# 每隔20分钟更新一次网站报表数据
def update_monitor_requests():
    task_ExecShell("update_monitor_requests")


# 每隔20分钟更新一次waf报表数据
def update_waf_config():
    task_ExecShell("update_waf_config")


# 每6小时进行恶意文件扫描
def malicious_file_scanning():
    task_ExecShell("malicious_file_scanning")


# 多服务守护任务，仅在多服务下执行，每5分钟 300 s 检查一次
def multi_web_server_daemon():
    task_ExecShell("multi_web_server_daemon")


def soft_task():
    # 执行面板soft corn之类的安装执行任务, from task.py -> def startTask():
    def ExecShell(cmdstring, cwd=None, shell=True, symbol='&>'):
        try:
            import shlex
            import subprocess
            import time
            sub = subprocess.Popen(
                cmdstring + symbol + exlogPath,
                cwd=cwd,
                stdin=subprocess.PIPE,
                shell=shell,
                bufsize=4096
            )
            while sub.poll() is None:
                time.sleep(0.1)
            return sub.returncode
        except:
            return None

    tip_file = "/dev/shm/.panelTask.pl"
    try:
        if os.path.exists(isTask):
            with db.Sql() as sql:
                sql.table('tasks').where(
                    "status=?", ('-1',)).setField('status', '0')
                taskArr = sql.table('tasks').where("status=?", ('0',)).field('id,type,execstr').order("id asc").select()
                for value in taskArr:
                    start = int(time.time())
                    if not sql.table('tasks').where("id=?", (value['id'],)).count():
                        write_file(tip_file, str(int(time.time())))
                        continue
                    sql.table('tasks').where("id=?", (value['id'],)).save('status,start', ('-1', start))
                    if value['type'] != 'execshell':
                        continue
                    ExecShell(value['execstr'])
                    end = int(time.time())
                    sql.table('tasks').where("id=?", (value['id'],)).save('status,end', ('1', end))
                    if sql.table('tasks').where("status=?", ('0',)).count() < 1:
                        if os.path.exists(isTask):
                            os.remove(isTask)
        write_file(tip_file, str(int(time.time())))
    except Exception as e:
        logger.error(f"start_bt_task error: {e}")


# 预安装网站监控报表
def check_site_monitor():
    task_ExecShell("check_site_monitor")

# 节点监控
def node_monitor():
    task_ExecShell("node_monitor")


# 节点监控
def node_monitor_check():
    task_ExecShell("node_monitor_check")


# 检测防爆破计划任务
def breaking_through():
    task_ExecShell("breaking_through")


# 找site favicons
def find_favicons():
    task_ExecShell(
        "find_favicons",
        paths_exists=[
            '/www/server/panel/config/auto_favicon.conf',
        ]
    )


# 邮件日志
def maillog_event():
    task_ExecShell(
        "maillog_event",
        paths_exists=[
            "/www/server/panel/plugin/mail_sys/mail_sys_main.py",
            "/www/vmail",
        ]
    )


# 邮件处理日志聚合
def aggregate_maillogs_task():
    task_ExecShell(
        "aggregate_maillogs_task",
        paths_exists=[
            "/www/server/panel/plugin/mail_sys/mail_sys_main.py",
            "/www/vmail",
        ]
    )


# 邮件自动化发件任务
def schedule_automations():
    task_ExecShell(
        "schedule_automations",
        paths_exists=[
            "/www/server/panel/plugin/mail_sys/mail_sys_main.py",
            "/www/vmail",
        ]
    )


# 刷新docker app 列表
def refresh_dockerapps():
    task_ExecShell("refresh_dockerapps")


# 版本更新执行一次性
def task_version_part():
    task_ExecShell("task_version_part")


# ================================ 这是任务分割线 ===============================


TASKS = [
    # <核心任务> 面板重启检查, 面板授权检查
    {"func": [restart_panel, panel_auth], "interval": 2, "is_core": True},
    {"func": soft_task, "interval": 2, "is_core": True},  # 原面板任务
    {"func": bt_box_task, "interval": 2, "is_core": True},  # 原面板任务
    # <核心任务> 服务守护
    {"func": daemon_service, "interval": 10, "is_core": True},
    # <核心任务> 原系统监控
    {"func": systemTask, "is_core": True},  # 每1分钟系统监控任务, 常驻, 内置间隔

    # ================================ 分割线 ===============================
    # <普通任务>
    # func 函数, interval 间隔时间秒s, 排队复用线程 (打印请用logger, 日志路径 .../logs/task.log)
    {"func": push_msg, "interval": 60},  # 每1分钟面板推送消息
    {"func": breaking_through, "interval": 60},  # 每分钟防爆破计划任务

    {"func": multi_web_server_daemon, "interval": 300},  # 每5分钟多服务守护任务
    {"func": check502Task, "interval": 60 * 10},  # 每10分钟 502检查(夹杂若干任务)
    {"func": check_site_monitor, "interval": 60 * 10},  # 每10分钟检查站点安装监控
    {"func": node_monitor, "interval": 60 },  # 每1分钟节点监控任务
    {"func": node_monitor_check, "interval": 60*60*24*30 },  # 每月节点监控检测任务
    {"func": update_waf_config, "interval": 60 * 20},  # 每隔20分钟更新一次waf报表数据
    {"func": update_monitor_requests, "interval": 60 * 20},  # 每隔20分钟更新一次网站报表数据

    {"func": check_panel_msg, "interval": 3600},  # 每1小时面板消息提醒
    {"func": find_favicons, "interval": 43200},  # 每12小时找favicons
    {"func": domain_ssl_service, "interval": 3600},  # 每6小时进行域名SSL服务(内置时间标记, 可提前检查)
    {"func": malicious_file_scanning, "interval": 60 * 60 * 6},  # 每每6小时进行恶意文件扫描
    {"func": count_ssh_logs, "interval": 3600 * 24},  # 每天统计SSH登录日志
    {"func": submit_module_call_statistics, "interval": 3600},  # 每天一次 提交今天之前的统计数据(内置时间标记, 可提前检查)

    {"func": maillog_event, "interval": 60, "loop": True},  # 邮局日志事件监控 event loop事件, 每60秒一次, 起守护作用
    {"func": send_mail_time, "interval": 60 * 3},  # 每3分钟检测邮件信息
    {"func": auto_reply_tasks, "interval": 3600},  # 每1小时自动回复邮件
    {"func": schedule_automations, "interval": 60},  # 每1分钟邮局自动化任务
    {"func": aggregate_maillogs_task, "interval": 60},  # 每1分钟聚合邮局日志
    {"func": mailsys_quota_alarm, "interval": 3600 * 2},  # 每2小时邮件域名邮箱使用限额告警
    {"func": auto_scan_abnormal_mail, "interval": 3600 * 2},  # 每2小时自动扫描异常邮箱
    {"func": mailsys_update_usage, "interval": 3600 * 12},  # 每12小时邮局更新域名邮箱使用量
    {"func": submit_email_statistics, "interval": 3600 * 24},  # 每天一次 昨日邮件发送统计
    {"func": mailsys_domain_blecklisted_alarm, "interval": 3600 * 24},  # # 每天一次 邮局黑名单检测

    {"func": update_vulnerabilities, "interval": 3600 * 24},  # # 每天一次 更新漏洞信息
    {"func": refresh_dockerapps, "interval": 3600 * 24},  # # 每天一次 更新docker app 列表
]


def thread_register(brain: SimpleBrain, is_core: bool = True):
    if not is_core:  # delay normal tasks
        logger.info("Normal Task will be join active after 30s")
        time.sleep(30)

    for index, task in enumerate(TASKS):
        try:
            if task.get("is_core", False) == is_core:
                if isinstance(task["func"], list):
                    task_id = "_".join([f.__name__ for f in task["func"]])
                else:
                    task_id = task.get("id", task["func"].__name__)

                # delay normal tasks, 削峰
                if not is_core:
                    time.sleep(10)

                brain.register_task(
                    func=task["func"],
                    task_id=task_id,
                    interval=task.get("interval", 3600),
                    is_core=task.get("is_core", False),
                    loop=task.get("loop", False),
                )
        except Exception:
            import traceback
            logger.error(f"Register task {task} failed: {traceback.format_exc()}")
            continue
    logger.info(
        f"All the {'[Core]' if is_core else '[Normal]'} tasks have been registered."
    )


def main(max_workers: int = None):
    main_pid = "logs/task.pid"
    if os.path.exists(main_pid):
        os.system("kill -9 $(cat {}) &> /dev/null".format(main_pid))
    pid = os.fork()
    if pid:
        sys.exit(0)

    os.setsid()
    _pid = os.fork()

    if _pid:
        write_file(main_pid, str(_pid))
        sys.exit(0)

    sys.stdout.flush()
    sys.stderr.flush()

    logger.info("Service Up")
    time.sleep(5)
    task_version_part()
    # =================== Start ===========================
    sb = SimpleBrain(cpu_max=30.0, workers=max_workers)
    try:
        # core tasks
        thread_register(brain=sb, is_core=True)
        # normal tasks will be delayed
        threading.Thread(
            target=thread_register, args=(sb, False), daemon=True
        ).start()
        sb.run()
    except Exception:
        import traceback
        logger.error(traceback.format_exc())
        sb._shutdown()
    # =================== End ========================


if __name__ == "__main__":
    main()
