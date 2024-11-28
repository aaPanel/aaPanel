#!/usr/bin/python
# coding: utf-8


import re, os, public
_title = 'Apache TRACE request checks'
_version = 1.0  # 版本
_ps = "Apache TRACE request checks"  # 描述
_level = 2  # 风险级别： 1.提示(低)  2.警告(中)  3.危险(高)
_date = '2023-11-21'  # 最后更新时间
_ignore = os.path.exists("data/warning/ignore/sw_httpd_trace_enable.pl")
_tips = [
    "Set TraceEnable off in [httpd.conf] file and restart Apache server ",
    "Or handle security risks with one-click fixes."
]
_help = ''
_remind = 'TRACE request is generally used to test HTTP protocol. Attackers may use TRACE request combined with other vulnerabilities to perform cross-site scripting attacks to obtain sensitive information.'


def check_run():
    '''
        @name
        @author lwh<2023-11-22>
        @return tuple (status<bool>,msg<string>)
    '''

    if os.path.exists('/www/server/apache/conf/httpd.conf'):
        try:
            info_data = public.ReadFile('/www/server/apache/conf/httpd.conf')
            if info_data:
                if not re.search('TraceEnable off', info_data):
                    return False, 'TRACE requests are not currently disabled by Apache. Set TraceEnable off in the [httpd.conf] file'
        except:
            return True, 'Risk-free'
    return True, 'Risk-free'
