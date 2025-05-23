#coding: utf-8
#-------------------------------------------------------------------
# aaPanel
#-------------------------------------------------------------------
# Copyright (c) 2015-2099 aaPanel(www.aapanel.com) All rights reserved.
#-------------------------------------------------------------------
# Author: hezhihong <bt_ahong@aapanel.com>
#-------------------------------------------------------------------

#------------------------------
# postgresql模型
#------------------------------
import os,re,json,time
from databaseModel.base import databaseBase
import public
try:
    from BTPanel import session
except :pass
try:
    import psycopg2
    from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
except:
    pass

class panelPgsql:
    __DB_PASS = None
    __DB_USER = 'postgres'
    __DB_PORT = 5432
    __DB_HOST = 'localhost'
    __DB_CONN = None
    __DB_CUR  = None
    __DB_ERR  = None

    __DB_CLOUD = 0 #远程数据库
    def __init__(self):
        self.__DB_CLOUD = 0
        if self.__DB_USER=='postgres' and self.__DB_HOST == 'localhost' and self.__DB_PASS ==None:
            tmp_args=public.dict_obj()
            tmp_args.is_True = True
            self.__DB_PASS =main().get_root_pwd(tmp_args)


    def set_host(self,host,port,name,username,password,prefix = ''):
        self.__DB_HOST = host
        self.__DB_PORT = int(port)
        self.__DB_NAME = name
        if self.__DB_NAME: self.__DB_NAME = str(self.__DB_NAME)
        self.__DB_USER = str(username)
        self._USER = str(username)
        self.__DB_PASS = str(password)
        self.__DB_PREFIX = prefix
        self.__DB_CLOUD = 1
        return self


    def check_psycopg(self):
        """
        @name检测依赖是否正常
        """
        try:
            import psycopg2
            from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
        except:
            os.system('btpip install psycopg2-binary')
            try:
                import psycopg2
                from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
            except:
                return False
        return True

    #连接MYSQL数据库
    def __Conn(self):
        self.check_psycopg()
        try:
            import psycopg2
        except:
            self.__DB_ERR = public.get_error_info()
            return False
        try:
            if self.__DB_USER == 'postgres' and self.__DB_HOST=='localhost':
                if not self.__DB_PASS:
                    tmp_args=public.dict_obj()
                    try:
                        self.__DB_PASS==main().get_root_pwd(tmp_args)['msg']
                    except:
                        pass
            self.__DB_CONN = psycopg2.connect(user=self.__DB_USER, password = self.__DB_PASS, host=self.__DB_HOST, port = self.__DB_PORT)
            self.__DB_CONN.autocommit = True
            self.__DB_CONN.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT) # <-- ADD THIS LINE

            self.__DB_CUR  = self.__DB_CONN.cursor()
            return True
        except :

            self.__DB_ERR = public.get_error_info()
            print(self.__DB_ERR)
            return False

    def execute(self,sql):
        #执行SQL语句返回受影响行
        if not self.__Conn(): return self.__DB_ERR
        try:
            #print(sql)
            result = self.__DB_CUR.execute(sql)
            self.__DB_CONN.commit()
            self.__Close()
            return result
        except Exception as ex:

            return ex

    def query(self,sql):

        #执行SQL语句返回数据集
        if not self.__Conn(): return self.__DB_ERR
        try:
            self.__DB_CUR.execute(sql)
            result = self.__DB_CUR.fetchall()

            data = list(map(list,result))
            self.__Close()
            return data
        except Exception as ex:
            return ex

    #关闭连接
    def __Close(self):
        self.__DB_CUR.close()
        self.__DB_CONN.close()

