#!/usr/bin/python
# coding: utf-8


import re, os, public
_title = 'Apache version leak'
_version = 1.0  # 版本
_ps = "Apache Version leak check"  # 描述
_level = 2  # 风险级别： 1.提示(低)  2.警告(中)  3.危险(高)
_date = '2023-03-14'  # 最后更新时间
_ignore = os.path.exists("data/warning/ignore/sw_httpd_version_leak.pl")
_tips = [
    "Add ServerSignature Off and ServerTokens Prod to the [httpd.conf] file",
]
_help = ''
_remind = 'This solution can enhance the protection of your server and reduce the risk of your website being compromised. '

def check_run():
    '''
        @name
        @author
        @return tuple (status<bool>,msg<string>)
    '''

    if os.path.exists('/www/server/apache/conf/httpd.conf'):
        try:
            info_data = public.ReadFile('/www/server/apache/conf/httpd.conf')
            if info_data:
                if not re.search('ServerSignature', info_data) and not re.search('ServerTokens',
                                                                                 info_data):
                    return True, 'Risk-free'
                if re.search('ServerSignature Off', info_data) and re.search('ServerTokens Prod',
                                                                             info_data):
                    return True, 'Risk-free'
                else:
                    return False, 'Currently Apache has a version leak problem, please add ServerSignature Off and ServerTokens Prod in the [httpd.conf] file'
        except:
            return True, 'Risk-free'
    return True, 'Risk-free'
