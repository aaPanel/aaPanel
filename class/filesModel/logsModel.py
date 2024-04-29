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
import os,sys,re
from filesModel.base import filesBase
import public,files,json,time

from BTPanel import cache

class main(filesBase):


    __objs = ['bos']
    def __init__(self):
        pass


    def get_logs_info(self,get):
        """
        @查看日志
        @param get
            limit:每页显示条数
            file:日志文件
        """
        p = 1
        limit = 200
        search = None
        file = get.file
        if 'limit' in get: limit = int(get.limit)
        if 'p' in get: limit = int(get.p)
        if 'search' in get: search = get.search

        if not os.path.exists(file):
            return public.returnMsg(False,'Please specify file!')

        res = {}
        res['status'] = True
        res['data'] = self.GetNumLines(file,limit,p,search)

        res['md5'] = public.md5(res['data'])
        res['limit'] = limit

        if not cache.get(file+'_logs_info'):
            public.set_module_logs('files_get_logs_info','get_logs_info')
            cache.set(file+'_logs_info','1',86400)
        return res


    def set_log_split(self,get):
        """
        @name 文件切割
        @param filename 文件路径
        @param stype 切割类型  day:按天切割 size:按大小切割
        @param size 切割大小（stype=size必传）
        """
        filename = get.filename
        stype = get.stype
        limit = int(get.limit)
        if not stype in ['day','size']:
            return public.returnMsg(False,'Cut type passing error.')

        if not os.path.exists(filename):
            return public.returnMsg(False,'FILE_NOT_EXISTS')

        if limit < 3:
            return public.returnMsg(False,'The number of reserved copies cannot be less than 3.')

        data = {'type':stype,'limit':limit,'addtime':int(time.time())}
        if stype == 'size':
            size = int(get.size)
            if size < 1024:
                return public.returnMsg(False,'Cut size cannot be empty.')
            data['size'] = size

        public.set_split_logs(filename,1,data)

        return public.returnMsg(True,'successfully set.')


    def get_log_split(self,get):
        """
        @name 获取文件切割信息
        @param filename 文件路径
        """
        data = {}
        sfile = '{}/data/cutting_log.json'.format(public.get_panel_path())
        if os.path.exists(sfile):
            try:
                data = json.loads(public.readFile(sfile))
            except:pass

        return data


    def get_file_ext(self,filename):
        """
        @name 获取文件扩展名
        @param filename
        """
        ss_exts = ['.tar.gz','.tar.bz2','.tar.bz']
        for s in ss_exts:
            e_len = len(s)
            f_len = len(filename)
            if f_len < e_len: continue
            if filename[-e_len:] == s:
                return filename[:-e_len] ,s
        if filename.find('.') == -1: return filename,''
        return os.path.splitext(filename)

    def copy_file_to(self, get):
        """
        @name 创建文件副本
        @param get
        @return
        """

        sfile = get.sfile
        if not os.path.exists(sfile):
            return public.returnMsg(False, 'FILE_NOT_EXISTS')

        spath,ext = sfile,''
        if os.path.isfile(get.sfile):
            spath,ext = self.get_file_ext(sfile)

        # public.print_log(spath)
        for x in range(1,1000):
            dfile = '{} - copy ({}){}'.format(spath,x,ext)
            if not os.path.exists(dfile):
                break

        get.dfile = dfile
        f_obj = files.files()
        if os.path.isdir(get.sfile):
            public.WriteLog("File manager","Create copy of the directory [{}]".format(sfile))
            return f_obj.CopyDir(get)

        import shutil
        try:
            shutil.copyfile(get.sfile, get.dfile)
            public.WriteLog('TYPE_FILE', 'FILE_COPY_SUCCESS',
                            (get.sfile, get.dfile))
            try:
                stat = os.stat(get.sfile)
                os.chmod(get.dfile,stat.st_mode)
                os.chown(get.dfile, stat.st_uid, stat.st_gid)
            except:pass
            public.WriteLog("File manager","Create copy of the file[{}]".format(sfile))
            return public.returnMsg(True, 'FILE_COPY_SUCCESS')
        except:
            return public.returnMsg(False, 'FILE_COPY_ERR')


    def set_topping_status(self,get):
        """
        @name 设置文件或目录置顶
        @param get
            file:文件路径
            type:置顶类型
        """
        sfile = get.sfile
        status = int(get.status)
        if not os.path.exists(sfile):
            import html
            sfile = html.unescape(sfile)
            if not os.path.exists(sfile):
                return public.returnMsg(False, 'File or directory does not exist.')


        data = {}
        conf_file = '{}/data/toping.json'.format(public.get_panel_path())
        try :
            if os.path.exists(conf_file):
                data = json.loads(public.readFile(conf_file))
        except:pass

        if sfile in data: del data[sfile]

        if status:
            data[sfile] = status
        public.writeFile(conf_file, json.dumps(data))
        public.set_module_logs('files_set_topping_status','set_topping_status')
        public.WriteLog("File manager","Modify [{}] top status".format(sfile))
        return public.returnMsg(True, 'Successful set.')


    def GetNumLines(self,path, num, p=1,search = None):
        """
        @name 取文件指定尾行数
        @param path 文件路径
        @param num 取尾行数
        @param p 当前页
        @param search 搜索关键字
        @return list
        """
        pyVersion = sys.version_info[0]
        max_len = 1024 * 128
        try:
            from html import escape
            if not os.path.exists(path): return ""
            start_line = (p - 1) * num
            count = start_line + num
            fp = open(path, 'rb')

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

                            is_res = True
                            if search:
                                is_res = False
                                if line.find(search) >= 0 or re.search(search,line):
                                    is_res = True

                            if is_res:
                                line_len = len(line)
                                total_len += line_len
                                sp_len = total_len - max_len
                                if sp_len > 0:
                                    line = line[sp_len:]
                                try:
                                    data.insert(0, escape(line))
                                except:
                                    pass
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
                            try:
                                if type(t_buf) == bytes: t_buf = t_buf.decode('utf-8',errors='ignore')
                            except:
                                try:
                                    if type(t_buf) == bytes: t_buf = t_buf.decode('gbk',errors='ignore')
                                except:
                                    t_buf = str(t_buf)
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
            result = ''
            if len(result) > max_len:
                result = result[-max_len:]

        try:
            try:
                result = json.dumps(result)
                return json.loads(result).strip()
            except:
                if pyVersion == 2:
                    result = result.decode('utf8', errors='ignore')
                else:
                    result = result.encode('utf-8', errors='ignore').decode("utf-8", errors="ignore")
            return result.strip()
        except:
            return ""