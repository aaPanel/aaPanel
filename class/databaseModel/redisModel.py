#coding: utf-8
#-------------------------------------------------------------------
# aaPanel
#-------------------------------------------------------------------
# Copyright (c) 2015-2099 aaPanel(www.aapanel.com) All rights reserved.
#-------------------------------------------------------------------
# Author: hwliang <hwl@aapanel.com>
#-------------------------------------------------------------------

# sqlite模型
#------------------------------
import os,re,json,shutil,time
from databaseModel.base import databaseBase
import public
try:
    import redis
except:
    public.ExecShell("btpip install redis")
    import redis
try:
    from BTPanel import session
except :pass


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

    def redis_conn(self,db_idx = 0):

        if self.__DB_HOST in ['127.0.0.1','localhost']:
            if not os.path.exists('/www/server/redis'): return False

        if not self.__DB_CLOUD:
            self.__DB_PASS = self.__config['requirepass']
            self.__DB_PORT = int(self.__config['port'])

        try:
            redis_pool = redis.ConnectionPool(host=self.__DB_HOST, port= self.__DB_PORT, password= self.__DB_PASS, db= db_idx)
            self.__DB_CONN = redis.Redis(connection_pool= redis_pool)
            return self.__DB_CONN
        except :
             self.__DB_ERR = public.get_error_info()
        return False


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


    #获取配置项
    def get_options(self,get = None):

        result = {}
        redis_conf = public.readFile("{}/redis/redis.conf".format(public.get_setup_path()))
        if not redis_conf: return False

        keys = ["bind","port","timeout","maxclients","databases","requirepass","maxmemory"]
        for k in keys:
            v = ""
            rep = "\n%s\\s+(.+)" % k
            group = re.search(rep,redis_conf)
            if not group:
                if k == "maxmemory":
                    v = "0"
                if k == "maxclients":
                    v = "10000"
                if k == "requirepass":
                    v = ""
            else:
                if k == "maxmemory":
                    v = int(group.group(1)) / 1024 / 1024
                else:
                    v = group.group(1)
            result[k] = v
        return result



