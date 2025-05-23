#coding: utf-8
#-------------------------------------------------------------------
# aaPanel
#-------------------------------------------------------------------
# Copyright (c) 2015-2099 aaPanel(www.aapanel.com) All rights reserved.
#-------------------------------------------------------------------
# Author: hwliang <hwl@aapanel.com>
#-------------------------------------------------------------------

#------------------------------
# sqlite模型
#------------------------------
import os,re,json,time
from databaseModelV2.base import databaseBase


# import public,panelMssql
import public
import panel_mssql_v2 as panelMssql


from public.validate import Param
try:
    from BTPanel import session
except :pass


class main(databaseBase):

    def get_list(self,args):
        """
        @获取数据库列表
        @sql_type = sqlserver
        """
        # {"table":"databases","search":"","limit":"10","p":1,"order":"username desc"}
        # 校验参数
        try:
            args.validate([
                Param('table').Require().String(),
                Param('search').String(),
                Param('order').String(),
                Param('limit').Integer(),
                Param('p').Integer(),
            ], [
                public.validate.trim_filter(),
            ])
        except Exception as ex:
            public.print_log("error info: {}".format(ex))
            return public.return_message(-1, 0, str(ex))

        # return self.get_base_list(args, sql_type = 'sqlserver')
        return public.return_message(0, 0, self.get_base_list(args, sql_type = 'sqlserver'))


    def get_mssql_obj_by_sid(self,sid = 0,conn_config = None):
        """
        @取mssql数据库对像 By sid
        @sid 数据库分类，0：本地
        """
        if type(sid) == str:
            try:
                sid = int(sid)
            except :sid = 0

        if sid:
            if not conn_config: conn_config = public.M('database_servers').where("id=?" ,sid).find()
            db_obj = panelMssql.panelMssql()

            try:
                db_obj = db_obj.set_host(conn_config['db_host'],conn_config['db_port'],None,conn_config['db_user'],conn_config['db_password'])
            except Exception as e:
                raise public.PanelError(e)
        else:
            db_obj = panelMssql.panelMssql()
        return db_obj

    def get_mssql_obj(self,db_name):
        """
        @取mssql数据库对象
        @db_name 数据库名称
        """
        is_cloud_db = False
        if db_name:
            db_find = public.M('databases').where("name=?" ,db_name).find()
            if db_find['sid']:
                return self.get_mssql_obj_by_sid(db_find['sid'])
            is_cloud_db = db_find['db_type'] in ['1',1]

        if is_cloud_db:

            db_obj = panelMssql.panelMssql()
            conn_config = json.loads(db_find['conn_config'])
            try:
                db_obj = db_obj.set_host(conn_config['db_host'],conn_config['db_port'],conn_config['db_name'],conn_config['db_user'],conn_config['db_password'])
            except Exception as e:
                raise public.PanelError(e)
        else:
            db_obj = panelMssql.panelMssql()
        return db_obj

    def GetCloudServer(self,args):
        '''
            @name 获取远程服务器列表
            @author hwliang<2021-01-10>
            @return list
        '''
        # {"type":"sqlserver"}
        # 校验参数
        try:
            args.validate([

                Param('type').Require().String('in', ['sqlserver']),
            ], [
                public.validate.trim_filter(),
            ])
        except Exception as ex:
            public.print_log("error info: {}".format(ex))
            return public.return_message(-1, 0, str(ex))

        # return self.GetBaseCloudServer(args)
        return public.return_message(0, 0, self.GetBaseCloudServer(args))


    def AddCloudServer(self,args):
        '''
        @添加远程数据库
        '''

        return self.AddBaseCloudServer(args)
        # return public.return_message(0, 0, self.AddBaseCloudServer(args))

    def RemoveCloudServer(self,args):
        '''
        @删除远程数据库
        '''
        return self.RemoveBaseCloudServer(args)
        # return public.return_message(0, 0, self.RemoveBaseCloudServer(args))

    def ModifyCloudServer(self,args):
        '''
        @修改远程数据库
        '''
        return self.ModifyBaseCloudServer(args)
        # return public.return_message(0, 0, self.ModifyBaseCloudServer(args))

    def AddDatabase(self,args):
        """
        @添加数据库
        """
        # {"name":"test1","db_user":"test1","password":"nnMCp2ccJcBahJec","sid":"3","active":true,"ps":"test1","ssl":"REQUIRE SSL"}
        # 校验参数
        try:
            args.validate([
                Param('name').Require().String(),
                Param('db_user').Require().String(),
                Param('password').Require().String(),
                Param('sid').Require().Integer(),
                Param('active').Require().Bool(),
                Param('ps').String(),
                Param('ssl').String(),
            ], [
                public.validate.trim_filter(),
            ])
        except Exception as ex:
            public.print_log("error info: {}".format(ex))
            return public.return_message(-1, 0, str(ex))


        try:
            res = self.add_base_database(args)
            if not res['status']:
                # return res
                return public.return_message(-1, 0,  res['msg'])

            data_name = res['data_name']
            username = res['username']
            password = res['data_pwd']

            if re.match(r"^\d+",data_name):
                # return public.returnMsg(False, public.lang("SQLServer databases cannot start with numbers!"))
                return public.return_message(-1, 0, public.lang("SQLServer databases cannot start with numbers!"))

            reg_count = 0
            regs = ['[a-z]','[A-Z]',r'\W','[0-9]']
            for x in regs:
                if re.search(x,password): reg_count += 1

            if len(password) < 8 or len(password) >128 or reg_count < 3 :
                # return public.returnMsg(False, public.lang("SQLServer password complexity policy does not match, should be 8-128 characters, and contain any 3 of them in upper case, lower case, digits, special symbols!"))
                return public.return_message(-1, 0, 'SQLServer password complexity policy does not match, should be 8-128 '
                                                    'characters, and contain any 3 of them in upper case, lower case, '
                                                    'digits, special symbols!')

            try:
                self.sid = int(args['sid'])
            except :
                self.sid = 0

            dtype = 'SQLServer'
            #添加SQLServer
            mssql_obj = self.get_mssql_obj_by_sid(self.sid)
            result = mssql_obj.execute("CREATE DATABASE %s" % data_name)
            isError = self.IsSqlError(result)
            if  isError != None:
                return isError
                # return public.return_message(-1, 0, isError)

            mssql_obj.execute("DROP LOGIN %s" % username)

            #添加用户
            self.__CreateUsers(data_name,username,password,'127.0.0.1')

            if not hasattr(args,'ps'): args['ps'] = public.getMsg('INPUT_PS');
            addTime = time.strftime('%Y-%m-%d %X',time.localtime())

            pid = 0
            if hasattr(args,'pid'): pid = args.pid

            if hasattr(args,'contact'):
                site = public.M('sites').where("id=?",(args.contact,)).field('id,name').find()
                if site:
                    pid = int(args.contact)
                    args['ps'] = site['name']

            db_type = 0
            if self.sid: db_type = 2

            public.set_module_logs('linux_sqlserver','AddDatabase',1)
            #添加入SQLITE
            public.M('databases').add('pid,sid,db_type,name,username,password,accept,ps,addtime,type',(pid,self.sid,db_type,data_name,username,password,'127.0.0.1',args['ps'],addTime,dtype))
            public.WriteLog("TYPE_DATABASE", 'DATABASE_ADD_SUCCESS',(data_name,))
            # return public.returnMsg(True, public.lang("Added successfully!"))
            return public.return_message(0, 0, public.lang("Added successfully!"))
        except Exception as ex:
            public.print_log("error info: {}".format(ex))
            return public.return_message(-1, 0, str(ex))

    def DeleteDatabase(self,args):
        """
        @删除数据库
        """
        # {"id":128,"name":"失去了23"}
        # 校验参数
        try:
            args.validate([
                Param('name').Require().String(),
                Param('id').Require().Integer(),
            ], [
                public.validate.trim_filter(),
            ])
        except Exception as ex:
            public.print_log("error info: {}".format(ex))
            return public.return_message(-1, 0, str(ex))

        id = args['id']
        find = public.M('databases').where("id=?",(id,)).field('id,pid,name,username,password,type,accept,ps,addtime,sid,db_type').find();
        if not find:
            # return public.returnMsg(False, public.lang("The specified database does not exist."))
            return public.return_message(-1, 0, public.lang("The specified database does not exist."))

        name = args['name']
        username = find['username']

        mssql_obj = self.get_mssql_obj_by_sid(find['sid'])
        mssql_obj.execute("ALTER DATABASE %s SET SINGLE_USER with ROLLBACK IMMEDIATE" % name)
        result = mssql_obj.execute("DROP DATABASE %s" % name)

        if self.get_database_size_by_id(find['sid']):
            isError = self.IsSqlError(result)
            if  isError != None:
                return isError
                # return public.return_message(-1, 0, isError)

        mssql_obj.execute("DROP LOGIN %s" % username)

        #删除SQLITE
        public.M('databases').where("id=?",(id,)).delete()
        public.WriteLog("TYPE_DATABASE", 'DATABASE_DEL_SUCCESS',(name,))
        # return public.returnMsg(True, public.lang("Delete successfully!"))
        return public.return_message(0, 0, public.lang("Delete successfully!"))



    def ToBackup(self,args):
        """
        @备份数据库 id 数据库id
        """


        id = args['id']
        find = public.M('databases').where("id=?",(id,)).find()
        if not find:
            # return public.returnMsg(False, public.lang("Database does not exist!"))
            return public.return_message(-1, 0, public.lang("Database does not exist!"))

        self.CheckBackupPath(args)

        fileName = find['name'] + '_' + time.strftime('%Y%m%d_%H%M%S',time.localtime()) + '.bak'
        backupName = session['config']['backup_path'] + '/database/sqlserver/' + fileName

        mssql_obj = self.get_mssql_obj_by_sid(find['sid'])

        if not int(find['sid']):
            ret = mssql_obj.execute("backup database %s To disk='%s'" % (find['name'],backupName))
            isError=self.IsSqlError(ret)
            if  isError != None:
                return isError
                # return public.return_message(-1, 0, isError)
        else:
            #远程数据库
            # return public.returnMsg(False, public.lang("Operation failed. Remote database cannot be backed up."))
            return public.return_message(-1, 0, public.lang("Operation failed. Remote database cannot be backed up."))

        if not os.path.exists(backupName):
            # return public.returnMsg(False, public.lang("Backup error"))
            return public.return_message(-1, 0, public.lang("Backup error"))

        public.M('backup').add('type,name,pid,filename,size,addtime',(1,fileName,id,backupName,0,time.strftime('%Y-%m-%d %X',time.localtime())))
        public.WriteLog("TYPE_DATABASE", "DATABASE_BACKUP_SUCCESS",(find['name'],))

        if os.path.getsize(backupName) < 2048:
            # return public.returnMsg(True, public.lang("The backup file size is smaller than 2Kb. Check the backup integrity."))
            return public.return_message(0, 0, public.lang("The backup file size is smaller than 2Kb. Check the backup integrity."))
        else:
            # return public.returnMsg(True, public.lang("Backup Succeeded!"))
            return public.return_message(0, 0, public.lang("Backup Succeeded!"))

    def DelBackup(self,args):
        """
        @删除备份文件
        """
        return self.delete_base_backup(args)
        # return public.return_message(0, 0, self.delete_base_backup(args))


    #导入
    def InputSql(self,get):
        # 校验参数
        try:
            get.validate([
                Param('file').SafePath(),   # 文件路径
                Param('name').String(),
            ], [
                public.validate.trim_filter(),
            ])
        except Exception as ex:
            public.print_log("error info: {}".format(ex))
            return public.return_message(-1, 0, str(ex))

        name = get.name
        file = get.file

        find = public.M('databases').where("name=?",(name,)).find()
        if not find:
            # return public.returnMsg(False, public.lang("Database does not exist!"))
            return public.return_message(-1, 0, public.lang("Database does not exist!"))

        tmp = file.split('.')
        exts = ['sql','zip','bak']
        ext = tmp[len(tmp) -1]
        if ext not in exts:
            # return public.returnMsg(False, public.lang("DATABASE_INPUT_ERR_FORMAT"))
            return public.return_message(-1, 0, public.lang("Select sql、gz、zip file!"))

        backupPath = session['config']['backup_path'] + '/database'

        if ext == 'zip':
            try:
                fname = os.path.basename(file).replace('.zip','')
                dst_path = backupPath + '/' +fname
                if not os.path.exists(dst_path): os.makedirs(dst_path)

                public.unzip(file,dst_path)
                for x in os.listdir(dst_path):
                    if x.find('bak') >= 0 or x.find('sql') >= 0:
                        file = dst_path + '/' + x
                        break
            except :
                # return public.returnMsg(False, public.lang("The import failed because the file is not a valid ZIP file."))
                return public.return_message(-1, 0, public.lang("The import failed because the file is not a valid ZIP file."))

        mssql_obj = self.get_mssql_obj_by_sid(find['sid'])
        data = mssql_obj.query("use %s ;select filename from sysfiles" % find['name'])

        isError = self.IsSqlError(data)
        if isError != None:
            return isError
            # return public.return_message(-1, 0, isError)
        if type(data) == str:
            # return public.returnMsg(False,data)
            return public.return_message(-1, 0, data)

        mssql_obj.execute("ALTER DATABASE %s SET OFFLINE WITH ROLLBACK IMMEDIATE" % (find['name']))
        mssql_obj.execute("use master;restore database %s from disk='%s' with replace, MOVE N'%s' TO N'%s',MOVE N'%s_Log'  TO N'%s' " % (find['name'],file,find['name'],data[0][0],find['name'],data[1][0]))
        mssql_obj.execute("ALTER DATABASE %s SET ONLINE" % (find['name']))

        public.WriteLog("TYPE_DATABASE", 'Description Succeeded in importing database [{}]'.format(name))
        # return public.returnMsg(True, public.lang("DATABASE_INPUT_SUCCESS"))
        return public.return_message(0, 0, public.lang("Successfully imported database!"))


    #同步数据库到服务器
    def SyncToDatabases(self,get):

        # 校验?

        type = int(get['type'])
        n = 0
        sql = public.M('databases')
        if type == 0:
            data = sql.field('id,name,username,password,accept,type,sid,db_type').where('type=?',('SQLServer',)).select()

            for value in data:
                if value['db_type'] in ['1',1]:
                    continue  # 跳过远程数据库
                result = self.ToDataBase(value)
                if result == 1: n +=1
        else:
            import json
            data = json.loads(get.ids)
            for value in data:
                find = sql.where("id=?",(value,)).field('id,name,username,password,sid,db_type,accept,type').find()
                result = self.ToDataBase(find)
                if result == 1: n +=1

        if n == 1:
            # return public.returnMsg(True, public.lang("Synchronization succeeded"))
            return public.return_message(0, 0, public.lang("Synchronization succeeded"))

        elif n == 0:
            # return public.returnMsg(False, public.lang("Sync failed"))
            return public.return_message(-1, 0, public.lang("Sync failed"))

        # return public.returnMsg(True,'Database sync success',(str(n),))
        return public.return_message(0, 0, public.lang("Database sync success", str(n)))

    #添加到服务器
    def ToDataBase(self,find):

        if find['username'] == 'bt_default':
            # return 0
            return public.return_message(0, 0, 0)
        if len(find['password']) < 3 :
            find['username'] = find['name']
            find['password'] = public.md5(str(time.time()) + find['name'])[0:10]
            public.M('databases').where("id=?",(find['id'],)).save('password,username',(find['password'],find['username']))

        self.sid = find['sid']
        mssql_obj = self.get_mssql_obj_by_sid(self.sid)
        result = mssql_obj.execute("CREATE DATABASE %s" % find['name'])
        isError = self.IsSqlError(result)
        if  isError != None and not 'already exists' in result:
            # return -1
            return public.return_message(0, 0, -1)

        self.__CreateUsers(find['name'],find['username'],find['password'],'127.0.0.1')

        # return 1
        return public.return_message(0, 0, 1)


    #从服务器获取数据库
    def SyncGetDatabases(self,get):

        n = 0
        s = 0
        db_type = 0
        self.sid = get.get('sid/d',0)
        if self.sid: db_type = 2

        mssql_obj = self.get_mssql_obj_by_sid(self.sid)

        data = mssql_obj.query('SELECT name FROM MASTER.DBO.SYSDATABASES ORDER BY name')
        isError = self.IsSqlError(data)
        if isError != None:
            return isError
            # return public.return_message(-1, 0, isError)
        if type(data) == str:
            # return public.returnMsg(False,data)
            return public.return_message(-1, 0, data)

        sql = public.M('databases')
        nameArr = ['information_schema','performance_schema','mysql','sys','master','model','msdb','tempdb','ReportServerTempDB','YueMiao','ReportServer']
        for item in data:
            dbname = item[0]
            if sql.where("name=?",(dbname,)).count(): continue
            if not dbname in nameArr:
                if sql.table('databases').add('name,username,password,accept,ps,addtime,type,sid,db_type',(dbname,dbname,'','',public.getMsg('INPUT_PS'),time.strftime('%Y-%m-%d %X',time.localtime()),'SQLServer',self.sid,db_type)): n +=1

        # return public.returnMsg(True,'Database success',(str(n),))
        return public.return_message(0, 0, public.lang("Database success", n))

    def ResDatabasePassword(self,args):
        """
        @修改用户密码
        """
        # 校验参数
        try:
            args.validate([
                Param('password').Require().String(),
                Param('name').Require().String(),
                Param('id').Require().Integer(),
            ], [
                public.validate.trim_filter(),
            ])
        except Exception as ex:
            public.print_log("error info: {}".format(ex))
            return public.return_message(-1, 0, str(ex))


        id = args['id']
        username = args['name'].strip()
        newpassword = public.trim(args['password'])

        try:
            # if not newpassword:
            #     return public.returnMsg(False, public.lang("The password of database [' + username + '] cannot be empty."))
            if len(re.search(r"^[\w@\.]+$", newpassword).groups()) > 0:
                # return public.returnMsg(False, public.lang("The database password cannot be empty or contain special characters"))
                return public.return_message(-1, 0, public.lang("The database password cannot be empty or contain special characters"))
        except :
            # return public.returnMsg(False, public.lang("The database password cannot be empty or contain special characters"))
            return public.return_message(-1, 0, public.lang("The database password cannot be empty or contain special characters"))

        find = public.M('databases').where("id=?",(id,)).field('id,pid,name,username,password,type,accept,ps,addtime,sid').find()
        if not find:
            # return public.returnMsg(False, public.lang("Modify the failure，The specified database does not exist."));
            return public.return_message(-1, 0, public.lang("Modify the failure，The specified database does not exist."))

        mssql_obj = self.get_mssql_obj_by_sid(find['sid'])
        mssql_obj.execute("EXEC sp_password NULL, '%s', '%s'" % (newpassword,username))

        #修改SQLITE
        public.M('databases').where("id=?",(id,)).setField('password',newpassword)

        public.WriteLog("TYPE_DATABASE",'Database password success',(find['name'],))
        # return public.returnMsg(True, 'Database password success',(find['name'],))
        return public.return_message(0, 0, public.lang("Database password success", find['name']))


    def get_root_pwd(self,args):
        """
        @获取sa密码
        """
        mssql_obj = panelMssql.panelMssql()
        ret = mssql_obj.get_sql_name()
        if not ret : return public.returnMsg(False, public.lang("The SQL Server is not installed or started. Install or start it first"))

        sa_path = '{}/data/sa.pl'.format(public.get_panel_path())
        if os.path.exists(sa_path):
            password = public.readFile(sa_path)
            return public.returnMsg(True,password)
        return public.returnMsg(True, public.lang(""))


    def set_root_pwd(self,args):
        """
        @设置sa密码
        """
        password = public.trim(args['password'])
        try:
            if not password:
                return public.returnMsg(False, public.lang("The password of database [' + username + '] cannot be empty."))
            if len(re.search(r"^[\w@\.]+$", password).groups()) > 0:
                return public.returnMsg(False, public.lang("saThe password cannot be empty or have special symbols"))
        except :
            return public.returnMsg(False, public.lang("saThe password cannot be empty or have special symbols"))

        mssql_obj = panelMssql.panelMssql()
        result = mssql_obj.execute("EXEC sp_password NULL, '%s', 'sa'" % password)

        isError = self.IsSqlError(result)
        if  isError != None:
            return isError
            # return public.return_message(-1, 0, isError)

        public.writeFile('data/sa.pl',password)
        session['config']['mssql_sa'] = password
        return public.returnMsg(True, public.lang("The password of sa is changed successfully."))



    def get_database_size_by_id(self,args):
        """
        @获取数据库尺寸（批量删除验证）
        @args json/int 数据库id
        """
        total = 0
        db_id = args
        if not isinstance(args,int): db_id = args['db_id']

        try:
            name = public.M('databases').where('id=?',db_id).getField('name')
            mssql_obj = self.get_mssql_obj(name)
            tables = mssql_obj.query("select name,size,type from sys.master_files where type=0 and name = '{}'".format(name))

            total = tables[0][1]
            if not total: total = 0
        except :pass

        return total

    def check_del_data(self,args):
        """
        @删除数据库前置检测
        """
        # {"ids": "[128]"}

        # return self.check_base_del_data(args)
        return public.return_message(0, 0, self.check_base_del_data(args))

    #本地创建数据库
    def __CreateUsers(self,data_name,username,password,address):
        """
        @创建数据库用户
        """
        mssql_obj = self.get_mssql_obj_by_sid(self.sid)
        mssql_obj.execute("use %s create login %s with password ='%s' , default_database = %s" % (data_name,username,password,data_name))
        mssql_obj.execute("use %s create user %s for login %s with default_schema=dbo" % (data_name,username,username))
        mssql_obj.execute("use %s exec sp_addrolemember 'db_owner','%s'" % (data_name,data_name))
        mssql_obj.execute("ALTER DATABASE %s SET MULTI_USER" % data_name)


    #检测备份目录并赋值权限（MSSQL需要Authenticated Users）
    def CheckBackupPath(self,get):
        backupFile = session['config']['backup_path'] + '/database/sqlserver'
        if not os.path.exists(backupFile):
            os.makedirs(backupFile)
            get.filename = backupFile
            get.user = 'Authenticated Users'
            get.access = 2032127
            import files
            files.files().SetFileAccess(get)

    def check_cloud_database_status(self,conn_config):
        """
        @检测远程数据库是否连接
        @conn_config 远程数据库配置，包含host port pwd等信息
        """
        try:

            import panelMssql
            if not 'db_name' in conn_config: conn_config['db_name'] = None
            sql_obj = panelMssql.panelMssql().set_host(conn_config['db_host'],conn_config['db_port'],conn_config['db_name'],conn_config['db_user'],conn_config['db_password'])
            data = sql_obj.query("SELECT name FROM MASTER.DBO.SYSDATABASES ORDER BY name")

            isError = self.IsSqlError(data)
            if isError != None:
                return isError
                # return public.return_message(-1, 0, isError)
            if type(data) == str:
                # return public.returnMsg(False,data)
                return public.return_message(-1, 0, data)

            if not conn_config['db_name']:
                # return True
                return public.return_message(0, 0, True)
            for i in data:
                if i[0] == conn_config['db_name']:
                    # return True
                    return public.return_message(0, 0, True)
            # return public.returnMsg(False, public.lang("The specified database does not exist!"))
            return public.return_message(-1, 0, public.lang("The specified database does not exist!"))
        except Exception as ex:

            # return public.returnMsg(False,ex)
            return public.return_message(-1, 0, ex)
