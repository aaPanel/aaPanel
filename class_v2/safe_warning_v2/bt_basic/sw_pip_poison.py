#!/usr/bin/python
#coding: utf-8

import os, re, public

_title = 'Pypi supply chain poisoning detection'
_version = 1.0  # 版本
_ps = "Pypi supply chain poisoning detection"  # 描述
_level = 2  # 风险级别： 1.提示(低)  2.警告(中)  3.危险(高)
_date = '2023-03-14'  # 最后更新时间
_ignore = os.path.exists("data/warning/ignore/sw_pip_poison.pl")
_tips = [
    "Execute the command btpip uninstall [detected malicious library name]",
]
_help = ''
_remind = 'This solution can remove vulnerable packages from the server and prevent them from being exploited by hackers. Before executing the solution command, make sure that the malicious library name is not a dependency library of normal business, otherwise it may affect the operation of the website. '

def check_run():
    pip = public.ExecShell("btpip freeze | grep -E \"istrib|djanga|easyinstall|junkeldat|libpeshka|mumpy|mybiubiubiu|nmap"
                               "-python|openvc|python-ftp|pythonkafka|python-mongo|python-mysql|python-mysqldb|python"
                               "-openssl|python-sqlite|virtualnv|mateplotlib|request=\"")[0].strip()
    if 'command not found' in pip or 'command not found' in pip:
        return True, 'Risk-free，pip is not installed'
    if pip:
        pip = pip.split('\n')
        return False, '【{}】security risk in the python library, please deal with it as soon as possible'.format('、'.join(pip))
    else:
        return True, 'Risk-free'

