 #coding: utf-8
# +-------------------------------------------------------------------
# | aaPanel
# +-------------------------------------------------------------------
# | Copyright (c) 2015-2016 aaPanel(www.aapanel.com) All rights reserved.
# +-------------------------------------------------------------------
# | Author: hwliang <hwl@aapanel.com>
# +-------------------------------------------------------------------
from flask import session,request

import public,os,json,time,apache,psutil
class ajax:
    __official_url = 'https://www.aapanel.com'

    def GetApacheStatus(self,get):
        a = apache.apache()
        return a.GetApacheStatus()

    def GetProcessCpuPercent(self,i,process_cpu):
        try:
            pp = psutil.Process(i)
            if pp.name() not in process_cpu.keys():
                process_cpu[pp.name()] = float(pp.cpu_percent(interval=0.01))
            process_cpu[pp.name()] += float(pp.cpu_percent(interval=0.01))
        except:
            pass
    def GetNginxStatus(self,get):
        try:
            if not os.path.exists('/www/server/nginx/sbin/nginx'): return public.return_msg_gettext(False, public.lang("Nginx is not install"))
            process_cpu = {}
            worker = int(public.ExecShell("ps aux|grep nginx|grep 'worker process'|wc -l")[0])-1
            workermen = int(public.ExecShell("ps aux|grep nginx|grep 'worker process'|awk '{memsum+=$6};END {print memsum}'")[0]) / 1024
            for proc in psutil.process_iter():
                if proc.name() == "nginx":
                    self.GetProcessCpuPercent(proc.pid,process_cpu)
            time.sleep(0.1)
            #取Nginx负载状态
            self.CheckStatusConf()
            result = public.httpGet('http://127.0.0.1/nginx_status')
            is_curl = False
            tmp = []
            if result:
                tmp = result.split()
            if len(tmp) < 15: is_curl = True

            if is_curl:
                result = public.ExecShell(
                    'curl http://127.0.0.1/nginx_status')[0]
                tmp = result.split()
            data = {}
            if "request_time" in tmp:
                data['accepts'] = tmp[8]
                data['handled'] = tmp[9]
                data['requests'] = tmp[10]
                data['Reading'] = tmp[13]
                data['Writing'] = tmp[15]
                data['Waiting'] = tmp[17]
            else:
                data['accepts'] = tmp[9]
                data['handled'] = tmp[7]
                data['requests'] = tmp[8]
                data['Reading'] = tmp[11]
                data['Writing'] = tmp[13]
                data['Waiting'] = tmp[15]
            data['active'] = tmp[2]
            data['worker'] = worker
            data['workercpu'] = round(float(process_cpu["nginx"]), 2)
            data['workermen'] = "%s%s" % (int(workermen), "MB")
            return data
        except Exception as ex:
            public.write_log_gettext('Get Info','Nginx load status acquisition failed:{}',(ex,))
            return public.return_msg_gettext(False, public.lang("Data acquisition failed!"))
    
    def GetPHPStatus(self,get):
        #取指定PHP版本的负载状态
        try:
            version = get.version
            uri = "/phpfpm_"+version+"_status?json"
            result = public.request_php(version,uri,'')
            tmp = json.loads(result)
            fTime = time.localtime(int(tmp['start time']))
            tmp['start time'] = time.strftime('%Y-%m-%d %H:%M:%S',fTime)
            return tmp
        except Exception as ex:
            public.write_log_gettext('Get Info',"PHP load status acquisition failed: {}",(public.get_error_info(),))
            return public.return_msg_gettext(False, public.lang("PHP load status acquisition failed!"))
        
    def CheckStatusConf(self):
        if public.get_webserver() != 'nginx': return
        filename = session['setupPath'] + '/panel/vhost/nginx/phpfpm_status.conf'
        if os.path.exists(filename):
            if public.ReadFile(filename).find('nginx_status')!=-1: return
        
        conf = '''server {
    listen 80;
    server_name 127.0.0.1;
    allow 127.0.0.1;
    location /nginx_status {
        stub_status on;
        access_log off;
    }
}'''
        public.writeFile(filename,conf)
        public.serviceReload()
    
    
    def GetTaskCount(self,get):
        #取任务数量
        return public.M('tasks').where("status!=?",('1',)).count()
    
    def GetSoftList(self,get):
        #取软件列表
        import json,os
        tmp = public.readFile('data/softList.conf')
        if not isinstance(tmp, str) or not tmp.strip():
            return []
        try:
            data = json.loads(tmp)
        except Exception as e:
            return []
        tasks = public.M('tasks').where("status!=?",('1',)).field('status,name').select()
        for i in range(len(data)):
            data[i]['check'] = public.GetConfigValue('root_path')+'/'+data[i]['check']
            for n in range(len(data[i]['versions'])):
                #处理任务标记
                isTask = '1'
                for task in tasks:
                    tmp = public.getStrBetween('[',']',task['name'])
                    if not tmp:continue
                    tmp1 = tmp.split('-')
                    if data[i]['name'] == 'PHP': 
                        if tmp1[0].lower() == data[i]['name'].lower() and tmp1[1] == data[i]['versions'][n]['version']: isTask = task['status'];
                    else:
                        if tmp1[0].lower() == data[i]['name'].lower(): isTask = task['status']
                
                #检查安装状态
                if data[i]['name'] == 'PHP': 
                    data[i]['versions'][n]['task'] = isTask
                    checkFile = data[i]['check'].replace('VERSION',data[i]['versions'][n]['version'].replace('.',''))
                else:
                    data[i]['task'] = isTask
                    version = public.readFile(public.GetConfigValue('root_path')+'/server/'+data[i]['name'].lower()+'/version.pl')
                    if not version:continue
                    if version.find(data[i]['versions'][n]['version']) == -1:continue
                    checkFile = data[i]['check']
                data[i]['versions'][n]['status'] = os.path.exists(checkFile)
        return data
    
    
    def GetLibList(self,get):
        #取插件列表
        import json,os
        tmp = public.readFile('data/libList.conf')
        data = json.loads(tmp)
        for i in range(len(data)):
            data[i]['status'] = self.CheckLibInstall(data[i]['check'])
            data[i]['optstr'] = self.GetLibOpt(data[i]['status'], data[i]['opt'])
        return data
    
    def CheckLibInstall(self,checks):
        for cFile in checks:
            if os.path.exists(cFile): return public.GetMsg('Already installed')
        return public.GetMsg('Not installed')
    
    #取插件操作选项
    def GetLibOpt(self,status,libName):
        optStr = ''
        if status == public.GetMsg('Not installed'):
            optStr = '<a class="link" href="javascript:InstallLib(\''+libName+'\');">'+public.GetMsg('Uninstallaton succeeded')+'</a>'
        else:
            libConfig = public.GetMsg('Old configuration')
            if(libName == 'beta'): libConfig = public.GetMsg('Beta tester profile')
                                  
            optStr = '<a class="link" href="javascript:SetLibConfig(\''+libName+'\');">'+libConfig+'</a> | <a class="link" href="javascript:UninstallLib(\''+libName+'\');">'+public.lang("Uninstallaton succeeded")+'</a>';
        return optStr
    
    #取插件AS
    def GetQiniuAS(self,get):
        filename = public.GetConfigValue('setup_path') + '/panel/data/'+get.name+'As.conf'
        if not os.path.exists(filename): public.writeFile(filename,'')
        data = {}
        data['AS'] = public.readFile(filename).split('|')
        data['info'] = self.GetLibInfo(get.name)
        if len(data['AS']) < 3:
            data['AS'] = ['','','','']
        return data


    #设置插件AS
    def SetQiniuAS(self,get):
        info = self.GetLibInfo(get.name)
        filename = public.GetConfigValue('setup_path') + '/panel/data/'+get.name+'As.conf'
        conf = get.access_key.strip() + '|' + get.secret_key.strip() + '|' + get.bucket_name.strip() + '|' + get.bucket_domain.strip()
        public.writeFile(filename,conf)
        if not os.path.exists(filename):
            return public.return_msg_gettext(False, public.lang("write file failed!"))
        public.ExecShell("chmod 600 " + filename)
        result = public.ExecShell(public.get_python_bin() + " " + public.GetConfigValue('setup_path') + "/panel/script/backup_"+get.name+".py list")
        
        if result[0].find("ERROR:") == -1: 
            public.write_log_gettext("Plugin manager","Set plugin [" +info['name']+ "]AS!")
            return public.return_msg_gettext(True, public.lang("Successfully set"))
        return public.return_msg_gettext(False,'ERROR: Unable to connect to the {} server, please check if the [AK/SK/Storage] setting is correct!',(info['name'],))
    
    #设置内测
    def SetBeta(self,get):
        data = {}
        data['username'] = get.bbs_name
        data['qq'] = get.qq
        data['email'] = get.email
        result = public.httpPost(public.GetConfigValue('home') + '/Api/LinuxBeta',data)
        import json
        data = json.loads(result)
        if data['status']:
            public.writeFile('data/beta.pl',get.bbs_name + '|' + get.qq + '|' + get.email)
        return data
    #取内测资格状态
    def GetBetaStatus(self,get):
        try:
            return public.readFile('data/beta.pl').strip()
        except:
            return 'False'
               

    #获取指定插件信息
    def GetLibInfo(self,name):
        import json
        tmp = public.readFile('data/libList.conf')
        data = json.loads(tmp)
        for lib in data:
            if name == lib['opt']: return lib
        return False

    #获取文件列表
    def GetQiniuFileList(self,get):
        try:
            import json             
            result = public.ExecShell(public.get_python_bin() + " " + public.GetConfigValue('setup_path') + "/panel/script/backup_"+get.name+".py list")
            return json.loads(result[0])
        except:
            return public.return_msg_gettext(False, public.lang("Failed to get the list, please check if the [AK/SK/Storage] setting is correct!"))

    
    
    #取网络连接列表
    def GetNetWorkList(self,get):
        import psutil
        netstats = psutil.net_connections()
        networkList = []
        for netstat in netstats:
            tmp = {}
            if netstat.type == 1:
                tmp['type'] = 'tcp'
            else:
                tmp['type'] = 'udp'
            tmp['family'] = netstat.family
            tmp['laddr'] = netstat.laddr
            tmp['raddr'] = netstat.raddr
            tmp['status'] = netstat.status
            p = psutil.Process(netstat.pid)
            tmp['process'] = p.name()
            tmp['pid'] = netstat.pid
            networkList.append(tmp)
            del (p)
            del (tmp)
        networkList = sorted(networkList,
                             key=lambda x: x['status'],
                             reverse=True)
        return networkList

    #取进程列表
    def GetProcessList(self, get):
        import psutil, pwd
        Pids = psutil.pids()

        processList = []
        for pid in Pids:
            try:
                tmp = {}
                p = psutil.Process(pid)
                if p.exe() == "": continue

                tmp['name'] = p.name()
                #进程名称
                if self.GoToProcess(tmp['name']): continue

                tmp['pid'] = pid
                #进程标识
                tmp['status'] = p.status()
                #进程状态
                tmp['user'] = p.username()
                #执行用户
                cputimes = p.cpu_times()
                tmp['cpu_percent'] = p.cpu_percent(0.1)
                tmp['cpu_times'] = cputimes.user  #进程占用的CPU时间
                tmp['memory_percent'] = round(p.memory_percent(),
                                              3)  #进程占用的内存比例
                pio = p.io_counters()
                tmp['io_write_bytes'] = pio.write_bytes  #进程总共写入字节数
                tmp['io_read_bytes'] = pio.read_bytes  #进程总共读取字节数
                tmp['threads'] = p.num_threads()  #进程总线程数

                processList.append(tmp)
                del (p)
                del (tmp)
            except:
                continue
        import operator
        processList = sorted(processList,
                             key=lambda x: x['memory_percent'],
                             reverse=True)
        processList = sorted(processList,
                             key=lambda x: x['cpu_times'],
                             reverse=True)
        return processList

    #结束指定进程
    def KillProcess(self, get):
        #return public.returnMsg(False, public.lang("演示服务器，禁止此操作!"));
        import psutil
        p = psutil.Process(int(get.pid))
        name = p.name()
        if name == 'python': return public.return_msg_gettext(False, public.lang("Error, cannot end task processes!"))
        
        p.kill()
        public.write_log_gettext('Task manager','Ended processes[{}][{}] Successfully!',(get.pid,name))
        return public.return_msg_gettext(True,'Ended processes[{}][{}] Successfully!',(get.pid,name))
    
    def GoToProcess(self,name):
        ps = ['sftp-server','login','nm-dispatcher','irqbalance','qmgr','wpa_supplicant','lvmetad','auditd','master','dbus-daemon','tapdisk','sshd','init','ksoftirqd','kworker','kmpathd','kmpath_handlerd','python','kdmflush','bioset','crond','kthreadd','migration','rcu_sched','kjournald','iptables','systemd','network','dhclient','systemd-journald','NetworkManager','systemd-logind','systemd-udevd','polkitd','tuned','rsyslogd']
        
        for key in ps:
            if key == name: return True
        
        return False
        
    
    def GetNetWorkIo(self,get):
        #取指定时间段的网络Io
        data = public.M('network').dbfile('system').where(
            "addtime>=? AND addtime<=?", (get.start, get.end)
        ).field(
            'id,up,down,total_up,total_down,down_packets,up_packets,addtime'
        ).order('id desc').select()
        return self.ToAddtime(data, None)

    def GetDiskIo(self, get):
        #取指定时间段的磁盘Io
        __OPT_FIELD = "*"
        tmp_cols = public.M('diskio').dbfile('system').query(
            'PRAGMA table_info(diskio)', ())
        cols = []
        for col in tmp_cols:
            if len(col) > 2: cols.append('`' + col[1] + '`')
        if len(cols) > 0:
            cols.append("disk_top")
            __OPT_FIELD = ','.join(cols)
        data = public.M('diskio').dbfile('system').query(
            "SELECT diskio.*,process_top_list.disk_top from diskio inner join process_top_list on diskio.addtime=process_top_list.addtime where diskio.addtime>={} AND diskio.addtime<={} ORDER BY diskio.addtime desc;"
            .format(get.start, get.end), ())
        if isinstance(data, str) and data.find(
                'error: no such table: process_top_list') != -1:
            return public.M('diskio').dbfile('system').where(
                "addtime>=? AND addtime<=?", (get.start, get.end)
            ).field(
                'id,read_count,write_count,read_bytes,write_bytes,read_time,write_time,addtime'
            ).order('id asc').select()
        try:
            if __OPT_FIELD != "*":
                fields = self.__format_field(__OPT_FIELD.split(','))
                tmp = []
                for row in data:
                    i = 0
                    tmp1 = {}
                    for key in fields:
                        tmp1[key.strip('`')] = row[i]
                        i += 1
                    tmp.append(tmp1)
                    del (tmp1)
                data = tmp
        except:
            return []
        return self.ToAddtime(data, True, 'disk')


    def __format_field(self,field):
        import re
        fields = []
        for key in field:
            s_as = re.search(r'\s+as\s+',key,flags=re.IGNORECASE)
            if s_as:
                as_tip = s_as.group()
                key = key.split(as_tip)[1]
            fields.append(key)
        return fields

    def GetCpuIo(self, get):
        #取指定时间段的CpuIo
        __OPT_FIELD = "*"
        tmp_cols = public.M('cpuio').dbfile('system').query(
            'PRAGMA table_info(cpuio)', ())
        cols = []
        for col in tmp_cols:
            if len(col) > 2: cols.append('`' + col[1] + '`')
        if len(cols) > 0:
            cols.append("cpu_top")
            cols.append("memory_top")
            __OPT_FIELD = ','.join(cols)
        data = public.M('cpuio').dbfile('system').query(
            "SELECT cpuio.*,process_top_list.cpu_top,process_top_list.memory_top from cpuio inner join process_top_list on cpuio.addtime=process_top_list.addtime where cpuio.addtime>={} AND cpuio.addtime<={} ORDER BY cpuio.addtime desc;"
            .format(get.start, get.end), ())
        if isinstance(data, str) and data.find(
                'error: no such table: process_top_list') != -1:
            return public.M('cpuio').dbfile('system').where(
                "addtime>=? AND addtime<=?",
                (get.start, get.end
                 )).field('id,pro,mem,addtime').order('id asc').select()
        try:
            if __OPT_FIELD != "*":
                fields = self.__format_field(__OPT_FIELD.split(','))
                tmp = []
                for row in data:
                    i = 0
                    tmp1 = {}
                    for key in fields:
                        tmp1[key.strip('`')] = row[i]
                        i += 1
                    tmp.append(tmp1)
                    del (tmp1)
                data = tmp
        except:
            return []
        return self.ToAddtime(data, True, 'cpu')

    def get_load_average(self, get):
        __OPT_FIELD = "*"
        tmp_cols = public.M('load_average').dbfile('system').query(
            'PRAGMA table_info(load_average)', ())
        cols = []
        for col in tmp_cols:
            if len(col) > 2: cols.append('`' + col[1] + '`')
        if len(cols) > 0:
            cols.append("cpu_top")
            __OPT_FIELD = ','.join(cols)
        data = public.M('load_average').dbfile('system').query(
            "SELECT load_average.*,process_top_list.cpu_top from load_average inner join process_top_list on load_average.addtime=process_top_list.addtime where load_average.addtime>={} AND load_average.addtime<={} ORDER BY load_average.addtime desc;"
            .format(get.start, get.end), ())
        if isinstance(data, str) and data.find(
                'error: no such table: process_top_list') != -1:
            return public.M('load_average').dbfile('system').where(
                "addtime>=? AND addtime<=?",
                (get.start, get.end)).field('id,pro,one,five,fifteen,addtime'
                                            ).order('id asc').select()
        try:
            if __OPT_FIELD != "*":
                fields = self.__format_field(__OPT_FIELD.split(','))
                tmp = []
                for row in data:
                    i = 0
                    tmp1 = {}
                    for key in fields:
                        tmp1[key.strip('`')] = row[i]
                        i += 1
                    tmp.append(tmp1)
                    del (tmp1)
                data = tmp
        except:
            return []
        return self.ToAddtime(data, True, 'cpu')

    def get_process_tops(self, get):
        '''
            @name 获取进程开销排行
            @author hwliang<2021-09-07>
            @param get<dict_obj>{
                start: int<开始时间>
                end: int<结束时间>
            }
            @return list
        '''
        data = public.M('process_tops').dbfile('system').where(
            "addtime>=? AND addtime<=?",
            (get.start, get.end
             )).field('id,process_list,addtime').order('id asc').select()
        return self.ToAddtime(data)

    def get_process_cpu_high(self, get):
        '''
            @name 获取CPU占用高的进程列表
            @author hwliang<2021-09-07>
            @param get<dict_obj>{
                start: int<开始时间>
                end: int<结束时间>
            }
            @return list
        '''
        data = public.M('process_high_percent').dbfile('system').where(
            "addtime>=? AND addtime<=?", (get.start, get.end)).field(
                'id,name,pid,cmdline,cpu_percent,memory,cpu_time_total,addtime'
            ).order('id asc').select()
        return self.ToAddtime(data)

    def ToAddtime(self, data, tomem=False, types=None):
        import time
        #格式化addtime列

        if tomem:
            import psutil
            mPre = (psutil.virtual_memory().total / 1024 / 1024) / 100
        length = len(data)
        he = 1
        if length > 100: he = 1
        if length > 1000: he = 3
        if length > 10000: he = 15
        if he == 1:
            for i in range(length):
                try:
                    if types:
                        key = '{}_top'.format(types)
                        if key in data[i]:
                            data[i][key] = json.loads(data[i][key])
                        if 'memory_top' in data[i]:
                            data[i]['memory_top'] = json.loads(
                                data[i]['memory_top'])
                    data[i]['addtime'] = time.strftime(
                        '%m/%d %H:%M',
                        time.localtime(float(data[i]['addtime'])))
                    if 'process_list' in data[i]:
                        data[i]['process_list'] = json.loads(
                            data[i]['process_list'])
                    if tomem and data[i]['mem'] > 100:
                        data[i]['mem'] = data[i]['mem'] / mPre
                    if tomem in [None]:
                        if type(data[i]['down_packets']) == str:
                            data[i]['down_packets'] = json.loads(
                                data[i]['down_packets'])
                            data[i]['up_packets'] = json.loads(
                                data[i]['up_packets'])
                except:
                    continue
            return data
        else:
            count = 0
            tmp = []
            couns = 0
            for value in data:
                if count < he:  # 0 1 2
                    count += 1
                    #cpu大于60的时候，随机取
                    if types == "cpu" and 'pro' in value and value['pro'] > 60:
                        couns += 1
                        #he等于3 的时候 百分之50的概率取  当he等于15的时候 百分之33的概率取
                        if (he == 3
                                and couns % 2 == 0) or (he == 15
                                                        and couns % 3 == 0):
                            if types:
                                key = '{}_top'.format(types)
                                if key in value:
                                    value[key] = json.loads(value[key])
                                if 'memory_top' in value:
                                    value['memory_top'] = json.loads(
                                        value['memory_top'])
                            value['addtime'] = time.strftime(
                                '%m/%d %H:%M',
                                time.localtime(float(value['addtime'])))
                            if tomem and 'mem' in value and value['mem'] > 100:
                                value['mem'] = value['mem'] / mPre
                            if tomem in [None]:
                                if type(value['down_packets']) == str:
                                    value['down_packets'] = json.loads(value['down_packets'])
                                    value['up_packets'] = json.loads(value['up_packets'])
                            tmp.append(value)
                    continue
                try:
                    if types:
                        key='{}_top'.format(types)
                        if key in value:
                            value[key] = json.loads(value[key])
                        if 'memory_top' in value:
                            value['memory_top'] = json.loads(value['memory_top'])
                    value['addtime'] = time.strftime('%m/%d %H:%M',time.localtime(float(value['addtime'])))
                    if tomem and 'mem' in value and  value['mem'] > 100: value['mem'] = value['mem'] / mPre
                    if tomem in [None]:
                        if type(value['down_packets']) == str:
                            value['down_packets'] = json.loads(value['down_packets'])
                            value['up_packets'] = json.loads(value['up_packets'])
                    tmp.append(value)
                    count = 0
                except: continue
            return tmp



    def GetInstalleds(self,softlist):
        softs = ''
        for soft in softlist['data']:
            try:
                for v in soft['versions']:
                    if v['status']: softs += soft['name'] + '-' + v['version'] + '|'
            except:
                pass
        return softs



    #获取SSH爆破次数
    def get_ssh_intrusion(self):
        fp = open('/var/log/secure','rb')
        l = fp.readline()
        intrusion_total = 0
        while l:
            if l.find('Failed password for root') != -1:  intrusion_total += 1
            l = fp.readline()
        fp.close()
        return intrusion_total

    #申请内测版
    def apple_beta(self,get):
        try:
            # userInfo = json.loads(public.ReadFile('data/userInfo.json'))
            # p_data = {}
            # p_data['uid'] = userInfo['uid']
            # p_data['access_key'] = userInfo['access_key']
            # p_data['username'] = userInfo['username']
            # result = public.HttpPost(public.GetConfigValue('home') + '/api/panel/apple_beta',p_data,5)
            public.writeFile('/www/server/panel/data/is_beta.pl','true')
            try:
                return {'status': True, 'msg': "Successful application!"}
            except: return public.return_msg_gettext(False, public.lang("Fail to connect to the server!"))
        except: return public.return_msg_gettext(False, public.lang("Please bind your account first!"))

    def to_not_beta(self,get):
        try:
            # userInfo = json.loads(public.ReadFile('data/userInfo.json'))
            # p_data = {}
            # p_data['uid'] = userInfo['uid']
            # p_data['access_key'] = userInfo['access_key']
            # p_data['username'] = userInfo['username']
            # result = public.HttpPost(public.GetConfigValue('home') + '/api/panel/to_not_beta',p_data,5)
            try:
                beta_file = '/www/server/panel/data/is_beta.pl'
                if os.path.exists(beta_file):
                    os.remove(beta_file)
                return {"status": True, "msg": "Successful application!"}
            except: return public.return_msg_gettext(False, public.lang("Fail to connect to the server!"))
        except: return public.return_msg_gettext(False, public.lang("Please bind your account first!"))

    def to_beta(self):
        try:
            userInfo = json.loads(public.ReadFile('data/userInfo.json'))
            p_data = {}
            p_data['uid'] = userInfo['uid']
            p_data['access_key'] = userInfo['access_key']
            p_data['username'] = userInfo['username']
            public.HttpPost(public.GetConfigValue('home') + '/api/panel/to_beta',p_data,5)
        except: pass

    def get_uid(self):
        try:
            userInfo = json.loads(public.ReadFile('data/userInfo.json'))
            return userInfo['uid']
        except: return 0

    #获取最新的5条测试版更新日志
    def get_beta_logs(self,get):
        try:
            data = json.loads(public.HttpGet('{}/api/panel/getBetaVersionLogs'.format(self.__official_url)))
            return data
        except:
            return public.return_msg_gettext(False, public.lang("Fail to connect to the server!"))

    def get_other_info(self):
        other = {}
        other['ds'] = []
        ds = public.M('domain').field('name').select()
        for d in ds:
            other['ds'].append(d['name'])
        return ','.join(other['ds'])



    #  更新面板
    def UpdatePanel(self,get):
        try:
            if not public.IsRestart(): return public.return_msg_gettext(False, public.lang("Please run the program when all install tasks finished!"))
            import json
            conf_status = public.M('config').where("id=?",('1',)).field('status').find()
            if int(session['config']['status']) == 0 and int(conf_status['status']) == 0:
                public.arequests('get', '{}/api/setupCount/setupPanel?type=Linux'.format(self.__official_url))
                public.M('config').where("id=?",('1',)).setField('status',1)
            
            #取回远程版本信息
            if 'updateInfo' in session and hasattr(get,'check') == False:
                updateInfo = session['updateInfo']
            else:
                logs = public.get_debug_log()
                import psutil,system,sys
                mem = psutil.virtual_memory()
                import panelPlugin
                mplugin = panelPlugin.panelPlugin()

                mplugin.ROWS = 10000
                panelsys = system.system()
                data = {}
                data['ds'] = ''#self.get_other_info()
                data['sites'] = str(public.M('sites').count())
                data['ftps'] = str(public.M('ftps').count())
                data['databases'] = str(public.M('databases').count())
                data['system'] = panelsys.GetSystemVersion() + '|' + str(mem.total / 1024 / 1024) + 'MB|' + str(public.getCpuType()) + '*' + str(psutil.cpu_count()) + '|' + str(public.get_webserver()) + '|' +session['version']
                data['system'] += '||'+self.GetInstalleds(mplugin.getPluginList(None))
                data['logs'] = logs
                data['client'] = request.headers.get('User-Agent')
                data['oem'] = ''
                data['intrusion'] = 0
                data['uid'] = self.get_uid()
                #msg = public.getMsg('Current version is stable version and already latest. Update cycle of stable version is generally 2 months，while developer version will update every Wednesday!');
                data['o'] = public.get_oem_name()
                sUrl = '{}/api/panel/updateLinuxEn'.format(self.__official_url)
                updateInfo = json.loads(public.httpPost(sUrl,data))
                if not updateInfo: return public.return_msg_gettext(False, public.lang("Failed to connect server!"))
                #updateInfo['msg'] = msg;
                if os.path.exists('/www/server/panel/data/is_beta.pl'):
                    updateInfo['is_beta'] = 1
                session['updateInfo'] = updateInfo


            # 输出忽略的版本
            updateInfo['ignore'] = []
            no_path = '{}/data/no_update.pl'.format(public.get_panel_path())
            if os.path.exists(no_path):
                try:
                    updateInfo['ignore'] = json.loads(public.readFile(no_path))
                except:
                    pass

            # 重启面板 默认开启系统监控
            # public.writeFile('data/control.conf', '30')


            #检查是否需要升级
            if not hasattr(get,'toUpdate'):
                if updateInfo['is_beta'] == 1:
                    if updateInfo['beta']['version'] == session['version']: return public.returnMsg(False,updateInfo)
                else:
                    if updateInfo['version'] == session['version']: return public.returnMsg(False,updateInfo)
            
            
            #是否执行升级程序 
            if(updateInfo['force'] == True or hasattr(get,'toUpdate') == True or os.path.exists('data/autoUpdate.pl') == True):
                if updateInfo['is_beta'] == 1: updateInfo['version'] = updateInfo['beta']['version']
                setupPath = public.GetConfigValue('setup_path')
                uptype = 'update'
                httpUrl = public.get_url()
                if httpUrl: updateInfo['downUrl'] =  httpUrl + '/install/' + uptype + '/LinuxPanel_EN-' + updateInfo['version'] + '.zip'
                public.downloadFile(updateInfo['downUrl'],'panel.zip')
                if os.path.getsize('panel.zip') < 1048576: return public.return_msg_gettext(False, public.lang("File download failed, please try again or update manually!"))
                cmd = 'unzip -o panel.zip -d {}/ && chmod 700 {}/panel/BT-Panel'.format(setupPath, setupPath)
                public.print_log(cmd)
                public.ExecShell(cmd)

                if os.path.exists('/www/server/panel/runserver.py'): public.ExecShell('rm -f /www/server/panel/*.pyc')
                if os.path.exists('/www/server/panel/class/common.py'): public.ExecShell('rm -f /www/server/panel/class/*.pyc')
                
                if os.path.exists('panel.zip'):os.remove("panel.zip")
                session['version'] = updateInfo['version']
                if 'getCloudPlugin' in session: del(session['getCloudPlugin'])
                if updateInfo['is_beta'] == 1: self.to_beta()
                public.ExecShell("/etc/init.d/bt start")
                public.writeFile('data/restart.pl','True')
                return public.return_msg_gettext(True,'Successful to update to {}',(updateInfo['version'],))

            public.ExecShell('rm -rf /www/server/phpinfo/*')
            return public.returnMsg(True,updateInfo)
        except Exception as ex:
            return public.get_error_info()
            return public.return_msg_gettext(False, public.lang("Failed to connect server!"))

    #检查是否安装任何
    def CheckInstalled(self,get):
        checks = ['nginx','apache','php','pure-ftpd','mysql']
        import os
        for name in checks:
            filename = public.GetConfigValue('root_path') + "/server/" + name
            if os.path.exists(filename): return True
        return False
    
    
    #取已安装软件列表
    def GetInstalled(self,get):
        import system
        data = system.system().GetConcifInfo()
        return data
    
    #取PHP配置
    def GetPHPConfig(self,get):
        import re,json
        filename = public.GetConfigValue('setup_path') + '/php/' + get.version + '/etc/php.ini'
        if public.get_webserver() == 'openlitespeed':
            filename = '/usr/local/lsws/lsphp{}/etc/php/{}.{}/litespeed/php.ini'.format(get.version,get.version[0],get.version[1])
            if os.path.exists('/etc/redhat-release'):
                filename = '/usr/local/lsws/lsphp' + get.version + '/etc/php.ini'
        if not os.path.exists(filename): return public.return_msg_gettext(False, public.lang("Requested PHP version does NOT exist!"))
        phpini = public.readFile(filename)
        data = {}
        rep = "disable_functions\\s*=\\s{0,1}(.*)\n"

        tmp = re.search(rep,phpini)
        if tmp:
            data['disable_functions'] = tmp.groups()[0]
        
        rep = r"upload_max_filesize\s*=\s*([0-9]+)(M|m|K|k)"

        tmp = re.search(rep,phpini)
        if tmp:
            data['max'] = tmp.groups()[0]
        
        rep = u"\n;*\\s*cgi\\.fix_pathinfo\\s*=\\s*([0-9]+)\\s*\n"
        tmp = re.search(rep,phpini)
        if tmp:
            if tmp.groups()[0] == '0':
                data['pathinfo'] = False
            else:
                data['pathinfo'] = True

        self.getCloudPHPExt(get)
        phplib = json.loads(public.readFile('data/phplib.conf'))
        libs = []
        tasks = public.M('tasks').where("status!=?",('1',)).field('status,name').select()
        phpini_ols = None
        for lib in phplib:
            lib['task'] = '1'
            for task in tasks:
                tmp = public.getStrBetween('[',']',task['name'])
                if not tmp:continue
                tmp1 = tmp.split('-')
                if tmp1[0].lower() == lib['name'].lower():
                    lib['task'] = task['status']
                    lib['phpversions'] = []
                    lib['phpversions'].append(tmp1[1])
            if public.get_webserver() == 'openlitespeed':
                lib['status'] = False
                get.php_version = "{}.{}".format(get.version[0],get.version[1])
                if not phpini_ols:
                    phpini_ols = self.php_info(get)['phpinfo']['modules'].lower()
                    phpini_ols = phpini_ols.split()
                for i in phpini_ols:
                    if lib['check'][:-3].lower() == i :
                        lib['status'] = True
                        break
                    if "ioncube" in lib['check'][:-3].lower() and "ioncube" == i:
                        lib['status'] = True
                        break
            else:
                if phpini.find(lib['check']) == -1:
                    lib['status'] = False
                else:
                    lib['status'] = True
                
            libs.append(lib)
        
        data['libs'] = libs
        return data
        
    #获取PHP扩展
    def getCloudPHPExt(self,get):
        try:
            self._process_chinese_ext_description()
            if 'php_ext' in session: return True
            if not self._get_cloud_phplib():
                return False
            session['php_ext'] = True
            return True
        except:
            return False

    # 处理PHP插件变描述中文
    def _process_chinese_ext_description(self):
        chinese = None
        phplib = json.loads(public.readFile('data/phplib.conf'))
        for p in phplib:
            if "缓存器" in p['type']:
                chinese = True
                break
        if chinese:
            self._get_cloud_phplib()

    # 下载云端php扩展配置
    def _get_cloud_phplib(self):
        if not session.get('download_url'): session['download_url'] = 'https://node.aapanel.com'
        download_url = session['download_url'] + '/install/lib/phplib_en.json'
        tstr = public.httpGet(download_url)
        data = json.loads(tstr)
        if not data: return False
        public.writeFile('data/phplib.conf', json.dumps(data))
        return True

    #取PHPINFO信息
    def GetPHPInfo(self,get):
        if public.get_webserver() == "openlitespeed":
            shell_str = "/usr/local/lsws/lsphp{}/bin/php -i".format(get.version)
            return public.ExecShell(shell_str)[0]
        sPath = '/www/server/phpinfo'
        if os.path.exists(sPath):
            public.ExecShell("rm -rf " + sPath)
        p_file = '/dev/shm/phpinfo.php'
        public.writeFile(p_file,'<?php phpinfo(); ?>')
        phpinfo = public.request_php(get.version,'/phpinfo.php','/dev/shm')
        if os.path.exists(p_file): os.remove(p_file)
        return phpinfo.decode()

    #清理日志
    def delClose(self,get):
        if not 'uid' in session: session['uid'] = 1
        if session['uid'] != 1: return public.return_msg_gettext(False, public.lang("Permission denied!"))
        if 'tmp_login_id' in session:
            return public.return_msg_gettext(False, public.lang("Permission denied!"))

        # 备份近100条日志
        new_bak = public.M('logs').limit('100').select()
        if len(new_bak) > 3:
            bak_file = '{}/data/logs.bak'.format(public.get_panel_path())
            public.writeFile(bak_file,json.dumps(new_bak))
        public.add_security_logs("Clear the log", 'The number of log entries cleared is:{}'.format(public.M('logs').count()))
        # 清空日志
        public.M('logs').where('id>?',(0,)).delete()
        public.write_log_gettext('Panel setting','Panel Logs emptied!')
        return public.return_msg_gettext(True, public.lang("Panel Logs emptied!"))

    def __get_webserver_conffile(self):
        webserver = public.get_webserver()
        if webserver == 'nginx':
            filename = public.GetConfigValue('setup_path') + '/nginx/conf/nginx.conf'
        elif webserver == 'openlitespeed':
            filename = public.GetConfigValue('setup_path') + "/panel/vhost/openlitespeed/detail/phpmyadmin.conf"
        else:
            filename = public.GetConfigValue('setup_path') + '/apache/conf/extra/httpd-vhosts.conf'
        return filename

    # 获取phpmyadmin ssl配置
    def get_phpmyadmin_conf(self):
        if public.get_webserver() == "nginx":
            conf_file = "/www/server/panel/vhost/nginx/phpmyadmin.conf"
            rep = r"listen\s*(\d+)"
        else:
            conf_file = "/www/server/panel/vhost/apache/phpmyadmin.conf"
            rep = r"Listen\s*(\d+)"
        return {"conf_file":conf_file,"rep":rep}

    # 设置phpmyadmin路径
    def set_phpmyadmin_session(self):
        import re
        conf_file = self.get_phpmyadmin_conf()
        conf = public.readFile(conf_file["conf_file"])
        rep = conf_file["rep"]
        if conf:
            port = re.search(rep,conf).group(1)
            if session['phpmyadminDir']:
                path = session['phpmyadminDir'].split("/")[-1]
                ip = public.GetHost()
                session['phpmyadminDir'] = "https://{}:{}/{}".format(ip, port, path)

    # 获取phpmyadmin ssl状态
    def get_phpmyadmin_ssl(self,get):
        import re
        conf_file = self.get_phpmyadmin_conf()
        conf = public.readFile(conf_file["conf_file"])
        rep = conf_file["rep"]
        if conf:
            port = re.search(rep, conf).group(1)
            return {"status":True,"port":port}
        return {"status":False,"port":""}

    # 修改php ssl端口
    def change_phpmyadmin_ssl_port(self,get):
        if public.get_webserver() == "openlitespeed":
            return public.return_msg_gettext(False, public.lang("The current web server is openlitespeed. This function is not supported yet."))
        import re
        try:
            port = int(get.port)
            if 1 > port > 65535:
                return public.return_msg_gettext(False, public.lang("Port range is incorrect!"))
        except:
            return public.return_msg_gettext(False, public.lang("Please enter the correct port number"))
        for i in ["nginx","apache"]:
            file = "/www/server/panel/vhost/{}/phpmyadmin.conf".format(i)
            conf = public.readFile(file)
            if not conf:
                return public.return_msg_gettext(False,'Did not find the {} configuration file, please try to close the ssl port settings before opening',(i,))
            rulePort = ['80', '443', '21', '20', '8080', '8081', '8089', '11211', '6379']
            if get.port in rulePort:
                return public.return_msg_gettext(False, public.lang("Please do NOT use the usual port as the phpMyAdmin port!"))
            if i == "nginx":
                if not os.path.exists("/www/server/panel/vhost/apache/phpmyadmin.conf"):
                    return public.return_msg_gettext(False, public.lang("Did not find the apache phpmyadmin ssl configuration file, please try to close the ssl port settings before opening"))
                rep = r"listen\s*([0-9]+)\s*.*;"
                oldPort = re.search(rep, conf)
                if not oldPort:
                    return public.return_msg_gettext(False, public.lang("Did not detect the port that nginx phpmyadmin listens, please confirm whether the file has been manually modified."))
                oldPort = oldPort.groups()[0]
                conf = re.sub(rep, 'listen ' + get.port + ' ssl;', conf)
            else:
                rep = r"Listen\s*([0-9]+)\s*\n"
                oldPort = re.search(rep, conf)
                if not oldPort:
                    return public.return_msg_gettext(False, public.lang("Did not detect the port that apache phpmyadmin listens, please confirm whether the file has been manually modified."))
                oldPort = oldPort.groups()[0]
                conf = re.sub(rep, "Listen " + get.port + "\n", conf, 1)
                rep = r"VirtualHost\s*\*:[0-9]+"
                conf = re.sub(rep, "VirtualHost *:" + get.port, conf, 1)
            if oldPort == get.port: return public.return_msg_gettext(False, 'Port [{}] is in use!',(get.port,))
            public.writeFile(file, conf)
            public.serviceReload()
            if i=="apache":
                import firewalls
                # aapanel 使用 get_msg_gettext
                get.ps = public.lang("New phpMyAdmin SSL Port")
                fw = firewalls.firewalls()
                fw.AddAcceptPort(get)
                public.serviceReload()
                public.write_log_gettext('Software manager', 'Modified access port to {} for phpMyAdmin!', (get.port,))
                get.id = public.M('firewall').where('port=?', (oldPort,)).getField('id')
                get.port = oldPort
                fw.DelAcceptPort(get)
        return public.return_msg_gettext(True, public.lang("Setup successfully!"))

    def _get_phpmyadmin_auth(self):
        import re
        nginx_conf = '/www/server/nginx/conf/nginx.conf'
        reg = '#AUTH_START(.|\n)*#AUTH_END'
        if os.path.exists(nginx_conf):
            nginx_conf = public.readFile(nginx_conf)
            auth_tmp = re.search(reg, nginx_conf)
            if auth_tmp:
                return True
        apache_conf = '/www/server/apache/conf/extra/httpd-vhosts.conf'
        if os.path.exists(apache_conf):
            apache_conf = public.readFile(apache_conf)
            auth_tmp = re.search(reg, apache_conf)
            if auth_tmp:
                return True

    # 设置phpmyadmin ssl
    def set_phpmyadmin_ssl(self,get):
        if public.get_webserver() == "openlitespeed":
            return public.return_msg_gettext(False, public.lang("The current web server is openlitespeed. This function is not supported yet."))
        if not os.path.exists("/www/server/panel/ssl/certificate.pem"):
            return public.return_msg_gettext(False, public.lang("The panel certificate does not exist. Please apply for the panel certificate and try again."))
        if get.v == "1":
            # 获取auth信息
            auth = ""
            if self._get_phpmyadmin_auth():
                auth = """
        #AUTH_START
        auth_basic "Authorization";
        auth_basic_user_file /www/server/pass/phpmyadmin.pass;
        #AUTH_END
"""
        # nginx配置文件
            ssl_conf = r"""server
    {
        listen 887 ssl;
        server_name phpmyadmin;
        index index.html index.htm index.php;
        root  /www/server/phpmyadmin;
        #SSL-START SSL相关配置，请勿删除或修改下一行带注释的404规则
        #error_page 404/404.html;
        ssl_certificate    /www/server/panel/ssl/certificate.pem;
        ssl_certificate_key    /www/server/panel/ssl/privateKey.pem;
        ssl_protocols TLSv1 TLSv1.1 TLSv1.2 TLSv1.3;
        ssl_ciphers ECDHE-RSA-AES128-GCM-SHA256:HIGH:!aNULL:!MD5:!RC4:!DHE;
        ssl_prefer_server_ciphers on;
        ssl_session_cache shared:SSL:10m;
        ssl_session_timeout 10m;
        error_page 497  https://$host$request_uri;
        #SSL-END
        %s
        include enable-php.conf;
        location ~ .*\.(gif|jpg|jpeg|png|bmp|swf)$
        {
            expires      30d;
        }
        location ~ .*\.(js|css)?$
        {
            expires      12h;
        }
        location ~ /\.
        {
            deny all;
        }
        access_log  /www/wwwlogs/access.log;
    }""" % auth
            public.writeFile("/www/server/panel/vhost/nginx/phpmyadmin.conf",ssl_conf)
            import panelPlugin
            get.sName = "phpmyadmin"
            v = panelPlugin.panelPlugin().get_soft_find(get)
            if self._get_phpmyadmin_auth():
                auth = """
        #AUTH_START
        AuthType basic
        AuthName "Authorization "
        AuthUserFile /www/server/pass/phpmyadmin.pass
        Require user jose
        #AUTH_END
            """
            # apache配置
            ssl_conf = r'''Listen 887
<VirtualHost *:887>
    ServerAdmin webmaster@example.com
    DocumentRoot "/www/server/phpmyadmin"
    ServerName 0b842aa5.phpmyadmin
    ServerAlias phpmyadmin.com
    #ErrorLog "/www/wwwlogs/BT_default_error.log"
    #CustomLog "/www/wwwlogs/BT_default_access.log" combined
    
    #SSL
    SSLEngine On
    SSLCertificateFile /www/server/panel/ssl/certificate.pem
    SSLCertificateKeyFile /www/server/panel/ssl/privateKey.pem
    SSLCipherSuite EECDH+AESGCM:EDH+AESGCM:AES256+EECDH:AES256+EDH
    SSLProtocol All -SSLv2 -SSLv3
    SSLHonorCipherOrder On
    
    #PHP
    <FilesMatch \.php$>
           SetHandler "proxy:{}"
    </FilesMatch>
    
    #DENY FILES
    <Files ~ (\.user.ini|\.htaccess|\.git|\.svn|\.project|LICENSE|README.md)$>
      Order allow,deny
      Deny from all
    </Files>
    
    #PATH
    <Directory "/www/wwwroot/bt.youbadbad.cn/">
{}
       SetOutputFilter DEFLATE
       Options FollowSymLinks
       AllowOverride All
       Require all granted
       DirectoryIndex index.php index.html index.htm default.php default.html default.htm
    </Directory>
</VirtualHost>'''.format(public.get_php_proxy(v["ext"]["phpversion"],'apache'),auth)
            public.writeFile("/www/server/panel/vhost/apache/phpmyadmin.conf", ssl_conf)

            import firewalls
            fw = firewalls.firewalls()
            fw.AddAcceptPort(public.to_dict_obj({
                'port': '887',
                'ps': public.lang("New phpMyAdmin SSL Port"),
            }))
        else:
            if os.path.exists("/www/server/panel/vhost/nginx/phpmyadmin.conf"):
                os.remove("/www/server/panel/vhost/nginx/phpmyadmin.conf")
            if os.path.exists("/www/server/panel/vhost/apache/phpmyadmin.conf"):
                os.remove("/www/server/panel/vhost/apache/phpmyadmin.conf")
            public.serviceReload()
            return public.return_msg_gettext(True, public.lang("Setup successfully!"))
        public.serviceReload()
        return public.return_msg_gettext(True, public.lang("Open successfully, please manually release phpmyadmin ssl port"))


    #设置PHPMyAdmin
    def setPHPMyAdmin(self,get):
        import re
        #try:
        filename = self.__get_webserver_conffile()
        if public.get_webserver() == 'openlitespeed':
            filename = "/www/server/panel/vhost/openlitespeed/detail/phpmyadmin.conf"
        conf = public.readFile(filename)
        if not conf: return public.return_msg_gettext(False, public.lang("Operation failed"))
        if hasattr(get,'port'):
            mainPort = public.readFile('data/port.pl').strip()
            rulePort = ['80','443','21','20','8080','8081','8089','11211','6379']
            oldPort = "888"
            if get.port in rulePort:
                return public.return_msg_gettext(False, public.lang("Please do NOT use the usual port as the phpMyAdmin port!"))
            if public.get_webserver() == 'nginx':
                rep = r"listen\s+([0-9]+)\s*;"
                oldPort = re.search(rep,conf).groups()[0]
                conf = re.sub(rep,'listen ' + get.port + ';\n',conf)
            elif public.get_webserver() == 'apache':
                rep = r"Listen\s+([0-9]+)\s*\n"
                oldPort = re.search(rep,conf).groups()[0]
                conf = re.sub(rep,"Listen " + get.port + "\n",conf,1)
                rep = r"VirtualHost\s+\*:[0-9]+"
                conf = re.sub(rep,"VirtualHost *:" + get.port,conf,1)
            else:
                filename = '/www/server/panel/vhost/openlitespeed/listen/888.conf'
                conf = public.readFile(filename)
                reg = r"address\s+\*:(\d+)"
                tmp = re.search(reg,conf)
                if tmp:
                    oldPort = tmp.groups(1)

                    ## 修复 openlitespeed 修改端口报错
                    oldPort = oldPort[0]

                conf = re.sub(reg,"address *:{}".format(get.port),conf)
            if oldPort == get.port: return public.return_msg_gettext(False,'Port [{}] is in use!',(get.port,))
            
            public.writeFile(filename,conf)
            import firewalls
            get.ps = public.lang("New phpMyAdmin Port")
            fw = firewalls.firewalls()
            fw.AddAcceptPort(get)
            public.serviceReload()
            public.write_log_gettext('Software manager','Modified access port to {} for phpMyAdmin!',(get.port,))
            get.id = public.M('firewall').where('port=?',(oldPort,)).getField('id')
            get.port = oldPort
            fw.DelAcceptPort(get)
            return public.returnMsg(True, public.lang("Setup successfully!"))
        
        if hasattr(get,'phpversion'):
            if public.get_webserver() == 'nginx':
                filename = public.GetConfigValue('setup_path') + '/nginx/conf/enable-php.conf'
                conf = public.readFile(filename)
                rep = r"(unix:/tmp/php-cgi.*\.sock|127.0.0.1:\d+)"
                conf = re.sub(rep,public.get_php_proxy(get.phpversion,'nginx'),conf,1)
            elif public.get_webserver() == 'apache':
                rep = r"(unix:/tmp/php-cgi.*\.sock\|fcgi://localhost|fcgi://127.0.0.1:\d+)"
                conf = re.sub(rep,public.get_php_proxy(get.phpversion,'apache'),conf,1)
            else:
                reg = r'/usr/local/lsws/lsphp\d+/bin/lsphp'
                conf = re.sub(reg,'/usr/local/lsws/lsphp{}/bin/lsphp'.format(get.phpversion),conf)
            public.writeFile(filename,conf)
            public.serviceReload()
            public.write_log_gettext('Software manager','Modified PHP runtime version to PHP-{} for phpMyAdmin!',(get.phpversion,))
            return public.return_msg_gettext(True, public.lang("Setup successfully!"))
        
        if hasattr(get,'password'):
            import panelSite
            if(get.password == 'close'):
                return panelSite.panelSite().CloseHasPwd(get)
            else:
                return panelSite.panelSite().SetHasPwd(get)
        
        if hasattr(get,'status'):
            pma_path = public.GetConfigValue('setup_path') + '/phpmyadmin'
            stop_path = public.GetConfigValue('setup_path') + '/stop'


            webserver = public.get_webserver()
            if conf.find(stop_path) != -1:
                conf = conf.replace(stop_path,pma_path)
                msg = public.getMsg('START')

            if webserver == 'nginx':
                sub_string = '''{};
        allow 127.0.0.1;
        allow ::1;
        deny all'''.format(pma_path)
                if conf.find(sub_string) != -1:
                    conf = conf.replace(sub_string,pma_path)
                    msg = public.getMsg('START')
                else:
                    conf = conf.replace(pma_path,sub_string)
                    msg = public.getMsg('STOP')
            elif webserver == 'apache':
                src_string = 'AllowOverride All'
                sub_string = '''{}
        Deny from all
        Allow from 127.0.0.1 ::1 localhost'''.format(src_string,pma_path)
                if conf.find(sub_string) != -1:
                    conf = conf.replace(sub_string,src_string)
                    msg = public.getMsg('START')
                else:
                    conf = conf.replace(src_string,sub_string)
                    msg = public.getMsg('STOP')
            else:
                if conf.find(stop_path) != -1:
                    conf = conf.replace(stop_path,pma_path)
                    msg = public.getMsg('START')
                else:
                    conf = conf.replace(pma_path,stop_path)
                    msg = public.getMsg('STOP')
            
            public.writeFile(filename,conf)
            public.serviceReload()
            public.write_log_gettext('Software manager','phpMyAdmin already {}!',(msg,))
            return public.return_msg_gettext(True,'phpMyAdmin already {}!',(msg,))
        #except:
            #return public.returnMsg(False, public.lang("ERROR"));

    def ToPunycode(self,get):
        import re
        get.domain = get.domain.encode('utf8')
        tmp = get.domain.split('.')
        newdomain = ''
        for dkey in tmp:
                #匹配非ascii字符
                match = re.search(u"[\x80-\xff]+",dkey)
                if not match:
                        newdomain += dkey + '.'
                else:
                        newdomain += 'xn--' + dkey.decode('utf-8').encode('punycode') + '.'

        return newdomain[0:-1]
    
    #保存PHP排序
    def phpSort(self,get):
        if public.writeFile('/www/server/php/sort.pl',get.ssort): return public.return_msg_gettext(True, public.lang("Setup successfully!"))
        return public.return_msg_gettext(False, public.lang("Operation failed"))
    
    #获取广告代码
    def GetAd(self,get):
        try:
            return public.HttpGet(public.GetConfigValue('home') + '/Api/GetAD?name='+get.name + '&soc=' + get.soc)
        except:
            return ''
        
    #获取进度
    def GetSpeed(self,get):
        return public.getSpeed()
    
    #检查登陆状态
    def CheckLogin(self,get):
        return True
    
    #获取警告标识
    def GetWarning(self,get):
        warningFile = 'data/warning.json'
        if not os.path.exists(warningFile): return public.return_msg_gettext(False, public.lang("Warning list does NOT exist!"))
        import json,time;
        wlist = json.loads(public.readFile(warningFile))
        wlist['time'] = int(time.time())
        return wlist
    
    #设置警告标识
    def SetWarning(self,get):
        wlist = self.GetWarning(get)
        id = int(get.id)
        import time,json;
        for i in xrange(len(wlist['data'])):
            if wlist['data'][i]['id'] == id:
                wlist['data'][i]['ignore_count'] += 1
                wlist['data'][i]['ignore_time'] = int(time.time())
        
        warningFile = 'data/warning.json'
        public.writeFile(warningFile,json.dumps(wlist))
        return public.return_msg_gettext(True, public.lang("Setup successfully!"))
    
    #获取memcached状态
    def GetMemcachedStatus(self,get):
        import telnetlib,re;
        conf = public.readFile('/etc/init.d/memcached')
        result = {}
        result['bind'] = re.search('IP=(.+)',conf).groups()[0]
        result['port'] = int(re.search(r'PORT=(\d+)',conf).groups()[0])
        result['maxconn'] = int(re.search(r'MAXCONN=(\d+)',conf).groups()[0])
        result['cachesize'] = int(re.search(r'CACHESIZE=(\d+)',conf).groups()[0])
        tn = telnetlib.Telnet(result['bind'],result['port'])
        tn.write(b"stats\n")
        tn.write(b"quit\n")
        data = tn.read_all()
        if type(data) == bytes: data = data.decode('utf-8')
        data = data.replace('STAT','').replace('END','').split("\n")
        res = ['cmd_get','get_hits','get_misses','limit_maxbytes','curr_items','bytes','evictions','limit_maxbytes','bytes_written','bytes_read','curr_connections'];
        for d in data:
            if len(d)<3: continue
            t = d.split()
            if not t[0] in res: continue
            result[t[0]] = int(t[1])
        result['hit'] = 1
        if result['get_hits'] > 0 and result['cmd_get'] > 0:
            result['hit'] = float(result['get_hits']) / float(result['cmd_get']) * 100

        return result
    
    #设置memcached缓存大小
    def SetMemcachedCache(self,get):
        import re
        confFile = '/etc/init.d/memcached'
        conf = public.readFile(confFile)
        conf = re.sub('IP=.+','IP='+get.ip,conf)
        conf = re.sub(r'PORT=\d+','PORT='+get.port,conf)
        conf = re.sub(r'MAXCONN=\d+','MAXCONN='+get.maxconn,conf)
        conf = re.sub(r'CACHESIZE=\d+','CACHESIZE='+get.cachesize,conf)
        public.writeFile(confFile,conf)
        public.ExecShell(confFile + ' reload')
        return public.return_msg_gettext(True, public.lang("Setup successfully!"))
    
    #取redis状态
    def GetRedisStatus(self,get):
        import re
        c = public.readFile('/www/server/redis/redis.conf')
        port = re.findall('\n\\s*port\\s+(\\d+)',c)[0]
        password = re.findall('\n\\s*requirepass\\s+(.+)',c)
        if password: 
            password = ' -a ' + password[0]
        else:
            password = ''
        data = public.ExecShell('/www/server/redis/src/redis-cli -p ' + port + password + ' info')[0];
        res = [
               'tcp_port',
               'uptime_in_days',    #已运行天数
               'connected_clients', #连接的客户端数量
               'used_memory',       #Redis已分配的内存总量
               'used_memory_rss',   #Redis占用的系统内存总量
               'used_memory_peak',  #Redis所用内存的高峰值
               'mem_fragmentation_ratio',   #内存碎片比率
               'total_connections_received',#运行以来连接过的客户端的总数量
               'total_commands_processed',  #运行以来执行过的命令的总数量
               'instantaneous_ops_per_sec', #服务器每秒钟执行的命令数量
               'keyspace_hits',             #查找数据库键成功的次数
               'keyspace_misses',           #查找数据库键失败的次数
               'latest_fork_usec'           #最近一次 fork() 操作耗费的毫秒数
               ]
        data = data.split("\n")
        result = {}
        for d in data:
            if len(d)<3: continue
            t = d.strip().split(':')
            if not t[0] in res: continue
            result[t[0]] = t[1]
        return result
    
    #取PHP-FPM日志
    def GetFpmLogs(self,get):
        import re
        fpm_path = '/www/server/php/' + get.version + '/etc/php-fpm.conf'
        if not os.path.exists(fpm_path): return public.return_msg_gettext(False, public.lang("Log file does NOT exist!"))
        fpm_conf = public.readFile(fpm_path)
        log_tmp = re.findall(r"error_log\s*=\s*(.+)",fpm_conf)
        if not log_tmp: return public.return_msg_gettext(False, public.lang("Log file does NOT exist!"))
        log_file = log_tmp[0].strip()
        if log_file.find('var/log') == 0:
            log_file = '/www/server/php/' +get.version + '/'+ log_file
        return public.returnMsg(True,public.GetNumLines(log_file,1000))
    
    #取PHP慢日志
    def GetFpmSlowLogs(self,get):
        import re
        fpm_path = '/www/server/php/' + get.version + '/etc/php-fpm.conf'
        if not os.path.exists(fpm_path): return public.return_msg_gettext(False, public.lang("Log file does NOT exist!"))
        fpm_conf = public.readFile(fpm_path)
        log_tmp = re.findall(r"slowlog\s*=\s*(.+)",fpm_conf)
        if not log_tmp: return public.return_msg_gettext(False, public.lang("Log file does NOT exist!"))
        log_file = log_tmp[0].strip()
        if log_file.find('var/log') == 0:
            log_file = '/www/server/php/' +get.version + '/'+ log_file
        return public.returnMsg(True,public.GetNumLines(log_file,1000))
    
    #取指定日志
    def GetOpeLogs(self,get):
        if not os.path.exists(get.path): return public.return_msg_gettext(False, public.lang("Log file does NOT exist!"))
        return public.returnMsg(True,public.xsssec(public.GetNumLines(get.path,1000)))

    # 获取授权信息
    def get_pd(self, get):
        return public.get_pd(get)

    #检查用户绑定是否正确
    def check_user_auth(self,get):
        # import requests
        m_key = 'check_user_auth'
        if m_key in session: return session[m_key]
        u_path = 'data/userInfo.json'
        try:
            userInfo = json.loads(public.ReadFile(u_path))
        except: 
            if os.path.exists(u_path): os.remove(u_path)
            return public.return_msg_gettext(False, public.lang("Account binding has expired, please re-bind on the [Settings] page!"))
        url_headers = {"authorization":"bt {}".format(userInfo['token'])}
        # resp = requests.post('{}/api/user/verifyToken'.format(self.__official_url),headers=url_headers,verify=False)
        resp = public.HttpPost.post('{}/api/user/verifyToken'.format(self.__official_url), headers=url_headers, verify=False)
        resp = resp.json()
        if not resp['success']:
            if os.path.exists(u_path): os.remove(u_path)
            return public.return_msg_gettext(False, public.lang("Account binding has expired, please re-bind on the [Settings] page!"))
        else:
            session[m_key] = public.return_msg_gettext(True,'Binding is valid!')
            return session[m_key]


    #PHP探针
    def php_info(self,args):
        php_version = args.php_version.replace('.','')
        php_path = '/www/server/php/'
        if public.get_webserver() == 'openlitespeed':
            php_path = '/usr/local/lsws/lsphp'
        php_bin = php_path + php_version + '/bin/php'
        php_ini = php_path + php_version + '/etc/php.ini'
        if not os.path.exists('/etc/redhat-release') and public.get_webserver() == 'openlitespeed':
            php_ini = php_path + php_version + '/etc/php/'+args.php_version+'/litespeed/php.ini'
        tmp = public.ExecShell(php_bin + ' -c {} /www/server/panel/class/php_info.php'.format(php_ini))[0]
        if tmp.find('Warning: JIT is incompatible') != -1:
            tmp = tmp.strip().split('\n')[-1]

        try:
            result = json.loads(tmp)
            result['phpinfo'] = {}
            if "modules" not in result:
                result['modules'] = []
            if 'php_version' in result:
                result['phpinfo']['php_version'] = result['php_version']
        except Exception:
            result = {
                'php_version': php_version,
                'phpinfo': {},
                'modules': [],
                'ini': ''
            }
        # result = json.loads(tmp)

        result['phpinfo'] = {}
        result['phpinfo']['php_version'] = result['php_version']
        result['phpinfo']['php_path'] = php_path
        result['phpinfo']['php_bin'] = php_bin
        result['phpinfo']['php_ini'] = php_ini
        result['phpinfo']['modules'] = ' '.join(result['modules'])
        result['phpinfo']['ini'] = result['ini']
        result['phpinfo']['keys'] = { "1cache": "Buffer", "2crypt": "Encryption and decryption library", "0db": "Database-driven", "4network": "Network Communication Library", "5io_string": "File and string processing libraries", "3photo":"Image processing library","6other":"Other third-party libraries"}
        del(result['php_version'])
        del(result['modules'])
        del(result['ini'])
        return result

    #取指定行
    def get_lines(self,args):
        if not os.path.exists(args.filename): return public.returnMsg(False, public.lang("Logs emptied"))
        num = args.get('num/d',10)
        s_body = public.GetNumLines(args.filename,num)
        return public.returnMsg(True,s_body)

    def log_analysis(self,get):
        public.set_module_logs('log_analysis', 'log_analysis', 1)
        import log_analysis
        log_analysis=log_analysis.log_analysis()
        return log_analysis.log_analysis(get)


    def speed_log(self,get):
        import log_analysis
        log_analysis=log_analysis.log_analysis()
        return log_analysis.speed_log(get)



    def get_result(self,get):
        import log_analysis
        log_analysis=log_analysis.log_analysis()
        return log_analysis.get_result(get)

    def get_detailed(self,get):
        import log_analysis
        log_analysis=log_analysis.log_analysis()
        return log_analysis.get_detailed(get)

    def download_pay_type(self, path):
        public.downloadFile(public.get_url() + '/install/lib/pay_type_en.json', path)
        return True

    def get_pay_type(self, get):
        """
            @name 获取推荐列表
        """
        # spath = '{}/data/pay_type.json'.format(public.get_panel_path())
        # if not os.path.exists(spath):
        #     public.run_thread(self.download_pay_type,(spath,))
        # try:
        #     data = json.loads(public.readFile("data/pay_type.json"))
        # except:
        #     public.run_thread(self.download_pay_type, (spath,))
        #     data = {}
        #
        # import panelPlugin
        # plu_panel = panelPlugin.panelPlugin()
        # plugin_list = plu_panel.get_cloud_list()
        # if not 'pro' in plugin_list: plugin_list['pro'] = -1
        #
        # for item in data:
        #     if 'list' in item:
        #         item['list'] = self.__get_home_list(item['list'], item['type'], plugin_list, plu_panel)
        #         if item['type'] == 1:
        #             if len(item['list']) > 4: item['list'] = item['list'][:4]
        #     # if item['type'] == 0 and plugin_list['pro'] >= 0:
        #     #     item['show'] = False
        #
        # return data

        spath = '{}/data/pay_type.json'.format(public.get_panel_path())
        if os.path.exists(spath) and os.path.getsize(spath) <= 0:
            os.remove(spath)

        if not os.path.exists(spath):
            public.run_thread(self.download_pay_type, (spath,))
        try:
            data = json.loads(public.readFile("data/pay_type.json"))
        except json.decoder.JSONDecodeError:
            os.remove(spath)
            public.run_thread(self.download_pay_type, (spath,))
            data = json.loads(public.readFile("data/pay_type.json"))
        except Exception:
            data = self.get_default_pay_type()

        import panelPlugin
        plu_panel = panelPlugin.panelPlugin()
        plugin_list = plu_panel.get_cloud_list()
        if not 'pro' in plugin_list: plugin_list['pro'] = -1

        for item in data:
            if 'list' in item:
                item['list'] = self.__get_home_list(item['list'], item['type'],plugin_list, plu_panel)
                if item['type'] == 1:
                    if len(item['list']) > 4: item['list'] = item['list'][:4]
            # if item['type'] == 0 and plugin_list['pro'] >= 0:
            #     item['show'] = False
        return data


    @staticmethod
    def get_default_pay_type():
        spath = '{}/data/default_pay_type.json'.format(public.get_panel_path())
        default = [{"type": -1}, {"type": -1}, {"type": -1}, {"type": -1},
                   {"type": -1}, {
            "type": 5,
            "describe": "网站-设置推荐",
            "show": True,
            "list": [
                {
                    "title": "防火墙",
                    "name": "btwaf",
                    "pay": "46",
                    "pluginName": "Nginx网站防火墙",
                    "ps": "有效拦截SQL 注入、XSS跨站、恶意代码、网站挂马等常见攻击，过滤恶意访问，降低数据泄露的风险，保障网站的可用性。",
                    "preview": "https://www.bt.cn/new/product_nginx_firewall.html",
                    "dependent": "nginx",
                    "pluginType": "pro",
                    "eventList": [
                        {
                            "event": "site_waf_config('$siteName')",
                            "version": "5.2.0"
                        }
                    ]
                },
                {
                    "title": "防火墙",
                    "name": "btwaf_httpd",
                    "pay": "46",
                    "pluginName": "网站防火墙",
                    "ps": "有效拦截SQL 注入、XSS跨站、恶意代码、网站挂马等常见攻击，过滤恶意访问，降低数据泄露的风险，保障网站的可用性。",
                    "preview": "https://www.bt.cn/new/product_nginx_firewall.html",
                    "dependent": "apache",
                    "pluginType": "pro",
                    "eventList": [
                        {
                            "event": "site_waf_config('$siteName')",
                            "version": "5.2.0"
                        }
                    ]
                },
                {
                    "title": "统计",
                    "name": "total",
                    "pay": "47",
                    "pluginName": "网站监控报表",
                    "ps": "快速分析网站运行状况，实时精确统计网站流量、ip、uv、pv、请求、蜘蛛等数据，网站SEO优化利器",
                    "preview": "https://www.bt.cn/new/product_website_total.html",
                    "dependent": "apache",
                    "pluginType": "pro",
                    "eventList": [
                        {
                            "event": "WebsiteReport('$siteName')",
                            "version": "5.0"
                        }
                    ]
                },
                {
                    "title": "统计",
                    "name": "total",
                    "pay": "47",
                    "pluginName": "网站监控报表",
                    "ps": "快速分析网站运行状况，实时精确统计网站流量、ip、uv、pv、请求、蜘蛛等数据，网站SEO优化利器",
                    "preview": "https://www.bt.cn/new/product_website_total.html",
                    "dependent": "nginx",
                    "pluginType": "pro",
                    "eventList": [
                        {
                            "event": "WebsiteReport('$siteName')",
                            "version": "5.0"
                        }
                    ]
                }
            ]
        }, {"type": -1}, {"type": -1}]
        if os.path.isfile(spath):
            try:
                res_data = json.loads(public.readFile(spath))
                if isinstance(res_data, list):
                    return res_data
            except json.JSONDecodeError:
                pass
            # 再次出错时，保障网站列表可以展示
            return default
        return default




    def __get_home_list(self, sList, stype, plugin_list, plu_panel):
        """
            @name 获取首页软件列表推荐
        """
        nList = []
        webserver = public.get_webserver()
        for x in sList:
            for plugin_info in plugin_list['list']:
                if x['name'] == plugin_info['name']:
                    if not 'endtime' in plugin_info or plugin_info['endtime'] >= 0:
                        x['isBuy'] = True
            is_check = False
            if 'dependent' in x:
                if x['dependent'] == webserver: is_check = True
            else:
                is_check = True
            if is_check:
                info = plu_panel.get_soft_find(x['name'])
                if info:
                    if stype == 1:
                        # if plugin_list['pro'] >= 0: continue
                        if not info['setup']:
                            x['install'] = info['setup']
                            nList.append(x)
                    else:
                        x['install'] = info['setup']
                        nList.append(x)
        return nList

    def ignore_version(self, get):
        """
        @忽略版本更新
        :param version 忽略的版本号
        """
        version = get.version
        path = '{}/data/no_update.pl'.format(public.get_panel_path())
        try:
            data = json.loads(public.readFile(path))
        except:
            data = []

        if not version in data: data.append(version)

        public.writeFile(path, json.dumps(data))
        try:
            del (session['updateInfo'])
        except:
            pass

        return public.return_msg_gettext(True, public.lang("Ignore success, this version will no longer be reminded to update."))