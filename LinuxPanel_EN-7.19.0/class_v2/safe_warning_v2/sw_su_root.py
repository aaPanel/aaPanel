#!/usr/bin/python
# coding: utf-8

import os, re, public


_title = 'Check if the user outside the whell group su is disabled as root'
_version = 1.0  # 版本
_ps = "Check if the PAM authentication module is used to forbid users outside the wheel group su to be root"  # 描述
_level = 1  # 风险级别： 1.提示(低)  2.警告(中)  3.危险(高)
_date = '2023-03-10'  # 最后更新时间
_ignore = os.path.exists("data/warning/ignore/sw_su_root.pl")
_tips = [
    "In the file [/etc/pam.d/su] add auth sufficient pam_rootok.so and auth required pam_wheel.so group=wheel",
    "To configure the user to switch to root, add the user to the wheel group with gpasswd -d a username wheel",
]
_help = ''
_remind = 'This scheme enhances the protection of server permissions by forbidding low-privilege users to switch to root user. Make sure that there is no need for the business to switch root before fixing, otherwise ignore this risk item.'


def check_run():
    '''
        @name 开始检测
        @return tuple (status<bool>,msg<string>)
    '''
    cfile = '/etc/pam.d/su'
    if not os.path.exists(cfile):
        return True, 'Risk-free'
    conf = public.readFile(cfile)
    rep1 = r'[^#](\s*)auth(\s*)sufficient(\s*)pam_rootok.so'
    tmp1 = re.search(rep1, conf)
    if not tmp1:
        return False, 'Normal user su is not prohibited as the root user'
    rep2 = r'[^#](\s*)auth(\s*)required(\s*)pam_wheel.so(\s*)group(\s*)=(\s*)wheel'
    tmp2 = re.search(rep2, conf)
    if not tmp2:
        return True, 'Risk-free, But the whell group user can su is not configured'
    else:
        return True, 'Risk-free'
