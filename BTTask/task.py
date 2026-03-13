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
import os
import shutil
import sqlite3
import subprocess
import sys
import threading
import time
import traceback
from datetime import datetime, timedelta
from typing import Optional, Tuple

import psutil

try:
    import ujson as json
except ImportError:
    try:
        os.system("btpip install ujson")
        import ujson as json
    except:
        import json

sys.path.insert(0, "/www/server/panel/class/")

try:
    from public.hook_import import hook_import

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


# 系统监控全局缓存
_system_task_state = {
    "table_ensure": False,
    # {"timestamp": 0, "total_up": 0, "total_down": 0, "up_packets": {}, "down_packets": {}}
    "last_network_io": {},
    # {"timestamp": 0, "read_count": 0, "write_count": 0, "read_bytes": 0, "write_bytes": 0, "read_time": 0, "write_time": 0}
    "last_disk_io": {},
    # {pid: (create_time, cpu_time, disk_read, disk_write, timestamp)}
    "last_process_cache": {},
    # {pid: (inactive_count, last_check_time)}
    "inactive_process_cache": {},
    "last_clear_time": 0,
    "last_cpu_times": None,
}


# 系统监控任务
def systemTask():
    def get_cpu_percent_smooth() -> float:
        """窗口时间内CPU占用率"""
        try:
            current_times = psutil.cpu_times()
            last_times = _system_task_state.get("last_cpu_times")
            if not last_times:
                _system_task_state["last_cpu_times"] = current_times
                return psutil.cpu_percent(interval=0.1)
            all_delta = sum(current_times) - sum(last_times)
            if all_delta == 0.0:
                return 0.0
            idle_delta = getattr(current_times, "idle", 0) - getattr(last_times, "idle", 0)
            cpu_percent = ((all_delta - idle_delta) / all_delta) * 100
            _system_task_state["last_cpu_times"] = current_times
            return max(0.0, min(100.0, cpu_percent))
        except Exception:
            return psutil.cpu_percent(interval=0.1)

    def get_mem_used_percent() -> float:
        """内存使用率"""
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

    # noinspection PyUnusedLocal,PyTypeChecker
    def get_swap_used_percent() -> float:
        """
        获取Swap内存已占用的百分比（返回0.0~100.0，异常时返回100.0）
        逻辑：Swap使用率 = (已使用Swap / 总Swap容量) * 100%
        """
        try:
            # 获取Swap内存信息（psutil.swap_memory()返回namedtuple）
            swap = psutil.swap_memory()

            # Swap总容量（bytes → MB，和物理内存计算单位保持一致）
            swap_total = swap.total / 1024 / 1024
            # Swap已使用量（bytes → MB）
            swap_used = swap.used / 1024 / 1024

            swap_free = swap.free / 1024 / 1024

            # 避免除以0（无Swap分区时）
            if swap_total == 0:
                return 0.0, 0, 0, 0  # 无Swap时默认返回100%（或根据需求改0.0）

            # 计算使用率（保留2位小数，确保返回float类型）
            used_percent = round((swap_used / swap_total) * 100.0, 2)

            # 边界值修正（防止因系统浮点误差导致超过100%）
            # return min(used_percent, 100.0),swap.total/1024,swap.used/1024,swap.free/1024
            return min(used_percent, 100.0), swap.total, swap.used, swap.free

        # 捕获所有异常，返回100%（和物理内存函数的异常返回逻辑一致）
        except Exception:
            return 100.0, 0, 0, 0

    def get_load_average() -> Tuple[float, float, float, float]:
        """负载平均"""
        try:
            one, five, fifteen = os.getloadavg()
            max_v = psutil.cpu_count() * 2
            lpro = round((one / max_v) * 100, 2) if max_v else 0
            if lpro > 100:
                lpro = 100
            return lpro, float(one), float(five), float(fifteen)
        except Exception:
            return 0.0, 0.0, 0.0, 0.0

    def get_network_io() -> Optional[dict]:
        """网络IO"""
        try:
            network_io = psutil.net_io_counters(pernic=True)
            ret = {
                'total_up': sum(v.bytes_sent for v in network_io.values()),
                'total_down': sum(v.bytes_recv for v in network_io.values()),
                'timestamp': time.time(),
                'down_packets': {k: v.bytes_recv for k, v in network_io.items()},
                'up_packets': {k: v.bytes_sent for k, v in network_io.items()}
            }

            last_io = _system_task_state["last_network_io"]
            if not last_io:
                _system_task_state["last_network_io"] = ret
                return None

            diff_t = (ret["timestamp"] - last_io.get("timestamp", 0)) * 1024  # 转KB
            if diff_t <= 0:
                return None

            res = {
                'up': round((ret['total_up'] - last_io.get('total_up', 0)) / diff_t, 2),
                'down': round((ret['total_down'] - last_io.get('total_down', 0)) / diff_t, 2),
                'total_up': ret['total_up'],
                'total_down': ret['total_down'],
                'down_packets': {
                    k: round((v - last_io.get('down_packets', {}).get(k, 0)) / diff_t, 2)
                    for k, v in ret['down_packets'].items()
                },
                'up_packets': {
                    k: round((v - last_io.get('up_packets', {}).get(k, 0)) / diff_t, 2)
                    for k, v in ret['up_packets'].items()
                }
            }
            _system_task_state["last_network_io"] = ret
            return res
        except Exception:
            return None

    def get_disk_io() -> Optional[dict]:
        """磁盘IO"""
        if not os.path.exists('/proc/diskstats'):
            return None
        try:
            disk_io = psutil.disk_io_counters()
            if not disk_io:
                return None

            ret = {
                'read_count': disk_io.read_count,
                'write_count': disk_io.write_count,
                'read_bytes': disk_io.read_bytes,
                'write_bytes': disk_io.write_bytes,
                'read_time': disk_io.read_time,
                'write_time': disk_io.write_time,
                'timestamp': time.time()
            }

            last_io = _system_task_state["last_disk_io"]
            if not last_io:
                _system_task_state["last_disk_io"] = ret
                return None

            diff_t = ret["timestamp"] - last_io.get("timestamp", 0)
            if diff_t <= 0:
                return None

            res = {
                'read_count': int((ret["read_count"] - last_io.get("read_count", 0)) / diff_t),
                'write_count': int((ret["write_count"] - last_io.get("write_count", 0)) / diff_t),
                'read_bytes': int((ret["read_bytes"] - last_io.get("read_bytes", 0)) / diff_t),
                'write_bytes': int((ret["write_bytes"] - last_io.get("write_bytes", 0)) / diff_t),
                'read_time': int((ret["read_time"] - last_io.get("read_time", 0)) / diff_t),
                'write_time': int((ret["write_time"] - last_io.get("write_time", 0)) / diff_t),
            }
            _system_task_state["last_disk_io"] = ret
            return res
        except Exception:
            return None

    _XSS_TRANS = str.maketrans({
        '&': '&amp;',
        '<': '&lt;',
        '>': '&gt;',
        '"': '&quot;',
        "'": '&#x27;'
    })

    def xss_encode(s: str) -> str:
        """XSS"""
        if not isinstance(s, str):
            s = str(s)
        if not any(c in s for c in '&<>"\''):
            return s
        return s.translate(_XSS_TRANS)

    def cut_top_list(process_list, *sort_key, top_num=5) -> list:
        # """最小堆取前N"""
        # import heapq
        # if not process_list or not sort_key:
        #     return []
        # try:
        #     if len(sort_key) == 1:
        #         return heapq.nlargest(
        #             top_num, process_list, key=lambda x: x.get(sort_key[0], 0)
        #         )
        #     else:
        #         return heapq.nlargest(
        #             top_num, process_list, key=lambda x: tuple(x.get(k, 0) for k in sort_key)
        #         )
        # except (TypeError, ValueError):
        #     return []
        """前N个"""
        if not process_list or not sort_key:
            return []
        tops = sorted(
            process_list, key=lambda x: tuple(x.get(k, 0) for k in sort_key), reverse=True
        )
        return tops[:top_num]

    def get_process_list() -> list:
        """获取进程列表"""
        SKIP_NAMES = {
            'edac-poller', 'devfreq_wq', 'watchdogd', 'kthrotld', 'acpi_thermal_pm', 'charger_manager',
            'kthreadd', 'rcu_gp', 'rcu_par_gp', 'rcu_sched', 'migration/0', 'cpuhp/0', 'kdevtmpfs',
            'netns', 'oom_reaper', 'writeback', 'crypto', 'kintegrityd', 'kblockd', 'ata_sff',
        }

        try:
            pids = psutil.pids()
            current_pid = os.getpid()
            timer = getattr(time, "monotonic", time.time)
            cpu_num = psutil.cpu_count() or 1
            process_list = []
            new_cache = {}
            inactive_cache = _system_task_state["inactive_process_cache"]
            for pid in pids:
                if pid == current_pid:
                    continue
                if pid < 10:  # 核心进程
                    continue
                if pid in inactive_cache:
                    inactive_count, last_check = inactive_cache[pid]
                    # 5分钟重新检查一次
                    if time.time() - last_check < 300 and inactive_count >= 3:
                        inactive_cache[pid] = (inactive_count, time.time())  # 结合后续10分钟清理逻辑
                        continue

                try:
                    p = psutil.Process(pid)
                    if p.status() in (psutil.STATUS_ZOMBIE, psutil.STATUS_DEAD):  # 休眠/僵尸
                        continue
                    process_name = None
                    try:
                        process_name = p.name()
                        if process_name in SKIP_NAMES:
                            continue
                    except:
                        pass

                    with p.oneshot():
                        create_time = p.create_time()
                        if not process_name:
                            try:
                                process_name = p.name()
                            except:
                                process_name = "unknown"
                        last_cache = _system_task_state["last_process_cache"].get(pid)
                        if last_cache and last_cache[0] != create_time:  # 进程应该被重启了
                            last_cache = None
                            if pid in inactive_cache:
                                del inactive_cache[pid]

                        p_cpu_time = p.cpu_times()
                        cpu_time = p_cpu_time.system + p_cpu_time.user
                        io_counters = p.io_counters()
                        memory_info = p.memory_info()
                        current_time = timer()
                        # 刷新缓存
                        new_cache[pid] = (
                            create_time, cpu_time, io_counters.read_bytes, io_counters.write_bytes, current_time
                        )
                        if not last_cache:  # 初次处理的进程
                            continue
                        diff_t = current_time - last_cache[4]
                        if diff_t <= 0:
                            continue

                        cpu_percent = max(round((cpu_time - last_cache[1]) * 100 / diff_t / cpu_num, 2), 0)
                        disk_read = max(0, int((io_counters.read_bytes - last_cache[2]) / diff_t))
                        disk_write = max(0, int((io_counters.write_bytes - last_cache[3]) / diff_t))
                        disk_total = disk_read + disk_write

                        if cpu_percent == 0 and disk_total == 0:
                            if pid in inactive_cache:
                                inactive_cache[pid] = (inactive_cache[pid][0] + 1, time.time())
                            else:
                                inactive_cache[pid] = (1, time.time())
                            continue

                        if pid in inactive_cache:
                            del inactive_cache[pid]

                        # swap占用
                        try:
                            swap = p.memory_full_info().swap
                        except:
                            swap = 0
                        # connect_count = len(
                        #     p.net_connections() if hasattr(p, "net_connections") else p.connections()  # noqa
                        # )
                        process_info = {
                            'pid': pid,
                            'name': process_name,
                            'username': p.username(),
                            'cpu_percent': cpu_percent,
                            'memory': memory_info.rss,
                            'swap': swap,
                            'disk_read': disk_read,
                            'disk_write': disk_write,
                            'disk_total': disk_total or 0,
                            'cmdline': ' '.join(filter(lambda x: x, p.cmdline()))[:500],
                            'create_time': create_time,
                            'connect_count': 0,  # future
                            'net_total': 0,  # future
                            'up': 0,  # future
                            'down': 0,  # future
                            'up_package': 0,  # future
                            'down_package': 0,  # future
                        }
                        # process_info["net_total"] = process_info["up"] + process_info["down"]
                        process_list.append(process_info)
                except Exception:
                    continue

            current_time = time.time()
            inactive_cache_copy = dict(inactive_cache)
            for pid, (count, last_check) in inactive_cache_copy.items():
                remove_flag = False
                if current_time - last_check > 600:  # 超过 10 分钟
                    remove_flag = True
                else:  # 进程残留, pid被复用
                    try:
                        current_create = psutil.Process(pid).create_time()
                        exist_create = None
                        if pid in _system_task_state["last_process_cache"]:
                            exist_create = _system_task_state["last_process_cache"][pid][0]
                        elif pid in new_cache:
                            exist_create = new_cache[pid][0]
                        if exist_create and current_create != exist_create:
                            remove_flag = True  # pid被复用
                    except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                        remove_flag = True

                if remove_flag and pid in inactive_cache:
                    del inactive_cache[pid]

            _system_task_state["last_process_cache"] = new_cache
            _system_task_state["inactive_process_cache"] = inactive_cache
            return process_list

        except Exception:
            return []

    # 暂无用
    # def start_process_net_total(self):
    #     # 进程流量监控，如果文件：/www/server/panel/data/is_net_task.pl 或 /www/server/panel/data/control.conf不存在，则不监控进程流量
    #     if not (os.path.isfile(self.proc_net_service) and os.path.isfile(self.base_service)):
    #         return
    #
    #     def process_net_total():
    #         class_path = '{}/class'.format(BASE_PATH)
    #         if class_path not in sys.path:
    #             sys.path.insert(0, class_path)
    #         import process_task
    #         process_task.process_network_total().start()
    #
    #     import threading
    #     th = threading.Thread(target=process_net_total, daemon=True)
    #     th.start()
    def ensure_table(db_file: str) -> None:
        """表, 字段处理"""
        if not os.path.isfile(db_file):
            os.makedirs(os.path.dirname(db_file), exist_ok=True)
            open(db_file, 'w').close()
        conn = None
        cursor = None
        init_sql = '''
CREATE TABLE IF NOT EXISTS `cpuio` (
    `id` INTEGER PRIMARY KEY AUTOINCREMENT,
    `pro` INTEGER, `mem` INTEGER,
    `swap_percent` INTEGER, `swap_total` INTEGER, `swap_used` INTEGER, `swap_free` INTEGER,
    `addtime` INTEGER
);

CREATE TABLE IF NOT EXISTS `network` (
    `id` INTEGER PRIMARY KEY AUTOINCREMENT,
    `up` INTEGER, `down` INTEGER, `total_up` INTEGER, `total_down` INTEGER,
    `down_packets` INTEGER, `up_packets` INTEGER, `addtime` INTEGER
);

CREATE TABLE IF NOT EXISTS `diskio` (
    `id` INTEGER PRIMARY KEY AUTOINCREMENT,
    `read_count` INTEGER, `write_count` INTEGER,`read_bytes` INTEGER, `write_bytes` INTEGER,
    `read_time` INTEGER, `write_time` INTEGER, `addtime` INTEGER
);

CREATE TABLE IF NOT EXISTS `load_average` (
    `id` INTEGER PRIMARY KEY AUTOINCREMENT,
    `pro` REAL, `one` REAL, `five` REAL, `fifteen` REAL, `addtime` INTEGER
);

CREATE TABLE IF NOT EXISTS `process_top_list` (
    `id` INTEGER PRIMARY KEY AUTOINCREMENT,
    `cpu_top` REAL, `memory_top` REAL, `disk_top` REAL, `net_top` REAL, `all_top` REAL,
    `swap_top` REAL,
    `addtime` INTEGER
);

-- 索引
CREATE INDEX IF NOT EXISTS idx_cpuio_addtime ON cpuio (addtime);
CREATE INDEX IF NOT EXISTS idx_network_addtime ON network (addtime);
CREATE INDEX IF NOT EXISTS idx_diskio_addtime ON diskio (addtime);
CREATE INDEX IF NOT EXISTS idx_load_average_addtime ON load_average (addtime);
CREATE INDEX IF NOT EXISTS idx_process_top_list_addtime ON process_top_list (addtime);
'''
        try:
            conn = sqlite3.connect(db_file)
            try:
                conn.executescript(init_sql)
                conn.commit()
            except Exception as e:
                logger.error("Failed to initialize system.db : {}".format(e))

            # 检测cpuio表是否存在swap字段
            cursor = conn.cursor()
            try:
                cursor.execute(
                    "SELECT swap_total, swap_percent, swap_used, swap_free FROM cpuio ORDER BY id DESC LIMIT 1"
                )
            except sqlite3.OperationalError:
                # swap字段不存在
                alter_sql = '''
    ALTER TABLE cpuio ADD COLUMN swap_percent INTEGER DEFAULT 0;
    ALTER TABLE cpuio ADD COLUMN swap_total INTEGER DEFAULT 0;
    ALTER TABLE cpuio ADD COLUMN swap_used INTEGER DEFAULT 0;
    ALTER TABLE cpuio ADD COLUMN swap_free INTEGER DEFAULT 0;
    '''
                try:
                    conn.executescript(alter_sql)
                    conn.commit()
                except sqlite3.OperationalError:
                    pass

            # 检测process_top_list表是否存在swap_top字段
            try:
                cursor.execute("SELECT swap_top FROM process_top_list ORDER BY id DESC LIMIT 1")
            except sqlite3.OperationalError:
                try:
                    conn.execute("ALTER TABLE process_top_list ADD COLUMN swap_top REAL DEFAULT []")
                    conn.commit()
                except sqlite3.OperationalError:
                    pass
            _system_task_state["table_ensure"] = True
        except Exception as e:
            logger.error("Failed to connect to system.db : {}".format(e))
            _system_task_state["table_ensure"] = False
        finally:
            if cursor: cursor.close()
            if conn: conn.close()

    def clear_expire_data(conn: sqlite3.Connection) -> None:
        if not _system_task_state.get("last_clear_time"):
            return
        now = int(time.time())
        # 检查是否需要清理（每小时一次）
        if now - _system_task_state.get("last_clear_time", 0) < 3600:
            return
        cur = None
        try:
            cur = conn.cursor()
            deltime = now - (keep_days * 86400)
            cur.execute("DELETE FROM cpuio WHERE addtime < ?", (deltime,))
            cur.execute("DELETE FROM network WHERE addtime < ?", (deltime,))
            cur.execute("DELETE FROM diskio WHERE addtime < ?", (deltime,))
            cur.execute("DELETE FROM load_average WHERE addtime < ?", (deltime,))
            cur.execute("DELETE FROM process_top_list WHERE addtime < ?", (deltime,))
            conn.commit()
            _system_task_state["last_clear_time"] = now
        except:
            pass
        finally:
            if cur: cur.close()

    control_conf = f"{BASE_PATH}/data/control.conf"
    db_file = f"{BASE_PATH}/data/system.db"

    # 表结构检查
    if not _system_task_state["table_ensure"]:
        ensure_table(db_file)

    # 是否启用监控, 不存在时为不开启监控, 存在时为监控天数
    if not os.path.exists(control_conf):
        return

    try:
        keep_days = int(read_file(control_conf) or 30)
        if keep_days < 1:
            return
    except Exception:
        keep_days = 30
    conn = None
    cursor = None

    try:
        conn = sqlite3.connect(db_file, timeout=3)
        cursor = conn.cursor()
        cpu_used = get_cpu_percent_smooth()
        mem_used = get_mem_used_percent()
        swap_percent, swap_total, swap_used, swap_free = get_swap_used_percent()
        lpro, one, five, fifteen = get_load_average()
        network_io = get_network_io()
        disk_io = get_disk_io()
        process_list = get_process_list()
        proc_net_service = f"{BASE_PATH}/data/is_net_task.pl"
        addtime = int(time.time())

        # cpu, swap
        cursor.execute(
            "INSERT INTO cpuio (pro, mem, swap_percent, swap_total, swap_used, swap_free, addtime) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (cpu_used, mem_used, swap_percent, swap_total, swap_used, swap_free, addtime)
        )
        # load
        cursor.execute(
            "INSERT INTO load_average (pro, one, five, fifteen, addtime) VALUES (?, ?, ?, ?, ?)",
            (lpro, one, five, fifteen, addtime)
        )
        # network io
        if network_io:
            cursor.execute(
                "INSERT INTO network (up, down, total_up, total_down, down_packets, up_packets, addtime) VALUES (?, ?, ?, ?, ?, ?, ?)",
                (
                    network_io['up'], network_io['down'],
                    network_io['total_up'], network_io['total_down'],
                    json.dumps(network_io['down_packets']),
                    json.dumps(network_io['up_packets']),
                    addtime
                )
            )

        # disk io
        if disk_io:
            cursor.execute(
                "INSERT INTO diskio (read_count, write_count, read_bytes, write_bytes, read_time, write_time, addtime) VALUES (?, ?, ?, ?, ?, ?, ?)",
                (
                    disk_io['read_count'], disk_io['write_count'],
                    disk_io['read_bytes'], disk_io['write_bytes'],
                    disk_io['read_time'], disk_io['write_time'],
                    addtime
                )
            )

        # process top list
        if process_list:
            all_top_list = cut_top_list(
                process_list, 'cpu_percent', 'disk_total', 'memory', 'net_total', top_num=5
            )
            cpu_top_list = cut_top_list(process_list, 'cpu_percent', top_num=5)
            disk_top_list = cut_top_list(process_list, 'disk_total', top_num=5)
            memory_top_list = cut_top_list(process_list, 'memory', top_num=5)
            swap_top_list = cut_top_list(process_list, 'swap', top_num=5)
            # net_top_list = all_top_list

            if os.path.isfile(proc_net_service):  # 进程流量监控, 暂无用
                # net_top_list = top_lists['net_top']
                pass

            all_top = json.dumps([(
                p['cpu_percent'], p['disk_read'], p['disk_write'], p['memory'], p['up'], p['down'], p['pid'],
                xss_encode(p['name']), xss_encode(p['cmdline']), xss_encode(p['username']),
                p['create_time']
            ) for p in all_top_list])

            cpu_top = json.dumps([(
                p['cpu_percent'], p['pid'], xss_encode(p['name']), xss_encode(p['cmdline']),
                xss_encode(p['username']), p['create_time']
            ) for p in cpu_top_list])

            disk_top = json.dumps([(
                p['disk_total'], p['disk_read'], p['disk_write'], p['pid'], xss_encode(p['name']),
                xss_encode(p['cmdline']), xss_encode(p['username']), p['create_time']
            ) for p in disk_top_list])

            # net_top = json.dumps([(
            #     p['net_total'], p['up'], p['down'], p['connect_count'], p['up_package'] + p['down_package'],
            #     p['pid'], xss_encode(p['name']), xss_encode(p['cmdline']), xss_encode(p['username']),
            #     p['create_time']
            # ) for p in net_top_list])
            net_top = None

            memory_top = json.dumps([(
                p['memory'], p['pid'], xss_encode(p['name']), xss_encode(p['cmdline']),
                xss_encode(p['username']), p['create_time']
            ) for p in memory_top_list])

            swap_top = json.dumps([(
                p['swap'], p['pid'], xss_encode(p['name']), xss_encode(p['cmdline']),
                xss_encode(p['username']), p['create_time']
            ) for p in swap_top_list])

            cursor.execute(
                "INSERT INTO process_top_list (all_top, cpu_top, disk_top, net_top, memory_top, swap_top, addtime) VALUES (?, ?, ?, ?, ?, ?, ?)",
                (all_top, cpu_top, disk_top, net_top, memory_top, swap_top, addtime)
            )

        conn.commit()
        # every 1h check clear old data
        clear_expire_data(conn)
    except sqlite3.OperationalError as e:
        logger.error(f"SQLite OperationalError in systemTask: {e}")
        ensure_table(db_file)
        _system_task_state["table_ensure"] = False
    except Exception:
        logger.error(f"systemTask error: {traceback.format_exc()}")
    finally:
        if cursor: cursor.close()
        if conn: conn.close()
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


