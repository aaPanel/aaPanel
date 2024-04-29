#coding: utf-8
#-------------------------------------------------------------------
# 宝塔Linux面板
#-------------------------------------------------------------------
# Copyright (c) 2015-2099 宝塔软件(http://bt.cn) All rights reserved.
#-------------------------------------------------------------------
# Author: cjxin <cjxin@bt.cn>
#-------------------------------------------------------------------

#
#------------------------------

import os, re
from filesModel.base import filesBase
import public, json
from html import escape


class main(filesBase):

    __s_class = []

    def __init__(self):
        for i in range(1, 100):
            self.__s_class.append('f-s-%s' % i)

    def get_search_status(self, get):
        """
        @name 验证是否可用
        """
        return public.returnMsg(True, '1')

    def get_search_result(self, get):
        """
        @name 搜索文件
        @param get
            path:搜索路径
            search:搜索关键字
            limit:每页显示条数
            p:页码
        """
        result = {}
        is_dir = 0
        search = []

        if not 'ext' in get: get.ext = '*'
        if 'search' in get: search = get.search
        if 'is_dir' in get: is_dir = get.is_dir

        public.set_module_logs('searchModel', 'get_search_result')
        if not is_dir:
            if len(search) == 0:
                return public.returnMsg(False, 'Please enter search keywords!')

        if not os.path.exists(get.path):
            return public.returnMsg(False, 'Search directory does not exist!')

        slist = self.get_search_files(get)
        if is_dir: return slist
        num = 0
        total_num = len(slist)
        if slist: public.writeSpeed('files_search', num, total_num)
        for sfile in slist:
            data = self.__check_file_contents(sfile, search)
            if data:
                result[sfile] = data
            num += 1
            public.writeSpeed('files_search', num, total_num)
            progress = int(public.getSpeed()['progress'])
            if '_ws' in get:
                get._ws.send(
                    public.getJson({
                        "end": False if progress < 100 else True,
                        "ws_callback": get.ws_callback,
                        "file": sfile,
                        "progress": progress,
                        "total": total_num,
                        "num": num,
                        "type": "get_search_result"
                    }))
        if not slist and '_ws' in get:
            get._ws.send(
                public.getJson({
                    "end": True,
                    "ws_callback": get.ws_callback,
                    "file": '',
                    "progress": 100,
                    "total": 0,
                    "num": 0,
                    "type": "get_search_result"
                }))
        return result

    def get_search_files(self, get):
        """
        @name 搜索文件
        @param get
            path:搜索路径
            search:搜索关键字
        """

        data = {}

        data['is_sub'] = 0
        if 'is_sub' in get:
            data['is_sub'] = int(get.is_sub)

        data['ext'] = []
        for ext in get.ext.split(','):
            if ext: data['ext'].append(ext)

        data['s_time'] = 0
        data['e_time'] = 4070880000
        if 's_time' in get:
            data['s_time'] = int(get.s_time)
        if 'e_time' in get:
            data['e_time'] = int(get.e_time)

        data['min_size'] = 0
        data['max_size'] = 1024 * 1024 * 10
        if 'min_size' in get:
            data['min_size'] = int(get.min_size)

        if 'max_size' in get:
            data['max_size'] = int(get.max_size)

        data['names'] = []
        if 'names' in get:
            data['names'] = get.names

        flist = []
        self.__get_file_list(get.path, data, flist)

        return flist

    def __check_file_contents(self, sfile, contents):
        """
        @name 验证文件内容
        @param sfile:文件路径
        @param contents:文件内容
        """
        n = 1
        result = {}
        try:
            for line in open(sfile, 'rb'):
                try:
                    if type(line) == bytes: line = line.decode('utf-8')
                except:
                    line = str(line)

                rep_list = {}
                _line = escape(line)
                p = 0
                for txt in contents:
                    if not txt: continue
                    p += 1
                    txt = escape(txt)
                    if line.find(txt) >= 0:
                        _line = self.__replace_contents(
                            _line, txt, p, rep_list)
                    else:
                        tmp = re.search('(' + txt + ')', _line, flags=re.I)
                        if tmp:
                            _line = self.__replace_contents(
                                _line,
                                tmp.groups()[0], p, rep_list)

                for key in rep_list:
                    # public.print_log(json.dumps(rep_list))
                    result[n] = _line.replace(key, rep_list[key])
                n += 1
        except:
            pass
        return result

    #    line = line.replace("BT_SEARCH".format(p), )
    def __replace_contents(self, line, txt, p, rep_list):
        """
        @name 替换文件内容
        @param line:文件内容
        @param txt:替换内容
        @param p:替换位置
        """
        n_data = 'BT_SEARCH{}'.format(p)
        line = line.replace(txt, n_data)
        rep_list[n_data] = "<span class='{}'>{}</span>".format(
            self.__s_class[p - 1], txt)
        return line

    def __get_file_list(self, path, data, flist):
        """
        @name 获取文件列表
        @param path:文件路径
        @param ext:文件类型
        @param s_time:开始时间
        @param e_time:结束时间
        @param min_size:最小文件大小
        @param max_size:最大文件大小
        @param flist:返回文件列表
        """

        exts, s_time, e_time, min_size, max_size, names = data['ext'], data[
            's_time'], data['e_time'], data['min_size'], data[
                'max_size'], data['names']

        for name in os.listdir(path):
            sfile = os.path.join(path, name)

            if os.path.isdir(sfile):
                if not data['is_sub']: continue

                self.__get_file_list(sfile, data, flist)
            else:

                #第一步：验证文件名
                if not self.__check_filename(sfile=sfile, names=names):
                    continue

                #第二步：验证后缀
                if not self.__check_ext(sfile=sfile, exts=exts):
                    continue

                #第三步：验证时间
                if not self.__check_time(
                        sfile=sfile, s_time=s_time, e_time=e_time):
                    continue

                #第四步：验证大小
                if not self.__check_size(
                        sfile=sfile, min_size=min_size, max_size=max_size):
                    continue

                flist.append(sfile)

    def __check_filename(self, sfile, names):
        """
        @name 验证文件名
        @param sfile:文件路径
        @param names:文件名
        """
        try:
            if len(names) == 0: return True

            filename = os.path.basename(sfile)
            for name in names:
                if filename.find(name) >= 0:
                    return True
                try:
                    if re.search(name, filename):
                        return True
                except:
                    pass
        except:
            pass
        return False

    def __check_ext(self, sfile, exts):
        """
        @name 验证文件后缀
        @param sfile:文件路径
        @param exts:文件类型
        """
        try:
            if "*" in exts:
                return True

            spath, ext = os.path.splitext(sfile)
            if ext:
                if ext[1:] in exts:
                    return True
            else:
                if 'no_ext' in exts:
                    return True
        except:
            pass
        return False

    def __check_time(self, sfile, s_time, e_time):
        """
        @name 验证文件时间
        @param sfile:文件路径
        @param s_time:开始时间
        @param e_time:结束时间
        """
        try:
            st_time = int(os.stat(sfile).st_mtime)
            if st_time >= s_time and st_time <= e_time:
                return True
        except:
            pass
        return False

    def __check_size(self, sfile, min_size, max_size):
        """
        @name 验证文件大小
        @param sfile:文件路径
        @param min_size:最小文件大小
        @param max_size:最大文件大小
        """
        try:
            f_size = os.path.getsize(sfile)

            if f_size >= min_size and f_size <= max_size:
                return True
        except:
            pass
        return False
