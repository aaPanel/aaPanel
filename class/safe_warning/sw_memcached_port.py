#!/usr/bin/python
#coding: utf-8
# -------------------------------------------------------------------
# 宝塔Linux面板
# -------------------------------------------------------------------
# Copyright (c) 2015-2099 宝塔软件(http://bt.cn) All rights reserved.
# -------------------------------------------------------------------
# Author: hwliang <hwl@bt.cn>
# -------------------------------------------------------------------

# -------------------------------------------------------------------
# Memcached安全检测
# -------------------------------------------------------------------

import os,sys,re,public

_title = 'Memcached security'
_version = 1.0                              # 版本
_ps = "Check whether the current Memcached is safe"             # 描述
_level = 2                                  # 风险级别： 1.提示(低)  2.警告(中)  3.危险(高)
_date = '2020-08-04'                        # 最后更新时间
_ignore = os.path.exists("data/warning/ignore/sw_memcached_port.pl")
_tips = [
    "Do not configure bindIP for Memcached as 0.0.0.0 unless necessary",
    "If bindIP is 0.0.0.0, be sure to set IP access restrictions through the [SYS firewall] plugin or the Security group"
    ]
_help = ''

def check_run():
    '''
        @name 开始检测
        @author hwliang<2020-08-03>
        @return tuple (status<bool>,msg<string>)
    '''

    p_file = '/etc/init.d/memcached'
    p_body = public.readFile(p_file)
    if not p_body: return True,'Risk-free'

    tmp = re.findall(r"^\s*IP=(0\.0\.0\.0)",p_body,re.M)
    if not tmp: return True,'Risk-free'
    
    tmp = re.findall(r"^\s*PORT=(\d+)",p_body,re.M)

    result = public.check_port_stat(int(tmp[0]),public.GetClientIp())
    if result == 0:
        return True,'Risk-free'
    
    return False,'The current Memcached port: {} allows arbitrary client access, which can lead to data leakage'.format(tmp[0])
    
