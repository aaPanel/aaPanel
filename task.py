#!/bin/python
#coding: utf-8
# +-------------------------------------------------------------------
# | aaPanel
# +-------------------------------------------------------------------
# | Copyright (c) 2015-2016 aaPanel(www.aapanel.com) All rights reserved.
# +-------------------------------------------------------------------
# | Author: hwliang <hwl@aapanel.com>
# +-------------------------------------------------------------------

# ------------------------------
# 计划任务
# ------------------------------

# import tracemalloc
# import objgraph
import sys
import os
import logging
from datetime import datetime, timedelta,timezone
from json import dumps, loads
from psutil import Process, pids, cpu_count, cpu_percent, net_io_counters, disk_io_counters, virtual_memory, pids, pid_exists, NoSuchProcess, AccessDenied, ZombieProcess
os.environ['BT_TASK'] = '1'
base_path = "/www/server/panel"
sys.path.insert(0, "/www/server/panel/class/")
if os.path.exists("/www/server/panel/plugin/mail_sys"):
    sys.path.insert(1, "/www/server/panel/plugin/mail_sys")
import time
import public
import db
import json
import threading
import panelTask
import process_task
import shutil

from public.hook_import import hook_import
hook_import()

from power_mta.maillog_stat import maillog_event, aggregate_maillogs_task
from power_mta.automations import schedule_automations_forever
from data_v2 import data as data_v2_cls

try:
    from BTPanel import cache
except:
    cache = None

CURRENT_TASK_VERSION = '1.0.1'


task_obj = panelTask.bt_task()
task_obj.not_web = True
global pre, timeoutCount, logPath, isTask, oldEdate, isCheck
pre = 0
timeoutCount = 0
isCheck = 0
oldEdate = None
logPath = '/tmp/panelExec.log'
isTask = '/tmp/panelTask.pl'
python_bin = None
thread_dict = {}



# def log_malloc():
#     snapshot = tracemalloc.take_snapshot()
#     top_stats = snapshot.statistics('lineno')
#
#     s = 'TOP 50 difference (traced_memory: {} tracemalloc_memory: {})\n'.format(tracemalloc.get_traced_memory(), tracemalloc.get_tracemalloc_memory())
#     for stat in top_stats[:50]:
#         s += '{}\n'.format(stat)
#
#     with open('{}/logs/malloc.log'.format(public.get_panel_path()), 'a') as fp:
#         fp.write('[{}]\n'.format(time.strftime('%Y-%m-%d %X')))
#         fp.write('{}\n'.format(s))
#
#
# def objgraph_log():
#     with open('{}/logs/objgraph.log'.format(public.get_panel_path()), 'a') as fp:
#         fp.write('[{}]\n'.format(time.strftime('%Y-%m-%d %X')))
#         fp.write('-------------------- SHOW GROWTH --------------------\n')
#         objgraph.show_growth(limit=50, file=fp)
#         fp.write('\n\n')
#
#         fp.write('-------------------- SHOW MOST COMMON TYPES --------------------\n')
#         objgraph.show_most_common_types(limit=50, file=fp)
#         fp.write('\n\n')
#
#
# def print_malloc_thread():
#     time.sleep(60)
#     log_malloc()
#     objgraph_log()
#     print_malloc_thread()


def get_python_bin():
    global python_bin
    if python_bin: return python_bin
    bin_file = '/www/server/panel/pyenv/bin/python'
    bin_file2 = '/usr/bin/python'
    if os.path.exists(bin_file):
        python_bin = bin_file
        return bin_file
    python_bin = bin_file2
    return bin_file2
def WriteFile(filename,s_body,mode='w+'):
    """
    写入文件内容
    @filename 文件名
    @s_body 欲写入的内容
    return bool 若文件不存在则尝试自动创建
    """
    try:
        fp = open(filename, mode)
        fp.write(s_body)
        fp.close()
        return True
    except:
        try:
            fp = open(filename, mode,encoding="utf-8")
            fp.write(s_body)
            fp.close()
            return True
        except:
            return False

def ReadFile(filename, mode='r'):
    """
    读取文件内容
    @filename 文件名
    return string(bin) 若文件不存在，则返回None
    """
    if not os.path.exists(filename):
        return False
    f_body = None
    with open(filename, mode) as fp:
        f_body = fp.read()
    return f_body

# 下载文件
def DownloadFile(url, filename):
    try:
        import urllib
        import socket
        socket.setdefaulttimeout(10)
        urllib.urlretrieve(url, filename=filename, reporthook=DownloadHook)
        os.system('chown www.www ' + filename)
        WriteLogs('done')
    except:
        WriteLogs('done')


# 下载文件进度回调
def DownloadHook(count, blockSize, totalSize):
    global pre
    used = count * blockSize
    pre1 = int((100.0 * used / totalSize))
    if pre == pre1:
        return
    speed = {'total': totalSize, 'used': used, 'pre': pre}
    WriteLogs(dumps(speed))
    pre = pre1

# 写输出日志
def WriteLogs(logMsg):
    try:
        global logPath
        with open(logPath, 'w+') as fp:
            fp.write(logMsg)
            fp.close()
    except:
        pass


def ExecShell(cmdstring, cwd=None, timeout=None, shell=True, symbol = '&>'):
    try:
        global logPath
        import shlex
        import subprocess
        import time
        sub = subprocess.Popen(cmdstring+ symbol +logPath, cwd=cwd,
                               stdin=subprocess.PIPE, shell=shell, bufsize=4096)

        while sub.poll() is None:
            time.sleep(0.1)

        return sub.returncode
    except:
        return None


# 任务队列
def startTask():
    global isTask,logPath,thread_dict
    tip_file = '/dev/shm/.panelTask.pl'
    n = 0
    tick = 60
    while 1:
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
                        if(sql.table('tasks').where("status=?", ('0')).count() < 1):
                            if os.path.exists(isTask):
                                os.remove(isTask)
                    sql.close()
                    taskArr = None
            public.writeFile(tip_file, str(int(time.time())))

            # 线程检查
            n+=1
            if n > tick:
                run_thread()
                n = 0
        except:
            pass
        time.sleep(2)



# 网站到期处理
def siteEdate():
    global oldEdate
    try:
        if not oldEdate:
            oldEdate = ReadFile('/www/server/panel/data/edate.pl')
        if not oldEdate:
            oldEdate = '0000-00-00'
        mEdate = time.strftime('%Y-%m-%d', time.localtime())
        if oldEdate == mEdate:
            return False
        oldEdate = mEdate
        os.system("nohup " + get_python_bin() + " /www/server/panel/script/site_task.py > /dev/null 2>&1 &")

    except Exception as ex:
        logging.info(ex)
        pass


def GetLoadAverage():
    c = os.getloadavg()
    data = {}
    data['one'] = float(c[0])
    data['five'] = float(c[1])
    data['fifteen'] = float(c[2])
    data['max'] = cpu_count() * 2
    data['limit'] = data['max']
    data['safe'] = data['max'] * 0.75
    return data


