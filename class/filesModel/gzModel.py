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
import public,json
import tarfile,shutil,gzip

class main(filesBase):

    def __init__(self):
        pass


    def __check_zipfile(self,sfile,is_close = False):
        '''
        @name 检查文件是否为zip文件
        @param sfile 文件路径
        @return bool
        '''

        pass

    def get_zip_files(self,args):
        '''
        @name 获取压缩包内文件列表
        @param args['path'] 压缩包路径
        @return list
        '''
        sfile = args.sfile
        if not os.path.exists(sfile):
            return public.returnMsg(False,'FILE_NOT_EXISTS')

        if not tarfile.is_tarfile(sfile):
            return public.returnMsg(False,'Not a valid tar.gz archive file')

        zip_file = tarfile.open(sfile)
        data = {}
        for item in zip_file.getmembers():

            sub_data = data
            f_name = self.__get_zip_filename(item)

            f_dirs = f_name.split('/')
            for d in f_dirs:
                if not d: continue
                if not d in sub_data:
                    if d == f_name[-len(d):]:

                        sub_data[d] = {
                            'file_size': item.size,
                            'filename':d,
                            'fullpath':f_name,
                            'date_time': public.format_date(times=item.mtime),
                            'is_dir': 0
                        }
                        if item.isdir():
                            sub_data[d]['is_dir'] = 1
                    else:
                        sub_data[d] = {}
                sub_data = sub_data[d]

        return data


    def get_fileinfo_by(self,args):
        '''
        @name 获取压缩包内文件信息
        @param args['path'] 压缩包路径
        @param args['filename'] 文件名
        @return dict
        '''

        sfile = args.sfile
        filename = args.filename
        if not os.path.exists(sfile):
            return public.returnMsg(False,'FILE_NOT_EXISTS')

        tmp_path = '{}/tmp/{}'.format(public.get_panel_path(),public.md5(sfile + filename))
        result = {}
        result['status'] = True
        result['data'] = ''
        with tarfile.open(sfile,'r') as zip_file:
            try:
                zip_file.extract(filename,tmp_path)
                result['data'] = public.readFile('{}/{}'.format(tmp_path,filename))
            except:pass
        try:
            public.rmdir(tmp_path)
        except:pass
        return result

    def delete_zip_file(self,args):
        '''
        @name 删除压缩包内文件
        @param args['path'] 压缩包路径
        @param args['filenames'] 文件名列表，数组格式
        @return dict
        '''
        sfile = args.sfile
        filenames = args.filenames

        if not tarfile.is_tarfile(sfile):
            return public.returnMsg(False,'Not a valid tar.gz archive file')

        tmp_path = self.__unzip_tmp_path(sfile)
        if not tmp_path: return public.returnMsg(False,'Failed edit!')

        #组装原有的文件
        s_list = []
        src_list = {}
        public.get_file_list(tmp_path,s_list)
        for f in s_list:
            if not os.path.isfile(f): continue
            src_file = f.replace(tmp_path,'').strip('/')
            if src_file in filenames:
                continue
            src_list[src_file] = f

        with tarfile.open(sfile,'w') as new_zfile:
            try:
                for src_file in src_list:
                    new_zfile.add(src_list[src_file],src_file)
            except:
                shutil.rmtree(tmp_path, True)
                return public.returnMsg(False,'Failed delete file,error:' + public.get_error_info())

        shutil.rmtree(tmp_path, True)
        return public.returnMsg(True,'Compressed package file modified successfully')


    def write_zip_file(self,args):
        '''
        @name 写入压缩包内文件
        @param args['path'] 压缩包路径
        @param args['filename'] 文件名
        @param args['data'] 写入数据
        @return dict
        '''

        sfile = args.sfile
        filename = args.filename
        data = args.data

        if not os.path.exists(sfile):
            return public.returnMsg(False,'FILE_NOT_EXISTS')

        tmp_path = self.__unzip_tmp_path(sfile)
        if not tmp_path: return public.returnMsg(False,'Failed edit!')
        public.writeFile('{}/{}'.format(tmp_path,filename),data)

        #组装原有的文件
        s_list = []
        src_list = {}
        public.get_file_list(tmp_path,s_list)
        for f in s_list:
            if os.path.isdir(f):
                continue
            src_file = f.replace(tmp_path,'').strip('/')
            if src_file in src_list:
                continue
            src_list[src_file] = f

        with tarfile.open(sfile,'w') as new_zfile:
            try:
                for src_file in src_list:
                    new_zfile.add(src_list[src_file],src_file)
            except:
                shutil.rmtree(tmp_path, True)
                return public.returnMsg(False,'Failed modify file,error:' + public.get_error_info())

        shutil.rmtree(tmp_path, True)
        return public.returnMsg(True,'Compressed package file modified successfully')



    def extract_byfiles(self,args):
        """
        @name 解压部分文件
        @param args['path'] 压缩包路径
        @param args['extract_path'] 解压路径
        @param args['filenames'] 文件名列表，数组格式
        """
        sfile = args.sfile
        filenames = args.filenames
        extract_path = args.extract_path
        if not os.path.exists(sfile):
            return public.returnMsg(False,'FILE_NOT_EXISTS')

        if not os.path.exists(extract_path):
            os.makedirs(extract_path,384)

        tmp_path = '{}/tmp/{}'.format(public.get_panel_path(),public.md5(public.GetRandomString(32)))
        if not os.path.exists(tmp_path):
            os.makedirs(tmp_path,384)

        with tarfile.open(sfile) as zip_file:
            try:
                m_list = {}

                f_infos = zip_file.getmembers()
                for item in f_infos:
                    filename = self.__get_zip_filename(item)

                    if filename in filenames:
                        spath = os.path.join(tmp_path,filename).strip('/')
                        if item.isdir():
                            m_list[spath] = []
                        else:
                            if not 'other' in m_list:
                                m_list['other'] = []

                            dir_key = os.path.dirname(spath)
                            info = {'src':spath,'dst':'{}/{}'.format(extract_path, filename.strip('/'))}
                            if dir_key in m_list:
                                info['dst'] = '{}/{}'.format(extract_path,'/'.join(filename.split('/')[1:]))
                                s_path = os.path.dirname(info['dst'])
                                if not os.path.exists(s_path): os.makedirs(s_path,384)

                                m_list[dir_key].append(info)
                            else:
                                m_list['other'].append(info)

                            s_path = os.path.dirname(info['dst'])
                            if not os.path.exists(s_path): os.makedirs(s_path, 384)
                        zip_file.extract(filename.strip('/'),tmp_path)

                for key in m_list:
                    try:
                        for info in m_list[key]:
                            if os.getenv('BT_PANEL'):
                                shutil.copyfile(info['src'],info['dst'])
                            else:
                                shutil.copyfile('/' + info['src'],'/' + info['dst'])
                    except:
                        pass
                shutil.rmtree(tmp_path, True)
            except:
                return public.returnMsg(False,'Decompression failed,error:' + public.get_error_info())
        return public.returnMsg(True,'File was decompressed successfully')

    def __unzip_tmp_path(self,sfile):
        '''
        @name 获取临时解压路径
        @param sfile 压缩包路径
        @return str
        '''
        tmp_path = '{}/tmp/{}'.format(public.get_soft_path(),public.md5(public.GetRandomString(32)))
        with tarfile.open(sfile) as zip_file:
            try:
                zip_file.extractall(tmp_path)
            except: return False

        return tmp_path


    def add_zip_file(self,args):
        '''
        @name 添加文件到压缩包
        @param args['r_path'] 跟路径
        @param args['filename'] 文件名
        @param args['f_list'] 写入数据
        @return dict
        '''

        sfile = args.sfile
        r_path = args.r_path
        f_list = args.f_list
        if not os.path.exists(sfile):
            return public.returnMsg(False,'FILE_NOT_EXISTS')

        tmp_path = self.__unzip_tmp_path(sfile)
        if not tmp_path: return public.returnMsg(False,'Failed edit!')

        #组装新添加的文件
        src_list = {}
        for fname in f_list:
            if os.path.isdir(fname):
                s_list = []
                public.get_file_list(fname,s_list)

                for f in s_list:
                    if os.path.isdir(f):
                        continue
                    src_file = '{}/{}{}'.format(r_path,os.path.basename(fname),f.replace(fname,'')).replace('//','/')
                    src_list[src_file] = f
            else:
                src_file = '{}/{}'.format(r_path, os.path.basename(fname)).replace('//','/')
                src_list[src_file] = fname

        #组装原有的文件
        s_list = []
        public.get_file_list(tmp_path,s_list)
        for f in s_list:
            if os.path.isdir(f):
                continue
            src_file = f.replace(tmp_path,'').strip('/')
            if src_file in src_list:
                continue
            src_list[src_file] = f

        with tarfile.open(sfile,'w') as new_zfile:
            try:
                for src_file in src_list:
                    new_zfile.add(src_list[src_file],src_file)
            except:
                shutil.rmtree(tmp_path, True)
                return public.returnMsg(False,'Failed add file,error:' + public.get_error_info())

        shutil.rmtree(tmp_path, True)
        return public.returnMsg(True,'Compressed package file modified successfully')



    def __get_zip_filename(self,item):
        '''
        @name 获取压缩包文件名
        @param item 压缩包文件对象
        @return string
        '''
        filename = item.name
        try:
            filename = item.name.encode('cp437').decode('gbk')
        except:pass
        if item.isdir():
            filename += '/'
        return filename






