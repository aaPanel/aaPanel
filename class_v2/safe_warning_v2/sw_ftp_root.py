#!/usr/bin/python
# coding: utf-8

import re, os, public

_title = 'Forbid the root user to log in to FTP'
_version = 1.0  # 版本
_ps = "Prohibit the root user from logging in to FTP inspection"  # 描述
_level = 2  # 风险级别： 1.提示(低)  2.警告(中)  3.危险(高)
_date = '2023-3-15'  # 最后更新时间
_ignore = os.path.exists("data/warning/ignore/sw_ftp_root.pl")
_tips = [
    "Modify the value of MinUID to 100 in the [/www/server/pure-ftpd/etc/pure-ftpd.conf] configuration file",
]
_help = ''
_remind = 'This solution can be used to enhance the protection of your FTP server. After configuration, the root user cannot login ftp, use with caution. '

def check_run():
    if os.path.exists('/www/server/pure-ftpd/etc/pure-ftpd.conf'):
        try:
            info_data = public.ReadFile('/www/server/pure-ftpd/etc/pure-ftpd.conf')
            if info_data:
                tmp = re.search('\nMinUID\\s*([0-9]{1,4})', info_data)
                if tmp:
                    if int(tmp.group(1).strip()) < 100:
                        return False, 'Currently pure-ftpd is not configured with security access, modify/add the value of MinUID to 100 in the [pure-ftpd.conf] file'
                    else:
                        return True, 'Risk-free'
                else:
                    return False, 'Currently pure-ftpd is not configured with security access, modify/add the value of MinUID to 100 in the [pure-ftpd.conf] file'
        except:
            return True, 'Risk-free'
    return True, 'Risk-free'
