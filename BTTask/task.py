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

import json
import os
import re
import shutil
import sys
import threading
import time
from datetime import datetime, timedelta

import psutil

sys.path.insert(0, "/www/server/panel/class/")
import db
import public
from panelTask import bt_task

try:
    from public.hook_import import hook_import

    hook_import()
except Exception:
    pass

from BTTask.brain import SimpleBrain
from BTTask.conf import (
    BASE_PATH,
    CURRENT_TASK_VERSION,
    PYTHON_BIN,
    exlogPath,
    isTask,
    logger,
)

# 非标准库等任务依赖导入请在函数中延迟导入

global pre

task_obj = bt_task()
task_obj.not_web = True
bt_box_task = task_obj.start_task_new


def task_ExecShell(fucn_name: str, **kw):
    """
    仅运行 /www/server/panel/BTTask/task_script.py 下的包装函数
    可通过 kw 参数扩展前置检查，例如:
      - kw['paths_exists']: List [str]
      (例如, 检查邮局插件是否存在
      paths_exists=['/www/server/panel/plugin/mail_sys/mail_sys_main.py', '/www/vmail'])

    """
    if PYTHON_BIN in fucn_name:
        raise ValueError("valid function name required")

    if kw.get("paths_exists") and isinstance(kw["paths_exists"], list):
        for p in kw["paths_exists"]:
            try:
                if not os.path.exists(str(p)):
                    logger.debug(f"Skip task [{fucn_name}]: path exists check failed - '{p}' not found")
                    return
            except Exception as e:
                raise ValueError(f"Invalid path in paths_exists: '{p}', error: {e}")

    cmd = f"{PYTHON_BIN} /www/server/panel/BTTask/task_script.py {fucn_name}"
    _, err = public.ExecShell(cmd)
    if err:
        raise Exception(err)
    del err, cmd


