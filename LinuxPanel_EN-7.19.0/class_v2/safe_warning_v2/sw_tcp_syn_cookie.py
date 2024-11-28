#!/usr/bin/python
#coding: utf-8

import os, re, sys, public


_title = 'TCP-SYNcookie protection detection'
_version = 1.0  # 版本
_ps = "Check whether TCP-SYNcookie protection is enabled to mitigate syn flood attacks"  # 描述
_level = 1  # 风险级别： 1.提示(低)  2.警告(中)  3.危险(高)
_date = '2023-03-09'  # 最后更新时间
_ignore = os.path.exists("data/warning/ignore/sw_tcp_syn_cookie.pl")
_tips = [
    "Add net.ipv4.tcp_syncookies=1 in [/etc/sysctl.conf] file ",
    "Then execute the command sysctl -p to effect the configuration ",
]
_help = ''
_remind = 'This scheme can alleviate network flood attacks and enhance the stability of server operation. '


def check_run():
    '''
        @name 开始检测
        @return tuple (status<bool>,msg<string>)
    '''

    cfile = '/etc/sysctl.conf'
    conf = public.readFile(cfile)
    rep = r"\nnet.ipv4.tcp_syncookies(\s*)=(\s*)1"
    tmp = re.search(rep, conf)
    if tmp:
        return True, 'Risk-free'
    else:
        return False, 'TCP-SYNcookie protection is not enabled'

