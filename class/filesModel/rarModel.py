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
try:
    from unrar import rarfile
except:
    os.system('btpip install unrar')
    from unrar import rarfile


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
            zip_file =  rarfile.RarFile(sfile)
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
            for d in f_dirs:
                if not d: continue
                if not d in sub_data:
                    if d == f_name[-len(d):]:
                        tmps = item.date_time

                        sub_data[d] = {
                            'file_size': item.file_size,
                            'compress_size': item.compress_size,
                            'filename':d,
                            'fullpath':f_name,
                            'date_time': public.to_date(times = '{}-{}-{} {}:{}:{}'.format(tmps[0],tmps[1],tmps[2],tmps[3],tmps[4],tmps[5])),
                            'is_dir': 0
                        }
                        if item.flag_bits == 32:
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

        result = {}
        result['status'] = True
        result['data'] = ''
        with rarfile.RarFile(sfile,'r') as zip_file:
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

        return public.returnMsg(False,'RAR archive files do not support file deletion')

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
        return public.returnMsg(False,'RAR archive does not support this function!')

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

        tmp_path = '{}/tmp/{}'.format(public.get_soft_path(),public.md5(public.GetRandomString(32)))
        if not os.path.exists(tmp_path):
            os.makedirs(tmp_path,384)

        with rarfile.RarFile(sfile) as zip_file:
            try:
                m_list = {}

                f_infos = zip_file.infolist()
                f_infos = sorted(f_infos,key=lambda x:x.filename)
                for item in f_infos:
                    filename = self.__get_zip_filename(item)

                    if filename in filenames:
                        spath = os.path.join(tmp_path,filename).strip('/')
                        if item.flag_bits == 32:
                            m_list[spath] = []
                        else:
                            if not 'other' in m_list:
                                m_list['other'] = []

                            dir_key = os.path.dirname(spath)
                            info = {'src':spath,'dst':'{}/{}'.format(extract_path,os.path.basename(spath))}
                            if dir_key in m_list:
                                info['dst'] = '{}/{}'.format(extract_path,'/'.join(filename.split('/')[1:]))
                                s_path = os.path.dirname(info['dst'])
                                if not os.path.exists(s_path): os.makedirs(s_path,384)

                                m_list[dir_key].append(info)
                            else:
                                m_list['other'].append(info)
                        zip_file.extract(filename.strip('/').replace('/','\\'),tmp_path)
                for key in m_list:
                    try:
                        # if key != 'other':
                        #     dir_name = '{}/{}'.format(extract_path,os.path.basename(key))
                        #     if not os.path.exists(dir_name): os.makedirs(dir_name,384)

                        for info in m_list[key]:
                            shutil.copyfile(info['src'],info['dst'])
                    except:pass

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
        return public.returnMsg(False,'RAR archive does not support this function!')



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
        if item.flag_bits == 32:
            filename  += '/'

        return filename.replace('\\','/')






