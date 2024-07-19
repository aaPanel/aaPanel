#!/usr/bin/python
#coding: utf-8

import os, re, public


_title = 'tomcat Background Access Weak Password Detection'
_version = 1.0  # 版本
_ps = "tomcat Background Access Weak Password Detection"  # 描述
_level = 3  # 风险级别： 1.提示(低)  2.警告(中)  3.危险(高)
_date = '2023-03-13'  # 最后更新时间
_ignore = os.path.exists("data/warning/ignore/sw_tomcat_pass.pl")
_tips = [
    "Change password weak password in【/usr/local/bttomcat/tomcat/conf/tomcat-users.xml】",
]
_help = ''
_remind = 'This scheme by strengthening the tomcat background login password strength, reduce the risk of being exploded, to avoid hackers using tomcat to invade the server. '


def check_run():
    '''
        @name 开始检测
        @return tuple (status<bool>,msg<string>)
    '''
    tomcat_conf = '/usr/local/bttomcat/tomcat{}/conf/tomcat-users.xml'
    version = ['7','8','9']
    vul_list = []
    # 第一步先用正则找到密码的输入点
    rep = 'password(\\s*)=(\\s*)[\"\'](.*?)[\"\']'
    for v in version:
        annotator = 0
        if not os.path.exists(tomcat_conf.format(v)):
            continue
        with open(tomcat_conf.format(v)) as f:
            lines = f.readlines()
            # 通过逐行判断是否存在注释符闭合，以annotator作锁计数，存在左闭合则+1，存在右闭合-1，当annotator值为0时才不在闭合范围内
            for l in lines:
                if '<!--' in l:
                    annotator += 1
                if '-->' in l:
                    annotator -= 1
                if '<!--' in l and '-->' in l:
                    continue
                if annotator != 0:
                    continue
                if 'manager-gui' in l and 'password' in l:
                    tmp = re.search(rep, l.rstrip())
                    passwd = tmp.group(3).strip()
                    for d in get_pass_list():
                        if passwd == d:
                            vul_list.append(v)
    if vul_list:
        return False, 'tomcat{} has a weak background password'.format('、'.join(vul_list))
    else:
        return True, 'Risk-free'


# 获取弱口令字典
def get_pass_list():
    pass_info = public.ReadFile("/www/server/panel/config/weak_pass.txt")
    return pass_info.split('\n')
