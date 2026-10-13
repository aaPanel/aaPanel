# coding: utf-8
# -------------------------------------------------------------------
# aaPanel
# -------------------------------------------------------------------
# Copyright (c) 2015-2099 aaPanel(www.aapanel.com) All rights reserved.
# -------------------------------------------------------------------
# Author: zhwwen <zhw@aapanel.com>
# -------------------------------------------------------------------
#
# ------------------------------
# 网站恢复
# ------------------------------
import public,os,files,sys, json, shlex, shutil, time, ftplib
from time import sleep
from public.validate import Param
class panel_restore:

    _local_file = '/tmp/{}'
    _progress_file = '/tmp/restore_site.log'
    _setup_path = '/www/server'

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
        backup_path = conf.split('|')[-2].strip()+'/'+btype+'/'+ domain + '/' + file_name
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

    def _restore_backup(self, local_backup_file_path, site_info, args):

        # 判断备份文件是否存在，如果不存在继续检查是否远程备份
        if not os.path.exists(local_backup_file_path):
            self._progress_rewrite('No backup file found: {}'.format(str(local_backup_file_path)))
            return public.return_message(-1, 0, public.lang("Panel does not find the backup file: {}",local_backup_file_path))

        # 区分全量备份与文件备份
        bak_type = public.M('backup').where("name=? and pid=?", (args.file_name,args.site_id)).getField('backup_type')
        if bak_type and bak_type== 1:
            self._progress_rewrite('Detected full backup archive, switching to full restore mode...')
            return self._restore_full_backup(local_backup_file_path, site_info, args)

        # 网站根目录为软链接时，保留软链接并将文件恢复到实际目录
        if os.path.islink(args.path):
            args.path = os.path.realpath(args.path)
            site_info['site_path'] = args.path

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
            public.ExecShell('cd {s} && mv {s}/{d}/{{*,.*}} .'.format(s=site_info['site_path'],d=site_info['site_name']))
            public.ExecShell('cd {s} && rmdir {d}'.format(s=site_info['site_path'],d=site_info['site_name']))
        # 将文件全新设置为644，文件夹设置为755
        self._progress_rewrite('Setting site permissions......')
        files.files().fix_permissions(args)
        public.write_log_gettext('Site manager', f'Successfully restored the website [{site_info['site_name']}], Restored file: [{local_backup_file_path}]')

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
        if download_file[0] != '/':
            download_file = '/' + download_file
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

    def _download_ftp_file(self, args, btype='site'):
        sys.path.append('/www/server/panel/plugin/ftp')
        import ftp_main
        ftp = ftp_main.ftp_main()
        self._progress_rewrite('Building FTP download path...')

        # 从备份表获取上传时存储的真实对象路径
        file_path = ''
        if btype == 'site':
            file_path = public.M('backup').where("name=?",(args.file_name,)).getField('filename')
        else:
            file_path = public.M('backup').where("name=?",(args.file_name,)).getField('filename')

        if not file_path:
            return public.return_message(-1,0,public.lang('No file found!'))

        file_list = file_path.split('|')
        object_name = file_list[-1]

        self._progress_rewrite('The download path is:{}'.format(object_name))
        self._local_file = self._local_file.format(args.file_name)
        self._progress_rewrite('Backup file will be downloaded to:{}'.format(self._local_file))
        self._progress_rewrite('Starting to download file:{}'.format(self._local_file))

        config = ftp.client.get_config()
        host_port = config.get('ftp_host', '')
        if ':' in host_port:
            host, port = host_port.split(':', 1)
        else:
            host, port = host_port, '21'
        user = config.get('ftp_user', '')
        passwd = config.get('ftp_pass', '')

        ftp_conn = ftplib.FTP()
        try:
            ftp_conn.connect(host, int(port))
            ftp_conn.login(user, passwd)
            ftp_conn.voidcmd('TYPE I')
            remote_dir = '/'.join(object_name.split('/')[:-1])
            remote_file = object_name.split('/')[-1]
            if remote_dir:
                ftp_conn.cwd(remote_dir)
            with open(self._local_file, 'wb') as f:
                ftp_conn.retrbinary('RETR ' + remote_file, f.write)
        except:
            return public.return_message(-1,0,public.lang('There was an error during the download of the backup package. Please check if the backup exists!'))

        finally:
            try:
                ftp_conn.quit()
            except Exception:
                pass

        self._progress_rewrite('Download completed:{}'.format(self._local_file))
        return self._local_file

    def restore_website_backup(self,args):
        """
            @name 恢复站点文件
            @author zhwen<zhw@aapanel.com>
            @parma file_name 备份得文件名
            @parma site_id 网站id
        """
         # 校验参数
        try:
            args.validate([
                Param('file_name').String(),
                Param('site_id').Integer(),

            ], [
                public.validate.trim_filter(),
            ])
        except Exception as ex:
            public.print_log("error info: {}".format(ex))
            return public.return_message(-1, 0, str(ex))

        self._progress_rewrite('','w')
        site_info = self._get_website_info(args.site_id)
        self._progress_rewrite('Get site information:{}'.format(str(site_info)))
        args.path = site_info['site_path']
        args.obj_name = site_info['site_name']
        self._progress_rewrite('Get the site path:{}'.format(str(site_info['site_path'])))
        local_backup_path = self._get_local_backup_path()
        local_backup_file_path = local_backup_path +'/site/'+ args.file_name
        if not os.path.exists(local_backup_file_path):
            local_backup_file_path = local_backup_path +'/site/'+ site_info['site_name']+'/'+args.file_name
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
        elif backup_method == 'Google Cloud' or backup_method == 'gcloud_storage':
            self._download_google_cloud_file(args)
            result = self._restore_backup(self._local_file, site_info, args)
        elif backup_method == 'Google Drive' or backup_method == 'gdrive':
            self._download_google_drive_file(args)
            result = self._restore_backup(self._local_file, site_info, args)
        elif backup_method == 'ftp':
            self._download_ftp_file(args)
            result = self._restore_backup(self._local_file, site_info, args)
        else:
            return public.return_msg_gettext(False,'Currently only supports restoring local, Google storage, S3 Storage and FTP backups')
        if os.path.exists(self._local_file):
            os.remove(self._local_file)
        if result:
            self._progress_rewrite('Recovery failed: {}'.format(str(site_info['site_path'])))
            return result
        self._progress_rewrite('Successful recovery: {}'.format(str(site_info['site_path'])))
        return public.return_message(0, 0, public.lang("Restore Successful"))

    # 取任务进度
    def get_progress(self, get):
        """
            @name 获取进度日志
            @author zhwen<zhw@aapanel.com>
        """
        # result = public.GetNumLines(self._progress_file, 20)
        result = public.ExecShell('tail -n 20 {}'.format(self._progress_file))[0]
        if len(result) < 1:
            return public.return_message(0, 0, public.lang("Wait for the restore to start"))
        return public.return_message(0,0,result)

    # 恢复数据库
    def restore_db_backup(self,args):
        """
            @name 恢复站点文件
            @author zhwen<zhw@aapanel.com>
            @parma file_name 备份得文件名 /www/backup/database/db_test_com_20200817_112722.sql.gz|Google Drive|db_test_com_20200817_112722.sql.gz
            @parma obj_name 数据库名
        """
        if "|" not in args.file:
            return public.returnMsg(True,'success')
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
            elif backup_method == 'ftp':
                self._download_ftp_file(args,'database')
            else:
                return public.returnMsg(False,'Currently only supports restoring local, Google storage, S3 Storage and FTP backups')
            public.ExecShell('mv {} {}/database'.format(self._local_file, self._get_local_backup_path()))
            return public.returnMsg(True,'success')
        except:
            return public.returnMsg(False,"Download error!")

    # ====================== PHP站点全量还原 ====================== #
    def _restore_full_backup(self, local_backup_file_path: str, site_info: dict,
                             args, tmp_path: str = None) -> dict:
        """PHP全量备份还原主逻辑
        解压 → meta.json → 文件 → 配置 → 数据库 → PHP版本 → 域名
        @return: dict {site_name, site_id, site_path}
        """
        tmp_path = f"/tmp/{str(time.time()).replace('.', '_')}"
        os.makedirs(tmp_path)

        try:
            # 0. 初始化
            try:
                restore_type = json.loads(args.get('restore_type', []))
            except:
                restore_type = []

            if not restore_type:
                raise FileNotFoundError(public.lang('Error in the "restore_type" parameter transmission.'))

            # 1. 解压备份文件到临时目录
            self._progress_rewrite('Extracting full backup archive to temp directory...')
            extract_cmd = 'tar -zxf "{}" -C "{}"'.format(local_backup_file_path, tmp_path)
            public.ExecShell(extract_cmd)
            public.ExecShell('chown -R www:www "{}"'.format(tmp_path))
            public.ExecShell('chmod -R 755 "{}"'.format(tmp_path))

            # 2. 读取 meta.json
            meta_file = os.path.join(tmp_path, 'meta.json')
            if not os.path.exists(meta_file):
                raise FileNotFoundError(public.lang('meta.json not found in backup archive'))

            with open(meta_file, 'r', encoding='utf-8') as fp:
                meta = json.load(fp)

            site_name = meta.get('site_name', '')
            site_path = meta.get('site_path', '')
            php_version = meta.get('php_version', '')
            has_database = meta.get('has_database', False)
            db_name = meta.get('db_name', '')
            domain_list = meta.get('domain_list', [])
            webserver = meta.get('webserver', '')

            if not site_name:
                raise ValueError(public.lang('site_name is empty in meta.json'))

            # 查找目标站点
            if site_info and site_info.get('site_name'):
                target_name = site_info['site_name']
            else:
                target_name = site_name

            find = public.M('sites').where("name=?", (target_name,)).field('id,name,path').find()
            if not isinstance(find, dict) or not find.get('id'):
                raise ValueError(public.lang('Site [{}] does not exist, please create it first').format(target_name))

            site_id = find['id']
            current_path = find.get('path', site_path)

            # 3. 还原网站文件
            if 'file' in restore_type:
                self._progress_rewrite('Restoring site files to: {}'.format(current_path))
                files_zip = os.path.join(tmp_path, 'files.tar.gz')
                if os.path.exists(files_zip):
                    self._restore_site_files(current_path, files_zip)

            # 4. 还原数据库
            if has_database and db_name and 'db' in restore_type:
                self._progress_rewrite('Restoring database: {}'.format(db_name))
                db_file = os.path.join(tmp_path, 'database.sql.gz')
                if os.path.exists(db_file):
                    self._restore_site_database(db_name, db_file, site_id, meta)

            # 5. 还原配置文件
            if 'conf' in restore_type:
                self._progress_rewrite('Restoring site configs...')
                configs_dir = os.path.join(tmp_path, 'configs')
                if os.path.exists(configs_dir):
                    self._restore_site_configs(target_name, configs_dir, meta)

                # 6. 恢复PHP版本
                if php_version:
                    self._progress_rewrite('Restoring PHP version: {}'.format(php_version))
                    self._restore_php_version(target_name, php_version)

                # 7. 恢复域名
                if domain_list:
                    self._progress_rewrite('Restoring domains...')
                    self._restore_site_domains(site_id, target_name, domain_list)

                # 8. 恢复Web服务状态
                if webserver:
                    self._progress_rewrite('Restoring webservice status...')
                    self._restore_site_webserver(site_id, meta)

            # 修复权限
            self._progress_rewrite('Setting site permissions...')
            if args and hasattr(args, 'path'):
                files.files().fix_permissions(args)

            self._progress_rewrite('Full backup restore completed for: {}'.format(target_name))
            public.write_log_gettext('Site manager',
                                     f'Successfully restored the website [{site_info['site_name']}], Restored file: [{local_backup_file_path}]')

        except Exception as e:
            self._progress_rewrite('Errors occurred during the restoration process.: {}'.format(str(e)))
            return public.return_message(-1, 0, 'Errors occurred during the restoration process.: {}'.format(str(e)))


        finally:
            if os.path.exists(tmp_path):
                shutil.rmtree(tmp_path, ignore_errors=True)

        self._progress_rewrite('Successful recovery: {}'.format(str(site_info['site_path'])))
        return public.return_message(0, 0, public.lang("Restore Successful"))

    # 网站文件还原
    def _restore_site_files(self, site_path: str, files_zip: str) -> None:
        """还原网站文件：备份当前 .user.ini 后解压覆盖"""
        if not os.path.exists(site_path):
            os.makedirs(site_path, 0o755)

        # 备份当前 .user.ini（先解锁再操作）
        user_ini = os.path.join(site_path, '.user.ini')
        user_ini_bak = None
        if os.path.exists(user_ini):
            public.ExecShell('chattr -i ' + user_ini)
            user_ini_bak = user_ini + '.restore_bak'
            shutil.copy2(user_ini, user_ini_bak)

        try:
            if '.zip' in files_zip:
                public.ExecShell(f'unzip -oq {files_zip} -d {site_path}')
            else:
                public.ExecShell(f'tar -zxf {files_zip} -C {site_path}')
        finally:
            # 还原user_ini
            if user_ini_bak and os.path.exists(user_ini_bak):
                if not os.path.exists(user_ini):
                    shutil.move(user_ini_bak, user_ini)
                else:
                    if os.path.exists(user_ini_bak):
                        os.remove(user_ini_bak)

            if os.path.exists(user_ini):
                public.ExecShell('chattr +i ' + user_ini)

    # 网站服务配置文件还原
    def _restore_site_configs(self, site_name: str, configs_dir: str, mate: dict = None) -> None:
        """还原站点配置文件（与 _backup_site_configs 对称）"""
        vhost = self._setup_path + '/panel/vhost'

        # --- Nginx ---
        nginx_src = os.path.join(configs_dir, 'nginx', '{}.conf'.format(site_name))
        if os.path.exists(nginx_src):
            nginx_dst = '{}/nginx/{}.conf'.format(vhost, site_name)
            shutil.copy2(nginx_src, nginx_dst)

        well_known_src = os.path.join(configs_dir, 'nginx', 'well-known', site_name)
        if os.path.exists(well_known_src):
            well_known_dst = '{}/nginx/well-known/{}'.format(vhost, site_name)
            if os.path.exists(well_known_dst):
                shutil.rmtree(well_known_dst, ignore_errors=True)
            shutil.copytree(well_known_src, well_known_dst, dirs_exist_ok=True)

        # --- Apache ---
        apache_src = os.path.join(configs_dir, 'apache', '{}.conf'.format(site_name))
        if os.path.exists(apache_src):
            apache_dst = '{}/apache/{}.conf'.format(vhost, site_name)
            shutil.copy2(apache_src, apache_dst)

        # --- OpenLiteSpeed ---
        ols_src = os.path.join(configs_dir, 'openlitespeed', '{}.conf'.format(site_name))
        if os.path.exists(ols_src):
            ols_dst = '{}/openlitespeed/{}.conf'.format(vhost, site_name)
            shutil.copy2(ols_src, ols_dst)

        ols_detail_src = os.path.join(configs_dir, 'openlitespeed', 'detail', '{}.conf'.format(site_name))
        if os.path.exists(ols_detail_src):
            ols_detail_dst = '{}/openlitespeed/detail/{}.conf'.format(vhost, site_name)
            shutil.copy2(ols_detail_src, ols_detail_dst)

        ols_ssl_src = os.path.join(configs_dir, 'openlitespeed', 'detail', 'ssl', '{}.conf'.format(site_name))
        if os.path.exists(ols_ssl_src):
            ols_ssl_dst = '{}/openlitespeed/detail/ssl/{}.conf'.format(vhost, site_name)
            shutil.copy2(ols_ssl_src, ols_ssl_dst)

        # --- Extension proxy dir_auth---
        for server in ['nginx', 'apache']:
            ext_src = os.path.join(configs_dir, server, 'extension', site_name)
            if os.path.exists(ext_src):
                ext_dst = '{}/{}/extension/{}'.format(vhost, server, site_name)
                if os.path.exists(ext_dst):
                    shutil.rmtree(ext_dst, ignore_errors=True)
                shutil.copytree(ext_src, ext_dst, dirs_exist_ok=True)

            proxy_src = os.path.join(configs_dir, server, 'proxy', site_name)
            if os.path.exists(proxy_src):
                proxy_dst = '{}/{}/proxy/{}'.format(vhost, server, site_name)
                if os.path.exists(proxy_dst):
                    shutil.rmtree(proxy_dst, ignore_errors=True)
                shutil.copytree(proxy_src, proxy_dst, dirs_exist_ok=True)

            dir_auth_src = os.path.join(configs_dir, server, 'dir_auth', site_name)
            if os.path.exists(dir_auth_src):
                dir_auth_dst = '{}/{}/dir_auth/{}'.format(vhost, server, site_name)
                if os.path.exists(dir_auth_dst):
                    shutil.rmtree(dir_auth_dst, ignore_errors=True)
                shutil.copytree(dir_auth_src, dir_auth_dst, dirs_exist_ok=True)

        # --- Rewrite ---
        rewrite_src = os.path.join(configs_dir, 'rewrite', '{}.conf'.format(site_name))
        if os.path.exists(rewrite_src):
            rewrite_dst = '{}/rewrite/{}.conf'.format(vhost, site_name)
            shutil.copy2(rewrite_src, rewrite_dst)

        rewrite_dir = os.path.join(configs_dir, 'rewrite')
        if os.path.exists(rewrite_dir):
            for f in os.listdir(rewrite_dir):
                if f.endswith('.conf') and site_name in f:
                    shutil.copy2(os.path.join(rewrite_dir, f),
                                 os.path.join(vhost, 'rewrite', f))

        if mate.get('is_proxy'):
            proxy = "/www/server/panel/data/proxyfile.json"
            if os.path.exists(proxy):
                try:
                    is_ = False
                    proxy_json = json.loads(public.readFile(proxy))
                    for idx, i in enumerate(proxy_json):
                        if i.get('sitename') == site_name:
                            proxy_json[idx] = mate.get('is_proxy')
                            is_ = True
                            break
                    if not is_:
                        proxy_json.append(mate.get('is_proxy'))
                    public.writeFile(proxy, json.dumps(proxy_json))
                except:
                    pass

        if mate.get('is_redirect'):
            redirect = "/www/server/panel/data/redirect.conf"
            if os.path.exists(redirect):
                try:
                    is_ = False
                    redirect_json = json.loads(public.readFile(redirect))
                    for idx, i in enumerate(redirect_json):
                        if i.get('sitename') == site_name:
                            redirect_json[idx] = mate.get('is_redirect')
                            is_ = True
                            break
                    if not is_:
                        redirect_json.append(mate.get('is_redirect'))
                    public.writeFile(redirect, json.dumps(redirect_json))
                except:
                    pass

        # --- SSL/Cert ---
        cert_src = os.path.join(configs_dir, 'cert', site_name)
        if os.path.exists(cert_src):
            cert_dst = os.path.join(vhost, 'cert', site_name)
            if os.path.exists(cert_dst):
                shutil.rmtree(cert_dst, ignore_errors=True)
            shutil.copytree(cert_src, cert_dst, dirs_exist_ok=True)

        # --- pass ---
        pass_src = '/www/server/pass/{}'.format(site_name)
        if os.path.exists(pass_src):
            pass_dst = os.path.join(vhost, 'pass', site_name)
            if os.path.exists(pass_dst):
                shutil.rmtree(pass_dst, ignore_errors=True)
            shutil.copytree(pass_src, pass_dst, dirs_exist_ok=True)

        if mate.get('is_dir_auth'):
            dir_auth = "/www/server/panel/data/site_dir_auth.json"
            if os.path.exists(dir_auth):
                try:
                    redirect_json = json.loads(public.readFile(dir_auth))
                    redirect_json[site_name] = mate.get('is_dir_auth')
                    public.writeFile(dir_auth, json.dumps(redirect_json))
                except:
                    pass

    # 数据库还原
    def _restore_site_database(self, db_name: str, db_file: str, site_id: int = 0, meta: dict = None) -> None:
        """还原数据库：若不存在则创建本地数据库并绑定网站，通过 gunzip + mysql 导入"""
        db_find = public.M('databases').where("name=?", (db_name,)).field('id,name,db_type,conn_config').find()
        if not isinstance(db_find, dict) or not db_find.get('id'):
            db_username = meta.get('db_username', '')
            db_password = meta.get('db_password', '')

            # 数据库不存在，创建本地数据库
            self._progress_rewrite('Database [{}] not found, creating local database...'.format(db_name))
            from database_v2 import database
            db_obj = database()
            get = public.to_dict_obj({
                'name': db_name,
                'db_user': db_username,
                'codeing': 'utf8mb4',
                'password': db_password,
                'sid': 0,
                'active': True,
                'address': '%',
                'ps': '',
                'dtype': 'MySQL',
                'pid': site_id,
            })
            result = db_obj.AddDatabase(get)
            if result.get('status') != 0:
                raise ValueError(public.lang('Failed to create database [{}]: {}').format(
                    db_name, result.get('message', '')))
            # 确保绑定网站ID
            new_db = public.M('databases').where("name=?", (db_name,)).field('id,pid').find()
            if isinstance(new_db, dict) and new_db.get('id') and new_db.get('pid', 0) != site_id:
                public.M('databases').where('id=?', (new_db['id'],)).update({'pid': site_id})
            self._progress_rewrite('Database [{}] created and bound to site [{}]'.format(db_name, site_id))
            # 重新查询
            db_find = public.M('databases').where("name=?", (db_name,)).field('id,name,db_type,conn_config').find()
            if not isinstance(db_find, dict) or not db_find.get('id'):
                raise ValueError(public.lang('Database [{}] creation failed').format(db_name))


        # 解压 .sql.gz → .sql
        sql_file = db_file.replace('.sql.gz', '.sql')

        public.ExecShell(f'gunzip -f {db_file}')
        if not os.path.exists(sql_file):
            raise FileNotFoundError(public.lang('Decompressed SQL file not found: {}').format(sql_file))

        mysql_bin = public.get_mysql_bin()
        if db_find['db_type'] in ['0', 0]:
            # 本地数据库
            mysql_root = public.M('config').where('id=?', (1,)).getField('mysql_root')
            if not mysql_root:
                raise ValueError(public.lang('MySQL root password is empty'))

            from database_v2 import database
            db_obj = database()
            if not db_obj.mypass(True, mysql_root):
                raise ValueError(public.lang('Failed to get MySQL root password'))

            try:
                os.environ["MYSQL_PWD"] = str(mysql_root)
                public.ExecShell('{} -u root --default-character-set=utf8mb4 {} < {}'.format(
                    shlex.quote(mysql_bin),
                    shlex.quote(db_name),
                    shlex.quote(sql_file)
                ))
            finally:
                os.environ["MYSQL_PWD"] = ""
                db_obj.mypass(False, mysql_root)
        else:
            # 远程数据库
            conn_config = json.loads(db_find.get('conn_config', '{}'))
            if not conn_config.get('db_host'):
                raise ValueError(public.lang('Remote database connection config missing'))

            try:
                os.environ["MYSQL_PWD"] = str(conn_config.get('db_password', ''))
                public.ExecShell('{} -h {} -P {} -u {} --default-character-set=utf8mb4 {} < {}'.format(
                    shlex.quote(mysql_bin),
                    shlex.quote(str(conn_config.get('db_host', ''))),
                    shlex.quote(str(conn_config.get('db_port', 3306))),
                    shlex.quote(str(conn_config.get('db_user', ''))),
                    shlex.quote(db_name),
                    shlex.quote(sql_file)
                ))
            finally:
                os.environ["MYSQL_PWD"] = ""

    # PHP版本还原
    def _restore_php_version(self, site_name: str, php_version: str) -> None:
        """恢复站点PHP版本（通过 panelSite.SetPHPVersion）"""
        try:
            current_ver = public.get_site_php_version(site_name)
            if current_ver != php_version and php_version not in ('', 'other', '00'):
                from panel_site_v2 import panelSite
                site_obj = panelSite()
                get = public.to_dict_obj({'siteName': site_name, 'version': php_version, 'other': ''})
                site_obj.SetPHPVersion(get)
        except Exception as e:
            self._progress_rewrite('Failed to switch PHP version: {}'.format(e))

    # web服务状态还原
    def _restore_site_webserver(self, site_id: int, meta: dict) -> None:
        """恢复站点Web服务状态（多Web服务场景下切换service_type）"""
        backup_webserver = meta.get('webserver', '')
        backup_multi = meta.get('multi_webservice_status', False)
        if not backup_webserver or backup_webserver not in ('nginx', 'apache', 'openlitespeed'):
            return

        current_multi = public.get_multi_webservice_status()

        # 多服务已启用，但备份文件中为单服务配置
        if current_multi and not backup_multi:
            site = public.M('sites').where('id=?', (site_id,)).field('service_type').find()
            current_type = (site.get('service_type') or 'nginx') if isinstance(site, dict) else 'nginx'
            if current_type == backup_webserver:
                return
            self._progress_rewrite('Switching webservice from [{}] to [{}]...'.format(current_type, backup_webserver))
            from panel_site_v2 import panelSite
            site_obj = panelSite()
            args = public.to_dict_obj({
                'site_id': str(site_id),
                'service_type': backup_webserver,
                'is_reload': True,
            })
            try:
                result = site_obj.switch_webservice(args)
                if isinstance(result, dict) and result.get('status', 0) < 0:
                    self._progress_rewrite('Webservice switch warning: {}'.format(
                        result.get('message', 'Unknown error')))
            except Exception as e:
                self._progress_rewrite('Webservice restore failed: {}'.format(str(e)))
        elif not current_multi and backup_multi:
            # 当前多服务未开启，但备份是多服务下配置文件
            site_name = public.M('sites').where('id=?', (site_id,)).getField('name')
            site_path = public.M('sites').where('id=?', (site_id,)).getField('path')
            current_global = public.get_webserver()
            vhost = os.path.join(public.get_panel_path(), 'vhost')

            from panel_site_v2 import panelSite
            site_obj = panelSite()

            # 切换nginx配置为当前全局webserver对应的格式
            nginx_conf = os.path.join(vhost, 'nginx', site_name + '.conf')
            if os.path.exists(nginx_conf):
                self._progress_rewrite('Regenerating nginx config for webservice [{}]...'.format(current_global))
                site_obj.nginx_update_config(current_global, nginx_conf, backup_webserver, site_name, site_path, site_id)

            # Apache配置端口替换与反向代理IP
            apache_conf = os.path.join(vhost, 'apache', site_name + '.conf')
            if os.path.exists(apache_conf):
                self._progress_rewrite('Fixing Apache config ports...')
                self._fix_apache_config_ports(apache_conf)
                # if current_global == 'apache':
                #     site_obj.set_apache_logs_ip(apache_conf)

            # OLS配置端口替换
            self._progress_rewrite('Fixing OLS config ports...')
            self._fix_ols_config_ports(vhost, site_name)
            backup_webserver = 'nginx'

        public.M('sites').where('id=?', (site_id,)).update({'service_type': backup_webserver})

    def _fix_apache_config_ports(self, conf_path: str) -> None:
        """修复Apache配置端口（代理模式：80→8288, 443→8290）"""
        import re
        try:
            content = public.readFile(conf_path)
            if not content:
                return
            content = re.sub(r'(<VirtualHost\s+\*:)80\b', r'\g<1>8288', content)
            content = re.sub(r'(<VirtualHost\s+\*:)443\b', r'\g<1>8290', content)
            public.writeFile(conf_path, content)
        except Exception as e:
            self._progress_rewrite('Apache port fix failed: {}'.format(str(e)))

    def _fix_ols_config_ports(self, vhost: str, site_name: str) -> None:
        """修复OLS配置端口（代理模式：80→8188, 443→8190）"""
        import re
        ols_paths = [
            os.path.join(vhost, 'openlitespeed', '{}.conf'.format(site_name)),
            os.path.join(vhost, 'openlitespeed', 'detail', '{}.conf'.format(site_name)),
            os.path.join(vhost, 'openlitespeed', 'detail', 'ssl', '{}.conf'.format(site_name)),
        ]
        for conf_path in ols_paths:
            if not os.path.exists(conf_path):
                continue
            try:
                content = public.readFile(conf_path)
                if not content:
                    continue
                content = re.sub(r'(\*:)(80)\b', r'\g<1>8188', content)
                content = re.sub(r'(\*:)(443)\b', r'\g<1>8190', content)
                public.writeFile(conf_path, content)
            except Exception as e:
                self._progress_rewrite('OLS port fix failed for {}: {}'.format(conf_path, str(e)))

    # 域名还原
    def _restore_site_domains(self, site_id: int, site_name: str,
                              domain_list: list) -> None:
        """恢复域名：先删除现有域名（保留主域名），再添加备份域名"""
        # 预检：过滤可用域名（未被其他站点占用的）
        usable_domains = []
        for info in domain_list:
            name = info.get('name', '')
            if not name:
                continue
            owner = public.M('domain').where('name=?', (name,)).field('pid').find()
            if owner and site_id != owner['pid']:
                continue
            usable_domains.append(info)
        if not usable_domains:
            return self._progress_rewrite(public.lang('No usable domains in backup, all domains are occupied by other sites'))

        from panel_site_v2 import panelSite
        site_obj = panelSite()

        # 构建过滤站点
        to_add_set = {
            (info.get('name'), int(info.get('port', 80)))
            for info in domain_list if info.get('name')
        }

        # 1. 删除现有域名（保留主域名即站点名）
        existing = public.M('domain').where('pid=?', (site_id,)).field('name,port').select()
        del_error = []
        if isinstance(existing, list):
            for d in existing:
                try:
                    # 判断域名是否需要删除
                    if (d['name'], int(d.get('port', 80))) in to_add_set:
                        continue

                    get = public.to_dict_obj({
                        'id': site_id,
                        'webname': site_name,
                        'domain': d['name'],
                        'port': int(d.get('port', 80))
                    })
                    res = site_obj.DelDomain(get)
                    if res['status'] == -1:
                        del_error.append({'domain': d['name'],'port': int(d.get('port', 80))})
                except Exception as e:
                    self._progress_rewrite("Domain deletion failed: " + str(e))

        # 2. 添加可用域名
        for domain_info in usable_domains:
            domain_name = domain_info.get('name', '')
            if not domain_name:
                continue

            try:
                get = public.to_dict_obj({
                    'id': site_id,
                    'webname': site_name,
                    'domain': domain_name + ':' + str(domain_info.get('port', '80'))
                })
                site_obj.AddDomain(get)
            except Exception as e:
                self._progress_rewrite("Domain restoration failed: " + str(e))

        # 3. 检查删除失败的域名，若不存在于待添加的域名列表中，则再次尝试删除
        if del_error:
            for error_item in del_error:
                # 判断当前失败的域名和端口，是否在准备添加的列表中
                if (error_item['domain'], error_item['port']) not in to_add_set:
                    try:
                        get = public.to_dict_obj({
                            'id': site_id,
                            'webname': site_name,
                            'domain': error_item['domain'],
                            'port': error_item['port']
                        })
                        # 再次尝试删除
                        site_obj.DelDomain(get)
                    except Exception as e:
                        self._progress_rewrite(f"Retry deleting domain {error_item['domain']} failed: {str(e)}")
        return

    def restore_site_database(self, db_name: str, db_file: str, site_id: int = 0, meta: dict = None) -> None:
        return self._restore_site_database(db_name,db_file,site_id,meta)
    # ====================== PHP站点全量还原 end ====================== #
