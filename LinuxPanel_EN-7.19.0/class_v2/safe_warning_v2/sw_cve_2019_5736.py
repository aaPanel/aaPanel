#!/usr/bin/python
#coding: utf-8

import os, public, re

_title = 'CVE-2019-5736容器逃逸漏洞检测'
_version = 1.0  # 版本
_ps = "检测CVE-2019-5736容器逃逸漏洞"  # 描述
_level = 0  # 风险级别： 1.提示(低)  2.警告(中)  3.危险(高)
_date = '2023-03-27'  # 最后更新时间
_ignore = os.path.exists("data/warning/ignore/sw_cve_2019_5736.pl")
_tips = [
    "docker version查看docker版本是否小于18.09.2，runc版本小于1.0-rc6",
]
_help = ''
_remind = 'An attacker can use this vulnerability to gain access to the server. '

# https://nvd.nist.gov/vuln/detail/CVE-2019-5736#match-7231264
def check_run():
    '''
        @name 开始检测
        @return tuple (status<bool>,msg<string>)
    '''
    docker = public.ExecShell("docker version --format=\'{{ .Server.Version }}\'")[0].strip()
    if 'command not found' in docker or 'Command not found' in docker:
        return True, 'Risk-free，docker is not installed'
    if not re.search(r'\d+.\d+.\d+', docker):
        return True, 'Risk-free'
    docker = docker.split('.')
    if len(docker[0]) < 2:
        return False, 'Risky，The current docker version has security risks and needs to be upgraded to a safe version'
    elif int(docker[0]) < 18:
        return False, 'Risky，The current docker version has security risks and needs to be upgraded to a safe version'
    elif int(docker[0]) == 18:
        if int(docker[1]) < 9:
            return False, 'Risky，The current docker version has security risks and needs to be upgraded to a safe version'
        elif int(docker[1]) == 9:
            if int(docker[2][0]) < 2:
                return False, 'Risky，The current docker version has security risks and needs to be upgraded to a safe version'
            else:
                return True, 'Risk-free'
        else:
            return True, 'Risk-free'
    else:
        return True, 'Risk-free'