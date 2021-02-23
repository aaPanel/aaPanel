#coding: utf-8
#-------------------------------------------------------------------
# 宝塔Linux面板
#-------------------------------------------------------------------
# Copyright (c) 2015-2017 宝塔软件(http:#bt.cn) All rights reserved.
#-------------------------------------------------------------------
# Author: hwliang <hwl@bt.cn>
#-------------------------------------------------------------------

#------------------------------
# 数据库管理类
#------------------------------
import public,db,re,time,os,sys,panelMysql
from BTPanel import session
import datatool
class database(datatool.datatools):
    sqlite_connection = None

    # 检查mysql是否存在空用户密码
    def _check_empty_user_passwd(self):
        mysql_obj = panelMysql.panelMysql()
        mysql_obj.execute("delete from mysql.user where user='' and password=''")

    #添加数据库
    def AddDatabase(self,get):
        try:
            self._check_empty_user_passwd()
            ssl = ""
            if hasattr(get,"ssl"):
                ssl = get.ssl
            if ssl == "REQUIRE SSL" and not self.check_mysql_ssl_status(get):
                return public.returnMsg(False,'MYSQL_SSL_ERR')
            data_name = get['name'].strip()
            if self.CheckRecycleBin(data_name): return public.returnMsg(False,'DATABASE_DEL_RECYCLE_BIN',(data_name,))
            if len(data_name) > 64: return public.returnMsg(False, 'DATABASE_NAME_LEN')
            reg = r"^[\w\.-]+$"
            if not re.match(reg, data_name): return public.returnMsg(False,'DATABASE_NAME_ERR_T')
            if not hasattr(get,'db_user'): get.db_user = data_name
            username = get.db_user.strip()
            checks = ['root','mysql','test','sys','panel_logs']
            if username in checks or len(username) < 1: return public.returnMsg(False,'DATABASE_USER_NAME_ERR')
            if data_name in checks or len(data_name) < 1: return public.returnMsg(False,'DATABASE_NAME_ERR')
            data_pwd = get['password']
            if len(data_pwd)<1:
                data_pwd = public.md5(str(time.time()))[0:8]
            
            sql = public.M('databases')
            if sql.where("name=?",(data_name)).count(): return public.returnMsg(False,'DATABASE_NAME_EXISTS')
            if sql.where("username=?", (username)).count(): return public.returnMsg(False, 'DATABASE_USERNAME_EXISTS')
            address = get['address'].strip()
            user = '是'
            password = data_pwd
            
            codeing = get['codeing']
            
            wheres={
                    'utf8'      :   'utf8_general_ci',
                    'utf8mb4'   :   'utf8mb4_general_ci',
                    'gbk'       :   'gbk_chinese_ci',
                    'big5'      :   'big5_chinese_ci'
                    }
            codeStr=wheres[codeing]
            #添加MYSQL
            mysql_obj = panelMysql.panelMysql()
            #从MySQL验证是否存在
            if self.database_exists_for_mysql(mysql_obj,data_name):  return public.returnMsg(False,'DB_EXIST1')

            result = mysql_obj.execute("create database `" + data_name + "` DEFAULT CHARACTER SET " + codeing + " COLLATE " + codeStr)
            isError = self.IsSqlError(result)
            if  isError != None: return isError
            mysql_obj.execute("drop user '" + username + "'@'localhost'")
            for a in address.split(','):
                mysql_obj.execute("drop user '" + username + "'@'" + a + "'")
            self.__CreateUsers(data_name,username,password,address,ssl)
            
            if get['ps'] == '': get['ps']=public.getMsg('INPUT_PS')
            addTime = time.strftime('%Y-%m-%d %X',time.localtime())
            
            pid = 0
            if hasattr(get,'pid'): pid = get.pid
            #添加入SQLITE
            sql.add('pid,name,username,password,accept,ps,addtime',(pid,data_name,username,password,address,get['ps'],addTime))
            public.WriteLog("TYPE_DATABASE", 'DATABASE_ADD_SUCCESS',(data_name,))
            return public.returnMsg(True,'ADD_SUCCESS')
        except Exception as ex:
            public.WriteLog("TYPE_DATABASE",'DATABASE_ADD_ERR', (data_name,str(ex)))
            return public.returnMsg(False,'ADD_ERROR')

    # 生成mysql证书
    def _create_mysql_ssl(self):
        ip = public.readFile("/www/server/panel/data/iplist.txt")
        openssl_command = """
cd /www/server/data
openssl genrsa 2048 > ca-key.pem
openssl req -sha1 -new -x509 -nodes -subj "/C=CA/ST=CA/L=CA/O=CA/OU=CA/CN={ip}BT" -days 3650 -key ca-key.pem > ca.pem
openssl req -sha1 -newkey rsa:2048 -days 3650 -nodes -subj "/C=CA/ST=CA/L=CA/O=CA/OU=CA/CN={ip}" -keyout server-key.pem > server-req.pem
openssl rsa -in server-key.pem -out server-key.pem
openssl x509 -sha1 -req -in server-req.pem -days 3650 -CA ca.pem -CAkey ca-key.pem -set_serial 01 > server-cert.pem
openssl req -sha1 -newkey rsa:2048 -days 3650 -nodes -subj "/C=CA/ST=CA/L=CA/O=CA/OU=CA/CN={ip}" -keyout client-key.pem > client-req.pem
openssl rsa -in client-key.pem -out client-key.pem
openssl x509 -sha1 -req -in client-req.pem -days 3650 -CA ca.pem -CAkey ca-key.pem -set_serial 01 > client-cert.pem
tar -zcvf ssl.zip client-cert.pem client-key.pem ca.pem
""".format(ip=ip)
        public.ExecShell(openssl_command)

    # 写入mysqlssl到配置
    def write_ssl_to_mysql(self,get):
        ssl_conf = """
ssl-ca=/www/server/data/ca.pem
ssl-cert=/www/server/data/server-cert.pem
ssl-key=/www/server/data/server-key.pem
"""
        conf_file = "/etc/my.cnf"
        conf = public.readFile(conf_file)
        if not conf:
            return public.returnMsg(False,"CONF_FILE_NOT_EXISTS")
        if self.check_mysql_ssl_status(get):
            reg = "ssl-ca=/www.*\n.*\n.*server-key.pem\n"
            conf = re.sub(reg,"",conf)
            public.writeFile(conf_file,conf)
            return public.returnMsg(True,"SET_SUCCESS")
        self._create_mysql_ssl()
        if "ssl-ca" not in conf:
            conf = re.sub('\[mysqld\]','[mysqld]'+ssl_conf,conf)
        public.writeFile(conf_file,conf)
        public.ExecShell('chown mysql.mysql /www/server/data/*.pem')
        return public.returnMsg(True,"MYSQL_SSL_OPEN_SUCCESS")

    # 检查mysqlssl状态
    def check_mysql_ssl_status(self,get):
        mysql_obj = panelMysql.panelMysql()
        result = mysql_obj.query("show variables like 'have_ssl';")
        if result and result[0][1] == "YES":
            return True
        return False

    #判断数据库是否存在—从MySQL
    def database_exists_for_mysql(self,mysql_obj,dataName):
        databases_tmp = self.map_to_list(mysql_obj.query('show databases'))
        if not isinstance(databases_tmp,list):
            return True

        for i in databases_tmp:
            if i[0] == dataName:
                return True
        return False

    #创建用户
    def __CreateUsers(self,dbname,username,password,address,ssl=None):
        mysql_obj = panelMysql.panelMysql()
        mysql_obj.execute("CREATE USER `%s`@`localhost` IDENTIFIED BY '%s'" % (username,password))
        mysql_obj.execute("grant all privileges on `%s`.* to `%s`@`localhost` %s" % (dbname,username,ssl))
        if not ssl:
            mysql_obj.execute("update mysql.user set ssl_type='' where user='%s' and host='localhost'" % (username))
        for a in address.split(','):
            mysql_obj.execute("CREATE USER `%s`@`%s` IDENTIFIED BY '%s'" % (username,a,password))
            mysql_obj.execute("grant all privileges on `%s`.* to `%s`@`%s` %s" % (dbname,username,a,ssl))
        mysql_obj.execute("flush privileges")
        
    #检查是否在回收站
    def CheckRecycleBin(self,name):
        try:
            for n in os.listdir('/www/Recycle_bin'):
                if n.find('BTDB_'+name+'_t_') != -1: return True
            return False
        except:
            return False
    
    #检测数据库执行错误
    def IsSqlError(self,mysqlMsg):
        mysqlMsg=str(mysqlMsg)
        if "MySQLdb" in mysqlMsg: return public.returnMsg(False,'DATABASE_ERR_MYSQLDB')
        if "2002," in mysqlMsg or '2003,' in mysqlMsg: return public.returnMsg(False,'DATABASE_ERR_CONNECT')
        if "using password:" in mysqlMsg: return public.returnMsg(False,'DATABASE_ERR_PASS')
        if "Connection refused" in mysqlMsg: return public.returnMsg(False,'DATABASE_ERR_CONNECT')
        if "1133" in mysqlMsg: return public.returnMsg(False,'DATABASE_ERR_NOT_EXISTS')
        if "libmysqlclient" in mysqlMsg: 
            self.rep_lnk()
            public.ExecShell("pip uninstall mysql-python -y")
            public.ExecShell("pip install pymysql")
            public.writeFile('data/restart.pl','True')
            return public.returnMsg(False,"MYSQL_FIX_WITH_AUTO_ERR")
        return None

    def rep_lnk(self):
        shell_cmd = '''
Setup_Path=/www/server/mysql
#删除软链
DelLink()
{	
	rm -f /usr/bin/mysql*
	rm -f /usr/lib/libmysql*
	rm -f /usr/lib64/libmysql*
    rm -f /usr/bin/myisamchk
    rm -f /usr/bin/mysqldump
    rm -f /usr/bin/mysql
    rm -f /usr/bin/mysqld_safe
    rm -f /usr/bin/mysql_config
}
#设置软件链
SetLink()
{
    ln -sf ${Setup_Path}/bin/mysql /usr/bin/mysql
    ln -sf ${Setup_Path}/bin/mysqldump /usr/bin/mysqldump
    ln -sf ${Setup_Path}/bin/myisamchk /usr/bin/myisamchk
    ln -sf ${Setup_Path}/bin/mysqld_safe /usr/bin/mysqld_safe
    ln -sf ${Setup_Path}/bin/mysqlcheck /usr/bin/mysqlcheck
	ln -sf ${Setup_Path}/bin/mysql_config /usr/bin/mysql_config
	
	rm -f /usr/lib/libmysqlclient.so.16
	rm -f /usr/lib64/libmysqlclient.so.16
	rm -f /usr/lib/libmysqlclient.so.18
	rm -f /usr/lib64/libmysqlclient.so.18
	rm -f /usr/lib/libmysqlclient.so.20
	rm -f /usr/lib64/libmysqlclient.so.20
	rm -f /usr/lib/libmysqlclient.so.21
	rm -f /usr/lib64/libmysqlclient.so.21
	
	if [ -f "${Setup_Path}/lib/libmysqlclient.so.18" ];then
		ln -sf ${Setup_Path}/lib/libmysqlclient.so.18 /usr/lib/libmysqlclient.so.16
		ln -sf ${Setup_Path}/lib/libmysqlclient.so.18 /usr/lib64/libmysqlclient.so.16
		ln -sf ${Setup_Path}/lib/libmysqlclient.so.18 /usr/lib/libmysqlclient.so.18
		ln -sf ${Setup_Path}/lib/libmysqlclient.so.18 /usr/lib64/libmysqlclient.so.18
		ln -sf ${Setup_Path}/lib/libmysqlclient.so.18 /usr/lib/libmysqlclient.so.20
		ln -sf ${Setup_Path}/lib/libmysqlclient.so.18 /usr/lib64/libmysqlclient.so.20
	elif [ -f "${Setup_Path}/lib/mysql/libmysqlclient.so.18" ];then
		ln -sf ${Setup_Path}/lib/mysql/libmysqlclient.so.18 /usr/lib/libmysqlclient.so.16
		ln -sf ${Setup_Path}/lib/mysql/libmysqlclient.so.18 /usr/lib64/libmysqlclient.so.16
		ln -sf ${Setup_Path}/lib/mysql/libmysqlclient.so.18 /usr/lib/libmysqlclient.so.18
		ln -sf ${Setup_Path}/lib/mysql/libmysqlclient.so.18 /usr/lib64/libmysqlclient.so.18
		ln -sf ${Setup_Path}/lib/mysql/libmysqlclient.so.18 /usr/lib/libmysqlclient.so.20
		ln -sf ${Setup_Path}/lib/mysql/libmysqlclient.so.18 /usr/lib64/libmysqlclient.so.20
	elif [ -f "${Setup_Path}/lib/libmysqlclient.so.16" ];then
		ln -sf ${Setup_Path}/lib/libmysqlclient.so.16 /usr/lib/libmysqlclient.so.16
		ln -sf ${Setup_Path}/lib/libmysqlclient.so.16 /usr/lib64/libmysqlclient.so.16
		ln -sf ${Setup_Path}/lib/libmysqlclient.so.16 /usr/lib/libmysqlclient.so.18
		ln -sf ${Setup_Path}/lib/libmysqlclient.so.16 /usr/lib64/libmysqlclient.so.18
		ln -sf ${Setup_Path}/lib/libmysqlclient.so.16 /usr/lib/libmysqlclient.so.20
		ln -sf ${Setup_Path}/lib/libmysqlclient.so.16 /usr/lib64/libmysqlclient.so.20
	elif [ -f "${Setup_Path}/lib/mysql/libmysqlclient.so.16" ];then
		ln -sf ${Setup_Path}/lib/mysql/libmysqlclient.so.16 /usr/lib/libmysqlclient.so.16
		ln -sf ${Setup_Path}/lib/mysql/libmysqlclient.so.16 /usr/lib64/libmysqlclient.so.16
		ln -sf ${Setup_Path}/lib/mysql/libmysqlclient.so.16 /usr/lib/libmysqlclient.so.18
		ln -sf ${Setup_Path}/lib/mysql/libmysqlclient.so.16 /usr/lib64/libmysqlclient.so.18
		ln -sf ${Setup_Path}/lib/mysql/libmysqlclient.so.16 /usr/lib/libmysqlclient.so.20
		ln -sf ${Setup_Path}/lib/mysql/libmysqlclient.so.16 /usr/lib64/libmysqlclient.so.20
	elif [ -f "${Setup_Path}/lib/libmysqlclient_r.so.16" ];then
		ln -sf ${Setup_Path}/lib/libmysqlclient_r.so.16 /usr/lib/libmysqlclient_r.so.16
		ln -sf ${Setup_Path}/lib/libmysqlclient_r.so.16 /usr/lib64/libmysqlclient_r.so.16
	elif [ -f "${Setup_Path}/lib/mysql/libmysqlclient_r.so.16" ];then
		ln -sf ${Setup_Path}/lib/mysql/libmysqlclient_r.so.16 /usr/lib/libmysqlclient_r.so.16
		ln -sf ${Setup_Path}/lib/mysql/libmysqlclient_r.so.16 /usr/lib64/libmysqlclient_r.so.16
	elif [ -f "${Setup_Path}/lib/libmysqlclient.so.20" ];then
		ln -sf ${Setup_Path}/lib/libmysqlclient.so.20 /usr/lib/libmysqlclient.so.16
		ln -sf ${Setup_Path}/lib/libmysqlclient.so.20 /usr/lib64/libmysqlclient.so.16
		ln -sf ${Setup_Path}/lib/libmysqlclient.so.20 /usr/lib/libmysqlclient.so.18
		ln -sf ${Setup_Path}/lib/libmysqlclient.so.20 /usr/lib64/libmysqlclient.so.18
		ln -sf ${Setup_Path}/lib/libmysqlclient.so.20 /usr/lib/libmysqlclient.so.20
		ln -sf ${Setup_Path}/lib/libmysqlclient.so.20 /usr/lib64/libmysqlclient.so.20
	elif [ -f "${Setup_Path}/lib/libmysqlclient.so.21" ];then
		ln -sf ${Setup_Path}/lib/libmysqlclient.so.21 /usr/lib/libmysqlclient.so.16
		ln -sf ${Setup_Path}/lib/libmysqlclient.so.21 /usr/lib64/libmysqlclient.so.16
		ln -sf ${Setup_Path}/lib/libmysqlclient.so.21 /usr/lib/libmysqlclient.so.18
		ln -sf ${Setup_Path}/lib/libmysqlclient.so.21 /usr/lib64/libmysqlclient.so.18
		ln -sf ${Setup_Path}/lib/libmysqlclient.so.21 /usr/lib/libmysqlclient.so.20
		ln -sf ${Setup_Path}/lib/libmysqlclient.so.21 /usr/lib64/libmysqlclient.so.20
		ln -sf ${Setup_Path}/lib/libmysqlclient.so.21 /usr/lib/libmysqlclient.so.21
		ln -sf ${Setup_Path}/lib/libmysqlclient.so.21 /usr/lib64/libmysqlclient.so.21
	elif [ -f "${Setup_Path}/lib/libmariadb.so.3" ]; then
		ln -sf ${Setup_Path}/lib/libmariadb.so.3 /usr/lib/libmysqlclient.so.16
		ln -sf ${Setup_Path}/lib/libmariadb.so.3 /usr/lib64/libmysqlclient.so.16
		ln -sf ${Setup_Path}/lib/libmariadb.so.3 /usr/lib/libmysqlclient.so.18
		ln -sf ${Setup_Path}/lib/libmariadb.so.3 /usr/lib64/libmysqlclient.so.18
		ln -sf ${Setup_Path}/lib/libmariadb.so.3 /usr/lib/libmysqlclient.so.20
		ln -sf ${Setup_Path}/lib/libmariadb.so.3 /usr/lib64/libmysqlclient.so.20
		ln -sf ${Setup_Path}/lib/libmariadb.so.3 /usr/lib/libmysqlclient.so.21
		ln -sf ${Setup_Path}/lib/libmariadb.so.3 /usr/lib64/libmysqlclient.so.21
	elif [ -f "${Setup_Path}/lib/mysql/libmysqlclient.so.20" ];then
		ln -sf ${Setup_Path}/lib/mysql/libmysqlclient.so.20 /usr/lib/libmysqlclient.so.16
		ln -sf ${Setup_Path}/lib/mysql/libmysqlclient.so.20 /usr/lib64/libmysqlclient.so.16
		ln -sf ${Setup_Path}/lib/mysql/libmysqlclient.so.20 /usr/lib/libmysqlclient.so.18
		ln -sf ${Setup_Path}/lib/mysql/libmysqlclient.so.20 /usr/lib64/libmysqlclient.so.18
		ln -sf ${Setup_Path}/lib/mysql/libmysqlclient.so.20 /usr/lib/libmysqlclient.so.20
		ln -sf ${Setup_Path}/lib/mysql/libmysqlclient.so.20 /usr/lib64/libmysqlclient.so.20
	fi
}
DelLink
SetLink
'''    
        return public.ExecShell(shell_cmd)
    
    #删除数据库
    def DeleteDatabase(self,get):
        try:
            id=get['id']
            name = get['name']
            if os.path.exists('data/recycle_bin_db.pl'): return self.DeleteToRecycleBin(name)
            
            find = public.M('databases').where("id=?",(id,)).field('id,pid,name,username,password,accept,ps,addtime').find()
            accept = find['accept']
            username = find['username']
            #删除MYSQL
            result = panelMysql.panelMysql().execute("drop database `" + name + "`")
            isError=self.IsSqlError(result)
            if  isError != None: return isError
            users = panelMysql.panelMysql().query("select Host from mysql.user where User='" + username + "' AND Host!='localhost'")
            panelMysql.panelMysql().execute("drop user '" + username + "'@'localhost'")
            for us in users:
                panelMysql.panelMysql().execute("drop user '" + username + "'@'" + us[0] + "'")
            panelMysql.panelMysql().execute("flush privileges")
            #删除SQLITE
            public.M('databases').where("id=?",(id,)).delete()
            public.WriteLog("TYPE_DATABASE", 'DATABASE_DEL_SUCCESS',(name,))
            return public.returnMsg(True, 'DEL_SUCCESS')
        except Exception as ex:
            public.WriteLog("TYPE_DATABASE",'DATABASE_DEL_ERR',(get.name , str(ex)))
            return public.returnMsg(False,'DEL_ERROR')
    
    #删除数据库到回收站  
    def DeleteToRecycleBin(self,name):
        import json
        data = public.M('databases').where("name=?",(name,)).field('id,pid,name,username,password,accept,ps,addtime').find()
        username = data['username']
        panelMysql.panelMysql().execute("drop user '" + username + "'@'localhost'")
        users = panelMysql.panelMysql().query("select Host from mysql.user where User='" + username + "' AND Host!='localhost'")
        for us in users:
            panelMysql.panelMysql().execute("drop user '" + username + "'@'" + us[0] + "'")
        panelMysql.panelMysql().execute("flush privileges")
        rPath = '/www/Recycle_bin/'
        public.writeFile(rPath + 'BTDB_' + name +'_t_' + str(time.time()),json.dumps(data))
        public.M('databases').where("name=?",(name,)).delete()
        public.WriteLog("TYPE_DATABASE", 'DATABASE_DEL_SUCCESS',(name,))
        return public.returnMsg(True,'RECYCLE_BIN_DB')
    
    #永久删除数据库
    def DeleteTo(self,filename):
        import json
        data = json.loads(public.readFile(filename))
        if public.M('databases').where("name=?",( data['name'],)).count():
            os.remove(filename)
            return public.returnMsg(True,'DEL_SUCCESS')
        result = panelMysql.panelMysql().execute("drop database `" + data['name'] + "`")
        isError=self.IsSqlError(result)
        if  isError != None: return isError
        panelMysql.panelMysql().execute("drop user '" + data['username'] + "'@'localhost'")
        users = panelMysql.panelMysql().query("select Host from mysql.user where User='" + data['username'] + "' AND Host!='localhost'")
        for us in users:
            panelMysql.panelMysql().execute("drop user '" + data['username'] + "'@'" + us[0] + "'")
        panelMysql.panelMysql().execute("flush privileges")
        os.remove(filename)
        public.WriteLog("TYPE_DATABASE", 'DATABASE_DEL_SUCCESS',(data['name'],))
        return public.returnMsg(True,'DEL_SUCCESS')
    
    #恢复数据库
    def RecycleDB(self,filename):
        import json
        data = json.loads(public.readFile(filename))
        if public.M('databases').where("name=?",( data['name'],)).count():
            os.remove(filename)
            return public.returnMsg(True,'RECYCLEDB')

        self.__CreateUsers(data['name'],data['username'],data['password'],data['accept'])
        #result = panelMysql.panelMysql().execute("grant all privileges on `" + data['name'] + "`.* to '" + data['username'] + "'@'localhost' identified by '" + data['password'] + "'")
        #isError=self.IsSqlError(result)
        #if isError != None: return isError
        #panelMysql.panelMysql().execute("grant all privileges on `" + data['name'] + "`.* to '" + data['username'] + "'@'" + data['accept'] + "' identified by '" + data['password'] + "'")
        #panelMysql.panelMysql().execute("flush privileges")
        
        public.M('databases').add('id,pid,name,username,password,accept,ps,addtime',(data['id'],data['pid'],data['name'],data['username'],data['password'],data['accept'],data['ps'],data['addtime']))
        os.remove(filename)
        return public.returnMsg(True,"RECYCLEDB")
    
    #设置ROOT密码
    def SetupPassword(self,get):
        password = get['password'].strip()
        try:
            if not password: return public.returnMsg(False,'MYSQL_ROOT_PASSWD_EMTPY_ERR')
            rep = "^[\w@\.\?\-\_\>\<\~\!\#\$\%\^\&\*\(\)]+$"
            if not re.match(rep, password): return public.returnMsg(False, 'DATABASE_NAME_ERR_T')
            mysql_root = public.M('config').where("id=?",(1,)).getField('mysql_root')
            #修改MYSQL
            mysql_obj = panelMysql.panelMysql()
            result = mysql_obj.query("show databases")
            isError=self.IsSqlError(result)
            is_modify = True
            if  isError != None: 
                #尝试使用新密码
                public.M('config').where("id=?",(1,)).setField('mysql_root',password)
                result = mysql_obj.query("show databases")
                isError=self.IsSqlError(result)
                if  isError != None: 
                    public.ExecShell("cd /www/server/panel && "+public.get_python_bin()+" tools.py root \"" + password + "\"")
                    is_modify = False
            if is_modify:
                m_version = public.readFile(public.GetConfigValue('setup_path') + '/mysql/version.pl')
                
                if m_version.find('5.7') == 0  or m_version.find('8.0') == 0:
                    accept = self.map_to_list(mysql_obj.query("select Host from mysql.user where User='root'"))
                    for my_host in accept:
                        mysql_obj.execute("UPDATE mysql.user SET authentication_string='' WHERE User='root' and Host='{}'".format(my_host[0]))
                        mysql_obj.execute("ALTER USER `%s`@`%s` IDENTIFIED BY '%s'" % ('root',my_host[0],password))
                elif m_version.find('10.5.') != -1 or m_version.find('10.4.') != -1:
                    accept = self.map_to_list(mysql_obj.query("select Host from mysql.user where User='root'"))
                    for my_host in accept:
                        mysql_obj.execute("ALTER USER `%s`@`%s` IDENTIFIED BY '%s'" % ('root',my_host[0],password))
                else:
                    result = mysql_obj.execute("update mysql.user set Password=password('" + password + "') where User='root'")
                mysql_obj.execute("flush privileges")

            msg = public.getMsg('DATABASE_ROOT_SUCCESS')
            #修改SQLITE
            public.M('config').where("id=?",(1,)).setField('mysql_root',password)  
            public.WriteLog("TYPE_DATABASE", "DATABASE_ROOT_SUCCESS")
            session['config']['mysql_root']=password
            return public.returnMsg(True,msg)
        except Exception as ex:
            return public.returnMsg(False,'EDIT_ERROR' + str(ex))
    
    #修改用户密码
    def ResDatabasePassword(self,get):
        try:
            newpassword = get['password']
            username = get['name']
            id = get['id']
            if not newpassword: return public.returnMsg(False,'DB_PASSWD_EMPTY_ERR', (username,))
            name = public.M('databases').where('id=?',(id,)).getField('name')
            
            rep = "^[\w@\.\?\-\_\>\<\~\!\#\$\%\^\&\*\(\)]+$"
            if  not re.match(rep, newpassword): return public.returnMsg(False, 'DATABASE_NAME_ERR_T')
            #修改MYSQL
            mysql_obj = panelMysql.panelMysql()
            m_version = public.readFile(public.GetConfigValue('setup_path') + '/mysql/version.pl')
            if m_version.find('5.7') == 0  or m_version.find('8.0') == 0 :
                accept = self.map_to_list(panelMysql.panelMysql().query("select Host from mysql.user where User='" + name + "' AND Host!='localhost'"))
                mysql_obj.execute("update mysql.user set authentication_string='' where User='" + username + "'")
                result = mysql_obj.execute("ALTER USER `%s`@`localhost` IDENTIFIED BY '%s'" % (username,newpassword))
                for my_host in accept:
                    mysql_obj.execute("ALTER USER `%s`@`%s` IDENTIFIED BY '%s'" % (username,my_host[0],newpassword))
            elif m_version.find('10.5.') != -1 or m_version.find('10.4.') != -1:
                accept = self.map_to_list(panelMysql.panelMysql().query("select Host from mysql.user where User='" + name + "' AND Host!='localhost'"))
                result = mysql_obj.execute("ALTER USER `%s`@`localhost` IDENTIFIED BY '%s'" % (username,newpassword))
                for my_host in accept:
                    mysql_obj.execute("ALTER USER `%s`@`%s` IDENTIFIED BY '%s'" % (username,my_host[0],newpassword))
            else:
                result = mysql_obj.execute("update mysql.user set Password=password('" + newpassword + "') where User='" + username + "'")
            
            isError=self.IsSqlError(result)
            if  isError != None: return isError

            mysql_obj.execute("flush privileges")
            #if result==False: return public.returnMsg(False,'DATABASE_PASS_ERR_NOT_EXISTS')
            #修改SQLITE
            if int(id) > 0:
                public.M('databases').where("id=?",(id,)).setField('password',newpassword)
            else:
                public.M('config').where("id=?",(id,)).setField('mysql_root',newpassword)
                session['config']['mysql_root'] = newpassword
            
            public.WriteLog("TYPE_DATABASE",'DATABASE_PASS_SUCCESS',(name,))
            return public.returnMsg(True,'DATABASE_PASS_SUCCESS',(name,))
        except Exception as ex:
            import traceback
            public.WriteLog("TYPE_DATABASE", 'DATABASE_PASS_ERROR',(username,traceback.format_exc(limit=True).replace('\n','<br>')))
            return public.returnMsg(False,'DATABASE_PASS_ERROR',(name,))    
    
    #备份
    def ToBackup(self,get):
        #try:
        result = panelMysql.panelMysql().execute("show databases")
        isError=self.IsSqlError(result)
        if isError: return isError
        id = get['id']
        name = public.M('databases').where("id=?",(id,)).getField('name')
        root = public.M('config').where('id=?',(1,)).getField('mysql_root')
        if not os.path.exists(session['config']['backup_path'] + '/database'): public.ExecShell('mkdir -p ' + session['config']['backup_path'] + '/database')
        if not self.mypass(True, root):return public.returnMsg(False, 'MYSQL_CONF_ERR')
        
        fileName = name + '_' + time.strftime('%Y%m%d_%H%M%S',time.localtime()) + '.sql.gz'
        backupName = session['config']['backup_path'] + '/database/' + fileName

        try:
            password = public.M('config').where('id=?',(1,)).getField('mysql_root')
            os.environ["MYSQL_PWD"] = password
            public.ExecShell("/www/server/mysql/bin/mysqldump -R -E --default-character-set="+ public.get_database_character(name) +" --force --opt \"" + name + "\"  -u root | gzip > " + backupName)
        except Exception as e:
            raise
        finally:
            os.environ["MYSQL_PWD"] = ""

        if not os.path.exists(backupName): return public.returnMsg(False,'BACKUP_ERROR')
        
        self.mypass(False, root)
        
        sql = public.M('backup')
        addTime = time.strftime('%Y-%m-%d %X',time.localtime())
        sql.add('type,name,pid,filename,size,addtime',(1,fileName,id,backupName,0,addTime))
        public.WriteLog("TYPE_DATABASE", "DATABASE_BACKUP_SUCCESS",(name,))
        return public.returnMsg(True, 'BACKUP_SUCCESS')
        #except Exception as ex:
            #public.WriteLog("数据库管理", "备份数据库[" + name + "]失败 => "  +  str(ex))
            #return public.returnMsg(False,'备份失败!')
    
    #删除备份文件
    def DelBackup(self,get):
        try:
            id = get.id
            where = "id=?"
            filename = public.M('backup').where(where,(id,)).getField('filename')
            if os.path.exists(filename): os.remove(filename)
            name=''
            if filename == 'qiniu':
                name = public.M('backup').where(where,(id,)).getField('name')
                public.ExecShell(public.get_python_bin() + " "+public.GetConfigValue('setup_path') + '/panel/script/backup_qiniu.py delete_file ' + name)
            
            public.M('backup').where(where,(id,)).delete()
            public.WriteLog("TYPE_DATABASE", 'DATABASE_BACKUP_DEL_SUCCESS',(name,filename))
            return public.returnMsg(True, 'DEL_SUCCESS')
        except Exception as ex:
            public.WriteLog("TYPE_DATABASE", 'DATABASE_BACKUP_DEL_ERR',(name,filename,str(ex)))
            return public.returnMsg(False,'DEL_ERROR')
    
    #导入
    def InputSql(self, get):
        # try:
        result = panelMysql.panelMysql().execute("show databases")
        isError = self.IsSqlError(result)
        if isError: return isError
        name = get['name']
        file = get['file']
        if "|" in file:
            file = file.split('|')[-1]
        root = public.M('config').where('id=?', (1,)).getField('mysql_root')
        tmp = file.split('.')
        exts = ['sql', 'gz', 'zip']
        ext = tmp[len(tmp) - 1]
        if ext not in exts:
            return public.returnMsg(False, 'DATABASE_INPUT_ERR_FORMAT')
        isgzip = False
        if ext != 'sql':
            import panel_restore
            tmp = file.split('/')
            tmpFile = tmp[len(tmp) - 1]
            tmpFile = tmpFile.replace('.sql.' + ext, '.sql')
            tmpFile = tmpFile.replace('.' + ext, '.sql')
            tmpFile = tmpFile.replace('tar.', '')
            # return tmpFile
            backupPath = session['config']['backup_path'] + '/database'
            panel_restore.panel_restore().restore_db_backup(get)
            if ext == 'zip':
                public.ExecShell("cd "  +  backupPath  +  " && unzip " + '"'+file+'"')
            else:
                public.ExecShell("cd "  +  backupPath  +  " && tar zxf " +  '"'+file+'"')
                if not os.path.exists(backupPath  +  "/"  +  tmpFile):
                    public.ExecShell("cd "  +  backupPath  +  " && gunzip -q " +  '"'+file+'"')
                    isgzip = True
            if not os.path.exists(backupPath + '/' + tmpFile) or tmpFile == '': return public.returnMsg(False, 'FILE_NOT_EXISTS',(tmpFile,))

            try:
                password = public.M('config').where('id=?',(1,)).getField('mysql_root')
                os.environ["MYSQL_PWD"] = password
                public.ExecShell(public.GetConfigValue('setup_path') + "/mysql/bin/mysql -uroot -p" + root + " --force \"" + name + "\" < " +'"'+ backupPath + '/' +tmpFile+'"')
            except Exception as e:
                raise
            finally:
                os.environ["MYSQL_PWD"] = ""



            if isgzip:
                public.ExecShell('cd ' +backupPath+ ' && gzip ' + file.split('/')[-1][:-3])
            else:
                public.ExecShell("rm -f " +  backupPath + '/' +tmpFile)
        else:
            try:
                password = public.M('config').where('id=?',(1,)).getField('mysql_root')
                os.environ["MYSQL_PWD"] = password
                public.ExecShell(public.GetConfigValue('setup_path') + "/mysql/bin/mysql -uroot -p" + root + " --force \"" + name + "\" < "+'"' +  file+'"')
            except Exception as e:
                raise
            finally:
                os.environ["MYSQL_PWD"] = ""

        public.WriteLog("TYPE_DATABASE", 'DATABASE_INPUT_SUCCESS',(name,))
        return public.returnMsg(True, 'DATABASE_INPUT_SUCCESS')
        #except Exception as ex:
            #public.WriteLog("TYPE_DATABASE", 'DATABASE_INPUT_ERR',(name,str(ex)))
            #return public.returnMsg(False,'DATABASE_INPUT_ERR')
    
    #同步数据库到服务器
    def SyncToDatabases(self,get):
        result = panelMysql.panelMysql().execute("show databases")
        isError=self.IsSqlError(result)
        if isError: return isError
        type = int(get['type'])
        n = 0
        sql = public.M('databases')
        if type == 0:
            data = sql.field('id,name,username,password,accept').select()
            for value in data:
                result = self.ToDataBase(value)
                if result == 1: n +=1
        else:
            import json
            data = json.loads(get.ids)
            for value in data:
                find = sql.where("id=?",(value,)).field('id,name,username,password,accept').find()   
                result = self.ToDataBase(find)
                if result == 1: n +=1
        
        return public.returnMsg(True,'DATABASE_SYNC_SUCCESS',(str(n),))
    
    #配置
    def mypass(self,act,password = None):
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

    #添加到服务器
    def ToDataBase(self,find):
        #if find['username'] == 'bt_default': return 0
        if len(find['password']) < 3 :
            find['username'] = find['name']
            find['password'] = public.md5(str(time.time()) + find['name'])[0:10]
            public.M('databases').where("id=?",(find['id'],)).save('password,username',(find['password'],find['username']))
        
        result = panelMysql.panelMysql().execute("create database `" + find['name'] + "`")
        if "using password:" in str(result): return -1
        if "Connection refused" in str(result): return -1
       
        password = find['password']
        #if find['password']!="" and len(find['password']) > 20:
            #password = find['password']
        
        self.__CreateUsers(find['name'],find['username'],password,find['accept'])
        return 1
    
    
    #从服务器获取数据库
    def SyncGetDatabases(self,get):
        data = panelMysql.panelMysql().query("show databases")
        isError = self.IsSqlError(data)
        if isError != None: return isError
        users = panelMysql.panelMysql().query("select User,Host from mysql.user where User!='root' AND Host!='localhost' AND Host!=''")
        if type(users) == str: return public.returnMsg(False,users)
        
        sql = public.M('databases')
        nameArr = ['information_schema','performance_schema','mysql','sys']
        n = 0
        for  value in data:
            b = False
            for key in nameArr:
                if value[0] == key:
                    b = True 
                    break
            if b:continue
            if sql.where("name=?",(value[0],)).count(): continue
            host = '127.0.0.1'
            for user in users:
                if value[0] == user[0]:
                    host = user[1]
                    break
                
            ps = public.getMsg('INPUT_PS')
            if value[0] == 'test':
                    ps = public.getMsg('DATABASE_TEST')
            addTime = time.strftime('%Y-%m-%d %X',time.localtime())
            if sql.table('databases').add('name,username,password,accept,ps,addtime',(value[0],value[0],'',host,ps,addTime)): n +=1
        
        return public.returnMsg(True,'DATABASE_GET_SUCCESS',(str(n),))
    
    
    #获取数据库权限
    def GetDatabaseAccess(self,get):
        name = get['name']
        users = panelMysql.panelMysql().query("select Host,ssl_type from mysql.user where User='" + name + "' AND Host!='localhost'")
        ssl_type = panelMysql.panelMysql().query("select ssl_type from mysql.user where User='%s'" % name)
        isError = self.IsSqlError(users)
        if isError != None: return isError
        users = self.map_to_list(users)
        if ssl_type:
            ssl_type = ssl_type[0][0]
        if len(users)<1:
            return public.returnMsg(True,{"permission":"127.0.0.1","ssl":ssl_type})
        
        accs = []
        for c in users:
            accs.append(c[0])
        userStr = ','.join(accs)
        return public.returnMsg(True,{"permission":userStr,"ssl":ssl_type})
    
    #设置数据库权限
    def SetDatabaseAccess(self,get):
        ssl = ""
        if hasattr(get,'ssl'):
            ssl = get.ssl
        if ssl == "REQUIRE SSL" and not self.check_mysql_ssl_status(get):
            return public.returnMsg(False,'SSL is not enabled in the database, please open it in the Mysql manager first')
        name = get['name']
        db_name = public.M('databases').where('username=?',(name,)).getField('name')
        access = get['access']
        password = public.M('databases').where("username=?",(name,)).getField('password')
        mysql_obj = panelMysql.panelMysql()
        result = mysql_obj.query("show databases")
        isError = self.IsSqlError(result)
        if isError != None: return isError
        users = mysql_obj.query("select Host from mysql.user where User='" + name + "' AND Host!='localhost'")
        for us in users:
            mysql_obj.execute("drop user '" + name + "'@'" + us[0] + "'")
        self.__CreateUsers(db_name,name,password,access,ssl)
        return public.returnMsg(True, 'SET_SUCCESS')

    #获取数据库配置信息
    def GetMySQLInfo(self,get):
        data = {}
        try:
            public.CheckMyCnf()
            myfile = '/etc/my.cnf'
            mycnf = public.readFile(myfile)
            rep = "datadir\s*=\s*(.+)\n"
            data['datadir'] = re.search(rep,mycnf).groups()[0]
            rep = "port\s*=\s*([0-9]+)\s*\n"
            data['port'] = re.search(rep,mycnf).groups()[0]
        except:
            data['datadir'] = '/www/server/data'
            data['port'] = '3306'
        return data
    
    #修改数据库目录
    def SetDataDir(self,get):
        if get.datadir[-1] == '/': get.datadir = get.datadir[0:-1]
        if not os.path.exists(get.datadir): public.ExecShell('mkdir -p ' + get.datadir)
        mysqlInfo = self.GetMySQLInfo(get)
        if mysqlInfo['datadir'] == get.datadir: return public.returnMsg(False,'DATABASE_MOVE_RE')
        
        public.ExecShell('/etc/init.d/mysqld stop')
        public.ExecShell('\cp -arf ' + mysqlInfo['datadir'] + '/* ' + get.datadir + '/')
        public.ExecShell('chown -R mysql.mysql ' + get.datadir)
        public.ExecShell('chmod -R 755 ' + get.datadir)
        public.ExecShell('rm -f ' + get.datadir + '/*.pid')
        public.ExecShell('rm -f ' + get.datadir + '/*.err')
        
        public.CheckMyCnf()
        myfile = '/etc/my.cnf'
        mycnf = public.readFile(myfile)
        public.writeFile('/etc/my_backup.cnf',mycnf)
        mycnf = mycnf.replace(mysqlInfo['datadir'],get.datadir)
        public.writeFile(myfile,mycnf)
        public.ExecShell('/etc/init.d/mysqld start')
        result = public.ExecShell('ps aux|grep mysqld|grep -v grep')
        if len(result[0]) > 10:
            public.writeFile('data/datadir.pl',get.datadir)
            return public.returnMsg(True,'DATABASE_MOVE_SUCCESS')
        else:
            public.ExecShell('pkill -9 mysqld')
            public.writeFile(myfile,public.readFile('/etc/my_backup.cnf'))
            public.ExecShell('/etc/init.d/mysqld start')
            return public.returnMsg(False,'DATABASE_MOVE_ERR')
    
    #修改数据库端口
    def SetMySQLPort(self,get):
        myfile = '/etc/my.cnf'
        mycnf = public.readFile(myfile)
        rep = r"port\s*=\s*([0-9]+)\s*\n"
        mycnf = re.sub(rep,'port = ' + get.port + '\n',mycnf)
        public.writeFile(myfile,mycnf)
        public.ExecShell('/etc/init.d/mysqld restart')
        return public.returnMsg(True,'EDIT_SUCCESS')
    
    #获取错误日志
    def GetErrorLog(self,get):
        path = self.GetMySQLInfo(get)['datadir']
        filename = ''
        for n in os.listdir(path):
            if len(n) < 5: continue
            if n[-3:] == 'err': 
                filename = path + '/' + n
                break
        if not os.path.exists(filename): return public.returnMsg(False,'FILE_NOT_EXISTS')
        if hasattr(get,'close'): 
            public.writeFile(filename,'')
            return public.returnMsg(True,'LOG_CLOSE')
        return public.GetNumLines(filename,1000)
    
    #二进制日志开关
    def BinLog(self,get):
        myfile = '/etc/my.cnf'
        mycnf = public.readFile(myfile)
        masterslaveconf = "/www/server/panel/plugin/masterslave/data.json"
        if mycnf.find('#log-bin=mysql-bin') != -1:
            if hasattr(get,'status'): return public.returnMsg(False,'0')
            mycnf = mycnf.replace('#log-bin=mysql-bin','log-bin=mysql-bin')
            mycnf = mycnf.replace('#binlog_format=mixed','binlog_format=mixed')
            public.ExecShell('sync')
            public.ExecShell('/etc/init.d/mysqld restart')
        else:
            path = self.GetMySQLInfo(get)['datadir']
            if not os.path.exists(path): return public.returnMsg(False,'MYSQL_DATA_DIR_ERR')
            if hasattr(get,'status'):
                dsize = 0
                for n in os.listdir(path):
                    if len(n) < 9: continue
                    if n[0:9] == 'mysql-bin':
                        dsize += os.path.getsize(path + '/' + n)
                return public.returnMsg(True,dsize)
            if os.path.exists(masterslaveconf):
                return public.returnMsg(False, "MYSQL_BINLOG_ERR")
            mycnf = mycnf.replace('log-bin=mysql-bin','#log-bin=mysql-bin')
            mycnf = mycnf.replace('binlog_format=mixed','#binlog_format=mixed')
            public.ExecShell('sync')
            public.ExecShell('/etc/init.d/mysqld restart')
            public.ExecShell('rm -f ' + path + '/mysql-bin.*')
        
        public.writeFile(myfile,mycnf)
        return public.returnMsg(True,'SUCCESS')
    
    #获取MySQL配置状态
    def GetDbStatus(self,get):
        result = {}
        data = self.map_to_list( panelMysql.panelMysql().query('show variables'))
        gets = ['table_open_cache','thread_cache_size','query_cache_type','key_buffer_size','query_cache_size','tmp_table_size','max_heap_table_size','innodb_buffer_pool_size','innodb_additional_mem_pool_size','innodb_log_buffer_size','max_connections','sort_buffer_size','read_buffer_size','read_rnd_buffer_size','join_buffer_size','thread_stack','binlog_cache_size']
        result['mem'] = {}
        for d in data:
            try:
                for g in gets:
                    if d[0] == g: result['mem'][g] = d[1]
            except:
                continue

        if 'query_cache_type' in result['mem']:
            if result['mem']['query_cache_type'] != 'ON': result['mem']['query_cache_size'] = '0'
        return result
    
    #设置MySQL配置参数
    def SetDbConf(self,get):
        gets = ['key_buffer_size','query_cache_size','tmp_table_size','max_heap_table_size','innodb_buffer_pool_size','innodb_log_buffer_size','max_connections','query_cache_type','table_open_cache','thread_cache_size','sort_buffer_size','read_buffer_size','read_rnd_buffer_size','join_buffer_size','thread_stack','binlog_cache_size']
        emptys = ['max_connections','query_cache_type','thread_cache_size','table_open_cache']
        mycnf = public.readFile('/etc/my.cnf')
        n = 0
        m_version = public.readFile('/www/server/mysql/version.pl')
        if not m_version: m_version = ''
        for g in gets:
            if m_version.find('8.') == 0 and g in ['query_cache_type','query_cache_size']:
                n += 1
                continue
            s = 'M'
            if n > 5 and not g in ['key_buffer_size','query_cache_size','tmp_table_size','max_heap_table_size','innodb_buffer_pool_size','innodb_log_buffer_size']: s = 'K'
            if g in emptys: s = ''
            if g in ['innodb_log_buffer_size']:
                s = 'M'
                if int(get[g]) < 8:
                    return public.returnMsg(False,'MYSQL_PARAMETER_ERR')

            rep = r'\s*'+g+r'\s*=\s*\d+(M|K|k|m|G)?\n'

            c = g+' = ' + get[g] + s +'\n'
            if mycnf.find(g) != -1:
                mycnf = re.sub(rep,'\n'+c,mycnf,1)
            else:
                mycnf = mycnf.replace('[mysqld]\n','[mysqld]\n' +c)
            n+=1
        public.writeFile('/etc/my.cnf',mycnf)
        return public.returnMsg(True,'SET_SUCCESS')
    
    #获取MySQL运行状态
    def GetRunStatus(self,get):
        import time
        result = {}
        data = panelMysql.panelMysql().query('show global status')
        gets = ['Max_used_connections','Com_commit','Com_rollback','Questions','Innodb_buffer_pool_reads','Innodb_buffer_pool_read_requests','Key_reads','Key_read_requests','Key_writes','Key_write_requests','Qcache_hits','Qcache_inserts','Bytes_received','Bytes_sent','Aborted_clients','Aborted_connects','Created_tmp_disk_tables','Created_tmp_tables','Innodb_buffer_pool_pages_dirty','Opened_files','Open_tables','Opened_tables','Select_full_join','Select_range_check','Sort_merge_passes','Table_locks_waited','Threads_cached','Threads_connected','Threads_created','Threads_running','Connections','Uptime']
        try:
            if data[0] == 1045:
                return public.returnMsg(False,'MYSQL_PASS_ERR')
            for d in data:
                for g in gets:
                    try:
                        if d[0] == g: result[g] = d[1]
                    except:
                        pass
        except:
            return public.returnMsg(False,str(data))

        if not 'Run' in result and result:
            result['Run'] = int(time.time()) - int(result['Uptime'])
        tmp = panelMysql.panelMysql().query('show master status')
        try:

            result['File'] = tmp[0][0]
            result['Position'] = tmp[0][1]
        except:
            result['File'] = 'OFF'
            result['Position'] = 'OFF'
        return result
    

    #取慢日志
    def GetSlowLogs(self,get):
        path = self.GetMySQLInfo(get)['datadir'] + '/mysql-slow.log'
        if not os.path.exists(path): return public.returnMsg(False,'AJAX_LOG_FILR_NOT_EXISTS')
        return public.returnMsg(True,public.GetNumLines(path,100))


    # 获取当前数据库信息
    def GetInfo(self,get):
        info=self.GetdataInfo(get)
        return info
        if info:
            return info
        else:
            return public.returnMsg(False,"GET_DB_ERR")
    
    #修复表信息
    def ReTable(self,get):
        m_version = public.readFile(public.GetConfigValue('setup_path') + '/mysql/version.pl')
        if m_version.find('5.1.')!=-1:return public.returnMsg(False,"NONSUPPORT51")
        info=self.RepairTable(get)
        if info:
            return public.returnMsg(True,"REPAIR_SUCCESS")
        else:
            return public.returnMsg(False,"REPAIR_FAILURE")
    
    # 优化表
    def OpTable(self,get):
        info=self.OptimizeTable(get)
        if info:
            return public.returnMsg(True,"OPTIMIZED_SUCCESS")
        else:
            return public.returnMsg(False,"OPTIMIZED_FAIL_OR_ALREADY_OPTIMIZED")

    #更改表引擎
    def AlTable(self,get):
        info=self.AlterTable(get)
        if info:
            return public.returnMsg(True,"CHANGE_SUCCESS")
        else:
            return public.returnMsg(False,"CHANVE_FAIL")

    # 检查用户管理表是否存在
    def _check_table_exist(self):
        result = public.M('sqlite_master').where("name=?", ('mysql_user',)).getField('name')
        if not result:
            self._create_mysql_user_tb()

    # 数据库对象
    def _get_sqlite_connect(self):
        import sqlite3
        try:
            if not self.sqlite_connection:
                self.sqlite_connection = sqlite3.connect('data/default.db')
        except Exception as ex:
            return "error: " + str(ex)

    # 创多用户表
    def _create_mysql_user_tb(self):
        self._get_sqlite_connect()
        sql="""
CREATE TABLE mysql_user(
   id INTEGER  PRIMARY KEY AUTOINCREMENT,
   pid INTEGER ,
   username CHAR,
   password CHAR,
   accept CHAR,
   ps CHAR,
   addtime CHAR
);"""
        self.sqlite_connection.execute(sql)

    # 根据id获取用户列表
    def get_mysql_user(self,get):
        self._create_mysql_user_tb()
        result = public.M('mysql_user').where("pid=?", (get.id,)).select()
        return result

    def add_mysql_user(self,get):
        '''
         * 添加mysql用户
         * @param get.id 面板数据库id
         * @param get.username 添加的用户
         * @param get.password 添加的用户密码
         * @param get.permission 添加的用户权限
         * @param get.host 允许在哪里访问
         * @return Bool
        '''
