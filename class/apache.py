#coding: utf-8
#-------------------------------------------------------------------
# 宝塔Linux面板
#-------------------------------------------------------------------
# Copyright (c) 2015-2018 宝塔软件(http:#bt.cn) All rights reserved.
#-------------------------------------------------------------------
# Author: hwliang <hwl@bt.cn>
#-------------------------------------------------------------------

#------------------------------
# Apache管理模块
#------------------------------
import public,os,re,shutil,math,psutil,time
os.chdir("/www/server/panel")

class apache:
    setupPath = '/www/server'
    apachedefaultfile = "%s/apache/conf/extra/httpd-default.conf" % (setupPath)
    apachempmfile = "%s/apache/conf/extra/httpd-mpm.conf" % (setupPath)

    def GetProcessCpuPercent(self,i,process_cpu):
        try:
            pp = psutil.Process(i)
            if pp.name() not in process_cpu.keys():
                process_cpu[pp.name()] = float(pp.cpu_percent(interval=0.1))
            process_cpu[pp.name()] += float(pp.cpu_percent(interval=0.1))
        except:
            pass

    def GetApacheStatus(self):
        process_cpu = {}
        apacheconf = "%s/apache/conf/httpd.conf" % (self.setupPath)
        confcontent = public.readFile(apacheconf)
        rep = "#Include conf/extra/httpd-info.conf"
        if re.search(rep,confcontent):
            confcontent = re.sub(rep,"Include conf/extra/httpd-info.conf",confcontent)
            public.writeFile(apacheconf,confcontent)
            public.serviceReload()
        result = public.HttpGet('http://127.0.0.1/server-status?auto')
        try:
            workermen = int(public.ExecShell("ps aux|grep httpd|grep 'start'|awk '{memsum+=$6};END {print memsum}'")[0]) / 1024
        except:
            return public.returnMsg(False,"Get worker RAM False")
        for proc in psutil.process_iter():
            if proc.name() == "httpd":
                self.GetProcessCpuPercent(proc.pid,process_cpu)
        time.sleep(0.5)

        data = {}

        # 计算启动时间
        Uptime = re.search("ServerUptimeSeconds:\s+(.*)",result)
        if not Uptime:
            return public.returnMsg(False, "Get worker Uptime False")
        Uptime = int(Uptime.group(1))
        min = Uptime / 60
        hours = min / 60
        days = math.floor(hours / 24)
        hours = math.floor(hours - (days * 24))
        min = math.floor(min - (days * 60 * 24) - (hours * 60))

        #格式化重启时间
        restarttime = re.search("RestartTime:\s+(.*)",result)
        if not restarttime:
            return public.returnMsg(False, "Get worker Restart Time False")
        restarttime = restarttime.group(1)
        rep = "\w+,\s([\w-]+)\s([\d\:]+)\s\w+"
        date = re.search(rep,restarttime)
        if not date:
            return public.returnMsg(False, "Get worker date False")
        date = date.group(1)
        timedetail = re.search(rep,restarttime)
        if not timedetail:
            return public.returnMsg(False, "Get worker time detail False")
        timedetail=timedetail.group(2)
        monthen = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"]
        n = 0
        for m in monthen:
            if m in date:
                date = re.sub(m,str(n+1),date)
            n+=1
        date = date.split("-")
        date = "%s-%s-%s" % (date[2],date[1],date[0])

        reqpersec = re.search("ReqPerSec:\s+(.*)", result)
        if not reqpersec:
            return public.returnMsg(False, "Get worker reqpersec False")
        reqpersec = reqpersec.group(1)
        if re.match("^\.", reqpersec):
            reqpersec = "%s%s" % (0,reqpersec)
        data["RestartTime"] = "%s %s" % (date,timedetail)
        data["UpTime"] = "%s day %s hour %s minute" % (str(int(days)),str(int(hours)),str(int(min)))
        total_acc = re.search("Total Accesses:\s+(\d+)",result)
        if not total_acc:
            return public.returnMsg(False, "Get worker TotalAccesses False")
        data["TotalAccesses"] = total_acc.group(1)
        total_kb = re.search("Total kBytes:\s+(\d+)",result)
        if not total_kb:
            return public.returnMsg(False, "Get worker TotalKBytes False")
        data["TotalKBytes"] = total_kb.group(1)
        data["ReqPerSec"] = round(float(reqpersec), 2)
        busywork = re.search("BusyWorkers:\s+(\d+)",result)
        if not busywork:
            return public.returnMsg(False, "Get worker BusyWorkers False")
        data["BusyWorkers"] = busywork.group(1)
        idlework = re.search("IdleWorkers:\s+(\d+)",result)
        if not idlework:
            return public.returnMsg(False, "Get worker IdleWorkers False")
        data["IdleWorkers"] = idlework.group(1)
        data["workercpu"] = round(float(process_cpu["httpd"]),2)
        data["workermem"] = "%s%s" % (int(workermen),"MB")
        return data

    def GetApacheValue(self):
        apachedefaultcontent = public.readFile(self.apachedefaultfile)
        apachempmcontent = public.readFile(self.apachempmfile)
        ps = ["%s，%s" % (public.GetMsg("SECOND"),public.GetMsg("REQUEST_TIMEOUT_TIME")),
              public.GetMsg("KEEP_ALIVE"),
              "%s，%s" % (public.GetMsg("SECOND"),public.GetMsg("CONNECT_TIMEOUT_TIME")),
              public.GetMsg("MAX_KEEP_ALIVE_REQUESTS")]
        gets = ["Timeout","KeepAlive","KeepAliveTimeout","MaxKeepAliveRequests"]
        if public.get_webserver() == 'apache':
            shutil.copyfile(self.apachedefaultfile, '/tmp/apdefault_file_bk.conf')
            shutil.copyfile(self.apachempmfile, '/tmp/apmpm_file_bk.conf')
        conflist = []
        n = 0
        for i in gets:
            rep = "(%s)\s+(\w+)" % i
            k = re.search(rep, apachedefaultcontent)
            if not k:
                return public.returnMsg(False, "Get Key {} False".format(k))
            k = k.group(1)
            v = re.search(rep, apachedefaultcontent)
            if not v:
                return public.returnMsg(False, "Get Value {} False".format(v))
            v = v.group(2)
            psstr = ps[n]
            kv = {"name":k,"value":v,"ps":psstr}
            conflist.append(kv)
            n += 1

        ps = [public.GetMsg("DEFUALT_PROCESSES"),
              public.GetMsg("MAX_SPARE_SERVERS"),
              "%s，%s" % (public.GetMsg("MAX_CONNECTIONS"),public.GetMsg("NOT_LIMITED_BY_0")),
              public.GetMsg("MAX_PROCESSES")]
        gets = ["StartServers","MaxSpareServers","MaxConnectionsPerChild","MaxRequestWorkers"]
        n = 0
        for i in gets:
            rep = "(%s)\s+(\w+)" % i
            k = re.search(rep, apachempmcontent)
            if not k:
                return public.returnMsg(False, "Get Key {} False".format(k))
            k = k.group(1)
            v = re.search(rep, apachempmcontent)
            if not v:
                return public.returnMsg(False, "Get Value {} False".format(v))
            v = v.group(2)
            psstr = ps[n]
            kv = {"name": k, "value": v, "ps": psstr}
            conflist.append(kv)
            n += 1
        return(conflist)

    def SetApacheValue(self,get):
        apachedefaultcontent = public.readFile(self.apachedefaultfile)
        apachempmcontent = public.readFile(self.apachempmfile)
        conflist = []
        getdict = get.__dict__
        for i in getdict.keys():
            if i != "__module__" and i != "__doc__" and i != "data" and i != "args" and i != "action":
                getpost = {
                    "name": i,
                    "value": str(getdict[i])
                }
                conflist.append(getpost)
        public.writeFile("/tmp/list",str(conflist))
        for c in conflist:
            if c["name"] == "KeepAlive":
                if not re.search("on|off", c["value"]):
                    return public.returnMsg(False, "INIT_ARGS_ERR")
            else:
                print(c["value"])
                if not re.search("\d+", c["value"]):
                    print(c["name"],c["value"])
                    return public.returnMsg(False, 'INIT_ARGS_ERR')

            rep = "%s\s+\w+" % c["name"]
            if re.search(rep,apachedefaultcontent):
                newconf = "%s %s" % (c["name"],c["value"])
                apachedefaultcontent = re.sub(rep,newconf,apachedefaultcontent)
            elif re.search(rep,apachempmcontent):
                newconf = "%s\t\t\t%s" % (c["name"], c["value"])
                apachempmcontent = re.sub(rep, newconf , apachempmcontent,count = 1)
        public.writeFile(self.apachedefaultfile,apachedefaultcontent)
        public.writeFile(self.apachempmfile, apachempmcontent)
        isError = public.checkWebConfig()
        if (isError != True):
            shutil.copyfile('/tmp/_file_bk.conf', self.apachedefaultfile)
            shutil.copyfile('/tmp/proxyfile_bk.conf', self.apachempmfile)
            return public.returnMsg(False, 'ERROR: %s<br><a style="color:red;">' % public.GetMsg("CONFIG_ERROR") + isError.replace("\n",
                                                                                            '<br>') + '</a>')
        public.serviceReload()
        return public.returnMsg(True, 'SET_SUCCESS')
