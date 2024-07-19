#!/usr/bin/python
#coding: utf-8

import os, re, public

_title = 'strace obtains login credentials backdoor detection'
_version = 1.0  # 版本
_ps = "Detect user information leakage via strace command during process"  # 描述
_level = 3  # 风险级别： 1.提示(低)  2.警告(中)  3.危险(高)
_date = '2023-03-09'  # 最后更新时间
_ignore = os.path.exists("data/warning/ignore/sw_strace_backdoor.pl")
_tips = [
    "The ps aux command checks whether there are sshd login credentials read through strace",
    "ps aux | grep strace",
    "If the process is filtered out, use the kill -9 [pid] command to stop the process"
]
_help = ''
_remind = 'detects the existence of hacker intrusion on the server, and the hacker behavior can be interrupted in time through the scheme command to prevent the server from being further invaded and controlled. '

def check_run():
    '''
        @name 开始检测
        @return tuple (status<bool>,msg<string>)
    '''
    sshd_pid = public.ExecShell('ps aux|grep "sshd -D"|grep -v grep|awk {\'print$2\'}')[0].strip()
    result = public.ExecShell('ps aux')[0].strip()
    rep = 'strace.*' + sshd_pid + '.*trace=read,write'
    tmp = re.search(rep, result)
    if tmp:
        return False, 'Malicious process that steals sshd login information through strace'
    else:
        return True, 'Risk-free'
