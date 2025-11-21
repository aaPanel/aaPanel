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
import time
import gettext
_ = gettext.gettext

import public
import traceback
from btdockerModelV2 import containerModel as dc
from btdockerModelV2 import dk_public as dp
from btdockerModelV2.dockerBase import dockerBase
from public.validate import Param


class main(dockerBase):

    def get_docker_compose_version(self):
        try:
            import subprocess
            result = subprocess.run(["docker-compose", "version", "--short"], capture_output=True, text=True)
            version_str = result.stdout.strip()
            major, minor, patch = map(int, version_str.split('.'))
            return major, minor, patch
        except Exception as e:
            print("Error:", e)
            return None

    # 验证配置文件
    def check_conf(self, path):
        # 2024/3/21 下午 5:58 检测path是否存在中文，如果有就false return
        if public.check_chinese(path):
            return public.return_message(-1, 0, public.lang("The file path cannot contain Chinese characters!"))

        # 2024/3/20 下午 4:33 获取docker-compose的版本，如果大于v2.24.7则不需要检测，比如是v2.25，解决高版本的docker-compose
        version = self.get_docker_compose_version()
        if version and version > (2, 24, 7):
            tmpfile = public.md5(path)
            public.ExecShell(r"\cp -r {} /tmp/{}.yml".format(path, public.md5(path)))
            public.ExecShell("sed -i '/version:/d' /tmp/{}.yml".format(tmpfile))
            path = "/tmp/{}.yml".format(tmpfile)

        shell = "/usr/bin/docker-compose -f {} config".format(path)
        a, e = public.ExecShell(shell)
        if e and "setlocale: LC_ALL: cannot change locale (en_US.UTF-8)" not in e:
            return public.return_message(-1, 0, public.lang("Detection failed: {}", e))
        return public.return_message(0, 0, public.lang("Detection passes!"))

    # 用引导方式创建模板
    def add_template_gui(self, get):
        """
        用引导方式创建模板
        :param name                     模板名
        :param description              模板描述
        :param data                     模板内容 {"version":3,"services":{...}...}
        :param get:
        模板文件参数：
        version 2/3version
            2: 仅支持单机
            3：支持单机和多机模式
        services:
            多个容器的集合
            下一层执行服务名
            如web1,服务名下面指定服务的变量
            web1:
                build: .                    基于dockerfile构建一个镜像
                image: nginx                服务所使用的镜像为nginx
                container_name: "web"       容器名
                depends_on:                 该服务在db服务启动后再启动
                  - db
                ports:
                  - "6061:80"               将容器的80端口映射到主机的6061端口
                networks:
                  - frontend                该容器所在的网络
                deploy:                     指定与部署和运行服务相关的配置(在使用 swarm时才会生效)
                  replicas: 6               6个副本
                  update_config:
                    parallelism: 2
                    delay: 10s
                  restart_policy:
                    condition: on-failure
        其他详细描述可以参考 https://docs.docker.com/compose/compose-file/compose-file-v3
        :return:
        """
        import yaml
        path = "{}/template".format(self.compose_path)
        file = "{}/{}.yaml".format(path, get.name)
        if not os.path.exists(path):
            os.makedirs(path)
        data = json.loads(get.data)
        yaml.dump(data, file)

    def get_template_kw(self, get):
        data = {
            "version": "",
            "services": {
                "server_name_str": {  # 用户输入
                    "build": {
                        "context": "str",
                        "dockerfile": "str",
                        "get": [],
                        "cache_from": [],
                        "labels": [],
                        "network": "str",
                        "shm_size": "str",
                        "target": "str"
                    },
                    "cap_add": "",
                    "cap_drop": "",
                    "cgroup_parent": "str",
                    "command": "str",
                    "configs": {
                        "my_config_str": []
                    },
                    "container_name": "str",
                    "credential_spec": {
                        "file": "str",
                        "registry": "str"
                    },
                    "depends_on": [],
                    "deploy": {
                        "endpoint_mode": "str",
                        "labels": {
                            "key": "value"
                        },
                        "mode": "str",
                        "placement": [{"key": "value"}],
                        "max_replicas_per_node": "int",
                        "replicas": "int",
                        "resources": {
                            "limits": {
                                "cpus": "str",
                                "memory": "str",
                            },
                            "reservations": {
                                "cpus": "str",
                                "memory": "str",
                            },
                            "restart_policy": {
                                "condition": "str",
                                "delay": "str",
                                "max_attempts": "int",
                                "window": "str"
                            }
                        }
                    }
                }
            }
        }

    # 创建项目配置文件
    def add_template(self, get):
        """
        添加一个模板文件
        :param name                     模板名
        :param remark              模板描述
        :param data                     模板内容
        :param get:
        :return:
        """
        import re
        name = get.name
        if not re.search(r"^[\w\.\-]+$", name):
            return public.return_message(-1, 0, public.lang("Template names cannot contain special characters; only letters, numbers, underscores, dots, and underscores are supported"))

        template_list = self._template_list(get)
        for template in template_list:
            if name == template['name']:
                return public.return_message(-1, 0, public.lang("This template name already exists!"))

        path = "{}/{}/template".format(self.compose_path, name)
        file = "{}/{}.yaml".format(path, name)
        if not os.path.exists(path):
            os.makedirs(path)
        public.writeFile(file, get.data)

        check_res = self.check_conf(file)
        if check_res['status'] == -1:
            if os.path.exists(file):
                os.remove(file)
            return public.return_message(-1, 0, check_res['message'])

        pdata = {
            "name": name,
            "remark": public.xsssec(get.remark),
            "path": file
        }
        dp.sql("templates").insert(pdata)
        dp.write_log("Added template [{}] successfully!".format(name))
        public.set_module_logs('docker', 'add_template', 1)
        return public.return_message(0, 0, public.lang("Template added successfully!"))

    def edit_template(self, get):
        """
        :param id 模板id
        :param data 模板内容
        :param remark              模板描述
        :param get:
        :return:
        """
        template_info = dp.sql("templates").where("id=?", (get.id,)).find()
        if not template_info:
            return public.return_message(-1, 0, public.lang("Did not change the template!"))

        # if "data" not in get:
        #     return public.return_message(-1, 0, public.lang("Template content format error, please enter a valid docker-compose template!"))
        #
        # if "version" not in get.data:
        #     return public.return_message(-1, 0, public.lang("Template content format error, please enter a valid docker-compose template!"))

        public.writeFile(template_info['path'], get.data)
        check_res = self.check_conf(template_info['path'])
        if check_res['status'] == -1:
            return public.return_message(-1, 0, check_res['message'])
        pdata = {
            "name": get.name,
            "remark": public.xsssec(get.remark),
            "path": template_info['path']
        }
        dp.sql("templates").where("id=?", (get.id,)).update(pdata)
        dp.write_log("Edit template [{}] successful!".format(template_info['name']))
        return public.return_message(0, 0, public.lang("Modified template successfully!"))

    def get_template(self, get):
        """
        id 模板ID
        获取模板内容
        :return:
        """

        # 校验参数
        try:
            get.validate([
                Param('template_id').Require().Integer(),
            ], [
                public.validate.trim_filter(),
            ])
        except Exception as ex:
            public.print_log("error info: {}".format(ex))
            return public.return_message(-1, 0,  str(ex))

        template_info = dp.sql("templates").where("id=?", (get.template_id,)).find()
        if not template_info:
            return public.return_message(-1, 0, public.lang("This template was not found!"))

        return public.return_message(0, 0, public.readFile(template_info['path']))

    def template_list(self, get):
        """
        获取所有模板
        :param get:
        :return:
        """
        template = dp.sql("templates").select()[::-1]
        if not isinstance(template, list):
            template = []

        return public.return_message(0, 0, template)

    # 内部调用 不改响应格式
    def _template_list(self, get):
        """
        获取所有模板
        :param get:
        :return:
        """
        template = dp.sql("templates").select()[::-1]
        if not isinstance(template, list):
            template = []

        return template
    #  检查模板是否被使用
    def check_use_template(self, get):
        """
        检查模板是否被使用
        :param get:
        :return:
        """
        template_info = dp.sql("stacks").where("template_id=?", (get.id,)).find()
        if not template_info:
            return public.return_message(-1, 0,  "")
        return public.return_message(0, 0, template_info["name"])

    def remove_template(self, get):
        """
        删除模板
        :param template_id
        :param get:
        :return:
        """
        # 校验参数
        try:
            get.validate([
                Param('template_id').Require().Integer(),
            ], [
                public.validate.trim_filter(),
            ])
        except Exception as ex:
            public.print_log("error info: {}".format(ex))
            return public.return_message(-1, 0, str(ex))

        data = dp.sql("templates").where("id=?", (get.template_id,)).find()
        if not data:
            return public.return_message(-1, 0, public.lang("This template was not found!"))
        if os.path.exists(data['path']):
            # 删除模板文件 目录不处理
            try:
                os.remove(data['path'])
            except:
                pass

        get.id = get.template_id

        if self.check_use_template(get)['status']==0:
            # 模板已被使用
            if hasattr(get, "status"):
                template_info = dp.sql("stacks").where("template_id=?", (get.template_id,)).find()
                if os.path.exists(template_info["path"]):
                    public.ExecShell("/usr/bin/docker-compose -f {} down".format(template_info["path"]))
                else:
                    stdout, stderr = public.ExecShell("docker-compose ls --format json")
                    try:
                        info = json.loads(stdout)
                    except:
                        info = []
                    for i in info:
                        if i['Name'] == public.md5(template_info['name']):
                            public.ExecShell("/usr/bin/docker-compose -p {} down".format(i['Name']))
                            break
                dp.sql("stacks").delete(id=template_info["id"])

        dp.sql("templates").delete(id=get.template_id)
        dp.write_log("Delete template [{}] successfully!".format(data['name']))
        return public.return_message(0, 0, public.lang("successfully delete!"))

    def edit_project_remark(self, get):
        """
        编辑项目
        :param project_id 项目
        :param remark备注
        :param get:
        :return:
        """
        stacks_info = dp.sql("stacks").where("id=?", (get.project_id,)).find()
        if not stacks_info:
            return public.return_message(-1, 0, public.lang("The item was not found!"))
        pdata = {
            "remark": public.xsssec(get.remark)
        }
        dp.write_log("Comment for project [{}] changed successfully [{}] --> [{}]!".format(stacks_info['name'],
                                                                                           stacks_info['remark'],
                                                                                           public.xsssec(get.remark)))
        dp.sql("stacks").where("id=?", (get.project_id,)).update(pdata)

    def edit_template_remark(self, get):
        """
        编辑项目
        :param templates_id 项目
        :param remark备注
        :param get:
        :return:
        """
        stacks_info = dp.sql("templates").where("id=?", (get.templates_id,)).find()
        if not stacks_info:
            return public.return_message(-1, 0, public.lang("The template was not found!"))
        pdata = {
            "remark": public.xsssec(get.remark)
        }
        dp.write_log(
            "Modify template [{}] Remark successful [{}] --> [{}]!".format(stacks_info['name'], stacks_info['remark'],
                                                                           public.xsssec(get.remark)))
        dp.sql("templates").where("id=?", (get.templates_id,)).update(pdata)

    def create_project_in_path(self, name, path):
        shell = "cd {} && /usr/bin/docker-compose -p {} up -d &> {}".format("/".join(path.split("/")[:-1]), name,
                                                                            self._log_path)
        public.ExecShell(shell)

    def create_project_in_file(self, project_name, file):
        project_path = "{}/{}".format(self.compose_path, project_name)
        project_file = "{}/docker-compose.yaml".format(project_path)
        if not os.path.exists(project_path):
            os.makedirs(project_path)
        template_content = public.readFile(file)
        public.writeFile(project_file, template_content)
        shell = "/usr/bin/docker-compose -p {} -f {} up -d &> {}".format(project_name, project_file, self._log_path)
        public.ExecShell(shell)

    def check_project_container_name(self, template_data, get):
        """
        检测模板文件中的容器名是否已经存在
        :return:
        """
        import re
        data = []
        template_container_name = re.findall("container_name\s*:\s*[\"\']+(.*)[\'\"]", template_data)
        # 调用容器列表接口 选择不改统一返回的
        container_list = dc.main()._get_list(get)

        container_list = container_list['container_list']
        for container in container_list:
            if container['name'] in template_container_name:
                data.append(container['name'])
        if data:
            return public.return_message(-1, 0, public.lang("The container name already exists!: <br>[{}]", ", ".join(data)))
        # 获取模板所使用的端口
        rep = r"(\d+):\d+"
        port_list = re.findall(rep, template_data)
        for port in port_list:
            if dp.check_socket(port):

                return public.return_message(-1, 0, public.lang("This port [{}] is already used by other templates", port))

    # 创建项目
    def create(self, get):
        """
        :param project_name         项目名
        :param remark          描述
        :param template_id             模板ID
        :param rags:
        :return:
        """
        # {"template_id": "13", "project_name": "dedf2f", "remark": "从本地添加asd"}
        # 校验参数
        try:
            get.validate([
                Param('template_id').Require().Integer(),
                Param('project_name').Require().String().Xss(),
                Param('remark').Require().String(),
            ], [
                public.validate.trim_filter(),
            ])
        except Exception as ex:
            public.print_log("error info: {}".format(ex))
            return public.return_message(-1, 0, str(ex))

        try:
            project_name = public.md5(public.xsssec(get.project_name))
            if "template_id" not in get:
                return public.return_message(-1, 0, public.lang("Parameter error, please pass in template_id!"))
            template_id = get.template_id
            template_info = dp.sql("templates").where("id=?", template_id).find()
            if len(template_info) < 1:
                return public.return_message(-1, 0, public.lang("This template was not found, or file is corrupt!"))

            if not os.path.exists(template_info['path']):
                return public.return_message(-1, 0,  public.lang("Template file does not exist"))

            template_exist = dp.sql("stacks").where("template_id=?", (template_id,)).find()
            if template_exist:
                return public.return_message(-1, 0,
                                             public.lang("Template [{}] has been deployed by project: [{}], please change a template and try again!",
                                                 template_info['name'], template_exist['name']))

            name_exist = self.check_project_container_name(public.readFile(template_info['path']), get)
            if name_exist:
                return public.return_message(-1, 0, name_exist['message'])

            stacks_info = dp.sql("stacks").where("name=?", (public.xsssec(get.project_name))).find()
            if not stacks_info:
                pdata = {
                    "name": public.xsssec(get.project_name),
                    "status": "1",
                    "path": template_info['path'],
                    "template_id": template_id,
                    "time": time.time(),
                    "remark": public.xsssec(get.remark)
                }
                dp.sql("stacks").insert(pdata)
            else:
                return public.return_message(-1, 0, public.lang("The project name already exists!"))

            if template_info['add_in_path'] == 1:
                self.create_project_in_path(
                    project_name,
                    template_info['path']
                )
            else:
                self.create_project_in_file(
                    project_name,
                    template_info['path']
                )
            dp.write_log("Project [{}] deployed successfully!".format(public.xsssec(get.project_name)))
            public.set_module_logs('docker', 'add_project', 1)
            return public.return_message(0, 0, public.lang("Successful deployment!"))
        except Exception as ex:
            public.print_log(traceback.format_exc())
            return public.return_message(-1, 0, str(ex))

    def compose_project_list(self, get):
        """
        获取所有已部署的项目列表
        @param get:
        """
        compose_project = dp.sql("stacks").select()
        # public.print_log("部署项目  {}".format(compose_project))
        try:
            cmd_result = public.ExecShell("/usr/bin/docker-compose ls -a --format json")[0]
            if "Segmentation fault" in cmd_result:
                return public.return_message(-1, 0, public.lang("docker-compose is too low, please upgrade to the latest version!"))
            result = json.loads(cmd_result)
        except:
            result = []

        for i in compose_project:
            for j in result:
                if public.md5(i['name']) in j['Name']:
                    i['run_status'] = j['Status'].split("(")[0].lower()
                    break
                else:
                    i['run_status'] = "exited"

        return public.return_message(0, 0, compose_project)

    def project_container_count(self, get):
        """
        获取项目容器数量
        @param get:
        @return:
        """
        from btdockerModelV2.dockerSock import container
        sk_container = container.dockerContainer()
        sk_container_list = sk_container.get_container()

        stacks_info = dp.sql("stacks").select()
        net_info = []

        for i in stacks_info:
            count = 0
            for c in sk_container_list:
                if public.md5(i['name']) in c["Names"][0].replace("/", ""):
                    count += 1
                    continue

                if 'com.docker.compose.project' in c.keys():
                    if "com.docker.compose.project.config_files" in c:
                        if public.md5(i['name']) in c['com.docker.compose.project.config_files']:
                            count += 1
                            continue

                        if public.md5(i['name']) in public.md5(c['com.docker.compose.project.config_files']):
                            count += 1
                            continue

                if 'com.docker.compose.project' in c['Labels'].keys():
                    if public.md5(i['name']) in c['Labels']['com.docker.compose.project.config_files']:
                        count += 1
                        continue

                    if public.md5(i['name']) in public.md5(c['Labels']['com.docker.compose.project.config_files']):
                        count += 1
                        continue

            net_info.append(count)

        return public.return_message(0, 0, net_info)

    def get_compose_container(self, get):
        """
        目前仅支持本地 url: unix:///var/run/docker.sock
        """
        # 校验参数
        try:
            get.validate([
                Param('name').Require().String(),
            ], [
                public.validate.trim_filter(),
            ])
        except Exception as ex:
            public.print_log("error info: {}".format(ex))
            return public.return_message(-1, 0, str(ex))

        from btdockerModelV2.dockerSock import container
        sk_container = container.dockerContainer()
        sk_container_list = sk_container.get_container()

        project_container_list = []
        for c in sk_container_list:
            if public.md5(get.name) in dp.rename(c["Names"][0].replace("/", "")):
                project_container_list.append(dc.main().struct_container_list(c))
                continue

            if 'com.docker.compose.project' in c.keys():
                if "com.docker.compose.project.config_files" in c:
                    if public.md5(get.name) in c['com.docker.compose.project.config_files']:
                        project_container_list.append(dc.main().struct_container_list(c))

                    if public.md5(get.name) in public.md5(c['com.docker.compose.project.config_files']):
                        project_container_list.append(dc.main().struct_container_list(c))

            if 'com.docker.compose.project' in c['Labels'].keys():
                if "com.docker.compose.project.config_files" in c['Labels']:
                    if public.md5(get.name) in c['Labels']['com.docker.compose.project.config_files']:
                        project_container_list.append(dc.main().struct_container_list(c))

                    if public.md5(get.name) in public.md5(c['Labels']['com.docker.compose.project.config_files']):
                        project_container_list.append(dc.main().struct_container_list(c))

        return public.return_message(0, 0, project_container_list)

    # 删除项目
    def remove(self, get):
        """
        project_id          数据库记录的项目ID
        :param get:
        :return:
        """
        # 校验参数
        try:
            get.validate([
                Param('project_id').Require().Integer(),
            ], [
                public.validate.trim_filter(),
            ])
        except Exception as ex:
            public.print_log("error info: {}".format(ex))
            return public.return_message(-1, 0, str(ex))

        statcks_info = dp.sql("stacks").where("id=?", (get.project_id,)).find()
        if not statcks_info:
            return public.return_message(-1, 0, public.lang("The project name was not found!"))
        container_name = public.ExecShell("docker ps --format \"{{.Names}}\"")
        if statcks_info['name'] in container_name[0]:
            shell = f"/usr/bin/docker-compose -p {statcks_info['name']} -f {statcks_info['path']} down &> {self._log_path}"
        else:
            shell = f"/usr/bin/docker-compose -p {public.md5(statcks_info['name'])} -f" \
                    f" {statcks_info['path']} down &> {self._log_path}"
        public.ExecShell(shell)
        dp.sql("stacks").delete(id=get.project_id)

        dp.write_log("Delete project [{}] success!".format(statcks_info['name']))
        return public.return_message(0, 0, public.lang("successfully delete!"))

    def prune(self, get):
        """
        删除所有没有容器的项目
        @param get:
        @return:
        """
        stacks_info = dp.sql("stacks").select()
        container_name = public.ExecShell("docker ps --format \"{{.Names}}\"")[0]
        # 正在运行的容器为空 直接返回结果
        if container_name == "":
            return public.return_message(0, 0, public.lang("The cleanup was successful!"))

        container_name = container_name.split("\n")

        # 数据库列表信息
        for i in stacks_info:
            # 2024/3/21 下午 6:26 如果i['name']在container_name[0]中，说明容器还在运行，不删除
            is_run = False
            docker_name = public.ExecShell("grep 'container_name' {}".format(i["path"]))[0]

            #  实际运行列表
            for j in container_name:
                if j == "": continue
                if public.md5(i['name']) in j or j in docker_name:
                    is_run = True
                    break

            if is_run: continue
            shell = "/usr/bin/docker-compose -f {} down &> {}".format(i['path'], self._log_path)
            public.ExecShell(shell)
            dp.sql("stacks").delete(id=i['id'])
            dp.write_log("Cleanup project [{}] successful!".format(i['name']))
        return public.return_message(0, 0, public.lang("Clean up successfully!"))


    def set_compose_status(self, get):
        """
        设置项目状态
        @param get:
        @return:
        """
        try:
            get.validate([

                Param('status').Require().String('in', ['start', 'stop','restart','pause','unpause','kill']),
            ], [
                public.validate.trim_filter(),
            ])
        except Exception as ex:
            public.print_log("error info: {}".format(ex))
            return public.return_message(-1, 0, str(ex))

        if get.status == 'start':
            data = self.start(get)

        elif get.status == 'stop':
            data = self.stop(get)
        elif get.status == 'restart':
            data = self.restart(get)
        elif get.status == 'pause':
            data = self.pause(get)
        elif get.status == 'unpause':
            data = self.unpause(get)
        else:
            data = self.kill(get)

        if data["status"]== -1:
            return public.return_message(0, 0, data['message'])
        else:
            return public.return_message(-1, 0, data['message'])
    # 项目状态执行命令调用
    def __host_temp(self, statcks_info, status):
        file_path = "{}/data/compose/{}/docker-compose.yaml".format(public.get_panel_path(), public.md5(statcks_info['name']))

        status_info = {
            "start": "start",
            "stop": "stop",
            "restart": "restart",
            "pause": "pause",
            "unpause": "Unpause",
            "kill": "kill",
        }

        # 本地添加模版
        if not os.path.exists(file_path):
            if os.path.exists(statcks_info["path"]):
                public.ExecShell("/usr/bin/docker-compose -f {} {} &> {}".format(statcks_info["path"], status, self._log_path))
            else:
                stdout, stderr = public.ExecShell("docker-compose ls --format json")
                try:
                    info = json.loads(stdout)
                except:
                    info = []
                if stdout:
                    for i in info:
                        if i['Name'] == statcks_info['name']:
                            public.ExecShell("docker-compose -p {} {} &> {}".format(i['Name'], status, self._log_path))
                            break
        else:
            shell = "/usr/bin/docker-compose -f {compose_path} {status} &> {_log_path}".format(
                compose_path="{}/data/compose/{}/docker-compose.yaml".format(
                    public.get_panel_path(),
                    public.md5(statcks_info['name'])),
                status=status,
                _log_path=self._log_path
            )

            a, e = public.ExecShell(shell)
            if e:
                return public.return_message(-1, 0,  public.lang("{}The project failed: {}",status_info[status], e))

    def kill(self, get):
        """
        强制停止项目
        @param get:
        @return:
        """
        if not hasattr(get, "project_id"):
            return public.return_message(-1, 0, public.lang("Missing parameter project_id!"))

        statcks_info = dp.sql("stacks").where("id=?", (get.project_id,)).find()
        if not statcks_info:
            return public.return_message(-1, 0, public.lang("Project configuration not found!"))

        if not hasattr(get, "status"):
            return public.return_message(-1, 0, public.lang("The status parameter is missing!"))

        self.__host_temp(statcks_info, get.status)
        dp.write_log("Stopping project [{}] succeeded".format(statcks_info['name']))
        return public.return_message(0, 0, public.lang("Setup successful!"))

    def stop(self, get):
        """
        停止项目
        project_id          数据库记录的项目ID
        kill                强制停止项目 0/1
        :param get:
        :return:
        """
        if not hasattr(get, "project_id"):
            return public.return_message(-1, 0, public.lang("Missing parameter project_id!"))

        statcks_info = dp.sql("stacks").where("id=?", (get.project_id,)).find()
        if not statcks_info:
            return public.return_message(-1, 0, public.lang("Project configuration not found!"))

        if not hasattr(get, "status"):
            return public.return_message(-1, 0, public.lang("The status parameter is missing!"))

        self.__host_temp(statcks_info, get.status)
        dp.write_log("Stopping project [{}] succeeded!".format(statcks_info['name']))
        return public.return_message(0, 0, public.lang("Setup successful!"))

    def start(self, get):
        """
        启动项目
        project_id          数据库记录的项目ID
        :param get:
        :return:
        """
        if not hasattr(get, "project_id"):
            return public.return_message(-1, 0, public.lang("Missing parameter project_id!"))

        statcks_info = dp.sql("stacks").where("id=?", (get.project_id,)).find()
        if not statcks_info:
            return public.return_message(-1, 0, public.lang("Project configuration not found!"))

        if not hasattr(get, "status"):
            return public.return_message(-1, 0, public.lang("The status parameter is missing!"))

        self.__host_temp(statcks_info, get.status)
        dp.write_log("Start project [{}] successful!".format(statcks_info['name']))
        return public.return_message(0, 0, public.lang("Setup successful!"))

    def restart(self, get):
        """
        拉取项目内需要的镜像
        project_id          数据库记录的项目ID
        :param get:
        :return:
        """
        if not hasattr(get, "project_id"):
            return public.return_message(-1, 0, public.lang("Missing parameter project_id!"))

        statcks_info = dp.sql("stacks").where("id=?", (get.project_id,)).find()
        if not statcks_info:
            return public.return_message(-1, 0, public.lang("Project configuration not found!"))

        if not hasattr(get, "status"):
            return public.return_message(-1, 0, public.lang("The status parameter is missing!"))

        self.__host_temp(statcks_info, get.status)
        dp.write_log("Restart project [{}] successfully!".format(statcks_info['name']))
        return public.return_message(0, 0, public.lang("Successfully set!"))

    def pull(self, get):
        """
        拉取模板内需要的镜像
        template_id          数据库记录的项目ID
        :param get:
        :return:
        """
        get.name = get.get("name", "")
        get.url = get.get("url", "docker.io")
        get.template_id = get.get("template_id", "")
        if get.template_id == "":
            return public.return_message(-1, 0, public.lang("Missing parameter template_id!"))

        statcks_info = dp.sql("templates").where("id=?", (get.template_id,)).find()
        if not statcks_info:
            return public.return_message(0, 0, public.lang("Didn't find the template!"))

        cmd = "/usr/bin/docker-compose -f {} pull >> {} 2>&1".format(statcks_info['path'], self._log_path)
        if get.name != "" and get.url != "docker.io":
            from btdockerModelV2 import registryModel as dr
            r_info = dr.main().registry_info(get)
            r_info['username'] = public.aes_decrypt(r_info['username'], self.aes_key)
            r_info['password'] = public.aes_decrypt(r_info['password'], self.aes_key)
            login_result = dr.main().login(self._url, r_info['url'], r_info['username'], r_info['password'])
            if not login_result["status"]:
                return login_result

            cmd = "docker login --username {} --password {} {} >> {} 2>&1 &&".format(
                r_info['username'],
                r_info['password'],
                r_info['url'],
                self._log_path
            ) + cmd

        os.system(
            "echo > {};nohup {} && echo 'bt_successful' >> {} "
            "|| echo 'bt_failed' >> {} &".format(
                self._log_path,
                cmd,
                self._log_path,
                self._log_path,
        ))
        dp.write_log("The image inside the template [{}] was pulled successfully  !".format(statcks_info['name']))
        return public.return_message(0, 0, public.lang("Pull successfully!"))

    def pause(self, get):
        """
        暂停项目
        project_id          数据库记录的项目ID
        :param get:
        :return:
        """
        if not hasattr(get, "project_id"):
            return public.return_message(-1, 0, public.lang("Missing parameter project_id!"))

        statcks_info = dp.sql("stacks").where("id=?", (get.project_id,)).find()
        if not statcks_info:
            return public.return_message(-1, 0, public.lang("Project configuration not found!"))
        if not hasattr(get, "status"):
            return public.return_message(-1, 0, public.lang("The status parameter is missing!"))

        self.__host_temp(statcks_info, get.status)
        dp.write_log("Pause [{}] success!".format(statcks_info['name']))
        return public.return_message(0, 0, public.lang("Successfully set!"))

    def unpause(self, get):
        """
        取消暂停项目
        project_id          数据库记录的项目ID
        :param get:
        :return:
        """
        if not hasattr(get, "project_id"):
            return public.return_message(-1, 0, public.lang("Missing parameter project_id!"))

        statcks_info = dp.sql("stacks").where("id=?", (get.project_id,)).find()
        if not statcks_info:
            return public.return_message(-1, 0, public.lang("Project configuration not found!"))

        if not hasattr(get, "status"):
            return public.return_message(-1, 0, public.lang("The status parameter is missing!"))

        self.__host_temp(statcks_info, get.status)
        dp.write_log("Unpause [{}] success!".format(statcks_info['name']))
        return public.return_message(0, 0, public.lang("Successfully set!"))

    def scan_compose_file(self, path, data):
        """
        递归扫描目录下的compose文件
        :param path 需要扫描的目录
        :param data 需要返回的数据 一个字典
        :param get:
        :return:
        """
        try:
            if not os.path.isdir(path):
                return data

            file_list = os.listdir(path)
            for file in file_list:
                current_path = os.path.join(path, file)
                # 判断是否是文件夹
                if os.path.isdir(current_path):
                    self.scan_compose_file(current_path, data)
                else:
                    if file == "docker-compose.yaml" or file == "docker-compose.yam" or file == "docker-compose.yml":
                        if "/www/server/panel/data/compose" in current_path:
                            continue
                        data.append(current_path)
                    if ".yaml" in file or ".yam" in file or ".yml" in file:
                        if "/www/server/panel/data/compose" in current_path:
                            continue
                        data.append(current_path)
        except:
            pass

        return data

    def get_compose_project(self, get):
        """
        :param path 需要获取的路径 是一个目录
        :param sub_dir 扫描子目录
        :param get:
        :return:
        """
        get.exists(["path", "sub_dir"])
        data = list()
        suffix = ["yaml", "yam", "yml"]
        if get.path == "/":
            return public.return_message(-1, 0, public.lang("Unable to scan the root directory"))

        if get.path[-1] == "/":
            get.path = get.path[:-1]

        if not os.path.exists(get.path):
            return public.return_message(-1, 0, public.lang("The path does not exist!"))

        if str(get.sub_dir) == "1":
            res = self.scan_compose_file(get.path, data)
            if not res:
                res = []
            else:
                tmp = list()
                p_name_tmp = list()
                for i in res:
                    if i.split(".")[1] not in suffix:
                        continue

                    project_name = i.split("/")[-1].split(".")[0]
                    if project_name in p_name_tmp:
                        project_name = "{}_{}".format(project_name, i.split("/")[-2])

                    tmp_data = {
                        "project_name": project_name,
                        "conf_file": "/".join(i.split("/")),
                        "remark": "Add locally"
                    }

                    tmp.append(tmp_data)
                    p_name_tmp.append(tmp_data['project_name'])
                res = tmp
                p_name_tmp.clear()
        else:
            yaml = "{}/docker-compose.yaml".format(get.path)
            yam = "{}/docker-compose.yam".format(get.path)
            yml = "{}/docker-compose.yml".format(get.path)
            if os.path.exists(yaml):
                res = [{
                    "project_name": get.path.split("/")[-1],
                    "conf_file": yaml,
                    "remark": "Add locally"
                }]
            elif os.path.exists(yam):
                res = [{
                    "project_name": get.path.split("/")[-1],
                    "conf_file": yam,
                    "remark": "Add locally"
                }]
            elif os.path.exists(yml):
                res = [{
                    "project_name": get.path.split("/")[-1],
                    "conf_file": yml,
                    "remark": "Add locally"
                }]
            else:
                res = list()

            if not os.path.isdir(get.path):
                return public.return_message(0, 0, res)

            dir_list = os.listdir(get.path)

            for i in dir_list:
                if i.rsplit(".")[-1] in suffix:
                    res.append({
                        "project_name": i.rsplit(".")[0],
                        "conf_file": "/".join(get.path.split("/") + [i]),
                        "remark": "Add locally"
                    })

        return public.return_message(0, 0, res)

    # 从现有目录中添加模板
    def add_template_in_path(self, get):
        """
        :param template_list list [{"project_name":"pathtest_template","conf_file":"/www/dockerce/mysecent-project/docker-compose.yaml","remark":"描述描述"}]
        :param get:
        :return:
        """

        create_failed = dict()
        create_successfully = dict()
        for template in get.template_list:
            path = template['conf_file']
            name = template['project_name']
            remark = template['remark']
            exists = self._template_list(get)

            is_continue = False
            for i in exists:
                if name.strip() == i['name'].strip():
                    create_failed[name] = "Template already exists!"
                    is_continue = True
                    break

            if is_continue: continue

            if not os.path.exists(path):
                create_failed[name] = "This template was not found!"
                continue
            check_res = self.check_conf(path)
            if check_res['status'] == -1:
                create_failed[name] = "Template validation failed, possibly malformed!"
                continue
            pdata = {
                "name": name,
                "remark": remark,
                "path": path,
                "add_in_path": 1
            }
            dp.sql("templates").insert(pdata)
            create_successfully[name] = "Template added successfully!"

        for i in create_failed:
            if i in create_successfully:
                del (create_successfully[i])
            else:
                dp.write_log("Template added successfully from path [{}]!".format(i))
        if not create_failed and create_successfully:
            return public.return_message(0, 0,
                                         public.lang("Template added successfully: [{}]", ','.join(create_successfully)))
        elif not create_successfully and create_failed:
            return public.return_message(-1, 0,
                                         public.lang("Failed to add template: template name already exists or is incorrectly formatted [{}],Use docker-compose -f [specify compose.yml file] config to check", ','.join(create_failed)))

        return public.return_message(-1, 0,
                                     public.lang('These templates succeed: [{}]<br> These templates fail: the template name already exists or is incorrectly formatted [{}]',','.join(create_successfully), ','.join(create_failed)))

    def get_pull_log(self, get):
        """
        获取镜像拉取日志，websocket
        @param get:
        @return:
        """
        get.wsLogTitle = "Start to pull the template image, please wait..."
        get._log_path = self._log_path
        return self.get_ws_log(get)

    # 编辑项目    todo 根据删除适配
    def edit(self, get):
        """
        :param project_id: 要编辑的项目的ID
        :param project_name: 新的项目名
        :param remark: 新的描述
        :param template_id: 新的模板ID
        :return:
        """
        # {"project_id": 1, "template_id": 2, "project_name": "福达坊", "remark": ""}
        # 校验参数
        try:
            get.validate([
                Param('project_id').Require().Integer(),
                Param('project_name').Require().String(),
                Param('remark').String(),
                Param('template_id').Require().Integer(),
            ], [
                public.validate.trim_filter(),
            ])
        except Exception as ex:
            public.print_log("error info: {}".format(ex))
            return public.return_message(-1, 0, str(ex))

        # 删除旧的项目
        remove_result = self.remove(get)
        # if not remove_result['status']:
        #     return public.return_message(-1, 0, public.lang("Fail to modify!"))

        # 创建新的项目
        self.create(get)
        return public.return_message(0, 0, public.lang("Modify successfully!"))