# 项目守护
def project_daemon_service():
    task_ExecShell("project_daemon_service")


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
    task_ExecShell("push_msg")


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


def parse_soft_name_of_version(name):
    """
        @name 获取软件名称和版本
        @param name<string> 软件名称
        @return tuple(string, string) 返回软件名称和版本
    """
    if name.find('Docker') != -1:
        return 'docker', '1.0'
    return_default = ('', '')
    l, r = name.find('['), name.find(']')
    if l == -1 or r == -1 or l > r:
        return return_default
    # 去除括号只保留括号中间的软件名称和版本
    if name[l + 1:r].count("-") == 0:
        return return_default
    soft_name, soft_version = name[l + 1:r].split('-')[:2]
    if soft_name == 'php':
        soft_version = soft_version.replace('.', '')
    return soft_name, soft_version


def check_install_status(name: str):
    """
    @name 检查软件是否安装成功
    @param name<string> 软件名称
    @return tuple(bool, string) 返回是否安装成功和安装信息
    """
    return_default = (1, 'Installation successful')
    try:
        # 获取安装检查配置
        install_config = json.loads(read_file("{}/config/install_check.json".format(BASE_PATH)))
    except:
        return return_default
    try:
        # 获取软件名称和版本
        soft_name, soft_version = parse_soft_name_of_version(name)
        if not soft_name or not soft_version:
            return return_default

        if soft_name not in install_config:
            return return_default

        if os.path.exists("{}/install/{}_not_support.pl".format(BASE_PATH, soft_name)):
            return 0, 'Not compatible with this system! Please click on the details to explain!'

        if os.path.exists("{}/install/{}_mem_kill.pl".format(BASE_PATH, soft_name)):
            return 0, 'Insufficient memory installation exception! Please click on the details to explain!'

        soft_config = install_config[soft_name]

        # 取计算机名
        def get_hostname():
            try:
                import socket
                return socket.gethostname()
            except:
                return 'localhost.localdomain'

        # 替换soft_config中所有变量
        def replace_all(dat: str):
            if not dat:
                return dat
            if dat.find('{') == -1:
                return dat
            # 替换安装路径, 替换版本号
            dat = dat.replace('{SetupPath}', '/www/server').replace('{Version}', soft_version)
            # 替换主机名
            if dat.find("{Host") != -1:
                host_name = get_hostname()
                host = host_name.split('.')[0]
                dat = dat.replace("{Hostname}", host_name)
                dat = dat.replace("{Host}", host)
            return dat

        # 检查文件是否存在
        if 'files_exists' in soft_config:
            for f_name in soft_config['files_exists']:
                filename = replace_all(f_name)
                if not os.path.exists(filename):
                    return 0, 'Installation failed, file does not exist:{}'.format(filename)

        # 检查pid文件是否有效
        if 'pid' in soft_config and soft_config['pid']:
            pid_file = replace_all(soft_config['pid'])
            if not os.path.exists(pid_file):
                return 0, 'Startup failed, PID file does not exist:{}'.format(pid_file)
            pid = read_file(pid_file)
            if not pid:
                return 0, 'Startup failed, PID file does not exist:{}'.format(pid_file)
            proc_file = '/proc/{}/cmdline'.format(pid.strip())
            if not os.path.exists(proc_file):
                return 0, 'Startup failed, PID file is empty: {}({}) process does not exist'.format(pid_file, pid)

        # 执行命令检查
        if 'cmd' in soft_config:
            for cmd in soft_config['cmd']:
                p = subprocess.Popen(
                    replace_all(cmd['exec']), shell=True,
                    stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
                )
                p.wait()
                res = p.stdout.read() + "\n" + p.stderr.read()
                if res.find(replace_all(cmd['success'])) == -1:
                    return 0, '[{}] Abnormal service startup status'.format(soft_name)
    except:
        pass

    return return_default


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

    # def TaskStart(value: dict, start: int = None, time_out: int = None):
    #     """执行安装任务, 并检测是否已经在执行或超时"""
    #     def is_time_out(pid: int) -> bool:
    #         res = int(time.time()) - start > time_out if time_out else False
    #         if res:
    #             try:
    #                 p = psutil.Process(pid)
    #                 child = p.children(recursive=True)
    #                 for c in child:
    #                     try: c.kill()
    #                     except: continue
    #                 p.kill()
    #             except Exception: pass
    #         return res
    #
    #     start = int(time.time()) if not start else start
    #     try:
    #         output, _ = exec_shell(f"pgrep -f \"{value['execstr'] + '&>' + exlogPath}\"")
    #         pids = output.strip().split()
    #         if pids:
    #             target_pid = int(pids[0])
    #             sql.table('tasks').where("id=?", (value['id'],)).save('status', (Running,))
    #             while not is_time_out(target_pid):
    #                 try:
    #                     os.kill(target_pid, 0)
    #                     time.sleep(1)  # 残留阻塞
    #                 except ProcessLookupError: break
    #                 except Exception: break
    #             if is_time_out(target_pid):
    #                 raise Exception
    #         raise Exception
    #     except Exception:
    #         sql.table('tasks').where("id=?", (value['id'],)).save('status,start', (Running, start))
    #         ExecShell(value['execstr'])

    tip_file = "/dev/shm/.panelTask.pl"
    panel_log_path = "/www/server/panel/logs/installed/"
    if not os.path.exists(panel_log_path):
        os.mkdir(panel_log_path)
        os.chmod(panel_log_path, 0o600)

    Waitting = "0"  # 等待
    Running = "-1"  # 执行中
    Finished = "1"  # 完成
    try:
        if os.path.exists(isTask):
            with db.Sql() as sql:
                # 检测task表是否存在install_status,message字段
                field = 'id,type,execstr,name,install_status,message'
                check_result = sql.table('tasks').order("id desc").field(field).select()
                if type(check_result) == str:
                    sql.table('tasks').execute("ALTER TABLE 'tasks' ADD 'install_status' INTEGER DEFAULT 1", ())
                    sql.table('tasks').execute("ALTER TABLE 'tasks' ADD 'message' TEXT DEFAULT ''", ())

                sql.table('tasks').where("status=?", (Running,)).setField('status', Waitting)
                taskArr = sql.table('tasks').where("status=?", (Waitting,)).field('id,type,execstr,name').order(
                    "id asc"
                ).select()
                for value in taskArr:
                    if value['type'] != 'execshell':
                        continue
                    if not sql.table('tasks').where("id=?", (value['id'],)).count():
                        write_file(tip_file, str(int(time.time())))
                        continue

                    start = int(time.time())
                    # TaskStart(value, start=start, time_out=3600)
                    sql.table('tasks').where("id=?", (value['id'],)).save('status,start', (Running, start))
                    ExecShell(value['execstr'])

                    # 保存安装日志
                    target_log_file = '{}/task_{}.log'.format(panel_log_path, value['id'])
                    shutil.copy(exlogPath, target_log_file)
                    # 检查软件是否安装成功
                    end = int(time.time())
                    try:
                        install_status, install_msg = check_install_status(value['name'])
                    except Exception:
                        install_status = 1
                        install_msg = ""

                    sql.table('tasks').where("id=?", (value['id'],)).save(
                        'status,end,install_status,message',
                        (Finished, end, install_status, install_msg)
                    )
                    if sql.table('tasks').where("status=?", (Waitting,)).count() < 1:
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
    {"func": systemTask, "interval": 60, "is_core": True},  # 每1分钟系统监控任务
    {"func": project_daemon_service, "interval": 120, "is_core": True},  # 每120秒项目守护

    # ================================ 分割线 ===============================
    # <普通任务>
    # func 函数, interval 间隔时间秒s, 排队复用线程 (打印请用logger, 日志路径 .../logs/task.log)
    {"func": push_msg, "interval": 60},  # 每1分钟面板推送消息
    {"func": breaking_through, "interval": 60},  # 每分钟防爆破计划任务

    {"func": multi_web_server_daemon, "interval": 300},  # 每5分钟多服务守护任务
    {"func": check502Task, "interval": 60 * 10},  # 每10分钟 502检查(夹杂若干任务)
    {"func": check_site_monitor, "interval": 60 * 10},  # 每10分钟检查站点安装监控
    {"func": node_monitor, "interval": 60},  # 每1分钟节点监控任务
    {"func": node_monitor_check, "interval": 60 * 60 * 24 * 30},  # 每月节点监控检测任务
    {"func": update_waf_config, "interval": 60 * 20},  # 每隔20分钟更新一次waf报表数据
    {"func": update_monitor_requests, "interval": 60 * 20},  # 每隔20分钟更新一次网站报表数据

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
    sb = SimpleBrain(cpu_max=20.0, workers=max_workers)
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
