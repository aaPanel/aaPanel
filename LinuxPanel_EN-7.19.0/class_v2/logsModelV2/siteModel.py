#coding: utf-8
#-------------------------------------------------------------------
# aaPanel
#-------------------------------------------------------------------
# Copyright (c) 2015-2099 aaPanel(www.aapanel.com) All rights reserved.
#-------------------------------------------------------------------
# Author: cjxin <bt_ahong@aapanel.com>
#-------------------------------------------------------------------

#------------------------------
# 面板日志类
#------------------------------

import os,re,json,time
from logsModel.base import logsBase
import public,db
from html import unescape,escape

class main(logsBase):

    def __init__(self):
        self.serverType = public.get_webserver()


    def __get_iis_log_files(self,path):
        """
        @name 获取IIS日志文件列表
        @param path 日志文件路径
        @return list
        """
        file_list = []
        if os.path.exists(path):
            for filename in os.listdir(path):
                if filename.find('.log') == -1: continue
                file_list.append('{}/{}'.format(path,filename))

        file_list = sorted(file_list,reverse=False)
        return file_list

    def get_iis_logs(self,get):
        """
        @name 获取IIS网站日志
        """

        p,limit,search = 1,2000,''
        if 'p' in get: limit = int(get.p)
        if 'limit' in get: limit = int(get.limit)
        if 'search' in get: search = get.search

        import panelSite
        site_obj = panelSite.panelSite()
        data = site_obj.get_site_info(get.siteName)
        if not data:
            return public.return_message(-1, 0, public.lang("[{}] Failed to get the website path, please check whether IIS exists this site, does not exist, please delete this site in the panel after the creation.", get.siteName))

        log_path = '{}/wwwlogs/W3SVC{}'.format(public.get_soft_path(), data['id'])
        file_list = self.__get_iis_log_files(log_path)

        find_idx = 0
        log_list = []
        for log_path in file_list:
            if not os.path.exists(log_path):  continue
            if len(log_list) >= limit: break

            p_num = 0 #分页计数器
            next_file = False
            while not next_file:
                if len(log_list) >= limit:
                    break
                p_num += 1
                result = self.GetNumLines(log_path,10001,p_num).split('\r\n')
                if len(result) < 10000:
                    next_file = True

                for _line in result:
                    if not _line: continue
                    if len(log_list) >= limit:
                        break

                    try:
                        if self.find_line_str(_line,search):
                            find_idx += 1
                            if find_idx > (p-1) * limit:
                                info = escape(_line)
                                log_list.append(info)
                    except:pass
        return public.return_message(0, 0, log_list)

    # 取网站日志
    def get_site_logs(self, get):
        logPath = ''
        if self.serverType == 'iis':
            return self.get_iis_logs(get)

        elif self.serverType == 'apache':
            logPath = self.setupPath + '/wwwlogs/' + get.siteName + '-access.log'
        else:
            logPath = self.setupPath + '/wwwlogs/' + get.siteName + '.log'

        data = {}
        data['path'] = ''
        data['path'] = os.path.dirname(logPath)
        if os.path.exists(logPath):
            data['status'] = True
            data['msg'] = public.GetNumLines(logPath, 1000)

            return public.return_message(0, 0, data)
        # data['status'] = False
        # data['msg'] = 'log is empty'
        # return data

        return public.return_message(-1, 0, 'log is empty')
