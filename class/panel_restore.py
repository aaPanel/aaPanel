# coding: utf-8
# -------------------------------------------------------------------
# 宝塔Linux面板
# -------------------------------------------------------------------
# Copyright (c) 2015-2099 宝塔软件(http:#bt.cn) All rights reserved.
# -------------------------------------------------------------------
# Author: zhwwen <zhw@bt.cn>
# -------------------------------------------------------------------
#
# ------------------------------
# 网站恢复
# ------------------------------
import public,os,files,sys
from time import sleep
class panel_restore:

    _local_file = '/tmp/{}'
    _progress_file = '/tmp/restore_site.log'

    # def __init__(self):
    #     # 清空日志文件

    def _progress_rewrite(self,content,mothed='a+'):
        sleep(2)
        public.writeFile(self._progress_file,content+'\n',mothed)

    def _get_local_backup_path(self):
        local_backdir = public.M('config').field('backup_path').find()['backup_path']
        return local_backdir

    def _build_aws_backup_path(self,btype,file_name,domain):
        config_file = "/www/server/panel/plugin/aws_s3/config.conf"
        conf = public.readFile(config_file)
        backup_path = conf.split('|')[-1].strip()+btype+'/'+ domain + '/' + file_name
        return backup_path

    def _build_google_backup_path(self,btype,file_name,domain):
        object_name = 'bt_backup/{}/{}/{}'.format(btype,domain,file_name)
        return object_name

    def _get_backfile_method(self,filename):
        backup_info = public.M('backup').where("name=?", (filename,)).getField('filename')
        backup_info = backup_info.split('|')
        if len(backup_info) >= 3:
            method = backup_info[1]
        else:
            method = 'local'
        return method

    def _remove_old_website_file_to_trush(self,args):
        # 将原来目录移至回收站
        files.files().DeleteDir(args)

    def _get_website_info(self,site_id):
        site_name = public.M('sites').where("id=?",(site_id,)).getField('name')
        site_path = public.M('sites').where("id=?",(site_id,)).getField('path')
        return {'site_name':site_name,'site_path':site_path}

    def _restore_backup(self,local_backup_file_path,site_info,args):
        # 判断备份文件是否存在，如果不存在继续检查是否远程备份
        if not os.path.exists(local_backup_file_path):
            self._progress_rewrite('No backup file found: {}'.format(str(local_backup_file_path)))
            return public.returnMsg(False, 'Panel does not find the backup file: {}'.format(local_backup_file_path))
        # 将网站目录移至回收站
        self._progress_rewrite('Move the current website directory to the recycle bin: {}'.format(str(args.path)))
        self._remove_old_website_file_to_trush(args)
        if not os.path.exists(args.path):
            self._progress_rewrite('Create an empty directory for the site: {}'.format(str(args.path)))
            os.makedirs(site_info['site_path'])
        if 'zip' in args.file_name:
            uncompress_comand = 'unzip'
        else:
            uncompress_comand = 'tar -zxvf'
        self._progress_rewrite('The decompression command is: {}'.format(str(uncompress_comand)))
        self._progress_rewrite('Start to restore data......')
        public.ExecShell('cd {} && {} {} >> /tmp/restore_site.log'.format(site_info['site_path'], uncompress_comand, local_backup_file_path))
        if len(os.listdir(site_info['site_path'])) == 2:
            public.ExecShell('cd {s} && mv {s}/{d}/* .'.format(s=site_info['site_path'],d=site_info['site_name']))
            public.ExecShell('cd {s} && rmdir {d}'.format(s=site_info['site_path'],d=site_info['site_name']))
        # 将文件全新设置为644，文件夹设置为755
        self._progress_rewrite('Setting site permissions......')
        files.files().fix_permissions(args)

    def _download_aws_file(self,args,btype='site'):
        sys.path.append('/www/server/panel/plugin/aws_s3')
        import aws_s3_main
        aws3 = aws_s3_main.aws_s3_main()
        self._progress_rewrite('Building S3 download path...')
        download_file = self._build_aws_backup_path(btype,args.file_name,args.obj_name)
        self._progress_rewrite('The download path is:{}'.format(download_file))
        self._local_file = self._local_file.format(args.file_name)
        self._progress_rewrite('Backup file will be downloaded to:{}'.format(self._local_file))
        self._progress_rewrite('Starting to download file:{}'.format(self._local_file))
        args.object_name = download_file
        args.local_file = self._local_file
        aws3.download_file(args)
        self._progress_rewrite('Download completed:{}'.format(self._local_file))
        return self._local_file

    def _download_google_cloud_file(self,args,btype='site'):
        sys.path.append('/www/server/panel/plugin/gcloud_storage')
        import gcloud_storage_main
        gs = gcloud_storage_main.gcloud_storage_main()
        self._progress_rewrite('Building Google Store download path...')
        download_file = self._build_google_backup_path(btype,args.file_name,args.obj_name)
        self._progress_rewrite('The download path is:{}'.format(download_file))
        self._local_file = self._local_file.format(args.file_name)
        self._progress_rewrite('Backup file will be downloaded to:{}'.format(self._local_file))
        self._progress_rewrite('Starting to download file:{}'.format(self._local_file))
        args.source_blob_name = download_file
        args.destination_file_name = self._local_file
        gs.download_blob(args)
        self._progress_rewrite('Download completed:{}'.format(self._local_file))
        return self._local_file

    def _download_google_drive_file(self,args):
        sys.path.append('/www/server/panel/plugin/gdrive')
        import gdrive_main
        gd = gdrive_main.gdrive_main()
        self._local_file = self._local_file.format(args.file_name)
        self._progress_rewrite('Backup file will be downloaded to:{}'.format(self._local_file))
        self._progress_rewrite('Starting to download file:{}'.format(self._local_file))
        gd.download_file(args.file_name)
        self._progress_rewrite('Download completed:{}'.format(self._local_file))
        return self._local_file

    def restore_website_backup(self,args):
        """
            @name 恢复站点文件
            @author zhwen<zhw@bt.cn>
            @parma file_name 备份得文件名
            @parma site_id 网站id
        """
        self._progress_rewrite('','w')
        site_info = self._get_website_info(args.site_id)
        self._progress_rewrite('Get site information:{}'.format(str(site_info)))
        args.path = site_info['site_path']
        args.obj_name = site_info['site_name']
        self._progress_rewrite('Get the site path:{}'.format(str(site_info['site_path'])))
        local_backup_path = self._get_local_backup_path()
        local_backup_file_path = local_backup_path +'/site/'+ args.file_name
        self._progress_rewrite('Get the local backup file path: {}'.format(str(local_backup_path)))
        backup_method = self._get_backfile_method(args.file_name)
        self._progress_rewrite('Get the backup method: {}'.format(str(backup_method)))
        if backup_method == 'local':
            self._progress_rewrite('Start to restore local backup files: {}'.format(str(local_backup_file_path)))
            result = self._restore_backup(local_backup_file_path,site_info,args)
            if result:
                self._progress_rewrite('Recovery failed: {}'.format(str(site_info['site_path'])))
                return result
        elif backup_method == 'aws_s3':
            self._download_aws_file(args)
            result = self._restore_backup(self._local_file, site_info, args)
        elif backup_method == 'Google Cloud':
            self._download_google_cloud_file(args)
            result = self._restore_backup(self._local_file, site_info, args)
        elif backup_method == 'Google Drive':
            self._download_google_drive_file(args)
            result = self._restore_backup(self._local_file, site_info, args)
        else:
            return public.ExecShell(False,'Currently only supports restoring local, Google storage and AWS S3 backups')
        if os.path.exists(self._local_file):
            os.remove(self._local_file)
        if result:
            self._progress_rewrite('Recovery failed: {}'.format(str(site_info['site_path'])))
            return result
        self._progress_rewrite('Successful recovery: {}'.format(str(site_info['site_path'])))
        return public.returnMsg(True,'Restore Successful')

    # 取任务进度
    def get_progress(self, get):
        """
            @name 获取进度日志
            @author zhwen<zhw@bt.cn>
        """
        # result = public.GetNumLines(self._progress_file, 20)
        result = public.ExecShell('tail -n 20 {}'.format(self._progress_file))[0]
        if len(result) < 1:
            return {'msg':"Wait for the restore to start"}
        return {'msg':result}

    # 恢复数据库
    def restore_db_backup(self,args):
        """
            @name 恢复站点文件
            @author zhwen<zhw@bt.cn>
            @parma file_name 备份得文件名 /www/backup/database/db_test_com_20200817_112722.sql.gz|Google Drive|db_test_com_20200817_112722.sql.gz
            @parma obj_name 数据库名
        """
        try:
            backup_info = args.file.split('|')
            args.file_name = backup_info[-1]
            args.obj_name = args.name
            backup_method = backup_info[1]
            self._progress_rewrite('','w')
            self._progress_rewrite('Restoring database...')
            self._progress_rewrite('Get the backup method: {}'.format(str(backup_method)))
            if backup_method == 'aws_s3':
                self._download_aws_file(args,'database')
            elif backup_method == 'Google Cloud':
                self._download_google_cloud_file(args,'database')
            elif backup_method == 'Google Drive':
                self._download_google_drive_file(args)
            else:
                return public.ExecShell(False,'Currently only supports restoring local, Google storage and AWS S3 backups')
            public.ExecShell('mv {} {}/database'.format(self._local_file, self._get_local_backup_path()))
        except:
            return False
