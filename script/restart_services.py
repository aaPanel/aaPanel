# coding: utf-8
import json
import os
import socket
import subprocess
import sys
import time
from functools import wraps, partial
from typing import Optional, Dict, Callable

import fcntl

os.chdir("/www/server/panel")
sys.path.insert(0, "class/")
sys.path.insert(0, "class_v2/")
from public import readFile

SETUP_PATH = "/www/server"
DATA_PATH = os.path.join(SETUP_PATH, "panel/data")
PLUGINS_PATH = os.path.join(SETUP_PATH, "panel/plugin")

DAEMON_SERVICE = os.path.join(DATA_PATH, "daemon_service.pl")
DAEMON_SERVICE_LOCK = os.path.join(DATA_PATH, "daemon_service_lock.pl")
DAEMON_RESTART_RECORD = os.path.join(DATA_PATH, "daemon_restart_record.pl")
MANUAL_FLAG = os.path.join(SETUP_PATH, "panel/data/mod_push_data", "manual_flag.pl")


def run_command(cmd, timeout=5) -> str:
    try:
        result = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            timeout=timeout,
            check=False
        )
        output = result.stdout.strip()
        return output if output else ""
    except subprocess.TimeoutExpired as t:
        write_logs(f"Command execution timed out: {cmd}, error: {t}")
        return ""
    except Exception as e:
        write_logs(f"Command execution failed: {cmd}, error: {e}")
        return ""


def service_shop_name(services_name: str) -> str:
    # 对应商店名字
    shop_name = {
        "postfix": "mail_sys",
        "pgsql": "pgsql_manager",
        "pure-ftpd": "pureftpd",

        "php-fpm-52": "php-5.2",
        "php-fpm-53": "php-5.3",
        "php-fpm-54": "php-5.4",
        "php-fpm-55": "php-5.5",
        "php-fpm-56": "php-5.6",
        "php-fpm-70": "php-7.0",
        "php-fpm-71": "php-7.1",
        "php-fpm-72": "php-7.2",
        "php-fpm-73": "php-7.3",
        "php-fpm-74": "php-7.4",
        "php-fpm-80": "php-8.0",
        "php-fpm-81": "php-8.1",
        "php-fpm-82": "php-8.2",
        "php-fpm-83": "php-8.3",
        "php-fpm-84": "php-8.4",
        "php-fpm-85": "php-8.5",
    }
    return shop_name.get(services_name, services_name)


def pretty_title(services_name: str) -> str:
    title = {
        "apache": "Apache",
        "nginx": "Nginx",
        "openlitespeed": "OpenLiteSpeed",
        "redis": "Redis",
        "mysql": "MySQL/MariaDB",
        "mongodb": "MongoDB",
        "pgsql": "PostgreSQL",
        "pure-ftpd": "Pure-FTPd",
        "memcached": "Memcached",
        "ssh": "SSH",
        "postfix": "Postfix",
        "pdns": "PowerDNS",

        # PHP-FPM
        "php-fpm-52": "PHP 5.2 FPM",
        "php-fpm-53": "PHP 5.3 FPM",
        "php-fpm-54": "PHP 5.4 FPM",
        "php-fpm-55": "PHP 5.5 FPM",
        "php-fpm-56": "PHP 5.6 FPM",
        "php-fpm-70": "PHP 7.0 FPM",
        "php-fpm-71": "PHP 7.1 FPM",
        "php-fpm-72": "PHP 7.2 FPM",
        "php-fpm-73": "PHP 7.3 FPM",
        "php-fpm-74": "PHP 7.4 FPM",
        "php-fpm-80": "PHP 8.0 FPM",
        "php-fpm-81": "PHP 8.1 FPM",
        "php-fpm-82": "PHP 8.2 FPM",
        "php-fpm-83": "PHP 8.3 FPM",
        "php-fpm-84": "PHP 8.4 FPM",
        "php-fpm-85": "PHP 8.5 FPM",

        # plugins
        "btwaf": "aaPanel WAF",
        "fail2ban": "Fail2Ban",
    }
    return title.get(services_name, services_name)


# =======================================================
def ssh_ver() -> str:
    version_info = run_command(["ssh", "-V"])
    if version_info and "OpenSSH" in version_info:
        return version_info.split(",")[0]
    return ""


def postfix_ver() -> str:
    # mail_version = x.x.x
    output = run_command(["/usr/sbin/postconf", "mail_version"])
    if output and "=" in output:
        return output.split("=")[-1].strip()
    return ""


