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
import shlex

os.chdir('/www/server/panel')
if not 'class/' in sys.path:
    sys.path.insert(0, 'class/')
import public
from public.hook_import import hook_import
hook_import()

_VERSION = 1.5


class backup:
    _path = None
    _exclude = ""
    _err_log = '/tmp/backup_err.log'
    _inode_min = 10
    _db_mysql = None
    _cloud = None
    _is_save_local = os.path.exists('data/is_save_local_backup.pl')
    _error_msg = ""
    _backup_all = False

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
        self._cloud = cloud_object
        self.cron_info = None
        if cron_info and 'echo' in cron_info.keys():
            self.cron_info = self.get_cron_info(cron_info["echo"])

        self._path = public.M('config').where("id=?", (1,)).getField('backup_path')

        if not public.M('sqlite_master').where('type=? AND name=? AND sql LIKE ?',
                                               ('table', 'backup', '%cron_id%')).count():
            public.M('backup').execute("ALTER TABLE 'backup' ADD 'cron_id' INTEGER DEFAULT 0", ())

    def echo_start(self):
        print("=" * 90)
        print("|-" + public.lang("Start backup") + "[{}]".format(public.format_date()))
        print("=" * 90)

    def echo_end(self):
        print("=" * 90)
        print("|-" + public.lang("Backup completed") + "[{}]".format(public.format_date()))
        print("=" * 90)
        print("\n")

    def echo_info(self, msg):
        print("|-{}".format(msg))

    def echo_error(self, msg):
        print("=" * 90)
        print("|-Error：{}".format(msg))
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
            self._exclude += " --exclude=\"" + ex + "\""
        self._exclude += " "
        return self._exclude

    def GetDiskInfo2(self):
        # 取磁盘分区信息
        temp = public.ExecShell("df -T -P|grep '/'|grep -v tmpfs|grep -v 'snap/core'|grep -v udev|grep -v overlay")[0]
        tempInodes = \
        public.ExecShell("df -i -P|grep '/'|grep -v tmpfs|grep -v 'snap/core'|grep -v udev|grep -v overlay")[0]
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

        error_msg = ""
        self.echo_start()
        if not os.path.exists(spath):
            error_msg = public.lang('The specified directory {} does not exist!', spath)
            self.echo_error(error_msg)
            self.send_failture_notification(error_msg, target=f"{spath}|path")
            return False

        if spath[-1] == '/':
            spath = spath[:-1]

        dirname = os.path.basename(spath)
        if not dfile:
            fname = 'path_{}_{}.tar.gz'.format(dirname, public.format_date("%Y%m%d_%H%M%S"))
            # fname = 'path_{}_{}_{}.tar.gz'.format(dirname, public.format_date("%Y%m%d_%H%M%S"),
            #                                       public.GetRandomString(6))
            dfile = os.path.join(self._path, 'path', fname)

        if not self.backup_path_to(spath, dfile, exclude):
            if self._error_msg:
                error_msg = self._error_msg
            self.send_failture_notification(error_msg, target=f"{spath}|path")
            return False

        if self._cloud:
            self.echo_info(public.lang('Uploading to {}, please wait ...', self._cloud._title))
            if self._cloud.upload_file(dfile, 'path'):
                self.echo_info(public.lang('Successfully uploaded to {}', self._cloud._title))
            else:
                if hasattr(self._cloud, "error_msg"):
                    if self._cloud.error_msg:
                        error_msg = self._cloud.error_msg
                if not error_msg:
                    error_msg = public.lang("File upload failed, skip this backup!")
                self.echo_error(error_msg)
                if os.path.exists(dfile):
                    os.remove(dfile)

                remark = "Backup to " + self._cloud._title
                self.send_failture_notification(error_msg, target=f"{spath}|path", remark=remark)
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
            'size': os.path.getsize(dfile)
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
                        'size': os.path.getsize(dfile)
                    }
                    public.M('backup').insert(pdata)
            if _not_save_local:
                if os.path.exists(dfile):
                    os.remove(dfile)
                    self.echo_info(
                        public.lang('User settings do not retain local backups, deleted {}', dfile))
            else:
                self.echo_info(public.lang("Local backup has been kept"))

        if not self._cloud:
            backups = public.M('backup').where("cron_id=? and type=? and pid=? and name=? and filename NOT LIKE '%|%'",
                                               (cron_id, '2', 0, spath)).field('id,name,filename').select()
        else:
            backups = public.M('backup').where("cron_id=? and type=? and pid=? and name=? and filename LIKE ?",
                                               (cron_id, '2', 0, spath, '%{}%'.format(self._cloud._name))).field(
                'id,name,filename').select()

        self.delete_old(backups, save, 'path')
        self.echo_end()
        self.save_backup_status(True, target=f"{spath}|path")
        return dfile

    # 清理过期备份文件
    def delete_old(self, backups, save, data_type=None, site_name=None):
        if type(backups) == str:
            self.echo_info(public.lang('Failed to clean expired backup, error: {}', backups))
            return
        self.echo_info(public.lang('Keep the latest number of backups: {} copies', str(save),))

        # 跳过手动备份文件
        new_backups = []
        for i in range(len(backups)):
            if data_type == 'database' and backups[i]['name'][:3] == 'db_':  # 数据库备份
                new_backups.append(backups[i])
            elif data_type == 'site' and backups[i]['name'][:4] == 'web_' and backups[i]['name'][
                                                                              -7:] == '.tar.gz':  # 网站备份
                new_backups.append(backups[i])
            elif data_type == 'path' and backups[i]['name'][:5] == 'path_':  # 目录备份
                new_backups.append(backups[i])
        if new_backups:
            backups = new_backups[:]
        num = len(backups) - int(save)
        if num > 0:
            # self._get_local_backdir()
            self.echo_info('-' * 88)
            for backup in backups:
                # 处理目录备份到远程的情况
                if backup['filename'].find('|') != -1:
                    tmp = backup['filename'].split('|')
                    backup['filename'] = tmp[0]
                    backup['name'] = tmp[-1]
                # 尝试删除本地文件
                if os.path.exists(backup['filename']):
                    try:
                        os.remove(backup['filename'])
                        self.echo_info(public.lang('Expired backup files have been cleaned from disk: {}',
                                                              backup['filename']))
                    except:
                        pass
                # 尝试删除远程文件
                if self._cloud:
                    self._cloud.delete_file(backup['name'], data_type)
                    self.echo_info(public.lang('Expired backup files have been cleaned from {}: {}',
                                                          self._cloud._title, backup['name']))

                # 从数据库清理
                public.M('backup').where('id=?', (backup['id'],)).delete()
                num -= 1
                if num < 1: break
        # if data_type == 'site':
        #     backup_path = public.get_backup_path() + '/site'.replace('//', '/')
        #     site_lists = os.listdir(backup_path)
        #     file_info = []
        #     del_list = []
        #     check_name = 'web_{}_'.format(site_name)
        #     for site_v in site_lists:
        #         tmp_dict = {}
        #         if check_name == 'web__': continue
        #         if site_v.find(check_name) == -1: continue
        #         filename = os.path.join(backup_path, site_v)
        #         if os.path.isfile(filename):
        #             tmp_dict['name'] = filename
        #             tmp_dict['time'] = int(os.path.getmtime(filename))
        #             file_info.append(tmp_dict)
        #     if file_info and len(file_info) > int(save):
        #         file_info = sorted(file_info, key=lambda keys: keys['time'])
        #         del_list = file_info[:-int(save)]
        #         for del_file in del_list:
        #             if not del_file: continue
        #             if os.path.isfile(del_file['name']):
        #                 os.remove(del_file['name'])
        #                 self.echo_info(u"Expired backup files cleaned from disk：" + del_file['name'])

    # 获取本地备份目录
    # def _get_local_backdir(self):
    #     self._local_backdir = public.M('config').field('backup_path').find()['backup_path']

    # 压缩目录
    def backup_path_to(self, spath, dfile, exclude=[], siteName=None):
        if not os.path.exists(spath):
            self.echo_error(public.lang('The specified directory {} does not exist!', spath))
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
        self.echo_info(public.lang('Partition {} available disk space is: {}, available Inode is: {}',disk_path, str(public.to_size(disk_free)), str(disk_inode)))
        if disk_path:
            if disk_free < p_size:
                self.echo_error(public.lang('The available disk space of the target partition is less than {}, and the backup cannot be completed. Please increase the disk capacity or change the default backup directory on the settings page!',str(public.to_size(p_size))))
                return False

            if disk_inode < self._inode_min:
                self.echo_error(public.lang('The available Inode of the target partition is less than {}, and the backup cannot be completed. Please increase the disk capacity or change the default backup directory on the settings page!',str(self._inode_min) ))
                return False

        stime = time.time()
        self.echo_info(public.lang('Start compressing files: {}', public.format_date(times=stime)))
        if os.path.exists(dfile):
            os.remove(dfile)
        public.ExecShell("cd " + os.path.dirname(
            spath) + " && tar zcvf '" + dfile + "' " + self._exclude + " '" + dirname + "' 2>{err_log} 1> /dev/null".format(
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

    # 备份指定站点
    def backup_site(self, siteName, save=3, exclude=[], echo_id=None):
        try:
            self.echo_start()
            find = public.M('sites').where('name=?', (siteName,)).field('id,path,project_type').find()
            public.print_log(find)
            if not find or not isinstance(find, dict):
                raise Exception(' The directory for does not exist')

            # Wordpress
            if find['project_type'] == 'WP2':
                try:
                    from wp_toolkit import wpbackup
                    bak_info = wpbackup(find['id']).backup_full_get_data()
                    self.echo_info(public.lang('Backup wordpress [{}] successfully', siteName))
                    self.echo_end()
                    return bak_info.bak_file
                except Exception as e:
                    public.print_error()
                    self.echo_info(str(e))
                    self.echo_end()
                    return None

            spath = find['path']
            pid = find['id']
            fname = 'web_{}_{}.tar.gz'.format(siteName, public.format_date("%Y%m%d_%H%M%S"))

            # fname = 'web_{}_{}_{}.tar.gz'.format(siteName, public.format_date("%Y%m%d_%H%M%S"),
            #                                      public.GetRandomString(6))

            dfile = os.path.join(self._path, 'site', fname)
            error_msg = ""
            if not self.backup_path_to(spath, dfile, exclude, siteName=siteName):
                if self._error_msg:
                    error_msg = self._error_msg
                self.send_failture_notification(error_msg, target=f"{siteName}|site")
                return False

            if self._cloud:
                self.echo_info(public.lang('Uploading to {}, please wait ...', self._cloud._title))
                if self._cloud.upload_file(dfile, 'site'):
                    self.echo_info(public.lang('Successfully uploaded to {}', self._cloud._title))
                else:
                    if hasattr(self._cloud, "error_msg"):
                        if self._cloud.error_msg:
                            error_msg = self._cloud.error_msg
                    if not error_msg:
                        error_msg = public.lang("File upload failed, skip this backup!")
                    self.echo_error(error_msg)
                    if os.path.exists(dfile):
                        os.remove(dfile)

                    remark = "Backup to " + self._cloud._title
                    self.send_failture_notification(error_msg, target=f"{siteName}|site", remark=remark)
                    return False

            filename = dfile
            if self._cloud:
                filename = dfile + '|' + self._cloud._name + '|' + fname
            cron_id = 0
            if echo_id:
                cron_id = public.M("crontab").where('echo=?', (echo_id,)).getField('id')
            pdata = {
                'cron_id': cron_id,
                'type': 0,
                'name': fname,
                'pid': pid,
                'filename': filename,
                'addtime': public.format_date(),
                'size': os.path.getsize(dfile)
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
                            'type': 0,
                            'name': fname,
                            'pid': pid,
                            'filename': dfile,
                            'addtime': public.format_date(),
                            'size': os.path.getsize(dfile)
                        }
                        public.M('backup').insert(pdata)

                if _not_save_local:
                    if os.path.exists(dfile):
                        print(dfile)
                        os.remove(dfile)
                        self.echo_info(
                            public.lang('User settings do not retain local backups, deleted {}', dfile))
                else:
                    self.echo_info(public.lang("Local backup has been kept"))

            # 清理多余备份
            if not self._cloud:
                backups = public.M('backup').where("cron_id=? and type=? and pid=? and filename NOT LIKE '%|%'",
                                                   (cron_id, '0', pid)).field('id,name,filename').select()
            else:
                backups = public.M('backup').where('cron_id=? and type=? and pid=? and filename LIKE ?',
                                                   (cron_id, '0', pid, "%{}%".format(self._cloud._name))).field(
                    'id,name,filename').select()

            self.delete_old(backups, save, 'site', siteName)
            self.echo_end()
            return dfile
        except Exception as e:
            self.send_failture_notification('site {} {}'.format(siteName, e), target=siteName)
            self.echo_error('site {} {}'.format(siteName, e))

    # 备份所有数据库
    def backup_database_all(self, save=3, echo_id=None):
        databases = public.M('databases').where("type=?", "MySQL").field('name').select()
        self._backup_all = True
        failture_count = 0
        results = []
        for database in databases:
            self._error_msg = ""
            result = self.backup_database(database['name'], save=save, echo_id=echo_id)
            if not result:
                failture_count += 1
            results.append((database['name'], result, self._error_msg,))
            self.save_backup_status(result, target=f"{database['name']}|database", msg=self._error_msg)

        if failture_count > 0:
            self.send_all_failture_notification("database", results)
        self._backup_all = False

    # 备份所有站点
    def backup_site_all(self, save=3, echo_id=None):
        sites = public.M('sites').field('name').select()
        self._backup_all = True
        failture_count = 0
        results = []
        for site in sites:
            self._error_msg = ""
            result = self.backup_site(site['name'], save, echo_id=echo_id)
            if not result:
                failture_count += 1
            results.append((site['name'], result, self._error_msg,))
            self.save_backup_status(result, target=f"{site['name']}|site", msg=self._error_msg)

        if failture_count > 0:
            self.send_all_failture_notification("site", results)
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

    # 备份指定数据库
    def backup_database(self, db_name, dfile=None, save=3, echo_id=None):
        try:
            self.echo_start()
            if not dfile:
                fname = 'db_{}_{}.sql.gz'.format(db_name, public.format_date("%Y%m%d_%H%M%S"))
                # fname = 'db_{}_{}_{}.sql.gz'.format(db_name, public.format_date("%Y%m%d_%H%M%S"),
                #                                     public.GetRandomString(6))
                dfile = os.path.join(self._path, 'database', fname)
            else:
                fname = os.path.basename(dfile)

            dpath = os.path.dirname(dfile)
            if not os.path.exists(dpath):
                os.makedirs(dpath, 384)

            error_msg = ""
            # ----- 判断是否为远程数据库START  @author hwliang<2021-01-08>--------
            db_find = public.M('databases').where("name=?", (db_name,)).find()
            if db_find['type'] != "MySQL":
                # if db_find['type'] in ['SQLServer','Redis']:
                print("|-{}The database does not currently support backup".format(db_find['type']))
                return False
                # if db_find['type'] == "MongoDB":
                #     import databaseModel.mongodbModel as mongodbModel
                #     args = public.dict_obj()
                #     args.id = db_find['id']
                #     args.name = db_find['name']
                #     backup_res = mongodbModel.panelMongoDB().ToBackup(args)
                # elif db_find['type'] == "PgSQL":
                #     import databaseModel.pgsqlModel as pgsqlModel
                #     args = public.dict_obj()
                #     args.id = db_find['id']
                #     args.name = db_find['name']
                #     backup_res = pgsqlModel.panelPgsql().ToBackup(args)

                # if not isinstance(backup_res,dict) or not 'status' in backup_res:

                #     return False

                # if not backup_res['status']:
                #     print("|-{}数据库备份失败".format(db_find['name']))
                #     print("|-{}".format(backup_res['msg']))
                #     return False
                # dfile = dfile = os.path.join(self._path,'database',,fname)
                # print("|-{}数据库备份成功".format(db_find['name']))
                # print("|-数据库已备份到:{}".format(dfile))

                # return False
            conn_config = {}
            self._db_mysql = public.get_mysql_obj(db_name)
            is_cloud_db = db_find['db_type'] in ['1', 1, '2', 2]
            if is_cloud_db:
                # 连接远程数据库
                if db_find['sid']:
                    conn_config = public.M('database_servers').where('id=?', db_find['sid']).find()
                    if not 'db_name' in conn_config: conn_config['db_name'] = None
                else:
                    conn_config = json.loads(db_find['conn_config'])
                conn_config['db_port'] = str(int(conn_config['db_port']))
                if not self._db_mysql or not self._db_mysql.set_host(conn_config['db_host'],
                                                                     int(conn_config['db_port']),
                                                                     conn_config['db_name'], conn_config['db_user'],
                                                                     conn_config['db_password']):
                    error_msg = "Failed to connect to remote database [{}:{}]".format(conn_config['db_host'],
                                                                                      conn_config['db_port'])
                    print(error_msg)
                    return False
            # ----- 判断是否为远程数据库END @author hwliang<2021-01-08>------------
            d_tmp = self._db_mysql.query(
                "select sum(DATA_LENGTH)+sum(INDEX_LENGTH) from information_schema.tables where table_schema='%s'" % db_name)
            try:
                p_size = self.map_to_list(d_tmp)[0][0]
            except:
                error_msg = public.get_msg_gettext(
                    'The database connection is abnormal. Please check whether the root user authority or database configuration parameters are correct.')
                self.echo_error(error_msg)
                self.send_failture_notification(error_msg, target=f"{db_name}|database")
                return False

            if p_size == None:
                error_msg = public.get_msg_gettext('The specified database [ {} ] has no data!', (db_name,))
                self.echo_error(error_msg)
                self.send_failture_notification(error_msg, target=f"{db_name}|database")
                return False

            character = public.get_database_character(db_name)

            self.echo_info(public.get_msg_gettext('Backup database:{}', (db_name,)))
            self.echo_info(public.get_msg_gettext('Database size: {}', (public.to_size(p_size),)))
            self.echo_info(public.get_msg_gettext('Database character set: {}', (character,)))
            disk_path, disk_free, disk_inode = self.get_disk_free(dfile)
            self.echo_info(public.get_msg_gettext(
                'Partition {} available disk space is: {}, available Inode is: {}', (
                    disk_path, str(public.to_size(disk_free)), str(disk_inode)
                )
            ))
            if disk_path:
                if disk_free < p_size:
                    error_msg = public.get_msg_gettext(
                        'The available disk space of the target partition is less than {}, and the backup cannot be completed. Please increase the disk capacity or change the default backup directory on the settings page!',
                        (
                            str(public.to_size(p_size), )
                        ))
                    self.echo_error(error_msg)
                    self.send_failture_notification(error_msg, target=f"{db_name}|database")
                    return False

                if disk_inode < self._inode_min:
                    error_msg = public.get_msg_gettext(
                        'The available Inode of the target partition is less than {}, and the backup cannot be completed. Please increase the disk capacity or change the default backup directory on the settings page!',
                        (self._inode_min,))
                    self.echo_error(error_msg)
                    self.send_failture_notification(error_msg, target=f"{db_name}|database")
                    return False

            stime = time.time()
            self.echo_info(public.get_msg_gettext('Start exporting database: {}', (public.format_date(times=stime),)))
            if os.path.exists(dfile):
                os.remove(dfile)
            # self.mypass(True)
            mysqldump_bin = public.get_mysqldump_bin()
            try:
                if not is_cloud_db:
                    # 本地数据库 @author hwliang<2021-01-08>
                    password = public.M('config').where('id=?', (1,)).getField('mysql_root')
                    password = public.shell_quote(str(password))
                    os.environ["MYSQL_PWD"] =  password
                    backup_cmd = mysqldump_bin + " -E -R --default-character-set=" + character + " --force --hex-blob --opt " + db_name + " -u root -p" + password + " 2>" + self._err_log + "| gzip > " + dfile
                else:
                    # 远程数据库 @author hwliang<2021-01-08>
                    password = public.shell_quote(str(conn_config['db_password']))
                    os.environ["MYSQL_PWD"] = password
                    backup_cmd = mysqldump_bin + " -h " + conn_config['db_host'] + " -P " + str(conn_config[
                                                                                                    'db_port']) + " -E -R --default-character-set=" + character + " --force --hex-blob --opt " + db_name + " -u " + str(
                        conn_config['db_user']) + " -p" + password + " 2>" + self._err_log + "| gzip > " + dfile
                public.ExecShell(backup_cmd)
            except Exception as e:
                raise
            finally:
                os.environ["MYSQL_PWD"] = ""
            # public.ExecShell("/www/server/mysql/bin/mysqldump --default-character-set="+ character +" --force --hex-blob --opt " + db_name + " 2>"+self._err_log+"| gzip > " + dfile)
            # self.mypass(False)
            gz_size = os.path.getsize(dfile)
            if gz_size < 400:
                error_msg = public.lang("Database export failed!")
                self.echo_error(error_msg)
                self.send_failture_notification(error_msg, target=f"{db_name}|database")
                self.echo_info(public.readFile(self._err_log))
                return False
            compressed_time = str('{:.2f}'.format(time.time() - stime))
            self.echo_info(
                public.get_msg_gettext('Compression completed, took {} seconds, compressed package size: {}',
                                       (str(compressed_time),
                                        str(public.to_size(gz_size))
                                        ))
            )
            if self._cloud:
                self.echo_info(public.get_msg_gettext('Uploading to {}, please wait ...', (self._cloud._title,)))
                if self._cloud.upload_file(dfile, 'database'):
                    self.echo_info(public.get_msg_gettext('Successfully uploaded to {}', (self._cloud._title,)))
                else:
                    if hasattr(self._cloud, "error_msg"):
                        if self._cloud.error_msg:
                            error_msg = self._cloud.error_msg
                    if not error_msg:
                        error_msg = public.lang("File upload failed, skip this backup!")
                    self.echo_error(error_msg)
                    if os.path.exists(dfile):
                        os.remove(dfile)

                    remark = "Backup to " + self._cloud._title
                    self.send_failture_notification(error_msg, target=f"{db_name}|database", remark=remark)
                    return False

            filename = dfile
            if self._cloud:
                filename = dfile + '|' + self._cloud._name + '|' + fname
            self.echo_info(public.get_msg_gettext('Database has been backed up to: {}', (dfile,)))
            if os.path.exists(self._err_log):
                os.remove(self._err_log)

            pid = public.M('databases').where('name=?', (db_name)).getField('id')
            cron_id = 0
            if echo_id:
                cron_id = public.M("crontab").where('echo=?', (echo_id,)).getField('id')
            pdata = {
                'cron_id': cron_id,
                'type': '1',
                'name': fname,
                'pid': pid,
                'filename': filename,
                'addtime': public.format_date(),
                'size': os.path.getsize(dfile)
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
                            'type': '1',
                            'name': fname,
                            'pid': pid,
                            'filename': dfile,
                            'addtime': public.format_date(),
                            'size': os.path.getsize(dfile)
                        }
                        public.M('backup').insert(pdata)

                if _not_save_local:
                    if os.path.exists(dfile):
                        os.remove(dfile)
                        self.echo_info(
                            public.get_msg_gettext('User settings do not retain local backups, deleted {}', (dfile,)))
                else:
                    self.echo_info(public.lang("Local backup has been kept"))

            # 清理多余备份
            if not self._cloud:
                backups = public.M('backup').where("cron_id=? and type=? and pid=? and filename NOT LIKE '%|%'",
                                                   (cron_id, '1', pid)).field('id,name,filename').select()
            else:
                backups = public.M('backup').where('cron_id=? and type=? and pid=? and filename LIKE ?',
                                                   (cron_id, '1', pid, "%{}%".format(self._cloud._name))).field(
                    'id,name,filename').select()

            self.delete_old(backups, save, 'database')
            self.echo_end()
            self.save_backup_status(True, target=f"{db_name}|database")
            return dfile
        except:
            self.send_failture_notification(public.get_msg_gettext('Database {} does not exist', (db_name,)), target=db_name)
            self.echo_error(public.get_msg_gettext('Database {} does not exist', (db_name,)))

    def generate_success_title(self, task_name):
        from send_mail import send_mail
        sm = send_mail()
        now = public.format_date(format="%Y-%m-%d %H:%M")
        server_ip = sm.GetLocalIp()
        title = public.get_msg_gettext('{}-{} The task was executed successfully', (server_ip, task_name))
        return title

    def generate_failture_title(self, task_name):
        title = "aaPanel backup task failed reminder".format(task_name)
        return title

    def generate_all_failture_notice(self, task_name, msg, backup_type, remark=""):
        from send_mail import send_mail
        sm = send_mail()
        now = public.format_date(format="%Y-%m-%d %H:%M:%S")
        server_ip = sm.GetLocalIp()
        if remark:
            remark = "\n* Task notes: {}".format(remark)

        notice_content = """*aaPanel reminds you that the cron failed to execute*
* Server IP*: {}
* Time*: {}
* Task name*: {} {}
* The following is a list of {} that failed to backup*:
{}
--Notification by aaPanel""".format(
            server_ip, now, task_name, remark, backup_type, msg)

#         tg_content = """📣‼*aaPanel reminds you that the cron failed to execute*‼
#
# * Server IP*: {}
# * Time*: {}
# * Task name*: {} {}
# * The following is a list of {} that failed to backup*:
# {}
# --Notification by aaPanel""".format(
#             server_ip, now, task_name, remark, backup_type, msg)
        # return {"mail":notice_content,"tg":tg_content}
        return notice_content

    def generate_failture_notice(self, task_name, msg, remark):
        from send_mail import send_mail
        sm = send_mail()
        now = public.format_date(format="%Y-%m-%d %H:%M:%S")
        server_ip = sm.GetLocalIp()
        if remark:
            remark = "\n* Task notes: {}".format(remark)

        notice_content = """*aaPanel reminds you that the cron failed to execute*
* Server IP*: {}
* Time*: {}
* Task name*: {} {}
* error message*:
{}
--Notification by aaPanel""".format(
            server_ip, now, task_name, remark, msg)

#         tg_content = """📣‼*aaPanel reminds you that the cron failed to execute*‼
#
# * Server IP*: {}
# * Time*: {}
# * Task name*: {} {}
# * Error messages*：
# {}
#
# -- Notification by aaPanel""".format(
#             server_ip, now, task_name, remark, msg)
        # return {'mail':notice_content,'tg':tg_content}
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
                self.echo_info(public.lang("Notification has been sent"))

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
                    content += "{}、".format(obj_name)
                    # content += "<tr><td style='color:red'>{}</td><tr>".format(obj_name)

            if failture_count > 0:
                if self._cloud:
                    remark = public.lang("Backup to {}, a total of {} {}, and failures {}."), (
                        self._cloud._title, total, backup_type_desc, failture_count)
                else:
                    remark = public.lang("Backup failed {}/total {} sites"), (
                        failture_count, total, backup_type_desc)

            msg = self.generate_all_failture_notice(task_name, content, backup_type_desc, remark)
            res = self.send_notification(notice_channel, title, msg=msg, total=total, failture_count=failture_count)
            if res:
                self.echo_info(public.lang("Notification has been sent"))
            else:
                self.echo_error(public.lang("Failed to send notification"))

    def send_notification(self, channel, title, msg="", total=0, failture_count=0):

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
                if ch in ["sms"]:
                    if total > 0 and failture_count > 0:
                        msg_data["sm_type"] = "backup_all"
                        msg_data["sm_args"] = {
                            "panel_name": public.GetConfigValue('title'),
                            "task_name": self.cron_info["name"],
                            "failed_count": failture_count,
                            "total": total
                        }
                    else:
                        msg_data["sm_type"] = "backup"
                        msg_data["sm_args"] = {
                            "panel_name": public.GetConfigValue('title'),
                            "task_name": self.cron_info["name"]
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
                self.echo_error("Notification:{} Failed send!".format(",".join(error_channel)))
            else:
                self.echo_info("Message sent successfully.")
            if error_count == len(tongdao):
                return False
            return True
        except Exception as e:
            import traceback
            print(traceback.format_exc())
        return False

    def send_notification2(self, channel, title, msg={}):
        try:
            from send_mail import send_mail
            from config import config
            tondao = []
            if channel.find(",") >= 0:
                tongdao = channel.split(",")
            else:
                tongdao = [channel]

            sm = send_mail()
            c = config()
            send_res = []
            error_count = 0
            channel_names = {
                "mail": "email",
                "telegram": "telegram"
            }
            error_channel = []
            # settings = sm.get_settings()
            settings = c.get_settings2()
            for td in tongdao:
                _res = False
                if td == "mail":
                    if len(settings["user_mail"]['mail_list']) == 0:
                        continue
                    mail_list = settings['user_mail']['mail_list']
                    if len(mail_list) == 1:
                        mail_list = mail_list[0]
                    _res = sm.qq_smtp_send(mail_list, title=title, body=msg['mail'].replace("\n", "<br/>"))
                    if not _res:
                        error_count += 1
                        error_channel.append(channel_names[td])
                if td == "telegram":
                    import panel_telegram_bot
                    if not settings["telegram"]['setup']:
                        continue
                    _res = panel_telegram_bot.panel_telegram_bot().send_by_tg_bot(msg['tg'])
                    send_res.append(_res)
                    if not _res:
                        error_count += 1
                        error_channel.append(channel_names[td])
            if error_count > 0:
                print("Notification:{} failed to send".format(",".join(error_channel)))
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
            print("Backup status saving error :{}.".format(e))