# 系统监控任务
def systemTask():
    try:
        filename = '{}/data/control.conf'.format(base_path)
        with db.Sql() as sql:
            sql = sql.dbfile('system')

            csql = '''CREATE TABLE IF NOT EXISTS `load_average` (
  `id` INTEGER PRIMARY KEY AUTOINCREMENT,
  `pro` REAL,
  `one` REAL,
  `five` REAL,
  `fifteen` REAL,
  `addtime` INTEGER
)'''

            network_sql = '''CREATE TABLE IF NOT EXISTS `network` (
  `id` INTEGER PRIMARY KEY AUTOINCREMENT,
  `up` INTEGER,
  `down` INTEGER,
  `total_up` INTEGER,
  `total_down` INTEGER,
  `down_packets` INTEGER,
  `up_packets` INTEGER,
  `addtime` INTEGER
)'''

            cpuio_sql = '''CREATE TABLE IF NOT EXISTS `cpuio` (
  `id` INTEGER PRIMARY KEY AUTOINCREMENT,
  `pro` INTEGER,
  `mem` INTEGER,
  `addtime` INTEGER
)'''

            diskio_sql = '''CREATE TABLE IF NOT EXISTS `diskio` (
  `id` INTEGER PRIMARY KEY AUTOINCREMENT,
  `read_count` INTEGER,
  `write_count` INTEGER,
  `read_bytes` INTEGER,
  `write_bytes` INTEGER,
  `read_time` INTEGER,
  `write_time` INTEGER,
  `addtime` INTEGER
)'''


            sql.execute(csql, ())
            sql.execute(network_sql, ())
            sql.execute(cpuio_sql, ())
            sql.execute(diskio_sql, ())

            sql.close()

        count = 0
        reloadNum=0
        diskio_1 = diskio_2 = networkInfo = cpuInfo = diskInfo = None
        network_up = {}
        network_down = {}
        cycle = 60
        # try:
        #     from panelDaily import panelDaily
        #     panelDaily().check_databases()
        # except Exception as e:
        #     logging.info(e)

        proc_task_obj = process_task.process_task()

        while True:
            if not os.path.exists(filename):
                time.sleep(10)
                continue

            day = 30
            try:
                day = int(ReadFile(filename))
                if day < 1:
                    time.sleep(10)
                    continue
            except:
                day = 30


            addtime = int(time.time())
            deltime = addtime - (day * 86400)
            # 取当前CPU Io
            tmp = {}
            tmp['used'] = proc_task_obj.get_monitor_list(addtime)
            tmp['mem'] = GetMemUsed()
            cpuInfo = tmp

            # 取当前网络Io
            networkIo_list = net_io_counters(pernic=True)
            tmp = {}
            tmp['upTotal'] = 0
            tmp['downTotal'] = 0
            tmp['up'] = 0
            tmp['down'] = 0
            tmp['downPackets'] = {}
            tmp['upPackets'] = {}

            for k in networkIo_list.keys():
                networkIo = networkIo_list[k][:4]
                if not k in network_up.keys():
                    network_up[k] = networkIo[0]
                    network_down[k] = networkIo[1]

                tmp['upTotal'] += networkIo[0]
                tmp['downTotal'] += networkIo[1]
                tmp['downPackets'][k] = round(
                    float((networkIo[1] - network_down[k]) / 1024)/cycle, 2)
                tmp['upPackets'][k] = round(
                    float((networkIo[0] - network_up[k]) / 1024)/cycle, 2)
                tmp['up'] += tmp['upPackets'][k]
                tmp['down'] += tmp['downPackets'][k]

                network_up[k] = networkIo[0]
                network_down[k] = networkIo[1]

            # if not networkInfo:
            #     networkInfo = tmp
            # if (tmp['up'] + tmp['down']) > (networkInfo['up'] + networkInfo['down']):
            networkInfo = tmp

            # 取磁盘Io
            disk_ios = True
            try:
                if os.path.exists('/proc/diskstats'):
                    diskio_2 = disk_io_counters()

                    if not diskio_1:
                        diskio_1 = diskio_2
                    tmp = {}
                    tmp['read_count'] = int((diskio_2.read_count - diskio_1.read_count) / cycle)
                    tmp['write_count'] = int((diskio_2.write_count - diskio_1.write_count) / cycle)
                    tmp['read_bytes'] = int((diskio_2.read_bytes - diskio_1.read_bytes) / cycle)
                    tmp['write_bytes'] = int((diskio_2.write_bytes -  diskio_1.write_bytes) / cycle)
                    tmp['read_time'] = int((diskio_2.read_time - diskio_1.read_time) / cycle)
                    tmp['write_time'] = int((diskio_2.write_time - diskio_1.write_time) / cycle)

                    if not diskInfo:
                        diskInfo = tmp

                    # if (tmp['read_bytes'] + tmp['write_bytes']) > (diskInfo['read_bytes'] + diskInfo['write_bytes']):
                    diskInfo['read_count'] = tmp['read_count']
                    diskInfo['write_count'] = tmp['write_count']
                    diskInfo['read_bytes'] = tmp['read_bytes']
                    diskInfo['write_bytes'] = tmp['write_bytes']
                    diskInfo['read_time'] = tmp['read_time']
                    diskInfo['write_time'] = tmp['write_time']

                    # logging.info(['read: ',tmp['read_bytes'] / 1024 / 1024,'write: ',tmp['write_bytes'] / 1024 / 1024])
                    diskio_1 = diskio_2
            except:
                logging.info(public.get_error_info())
                disk_ios = False

            try:
                sql = db.Sql().dbfile('system')
                data = (cpuInfo['used'], cpuInfo['mem'], addtime)
                #
                sql.table('cpuio').add('pro,mem,addtime', data)
                sql.table('cpuio').where("addtime<?", (deltime,)).delete()
                data = (networkInfo['up'], networkInfo['down'], networkInfo['upTotal'], networkInfo['downTotal'], dumps(networkInfo['downPackets']), dumps(networkInfo['upPackets']), addtime)
                sql.table('network').add('up,down,total_up,total_down,down_packets,up_packets,addtime', data)
                sql.table('network').where("addtime<?", (deltime,)).delete()
                # logging.info(diskInfo)
                if os.path.exists('/proc/diskstats') and disk_ios:
                    data = (diskInfo['read_count'], diskInfo['write_count'], diskInfo['read_bytes'],diskInfo['write_bytes'], diskInfo['read_time'], diskInfo['write_time'], addtime)
                    sql.table('diskio').add('read_count,write_count,read_bytes,write_bytes,read_time,write_time,addtime', data)
                    sql.table('diskio').where("addtime<?", (deltime,)).delete()

                # LoadAverage
                load_average = GetLoadAverage()
                lpro = round(
                    (load_average['one'] / load_average['max']) * 100, 2)
                if lpro > 100:
                    lpro = 100
                sql.table('load_average').add('pro,one,five,fifteen,addtime', (lpro, load_average['one'], load_average['five'], load_average['fifteen'], addtime))
                sql.table('load_average').where("addtime<?", (deltime,)).delete()
                sql.close()

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



                # 日报数据收集
                # if os.path.exists("/www/server/panel/data/start_daily.pl"):
                #     try:
                #         from panelDaily import panelDaily
                #         pd = panelDaily()
                #         t_now = time.localtime()
                #         yesterday  = time.localtime(time.mktime((
                #             t_now.tm_year, t_now.tm_mon, t_now.tm_mday-1,
                #             0,0,0,0,0,0
                #         )))
                #         yes_time_key = pd.get_time_key(yesterday)
                #         con = ReadFile("/www/server/panel/data/store_app_usage.pl")
                #         # logging.info(str(con))
                #         store = False
                #         if con:
                #             if con != str(yes_time_key):
                #                 store = True
                #         else:
                #             store = True
                #
                #         if store:
                #             date_str = str(yes_time_key)
                #             daily_data = pd.get_daily_data_local(date_str)
                #             if "status" in daily_data.keys():
                #                 if daily_data["status"]:
                #                     score = daily_data["score"]
                #                     if public.M("system").dbfile("system").table("daily").where("time_key=?", (yes_time_key,)).count() == 0:
                #                         public.M("system").dbfile("system").table("daily").add("time_key,evaluate,addtime", (yes_time_key, score, time.time()))
                #                     pd.store_app_usage(yes_time_key)
                #                     WriteFile("/www/server/panel/data/store_app_usage.pl", str(yes_time_key), "w")
                #                 # logging.info("更新应用存储信息:"+str(yes_time_key))
                #                 pd.check_server()
                #     except Exception as e:
                #         logging.info("存储应用空间信息错误:"+str(e))
            except Exception as ex:
                logging.info(str(ex))
            del(tmp)
            time.sleep(cycle)
            count += 1
    except Exception as ex:
        logging.info(ex)
        time.sleep(cycle)
        systemTask()


# 取内存使用率
def GetMemUsed():
    try:
        mem = virtual_memory()
        memInfo = {'memTotal': mem.total/1024/1024, 'memFree': mem.free/1024/1024,
                   'memBuffers': mem.buffers/1024/1024, 'memCached': mem.cached/1024/1024}
        tmp = memInfo['memTotal'] - memInfo['memFree'] - \
            memInfo['memBuffers'] - memInfo['memCached']
        tmp1 = memInfo['memTotal'] / 100
        return (tmp / tmp1)
    except:
        return 1


# 更新 GeoLite2-Country.json
def flush_geoip():
    """
        @name 检测如果大小小于3M或大于1个月则更新
        @author wzz <2024/5/21 下午5:33>
        @param "data":{"参数名":""} <数据类型> 参数描述
        @return dict{"status":True/False,"msg":"提示信息"}
    """
    _ips_path = "/www/server/panel/data/firewall/GeoLite2-Country.json"
    m_time_file = "/www/server/panel/data/firewall/geoip_mtime.pl"
    if not os.path.exists(_ips_path):
        os.system("mkdir -p /www/server/panel/data/firewall")
        os.system("touch {}".format(_ips_path))

    try:
        if not os.path.exists(_ips_path):
            public.downloadFile('{}/install/lib/{}'.format(public.get_url(), os.path.basename(_ips_path)), _ips_path)
            public.writeFile(m_time_file, str(int(time.time())))
            return

        _ips_size = os.path.getsize(_ips_path)
        if os.path.exists(m_time_file):
            _ips_mtime = int(public.readFile(m_time_file))
        else:
            _ips_mtime = 0

        if _ips_size < 3145728 or time.time() - _ips_mtime > 2592000:
            core = cpu_count()
            delay = round(1 / (core if core > 0 else 1), 2)
            os.system("rm -f {}".format(_ips_path))
            os.system("rm -f {}".format(m_time_file))
            public.downloadFile('{}/install/lib/{}'.format(public.get_url(), os.path.basename(_ips_path)), _ips_path)
            public.writeFile(m_time_file, str(int(time.time())))
            if os.path.exists(_ips_path):
                try:
                    import json
                    from xml.etree.ElementTree import ElementTree, Element
                    from safeModelV2.firewallModel import main as firewall

                    firewallobj = firewall()
                    ips_list = json.loads(public.readFile(_ips_path))
                    if ips_list:
                        bash = os.path.exists('/usr/bin/apt-get') and not os.path.exists("/etc/redhat-release")
                        if bash:
                            btsh_path = "/etc/ufw/btsh"
                            if not os.path.exists(btsh_path):
                                os.makedirs(btsh_path)

                            write_map = {}
                            for ip_dict in ips_list:
                                tmp_path = '{}/{}.sh'.format(btsh_path, ip_dict['brief'])
                                commands = [
                                    f'ipset add {ip_dict["brief"]} {ip}'
                                    for ip in ip_dict.get("ips", [])
                                    if firewallobj.verify_ip(ip)
                                ]
                                if commands:
                                    script_content = "#!/bin/bash\n" + "\n".join(commands) + "\n"
                                    write_map[tmp_path] = script_content
                                time.sleep(delay)

                            for path, content in write_map.items():
                                public.writeFile(path, content)
                                time.sleep(0.05)
                        else:
                            for ip_dict in ips_list:
                                xml_path = "/etc/firewalld/ipsets/{}.xml.old".format(ip_dict['brief'])
                                xml_body = """<?xml version="1.0" encoding="utf-8"?>
<ipset type="hash:net">
<option name="maxelem" value="1000000"/>
</ipset>
"""
                                if os.path.exists(xml_path):
                                    public.writeFile(xml_path, xml_body)
                                else:
                                    os.makedirs(os.path.dirname(xml_path), exist_ok=True)
                                    public.writeFile(xml_path, xml_body)

                                tree = ElementTree()
                                tree.parse(xml_path)
                                root = tree.getroot()
                                for ip in ip_dict['ips']:
                                    if firewallobj.verify_ip(ip):
                                        entry = Element("entry")
                                        entry.text = ip
                                        root.append(entry)

                                firewallobj.format(root)
                                tree.write(xml_path, 'utf-8', xml_declaration=True)
                                time.sleep(delay)
                except:
                    pass
    except:
        try:
            public.downloadFile(
                '{}/install/lib/{}'.format(public.get_url(), os.path.basename(_ips_path)), _ips_path
            )
            public.writeFile(m_time_file, str(int(time.time())))
        except:
            pass

