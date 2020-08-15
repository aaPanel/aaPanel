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
# 检测风险用户
# -------------------------------------------------------------------


import os,sys,re,public

_title = 'Risk User'
_version = 1.0                              # 版本
_ps = "Detect if there is a risk user in the system user list"      # 描述
_level = 2                                  # 风险级别： 1.提示(低)  2.警告(中)  3.危险(高)
_date = '2020-08-05'                        # 最后更新时间
_ignore = os.path.exists("data/warning/ignore/sw_login_user.pl")
_tips = [
    "If these users are not added by the server administrator, the system may have been compromised and should be dealt with as soon as possible."
    ]

_help = ''


def check_run():
    '''
        @name 开始检测
        @author hwliang<2020-08-04>
        @return tuple (status<bool>,msg<string>)
    '''

    u_list = get_ulist()

    try_users = []
    for u_info in u_list:
        if u_info['user'] == 'root': continue
        if u_info['pass'] == '*': continue
        if u_info['uid'] == 0:
            try_users.append(u_info['user'] + ' > Unknown administrator user [high risk]')
        
        if u_info['login'] in ['/bin/bash','/bin/sh']:
            try_users.append(u_info['user'] + ' > Logged-in user [medium risk]')

    if try_users:
        return False, 'There are security risks for the following users: <br />' + ('<br />'.join(try_users))

    return True,'Risk-free'
        


#获取用户列表
def get_ulist():
    u_data = public.readFile('/etc/passwd')
    u_list = []
    for i in u_data.split("\n"):
        u_tmp = i.split(':')
        if len(u_tmp) < 3: continue
        u_info = {}
        u_info['user'],u_info['pass'],u_info['uid'],u_info['gid'],u_info['user_msg'],u_info['home'],u_info['login'] = u_tmp
        u_list.append(u_info)
    return u_list