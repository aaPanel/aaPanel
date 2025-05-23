# coding: utf-8
# -------------------------------------------------------------------
# aaPanel
# -------------------------------------------------------------------
# Copyright (c) 2015-2017 aaPanel(www.aapanel.com) All rights reserved.
# -------------------------------------------------------------------
# Author: hwliang <hwl@aapanel.com>
# -------------------------------------------------------------------
# ------------------------------
# 数据库管理类
# ------------------------------
import os
import time
import json
import re
import sys

import public, db, panelMysql
import datatool_v2 as datatool
import db_mysql
from public.validate import Param

class database(datatool.datatools):
    _MYSQL_CNF = "/etc/my.cnf"
    _DB_BACKUP_DIR = os.path.join(public.M("config").where("id=?", (1,)).getField("backup_path"), "database")
    _MYSQL_BACKUP_DIR = os.path.join(_DB_BACKUP_DIR, "mysql")
    _MYSQLDUMP_BIN = public.get_mysqldump_bin()
    _MYSQL_BIN = public.get_mysql_bin()

    sqlite_connection = None

    def __init__(self):
        if not os.path.exists(self._MYSQL_BACKUP_DIR):
            os.makedirs(self._MYSQL_BACKUP_DIR)

    sid = 0

    def __check_mysql_query_error(self, result):
        isError = self.IsSqlError(result)
        if isError is not None:
            return public.return_message(-1, 0, isError)

    # mysql 在使用
    def AddCloudServer(self, get):
        '''
            @name 添加远程服务器
            @author hwliang<2021-01-10>
            @param db_host<string> 服务器地址
            @param db_port<port> 数据库端口
            @param db_user<string> 用户名
            @param db_password<string> 数据库密码
            @param db_ps<string> 数据库备注
            @return dict
        '''
        # 校验参数
        try:
            get.validate([
                Param('db_host').Require(),
                Param('db_port').Require().Number(">=", 1).Number("<=", 65535),
                Param('db_user').Require().String(),
                Param('db_password').Require().String(),
                Param('db_ps').Require().String(),
                Param('type').Require().String(),

            ], [
                public.validate.trim_filter(),
            ])
        except Exception as ex:
            public.print_log("error info: {}".format(ex))
            return public.return_message(-1, 0, str(ex))


        get.db_name = None
        res = self.CheckCloudDatabase(get)
        if isinstance(res, dict):
            # return res
            info1 = res.get("msg", "Database unable to connect!")
            return public.return_message(-1, 0, info1)
            # return public.return_message(-1, 0, public.lang("Database unable to connect!"))
        if public.M('database_servers').where('db_host=? AND db_port=?', (get.db_host, get.db_port)).count():
            # return public.return_msg_gettext(False, 'The specified server already exists: [{}:{}]', (get.db_host, get.db_port))
            return public.return_message(-1, 0, public.lang("The specified server already exists: [{}:{}]", get.db_host, get.db_port))

        get.db_port = int(get.db_port)
        pdata = {
            'db_host': get.db_host,
            'db_port': get.db_port,
            'db_user': get.db_user,
            'db_password': get.db_password,
            'ps': public.xssencode2(get.db_ps.strip()),
            'addtime': int(time.time())
        }

        result = public.M("database_servers").insert(pdata)

        if isinstance(result, int):
            public.write_log_gettext('Database manager', 'Add remote MySQL server [{}:{}]', (get.db_host, get.db_port))
            # return public.return_msg_gettext(True, public.lang("Setup successfully!"))
            return public.return_message(0, 0, public.lang("Setup successfully!"))
        # return public.return_msg_gettext(False, 'Add failed: {}', (result,))
        return public.return_message(-1, 0, 'Add failed: {}', (result,))

    def GetCloudServer(self, get):
        '''
            @name 获取远程服务器列表
            @author hwliang<2021-01-10>
            @return list
        '''
        data = public.M('database_servers').where("LOWER(db_type)=LOWER('mysql')", ()).select()
        bt_mysql_bin = '{}/mysql/bin/mysql'.format(public.get_setup_path())

        if not isinstance(data, list): data = []
        if os.path.exists(bt_mysql_bin):
            data.insert(0, {'id': 0, 'db_host': '127.0.0.1', 'db_port': 3306, 'db_user': 'root', 'db_password': '',
                            'ps': 'LocalServer', 'addtime': 0})
        # return data
        return public.return_message(0, 0,  data)

    def RemoveCloudServer(self, get):
        '''
            @name 删除远程服务器
            @author hwliang<2021-01-10>
            @param id<int> 远程服务器ID
            @return dict
        '''
        # 校验参数
        try:
            get.validate([
                Param('id').Require().Integer(),

            ], [
                public.validate.trim_filter(),
            ])
        except Exception as ex:
            public.print_log("error info: {}".format(ex))
            return public.return_message(-1, 0, str(ex))


        id = int(get.id)

        db_find = public.M('database_servers').where('id=?', (id,)).find()
        if not db_find:

            return public.return_message(-1, 0, public.lang("The specified server dose not exists!"))
        public.M('databases').where('sid=?', id).delete()
        result = public.M('database_servers').where('id=?', id).delete()
        if isinstance(result, int):
            public.WriteLog('Database manager', 'Delete the remote MySQL server [{}:{}]',
                            (db_find['db_host'], int(db_find['db_port'])))

            return public.return_message(0, 0, public.lang("Successfully deleted!"))

        return public.return_message(-1, 0, 'Failed to delete: {}', (result,))

    def ModifyCloudServer(self, get):
        '''
            @name 修改远程服务器
            @author hwliang<2021-01-10>
            @param id<int> 远程服务器ID
            @param db_host<string> 服务器地址
            @param db_port<port> 数据库端口
            @param db_user<string> 用户名
            @param db_password<string> 数据库密码
            @param db_ps<string> 数据库备注
            @return dict
        '''
        # 校验参数
        try:
            get.validate([
                Param('db_host').Require(),
                Param('db_port').Require().Number(">=", 1).Number("<=", 65535),
                Param('db_user').Require().String(),
                Param('db_password').Require().String(),
                Param('db_ps').Require().String(),
                Param('id').Require().Integer(),
            ], [
                public.validate.trim_filter(),
            ])
        except Exception as ex:
            public.print_log("error info: {}".format(ex))
            return public.return_message(-1, 0, str(ex))


        id = int(get.id)
        get.db_port = int(get.db_port)
        db_find = public.M('database_servers').where('id=?', (id,)).find()
        if not db_find:

            return public.return_message(-1, 0, public.lang("The specified server dose not exists!"))
        _modify = False
        if db_find['db_host'] != get.db_host or db_find['db_port'] != get.db_port:
            _modify = True
            if public.M('database_servers').where('db_host=? AND db_port=?', (get.db_host, get.db_port)).count():

                return public.return_message(-1, 0, public.lang("The specified server already exists: [{}:{}]", get.db_host, get.db_port))

        if db_find['db_user'] != get.db_user or db_find['db_password'] != get.db_password:
            _modify = True

        if _modify:
            res = self.CheckCloudDatabase(get)
            if isinstance(res, dict):
                # return res
                info1 = res.get("msg", "Database unable to connect")
                return public.return_message(-1, 0, info1)

        pdata = {
            'db_host': get.db_host,
            'db_port': get.db_port,
            'db_user': get.db_user,
            'db_password': get.db_password,
            'ps': public.xssencode2(get.db_ps.strip())
        }

        result = public.M("database_servers").where('id=?', (id,)).update(pdata)
        if isinstance(result, int):
            public.WriteLog('Database manager', 'Edit remote MySQL server [{}:{}]', (get.db_host, get.db_port))

            return public.return_message(0, 0, public.lang("Setup successfully!"))

        return public.return_message(-1, 0, public.lang("Fail to edit: {}", result))

    def AddCloudDatabase(self, get):
        '''
            @name 添加远程数据库
            @author hwliang<2022-01-06>
            @param db_host<string> 服务器地址
            @param db_port<port> 数据库端口
            @param db_user<string> 用户名
            @param db_name<string> 数据库名称
            @param db_password<string> 数据库密码
            @param db_ps<string> 数据库备注
            @return dict
        '''

        # 校验参数
        try:
            get.validate([
                Param('db_host').Require(),
                Param('db_port').Require().Number(">=", 1).Number("<=", 65535),
                Param('db_user').Require().String(),
                Param('db_password').Require().String(),
                Param('db_name').Require().String(),
                Param('db_ps').Require().String(),
            ], [
                public.validate.trim_filter(),
            ])
        except Exception as ex:
            public.print_log("error info: {}".format(ex))
            return public.return_message(-1, 0, str(ex))



        # 检查数据库是否能连接
        res = self.CheckCloudDatabase(get)
        if isinstance(res, dict):
            # return res
            info1 = res.get("msg", "Database unable to connect")
            return public.return_message(-1, 0, info1)

        if public.M('databases').where('name=?', (get.db_name,)).count():
            # return public.return_msg_gettext(False, "A database with the same name already exists: [{}]",(get.db_name,))
            return public.return_msg_gettext(False, public.lang("A database with the same name already exists: [{}]", get.db_name))
        get.db_port = int(get.db_port)
        conn_config = {
            'db_host': get.db_host,
            'db_port': get.db_port,
            'db_user': get.db_user,
            'db_password': get.db_password,
            'db_name': get.db_name
        }

        pdata = {
            'name': get.db_name,
            'ps': get.db_ps,
            'conn_config': json.dumps(conn_config),
            'db_type': '1',
            'username': get.db_user,
            'password': get.db_password,
            'accept': '127.0.0.1',
            'addtime': time.strftime('%Y-%m-%d %X', time.localtime()),
            'pid': 0
        }

        result = public.M('databases').insert(pdata)
        if isinstance(result, int):
            public.write_log_gettext('Database manager', 'Add remote MySQL database [{}] successfully', (get.db_name,))
            # return public.return_msg_gettext(True, public.lang("Setup successfully!"))
            return public.return_message(0, 0, public.lang("Setup successfully!"))
        # return public.return_msg_gettext(False, 'Add failed: {}', (result,))
        return public.return_message(-1, 0, 'Add failed: {}', (result,))

    def CheckCloudDatabase(self, conn_config):
        '''
            @name 检查远程数据库信息是否正确
            @author hwliang<2022-01-06>
            @param conn_config<dict> 连接信息
                db_host<string> 服务器地址
                db_port<port> 数据库端口
                db_user<string> 用户名
                db_name<string> 数据库名称
                db_password<string> 数据库密码
            @return True / dict
        '''
        try:
            if not 'db_name' in conn_config: conn_config['db_name'] = None
            mysql_obj = db_mysql.panelMysql()
            mysql_obj.set_host(conn_config['db_host'], conn_config['db_port'], conn_config['db_name'],
                               conn_config['db_user'], conn_config['db_password'])
            result = mysql_obj.query("show databases")
            if isinstance(result, str):
                if mysql_obj._ex:
                    return public.returnMsg(False, self.GetMySQLError(mysql_obj._ex))
                else:
                    return public.returnMsg(False, self.GetMySQLError(result))
            if not conn_config['db_name']: return True
            for i in result:
                if i[0] == conn_config['db_name']:
                    return True
            return public.returnMsg(False, public.lang("The specified database does not exist!"))
        except Exception as ex:
            res = self.GetMySQLError(ex)
            if not res: res = str(ex)
            return public.returnMsg(False, res)

    def GetMySQLError(self, e):
        if isinstance(e, str):
            return e
        res = ''
        if e.args[0] == 1045:
            res = public.gettext_msg("Wrong user name or password!")
        if e.args[0] == 1049:
            res = public.gettext_msg("Database does NOT exist!")
        if e.args[0] == 1044:
            res = public.gettext_msg("No access rights, or the database does not exist!")
        if e.args[0] == 1062:
            res = public.gettext_msg("Database exists!")
        if e.args[0] == 1146:
            res = public.gettext_msg('Database table does not exist!')
        if e.args[0] == 2003:
            res = public.gettext_msg('Fail to connect to the server!')
        if res:
            res = res + "<pre>" + str(e) + "</pre>"
        else:
            res = str(e)
        return res

    # 检查mysql是否存在空用户密码
    def _check_empty_user_passwd(self):
        mysql_obj = panelMysql.panelMysql()
        mysql_obj.execute("delete from mysql.user where user='' and password=''")

    # 添加数据库
    def AddDatabase(self, get):
        try:
            # 校验参数
            try:
                get.validate([
                    # Param('name').Require().String('in', ['root', 'mysql', 'test', 'sys', 'panel_logs']),
                    # Param('db_user').Require().String('in', ['root', 'mysql', 'test', 'sys', 'panel_logs']),
                    Param('name').Require().String(),
                    Param('db_user').Require().String(),
                    Param('codeing').Require().String(),
                    Param('password').Require().String(),
                    # Param('dataAccess').Require(),
                    Param('sid').Require().Integer(),
                    Param('active').Require().Bool(),
                    Param('address').Require(),
                    Param('ps').Require().String(),
                    Param('ssl').String(),
                    Param('dtype').Require().String(),
                ], [
                    public.validate.trim_filter(),
                ])
            except Exception as ex:
                public.print_log("error info: {}".format(ex))
                return public.return_message(-1, 0, str(ex))

            # try:
            self._check_empty_user_passwd()
            ssl = ""
            if hasattr(get, "ssl"):
                ssl = get.ssl
            if ssl == "REQUIRE SSL" and not self.check_mysql_ssl_status(get)["message"].get("status"):

                return public.return_message(-1, 0, public.lang("SSL is not enabled in the database, please open it in the Mysql manager first"))
            data_name = get['name'].strip().lower()

            if self.CheckRecycleBin(data_name):
                return public.return_message(-1, 0, public.lang("Database [{}] already at the recycle bin, please recover from the recycle bin!", data_name))
            if len(data_name) > 64:

                return public.return_message(-1, 0, public.lang("Database name cannot be more than 16 characters"))
            reg = r"^[\w\.-]+$"
            username = get.db_user.strip()

            if not re.match(reg, data_name):

                return public.return_message(-1, 0, public.lang("Database name cannot contain special characters"))

            if not re.match(reg, username):

                return public.return_message(-1, 0, public.lang("Database name is illegal"))
            if not hasattr(get, 'db_user'):
                get.db_user = data_name

            checks = ['root', 'mysql', 'test', 'sys', 'panel_logs']
            if username in checks or len(username) < 1:
                return public.return_msg_gettext(False, public.lang("Database username is illegal!"))
            if data_name in checks or len(data_name) < 1:
                return public.return_msg_gettext(False, public.lang("Database name is illegal!"))
            data_pwd = get['password']
            if len(data_pwd) < 1:
                data_pwd = public.md5(str(time.time()))[0:16]

            sql = public.M('databases')
            if sql.where("name=?", (data_name)).count():
                # return public.return_msg_gettext(False, public.lang("Database exists!"))
                return public.return_message(-1, 0, public.lang("Database exists!"))
            if sql.where("username=?", (username)).count():
                return public.return_message(-1, 0, 'The user name already exists. For security reasons, we do not allow '
                                                   'one database user to manage multiple databases')
            address = get['address'].strip()
            if address in ['', 'ip']:

                return public.return_message(-1, 0, 'If the access permission is [Specified IP], '
                                                    'you need to enter the IP address!')

            user = '是'
            password = data_pwd

            codeing = get['codeing']

            wheres = {
                'utf8': 'utf8_general_ci',
                'utf8mb4': 'utf8mb4_general_ci',
                'gbk': 'gbk_chinese_ci',
                'big5': 'big5_chinese_ci'
            }
            codeStr = wheres[codeing]
            # 添加MYSQL
            self.sid = get.get('sid/d', 0)
            mysql_obj = public.get_mysql_obj_by_sid(self.sid)
            if not mysql_obj:
                # return public.returnMsg(False, public.lang("Failed to connect to the specified database"))
                return public.return_message(-1, 0, public.lang("Failed to connect to the specified database"))

            # 从MySQL验证是否存在
            if self.database_exists_for_mysql(mysql_obj, data_name):

                return public.return_message(-1, 0, public.lang("The specified database already exists in MySQL,please change the name!"))

            result = mysql_obj.execute(
                "create database `" + data_name + "` DEFAULT CHARACTER SET " + codeing + " COLLATE " + codeStr)


            isError = self.IsSqlError(result)
            if isError != None:
                # return isError
                return public.return_message(-1, 0, isError)
            mysql_obj.execute("drop user '" + username + "'@'localhost'")
            for a in address.split(','):
                mysql_obj.execute("drop user '" + username + "'@'" + a + "'")
            self.__CreateUsers(data_name, username, password, address, ssl)

            if get['ps'] == '': get['ps'] = public.lang('Edit notes')
            get['ps'] = public.xssencode2(get['ps'])
            addTime = time.strftime('%Y-%m-%d %X', time.localtime())

            pid = 0
            if hasattr(get, 'pid'): pid = get.pid
            # 添加入SQLITE
            db_type = 0
            if self.sid: db_type = 2
            sql.add('pid,sid,db_type,name,username,password,accept,ps,addtime',
                    (pid, self.sid, db_type, data_name, username, password, address, get['ps'], addTime))
            public.write_log_gettext("Database manager", 'Successfully added database [{}]!', (data_name,))

            return public.return_message(0, 0, public.lang("Setup successfully!"))


        except Exception as ex:
            public.print_log("error info666: {}".format(ex))
            return public.return_message(-1, 0, str(ex))

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
zip -q ssl.zip client-cert.pem client-key.pem ca.pem
""".format(ip=ip)
        public.ExecShell(openssl_command)

    # 写入mysqlssl到配置
    def write_ssl_to_mysql(self, get):
        return public.fail_v2("Not support now")
        ssl_original_path = """
