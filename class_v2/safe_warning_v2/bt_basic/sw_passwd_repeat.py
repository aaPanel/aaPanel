#!/usr/bin/python
#coding: utf-8

import os, re, public


_title = 'Check password reuse limit'
_version = 1.0  # 版本
_ps = "Detect whether to limit password reuse times"  # 描述
_level = 2  # 风险级别： 1.提示(低)  2.警告(中)  3.危险(高)
_date = '2023-03-10'  # 最后更新时间
_ignore = os.path.exists("data/warning/ignore/sw_passwd_repeat.pl")
_tips = [
    "Configuration file backup: cp -p /etc/pam.d/system-auth /etc/pam.d/system-auth.bak",
    "Add or modify remember=5 after [password sufficient] in [/etc/pam.d/system-auth] file"
]
_help = ''
_remind = 'This scheme enhances server access control protection by limiting the number of times login passwords are reused. '

def check_run():
    '''
        @name 开始检测
        @return tuple (status<bool>,msg<string>)
    '''
    try:
        cfile = '/etc/pam.d/system-auth'
        conf = public.readFile(cfile)
        rep = r"password(\s*)sufficient.*remember(\s*)=(\s*)[1-9]+"
        tmp = re.search(rep, conf)
        if tmp:
            return True, 'Risk-free'
        else:
            return False, 'Unlimited password reuse'
    except:
        return True, 'Risk-free'

