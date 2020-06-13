#coding: utf-8
#-------------------------------------------------------------------
# 宝塔Linux面板
#-------------------------------------------------------------------
# Copyright (c) 2015-2099 宝塔软件(http:#bt.cn) All rights reserved.
#-------------------------------------------------------------------
# Author: hwliang <hwl@bt.cn>
#-------------------------------------------------------------------

#------------------------------
# Nginx管理模块
#------------------------------
import public,os,re,shutil
os.chdir("/www/server/panel")

class nginx:
    setupPath = '/www/server'
    nginxconf = "%s/nginx/conf/nginx.conf" % (setupPath)
    proxyfile = "%s/nginx/conf/proxy.conf" % (setupPath)
    def GetNginxValue(self):
        ngconfcontent = public.readFile(self.nginxconf)
        proxycontent = public.readFile(self.proxyfile)
        for i in [[ngconfcontent,self.nginxconf],[proxycontent,self.proxyfile]]:
            if not i[0]:
                return public.returnMsg(False,"Can not find nginx config file [ {} ]".format(i[1]))
        unitrep = "[kmgKMG]"
        conflist = []
        ps = ["%s,%s" % (public.GetMsg("WORKER_PROCESSES"),public.GetMsg("WORKER_PROCESSES_AUTO")),
              public.GetMsg("WORKER_CONNECTIONS"),
              public.GetMsg("CONNECT_TIMEOUT_TIME"),
              public.GetMsg("NGINX_ZIP"),
              public.GetMsg("NGINX_ZIP_MIN"),
              public.GetMsg("ZIP_COMP_LEVEL"),
              public.GetMsg("UPLOAD_MAX_FILE"),
              public.GetMsg("SERVER_NAME_HASH"),
              public.GetMsg("CLIENT_HEADER_BUFF")]
        gets = ["worker_processes","worker_connections","keepalive_timeout","gzip","gzip_min_length","gzip_comp_level","client_max_body_size","server_names_hash_bucket_size","client_header_buffer_size"]
        n = 0
        for i in gets:
            rep = "(%s)\s+(\w+)" % i
            k = re.search(rep, ngconfcontent)
            if not k:
                return public.returnMsg(False,"Get key {} False".format(k))
            k = k.group(1)
            v = re.search(rep, ngconfcontent)
            if not v:
                return public.returnMsg(False,"Get value {} False".format(v))
            v = v.group(2)
            if re.search(unitrep,v):
                u = str.upper(v[-1])
                v = v[:-1]
                if len(u) == 1:
                    psstr = u+"B，"+ps[n]
                else:
                    psstr = u + "，" + ps[n]
            else:
                u = ""
                psstr = ps[n]
            kv = {"name":k,"value":v,"unit":u,"ps":psstr}
            conflist.append(kv)
            n += 1
        ps = [public.GetMsg("CLIENT_BODY_BUFF")]
        gets = ["client_body_buffer_size"]
        n = 0
        for i in gets:
            rep = "(%s)\s+(\w+)" % i
            k = re.search(rep, proxycontent)
            if not k:
                return public.returnMsg(False,"Get key {} False".format(k))
            k=k.group(1)
            v = re.search(rep, proxycontent)
            if not v:
                return public.returnMsg(False,"Get value {} False".format(v))
            v = v.group(2)
            if re.search(unitrep, v):
                u = str.upper(v[-1])
                v = v[:-1]
                if len(u) == 1:
                    psstr = u+"B，"+ps[n]
                else:
                    psstr = u + "，" + ps[n]
            else:
                psstr = ps[n]
                u = ""
            kv = {"name":k, "value":v, "unit":u,"ps":psstr}
            conflist.append(kv)
            n+=1
        print(conflist)
        return conflist

    def SetNginxValue(self,get):
        ngconfcontent = public.readFile(self.nginxconf)
        proxycontent = public.readFile(self.proxyfile)
        if public.get_webserver() == 'nginx':
            shutil.copyfile(self.nginxconf, '/tmp/ng_file_bk.conf')
            shutil.copyfile(self.proxyfile, '/tmp/proxyfile_bk.conf')
        conflist = []
        getdict = get.__dict__
        for i in getdict.keys():
            if i != "__module__" and i != "__doc__" and i != "data" and i != "args" and i != "action":
                getpost = {
                    "name": i,
                    "value": str(getdict[i])
                }
                conflist.append(getpost)

        for c in conflist:
            rep = "%s\s+[^kKmMgG\;\n]+" % c["name"]
            if c["name"] == "worker_processes" or c["name"] == "gzip":
                if not re.search("auto|on|off|\d+", c["value"]):
                    return public.returnMsg(False, 'INIT_ARGS_ERR')
            else:
                if not re.search("\d+", c["value"]):
                    return public.returnMsg(False, 'INIT_ARGS_ERR')
            if re.search(rep,ngconfcontent):
                newconf = "%s %s" % (c["name"],c["value"])
                ngconfcontent = re.sub(rep,newconf,ngconfcontent)
            elif re.search(rep,proxycontent):
                newconf = "%s %s" % (c["name"], c["value"])
                proxycontent = re.sub(rep, newconf , proxycontent)
        public.writeFile(self.nginxconf,ngconfcontent)
        public.writeFile(self.proxyfile, proxycontent)
        isError = public.checkWebConfig()
        if (isError != True):
            shutil.copyfile('/tmp/ng_file_bk.conf', self.nginxconf)
            shutil.copyfile('/tmp/proxyfile_bk.conf', self.proxyfile)
            return public.returnMsg(False, 'ERROR: <br><a style="color:red;">' + isError.replace("\n",
                                                                                                          '<br>') + '</a>')
        public.serviceReload()
        return public.returnMsg(True, 'SET_SUCCESS')
