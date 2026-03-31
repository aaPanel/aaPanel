#!/usr/bin/python
#coding: utf-8
# -------------------------------------------------------------------
# aapanel
# -------------------------------------------------------------------
# Copyright (c) 2015-2099 aapanel(http://www.aapanel.com) All rights reserved.
# -------------------------------------------------------------------
# Author: lkq <lkq@bt.cn>
# -------------------------------------------------------------------
# Time: 2022-08-10
# -------------------------------------------------------------------
# Nginx 版本泄露
# -------------------------------------------------------------------

import re, public, os
_title = 'Nginx version disclosure'
_version = 1.0  # 版本
_ps = "Nginx version disclosure"  # 描述
_level = 2  # 风险级别： 1.提示(低)  2.警告(中)  3.危险(高)
_date = '2022-8-10'  # 最后更新时间
_ignore = os.path.exists("data/warning/ignore/sw_nginx_server.pl")
_tips = [
    "Set server_tokens off; in the [/www/server/nginx/conf/nginx.conf] file;",
    "Tip: server_tokens off;"
]
_help = ''
_remind = 'This solution strengthens server protection and reduces the risk of website intrusion.'

def check_run():
    '''
        @name Check nginx version disclosure
        @author lkq<2020-08-10>
        @return tuple (status<bool>,msg<string>)
    '''

    if os.path.exists('/www/server/nginx/conf/nginx.conf'):
        try:
            info_data = public.ReadFile('/www/server/nginx/conf/nginx.conf')
            if info_data:
                if re.search('server_tokens off;', info_data):
                    return True, 'No risk'
                else:
                    return False, 'Current Nginx has version disclosure. Please add or modify the server_tokens parameter to off in the Nginx configuration file, for example: server_tokens off;'
        except:
            return True, 'No risk'
    return True, 'No risk'
