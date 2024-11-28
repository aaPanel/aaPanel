#coding: utf-8
# +-------------------------------------------------------------------
# | aapanel Windows面板
# +-------------------------------------------------------------------
# | Copyright (c) 2015-2020 aapanel(https://www.bt.cn) All rights reserved.
# +-------------------------------------------------------------------
# | Author: 沐落 <cjx@aapanel.com>
# +-------------------------------------------------------------------
import sys, os, time, json, re, psutil

panelPath = "/www/server/panel"
os.chdir(panelPath)
sys.path.append("class/")
import public,db,time,html,panelPush
import config

try:
    from BTPanel import cache
except :
    from cachelib import SimpleCache
    cache = SimpleCache()

class site_push:

    __push = None
    __push_model = ['dingding','weixin','mail','sms','wx_account','feishu']
    __conf_path =  "{}/class/push/push.json".format(panelPath)
    pids = None

    def __init__(self):
        self.__push = panelPush.panelPush()

    #-----------------------------------------------------------start 添加推送 ------------------------------------------------------
    def get_version_info(self,get):
        """
        获取版本信息
        """
        data = {}
        data['ps'] = ''
        data['version'] = '1.0'
        data['date'] = '2020-08-10'
        data['author'] = 'aaPanel'
        data['help'] = 'http://www.aapanel.com'
        return data

    """
    @获取推送模块配置
    """
    def get_module_config(self,get):

        stype =  None
        if 'type' in get:
            stype = get.type

        data = []
        #证书到期提醒
        item = self.__push.format_push_data()
        item['cycle'] = 30
        item['type'] = 'ssl'
        item['push'] = self.__push_model
        item['title'] = 'Website SSL Expiration Reminder'
        item['helps'] = ['SSL expiration reminders are sent only once a day']
        data.append(item)

        #网站到期提醒
        item = self.__push.format_push_data(push = ['dingding','weixin','mail'])
        item['cycle'] = 15
        item['type'] = 'site_endtime'
        item['title'] = 'Website Expiration Reminder'
        item['helps'] = ['Site expiration reminders are sent only once a day']
        data.append(item)

        for data_item in data:
            if stype == data_item['type']:
                return data_item
        return data


    def get_push_cycle(self,data):
        """
        @获取执行周期
        """
        result = {}
        for skey in data:
            result[skey] = data[skey]

            m_cycle =[]
            m_type = data[skey]['type']
            if m_type in ['endtime','ssl','site_endtime']:
                m_cycle.append('1 time per day when {} days remain'.format(data[skey]['cycle']))

            if len(m_cycle) > 0:
                result[skey]['m_cycle'] = ''.join(m_cycle)
        return result

    def get_server_status(self, server_name):
        status = self.check_run(server_name)
        if status:
            return 1
        return 0

        # 检测指定进程是否存活

    def checkProcess(self, pid):
        try:
            if not self.pids: self.pids = psutil.pids()
            if int(pid) in self.pids: return True
            return False
        except Exception as e:
            return False

        # 名取PID

    def getPid(self, pname):
        try:
            if not self.pids: self.pids = psutil.pids()
            for pid in self.pids:
                if psutil.Process(pid).name() == pname: return True
            return False
        except:
            return True

        # 检查是否启动

    def check_run(self, name):
        if name == "php-fpm":
            status = False
            base_path = "/www/server/php"
            if not os.path.exists(base_path):
                return status
            for p in os.listdir(base_path):
                pid_file = os.path.join(base_path, p, "var/run/php-fpm.pid")
                if os.path.exists(pid_file):
                    php_pid = int(public.readFile(pid_file))
                    status = self.checkProcess(php_pid)
                    if status:
                        return status
            return status
        elif name == 'nginx':
            status = False
            if os.path.exists('/etc/init.d/nginx'):
                pidf = '/www/server/nginx/logs/nginx.pid'
                if os.path.exists(pidf):
                    try:
                        pid = public.readFile(pidf)
                        status = self.checkProcess(pid)
                    except:
                        pass
            return status
        elif name == 'apache':
            status = False
            if os.path.exists('/etc/init.d/httpd'):
                pidf = '/www/server/apache/logs/httpd.pid'
                if os.path.exists(pidf):
                    pid = public.readFile(pidf)
                    status = self.checkProcess(pid)
                    #public.print_log(status)
            return status
        elif name == 'mysql':
            res = public.ExecShell("service mysqld status")
            if res and not re.search(r"not\s+running", res[0]):
                return True
            return False
        elif name == 'tomcat':
            status = False
            if os.path.exists('/www/server/tomcat/logs/catalina-daemon.pid'):
                if self.getPid('jsvc'): status = True
            if not status:
                if self.getPid('java'): status = True
            return status
        elif name == 'pure-ftpd':
            pidf = '/var/run/pure-ftpd.pid'
            status = False
            if os.path.exists(pidf):
                pid = public.readFile(pidf)
                status = self.checkProcess(pid)
            return status
        elif name == 'redis':
            status = False
            pidf = '/www/server/redis/redis.pid'
            if os.path.exists(pidf):
                pid = public.readFile(pidf)
                status = self.checkProcess(pid)
            return status
        elif name == 'memcached':
            status = False
            pidf = '/var/run/memcached.pid'
            if os.path.exists(pidf):
                pid = public.readFile(pidf)
                status = self.checkProcess(pid)
            return status
        return True

    def clear_push_count(self,id):
        """
        @清除推送次数
        """
        try:
            #编辑后清理推送次数标记
            tip_file = '{}/data/push/tips/{}'.format(public.get_panel_path(),id)
            if os.path.exists(tip_file):
                os.remove(tip_file)
        except:pass


    def set_push_config(self,get):
        """
        @name 设置推送配置
        """
        id = get.id
        module = get.name
        pdata = json.loads(get.data)

        data = self.__push._get_conf()
        if not module in data:data[module] = {}

        self.clear_push_count(id)

        is_create = True
        if pdata['type'] in ['ssl']:
            for x in data[module]:
                item = data[module][x]
                if item['type'] == pdata['type'] and item['project'] == pdata['project']:
                    is_create = False
                    data[module][x] = pdata
        elif pdata['type'] in ['panel_login']:
            p_module = pdata['module'].split(',')
            if len(p_module) > 1:
                return public.returnMsg(False, public.lang("The panel login alarm only supports one alarm mode."))

            if not pdata['status']:
                return public.returnMsg(False, public.lang("It does not support suspending the panel login alarm, if you need to suspend, please delete it directly."))

            import config
            c_obj = config.config()

            args = public.dict_obj()
            args.type = pdata['module'].strip()

            res = c_obj.set_login_send(args)
            if not res['status']: return res

        elif pdata['type'] in ['ssh_login']:

            p_module = pdata['module'].split(',')
            if len(p_module) > 1:
                return public.returnMsg(False, public.lang("SSH login alarm only supports one alarm mode."))

            if not pdata['status']:
                return public.returnMsg(False, public.lang("It does not support suspending the SSH login alarm. If you need to suspend, please delete it directly."))

            import ssh_security
            c_obj = ssh_security.ssh_security()

            args = public.dict_obj()
            args.type = pdata['module'].strip()

            res = c_obj.set_login_send(args)
            if not res['status']: return res

        elif pdata['type'] in ['ssh_login_error']:

            res = public.get_ips_area(['127.0.0.1'])
            if 'status' in res:
                return res

        elif pdata['type'] in ['panel_safe_push']:
            pdata['interval'] = 30

        if is_create: data[module][id] = pdata
        public.set_module_logs('site_push_ssl','set_push_config',1)
        return data

    def del_push_config(self,get):
        """
        @name 删除推送记录
        @param get
            id = 告警记录标识
            module = 告警模块, site_push,panel_push
        """
        id = get.id
        module = get.name
        self.clear_push_count(id)

        data = self.__push.get_push_list(get)
        info = data[module][id]
        if id in ['panel_login']:

            c_obj = config.config()
            args = public.dict_obj()
            args.type = info['module'].strip()
            res = c_obj.clear_login_send(args)
            # public.print_log(json.dumps(res))
            if not res['status']: return res
        elif id in ['ssh_login']:

            import ssh_security
            c_obj = ssh_security.ssh_security()
            res = c_obj.clear_login_send(None)

            if not res['status']: return res

        try:
            data = self.__push._get_conf()
            del data[module][id]
            public.writeFile(self.__conf_path,json.dumps(data))
        except: pass
        return public.returnMsg(True, public.lang("successfully deleted."))


    #-----------------------------------------------------------end 添加推送 ------------------------------------------------------
    def get_unixtime(self,data,format = "%Y-%m-%d %H:%M:%S"):
        import time
        timeArray = time.strptime(data,format )
        timeStamp = int(time.mktime(timeArray))
        return timeStamp

    def get_site_ssl_info(self,webType,siteName,project_type = ''):
        """
        @获取SSL详细信息
        @webType string web类型 /nginx /apache /iis
        @siteName string 站点名称
        """
        result = False
        if webType in ['nginx','apache']:
            path = public.get_setup_path()
            if public.get_os('windows'):
                conf_file = '{}/{}/conf/vhost/{}.conf'.format(path,webType,siteName)
                ssl_file = '{}/{}/conf/ssl/{}/fullchain.pem'.format(path,webType,siteName)
            else:
                conf_file ='{}/vhost/{}/{}{}.conf'.format(public.get_panel_path(),webType,project_type,siteName)
                ssl_file = '{}/vhost/cert/{}/fullchain.pem'.format(public.get_panel_path(),siteName)

            conf = public.readFile(conf_file)

            if not conf:
                return result

            if conf.find('SSLCertificateFile') >=0  or conf.find('ssl_certificate') >= 0:

                if os.path.exists(ssl_file):
                    cert_data = public.get_cert_data(ssl_file)
                    return cert_data
        return result


    def get_total(self):
        return True

    def get_ssl_push_data(self,data):
        """
        @name 获取SSL推送数据
        @param data
            type = ssl
            project = 项目名称
            siteName = 站点名称
        """

        if time.time() < data['index'] + 86400:
            return public.returnMsg(False, public.lang("SSL is pushed once a day, skipped."))

        push_keys = []
        ssl_list = []
        sql = public.M('sites')
        if data['project'] == 'all':
            #过滤单独设置提醒的网站
            n_list = []
            try:
                push_list = self.__push._get_conf()['site_push']
                for skey in push_list:
                    p_name = push_list[skey]['project']
                    if p_name != 'all': n_list.append(p_name)
            except : pass

            #所有正常网站
            web_list =  sql.where('status=1',()).select()
            for web in web_list:
                project_type = ''
                if web['name'] in n_list: continue
                if web['name'] in data['tips_list']: continue

                if not web['project_type'] in ['PHP']:
                    project_type = web['project_type'].lower() + '_'

                nlist = []
                info = self.__check_endtime(web['name'],data['cycle'],project_type)
                if type(info) != list:
                    nlist.append(info)
                else:
                    nlist = info

                for info in nlist:
                    if not info: continue
                    info['siteName'] = web['name']
                    push_keys.append(web['name'])
                    ssl_list.append(info)
        else:
            project_type = ''
            find = sql.where('name=? and status=1',(data['project'],)).find()
            if not find: return public.returnMsg(False, public.lang("no site available."))

            if not find['project_type'] in ['PHP']:
                project_type = find['project_type'].lower() + '_'

            nlist = []
            info = self.__check_endtime(find['name'],data['cycle'],project_type)
            if type(info) != list:
                nlist.append(info)
            else:
                nlist = info

            for info in nlist:
                if not info: continue
                info['siteName'] = find['name']
                ssl_list.append(info)

        return self.__get_ssl_result(data,ssl_list,push_keys)

    def get_panel_update_data(self,data):
        """
        @name 获取面板更新推送
        @param push_keys array 推送次数缓存key
        """
        stime = time.time()
        result = {'index': stime ,'push_keys':[data['id']]}

        #面板更新提醒
        if stime < data['index'] + 86400:
            return public.returnMsg(False, public.lang("push once a day, skip."))

        s_url = '{}/api/panel/updateLinuxEn'
        if public.get_os('windows'): s_url = '{}/api/wpanel/updateWindows'
        s_url = s_url.format(public.OfficialApiBase())

        try:
            res = json.loads(public.httpPost(s_url,{}))
            if not res: return public.returnMsg(False, public.lang("Failed to get update information."))
        except:pass

        n_ver = res['version']
        if res['is_beta']:
            n_ver = res['beta']['version']

        old_ver = public.get_cache_func(data['type'])['data']
        if not old_ver:
            public.set_cache_func(data['type'],n_ver)
        else:
            if old_ver == n_ver:
                #处理推送次数逻辑
                if data['id'] in data['tips_list']:
                    print('Notifications exceeded, skip.')
                    return result
            else:
                #清除缓存
                data['tips_list'] = []
                try:
                    tips_path = '{}/data/push/tips/{}'.format(public.get_panel_path(),data['id'])
                    os.remove(tips_path)
                    print('New version found, recount notifications.')
                except:pass
                public.set_cache_func(data['type'],n_ver)

        if public.version() != n_ver:
            for m_module in data['module'].split(','):
                if m_module == 'sms': continue

                s_list = ["> Notification Type: Panel Version Update",">current version:{} ".format(public.version()),">The latest version of:{}".format(n_ver)]
                sdata = public.get_push_info('Panel Update Reminder',s_list)
                result[m_module] = sdata

        return result

    def get_panel_safe_push(self,data,result):
        s_list = []
        #面板登录用户安全
        t_add,t_del,total = self.get_records_calc('login_user_safe',public.M('users'))
        if t_add > 0 or t_del > 0:
            s_list.append(">Login user change:<font color=#ff0000> total {}, add {}, delete {}</font>.".format(total,t_add,t_del))

        #面板日志发生删除
        t_add,t_del,total = self.get_records_calc('panel_logs_safe',public.M('logs'),1)
        if t_del > 0:
            s_list.append(">The panel log is deleted, the number of deleted items:<font color=#ff0000>{} </font>".format(t_del))

        debug_str = 'Disable'
        debug_status = 'False'
        #面板开启开发者模式告警
        if os.path.exists('{}/data/debug.pl'.format(public.get_panel_path())):
            debug_status = 'True'
            debug_str = 'Enable'

        skey = 'panel_debug_safe'
        tmp = public.get_cache_func(skey)['data']
        if not tmp:
            public.set_cache_func(skey,debug_status)
        else:
            if str(debug_status) != tmp:
                s_list.append(">Panel developer mode changed, current status:{}".format(debug_str))
                public.set_cache_func(skey,debug_status)

        # #面板开启api告警
        # api_str = 'False'
        # s_path = '{}/config/api.json'.format(public.get_panel_path())
        # if os.path.exists(s_path):
        #     api_str = public.readFile(s_path).strip()
        #     if not api_str: api_str = 'False'

        # api_str = public.md5(api_str)
        # skey = 'panel_api_safe'
        # tmp = public.get_cache_func(skey)['data']
        # if not tmp:
        #     public.set_cache_func(skey,api_str)
        # else:
        #     if api_str != tmp:
        #         s_list.append(">面板API配置发生改变，请及时确认是否本人操作.")
        #         public.set_cache_func(skey,api_str)


        #面板用户名和密码发生变更
        find = public.M('users').where('id=?',(1,)).find()

        if find:
            skey = 'panel_user_change_safe'
            user_str = public.md5(find['username']) + '|' + public.md5(find['password'])
            tmp = public.get_cache_func(skey)['data']
            if not tmp:
                public.set_cache_func(skey,user_str)
            else:
                if user_str != tmp:
                    s_list.append(">aaPanel login account or password changed")
                    public.set_cache_func(skey,user_str)


        if len(s_list) > 0:
            sdata = public.get_push_info('aaPanel security warning',s_list)
            for m_module in data['module'].split(','):
                if m_module == 'sms': continue
                result[m_module] = sdata

        return result

    def get_push_data(self,data,total):
        """
        @检测推送数据
        @data dict 推送数据
            title:标题
            project:项目
            type:类型 ssl:证书提醒
            cycle:周期 天、小时
            keys:检测键值
        """
        stime = time.time()
        if not 'tips_list' in data: data['tips_list'] = []
        if not 'project' in data: data['project'] = ''

        #优先处理面板更新
        if data['type'] in ['panel_update']:
            return self.get_panel_update_data(data)

        result = {'index': stime ,'push_keys':[data['id']]}
        if data['project']:
            result['push_keys'] = [data['project']]

        #检测推送次数,超过次数不再推送
        if data['project'] in data['tips_list'] or  data['id'] in data['tips_list']:
            return result

        if data['type'] in ['ssl']:
            return self.get_ssl_push_data(data)

        elif data['type'] in ['site_endtime']:
            result['push_keys'] = []

            if stime < data['index'] + 86400:
                return public.returnMsg(False, public.lang("push once a day, skip."))

            mEdate = public.format_date(format='%Y-%m-%d',times = stime + 86400 * int(data['cycle']))
            web_list = public.M('sites').where('edate>? AND edate<? AND (status=? OR status=?)',('0000-00-00',mEdate,1,u'Running')).field('id,name,edate').select()

            if len(web_list) > 0:
                for m_module in data['module'].split(','):
                    if m_module == 'sms': continue

                    s_list = ['>Expiring:<font color=#ff0000>{} website</font>'.format(len(web_list))]
                    for x in web_list:
                        if x['name'] in data['tips_list']: continue
                        result['push_keys'].append(x['name'])

                        s_list.append(">Website: {} Expires: {}".format(x['name'],x['edate']))

                    sdata = public.get_push_info('aaPanel Website Expiration Reminder',s_list)
                    result[m_module] = sdata
                return result

        elif data['type'] in ['panel_pwd_endtime']:
            if stime < data['index'] + 86400:
                return public.returnMsg(False, public.lang("push once a day, skip."))

            import config
            c_obj = config.config()
            res = c_obj.get_password_config(None)

            if res['expire'] > 0 and res['expire_day'] < data['cycle']:
                for m_module in data['module'].split(','):
                    if m_module == 'sms': continue

                    s_list = [">Alarm type: Login password is about to expire",">Days remaining: <font color=#ff0000>{} days</font>".format(res['expire_day'])]
                    sdata = public.get_push_info('aaPanel password expiration reminder',s_list)
                    result[m_module] = sdata
                return result
        elif data['type'] in ['clear_bash_history']:
            stime = time.time()

            result = {'index': stime}

        elif data['type'] in ['panel_bind_user_change']:
            #面板绑定帐号发生变更
            uinfo = public.get_user_info()

            user_str = public.md5(uinfo['username'])
            old_str = public.get_cache_func(data['type'])['data']
            if not old_str:
                public.set_cache_func(data['type'],user_str)
            else:
                if user_str != old_str:

                    for m_module in data['module'].split(','):
                        if m_module == 'sms': continue

                        s_list = [">Alarm type: panel binding account change",">Currently bound account:{}****{}".format(uinfo['username'][:3],uinfo['username'][-4:])]
                        sdata = public.get_push_info('Panel binding account change reminder',s_list)
                        result[m_module] = sdata

                    public.set_cache_func(data['type'],user_str)
                    return result

        elif data['type'] in ['panel_safe_push']:
            return self.get_panel_safe_push(data,result)

        elif data['type'] in ['panel_oneav_push']:
            #微步在线木马扫描提醒
            sfile = '{}/plugin/oneav/oneav_main.py'.format(public.get_panel_path())
            if not os.path.exists(sfile): return

            _obj = public.get_script_object(sfile)
            _main = getattr(_obj,'oneav_main',None)
            if not _main: return

            args = public.dict_obj()
            args.p = 1
            args.count = 1000

            f_list = []
            s_day = public.getDate(format='%Y-%m-%d')

            for line in _main().get_logs(args):

                #未检测到当天日志，跳出
                if public.format_date(times=line['time']).find(s_day) == -1:
                    break
                if line['file'] in f_list: continue

                f_list.append(line['file'])

            if not f_list: return

            for m_module in data['module'].split(','):
                if m_module == 'sms': continue

                s_list = [">alert type:Trojan detects alarms",">Content of notification: <font color=#ff0000> Found suspected Trojan files {}</font>".format(len(f_list)),">listed files:[{}]".format('、'.join(f_list))]
                sdata = public.get_push_info('aaPanel trojan detects alarms',s_list)
                result[m_module] = sdata
            return result

        # 登录失败次数
        elif data['type'] in ['ssh_login_error']:
            import PluginLoader

            args = public.dict_obj()
            args.model_index = 'safe'
            args.count = data['count']
            args.p = 1
            res = PluginLoader.module_run("syslog","get_ssh_error",args)
            if 'status' in res:
                return

            if type(res) == list:
                last_info = res[data['count'] -1]
                if public.to_date(times=last_info['time']) >= time.time() - data['cycle'] * 60:
                    for m_module in data['module'].split(','):
                        if m_module == 'sms': continue

                        s_list = [">Notification type: SSH login failure alarm",">Alarm content: <font color=#ff0000>login failed more than {} times within {} minutes</font> ".format(data['cycle'],data['count'])]
                        sdata = public.get_push_info('SSH login failure alarm',s_list)
                        result[m_module] = sdata
                    return result

        elif data['type'] in ['services']:
            ser_name = data['project']

            status = self.get_server_status(ser_name)
            if status > 0:
                return public.returnMsg(False, public.lang("normal status，Skip."))
            else:
                if status == 0:
                    return self.__get_service_result(data)
                return public.returnMsg(False, public.lang("service not installed，Skip."))

        return public.returnMsg(False, public.lang("Threshold not reached，Skip."))


    def get_records_calc(self,skey,table,stype = 0):
        '''
            @name 获取指定表数据是否发生改变
            @param skey string 缓存key
            @param table db 表对象
            @param stype int 0:计算总条数 1:只计算删除
            @return array
                total int 总数

        '''
        total_add = 0
        total_del = 0

        #获取当前总数和最大索引值
        u_count = table.count()
        u_max =  table.order('id desc').getField('id')

        n_data = {'count': u_count,'max': u_max}
        tmp = public.get_cache_func(skey)['data']
        if not tmp:
            public.set_cache_func(skey,n_data)
        else:
            n_data = tmp

            #检测上一次记录条数是否被删除
            pre_count =  table.where('id<=?',(n_data['max'])).count()
            if stype == 1:
                if pre_count < n_data['count']: #有数据被删除，记录被删条数
                    total_del += n_data['count'] - pre_count

                n_count =  u_max - pre_count  #上次记录后新增的条数
                n_idx = u_max - n_data['max']  #上次记录后新增的索引差
                if n_count < n_idx:
                    total_del += n_idx - n_count
            else:

                if pre_count < n_data['count']: #有数据被删除，记录被删条数
                    total_del += n_data['count'] - pre_count
                elif pre_count > n_data['count']:
                    total_add += pre_count - n_data['count']

                t1_del = 0
                t1_add = 0
                n_count =  u_count - pre_count  #上次记录后新增的条数

                if u_max > n_data['max']:
                    n_idx = u_max - n_data['max']  #上次记录后新增的索引差
                    if n_count < n_idx: t1_del = n_idx - n_count

                #新纪录除开删除，全部计算为新增
                t1_add = n_count - t1_del
                if t1_add > 0: total_add += t1_add

                total_del += t1_del

            public.set_cache_func(skey,{'count': u_count,'max': u_max})
        return total_add,total_del,u_count

    def __check_endtime(self,siteName,cycle,project_type = ''):
        """
        @name 检测到期时间
        @param siteName str 网站名称
        @param cycle int 提前提醒天数
        @param project_type str 网站类型
        """
        info = self.get_site_ssl_info(public.get_webserver(),siteName,project_type)
        if info:
            endtime = self.get_unixtime(info['notAfter'],'%Y-%m-%d')
            day = int((endtime - time.time()) / 86400)
            if day <= cycle: return info

        return False

    def __get_ssl_result(self,data,clist,push_keys = []):
        """
        @ssl到期返回
        @data dict 推送数据
        @clist list 证书列表
        @return dict
        """
        if len(clist) == 0:
            return public.returnMsg(False, public.lang("Expired certificate not found, skipping."))

        result = {'index':time.time(),'push_keys':push_keys }
        for m_module in data['module'].split(','):
            if m_module in self.__push_model:

                sdata = self.__push.format_msg_data()
                if m_module in ['sms']:

                    sdata['sm_type'] = 'ssl_end|aaPanel SSL Expiration Reminder'
                    sdata['sm_args'] = public.check_sms_argv({
                        'name':public.get_push_address(),
                        'website':public.push_argv(clist[0]["siteName"]),
                        'time':clist[0]["notAfter"],
                        'total':len(clist)
                    })
                else:
                    s_list = ['>Expiring soon: <font color=#ff0000>{} copies</font>'.format(len(clist))]
                    for x in clist:
                        s_list.append(">Website: {} Expires: {}".format(x['siteName'],x['notAfter']))

                    sdata = public.get_push_info('aaPanel SSL expiration reminder',s_list)

                result[m_module] = sdata
        return result

    # 服务停止返回
    def __get_service_result(self, data):
        s_idx = int(time.time())
        if s_idx < data['index'] + data['interval']:
            return public.returnMsg(False, public.lang("Interval not reached，Skip."))

        result = {'index': s_idx}

        for m_module in data['module'].split(','):
            result[m_module] = self.__push.format_msg_data()

            if m_module in ['dingding', 'weixin', 'mail', 'wx_account', 'feishu']:
                s_list = [
                    ">Service type：" + data["project"],
                    ">Service Status: Stopped"]
                sdata = public.get_push_info('service stop warning', s_list)
                result[m_module] = sdata

            elif m_module in ['sms']:
                result[m_module]['sm_type'] = 'servcies'
                result[m_module]['sm_args'] = {'name': '{}'.format(public.GetConfigValue('title')),
                                               'product': data["project"], 'product1': data["project"]}

        return result
