#coding: utf-8
#-------------------------------------------------------------------
# 宝塔Linux面板
#-------------------------------------------------------------------
# Copyright (c) 2015-2099 宝塔软件(http://bt.cn) All rights reserved.
#-------------------------------------------------------------------
# Author: cjxin <cjxin@bt.cn>
#-------------------------------------------------------------------
import copy
import random
# 获取目录大小
#------------------------------
import sys, os
import json, os, time, re

import public
from filesModel.base import filesBase

panelPath = '/www/server/panel'
os.chdir(panelPath)


class main(filesBase):
    _exe_cmd = 'ncdu'
    # 扫描历史
    log_path = '{}/data/scan/'.format(public.get_panel_path())
    # 缓存
    cache_file = '{}/config/scan_disk_cache.json'.format(public.get_panel_path())

    def __init__(self):
        self.is_use = False
        if os.path.isdir("{}/plugin/disk_analysis".format(public.get_panel_path())):
            self.is_use = True
        if not os.path.exists(self.log_path):
            os.makedirs(self.log_path)
        if not os.path.exists(self.cache_file):
            public.writeFile(self.cache_file,"{}")
        if os.getenv('BT_PANEL'):
            self._exe_cmd = '{}/plugin/disk_analysis/ncdu'.format(panelPath)

    def get_path_size(self, get):
        """
        @name 根据排除目录获取路径的总大小
        @param path 目标路径
        """
        if self.is_use is False:
            return {"code": 404, "status": False, "msg": 'Please install [Disk analysis] first !'}
        path = get.path
        is_refresh = get.is_refresh == "true"

        real_path_dict = {} # 软连接处理
        temp_path_list = []
        for path in str(path).split(","):
            r_path = os.path.realpath(path)
            if r_path != path:
                real_path_dict[r_path] = path
                path = r_path
            if path != "/": path = str(path).rstrip("/")
            temp_path_list.append(path)

        try:
            cache_data = json.loads(public.readFile(self.cache_file))
        except:
            cache_data = {}

        result = {}

        path_list = []
        if is_refresh is True:
            path_list = temp_path_list
        else:
            for path in temp_path_list:
                if cache_data.get(path) is not None:
                    result[path] = cache_data.get(path)
                else:
                    path_list.append(path)

        if path_list:
            scan_path = path_list[0]
            if os.path.isfile(scan_path):
                scan_path = os.path.split(scan_path)[0]
            for path in path_list[1:]:
                while True:
                    if path.startswith(scan_path):
                        break
                    scan_path = os.path.split(scan_path)[0]
            import string
            code = "".join(random.sample(string.ascii_letters + string.digits, 8))
            result_file = '{}{}'.format(self.log_path, f"temp_scan_size_{code}")
            scan_time = int(time.time())
            exec_shell = "{} '{}' -o '{}' ".format(self._exe_cmd, scan_path, result_file).replace('\\', '/').replace('//','/')
            public.ExecShell(exec_shell)
            scan_result = self.__get_log_size(result_file, path_list, scan_time, cache_data)
            os.remove(result_file)
            result.update(scan_result)
            public.writeFile(self.cache_file, json.dumps(cache_data))
        for r_path, path in real_path_dict.items():
            result[path] = result[r_path]
            del result[r_path]
        return result

    @classmethod
    def __get_log_size(cls, log_file, path_list, scan_time, cache_data):
        """
        @name 获取文件或目录大小
        @param log_file 日志文件
        """
        result = {}
        for path in path_list:
            result[path] = None
        data = public.readFile(log_file)
        data = json.loads(data)
        data = data[-1]
        root_path = data[0]["name"]
        if root_path in path_list:
            result[root_path] = data
        else:
            cls.__get_sub_size(data[1:], root_path, path_list, result)
        for path,info in result.items():
            if info is None:
                continue
            if isinstance(info, dict):
                info["type"] = 0
                info["asize"] = info.get("asize", 0)
                info["dsize"] = info.get("dsize", 0)
                info["dir_num"] = 0
                info["file_num"] = 0
                info["total_asize"] = info.get("asize", 0)
                info["total_dsize"] = info.get("dsize", 0)
                info["stime"] = scan_time
                cls.__get_stat(path, info)
                cache_data[path] = info
            else:
                cls.__get_dirs_size(info)
                cls.__get_stat(path, info[0])
                result[path] = info[0]
                result[path]["stime"] = scan_time
                cache_data[path] = result[path]
        return result

    @classmethod
    def __get_sub_size(cls, data, root_path, path_list, result):
        """
        @name 获取子目录数据
        @param id int 记录id
        @param path string 目录
        """
        if len(path_list) == 0: return
        for val in data:
            if isinstance(val, list):
                sfile = f"{root_path}/{val[0]['name']}".replace('\\', '/').replace('//', '/')
                if sfile in path_list:
                    result[sfile] = val
                    path_list.remove(sfile)
                if len(val) > 1:
                    cls.__get_sub_size(val[1:], sfile, path_list, result)
            elif isinstance(val, dict):
                sfile = f"{root_path}/{val['name']}".replace('\\', '/').replace('//', '/')
                if sfile in path_list:
                    result[sfile] = val
                    path_list.remove(sfile)

    @classmethod
    def __get_dirs_size(cls, dirs_list):
        """
        @param info 目录信息
        @param result 结果
        """
        dir_info = dirs_list[0]
        dir_info["type"] = 1
        dir_info["asize"] = dir_info.get("asize", 0)
        dir_info["dsize"] = dir_info.get("dsize", 0)
        dir_info["dirs"] = 0
        dir_info["files"] = 0
        dir_info["dir_num"] = 0
        dir_info["file_num"] = 0
        dir_info["total_asize"] = dir_info.get("asize", 0)
        dir_info["total_dsize"] = dir_info.get("dsize", 0)
        for info in dirs_list[1:]:
            if isinstance(info, list):  # 目录
                dir_info["dirs"] += 1
                dir_info["dir_num"] += 1
                cls.__get_dirs_size(info)
                temp_info = info[0]
                dir_info["dir_num"] += temp_info["dir_num"]
                dir_info["file_num"] += temp_info["file_num"]
                dir_info["total_asize"] += temp_info["total_asize"]
                dir_info["total_dsize"] += temp_info["total_dsize"]
            else:
                if info.get("excluded") == "pattern":
                    continue
                dir_info["files"] += 1
                dir_info["file_num"] += 1
                if info.get("asize") is None: info["asize"] = 0
                if info.get("dsize") is None: info["dsize"] = 0
                info["type"] = 0
                dir_info["total_asize"] += info["asize"]
                dir_info["total_dsize"] += info["dsize"]

    @classmethod
    def __get_stat(cls, path, info):
        if not os.path.exists(path):
            info["accept"] = None
            info["user"] = None
            info["mtime"] = "--"
            info["ps"] = None
            return
        stat_file = os.stat(path)

        info["accept"] = oct(stat_file.st_mode)[-3:]
        import pwd
        try:
            info["user"] = pwd.getpwuid(stat_file.st_uid).pw_name
        except:
            info["user"] = str(stat_file.st_uid)
        info["atime"] = int(stat_file.st_atime)
        info["ctime"] = int(stat_file.st_ctime)
        info["mtime"] = int(stat_file.st_mtime)
        info["ps"] = cls.get_file_ps(path)

    @classmethod
    def get_file_ps(cls,filename):
        '''
            @name 获取文件或目录备注
            @author hwliang<2020-10-22>
            @param filename<string> 文件或目录全路径
            @return string
        '''

        ps_path = public.get_panel_path() + '/data/files_ps'
        f_key1 = '/'.join((ps_path,public.md5(filename)))
        if os.path.exists(f_key1):
            return public.readFile(f_key1)

        f_key2 = '/'.join((ps_path,public.md5(os.path.basename(filename))))
        if os.path.exists(f_key2):
            return public.readFile(f_key2)

        pss = {
            '/www/server/data': 'This is the default data directory of the MySQL database, please do not delete it!',
            '/www/server/mysql': 'MySQL program directory',
            '/www/server/redis': 'Redis program directory',
            '/www/server/mongodb': 'MongoDB program directory',
            '/www/server/nvm': 'PM2/NVM/NPM program directory',
            '/www/server/pass': 'Website BasicAuth authentication password storage directory',
            '/www/server/speed': 'Website acceleration data directory',
            '/www/server/docker': 'Docker plugin and data directory',
            '/www/server/total': 'Website monitoring report data directory',
            '/www/server/btwaf': 'WAF firewall data directory',
            '/www/server/pure-ftpd': 'ftp program directory',
            '/www/server/phpmyadmin': 'phpMyAdmin program directory',
            '/www/server/rar': 'rar expansion library directory, will lose support for RAR compressed files after deletion',
            '/www/server/stop': 'The website deactivates the page directory, please do not delete it!',
            '/www/server/nginx': 'Nginx program directory',
            '/www/server/apache': 'Apache program directory',
            '/www/server/cron': 'Scheduled task script and log directory',
            '/www/server/php': 'PHP directory, all PHP version interpreters are in this directory',
            '/www/server/tomcat': 'Tomcat program directory',
            '/www/php_session': 'PHP-SESSION isolation directory',
            '/www/server/panel': 'aaPanel program directory',
            '/proc': 'system process directory',
            '/dev': 'system device directory',
            '/sys': 'system call directory',
            '/tmp': 'system temporary file directory',
            '/var/log': 'System log directory',
            '/var/run': 'System running log directory',
            '/var/spool': 'system queue directory',
            '/var/lock': 'system lock directory',
            '/var/mail': 'system mail directory',
            '/mnt': 'System mount directory',
            '/media': 'System multimedia directory',
            '/dev/shm': 'system shared memory directory',
            '/lib': 'system dynamic library directory',
            '/lib64': 'system dynamic library directory',
            '/lib32': 'system dynamic library directory',
            '/usr/lib': 'system dynamic library directory',
            '/usr/lib64': 'system dynamic library directory',
            '/usr/local/lib': 'system dynamic library directory',
            '/usr/local/lib64': 'system dynamic library directory',
            '/usr/local/libexec': 'system dynamic library directory',
            '/usr/local/sbin': 'System script directory',
            '/usr/local/bin': 'System script directory'


        }
        if filename in pss:  return "PS：" + pss[filename]
        return None