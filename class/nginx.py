#coding: utf-8
#-------------------------------------------------------------------
# aaPanel
#-------------------------------------------------------------------
# Copyright (c) 2015-2099 aaPanel(www.aapanel.com) All rights reserved.
#-------------------------------------------------------------------
# Author: hwliang <hwl@aapanel.com>
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
                return public.return_msg_gettext(False, public.lang("Can not find nginx config file [ {} ]", i[1]))
        unitrep = "[kmgKMG]"
        conflist = []
        ps = ["%s,%s" % (public.lang("Worker processes"),public.lang("Auto means automatic")),
              public.lang("Worker connections"),
              public.lang("Connection timeout"),
              public.lang("Whether to enable compressed transmission"),
              public.lang("Minimum file to compress"),
              public.lang("Compression level"),
              public.lang("Maximum file to upload"),
              public.lang("Hash table size of server name"),
              public.lang("Client header buffer size")]
        gets = ["worker_processes","worker_connections","keepalive_timeout","gzip","gzip_min_length",
                "gzip_comp_level","client_max_body_size","server_names_hash_bucket_size","client_header_buffer_size"]
        n = 0
        for i in gets:
            rep = r"(%s)\s+(\w+)" % i
            k = re.search(rep, ngconfcontent)
            if not k:
                return public.return_msg_gettext(False, public.lang("Get key {} False", k))
            k = k.group(1)
            v = re.search(rep, ngconfcontent)
            if not v:
                return public.return_msg_gettext(False, public.lang("Get value {} False", v))
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

            try:
                v = int(v) if k != "worker_processes" and k != "gzip" else v
            except ValueError:
                pass

            kv = {"name":k,"value":v,"unit":u,"ps":psstr}
            conflist.append(kv)
            n += 1
        ps = [public.lang("Client body buffer")]
        gets = ["client_body_buffer_size"]
        n = 0
        for i in gets:
            rep = r"(%s)\s+(\w+)" % i
            k = re.search(rep, proxycontent)
            if not k:
                return public.return_msg_gettext(False, public.lang("Get key {} False", k))
            k=k.group(1)
            v = re.search(rep, proxycontent)
            if not v:
                return public.return_msg_gettext(False, public.lang("Get value {} False", v))
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

            try:
                v = int(v)
            except ValueError:
                v = 0

            kv = {"name":k, "value": int(v), "unit":u,"ps":psstr}
            conflist.append(kv)
            n+=1
        return conflist

    def SetNginxValue(self, get: public.dict_obj):
        ngconfcontent = public.readFile(self.nginxconf)
        proxycontent = public.readFile(self.proxyfile)
        if public.get_webserver() == 'nginx':
            shutil.copyfile(self.nginxconf, '/tmp/ng_file_bk.conf')
            shutil.copyfile(self.proxyfile, '/tmp/proxyfile_bk.conf')
        conflist = []
        getdict = get.get_items()
        for i in getdict.keys():
            if i != "__module__" and i != "__doc__" and i != "data" and i != "args" and i != "action":
                getpost = {
                    "name": i,
                    "value": str(getdict[i])
                }
                conflist.append(getpost)

        for c in conflist:
            rep = r"%s\s+[^kKmMgG\;\n]+" % c["name"]
            if c["name"] == "worker_processes" or c["name"] == "gzip":
                if not re.search(r"auto|on|off|\d+", c["value"]):
                    return public.return_msg_gettext(False, public.lang("Parameter ERROR! -1"))
            else:
                if not re.search(r"\d+", c["value"]):
                    return public.return_msg_gettext(False, public.lang("Parameter ERROR! -2"))
            if re.search(rep,ngconfcontent):
                newconf = "%s %s" % (c["name"],c["value"])
                ngconfcontent = re.sub(rep,newconf,ngconfcontent)
            elif re.search(rep,proxycontent):
                newconf = "%s %s" % (c["name"], c["value"])
                proxycontent = re.sub(rep, newconf , proxycontent)
        public.writeFile(self.nginxconf, ngconfcontent)
        public.writeFile(self.proxyfile, proxycontent)
        isError = public.checkWebConfig()
        if (isError != True):
            shutil.copyfile('/tmp/ng_file_bk.conf', self.nginxconf)
            shutil.copyfile('/tmp/proxyfile_bk.conf', self.proxyfile)
            return public.return_msg_gettext(False, 'ERROR: <br><a style="color:red;">' + isError.replace("\n",
                                                                                                          '<br>') + '</a>')
        public.serviceReload()
        return public.return_msg_gettext(True, public.lang("Setup successfully!"))

    def add_nginx_access_log_format(self,args):
        '''
        @name 添加日志格式
        @author zhwen<zhw@aapanel.com>
        @param log_format 需要设置的日志格式["$server_name","$remote_addr","-"....]
        @param log_format_name
        @param act 操作方式 add/edit
        '''
        try:
            log_format = loads(args.log_format)
            data = """
        #LOG_FORMAT_BEGIN_{n}
        log_format {n} '{c}';
        #LOG_FORMAT_END_{n}
""".format(n=args.log_format_name,c=' '.join(log_format))
            data = data.replace('$http_user_agent','"$http_user_agent"')
            data = data.replace('$request', '"$request"')
            if args.act == 'edit':
                self.del_nginx_access_log_format(args)
            conf = public.readFile(self.nginxconf)
            if not conf:
                return public.return_msg_gettext(False, public.lang("Nginx configuration file does not exist!"))
            reg = r'http(\n|\s)+{'
            conf = re.sub(reg,'http\n\t{'+data,conf)
            public.writeFile(self.nginxconf,conf)
            public.serviceReload()
            return public.return_msg_gettext(True, public.lang("Setup successfully!"))
        except:
            return public.return_msg_gettext(False, str(public.get_error_info()))

    def del_nginx_access_log_format(self,args):
        '''
        @name 删除日志格式
        @author zhwen<zhw@aapanel.com>
        @param log_format_name
        '''
        log_format_name = args.log_format_name
        conf = public.readFile(self.nginxconf)
        if not conf:
            return public.return_msg_gettext(False, public.lang("Nginx configuration file does not exist!"))
        reg = r'\s*#LOG_FORMAT_BEGIN_{n}(\n|.)+#LOG_FORMAT_END_{n}\n?'.format(n=args.log_format_name)
        conf = re.sub(reg,'',conf)
        self._del_format_log_of_website(log_format_name)
        public.writeFile(self.nginxconf,conf)
        public.serviceReload()
        return public.return_msg_gettext(True, public.lang("Setup successfully!"))

    def del_all_log_format(self,args):
        all_format = self.get_nginx_access_log_format(args)
        for i in all_format:
            args.log_format_name = i
            self.del_nginx_access_log_format(args)

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
                return public.return_msg_gettext(False, public.lang("Nginx configuration file does not exist!"))
            data = re.findall(reg,conf)
            format_name = [i.split('LOG_FORMAT_BEGIN_')[-1] for i in data]
            format_log = {}
            for i in format_name:
                format_reg = r"#LOG_FORMAT_BEGIN_{n}(\n|.)+log_format\s+{n}\s*(.*);".format(n=i)
                tmp = re.search(format_reg,conf)
                if not tmp:
                    continue
                tmp = tmp.groups()[1].split()
                format_log[i] = self._process_log_format(tmp)
            return format_log
        except:
            return public.return_msg_gettext(False,public.get_error_info())

    def set_format_log_to_website(self,args):
        '''
        @name 设置日志格式
        @author zhwen<zhw@aapanel.com>
        @param sites aaa.com,bbb.com
        @param log_format_name
        '''
        # sites = args.sites.split(',')
        sites = loads(args.sites)
        try:
            all_site = public.M('sites').field('name').select()
            reg = r'access_log\s+/www.*{}\s*;'.format(args.log_format_name)
            for site in all_site:
                website_conf_file = '/www/server/panel/vhost/nginx/{}.conf'.format(site['name'])
                conf = public.readFile(website_conf_file)
                if not conf:
                    return public.return_msg_gettext(False, public.lang("Nginx configuration file does not exist!"))
                format_exist_reg = r'(access_log\s+/www.*\.log).*;'
                access_log = self.get_nginx_access_log(conf)
                if not access_log:
                    continue
                access_log = 'access_log '+ access_log + ' ' + args.log_format_name + ';'
                if site['name'] not in sites and re.search(format_exist_reg,conf):
                    access_log = ' '.join(access_log.split()[:-1])+';'
                    conf = re.sub(reg, access_log, conf)
                    public.writeFile(website_conf_file,conf)
                    continue
                conf = re.sub(format_exist_reg,access_log,conf)
                public.writeFile(website_conf_file,conf)
            return public.return_msg_gettext(True, public.lang("Setup successfully!"))
        except:
            return public.return_msg_gettext(False, str(public.get_error_info()))

    def get_nginx_access_log(self,nginx_conf):
        try:
            reg = r'access_log\s+(.*\.log)'
            log_path = re.findall(reg, nginx_conf)
            if not log_path:
                return False
            for i in log_path:
                if 'purge_cache' in i:
                    continue
                if not os.path.exists(i):
                    continue
                return i
            return False
        except:
            return False

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

    def _del_format_log_of_website(self,log_format_name):
        site_format_log_status = self._get_format_log_to_website(log_format_name)
        try:
            for s in site_format_log_status.keys():
                if not site_format_log_status[s]:
                    continue
                website_conf_file = '/www/server/panel/vhost/nginx/{}.conf'.format(s)
                format_exist_reg = r'access_log\s+/www.*\.log\s+{};'.format(log_format_name)
                conf = public.readFile(website_conf_file)
                if not conf:continue
                if not re.search(format_exist_reg,conf):continue
                access_log = re.search(format_exist_reg,conf).group().split()
                access_log = access_log[0] + ' ' +access_log[1] +';'
                conf = re.sub(format_exist_reg,access_log,conf)
                public.writeFile(website_conf_file,conf)
            return True
        except:
            return False