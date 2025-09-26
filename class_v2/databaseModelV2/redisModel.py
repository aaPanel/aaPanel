# coding: utf-8
# -------------------------------------------------------------------
# aaPanel
# -------------------------------------------------------------------
# Copyright (c) 2015-2099 aaPanel(www.aapanel.com) All rights reserved.
# -------------------------------------------------------------------
# Author: hwliang <hwl@aapanel.com>
# -------------------------------------------------------------------

import json
# sqlite模型
# ------------------------------
import os
import re
import shutil
import time
from typing import Union

import public
from databaseModelV2.base import databaseBase
from public.validate import Param

try:
    import redis
except:
    public.ExecShell("btpip install redis")
    import redis
try:
    from BTPanel import session
except:
    pass


# 2025/6/6 同步国内

class panelRedisDB():
    __DB_PASS = None
    __DB_USER = None
    __DB_PORT = 6379
    __DB_HOST = '127.0.0.1'
    __DB_CONN = None
    __DB_ERR = None

    __DB_CLOUD = None

    def __init__(self):
        self.__config = self.get_options(None)
        self.error_message = ""

    def redis_conn(self, db_idx=0):
        if self.__DB_HOST in ['127.0.0.1', 'localhost']:
            if not os.path.exists('/www/server/redis'):
                return False
            if self.__config == "Config Error":
                return False

        if not self.__DB_CLOUD:
            self.__DB_PASS = self.__config['requirepass']
            self.__DB_PORT = int(self.__config['port'])

        try:
            redis_pool = redis.ConnectionPool(
                host=self.__DB_HOST, port=self.__DB_PORT, password=self.__DB_PASS, db=db_idx
            )
            self.__DB_CONN = redis.Redis(connection_pool=redis_pool)
            self.__DB_CONN.ping()
            return self.__DB_CONN
        except redis.exceptions.ConnectionError:
            return False
        except Exception:
            self.__DB_ERR = public.get_error_info()
        return False

    def set_host(self, host, port, name, username, password, prefix=''):
        self.__DB_HOST = host
        self.__DB_PORT = int(port)
        self.__DB_NAME = name
        if self.__DB_NAME:
            self.__DB_NAME = str(self.__DB_NAME)
        self.__DB_USER = str(username)
        self._USER = str(username)
        self.__DB_PASS = str(password)
        self.__DB_PREFIX = prefix
        self.__DB_CLOUD = 1
        return self

    # 获取配置项
    def get_options(self, get=None):
        import ipaddress

        result = {}
        redis_conf = public.readFile("{}/redis/redis.conf".format(public.get_setup_path()))

        if not redis_conf:
            if not os.path.exists('/www/server/redis'):
                return False
            public.ExecShell("mv /www/server/redis/redis.conf /www/server/redis/redis.conf.bak")
            public.ExecShell(
                "wget -O /www/server/redis/redis.conf https://node.aapanel.com/conf/redis.conf;chmod 600 /www/server/redis/redis.conf;chown redis:redis /www/server/redis/redis.conf"
            )
            time.sleep(1)
            redis_conf = public.readFile("{}/redis/redis.conf".format(public.get_setup_path()))

        keys = ["bind", "port", "timeout", "maxclients", "databases", "requirepass", "maxmemory"]
        defaults = ["127.0.0.1", "6379", "300", "10000", "16", "", "0"]
        errors = []

        for n, k in enumerate(keys):
            rep = r"\n{}\s+(.*)".format(k)  # 更准确地捕获整行
            group = re.search(rep, redis_conf)
            if group:
                value = group.group(1).strip()
                try:
                    if k == "maxmemory":
                        # 将 maxmemory 从字节转换为兆字节并赋值
                        value = str(int(value) // 1024 // 1024)
                except:
                    pass
            else:
                value = defaults[n]

            if k in ["port", "timeout", "maxclients", "databases", "maxmemory"]:
                if not value.isdigit():
                    errors.append(f"'{k}' value must be a number, and the currently configured value is '{value}'")
                    continue

            if k == "bind":
                try:
                    # 尝试解析IP地址以验证其格式
                    ipaddress.ip_address(value)
                except ValueError:
                    errors.append(
                        f"'{k}' value must be a valid IP address, the current configuration value is '{value}'")
                    continue

            result[k] = value

        if errors:
            error_message = "The following error was detected in the configuration file for the Redis database:\n" + "\n".join(
                errors)
            error_message += "\nPlease go to the software shop to make the correct changes to the configuration file of the redis plugin!"
            self.error_message = error_message
            return "Config Error"

        return result


class main(databaseBase):
    _DB_BACKUP_DIR = os.path.join(public.M("config").where("id=?", (1,)).getField("backup_path"), "database")
    _REDIS_BACKUP_DIR = os.path.join(_DB_BACKUP_DIR, "redis")
    _REDIS_CONF = os.path.join(public.get_setup_path(), "redis/redis.conf")

    def __init__(self):
        if not os.path.exists(self._REDIS_BACKUP_DIR):
            os.makedirs(self._REDIS_BACKUP_DIR)

        self._db_num = 16
        if os.path.exists(self._REDIS_CONF):
            redis_conf = public.readFile(self._REDIS_CONF)
            db_obj = re.search("\ndatabases\s+(\d+)", redis_conf)
            if db_obj:
                self._db_num = int(db_obj.group(1))

    def GetCloudServer(self, args):
        """
            @name 获取远程服务器列表
            @author hwliang<2021-01-10>
            @return list
        """
        return public.return_message(0, 0, self.GetBaseCloudServer(args))

    def AddCloudServer(self, args):
        """
        @添加远程数据库
        """
        # {"db_host":"192.168.66.129","db_port":"6379","db_user":"root","db_password":"password1","db_ps":"192.168.66.129","type":"redis"}
        # 校验参数
        try:
            args.validate([

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

        return self.AddBaseCloudServer(args)

    def RemoveCloudServer(self, args):
        """
        @删除远程数据库
        """
        return self.RemoveBaseCloudServer(args)

    def ModifyCloudServer(self, args):
        """
        @修改远程数据库
        """
        return self.ModifyBaseCloudServer(args)

    def get_obj_by_sid(self, sid: Union[int, str] = 0, conn_config: dict = None):
        """
        @取mssql数据库对像 By sid
        @sid 数据库分类，0：本地
        """
        if isinstance(sid, str):
            sid = int(sid)
        if sid != 0:
            if not conn_config: conn_config = public.M('database_servers').where("id=?", sid).find()
            db_obj = panelRedisDB()

            try:
                db_obj = db_obj.set_host(
                    conn_config['db_host'],
                    conn_config['db_port'],
                    None, conn_config['db_user'],
                    conn_config['db_password']
                )
            except Exception as e:
                raise public.PanelError(e)
        else:
            db_obj = panelRedisDB()
        return db_obj

    def local_xsssec(self, text):
        """
            @name XSS防御，只替换关键字符，不转义字符
            @author hwliang
            @param text 要转义的字符
            @return str
        """
        sub_list = {
            '<': '＜',
            '>': '＞'
        }
        for s in sub_list.keys():
            text = text.replace(s, sub_list[s])
        return text

    def get_list(self, args):
        """
        @获取数据库列表
        @sql_type = redis
        """

        # 校验参数
        try:
            args.validate([
                Param('sid').Require().Integer(),
            ], [
                public.validate.trim_filter(),
            ])
        except Exception as ex:
            public.print_log("error info: {}".format(ex))
            return public.return_message(-1, 0, str(ex))

        result = []
        sid = args.get('sid/d', 0)

        redis_obj = self.get_obj_by_sid(sid).redis_conn(0)
        if redis_obj is False:
            if panelRedisDB().error_message:
                return public.fail_v2(public.lang(str(panelRedisDB().error_message)))
            return public.success_v2(result)
        redis_info = redis_obj.info()
        is_cluster = redis_info.get("cluster_enabled", 0)
        if is_cluster != 0:
            return public.fail_v2(public.lang("not support redis cluster!"))
        db_num = self._db_num
        if sid != 0:
            db_num = 1000
        for x in range(0, db_num):

            data = {}
            data['id'] = x
            data['name'] = 'DB{}'.format(x)

            try:
                redis_obj = self.get_obj_by_sid(sid).redis_conn(x)

                data['keynum'] = redis_obj.dbsize()
                result.append(data)
            except Exception as ex:
                break

        return public.return_message(0, 0, result)

    def set_redis_val(self, args):
        """
        @设置或修改指定值
        """
        # 校验参数
        try:
            args.validate([
                Param('db_idx').Require().Integer(),
                Param('sid').Require().Integer(),
                Param('name').Require().String(),  # 键
                Param('val').Require().String(),  # 值
                Param('endtime').Integer(),  # 过期时间
            ], [
                public.validate.trim_filter(),
            ])
        except Exception as ex:
            public.print_log("error info: {}".format(ex))
            return public.return_message(-1, 0, str(ex))

        sid = args.get("sid/d", 0)
        db_idx = args.get("db_idx")
        name = args.get("name")
        val = args.get("val")
        endtime = args.get("endtime", None)

        redis_obj = self.get_obj_by_sid(sid).redis_conn(db_idx)
        if redis_obj is False:
            return public.fail_v2(public.lang("redis connect fail!"))
        if endtime is not None:
            redis_obj.set(name, val, int(endtime))
        else:
            redis_obj.set(name, val)

        public.set_module_logs('linux_redis', 'set_redis_val', 1)
        return public.return_message(0, 0, public.lang("Operation is successful"))

    def del_redis_val(self, args):
        """
        @删除key值
        """
        # 校验参数
        try:
            args.validate([

                Param('db_idx').Require().Integer(),
                Param('sid').Require().Integer(),
                Param('key').Require().String(),  # 键
            ], [
                public.validate.trim_filter(),
            ])
        except Exception as ex:
            public.print_log("error info: {}".format(ex))
            return public.return_message(-1, 0, str(ex))

        sid = args.get('sid/d', 0)

        redis_obj = self.get_obj_by_sid(sid).redis_conn(args.db_idx)
        if redis_obj is False:
            return public.fail_v2(public.lang("redis connect fail!"))
        redis_obj.delete(args.key)

        return public.return_message(0, 0, public.lang("Operation is successful"))

    def clear_flushdb(self, args):
        """
        清空数据库
        @ids 清空数据库列表，不传则清空所有
        """
        # 校验参数
        try:
            args.validate([

                Param('ids').String(),  # "ids":"[0,1]"
                Param('sid').Require().Integer(),
            ], [
                public.validate.trim_filter(),
            ])
        except Exception as ex:
            public.print_log("error info: {}".format(ex))
            return public.return_message(-1, 0, str(ex))

        sid = args.get('sid/d', 0)
        ids = json.loads(args.ids)
        # ids = []
        if len(ids) == 0:
            for x in range(0, self._db_num):
                ids.append(x)
        redis_obj = self.get_obj_by_sid(sid).redis_conn(0)
        if redis_obj is False:
            return public.fail_v2(public.lang("redis connect fail!"))
        for x in ids:
            redis_obj = self.get_obj_by_sid(sid).redis_conn(x)
            redis_obj.flushdb()

        return public.return_message(0, 0, public.lang("Operation is successful"))

    def get_db_keylist(self, args):
        """
        @获取指定数据库key集合
        """
        # 校验参数
        try:
            args.validate([
                Param('db_type').Integer(),
                Param('db_idx').Require().Integer(),
                Param('limit').Integer(),
                Param('p').Integer(),
                Param('search').String(),
                Param('tojs').String(),  # 不知道
            ], [
                public.validate.trim_filter(),
            ])
        except Exception as ex:
            public.print_log("error info: {}".format(ex))
            return public.return_message(-1, 0, str(ex))

        search = '*'
        if 'search' in args: search = "*" + args.search + "*"
        db_idx = args.db_idx
        sid = args.get('sid/d', 0)

        redis_obj = self.get_obj_by_sid(sid).redis_conn(db_idx)
        if redis_obj is False:
            return public.fail_v2(public.lang("redis connect fail!"))
        try:
            total = redis_obj.dbsize()
        except Exception as err:
            if str(err).find("Connection refused"):
                return public.fail_v2(
                    public.lang(f"redis connection failed, please check if the database service is started!"))
            return public.fail_v2(
                public.lang(f"redis connection failed, please check if the database service is started!{err}"))
        info = {'p': 1, 'row': 20, 'count': total}

        if hasattr(args, 'limit'): info['row'] = int(args.limit)
        if hasattr(args, 'p'): info['p'] = int(args['p'])

        try:

            if search != '*':
                keylist = redis_obj.keys(search)
                info['count'] = len(keylist)
            else:
                keys = redis_obj.scan(match="{}".format(search), count=info['p'] * info['row'])
                keylist = keys[1]
        except:
            keylist = []

        info = {'p': 1, 'row': 10, 'count': len(keylist)}

        if hasattr(args, 'limit'): info['row'] = int(args.limit)
        if hasattr(args, 'p'): info['p'] = int(args['p'])

        import page
        # 实例化分页类
        page = page.Page()

        info['uri'] = args
        info['return_js'] = ''
        if hasattr(args, 'tojs'):
            info['return_js'] = args.tojs

        slist = keylist[(info['p'] - 1) * info['row']:info['p'] * info['row']]

        rdata = {}
        rdata['page'] = page.GetPage(info, '1,2,3,4,5,8')
        rdata['where'] = ''
        rdata['data'] = []

        from datetime import timedelta

        idx = 0
        for key in slist:
            item = {}
            try:
                item['name'] = key.decode()
            except:
                item['name'] = str(key)

            item['endtime'] = redis_obj.ttl(key)
            if item['endtime'] == -1:
                item['endtime'] = 0
                item['showtime'] = "royalty-free"
            else:
                key_ttl = redis_obj.ttl(key)
                INT_MAX = 2147483647
                INT_MIN = -2147483648
                if key_ttl > INT_MAX or key_ttl < INT_MIN:
                    item['showtime'] = str(key_ttl) + "second"
                else:
                    delta = timedelta(seconds=key_ttl)
                    days, remainder = divmod(delta.total_seconds(), 86400)
                    hours, remainder = divmod(remainder, 3600)
                    minutes, seconds = divmod(remainder, 60)
                    formatted_ttl = f"{int(days)}days{int(hours)}hours{int(minutes)}min{int(seconds)}second"
                    item['showtime'] = str(formatted_ttl)

            item['type'] = redis_obj.type(key).decode()

            if item['type'] == 'string':
                try:
                    item['val'] = redis_obj.get(key).decode()
                except:
                    item['val'] = str(redis_obj.get(key))
            elif item['type'] == 'hash':
                if redis_obj.hlen(key) > 500:
                    item['val'] = "The amount of data is too large to display!Total {} entries".format(
                        redis_obj.hlen(key))
                else:
                    item['val'] = str(redis_obj.hgetall(key))
            elif item['type'] == 'list':
                if redis_obj.llen(key) > 500:
                    item['val'] = "The amount of data is too large to display!Total {} entries".format(
                        redis_obj.llen(key))
                else:
                    item['val'] = str(redis_obj.lrange(key, 0, -1))
            elif item['type'] == 'set':
                if redis_obj.scard(key) > 500:
                    item['val'] = "The amount of data is too large to display!Total {} entries".format(
                        redis_obj.scard(key))
                else:
                    item['val'] = str(redis_obj.smembers(key))
            elif item['type'] == 'zset':
                if redis_obj.zcard(key) > 500:
                    item['val'] = "The amount of data is too large to display!Total {} entries".format(
                        redis_obj.zcard(key))
                else:
                    item['val'] = str(redis_obj.zrange(key, 0, -1, withscores=True))
            else:
                item['val'] = ''
            try:
                item['len'] = redis_obj.strlen(key)
            except:
                item['len'] = len(item['val'])
            item['val'] = self.local_xsssec(item['val'])
            item['name'] = public.xsssec(item['name'])
            rdata['data'].append(item)
            idx += 1
        return public.return_message(0, 0, rdata)

    # 备份数据库
    def ToBackup(self, args):
        """
        @备份数据库
        """

        # 校验参数
        try:
            args.validate([
                Param('sid').Require().Integer(),
            ], [
                public.validate.trim_filter(),
            ])
        except Exception as ex:
            public.print_log("error info: {}".format(ex))
            return public.return_message(-1, 0, str(ex))
        sid = args.get('sid/d', 0)
        if sid != 0:
            return public.fail_v2(public.lang("Backing up remote databases is not supported at this time!"))

        db_fidx = None
        if not hasattr(args, "db_idx"):
            db_fname = "all_db"
        else:
            db_fidx = args.db_idx
            db_fname = "db_{}".format(db_fidx)

        redis_obj = self.get_obj_by_sid(sid)
        if redis_obj.redis_conn(0) is False:
            return public.fail_v2(public.lang("redis connect fail!"))

        if db_fidx:
            redis_obj.redis_conn(0).execute_command("SELECT", int(db_fidx))
            redis_obj.redis_conn(0).execute_command("SAVE")
        else:
            for db_idx in range(0, self._db_num):
                redis_obj.redis_conn(db_idx).save()

        redis_obj = redis_obj.redis_conn(0)
        src_path = os.path.join(redis_obj.config_get().get("dir", ""), "dump.rdb")
        if not os.path.exists(src_path):
            return public.fail_v2(public.lang('BACKUP_ERROR'))

        file_name = "{db_fname}_{backup_time}_redis_data.rdb".format(db_fname=db_fname,
                                                                     backup_time=time.strftime("%Y-%m-%d_%H-%M-%S",
                                                                                               time.localtime()))
        file_path = os.path.join(self._REDIS_BACKUP_DIR, file_name)

        shutil.copyfile(src_path, file_path)
        if not os.path.exists(file_path):
            return public.fail_v2(public.lang('BACKUP_ERROR'))

        return public.success_v2(public.lang('BACKUP_SUCCESS'))

    def DelBackup(self, args):
        """
        @删除备份文件
        """
        # 校验参数
        try:
            args.validate([
                Param('file').Require().SafePath(),
                # Param('sid').Require().Integer(),
            ], [
                public.validate.trim_filter(),
            ])
        except Exception as ex:
            public.print_log("error info: {}".format(ex))
            return public.return_message(-1, 0, str(ex))

        file = args.file
        if os.path.exists(file):
            os.remove(file)

        return public.return_message(0, 0, public.lang("Delete successfully!"))

    def InputSql(self, get):
        """
        @导入数据库
        """

        # 校验参数
        try:
            get.validate([
                Param('file').Require().SafePath(),
                Param('sid').Require().Integer(),
            ], [
                public.validate.trim_filter(),
            ])
        except Exception as ex:
            public.print_log("error info: {}".format(ex))
            return public.return_message(-1, 0, str(ex))

        file = get.file
        sid = get.get('sid/d', 0)
        if not os.path.isfile(file):
            return public.fail_v2(public.lang("file not found"))

        redis_obj = self.get_obj_by_sid(sid).redis_conn(0)
        if redis_obj is False:
            return public.fail_v2(public.lang("redis connect fail"))

        rpath = redis_obj.config_get()['dir']
        dst_path = '{}/dump.rdb'.format(rpath)
        public.ExecShell("/etc/init.d/redis stop")
        if os.path.exists(dst_path): os.remove(dst_path)
        shutil.copy2(file, dst_path)
        public.ExecShell("chown redis.redis {dump} && chmod 644 {dump}".format(dump=dst_path))
        public.ExecShell("/etc/init.d/redis start")
        if os.path.exists(dst_path):
            return public.return_message(0, 0, public.lang("Restore Successful."))
        return public.return_message(-1, 0, public.lang("Restore failure."))

    def get_backup_list(self, get):
        """
        @获取备份文件列表
        """
        # 校验参数
        try:
            get.validate([
                Param('search').String(),
            ], [
                public.validate.trim_filter(),
            ])
        except Exception as ex:
            public.print_log("error info: {}".format(ex))
            return public.return_message(-1, 0, str(ex))

        def rd_file_info(f_path: str, arrs: list) -> dict:
            stat = os.stat(f_path)
            item = {
                'name': os.path.basename(f_path),
                'filepath': f_path,
                'size': stat.st_size,
                'mtime': int(stat.st_mtime),
                'sid': arrs[0],
            }
            try:
                if 0 <= int(arrs[0]) <= 15:
                    item['conn_config'] = cloud_list['id-' + str(arrs[0])]
            except ValueError:
                pass
            return item

        search = ''
        if hasattr(get, 'search'):
            search = get['search'].strip().lower()

        nlist = []
        cloud_list = {}
        for x in self.GetCloudServer({'type': 'redis'}).get("message", []):
            cloud_list['id-' + str(x['id'])] = x

        for name in os.listdir(self._REDIS_BACKUP_DIR):
            if search:
                if name.lower().find(search) == -1: continue

            file_path = os.path.join(self._REDIS_BACKUP_DIR, name).replace('//', '/')

            if os.path.isdir(file_path):
                for f in os.listdir(file_path):
                    f_path = os.path.join(file_path, f).replace('//', '/')
                    if os.path.isfile(f_path):
                        nlist.append(
                            rd_file_info(f_path, f.split('_'))
                        )
            elif os.path.isfile(file_path):
                nlist.append(
                    rd_file_info(file_path, name.split('_'))
                )
            else:
                continue

        if hasattr(get, 'sort'):
            nlist = sorted(nlist, key=lambda data: data['mtime'], reverse=get["sort"] == "desc")

        return public.return_message(0, 0, nlist)

    def restart_services(self):
        """
        @重启服务
        """
        public.ExecShell('net stop redis')
        public.ExecShell('net start redis')
        return True

    def check_cloud_database_status(self, conn_config):
        """
        @检测远程数据库是否连接
        @conn_config 远程数据库配置，包含host port pwd等信息
        """
        try:

            sql_obj = panelRedisDB().set_host(conn_config['db_host'], conn_config['db_port'], conn_config['db_name'],
                                              conn_config['db_user'], conn_config['db_password'])
            redis_obj = sql_obj.redis_conn(0)
            if redis_obj is False:
                return public.fail_v2(public.lang("redis connect fail"))
            keynum = redis_obj.dbsize()
            return True
        except Exception as ex:
            return public.fail_v2(public.lang("remote database connect fail {}".format(ex)))

    # 数据库状态检测
    def CheckDatabaseStatus(self, get):
        """
        数据库状态检测
        """
        if not hasattr(get, "sid"):
            return public.fail_v2("params not found! sid")
        if not str(get.sid).isdigit():
            return public.fail_v2("params not found! sid")
        sid = int(get.sid)

        if sid != 0:
            conn_config = public.M("database_servers").where("id=? AND LOWER(db_type)=LOWER('redis')",
                                                             (sid,)).find()
            if not conn_config:
                return public.fail_v2(public.lang("Remote database information does not exist！"))
            conn_config["db_name"] = None
            redis_obj = panelRedisDB().set_host(conn_config['db_host'], conn_config['db_port'],
                                                conn_config.get("db_name"), conn_config['db_user'],
                                                conn_config['db_password'])
        else:
            redis_obj = panelRedisDB()
        if redis_obj.redis_conn(0) is False:
            return {"status": True, "msg": "exceptions", "db_status": False}
        try:
            redis_obj.redis_conn(0).dbsize()
            db_status = True
        except:
            db_status = False
        return {"status": True, "msg": "normalcy" if db_status is True else "exceptions", "db_status": db_status}
