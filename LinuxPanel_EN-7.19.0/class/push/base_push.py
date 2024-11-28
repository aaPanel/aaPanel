#coding: utf-8
# +-------------------------------------------------------------------
# | aaPanel
# +-------------------------------------------------------------------
# | Copyright (c) 2015-2020 aapanel(https://www.bt.cn) All rights reserved.
# +-------------------------------------------------------------------
# | Author: baozi <baozi@aapanel.com>
# | Author: baozi
# +-------------------------------------------------------------------
import sys,os,re,json

import public,panelPush, time
from datetime import datetime, timedelta

try:
    from BTPanel import cache
except :
    from cachelib import SimpleCache
    cache = SimpleCache()

class base_push:

    # 版本信息 目前无作用
    def get_version_info(self, get=None):
        raise NotImplementedError

    # 格式化返回执行周期， 目前无作用
    def get_push_cycle(self, data: dict):
        return data

    # 获取模块推送参数
    def get_module_config(self, get: public.dict_obj):
        raise NotImplementedError

    # 获取模块配置项
    def get_push_config(self, get: public.dict_obj):
        # 其实就是配置信息，没有也会从全局配置文件push.json中读取
        raise NotImplementedError

    # 写入推送配置文件
    def set_push_config(self, get: public.dict_obj):
        raise NotImplementedError

    # 删除推送配置
    def del_push_config(self, get: public.dict_obj):
        # 从配置中删除信息，并做一些您想做的事，如记日志
        raise NotImplementedError

    # 无意义？？？
    def get_total(self):
        return True

    # 检查并获取推送消息，返回空时，不做推送, 传入的data是配置项
    def get_push_data(self, data, total):
        # data 内容
        # index :  时间戳 time.time()
        # 消息 以类型为key， 以内容为value， 内容中包含title 和msg
        # push_keys： 列表，发送了信息的推送任务的id，用来验证推送任务次数（） 意义不大
        raise NotImplementedError