#coding: utf-8
# +-------------------------------------------------------------------
# | aaPanel
# +-------------------------------------------------------------------
# | Copyright (c) 2015-2016 aaPanel(www.aapanel.com) All rights reserved.
# +-------------------------------------------------------------------
# | Author: 沐落 <cjx@aapanel.com>
# | Author: lx
# | 消息推送管理
# | 对外方法 get_modules_list、install_module、uninstall_module、get_module_template、set_push_config、get_push_config、del_push_config
# +-------------------------------------------------------------------

import os, sys

panelPath = "/www/server/panel"
os.chdir(panelPath)
sys.path.insert(0,panelPath + "/class/")
import public,re,json,time
try:
    from BTPanel import session
except :
    pass
class panelPush:

    __conf_path =  "{}/class/push/push.json".format(panelPath)
    def __init__(self):
        spath = '{}/class/push'.format(panelPath)
        if not os.path.exists(spath): os.makedirs(spath)

    """
    @获取推送模块列表
    """
    def get_modules_list(self,get):
        cpath = '{}/class/push/push_list.json'.format(panelPath)
        try:
            spath = os.path.dirname(cpath)
            if not os.path.exists(spath): os.makedirs(spath)

            if 'force' in get or not os.path.exists(cpath):
                if not 'download_url' in session: session['download_url'] = public.get_url()
                public.downloadFile('{}/linux/panel/push/push_list.json'.format(session['download_url']),cpath)
        except : pass

        if not os.path.exists(cpath):
            return {}

        data = {}
        push_list = self._get_conf()
        module_list = public.get_modules('class/push')

        configs = json.loads(public.readFile(cpath))
        for p_info in configs:
            p_info['data'] = {}
            p_info['setup'] = False
            p_info['info'] = False
            key = p_info['name']
            try:
                if hasattr(module_list, key):
                    p_info['setup'] = True
                    # if key in module_list:
                    #     print(dir(module_list))
                    #     print(dir(module_list[key]))
                    #     print(dir(getattr(module_list[key], key)))
                    push_module = getattr(module_list[key], key)()
                    p_info['info'] = push_module.get_version_info(None);
                    #格式化消息通道
                    if key in push_list:
                        p_info['data'] = self.__get_push_list(push_list[key])
                    #格式化返回执行周期
                    if hasattr(push_module,'get_push_cycle'):
                        p_info['data'] = push_module.get_push_cycle(p_info['data'])
            except :
                return public.get_error_object(None)
            data[key] = p_info
        return data

    """
    安装/更新消息通道模块
    @name 需要安装的模块名称
    """
    def install_module(self,get):
        module_name = get.name
        down_url = public.get_url()

        local_path = '{}/class/push'.format(panelPath)
        if not os.path.exists(local_path): os.makedirs(local_path)

        sfile = '{}/{}.py'.format(local_path,module_name)
        public.downloadFile('{}/linux/panel/push/{}.py'.format(down_url,module_name),sfile)
        if not os.path.exists(sfile): return public.returnMsg(False, '[{}] Module installation failed'.format(module_name))
        if os.path.getsize(sfile) < 1024: return public.returnMsg(False, '[{}] Module installation failed'.format(module_name))

        sfile = '{}/class/push/{}.html'.format(panelPath,module_name)
        public.downloadFile('{}/linux/panel/push/{}.html'.format(down_url,module_name),sfile)

        return public.returnMsg(True, '[{}] Module installed successfully.'.format(module_name))

    """
    卸载消息通道模块
    @name 需要卸载的模块名称
    """
    def uninstall_module(self,get):
        module_name = get.name
        sfile = '{}/class/push/{}.py'.format(panelPath,module_name)
        if os.path.exists(sfile): os.remove(sfile)

        return public.returnMsg(True, '[{}] Module uninstalled successfully'.format(module_name))


    """
    @获取模块执行日志
    """
    def get_module_logs(self,get):
        module_name = get.name
        id = get.id
        return []

    """
    获取模块模板
    """
    def get_module_template(self,get):
        sfile = '{}/class/push/{}.html'.format(panelPath,get.module_name)

        if not os.path.exists(sfile):
            return public.returnMsg(False, 'template file does not exist!')

        shtml = public.readFile(sfile)
        return public.returnMsg(True, shtml)


    """
    @获取模块推送参数，如：panel_push ssl到期，服务停止
    """
    def get_module_config(self,get):
        module = get.name
        p_list = public.get_modules('class/push')
        push_module = getattr(p_list[module], module)()

        if not module in p_list:
            return public.returnMsg(False, 'The specified module [{}] is not installed!'.format(module))

        if not hasattr(push_module,'get_module_config'):
            return public.returnMsg(False, 'No get_module_config method exists for the specified module [{}].'.format(module))
        return push_module.get_module_config(get)



    """
    @获取模块配置项
    @优先调用模块内的get_push_config
    """
    def get_push_config(self,get):
        module = get.name
        id = get.id
        p_list = public.get_modules('class/push')
        if not module in p_list:
            return public.returnMsg(False, 'The specified module [{}] is not installed.'.format(module))

        result = None
        push_module = getattr(p_list[module], module)()
        if not hasattr(push_module,'get_push_config'):
            push_list = self._get_conf()

            res_data = public.returnMsg(False, 'The specified configuration was not found!')
            res_data['code'] = 100
            if not module in push_list:
                return res_data
            if not id in push_list[module]:
                return res_data

            result = push_list[module][id]
        else:
            result = push_module.get_push_config(get)
        return self.get_push_user(result)

    def get_push_user(self,result):

        #获取发送给谁
        if not 'to_user' in result:
            result['to_user'] = {}
            if 'module' in result:
                for s_module in result['module'].split(','):
                    result['to_user'][s_module] = 'default'
            else:
                return False

        info = {}
        for s_module in result['module'].split(','):
            msg_obj = public.init_msg(s_module)
            if not msg_obj: continue

            info[s_module] = {}
            data = msg_obj.get_config(None)

            if 'list' in data:
                for key in result['to_user'][s_module].split(','):
                    if not key in data['list']:
                        continue
                    info[s_module][key] = data['list'][key]
        result['user_info'] = info
        return result

    """
    @设置推送配置
    @优先调用模块内的set_push_config
    """
    def set_push_config(self,get):
        module = get.name
        id = get.id
        p_list = public.get_modules('class/push')

        if not module in p_list:
            return public.returnMsg(False, 'The specified module [{}] is not installed.'.format(module))

        pdata = json.loads(get.data)
        if not 'module' in pdata or not pdata['module']:
            return public.returnMsg(False, 'The specified alarm method is not set, please select again.')
        if module == "load_balance_push":
            pdata = self.__get_args(pdata,'cycle', "500|502|503|504")
        else:
            pdata = self.__get_args(pdata, 'cycle', 1)
        pdata = self.__get_args(pdata,'count',1)
        pdata = self.__get_args(pdata,'interval',600)
        pdata = self.__get_args(pdata,'key','')
        pdata = self.__get_args(pdata,'push_count',0)

        nData = {}
        for skey in ['key','type','cycle','count','interval','module','title','project','status','index','push_count']:
            if skey in pdata:
                nData[skey] = pdata[skey]

        public.set_module_logs('set_push_config',nData['type'])
        class_obj = getattr(p_list[module], module)()
        if hasattr(class_obj,'set_push_config'):
            get['data'] = json.dumps(nData)
            result = class_obj.set_push_config(get)
            if 'status' in result: return result

            data = result
        else:
            data = self._get_conf()
            if not module in data:data[module] = {}
            data[module][id] = nData


        public.writeFile(self.__conf_path,json.dumps(data))
        return public.returnMsg(True, 'Saved successfully')

    """
    @设置推送状态
    """
    def set_push_status(self,get):
        id = get.id
        module = get.name

        data = self._get_conf()
        if not module in data: return public.returnMsg(True, 'module name does not exist!')
        if not id in data[module]: return public.returnMsg(True, 'The specified push task does not exist!')

        status = int(get.status)
        if status:
            data[module][id]['status'] = True
        else:
            data[module][id]['status'] =  False
        public.writeFile(self.__conf_path,json.dumps(data))
        return public.returnMsg(True, 'Successful operation.')
    """
    @删除指定配置
    """
    def del_push_config(self,get):
        id = get.id
        module = get.name

        p_list = public.get_modules('class/push')
        if not module in p_list:
            return public.returnMsg(False, 'The specified module {} is not installed.'.format(module))
        push_module = getattr(p_list[module], module)()
        if not hasattr(push_module,'del_push_config'):
            data = self._get_conf()
            del data[module][id]
            public.writeFile(self.__conf_path,json.dumps(data))
            return public.returnMsg(True, 'successfully deleted.')

        return push_module.del_push_config(get)

    """
    获取消息通道配置列表
    """
    def get_push_msg_list(self,get):
        data = {}
        msgs = self.__get_msg_list()
        from panelMessage import panelMessage
        pm = panelMessage()
        for x in msgs:
            x['setup'] = False
            key = x['name']
            try:
                obj =  pm.init_msg_module(key)
                if obj:
                    x['setup'] = True
                    if key == 'sms':x['title'] = '{}<a title="Please make sure there are enough SMS messages, otherwise you will not be able to receive notifications." href="javascript:;" class="bt-ico-ask">?</a>'.format(x['title'])
            except :
                pass
            data[key] = x
        return data

    """
    @ 获取消息推送配置
    """
    def _get_conf(self):
        data = {}
        try:
            if os.path.exists(self.__conf_path):
                data = json.loads(public.readFile(self.__conf_path))
                self.update_config(data)
        except:pass
        return data

    """
    @ 获取插件版本信息
    """
    def get_version_info(self):
        """
        获取版本信息
        """
        data = {}
        data['ps'] = ''
        data['version'] = '1.0'
        data['date'] = '2020-07-14'
        data['author'] = '宝塔'
        data['help'] = 'http://www.aapanel.com'
        return data

    """
    @格式化推送对象
    """
    def format_push_data(self,push = ['dingding','weixin','feishu'], project = '', type = ''):
        item = {
            'title':'',
            'project':project,
            'type':type,
            'cycle':1,
            'count':1,
            'keys':[],
            'helps':[],
            'push':push
        }
        return item



    def push_message_immediately(self, channel_data):
        """推送消息到指定的消息通道，即时

        Args:
            channel_data(dict):
                key: msg_channel, 消息通道名称，多个用逗号相连
                value: msg obj, 每种消息通道的消息内容格式，可能包含标题

        Returns:
            {
                status: True/False,
                msg: {
                    "email": {"status": msg},
                    ...
                }
            }
        """
        if type(channel_data) != dict:
            return public.returnMsg(False, "The parameter is wrong")

        from panelMessage import panelMessage
        pm = panelMessage()
        channel_res = {}
        res = {
            "status": False,
            "msg": channel_res
        }

        for module, msg in channel_data.items():
            modules = []
            if module.find(",") != -1:
                modules = module.split(",")
            else:
                modules.append(module)
            for m_module in modules:
                msg_obj = pm.init_msg_module(m_module)
                if not msg_obj:continue
                ret = msg_obj.push_data(msg)
                if ret and "status" in ret and ret['status']:
                    res["status"] = True
                    channel_res[m_module] = ret
                else:
                    msg = "Message push failed."
                    if "msg" in ret:
                        msg = ret["msg"]
                    channel_res[m_module] = public.returnMsg(False, msg)
        return res

    """
    @格式为消息通道格式
    """
    def format_msg_data(self):
        data = {
            'title':'',
            'to_email':'',
            'sms_type':'',
            'sms_argv':{},
            'msg':''
        }
        return data

    def __get_msg_list(self):
        """
        获取消息通道列表
        """
        data = []
        cpath = '{}/data/msg.json'.format(panelPath)
        if not os.path.exists(cpath):
            return data
        try:
            conf = public.readFile(cpath)
            data = json.loads(conf)
        except :
            try:
                time.sleep(0.5)
                conf = public.readFile(cpath)
                data = json.loads(conf)
            except:pass

        return data

    def __get_args(self,data,key,val = ''):
        """
        @获取默认参数
        """
        if not key in data: data[key] = val
        if type(data[key]) != type(val):
            data[key] = val
        return data


    def __get_push_list(self,data):
        """
        @格式化列表数据
        """
        m_data = {}
        result = {}
        for x in self.__get_msg_list(): m_data[x['name']] = x

        for skey in data:
            result[skey] = data[skey]

            m_list = []
            for x in data[skey]['module'].split(','):
                if x in m_data: m_list.append(m_data[x]['title'])
            result[skey]['m_title'] = '、'.join(m_list)

            m_cycle =[]
            if data[skey]['cycle'] > 1:
                m_cycle.append('every {} seconds'.format(data[skey]['cycle']))
            m_cycle.append('{} times, with an interval of {} seconds'.format(data[skey]['count'],data[skey]['interval']))
            result[skey]['m_cycle'] = ''.join(m_cycle)

            # 兼容旧版本没有返回project项，导致前端无法编辑问题
            if "project" not in result[skey] and "type" in result[skey]:
                if result[skey]["type"]  == "services":
                    services = ['nginx','apache',"pure-ftpd",'mysql','php-fpm','memcached','redis']
                    _title = result[skey]['title']
                    for s in services:
                        if _title.find(s)!=-1:
                            result[skey]["project"] = s
                else:
                    result[skey]["project"] = result[skey]["type"]
            if "project" in result[skey]:
                if result[skey]["project"] == "FTP server":
                    result[skey]["project"] ="pure-ftpd"
        return result


    #************************************************推送
    """
    @推送data/push目录的所有文件
    """
    def push_messages_from_file(self):

        path = "{}/data/push".format(panelPath)
        if not os.path.exists(path): os.makedirs(path)

        from panelMessage import panelMessage
        pm = panelMessage()

        for x in os.listdir(path):
            try:
                spath = '{}/{}'.format(path,x)
                if os.path.isdir(spath): continue
                data = json.loads(public.readFile(spath))

                msg_obj = pm.init_msg_module(data['module'])
                if not msg_obj:continue

                ret = msg_obj.push_data(data)
                if ret['status']: pass

                os.remove(spath)
            except :
                print(public.get_error_info())

    """
    @消息推送线程
    """
    def start(self):

        total = 0
        interval = 5

        tips = '{}/data/push/tips'.format(public.get_panel_path())
        if not os.path.exists(tips): os.makedirs(tips)

        try:
            if True:
                # 推送文件
                self.push_messages_from_file()

                # 调用推送子模块
                data = {}
                is_write = False
                path = "{}/class/push/push.json".format(panelPath)

                if os.path.exists(path):
                    data = public.readFile(path)
                    data = json.loads(data)

                p = public.get_modules('class/push')
                for skey in data:
                    if len(data[skey]) <= 0: continue
                    if skey in ['panelLogin_push','panel_login']: continue #面板登录主动触发

                    total = None
                    obj = getattr(p[skey], skey)()

                    for x in data[skey]:
                        try:

                            item = data[skey][x]
                            item['id'] = x
                            if not item['status']: continue
                            if not item['module']: continue
                            if not 'index' in item: item['index'] = 0

                            if time.time() - item['index'] < item['interval']:
                                print('{} Interval not reached, skip.'.format(item['title']))
                                continue

                            #验证推送次数
                            push_record = {}
                            tips_path = '{}/{}'.format(tips,x)
                            if 'push_count' in item and item['push_count'] > 0:
                                item['tips_list'] = []
                                try:
                                    push_record = json.loads(public.readFile(tips_path))
                                except:pass
                                for k in push_record:
                                    if push_record[k] < item['push_count']:
                                        continue
                                    item['tips_list'].append(k)

                            #获取推送数据
                            if not total: total = obj.get_total()
                            rdata = obj.get_push_data(item,total)
                            if not rdata:
                                continue
                            push_status = False
                            for m_module in item['module'].split(','):
                                if not m_module in rdata:
                                    continue

                                msg_obj = public.init_msg(m_module)
                                if not msg_obj:continue

                                if 'to_user' in item and m_module in item['to_user']:
                                    rdata[m_module]['to_user'] = item['to_user'][m_module]

                                ret = msg_obj.push_data(rdata[m_module])
                                data[skey][x]['index'] = rdata['index']
                                is_write = True
                                push_status = True

                            #获取是否推送成功.
                            if push_status:
                                if 'push_keys' in rdata:
                                    for k in rdata['push_keys']:
                                        if not k in push_record: push_record[k] = 0
                                        push_record[k] += 1
                                    public.writeFile(tips_path,json.dumps(push_record))
                        except :
                            print(public.get_error_info())

                if is_write:
                    public.writeFile(path,json.dumps(data))
                #time.sleep(interval)
        except :

            print(public.get_error_info())


    def __get_login_panel_info(self):
        """
        @name 获取面板登录列表
        @auther cjxin
        @date 2022-09-29
        """
        import config
        c_obj = config.config()
        send_type = c_obj.get_login_send(None)['msg']
        if not send_type:
            return False
        return {"type":"panel_login","module":send_type,"interval":600,"status":True,"title":"Panel Login Alert","cycle":1,"count":1,"key":"","module_type":'site_push'}


    def __get_ssh_login_info(self):
        """
        @name 获取SSH登录列表
        @auther cjxin
        @date 2022-09-29
        """
        import ssh_security
        c_obj = ssh_security.ssh_security()
        send_type = c_obj.get_login_send(None)['msg']
        if not send_type or send_type in ['error']:
            return False

        return {"type":"ssh_login","module":send_type,"interval":600,"status":True,"title":"SSH login warning","cycle":1,"count":1,"key":"","module_type":'site_push'}



    def get_push_list(self,get):
        """
        @获取所有推送列表
        """
        conf = self._get_conf()
        for key in conf.keys():
            for x in conf[key]:
                data = conf[key][x]
                data['module_type'] = key

                conf[key][x] = self.get_push_user(data)

        if not 'site_push' in conf: conf['site_push'] = {}

        data = conf['site_push']
        for skey in ['panel_login','ssh_login']:
            info = None
            if skey in data:
                del data[skey]
            if skey in ['panel_login']:
                info = self.__get_login_panel_info()
            elif skey in ['ssh_login']:
                info = self.__get_ssh_login_info()

            if info:
                data[skey] = info
        conf['site_push'] = data
        return conf

    def get_push_logs(self,get):
        """
        @name 获取推送日志
        """

        p = 1
        limit = 15
        if 'p' in get: p = get.p
        if 'limit' in get: limit = get.limit

        where = "type = 'Alarm notification'"
        sql = public.M('logs')

        if hasattr(get, 'search'):
            where = " and logs like '%{search}%' ".format(search=get.search)

        count = sql.where(where,()).count()
        data = public.get_page(count,int(p),int(limit))
        pattern = r"href='(?:/v2)?/push.*?\?p=(\d+)'"
        # 使用re.sub进行替换
        data['page'] = re.sub(pattern, r"href='\1'", data['page'])

        data['data'] = public.M('logs').where(where,()).limit('{},{}'.format(data['shift'], data['row'])).order('id desc').select()

        return public.return_message(0, 0,  data)

    # 兼容旧版本的告警
    def update_config(self, config):
        if "site_push" not in config:
            config["site_push"] = {}
        if "panel_push" in config:
            for k, v in config["panel_push"].items():
                if v["type"] != "endtime":
                    config["site_push"][k] = v
                if "push_count" not in v:
                    v["push_count"] = 1 if v["type"] == "ssl" else 0
            del config["panel_push"]
            public.writeFile(self.__conf_path, json.dumps(config))


if __name__ == '__main__':
    panelPush().start()
