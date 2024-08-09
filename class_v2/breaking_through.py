# coding: utf-8
# -------------------------------------------------------------------
# aaPanel
# -------------------------------------------------------------------
# Copyright (c) 2015-2017 aaPanel(www.aapanel.com) All rights reserved.
# -------------------------------------------------------------------
# Author: hezhihong <hezhihong@aapanel.com>
# -------------------------------------------------------------------

# ------------------------------
# 防爆破类
#------------------------------

import os,sys,time,db,json
import shlex
panel_path = '/www/server/panel'
if not os.name in ['nt']:
    os.chdir(panel_path)
if not 'class/' in sys.path:
    sys.path.insert(0, 'class/')
if not 'class_v2/' in sys.path:
    sys.path.insert(0, 'class_v2/')
    
import public
from public.regexplib import match_ipv4,match_ipv6
from safeModelV2.base import safeBase

class main(safeBase):
    _config={}

    def __init__(self):
        self._types={'white':'aapanel.ipv4.whitelist','black':'aapanel.ipv4.blacklist'}
        self._config_file='{}/data/breaking_through.json'.format(public.get_panel_path())
        self._limit_file='{}/data/limit_login.pl'.format(public.get_panel_path())
        self.__script_py = public.get_panel_path() + '/script/breaking_through_check.py'
        try:
            for i in self._types:
                rule_type='DROP'
                if i=='white':rule_type='ACCEPT'
                if not public.ExecShell('iptables-save | grep "match-set '+self._types[i]+'"')[0]:
                    public.ExecShell('iptables -I INPUT -m set --match-set '+self._types[i]+' src -j '+rule_type)
        except:pass
        with db.Sql() as sql:
            sql = sql.dbfile("/www/server/panel/data/default.db")

            black_white_sql = '''CREATE TABLE IF NOT EXISTS `black_white` (
  `id` INTEGER PRIMARY KEY AUTOINCREMENT,
  `ip` VARCHAR(45),
  `ps` VARCHAR(40),
  `add_type` VARCHAR(20),
  `add_time` TEXT,
  `timeout` INTEGER,
  `black_reason` INTEGER
)'''

            #black_reason 0 手动添加 1 ssh爆破ip 2 ftp爆破ip

            sql.execute(black_white_sql, ())
            sql.close()
        self._config=self.read_config()
        self.add_cron()
            
            
    def type_conversion(self,data,types):
        if types =='bool':
            try:
                if data=='true':
                    return True
                else:return False
                # data=bool(data)
                # return data
            except:return False
        elif types =='int':
            public.print_log('type==:{}'.format(type(data)))
            try:
                if type(data)=='int':return data
                data=int(data)
                return data
            except:return 0
                
        
    def set_config(self,get):
        """
        @name 设置防护配置
        """
        # public.print_log('tyep-get.global_status:{}'.format(type(get.username_limit)))
        if 'global_status' in get or 'username_status' in get or 'ip_status' in get:
            self._config['global_status']=self.type_conversion(get.global_status,'bool') if 'global_status' in get else self._config['global_status']
            self._config['username_status']=self.type_conversion(get.username_status,'bool') if 'username_status' in get else self._config['username_status']
            self._config['ip_status']=self.type_conversion(get.ip_status,'bool') if 'ip_status' in get else self._config['ip_status']
            public.writeFile(self._config_file,json.dumps(self._config))
            return public.return_message(0,0,"Setting successful")
        try:
            # if 'ip_command' in get:
            try:
                get.ip_command=get.ip_command.strip()
            except:pass
            if get.ip_command!='' and not self.is_shell_command(get.ip_command):return public.return_message(-1,0,"Command incorrect")
            if get.ip_command=='' and not self.type_conversion(get.ip_ipset_filter,'bool'): return public.return_message(-1,0,"Please enable at least one command and firewall")
            self._config['based_on_username']={"limit":self.type_conversion(get.username_limit,'int'),"count":self.type_conversion(get.username_count,'int'),"type":self.type_conversion(get.username_type,'int'),"limit_root":self.type_conversion(get.username_limit_root,'bool')}
            self._config['based_on_ip']={"limit":self.type_conversion(get.ip_limit,'int'),"count":self.type_conversion(get.ip_count,'int'),"command":get.ip_command,"ipset_filter":self.type_conversion(get.ip_ipset_filter,'bool')}
            self._config['history_login_time']=self.type_conversion(get.history_login_time,'int')
            self._config['global_status']=self._config['global_status']
            self._config['username_status']=self._config['username_status']
            self._config['ip_status']=self._config['ip_status']
            # public.print_log('config_type:{}'.format(type(self._config)))
            # public.print_log('config_info:{}'.format(self._config))
            public.writeFile(self._config_file,json.dumps(self._config))
        except Exception as ee:
            public.print_log('ee:{}'.format(ee))
            
        return public.return_message(0,0,"Setting successful")
    
    
    def get_config(self,get):
        """
        @name 获取防护配置
        """
        try:
            tmp_config=public.readFile(self._config_file)
            self._config = json.loads(tmp_config)
            return public.return_message(0,0,self._config)
        except:
            pass
            
        return public.return_message(0,0,self._config)
        
    def read_config(self):
        """
        @name 读取防护配置
        """
        self._config={"based_on_username":{"limit":5,"count":8,"type":0,"limit_root":False},"based_on_ip":{"limit":5,"count":8,"command":"","ipset_filter":True},"history_login_time":60,'global_status':True,'username_status':True,'ip_status':True}
        if not os.path.exists(self._config_file):
            public.writeFile(self._config_file,json.dumps(self._config))
            return self._config
        tmp_config = public.readFile(self._config_file)
        if not tmp_config:
            return self._config
        try:
            self._config = json.loads(tmp_config)
        except:
            public.writeFile(self._config_file,json.dumps(self._config))
            return self._config
        return self._config
        
        
    def format_date_to_timestamp(self,time_string):
        """
        @name将时间转化为字符串
        """
        from datetime import datetime
    
        # 给定的时间字符串
        # time_string = "Jul 16 02:33:09"
        
        # 当前年份
        current_year = datetime.now().year
        
        # 构造完整的日期时间字符串
        full_time_string = f"{current_year} {time_string}"
        
        # 定义日期时间格式
        date_format = "%Y %b %d %H:%M:%S"
        
        # 解析时间字符串
        parsed_time = datetime.strptime(full_time_string, date_format)
        
        # 转换为时间戳
        timestamp = parsed_time.timestamp()
        return timestamp
        
        # # 输出时间戳
        # print("Timestamp:", timestamp)
        
    def get_ssh_info(self,result,data=[],keyword=''):
        """
        @获取SSH信息
        @param since_time:'2024-07-01 05:39:30'
        """
        ssh_info_list=data
        keys=['journalctl_fail','journalctl_connection',"log_file_fail","log_file_connection"]
        ip_total={}
        limit_time=self._config['based_on_ip']['limit']*60
        now_time=int(time.time())
        
        for key in keys:
            if key in result and result[key]:
                line_list=result[key].split('\n')
                for line in line_list:
                    line_split=line.split(' ')
                    if line =='' or len(line)<50 :continue
                    # public.print_log('line_split:{}'.format(line_split))
                    ip=line_split[11]
                    
                    ssh_info={"user":"","exptime":"","ip":"","authservice":"","country_code":"","logintime":"","service":"","country_name":"","timeleft":""}
                    ssh_info['user']=line_split[10]
                    
                    if ip=='port':
                        ip=line_split[10]
                        if ssh_info['user']==ip:ssh_info['user']=line_split[8]
                        ssh_info['authservice']=line_split[13]
                    else:
                        ssh_info['authservice']=line_split[14]

                    
                    ssh_info['service']='sshd'
                    ssh_info['ip']=ip
                    
                    logintime=public.format_date(times=self.format_date_to_timestamp(line[:15]))
                    exp_time=public.format_date(times=self.format_date_to_timestamp(line[:15])+limit_time)
                    timeleft=0 if now_time>self.format_date_to_timestamp(line[:15])+limit_time else self.format_date_to_timestamp(line[:15])+limit_time-now_time
                    ssh_info["exptime"]=exp_time
                    ssh_info["timeleft"]=timeleft
                    
                    # public.print_log('logintime:{}'.format(line[:15]))
                    # public.print_log('logintime2:{}'.format(self.format_date_to_timestamp(line[:15])))
                    
                    # public.print_log('logintime3:{}'.format(logintime))
                    ssh_info['logintime']=logintime
                    if ip not in ip_total:
                        # public.print_log('ip toal ----ip:{}'.format(ip))
                        ip_total[ip]={'count':1,'ssh_infos':[]}
                    else:
                        # public.print_log('ip toal ----ip+:{}'.format(ip))
                        ip_total[ip]['count']+=1
                    # public.print_log("keyword---2:{}".format(keyword))
                    # public.print_log("ssh_info['user']---2:{}".format(ssh_info['user']))
                    if keyword !='' and (keyword in 'sshd' or keyword in ssh_info['authservice'] or keyword in ip or keyword in ssh_info['user'] or keyword in logintime):
                        ip_total[ip]['ssh_infos'].append(ssh_info)
                        ssh_info_list.append(ssh_info)
                    if keyword =='':
                        ip_total[ip]['ssh_infos'].append(ssh_info)
                        ssh_info_list.append(ssh_info)
        return ssh_info_list,ip_total
                        
                    
                    
            
        
    def get_ssh_intrusion(self,since_time):
            """
            @获取SSH爆破次数
            @param since_time:'2024-07-01 05:39:30'
            """
            test_string="""Aug  4 05:22:56 cpanel76262789 sshd[2112635]: Failed password for root from 218.92.0.52 port 20956 ssh2
    Aug  4 05:23:01 cpanel76262789 sshd[2112635]: Failed password for root from 218.92.0.52 port 20956 ssh2
    Aug  4 05:23:04 cpanel76262789 sshd[2112635]: Failed password for root from 218.92.0.52 port 20956 ssh2
    Aug  4 05:23:08 cpanel76262789 sshd[2112635]: Failed password for root from 218.92.0.52 port 20956 ssh2
    Aug  4 05:23:11 cpanel76262789 sshd[2112635]: Failed password for root from 218.92.0.52 port 20956 ssh2
    Aug  4 05:23:18 cpanel76262789 sshd[2112655]: Failed password for root from 218.92.0.52 port 41852 ssh2
    Aug  4 05:23:23 cpanel76262789 sshd[2112655]: Failed password for root from 218.92.0.52 port 41852 ssh2
    Aug  4 05:47:03 cpanel76262789 sshd[2114164]: Failed password for root from 49.235.86.107 port 54144 ssh2
    Aug  4 05:47:13 cpanel76262789 sshd[2114181]: Failed password for root from 81.192.46.48 port 39134 ssh2
    Aug  4 05:49:10 cpanel76262789 sshd[2114252]: Failed password for root from 188.235.158.112 port 41790 ssh2
    """
            
            
            result = {'journalctl_fail':"",'journalctl_connection':"","log_file_fail":"","log_file_connection":""}
            if os.path.exists("/etc/debian_version"):
                version = public.readFile('/etc/debian_version').strip()
                if 'bookworm' in version or 'jammy' in version or 'impish' in version:
                    version = 12
                else:
                    try:
                        version = float(version)
                    except:
                        version = 11
                if version >= 12:
                    # public.print_log('开始获取防爆破日志----')
                    result['journalctl_fail'] = public.ExecShell("journalctl -u ssh --no-pager --since '"+since_time+"'|grep -a 'Failed password for' |grep -v 'invalid'")[0]
                    # public.print_log('开始获取防爆破日志----1')
                    result['journalctl_connection']=public.ExecShell("journalctl -u ssh --no-pager --since '"+since_time+"'|grep -a 'Connection closed by authenticating user' |grep -a 'preauth'")[0]
                    # public.print_log('开始获取防爆破日志----2')
                    return result
                    # return public.return_message(0, 0, result)
            # data = self.get_ssh_cache()
            for sfile in self.get_ssh_log_files(None):
                count = 0
                try:
                    try:
                        result['log_file_fail'] = public.ExecShell("cat %s|grep -a 'Failed password for' |grep -v 'invalid'" % (sfile))[0].strip()
                    except:pass
                    try:
                        result['log_file_connection'] = public.ExecShell("cat %s|grep -a 'Connection closed by authenticating user' |grep -a 'preauth'" % (sfile))[0].strip()
                    except:pass
                except: pass
            # self.set_ssh_cache(data)
            return result
            
            
    def cron_method(self):
        if not self._config['global_status']:
            return 
        # public.print_log('防爆破脚本开始运行...')
        #aapanel login
        limit_time=int(self._config['based_on_username']['limit'])*60
        count=int(self._config['based_on_username']['count'])
        now_time=old_limit=time.time()
        start_time=public.format_date(times=now_time-limit_time)
        login_info=public.M('logs').where('type=? and addtime>=? and log LIKE ?',('Login',start_time,'%is incorrec%')).select()
        aapanel_login_limit=now_time+limit_time
        try:
            old_limit=int(public.readFile(self._limit_file))
        except:old_limit=now_time
        if len(login_info)>=count and old_limit<=now_time:
            public.writeFile(self._limit_file,str(aapanel_login_limit))
            # public.print_log('统计到面板登录最大尝试次数')
        
        #ssh login
        #取ssh记录
        limit_time=int(self._config['based_on_ip']['limit'])*60
        # limit_time=2592000
        start_time=public.format_date(times=now_time-limit_time)
        count=int(self._config['based_on_ip']['count'])
        # public.print_log('ssh start_time:{}'.format(start_time))
        ssh_info=self.get_ssh_intrusion(start_time)
        # public.print_log('ssh_info:{}'.format(ssh_info))
        result,ip_total=self.get_ssh_info(ssh_info)
        # public.print_log('ssh_info result:{}'.format(result))
        # public.print_log('ssh_info ip_total:{}'.format(ip_total))
        # if self._config['ip_status'] and self._config['based_on_ip']['ipset_filter']:
            # public.print_log('检测到ip状态打开')
        # 遍历外部字典
        for ip, details in ip_total.items():
            if int(details['count'])<count:continue
            # public.print_log('统计到ssh登录最大尝试次数')
            
            if self._config['ip_status'] and self._config['based_on_ip']['ipset_filter']:
                # public.print_log('防火墙防护状态打开')
                args=public.dict_obj()
                args.types='black'
                args.ips=ip
                args.cron='true'
                args.black_reason=1
                self.add_black_white(args)
            # public.print_log('执行命令结果：')
            # public.print_log(self._config['based_on_ip']['command'])
                public.ExecShell('nohup '+self._config['based_on_ip']['command']+' &')
            # public.print_log(result)
            # 遍历 ssh_infos 列表
            # for info in details['ssh_infos']:
        # public.print_log('防爆破脚本开始结束')
        return
    def is_shell_command(self,command_string):
        # 尝试使用shlex.split处理字符串
        try:
            # 分割字符串
            split_command = shlex.split(command_string)
            
            # 检查是否有至少一个非空字符串
            if split_command:
                # 检查第一个元素是否可能是命令名
                command_name = split_command[0]
                
                # 检查命令名是否只包含字母、数字或下划线
                if all(c.isalnum() or c == '_' for c in command_name):
                    return True
        except ValueError:
            # 如果shlex.split抛出ValueError，那么可能不是一个合法的shell命令
            pass
        
        return False
        
    def get_history_record(self,get):
        """
        @name 获取历史记录，能匹配关键词搜索
        
        
        {'error_logins':[
                {
                    "timeleft": "356099", #解封剩余分钟数
                    "user": "anonymous", #用户名
                    "exptime": "2025-04-09 10:21:01", #解封时间
                    "ip": "34.22.135.234",
                    "authservice": "pure-ftpd",#身份验证服务
                    "country_code": "BE",#所在国家简称
                    "logintime": "2024-08-02 10:21:01",#登录时间
                    "service": "system", #服务
                    "country_name": "Belgium"#所在国家名称
                }]
        """
        now_time=int(time.time())
        keyword=get.keyword.strip()
        result=[]
        limit_time=int(self._config['history_login_time'])*60  #默认最近1小时
        aapanel_user=public.M('users').where("id=?", (1,)).getField('username')
        if get.types == 'login':
            start_time=public.format_date(times=time.time()-limit_time)
            login_info=public.M('logs').where('type=? and addtime>=? and log LIKE ?',('Login',start_time,'%is incorrec%')).select()
            if len(login_info)>0:
                for i in login_info:
                    ip=i['log'].split('Login IP:')[1].strip()
                    ip=ip.split(':')[0]
                    exptime=int(time.time())-limit_time-public.to_date(i['addtime'])
                    if exptime<0:exptime=0
                    timeleft= 0 if now_time>public.to_date(i['addtime'])+limit_time else now_time-(public.to_date(i['addtime'])+limit_time)
                    tt_time=public.format_date(times=public.to_date(times=i['addtime'])+limit_time)
                    single_info={"timeleft":timeleft,
                    "user":aapanel_user,
                    "ip":ip,
                    "authservice":"aapanel",
                    "exptime":tt_time,#当前时间-超时时间-登录时间
                    "country_code":"",
                    "logintime":i['addtime'],
                    "service":"aapanel",
                    "country_name":""}
                    if keyword !='' and (keyword in aapanel_user or keyword in ip or keyword in "aapanel" or keyword in i['addtime']) :result.append(single_info)
                    if keyword =='':result.append(single_info)
            # public.print_log('aapanel_login:{}'.format(result))
            # public.print_log('keyword:{}'.format(get.keyword))
            #取ssh记录
            # public.print_log('ssh start_time:{}'.format(start_time))
            ssh_info=self.get_ssh_intrusion(start_time)
            # public.print_log('ssh_login:{}'.format(ssh_info))
            # public.print_log('keyword:{}'.format(get.keyword))
            result,ip_total=self.get_ssh_info(ssh_info,result,keyword=get.keyword)
                    
        elif get.types == 'ip':
            ip_info=public.M('black_white').where('add_type=? and timeout !=?', ('black',0 )).select()
            black_ipset=public.ExecShell('ipset list aapanel.ipv4.blacklist')[0]
            for i in ip_info:
                # if i['ip'] not in black_ipset:continue
                if keyword !='' and (keyword not in i['ip'] and keyword in "aapanel" and  keyword in i['addtime']) :continue
                # public.print_log('---------23:{}'.format(i['add_time']))
                time1=int(public.to_date(times=i['add_time']))
                timeleft= 0 if now_time>time1+i['timeout'] else now_time-(time1+i['timeout'])
                single_info={"timeleft":timeleft,
                "ip":i['ip'],
                "exptime":public.format_date(times=time1+i['timeout']),
                "begin":i['add_time'],
                "country_code":"",
                "note":"",
                "action":"aapanel",
                "country_name":""}
                result.append(single_info)
        # elif get.types == 'ip':
            
        # elif get.types == 'login':
        
        #取分页数据
        import page
        page = page.Page()
        info = {}
        info['count'] = len(result)
        info['row'] = 10
        info['p'] = 1
        if hasattr(get, 'p'):
            info['p'] = int(get['p'])
        if hasattr(get, 'limit'):
            info['row'] = int(get['limit'])
        info['uri'] = get
        info['return_js'] = ''
        if hasattr(get, 'tojs'):
            info['return_js'] = get.tojs
        data = {}
        # 获取分页数据
        data['data']=[]
        data['page'] = page.GetPage(info, '1,2,3,4,5,8')
        start = (info['p']-1)*info['row']
        end= info['p']*info['row']-1
        # public.print_log('start:{}'.format(start))
        # public.print_log('end:{}'.format(end))
        for index in range(len(result)):
            if index<start:continue
            if index >end:continue
            data['data'].append(result[index])
        return public.return_message(0,0,data)
        
    def set_history_record_limit(self,get=None):
        """
        @name 设置历史记录时间
        """
        # times=int(time.time())
        # public.writeFile(self._limit_time_file, str(times))
        # public.print_log(get.history_login_time)
        try:
            # public.print_log(self.type_conversion(get.history_login_time,'int'))
            self._config['history_login_time']=self.type_conversion(get.history_login_time,'int')
        except Exception as ee:
            public.print_log('ee:{}'.format(ee))
        public.writeFile(self._config_file,json.dumps(self._config))
        # public.print_log(self._config)
        return public.return_message(0,0,'Setting successful')
        
        
    def clear_history_record_limit(self,get):
        """
        @name 移除并清空历史记录
        """
        get.history_login_time=int(time.time())
        self.set_history_record_limit(get)
        #清除历史记录
        public.ExecShell('ipset flush '+self._types['black'])
        public.M('black_white').where('add_type=? and timeout !=?', ('black',0)).delete()
        return public.return_message(0,0,'Setting successful')
        
        
        
    def get_black_white(self,get):
        """
        @name 获取黑/白名单
        """
        ip_list=[]
        result=public.M('black_white').where('add_type=? and black_reason=?', (get.types,0)).select()
        return public.return_message(0,0,result)
        
    def add_black_white(self,get):
        """
        @name 添加、编辑、删除黑/白名单
        """
        # public.print_log('ips:{}'.format(get.ips))
        if 'black_reason' not in get:get.black_reason=0
        ip_infos=get.ips.strip().split('\\n')
        ip_list=[]
        #检测ip是否正确
        for i in ip_infos:
            if i=='':continue
            ps=''
            i_list=i.split('#',1)
            ip=i_list[0].replace('"', '').strip()
            if len(i_list)>1:
                ps=i_list[1].strip()
            single_info={"ip":ip,"ps":ps}
            if public.is_ipv4(ip):
                ip_list.append(single_info)
            else:
                public.print_log('ip:{}'.format(ip))
                return {'status': -1, "timestamp": int(time.time()), "message": {'result':'[{}] IP address incorrect'.format(ip)}}
               
        if len(ip_list)==0:
            #清空黑/白名单
            public.ExecShell('ipset flush '+self._types[get.types])
            public.M('black_white').where('add_type=? and black_reason =?', (get.types,0)).delete()
            return public.return_message(0,0,'The operation has been executed')
        if 'ps' not in get and 'cron' not in get:       
            public.ExecShell('ipset flush '+self._types[get.types])
            public.M('black_white').where('add_type=? and black_reason =?', (get.types,0)).delete()
        timeout=0
        if get.types=='black':timeout=int(self._config['based_on_ip']['limit']) *60
        
        check_result=public.ExecShell('ipset list')[0]
        if self._types[get.types] not in check_result:
            public.ExecShell('ipset create '+self._types[get.types]+' hash:net timeout 0')
        
        # ip_list=get.ips
        success_list=[]
        failed_list=[]
        # message=''
        # effective_ip_list=[]
        # public.print_log('ip_list:{}'.format(ip_list))
        try:
            for ip_info in ip_list:
                ip=ip_info['ip']
                ps=ip_info['ps']
                if ps=='' and len(ip_list)==1 and 'ps' in get:ps=get.ps 
                if ip=='':continue
                if not public.M('black_white').where('ip=? and add_type=?', (ip, get.types)).count():
                    # public.print_log('----1------3')
                    public.M('black_white').add('ip,add_type,ps,add_time,timeout,black_reason',(ip, get.types,ps,time.strftime('%Y-%m-%d %X',time.localtime()),timeout,get.black_reason))
                
                result=public.ExecShell('ipset add '+self._types[get.types]+' '+ip+' timeout '+str(timeout))
                if public.M('black_white').where('ip=? and add_type=?', (ip, get.types)).count():
                    success_list.append(ip)
                else:
                    failed_list.append(ip)
        except:pass
        # if len(success_list)>0:
        #     message='The following IP addresses have been successfully added：【{}】'.format(",".join(success_list))
        # if len(failed_list)>0:
        #     message+='The following IP addresses have been failed added：【{}】'.format(",".join(failed_list))
        return {'status': 0, "timestamp": int(time.time()), "message": {'result':'The operation has been executed'}}
        # return public.return_message(0,0,'The operation has been executed')
        
    def modify_black_white(self,get):
        """
        @name 编辑黑/白名单
        """
        if public.M('black_white').where('id=?', (get.id, )).count():
            public.M('black_white').where('id=?',(get.id, )).setField('ps',get.ps)
        return public.return_message(0,0,'Edited successfully')
            
        
    def del_balck_white(self,get):
        """
        @name 删除黑/白名单
        """
        public.print_log('---------010')
        #数据库内添加指定数据并返回数据库id
        #rgs_obj.id = public.M('crontab').add('name,type,where1,where_hour,where_minute,echo,addtime,status,save,backupTo,sType,sName,sBody,urladdress',("续签Let's Encrypt证书",'day','',hour,minute,echo,time.strftime('%Y-%m-%d %X',time.localtime()),0,'','localhost','toShell','',shell,''))
        if not public.M('black_white').where('id=?', (get.id,)).count():
            public.M('black_white').where('id=?', (get.id,)).delete()
        ip=public.M('black_white').where("id=?", (get.id,)).getField('ip')
        public.print_log('---------01')
        types=public.M('black_white').where("id=?", (get.id,)).getField('add_type')
        public.print_log('---------02')
        public.print_log('id:{}'.format(get.id))
        public.M('black_white').where('id=?', (get.id,)).delete()
        public.ExecShell('ipset del '+self._types[types]+' '+ip)
        public.print_log('---------03')
        return public.return_message(0,0,'Delete successfully')

        
    def check_local_ip_white(self,get):
        """
        @name 编辑黑/白名单
        """
        if not public.M('black_white').where('ip=? and add_type=?', (get.ip, 'white')).count():
            return public.return_message(-1,0,'Your current IP address [{}] is not on the whitelist.'.format(get.ip))
        return public.return_message(0,0,'Your current IP address [{}] is on the whitelist.'.format(get.ip))
        
        
    def panel_ip_white(self,get):
        """
        @name 面板设置ip加白
        """
        get.ips=get.ip
        # from BTPanel import cache
        # limitip=''
        # try:
        #     limitip = public.readFile('data/limitip.conf')
        #     limitip=limitip.strip()
        # except:
        #     limitip=''
        # if limitip=='':limitip=get.ip
        # else:
        #     if get.ip not in limitip:
        #         limitip=limitip+','+get.ip
        # public.writeFile('data/limitip.conf',limitip)
        # cache.set('limit_ip',[])
        get.types='white'
        get.ps='your ip address'
        result=self.add_black_white(get)
        if result['status']==0:
            return public.return_message(0,0,'Added successfully')
        else:
            return public.return_message(-1,0,'Added failed')
        
        
    def add_cron(self):
        cron_name='[Do not delete] breaking through check task'
        cron_path = public.GetConfigValue('setup_path') + '/cron/'
        python_path = ''
        try:
            python_path = public.ExecShell('which btpython')[0].strip("\n")
        except:
            try:
                python_path = public.ExecShell('which python')[0].strip("\n")
            except:
                pass
        if not python_path: return False
        count=public.M('crontab').where('name=?',(cron_name,)).count()
        if count>1:
            cron_echo = public.M('crontab').where(
                    "name=?", (cron_name, )).getField('echo')
            cron_id = public.M('crontab').where(
                    "echo=?", (cron_echo, )).getField('id')
            args = {"id": cron_id}
            import crontab
            crontab.crontab().DelCrontab(args)
            del_cron_file = cron_path + cron_echo
            public.ExecShell(
                "crontab -u root -l| grep -v '{}'|crontab -u root -".
                format(del_cron_file))
                    
        if not public.M('crontab').where('name=?',
                                         (cron_name, )).count():
            cmd = '{} {}'.format(python_path, self.__script_py)
            args = {
                "name": cron_name,
                "type": 'minute-n',
                "where1": '1',
                "hour": '',
                "week":'',
                "minute": '',
                "sName": "",
                "sType": 'toShell',
                "notice": '',
                "notice_channel": '',
                'datab_name':'',
                'tables_name':'',
                "save": '',
                "save_local": '1',
                "backupTo": '',
                "sBody": cmd,
                "urladdress": ''
            }
            import crontab
            res = crontab.crontab().AddCrontab(args)
            if res and "id" in res.keys():
                return True
            return False
        return True
        
    def get_protected_services(self,get):
        """
        @name 获取防护配置
        """
        result={'based_on_username':['aapanel'],'based_on_ip':['ssh']}
            
        return public.return_message(0,0,result)
        
        
    
        
    
        
        
        
        