# 检查502错误
def check502():
    try:
        phpversions = public.get_php_versions()
        for version in phpversions:
            if version in ['52','5.2']: continue
            php_path = '/www/server/php/' + version + '/sbin/php-fpm'
            if not os.path.exists(php_path):
                continue
            if checkPHPVersion(version):
                continue
            if startPHPVersion(version):
                public.WriteLog('PHP daemon',
                                'PHP-' + version + 'processing exception was detected and has been automatically fixed!',
                                not_web=True)
    except Exception as ex:
        logging.info(ex)

# 处理指定PHP版本
def startPHPVersion(version):
    try:
        fpm = '/etc/init.d/php-fpm-' + version
        php_path = '/www/server/php/' + version + '/sbin/php-fpm'
        if not os.path.exists(php_path):
            if os.path.exists(fpm): os.remove(fpm)
            return False

        # 尝试重载服务
        os.system(fpm + ' start')
        os.system(fpm + ' reload')
        if checkPHPVersion(version): return True

        # 尝试重启服务
        cgi = '/tmp/php-cgi-' + version + '.sock'
        pid = '/www/server/php/' + version + '/var/run/php-fpm.pid'
        os.system('pkill -9 php-fpm-' + version)
        time.sleep(0.5)
        if os.path.exists(cgi):
            os.remove(cgi)
        if os.path.exists(pid):
            os.remove(pid)
        os.system(fpm + ' start')
        if checkPHPVersion(version):
            return True
        # 检查是否正确启动
        if os.path.exists(cgi):
            return True
        return False
    except Exception as ex:
        logging.info(ex)
        return True


# 检查指定PHP版本
def checkPHPVersion(version):
    try:
        cgi_file = '/tmp/php-cgi-{}.sock'.format(version)
        if os.path.exists(cgi_file):
            init_file = '/etc/init.d/php-fpm-{}'.format(version)
            if os.path.exists(init_file):
                init_body = public.ReadFile(init_file)
                if not init_body: return True
            uri = "/phpfpm_"+version+"_status?json"
            result = public.request_php(version, uri, '')
            loads(result)
        return True
    except:
        logging.info("PHP-{} unreachable detected".format(version))
        return False


# 502错误检查线程
def check502Task():
    try:
        while True:
            public.auto_backup_panel()
            check502()
            sess_expire()
            mysql_quota_check()
            siteEdate()
            flush_geoip()
            time.sleep(600)
    except Exception as ex:
        logging.info(ex)
        time.sleep(600)
        check502Task()

# MySQL配额检查
def mysql_quota_check():
    os.system("nohup " + get_python_bin() +" /www/server/panel/script/mysql_quota.py > /dev/null 2>&1 &")

# session过期处理
def sess_expire():
    try:
        sess_path = '{}/data/session'.format(base_path)
        if not os.path.exists(sess_path): return
        s_time = time.time()
        f_list = os.listdir(sess_path)
        f_num = len(f_list)
        for fname in f_list:
            filename = '/'.join((sess_path, fname))
            fstat = os.stat(filename)
            f_time = s_time - fstat.st_mtime
            if f_time > 3600:
                os.remove(filename)
                continue
            if fstat.st_size < 256 and len(fname) == 32:
                if f_time > 60 or f_num > 30:
                    os.remove(filename)
                    continue
        del (f_list)

    except Exception as ex:
        logging.info(str(ex))


# 检查面板证书是否有更新
def check_panel_ssl():
    try:
        while True:
            lets_info = ReadFile("{}/ssl/lets.info".format(base_path))
            if not lets_info:
                time.sleep(3600)
                continue
            os.system(get_python_bin() + " {}/script/panel_ssl_task.py > /dev/null".format(base_path))
            time.sleep(3600)
    except Exception as e:
        public.writeFile("/tmp/panelSSL.pl", str(e), "a+")

# 面板进程守护
def daemon_panel11():
    cycle = 10
    panel_pid_file = "{}/logs/panel.pid".format(public.get_panel_path())
    while 1:
        time.sleep(cycle)

        # 检查pid文件是否存在
        if not os.path.exists(panel_pid_file):
            continue

        # 读取pid文件
        panel_pid = public.readFile(panel_pid_file)
        if not panel_pid:
            logging.info("not pid -- {}".format(panel_pid_file))
            service_panel('start')
            continue

        # 检查进程是否存在
        comm_file = "/proc/{}/comm".format(panel_pid)
        if not os.path.exists(comm_file):
            logging.info("not comm_file-- {}".format(comm_file))
            service_panel('start')
            continue

        # 是否为面板进程
        comm = public.readFile(comm_file)
        if comm.find('BT-Panel') == -1:
            logging.info("not BT-Panel-- {}".format(comm))
            service_panel('start')
            continue

        # # 是否为面板进程
        # with open(comm_file, 'r') as f:
        #     comm = f.read()
        #     if comm.find('BT-Panel') == -1:
        #         logging.info("3 not BT-Panel-- {}".format(comm))
        #         service_panel('start')
        #         continue


# 查找面板进程并返回PID
def find_panel_pid():
    for pid in pids():
        try:
            p = Process(pid)
            if 'BT-Panel' in p.name():  # 假设进程名包含 'BT-Panel'
                return pid
        except (NoSuchProcess, AccessDenied, ZombieProcess):
            continue
    return None

# 更新PID文件
def update_pid_file(pid):
    pid_file = "{}/logs/panel.pid".format(public.get_panel_path())
    try:
        with open(pid_file, 'w') as f:
            f.write(str(pid))
        logging.info(f'Updated panel PID file with PID {pid}')
    except Exception as e:
        logging.error(f'Error writing to PID file: {e}')


def daemon_panel():
    cycle = 10
    panel_pid_file = "{}/logs/panel.pid".format(public.get_panel_path())

    while True:
        time.sleep(cycle)

        # 检查PID文件是否存在
        if not os.path.exists(panel_pid_file):
            logging.info(f'{panel_pid_file} not found, starting panel service...')
            continue

        panel_pid=""
        try:
        # 读取PID文件
            with open(panel_pid_file, 'r') as file:
                panel_pid = file.read()
        except Exception as e:
            service_panel('start')
            continue
        if not panel_pid:
            logging.info(f'PID is empty in {panel_pid_file}, starting panel service...')
            service_panel('start')
            continue
        panel_pid = panel_pid.strip()
        # 检查PID对应的进程是否存在
        if not pid_exists(int(panel_pid)):
            logging.info(f'PID {panel_pid} not found, attempting to find running panel process...')
            panel_pid = find_panel_pid()

            if panel_pid:
                # 更新PID文件
                update_pid_file(panel_pid)
            else:
                logging.info('No panel process found, starting service...')
                service_panel('start')

        else:
            # 检查进程是否是面板进程
            comm_file = f"/proc/{panel_pid}/comm"
            if os.path.exists(comm_file):
                with open(comm_file, 'r') as file:
                    comm = file.read()
                if not comm or comm.find("BT-Panel") == -1:
                    logging.info(f'Process {panel_pid} is not a BT-Panel process,comm-{comm} commtype-{type(comm)}')
                    service_panel('start')
                    continue

            else:
                logging.info(f'comm file not found for PID {panel_pid}, restarting service...')
                service_panel('start')

def daemon_service():
    from script.restart_services import RestartServices, DaemonManager
    try:
        # remove old deamons
        from BTPanel import app
        from crontab_v2 import crontab
        with app.app_context():
            old_deamons = public.M('crontab').where("name Like ?", "[Do not delete]%Daemon").select()
            for i in old_deamons:
                try:
                    cron_name = i.get("name")
                    s_name = cron_name.replace("[Do not delete] ", "").replace(" Daemon", "")
                    DaemonManager.add_daemon(s_name.lower())
                except:
                    pass
                args = public.dict_obj()
                args.id = i.get("id")
                crontab().DelCrontab(args)
    except:
        pass

    while 1:
        RestartServices().main()
        time.sleep(10)


