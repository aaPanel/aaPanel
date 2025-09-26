# coding: utf-8
# +-------------------------------------------------------------------
# | 宝塔Linux面板
# +-------------------------------------------------------------------
# | Copyright (c) 2024-2099 宝塔软件(http://bt.cn) All rights reserved.
# +-------------------------------------------------------------------
# | Author: lkq <safe@bt.cn>
# +-------------------------------------------------------------------
# |   Wordpress 安全扫描
# +--------------------------------------------------------------------
import json, os, time
import requests,re,zipfile
proxies = {}
import public
import sys,os
if "/www/server/panel/class_v2/wp_toolkit/" not in sys.path:
    sys.path.insert(1, "/www/server/panel/class_v2/wp_toolkit/")
#进入到
from . import totle_db

class wordpress_scan:
    wordpress_diff_path = "/www/wordpress_diff_path"

    #默认插件的头部信息
    plugin_default_headers = {
        "Name": "Plugin Name",
        "PluginURI": "Plugin URI",
        "Version": "Version",
        "Description": "Description",
        "Author": "Author",
        "AuthorURI": "Author URI",
        "TextDomain": "Text Domain",
        "DomainPath": "Domain Path",
        "Network": "Network",
        "RequiresWP": "Requires at least",
        "RequiresPHP": "Requires PHP",
        "UpdateURI": "Update URI",
        "RequiresPlugins": "Requires Plugins",
        "_sitewide": "Site Wide Only"
    }

    #默认主题的头部信息
    theme_default_headers = {
        "Name": "Theme Name",
        "Title": "Theme Name",
        "Version": "Version",
        "Author": "Author",
        "AuthorURI": "Author URI",
        "UpdateURI": "Update URI",
        "Template": "Theme Name",
        "Stylesheet": "Theme Name",
    }

    def check_dir(self):
        '''
            @name 检查需要的目录是否存在
            @auther lkq
            @time 2024-10-08
            @msg 检查需要的目录是否存在
        '''
        if not os.path.exists(self.wordpress_diff_path):
            os.makedirs(self.wordpress_diff_path)

        if not os.path.exists(self.wordpress_diff_path + "/plugin/"):
            os.makedirs(self.wordpress_diff_path + "/plugin/")

    def M(self, table, db="wordpress_plugin"):
        '''
            @name 获取数据库对象
            @param table 表名
            @param db 数据库名
        '''
        with totle_db.Sql(db) as sql:
            return sql.table(table)

    def get_wordpress_version(self, path):
        '''
            @name 获取WordPress版本
            @param path WordPress路径
            @return dict
        '''
        wp_version_file = path + "/wp-includes/version.php"
        version = {"version": "", "locale": ""}
        if not os.path.exists(wp_version_file): return version
        with open(wp_version_file, 'r', encoding='utf-8') as file:
            file_data = file.read()
        match = re.search(r"\$wp_version\s*=\s*\'(.*)\';", file_data)
        if match:
            version["version"] = match.group(1)
        # $wp_local_package
        match = re.search(r"\$wp_local_package\s*=\s*\'(.*)\';", file_data)
        if match:
            version["locale"] = match.group(1)
        return version

    def get_plugin_data(self, plugin_file, default_headers, context=''):
        '''
            @参考：/wp-admin/includes/plugin.php get_plugin_data 代码
            @name 获取插件信息
            @param plugin_file 插件文件
            @return dict
            @auther lkq
            @time 2024-10-08
        '''
        # 读取文件内容
        if not os.path.exists(plugin_file): return {}
        # 定义8KB大小
        max_length = 8 * 1024  # 8 KB
        try:
            # 读取文件的前8KB
            with open(plugin_file, 'r', encoding='utf-8') as file:
                file_data = file.read(max_length)
        except Exception as e:
            return {}
        # 替换CR为LF
        file_data = file_data.replace('\r', '\n')
        # 处理额外的headers
        extra_headers = {}
        if context:
            extra_context_headers = []
            # 假设有一个函数可以获取额外的headers
            # extra_context_headers = get_extra_headers(context)
            extra_headers = dict.fromkeys(extra_context_headers, '')  # 假设额外的headers
        all_headers = {**extra_headers, **default_headers}

        # 检索所有headers
        for field, regex in all_headers.items():
            if field.startswith('_'):  # 跳过以_开头的内部字段
                continue
            match = re.search(f'{regex}:(.*)$', file_data, re.IGNORECASE | re.MULTILINE)
            if match:
                all_headers[field] = match.group(1).strip()
            else:
                all_headers[field] = ''
        if all_headers.get("Network") and not all_headers['Network'] and all_headers['_sitewide']:
            all_headers['Network'] = all_headers['_sitewide']
        if all_headers.get("Network"):
            all_headers['Network'] = 'true' == all_headers['Network'].lower()
        if all_headers.get("_sitewide"):
            del all_headers['_sitewide']

        if all_headers.get("TextDomain") and not all_headers['TextDomain']:
            plugin_slug = os.path.dirname(os.path.basename(plugin_file))
            if '.' != plugin_slug and '/' not in plugin_slug:
                all_headers['TextDomain'] = plugin_slug

        all_headers['Title'] = all_headers['Name']
        all_headers['AuthorName'] = all_headers['Author']

        # 返回插件的信息
        return all_headers

    def Md5(self,strings):
        """
            @name    生成MD5
            @author hwliang<hwl@bt.cn>
            @param strings 要被处理的字符串
            @return string(32)
        """
        if type(strings) != bytes:
            strings = strings.encode()
        import hashlib
        m = hashlib.md5()
        m.update(strings)
        return m.hexdigest()

    def FileMd5(self,filename):
        """
            @name 生成文件的MD5
            @author hwliang<hwl@bt.cn>
            @param filename 文件名
            @return string(32) or False
        """
        if not os.path.isfile(filename): return False
        import hashlib
        my_hash = hashlib.md5()
        f = open(filename, 'rb')
        while True:
            b = f.read(8096)
            if not b:
                break
            my_hash.update(b)
        f.close()
        return my_hash.hexdigest()

    def get_plugin(self, path,one=''):
        '''
            @name 获取WordPress插件信息
            @param path 插件路径
            @return dict
            @auther lkq
            @time 2024-10-08
        '''
        plugin_path = path + "/wp-content/plugins"
        if not os.path.exists(plugin_path): return {}
        tmp_list = []
        for file in os.listdir(plugin_path):
            if one:
                if file!=one:continue
            plugin_file = os.path.join(plugin_path, file)
            # if os.path.isfile(plugin_file) and plugin_file.endswith(".php"):
            #     tmp_list.append(file)
            if os.path.isdir(plugin_file):
                # 读取文件夹中的第一层文件
                for file2 in os.listdir(plugin_file):
                    plugin_file2 = os.path.join(plugin_file, file2)
                    if os.path.isfile(plugin_file2) and plugin_file2.endswith(".php"): tmp_list.append(
                        file + "/" + file2)
        if len(tmp_list) == 0: return {}
        result = {}

        for i in tmp_list:
            plugin_file = plugin_path + "/" + i
            # 判断文件是否可读
            if not os.access(plugin_file, os.R_OK): continue
            plugin_data = self.get_plugin_data(plugin_file, self.plugin_default_headers)
            if not plugin_data: continue
            if plugin_data["Name"] == "": continue
            #如果 name 中没/ 的话
            if "/" not in i:
                #则判断一下
                if 'wordpress.org/plugins/' in  plugin_data["PluginURI"]:
                    plugin_data["PluginURI"] = plugin_data["PluginURI"].replace('http://wordpress.org/plugins/', '').replace("http://wordpress.org/plugins/","")
                    #去掉最后的/
                    if plugin_data["PluginURI"][-1]=="/":
                        plugin_data["PluginURI"]=plugin_data["PluginURI"][:-1]
                    i=plugin_data["PluginURI"]
                else:
                    continue
            result[i] = plugin_data
        return result

    def get_themes(self, path):
        '''
            @name 获取WordPress主题信息
            @param path 主题路径
            @return dict
            @auther lkq
            @time 2024-10-08
        '''
        themes_path = path + "/wp-content/themes"
        # 循环目录
        if not os.path.exists(themes_path): return {}
        tmp_list = []
        for file in os.listdir(themes_path):
            plugin_file = os.path.join(themes_path, file)
            if os.path.isdir(plugin_file):
                if os.path.exists(plugin_file + "/style.css"):
                    tmp_list.append(file)
        if len(tmp_list) == 0: return {}

        result = {}
        for i in tmp_list:
            plugin_file = themes_path + "/" + i + "/style.css"
            # 判断文件是否可读
            if not os.access(plugin_file, os.R_OK): continue
            plugin_data = self.get_plugin_data(plugin_file, self.theme_default_headers)
            if not plugin_data: continue
            if plugin_data["Name"] == "": continue
            result[i] = plugin_data
        return result

    def get_plugins_update(self, path):
        '''
            @name 获取插件更新
            @param path WordPress路径
            @auther lkq
            @time 2024-10-10
            @msg 获取插件更新
        '''
        plugin_info = self.get_plugin(path)
        active = []
        url = 'http://api.wordpress.org/plugins/update-check/1.1/'
        for i in plugin_info: active.append(i)
        plugins = {"plugins": json.dumps({"plugins": plugin_info, "active": active}), "locale": "%5B%22zh_CN%22%5D",
                   "all": "true", "translations": ""}
        headers = {
            'User-Agent': "WordPress/6.6.2; http://wp471.com",
            'Content-Type': 'application/x-www-form-urlencoded',
        }
        response = requests.post(url, headers=headers, data=plugins, proxies=proxies)
        print(response.text)

    def get_themes_update(self, path):
        '''
            @name 获取主题更新
            @param path WordPress路径
            @auther lkq
            @time 2024-10-10
            @msg 获取主题更新
        '''
        plugin_info = self.get_themes(path)
        active = []
        url = 'http://api.wordpress.org/themes/update-check/1.1/'
        for i in plugin_info: active.append(i)
        plugins = {"themes": json.dumps({"themes": plugin_info, "active": active}), "locale": "", "all": "true",
                   "translations": ""}
        headers = {
            'User-Agent': "WordPress/6.6.2; http://wp471.com",
            'Content-Type': 'application/x-www-form-urlencoded',
        }
        response = requests.post(url, headers=headers, data=plugins, proxies=proxies)
        print(response.text)

    def get_wordpress_update(self, path):
        '''
            @name 获取WordPress更新
            @param path WordPress路径
            @auther lkq
            @time 2024-10-10
            @msg 获取WordPress更新
        '''
        version = self.get_wordpress_version(path)
        if version["version"] == "":
            return
        url = 'http://api.wordpress.org/core/version-check/1.7/?version=' + version["version"] + '&locale=' + version[
            "locale"]
        headers = {
            'User-Agent': "WordPress/6.6.2; http://wp471.com",
        }
        response = requests.get(url, headers=headers, proxies=proxies)
        print(response.text)

    def compare_versions(self,version1, version2):
        '''
            @name 对比版本号
            @param version1 版本1
            @param version2 版本2
            @return int  0 相等 1 大于 -1 小于
        '''
        # 分割版本号为整数列表
        v1 = [int(num) if num.strip() != '' else 0 for num in version1.split('.')]
        v2 = [int(num) if num.strip() != '' else 0 for num in version2.split('.')]
        # 逐个比较版本号的每个部分
        for num1, num2 in zip(v1, v2):
            if num1 > num2:
                return 1  # version1 > version2
            elif num1 < num2:
                return -1  # version1 < version2
        # 如果所有部分都相同，比较长度（处理像'1.0'和'1.0.0'这样的情况）
        if len(v1) > len(v2):
            return 1 if any(num > 0 for num in v1[len(v2):]) else 0
        elif len(v1) < len(v2):
            return -1 if any(num > 0 for num in v2[len(v1):]) else 0
        # 如果完全相同
        return 0

    def let_identify(self,version,vlun_infos):
        '''
            @name 对比版本号判断是否存在漏洞
            @param version 当前版本
            @param vlun_infos 漏洞信息
            @return list
        '''
        for i in vlun_infos:
            i["vlun_status"] = False
            #如果是小于等于的话
            if i["let"]=="<=":
                if self.compare_versions(version,i["vlun_version"])<=0:
                    i["vlun_status"]=True
            #小于
            if i["let"]=="<":
                if self.compare_versions(version,i["vlun_version"])<0:
                    i["vlun_status"]=True
            if i['let']=='-':
                #从某个版本开始、到某个版本结束
                version_list=i["vlun_version"].split("-")
                if len(version_list)!=2:continue
                if self.compare_versions(version,version_list[0])>=0 and self.compare_versions(version,version_list[1])<=0:
                    i["vlun_status"]=True

        return vlun_infos

    def scan(self,path):
        '''
            @name 扫描WordPress
            @param path WordPress路径
            @return dict
            @auther lkq
            @time 2024-10-10
            @msg 通过扫描WordPress的版本、插件、主题来判断是否存在漏洞
        '''
        vlun_list = []
        #判断文件是否存在
        import os
        if not os.path.exists(path):
            return vlun_list
        result = {}
        result["version"] = self.get_wordpress_version(path)
        result["plugins"] = self.get_plugin(path)
        result["themes"] = self.get_themes(path)

        #扫描插件是否存在漏洞
        for i in result["plugins"]:
            plguin=i.split("/")[0]
            Name=result["plugins"][i]["Name"]
            #检查插件是否下架了
            if self.M("plugin_error","plugin_error").where("slug=?",(plguin,)).count()>0:
                error_status = self.M("plugin_error","plugin_error").where("slug=?",(plguin,)).field("error,name,slug,description,closed_date,reason,status").find()
                if type(error_status)!=dict:continue
                if error_status["status"]==0:
                    vlun = {"name": "", "vlun_info": "", "css": "", "type": "plugin_closed", "load_version": "","cve": "","time":"","status":0}
                    #时间格式转为时间戳
                    if len(error_status["closed_date"])<10:
                        error_status["closed_date"]=int(time.time())
                    else:
                        try:
                            error_status["closed_date"]=int(time.mktime(time.strptime(error_status["closed_date"], "%Y-%m-%d %H:%M:%S")))
                        except:
                            error_status["closed_date"]=int(time.time())
                    vlun["slug"]=plguin
                    vlun["name"]=Name
                    vlun["vlun_info"]=error_status["description"]
                    vlun["css"]="10"
                    vlun["load_version"]=result["plugins"][i]["Version"]
                    vlun["time"]=error_status["closed_date"]
                    vlun_list.append(vlun)
                    # continue
            #检查插件这个插件是否好久没有更新了
            if self.M("wordpress_not_update","wordpress_not_update").where("slug=?",(plguin,)).count()>0:
                error_status = self.M("wordpress_not_update", "wordpress_not_update").where("slug=?", (plguin,)).field(
                    "last_time,status").find()
                vlun = {"name": "", "vlun_info": "", "css": "", "type": "plugin_not_update", "load_version": "", "cve": "",
                        "time": "", "status": 0}
                if type(error_status)!=dict:continue
                #当前时间减去最后更新时间 计算出年数
                if len(str(error_status["last_time"])) > 6:
                    #当前时间减去最后更新时间 计算出年数
                    year = int((time.time() - error_status["last_time"]) / 60 / 60 / 24 / 365)
                    if year >= 10:
                        vlun["css"] = 10
                    elif year >= 5:
                        vlun["css"] = 8
                    elif year >= 3:
                        vlun["css"] = 6
                    vlun["slug"] = plguin
                    vlun["name"] = Name
                    vlun["vlun_info"] = "The plugin has not been updated for more than {} years".format(year)
                    vlun["load_version"] = result["plugins"][i]["Version"]
                    vlun["time"] = int(time.time())
                    vlun_list.append(vlun)

            if result["plugins"][i]["Version"]=="":continue
            #检查插件是否存在漏洞
            if self.M("wordpress_vulnerabilities","wordpress_vulnerabilities").where("plugin=?",(plguin,)).count()>0:
                vlun_infos=self.M("wordpress_vulnerabilities","wordpress_vulnerabilities").where("plugin=? and types='plugin'",(plguin)).select()
                vlun_infos=self.let_identify(result["plugins"][i]["Version"],vlun_infos)
                for j2 in vlun_infos:
                    if j2["vlun_status"]:
                        vlun = {"name": "", "vlun_info": "", "css": "", "type": "plugin", "load_version": "","cve": "","time":""}
                        vlun["load_version"]=result["plugins"][i]["Version"]
                        vlun["cve"]=j2["cve"]
                        vlun["slug"]=plguin
                        vlun["name"] = Name
                        vlun["vlun_info"]=j2["msg"]
                        vlun["css"]=j2["css"]
                        vlun["time"] = j2["data_time"]
                        vlun_list.append(vlun)
        #扫描主题是否存在漏洞
        for i in result["themes"]:
            plguin = i.split("/")[0]
            if result["themes"][i]["Version"] == "": continue
            Name = result["themes"][i]["Name"]
            # 检查插件是否存在漏洞
            if self.M("wordpress_vulnerabilities","wordpress_vulnerabilities").where("plugin=? and types='theme'", (plguin,)).count() > 0:
                vlun_infos = self.M("wordpress_vulnerabilities","wordpress_vulnerabilities").where("plugin=? and types='theme'", (plguin)).select()
                vlun_infos = self.let_identify(result["themes"][i]["Version"], vlun_infos)
                for j2 in vlun_infos:
                    if j2["vlun_status"]:
                        vlun = {"name": "", "vlun_info": "", "css": "", "type": "theme", "load_version": "","cve": "","time":""}
                        vlun["load_version"] = result["themes"][i]["Version"]
                        vlun["cve"] = j2["cve"]
                        vlun["slug"] = plguin
                        vlun["name"] = Name
                        vlun["vlun_info"] = j2["msg"]
                        vlun["css"] = j2["css"]
                        vlun["time"] = j2["data_time"]
                        vlun_list.append(vlun)

        #检查WordPress是否存在漏洞  #使用date_time 排序取最新的15个版本
        if len(result["version"]["version"])>=1 and  self.M("wordpress_vulnerabilities", "wordpress_vulnerabilities").where("types=?",("core")).count() > 0:
            #取10个版本
            vlun_infos = self.M("wordpress_vulnerabilities","wordpress_vulnerabilities").where("types=?",("core")).order("data_time desc").limit("15").select()
            vlun_infos = self.let_identify(result["version"]["version"], vlun_infos)
            for j2 in vlun_infos:
                if j2["vlun_status"]:
                    vlun = {"name": "", "vlun_info": "", "css": "", "type": "core", "load_version": "","cve": "","time":""}
                    vlun["load_version"] = result["version"]["version"]
                    vlun["cve"] = j2["cve"]
                    vlun["slug"] = "WordPress"
                    vlun["name"] = "WordPress"
                    vlun["vlun_info"] = j2["msg"]
                    vlun["css"] = j2["css"]
                    vlun["time"]=j2["data_time"]
                    vlun_list.append(vlun)
        #忽略
        ignore_path = "/www/server/panel/data/wordpress_ignore_vuln.json"
        if os.path.exists(ignore_path):
            try:
                ignore_infos = json.loads(public.readFile(ignore_path))
            except:
                ignore_infos = {}
        else:
            ignore_infos = {}
        if path  in ignore_infos:
            for i in ignore_infos[path]:
                for i2 in vlun_list:
                    if i["type"]=="plugin_closed":
                        if i["slug"]==i2["slug"]:
                            vlun_list.remove(i2)
                    if i["type"]=="plugin_not_update":
                        if i["slug"]==i2["slug"]:
                            vlun_list.remove(i2)
                    if i["slug"]==i2["slug"] and i["name"]==i2["name"] and i["vlun_info"]==i2["vlun_info"] and i["css"]==i2["css"] and i["type"]==i2["type"] and i["cve"]==i2["cve"] and i["time"]==i2["time"]:
                        vlun_list.remove(i2)

        #更新到文件中
        wordpress_scan_path = "/www/server/panel/data/wordpress_wp_scan.json"
        status= {"last_time": int(time.time()), "vulnerabilities": len(vlun_list), "status": True}
        import os
        if os.path.exists(wordpress_scan_path):
            try:
                wordpress_scan_info = json.loads(public.readFile(wordpress_scan_path))
            except:
                wordpress_scan_info = {}
        else:
            wordpress_scan_info = {}
        if path not in wordpress_scan_info:
            wordpress_scan_info[path]=status
        else:
            wordpress_scan_info[path]["last_time"]=int(time.time())
            wordpress_scan_info[path]["vulnerabilities"]=len(vlun_list)
        public.WriteFile(wordpress_scan_path,json.dumps(wordpress_scan_info))
        return vlun_list

    def ignore_vuln(self,get):
        '''
            @name 增加忽略漏洞
            @param slug 插件slug
            @param path 插件路径
            @auther lkq
            @time 2024-10-10
            @msg 增加忽略漏洞
        '''
        if 'path' not in get: return public.return_message(-1,0,public.lang("Parameter error"))
        if 'name' not in get: return public.return_message(-1,0,public.lang("Parameter error"))
        if 'vlun_info' not in get: return public.return_message(-1,0,public.lang("Parameter error"))
        if 'css' not in get: return public.return_message(-1,0,public.lang("Parameter error"))
        if 'type' not in get: return public.return_message(-1,0,public.lang("Parameter error"))
        if 'cve' not in get: return public.return_message(-1,0,public.lang("Parameter error"))
        if 'time' not in get: return public.return_message(-1, 0, public.lang("Parameter error"))
        if 'slug' not in get: return public.return_message(-1, 0, public.lang("Parameter error"))
        if 'ignore_type' not in get: return public.return_message(-1, 0, public.lang("Parameter error"))
        path = get['path']
        name = get['name']
        vlun_info = get['vlun_info']
        css = float(get['css'])
        type = get['type']
        cve = get['cve']
        time = int(get['time'])
        slug = get['slug']
        ignore_type=get['ignore_type']
        #忽略的列表路径path
        ignore_path ="/www/server/panel/data/wordpress_ignore_vuln.json"
        if os.path.exists(ignore_path):
            try:
                ignore_infos=json.loads(public.readFile(ignore_path))
            except:
                ignore_infos={}
        else:
            ignore_infos={}

        if ignore_type=="add":
            if path not in ignore_infos:
                ignore_infos[path]=[]
            ignore={"name":name,"vlun_info":vlun_info,"css":css,"type":type,"cve":cve,"time":time,"slug":slug}
            if ignore not in ignore_infos[path]:
                ignore_infos[path].append(ignore)
            public.writeFile(ignore_path,json.dumps(ignore_infos))
            return public.return_message(0,0,public.lang("Added successfully"))
        if ignore_type=="del":
            if path not in ignore_infos:
                return public.return_message(-1,0,public.lang("No data found"))
            ignore={"name":name,"vlun_info":vlun_info,"css":css,"type":type,"cve":cve,"time":time,"slug":slug}
            if ignore in ignore_infos[path]:
                ignore_infos[path].remove(ignore)
            public.writeFile(ignore_path,json.dumps(ignore_infos))
            return public.return_message(0,0,public.lang("Deleted successfully"))

    def get_ignore_vuln(self,get):
        '''
            @name 获取忽略的漏洞
            @param path 插件路径
            @auther lkq
            @time 2024-10-10
            @msg 获取忽略的漏洞
        '''
        #如果不传递参数就返回所有
        ignore_path = "/www/server/panel/data/wordpress_ignore_vuln.json"
        if os.path.exists(ignore_path):
            try:
                ignore_infos = json.loads(public.readFile(ignore_path))
            except:
                ignore_infos = {}
        else:
            ignore_infos = {}
        if 'path' in get:
            path = get['path']
            if path not in ignore_infos:
                return public.return_message(0,0,[])
            else:
                return public.return_message(0,0,ignore_infos[path])
        else:
            return public.return_message(0, 0, [])

    def download_file_with_progress(self,url, filename,slug,re=False):
        '''
            @name 下载插件的文件
            @param url 下载地址
            @param filename 文件名
            @param slug 插件slug
            @param re 是否重试
        '''
        header = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        }
        with requests.get(url, stream=True, headers=header, proxies=proxies, timeout=20) as response:
            #判断状态码
            if response.status_code!=200:
                # print("Download failed, status code:",response.status_code," URL:",url)
                if not re:
                    self.download_file_with_progress("https://downloads.wordpress.org/plugin/"+slug+".zip", filename,slug,re=True)
                    return
            total_length = response.headers.get('content-length')
            if total_length is None:  # 无法获取文件大小
                response.raise_for_status()
                with open(filename, 'wb') as file:
                    for chunk in response.iter_content(chunk_size=65536):
                        if chunk:  # 过滤掉保活新块
                            file.write(chunk)
                            file.flush()
            else:
                total_length = int(total_length)
                if total_length > 1024 * 1024 * 20:
                    print("\nSkip files larger than 20M ", slug)
                    return
                downloaded = 0
                with open(filename, 'wb') as file:
                    for chunk in response.iter_content(chunk_size=65536):
                        file.write(chunk)
                        file.flush()
                        downloaded += len(chunk)
                        # 计算下载进度
                        done = int(50 * downloaded / total_length)
                        if total_length < 1024 * 1024:
                            total_length_mb = total_length / 1024
                            # 已下载大小转为KB
                            downloaded_mb = downloaded / 1024
                            infos = "{:.2f}KB/{:.2f}KB slug:{}".format(downloaded_mb, total_length_mb,slug)
                        else:
                            total_length_mb = total_length / (1024 * 1024)
                            downloaded_mb = downloaded / (1024 * 1024)
                            infos = "{:.2f}MB/{:.2f}MB slug:{}".format(downloaded_mb, total_length_mb,slug)
                        print("\r[{}{}] {:.2f}%  file_size:{} ".format('█' * done, '.' * (50 - done),100 * downloaded / total_length,infos,), end='')
                # 判断文件是否下载完整
                if total_length != os.path.getsize(filename):
                    os.remove(filename)
                    print("\nThe downloaded file is incomplete and has been deleted. The file is currently being re downloaded", filename)
                    self.download_file_with_progress(url, filename,slug)

    def zip_file_plugin_data(self,file_data, default_headers, context=''):
        '''
            @参考：/wp-admin/includes/plugin.php get_plugin_data 代码
            @name 通过ZIP文件获取插件信息
            @param plugin_file 插件文件
            @return dict
            @auther lkq
            @time 2024-10-08
        '''
        file_data = file_data.replace('\r', '\n')
        # 处理额外的headers
        extra_headers = {}
        if context:
            extra_context_headers = []
            extra_headers = dict.fromkeys(extra_context_headers, '')  # 假设额外的headers
        all_headers = {**extra_headers, **default_headers}
        # 检索所有headers
        for field, regex in all_headers.items():
            if field.startswith('_'):  # 跳过以_开头的内部字段
                continue
            match = re.search(f'{regex}:(.*)$', file_data, re.IGNORECASE | re.MULTILINE)
            if match:
                all_headers[field] = match.group(1).strip()
            else:
                all_headers[field] = ''
        if all_headers.get("Network") and not all_headers['Network'] and all_headers['_sitewide']:
            all_headers['Network'] = all_headers['_sitewide']
        if all_headers.get("Network"):
            all_headers['Network'] = 'true' == all_headers['Network'].lower()
        if all_headers.get("_sitewide"):
            del all_headers['_sitewide']
        all_headers['Title'] = all_headers['Name']
        all_headers['AuthorName'] = all_headers['Author']
        # 返回插件的信息
        return all_headers

    def check_plugin(self,path,plugin_info):
        '''
            @name 检查所有的插件是否被修改过、或者新增了文件
            @param path WordPress路径
            @param plugin_info 插件信息
            @return dict
            @auther lkq
            @time 2024-10-10
        '''
        self.check_dir()
        for i in plugin_info:
            slug=i.split("/")[0]
            version=plugin_info[i]["Version"]
            if version == "": continue
            plugin_file = self.wordpress_diff_path + "/plugin/" + slug+"."+version+".zip"
            if not os.path.exists(plugin_file):
                self.download_file_with_progress("https://downloads.wordpress.org/plugin/"+slug+"."+version+".zip", plugin_file,slug)
            else:
                try:
                    zipfile.ZipFile(plugin_file)
                    print("压缩包文件已经存在、且可正常读取文件、正在跳过", plugin_file)
                except:
                    print("The zip file cannot be opened, it is being deleted and re downloaded",slug+"."+version+".zip")
                    os.remove(plugin_file)
                    self.download_file_with_progress("https://downloads.wordpress.org/plugin/"+slug+"."+version+".zip", plugin_file,slug)
        plugin_file_list={}
        #获取所有插件的文件
        for i in plugin_info:
            slug = i.split("/")[0]
            version=plugin_info[i]["Version"]
            if version == "": continue
            plugin_file = self.wordpress_diff_path + "/plugin/" + slug + "." + version + ".zip"
            if not os.path.exists(plugin_file): continue
            plugin_file_list[slug] = {}
            plugin_path=path+"/wp-content/plugins/"+slug
            #判断文件是否存在
            if not os.path.exists(plugin_path): continue
            #遍历目录下所有的PHP文件
            for root, dirs, files in os.walk(plugin_path):
                for file in files:
                    if file.endswith('.php'):
                        file_path = os.path.join(root, file)
                        plugin_file_list[slug][slug+"/"+file_path.replace(plugin_path + "/", "")] = self.FileMd5(file_path)

            #读取压缩包中的文件版本是否和本地的版本一致
            with zipfile.ZipFile(plugin_file, 'r') as zip_file:
                #查找i 的文件
                if i in zip_file.namelist():
                    #读取文件内容
                    with zip_file.open(i) as file:
                        file_data = file.read()
                        # #获取插件信息
                        plugin_data = self.zip_file_plugin_data(file_data.decode("utf-8"), self.plugin_default_headers)
                        if not plugin_data: continue
                        if plugin_data["Name"] == "": continue
                        #判断版本是否一致
                        if plugin_data["Version"]!=version:
                            print("版本不一致、跳过")
                            continue
                #对比MD5
                for file_name in plugin_file_list[slug]:
                    if file_name in zip_file.namelist():
                        with zip_file.open(file_name) as file:
                            file_data = file.read()
                            if self.Md5(file_data)!=plugin_file_list[slug][file_name]:
                                print("文件已经被修改、MD5于云端文件不一致",file_name)
                    else:
                        print("文件异常、原版压缩包中不存在该文件",file_name)

    def check_all_plugin(self,path):
        '''
        @name 检查所有的插件是否被修改过、或者新增了文件
        :param path:
        :return:
        '''
        return self.check_plugin(path,self.get_plugin(path))

    def one_check_plugin(self,path,slug):
        '''
            @name 检查单个插件是否被修改过、或者新增了文件
            @param path WordPress路径
            @return dict
            @auther lkq
            @time 2024-10-10
        '''
        plugin_file_path = path + "/wp-content/plugins/" + slug
        if not os.path.exists(plugin_file_path):
            return []
        #获取所在插件的信息
        plugin_info = self.get_plugin(path,slug)
        if len(plugin_info)==0:
            return []
        self.check_plugin(path, plugin_info)

    def get_vlu_time(self):
        '''
            @name 获取漏洞库更新时间
            @param get:
        :param get:
        :return:
        '''
        date_time=self.M("wordpress_vulnerabilities", "wordpress_vulnerabilities").order("data_time desc").limit("1").field("data_time").find()
        #转为2024-10-10
        if date_time:
            date_time=time.strftime("%Y-%m-%d", time.localtime(date_time["data_time"]))
            return date_time
        else:
            #今天的日期
            return time.strftime("%Y-%m-%d", time.localtime(time.time()))

    def auto_scan(self):
        '''
            @name 自动扫描 每天扫描一次 每个网站延迟1S
        '''
        site_infos=public.M("sites").where("project_type=?",("WP2")).select()
        #如果没有站点的话
        if len(site_infos)==0:
            return
        #自动扫描的配置文件
        wordpress_scan_path="/www/server/panel/data/wordpress_wp_scan.json"
        if not os.path.exists(wordpress_scan_path):
            wordpress_wp_scan={}
        else:
            try:
                wordpress_wp_scan=json.loads(public.ReadFile(wordpress_scan_path))
            except:
                wordpress_wp_scan={}
        for i in site_infos:
            if i["path"] not in wordpress_wp_scan:
                wordpress_wp_scan[i["path"]]={"last_time":0,"vulnerabilities":0,"status":True}
            if not i["status"]:
                continue
            #获取上次扫描的时间
            last_time=wordpress_wp_scan[i["path"]]["last_time"]
            #判断有没有超过一天
            if time.time()-last_time<43200:
                continue
            #获取站点的路径
            path=i["path"]
            time.sleep(1)
            #扫描站点
            try:
                vlun_list=self.scan(path)
            except:
                continue
            wordpress_wp_scan[i["path"]]["last_time"]=int(time.time())
            wordpress_wp_scan[i["path"]]["vulnerabilities"]=len(vlun_list)
        public.WriteFile(wordpress_scan_path,json.dumps(wordpress_wp_scan))

    def set_auth_scan(self,path):
        '''
            @name 停止扫描
            @param path WordPress路径
            @auther lkq
            @time 2024-10-10
            @msg 停止扫描
        '''
        wordpress_scan_path = "/www/server/panel/data/wordpress_wp_scan.json"
        flag=False
        if os.path.exists(wordpress_scan_path):
            try:
                wordpress_scan_info = json.loads(public.readFile(wordpress_scan_path))
            except:
                wordpress_scan_info = {}
        else:
            wordpress_scan_info = {}
        if path in wordpress_scan_info:
            if wordpress_scan_info[path]["status"]:
                wordpress_scan_info[path]["status"]=False
            else:
                wordpress_scan_info[path]["status"]=True
                flag=True
        else:
            wordpress_scan_info[path]={"last_time":0,"vulnerabilities":0,"status":False}

        public.WriteFile(wordpress_scan_path,json.dumps(wordpress_scan_info))

        if flag:
            return public.return_message(0,0,public.lang("Started successfully"))
        return public.return_message(0,0,public.lang("Stopped successfully"))

    def get_auth_scan_status(self,path):
        '''
            @name 获取扫描状态
            @param path WordPress路径
            @auther lkq
            @time 2024-10-10
            @msg 获取扫描状态
        '''
        wordpress_scan_path = "/www/server/panel/data/wordpress_wp_scan.json"
        if os.path.exists(wordpress_scan_path):
            try:
                wordpress_scan_info = json.loads(public.readFile(wordpress_scan_path))
            except:
                wordpress_scan_info = {}
        else:
            wordpress_scan_info = {}
        if path in wordpress_scan_info:
            return public.return_message(0,0,wordpress_scan_info[path]["status"])
        return public.return_message(0,0,True)