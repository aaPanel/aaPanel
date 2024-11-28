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
import docker.errors
import public
from btdockerModelV2 import dk_public as dp
from btdockerModelV2.dockerBase import dockerBase
from public.validate import Param

class main(dockerBase):

    def docker_client(self, url):
        return dp.docker_client(url)

    def get_volume_container_name(self, volume_detail, container_list):
        '''
        拼接对应的容器名与卷名
        @param volume_detail: 卷字典
        @param container_list: 容器详情列表
        @return:
        '''
        try:
            for container in container_list:
                if not container['Mounts']:
                    continue
                for mount in container['Mounts']:
                    if "Name" not in mount:
                        continue
                    if volume_detail['Name'] == mount['Name']:
                        volume_detail['container'] = container['Names'][0].replace("/", "")
            if 'container' not in volume_detail:
                volume_detail['container'] = ''
        except:
            volume_detail['container'] = ''

        return volume_detail

    def get_volume_list(self, args):
        """
        :param self._url: 链接docker的URL
        :return:
        """
        try:
            data = list()
            from btdockerModelV2.dockerSock import volume
            sk_volume = volume.dockerVolume()
            volume_list = sk_volume.get_volumes()

            from btdockerModelV2.dockerSock import container
            sk_container = container.dockerContainer()
            container_list = sk_container.get_container()

            if "Volumes" in volume_list and type(volume_list["Volumes"]) == list:
                for v in volume_list["Volumes"]:
                    v["CreatedAt"] = dp.convert_timezone_str_to_timestamp(v["CreatedAt"])
                    data.append(self.get_volume_container_name(v, container_list))

                return public.return_message(0, 0, sorted(data, key=lambda x: x['CreatedAt'], reverse=True))
            else:
                return public.return_message(0, 0, [])
        except Exception as e:
            return public.return_message(-1, 0, [])

    def add(self, args):
        """
        添加一个卷
        :param name
        :param driver  local
        :param driver_opts (dict) – Driver options as a key-value dictionary
        :param labels str
        :return:
        """
        try:
            args.driver_opts = args.get("driver_opts", "")
            args.labels = args.get("labels", "")
            if args.driver_opts != "":
                args.driver_opts = dp.set_kv(args.driver_opts)
            if args.labels != "":
                args.labels = dp.set_kv(args.labels)

            if len(args.name) < 2:
                return public.return_message(-1, 0, public.lang("Volume names can be no less than 2 characters long!"))

            self.docker_client(self._url).volumes.create(
                name=args.name,
                driver=args.driver,
                driver_opts=args.driver_opts if args.driver_opts else None,
                labels=args.labels if args.labels != "" else None
            )
            dp.write_log("Add storage volume [{}] success!".format(args.name))
            return public.return_message(0, 0, public.lang("successfully added!"))
        except docker.errors.APIError as e:
            if "volume name is too short, names should be at least two alphanumeric characters" in str(e):
                return public.return_message(-1, 0, public.lang("Volume names can be no less than 2 characters long!"))
            if "volume name" in str(e):
                return public.return_message(-1, 0, public.lang("Volume name already exists!"))
            return public.return_message(-1, 0, public.lang("addition failed {}", e))

        except Exception as e:
            if "driver_opts must be a dictionary" in str(e):
                return public.return_message(-1, 0, public.lang("Driver option tags must be dictionary/key-value pairs!"))
            return public.return_message(-1, 0, public.lang("Add failed! {}", e))

    def remove(self, args):
        """
        删除一个卷
        :param name  volume name
        :param args:
        :return:
        """

        # 校验参数
        try:
            args.validate([
                Param('name').Require().String(),
            ], [
                public.validate.trim_filter(),
            ])
        except Exception as ex:
            public.print_log("error info: {}".format(ex))
            return public.return_message(-1, 0, str(ex))
        try:
            obj = self.docker_client(self._url).volumes.get(args.name)
            obj.remove()
            dp.write_log("Delete volume [{}] successful!".format(args.name))
            return public.return_message(0, 0, public.lang("successfully delete"))

        except docker.errors.APIError as e:
            if "volume is in use" in str(e):
                return public.return_message(-1, 0, public.lang("The storage volume is in use and cannot be deleted!"))
            if "no such volume" in str(e):
                return public.return_message(-1, 0, public.lang("The storage volume does not exist!"))
            return public.return_message(-1, 0, public.lang("Delete failed! {}", e))

    def prune(self, args):
        """
        删除无用的卷
        :param args:
        :return:
        """
        try:
            res = self.docker_client(self._url).volumes.prune()
            if not res['VolumesDeleted']:
                return public.return_message(-1, 0, public.lang("No useless storage volumes!"))

            dp.write_log("Delete useless storage volume successfully!")
            return public.return_message(0, 0, public.lang("successfully delete!"))
        except docker.errors.APIError as e:
            return public.return_message(-1, 0, public.lang("Delete failed! {}", e))