# 系统监控任务
# noinspection PyUnusedLocal
def systemTask():
    def GetMemUsed():
        try:
            mem = psutil.virtual_memory()
            memInfo = {'memTotal': mem.total / 1024 / 1024, 'memFree': mem.free / 1024 / 1024,
                       'memBuffers': mem.buffers / 1024 / 1024, 'memCached': mem.cached / 1024 / 1024}
            tmp = memInfo['memTotal'] - memInfo['memFree'] - \
                  memInfo['memBuffers'] - memInfo['memCached']
            tmp1 = memInfo['memTotal'] / 100
            return tmp / tmp1
        except:
            return 1

    def GetLoadAverage():
        c = os.getloadavg()
        data = {
            'one': float(c[0]),
            'five': float(c[1]),
            'fifteen': float(c[2]),
            'max': psutil.cpu_count() * 2
        }
        data['limit'] = data['max']
        data['safe'] = data['max'] * 0.75
        return data

    cycle = 60
    try:
        filename = '{}/data/control.conf'.format(BASE_PATH)
        with db.Sql() as sql:
            sql = sql.dbfile('system')

            csql = '''CREATE TABLE IF NOT EXISTS `load_average`
                      (
                          `id`
                          INTEGER
                          PRIMARY
                          KEY
                          AUTOINCREMENT,
                          `pro`
                          REAL,
                          `one`
                          REAL,
                          `five`
                          REAL,
                          `fifteen`
                          REAL,
                          `addtime`
                          INTEGER
                      )'''

            network_sql = '''CREATE TABLE IF NOT EXISTS `network`
                             (
                                 `id`
                                 INTEGER
                                 PRIMARY
                                 KEY
                                 AUTOINCREMENT,
                                 `up`
                                 INTEGER,
                                 `down`
                                 INTEGER,
                                 `total_up`
                                 INTEGER,
                                 `total_down`
                                 INTEGER,
                                 `down_packets`
                                 INTEGER,
                                 `up_packets`
                                 INTEGER,
                                 `addtime`
                                 INTEGER
                             )'''

            cpuio_sql = '''CREATE TABLE IF NOT EXISTS `cpuio`
                           (
                               `id`
                               INTEGER
                               PRIMARY
                               KEY
                               AUTOINCREMENT,
                               `pro`
                               INTEGER,
                               `mem`
                               INTEGER,
                               `addtime`
                               INTEGER
                           )'''

            diskio_sql = '''CREATE TABLE IF NOT EXISTS `diskio`
                            (
                                `id`
                                INTEGER
                                PRIMARY
                                KEY
                                AUTOINCREMENT,
                                `read_count`
                                INTEGER,
                                `write_count`
                                INTEGER,
                                `read_bytes`
                                INTEGER,
                                `write_bytes`
                                INTEGER,
                                `read_time`
                                INTEGER,
                                `write_time`
                                INTEGER,
                                `addtime`
                                INTEGER
                            )'''

            sql.execute(csql, ())
            sql.execute(network_sql, ())
            sql.execute(cpuio_sql, ())
            sql.execute(diskio_sql, ())

            sql.close()

        count = 0
        reloadNum = 0
        diskio_1 = diskio_2 = networkInfo = cpuInfo = diskInfo = None
        network_up = {}
        network_down = {}
        import process_task
        proc_task_obj = process_task.process_task()

        while True:
            if not os.path.exists(filename):
                time.sleep(10)
                continue

            day = 30
            try:
                day = int(public.readFile(filename))
                if day < 1:
                    time.sleep(10)
                    continue
            except:
                day = 30

            addtime = int(time.time())
            deltime = addtime - (day * 86400)
            # 取当前CPU Io
            tmp = {'used': proc_task_obj.get_monitor_list(addtime), 'mem': GetMemUsed()}
            cpuInfo = tmp

            # 取当前网络Io
            networkIo_list = psutil.net_io_counters(pernic=True)
            tmp = {'upTotal': 0, 'downTotal': 0, 'up': 0, 'down': 0, 'downPackets': {}, 'upPackets': {}}

            for k in networkIo_list.keys():
                networkIo = networkIo_list[k][:4]
                if not k in network_up.keys():
                    network_up[k] = networkIo[0]
                    network_down[k] = networkIo[1]

                tmp['upTotal'] += networkIo[0]
                tmp['downTotal'] += networkIo[1]
                tmp['downPackets'][k] = round(
                    float((networkIo[1] - network_down[k]) / 1024) / cycle, 2)
                tmp['upPackets'][k] = round(
                    float((networkIo[0] - network_up[k]) / 1024) / cycle, 2)
                tmp['up'] += tmp['upPackets'][k]
                tmp['down'] += tmp['downPackets'][k]

                network_up[k] = networkIo[0]
                network_down[k] = networkIo[1]

            networkInfo = tmp

            # 取磁盘Io
            disk_ios = True
            try:
                if os.path.exists('/proc/diskstats'):
                    diskio_2 = psutil.disk_io_counters()

                    if not diskio_1:
                        diskio_1 = diskio_2
                    tmp = {'read_count': int((diskio_2.read_count - diskio_1.read_count) / cycle),
                           'write_count': int((diskio_2.write_count - diskio_1.write_count) / cycle),
                           'read_bytes': int((diskio_2.read_bytes - diskio_1.read_bytes) / cycle),
                           'write_bytes': int((diskio_2.write_bytes - diskio_1.write_bytes) / cycle),
                           'read_time': int((diskio_2.read_time - diskio_1.read_time) / cycle),
                           'write_time': int((diskio_2.write_time - diskio_1.write_time) / cycle)}

                    if not diskInfo:
                        diskInfo = tmp

                    diskInfo['read_count'] = tmp['read_count']
                    diskInfo['write_count'] = tmp['write_count']
                    diskInfo['read_bytes'] = tmp['read_bytes']
                    diskInfo['write_bytes'] = tmp['write_bytes']
                    diskInfo['read_time'] = tmp['read_time']
                    diskInfo['write_time'] = tmp['write_time']

                    diskio_1 = diskio_2
            except:
                logger.info(public.get_error_info())
                disk_ios = False

            try:
                with db.Sql().dbfile("system") as sql:
                    data = (cpuInfo['used'], cpuInfo['mem'], addtime)
                    sql.table('cpuio').add('pro,mem,addtime', data)
                    sql.table('cpuio').where("addtime<?", (deltime,)).delete()
                    data = (networkInfo['up'], networkInfo['down'], networkInfo['upTotal'], networkInfo['downTotal'],
                            json.dumps(networkInfo['downPackets']), json.dumps(networkInfo['upPackets']), addtime)
                    sql.table('network').add('up,down,total_up,total_down,down_packets,up_packets,addtime', data)
                    sql.table('network').where("addtime<?", (deltime,)).delete()
                    if os.path.exists('/proc/diskstats') and disk_ios:
                        data = (diskInfo['read_count'], diskInfo['write_count'], diskInfo['read_bytes'],
                                diskInfo['write_bytes'], diskInfo['read_time'], diskInfo['write_time'], addtime)
                        sql.table('diskio').add(
                            'read_count,write_count,read_bytes,write_bytes,read_time,write_time,addtime', data)
                        sql.table('diskio').where("addtime<?", (deltime,)).delete()

                    # LoadAverage
                    load_average = GetLoadAverage()
                    lpro = round(
                        (load_average['one'] / load_average['max']) * 100, 2)
                    if lpro > 100:
                        lpro = 100
                    sql.table('load_average').add('pro,one,five,fifteen,addtime',
                                                  (lpro, load_average['one'], load_average['five'],
                                                   load_average['fifteen'],
                                                   addtime))
                    sql.table('load_average').where("addtime<?", (deltime,)).delete()

                lpro = None
                load_average = None
                cpuInfo = None
                networkInfo = None
                diskInfo = None
                data = None
                count = 0
                reloadNum += 1
                if reloadNum > 1440:
                    reloadNum = 0
            except Exception:
                import traceback
                logger.error(traceback.format_exc())
            del tmp
            time.sleep(cycle)
            count += 1
    except Exception:
        import traceback
        logger.error(traceback.format_exc())
    finally:
        import gc
        gc.collect()