def update_panel():
    os.system("curl -k https://node.aapanel.com/install/update_7.x_en.sh|bash &")


def service_panel(action='reload'):
    if not os.path.exists('{}/init.sh'.format(base_path)):
        update_panel()
    else:
        os.system("nohup bash /www/server/panel/init.sh {} > /dev/null 2>&1 &".format(action))
    logging.info("Panel Service: {}".format(action))


# 重启面板服务
def restart_panel_service():
    rtips = '{}/data/restart.pl'.format(base_path)
    reload_tips = '{}/data/reload.pl'.format(base_path)
    while True:
        if os.path.exists(rtips):
            os.remove(rtips)
            service_panel('restart')
        if os.path.exists(reload_tips):
            os.remove(reload_tips)
            service_panel('reload')
        time.sleep(1)

# 取面板pid
def get_panel_pid():
    try:
        pid = ReadFile('/www/server/panel/logs/panel.pid')
        if pid:
            return int(pid)
        for pid in pids():
            try:
                p = Process(pid)
                n = p.cmdline()[-1]
                if n.find('runserver') != -1 or n.find('BT-Panel') != -1:
                    return pid
            except:
                pass
    except:
        pass
    return None


def HttpGet(url, timeout=6, headers={}):
    if sys.version_info[0] == 2:
        try:
            import urllib2
            req = urllib2.Request(url, headers=headers)
            response = urllib2.urlopen(req, timeout=timeout,)
            return response.read()
        except Exception as ex:
            logging.info(str(ex))
            return str(ex)
    else:
        try:
            import urllib.request
            req = urllib.request.Request(url, headers=headers)
            response = urllib.request.urlopen(req, timeout=timeout)
            result = response.read()
            if type(result) == bytes:
                result = result.decode('utf-8')
            return result
        except Exception as ex:
            logging.info("URL: {}  => {}".format(url, ex))
            return str(ex)


# 定时任务去检测邮件信息
def send_mail_time():
    while True:
        try:
            os.system("nohup " + get_python_bin() +" /www/server/panel/script/mail_task.py > /dev/null 2>&1 &")
            time.sleep(180)
        except:
            time.sleep(360)
            send_mail_time()

#5个小时更新一次更新软件列表
def update_software_list():
    while True:
        try:
            import panelPlugin
            panelPlugin.panelPlugin().get_cloud_list_status(None)
            time.sleep(18000)
        except:
            time.sleep(1800)
            update_software_list()

# 面板消息提醒
def check_panel_msg():
    python_bin = get_python_bin()
    while True:
        os.system('nohup {} /www/server/panel/script/check_msg.py > /dev/null 2>&1 &'.format(python_bin))
        time.sleep(3600)

# 面板推送消息
def push_msg():
    python_bin = get_python_bin()
    while True:
        time.sleep(60)
        os.system('nohup {} /www/server/panel/script/push_msg.py > /dev/null 2>&1 &'.format(python_bin))

def JavaProDaemons():
    '''
        @name Java 项目守护进程
        @author lkq@aapanel.com
        @time 2022-07-19
        @param None
    '''
    if public.M('sites').where('project_type=?',('Java')).count()>=1:
        project_info=public.M('sites').where('project_type=?',('Java')).select()
        for i in project_info:
            try:
                import json
                i['project_config'] = json.loads(i['project_config'])
                #判断项目是否设置了守护进程
                if  i['project_config']['java_type']!='springboot':continue
                if 'auth' in i['project_config'] and i['project_config']['auth']==1 or i['project_config']['auth']=='1':
                    print("Java",i['name'])
                    from projectModel import javaModel
                    java = javaModel.main()
                    if java.get_project_run_state(project_name=i['name']):
                        continue
                    else:
                        #如果项目是在后台停止的，那么就不再启动
                        if  os.path.exists("/var/tmp/springboot/vhost/pids/{}.pid".format(i['name'])):
                            get=public.dict_obj()
                            get.project_name=i['name']
                            java.start_project(get)
                            public.WriteLog('守护进程','Java项目[{}]已经被守护进程启动'.format(i['name']))
            except:
                continue

def ProLog():
    path_list=["/www/server/go_project/vhost/logs","/var/tmp/springboot/vhost/logs/"]
    try:
        for i2 in path_list:
            if os.path.exists(i2):
                for dir in os.listdir(i2):
                    dir = os.path.join(i2, dir)
                    # 判断当前目录是否为文件夹
                    if os.path.isfile(dir):
                        if dir.endswith(".log"):
                            #文件大于500M的时候则清空文件
                            if os.stat(dir).st_size >200000000:
                                public.ExecShell("echo ''>{}".format(dir))
    except:
        pass

def ProDadmons():
    '''
        @name 项目守护进程
        @author
    '''
    n = 30
    while 1:
        n += 1
        if n >= 30:
            n = 1
            ProLog()
        time.sleep(120)
        try:
            JavaProDaemons()
        except:
            pass

def process_task_thread():
    '''
        @name 进程监控
        @auther hwliang
    '''


    # 进程流量监控，如果文件：/www/server/panel/data/is_net_task.pl 或 /www/server/panel/data/control.conf不存在，则不监控进程流量
    net_task_obj = process_task.process_network_total()
    net_task_obj.start()

# 检测面板授权
def check_panel_auth():
    while True:
        pro_file='/www/server/panel/data/panel_pro.pl'
        update_file='/www/server/panel/data/now_update_pro.pl'
        if os.path.exists(pro_file):
            python_bin = get_python_bin()
            from BTPanel import cache
            if cache:
                key='pro_check_sdfjslk'
                res = cache.get(key)
            if os.path.exists(update_file) or res is None:
                os.system('nohup {} /www/server/panel/script/check_auth.py > /dev/null 2>&1 &'.format(python_bin))
                if cache:
                    cache.set(key, 'sddsf', 3600)
        if os.path.exists(update_file):os.remove(update_file)
        time.sleep(2)

def count_ssh_logs():
    '''
        @name 统计SSH登录日志
        @return None
    '''
    # 重启后延迟执行 避开cpu高峰期
    time.sleep(1800)
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
                # public.print_log("进入计算count_ssh_logs--{}")
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
                            # public.print_log("进入计算count_ssh_logs--{退出1}")
                            break

                    if found_today:
                        # public.print_log("进入计算count_ssh_logs--{退出2}")
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
                    # import re
                    import json
                    total_bytes = parse_journal_disk_usage(res)
                    # public.print_log("文件大小--{}".format(total_bytes))
                    limit_bytes = 5 * 1024 * 1024 * 1024
                    if total_bytes > limit_bytes:
                        is_bigfile = True

                    if is_bigfile:
                        # public.print_log("取30天--{}".format(total_bytes))
                        err_num1 = int(public.ExecShell("journalctl -u ssh --since '30 days ago' --no-pager | grep -a 'Failed password for' | grep -v 'invalid' | wc -l")[0])
                        err_num2 = int(public.ExecShell("journalctl -u ssh --since '30 days ago' --no-pager --grep='Connection closed by authenticating user|preauth' | wc -l")[0])
                        success = int(public.ExecShell("journalctl -u ssh --since '30 days ago' --no-pager | grep -a 'Accepted' | wc -l")[0])
                    else:
                         # public.print_log("取所有--{}")
                        # 统计失败登陆次数
                        err_num1 = int(public.ExecShell("journalctl -u ssh --no-pager |grep -a 'Failed password for' |grep -v 'invalid' |wc -l")[0])
                        err_num2 = int(public.ExecShell("journalctl -u ssh --no-pager --grep='Connection closed by authenticating user|preauth' |wc -l")[0])
                        success = int(public.ExecShell("journalctl -u ssh --no-pager|grep -a 'Accepted' |wc -l")[0])
                    # public.print_log("计算完毕22--{}")
                    result['error'] = err_num1 + err_num2
                    # 统计成功登录次数
                    result['success'] = success
                    result['today_error'] = today_err_num1 + today_err_num2
                    result['today_success'] = today_success

                    data_list.insert(0, result)
                    data_list = data_list[:7]
                    public.writeFile(filepath, json.dumps(data_list))
                except:
                    public.print_log(public.get_error_info())
                    public.writeFile(filepath, json.dumps([{
                        'date': today,  # 添加日期字段
                        'error': 0,
                        'success': 0,
                        'today_error': 0,
                        'today_success': 0
                    }]))
                time.sleep(86400)
        else:
            time.sleep(86400)


def parse_journal_disk_usage(output):
    import re
    # 使用正则表达式来提取数字和单位
    match = re.search(r'take up (\d+(\.\d+)?)\s*([KMGTP]?)', output)
    total_bytes = 0
    if match:
        value = float(match.group(1))  # 数字
        unit = match.group(3)  # 单位
        # public.print_log("匹配字符--value>{}   unit>{}".format(value, unit))
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

