# coding: utf-8
import json
import os
import sys
import time

panelPath = '/www/server/panel'
os.chdir(panelPath)
if not panelPath + "/class/" in sys.path:
    sys.path.insert(0, panelPath + "/class/")
import public, re
from public.exceptions import HintException


class databaseBase:
    def get_base_list(self, args, sql_type='mysql'):
        """
        @获取数据库列表
        @type:数据库类型，MySQL,SQLServer
        """
        search = ''
        if 'search' in args: search = args['search']

        conditions = ''
        if '_' in search:
            cs = ''
            for i in search:
                if i == '_':
                    cs += '/_'
                else:
                    cs += i
            search = cs
            conditions = " escape '/'"

        SQL = public.M('databases')

        where = "lower(type) = lower('{}')".format(sql_type)
        if search:
            where += "AND (name like '%{search}%' or ps like '%{search}%'{conditions})".format(search=search,
                                                                                               conditions=conditions)
        if 'db_type' in args:
            where += " AND db_type='{}'".format(args['db_type'])

        if 'sid' in args:
            where += " AND sid='{}'".format(args['sid'])

        order = "id desc"
        if hasattr(args, 'order'): order = args.order

        info = {}
        rdata = {}

        info['p'] = 1
        info['row'] = 20
        result = '1,2,3,4,5,8'
        info['count'] = SQL.where(where, ()).count()

        if hasattr(args, 'limit'): info['row'] = int(args.limit)
        if hasattr(args, 'result'): result = args.result
        if hasattr(args, 'p'): info['p'] = int(args['p'])

        import page
        # 实例化分页类
        page = page.Page()

        info['uri'] = args
        info['return_js'] = ''
        if hasattr(args, 'tojs'): info['return_js'] = args.tojs

        rdata['where'] = where

        # 获取分页数据
        rdata['page'] = page.GetPage(info, result)
        # 取出数据
        rdata['data'] = SQL.where(where, ()).order(order).field(
            'id,sid,pid,name,username,password,accept,ps,addtime,type,db_type,conn_config').limit(
            str(page.SHIFT) + ',' + str(page.ROW)).select()

        if type(rdata['data']) == str:
            raise HintException("Database query error: " + rdata['data'])

        for sdata in rdata['data']:
            # 清除不存在的
            backup_count = 0
            backup_list = public.M('backup').where("pid=? AND type=1", (sdata['id'])).select()
            for backup in backup_list:
                if not os.path.exists(backup["filename"]):
                    public.M('backup').where("id=? AND type=1", (backup['id'])).delete()
                    continue
                backup_count += 1
            sdata['backup_count'] = backup_count
            sdata['conn_config'] = json.loads(sdata['conn_config'])
        return rdata

    def get_databaseModel(self):
        '''
        获取数据库模型对象
        @db_type 数据库类型
        '''
        from panelDatabaseControllerV2 import DatabaseController

        project_obj = DatabaseController()

        return project_obj

    def get_average_num(self, slist):
        """
        @批量删除获取平均值
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
        p = self.get_databaseModel()
        for id in ids:
            if not is_pid:
                x = public.M('databases').where('id=?', id).field('id,sid,pid,name,type,ps,addtime').find()
            else:
                x = public.M('databases').where('pid=?', id).field('id,sid,pid,name,type,ps,addtime').find()
            if not x: continue
            x['backup_count'] = public.M('backup').where("pid=? AND type=?", (x['id'], '1')).count()
            if x['type'] == 'MySQL':
                x['total'] = int(public.get_database_size_by_id(id))
            else:
                try:

                    get = public.dict_obj()
                    get['data'] = {'db_id': x['id']}
                    get['mod_name'] = x['type'].lower()
                    get['def_name'] = 'get_database_size_by_id'
                    try:
                        x['total'] = p.model(get)["message"]["result"]
                    except:
                        x['total'] = 0
                except:
                    x['total'] = 0
            result[x['name']] = x

        return result

    def check_base_del_data(self, get):
        """
        @删除数据库前置检测
        """
        if not hasattr(get, 'ids'):
            raise HintException("Parameter 'ids' is required for deletion.")
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
        return slist

    def get_test(self, args):

        p = self.get_databaseModel()
        get = public.dict_obj()
        get['data'] = {'db_id': 18}
        get['mod_name'] = args['type'].lower()
        get['def_name'] = 'get_database_size_by_id'

        return p.model(get)

    def add_base_database(self, get, dtype):
        """
        @添加数据库前置检测
        @return username 用户名
                data_name 数据库名
                data_pwd:数据库密码
        """
        data_name = get['name'].strip().lower()
        if self.check_recyclebin(data_name):
            return public.returnMsg(False, public.lang(
                "Database [' + data_name + '] is already in recycle bin, please restore from recycle bin!"))

        if len(data_name) > 16:
            return public.returnMsg(False, public.lang("Database name cannot be more than 16 characters!"))

        if not hasattr(get, 'db_user'): get.db_user = data_name
        username = get.db_user.strip()
        checks = ['root', 'mysql', 'test', 'sys', 'panel_logs']
        if username in checks or len(username) < 1:
            return public.returnMsg(False, public.lang("Database username is invalid!"))
        if data_name in checks or len(data_name) < 1:
            return public.returnMsg(False, public.lang("Database name is invalid!"))

        reg = r"^\w+$"
        if not re.match(reg, data_name):
            return public.returnMsg(False, public.lang("Database name cannot contain special characters!"))

        data_pwd = get['password']
        if len(data_pwd) < 1:
            data_pwd = public.md5(str(time.time()))[0:8]

        if public.M('databases').where("(name=? or username=?) AND LOWER(type)=LOWER(?)",
                                       (data_name, username, dtype)).count():
            return public.returnMsg(False, public.lang("Database exists!"))

        res = {
            'data_name': data_name,
            'username': username,
            'data_pwd': data_pwd,
            'status': True
        }
        return res

    def delete_base_backup(self, get):
        """
        @删除备份文件
        """

        name = ''
        id = get.id
        where = "id=?"
        filename = public.M('backup').where(where, (id,)).getField('filename')
        if os.path.exists(filename): os.remove(filename)

        # if filename == 'qiniu':
        #     name = public.M('backup').where(where, (id,)).getField('name')
        #
        #     public.ExecShell(public.get_run_python("[PYTHON] " + public.GetConfigValue('setup_path') + '/panel/script/backup_qiniu.py delete_file ' + name))
        public.M('backup').where(where, (id,)).delete()
        public.WriteLog("TYPE_DATABASE", 'DATABASE_BACKUP_DEL_SUCCESS', (name, filename))
        return public.return_message(0, 0, 'DEL_SUCCESS')

    # 检查是否在回收站
    def check_recyclebin(self, name):
        try:
            for n in os.listdir('{}/Recycle_bin'.format(public.get_setup_path())):
                if n.find('BTDB_' + name + '_t_') != -1: return True
            return False
        except:
            return False

    # map to list
    def map_to_list(self, map_obj):
        try:
            if type(map_obj) != list and type(map_obj) != str: map_obj = list(map_obj)
            return map_obj
        except:
            return []

    # ******************************************** 远程数据库 ******************************************/

    def check_cloud_args(self, get, nlist=[]):
        """
        验证参数是否合法
        @get param
        @args 参数列表
        """
        for key in nlist:
            if not key in get:
                return public.return_message(-1, 0, public.lang("Parameter passing error, missing parameter {}!", key))
        return public.return_message(0, 0, "success")

    def check_cloud_database(self, args):
        '''
        @检查远程数据库是否存在
        @conn_config param
        '''
        p = self.get_databaseModel()

        get = public.dict_obj()
        get['data'] = args
        get['mod_name'] = args['type']
        get['def_name'] = 'check_cloud_database_status'
        return p.model(get)

    def AddBaseCloudServer(self, get):
        """
        @name 添加远程服务器
        @author hwliang<2021-01-10>
        @param db_host<string> 服务器地址
        @param db_port<port> 数据库端口
        @param db_user<string> 用户名
        @param db_password<string> 数据库密码
        @param db_ps<string> 数据库备注
        @param type<string> 数据库类型，mysql/sqlserver/sqlite
        @return dict
        """
        arrs = ['db_host', 'db_port', 'db_user', 'db_password', 'db_ps', 'type']
        if get.type == 'redis':
            arrs = ['db_host', 'db_port', 'db_password', 'db_ps', 'type']
        cRet = self.check_cloud_args(get, arrs)
        if isinstance(cRet, dict):
            return cRet

        get['db_name'] = None
        res = self.check_cloud_database(get)
        if isinstance(res, dict):
            return res

        if public.M('database_servers').where('db_host=? AND db_port=?', (get['db_host'], get['db_port'])).count():
            return public.return_message(-1, 0, 'The specified server already exists: [{}:{}]'.format(get['db_host'],
                                                                                                      get['db_port']))
        get['db_port'] = int(get['db_port'])
        pdata = {
            'db_host': get['db_host'],
            'db_port': int(get['db_port']),
            'db_user': get['db_user'],
            'db_password': get['db_password'],
            'db_type': get['type'],
            'ps': public.xssencode2(get['db_ps'].strip()),
            'addtime': int(time.time())
        }
        result = public.M("database_servers").insert(pdata)

        if isinstance(result, int):
            public.WriteLog('Database manager', 'Add remote MySQL server[{}:{}]'.format(get['db_host'], get['db_port']))
            return public.return_message(0, 0, public.lang("Added successfully!"))
        return public.return_message(0, 0, public.lang("Add failed： {}", result))

    def GetBaseCloudServer(self, get):
        '''
            @name 获取远程服务器列表
            @author hwliang<2021-01-10>
            @return list
        '''

        # 解决get外多一层data
        if not get.get('type', None) and get.get('data', None):
            get['type'] = get['data'].get('type', '')
        where = '1=1'
        if 'type' in get: where = "db_type = '{}'".format(get['type'])

        data = public.M('database_servers').where(where, ()).select()

        if not isinstance(data, list): data = []

        if get['type'] == 'mysql':
            bt_mysql_bin = public.get_mysql_info()['path'] + '/bin/mysql.exe'
            if os.path.exists(bt_mysql_bin):
                data.insert(0, {'id': 0, 'db_host': '127.0.0.1', 'db_port': 3306, 'db_user': 'root', 'db_password': '',
                                'ps': 'local server', 'addtime': 0, 'db_type': 'mysql'})
        elif get['type'] == 'sqlserver':
            pass
        elif get['type'] == 'mongodb':
            if os.path.exists('/www/server/mongodb/bin'):
                data.insert(0, {'id': 0, 'db_host': '127.0.0.1', 'db_port': 27017, 'db_user': 'root', 'db_password': '',
                                'ps': 'local server', 'addtime': 0, 'db_type': 'mongodb'})
        elif get['type'] == 'redis':
            if os.path.exists('/www/server/redis'):
                data.insert(0, {'id': 0, 'db_host': '127.0.0.1', 'db_port': 6379, 'db_user': 'root', 'db_password': '',
                                'ps': 'local server', 'addtime': 0, 'db_type': 'redis'})
        elif get['type'] == 'pgsql':
            if os.path.exists('/www/server/pgsql'):
                data.insert(0,
                            {'id': 0, 'db_host': '127.0.0.1', 'db_port': 5432, 'db_user': 'postgres', 'db_password': '',
                             'ps': 'local server', 'addtime': 0, 'db_type': 'pgsql'})
        return data

    def RemoveBaseCloudServer(self, get):
        '''
            @name 删除远程服务器
            @author hwliang<2021-01-10>
            @param id<int> 远程服务器ID
            @return dict
        '''

        id = int(get.id)
        if not id:
            return public.return_message(-1, 0, public.lang("Parameter passed error, please try again!"))
        db_find = public.M('database_servers').where('id=?', (id,)).find()
        if not db_find:
            return public.return_message(-1, 0, public.lang("The specified remote server does not exist!"))
        public.M('databases').where('sid=?', id).delete()
        result = public.M('database_servers').where('id=?', id).delete()
        if isinstance(result, int):
            public.WriteLog('Database manager',
                            'Delete remote MySQL server [{}:{}]'.format(db_find['db_host'], int(db_find['db_port'])))
            return public.return_message(0, 0, public.lang("Successfully deleted!"))
        return public.return_message(0, 0, public.lang("Successfully deleted： {}", result))

    def ModifyBaseCloudServer(self, get):
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

        arrs = ['db_host', 'db_port', 'db_user', 'db_password', 'db_ps', 'type']
        if get.type == 'redis':
            arrs = ['db_host', 'db_port', 'db_password', 'db_ps', 'type']

        cRet = self.check_cloud_args(get, arrs)
        if isinstance(cRet, dict):
            return cRet

        get['db_name'] = None
        id = int(get.id)
        get['db_port'] = int(get['db_port'])
        db_find = public.M('database_servers').where('id=?', (id,)).find()
        if not db_find:
            return public.return_message(-1, 0, public.lang("The specified remote server does not exist!"))
        _modify = False
        if db_find['db_host'] != get['db_host'] or db_find['db_port'] != get['db_port']:
            _modify = True
            if public.M('database_servers').where('db_host=? AND db_port=?', (get['db_host'], get['db_port'])).count():
                return public.return_message(-1, 0,
                                             'The specified server already exists: [{}:{}]'.format(get['db_host'],
                                                                                                   get['db_port']))
        if db_find['db_user'] != get['db_user'] or db_find['db_password'] != get['db_password']:
            _modify = True
        _modify = True

        if _modify:
            res = self.check_cloud_database(get)
            if isinstance(res, dict): return res
        pdata = {
            'db_host': get['db_host'],
            'db_port': int(get['db_port']),
            'db_user': get['db_user'],
            'db_password': get['db_password'],
            'db_type': get['type'],
            'ps': public.xssencode2(get['db_ps'].strip())
        }

        result = public.M("database_servers").where('id=?', (id,)).update(pdata)
        if isinstance(result, int):
            public.WriteLog('Database manager',
                            'Modify the remote MySQL server[{}:{}]'.format(get['db_host'], get['db_port']))

            return public.return_message(0, 0, public.lang("Successfully modified!"))
        return public.return_message(-1, 0, public.lang("Fail to edit： {}", result))

    # 检测数据库执行错误
    def IsSqlError(self, mysqlMsg):

        if mysqlMsg:
            mysqlMsg = str(mysqlMsg)
            if "MySQLdb" in mysqlMsg:
                return public.return_message(-1, 0, public.lang("MySQLdb component is missing!"))
            if "2002," in mysqlMsg:
                return public.return_message(-1, 0, public.lang("ERROR to connect database"))
            if "2003," in mysqlMsg:
                return public.return_message(-1, 0, public.lang(
                    "Database connection timed out, please check if the configuration is correct."))
            if "1045," in mysqlMsg:
                return public.return_message(-1, 0, public.lang("MySQL password error."))
            if "1040," in mysqlMsg:
                return public.return_message(-1, 0, public.lang(
                    "Exceeded maximum number of connections, please try again later."))
            if "1130," in mysqlMsg:
                return public.return_message(-1, 0, public.lang(
                    "Database connection failed, please check whether the root user is authorized to access 127.0.0.1."))
            if "using password:" in mysqlMsg:
                return public.return_message(-1, 0, public.lang("Database password is incorrect!"))
            if "Connection refused" in mysqlMsg:
                return public.return_message(-1, 0, public.lang("ERROR to connect database"))
            if "1133" in mysqlMsg:
                return public.return_message(-1, 0, public.lang("Database user does NOT exist!"))
            if "2005_login_error" == mysqlMsg:
                return public.return_message(-1, 0, public.lang(
                    "The connection times out, please manually enable the TCP/IP function (Start Menu->SQL 2005->Configuration Tools->2005 Network Configuration->TCP/IP->Enable)"))
            if 'already exists' in mysqlMsg:
                return public.return_message(-1, 0, public.lang(
                    "The specified database already exists, please do not add it repeatedly."))
            if 'Cannot open backup device' in mysqlMsg:
                return public.return_message(-1, 0, public.lang(
                    "The operation failed, the remote database does not support the operation."))

            if '1142' in mysqlMsg:
                return public.return_message(-1, 0, public.lang("Insufficient permissions, please use root user."))

            if "DB-Lib error message 20018" in mysqlMsg:
                return public.return_message(-1, 0, public.lang("Create failed, SQL Server requires GUI support"))

        return None

    # ******************************************** 数据库公用方法 ******************************************/


if __name__ == "__main__":
    # get = {}
    # get['db_host'] = '192.168.1.37'
    # get['db_port'] = '3306'
    # get['db_user'] = 'root'

    # get['db_password'] = 'HLANEMJFRbPE7Ny2'
    # get['db_ps'] = '2'
    # get['type'] = 'mysql'
    # bt = databaseBase()
    # ret = bt.AddCloudServer(get)
    # print(ret)

    get = {}
    get['db_host'] = '192.168.66.73'
    get['db_port'] = '1433'
    get['db_user'] = 'sa'

    get['db_password'] = 'dPYi6Gt8GC7SL58C'
    get['db_ps'] = '2'
    get['type'] = 'sqlserver'
    bt = databaseBase()
    ret = bt.get_test(get)
    print(ret)
