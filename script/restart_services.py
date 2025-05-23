# coding: utf-8
import json
import os
import subprocess
import sys
import time

import fcntl

os.chdir("/www/server/panel")
sys.path.insert(0, "class/")
sys.path.insert(0, "/www/server/panel/")

import public

if not "class_v2" in sys.path:
    sys.path.insert(0, "/www/server/panel/class_v2")
from panel_site_v2 import panelSite

SETUP_PATH = public.get_setup_path()
DATA_PATH = os.path.join(SETUP_PATH, "panel/data")

DAEMON_SERVICE = os.path.join(DATA_PATH, "daemon_service.pl")
if not os.path.exists(DAEMON_SERVICE):
    public.writeFile(DAEMON_SERVICE, json.dumps([]))

MANUAL_FLAG = os.path.join(public.get_panel_path(), "data/mod_push_data", "manual_flag.pl")
if not os.path.exists(MANUAL_FLAG):
    public.writeFile(MANUAL_FLAG, json.dumps({}))

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


def add_daemon(service_name: str) -> bool:
    if not service_name or service_name not in SERVICES_MAP.keys():
        return False
    daemon_list = json.loads(public.readFile(DAEMON_SERVICE))
    if service_name in daemon_list:
        return True
    daemon_list.append(service_name)
    public.writeFile(DAEMON_SERVICE, json.dumps(list(set(daemon_list))))
    return True


def del_daemon(service_name: str) -> bool:
    if not service_name:
        return False
    try:
        public.writeFile(DAEMON_SERVICE, json.dumps([
            x for x in json.loads(public.readFile(DAEMON_SERVICE)) if x != service_name
        ]))
    except:
        return False
    return True


def save_file(path: str, body: str) -> None:
    try:
        with open(path, "w+") as f:
            fcntl.flock(f, fcntl.LOCK_EX)
            f.write(body)
            fcntl.flock(f, fcntl.LOCK_UN)
    except (IOError, OSError) as _:
        pass


def read_file(path: str) -> dict:
    try:
        with open(path, "r") as f:
            fcntl.flock(f, fcntl.LOCK_SH)
            content = f.read()
            fcntl.flock(f, fcntl.LOCK_UN)
        return json.loads(content) if content else {}
    except json.JSONDecodeError as _:
        return {}
    except (IOError, OSError) as _:
        return {}


def manual_flag(server_name: str = None, open_: str = None) -> dict:
    """人为关闭标记"""
    manual = read_file(MANUAL_FLAG)
    if server_name and open_ == "stop":
        manual[server_name] = 1
        save_file(MANUAL_FLAG, json.dumps(manual))
        return manual
    elif server_name and open_ in ["start", "restart"] and manual.get(server_name) == 1:
        manual[server_name] = 0
        save_file(MANUAL_FLAG, json.dumps(manual))
        return manual
    else:
        return manual


class RestartServices:
    def __init__(self):
        self.nick_name = None
        self.serviced = None
        self.pid_file = None
        self.bash = None

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

    def _script(self, act: str) -> None:
        try:
            if act not in ["start", "stop", "restart", "status"]:
                return
            # "try to {act} [{self.nick_name}]..."
            bash_path = self.bash if self.bash else f"/etc/init.d/{self.serviced}"
            if self.pid_file.endswith(".sock"):
                try:
                    subprocess.run([f"rm -f {self.pid_file}"])
                except FileNotFoundError:
                    pass
                except:
                    pass
            subprocess.run(
                [bash_path, act],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )
        except Exception as e:
            print(str(e))

    def main(self):
        with open(MANUAL_FLAG, 'rb') as fp:
            fcntl.flock(fp, fcntl.LOCK_SH)
            check_list = json.loads(public.readFile(DAEMON_SERVICE))
            manual_info = manual_flag()

            for service in check_list:
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
                    self._script("start")
                    time.sleep(5)
                    if not self.is_process_running():
                        self._script("restart")

            if manual_info.get(self.nick_name) == 1:
                # service is running, remove manual flag
                manual_info[self.nick_name] = 0
                save_file(MANUAL_FLAG, json.dumps(manual_info))
                return
            return


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
                    get = public.dict_obj()
                    get.name = service
                    get.status = 1
                    panelSite().set_restart_task(get)
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
