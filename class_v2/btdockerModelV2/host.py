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
import public
import dk_public as dp

class main:

    # 获取docker主机列表
    def get_list(self,args=None):
        info = dp.sql("hosts").select()
        for i in info:
            if dp.docker_client(i['url']):
                i['status'] = True
            else:
                i['status'] = False
        return info

    # 添加docker主机
    def add(self,args):
        """
        :param url      连接主机的url
        :param remark   主机备注
        :return:
        """
        import time
        host_lists = self.get_list()
        for h in host_lists:
            if h['url'] == args.url:
                return public.returnMsg(False, public.lang("The host already exists！"))
        # 测试连接
        if not dp.docker_client(args.url):
            return public.returnMsg(False, public.lang("Failed to connect to the server, please check if docker is started！"))
        pdata = {
            "url": args.url,
            "remark": public.xsssec(args.remark),
            "time": int(time.time())
        }
        dp.write_log("Add host [{}] successful！".format(args.url))
        dp.sql('hosts').insert(pdata)
        return public.returnMsg(True, public.lang("Add docker host successfully！"))

    def delete(self,args):
        """
        :param id      连接主机id
        :return:
        """
        data = dp.sql('hosts').where('id=?',args(args.id,)).find()
        dp.sql('hosts').delete(id=args.id)
        dp.write_log("Delete host [{}] successful！".format(data['url']))
        return public.returnMsg(True, public.lang("Delete host successfully！"))