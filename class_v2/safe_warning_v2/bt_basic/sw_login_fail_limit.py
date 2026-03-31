#!/usr/bin/python
#coding: utf-8

import os, re, public


_title = 'Check account authentication failure limit'
_version = 1.0  # 版本
_ps = "Check whether to limit the number of account authentication failures"  # 描述
_level = 0  # 风险级别： 1.提示(低)  2.警告(中)  3.危险(高)
_date = '2023-03-20'  # 最后更新时间
_ignore = os.path.exists("data/warning/ignore/sw_login_fail_limit.pl")
_tips = [
    "Add or modify the second line of the [/etc/pam.d/sshd] file",
    "auth required pam_tally2.so onerr=fail deny=5 unlock_time=300 even_deny_root root_unlock_time=300"
]
_help = ''
_remind = 'This reduces the risk of a server being blown up. Be sure to remember your login password, though, in case you get locked out of your account for five minutes because of too many failed login attempts. '

def check_run():
    '''
        @name 开始检测
        @return tuple (status<bool>,msg<string>)
    '''
    cfile = '/etc/pam.d/sshd'
    if not os.path.exists(cfile):
        return True, 'Risk-free'
    conf = public.readFile(cfile)
    rep = r".*auth(\s*)required(\s*)pam_tally[2]?\.so.*deny(\s*)=.*unlock_time(\s*)=.*even_deny_root.*root_unlock_time(\s*)="
    tmp = re.search(rep, conf)
    if tmp:
        if tmp.group()[0] == '#':
            return False, 'The limit on the number of authentication failures is not configured or is improperly configured'
        return True, 'Risk-free'
    else:
        return False, 'The limit on the number of authentication failures is not configured or is improperly configured'

