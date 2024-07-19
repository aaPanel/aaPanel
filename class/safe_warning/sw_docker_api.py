#!/usr/bin/python
# coding: utf-8
# -------------------------------------------------------------------
# aaPanel
# -------------------------------------------------------------------
# Copyright (c) 2015-2099 aaPanel(www.aapanel.com) All rights reserved.
# -------------------------------------------------------------------
# Author: lkq <lkq@aapanel.com>
# -------------------------------------------------------------------
# Time: 2022-08-10
# -------------------------------------------------------------------
# Docker API 未授权访问
# -------------------------------------------------------------------
# import sys, os
# os.chdir('/www/server/panel')
# sys.path.append("class/")

import  public, os,requests
_title = 'Docker API unauthorized access'
_version = 1.0  # 版本
_ps = "Docker API unauthorized access"  # 描述
_level = 3  # 风险级别： 1.提示(低)  2.警告(中)  3.危险(高)
_date = '2022-8-10'  # 最后更新时间
_ignore = os.path.exists("data/warning/ignore/sw_docker_api.pl")
_tips = [
    "Authentication should be turned on to authenticate or turn off the Docker Api"
]
_help = ''
_remind = "This solution fixes Docker's unauthorized access vulnerability, preventing attackers from using Docker to break into the server. We need to restrict API access to ensure that it does not affect the original website business operation. "

#
def get_local_ip():
    '''获取内网IP'''
    import socket
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(('8.8.8.8', 80))
        ip = s.getsockname()[0]
        return ip
    finally:
        s.close()
    return '127.0.0.1'

def check_run():
    '''
        @name 面板登录告警是否开启
        @time 2022-08-12
        @author lkq@aapanel.com
    '''
    try:
        if os.path.exists("/lib/systemd/system/docker.service"):
            data=public.ReadFile("/lib/systemd/system/docker.service")
            if not data:return  True, 'Risk-free'
            if '-H tcp://' in data:
                datas=requests.get("http://{}:2375/info".format(get_local_ip()),timeout=1)
                datas.json()
                if 'KernelVersion' in  datas.text and 'RegistryConfig' in datas.text and 'DockerRootDir' in datas.text:
                    return False,"Unauthorized access to the Docker API"
        return True, 'Risk-free'
    except:return True,"Risk-free"