def pgsql_pid() -> str:
    pid_str = run_command(["pgrep", "-o", "postgres"])
    if pid_str and pid_str.isdigit():
        return pid_str
    return ""


def pgsql_ver() -> str:
    # psql (PostgreSQL) 18.0
    output = run_command([f"{SETUP_PATH}/pgsql/bin/psql", "--version"])
    if output:
        from re import search
        match = search(r"(\d+\.\d+(\.\d+)?)", output)
        if match:
            return match.group(1)

    org_file = f"{SETUP_PATH}/pgsql/data/PG_VERSION",
    if os.path.exists(str(org_file)):
        try:
            with open(str(org_file), "r") as f:
                version = f.read().strip()
            return version
        except:
            return ""
    return ""


def pdns_pid() -> str:
    pid_str = run_command(["pgrep", "-x", "pdns_server"])
    if pid_str and pid_str.isdigit():
        return pid_str
    return ""


def pdns_ver() -> str:
    # PowerDNS Authoritative Server x.x.x
    output = run_command(["pdns_server", "--version"])
    if not output:
        return ""
    from re import search
    match = search(r"(\d+\.\d+\.\d+)", output)
    if match:
        return match.group(1)

    if "PowerDNS" in output:
        return output.split()[-1]
    return ""


def waf_pid() -> str:
    pid_str = run_command(["pgrep", "-x", "BT-WAF"])
    if pid_str and pid_str.isdigit():
        return pid_str
    return ""


def pluign_ver(plugin_name: str) -> str:
    info = f"{PLUGINS_PATH}/{plugin_name}/info.json"
    if not os.path.exists(info):
        return ""
    try:
        with open(info, "r") as f:
            json_data = json.load(f)
        ret = json_data.get("versions", "")
        return ret
    except:
        pass
    return ""


