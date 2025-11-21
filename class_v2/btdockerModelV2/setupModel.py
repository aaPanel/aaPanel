# coding: utf-8
# -------------------------------------------------------------------
# aaPanel
# -------------------------------------------------------------------
# Copyright (c) 2015-2099 aaPanel(www.aapanel.com) All rights reserved.
# -------------------------------------------------------------------
# Author: wzz <wzz@aapanel.com>
# -------------------------------------------------------------------

# ------------------------------
# Docker模型
# ------------------------------

import json
import os
import shutil
import time
from typing import Dict, Callable, Any

import public
from btdockerModelV2 import dk_public as dp
from btdockerModelV2.dockerBase import dockerBase
from public.validate import Param


class main(dockerBase):
    __CONFIG_FILE = "/etc/docker/daemon.json"

    def __init__(self):
        if not os.path.exists(self.__CONFIG_FILE):
            public.writeFile(self.__CONFIG_FILE, '{}')

    def get_docker_compose_version(self):
        try:
            key = "dk_compose_version"
            if public.get_cache_func(key)['data']:
                if int(time.time()) - public.get_cache_func(key)["time"] < 86400:
                    return public.get_cache_func(key)["data"]

            stdout, stderr = public.ExecShell("docker compose version --short")
            if stderr != "":
                stdout, stderr = public.ExecShell("docker-compose version --short")
                if stderr != "":
                    return ""
            public.set_cache_func(key, stdout.strip())
            return stdout.strip()
        except:
            return ""

    def get_config(self, get):
        """
        获取设置配置信息
        @param get:
        @return:
        """
        check_docker_compose = self.check_docker_compose_service()
        try:
            installing = public.M('tasks').where('name=? and status=?', ("Install Docker Service", "-1")).count()
            if not installing:
                installing = public.M('tasks').where('name=? and status=?', ("Install Docker Service", "-1")).count()
        except:
            public.print_log(public.get_error_info())
            installing = 0

        # if not os.path.exists("/www/server/panel/data/db/docker.db"):
        #     public.ExecShell("mv -f /www/server/panel/data/docker.db /www/server/panel/data/db/docker.db")

        if not os.path.exists("/www/server/panel/data/docker.db"):
            public.ExecShell("mv -f /www/server/panel/data/db/docker.db /www/server/panel/data/docker.db")
        # 检查docker服务状态
        service_status = self.get_service_status()
        if not service_status:
            service_status = self.get_service_status()
        # 获取 Docker 守护进程文件配置
        daemon_config = self._get_daemon_config()

        # # 获取docker-compose版本
        docker_compose_version = self.get_docker_compose_version()

        # ipv6_file = "/etc/docker/daemon.json"

        # try:
        #     data = json.loads(public.readFile(self.__CONFIG_FILE))
        #     ipv6_status = data["ipv6"]
        #     ipv6_addr = data["fixed-cidr-v6"]
        # except:
        #     ipv6_addr = ""
        #     ipv6_status = False

        try:
            bad_registry = os.path.exists("/www/server/panel/config/bad_registry.pl")
            bad_registry_path = public.readFile("/www/server/panel/config/bad_registry.pl")
            if not bad_registry_path:
                bad_registry = False
                bad_registry_path = ""
        except:
            bad_registry = False
            bad_registry_path = ""

        # 应用商店路径
        from mod.project.docker.app.base import App
        dk_project_path = App.dk_project_path
        install_path = os.path.join(dk_project_path, 'dk_app', 'installed.json')
        allow_update_install_path = True
        if os.path.exists(install_path):
            try:
                installed_apps = json.loads(public.readFile(install_path))
                for type, apps in installed_apps.items():
                    if len(apps) > 0:
                        allow_update_install_path = False
            except:
                allow_update_install_path = False

        data = {
            "service_status": service_status,
            "docker_installed": self.check_docker_service(),
            "docker_compose_installed": check_docker_compose[0],
            "docker_compose_path": check_docker_compose[1],
            "monitor_status": self.get_monitor_status(),
            "monitor_save_date": dp.docker_conf()['SAVE'],
            "daemon_path": self.__CONFIG_FILE,
            "installing": installing,
            **daemon_config,
            "docker_compose_version": docker_compose_version,
            "bad_registry": bad_registry,
            "bad_registry_path": bad_registry_path,
            "dk_project_path": dk_project_path,
            "allow_update_install_path": allow_update_install_path
        }
        return public.return_message(0, 0, data)

    @classmethod
    def _get_daemon_config(cls):
        """获取 Docker 守护进程配置"""
        default_config = {
            "warehouse": [],
            "log_cutting": {},
            "iptables": True,
            "live_restore": False,
            "driver": ["native.cgroupdriver=systemd"],
            "socket": "unix:///var/run/docker.sock",
            "ipv6_status": False,
            "ipv6_addr": "",
            "proxy": {},
            "data-root": "/var/lib/docker"
        }

        try:
            data = json.loads(public.readFile(cls.__CONFIG_FILE))

            proxy = {
                "http_proxy": data.get("http-proxy"),
                "https_proxy": data.get("https-proxy"),
                "no_proxy": data.get("no-proxy")
            } if data.get("http-proxy", "") else default_config["proxy"]
            driver = data.get("exec-opts", 0)
            if not driver or len(driver) == 0:
                driver = default_config["driver"]
            return {
                "warehouse": data.get("insecure-registries", default_config["warehouse"]),
                "log_cutting": data.get("log-opts", default_config["log_cutting"]),
                "iptables": data.get("iptables", default_config["iptables"]),
                "live_restore": data.get("live-restore", default_config["live_restore"]),
                "driver": driver[0],
                "socket": data.get("hosts", default_config["socket"]),
                "ipv6_status": data.get("ipv6", default_config["ipv6_status"]),
                "ipv6_addr": data.get("fixed-cidr-v6", default_config["ipv6_addr"]),
                "proxy": proxy,
                "data-root": data.get("data-root", default_config["data-root"])
            }
        except:
            # public.print_log(public.get_error_info())
            return default_config

    @staticmethod
    def _get_com_registry_mirrors():
        """
        获取常用加速配置
        @return:
        """
        com_reg_mirror_file = "{}/class_v2/btdockerModelV2/config/com_reg_mirror.json".format(public.get_panel_path())
        try:
            com_reg_mirror = json.loads(public.readFile(com_reg_mirror_file))
        except:
            # public.ExecShell("rm -f {}".format(com_reg_mirror_file))
            # public.downloadFile("{}/src/com_reg_mirror.json".format(public.get_url()), com_reg_mirror_file)
            try:
                com_reg_mirror = json.loads(public.readFile(com_reg_mirror_file))
            except:
                com_reg_mirror = {
                    "https://docker.m.daocloud.io": "Third party image accelerator",
                }

        return com_reg_mirror

    def set_monitor_save_date(self, get):
        """
        :param save_date: int 例如30 表示 30天
        :param get:
        :return:
        """
        # 校验参数
        try:
            get.validate([
                Param('save_date').Require().Integer(),
            ], [
                public.validate.trim_filter(),
            ])
        except Exception as ex:
            public.print_log("error info: {}".format(ex))
            return public.return_message(-1, 0, str(ex))

        import re
        conf_path = "{}/data/docker.conf".format(public.get_panel_path())
        docker_conf = public.readFile(conf_path)
        try:
            save_date = int(get.save_date)
        except:
            return public.return_message(-1, 0, public.lang("The monitoring save time needs to be a positive integer!"))
        if save_date > 999:
            return public.return_message(-1, 0,
                                         public.lang("Monitoring data cannot be retained for more than 999 days!"))
        if not docker_conf:
            docker_conf = "SAVE={}".format(save_date)
            public.writeFile(conf_path, docker_conf)
            return public.return_message(0, 0, public.lang("Successfully set!"))
        docker_conf = re.sub(r"SAVE\s*=\s*\d+", "SAVE={}".format(save_date),
                             docker_conf)
        public.writeFile(conf_path, docker_conf)
        dp.write_log("et the monitoring time to [{}] days!".format(save_date))
        return public.return_message(0, 0, public.lang("Successfully set!"))

    def get_service_status(self):
        sock = '/var/run/docker.pid'

        # Nas镜像标识文件
        tagfile = "/www/server/panel/data/o.pl"
        if os.path.exists(tagfile) and self.check_docker_service():
            try:
                if public.cache_get(tagfile):
                    return True
                content = public.readFile(tagfile).strip()
                if content == "docker_bt_nas":
                    public.cache_set(tagfile, 1, 86400)
                    return True
            except:
                pass

        if os.path.exists(sock):
            try:
                client = dp.docker_client()
                if client:
                    return True
                return False
            except:
                return False
        else:
            return False

    # docker服务状态设置
    def docker_service(self, get):
        """
        :param act start/stop/restart
        :param get:
        :return:
        """

        act_dict = {'start': 'start', 'stop': 'stop', 'restart': 'restart'}
        if get.act not in act_dict:
            return public.return_message(-1, 0, public.lang("There's no way to do that"))
        exec_str = 'systemctl {} docker'.format(get.act)
        if get.act == "stop":
            exec_str += ";systemctl {} docker.socket".format(get.act)
        stdout, stderr = public.ExecShell(exec_str)
        if stderr and not "but it can still be activated by:\n  docker.socket\n" in stderr:
            dp.write_log(
                "Setting the Docker service status to [{}] failed, failure reason:{}".format(act_dict[get.act], stderr))

            jou_stdout, jou_stderr = public.ExecShell(
                "journalctl -xe -u docker -n 100 --no-pager|grep libusranalyse.so")
            if jou_stdout != "":
                return public.return_message(-1, 0, public.lang(
                    "Docker service setup failed, please turn off aapanel anti-intrusion and try again!"))

            if "Can't operate. Failed to connect to bus" in stderr:
                wsl_cmd = "/etc/init.d/docker {}".format(get.act)
                wsl_stdout, wsl_stderr = public.ExecShell(wsl_cmd)
                if not wsl_stderr:
                    return public.return_message(0, 0, public.lang("Setup Successful!"))
                return public.return_message(-1, 0, public.lang("Setup failed! Failure reason:{}", wsl_stderr))
            return public.return_message(-1, 0, public.lang("Setup failed! Failure reason:{}", stderr))

        if get.act != "stop":
            service_status = self.get_service_status()
            if not service_status:
                import time
                public.ExecShell("systemctl stop docker")
                public.ExecShell("systemctl stop docker.socket")
                time.sleep(1)
                public.ExecShell("systemctl start docker")

        dp.write_log("Set the Docker service status to [{}]".format(act_dict[get.act]))
        return public.return_message(0, 0, public.lang("{} success", act_dict[get.act]))

    # 获取加速配置
    def get_registry_mirrors(self, get):
        """
        获取镜像加速信息
        @param get:
        @return:
        """
        try:
            if not os.path.exists(self.__CONFIG_FILE):
                reg_mirrors = []
            else:
                # 修复文件为空报错
                conf = {}
                con = public.readFile(self.__CONFIG_FILE)
                if con:
                    conf = json.loads(con)

                # conf = json.loads(public.readFile(self.__CONFIG_FILE))

                if "registry-mirrors" not in conf:
                    reg_mirrors = []
                else:
                    reg_mirrors = conf['registry-mirrors']
        except:
            reg_mirrors = []

        # 缓存一天获取列表  不用每次都去请求
        com_reg_mirrors = public.cache_get("com_reg_mirrors")
        if not com_reg_mirrors:
            com_reg_mirrors = self._get_com_registry_mirrors()
            public.cache_set("com_reg_mirrors", com_reg_mirrors, 86400)

        data = {
            "registry_mirrors": reg_mirrors,
            "com_reg_mirrors": com_reg_mirrors
        }
        return public.return_message(0, 0, data)

    # 设置加速配置
    def set_registry_mirrors(self, get):
        """
        :param registry_mirrors_address registry.docker-cn.com\nhub-mirror.c.163.com
        :param get:
        :return:
        """
        # {"registry_mirrors_address": "https://wzz1sdf11nb.com", "remarks": ""}
        # 校验参数
        try:
            get.validate([
                Param('registry_mirrors_address').Require().String(),
                Param('remarks').String(),
            ], [
                public.validate.trim_filter(),
            ])
        except Exception as ex:
            public.print_log("error info: {}".format(ex))
            return public.return_message(-1, 0, str(ex))

        if not os.path.exists('/etc/docker/'):
            os.makedirs('/etc/docker', 755, True)

        import re
        try:
            get.registry_mirrors_address = get.get("registry_mirrors_address/s", "")
            conf = self.get_daemon_json()

            if not get.registry_mirrors_address.strip():
                if "registry-mirrors" in conf:
                    del (conf['registry-mirrors'])
            else:
                registry_mirrors = get.registry_mirrors_address.strip()
                if registry_mirrors == "":
                    # 2024/4/16 下午12:10 双重保险
                    if 'registry-mirrors' in conf:
                        del (conf['registry-mirrors'])
                else:
                    if not re.search('https?://', registry_mirrors):
                        return public.return_message(-1, 0, public.lang(
                            "Speedup address [ {}] Format error <br> Reference: https://mirror.ccs.tencentyun.com",
                            registry_mirrors))

                    conf['registry-mirrors'] = public.xsssec2(registry_mirrors)
                    if isinstance(conf['registry-mirrors'], str):
                        conf['registry-mirrors'] = [conf['registry-mirrors']]

            public.writeFile(self.__CONFIG_FILE, json.dumps(conf, indent=2))
            self.update_com_registry_mirrors(get)
            dp.write_log("Setup Docker acceleration successful!")
            get.act = "restart"
            self.docker_service(get)
            return public.return_message(0, 0, public.lang("successfully set"))

        except:
            return public.return_message(-1, 0,
                                         public.lang("Setup failed! Failure reason :{}", public.get_error_info()))

    def update_com_registry_mirrors(self, get):
        """
        更新常用加速配置
        @param get:
        @return:
        """
        if get.registry_mirrors_address == "":
            return public.return_message(0, 0, public.lang("successfully set"))

        import time
        com_reg_mirror_file = "{}/class_v2/btdockerModelV2/config/com_reg_mirror.json".format(public.get_panel_path())
        try:
            com_reg_mirror = json.loads(public.readFile(com_reg_mirror_file))
        except:
            com_reg_mirror = {
                "https://docker.m.daocloud.io": "Third party image accelerator",
                # "https://mirror.ccs.tencentyun.com": "腾讯云镜像加速站",
            }

        if get.registry_mirrors_address in com_reg_mirror:
            return public.return_message(0, 0, public.lang("Successfully set!"))

        remarks = get.remarks if "remarks" in get and get.remarks != "" else ("Custom mirrors" + str(int(time.time())))

        com_reg_mirror.update({"{}".format(get.registry_mirrors_address): remarks})
        public.writeFile(com_reg_mirror_file, json.dumps(com_reg_mirror, indent=2))
        dp.write_log("Updated common acceleration configuration successfully!")
        return public.return_message(0, 0, public.lang("Update successfully!"))

    def del_com_registry_mirror(self, get):
        """
        删除常用加速配置
        @param get:
        @return:
        """
        com_reg_mirror_file = "{}/class_v2/btdockerModelV2/config/com_reg_mirror.json".format(public.get_panel_path())
        try:
            com_reg_mirror = json.loads(public.readFile(com_reg_mirror_file))
        except:
            com_reg_mirror = {
                "https://docker.m.daocloud.io": "Third party image accelerator",
                # "https://mirror.ccs.tencentyun.com": "腾讯云镜像加速站",
            }

        if get.registry_mirrors_address not in com_reg_mirror:
            return public.return_message(0, 0, public.lang("successfully delete!"))

        del com_reg_mirror["{}".format(get.registry_mirrors_address)]
        public.writeFile(com_reg_mirror_file, json.dumps(com_reg_mirror, indent=2))
        dp.write_log("Remove common acceleration configuration successfully!")
        return public.return_message(0, 0, public.lang("successfully delete!"))

    def get_monitor_status(self):
        """
        获取docker监控状态
        @return:
        """
        try:
            from BTPanel import cache
        except:
            from cachelib import SimpleCache
            cache = SimpleCache()

        skey = "docker_monitor_status"
        result = cache.get(skey)
        if isinstance(result, bool):
            return result

        import psutil
        is_monitor = False
        try:
            for proc in psutil.process_iter():
                try:
                    pinfo = proc.as_dict(attrs=['pid', 'name'])
                    if "monitorModel.py" in pinfo['name']:
                        is_monitor = True
                except:
                    pass
        except:
            pass
        cache.set(skey, is_monitor, 86400)
        return is_monitor

    def set_docker_monitor(self, get):
        """
        开启docker监控获取docker相取资源信息
        :param act: start/stop
        :return:
        """
        # 校验参数
        try:
            get.validate([
                Param('act').Require().String('in', ['start', 'stop']),
            ], [
                public.validate.trim_filter(),
            ])
        except Exception as ex:
            public.print_log("error info: {}".format(ex))
            return public.return_message(-1, 0, str(ex))

        import time
        python = "/www/server/panel/pyenv/bin/python"
        if not os.path.exists(python):
            python = "/www/server/panel/pyenv/bin/python3"
        cmd_line = "/www/server/panel/class_v2/btdockerModelV2/monitorModel.py"
        if get.act == "start":
            self.stop_monitor(get)
            if not os.path.exists(self.moinitor_lock):
                public.writeFile(self.moinitor_lock, "1")

            shell = "nohup {} {} &".format(python, cmd_line)
            public.ExecShell(shell)
            time.sleep(1)
            if self.get_monitor_status():
                dp.write_log("Docker started monitoring successfully!")
                self.add_monitor_cron(get)
                return public.return_message(0, 0, public.lang("Start monitoring successfully!"))
            return public.return_message(-1, 0, public.lang("Failed to start monitoring!"))
        else:
            from BTPanel import cache
            skey = "docker_monitor_status"
            cache.set(skey, False)

            if os.path.exists(self.moinitor_lock):
                os.remove(self.moinitor_lock)

            self.stop_monitor(get)
            return public.return_message(0, 0, public.lang("Docker monitoring stopped successfully!"))

    # 2024/1/4 上午 9:32 停止容器监控进程
    def stop_monitor(self, get):
        '''
            @name 名称/描述
            @param 参数名<数据类型> 参数描述
            @return 数据类型
        '''
        cmd_line = [
            "/www/server/panel/class_v2/btdockerModelV2/monitorModel.py",
            "/www/server/panel/class/projectModel/bt_docker/dk_monitor.py"
        ]

        for cmd in cmd_line:
            in_pid = True
            sum = 0
            while in_pid:
                in_pid = False
                pid = dp.get_process_id(
                    "python",
                    "{}".format(cmd))
                if pid:
                    in_pid = True

                if not pid:
                    pid = dp.get_process_id(
                        "python3",
                        "{}".format(cmd)
                    )
                    if pid:
                        in_pid = True
                public.ExecShell("kill -9 {}".format(pid))
                sum += 1
                if sum > 100:
                    break

        import os

        # 指定目录路径
        directory = "/www/server/cron/"
        if not os.path.exists(directory):
            os.makedirs(directory)

        # 遍历目录下的所有非.log结尾的文件
        for filename in os.listdir(directory):
            if not filename.endswith(".log"):
                filepath = os.path.join(directory, filename)
                if os.path.isdir(filepath):
                    continue
                # 检查文件内容是否包含 "monitorModel.py"
                with open(filepath, 'r') as file:
                    content = file.read()
                    if "monitorModel.py" in content or "dk_monitor.py" in content:
                        # 删除原文件和对应的.log文件
                        if os.path.exists(filepath):
                            os.remove(filepath)
                        if os.path.exists(os.path.join(directory, "{}.log".format(filename))):
                            os.remove(os.path.join(directory, "{}.log".format(filename)))
                        public.ExecShell("crontab -l | sed '/{}/d' | crontab -".format(filename))

        dp.write_log("Docker monitoring stopped successfully!")

        public.M('crontab').where('name=?', ("[Do not delete] docker monitoring daemon",)).delete()
        return public.return_message(0, 0, public.lang("Docker monitoring stopped successfully!"))

    # 2023/12/7 下午 6:24 创建计划任务，监听监控进程是否存在，如果不存在则添加
    def add_monitor_cron(self, get):
        '''
            @name 名称/描述
            @author wzz <2023/12/7 下午 6:24>
            @param 参数名<数据类型> 参数描述
            @return 数据类型
        '''
        try:
            import crontab
            if public.M('crontab').where('name', ("[Do not delete] docker monitoring daemon",)).count() == 0:
                p = crontab.crontab()
                llist = p.GetCrontab(None)

                if type(llist) == list:
                    for i in llist:
                        if i['name'] == '[Do not delete] docker monitoring daemon':
                            return

                get = {
                    "name": "[Do not delete] docker monitoring daemon",
                    "type": "minute-n",
                    "where1": 5,
                    "hour": "",
                    "minute": "",
                    "week": "",
                    "sType": "toShell",
                    "sName": "",
                    "backupTo": "localhost",
                    "save": '',
                    "sBody": """
if [ -f {} ]; then
    new_mt=`ps aux|grep monitorModel.py|grep -v grep`
    old_mt=`ps aux|grep dk_monitor.py|grep -v grep`

    if [ -z "$new_mt" ] && [ -z "$old_mt" ]; then
        nohup /www/server/panel/pyenv/bin/python /www/server/panel/class_v2/btdockerModelV2/monitorModel.py &
    fi
fi
    """.format(self.moinitor_lock),
                    "urladdress": "undefined"
                }
                p.AddCrontab(get)
        except Exception as e:
            return False

    def check_docker_compose_service(self):
        """
        检查docker-compose是否已经安装
        :return:
        """
        docker_compose = "/usr/bin/docker-compose"

        docker_compose_path = "{}/class_v2/btdockerModelV2/config/docker_compose_path.pl".format(
            public.get_panel_path())
        if os.path.exists(docker_compose_path):
            docker_compose = public.readFile(docker_compose_path).strip()

        if not os.path.exists(docker_compose):
            dk_compose_list = ["/usr/libexec/docker/cli-plugins/docker-compose", "/usr/local/docker-compose"]
            for i in dk_compose_list:
                if os.path.exists(i):
                    public.ExecShell("ln -sf {} {}".format(i, "/usr/bin/docker-compose"))
                    break

        if not os.path.exists(docker_compose):
            return False, ""

        return True, docker_compose

    def check_docker_service(self):
        """
        检查docker是否安装
        @return:
        """
        docker = "/usr/bin/docker"
        if not os.path.exists(docker):
            return False
        return True

    def set_docker_compose_path(self, get):
        """
        设置docker-compose的路径
        @param get:
        @return:
        """
        docker_compose_file = get.docker_compose_path if "docker_compose_path" in get else ""
        if docker_compose_file == "":
            return public.return_message(-1, 0, public.lang("docker-compose file path cannot be empty!"))

        if not os.path.exists(docker_compose_file):
            return public.return_message(-1, 0, public.lang("docker-compose file does not exist!"))

        public.ExecShell("chmod +x {}".format(docker_compose_file))
        cmd_result = public.ExecShell("{} --version".format(docker_compose_file))
        if not cmd_result[0]:
            return public.return_message(-1, 0, public.lang(
                "docker-compose file is not executable or is not a docker-compose file!"))

        docker_compose_path = "{}/class_v2/btdockerModelV2/config/docker_compose_path.pl".format(
            public.get_panel_path())

        public.writeFile(docker_compose_path, docker_compose_file)
        dp.write_log("Set docker-compose path successfully!")
        return public.return_message(0, 0, public.lang("Successfully set!"))

    # 2024/9/2 下午2:22 检查本机公网IP归属地是否为中国大陆IP
    def check_area(self, get):
        '''
            @name 检查本机公网IP归属地是否为中国大陆IP
            @param get:
            @return dict{"status":True/False,"msg":"提示信息"}
        '''
        flag = "0"
        try:
            client_ip = public.get_server_ip()
            c_area = public.get_free_ip_info(client_ip)
            if ("中国" in c_area["country"] and
                    "中国" in c_area["info"] and
                    "CN" in c_area["en_short_code"] and
                    not "local" in c_area):
                if "腾讯云" in c_area["carrier"]:
                    flag = "2"
                elif "阿里云" in c_area["carrier"]:
                    flag = "3"
                else:
                    flag = "1"
        except:
            # 如果获取失败，就默认为中国大陆IP
            flag = "1"

        return flag

    # 2024/9/2 下午3:00 安装docker和docker-compose
    def install_docker_program(self, get):
        """
        安装docker和docker-compose
        :param get:
        :return:
        """
        import time
        url = get.get("url/s", "")
        type = get.get("type/d", 0)

        public.ExecShell("rm -f /etc/yum.repos.d/docker-ce.repo")
        if url == "":
            c_flag = self.check_area(get)
            if c_flag != "0":
                if c_flag == "2":
                    url = "mirrors.tencent.com/docker-ce"
                elif c_flag == "3":
                    url = "mirrors.aliyun.com/docker-ce"
                else:
                    url_file = "/www/server/panel/class/btdockerModel/config/install_url.pl"
                    public.ExecShell("rm -f {}".format(url_file))
                    public.downloadFile("{}/src/dk_app/aapanel/apps/install_url.pl".format(public.get_url()), url_file)
                    url_body = public.readFile(url_file)
                    url = url_body.strip() if url_body else ""

        # 2024/3/28 上午 10:36 检测是否已存在安装任务
        if public.M('tasks').where('name=? and status=?', ("Install Docker Service", "-1")).count():
            return public.return_message(-1, 0, public.lang(
                "The installation task already exists, please do not add it again!"))

        mmsg = "Install Docker Service"
        if type == 0 and url == "":
            # 默认安装
            execstr = ("wget -O /tmp/docker_install.sh {}/install/0/docker_install.sh && "
                       "bash /tmp/docker_install.sh install ").format(public.get_url())
        elif type == 0 and url != "":
            # 选择镜像源安装
            execstr = ("wget -O /tmp/docker_install.sh {}/install/0/docker_install.sh && "
                       "bash /tmp/docker_install.sh install {} ").format(public.get_url(), url.strip('"'))
        else:
            # 二进制安装
            execstr = "wget -O /tmp/docker_bin.sh {}/install/0/docker_bin.sh && bash /tmp/docker_bin.sh install".format(
                public.get_url())

        sid_result = public.M('tasks').add('id,name,type,status,addtime,execstr',
                                           (None, mmsg, 'execshell', '0', time.strftime('%Y-%m-%d %H:%M:%S'), execstr))
        # 暂时没
        # from panelPlugin import panelPlugin
        # panelPlugin().create_install_wait_msg(sid_result, mmsg, False)

        # public.httpPost(
        #     public.GetConfigValue('home') + '/api/panel/plugin_total', {
        #         "pid": "1111111",
        #         'p_name': "Docker commercial module"
        #     }, 3)

        # 提交安装统计
        import threading
        import requests
        threading.Thread(target=requests.post, kwargs={
            'url': '{}/api/panel/panel_count_daily'.format(public.OfficialApiBase()),
            'data': {
                'name': 'docker_installations',
            }}).start()

        return public.return_message(0, 0, public.lang("The installation task has been added to the queue!"))


    def uninstall_status(self, get):
        """
        检测docker是否可以卸载
        :param get:
        :return:
        """
        from btdockerModelV2 import containerModel
        docker_list = containerModel.main().get_list(get)['message']
        from btdockerModelV2 import imageModel
        images_list = imageModel.main().image_list(get)['message']
        if len(images_list) > 0 or len(docker_list["container_list"]) > 0:
            return public.return_message(0, 0, public.lang(
                "Please delete all containers and images before uninstalling docker!"))
        return public.return_message(0, 0, public.lang("Can be uninstalled!"))

    def uninstall_docker_program(self, get):
        """
        卸载docker和docker-compose
        :param get:
        :return:
        """
        type = get.get("type/d", 0)
        if type == 0:
            uninstall_status = self.uninstall_status(get)
            if not uninstall_status["status"]:
                return uninstall_status

        public.ExecShell(
            "wget -O /tmp/docker_install.sh {}/install/0/docker_install.sh && bash /tmp/docker_install.sh uninstall"
            .format(public.get_url()
                    ))
        public.ExecShell("rm -rf /usr/bin/docker-compose")

        return public.return_message(0, 0, public.lang("Uninstall successful!"))

    def repair_docker(self, get):
        """
        修复docker
        @param get:
        @return:
        """
        import time
        mmsg = "Repair Docker service"
        execstr = "curl -fsSL https://get.docker.com -o /tmp/get-docker.sh && sed -i '/sleep 20/d' /tmp/get-docker.sh && /bin/bash /tmp/get-docker.sh"
        public.M('tasks').add('id,name,type,status,addtime,execstr',
                              (None, mmsg, 'execshell', '0',
                               time.strftime('%Y-%m-%d %H:%M:%S'), execstr))
        # public.httpPost(
        #     public.GetConfigValue('home') + '/api/panel/plugin_total', {
        #         "pid": "1111111",
        #         'p_name': "Docker commercial module"
        #     }, 3)
        return public.return_message(0, 0, public.lang("The repair task has been added to the queue!"))

    def get_daemon_json(self):
        """
        获取daemon.json配置信息
        @param get:
        @return:
        """

        if not os.path.exists(self.__CONFIG_FILE):
            public.ExecShell("mkdir -p /etc/docker")
            public.ExecShell("touch /etc/docker/daemon.json")
            return {}

        try:
            return json.loads(public.readFile(self.__CONFIG_FILE))
        except Exception as e:
            print(e)
            return {}

    def save_daemon_json(self, get):
        """
        保存daemon.json配置信息，保存前备份，验证可以成功执行后再替换
        @param get:
        @return:
        """

        if getattr(get, "daemon_json", "") == "":
            public.ExecShell("rm -f {}".format(self.__CONFIG_FILE))
            return public.return_message(0, 0, public.lang("Saved successfully!"))

        try:
            conf = json.loads(get.daemon_json)
            public.writeFile(self.__CONFIG_FILE, json.dumps(conf, indent=2))
            dp.write_log("Save daemon.json configuration successfully!")
            return public.return_message(0, 0, public.lang("Saved successfully!"))
        except Exception as e:
            public.print_log("err: {}".format(e))
            if "Expecting property name enclosed in double quotes" in str(e):
                return public.return_message(-1, 0, public.lang(
                    "Saving failed, reason: daemon.json configuration file format error!"))

            return public.return_message(-1, 0, public.lang("Save failed, reason: {}", e))

    def set_docker_global(self, get):
        '''
        docker全局配置接口
        根据传值进行不同操作的写入/etc/docker/daemon.json
        全局设置后都需要重启docker生效
        '''

        # 配置项与对应的处理方法的映射
        '''
        加速URL  默认 https://docker.1ms.run
        私有仓库  warehouse
        日志切割  log_cutting  {"max-file":"2","max-size":"10m"}  保留份数  文件大小,  关闭功能:log_cutting {}
        iptables  是否自动管理iptables规则  默认True
        live-restore docker实时恢复  默认False
        driver方式   指定容器运行参数 默认systemd
        全局开启ipv6
        '''
        config_actions: Dict[str, Callable[[Any], Any]] = {
            'registry_mirrors_address': self.set_registry_mirrors,
            'warehouse': self.set_warehouse,
            'log_cutting': self.set_log_cutting,
            'iptables': self.set_iptables,
            'live_restore': self.set_live_restore,
            'driver': self.set_drive,
            'status': self.set_ipv6_global,
            'proxy_settings': self.set_proxy,
            "docker_root_dir": self.set_docker_root_dir
        }

        # 遍历每个配置项，调用相应的方法
        for key, func_name in config_actions.items():
            if hasattr(get, key):
                result = func_name(get)
                return result

        return public.return_message(-1, 0, public.lang("A configuration item that doesn't exist!"))

    def set_docker_root_dir(self, get):
        '''
        设置docker根目录
        @param get: docker_root_dir
        @return:
        '''
        try:
            # 停止docker服务
            get.act = "stop"
            self.docker_service(get)

            # 获取当前和目标Docker根目录
            data = self.get_daemon_json()
            current_root_dir = data.get("data-root", "/var/lib/docker")
            new_root_dir = get.get("docker_root_dir", "")

            if not new_root_dir:
                return public.return_message(-1, 0, public.lang("The Docker root cannot be empty！"))

            if current_root_dir == new_root_dir:
                return public.return_message(0, 0, public.lang("The current Docker root directory is the target directory and does not need to be changed!"))

            # 检查是否需要移动现有的Docker数据
            move_data = get.get("move_data", False)

            if move_data and os.path.exists(current_root_dir):
                try:
                    # 检查当前目录大小
                    current_size = sum(os.path.getsize(os.path.join(dirpath, filename))
                                       for dirpath, dirnames, filenames in os.walk(current_root_dir)
                                       for filename in filenames)

                    # 使用shutil.copytree进行拷贝
                    shutil.copytree(current_root_dir, new_root_dir)

                    # 检查新目录大小
                    new_size = sum(os.path.getsize(os.path.join(dirpath, filename))
                                   for dirpath, dirnames, filenames in os.walk(new_root_dir)
                                   for filename in filenames)

                    if current_size != new_size:
                        raise Exception("File size mismatch, data loss is possible!")

                    # 拷贝成功后删除源目录
                    shutil.rmtree(current_root_dir)

                except Exception as e:
                    # 如果移动失败，恢复原来的配置并返回错误
                    data = self.get_daemon_json()
                    data["data-root"] = current_root_dir
                    public.writeFile(self.__CONFIG_FILE, json.dumps(data, indent=2))

                    # 重启docker服务
                    get.act = "start"
                    self.docker_service(get)

                    return public.return_message(-1, 0, public.lang(
                        "The move failed, the original configuration has been restored, the reason:{}", e))

            # 写入新的Docker根目录到配置文件
            data["data-root"] = new_root_dir
            public.writeFile(self.__CONFIG_FILE, json.dumps(data, indent=2))

            # 重启docker服务
            get.act = "start"
            self.docker_service(get)
            return public.return_message(0, 0, public.lang("Setup successful!"))
        except Exception as e:
            return public.return_message(-1, 0, public.lang("Setup failed!{}", e))

    def set_proxy(self, get):
        '''
        设置全局代理
        @param get: proxy_settings
        @return:
        '''
        try:
            # 从 JSON 字符串中解析代理设置
            try:
                proxy_settings = json.loads(get.get("proxy_settings", "{}"))
                http_proxy = proxy_settings.get("http_proxy", "").strip()
                https_proxy = proxy_settings.get("https_proxy", "").strip()
                no_proxy = proxy_settings.get("no_proxy", "localhost,127.0.0.1").strip()
            except json.JSONDecodeError:
                return public.return_message(-1, 0, public.lang("The JSON format of the proxy settings is wrong!"))

            data = self.get_daemon_json()

            if not proxy_settings and "http-proxy" in data:
                del data["http-proxy"]
                del data["https-proxy"]
                del data["no-proxy"]
            else:
                data["http-proxy"] = http_proxy
                data["https-proxy"] = https_proxy
                data["no-proxy"] = no_proxy

            public.writeFile(self.__CONFIG_FILE, json.dumps(data, indent=2))

            # 重载全局配置文件
            self.reload_global_config()

            # 重启docker服务
            get.act = "restart"
            self.docker_service(get)
            return public.return_message(0, 0, public.lang("Proxy setup successful!"))
        except Exception as e:
            return public.return_message(-1, 0, public.lang("Setup failed!{}", e))

    def set_warehouse(self, get):
        '''
        设置私有仓库
        @param get: warehouse
        @return:
        '''
        try:
            warehouse = get.get("warehouse", "").strip()
            data = self.get_daemon_json()

            if warehouse == "" and "insecure-registries" in data:
                del data["insecure-registries"]
            else:
                warehouse = [i.strip() for i in warehouse.split(",")]
                data["insecure-registries"] = warehouse

            public.writeFile(self.__CONFIG_FILE, json.dumps(data, indent=2))

            #  重启docker服务
            get.act = "restart"
            self.docker_service(get)
            return public.return_message(0, 0, public.lang("Setup successful!"))
        except Exception as e:
            return public.return_message(-1, 0, public.lang("Setup failed!{}", e))

    def set_log_cutting(self, get):
        '''
        设置日志切割
        @param get: log_cutting
        @return:
        '''
        try:
            log_cutting = get.get("log_cutting", {})
            if isinstance(log_cutting, str):
                try:
                    log_cutting = json.loads(log_cutting)
                except:
                    log_cutting = {}

            # 确保 log_cutting 里的所有值都转换为字符串
            if isinstance(log_cutting, dict):
                log_cutting = {k: str(v) for k, v in log_cutting.items()}

            data = self.get_daemon_json()
            if not log_cutting and "log-opts" in data:
                del data["log-opts"]
            else:
                data["log-opts"] = log_cutting

            public.writeFile(self.__CONFIG_FILE, json.dumps(data, indent=2))

            #  重启docker服务
            get.act = "restart"
            self.docker_service(get)
            return public.return_message(0, 0, public.lang("Setup successful!"))
        except Exception as e:
            return public.return_message(-1, 0, public.lang("Setup failed!{}", e))

    def set_iptables(self, get):
        '''
        设置 Docker 对 iptables 规则的自动配置
        @param get:a
        @return:  dict
        '''
        try:
            iptables = get.get("iptables/d", "")
            data = self.get_daemon_json()
            data["iptables"] = True if iptables == 1 else False
            public.writeFile(self.__CONFIG_FILE, json.dumps(data, indent=2))

            #  重启docker服务
            get.act = "restart"
            self.docker_service(get)
            return public.return_message(0, 0, public.lang("Setup successful!"))
        except Exception as e:
            return public.return_message(-1, 0, public.lang("Setup failed!{}", e))

    def set_live_restore(self, get):
        '''
        设置 docker实时恢复容器
        允许在 Docker 守护进程发生意外停机或崩溃时保留正在运行的容器状态
        @param get:
        @return:  dict
        '''
        try:
            live_restore = get.get("live_restore/d", "")

            data = self.get_daemon_json()
            data["live-restore"] = True if live_restore == 1 else False

            public.writeFile(self.__CONFIG_FILE, json.dumps(data, indent=2))

            #  重启docker服务
            get.act = "restart"
            self.docker_service(get)
            return public.return_message(0, 0, public.lang("Setup successful!"))
        except Exception as e:
            return public.return_message(-1, 0, public.lang("Setup failed!{}", e))

    def set_drive(self, get):
        '''
        设置docker driver方式
        @param get:
        @return:  dict
        '''
        try:
            drive = get.get("driver", "")

            data = self.get_daemon_json()

            if drive == "systemd":
                data["exec-opts"] = ["native.cgroupdriver=systemd"]
            elif drive == "cgroupfs":
                data["exec-opts"] = ["native.cgroupdriver=cgroupfs"]
            elif drive == "" and "exec-opts" in data:
                del data["exec-opts"]

            public.writeFile(self.__CONFIG_FILE, json.dumps(data, indent=2))

            #  重启docker服务
            get.act = "restart"
            self.docker_service(get)
            return public.return_message(0, 0, public.lang("Setup successful!"))
        except Exception as e:
            return public.return_message(-1, 0, public.lang("Setup failed!{}", e))


    def set_ipv6_global(self, get):
        '''
        设置全局开启ipv6
        @param get:
        @return:  dict
        '''
        try:
            status = get.get("status/d", 0)
            ipaddr = get.get("ipaddr", "")
            if not os.path.exists("/etc/docker"): public.ExecShell("mkdir -p /etc/docker")
            data = self.get_daemon_json()
            if status == 1:
                data["ipv6"] = True
                if ipaddr == "":
                    subnet = self.random_ipv6_subnet()
                    data["fixed-cidr-v6"] = subnet
                else:
                    if not self.is_valid_ipv6_subnet(ipaddr):
                        return public.return_message(-1, 0, public.lang("Please enter the correct I Pv 6 address!"))
                    data["fixed-cidr-v6"] = ipaddr
            else:

                if "ipv6" in data and data["ipv6"]:
                    del data["ipv6"]
                if "fixed-cidr-v6" in data and data["fixed-cidr-v6"]:
                    del data["fixed-cidr-v6"]

            public.writeFile(self.__CONFIG_FILE, json.dumps(data, indent=2))

            #  重启docker服务
            get.act = "restart"
            self.docker_service(get)

            return public.return_message(0, 0, public.lang("Setup Successful!"))
        except Exception as e:
            return public.return_message(-1, 0, public.lang("Setup failed!{}", e))

    def random_ipv6_subnet(self):
        """
        在2001:db8前缀中生成一个随机IPv6子网
        Returns:
            str: Random IPv6 subnet in CIDR format.
        """
        import random
        prefix = "2001:db8:"
        hextets = [
            "".join(random.choice("123456789abcdef") + ''.join(random.choice("0123456789abcdef") for _ in range(3))) for
            _ in range(6)]
        return prefix + ":".join(hextets) + "/64"

    def is_valid_ipv6_subnet(self, subnet):
        import ipaddress
        try:
            # 尝试解析IPv6子网
            ipaddress.IPv6Network(subnet, strict=False)
            return True
        except (ipaddress.AddressValueError, ValueError) as e:
            # 解析失败，不是合法的IPv6子网
            return False

    # 2024/12/16 17:49 获取系统信息
    def get_system_info(self, get):
        '''
            @name 获取系统信息
        '''
        from btdockerModelV2.dockerSock.system import dockerSystem
        import psutil
        system_info = dockerSystem().get_system_info()

        if not system_info:
            try:
                if os.path.exists("/etc/redhat-release"):
                    OperatingSystem = public.readFile("/etc/redhat-release").strip()
                elif os.path.exists("/etc/issue"):
                    OperatingSystem = public.readFile("/etc/issue").strip()
                else:
                    OperatingSystem = public.ExecShell(". /etc/os-release && echo $VERSION")[0].strip()
            except:
                OperatingSystem = "Linux system, the version number cannot be obtained correctly!"

            system_info = {
                "Name": public.ExecShell("hostname")[0].strip(),
                "OperatingSystem": OperatingSystem,
                "Architecture": public.ExecShell("uname -m")[0].strip(),
                "KernelVersion": public.ExecShell("uname -r")[0].strip(),
                "NCPU": public.ExecShell("nproc")[0].strip(),
                "MemTotal": psutil.virtual_memory().total,
                "ServerVersion": "",
                "DockerRootDir": "",
            }
        return public.return_message(0, 0, system_info)
        # return public.returnResult(True, data=system_info)

    def update_compose(self, get):
        '''
        升级docker-compose版本
        '''
        try:
            pid_file = "/tmp/update_dk-compose.pid"
            log_file = "/tmp/update_dk-compose.log"
            try:
                import psutil
                p = psutil.Process(int(public.readFile(pid_file)))
                if p.is_running():
                    return public.return_message(0, 0, public.lang(
                        "The upgrade process PID is being executed, please wait for it to complete!"))
            except:
                pass

            if os.path.exists(log_file):
                public.writeFile(log_file, "")

            if os.path.exists(pid_file):
                os.remove(pid_file)
            # 获取当前compose版本
            key = "dk_compose_version"
            skey = "dk_compose_github_version"

            compose_version, stderr = public.ExecShell("docker compose version --short")
            if stderr != "":
                compose_version, stderr = public.ExecShell("docker-compose version --short")
                if stderr != "":
                    return public.return_message(-1, 0, public.lang(
                        "Getting the current compose version failed! Reasons for failure:{}", stderr))

            # 写入缓存compose version 版本文件
            public.set_cache_func(key, compose_version.strip())

            github_version = public.cache_get(skey)
            if not public.cache_get(skey):
                # 获取github最新compose版本
                github_version, stderr = public.ExecShell(
                    '''
                    curl -s https://api.github.com/repos/docker/compose/releases/latest | awk -F'"' '/"tag_name":/ {print $4}' | sed 's/^v//'
                    '''
                )
                if stderr != "":
                    return public.return_message(-1, 0, public.lang(
                        "Getting the latest compose version on github failed! Reasons for failure:{}", stderr))
                # 写入缓存github version 版本
                public.cache_set(skey, github_version.strip(), 86400)

            if compose_version.strip() == github_version.strip():
                return public.return_message(-1, 0, public.lang(
                    "The current compose version is consistent with the latest version on github, no upgrade required!"))

            if compose_version.strip() < github_version.strip():
                # 删除旧版本
                try:
                    if os.path.exists("/usr/bin/docker-compose"):
                        os.remove("/usr/bin/docker-compose")
                    if os.path.exists("/usr/local/lib/docker/cli-plugins/docker-compose"):
                        os.remove("/usr/local/lib/docker/cli-plugins/docker-compose")
                except:
                    pass

                public.ExecShell(
                    '''
                    nohup bash -c '
                        sudo curl -L "https://1ms.run/install/docker-compose/latest/$(uname -s)/$(uname -m)" -o /usr/local/bin/docker-compose &&
                        sudo chmod +x /usr/local/bin/docker-compose &&
                        sudo ln -sf /usr/local/bin/docker-compose /usr/bin/docker-compose &&
                        sudo ln -sf /usr/local/bin/docker-compose /usr/libexec/docker/cli-plugins/docker-compose
                    ' >{log_file} 2>&1 && echo 'bt_successful' >> {log_file} || echo 'bt_failed' >> {log_file} &
                    echo $! > {pid_file}
                    '''.format(log_file=log_file, pid_file=pid_file)
                )

            return public.return_message(0, 0, public.lang(
                "Upgrading docker-compose version, check the logs later! Latest Version:{}", github_version.strip()))

        except Exception as e:
            return public.return_message(-1, 0, public.lang("Upgrade failed! Reasons for failure:{}", e))

    @staticmethod
    def reload_global_config():
        '''
        重载全局配置文件
        '''
        try:
            # 执行重载命令
            stdout, stderr = public.ExecShell("systemctl reload docker")
            if stderr:
                return public.return_message(-1, 0, public.lang("Overload fails due to:{}", stderr))
            return public.return_message(0, 0, public.lang("Reload successful!"))
        except Exception as e:
            error_message = "Global profile overload failed:{}".format(e)
            dp.write_log(error_message)
            return public.return_message(-1, 0, public.lang("Global profile overload failed:{}", e))

    def set_dk_project_path(self, get):
        '''
            @name 设置docker项目路径
            @param "data":{"参数名":""} <数据类型> 参数描述
            @return dict{"status":True/False,"msg":"提示信息"}
        '''
        if not hasattr(get, 'path') and get.path is None and get.path == "":
            return public.return_message(-1, 0, public.lang("Wrong parameter, path parameter!"))

        if get.path.strip() == "":
            get.path = "/www/dk_project"

        project_path_file = "{}/class_v2/btdockerModelV2/config/project_path.pl".format(public.get_panel_path())

        res = public.writeFile(project_path_file, get.path)
        if not res:
            return public.return_message(-1, 0, public.lang("Setup failed!"))
        return public.return_message(0, 0, public.lang("Setup successful!"))
