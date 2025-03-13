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
# SSH 空闲超时时间检测
# -------------------------------------------------------------------
import re,public,os


_title = 'SSH idle timeout detection'
_version = 1.0                              # 版本
_ps = "SSH idle timeout detection"          # 描述
_level = 2                                  # 风险级别： 1.提示(低)  2.警告(中)  3.危险(高)
_date = '2022-8-10'                        # 最后更新时间
_ignore = os.path.exists("data/warning/ignore/sw_ssh_clientalive.pl")
_tips = [
    "Set [ClientAliveInterval] in the [/etc/ssh/sshd_config] file to be between 600 and 900",
    "Tip: The recommended SSH idle timeout time is: 600-900"
    ]

_help = ''
_remind = 'This scheme can enhance the security of SSH service, after the repair of SSH connection for a long time without operation will automatically quit, to prevent others from using. '


def check_run():
    '''
        @name SSH 空闲超时检测
        @time 2022-08-10
        @author lkq<2020-08-10>
        @return tuple (status<bool>,msg<string>)
    '''
    if os.path.exists('/etc/ssh/sshd_config'):
        try:
            info_data=public.ReadFile('/etc/ssh/sshd_config')
            if info_data:
                if re.search(r'ClientAliveInterval\s+\d+',info_data):
                    clientalive=re.findall(r'ClientAliveInterval\s+\d+',info_data)[0]
                    #clientalive 需要大于600 小于900
                    if int(clientalive.split(' ')[1]) >= 600 and int(clientalive.split(' ')[1]) <= 900:
                        return True,'Rick-free'
                    else:
                        return False,'The current SSH idle timeout time is: '+clientalive.split(' ')[1]+', it is recommended to set it to 600-900'
                else:
                    return True,'Rick-free'
        except:
            return True,'Rick-free'
    return True,'Rick-free'

def repaired():
    '''
        @name 修复ssh最大连接数
        @author lkq<2022-08-10>
        @return tuple (status<bool>,msg<string>)
    '''
    # 暂时不处理
    pass
