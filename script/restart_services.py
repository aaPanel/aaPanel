# coding: utf-8
import json
import os
import subprocess
import sys
import time
from functools import wraps
from typing import Optional, Dict

import fcntl

os.chdir("/www/server/panel")
sys.path.insert(0, "class/")
sys.path.insert(0, "class_v2/")
import public

SETUP_PATH = public.get_setup_path()
DATA_PATH = os.path.join(SETUP_PATH, "panel/data")

DAEMON_SERVICE = os.path.join(DATA_PATH, "daemon_service.pl")
DAEMON_SERVICE_LOCK = os.path.join(DATA_PATH, "daemon_service_lock.pl")
MANUAL_FLAG = os.path.join(public.get_panel_path(), "data/mod_push_data", "manual_flag.pl")

SERVICES_MAP = {
    "apache": (
        "httpd", f"{SETUP_PATH}/apache/logs/httpd.pid", "/etc/init.d/httpd"
    ),
    "nginx": (
        "nginx", f"{SETUP_PATH}/nginx/logs/nginx.pid", "/etc/init.d/nginx"
    ),
    "redis": (
        "redis", f"{SETUP_PATH}/redis/redis.pid", "/etc/init.d/redis"
    ),
    "mysql": (
        "mysqld", "/tmp/mysql.sock", "/etc/init.d/mysqld"
    ),
    "mongodb": (
        "mongod", f"{SETUP_PATH}/mongodb/log/configsvr.pid", "/etc/init.d/mongodb"
    ),
    "pure-ftpd": (
        "pure-ftpd", "/var/run/pure-ftpd.pid", "/etc/init.d/pure-ftpd"
    ),
    "memcached": (
        "memcached", "/var/run/memcached.pid", "/etc/init.d/memcached"
    ),
    "openlitespeed": (
        "litespeed", "/tmp/lshttpd/lsphp.sock", "/usr/local/lsws/bin/lswsctrl"
    )
}


def manual_flag(server_name: str = None, open_: str = None) -> Optional[dict]:
    if not server_name:  # only read
        return DaemonManager.manual_safe_read()
    # 人为干预
    if open_ in ["start", "restart"]:  # 激活服务检查
        return DaemonManager.active_daemon(server_name)
    elif open_ == "stop":  # 跳过服务检查
        return DaemonManager.skip_daemon(server_name)
    return DaemonManager.manual_safe_read()


class DaemonManager:
    @classmethod
    def __ensure(cls):
        if not os.path.exists(DAEMON_SERVICE_LOCK):
            with open(DAEMON_SERVICE_LOCK, "w") as _:
                pass
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
            res = public.readFile(DAEMON_SERVICE)
            return json.loads(res) if res else []
        except:
            return []

    @staticmethod
    @read_lock
    def manual_safe_read():
        """手动干预服务字典, 0: 需要干预, 1: 被手动关闭的"""
        try:
            manual = public.readFile(MANUAL_FLAG)
            return json.loads(manual) if manual else {}
        except:
            return {}


