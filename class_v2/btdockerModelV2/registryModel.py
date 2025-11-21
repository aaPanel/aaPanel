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
            return public.return_message(-1, 0, res['msg'])
        r_list = self.registry_list(args)
        if len(r_list) > 0:
            for r in r_list:
                if "reg_name" in r:
                    if r['reg_name'] == args.name and r["reg_url"] == args.registry and r['username'] == args.username:
                        return public.return_message(-1, 0, public.lang("Repository information already exists!"))

                if r['name'] == args.name and r["reg_url"] == args.registry and r['username'] == args.username:
                    return public.return_message(-1, 0, public.lang("Repository information already exists!"))
        pdata = {
            "reg_name": args.name,
            "url": args.registry,
            "namespace": args.namespace,
            "username": public.aes_encrypt(args.username, self.aes_key),
            "password": public.aes_encrypt(args.password, self.aes_key),
            "remark": public.xsssec(args.remark)
        }
        aa = dp.sql("registry").insert(pdata)

        dp.write_log("Added repository [{}] [{}] success!".format(args.name, args.registry))
        return public.return_message(0, 0, public.lang("successfully added!"))

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
        #     return public.return_message(-1, 0, public.lang("[Official Docker repository] Not editable!"))
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
                return public.return_message(-1, 0, public.lang("Editing failed! Reason: Account password decryption failed! Please delete the repository and add it again"))
            return public.return_message(-1, 0, public.lang("Editing failed! Reason:{}", e))

        res = dp.sql("registry").where("id=?", (args.id,)).find()
        if not res:
            return public.return_message(-1, 0, public.lang("This repository could not be found"))
        pdata = {
            "reg_name": args.name,
            "url": args.registry,
            "username": public.aes_encrypt(args.username, self.aes_key) if is_encrypt is False else args.username,
            "password": public.aes_encrypt(args.password, self.aes_key) if is_encrypt is False else args.password,
            "namespace": args.namespace,
            "remark": args.remark
        }
        dp.sql("registry").where("id=?", (args.id,)).update(pdata)
        dp.write_log("Edit repository [{}][{}] Success!".format(args.name, args.registry))
        return public.return_message(0, 0, public.lang("Edit success!"))

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
        #     return public.return_message(-1, 0, public.lang("[Official Docker repository] can not be removed!"))

        data = dp.sql("registry").where("id=?", (args.id)).find()

        if len(data) < 1:
            return public.return_message(0, 0, public.lang("Delete failed,The repository id may not exist!"))

        dp.sql("registry").where("id=?", (args.id,)).delete()

        dp.write_log("Delete repository [{}][{}] Success!".format(data['name'], data['url']))
        return public.return_message(0, 0, public.lang("Successfully deleted!"))
    def registry_list(self, get):
        """
        获取仓库列表
        :return:
        """
        self.check_table_dk_registry()
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

        for r in res:
            if "reg_name" not in r: continue
            if r["name"] == "" or not r["name"] or r["name"] is None:
                r["name"] = r["reg_name"]

        return res
    # 改返回
    def registry_listV2(self, get):
        """
        获取仓库列表
        :return:
        """
        res = self.registry_list(get)
        return public.return_message(0, 0,  res)
    # 2024/5/24 下午6:09 设置备注
    def set_remark(self, get):
        '''
            @name 设置备注
            @param "data":{"id":"仓库ID","remark":"备注"}
            @return dict{"status":True/False,"msg":"提示信息"}
        '''
        try:
            get.remark = get.get("remark/s", "")
            if get.remark != "":
                get.remark = public.xssencode2(get.remark)

            dp.sql("registry").where("id=?", (get.id,)).setField("remark", get.remark)
            return public.return_message(0, 0,  public.lang("Setup Successful!"))
        except Exception as e:
            return public.return_message(-1, 0, public.lang("Setup failed!{}",str(e)))

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
    # todo  检查字段新增reg_name
    def registry_info(self, get):
        '''
            @name 获取指定仓库的信息
            @author wzz <2024/5/24 下午3:16>
            @param "data":{"参数名":""} <数据类型> 参数描述
            @return dict{"status":True/False,"msg":"提示信息"}
        '''
        registry_info = dp.sql("registry").where("reg_name=? and url=?", (get.name, get.url)).find()
        if not registry_info:
            registry_info = dp.sql("registry").where("name=? and url=?", (get.name, get.url)).find()

        return registry_info

    def login(self, url, registry, username, password):
        """
        仓库登录测试
        :param args:
        :return:
        """

        try:
            res = self.docker_client(url).login(
                registry=registry,
                username=username,
                password=password,
                reauth=False
            )

            return public.returnMsg(True, str(res))
        except:
            error_info = public.get_error_info()
            return public.returnMsg(False, public.lang("Login test failed! Reason: {}", error_info))
        # except docker.errors.APIError as e:
        #     if "authentication required" in str(e):
        #         return public.returnMsg(False, public.lang("Login test failed! Reason: May be account password error, please check!"))
        #     if "unauthorized: incorrect username or password" in str(e):
        #         return public.returnMsg(False, public.lang("Login test failed! Reason: May be account password error, please check!"))
        #     return public.returnMsg(False, public.lang("Login test failed! Reason: {}", e))


    def check_table_dk_registry(self):
        '''
            @name 检查表registry 字段 reg_name  remark是否存在
            @return dict{"status":True/False,"msg":"提示信息"}
        '''

        # if public.M('sqlite_master').where('type=? AND name=?', ('table', 'docker_log_split')).count():
        #     create_table_str = public.M('sqlite_master').where('type=? AND name=?', ('table', 'docker_log_split')).getField('sql')
        #
        # if dp.sql('sqlite_master').where('type=? AND name=?', ('table', 'docker_log_split')).count():
        #     create_table_str = dp.sql('sqlite_master').where('type=? AND name=?', ('table', 'docker_log_split')).getField('sql')


        create_table_str = dp.sql('sqlite_master').where('type=? AND name=?', ('table', 'registry')).getField('sql')
        if create_table_str and 'reg_name' not in create_table_str:
            dp.sql('registry').execute('ALTER TABLE `registry` ADD COLUMN `reg_name` VARCHAR default "";')

        if create_table_str and 'remark' not in create_table_str:
            dp.sql('registry').execute('ALTER TABLE `registry` ADD COLUMN `remark` VARCHAR default "";')