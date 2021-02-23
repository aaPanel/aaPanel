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
from json import loads
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

    def add_nginx_access_log_format(self,args):
        '''
        @name 添加日志格式
        @author zhwen<zhw@bt.cn>
        @param log_format 需要设置的日志格式["$server_name","$remote_addr","-"....]
        @param log_format_name
        @param act 操作方式 add/edit
        '''
        try:
            log_format = loads(args.log_format)
            data = """
        #LOG_FORMAT_BEGIN_{n}
        log_format {n} '{c};'
        #LOG_FORMAT_END_{n}
""".format(n=args.log_format_name,c=' '.join(log_format))
            data = data.replace('$http_user_agent','"$http_user_agent"')
            data = data.replace('$request', '"$request"')
            if args.act == 'edit':
                self.del_nginx_access_log_format(args)
            conf = public.readFile(self.nginxconf)
            if not conf:
                return public.returnMsg(False,'NGINX_CONF_NOT_EXISTS')
            reg = 'http(\n|\s)+{'
            conf = re.sub(reg,'http\n\t{'+data,conf)
            public.writeFile(self.nginxconf,conf)
            public.serviceReload()
            return public.returnMsg(True, 'SET_SUCCESS')
        except:
            return public.returnMsg(False, str(public.get_error_info()))

    def del_nginx_access_log_format(self,args):
        '''
        @name 删除日志格式
        @author zhwen<zhw@bt.cn>
        @param log_format_name
        '''
        conf = public.readFile(self.nginxconf)
        if not conf:
            return public.returnMsg(False, 'NGINX_CONF_NOT_EXISTS')
        reg = '\s*#LOG_FORMAT_BEGIN_{n}(\n|.)+#LOG_FORMAT_END_{n}\n?'.format(n=args.log_format_name)
        conf = re.sub(reg,'',conf)
        public.writeFile(self.nginxconf,conf)
        public.serviceReload()
        return public.returnMsg(True, 'SET_SUCCESS')

    def get_nginx_access_log_format_parameter(self,args=None):
        data = {
            "$server_name":"Server Name",
            "$remote_addr":"Client's IP address",
            "$request":"Request agreement",
            "[$time_local]":"Request time",
            "$status":"http status code",
            "$body_bytes_sent":"Send data size",
            "$http_referer":"http referer",
            "$http_user_agent":"http user agent",
            "$http_x_forwarded_for":"The real ip of the client",
            "$ssl_protocol":"ssl protocol",
            "$ssl_cipher":"ssl cipher",
            "$request_time":"request time",
            "$upstream_addr":"upstream address",
            "$upstream_response_time":"upstream response time",
            "-":"-"
        }
        if hasattr(args,'log_format_name'):
            site_list = self._get_format_log_to_website(args.log_format_name)
            return {'site_list':site_list,'format_log':data}
        else:
            return data

    def _process_log_format(self,tmp):
        log_tips = self.get_nginx_access_log_format_parameter()
        data = []
        for t in tmp:
            t = t.replace('\"','')
            t = t.replace("'", "")
            if t not in log_tips:
                continue
            data.append({t:log_tips[t]})
        return data

    def get_nginx_access_log_format(self,args=None):
        try:
            reg = "#LOG_FORMAT_BEGIN.*"
            conf = public.readFile(self.nginxconf)
            if not conf:
                return public.returnMsg(False, 'NGINX_CONF_NOT_EXISTS')
            data = re.findall(reg,conf)
            format_name = [i.split('_')[-1] for i in data]
            format_log = {}
            for i in format_name:
                format_reg = "#LOG_FORMAT_BEGIN_{n}(\n|.)+log_format\s+{n}\s*(.*);".format(n=i)
                tmp = re.search(format_reg,conf).groups()[1].split()
                format_log[i] = self._process_log_format(tmp)
            return format_log
        except:
            return public.get_error_info()

    def set_format_log_to_website(self,args):
        '''
        @name 设置日志格式
        @author zhwen<zhw@bt.cn>
        @param sites aaa.com,bbb.com
        @param log_format_name
        '''
        # sites = args.sites.split(',')
        sites = loads(args.sites)
        try:
            all_site = public.M('sites').field('name').select()
            reg = 'access_log\s+/www.*{}\s*;'.format(args.log_format_name)
            for site in all_site:
                website_conf_file = '/www/server/panel/vhost/nginx/{}.conf'.format(site['name'])
                conf = public.readFile(website_conf_file)
                if not conf:
                    return public.returnMsg(False, 'NGINX_CONF_NOT_EXISTS')
                format_exist_reg = '(access_log\s+/www.*\.log).*;'
                access_log = re.search(format_exist_reg, conf).groups()[0] + ' ' + args.log_format_name + ';'
                if site['name'] not in sites and re.search(format_exist_reg,conf):
                    access_log = ' '.join(access_log.split()[:-1])+';'
                    conf = re.sub(reg, access_log, conf)
                    public.writeFile(website_conf_file,conf)
                    continue
                conf = re.sub(format_exist_reg,access_log,conf)
                public.writeFile(website_conf_file,conf)
            return public.returnMsg(True, 'SET_SUCCESS')
        except:
            return public.returnMsg(False, str(public.get_error_info()))

    def _get_format_log_to_website(self,log_format_name):
        tmp = public.M('sites').field('name').select()
        reg = 'access_log.*{};'.format(log_format_name)
        data = {}
        for i in tmp:
            website_conf_file = '/www/server/panel/vhost/nginx/{}.conf'.format(i['name'])
            conf = public.readFile(website_conf_file)
            if not conf:
                data[i['name']] = False
                continue
            if re.search(reg,conf):
                data[i['name']] = True
            else:
                data[i['name']] = False
        return data
