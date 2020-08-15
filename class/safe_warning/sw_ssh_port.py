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
# SSH安全检测
# -------------------------------------------------------------------


import os,sys,re,public

_title = 'SSH security'
_version = 1.0                              # 版本
_ps = "Check whether the SSH port of the current server is safe"      # 描述
_level = 2                                  # 风险级别： 1.提示(低)  2.警告(中)  3.危险(高)
_date = '2020-08-04'                        # 最后更新时间
_ignore = os.path.exists("data/warning/ignore/sw_ssh_port.pl")
_tips = [
    "Modify the SSH port on the [Security] page, and consider turning off [SSH password login] in [SSH security management], and turning on [SSH key login]",
    "If SSH connection service is not required, it is recommended to disable SSH service on the [Security] page",
    "Through the [System Firewall] plug-in or in the [Security Group] modify the release behavior of the SSH port to limit the IP to enhance security",
    "Use [Fail2ban] plug-in to protect SSH service"
    ]

_help = ''


def check_run():
    '''
        @name 开始检测
        @author hwliang<2020-08-03>
        @return tuple (status<bool>,msg<string>)

        @example   
            status, msg = check_run()
            if status:
                print('OK')
            else:
                print('Warning: {}'.format(msg))
        
    '''

    file = '/etc/ssh/sshd_config'
    conf = public.readFile(file)
    if not conf: conf = ''
    rep = r"#*Port\s+([0-9]+)\s*\n"
    tmp1 = re.search(rep,conf)
    port = '22'
    if tmp1:
        port = tmp1.groups(0)[0]
    

    version = public.readFile('/etc/redhat-release')
    if not version:
        version = public.readFile('/etc/issue').strip().split("\n")[0].replace('\\n','').replace('\l','').strip()
    else:
        version = version.replace('release ','').replace('Linux','').replace('(Core)','').strip()

    if os.path.exists('/usr/bin/apt-get'):
        if os.path.exists('/etc/init.d/sshd'):
            status = public.ExecShell("service sshd status | grep -P '(dead|stop)'|grep -v grep")
        else:
            status = public.ExecShell("service ssh status | grep -P '(dead|stop)'|grep -v grep")
    else:
        if version.find(' 7.') != -1 or version.find(' 8.') != -1 or version.find('Fedora') != -1:
            status = public.ExecShell("systemctl status sshd.service | grep 'dead'|grep -v grep")
        else:
            status = public.ExecShell("/etc/init.d/sshd status | grep -e 'stopped' -e '已停'|grep -v grep")
        
    if len(status[0]) > 3:
        status = False
    else:
        status = True

    if not status:
        return True,'SSH service is not enabled'
    if port != '22':
        return True,'The default SSH port has been modified'
    
    result = public.check_port_stat(int(port),public.GetClientIp())
    if result == 0:
        return True,'Rick-free'
    
    return False,'The default SSH port ({}) has not been modified, and the access IP limit configuration has not been done, there is a risk of SSH breaching'.format(port)

