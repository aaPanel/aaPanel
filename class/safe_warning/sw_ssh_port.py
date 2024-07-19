#!/usr/bin/python
#coding: utf-8
# -------------------------------------------------------------------
# aaPanel
# -------------------------------------------------------------------
# Copyright (c) 2015-2099 aaPanel(www.aapanel.com) All rights reserved.
# -------------------------------------------------------------------
# Author: hwliang <hwl@aapanel.com>
# -------------------------------------------------------------------

# -------------------------------------------------------------------
# SSH安全检测
# -------------------------------------------------------------------


import os,sys,re,public,json

_title = 'SSH security'
_version = 1.0                              # 版本
_ps = "Check whether the SSH port of the current server is safe"      # 描述
_level = 1                                  # 风险级别： 1.提示(低)  2.警告(中)  3.危险(高)
_date = '2020-08-04'                        # 最后更新时间
_ignore = os.path.exists("data/warning/ignore/sw_ssh_port.pl")
_tips = [
    "Modify the SSH port on the [Security] page, and consider turning off [SSH password login] in [SSH security management], and turning on [SSH key login]",
    "If SSH connection service is not required, it is recommended to disable SSH service on the [Security] page",
    "Through the [System Firewall] plug-in or in the [Security Group] modify the release behavior of the SSH port to limit the IP to enhance security",
    "Use [Fail2ban] plug-in to protect SSH service"
    ]

_help = ''
_remind = "This solution reduces the risk of a breach by changing the default SSH login port. Noteafter the fix, you'll need to change the SSH port that the relevant business logs on to. "

def check_run():
    '''
        @name 开始检测
        @author hwliang<2022-08-18>
        @return tuple (status<bool>,msg<string>)

        @example   
            status, msg = check_run()
            if status:
                print('OK')
            else:
                print('Warning: {}'.format(msg))
        
    '''
    port = public.get_sshd_port()

    version = public.readFile('/etc/redhat-release')
    if not version:
        version = public.readFile('/etc/issue').strip().split("\n")[0].replace('\\n','').replace(r'\l','').strip()
    else:
        version = version.replace('release ','').replace('Linux','').replace('(Core)','').strip()

    status = public.get_sshd_status()

    fail2ban_file = '/www/server/panel/plugin/fail2ban/config.json'
    if os.path.exists(fail2ban_file):
        try:
            fail2ban_config = json.loads(public.readFile(fail2ban_file))
            if 'sshd' in fail2ban_config.keys():
                if fail2ban_config['sshd']['act'] == 'true':
                    return True,'Fail2ban is enable'
        except: pass

    if not status:
        return True,'SSH service is not enabled'
    if port != '22':
        return True,'The default SSH port has been modified'
    
    result = public.check_port_stat(int(port),public.GetLocalIp())
    if result == 0:
        return True,'Rick-free'
    
    return False,'The default SSH port ({}) has not been modified, and the access IP limit configuration has not been done, there is a risk of SSH breaching'.format(port)

