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
        pass


    def get_logs_info(self,args):
        '''
            @name 获取分类日志信息
        '''
        data = public.M('logs').query('''
            select type,count(id) as 'count' from logs
            group by type
            order by count(id) desc
        ''')
        result = []
        for arrs in data:
            item = {}
            if not arrs: continue

            item['count'] = arrs[1]
            item['type'] = arrs[0]
            result.append(item)
        public.set_module_logs('get_logs_info','get_logs_info')
        return result

    def get_logs_bytype(self,args):
        """
        @name 根据类型获取日志
        @param args.type 日志类型
        """
        p,limit = 1,20
        if 'p' in args: p = int(args.p)
        if 'limit' in args: limit = int(args.limit)

        stype = args.stype
        search = '[' + str(args.search) + ']'

        where = "type=? and log like ? "

        count = public.M('logs').where(where,(stype,'%'+search+'%')).count()
        data = public.get_page(count,p,limit)
        data['data'] = public.M('logs').where(where,(stype,'%'+search+'%')).limit('{},{}'.format(data['shift'], data['row'])).order('id desc').select()

        return data


    def __get_panel_dirs(self):
        '''
            @name 获取面板日志目录
        '''
        dirs = []
        for filename in os.listdir('{}/logs/request'.format(public.get_panel_path())):
            if filename.find('.json') != -1:
                dirs.append(filename)

        dirs = sorted(dirs,reverse=True)
        return dirs



    def get_panel_log(self,get):
        """
        @name 获取面板日志
        """
        p,limit,search = 1,20,''
        if 'p' in get: p = int(get.p)
        if 'limit' in get: limit = int(get.limit)
        if 'search' in get: search = get.search

        find_idx = 0
        log_list = []
        dirs = self.__get_panel_dirs()
        for filename in dirs:
            log_path = '{}/logs/request/{}'.format(public.get_panel_path(),filename)
            if not os.path.exists(log_path): #文件不存在
                continue

            if len(log_list) >= limit:
                break

            p_num = 0 #分页计数器
            next_file = False
            while not next_file:
                if len(log_list) >= limit:
                    break
                p_num += 1
                result = self.GetNumLines(log_path,10001,p_num).split('\r\n')
                if len(result) < 10000:
                    next_file = True
                result.reverse()
                for _line in result:
                    if not _line: continue
                    if len(log_list) >= limit:
                        break

                    try:
                        if self.find_line_str(_line,search):
                            find_idx += 1

                            if find_idx > (p-1) * limit:

                                info = json.loads(unescape(_line))
                                for key in info:
                                    if isinstance(info[key],str):
                                        info[key] = escape(info[key])

                                info['address'] = info['ip'].split(':')[0]
                                log_list.append(info)
                    except:pass

        return public.return_area(log_list,'address')

    def get_panel_error_logs(self,get):
        '''
            @name 获取面板错误日志
        '''
        search = ''
        if 'search' in get:
            search = get.search
        filename = '{}/logs/error.log'.format(public.get_panel_path())
        if not os.path.exists(filename):
            return public.returnMsg(False, public.lang("No error log"))

        res = {}
        res['data'] = public.xssdecode(self.GetNumLines(filename,2000,1,search))
        res['data'].reverse()
        return res


    def __get_ftp_log_files(self,path):
        """
        @name 获取FTP日志文件列表
        @param path 日志文件路径
        @return list
        """
        file_list = []
        if os.path.exists(path):
            for filename in os.listdir(path):
                if filename.find('.log') == -1: continue
                file_list.append('{}/{}'.format(path,filename))

        file_list = sorted(file_list,reverse=True)
        return file_list

    def get_ftp_logs(self,get):
        """
        @name 获取ftp日志
        """

        p,limit,search,username = 1,500,'',''
        if 'p' in get: p = int(get.p)
        if 'limit' in get: limit = int(get.limit)
        if 'search' in get: search = get.search
        if 'username' in get: username = get.username

        find_idx = 0
        ip_list = []
        log_list = []
        dirs = self.__get_ftp_log_files('{}/ftpServer/Logs'.format(public.get_soft_path()))
        for log_path in dirs:

            if not os.path.exists(log_path): continue
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
                result.reverse()
                for _line in result:
                    if not _line.strip(): continue
                    if len(log_list) >= limit:
                        break
                    try:
                        if self.find_line_str(_line,search):
                            #根据用户名查找
                            if username and not re.search(r'-\s+({})\s+\('.format(username),_line):
                                continue

                            find_idx += 1
                            if find_idx > (p-1) * limit:
                                #获取ip归属地
                                for _ip in public.get_line_ips(_line):
                                    if not _ip in ip_list: ip_list.append(_ip)

                                info = escape(_line)
                                log_list.append(info)
                    except:pass

        return self.return_line_area(log_list,ip_list)


    #取慢日志
    def get_slow_logs(self,get):
        '''
            @name 获取慢日志
            @get.search 搜索关键字
        '''
        search,p,limit = '',1,1000
        if 'search' in get: search = get.search
        if 'limit' in get: limit = get.limit

        my_info = public.get_mysql_info()
        if not my_info['datadir']:
            return public.returnMsg(False, public.lang("MySQL is not installed!"))

        path = my_info['datadir'] + '/mysql-slow.log'
        if not os.path.exists(path):
            return public.returnMsg(False, public.lang("Log file does not exist!"))
        # mysql慢日志有顺序问题,倒序显示不利于排查问题
        return public.returnMsg(True, public.xsssec(public.GetNumLines(path, limit)))

        # find_idx = 0
        # p_num = 0 #分页计数器
        # next_file = False
        # log_list = []
        # while not next_file:
        #     if len(log_list) >= limit:
        #         break
        #     p_num += 1
        #     result = self.GetNumLines(path,10001,p_num).replace('\r\n','\n').split('\n')
        #     if len(result) < 10000:
        #         next_file = True
        #     result.reverse()

        #     for _line in result:
        #         if not _line: continue
        #         if len(log_list) >= limit:
        #             break

        #         try:
        #             if self.find_line_str(_line,search):
        #                 find_idx += 1
        #                 if find_idx > (p-1) * limit:
        #                     info = escape(_line)
        #                     log_list.append(info)
        #         except:pass
        # return log_list

    def IP_geolocation(self, get):
        '''
            @name 列出所有IP及其归属地
            @return list {ip: {ip: ip_address, operation_num: 12 ,info: 归属地}, ...]
        '''

        result = dict()

        data = public.M('logs').query('''
            select * from logs
        ''')
        for arrs in data:
            if not arrs: continue
            end = 0
            # 获得IP的尾后索引
            for ch in arrs[2]:
                if ch.isnumeric() or ch == '.':
                    end += 1
                else:
                    break

            ip_addr = arrs[2][0:end]

            if ip_addr:
                if result.get(ip_addr) != None:
                    result[ip_addr]["operation_num"] = result[ip_addr]["operation_num"] + 1
                else:
                    result[ip_addr] = {"ip":ip_addr,"operation_num":1, "info":None}

        return_list = []

        for k in result:
            info = public.get_free_ip_info(k)
            result[k]["info"] = info["info"]
            return_list.append(result[k])

        return return_list

    def get_error_logs_by_search(self, args):
         '''
             @name 根据搜索内容, 获取运行日志中的内容
             @args.search 匹配内容
             @return 匹配该内容的所有日志
         '''
         log_file_path = "{}/logs/error.log".format(public.get_panel_path())
         #return log_file_path
         data = public.readFile(log_file_path)
         if not data:
             return None
         data = data.split('\n')
         result = []
         for line in data:
            if args.search == None:
                result.append(line)
            elif args.search in line:
                result.append(line)

         return result