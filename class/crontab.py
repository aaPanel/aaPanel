#coding: utf-8
# +-------------------------------------------------------------------
# | aaPanel
# +-------------------------------------------------------------------
# | Copyright (c) 2015-2099 aaPanel(www.aapanel.com) All rights reserved.
# +-------------------------------------------------------------------
# | Author: hwliang <hwl@aapanel.com>
# +-------------------------------------------------------------------
import public,db,os,time,re, json

class crontab:
    field = 'id,name,type,where1,where_hour,where_minute,echo,addtime,status,save,backupTo,sName,sBody,sType,urladdress'
    field += ",save_local,notice,notice_channel"
    #取计划任务列表
    def GetCrontab(self,get):
        self.checkBackup()
        self.__clean_log()
        cront = public.M('crontab').order("id desc").field(self.field).select()
        if type(cront) == str:
            public.M('crontab').execute("ALTER TABLE 'crontab' ADD 'status' INTEGER DEFAULT 1",())
            public.M('crontab').execute("ALTER TABLE 'crontab' ADD 'save' INTEGER DEFAULT 3",())
            public.M('crontab').execute("ALTER TABLE 'crontab' ADD 'backupTo' TEXT DEFAULT off",())
            public.M('crontab').execute("ALTER TABLE 'crontab' ADD 'sName' TEXT",())
            public.M('crontab').execute("ALTER TABLE 'crontab' ADD 'sBody' TEXT",())
            public.M('crontab').execute("ALTER TABLE 'crontab' ADD 'sType' TEXT",())
            public.M('crontab').execute("ALTER TABLE 'crontab' ADD 'urladdress' TEXT",())
            public.M('crontab').execute("ALTER TABLE 'crontab' ADD 'save_local' INTEGER DEFAULT 0",())
            public.M('crontab').execute("ALTER TABLE 'crontab' ADD 'notice' INTEGER DEFAULT 0",())
            public.M('crontab').execute("ALTER TABLE 'crontab' ADD 'notice_channel' TEXT DEFAULT ''",())
            cront = public.M('crontab').order("id desc").field(self.field).select()
        data=[]
        for i in range(len(cront)):
            tmp = {}
            tmp=cront[i]
            if cront[i]['type']=="day":
                tmp['type']=public.lang("Per Day")
                tmp['cycle']= public.lang('Per Day, run at {} Hour {} Min',str(cront[i]['where_hour']),str(cront[i]['where_minute']))
            elif cront[i]['type']=="day-n":
                tmp['type']=public.lang('Every {} Days',str(cront[i]['where1']))
                tmp['cycle']=public.lang('Every {} Days, run at {} Hour {} Min',str(cront[i]['where1']),str(cront[i]['where_hour']),str(cront[i]['where_minute']))
            elif cront[i]['type']=="hour":
                tmp['type']=public.lang("Per Hour")
                tmp['cycle']=public.lang('Per Hour, run at {} Min',str(cront[i]['where_minute']))
            elif cront[i]['type']=="hour-n":
                tmp['type']=public.lang('Every {} Hours',str(cront[i]['where1']))
                tmp['cycle']=public.lang('Every {} Hours, run at {} Min',str(cront[i]['where1']),str(cront[i]['where_minute']))
            elif cront[i]['type']=="minute-n":
                tmp['type']=public.lang('Every {} Minutes',str(cront[i]['where1']))
                tmp['cycle']=public.lang('Run Every {} Minutes',str(cront[i]['where1']))
            elif cront[i]['type']=="week":
                tmp['type']=public.lang("Weekly")
                if not cront[i]['where1']: cront[i]['where1'] = '0'
                tmp['cycle']= public.lang('Every {}, run at {} Hour {} Min',self.toWeek(int(cront[i]['where1'])),str(cront[i]['where_hour']),str(cront[i]['where_minute']))
            elif cront[i]['type']=="month":
                tmp['type']=public.lang("Monthly")
                tmp['cycle']=public.lang('Monthly, run on {}Day {} Hour {}Min',str(cront[i]['where1']),str(cront[i]['where_hour']),str(cront[i]['where_minute']))

            log_file = '/www/server/cron/{}.log'.format(tmp['echo'])
            if os.path.exists(log_file):
                tmp['addtime'] = self.get_last_exec_time(log_file)
            data.append(tmp)
        return data

    def get_backup_list(self, args):
        '''
            @name 获取指定备份任务的备份文件列表
            @author hwliang
            @param args<dict> 参数{
                cron_id<int> 任务ID 必填
                p<int> 页码 默认1
                rows<int> 每页显示条数 默认10
                callback<string> jsonp回调函数  默认为空
            }
            @return <dict>{
                page<str> 分页HTML
                data<list> 数据列表
            }
        '''

        p = args.get('p/d', 1)
        rows = args.get('rows/d', 10)
        tojs = args.get('tojs/s', '')
        callback = args.get('callback/s', '') if tojs else tojs

        cron_id = args.get('cron_id/d')
        count = public.M('backup').where('cron_id=?', (cron_id,)).count()
        data = public.get_page(count, p, rows, callback)
        data['data'] = public.M('backup').where('cron_id=?', (cron_id,)).limit(data['row'], data['shift']).select()
        return data

    def get_last_exec_time(self,log_file):
        '''
            @name 获取上次执行时间
            @author hwliang
            @param log_file<string> 日志文件路径
            @return format_date
        '''
        exec_date = ''
        try:
            log_body = public.GetNumLines(log_file,20)
            if log_body:
                log_arr = log_body.split('\n')
                date_list = []
                for i in log_arr:
                    if i.find('★') != -1 and i.find('[') != -1 and i.find(']') != -1:
                        date_list.append(i)
                if date_list:
                    exec_date = date_list[-1].split(']')[0].split('[')[1]
        except:
            pass

        finally:
            if not exec_date:
                exec_date = public.format_date(times=int(os.path.getmtime(log_file)))
        return exec_date


    #清理日志
    def __clean_log(self):
        try:
            log_file = '/www/server/cron'
            if not os.path.exists(log_file): return False
            for f in os.listdir(log_file):
                if f[-4:] != '.log': continue
                filename = log_file + '/' + f
                if os.path.getsize(filename) < 1048576 /2: continue
                tmp = public.GetNumLines(filename,100)
                public.writeFile(filename,tmp)
        except:
            pass


    #转换大写星期
    def toWeek(self,num):
        wheres={
                0   :   public.lang("Sunday"),
                1   :   public.lang("Monday"),
                2   :   public.lang("Tuesday"),
                3   :   public.lang("Wednesday"),
                4   :   public.lang("Thursday"),
                5   :   public.lang("Friday"),
                6   :   public.lang("Saturday")
                }
        try:
            return wheres[num]
        except:
            return ''
    
    #检查环境
    def checkBackup(self):
        from BTPanel import cache
        if cache.get('check_backup'): return None

        # 检查备份表是否正确
        if not public.M('sqlite_master').where('type=? AND name=? AND sql LIKE ?', ('table', 'backup','%cron_id%')).count():
            public.M('backup').execute("ALTER TABLE 'backup' ADD 'cron_id' INTEGER DEFAULT 0",())

        #检查备份脚本是否存在
        filePath=public.GetConfigValue('setup_path')+'/panel/script/backup'
        if not os.path.exists(filePath):
            public.downloadFile(public.GetConfigValue('home') + '/linux/backup.sh',filePath)
        #检查日志切割脚本是否存在
        filePath=public.GetConfigValue('setup_path')+'/panel/script/logsBackup'
        if not os.path.exists(filePath):
            public.downloadFile(public.GetConfigValue('home') + '/linux/logsBackup.py',filePath)
        #检查计划任务服务状态
        import system
        sm = system.system()
        if os.path.exists('/etc/init.d/crond'): 
            if not public.process_exists('crond'): public.ExecShell('/etc/init.d/crond start')
        elif os.path.exists('/etc/init.d/cron'):
            if not public.process_exists('cron'): public.ExecShell('/etc/init.d/cron start')
        elif os.path.exists('/usr/lib/systemd/system/crond.service'):
            if not public.process_exists('crond'): public.ExecShell('systemctl start crond')
        cache.set('check_backup',True,3600)
    

    #设置计划任务状态
    def set_cron_status(self,get):
        id = get['id']
        cronInfo = public.M('crontab').where('id=?',(id,)).field(self.field).find()
        status_msg = ['Stop','Start']
        status = 1
        if cronInfo['status'] == status:
            status = 0
            self.remove_for_crond(cronInfo['echo'])
        else:
            cronInfo['status'] = 1
            if not self.sync_to_crond(cronInfo):
                return public.return_msg_gettext(False,  public.lang("Unable to write to file, please check if [System hardening] is enabled!"))
        
        public.M('crontab').where('id=?',(id,)).setField('status',status)
        public.WriteLog(
            'TYPE_CRON',
            "Modified cron job [{}] status to [{}]".format(cronInfo['name'], str(status_msg[status]))
        )
        return public.return_msg_gettext(True, public.lang("Setup successfully!"))

    #修改计划任务
    def modify_crond(self,get):
        if len(get['name'])<1:
             return public.return_msg_gettext(False, public.lang("Name of task cannot be empty!"))
        id = get['id']
        cuonConfig,get,name = self.GetCrondCycle(get)
        cronInfo = public.M('crontab').where('id=?',(id,)).field(self.field).find()
        if not get['where1']: get['where1'] = get['week']
        del(cronInfo['id'])
        del(cronInfo['addtime'])
        cronInfo['name'] = get['name']
        cronInfo['type'] = get['type']
        cronInfo['where1'] = get['where1']
        cronInfo['where_hour'] = get['hour']
        cronInfo['where_minute'] = get['minute']
        cronInfo['save'] = get['save']
        cronInfo['backupTo'] = get['backupTo']
        cronInfo['sBody'] = get['sBody']
        cronInfo['urladdress'] = get['urladdress']
        columns = 'name,type,where1,where_hour,where_minute,save,backupTo,sBody,urladdress'
        values = (get['name'],get['type'],get['where1'],get['hour'],
                  get['minute'],get['save'],get['backupTo'],get['sBody']
                  ,get['urladdress'])
        if 'save_local' in get:
            columns += ",save_local, notice, notice_channel"
            values = (get['name'],get['type'],get['where1'],get['hour'],
                      get['minute'],get['save'],get['backupTo'],get['sBody'],
                      get['urladdress'],get['save_local'],get["notice"],
                      get["notice_channel"])
        self.remove_for_crond(cronInfo['echo'])
        if cronInfo['status'] == 0: return public.return_msg_gettext(False, public.lang("The current task is Disable status, please open the task before modifying!"))
        if not self.sync_to_crond(cronInfo):
            return public.return_msg_gettext(False,  public.lang("Unable to write to file, please check if [System hardening] is enabled!"))
        public.M('crontab').where('id=?',(id,)).save(columns,values)

        public.WriteLog('TYPE_CRON',"MODIFY_CRON",(cronInfo['name'],))
        return public.return_msg_gettext(True, public.lang("Setup successfully!"))


    #获取指定任务数据
    def get_crond_find(self,get):
        id = int(get.id)
        data = public.M('crontab').where('id=?',(id,)).field(self.field).find()
        return data

    #同步到crond
    def sync_to_crond(self,cronInfo):
        if not 'status' in cronInfo: return False
        if 'where_hour' in cronInfo:
            cronInfo['hour'] = cronInfo['where_hour']
            cronInfo['minute'] = cronInfo['where_minute']
            cronInfo['week'] = cronInfo['where1']
        cuonConfig,cronInfo,name = self.GetCrondCycle(cronInfo)
        cronPath=public.GetConfigValue('setup_path')+'/cron'
        cronName=self.GetShell(cronInfo)
        if type(cronName) == dict: return cronName
        #if cronInfo['status'] == 0: return False
        cuonConfig += ' ' + cronPath+'/'+cronName+' >> '+ cronPath+'/'+cronName+'.log 2>&1'
        wRes = self.WriteShell(cuonConfig)
        if type(wRes) != bool: return False
        self.CrondReload()
        return True

    #添加计划任务
    def AddCrontab(self,get):
        if len(get['name'])<1:
             return public.return_msg_gettext(False, public.lang("Name of task cannot be empty!"))
        cuonConfig,get,name = self.GetCrondCycle(get)
        cronPath=public.GetConfigValue('setup_path')+'/cron'
        cronName=self.GetShell(get)
        if type(cronName) == dict: return cronName
        cuonConfig += ' ' + cronPath+'/'+cronName+' >> '+ cronPath+'/'+cronName+'.log 2>&1'

        wRes = self.WriteShell(cuonConfig)
        if type(wRes) != bool: return wRes
        self.CrondReload()
        columns = 'name,type,where1,where_hour,where_minute,echo,addtime,\
                  status,save,backupTo,sType,sName,sBody,urladdress'
        values = (public.xssencode2(get['name']),get['type'],get['where1'],get['hour'],
        get['minute'],cronName,time.strftime('%Y-%m-%d %X',time.localtime()),
        1,get['save'],get['backupTo'],get['sType'],get['sName'],get['sBody'],
        get['urladdress'])
        if "save_local" in get:
            columns += ",save_local,notice,notice_channel"
            values = (public.xssencode2(get['name']),get['type'],get['where1'],get['hour'],
        get['minute'],cronName,time.strftime('%Y-%m-%d %X',time.localtime()),
        1,get['save'],get['backupTo'],get['sType'],get['sName'],get['sBody'],
        get['urladdress'], get["save_local"], get['notice'], get['notice_channel'])
        addData=public.M('crontab').add(columns,values)
        public.add_security_logs('TYPE_CRON','Add Cron tasks ['+get['name']+'] success'+str(values))
        if type(addData) == str:
            return public.return_msg_gettext(False, addData)
        public.WriteLog('TYPE_CRON', 'Add Cron tasks [' + get['name'] + '] success')
        if addData>0:
            result = public.return_msg_gettext(True,'Setup successfully!')
            result['id'] = addData
            return result
        return public.return_msg_gettext(False, public.lang("Failed to add"))
    
    #构造周期
    def GetCrondCycle(self,params):
        cuonConfig=""
        name = ""
        if params['type']=="day":
            cuonConfig = self.GetDay(params)
            name = public.lang("Per Day")
        elif params['type']=="day-n":
            cuonConfig = self.GetDay_N(params)
            name = public.get_msg_gettext('Every {0} Days',(params['where1'],))
        elif params['type']=="hour":
            cuonConfig = self.GetHour(params)
            name = public.lang("Per Hour")
        elif params['type']=="hour-n":
            cuonConfig = self.GetHour_N(params)
            name = public.lang("Per Hour")
        elif params['type']=="minute-n":
            cuonConfig = self.Minute_N(params)
        elif params['type']=="week":
            params['where1']=params['week']
            cuonConfig = self.Week(params)
        elif params['type']=="month":
            cuonConfig = self.Month(params)
        return cuonConfig,params,name

    #取任务构造Day
    def GetDay(self,param):
        cuonConfig ="{} {} * * * ".format(param['minute'],param['hour'])
        return cuonConfig
    #取任务构造Day_n
    def GetDay_N(self,param):
        cuonConfig ="{} {} */{} * * ".format(param['minute'],param['hour'],param['where1'])
        return cuonConfig
    
    #取任务构造Hour
    def GetHour(self,param):
        cuonConfig ="{} * * * * ".format(param['minute'])
        return cuonConfig
    
    #取任务构造Hour-N
    def GetHour_N(self,param):
        cuonConfig ="{} */{} * * * ".format(param['minute'],param['where1'])
        return cuonConfig
    
    #取任务构造Minute-N
    def Minute_N(self,param):
        cuonConfig ="*/{} * * * * ".format(param['where1'])
        return cuonConfig
    
    #取任务构造week
    def Week(self,param):
        cuonConfig ="{} {} * * {}".format(param['minute'],param['hour'],param['week'])
        return cuonConfig
    
    #取任务构造Month
    def Month(self,param):
        cuonConfig = "{} {} {} * * ".format(param['minute'],param['hour'],param['where1'])
        return cuonConfig
    
    #取数据列表
    def GetDataList(self,get):
        data = {}
        if get['type'] == 'databases':
            data['data'] = public.M(get['type']).where("type=?","MySQL").field('name,ps').select()
        else:
            data['data'] = public.M(get['type']).field('name,ps').select()
        for i in data['data']:
            if 'ps' in i:
                i['ps'] = public.xsssec(i['ps'])
        data['orderOpt'] = []
        import json
        tmp = public.readFile('data/libList.conf')
        if not tmp: return data
        libs = json.loads(tmp)
        for lib in libs:
            if not 'opt' in lib: continue
            filename = 'plugin/{}'.format(lib['opt'])
            if not os.path.exists(filename): continue
            tmp = {}
            tmp['name'] = lib['name']
            tmp['value']= lib['opt']
            data['orderOpt'].append(tmp)
        return data
    
    #取任务日志
    def GetLogs(self,get):
        id = get['id']
        echo = public.M('crontab').where("id=?",(id,)).field('echo').find()
        logFile = public.GetConfigValue('setup_path')+'/cron/'+echo['echo']+'.log'
        if not os.path.exists(logFile):return public.return_msg_gettext(False, public.lang("log is empty"))
        log = public.GetNumLines(logFile,2000)
        return public.return_msg_gettext(True, log)
    
    #清理任务日志
    def DelLogs(self,get):
        try:
            id = get['id']
            echo = public.M('crontab').where("id=?",(id,)).getField('echo')
            logFile = public.GetConfigValue('setup_path')+'/cron/'+echo+'.log'
            os.remove(logFile)
            return public.return_msg_gettext(True, public.lang("Logs emptied"))
        except:
            return public.return_msg_gettext(False, public.lang("Failed to empty task logs!"))
    
    #删除计划任务
    def DelCrontab(self,get):
        try:
            id = get['id']
            find = public.M('crontab').where("id=?",(id,)).field('name,echo').find()
            if not find: return public.return_msg_gettext(False, public.lang("The specified task does not exist!"))

            if not self.remove_for_crond(find['echo']): return public.return_msg_gettext(False,  public.lang("Unable to write to file, please check if [System hardening] is enabled!"))
            cronPath = public.GetConfigValue('setup_path') + '/cron'
            sfile = cronPath + '/' + find['echo']
            if os.path.exists(sfile): os.remove(sfile)
            sfile = cronPath + '/' + find['echo'] + '.log'
            if os.path.exists(sfile): os.remove(sfile)
            
            public.M('crontab').where("id=?",(id,)).delete()
            public.add_security_logs("Delete cron", "Delete cron:" + find['name'])
            public.WriteLog('TYPE_CRON', 'CRONTAB_DEL',(find['name'],))
            return public.return_msg_gettext(True, public.lang("Successfully deleted"))
        except:
            return public.return_msg_gettext(False, public.lang("Failed to delete"))

    #从crond删除
    def remove_for_crond(self,echo):
        file = self.get_cron_file()
        if not os.path.exists(file):
            return False
        conf=public.readFile(file)
        if not conf: return False
        if conf.find(str(echo)) == -1: return True
        rep = ".+" + str(echo) + ".+\n"
        conf = re.sub(rep, "", conf)
        try:
            if not public.writeFile(file,conf): return False
        except:
            return False
        self.CrondReload()
        return True
    
    #取执行脚本
    def GetShell(self,param):
        #try:
        type=param['sType']
        if not 'echo' in param:
            cronName=public.md5(public.md5(str(time.time()) + '_bt'))
        else:
            cronName = param['echo']
        if type=='toFile':
            shell=param.sFile
        else :
            head="#!/bin/bash\nPATH=/bin:/sbin:/usr/bin:/usr/sbin:/usr/local/bin:/usr/local/sbin:~/bin\nexport PATH\n"
            python_bin = "{} -u".format(public.get_python_bin())
            if public.get_webserver()=='nginx':
                log='.log'
            elif public.get_webserver()=='apache':
                log = '-access_log'
            else:
                log = '_ols.access_log'
            if type in ['site','path'] and param['sBody'] != 'undefined' and len(param['sBody']) > 1:
                exports = param['sBody'].replace("\r\n","\n").replace("\n",",")
                head += "BT_EXCLUDE=\"" + exports.strip() + "\"\nexport BT_EXCLUDE\n"
            attach_param = " " + cronName
            wheres={
                    'path': head + python_bin +" " + public.GetConfigValue('setup_path')+"/panel/script/backup.py path "+param['sName']+" "+str(param['save'])+attach_param,
                    'site'  :   head +python_bin+ " " + public.GetConfigValue('setup_path')+"/panel/script/backup.py site "+param['sName']+" "+str(param['save'])+attach_param,
                    'database': head +python_bin+ " " + public.GetConfigValue('setup_path')+"/panel/script/backup.py database "+param['sName']+" "+str(param['save'])+attach_param,
                    'logs'  :   head +python_bin+ " " + public.GetConfigValue('setup_path')+"/panel/script/logsBackup "+param['sName']+log+" "+str(param['save']),
                    'rememory' : head + "/bin/bash " + public.GetConfigValue('setup_path') + '/panel/script/rememory.sh',
                    'webshell': head +python_bin+ " " + public.GetConfigValue('setup_path') + '/panel/class/webshell_check.py site ' + param['sName'] +' ' +param['urladdress']
                    }
            if param['backupTo'] != 'localhost':
                cfile = public.GetConfigValue('setup_path') + "/panel/plugin/" + param['backupTo'] + "/" + param['backupTo'] + "_main.py"
                if not os.path.exists(cfile): cfile = public.GetConfigValue('setup_path') + "/panel/script/backup_" + param['backupTo'] + ".py"
                wheres={
                    'path': head + python_bin+" " + cfile + " path " + param['sName'] + " " + str(param['save'])+attach_param,
                    'site'  :   head + python_bin+" " + cfile + " site " + param['sName'] + " " + str(param['save'])+attach_param,
                    'database': head + python_bin+" " + cfile + " database " + param['sName'] + " " + str(param['save'])+attach_param,
                    'logs'  :   head + python_bin+" " + public.GetConfigValue('setup_path')+"/panel/script/logsBackup "+param['sName']+log+" "+str(param['save']),
                    'rememory' : head + "/bin/bash " + public.GetConfigValue('setup_path') + '/panel/script/rememory.sh',
                     'webshell': head + python_bin+" " + public.GetConfigValue('setup_path') + '/panel/class/webshell_check.py site ' + param['sName'] +' ' +param['urladdress']
                    }
                
            try:
                shell=wheres[type]
            except:
                if type == 'toUrl':
                    shell = head + "curl -sS --connect-timeout 10 -m 3600 '" + param['urladdress']+"'"
                else:
                    shell=head+param['sBody'].replace("\r\n","\n")
                    
                shell += '''
echo "----------------------------------------------------------------------------"
endDate=`date +"%Y-%m-%d %H:%M:%S"`
echo "★[$endDate] Successful"
echo "----------------------------------------------------------------------------"
'''
        cronPath=public.GetConfigValue('setup_path')+'/cron'
        if not os.path.exists(cronPath): public.ExecShell('mkdir -p ' + cronPath)
        file = cronPath+'/' + cronName
        public.writeFile(file,self.CheckScript(shell))
        public.ExecShell('chmod 750 ' + file)
        return cronName
        #except Exception as ex:
            #return public.return_msg_gettext(False, 'Failed to write in file!' + str(ex))
        
    #检查脚本
    def CheckScript(self,shell):
        keys = ['shutdown','init 0','mkfs','passwd','chpasswd','--stdin','mkfs.ext','mke2fs']
        for key in keys:
            shell = shell.replace(key,'[***]')
        return shell
    
    #重载配置
    def CrondReload(self):
        if os.path.exists('/etc/init.d/crond'): 
            public.ExecShell('/etc/init.d/crond reload')
        elif os.path.exists('/etc/init.d/cron'):
            public.ExecShell('service cron restart')
        else:
            public.ExecShell("systemctl reload crond")
        
    #将Shell脚本写到文件
    def WriteShell(self,config):
        u_file = '/var/spool/cron/crontabs/root'
        file = self.get_cron_file()
        if not os.path.exists(file): public.writeFile(file,'')
        conf = public.readFile(file)
        if type(conf)==bool:return public.return_msg_gettext(False, public.lang("Failed to read file!"))
        conf += config + "\n"
        if public.writeFile(file,conf):
            if not os.path.exists(u_file):
                public.ExecShell("chmod 600 '" + file + "' && chown root.root " + file)
            else:
                public.ExecShell("chmod 600 '" + file + "' && chown root.crontab " + file)
            return True
        return public.return_msg_gettext(False,  public.lang("Unable to write to file, please check if [System hardening] is enabled!"))
    
    #立即执行任务
    def StartTask(self,get):
        echo = public.M('crontab').where('id=?',(get.id,)).getField('echo')
        execstr = public.GetConfigValue('setup_path') + '/cron/' + echo
        public.ExecShell('chmod +x ' + execstr)
        public.ExecShell('nohup ' + execstr + ' >> ' + execstr + '.log 2>&1 &')
        return public.return_msg_gettext(True, public.lang("Task has been executed!"))

    #获取计划任务文件位置
    def get_cron_file(self):
        u_path = '/var/spool/cron/crontabs'
        u_file = u_path + '/root'
        c_file = '/var/spool/cron/root'
        cron_path = c_file
        if not os.path.exists(u_path):
            cron_path=c_file

        if os.path.exists("/usr/bin/apt-get"):
            cron_path = u_file
        elif os.path.exists('/usr/bin/yum'):
            cron_path = c_file

        if cron_path == u_file:
            if not os.path.exists(u_path):
                os.makedirs(u_path,472)
                public.ExecShell("chown root:crontab {}".format(u_path))
        if not os.path.exists(cron_path):
            public.writeFile(cron_path,"")
        return cron_path

    
        