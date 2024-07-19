# coding: utf-8
# -------------------------------------------------------------------
# aaPanel
# -------------------------------------------------------------------
# Copyright (c) 2014-2099 aaPanel(www.aapanel.com) All rights reserved.
# -------------------------------------------------------------------
# Author: wzz <wzz@aapanel.com>
# -------------------------------------------------------------------

# ------------------------------
# Docker模型 - Docker应用
# ------------------------------
import public
import os
import time
import json
import re
from btdockerModelV2 import dk_public as dp
from btdockerModelV2.dockerBase import dockerBase
from public.validate import Param

class main(dockerBase):

    def __init__(self):
        pass

    # 2024/2/20 下午 4:31 获取/搜索docker应用的列表
    def get_app_list(self, get=None):
        '''
            @name 获取docker应用的列表
            @author wzz <2024/2/20 下午 4:32>
            @param "data":{"参数名":""} <数据类型> 参数描述
            @return dict{"status":True/False,"msg":"提示信息"}
        '''

        try:
            from btdockerModelV2 import registryModel as dr
            dr.main().registry_list(get)

            from panelPlugin import panelPlugin
            pp = panelPlugin()
            get.type = 10
            # get.type = 16  # dev docker
            # get.type = 14  # www docker
            get.force = get.force if "force" in get and get.force else 0
            if not hasattr(get, "query"):
                get.query = ""
            get.tojs = "soft.get_list"
            # softList = pp.get_soft_list(get)
            if get.query != "":
                get.row = 1000
                softList = pp.get_soft_list(get)
                softList['list'] = self.struct_list(softList['list'])
                softList['list'] = pp.get_page(softList['list']['data'], get)
            else:

                softList = pp.get_soft_list(get)
            return public.return_message(0, 0, softList['list'])
        except Exception as e:
            # public.print_log("1111111111  进方法")
            return public.return_message(-1, 0, e)

    # 2024/2/20 下午 4:47 处理云端软件列表，只需要list中type=13的数据
    def struct_list(self, softList: dict):
        '''
            @name 处理云端软件列表，只需要list中type=13的数据
            @param softList:
            @return:
        '''
        new_list = []
        for i in softList['data']:
            # if i['type'] == 14:   # www docker
            # if i['type'] == 16:  # dev docker
            if i['type'] == 10:
                new_list.append(i)

        softList['data'] = new_list

        return softList