# 每10分钟, 原来旧的502错误检查线程 (夹杂其他任务)
def check502Task():
    task_ExecShell("check502task")


# 每1小时检查面板证书是否有更新
def check_panel_ssl():
    try:
        lets_info = public.ReadFile("{}/ssl/lets.info".format(BASE_PATH))
        if not lets_info:
            del lets_info
            return
        os.system(
            PYTHON_BIN + " {}/script/panel_ssl_task.py > /dev/null".format(BASE_PATH)
        )
        del lets_info
    except Exception as e:
        raise e


# 更新PID文件
def update_pid_file(pid):
    pid_file = "{}/logs/panel.pid".format(public.get_panel_path())
    try:
        with open(pid_file, 'w') as f:
            f.write(str(pid))
        logger.info(f'Updated panel PID file with PID {pid}')
    except Exception as e:
        logger.error(f'Error writing to PID file: {e}')


# 面板守护
# todo
def daemon_panel():
    def find_panel_pid():
        for pid in psutil.pids():
            try:
                p = psutil.Process(pid)
                if 'BT-Panel' in p.name():  # 假设进程名包含 'BT-Panel'
                    return pid
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                continue
        return None

    panel_pid_file = "{}/logs/panel.pid".format(public.get_panel_path())
    # 检查PID文件是否存在
    if not os.path.exists(panel_pid_file):
        logger.info(f'{panel_pid_file} not found, starting panel service...')
        return

    panel_pid = ""
    try:
        # 读取PID文件
        with open(panel_pid_file, 'r') as file:
            panel_pid = file.read()
    except Exception:
        service_panel('start')
        return

    if not panel_pid:
        logger.info(f'PID is empty in {panel_pid_file}, starting panel service...')
        service_panel('start')
        return

    panel_pid = panel_pid.strip()
    # 检查PID对应的进程是否存在
    if not psutil.pid_exists(int(panel_pid)):
        logger.info(
            f'PID {panel_pid} not found, attempting to find running panel process...'
        )
        panel_pid = find_panel_pid()

        if panel_pid:
            # 更新PID文件
            update_pid_file(panel_pid)
        else:
            logger.info('No panel process found, starting service...')
            service_panel('start')

    else:
        # 检查进程是否是面板进程
        comm_file = f"/proc/{panel_pid}/comm"
        if os.path.exists(comm_file):
            with open(comm_file, 'r') as file:
                comm = file.read()
            if not comm or comm.find("BT-Panel") == -1:
                logger.info(
                    f'Process {panel_pid} is not a BT-Panel process,'
                    f'comm-{comm} commtype-{type(comm)}'
                )
                service_panel('start')
                return

        else:
            logger.info(f'comm file not found for PID {panel_pid}, restarting service...')
            service_panel('start')


