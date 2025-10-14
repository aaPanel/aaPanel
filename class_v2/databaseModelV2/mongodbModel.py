# coding: utf-8
# -------------------------------------------------------------------
# aaPanel
# -------------------------------------------------------------------
# Copyright (c) 2015-2099 aaPanel(www.aapanel.com) All rights reserved.
# -------------------------------------------------------------------
# Author: hwliang <hwl@aapanel.com>
# -------------------------------------------------------------------
# 角色说明：
# read：允许用户读取指定数据库
# readWrite：允许用户读写指定数据库
# dbAdmin：允许用户在指定数据库中执行管理函数，如索引创建、删除，查看统计或访问system.profile
# userAdmin：允许用户向system.users集合写入，可以找指定数据库里创建、删除和管理用户
# clusterAdmin：只在admin数据库中可用，赋予用户所有分片和复制集相关函数的管理权限。
# readAnyDatabase：只在admin数据库中可用，赋予用户所有数据库的读权限
# readWriteAnyDatabase：只在admin数据库中可用，赋予用户所有数据库的读写权限
# userAdminAnyDatabase：只在admin数据库中可用，赋予用户所有数据库的userAdmin权限
# dbAdminAnyDatabase：只在admin数据库中可用，赋予用户所有数据库的dbAdmin权限。
# root：只在admin数据库中可用。超级账号，超级权限
# mg模型

import json
import os
import re
import time
from typing import Tuple, Any, Union

import yaml

import public
from databaseModelV2.base import databaseBase
from public.validate import Param

try:
    import pymongo
except:
    public.ExecShell("btpip install pymongo")
    import pymongo
try:
    from BTPanel import session
except:
    pass


class panelMongoDB:
    DEFUALT_DB = ["admin", "config", "local"]
    CONFIG_PATH = os.path.join(public.get_setup_path(), "mongodb/config.conf")

    def __init__(self):
        self.check_package()

        self.__CONN_KWARGS = {
            "host": "localhost",
            "port": 27017,
            "username": None,
            "password": None,
            "socketTimeoutMS": 3000,  # 套接字超时时间
            "connectTimeoutMS": 3000,  # 连接超时时间
            "serverSelectionTimeoutMS": 3000,  # 服务器选择超时时间
        }
        self.__DB_CONN = None

    # 检查python包是否存在
    @classmethod
    def check_package(cls):
        """
        @name检测依赖是否正常
        """
        try:
            import pymongo
        except:
            public.ExecShell("btpip install pymongo")
            try:
                import pymongo
            except:
                return False
        return True

    # 连接MongoDB数据库
    def connect(self) -> Tuple[bool, str]:
        auth = self.get_config_options("security", "authorization", "disabled") == "enabled"
        is_localhost = self.__CONN_KWARGS["host"] in ["localhost", "127.0.0.1"]
        # 本地连接自动补充 port username password
        if is_localhost:
            self.__CONN_KWARGS["port"] = self.get_config_options("net", "port", 27017)

            if auth:
                if self.__CONN_KWARGS.get("username") is None and auth:  # 自动补充 username
                    # noinspection PyTypedDict
                    self.__CONN_KWARGS["username"] = "root"
                if self.__CONN_KWARGS.get("password") is None:  # 自动补充 password
                    mongodb_root_path = os.path.join(public.get_panel_path(), "data/mongo.root")
                    if not os.path.exists(mongodb_root_path):
                        return False, public.lang("Local login password is empty")
                    self.__CONN_KWARGS["password"] = public.readFile(mongodb_root_path)

        if not isinstance(self.__CONN_KWARGS["port"], int):
            self.__CONN_KWARGS["port"] = int(self.__CONN_KWARGS["port"])

        try:
            self.__DB_CONN = pymongo.MongoClient(**self.__CONN_KWARGS)
            self.__DB_CONN.admin.command({"listDatabases": 1})
            return True, public.lang("normal")
        except Exception as err:
            err_msg = str(err)
            return False, public.lang(err_msg)

    # 设置连接参数
    def set_host(self, *args, **kwargs):
        """
        设置连接参数
        """
        # args 兼容老版本，后续新增禁止使用 args
        if len(args) >= 5:
            kwargs["host"] = args[0]
            kwargs["port"] = args[1]
            kwargs["username"] = args[2]
            kwargs["password"] = args[3]

        if kwargs.get("db_host") is not None:
            kwargs["host"] = kwargs.get("db_host")
        if kwargs.get("db_port") is not None:
            kwargs["port"] = kwargs.get("db_port")
        if kwargs.get("db_user") is not None:
            kwargs["username"] = kwargs.get("db_user")
        if kwargs.get("db_password") is not None:
            kwargs["password"] = kwargs.get("db_password")
        self.__CONN_KWARGS.update(kwargs)

        if not isinstance(self.__CONN_KWARGS["port"], int):
            self.__CONN_KWARGS["port"] = int(self.__CONN_KWARGS["port"])
        return self

    # 已弃用
    def get_db_obj(self, db_name="admin"):
        if self.__DB_CONN is None:
            status, err_msg = self.connect()
            if status is False:
                return err_msg

        return self.__DB_CONN[db_name]

    # 新方法
    def get_db_obj_new(self, db_name="admin") -> Tuple[bool, Any]:
        if self.__DB_CONN is None:
            status, err_msg = self.connect()
            if status is False:
                return status, "Failed to connect to database [{}:{}]! {}".format(self.__CONN_KWARGS["db_host"],
                                                                                  self.__CONN_KWARGS["db_port"],
                                                                                  err_msg)

        return True, self.__DB_CONN[db_name]

    # 获取配置文件
    @classmethod
    def get_config(cls, name: str = None, default=None) -> dict:
        config_data = public.readFile(cls.CONFIG_PATH)
        try:
            config = yaml.safe_load(config_data)
        except:
            config = {
                "systemLog": {
                    "destination": "file",
                    "logAppend": True,
                    "path": "/www/server/mongodb/log/config.log"
                },
                "storage": {
                    "dbPath": "/www/server/mongodb/data",
                    "directoryPerDB": True,
                    "journal": {
                        "enabled": True
                    }
                },
                "processManagement": {
                    "fork": True,
                    "pidFilePath": "/www/server/mongodb/log/configsvr.pid"
                },
                "net": {
                    "port": 27017,
                    "bindIp": "0.0.0.0"
                },
                "security": {
                    "authorization": "enabled",
                    "javascriptEnabled": False
                }
            }
        if name is not None:
            config.get(name, default)
        return config

    # 获取未注释的配置文件参数
    @classmethod
    def get_config_options(cls, key: str, name: str, default=None):
        config = cls.get_config()

        config_info = config.get(key)
        if config_info is None:
            return default
        return config_info.get(name, default)

    # 获取配置项
    @classmethod
    def get_options(cls, *args, **kwargs):
        config_info = {
            "port": 27017,
            "bind_ip": "127.0.0.1",
            "logpath": "",
            "dbpath": "",
            "authorization": "disabled"
        }
        if not os.path.exists(cls.CONFIG_PATH):
            return config_info

        conf = public.readFile(cls.CONFIG_PATH)

        for opt in config_info.keys():
            tmp = re.findall(opt + r":\s+(.+)", conf)
            if not tmp: continue
            config_info[opt] = tmp[0]

        # public.writeFile("/www/server/1.txt",json.dumps(data))
        return config_info

    # 重启 mongodb 服务
    @classmethod
    def restart_localhost_services(cls):
        """
        @重启服务
        """
        public.ExecShell('/etc/init.d/mongodb restart')

    @classmethod
    def set_auth_open(cls, status):
        """
        @设置数据库密码访问开关
        @状态 status:1 开启，2：关闭
        """

        conf = public.readFile(cls.CONFIG_PATH)
        if conf:
            if status:
                conf = re.sub(r'authorization\s*:\s*disabled', 'authorization: enabled', conf)
            else:
                conf = re.sub(r'authorization\s*:\s*enabled', 'authorization: disabled', conf)

        public.writeFile(cls.CONFIG_PATH, conf)
        cls.restart_localhost_services()
        return True

    @classmethod
    def get_auth_status(cls) -> bool:
        """获取认证开关状态"""
        return cls.get_config_options("security", "authorization", "disabled") == "enabled"

    @classmethod
    def get_root_pwd(cls) -> str:
        """获取root"""
        mongodb_root_path = os.path.join(public.get_panel_path(), "data/mongo.root")
        if not os.path.exists(mongodb_root_path):
            return ""
        pwd = public.readFile(mongodb_root_path)
        if not pwd:
            return ""
        return pwd.strip()


