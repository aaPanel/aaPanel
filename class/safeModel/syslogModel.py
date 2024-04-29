#coding: utf-8
#-------------------------------------------------------------------
# 宝塔Linux面板
#-------------------------------------------------------------------
# Copyright (c) 2015-2099 宝塔软件(http://bt.cn) All rights reserved.
#-------------------------------------------------------------------
# Author: hwliang <hwl@bt.cn>
#-------------------------------------------------------------------

# 系统日志
#------------------------------
import datetime
import json
import os
import re
import sys
import time

import public
from safeModel.base import safeBase


class main(safeBase):

    def __init__(self):
        ssh_cache_path = "{}/data/ssh".format(public.get_panel_path())
        if not os.path.exists(ssh_cache_path): os.makedirs(ssh_cache_path,384)


    #*********************************************** start ssh收费模块  ******************************************************

    def get_ssh_list(self,get):
        """
        @获取SSH登录
        @param get:
            count :数量
        """
        select_pl = ['Accepted', 'Failed password for']
        if hasattr(get, 'select'):
            if get.select == "Accepted":
                select_pl = ['Accepted']
            elif get.select == "Failed":
                select_pl = ['Failed password for']

        p = 1
        count = 20

        if 'count' in get: count = int(get['count'])
        if 'p' in get: p = int(get['p'])

        result = []
        min,max = (p -1) * count,  p * count

        log_list = self.get_log_byfile(self.get_ssh_log_files(get)[0], min, max,
                                       self.__get_search_list(get, select_pl))
        for log in log_list:
            data = self.get_ssh_log_line(log['log'],log['time'])
            if not data: continue

            result.append(data)

        if p < 1000000: public.set_module_logs('ssh_log','get_ssh_list')
        return public.return_area(result,'address')



    def get_ssh_error(self,get):
        """
        @获取SSH错误次数
         @param get:
            count :数量
        """
        p = 1
        count = 20
        if 'count' in get: count = int(get['count'])
        if 'p' in get: p = int(get['p'])

        result = []
        min,max = (p -1) * count, p * count

        log_list = self.get_log_byfile(self.get_ssh_log_files(get)[0],min,max,self.__get_search_list(get,['Failed password for']))

        for log in log_list:
            data = self.get_ssh_log_line(log['log'],log['time'])
            if not data:continue
            result.append(data)

        if p < 1000000: public.set_module_logs('ssh_log','get_ssh_list')
        return public.return_area(result,'address')

    def get_ssh_success(self,get):
        """
        @获取SSH登录成功次数
        @param get:
            count :数量
        """
        p = 1
        count = 20
        if 'count' in get: count = int(get['count'])
        if 'p' in get: p = int(get['p'])

        result = []
        min,max  = (p -1) * count,p * count

        log_list = self.get_log_byfile(self.get_ssh_log_files(get)[0],min,max,self.__get_search_list(get,['Accepted']))

        for log in log_list:
            data = self.get_ssh_log_line(log['log'],log['time'])
            if not data: continue

            result.append(data)
        if p < 1000000: public.set_module_logs('ssh_log','get_ssh_list')
        return public.return_area(result,'address')


    def __get_search_list(self,get,slist):
        """
        @组合搜索条件
        return list 查询组合
               status 1 增加查询条件
        """
        res = []
        if 'search' in get and get['search'].strip():
            search = get['search'].strip()
            for info in slist:
                res.append(info +'&' + search)
            if len(res) == 0:
                return search
            return res
        return slist


    def get_ssh_log_line(self,log,log_time):
        '''
            @name 获取ssh日志行
            @param log<str> 日志行
            @param log_time<str> 前一条记录的日志时间
        '''
        tmps = log.replace('  ',' ').split(' ')
        if len(tmps) < 3:
            return False

        data = {}
        data['time'] = log_time
        if log.find('closed by authenticating user') != -1:
            data['user'] = tmps[10]
            data['address'] = tmps[11]
            data['port'] = tmps[13]
        else:
            data['user'] = tmps[8]
            data['address'] = tmps[10]
            data['port'] = tmps[12]

        data['status'] = 0
        if log.find('Accepted') >= 0:
            data['status'] = 1
        return data

    #*********************************************** end ssh收费模块 ******************************************************



    def get_curr_log_file(self,filename,search,min,max,log_list):
        """
        @name 获取当前日志文件
        @param filename: 日志文件名
        @param search: 搜索条件
        @param min: 最小值
        @param max: 最大值
        @param log_list: 匹配的日志列表
        """

        log_list.clear()
        limit_max = '| tail -n {}'.format(max)
        if search[0].find('&') >= 0: limit_max = ''

        shells = [
            "cat {}|grep -a 'Failed password for' |grep -v 'invalid' {} ".format(filename,limit_max), #登录失败
            "cat {}|grep -a 'Accepted' {}".format(filename,limit_max),
            "cat {}|grep -E 'Failed password for|Accepted|Connection closed by authenticating user' |grep -v 'invalid' {} ".format(filename,limit_max),
            "cat {}|grep -a 'Connection closed by authenticating user' |grep -a 'preauth' {} ".format(filename,
                                                                                                      limit_max)
            # 登录失败
        ]
        if filename == 'journalctl':
            shells = [
                "journalctl -u ssh --no-pager|grep -a 'Failed password for' |grep -v 'invalid' {} ".format(limit_max),
                # 登录失败
                "journalctl -u ssh --no-pager|grep -a 'Accepted' {}".format(limit_max),
                "journalctl -u ssh --no-pager|grep -E 'Failed password for|Accepted|Connection closed by authenticating user' |grep -v 'invalid' {} ".format(
                    limit_max),
                "journalctl -u ssh --no-pager|grep -a 'Connection closed by authenticating user' |grep -a 'preauth' {} ".format(
                    limit_max)
                # 登录失败
        ]
        if len(search) == 1:
            if search[0].find('Accepted') >= 0:
                shells = [shells[1]]
            else:
                shells = [shells[0],shells[3]]
        else:
            shells = [shells[2]]

        result = []
        for shell in shells:

            res = public.ExecShell(shell)[0].strip().split('\n')
            res.reverse()
            for log in res:
                result.append(log)

        find_idx = 0
        log_time = 0
        limit = max - min
        for log in result:
            log_time = self.get_log_pre_time(filename,log,log_time)
            if len(log_list) >= limit:
                break

            if self.__find_line_str(log,search):

                find_idx += 1
                if find_idx > min:
                    log = public.xssencode2(log.replace('  ',' '))
                    log_list.append({'log':log,'time':log_time})

        return find_idx


    def get_sys_datetime(self,pre_time,log_time):
        """
        @name 对比日志时间，日志时间保存年份，日志时间比前一条时间大，则判断为上一年，
        @param pre_time 上一条日志时间
        @param log_time 当前日志时间
        @return 当前日志时间(校准年份)
        """

        if type(log_time) == str:
            log_time = self.__get_to_date(log_time)

        if type(pre_time) == str:
            pre_time = self.__get_to_date(pre_time)

        if (log_time > pre_time and pre_time > 0) or log_time >= time.time():
            d = datetime.datetime.strptime(public.format_date(times =log_time), "%Y-%m-%d %H:%M:%S")
            n_date = self.__get_to_date('{}-{}-{} {}:{}:{}'.format(d.year-1,d.month,d.day,d.hour,d.minute,d.second))
            return public.format_date(times=n_date)
        if type(log_time) == int:
            return public.format_date(times=log_time)
        return log_time



    def get_log_pre_time(self,log_file,_line,pre_time):
        """
        @name 计算上次日志时间
        @param log_file<str> 日志文件
        @param _line<str> 日志行
        @param pre_time<str> 上次日志时间
        @auther cjxin
        """
        log_time = 0
        if _line[:3] in self._months:
            log_time = self.to_date4(_line[:16].strip())
        elif _line[:2] in ['19','20','21','22']:
            log_time = _line[:19].strip()
        elif log_file.find('alternatives') >= 0:
            _tmp = _line.split(": ")
            _last = _tmp[0].split(" ")
            log_time = ' '.join(_last[1:]).strip()

        log_time = self.get_sys_datetime(pre_time,log_time)
        return log_time


    def get_user(self):
        '''
        @name 获取系统用户名
        :return:
        '''
        pass_file = public.readFile("/etc/passwd")
        pass_file = pass_file.split('\n')
        user_list = []
        for p in pass_file:
            p = p.split(':', 1)
            user_list.append(p[0])
        return user_list


    def get_log_byfile(self,sfile,min_num,max_num,search = None):
        """
        @name 获取日志文件的日志
        @param sfile:日志文件
        @param min_num:起始行数
        @param max_num:结束行数
        @param search:搜索关键字
        """
        log_list = []
        h_find = None
        #获取归档文件列表
        for info in self.get_sys_logfiles(None):
            if info['log_file'] == sfile:
                h_find = info
                break
        if os.path.exists('/etc/debian_version'):
            version = public.readFile('/etc/debian_version').strip()
            if 'bookworm' in version or 'jammy' in version or 'impish' in version:
                version = 12
            else:
                try:
                    version = float(version)
                except:
                    version = 11
            if version >= 12:
                h_find = {'log_file': 'journalctl', "list": [], 'uptime': time.time(), 'title': '授权日志',
                          'size': 10000}
        if not h_find:
            return log_list

        #获取遍历文件列表
        file_list = [h_find['log_file']]
        for info in h_find['list']:
            file_list.append(info['log_file'])

        find_idx = 0
        log_time = 0
        limit = max_num - min_num
        user_list = self.get_user()

        for filename in file_list:
            #处理最新文件

            if filename in ['/var/log/secure', '/var/log/auth.log', 'journalctl'] and search:
                find_idx = self.get_curr_log_file(filename,search,min_num,max_num,log_list)
                continue

            p = 0 #分页计数器
            next_file = False
            sfile = filename
            if filename[-3:] in ['.gz','.xz']: sfile = sfile[:-3]

            check_file,is_cache = self.__check_other_search(filename,search)
            if check_file:

                cache_path = '{}/data/ssh/{}{}'.format(public.get_panel_path(),os.path.basename(sfile),check_file)
                if not os.path.exists(cache_path):
                    self.__set_ssh_log(filename,check_file)
                filename = cache_path

            #数据不够，则解压归档文件进行查询
            if filename[-3:] in ['.gz','.xz']:
                public.ExecShell("gunzip -c " + filename + " > " + filename[:-3])
                filename = filename[:-3]

            while not next_file:
                if not os.path.exists(filename): continue # 文件不存在？
                if len(log_list) >= limit or os.path.getsize(filename) == 0:
                    break
                p += 1

                #public.print_log('读取文件：{},第{}页'.format(filename,p))
                #每次读取10000行，不足10000行跳转下个文件
                result = self.GetNumLines(filename,10001,p).split("\n")
                if len(result) < 10000:
                    next_file = True

                result.reverse()
                for _line in result:
                    if not _line.strip(): continue

                    log_time = self.get_log_pre_time(filename,_line,log_time)
                    #处理搜索关键词
                    is_search = False
                    if self.__find_line_str(_line,search):
                        is_search = True

                    #读取数量超过最大值，跳出
                    if len(log_list) >= limit:
                        break

                    if is_search:
                        find_idx += 1
                        if find_idx > min_num:
                            _line = public.xssencode2(_line.replace('  ',' '))
                            # 解决SSH登录日志搜索ip或用户名不准确的情况
                            if type(search) == list and len(search[0].split("&")) > 1:
                                rep_str = search[0].split("&")
                                rep = "\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}"
                                re_result = re.search(rep, _line).group()
                                if rep_str[1] in re_result:
                                    log_list.append({'log': _line, 'time': log_time})
                                elif rep_str[1] in user_list:
                                    log_list.append({'log': _line, 'time': log_time})
                            else:
                                log_list.append({'log':_line,'time':log_time})

        return log_list

    def __set_ssh_log(self,filename,check_file):
        """
        @name 缓存SSH登录日志
        @param filename<str> 缓存文件
        @param check_file<list> 文件类型
        """

        cache_path = '{}/data/ssh/{}{}'.format(public.get_panel_path(),os.path.basename(filename),check_file)

        if check_file == '_success':
            if filename == "journalctl":
                shell = "journalctl  -u ssh --no-pager|grep -a 'Accepted'"
            else:
                shell = "cat {}|grep -a 'Accepted'".format(filename)
        elif check_file == '_error':
            if filename == "journalctl":
                shell = "journalctl  -u ssh --no-pager|grep -E 'Failed password for|Connection closed by authenticating user' |grep -v 'invalid'"
            else:
                shell = "cat {}|grep -E 'Failed password for|Connection closed by authenticating user' |grep -v 'invalid'".format(
                    filename)
        else:
            if filename == "journalctl":
                shell = "journalctl  -u ssh --no-pager|grep -E 'Failed password for|Accepted|Connection closed by authenticating user' |grep -v 'invalid'"
            else:
                shell = "cat {}|grep -E 'Failed password for|Accepted|Connection closed by authenticating user' |grep -v 'invalid'".format(filename)

        if not os.path.exists(cache_path):
            res = public.ExecShell(shell)[0]
            public.writeFile(cache_path,res)
        return True

    def __check_other_search(self,filename,search):
        """
        @检测是否需要缓存ssh登录日志
        @filename<str> 文件名
        @search<str> 搜索关键字
        """
        if not search: return False,False

        if filename.find('secure-') >= 0 or filename.find('auth.log.') >= 0:
            res = search
            if type(search) == list:
                res = ' '.join(search)

            is_cache = False
            if res.find('&') == -1: is_cache = True

            if len(search) == 2:
                return '_all',is_cache
            if search[0].find('Accepted') >= 0:
                return '_success',is_cache
            return '_error',is_cache
        return False,False

    def __find_line_str(self,__line,find_str):
        """
        @ 批量搜索文件
        @ __line<str> 文件行
        @ find_str<str> 搜索关键字
        """
        if type(find_str) == list:
            if len(find_str) == 0:
                return True
            for search in find_str:
                if self.__find_str(__line,search.strip()):
                    return True
            return False
        else:
            if find_str:
                return self.__find_str(__line,find_str.strip())
            return True

    def __find_str(self,_line,find_str):
        """
        @查找关键词
        @_line<str> 文件行
        @find_str<str> 搜索关键字
        """
        is_num = 0
        slist = find_str.split("&")
        for search in slist:
            if search == 'Failed password for':
                #兼容多个系统的登录失败
                if _line.find(search) >= 0 and _line.find('invalid') == -1:
                    is_num += 1
                elif _line.find('Connection closed by authenticating user') >= 0 and _line.find('preauth') >= 0: #debian系统使用宝塔SSH终端登录失败
                    is_num += 1
            else:
                if _line.find(search) >= 0:
                    is_num += 1

        if is_num == len(slist):
            return True
        return False


    def get_log_title(self,log_name):
        '''
            @name 获取日志标题
            @author hwliang<2021-09-03>
            @param log_name<string> 日志名称
            @return <string> 日志标题
        '''
        log_name = log_name.replace('.1','')
        if log_name in ['auth.log','secure'] or log_name.find('auth.') == 0:
            return 'Authorization log'
        if log_name in ['dmesg'] or log_name.find('dmesg') == 0:
            return 'kernel buffer log'
        if log_name in ['syslog'] or log_name.find('syslog') == 0:
            return 'System warning/error log'
        if log_name in ['btmp']:
            return 'failed login record'
        if log_name in ['utmp','wtmp']:
            return 'Logon and restart records'
        if log_name in ['lastlog']:
            return 'User last logged in'
        if log_name in ['yum.log']:
            return 'yum package manager log'
        if log_name in ['anaconda.log']:
            return 'Anaconda log'
        if log_name in ['dpkg.log']:
            return 'dpkg package manager log'
        if log_name in ['daemon.log']:
            return 'System background daemon log'
        if log_name in ['boot.log']:
            return 'Boot oog'
        if log_name in ['kern.log']:
            return 'Kern log'
        if log_name in ['maillog','mail.log']:
            return 'Mail log'
        if log_name.find('Xorg') == 0:
            return 'Xorg log'
        if log_name in ['cron.log']:
            return 'Scheduled task log'
        if log_name in ['alternatives.log']:
            return 'Update alternate information'
        if log_name in ['debug']:
            return 'Debug log'
        if log_name.find('apt') == 0:
            return 'apt-get related logs'
        if log_name.find('installer') == 0:
            return 'System installation related logs'
        if log_name in ['messages']:
            return 'Comprehensive log'
        return '{} log'.format(log_name.split('.')[0])


    def get_history_filename(self,filepath):
        '''
        @name 获取归档文件名称
        @filepath<string> 文件路径
        '''
        log_name = os.path.basename(filepath)

        #归档压缩文件,auth.log.1.gz
        if filepath[-3:] in ['.gz','.xz']:
            log_file = filepath[:-3]
            if os.path.exists(log_file):
                return False
            log_name = os.path.basename(log_file)

        #处理auth.log-20221024
        if re.search('-(\d{8})',log_name):
            arrs = log_name.split('-')
            arrs = arrs[0 : len(arrs)-1]
            return '-'.join(arrs)
        #处理auth.log.1
        if re.search('.\d{1,10}$',log_name):
            arrs = log_name.split('.')
            arrs = arrs[0 : len(arrs)-1]
            return '.'.join(arrs)
        return log_name



    def get_sys_logfiles(self,get):
        '''
            @name 获取系统日志文件列表
            @author hwliang<2021-09-02>
            @param get<dict_obj>
            @return list
        '''
        res = {}
        log_dir = '/var/log'
        for log_file in os.listdir(log_dir):
            if log_file in ['.','..','faillog','fontconfig.log','unattended-upgrades','tallylog']: continue

            filename = os.path.join(log_dir,log_file)
            if os.path.isfile(filename):
                #归档文件原名
                log_name = self.get_history_filename(filename)
                if not log_name: continue

                if not log_name in res:
                    filepath = os.path.join(log_dir,log_name)
                    if not os.path.exists(filepath): continue

                    res[log_name] = {
                        'name':log_name,
                        'log_file':filepath,
                        'size':os.path.getsize(filepath),
                        'title': self.get_log_title(log_name),
                        'uptime': os.path.getmtime(filepath),
                        'list':[]
                    }

                if log_name != log_file:
                    res[log_name]['list'].append({
                            'name':log_file,
                            'size':os.path.getsize(filename),
                            'uptime': os.path.getmtime(filename),
                            'log_file':filename
                        })
            else:
                for next_name in os.listdir(filename):
                    next_file = os.path.join(filename,next_name)
                    if not os.path.isfile(next_file): continue

                    log_name = self.get_history_filename(next_file)
                    if not log_name: continue

                    if not log_name in res:

                        filepath = os.path.join(filename,log_name)
                        if not os.path.exists(filepath): continue

                        res[log_name] = {
                            'name':log_name,
                            'log_file':filepath,
                            'size':os.path.getsize(filepath),
                            'title': self.get_log_title(log_name),
                            'uptime': os.path.getmtime(filepath),
                            'list':[]
                        }

                    if log_name != next_name:
                        res[log_name]['list'].append({
                                'name':next_name,
                                'size':os.path.getsize(next_file),
                                'uptime': os.path.getmtime(next_file),
                                'log_file':next_file
                            })


        log_files = []
        for key in res:
            res[key]['list'] = sorted(res[key]['list'],key=lambda x:x['name'],reverse=True)
            log_files.append(res[key])
        log_files = sorted(log_files,key=lambda x:x['name'],reverse=True)
        return log_files


    def get_lastlog(self,get):
        '''
            @name 获取lastlog日志
            @author hwliang<2021-09-02>
            @param get<dict_obj>
            @return list
        '''
        cmd = '''LANG=en_US.UTF-8
lastlog|grep -v Username'''
        result = public.ExecShell(cmd)
        lastlog_list = []

        p = 1
        count = 20
        if 'count' in get: count = int(get['count'])
        if 'p' in get: p = int(get['p'])

        search = ''
        if 'search' in get:
            search = get.search

        idx = 0
        min,max = (p -1) * count,  p * count
        for _line in result[0].split("\n"):
            if not _line: continue
            if search and _line.find(search) == -1: continue

            _line = public.xssencode2(_line)
            tmp = {}
            sp_arr = _line.split()
            tmp['User'] = sp_arr[0]
            # tmp['_line'] = _line
            if _line.find('Never logged in') != -1:
                tmp['last login time'] = '0'
                tmp['Last login source'] = '-'
                tmp['Last login port'] = '-'

            else:
                tmp['last login time'] = sp_arr[2]
                tmp['Last login source'] = sp_arr[1]
                tmp['Last login port'] = self.to_date2(' '.join(sp_arr[3:]))

            if idx >= min and idx < max:
                lastlog_list.append(tmp)

            idx += 1
        lastlog_list = sorted(lastlog_list,key=lambda x:x['Last login port'],reverse=True)
        for i in range(len(lastlog_list)):
            if lastlog_list[i]['Last login port'] == '0': lastlog_list[i]['Last login port'] = 'never logged in'
        return lastlog_list


    def get_last(self,get):
        '''
            @name 获取用户会话日志
            @author hwliang<2021-09-02>
            @param get<dict_obj>
            @return list
        '''
        cmd = '''LANG=en_US.UTF-8
last -n 1000 -x -f {}|grep -v 127.0.0.1|grep -v " begins"'''.format(get.log_name)
        result = public.ExecShell(cmd)
        lastlog_list = []

        search = ''
        if 'search' in get:
            search = get.search

        p = 1
        count = 20
        if 'count' in get: count = int(get['count'])
        if 'p' in get: p = int(get['p'])

        idx = 0
        min,max = (p -1) * count,  p * count

        for _line in result[0].split("\n"):
            if not _line: continue
            if search and _line.find(search) == -1: continue

            _line = public.xssencode2(_line)
            tmp = {}
            sp_arr = _line.split()
            tmp['User'] = sp_arr[0]
            if sp_arr[0] == 'runlevel':
                tmp['Source'] = sp_arr[4]
                tmp['Port'] = ' '.join(sp_arr[1:4])
                tmp['Time'] = self.to_date3(' '.join(sp_arr[5:])) + ' ' +' '.join(sp_arr[-2:])
            elif sp_arr[0] in ['reboot','shutdown']:
                tmp['Source'] = sp_arr[3]
                tmp['Port'] = ' '.join(sp_arr[1:3])
                if sp_arr[-3] == '-':
                    tmp['Time'] = self.to_date3(' '.join(sp_arr[4:])) + ' ' +' '.join(sp_arr[-3:])
                else:
                    tmp['Time'] = self.to_date3(' '.join(sp_arr[4:])) + ' ' +' '.join(sp_arr[-2:])
            elif sp_arr[1] in ['tty1','tty','tty2','tty3','hvc0','hvc1','hvc2']  or len(sp_arr) == 9:
                tmp['Source'] = ''
                tmp['Port'] = sp_arr[1]
                tmp['Time'] = self.to_date3(' '.join(sp_arr[2:])) + ' ' +' '.join(sp_arr[-3:])
            else:
                tmp['Source'] = sp_arr[2]
                tmp['Port'] = sp_arr[1]
                tmp['Time'] = self.to_date3(' '.join(sp_arr[3:]))  + ' ' +' '.join(sp_arr[-3:])
            if idx >= min and idx < max:
                lastlog_list.append(tmp)
            idx += 1
        # lastlog_list = sorted(lastlog_list,key=lambda x:x['时间'],reverse=True)
        return lastlog_list



    def __get_to_date(self,times):
        """
        日期转时间戳
        """
        try:
            return int(time.mktime(time.strptime(times, "%Y-%m-%d %H:%M:%S")))
        except:
            try:
                return int(time.mktime(time.strptime(times, "%Y/%m/%d %H:%M:%S")))
            except:
                return 0



    def get_sys_log(self,get):
        '''
            @name  获取指定系统日志
            @author hwliang<2021-09-02>
            @param get<dict_obj>
            @return list
        '''

        log_file = get.log_name

        p,limit,search = 1,5,''
        if 'p' in get: p = int(get.p)
        if 'limit' in get: limit = int(get.limit)
        if 'search' in get: search = get.search

        sfile_name = os.path.basename(get.log_name)
        if sfile_name in ['wtmp','btmp','utmp'] :
            return self.get_last(get)

        if sfile_name in ['lastlog']:
            return self.get_lastlog(get)

        if get.log_name.find('sa/sa') >= 0:
            if get.log_name.find('sa/sar') == -1:
                return public.xssencode2(public.ExecShell("sar -f /var/log/{}".format(get.log_name))[0])

        is_string = True

        result = []
        min,max  = (p-1) * limit , p * limit  #最小值，最大值
        log_list = self.get_log_byfile(log_file,min,max,search)

        for info in log_list:
            _line = info['log']
            if _line[:3] in self._months:
                _tmps = _line.split(' ')
                _msg = ' '.join(_tmps[3:])
                _tmp = _msg.split(": ")
                _act = ''
                if len(_tmp) > 1:
                    _act = _tmp[0]
                    _msg = _tmp[1]
                else:
                    _msg = _tmp[0]
                _line = { "Time": info['time'], "Role":_act, "Even":_msg }
                is_string = False
            elif _line[:2] in ['19','20','21','22']:
                _msg = _line[19:]
                _tmp = _msg.split(" ")
                _act = _tmp[1]
                _msg = ' '.join(_tmp[2:])
                _line = { "Time":info['time'], "Role":_act, "Even":_msg }
                is_string = False
            elif log_file.find('alternatives') >= 0:
                _tmp = _line.split(": ")
                _last = _tmp[0].split(" ")
                _act = _last[0]
                _msg = ' '.join(_tmp[1:])
                _line = { "Time":info['time'], "Role":_act, "Even":_msg }
                is_string = False
            else:
                if not is_string:
                    if type(_line) != dict: continue

            result.append(_line)

        public.set_module_logs('sys_log','get_sys_log')
        try:
            _string = []
            _dict = []
            _list = []
            for _line in result:
                if isinstance(_line,str):
                    _string.append(_line.strip())
                elif isinstance(_line,dict):
                    _dict.append(_line)
                elif isinstance(_line,list):
                    _list.append(_line)
                else:
                    continue
            _str_len = len(_string)
            _dict_len = len(_dict)
            _list_len = len(_list)
            if _str_len >= _dict_len + _list_len:
                return _string
            elif _dict_len >= _str_len + _list_len:
                return _dict
            else:
                return _list
        except:
            return '\n'.join(result)



    #取文件指定尾行数
    def GetNumLines(self,path,num,p=1):
        pyVersion = sys.version_info[0]
        max_len = 1024*1024 * 2
        try:
            from cgi import html
            if not os.path.exists(path): return ""
            start_line = (p - 1) * num
            count = start_line + num
            fp = open(path,'rb')
            buf = ""
            fp.seek(-1, 2)
            if fp.read(1) == "\n": fp.seek(-1, 2)
            data = []
            total_len = 0
            b = True
            n = 0
            for i in range(count):
                while True:
                    newline_pos = str.rfind(str(buf), "\n")
                    pos = fp.tell()
                    if newline_pos != -1:
                        if n >= start_line:
                            line = buf[newline_pos + 1:]
                            line_len = len(line)
                            total_len += line_len
                            sp_len = total_len - max_len
                            if sp_len > 0:
                                line = line[sp_len:]
                            try:
                                data.insert(0,line)
                            except: pass
                        buf = buf[:newline_pos]
                        n += 1
                        break
                    else:
                        if pos == 0:
                            b = False
                            break
                        to_read = min(4096, pos)
                        fp.seek(-to_read, 1)
                        t_buf = fp.read(to_read)
                        if pyVersion == 3:
                            t_buf = t_buf.decode('utf-8')

                        buf = t_buf + buf
                        fp.seek(-to_read, 1)
                        if pos - to_read == 0:
                            buf = "\n" + buf
                    if total_len >= max_len: break
                if not b: break
            fp.close()
            result = "\n".join(data)
            if not result: raise Exception('null')
        except:
            result = public.ExecShell("tail -n {} {}".format(num,path))[0]
            if len(result) > max_len:
                result = result[-max_len:]

        try:
            try:
                result = json.dumps(result)
                return json.loads(result).strip()
            except:
                if pyVersion == 2:
                    result = result.decode('utf8',errors='ignore')
                else:
                    result = result.encode('utf-8',errors='ignore').decode("utf-8",errors="ignore")
            return result.strip()
        except: return ""