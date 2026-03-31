#!/usr/bin/python
# coding: utf-8

import re, os, public
_title = 'User FTP access security configuration'
_version = 1.0  # 版本
_ps = "User FTP access security configuration checks"  # 描述
_level = 2  # 风险级别： 1.提示(低)  2.警告(中)  3.危险(高)
_date = '2023-3-15'  # 最后更新时间
_ignore = os.path.exists("data/warning/ignore/sw_ftp_umask.pl")
_tips = [
    "In [/www/server/pure-ftpd/etc/pure-ftpd.conf] change the value of Umask to 177:077 in the config file",
]
_help = ''
_remind = 'This scheme can enhance the protection of FTP server and reduce the risk of server intrusion.'


def check_run():

    if os.path.exists('/www/server/pure-ftpd/etc/pure-ftpd.conf'):
        try:
            info_data = public.ReadFile('/www/server/pure-ftpd/etc/pure-ftpd.conf')
            if info_data:
                if re.search(r'.*Umask\s*177:077', info_data):
                    return True, 'Risk-free'
                else:
                    return False, 'Currently pure-ftpd is not configured with security access. Modify/add the value of Umask to 177:077 in the [pure-ftpd.conf] file'
        except:
            return True, 'Risk-free'
    return True, 'Risk-free'
