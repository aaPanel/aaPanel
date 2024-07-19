# coding: utf-8
# -------------------------------------------------------------------
# aaPanel
# -------------------------------------------------------------------
# Copyright (c) 2015-2099 aaPanel(www.aapanel.com) All rights reserved.
# -------------------------------------------------------------------
# Author: wzz <wzz@aapanel.com>
# -------------------------------------------------------------------

import docker.errors

import gettext
_ = gettext.gettext
# ------------------------------
# Docker模型
# ------------------------------
import public

from btdockerModelV2 import dk_public as dp
from btdockerModelV2.dockerBase import dockerBase
from public.validate import Param

class main(dockerBase):

    def docker_client(self, url):
        return dp.docker_client(url)

    def get_network_id(self, get):
        """
        asdf
        @param get:
        @return:
        """
        networks = self.docker_client(self._url).networks
        network = networks.get(get.id)
        return network.attrs

    def get_host_network(self, get):
        """
        获取服务器的docker网络
        :param get:
        :return:
        """
        try:
            client = self.docker_client(self._url)
            if not client:
                return public.return_message(-1, 0, [])

            networks = client.networks
            network_attr = self.get_network_attr(networks)
            data = list()

            for attr in network_attr:
                get.id = attr["Id"]
                c_result = self.get_network_id(get)
                subnet = ""
                gateway = ""
                if attr["IPAM"]["Config"]:
                    if "Subnet" in attr["IPAM"]["Config"][0]:
                        subnet = attr["IPAM"]["Config"][0]["Subnet"]
                    if "Gateway" in attr["IPAM"]["Config"][0]:
                        gateway = attr["IPAM"]["Config"][0]["Gateway"]

                tmp = {
                    "id": attr["Id"],
                    "name": attr["Name"],
                    "time": dp.convert_timezone_str_to_timestamp(attr["Created"]),
                    "driver": attr["Driver"],
                    "subnet": subnet,
                    "gateway": gateway,
                    "labels": attr["Labels"],
                    "used": 1 if c_result["Containers"] else 0,
                    "containers": c_result["Containers"],
                }
                data.append(tmp)

            return public.return_message(0, 0, sorted(data, key=lambda x: x['time'], reverse=True))
        except Exception as e:
            err = str(e)
            if "Connection reset by peer" in err:
                return public.return_message(-1, 0, _(
                                             "The docker service is running abnormally, please restart and try again!"))
            return public.return_message(-1, 0, [])

    def get_network_attr(self, networks):
        network = networks.list()
        return [i.attrs for i in network]

    def add(self, get):
        """
        :param name 网络名称
        :param driver  bridge/ipvlan/macvlan/overlay
        :param options Driver options as a key-value dictionary
        :param subnet '124.42.0.0/16'
        :param gateway '124.42.0.254'
        :param iprange '124.42.0.0/24'
        :param labels Map of labels to set on the network. Default None.
        :param remarks 备注
        :param get:
        :return:
        """
        # {"name": "23sdff223f", "driver": "overlay", "options": "", "subnet": "192.168.13.0/24",
        #  "gateway": "192.168.13.1", "iprange": "192.168.13.0/24", "labels": ""}
        # 校验参数
        try:
            get.validate([
                Param('name').Require().String(),
                Param('subnet').Require(),
                Param('gateway').Require(),
                Param('iprange').Require(),
            ], [
                public.validate.trim_filter(),
            ])
        except Exception as ex:
            public.print_log("error info: {}".format(ex))
            return public.return_message(-1, 0, str(ex))

        import docker

        ipam_pool = docker.types.IPAMPool(
            subnet=get.subnet,
            gateway=get.gateway,
            iprange=get.iprange
        )

        ipam_config = docker.types.IPAMConfig(
            pool_configs=[ipam_pool]
        )

        try:
            self.docker_client(self._url).networks.create(
                name=get.name,
                options=dp.set_kv(get.options),
                driver="bridge",
                ipam=ipam_config,
                labels=dp.set_kv(get.labels)
            )
        except docker.errors.APIError as e:
            print(str(e))
            if "failed to allocate gateway" in str(e):
                return public.return_message(-1, 0, _(
                                             "The gateway setting is wrong, Please enter a gateway that matches the subnet: {}".format(
                                                 get.subnet)))
            if "invalid CIDR address" in str(e):
                return public.return_message(-1, 0, _(
                                             "Subnet address format error, please enter for example: 172.16.0.0/16"))
            if "invalid Address SubPool" in str(e):
                return public.return_message(-1, 0, _(
                                             "IP range format error, please enter the appropriate IP range for this subnet:".format(
                                                 get.subnet)))
            if "Pool overlaps with other one on this address space" in str(e):
                return public.return_message(-1, 0, _( "IP range [{}] already exists!".format(get.subnet)))
            return public.return_message(-1, 0, _( "Failed to add network! {}".format(str(e))))

        dp.write_log("Added network [{}] [{}] successful!".format(get.name, get.iprange))
        return public.return_message(0, 0, _( "Added network successfully!"))

    def del_network(self, get):
        """
        :param id
        :param get:
        :return:
        """
        # 校验参数
        try:
            get.validate([
                Param('id').Require().String(),
            ], [
                public.validate.trim_filter(),
            ])
        except Exception as ex:
            public.print_log("error info: {}".format(ex))
            return public.return_message(-1, 0, str(ex))

        try:
            networks = self.docker_client(self._url).networks.get(get.id)
            attrs = networks.attrs
            if attrs['Name'] in ["bridge", "none"]:
                return public.return_message(-1, 0, _( "The system default network cannot be deleted!"))

            networks.remove()
            dp.write_log("Delete network [{}] successfully!".format(attrs['Name']))
            return public.return_message(0, 0, _( "successfully delete!"))

        except docker.errors.APIError as e:
            if " has active endpoints" in str(e):
                return public.return_message(-1, 0, _( "The network cannot be deleted while it is in use!"))
            return public.return_message(-1, 0, _( "Delete failed! {}".format(str(e))))

    def prune(self, get):
        """
        删除无用的网络
        :param get:
        :return:
        """
        try:
            res = self.docker_client(self._url).networks.prune()
            if not res['NetworksDeleted']:
                return public.return_message(-1, 0, _( "There are no useless networks!"))

            dp.write_log("Delete useless network successfully!")
            return public.return_message(0, 0, _( "successfully delete!"))

        except docker.errors.APIError as e:
            return public.return_message(-1, 0, _( "Delete failed! {}".format(str(e))))

    def disconnect(self, get):
        """
        断开某个容器的网络
        :param id
        :param container_id
        :param get:
        :return:
        """
        # 校验参数
        try:
            get.validate([
                Param('id').Require().String(),
                Param('container_id').Require().String(),
            ], [
                public.validate.trim_filter(),
            ])
        except Exception as ex:
            public.print_log("error info: {}".format(ex))
            return public.return_message(-1, 0, str(ex))

        try:
            get.id = get.get("id/s", "")
            get.container_id = get.get("container_id/s", "")
            if get.id == "":
                return public.return_message(-1, 0, _( "Network ID cannot be empty"))
            if get.container_id == "":
                return public.return_message(-1, 0, _( "Container ID cannot be empty"))

            networks = self.docker_client(self._url).networks.get(get.id)
            networks.disconnect(get.container_id)
            dp.write_log("Network disconnection [{}] successful!".format(get.id))
            return public.return_message(0, 0, _( "Network disconnection was successful!"))
        except docker.errors.APIError as e:
            if "No such container" in str(e):
                return public.return_message(-1, 0, _( "Container ID: {}, does not exist!".format(get.container_id)))
            if "network" in str(e) and "Not Found" in str(e):
                return public.return_message(-1, 0, _( "Network ID: {}, does not exist!".format(get.id)))
            return public.return_message(-1, 0, _( "Network disconnection failed! {}".format(str(e))))

    def connect(self, get):
        """
        连接到指定网络
        :param id
        :param container_id
        :param get:
        :return:
        """
        # 校验参数
        try:
            get.validate([
                Param('id').Require().String(),
                Param('container_id').Require().String(),
            ], [
                public.validate.trim_filter(),
            ])
        except Exception as ex:
            public.print_log("error info: {}".format(ex))
            return public.return_message(-1, 0, str(ex))

        try:
            networks = self.docker_client(self._url).networks.get(get.id)
            networks.connect(get.container_id)
            dp.write_log("Network connection [{}] successful!".format(get.id))
            return public.return_message(0, 0, _( "Network connection successful!"))
        except docker.errors.APIError as e:
            if "No such container" in str(e):
                return public.return_message(-1, 0, _( "Container ID: {}, does not exist!".format(get.container_id)))
            if "network" in str(e) and "Not Found" in str(e):
                return public.return_message(-1, 0, _( "Network ID: {}, does not exist!".format(get.id)))
            return public.return_message(-1, 0, _( "Failed to connect to network! {}".format(str(e))))
