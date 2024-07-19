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
import gettext
_ = gettext.gettext

import json
import os

import public
from btdockerModelV2 import dk_public as dp
from btdockerModelV2.dockerBase import dockerBase
from public.validate import Param



class main(dockerBase):
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
            installing = 0

        # if not os.path.exists("/www/server/panel/data/db/docker.db"):
        #     public.ExecShell("mv -f /www/server/panel/data/docker.db /www/server/panel/data/db/docker.db")

        if not os.path.exists("/www/server/panel/data/docker.db"):
            public.ExecShell("mv -f /www/server/panel/data/db/docker.db /www/server/panel/data/docker.db")

        service_status = self.get_service_status()
        if not service_status:
            service_status = self.get_service_status()

        data = {
            "service_status": service_status,
            "docker_installed": self.check_docker_service(),
            "docker_compose_installed": check_docker_compose[0],
            "docker_compose_path": check_docker_compose[1],
            "monitor_status": self.get_monitor_status(),
            "monitor_save_date": dp.docker_conf()['SAVE'],
            "daemon_path": "/etc/docker/daemon.json",
            "installing": installing,
        }
        return public.return_message(0, 0, data)

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
            return public.return_message(-1, 0, _( "The monitoring save time needs to be a positive integer!"))
        if save_date > 999:
            return public.return_message(-1, 0, _( "Monitoring data cannot be retained for more than 999 days!"))
        if not docker_conf:
            docker_conf = "SAVE={}".format(save_date)
            public.writeFile(conf_path, docker_conf)
            return public.return_message(0, 0, _( "Successfully set!"))
        docker_conf = re.sub(r"SAVE\s*=\s*\d+", "SAVE={}".format(save_date),
                             docker_conf)
        public.writeFile(conf_path, docker_conf)
        dp.write_log("et the monitoring time to [{}] days!".format(save_date))
        return public.return_message(0, 0, _( "Successfully set!"))

    def get_service_status(self):
        sock = '/var/run/docker.pid'
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

        import public
        act_dict = {'start': 'start', 'stop': 'stop', 'restart': 'restart'}
        if get.act not in act_dict:
            return public.return_message(-1, 0, _( "There's no way to do that"))
        exec_str = 'systemctl {} docker'.format(get.act)
        if get.act == "stop":
            exec_str += ";systemctl {} docker.socket".format(get.act)
        stdout, stderr = public.ExecShell(exec_str)
        if stderr and not "but it can still be activated by:\n  docker.socket\n" in stderr:
            dp.write_log("Setting the Docker service status to [{}] failed, failure reason:{}".format(act_dict[get.act], stderr))

            jou_stdout, jou_stderr = public.ExecShell("journalctl -xe -u docker -n 100 --no-pager|grep libusranalyse.so")
            if jou_stdout != "":
                return public.return_message(-1, 0, _("Docker service setup failed, please turn off aapanel anti-intrusion and try again!"))

            return public.return_message(-1, 0, _("Setup failed! Reason for failure:{}".format(stderr)))

        if get.act != "stop":
            service_status = self.get_service_status()
            if not service_status:
                import time
                public.ExecShell("systemctl stop docker")
                public.ExecShell("systemctl stop docker.socket")
                time.sleep(1)
                public.ExecShell("systemctl start docker")

        dp.write_log("Set the Docker service status to [{}]".format(act_dict[get.act]))
        return public.return_message(0, 0, _("{} success".format(act_dict[get.act])))

    # 获取加速配置
    def get_registry_mirrors(self, get):
        """
        获取镜像加速信息
        @param get:
        @return:
        """
        try:
            if not os.path.exists('/etc/docker/daemon.json'):
                reg_mirrors = []
            else:
                conf = json.loads(public.readFile('/etc/docker/daemon.json'))
                if "registry-mirrors" not in conf:
                    reg_mirrors = []
                else:
                    reg_mirrors = conf['registry-mirrors']
        except:
            reg_mirrors = []

        com_reg_mirrors = self._get_com_registry_mirrors()

        # return {
        #     "registry_mirrors": reg_mirrors,
        #     "com_reg_mirrors": com_reg_mirrors
        # }

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
            conf = {}
            if os.path.exists('/etc/docker/daemon.json'):
                try:
                    conf = json.loads(public.readFile('/etc/docker/daemon.json'))
                except Exception as e:
                    return public.return_message(-1, 0, _( "Global configuration file error, please check {}!".format(str(e))))

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
                        return public.return_message(-1, 0, _( 'Speedup address [{}] Format error <br> Reference: https://mirror.ccs.tencentyun.com'.format(registry_mirrors)))

                    conf['registry-mirrors'] = public.xsssec2(registry_mirrors)
                    if isinstance(conf['registry-mirrors'], str):
                        conf['registry-mirrors'] = [conf['registry-mirrors']]

            public.writeFile('/etc/docker/daemon.json', json.dumps(conf, indent=2))
            if get.registry_mirrors_address != "":
                self.update_com_registry_mirrors(get)

            dp.write_log("Setup Docker acceleration successful!")
            return public.return_message(0, 0, _( 'successfully set'))

        except:
            return public.return_message(-1, 0, _('Setup failed! Failure reason :{}'.format(public.get_error_info())))

    def update_com_registry_mirrors(self, get):
        """
        更新常用加速配置
        @param get:
        @return:
        """
        import time
        com_reg_mirror_file = "{}/class_v2/btdockerModelV2/config/com_reg_mirror.json".format(public.get_panel_path())
        try:
            com_reg_mirror = json.loads(public.readFile(com_reg_mirror_file))
        except:
            com_reg_mirror = {
                "https://docker.m.daocloud.io": "Third party image accelerator",
            }

        if get.registry_mirrors_address in com_reg_mirror:
            return public.return_message(0, 0, _( "Successfully set!"))

        remarks = get.remarks if "remarks" in get and get.remarks != "" else ("Custom mirrors" + str(int(time.time())))

        com_reg_mirror.update({"{}".format(get.registry_mirrors_address): remarks})
        public.writeFile(com_reg_mirror_file, json.dumps(com_reg_mirror, indent=2))
        dp.write_log("Updated common acceleration configuration successfully!")
        return public.return_message(0, 0, _( "Update successfully!"))

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
            }

        if get.registry_mirrors_address not in com_reg_mirror:
            return public.return_message(0, 0, _( "successfully delete!"))

        del com_reg_mirror["{}".format(get.registry_mirrors_address)]
        public.writeFile(com_reg_mirror_file, json.dumps(com_reg_mirror, indent=2))
        dp.write_log("Remove common acceleration configuration successfully!")
        return public.return_message(0, 0, _( "successfully delete!"))

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
        for proc in psutil.process_iter():
            try:
                pinfo = proc.as_dict(attrs=['pid', 'name'])
                if "monitorModel.py" in pinfo['name']:
                    is_monitor = True
            except psutil.NoSuchProcess:
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
                return public.return_message(0, 0, _( "Start monitoring successfully!"))
            return public.return_message(-1, 0, _( "Failed to start monitoring!"))
        else:
            from BTPanel import cache
            skey = "docker_monitor_status"
            cache.set(skey, False)

            if os.path.exists(self.moinitor_lock):
                os.remove(self.moinitor_lock)

            self.stop_monitor(get)
            return public.return_message(0, 0, _( "Docker monitoring stopped successfully!"))

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
        return public.returnMsg(True, "Docker monitoring stopped successfully!")

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

        docker_compose_path = "{}/class_v2/btdockerModelV2/config/docker_compose_path.pl".format(public.get_panel_path())
        if os.path.exists(docker_compose_path):
            docker_compose = public.readFile(docker_compose_path).strip()

        if not os.path.exists(docker_compose):
            # public.print_log("mwmwmwmwm 没文件")
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
            return public.return_message(-1, 0, _( "docker-compose file path cannot be empty!"))

        if not os.path.exists(docker_compose_file):
            return public.return_message(-1, 0, _( "docker-compose file does not exist!"))

        public.ExecShell("chmod +x {}".format(docker_compose_file))
        cmd_result = public.ExecShell("{} --version".format(docker_compose_file))
        if not cmd_result[0]:
            return public.return_message(-1, 0, _( "docker-compose file is not executable or is not a docker-compose file!"))

        docker_compose_path = "{}/class_v2/btdockerModelV2/config/docker_compose_path.pl".format(public.get_panel_path())

        public.writeFile(docker_compose_path, docker_compose_file)
        dp.write_log("Set docker-compose path successfully!")
        return public.return_message(0, 0, _( "Successfully set!"))

    def install_docker_program(self, get):
        """
        安装docker和docker-compose
        :param get:
        :return:
        """
        import time
        url = get.get("url/s", "")
        type = get.get("type/d", 0)

        # 2024/3/28 上午 10:36 检测是否已存在安装任务
        if public.M('tasks').where('name=? and status=?', ("Install Docker Service", "-1")).count():
            return public.return_message(-1, 0, _( "The installation task already exists, please do not add it again!"))

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
            execstr = "/bin/bash /www/server/panel/install/install_soft.sh 0 install docker_bin "

        public.M('tasks').add('id,name,type,status,addtime,execstr',
                              (None, mmsg, 'execshell', '0',
                               time.strftime('%Y-%m-%d %H:%M:%S'), execstr))
        public.httpPost(
            public.GetConfigValue('home') + '/api/panel/plugin_total', {
                "pid": "1111111",
                'p_name': "Docker commercial module"
            }, 3)
        return public.return_message(0, 0, _( "The installation task has been added to the queue!"))

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
        public.httpPost(
            public.GetConfigValue('home') + '/api/panel/plugin_total', {
                "pid": "1111111",
                'p_name': "Docker commercial module"
            }, 3)
        return public.return_message(0, 0, _(  "The repair task has been added to the queue!"))

    def get_daemon_json(self, get):
        """
        获取daemon.json配置信息
        @param get:
        @return:
        """
        daemon_json = "/etc/docker/daemon.json"
        if not os.path.exists(daemon_json):
            return public.return_message(0, 0, "")

        try:
            return public.return_message(0, 0, json.loads(public.readFile(daemon_json)))
        except Exception as e:
            print(e)
            return public.return_message(-1, 0, "")

    def save_daemon_json(self, get):
        """
        保存daemon.json配置信息，保存前备份，验证可以成功执行后再替换
        @param get:
        @return:
        """
        daemon_json = "/etc/docker/daemon.json"
        if getattr(get, "daemon_json", "") == "":
            public.ExecShell("rm -f {}".format(daemon_json))
            return public.return_message(0, 0, _( "Saved successfully!"))

        try:
            conf = json.loads(get.daemon_json)
            public.writeFile(daemon_json, json.dumps(conf, indent=2))
            dp.write_log("Save daemon.json configuration successfully!")
            return public.return_message(0, 0, _( "Saved successfully!"))
        except Exception as e:
            public.print_log("err: {}".format(e))
            if "Expecting property name enclosed in double quotes" in str(e):
                return public.return_message(-1, 0, _( "Saving failed, reason: daemon.json configuration file format error!"))

            return public.return_message(-1, 0, _( "Save failed, reason: {}".format(e)))
    def uninstall_status(self, get):
        """
        检测docker是否可以卸载
        :param get:
        :return:
        """
        from btdockerModelV2 import containerModel
        docker_list = containerModel.main().get_list(get)
        from btdockerModelV2 import imageModel
        images_list = imageModel.main().image_list(get)
        if len(images_list) > 0 or len(docker_list["container_list"]) > 0:
            return public.return_message(0, 0, {"status": False,
                                                "msg": "Please manually delete all containers and images before uninstalling!"})
        return public.return_message(0, 0, "Allow uninstallation")

    def uninstall_status1(self, get):
        """
        检测docker是否可以卸载
        :param get:
        :return:
        """
        from btdockerModelV2 import containerModel
        docker_list = containerModel.main().get_list(get)
        from btdockerModelV2 import imageModel
        images_list = imageModel.main().image_list(get)
        if len(images_list) > 0 or len(docker_list["container_list"]) > 0:
            return False
        return True
    def uninstall_docker_program(self, get):
        """
        卸载docker和docker-compose
        :param get:
        :return:
        """
        type = get.get("type/d", 0)
        if type == 0:
            uninstall_status = self.uninstall_status1(get)
            if not uninstall_status["status"]:
                return public.return_message(-1, 0, _( "Please manually delete all containers and images before uninstalling!"))

        public.ExecShell(
            "wget -O /tmp/docker_install.sh {}/install/0/docker_install.sh && bash /tmp/docker_install.sh uninstall"
            .format(public.get_url()
                    ))
        public.ExecShell("rm -rf /usr/bin/docker-compose")

        return public.return_message(0, 0, "Uninstall successfully!")
