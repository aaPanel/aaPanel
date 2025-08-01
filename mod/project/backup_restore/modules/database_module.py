# coding: utf-8
# -------------------------------------------------------------------
# aapanel
# -------------------------------------------------------------------
# Copyright (c) 2015-2099 aapanel(http://www.aapanel.com) All rights reserved.
# -------------------------------------------------------------------
# Author: miku <miku@bt.cn>
# -------------------------------------------------------------------

import json
import os
import random
import re
import shutil
import string
import sys
import time
import warnings

if "/www/server/panel/class" not in sys.path:
    sys.path.insert(0, "/www/server/panel/class")
if "/www/server/panel/class_v2" not in sys.path:
    sys.path.insert(0, "/www/server/panel/class_v2")
if "/www/server/panel" not in sys.path:
    sys.path.insert(0, "/www/server/panel")

import public
from BTPanel import app
import panelMysql
import database_v2 as database
import databaseModelV2.pgsqlModel as panelPgsql
import databaseModelV2.mongodbModel as panelMongoDB
import databaseModelV2.redisModel as panelRedis
from mod.project.backup_restore.data_manager import DataManager

warnings.filterwarnings("ignore", category=SyntaxWarning)


class DatabaseModule(DataManager):
    _MYSQLDUMP_BIN = public.get_mysqldump_bin()
    _MYSQL_BIN = public.get_mysql_bin()

    _MONGODBDUMP_BIN = "/www/server/mongodb/bin/mongodump"
    _MONGOEXPORT_BIN = "/www/server/mongodb/bin/mongoexport"

    _PGDUMP_BIN = "/www/server/pgsql/bin/pg_dump"

    def __init__(self):
        super().__init__()
        self.base_path = '/www/backup/backup_restore'
        self.bakcup_task_json = self.base_path + '/backup_task.json'
        self.mysql_table_data_exist = True
        self.mg_table_data_exist = True
        self.pgsql_table_data_exist = True

    def get_database_backup_conf(self, timestamp=None):
        mysql_data = public.M('databases').select()
        db_list = []
        with app.app_context():
            for data in mysql_data:
                try:
                    real_access = database.database().GetDatabaseAccess(
                        public.to_dict_obj({'name': data['name']})
                    )['message'].get("permission", "127.0.0.1")
                except:
                    real_access = "127.0.0.1"
                related_site = self._get_current_site_name_by_pid(data.get('pid', 0))
                if related_site == "" and data.get('ps'):
                    # try ps
                    p_site = public.M('sites').where('name=?', (data['ps'],)).field('id,name').find()
                    if p_site and not isinstance(p_site, str):
                        related_site = p_site.get('name', '')

                db_info = {
                    'name': data['name'],
                    'type': data['type'],
                    'id': data['id'],
                    'sid': data['sid'],
                    'ps': data['ps'],
                    'username': data['username'],
                    'password': data['password'],
                    "data_type": "backup",
                    'accept': data['accept'],
                    'database_record': data,
                    'real_access': real_access,
                    'related_site': related_site,
                    'status': 0,
                    'msg': None,
                }
                db_list.append(db_info)

        if os.path.exists("/www/server/redis/src/redis-server") and os.path.exists("/www/server/redis/version.pl"):
            db_info = self.get_redis_info()
            db_list.append(db_info)
        return db_list

    def get_redis_info(self):
        return {
            'name': "redis",
            'type': "redis",
            'id': 0,
            'sid': 0,
            'ps': "redis",
            'username': "redis",
            'password': "redis",
            'status': 0,
            'msg': None,
        }

    def get_remote_db_list(self, timestamp=None):
        import db
        sql = db.Sql()
        sql.table('database_servers')
        result = sql.select()
        if result:
            return {
                'status': True,
                'msg': result
            }
        else:
            return {
                'status': False,
                'msg': public.lang('The list of remote databases is empty'),
            }

    def resotre_remote_db_server(self, remote_db_list):
        try:
            for remote_db in remote_db_list:
                local_remote_db_info = public.M('database_servers').where(
                    'db_host=? AND db_port=?',
                    (remote_db['db_host'], remote_db['db_port'])
                ).select()
                if not local_remote_db_info:
                    pdata = {
                        'id': remote_db['id'],
                        'db_host': remote_db['db_host'],
                        'db_port': remote_db['db_port'],
                        'db_user': remote_db['db_user'],
                        'db_password': remote_db['db_password'],
                        'ps': remote_db['ps'],
                        'type': remote_db['type'],
                        'db_type': remote_db['db_type']
                    }
                    result = public.M("database_servers").insert(pdata)
        except:
            pass

    def restore_remote_database(self, db_data):
        database_record = db_data['database_record']
        local_db_info = public.M('databases').where('name=?', (db_data["name"],)).select()
        if not local_db_info:
            pdata = {
                'pid': database_record['pid'],
                'name': database_record['name'],
                'username': database_record['username'],
                'password': database_record['password'],
                'accept': database_record['accept'],
                'ps': database_record['ps'],
                'addtime': database_record['addtime'],
                'db_type': database_record['db_type'],
                'conn_config': database_record['conn_config'],
                'sid': database_record['sid'],
                'type': database_record['type'],
                'type_id': database_record['type_id']
            }
            public.M("databases").insert(pdata)

    def backup_redis_data(self, timestamp: int):
        """
        备份数据库
        """
        db_fname = "all_db"
        redis_obj = panelRedis.panelRedisDB()
        if redis_obj.redis_conn(0) is False:
            return public.returnMsg(False, public.lang("Redis connection exception!"))

        _db_num = 16
        _REDIS_CONF = os.path.join(public.get_setup_path(), "redis/redis.conf")
        if os.path.exists(_REDIS_CONF):
            redis_conf = public.readFile(_REDIS_CONF)
            db_obj = re.search("\ndatabases\s+(\d+)", redis_conf)
            if db_obj:
                _db_num = int(db_obj.group(1))

        for db_idx in range(0, _db_num):
            try:
                redis_obj.redis_conn(db_idx).save()
            except:
                continue

        redis_obj = redis_obj.redis_conn(0)
        src_path = os.path.join(redis_obj.config_get().get("dir", ""), "dump.rdb")
        if not os.path.exists(src_path):
            return public.returnMsg(False, public.lang('BACKUP_ERROR'))
        backup_path = f"/www/backup/backup_restore/{timestamp}_backup/database/redis".format(timestamp=timestamp)
        if not os.path.exists(backup_path):
            public.ExecShell("mkdir -p {}".format(backup_path))
        file_name = "{db_fname}_{backup_time}_redis_data.rdb".format(
            db_fname=db_fname,
            backup_time=time.strftime("%Y-%m-%d_%H-%M-%S", time.localtime())
        )
        file_path = os.path.join(backup_path, file_name)
        shutil.copyfile(src_path, file_path)
        if not os.path.exists(file_path):
            return public.returnMsg(False, public.lang('BACKUP_ERROR'))

        return public.returnMsg(True, file_path)

    def backup_database_data(self, timestamp):
        data_list = self.get_backup_data_list(timestamp)
        if not data_list:
            return None
        self.print_log("====================================================", "backup")
        self.print_log(public.lang("Starting a backup of database data"), 'backup')
        for db in data_list['data_list']['database']:
            db['status'] = 1
            self.update_backup_data_list(timestamp, data_list)
            try:
                if db['sid'] == 0:
                    log_str = f"Backup {db['type']} database: {db['name']}"
                    self.print_log(public.lang(log_str), "backup")
                    backup_result = None
                    db['sql_file_name'] = None
                    db['size'] = None
                    db['sql_sha256'] = None

                    if db.get('type', '').lower() == 'mysql':
                        backup_result = self.backup_mysql_data(db['name'], timestamp)

                    elif db.get('type', '').lower() == 'mongodb':
                        backup_result = self.backup_mongodb_data(db['name'], timestamp)

                    elif db.get('type', '').lower() == 'pgsql':
                        backup_result = self.backup_pgsql_data(db['name'], timestamp)

                    elif db.get('type', '').lower() == 'redis':
                        backup_result = self.backup_redis_data(timestamp)

                    if backup_result:
                        if backup_result['status'] is True:
                            backup_file = backup_result['msg']
                            db['sql_file_name'] = backup_file
                            db['size'] = self.get_file_size(backup_file)
                            db['sql_sha256'] = self.get_file_sha256(backup_file)
                            db['status'] = 2
                            db['msg'] = None
                            format_backup_file_size = self.format_size(int(db['size']))
                            new_log_str = f"{db['type']} database {db['name']} ✓ ({format_backup_file_size})"
                            self.replace_log(log_str, new_log_str, 'backup')
                        elif backup_result['status'] is False:
                            db['status'] = 3
                            db['msg'] = backup_result['msg']
                            new_log_str = f"{db['type']} database {db['name']} ✗ ({backup_result['msg']})"
                            self.replace_log(log_str, new_log_str, 'backup')
                    else:
                        db['status'] = 2
                        db['msg'] = None
                else:
                    log_str = public.lang("Backup {}remote {}database".format(db['name'], db['type']))
                    self.print_log(log_str, "backup")
                    db['status'] = 2
                    db['msg'] = None
                    new_log_str = public.lang("{}Remote {} database information ✓".format(db['name'], db['type']))
                    self.replace_log(log_str, new_log_str, 'backup')
            except Exception as e:
                self.print_log(public.lang(f"Backup {db['type']} database {db['name']} failed Cause:{str(e)}"),
                               "backup")
                db['status'] = 3
                db['msg'] = str(e)
                continue
            self.update_backup_data_list(timestamp, data_list)

        get_remote_list_result = self.get_remote_db_list()
        if get_remote_list_result['status'] is True:
            data_list['data_list']['remote_db_list'] = get_remote_list_result['msg']
            self.update_backup_data_list(timestamp, data_list)
        self.print_log(public.lang("Database data backup completed"), 'backup')

    # ======================== sqlite ==========================================
    def backup_sqlite_data(self, timestamp):
        db_model_path = "/www/server/panel/data/db_model.json"
        if os.path.exists(db_model_path):
            if not os.path.exists(
                    "/www/backup/backup_restore/{timestamp}_backup/database/db_model.json".format(timestamp=timestamp)):
                public.ExecShell(
                    "mkdir -p /www/backup/backup_restore/{timestamp}_backup/database".format(timestamp=timestamp))
            public.ExecShell(
                "\cp -rpa {db_model_path} /www/backup/backup_restore/{timestamp}_backup/database/db_model.json".format(
                    db_model_path=db_model_path, timestamp=timestamp))
            db_model_info = json.loads(public.readFile(db_model_path))

            db_list = []
            for db_path, db_info in db_model_info.items():
                if os.path.exists(db_path):
                    backup_dir = "/www/backup/backup_restore/{timestamp}_backup/database/sqlite".format(
                        timestamp=timestamp)
                    if not os.path.exists(backup_dir):
                        public.ExecShell("mkdir -p {backup_dir}".format(backup_dir=backup_dir))

                    random_suffix = ''.join(random.choice(string.ascii_letters + string.digits) for _ in range(8))
                    new_db_name = db_info['name'] + '_' + random_suffix
                    db_list.append({
                        "db_path": db_path,
                        "db_name": db_info['name'],
                        "new_db_name": new_db_name
                    })
                    backup_file_path = "{backup_dir}/{db_name}".format(backup_dir=backup_dir, db_name=new_db_name)
                    public.ExecShell("\cp -rpa {db_path} {backup_file_path}".format(db_path=db_path,
                                                                                    backup_file_path=backup_file_path))
            public.WriteFile("/www/backup/backup_restore/{timestamp}_backup/database/sqlite/db_list.json".format(
                timestamp=timestamp), json.dumps(db_list))

    def restore_sqlite_data(self, timestamp):
        self.print_log("==================================", "restore")
        self.print_log(public.lang("Start restoring SQLite database list"), "restore")
        db_model_path = "/www/server/panel/data/db_model.json"
        backup_db_model_path = "/www/backup/backup_restore/{timestamp}_backup/database/db_model.json".format(
            timestamp=timestamp)
        backup_sqlite_dir = "/www/backup/backup_restore/{timestamp}_backup/database/sqlite".format(timestamp=timestamp)
        backup_sqlite_info_path = "/www/backup/backup_restore/{timestamp}_backup/database/sqlite/db_list.json".format(
            timestamp=timestamp)

        if not os.path.exists(backup_db_model_path) or not os.path.exists(backup_sqlite_dir):
            self.print_log(public.lang("SQLite database list backup file does not exist, skipping restoration"),
                           "restore")
            return True

        db_model_info = json.loads(public.readFile(backup_sqlite_info_path))

        for db_info in db_model_info:
            db_name = db_info['db_name']
            new_db_name = db_info['new_db_name']
            db_path = db_info['db_path']
            if os.path.exists(db_path):
                continue

            db_dir = os.path.dirname(db_path)
            if not os.path.exists(db_dir):
                public.ExecShell("mkdir -p {}".format(db_dir))

            public.ExecShell(
                "\cp -rpa {backup_sqlite_dir}/{new_db_name} {db_path}".format(backup_sqlite_dir=backup_sqlite_dir,
                                                                              new_db_name=new_db_name, db_path=db_path))

        cp_cmd = "\cp -rpa {backup_db_model_path} {db_model_path}".format(backup_db_model_path=backup_db_model_path,
                                                                          db_model_path=db_model_path)
        public.ExecShell(cp_cmd)
        self.print_log(public.lang("SQLite database list restoration completed"), "restore")
        return True

    # ======================== sqlite ==========================================

    def backup_mysql_data(self, db_name: str, timestamp: int):
        try:
            db_port = int(panelMysql.panelMysql().query("show global variables like 'port'")[0][1])
        except:
            db_port = 3306

        db_charset = public.get_database_character(db_name)

        set_gtid_purged = ""
        resp = public.ExecShell("{} --help | grep set-gtid-purged".format(self._MYSQLDUMP_BIN))[0]
        if resp.find("--set-gtid-purged") != -1:
            set_gtid_purged = "--set-gtid-purged=OFF"
        db_user = "root"
        db_password = public.M("config").where("id=?", (1,)).getField("mysql_root")
        db_host = "localhost"

        backup_path = "/www/backup/backup_restore/{timestamp}_backup/database/mysql".format(timestamp=timestamp)
        if not os.path.exists(backup_path):
            os.makedirs(backup_path, exist_ok=True)
        sql_file = backup_path + "/{}.sql".format(db_name)
        # 导出结构和数据
        shell = "'{mysqldump_bin}' {set_gtid_purged} --opt --skip-lock-tables --single-transaction --routines --events --skip-triggers --default-character-set='{db_charset}' --force " \
                "--host='{db_host}' --port={db_port} --user='{db_user}' --password='{db_password}' '{db_name}'".format(
            mysqldump_bin=self._MYSQLDUMP_BIN,
            set_gtid_purged=set_gtid_purged,
            db_charset=db_charset,
            db_host=db_host,
            db_port=db_port,
            db_user=db_user,
            db_password=db_password,
            db_name=db_name,
        )
        shell += " > '{export_sql_file}' ".format(export_sql_file=sql_file)
        public.ExecShell(shell, env={"MYSQL_PWD": db_password})
        return {"status": True, "msg": sql_file}

    def backup_mongodb_data(self, db_name, timestamp: int):
        """
        备份 MongoDB 数据库(仅本地)
        Args:
            db_name (str): 数据库名称
            timestamp (int): 时间戳
        Returns:
            dict: 备份结果状态
        """

        # 检查备份工具是否存在
        if not os.path.exists(self._MONGODBDUMP_BIN):
            return {"status": False,
                    "msg": public.lang("Lack of backup tools, please install MongoDB via Software Manager first!")}

        if not os.path.exists(self._MONGOEXPORT_BIN):
            return {"status": False,
                    "msg": public.lang("Lack of backup tools, please install MongoDB via Software Manager first!")}

        # 查询数据库信息
        db_find = public.M("databases").where("name=? AND LOWER(type)=LOWER('mongodb')", (db_name,)).find()
        if not db_find:
            return {"status": False, "msg": public.lang(f"Database not found! {db_name}")}

        if not public.process_exists("mongod"):
            return {"status": False, "msg": public.lang("Mongodb service is not running!")}

        # 设置基本备份参数
        db_user = db_find.get("username", "")
        db_password = db_find.get("password", "")
        file_type = "bson"  # 默认使用bson格式备份
        db_host = "127.0.0.1"
        db_port = panelMongoDB.panelMongoDB().get_config_options("net", "port", 27017)

        # 设置备份路径
        backup_path = f"/www/backup/backup_restore/{timestamp}_backup/database/mongodb"
        if not os.path.exists(backup_path):
            os.makedirs(backup_path, exist_ok=True)

        file_name = f"{db_name}_{file_type}_{time.strftime('%Y-%m-%d_%H-%M-%S', time.localtime())}_mongodb_data"
        export_dir = os.path.join(backup_path, file_name)

        # 构建备份命令
        mongodump_shell = f"'{self._MONGODBDUMP_BIN}' --host='{db_host}' --port={int(db_port)} --db='{db_name}' --out='{export_dir}'"

        auth_status = panelMongoDB.panelMongoDB().get_config_options("security", "authorization",
                                                                     "disabled") == "enabled"

        if auth_status and not os.path.exists(f"{export_dir}/auth.pl"):
            public.ExecShell(f"echo True > {export_dir}/auth.pl")

        # 如果需要认证，添加用户名和密码
        if auth_status and db_password:
            mongodump_shell += f" --username='{db_user}' --password='{db_password}'"

        # 执行备份命令
        public.ExecShell(mongodump_shell)

        # 检查备份是否成功
        if not os.path.exists(export_dir):
            return {"status": False, "msg": public.lang("Database backup failed, export directory does not exist!")}

        # 压缩备份文件
        backup_file = f"{export_dir}.zip"
        public.ExecShell(f"cd {backup_path} && zip -m {backup_file} -r {file_name}")

        if not os.path.exists(backup_file):
            public.ExecShell(f"rm -rf {export_dir}")
            return {"status": False, "msg": public.lang("Backup compression failed!")}

        # 记录备份信息
        return {"status": True, "msg": backup_file}

    def backup_pgsql_data(self, db_name: str, timestamp: int):
        """
        备份PostgreSQL数据库(仅本地)
        Args:
            db_name (str): 数据库名称
            timestamp (int): 时间戳，用于创建备份目录
        Returns:
            dict: 备份结果状态
        """
        # 检查备份工具是否存在

        if not os.path.exists(self._PGDUMP_BIN):
            return {"status": False,
                    "msg": public.lang("Lack of backup tool, please install pgsql manager via software store first!")}

        # 查询数据库信息
        db_find = public.M("databases").where("name=? AND LOWER(type)=LOWER('pgsql')", (db_name,)).find()
        if not db_find:
            return {"status": False, "msg": public.lang(f"Database does not exist! {db_name}")}

        # Set basic backup parameters
        db_user = "postgres"
        db_host = "127.0.0.1"
        db_port = 5432

        # Get PostgreSQL password
        try:
            t_path = os.path.join(public.get_panel_path(), "data/postgresAS.json")
            if not os.path.isfile(t_path):
                return {"status": False, "msg": public.lang("Please set administrator password first!")}

            admin_info = json.loads(public.readFile(t_path))
            db_password = admin_info.get("password", "")
            if not db_password:
                return {"status": False,
                        "msg": public.lang("Database password is empty! Please set database password first!")}
        except Exception as e:
            return {"status": False, "msg": public.lang(f"Failed to get PostgreSQL password: {str(e)}")}

        # 设置备份路径
        backup_path = f"/www/backup/backup_restore/{timestamp}_backup/database/pgsql"
        if not os.path.exists(backup_path):
            os.makedirs(backup_path, exist_ok=True)

        # 构建备份文件名
        file_name = f"{db_name}_{time.strftime('%Y-%m-%d_%H-%M-%S', time.localtime())}_pgsql_data.sql.gz"
        backup_file = os.path.join(backup_path, file_name)

        # 构建备份命令
        shell = f"'{self._PGDUMP_BIN}' --host='{db_host}' --port={int(db_port)} --username='{db_user}' --dbname='{db_name}' --clean | gzip > '{backup_file}'"

        # 执行备份命令
        public.ExecShell(shell, env={"PGPASSWORD": db_password})

        # 检查备份是否成功
        if not os.path.exists(backup_file):
            return {"status": False, "msg": public.lang("Database backup failed, export file does not exist!")}

        # 写入日志
        public.WriteLog("TYPE_DATABASE", "DATABASE_BACKUP_SUCCESS", (db_name,))
        return {"status": True, "msg": backup_file}

    def _sync_database(self, db_client: object):
        bin_path = None
        name = "unknown"
        try:
            if hasattr(db_client, "_MYSQL_BIN"):
                bin_path = "/www/server/mysql/bin/mysqld"
                name = "MySQL"
            elif hasattr(db_client, "_MONGODBDUMP_BIN"):
                bin_path = "/www/server/mongodb/bin/mongod"
                name = "MongoDB"
            elif hasattr(db_client, "_PSQL_BIN"):
                bin_path = "/www/server/pgsql/bin/pg_config"
                name = "PostgreSQL"
            if not bin_path or not os.path.exists(bin_path) or not name:
                return

            log = public.lang(f"{name} synchronization...")
            self.print_log(log, "restore")
            # noinspection PyUnresolvedReferences
            sync_db_user_pwd = db_client.SyncToDatabases(public.to_dict_obj({"type": 0, "ids": "[]"}))
            public.print_log(f"sync_db_user_pwd {name}>>> {sync_db_user_pwd}")
            self.replace_log(log, public.lang(f"{name} synchronization completed!"), "restore")
        except Exception as e:
            public.print_log("{} sync database func error: {}".format(name, str(e)))

    def _init_mysql_root(self):
        try:
            root_pwd = None
            if self.overwrite:  # table config has overwrited this time
                root_pwd = public.M("config").where("id=?", (1,)).getField("mysql_root")

            if not os.path.exists("/www/server/panel/data/remysql_root.pl"):
                root_pwd = ''.join(random.choice(string.ascii_letters + string.digits) for _ in range(16))

            if root_pwd:
                init_root_cmd = "btpython /www/server/panel/tools.py root {}".format(root_pwd)
                public.ExecShell(init_root_cmd)
                public.ExecShell("echo 'True' > /www/server/panel/data/remysql_root.pl")
                self.print_log(public.lang("MySQL initialization successful!"), "restore")
                self.print_log(public.lang("MySQL will restart, please wait..."), "restore")
                time.sleep(5)
                public.ExecShell("/etc/init.d/mysqld restart")
                time.sleep(7)
        except:
            pass

    def _init_mg_root(self, timestamp: int):
        if not self.overwrite:
            return
        try:
            auth = os.path.join(self.base_path, f"{timestamp}_backup/database/mongodb/auth.pl")
            body = {"status": 1} if auth else {"status": 0}
            set_root = panelMongoDB.main().set_auth_status(public.to_dict_obj(body))
            time.sleep(1)
            if set_root.get("status") == 0:
                self.print_log(public.lang("MongoDB initialization successful!"), "restore")
            else:
                self.print_log(public.lang(f"MongoDB set auth failed!"), "restore")
        except Exception as e:
            self.print_log(public.lang("MongoDB set auth failed! error: {}".format(e)), "restore")

    def _init_pg_root(self):
        try:
            current_root = panelPgsql.main().get_root_pwd(public.dict_obj())["message"].get("result")
        except:
            current_root = None

        pwd_root = current_root if current_root else public.GetRandomString(16)
        set_root = panelPgsql.main().set_root_pwd(
            public.to_dict_obj({"password": pwd_root})
        )
        time.sleep(1)
        if set_root.get("status") == 0:
            self.print_log(public.lang("PostgreSQL initialization successful!"), "restore")
        else:
            self.print_log(public.lang(f"PostgreSQL set root failed!"), "restore")

    def _init_redis(self):
        config = public.readFile("/www/server/redis/redis.conf")
        if config and "protected-mode yes" in config and not re.search(
                r"# Redis configuration file example.\nrequirepass (\S+)", config
        ):
            config = config.replace(
                "# Redis configuration file example.\n",
                f"# Redis configuration file example.\nrequirepass {public.GetRandomString(16)}\n",
            )
            public.writeFile("/www/server/redis/redis.conf", config)
            self.print_log(public.lang("Redis initialization successful!"), "restore")
            public.ExecShell("/etc/init.d/redis restart")
            time.sleep(1)

    def _before_restore(self, timestamp: int):
        # init root
        self._init_mysql_root()
        self._init_mg_root(timestamp)
        self._init_pg_root()
        self._init_redis()
        # sync to database
        self._sync_database(database.database())
        self._sync_database(panelMongoDB.main())
        self._sync_database(panelPgsql.main())

    def restore_database_data(self, timestamp):
        self.print_log("==================================", "restore")
        self.print_log(public.lang("Start restoring database"), "restore")
        restore_data = self.get_restore_data_list(timestamp)
        database_data = restore_data['data_list']['database']
        with app.app_context():
            # === before restore ===
            self._before_restore(timestamp)
            self.print_log(public.lang("Start restoring database's data..."), "restore")
            for db_data in database_data:
                log_str = public.lang("Restoring {} database {}").format(db_data['type'], db_data['name'])
                result = None
                self.print_log(log_str, "restore")
                db_data['restore_status'] = 1
                self.update_restore_data_list(timestamp, restore_data)
                try:
                    # server local db
                    if db_data['sid'] == 0:
                        # ==================== MySQL  ====================
                        if db_data['type'] == 'MySQL':
                            self.restore_mysql_info(db_data)
                            result = self.input_mysql_sql(db_data)

                        # ==================== MongoDB  ====================
                        elif db_data['type'] == 'MongoDB':
                            self.restore_mongodb_info(db_data)
                            result = self.input_mongodb_data(db_data)

                        # ==================== PostgreSQL  ====================
                        elif db_data['type'] == 'pgsql':
                            self.restore_pgsql_info(db_data)
                            result = self.input_pgsql_data(db_data)

                        # ==================== Redis  ====================
                        elif db_data['type'] == 'redis':
                            result = self.restore_redis_data(db_data)

                    else:  # remote db
                        self.restore_remote_database(db_data)

                    result = {'status': True, 'msg': ''} if not result else result
                    if result['status'] is True:
                        db_data['restore_status'] = 2
                        self.update_restore_data_list(timestamp, restore_data)
                        new_log_str = public.lang("{} database {} ✓").format(db_data['type'], db_data['name'])
                        self.replace_log(log_str, new_log_str, "restore")

                    else:
                        db_data['restore_status'] = 3
                        db_data['msg'] = result['msg']
                        new_log_str = public.lang("{} database {} ✗ ({})").format(db_data['type'], db_data['name'],
                                                                                  result['msg'])
                        self.replace_log(log_str, new_log_str, 'restore')

                except Exception as e:
                    err_msg = public.lang("Failed to restore {} database {} Reason: {}").format(db_data['type'],
                                                                                                db_data['name'], str(e))
                    self.replace_log(log_str, err_msg, 'restore')
                    db_data['restore_status'] = 3
                    db_data['msg'] = err_msg
                    self.update_restore_data_list(timestamp, restore_data)
                    continue

            self.print_log(public.lang("Database data restoration completed"), "restore")

        # ==================== remote db  =================
        remote_db_list = restore_data['data_list'].get('remote_db_list')
        if remote_db_list is not None:
            self.print_log("==================================", "restore")
            self.print_log(public.lang("Start restoring remote database"), "restore")
            self.resotre_remote_db_server(restore_data['data_list']['remote_db_list'])
            self.print_log(public.lang("Remote database restoration completed"), "restore")

    def _get_mysql_db_access(self, db_data) -> tuple[str, str]:
        real_access = db_data.get("real_access", "127.0.0.1")
        if real_access == "%":
            dataAccess = "%"
        elif real_access not in ["%", "127.0.0.1"]:
            dataAccess = "ip"
        else:
            dataAccess = "127.0.0.1"
        return dataAccess, real_access

    def _reset_password(self, db_client, id: int, name: str, password: str) -> dict:
        res = db_client.ResDatabasePassword(public.to_dict_obj({
            "id": id,
            "name": name,
            "password": password,
        }))
        return res

    def _before_input_sql(self, db_client, db_data: dict, db_type: str) -> dict:
        # 插入前备份
        db_id = public.M('databases').where(
            "name=? AND LOWER(type)=?", (db_data['name'], db_type)
        ).getField('id')
        if not db_id:
            self.print_log(public.lang("{} backup id does not exist, import terminated").format(db_data['name']),
                           "restore")
            return {"status": False,
                    "msg": public.lang("{} database id does not exist, data recovery terminated").format(db_type)}

        back_up = db_client.ToBackup(public.to_dict_obj({"id": db_id}))
        if back_up.get('status') != 0:
            return {"status": False, "msg": back_up.get('message', '')}

        return {"status": True, "msg": "success"}

    def restore_mysql_info(self, db_data) -> dict:
        dataAccess, real_access = self._get_mysql_db_access(db_data)
        if_exist = public.M('databases').where(
            "name=? AND LOWER(type)=LOWER('mysql')", (db_data["name"],)
        ).find()
        if if_exist:
            self.mysql_table_data_exist = True
            # always fix pid
            public.M("databases").where("id=?", (if_exist['id'],)).update({
                "pid": self._get_current_pid_by_site_name(
                    db_data.get("related_site", "")
                )
            })
            if not self.overwrite:
                return {"status": True, "msg": public.lang("MySQL database {} already exists").format(db_data['name'])}
            # default.db is overwrited
            # mysql real access
            set_res = database.database().SetDatabaseAccess(public.to_dict_obj({
                "dataAccess": dataAccess,
                "access": real_access,
                "name": db_data["username"],
                "ssl": "",  # todo ssl 计划移除
            }))
            if set_res.get("status") != 0:
                self.print_log(
                    public.lang(
                        "Failed to restore {} database access permissions. Reason: {}"
                    ).format(db_data['name'], set_res['message']),
                    "restore"
                )
            return set_res
        else:  # no exitst
            self.mysql_table_data_exist = False
            args = public.dict_obj()
            args.pid = self._get_current_pid_by_site_name(db_data.get("related_site", ""))
            args.name = db_data["name"]
            args.db_user = db_data["username"]
            args.password = db_data["password"]
            args.dataAccess = dataAccess  # restore access
            args.address = real_access  # restore access
            args.codeing = "utf8mb4"
            args.dtype = "MySQL"
            args.ps = db_data["ps"]
            args.sid = "0"
            args.listen_ip = "0.0.0.0/0"
            args.active = False
            res = database.database().AddDatabase(args)
            if res['status'] != 0:
                self.print_log(
                    public.lang("Failed to create {} database. Reason: {}").format(db_data['name'], res['message']),
                    "restore")
            return res

    def input_mysql_sql(self, db_data):
        db_host = "localhost"
        db_user = "root"
        try:
            db_port = int(panelMysql.panelMysql().query("show global variables like 'port'")[0][1])
        except:
            db_port = 3306
        if self.mysql_table_data_exist and not self.overwrite:
            return {"status": True, "msg": public.lang("Database already exists, skipping SQL restoration")}
        # 备份数据库
        back_up = self._before_input_sql(
            db_client=database.database(),
            db_data=db_data,
            db_type='mysql'
        )

        if not back_up.get('status'):
            return back_up

        # force dump
        db_password = public.M("config").where("id=?", (1,)).getField("mysql_root")
        db_name = db_data['name']
        db_charset = public.get_database_character(db_name)
        shell = "'{mysql_bin}' --force --default-character-set='{db_charset}' --host='{db_host}' --port={db_port} --user='{db_user}' --password='{password}' '{db_name}'".format(
            mysql_bin=self._MYSQL_BIN,
            db_charset=db_charset,
            db_host=db_host,
            db_port=db_port,
            db_user=db_user,
            password=db_password,
            db_name=db_name,
        )
        sql_path = db_data['sql_file_name']
        output, error = public.ExecShell(
            "{shell} < '{path}'".format(shell=shell, path=sql_path), env={"MYSQL_PWD": db_password}
        )

        if "error:" in output.lower() or "error:" in error.lower():
            return {"status": False, "msg": output + error}
        else:
            return {"status": True, "msg": public.lang("Import successful")}

    def restore_mongodb_info(self, db_data):
        if_exist = public.M('databases').where(
            "name=? AND LOWER(type)=LOWER('mongodb')", (db_data["name"],)
        ).find()
        if if_exist:
            self.mg_table_data_exist = True
            if not self.overwrite:
                return {
                    "status": True, "msg": public.lang("MongoDB database {} already exists").format(db_data['name'])
                }
            return {"status": True, "msg": public.lang(f"MongoDB database {db_data['name']} successfully")}
        else:
            self.mg_table_data_exist = False
            args = public.dict_obj()
            args.name = db_data['name']
            args.db_user = db_data['username']
            args.password = db_data['password']
            args.ps = db_data['ps']
            args.sid = 0
            # args.dataAccess = db_data['accept']
            # args.address = ""
            # args.codeing = "utf8mb4"
            # args.dtype = "MongoDb"
            # args.listen_ip = "0.0.0.0/0"
            # args.host = ""
            res = panelMongoDB.main().AddDatabase(args)
            if res['status'] is False:
                return {"status": False, "msg": res['msg']}
            else:
                return {"status": True, "msg": public.lang("Creation successful")}

    def input_mongodb_data(self, db_data):
        if self.mg_table_data_exist and not self.overwrite:
            return {"status": True, "msg": public.lang("Database already exists, skipping data restoration")}

        back_up = self._before_input_sql(
            db_client=panelMongoDB.main(),
            db_data=db_data,
            db_type='mongodb'
        )
        if not back_up.get('status'):
            return back_up

        db_name = db_data['name']
        sql_path = db_data['sql_file_name']
        args = public.dict_obj()
        args.file = sql_path
        args.name = db_name
        res = panelMongoDB.main().InputSql(args)
        if res['status'] is False:
            return {"status": False, "msg": res['msg']}
        else:
            return {"status": True, "msg": public.lang("Import successful")}

    def restore_pgsql_info(self, db_data):
        if_exist = public.M('databases').where(
            "name=? AND LOWER(type)=LOWER('pgsql')", (db_data["name"],)
        ).find()
        if if_exist:
            self.pgsql_table_data_exist = True
            if not self.overwrite:
                return {"status": True,
                        "msg": public.lang("PostgreSQL database {} already exists").format(db_data['name'])}
            return {
                "status": True, "msg": public.lang(f"PostgreSQL database {db_data['name']} successfully")
            }
        else:
            self.pgsql_table_data_exist = False
            args = public.dict_obj()
            args.name = db_data['name']
            args.db_user = db_data['username']
            args.password = db_data['password']
            args.ps = db_data['ps']
            args.sid = 0
            # todo pgsql listener ip 依赖前端传递, 默认本地
            # args.listen_ip = "0.0.0.0/0"
            args.host = ""
            res = panelPgsql.main().AddDatabase(args)
            if res['status'] is False:
                return {"status": False, "msg": res['msg']}
            else:
                return {"status": True, "msg": public.lang("Creation successful")}

    def restore_pgsql_root_pwd(self, pgsql_root_pwd):
        args = public.dict_obj()
        args.password = pgsql_root_pwd
        panelPgsql.main().set_root_pwd(args)

    def input_pgsql_data(self, db_data):
        """还原PostgreSQL数据库
        @param db_data: dict 数据库信息
        """
        try:
            if self.pgsql_table_data_exist and not self.overwrite:
                return {"status": True, "msg": public.lang("Database already exists, skipping data restoration")}
            # 备份数据库
            back_up = self._before_input_sql(
                db_client=panelPgsql.main(),
                db_data=db_data,
                db_type='pgsql'
            )
            if not back_up.get('status'):
                return back_up

            if not os.path.exists('/www/server/pgsql/bin/psql'):
                return {"status": False, "msg": public.lang(
                    "Lack of restoration tools, please install pgsql via software manager first!")}

            db_name = db_data['name']
            sql_gz_file = db_data['sql_file_name']
            if os.path.exists(sql_gz_file):
                public.ExecShell("gunzip {sql_file}".format(sql_file=sql_gz_file))

            sql_file = sql_gz_file.replace(".gz", "")
            if not os.path.exists(sql_file):
                return {"status": False, "msg": public.lang("Backup file does not exist!")}

            # 获取本地PostgreSQL的配置信息
            t_path = os.path.join('/www/server/panel/data/postgresAS.json')
            if not os.path.isfile(t_path):
                characters = string.ascii_lowercase + string.digits
                pgsql_root_pwd = ''.join(random.choice(characters) for _ in range(16))
                self.restore_pgsql_root_pwd(pgsql_root_pwd)

            db_port = panelPgsql.main().get_port(None)["data"]
            db_password = json.loads(public.readFile(t_path)).get("password", "")

            # 构建psql命令
            shell = "'/www/server/pgsql/bin/psql' --host='127.0.0.1' --port={} --username='postgres' --dbname='{}'".format(
                int(db_port),
                db_name
            )

            # 执行还原命令
            result = public.ExecShell("{} < '{}'".format(shell, sql_file), env={"PGPASSWORD": db_password})
            # if "error:" in result[0].lower() or "error:" in result[1].lower():
            #     return {"status": False, "msg": result[0] + result[1]}

            return {"status": True, "msg": public.lang("Restoration successful")}

        except Exception as e:
            return {"status": False, "msg": str(e)}

    def restore_redis_data(self, db_data):
        try:
            rdb_file = db_data['sql_file_name']
            if os.path.exists(rdb_file):
                if os.path.exists("/www/server/redis/dump.rdb"):
                    public.ExecShell("/etc/init.d/redis stop")
                    time.sleep(1)
                    public.ExecShell("rm -f /www/server/redis/dump.rdb.bak")
                    public.ExecShell("mv /www/server/redis/dump.rdb /www/server/redis/dump.rdb.bak")

                public.ExecShell("\cp -pra {rdb_file} /www/server/redis/dump.rdb".format(rdb_file=rdb_file))
                public.ExecShell("chown -R redis:redis /www/server/redis")
                public.ExecShell("chmod 644 /www/server/redis/dump.rdb")
                time.sleep(1)
                public.ExecShell("/etc/init.d/redis start")

                time.sleep(1)
                public.ExecShell("/etc/init.d/redis stop")
                public.ExecShell("rm -f /www/server/redis/dump.rdb.bak")
                public.ExecShell("mv /www/server/redis/dump.rdb /www/server/redis/dump.rdb.bak")
                public.ExecShell("\cp -pra {rdb_file} /www/server/redis/dump.rdb".format(rdb_file=rdb_file))
                public.ExecShell("chown -R redis:redis /www/server/redis")
                public.ExecShell("chmod 644 /www/server/redis/dump.rdb")
                public.ExecShell("/etc/init.d/redis start")
            return {"status": True, "msg": public.lang("Restoration successful")}
        except Exception as e:
            return {"status": False, "msg": str(e)}

    def fix_wp_onekey(self, timestamp: int):
        restore_data = self.get_restore_data_list(timestamp)
        site_backup_path = self.base_path + f"/{timestamp}_backup/site/"
        if not os.path.exists(site_backup_path):
            return

        for site in restore_data['data_list'].get('site', []):
            if site.get('project_type').lower() not in ['wp2', 'wp']:
                continue
            if not site.get('wp_onekey'):
                continue
            # wp_onekey = {"prefix": "wp_", "user", "wp_user", "pass": "wp_password"}
            wp_onekey: dict = site['wp_onekey']
            s_id = self._get_current_pid_by_site_name(site['name'])
            if not s_id:
                continue

            d_id = public.M('databases').where(
                '(pid=? AND LOWER(type)=LOWER("mysql")) OR ps=?', (s_id, site['name'])
            ).getField('id')
            if not d_id:
                continue
            try:
                if_exist = public.M('wordpress_onekey').where('prefix=?', (wp_onekey['prefix'],)).find()
                if if_exist:
                    public.M('wordpress_onekey').where('prefix=?', (wp_onekey['prefix'],)).update({
                        's_id': int(s_id),
                        'd_id': int(d_id),
                    })
                else:
                    public.M('wordpress_onekey').insert({
                        **wp_onekey,
                        's_id': int(s_id),
                        'd_id': int(d_id),
                    })
            except Exception as e:
                public.print_log("fix forign key error: {}".format(str(e)))
                continue


if __name__ == '__main__':
    # 获取命令行参数
    if len(sys.argv) < 3:
        print("Usage: btpython backup_manager.py <method> <timestamp>")
        sys.exit(1)
    method_name = sys.argv[1]  # 方法名
    timestamp = sys.argv[2]  # IP地址
    database_module = DatabaseModule()  # 实例化对象
    if hasattr(database_module, method_name):  # 检查方法是否存在
        method = getattr(database_module, method_name)  # 获取方法
        method(timestamp)  # 调用方法
    else:
        print(f"Error: method '{method_name}' not found")
