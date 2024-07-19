#!/usr/bin/python
# coding: utf-8

import os, sys, public

_title = 'Check if an empty password sudo is allowed'
_version = 1.0  # 版本
_ps = "Check if an empty password sudo is allowed"  # 描述
_level = 2  # 风险级别： 1.提示(低)  2.警告(中)  3.危险(高)
_date = '2023-11-21'  # 最后更新时间
_ignore = os.path.exists("data/warning/ignore/sw_sudoers_nopasswd.pl")
_tips = [
    "Open /etc/sudoers or /etc/sudoers.d ",
    "Remove or comment the line of the [NOPASSWD] marker ",
    "Or handle security risks with one-click fixes."
]
_help = ''
_remind = 'When sudo uses the [NOPASSWD] flag, it allows users to execute commands using sudo without authenticating. This insecure configuration can lead to hackers gaining advanced privileges on the server.'


def check_run():
    '''
        @name 开始检测
        @author lwh<2023-11-21>
        @return tuple (status<bool>,msg<string>)
    '''
    risk_list = []
    sudo_file = "/etc/sudoers"
    sudo_dir = "/etc/sudoers.d/"
    if not os.path.exists(sudo_file):
        return True, 'Risk-free'
    try:
        output, err = public.ExecShell('grep -P \'^(?!#).*[\\s]+NOPASSWD[\\s]*\\:.*$\' {}'.format(sudo_file))
        if err == '' and output != '':
            risk_list.append(sudo_file)
        if os.path.exists(sudo_dir):
            import glob
            for filename in glob.glob(os.path.join(sudo_dir, '*')):
                output, err = public.ExecShell('grep -P \'^(?!#).*[\\s]+NOPASSWD[\\s]*\\:.*$\' {}'.format(filename))
                if err == '' and output != '':
                    risk_list.append(filename)
        if len(risk_list)>0:
            return False, 'The following sudo files contain the NOPASSWD flag:【{}】'.format('、'.join(risk_list))
    except:
        return True, 'Risk-free'
    return True, 'Risk-free'
