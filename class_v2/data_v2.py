#coding: utf-8
# +-------------------------------------------------------------------
# | aaPanel
# +-------------------------------------------------------------------
# | Copyright (c) 2015-2016 aaPanel(www.aapanel.com) All rights reserved.
# +-------------------------------------------------------------------
# | Author: hwliang <hwl@aapanel.com>
# +-------------------------------------------------------------------
import sys,os,re,time,json
from datetime import datetime, timedelta

import requests

if not 'class/' in sys.path:
    sys.path.insert(0,'class/')
import db,public,panelMysql
import json
import public
from public.validate import Param

try:
    from BTPanel import cache
except:
    cache = None

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
        # 校验参数
        try:
            get.validate([
                Param('table').Require().String(),
                Param('ps').Require().String(),
                Param('id').Require().Integer(),
            ], [
                public.validate.trim_filter(),
            ])
        except Exception as ex:
            public.print_log("error info: {}".format(ex))
            return public.return_message(-1, 0, str(ex))

        id = get.id
        get.ps = public.xssencode2(get.ps)
        if public.M(get.table).where("id=?",(id,)).setField('ps',get.ps):
            # public.get_msg_gettext(True, public.lang("Setup successfully!"))
            return public.return_message(0, 0, public.lang("Setup successfully"))
        # public.get_msg_gettext(False, public.lang("Failed to modify"))
        return public.return_message(-1, 0, public.lang("Failed to modify"))

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

    # 查询网站对应的PHP版本
    def get_php_version(self, siteName):
        try:

            if not self.web_server:
                self.web_server = public.get_webserver()

            detail = 'detail/' if self.web_server == 'openlitespeed' else ''
            sub = ''
            if '/' in siteName:
                parent_site_name = public.get_parent_site_name(siteName)
                if parent_site_name:
                    siteName = parent_site_name[0] + '/' + parent_site_name[1]
                sub = 'sub_dir/'

            conf_path = f"{self.setupPath}/panel/vhost/{self.web_server}/{detail}{sub}{siteName}.conf"
            conf = public.readFile(conf_path.replace('//', '/'))

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
        res = {
            "used": 0,
            "size": 0,
            "quota_push": {
                "size": 0,
                "used": 0,
            },
            "quota_storage": {
                "size": 0,
                "used": 0,
            }
        }
        try:
            from projectModelV2.quotaModel import main
            quota_info = main().get_quota_path(path)

            if isinstance(quota_info, dict):
                res.update(quota_info)
                res['size'] = int(quota_info['quota_push']['size']) + int(quota_info['quota_storage']['size'])
                return res
            return res
        except:
            # from traceback import format_exc
            # public.print_log(format_exc())
            return res
        #最新版本v2版本
        # try:
        #     from projectModelV2.quotaModel import main
        #     quota_info =  main().get_quota_path(path)
        #     if isinstance(quota_info,dict):
        #         return quota_info
        #     return res
        # except: return res

    def get_database_quota(self,db_name):
        '''
            @name 获取网站目录配额信息
            @author hwliang<2022-02-15>
            @param path<string> 网站目录
            @return dict
        '''
        res = {
            "used": 0,
            "size": 0,
            "quota_push": {
                "size": 0,
                "used": 0,
            },
            "quota_storage": {
                "size": 0,
                "used": 0,
            }
        }
        try:
            from projectModelV2.quotaModel import main
            quota_info = main().get_quota_mysql(db_name)

            if isinstance(quota_info, dict):
                res.update(quota_info)
                res['size'] = int(quota_info['quota_push']['size']) + int(quota_info['quota_storage']['size'])
                return res

            return res
        except:
            return res
        #最新版本v2版本
        # try:
        #     from projectModelV2.quotaModel import main
        #     quota_info = main().get_quota_mysql(db_name)
        #     if isinstance(quota_info,dict):
        #         return quota_info
        #     return res
        # except: return res

    '''
     * 取数据列表
     * @param String _GET['tab'] 数据库表名
     * @param Int _GET['count'] 每页的数据行数
     * @param Int _GET['p'] 分页号  要取第几页数据
     * @return Json  page.分页数 , count.总行数   data.取回的数据
    '''
    def getData(self, get):

        # 校验参数
        try:
            get.validate([
                Param('table').Require().String(),
                Param('search').String(),
                Param('limit').Integer(),
                Param('p').Integer(),
                Param('type').String(),
                Param('project_type'),
            ], [
                public.validate.trim_filter(),
            ])
        except Exception as ex:
            public.print_log("error info: {}".format(ex))
            return public.return_message(-1, 0, str(ex))

        # 如果网站列表包含 rname 字段排序  先检查表内是否有 rname字段
        if hasattr(get, "order") and get.table == 'sites':
            if get.order.startswith('rname'):
                data = public.M('sites').find()
                if 'rname' not in data.keys():
                    public.M('sites').execute("ALTER TABLE 'sites' ADD 'rname' text DEFAULT ''", ())
        # 先检查tasks表内是否有 install_status、message字段
        if get.table == 'tasks':
            data = public.M('tasks').find()
            if 'install_status' not in data.keys():
                public.M('tasks').execute("ALTER TABLE 'tasks' ADD 'install_status' INTEGER DEFAULT 1", ())
            if 'message' not in data.keys():
                public.M('tasks').execute("ALTER TABLE 'tasks' ADD 'message' TEXT DEFAULT ''", ())
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
                site_ids=[]
                if table == 'databases':
                    type = '1'
                for i in range(len(data['data'])):
                    #将data['data'][i]['id']添加到site_ids列表中
                    site_ids.append(data['data'][i]['id'])
                    if table == 'databases': data['data'][i]['conn_config'] = json.loads(data['data'][i]['conn_config'])
                    data['data'][i]['quota'] = self.get_database_quota(data['data'][i]['name'])
                try:
                    # 兼容wp备份时间，转换格式
                    if get.get('project_type','') == 'WP2':
                        backup_records = public.S('wordpress_backups').where_in('s_id', site_ids).group('s_id').field(
                            's_id', 'count(*) as cnt', 'max(bak_time) as last_backup_time').select()
                        backup_info_map = {}
                        for record in backup_records:
                            s_id = record['s_id']
                            last_backup_time = record['last_backup_time']
                            if isinstance(last_backup_time, (int, float)):
                                formatted_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(last_backup_time))
                            else:
                                try:
                                    formatted_time = last_backup_time.strftime("%Y-%m-%d %H:%M:%S")
                                except Exception:
                                    formatted_time = ''
                            formatted_record = {
                                's_id': s_id,
                                'cnt': record['cnt'],
                                'last_backup_time': formatted_time
                            }

                            # 添加到映射表
                            backup_info_map[s_id] = formatted_record
                    else:
                        backup_info_map = {j['pid']: j for j in public.S('backup').where_in('pid', site_ids).where("type", type).group('pid').field('pid','count(*) as cnt','max(addtime) as last_backup_time').select()}
                except Exception as e:
                    backup_info_map = {}

                for i in range(len(data['data'])): data['data'][i]['backup_count'] = backup_info_map.get(data['data'][i]['id'], {}).get("cnt", 0)

                if table == 'sites':
                    if get.get('project_type','') == 'WP2':
                        # 检测类型表，是否正确
                        import one_key_wp_v2
                        ok, msg = one_key_wp_v2.checklist_fields()
                        if not ok and msg== "no such table: wordpress_onekey":
                            return public.return_message(0, 0, msg)
                        elif not ok:
                            return public.return_message(-1, 0, msg)

                    # 获取网站类型
                    if get.get('site_type', ''):
                        site_sql = public.M("wordpress_onekey").select()
                        site_type = public.M("wp_site_types").where('`id` = ?', (get.get('site_type', ''),)).find()
                        filtered_data = []

                    # 加载网站图标
                    import os
                    multi_webservice_status = public.get_multi_webservice_status()
                    webservice = public.get_webserver()
                    nginx_b64_path = public.image_to_base64(os.path.join(public.get_panel_path(), "BTPanel/static/img/soft_ico/ico-nginx.png"))
                    apache_b64_path = public.image_to_base64(os.path.join(public.get_panel_path(), "BTPanel/static/img/apache.png"))
                    ols_b64_path = public.image_to_base64(os.path.join(public.get_panel_path(), "BTPanel/static/img/soft_ico/ico-openlitespeed.png"))

                    # 按流量排序
                    re_data = None
                    if get.get('re_order'):
                        re_data =  self.get_site_request(public.to_dict_obj({'site_type':'PHP'}))
                        if re_data['status'] == 0:
                            re_data = re_data['message']

                    for i in range(len(data['data'])):
                        # 添加流量排序
                        if re_data:
                            if data["data"][i]['name'] in re_data:
                                data['data'][i]['re_total'] = re_data[data["data"][i]['name']]['total']['request']
                            else:
                                data['data'][i]['re_total'] = 0

                        data["data"][i]["last_backup_time"] = backup_info_map.get(data['data'][i]['id'], {}).get("last_backup_time", "")

                        data['data'][i]['domain'] = SQL.table('domain').where("pid=?",(data['data'][i]['id'],)).count()
                        # data['data'][i]['ssl'] = self.get_site_ssl_info(data['data'][i]['name'])

                        ssl_info = self.get_site_ssl_info(data['data'][i]['name'])
                        data['data'][i]['ssl'] = ssl_info
                        data['data'][i]['site_ssl'] = ssl_info['endtime'] if ssl_info != -1 else -1

                        data['data'][i]['php_version'] = self.get_php_version(data['data'][i]['name'])
                        data['data'][i]['attack'] = self.get_analysis(get,data['data'][i])
                        data['data'][i]['project_type'] = SQL.table('sites').where('id=?',(data['data'][i]['id'])).field('project_type').find()['project_type']
                        data['data'][i]['ps']=data['data'][i]['ps'].replace("For panel Lets Encrypt certificate","For panel Let's Encrypt certificate",1)
                        if data['data'][i]['project_type'] in ['WP', 'WP2']:
                            import one_key_wp
                            one_key_wp_obj = one_key_wp.one_key_wp()
                            data['data'][i]['cache_status'] = False
                            data['data'][i]['wp_version'] = '0.0.0'
                            try:
                                data['data'][i]['cache_status'] = one_key_wp_obj.get_cache_status(data['data'][i]['id'])
                                data['data'][i]['wp_version'] = one_key_wp_obj.get_wp_version(data['data'][i]['id'])
                            except:
                                pass
                            data['data'][i]['login_url'] = '/v2/wp/login/{}'.format(data['data'][i]['id'])


                            if data['data'][i]['project_type'] == 'WP2':
                                from wp_toolkit import wpbackup
                                data['data'][i]['backup_count'] = wpbackup(data['data'][i]['id']).backup_count()
                                wordpress_scan_path = "/www/server/panel/data/wordpress_wp_scan.json"
                                data['data'][i]['scan']={"last_time": 0,"vulnerabilities": 0,"status": True}
                                import os
                                if os.path.exists(wordpress_scan_path):
                                    try:
                                        wordpress_scan_info = json.loads(public.readFile(wordpress_scan_path))
                                        if data['data'][i]['path'] in wordpress_scan_info:
                                            data['data'][i]['scan'] = wordpress_scan_info[data['data'][i]['path']]
                                    except:
                                        pass

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

                        # 网站图标
                        data['data'][i]['ico']=""
                        try:
                            import os
                            ico_b64_path = os.path.join(public.get_panel_path(), "data/site_favs", data['data'][i]['name'] + ".b64")

                            default = public.readFile(ico_b64_path) if os.path.exists(ico_b64_path) else ''

                            if multi_webservice_status:
                                if default:
                                    data['data'][i]['ico'] = default
                                elif 'apache' == data['data'][i]['service_type']:
                                    data['data'][i]['ico'] = apache_b64_path
                                elif 'nginx' == data['data'][i]['service_type'] or not data['data'][i]['service_type']:
                                    data['data'][i]['ico'] = nginx_b64_path
                                elif 'openlitespeed' == data['data'][i]['service_type']:
                                    data['data'][i]['ico'] = ols_b64_path
                                else:
                                    data['data'][i]['ico'] = default
                            else:
                                if default:
                                    data['data'][i]['ico'] = default
                                elif webservice == 'nginx':
                                    data['data'][i]['ico'] = nginx_b64_path
                                elif webservice == 'apache':
                                    data['data'][i]['ico'] = apache_b64_path
                                elif webservice == 'openlitespeed':
                                    data['data'][i]['ico'] = ols_b64_path
                                else:
                                    data['data'][i]['ico'] = default

                            # 判断是否启动类型筛选，启动后为数据添加类型
                            if get.get('site_type', ''):
                                for type_ in site_sql:
                                    if data['data'][i]['id'] == type_['s_id'] and site_type['name'] == type_[
                                        'site_type']:
                                        data['data'][i]['site_type'] = type_['site_type']
                                        filtered_data.append(data['data'][i])

                        except:
                            public.print_log(public.get_error_info())
                    # try:
                    #     net_flow_json_info = json.loads(public.readFile(net_flow_json_file))
                    #     data["net_flow_info"] = net_flow_json_info
                    # except Exception:
                    #     data["net_flow_info"] = {}

                    # 判断是否进行了类型筛选
                    if get.get('site_type', ''):
                        data['data'] = filtered_data

                    if get.get('re_order') and re_data:
                        if get.get('re_order') == 'desc':
                            data['data'] = sorted(data['data'], key=lambda x: x["re_total"], reverse=True)
                        else:
                            data['data']  = sorted(data['data'], key=lambda x: x["re_total"])

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
            res = self.get_sort_data(data)
            return public.return_message(0, 0, res)
        except:
            res = public.get_error_info()
            # return public.get_error_info()
            return public.return_message(0, 0, res)
            
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
            data['data'] = data['data'][plist['shift']: plist['shift'] + plist['row']]
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

        # 校验参数
        try:
            get.validate([
                Param('table').Require().String(),
                Param('key').Require().String(),
                Param('id').Require().Integer(),
            ], [
                public.validate.trim_filter(),
            ])
        except Exception as ex:
            public.print_log("error info: {}".format(ex))
            return public.return_message(-1, 0, str(ex))

        tableName = get.table
        keyName = get.key
        id = get.id
        SQL = db.Sql().table(tableName)
        where = "id=?"
        result = SQL.where(where,(id,)).getField(keyName)
        if result is None:
            return public.return_message(-1, 0, None)
        res = result
        if isinstance(result, str):
            res = public.xsssec(result)

        return public.return_message(0, 0, res)


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

            # 额外对 project_type 字段做处理
            if 'project_type' in get:
                extra_where = "`project_type` = '{}'".format(get.project_type)
                if where:
                    where = r"({}) AND {}".format(where, extra_where)
                else:
                    where = extra_where
            else:
                extra_where = "`project_type` IN ('PHP', 'WP')"
                if where:
                    where = r"({}) AND {}".format(where, extra_where)
                else:
                    where = extra_where

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
            'sites'     :   "id,name,path,status,ps,addtime,edate,service_type",
            'ftps'      :   "id,pid,name,password,status,ps,addtime,path",
            'databases' :   "id,sid,pid,name,username,password,accept,ps,addtime,db_type,conn_config",
            'logs'      :   "id,uid,username,type,log,addtime",
            'backup'    :   "id,pid,name,filename,addtime,size,ps",
            'users'     :   "id,username,phone,email,login_ip,login_time",
            'firewall'  :   "id,port,ps,addtime",
            'domain'    :   "id,pid,name,port,addtime",
            'tasks'     :   "id,name,type,status,addtime,start,end,install_status"
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




    def get_date_range(self,
        start_date: str = None,
        end_date: str = None,
        date_format: str = "%Y-%m-%d"
    ) -> list[str]:
        """
        根据起止日期获取日期列表，支持指定日期格式
        
        参数:
            start_date: 开始日期字符串（格式与date_format一致，默认None表示end_date往前推29天）
            end_date: 结束日期字符串（格式与date_format一致，默认None表示今天）
            date_format: 日期字符串格式（默认"%Y-%m-%d"）
        
        返回:
            日期字符串列表（按从end_date到start_date的顺序排列，包含两端日期）
        
        异常:
            ValueError: 日期格式错误或start_date晚于end_date
        """
        # 处理默认结束日期（默认为今天）
        if end_date is None:
            end_date_obj = datetime.now().date()
        else:
            try:
                end_date_obj = datetime.strptime(end_date, date_format).date()
            except ValueError:
                raise ValueError(f"结束日期格式错误，应为{date_format}")
        
        # 处理默认开始日期（默认是结束日期往前推29天，共30天）
        if start_date is None:
            start_date_obj = end_date_obj - timedelta(days=29)
        else:
            try:
                start_date_obj = datetime.strptime(start_date, date_format).date()
            except ValueError:
                raise ValueError(f"开始日期格式错误，应为{date_format}")
        
        # 校验日期逻辑（开始日期不能晚于结束日期）
        if start_date_obj > end_date_obj:
            raise ValueError(f"开始日期({start_date})不能晚于结束日期({end_date})")
        
        # 生成日期列表（从start_date递增到end_date，自然从小到大）
        date_list = []
        current_date = start_date_obj  # 从开始日期开始
        while current_date <= end_date_obj:  # 循环到结束日期为止
            date_list.append(current_date.strftime(date_format))
            current_date += timedelta(days=1)  # 日期递增
        
        return date_list



    def get_site_data(self,
        base_dir: str,
        site_name: str,
        date_list: list[str]
    ) -> dict[str, any]:
        """
        获取单个站点的统计数据
        
        参数:
            base_dir: 基础数据目录
            site_name: 站点名称
            date_list: 日期列表（YYYY-MM-DD格式）
        
        返回:
            包含list和total的站点数据字典
        """
        site_dir = os.path.join(base_dir, site_name)
        daily_data = []
        total_requests = 0

        # 处理每个日期的数据
        for date_str in date_list:
            # 转换日期格式为YYYYMMDD（整数类型）
            date_int = int(date_str.replace("-", ""))
            file_path = os.path.join(site_dir, f"{date_str}.json")
            
            # 初始化当日请求数为0
            requests = 0
            
            # 尝试读取文件
            if os.path.exists(file_path) and os.path.isfile(file_path):
                try:
                    with open(file_path, "r", encoding="utf-8") as f:
                        data = json.load(f)
                        # 确保requests字段存在且为数字
                        if isinstance(data.get("requests"), (int, float)):
                            requests = int(data["requests"])
                except (json.JSONDecodeError, Exception):
                    # 解析错误或其他异常时保持请求数为0
                    pass
            
            # 添加当日数据
            daily_data.append({
                "request": requests,
                "date": date_int
            })
            # 累计总请求数
            total_requests += requests

        return {
            "list": daily_data,
            "total": {
                "request": total_requests
            }
        }

    


    def get_multi_site_stats(self,
        base_dir: str = "/www/server/site_total/data/total",
        site_names: list[str] = None,
        start_date: str = None,
        end_date: str = None
    ) -> dict[str, any]:
        """
        获取多个站点的统计数据，返回指定格式的结果
        
        参数:
            base_dir: 基础数据目录
            site_names: 要查询的站点名称列表，默认包含示例站点
        
        返回:
            符合指定格式的统计数据字典
        """
        message = {}
        # 默认站点列表
        if site_names is None:
            return message
        
        # 获取日期列表
        date_list = self.get_date_range(start_date, end_date)
        
        # 收集所有站点数据
        
        for site in site_names:
            # 检查站点目录是否存在
            site_dir = os.path.join(base_dir, site)
            if os.path.exists(site_dir) and os.path.isdir(site_dir):
                message[site] = self.get_site_data(base_dir, site, date_list)
            else:
                # 站点不存在时返回空数据结构
                message[site] = {
                    "list": [{"request": 0, "date": int(date.replace("-", ""))} for date in date_list],
                    "total": {"request": 0}
                }
        
        # 构建最终返回格式
        return message

    def __check_auth(self):
        from plugin_auth_v2 import Plugin as Plugin
        plugin_obj = Plugin(False)
        plugin_list = plugin_obj.get_plugin_list()
        import PluginLoader
        self.__IS_PRO_MEMBER = PluginLoader.get_auth_state() > 0
        return int(plugin_list["pro"]) > time.time() or self.__IS_PRO_MEMBER

    # 获取网站监控报表数据
    def getSiteThirtyTotal(self, get=None):
        """
            2026/2/26 调整由前端传入site_type控制输出
        """
        project_type = ['PHP', 'WP2',' proxy' , 'Node' , 'Python', 'Go']
        if get is not None:
            if get.get("site_type", None) in project_type:
                project_type = [get.get("site_type")]

        #检测插件是否安装
        if not os.path.exists(os.path.join(public.get_panel_path(),"plugin/monitor/info.json")):
            site_names = [ i.get('name','') for i in public.S('sites').where_in('project_type',project_type).field('name').select() if i.get('name','') !='' ]
            start_date= None if get==None else get.get('start_date',None)
            end_date= None if get==None else get.get('end_date',None)
            return {'status': 0, "timestamp": int(time.time()), "message": self.get_multi_site_stats(site_names=site_names,start_date=start_date,end_date=end_date)}
        cache_file = os.path.join(public.get_panel_path(), 'plugin/monitor/site_thirty_total.json')
        result ={}
        try:
            version=self.get_plugin_version(os.path.join(public.get_panel_path(),"plugin/monitor/info.json"))
            version_list=version.split(".")
            if len(version_list)<3:return {'status': 0, "timestamp": int(time.time()), "message": result}
            if int(version_list[0])<4:return {'status': 0, "timestamp": int(time.time()), "message": result}
            if int(version_list[0])==4 and int(version_list[1])<1:return {'status': 0, "timestamp": int(time.time()), "message": result}
            if int(version_list[0])==4 and int(version_list[1])<1 and int(version_list[2])<2:return {'status': 0, "timestamp": int(time.time()), "message": result}
            #取网站域名列表
            try:
                domain_list = public.S('sites').where_in('project_type',project_type).field('name').select()
            except Exception as ex:
                domain_list = []
            now_time = int(time.time())
            start_date = public.format_date(format="%Y-%m-%d", times=now_time - 86400 * 30)
            end_date = public.format_date(format="%Y-%m-%d", times=now_time)
            
            cache_info = {}
            
            if get!=None:
                content = public.readFile(cache_file)
                
                if content:
                    cache_info = json.loads(content)
            
            
            #取网站统计信息
            for domain in domain_list:
                result[domain["name"]]={"list":[],"total":{"request":0}}
                site_requests= {}
                if get==None:
                    # 等待500ms
                    time.sleep(0.1)
                    args=public.dict_obj()
                    args.start_date=start_date
                    args.end_date=end_date
                    args.part_type="date"
                    args.SiteName=domain["name"]
                    site_requests = public.run_plugin("monitor","get_site_total_list_custom",args)
                    try:
                        if "list" in site_requests:
                            result[domain["name"]]["total"]["request"]=site_requests["total"]["request"]
                            for site in site_requests["list"]:
                                # 等待100ms
                                time.sleep(0.03)
                                result[domain["name"]]["list"].append({"request":site["request"],"date":site["date"]})
                                
                            
                    except Exception as e:
                        # public.print_log('Error__________ {}'.format(str(e)))
                        pass
                    
                else:
                    try:
                        if cache_info and "list" in cache_info[domain["name"]]:
                            result[domain["name"]]=cache_info[domain["name"]]
                    except Exception as e:
                        # public.print_log('Error__________ {}'.format(str(e)))
                        result[domain["name"]]={}
        except Exception as e:
            # public.print_log(public.get_error_info())
            pass
        
        if get==None:
            public.writeFile(cache_file, json.dumps(result))

        return {'status': 0, "timestamp": int(time.time()), "message": result}

    # 简化版获取网站请求数用于排序
    def get_site_request(self,get=None):
        project_type = ['PHP', 'WP2',' proxy' , 'Node' , 'Python', 'Go']
        if get is not None:
            if get.get("site_type") and get.get("site_type") in project_type:
                project_type = [get.get("site_type")]

        #保留免费版
        if not os.path.exists(os.path.join(public.get_panel_path(),"plugin/monitor/info.json")):
            site_names = [ i.get('name','') for i in public.S('sites').where_in('project_type',project_type).field('name').select() if i.get('name','') !='' ]
            start_date= None if get==None else get.get('start_date',None)
            end_date= None if get==None else get.get('end_date',None)
            return {'status': 0, "timestamp": int(time.time()), "message": self.get_multi_site_stats(site_names=site_names,start_date=start_date,end_date=end_date)}

        # 直接读取监控报表数据缓存
        path = os.path.join(public.get_panel_path(), "plugin/monitor/site_thirty_total.json")
        try:
            re_data = {}
            if os.path.exists(path):
                re_data = json.loads(public.readFile(path))
            return {'status': 0, "timestamp": int(time.time()), "message": re_data}
        except:
            return {'status': -1, "timestamp": int(time.time()), "message": {}}

        
    # 获取waf报表数据
    def getSiteWafConfig(self, get=None):
        cache_file = os.path.join(public.get_panel_path(), "plugin/btwaf/site_waf_config_php.json")
        if get!=None:
            try:
                result=json.loads(public.readFile(cache_file))
                if "status" in result:
                    result={}
            except Exception as e:
                result={}
            return {'status': 0, "timestamp": int(time.time()), "message": result}

        result ={}
        try:
            version=self.get_plugin_version(os.path.join(public.get_panel_path(),"plugin/btwaf/info.json"))
            version_list=version.split(".")
            #9.6.8版本以上才支持waf报表
            if len(version_list)<3:return result
            if int(version_list[0])<9:return result
            if int(version_list[0])==9 and int(version_list[1])<6:return result
            if int(version_list[0])==9 and int(version_list[1])<6 and int(version_list[2])<8:return result
            get=public.dict_obj()
            get.p=1
            get.limit=10000
            get.search=""
            result = public.run_plugin("btwaf","get_site_config3",get)
            if "status" in result:
                result={}
            public.writeFile(cache_file, json.dumps(result))
        except Exception as e:
            public.print_log(public.get_error_info())
            pass
        return result
    

    def get_plugin_version(self,filename):
        if os.path.exists(filename):
            try:
                with open(filename, "r", encoding="utf-8") as f:
                    data = json.load(f)
                return data.get("versions")
            except: return "0.0.0"
        return "0.0.0"


    def find_stored_favicons(self):
        try:
            # 检查是否开关是否开启
            icon_path = '/www/server/panel/config/auto_favicon.conf'
            if os.path.exists(icon_path):
                return

            cur_time = int(time.time())
            last_find_stored_favicons_time = cache.get('last_find_stored_favicons_time')

            if last_find_stored_favicons_time and cur_time - last_find_stored_favicons_time < 3600 * 12:
                return

            import requests
            import base64
            site_favs_root = os.path.join(public.get_panel_path(), "data/site_favs")

            if not os.path.exists(site_favs_root):
                os.makedirs(site_favs_root, 0o755)

            sites = public.S('sites').field('id', 'name', 'path').select()

            reg_obj = re.compile(
                r'<link (?:rel="(?:shortcut|icon| )+" *|type="image/x-icon" *|href="([^"]+)" *)+[^>]*>')

            for site in sites:
                site_name = site['name']
                site_path = site['path']
                ico_path = os.path.join(site_path, "favicon.ico")
                stored_ico_path = os.path.join(site_favs_root, site_name + '.ico')

                if not os.path.exists(ico_path) and (not os.path.exists(stored_ico_path) or os.path.getmtime(stored_ico_path) < cur_time - 86400):
                    # 尝试请求favicon.ico
                    domains = public.S('domain').where('pid=?', (site['id'],)).field('name', 'port').select()
                    # 只在前2个域名中查找
                    if len(domains) > 2:
                        domains = domains[:2]

                    for domain in domains:
                        domain_name = domain['name']

                        port = domain['port'] if domain['port'] else 80
                        protocol = 'https' if port == 443 else 'http'
                        url = "{}://127.0.0.1{}/".format(protocol, ':{}'.format(port) if port not in [80, 443] else '')

                        # public.print_log('url: {} {}'.format(domain, url))

                        try:
                            # 首先尝试直接请求favicon.ico
                            ico_url = "{}/favicon.ico".format(url.strip('/'))

                            # public.print_log('ico_url: {}'.format(ico_url))

                            # 等待1s
                            time.sleep(1)

                            try:
                                ico_response = requests.get(ico_url, headers={
                                    'host': domain_name,
                                    'user-agent': 'aaPanel',
                                }, verify=False, timeout=15)

                                if ico_response.status_code == 200 and ico_response.headers.get('Content-Type','').lower() == 'image/x-icon':
                                    ico_content = ico_response.content
                                    with open(stored_ico_path, 'wb') as f:
                                        f.write(ico_content)
                                    # public.print_log('Successfully fetched favicon.ico from {}'.format(ico_url))
                                    break
                            except:
                                pass

                            # 等待500ms
                            time.sleep(1)

                            max_redirects = 2

                            for _ in range(max_redirects):
                                # 无法获取favicon.ico，尝试从首页中获取
                                response = requests.get(url, headers={
                                    'host': domain_name,
                                    'user-agent': 'aaPanel',
                                }, verify=False, timeout=15)

                                # 检查是否重定向
                                if response.status_code >= 300 and response.status_code < 400:
                                    new_url = response.headers.get('location')

                                    # 从new_url中提取域名和端口
                                    if new_url:
                                        # public.print_log('Redirected to: {}'.format(new_url))
                                        parsed_url = requests.utils.urlparse(new_url)
                                        domain_name = parsed_url.netloc.split(':')[0]
                                        continue

                                    # 等待500ms
                                    time.sleep(0.5)
                                    continue

                                break

                            if response.status_code == 200:
                                # 尝试从首页中获取favicon.ico
                                m = reg_obj.search(response.text)

                                # public.print_log('matched ico_url: {}'.format(m.group(1) if m else 'None'))

                                if m:
                                    ico_url = m.group(1)
                                    headers = {
                                        'user-agent': 'aaPanel',
                                    }
                                    if not ico_url.startswith('http'):
                                        headers['host'] = domain_name
                                        # 如果favicon.ico是相对路径，拼接完整URL
                                        if ico_url.startswith('//') and ico_url[2:].startswith(domain_name):
                                            ico_url = url + ico_url[2:].split('/', 2)[-1]
                                        else:
                                            ico_url = url + ico_url.lstrip('/')

                                    # 等待500ms
                                    time.sleep(0.5)

                                    try:
                                        ico_response = requests.get(ico_url, headers=headers, verify=False, timeout=15)
                                        if ico_response.status_code == 200:
                                            ico_content = ico_response.content
                                            # 校验图片格式
                                            is_valid = False
                                            # 检查是否为.ico
                                            if len(ico_content) >= 4 and ico_content[:4] == b'\x00\x00\x01\x00':
                                                is_valid = True
                                            # 检查是否为PNG
                                            elif len(ico_content) >= 8 and ico_content[:8] == b'\x89PNG\r\n\x1a\n':
                                                is_valid = True
                                            # 检查是否为JPG
                                            elif len(ico_content) >= 3 and ico_content[:3] == b'\xff\xd8\xff':
                                                is_valid = True
                                            # 检查是否为GIF
                                            elif len(ico_content) >= 6 and (
                                                    ico_content[:6] == b'GIF87a' or ico_content[:6] == b'GIF89a'):
                                                is_valid = True

                                            if is_valid:
                                                with open(stored_ico_path, 'wb') as f:
                                                    f.write(ico_content)
                                                break
                                    except requests.RequestException as e:
                                        public.print_log("Error fetching favicon from {}: {}".format(ico_url, str(e)),
                                                         _level='error')

                                    break  # 成功获取favicon.ico后跳出循环
                        except requests.RequestException as e:
                            public.print_log("Error fetching favicon for {}: {}".format(domain_name, str(e)),
                                             _level='error')

                if not os.path.exists(ico_path):
                    # 如果仍然没有favicon.ico，尝试从存储的favicon中读取
                    if os.path.exists(stored_ico_path):
                        ico_path = stored_ico_path

                if os.path.exists(ico_path):
                    try:
                        with open(ico_path, 'rb') as f:
                            ico_content = f.read()
                        base64_ico = "data:image/x-icon;base64," + base64.b64encode(ico_content).decode('utf-8')
                        public.writeFile(os.path.join(site_favs_root, site_name + '.b64'), base64_ico)
                    except Exception as e:
                        public.print_log("Error storing favicon for {}: {}".format(site_name, str(e)), _level='error')

            cache.set('last_find_stored_favicons_time', cur_time, timeout=3600 * 12)
        except Exception as e:
            public.print_log(str(e))

    # 获取wp类型
    def get_wp_classification(self, get=None):
        data = public.M("wp_site_types").select()
        return public.return_message(0, 0, data)

    # 获取站点备份数和最后备份时间
    @staticmethod
    def _get_backup_count(site_id):
        res = {"backup_count": 0, "last_backup_time": ""}
        try:
            if public.M('sqlite_master').where('type=? AND name=?', ('table', 'wordpress_backups')).count():
                backups = public.M('wordpress_backups').where('s_id=?', (site_id,)).field(
                    'COUNT(id) as count, MAX(bak_time) as last_time'
                ).find()
                if backups:
                    res = {
                        'backup_count': backups['count'],
                        'last_backup_time': public.format_date("%Y-%m-%d %H:%M:%S", backups['last_time'])
                    }
            return res
        except Exception as e:
            public.print_log("Error fetching backup count for site_id {}: {}".format(site_id, str(e)))
            return res

    # 获取wp网站列表（新）get_wp_site_list
    def get_wp_site_list(self, get=None):
        try:
            # 环境检测与参数初始化
            import one_key_wp_v2
            ok, msg = one_key_wp_v2.checklist_fields()

            # 未安装wp toolkit时
            if not ok and msg == "no such table: wordpress_onekey":
                return public.return_message(0, 0, {"data": [], "total": 0})
            elif not ok:
                return public.return_message(-1, 0, msg)

            # 校验参数
            try:
                p = int(get.get('p', 1))
                limit = int(get.get('limit', 100))
                search = get.get('search', '').strip()
                site_type = get.get('site_type', '').strip()
                order = get.get('order', 'addtime DESC')
                table = get.get('table', '')
                if p < 1: p = 1
                if limit < 1: limit = 100
            except:
                return public.return_message(-1, 0, "Parameter error")

            # 域名查询特殊路由
            if table == 'domain':
                data = self.GetSql(get)
                return public.return_message(0, 0, data)

            one_key_wp_obj = one_key_wp_v2.one_key_wp()

            # 构造基础查询
            query = public.S('sites').prefix('').where('project_type = ?', 'WP2').alias('s')

            # 处理搜索条件
            if search:
                query = query.where('s.name LIKE ? or s.ps LIKE ?', (f'%{search}%', f'%{search}%'))

            # 获取网站类型过滤
            if site_type:
                query = query.join(
                    'wordpress_onekey wok',
                    's.id = wok.s_id',
                    'INNER'
                ).join(
                    'wp_site_types wst',
                    'wok.site_type = wst.name',
                    'INNER',
                ).where('wst.id = ?', site_type)

            # 检查备份表
            try:
                has_backup_table = public.S('wordpress_backups').exists()
            except:
                has_backup_table = False

            # 定义需要查询的字段（确保包含 parent_id 用于层级判断）
            fields = [
                's.id', 's.name', 's.path', 's.status', 's.addtime',
                's.ps', 'edate', 'project_type', 'service_type', 's.parent_id'
            ]

            if has_backup_table:
                query = query.left_join('wordpress_backups wb', 's.id = wb.s_id')
                query = query.field(*(fields + [
                    'COALESCE(COUNT(wb.id), 0) AS backup_count',
                    'MAX(wb.bak_time) AS last_backup_time'
                ])).group('s.id')
            else:
                query = query.field(*fields)

            # 基础排序
            order_list = order.split(' ')
            if order_list[0] not in ['site_ssl', 're_total']:
                query = query.order(order_list[0], order_list[1])

            # 环境状态与图标初始化
            multi_webservice_status = public.get_multi_webservice_status()
            webservice = public.get_webserver()
            panel_path = public.get_panel_path()

            nginx_ico = public.image_to_base64(os.path.join(panel_path, "BTPanel/static/img/soft_ico/ico-nginx.png"))
            apache_ico = public.image_to_base64(os.path.join(panel_path, "BTPanel/static/img/apache.png"))
            ols_ico = public.image_to_base64(
                os.path.join(panel_path, "BTPanel/static/img/soft_ico/ico-openlitespeed.png"))

            # 获取流量信息
            re_data = {}
            if get.get('re_order') or True:
                re_res = self.get_site_request(public.to_dict_obj({'site_type': 'WP2'}))
                if re_res.get('status') == 0:
                    re_data = re_res.get('message')

            # 执行数据库查询
            all_data = query.select()
            if not all_data:
                return public.return_message(0, 0, {"data": [], "total": 0})

            # 构建初始查找映射
            data_map = {}
            for item in all_data:
                data_map[item['id']] = item


            # 保存原始结果ID，用于区分"原始主站"与"补充主站"
            original_ids = set(data_map.keys())

            # search 非空时，若子站被搜出但主站不在结果中，补充主站
            missing_parent_ids = set()
            if search:
                for item in all_data:
                    pid = item.get('parent_id', 0)
                    if pid and pid != -1 and pid not in data_map:
                        missing_parent_ids.add(pid)

            if missing_parent_ids:
                try:
                    parent_rows = public.S('sites').prefix('').where_in(
                        'id', list(missing_parent_ids)
                    ).where('project_type = ?', 'WP2').select()
                    if parent_rows:
                        for p_item in parent_rows:
                            data_map[p_item['id']] = p_item
                        all_data.extend(parent_rows)
                except Exception as ex:
                    public.print_log('get_wp_site_list fetch missing parents error: {}'.format(ex))

            # 统计子站点数量逻辑
            for item in all_data:
                item['sub_site'] = 0

            # 遍历全量数据，内存一次过滤，避免多次sql查询
            for item in all_data:
                pid = item.get('parent_id', 0)
                if pid > 0 and pid in data_map:
                    data_map[pid]['sub_site'] += 1

            # 处理主站点数据并过滤
            result_list = []
            for item in all_data:
                pid = item.get('parent_id', 0)
                # search模式：命中子站时只返回其主站，命中主站也只返回主站
                if pid not in [0, -1]:
                    if search or pid in original_ids:
                        continue

                try:
                    # 流量统计
                    item['re_total'] = re_data.get(item['name'], {}).get('total', {}).get('request', 0)
                    # 备份时间格式化
                    item['last_backup_time'] = public.format_date("%Y-%m-%d %H:%M:%S", item.get('last_backup_time', ''))
                    # 维护模式检测
                    item['maintenance'] = os.path.exists(os.path.join(item['path'], '.maintenance'))
                    # PHP版本
                    item['php_version'] = self.get_php_version(item['name'])
                    # 登录入口
                    item['login_url'] = '/v2/wp/login/{}'.format(item['id'])

                    # WP版本
                    try:
                        item['wp_version'] = one_key_wp_obj.get_wp_version(item['id'])
                        item['cache_status'] = one_key_wp_obj.get_cache_status(item['id'])


                    except:
                        item['wp_version'] = '0.0.0'
                        item['cache_status'] = False

                    # SSL状态处理
                    ssl_info = self.get_site_ssl_info(item['name'])
                    item['ssl'] = ssl_info
                    item['site_ssl'] = ssl_info['endtime'] if (ssl_info and ssl_info != -1) else -1

                    # 图标处理
                    ico_path = os.path.join(panel_path, "data/site_favs", item['name'] + ".b64")
                    user_ico = public.readFile(ico_path) if os.path.exists(ico_path) else ''
                    if user_ico:
                        item['ico'] = user_ico
                    else:
                        st = item.get('service_type', '')
                        current_ws = st if multi_webservice_status else webservice
                        if current_ws == 'apache':
                            item['ico'] = apache_ico
                        elif current_ws == 'openlitespeed':
                            item['ico'] = ols_ico
                        else:
                            item['ico'] = nginx_ico

                    result_list.append(item)
                except Exception as ex:
                    public.print_log('get_wp_site_list enrich item error [id={}, name={}]: {}'.format(
                        item.get('id'), item.get('name'), ex))
                    item['site_ssl'] = item.get('site_ssl', -1)
                    item['ssl'] = item.get('ssl', -1)
                    item['wp_version'] = item.get('wp_version', '0.0.0')
                    item['cache_status'] = item.get('cache_status', False)
                    item['php_version'] = item.get('php_version', 'Static')
                    item['re_total'] = item.get('re_total', 0)
                    item['maintenance'] = item.get('maintenance', False)
                    item['ico'] = item.get('ico', '')
                    result_list.append(item)

            # 排序处理
            if order_list[0] == 'site_ssl':
                is_rev = order_list[1].lower() == 'desc'
                result_list = sorted(result_list, key=lambda x: x['site_ssl'], reverse=is_rev)
            elif get.get('re_order'):
                is_rev = get.get('re_order').lower() == 'desc'
                result_list = sorted(result_list, key=lambda x: x['re_total'], reverse=is_rev)

            # 8分页返回
            total = len(result_list)
            start = (p - 1) * limit
            end = p * limit
            paged_data = result_list[start:end]

            for d in paged_data:
                if d.get('sub_site') > 0:
                    d['id'] = f'group_{d['id']}'

            return public.return_message(0, 0, {'data': paged_data, 'total': total})

        except Exception as e:
            import traceback
            traceback.print_exc()
            return public.return_message(-1, 0, "Internal Server Error: " + str(e))

    # 子网站获取
    def get_wp_sub_site(self, get=None):
        """
        获取指定主站下的子站列表（在内存中进行排序和分页）
        @param get.site_id: 主站ID (s_id)
        @param get.limit: 每页数量 (默认10)
        @param get.p: 当前页码 (默认1)
        """
        try:
            import os
            try:
                parent_id = int(get.get('site_id'))
                limit = int(get.get('limit', 10))
                p = int(get.get('p', 1))
                search = get.get('search', '').strip()
                if p < 1: p = 1
            except:
                return False, "Parameter error"

            import one_key_wp_v2
            one_key_wp_obj = one_key_wp_v2.one_key_wp()

            query = public.S('sites').prefix('').where('parent_id = ? AND project_type = ?', (parent_id, 'WP2'))
            if search:
                query = query.where('(name LIKE ? OR ps LIKE ?)', (f'%{search}%', f'%{search}%'))
            data = query.select()

            if not data:
                return public.return_message(0, 0, {
                    'data': [],
                    'total': 0
                })

            data = sorted(data, key=lambda x: x.get('addtime', 0), reverse=True)

            # 执行分页切片
            total_count = len(data)
            start = (p - 1) * limit
            end = start + limit
            paged_data = data[start:end]

            # 流量
            re_data = {}
            try:
                re_res = self.get_site_request(public.to_dict_obj({'site_type': 'WP2'}))
                if re_res.get('status') == 0:
                    re_data = re_res.get('message')
            except:
                pass

            # 重写路径
            rewrite_path = None
            server_type = public.get_webserver()
            site_main = public.S('sites').where('id = ?', (parent_id,)).field('name,service_type').find()
            if public.get_multi_webservice_status():
                if site_main:
                    server_type = site_main['service_type'] if site_main['service_type'] else 'nginx'

            if server_type == 'nginx':
                rewrite_path = f"{public.get_vhost_path()}/nginx/sub_dir/rewrite/{site_main['name']}/"

            for item in paged_data:
                path_parts = item['name'].strip('/').split('/')
                item['display_name'] = '/'.join(path_parts[1:]) if len(path_parts) > 1 else item['name']
                # 流量统计
                item['re_total'] = re_data.get(item['name'], {}).get('total', {}).get('request', 0)
                item['maintenance'] = os.path.exists(os.path.join(item['path'], '.maintenance'))
                item['php_version'] = self.get_php_version(item['name'])
                item['login_url'] = '/v2/wp/login/{}'.format(item['id'])

                if rewrite_path:
                    item['rewrite_path'] = rewrite_path + item['display_name'].replace('/','_') + '.conf'
                else:
                    item['rewrite_path'] = f"{item['path']}/.htaccess"

                # WP版本
                try:
                    item['wp_version'] = one_key_wp_obj.get_wp_version(item['id'])
                    item['cache_status'] = one_key_wp_obj.get_cache_status(item['id'])
                except:
                    item['wp_version'] = '0.0.0'
                    item['cache_status'] = 0

                # 备份信息处理
                item.update(self._get_backup_count(item['id']))

            return True, {
                'data': paged_data,
                'total': total_count
            }

        except Exception as e:
            return False, e

    # 主站获取
    def get_wp_main_site(self, site_id):
        """
        根据 ID 获取单个 WordPress 站点的完整详情（保留原列表所有字段）
        """
        try:
            import one_key_wp_v2
            one_key_wp_obj = one_key_wp_v2.one_key_wp()
            panel_path = public.get_panel_path()

            # 查询站点基础信息 (对应原 fields 列表)
            item = public.M('sites').where('id=?', (site_id,)).field(
                'id,name,path,status,addtime,ps,edate,project_type,service_type,parent_id'
            ).find()

            if not item: return None

            # 备份信息字段 (backup_count, last_backup_time)
            item.update(self._get_backup_count(site_id))

            # 子站点统计 (sub_site)
            item['main_site'] = True

            # 流量统计字段 (re_total)
            item['re_total'] = 0
            try:
                re_res = self.get_site_request(public.to_dict_obj({'site_type': 'WP2'}))
                if re_res.get('status') == 0:
                    re_data = re_res.get('message', {})
                    item['re_total'] = re_data.get(item['name'], {}).get('total', {}).get('request', 0)
            except:
                pass

            # 维护模式与基础环境 (maintenance, php_version, login_url)
            item['maintenance'] = os.path.exists(os.path.join(item['path'], '.maintenance'))
            item['php_version'] = self.get_php_version(item['name'])
            item['login_url'] = '/v2/wp/login/{}'.format(item['id'])
            item['display_name']=  item['name']

            # WordPress 特有字段 (wp_version, cache_status)
            try:
                item['wp_version'] = one_key_wp_obj.get_wp_version(item['id'])
                item['cache_status'] = one_key_wp_obj.get_cache_status(item['id'])
            except:
                item['wp_version'] = '0.0.0'
                item['cache_status'] = False

            # SSL 状态字段 (ssl, site_ssl)
            ssl_info = self.get_site_ssl_info(item['name'])
            item['ssl'] = ssl_info
            item['site_ssl'] = ssl_info['endtime'] if (ssl_info and ssl_info != -1) else -1

            # 图标处理 (ico)
            ico_path = os.path.join(panel_path, "data/site_favs", item['name'] + ".b64")
            if os.path.exists(ico_path):
                item['ico'] = public.readFile(ico_path)
            else:
                # 如果没有自定义图标，根据服务类型匹配默认图标
                webservice = public.get_webserver()
                st = item.get('service_type', '')
                # 这里的逻辑参考原函数对多服务状态的判断
                current_ws = st if public.get_multi_webservice_status() else webservice

                ico_map = {
                    'apache': 'apache.png',
                    'openlitespeed': 'soft_ico/ico-openlitespeed.png',
                    'nginx': 'soft_ico/ico-nginx.png'
                }
                icon_file = ico_map.get(current_ws, 'soft_ico/ico-nginx.png')
                item['ico'] = public.image_to_base64(os.path.join(panel_path, "BTPanel/static/img", icon_file))

            return item

        except:
            return None

    # 获取子站列表
    def get_wp_sub_sites(self, get=None):
        """
        获取指定主站下的子站列表（在内存中进行排序和分页）
        @param get.site_id: 主站ID (s_id)
        @param get.limit: 每页数量 (默认10)
        @param get.p: 当前页码 (默认1)
        """
        try:
            import os
            try:
                parent_id = json.loads(get.get('site_id', []))
                limit = int(get.get('limit', 10))
                p = int(get.get('p', 1))
                search = get.get('search', '').strip()
                if p < 1: p = 1

                parent_id = [ int(site_id) for site_id in parent_id ]
            except:
                return public.return_message(-1, 0, "Parameter error")

            data = []
            for site_id in parent_id:
                ok, msg = self.get_wp_sub_site(public.to_dict_obj({'site_id':site_id,'limit':limit,'p':p,'search':search}))
                if not ok:
                    return public.return_message(-1, 0, "Failed to obtain sub-sites: " + str(msg))
                # 添加主站, 只有p=1时插入主站标识
                if p < 2:
                    main = self.get_wp_main_site(site_id)
                    if not main:
                        return public.return_message(-1, 0, "Could not obtain the main station.")
                    if main['parent_id'] != -1:
                        data.append(main)
                data.extend(msg['data'])
            return public.return_message(0, 0, data)
        except Exception as e:
            import traceback
            traceback.print_exc()
            return public.return_message(-1, 0, "Failed to obtain sub-sites: " + str(e))

    # 获取所有真实站点列表
    def get_wp_real_sites(self, get=None):
        """获取所有真实站点列表(返回所有site_id的完整信息, 包括组, 如果有组按组返回)"""
        try:
            get.validate([
                Param('site_id').String().Require(),
            ], [
                public.validate.trim_filter(),
            ])
            get.site_id = json.loads(get.get('site_id', []))
            if not get.site_id:
                return public.success_v2([])
        except Exception as ex:
            public.print_log('error info: {}'.format(ex))
            return public.return_message(-1, 0, str(ex))
        try:
            fields = 'id,name,parent_id'
            parent_ids = set()
            direct_ids = [] # 保序
            direct_ids_set = set()
            for sid in get.site_id:
                if isinstance(sid, str) and sid.startswith('group_'):
                    try:
                        pid = int(sid.split('_', 1)[1])
                        parent_ids.add(pid)
                        if pid not in direct_ids_set:
                            direct_ids.append(pid)
                            direct_ids_set.add(pid)
                    except ValueError:
                        continue
                else:
                    try:
                        sid_int = int(sid)
                        if sid_int not in direct_ids_set:
                            direct_ids.append(sid_int)
                            direct_ids_set.add(sid_int)
                    except (ValueError, TypeError):
                        continue
            # 天然去重map
            result_map = {}

            def _query_by_ids(key_field: str, ids: list):
                """根据字段批量查询站点, 构造到map中"""
                if not ids:
                    return
                rows = public.M('sites').where(
                    '{} IN ({})'.format(key_field, ','.join(['?'] * len(ids))), ids
                ).field(fields).select()
                for item in rows or []:
                    result_map[item['id']] = item

            _query_by_ids('parent_id', list(parent_ids))
            _query_by_ids('id', list(direct_ids))

            # 每组父站排第一，后跟其子站点
            res = []
            for did in direct_ids:
                if did in result_map:
                    res.append(result_map.pop(did))
                # 提取该子站点
                children = [
                    item for item in result_map.values() if item.get('parent_id') == did
                ]
                res.extend(children)
                for c in children:
                    result_map.pop(c['id'])
            # 其余追加
            res.extend(result_map.values())
            return public.success_v2(res)
        except Exception as e:
            import traceback
            traceback.print_exc()
            return public.fail_v2(f"Failed to obtain real sites: {str(e)}")

    # 获取aacloud数据，一次性返回
    def get_aacloud_data(self,get):
        webname = public.GetConfigValue("title")
        version = ''
        conf_path = os.path.join(public.get_panel_path(), 'class/common.py')
        try:
            data = public.readFile(conf_path)

            match = re.search(r"g\.version\s*=\s*['\"](.*?)['\"]", data)
            if match:
                version = match.group(1)
        except:
            pass

        return {'webname' : webname,'version': version}
