#!/usr/bin/python
# coding: utf-8

import re, os, public

_title = 'Disable anonymous FTP login'
_version = 1.0  # 版本
_ps = "Disable Anonymous Login FTP Detection"  # 描述
_level = 2  # 风险级别： 1.提示(低)  2.警告(中)  3.危险(高)
_date = '2023-3-15'  # 最后更新时间
_ignore = os.path.exists("data/warning/ignore/sw_ftp_login.pl")
_tips = [
    "Modify the value of NoAnonymous to yes in the [/www/server/pure-ftpd/etc/pure-ftpd.conf] configuration file",
]
_help = ''
_remind = 'This scheme can enhance the FTP server protection, prevent illegal intrusion into the server. Unable to log in to the FTP server using Anonymous after configuration. '

def check_run():

    if os.path.exists('/www/server/pure-ftpd/etc/pure-ftpd.conf'):
        try:
            info_data = public.ReadFile('/www/server/pure-ftpd/etc/pure-ftpd.conf')
            if info_data:
                if re.search(r'.*NoAnonymous\s*yes', info_data):
                    return True, 'Risk-free'
                else:
                    return False, 'Currently pure-ftpd does not disable anonymous login, modify/add the value of NoAnonymous to yes in the [pure-ftpd.conf] file'
        except:
            return True, 'Risk-free'
    return True, 'Risk-free'