def update_vulnerabilities():
    if "/www/server/panel/class_v2/wp_toolkit/" not in sys.path:
        sys.path.insert(1, "/www/server/panel/class_v2/wp_toolkit/")
    import totle_db
    import requests, json
    requests.packages.urllib3.disable_warnings()

    def auto_scan():
        '''
            @name 自动扫描
            @msg 一天一次
        :return:
        '''
        path_time = "/www/server/panel/data/auto_scan.pl"
        if not os.path.exists(path_time):
            public.writeFile(path_time, json.dumps({"time": int(time.time())}))
            share_ip_info = {"time": 0}
        else:
            share_ip_info = json.loads(public.readFile(path_time))
        if (int(time.time()) - share_ip_info["time"]) < 86400:
            return public.returnMsg(False, "未达到时间")
        share_ip_info["time"] = int(time.time())
        public.writeFile(path_time, json.dumps(share_ip_info))
        import wordpress_scan
        wordpress_scan.wordpress_scan().auto_scan()

    def M(table, db="wordpress_vulnerabilities"):
        '''
            @name 获取数据库对象
            @param table 表名
            @param db 数据库名
        '''
        with totle_db.Sql(db) as sql:
            return sql.table(table)

    def check_vlun():
        path_time = "/www/server/panel/data/wordpress_check_vlun.pl"
        if not os.path.exists(path_time):
            public.writeFile(path_time, json.dumps({"time": int(time.time())}))
            share_ip_info = {"time": 0}
        else:
            share_ip_info = json.loads(public.readFile(path_time))
        if (int(time.time()) - share_ip_info["time"]) < 86400:
            return public.returnMsg(False, "未达到时间")
        share_ip_info["time"] = int(time.time())
        public.writeFile(path_time, json.dumps(share_ip_info))
        load_time = M("wordpress_vulnerabilities", "wordpress_vulnerabilities").order("data_time desc").limit(
            "1").field(
            "data_time").find()
        if type(load_time) != dict: return

        def get_yun_infos(page):
            url = "https://wafapi2.aapanel.com/api/bt_waf/get_wordpress_scan?size=100&p=" + str(page)
            yun_infos = requests.get(url, verify=False, timeout=60).json()
            for i in yun_infos['res']:
                if i['data_time'] > load_time['data_time']:
                    del i['id']
                    M("wordpress_vulnerabilities", "wordpress_vulnerabilities").insert(i)
                else:
                    return True

        for i in range(1, 20):
            time.sleep(26)
            if get_yun_infos(i):
                return

    def check_plugin_close():
        '''
        @name 检查插件是否关闭
        @return True 关闭
        @return False 开启
    '''
        path_time = "/www/server/panel/data/wordpress_check_plugin_close.pl"
        if not os.path.exists(path_time):
            public.writeFile(path_time, json.dumps({"time": int(time.time())}))
            share_ip_info = {"time": 0}
        else:
            share_ip_info = json.loads(public.readFile(path_time))
        if (int(time.time()) - share_ip_info["time"]) < 86400:
            return public.returnMsg(False, "未达到时间")
        share_ip_info["time"] = int(time.time())
        public.writeFile(path_time, json.dumps(share_ip_info))
        check_sql=M("plugin_error", "plugin_error").order("id desc").limit("1").field("id").find()
        if type(check_sql) != dict: return
        time.sleep(30)
        url = "https://wafapi2.aapanel.com/api/bt_waf/plugin_error_list"
        try:
            res = requests.get(url, verify=False, timeout=60).json()
        except:
            return False
        res_list = res['res']
        for i in res_list:
            if M("plugin_error", "plugin_error").where("slug=? and status=0", i['slug']).count() > 0:
                M("plugin_error", "plugin_error").where("slug=?", i['slug']).update({"status": 1})

    def get_plugin_update_time():
        '''
            @name 获取插件更新时间
            @ps   一周更新一次
        '''
        path_time = "/www/server/panel/data/wordpress_get_plugin_update_time.pl"
        if not os.path.exists(path_time):
            public.writeFile(path_time, json.dumps({"time": int(time.time())}))
            #如果第一次运行则三天后再运行
            share_ip_info = {"time": int(time.time())-86400*2}
        else:
            share_ip_info = json.loads(public.readFile(path_time))
        if (int(time.time()) - share_ip_info["time"]) < 259200:
            return public.returnMsg(False, "未达到时间")
        share_ip_info["time"] = int(time.time())
        public.writeFile(path_time, json.dumps(share_ip_info))

        check_sql=M("wordpress_not_update", "wordpress_not_update").order("id desc").limit("1").field("id").find()
        if type(check_sql) != dict: return
        import random
        def get_plugin_time(id):
            time.sleep(30)
            url = "https://wafapi2.aapanel.com/api/bt_waf/get_wordpress_not_update?p=" + str(id)
            try:
                res = requests.get(url, verify=False, timeout=60).json()
                if len(res['res']) == 0:
                    return True
                for i in res['res']:
                    if M("wordpress_not_update", "wordpress_not_update").where("slug=?", i['slug']).count() > 0:
                        if M("wordpress_not_update", "wordpress_not_update").where("slug=? and last_time=?", (
                        i['slug'], i['last_time'])).count() == 0:
                            M("wordpress_not_update", "wordpress_not_update").where("slug=?", i['slug']).update(
                                {"last_time": i['last_time']})
                # 随机时间
            except:
                pass

        for i in range(1, 50):
            time.sleep(random.randint(10, 30))
            if get_plugin_time(i):
                return

    while True:
        try:
            auto_scan()
            check_vlun()
            check_plugin_close()
            get_plugin_update_time()
            time.sleep(7200)
        except:
            time.sleep(3600)

# 每天提交一次昨天的邮局发送总数
def submit_email_statistics():
    # 添加提交标记   每次提交昨天的  标记存在跳过  不存在添加 删除前天标记
    yesterday = datetime.now() - timedelta(days=1)
    yesterday = yesterday.strftime('%Y-%m-%d')
    cloud_yesterday_submit = f'/www/server/panel/data/{yesterday}_submit_email_statistics.pl'
    if os.path.exists(cloud_yesterday_submit):
        return
    # 判断是否有邮局
    if not os.path.exists('/www/server/panel/plugin/mail_sys/mail_send_bulk.py') or not os.path.exists('/www/vmail'):
        return

    # 处理昨天数据
    all = _get_yesterday_count2()
    if not all:
        return

    # 记录昨日发件总数
    public.set_module_logs('sys_mail', 'sent', all)

    # 添加标记
    public.writeFile(cloud_yesterday_submit, '1')
    # 删除前天标记
    before_yesterday = datetime.now() - timedelta(days=2)
    before_yesterday = before_yesterday.strftime('%Y-%m-%d')
    cloud_before_yesterday_submit = f'/www/server/panel/data/{before_yesterday}_submit_email_statistics.pl'
    if os.path.exists(cloud_before_yesterday_submit):
        os.remove(cloud_before_yesterday_submit)



def submit_module_call_statistics():
    # 添加提交标记   每次提交昨天的  标记存在跳过  不存在添加 删除前天标记  提交过的数据在统计文件里删除
    yesterday = datetime.now() - timedelta(days=1)
    yesterday = yesterday.strftime('%Y-%m-%d')
    cloud_yesterday_submit = '{}/data/{}_submit_module_call_statistics.pl'.format(public.get_panel_path(), yesterday)
    if os.path.exists(cloud_yesterday_submit):
        return

    # 取文件中yesterday和yesterday以前的数据
    datainfo = {}
    path = '{}/data/mod_log.json'.format(public.get_panel_path())
    if os.path.exists(path):
        try:
            datainfo = json.loads(public.readFile(path))
        except:
            pass
    else:
        return

    if type(datainfo) != dict:
        datainfo = {}
    # 需要提交的
    data_submit = {}
    # 当天数据
    data_reserve = {}

    try:
        for date, modules in datainfo.items():
            # 如果日期小于昨天，则提交数据
            if date.strip() <= yesterday.strip():
                data_submit[date] = modules
            else:
                data_reserve[date] = modules
    except:
        public.print_log(public.get_error_info())

    if not data_submit:
        return
    _submit_to_cloud(data_submit)

    # 将data_reserve 重新写入
    public.writeFile(path, json.dumps(data_reserve))

    # 添加标记
    public.writeFile(cloud_yesterday_submit, '1')
    # 删除前天标记
    before_yesterday = datetime.now() - timedelta(days=2)
    before_yesterday = before_yesterday.strftime('%Y-%m-%d')
    cloud_before_yesterday_submit = '{}/data/{}_submit_module_call_statistics.pl'.format(public.get_panel_path(), before_yesterday)
    if os.path.exists(cloud_before_yesterday_submit):
        os.remove(cloud_before_yesterday_submit)
    # print("提交完")
    return

def mailsys_domain_restrictions():
    if not os.path.exists('/www/server/panel/plugin/mail_sys/mail_send_bulk.py'):
        # public.print_log('000 /mail_send_bulk')
        # print('000 /mail_send_bulk')
        return

    if not os.path.exists('/www/vmail'):
        # public.print_log('000 /www/vmail')
        # print('000 /www/vmail')
        return

    yesterday = datetime.now() - timedelta(days=1)
    yesterday = yesterday.strftime('%Y-%m-%d')
    cloud_yesterday_submit = '{}/data/{}_update_mailsys_domain_restrictions.pl'.format(public.get_panel_path(), yesterday)
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
        # public.print_log('111 调用插件方法检查额度')
        # print('111 调用插件方法检查额度')
    except:
        public.print_log(public.get_error_info())
        return


    # 添加标记
    public.writeFile(cloud_yesterday_submit, '1')
    # 删除前天标记
    before_yesterday = datetime.now() - timedelta(days=2)
    before_yesterday = before_yesterday.strftime('%Y-%m-%d')
    cloud_before_yesterday_submit = '{}/data/{}_update_mailsys_domain_restrictions.pl'.format(public.get_panel_path(), before_yesterday)
    if os.path.exists(cloud_before_yesterday_submit):
        os.remove(cloud_before_yesterday_submit)
    return


