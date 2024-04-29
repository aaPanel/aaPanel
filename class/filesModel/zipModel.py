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
import zipfile,shutil
from pathlib import Path
class main(filesBase):

    def __init__(self):
        pass


    def __check_zipfile(self,sfile,is_close = False):
        '''
        @name 检查文件是否为zip文件
        @param sfile 文件路径
        @return bool
        '''

        zip_file = None
        try:
            zip_file = zipfile.ZipFile(sfile)
        except:pass

        if is_close and zip_file:
            zip_file.close()

        return zip_file

    def get_zip_files(self,args):
        '''
        @name 获取压缩包内文件列表
        @param args['path'] 压缩包路径
        @return list
        '''
        sfile = args.sfile
        if not os.path.exists(sfile):
            return public.returnMsg(False,'FILE_NOT_EXISTS')

        zip_file = self.__check_zipfile(sfile)
        if not zip_file:
            return public.returnMsg(False,'NOT_ZIP_FILE')

        data = {}
        for item in zip_file.infolist():
            sub_data = data
            f_name = self.__get_zip_filename(item)

            f_dirs = f_name.split('/')

            d_idx = 0
            for d in f_dirs:
                if not d: continue
                if not d in sub_data:
                    if d == f_name[-len(d):] and d_idx == len(f_dirs) - 1:
                        tmps = item.date_time
                        sub_data[d] = {
                            'file_size': item.file_size,
                            'compress_size': item.compress_size,
                            'compress_type': item.compress_type,
                            'filename':d,
                            'fullpath':f_name,
                            'date_time': public.to_date(times = '{}-{}-{} {}:{}:{}'.format(tmps[0],tmps[1],tmps[2],tmps[3],tmps[4],tmps[5])),
                            'is_dir': 0
                        }
                        if item.is_dir():
                            sub_data[d]['is_dir'] = 1
                    else:
                        sub_data[d] = {}
                d_idx += 1
                sub_data = sub_data[d]

        zip_file.close()
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

        result = {}
        result['status'] = True
        result['data'] = ''
        with zipfile.ZipFile(sfile,'r') as zip_file:
            for item in zip_file.infolist():
                z_filename = self.__get_zip_filename(item)
                if z_filename == filename:

                    buff = zip_file.read(item.filename)
                    encoding,srcBody = public.decode_data(buff)
                    result['encoding'] = encoding
                    result['data'] = srcBody
                    break
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
        if not os.path.exists(sfile):
            return public.returnMsg(False,'FILE_NOT_EXISTS')

        with zipfile.ZipFile(sfile,'r') as zip_file:
            with zipfile.ZipFile(sfile + '.tmp','w',zipfile.ZIP_DEFLATED) as new_zfile:
                for item in zip_file.infolist():
                    filename = self.__get_zip_filename(item)

                    if filename in filenames:
                        continue
                    src_name = item.filename
                    item.filename = filename
                    new_zfile.writestr(item,zip_file.read(src_name))
        shutil.move(sfile + '.tmp',sfile)
        return public.returnMsg(True,'File deleted successfully')

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

        with zipfile.ZipFile(sfile,'r') as zip_file:
            with zipfile.ZipFile(sfile + '.tmp','w',zipfile.ZIP_DEFLATED) as new_zfile:
                for item in zip_file.infolist():
                    z_filename = self.__get_zip_filename(item)
                    if z_filename == filename:
                        continue

                    new_zfile.writestr(item,zip_file.read(item.filename))
                new_zfile.writestr(filename, data=data, compress_type=zipfile.ZIP_DEFLATED)

        shutil.move(sfile + '.tmp',sfile)
        return public.returnMsg(True,'File written successfully')


    def extract_byfiles(self,args):
        """
        @name 解压部分文件
        @param args['path'] 压缩包路径
        @param args['extract_path'] 解压路径
        @param args['filenames'] 文件名列表，数组格式
        """

        zip_path = ''
        if 'zip_path' in args: zip_path = args.zip_path
        sfile = args.sfile
        filenames = args.filenames
        extract_path = args.extract_path
        if not os.path.exists(sfile):
            return public.returnMsg(False,'FILE_NOT_EXISTS')

        if not os.path.exists(extract_path):
            os.makedirs(extract_path,384)

        tmp_path = '{}/tmp/{}'.format(public.get_soft_path(),public.md5(public.GetRandomString(32)))
        if not os.path.exists(tmp_path):
            os.makedirs(tmp_path,384)

        with zipfile.ZipFile(sfile) as zip_file:
            try:
                m_list = {}
                for item in zip_file.infolist():
                    filename = self.__get_zip_filename(item)

                    if filename in filenames:
                        spath = os.path.join(tmp_path,filename).strip('/')
                        if item.is_dir():
                            m_list[spath] = []
                        else:
                            if not 'other' in m_list:
                                m_list['other'] = []

                            dir_key = os.path.dirname(spath)
                            info = {'src':spath,'dst':'{}/{}'.format(extract_path,filename.strip('/'))}
                            if zip_path:
                                info['dst'] = '{}/{}'.format(extract_path,filename.replace(zip_path,'').strip('/'))

                            s_path = os.path.dirname(info['dst'])
                            if not os.path.exists(s_path): os.makedirs(s_path,384)

                            if dir_key in m_list:
                                m_list[dir_key].append(info)
                            else:
                                m_list['other'].append(info)

                        item.filename = filename
                        zip_file.extract(item,tmp_path)

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
        return public.returnMsg(True,'The file was decompressed successfully')

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

        #追加原路径
        src_list = {}
        for fname in f_list:
            if os.path.isdir(fname):
                s_list = []
                public.get_file_list(fname,s_list)

                for f in s_list:
                    if os.path.isdir(f):
                        continue
                    src_file = '{}/{}{}'.format(r_path,os.path.basename(fname),f.replace(fname,''))
                    src_list[src_file] = f
            else:
                src_file = r_path + '/' + os.path.basename(fname)
                src_list[src_file] = fname

        tmp_path = sfile + '.tmp'
        if os.path.exists(tmp_path):
            os.remove(tmp_path)

        with zipfile.ZipFile(sfile,'r') as zip_file:
            with zipfile.ZipFile(tmp_path,'w',zipfile.ZIP_DEFLATED) as new_zfile:
                try:
                    #过滤旧文件
                    for item in zip_file.namelist():
                        if item in src_list:
                            continue
                        new_zfile.writestr(item,zip_file.read(item))

                    #追加新文件
                    for src_file in src_list:
                        new_zfile.write(src_list[src_file],src_file)
                except:
                    return public.returnMsg(False,'Failed add file,error:' + public.get_error_info())

        shutil.move(tmp_path,sfile)
        return public.returnMsg(True,'Compressed package file modified successfully')


    # def __get_zip_filename(self,item):
    #     '''
    #     @name 获取压缩包文件名
    #     @param item 压缩包文件对象
    #     @return string
    #     '''
    #     path = item.filename
    #     try:
    #         path_name = path.decode('utf-8')
    #     except:
    #         path_name = path.encode('cp437').decode('gbk')
    #         path_name = path_name.encode('utf-8').decode('utf-8')
    #     return path_name




    def __get_zip_filename(self,item):
        '''
        @name 获取压缩包文件名
        @param item 压缩包文件对象
        @return string
        '''


        filename = item.filename
        try:
            filename = item.filename.encode('cp437').decode('gbk')
        except:pass
        return filename






