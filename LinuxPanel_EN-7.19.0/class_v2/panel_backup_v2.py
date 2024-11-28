# coding: utf-8
# -------------------------------------------------------------------
# aaPanel
# -------------------------------------------------------------------
# Copyright (c) 2015-2099 aaPanel(www.aapanel.com) All rights reserved.
# -------------------------------------------------------------------
# Author: hwliang <hwl@aapanel.com>
# -------------------------------------------------------------------

# ------------------------------
# 数据备份模块
# ------------------------------
import os
import sys
import json
import re
import time
from typing import Tuple, Union

os.chdir('/www/server/panel')
if not 'class/' in sys.path:
    sys.path.insert(0, 'class/')
if not 'class_v2/' in sys.path:
    sys.path.insert(0, 'class_v2/')
import public

# from files import files

_VERSION = 1.5


class backup:
    _BACKUP_DIR = public.M('config').where("id=?", (1,)).getField('backup_path')
    _exclude = ""
    _err_log = '/tmp/backup_err.log'
    _inode_min = 10
    _db_mysql = None
    _cloud = None
    _is_save_local = os.path.exists('data/is_save_local_backup.pl')
    _error_msg = ""
    _backup_all = False

    # 数据库备份
    _DB_BACKUP_DIR: str = os.path.join(_BACKUP_DIR, "database")
    # mysql 备份
    _MYSQL_BACKUP_DIR = os.path.join(_DB_BACKUP_DIR, "mysql", "crontab_backup")
    _MYSQLDUMP_BIN = public.get_mysqldump_bin()
    # mongodb 备份
    _MONGODB_BACKUP_DIR = os.path.join(_DB_BACKUP_DIR, "mongodb", "crontab_backup")
    _MONGODBDUMP_BIN = os.path.join(public.get_setup_path(), "mongodb/bin/mongodump")
    _MONGOEXPORT_BIN = os.path.join(public.get_setup_path(), "mongodb/bin/mongoexport")
    # redis 备份
    _REDIS_BACKUP_DIR = os.path.join(_DB_BACKUP_DIR, "redis", "crontab_backup")
    # pgsql 备份
    _PGSQL_BACKUP_DIR = os.path.join(_DB_BACKUP_DIR, "pgsql", "crontab_backup")
    _PGDUMP_BIN = os.path.join(public.get_setup_path(), "pgsql/bin/pg_dump")

    _SPLIT_SIZE = 5 * 1024 * 1024 * 1024  # 拆分文件大小

    _CLOUD_OBJ = {
        "qiniu": "Qiniu Cloud Storage",
        "alioss": "Alibaba Cloud OSS",
        "ftp": "FTP Storage",
        "bos": "Baidu Cloud BOS",
        "obs": "Huawei Cloud OBS",
        "aws_s3": "AWS S3",
        "gdrive": "Google Drive",
        "msonedrive": "Microsoft OneDrive",
        "gcloud_storage": "Google Cloud Storage",
        "upyun": "Upyun Storage",
        "jdcloud": "JD Cloud Storage",
        "txcos": "Tencent Cloud COS",
        'tianyiyun': "Tianyi Cloud ZOS",
        'webdav':"WebDav",
        'minio':"MinIO Storage",
        'dogecloud':"Duoji Cloud COS",
        'localhost':'Local Disk'
        }

    def __init__(self, cloud_object=None, cron_info={}):
        '''
            @name 数据备份对象
            @param cloud_object 远程上传对象，需具备以下几个属性和方法：
                    _title = '中文名称,如：阿里云OSS'
                    _name = '英文名称,如：alioss'

                    upload_file(filename,data_type = None)
                        文件名 , 数据类型 site/database/path

                    delete_file(filename,data_type = None)
                        文件名 , 数据类型 site/database/path

                    给_error_msg赋值，传递错误消息:
                    _error_msg = "错误消息"
        '''
        if not os.path.exists(self._BACKUP_DIR):
            os.makedirs(self._BACKUP_DIR)
        if not os.path.exists(self._MYSQL_BACKUP_DIR):
            os.makedirs(self._MYSQL_BACKUP_DIR)
        if not os.path.exists(self._MONGODB_BACKUP_DIR):
            os.makedirs(self._MONGODB_BACKUP_DIR)
        if not os.path.exists(self._REDIS_BACKUP_DIR):
            os.makedirs(self._REDIS_BACKUP_DIR)
        if not os.path.exists(self._PGSQL_BACKUP_DIR):
            os.makedirs(self._PGSQL_BACKUP_DIR)

        self._cloud_new = None
        self._cloud = cloud_object
        self.cron_info = None
        self.echo_id = cron_info.get('echo')
        if cron_info and 'echo' in cron_info.keys():
            self.cron_info = self.get_cron_info(cron_info["echo"])
        if not os.path.exists(self._BACKUP_DIR):
            os.makedirs(self._BACKUP_DIR)
        if not public.M('sqlite_master').db('backup').where('type=? AND name=? AND sql LIKE ?',
                                               ('table', 'backup', '%cron_id%')).count():
            public.M('backup').execute("ALTER TABLE 'backup' ADD 'cron_id' INTEGER DEFAULT 0", ())
        
        self.check_databases()
        
    def echo_start(self):
        print("=" * 90)
        print(public.lang("★start backup[{}]",str(public.format_date())))
        print("=" * 90)

    def echo_end(self):
        print("=" * 90)
        print(public.lang("☆backup is complete[{}]",str(public.format_date())))
        print("=" * 90)
        print("\n")

    def echo_info(self, msg):
        print("|-{}".format(public.lang(msg)))

    def echo_error(self, msg):
        print("=" * 90)
        print(public.lang("|-Error：{}",str(msg)))
        if self._error_msg:
            self._error_msg += "\n"
        self._error_msg += msg

    # 取排除列表用于计算排除目录大小
    def get_exclude_list(self, exclude=[]):
        if not exclude:
            tmp_exclude = os.getenv('BT_EXCLUDE')
            if tmp_exclude:
                exclude = tmp_exclude.split(',')
        if not exclude: return []
        return exclude

    # 构造排除
    def get_exclude(self, exclude=[]):
        self._exclude = ""
        if not exclude:
            tmp_exclude = os.getenv('BT_EXCLUDE')
            if tmp_exclude:
                exclude = tmp_exclude.split(',')
        if not exclude: return ""
        for ex in exclude:
            if ex[-1] == '/': ex = ex[:-1]
            self._exclude += " --exclude='" + ex + "'"
        self._exclude += " "
        return self._exclude

    def GetDiskInfo2(self):
        # 取磁盘分区信息
        temp = public.ExecShell("df -T -P|grep '/'|grep -v tmpfs|grep -v 'snap/core'|grep -v udev")[0]
        tempInodes = public.ExecShell("df -i -P|grep '/'|grep -v tmpfs|grep -v 'snap/core'|grep -v udev")[0]
        temp1 = temp.split('\n')
        tempInodes1 = tempInodes.split('\n')
        diskInfo = []
        n = 0
        cuts = []
        for tmp in temp1:
            n += 1
            try:
                inodes = tempInodes1[n - 1].split()
                disk = re.findall(r"^(.+)\s+([\w\.]+)\s+([\w\.]+)\s+([\w\.]+)\s+([\w\.]+)\s+([\d%]{2,4})\s+(/.{0,50})$",
                                  tmp.strip())
                if disk: disk = disk[0]
                if len(disk) < 6: continue
                if disk[2].find('M') != -1: continue
                if disk[2].find('K') != -1: continue
                if len(disk[6].split('/')) > 10: continue
                if disk[6] in cuts: continue
                if disk[6].find('docker') != -1: continue
                if disk[1].strip() in ['tmpfs']: continue
                arr = {}
                arr['filesystem'] = disk[0].strip()
                arr['type'] = disk[1].strip()
                arr['path'] = disk[6]
                tmp1 = [disk[2], disk[3], disk[4], disk[5]]
                arr['size'] = tmp1
                if int(inodes[1]) == 0 and int(inodes[2]) == 0:
                    arr['inodes'] = [inodes[1], 10000, 10000, 0]
                else:
                    arr['inodes'] = [inodes[1], inodes[2], inodes[3], inodes[4]]
                diskInfo.append(arr)
            except:
                continue
        return diskInfo

    # 取磁盘可用空间
    def get_disk_free(self, dfile):
        diskInfo = self.GetDiskInfo2()
        if not diskInfo: return '', 0, 0
        _root = None
        for d in diskInfo:
            if d['path'] == '/':
                _root = d
                continue
            if re.match("^{}/.+".format(d['path']), dfile):
                return d['path'], float(d['size'][2]) * 1024, int(d['inodes'][2])
        if _root:
            return _root['path'], float(_root['size'][2]) * 1024, int(_root['inodes'][2])
        return '', 0, 0

    # 备份指定目录
    def backup_path(self, spath, dfile=None, exclude=[], save=3, echo_id=None):
        try:
            if echo_id is None:
                echo_id = self.echo_id
            self.cron_info = public.M('crontab').where('echo=?', (echo_id,)).field(
                'backupto,name,save_local,notice,notice_channel,id,sType,split_type,split_value').select()[0]
            error_msg = ""
            self.echo_start()
            if not os.path.exists(spath):
                error_msg = 'The specified directory {} does not exist!'.format(spath)
                self.echo_error(error_msg)
                self.send_failture_notification(error_msg, target="{}|path".format(spath))
                return False

            if spath[-1] == '/':
                spath = spath[:-1]

            dirname = os.path.basename(spath)
            if not dfile:
                fname = 'path_{}_{}_{}.tar.gz'.format(dirname, public.format_date("%Y%m%d_%H%M%S"),
                                                      public.GetRandomString(6))
                dfile = os.path.join(self._BACKUP_DIR, 'path',dirname, fname)
            
            if not self.backup_path_to(spath, dfile, exclude):
                if self._error_msg:
                    error_msg = self._error_msg
                self.send_failture_notification(error_msg, target="{}|path".format(spath))
                return False
            cloud_name = self.cron_info['backupto']
            if self._cloud is None:
                from cloud_stora_upload_v2 import CloudStoraUpload
                self._cloud_new = CloudStoraUpload()
                self._cloud = self._cloud_new.run(cloud_name)

            if not self._cloud:
                if cloud_name != 'localhost':
                    error_msg = "Failed to link to cloud storage, please check if the configuration is correct!"
                    self.echo_error(error_msg)
                    self.send_failture_notification(error_msg, target=self.cron_info['name'], remark='Link to cloud storage failed')

            backup_size = os.path.getsize(dfile)
            if self._cloud:
                upload_path = os.path.join("path", dirname)
                self.echo_info("Uploading to {}, please wait...".format(self._cloud._title))

                # 判断是否 大于 5 GB 进行切割上传
                if backup_size >= self._SPLIT_SIZE and self.cron_info.get("split_type") and self.cron_info.get("split_value") and (
                        self.cron_info.get("split_type") != "size" or backup_size // 1024 // 1024 > self.cron_info.get("split_value")):
                    is_status, err = self.split_upload_file(dfile, upload_path)
                    if is_status is False:
                        remark = "Backup to " + self._cloud._title
                        self.send_failture_notification(err, target="{}|path".format(spath), remark=remark)
                        return False, err
                    fname = err  # 云存储保存路径
                else:  # 正常上传
                    if self._cloud._title in ["多吉云COS"]:
                        upload_file_path=os.path.join(self._cloud.backup_path , 'path',dirname, fname)
                    else:
                        upload_file_path="path"

                    if self._cloud.upload_file(dfile, upload_file_path):
                        self.echo_info("Successfully uploaded to {}".format(self._cloud._title))
                    else:
                        if hasattr(self._cloud, "error_msg"):
                            if self._cloud.error_msg:
                                error_msg = self._cloud.error_msg
                        if not error_msg:
                            error_msg = "The scheduled task execution failed."
                        self.echo_error(error_msg)
                        if os.path.exists(dfile):
                            os.remove(dfile)

                        remark = "Backup to" + self._cloud._title
                        self.send_failture_notification(error_msg, target="{}|path".format(spath), remark=remark)
                        return False

            filename = dfile
            if self._cloud:
                filename = dfile + '|' + self._cloud._name + '|' + fname
            cron_id = 0
            if echo_id:
                cron_id = public.M("crontab").where('echo=?', (echo_id,)).getField('id')
            pdata = {
                'cron_id': cron_id,
                'type': '2',
                'name': spath,
                'pid': 0,
                'filename': filename,
                'addtime': public.format_date(),
                'size': backup_size
            }
            public.M('backup').insert(pdata)

            if self._cloud:
                _not_save_local = True
                save_local = 0
                if self.cron_info:
                    save_local = self.cron_info["save_local"]
                if save_local:
                    _not_save_local = False
                else:
                    if self._is_save_local:
                        _not_save_local = False

                        pdata = {
                            'cron_id': cron_id,
                            'type': '2',
                            'name': spath,
                            'pid': 0,
                            'filename': dfile,
                            'addtime': public.format_date(),
                            'size': backup_size
                        }
                        public.M('backup').insert(pdata)
                if _not_save_local:
                    if os.path.exists(dfile):
                        os.remove(dfile)
                        self.echo_info("User settings do not retain local backups, deleted {}".format(dfile))
                else:
                    self.echo_info("Local backup has been kept")

            if not self._cloud:
                backups = public.M('backup').where(
                    "cron_id=? and type=? and pid=? and name=? and filename NOT LIKE '%|%'",
                    (cron_id, '2', 0, spath)).field('id,name,filename').select()
            else:
                backups = public.M('backup').where("cron_id=? and type=? and pid=? and name=? and filename LIKE ?",
                                                   (cron_id, '2', 0, spath, '%{}%'.format(self._cloud._name))).field(
                    'id,name,filename').select()

            self.delete_old(backups, save, 'path')
            self.echo_end()
            self.save_backup_status(True, target="{}|path".format(spath))
            return dfile
        except:
            self.send_failture_notification('Backup failed')

    # 清理过期备份文件
    def delete_old(self, backups, save, data_type=None, site_name=None):
        if type(backups) == str:
            self.echo_info('Failed to clean expired backup, error:{} '.format(backups))
            return
        self.echo_info('Keep the latest number of backups: {} copies'.format(save))
        # 跳过手动备份文件
        new_backups = []
        for i in range(len(backups)):
            if data_type == 'database':  # 数据库备份
                new_backups.append(backups[i])
            elif data_type == 'site' and backups[i]['name'][:4] == 'web_' and backups[i]['name'][-7:] == '.tar.gz':  # 网站备份
                new_backups.append(backups[i])
            elif data_type == 'path' and backups[i]['name'][:5] == 'path_':  # 目录备份
                new_backups.append(backups[i])
        if new_backups:
            backups = new_backups[:]
        num = len(backups) - int(save)
        if num > 0:
            self.echo_info('-' * 88)
            for backup in backups:
                # 处理目录备份到远程的情况
                if backup['filename'].find('|') != -1:
                    tmp = backup['filename'].split('|')
                    backup['filename'] = tmp[0]
                    backup['name'] = tmp[-1]
                # 尝试删除本地文件
                if os.path.exists(backup['filename']):
                    os.remove(backup['filename'])
                    self.echo_info(public.lang('Expired backup files have been cleaned from disk: {}',backup['filename']))
                # 尝试删除远程文件
                if self._cloud:
                    if backup['name'].endswith("_split"):  # 是否为切割文件
                        self._cloud_new.cloud_delete_dir(backup['name'])
                    elif data_type == "database":
                        self._cloud_new.cloud_delete_file(backup.get("cloud_path"))
                    elif data_type == "site":
                        try:
                            siteName = public.M('sites').where('id=?', (backup['pid'],)).getField('name')
                            site_backup_dir= self._cloud_new.backup_path
                            fname = backup['name']
                            dfile = os.path.join(site_backup_dir, 'site', siteName, fname)
                            self._cloud_new.cloud_delete_file(dfile)
                        except:
                            # import traceback
                            # print(traceback.format_exc())
                            pass
                    else:
                        self._cloud.delete_file(backup['name'], data_type)
                    self.echo_info(public.lang('Expired backup files have been cleaned from {}: {}',
                                                          self._cloud._title, backup['name']))

                # 从数据库清理
                public.M('backup').where('id=?', (backup['id'],)).delete()
                num -= 1
                if num < 1: break
        # if data_type=='site':
        #     backup_path = public.get_backup_path()+'/site'.replace('//','/')
        #     site_lists = os.listdir(backup_path)
        #     file_info =[]
        #     del_list=[]
        #     check_name = 'web_{}_'.format(site_name)
        #     for site_v in site_lists:
        #         tmp_dict = {}
        #         if check_name=='web__':continue
        #         if site_v.find(check_name)==-1:continue
        #         filename =os.path.join(backup_path,site_v)
        #         if os.path.isfile(filename):
        #             tmp_dict['name']=filename
        #             tmp_dict['time']=int(os.path.getmtime(filename))
        #             file_info.append(tmp_dict)
        #     if file_info and len(file_info)>int(save):
        #         file_info=sorted(file_info,key=lambda keys:keys['time'])
        #         del_list=file_info[:-int(save)]
        #         for del_file in del_list:
        #             if not del_file:continue
        #             if os.path.isfile(del_file['name']):
        #                 os.remove(del_file['name'])
        #                 self.echo_info(u"已从磁盘清理过期备份文件：" + del_file['name'])

    # 压缩目录
    def backup_path_to(self, spath, dfile, exclude=[], siteName=None):
        if not os.path.exists(spath):
            error_msg = public.lang('The specified directory {} does not exist!', spath)
            self.echo_error(error_msg)
            return False

        if spath[-1] == '/':
            spath = spath[:-1]

        dirname = os.path.basename(spath)
        dpath = os.path.dirname(dfile)
        if not os.path.exists(dpath):
            os.makedirs(dpath, 384)
        self.get_exclude(exclude)
        if self._exclude:
            self._exclude = self._exclude.replace(spath + '/', '')
        exclude_config = self._exclude
        exclude_list = self.get_exclude_list(exclude)
        p_size = public.get_path_size(spath, exclude=exclude_list)
        if not self._exclude:
            exclude_config = "Not set"

        if siteName:
            self.echo_info(public.lang('Backup site: {}', siteName))
            self.echo_info(public.lang('Website document root: {}', spath))
        else:
            self.echo_info(public.lang('Backup directory: {}', spath))

        self.echo_info(public.lang('Directory size: {}',str(public.to_size(p_size))))
        self.echo_info(public.lang('Exclusion setting: {}', exclude_config))
        disk_path, disk_free, disk_inode = self.get_disk_free(dfile)
        self.echo_info(public.lang(
            'Partition {} available disk space is: {}, available Inode is: {}',disk_path, str(public.to_size(disk_free)), str(disk_inode)))
        if disk_path:
            if disk_free < p_size:
                self.echo_error(public.lang(
                    'The available disk space of the target partition is less than {}, and the backup cannot be completed. Please increase the disk capacity or change the default backup directory on the settings page!',
                    str(public.to_size(p_size))
                ))
                return False

            if disk_inode < self._inode_min:
                self.echo_error(public.lang(
                    'The available Inode of the target partition is less than {}, and the backup cannot be completed. Please increase the disk capacity or change the default backup directory on the settings page!',
                    str(self._inode_min)
                ))
                return False

        stime = time.time()
        self.echo_info("Start compressing files: {}".format(public.format_date(times=stime)))
        if os.path.exists(dfile):
            os.remove(dfile)
        public.ExecShell("cd " + os.path.dirname(
            spath) + " && tar zcvhf '" + dfile + "' " + self._exclude + " '" + dirname + "' 2>{err_log} 1> /dev/null".format(
            err_log=self._err_log))
        tar_size = os.path.getsize(dfile)
        if tar_size < 1:
            self.echo_error(public.lang("Compression failed!"))
            self.echo_info(public.readFile(self._err_log))
            return False
        compression_time = str('{:.2f}'.format(time.time() - stime))
        self.echo_info(public.lang('Compression completed, took {} seconds, compressed package size: {}',compression_time, str(public.to_size(tar_size))))
        if siteName:
            self.echo_info(public.lang('Site backed up to: {}', dfile))
        else:
            self.echo_info(public.lang('Directory has been backed up to: {}', dfile))
        if os.path.exists(self._err_log):
            os.remove(self._err_log)
        return dfile

    def remove_last_directory_if_directory(self,spath):

        # 获取路径的最后一个部分
        last_part = os.path.basename(spath)
        
        # 获取路径的上一级目录
        parent_dir = os.path.dirname(spath)
        
        # 构建完整路径
        full_path = os.path.join(parent_dir, last_part)      
        # 检查路径的最后一部分是否是文件
        if os.path.isfile(full_path):
            # 如果是文件，返回上一级目录
            return parent_dir + "/"
        else:
            # 如果不是文件，返回原路径
            return spath

    def __backup_site_init_cloud(self, cloud_name: str, siteName: str) -> None:
        if self._cloud is None:
            from cloud_stora_upload_v2 import CloudStoraUpload
            self._cloud_new = CloudStoraUpload()
            self._cloud = self._cloud_new.run(cloud_name)

        if not self._cloud:
            if cloud_name != 'localhost':
                self.echo_info("Failed to link to cloud storage, please check if the configuration is correct!")
                self.send_failture_notification(
                    '"Failed to link to cloud storage, please check if the configuration is correct!"',
                    target="{}|site".format(siteName), remark='')

    def __backup_site_cloud_upload(self, backup_size, dfile, upload_path, siteName, fname) -> bool:
        # 判断是否 大于 5 GB 进行切割上传
        if backup_size >= self._SPLIT_SIZE and self.cron_info.get("split_type") and self.cron_info.get(
                "split_value") and (
                self.cron_info.get("split_type") != "size" or
                backup_size // 1024 // 1024 > self.cron_info.get("split_value")
        ):
            is_status, err = self.split_upload_file(dfile, upload_path)
            if is_status is False:
                remark = "Backup to " + self._cloud._title
                self.send_failture_notification(err, target="{}|site".format(siteName), remark=remark)
                return False
            # fname = err  # 云存储保存路径
        else:  # 正常上传
            error_msg = ''
            if self._cloud._title in [
                "AWS S3", "AWS S3对象存储", "天翼云ZOS", "MinIO存储", "多吉云COS"
            ]:  ## 由于aws s3上传函数独特，单独处理
                if self._cloud._title == "AWS S3":
                    res = self._cloud.upload_file1(dfile,
                                                   os.path.join(self._cloud.backup_path, 'site', siteName, fname))
                else:
                    res = self._cloud.upload_file(dfile, os.path.join('site', siteName))

            else:  # ftp,  google drive...
                res = self._cloud.upload_file(dfile, 'site')

            if not res:
                if hasattr(self._cloud, "error_msg"):
                    if self._cloud.error_msg:
                        error_msg = self._cloud.error_msg
                if not error_msg:
                    error_msg = public.lang("Backup task execution failed.")
                self.echo_error(error_msg)
                # if os.path.exists(dfile):
                #     os.remove(dfile)
                remark = public.lang("Backup to " + self._cloud._title)
                self.send_failture_notification(error_msg, target="{}|site".format(siteName), remark=remark)
                return False

            self.echo_info("Successfully uploaded to {}".format(self._cloud._title))
            return True

    def __backup_site_check_local_flag(self) -> bool:
        if self.cron_info['backupTo'] == "localhost":
            if_save_local = True
        else:
            if_save_local = self.cron_info["save_local"] if self.cron_info else 0
        if if_save_local and not self._is_save_local:
            os.mknod('data/is_save_local_backup.pl')
        save_local = True if self._is_save_local and if_save_local else False
        return save_local

    def __backup_site_delete_old(self, target: str, backups: list, save: int, data_type=None, if_wp: bool = False):
        self.echo_info('-' * 88)
        self.echo_info('Keep the latest number of backups: {} copies for {}'.format(save, target))
        num = len(backups) - int(save)
        if num > 0:
            for backup in backups:
                try:
                    # 从数据库清理
                    if not if_wp:
                        public.M('backup').where('id=?', (backup['id'],)).delete()
                    else:
                        public.M('wordpress_backups').where('id=?', (backup['id'],)).delete()

                    if os.path.exists(backup.get('filename', '')):
                        os.remove(backup['filename'])
                        self.echo_info(public.lang(
                            'Expired backup files have been cleaned from disk: {}', backup['filename'])
                        )
                    # 尝试删除远程site文件
                    elif backup.get('filename', '').find('|') != -1 and self._cloud and data_type == 'site':
                        try:
                            tmp = backup['filename'].split('|')
                            backup['filename'] = tmp[0]
                            backup['name'] = tmp[-1]
                            siteName = public.M('sites').where('id=?', (backup['pid'],)).getField('name')
                            site_backup_dir = self._cloud_new.backup_path
                            fname = backup['name']
                            dfile = os.path.join(site_backup_dir, 'site', siteName, fname)
                            res = self._cloud_new.cloud_delete_file(dfile, 'site')
                            if res:
                                remote_name = backup.get('name', '')
                                if not remote_name:
                                    remote_name = backup.get('filename', '').split('|')[-1]
                                remote_path = os.path.join(self._cloud.backup_path, 'site', siteName, remote_name)
                                self.echo_info(
                                    public.lang(
                                        'Expired backup files have been cleaned from {}: {}', target, remote_path
                                    ))
                            return res
                        except Exception:
                            continue
                    else:
                        continue
                except Exception:
                    continue
                num -= 1
                if num < 1:
                    break

    # 备份指定站点
    def backup_site(self, siteName, save: int = 3, exclude: list = None, echo_id=None) -> str | bool:
        panelPath = '/www/server/panel/'
        os.chdir(panelPath)
        sys.path.insert(0, panelPath)
        echo_id = self.echo_id if echo_id is None else echo_id
        cron_id = public.M("crontab").where('echo=?', (echo_id,)).getField('id') if echo_id else 0
        self.echo_start()
        self.cron_info = public.M('crontab').where('echo=?', (echo_id,)).field(
            'backupTo,name,save_local,notice,notice_channel,id,sType,split_type,split_value,db_backup_path'
        ).select()[0]
        if not self.cron_info:
            return False
        save_local = self.__backup_site_check_local_flag()
        find = public.M('sites').where('name=?', (siteName,)).select()[0]
        if not find:
            error_msg = 'The specified website [{}] does not exist!'.format(siteName)
            self.echo_error(error_msg)
            self.send_failture_notification(error_msg, target=siteName)
            return False

        # if self.cron_info['stop_site']=="1" :
        #     if find['project_type']=="PHP":
        #         if find['status']=="0":
        #             print("|-网站{}已停用，跳过备份".format(siteName))
        #             return False
        # if find['project_type']=="Java":
        #     from mod.project.java.projectMod import main as java
        #     if not java().get_project_stat(find)['pid']:
        #         print("|-网站{}已停用，跳过备份".format(siteName))
        #         return False
        # if find['project_type']=="Node":
        #     from projectModel.nodejsModel import main as nodejs
        #     if not nodejs().get_project_run_state(project_name=find['name']):
        #         print("|-网站{}已停用，跳过备份".format(siteName))
        #         return False
        # if find['project_type']=="Go":
        #     from projectModel.goModel import main as go
        #     if not go().get_project_run_state(project_name=find['name']):
        #         print("|-网站{}已停用，跳过备份".format(siteName))
        #         return False

        # if find['project_type']=="Python":
        #     from projectModel.pythonModel import main as python
        #     if not python().get_project_run_state(project_name=find['name']):
        #         print("|-网站{}已停用，跳过备份".format(siteName))
        #         return False

        # if find['project_type']=="Other":

        #     from projectModel.otherModel import main as other
        #     if not other().get_project_run_state(project_name=find['name']):
        #         print("|-网站{}已停用，跳过备份".format(siteName))
        #         return False

        # if self.cron_info['stop_site']=="1" and find['status']=="0":
        #     print("{}网站已停用，跳过备份".format(siteName))
        #     return False
        site_backup_dir = self.get_site_backup_dir(
            self.cron_info['backupTo'], self.cron_info['db_backup_path'], siteName
        )
        backup_dir = os.path.join(site_backup_dir, 'site')

        # save local file at first, insert db depend on 'save_local'
        bak_info = None
        if find['project_type'] != 'WP2':
            spath = find['path']
            pid = find['id']
            fname = 'web_{}_{}_{}.tar.gz'.format(
                siteName, public.format_date("%Y%m%d_%H%M%S"), public.GetRandomString(6)
            )  # save
            dfile = os.path.join(site_backup_dir, 'site', siteName, fname)
            if find['project_type'] == "Go":
                spath = self.remove_last_directory_if_directory(spath)

            if not self.backup_path_to(spath, dfile, exclude, siteName=siteName):
                error_msg = self._error_msg if self._error_msg else ""
                self.send_failture_notification(error_msg, target=siteName)
                return False
            # insert
            if save_local:
                public.M('backup').insert({
                    'cron_id': cron_id,
                    'type': 0,
                    'name': fname,
                    'pid': pid,
                    'filename': dfile,
                    'addtime': public.format_date(),
                    'size': os.path.getsize(dfile)
                })
        else:
            try:
                from wp_toolkit import wpbackup
                # save & insert
                bak_info = wpbackup(find['id']).backup_full_get_data(False)
                self.echo_info(public.lang('Backup wordpress [{}] successfully', siteName))
            except Exception as e:
                self.echo_info(str(e))
                self.echo_end()
                return False
            pid = bak_info.id
            fname = bak_info.bak_file.split('/')[-1]
            dfile = bak_info.bak_file

        backup_size = os.path.getsize(dfile)
        if not self._backup_all:
            self.check_disk_space(backup_size, backup_dir)

        # init_cloud
        self.__backup_site_init_cloud(cloud_name=self.cron_info['backupTo'], siteName=siteName)

        # cloud part
        if self._cloud:
            cloud_file_name = dfile + '|' + self._cloud._name + '|' + fname
            upload_path = os.path.join("site", siteName)
            self.echo_info("Uploading to {}, please wait...".format(self._cloud._title))
            res = self.__backup_site_cloud_upload(backup_size, dfile, upload_path, siteName, fname)
            if res:
                # insert data
                if find['project_type'] != 'WP2':
                    public.M('backup').insert({
                        'cron_id': cron_id,
                        'type': 0,
                        'name': fname,
                        'pid': pid,
                        'filename': cloud_file_name,
                        'addtime': public.format_date(),
                        'size': backup_size
                    })
                else:  # wp
                    public.M('wordpress_backups').insert({
                        's_id': bak_info.site_id,
                        'bak_type': 3,
                        'bak_file': cloud_file_name,
                        'bak_time': bak_info.bak_time,
                        'size': backup_size,
                    })
                self.echo_info(public.lang("Local backup has been kept"))

                if not save_local:  # 选了云但没选择保存本地, 移除
                    public.M('wordpress_backups').where('id=?', (pid,)).delete()
                    if os.path.exists(dfile):
                        os.remove(dfile)
                        self.echo_info(public.lang(
                            'User settings do not retain local backups, deleted {}', dfile
                        ))
            else:
                self.echo_info("upload to cloud fail...please check if the configuration is correct!")
                public.WriteLog("Cloud_Upload", "upload to cloud fail...")

        # 清理多余备份
        if find['project_type'] != 'WP2':
            if save_local:
                local_backups = public.M('backup').where(
                    "cron_id=? AND type=? AND pid=? AND filename NOT LIKE '%|%' AND name LIKE 'web_%'",
                    (cron_id, '0', pid)
                ).order('addtime').select()
                # 清理local
                self.__backup_site_delete_old('Local Storage', local_backups, save, 'site')
            if self._cloud:
                cloud_backups = public.M('backup').where(
                    'cron_id=? and type=? and pid=? and filename LIKE ?',
                    (cron_id, '0', pid, f"%{self._cloud._name}%")
                ).order('addtime').select()
                self.__backup_site_delete_old(self._cloud._title, cloud_backups, save, 'site')  # 清理cloud
        else:
            # wp
            site_id = public.M('sites').where('name=?', (siteName,)).getField('id')
            if save_local:
                local_wp_backups = public.M('wordpress_backups').where(
                    "s_id=? AND bak_file NOT LIKE '%|%' AND bak_file LIKE '%web_%'",
                    (site_id,)
                ).order('bak_time').select()
                local_wp_backups = [
                    {
                        'id': x.get('id'),
                        'pid': x.get('s_id'),
                        'name': x.get('bak_file', '').split('/')[-1],  # 纯文件名
                        'filename': x.get('bak_file', ''),  # 绝对路径
                    } for x in local_wp_backups if x
                ]
                # 清理wp2 local
                self.__backup_site_delete_old('Local Storage', local_wp_backups, save, 'site', True)
            if self._cloud:
                cloud_wp_backups = public.M('wordpress_backups').where(
                    's_id=? AND bak_file LIKE ?', (site_id, f"%{self._cloud._name}%")
                ).order('bak_time').select()
                cloud_wp_backups = [
                    {
                        'id': x.get('id'),
                        'pid': x.get('s_id'),
                        'name': x.get('bak_file', '').split('|')[0].split('/')[-1],  # 纯文件名
                        'filename': x.get('bak_file', ''),  # 绝对路径
                    } for x in cloud_wp_backups if x
                ]
                # 清理wp2 cloud
                self.__backup_site_delete_old(self._cloud._title, cloud_wp_backups, save, 'site', True)

        self.echo_end()
        return dfile
    def delete_old_from_wp2(self, save,siteName):
        """
        @name 从wp删除过期备份文件
        @author hezhihong
        """
        site_id=public.M('sites').where('name=?',(siteName,)).getField('id')
        if not site_id:
            self.echo_info('Failed to clean expired backup, error: site id not found')
            return
        backups =public.M('wordpress_backups').where('s_id=?',(site_id,)).select()
        if type(backups) == str:
            self.echo_info('Failed to clean expired backup, error:{} '.format(backups))
            return
        self.echo_info('Keep the latest number of backups: {} copies'.format(save))
        num = len(backups) - int(save)
        if num > 0:
            for backup in backups:
                if os.path.exists(backup['bak_file']):
                    os.remove(backup['bak_file'])
                    self.echo_info(public.lang('Expired backup files have been cleaned from disk: {}', backup['bak_file']))
                public.M('wordpress_backups').where('id=?', (backup['id'],)).delete()
                num -= 1
                if num < 1: break

    # 备份所有站点
    def backup_site_all(self, save=3, echo_id=None):
        if echo_id is None:
            echo_id = self.echo_id
        self.cron_info = public.M('crontab').where('echo=?', (echo_id,)).field(
            'backupto,name,save_local,notice,notice_channel,id,sType').select()[0]
        sites = public.M('sites').field('name').select()
        self._backup_all = True
        failture_count = 0
        results = []
        backup_files = []  # 用于存储成功备份的文件路径
        if self._cloud == None:
            try:
                cloud_name = self.cron_info['backupTo']
            except:
                cloud_name = self.cron_info['backupto']
            from cloud_stora_upload_v2 import CloudStoraUpload
            self._cloud_new = CloudStoraUpload()
            self._cloud = self._cloud_new.run(cloud_name)
        for site in sites:
            self._error_msg = ""
            result = self.backup_site(site['name'], save, echo_id=echo_id)
            if not result:
                failture_count += 1
            else:
                backup_files.append(result)  # 收集成功备份的文件路径
            results.append((site['name'], result, self._error_msg,))
            self.save_backup_status(result, target="{}|site".format(site['name']), msg=self._error_msg)

        if failture_count > 0:
            self.send_all_failture_notification("site", results)
        else:
            size = sum(os.path.getsize(file) for file in backup_files if os.path.exists(file))
            backup_dir=self._BACKUP_DIR
            self.check_disk_space(size,backup_dir)
        
        self._backup_all = False

    # 配置
    def mypass(self, act):
        conf_file = '/etc/my.cnf'
        conf_file_bak = '/etc/my.cnf.bak'
        if os.path.getsize(conf_file) > 2:
            public.writeFile(conf_file_bak, public.readFile(conf_file))
            public.set_mode(conf_file_bak, 600)
            public.set_own(conf_file_bak, 'mysql')
        elif os.path.getsize(conf_file_bak) > 2:
            public.writeFile(conf_file, public.readFile(conf_file_bak))
            public.set_mode(conf_file, 600)
            public.set_own(conf_file, 'mysql')

        public.ExecShell("sed -i '/user=root/d' {}".format(conf_file))
        public.ExecShell("sed -i '/password=/d' {}".format(conf_file))
        if act:
            password = public.M('config').where('id=?', (1,)).getField('mysql_root')
            mycnf = public.readFile(conf_file)
            if not mycnf: return False
            src_dump_re = r"\[mysqldump\][^.]"
            sub_dump = "[mysqldump]\nuser=root\npassword=\"{}\"\n".format(password)
            mycnf = re.sub(src_dump_re, sub_dump, mycnf)
            if len(mycnf) > 100: public.writeFile(conf_file, mycnf)
            return True
        return True

    # map to list
    def map_to_list(self, map_obj):
        try:
            if type(map_obj) != list and type(map_obj) != str: map_obj = list(map_obj)
            return map_obj
        except:
            return []

    # 备份所有数据库
    def backup_database_all(self, save, echo_id: str):
        if echo_id is None:
            echo_id = self.echo_id
        self.cron_info = public.M('crontab').where("echo=? and sType='database'", (echo_id,)).find()
        if not self.cron_info:
            print(public.lang("The scheduled task does not exist!"))

        sName = self.cron_info["sName"]
        save = self.cron_info["save"]
        db_type = str(self.cron_info.get("db_type", "mysql")).lower()
        if not db_type:
            public.M('crontab').where("echo=? and sType='database'", (echo_id,)).update({"db_type": "mysql"})
            self.cron_info["db_type"] = "mysql"
            db_type = "mysql"
        if db_type == "mysql":
            try:
                from database import database
                database = database()
                mysql_server = public.M('database_servers').where("db_type=?", ('mysql',)).select()
                for i in mysql_server:
                    database.SyncGetDatabases(public.to_dict_obj({'sid': i['id']}))
            except:
                pass
        database_list = []
        if db_type in ["mysql", "mongodb", "pgsql"]:
            if sName == "ALL":  # 备份所有数据库
                data_list = public.M("databases").field("name").where("LOWER(type)=LOWER(?)", (db_type)).select()
                database_list = [data["name"] for data in data_list]
        elif db_type == "redis":
            database_list.append("redis")

        # 上传对象
        self._cloud = None
        cloud_name = self.cron_info["backupTo"]
        if cloud_name.find("localhost") == -1:
            from cloud_stora_upload_v2 import CloudStoraUpload
            self._cloud_new = CloudStoraUpload()
            self._cloud = self._cloud_new.run(cloud_name)
        self._backup_all = True
        resp_list = []
        failture_count = 0
        for db_name in database_list:
            status, backup_path = self.backup_database(db_name, save, echo_id=echo_id)
            if status is False:
                failture_count += 1
            resp_list.append((db_name, status, backup_path))
        if failture_count > 0:
            self.send_all_failture_notification("database", resp_list)
        else:
            size = 0
            backup_dir=self._DB_BACKUP_DIR
            self.check_disk_space(size,backup_dir)       
        self._backup_all = False

    # 备份单个数据库
    def backup_database(self, sName, save, echo_id: str):
        self.echo_start()
        if echo_id is None:
            echo_id = self.echo_id
        self.cron_info = public.M('crontab').where("echo=? and sType='database'", (echo_id,)).find()
        # print(self.cron_info)
        if not self.cron_info:
            error_msg = public.lang("The scheduled task does not exist! {}",str(echo_id))
            self.echo_error(error_msg)
            self.send_failture_notification(error_msg)
            return False, error_msg
        sName = sName.strip()
        save = self.cron_info["save"]
        db_type = str(self.cron_info.get("db_type", "mysql")).lower()
        if not db_type:
            public.M('crontab').where("echo=? and sType='database'", (echo_id,)).update({"db_type": "mysql"})
            self.cron_info["db_type"] = "mysql"
            db_type = "mysql"

        database = {}
        if db_type in ["mysql", "mongodb", "pgsql"]:
            database = public.M("databases").where("name=? and LOWER(type)=LOWER(?)", (sName, db_type)).find()
            if not database:
                error_msg = public.lang("{} Backup database {} does not exist",db_type, sName)
                self.echo_error(error_msg)
                self.send_failture_notification(error_msg, target="{}|database".format(sName))
                return False, error_msg

        elif db_type == "redis":
            database = {"id": 0, "name": "redis", "db_type": 0}
        db_name = database["name"]

        # if not database:

        #     error_msg = "{} 备份数据库 {} 不存在".format(db_type, sName)
        #     self.echo_error(error_msg)
        #     self.send_failture_notification(error_msg, target="{}|database".format(db_name))
        #     return False, error_msg

        func_dict = {
            "mysql": self.mysql_backup_database,
            "mongodb": self.mongodb_backup_database,
            "redis": self.redis_backup_database,
            "pgsql": self.pgsql_backup_database,
        }

        func_backup_database = func_dict[db_type]
        table_list=self.cron_info["table_list"]
        if table_list:
            # 备份
            args = {"backup_mode": self.cron_info["backup_mode"], "db_backup_path": self.cron_info["db_backup_path"], "save_local": self.cron_info["save_local"],"table_list":[table_list]}
        else:

            # 备份
            args = {"backup_mode": self.cron_info["backup_mode"], "db_backup_path": self.cron_info["db_backup_path"], "save_local": self.cron_info["save_local"]}
        status, msg = func_backup_database(database, args)
        if status is False:  # 备份失败
            self.send_failture_notification(msg, target="{}|database".format(db_name))
            return status, msg

        backup_path = msg
        backup_size = os.path.getsize(backup_path)
        if not self._backup_all:
             self.check_disk_space(backup_size,backup_path)
        file_name = os.path.basename(backup_path)
        # 上传对象
        if self._cloud is None:
            cloud_name = self.cron_info["backupTo"]
            if cloud_name.find("localhost") == -1:
                from cloud_stora_upload_v2 import CloudStoraUpload
                self._cloud_new = CloudStoraUpload()
                self._cloud = self._cloud_new.run(cloud_name)
        # 上传
        if self._cloud is not None:
            if self._cloud is False:
                error_msg = public.lang("Failed to link to cloud storage, please check if the configuration is correct!")
                self.echo_info(error_msg)
                self.send_failture_notification(error_msg, target="{}|database".format(db_name))
                return False, error_msg

            self.echo_info(public.lang("Uploading to {}, please wait...",self._cloud._title))

            # 判断是否 大于 5 GB 进行切割上传
            if backup_size >= self._SPLIT_SIZE and self.cron_info.get("split_type") and self.cron_info.get("split_value") and (
                    self.cron_info.get("split_type") != "size" or backup_size // 1024 // 1024 > self.cron_info.get("split_value")):
                upload_path = os.path.join("database", db_type, db_name)
                is_status, err = self.split_upload_file(backup_path, upload_path)
                if is_status is False:
                    remark = public.lang("Backup to " + self._cloud._title)
                    self.send_failture_notification(err, target="{}|database".format(db_name), remark=remark)
                    return False, err
                file_name = err  # 云存储保存路径
            else:  # 正常上传
                if db_type=="redis":
                    upload_path = os.path.join(self._cloud_new.backup_path, "database", db_type, file_name)
                else:
                    upload_path = os.path.join(self._cloud_new.backup_path, "database", db_type, db_name, file_name)
                # print(upload_path)
                if self._cloud._title in ["AWS S3","AWS S3对象存储", "天翼云ZOS","WebDAV存储","MinIO存储","多吉云COS"]:  ## 由于aws s3上传函数独特，单独处理
                    if self._cloud._title == "AWS S3":
                        res = self._cloud.upload_file1(backup_path, upload_path)
                    else:
                        res = self._cloud.upload_file(backup_path, upload_path)
                    if res:
                        self.echo_info("Successfully uploaded to {}".format(self._cloud._title))
                    else:
                        if hasattr(self._cloud, "error_msg"):
                            if self._cloud.error_msg:
                                error_msg = self._cloud.error_msg
                        if not error_msg:
                            error_msg = "Backup task execution failed."
                        self.echo_error(error_msg)
                        if os.path.exists(upload_path):
                            os.remove(upload_path)

                        remark = "Backup to " + self._cloud._title
                        self.send_failture_notification(error_msg, target="{}|database".format(db_name), remark=remark)
                        return False
                else:
                    # if db_type=="redis":
                    #     upload_path = os.path.join(self._cloud_new.backup_path, "database", db_type, file_name)
                    # else:
                    #     upload_path = os.path.join(self._cloud_new.backup_path, "database", db_type, db_name, file_name)
                    upload_method = self._cloud.upload_file if self._cloud._title == "Google Drive" else self._cloud_new.cloud_upload_file
                    if upload_method(backup_path, upload_path):
                         self.echo_info("Successfully uploaded to {}".format(self._cloud._title))
                    else:
                        error_msg = "Backup task execution failed."
                        if hasattr(self._cloud, "error_msg"):
                            if self._cloud.error_msg:
                                error_msg = self._cloud.error_msg
                        self.echo_error(error_msg)
                        if os.path.exists(backup_path):
                            os.remove(backup_path)

                        remark = "Backup to " + self._cloud._title
                        self.send_failture_notification(error_msg, target="{}|database".format(db_name), remark=remark)
                        return False, error_msg


        cloud_backup_path = backup_path
        if self._cloud is not None:
            cloud_backup_path = backup_path + "|" + self._cloud._name + "|" + file_name

        self.echo_info("The database has been backed up to: {}".format(backup_path))
        if os.path.exists(self._err_log):
            os.remove(self._err_log)

        # back_to = self._CLOUD_OBJ[self.cron_info.get("backupTo")]
        back_to = self.cron_info.get("backupTo")
        pdata = {
            "type": "1",
            "name": file_name,
            "pid": database["id"],
            "filename": cloud_backup_path,
            "size": backup_size,
            "addtime": public.format_date(),
            "ps": "Plan task backup to {}".format(back_to),
            "cron_id": self.cron_info["id"],
        }
        public.M("backup").insert(pdata)

        if self._cloud is not None:  # 云端上传
            if self.cron_info.get("save_local", 0) == 0 and self._is_save_local:  # 本地保留
                pdata = {
                    "type": "1",
                    "name": file_name,
                    "pid": database["id"],
                    "filename": backup_path,
                    "size": backup_size,
                    "addtime": public.format_date(),
                    "ps": "Plan task backup to {}(Local reservation)".format(back_to),
                    "cron_id": self.cron_info["id"],
                }
                public.M("backup").insert(pdata)
            if self.cron_info.get("save_local", 0) == 0 and not self._is_save_local:
                if os.path.exists(backup_path):
                    os.remove(backup_path)
                    self.echo_info("User setting to not keep local backup, deleted {}".format(backup_path))
            else:  # 本地不保留
                self.echo_info("Local backup has been retained.")

        # 清理多余备份
        if self._cloud is not None:
            backups = public.M("backup").where("cron_id=? and type=? and pid=? and filename LIKE ?", (self.cron_info["id"], "1", database["id"], "%{}%".format(self._cloud._name))).field(
                "id,name,filename").select()
        else:
            backups = public.M("backup").where("cron_id=? and type=? and pid=? and filename NOT LIKE '%|%'", (self.cron_info["id"], "1", database["id"])).field("id,name,filename").select()

        if self._cloud:
            for backup in backups:
                if db_type=="redis":
                    backup["cloud_path"] = os.path.join(self._cloud_new.backup_path, "database", db_type, backup["name"])
                else:
                    backup["cloud_path"] = os.path.join(self._cloud_new.backup_path, "database", db_type, db_name, backup["name"])

        self.delete_old(backups, save, "database")
        self.echo_end()
        self.save_backup_status(True, target="{}|database".format(db_name))
        return True, backup_path

    # mysql 备份数据库
    def mysql_backup_database(self, db_find: dict, args: dict) -> Tuple[bool, str]:
        import db_mysql
        storage_type = args.get("storage_type", "db")  # 备份的文件数量， 按照数据库 | 按照表
        table_list = args.get("table_list", [])  # 备份的集合

        db_name = db_find["name"]
        db_host = "localhost"
        db_user = "root"
        if db_find["db_type"] == 0:  # 本地数据库
            backup_mode = args.get("backup_mode", "0")

            if backup_mode == "1":  # 使用非 root 账号
                db_user = db_find["username"]  # 获取数据库用户
                db_password = db_find["password"]  # 获取数据库密码
                print("Using non root user {} to backup database {}".format(db_user, db_name))
            else:  # 使用 root 账号
                # db_user = "root"
                db_password = public.M("config").where("id=?", (1,)).getField("mysql_root")
                if not db_password:
                    error_msg = "The database password is empty! Please set the database password first!"
                    self.echo_error(error_msg)
                    return False, error_msg
            try:
                from panelMysql import panelMysql
                db_port = int(panelMysql().query("show global variables like 'port'")[0][1])
            except:
                db_port = 3306
        elif db_find["db_type"] == 1:  # 远程数据库
            conn_config = json.loads(db_find["conn_config"])
            db_host = conn_config["db_host"]
            db_port = int(conn_config["db_port"])
            db_user = conn_config["db_user"]
            db_password = conn_config["db_password"]
        elif db_find["db_type"] == 2:
            conn_config = public.M("database_servers").where("id=? AND LOWER(db_type)=LOWER('mysql')", db_find["sid"]).find()
            db_host = conn_config["db_host"]
            db_port = int(conn_config["db_port"])
            db_user = conn_config["db_user"]
            db_password = conn_config["db_password"]
        else:
            error_msg = "Unknown database type"
            self.echo_error(error_msg)
            return False, error_msg

        if not db_password:
            error_msg = "The database password cannot be empty"
            self.echo_error(error_msg)
            return False, error_msg
        db_charset = public.get_database_character(db_name)

        mysql_obj = db_mysql.panelMysql().set_host(db_host, db_port, None, db_user, db_password)
        if isinstance(mysql_obj, bool):
            error_msg = "Failed to connect to database [{}: {}]".format(db_host, db_port)
            self.echo_error(error_msg)
            return False, error_msg

        db_data = mysql_obj.query("select sum(DATA_LENGTH)+sum(INDEX_LENGTH) from information_schema.tables where table_schema='{}'".format(db_name))
        db_size = 0
        if isinstance(db_data, list) and len(db_data) != 0:
            if db_data[0][0] != None:
                db_size = db_data[0][0]

        if not db_size:
            error_msg = "The specified database '{}' has no data!".format(db_name)
            self.echo_error(error_msg)
            return False, error_msg
        self.echo_info('Backup MySQL database: {}'.format(db_name))
        self.echo_info("Database size: {}".format(public.to_size(db_size)))
        self.echo_info("Database Character Set: {}".format(db_charset))

        disk_path, disk_free, disk_inode = self.get_disk_free(self._MYSQL_BACKUP_DIR)
        self.echo_info("The available disk space for partition {} is: {}, and the available Inode is: {}".format(disk_path, public.to_size(disk_free), disk_inode))
        if disk_path:
            if disk_free < db_size:
                error_msg = "The available disk space of the target partition is less than {}, and the backup cannot be completed. Please increase the disk capacity or change the default backup directory on the settings page!".format(public.to_size(db_size))
                self.echo_error(error_msg)
                return False, error_msg
            if disk_inode < self._inode_min:
                error_msg = "The available Inode for the target partition is less than {}, and the backup cannot be completed. Please increase the disk capacity or change the default backup directory on the settings page!".format(self._inode_min)
                self.echo_error(error_msg)
                return False, error_msg
        stime = time.time()
        self.echo_info("Start exporting database:{}".format(public.format_date(times=stime)))

        mysql_backup_dir = self.get_backup_dir(db_find, args, "mysql")
        db_backup_dir = os.path.join(mysql_backup_dir, db_name)
        if not os.path.exists(db_backup_dir):
            os.makedirs(db_backup_dir)
        file_name = "{db_name}_{backup_time}_mysql_data".format(db_name=db_name, backup_time=time.strftime("%Y-%m-%d_%H-%M-%S", time.localtime()))

        backup_shell = "'{mysqldump_bin}' --opt --hex-blob --skip-lock-tables --single-transaction --routines --events --skip-triggers --default-character-set='{db_charset}' --force " \
                       "--host='{db_host}' --port={db_port} --user='{db_user}' --password='{db_password}' '{db_name}'".format(
            mysqldump_bin=self._MYSQLDUMP_BIN,
            db_charset=db_charset,
            db_user=db_user,
            db_password=db_password,
            db_host=db_host,
            db_port=db_port,
            db_name=db_name,
        )

        if storage_type == "db":  # 导出单个文件
            file_name = file_name + ".sql.gz"
            backup_path = os.path.join(db_backup_dir, file_name)
            table_shell = ""
            if len(table_list) != 0:
                if table_list and isinstance(table_list[0], str):
                    table_list = table_list[0].split(',')
                    # print("正在备份表{}".format(table_list))

                table_shell = "'" + "' '".join(table_list) + "'"
            backup_shell += " {table_shell} 2> '{err_log}' | gzip > '{backup_path}'".format(table_shell=table_shell, err_log=self._err_log, backup_path=backup_path)
            public.ExecShell(backup_shell, env={"MYSQL_PWD": db_password})
        else:  # 按表导出
            export_dir = os.path.join(db_backup_dir, file_name)
            if not os.path.isdir(export_dir):
                os.makedirs(export_dir)

            for table_name in table_list:
                tb_backup_path = os.path.join(export_dir, "{table_name}.sql".format(table_name=table_name))
                tb_shell = backup_shell + " '{table_name}' 2> '{err_log}' > '{tb_backup_path}'".format(table_name=table_name, err_log=self._err_log, tb_backup_path=tb_backup_path)
                public.ExecShell(tb_shell, env={"MYSQL_PWD": db_password})
            backup_path = "{export_dir}.zip".format(export_dir=export_dir)
            public.ExecShell("cd '{backup_dir}' && zip -m '{backup_path}' -r '{file_name}'".format(backup_dir=db_backup_dir, backup_path=backup_path, file_name=file_name))
            if not os.path.exists(backup_path):
                public.ExecShell("rm -rf {}".format(export_dir))

        if not os.path.exists(backup_path):
            error_msg = "Database backup failed!!"
            self.echo_error(error_msg)
            self.echo_info(public.readFile(self._err_log))
            return False, error_msg
        # self.echo_info('backup_path:{}'.format(backup_path))
        gz_size = os.path.getsize(backup_path)
        if gz_size < 400:
            error_msg = "Backup file size abnormal, backup failed!"
            self.echo_error(error_msg)
            self.echo_info(public.readFile(self._err_log))
            os.remove(backup_path)
            return False, error_msg
        
        
        self.echo_info("Database backup completed, taking {:.2f} seconds, compressed file size: {}".format(time.time() - stime, public.to_size(gz_size)))
        # self.check_disk_space(gz_size,self._MYSQL_BACKUP_DIR,type=1)        
        return True, backup_path

    # mongodb 备份数据库
    def mongodb_backup_database(self, db_find: dict, args: dict) -> Tuple[bool, str]:
        file_type = db_find.get("file_type", "bson")

        collection_list = args.get("collection_list", [])  # 备份的集合
        field_list = args.get("field_list", [])

        from databaseModel.mongodbModel import panelMongoDB

        db_name = db_find["name"]
        db_host = "127.0.0.1"
        db_user = db_find["username"]
        db_password = db_find["password"]
        conn_data = {}
        if db_find["db_type"] == 0:
            if panelMongoDB.get_config_options("security", "authorization", "disabled") == "enabled":
                if not db_password:
                    error_msg = "MongoDB has enabled security authentication. The database password cannot be empty. Please set the password and try again!"
                    self.echo_error(error_msg)
                    return False, error_msg
            else:
                db_password = None
            db_port = int(panelMongoDB.get_config_options("net", "port", 27017))
        elif db_find["db_type"] == 1:
            if not db_password:
                error_msg = "The database password is empty! Please set the database password first!"
                self.echo_error(error_msg)
                return False, error_msg
            # 远程数据库
            conn_config = json.loads(db_find["conn_config"])
            db_host = conn_config["db_host"]
            db_port = int(conn_config["db_port"])

            conn_data["host"] = conn_config["db_host"]
            conn_data["port"] = conn_config["db_port"]
            conn_data["username"] = conn_config["db_user"]
            conn_data["password"] = conn_config["db_password"]
        elif db_find["db_type"] == 2:
            if not db_password:
                error_msg = "The database password is empty! Please set the database password first!"
                self.echo_error(error_msg)
                return False, error_msg
            conn_config = public.M("database_servers").where("id=? AND LOWER(db_type)=LOWER('mongodb')", db_find["sid"]).find()
            db_host = conn_config["db_host"]
            db_port = int(conn_config["db_port"])

            conn_data["host"] = conn_config["db_host"]
            conn_data["port"] = conn_config["db_port"]
            conn_data["username"] = conn_config["db_user"]
            conn_data["password"] = conn_config["db_password"]
        else:
            error_msg = "Unknown database type!"
            self.echo_error(error_msg)
            return False, error_msg
        mongodb_obj = panelMongoDB().set_host(**conn_data)
        status, err_msg = mongodb_obj.connect()
        if status is False:
            error_msg = "Failed to connect to database [{}: {}]".format(db_host, db_port)
            self.echo_error(error_msg)
            return False, error_msg

        db_collections = 0
        db_storage_size = 0
        try:
            status, db_obj = mongodb_obj.get_db_obj_new(db_name)
            if status is False:
                error_msg = db_obj
                self.echo_error(error_msg)
                return False, error_msg

            data = db_obj.command("dbStats")
            db_collections = data.get("collections", 0)  # 获取集合数
            db_storage_size = data.get("storageSize", 0)  # 获取存储大小
            # if len(collection_list) == 0:
            #     collection_list = db_obj.list_collection_names()
        except:
            error_msg = "Failed to connect to database [{}: {}]".format(db_host, db_port)
            self.echo_error(error_msg)
            return False, error_msg

        if db_collections == 0:
            error_msg = "The specified database '{}' does not have any collections!".format(db_name)
            self.echo_error(error_msg)
            return False, error_msg
        self.echo_info("Backup MongoDB database: {}".format(db_name))
        self.echo_info("Database size: {}".format(public.to_size(db_storage_size)))
        self.echo_info("Number of database collections: {}".format(db_collections))

        disk_path, disk_free, disk_inode = self.get_disk_free(self._MONGODB_BACKUP_DIR)
        self.echo_info("The available disk space for partition {} is: {}, and the available Inode is: {}".format(disk_path, public.to_size(disk_free), disk_inode))
        if disk_path:
            if disk_free < db_storage_size:
                error_msg = "The available disk space of the target partition is less than {}, and the backup cannot be completed. Please increase the disk capacity or change the default backup directory on the settings page!".format(public.to_size(db_storage_size))
                self.echo_error(error_msg)
                return False, error_msg
            if disk_inode < self._inode_min:
                error_msg = "The available Inode for the target partition is less than {}, and the backup cannot be completed. Please increase the disk capacity or change the default backup directory on the settings page!".format(self._inode_min)
                self.echo_error(error_msg)
                return False, error_msg
        stime = time.time()
        self.echo_info("Start exporting database:{}".format(public.format_date(times=stime)))
        mongodb_backup_dir = self.get_backup_dir(db_find, args, "mongodb")
        db_backup_dir = os.path.join(mongodb_backup_dir, db_name)
        if not os.path.exists(db_backup_dir):
            os.makedirs(db_backup_dir)

        file_name = "{db_name}_{file_type}_{backup_time}_mongodb_data".format(db_name=db_find["name"], file_type=file_type, backup_time=time.strftime("%Y-%m-%d_%H-%M-%S", time.localtime()))

        export_dir = os.path.join(db_backup_dir, file_name)

        mongodump_shell = "'{mongodump_bin}' --host='{db_host}' --port={db_port} --db='{db_name}' --out='{out}' 2> '{err_log}'".format(
            mongodump_bin=self._MONGODBDUMP_BIN,
            db_host=db_host,
            db_port=db_port,
            db_name=db_name,
            out=export_dir,
            err_log=self._err_log,
        )
        mongoexport_shell = "'{mongoexport_bin}' --host='{db_host}' --port={db_port} --db='{db_name}' 2> '{err_log}'".format(
            mongoexport_bin=self._MONGOEXPORT_BIN,
            db_host=db_host,
            db_port=db_port,
            db_name=db_name,
            err_log=self._err_log,
        )
        if db_password is not None:  # 本地未开启安全认证
            mongodump_shell += " --username='{db_user}' --password={db_password}".format(db_user=db_user, db_password=public.shell_quote(str(db_password)))
            mongoexport_shell += " --username='{db_user}' --password={db_password}".format(db_user=db_user, db_password=public.shell_quote(str(db_password)))

        if file_type == "bson":
            if len(collection_list) == 0:
                public.ExecShell(mongodump_shell)
            else:
                for collection_name in collection_list:
                    shell = "{mongodump_shell} --collection='{collection}'".format(
                        mongodump_shell=mongodump_shell,
                        collection=collection_name
                    )
                    public.ExecShell(shell)
        else:  # 导出 json csv 格式
            fields = None
            if file_type == "csv":  # csv
                fields = "--fields='{}'".format(",".join(field_list))

            for collection_name in collection_list:

                file_path = os.path.join(export_dir, "{collection_name}.{file_type}".format(collection_name=collection_name, file_type=file_type))
                shell = "{mongoexport_shell} --collection='{collection}' --type='{type}' --out='{out}'".format(
                    mongoexport_shell=mongoexport_shell,
                    collection=collection_name,
                    type=file_type,
                    out=file_path,
                )
                if fields is not None:
                    shell += " --fields='{fields}'".format(fields=fields)
                public.ExecShell(shell)
        backup_path = "{export_dir}.zip".format(export_dir=export_dir)

        public.ExecShell("cd {backup_dir} && zip -m {backup_path} -r  {file_name}".format(backup_dir=db_backup_dir, backup_path=backup_path, file_name=file_name))
        if not os.path.exists(backup_path):
            public.ExecShell("rm -rf {}", format(export_dir))
            error_msg = "Database backup failed!"
            self.echo_error(error_msg)
            self.echo_info(public.readFile(self._err_log))
            return False, error_msg
        zip_size = os.path.getsize(backup_path)
        # self.check_disk_space(zip_size,self._MONGODB_BACKUP_DIR,type=1)
        self.echo_info("Database backup completed, taking {:.2f} seconds, compressed file size: {}".format(time.time() - stime, public.to_size(zip_size)))
        return True, backup_path

    # redis 备份数据库
    def redis_backup_database(self, db_find: dict, args: dict) -> Tuple[bool, str]:

        if db_find["db_type"] != 0:
            error_msg = 'We currently do not support backing up remote databases!'
            self.echo_error(error_msg)
            return False, error_msg

        from databaseModel.redisModel import panelRedisDB
        redis_obj = panelRedisDB()
        redis_config = redis_obj.get_options(None)
        db_num = redis_config.get("databases", 16)
        for db_idx in range(0, int(db_num)):
            if redis_obj.redis_conn(db_idx) is False:
                error_msg = "Failed to connect to local Redis database"
                self.echo_error(error_msg)
                return False, error_msg
            redis_obj.redis_conn(db_idx).save()

        redis_obj_t = redis_obj.redis_conn(0)
        if redis_obj_t is False:
            error_msg = "Failed to connect to local Redis database"
            self.echo_error(error_msg)
            return False, error_msg

        redis_dir = redis_obj_t.config_get().get("dir", "")
        src_path = os.path.join(redis_dir, "dump.rdb")
        if not os.path.exists(src_path):
            error_msg = 'The database file does not exist! {}'.format(src_path)
            self.echo_error(error_msg)
            return False, error_msg

        file_name = "{sid}_{backup_time}_redis_data.rdb".format(sid=db_find["id"], backup_time=time.strftime("%Y-%m-%d_%H-%M-%S", time.localtime()))

        # 调用 get_backup_dir 函数来获取备份目录的路径
        redis_backup_dir = self.get_backup_dir(db_find, args, "redis")

        # 使用获取的路径来构建备份文件的路径
        backup_path = os.path.join(redis_backup_dir, file_name)

        db_size = os.path.getsize(src_path)

        self.echo_info('Backup Redis database')
        self.echo_info("Backup file size: {}".format(public.to_size(db_size)))
        self.echo_info("Backup path: {}".format(src_path))

        disk_path, disk_free, disk_inode = self.get_disk_free(self._REDIS_BACKUP_DIR)
        self.echo_info("The available disk space for partition {} is: {}, and the available Inode is: {}".format(disk_path, public.to_size(disk_free), disk_inode))
        if disk_path:
            if disk_free < db_size:
                error_msg = "The available disk space of the target partition is less than {}, and the backup cannot be completed. Please increase the disk capacity or change the default backup directory on the settings page!".format(public.to_size(db_size))
                self.echo_error(error_msg)
                return False, error_msg
            if disk_inode < self._inode_min:
                error_msg = "The available Inode for the target partition is less than {}, and the backup cannot be completed. Please increase the disk capacity or change the default backup directory on the settings page!".format(self._inode_min)
                self.echo_error(error_msg)
                return False, error_msg
        stime = time.time()
        self.echo_info("Start backing up the database:{}".format(public.format_date(times=stime)))

        import shutil
        shutil.copyfile(src_path, backup_path)
        if not os.path.exists(backup_path):
            error_msg = "Database backup failed!"
            self.echo_error(error_msg)
            self.echo_info(public.readFile(self._err_log))
            return False, error_msg

        backup_size = os.path.getsize(backup_path)
        # self.check_disk_space(backup_size,self._REDIS_BACKUP_DIR,type=1)
        self.echo_info("Database backup completed, taking {:.2f} seconds, file size: {}".format(time.time() - stime, public.to_size(backup_size)))
        return True, backup_path

    # pgsql 备份数据库
    def pgsql_backup_database(self, db_find: dict, args: dict) -> Tuple[bool, str]:
        from databaseModel.pgsqlModel import panelPgsql

        storage_type = args.get("storage_type", "db")  # 备份的文件数量， 按照数据库 | 按照表
        table_list = args.get("table_list", [])  # 备份的集合

        db_name = db_find["name"]
        db_user = "postgres"
        db_host = "127.0.0.1"
        if db_find["db_type"] == 0:
            db_port = panelPgsql.get_config_options("port", int, 5432)

            t_path = os.path.join(public.get_panel_path(), "data/postgresAS.json")
            if not os.path.isfile(t_path):
                error_msg = "Administrator password not set!"
                self.echo_error(error_msg)
                return False, error_msg
            db_password = json.loads(public.readFile(t_path)).get("password", "")
            if not db_password:
                error_msg = "The database password is empty! Please set the database password first!"
                self.echo_error(error_msg)
                return False, error_msg

        elif db_find["db_type"] == 1:
            # 远程数据库
            conn_config = json.loads(db_find["conn_config"])
            db_host = conn_config["db_host"]
            db_port = conn_config["db_port"]
            db_user = conn_config["db_user"]
            db_password = conn_config["db_password"]
        elif db_find["db_type"] == 2:
            conn_config = public.M("database_servers").where("id=? AND LOWER(db_type)=LOWER('pgsql')", db_find["sid"]).find()
            db_host = conn_config["db_host"]
            db_port = conn_config["db_port"]
            db_user = conn_config["db_user"]
            db_password = conn_config["db_password"]
        else:
            error_msg = "Unknown database type"
            self.echo_error(error_msg)
            return False, error_msg

        pgsql_obj = panelPgsql().set_host(host=db_host, port=db_port, database=None, user=db_user, password=db_password)
        status, err_msg = pgsql_obj.connect()
        if status is False:
            error_msg = "Failed to connect to database [{}: {}]".format(db_host, int(db_port))
            self.echo_error(error_msg)
            return False, error_msg

        db_size = 0
        db_data = pgsql_obj.query("SELECT pg_database_size('{}') AS database_size;".format(db_name))
        if isinstance(db_data, list) and len(db_data) != 0:
            db_size = db_data[0][0]

        if db_size == 0:
            error_msg = "The specified database '{}' has no data!".format(db_name)
            self.echo_error(error_msg)
            return False, error_msg
        self.echo_info('Backup PgSQL database: {}'.format(db_name))
        self.echo_info("Database size: {}".format(public.to_size(db_size)))

        disk_path, disk_free, disk_inode = self.get_disk_free(self._PGSQL_BACKUP_DIR)
        self.echo_info("The available disk space for partition {} is: {}, and the available Inode is: {}".format(disk_path, public.to_size(disk_free), disk_inode))
        if disk_path:
            if disk_free < db_size:
                error_msg = "The available disk space of the target partition is less than {}, and the backup cannot be completed. Please increase the disk capacity or change the default backup directory on the settings page!".format(public.to_size(db_size))
                self.echo_error(error_msg)
                return False, error_msg
            if disk_inode < self._inode_min:
                error_msg = "The available Inode for the target partition is less than {}, and the backup cannot be completed. Please increase the disk capacity or change the default backup directory on the settings page!".format(self._inode_min)
                self.echo_error(error_msg)
                return False, error_msg
        stime = time.time()
        self.echo_info("Start exporting database:{}".format(public.format_date(times=stime)))
        # 调用 get_backup_dir 函数来获取备份目录的路径
        pgsql_backup_dir = self.get_backup_dir(db_find, args, "pgsql")
        # 使用获取的路径来构建备份文件的路径
        db_backup_dir = os.path.join(pgsql_backup_dir, db_name)
        if not os.path.exists(db_backup_dir):
            os.makedirs(db_backup_dir)

        file_name = "{db_name}_{backup_time}_pgsql_data".format(db_name=db_name, backup_time=time.strftime("%Y-%m-%d_%H-%M-%S", time.localtime()))

        shell = "'{pgdump_bin}' --host='{db_host}' --port={db_port} --username='{db_user}' --dbname='{db_name}' --clean".format(
            pgdump_bin=self._PGDUMP_BIN,
            db_host=db_host,
            db_port=int(db_port),
            db_user=db_user,
            db_name=db_name,
        )

        if storage_type == "db":  # 导出单个文件
            file_name = file_name + ".sql.gz"
            backup_path = os.path.join(db_backup_dir, file_name)
            table_shell = ""
            if len(table_list) != 0:
                table_shell = "--table='" + "' --table='".join(table_list) + "'"
            shell += " {table_shell} | gzip > '{backup_path}'".format(table_shell=table_shell, backup_path=backup_path)
            public.ExecShell(shell, env={"PGPASSWORD": db_password})
        else:  # 按表导出
            export_dir = os.path.join(db_backup_dir, file_name)
            if not os.path.isdir(export_dir):
                os.makedirs(export_dir)

            for table_name in table_list:
                tb_backup_path = os.path.join(export_dir, "{table_name}.sql".format(table_name=table_name))
                tb_shell = shell + " --table='{table_name}' > '{tb_backup_path}'".format(table_name=table_name, tb_backup_path=tb_backup_path)
                public.ExecShell(tb_shell, env={"PGPASSWORD": db_password})
            backup_path = "{export_dir}.zip".format(export_dir=export_dir)
            public.ExecShell("cd '{backup_dir}' && zip -m '{backup_path}' -r '{file_name}'".format(backup_dir=db_backup_dir, backup_path=backup_path, file_name=file_name))
            if not os.path.exists(backup_path):
                public.ExecShell("rm -rf {}", format(export_dir))

        # public.ExecShell(shell, env={"PGPASSWORD": db_password})
        if not os.path.exists(backup_path):
            error_msg = "Database backup failed!"
            self.echo_error(error_msg)
            self.echo_info(public.readFile(self._err_log))
            return False, error_msg
        gz_size = os.path.getsize(backup_path)
        # self.check_disk_space(gz_size,self._PGSQL_BACKUP_DIR,type=1)
        self.echo_info("Database backup completed, taking {:.2f} seconds, compressed file size: {}".format(time.time() - stime, public.to_size(gz_size)))
        return True, backup_path

    def generate_success_title(self, task_name):
        from send_mail import send_mail
        sm = send_mail()
        now = public.format_date(format="%Y-%m-%d %H:%M")
        server_ip = sm.GetLocalIp()
        title = "{}-{} Task execution successful".format(server_ip, task_name)
        return title

    def generate_failture_title(self, task_name):
        title = "aapanel Plan Task Backup Failure Reminder".format(task_name)
        return title

    def generate_all_failture_notice(self, task_name, msg, backup_type, remark=""):
        from send_mail import send_mail
        sm = send_mail()
        now = public.format_date(format="%Y-%m-%d %H:%M:%S")
        server_ip = sm.GetLocalIp()
        if remark:
            remark = "\n* Task note: {}".format(remark)

        notice_content = """####Planned task execution failed:
* Server IP: {}
* time: {}
* Plan task name:{}{}
* The following is a list of {} backup failures：{}
Please handle it as soon as possible""".format(
            server_ip, now, task_name, remark, backup_type, msg)
        return notice_content

    def generate_failture_notice(self, task_name, msg, remark):
        from send_mail import send_mail
        sm = send_mail()
        now = public.format_date(format="%Y-%m-%d %H:%M:%S")
        server_ip = sm.GetLocalIp()
        if remark:
            remark = "\n* Task note: {}".format(remark)

        notice_content = """####Planned task execution failed:
* Server IP: {}
* time: {}
* Plan task name:{}{}
* Error message:
{}
Please handle it as soon as possible""".format(
            server_ip, now, task_name, remark, msg)
        return notice_content
        
    def generate_disk_notice(self, task_name,free_space_gb,remark=""):
        from send_mail import send_mail
        sm = send_mail()
        now = public.format_date(format="%Y-%m-%d %H:%M:%S")
        server_ip = sm.GetLocalIp()
        if remark:
            remark = "\n* Task note: {}".format(remark)

        notice_content = """####Warm reminder for backup files of planned tasks:
    * Server IP: {}
    * time: {}
    * Plan task name: {}{}
    * reminder:
    We have detected that your server's disk space is insufficient {} G, which may cause subsequent backup file failures. Please clean up the disk as soon as possible!
    """.format(
            server_ip, now, task_name, remark,free_space_gb)
        return notice_content
    
    def get_cron_info(self, cron_name):
        """ 通过计划任务名称查找计划任务配置参数 """
        try:
            cron_info = public.M('crontab').where('echo=?', (cron_name,)) \
                .field('name,save_local,notice,notice_channel,id,sType').find()
            return cron_info
        except Exception as e:
            pass
        return {}

    def send_success_notification(self, msg, target="", remark=""):
        pass
    

    def send_disk_notification(self,free_space_gb,remark=""):
        """发送任务失败消息

        :error_msg 错误信息
        :remark 备注
        """
        if not self.cron_info:
            return
        cron_info = self.cron_info
        cron_title = cron_info["name"]
        notice = cron_info["notice"]
        notice_channel = cron_info["notice_channel"]
        if notice == 0 or not notice_channel:
            return

        if notice == 1 or notice == 2:
            title = self.generate_failture_title(cron_title)
            task_name = cron_title               
            msg=self.generate_disk_notice(task_name,free_space_gb,remark)
            res = self.send_notification(notice_channel, title, msg)
            if res:
                self.echo_info("The message notification has been sent.")

    def send_failture_notification(self, error_msg, target="", remark=""):
        """发送任务失败消息

        :error_msg 错误信息
        :remark 备注
        """
        if self._backup_all:
            return
        if not self.cron_info:
            return
        cron_info = self.cron_info
        cron_title = cron_info["name"]
        save_local = cron_info["save_local"]
        notice = cron_info["notice"]
        notice_channel = cron_info["notice_channel"]
        self.save_backup_status(False, target, msg=error_msg)
        if notice == 0 or not notice_channel:
            return

        if notice == 1 or notice == 2:
            title = self.generate_failture_title(cron_title)
            task_name = cron_title
            msg = self.generate_failture_notice(task_name, error_msg, remark)
            res = self.send_notification(notice_channel, title, msg)
            if res:
                self.echo_info("The message notification has been sent.")

    def send_all_failture_notification(self, backup_type, results, remark=""):
        """统一发送任务失败消息

        :results [(备份对象， 备份结果，错误信息),...]
        :remark 备注
        """
        if not self.cron_info:
            return
        cron_info = self.cron_info
        cron_title = cron_info["name"]
        save_local = cron_info["save_local"]
        notice = cron_info["notice"]
        notice_channel = cron_info["notice_channel"]
        if notice == 0 or not notice_channel:
            return

        if notice == 1 or notice == 2:
            title = self.generate_failture_title(cron_title)
            type_desc = {
                "site": "site",
                "database": "database"
            }
            backup_type_desc = type_desc[backup_type]
            task_name = cron_title
            failture_count = 0
            total = 0
            content = ""

            for obj in results:
                total += 1
                obj_name = obj[0]
                result = obj[1]
                if not result:
                    failture_count += 1
                    # content += "<tr><td style='color:red'>{}</td><tr>".format(obj_name)
                    content += "\n{}".format(obj_name)

            if failture_count > 0:
                if self._cloud:
                    remark = "Backup to {}, total {} {}, failed {}.".format(
                        self._cloud._title, total, backup_type_desc, failture_count)
                else:
                    remark = "Backup failed for {}/total of {} sites".format(
                        failture_count, total, backup_type_desc)

            msg = self.generate_all_failture_notice(task_name, content, backup_type_desc, remark)
            res = self.send_notification(notice_channel, title, msg=msg, total=total, failture_count=failture_count)
            if res:
                self.echo_info("The message notification has been sent.")
            else:
                self.echo_error("Message notification sending failed.")

    def send_notification(self, channel, title, msg="", total=0, failture_count=0,cron_info=None):
        """发送通知

        Args:
            channel (str): 消息通道，多个用英文逗号隔开
            title (str): 通知标题
            msg (str, optional): 消息内容. Defaults to "".

        Returns:
            bool: 通知是否发送成功
        """
        try:
            from config import config
            from panelPush import panelPush
            tongdao = []
            if channel.find(",") >= 0:
                tongdao = channel.split(",")
            else:
                tongdao = [channel]

            error_count = 0
            con_obj = config()
            get = public.dict_obj()
            msg_channels = con_obj.get_msg_configs(get)

            error_channel = []
            channel_data = {}
            msg_data = {}
            for ch in tongdao:
                # 根据不同的消息通道准备不同的内容
                if ch == "mail":
                    msg_data = {
                        "msg": msg.replace("\n", "<br/>"),
                        "title": title
                    }
                if ch in ["dingding", "weixin", "feishu", "wx_account", "tg"]:
                    msg_data["msg"] = msg
                    # print("msg",msg_data["msg"])
                if ch in ["sms"]:
                    if not cron_info:
                       task_name=self.cron_info["name"]
                    else:
                       task_name=cron_info["name"]
                    if total > 0 and failture_count > 0:
                        msg_data["sm_type"] = "backup_all"
                        msg_data["sm_args"] = {
                            "panel_name": public.GetConfigValue('title'),
                            "task_name": task_name,
                            "failed_count": failture_count,
                            "total": total
                        }
                    else:
                        msg_data["sm_type"] = "backup"
                        msg_data["sm_args"] = {
                            "panel_name": public.GetConfigValue('title'),
                            "task_name": task_name
                        }
                channel_data[ch] = msg_data
            # print("channel data:")
            # print(channel_data)
            # 即时推送
            pp = panelPush()

            push_res = pp.push_message_immediately(channel_data)
            if push_res["status"]:
                channel_res = push_res["msg"]
                for ch, res in channel_res.items():
                    if not res["status"]:
                        if ch in msg_channels:
                            error_channel.append(msg_channels[ch]["title"])
                            error_count += 1
            if not push_res["status"] or error_count:
                self.echo_error("Message channel: {} failed to send!".format(",".join(error_channel)))
            else:
                self.echo_info("Message sent successfully.")
            if error_count == len(tongdao):
                return False
            return True
        except Exception as e:
            import traceback
            print(traceback.format_exc())
        return False

    def send_notification2(self, channel, title, msg=""):
        try:
            from send_mail import send_mail
            tongdao = []
            if channel.find(",") >= 0:
                tongdao = channel.split(",")
            else:
                tongdao = [channel]

            sm = send_mail()
            send_res = []
            error_count = 0
            channel_names = {
                "mail": "mail",
                "dingidng": "dingidng"
            }
            error_channel = []
            settings = sm.get_settings()
            for td in tongdao:
                _res = False
                if td == "mail":
                    if len(settings["user_mail"]['mail_list']) == 0:
                        continue
                    mail_list = settings['user_mail']['mail_list']
                    if len(mail_list) == 1:
                        mail_list = mail_list[0]
                    _res = sm.qq_smtp_send(mail_list, title=title, body=msg.replace("\n", "<br/>"))
                    if not _res:
                        error_count += 1
                        error_channel.append(channel_names[td])
                if td == "dingding":
                    if len(settings["dingding"]['info']) == 0:
                        continue
                    _res = sm.dingding_send(msg)
                    send_res.append(_res)
                    if not _res:
                        error_count += 1
                        error_channel.append(channel_names[td])
            if error_count > 0:
                print("Message channel: {} failed to send!".format(",".join(error_channel)))
            if error_count == len(tongdao):
                return False
            return True
        except Exception as e:
            print(e)
        return False

    def save_backup_status(self, status, target="", msg=""):
        """保存备份的状态"""
        try:
            if not self.cron_info:
                return
            cron_id = self.cron_info["id"]
            sql = public.M("system").dbfile("system").table("backup_status")
            sql.add("id,target,status,msg,addtime", (cron_id, target, status, msg, time.time(),))
        except Exception as e:
            print("Save backup status exception: {}.".format(e))

    # 切割文件上传
    def split_upload_file(self, backup_path: str, upload_path: str) -> Tuple[bool, str]:
        is_status = True
        data = ""
        self.echo_info("File splitting in progress, please wait...")
        if self._cloud is None or self._cloud_new is None:
            return False, "No cloud storage specified!"

        if self.cron_info.get("split_type") == "size":
            is_status, data = self.split_file(
                file_path=backup_path,
                split_size=self.cron_info.get("split_value"),
            )
        elif self.cron_info.get("split_type") == "num":
            is_status, data = self.split_file(
                file_path=backup_path,
                split_num=self.cron_info.get("split_value"),
            )
        if is_status is False:
            return False, data

        save_dir = data["save_dir"]
        upload_dir = os.path.join(self._cloud_new.backup_path, upload_path, os.path.basename(save_dir))
        self.echo_info("File splitting is in progress. The size of each individual file after splitting is {} M, and the number of files after splitting is {}".format(data.get("split_size"), data.get("split_num")))
        join_msg = """Split file recovery method:
1. Download cloud storage directory: {upload_dir} On the panel
2. Enter the directory and click on 'File Merge'""".format(
            upload_dir=upload_dir
        )
        self.echo_info(join_msg)

        # upload_path = os.path.join(upload_path, os.path.basename(save_dir))
        for name in os.listdir(save_dir):
            path = os.path.join(save_dir, name)
            if not os.path.isfile(path):
                continue

            upload_path_temp = os.path.join(upload_dir, name)
            if not self._cloud_new.cloud_upload_file(path, upload_path_temp):
                public.ExecShell("chattr -i -R {split_dir}".format(split_dir=save_dir))
                public.ExecShell("rm -rf {}".format(save_dir))
                error_msg = "Backup task execution failed."
                if hasattr(self._cloud, "error_msg"):
                    if self._cloud.error_msg:
                        error_msg = self._cloud.error_msg
                self.echo_error(error_msg)
                if os.path.exists(backup_path):
                    os.remove(backup_path)
                return False, error_msg

        self.echo_info("Successfully uploaded to {}".format(self._cloud._title))
        public.ExecShell("chattr -i -R {split_dir}".format(split_dir=save_dir))
        public.ExecShell("rm -rf {}".format(save_dir))
        return True, upload_dir
    
    def split_file(self,
                   file_path: str,  # 文件路径
                   split_size: int = None,  # 切割大小 MB
                   split_num: int = None,  # 切割数量
                   split_file_name: str = None,  # 切割文件名，默认为切割目标文件名
                   split_file_ext: str = None,  # 切割文件后缀
                   save_path: str = None,  # 切割后保存的路径
                   ) -> Tuple[bool, Union[str, dict]]:
        import math
        if not os.path.isfile(file_path):
            return False, "The file does not exist!"
        totoal_size = os.path.getsize(file_path)
        split_file_option = ""
        totoal_split_size = math.ceil(totoal_size / 1024 / 1024)
        if split_size:  # 默认使用大小
            split_file_option = "--bytes={}M".format(split_size)
            split_num = math.ceil(totoal_split_size / split_size)
        elif split_num:  # 按照数量拆分
            split_file_option = "--number={}".format(split_num)
            split_size = round(totoal_split_size / split_num)
        else:  # 默认按照大小拆分 100M
            split_size = 100
            split_file_option = "--bytes={}M".format(split_size)
            split_num = math.ceil(totoal_split_size / split_size)

        if split_num < 2:
            return False, "The minimum number of file splits is 2!"

        file_name = os.path.basename(file_path)

        if not save_path:  # 保存路径
            save_path = os.path.dirname(file_path)

        save_dir_name = "{file_name}_split".format(file_name=file_name)
        save_dir = os.path.join(save_path, save_dir_name)
        i = 1
        while os.path.isdir(save_dir):
            save_dir_name = "{file_name}_split-({ectype})".format(file_name=file_name, ectype=i)
            save_dir = os.path.join(save_path, save_dir_name)
            i += 1

        os.makedirs(save_dir)

        if not split_file_name:  # 切割文件名，默认为切割目标文件名
            file_ext_temp = file_name.split(".")
            if len(file_ext_temp) != 0:
                split_file_name = "{file_name}_sqlit_".format(file_name=".".join(file_ext_temp[:-1]))
            else:
                split_file_name = "{file_name}_sqlit_".format(file_name=file_name)

        if not split_file_ext:
            split_file_ext = ".bt_split"
        split_file_shell = "--additional-suffix={split_file_ext}".format(split_file_ext=split_file_ext)

        shell = "cd '{save_dir}' && split {split_file_option} --numeric-suffixes=1 --suffix-length={split_length} {split_file_shell} '{file_path}' {split_file_name}".format(
            save_dir=save_dir,
            split_file_option=split_file_option,
            split_length=len(str(split_num)),
            file_path=file_path,
            split_file_name=split_file_name,
            split_file_shell=split_file_shell,
        )
        public.ExecShell(shell)

        split_file_list = []
        for name in os.listdir(save_dir):
            path = os.path.join(save_dir, name)
            if not os.path.isfile(path):
                continue
            split_file_list.append(name)

        split_config_info = {
            "name": file_name,
            "size": totoal_size,
            "split_size": split_size,
            "split_num": split_num,
            "md5": public.FileMd5(file_path),
            "split_file": split_file_list,
            "save_dir": save_dir,
        }
        split_config_path = os.path.join(save_dir, "split_config.bt_split_json")
        public.writeFile(split_config_path, json.dumps(split_config_info))

        public.ExecShell("chattr +i -R {split_dir}".format(split_dir=save_dir))
        return True, split_config_info
    
    def get_backup_dir(self, db_find: dict, args: dict, db_type: str) -> str:
        backup_dir = args.get("db_backup_path", "")
        save_local = args.get("save_local", "")
        if db_find["db_type"] == 0 or save_local == 1:  # 本地数据库

            if backup_dir:
                db_backup_dir = os.path.join(backup_dir, "database")
                specific_db_backup_dir = os.path.join(db_backup_dir, db_type, "crontab_backup")
            else:
                specific_db_backup_dir = os.path.join(self._DB_BACKUP_DIR, db_type, "crontab_backup")
        else:
            specific_db_backup_dir = os.path.join(self._DB_BACKUP_DIR, db_type, "crontab_backup")

        return specific_db_backup_dir

    # def get_site_backup_dir(self, backupto: str, save_local: int, db_backup_path: str, site_name: str) -> str:
    def get_site_backup_dir(self, backupto: str,  db_backup_path: str, site_name: str) -> str:
        site_backup_dir = self._BACKUP_DIR  # 给 site_backup_dir 一个默认值
        if backupto == "localhost":
            if db_backup_path:
                site_backup_dir = db_backup_path

        return site_backup_dir
    
    def check_disk_space(self,file_size,backup_dir):
        min_required_space = max(file_size* 5,  1* 1024 * 1024 * 1024)  # 1GB
        disk_usage = public.get_disk_usage(backup_dir)
        if disk_usage.free < min_required_space:
            free_space_gb = int(min_required_space / (1024 * 1024 * 1024))
            self.send_disk_notification(free_space_gb)

    def check_databases(self):
        """检查数据表是否存在"""
        tables = ["backup_status"]
        import sqlite3
        conn = sqlite3.connect("/www/server/panel/data/system.db")
        cur = conn.cursor()
        table_key = ",".join(["'"+t+"'" for t in tables])
        sel_res = cur.execute("SELECT name FROM sqlite_master WHERE type='table' and name in ({})".format(table_key))
        res = sel_res.fetchall()
        to_commit = False
        exists_dbs = []
        if res:
            exists_dbs = [d[0] for d in res]

        if "backup_status" not in exists_dbs:
            csql = '''CREATE TABLE IF NOT EXISTS `backup_status` (
                    `id` INTEGER,
                    `target` TEXT,
                    `status` INTEGER,
                    `msg` TEXT DEFAULT "",
                    `addtime` DATETIME DEFAULT CURRENT_TIMESTAMP
                )'''
            cur.execute(csql)
            to_commit = True

        if to_commit:
            conn.commit()
        cur.close()
        conn.close()
        return True