def daemon_service():
    task_ExecShell("daemon_service")


def service_panel(action='reload'):
    if not os.path.exists('{}/init.sh'.format(BASE_PATH)):
        os.system("curl -k https://node.aapanel.com/install/update_7.x_en.sh|bash &")
    else:
        os.system("nohup bash /www/server/panel/init.sh {} > /dev/null 2>&1 &".format(action))
    logger.info("Panel Service: {}".format(action))


# 重启面板服务
def restart_panel():
    rtips = '{}/data/restart.pl'.format(BASE_PATH)
    reload_tips = '{}/data/reload.pl'.format(BASE_PATH)

    if os.path.exists(rtips):
        os.remove(rtips)
        service_panel('restart')
    if os.path.exists(reload_tips):
        os.remove(reload_tips)
        service_panel('reload')


# 取面板pid
def get_panel_pid():
    try:
        pid = public.ReadFile('/www/server/panel/logs/panel.pid')
        if pid:
            return int(pid)
        for pid in psutil.pids():
            try:
                p = psutil.Process(pid)
                n = p.cmdline()[-1]
                if n.find('runserver') != -1 or n.find('BT-Panel') != -1:
                    return pid
            except:
                pass
    except:
        pass
    return None


# 定时任务去检测邮件信息
def send_mail_time():
    if not os.path.exists('/www/server/panel/plugin/mail_sys/mail_sys_main.py') or not os.path.exists('/www/vmail'):
        return
    os.system("nohup " + PYTHON_BIN + " /www/server/panel/script/mail_task.py > /dev/null 2>&1 &")


# 面板消息提醒
def check_panel_msg():
    os.system(
        'nohup {} /www/server/panel/script/check_msg.py > /dev/null 2>&1 &'.format(PYTHON_BIN)
    )


