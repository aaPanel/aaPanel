#!/usr/bin/python
# coding: utf-8

import os, sys, public

_title = 'Check if an empty password user exists'
_version = 1.0  # 版本
_ps = "Check if an empty password user exists"  # 描述
_level = 3  # 风险级别： 1.提示(低)  2.警告(中)  3.危险(高)
_date = '2023-11-21'  # 最后更新时间
_ignore = os.path.exists("data/warning/ignore/sw_empty_passwd_user.pl")
_tips = [
    "Log in to server as root, set password for empty password user ",
    "If you do not know the user's purpose, you can execute the command [passwd -l (username)] to temporarily block the user."
    "Unlock user command [passwd-fu (username)]"
]
_help = ''
_remind = 'detects the existence of blank password users, may be hackers reserved backdoor users, if not business needs to suggest setting a password. '


def check_run():
    '''
        @name 开始检测
        @author lwh<2023-11-21>
        @return tuple (status<bool>,msg<string>)
    '''
    user_list = []
    try:
        output, err = public.ExecShell('awk -F: \'($2 == "") {print}\' /etc/shadow')
        if err == '' and output != '':
            output_list = output.strip().split('\n')
            for op in output_list:
                user_list.append(op.split(':')[0])
        if len(user_list)>0:
            return False, 'Found an empty password user【{}】'.format('、'.join(user_list))
    except:
        return True, 'Risk-free'
    return True, 'Risk-free'