class RestartServices:
    COUNT = 30
    RECORD: Dict[str, int] = {}

    def __init__(self):
        self.nick_name = None
        self.serviced = None
        self.pid_file = None
        self.bash = None

    def __keep_flag_right(self, manual_info: dict) -> None:
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

    def _overhead(self) -> bool:
        if self.nick_name not in self.RECORD:
            self.RECORD[self.nick_name] = 0
            return True

        if self.RECORD[self.nick_name] >= self.COUNT:
            return False

        self.RECORD[self.nick_name] += 1
        return True

    def _script(self, act: str) -> None:
        try:
            if act not in ["start", "stop", "restart", "status"]:
                return
            # "try to {act} [{self.nick_name}]..."
            bash_path = self.bash if self.bash else f"/etc/init.d/{self.serviced}"
            if self.pid_file.endswith(".sock"):
                try:
                    os.remove(self.pid_file)
                except:
                    pass
            result = subprocess.run(
                [bash_path, act],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=10,
            )
            if result.returncode != 0:
                public.WriteLog(
                    "Service Daemon", f"Failed to {act} {self.nick_name}, error: {result.stderr.strip()}"
                )
                # todo 暂时解决公共安装脚本无法启动mongodb的问题
                mg_path = f"{SETUP_PATH}/mongodb"
                if act == "restart" and self.nick_name == "mongodb" and os.path.exists(f"{mg_path}/bin/mongod"):
                    try:
                        public.ExecShell(f"rm -f {mg_path}/log/configsvr.pid")
                        public.ExecShell("rm -f /tmp/mongodb-27017.sock")
                        public.ExecShell(f"chown -R mongo:mongo {mg_path}")
                        public.ExecShell(f"sudo -u mongo {mg_path}/bin/mongod -f {mg_path}/config.conf")
                    except:
                        pass

        except subprocess.TimeoutExpired as t:
            public.WriteLog(
                "Service Daemon", f"Failed to {act} {self.nick_name}, error: time out, {t}"
            )
        except Exception as e:
            print(str(e))
            public.WriteLog(
                "Service Daemon", f"Failed to {act} {self.nick_name}, error: {e}"
            )

    def is_support(self) -> bool:
        try:
            map_info = SERVICES_MAP.get(self.nick_name)
            if not map_info:
                return False

            self.serviced, self.pid_file, self.bash = map_info

            if not all([self.serviced, self.pid_file, self.bash]):
                return False
            return True
        except:
            return False

    def is_install_service(self) -> bool:
        if self.serviced == "mysqld":  # mysql系列卸载根本不干净, 判断bin
            if any([
                os.path.exists(f"{SETUP_PATH}/mysql/bin/mariadbd"),
                os.path.exists(f"{SETUP_PATH}/mysql/bin/mysqld"),
            ]):
                return True
            else:
                return False
        # other
        if any([
            os.path.exists(f"/etc/init.d/{self.serviced}"),
            os.path.exists(f"/etc/init.d/{self.nick_name}"),
            os.path.exists(self.bash),
        ]):
            return True
        else:
            return False

    def is_process_running(self) -> bool:
        if not os.path.exists(self.pid_file):
            return False
        # sock file
        if self.pid_file.endswith(".sock"):
            try:
                check_list = [self.serviced] if self.serviced != "mysqld" else ["mysqld", "mariadbd"]
                cmd = f"lsof {self.pid_file} 2>/dev/null | grep -E '{'|'.join(check_list)}'"
                result = subprocess.run(cmd, shell=True, stdout=subprocess.PIPE)
                return result.returncode == 0
            except:
                return False
        else:  # pid file
            try:
                pid = public.readFile(self.pid_file)
                if not pid:
                    return False
                pid = int(pid.strip())
                if not os.path.exists(f"/proc/{pid}"):
                    return False
                try:
                    with open(f"/proc/{pid}/stat", "r") as f:
                        stat = f.read().split()
                        return stat[2] != "Z"
                except:
                    return False
            except:
                return False

    @DaemonManager.read_lock
    def main(self):
        manaul = public.readFile(MANUAL_FLAG)
        services = public.readFile(DAEMON_SERVICE)
        try:
            manual_info = json.loads(manaul) if manaul else {}
            check_list = json.loads(services) if services else []
        except Exception as e:
            public.print_log(f"error, {e}")
            return

        for service in [
            x for x in check_list if self.RECORD.get(x, 0) < self.COUNT
        ]:
            self.nick_name = service
            if not self.is_support() or not self.is_install_service():
                continue

            if not self.is_process_running():
                if manual_info.get(self.nick_name) == 1:
                    # service closed maually, skip
                    continue
                public.WriteLog(
                    "Service Daemon", f"Service [ {self.nick_name} ] is Not Running, Try to start it..."
                )
                self._overhead()
                self._script("start")
                time.sleep(3)
                if not self.is_process_running():
                    self._overhead()
                    self._script("restart")

            if manual_info.get(self.nick_name) == 1:
                # service is running, fix the wrong flag
                manual_info[self.nick_name] = 0
                # under lock file read lock
                self.__keep_flag_right(manual_info)


def first_time_installed(data: dict) -> None:
    """
    首次安装服务启动守护进程服务
    """
    if not data:
        return
    try:
        for service in SERVICES_MAP.keys():  # support service
            pl_name = f"{DATA_PATH}/first_installed_flag_{service}.pl"
            if data.get(service):  # panel installed
                setup = data[service].get("setup", False)
                if setup is False and os.path.exists(pl_name):
                    os.remove(pl_name)
                elif setup is True and not os.path.exists(pl_name):
                    DaemonManager.add_daemon(service)
                    public.writeFile(pl_name, "1", mode="w")
                else:
                    pass
    except:
        pass


if __name__ == "__main__":
    pass
    # import tracemalloc

    # tracemalloc.start()
    # snapshot1 = tracemalloc.take_snapshot()
    # RestartServices().main()
    # snapshot2 = tracemalloc.take_snapshot()

    # top_stats = snapshot2.compare_to(snapshot1, 'lineno')
    # print("[Top memory differences]")
    # for stat in top_stats[:3]:
    #     print("stat", stat)