ssl-ca=/www/server/mysql/mysql-test/std_data/cacert.pem
ssl-cert=/www/server/mysql/mysql-test/std_data//server-cert.pem
ssl-key=/www/server/mysql/mysql-test/std_data/server-key.pem
"""
        conf_file = "/etc/my.cnf"
        conf = public.readFile(conf_file)
        if not conf:
            return public.fail_v2("Configuration file not exist")
        status = self.check_mysql_ssl_status(get)["message"].get("status")
        # reg = "ssl-ca=/www.*\n.*\n.*server-key.pem\n"
        if status is False: # 当前关着
            conf = re.sub(r"\[mysqld]", "[mysqld]" + ssl_original_path, conf)
            # if os.path.exists('/www/server/mysql/mysql-test/std_data/server-cert.pem'):
            #     conf = re.sub(r'\[mysqld\]', '[mysqld]\nskip_ssl', conf)
            public.writeFile(conf_file, conf)
            public.ExecShell('/etc/init.d/mysqld restart')
            return public.success_v2("support ssl successfully! Mysql Restart!")
        else:
            conf = re.sub(ssl_original_path, '', conf)
            # if "ssl-ca" not in conf:
            #     conf = re.sub(r'\[mysqld\]', '[mysqld]' + ssl_original_path, conf)
            # conf = re.sub('skip_ssl\n', '', conf)
            public.writeFile(conf_file, conf)
            public.ExecShell('/etc/init.d/mysqld restart')
            return public.success_v2("close ssl successfully! Mysql Restart!")

    # 检查mysqlssl状态
    def check_mysql_ssl_status(self, get):
        ssl_original_path = """
