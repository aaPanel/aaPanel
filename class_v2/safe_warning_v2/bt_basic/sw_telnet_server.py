#!/usr/bin/python
# coding: utf-8

import sys, os, public
_title = 'Disable non-encrypted remote management telnet'
_version = 1.0  # 版本
_ps = "Turn off non-encrypted remote management telnet checks"  # 描述
_level = 2  # 风险级别： 1.提示(低)  2.警告(中)  3.危险(高)
_date = '2023-03-15'  # 最后更新时间
_ignore = os.path.exists("data/warning/ignore/sw_telnet_server.pl")
_tips = [
    "Use encrypted remote management sshd service as much as possible, and close unsafe telnet service",
    "systemctl stop telnet.socket stop telnet service"
]
_help = ''
_remind = 'This scheme shuts down the insecure telnet service, reducing the risk of data leakage. If the business requires telnet, this risk term is ignored. '

def check_run():
    result = public.ExecShell('systemctl is-active telnet.socket')[0].strip()
    if 'active' == result:
        return False, 'telnet service is not closed'
    else:
        return True, 'Risk-free'