def _submit_to_cloud(data_submit):
    """提交用户统计数据  接口调用  安装量等 """
    import panelAuth
    import requests
    from BTPanel import session
    cloudUrl = '{}/api/panel/submit_feature_invoked_bulk'.format(public.OfficialApiBase())
    pdata = panelAuth.panelAuth().create_serverid(None)
    url_headers = {}
    if 'token' in pdata:
        url_headers = {"authorization": "bt {}".format(pdata['token'])}

    pdata['environment_info'] = json.dumps(public.fetch_env_info())


    pdata['data'] = data_submit
    pdata['utc_offset'] = _get_utc_offset_modele()
    listTmp = requests.post(cloudUrl, json=pdata, headers=url_headers)
    ret = listTmp.json()
    # public.print_log(f"提交上传['data']999 ---{pdata['data']}")
    # public.print_log(f"提交返回999 ---{ret}")
    # if not ret['success']:
    #     print(f"|-{ret['res']}")
    #     public.print_log(f"|-submit_module_call_statistics: {ret['res']}")
    # public.print_log(f"|-{ret}")
    return


# 获取系统时间与utc时间的差值
def _get_utc_offset_modele():
    # 系统时间戳
    current_local_time = datetime.now()
    current_local_timestamp = int(current_local_time.timestamp())

    # 获取当前 UTC 时间的时间戳
    current_utc_time = datetime.utcnow()
    current_utc_timestamp = int(current_utc_time.timestamp())

    # 计算时区差值（秒）
    timezone_offset = current_local_timestamp - current_utc_timestamp
    offset = timezone_offset/3600

    return offset


# 获取系统时间与utc时间的差值
def _get_utc_offset():
    # 系统时间戳
    current_local_time = datetime.now()
    current_local_timestamp = int(current_local_time.timestamp())

    # UTC时间戳
    current_utc_time = datetime.utcnow()
    current_utc_timestamp = int(current_utc_time.timestamp())

    # 计算时区差值（秒）
    timezone_offset = current_local_timestamp - current_utc_timestamp

    if timezone_offset > 0:     # 东时区   需要减
        return timezone_offset, True
    else:                       # 西时区
        return abs(timezone_offset), False


def _get_yesterday_count2():
    # 获取昨天的开始时间和结束时间（本地时间）
    today = datetime.now()
    yesterday = today - timedelta(days=1)

    # 昨天 00:00:00
    yesterday_start = datetime(yesterday.year, yesterday.month, yesterday.day, 0, 0, 0)

    # 昨天 23:59:59
    yesterday_end = datetime(yesterday.year, yesterday.month, yesterday.day, 23, 59, 59)

    # 转为时间戳
    start_time = int(yesterday_start.timestamp())
    end_time = int(yesterday_end.timestamp())

    try:
        query = public.S('send_mails').alias('rm').prefix('')
        query.inner_join('senders s', 'rm.postfix_message_id=s.postfix_message_id')
        query.where('s.postfix_message_id is not null')
        if start_time > 0:
            query.where('rm.log_time > ?', start_time - 1)
        if end_time > 0:
            query.where('rm.log_time < ?', end_time + 1)

        query.where('rm.status  =?', 'sent')
        from power_mta.maillog_stat import query_maillog_with_time_section
        ret = query_maillog_with_time_section(query, start_time, end_time)
        allnum = len(ret)
    except:
        allnum = 0
    return allnum

# # 获取昨日邮局收发件统计数据
# def _get_yesterday_count():
#     maillog_path = '/var/log/maillog'
#     if "ubuntu" in public.get_linux_distribution().lower():
#         maillog_path = '/var/log/mail.log'
#
#     if not os.path.exists(maillog_path):
#         return 0
#     output, err = public.ExecShell(
#     f'pflogsumm -d yesterday --verbose-msg-detail --zero-fill --iso-date-time --rej-add-from {maillog_path}')
#     if err:
#         # public.print_log(f"err 4444 {err}")
#         return 0
#
#     data = _pflogsumm_data_treating(output)
#     all = 0
#     # public.print_log(f"yesterday sent: {data['stats_dict']}")
#     if data.get('stats_dict', None):
#         all = data['stats_dict'].get('delivered', 0)
#     return all
#
# # 分析命令执行后的数据
# def _pflogsumm_data_treating(output):
#     import re
#     stats_dict = {}
#
#     # 使用正则表达式来匹配和提取关键信息
#     patterns = [
#         r'(\d+)\s+received',
#         r'(\d+)\s+delivered',
#         r'(\d+)\s+forwarded',
#         r'(\d+)\s+deferred\s+\((\d+)\s+deferrals\)',
#         r'(\d+)\s+bounced',
#         r'(\d+)\s+rejected\s+\((\d+)%\)',
#         r'(\d+)\s+reject\s+warnings',
#         r'(\d+)\s+held',
#         r'(\d+)\s+discarded\s+\((\d+)%\)',
#         r'(\d+)\s+bytes\s+received',
#         r'(\d+)k\s+bytes\s+delivered',
#         r'(\d+)\s+senders',
#         r'(\d+)\s+sending\s+hosts/domains',
#         r'(\d+)\s+recipients',
#         r'(\d+)\s+recipient\s+hosts/domains'
#     ]
#
#     for pattern in patterns:
#         match = re.search(pattern, output)
#         if match:
#             # 将找到的数字转换为整数并存入字典
#             stats_dict[pattern] = int(match.group(1))
#
#     friendly_names = {
#         r'(\d+)\s+received': 'received',
#         r'(\d+)\s+delivered': 'delivered',
#         r'(\d+)\s+forwarded': 'forwarded',
#         r'(\d+)\s+deferred\s+\((\d+)\s+deferrals\)': 'deferred',
#         r'(\d+)\s+bounced': 'bounced',
#         r'(\d+)\s+rejected\s+\((\d+)%\)': 'rejected',
#         r'(\d+)\s+reject\s+warnings': 'reject_warnings',
#         r'(\d+)\s+held': 'held',
#         r'(\d+)\s+discarded\s+\((\d+)%\)': 'discarded',
#         r'(\d+)\s+bytes\s+received': 'bytes_received',
#         r'(\d+)k\s+bytes\s+delivered': 'bytes_delivered_kilo',
#         r'(\d+)\s+senders': 'senders',
#         r'(\d+)\s+sending\s+hosts/domains': 'sending_hosts_domains',
#         r'(\d+)\s+recipients': 'recipients',
#         r'(\d+)\s+recipient\s+hosts/domains': 'recipient_hosts_domains'
#     }
#
#     stats_dict = {friendly_names[key]: value for key, value in stats_dict.items() if key in friendly_names}
#     keys_to_remove = [
#         "reject_warnings",
#         "held",
#         "discarded",
#         "bytes_received",
#         "senders",
#         "sending_hosts_domains",
#         "recipients",
#         "recipient_hosts_domains"
#     ]
#
#     for key in keys_to_remove:
#         stats_dict.pop(key, None)
#
#     data = {
#         "stats_dict": stats_dict,
#     }
#     return data



def mailsys_domain_blecklisted_alarm():
    if not os.path.exists('/www/server/panel/plugin/mail_sys/mail_send_bulk.py') or not os.path.exists('/www/vmail'):
        return

    yesterday = datetime.now() - timedelta(days=1)
    yesterday = yesterday.strftime('%Y-%m-%d')
    cloud_yesterday_submit = '{}/data/{}_mailsys_domain_blecklisted_alarm.pl'.format(public.get_panel_path(), yesterday)
    if os.path.exists(cloud_yesterday_submit):
        return
    if os.path.exists("/www/server/panel/plugin/mail_sys"):
        sys.path.insert(1, "/www/server/panel/plugin/mail_sys")
    # 检查版本 检查是否能查询额度  剩余额度
    import public.PluginLoader as plugin_loader
    bulk = plugin_loader.get_module('{}/plugin/mail_sys/mail_send_bulk.py'.format(public.get_panel_path()))
    SendMailBulk = bulk.SendMailBulk
    try:
        SendMailBulk().check_domain_blacklist_corn()

    except:
        public.print_log(public.get_error_info())
        return


    # 添加标记
    public.writeFile(cloud_yesterday_submit, '1')
    # 删除前天标记
    before_yesterday = datetime.now() - timedelta(days=2)
    before_yesterday = before_yesterday.strftime('%Y-%m-%d')
    cloud_before_yesterday_submit = '{}/data/{}_mailsys_domain_blecklisted_alarm.pl'.format(public.get_panel_path(), before_yesterday)
    if os.path.exists(cloud_before_yesterday_submit):
        os.remove(cloud_before_yesterday_submit)
    return

# 邮件证书过期告警
# def mailsys_cert_expiry_alarm():
#     if not os.path.exists('/www/server/panel/plugin/mail_sys/mail_send_bulk.py') or not os.path.exists('/www/vmail'):
#         return
#
#     yesterday = datetime.now() - timedelta(days=1)
#     yesterday = yesterday.strftime('%Y-%m-%d')
#     cloud_yesterday_submit = '{}/data/{}_mailsys_cert_expiry_alarm.pl'.format(public.get_panel_path(), yesterday)
#     if os.path.exists(cloud_yesterday_submit):
#         return
#
#     script = '/www/server/panel/plugin/mail_sys/script/certificate_expired.py'
#     if not os.path.exists(script):
#         return
#
#     cmd = f"btpython {script}"
#     aa = public.ExecShell(cmd)
#
#
#     # 添加标记
#     public.writeFile(cloud_yesterday_submit, '1')
#     # 删除前天标记
#     before_yesterday = datetime.now() - timedelta(days=2)
#     before_yesterday = before_yesterday.strftime('%Y-%m-%d')
#     cloud_before_yesterday_submit = '{}/data/{}_mailsys_cert_expiry_alarm.pl'.format(public.get_panel_path(), before_yesterday)
#     if os.path.exists(cloud_before_yesterday_submit):
#         os.remove(cloud_before_yesterday_submit)
#     return