class main(databaseBase,panelPgsql):

    __ser_name = None
    __soft_path = '/www/server/pgsql'
    __setup_path = '/www/server/panel/'
    __dbuser_info_path = "{}plugin/pgsql_manager_dbuser_info.json".format(__setup_path)
    __plugin_path = "{}plugin/pgsql_manager/".format(__setup_path)

    def __init__(self):

        s_path = public.get_setup_path()
        v_info = public.readFile("{}/pgsql/version.pl".format(s_path))
        if v_info:
            ver = v_info.split('.')[0]
            self.__ser_name = 'postgresql-x64-{}'.format(ver)
            self.__soft_path = '{}/pgsql/{}'.format(s_path)


    #获取配置项
    def get_options(self,get):
        data = {}
        options = ['port','listen_addresses']
        if not self.__soft_path:self.__soft_path='{}/pgsql'.format(public.get_setup_path())
        conf = public.readFile('{}/data/postgresql.conf'.format(self.__soft_path))
        for opt in options:
            tmp = re.findall(r"\s+" +opt + r"\s*=\s*(.+)#",conf)
            if not tmp: continue;
            data[opt] = tmp[0].strip()
            if opt == 'listen_addresses':
                data[opt] = data[opt].replace('\'','')
        data['password'] = self.get_root_pwd(None)['msg']
        return data

    def get_list(self,args):
        """
        @获取数据库列表
        @sql_type = pgsql
        """
        return self.get_base_list(args, sql_type = 'pgsql')


    def get_sql_obj_by_sid(self,sid = 0,conn_config = None):
        """
        @取pgsql数据库对像 By sid
        @sid 数据库分类，0：本地
        """
        if type(sid) == str:
            try:
                sid = int(sid)
            except :sid = 0

        if sid:
            if not conn_config: conn_config = public.M('database_servers').where("id=?" ,sid).find()
            db_obj = panelPgsql()

            try:
                db_obj = db_obj.set_host(conn_config['db_host'],conn_config['db_port'],None,conn_config['db_user'],conn_config['db_password'])
            except Exception as e:
                raise public.PanelError(e)
        else:
            db_obj = panelPgsql()
        return db_obj

    def get_sql_obj(self,db_name):
        """
        @取pgsql数据库对象
        @db_name 数据库名称
        """
        is_cloud_db = False
        if db_name:
            db_find = public.M('databases').where("name=?" ,db_name).find()
            if db_find['sid']:
                return self.get_sql_obj_by_sid(db_find['sid'])
            is_cloud_db = db_find['db_type'] in ['1',1]

        if is_cloud_db:

            db_obj = panelPgsql()
            conn_config = json.loads(db_find['conn_config'])
            try:
                db_obj = db_obj.set_host(conn_config['db_host'],conn_config['db_port'],conn_config['db_name'],conn_config['db_user'],conn_config['db_password'])
            except Exception as e:
                raise public.PanelError(e)
        else:
            db_obj = panelPgsql()
        return db_obj

    def GetCloudServer(self,args):
        '''
            @name 获取远程服务器列表
            @author hwliang<2021-01-10>
            @return list
        '''
        check_result = os.system('/www/server/pgsql/bin/psql --version')
        if check_result !=0 and not public.M('database_servers').where('db_type=?','pgsql').count():
            return []
        return self.GetBaseCloudServer(args)


    def AddCloudServer(self,args):
        '''
        @添加远程数据库
        '''
        return self.AddBaseCloudServer(args)

    def RemoveCloudServer(self,args):
        '''
        @删除远程数据库
        '''
        return self.RemoveBaseCloudServer(args)

    def ModifyCloudServer(self,args):
        '''
        @修改远程数据库
        '''
        return self.ModifyBaseCloudServer(args)

    def AddDatabase(self,args):
        """
        @添加数据库
        """
        if not args.get('name/str',0):return public.returnMsg(False, public.lang("Database name cannot be empty!"))
        import re
        test_str = re.search(r"\W",args.name)
        if test_str!=None:
            return public.returnMsg(False, public.lang("The database name cannot contain special characters"))
        res = self.add_base_database(args)
        if not res['status']: return res

        data_name = res['data_name']
        username = res['username']
        password = res['data_pwd']
        try:
            self.sid = int(args['sid'])
        except :
            self.sid = 0

        dtype = 'PgSql'
        sql_obj = self.get_sql_obj_by_sid(self.sid)
        result = sql_obj.execute("CREATE DATABASE {};".format(data_name))
        isError = self.IsSqlError(result)
        if  isError != None: return isError

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

        public.set_module_logs('pgsql','AddDatabase',1)
        #添加入SQLITE
        public.M('databases').add('pid,sid,db_type,name,username,password,accept,ps,addtime,type',(pid,self.sid,db_type,data_name,username,password,'127.0.0.1',args['ps'],addTime,dtype))
        public.WriteLog("TYPE_DATABASE", 'DATABASE_ADD_SUCCESS',(data_name,))
        return public.returnMsg(True, public.lang("Added successfully!"))

    def DeleteDatabase(self,get):
        """
        @删除数据库
        """
        id = get['id']
        find = public.M('databases').where("id=?",(id,)).field('id,pid,name,username,password,accept,ps,addtime,db_type,conn_config,sid,type').find();
        if not find: return public.returnMsg(False, public.lang("The specified database does not exist."))

        name = get['name']
        username = find['username']

        sql_obj = self.get_sql_obj_by_sid(find['sid'])
        result = sql_obj.execute("drop database {};".format(name))
        sql_obj.execute("drop user {};".format(username))
        #删除SQLITE
        public.M('databases').where("id=?",(id,)).delete()
        public.WriteLog("TYPE_DATABASE", 'DATABASE_DEL_SUCCESS',(name,))
        return public.returnMsg(True, public.lang("Delete successfully!"))


    def ToBackup(self,args):
        """
        @备份数据库 id 数据库id
        """
        id = args['id']

        find = public.M('databases').where("id=?",(id,)).find()
        if not find: return public.returnMsg(False, public.lang("Database does not exist!"))

        if not find['password'].strip(): 
            return public.returnMsg(False, public.lang("The database password is empty. Set the password first."))

        sql_dump = '{}/bin/pg_dump'.format(self.__soft_path)
        # return sql_dump
        if not os.path.isfile(sql_dump): 
            return public.returnMsg(False, public.lang("Lack of backup tools, please first through the software store PGSQL manager!"))       

        back_path = session['config']['backup_path'] + '/database/pgsql/'
        # return back_path
        if not os.path.exists(back_path): os.makedirs(back_path)

        fileName = find['name'] + '_' + time.strftime('%Y%m%d_%H%M%S',time.localtime()) + '.sql'

        backupName =  back_path + fileName


        if int(find['sid']):
            info = self.get_info_by_db_id(id)
            shell = '{} "host={} port={} user={} dbname={} password={}" > {}'.format(sql_dump,info['db_host'],info['db_port'],info['db_user'],find['name'],info['db_password'],backupName)
        else:
            args_one =public.dict_obj()
            port = self.get_port(args_one)
            shell = '{} "host=127.0.0.1 port={} user={} dbname={} password={}" > {}'.format(sql_dump,port['data'],find['username'],find['name'],find['password'],backupName)

        ret = public.ExecShell(shell)
        if not os.path.exists(backupName):
            return public.returnMsg(False, public.lang("Backup error"));

        public.M('backup').add('type,name,pid,filename,size,addtime',(1,fileName,id,backupName,0,time.strftime('%Y-%m-%d %X',time.localtime())))
        public.WriteLog("TYPE_DATABASE", "DATABASE_BACKUP_SUCCESS",(find['name'],))

        if os.path.getsize(backupName) < 2048:
            return public.returnMsg(True, public.lang("The backup file size is smaller than 2Kb. Check the backup integrity."))
        else:
            return public.returnMsg(True, public.lang("Backup Succeeded!"))

    def DelBackup(self,args):
        """
        @删除备份文件
        """
        return self.delete_base_backup(args)

    def get_port(self, args):  # 获取端口号
        str_shell = '''netstat -luntp|grep postgres|head -1|awk '{print $4}'|awk -F: '{print $NF}' '''
        try:
            port = public.ExecShell(str_shell)[0]
            if port.strip():
                return {'data': port.strip(), "status": True}
            else:
                return {'data': 5432, "status": False}
        except:
            return {'data': 5432, "status": False}


    #导入
    def InputSql(self,get):

        name = get.name
        file = get.file
        # return name

        find = public.M('databases').where("name=?",(name,)).find()
        if not find: return public.returnMsg(False, public.lang("Database does not exist!"))
        # return find
        if not find['password'].strip(): 
            return public.returnMsg(False, public.lang("The database password is empty. Set the password first."))

        tmp = file.split('.')
        exts = ['sql']
        ext = tmp[len(tmp) -1]
        if ext not in exts:
            return public.returnMsg(False, public.lang("Select sql、gz、zip file!"))

        sql_dump = '{}/bin/psql'.format(self.__soft_path)
        if not os.path.exists(sql_dump): 
            return public.returnMsg(False, public.lang("Lack of recovery tool, please use software management to install PGSQL!"))    

        if int(find['sid']):
            info = self.get_info_by_db_id(find['id'])
            shell = '{} "host={} port={} user={} dbname={} password={}" < {}'.format(sql_dump,info['db_host'],info['db_port'],info['db_user'],find['name'],info['db_password'],file)
        else:
            args_one =public.dict_obj()
            port = self.get_port(args_one)
            shell = '{} "host=127.0.0.1 port={} user={} dbname={} password={}" < {}'.format(sql_dump,port['data'],find['username'],find['name'],find['password'],file)

        ret = public.ExecShell(shell)
      
        public.WriteLog("TYPE_DATABASE", 'Description Succeeded in importing database [{}]'.format(name))
        return public.returnMsg(True, public.lang("Successfully imported database!"));


    def SyncToDatabases(self,get):
        """
        @name同步数据库到服务器
        """
        tmp_type = int(get['type'])
        n = 0
        sql = public.M('databases')
        if tmp_type == 0:
            where = "lower(type) = lower('pgsql')"
            # data = sql.field('id,name,username,password,accept,type,sid,db_type').where('type=?',('pgsql',)).select()
            data = sql.field('id,name,username,password,accept,type,sid,db_type').where(where,()).select()
            print(data)
            for value in data:
                if value['db_type'] in ['1',1]:
                    continue # 跳过远程数据库
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
            return public.returnMsg(True, public.lang("Synchronization succeeded"))
        elif n == 0:
            return public.returnMsg(False, public.lang("Sync failed"))
        return public.returnMsg(True,'Database sync success',(str(n),))

    def ToDataBase(self,find):
        """
        @name 添加到服务器
        """
        if find['username'] == 'bt_default': return 0
        if len(find['password']) < 3 :
            find['username'] = find['name']
            find['password'] = public.md5(str(time.time()) + find['name'])[0:10]
            public.M('databases').where("id=?",(find['id'],)).save('password,username',(find['password'],find['username']))

        self.sid = find['sid']
        sql_obj = self.get_sql_obj_by_sid(self.sid)
        result = sql_obj.execute("CREATE DATABASE {};".format(find['name']))
        isError = self.IsSqlError(result)
        if isError != None and isError['status']==False and isError['msg']=='指定数据库已存在，请勿重复添加.':return 1

        self.__CreateUsers(find['name'],find['username'],find['password'],'127.0.0.1')

        return 1


    def SyncGetDatabases(self,get):
        """
        @name 从服务器获取数据库
        @param sid 0为本地数据库 1为远程数据库
        """
        n = 0;s = 0;
        db_type = 0
        self.sid = get.get('sid/d',0)
        if self.sid: db_type = 2

        sql_obj = self.get_sql_obj_by_sid(self.sid)
        data = sql_obj.query('SELECT datname FROM pg_database;')#select * from pg_database order by datname;
        isError = self.IsSqlError(data)
        if isError != None: return isError
        if type(data) == str: return public.returnMsg(False,data)

        sql = public.M('databases')
        nameArr = ['information_schema','postgres','template1','template0','performance_schema','mysql','sys','master','model','msdb','tempdb','ReportServerTempDB','YueMiao','ReportServer']
        for item in data:

            dbname = item[0]

            if sql.where("name=?",(dbname,)).count(): continue
            if not dbname in nameArr:
                if sql.table('databases').add('name,username,password,accept,ps,addtime,type,sid,db_type',(dbname,dbname,'','',public.getMsg('INPUT_PS'),time.strftime('%Y-%m-%d %X',time.localtime()),'pgsql',self.sid,db_type)): n +=1

        return public.returnMsg(True,'Database success',(str(n),))

    def ResDatabasePassword(self,args):
        """
        @修改用户密码
        """
        id = args['id']
        username = args['name'].strip()
        newpassword = public.trim(args['password'])
        if not newpassword: return public.returnMsg(False, public.lang("The database password cannot be empty."));
                        

        find = public.M('databases').where("id=?",(id,)).field('id,pid,name,username,password,type,accept,ps,addtime,sid').find();
        if not find: return public.returnMsg(False, public.lang("Modify the failure，The specified database does not exist."));
          
        sql_obj = self.get_sql_obj_by_sid(find['sid'])   
        result = sql_obj.execute("alter user {} with password '{}';".format(username,newpassword))
        isError = self.IsSqlError(result)
        if isError != None: return isError

        #修改SQLITE
        public.M('databases').where("id=?",(id,)).setField('password',newpassword)

        public.WriteLog("TYPE_DATABASE",'Database password success',(find['name'],))
        return public.returnMsg(True,'Database password success',(find['name'],))


    def get_root_pwd(self,args):
        """
        @获取sa密码
        """ 
        check_result = os.system('/www/server/pgsql/bin/psql --version')
        if check_result !=0:return public.returnMsg(False, public.lang("If PgSQL is not installed or started, install or start it first"))     
        password = ''
        path =  '{}/data/postgresAS.json'.format(public.get_panel_path())      
        if os.path.isfile(path):
            try:
                password = json.loads(public.readFile(path))['password']
                print('333333333')
                print(password)
            except :pass
        if 'is_True' in args and args.is_True:return password
        return public.returnMsg(True,password)


    def set_root_pwd(self,args):
        """
        @设置sa密码
        """
        password = public.trim(args['password'])   
        if len(password) < 8 : return public.returnMsg(False, public.lang("The password must not be less than 8 digits."))
        check_result = os.system('/www/server/pgsql/bin/psql --version')
        if check_result !=0:return public.returnMsg(False, public.lang("If PgSQL is not installed or started, install or start it first"))
        sql_obj = self.get_sql_obj_by_sid('0')
        data = sql_obj.query('SELECT datname FROM pg_database;')
        isError = self.IsSqlError(data)
        if isError != None: return isError
            
        path = '{}/data/pg_hba.conf'.format(self.__soft_path) 
        p_path = '{}/data/postgresAS.json'.format(public.get_panel_path())
        if not os.path.isfile(path):
            return public.returnMsg(False,public.lang('{}File does not exist, please check the installation is complete!',path))

        src_conf = public.readFile(path)
        add_conf = src_conf.replace('md5','trust')
        # public.writeFile(path,public.readFile(path).replace('md5','trust'))
        public.writeFile(path,add_conf)
        
        pg_obj = panelPgsql()
        pg_obj.execute("ALTER USER postgres WITH PASSWORD '{}';".format(password))
        data = {"username":"postgres","password":""}
        try:
            data = json.loads(public.readFile(p_path))
        except : pass
        data['password'] = password
        public.writeFile(p_path,json.dumps(data))
        public.writeFile(path, src_conf)
        return public.returnMsg(True, public.lang("The administrator password is successfully changed. Procedure.")) 
        

  
    def get_info_by_db_id(self,db_id):
        """
        @获取数据库连接详情
        @db_id 数据库id
        """
        # print(db_id,'111111111111')
        find = public.M('databases').where("id=?" ,db_id).find()
        # return find
        if not find: return False
        # print(find)
        data = {
            'db_host':'127.0.0.1',
            'db_port':5432,
            'db_user':find['username'],
            'db_password':find['password']
        }

        if int(find['sid']):
            conn_config = public.M('database_servers').where("id=?" ,find['sid']).find()

            data['db_host'] = conn_config['db_host']
            data['db_port'] = int(conn_config['db_port'])
        return data

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
            sql_obj = self.get_sql_obj(name)
            tables = sql_obj.query("select name,size,type from sys.master_files where type=0 and name = '{}'".format(name))

            total = tables[0][1]
            if not total: total = 0
        except :pass

        return total

    def check_del_data(self,args):
        """
        @删除数据库前置检测
        """
        return self.check_base_del_data(args)

    #本地创建数据库
    def __CreateUsers(self,data_name,username,password,address):
        """
        @创建数据库用户
        """
        sql_obj = self.get_sql_obj_by_sid(self.sid)
        sql_obj.execute("CREATE USER {} WITH PASSWORD '{}';".format(username,password))
        sql_obj.execute("GRANT ALL PRIVILEGES ON DATABASE {} TO {};".format(data_name,username))
        return True


    def __get_db_list(self,sql_obj):
        """
        获取pgsql数据库列表
        """
        data = []
        ret = sql_obj.query('SELECT datname FROM pg_database;')
        if type(ret) == list:
            for x in ret:
                data.append(x[0])
        return data

    def check_cloud_database_status(self,conn_config):
        """
        @检测远程数据库是否连接
        @conn_config 远程数据库配置，包含host port pwd等信息
        """
        try:

            if not 'db_name' in conn_config: conn_config['db_name'] = None
            sql_obj = panelPgsql().set_host(conn_config['db_host'],conn_config['db_port'],conn_config['db_name'],conn_config['db_user'],conn_config['db_password'])

            data = sql_obj.query("SELECT datname FROM pg_database;")                  
            if type(data) == str: 
                return public.returnMsg(False, public.lang("Connecting to remote PGSQL fails. Perform the following operations to rectify the fault：<br/>1、The database port is correct and the firewall allows access<br/>2、Check whether the database account password is correct<br/>3、pg_hba.confWhether to add a client release record<br/>4、postgresql.conf Add listen_addresses to the correct server IP address."))

            if not conn_config['db_name']: return True
            for i in data:          
                if i[0] == conn_config['db_name']:
                    return True
            return public.returnMsg(False, public.lang("The specified database does not exist!"))
        except Exception as ex:
     
            return public.returnMsg(False, public.lang(""))
