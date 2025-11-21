# coding: utf-8
# -------------------------------------------------------------------
# aaPanel
# -------------------------------------------------------------------
# Copyright (c) 2015-2099 aaPanel(www.aapanel.com) All rights reserved.
# -------------------------------------------------------------------
# Author: wzz <wzz@aapanel.com>
# -------------------------------------------------------------------
import json
import os
import traceback
import time

import crontab
import docker.errors
# ------------------------------
# Docker模型
# ------------------------------
import public
from btdockerModelV2 import dk_public as dp
from btdockerModelV2.dockerBase import dockerBase
from public.validate import Param


class main(dockerBase):

    def __init__(self):
        super().__init__()
        self.alter_table()
        if public.M('sqlite_master').db('docker_log_split').where('type=? AND name=?', ('table', 'docker_log_split')).count():
        # if public.M('sqlite_master').where('type=? AND name=?',('table', 'docker_log_split')).count():
        #if dp.sql('sqlite_master').where('type=? AND name=?',('table', 'docker_log_split')).count():
            p = crontab.crontab()
            llist = p.GetCrontab(None)

            add_crond = True
            if type(llist) == list:
                for i in llist:
                    if i['name'] == "[Do not delete] Docker log cuts":
                        add_crond = False
                        break
                else:
                    add_crond = True

            if add_crond:
                get = {
                    "name": "[Do not delete] Docker log cuts",
                    "type": "minute-n",
                    "where1": 5,
                    "hour": "",
                    "minute": "",
                    "week": "",
                    "sType": "toShell",
                    "sName": "",
                    "backupTo": "localhost",
                    "save": '',
                    "sBody": "btpython /www/server/panel/script/dk_log_split.py",
                    "urladdress": "undefined"
                }
                p.AddCrontab(get)

    def alter_table(self):
        if not dp.sql('sqlite_master').db('container').where('type=? AND name=? AND sql LIKE ?',
                                             ('table', 'container', '%sid%')).count():
            dp.sql('container').execute("alter TABLE container add container_name VARCHAR DEFAULT ''", ())

    def docker_client(self, url):
        # unix:///var/run/docker.sock
        return dp.docker_client(url)

    def get_cmd_log(self, get):
        """
        获取命令运行容器的日志,websocket
        @param get:
        @return:
        """
        get.wsLogTitle = "Please wait to execute the command..."
        get._log_path = self._rCmd_log
        return self.get_ws_log(get)

    def run_cmd(self, get):
        """
        命令行创建运行容器(docker run),需要做危险命令校验,存在危险命令则不执行
        @param get:
        @return:
        """
        try:
            get.validate([
                Param('cmd').Require().String(),
            ], [
                public.validate.trim_filter(),
            ])
        except Exception as ex:
            public.print_log("error info: {}".format(ex))
            return public.return_message(-1, 0, ex)

        import re
        # if not hasattr(get, 'cmd'):
        #     return public.return_message(-1, 0, public.lang("cmd parameter error"))
        if "docker run" not in get.cmd:
            return public.return_message(-1, 0, public.lang("Only the docker run command can be executed"))

        danger_cmd = ['rm', 'rmi', 'kill', 'stop', 'pause', 'unpause', 'restart', 'update', 'exec', 'init',
                      'shutdown', 'reboot', 'chmod', 'chown', 'dd', 'fdisk', 'killall', 'mkfs', 'mkswap', 'mount',
                      'swapoff', 'swapon', 'umount', 'userdel', 'usermod', 'passwd', 'groupadd', 'groupdel',
                      'groupmod', 'chpasswd', 'chage', 'usermod', 'useradd', 'userdel', 'pkill']

        danger_symbol = ['&', '&&', '||', '|', ';']

        for d in danger_cmd:
            if get.cmd.startswith(d) or re.search(r'\s{}\s'.format(d), get.cmd):
                return public.return_message(-1, 0, public.lang(
                    "Dangerous command exists: [ {}],Execution is not allowed!",d))

        for d in danger_symbol:
            if d in get.cmd:
                return public.return_message(-1, 0,  public.lang('There are danger symbols: [{}],Execution is not allowed!',d))

        get.cmd = get.cmd.replace("\n", "").replace("\r", "").replace("\\", " ")
        os.system("echo -n > {}".format(self._rCmd_log))
        os.system("nohup {} >> {} 2>&1 && echo 'bt_successful' >> {} || echo 'bt_failed' >> {} &".format(
            get.cmd,
            self._rCmd_log,
            self._rCmd_log,
            self._rCmd_log,
        ))

        return public.return_message(0, 0, public.lang("The command has been executed!"))

    # 添加容器
    def run(self, get):
        """
        :param name:容器名
        :param image: 镜像
        :param publish_all_ports 暴露所有端口 1/0
        :param ports  暴露某些端口 {'1111/tcp': ('127.0.0.1', 1111)}
        :param command 命令
        :param entrypoint  配置容器启动后执行的命令
        :param environment 环境变量 xxx=xxx 一行一条
        :param auto_remove 当容器进程退出时,在守护进程端启用自动移除容器。 0/1

        :param get:
        :return:
        """

        # 校验参数
        try:
            get.validate([
                Param('name').Require().String(),
                Param('image').Require().String(),
                Param('publish_all_ports').Require().Integer(),
                Param('command').String(),
                Param('entrypoint').String(),
                Param('environment').String(),
                Param('auto_remove').String(),
            ], [
                public.validate.trim_filter(),
            ])
        except Exception as ex:
            public.print_log("error info: {}".format(ex))
            return public.return_message(-1, 0, ex)

        config_path = "{}/config/name_map.json".format(public.get_panel_path())
        if not os.path.exists(config_path):
            public.writeFile(config_path, json.dumps({}))

        if public.readFile(config_path) == '':
            public.writeFile(config_path, json.dumps({}))

        # 2024/2/20 下午 3:21 如果检测到是中文的容器名,则自动转换为英文
        name_map = json.loads(public.readFile(config_path))
        import re
        if re.findall(r"[\u4e00-\u9fa5]", get.name):
            name_str = 'q18q' + public.GetRandomString(10).lower()
            name_map[name_str] = get.name
            get.name = name_str
            public.writeFile(config_path, json.dumps(name_map))

        cPorts = get.ports if "ports" in get and get.ports != "" else False
        nPorts = {}
        if not cPorts is False:
            if ":" in cPorts.keys():
                return public.return_message(-1, 0, public.lang("The port format is wrong, this method is not supported!"))
            if "-" in cPorts.keys():
                return public.return_message(-1, 0, public.lang("The port format is wrong, this method is not supported!"))

            for i in cPorts.keys():
                if cPorts[i] == "": continue
                if isinstance(cPorts[i], list):
                    cPorts[i] = tuple(cPorts[i])

                check_port = cPorts[i]
                if isinstance(cPorts[i], tuple):
                    check_port = cPorts[i][1]

                if dp.check_socket(check_port):
                    return public.return_message(-1, 0, public.lang("The server port [{}] is already occupied, please replace it with a different port!",cPorts[i]))

                if "tcp/udp" in i:
                    cPort = i.split('/')[0]
                    nPorts[str(cPort) + "/tcp"] = cPorts[i]
                    nPorts[str(cPort) + "/udp"] = cPorts[i]
                else:
                    nPorts[i] = cPorts[i]
            del cPorts

        if "image" not in get or not get.image:
            return public.return_message(-1, 0, public.lang("Please pull the image you need"))

        if get.image == "<none>" or "<none>" in get.image:
            return public.return_message(-1, 0, public.lang("The image does not exist!"))

        mem_limit = get.mem_limit if "mem_limit" in get and get.mem_limit != "0" else None
        if not mem_limit is None:
            mem_limit_byte = dp.byte_conversion(get.mem_limit)
            if mem_limit_byte > dp.get_mem_info():
                return public.return_message(-1, 0, public.lang("The memory quota has exceeded the available amount!"))
            if mem_limit_byte < 6291456:
                return public.return_message(-1, 0, public.lang("The memory quota cannot be less than 6MB!"))

        try:
            if "force_pull" in get and get.force_pull == "0":
                self.docker_client(self._url).images.get(get.image)
        except docker.errors.ImageNotFound as e:
            return public.return_message(-1, 0,  public.lang("Image [{}] does not exist, You can try [Forced Pull]!",get.image))
        except docker.errors.APIError as e:
            return public.return_message(-1, 0,  public.lang("Image [{}] does not exist, You can try [Forced Pull]!",get.image))

        # 2024/4/16 上午11:40 检查镜像是否存在并且处理镜像如果是非应用容器的情况
        try:
            from btdockerModelV2.dockerSock import image
            sk_image = image.dockerImage()
            check_image = get.image if ":" in get.image else get.image + ":latest"
            image_inspect = sk_image.inspect(check_image)
            if type(image_inspect) != dict or "message" in image_inspect:
                self.docker_client(self._url).images.pull(check_image)

            if "Config" in image_inspect and "Cmd" in image_inspect["Config"]:
                sh_list = ("bash", "sh", "dash", "/bin/sh", "/bin/bash", "/bin/dash")
                if len(image_inspect["Config"]["Cmd"]) == 1 and image_inspect["Config"]["Cmd"][0] in sh_list:
                    get.tty = "1"
                    get.stdin_open = "1"
        except Exception as e:
            pass

        cpu_quota = get.cpu_quota if "cpu_quota" in get and get.cpu_quota != "0" else 0
        if int(cpu_quota) != 0:
            cpu_quota = float(get.cpu_quota) * 100000

            if int(cpu_quota) / 100000 > dp.get_cpu_count():
                return public.return_message(-1, 0, public.lang("cpu quota has exceeded available cores!"))

        df_restart_policy = {"Name": "unless-stopped", "MaximumRetryCount": 0}
        restart_policy = get.restart_policy if "restart_policy" in get and get.restart_policy else df_restart_policy
        if restart_policy['Name'] == "always":
            restart_policy = {"Name": "always"}

        mem_reservation = get.mem_reservation if "mem_reservation" in get and get.mem_reservation != "" else None
        # 2023/12/19 下午 3:08 检测如果小于6MB则报错
        if not mem_reservation is None and mem_reservation != "0":
            mem_reservation_byte = dp.byte_conversion(mem_reservation)
            if mem_reservation_byte < 6291456:
                return public.return_message(-1, 0, public.lang("Memory reservation cannot be less than 6MB!"))

        network_info = get.network_info if hasattr(get, "network_info") and get.network_info != "" else []

        device_request = []
        gpus = str(get.get("gpus", "0"))
        if gpus != "0":
            count = 0
            if gpus == "all":
                count = -1
            else:
                count = int(gpus)

            from docker.types import DeviceRequest
            device_request.append(DeviceRequest(driver="nvidia",count=count,capabilities=[["gpu"]]))

        try:
            res = self.docker_client(self._url).containers.create(
                name=get.name,
                image=get.image,
                detach=True,
                # cpuset_cpus=get.cpuset_cpus ,#指定容器使用的cpu个数
                tty=True if "tty" in get and get.tty == "1" else False,
                stdin_open=True if "stdin_open" in get and get.stdin_open == "1" else False,
                publish_all_ports=True if "publish_all_ports" in get and get.publish_all_ports != "0" else False,
                ports=nPorts if len(nPorts) > 0 else None,
                cpu_quota=int(cpu_quota) or 0,
                mem_reservation=mem_reservation,  # b,k,m,g
                mem_limit=mem_limit,  # b,k,m,g
                restart_policy=restart_policy,
                command=get.command if "command" in get and get.command != "" else None,
                volume_driver=get.volume_driver if "volume_driver" in get and get.volume_driver != "" else None,
                volumes=get.volumes if "volumes" in get and get.volumes != "" else None,
                auto_remove=True if "auto_remove" in get and get.auto_remove != "0" else False,
                privileged=True if "privileged" in get and get.privileged != "0" else False,
                environment=dp.set_kv(get.environment),  # "HOME=/value\nHOME11=value1"
                labels=dp.set_kv(get.labels),  # "key=value\nkey1=value1"
                device_requests=device_request
            )

        except docker.errors.APIError as e:
            if "invalid reference format" in str(e):
                return public.return_message(-1, 0, public.lang("The image name format is incorrect.such as:nginx:latest"))
            if "failed to create task for container" in str(e) or "failed to create shim task" in str(e):
                return public.return_message(-1, 0, public.lang("Container creation failed, details: {}!", str(e)))
            if "Minimum memory limit can not be less than memory reservation limit, see usage" in str(e):
                return public.return_message(-1, 0, public.lang("The memory quota cannot be less than the memory reserve!"))
            if "already exists in network bridge" in str(e):
                return public.return_message(-1, 0, public.lang("The container name or network bridge already exists. Please change the container name and try again!"))
            if "No command specified" in str(e):
                return public.return_message(-1, 0, public.lang("There is no startup command in this image, please specify the container startup command!"))
            if "permission denied" in str(e):
                return public.return_message(-1, 0,  public.lang("Permission exception! Details:{}", str(e)))
            if "Internal Server Error" in str(e):
                return public.return_message(-1, 0, public.lang("Container creation failed! Please restart the docker service at the appropriate time!"))
            if "repository does not exist or may require 'docker login'" in str(e):
                return public.return_message(-1, 0, public.lang("Image [{}] does not exist!",get.image))
            if "Minimum memory reservation allowed is 6MB" in str(e):
                return public.return_message(-1, 0, public.lang("Memory reservation cannot be less than 6MB!"))
            if "container to be able to reuse that name." in str(e):
                return public.return_message(-1, 0, public.lang("Container name already exists!"))
            if "Invalid container name" in str(e):
                return public.return_message(-1, 0, public.lang("The container name is invalid"))
            if "bind: address already in use" in str(e):
                port = ""
                for i in get.ports:
                    if ":{}:".format(get.ports[i]) in str(e):
                        port = get.ports[i]
                get.id = get.name
                self.del_container(get)
                return public.return_message(-1, 0, public.lang("Server port {}in use! Change the other port", port))
            return public.return_message(-1, 0,  public.lang("Creation failure! {}", public.get_error_info()))
        except Exception as a:
            public.print_log(traceback.format_exc())
            self.del_container(get)
            if "Read timed out" in str(a):
                return public.return_message(-1, 0, public.lang("The container creation failed and the connection to docker timed out!"))
            return public.return_message(-1, 0,  public.lang("Container failed to run! {}", str(a)))

        if res:
            # 将容器的ip改成用户指定的ip
            pdata = {
                "cpu_limit": str(get.cpu_quota),
                "container_name": get.name
            }
            dp.sql('container').insert(pdata)
            public.set_module_logs('docker', 'run_container', 1)
            dp.write_log("Container creation [{}] successful!".format(get.name))

            # 2024/2/26 下午 6:00 添加备注
            self.check_remark_table()
            dp.sql('dk_container_remark').insert({
                "container_id": res.id,
                "container_name": get.name,
                "remark": public.xssencode2(get.remark),
                "addtime": int(time.time())
            })

            if len(network_info) > 0:
                self.docker_client(self._url).networks.get("bridge").disconnect(res.id)
                for network in network_info:
                    get.net_name = network["network"]
                    get.new_container_id = res.id
                    get.tmp_ip_address = network["ip_address"]
                    get.tmp_ip_addressv6 = network["ip_addressv6"]
                    net_result = self.connent_network(get)
                    if net_result["status"] == -1:
                        return net_result

            res.start()
            return public.return_message(0, 0, {
                "status": True,
                "result": "Successfully created!",
                "id": res.id,
                "name": dp.rename(res.name),
            })

        return public.return_message(-1, 0, public.lang("Creation failure!"))
    # 2024/11/12 17:15 创建并启动容器
    def create_some_container(self, get, new_name=None):
        '''
            @name 创建并启动容器
        '''
        container = new_name if not new_name is None else get.new_container_config["name"]
        network_info = get.network_info if "network_info" in get and get.network_info != "" else []
        try:
            get.new_container = self.docker_client(self._url).containers.create(
                name=container,
                image=get.new_container_config["image"],
                detach=get.new_container_config["detach"],
                cpu_quota=get.new_container_config["cpu_quota"],
                mem_limit=get.new_container_config["mem_limit"],
                tty=get.new_container_config["tty"],
                stdin_open=get.new_container_config["stdin_open"],
                publish_all_ports=True if get.new_container_config["publish_all_ports"] == "1" else False,
                ports=get.new_container_config["ports"],
                command=get.new_container_config["command"],
                entrypoint=get.new_container_config["entrypoint"],
                environment=get.new_container_config["environment"],
                labels=get.new_container_config["labels"],
                auto_remove=get.new_container_config["auto_remove"],
                privileged=get.new_container_config["privileged"],
                volumes=get.new_container_config["volumes"],
                volume_driver=get.new_container_config["volume_driver"],
                mem_reservation=get.new_container_config["mem_reservation"],
                restart_policy=get.new_container_config["restart_policy"],
                device_requests=get.new_container_config["device_requests"]
            )
        except Exception as e:
            if "Read timed out" in str(e):
                return public.return_message(-1, 0, public.lang("Editing failed, connection to docker timed out, please restart docker and try again!"))
            return public.return_message(-1, 0, public.lang("Update failed!{}",str(e)))

        if not "upgrade" in get or get.upgrade != "1":
            if len(network_info) > 0:
                self.docker_client(self._url).networks.get("bridge").disconnect(get.new_container.id)
                for temp in network_info:
                    get.net_name = temp["network"]
                    get.new_container_id = get.new_container.id
                    get.tmp_ip_address = temp["ip_address"]
                    get.tmp_ip_addressv6 = temp["ip_addressv6"]
                    net_result = self.connent_network(get)
                    if net_result["status"] == -1:
                        get.new_container.remove()
                        return net_result
        else:
            self.docker_client(self._url).networks.get("bridge").disconnect(get.new_container.id)
            for net_name, net_settings in get.old_container_config["networking_config"].items():
                get.net_name = net_name
                get.new_container_id = get.new_container.id
                get.tmp_ip_address = net_settings["IPAddress"]
                get.tmp_ip_addressv6 = net_settings["GlobalIPv6Address"]
                net_result = self.connent_network(get)
                if net_result["status"] == -1:
                    get.new_container.remove()
                    return net_result

        get.new_container.start()
    def upgrade_container(self, get):
        """
        更新正在运行的容器镜像（重建）
        @param get:
        @return:
        """
        public.set_module_logs('docker', 'upgrade_container', 1)
        try:
            if "id" not in get:
                return public.return_message(-1, 0, public.lang("Container ID is abnormal"))

            container = self.docker_client(self._url).containers.get(get.id)

            old_container_config = self.save_container_config(container)
            new_image = get.new_image if "new_image" in get and get.new_image else "latest"
            if new_image is None:
                return public.return_message(-1, 0, public.lang("The new image name cannot be empty!"))

            if "upgrade" in get and get.upgrade == "1":
                get.new_image = "{}:{}".format(old_container_config["image"].split(':')[0], new_image)

            try:
                if "force_pull" in get and get.force_pull == "1":
                    public.ExecShell("docker pull {}".format(get.new_image))
            except docker.errors.ImageNotFound as e:
                return public.return_message(-1, 0, public.lang("The mirror does not exist!"))
            except docker.errors.APIError as e:
                return public.return_message(-1, 0, public.lang("The mirror does not exist!"))
            # except Exception as e:
            #     public.print_log(traceback.format_exc())
            #     return public.return_message(-1, 0, e)


            get.old_container_config = old_container_config
            new_container_config = self.structure_new_container_conf(get)
            if new_container_config['status']==-1:
                return public.return_message(-1, 0,  public.lang( new_container_config['message']))

            get.new_container_config = new_container_config

            # 2024/11/12 17:05 旧的容器停止掉，以便后面创建新的容器
            container.stop()

            # 2024/11/12 17:04 创建一个当前时间戳的新容器，测试是否可以正常运行
            new_name_time = int(time.time())
            new_name = "{}_{}".format(new_container_config["name"], new_name_time)
            result = self.create_some_container(get, new_name=new_name)
            if result:
                container = self.docker_client(self._url).containers.get(get.id)
                container.start()

                if "No such image" in result["msg"]:
                    return public.return_message(-1, 0, public.lang("The image [{}] does not exist, please try to check [Force pull image] and try again!", get.new_container_config["image"]))
                return public.return_message(-1, 0, public.lang("The new container was not created successfully, and the old container has been restored.  {}", str(result["msg"])))


            from btdockerModelV2.dockerSock import container
            sk_container = container.dockerContainer()

            # 2024/11/12 17:05 循环检测10次，每次1秒，看是否能获取到新容器的状态，并且必须是running运行中，否则判定为新容器创建失败，然后回滚旧容器
            is_break = False
            for i in range(10):
                sk_container_info = sk_container.get_container_inspect(get.new_container.attrs["Id"])
                state_n = sk_container_info["State"]
                if "running" in state_n["Status"] and state_n["Running"]:
                    is_break = True
                    get.new_container.stop()
                    get.new_container.remove()
                    time.sleep(1)

                    # 2024/11/12 17:06 验证了新的配置文件没有问题，可以正常启动，删掉旧容器，开始创建新的容器
                    container = self.docker_client(self._url).containers.get(get.id)
                    container.remove()
                    result = self.create_some_container(get)
                    if result: return result

                    # 2024/11/12 17:07 再次检查新的容器状态，如果已经是运行中，则返回编辑成功，否则失败
                    for i in range(10):
                        new_sk_container_info = sk_container.get_container_inspect(get.new_container.attrs["Id"])
                        if "message" in new_sk_container_info:
                            time.sleep(1)
                            continue

                        state_n = new_sk_container_info["State"]
                        if "running" in state_n["Status"] and state_n["Running"]:
                            return public.return_message(0, 0, public.lang("Update successful!"))

                        time.sleep(1)

                if is_break: break
                time.sleep(1)

            try:
                container = self.docker_client(self._url).containers.get(get.id)
                container.start()
            except:
                return public.return_message(-1, 0,  public.lang("Update failed!{}", str(e)))

            return public.return_message(0, 0,  public.lang("Update failed! The container state has been restored"))
        except docker.errors.NotFound as e:
            if "No such container" in str(e):
                return public.return_message(-1, 0, public.lang("Container does not exist!"))
            return public.return_message(-1, 0, public.lang("Update failed!{}", str(e)))
        except docker.errors.APIError as e:
            if "No such container" in str(e):
                return public.return_message(-1, 0, public.lang("Container does not exist!"))
            return public.return_message(-1, 0, public.lang("Update failed!{}", str(e)))
        except Exception as a:
            public.print_log(traceback.format_exc())
            if "Read timed out" in str(a):
                return public.return_message(-1, 0, public.lang("Container editing failed and the connection to docker timed out."))
            return public.return_message(-1, 0, public.lang("Update failed!{}", str(a)))
    # 2024/5/28 下午3:30 编辑容器连接网络
    def connent_network(self, get):
        '''
            @name 编辑容器连接网络
            @author wzz <2024/5/28 下午3:30>
            @param "data":{"参数名":""} <数据类型> 参数描述
            @return dict{"status":True/False,"msg":"提示信息"}
        '''
        if get.net_name == "bridge":
            self.docker_client(self._url).networks.get(get.net_name).connect(get.new_container_id)
            return public.return_message(0, 0, "")

        try:
            self.docker_client(self._url).networks.get(get.net_name).connect(
                get.new_container_id,
                ipv4_address=get.tmp_ip_address,
                ipv6_address=get.tmp_ip_addressv6,
            )
        except docker.errors.APIError as e:
            if ("user specified IP address is supported only when "
                "connecting to networks with user configured subnets") in str(e):
                return public.return_message(-1, 0, public.lang("The container is successfully edited, and the subnet is not specified when the currently specified [{}] network is created, and the IP cannot be customized, and the IP has been automatically assigned to you!",str(get.net_name)))
        except Exception as e:
            return public.return_message(-1, 0, public.lang("The container is successfully edited, the network [{}] setting fails, and the IP address has been automatically assigned to you, error details:{}！",get.net_name, str(e)))

        return public.return_message(0, 0, "")

    def save_container_config(self, container):
        """
        保存容器的配置信息
        """
        network_config = {}
        for net_name, net_settings in container.attrs["NetworkSettings"]["Networks"].items():
            network_config[net_name] = {
                "IPAMConfig": net_settings["IPAMConfig"],
                "Links": net_settings["Links"],
                "MacAddress": net_settings["MacAddress"],
                "Aliases": net_settings["Aliases"],
                "NetworkID": net_settings["NetworkID"],
                "EndpointID": net_settings["EndpointID"],
                "Gateway": net_settings["Gateway"],
                "IPAddress": net_settings["IPAddress"],
                "IPPrefixLen": net_settings["IPPrefixLen"],
                "IPv6Gateway": net_settings["IPv6Gateway"],
                "GlobalIPv6Address": net_settings["GlobalIPv6Address"],
                "GlobalIPv6PrefixLen": net_settings["GlobalIPv6PrefixLen"],
                "DriverOpts": net_settings["DriverOpts"],
            }
            if "DNSNames" in net_settings: network_config[net_name]["DNSNames"] = net_settings["DNSNames"]

        return public.return_message(0, 0,{
            "image": container.attrs['Config']['Image'],
            "name": container.attrs['Name'],
            "detach": True,
            "cpu_quota": container.attrs['HostConfig']['CpuQuota'],
            "mem_limit": container.attrs['HostConfig']['Memory'],
            "tty": container.attrs['Config']['Tty'],
            "stdin_open": container.attrs['Config']['OpenStdin'],
            "publish_all_ports": container.attrs['HostConfig']['PublishAllPorts'],
            "ports": container.attrs['NetworkSettings']['Ports'],
            "command": container.attrs['Config']['Cmd'],
            "entrypoint": container.attrs['Config']['Entrypoint'],
            "environment": container.attrs['Config']['Env'],
            "labels": container.attrs['Config']['Labels'],
            "auto_remove": container.attrs['HostConfig']['AutoRemove'],
            "privileged": container.attrs['HostConfig']['Privileged'],
            "volumes": container.attrs['HostConfig']['Binds'],
            "volume_driver": container.attrs['HostConfig']['VolumeDriver'],
            "mem_reservation": container.attrs['HostConfig']['MemoryReservation'],
            "restart_policy": container.attrs['HostConfig']['RestartPolicy'],
            "networking_config": network_config,
        })

    def structure_new_container_conf(self, get):
        """
        构造新的容器配置
        @param get:
        @return:
        """
        new_image = get.new_image if hasattr(get, "new_image") and get.new_image else get.old_container_config["image"]
        new_name = get.new_name if hasattr(get, "new_name") and get.new_name else get.old_container_config["name"].replace("/", "")
        new_cpu_quota = get.new_cpu_quota if hasattr(get, "new_cpu_quota") and get.new_cpu_quota != 0 else get.old_container_config["cpu_quota"]
        if int(new_cpu_quota) != 0:
            new_cpu_quota = float(new_cpu_quota) * 100000

            if int(new_cpu_quota) / 100000 > dp.get_cpu_count():
                return public.return_message(-1, 0, public.lang( "cpu quota has exceeded available cores!"))

        new_mem_limit = get.new_mem_limit if hasattr(get, "new_mem_limit") and get.new_mem_limit else get.old_container_config["mem_limit"]
        new_tty = get.new_tty if hasattr(get, "new_tty") and get.new_tty else get.old_container_config["tty"]
        new_stdin_open = get.new_stdin_open if hasattr(get, "new_stdin_open") and get.new_stdin_open else get.old_container_config["stdin_open"]
        new_publish_all_ports = get.new_publish_all_ports if hasattr(get, "new_publish_all_ports") and get.new_publish_all_ports != '0' else get.old_container_config["publish_all_ports"]
        get_new_ports = get.new_ports if hasattr(get, "new_ports") and get.new_ports else False
        new_ports = {}
        if get_new_ports:
            if ":" in get_new_ports.keys():
                return public.return_message(-1, 0, public.lang( "The port format is incorrect"))
            if "-" in get_new_ports.keys():
                return public.return_message(-1, 0, public.lang( "The port format is incorrect"))

            for i in get_new_ports.keys():
                if get_new_ports[i] == "": continue
                if isinstance(get_new_ports[i], list):
                    get_new_ports[i] = tuple(get_new_ports[i])

                if "tcp/udp" in i:
                    cPort = i.split('/')[0]
                    new_ports[str(cPort) + "/tcp"] = get_new_ports[i]
                    new_ports[str(cPort) + "/udp"] = get_new_ports[i]
                else:
                    new_ports[i] = get_new_ports[i]
            del get_new_ports

        new_ports = new_ports if new_ports else get.old_container_config["ports"]
        new_command = get.new_command if hasattr(get, "new_command") else get.old_container_config["command"]
        new_entrypoint = get.new_entrypoint if hasattr(get, "new_entrypoint") else get.old_container_config["entrypoint"]
        new_environment = get.new_environment if hasattr(get, "new_environment") and get.new_environment != '' else get.old_container_config["environment"]
        new_labels = get.new_labels if hasattr(get, "new_labels") and get.new_labels != '' else get.old_container_config["labels"]
        new_auto_remove = True if hasattr(get, "new_auto_remove") and get.new_auto_remove != '0' else get.old_container_config["auto_remove"]
        new_privileged = True if hasattr(get, "new_privileged") and get.new_privileged != '0' else get.old_container_config["privileged"]
        new_volumes = get.new_volumes if hasattr(get, "new_volumes") and get.new_volumes else get.old_container_config["volumes"]
        new_volume_driver = get.new_volume_driver if hasattr(get, "new_volume_driver") and get.new_volume_driver else get.old_container_config["volume_driver"]
        new_mem_reservation = get.new_mem_reservation if hasattr(get, "new_mem_reservation") and get.new_mem_reservation else get.old_container_config["mem_reservation"]
        new_restart_policy = get.new_restart_policy if hasattr(get, "new_restart_policy") and get.new_restart_policy else get.old_container_config["restart_policy"]
        new_network = get.new_network if hasattr(get, "new_network") and get.new_network else get.old_container_config["network"]

        device_request = []
        gpus = str(get.get("gpus", "0"))
        if gpus != "0":
            count = 0
            if gpus == "all":
                count = -1
            else:
                count = int(gpus)

            from docker.types import DeviceRequest
            device_request.append(DeviceRequest(driver="nvidia", count=count, capabilities=[["gpu"]]))

        return public.return_message(0, 0, {
            "image": new_image,
            "name": new_name,
            "detach": True,
            "cpu_quota": int(new_cpu_quota),
            "mem_limit": new_mem_limit,
            "tty": new_tty,
            "stdin_open": new_stdin_open,
            "publish_all_ports": new_publish_all_ports,
            "ports": new_ports,
            "command": new_command,
            "entrypoint": new_entrypoint,
            "environment": dp.set_kv(new_environment) if type(new_environment) != list else new_environment,
            "labels": dp.set_kv(new_labels) if type(new_labels) != dict else new_labels,
            "auto_remove": new_auto_remove,
            "privileged": new_privileged,
            "volumes": new_volumes,
            "volume_driver": new_volume_driver,
            "mem_reservation": new_mem_reservation,
            "restart_policy": new_restart_policy,
            "device_requests":device_request
        })

    def commit(self, get):
        """
        保存为镜像
        :param repository       推送到的仓库
        :param tag              镜像标签 jose:v1
        :param message          提交的信息
        :param author           镜像作者
        :param changes
        :param conf dict
        :param path 导出路径
        :param name 导出文件名
        :param get:
        :return:
        """
        try:
            if not hasattr(get, 'conf') or not get.conf:
                get.conf = None
            if get.repository == "docker.io":
                get.repository = ""

            container = self.docker_client(self._url).containers.get(get.id)
            container.commit(
                repository=get.repository if "repository" in get else None,
                tag=get.tag if "tag" in get else None,
                message=get.message if "message" in get else None,
                author=get.author if "author" in get else None,
                # changes=get.changes if get.changes else None,
                conf=get.conf
            )
            dp.write_log("Submitted container [{}] as image [{}] successfully".format(container.attrs['Name'], get.tag))

            if hasattr(get, "path") and get.path:
                get.id = "{}:{}".format(get.repository, get.tag)
                from btdockerModelV2 import imageModel as di
                result = di.main().save(get)
                if result['status'] == -1:
                    return public.return_message(0, 0,  public.lang("The image has been generated, and{}", result['message']))
                return public.return_message(0, 0, result)

            return public.return_message(0, 0, public.lang("submit successfully!"))
        except Exception as e:
            return public.return_message(-1, 0,  public.lang("Submission Failed!{}", str(e)))


    def docker_shell(self, get):
        """
        容器执行命令
        :param get:
        :return:
        """
        try:
            get.validate([
                Param('id').Require().String(),
                Param('shell').Require().String('in', ['bash', 'sh']),
                # Param('sudo_i').Require().String(),
            ], [
                public.validate.trim_filter(),
            ])
        except Exception as ex:
            public.print_log("error info: {}".format(ex))
            return public.return_message(-1, 0, ex)
        try:

            user_root = "-u root" if hasattr(get, "sudo_i") else ""

            cmd = 'docker container exec -it {} {} {}'.format(user_root, get.id, get.shell)
            return public.return_message(0, 0, cmd)
        except docker.errors.APIError as ex:
            return public.return_message(-1, 0, public.lang("Failed to get container"))

    def export(self, get):
        """
        导出容器为tar 没有导入方法,目前弃用
        :param get:
        :return:
        """
        from os import path as ospath
        from os import makedirs as makedirs
        try:
            if "tar" in get.name:
                file_name = '{}/{}'.format(get.path, get.name)
            else:
                file_name = '{}/{}.tar'.format(get.path, get.name)
            if not ospath.exists(get.path):
                makedirs(get.path)
            public.writeFile(file_name, '')
            f = open(file_name, 'wb')
            container = self.docker_client(self._url).containers.get(get.id)
            data = container.export()
            for i in data:
                f.write(i)
            f.close()
            return public.return_message(0, 0, public.lang("Successfully exported to:{}", file_name))
        except:
            return public.return_message(-1, 0, public.lang( 'operation failure:' + str(public.get_error_info())))

    def del_container(self, get):
        """
        删除指定容器
        @param get:
        @return:
        """

        try:
            get.validate([
                Param('id').Require().String(),
            ], [
                public.validate.trim_filter(),
            ])
        except Exception as ex:
            public.print_log("error info: {}".format(ex))
            return public.return_message(-1, 0, ex)

        import sys
        sys.path.insert(0, '/www/server/panel/class')
        from btdockerModelV2.proxyModel import main
        from panelSite import panelSite
        try:
            container = self.docker_client(self._url).containers.get(get.id)
            config_path = "{}/config/name_map.json".format(public.get_panel_path())
            if not os.path.exists(config_path):
                public.writeFile(config_path, json.dumps({}))
            if public.readFile(config_path) == '':
                public.writeFile(config_path, json.dumps({}))
            config_data = json.loads(public.readFile(config_path))
            if container.name in config_data.keys():
                config_data.pop(container.name)
            public.writeFile(config_path, json.dumps(config_data))
            container.remove(force=True)
            dp.sql("cpu_stats").where("container_id=?", (get.id,)).delete()
            dp.sql("io_stats").where("container_id=?", (get.id,)).delete()
            dp.sql("mem_stats").where("container_id=?", (get.id,)).delete()
            dp.sql("net_stats").where("container_id=?", (get.id,)).delete()
            dp.sql("container").where("container_nam=?", (container.attrs['Name'])).delete()
            dp.write_log("Delete container [{}] successfully!".format(container.attrs['Name']))
            get.container_id = get.id
            # todo 此处导入注意适配  info返回已改
            info = main().get_proxy_info(get)['message']
            if info and 'name' in info and 'id' in info:
                args = public.to_dict_obj({
                    'id': info['id'],
                    'webname': info['name']

                })
                panelSite().DeleteSite(args)
                # domain_id = dp.sql('dk_domain').where('id=?', (info['id'],)).find()

                # 删除站点  改默认数据库
                # dp.sql('sites').where('name=?', (info['name'],)).delete()
                # dp.sql('domain').where("name=?", (info['name'],)).delete()
                public.M('sites').where('name=?', (info['name'],)).delete()
                public.M('domain').where("name=?", (info['name'],)).delete()

                # 删除数据库记录
                dp.sql('dk_domain').where('id=?', (info['id'],)).delete()
                dp.sql('dk_sites').where('container_id=?', (get.id,)).delete()

            if public.M('sqlite_master').where('type=? AND name=?', ('table', 'docker_log_split')).count():
                id = public.M('docker_log_split').where('pid=?', (get.id,)).getField('id')
                public.M('docker_log_split').where('id=?', (id,)).delete()

                all_data = public.M('docker_log_split').field('pid').select()
                if not all_data:
                    public.M("docker_log_split").execute('drop table if exists docker_log_split')

                containers_list = self._get_list(get)
                if not containers_list["container_list"]:
                    public.M("docker_log_split").execute('drop table if exists docker_log_split')

                for i in all_data:
                    for cc in containers_list["container_list"]:
                        if i['pid'] in cc['id']:
                            break
                    else:
                        public.M('docker_log_split').where('pid=?', (i['pid'],)).delete()

            if not public.M('sqlite_master').where('type=? AND name=?', ('table', 'docker_log_split')).count():
                p = crontab.crontab()
                llist = p.GetCrontab(None)
                if type(llist) == list:
                    for i in llist:
                        if i['name'] == '[do not delete] Docker log cut':
                            get.id = i['id']
                            p.DelCrontab(get)
                            break

            return public.return_message(0, 0, public.lang("Successfully deleted!"))
        except Exception as e:
            if "operation not permitted" in str(e):
                return public.return_message(-1, 0,  public.lang("Please turn off the [Tamper-proof for Enterprise] before trying!"))
            return public.return_message(-1, 0,  public.lang("Delete failed! {}", str(e)))

    # 设置容器状态
    def set_container_status(self, get):
        """
        设置容器状态
        @param get:
        @return:
        """
        try:
            get.validate([
                Param('id').Require().String(),
                Param('status').Require().String(),
            ], [
                public.validate.trim_filter(),
            ])
        except Exception as ex:
            public.print_log("error info: {}".format(ex))
            return public.return_message(-1, 0, ex)

        try:
            container = self.docker_client(self._url).containers.get(get.id)
            result = {"status": 0, "message": {"result": "Successfully set!"}}
            if get.status == "start":
                result = self.start(get)
            elif get.status == "stop":
                result = self.stop(get)
            elif get.status == "pause":
                result = self.pause(get)
            elif get.status == "unpause":
                result = self.unpause(get)
            elif get.status == "reload":
                result = self.reload(get)
            elif get.status == "kill":
                container.kill()
            else:
                container.restart()

            try:
                # public.print_log(result)
                #{"status": 0, "timestamp": 1729561303, "message": {"result": "\u505c\u6b62\u6210\u529f\uff01"}}
                data = {
                    "name": container.attrs['Name'].replace('/', ''),
                    "result": result['message']['result'],
                    # "msg": result['msg'],
                }

                if result['status'] == 0:
                    return public.return_message(0, 0,data)
                else:
                    return public.return_message(-1, 0, data)

            except:
                return public.return_message(-1, 0, {
                        "name": container.attrs['Name'].replace('/', ''),
                        # "status": False,
                        "result": str(result['message']['result']),
                    })
                    # return public.return_message(-1, 0, str(result['msg']))
        except Exception as e:

            try:
                if "No such container" in str(e):
                    return public.return_message(-1, 0, public.lang("The container has been deleted!"))
                if "port is already allocated" in str(e) or "address already in use" in str(e):
                    if "[::]" in str(e):
                        str_port = str(e).split("[::]:")[1].split(":")[0]
                        return public.return_message(-1, 0, public.lang("ipv6 server port [ {}] is occupied!", str_port))
                    else:
                        str_port = str(e).split("0.0.0.0")[1].split(":")[1].split(" ")[0]
                        return public.return_message(-1, 0, public.lang("ipv4 server port [ {}] is occupied!", str_port))
                return public.return_message(-1, 0,  public.lang("Setup failed! {}", str(e)))

            except Exception as e:
                return public.return_message(-1, 0,  public.lang("Setup failed! {}", str(e)))

    # 停止容器
    def stop(self, get):
        """
        停止指定容器  (内部调用)
        :param get:
        :return:
        """
        try:
            get.status = "stop"
            container = self.docker_client(self._url).containers.get(get.id)
            container.stop()
            time.sleep(1)
            data = self.docker_client(self._url).containers.get(get.id)
            if data.attrs['State']['Status'] != "exited":
                return public.return_message(-1, 0, public.lang( "Stop failing!"))
            dp.write_log("Stopping container [{}] success!".format(data.attrs['Name'].replace('/', '')))
            return public.return_message(0, 0, public.lang("Stop succeeding!"))
        except docker.errors.APIError as e:
            if "is already paused" in str(e):
                return public.return_message(-1, 0, public.lang("The container has paused."))
            if "No such container" in str(e):
                return public.return_message(0, 0, public.lang( "Container stopped and deleted"))
            return public.return_message(-1, 0,  public.lang("Stop failing!{}", e))

    def start(self, get):
        """
        启动指定容器 (内部调用)
        :param get:
        :return:
        """
        try:
            get.status = "start"
            container = self.docker_client(self._url).containers.get(get.id)
            container.start()
            time.sleep(1)
            data = self.docker_client(self._url).containers.get(get.id)
            if data.attrs['State']['Status'] != "running":
                return public.return_message(-1, 0, public.lang( "boot failed!"))
            dp.write_log("Starting container [{}] was successful!".format(data.attrs['Name'].replace('/', '')))
            return public.return_message(0, 0, public.lang( "starting success!"))
        except docker.errors.APIError as e:
            if "cannot start a paused container, try unpause instead" in str(e):
                return self.unpause(get)
        except Exception as a:
            print(traceback.format_exc())
            raise Exception(a)

    def pause(self, get):
        """
        暂停此容器内的所有进程  (内部调用)
        :param get:
        :return:
        """
        try:
            get.status = "pause"
            container = self.docker_client(self._url).containers.get(get.id)
            container.pause()
            time.sleep(1)
            data = self.docker_client(self._url).containers.get(get.id)
            if data.attrs['State']['Status'] != "paused":
                return public.return_message(-1, 0, public.lang( "Container pause failed!"))
            dp.write_log("Pause container [{}] success!".format(data.attrs['Name'].replace('/', '')))
            return public.return_message(0, 0, public.lang( "Container pause successfully!"))
        except docker.errors.APIError as e:
            if "is already paused" in str(e):
                return public.return_message(-1, 0, public.lang( "The container has been suspended!"))
            if "is not running" in str(e):
                return public.return_message(-1, 0, public.lang( "The container is not started and cannot be paused!"))
            if "is not paused" in str(e):
                return public.return_message(-1, 0, public.lang(
                                        "The container is not paused or has been deleted. Check if the container has the option to delete immediately after stopping!"))
            return str(e)
        except Exception as a:
            print(traceback.format_exc())
            raise Exception(a)

    def unpause(self, get):
        """
        取消暂停该容器内的所有进程  (内部调用)
        :param get:
        :return:
        """
        try:
            get.status = "unpause"
            container = self.docker_client(self._url).containers.get(get.id)
            container.unpause()
            time.sleep(1)
            data = self.docker_client(self._url).containers.get(get.id)
            if data.attrs['State']['Status'] != "running":
                return public.return_message(-1, 0, public.lang( "boot failed!"))
            dp.write_log("Unpause container [{}] success!".format(data.attrs['Name'].replace('/', '')))
            return public.return_message(0, 0, public.lang( "The container unpaused successfully"))
        except docker.errors.APIError as e:
            if "is already paused" in str(e):
                return public.return_message(-1, 0, public.lang( "The container has paused."))
            if "is not running" in str(e):
                return public.return_message(-1, 0, public.lang( "The container is not started and cannot be paused!"))
            if "is not paused" in str(e):
                return public.return_message(-1, 0, public.lang(
                                        "The container is not paused or has been deleted. Check if the container has the option to delete immediately after stopping!"))
            return str(e)
        except Exception as a:
            print(traceback.format_exc())
            raise Exception(a)

    def reload(self, get):
        """
        再次从服务器加载此对象并使用新数据更新 attrs  (内部调用)
        :param get:
        :return:
        """
        get.status = "reload"
        container = self.docker_client(self._url).containers.get(get.id)
        container.reload()
        time.sleep(1)
        data = self.docker_client(self._url).containers.get(get.id)
        if data.attrs['State']['Status'] != "running":
            return public.return_message(-1, 0, public.lang( "boot failed!"))
        dp.write_log("Reloading container [{}] succeeded!".format(data.attrs['Name'].replace('/', '')))
        return public.return_message(0, 0, public.lang( "The container was reloaded successfully!"))

    def restart(self, get):
        """
        重新启动这个容器。类似于 docker restart 命令
        :param get:
        :return:
        """
        try:
            get.status = "restart"
            container = self.docker_client(self._url).containers.get(get.id)
            container.restart()
            time.sleep(1)
            data = self.docker_client(self._url).containers.get(get.id)
            if data.attrs['State']['Status'] != "running":
                return public.return_message(-1, 0, public.lang( "boot failed!"))
            dp.write_log("Restart container [{}] successfully!".format(data.attrs['Name'].replace('/', '')))
            return public.return_message(0, 0, public.lang( "Container restarts successfully!"))
        except docker.errors.APIError as e:
            if "container is marked for removal and cannot be started" in str(e):
                return public.return_message(-1, 0, public.lang(
                                        "The container has been stopped and deleted because containers have the option to automatically delete when stopped"))
            if "is already paused" in str(e):
                return public.return_message(-1, 0, public.lang( "The container has paused"))
            return str(e)

    def get_container_ip(self, container_networks):
        """
        获取容器IP
        @param container_networks:
        @return:
        """
        ipv4_list = []
        ipv6_list = []
        for network in container_networks:
            if container_networks[network]['IPAddress'] != "":
                ipv4_list.append(container_networks[network]['IPAddress'])

            if container_networks[network]['GlobalIPv6Address'] != "":
                ipv6_list.append(container_networks[network]['GlobalIPv6Address'])
        return {"ipv4": ipv4_list, "ipv6": ipv6_list}

    def get_container_path(self, detail):
        """
        获取容器路径
        @param detail:
        @return:
        """
        try:
            import os
            if not "GraphDriver" in detail:
                return False
            if "Data" not in detail["GraphDriver"]:
                return False
            if "MergedDir" not in detail["GraphDriver"]["Data"]:
                return False
            path = detail["GraphDriver"]["Data"]["MergedDir"]
            if not os.path.exists(path):
                return ""
            return path
        except:
            return False

    def get_container_info(self, get):
        """
        获取容器信息
        @param get:
        @return:
        """
        try:
            if "id" not in get or get.id == "":
                return public.return_message(-1, 0, public.lang("The container ID is empty"))

            from btdockerModelV2.dockerSock import container
            sk_container = container.dockerContainer()
            sk_container_info = sk_container.get_container_inspect(get.id)

            if "No such container" in str(sk_container_info):
                return public.return_message(-1, 0, public.lang("The container doesn't exist!"))

            info_path = "/var/lib/docker/containers/{}/container_info.json".format(sk_container_info["Id"])
            public.writeFile(info_path, json.dumps(sk_container_info, indent=3))
            sk_container_info['container_info'] = info_path
            # 计算GPU数量
            device_requests = sk_container_info["HostConfig"].get('DeviceRequests', [])
            sk_container_info["gpu_count"] = 0
            if device_requests is not None and len(device_requests) != 0:
                for item in device_requests:
                    if item["Driver"] == "nvidia":
                        sk_container_info["gpu_count"] = item["Count"]
                        break
            return public.return_message(0, 0, sk_container_info)
        except Exception as e:
            if "No such container" in str(e):
                return public.return_message(-1, 0, public.lang("Container does not exist!"))
            return public.return_message(-1, 0,  public.lang("Failed to get container information!{}", str(e)))

    def struct_container_ports(self, ports):
        """
        构造容器ports
        @param ports:
        @return:
        """
        data = dict()
        for port in ports:
            key = str(port["PrivatePort"]) + "/" + port["Type"]
            if key not in data.keys():
                data[str(port["PrivatePort"]) + "/" + port["Type"]] = [{
                    "HostIp": port["IP"],
                    "HostPort": str(port.get("PublicPort", ""))
                }] if "IP" in port else None
            else:
                data[str(port["PrivatePort"]) + "/" + port["Type"]].append({
                    "HostIp": port["IP"],
                    "HostPort": str(port.get("PublicPort", ""))
                })
        return data

    def struct_container_list(self, container, container_to_top=None):
        '''
            @name 构造容器列表
            @author wzz <2024/3/13 下午 5:32>
            @param "data":{"参数名":""} <数据类型> 参数描述
            @return dict{"status":True/False,"msg":"提示信息"}
        '''
        tmp = {
            "id": container["Id"],
            "name": dp.rename(container['Names'][0].replace("/", "")),
            "status": container["State"],
            "image": container["Image"],
            "created_time": container["Created"],
            "ip": self.get_container_ip(container["NetworkSettings"]['Networks'])["ipv4"],
            "ipv6": self.get_container_ip(container["NetworkSettings"]['Networks'])["ipv6"],
            "ports": self.struct_container_ports(container["Ports"]),
            "is_top": 0 if container_to_top is None else 1 if container['Names'][0].replace("/", "") in container_to_top else 0,
        }

        return tmp

    # 2024/4/11 下午2:46 获取 merged 目录
    def get_container_merged(self, get):
        '''
            @name 获取容器 merged 目录
            @author wzz <2024/4/11 下午2:47>
            @param "data":{"参数名":""} <数据类型> 参数描述
            @return dict{"status":True/False,"msg":"提示信息"}
        '''
        try:
            get.id = get.get("id", "")
            if get.id == "":
                return public.return_message(-1, 0, public.lang("The container ID is empty"))
            return public.return_message(0, 0, {
                "path": public.ExecShell("docker inspect -f \"{{json .GraphDriver.Data.MergedDir}}\" " + get.id)[
                    0].strip().strip('"')})

        except Exception as e:
            return public.return_message(0, 0, {"path": ""})

    # 2024/4/11 下午3:44 获取其他容器列表的数据
    def get_other_container_data(self, get):
        '''
            @name 获取其他容器列表的数据
            @author wzz <2024/4/11 下午3:45>
            @param "data":{"参数名":""} <数据类型> 参数描述
            @return dict{"status":True/False,"msg":"提示信息"}
        '''
        try:
            from btdockerModelV2.dockerSock import container

            sk_container = container.dockerContainer()
            container_list = sk_container.get_container()

            data = []
            # 获取前先检测数据库是否存在
            self.check_remark_table()
            dk_container_remark = dp.sql("dk_container_remark").select()
            self.check_table_dk_backup()
            dk_backup = dp.sql("dk_backup").select()
            for sk_c in container_list:
                try:
                    remark = [i['remark'] for i in dk_container_remark if i['container_id'] == sk_c["Id"]][0]
                except Exception as e:
                    remark = ""


                # 计算备份数量
                backup_count = 0
                for i in dk_backup:
                    if i['container_id'] == sk_c["Id"]:
                        backup_count += 1

                data.append({
                    "id": sk_c["Id"],
                    "name": dp.rename(sk_c['Names'][0].replace("/", "")),
                    "backup_count": backup_count,
                    "remark": remark,
                })

            return public.return_message(0, 0, data)
        except Exception as e:
            public.print_log(traceback.format_exc())
            return public.return_message(0, 0, [])

    # 获取容器列表
    def get_list(self, get):
        """
        获取所有容器列表 1
        :param get
        :return:
        """
        data = self._get_list(get)
        return public.return_message(0, 0, data)

    def _get_list(self, get):
        """
        获取所有容器列表 1
        :param get
        :return:
        """
        from btdockerModelV2.dockerSock import container
        sk_container = container.dockerContainer()
        sk_container_list = sk_container.get_container()

        container_to_top = self._get_container_to_top()
        #获取gpu数量
        try:
            from mod.project.docker.app.gpu.nvidia import NVIDIA
            gpu_count = NVIDIA().device_count
        except:
            gpu_count = 0
        data = {
            "online_cpus": dp.get_cpu_count(),
            "mem_total": dp.get_mem_info(),
            "container_list": [],
            "gpu": gpu_count
        }

        container_detail = list()
        grouped_by_status = dict()
        for sk_c in sk_container_list:
            struct_container = self.struct_container_list(sk_c, container_to_top)
            status = struct_container['status']
            grouped_by_status.setdefault(status, []).append(struct_container)
            container_detail.append(struct_container)

        if container_to_top:
            container_detail = sorted(container_detail, key=lambda x: (x['is_top'], x['created_time']), reverse=True)
            for key in grouped_by_status:
                grouped_by_status[key] = sorted(grouped_by_status[key], key=lambda x: (x['is_top'], x['created_time']), reverse=True)
        else:
            container_detail = sorted(container_detail, key=lambda x: x['created_time'], reverse=True)
            for key in grouped_by_status:
                grouped_by_status[key] = sorted(grouped_by_status[key], key=lambda x: x['created_time'], reverse=True)

        data['grouped_by_status'] = grouped_by_status
        data['container_list'] = container_detail
        return data

    # 获取容器的attr
    def get_container_attr(self, containers):
        c_list = containers.list(all=True)
        return [container_info.attrs for container_info in c_list]

    # 获取容器日志
    def get_logs11(self, get):
        """
        获取指定容器日志
        :param get:
        :return:
        """
        res = {
            "logs": "",
            'split_status': False,
            'split_type': 'day',
            'split_size': 1000,
            'split_hour': 2,
            'split_minute': 0,
            'save': '180'
        }

        try:
            container = self.docker_client(self._url).containers.get(get.id)
            if hasattr(get, 'time_search') and get.time_search != '':
                if not os.path.exists(container.attrs['LogPath']):
                    return public.return_message(-1, 0, public.lang("No container logging"))
                    # return public.return_message(0, 0, None)

                time_search = json.loads(str(get.time_search))
                since = int(time_search[0])
                until = int(time_search[1])
                r_logs = container.logs(since=since, until=until).decode()

            else:
                if not os.path.exists(container.attrs['LogPath']):
                    return public.return_message(-1, 0, public.lang("No container logging"))
                    # return public.return_message(0, 0, None)

                size = os.stat(container.attrs['LogPath']).st_size
                if size < 1048576:
                    r_logs = container.logs().decode()
                else:
                    tail = int(get.tail) if "tail" in get else 3000
                    r_logs = container.logs(tail=tail).decode()

            if hasattr(get, 'search') and get.search != '':
                if get.search:
                    r_logs = r_logs.split("\n")
                    r_logs = [i for i in r_logs if get.search in i]
                    r_logs = "\n".join(r_logs)

            res['logs'] = r_logs
            res['id'] = get.id
            res['name'] = dp.rename(container.attrs['Name'][1:])
            res['logs_path'] = container.attrs['LogPath']
            res['size'] = os.stat(container.attrs['LogPath']).st_size

            if public.M('sqlite_master').db('docker_log_split').where('type=? AND name=?',
                                                                      ('table', 'docker_log_split')).count():
                res['split_status'] = True if public.M('docker_log_split').where('pid=?', (get.id,)).count() else False
                data = public.M('docker_log_split').where('pid=?', (get.id,)).select()
                if data:
                    res['split_type'] = data[0]['split_type']
                    res['split_size'] = data[0]['split_size']
                    res['split_hour'] = data[0]['split_hour']
                    res['split_minute'] = data[0]['split_minute']
                    res['save'] = data[0]['save']
                else:
                    res['split_type'] = 'day'
                    res['split_size'] = 1000
                    res['split_hour'] = 2
                    res['split_minute'] = 0
                    res['save'] = '180'

            return public.return_message(0, 0, res)

        except Exception:
            return public.return_message(0, 0, res)


    def get_logs(self, get):
        """
        获取指定容器日志
        :param get:
        :return:
        """
        res = {
            "logs": "",
        }

        try:
            # 获取容器信息   名称 日志路径  大小
            container_info = self.docker_client(self._url).containers.get(get.id)

            if not os.path.exists(container_info.attrs['LogPath']):
                return public.return_message(0, 0, "")

            since = ""
            until = ""
            tail = ""
            if hasattr(get, 'time_search') and get.time_search != '':
                time_search = json.loads(str(get.time_search))
                since = int(time_search[0])
                until = int(time_search[1])
                size = os.stat(container_info.attrs['LogPath']).st_size
                if size > 1048576:
                    tail = int(get.tail) if "tail" in get else 10000

            options = {
                "since": since,
                "until": until,
                "tail": tail
              }
            from btdockerModelV2.dockerSock import container

            sk_container = container.dockerContainer()
            sk_container_logs = sk_container.get_container_logs(get.id,options)
            if hasattr(get, 'search') and get.search != '':
                if get.search:
                    sk_container_logs = sk_container_logs.split("\n")
                    sk_container_logs = [i for i in sk_container_logs if get.search in i]
                    sk_container_logs = "\n".join(sk_container_logs)

            res["logs"] = sk_container_logs
            res['id'] = get.id
            res['name'] = dp.rename(container_info.attrs['Name'][1:])
            res['logs_path'] = container_info.attrs['LogPath']
            res['size'] = os.stat(container_info.attrs['LogPath']).st_size

            return public.return_message(0, 0, res)

        except Exception:
            return public.return_message(0, 0, res)

    def get_logs_all(self, get):
        """
        获取所有容器的日志
        @param get:
        @return:
        """
        try:
            client = self.docker_client(self._url)
            if not client:
                return public.return_message(-1, 0, public.lang("docker connection failed"))
            containers = client.containers
            clist = [i.attrs for i in containers.list(all=True)]
            clist = [{'id': i['Id'], 'name': dp.rename(i['Name'][1:]), 'log_path': i['LogPath']} for i in clist]
            for i in clist:
                if os.path.exists(i['log_path']):
                    i['size'] = os.stat(i['log_path']).st_size
                else:
                    i['size'] = 0
            return public.return_message(0, 0, clist)
        except Exception as e:
            return public.return_message(-1, 0, e)

    def docker_split(self, get):
        """
        设置容器日志切割
        @param get:
        @return:
        """
        # {"pid": "3f225d2b41bcadb1b4bb73dc7521a35d1933cb1e1caa8ac61bd53cf718b9910c", "type": "del"}
        try:
            get.validate([
                Param('pid').Require().String(),
                Param('type').Require().String(),
            ], [
                public.validate.trim_filter(),
            ])
        except Exception as ex:
            public.print_log("error info: {}".format(ex))
            return public.return_message(-1, 0, ex)
        try:
            client = self.docker_client(self._url)
            if not client:
                return public.return_message(-1, 0, public.lang("docker connection failed"))
            containers = client.containers
            clist = [i.attrs for i in containers.list(all=True)]
            name = [dp.rename(i['Name'][1:]) for i in clist if i['Id'] == get.pid]
            if name:
                name = name[0]
            else:
                name = ''
            if not hasattr(get, 'type'):
                return public.return_message(-1, 0, public.lang("parameter error,Pass: type"))
            if not public.M('sqlite_master').db('docker_log_split').where('type=? AND name=?',
                                                                          ('table', 'docker_log_split')).count():
                public.M('docker_log_split').execute('''CREATE TABLE IF NOT EXISTS docker_log_split (
                id      INTEGER      PRIMARY KEY AUTOINCREMENT,
                name    text default '',
                pid    text default '',
                log_path     text default '',
                split_type text default '',
                split_size INTEGER default 0,
                split_hour INTEGER default 2,
                split_minute INTEGER default 0,
                save INTEGER default 180)''', ())
            if get.type == 'add':
                if "log_path" not in get or not get.log_path:
                    return public.return_message(-1, 0, public.lang("Container log directory does not exist, log cut cannot be set!"))

                if not (hasattr(get, 'pid') and hasattr(get, 'log_path') and
                        hasattr(get, 'split_type') and hasattr(get, 'split_size') and
                        hasattr(get, 'split_minute') and
                        hasattr(get, 'split_hour') and hasattr(get, 'save')):
                    return public.return_message(-1, 0, public.lang("parameter error"))
                data = {
                    'name': name,
                    'pid': get.pid,
                    'log_path': get.log_path,
                    'split_type': get.split_type,
                    'split_size': get.split_size,
                    'split_hour': get.split_hour,
                    'split_minute': get.split_minute,
                    'save': get.save
                }
                if public.M('docker_log_split').where('pid=?', (get.pid,)).count():
                    id = public.M('docker_log_split').where('pid=?', (get.pid,)).select()
                    public.M('docker_log_split').delete(id[0]['id'])
                public.M('docker_log_split').insert(data)
                return public.return_message(0, 0, public.lang("Opened successfully!"))
            elif get.type == 'del':
                id = public.M('docker_log_split').where('pid=?', (get.pid,)).getField('id')
                public.M('docker_log_split').where('id=?', (id,)).delete()
                return public.return_message(0, 0, public.lang("Closed successfully!"))
        except:
            return public.return_message(-1, 0, traceback.format_exc())

    def clear_log(self, get):
        """
        清空日志
        @param get:
        @return:
        """
        if not hasattr(get, 'log_path'):
            return public.return_message(-1, 0, public.lang("parameter error"))
        if not os.path.exists(get.log_path):
            return public.return_message(-1, 0, public.lang("The log file does not exist"))
        public.writeFile(get.log_path, '')
        return public.return_message(0, 0, public.lang("Log cleaning was successful!"))

    # 清理无用已停止未使用的容器
    def prune(self, get):
        """
        :param get:
        :return:
        """
        try:
            type = get.get("type/d", 0)
            if type == 0:
                res = self.docker_client(self._url).containers.prune()
                if not res['ContainersDeleted']:
                    return public.return_message(-1, 0, public.lang("No useless containers!"))
                dp.write_log("Delete useless containers successfully!")
                return public.return_message(0, 0, public.lang("successfully deleted!"))
            else:
                import docker
                client = docker.from_env()
                containers = client.containers.list(all=True)
                for container in containers:
                    container.remove(force=True)
                dp.write_log("Delete useless containers successfully!")
                return public.return_message(0, 0, public.lang("successfully deleted!"))
        except Exception as e:
            if "operation not permitted" in str(e):
                return public.return_message(-1, 0, public.lang("Please turn off enterprise tamper protection before trying again!"))
            return public.return_message(-1, 0, public.lang("failed to delete! {}", e))


    def update_restart_policy(self, get):
        """
        更新容器重启策略
        @param get:
        @return:
        """
        try:
            get.validate([
                Param('id').Require().String(),
                Param('restart_policy').Require(),
            ], [
                public.validate.trim_filter(),
            ])
        except Exception as ex:
            public.print_log("error info: {}".format(ex))
            return public.return_message(-1, 0, ex)

        try:
            # if "restart_policy" not in get:
            #     return public.return_message(-1, 0, public.lang("Parameter error, please pass in restart policy restart_policy!"))

            container = self.docker_client(self._url).containers.get(get.id)
            # 修复偶尔 go反序列化 报错
            if isinstance(get.restart_policy, str):
                import json
                restart_policy = get.restart_policy.replace("'", "\"")
                restart_policy = json.loads(restart_policy)
            else:
                restart_policy = get.restart_policy

            container.update(restart_policy=restart_policy)
            # container.update(restart_policy=get.restart_policy)
            # container.update(restart_policy= json.dumps(get.restart_policy))
            dp.write_log("Update container [{}] Restart policy successful!".format(container.attrs['Name']))
            return public.return_message(0, 0, public.lang("Update successfully!"))
        # except docker.errors.APIError as e:
        except Exception as e:
            public.print_log(traceback.format_exc())
            return public.return_message(-1, 0,  public.lang("Update failed! {}", e))

    '''
        @name 重命名指定容器
        @author wzz <2023/12/1 下午 3:13>
        @param 参数名<数据类型> 参数描述
        @return 数据类型
    '''

    def rename_container(self, get):
        """
        重命名指定容器
        @param get:
        @return:
        """
        try:
            get.validate([
                Param('id').Require().String(),
                Param('name').Require().String(),
            ], [
                public.validate.trim_filter(),
            ])
        except Exception as ex:
            public.print_log("error info: {}".format(ex))
            return public.return_message(-1, 0, ex)

        try:
            # 2023/12/6 上午 10:54 容器未启动时,不允许重命名
            container = self.docker_client(self._url).containers.get(get.id)
            if container.attrs['State']['Status'] != "running":
                return public.return_message(-1, 0, public.lang("The container is not started and cannot be renamed!"))
            config_path = "{}/config/name_map.json".format(public.get_panel_path())
            if not os.path.exists(config_path):
                public.writeFile(config_path, json.dumps({}))

            if public.readFile(config_path) == '':
                public.writeFile(config_path, json.dumps({}))

            name_map = json.loads(public.readFile(config_path))
            name_str = 'q18q' + public.GetRandomString(10).lower()
            name_map[name_str] = get.name
            get.name = name_str
            public.writeFile(config_path, json.dumps(name_map))

            container.rename(get.name)
            dp.write_log("Renaming container [{}] succeeded!".format(get.name))
            return public.return_message(0, 0, public.lang("Rename successfully!"))
        except docker.errors.APIError as e:
            return public.return_message(-1, 0,  public.lang("Renaming failed! {}", e))

    # 2024/2/23 上午 9:58 设置容器列表置顶
    def set_container_to_top(self, get):
        """
        设置容器列表置顶
        @param get:
        @return:
        """
        # {"type": "add", "container_name": "dk_wordpress-wordpress-1"}

        set_type = get.type if "type" in get else ""
        container_name = get.container_name if "container_name" in get else None

        if set_type not in ['add', 'del']: return public.return_message(-1, 0, public.lang( 'The type only supports add/del'))
        if container_name is None: return public.return_message(-1, 0, public.lang( 'Please select a container'))

        _conf_path = "{}/class_v2/btdockerModelV2/config/container_top.json".format(public.get_panel_path())
        if os.path.exists(_conf_path):
            container_top_conf = json.loads(public.readFile(_conf_path))
        else:
            container_top_conf = []

        if set_type == "add":
            container_top_conf = [i for i in container_top_conf if i != container_name]
            container_top_conf.insert(0, container_name)
            public.writeFile(_conf_path, json.dumps(container_top_conf))
            return public.return_message(0, 0, public.lang("Set top successfully!"))
        elif set_type == "del":
            container_top_conf.remove(container_name)
            public.writeFile(_conf_path, json.dumps(container_top_conf))
            return public.return_message(0, 0, public.lang("Unpinned successfully!"))

    # 2024/2/23 上午 9:58 获取容器列表置顶
    def _get_container_to_top(self):
        """
        获取容器列表置顶
        @return:
        """
        _conf_path = "{}/class_v2/btdockerModelV2/config/container_top.json".format(public.get_panel_path())
        if os.path.exists(_conf_path):
            container_top_conf = json.loads(public.readFile(_conf_path))
        else:
            container_top_conf = []

        return container_top_conf
    # 2024/3/13 下午 5:46 检查并创建备注的表
    def check_remark_table(self):
        '''
            @name 检查并创建备注的表
            @author wzz <2024/2/26 下午 5:59>
            @param "data":{"参数名":""} <数据类型> 参数描述
            @return dict{"status":True/False,"msg":"提示信息"}
        '''
        if not dp.sql('sqlite_master').where('type=? AND name=?', ('table', 'dk_container_remark')).count():
            dp.sql('dk_container_remark').execute(
                "CREATE TABLE `dk_container_remark` (`id` INTEGER PRIMARY KEY AUTOINCREMENT, `container_id` TEXT, `container_name` TEXT, `remark` TEXT, `addtime` TEXT)",
                ()
            )

    # 2024/2/26 下午 6:11 修改备注
    def set_container_remark(self, get):
        """
        设置容器备注
        @param get:
        @return:
        """

        try:
            get.validate([
                Param('id').Require().String(),
                Param('remark').Require().String(),
            ], [
                public.validate.trim_filter(),
            ])
        except Exception as ex:
            public.print_log("error info: {}".format(ex))
            return public.return_message(-1, 0, ex)

        # if not hasattr(get, 'remark'):
        #     return public.return_message(-1, 0, public.lang("Parameter error, Please pass in: remark!"))
        # if not hasattr(get, 'id'):
        #     return public.return_message(-1, 0, public.lang("Parameter error, Please pass in: id!"))

        container_id = get.id
        container_remark = public.xssencode2(get.remark)

        if not dp.sql("dk_container_remark").where("container_id=?", (container_id,)).count():
            dp.sql("dk_container_remark").insert({
                "container_id": container_id,
                "remark": container_remark,
            })
        else:
            dp.sql("dk_container_remark").where("container_id=?", (container_id,)).setField("remark", container_remark)

        return public.return_message(0, 0, public.lang("Setup successful!"))

    # 2024/2/27 上午 11:03 通过cgroup获取所有容器的cpu和内存使用情况
    def get_all_stats(self, get):
        """
        # 通过cgroup获取所有容器的cpu和内存使用情况
        @param get:
        @return:
        """
        if not hasattr(get, 'ws_callback'):
            return public.return_message(-1, 0, public.lang('Parameter error, Please pass in: ws_callback!'))
        if not hasattr(get, '_ws'):
            return public.return_message(-1, 0, public.lang('Parameter error, Please pass in: _ws!'))

        try:
            result = {
                "container_list": {},
            }
            # 获取所有容器列表
            container_list = self._get_list(get)["container_list"]
            for container in container_list:
                result["container_list"][container["name"]] = {
                    "id": container["id"],
                    "name": container["name"],
                    "image": container["image"],
                    "created_time": container["created_time"],
                    "status": container["status"],
                    "memory_usage": "",
                    "cpu_usage": "",
                    "pids": "",
                }

            get._ws.send(public.getJson(
                {
                    "data": result,
                    "ws_callback": get.ws_callback,
                    "msg": "Start getting CPU and memory usage for all containers!",
                    "status": True,
                    "end": False,
                }))

            while True:
                docker_stats_result = public.ExecShell(
                    "docker stats --all --no-stream --format "
                    "'{{.ID}},{{.Name}},{{.CPUPerc}},{{.MemUsage}},{{.MemPerc}},{{.NetIO}},{{.BlockIO}},{{.PIDs}};'"
                )[0]

                if not docker_stats_result:
                    get._ws.send(public.getJson(
                        {
                            "data": {},
                            "ws_callback": get.ws_callback,
                            "msg": "I haven't received any information about the running container resources!",
                            "status": True,
                            "end": True,
                        }))
                    return

                for i in docker_stats_result.split(";"):
                    if not i: continue
                    tmp = i.strip().split(",")
                    if len(tmp) == 0: continue
                    if len(tmp) == 1 and not tmp[0]: continue
                    container_name = dp.rename(tmp[1])
                    if container_name not in result["container_list"]:
                        continue

                    result["container_list"][container_name]["cpu_usage"] = tmp[2].strip("%")
                    result["container_list"][container_name]["mem_percent"] = tmp[4].strip("%")
                    result["container_list"][container_name]["memory_usage"] = {
                        "mem_usage": dp.byte_conversion(tmp[3].split("/")[0]),
                        "mem_limit": dp.byte_conversion(tmp[3].split("/")[1]),
                    }
                    result["container_list"][container_name]["pids"] = tmp[7]

                get._ws.send(public.getJson(
                    {
                        "data": result,
                        "ws_callback": get.ws_callback,
                        "msg": "Get CPU and memory usage for all containers successfully!",
                        "status": True,
                        "end": False,
                    }))

                time.sleep(0.1)


        except Exception as ex:
            # import traceback
            # public.print_log(traceback.format_exc())
            # public.print_log("error info: {}".format(ex))
            get._ws.send(public.getJson(
                {
                    "data": {},
                    "ws_callback": get.ws_callback,
                    "msg": "Failed to get CPU and memory usage for all containers!",
                    "status": True,
                    "end": True,
                }))
            return

    def check_table_dk_backup(self):
        '''
            @name 检查并创建表
            @return dict{"status":True/False,"msg":"提示信息"}
        '''
        if not dp.sql('sqlite_master').where('type=? AND name=?', ('table', 'dk_backup')).count():
            dp.sql('dk_backup').execute(
                "CREATE TABLE `dk_backup` (`id` INTEGER PRIMARY KEY AUTOINCREMENT, `type` INTEGER, `name` TEXT, `container_id` TEXT, `container_name` TEXT, `filename` TEXT, `size` INTEGER, `addtime` TEXT, `ps` STRING DEFAULT 'none', `cron_id` INTEGER DEFAULT 0 )",
                ()
            )