# 邮件域名邮箱使用限额告警
def mailsys_quota_alarm1():
    if not os.path.exists('/www/server/panel/plugin/mail_sys/mail_sys_main.py') or not os.path.exists('/www/vmail'):
        return

    yesterday = datetime.now() - timedelta(days=1)
    yesterday = yesterday.strftime('%Y-%m-%d')
    cloud_yesterday_submit = '{}/data/{}_mailsys_quota_alarm.pl'.format(public.get_panel_path(), yesterday)
    if os.path.exists(cloud_yesterday_submit):
        return

    script = '/www/server/panel/plugin/mail_sys/script/check_quota_alerts.py'
    if not os.path.exists(script):
        return

    cmd = f"btpython {script}"
    aa = public.ExecShell(cmd)


    # 添加标记
    public.writeFile(cloud_yesterday_submit, '1')
    # 删除前天标记
    before_yesterday = datetime.now() - timedelta(days=2)
    before_yesterday = before_yesterday.strftime('%Y-%m-%d')
    cloud_before_yesterday_submit = '{}/data/{}_mailsys_quota_alarm.pl'.format(public.get_panel_path(), before_yesterday)
    if os.path.exists(cloud_before_yesterday_submit):
        os.remove(cloud_before_yesterday_submit)
    return

# 邮件域名邮箱使用限额告警
def mailsys_quota_alarm():
    while True:
        try:
            if not os.path.exists('/www/server/panel/plugin/mail_sys/mail_sys_main.py') or not os.path.exists(
                    '/www/vmail'):
                # time.sleep(7200)
                time.sleep(43200)
                continue

            script = '/www/server/panel/plugin/mail_sys/script/check_quota_alerts.py'
            if not os.path.exists(script):
                # time.sleep(7200)
                time.sleep(43200)
                continue

            time.sleep(3600)  # 进入脚本前等待 和更新配额错开时间
            cmd = f"btpython {script}"
            public.ExecShell(cmd)

        except:
            pass

        time.sleep(43200)


# 邮局更新域名邮箱使用量
def mailsys_update_usage():
    while True:
        try:
            if not os.path.exists('/www/server/panel/plugin/mail_sys/mail_sys_main.py') or not os.path.exists(
                    '/www/vmail'):
                time.sleep(43200)
                continue

            script = '/www/server/panel/plugin/mail_sys/script/update_usage.py'
            if not os.path.exists(script):
                time.sleep(43200)
                continue
            cmd = f"btpython {script}"
            public.ExecShell(cmd)

        except:
            pass

        # 每12小时执行一次
        time.sleep(43200)



# 邮局自动回复
def auto_reply_tasks():
    while True:
        try:

            if not os.path.exists('/www/server/panel/plugin/mail_sys/mail_sys_main.py') or not os.path.exists(
                    '/www/vmail'):
                time.sleep(3600)
                continue

            if os.path.exists("/www/server/panel/plugin/mail_sys"):
                sys.path.insert(1, "/www/server/panel/plugin/mail_sys")
            try:
                from plugin.mail_sys.mail_sys_main import mail_sys_main
                mail_sys_main().auto_reply_tasks()
            except Exception as e:
                public.print_log(public.get_error_info())

        except:
            pass

        # 每小时执行一次
        time.sleep(3600)




# 邮局自动扫描异常邮箱
def auto_scan_abnormal_mail():
    while True:
        try:

            if not os.path.exists('/www/server/panel/plugin/mail_sys/mail_send_bulk.py') or not os.path.exists(
                    '/www/vmail'):
                time.sleep(7200)
                continue

            # 检查授权
            endtime = public.get_pd()[1]
            curtime = int(time.time())
            if endtime != 0 and endtime < curtime:
                time.sleep(7200)
                continue

            # 检查是否关闭了自动扫描
            path = '/www/server/panel/plugin/mail_sys/data/abnormal_mail_check_switch'
            if os.path.exists(path):
                time.sleep(7200)
                continue
            if os.path.exists("/www/server/panel/plugin/mail_sys"):
                sys.path.insert(1, "/www/server/panel/plugin/mail_sys")
            # 导入并执行扫描
            import public.PluginLoader as plugin_loader
            bulk = plugin_loader.get_module('{}/plugin/mail_sys/mail_send_bulk.py'.format(public.get_panel_path()))
            SendMailBulk = bulk.SendMailBulk
            try:
                SendMailBulk().check_abnormal_emails()
                # public.print_log(f"MailServer automatically scans for abnormal mailboxes ----")
            except Exception as e:
                # public.print_log(f"异常邮箱扫描出错: {str(e)}")
                public.print_log(public.get_error_info())

        except:
            pass

        time.sleep(7200)


# 每天刷新docker app 列表
def refresh_dockerapps():
    while True:
        try:

            from mod.project.docker.app.appManageMod import AppManage
            AppManage().refresh_apps_list()
        except Exception as e:
            # public.print_log(f"每天刷新docker: {str(e)}")
            pass

        time.sleep(86400)


def domain_ssl_service():
    while 1:
        try:
            # check 6h, inside
            from ssl_domainModelV2.service import make_suer_ssl_task
            make_suer_ssl_task()
        except Exception as e:
            public.print_log("domain_ssl_service make_suer_ssl_task error , %s" % e)
        time.sleep(3600)
        # 1h
        try:
            from ssl_dnsV2.dns_manager import DnsManager
            DnsManager().builtin_dns_checker()
        except Exception as e:
            public.print_log("builtin_dns_auth error , %s" % e)

#每隔20分钟更新一次网站报表数据
def update_monitor_requests():
    while True:
        try:
            import class_v2.data_v2 as data_v2
            dataObject = data_v2.data()
            dataObject.getSiteThirtyTotal()
        except Exception as e:
            public.print_log(f"更新网站报表数据: {str(e)}")
            pass

        time.sleep(60*20)

# 每隔20分钟更新一次waf报表数据
def update_waf_config():
    while True:
        try:
            import class_v2.data_v2 as data_v2
            dataObject = data_v2.data()
            dataObject.getSiteWafConfig()
        except Exception as e:
            public.print_log(f"更新Waf报表数据: {str(e)}")
            pass

        time.sleep(60*20)

# 每6小时进行恶意文件扫描
def malicious_file_scanning():
    while True:
        try:
            from projectModelV2 import safecloudModel
            safecloud = safecloudModel.main()
            # 调用 webshell_detection 函数
            safecloud.webshell_detection({'is_task': 'true'})
        except Exception as e:
            public.print_log(f"Malicious file scanning: {str(e)}")
            pass

        time.sleep(60*60*6)


# 多服务守护任务，仅在多服务下执行，每5分钟检查一次
def multi_web_server_daemon():
    while True:
        try:
            if public.get_multi_webservice_status():
                import psutil
                from panel_site_v2 import panelSite
                from script.restart_services import DaemonManager

                obj = panelSite()
                pid_paths = {
                    'nginx': "/www/server/nginx/logs/nginx.pid",
                    'apache': "/www/server/apache/logs/httpd.pid",
                    'openlitespeed': "/tmp/lshttpd/lshttpd.pid"
                }

                for service_name, pid_path in pid_paths.items():
                    sys.path.append("..")
                    daemon_info = DaemonManager.safe_read()
                    if service_name not in daemon_info:
                        continue

                    is_running = False
                    if os.path.exists(pid_path):
                        pid = public.readFile(pid_path)

                        if pid:
                            try:
                                psutil.Process(int(pid))
                                is_running = True
                            except:
                                pass

                    if not is_running:
                        public.WriteLog("Service Daemon", f"Multi-WebServer: An error occurred in {service_name}. Initiate the repair")
                        obj.cheak_port_conflict('enable')
                        obj.ols_update_config('enable')
                        obj.apache_update_config('enable')
                        public.webservice_operation('nginx')
                        public.WriteLog("Service Daemon", f"Multi-WebServer: The {service_name} repair was successful")
                        break
        except Exception as e:
            public.print_log(f"Multi-WebServer: {e}")

        time.sleep(300)


