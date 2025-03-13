# coding: utf-8
import json
import os
import subprocess
import sys
import time

import psutil

os.chdir("/www/server/panel")
sys.path.insert(0, "class/")
sys.path.insert(0, "/www/server/panel/")

import public

SETUP_PATH = public.get_setup_path()

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


def manual_flag(server_name: str = None, open_: str = None) -> dict:
    import fcntl
    def save_file(path: str, body: str) -> None:
        try:
            with open(path, "w+") as f:
                fcntl.flock(f, fcntl.LOCK_EX)
                f.write(body)
                fcntl.flock(f, fcntl.LOCK_UN)
        except (IOError, OSError) as e:
            print("error, %s" % e)

    def read_file(path: str) -> dict:
        try:
            with open(path, "r") as f:
                fcntl.flock(f, fcntl.LOCK_SH)
                content = f.read()
                fcntl.flock(f, fcntl.LOCK_UN)
            return json.loads(content) if content else {}
        except json.JSONDecodeError as er:
            print("error, %s" % er)
            return {}
        except (IOError, OSError) as e:
            print("error, %s" % e)
            return {}

    manual_path = os.path.join(
        public.get_panel_path(), 'data/mod_push_data', 'manual_flag.json'
    )
    if not os.path.exists(manual_path):
        save_file(manual_path, json.dumps({}))
        manual = {}
    else:
        manual = read_file(manual_path)
    if server_name and open_ == "stop":
        manual[server_name] = 1
        save_file(manual_path, json.dumps(manual))
        return manual
    elif server_name and open_ in ["start", "restart"] and manual.get(server_name) == 1:
        manual[server_name] = 0
        save_file(manual_path, json.dumps(manual))
        return manual
    else:
        return manual


def console(body: str):
    print(public.lang(body))


class RestartServices:
    def __init__(self):
        self.nick_name = original_name
        self.serviced = None
        self.pid_file = None
        self.bash = None

    def is_support(self) -> bool:
        try:
            map_info = SERVICES_MAP.get(original_name)
            if not map_info:
                return False

            self.serviced, self.pid_file, self.bash = map_info

            if not all([self.serviced, self.pid_file, self.bash]):
                return False
            else:
                return True

        except Exception as e:
            print("error: %s" % e)
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
            for proc in psutil.process_iter(['pid', 'name', 'connections']):
                try:
                    check_list = [self.serviced] if self.serviced != "mysqld" else ["mysqld", "mariadbd"]
                    for c in check_list:
                        if c in proc.info['name']:
                            # noinspection PyDeprecation
                            for conn in proc.connections(kind='unix'):
                                if conn.laddr == self.pid_file:
                                    return True

                except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                    continue
            return False
        else:  # pid file
            try:
                pid = public.readFile(self.pid_file)
                pid = int(pid) if pid else 0
                if pid:
                    p = psutil.Process(int(pid))
                    return True if p.is_running() else False
                else:
                    return False
            except psutil.NoSuchProcess:
                return False
            except Exception as e:
                print("error: %s" % e)
                return False

    def _script(self, act: str) -> None:
        try:
            if act not in ["start", "stop", "restart", "status"]:
                return
            console(f"try to {act} [{self.nick_name}]...")
            bash_path = self.bash if self.bash else f"/etc/init.d/{self.serviced}"
            if self.pid_file.endswith(".sock"):
                try:
                    subprocess.run([f"rm -f {self.pid_file}"])
                except FileNotFoundError:
                    pass
                except Exception as e:
                    console(str(e))
            res = subprocess.run(
                [bash_path, act],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )
            if res.returncode == 0:
                console(res.stdout)
            else:
                console(res.stderr)
        except Exception as e:
            print(str(e))

    def main(self):
        if not self.is_support():
            console(f"{self.nick_name} is not support...")
            return
        if not self.is_install_service():
            console(f'[{self.nick_name}] is not installed')
            return
        if self.is_process_running():
            manual_flag(original_name, "start")
            console(f'[{self.nick_name}] is running')
            return
        else:
            console(f"[{self.nick_name}] is not running...\n")
            if manual_flag().get(original_name) == 1:
                console(
                    f'[{self.nick_name}] has been manually stopped, '
                    f'and this will not affect the daemon service.'
                    f'\nPlease manually restart the service.'
                )
                return
            else:
                self._script("start")
                time.sleep(3)
                if not self.is_process_running():
                    self._script("restart")
                return


if __name__ == "__main__":
    if len(sys.argv) == 2:
        original_name = sys.argv[1]
        RestartServices().main()
    else:
        pass
