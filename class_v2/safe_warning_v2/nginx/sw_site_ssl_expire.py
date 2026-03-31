#!/usr/bin/python
#coding: utf-8
# -------------------------------------------------------------------
# aapanel
# -------------------------------------------------------------------
# Copyright (c) 2015-2099 aapanel(http://www.aapanel.com) All rights reserved.
# -------------------------------------------------------------------
# Author: hwliang <hwl@bt.cn>
# -------------------------------------------------------------------

# -------------------------------------------------------------------
# 网站证书过期检测
# -------------------------------------------------------------------

import os,sys,re,public,time

_title = 'Website certificate expiration detection'
_version = 1.0                              # 版本
_ps = "Check if all websites with deployed security certificates have expired"    # 描述
_level = 2                                  # 风险级别： 1.提示(低)  2.警告(中)  3.危险(高)
_date = '2020-08-04'                        # 最后更新时间
_ignore = os.path.exists("data/warning/ignore/sw_site_ssl_expire.pl")
_tips = [
    "Please renew or replace your SSL certificate to avoid affecting normal website access",
    "After the SSL certificate expires, users will be prompted by the browser that the website is unsafe, and most browsers will block access, seriously affecting online business"
    ]
_help = ''
_remind = 'SSL certificates ensure the security of website communication and prevent data from being stolen by hackers during transmission.'


def check_run():
    '''
        @name Start detection
        @author hwliang<2020-08-04>
        @return tuple (status<bool>,msg<string>)
    '''

    site_list = public.M('sites').field('id,name').select()

    not_ssl_list = []
    s_time = time.time()
    for site_info in site_list:
        ng_conf_file = '/www/server/panel/vhost/nginx/' + site_info['name'] + '.conf'
        if not os.path.exists(ng_conf_file): continue
        s_body = public.readFile(ng_conf_file)
        if not s_body: continue
        if s_body.find('ssl_certificate') == -1: continue

        cert_file = '/www/server/panel/vhost/cert/{}/fullchain.pem'.format(site_info['name'])
        if not os.path.exists(cert_file): continue

        cert_timeout = get_cert_timeout(cert_file)
        if s_time > cert_timeout:
            not_ssl_list.append(site_info['name'] + ' Expiration time: ' + public.format_date("%Y-%m-%d",cert_timeout))

    if not_ssl_list:
        return False ,'The following sites have expired SSL certificates: <br />' + ('<br />'.join(not_ssl_list))

    return True,'No risk'



# Get certificate expiration time
def get_cert_timeout(cert_file):
    try:
        # cert = split_ca_data(public.readFile(cert_file))
        # x509 = OpenSSL.crypto.load_certificate(
        #     OpenSSL.crypto.FILETYPE_PEM, cert)
        # cert_timeout = bytes.decode(x509.get_notAfter())[:-1]
        if "/www/server/panel/class" not in sys.path:
            sys.path.insert(0, "/www/server/panel/class")
        import ssl_info
        data = ssl_info.ssl_info().load_ssl_info(cert_file)

        return int(time.mktime(time.strptime(data["notAfter"], "%Y-%m-%d %H:%M:%S")))
    except:
        return time.time() + 86400



# Split root certificate
def split_ca_data(cert):
    datas = cert.split('-----END CERTIFICATE-----')
    return datas[0] + "-----END CERTIFICATE-----\n"
