# coding: utf-8
# -------------------------------------------------------------------
# aaPanel
# -------------------------------------------------------------------
# Copyright (c) 2015-2099 aaPanel(www.aapanel.com) All rights reserved.
# -------------------------------------------------------------------
# Author: zouhw <zhw@aapanel.com>
# -------------------------------------------------------------------

# ------------------------------
# Docker模型
# ------------------------------
import json

import gettext
_ = gettext.gettext

import public
from btdockerModelV2 import dk_public as dp
from btdockerModelV2.dockerBase import dockerBase
from public.validate import Param

class main(dockerBase):

    def docker_client(self, url):
        return dp.docker_client(url)

    def add(self, args):
        """
        添加仓库
        :param registry 仓库URL docker.io
        :param name
        :parma username
        :parma password
        :param namespace 仓库命名空间
        :param remark 备注
        :param args:
        :return:
        """
        # {"registry": "docker.io", "name": "wzznb", "username": "akaishuichi", "password": "xiuyi999..",
        #  "namespace": "akaishuichi", "remark": "wzz_docker_io"}

        # 校验参数
        try:
            args.validate([
                Param('name').Require().String(),
                Param('username').Require().String(),
                Param('password').Require().String(),
                Param('namespace').Require().String(),
                Param('remark').String(),

            ], [
                public.validate.trim_filter(),
            ])
        except Exception as ex:
            public.print_log("error info: {}".format(ex))
            return public.return_message(-1, 0, str(ex))
        # 验证登录
        if not args.registry:
            args.registry = "docker.io"
        res = self.login(self._url, args.registry, args.username, args.password)
        if not res['status']:
            return public.return_message(-1, 0, res)
        r_list = self.registry_list(args)
        if len(r_list) > 0:
            for r in r_list:
                if r['name'] == args.name:
                    return public.return_message(-1, 0, _( "The name already exists! <br><br>name: {}".format(args.name)))
                if r['username'] == args.username and args.registry == r['url']:
                    return public.return_message(-1, 0, _( "Repository information already exists!"))
        pdata = {
            "name": args.name,
            "url": args.registry,
            "namespace": args.namespace,
            "username": public.aes_encrypt(args.username, self.aes_key),
            "password": public.aes_encrypt(args.password, self.aes_key),
            "remark": public.xsssec(args.remark)
        }
        dp.sql("registry").insert(pdata)
        dp.write_log("Added repository [{}] [{}] success!".format(args.name, args.registry))
        return public.return_message(0, 0, _( "successfully added!"))

    def edit(self, args):
        """
        编辑仓库
        :param registry 仓库URL docker.io
        :param id 仓库id
        :parma username
        :parma password
        :param namespace
        :param remark
        :param args:
        :return:
        """

        # 校验参数
        try:
            args.validate([
                Param('id').Require().Integer(),
                Param('username').Require().String(),
                Param('password').Require().String(),
                Param('namespace').Require().String(),
                Param('remark').String(),

            ], [
                public.validate.trim_filter(),
            ])
        except Exception as ex:
            public.print_log("error info: {}".format(ex))
            return public.return_message(-1, 0, str(ex))

        # 验证登录
        # if str(args.id) == "1":
        #     return public.return_message(-1, 0, "[Official Docker repository] Not editable!")
        if not args.registry:
            args.registry = "docker.io"

        # 2023/12/13 上午 11:40 处理加密的编辑
        try:
            is_encrypt = False
            res = self.login(self._url, args.registry, args.username, args.password)
            if not res['status']:
                res = self.login(
                    self._url,
                    args.registry,
                    public.aes_decrypt(args.username, self.aes_key),
                    public.aes_decrypt(args.password, self.aes_key)
                )
                if not res['status']:
                    return public.return_message(-1, 0, res['msg'])
                is_encrypt = True
        except Exception as e:
            if "binascii.Error: Incorrect padding" in str(e):
                return public.return_message(-1, 0, _(
                                             "Editing failed! Reason: Account password decryption failed! Please delete the repository and add it again"))
            return public.return_message(-1, 0, _( "Editing failed! Reason:{}".format(e)))

        res = dp.sql("registry").where("id=?", (args.id,)).find()
        if not res:
            return public.return_message(-1, 0, _( "This repository could not be found"))
        pdata = {
            "name": args.name,
            "url": args.registry,
            "username": public.aes_encrypt(args.username, self.aes_key) if is_encrypt is False else args.username,
            "password": public.aes_encrypt(args.password, self.aes_key) if is_encrypt is False else args.password,
            "namespace": args.namespace,
            "remark": args.remark
        }
        dp.sql("registry").where("id=?", (args.id,)).update(pdata)
        dp.write_log("Edit repository [{}][{}] Success!".format(args.name, args.registry))
        return public.return_message(0, 0, _( "Edit success!"))

    def remove(self, args):
        """
        删除某个仓库
        :param id
        :param rags:
        :return:
        """
        # 校验参数
        try:
            args.validate([
                Param('id').Require().Integer(),
            ], [
                public.validate.trim_filter(),
            ])
        except Exception as ex:
            public.print_log("error info: {}".format(ex))
            return public.return_message(-1, 0, str(ex))

        # if str(args.id) == "1":
        #     return public.return_message(-1, 0, "[Official Docker repository] can not be removed!")

        data = dp.sql("registry").where("id=?", (args.id)).find()

        if len(data) < 1:
            return public.return_message(0, 0, _( "Delete failed,The repository id may not exist!"))

        dp.sql("registry").where("id=?", (args.id,)).delete()

        dp.write_log("Delete repository [{}][{}] Success!".format(data['name'], data['url']))
        return public.return_message(0, 0, _( "Successfully deleted!"))
    def registry_list(self, get):
        """
        获取仓库列表
        :return:
        """

        db_obj = dp.sql("registry")
        # 2024/1/3 下午 6:00 检测数据库是否存在并且表健康
        search_result = db_obj.where('id=? or name=?', (1, "Docker public repository")).select()

        # if db_obj.ERR_INFO:
        #     return []


        if len(search_result) == 0:
            dp.sql("registry").insert({
                "name": "Docker public repository",
                "url": "docker.io",
                "username": "",
                "password": "",
                "namespace": "",
                "remark": "Docker public repository"
            })
        if "error: no such table: registry" in search_result or len(search_result) == 0:
            # public.ExecShell("mv -f /www/server/panel/data/docker.db /www/server/panel/data/db/docker.db")
            public.ExecShell("mv -f /www/server/panel/data/db/docker.db /www/server/panel/data/docker.db")
            dp.check_db()

        res = dp.sql("registry").select()
        if not isinstance(res, list):
            res = []
        return res
    # 改返回
    def registry_listV2(self, get):
        """
        获取仓库列表
        :return:
        """
        db_obj = dp.sql("registry")
        # 2024/1/3 下午 6:00 检测数据库是否存在并且表健康
        search_result = db_obj.where('id=? or name=?', (1, "Docker public repository")).select()
        # search_result = db_obj.where('id=? ', (1)).select()
        # if db_obj.ERR_INFO:
        #     return public.return_message(0, 0,  [])


        if len(search_result) == 0:
            dp.sql("registry").insert({
                "name": "Docker public repository",
                "url": "docker.io",
                "username": "",
                "password": "",
                "namespace": "",
                "remark": "Docker public repository"
            })
        if "error: no such table: registry" in search_result or len(search_result) == 0:
            # public.ExecShell("mv -f /www/server/panel/data/docker.db /www/server/panel/data/db/docker.db")
            public.ExecShell("mv -f /www/server/panel/data/db/docker.db /www/server/panel/data/docker.db")
            dp.check_db()

        res = dp.sql("registry").select()
        if not isinstance(res, list):
            res = []

        return public.return_message(0, 0,  res)

    def get_com_registry(self, get):
        """
        获取常用仓库列表
        @param get:
        @return:
        """
        com_registry_file = "{}/class/btdockerModelV2/config/com_registry.json".format(public.get_panel_path())
        try:
            com_registry = json.loads(public.readFile(com_registry_file))
        except:
            com_registry = {
                "docker.io": "Docker public repository",
                "swr.cn-north-4.myhuaweicloud.com": "Huawei Cloud mirror station",
                "ccr.ccs.tencentyun.com": "Tencent cloud mirror station",
                "registry.cn-hangzhou.aliyuncs.com": "Alibaba Cloud Mirror Station (Hangzhou)"
            }

        return public.return_message(0, 0, com_registry)

    def registry_info(self, name):
        return dp.sql("registry").where("name=?", (name,)).find()

    def login(self, url, registry, username, password):
        """
        仓库登录测试
        :param args:
        :return:
        """
        import docker.errors
        try:
            res = self.docker_client(url).login(
                registry=registry,
                username=username,
                password=password,
                reauth=False
            )
            return public.returnMsg(True, str(res))
        except docker.errors.APIError as e:
            if "authentication required" in str(e):
                return public.returnMsg(False,
                                        "Login test failed! Reason: May be account password error, please check!")
            if "unauthorized: incorrect username or password" in str(e):
                return public.returnMsg(False,
                                        "Login test failed! Reason: May be account password error, please check!")
            return public.returnMsg(False, "Login test failed! Reason: {}".format(e))