ssl-ca=/www/server/mysql/mysql-test/std_data/cacert.pem
ssl-cert=/www/server/mysql/mysql-test/std_data//server-cert.pem
ssl-key=/www/server/mysql/mysql-test/std_data/server-key.pem
"""
        conf_file = "/etc/my.cnf"
        conf = public.readFile(conf_file)
        if not conf:
            return public.fail_v2("Configuration file not exist")
        if re.search(ssl_original_path, conf, re.IGNORECASE):
            status = True
        else:
            status = False
        mysql_obj = panelMysql.panelMysql()
        result = mysql_obj.query("show variables like 'have_ssl';")
        if not os.path.exists('/www/server/data/ssl.zip'):
            if os.path.exists('/www/server/mysql/mysql-test/std_data/client-cert.pem'):
                public.ExecShell(
                    "cd /www/server/mysql/mysql-test/std_data/ && zip -q /www/server/data/ssl.zip client-cert.pem client-key.pem cacert.pem"
                )
        try:
            if result and result[0][1] == "YES" and status is True:
                return public.success_v2({"status": True})
            return public.success_v2({"status": False})
        except:
            return public.success_v2({"status": False})

    # 判断数据库是否存在—从MySQL
    def database_exists_for_mysql(self, mysql_obj, dataName):
        databases_tmp = self.map_to_list(mysql_obj.query('show databases'))
        if not isinstance(databases_tmp, list):
            return True

        for i in databases_tmp:
            if i[0] == dataName:
                return True
        return False

    # 创建用户
    def __CreateUsers(self, dbname, username, password, address, ssl=None):
        mysql_obj = public.get_mysql_obj_by_sid(self.sid)
        if not mysql_obj:
            return public.returnMsg(False, public.lang("Failed to connect to the specified database"))
        mysql_obj.execute("CREATE USER `%s`@`localhost` IDENTIFIED BY '%s'" % (username, password))
        result = mysql_obj.execute("grant all privileges on `%s`.* to `%s`@`localhost`" % (dbname, username))
        if str(result).find('1044') != -1:
            mysql_obj.execute(
                "grant SELECT,INSERT,UPDATE,DELETE,CREATE,DROP,INDEX,ALTER,CREATE TEMPORARY TABLES,"
                "LOCK TABLES,EXECUTE,CREATE VIEW,SHOW VIEW,EVENT,TRIGGER on `%s`.* to `%s`@`localhost`" % (
                    dbname, username
                )
            )
        if not ssl:
            mysql_obj.execute(
                "update mysql.user set ssl_type='' where user='%s' and host='localhost'" % username
            )

        for a in address.split(','):
            mysql_obj.execute("CREATE USER `%s`@`%s` IDENTIFIED BY '%s'" % (username, a, password))
            result = mysql_obj.execute("grant all privileges on `%s`.* to `%s`@`%s`" % (dbname, username, a))
            if str(result).find('1044') != -1:
                mysql_obj.execute(
                    "grant SELECT,INSERT,UPDATE,DELETE,CREATE,DROP,INDEX,ALTER,CREATE TEMPORARY TABLES,"
                    "LOCK TABLES,EXECUTE,CREATE VIEW,SHOW VIEW,EVENT,TRIGGER on `%s`.* to `%s`@`%s` %s" % (
                        dbname, username, a, ssl
                    )
                )
        mysql_obj.execute("flush privileges")

    # 检查是否在回收站
    def CheckRecycleBin(self, name):
        try:
            u_name = self.db_name_to_unicode(name)
            for n in os.listdir('/www/.Recycle_bin'):
                if n.find('BTDB_' + name + '_t_') != -1: return True
                if n.find('BTDB_' + u_name + '_t_') != -1: return True
            return False
        except:
            return False

    # 检测数据库执行错误
    def IsSqlError(self, mysqlMsg):
        mysqlMsg = str(mysqlMsg)
        if "MySQLdb" in mysqlMsg:
            return 'MySQLdb component is missing! <br>Please enter SSH and run the command: pip install mysql-python'
        if "2002," in mysqlMsg or '2003,' in mysqlMsg:
            return 'ERROR to connect database, pls check database status!'
        if "using password:" in mysqlMsg:
            return 'Mysql root or user password is incorrect, please try to reset!'
        if "Connection refused" in mysqlMsg:
            return 'ERROR to connect database, pls check database status!'
        if "1133" in mysqlMsg:
            return 'Database user does NOT exist!'
        if "3679" in mysqlMsg:
            return'Slave database deletion failed, data directory does not exist!'

        if "libmysqlclient" in mysqlMsg:
            self.rep_lnk()
            public.ExecShell("pip uninstall mysql-python -y")
            public.ExecShell("pip install pymysql")
            public.writeFile('data/restart.pl', 'True')
            return 'Execution failed, attempted auto repair, please try again later!'
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

    # 删除数据库
    def DeleteDatabase(self, get):

        # 校验参数
        try:
            get.validate([
                Param('id').Require().Integer(),
                Param('name').Require().String(),
            ], [
                public.validate.trim_filter(),
            ])
        except Exception as ex:
            public.print_log("error info: {}".format(ex))
            return public.return_message(-1, 0, str(ex))

        # try:
        id = get['id']
        name = get['name']
        find = public.M('databases').where("id=?", (id,)).field(
            'id,sid,pid,name,username,password,accept,ps,addtime,db_type').find()
        if not find:
            return public.return_message(-1, 0, public.lang("Database [{}] does not exist!", name))
        self.sid = find['sid']
        if find['db_type'] in ['0', 0] or self.sid:  # 删除本地数据库
            if os.path.exists('data/recycle_bin_db.pl') and not self.sid:
                res = self.DeleteToRecycleBin(name)

                # return self.DeleteToRecycleBin(name)
                info2 = res.get("msg", "Database moved to recycle bin")
                return public.return_message(0, 0, info2)
            accept = find['accept']
            username = find['username']
            # 删除MYSQL
            mysql_obj = public.get_mysql_obj_by_sid(self.sid)
            if not mysql_obj:
                return public.return_message(-1, 0, public.lang("Database [{}] connection failed", name))
            result = mysql_obj.execute("drop database `" + name + "`")
            isError = self.IsSqlError(result)
            if isError != None:
                # return isError
                return public.return_message(-1, 0, isError)
            users = mysql_obj.query("select Host from mysql.user where User='" + username + "' AND Host!='localhost'")
            mysql_obj.execute("drop user '" + username + "'@'localhost'")
            for us in users:
                mysql_obj.execute("drop user '" + username + "'@'" + us[0] + "'")
            mysql_obj.execute("flush privileges")
        # 删除SQLITE
        public.M('databases').where("id=?", (id,)).delete()
        public.write_log_gettext("Database manager", 'Successfully deleted database [{}]!', (name,))
        return public.return_message(0, 0, public.lang("Successfully deleted"))
        # except Exception as ex:
        #     public.write_log_gettext("Database manager",'Failed to delete database [{}]!, {}',(get.name , str(ex)))
        #     return public.return_msg_gettext(False, public.lang("Failed to delete"))

    def db_name_to_unicode(self, name):
        '''
            @name 中文数据库名转换为Unicode编码
            @author hwliang<2021-12-20>
            @param name<string> 数据库名
            @return name<string> Unicode编码的数据库名
        '''
        name = name.replace('.', '@002e')
        name = name.replace('-', '@002d')
        return name.encode("unicode_escape").replace(b"\\u", b"@").decode()

    # 删除数据库到回收站
    def DeleteToRecycleBin(self, name):
        import json
        data = public.M('databases').where("name=?", (name,)).field(
            'id,pid,name,username,password,accept,ps,addtime').find()
        username = data['username']
        panelMysql.panelMysql().execute("drop user '" + username + "'@'localhost'")
        users = panelMysql.panelMysql().query(
            "select Host from mysql.user where User='" + username + "' AND Host!='localhost'")
        if isinstance(users, str):
            return public.return_msg_gettext(False, public.lang("Delete failed, failed to connect to database!"))
        try:
            for us in users:
                panelMysql.panelMysql().execute("drop user '" + username + "'@'" + us[0] + "'")
        except Exception:
            pass
        panelMysql.panelMysql().execute("flush privileges")
        rPath = '/www/.Recycle_bin/'
        data['rmtime'] = int(time.time())
        u_name = self.db_name_to_unicode(name)
        rm_path = '{}/BTDB_{}_t_{}'.format(rPath, u_name, data['rmtime'])
        if os.path.exists(rm_path): rm_path += '.1'
        rm_config_file = '{}/config.json'.format(rm_path)
        datadir = public.get_datadir()

        db_path = '{}/{}'.format(datadir, u_name)
        if not os.path.exists(db_path):
            return public.return_msg_gettext(False, public.lang("The database data does not exist!"))

        public.ExecShell("mv -f {} {}".format(db_path, rm_path))
        if not os.path.exists(rm_path):
            return public.return_msg_gettext(False, public.lang("Failed to move database data to the recycle bin!"))
        public.writeFile(rm_config_file, json.dumps(data))
        # public.writeFile(rPath + 'BTDB_' + name +'_t_' + str(time.time()),json.dumps(data))
        public.M('databases').where("name=?", (name,)).delete()
        public.write_log_gettext("Database manager", 'Successfully deleted database [{}]!', (name,))
        return public.return_msg_gettext(True, public.lang("Database moved to recycle bin!"))

    # 永久删除数据库
    def DeleteTo(self, filename):
        import json
        if os.path.isfile(filename):
            data = json.loads(public.readFile(filename))
            if public.M('databases').where("name=?", (data['name'],)).count():
                os.remove(filename)
                return public.return_msg_gettext(True, public.lang("Successfully deleted"))
        else:
            if os.path.exists(filename):
                data = json.loads(public.readFile(filename + '/config.json'))
            else:
                return public.returnMsg(False, public.lang("Recycle Bin does not exist for this database!"))

        db_obj = panelMysql.panelMysql()
        if self.database_exists_for_mysql(db_obj, data['name']):
            u_name = self.db_name_to_unicode(data['name'])
            datadir = public.get_datadir()
            db_path = '{}/{}'.format(datadir, u_name)
            if not os.path.exists(db_path):
                os.makedirs(db_path)
                public.ExecShell("chown mysql:mysql {}".format(db_path))
            result = db_obj.execute("drop database `" + data['name'] + "`")
            isError = self.IsSqlError(result)
            if isError != None: return isError
            db_obj.execute("drop user '" + data['username'] + "'@'localhost'")
            users = db_obj.query(
                "select Host from mysql.user where User='" + data['username'] + "' AND Host!='localhost'")
            for us in users:
                db_obj.execute("drop user '" + data['username'] + "'@'" + us[0] + "'")
            db_obj.execute("flush privileges")

        if os.path.isfile(filename):
            os.remove(filename)
        else:
            import shutil
            shutil.rmtree(filename)

        try:
            public.write_log_gettext("Database manager", 'Successfully deleted database [{}]!', (data['name'],))
        except:
            pass
        return public.return_msg_gettext(True, public.lang("Successfully deleted"))

    # 恢复数据库
    def RecycleDB(self, filename):
        import json
        _isdir = False
        if os.path.isfile(filename):
            data = json.loads(public.readFile(filename))
        else:
            re_config_file = filename + '/config.json'
            data = json.loads(public.readFile(re_config_file))
            u_name = self.db_name_to_unicode(data['name'])
            db_path = "{}/{}".format(public.get_datadir(), u_name)
            if os.path.exists(db_path):
                return public.return_msg_gettext(False, public.lang("There is a database with the same name in the current database. To ensure data security, stop recovery!"))
            _isdir = True

        if public.M('databases').where("name=?", (data['name'],)).count():
            if not _isdir: os.remove(filename)
            return public.return_msg_gettext(True, public.lang("Database recovered!"))

        if not _isdir:
            os.remove(filename)
        else:
            public.ExecShell('mv -f {} {}'.format(filename, db_path))
            if not os.path.exists(db_path):
                return public.return_msg_gettext(False, public.lang("Data recovery failed!"))
            db_config_file = "{}/config.json".format(db_path)
            if os.path.exists(db_config_file): os.remove(db_config_file)

            # 设置文件权限
            public.ExecShell("chown -R mysql:mysql {}".format(db_path))
            public.ExecShell("chmod -R 660 {}".format(db_path))
            public.ExecShell("chmod  700 {}".format(db_path))

        self.__CreateUsers(data['name'], data['username'], data['password'], data['accept'])
        public.M('databases').add('id,pid,name,username,password,accept,ps,addtime', (
        data['id'], data['pid'], data['name'], data['username'], data['password'], data['accept'], data['ps'],
        data['addtime']))
        return public.return_msg_gettext(True, public.lang("Database recovered!"))

    # 设置ROOT密码
    def SetupPassword(self, get):
        from BTPanel import session

        # 校验参数
        try:
            get.validate([
                Param('password').Require().String(),
            ], [
                public.validate.trim_filter(),
            ])
        except Exception as ex:
            public.print_log("error info: {}".format(ex))
            return public.return_message(-1, 0, str(ex))

        password = get['password'].strip()
        try:
            # if not password: return public.return_msg_gettext(False, public.lang("Root password cannot be empty"))
            # rep = r"^[\w@\.\?\-\_\>\<\~\!\#\$\%\^\&\*\(\)]+$"
            # if not re.match(rep, password): return public.return_msg_gettext(False, 'Database password cannot contain special characters!')
            self.sid = get.get('sid/d', 0)
            # 修改MYSQL
            mysql_obj = public.get_mysql_obj_by_sid(self.sid)
            if not mysql_obj:
                # return public.returnMsg(False, public.lang("Failed to connect to the specified database"))
                return public.return_message(-1, 0, public.lang("Failed to connect to the specified database"))

            result = mysql_obj.query("show databases")
            isError = self.IsSqlError(result)
            is_modify = True
            if isError != None and not self.sid:
                # 尝试使用新密码
                public.M('config').where("id=?", (1,)).setField('mysql_root', password)
                result = mysql_obj.query("show databases")
                isError = self.IsSqlError(result)
                if isError != None:
                    public.ExecShell(
                        "cd /www/server/panel && " + public.get_python_bin() + " tools.py root \"" + password + "\"")
                    is_modify = False

            if is_modify:
                admin_user = 'root'
                m_version = public.readFile(public.GetConfigValue('setup_path') + '/mysql/version.pl')
                if self.sid:
                    admin_user = mysql_obj._USER
                    m_version = mysql_obj.query('select version();')[0][0]

                if m_version.find('5.7') == 0 or m_version.find('8.0') == 0:
                    accept = self.map_to_list(
                        mysql_obj.query("select Host from mysql.user where User='{}'".format(admin_user)))
                    for my_host in accept:
                        mysql_obj.execute(
                            "UPDATE mysql.user SET authentication_string='' WHERE User='{}' and Host='{}'".format(
                                admin_user, my_host[0]))
                        mysql_obj.execute(
                            "ALTER USER `%s`@`%s` IDENTIFIED BY '%s'" % (admin_user, my_host[0], password))
                # elif m_version.find('10.5.') != -1 or m_version.find('10.4.') != -1:
                elif any(mariadb_ver in m_version for mariadb_ver in
                             ['10.5.', '10.4.', '10.6.', '10.7.', '10.11.', '11.3.']):

                    accept = self.map_to_list(
                        mysql_obj.query("select Host from mysql.user where User='{}'".format(admin_user)))
                    for my_host in accept:
                        mysql_obj.execute(
                            "ALTER USER `%s`@`%s` IDENTIFIED BY '%s'" % (admin_user, my_host[0], password))
                else:
                    result = mysql_obj.execute(
                        "update mysql.user set Password=password('" + password + "') where User='{}'".format(
                            admin_user))
                mysql_obj.execute("flush privileges")

            msg = public.get_msg_gettext('Successfully modified root password!')
            # 修改SQLITE
            if self.sid:
                public.M('database_servers').where('id=?', self.sid).setField('db_password', password)
                public.write_log_gettext("Database manager", "Change the password of the remote MySQL server")
            else:
                public.M('config').where("id=?", (1,)).setField('mysql_root', password)
                public.write_log_gettext("Database manager", 'Successfully modified root password!')
                session['config']['mysql_root'] = password
            # return public.return_msg_gettext(True, msg)
            return public.return_message(0, 0, msg)
        except Exception as ex:
            # return public.return_msg_gettext(False, 'Failed to modify ' + str(ex))
            return public.return_message(-1, 0, public.lang("Failed to modify : {}", ex))

    # 修改用户密码
    def ResDatabasePassword(self, get):
        from BTPanel import session

        # 校验参数
        try:
            get.validate([
                Param('name').Require().String(),
                Param('id').Require().Integer(),
                Param('password').Require().String(),
            ], [
                public.validate.trim_filter(),
            ])
        except Exception as ex:
            public.print_log("error info: {}".format(ex))
            return public.return_message(-1, 0, str(ex))

        # try:
        newpassword = get['password']
        username = get['name']
        # data_name=get['data_name']
        id = get['id']
        if not newpassword:
            # return public.return_msg_gettext(False, 'Database [{}] password cannot be empty',(username,))
            return public.return_message(-1, 0, public.lang("Database [{}] password cannot be empty", username))
        re_list = re.findall("[，。？！；：“”‘’（）【】《》￥&\u4e00-\u9fa5]+", newpassword)
        if re_list: return public.return_message(-1, 0, public.lang('The database password cannot contain Chinese characters {}', " ".join(re_list)))

        db_find = public.M('databases').where("id=? AND LOWER(type)=LOWER('mysql')", (id,)).find()
        if not db_find:
            return public.return_message(-1, 0, public.lang("db not found!"))
        name = db_find['name']

        rep = r"^[\w@\.\?\-\_\>\<\~\!\#\$\%\^\&\*\(\)]+$"
        if not re.match(rep, newpassword):
            # return public.return_msg_gettext(False, public.lang("Database password cannot contain special characters!"))
            return public.return_message(-1, 0, public.lang("Database password cannot contain special characters!"))
        # 修改MYSQL
        self.sid = db_find['sid']
        if self.sid and username == 'root':
            # return public.returnMsg(False, public.lang("Cannot change the root password of the remote database"))
            return public.return_message(-1, 0, public.lang("Cannot change the root password of the remote database"))
        mysql_obj = public.get_mysql_obj_by_sid(self.sid)
        if not mysql_obj:
            # return public.returnMsg(False, public.lang("Failed to connect to the specified database"))
            return public.return_message(-1, 0, public.lang("Failed to connect to the specified database"))
        m_version = public.readFile(public.GetConfigValue('setup_path') + '/mysql/version.pl')
        if self.sid:
            m_version = mysql_obj.query('select version();')[0][0]

        if not isinstance(m_version, str):
            public.ExecShell('mysql -V > /www/server/mysql/version_v.pl')
            m_version = public.readFile('/www/server/mysql/version_v.pl')

        user_result = mysql_obj.query("select * from mysql.user where User='" + username + "'")
        if not user_result:
            return public.return_message(-1,0, "User Db Not Found, please Sync ALL And Reset The Password")

        if any(mysql_version in m_version for mysql_version in ['5.7', '8.0', '8.4', '9.0']):
            accept = self.map_to_list(mysql_obj.query("select Host from mysql.user where User='" + username + "' AND Host!='localhost'"))
            mysql_obj.execute("update mysql.user set authentication_string='' where User='" + username + "'")
            result = mysql_obj.execute("ALTER USER `%s`@`localhost` IDENTIFIED BY '%s'" % (username, newpassword))
            for my_host in accept:
                mysql_obj.execute("ALTER USER `%s`@`%s` IDENTIFIED BY '%s'" % (username, my_host[0], newpassword))
        elif any(mariadb_ver in m_version for mariadb_ver in ['10.5.', '10.4.', '10.6.', '10.7.', '10.11.', '11.3.']):
            accept = self.map_to_list(mysql_obj.query("select Host from mysql.user where User='" + username + "' AND Host!='localhost'"))
            result = mysql_obj.execute("ALTER USER `%s`@`localhost` IDENTIFIED BY '%s'" % (username, newpassword))
            for my_host in accept:
                mysql_obj.execute("ALTER USER `%s`@`%s` IDENTIFIED BY '%s'" % (username, my_host[0], newpassword))
        else:
            result = mysql_obj.execute("update mysql.user set Password=password('" + newpassword + "') where User='" + username + "'")

        isError = self.IsSqlError(result)
        if isError != None:
            # return isError
            return public.return_message(-1, 0, isError)

        mysql_obj.execute("flush privileges")
        # if result==False: return public.return_msg_gettext(False, public.lang("Failed to modify, database user does not exist!"))
        # 修改SQLITE
        if int(id) > 0:
            public.M('databases').where("id=? AND LOWER(type)=LOWER('mysql')", (id,)).setField('password', newpassword)
        else:
            public.M('config').where("id=?", (id,)).setField('mysql_root', newpassword)
            session['config']['mysql_root'] = newpassword

        public.write_log_gettext("Database manager", 'Successfully modifyied password for database [{}]!', (name,))
        # return public.return_msg_gettext(True, 'Successfully modifyied password for database [{}]!', (name,))
        return public.return_message(0, 0, public.lang("Successfully modifyied password for database [{}]!", name))
        # except Exception as ex:
        #     import traceback
        #     public.write_log_gettext("Database manager", 'Failed to modify password for database [{}]!',(username,traceback.format_exc(limit=True).replace('\n','<br>')))
        #     return public.return_msg_gettext(False,'Failed to modify password for database [{}]!',(name,))

    # 备份
    def ToBackup(self, get):
        from BTPanel import session

        # 校验参数
        try:
            get.validate([
                Param('id').Require().Integer(),
            ], [
                public.validate.trim_filter(),
            ])
        except Exception as ex:
            public.print_log("error info: {}".format(ex))
            return public.return_message(-1, 0, str(ex))

        # try:
        import shlex
        id = get['id']
        db_find = public.M('databases').where("id=?", (id,)).find()
        name = db_find['name']
        fileName = name + '_' + time.strftime('%Y%m%d_%H%M%S', time.localtime()) + '.sql.gz'
        backupName = session['config']['backup_path'] + '/database/' + fileName
        mysqldump_bin = public.get_mysqldump_bin()
        if db_find['db_type'] in ['0', 0]:
            # 本地数据库
            result = panelMysql.panelMysql().execute("show databases")
            isError = self.IsSqlError(result)
            if isError:
                # return isError
                return public.return_message(-1, 0, isError)

            root = public.M('config').where('id=?', (1,)).getField('mysql_root')
            if not os.path.exists(session['config']['backup_path'] + '/database'): public.ExecShell(
                'mkdir -p ' + session['config']['backup_path'] + '/database')
            if not self.mypass(True, root):
                # return public.return_msg_gettext(False,'Database configuration file failed to get checked, please
                # check if MySQL configuration file exists [/etc/my.cnf]')
                return public.return_message(-1, 0, "Database configuration file failed to get checked, please check "
                                                    "if MySQL configuration file exists [/etc/my.cnf]")
            try:
                password = public.M('config').where('id=?', (1,)).getField('mysql_root')
                if not password:
                    # return public.returnMsg(False, public.lang("Database password cannot be empty"))
                    return public.return_message(-1, 0, public.lang("Database password cannot be empty"))
                password = shlex.quote(str(password))
                os.environ["MYSQL_PWD"] = password
                public.ExecShell(
                    mysqldump_bin + " -R -E --triggers=false --default-character-set=" + public.get_database_character(
                        name) + " --force --opt \"" + name + "\"  -u root -p" + password + " | gzip > " + backupName)
            except Exception as e:
                raise
            finally:
                os.environ["MYSQL_PWD"] = ""
            self.mypass(False, root)
        elif db_find['db_type'] in ['1', 1]:
            # 远程数据库
            try:
                conn_config = json.loads(db_find['conn_config'])
                res = self.CheckCloudDatabase(conn_config)
                if isinstance(res, dict):
                    # return res
                    return public.return_message(0, 0, res)
                password = shlex.quote(str(conn_config['db_password']))
                os.environ["MYSQL_PWD"] = password
                public.ExecShell(mysqldump_bin + " -h " + conn_config['db_host'] + " -P " + str(int(conn_config[
                                                                                                        'db_port'])) + " -R -E --triggers=false --default-character-set=" + public.get_database_character(
                    name) + " --force --opt \"" + str(db_find['name']) + "\"  -u " + str(
                    conn_config['db_user']) + " -p" + password + " | gzip > " + backupName)
            except Exception as e:
                raise
            finally:
                os.environ["MYSQL_PWD"] = ""
        elif db_find['db_type'] in ['2', 2]:
            try:
                conn_config = public.M('database_servers').where('id=?', db_find['sid']).find()
                res = self.CheckCloudDatabase(conn_config)
                if isinstance(res, dict):
                    # return res
                    return public.return_message(0, 0, res)
                password = shlex.quote(str(conn_config['db_password']))
                os.environ["MYSQL_PWD"] = password
                public.ExecShell(mysqldump_bin + " -h " + conn_config['db_host'] + " -P " + str(int(conn_config[
                                                                                                        'db_port'])) + " -R -E --triggers=false --default-character-set=" + public.get_database_character(
                    name) + " --force --opt \"" + str(db_find['name']) + "\"  -u " + str(
                    conn_config['db_user']) + " -p" + str(conn_config['db_password']) + " | gzip > " + backupName)
            except Exception as e:
                raise
            finally:
                os.environ["MYSQL_PWD"] = ""
        else:
            # return public.return_msg_gettext(False, public.lang("Unsupported database type"))
            return public.return_message(-1, 0, public.lang("Unsupported database type"))

        if not os.path.exists(backupName):
            # return public.return_msg_gettext(False, public.lang("Backup error!"))
            return public.return_message(-1, 0, public.lang("Backup error"))
        sql = public.M('backup')
        addTime = time.strftime('%Y-%m-%d %X', time.localtime())
        sql.add('type,name,pid,filename,size,addtime', (1, fileName, id, backupName, 0, addTime))
        public.write_log_gettext("Database manager", "Backup database [{}] succeed!", (name,))
        # return public.return_msg_gettext(True, public.lang("Backup Succeeded!"))
        return public.return_message(0, 0, public.lang("Backup Succeeded"))
        # except Exception as ex:
        # public.write_log_gettext("数据库管理", "备份数据库[" + name + "]失败 => "  +  str(ex))
        # return public.return_msg_gettext(False, public.lang("备份失败!"))

    # 删除备份文件
    def DelBackup(self, get):

        # 校验参数
        try:
            get.validate([
                Param('id').Require().Integer().Xss(),
            ], [
                public.validate.trim_filter(),
            ])
        except Exception as ex:
            public.print_log("error info: {}".format(ex))
            return public.return_message(-1, 0, str(ex))

        try:
            id = get.id
            where = "id=?"
            backup_info = public.M('backup').where(where, (id,)).find()
            filename = backup_info['filename']
            if os.path.exists(filename): os.remove(filename)
            db_name = ''
            if filename == 'qiniu':
                name = backup_info['name']
                public.ExecShell(public.get_python_bin() + " " + public.GetConfigValue(
                    'setup_path') + '/panel/script/backup_qiniu.py delete_file ' + name)
            public.M('backup').where(where, (id,)).delete()
            # 取实际
            pid = backup_info['pid']
            db_name = public.M('databases').where('id=?', (pid,)).getField('name')
            public.write_log_gettext("Database manager", 'Successfully deleted backup [{}] for database [{}]!',
                                     (db_name, filename))
            # return public.return_msg_gettext(True, public.lang("Successfully deleted"))
            return public.return_message(0, 0, public.lang("Successfully deleted"))
        except Exception as ex:
            public.write_log_gettext("Database manager", 'Failed to delete backup [{}] for database [{}]! => {}',
                                     (db_name, filename, str(ex)))
            # return public.return_msg_gettext(False, public.lang("Failed to delete"))
            return public.return_message(-1, 0, public.lang("Failed to delete"))

    # 导入
    def InputSql(self, get):
        from BTPanel import session

        # 校验参数
        try:
            get.validate([
                Param('file').SafePath(force=False),   # 文件路径
                Param('name').String(),
            ], [
                public.validate.trim_filter(),
            ])
        except Exception as ex:
            public.print_log("error info: {}".format(ex))
            return public.return_message(-1, 0, str(ex))
        # try:
        import shlex
        name = get['name']
        file = get['file']
        if "|" in file:
            file = file.split('|')[-1]
        root = public.M('config').where('id=?', (1,)).getField('mysql_root')
        tmp = file.split('.')
        exts = ['sql', 'gz', 'zip']
        ext = tmp[len(tmp) - 1]

        if ext not in exts:
            # return public.return_msg_gettext(False, public.lang("Select sql/gz/zip file!"))
            return public.return_message(-1, 0, public.lang("Select sql/gz/zip file"))
        db_find = public.M('databases').where('name=?', name).find()
        mysql_obj = public.get_mysql_obj_by_sid(db_find['sid'])

        if not mysql_obj:
            # return public.returnMsg(False, public.lang("Failed to connect to the specified database"))
            return public.return_message(-1, 0, public.lang("Failed to connect to the specified database"))
        result = mysql_obj.execute("show databases")
        isError = self.IsSqlError(result)
        if isError:
            # return isError
            return public.return_message(0, 0, isError)
        isgzip = False

        mysql_bin = public.get_mysql_bin()
        if ext != 'sql':
            import panel_restore
            tmp = file.split('/')
            tmpFile = tmp[len(tmp) - 1]
            tmpFile = tmpFile.replace('.sql.' + ext, '.sql')
            tmpFile = tmpFile.replace('.' + ext, '.sql')
            tmpFile = tmpFile.replace('tar.', '')
            # return tmpFile
            backupPath = session['config']['backup_path'] + '/database'
            if "|" in file:
                panel_restore.panel_restore().restore_db_backup(get)
                download_msg = panel_restore.panel_restore().restore_db_backup(get)
                if not download_msg['status']:
                    # return download_msg
                    return public.return_message(0, 0, download_msg)
            input_path = os.path.join(backupPath, tmpFile)
            # 备份文件的路径
            input_path2 = os.path.join(os.path.dirname(file), tmpFile)
            if ext == 'zip':
                public.ExecShell("cd " + backupPath + " && unzip " + '"' + file + '"')
            else:
                public.ExecShell("cd " + backupPath + " && tar zxf " + '"' + file + '"')
                if not os.path.exists(input_path):
                    # 兼容从备份文件所在目录恢复
                    if not os.path.exists(input_path2):
                        public.ExecShell("cd " + backupPath + " && gunzip -q " + '"' + file + '"')
                        isgzip = True
                    else:
                        input_path = input_path2
            if not os.path.exists(input_path) or tmpFile == '':
                if tmpFile and os.path.isfile(input_path2):
                    input_path = input_path2
                else:
                    # return public.return_msg_gettext(False, 'Configuration file not exist', (tmpFile,))
                    return public.return_message(-1, 0, public.lang("Configuration file not exist {}", tmpFile))

            try:
                if db_find['db_type'] in ['0', 0]:
                    password = public.M('config').where('id=?', (1,)).getField('mysql_root')
                    password = shlex.quote(str(password))
                    os.environ["MYSQL_PWD"] = str(password)
                    public.ExecShell(mysql_bin + " -uroot -p" + str(
                        password) + " --force \"" + name + "\" < " + '"' + input_path + '"')
                elif db_find['db_type'] in ['1', 1]:
                    conn_config = json.loads(db_find['conn_config'])
                    password = shlex.quote(str(conn_config['db_password']))
                    os.environ["MYSQL_PWD"] = str(password)
                    public.ExecShell(mysql_bin + " -h " + conn_config['db_host'] + " -P " + str(
                        int(conn_config['db_port'])) + " -u" + str(conn_config['db_user']) + " -p" + str(
                        password) + " --force \"" + name + "\" < " + '"' + input_path + '"')
                elif db_find['db_type'] in ['2', 2]:
                    conn_config = public.M('database_servers').where('id=?', db_find['sid']).find()
                    password = shlex.quote(str(conn_config['db_password']))
                    os.environ["MYSQL_PWD"] = str(password)
                    public.ExecShell(mysql_bin + " -h " + conn_config['db_host'] + " -P " + str(
                        int(conn_config['db_port'])) + " -u" + str(conn_config['db_user']) + " -p" + str(
                        password) + " --force \"" + name + "\" < " + '"' + input_path + '"')
            except Exception as e:
                raise
            finally:
                os.environ["MYSQL_PWD"] = ""

            if isgzip:
                public.ExecShell('cd ' + os.path.dirname(input_path) + ' && gzip ' + file.split('/')[-1][:-3])
            else:
                public.ExecShell("rm -f " + input_path)
        else:
            try:
                if db_find['db_type'] in ['0', 0]:
                    password = public.M('config').where('id=?', (1,)).getField('mysql_root')
                    password = shlex.quote(str(password))
                    os.environ["MYSQL_PWD"] = password
                    public.ExecShell(
                        mysql_bin + " -uroot -p" + password + " --force \"" + name + "\" < " + '"' + file + '"')
                elif db_find['db_type'] in ['1', 1]:
                    conn_config = json.loads(db_find['conn_config'])
                    password = shlex.quote(str(conn_config['db_password']))
                    os.environ["MYSQL_PWD"] = password
                    public.ExecShell(mysql_bin + " -h " + conn_config['db_host'] + " -P " + str(
                        int(conn_config['db_port'])) + " -u" + str(conn_config['db_user']) + " -p" + str(
                        password) + " --force \"" + name + "\" < " + '"' + file + '"')
                elif db_find['db_type'] in ['2', 2]:
                    conn_config = public.M('database_servers').where('id=?', db_find['sid']).find()
                    password = shlex.quote(str(conn_config['db_password']))
                    os.environ["MYSQL_PWD"] = password
                    public.ExecShell(mysql_bin + " -h " + conn_config['db_host'] + " -P " + str(
                        int(conn_config['db_port'])) + " -u" + str(conn_config['db_user']) + " -p" + str(
                        password) + " --force \"" + name + "\" < " + '"' + file + '"')
            except Exception as e:
                raise
            finally:
                os.environ["MYSQL_PWD"] = ""

        public.write_log_gettext("Database manager", 'Successfully imported database [{}]', (name,))
        # return public.return_msg_gettext(True, public.lang("Successfully imported database!"))
        return public.return_message(0, 0, public.lang("Successfully imported database!"))


    # 同步数据库到服务器
    def SyncToDatabases(self, get):

        # 校验参数
        try:
            get.validate([
                Param('ids').Require(),   # [67,66]
                Param('type').Require().Integer(),   # query传参 不确定..
            ], [
                public.validate.trim_filter(),
            ])
        except Exception as ex:
            public.print_log("error info: {}".format(ex))
            return public.return_message(-1, 0, str(ex))

        # result = panelMysql.panelMysql().execute("show databases")
        # isError=self.IsSqlError(result)
        # if isError: return isError
        type = int(get['type'])
        n = 0
        sql = public.M('databases')
        if type == 0:
            data = sql.field('id,sid,name,username,password,accept,db_type').where("type='MySQL'", ()).select()
            for value in data:
                if value['db_type'] in ['1', 1]:
                    continue  # 跳过远程数据库
                result = self.ToDataBase(value)
                if result == 1: n += 1
        else:
            import json
            data = json.loads(get.ids)
            for value in data:
                find = sql.where("id=?", (value,)).field('id,sid,name,username,password,accept').find()
                result = self.ToDataBase(find)
                if result == 1: n += 1
        # 当只同步1个数据库时，不返回成功数量
        if n == 1:
            # return public.returnMsg(True, public.lang("Synchronization succeeded"))
            return public.return_message(0, 0, public.lang("Synchronization succeeded"))
        elif n == 0:
            # 失败
            # return public.returnMsg(False, public.lang("Sync failed"))
            return public.return_message(-1, 0, public.lang("Sync failed"))
        else:
            # return public.return_msg_gettext(True, 'Sync {} database(s) from server!', (str(n),))
            return public.return_message(0, 0, public.lang("Sync {} database(s) from server!", str(n)))

    # 配置
    def mypass(self, act, password=None):
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

    # 添加到服务器
    def ToDataBase(self, find):
        # if find['username'] == 'bt_default': return 0
        if len(find['password']) < 3:
            find['username'] = find['name']
            find['password'] = public.md5(str(time.time()) + find['name'])[0:10]
            public.M('databases').where("id=?", (find['id'],)).save('password,username',
                                                                    (find['password'], find['username']))
        self.sid = find['sid']
        mysql_obj = public.get_mysql_obj_by_sid(find['sid'])
        if not mysql_obj: return public.returnMsg(False, public.lang("Failed to connect to the specified database"))
        result = mysql_obj.execute("create database `" + find['name'] + "`")
        if "using password:" in str(result): return -1
        if "Connection refused" in str(result): return -1

        password = find['password']
        # if find['password']!="" and len(find['password']) > 20:
        # password = find['password']

        self.__CreateUsers(find['name'], find['username'], password, find['accept'])
        return 1

    # 从服务器获取数据库
    def SyncGetDatabases(self, get):

        # 校验参数
        try:
            get.validate([
                Param('sid').Require().Integer(),

            ], [
                public.validate.trim_filter(),
            ])
        except Exception as ex:
            public.print_log("error info: {}".format(ex))
            return public.return_message(-1, 0, str(ex))

        self.sid = get.get('sid/d', 0)
        db_type = 0
        if self.sid: db_type = 2
        mysql_obj = public.get_mysql_obj_by_sid(self.sid)
        if not mysql_obj:
            # return public.returnMsg(False, public.lang("Failed to connect to the specified database"))
            return public.return_message(-1, 0, public.lang("Failed to connect to the specified database"))
        data = mysql_obj.query("show databases")
        isError = self.IsSqlError(data)
        if isError != None:
            # return isError
            return public.return_message(-1, 0,  isError)
        users = mysql_obj.query(
            "select User,Host from mysql.user where User!='root' AND Host!='localhost' AND Host!=''")

        if type(users) == str:
            # return public.returnMsg(False, users)
            return public.return_message(-1, 0,  users)
        if type(users) != list:
            # return public.returnMsg(False, public.GetMySQLError(users))
            return public.return_message(-1, 0, public.GetMySQLError(users))

        sql = public.M('databases')
        nameArr = ['information_schema', 'performance_schema', 'mysql', 'sys']
        n = 0
        for value in data:
            b = False
            for key in nameArr:
                if value[0] == key:
                    b = True
                    break
            if b: continue
            if sql.where("name=?", (value[0],)).count(): continue
            host = '127.0.0.1'
            for user in users:
                if value[0] == user[0]:
                    host = user[1]
                    break

            ps = public.lang('Edit notes')
            if value[0] == 'test':
                ps = public.lang('Test Database')

            # XSS filter
            if not re.match(r"^[\w+\.-]+$", value[0]): continue

            addTime = time.strftime('%Y-%m-%d %X', time.localtime())

            if sql.table('databases').add('name,sid,db_type,username,password,accept,ps,addtime',
                                          (value[0], self.sid, db_type, value[0], '', host, ps, addTime)): n += 1

        # return public.return_msg_gettext(True, 'Obtain {} database(s) from server!', (str(n),))
        return public.return_message(0, 0, public.lang("Obtain {} database(s) from server!", n))

    # 获取数据库权限
    def GetDatabaseAccess(self, get):
        # 校验参数
        try:
            get.validate([
                Param('name').Require().String(),
            ], [
                public.validate.trim_filter(),
            ])
        except Exception as ex:
            public.print_log("error info: {}".format(ex))
            return public.return_message(-1, 0, str(ex))

        db_name = get['name']
        mysql_obj = public.get_mysql_obj(db_name)
        user_name = public.M('databases').where('name=?', db_name).getField('username')
        results = mysql_obj.query(
            "SELECT Host, ssl_type FROM mysql.user WHERE User='%s' AND Host!='localhost'" % user_name
        )
        self.__check_mysql_query_error(results)
        try:
            permission = [x[0] for x in results if x[0]]
            ssl_type = [x[1] for x in results if x[1]]
            permission = '127.0.0.1' if len(permission) < 1 else ','.join(permission)
        except Exception as e:
            public.print_log("error info: {}".format(e))
            permission = '127.0.0.1'
            ssl_type = []

        return public.return_message(0, 0, {'permission': permission, 'ssl': ssl_type})

    # 设置数据库权限
    def SetDatabaseAccess(self, get):
        # 校验参数
        try:
            get.validate([
                Param('name').Require().String(),
                # Param('dataAccess').String().Xss(),
                # Param('address').String().Xss(),
                Param('access').Require().String(),
                Param('ssl').String(),
            ], [
                public.validate.trim_filter(),
            ])
        except Exception as ex:
            public.print_log("error info: {}".format(ex))
            return public.return_message(-1, 0, str(ex))

        user_name = get['name']
        access = get['access'].strip()
        ssl = get.ssl if hasattr(get, 'ssl') else ''

        if ssl == "REQUIRE SSL" and not self.check_mysql_ssl_status(get)["message"].get("status"):
            return public.return_message(-1, 0, public.lang(
                "SSL is not enabled in the database, please open it in the Mysql manager first"
            ))

        db_find = public.M('databases').where('username=?', (user_name,)).find()
        db_name = db_find['name']
        password = db_find['password']
        mysql_obj = public.get_mysql_obj(db_name)
        hosts = mysql_obj.query(
            "SELECT Host FROM mysql.user WHERE User='%s' AND Host!='localhost'" % user_name
        )
        self.__check_mysql_query_error(hosts)
        for host in hosts:
            mysql_obj.execute("DROP user '%s'@'%s'" % (user_name, host[0]))

        self.sid = db_find['sid']
        self.__CreateUsers(db_name, user_name, password, access, ssl)
        return public.return_message(0, 0, public.lang("Setup successfully!"))

    # 获取数据库配置信息
    def GetMySQLInfo(self, get):
        data = {}
        try:
            public.CheckMyCnf()
            myfile = '/etc/my.cnf'
            mycnf = public.readFile(myfile)
            rep = "datadir\\s*=\\s*(.+)\n"
            data['datadir'] = re.search(rep, mycnf).groups()[0]
            rep = "port\\s*=\\s*([0-9]+)\\s*\n"
            data['port'] = re.search(rep, mycnf).groups()[0]
        except:
            data['datadir'] = '/www/server/data'
            data['port'] = '3306'
        # return data
        return public.return_message(0, 0, data)

    # 修改数据库目录
    def SetDataDir(self, get):
        if get.datadir[-1] == '/':
            get.datadir = get.datadir[0:-1]
        if len(get.datadir) > 32:
            return public.fail_v2("The data directory length cannot exceed 32 bits")
        # if not re.search(r"^[0-9A-Za-z_/\\]$+",get.datadir): return public.return_msg_gettext(False, public.lang("Special symbols cannot be included in the database path"))
        if not os.path.exists(get.datadir): public.ExecShell('mkdir -p ' + get.datadir)
        mysqlInfo = self.GetMySQLInfo(get)["message"]
        if mysqlInfo['datadir'] == get.datadir:
            return public.fail_v2("The same as the current storage directory, file cannot be moved!")

        public.ExecShell('/etc/init.d/mysqld stop')
        public.ExecShell(r'\cp -arf ' + mysqlInfo['datadir'] + '/* ' + get.datadir + '/')
        public.ExecShell('chown -R mysql.mysql ' + get.datadir)
        public.ExecShell('chmod -R 755 ' + get.datadir)
        public.ExecShell('rm -f ' + get.datadir + '/*.pid')
        public.ExecShell('rm -f ' + get.datadir + '/*.err')

        public.CheckMyCnf()
        myfile = '/etc/my.cnf'
        mycnf = public.readFile(myfile)
        public.writeFile('/etc/my_backup.cnf', mycnf)
        mycnf = mycnf.replace(mysqlInfo['datadir'], get.datadir)
        public.writeFile(myfile, mycnf)
        public.ExecShell('/etc/init.d/mysqld start')
        result = public.ExecShell('ps aux|grep mysqld|grep -v grep')
        if len(result[0]) > 10:
            public.writeFile('data/datadir.pl', get.datadir)
            return public.success_v2("File moved!")
        else:
            public.ExecShell('pkill -9 mysqld')
            public.writeFile(myfile, public.readFile('/etc/my_backup.cnf'))
            public.ExecShell('/etc/init.d/mysqld start')
            return public.fail_v2("Failed to move file!")

    # 获取迁移进度
    def GetmvDataDirSpeed(self, get):
        if not os.path.exists("/www/server/panel/config/db_dir_cp_info.json"):
            return public.fail_v2('Failed to obtain migration information!')

        if os.path.exists("/www/server/panel/config/db_dir_cp_status.pl"):
            return public.success_v2('Database move success')

        try:
            DB_DIR_CP_INFO = json.loads(public.ReadFile("/www/server/panel/config/db_dir_cp_info.json"))
        except:
            return public.success_v2('running...')

        data = {}
        data_dir = DB_DIR_CP_INFO["new_dir"]
        data_size = DB_DIR_CP_INFO["data_size"]

        try:
            data_size_1 = public.ExecShell("du -s {}/".format(data_dir))[0].split("\t")
            time.sleep(1)
            data_size_2 = public.ExecShell("du -s {}/".format(data_dir))[0].split("\t")
            speed = int(int(data_size_2[0]) - int(data_size_1[0]))

            if speed <= 0:
                speed = "0kb"
            else:
                speed = public.to_size(speed * 1024)

            total = int(data_size_2[0])
            percentage = (total / int(data_size)) * 100
            percentage = round(percentage, 2)
            total = public.to_size(total * 1024)
            data['data_size'] = public.to_size(int(data_size) * 1024)
            data['total'] = total
            data['speed'] = "{}/s".format(speed)
            data['status'] = True
            data['percentage'] = percentage
            return public.success_v2(data)
        except:
            return public.success_v2(data)

    # 修改数据库端口
    def SetMySQLPort(self, get):
        myfile = '/etc/my.cnf'
        mycnf = public.readFile(myfile)
        rep = "port\\s*=\\s*([0-9]+)\\s*\n"
        mycnf = re.sub(rep, 'port = ' + get.port + '\n', mycnf)
        public.writeFile(myfile, mycnf)
        public.ExecShell('/etc/init.d/mysqld restart')
        return public.success_v2("Setup successfully!")

    # 获取错误日志
    def GetErrorLog(self, get):
        path = self.GetMySQLInfo(get)['message'].get('datadir')
        filename = ''
        for n in os.listdir(path):
            if len(n) < 5: continue
            if n[-3:] == 'err':
                filename = path + '/' + n
                break
        if not os.path.exists(filename): return public.return_message(-1, 0, public.lang("Configuration file not exist"))
        if hasattr(get, 'close'):
            public.writeFile(filename, '')
            return public.return_message(-1, 0, public.lang("log is empty"))
        return public.return_message(0, 0,  public.GetNumLines(filename, 1000))

    # 二进制日志开关
    def BinLog(self, get):
        status = getattr(get, "status", None)
        mysql_cnf = public.readFile(self._MYSQL_CNF)

        if not mysql_cnf:
            return public.fail_v2(
                'The configuration file does not exist.'
                ' Please check whether MySQL is installed properly or post a message for help.'
            )

        log_bin_status = re.search("\nlog-bin", mysql_cnf)
        is_off_bin_log = re.search("\nskip-log-bin", mysql_cnf)
        bin_log_status = False
        if log_bin_status and not is_off_bin_log:
            bin_log_status = True

        mysql_data_dir = self.GetMySQLInfo(get)['message'].get('datadir')
        if status is not None:
            bin_log_total_size = 0
            mysql_bin_index = os.path.join(mysql_data_dir, "mysql-bin.index")
            mysql_bin_index_content = public.readFile(mysql_bin_index)
            if mysql_bin_index_content is not False:
                for name in str(mysql_bin_index_content).strip().split("\n"):
                    bin_log_path = os.path.join(mysql_data_dir, os.path.basename(name))
                    if os.path.isfile(bin_log_path):
                        bin_log_total_size += os.path.getsize(bin_log_path)
            return public.success_v2({"binlog_status": bin_log_status, "size": bin_log_total_size})

        if bin_log_status is True:  # 关闭 binlog 日志
            master_slave_conf_1 = "/www/server/panel/plugin/masterslave/data.json"
            master_slave_conf_2 = "/www/server/panel/plugin/mysql_replicate/config.json"
            if os.path.exists(master_slave_conf_1):
                return public.fail_v2(
                    "Please uninstall the Mysql master-slave replication plugin before closing the binary log! !"
                )
            if os.path.exists(master_slave_conf_2):
                return public.fail_v2(
                    "Please uninstall the Mysql master-slave replication plugin before closing the binary log! !"
                )
            if log_bin_status:
                mysql_cnf = re.sub(r"\nlog-bin", "\n#log-bin", mysql_cnf)
            mysql_cnf = re.sub(r"\nbinlog_format", "\n#binlog_format", mysql_cnf)
            if not is_off_bin_log:
                if re.search(r"\n#\s*skip-log-bin", mysql_cnf):
                    mysql_cnf = re.sub(r"\n#\s*skip-log-bin", "\nskip-log-bin", mysql_cnf)
                else:
                    mysql_cnf = re.sub(r"\n#\s*log-bin", "\nskip-log-bin\n#log-bin", mysql_cnf)
            # public.ExecShell("rm -f {}/mysql-bin.*".format(mysql_data_dir))
        else:  # 开启 binlog 日志
            if re.search(r"\n#\s*log-bin", mysql_cnf):
                mysql_cnf = re.sub("\n#\s*log-bin", "\nlog-bin", mysql_cnf)
            else:
                if not re.search(r"\n\s*log-bin", mysql_cnf):
                    mysql_cnf = re.sub(r"\[mysqld]", "[mysqld]\nlog-bin=mysql-bin", mysql_cnf)

            if re.search(r"\n#\s*binlog_format", mysql_cnf):
                mysql_cnf = re.sub(r"\n#\s*binlog_format", "\nbinlog_format", mysql_cnf)
            else:
                if not re.search(r"\n\s*binlog_format", mysql_cnf):
                    mysql_cnf = re.sub(r"\[mysqld]", "[mysqld]\nbinlog_format=mixed", mysql_cnf)

            if is_off_bin_log:
                mysql_cnf = re.sub(r"\nskip-log-bin", "\n#skip-log-bin", mysql_cnf)
        public.writeFile(self._MYSQL_CNF, mysql_cnf)
        public.ExecShell('sync')
        public.ExecShell('/etc/init.d/mysqld restart')
        return public.success_v2({"binlog_status": not bin_log_status})

    # 获取MySQL配置状态
    def GetDbStatus(self, get):
        result = {}
        data = self.map_to_list(panelMysql.panelMysql().query('show variables'))
        gets = ['bt_mysql_set', 'bt_mem_size', 'bt_query_cache_size', 'table_open_cache', 'thread_cache_size',
                'query_cache_type', 'key_buffer_size', 'query_cache_size', 'tmp_table_size', 'max_heap_table_size',
                'innodb_buffer_pool_size', 'innodb_additional_mem_pool_size', 'innodb_log_buffer_size',
                'max_connections', 'sort_buffer_size', 'read_buffer_size', 'read_rnd_buffer_size', 'join_buffer_size',
                'thread_stack', 'binlog_cache_size']
        size_keys = ['join_buffer_size', 'thread_stack', 'binlog_cache_size', 'sort_buffer_size', 'read_buffer_size']
        processed_keys = {key: False for key in size_keys}
        result['mem'] = {}
        mycnf = public.readFile('/etc/my.cnf')
        if not mycnf:
            return public.fail_v2('The configuration file does not exist. '
                                  'Please check whether MySQL is installed properly or post a message for help.')
        for g in gets:
            reg = g + r"\s+=\s+\d+(\.\d+)?"
            if re.search(reg, mycnf):
                value = re.search(reg, mycnf).group()
                if re.search(r"\d+(\.\d+)+", value):
                    value = re.search(r"\d+(\.\d+)?", value).group()
                    value = value
                elif re.search(r"\d+", value):
                    value = re.search(r"\d+", value).group()
                    value = int(value)
                result['mem'][g] = value
            else:
                for d in data:
                    if d[0] == g: result['mem'][g] = d[1]
                if 'query_cache_type' in result['mem']:
                    if result['mem']['query_cache_type'] != 'ON':
                        result['mem']['query_cache_size'] = 0
                    else:
                        result['mem']['query_cache_size'] = int(result.get('mem').get('query_cache_size', 0))
                if g in size_keys and not processed_keys[g]:
                    if g in result['mem'] and int(result['mem'][g]) > 1024:
                        result['mem'][g] = int(int(result['mem'][g]) / 1024)
                        processed_keys[g] = True

        if 'sort_buffer_size' in result['mem'] and len(str(result['mem']['sort_buffer_size'])) < 3:
            result['mem']['sort_buffer_size'] = int(result['mem']['sort_buffer_size']) * 1024
        if 'read_buffer_size' in result['mem'] and len(str(result['mem']['read_buffer_size'])) < 3:
            result['mem']['read_buffer_size'] = int(result['mem']['read_buffer_size']) * 1024
        return public.success_v2(result)

    # 设置MySQL配置参数
    def SetDbConf(self, get):
        gets = ['key_buffer_size', 'query_cache_size', 'tmp_table_size', 'max_heap_table_size',
                'innodb_buffer_pool_size', 'innodb_log_buffer_size', 'max_connections', 'query_cache_type',
                'table_open_cache', 'thread_cache_size', 'sort_buffer_size', 'read_buffer_size', 'read_rnd_buffer_size',
                'join_buffer_size', 'thread_stack', 'binlog_cache_size']
        emptys = ['max_connections', 'query_cache_type', 'thread_cache_size', 'table_open_cache']
        annotation = {'mysql_set': 'bt_mysql_set', 'memSize': 'bt_mem_size', 'query_cache_size': 'bt_query_cache_size'}
        mycnf = public.readFile('/etc/my.cnf')
        n = 0
        m_version = public.readFile('/www/server/mysql/version.pl')
        if not m_version: m_version = ''

        # 保存选项
        for k, v in annotation.items():
            reg = v + r"\s+=\s+\d+(\.\d+)?"
            if re.search(reg, mycnf):
                bt_mysql_set = "{} = {}".format(v, get.get(k))
                mycnf = re.sub(v + r"\s+=\s+\d+(\.\d+)?", bt_mysql_set, mycnf, 1)
            else:
                mycnf = mycnf + "\n# {} = {}".format(v, get.get(k))
        for g in gets:
            if any(mysql_v in m_version for mysql_v in ['8.0','8.4','9.0']) and g in ['query_cache_type', 'query_cache_size']:
                n += 1
                continue

            if g not in get:
                n += 1
                continue

            s = 'M'
            if n > 5 and not g in ['key_buffer_size', 'query_cache_size', 'tmp_table_size', 'max_heap_table_size',
                                   'innodb_buffer_pool_size', 'innodb_log_buffer_size']: s = 'K'
            if g in emptys: s = ''
            if g in ['innodb_log_buffer_size']:
                s = 'M'
                if int(get[g]) < 8:
                    return public.fail_v2("innodb_log_buffer_size cannot be less than 8MB")

            rep = r'\s*' + g + r'\s*=\s*\d+(M|K|k|m|G)?\n'

            c = g + ' = ' + get[g] + s + '\n'
            if mycnf.find(g) != -1:
                mycnf = re.sub(rep, '\n' + c, mycnf, 1)
            else:
                mycnf = mycnf.replace('[mysqld]\n', '[mysqld]\n' + c)
            n += 1
        public.writeFile('/etc/my.cnf', mycnf)
        return public.success_v2("Setup successfully!")

    # 获取MySQL运行状态
    def GetRunStatus(self, get):
        import time
        result = {}
        data = panelMysql.panelMysql().query('show global status')
        gets = ['Max_used_connections', 'Com_commit', 'Com_rollback', 'Questions', 'Innodb_buffer_pool_reads',
                'Innodb_buffer_pool_read_requests', 'Key_reads', 'Key_read_requests', 'Key_writes',
                'Key_write_requests', 'Qcache_hits', 'Qcache_inserts', 'Bytes_received', 'Bytes_sent',
                'Aborted_clients', 'Aborted_connects', 'Created_tmp_disk_tables', 'Created_tmp_tables',
                'Innodb_buffer_pool_pages_dirty', 'Opened_files', 'Open_tables', 'Opened_tables', 'Select_full_join',
                'Select_range_check', 'Sort_merge_passes', 'Table_locks_waited', 'Threads_cached', 'Threads_connected',
                'Threads_created', 'Threads_running', 'Connections', 'Uptime']
        try:
            if data[0] == 1045:
                return public.fail_v2("MySQL password ERROR!")
            for d in data:
                for g in gets:
                    try:
                        if d[0] == g: result[g] = d[1]
                    except:
                        pass
        except:
            return public.fail_v2(str(data))

        if not 'Run' in result and result:
            result['Run'] = int(time.time()) - int(result['Uptime'])
        # tmp = panelMysql.panelMysql().query('show master status')
        m_version = public.readFile(public.GetConfigValue('setup_path') + '/mysql/version.pl')
        if m_version.find('8.4') != -1 or m_version.find('9.0') != -1:
            tmp = panelMysql.panelMysql().query('SHOW BINARY LOG STATUS')
        else:
            tmp = panelMysql.panelMysql().query('show master status')

        try:

            result['File'] = tmp[0][0]
            result['Position'] = tmp[0][1]
        except:
            result['File'] = 'OFF'
            result['Position'] = 'OFF'
        return public.success_v2(result)

    # 取慢日志
    def GetSlowLogs(self, get):
        path = self.GetMySQLInfo(get)['message'].get('datadir')
        if not path:
            return public.fail_v2("get MySQL datadir fail!")
        path = path + '/mysql-slow.log'
        if not os.path.exists(path):
            return public.fail_v2("Log file does NOT exist!")
        return public.success_v2(public.GetNumLines(path, 100))

    # 获取binlog文件列表
    def GetMySQLBinlogs(self, get):
        data_dir = self.GetMySQLInfo(get)['message'].get('datadir')
        index_file = os.path.join(data_dir, "mysql-bin.index")
        if not os.path.exists(index_file):
            return public.fail_v2("Binlog is not enabled or binlog file does not exist!")

        text = public.readFile(index_file)

        # rows = panelMysql.panelMysql().query("show master status")
        m_version = public.readFile(public.GetConfigValue('setup_path') + '/mysql/version.pl')
        if m_version.find('8.4') != -1 or m_version.find('9.0') != -1:
            rows = panelMysql.panelMysql().query("SHOW BINARY LOG STATUS")
        else:
            rows = panelMysql.panelMysql().query("show master status")
        current_log = ""
        if not isinstance(rows, list):
            return public.fail_v2("Mysql status is abnormal!")
        if len(rows) != 0:
            current_log = rows[0][0]

        bin_log = []
        for item in text.split('\n'):
            log_file = item.strip()
            log_name = log_file.lstrip("./")
            if not log_file: continue  # 空行
            bin_log_path = os.path.join(data_dir, log_name)
            if not os.path.isfile(bin_log_path): continue
            st = os.stat(bin_log_path)
            bin_log.append({
                "name": log_name,
                "path": bin_log_path,
                "size": st.st_size,
                "last_modified": int(st.st_mtime),
                "last_access": int(st.st_atime),
                "current": current_log == log_name
            })
        return public.success_v2(bin_log)

    def ClearMySQLBinlog(self, get):
        if not hasattr(get, "days"):
            return public.returnMsg(False, public.lang("Parameters are missing! days"))
        if not str(get.days).isdigit():
            return public.returnMsg(False, public.lang("Parameters are missing! days"))
        days = int(get.days)
        if days < 7: return public.return_msg_gettext(False, public.lang("To ensure data security, recent binlogs cannot be deleted!"))

        rows = panelMysql.panelMysql().query("PURGE BINARY LOGS BEFORE DATE_SUB(NOW(), INTERVAL {days} DAY)".format(days=days))
        # public.print_log(rows)
        # if rows: public.print_log(rows[0])

        return public.return_msg_gettext(True, public.lang("Cleanup complete!"))

    # 获取当前数据库信息
    def GetInfo(self, get):
        # 校验参数
        try:
            get.validate([
                Param('db_name').Require().String(),

            ], [
                public.validate.trim_filter(),
            ])
        except Exception as ex:
            public.print_log("error info: {}".format(ex))
            return public.return_message(-1, 0, str(ex))

        info = self.GetdataInfo(get)
        # return info
        return public.return_message(0, 0,  info)
        # if info:
        #     return info
        # else:
        #     return public.return_msg_gettext(False, public.lang("Failed to get databases"))

    # 修复表信息
    def ReTable(self, get):
        info = self.RepairTable(get)
        if info:
            # return public.return_msg_gettext(True, public.lang("Successfully repaired!"))
            return public.return_message(0, 0, public.lang("Successfully repaired!"))
        else:
            # return public.return_msg_gettext(False, public.lang("Failed to repair!"))
            return public.return_message(-1, 0, public.lang("Failed to repair!"))

    # 优化表
    def OpTable(self, get):


        info = self.OptimizeTable(get)
        if info:
            # return public.return_msg_gettext(True, public.lang("Successfully optimized!"))
            return public.return_message(0, 0, public.lang("Successfully optimized!"))
        else:
            # return public.return_msg_gettext(False, public.lang("Failed to optimize or already optimized"))
            return public.return_message(-1, 0, public.lang("Failed to optimize or already optimized"))

    # 更改表引擎
    def AlTable(self, get):

        # 校验参数
        try:
            get.validate([
                Param('db_name').Require().String(),
                Param('tables').Require().String(),   # ["wp_commentmeta"]
                Param('table_type').Require().String(),

            ], [
                public.validate.trim_filter(),
            ])
        except Exception as ex:
            public.print_log("error info: {}".format(ex))
            return public.return_message(-1, 0, str(ex))


        info = self.AlterTable(get)
        if info:
            # return public.return_msg_gettext(True, public.lang("Successfully changed"))
            return public.return_message(0, 0, public.lang("Successfully changed"))
        else:
            # return public.return_msg_gettext(False, public.lang("Failed to change"))
            return public.return_message(-1, 0, public.lang("Failed to change"))

    def get_average_num(self, slist):
        """
        @获取平均值
        """
        count = len(slist)
        limit_size = 1 * 1024 * 1024
        if count <= 0: return limit_size

        if len(slist) > 1:
            slist = sorted(slist)
            limit_size = int((slist[0] + slist[-1]) / 2 * 0.85)
        return limit_size

    def get_database_size(self, ids, is_pid=False):
        """
        获取数据库大小
        """
        result = {}
        for id in ids:
            if not is_pid:
                x = public.M('databases').where('id=?', id).field('id,sid,pid,name,type,ps,addtime').find()
            else:
                x = public.M('databases').where('pid=?', id).field('id,sid,pid,name,ps,type,addtime').find()
            if not x: continue
            x['backup_count'] = public.M('backup').where("pid=? AND type=?", (x['id'], '1')).count()
            if x['type'] == 'MySQL':
                x['total'] = int(public.get_database_size_by_id(x['id']))
            else:
                try:
                    from panelDatabaseController import DatabaseController
                    project_obj = DatabaseController()

                    get = public.dict_obj()
                    get['data'] = {'db_id': x['id']}
                    get['mod_name'] = x['type'].lower()
                    get['def_name'] = 'get_database_size_by_id'

                    x['total'] = project_obj.model(get)
                except:
                    x['total'] = int(public.get_database_size_by_id(x['id']))
            result[x['name']] = x
        return result

    def check_del_data(self, get):
        """
        @删除数据库前置检测
        """

        # 校验参数
        try:
            get.validate([
                Param('ids').Require(),

            ], [
                public.validate.trim_filter(),
            ])
        except Exception as ex:
            public.print_log("error info: {}".format(ex))
            return public.return_message(-1, 0, str(ex))

        ids = json.loads(get.ids)
        slist = {}
        result = []
        db_list_size = []
        db_data = self.get_database_size(ids)
        for key in db_data:
            data = db_data[key]
            if not data['id'] in ids: continue

            db_addtime = public.to_date(times=data['addtime'])
            data['score'] = int(time.time() - db_addtime) + data['total']
            data['st_time'] = db_addtime

            if data['total'] > 0: db_list_size.append(data['total'])
            result.append(data)

        slist['data'] = sorted(result, key=lambda x: x['score'], reverse=True)
        slist['db_size'] = self.get_average_num(db_list_size)
        # return slist
        return public.return_message(0, 0, slist)


    # 获取备份文件
    def GetBackup(self, get):

        # 分页校验参数
        try:
            get.validate([
                Param('limit').Integer(),
                Param('p').Integer(),
                Param('search').String(),
            ], [
                public.validate.trim_filter(),
            ])
        except Exception as ex:
            public.print_log("error info: {}".format(ex))
            return public.return_message(-1, 0, str(ex))

        p = getattr(get, "p", 1)
        limit = getattr(get, "limit", 10)
        return_js = getattr(get, "return_js", "")
        search = getattr(get, "search", None)

        # if not str(p).isdigit():
        #     return public.returnMsg(False, public.lang("参数错误！p"))
        # if not str(limit).isdigit():
        #     return public.returnMsg(False, public.lang("参数错误！limit"))

        p = int(p)
        limit = int(limit)

        ext_list = ["sql", "tar.gz", "gz", "zip"]

        backup_list = []

        # 递归获取备份文件
        def get_dir_backup(backup_dir: str, backup_list: list, is_recursion: bool):
            for name in os.listdir(backup_dir):
                path = os.path.join(backup_dir, name)
                if os.path.isdir(path) and name == "all_backup": continue  # 跳过全部备份目录
                if os.path.isfile(path):
                    ext = name.split(".")[-1]
                    if ext.lower() not in ext_list: continue
                    if search is not None and search not in name: continue

                    stat_file = os.stat(path)
                    path_data = {
                        "name": name,
                        "path": path,
                        "size": stat_file.st_size,
                        "mtime": int(stat_file.st_mtime),
                        "ctime": int(stat_file.st_ctime),
                    }
                    backup_list.append(path_data)
                elif os.path.isdir(path) and is_recursion is True:
                    get_dir_backup(path, backup_list, is_recursion)

        get_dir_backup(self._MYSQL_BACKUP_DIR, backup_list, True)
        get_dir_backup(self._DB_BACKUP_DIR, backup_list, False)

        try:
            from flask import request
            uri = public.url_encode(request.full_path)
        except:
            uri = ''
        # 包含分页类
        import page
        # 实例化分页类
        page = page.Page()
        info = {
            "p": p,
            "count": len(backup_list),
            "row": limit,
            "return_js": return_js,
            "uri": uri,
        }
        page_info = page.GetPage(info)

        start_idx = (int(p) - 1) * limit
        end_idx = p * limit if p * limit < len(backup_list) else len(backup_list)
        backup_list.sort(key=lambda data: data["mtime"], reverse=True)
        backup_list = backup_list[start_idx:end_idx]
        # return {"status": True, "msg": "OK", "data": backup_list, "page": page_info}
        return public.return_message(0, 0, {"status": True, "msg": "OK", "data": backup_list, "page": page_info})

    # 获取所有用户列表
    def GetMysqlUser(self, get):
        try:
            get.validate([
                Param('sid').Require().Integer('>=', 0),
                Param('search').String(),
            ], [
                public.validate.trim_filter(),
            ])
        except Exception as ex:
            public.print_log("error info: {}".format(ex))
            return public.return_message(-1, 0, str(ex))
        search = getattr(get, "search", None)
        mysql_obj = public.get_mysql_obj_by_sid(get.sid)
        if not mysql_obj:
            return public.fail_v2(public.lang("Database connection error!"))

        if search is not None:
            user_data = mysql_obj.query(
                "SELECT user FROM mysql.user WHERE user not in ('mysql.sys', 'mysql.session', 'mysql.infoschema', '') "
                "and user like '%{}%' GROUP BY user;".format(search)
            )
        else:
            user_data = mysql_obj.query(
                "SELECT user FROM mysql.user WHERE user not in ('mysql.sys', 'mysql.session', 'mysql.infoschema', '') "
                "GROUP BY user;"
            )
        if not isinstance(user_data, list):
            return public.fail_v2(public.lang("Database connection error!"))
        filter_user = ['mariadb.sys', 'PUBLIC']
        user_data = [x for x in user_data if x[0] not in filter_user]
        # get alarm msg
        try:
            push_dict = json.loads(public.readFile(os.path.join(public.get_panel_path(), "class/push/push.json")))
            database_push = push_dict.get("database_push", {})
            if not isinstance(database_push, dict):
                database_push = {}
        except:
            database_push = {}

        is_password_last_changed = False
        try:
            data_list = mysql_obj.query(
                "SELECT count(*) FROM information_schema.COLUMNS WHERE TABLE_SCHEMA = 'mysql' "
                "AND TABLE_NAME = 'user' AND COLUMN_NAME = 'password_last_changed';"
            )
            if data_list == [[1]]:
                is_password_last_changed = True
        except Exception as e:
            public.print_log("error info: {}".format(e))
            pass

        user_list = []
        for user_item in user_data:
            user = user_item[0]
            if is_password_last_changed is True:
                host_data = mysql_obj.query(
                    "SELECT host, authentication_string, password_last_changed FROM mysql.user WHERE user='{}';".format(
                        user)
                )
            else:
                host_data = mysql_obj.query(
                    "SELECT host, authentication_string, null FROM mysql.user WHERE user='{}';".format(user)
                )
            if not isinstance(host_data, list):
                continue
            host_list = []
            for host_item in host_data:
                info = {
                    "host": host_item[0],
                    "password": "Has" if host_item[1] else "None",
                    "password_last_changed": host_item[2].strftime("%Y-%m-%d %H:%M:%S") if host_item[2] else host_item[
                        2],
                    "password_expire_push": {
                        "time": int(time.time()),
                        "tid": "database_push@0",
                        "type": "mysql_pwd_endtime",
                        "title": public.lang("MySQL database password expires"),
                        "status": False,
                        "count": 0,
                        "project": [int(get.sid), user, host_item[0]],
                        "cycle": 15,
                        "push_count": 1,
                        "interval": 600,
                        "module": "",
                        "module_type": "database_push"
                    },
                }
                # get alarm msg
                for key, push_info in database_push.items():
                    if push_info.get("project") == [int(get.sid), user, info["host"]]:
                        push_info["time"] = key
                        info["password_expire_push"].update(push_info)
                host_list.append(info)

            user_info = {
                "user": user,
                "list": host_list,
            }
            user_list.append(user_info)
        return public.success_v2({"data": user_list, "is_password_last_changed": is_password_last_changed})

    # 获取用户有权限的数据库表
    def GetUserHostDbGrant(self, get):
        try:
            get.validate([
                Param('sid').Require().Integer('>=', 0),
                Param('username').Require().String(),
                Param('host').Require().String(),
            ], [
                public.validate.trim_filter(),
            ])
        except Exception as ex:
            public.print_log("error info: {}".format(ex))
            return public.return_message(-1, 0, str(ex))

        mysql_obj = public.get_mysql_obj_by_sid(get.sid)
        if not mysql_obj:
            return public.fail_v2(public.lang("Database connection error!"))

        access_data = mysql_obj.query("SHOW GRANTS FOR `{}`@`{}`;".format(get.username, get.host))
        if not isinstance(access_data, list):
            return public.fail_v2(public.lang("Database query error!"))

        last_access_list = []
        for access_item in access_data:
            re_obj = re.search(
                "GRANT\s*([^.]+)\s*ON\s*([^.]+)\.([^.]+)\s*TO", access_item[0], flags=re.IGNORECASE
            )
            if re_obj:
                access_str = re_obj.group(1)
                database = re_obj.group(2).strip("`'\" ")
                table = re_obj.group(3).strip("`'\" ")
                access_list = []
                for access in access_str.split(","):
                    access = access.strip()
                    access_temp = {
                        "title": public.lang(access.capitalize()),
                        "access": access,
                    }
                    access_list.append(access_temp)
                access_info = {
                    "database": database,
                    "table": table,
                    "access": access_list,
                }
                last_access_list.append(access_info)
        return public.success_v2({"data": last_access_list})

    @staticmethod
    def _host_db_table_grant(host_grants: list, db_name: str, tb: str) -> list:
        access_list = []
        for grant in host_grants:
            if db_name == "*" and tb == "*":
                access_list.extend(
                    [x.get("access", []) for x in grant.get("access", [])]
                )
            elif grant.get("database") == db_name and grant.get("table") == tb:
                access_list.extend(
                    [x.get("access", []) for x in grant.get("access", [])]
                )
        return access_list

    # 获取用户所有数据库表的所有权限
    def GetDatabasesList(self, get):
        try:
            get.validate([
                Param('sid').Require().Integer('>=', 0),
                Param('username').Require().String(),
                Param('host').Require().String(),
            ], [
                public.validate.trim_filter(),
            ])
        except Exception as ex:
            public.print_log("error info: {}".format(ex))
            return public.return_message(-1, 0, str(ex))

        mysql_obj = public.get_mysql_obj_by_sid(get.sid)
        if not mysql_obj:
            return public.fail_v2("Database connection error!")

        db_names = mysql_obj.query(
            "select schema_name from information_schema.schemata where schema_name not in "
            "('sys', 'mysql', 'information_schema', 'performance_schema');"
        )
        if not isinstance(db_names, list):
            return public.fail_v2(f"Database query failed! {db_names}")
        try:
            user_host_grant = self.GetUserHostDbGrant(get)
            if user_host_grant.get('status') != 0:
                return public.fail_v2(f"Database query failed! {user_host_grant}")
            user_host_grant = user_host_grant.get("message").get("data", [])
        except Exception as ex:
            return public.fail_v2(f"Database query failed! {ex}")

        db_list = []
        for d in db_names:
            db_name = d[0]
            # ALL PRIVILEGES
            all_acc_list = self._host_db_table_grant(user_host_grant, db_name, "*")
            info = {
                "name": db_name,
                "value": db_name,
                "tb_list": [
                    {"name": "All", "value": "*", "access_list": all_acc_list}
                ],
            }
            table_list = mysql_obj.query("show tables from `{}`;".format(db_name))
            if not isinstance(table_list, list):
                continue
            tb_list = []
            # other table
            for tb in table_list:
                tb_acc = self._host_db_table_grant(user_host_grant, db_name, tb[0])
                tb_info = {
                    "name": tb[0],
                    "value": tb[0],
                    "access_list": tb_acc,
                }
                tb_list.append(tb_info)
            info["tb_list"].extend(tb_list)
            db_list.append(info)
        return public.success_v2({"data": db_list})

    @staticmethod
    def _legal_pwd(pwd: str) -> str:
        re_list = re.findall("[，。？！；：“”‘’（）【】《》￥&\u4e00-\u9fa5]+", pwd)
        if re_list:
            return f'Database password cannot contain Chinese characters {" ".join(re_list)}'
        if pwd.find("'") != -1 or pwd.find('"') != -1:
            return "Database password cannot contain quotation marks"
        return ""

    # 添加用户
    def AddMysqlUser(self, get):
        try:
            get.validate([
                Param('sid').Require().Integer(),
                Param('username').Require().String(),
                Param('password').Require().String(),
                Param('host').Require().String(),
            ], [
                public.validate.trim_filter(),
            ])
        except Exception as ex:
            public.print_log("error info: {}".format(ex))
            return public.return_message(-1, 0, str(ex))

        username = get.username
        password = get.password
        host = get.host
        check = self._legal_pwd(password)
        if check != "":
            return public.fail_v2(check)

        if host != "localhost" and host != "%" and host != "127.0.0.1":
            if public.check_ip(host) is False:
                return public.fail_v2('Please fill in the correct IP')

        mysql_obj = public.get_mysql_obj_by_sid(int(get.sid))
        if not mysql_obj:
            return public.fail_v2("Database connection error!")

        data_list = mysql_obj.query(
            "SELECT count(user) FROM mysql.user WHERE user='{}' and host='{}';".format(username, host)
        )
        if data_list == [[1]]:
            return public.return_message(-1, 0, 'There is already a user with the same username and hostname!')
        result = mysql_obj.execute(
            "CREATE USER `{}`@`{}` IDENTIFIED BY '{}';".format(username, host, password)
        )
        isError = self.IsSqlError(result)
        if isError is not None:
            return public.fail_v2(isError)
        return public.success_v2('ADD_SUCCESS')

    # 删除用户
    def DelMysqlUser(self, get):
        try:
            get.validate([
                Param('sid').Require().Integer(),
                Param('username').Require().String(),
                Param('host').Require().String(),
            ], [
                public.validate.trim_filter(),
            ])
        except Exception as ex:
            public.print_log("error info: {}".format(ex))
            return public.return_message(-1, 0, str(ex))

        username = get.username
        host = get.host
        if username == "root":
            return public.fail_v2('root account can not be delete')
        mysql_obj = public.get_mysql_obj_by_sid(get.sid)
        if not mysql_obj:
            return public.fail_v2("Database connection error!")
        result = mysql_obj.execute("drop user `{}`@`{}`".format(username, host))
        isError = self.IsSqlError(result)
        if isError is not None:
            return public.fail_v2(isError)
        return public.success_v2('DEL_SUCCESS')

    # 修改用户密码
    def ChangeUserPass(self, get):
        try:
            get.validate([
                Param('sid').Require().Integer('>=', 0),
                Param('username').Require().String(),
                Param('host').Require().String(),
                Param('password').Require().String(),
            ], [
                public.validate.trim_filter(),
            ])
        except Exception as ex:
            public.print_log("error info: {}".format(ex))
            return public.return_message(-1, 0, str(ex))

        username = get.username
        newpassword = get.password
        host = get.host
        check = self._legal_pwd(newpassword)
        if check != "":
            return public.fail_v2(check)

        mysql_obj = public.get_mysql_obj_by_sid(get.sid)
        if not mysql_obj:
            return public.fail_v2("Database connection error!")

        m_version = public.readFile(public.GetConfigValue('setup_path') + '/mysql/version.pl')
        if m_version.find('5.7') != -1 or m_version.find('8.0') != -1:
            result = mysql_obj.execute(
                "ALTER USER `{}`@`{}` IDENTIFIED BY '{}';".format(username, host, newpassword)
            )
        elif any(mariadb_ver in m_version for mariadb_ver in ['10.5.', '10.4.', '10.6.', '10.7.', '10.11.', '11.3.']):
            accept = self.map_to_list(mysql_obj.query(
                "select Host from mysql.user where User='{}' AND Host!='localhost'".format(username)
            ))
            result = mysql_obj.execute(
                "ALTER USER `{}`@`localhost` IDENTIFIED BY '{}';".format(username, newpassword)
            )
            for my_host in accept:
                mysql_obj.execute(
                    "ALTER USER `{}`@`{}` IDENTIFIED BY '{}';".format(username, my_host[0], newpassword)
                )
        else:
            result = mysql_obj.execute(
                "update mysql.user set Password=password('{}') where User='{}'".format(newpassword, username)
            )

        isError = self.IsSqlError(result)
        if isError is not None:
            return public.fail_v2(isError)

        mysql_obj.execute("flush privileges")
        return public.success_v2('Password changed successfully')

    # 获取用户权限
    def GetUserGrants(self, get):
        try:
            get.validate([
                Param('sid').Require().Integer('>=', 0),
                Param('username').Require().String(),
                Param('host').Require().String(),
            ], [
                public.validate.trim_filter(),
            ])
        except Exception as ex:
            public.print_log("error info: {}".format(ex))
            return public.return_message(-1, 0, str(ex))

        username = get.username
        host = get.host
        mysql_obj = public.get_mysql_obj_by_sid(get.sid)
        if not mysql_obj:
            return public.fail_v2("Database connection error!")

        usergrant = mysql_obj.query("SHOW GRANTS FOR `{}`@`{}`;".format(username, host))
        merged_text = "\n".join([item[0] for item in usergrant if item])
        return public.success_v2(merged_text)

    # 添加用户权限
    def AddUserGrants(self, get):
        try:
            get.validate([
                Param('sid').Require().Integer('>=', 0),
                Param('username').Require().String(),
                Param('host').Require().String(),
                Param('db_name').Require().String(),
                Param('tb_name').Require().String(),
                Param('access').Require().String(),
                Param('with_grant').String(),
            ], [
                public.validate.trim_filter(),
            ])
        except Exception as ex:
            public.print_log("error info: {}".format(ex))
            return public.return_message(-1, 0, str(ex))

        username = get.username
        host = get.host
        db_name = get.db_name
        tb_name = get.tb_name
        access = get.access.replace(",", ", ")
        with_grant = get.with_grant == "1"  # 是否允许创建用户授权其它用户, (不开放)
        mysql_obj = public.get_mysql_obj_by_sid(get.sid)
        if not mysql_obj:
            return public.fail_v2("Database connection error!")
        user_access = mysql_obj.query("SHOW GRANTS FOR `{}`@`{}`".format(username, host))
        if not isinstance(user_access, list):
            return public.fail_v2("query user `{}`@`{}` permission fail!".format(username, host))
        user_access = [access[0].lower() for access in user_access]

        if db_name != "*":
            db_name = "`{}`".format(db_name)
        if tb_name != "*":
            tb_name = "`{}`".format(tb_name)
        if with_grant is True:
            grant_sql = "grant {access} on {db_name}.{tb_name} to `{user}`@`{host}` WITH GRANT OPTION;".format(
                access=access,
                db_name=db_name,
                tb_name=tb_name,
                user=username,
                host=host
            )
        else:
            grant_sql = "grant {access} on {db_name}.{tb_name} to `{user}`@`{host}`;".format(
                access=access,
                db_name=db_name,
                tb_name=tb_name,
                user=username,
                host=host
            )

        if grant_sql.lower().replace(";", "") in user_access:
            return public.fail_v2("a user with the same username and hostname already exists!")

        has_access = ""
        for i in user_access:
            if db_name in i and tb_name in i:
                regex = re.search(r'grant\s+(.*?)\s+on', i, re.IGNORECASE)
                if regex:
                    has_access = regex.group(1)
                    break
        if has_access:  # revoke permission if user has
            get.access = has_access
            revoke = self.DelUserGrants(get)
            if revoke.get("status") != 0:
                return public.fail_v2(revoke.get("message"))

        result = mysql_obj.execute(grant_sql)
        isError = self.IsSqlError(result)
        if isError is not None:
            return public.fail_v2(isError)

        mysql_obj.execute("flush privileges")
        return public.success_v2("Added successfully!")

    # 删除用户权限
    def DelUserGrants(self, get):
        try:
            get.validate([
                Param('sid').Require().Integer('>=', 0),
                Param('username').Require().String(),
                Param('host').Require().String(),
                Param('db_name').Require().String(),
                Param('tb_name').Require().String(),
                Param('access').Require().String(),
                Param('with_grant').String(),
            ], [
                public.validate.trim_filter(),
            ])
        except Exception as ex:
            public.print_log("error info: {}".format(ex))
            return public.return_message(-1, 0, str(ex))

        username = get.username
        if username == "root":
            return public.fail_v2("root user cannot be deleted!")
        host = get.host
        db_name = get.db_name
        tb_name = get.tb_name
        access = get.access
        with_grant: bool = get.with_grant == "1"  # 是否允许创建用户授权其它用户

        mysql_obj = public.get_mysql_obj_by_sid(get.sid)
        if not mysql_obj:
            return public.fail_v2("Database connection error!")

        if db_name != "*":
            db_name = "`{}`".format(db_name)
        if tb_name != "*":
            tb_name = "`{}`".format(tb_name)

        if with_grant is True:
            grant_sql = "revoke {access} on {db_name}.{tb_name} from `{user}`@`{host}` WITH GRANT OPTION;".format(
                access=access,
                db_name=db_name,
                tb_name=tb_name,
                user=username,
                host=host
            )
        else:
            grant_sql = "revoke {access} on {db_name}.{tb_name} from `{user}`@`{host}`;".format(
                access=access,
                db_name=db_name,
                tb_name=tb_name,
                user=username,
                host=host
            )
        result = mysql_obj.execute(grant_sql)
        isError = self.IsSqlError(result)
        if isError is not None:
            return public.fail_v2(isError)

        mysql_obj.execute("flush privileges")
        return public.success_v2("Revocation of authorization successful!")

    def mysql_oom_adj(self, get):
        oom_score_adj_value = None
        if not hasattr(get, "status"):
            oom_score_adj_value = None
        else:
            oom_status = int(get.status)
            if oom_status == 1:
                oom_score_adj_value = "-1000"
            elif oom_status == 0:
                oom_score_adj_value = "0"

        data_path = self.GetMySQLInfo(get)['message'].get('datadir')
        if not os.path.exists(data_path):
            return public.fail_v2(
                'The database directory does not exist. Please check whether MySQL is installed properly.'
            )
        import socket
        hostname = socket.gethostname()
        mysqld_pid_file = data_path + "/" + hostname + ".pid"
        if os.path.exists(mysqld_pid_file):
            mysql_pid = int(public.ReadFile(mysqld_pid_file).strip())
            if os.path.exists(f"/proc/{mysql_pid}"):
                if oom_score_adj_value:
                    public.ExecShell(
                        "echo {} > /proc/{}/oom_score_adj".format(oom_score_adj_value, mysql_pid)
                    )
                    return public.success_v2('Set Successfully!')
                else:
                    oom_score_adj_value = public.ReadFile("/proc/{}/oom_score_adj".format(mysql_pid)).strip()
                    if oom_score_adj_value == "-1000":
                        return public.success_v2('Current Status is On!')
                    else:
                        return public.fail_v2('Current Status is Off!')
        return public.fail_v2(
            'No process information related to MySQL has been retrieved.'
            ' Please check whether MySQL has been started properly.'
        )
