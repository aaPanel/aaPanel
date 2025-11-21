#coding: utf-8
# +-------------------------------------------------------------------
# | aaPanel
# +-------------------------------------------------------------------
# | Copyright (c) 2015-2016 aaPanel(www.aapanel.com) All rights reserved.
# +-------------------------------------------------------------------
# | Author: hwliang <hwl@aapanel.com>
# +-------------------------------------------------------------------
import sys,os,re,time
if not 'class/' in sys.path:
    sys.path.insert(0,'class/')
import db,public,panelMysql
import json
import public
class data:
    __ERROR_COUNT = 0
    #自定义排序字段
    __SORT_DATA = ['site_ssl','php_version','backup_count']
    DB_MySQL = None
    web_server = None
    setupPath = '/www/server'
    siteorder_path = '/www/server/panel/data/siteorder.pl'
    limit_path = '/www/server/panel/data/limit.pl'

    # 删除排序记录
    def del_sorted(self, get):
        public.ExecShell("rm -rf {}".format(self.siteorder_path))
        return public.returnMsg(True, public.lang("Clear sorting successfully"))


    '''
     * 设置备注信息
     * @param String _GET['tab'] 数据库表名
     * @param String _GET['id'] 条件ID
     * @return Bool
    '''
    def setPs(self,get):
        id = get.id
        get.ps = public.xssencode2(get.ps)
        if public.M(get.table).where("id=?",(id,)).setField('ps',get.ps):
            return public.return_msg_gettext(True, public.lang("Setup successfully!"))
        return public.return_msg_gettext(False, public.lang("Failed to modify"))

    #端口扫描
    def CheckPort(self,port):
        import socket
        localIP = '127.0.0.1'
        temp = {}
        temp['port'] = port
        temp['local'] = True
        try:
            s = socket.socket()
            s.settimeout(0.01)
            s.connect((localIP,port))
            s.close()
        except:
            temp['local'] = False

        result = 0
        if temp['local']: result +=2
        return result

    # 转换时间
    def strf_date(self, sdate):
        return time.strftime('%Y-%m-%d', time.strptime(sdate, '%Y%m%d%H%M%S'))

    def get_cert_end(self,pem_file):
        try:
            import OpenSSL
            result = {}
            x509 = OpenSSL.crypto.load_certificate(
                OpenSSL.crypto.FILETYPE_PEM, public.readFile(pem_file))
            # 取产品名称
            issuer = x509.get_issuer()
            result['issuer'] = ''
            if hasattr(issuer, 'CN'):
                result['issuer'] = issuer.CN
            if not result['issuer']:
                is_key = [b'0', '0']
                issue_comp = issuer.get_components()
                if len(issue_comp) == 1:
                    is_key = [b'CN', 'CN']
                for iss in issue_comp:
                    if iss[0] in is_key:
                        result['issuer'] = iss[1].decode()
                        break
            # 取到期时间
            result['notAfter'] = self.strf_date(
                bytes.decode(x509.get_notAfter())[:-1])
            # 取申请时间
            result['notBefore'] = self.strf_date(
                bytes.decode(x509.get_notBefore())[:-1])
            # 取可选名称
            result['dns'] = []
            for i in range(x509.get_extension_count()):
                s_name = x509.get_extension(i)
                if s_name.get_short_name() in [b'subjectAltName', 'subjectAltName']:
                    s_dns = str(s_name).split(',')
                    for d in s_dns:
                        result['dns'].append(d.split(':')[1])
            subject = x509.get_subject().get_components()
            # 取主要认证名称
            if len(subject) == 1:
                result['subject'] = subject[0][1].decode()
            else:
                result['subject'] = result['dns'][0]
            return result
        except:
            return public.get_cert_data(pem_file)


    def get_site_ssl_info(self,siteName):
        try:
            s_file = 'vhost/nginx/{}.conf'.format(siteName)
            is_apache = False
            if not os.path.exists(s_file):
                s_file = 'vhost/apache/{}.conf'.format(siteName)
                is_apache = True

            if not os.path.exists(s_file):
                return -1

            s_conf = public.readFile(s_file)
            if not s_conf: return -1
            ssl_file = None
            if is_apache:
                if s_conf.find('SSLCertificateFile') == -1:
                    return -1
                s_tmp = re.findall(r"SSLCertificateFile\s+(.+\.pem)",s_conf)
                if not s_tmp: return -1
                ssl_file = s_tmp[0]
            else:
                if s_conf.find('ssl_certificate') == -1:
                    return -1
                s_tmp = re.findall(r"ssl_certificate\s+(.+\.pem);",s_conf)
                if not s_tmp: return -1
                ssl_file = s_tmp[0]
            ssl_info = self.get_cert_end(ssl_file)
            if not ssl_info: return -1
            ssl_info['endtime'] = int(int(time.mktime(time.strptime(ssl_info['notAfter'], "%Y-%m-%d")) - time.time()) / 86400)
            return ssl_info
        except: return -1
        #return "{}:{}".format(ssl_info['issuer'],ssl_info['notAfter'])

    def get_php_version(self,siteName):
        try:

            if not self.web_server:
                self.web_server = public.get_webserver()

            conf = public.readFile(self.setupPath + '/panel/vhost/'+self.web_server+'/'+siteName+'.conf')
            if self.web_server == 'openlitespeed':
                conf = public.readFile(
                    self.setupPath + '/panel/vhost/' + self.web_server + '/detail/' + siteName + '.conf')
            if self.web_server == 'nginx':
                rep = r"enable-php-(\w{2,5})[-\w]*\.conf"
            elif self.web_server == 'apache':
                rep = r"php-cgi-(\w{2,5})\.sock"
            else:
                rep = r"path\s*/usr/local/lsws/lsphp(\d+)/bin/lsphp"
            tmp = re.search(rep,conf).groups()
            if tmp[0] == '00':
                return 'Static'
            if tmp[0] == 'other':
                return 'Other'

            return tmp[0][0] + '.' + tmp[0][1]
        except:
            return 'Static'

    def map_to_list(self,map_obj):
        try:
            if type(map_obj) != list and type(map_obj) != str: map_obj = list(map_obj)
            return map_obj
        except: return []

    def get_database_size(self,databaseName):
        try:
            if not self.DB_MySQL:self.DB_MySQL = panelMysql.panelMysql()
            db_size = self.map_to_list(self.DB_MySQL.query("select sum(DATA_LENGTH)+sum(INDEX_LENGTH) from information_schema.tables  where table_schema='{}'".format(databaseName)))[0][0]
            if not db_size: return 0
            return int(db_size)
        except:
            return 0

    def get_site_quota(self,path):
        '''
            @name 获取网站目录配额信息
            @author hwliang<2022-02-15>
            @param path<string> 网站目录
            @return dict
        '''
        res = {'size':0 ,'used':0 }
        try:
            from projectModel.quotaModel import main
            quota_info =  main().get_quota_path_list(get_path = path)
            if isinstance(quota_info,dict):
                return quota_info
            return res
        except: return res

    def get_database_quota(self,db_name):
        '''
            @name 获取网站目录配额信息
            @author hwliang<2022-02-15>
            @param path<string> 网站目录
            @return dict
        '''
        res = {'size':0 ,'used':0 }
        try:
            from projectModel.quotaModel import main
            quota_info = main().get_quota_mysql_list(get_name = db_name)
            if isinstance(quota_info,dict):
                return quota_info
            return res
        except: return res

    '''
     * 取数据列表
     * @param String _GET['tab'] 数据库表名
     * @param Int _GET['count'] 每页的数据行数
     * @param Int _GET['p'] 分页号  要取第几页数据
     * @return Json  page.分页数 , count.总行数   data.取回的数据
    '''
    def getData(self, get):
        # # net_flow_type = {
        # #     "total_flow": "总流量",
        # #     "7_day_total_flow": "近7天流量",
        # #     "one_day_total_flow": "近1天流量",
        # #     "one_hour_total_flow": "近1小时流量"
        # # }
        # # net_flow_json_file = "/www/server/panel/plugin/total/panel_net_flow.json"
        #
        # if get.table == 'sites':
        #     if not hasattr(get, 'order'):
        #         if os.path.exists(self.siteorder_path):
        #             order = public.readFile(self.siteorder_path)
        #             if order.split(' ')[0] in self.__SORT_DATA:
        #                 get.order = order
        #
        #     if not hasattr(get, 'limit') or get.limit == '' or int(get.limit) == 0:
        #         try:
        #             if os.path.exists(self.limit_path):
        #                 get.limit = int(public.readFile(self.limit_path))
        #             else:
        #                 get.limit = 20
        #         except:
        #             get.limit = 20
        # if "order" in get:
        #     order = get.order
        #     if get.table == 'sites':
        #         public.writeFile(self.siteorder_path, order)
        #     # o_list = order.split(' ')
        #     # net_flow_dict = {}
        #     # order_type = None
        #     # if o_list[0].strip() in net_flow_type.keys():
        #     #     # net_flow_dict["flow_type"] = o_list[0].strip()
        #     #     if len(o_list) > 1:
        #     #         order_type = o_list[1].strip()
        #     #     else:
        #     #         get.order = 'id desc'
        #     #     # net_flow_dict["order_type"] = order_type
        #         # public.writeFile(net_flow_json_file, json.dumps(net_flow_dict))
        # 如果网站列表包含 rname 字段排序  先检查表内是否有 rname字段
        if hasattr(get, "order") and get.table == 'sites':
            if get.order.startswith('rname'):
                data = public.M('sites').find()
                if 'rname' not in data.keys():
                    public.M('sites').execute("ALTER TABLE 'sites' ADD 'rname' text DEFAULT ''", ())
        table = get.table
        data = self.GetSql(get)
        SQL = public.M(table)
        user_Data = self.get_user_power()
        if user_Data != 'all' and table in ['sites', 'databases', 'ftps']:
            data['data'] = [i for i in data['data'] if str(i['id']) in user_Data.get(table, [])]

        try:
            # table = get.table
            # data = self.GetSql(get)
            # SQL = public.M(table)
            if table == 'backup':
                import os
                backup_path = public.M('config').where('id=?',(1,)).getField('backup_path')
                for i in range(len(data['data'])):
                    if data['data'][i]['size'] == 0:
                        if os.path.exists(data['data'][i]['filename']):
                            data['data'][i]['size'] = os.path.getsize(data['data'][i]['filename'])
                    else:
                        if not os.path.exists(data['data'][i]['filename']):
                            if (data['data'][i]['filename'].find('/www/') != -1 or data['data'][i]['filename'].find(backup_path) != -1) and data['data'][i]['filename'][0] == '/' and data['data'][i]['filename'].find('|') == -1:
                                data['data'][i]['size'] = 0
                                data['data'][i]['ps'] = '文件不存在'
                    if data['data'][i]['ps'] in ['','无']:
                        if data['data'][i]['name'][:3] == 'db_' or (data['data'][i]['name'][:4] == 'web_' and data['data'][i]['name'][-7:] == '.tar.gz'):
                            data['data'][i]['ps'] = '自动备份'
                        else:
                            data['data'][i]['ps'] = '手动备份'
                    #判断本地文件是否存在，以确定能否下载
                    data['data'][i]['local']=data['data'][i]['filename'].split('|')[0]
                    data['data'][i]['localexist']=0 if os.path.isfile(data['data'][i]['local']) else 1

            elif table == 'sites' or table == 'databases':
                type = '0'
                if table == 'databases':
                    type = '1'
                for i in range(len(data['data'])):
                    backup_count = 0
                    try:
                        backup_count = SQL.table('backup').where("pid=? AND type=?",(data['data'][i]['id'],type)).count()
                    except:pass


                    data['data'][i]['backup_count'] = backup_count
                    if table == 'databases': data['data'][i]['conn_config'] = json.loads(data['data'][i]['conn_config'])
                    data['data'][i]['quota'] = self.get_database_quota(data['data'][i]['name'])

                if table == 'sites':
                    for i in range(len(data['data'])):

                        data['data'][i]['domain'] = SQL.table('domain').where("pid=?",(data['data'][i]['id'],)).count()
                        # data['data'][i]['ssl'] = self.get_site_ssl_info(data['data'][i]['name'])

                        ssl_info = self.get_site_ssl_info(data['data'][i]['name'])
                        data['data'][i]['ssl'] = ssl_info
                        data['data'][i]['site_ssl'] = ssl_info['endtime'] if ssl_info != -1 else -1

                        data['data'][i]['php_version'] = self.get_php_version(data['data'][i]['name'])
                        data['data'][i]['attack'] = self.get_analysis(get,data['data'][i])
                        data['data'][i]['project_type'] = SQL.table('sites').where('id=?',(data['data'][i]['id'])).field('project_type').find()['project_type']
                        if data['data'][i]['project_type'] == 'WP':
                            import one_key_wp
                            data['data'][i]['cache_status'] = one_key_wp.one_key_wp().get_cache_status(data['data'][i]['id'])
                        if not data['data'][i]['status'] in ['0','1',0,1]:
                            data['data'][i]['status'] = '1'
                        data['data'][i]['quota'] = self.get_site_quota(data['data'][i]['path'])
                        site1 = SQL.table('sites').where('id=?', (data['data'][i]['id'])).find()
                        if hasattr(site1, 'rname'):
                            data['data'][i]['rname'] = \
                            SQL.table('sites').where('id=?', (data['data'][i]['id'])).field('rname').find()['rname']
                        if not data['data'][i].get('rname', ''):
                            data['data'][i]['rname'] = data['data'][i]['name']
                        data["net_flow_info"] = {}
                    # try:
                    #     net_flow_json_info = json.loads(public.readFile(net_flow_json_file))
                    #     data["net_flow_info"] = net_flow_json_info
                    # except Exception:
                    #     data["net_flow_info"] = {}


            elif table == 'firewall':
                for i in range(len(data['data'])):
                    if data['data'][i]['port'].find(':') != -1 or data['data'][i]['port'].find('.') != -1 or data['data'][i]['port'].find('-') != -1:
                        data['data'][i]['status'] = -1
                    else:
                        data['data'][i]['status'] = self.CheckPort(int(data['data'][i]['port']))

            elif table == 'ftps':
                 for i in range(len(data['data'])):
                     data['data'][i]['quota'] = self.get_site_quota(data['data'][i]['path'])

            try:
                for _find in data['data']:
                    _keys = _find.keys()
                    for _key in _keys:
                        _find[_key] = public.xsssec(_find[_key])
            except:
                pass

            #返回
            return self.get_sort_data(data)
        except:
            return public.get_error_info()

    def get_data_list(self, get):

            try:
                self.check_and_add_stop_column()
                if get.table == 'sites':
                    if not hasattr(get, 'order'):
                        if os.path.exists(self.siteorder_path):
                            order = public.readFile(self.siteorder_path)
                            if order.split(' ')[0] in self.__SORT_DATA:
                                get.order = order
                    else:
                        public.writeFile(self.siteorder_path, get.order)
                    if not hasattr(get, 'limit') or get.limit == '' or int(get.limit) == 0:
                        try:
                            if os.path.exists(self.limit_path):
                                get.limit = int(public.readFile(self.limit_path))
                            else:
                                get.limit = 20
                        except:
                            get.limit = 20
                    else:
                        public.writeFile(self.limit_path, get.limit)
                if not hasattr(get, 'order'):
                    get.order = 'addtime desc'
                get = self._get_args(get)
                try:
                    s_list = self.func_models(get, 'get_data_where')
                except:
                    s_list = []

                where_sql, params = self.get_where(get, s_list)
                data = self.get_page_data(get, where_sql, params)
                get.data_list = data['data']
                try:
                    data['data'] = self.func_models(get, 'get_data_list')
                except :
                    print(traceback.format_exc())
                if get.table == 'sites':
                    if isinstance(data, dict):
                        file_path = os.path.join(public.get_panel_path(), "data/sort_list.json")
                        if os.path.exists(file_path):
                            sort_list_raw = public.readFile(file_path)
                            sort_list = json.loads(sort_list_raw)
                            sort_list_int = [int(item) for item in sort_list["list"]]

                            for i in range(len(data['data'])):
                                if int(data['data'][i]['id']) in sort_list_int:
                                    data['data'][i]['sort'] = 1
                                else:
                                    data['data'][i]['sort'] = 0

                            top_list = sort_list["list"]
                            if top_list:
                                top_list = top_list[::-1]
                            top_data = [item for item in data["data"] if str(item['id']) in top_list]
                            data1 = [item for item in data["data"] if str(item['id']) not in top_list]
                            top_data.sort(key=lambda x: top_list.index(str(x['id'])))
                            data['data'] = top_data + data1
                public.set_search_history(get.table, get.search_key, get.search)  # 记录搜索历史
                # 字段排序
                data = self.get_sort_data(data)
                if 'type_id' in get:
                    type_id=int(get['type_id'])
                    if type_id:
                        filtered_data = []
                        target_type_id = type_id
                        # print(data['data'])
                        for item in data['data']:
                            if item.get('type_id') == target_type_id:
                                filtered_data.append(item)
                        data['data'] = filtered_data
                    if get.get("db_type",""):
                        if  type_id < 0:
                            filtered_data = []
                            target_type_id = type_id
                            for item in data['data']:
                                if item.get('type_id') == target_type_id:
                                    filtered_data.append(item)
                            data['data'] = filtered_data
                return data
            except:
                return traceback.format_exc()


    # 获取用户权限列表
    def get_user_power(self, get=None):
        user_Data = 'all'
        try:
            uid = session.get('uid')
            if uid != 1 and uid:
                plugin_path = '/www/server/panel/plugin/users'
                if os.path.exists(plugin_path):
                    user_authority = os.path.join(plugin_path, 'authority')
                    if os.path.exists(user_authority):
                        if os.path.exists(os.path.join(user_authority, str(uid))):
                            try:
                                data = json.loads(self._decrypt(public.ReadFile(os.path.join(user_authority, str(uid)))))
                                if data['role'] == 'administrator':
                                    user_Data = 'all'
                                else:
                                    user_Data = json.loads(self._decrypt(public.ReadFile(os.path.join(user_authority, str(uid) + '.data'))))
                            except:
                                user_Data = {}
                        else:
                            user_Data = {}
        except:
            pass
        return user_Data


    def get_sort_data(self,data):
        """
        @获取自定义排序数据
        @param data: 数据
        """
        if 'plist' in data:
            plist = data['plist']
            o_list = plist['order'].split(' ')

            reverse = False
            sort_key = o_list[0].strip()

            if o_list[1].strip()  == 'desc':
                reverse = True

            if sort_key in ['site_ssl']:
                for info in data['data']:
                    if type(info['ssl']) == int:
                        info[sort_key] = info['ssl']
                    else:
                        try:
                           info[sort_key] = info['ssl']['endtime']
                        except :
                           info[sort_key] = ''

            data['data'] = sorted(data['data'],key=lambda x:x[sort_key],reverse=reverse)
            data['data'] = data['data'][plist['shift'] : plist['row'] ]
        return data

    '''
     * 取数据库行
     * @param String _GET['tab'] 数据库表名
     * @param Int _GET['id'] 索引ID
     * @return Json
    '''
    def getFind(self,get):
        tableName = get.table
        id = get.id
        field = self.GetField(get.table)
        SQL = public.M(tableName)
        where = "id=?"
        find = SQL.where(where,(id,)).field(field).find()
        try:
            _keys = find.keys()
            for _key in _keys:
                find[_key] = public.xsssec(find[_key])
        except:
            pass
        return find


    '''
     * 取字段值
     * @param String _GET['tab'] 数据库表名
     * @param String _GET['key'] 字段
     * @param String _GET['id'] 条件ID
     * @return String
    '''
    def getKey(self,get):
        tableName = get.table
        keyName = get.key
        id = get.id
        SQL = db.Sql().table(tableName)
        where = "id=?"
        result = SQL.where(where,(id,)).getField(keyName)
        if type(result) == str:
            result = public.xsssec(result)
        return result

    '''
     * 获取数据与分页
     * @param string table 表
     * @param string where 查询条件
     * @param int limit 每页行数
     * @param mixed result 定义分页数据结构
     * @return array
    '''
    def GetSql(self,get,result = '1,2,3,4,5,8'):
        #判断前端是否传入参数
        order = 'id desc'
        if hasattr(get,'order'):
            # 验证参数格式
            if re.match(r"^[\w\s\-\.]+$",get.order):
                order = get.order

        search_key = 'get_list'
        limit = 20
        if hasattr(get,'limit'):
            limit = int(get.limit)
            if limit < 1: limit = 20

        if hasattr(get,'result'):
            # 验证参数格式
            if re.match(r"^[\d\,]+$",get.result):
                result = get.result

        SQL = db.Sql()
        data = {}
        #取查询条件
        where = ''
        search = ''
        param = ()
        if hasattr(get,'search'):
            search = get.search
            if sys.version_info[0] == 2: get.search = get.search.encode('utf-8')
            where,param = self.GetWhere(get.table,get.search)
            if get.table == 'backup':
                where += " and type='{}'".format(int(get.type))

            if get.table == 'sites' and get.search:
                conditions = ''
                if '_' in get.search:
                    cs = ''
                    for i in get.search:
                        if i == '_':
                            cs += '/_'
                        else:
                            cs += i
                    get.search = cs
                    conditions = " escape '/'"
                pid = SQL.table('domain').where("name LIKE ?{}".format(conditions),("%{}%".format(get.search),)).getField('pid')
                if pid:
                    if where:
                        where += " or id=" + str(pid)
                    else:
                        where += "id=" + str(pid)

        if get.table == 'sites':
            search_key = 'php'
            if where:
                where = "({}) AND (project_type='PHP' OR project_type='WP')".format(where)
            else:
                where = "(project_type='PHP' OR project_type='WP')"

            if hasattr(get,'type'):
                if get.type != '-1':
                    where += " AND type_id={}".format(int(get.type))

        if get.table == 'databases':
            if hasattr(get,'db_type'):
                if where:
                    where += " AND db_type='{}'".format(int(get.db_type))
                else:
                    where = "db_type='{}'".format(int(get.db_type))
            if hasattr(get,'sid'):
                if where:
                    where += " AND sid='{}'".format(int(get.sid))
                else:
                    where = "sid='{}'".format(int(get.sid))

            if where:
                where += " and type='MySQL'"
            else:
                where = 'type = "MySQL"'

        field = self.GetField(get.table)
        #实例化数据库对象

        public.set_search_history(get.table,search_key,search)  #记录搜索历史

        #是否直接返回所有列表
        if hasattr(get,'list'):
            data = SQL.table(get.table).where(where,param).field(field).order(order).select()
            return data

        #取总行数
        count = SQL.table(get.table).where(where,param).count()
        #get.uri = get
        #包含分页类
        import page
        #实例化分页类
        page = page.Page()

        info = {}
        info['count'] = count
        info['row']   = limit

        info['p'] = 1
        if hasattr(get,'p'):
            info['p']     = int(get['p'])
            if info['p'] <1: info['p'] = 1

        try:
            from flask import request
            info['uri']   = public.url_encode(request.full_path)
        except:
            info['uri'] = ''
        info['return_js'] = ''
        if hasattr(get,'tojs'):
            if re.match(r"^[\w\.\-]+$",get.tojs):
                info['return_js']   = get.tojs

        data['where'] = where

        #获取分页数据
        data['page'] = page.GetPage(info,result)
        #取出数据
        #data['data'] = SQL.table(get.table).where(where,param).order(order).field(field).limit(str(page.SHIFT)+','+str(page.ROW)).select()

        o_list = order.split(' ')
        if o_list[0] in self.__SORT_DATA:
            data['data'] = SQL.table(get.table).where(where,param).field(field).select()
            data['plist'] = {'shift':page.SHIFT,'row':page.ROW,'order':order}
        else:
            data['data'] = SQL.table(get.table).where(where,param).order(order).field(field).limit(str(page.SHIFT)+','+str(page.ROW)).select()      #取出数据

        data['search_history'] =  public.get_search_history(get.table,search_key)

        return data

    #获取条件
    def GetWhere(self,tableName,search):
        if not search: return "",()

        if type(search) == bytes: search = search.encode('utf-8').strip()
        try:
            search = re.search(r"[\w\x80-\xff\.\_\-]+",search).group()
        except:
            return '',()
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
        wheres = {
            'sites': ("name LIKE ? OR ps LIKE ?{}".format(conditions), ('%' + search + '%', '%' + search + '%')),
            'ftps': ("name LIKE ? OR ps LIKE ?{}".format(conditions), ('%' + search + '%', '%' + search + '%')),
            'databases': (
                "(name LIKE ? {} OR ps LIKE ?{})".format(conditions, conditions),
                ("%" + search + "%", "%" + search + "%")),
            'crontab': ("name LIKE ?{}".format(conditions), ('%' + (search) + '%')),
            'logs': ("username=? OR type LIKE ?{} OR log LIKE ?{}".format(conditions, conditions),
                     (search, '%' + search + '%', '%' + search + '%')),
            'backup'    :   ("pid=?",(search,)),
            'users'     :   ("id='?' OR username=?",(search,search)),
            'domain'    :   ("pid=? OR name=?",(search,search)),
            'tasks'     :   ("status=? OR type=?",(search,search)),
            }

        # wheres = {
        #     'sites'     :   ("name LIKE ? OR ps LIKE ?",('%'+search+'%','%'+search+'%')),
        #     'ftps'      :   ("name LIKE ? OR ps LIKE ?",('%'+search+'%','%'+search+'%')),
        #     'databases' :   ("(name LIKE ? OR ps LIKE ?)",("%"+search+"%","%"+search+"%")),
        #     'logs'      :   ("username=? OR type LIKE ? OR log LIKE ?",(search,'%'+search+'%','%'+search+'%')),
        #     'backup'    :   ("pid=?",(search,)),
        #     'users'     :   ("id='?' OR username=?",(search,search)),
        #     'domain'    :   ("pid=? OR name=?",(search,search)),
        #     'tasks'     :   ("status=? OR type=?",(search,search)),
        #     }

        try:
            return wheres[tableName]
        except:
            return '',()

    # 获取返回的字段
    def GetField(self,tableName):
        fields = {
            'sites'     :   "id,name,path,status,ps,addtime,edate",
            'ftps'      :   "id,pid,name,password,status,ps,addtime,path",
            'databases' :   "id,sid,pid,name,username,password,accept,ps,addtime,db_type,conn_config",
            'logs'      :   "id,uid,username,type,log,addtime",
            'backup'    :   "id,pid,name,filename,addtime,size,ps",
            'users'     :   "id,username,phone,email,login_ip,login_time",
            'firewall'  :   "id,port,ps,addtime",
            'domain'    :   "id,pid,name,port,addtime",
            'tasks'     :   "id,name,type,status,addtime,start,end"
            }
        try:
            return fields[tableName]
        except:
            return ''

    def get_analysis(self,get,i):
        import log_analysis
        get.path = '/www/wwwlogs/{}.log'.format(i['name'])
        get.action = 'get_result'
        data = log_analysis.log_analysis().get_result(get)
        return int(data['php']) + int(data['san']) + int(data['sql']) + int(data['xss'])