SERVICES_MAP = {
    # ========================= core base =============================
    "panel": (
        "BT-Panel", f"{SETUP_PATH}/panel/logs/panel.pid", f"{SETUP_PATH}/panel/init.sh",
        f"{SETUP_PATH}/nginx/version.pl",
    ),
    "apache": (
        "httpd", f"{SETUP_PATH}/apache/logs/httpd.pid", "/etc/init.d/httpd",
        f"{SETUP_PATH}/apache/version.pl",
    ),
    "nginx": (
        "nginx", f"{SETUP_PATH}/nginx/logs/nginx.pid", "/etc/init.d/nginx",
        f"{SETUP_PATH}/nginx/version.pl",
    ),
    "openlitespeed": (
        "litespeed", "/tmp/lshttpd/lsphp.sock", "/usr/local/lsws/bin/lswsctrl",
        "/usr/local/lsws/VERSION",
    ),
    "redis": (
        "redis-server", f"{SETUP_PATH}/redis/redis.pid", "/etc/init.d/redis",
        f"{SETUP_PATH}/redis/version.pl",
    ),
    "mysql": (
        "mysqld", "/tmp/mysql.sock", "/etc/init.d/mysqld",
        f"{SETUP_PATH}/mysql/version.pl",
    ),
    "mongodb": (
        "mongod", f"{SETUP_PATH}/mongodb/log/configsvr.pid", "/etc/init.d/mongodb",
        f"{SETUP_PATH}/mongodb/version.pl",
    ),
    "pgsql": (
        "postgres", pgsql_pid, "/etc/init.d/pgsql",
        pgsql_ver,
    ),
    "pure-ftpd": (
        "pure-ftpd", "/var/run/pure-ftpd.pid", "/etc/init.d/pure-ftpd",
        f"{SETUP_PATH}/pure-ftpd/version.pl",
    ),
    "memcached": (
        "memcached", "/var/run/memcached.pid", "/etc/init.d/memcached",
        "/usr/local/memcached/version_check.pl",
    ),
    "ssh": (
        "sshd", "/var/run/sshd.pid", "/etc/init.d/ssh",
        ssh_ver,
    ),
    "postfix": (
        "master", "/var/spool/postfix/pid/master.pid", "/etc/init.d/postfix",
        postfix_ver,
    ),
    "pdns": (
        # "pdns_server", pdns_pid, "/usr/sbin/pdns_server",
        "pdns_server", pdns_pid, "/www/server/panel/class_v2/ssl_dnsV2/aadns.pl",
        pdns_ver,
    ),

    # ======================== PHP-FPM ============================
    "php-fpm-52": ("php-fpm", f"{SETUP_PATH}/php/52/var/run/php-fpm.pid", "/etc/init.d/php-fpm-52",
                   f"{SETUP_PATH}/php/52/version.pl"),
    "php-fpm-53": ("php-fpm", f"{SETUP_PATH}/php/53/var/run/php-fpm.pid", "/etc/init.d/php-fpm-53",
                   f"{SETUP_PATH}/php/53/version.pl"),
    "php-fpm-54": ("php-fpm", f"{SETUP_PATH}/php/54/var/run/php-fpm.pid", "/etc/init.d/php-fpm-54",
                   f"{SETUP_PATH}/php/54/version.pl"),
    "php-fpm-55": ("php-fpm", f"{SETUP_PATH}/php/55/var/run/php-fpm.pid", "/etc/init.d/php-fpm-55",
                   f"{SETUP_PATH}/php/55/version.pl"),
    "php-fpm-56": ("php-fpm", f"{SETUP_PATH}/php/56/var/run/php-fpm.pid", "/etc/init.d/php-fpm-56",
                   f"{SETUP_PATH}/php/56/version.pl"),
    "php-fpm-70": ("php-fpm", f"{SETUP_PATH}/php/70/var/run/php-fpm.pid", "/etc/init.d/php-fpm-70",
                   f"{SETUP_PATH}/php/70/version.pl"),
    "php-fpm-71": ("php-fpm", f"{SETUP_PATH}/php/71/var/run/php-fpm.pid", "/etc/init.d/php-fpm-71",
                   f"{SETUP_PATH}/php/71/version.pl"),
    "php-fpm-72": ("php-fpm", f"{SETUP_PATH}/php/72/var/run/php-fpm.pid", "/etc/init.d/php-fpm-72",
                   f"{SETUP_PATH}/php/72/version.pl"),
    "php-fpm-73": ("php-fpm", f"{SETUP_PATH}/php/73/var/run/php-fpm.pid", "/etc/init.d/php-fpm-73",
                   f"{SETUP_PATH}/php/73/version.pl"),
    "php-fpm-74": ("php-fpm", f"{SETUP_PATH}/php/74/var/run/php-fpm.pid", "/etc/init.d/php-fpm-74",
                   f"{SETUP_PATH}/php/74/version.pl"),
    "php-fpm-80": ("php-fpm", f"{SETUP_PATH}/php/80/var/run/php-fpm.pid", "/etc/init.d/php-fpm-80",
                   f"{SETUP_PATH}/php/80/version.pl"),
    "php-fpm-81": ("php-fpm", f"{SETUP_PATH}/php/81/var/run/php-fpm.pid", "/etc/init.d/php-fpm-81",
                   f"{SETUP_PATH}/php/81/version.pl"),
    "php-fpm-82": ("php-fpm", f"{SETUP_PATH}/php/82/var/run/php-fpm.pid", "/etc/init.d/php-fpm-82",
                   f"{SETUP_PATH}/php/82/version.pl"),
    "php-fpm-83": ("php-fpm", f"{SETUP_PATH}/php/83/var/run/php-fpm.pid", "/etc/init.d/php-fpm-83",
                   f"{SETUP_PATH}/php/83/version.pl"),
    "php-fpm-84": ("php-fpm", f"{SETUP_PATH}/php/84/var/run/php-fpm.pid", "/etc/init.d/php-fpm-84",
                   f"{SETUP_PATH}/php/84/version_check.pl"),
    "php-fpm-85": ("php-fpm", f"{SETUP_PATH}/php/85/var/run/php-fpm.pid", "/etc/init.d/php-fpm-85",
                   f"{SETUP_PATH}/php/85/version_check.pl"),

    # ======================== plugins ============================
    # nginx : btwaf
    # apache: btwaf_httpd
    "btwaf": (
        # "BT-WAF", f"{PLUGINS_PATH}/btwaf/BT-WAF.pid", f"/etc/init.d/btwaf",
        "BT-WAF", waf_pid, f"/etc/init.d/btwaf",
        partial(pluign_ver, "btwaf"),
    ),
    "fail2ban": (
        "fail2ban-server", f"{PLUGINS_PATH}/fail2ban/fail2ban.pid", "/etc/init.d/fail2ban",
        partial(pluign_ver, "fail2ban"),
    ),
}


# 日志
def write_logs(msg: str):
    try:
        from public import M
        t = time.strftime('%Y-%m-%d %X', time.localtime())
        M("logs").add("uid,username,type,log,addtime", (1, "system", "Service Daemon", msg, t))
    except:
        pass