# 面板推送消息
def push_msg():
    os.system('nohup {} /www/server/panel/script/push_msg.py > /dev/null 2>&1 &'.format(PYTHON_BIN))


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
    """
        @name 统计SSH登录日志
        @return None
    """

    import json

    def parse_journal_disk_usage(output):
        # 使用正则表达式来提取数字和单位
        match = re.search(r'take up (\d+(\.\d+)?)\s*([KMGTP]?)', output)
        total_bytes = 0
        if match:
            value = float(match.group(1))  # 数字
            unit = match.group(3)  # 单位
            # 将所有单位转换为字节
            if unit == '':
                unit_value = 1
            elif unit == 'K':
                unit_value = 1024
            elif unit == 'M':
                unit_value = 1024 * 1024
            elif unit == 'G':
                unit_value = 1024 * 1024 * 1024
            elif unit == 'T':
                unit_value = 1024 * 1024 * 1024 * 1024
            elif unit == 'P':
                unit_value = 1024 * 1024 * 1024 * 1024 * 1024
            else:
                unit_value = 0

            # 计算总字节数
            total_bytes = value * unit_value
        return total_bytes

    if os.path.exists("/etc/debian_version"):
        version = public.readFile('/etc/debian_version')
        if not version:
            return
        version = version.strip()
        if 'bookworm' in version or 'jammy' in version or 'impish' in version:
            version = 12
        else:
            try:
                version = float(version)
            except:
                version = 11

        if version >= 12:
            while True:
                filepath = "/www/server/panel/data/ssh_login_counts.json"

                # 获取今天的日期
                today = datetime.now().strftime('%Y-%m-%d')
                result = {
                    'date': today,  # 添加日期字段
                    'error': 0,
                    'success': 0,
                    'today_error': 0,
                    'today_success': 0
                }
                try:
                    filedata = public.readFile(filepath) if os.path.exists(filepath) else public.writeFile(filepath,
                                                                                                           "[]")
                    try:
                        data_list = json.loads(filedata)
                    except:
                        data_list = []

                    # 检查是否已有今天的记录，避免重复统计
                    found_today = False
                    for day in data_list:
                        if day['date'] == today:
                            found_today = True
                            break

                    if found_today:
                        break  # 如果找到今天的记录，跳出while循环

                    today_err_num1 = int(public.ExecShell(
                        "journalctl -u ssh --no-pager -S today |grep -a 'Failed password for' |grep -v 'invalid' |wc -l")[
                                             0])

                    today_err_num2 = int(public.ExecShell(
                        "journalctl -u ssh --no-pager -S today |grep -a 'Connection closed by authenticating user' |grep -a 'preauth' |wc -l")[
                                             0])

                    today_success = int(
                        public.ExecShell("journalctl -u ssh --no-pager -S today |grep -a 'Accepted' |wc -l")[0])

                    # 查看文件大小 判断是否超过5G
                    is_bigfile = False

                    res, err = public.ExecShell("journalctl --disk-usage")
                    total_bytes = parse_journal_disk_usage(res)
                    limit_bytes = 5 * 1024 * 1024 * 1024
                    if total_bytes > limit_bytes:
                        is_bigfile = True

                    if is_bigfile:
                        err_num1 = int(public.ExecShell(
                            "journalctl -u ssh --since '30 days ago' --no-pager | grep -a 'Failed password for' | grep -v 'invalid' | wc -l")[
                                           0])
                        err_num2 = int(public.ExecShell(
                            "journalctl -u ssh --since '30 days ago' --no-pager --grep='Connection closed by authenticating user|preauth' | wc -l")[
                                           0])
                        success = int(public.ExecShell(
                            "journalctl -u ssh --since '30 days ago' --no-pager | grep -a 'Accepted' | wc -l")[0])
                    else:
                        # 统计失败登陆次数
                        err_num1 = int(public.ExecShell(
                            "journalctl -u ssh --no-pager |grep -a 'Failed password for' |grep -v 'invalid' |wc -l")[0])
                        err_num2 = int(public.ExecShell(
                            "journalctl -u ssh --no-pager --grep='Connection closed by authenticating user|preauth' |wc -l")[
                                           0])
                        success = int(public.ExecShell("journalctl -u ssh --no-pager|grep -a 'Accepted' |wc -l")[0])
                    result['error'] = err_num1 + err_num2
                    # 统计成功登录次数
                    result['success'] = success
                    result['today_error'] = today_err_num1 + today_err_num2
                    result['today_success'] = today_success

                    data_list.insert(0, result)
                    data_list = data_list[:7]
                    public.writeFile(filepath, json.dumps(data_list))
                except:
                    logger.error(public.get_error_info())
                    public.writeFile(filepath, json.dumps([{
                        'date': today,  # 添加日期字段
                        'error': 0,
                        'success': 0,
                        'today_error': 0,
                        'today_success': 0
                    }]))


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
        public.get_panel_path(), yesterday
    )
    if os.path.exists(cloud_yesterday_submit):
        return

    if os.path.exists("/www/server/panel/plugin/mail_sys"):
        sys.path.insert(1, "/www/server/panel/plugin/mail_sys")

    # 检查版本 检查是否能查询额度  剩余额度
    import public.PluginLoader as plugin_loader
    bulk = plugin_loader.get_module('{}/plugin/mail_sys/mail_send_bulk.py'.format(public.get_panel_path()))
    SendMailBulk = bulk.SendMailBulk
    try:
        SendMailBulk()._get_user_quota()
    except:
        logger.error(public.get_error_info())
        return

    # 添加标记
    public.writeFile(cloud_yesterday_submit, '1')
    # 删除前天标记
    before_yesterday = datetime.now() - timedelta(days=2)
    before_yesterday = before_yesterday.strftime('%Y-%m-%d')
    cloud_before_yesterday_submit = '{}/data/{}_update_mailsys_domain_restrictions.pl'.format(
        public.get_panel_path(), before_yesterday
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

        time.sleep(3600)  # 进入脚本前等待 和更新配额错开时间
        cmd = f"btpython {script}"
        public.ExecShell(cmd)
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
        public.ExecShell(cmd)
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


# 3小时一次检查DNS解析状态
def dns_checker():
    os.system(
        f"{PYTHON_BIN} /www/server/panel/class_v2/ssl_dnsV2/dns_manager.py"
    )


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
    global pre

    # 下载文件
    def DownloadFile(url, filename):
        try:
            import urllib
            import socket
            socket.setdefaulttimeout(10)
            # noinspection PyUnresolvedReferences
            urllib.urlretrieve(url, filename=filename, reporthook=DownloadHook)
            os.system('chown www.www ' + filename)
            public.writeFile(exlogPath, 'done')
        except:
            public.writeFile(exlogPath, 'done')

    # 下载文件进度回调
    def DownloadHook(count, blockSize, totalSize):
        global pre
        used = count * blockSize
        pre1 = int((100.0 * used / totalSize))
        if pre == pre1:
            return
        speed = {'total': totalSize, 'used': used, 'pre': pre}
        public.writeFile(exlogPath, json.dumps(speed))
        pre = pre1

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
                        public.writeFile(tip_file, str(int(time.time())))
                        continue
                    sql.table('tasks').where("id=?", (value['id'],)).save('status,start', ('-1', start))
                    if value['type'] == 'download':
                        argv = value['execstr'].split('|bt|')
                        DownloadFile(argv[0], argv[1])
                    elif value['type'] == 'execshell':
                        ExecShell(value['execstr'])
                    end = int(time.time())
                    sql.table('tasks').where("id=?", (value['id'],)).save('status,end', ('1', end))
                    if sql.table('tasks').where("status=?", ('0',)).count() < 1:
                        if os.path.exists(isTask):
                            os.remove(isTask)
        public.writeFile(tip_file, str(int(time.time())))
    except Exception as e:
        logger.error(f"start_bt_task error: {e}")


# 预安装网站监控报表
def check_site_monitor():
    task_ExecShell("check_site_monitor")


# 检测防爆破计划任务
def breaking_through():
    task_ExecShell("breaking_through")


# 找site favicons
def find_favicons():
    task_ExecShell("find_favicons")


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
    def _run_post_update_tasks(from_version, to_version):
        """
        在版本更新后执行一次性任务。
        :param from_version: 旧版本号
        :param to_version: 新版本号
        :return: bool, 任务是否成功
        """
        try:
            if from_version == to_version:
                logger.info("Current task version is the same as the last version, no update tasks to run.")
                return True

            logger.info(
                f"Detected update program start, {from_version} -> {to_version}. Executing one-time update tasks..."
            )

            if from_version < '1.0.0':
                dirs_to_clean = [
                    os.path.join(BASE_PATH, 'logs/sqlite_easy'),
                    os.path.join(BASE_PATH, 'logs/sql_log')
                ]

                for dir_path in dirs_to_clean:
                    if os.path.isdir(dir_path):
                        try:
                            shutil.rmtree(dir_path)
                            logger.info(f"Removed directory: {dir_path}")
                        except Exception as e:
                            logger.error(f"Removing directory {dir_path} failed: {str(e)}")
                    else:
                        logger.info(f"Directory not exists, skipped: {dir_path}")

            if from_version < '1.0.1':
                sites = public.M('sites').field('id,name,path').select()
                pattern = r'<a class="btlink" href="https://www\.aapanel\.com/new/download\.html\?invite_code=aapanele" target="_blank">(.+?)</a>'
                for site in sites:
                    temo_dir = [
                        os.path.join(site['path'], '404.html'),
                        os.path.join(site['path'], '502.html'),
                        os.path.join(site['path'], 'index.html'),
                    ]
                    for d in temo_dir:
                        if os.path.exists(d):
                            html = public.readFile(d)
                            result = re.sub(pattern, r'\1', html)
                            public.writeFile(d, result.strip())

            logger.info("All one-time update tasks executed successfully.")
            return True
        except Exception as e:
            logger.error(f"Executing one-time update task failed: {str(e)}")
            return False

    # run_post_update_tasks
    version_file = '{}/data/task_version.pl'.format(public.get_panel_path())
    last_version = "0.0.0"  # 默认为一个很旧的版本

    if os.path.exists(version_file):
        last_version = public.readFile(version_file) or "0.0.0"
    if _run_post_update_tasks(last_version, CURRENT_TASK_VERSION):
        public.writeFile(version_file, CURRENT_TASK_VERSION)


# ================================ 这是任务分割线 ===============================


TASKS = [
    # <核心任务> 面板重启检查, 面板任务2个, 面板授权检查
    {"func": [restart_panel, bt_box_task, soft_task, panel_auth], "interval": 2, "is_core": True},
    # <核心任务> 服务守护
    {"func": daemon_service, "interval": 10, "is_core": True},
    # <核心任务> 系统监控
    {"func": systemTask, "is_core": True},  # 每1分钟系统监控任务, 常驻, 内置间隔

    # ================================ 分割线 ===============================
    # <普通任务>
    # func 函数, interval 间隔时间秒s, 排队复用线程 (打印请用logger, 日志路径 .../logs/task.log)
    {"func": push_msg, "interval": 60},  # 每1分钟面板推送消息
    {"func": breaking_through, "interval": 60},  # 每分钟防爆破计划任务

    {"func": multi_web_server_daemon, "interval": 300},  # 每5分钟多服务守护任务
    {"func": check502Task, "interval": 60 * 10},  # 每10分钟 502检查(夹杂若干任务)
    {"func": check_site_monitor, "interval": 60 * 10},  # 每10分钟检查站点安装监控
    {"func": update_waf_config, "interval": 60 * 20},  # 每隔20分钟更新一次waf报表数据
    {"func": update_monitor_requests, "interval": 60 * 20},  # 每隔20分钟更新一次网站报表数据

    {"func": check_panel_msg, "interval": 3600},  # 每1小时面板消息提醒
    {"func": check_panel_ssl, "interval": 3600},  # 每1小时面板证书是否有更新
    {"func": dns_checker, "interval": 3600 * 3},  # 每3小时dns解析验证
    {"func": find_favicons, "interval": 43200},  # 每12小时找favicons
    {"func": domain_ssl_service, "interval": 3600},  # 每6小时进行域名SSL服务(内置时间标记, 可提前检查)
    {"func": malicious_file_scanning, "interval": 60 * 60 * 6},  # 每每6小时进行恶意文件扫描
    {"func": count_ssh_logs, "interval": 3600 * 24},  # 每天统计SSH登录日志
    {"func": submit_module_call_statistics, "interval": 3600},  # 每天一次 提交今天之前的统计数据(内置时间标记, 可提前检查)

    {"func": maillog_event, "interval": 60},  # 邮局日志事件监控 event loop事件, 每60秒一次, 起守护作用
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
                    d = min(3, int(1 + (index + 1) / 2))
                    time.sleep(d)

                brain.register_task(
                    func=task["func"],
                    task_id=task_id,
                    interval=task.get("interval", 3600),
                    is_core=task.get("is_core", False),
                )
        except Exception:
            import traceback
            logger.error(f"Register task {task} failed: {traceback.format_exc()}")
            continue
    logger.info(
        f"All the {'[Core]' if is_core else '[Normal]'} tasks have been registered."
    )


def main():
    main_pid = "logs/task.pid"
    if os.path.exists(main_pid):
        os.system("kill -9 $(cat {}) &> /dev/null".format(main_pid))
    pid = os.fork()
    if pid:
        sys.exit(0)

    os.setsid()
    _pid = os.fork()

    if _pid:
        public.writeFile(main_pid, str(_pid))
        sys.exit(0)

    sys.stdout.flush()
    sys.stderr.flush()

    logger.info("Service Up")
    time.sleep(5)
    task_version_part()
    # =================== Start ===========================
    sb = SimpleBrain(cpu_max=50.0)
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
        sb.shutdown()
    # =================== End ========================


if __name__ == "__main__":
    main()
