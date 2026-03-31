#!/usr/bin/python
#coding: utf-8
import os
import public
import re

_title = 'CVE-2023-0386 Linux Kernel OverlayFS Vulnerability'
_version = 1.0  # 版本
_ps = "CVE-2023-0386 Linux Kernel OverlayFS Vulnerability"  # 描述
_level = 3  # 风险级别： 1.提示(低)  2.警告(中)  3.危险(高)
_date = '2023-06-06'  # 最后更新时间
_ignore = os.path.exists("data/warning/ignore/sw_cve_2023_0386.pl")
_tips = [
    "Check whether the kernel version is lower than the specified version according to the prompt [uname -r]",
    "If is CentOS 8 Stream, execute [yum install kernel] command to upgrade the kernel version, and restart the server",
    "If it Ubuntu 22.04, execute [apt install linux-image] to check the installable version number, select version number higher than 5.15.0-70, execute [apt install linux-image-version_number] again, and restart the server"
]
_help = ''
_remind = 'The above kernel upgrade operation has certain risks, it is strongly recommended that the server do a snapshot backup first, in case the operation fails to restore in time! '

# https://nvd.nist.gov/vuln/detail/CVE-2023-0386
def check_run():
    '''
        @name 开始检测
        @return tuple (status<bool>,msg<string>)
    '''
    kernel = public.ExecShell('uname -r')[0]
    result = re.search("^(\\d+.\\d+.\\d+-\\d+)", kernel)
    # centos8
    if os.path.exists('/etc/redhat-release'):
        ver = public.ReadFile('/etc/redhat-release')
        if ver.startswith('CentOS Stream release 8'):
            if result:
                result = result.group(1).split('.')
                result = result[:2] + result[2].split('-')
                if len(result) == 4:
                    if result[0] == '4' and result[1] == '18' and result[2] == '0':
                        if len(result[3]) <= 3:
                            fin = contrast(result[3], 425)
                            if not fin:
                                return False, 'The current kernel version [{}] has security risks, please upgrade to 4.18.0-425 and above as soon as possible'.format(kernel)
    if os.path.exists('/etc/issue'):
        ver = public.ReadFile('/etc/issue')
        if ver.startswith('Ubuntu 22.04'):
            if result:
                result = result.group(1).split('.')
                result = result[:2] + result[2].split('-')
                print(result)
                if len(result) == 4:
                    if result[0] == '5' and result[1] == '15' and result[2] == '0':
                        if len(result[3]) <= 3:
                            fin = contrast(result[3], 70)
                            if not fin:
                                return False, 'The current kernel version [{}] has security risks, please upgrade to 5.15.0-70 and above as soon as possible'.format(kernel)
    return True, 'The current kernel version [{}] is risk-free'.format(kernel)


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

