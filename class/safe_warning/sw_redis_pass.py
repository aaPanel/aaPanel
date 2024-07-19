#!/usr/bin/python
#coding: utf-8
# -------------------------------------------------------------------
# aaPanel
# -------------------------------------------------------------------
# Copyright (c) 2015-2099 aaPanel(www.aapanel.com) All rights reserved.
# -------------------------------------------------------------------
# Author: hwliang <hwl@aapanel.com>
# -------------------------------------------------------------------

# -------------------------------------------------------------------
# Redis 密码检测
# -------------------------------------------------------------------

import os,sys,re,public

_title = 'Redis weak password'
_version = 1.0                              # 版本
_ps = "Check if the current Redis password is secure"                 # 描述
_level = 3                                  # 风险级别： 1.提示(低)  2.警告(中)  3.危险(高)
_date = '2022-08-10'                        # 最后更新时间
_ignore = os.path.exists("data/warning/ignore/sw_redis_pass.pl")
_tips = [
    "1.Redis passwords are too simple"
    "2.Please change your password in time"
    ]
_help = ''
_remind = 'This solution reduces the risk of server intrusion by strengthening the database login password. '

def check_run():
    try:
        p_file = '/www/server/redis/redis.conf'
        p_body = public.readFile(p_file)
        if not p_body: return True, 'Risk-free'

        tmp = re.findall(r"^\s*requirepass\s+(.+)", p_body, re.M)
        if not tmp: return True, 'Risk-free'

        redis_pass = tmp[0].strip()
        pass_info=public.ReadFile("/www/server/panel/config/weak_pass.txt")
        if not pass_info: return True, 'Risk-free'
        pass_list = pass_info.split('\n')
        for i in pass_list:
            if i==redis_pass:
                return False, 'The Redis password [%s] is a weak password, please change the password'%redis_pass
        return True, 'Risk-free'
    except:
        return True, 'Risk-free'
