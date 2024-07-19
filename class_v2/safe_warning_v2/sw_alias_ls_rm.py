#!/usr/bin/python
# coding: utf-8

import os, re, public


_title = 'Check alias configuration'
_version = 1.0  # 版本
_ps = "Check if the ls and rm commands set aliases"  # 描述
_level = 1  # 风险级别： 1.提示(低)  2.警告(中)  3.危险(高)
_date = '2023-03-10'  # 最后更新时间
_ignore = os.path.exists("data/warning/ignore/sw_alias_ls_rm.pl")
_tips = [
    "Add or modify alias ls=\'ls -alh\' and alias rm=\'rm -i\' in the file [~/.bashrc]",
    "Execute [source ~/.bashrc] to make the configuration take effect",
]
_help = ''
_remind = 'This scheme can make ls command list more detailed file information and reduce the risk of rm command deleting files by mistake, but it may affect the original operation habits.'

def check_run():
    '''
        @name 开始检测
        @return tuple (status<bool>,msg<string>)
    '''
    # 存放配置不当的命令，分别用正则判断是否配置别名
    result_list = []
    cfile = '/root/.bashrc'
    if not os.path.exists(cfile):
        return True, 'Risk-free'
    conf = public.readFile(cfile)
    # rep1 = 'alias(\\s*)ls(\\s*)=(\\s*)[\'\"]ls(\\s*)-.*[alh].*[alh].*[alh]'
    # tmp1 = re.search(rep1, conf)
    # if not tmp1:
    #     result_list.append('ls')
    rep2 = 'alias(\\s*)rm(\\s*)=(\\s*)[\'\"]rm(\\s*)-.*[i?].*'
    tmp2 = re.search(rep2, conf)
    if not tmp2:
        result_list.append('rm')
    if len(result_list) > 0:
        return False, '{} The command does not have an alias configured or is configured incorrectly'.format('、'.join(result_list))
    else:
        return True, 'Risk-free'
