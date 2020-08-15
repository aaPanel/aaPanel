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
# 面板安全入口检测
# -------------------------------------------------------------------

import os,sys,re,public

_title = 'Safe entrance'
_version = 1.0                              # 版本
_ps = "Check the security entrance security of the panel"           # 描述
_level = 3                                  # 风险级别： 1.提示(低)  2.警告(中)  3.危险(高)
_date = '2020-08-04'                        # 最后更新时间
_ignore = os.path.exists("data/warning/ignore/sw_panel_path.pl")
_tips = [
    "Please modify the security entrance on the [Settings] page",
    "Set the binding domain name on the [Settings] page, or set authorized IP restrictions",
    "Note: Please do not set up too simple safety entrance, which may cause safety hazards"
    ]
_help = ''

def check_run():
    '''
        @name 开始检测
        @author hwliang<2020-08-03>
        @return tuple (status<bool>,msg<string>)
    '''

    p_file = '/www/server/panel/data/domain.conf'
    if public.readFile(p_file):
        return True,'Risk-free'

    p_file = '/www/server/panel/data/limitip.conf'
    if public.readFile(p_file):
        return True,'Risk-free'
    

    p_file = '/www/server/panel/data/admin_path.pl'
    p_body = public.readFile(p_file)
    if not p_body: return False,'No security entrance is set, the panel is at risk of being scanned'
    p_body = p_body.strip('/').lower()
    if p_body == '': return False,'No security entrance is set, the panel is at risk of being scanned'

    lower_path = ['root','admin','123456','123','12','1234567','12345','1234','12345678','123456789','abc','bt']
    
    if p_body in lower_path:
        return False,'The security entrance is: {}, too simple, there are potential safety hazards'.format(p_body)
    
    lower_rule = 'qwertyuiopasdfghjklzxcvbnm1234567890'
    for s in lower_rule:
        for i in range(12):
            if not i: continue
            lp = s * i
            if p_body == lp:
                return False,'The security entrance is: {}, too simple, there are potential safety hazards'.format(p_body)
    
    return True,'Risk-free'
