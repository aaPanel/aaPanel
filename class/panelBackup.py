#coding: utf-8
#-------------------------------------------------------------------
# 宝塔Linux面板
#-------------------------------------------------------------------
# Copyright (c) 2015-2099 宝塔软件(http://bt.cn) All rights reserved.
#-------------------------------------------------------------------
# Author: hwliang <hwl@bt.cn>
#-------------------------------------------------------------------

#------------------------------
# 数据备份模块
#------------------------------
import os
import sys
import json
import re
import time

os.chdir('/www/server/panel')
if not 'class/' in sys.path:
    sys.path.insert(0,'class/')
import public
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
    def __init__(self,cloud_object=None, cron_info={}):
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
        self._path = public.M('config').where("id=?",(1,)).getField('backup_path')

    def echo_start(self):
        print("="*90)
        print("★"+public.getMsg('START_BACKUP')+"[{}]".format(public.format_date()))
        print("="*90)

    def echo_end(self):
        print("="*90)
        print("☆"+public.getMsg('BACKUP_COMPLETED')+"[{}]".format(public.format_date()))
        print("="*90)
        print("\n")

    def echo_info(self,msg):
        print("|-{}".format(msg))

    def echo_error(self,msg):
        print("=" * 90)
        print("|-Error：{}".format(msg))
        if self._error_msg:
            self._error_msg += "\n"
        self._error_msg += msg

    #构造排除
    def get_exclude(self,exclude = []):
        if not exclude:
            tmp_exclude = os.getenv('BT_EXCLUDE')
            if tmp_exclude:
                exclude = tmp_exclude.split(',')
        if not exclude: return ""
        for ex in exclude:
            self._exclude += " --exclude=\"" + ex + "\""
        self._exclude += " "
        return self._exclude

    def GetDiskInfo2(self):
        #取磁盘分区信息
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
                inodes = tempInodes1[n-1].split()
                disk = re.findall(r"^(.+)\s+([\w\.]+)\s+([\w\.]+)\s+([\w\.]+)\s+([\w\.]+)\s+([\d%]{2,4})\s+(/.{0,50})$",tmp.strip())
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
                tmp1 = [disk[2],disk[3],disk[4],disk[5]]
                arr['size'] = tmp1
                if int(inodes[1]) == 0 and int(inodes[2]) == 0:
                    arr['inodes'] = [inodes[1],10000,10000,0]
                else:
                    arr['inodes'] = [inodes[1],inodes[2],inodes[3],inodes[4]]
                diskInfo.append(arr)
            except:
                continue
        return diskInfo

    #取磁盘可用空间
    def get_disk_free(self,dfile):
        diskInfo = self.GetDiskInfo2()
        if not diskInfo: return '',0,0
        _root = None
        for d in diskInfo:
            if d['path'] == '/': 
                _root = d
                continue
            if re.match("^{}/.+".format(d['path']),dfile):
                return d['path'],float(d['size'][2]) * 1024,int(d['inodes'][2])
        if _root:
            return _root['path'],float(_root['size'][2]) * 1024,int(_root['inodes'][2])
        return '',0,0

    #备份指定目录 
    def backup_path(self,spath,dfile = None,exclude=[],save=3):

        error_msg = ""
        self.echo_start()
        if not os.path.exists(spath):
            error_msg= public.getMsg('BACKUP_DIR_NOT_EXIST',(spath,))
            self.echo_error(error_msg)
            self.send_failture_notification(error_msg)
            return False

        if spath[-1] == '/':
            spath = spath[:-1]

        dirname = os.path.basename(spath)
        if not dfile:
            fname = 'path_{}_{}.tar.gz'.format(dirname,public.format_date("%Y%m%d_%H%M%S"))
            dfile = os.path.join(self._path,'path',fname)
        
        if not self.backup_path_to(spath,dfile,exclude):
            if self._error_msg:
                error_msg = self._error_msg
            self.send_failture_notification(error_msg)
            return False

        if self._cloud:
            self.echo_info(public.getMsg("BACKUP_UPLOADING",(self._cloud._title,)))
            if self._cloud.upload_file(dfile,'path'):
                self.echo_info(public.getMsg("BACKUP_UPLOAD_SUCCESS",(self._cloud._title,)))
            else:
                if hasattr(self._cloud, "error_msg"):
                    if self._cloud.error_msg:
                        error_msg = self._cloud.error_msg
                if not error_msg:
                    error_msg = public.getMsg('BACKUP_UPLOAD_FAILED')
                self.echo_error(error_msg)
                if os.path.exists(dfile):
                    os.remove(dfile)

                remark = "Backup to " + self._cloud._title
                self.send_failture_notification(error_msg, remark=remark)
                return False

        filename = dfile
        if self._cloud:
            filename = dfile + '|' + self._cloud._name + '|' + fname

        pdata = {
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

            if _not_save_local:
                if os.path.exists(dfile):
                    os.remove(dfile)
                    self.echo_info(public.getMsg("BACKUP_DEL",(dfile,)))
            else:
                self.echo_info(public.getMsg('KEEP_LOCAL'))

        if not self._cloud:
            backups = public.M('backup').where("type=? and pid=? and name=? and filename NOT LIKE '%|%'",('2',0,spath)).field('id,name,filename').select()
        else:
            backups = public.M('backup').where("type=? and pid=? and name=? and filename LIKE '%{}%'".format(self._cloud._name),('2',0,spath)).field('id,name,filename').select()

        self.delete_old(backups,save,'path')
        self.echo_end()
        return dfile

    
    #清理过期备份文件
    def delete_old(self,backups,save,data_type = None):
        if type(backups) == str:
            self.echo_info(public.getMsg('BACKUP_CLEAN_ERR',(backups,)))
            return
        self.echo_info(public.getMsg('BACKUP_KEEP',(str(save),)))
        num = len(backups) - int(save)
        if  num > 0:
            self._get_local_backdir()
            self.echo_info('-' * 88)
            for backup in backups:
                #处理目录备份到远程的情况
                if backup['filename'].find('|') != -1:
                    tmp = backup['filename'].split('|')
                    backup['filename'] = tmp[0]
                    backup['name'] = tmp[-1]
                #尝试删除本地文件
                if os.path.exists(backup['filename']):
                    try:
                        os.remove(self._local_backdir + '/'+ data_type +'/' + backup['name'])
                    except:
                        pass
                    self.echo_info(public.getMsg("BACKUP_CLEAN",(backup['filename'],)))
                #尝试删除远程文件
                if self._cloud:
                    self._cloud.delete_file(backup['name'],data_type)
                    self.echo_info(public.getMsg("BACKUP_CLEAN_REMOVE",(self._cloud._title,backup['name'])))

                #从数据库清理
                public.M('backup').where('id=?',(backup['id'],)).delete()
                num -= 1
                if num < 1: break

    # 获取本地备份目录
    def _get_local_backdir(self):
        self._local_backdir = public.M('config').field('backup_path').find()['backup_path']

    #压缩目录
    def backup_path_to(self,spath,dfile,exclude = [],siteName = None):
        if not os.path.exists(spath):
            self.echo_error(public.getMsg('BACKUP_DIR_NOT_EXIST',(spath,)))
            return False

        if spath[-1] == '/':
            spath = spath[:-1]

        dirname = os.path.basename(spath)
        dpath = os.path.dirname(dfile)
        if not os.path.exists(dpath):
            os.makedirs(dpath,384)
        
        p_size = public.get_path_size(spath)
        self.get_exclude(exclude)
        exclude_config = self._exclude
        if not self._exclude:
            exclude_config = "Not set"
        
        if siteName:
            self.echo_info(public.getMsg('BACKUP_SITE',(siteName,)))
            self.echo_info(public.getMsg('WEBSITE_DIR',(spath,)))
        else:
            self.echo_info(public.getMsg('BACKUP_DIR',(spath,)))
        
        self.echo_info(public.getMsg(
            "DIR_SIZE",
            (str(public.to_size(p_size),))
        ))
        self.echo_info(public.getMsg('BACKUP_EXCLUSION',(exclude_config,)))
        disk_path,disk_free,disk_inode = self.get_disk_free(dfile)
        self.echo_info(public.getMsg(
            "PARTITION_INFO",
            (disk_path,str(public.to_size(disk_free)),str(disk_inode))
        ))
        if disk_path:
            if disk_free < p_size:
                self.echo_error(public.getMsg(
                    "PARTITION_LESS_THEN",
                    (str(public.to_size(p_size)),)
                ))
                return False

            if disk_inode < self._inode_min:
                self.echo_error(public.getMsg(
                    "INODE_LESS_THEN",
                    (str(self._inode_min,))
                ))
                return False

        stime = time.time()
        self.echo_info(public.getMsg("START_COMPRESS",(public.format_date(times=stime),)))
        if os.path.exists(dfile):
            os.remove(dfile)
        public.ExecShell("cd " + os.path.dirname(spath) + " && tar zcvf '" + dfile + "' " + self._exclude + " '" + dirname + "' 2>{err_log} 1> /dev/null".format(err_log = self._err_log))
        tar_size = os.path.getsize(dfile)
        if tar_size < 1:
            self.echo_error(public.getMsg('ZIP_ERR'))
            self.echo_info(public.readFile(self._err_log))
            return False
        compression_time = str('{:.2f}'.format(time.time() - stime))
        self.echo_info(public.getMsg(
            'COMPRESS_TIME',
            (compression_time,str(public.to_size(tar_size)))
        ))
        if siteName:
            self.echo_info(public.getMsg("WEBSITE_BACKUP_TO",(dfile,)))
        else:
            self.echo_info(public.getMsg("DIR_BACKUP_TO",(dfile,)))
        if os.path.exists(self._err_log):
            os.remove(self._err_log)
        return dfile

    #备份指定站点
    def backup_site(self,siteName,save = 3 ,exclude = []):
        self.echo_start()
        find = public.M('sites').where('name=?',(siteName,)).field('id,path').find()
        spath = find['path']
        pid = find['id']
        fname = 'web_{}_{}.tar.gz'.format(siteName,public.format_date("%Y%m%d_%H%M%S"))
        dfile = os.path.join(self._path,'site',fname)
        error_msg = ""
        if not self.backup_path_to(spath,dfile,exclude,siteName=siteName):
            if self._error_msg:
                error_msg = self._error_msg
            self.send_failture_notification(error_msg)
            return False
        if self._cloud:
            self.echo_info(public.getMsg("BACKUP_UPLOADING",(self._cloud._title,)))
            if self._cloud.upload_file(dfile,'site'):
                self.echo_info(public.getMsg("BACKUP_UPLOAD_SUCCESS",(self._cloud._title,)))
            else:
                if hasattr(self._cloud, "error_msg"):
                    if self._cloud.error_msg:
                        error_msg = self._cloud.error_msg
                if not error_msg:
                    error_msg = public.getMsg('BACKUP_UPLOAD_FAILED')
                self.echo_error(error_msg)
                if os.path.exists(dfile):
                    os.remove(dfile)

                remark = "Backup to " + self._cloud._title
                self.send_failture_notification(error_msg, remark=remark)
                return False

        filename = dfile
        if self._cloud:
            filename = dfile + '|' + self._cloud._name + '|' + fname

        pdata = {
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

            if _not_save_local:
                if os.path.exists(dfile):
                    os.remove(dfile)
                    self.echo_info(public.getMsg("BACKUP_DEL",(dfile,)))
            else:
                self.echo_info(public.getMsg('KEEP_LOCAL'))

        #清理多余备份
        if not self._cloud:
            backups = public.M('backup').where("type=? and pid=? and filename NOT LIKE '%|%'",('0',pid)).field('id,name,filename').select()
        else:
            backups = public.M('backup').where('type=? and pid=? and filename LIKE "%{}%"'.format(self._cloud._name),('0',pid)).field('id,name,filename').select()

        self.delete_old(backups,save,'site')
        self.echo_end()
        return dfile

    #备份所有数据库
    def backup_database_all(self,save = 3):
        databases = public.M('databases').field('name').select()
        self._backup_all = True
        failture_count = 0
        results = []
        for database in databases:
            self._error_msg = ""
            result = self.backup_database(database['name'],save=save)
            if not result:
                failture_count += 1
            results.append((database['name'], result, self._error_msg,))

        if failture_count > 0:
            self.send_all_failture_notification("database", results)
        self._backup_all = False

    #备份所有站点
    def backup_site_all(self,save = 3):
        sites = public.M('sites').field('name').select()
        self._backup_all = True
        failture_count = 0
        results = []
        for site in sites:
            self._error_msg = ""
            result = self.backup_site(site['name'],save)
            if not result:
                failture_count += 1
            results.append((site['name'], result, self._error_msg,))

        if failture_count > 0:
            self.send_all_failture_notification("site", results)
        self._backup_all = False

    #配置
    def mypass(self,act):
        conf_file = '/etc/my.cnf'
        conf_file_bak = '/etc/my.cnf.bak'
        if os.path.getsize(conf_file) > 2:
            public.writeFile(conf_file_bak,public.readFile(conf_file))
            public.set_mode(conf_file_bak,600)
            public.set_own(conf_file_bak,'mysql')
        elif os.path.getsize(conf_file_bak) > 2:
            public.writeFile(conf_file,public.readFile(conf_file_bak))
            public.set_mode(conf_file,600)
            public.set_own(conf_file,'mysql')

        public.ExecShell("sed -i '/user=root/d' {}".format(conf_file))
        public.ExecShell("sed -i '/password=/d' {}".format(conf_file))
        if act:
            password = public.M('config').where('id=?',(1,)).getField('mysql_root')
            mycnf = public.readFile(conf_file)
            if not mycnf: return False
            src_dump_re = r"\[mysqldump\][^.]"
            sub_dump = "[mysqldump]\nuser=root\npassword=\"{}\"\n".format(password)
            mycnf = re.sub(src_dump_re, sub_dump, mycnf)
            if len(mycnf) > 100: public.writeFile(conf_file,mycnf)
            return True
        return True

    #map to list
    def map_to_list(self,map_obj):
        try:
            if type(map_obj) != list and type(map_obj) != str: map_obj = list(map_obj)
            return map_obj
        except: return []

    #备份指定数据库
    def backup_database(self,db_name,dfile = None,save=3):
        self.echo_start()
        if not dfile:
            fname = 'db_{}_{}.sql.gz'.format(db_name,public.format_date("%Y%m%d_%H%M%S"))
            dfile = os.path.join(self._path,'database',fname)
        else:
            fname = os.path.basename(dfile)
        
        dpath = os.path.dirname(dfile)
        if not os.path.exists(dpath):
            os.makedirs(dpath,384)

        error_msg = ""
        import panelMysql
        if not self._db_mysql:self._db_mysql = panelMysql.panelMysql()
        d_tmp = self._db_mysql.query("select sum(DATA_LENGTH)+sum(INDEX_LENGTH) from information_schema.tables where table_schema='%s'" % db_name)
        try:
            p_size = self.map_to_list(d_tmp)[0][0]
        except:
            error_msg = public.getMsg('DB_CONN_ERR')
            self.echo_error(error_msg)
            self.send_failture_notification(error_msg)
            return False
        
        if p_size == None:
            error_msg = public.getMsg('DB_BACKUP_ERR',(db_name,))
            self.echo_error(error_msg)
            self.send_failture_notification(error_msg)
            return False

        character = public.get_database_character(db_name)

        self.echo_info(public.getMsg('DB_BACKUP',(db_name,)))
        self.echo_info(public.getMsg("DB_SIZE",(public.to_size(p_size),)))
        self.echo_info(public.getMsg("DB_CHARACTER",(character,)))
        disk_path,disk_free,disk_inode = self.get_disk_free(dfile)
        self.echo_info(public.getMsg(
            "PARTITION_INFO",(
                disk_path,str(public.to_size(disk_free)),str(disk_inode)
            )
        ))
        if disk_path:
            if disk_free < p_size:
                error_msg = public.getMsg("PARTITION_LESS_THEN",(
                        str(public.to_size(p_size),)
                    ))
                self.echo_error(error_msg)
                self.send_failture_notification(error_msg)
                return False

            if disk_inode < self._inode_min:
                error_msg = public.getMsg("INODE_LESS_THEN",(self._inode_min,))
                self.echo_error(error_msg)
                self.send_failture_notification(error_msg)
                return False
        
        stime = time.time()
        self.echo_info(public.getMsg("EXPORT_DB",(public.format_date(times=stime),)))
        if os.path.exists(dfile):
            os.remove(dfile)
        #self.mypass(True)
        try:
            password = public.M('config').where('id=?',(1,)).getField('mysql_root')
            os.environ["MYSQL_PWD"] = password
            backup_cmd = "/www/server/mysql/bin/mysqldump -E -R --default-character-set="+ character +" --force --hex-blob --opt " + db_name + " -u root" + " 2>"+self._err_log+"| gzip > " + dfile
            public.ExecShell(backup_cmd)
        except Exception as e:
            raise
        finally:
            os.environ["MYSQL_PWD"] = ""
        #public.ExecShell("/www/server/mysql/bin/mysqldump --default-character-set="+ character +" --force --hex-blob --opt " + db_name + " 2>"+self._err_log+"| gzip > " + dfile)
        #self.mypass(False)
        gz_size = os.path.getsize(dfile)
        if gz_size < 400:
            error_msg = public.getMsg("EXPORT_DB_ERR")
            self.echo_error(error_msg)
            self.send_failture_notification(error_msg)
            self.echo_info(public.readFile(self._err_log))
            return False
        compressed_time = str('{:.2f}'.format(time.time() - stime))
        self.echo_info(
            public.getMsg("COMPRESS_TIME",(str(compressed_time),
            str(public.to_size(gz_size))
            ))
        )
        if self._cloud:
            self.echo_info(public.getMsg("BACKUP_UPLOADING",(self._cloud._title,)))
            if self._cloud.upload_file(dfile, 'database'):
                self.echo_info(public.getMsg("BACKUP_UPLOAD_SUCCESS",(self._cloud._title,)))
            else:
                if hasattr(self._cloud, "error_msg"):
                    if self._cloud.error_msg:
                        error_msg = self._cloud.error_msg
                if not error_msg:
                    error_msg = public.getMsg('BACKUP_UPLOAD_FAILED')
                self.echo_error(error_msg)
                if os.path.exists(dfile):
                    os.remove(dfile)

                remark = "Backup to " + self._cloud._title
                self.send_failture_notification(error_msg, remark=remark)
                return False

        filename = dfile
        if self._cloud:
            filename = dfile + '|' + self._cloud._name + '|' + fname
        self.echo_info(public.getMsg("DB_BACKUP_TO",(dfile,)))
        if os.path.exists(self._err_log):
            os.remove(self._err_log)

        pid = public.M('databases').where('name=?',(db_name)).getField('id')
        pdata = {
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

            if _not_save_local:
                if os.path.exists(dfile):
                    os.remove(dfile)
                    self.echo_info(public.getMsg("BACKUP_DEL",(dfile,)))
            else:
                self.echo_info(public.getMsg('KEEP_LOCAL'))

        #清理多余备份
        if not self._cloud:
            backups = public.M('backup').where("type=? and pid=? and filename NOT LIKE '%|%'",('1',pid)).field('id,name,filename').select()
        else:
            backups = public.M('backup').where('type=? and pid=? and filename LIKE "%{}%"'.format(self._cloud._name),('1',pid)).field('id,name,filename').select()
        self.delete_old(backups,save,'database')
        self.echo_end()
        return dfile

    def generate_success_title(self, task_name):
        from send_mail import send_mail
        sm = send_mail()
        now = public.format_date(format="%Y-%m-%d %H:%M")
        server_ip = sm.GetLocalIp()
        title = public.getMsg("BACKUP_TASK_TITLE",(server_ip, task_name))
        return title

    def generate_failture_title(self):
        title = "aaPanel backup task failed reminder"
        return title

    def generate_all_failture_notice(self, task_name, msg, backup_type, remark=""):
        # from send_mail import send_mail
        # sm = send_mail()
        now = public.format_date(format="%Y-%m-%d %H:%M:%S")
        server_ip = public.GetLocalIp()
        if remark:
            remark = "\n* Task notes: {}".format(remark)

        notice_content = """Hello,
                         aaPanel reminds you that the cron you set failed to execute:
                         * Server IP: {}
                         * Time: {}
                         * Task name: {}{}
                         * The following is a list of {} that failed to backup:
                         <table style="color:red;">
                         {}
                         </table>
                         Please deal with it as soon as possible to avoid unnecessary trouble due to the failure of the backup task.
                         - Notification by aaPanel""".format(
                        server_ip, now, task_name, remark, backup_type, msg)
        return notice_content

    def generate_failture_notice(self, task_name, msg, remark):
        # from send_mail import send_mail
        # sm = send_mail()
        now = public.format_date(format="%Y-%m-%d %H:%M:%S")
        server_ip = public.GetLocalIp()
        if remark:
            remark = "\n* Task notes: {}".format(remark)

        notice_content = """Hello,
                         aaPanel reminds you that the cron you set failed to execute:
                        * Server IP: {}
                        * Time: {}
                        * Task name:{}{}
                        * Error messages：
                        <span style="color:red;">
                        {}
                        </span>
                        Please deal with it as soon as possible to avoid unnecessary trouble due to the failure of the backup task.
                        -- Notification by aaPanel""".format(
                        server_ip, now, task_name, remark, msg)
        return notice_content

    def get_cron_info(self, cron_name):
        """ 通过计划任务名称查找计划任务配置参数 """
        try:
            cron_info  = public.M('crontab').where('echo=?',(cron_name,))\
            .field('name,save_local,notice,notice_channel').find()
            return cron_info
        except Exception as e:
            pass
        return {}

    def send_failture_notification(self, error_msg, remark=""):
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
        if notice == 0 or not notice_channel:
            return

        if notice == 1 or notice == 2:
            title = self.generate_failture_title()
            task_name = cron_title
            msg = self.generate_failture_notice(task_name, error_msg, remark)
            res = self.send_notification(notice_channel, title, msg)
            if res:
                self.echo_info(public.getMsg('NOTIFICATION_SENT'))

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
            title = self.generate_failture_title()
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
                    content += "<tr><td style='color:red'>{}</td><tr>".format(obj_name)

            if failture_count > 0:
                if self._cloud:
                    remark = public.getMsg("BACKUP_MSG"),(
                   self._cloud._title, total, backup_type_desc, failture_count)
                else:
                        remark = public.getMsg("BACKUP_MSG1"),(
                        failture_count, total, backup_type_desc)

            msg = self.generate_all_failture_notice(task_name, content, backup_type_desc, remark)
            res = self.send_notification(notice_channel, title, msg)
            if res:
                self.echo_info(public.getMsg('NOTIFICATION_SENT'))
            else:
                self.echo_error(public.getMsg('NOTIFICATION_ERR'))

    def send_notification(self, channel, title, msg = ""):
        try:
            from send_mail import send_mail
            tondao = []
            if channel.find(",") >= 0:
                tongdao = channel.split(",")
            else:
                tongdao = [channel]

            sm = send_mail()
            send_res = []
            error_count = 0
            channel_names = {
                "mail": "email",
                # "dingidng": "钉钉"
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
                print("Notification:{} failed to send".format(",".join(error_channel)))
            if error_count == len(tongdao):
                return False
            return True
        except Exception as e:
            print(e)
        return False

    
