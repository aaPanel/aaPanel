# coding: utf-8
# -------------------------------------------------------------------
# aapanel
# -------------------------------------------------------------------
# Copyright (c) 2014-2099 aapanel(http://www.aapanel.com) All rights reserved.
# -------------------------------------------------------------------
# Author: wzz <wzz@bt.cn>
# -------------------------------------------------------------------

# ------------------------------
# 系统防火墙模型 - 底层基类
# ------------------------------

import sys
if "/www/server/panel/class" not in sys.path:
    sys.path.insert(0, "/www/server/panel/class")
import public


class Base(object):

    def __init__(self):
        pass

    # 2024/3/22 下午 3:18 通用返回
    def _result(self, status: bool, msg: str) -> dict:
        '''
            @name 通用返回
            @author wzz <2024/3/22 下午 3:19>
            @param status: True/False
                    msg: 提示信息
            @return dict{"status":True/False,"msg":"提示信息"}
        '''
        return {"status": status, "msg": msg}

    # 2024/3/22 下午 4:55 检查是否设置了net.ipv4.ip_forward = 1，没有则设置
    def check_ip_forward(self) -> dict:
        '''
            @name 检查是否设置了net.ipv4.ip_forward = 1，没有则设置
            @param "data":{"参数名":""} <数据类型> 参数描述
            @return dict{"status":True/False,"msg":"提示信息"}
        '''
        stdout, stderr = public.ExecShell("sysctl net.ipv4.ip_forward")
        if "net.ipv4.ip_forward = 1" not in stdout:
            # 2024/3/22 下午 4:56 永久设置
            stdout, stderr = public.ExecShell("echo net.ipv4.ip_forward=1 >> /etc/sysctl.conf")
            if stderr:
                return self._result(False, "设置net.ipv4.ip_forward失败, err: {}".format(stderr))

            stdout, stderr = public.ExecShell("sysctl -p")
            if stderr:
                return self._result(False, "设置net.ipv4.ip_forward失败, err: {}".format(stderr))
            return self._result(True, "设置net.ipv4.ip_forward成功")
        return self._result(True, "net.ipv4.ip_forward已经设置")

    # 2024/3/18 上午 11:35 处理192.168.1.100-192.168.1.200这种ip范围
    # 返回192.168.1.100,192.168.1.101,192.168.1...,192.168.1.200列表
    def handle_ip_range(self, ip):
        '''
            @name 处理192.168.1.100-192.168.1.200这种ip范围的ip列表
            @author wzz <2024/3/19 下午 4:58>
            @param "data":{"参数名":""} <数据类型> 参数描述
            @return dict{"status":True/False,"msg":"提示信息"}
        '''
        ip_range = ip.split("-")
        ip_start = ip_range[0]
        ip_end = ip_range[1]
        ip_start = ip_start.split(".")
        ip_end = ip_end.split(".")
        ip_start = [int(i) for i in ip_start]
        ip_end = [int(i) for i in ip_end]
        ip_list = []
        for i in range(ip_start[0], ip_end[0] + 1):
            for j in range(ip_start[1], ip_end[1] + 1):
                for k in range(ip_start[2], ip_end[2] + 1):
                    for l in range(ip_start[3], ip_end[3] + 1):
                        ip_list.append("{}.{}.{}.{}".format(i, j, k, l))
        return ip_list
