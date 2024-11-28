#coding: utf-8
#-------------------------------------------------------------------
# aaPanel
#-------------------------------------------------------------------
# Copyright (c) 2015-2099 aaPanel(www.aapanel.com) All rights reserved.
#-------------------------------------------------------------------
# Author: zouhw <zhw@aapanel.com>
#-------------------------------------------------------------------

#------------------------------
# Docker模型
#------------------------------
import public
import docker.errors
import projectModel.bt_docker.dk_public as dp
class main:

    def __init__(self):
        self.alter_table()

    def alter_table(self):
        if not dp.sql('sqlite_master').where('type=? AND name=? AND sql LIKE ?',
                                               ('table', 'container', '%sid%')).count():
            dp.sql('container').execute("alter TABLE container add container_name VARCHAR DEFAULT ''", ())

    def docker_client(self,url):
        return dp.docker_client(url)

    # 添加容器
    def run(self,args):
        """
        :param name:容器名
        :param image: 镜像
        :param publish_all_ports 暴露所有端口 1/0
        :param ports  暴露某些端口 {'1111/tcp': ('127.0.0.1', 1111)}
        :param command 命令
        :param entrypoint  配置容器启动后执行的命令
        :param environment 环境变量 xxx=xxx 一行一条
        :param auto_remove 当容器进程退出时，在守护进程端启用自动移除容器。 0/1

        :param args:
        :return:
        """
        if not hasattr(args,'ports'):
            args.ports = False
        if not hasattr(args,'volumes'):
            args.volumes = False
        #检测端口是否已经在使用
        if args.ports:
            for i in args.ports:
                if dp.check_socket(args.ports[i]):
                    return public.returnMsg(False,"The server port [{}] has been used, please replace it with another port!".format(args.ports[i]))
        if not args.image:
            return public.returnMsg(False, "If there is no image selected, please go to the image tab to pull the image you need!")
        if args.restart_policy['Name'] == "always":
            args.restart_policy = {"Name":"always"}
        # return args.restart_policy
        # if
        args.cpu_quota = float(args.cpuset_cpus) * 100000
        # if not args.volumes:
        #     args.volumes = {"/sys/fs/cgroup":{"bind":"/sys/fs/cgroup","mode":"rw"}}
        # else:
        #     if not "/sys/fs/cgroup" in args.volumes:
        #         args.volumes['/sys/fs/cgroup'] = {"bind":"/sys/fs/cgroup","mode":"rw"}
        try:
            if not args.name:
                args.name = "{}-{}".format(args.image,public.GetRandomString(8))
            if int(args.cpu_quota) / 100000 > dp.get_cpu_count():
                return public.returnMsg(False,"The CPU quota has exceeded the number of cores available!")
            mem_limit_byte = dp.byte_conversion(args.mem_limit)
            if mem_limit_byte > dp.get_mem_info():
                return public.returnMsg(False, "The memory quota has exceeded the available number!")
            res = self.docker_client(args.url).containers.run(
                name=args.name,
                image=args.image,
                detach=True,
                publish_all_ports=True if args.publish_all_ports == "1" else False,
                ports=args.ports if args.ports else None,
                command=args.command,
                auto_remove=True if str(args.auto_remove) == "1" else False,
                environment=dp.set_kv(args.environment), #"HOME=/value\nHOME11=value1"
                volumes=args.volumes, #一个字典对象 {'服务器路径/home/user1/': {'bind': '容器路径/mnt/vol2', 'mode': 'rw'},'/var/www': {'bind': '/mnt/vol1', 'mode': 'ro'}}
                # cpuset_cpus=args.cpuset_cpus ,#指定容器使用的cpu个数
                cpu_quota=int(args.cpu_quota),
                mem_limit=args.mem_limit, #b,k,m,g
                restart_policy=args.restart_policy,
                labels=dp.set_kv(args.labels), #"key=value\nkey1=value1"
                tty=True,
                stdin_open=True,
                privileged=True

            )
            if res:
                pdata = {
                    "cpu_limit": str(args.cpu_quota),
                    "container_name": args.name
                }
                dp.sql('container').insert(pdata)
                public.set_module_logs('docker', 'run_container', 1)
                dp.write_log("Create container [{}] successful!".format(args.name))
                return public.returnMsg(True,"The container was created successfully!")
            return public.returnMsg(False, 'Create failed!')
        except docker.errors.APIError as e:
            if "container to be able to reuse that name." in str(e):
                return public.returnMsg(False, "The container name already exists!")
            if "Invalid container name" in str(e):
                return public.returnMsg(False, "The container name is illegal, please do not use Chinese container name!")
            if "bind: address already in use" in str(e):
                port = ""
                for i in args.ports:
                    if ":{}:".format(args.ports[i]) in str(e):
                        port = args.ports[i]
                args.id = args.name
                self.del_container(args)
                return public.returnMsg(False, "Server port {} is in use! Please change other ports".format(port))
            return public.returnMsg(False, 'Create failed! {}'.format(public.get_error_info()))

    # 保存为镜像
    def commit(self,args):
        """
        :param repository       推送到的仓库
        :param tag              镜像标签 jose:v1
        :param message          提交的信息
        :param author           镜像作者
        :param changes
        :param conf dict
        :param path 导出路径
        :param name 导出文件名
        :param args:
        :return:
        """
        if not hasattr(args,'conf') or not args.conf:
            args.conf = None
        if args.repository == "docker.io":
            args.repository = ""
        container = self.docker_client(args.url).containers.get(args.id)
        container.commit(
            repository=args.repository if args.repository else None,
            tag=args.tag if args.tag else None,
            message=args.message if args.message else None,
            author=args.author if args.author else None,
            # changes=args.changes if args.changes else None,
            conf=args.conf
        )
        if hasattr(args,"path") and args.path:
            args.id = "{}:{}".format(args.name,args.tag)
            import projectModel.bt_docker.dk_image as dk
            return dk.main().save(args)
        dp.write_log("Submitting container [{}] as image [{}] succeeded!".format(container.attrs['Name'],args.tag))
        return public.returnMsg(True,"提交成功！")

    # 容器执行命令
    def docker_shell(self, args):
        """
        :param container_id
        :param args:
        :return:
        """
        try:
            self.docker_client(args.url).containers.get(args.container_id)
            cmd = 'docker container exec -it {} /bin/bash'.format(args.container_id)
            return public.returnMsg(True, cmd)
        except docker.errors.APIError as ex:
            return public.returnMsg(False, 'Failed to get container')

    # 导出容器为tar 没有导入方法，目前弃用
    def export(self,args):
        """
        :param path 保存路径
        :param name 包名
        :param args:
        :return:
        """
        from os import path as ospath
        from os import makedirs as makedirs
        try:
            if "tar" in args.name:
                file_name = '{}/{}'.format(args.path,args.name)
            else:
                file_name = '{}/{}.tar'.format(args.path, args.name)
            if not ospath.exists(args.path):
                makedirs(args.path)
            public.writeFile(file_name,'')
            f = open(file_name, 'wb')
            container = self.docker_client(args.url).containers.get(args.id)
            data = container.export()
            for i in data:
                f.write(i)
            f.close()
            return public.returnMsg(True, "Successfully exported to: {}".format(file_name))
        except:
            return public.returnMsg(False, 'Operation failed:' + str(public.get_error_info()))

    # 删除容器
    def del_container(self,args):
        """
        :return:
        """
        import projectModel.bt_docker.dk_public as dp
        container = self.docker_client(args.url).containers.get(args.id)
        container.remove(force=True)
        dp.sql("cpu_stats").where("container_id=?", (args.id,)).delete()
        dp.sql("io_stats").where("container_id=?", (args.id,)).delete()
        dp.sql("mem_stats").where("container_id=?", (args.id,)).delete()
        dp.sql("net_stats").where("container_id=?", (args.id,)).delete()
        dp.sql("container").where("container_nam=?", (container.attrs['Name'])).delete()
        dp.write_log("Delete container [{}] succeeded!".format(container.attrs['Name']))
        return public.returnMsg(True,"Successfully deleted!")

    # 设置容器状态
    def set_container_status(self,args):
        import time
        container = self.docker_client(args.url).containers.get(args.id)
        if args.act == "start":
            container.start()
        elif args.act == "stop":
            container.stop()
        elif args.act == "pause":
            container.pause()
        elif args.act == "unpause":
            container.unpause()
        elif args.act == "reload":
            container.reload()
        else:
            container.restart()
        time.sleep(1)
        tmp = self.docker_client(args.url).containers.get(args.id)
        return {"name":container.attrs['Name'].replace('/',''),"status":tmp.attrs['State']['Status']} #返回设置后的状态


    # 停止容器
    def stop(self,args):
        """
        :param url
        :param id
        :param args:
        :return:
        """
        try:
            args.act = "stop"
            data = self.set_container_status(args)
            if data['status'] != "exited":
                return public.returnMsg(False, "Stop failing!")
            dp.write_log("Stop container [{}] succeeded!".format(data['name']))
            return public.returnMsg(True, "Stop success!")
        except docker.errors.APIError as e:
            if "is already paused" in str(e):
                return public.returnMsg(False,"The container has been suspended!")
            if "No such container" in str(e):
                return public.returnMsg(True, "The container has been stopped and deleted because the container has the option to automatically delete after stopping!")
            return public.returnMsg(False,"Stop failing!{}".format(e))

    def start(self,args):
        """
        :param url
        :param id
        :param args:
        :return:
        """
        try:
            args.act = "start"
            data = self.set_container_status(args)
            if data['status'] != "running":
                return public.returnMsg(False, "Startup failed!")
            dp.write_log("Start the container [{}] successfully!".format(data['name']))
            return public.returnMsg(True, "Started successfully!")
        except docker.errors.APIError as e:
            if "cannot start a paused container, try unpause instead" in str(e):
                return self.unpause(args)

    def pause(self,args):
        """
        Pauses all processes within this container.
        :param url
        :param id
        :param args:
        :return:
        """
        try:
            args.act = "pause"
            data = self.set_container_status(args)
            if data['status'] != "paused":
                return public.returnMsg(False, "Container pause failed!")
            dp.write_log("Suspended container [{}] succeeded!".format(data['name']))
            return public.returnMsg(True, "Container paused successfully!")
        except docker.errors.APIError as e:
            if "is already paused" in str(e):
                return public.returnMsg(False,"The container has been suspended!")
            if "is not running" in str(e):
                return public.returnMsg(False, "The container is not started and cannot be paused!")
            if "is not paused" in str(e):
                return public.returnMsg(False, "The container has not been suspended!")
            return str(e)

    def unpause(self,args):
        """
        unPauses all processes within this container.
        :param url
        :param id
        :param args:
        :return:
        """
        try:
            args.act = "unpause"
            data = self.set_container_status(args)
            if data['status'] != "running":
                return public.returnMsg(False, "Startup failed!")
            dp.write_log("Unpausing the container [{}] succeeded!".format(data['name']))
            return public.returnMsg(True, "Container unpause succeeded!")
        except docker.errors.APIError as e:
            if "is already paused" in str(e):
                return public.returnMsg(False,"The container has been suspended!")
            if "is not running" in str(e):
                return public.returnMsg(False, "The container is not started and cannot be paused!")
            if "is not paused" in str(e):
                return public.returnMsg(False, "The container has not been suspended!")
            return str(e)

    def reload(self,args):
        """
        Load this object from the server again and update attrs with the new data.
        :param url
        :param id
        :param args:
        :return:
        """
        args.act = "reload"
        data = self.set_container_status(args)
        if data['status'] != "running":
            return public.returnMsg(False, "Startup failed!")
        dp.write_log("Reloading container [{}] succeeded!".format(data['name']))
        return public.returnMsg(True, "Container reload succeeded!")

    def restart(self,args):
        """
        Restart this container. Similar to the docker restart command.
        :param url
        :param id
        :param args:
        :return:
        """
        args.act = "restart"
        data = self.set_container_status(args)
        if data['status'] != "running":
            return public.returnMsg(False, "Startup failed!")
        dp.write_log("Restarting the container [{}] succeeded!".format(data['name']))
        return public.returnMsg(True, "The container restarted successfully!")

    def get_container_ip(self,container_networks):
        data = list()
        for network in container_networks:
            data.append(container_networks[network]['IPAddress'])
        return data

    def get_container_path(self,detail):
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

    # 获取容器列表所需的外部数据
    def get_other_data_for_container_list(self,args):
        import projectModel.bt_docker.dk_image as di
        import projectModel.bt_docker.dk_volume as dv
        import projectModel.bt_docker.dk_compose as dc
        import projectModel.bt_docker.dk_setup as ds
        # 获取镜像列表
        images = di.main().image_list(args)
        if images['status']:
            images = images['msg']['images_list']
        else:
            images = list()
        # 获取卷列表
        volumes = dv.main().get_volume_list(args)
        if volumes['status']:
            volumes = volumes['msg']['volume']
        else:
            volumes = list()
        # 获取模板列表
        template = dc.main().template_list(args)
        if template['status']:
            template = template['msg']['template']
        else:
            template = list()
        online_cpus = dp.get_cpu_count()
        mem_total = dp.get_mem_info()
        docker_setup = ds.main()
        return {
            "images":images,
            "volumes":volumes,
            "template":template,
            "online_cpus":online_cpus,
            "mem_total":mem_total,
            "installed":docker_setup.check_docker_program(),
            "service_status":docker_setup.get_service_status()
        }

    # 获取容器列表
    def get_list(self,args):
        """
        :param url
        :return:
        """
        # 判断docker是否安装
        import projectModel.bt_docker.dk_setup as ds
        data = self.get_other_data_for_container_list(args)
        if not ds.main().check_docker_program():
            data['container_list'] = list()
            return public.returnMsg(True,data)
        client = self.docker_client(args.url)
        if not client:

            return public.returnMsg(True,data)
        containers = client.containers
        attr_list = self.get_container_attr(containers)
        # data = self.get_other_data_for_container_list(args)
        container_detail = list()
        for attr in attr_list:
            cpu_usage = dp.sql("cpu_stats").where("container_id=?",(attr["Id"],)).select()
            if cpu_usage and isinstance(cpu_usage,list):
                cpu_usage = cpu_usage[-1]['cpu_usage']
            else:
                cpu_usage = "0.0"
            tmp = {
                "id": attr["Id"],
                "name": attr['Name'].replace("/",""),
                "status": attr["State"]["Status"],
                "image": attr["Config"]["Image"],
                "time": attr["Created"],
                "merged": self.get_container_path(attr),
                "ip": self.get_container_ip(attr["NetworkSettings"]['Networks']),
                "ports": attr["NetworkSettings"]["Ports"],
                "detail": attr,
                "cpu_usage":cpu_usage if attr["State"]["Status"] == "running" else ""
            }
            container_detail.append(tmp)
        data['container_list'] = container_detail
        return public.returnMsg(True,data)

    # 获取容器的attr
    def get_container_attr(self,containers):
        c_list = containers.list(all=True)
        return [container_info.attrs for container_info in c_list]

    # 获取容器日志
    def get_logs(self,args):
        """
        :param url
        :param id
        :param args:
        :return:
        """
        try:
            container = self.docker_client(args.url).containers.get(args.id)
            res = container.logs().decode()
            return public.returnMsg(True,res)
        except docker.errors.APIError as e:
            if "configured logging driver does not support reading" in str(e):
                return public.returnMsg(False,"The container has no log files!")



    # 登录容器


    # 获取容器配置文件