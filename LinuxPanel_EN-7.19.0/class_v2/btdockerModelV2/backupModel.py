# coding: utf-8
# -------------------------------------------------------------------
# aaPanel
# -------------------------------------------------------------------
# Copyright (c) 2015-2099 aaPanel(www.aapanel.com) All rights reserved.
# -------------------------------------------------------------------
# Author: wzz <wzz@aapanel.com>
# -------------------------------------------------------------------
import os
import time
import traceback
import gettext
_ = gettext.gettext

# ------------------------------
# Docker模型
# ------------------------------
import public
from btdockerModelV2 import containerModel as dc
from btdockerModelV2 import dk_public as dp
from btdockerModelV2.dockerBase import dockerBase
from public.validate import Param

class main(dockerBase):

    # 2023/12/22 上午 9:56 备份指定容器的mount volume
    def backup_volume(self, get):
        '''
            @name 备份指定容器的mount volume
            @author wzz <2023/12/22 上午 11:19>
            @param "data":{"container_id":"容器ID"}
            @return dict{"status":True/False,"msg":"提示信息"}
        '''

        # 校验参数
        try:
            get.validate([
                Param('container_id').Require().String(),
            ], [
                public.validate.trim_filter(),
            ])
        except Exception as ex:
            public.print_log("error info: {}".format(ex))
            return public.return_message(-1, 0, str(ex))

        try:
            client = dp.docker_client()
            container = client.containers.get(get.container_id)
            volume_list = container.attrs["Mounts"]
            volume_list = [v["Source"] for v in volume_list]

            if not volume_list:
                return public.return_message(-1, 0,
                                             public.lang("There is no volume to back up"))

            backup_path = "/www/backup/btdocker/volumes/{}".format(container.name)
            if not os.path.exists(backup_path):
                os.makedirs(backup_path, 0o755)

            import subprocess
            public.ExecShell("echo -n > {}".format(self._backup_log))

            for v in volume_list:
                backup_name = os.path.basename(v)
                # 2023/12/22 上午 10:34 每个压缩包命名都用v的目录名，如果是文件则用文件名
                tar_name = "{}_{}_{}.tar.gz".format(
                    container.name,
                    backup_name,
                    time.strftime("%Y%m%d_%H%M%S", time.localtime())
                )
                backup_file = os.path.join(backup_path, tar_name)
                source_path = os.path.dirname(v)
                cmd = "cd {} && tar zcvf {} {}".format(source_path, backup_file, backup_name)
                cmd = ("nohup echo 'To start backing up {} of container {}, it may take more than 1-5 minutes...' >> {};"
                       "{} >> {} 2>&1 &&"
                       "echo 'bt_successful' >> {} || echo 'bt_failed' >> {} &"
                .format(
                    container.name,
                    tar_name,
                    self._backup_log,
                    cmd,
                    self._backup_log,
                    self._backup_log,
                    self._backup_log,
                ))
                subprocess.Popen(cmd, shell=True)

                # 2023/12/22 下午 12:17 添加到数据库
                dp.sql('dk_backup').add(
                    'type,name,container_id,container_name,filename,size,addtime',
                    (3, tar_name, container.id, container.name, backup_file, 0, time.strftime(
                        "%Y-%m-%d %H:%M:%S", time.localtime()
                    ))
                )
                public.WriteLog("Docker module", "The {} of the backup container {} succeeds！".format(container.name, tar_name))

            return public.return_message(0, 0, public.lang("The backup task was created successfully."))
        except Exception as e:
            print(traceback.format_exc())
            return public.return_message(-1, 0, public.lang("Failed to create a backup task {}", str(e)))

    # 2023/12/22 上午 11:23 获取指定容器的备份列表
    def get_backup_list(self, get):
        '''
            @name 获取指定容器的备份列表
            @param "data":{"container_id":"容器ID"}
            @return list[dict{"":""}]
        '''
        # 校验参数
        try:
            get.validate([
                Param('container_id').Require().String(),
            ], [
                public.validate.trim_filter(),
            ])
        except Exception as ex:
            public.print_log("error info: {}".format(ex))
            return public.return_message(-1, 0, str(ex))

        try:
            # 2023/12/22 下午 12:24 从数据库中获取已备份的指定容器
            backup_list = dp.sql('dk_backup').where('container_id=?', (get.container_id,)).field(
                'name,container_id,container_name,filename,size,addtime'
            ).select()

            for l in backup_list:
                if not os.path.exists(l['filename']):
                    l['size'] = 0
                    l['ps'] = 'file does not exist'
                    continue

                l['size'] = os.path.getsize(l['filename'])
                l['ps'] = 'local backup'

            return public.return_message(0, 0,  backup_list)

        except Exception as e:
            print(traceback.format_exc())
            return public.return_message(0, 0, [])

    # 2023/12/22 下午 2:25 删除指定容器的备份
    def remove_backup(self, get):
        '''
            @name 删除指定容器的备份
            @param "data":{"container_id":"容器ID","container_name":"容器名","name":"文件名"}
            @return dict{"status":True/False,"msg":"提示信息"}
        '''

        # 校验参数
        try:
            get.validate([
                Param('container_id').Require().String(),
                Param('container_name').Require().String(),
                Param('name').Require().String(),
            ], [
                public.validate.trim_filter(),
            ])
        except Exception as ex:
            public.print_log("error info: {}".format(ex))
            return public.return_message(-1, 0, str(ex))


        try:
            # 2023/12/22 下午 2:26 从数据库中删除指定容器的备份
            dp.sql('dk_backup').where('container_id=? and name=?', (get.container_id, get.name)).delete()

            # 2023/12/22 下午 2:27 删除本地备份文件
            backup_path = "/www/backup/btdocker/volumes/{}".format(get.container_name)
            file_path = os.path.join(backup_path, get.name)
            if not os.path.exists(file_path):
                return public.return_message(0, 0, public.lang("successfully delete"))
            os.remove(file_path)
            return public.return_message(0, 0, public.lang("successfully delete"))
        except Exception as e:
            print(traceback.format_exc())
            return public.return_message(-1, 0, public.lang("Failed to delete the file, reason: {}", get.name, str(e)))

    def get_pull_log(self, get):
        """
        获取镜像拉取日志，websocket
        @param get:
        @return:
        """
        get.wsLogTitle = "Start container directory backup, please wait..."
        get._log_path = self._backup_log
        return self.get_ws_log(get)