# 手动干预
def manual_flag(server_name: str = None, open_: str = None) -> Optional[dict]:
    if not server_name:  # only read
        return DaemonManager.manual_safe_read()
    # 人为干预
    if open_ in ["start", "restart"]:  # 激活服务检查
        return DaemonManager.active_daemon(server_name)
    elif open_ == "stop":  # 跳过服务检查
        return DaemonManager.skip_daemon(server_name)
    return DaemonManager.manual_safe_read()


# 管理服务助手
class ServicesHelper:
    def __init__(self, nick_name: str = None):
        self.nick_name = nick_name
        self._serviced = None
        self._pid_source = None
        self._bash = None
        self._ver_source = None
        self._pid_cache = None
        self._ver_cache = None
        self._install_cache = None
        self._info_inited = False

    def __check_pid_process(self, pid: int) -> bool:
        try:
            # 是否活跃
            with open(f"/proc/{pid}/stat", "r") as f:
                if f.read().split()[2] == "Z":
                    return False  # 僵尸进程
            # 进程是否名字匹配
            with open(f"/proc/{pid}/comm", "r") as f:
                proc_name = f.read().strip()
            return proc_name == self.nick_name or proc_name == self._serviced
        except (FileNotFoundError, IndexError):
            return False
        except Exception:
            return False

    def _init_info(self) -> None:
        if self._info_inited:
            return
        if not self.nick_name or not isinstance(self.nick_name, str):
            self._info_inited = True
            return

        map_info = SERVICES_MAP.get(self.nick_name)
        if map_info:
            self._serviced, self._pid_source, self._bash, self._ver_source = map_info

        self._info_inited = True

    @property
    def pid(self):
        """返回pid文件路径或pid值"""
        if self._pid_cache is None:
            self._init_info()
            if isinstance(self._pid_source, Callable):
                try:
                    pid_val = self._pid_source()
                    self._pid_cache = int(pid_val) if pid_val and pid_val.isdigit() else pid_val
                except Exception:
                    self._pid_cache = self._pid_source
            else:
                self._pid_cache = self._pid_source
        return self._pid_cache

    @property
    def version(self) -> str:
        """返回服务版本号"""
        if self._ver_cache is None:
            self._init_info()
            if isinstance(self._ver_source, Callable):
                try:
                    self._ver_cache = self._ver_source()
                except:
                    self._ver_cache = ""
            elif isinstance(self._ver_source, str) and os.path.exists(self._ver_source):
                try:
                    with open(self._ver_source, "r") as f:
                        self._ver_cache = f.read().strip()
                except:
                    self._ver_cache = ""
            else:
                self._ver_cache = ""

        return str(self._ver_cache).strip()

    @property
    def is_install(self) -> bool:
        """判断是否安装"""
        if self._install_cache is not None:
            return self._install_cache

        self._init_info()
        self._install_cache = False
        # waf特殊处理
        if self.nick_name == "btwaf":
            if os.path.exists(f"{PLUGINS_PATH}/btwaf"):
                self._install_cache = True
            return self._install_cache
        # postfix特殊处理
        if self.nick_name == "postfix":
            if os.path.exists(f"{PLUGINS_PATH}/mail_sys"):
                self._install_cache = True
            return self._install_cache

        if any([
            self._serviced and os.path.exists(f"/etc/init.d/{self._serviced}"),
            self.nick_name and os.path.exists(f"/etc/init.d/{self.nick_name}"),
            self._bash and os.path.exists(self._bash),
        ]):
            self._install_cache = True

        return self._install_cache

    @property
    def shop_name(self) -> str:
        return service_shop_name(self.nick_name)

    @property
    def pretty_title(self) -> str:
        return pretty_title(self.nick_name)

    @property
    def is_running(self) -> bool:
        """
        判断进程是否存活
        pid: 进程pid文件 str 或 int
        serviced: 进程服务名称
        nick_name: 进程别名
        """
        if not self.is_install:
            return False

        if not self.pid:
            return False

        if isinstance(self.pid, int):
            return self.__check_pid_process(self.pid)

        if isinstance(self.pid, str):
            if not os.path.exists(self.pid):
                return False
            if self.pid.endswith(".pid"):
                try:
                    with open(self.pid, "r") as f:
                        temp_pid = int(f.read().strip())
                    return self.__check_pid_process(temp_pid)
                except (ValueError, FileNotFoundError):
                    return False
                except Exception:
                    return False
            elif self.pid.endswith(".sock"):
                try:
                    with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as s:
                        s.settimeout(0.1)
                        s.connect(self.pid)
                    return True
                except (socket.timeout, ConnectionRefusedError, FileNotFoundError):
                    return False
                except Exception:
                    return False
        # not str and not int
        return False

    def script(self, act: str) -> None:
        if not self.is_install or act not in ["start", "stop", "restart", "status"]:
            return
        try:
            # "try to {act} [{self.nick_name}]..."
            self._init_info()
            bash_path = self._bash if self._bash else f"/etc/init.d/{self._serviced}"

            if isinstance(self.pid, str) and (
                    self.pid.endswith(".sock") or self.pid.endswith(".pid")
            ):
                try:
                    os.remove(self.pid)
                except:
                    pass

            if self.nick_name == "panel":
                if not os.path.exists(f"{SETUP_PATH}/panel/init.sh"):
                    from public import get_url
                    os.system(f"curl -k {get_url()}/install/update_7.x_en.sh|bash &")
                cmd = ["bash", bash_path, act]

            elif self.nick_name == "pdns":
                cmd = ["systemctl", act, "pdns"]
            else:
                cmd = [bash_path, act]

            result = run_command(cmd)
            if not result and act in ["start", "restart"]:
                write_logs(f"Failed to {act} {self.nick_name}, error: command returned no output.")

        except Exception as e:
            print(str(e))
            write_logs(f"Failed to {act} {self.nick_name}, error: {e}")