class main(databaseBase):
    _DB_BACKUP_DIR = os.path.join(public.M("config").where("id=?", (1,)).getField("backup_path"), "database")
    _MONGODB_BACKUP_DIR = os.path.join(_DB_BACKUP_DIR, "mongodb")
    _MONGODBDUMP_BIN = os.path.join(public.get_setup_path(), "mongodb/bin/mongodump")
    _MONGOEXPORT_BIN = os.path.join(public.get_setup_path(), "mongodb/bin/mongoexport")
    _MONGORESTORE_BIN = os.path.join(public.get_setup_path(), "mongodb/bin/mongorestore")
    _MONGOIMPORT_BIN = os.path.join(public.get_setup_path(), "mongodb/bin/mongoimport")

    _MONGO_ROLE_DICT = {
        # 数据库用户角色
        "read": "read",
        "readWrite": "readWrite",
        # 数据库管理角色
        # "dbAdmin": "数据库管理员",
        "dbOwner": "dbOwner",
        "userAdmin": "userAdmin",
        # 集群管理角色
        # "clusterAdmin": "集群管理员",
        # "clusterManager": "集群管理器",
        # "clusterMonitor": "集群监视器",
        # "hostManager": "主机管理员",
        # 备份和恢复角色
        # "backup": "备份数据",
        # "restore": "还原数据",
        # 所有数据库角色
        # "readAnyDatabase": "任意数据库读取",
        # "readWriteAnyDatabase": "任意数据库读取和写入",
        # "userAdminAnyDatabase": "任意数据库用户管理员",
        # "dbAdminAnyDatabase": "任意数据库管理员",
        # 超级用户角色
        # "root": "超级管理员",
        # 内部角色
        # "__queryableBackup": "可查询备份",
        # "__system": "系统角色",
        # "enableSharding": "启用分片",
    }

    def __init__(self):
        if not os.path.exists(self._MONGODB_BACKUP_DIR):
            os.makedirs(self._MONGODB_BACKUP_DIR, exist_ok=True)

    def get_list(self, get):
        """
        @获取数据库列表
        @sql_type = sqlserver
        """
        # 校验参数
        try:
            get.validate([
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

        rdata = self.get_base_list(get, sql_type="mongodb")
        return public.success_v2(rdata)

    def GetCloudServer(self, get):
        """
            @name 获取远程服务器列表
            @author hwliang<2021-01-10>
            @return list
        """
        where = '1=1'
        if 'type' in get:
            where = "db_type = '{}'".format(get['type'])

        data = public.M('database_servers').where(where, ()).select()

        if not isinstance(data, list):
            data = []

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
        return public.success_v2(data)

    def AddCloudServer(self, get):
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

        for key in arrs:
            if key not in get:
                return public.fail_v2(public.lang('Parameter passing error, missing parameter {}!'.format(key)))

        get['db_name'] = None

        mongodb_obj = panelMongoDB().set_host(
            host=get.get("db_host"),
            port=get.get("db_port"),
            username=get.get("db_user"),
            password=get.get("db_password")
        )
        status, err_msg = mongodb_obj.connect()
        if status is False:
            return public.fail_v2(public.lang("Failed to connect to the database!"))

        if public.M('database_servers').where('db_host=? AND db_port=?', (get['db_host'], get['db_port'])).count():
            return public.fail_v2(
                public.lang('Specifies that the server already exists: [{}:{}]'.format(get['db_host'], get['db_port'])))
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
            public.WriteLog('Database management',
                            'Adding a Remote MongoDB Server[{}:{}]'.format(get['db_host'], get['db_port']))
            return public.success_v2(public.lang('Add successfully!'))
        return public.fail_v2(public.lang('Add Failure： {}'.format(result)))

    def RemoveCloudServer(self, get):
        """
        @删除远程数据库
        """
        id = int(get.id)
        if not id:
            return public.fail_v2(public.lang('Parameter passing error, please try again!'))
        db_find = public.M("database_servers").where("id=? AND LOWER(db_type)=LOWER('mongodb')", (id,)).find()
        if not db_find:
            return public.fail_v2(public.lang('The specified remote server does not exist!'))
        public.M('databases').where('sid=?', id).delete()
        result = public.M('database_servers').where("id=? AND LOWER(db_type)=LOWER('mongodb')", id).delete()
        if isinstance(result, int):
            public.WriteLog(
                'Database management',
                'Removing a Remote MonogoDB Server[{}:{}]'.format(db_find['db_host'], int(db_find['db_port']))
            )
            return public.success_v2(public.lang('Deleted successfully!'))
        return public.fail_v2(public.lang('Failed to delete： {}'.format(result)))

    def ModifyCloudServer(self, get):
        """
            @name 修改远程服务器
            @author hwliang<2021-01-10>
            @param id<int> 远程服务器ID
            @param db_host<string> 服务器地址
            @param db_port<port> 数据库端口
            @param db_user<string> 用户名
            @param db_password<string> 数据库密码
            @param db_ps<string> 数据库备注
            @return dict
        """
        arrs = ['db_host', 'db_port', 'db_user', 'db_password', 'db_ps', 'type']
        if get.type == 'redis': arrs = ['db_host', 'db_port', 'db_password', 'db_ps', 'type']

        for key in arrs:
            if key not in get:
                return public.returnMsg(False, 'Parameter passing error, missing parameter{}!'.format(key))

        id = int(get.id)
        get['db_port'] = int(get['db_port'])
        db_find = public.M('database_servers').where('id=?', (id,)).find()
        if not db_find: return public.returnMsg(False, 'Specifies that the remote server does not exist!')
        _modify = False
        if db_find['db_host'] != get['db_host'] or db_find['db_port'] != get['db_port']:
            _modify = True
            if public.M('database_servers').where('db_host=? AND db_port=?', (get['db_host'], get['db_port'])).count():
                return public.returnMsg(False,
                                        'Specifies that the server already exists: [{}:{}]'.format(get['db_host'],
                                                                                                   get['db_port']))

        if db_find['db_user'] != get['db_user'] or db_find['db_password'] != get['db_password']:
            _modify = True
        _modify = True

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
            public.WriteLog(
                'Database management',
                'Modifying a Remote MySQL Server[{}:{}]'.format(get['db_host'], get['db_port'])
            )
            return public.returnMsg(True, 'Modified successfully!')
        return public.returnMsg(False, 'Modification Failure： {}'.format(result))

    def set_auth_status(self, get):
        """
        @设置密码认证状态
        @status int 0：关闭，1：开启
        """
        if not public.process_exists("mongod"):
            return public.return_message(-1, 0, public.lang("Mongodb service has not been started yet!"))

        status = int(get.status)
        path = '{}/data/mongo.root'.format(public.get_panel_path())
        if status:
            if hasattr(get, 'password'):
                password = get['password'].strip()
                if not password or not re.search(r"^[\w@.]+$", password):
                    return public.return_message(-1, 0, public.lang(
                        "Database password cannot be empty or have special characters!"))

                if re.search(r'[\u4e00-\u9fa5]', password):
                    return public.return_message(-1, 0, public.lang(
                        "Database password cannot be Chinese, please change the name!"))
            else:
                password = public.GetRandomString(16)
            panelMongoDB.set_auth_open(False)

            status, mongodb_obj = self.get_obj_by_sid(0)
            if status is False:
                return public.fail_v2(mongodb_obj)

            status, db_obj = mongodb_obj.get_db_obj_new("admin")
            if status is False:
                return public.fail_v2(db_obj)
            try:
                db_obj.command("dropUser", "root")
            except:
                pass

            db_obj.command("createUser", "root", pwd=password, roles=[
                {'role': 'root', 'db': 'admin'},
                {'role': 'clusterAdmin', 'db': 'admin'},
                {'role': 'readAnyDatabase', 'db': 'admin'},
                {'role': 'readWriteAnyDatabase', 'db': 'admin'},
                {'role': 'userAdminAnyDatabase', 'db': 'admin'},
                {'role': 'dbAdminAnyDatabase', 'db': 'admin'},
                {'role': 'userAdmin', 'db': 'admin'},
                {'role': 'dbAdmin', 'db': 'admin'}
            ])
            panelMongoDB.set_auth_open(True)

            public.writeFile(path, password)
        else:
            if os.path.exists(path): os.remove(path)
            panelMongoDB.set_auth_open(False)

        return public.return_message(0, 0, public.lang("Setup successfully!"))

    def get_obj_by_sid(self, sid=0, conn_config=None) -> Tuple[bool, Union[str, panelMongoDB]]:
        """
        @取mssql数据库对像 By sid
        @sid 数据库分类，0：本地
        """
        if type(sid) == str:
            try:
                sid = int(sid)
            except:
                sid = 0

        if sid:
            if not conn_config: conn_config = public.M('database_servers').where(
                "id=? AND LOWER(db_type)=LOWER('mongodb')", sid
            ).find()
            mongodb_obj = panelMongoDB().set_host(
                host=conn_config["db_host"],
                port=conn_config["db_port"],
                username=conn_config["db_user"],
                password=conn_config["db_password"]
            )
            status, err_msg = mongodb_obj.connect()
            if status is False:
                return status, public.lang("Failed to connect to database [{}:{}].".format(conn_config["db_host"],
                                                                                           int(conn_config["db_port"])))
            return status, mongodb_obj
        else:
            mongodb_obj = panelMongoDB()
            status, err_msg = mongodb_obj.connect()
            if status is False:
                return status, public.lang("Connecting to database [localhost:27017] failed!{}".format(err_msg))
            return status, mongodb_obj

    def AddDatabase(self, get):
        """
        @添加数据库
        """
        # 校验参数
        try:
            get.validate([
                Param('sid').Require().Integer(),
                Param('name').Require().String(),
            ], [
                public.validate.trim_filter(),
            ])
        except Exception as ex:
            public.print_log("error info: {}".format(ex))
            return public.return_message(-1, 0, str(ex))
        sid = int(get.sid)
        if not int(get.sid) and not public.process_exists("mongod"):
            return public.fail_v2(public.lang("Mongodb service is not turned on yet!"))
        dtype = 'MongoDB'
        # username = ''
        password = ''
        auth_status = panelMongoDB.get_config_options("security", "authorization",
                                                      "disabled") == "enabled"  # auth为true时如果__DB_USER为空则将它赋值为 root，用于开启本地认证后数据库用户为空的情况
        data_name = get.name.strip()
        if not data_name:
            return public.fail_v2(False, "The database name cannot be empty!")
        if auth_status:
            res = self.add_base_database(get, dtype)
            if not res['status']:
                return public.fail_v2(res.get("msg"))
            data_name = res['data_name']
            username = res['username']
            password = res['data_pwd']
        else:
            username = data_name
        # 检查数据库名称是否含有非法字符
        if any(char in data_name for char in '/\\. "$*<>:|?'):
            return public.fail_v2(
                public.lang("The database name cannot contain the following characters. /\\. \"$*<>:|?"))
        if ' ' in data_name:
            return public.fail_v2(public.lang('The database name contains spaces and cannot be added properly!'))

        sql = public.M('databases')
        if sql.where(
                "(username=?) AND LOWER(type)=LOWER('MongoDB')", (username,)
        ).count():
            return public.fail_v2(public.lang('Database user already exists, please use another database name!'))

        status, mongodb_obj = self.get_obj_by_sid(get.sid)
        if status is False:
            return public.fail_v2(mongodb_obj)
        status, db_obj = mongodb_obj.get_db_obj_new(data_name)
        if status is False:
            return public.fail_v2(db_obj)

        if not hasattr(get, 'ps'):
            get['ps'] = public.getMsg('INPUT_PS')
        addTime = time.strftime('%Y-%m-%d %X', time.localtime())

        pid = 0
        if hasattr(get, 'pid'): pid = get.pid

        if hasattr(get, 'contact'):
            site = public.M('sites').where("id=?", (get.contact,)).field('id,name').find()
            if site:
                pid = int(get.contact)
                get['ps'] = site['name']

        db_type = 0
        if sid:
            db_type = 2

        db_obj.chat.insert_one({})
        if auth_status:
            db_obj.command(
                "createUser",
                username,
                pwd=password,
                roles=[{'role': 'dbOwner', 'db': data_name}, {'role': 'userAdmin', 'db': data_name}]
            )
        public.set_module_logs('linux_mongodb', 'AddDatabase', 1)

        # 添加入SQLITE
        public.M('databases').add(
            'pid,sid,db_type,name,username,password,accept,ps,addtime,type',
            (pid, sid, db_type, data_name, username, password, '127.0.0.1', get['ps'], addTime, dtype)
        )
        public.WriteLog("TYPE_DATABASE", 'DATABASE_ADD_SUCCESS', (data_name,))
        return public.success_v2(public.lang('ADD_SUCCESS'))

    def DeleteDatabase(self, get):
        """
        @删除数据库
        """
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
        id = get['id']
        find = public.M('databases').where(
            "id=? AND LOWER(type)=LOWER('MongoDB')", (id,)
        ).field('id,pid,name,username,password,type,accept,ps,addtime,sid,db_type').find()
        if not find:
            return public.fail_v2(public.lang('database does not exist.'))

        if not public.process_exists("mongod") and not int(find['sid']):
            return public.fail_v2(public.lang("Mongodb service is not yet turned on!"))
        name = get['name']
        username = find['username']

        if name == "admin":
            return public.fail_v2(
                public.lang('Deletion of the admin name database is prohibited due to Mongodb restrictions!'))

        status, mongodb_obj = self.get_obj_by_sid(find['sid'])
        if status is False:
            return public.fail_v2(mongodb_obj)
        status, db_obj = mongodb_obj.get_db_obj_new(name)
        if status is False:
            return public.fail_v2(db_obj)
        try:
            db_obj.command("dropUser", username)
        except:
            pass

        db_obj.command('dropDatabase')
        # 删除SQLITE
        public.M('databases').where("id=? AND LOWER(type)=LOWER('MongoDB')", (id,)).delete()
        public.WriteLog("TYPE_DATABASE", 'DATABASE_DEL_SUCCESS', (name,))
        return public.return_message(0, 0, public.lang("Successfully deleted!"))

    def get_info_by_db_id(self, db_id):
        """
        @获取数据库连接详情
        @db_id 数据库id
        """
        find = public.M('databases').where("id=? AND LOWER(type)=LOWER('mongodb')", db_id).find()
        if not find: return False

        if find["db_type"] == 1:
            # 远程数据库
            conn_config = json.loads(find["conn_config"])
            db_host = conn_config["db_host"]
            db_port = conn_config["db_port"]
        elif find["db_type"] == 2:
            conn_config = public.M("database_servers").where("id=? AND LOWER(db_type)=LOWER('mongodb')",
                                                             find["sid"]).find()
            db_host = conn_config["db_host"]
            db_port = conn_config["db_port"]
        else:  # 本地数据库
            db_host = '127.0.0.1'
            db_port = panelMongoDB.get_config_options("net", "port", 27017)
        data = {
            'db_name': find["name"],
            'db_host': db_host,
            'db_port': int(db_port),
            'db_user': find['username'],
            'db_password': find['password'],
        }
        return data

    # 备份数据库
    def ToBackup(self, get):
        """
        备份数据库
        """
        if not os.path.exists(self._MONGODBDUMP_BIN):
            return public.fail_v2(
                public.lang("Lack of backup tools, please install MongoDB via Software Manager first!"))
        if not os.path.exists(self._MONGOEXPORT_BIN):
            return public.fail_v2(
                public.lang("Lack of backup tools, please install MongoDB via Software Manager first!"))

        if not hasattr(get, "id"):
            return public.fail_v2(public.lang("Missing parameter! id"))
        db_id = get.id
        file_type = getattr(get, "file_type", "bson")
        collection_list = getattr(get, "collection_list", [])
        field_list = getattr(get, "field_list", [])

        db_find = public.M("databases").where("id=? AND LOWER(type)=LOWER('mongodb')", (db_id,)).find()
        if not db_find:
            return public.fail_v2(public.lang("The database does not exist! {db_id}".format(db_id=db_id)))
        if not public.process_exists("mongod") and not int(db_find["sid"]):
            return public.fail_v2(public.lang("Mongodb service is not turned on yet!"))

        if file_type not in ["bson", "json", "csv"]:
            return public.fail_v2(public.lang("The bson json csv format is currently supported!"))

        if file_type == "csv" and len(field_list) == 0:
            return public.fail_v2(public.lang("You need to specify the export fields when exporting to csv format!"))

        db_name = db_find["name"]
        db_host = "127.0.0.1"
        db_user = db_find["username"]
        db_password = db_find["password"]
        conn_data = {}
        if db_find["db_type"] == 0:
            db_port = panelMongoDB.get_config_options("net", "port", 27017)
            auth_enabled = panelMongoDB.get_auth_status()
            if auth_enabled:
                if not db_password:
                    return public.fail_v2(
                        public.lang("Local login password is empty, please set the database password first!")
                    )
            else:
                db_password = None
        elif db_find["db_type"] == 1:
            auth_enabled = True
            if not db_password:
                return public.fail_v2(
                    public.lang("The database password is empty!Please set the database password first!"))
            # 远程数据库
            conn_config = json.loads(db_find["conn_config"])
            db_host = conn_config["db_host"]
            db_port = conn_config["db_port"]
            conn_data["host"] = conn_config["db_host"]
            conn_data["port"] = conn_config["db_port"]
            conn_data["username"] = conn_config["db_user"]
            conn_data["password"] = conn_config["db_password"]
        elif db_find["db_type"] == 2:
            auth_enabled = True
            if not db_password:
                return public.fail_v2(public.lang("MongoDB has enabled security authentication, "
                                                  "the database password cannot be empty, "
                                                  "please set the password and try again!"))
            conn_config = public.M("database_servers").where(
                "id=? AND LOWER(db_type)=LOWER('mongodb')",
                db_find["sid"]
            ).find()
            db_host = conn_config["db_host"]
            db_port = conn_config["db_port"]

            conn_data["host"] = conn_config["db_host"]
            conn_data["port"] = conn_config["db_port"]
            conn_data["username"] = conn_config["db_user"]
            conn_data["password"] = conn_config["db_password"]
        else:
            return public.fail_v2(public.lang("Unknown database type"))

        mongodb_obj = panelMongoDB().set_host(**conn_data)
        status, err_msg = mongodb_obj.connect()
        if status is False:
            return public.fail_v2(public.lang("Failed to connect to database [{}:{}].".format(db_host, int(db_port))))

        db_backup_dir = os.path.join(self._MONGODB_BACKUP_DIR, db_name)
        if not os.path.exists(db_backup_dir):
            os.makedirs(db_backup_dir)

        file_name = "{db_name}_{file_type}_{backup_time}_mongodb_data".format(
            db_name=db_name, file_type=file_type,
            backup_time=time.strftime("%Y-%m-%d_%H-%M-%S", time.localtime())
        )
        export_dir = os.path.join(db_backup_dir, file_name)

        mongodump_shell = "'{mongodump_bin}' --host='{db_host}' --port={db_port} --db='{db_name}' --out='{out}'".format(
            mongodump_bin=self._MONGODBDUMP_BIN,
            db_host=db_host,
            db_port=int(db_port),
            db_name=db_name,
            out=export_dir,
        )
        mongoexport_shell = "'{mongoexport_bin}' --host='{db_host}' --port={db_port} --db='{db_name}'".format(
            mongoexport_bin=self._MONGOEXPORT_BIN,
            db_host=db_host,
            db_port=int(db_port),
            db_name=db_name,
        )
        # 开启认证
        if auth_enabled:
            mongodump_shell += " --username='{db_user}' --password={db_password} --authenticationDatabase='{auth_db}'".format(
                db_user=db_user, db_password=public.shell_quote(str(db_password)), auth_db=db_name
            )
            mongoexport_shell += " --username='{db_user}' --password={db_password} --authenticationDatabase='{auth_db}'".format(
                db_user=db_user, db_password=public.shell_quote(str(db_password)), auth_db=db_name
            )
        backup_ps = "Manual Backup"
        if file_type == "bson":
            if len(collection_list) == 0:
                public.ExecShell(mongodump_shell)
            else:
                backup_ps += "-bson"
                for collection_name in collection_list:
                    shell = f"{mongodump_shell} --collection='{collection_name}'"
                    public.ExecShell(shell)
        else:  # 导出 json csv 格式
            backup_ps += "-json"
            fields = None
            if file_type == "csv":  # csv
                fields = "--fields='{}'".format(",".join(field_list))

            for collection_name in collection_list:
                file_path = os.path.join(export_dir,
                                         "{collection_name}.{file_type}".format(collection_name=collection_name,
                                                                                file_type=file_type))
                shell = "{mongoexport_shell} --collection='{collection}' --type='{type}' --out='{out}'".format(
                    mongoexport_shell=mongoexport_shell,
                    collection=collection_name,
                    type=file_type,
                    out=file_path,
                )
                if fields is not None:
                    shell += " --fields='{fields}'".format(fields=fields)
                public.ExecShell(shell)

        if not os.path.exists(export_dir):
            return public.fail_v2(public.lang("Database backup failed, export file does not exist!"))
        backup_path = "{export_dir}.zip".format(export_dir=export_dir)
        public.ExecShell("cd {backup_dir} && zip -m {backup_path} -r {file_name}".format(
            backup_dir=db_backup_dir, backup_path=backup_path, file_name=file_name)
        )
        if not os.path.exists(backup_path):
            public.ExecShell("rm -rf {}".format(export_dir))
            return public.fail_v2(public.lang("Backup failed!"))

        backup_size = os.path.getsize(backup_path)
        public.M("backup").add("type,name,pid,filename,size,addtime,ps", (
            1, os.path.basename(backup_path), db_id, backup_path, backup_size,
            time.strftime("%Y-%m-%d %X", time.localtime()), backup_ps))
        public.WriteLog("TYPE_DATABASE", "DATABASE_BACKUP_SUCCESS", (db_name,))
        if backup_size < 1:
            return public.success_v2(public.lang(
                "Backup executed successfully, backup file is smaller than 1b, please check backup integrity."
            ))
        else:
            return public.success_v2(public.lang("BACKUP_SUCCESS"))

    # 导入
    def InputSql(self, get):
        # 校验参数
        try:
            get.validate([
                Param('file').SafePath(),  # 文件路径
                Param('name').String(),
            ], [
                public.validate.trim_filter(),
            ])
        except Exception as ex:
            public.print_log("error info: {}".format(ex))
            return public.return_message(-1, 0, str(ex))

        if not os.path.exists(self._MONGORESTORE_BIN):
            return public.fail_v2(
                public.lang("Lack of backup tools, please install MongoDB via Software Manager first!"))
        if not os.path.exists(self._MONGOIMPORT_BIN):
            return public.fail_v2(
                public.lang("Lack of backup tools, please install MongoDB via Software Manager first!"))

        db_name = get.name
        file = get.file

        if not os.path.exists(file):
            return public.fail_v2(public.lang("Import path does not exist!"))
        if not os.path.isfile(file):
            return public.fail_v2(public.lang("Importing zip files is only supported!"))
        db_find = public.M("databases").where("name=? AND LOWER(type)=LOWER('MongoDB')", (db_name,)).find()
        if not db_find:
            return public.fail_v2(public.lang("Database does not exist!"))

        if not public.process_exists("mongod") and not int(db_find["sid"]):
            return public.fail_v2(public.lang("Mongodb service is not yet turned on!"))

        file_name = os.path.basename(file)
        ext_list = ['json', 'csv', 'tar.gz', 'zip']
        ext_tmp = file_name.split(".")
        file_ext = ".".join(ext_tmp[1:])
        ext_temp = [ext.lower() for ext in ext_list if ext.lower() in file_ext]
        if len(ext_temp) == 0:
            return public.fail_v2("Please choose json, csv, tar.gz, zip file formats!")

        input_dir = os.path.join(self._MONGODB_BACKUP_DIR, db_name, "input_tmp_{}".format(int(time.time() * 1000_000)))

        is_zip = False
        if "zip" in file_ext:
            if not os.path.isdir(input_dir): os.makedirs(input_dir)
            public.ExecShell("unzip -o '{file}' -d {input_dir}".format(file=file, input_dir=input_dir))
            is_zip = True
        elif "tar.gz" in file_ext:
            if not os.path.isdir(input_dir): os.makedirs(input_dir)
            public.ExecShell("tar zxf '{file}' -C {input_dir}".format(file=file, input_dir=input_dir))
            is_zip = True
        elif "gz" in file_ext:
            if not os.path.isdir(input_dir): os.makedirs(input_dir)
            temp_file = os.path.join(input_dir, file_name)
            public.ExecShell(
                "cp '{file}' '{temp_file}' && gunzip -q '{temp_file}'".format(file=file, temp_file=temp_file))
            is_zip = True

        input_path_list = []
        if is_zip is True:
            def get_input_path(input_dir: str, input_path_list: list):
                for name in os.listdir(input_dir):
                    path = os.path.join(input_dir, name)
                    if os.path.isfile(path) and (path.endswith(".json") or path.endswith(".csv")):
                        input_path_list.append(path)
                    elif os.path.isdir(path):
                        is_bson = False
                        for t_name in os.listdir(path):
                            t_path = os.path.join(path, t_name)
                            if os.path.isfile(t_path) and t_path.endswith(".bson"):
                                input_path_list.append(path)
                                is_bson = True
                                break
                        if is_bson is False:
                            get_input_path(path, input_path_list)

            get_input_path(input_dir, input_path_list)
        else:
            input_path_list.append(file)  # json,csv

        db_name = db_find["name"]

        db_host = "127.0.0.1"
        db_user = db_find["username"]
        db_password = db_find["password"]
        if db_find["db_type"] == 0:
            if panelMongoDB.get_config_options("security", "authorization", "disabled") == "enabled":
                if not db_password:
                    return public.fail_v2(public.lang("MongoDB has enabled security authentication, "
                                                      "the database password cannot be empty, please set the password and try again!"))
            else:
                db_password = None
            db_port = panelMongoDB.get_config_options("net", "port", 27017)
        elif db_find["db_type"] == 1:
            # 远程数据库
            conn_config = json.loads(db_find["conn_config"])
            db_host = conn_config["db_host"]
            db_port = conn_config["db_port"]
        elif db_find["db_type"] == 2:
            conn_config = public.M("database_servers").where("id=? AND LOWER(db_type)=LOWER('mongodb')",
                                                             db_find["sid"]).find()
            db_host = conn_config["db_host"]
            db_port = conn_config["db_port"]
        else:
            return public.fail_v2(public.lang("Unknown database type"))

        status, err_msg = panelMongoDB().connect()
        if status is False:
            return public.fail_v2(public.lang("Failed to connect to database [{}:{}].".format(db_host, int(db_port))))
        mongorestore_shell = "'{mongorestore}' --host='{host}' --port={port} --db='{db_name}' --drop ".format(
            mongorestore=self._MONGORESTORE_BIN,
            host=db_host,
            port=int(db_port),
            db_name=db_name,
        )
        mongoimport_shell = "'{mongoimport}' --host='{host}' --port={port} --db='{db_name}' --drop ".format(
            mongoimport=self._MONGOIMPORT_BIN,
            host=db_host,
            port=int(db_port),
            db_name=db_name,
        )
        if db_password is not None:  # 本地未开启安全认证
            mongorestore_shell += " --username='{db_user}' --password='{db_password}'".format(db_user=db_user,
                                                                                              db_password=db_password)
            mongoimport_shell += " --username='{db_user}' --password='{db_password}'".format(db_user=db_user,
                                                                                             db_password=db_password)

        for path in input_path_list:
            if os.path.isdir(path):  # bson
                public.ExecShell(
                    "{mongorestore_shell} '{path}'".format(mongorestore_shell=mongorestore_shell, path=path))
            elif os.path.isfile(path) and (path.endswith(".json") or path.endswith(".csv")):  # json/csv
                fields = None
                if path.endswith(".csv"):  # csv
                    fp = open(path, "r")
                    fields = fp.readline()
                    fp.close()
                file_name = os.path.basename(path)
                collection = file_name.split(".")[0]
                file_type = file_name.split(".")[-1]
                shell = "{mongoimport_shell} --collection='{collection}' --file='{file}' --type='{type}'".format(
                    mongoimport_shell=mongoimport_shell,
                    collection=collection,
                    file=path,
                    type=file_type,
                )
                if fields is not None:
                    shell += " --fields='{fields}'".format(fields=fields)
                public.ExecShell(shell)
        # 清理导入临时目录
        if is_zip is True:
            public.ExecShell("rm -rf {input_dir}".format(input_dir=input_dir))
        public.WriteLog("TYPE_DATABASE", 'Importing the database[{}]successes'.format(db_name))
        return public.success_v2(public.lang('DATABASE_INPUT_SUCCESS'))

    # 获取备份文件
    def GetBackup(self, get):
        p = getattr(get, "p", 1)
        limit = getattr(get, "limit", 10)
        return_js = getattr(get, "return_js", "")
        search = getattr(get, "search", None)

        if not str(p).isdigit():
            return public.fail_v2("Parameter error! p")
        if not str(limit).isdigit():
            return public.fail_v2("Parameter error! limit")

        p = int(p)
        limit = int(limit)

        ext_list = ['json', 'csv', 'tar.gz', 'zip']

        backup_list = []

        # 递归获取备份文件
        def get_dir_backup(backup_dir: str, backup_list: list, is_recursion: bool):
            for name in os.listdir(backup_dir):
                path = os.path.join(backup_dir, name)
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

        get_dir_backup(self._MONGODB_BACKUP_DIR, backup_list, True)
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
        return {"status": True, "msg": "OK", "data": backup_list, "page": page_info}

    def DelBackup(self, get):
        """
        @删除备份文件
        """
        self.delete_base_backup(get)

    # 同步数据库到服务器
    def SyncToDatabases(self, get):
        type = int(get['type'])
        n = 0
        sql = public.M('databases')
        if type == 0:
            data = sql.field('id,name,username,password,accept,type,sid,db_type').where("LOWER(type)=LOWER('MongoDB')",
                                                                                        ()).select()
            for value in data:
                if value['db_type'] in ['1', 1]:
                    continue  # 跳过远程数据库
                result = self.ToDataBase(value)
                if result.get("status") == 0 and result["message"].get("result") == 1:
                    n += 1
        else:
            import json
            data = json.loads(get.ids)
            for value in data:
                find = sql.where("id=?", (value,)).field('id,name,username,password,sid,db_type,accept,type').find()
                result = self.ToDataBase(find)
                if result.get("status") == 0 and result["message"].get("result") == 1:
                    n += 1
        if n == 1:
            return public.return_message(0, 0, public.lang("Synchronization succeeded"))
        elif n == 0:
            return public.return_message(-1, 0, public.lang("No synchronized database"))
        return public.return_message(0, 0, public.lang("Database sync success {}", n))

    # 添加到服务器
    def ToDataBase(self, find):
        if find['username'] == 'bt_default':
            return public.return_message(0, 0, 0)
        if len(find['password']) < 3:
            find['username'] = find['name']
            find['password'] = public.md5(str(time.time()) + find['name'])[0:10]
            public.M('databases').where("id=? AND LOWER(type)=LOWER('MongoDB')", (find['id'],)).save(
                'password,username', (find['password'], find['username']))

        try:
            sid = int(find['sid'])
        except:
            return public.return_message(-1, 0, public.lang("Database type sid needs int type!！"))
        if not public.process_exists("mongod") and not int(find['sid']):
            return public.return_message(-1, 0, public.lang("Mongodb service has not been started yet!！"))

        get = public.dict_obj()
        get.sid = sid
        auth_status = panelMongoDB.get_config_options("security", "authorization", "disabled") == "enabled"
        if auth_status:
            status, mongodb_obj = self.get_obj_by_sid(sid)
            if status is False:
                return public.returnMsg(False, mongodb_obj)
            status, db_obj = mongodb_obj.get_db_obj_new(find['name'])
            if status is False:
                return public.returnMsg(False, db_obj)
            try:
                db_obj.chat.insert_one({})
                db_obj.command("dropUser", find['username'])
            except:
                pass
            try:
                db_obj.command(
                    "createUser",
                    find['username'],
                    pwd=find['password'],
                    roles=[{'role': 'dbOwner', 'db': find['name']}, {'role': 'userAdmin', 'db': find['name']}]
                )
            except:
                pass
        return public.return_message(0, 0, 1)

    def SyncGetDatabases(self, get):
        """
        @从服务器获取数据库
        """
        n = 0
        # s = 0
        db_type = 0

        if public.process_exists("mongod") and get.sid is None:
            sid = 0
        else:
            sid = get.get('sid/d', 0)
            if sid: db_type = 2
            try:
                int(get.sid)
            except:
                return public.fail_v2(public.lang('The database type sid requires the int type!'))
            if not public.process_exists("mongod") and not int(get.sid):
                return public.fail_v2(public.lang("Mongodb service is not turned on yet!"))

        status, mongodb_obj = self.get_obj_by_sid(sid)
        if status is False:
            return public.fail_v2(mongodb_obj)
        status, db_obj = mongodb_obj.get_db_obj_new('admin')
        if status is False:
            return public.fail_v2(db_obj)

        data = db_obj.command({"listDatabases": 1})

        sql = public.M('databases')

        for item in data['databases']:
            dbname = item['name']
            if sql.where("name=? AND LOWER(type)=LOWER('MongoDB')", (dbname,)).count():
                continue
            if dbname in panelMongoDB.DEFUALT_DB:
                continue
            if sql.table('databases').add(
                    'name,username,password,accept,ps,addtime,type,sid,db_type',
                    (dbname, dbname, "", "", public.getMsg('INPUT_PS'), time.strftime('%Y-%m-%d %X', time.localtime()),
                     'MongoDB', sid, db_type)
            ):
                n += 1

        return public.success_v2(public.lang('DATABASE_GET_SUCCESS'))

    def ResDatabasePassword(self, get):
        """
        @修改用户密码
        """
        id = get['id']
        username = get['name'].strip()
        newpassword = public.trim(get['password'])
        try:
            if not newpassword:
                return public.fail_v2(
                    public.lang('Modification failed, database [' + username + ']password cannot be empty.'))
            if len(re.search(r"^[\w@.]+$", newpassword).groups()) > 0:
                return public.fail_v2(public.lang('The database password cannot be empty or have special characters.'))

            if re.search(r'[\u4e00-\u9fa5]', newpassword):
                return public.fail_v2(public.lang('Database password can not be Chinese, please change the name!'))
        except:
            return public.fail_v2(public.lang('The database password cannot be empty or have special characters.'))

        find = public.M('databases').where("id=? AND LOWER(type)=LOWER('MongoDB')", (id,)).field(
            'id,pid,name,username,password,type,accept,ps,addtime,sid').find()
        if not find:
            return public.fail_v2(public.lang('The modification failed, the specified database does not exist.'))

        get = public.dict_obj()
        get.sid = find['sid']
        try:
            int(find['sid'])
        except:
            return public.fail_v2(public.lang('The database type sid requires the int type!'))
        if not public.process_exists("mongod") and not int(find['sid']):
            return public.fail_v2("Mongodb service is not turned on yet!")
        auth_status = panelMongoDB.get_config_options("security", "authorization", "disabled") == "enabled"
        if auth_status:
            status, mongodb_obj = self.get_obj_by_sid(find['sid'])
            if status is False:
                return public.fail_v2(mongodb_obj)
            status, db_obj = mongodb_obj.get_db_obj_new(username)
            if status is False:
                return public.fail_v2(db_obj)
            try:
                db_obj.command("updateUser", username, pwd=newpassword)
            except:
                db_obj.command("createUser", username, pwd=newpassword, roles=[{'role': 'dbOwner', 'db': find['name']},
                                                                               {'role': 'userAdmin',
                                                                                'db': find['name']}])
        else:
            return public.fail_v2(
                public.lang('Modification failed, the database is not enabled for security authentication.'))

        # 修改SQLITE
        public.M('databases').where("id=? AND LOWER(type)=LOWER('MongoDB')", (id,)).setField('password', newpassword)

        public.WriteLog("TYPE_DATABASE", 'DATABASE_PASS_SUCCESS', (find['name'],))
        return public.success_v2(f"Successfully modifyied password for database [{find['name']}]!")

    def get_root_pwd(self, get):
        """
        @获取root密码
        """
        config = panelMongoDB.get_config()
        config_info = {
            "port": config["net"].get("port", 27017),
            "bind_ip": config["net"].get("bindIp", "127.0.0.1"),
            "logpath": config["systemLog"].get("path", ""),
            "dbpath": config["storage"].get("dbPath", ""),
            "authorization": config["security"].get("authorization", "disabled")
        }
        sa_path = '{}/data/mongo.root'.format(public.get_panel_path())
        if os.path.exists(sa_path):
            config_info['msg'] = public.readFile(sa_path)
        else:
            config_info['msg'] = ''
        config_info['root'] = config_info['msg']
        return public.return_message(0, 0, config_info)

    def get_database_size_by_id(self, get):
        """
        @获取数据库尺寸（批量删除验证）
        @get json/int 数据库id
        """
        # if not public.process_exists("mongod"):
        #     return public.returnMsg(False,"Mongodb服务还未开启！")
        total = 0
        db_id = get
        if not isinstance(get, int): db_id = get['db_id']

        find = public.M('databases').where("id=? AND LOWER(type)=LOWER('MongoDB')", db_id).find()
        try:
            int(find['sid'])
        except:
            return 0
        if not public.process_exists("mongod") and not int(find['sid']):
            return 0
        return public.return_message(0, 0, total)

    # todo 前端未使用新接口
    def check_del_data(self, args):
        """
        @删除数据库前置检测
        """
        return public.return_message(0, 0, self.check_base_del_data(args))

    def __new_password(self):
        """
        生成随机密码
        """
        import random
        import string
        # 生成随机密码
        password = "".join(random.sample(string.ascii_letters + string.digits, 16))
        return password

    # 数据库状态检测
    def CheckDatabaseStatus(self, get):
        """
        数据库状态检测
        """
        if not hasattr(get, "sid"):
            return public.fail_v2("Missing parameters! sid")
        if not str(get.sid).isdigit():
            return public.fail_v2("Parameter error! sid")
        sid = int(get.sid)
        mongodb_obj = panelMongoDB()
        if sid == 0:
            db_status, err_msg = mongodb_obj.connect()
        else:
            conn_config = public.M('database_servers').where("id=? AND LOWER(db_type)=LOWER('mongodb')", sid).find()
            if not conn_config:
                db_status = False
                err_msg = public.lang("Remote database information does not exist!")
            else:
                mongodb_obj.set_host(host=conn_config.get("db_host"), port=conn_config.get("db_port"),
                                     username=conn_config.get("db_user"), password=conn_config.get("db_password"))
                db_status, err_msg = mongodb_obj.connect()

        return {"status": True, "msg": "normal" if db_status is True else "exceptions", "db_status": db_status,
                "err_msg": err_msg}

    def check_cloud_database_status(self, conn_config):
        """
        @检测远程数据库是否连接
        @conn_config 远程数据库配置，包含host port pwd等信息
        旧方法，添加数据库时调用
        """
        try:
            mongodb_obj = panelMongoDB().set_host(host=conn_config.get("db_host"), port=conn_config.get("db_port"),
                                                  username=conn_config.get("db_user"),
                                                  password=conn_config.get("db_password"))
            status, err_msg = mongodb_obj.connect()
            return status
        except:
            return public.fail_v2("Remote database connection failed!")

    # 获取数据库集合
    def GetInfo(self, get):
        """
       获取数据库集合
       """
        db_name = get.db_name

        db_find = public.M("databases").where("name=? AND LOWER(type)=LOWER('MongoDB')", (db_name,)).find()
        if not db_find:
            return public.fail_v2("The database does not exist!")

        if not public.process_exists("mongod") and not int(db_find["sid"]):
            return public.fail_v2("Mongodb service is not turned on yet!")

        status, mongodb_obj = self.get_obj_by_sid(db_find["sid"])
        if status is False:
            return public.fail_v2(mongodb_obj)
        status, db_obj = mongodb_obj.get_db_obj_new(db_name)
        if status is False:
            return public.fail_v2(db_obj)

        result = db_obj.command("dbStats")

        result["collection_list"] = []
        for collection_name in db_obj.list_collection_names():
            collection = db_obj.command("collStats", collection_name)
            data = {
                "collection_name": collection_name,
                "count": collection.get("count"),  # 文档数
                "size": collection.get("size"),  # 内存中的大小
                "avg_obj_size": collection.get("avgObjSize"),  # 对象平均大小
                "storage_size": collection.get("storageSize"),  # 存储大小
                "capped": collection.get("capped"),
                "nindexes": collection.get("nindexes"),  # 索引数
                "total_index_size": collection.get("totalIndexSize"),  # 索引大小
            }
            result["collection_list"].append(data)
        return {"status": True, "msg": "ok", "data": result}

    def GetRole(self, get):
        """
        @获取所有角色权限
        """
        status, mongodb_obj = self.get_obj_by_sid(0)
        if status is False:
            return public.fail_v2(mongodb_obj)

        status, db_obj = mongodb_obj.get_db_obj_new("admin")
        if status is False:
            return public.fail_v2(db_obj)

        # 获取所有角色
        role_data = db_obj.command('rolesInfo', showBuiltinRoles=True)
        result = []
        for role in role_data["roles"]:
            if self._MONGO_ROLE_DICT.get(role["role"]) is not None:
                role["name"] = self._MONGO_ROLE_DICT.get(role["role"])
                result.append(role)
        return {"status": True, "msg": "ok", "data": result}

    def GetDatabaseAccess(self, get):
        """
        @获取用户权限
        @user_name: 用户名
        """
        user_name = get.get("user_name")
        if user_name is None:
            return public.fail_v2('Parameter error!Missing database user name!')

        db_find = public.M("databases").where("username=? AND LOWER(type)=LOWER('MongoDB')", (user_name,)).find()
        if not db_find:
            return public.fail_v2("The database does not exist!")

        if not public.process_exists("mongod") and not int(db_find["sid"]):
            return public.fail_v2("Mongodb service is not turned on yet!")

        status, mongodb_obj = self.get_obj_by_sid(db_find["sid"])
        if status is False:
            return public.fail_v2(mongodb_obj)
        status, db_obj = mongodb_obj.get_db_obj_new(user_name)
        if status is False:
            return public.fail_v2(db_obj)
        # 查看用户信息
        user_data = db_obj.command('usersInfo', user_name)
        # 打印用户的权限信息
        result = {
            "user": user_name,
            "db": user_name,
            "roles": [],
        }
        if user_data:
            if len(user_data["users"]) != 0:
                user = user_data["users"][0]
                result["user"] = user.get("user", user_name)
                result["db"] = user.get("db", user_name)
                result["roles"] = [info.get("role") for info in user.get("roles", []) if info.get("role")]

        return {"status": True, "msg": "ok", "data": result}

    def SetDatabaseAccess(self, get):
        """
        @设置用户权限
        @remote_ip: 远程连接地址
        """
        user_name = get.get("user_name", None)
        db_permission = get.get("db_permission", None)
        if user_name is None:
            return public.fail_v2('Parameter error!Missing database username!')
        if db_permission is None or not db_permission:
            return public.fail_v2('Please set permissions!')
        # if db_permission not in ["read","readWrite","dbAdmin","clusterAdmin","userAdmin","backup","restore","root"]:
        #     return public.returnMsg(False, '数据库权限错误!')
        role_permission = [{"role": permission, "db": user_name} for permission in db_permission]

        db_find = public.M("databases").where("username=? AND LOWER(type)=LOWER('MongoDB')", (user_name,)).find()
        if not db_find:
            return public.fail_v2("The database does not exist!")

        if not public.process_exists("mongod") and not int(db_find["sid"]):
            return public.fail_v2("The Mongodb service is not turned on yet!")

        status, mongodb_obj = self.get_obj_by_sid(db_find["sid"])
        if status is False:
            return public.fail_v2(mongodb_obj)

        status, db_obj = mongodb_obj.get_db_obj_new(user_name)
        if status is False:
            return public.fail_v2(db_obj)

        try:
            user_data = db_obj.command('usersInfo', user_name)
            if user_data:
                if len(user_data["users"]) != 0:
                    del_role_permission = [{"role": role.get("role"), "db": user_name} for role in
                                           user_data["users"][0].get("roles", [])]
                    db_obj.command('revokeRolesFromUser', user_name, roles=del_role_permission)
            db_obj.command("grantRolesToUser", user_name, roles=role_permission)

            return public.success_v2(f"{user_name} Authorisation successful!")
        except Exception as err:
            return public.fail_v2(f"Authorisation failed!{err}")
