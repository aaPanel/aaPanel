#coding: utf-8
# +-------------------------------------------------------------------
# | aaPanel
# +-------------------------------------------------------------------
# | Copyright (c) 2015-2099 aaPanel(www.aapanel.com) All rights reserved.
# +-------------------------------------------------------------------
# | Author: hwliang <hwl@aapanel.com>
# +-------------------------------------------------------------------

import re,os,sys,public

class panelMysql:
    __DB_PASS = None
    __DB_USER = 'root'
    __DB_PORT = 3306
    __DB_HOST = 'localhost'
    __DB_CONN = None
    __DB_CUR  = None
    __DB_ERR  = None
    __DB_NET = None
    #连接MYSQL数据库
    def __Conn(self):
        if self.__DB_NET: return True
        try:
            myconf = public.readFile('/etc/my.cnf')
            socket_re = re.search(r"socket\s*=\s*(.+)",myconf)
            if socket_re:
                socket = socket_re.groups()[0]
            else:
                socket = '/tmp/mysql.sock'

            try:
                if sys.version_info[0] != 2:
                    try:
                        import pymysql
                    except:
                        public.ExecShell("pip install pymysql")
                        import pymysql
                    pymysql.install_as_MySQLdb()
                import MySQLdb
                if sys.version_info[0] == 2:
                    reload(MySQLdb)
            except:
                try:
                    import pymysql
                    pymysql.install_as_MySQLdb()
                    import MySQLdb
                except Exception as e:
                    self.__DB_ERR = e
                    return False
            try:

                rep = r"port\s*=\s*([0-9]+)"
                self.__DB_PORT = int(re.search(rep,myconf).groups()[0])
            except:
                self.__DB_PORT = 3306
            self.__DB_PASS = public.M('config').where('id=?',(1,)).getField('mysql_root')
            
            try:
                self.__DB_CONN = MySQLdb.connect(host = self.__DB_HOST,user = self.__DB_USER,passwd = self.__DB_PASS,port = self.__DB_PORT,charset="utf8",connect_timeout=1,unix_socket=socket)
            except MySQLdb.Error as e:
                self.__DB_HOST = '127.0.0.1'
                self.__DB_CONN = MySQLdb.connect(host = self.__DB_HOST,user = self.__DB_USER,passwd = self.__DB_PASS,port = self.__DB_PORT,charset="utf8",connect_timeout=1,unix_socket=socket)
            self.__DB_CUR  = self.__DB_CONN.cursor()
            return True
        except MySQLdb.Error as e:
            self.__DB_ERR = e
            return False

    #连接远程数据库
    def connect_network(self,host,port,username,password):
        self.__DB_NET = True
        try:
            try:
                if sys.version_info[0] != 2:
                    try:
                        import pymysql
                    except:
                        public.ExecShell("pip install pymysql")
                        import pymysql
                    pymysql.install_as_MySQLdb()
                import MySQLdb
                if sys.version_info[0] == 2:
                    reload(MySQLdb)
            except:
                try:
                    import pymysql
                    pymysql.install_as_MySQLdb()
                    import MySQLdb
                except Exception as e:
                    self.__DB_ERR = e
                    return False
            self.__DB_CONN = MySQLdb.connect(host = host,user = username,passwd = password,port = port,charset="utf8",connect_timeout=10)
            self.__DB_CUR  = self.__DB_CONN.cursor()
            return True
        except MySQLdb.Error as e:
            self.__DB_ERR = e
            return False



    def execute(self,sql):
        #执行SQL语句返回受影响行
        if not self.__Conn(): return self.__DB_ERR
        try:
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
            #将元组转换成列表
            if sys.version_info[0] == 2:
                data = map(list,result)
            else:
                data = list(map(list,result))
            self.__Close()
            return data
        except Exception as ex:
            return ex


    #关闭连接        
    def __Close(self):
        self.__DB_CUR.close()
        self.__DB_CONN.close()


# Mysql数据库连接类 支持Context
class PanelMysqlWithContext:
    def __init__(self, db_name=None, db_user: str = 'root', db_pwd=None, db_host: str = 'localhost'):
        self.__CONN = None
        self.__DB_NAME = db_name
        self.__HOST = db_host
        self.__PORT = 3306
        self.__USERNAME = db_user
        self.__PASSWORD = db_pwd
        self.__CHARSET = 'utf8mb4'
        self.__CONNECT_TIMEOUT = 10
        self.__UNIX_SOCK = None

    def __enter__(self):
        if self.__CONN:
            return self

        if self.__HOST in ('localhost', '127.0.0.1'):
            self.__UNIX_SOCK = '/tmp/mysql.sock'
            self.__CONNECT_TIMEOUT = 1

            myconf = public.readFile('/etc/my.cnf')
            m = re.search(r"socket\s*=\s*(.+)", myconf)
            if m:
                self.__UNIX_SOCK = m.group(1)

            m = re.search(r"port\s*=\s*([0-9]+)", myconf)
            if m:
                self.__PORT = int(m.group(1))

            if self.__USERNAME == 'root':
                self.__PASSWORD = public.M('config').where('id=?', (1,)).getField('mysql_root')

        import pymysql

        try:
            self.__CONN = pymysql.connect(host=self.__HOST, user=self.__USERNAME, passwd=self.__PASSWORD,
                                             port=self.__PORT, charset=self.__CHARSET, database=self.__DB_NAME,
                                             connect_timeout=self.__CONNECT_TIMEOUT,
                                             cursorclass=pymysql.cursors.DictCursor, unix_socket=self.__UNIX_SOCK)
        except pymysql.Error:
            if self.__HOST == 'localhost':
                self.__HOST = '127.0.0.1'
                self.__CONN = pymysql.connect(host=self.__HOST, user=self.__USERNAME, passwd=self.__PASSWORD,
                                                 port=self.__PORT, charset=self.__CHARSET, database=self.__DB_NAME,
                                                 connect_timeout=self.__CONNECT_TIMEOUT,
                                                 cursorclass=pymysql.cursors.DictCursor, unix_socket=self.__UNIX_SOCK)
            raise

        return self

    def __del__(self):
        if self.__CONN:
            self.__CONN.close()
            self.__CONN = None

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.__CONN.close()
        self.__CONN = None

    # 执行SQL
    def execute(self, sql):
        cur = self.__CONN.cursor()

        try:
            row_count = cur.execute(sql)

            self.__CONN.commit()

            return row_count
        finally:
            cur.close()

    # 查询多条
    def query(self, sql):
        cur = self.__CONN.cursor()

        try:
            row_count = cur.execute(sql)

            if row_count == 0:
                return []

            return cur.fetchall()
        finally:
            cur.close()

    # 查询单条
    def find(self, sql):
        ret = self.query(sql)

        if len(ret) == 0:
            return None

        return ret[0]