# 守护服务管理
class DaemonManager:
    @classmethod
    def __ensure(cls):
        if not os.path.exists(DAEMON_SERVICE_LOCK):
            with open(DAEMON_SERVICE_LOCK, "w") as _:
                pass
        if not os.path.exists(DAEMON_RESTART_RECORD):
            with open(DAEMON_RESTART_RECORD, "w") as fm:
                fm.write(json.dumps({}))
        os.makedirs(os.path.dirname(MANUAL_FLAG), exist_ok=True)
        if not os.path.exists(MANUAL_FLAG):
            with open(MANUAL_FLAG, "w") as fm:
                fm.write(json.dumps({}))
        if not os.path.exists(DAEMON_SERVICE):
            with open(DAEMON_SERVICE, "w") as fm:
                fm.write(json.dumps([]))

    @staticmethod
    def read_lock(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            DaemonManager.__ensure()
            with open(DAEMON_SERVICE_LOCK, "r") as lock_file:
                fcntl.flock(lock_file, fcntl.LOCK_SH)
                try:
                    result = func(*args, **kwargs)
                finally:
                    fcntl.flock(lock_file, fcntl.LOCK_UN)
                return result

        return wrapper

    @staticmethod
    def write_lock(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            DaemonManager.__ensure()
            with open(DAEMON_SERVICE_LOCK, "r+") as lock_file:
                fcntl.flock(lock_file, fcntl.LOCK_EX)
                try:
                    result = func(*args, **kwargs)
                finally:
                    fcntl.flock(lock_file, fcntl.LOCK_UN)
                return result

        return wrapper

    @staticmethod
    @write_lock
    def operate_daemon(service_name: str, flag: int = 0) -> list:
        """
        flag: 0 add, 1 del
        """
        with open(DAEMON_SERVICE, "r+") as f:
            try:
                service = json.load(f)
            except json.JSONDecodeError:
                service = []
            if flag == 0:
                service.append(service_name)
            elif flag == 1:
                service = [x for x in service if x != service_name]
            service = list(set(service))
            f.seek(0)
            # noinspection PyTypeChecker
            json.dump(service, f)
            f.truncate()
            return service

    @staticmethod
    @write_lock
    def operate_manual_flag(service_name: str, flag: int = 0) -> dict:
        """
        flag: 0 normal, 1 manual closed
        """
        with open(MANUAL_FLAG, "r+") as f:
            try:
                service = json.load(f)
            except json.JSONDecodeError:
                service = {}
            service[service_name] = flag
            f.seek(0)
            # noinspection PyTypeChecker
            json.dump(service, f)
            f.truncate()
            return service

    @staticmethod
    def remove_daemon(service_name: str) -> list:
        """移除守护进程服务"""
        return DaemonManager.operate_daemon(service_name, 1)

    @staticmethod
    def add_daemon(service_name: str) -> list:
        """添加守护进程服务"""
        return DaemonManager.operate_daemon(service_name, 0)

    @staticmethod
    def skip_daemon(service_name: str) -> dict:
        """跳过服务检查"""
        return DaemonManager.operate_manual_flag(service_name, 1)

    @staticmethod
    def active_daemon(service_name: str) -> dict:
        """激活服务检查"""
        return DaemonManager.operate_manual_flag(service_name, 0)

    @staticmethod
    @read_lock
    def safe_read():
        """服务守护进程服务列表"""
        try:
            res = readFile(DAEMON_SERVICE)
            return json.loads(res) if res else []
        except:
            return []

    @staticmethod
    @read_lock
    def manual_safe_read():
        """手动干预服务字典, 0: 需要干预, 1: 被手动关闭的"""
        try:
            manual = readFile(MANUAL_FLAG)
            return json.loads(manual) if manual else {}
        except:
            return {}

    @staticmethod
    def update_restart_record(service_name: str, max_count: int) -> bool:
        try:
            with open(DAEMON_RESTART_RECORD, "r+") as f:
                fcntl.flock(f, fcntl.LOCK_EX)
                try:
                    record = json.load(f)
                except json.JSONDecodeError:
                    record = {}

                count = record.get(service_name, 0)
                if count >= max_count:
                    return True

                record[service_name] = count + 1
                f.seek(0)
                json.dump(record, f)
                f.truncate()
                return False
        except Exception:
            return True

    @staticmethod
    def safe_read_restart_record() -> Dict[str, int]:
        try:
            with open(DAEMON_RESTART_RECORD, "r") as f:
                fcntl.flock(f, fcntl.LOCK_SH)
                record = json.load(f)
        except Exception:
            record = {}
        return record


# 服务守护
class RestartServices:
    COUNT = 30

    @staticmethod
    def __keep_flag_right(manual_info: dict) -> None:
        try:
            with open(MANUAL_FLAG, "r+") as f:
                try:
                    fcntl.flock(f.fileno(), fcntl.LOCK_EX)
                    f.seek(0)
                    # noinspection PyTypeChecker
                    json.dump(manual_info, f)
                    f.truncate()
                except:
                    print("Error writing manual flag file")
                finally:
                    fcntl.flock(f.fileno(), fcntl.LOCK_UN)
        except Exception as e:
            print("Error keep_flag_right:", e)

    def _overhead(self, nick_name) -> bool:
        return DaemonManager.update_restart_record(
            nick_name, self.COUNT
        )

    @DaemonManager.read_lock
    def main(self):
        manaul = readFile(MANUAL_FLAG)
        services = readFile(DAEMON_SERVICE)
        try:
            manual_info = json.loads(manaul) if manaul else {}
            check_list = json.loads(services) if services else []
            check_list = ["panel"] + check_list  # panel 强制守护
        except Exception:
            manual_info = {}
            check_list = ["panel"]

        record = DaemonManager.safe_read_restart_record()
        for service in [
            x for x in list(set(check_list)) if record.get(x, 0) < self.COUNT
        ]:
            obj = ServicesHelper(service)
            if not obj.is_install:
                continue

            if not obj.is_running:
                if int(manual_info.get(obj.nick_name, 0)) == 1:
                    # service closed maually, skip
                    continue
                if obj.nick_name != "panel":
                    write_logs(f"Service [ {obj.nick_name} ] is Not Running, Try to start it...")

                if not self._overhead(obj.nick_name):
                    obj.script("start")
                    time.sleep(3)
                    if not obj.is_running:
                        if not self._overhead(obj.nick_name):
                            obj.script("restart")

            if manual_info.get(obj.nick_name) == 1:
                # service is running, fix the wrong flag
                manual_info[obj.nick_name] = 0
                # under lock file read lock
                self.__keep_flag_right(manual_info)


def first_time_installed(data: dict) -> None:
    """
    首次安装服务启动守护进程服务
    """
    # todo 虽然支持, 但是守护目前不干预, 前端没开放
    exculde = [
        "pgsql", "fail2ban", "btwaf", "ssh", "pdns", "php-fpm", "memcached"
    ]
    if not data:
        return
    try:
        for service in SERVICES_MAP.keys():  # support service
            if service in exculde:
                continue
            if "php-fpm" in service:
                continue
            pl_name = f"{DATA_PATH}/first_installed_flag_{service}.pl"
            if data.get(service):  # panel installed
                setup = data[service].get("setup", False)
                if setup is False and os.path.exists(pl_name):
                    os.remove(pl_name)
                elif setup is True and not os.path.exists(pl_name):
                    DaemonManager.add_daemon(service)
                    with open(pl_name, "w") as f:
                        f.write("1")
                else:
                    pass
    except:
        pass


if __name__ == "__main__":
    pass
