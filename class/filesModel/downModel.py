#coding: utf-8
#-------------------------------------------------------------------
# 宝塔Linux面板
#-------------------------------------------------------------------
# Copyright (c) 2015-2099 宝塔软件(http://bt.cn) All rights reserved.
#-------------------------------------------------------------------
# Author: cjxin <cjxin@bt.cn>
#-------------------------------------------------------------------

# 上传文件至oss
#------------------------------
from filesModel.base import filesBase
import public

class main(filesBase):


    def __init__(self):
        pass


    def get_oss_objects(self,get):
        """
        @name 获取可上传的对象存储
        """
        return self.get_all_objects(get)


    def download_file(self,get):
        """
        @name 下载文件
        @param get
            file:文件路径
        """

        info = self.get_soft_find(get.name)
        if not info['setup']:
            return public.returnMsg(False,'未安装[{}]插件'.format(info['title']))

        import panelTask
        task_obj = panelTask.bt_task()
        task_obj.create_task('下载文件', 1, get.url, get.path + '/' + get.filename)
        public.set_module_logs('files_down_to_file', 'download_file', 1)
        public.WriteLog('TYPE_FILE', '从 [{}] 下载文件 [{}] 到 {}'.format(info['title'],get.filename,get.path))
        return public.returnMsg(True, 'FILE_DOANLOAD')

