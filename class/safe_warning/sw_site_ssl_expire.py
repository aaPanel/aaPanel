#!/usr/bin/python
#coding: utf-8
# -------------------------------------------------------------------
# 宝塔Linux面板
# -------------------------------------------------------------------
# Copyright (c) 2015-2099 宝塔软件(http://bt.cn) All rights reserved.
# -------------------------------------------------------------------
# Author: hwliang <hwl@bt.cn>
# -------------------------------------------------------------------

# -------------------------------------------------------------------
# 网站证书过期检测
# -------------------------------------------------------------------

import os,sys,re,public,OpenSSL,time

_title = 'Website certificate expired'
_version = 1.0                              # 版本
_ps = "Check whether the websites SSL has expired"    # 描述
_level = 2                                  # 风险级别： 1.提示(低)  2.警告(中)  3.危险(高)
_date = '2020-08-04'                        # 最后更新时间
_ignore = os.path.exists("data/warning/ignore/sw_site_ssl_expire.pl")
_tips = [
    "Please renew or replace with a new SSL certificate for your site to avoid affecting normal website access",
    "After the SSL certificate expires, the user will be prompted by the browser to access the website as insecure, and most browsers will block access, seriously affecting online business"
    ]
_help = ''

def check_run():
    '''
        @name 开始检测
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
            not_ssl_list.append(site_info['name'] + ' Expiration: ' + public.format_date("%Y-%m-%d",cert_timeout))
        
    if not_ssl_list:
        return False ,'The following sites SSL certificate has expired: <br />' + ('<br />'.join(not_ssl_list))
    
    return True,'Rick-free'
        
        
    
# 获取证书到期时间
def get_cert_timeout(cert_file):
    try:
        cert = split_ca_data(public.readFile(cert_file))
        x509 = OpenSSL.crypto.load_certificate(
            OpenSSL.crypto.FILETYPE_PEM, cert)
        cert_timeout = bytes.decode(x509.get_notAfter())[:-1]
        return int(time.mktime(time.strptime(cert_timeout, '%Y%m%d%H%M%S')))
    except:
        return time.time() + 86400



# 拆分根证书
def split_ca_data(cert):
    datas = cert.split('-----END CERTIFICATE-----')
    return datas[0] + "-----END CERTIFICATE-----\n"