class main(databaseBase):

    _db_max = 16  #最大redis数据库
    def __init__(self):
        pass



    def GetCloudServer(self,args):
        '''
            @name 获取远程服务器列表
            @author hwliang<2021-01-10>
            @return list
        '''
        return self.GetBaseCloudServer(args)
        # return public.return_message(0, 0,  self.GetBaseCloudServer(args))


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

    def get_obj_by_sid(self,sid = 0,conn_config = None):
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
            db_obj = panelRedisDB()

            try:
                db_obj = db_obj.set_host(conn_config['db_host'],conn_config['db_port'],None,conn_config['db_user'],conn_config['db_password'])
            except Exception as e:
                raise public.PanelError(e)
        else:
            db_obj = panelRedisDB()
        return db_obj



    def get_list(self,args):
        """
        @获取数据库列表
        @sql_type = redis
        """
        result = []
        self.sid = args.get('sid/d',0)
        for x in range(0,self._db_max):

            data = {}
            data['id'] = x
            data['name'] = 'DB{}'.format(x)


            try:
                redis_obj = self.get_obj_by_sid(self.sid).redis_conn(x)

                data['keynum'] = redis_obj.dbsize()
                if data['keynum'] > 0:
                    result.append(data)
            except :pass

        #result = sorted(result,key= lambda  x:x['keynum'],reverse=True)
        return result


    def set_redis_val(self,args):
        """
        @设置或修改指定值
        """

        self.sid = args.get('sid/d',0)
        if not 'name' in args or not 'val' in args:
            return public.returnMsg(False, public.lang("Parameter passing error."));

        endtime = 0
        if 'endtime' in args : endtime = int(args.endtime)

        redis_obj = self.get_obj_by_sid(self.sid).redis_conn(args.db_idx)
        if endtime:
            redis_obj.set(args.name, args.val, endtime)
        else:
            redis_obj.set(args.name, args.val)
        public.set_module_logs('linux_redis','set_redis_val',1)
        return public.returnMsg(True, public.lang("Operation is successful."));

    def del_redis_val(self,args):
        """
        @删除key值
        """
        self.sid = args.get('sid/d',0)
        if  not 'key' in args:
            return public.returnMsg(False, public.lang("Parameter passing error."));

        redis_obj = self.get_obj_by_sid(self.sid).redis_conn(args.db_idx)
        redis_obj.delete(args.key)

        return public.returnMsg(True, public.lang("Operation is successful."));


    def clear_flushdb(self,args):
        """
        清空数据库
        @ids 清空数据库列表，不传则清空所有
        """
        self.sid = args.get('sid/d',0)
        ids = json.loads(args.ids)
        #ids = []
        if len(ids) == 0:
             for x in range(0,self._db_max):
                 ids.append(x)

        for x in ids:
            redis_obj = self.get_obj_by_sid(self.sid).redis_conn(x)
            redis_obj.flushdb()

        return public.returnMsg(True, public.lang("Operation is successful."));

    def get_db_keylist(self,args):
        """
        @获取指定数据库key集合
        """

        search = '*'
        if 'search' in args: search = "*" + args.search+"*"
        db_idx = args.db_idx
        self.sid = args.get('sid/d',0)

        redis_obj = self.get_obj_by_sid(self.sid).redis_conn(db_idx)
        try:
            keylist = sorted(redis_obj.keys(search))
        except :
            keylist = []


        info = {'p':1,'row':10,'count':len(keylist)}

        if hasattr(args,'limit'): info['row'] = int(args.limit)
        if hasattr(args,'p'): info['p']  = int(args['p'])

        import page
        #实例化分页类
        page = page.Page();

        info['uri']   = args
        info['return_js'] = ''
        if hasattr(args,'tojs'): info['return_js']   = args.tojs

        slist = keylist[(info['p']-1) * info['row']:info['p'] * info['row']]

        rdata = {}
        rdata['page'] = page.GetPage(info,'1,2,3,4,5,8')
        rdata['where'] = ''
        rdata['data'] = []

        idx = 0
        for key in slist:
            item = {}
            try:
                item['name'] = key.decode()
            except:
                item['name'] = str(key)

            item['endtime'] = redis_obj.ttl(key)
            if item['endtime'] == -1: item['endtime'] = 0

            item['type'] = redis_obj.type(key).decode()

            if item['type'] == 'string':
                try:
                    item['val'] = redis_obj.get(key).decode()
                except:
                    item['val'] = str(redis_obj.get(key))
            elif item['type'] == 'hash':
                item['val'] = str(redis_obj.hgetall(key))
            elif item['type'] == 'list':
                item['val'] = str(redis_obj.lrange(key, 0, -1))
            elif item['type'] == 'set':
                item['val'] = str(redis_obj.smembers(key))
            elif item['type'] == 'zset':
                item['val'] = str(redis_obj.zrange(key, 0, 1, withscores=True))
            else:
                item['val'] = ''
            try:
                item['len'] = redis_obj.strlen(key)
            except:
                item['len'] = len(item['val'])
            item['val'] = public.xsssec(item['val'])
            item['name'] = public.xsssec(item['name'])
            rdata['data'].append(item)
            idx += 1
        return rdata


    def ToBackup(self,args):
        """
        @备份数据库
        """

        self.sid = args.get('sid/d',0)

        redis_obj = self.get_obj_by_sid(self.sid).redis_conn(0)
        redis_obj.save()

        src_path = '{}/dump.rdb'.format(redis_obj.config_get()['dir'])
        if not os.path.exists(src_path):
            return public.returnMsg(False, public.lang("Backup error"));

        backup_path = session['config']['backup_path'] + '/database/redis/'
        if not os.path.exists(backup_path): os.makedirs(backup_path)

        fileName = backup_path + str(self.sid) + '_db_' + time.strftime('%Y%m%d_%H%M%S',time.localtime()) +'.rdb'

        shutil.copyfile(src_path,fileName)
        if not os.path.exists(fileName):
            return public.returnMsg(False, public.lang("Backup error"));

        return public.returnMsg(True, public.lang("Backup Succeeded!"))

    def DelBackup(self,args):
        """
        @删除备份文件
        """
        file = args.file
        if os.path.exists(file): os.remove(file)

        return public.returnMsg(True, public.lang("Delete successfully!"));

    def InputSql(self,get):
        """
        @导入数据库
        """
        file = get.file
        self.sid = get.get('sid/d',0)

        redis_obj = self.get_obj_by_sid(self.sid).redis_conn(0)

        rpath = redis_obj.config_get()['dir']
        dst_path = '{}/dump.rdb'.format(rpath)
        public.ExecShell("/etc/init.d/redis stop")
        if os.path.exists(dst_path): os.remove(dst_path)
        shutil.copy2(file, dst_path)
        public.ExecShell("chown redis.redis {dump} && chmod 644 {dump}".format(dump=dst_path))
        # self.restart_services()
        public.ExecShell("/etc/init.d/redis start")
        if os.path.exists(dst_path):
            return public.returnMsg(True, public.lang("Restore Successful."))
        return public.returnMsg(False, public.lang("Restore failure."))


    def get_backup_list(self,get):
        """
        @获取备份文件列表
        """
        search = ''
        if hasattr(get,'search'): search = get['search'].strip().lower();


        nlist = []
        cloud_list = {}
        for x in self.GetCloudServer({'type':'redis'}):
            cloud_list['id-' + str(x['id'])] = x

        path  = session['config']['backup_path'] + '/database/redis/'
        if not os.path.exists(path): os.makedirs(path)
        for name in os.listdir(path):
            if search:
                if name.lower().find(search) == -1: continue;

            arrs = name.split('_')

            filepath = '{}/{}'.format(path,name).replace('//','/')
            stat = os.stat(filepath)

            item = {}
            item['name'] = name
            item['filepath'] = filepath
            item['size'] = stat.st_size
            item['mtime'] = int(stat.st_mtime)
            item['sid'] = arrs[0]
            item['conn_config'] = cloud_list['id-' + str(arrs[0])]

            nlist.append(item)
        if hasattr(get, 'sort'):
            nlist = sorted(nlist, key=lambda data: data['mtime'], reverse=get["sort"] == "desc")
        return nlist



    def restart_services(self):
        """
        @重启服务
        """
        public.ExecShell('net stop redis')
        public.ExecShell('net start redis')
        return True


    def check_cloud_database_status(self,conn_config):
        """
        @检测远程数据库是否连接
        @conn_config 远程数据库配置，包含host port pwd等信息
        """
        try:

            sql_obj = panelRedisDB().set_host(conn_config['db_host'],conn_config['db_port'],conn_config['db_name'],conn_config['db_user'],conn_config['db_password'])
            keynum = sql_obj.redis_conn(0).dbsize()
            return True
        except Exception as ex:

            return public.returnMsg(False,ex)