def run_thread():
    global thread_dict,task_obj
    thread_keys = thread_dict.keys()
    # 优先启动
    core_tasks_list = {
        "daemon_panel": daemon_panel,  # 面板守护
        "daemon_service": daemon_service,  # 服务守护
        "restart_panel_service": restart_panel_service,  # 面板重启服务
        "check_panel_auth": check_panel_auth,  # 面板授权检查
        "push_msg": push_msg,  # 面板推送消息
        "start_task": task_obj.start_task, # panel task
        "systemTask": systemTask, # 系统监控
        "check_panel_msg": check_panel_msg,  # 面板消息提醒
        "check_breaking_through_cron": check_breaking_through_cron,  # 检测防爆破计划任务
    }

    # 延迟启动
    normal_tasks_list = {
        "check502Task": check502Task,  # 检测502
        "send_mail_time": send_mail_time, # 每3分钟检测邮件信息
        "update_waf_config": update_waf_config, # 每隔20分钟更新一次waf报表数据
        "update_monitor_requests": update_monitor_requests, # 每隔20分钟更新一次网站报表数据
        "check_site_monitor": check_site_monitor, # 每10分钟检查站点监控
        "check_panel_ssl": check_panel_ssl, # 每小时检查面板SSL证书
        "find_stored_favs": data_v2_cls().find_stored_favicons, # 每1小时找favicons
        "update_software_list": update_software_list,  # 每5小时更新软件列表
        "malicious_file_scanning": malicious_file_scanning, # 每6小时进行恶意文件扫描
        "domain_ssl_service": domain_ssl_service, # 每6小时进行域名SSL服务
        "multi_web_server_daemon": multi_web_server_daemon, # 多服务守护每5分钟检测一次
        "maillog_event": maillog_event,  # 邮局日志事件监控 event loop
        "aggregate_maillogs": aggregate_maillogs_task,  # 每分钟聚合邮局日志
        "mail_automations": schedule_automations_forever,  # 每分钟邮局自动化任务
        "auto_reply_tasks": auto_reply_tasks,  # 每1小时执行一次 自动回复邮件
        "mailsys_quota_alarm": mailsys_quota_alarm,  # 2h 邮件域名邮箱使用限额告警
        "auto_scan_abnormal_mail": auto_scan_abnormal_mail,  # 每2小时执行一次 自动扫描异常邮箱
        "mailsys_update_usage": mailsys_update_usage,  # 12h 邮局更新域名邮箱使用量
        "submit_email_statistics": submit_email_statistics,  # 每天一次 昨日邮件发送统计
        "submit_module_call_statistics": submit_module_call_statistics,  # 每天一次 提交今天之前的统计数据
        "mailsys_domain_blecklisted_alarm": mailsys_domain_blecklisted_alarm,  # 每天一次 邮局黑名单检测

        "count_ssh_logs": count_ssh_logs,  # 每天一次统计SSH登录日志
        "update_vulnerabilities": update_vulnerabilities,  # 每天一次 更新漏洞信息
        "refresh_dockerapps": refresh_dockerapps, # 每天刷新docker app 列表
    }

    for core in core_tasks_list.keys():
        if not core in thread_keys or not thread_dict[core].is_alive():
            thread_dict[core] = threading.Thread(
                target=core_tasks_list[core]
            )
            thread_dict[core].start()
            time.sleep(0.5) # 错峰
    time.sleep(3) # 等核心稳定

    max_cpu_rate = 70
    total_time = 0
    for normal in normal_tasks_list.keys():
        if normal in core_tasks_list.keys():
            continue
        if not normal in thread_keys or not thread_dict[normal].is_alive():
            while 1:
                if total_time >= 60:  # 累计超过1分钟, 直接运行
                    thread_dict[normal] = threading.Thread(
                        target=normal_tasks_list[normal]
                    )
                    thread_dict[normal].start()
                    break

                current_cpu = cpu_percent(interval=1)
                if current_cpu < max_cpu_rate:
                    thread_dict[normal] = threading.Thread(
                        target=normal_tasks_list[normal]
                    )
                    thread_dict[normal].start()
                    break
                else:
                    delay = min(max(1 + (current_cpu / 10) * 0.5, 1), 5)
                    total_time += delay
                    time.sleep(delay)
            time.sleep(0.5)



def func():
    os.system(get_python_bin() + " {}/script/scan_log.py > /dev/null".format(base_path))
    #如果需要循环调用，就要添加以下方法
    timer = threading.Timer(86400, func)
    timer.start()

def scan_log_site():
    now_time = datetime.datetime.now()
    next_time = now_time + datetime.timedelta(days=+1)
    next_year = next_time.date().year
    next_month = next_time.date().month
    next_day = next_time.date().day
    next_time = datetime.datetime.strptime(str(next_year) + "-" + str(next_month) + "-" + str(next_day) + " 03:00:00",
                                           "%Y-%m-%d %H:%M:%S")
    timer_start_time = (next_time - now_time).total_seconds()
    timer = threading.Timer(timer_start_time, func)
    timer.start()

# 面板消息提醒
# def check_panel_msg():
#     python_bin = get_python_bin()
#     while True:
#         os.system('{} {}/script/check_msg.py &'.format(python_bin,base_path))
#         time.sleep(600)



#预安装网站监控报表
def check_site_monitor():
    site_total_uninstall = '{}/data/site_total_uninstall.pl'.format(public.get_panel_path())
    site_total_install_path = '{}/site_total'.format(public.get_setup_path())
    site_total_service='/etc/systemd/system/site_total.service'
    sleep_time = 60
    while True:
        install_name = ''
        if not os.path.exists(site_total_uninstall):
            if not os.path.exists(site_total_install_path):public.ExecShell("rm -f {}".format(site_total_service))
            if public.GetWebServer() !="openlitespeed" and not os.path.exists(site_total_service) and not os.path.exists(os.path.join(public.get_panel_path(),"plugin/monitor/info.json")) and public.M('tasks').where('name=? and status=?',('Install [site_total_monitor]','0')).count() < 1:
                execstr="curl https://node.aapanel.com/site_total/install.sh|bash"
                install_name = 'Install [site_total_monitor]'
                sleep_time=86400
        else:
            if os.path.exists(site_total_service):
                install_name = 'Uninstall [site_total_monitor]'
                execstr="bash /www/server/site_total/scripts/uninstall.sh"
        if install_name:
            public.M('tasks').add('id,name,type,status,addtime,execstr',(None, install_name,'execshell','0',time.strftime('%Y-%m-%d %H:%M:%S'),execstr))
            public.writeFile('/tmp/panelTask.pl','True')
        time.sleep(sleep_time)

# 检测防爆破计划任务
def check_breaking_through_cron():
    try:
        key='breaking_through_cron'
        import class_v2.breaking_through as breaking_through
        _breaking_through_obj = breaking_through.main()
        _breaking_through_obj.del_cron()
        while True:
            time.sleep(60)
            _breaking_through_obj.cron_method()
    except Exception as e:
        time.sleep(60)
        # public.writeFile('/www/server/panel/logs/breaking_through.log', "[{}]{}\n".format(public.format_date(), public.get_error_info()), 'a')
        public.writeFile('/www/server/panel/logs/breaking_through.log',"{}".format(e))
        check_breaking_through_cron()

def run_post_update_tasks(from_version, to_version):
    """
    在版本更新后执行一次性任务。
    :param from_version: 旧版本号
    :param to_version: 新版本号
    :return: bool, 任务是否成功
    """
    try:
        if from_version == to_version:
            logging.info("Current task version is the same as the last version, no update tasks to run.")
            return True

        logging.info(f"Detected update program start, {from_version} -> {to_version}. Executing one-time update tasks...")

        if from_version < '1.0.0':
            base_path = public.get_panel_path()
            dirs_to_clean = [
                os.path.join(base_path, 'logs/sqlite_easy'),
                os.path.join(base_path, 'logs/sql_log')
            ]

            for dir_path in dirs_to_clean:
                if os.path.isdir(dir_path):
                    try:
                        shutil.rmtree(dir_path)
                        logging.info(f"Removed directory: {dir_path}")
                    except Exception as e:
                        logging.error(f"Removing directory {dir_path} failed: {str(e)}")
                else:
                    logging.info(f"Directory not exists, skipped: {dir_path}")

        if from_version < '1.0.1':
            sites = public.M('sites').field('id,name,path').select()
            pattern = r'<a class="btlink" href="https://www\.aapanel\.com/new/download\.html\?invite_code=aapanele" target="_blank">(.+?)</a>'
            import re
            for site in sites:
                dir = [
                    os.path.join(site['path'], '404.html'),
                    os.path.join(site['path'], '502.html'),
                    os.path.join(site['path'], 'index.html'),
                ]
                for d in dir:
                    if os.path.exists(d):
                        html = public.readFile(d)
                        result = re.sub(pattern, r'\1', html)
                        public.writeFile(d, result.strip())

        logging.info("All one-time update tasks executed successfully.")
        return True
    except Exception as e:
        logging.error(f"Executing one-time update task failed: {str(e)}")
        return False


def main():
    main_pid = 'logs/task.pid'
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
    task_log_file = 'logs/task.log'

    # trace malloc
    # tracemalloc.start()

    is_debug = False

    if os.path.exists('{}/data/debug.pl'.format(base_path)):
        is_debug = True

    try:
        logging.basicConfig(level=logging.NOTSET if is_debug else logging.INFO, format='%(asctime)s [%(levelname)s]: %(message)s',
                            datefmt='%Y-%m-%d %H:%M:%S', filename=task_log_file, filemode='a+')
    except Exception as ex:
        print(ex)
    logging.info('Service Up')
    time.sleep(5)

    # run_post_update_tasks
    version_file = '{}/data/task_version.pl'.format(public.get_panel_path())
    last_version = "0.0.0"  # 默认为一个很旧的版本

    if os.path.exists(version_file):
        last_version = public.readFile(version_file) or "0.0.0"

    if run_post_update_tasks(last_version, CURRENT_TASK_VERSION):
        public.writeFile(version_file, CURRENT_TASK_VERSION)

    run_thread()
    # time.sleep(15)
    startTask()


if __name__ == "__main__":
    main()

