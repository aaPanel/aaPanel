#!/usr/bin/python
#coding: utf-8

import os, re, public

_title = 'CVE-2022-25845 Fastjson Arbitrary Code Execution vulnerability Detection'
_version = 1.0  # 版本
_ps = "CVE-2022-25845 Fastjson Arbitrary Code Execution vulnerability Detection"  # 描述
_level = 0  # 风险级别： 1.提示(低)  2.警告(中)  3.危险(高)
_date = '2023-03-13'  # 最后更新时间
_ignore = os.path.exists("data/warning/ignore/sw_cve_2022_25845.pl")
_tips = [
    "Open the pom.xml file in the website directory and check for fastjson dependencies."
    "If fastjson version is less than 1.2.83, upgrade to security version 1.2.83 or higher ",
]
_help = ''


# https://nvd.nist.gov/vuln/detail/CVE-2022-25845
def check_run():
    '''
        @name 开始检测
        @return tuple (status<bool>,msg<string>)
    '''
    web_list = []
    path = '/www/wwwroot/'
    pom = public.ExecShell("find {} |grep pom.xml".format(path))[0].split('\n')
    if pom[0]:
        for p in pom:
            if p == '':
                continue
            conf = public.ReadFile(p.strip())
            rep = r'<artifactId>fastjson</artifactId>(\s*)<version>(.*)</version>'
            tmp = re.search(rep, conf)
            rep1 = r'{}(.*)/'.format(path)
            if tmp:
                fastjson = tmp.group(2).split('.')
                if len(fastjson) == 3:
                    if fastjson[0] == '1' and fastjson[1] == '1':
                        if not contrast(fastjson[2], '157'):
                            web_list.append(re.search(rep1, p).group(1))
                    elif fastjson[0] == '1' and fastjson[1] == '2':

                        if not contrast(fastjson[2], '83'):
                            web_list.append(re.search(rep1, p).group(1))
        if web_list:
            return False, 'Website [{}] fastjson component has a security risk, need to upgrade the component to a secure version'.format('、'.join(web_list))
    return True, 'Risk-free'


def contrast(a, b):
    if len(a) >= 3:
        if a[0].isdigit() and a[1].isdigit() and a[2].isdigit():
            if int(a[0:3]) >= int(b):
                return True
            else:
                return False
        elif a[0].isdigit() and a[1].isdigit():
            if int(a[0:2]) >= int(b):
                return True
            else:
                return False
        elif a[0].isdigit():
            if int(a[0]) >= int(b):
                return True
            else:
                return False
        else:
            return False
    elif len(a) == 2:
        if a[0].isdigit() and a[1].isdigit():
            if int(a[0:2]) >= int(b):
                return True
            else:
                return False
        elif a[0].isdigit():
            if int(a[0]) >= int(b):
                return True
            else:
                return False
        else:
            return False
    elif len(a) == 1:
        if a[0].isdigit():
            if int(a[0]) >= int(b):
                return True
            else:
                return False
        else:
            return False
    else:
        return False
