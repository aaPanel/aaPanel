# coding: utf-8
# -------------------------------------------------------------------
# aaPanel
# -------------------------------------------------------------------
# Copyright (c) 2015-2099 aaPanel(www.aapanel.com) All rights reserved.
# -------------------------------------------------------------------
# Author: wzz <wzz@aapanel.com>
# -------------------------------------------------------------------
# docker模型sock 封装库 容器库
# -------------------------------------------------------------------
import json

import public
from btdockerModelV2.dockerSock.sockBase import base


class dockerContainer(base):
    def __init__(self):
        super(dockerContainer, self).__init__()

    # 2024/3/13 上午 11:20 获取所有容器列表
    def get_container(self):
        '''
            @name 获取所有容器列表
            @author wzz <2024/3/13 上午 10:54>
            @param "data":{"参数名":""} <数据类型> 参数描述
            @return dict{"status":True/False,"msg":"提示信息"}
        '''
        try:
            return json.loads(public.ExecShell("curl -s --unix-socket {} http:/{}/containers/json?all=1".format(self._sock, self.get_api_version()))[0])

        except Exception as e:
            print(public.get_error_info())
            return []

    # 2024/3/28 下午 11:37 获取指定容器的inspect
    def get_container_inspect(self, container_id: str):
        '''
            @name 获取指定容器的inspect
            @param container_id: 容器id
            @return dict{"status":True/False,"msg":"提示信息"}
        '''
        try:
            return json.loads(public.ExecShell("curl -s --unix-socket {} http:/{}/containers/{}/json"
            .format(self._sock, self.get_api_version(), container_id))[0])
        except Exception as e:
            print(public.get_error_info())
            return []
