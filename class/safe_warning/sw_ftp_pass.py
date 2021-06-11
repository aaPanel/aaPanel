#!/usr/bin/python
# coding: utf-8
# -------------------------------------------------------------------
# 宝塔Linux面板
# -------------------------------------------------------------------
# Copyright (c) 2015-2099 宝塔软件(http://bt.cn) All rights reserved.
# -------------------------------------------------------------------
# Author: linxiao
# -------------------------------------------------------------------

# -------------------------------------------------------------------
# FTP弱口令检测
# -------------------------------------------------------------------

import os, re#, public

_title = 'FTP service weak password detection'
_version = 1.0  # 版本
_ps = "Detect weak passwords for the enabled FTP service"  # 描述
_level = 2  # 风险级别： 1.提示(低)  2.警告(中)  3.危险(高)
_date = '2020-09-19'  # 最后更新时间
_ignore = os.path.exists("data/warning/ignore/sw_ftp_pass.pl")
_tips = [
    "Please go to [FTP] page to change FTP password",
    "Note: Please do not use too simple account and password, so as not to cause security risks",
    "Use [Fail2ban] plug-in to protect FTP service"
]

_help = ''
_topic = "ftp"


def check_run():
    """检测FTP弱口令

        @author linxiao<2020-9-19>
        @return (bool, msg)
    """

    ftp_list = public.M("ftps").field("name,password,status").select()
    if not ftp_list:
        return True, 'Risk-free'
    weak_pass_ftp = []
    for ftp_info in ftp_list:
        status = ftp_info["status"]
        if status == "0" or status == 0:
            continue
        login_name = ftp_info["name"]
        login_pass = ftp_info["password"]
        if not is_strong_password(login_pass):
            weak_pass_ftp.append(login_name)

    if weak_pass_ftp:
        return False, "The following FTP service password settings are too simple and pose security risks: <br />" + \
               "<br />".join(weak_pass_ftp)
    return True, 'Risk-free'


def is_strong_password(password):
    """判断密码复杂度是否安全

    非弱口令标准：长度大于等于7，分别包含数字、小写、大写、特殊字符。
    @password: 密码文本
    @return: True/False
    @author: linxiao<2020-9-19>
    """

    if len(password) < 7:
        return False

    import re
    digit_reg = "[0-9]"  # 匹配数字 +1
    lower_case_letters_reg = "[a-z]"  # 匹配小写字母 +1
    upper_case_letters_reg = "[A-Z]"  # 匹配大写字母 +1
    special_characters_reg = r"((?=[\x21-\x7e]+)[^A-Za-z0-9])"  # 匹配特殊字符 +1

    regs = [digit_reg,
            lower_case_letters_reg,
            upper_case_letters_reg,
            special_characters_reg]

    grade = 0
    for reg in regs:
        if re.search(reg, password):
            grade += 1

    if grade == 4 or (grade >= 2 and len(password) >= 9):
        return True
    return False


# if __name__ == "__main__":
#     passwords = ["000000", "aaaaaaa", "Ab2aaaaaa"]
#     for p in passwords:
#         if is_strong_password(p):
#             print("密码：{} 安全性高。".format(p))
#         else:
#             print("密码：{} 安全性弱， 建议更换密码。".format(p))
