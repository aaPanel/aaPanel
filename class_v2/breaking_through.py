# coding: utf-8
# -------------------------------------------------------------------
# aaPanel
# -------------------------------------------------------------------
# Copyright (c) 2015-2017 aaPanel(www.aapanel.com) All rights reserved.
# -------------------------------------------------------------------
# Author: hezhihong <hezhihong@aapanel.com>
# -------------------------------------------------------------------

# ------------------------------
# 防爆破、编译器类
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

# from pyroute2 import IPSet, NetlinkError

try:
    from pyroute2 import IPSet, NetlinkError
except:
    public.ExecShell("btpip install pyroute2")
    from pyroute2 import IPSet, NetlinkError


class main(safeBase):
    _config={}

    def __init__(self):
        self._types={'white':'aapanel.ipv4.whitelist','black':'aapanel.ipv4.blacklist'}
        self._types_system={'white':'whitelist','black':'blacklist'}
        self._config_file='/www/server/panel/data/breaking_through.json'
        try:
            self._config_file='{}/data/breaking_through.json'.format(public.get_panel_path())
        except:
            pass
        self._breaking_white_file='{}/data/breaking_white.conf'.format(public.get_panel_path())
        self._limit_file='{}/data/limit_login.pl'.format(public.get_panel_path())
        self.__script_py = public.get_panel_path() + '/script/breaking_through_check.py'
        self.__complier_group='aapanel_complier'
        self.__gcc_path=""
        if os.path.exists("/usr/bin/gcc"):
            self.__gcc_path="/usr/bin/gcc"
        else:self.__gcc_path=public.ExecShell('which gcc')[0].strip()
        self.__log_type='Brute force protection'
        self.__write_log=True

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

            #black_reason 0 手动添加 1 ssh爆破ip 2 aapanel爆破ip 3 ftp爆破ip 4 历史记录爆破ip

            sql.execute(black_white_sql, ())
            sql.close()
        
        
        
    def init_ipset(self):
        """
        @name 初始化ipset
        """
        # try:
        #     # 在循环外只查询指定 ipset集合
        #     check_result = public.ExecShell('ipset list aapanel.ipv4.whitelist && ipset list aapanel.ipv4.blacklist')[0]
        #     for i in self._types:
        #         # check_result=public.ExecShell('ipset list')[0]
        #         if self._types[i] not in check_result:
        #             public.ExecShell('ipset create '+self._types[i]+' hash:net timeout 0')
        #         rule_type='DROP'
        #         if i=='white':rule_type='ACCEPT'
        #         if not public.ExecShell('iptables-save | grep "match-set '+self._types[i]+'"')[0]:
        #             public.ExecShell('iptables -I INPUT -m set --match-set '+self._types[i]+' src -j '+rule_type)
        # except:pass


        from pyroute2 import IPSet, NetlinkError
        import socket

        try:
            with IPSet() as ipset:
                # 创建或检查ipset集合
                for i in self._types:
                    try:
                        # 尝试获取集合
                        ipset.get_set_byname(self._types[i])
                    except NetlinkError as e:
                        if e.code == 2:  # ENOENT - No such file or directory
                            # 集合不存在，创建新的ipset集合
                            public.print_log(f"Creating ipset {self._types[i]}")
                            ipset.create(name=self._types[i], stype='hash:net', family=socket.AF_INET, timeout=0)
                        else:
                            raise

            # 设置iptables规则
            for i in self._types:
                rule_type = 'DROP'
                if i == 'white':
                    rule_type = 'ACCEPT'
                if not public.ExecShell('iptables-save | grep "match-set {}"'.format(self._types[i]))[0]:
                    public.ExecShell('iptables -I INPUT -m set --match-set {} src -j {}'.format(self._types[i], rule_type))
        except:
            pass

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
            try:
                if type(data)=='int':return data
                data=int(data)
                return data
            except:return 0
                
        
    def set_config(self,get):
        """
        @name 设置防护配置
        """
        self._config=self.read_config()
        if 'global_status' in get or 'username_status' in get or 'ip_status' in get:
            self._config['global_status']=self.type_conversion(get.global_status,'bool') if 'global_status' in get else self._config['global_status']
            self._config['username_status']=self.type_conversion(get.username_status,'bool') if 'username_status' in get else self._config['username_status']
            self._config['ip_status']=self.type_conversion(get.ip_status,'bool') if 'ip_status' in get else self._config['ip_status']
            public.writeFile(self._config_file,json.dumps(self._config))
            public.write_log_gettext(self.__log_type, 'Configuration modification successful!')
            return public.return_message(0, 0, public.lang("Setting successful"))
        try:
            # if 'ip_command' in get:
            try:
                get.ip_command=get.ip_command.strip()
            except:pass
            if get.ip_command=='' and not self.type_conversion(get.ip_ipset_filter,'bool'): return public.return_message(-1, 0, public.lang("Please enable at least one command and firewall"))
            self._config['based_on_username']={"limit":self.type_conversion(get.username_limit,'int'),"count":self.type_conversion(get.username_count,'int'),"type":self.type_conversion(get.username_type,'int'),"limit_root":self.type_conversion(get.username_limit_root,'bool')}
            self._config['based_on_ip']={"limit":self.type_conversion(get.ip_limit,'int'),"count":self.type_conversion(get.ip_count,'int'),"command":get.ip_command,"ipset_filter":self.type_conversion(get.ip_ipset_filter,'bool')}
            self._config['history_limit']=self.type_conversion(get.history_limit,'int')
            self._config['global_status']=self._config['global_status']
            self._config['username_status']=self._config['username_status']
            self._config['ip_status']=self._config['ip_status']
            public.writeFile(self._config_file,json.dumps(self._config))
        except Exception as ee:
            public.print_log('ee:{}'.format(ee))
        #写日志
        if self.__write_log:
            public.write_log_gettext(self.__log_type, 'Configuration modification successful!')
        return public.return_message(0, 0, public.lang("Setting successful"))
    
    
    def get_config(self,get):
        """
        @name 获取防护配置
        """
        self._config=self.read_config()
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
        self._config={"based_on_username":{"limit":5,"count":8,"type":0,"limit_root":False},"based_on_ip":{"limit":5,"count":8,"command":"","ipset_filter":True},"history_limit":60,"history_start":0,'global_status':True,'username_status':False,'ip_status':False}
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
        
        
    def get_ssh_info(self,result, data=[], keyword='', get_data: bool = False):
        """
        @获取SSH信息
        @param since_time:'2024-07-01 05:39:30'
        """
        self._config=self.read_config()
        ssh_info_list=data
        keys=['journalctl_fail','journalctl_connection','journalctl_invalid_user',"log_file_fail","log_file_connection","log_file_invalid_user"]
        ip_total={}
        limit_time=self._config['based_on_ip']['limit']*60
        now_time=int(time.time())
        
        for key in keys:
            if key in result and result[key]:
                line_list=result[key].split('\n')
                for line in line_list:
                    if line =='' or len(line)<50 :continue
                    
                    # ssh_info={"user":"","exptime":"","ip":"","authservice":"aapanel safe","country_code":"","logintime":"","service":"","country_name":"","timeleft":"","lock_status":'unlock'}
                    ssh_info={"user":"","exptime":"","ip":"","authservice":"","country_code":"","logintime":"","service":"","country_name":"","timeleft":"","lock_status":'unlock'}
                    user='root'
                    ip='127.0.0.1'

                    #取user
                    try:
                        user=line.split(' for ',1)[1].split(' ')[0]
                    except: pass
                
                    #取ip
                    try:
                        ip=line.split(' from ',1)[1].split(' ')[0]
                    except: pass
                    
                    ssh_info['service']='sshd'
                    if ip =="127.0.0.1" and "Connection closed by authenticating user" in line:            
                        #取ip
                        try:
                            ip=line.split(' user ',1)[1].split(' ')[1]
                        except: pass
                    #从爆破用户日志取用户
                    if key in ['journalctl_invalid_user','log_file_invalid_user']:
                        #取user
                        try:
                            user=line.split('Invalid user ',1)[1].split(' ')[0]
                        except: pass

                    #检测用户是否为空
                    if user =='':
                        user='-'
                    ssh_info['ip']=ip
                    ssh_info['user']=user
                    check_result=public.ExecShell('ipset test aapanel.ipv4.blacklist '+ip)[1]
                    if 'is in set' in check_result:ssh_info['lock_status']='lock'

                    #取时间
                    try:
                        tmp_time=self.format_date_to_timestamp(line[:15])
                        
                    except:
                        tmp_time=public.to_date(format="%Y-%m-%dT%H:%M:%S.%f%z",times=line[:32])

                    logintime=public.format_date(times=tmp_time)
                    tmp_exp_time=tmp_time+limit_time
                    exp_time=public.format_date(times=tmp_exp_time)
                    timeleft=0 if now_time>tmp_exp_time else tmp_exp_time-now_time
                    ssh_info["exptime"]=exp_time
                    ssh_info["timeleft"]=timeleft
                    
                    ssh_info['logintime']=logintime
                    if ip not in ip_total:
                        ip_total[ip]={'count':1,'ssh_infos':[]}
                    else:
                        ip_total[ip]['count']+=1

                    if get_data:
                        if keyword !='' and (keyword in 'sshd' or keyword in ssh_info['authservice'] or keyword in ip or keyword in ssh_info['user'] or keyword in logintime):
                            ip_total[ip]['ssh_infos'].append(ssh_info)
                            ssh_info_list.append(ssh_info)
                        if keyword =='':
                            ip_total[ip]['ssh_infos'].append(ssh_info)
                            ssh_info_list.append(ssh_info)

        return ssh_info_list, ip_total
                        
                    
                    
            
        
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
            
            
            result = {'journalctl_fail':"",'journalctl_connection':"",'journalctl_invalid_user':"","log_file_fail":"","log_file_connection":"","log_file_invalid_user":""}
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
                    result['journalctl_fail'] = public.ExecShell("journalctl -u ssh --no-pager --since '"+since_time+"'|grep -a 'Failed password for' |grep -v 'invalid'")[0]
                    result['journalctl_connection']=public.ExecShell("journalctl -u ssh --no-pager --since '"+since_time+"'|grep -a 'Connection closed by authenticating user' |grep -a 'preauth'")[0]
                    result['journalctl_invalid_user']=public.ExecShell("journalctl -u ssh --no-pager --since '"+since_time+"'|grep -a 'sshd' |grep -a 'Invalid user'|grep -v 'Connection closed by'")[0]
                    return result
            for sfile in self.get_ssh_log_files(None):
                start_timestramp=public.to_date(times=since_time)
                try:
                    try:
                        tmp_result = public.ExecShell("cat %s|grep -a 'Failed password for' |grep -v 'invalid'" % (sfile))[0].strip()
                        add_result=[]
                        line_list=tmp_result.split('\n')
                        for line in line_list:
                            try:
                                tmp_time=self.format_date_to_timestamp(line[:15])
                            except:
                                tmp_time=public.to_date(format="%Y-%m-%dT%H:%M:%S.%f%z",times=line[:32])
                            # print('tmp_time:{}'.format(public.format_date(times=tmp_time)))
                            if start_timestramp<=tmp_time:
                                add_result.append(line)
                        add_string='\n'.join(add_result)
                        result['log_file_fail']+=add_string
                    except:pass
                    try:
                        tmp_result= public.ExecShell("cat %s|grep -a 'Connection closed by authenticating user' |grep -a 'preauth'" % (sfile))[0].strip()
                        
                        add_result=[]
                        line_list=tmp_result.split('\n')
                        for line in line_list:
                            try:
                                tmp_time=self.format_date_to_timestamp(line[:15])
                            except:
                                tmp_time=public.to_date(format="%Y-%m-%dT%H:%M:%S.%f%z",times=line[:32])

                            # print('tmp_time:{}'.format(public.format_date(times=tmp_time)))
                            if start_timestramp<=tmp_time:
                                add_result.append(line)
                        add_string='\n'.join(add_result)
                        result['log_file_connection']+=add_string
                    except:pass
                    try:
                        cmd="cat %s|grep -a 'sshd' |grep -a 'Invalid user '|grep -v 'Connection closed by'" % (sfile)
                        tmp_result= public.ExecShell("cat %s|grep -a 'sshd' |grep -a 'Invalid user'|grep -v 'Connection closed by'" % (sfile))[0].strip()
                        
                        add_result=[]
                        line_list=tmp_result.split('\n')
                        for line in line_list:
                            try:
                                tmp_time=self.format_date_to_timestamp(line[:15])
                            except:
                                tmp_time=public.to_date(format="%Y-%m-%dT%H:%M:%S.%f%z",times=line[:32])

                            # print('tmp_time:{}'.format(public.format_date(times=tmp_time)))
                            if start_timestramp<=tmp_time:
                                add_result.append(line)
                        add_string='\n'.join(add_result)
                        result['log_file_invalid_user']+=add_string
                    except:pass
                except: pass
            # self.set_ssh_cache(data)
            return result
            
    def check_black_white_ipset(self):
        """
        @name 检测ipset黑白名单
        """
        for list_type,list_name in self._types.items():
            ip_info=public.M('black_white').where('add_type=?', (list_type,)).select()
            if list_type=='white':#白名单检测
                for ip in ip_info:
                    public.ExecShell('ipset add '+list_name+' '+ip['ip']+' timeout 0')
            else:#黑名单检测
                for ip in ip_info:
                    timeout=timeleft=0
                    if int(ip['timeout'])!=0:
                        add_time=int(public.to_date(times=ip['add_time']))
                        now_time=int(time.time())
                        exptime=add_time+int(ip['timeout'])
                        timeleft=exptime-now_time
                        timeout=timeleft
                        if timeleft>0:
                            public.ExecShell('ipset add '+list_name+' '+ip['ip']+' timeout '+str(timeout))
                        else:
                            public.M('black_white').where('id=?', (ip['id'],)).delete()
                    else:
                        public.ExecShell('ipset add '+list_name+' '+ip['ip']+' timeout 0')
                        
                        
        return
                            
                        
                
            
            
    def cron_method(self):
        """
        @name 防爆破检测方法
        """
        self.init_ipset()
        # public.print_log('Starting through check task execution')
        self.check_black_white_ipset()
        self._config=self.read_config()
        
        if not self._config['global_status']:
            return 
        # public.print_log('防爆破脚本开始运行...')
        aapanel_login_info=[]
        now_time=old_limit=time.time()
        if  self._config['username_status']:
            limit_time=int(self._config['based_on_username']['limit'])*60
            count=int(self._config['based_on_username']['count'])
            
            start_time=public.format_date(times=now_time-limit_time)
            aapanel_login_info=public.M('logs').where('type=? and addtime>=? and log LIKE ?',('Login',start_time,'%is incorrec%')).select()
            aapanel_login_limit=now_time+limit_time
            try:
                old_limit=int(public.readFile(self._limit_file))
            except:old_limit=now_time
            if len(aapanel_login_info)>=count and old_limit<=now_time:
                public.writeFile(self._limit_file,str(aapanel_login_limit))
                # public.print_log('统计到面板登录最大尝试次数')
                # public.print_log('当前时间为：{}'.format(public.format_date(times=now_time)))
                # public.print_log('限制时间为：{}'.format(public.format_date(times=aapanel_login_limit)))
            
            
        if self._config['ip_status']:
            #ssh login
            #取ssh记录
            limit_time=int(self._config['based_on_ip']['limit'])*60
            # limit_time=2592000
            start_time=public.format_date(times=now_time-limit_time)
            ip_count=int(self._config['based_on_ip']['count'])
            ssh_info=self.get_ssh_intrusion(start_time)
            _, ip_total = self.get_ssh_info(ssh_info)

            # ssh最大ip限制处理
            for ip, details in ip_total.items():
                if int(details['count'])<ip_count:continue
                # public.print_log('统计到ssh登录最大尝试次数')

                if self._config['based_on_ip']['ipset_filter']:
                    # public.print_log('防火墙防护状态打开')
                    args = public.dict_obj()
                    args.types = 'black'
                    args.ips = ip
                    args.cron = 'true'
                    args.black_reason = 1
                    self.add_black_white(args,False)
                command = self._config['based_on_ip']['command']
                if command != '':
                    public.ExecShell('nohup ' + str(command) + ' &')
                    
        # public.print_log('Breaking through check task has been executed')
        # time.sleep(60)
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
    
    def get_ssh_info_v2(self,search='',select='Failed',limit=999):
        """
        @name 获取ssh信息
        """
        from pathlib import Path
        import public.PluginLoader as plugin_loader
        mod_relative_path = "mod/project/ssh/comMod.py"
        # 拼接路径
        mod_file = str(Path(public.get_panel_path()) / mod_relative_path)
        plugin_class = plugin_loader.get_module(mod_file)
        class_string='main'
        plugin_object = getattr(plugin_class,class_string)()
        pdata = public.dict_obj()
        pdata.p=1
        pdata.limit=limit
        pdata.search=search
        pdata.select=select
        result = getattr(plugin_object,"get_ssh_list")(pdata)
        
        if isinstance(result, dict):
            try:
                #检测数据获取是否成功
                status=result.get("status",-1)
                if status<0:
                    return 0,[]
                data = result["message"]["data"]
                return len(data),data
            except:
                return 0,[]
        return 0,[]
        
    def get_history_record2(self,get):
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
                    "lock_status":0 #0(未封锁)/1(封锁中)
                }]
        """
        self._config=self.read_config()
        now_time=int(time.time())
        keyword=get.keyword.strip()
        result=[]
        limit_time=int(self._config['history_limit'])*60  #默认最近1小时
        aapanel_user=public.M('users').where("id=?", (1,)).getField('username')
        start_time=public.format_date(times=now_time-limit_time)
        if self._config['history_start'] !=0 and int(time.time())-int(self._config['history_start'])<limit_time:
            start_time=public.format_date(times=self._config['history_start'])
        if get.types == 'login':
            #取面板登录记录
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
                    "country_name":""
                    }
                    #搜索过滤
                    if keyword !='' and (keyword in aapanel_user or keyword in ip or keyword in "aapanel" or keyword in i['addtime']) :result.append(single_info)
                    if keyword =='':result.append(single_info)
            #取ssh记录
            _,ssh_result=self.get_ssh_info_v2()
            for i in ssh_result:
                timeleft= 0 if now_time>public.to_date(i['timestamp'])+limit_time else now_time-(public.to_date(i['timestamp'])+limit_time)
                tt_time=public.format_date(times=public.to_date(times=i['timestamp'])+limit_time)
                single_info={"timeleft":timeleft,
                    "user":i["user"],
                    "ip":i["address"],
                    "authservice":"sshd",
                    "exptime":tt_time,#当前时间-超时时间-登录时间
                    "country_code":"",
                    "logintime":i['time'],
                    "service":"sshd",
                    "country_name":""
                    }
                #搜索过滤
                if keyword !='' and (keyword in aapanel_user or keyword in i["address"] or keyword in "sshd" or keyword in single_info['logintime']) :result.append(single_info)
                if keyword =='':result.append(single_info)

                    
        elif get.types == 'ip':
            ip_info=public.M('black_white').where('add_type=? and timeout !=? and add_time>?', ('black',0,start_time )).select()
            for i in ip_info:
                if keyword !='' and (keyword not in i['ip'] and keyword in "aapanel" and  keyword in i['addtime']) :continue
                add_time=int(public.to_date(times=i['add_time']))
                exptime=add_time+i['timeout']
                timeleft= 0 if now_time>exptime else exptime-now_time
                single_info={"timeleft":timeleft//60,
                "ip":i['ip'],
                "exptime":public.format_date(times=exptime),
                "begin":i['add_time'],
                "country_code":"",
                "note":"",
                "action":"aapanel",
                "country_name":"",
                'lock_status':'blocked',
                'block_reason':'Trigger SSH explosion-proof rule breaking' if i['black_reason']==1 else 'Trigger aapanel explosion-proof rule breaking'
                }
                result.append(single_info)
                

        #排序
        result = sorted(result, key=lambda x: x['logintime'], reverse=True)
        #取分页数据
        data = self.get_page(get,result)
        return public.return_message(0,0,data)
    

    def get_history_record(self, get):
        """
        获取历史记录，支持关键词搜索
        
        返回格式:
        {'error_logins': [
            {
                "timeleft": "356099",  # 解封剩余分钟数
                "user": "anonymous",   # 用户名
                "exptime": "2025-04-09 10:21:01",  # 解封时间
                "ip": "34.22.135.234",
                "authservice": "pure-ftpd",  # 身份验证服务
                "country_code": "BE",  # 国家简称
                "logintime": "2024-08-02 10:21:01",  # 登录时间
                "service": "system",   # 服务
                "country_name": "Belgium",  # 国家名称
                "lock_status": 0  # 0(未封锁)/1(封锁中)
            }
        ]}
        """
        # 常量定义：避免硬编码，便于维护
        SERVICE_AAPANEL = "aapanel"
        SERVICE_SSHD = "sshd"
        BLOCK_REASON_SSH = "Trigger SSH explosion-proof rule breaking"
        BLOCK_REASON_PANEL = "Trigger aapanel explosion-proof rule breaking"

        # 初始化配置和时间参数
        self._config = self.read_config()
        now_time = int(time.time())
        keyword = get.keyword.strip()
        limit_time = int(self._config['history_limit']) * 60  # 默认最近1小时
        start_time = self._get_start_time(now_time, limit_time)

        # 获取用户名
        aapanel_user = public.M('users').where("id=?", (1,)).getField('username')

        result = []
        # 根据类型分发处理逻辑
        if get.types == 'login':
            result = self._handle_login_type(
                start_time, now_time, limit_time, 
                aapanel_user, keyword, 
                SERVICE_AAPANEL, SERVICE_SSHD
            )
            # 排序
            if len(result)>1:
                result = sorted(result, key=lambda x: x['logintime'], reverse=True)
        elif get.types == 'ip':
            result = self._handle_ip_type(
                start_time, now_time, keyword,
                SERVICE_AAPANEL, BLOCK_REASON_SSH, BLOCK_REASON_PANEL
            )

            # 排序
            if len(result)>1:
                result = sorted(result, key=lambda x: x['begin'], reverse=True)
        #分页返回结果
        data = self.get_page(get, result)
        return public.return_message(0, 0, data)

    # ------------------------------
    # 拆分后的逻辑模块
    # ------------------------------
    def _get_start_time(self, now_time, limit_time):
        """计算查询的起始时间"""
        config_start = self._config['history_start']
        if config_start != 0 and (now_time - int(config_start) < limit_time):
            return public.format_date(times=config_start)
        return public.format_date(times=now_time - limit_time)

    def _handle_login_type(self, start_time, now_time, limit_time, aapanel_user, keyword, service_panel, service_sshd):
        """处理登录类型(login)的记录逻辑"""
        result = []
        # 1. 处理面板登录记录
        panel_logs = public.M('logs').where(
            'type=? and addtime>=? and log LIKE ?',
            ('Login', start_time, '%is incorrec%')
        ).select()
        for login_log in panel_logs:
            login_info = self._build_panel_login_info(
                login_log, aapanel_user, now_time, limit_time, service_panel
            )
            if self._is_match_keyword(login_info, keyword, service_panel):
                result.append(login_info)
        
        # 2. 处理SSH登录记录
        _, ssh_logs = self.get_ssh_info_v2()
        start_time_int= public.to_date(times=start_time)
        for ssh_log in ssh_logs:
            if ssh_log["timestamp"]<start_time_int:continue
            ssh_info = self._build_ssh_login_info(
                ssh_log, now_time, limit_time, service_sshd
            )
            if self._is_match_keyword(ssh_info, keyword, service_sshd):
                result.append(ssh_info)
        
        return result

    def _handle_ip_type(self, start_time, now_time, keyword, service, reason_ssh, reason_panel):
        """处理IP类型(ip)的记录逻辑"""
        result = []
        ip_logs = public.M('black_white').where(
            'add_type=? and timeout !=? and add_time>?',
            ('black', 0, start_time)
        ).select()
        
        for ip_log in ip_logs:
            # 关键词过滤
            if keyword and not self._ip_log_match_keyword(ip_log, keyword, service):
                continue
            # 构建IP记录信息
            ip_info = self._build_ip_info(ip_log, now_time, service, reason_ssh, reason_panel)
            result.append(ip_info)
        
        return result

    # ------------------------------
    # 信息构建与过滤
    # ------------------------------
    def _build_panel_login_info(self, login_log, username, now_time, limit_time, service):
        """构建面板登录记录的信息字典"""
        # 解析IP地址
        log_str = login_log['log']
        ip = log_str.split('Login IP:')[1].strip().split(':')[0]
        
        # 计算过期时间和剩余时间
        login_timestamp = public.to_date(login_log['addtime'])
        expire_timestamp = login_timestamp + limit_time
        timeleft = self._calculate_timeleft(now_time, expire_timestamp)
        
        return {
            "timeleft": timeleft,
            "user": username,
            "ip": ip,
            "authservice": service,
            "exptime": public.format_date(times=expire_timestamp),
            "country_code": "",
            "logintime": login_log['addtime'],
            "service": service,
            "country_name": ""
        }

    def _build_ssh_login_info(self, ssh_log, now_time, limit_time, service):
        """构建SSH登录记录的信息字典"""
        login_timestamp = public.to_date(ssh_log['timestamp'])
        expire_timestamp = login_timestamp + limit_time
        timeleft = self._calculate_timeleft(now_time, expire_timestamp)
        
        return {
            "timeleft": timeleft,
            "user": ssh_log["user"],
            "ip": ssh_log["address"],
            "authservice": service,
            "exptime": public.format_date(times=expire_timestamp),
            "country_code": "",
            "logintime": ssh_log['time'],
            "service": service,
            "country_name": ""
        }

    def _build_ip_info(self, ip_log, now_time, service, reason_ssh, reason_panel):
        """构建IP封锁记录的信息字典"""
        add_timestamp = int(public.to_date(times=ip_log['add_time']))
        exptime_timestamp = add_timestamp + ip_log['timeout']
        timeleft = self._calculate_timeleft(now_time, exptime_timestamp) // 60  # 转换为分钟
        
        # 确定封锁原因
        block_reason = reason_ssh if ip_log['black_reason'] == 1 else reason_panel
        
        return {
            "timeleft": timeleft,
            "ip": ip_log['ip'],
            "exptime": public.format_date(times=exptime_timestamp),
            "begin": ip_log['add_time'],
            "country_code": "",
            "note": "",
            "action": service,
            "country_name": "",
            'lock_status': 'blocked',
            'block_reason': block_reason
        }

    def _calculate_timeleft(self, now_time, expire_timestamp):
        """计算剩余时间（如果已过期则返回0）"""
        return max(0, expire_timestamp - now_time) if now_time <= expire_timestamp else 0

    def _is_match_keyword(self, info, keyword, service):
        """判断记录是否匹配关键词（无关键词时默认匹配）"""
        if not keyword:
            return True
        # 检查关键词是否在关键字段中
        match_fields = [
            info['user'], info['ip'], service, info['logintime']
        ]
        return any(keyword in str(field) for field in match_fields)

    def _ip_log_match_keyword(self, ip_log, keyword, service):
        """IP记录的关键词匹配逻辑"""
        return (keyword in ip_log['ip']) or (keyword in service) or (keyword in ip_log['add_time'])
            
    def set_history_record_limit(self,get=None):
        """
        @name 设置历史记录时间
        """
        self._config=self.read_config()
        try:
            if 'history_limit' in get:
                self._config['history_limit']=self.type_conversion(get.history_limit,'int')
                #写日志
                if self.__write_log:
                    public.write_log_gettext(self.__log_type, 'Set the duration of failed login attempts (in minutes) to [{}] minutes'.format(self._config['history_limit']))
            if 'history_start' in get:
                self._config['history_start']=self.type_conversion(get.history_start,'int')
                #写日志
                if self.__write_log:
                    public.write_log_gettext(self.__log_type, 'History has been cleared!')
        except Exception as ee:
            public.print_log('ee:{}'.format(ee))
        public.writeFile(self._config_file,json.dumps(self._config))
            
        return public.return_message(0, 0, public.lang("Setting successful"))
            
            
    def clear_history_record_limit(self,get):
        """
        @name 移除并清空历史记录
        """
        self.init_ipset()
        get.history_start=int(time.time())
        self.set_history_record_limit(get)
        #清除历史记录
        clear_ips=public.M('black_white').where('add_type=? and timeout !=?', ('black',0)).select()
        for clear_info in clear_ips:
            check_result=public.ExecShell('ipset test aapanel.ipv4.blacklist '+clear_info['ip'])[1]
            if 'is in set' in check_result:
                public.ExecShell('ipset del '+self._types['black']+' '+clear_info['ip'])
        public.M('black_white').where('add_type=? and timeout !=?', ('black',0)).delete()
        
        #写日志
        if self.__write_log:
            public.write_log_gettext(self.__log_type, 'The history has been cleared and the blocked IP has been cleared')
        return public.return_message(0, 0, public.lang("Setting successful"))
        
        
        
    def get_black_white(self,get):
        """
        @name 获取黑/白名单
        """
        ip_list=[]
        result=public.M('black_white').where('add_type=? and black_reason=?', (get.types,0)).select()
        return public.return_message(0,0,result)
        
    def add_black_white(self,get,write_log=True):
        """
        @name 添加、编辑、删除黑/白名单
        """
        self.init_ipset()
        self.init_complier()
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
                # public.print_log('ip:{}'.format(ip))
                return {'status': -1, "timestamp": int(time.time()), "message": {'result':'[{}] IP address incorrect'.format(ip)}}
        if len(ip_list)==0:
            #清空黑/白名单
            public.ExecShell('ipset flush '+self._types[get.types])
            public.M('black_white').where('add_type=? and black_reason =?', (get.types,0)).delete()
            self.writeListFile()
            if write_log:
                public.write_log_gettext(self.__log_type,  'The black and white list operation settings have been executed')
            return public.return_message(0, 0, public.lang("The operation has been executed"))
        if 'ps' not in get and 'cron' not in get:       
            public.ExecShell('ipset flush '+self._types[get.types])
            public.M('black_white').where('add_type=? and black_reason =?', (get.types,0)).delete()
        timeout=0
        if get.types=='black' and 'hand' not in get:
            timeout=int(self._config['based_on_ip']['limit']) *60
        
        check_result=public.ExecShell('ipset list')[0]
        if self._types[get.types] not in check_result:
            public.ExecShell('ipset create '+self._types[get.types]+' hash:net timeout 0')
        
        # success_list=[]
        # failed_list=[]

        try:
            for ip_info in ip_list:
                ip=ip_info['ip']
                ps=ip_info['ps']
                if ps=='' and len(ip_list)==1 and 'ps' in get:ps=get.ps
                if ip=='':continue
                if 'cron' in get and get.types=='black' and public.M('black_white').where('ip=? and add_type=?', (ip, 'white')).count():
                    # public.print_log('匹配到白名单规则，跳过：{}'.format(ip))
                    continue
                    
                #解封黑名单
                if 'clear_black' in get:
                    public.ExecShell('ipset del '+self._types['black']+' '+ip )
                    public.M('black_white').where('ip=?', (ip,)).delete()
                    
                if get.types=='black' and 'hand' not in get:
                    if ip=='127.0.0.1':
                        # public.print_log('The IP address [{}] is the local IP address and cannot be added to the blacklist'.format(ip))
                        continue

                if not public.M('black_white').where('ip=? and add_type=?', (ip, get.types)).count():
                    public.M('black_white').add('ip,add_type,ps,add_time,timeout,black_reason',(ip, get.types,ps,time.strftime('%Y-%m-%d %X',time.localtime()),timeout,get.black_reason))
                    if public.M('black_white').where('ip=? and add_type=?', (ip, get.types)).count():
                        #写日志
                        if write_log:
                            public.write_log_gettext(self.__log_type,  'Successfully added IP [{}] to the interception system [{}]', (ip,self._types_system[get.types]))
                
                result=public.ExecShell('ipset add '+self._types[get.types]+' '+ip+' timeout '+str(timeout))
                # if public.M('black_white').where('ip=? and add_type=?', (ip, get.types)).count():
                #     success_list.append(ip)
                # else:
                #     failed_list.append(ip)
        except:pass
        # if len(success_list)>0:
        #     message='The following IP addresses have been successfully added：【{}】'.format(",".join(success_list))
        # if len(failed_list)>0:
        #     message+='The following IP addresses have been failed added：【{}】'.format(",".join(failed_list))
        self.writeListFile()
        # if self.__write_log:
        #         public.write_log_gettext(self.__log_type,  'The black and white list operation settings have been executed')
        return {'status': 0, "timestamp": int(time.time()), "message": {'result':'The operation has been executed'}}
        # return public.return_message(0, 0, public.lang("The operation has been executed"))
        
    def writeListFile(self):
        result=public.M('black_white').where('add_type=?', ('white',)).select()
        if len(result)<1:return
        ip_list=[]
        for i in result:
            ip_list.append(i['ip'])
        ip_string=','.join(ip_list)
        public.writeFile(self._breaking_white_file,ip_string)
        return 
        


        
    def check_local_ip_white(self,get):
        """
        @name 编辑黑/白名单
        """
        if not public.M('black_white').where('ip=? and add_type=?', (get.ip, 'white')).count():
            return public.return_message(-1, 0, public.lang("Your current IP address [{}] is not on the whitelist.", get.ip))
        return public.return_message(0, 0, public.lang("Your current IP address [{}] is on the whitelist.", get.ip))
        
        
    def panel_ip_white(self,get):
        """
        @name 面板设置ip加白
        """
        get.ips=get.ip.strip()
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
        if 'ps' not in get:
            get.ps='your ip address'
        get.hand=True
        self.__write_log=False
        result=self.add_black_white(get)
        self.__write_log=True
        if result['status']==0:
            if self.__write_log:
                public.write_log_gettext(self.__log_type,  'Access IP [{}] successfully whitelisted'.format(get.ips))
            return public.return_message(0, 0, public.lang("Added successfully"))
        else:
            return public.return_message(-1, 0, public.lang("Added failed"))
        

    def del_cron(self):
        cron_name='[Do not delete] breaking through check task'
        cron_path = public.GetConfigValue('setup_path') + '/www/server/cron/'
        try:
            cron_path = public.GetConfigValue('setup_path') + '/cron/'
        except:
            pass
        # python_path = ''
        # try:
        #     python_path = public.ExecShell('which btpython')[0].strip("\n")
        # except:
        #     try:
        #         python_path = public.ExecShell('which python')[0].strip("\n")
        #     except:
        #         pass
        # if not python_path: return False
        if public.M('crontab').where('name=?',(cron_name,)).count():
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
                    
        return True
        
        
    def add_cron(self):
        cron_name='[Do not delete] breaking through check task'
        cron_path = public.GetConfigValue('setup_path') + '/www/server/cron/'
        try:
            cron_path = public.GetConfigValue('setup_path') + '/cron/'
        except:
            pass
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
    

    def get_login_limit(self):
        """
        @name 获取登录限制配置
        """
        self._config=self.read_config()
        if not self._config['global_status'] or not self._config['username_status']:return False
         #防爆破检测
        now_time=limit_time=time.time()
        white_ips=''
        _limit_login='{}/data/limit_login.pl'.format(public.get_panel_path())
        breaking_white='{}/data/breaking_white.conf'.format(public.get_panel_path())
        #获取限制时间
        try:
            limit_time=float(public.readFile(_limit_login))
            if os.path.exists(breaking_white):
                limit_time=float(public.readFile(_limit_login))
            if os.path.exists(breaking_white):
                white_ips+=public.readFile(breaking_white)
        except:pass
        intranet_local_ip=public.get_local_ip()
        if intranet_local_ip=='':intranet_local_ip=public.get_local_ip_2()
        from BTPanel import session
        if 'address' not in session:
            session['address']=public.GetClientIp()
        if now_time<limit_time and (white_ips=='' or session['address'] not in white_ips and  intranet_local_ip not in white_ips):
            return True
        return False
        
        
    def get_linux_users(self,get):
        """
        @name 获取linux用户列表信息
        """
        #取用户列表
        user_list=[]
        user_exec=public.ExecShell('cat /etc/passwd')[0].strip()
        try:
            tmp_list=user_exec.split('\n')
            for i in tmp_list:
                i_strip=i.strip()
                if i_strip=='':continue
                user_list.append(i_strip.split(':',1)[0])
        except:pass
        
        #取分页数据
        data = self.get_page(get,user_list)
            
        return public.return_message(0,0,data)
        
        
    def get_page(self,get,result):
        """
        @name 取分页信息
        """
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
        for index in range(len(result)):
            if index<start:continue
            if index >end:continue
            data['data'].append(result[index])
            
        return data
        
    def get_compiler_info(self,get):
        """
        @name 获取编译器组内成员信息
        """
        complier_members=[]
        try:
            group_exec=public.ExecShell('grep '+self.__complier_group+' /etc/group')[0].strip()
            group_string=group_exec.split(':')[3].strip()
            if group_string!='':
                complier_members=group_exec.split(':')[3].split(',')
        except:pass
        
        #取分页数据
        data = self.get_page(get,complier_members)
        return public.return_message(0,0,data)
        
    def init_complier(self):
        """
        @name 初始化编译器组
        """
        #读取配置文件/etc/group
        if os.path.exists('/etc/group'):
            groupContent = public.readFile('/etc/group')
            if groupContent.find(self.__complier_group+":x:") == -1:
                public.ExecShell('groupadd '+self.__complier_group)
            try:
                file_stat = os.stat(self.__gcc_path)
                gid=file_stat.st_gid
                import grp
                group_name=grp.getgrgid(gid).gr_name
                if group_name!=self.__complier_group:
                    public.ExecShell('chgrp '+self.__complier_group+' '+self.__gcc_path)
                    
            except:pass
        
            
        
    def add_user_to_compiler(self,get):
        """
        @name 添加指定用户到编译器组
        """
        self.init_complier()
        if 'users' not in get:return public.return_message(-1, 0, public.lang("parameter error"))
        try:
            if type(get.users)==str:
                import ast
                get.users=ast.literal_eval(get.users)
        except:pass
        add_users=get.users
        get.limit=10000
        complier_members=self.get_compiler_info(get)['message']['data']
        for add_user in add_users:
            try:
                if (len(complier_members)>0 and add_user not in complier_members) or len(complier_members)<1:
                    public.ExecShell('usermod -aG '+self.__complier_group+' '+add_user)
                    # complier_members=self.get_compiler_info(get)['message']['data']
                    # public.print_log('complier_members2:{}'.format(complier_members))
                    # if add_user in complier_members:return public.return_message(0, 0, public.lang("Added successfully"))
            except:pass
        #写日志
        if self.__write_log:
            public.write_log_gettext(self.__log_type,  'Successfully added users [{}] to the compiler group', (','.join(add_users),))
        return public.return_message(0, 0, public.lang("Operation executed"))
        
        
    def del_user_to_compiler(self,get):
        """
        @name 删除编译器组内指定用户
        """
        if 'user' not in get or get.user.strip()=='':return public.return_message(-1, 0, public.lang("parameter error"))
        del_user=get.user.strip()
        get.limit=10000
        complier_members=self.get_compiler_info(get)['message']['data']
        try:
            if len(complier_members)>0 and del_user in complier_members:
                public.ExecShell('gpasswd -d '+del_user+' '+self.__complier_group)
                complier_members=self.get_compiler_info(get)['message']['data']
                if len(complier_members)>0 and del_user in complier_members:return public.return_message(-1, 0, public.lang("Delete failed"))
        except:pass
        #写日志
        if self.__write_log:
            public.write_log_gettext(self.__log_type,  'User [{}] successfully removed from compiler group', (del_user,))
        return public.return_message(0, 0, public.lang("Delete successfully"))
        
    def set_compiler_status(self,get):
        """
        @name 为编译器其他用户设置状态
        @param get.status 0关闭 1开启 不传此参数时，仅获取状态，不设置状态
        """
        
        chmod_limt='0750'
        log_string={'0750':'closed','0755':'enabled'}
        if 'status' in get:
            if int(get.status)==1:chmod_limt='0755'
            public.ExecShell('chmod '+chmod_limt+' '+self.__gcc_path)
            #写日志
            if self.__write_log:
                public.write_log_gettext(self.__log_type,  'Non privileged user successfully {} gcc compiler', (log_string[chmod_limt],))
        limit_status=False
        try:
            accept=oct(os.stat(self.__gcc_path).st_mode)[-4:]
            if accept=='0755':limit_status=True
        except:pass
        return public.return_message(0,0,limit_status)
        
            
        
        
        
        
    
        
    
        
        
        
        
