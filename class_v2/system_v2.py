#coding: utf-8
# +-------------------------------------------------------------------
# | aapanel x3
# +-------------------------------------------------------------------
# | Copyright (c) 2015-2016 aapanel(http://www.aapanel.com) All rights reserved.
# +-------------------------------------------------------------------
# | Author: hwliang <hwl@bt.cn>
# +-------------------------------------------------------------------
import json

import os
import psutil
import public
import re
# 发布前临时禁用磁盘统计线程模块导入
# import threading
import time

from public.validate import Param

try:
    from BTPanel import session, cache
except:
    pass

# 发布前临时禁用磁盘统计监听状态初始化
# _disk_category_inotify_fd = None
# _disk_category_inotify_thread = None
# _disk_category_inotify_libc = None
# _disk_category_watch_paths = {}
# _disk_category_watch_sites = {}
# _disk_category_watch_roots = {}
# _disk_category_dirty_sites = set()
# _disk_category_inotify_overflow = False
# _disk_category_inotify_lock = threading.RLock()

class system:
    setupPath = None
    ssh = None
    shell = None

    def __init__(self):
        self.setupPath = public.GetConfigValue('setup_path')

    def GetConcifInfo(self,get=None):
        #取环境配置信息
        if 'config' not in session:
            session['config'] = public.M('config').where("id=?",('1',)).field('webserver,sites_path,backup_path,status,mysql_root').find()
        if 'email' not in session['config']:
            session['config']['email'] = public.M('users').where("id=?",('1',)).getField('email')
        data = {}
        data = session['config']
        data['webserver'] = public.get_webserver()
        #PHP版本
        phpVersions = public.get_php_versions()

        data['php'] = []

        for version in phpVersions:
            tmp = {}
            tmp['setup'] = os.path.exists(self.setupPath + '/php/'+version+'/bin/php')
            if tmp['setup']:
                phpConfig = self.GetPHPConfig(version)
                tmp['version'] = version
                tmp['max'] = phpConfig['max']
                tmp['maxTime'] = phpConfig['maxTime']
                tmp['pathinfo'] = phpConfig['pathinfo']
                tmp['status'] = os.path.exists('/tmp/php-cgi-' + version + '.sock')
                data['php'].append(tmp)

        tmp = {}
        data['webserver'] = public.get_webserver()
        serviceName = {
            'nginx': 'nginx',
            'apache': 'httpd',
            'openlitespeed': 'openlitespeed',
        }.get(data['webserver'], 'nginx')
        tmp['setup'] = False
        phpversion = "54"
        phpport = '888'
        pstatus = False
        pauth = False
        if data['webserver'] == 'nginx':
            tmp['setup'] = os.path.exists(self.setupPath +'/nginx/sbin/nginx')
            configFile = self.setupPath + '/nginx/conf/nginx.conf'
            try:
                if os.path.exists(configFile):
                    conf = public.readFile(configFile)
                    rep = r"listen\s+([0-9]+)\s*;"
                    rtmp = re.search(rep,conf)
                    if rtmp:
                        phpport = rtmp.groups()[0]

                    if conf.find('AUTH_START') != -1: pauth = True
                    if conf.find(self.setupPath + '/stop') == -1: pstatus = True
                    configFile = self.setupPath + '/nginx/conf/enable-php.conf'
                    conf = public.readFile(configFile)
                    rep = r"php-cgi-([0-9]+)\.sock"
                    rtmp = re.search(rep,conf)
                    if rtmp:
                        phpversion = rtmp.groups()[0]
            except:
                pass

        elif data['webserver'] == 'apache':
            tmp['setup'] = os.path.exists(self.setupPath +'/apache/bin/httpd')
            configFile = self.setupPath + '/apache/conf/extra/httpd-vhosts.conf'
            try:
                if os.path.exists(configFile):
                    conf = public.readFile(configFile)
                    rep = r"php-cgi-([0-9]+)\.sock"
                    rtmp = re.search(rep,conf)
                    if rtmp:
                        phpversion = rtmp.groups()[0]
                    rep = "Listen\\s+([0-9]+)\\s*\n"
                    rtmp = re.search(rep,conf)
                    if rtmp:
                        phpport = rtmp.groups()[0]
                    if conf.find('AUTH_START') != -1: pauth = True
                    if conf.find(self.setupPath + '/stop') == -1: pstatus = True
            except:
                pass
        elif data['webserver'] == 'openlitespeed':
            tmp['setup'] = os.path.exists('/usr/local/lsws/bin/lswsctrl')
            configFile = '/usr/local/lsws/bin/lswsctrl'
            try:
                if os.path.exists(configFile):
                    conf = public.readFile('/www/server/panel/vhost/openlitespeed/detail/phpmyadmin.conf')
                    rep = r"/usr/local/lsws/lsphp(\d+)/bin/lsphp"
                    rtmp = re.search(rep,conf)
                    if rtmp:
                        phpversion = rtmp.groups()[0]
                    conf = public.readFile('/www/server/panel/vhost/openlitespeed/listen/888.conf')
                    rep = r"address\s+\*\:(\d+)"
                    rtmp = re.search(rep,conf)
                    if rtmp:
                        phpport = rtmp.groups()[0]
                    if conf.find('AUTH_START') != -1: pauth = True
                    if conf.find(self.setupPath + '/stop') == -1: pstatus = True
            except:
                pass


        tmp['type'] = data['webserver']
        version_file = self.setupPath + '/' + data['webserver'] + '/version.pl'
        if data['webserver'] == 'openlitespeed':
            version_file = '/usr/local/lsws/VERSION'
        tmp['version'] = public.xss_version(public.readFile(version_file))
        tmp['status'] = False
        if serviceName=="nginx":
            mPID=public.readFile("/www/server/nginx/logs/nginx.pid")
            if mPID:
                isStart="ps ax | awk '{ print $1 }' | grep -e \"^"+mPID+"$\""
                result = public.ExecShell(isStart)[0]
                if "running" in result:
                    tmp['status'] = True
        else:
            result=public.ExecShell("/etc/init.d/"+serviceName+" status")[0]
            if result.find('running') != -1: tmp['status'] = True
        data['web'] = tmp

        tmp = {}
        vfile = self.setupPath + '/phpmyadmin/version.pl'
        tmp['version'] = public.xss_version(public.readFile(vfile))
        if tmp['version']: tmp['version'] = tmp['version'].strip()
        tmp['setup'] = os.path.exists(vfile)
        tmp['status'] = pstatus
        tmp['phpversion'] = phpversion.strip()
        tmp['port'] = phpport
        tmp['auth'] = pauth
        data['phpmyadmin'] = tmp

        tmp = {}
        tmp['setup'] = os.path.exists('/etc/init.d/tomcat')
        tmp['status'] = tmp['setup']
        #if public.ExecShell('ps -aux|grep tomcat|grep -v grep')[0] == "": tmp['status'] = False
        tmp['version'] = public.xss_version(public.readFile(self.setupPath + '/tomcat/version.pl'))
        data['tomcat'] = tmp

        tmp = {}
        tmp['setup'] = os.path.exists(self.setupPath +'/mysql/bin/mysql')
        tmp['version'] = public.xss_version(public.readFile(self.setupPath + '/mysql/version.pl'))
        tmp['status'] = os.path.exists('/tmp/mysql.sock')
        data['mysql'] = tmp

        tmp = {}
        tmp['setup'] = os.path.exists(self.setupPath +'/mongodb/bin/mongod')
        tmp['version'] = public.xss_version(public.readFile(self.setupPath + '/mongodb/version.pl'))
        tmp['status'] = os.path.exists('/www/server/mongodb/log/configsvr.pid')
        data['mongodb'] = tmp

        tmp = {}
        tmp['pgsql_manager_setup'] = os.path.exists('/www/server/panel/plugin/pgsql_manager')
        tmp['setup'] = os.path.exists(self.setupPath +'/pgsql/bin/psql')
        tmp['version'] = public.xss_version(public.readFile(self.setupPath + '/pgsql/data/PG_VERSION'))
        tmp['status'] = os.path.exists('/www/server/pgsql/data/postmaster.pid')
        data['pgsql'] = tmp

        tmp = {}
        tmp['setup'] = os.path.exists(self.setupPath +'/redis/runtest')
        tmp['status'] = os.path.exists('/var/run/redis_6379.pid')
        data['redis'] = tmp

        tmp = {}
        tmp['setup'] = os.path.exists('/usr/local/memcached/bin/memcached')
        tmp['status'] = os.path.exists('/var/run/memcached.pid')
        data['memcached'] = tmp

        tmp = {}
        tmp['setup'] = os.path.exists(self.setupPath +'/pure-ftpd/bin/pure-pw')
        tmp['version'] = public.xss_version(public.readFile(self.setupPath + '/pure-ftpd/version.pl'))
        tmp['status'] = os.path.exists('/var/run/pure-ftpd.pid')
        data['pure-ftpd'] = tmp
        data['panel'] = self.GetPanelInfo()
        data['systemdate'] = public.ExecShell('date +"%Y-%m-%d %H:%M:%S %Z %z"')[0].strip();
        data['show_workorder'] = not os.path.exists('data/not_workorder.pl')
        return data

    def GetPanelInfo(self,get=None):
        #取面板配置
        address = public.GetLocalIp()
        try:
            port = public.GetHost(True)
        except:
            port = '7800'
        domain = ''
        if os.path.exists('data/domain.conf'):
           domain = public.readFile('data/domain.conf')

        try:
            listen_port = public.readFile('data/port.pl')
            if int(listen_port) <= 0: listen_port = '7800'
        except:
            listen_port = '7800'
        autoUpdate = ''
        if os.path.exists('data/autoUpdate.pl'): autoUpdate = 'checked';
        limitip = ''
        if os.path.exists('data/limitip.conf'): limitip = public.readFile('data/limitip.conf');
        admin_path = '/'
        if os.path.exists('data/admin_path.pl'): admin_path = public.readFile('data/admin_path.pl').strip()
        # 取面板访问限制地区
        limitarea = {"allow": [], "deny": []}
        if os.path.exists('data/limit_area.json'):
            try:
                limitarea = json.loads(public.readFile('data/limit_area.json'))
            except:
                limitarea = {"allow": [], "deny": []}
        limitarea_status = 'false'
        if os.path.exists('data/limit_area.pl'): limitarea_status = 'true'

        templates = []
        #for template in os.listdir('BTPanel/templates/'):
        #    if os.path.isdir('templates/' + template): templates.append(template);
        template = public.GetConfigValue('template')

        check502 = ''
        if os.path.exists('data/502Task.pl'): check502 = 'checked';

        # 版本ver
        if os.path.exists('data/is_beta.pl'):
            version_type = 'Beta'
        elif os.path.exists('data/panel_pro.pl'):
            version_type = 'PRO'
        else: # 正式版
            version_type = ''
        return {'port': port,'listen_port':listen_port, 'address': address, 'domain': domain, 'auto': autoUpdate, '502': check502, 'limitip': limitip, 'limitarea_status': limitarea_status, 'limitarea': limitarea,
                'templates': templates, 'template': template, 'admin_path': admin_path, 'version_type': version_type}


    def GetPHPConfig(self,version):
        #取PHP配置
        file = self.setupPath + "/php/"+version+"/etc/php.ini"
        phpini = public.readFile(file)
        file = self.setupPath + "/php/"+version+"/etc/php-fpm.conf"
        phpfpm = public.readFile(file)
        data = {}
        try:
            rep = r"upload_max_filesize\s*=\s*([0-9]+)M"
            tmp = re.search(rep,phpini).groups()
            data['max'] = tmp[0]
        except:
            data['max'] = '50'
        try:
            rep = "request_terminate_timeout\\s*=\\s*([0-9]+)\n"
            tmp = re.search(rep,phpfpm).groups()
            data['maxTime'] = tmp[0]
        except:
            data['maxTime'] = 0

        try:
            rep = r"\n;*\s*cgi\.fix_pathinfo\s*=\s*([0-9]+)\s*\n"
            tmp = re.search(rep,phpini).groups()

            if tmp[0] == '1':
                data['pathinfo'] = True
            else:
                data['pathinfo'] = False
        except:
            data['pathinfo'] = False

        return data


    def GetSystemTotal(self,get,interval = 1):
        #取系统统计信息
        data = self.GetMemInfo()['message']
        cpu = self.GetCpuInfo(interval)
        data['cpuNum'] = cpu[1]
        data['cpuRealUsed'] = cpu[0]
        data['time'] = self.GetBootTime()
        data['system'] = self.GetSystemVersion()
        data['isuser'] = public.M('users').where('username=?',('admin',)).count()
        try:
            data['isport'] = public.GetHost(True) == '8888'
        except:data['isport'] = False

        data['version'] = session['version']
        return public.return_message(0,0,data)

    def GetLoadAverage(self,get):
        try:
            c = os.getloadavg()
        except:
            c = [0,0,0]
        data = {}
        data['one'] = float(c[0])
        data['five'] = float(c[1])
        data['fifteen'] = float(c[2])
        data['max'] = psutil.cpu_count() * 2
        data['limit'] = data['max']
        data['safe'] = data['max'] * 0.75
        return data

    def GetAllInfo(self,get):
        data = {}
        data['load_average'] = self.GetLoadAverage(get)
        data['title'] = self.GetTitle()
        data['network'] = self.GetNetWorkApi(get)
        data['cpu'] = self.GetCpuInfo(1)
        data['time'] = self.GetBootTime()
        data['system'] = self.GetSystemVersion()
        data['mem'] = self.GetMemInfo()['message']
        data['version'] = session['version']
        return data

    def GetTitle(self):
        return public.xss_version(public.GetConfigValue('title'))

    def GetSystemVersion(self):
        #取操作系统版本
        key = 'sys_version'
        version = cache.get(key)
        if version: return version
        version = public.get_os_version()
        cache.set(key,version,600)
        return version

    def GetBootTime(self):
        #取系统启动时间
        key = 'sys_time'
        sys_time = cache.get(key)
        if sys_time: return sys_time
        import public,math
        conf = public.readFile('/proc/uptime').split()
        tStr = float(conf[0])
        min = tStr / 60
        hours = min / 60
        days = math.floor(hours / 24)
        hours = math.floor(hours - (days * 24))
        min = math.floor(min - (days * 60 * 24) - (hours * 60))
        # sys_time = "{} Day(s)".format(int(days))
        sys_time = public.lang("{} Day(s)", int(days))
        cache.set(key,sys_time,1800)
        return sys_time
        #return public.getMsg('SYS_BOOT_TIME',(str(int(days)),str(int(hours)),str(int(min))))

    def GetCpuInfo(self,interval = 1):
        #取CPU信息
        cpuCount = psutil.cpu_count()
        cpuNum = psutil.cpu_count(logical=False)
        c_tmp = public.readFile('/proc/cpuinfo')
        d_tmp = re.findall("physical id.+",c_tmp)
        cpuW = len(set(d_tmp))
        used = cache.get('cpu_used_all')
        if used is None:
            used = self.get_cpu_percent_thead(interval)
        else:
            import threading
            p = threading.Thread(target=self.get_cpu_percent_thead,args=(interval,))
            p.daemon = True
            p.start()

        used_all = psutil.cpu_percent(percpu=True)
        cpu_name = public.getCpuType() + " * {}".format(cpuW)

        return used,cpuCount,used_all,cpu_name,cpuNum,cpuW

    def get_cpu_percent_thead(self,interval):
        used = psutil.cpu_percent(interval)
        cache.set('cpu_used_all',used,10)
        return used


    def get_cpu_percent(self):
        percent = 0.00
        old_cpu_time = cache.get('old_cpu_time')
        old_process_time = cache.get('old_process_time')
        if not old_cpu_time:
            old_cpu_time = self.get_cpu_time()
            old_process_time = self.get_process_cpu_time()
            time.sleep(1)
        new_cpu_time = self.get_cpu_time()
        new_process_time = self.get_process_cpu_time()
        try:
            percent = round(100.00 * ((new_process_time - old_process_time) / (new_cpu_time - old_cpu_time)),2)
        except: percent = 0.00
        cache.set('old_cpu_time',new_cpu_time)
        cache.set('old_process_time',new_process_time)
        if percent > 100: percent = 100
        if percent > 0: return percent
        return 0.00

    def get_process_cpu_time(self):
        pids = psutil.pids()
        cpu_time = 0.00
        for pid in pids:
            try:
                cpu_times = psutil.Process(pid).cpu_times()
                for s in cpu_times: cpu_time += s
            except:continue
        return cpu_time

    def get_cpu_time(self):
        cpu_time = 0.00
        cpu_times = psutil.cpu_times()
        for s in cpu_times: cpu_time += s
        return cpu_time

    def GetMemInfo(self,get=None):
        #取内存信息
        skey = 'memInfo'
        memInfo = cache.get(skey)
        if memInfo: return public.return_message(0,0,memInfo)
        mem = psutil.virtual_memory()
        memInfo = {'memTotal':int(mem.total/1024/1024),'memFree':int(mem.free/1024/1024),'memBuffers':int(mem.buffers/1024/1024),'memCached':int(mem.cached/1024/1024)}
        memInfo['memRealUsed'] = memInfo['memTotal'] - memInfo['memFree'] - memInfo['memBuffers'] - memInfo['memCached']
        cache.set(skey,memInfo,60)
        return public.return_message(0,0,memInfo)

    def GetDiskInfo(self,get=None):
        return self.GetDiskInfo2()
        #取磁盘分区信息
        diskIo = psutil.disk_partitions()
        diskInfo = []
        cuts = ['/mnt/cdrom','/boot','/boot/efi','/dev','/dev/shm','/run/lock','/run','/run/shm','/run/user']
        for disk in diskIo:
            if not cuts: continue
            tmp = {}
            tmp['path'] = disk[1]
            tmp['size'] = psutil.disk_usage(disk[1])
            diskInfo.append(tmp)
        return diskInfo

    def GetDiskInfo2(self, human=True):

        #取磁盘分区信息
        key = f'sys_disk_{human}'
        diskInfo = cache.get(key)
        if diskInfo: return diskInfo
        if human:
            temp = public.ExecShell("df -hT -P|grep '/'|grep -v tmpfs|grep -v 'snap/core'|grep -v udev")[0]
        else:
            temp = public.ExecShell("df -T -P|grep '/'|grep -v tmpfs|grep -v 'snap/core'|grep -v udev")[0]
        tempInodes = public.ExecShell("df -i -P|grep '/'|grep -v tmpfs|grep -v 'snap/core'|grep -v udev")[0]
        temp1 = temp.split('\n')
        tempInodes1 = tempInodes.split('\n')
        diskInfo = []
        n = 0
        cuts = ['/mnt/cdrom','/boot','/boot/efi','/dev','/dev/shm','/run/lock','/run','/run/shm','/run/user']
        for tmp in temp1:
            n += 1
            try:
                inodes = tempInodes1[n-1].split()
                disk = re.findall(r"^(.+)\s+([\w\.]+)\s+([\w\.]+)\s+([\w\.]+)\s+([\w\.]+)\s+([\d%]{2,4})\s+(/.{0,100})$",tmp.strip().replace(',','.'))
                if disk: disk = disk[0]
                if len(disk) < 6: continue
                # if disk[2].find('M') != -1: continue
                if disk[2].find('K') != -1: continue
                if len(disk[6].split('/')) > 10: continue
                if disk[6] in cuts: continue
                if str(disk[6]).startswith("/snap"): continue
                if disk[6].find('docker') != -1: continue
                if disk[1].strip() in ['tmpfs']: continue
                arr = {}
                arr['filesystem'] = disk[0].strip()
                arr['type'] = disk[1].strip()
                arr['path'] = disk[6].replace('/usr/local/lighthouse/softwares/btpanel','/www')
                tmp1 = [disk[2],disk[3],disk[4],disk[5]]
                arr['size'] = tmp1
                arr['inodes'] = [inodes[1],inodes[2],inodes[3],inodes[4]]
                diskInfo.append(arr)
            except Exception as ex:
                public.write_log_gettext('Get Info',str(ex))
                continue
        cache.set(key,diskInfo,10)
        return diskInfo

    # 发布前临时禁用磁盘分类统计实现，后续上线时恢复下方代码
    # # 收集四个磁盘分类对应的原始目录列表，供 unit 生成和刷新流程使用
    # def _get_disk_category_paths(self):
    #     # 初始化项目文件、数据库、备份和系统日志四类目录
    #     path_info = {
    #         'project_files_size': [],
    #         'databases_size': [],
    #         'backups_size': [],
    #         'system_logs_size': ['/www/wwwlogs','/www/server/panel/logs','/var/log']
    #     }

    #     # 从 sites 表读取所有网站根目录
    #     try:
    #         sites = public.M('sites').field('path').select()
    #         for site in sites:
    #             if site.get('path'): path_info['project_files_size'].append(site['path'])
    #     except:
    #         pass

    #     # 没有网站记录时使用面板提供的默认网站目录作为兜底
    #     if not path_info['project_files_size']:
    #         try:
    #             path_info['project_files_size'].append(public.get_site_path())
    #         except:
    #             pass

    #     # 读取数据库服务实际使用的数据目录
    #     try:
    #         path_info['databases_size'] += self._get_database_data_paths()
    #     except:
    #         pass

    #     # 读取备份根目录，读取失败时使用默认路径
    #     try:
    #         path_info['backups_size'].append(public.get_backup_path())
    #     except:
    #         path_info['backups_size'].append('/www/backup')

    #     return path_info

    # # 返回接口使用的四个分类字段名称
    # def _get_disk_category_fields(self):
    #     return ('project_files_size','databases_size','backups_size','system_logs_size')

    # # 按分类目录生成不重叠的统计单元；父目录覆盖子目录时只保留父单元
    # def _get_disk_category_units(self,path_info=None):
    #     path_info = path_info if isinstance(path_info,dict) else self._get_disk_category_paths()
    #     candidates = []
    #     for order,category in enumerate(self._get_disk_category_fields()):
    #         for path in path_info.get(category,[]):
    #             path = self._format_disk_path(path)
    #             if path and os.path.exists(path):
    #                 candidates.append((len(path.rstrip('/')),order,path,category))
    #     result = []
    #     for _,_,path,category in sorted(set(candidates)):
    #         if any(self._is_path_in_mount(path,current['unit_path']) for current in result): continue
    #         result.append({'category': category,'unit_path': path})
    #     return result


    # # 将输入路径统一转换为绝对、真实、正斜杠格式
    # def _format_disk_path(self,path):
    #     try:
    #         path = str(path).strip()
    #         if not path: return ''
    #         return os.path.abspath(os.path.realpath(path)).replace('\\','/')
    #     except:
    #         return ''

    # # 判断一个路径是否位于指定挂载点或统计单元目录之下
    # def _is_path_in_mount(self,path,mount_path):
    #     path = self._format_disk_path(path)
    #     mount_path = self._format_disk_path(mount_path)
    #     if not path or not mount_path: return False
    #     if mount_path == '/': return path.startswith('/')
    #     mount_path = mount_path.rstrip('/')
    #     return path == mount_path or path.startswith(mount_path + '/')

    # # 按挂载点列表找到路径实际归属的挂载点
    # def _get_path_mount(self,path,mount_paths):
    #     for mount_path in mount_paths:
    #         if self._is_path_in_mount(path,mount_path): return mount_path
    #     return None

    # # 在调用方已保证路径规范化时执行快速归属判断，避免热循环重复 realpath
    # def _is_formatted_path_in_mount(self,path,mount_path):
    #     if not path or not mount_path: return False
    #     if mount_path == '/': return str(path).startswith('/')
    #     mount_path = str(mount_path).rstrip('/')
    #     return path == mount_path or str(path).startswith(mount_path + '/')

    # # 在调用方已保证路径规范化时快速查找挂载点
    # def _get_formatted_path_mount(self,path,mount_paths):
    #     for mount_path in mount_paths:
    #         if self._is_formatted_path_in_mount(path,mount_path): return mount_path
    #     return None

    # # 清理数据库配置文件中的注释、引号和相对路径
    # def _format_database_config_path(self,path,base_path=''):
    #     try:
    #         path = str(path).strip().strip('"\'')
    #         if not path: return ''
    #         path = re.split(r'\s+#|\s+;',path,1)[0].strip().strip('"\'')
    #         if not path: return ''
    #         if base_path and not os.path.isabs(path): path = os.path.join(base_path,path)
    #         return path
    #     except:
    #         return ''

    # # 获取 MySQL 或 MariaDB 的数据目录
    # def _get_mysql_data_paths(self):
    #     paths = []
    #     try:
    #         datadir = public.get_mysql_info().get('datadir','')
    #         datadir = self._format_database_config_path(datadir)
    #         if datadir: paths.append(datadir)
    #     except:
    #         pass
    #     if not paths: paths.append('/www/server/data')
    #     return paths

    # # 获取 PostgreSQL 的数据目录配置
    # def _get_pgsql_data_paths(self):
    #     paths = []
    #     try:
    #         data_directory_file = os.path.join(public.get_setup_path(),'pgsql/data_directory')
    #         if os.path.isfile(data_directory_file):
    #             data_directory = public.readFile(data_directory_file)
    #             data_directory = self._format_database_config_path(data_directory)
    #             if data_directory: paths.append(data_directory)
    #         else:
    #             paths.append(os.path.join(public.get_setup_path(),'pgsql/data'))
    #     except:
    #         pass
    #     return paths

    # # 从 MongoDB 配置文件解析 storage.dbPath
    # def _get_mongodb_data_paths(self):
    #     paths = []
    #     try:
    #         config_file = os.path.join(public.get_setup_path(),'mongodb/config.conf')
    #         if not os.path.exists(config_file): return paths
    #         conf = public.readFile(config_file)
    #         try:
    #             import yaml
    #             config = yaml.safe_load(conf)
    #             if isinstance(config,dict):
    #                 storage = config.get('storage',{})
    #                 if isinstance(storage,dict) and storage.get('dbPath'):
    #                     db_path = self._format_database_config_path(storage['dbPath'],os.path.dirname(config_file))
    #                     if db_path: paths.append(db_path)
    #         except:
    #             tmp = re.findall(r'(?m)^\s*(?:dbPath|dbpath)\s*:\s*(.+)$',conf)
    #             if tmp:
    #                 db_path = self._format_database_config_path(tmp[0],os.path.dirname(config_file))
    #                 if db_path: paths.append(db_path)
    #         if not paths:
    #             tmp = re.findall(r'(?m)^\s*dbpath\s*=\s*(.+)$',conf)
    #             if tmp:
    #                 db_path = self._format_database_config_path(tmp[0],os.path.dirname(config_file))
    #                 if db_path: paths.append(db_path)
    #     except:
    #         pass
    #     return paths

    # # 从 Redis 配置文件解析持久化目录
    # def _get_redis_data_paths(self):
    #     paths = []
    #     try:
    #         config_file = os.path.join(public.get_setup_path(),'redis/redis.conf')
    #         if not os.path.exists(config_file): return paths
    #         conf = public.readFile(config_file)
    #         tmp = re.findall(r'(?m)^\s*dir\s+(.+)$',conf)
    #         if tmp:
    #             redis_dir = self._format_database_config_path(tmp[-1],os.path.dirname(config_file))
    #             if redis_dir: paths.append(redis_dir)
    #     except:
    #         pass
    #     return paths

    # # 汇总 MySQL、PostgreSQL、MongoDB 和 Redis 的数据目录
    # def _get_database_data_paths(self):
    #     paths = []
    #     for get_paths in (
    #         self._get_mysql_data_paths,
    #         self._get_pgsql_data_paths,
    #         self._get_mongodb_data_paths,
    #         self._get_redis_data_paths,
    #     ):
    #         try:
    #             paths += get_paths()
    #         except:
    #             pass
    #     return paths

    # # 获取对外磁盘分类统计 JSON 文件路径
    # def _get_disk_category_result_path(self):
    #     return os.path.join(public.get_panel_path(),'data/disk_category_stats.json')

    # # 读取磁盘分类统计总开关；配置不存在时默认开启
    # def is_disk_category_stats_enabled(self):
    #     try:
    #         value = public.get_config_value('disk_category_stats','enabled',1)
    #         if isinstance(value,str):
    #             return value.strip().lower() not in ('0','false','off','no')
    #         return bool(value)
    #     except:
    #         return True

    # # 获取刷新任务使用的互斥锁文件路径
    # def _get_disk_category_lock_path(self):
    #     return os.path.join(public.get_panel_path(),'data/disk_category_stats.lock')

    # # 获取旧版 dirty JSON journal 的兼容路径
    # def _get_disk_category_dirty_path(self):
    #     return os.path.join(public.get_panel_path(),'data/disk_category_dirty.json')

    # # 获取长期运行 watcher 的进程状态文件路径
    # def _get_disk_category_watcher_state_path(self):
    #     return os.path.join(public.get_panel_path(),'data/disk_category_watcher.state')

    # # 使用独立 SQLite 连接执行查询，返回查询结果
    # def _disk_category_db_query(self,sql,params=()):
    #     with public.SqliteConn('default') as db:
    #         return db.query().query(sql,params)

    # # 使用独立 SQLite 连接执行单条写操作，失败时返回 0
    # def _disk_category_db_execute(self,sql,params=()):
    #     try:
    #         with public.SqliteConn('default') as db:
    #             return db.query().execute(sql,params)
    #     except:
    #         return 0

    # # 将 inotify 位掩码和 rename cookie 编码成可持久化字符串
    # def _disk_category_encode_event_type(self,mask,cookie):
    #     names = ((0x2,'MODIFY'),(0x4,'ATTRIB'),(0x8,'CLOSE_WRITE'),(0x100,'CREATE'),
    #              (0x200,'DELETE'),(0x40,'MOVED_FROM'),(0x80,'MOVED_TO'))
    #     name = next((value for bit,value in names if int(mask) & bit),'UNKNOWN')
    #     return '{}|{}|{}'.format(name,int(mask),int(cookie or 0))

    # # 将分类 unit 总量、目录 bucket 和稀疏文件缓存批量写入 SQLite
    # def _save_disk_category_project_state(self,buckets,file_caches,category='project_files_size'):
    #     now = int(time.time() * 1000000000)
    #     with public.SqliteConn('default') as db:
    #         db.autocommit(False)
    #         db.query().execute('DELETE FROM `disk_category_stats` WHERE `category`=?',(category,))
    #         for mount_buckets in buckets.values():
    #             for path,size in mount_buckets.items():
    #                 db.query().execute(
    #                     'INSERT OR REPLACE INTO `disk_category_stats` (`category`,`unit_path`,`size`,`initialized`,`updated_at`) VALUES (?,?,?,?,?)',
    #                     (category,path,max(0,int(size)),1,now))
    #         db.query().execute('DELETE FROM `disk_category_file_cache` WHERE `category`=?',(category,))
    #         sorted_sites = {
    #             mount_path: sorted(buckets.get(mount_path,{}),key=len,reverse=True)
    #             for mount_path in buckets
    #         }
    #         file_rows = []
    #         for mount_path,mount_cache in file_caches.items():
    #             sites = sorted_sites.get(mount_path,())
    #             for path,meta in mount_cache.items():
    #                 unit_path = next((site for site in sites
    #                                   if self._is_formatted_path_in_mount(path,site)),'')
    #                 if not unit_path: continue
    #                 file_rows.append((path,category,unit_path,int(meta.get('size',0)),int(meta.get('dev',0)),
    #                                   int(meta.get('ino',0)),int(meta.get('mtime_ns',0)),now))
    #         for index in range(0,len(file_rows),100):
    #             chunk = file_rows[index:index + 100]
    #             values_sql = ','.join(['(?,?,?,?,?,?,?,?)'] * len(chunk))
    #             params = []
    #             for row in chunk: params.extend(row)
    #             db.query().execute(
    #                 'INSERT OR REPLACE INTO `disk_category_file_cache` (`path`,`category`,`unit_path`,`size`,`dev`,`inode`,`mtime_ns`,`updated_at`) VALUES ' + values_sql,
    #                 tuple(params))
    #         db.commit()

    # # 从持久化的事件字段恢复 inotify 位掩码和 rename cookie
    # def _disk_category_decode_event_type(self,value):
    #     try:
    #         name,mask,cookie = str(value).split('|',2)
    #         return int(mask),int(cookie)
    #     except:
    #         return 0,0

    # # 将不同格式的 unit 输入规范化为分类和真实路径二元组
    # def _normalize_disk_category_unit(self,value):
    #     if isinstance(value,dict):
    #         category,path = value.get('category'),value.get('unit_path')
    #     elif isinstance(value,(tuple,list)) and len(value) == 2:
    #         category,path = value
    #     else:
    #         category,path = 'project_files_size',value
    #     return category,self._format_disk_path(path)

    # # 在当前事务中插入或更新一个 dirty 标记
    # def _upsert_disk_category_dirty_marker(self,db,category,unit_path,path,event_type,now):
    #     db.query().execute(
    #         'INSERT OR IGNORE INTO `disk_category_dirty` (`category`,`unit_path`,`path`,`event_type`,`created_at`,`updated_at`) VALUES (?,?,?,?,?,?)',
    #         (category,unit_path,path,event_type,now,now))
    #     db.query().execute(
    #         'UPDATE `disk_category_dirty` SET `event_type`=?,`updated_at`=? WHERE `category`=? AND `unit_path`=? AND `path`=?',
    #         (event_type,now,category,unit_path,path))

    # # 校验磁盘分类 JSON 是否完整、格式正确且覆盖当前磁盘
    # def is_disk_category_stats_valid(self,disk_info=None):
    #     try:
    #         result_file = self._get_disk_category_result_path()
    #         if not os.path.exists(result_file): return False
    #         result = json.loads(public.readFile(result_file))
    #         if not isinstance(result,dict) or not result: return False
    #         fields = ('project_files_size','databases_size','backups_size','system_logs_size','other_files_size')
    #         for mount_path,disk_stats in result.items():
    #             if not isinstance(mount_path,str) or not mount_path or not isinstance(disk_stats,dict): return False
    #             for field in fields:
    #                 value = disk_stats.get(field)
    #                 if not isinstance(value,int) or isinstance(value,bool) or value < 0: return False
    #             updated_at = disk_stats.get('updated_at')
    #             if not isinstance(updated_at,str) or not updated_at: return False
    #             parsed_time = time.strptime(updated_at,'%Y-%m-%d %H:%M:%S')
    #             if time.strftime('%Y-%m-%d %H:%M:%S',parsed_time) != updated_at: return False
    #         if disk_info is None: disk_info = self.GetDiskInfo2(False)
    #         if not disk_info: return False
    #         for disk in disk_info:
    #             mount_path = disk.get('path')
    #             if mount_path and mount_path not in result: return False
    #         return True
    #     except:
    #         return False

    # # 为当前磁盘列表创建四分类和 Other Files 的默认结果
    # def _get_disk_category_default_stats(self,disk_info):
    #     stats = {}
    #     updated_at = time.strftime('%Y-%m-%d %H:%M:%S',time.localtime())
    #     for disk in disk_info:
    #         mount_path = disk.get('path')
    #         if not mount_path: continue
    #         stats[mount_path] = {
    #             'project_files_size': 0,
    #             'databases_size': 0,
    #             'backups_size': 0,
    #             'system_logs_size': 0,
    #             'other_files_size': 0,
    #             'updated_at': updated_at
    #         }
    #     return stats

    # # 读取有效的 JSON 结果，并补齐当前磁盘缺少的默认字段
    # def _read_disk_category_stats(self,disk_info):
    #     try:
    #         result_file = self._get_disk_category_result_path()
    #         result = json.loads(public.readFile(result_file)) if self.is_disk_category_stats_valid(disk_info) else {}
    #     except:
    #         result = {}

    #     stats = self._get_disk_category_default_stats(disk_info)
    #     for mount_path in stats:
    #         current = result.get(mount_path,{})
    #         if not isinstance(current,dict): current = {}
    #         for field in ('project_files_size','databases_size','backups_size','system_logs_size','other_files_size'):
    #             if field not in current: continue
    #             try:
    #                 stats[mount_path][field] = max(0,int(current.get(field,0)))
    #             except:
    #                 pass
    #         if isinstance(current.get('updated_at'),str) and current.get('updated_at'):
    #             stats[mount_path]['updated_at'] = current['updated_at']
    #     return stats

    # # 在内存集合和 SQLite 中标记发生变化、需要重新统计的分类单元
    # def _mark_disk_category_dirty(self,site_path,category='project_files_size'):
    #     if site_path and category in self._get_disk_category_fields():
    #         site_path = self._format_disk_path(site_path)
    #         with _disk_category_inotify_lock:
    #             _disk_category_dirty_sites.add((category,site_path))
    #         self._update_disk_category_dirty_file([(category,site_path)])

    # # 兼容旧版网站列表，并规范化为带事件明细的 dirty journal
    # # 将旧版 dirty JSON 或新版结构统一转换为标准事件 journal
    # def _normalize_disk_category_dirty_state(self,value):
    #     state = {'version': 2,'force_full': False,'sites': {}}
    #     if isinstance(value,list):
    #         for site_path in value:
    #             site_path = self._format_disk_path(site_path)
    #             if site_path:
    #                 state['sites'][site_path] = {'force_site': True,'events': []}
    #         return state
    #     if not isinstance(value,dict): return state
    #     state['force_full'] = bool(value.get('force_full',False))
    #     sites = value.get('sites',{})
    #     if not isinstance(sites,dict): return state
    #     for site_path,payload in sites.items():
    #         site_path = self._format_disk_path(site_path)
    #         if not site_path: continue
    #         payload = payload if isinstance(payload,dict) else {}
    #         events = payload.get('events',[])
    #         state['sites'][site_path] = {
    #             'force_site': bool(payload.get('force_site',False)),
    #             'events': [event for event in events if isinstance(event,dict)] if isinstance(events,list) else []
    #         }
    #     return state

    # # 持久化 dirty unit 和文件事件，供后续刷新进程读取
    # def _update_disk_category_dirty_file(self,site_paths=None,remove_paths=None,events=None,force_full=False,categories=None):
    #     try:
    #         # 过滤允许的分类，并为本批写入生成统一时间戳
    #         now = int(time.time() * 1000000000)
    #         valid_categories = self._get_disk_category_fields()
    #         categories = tuple(category for category in (categories or valid_categories)
    #                            if category in valid_categories)
    #         with public.SqliteConn('default') as db:
    #             db.autocommit(False)
    #             # 用特殊的 unit_path/path 标记要求整个分类全量重建
    #             if force_full:
    #                 for category in categories:
    #                     self._upsert_disk_category_dirty_marker(
    #                         db,category,'*','*','FORCE_FULL',now)
    #             # 写入需要重新扫描整个统计 unit 的 FORCE_SITE 标记
    #             for value in (site_paths or []):
    #                 category,path = value if isinstance(value,(tuple,list)) and len(value) == 2 else ('project_files_size',value)
    #                 path = self._format_disk_path(path)
    #                 if category not in valid_categories or not path: continue
    #                 self._upsert_disk_category_dirty_marker(
    #                     db,category,path,'','FORCE_SITE',now)
    #             db.commit()
    #         # 普通 inotify 事件单独在一个批量事务中合并写入
    #         event_values = [event for event in (events or []) if isinstance(event,dict)]
    #         if event_values:
    #             with public.SqliteConn('default') as db:
    #                 db.autocommit(False)
    #                 # 同一 category、unit 和 path 只保留一行，并合并事件掩码
    #                 for event in event_values:
    #                     category = event.get('category','project_files_size')
    #                     site_path = self._format_disk_path(event.get('site'))
    #                     event_path = self._format_disk_path(event.get('path'))
    #                     if category not in valid_categories or not site_path or not event_path: continue
    #                     mask = int(event.get('mask',0))
    #                     cookie = int(event.get('cookie',0))
    #                     event_type = self._disk_category_encode_event_type(mask,cookie)
    #                     incoming_old_path = self._format_disk_path(event.get('old_path')) if event.get('old_path') else ''
    #                     row = db.query().query(
    #                         'SELECT `id`,`event_type`,`created_at`,`old_path` FROM `disk_category_dirty` WHERE `category`=? AND `unit_path`=? AND `path`=?',
    #                         (category,site_path,event_path),True)
    #                     created_at = now
    #                     old_path = incoming_old_path
    #                     if row:
    #                         previous_mask,previous_cookie = self._disk_category_decode_event_type(row['event_type'])
    #                         if previous_mask and (previous_mask & ~(0x2 | 0x4 | 0x8)):
    #                             mask |= previous_mask
    #                         if not cookie: cookie = previous_cookie
    #                         event_type = self._disk_category_encode_event_type(mask,cookie)
    #                         created_at = row.get('created_at') or now
    #                         old_path = row.get('old_path') or ''
    #                     db.query().execute(
    #                         'INSERT OR IGNORE INTO `disk_category_dirty` (`category`,`unit_path`,`path`,`old_path`,`event_type`,`is_dir`,`created_at`,`updated_at`) VALUES (?,?,?,?,?,?,?,?)',
    #                         (category,site_path,event_path,old_path,event_type,int(bool(event.get('is_dir'))),created_at,now))
    #                     db.query().execute(
    #                         'UPDATE `disk_category_dirty` SET `event_type`=?,`is_dir`=?,`updated_at`=? WHERE `category`=? AND `unit_path`=? AND `path`=?',
    #                         (event_type,int(bool(event.get('is_dir'))),now,category,site_path,event_path))
    #                 db.commit()
    #         # 统计单元失效时删除该 unit 下残留的 dirty 记录
    #         for value in (remove_paths or []):
    #             category,path = value if isinstance(value,(tuple,list)) and len(value) == 2 else ('project_files_size',value)
    #             path = self._format_disk_path(path)
    #             if category in valid_categories and path:
    #                 self._disk_category_db_execute(
    #                     'DELETE FROM `disk_category_dirty` WHERE `category`=? AND `unit_path`=?',
    #                     (category,path))
    #         return True
    #     except Exception:
    #         try:
    #             if 'db' in locals(): db.rollback()
    #         except:
    #             pass
    #         return False

    # # 读取并取出持久化事件，形成本轮 refresh 的快照
    # def _take_disk_category_dirty_file(self,units):
    #     try:
    #         # 根据当前 unit 列表构造允许读取的分类和路径集合
    #         allowed = {category:set() for category in self._get_disk_category_fields()}
    #         for value in (units or []):
    #             category,path = self._normalize_disk_category_unit(value)
    #             if category in allowed and path: allowed[category].add(path)
    #         # 将旧版 JSON journal 迁移到 SQLite，随后删除旧文件避免重复迁移
    #         dirty_path = self._get_disk_category_dirty_path()
    #         if os.path.exists(dirty_path):
    #             legacy = self._normalize_disk_category_dirty_state(json.loads(public.readFile(dirty_path)))
    #             for site_path,payload in legacy.get('sites',{}).items():
    #                 if payload.get('force_site'):
    #                     if not self._update_disk_category_dirty_file([site_path]): return {'version': 2,'force_full': False,'sites': {}}
    #                 if not self._update_disk_category_dirty_file(events=payload.get('events',[])):
    #                     return {'version': 2,'force_full': False,'sites': {}}
    #             if legacy.get('force_full'):
    #                 if not self._update_disk_category_dirty_file(force_full=True):
    #                     return {'version': 2,'force_full': False,'sites': {}}
    #             os.remove(dirty_path)
    #         # 读取 SQLite 中全部 dirty 行，并转换为按分类组织的 refresh 快照
    #         rows = self._disk_category_db_query(
    #             'SELECT `id`,`category`,`unit_path`,`path`,`old_path`,`event_type`,`is_dir`,`created_at`,`updated_at` FROM `disk_category_dirty`',())
    #         dirty = {category:{'force_full': False,'sites': {}}
    #                  for category in self._get_disk_category_fields()}
    #         row_tokens = []
    #         for row in rows or []:
    #             category = row.get('category')
    #             if category not in dirty: continue
    #             site_path = row.get('unit_path')
    #             if site_path == '*' and row.get('path') == '*':
    #                 dirty[category]['force_full'] = True
    #                 row_tokens.append((row['id'],row['updated_at']))
    #                 continue
    #             if site_path not in allowed[category]: continue
    #             payload = dirty[category]['sites'].setdefault(
    #                 site_path,{'force_site': False,'events': []})
    #             if row.get('path') == '' and row.get('event_type') == 'FORCE_SITE':
    #                 payload['force_site'] = True
    #             elif row.get('path'):
    #                 mask,cookie = self._disk_category_decode_event_type(row.get('event_type'))
    #                 if mask:
    #                     payload['events'].append({
    #                         'category': category,'site': site_path,'path': row['path'],
    #                         'old_path': row.get('old_path') or '',
    #                         'mask': mask,'cookie': cookie,'is_dir': bool(row.get('is_dir')),'time': row.get('updated_at',0)
    #                     })
    #             row_tokens.append((row['id'],row['updated_at']))
    #         # 清理已经不属于当前统计 unit 的残留记录
    #         stale_sites = set((row.get('category'),row.get('unit_path')) for row in rows or []
    #                           if row.get('category') in allowed and row.get('unit_path') != '*' and
    #                           row.get('unit_path') not in allowed[row.get('category')])
    #         for category,stale_site in stale_sites:
    #             self._disk_category_db_execute(
    #                 'DELETE FROM `disk_category_dirty` WHERE `category`=? AND `unit_path`=?',
    #                 (category,stale_site))
    #         snapshot = {'version': 3,'categories': dirty,'_db_rows': row_tokens}
    #         snapshot['force_full'] = any(value.get('force_full') for value in dirty.values())
    #         snapshot['sites'] = dirty['project_files_size']['sites']
    #         return snapshot
    #     except:
    #         raise

    # # 成功写入统计结果后，仅删除本轮读取且未被 watcher 更新的记录
    # def _finish_disk_category_dirty_snapshot(self,snapshot):
    #     rows = snapshot.get('_db_rows',[]) if isinstance(snapshot,dict) else []
    #     if not rows: return True
    #     try:
    #         with public.SqliteConn('default') as db:
    #             db.autocommit(False)
    #             row_groups = {}
    #             for row_id,updated_at in rows:
    #                 row_groups.setdefault(updated_at,[]).append(row_id)
    #             for updated_at,row_ids in row_groups.items():
    #                 for index in range(0,len(row_ids),500):
    #                     chunk = row_ids[index:index + 500]
    #                     placeholders = ','.join(['?'] * len(chunk))
    #                     params = list(chunk)
    #                     params.append(updated_at)
    #                     db.query().execute(
    #                         'DELETE FROM `disk_category_dirty` WHERE `id` IN ({}) AND `updated_at`=?'.format(placeholders),
    #                         tuple(params))
    #             db.commit()
    #         return True
    #     except:
    #         try: db.rollback()
    #         except: pass
    #         return False

    # # 刷新失败时将完整事件快照合并回 SQLite dirty journal
    # def _restore_disk_category_dirty_snapshot(self,snapshot):
    #     if not isinstance(snapshot,dict): return
    #     categories = snapshot.get('categories')
    #     if not isinstance(categories,dict):
    #         categories = {'project_files_size': {
    #             'force_full': bool(snapshot.get('force_full',False)),
    #             'sites': snapshot.get('sites',{})}}
    #     for category,current in categories.items():
    #         if category not in self._get_disk_category_fields() or not isinstance(current,dict): continue
    #         events = []
    #         force_sites = []
    #         for site_path,payload in current.get('sites',{}).items():
    #             if not isinstance(payload,dict): continue
    #             if payload.get('force_site'): force_sites.append((category,site_path))
    #             for event in payload.get('events',[]) if isinstance(payload.get('events'),list) else []:
    #                 if isinstance(event,dict):
    #                     event = event.copy()
    #                     event['category'] = category
    #                     events.append(event)
    #         self._update_disk_category_dirty_file(
    #             force_sites,events=events,force_full=bool(current.get('force_full',False)),
    #             categories=[category])

    # # 为一个统计单元目录增加单个 inotify watch
    # def _add_disk_category_watch(self,watch_path,category,site_path):
    #     if not _disk_category_inotify_libc or _disk_category_inotify_fd is None: return
    #     watch_path = self._format_disk_path(watch_path)
    #     if not watch_path or watch_path in _disk_category_watch_paths or not os.path.isdir(watch_path): return
    #     try:
    #         mask = 0x2 | 0x4 | 0x8 | 0x100 | 0x200 | 0x40 | 0x80 | 0x4000 | 0x40000000
    #         wd = _disk_category_inotify_libc.inotify_add_watch(
    #             _disk_category_inotify_fd,watch_path.encode('utf-8'),mask)
    #         if wd >= 0:
    #             _disk_category_watch_paths[watch_path] = wd
    #             _disk_category_watch_sites[wd] = (category,site_path)
    #             _disk_category_watch_roots[wd] = watch_path
    #     except:
    #         pass

    # # 递归为统计单元及其现有子目录补齐 inotify watch
    # def _add_disk_category_watch_tree(self,watch_path,category,site_path):
    #     if not watch_path or not os.path.isdir(watch_path): return
    #     try:
    #         for root,_,_ in os.walk(watch_path):
    #             self._add_disk_category_watch(root,category,site_path)
    #     except:
    #         self._mark_disk_category_dirty(site_path,category)

    # # 同步所有分类统计单元监听，增删目录后更新 watch 和 dirty 残留
    # def _sync_disk_category_watches(self,units):
    #     # 计算当前应该存在的 category/unit 集合
    #     desired = set()
    #     for value in (units or []):
    #         category,path = self._normalize_disk_category_unit(value)
    #         if category in self._get_disk_category_fields() and path: desired.add((category,path))
    #     # 删除已经失效、移除或不再属于当前 unit 的 watch
    #     stale_wds = []
    #     with _disk_category_inotify_lock:
    #         for wd,value in list(_disk_category_watch_sites.items()):
    #             watch_path = _disk_category_watch_roots.get(wd)
    #             if value not in desired or not watch_path or not os.path.isdir(watch_path):
    #                 stale_wds.append(wd)
    #         for wd in stale_wds:
    #             watch_path = _disk_category_watch_roots.pop(wd,None)
    #             _disk_category_watch_sites.pop(wd,None)
    #             if watch_path: _disk_category_watch_paths.pop(watch_path,None)
    #             try: _disk_category_inotify_libc.inotify_rm_watch(_disk_category_inotify_fd,wd)
    #             except: pass
    #     # 为新增 unit 递归添加目录监听，并清理旧 unit 的 dirty 记录
    #     watched_sites = set(_disk_category_watch_sites.values())
    #     for category,site_path in desired:
    #         if os.path.isdir(site_path) and (category,site_path) not in watched_sites:
    #             self._add_disk_category_watch_tree(site_path,category,site_path)
    #     self._update_disk_category_dirty_file(remove_paths=(watched_sites - desired))

    # # 持续读取 inotify 事件，只记录变化位置，不直接计算目录大小
    # def _disk_category_inotify_loop(self):
    #     global _disk_category_inotify_overflow
    #     import select
    #     import struct
    #     last_sync = 0
    #     disabled = False
    #     while True:
    #         try:
    #             if not self.is_disk_category_stats_enabled():
    #                 disabled = True
    #                 time.sleep(1)
    #                 continue
    #             if disabled:
    #                 # 关闭期间可能漏掉事件，重新开启后要求下次定时任务全量校准
    #                 self._update_disk_category_dirty_file(force_full=True)
    #                 disabled = False
    #             # 周期性同步监听树，补上新建目录和新增统计 unit
    #             if time.time() - last_sync >= 10:
    #                 self._sync_disk_category_watches(self._get_disk_category_units())
    #                 last_sync = time.time()
    #             # 等待 inotify fd 可读，避免 watcher 空转占用 CPU
    #             ready,_,_ = select.select([_disk_category_inotify_fd],[],[],1)
    #             if not ready: continue
    #             # 一次读取一批事件，统一在本轮结束后批量写入 SQLite
    #             data = os.read(_disk_category_inotify_fd,1024 * 1024)
    #             offset = 0
    #             events = []
    #             watch_additions = []
    #             overflowed = False
    #             # 按 inotify_event 结构逐条解析本次读取的数据
    #             while offset + 16 <= len(data):
    #                 watch_id,mask,cookie,name_len = struct.unpack_from('iIII',data,offset)
    #                 offset += 16
    #                 name = data[offset:offset + name_len].split(b'\0',1)[0].decode('utf-8','ignore')
    #                 offset += name_len
    #                 # 队列溢出意味着事件可能丢失，要求下一次 refresh 全量校准
    #                 if mask & 0x4000:
    #                     with _disk_category_inotify_lock:
    #                         _disk_category_inotify_overflow = True
    #                     overflowed = True
    #                     continue
    #                 watch_value = _disk_category_watch_sites.get(watch_id)
    #                 watch_path = _disk_category_watch_roots.get(watch_id)
    #                 if not watch_value or not watch_path: continue
    #                 category,site_path = watch_value
    #                 if mask & 0x8000:
    #                     with _disk_category_inotify_lock:
    #                         _disk_category_watch_sites.pop(watch_id,None)
    #                         _disk_category_watch_roots.pop(watch_id,None)
    #                         _disk_category_watch_paths.pop(watch_path,None)
    #                     continue
    #                 # 将 watch 根目录和事件名称拼成规范化的实际路径
    #                 event_path = self._format_disk_path(os.path.join(watch_path,name) if name else watch_path)
    #                 event = {
    #                     'category': category,'site': site_path,'path': event_path,'mask': int(mask),
    #                     'cookie': int(cookie),'is_dir': bool(mask & 0x40000000),
    #                     'time': time.time()
    #                 }
    #                 events.append(event)
    #                 if mask & 0x40000000 and name:
    #                     if mask & (0x100 | 0x80):
    #                         watch_additions.append((event_path,category,site_path))
    #             # 普通事件一次事务写入，overflow 另写 FORCE_FULL 标记
    #             if events:
    #                 self._update_disk_category_dirty_file(events=events)
    #             if overflowed:
    #                 self._update_disk_category_dirty_file(force_full=True)
    #             # 新建或移入的目录需要递归加入 watch
    #             for event_path,category,site_path in watch_additions:
    #                 self._add_disk_category_watch_tree(event_path,category,site_path)
    #         except:
    #             time.sleep(1)

    # # 初始化 inotify 文件描述符、目录监听和后台线程
    # def _ensure_disk_category_inotify(self,units,start_thread=True):
    #     global _disk_category_inotify_fd,_disk_category_inotify_thread,_disk_category_inotify_libc
    #     if os.name != 'posix': return False
    #     try:
    #         # refresh 只检查 watcher 是否可用，BT-Task 启动时才创建线程
    #         if not start_thread:
    #             return self._disk_category_watcher_state_valid()
    #         import ctypes
    #         # 只初始化一次 libc inotify fd 及其调用签名
    #         if _disk_category_inotify_fd is None:
    #             _disk_category_inotify_libc = ctypes.CDLL(None,use_errno=True)
    #             _disk_category_inotify_libc.inotify_init1.argtypes = [ctypes.c_int]
    #             _disk_category_inotify_libc.inotify_init1.restype = ctypes.c_int
    #             _disk_category_inotify_libc.inotify_add_watch.argtypes = [
    #                 ctypes.c_int,ctypes.c_char_p,ctypes.c_uint32]
    #             _disk_category_inotify_libc.inotify_add_watch.restype = ctypes.c_int
    #             _disk_category_inotify_libc.inotify_rm_watch.argtypes = [ctypes.c_int,ctypes.c_int]
    #             _disk_category_inotify_libc.inotify_rm_watch.restype = ctypes.c_int
    #             _disk_category_inotify_fd = _disk_category_inotify_libc.inotify_init1(os.O_NONBLOCK)
    #             if _disk_category_inotify_fd < 0: return False
    #         # 首次启动先同步现有目录，再启动后台循环
    #         self._sync_disk_category_watches(units)
    #         if _disk_category_inotify_thread is None:
    #             _disk_category_inotify_thread = threading.Thread(
    #                 target=self._disk_category_inotify_loop,name='disk-category-inotify',daemon=True)
    #             _disk_category_inotify_thread.start()
    #             # 持久化 watcher 进程状态，供 refresh 判断长期 watcher 是否存活
    #             state_path = self._get_disk_category_watcher_state_path()
    #             temp_path = '{}.tmp.{}'.format(state_path,os.getpid())
    #             with open(temp_path,'w') as fp:
    #                 json.dump({'pid': os.getpid(),'initialized': True,'started_at': time.time()},fp)
    #                 fp.flush()
    #                 os.fsync(fp.fileno())
    #             os.replace(temp_path,state_path)
    #         return True
    #     except:
    #         try:
    #             if 'temp_path' in locals() and os.path.exists(temp_path): os.remove(temp_path)
    #         except:
    #             pass
    #         return False

    # # 判断状态文件记录的 watcher 进程是否仍然存活
    # def _disk_category_watcher_state_valid(self):
    #     try:
    #         with open(self._get_disk_category_watcher_state_path(),'r') as fp:
    #             state = json.load(fp)
    #         pid = int(state.get('pid')) if isinstance(state,dict) else int(state)
    #         os.kill(pid,0)
    #         return True
    #     except:
    #         return False

    # # 判断长期 watcher 是否尚未完成重启后的首次全量刷新
    # def _disk_category_watcher_needs_full(self):
    #     return False

    # # 标记当前 watcher 已完成首次全量刷新
    # def _set_disk_category_watcher_initialized(self):
    #     try:
    #         state_path = self._get_disk_category_watcher_state_path()
    #         with open(state_path,'r') as fp:
    #             state = json.load(fp)
    #         if not isinstance(state,dict): return
    #         state['initialized'] = True
    #         temp_path = '{}.tmp.{}'.format(state_path,os.getpid())
    #         with open(temp_path,'w') as fp:
    #             json.dump(state,fp)
    #             fp.flush()
    #             os.fsync(fp.fileno())
    #         os.replace(temp_path,state_path)
    #     except:
    #         try:
    #             if 'temp_path' in locals() and os.path.exists(temp_path): os.remove(temp_path)
    #         except:
    #             pass

    # # 在长期运行的 BT-Task 主进程中启动所有磁盘分类目录 watcher
    # def start_disk_category_watcher(self):
    #     try:
    #         if not self.is_disk_category_stats_enabled(): return False
    #         return self._ensure_disk_category_inotify(self._get_disk_category_units(),True)
    #     except:
    #         return False

    # # 取出当前 dirty 统计单元，并把内存 dirty 与 overflow 合并进快照
    # def _take_disk_category_dirty_sites(self,units):
    #     global _disk_category_inotify_overflow
    #     file_dirty = self._take_disk_category_dirty_file(units)
    #     with _disk_category_inotify_lock:
    #         dirty = set(_disk_category_dirty_sites)
    #         _disk_category_dirty_sites.difference_update(dirty)
    #         overflow = _disk_category_inotify_overflow
    #         _disk_category_inotify_overflow = False
    #     for category,site_path in dirty:
    #         current = file_dirty['categories'].setdefault(category,{'force_full': False,'sites': {}})
    #         payload = current['sites'].setdefault(site_path,{'force_site': False,'events': []})
    #         payload['force_site'] = True
    #     if overflow:
    #         for current in file_dirty['categories'].values(): current['force_full'] = True
    #     file_dirty['force_full'] = bool(file_dirty.get('force_full')) or overflow
    #     file_dirty['sites'] = file_dirty['categories']['project_files_size']['sites']
    #     return file_dirty

    # # 统计失败时恢复本轮取出的 dirty 快照，避免丢失待处理事件
    # def _restore_disk_category_dirty_sites(self,site_paths):
    #     if isinstance(site_paths,dict):
    #         self._restore_disk_category_dirty_snapshot(site_paths)
    #         return
    #     values = [('project_files_size',path) for path in (site_paths or [])]
    #     with _disk_category_inotify_lock:
    #         _disk_category_dirty_sites.update(values)
    #     self._update_disk_category_dirty_file(values)

    # # 读取包含内部 bucket 和路径签名字段的完整统计结果
    # def _get_disk_category_raw_result(self):
    #     try:
    #         result = json.loads(public.readFile(self._get_disk_category_result_path()))
    #         return result if isinstance(result,dict) else {}
    #     except:
    #         return {}

    # # 检查项目目录的 SQLite 状态和 JSON 结果是否足以支持增量刷新
    # def _disk_category_project_cache_ready(self,result,disk_info):
    #     project_paths = self._get_disk_category_project_units(
    #         self._get_disk_category_paths().get('project_files_size',[]))
    #     return self._disk_category_cache_ready('project_files_size',project_paths,result,disk_info)

    # # 检查指定分类的结果、路径签名和 SQLite unit 状态是否完整
    # def _disk_category_cache_ready(self,category,units,result,disk_info):
    #     if not result or not self.is_disk_category_stats_valid(disk_info): return False
    #     try:
    #         db_units = set(row.get('unit_path') for row in self._disk_category_db_query(
    #             'SELECT `unit_path` FROM `disk_category_stats` WHERE `category`=? AND `initialized`=1',
    #             (category,)) or [])
    #         # SQLite 是持久化状态的真实来源；如果行缺失或不可读，
    #         # 不能继续信任过期的 JSON bucket，而要明确执行一次重建。
    #         return all(path in db_units for path in (units or []))
    #     except:
    #         return False

    # # 保留旧版全量计算器便于回溯；实际刷新使用下方细颗粒度实现
    # def _calculate_disk_category_stats_legacy(self,disk_info,previous_result=None,dirty_sites=None,force_full=False):
    #     # 按当前挂载点创建本轮统计结果的初始结构
    #     stats = self._get_disk_category_default_stats(disk_info)
    #     mount_paths = list(stats.keys())
    #     if not mount_paths: return stats

    #     # 规范化上一轮结果和 dirty 网站集合，避免异常输入影响后续计算
    #     previous_result = previous_result if isinstance(previous_result,dict) else {}
    #     dirty_sites = set(dirty_sites or [])

    #     # 挂载点按路径长度倒序，优先匹配更具体的挂载点
    #     mount_paths = sorted(mount_paths,key=lambda x: len(str(x).rstrip('/')),reverse=True)

    #     # 收集当前所有分类目录，格式化路径并过滤不存在的目录
    #     path_info = self._get_disk_category_paths()
    #     path_candidates = []
    #     for field,path_list in path_info.items():
    #         for path in path_list:
    #             path = self._format_disk_path(path)
    #             if path and os.path.exists(path): path_candidates.append((field,path))

    #     # 从上一轮 JSON 中加载每个挂载点下的网站 bucket 大小
    #     old_buckets = {}
    #     for mount_path in stats:
    #         current = previous_result.get(mount_path,{})
    #         buckets = current.get('_project_buckets',{}) if isinstance(current,dict) else {}
    #         old_buckets[mount_path] = {}
    #         if isinstance(buckets,dict):
    #             for path,value in buckets.items():
    #                 try: old_buckets[mount_path][path] = max(0,int(value))
    #                 except: pass

    #     # 准备新的 bucket，并按路径深度排序以便执行父子目录去重
    #     new_buckets = {mount_path:{} for mount_path in stats}
    #     count_paths = []
    #     path_candidates.sort(key=lambda item: len(item[1].rstrip('/')))

    #     # 逐个处理项目、数据库、备份和日志目录
    #     for field,path in path_candidates:
    #         # 已被更短父目录覆盖的路径不再重复统计
    #         if any(self._is_path_in_mount(path,count_path) for count_path in count_paths): continue

    #         # 将当前目录归属到对应挂载点，无法匹配时跳过
    #         mount_path = self._get_path_mount(path,mount_paths)
    #         if not mount_path: continue
    #         try:
    #             if field == 'project_files_size':
    #                 # 项目目录未变化时复用 bucket，否则只重新执行当前目录统计
    #                 old_size = old_buckets.get(mount_path,{}).get(path)
    #                 if not force_full and path not in dirty_sites and old_size is not None:
    #                     path_size = old_size
    #                 else:
    #                     path_size = self._get_disk_path_size(path)
    #                 new_buckets[mount_path][path] = max(0,int(path_size))
    #             else:
    #                 # 非项目分类沿用逐路径统计逻辑，结果直接累加到分类字段
    #                 path_size = self._get_disk_path_size(path)
    #                 stats[mount_path][field] += path_size
    #         except:
    #             # 单个目录失败时保留旧项目 bucket，并让后续刷新继续重试
    #             if field == 'project_files_size':
    #                 new_buckets[mount_path][path] = old_buckets.get(mount_path,{}).get(path,0)
    #                 self._mark_disk_category_dirty(path)
    #             public.print_log('[Disk category stats] Failed to scan path [{}]: {}'.format(
    #                 path,public.get_error_info()),'ERROR')
    #             continue

    #         # 记录已统计目录，用于后续父子目录去重
    #         count_paths.append(path)

    #     # 记录本次全量校准时间；增量刷新时沿用上一轮时间

    #     # 汇总每个挂载点的项目 bucket，并更新内部缓存字段
    #     for mount_path in stats:
    #         current = previous_result.get(mount_path,{})
    #         old_total = 0
    #         try: old_total = int(current.get('project_files_size',0))
    #         except: pass

    #         # 首次或强制全量时直接求和，否则只应用发生变化的 bucket 差值
    #         if force_full or not old_buckets.get(mount_path):
    #             project_total = sum(new_buckets[mount_path].values())
    #         else:
    #             project_total = old_total
    #             for path in set(old_buckets[mount_path]) | set(new_buckets[mount_path]):
    #                 project_total += new_buckets[mount_path].get(path,0) - old_buckets[mount_path].get(path,0)

    #         # 保存项目总大小、bucket 明细和最近一次全量校准时间
    #         stats[mount_path]['project_files_size'] = max(0,project_total)
    #         stats[mount_path]['_project_buckets'] = new_buckets[mount_path]

    #     # 用磁盘已用空间减去已分类大小，得到各挂载点的 other_files_size
    #     for disk in disk_info:
    #         mount_path = disk.get('path')
    #         if mount_path not in stats: continue

    #         # 读取挂载点总已用空间，异常时按 0 处理
    #         try: used_size = int(disk['size'][1]) * 1024
    #         except: used_size = 0

    #         # 汇总项目、数据库、备份和日志大小，计算未分类剩余空间
    #         classified_size = sum(int(stats[mount_path].get(field,0)) for field in (
    #             'project_files_size','databases_size','backups_size','system_logs_size'))
    #         stats[mount_path]['other_files_size'] = max(0,used_size - classified_size)
    #     return stats

    # # 返回可安全用于文件级差值的普通文件元数据
    # def _get_disk_category_file_meta(self,path):
    #     try:
    #         import stat
    #         value = os.lstat(path)
    #         if not stat.S_ISREG(value.st_mode) or int(value.st_nlink) != 1: return None
    #         return {
    #             'size': max(0,int(value.st_size)),'dev': int(value.st_dev),'ino': int(value.st_ino),
    #             'nlink': int(value.st_nlink),'mtime_ns': int(getattr(value,'st_mtime_ns',int(value.st_mtime * 1000000000))),
    #             'time': time.time()
    #         }
    #     except:
    #         return None

    # # 获取目录自身 inode 大小，用于维护目录 bucket 的元数据
    # def _get_disk_category_dir_self_size(self,path):
    #     try: return max(0,int(os.lstat(path).st_size))
    #     except: return 0

    # # 将 JSON 中的目录 bucket 统一为可参与增量计算的字典
    # def _normalize_disk_category_dir_cache(self,value):
    #     result = {}
    #     if not isinstance(value,dict): return result
    #     for path,current in value.items():
    #         path = self._format_disk_path(path)
    #         if not path: continue
    #         if isinstance(current,dict):
    #             try:
    #                 result[path] = {
    #                     'size': max(0,int(current.get('size',0))),
    #                     'self_size': max(0,int(current.get('self_size',0))),
    #                     'time': float(current.get('time',0))
    #                 }
    #             except: pass
    #         else:
    #             try: result[path] = {'size': max(0,int(current)),'self_size': 0,'time': 0}
    #             except: pass
    #     return result

    # # 将 JSON 或 SQLite 中的文件缓存统一为可靠元数据字典
    # def _normalize_disk_category_file_cache(self,value):
    #     result = {}
    #     if not isinstance(value,dict): return result
    #     for path,current in value.items():
    #         path = self._format_disk_path(path)
    #         if not path or not isinstance(current,dict): continue
    #         try:
    #             if int(current.get('nlink',0)) != 1: continue
    #             result[path] = {
    #                 'size': max(0,int(current.get('size',0))),'dev': int(current.get('dev',0)),
    #                 'ino': int(current.get('ino',0)),'nlink': 1,
    #                 'mtime_ns': int(current.get('mtime_ns',0)),'time': float(current.get('time',0))
    #             }
    #         except: pass
    #     return result

    # # 对项目路径做真实路径、存在性和父子目录去重
    # def _get_disk_category_project_units(self,site_paths):
    #     result = []
    #     paths = set()
    #     for path in (site_paths or []):
    #         path = self._format_disk_path(path)
    #         if path and os.path.exists(path): paths.add(path)
    #     for path in sorted(paths,key=lambda value: (len(value.rstrip('/')),value)):
    #         if any(self._is_path_in_mount(path,current) for current in result): continue
    #         result.append(path)
    #     return result

    # # 计算项目 unit 集合的稳定签名，用于检测路径配置变化
    # def _disk_category_project_signature(self,site_paths):
    #     return self._disk_category_signature(self._get_disk_category_project_units(site_paths))

    # # 对任意分类 unit 集合排序后计算稳定哈希签名
    # def _disk_category_signature(self,units):
    #     import hashlib
    #     value = '\n'.join(sorted(set(self._format_disk_path(path) for path in (units or []) if path)))
    #     return hashlib.sha256(value.encode('utf-8')).hexdigest()

    # # 判断项目分类的路径集合是否发生变化
    # def _disk_category_project_paths_changed(self,result,site_paths):
    #     units = self._get_disk_category_project_units(site_paths)
    #     return self._disk_category_paths_changed('project_files_size',result,units)

    # # 判断指定分类的路径签名是否变化或尚未建立 baseline
    # def _disk_category_paths_changed(self,category,result,units):
    #     signature = self._disk_category_signature(units)
    #     found = False
    #     for value in result.values():
    #         if not isinstance(value,dict): continue
    #         signatures = value.get('_disk_category_paths_signatures',{})
    #         current = signatures.get(category) if isinstance(signatures,dict) else None
    #         if current is None and category == 'project_files_size':
    #             current = value.get('_project_paths_signature')
    #         if current is None: continue
    #         found = True
    #         if current != signature: return True
    #     return not found

    # # 计算事件对应的最小父目录，作为目录 fallback 的统计边界
    # def _disk_category_event_parent(self,site_path,event_path,is_dir=False,mask=0):
    #     site_path = self._format_disk_path(site_path)
    #     event_path = self._format_disk_path(event_path)
    #     # MOVED_FROM、MOVED_TO 和 DELETE 指向包含该条目的父目录；
    #     # MOVED_TO 的目录已经存在，不能因为 os.path.isdir(event_path)
    #     # 就把事件条目本身当成父目录。
    #     if int(mask) & (0x40 | 0x80 | 0x200):
    #         parent = os.path.dirname(event_path)
    #     elif is_dir and os.path.isdir(event_path):
    #         parent = event_path
    #     else:
    #         parent = os.path.dirname(event_path)
    #     parent = self._format_disk_path(parent)
    #     if not parent or not self._is_path_in_mount(parent,site_path): return site_path
    #     return parent

    # # 热循环使用的事件父目录计算；调用方已保证 site_path 和 event_path 是规范化路径
    # def _disk_category_event_parent_fast(self,site_path,event_path,is_dir=False,mask=0):
    #     if int(mask) & (0x40 | 0x80 | 0x200):
    #         parent = os.path.dirname(event_path)
    #     elif is_dir and os.path.isdir(event_path):
    #         parent = event_path
    #     else:
    #         parent = os.path.dirname(event_path)
    #     if not parent or not self._is_formatted_path_in_mount(parent,site_path): return site_path
    #     return parent

    # # 对受影响目录做父子去重，只保留最小数量的 fallback 目录
    # def _disk_category_compact_dirs(self,paths):
    #     result = []
    #     for path in sorted(set(self._format_disk_path(path) for path in paths if path),key=len):
    #         if any(self._is_path_in_mount(path,current) for current in result): continue
    #         result.append(path)
    #     return result

    # # 将文件变化量沿目录层级传播到已有目录 bucket
    # def _disk_category_adjust_dir_cache(self,dir_cache,changed_path,delta,skip_path=None):
    #     for path,current in list(dir_cache.items()):
    #         if path == skip_path: continue
    #         if self._is_formatted_path_in_mount(changed_path,path):
    #             current['size'] = max(0,int(current.get('size',0)) + int(delta))
    #             current['time'] = time.time()

    # # 用一次 du 结果建立或替换目录 bucket，并修正祖先 bucket
    # def _disk_category_set_dir_bucket(self,dir_cache,path,new_size):
    #     path = self._format_disk_path(path)
    #     old = dir_cache.get(path)
    #     old_size = int(old.get('size',0)) if isinstance(old,dict) else 0
    #     delta = int(new_size) - old_size
    #     self._disk_category_adjust_dir_cache(dir_cache,path,delta,skip_path=path)
    #     for child in list(dir_cache):
    #         if child != path and self._is_formatted_path_in_mount(child,path): dir_cache.pop(child,None)
    #     dir_cache[path] = {
    #         'size': max(0,int(new_size)),'self_size': self._get_disk_category_dir_self_size(path),
    #         'time': time.time()
    #     }
    #     return delta

    # # 限制稀疏缓存大小，优先淘汰最久未更新的条目
    # def _disk_category_prune_sparse_cache(self,cache,limit):
    #     if len(cache) <= limit: return
    #     ordered = sorted(cache.items(),key=lambda item: float(item[1].get('time',0)) if isinstance(item[1],dict) else 0)
    #     for path,_ in ordered[:len(cache) - limit]: cache.pop(path,None)

    # # 对一个网站应用文件差值；不可靠时逐级回退目录 bucket、网站 bucket
    # def _apply_disk_category_project_changes(self,site_path,old_size,payload,file_cache,dir_cache,move_pairs):
    #     import copy
    #     site_path = self._format_disk_path(site_path)
    #     # 过滤本 unit 的有效事件，并保留原始缓存用于 fallback 恢复
    #     events = payload.get('events',[]) if isinstance(payload,dict) else []
    #     events = [event for event in events if isinstance(event,dict)]
    #     # 文件缓存只替换或删除，不在原元数据对象上原地修改；目录缓存做深拷贝，
    #     # 这样目录 fallback 可以恢复到本轮计算前的状态。
    #     original_file_cache = file_cache.copy()
    #     original_dir_cache = copy.deepcopy(dir_cache)
    #     fallback_dirs = set()
    #     handled = set()
    #     total_delta = 0
    #     direct_deltas = []
    #     same_site_move_dirs = []
    #     move_cache_moves = []
    #     move_cache_removals = []

    #     # 先按 rename cookie 配对 MOVED_FROM 和 MOVED_TO，区分同目录、跨目录和跨 unit 移动。
    #     for cookie,pair in move_pairs.items():
    #         source,target = pair
    #         if not source or not target: continue
    #         if source.get('site') != site_path and target.get('site') != site_path: continue
    #         source_parent = self._disk_category_event_parent_fast(
    #             source.get('site'),source.get('path'),bool(source.get('is_dir')),int(source.get('mask',0)))
    #         target_parent = self._disk_category_event_parent_fast(
    #             target.get('site'),target.get('path'),bool(target.get('is_dir')),int(target.get('mask',0)))
    #         if source.get('site') == target.get('site') == site_path and source_parent == target_parent:
    #             old_path = source.get('path')
    #             new_path = target.get('path')
    #             direct_deltas.append((old_path,0))
    #             direct_deltas.append((new_path,0))
    #             cached = file_cache.pop(old_path,None)
    #             meta = self._get_disk_category_file_meta(new_path)
    #             if cached and meta:
    #                 file_cache[new_path] = meta
    #                 if int(source.get('mask',0) | target.get('mask',0)) & (0x2 | 0x8):
    #                     delta = int(meta.get('size',0)) - int(cached.get('size',0))
    #                     total_delta += delta
    #                     direct_deltas.append((old_path,delta))
    #             move_cache_removals.append(old_path)
    #             move_cache_moves.append((old_path,new_path,meta))
    #             # 目录 rename 不改变总大小，但目录下的稀疏缓存路径必须同步改名。
    #             if source.get('is_dir') or target.get('is_dir'):
    #                 renamed_files = {}
    #                 for path,current in list(file_cache.items()):
    #                     if self._is_formatted_path_in_mount(path,old_path):
    #                         suffix = path[len(old_path):]
    #                         renamed_files[new_path + suffix] = current
    #                         move_cache_moves.append((path,new_path + suffix,current))
    #                         file_cache.pop(path,None)
    #                 file_cache.update(renamed_files)
    #             renamed_dirs = {}
    #             for path,current in list(dir_cache.items()):
    #                 if self._is_formatted_path_in_mount(path,old_path):
    #                     suffix = path[len(old_path):]
    #                     renamed_dirs[new_path + suffix] = current
    #                     dir_cache.pop(path,None)
    #             dir_cache.update(renamed_dirs)
    #         elif source.get('site') == target.get('site') == site_path:
    #             old_path = source.get('path')
    #             new_path = target.get('path')
    #             if source.get('is_dir') or target.get('is_dir'):
    #                 fallback_dirs.add(source_parent)
    #                 fallback_dirs.add(target_parent)
    #                 for path,current in list(file_cache.items()):
    #                     if self._is_formatted_path_in_mount(path,old_path):
    #                         suffix = path[len(old_path):]
    #                         move_cache_removals.append(path)
    #                         move_cache_moves.append((path,new_path + suffix,current))
    #                 handled.add(id(source))
    #                 handled.add(id(target))
    #                 continue
    #             cached = file_cache.get(old_path)
    #             meta = self._get_disk_category_file_meta(new_path)
    #             if cached and meta:
    #                 # 同一网站跨目录移动时总量不变；仅调整稀疏缓存和已知目录 bucket。
    #                 file_cache.pop(old_path,None)
    #                 file_cache[new_path] = meta
    #                 move_size = int(cached.get('size',0))
    #                 has_modify = bool(int(source.get('mask',0) | target.get('mask',0)) & (0x2 | 0x8))
    #                 target_size = int(meta.get('size',0)) if has_modify else move_size
    #                 delta = target_size - move_size if has_modify else 0
    #                 self._disk_category_adjust_dir_cache(dir_cache,old_path,-move_size)
    #                 self._disk_category_adjust_dir_cache(dir_cache,new_path,target_size)
    #                 if delta:
    #                     total_delta += delta
    #                     direct_deltas.append((old_path,delta))
    #                 same_site_move_dirs.append((source_parent,target_parent))
    #             else:
    #                 fallback_dirs.add(source_parent)
    #                 fallback_dirs.add(target_parent)
    #             move_cache_removals.append(old_path)
    #             move_cache_moves.append((old_path,new_path,meta))
    #         else:
    #             # 跨统计 unit 移动：源端尝试使用旧缓存，目标端使用当前 stat。
    #             if source.get('is_dir') or target.get('is_dir'):
    #                 if source.get('site') == site_path: fallback_dirs.add(source_parent)
    #                 if target.get('site') == site_path: fallback_dirs.add(target_parent)
    #                 handled.add(id(source))
    #                 handled.add(id(target))
    #                 continue
    #             if source.get('site') == site_path:
    #                 cached = file_cache.get(source.get('path'))
    #                 target_meta = self._get_disk_category_file_meta(target.get('path'))
    #                 move_cache_removals.append(source.get('path'))
    #                 if cached and target_meta and int(cached.get('size',0)) == int(target_meta.get('size',0)):
    #                     move_size = int(cached.get('size',0))
    #                     file_cache.pop(source.get('path'),None)
    #                     self._disk_category_adjust_dir_cache(dir_cache,source_parent,-move_size)
    #                     total_delta -= move_size
    #                     direct_deltas.append((source.get('path'),-move_size))
    #                 else:
    #                     fallback_dirs.add(source_parent)
    #             if target.get('site') == site_path:
    #                 target_meta = self._get_disk_category_file_meta(target.get('path'))
    #                 move_cache_moves.append((source.get('path'),target.get('path'),target_meta))
    #                 if target_meta:
    #                     move_size = int(target_meta.get('size',0))
    #                     file_cache[target.get('path')] = target_meta
    #                     self._disk_category_adjust_dir_cache(dir_cache,target_parent,move_size)
    #                     total_delta += move_size
    #                     direct_deltas.append((target.get('path'),move_size))
    #                 else:
    #                     fallback_dirs.add(target_parent)
    #         handled.add(id(source))
    #         handled.add(id(target))

    #     # 再把没有被 rename 配对处理的事件按实际路径聚合
    #     path_events = {}
    #     for event in events:
    #         if id(event) in handled: continue
    #         path_events.setdefault(event.get('path'),[]).append(event)

    #     for path,current_events in path_events.items():
    #         if not path: continue
    #         masks = [int(event.get('mask',0)) for event in current_events]
    #         is_dir = any(event.get('is_dir') for event in current_events)
    #         has_create = any(mask & (0x100 | 0x80) for mask in masks)
    #         has_delete = any(mask & (0x200 | 0x40) for mask in masks)
    #         has_modify = any(mask & (0x2 | 0x8) for mask in masks)
    #         parent = self._disk_category_event_parent_fast(
    #             site_path,path,is_dir,0 if not masks else masks[-1])
    #         parent_bucket = dir_cache.get(parent)

    #         # 未配对 move 视为移入或移出；CREATE 后又 DELETE 时回退到父目录 du。
    #         if has_create and has_delete:
    #             fallback_dirs.add(parent)
    #             file_cache.pop(path,None)
    #             continue

    #         if has_create:
    #             if not is_dir:
    #                 meta = self._get_disk_category_file_meta(path)
    #                 if meta:
    #                     delta = int(meta.get('size',0))
    #                     total_delta += delta
    #                     direct_deltas.append((path,delta))
    #                     self._disk_category_adjust_dir_cache(dir_cache,path,delta)
    #                     file_cache[path] = meta
    #                 else:
    #                     fallback_dirs.add(parent)
    #             else:
    #                 fallback_dirs.add(parent)
    #             continue

    #         if has_delete:
    #             if not is_dir:
    #                 cached = file_cache.get(path)
    #                 if cached and all(key in cached for key in ('size','dev','ino')):
    #                     delta = -int(cached.get('size',0))
    #                     total_delta += delta
    #                     direct_deltas.append((path,delta))
    #                     self._disk_category_adjust_dir_cache(dir_cache,path,delta)
    #                     file_cache.pop(path,None)
    #                 else:
    #                     fallback_dirs.add(parent)
    #             else:
    #                 fallback_dirs.add(parent)
    #             continue

    #         if has_modify and not is_dir:
    #             cached = file_cache.get(path)
    #             meta = self._get_disk_category_file_meta(path)
    #             if cached and meta and cached.get('dev') == meta.get('dev') and cached.get('ino') == meta.get('ino'):
    #                 delta = int(meta['size']) - int(cached.get('size',0))
    #                 total_delta += delta
    #                 direct_deltas.append((path,delta))
    #                 self._disk_category_adjust_dir_cache(dir_cache,path,delta)
    #                 file_cache[path] = meta
    #             else:
    #                 fallback_dirs.add(parent)

    #     # 同一 unit 内 rename 的总量通常不变；如果两侧被其它目录 fallback 覆盖，
    #     # 则把两侧都加入 fallback，保证移动只被目录 du 计算一次。
    #     for source_parent,target_parent in same_site_move_dirs:
    #         if any(self._is_formatted_path_in_mount(source_parent,path) or
    #                self._is_formatted_path_in_mount(target_parent,path) or
    #                self._is_formatted_path_in_mount(path,source_parent) or
    #                self._is_formatted_path_in_mount(path,target_parent)
    #                for path in fallback_dirs):
    #             fallback_dirs.update((source_parent,target_parent))

    #     fallback_dirs = self._disk_category_compact_dirs(fallback_dirs)

    #     # 目录 du 覆盖其目录下的文件差值；恢复范围内旧缓存，避免同一变化重复计算。
    #     if fallback_dirs:
    #         covered_paths = [
    #             (path,delta) for path,delta in direct_deltas
    #             if any(self._is_formatted_path_in_mount(path,directory) for directory in fallback_dirs)
    #         ]
    #         total_delta -= sum(delta for _,delta in covered_paths)
    #         for directory in fallback_dirs:
    #             for path in list(file_cache):
    #                 if self._is_formatted_path_in_mount(path,directory): file_cache.pop(path,None)
    #             for path,current in original_file_cache.items():
    #                 if self._is_formatted_path_in_mount(path,directory): file_cache[path] = copy.deepcopy(current)
    #             for path in list(dir_cache):
    #                 if (self._is_formatted_path_in_mount(path,directory) or
    #                         self._is_formatted_path_in_mount(directory,path)):
    #                     dir_cache.pop(path,None)
    #             if directory in original_dir_cache:
    #                 dir_cache[directory] = copy.deepcopy(original_dir_cache[directory])

    #     if payload.get('force_site'):
    #         fallback_dirs = fallback_dirs or [site_path]
    #         site_scan = True
    #     else:
    #         # 未知文件差值使用最小受影响目录；目录 bucket 不存在时先建立 bucket，
    #         # 但不能把完整目录大小直接当作旧总量差值，所以保留 unit 总量并等待校准。
    #         site_scan = any(path not in original_dir_cache for path in fallback_dirs)

    #     if site_scan:
    #         # FORCE_SITE 或 unit 级 fallback 直接执行网站根目录 du
    #         new_size = self._get_disk_path_size(site_path)
    #         # 网站 du 已覆盖本轮全部目录和文件增量，不再额外执行目录 du
    #         for path in list(file_cache):
    #             if self._is_formatted_path_in_mount(path,site_path): file_cache.pop(path,None)
    #         for path in list(dir_cache):
    #             if self._is_formatted_path_in_mount(path,site_path): dir_cache.pop(path,None)
    #         for path in path_events:
    #             meta = self._get_disk_category_file_meta(path)
    #             if meta: file_cache[path] = meta
    #         for path in move_cache_removals:
    #             file_cache.pop(path,None)
    #         for old_path,new_path,meta in move_cache_moves:
    #             if meta: file_cache[new_path] = meta
    #         for path in fallback_dirs:
    #             if path == site_path:
    #                 self._disk_category_set_dir_bucket(dir_cache,path,new_size)
    #             elif os.path.isdir(path):
    #                 self._disk_category_set_dir_bucket(
    #                     dir_cache,path,self._get_disk_path_size(path))
    #         self._disk_category_prune_sparse_cache(dir_cache,512)
    #         return max(0,int(new_size))

    #     # 目录 bucket 已存在时，用最小父目录 du 的差值修正 unit 总量
    #     for path in fallback_dirs:
    #         had_dir_bucket = path in original_dir_cache
    #         new_dir_size = self._get_disk_path_size(path) if os.path.isdir(path) else 0
    #         directory_delta = self._disk_category_set_dir_bucket(dir_cache,path,new_dir_size)
    #         if had_dir_bucket:
    #             total_delta += directory_delta
    #         for event_path in path_events:
    #             if self._is_formatted_path_in_mount(event_path,path):
    #                 meta = self._get_disk_category_file_meta(event_path)
    #                 if meta: file_cache[event_path] = meta
    #                 else: file_cache.pop(event_path,None)

    #     for path in move_cache_removals:
    #         file_cache.pop(path,None)
    #     for old_path,new_path,meta in move_cache_moves:
    #         if meta: file_cache[new_path] = meta

    #     self._disk_category_prune_sparse_cache(file_cache,4096)
    #     self._disk_category_prune_sparse_cache(dir_cache,512)
    #     return max(0,int(old_size) + int(total_delta))

    # # 按分类读取 dirty、应用增量或 fallback，并汇总四个分类结果
    # def _calculate_disk_category_stats(self,disk_info,previous_result=None,dirty_sites=None,force_full=False):
    #     # 先创建当前磁盘的默认结果，并规范化输入状态
    #     stats = self._get_disk_category_default_stats(disk_info)
    #     mount_paths = sorted(stats.keys(),key=lambda x: len(str(x).rstrip('/')),reverse=True)
    #     if not mount_paths: return stats
    #     previous_result = previous_result if isinstance(previous_result,dict) else {}
    #     dirty_state = dirty_sites if isinstance(dirty_sites,dict) else {}
    #     dirty_categories = dirty_state.get('categories')
    #     if not isinstance(dirty_categories,dict):
    #         dirty_categories = {'project_files_size': {
    #             'force_full': bool(dirty_state.get('force_full',False)),
    #             'sites': dirty_state.get('sites',{}) if isinstance(dirty_state.get('sites'),dict) else {}}}
    #     force_values = force_full if isinstance(force_full,dict) else {
    #         category: bool(force_full) for category in self._get_disk_category_fields()}

    #     # 根据当前路径配置生成分类 unit 列表
    #     path_info = self._get_disk_category_paths()
    #     units = self._get_disk_category_units(path_info)
    #     category_units = {category:[] for category in self._get_disk_category_fields()}
    #     for value in units:
    #         category_units[value['category']].append(value['unit_path'])

    #     # 将 dirty site 映射到实际分类 unit，并收集本轮所有事件
    #     changes = {}
    #     all_events = []
    #     for category in self._get_disk_category_fields():
    #         current_dirty = dirty_categories.get(category,{})
    #         sites = current_dirty.get('sites',{}) if isinstance(current_dirty,dict) else {}
    #         category_changes = {}
    #         for site_path,payload in sites.items():
    #             site_path = self._format_disk_path(site_path)
    #             unit_path = next((path for path in category_units[category]
    #                               if self._is_formatted_path_in_mount(site_path,path)),'')
    #             if not unit_path or not isinstance(payload,dict): continue
    #             current = category_changes.setdefault(unit_path,{'force_site': False,'events': []})
    #             current['force_site'] = current['force_site'] or bool(payload.get('force_site'))
    #             for event in payload.get('events',[]) if isinstance(payload.get('events'),list) else []:
    #                 if not isinstance(event,dict): continue
    #                 event = event.copy()
    #                 event['category'] = category
    #                 event['site'] = unit_path
    #                 current['events'].append(event)
    #                 all_events.append(event)
    #         changes[category] = category_changes

    #     # 按 rename cookie 配对 MOVED_FROM 和 MOVED_TO
    #     move_values = {}
    #     for event in all_events:
    #         cookie = int(event.get('cookie',0))
    #         mask = int(event.get('mask',0))
    #         if not cookie or not mask & (0x40 | 0x80): continue
    #         pair = move_values.setdefault(cookie,[None,None])
    #         if mask & 0x40: pair[0] = event
    #         if mask & 0x80: pair[1] = event
    #     move_pairs = {cookie: pair for cookie,pair in move_values.items()}

    #     # 逐分类读取 SQLite baseline、文件缓存和 JSON 目录 bucket
    #     for category in self._get_disk_category_fields():
    #         unit_paths = category_units[category]
    #         category_changes = changes.get(category,{})
    #         category_force = bool(force_values.get(category,False))
    #         signature = self._disk_category_signature(unit_paths)
    #         db_buckets = {}
    #         for row in self._disk_category_db_query(
    #                 'SELECT `unit_path`,`size` FROM `disk_category_stats` WHERE `category`=? AND `initialized`=1',
    #                 (category,)) or []:
    #             try: db_buckets[row['unit_path']] = max(0,int(row['size']))
    #             except: pass
    #         db_file_cache = {}
    #         for row in self._disk_category_db_query(
    #                 'SELECT `path`,`unit_path`,`size`,`dev`,`inode`,`mtime_ns` FROM `disk_category_file_cache` WHERE `category`=?',
    #                 (category,)) or []:
    #             try:
    #                 db_file_cache[row['path']] = {
    #                     'size': max(0,int(row['size'])),'dev': int(row['dev']),'ino': int(row['inode']),
    #                     'nlink': 1,'mtime_ns': int(row['mtime_ns']),
    #                     'unit_path': row['unit_path'],'time': time.time()
    #                 }
    #             except: pass

    #         old_buckets = {}
    #         new_buckets = {mount_path:{} for mount_path in stats}
    #         file_caches = {}
    #         dir_caches = {}
    #         for mount_path in stats:
    #             current = previous_result.get(mount_path,{})
    #             old_buckets[mount_path] = {
    #                 path:size for path,size in db_buckets.items()
    #                 if self._get_formatted_path_mount(path,mount_paths) == mount_path}
    #             file_caches[mount_path] = {
    #                 path:meta for path,meta in db_file_cache.items()
    #                 if self._get_formatted_path_mount(path,mount_paths) == mount_path}
    #             all_dir_caches = current.get('_disk_category_dir_buckets',{}) if isinstance(current,dict) else {}
    #             dir_value = all_dir_caches.get(category,{}) if isinstance(all_dir_caches,dict) else {}
    #             if category == 'project_files_size' and not dir_value and isinstance(current,dict):
    #                 dir_value = current.get('_project_dir_buckets',{})
    #             dir_caches[mount_path] = self._normalize_disk_category_dir_cache(dir_value)

    #         # 对每个 unit 选择全量 du、复用旧值或应用本轮增量
    #         for path in unit_paths:
    #             mount_path = self._get_formatted_path_mount(path,mount_paths)
    #             if not mount_path: continue
    #             old_size = old_buckets.get(mount_path,{}).get(path)
    #             try:
    #                 if category_force or old_size is None:
    #                     # 没有可靠 baseline 或被强制刷新时重建整个 unit
    #                     path_size = self._get_disk_path_size(path,strict=True)
    #                     for cache in (file_caches[mount_path],dir_caches[mount_path]):
    #                         for cache_path in list(cache):
    #                             if self._is_path_in_mount(cache_path,path): cache.pop(cache_path,None)
    #                 elif path not in category_changes:
    #                     # 没有 dirty 事件时直接复用 SQLite 中的 unit 大小
    #                     path_size = old_size
    #                 else:
    #                     # 有事件时进入文件差值、目录 fallback 或 unit fallback
    #                     path_size = self._apply_disk_category_project_changes(
    #                         path,old_size,category_changes[path],file_caches[mount_path],
    #                         dir_caches[mount_path],move_pairs)
    #                 new_buckets[mount_path][path] = max(0,int(path_size))
    #             except:
    #                 self._mark_disk_category_dirty(path,category)
    #                 public.print_log('[Disk category stats] Failed to update {} path [{}]: {}'.format(
    #                     category,path,public.get_error_info()),'ERROR')
    #                 raise

    #         # 只有 baseline 变化或本轮有事件时才回写 SQLite 状态
    #         if category_force or category_changes or set(db_buckets) != set(unit_paths):
    #             self._save_disk_category_project_state(new_buckets,file_caches,category)
    #         for mount_path in stats:
    #             stats[mount_path][category] = sum(new_buckets[mount_path].values())
    #             stats[mount_path].setdefault('_disk_category_dir_buckets',{})[category] = dir_caches[mount_path]
    #             stats[mount_path].setdefault('_disk_category_paths_signatures',{})[category] = signature
    #             if category == 'project_files_size':
    #                 stats[mount_path]['_project_dir_buckets'] = dir_caches[mount_path]
    #                 stats[mount_path]['_project_paths_signature'] = signature

    #     # 用挂载点已用空间减去四类已分类大小得到 Other Files
    #     for disk in disk_info:
    #         mount_path = disk.get('path')
    #         if mount_path not in stats: continue
    #         try: used_size = int(disk['size'][1]) * 1024
    #         except: used_size = 0
    #         classified_size = sum(int(stats[mount_path].get(field,0))
    #                               for field in self._get_disk_category_fields())
    #         stats[mount_path]['other_files_size'] = max(0,used_size - classified_size)
    #     return stats
    # # 读取接口使用的磁盘分类结果，不在接口请求中触发刷新
    # def _get_disk_category_stats(self,disk_info):
    #     return self._read_disk_category_stats(disk_info)

    # # 使用 du 获取目录逻辑大小，失败时回退到 Python 统计
    # def _get_disk_path_size(self,path,strict=False):
    #     try:
    #         import shutil
    #         import subprocess
    #         command = ['du','-sB1','--apparent-size','--',path]
    #         # 顺序扫描，降低 CPU 和 IO 优先级，不限制执行时长
    #         if shutil.which('nice'): command = ['nice','-n','19'] + command
    #         if shutil.which('ionice'): command = ['ionice','-c','3'] + command
    #         output = subprocess.check_output(command,stderr=subprocess.STDOUT)
    #         return int(output.split(None,1)[0])
    #     except:
    #         # 全量必须全部 du 成功，不能将不完整的 Python 扫描当成新基线
    #         if strict: raise
    #         public.print_log('[Disk category stats] Failed to scan path with du [{}], fallback to Python: {}'.format(
    #             path,public.get_error_info()),'WARNING')
    #         return public.get_path_size(path)

    # # 由独立任务进程执行的磁盘分类统计刷新入口
    # def refresh_disk_category_stats(self):
    #     lock_file = None
    #     flock = None
    #     fallback_lock = False
    #     dirty_snapshot = {'version': 3,'categories': {},'_db_rows': []}
    #     try:
    #         if not self.is_disk_category_stats_enabled(): return True
    #         # 先获取刷新锁，避免多个 task 同时读取和更新同一份状态
    #         lock_path = self._get_disk_category_lock_path()
    #         lock_file = open(lock_path,'a+')
    #         try:
    #             import fcntl
    #             flock = fcntl
    #             flock.flock(lock_file.fileno(),flock.LOCK_EX | flock.LOCK_NB)
    #         except ImportError:
    #             if not public.progress_acquire_lock(lock_path):
    #                 public.print_log('[Disk category stats] Failed to acquire task lock: {}'.format(lock_path),'WARNING')
    #                 return False
    #             fallback_lock = True
    #         except OSError:
    #             public.print_log('[Disk category stats] Failed to acquire task lock: {}'.format(
    #                 public.get_error_info()),'WARNING')
    #             return False

    #         # 读取当前磁盘和分类 unit，并确认长期 watcher 状态
    #         disk_info = self.GetDiskInfo2(False)
    #         if not disk_info:
    #             public.print_log('[Disk category stats] Failed to get disk information.','ERROR')
    #             return False
    #         units = self._get_disk_category_units()
    #         watcher_ready = self._ensure_disk_category_inotify(units,False)
    #         # 读取上一轮 JSON 和本轮 dirty snapshot
    #         previous_result = self._get_disk_category_raw_result()
    #         dirty_snapshot = self._take_disk_category_dirty_sites(units)
    #         category_units = {category:[] for category in self._get_disk_category_fields()}
    #         for value in units: category_units[value['category']].append(value['unit_path'])
    #         # 按分类判断是否缺少 baseline、路径变化或收到 FORCE_FULL
    #         force_full = {}
    #         for category in self._get_disk_category_fields():
    #             current_dirty = dirty_snapshot.get('categories',{}).get(category,{})
    #             force_full[category] = (
    #                 not self._disk_category_cache_ready(
    #                     category,category_units[category],previous_result,disk_info) or
    #                 self._disk_category_paths_changed(
    #                     category,previous_result,category_units[category]) or
    #                 bool(current_dirty.get('force_full',False)))
    #         # 全量时间与结果一起原子保存；旧结果没有该字段时重新建立完整基线
    #         try:
    #             last_full_scan_time = min(int(value.get('last_full_scan_time',0))
    #                                       for value in previous_result.values())
    #         except:
    #             last_full_scan_time = 0
    #         full_scan = (not watcher_ready or any(force_full.values()) or
    #                      last_full_scan_time <= 0 or
    #                      time.time() - last_full_scan_time >= 30 * 24 * 3600)
    #         if full_scan:
    #             force_full = {category:True for category in self._get_disk_category_fields()}
    #         # 全量与增量只选一个分支，全量当晚不再应用 dirty 差值
    #         stats = self._calculate_disk_category_stats(
    #             disk_info,previous_result,dirty_snapshot,force_full)
    #         if full_scan: last_full_scan_time = int(time.time())
    #         # 为本轮所有挂载点写入统一更新时间
    #         updated_at = time.strftime('%Y-%m-%d %H:%M:%S',time.localtime())
    #         for disk_stats in stats.values():
    #             disk_stats['updated_at'] = updated_at
    #             disk_stats['last_full_scan_time'] = last_full_scan_time
    #         # 先写临时文件并原子替换，避免接口读到半份 JSON
    #         result_file = self._get_disk_category_result_path()
    #         temp_file = '{}.tmp.{}'.format(result_file,os.getpid())
    #         with open(temp_file,'w') as fp:
    #             json.dump(stats,fp)
    #             fp.flush()
    #             os.fsync(fp.fileno())
    #         os.replace(temp_file,result_file)
    #         # 结果落盘成功后，按 id 和 updated_at 条件清理本轮 dirty
    #         if not self._finish_disk_category_dirty_snapshot(dirty_snapshot):
    #             self._update_disk_category_dirty_file(force_full=True)
    #         if any(force_full.values()):
    #             self._set_disk_category_watcher_initialized()
    #         return True
    #     except:
    #         # 失败时恢复本轮快照，并追加 FORCE_FULL 保障下一轮校准
    #         try:
    #             public.print_log('[Disk category stats] Refresh failed: {}'.format(public.get_error_info()),'ERROR')
    #         except:
    #             pass
    #         try:
    #             if 'temp_file' in locals() and os.path.exists(temp_file): os.remove(temp_file)
    #         except:
    #             pass
    #         self._restore_disk_category_dirty_snapshot(dirty_snapshot)
    #         self._update_disk_category_dirty_file(force_full=True)
    #         return False
    #     finally:
    #         if flock and lock_file:
    #             try: flock.flock(lock_file.fileno(),flock.LOCK_UN)
    #             except: pass
    #         if fallback_lock:
    #             public.progress_release_lock(self._get_disk_category_lock_path())
    #         if lock_file:
    #             try: lock_file.close()
    #             except: pass
    # # 读取指定挂载点的磁盘使用报警配置
    # def _get_disk_usage_alarm(self,path):
    #     data = {'usage_alarm_enabled': False,'usage_alarm_threshold': '80%'}
    #     try:
    #         filename = os.path.join(public.get_panel_path(),'data/mod_push_data/task.json')
    #         if not os.path.exists(filename): return data
    #         task_list = json.loads(public.readFile(filename))
    #         for task in task_list:
    #             if task.get('source') != 'system_disk' or task.get('keyword') != path: continue
    #             task_data = task.get('task_data',{})
    #             if int(task_data.get('cycle',0)) == 2:
    #                 data['usage_alarm_enabled'] = bool(task.get('status',False))
    #                 data['usage_alarm_threshold'] = '{}%'.format(int(task_data.get('count',80)))
    #             break
    #     except:
    #         pass
    #     return data
    # # 根据磁盘使用率和报警阈值计算接口返回状态
    # def _get_disk_status(self,disk,alarm_info):
    #     try:
    #         if not alarm_info.get('usage_alarm_enabled'): return 'Normal'
    #         usage = float(str(disk['size'][3]).replace('%',''))
    #         threshold = float(str(alarm_info.get('usage_alarm_threshold','80%')).replace('%',''))
    #         if usage >= threshold: return 'Warning'
    #     except:
    #         pass
    #     return 'Normal'
    # # 将内部字节数转换为兼容接口的 GB 字符串
    # def _format_disk_size(self,size):
    #     try:
    #         return '{}G'.format(round(int(size) / 1073741824,2))
    #     except:
    #         return '0.0G'

    # # 将五类磁盘大小、更新时间和报警字段写入单个磁盘对象
    # def _add_disk_category_fields(self,disk,category_stats):
    #     stats = category_stats.get(disk.get('path'),{})
    #     alarm_info = self._get_disk_usage_alarm(disk.get('path'))
    #     disk['project_files_size'] = self._format_disk_size(stats.get('project_files_size',0))
    #     disk['databases_size'] = self._format_disk_size(stats.get('databases_size',0))
    #     disk['backups_size'] = self._format_disk_size(stats.get('backups_size',0))
    #     disk['system_logs_size'] = self._format_disk_size(stats.get('system_logs_size',0))
    #     disk['other_files_size'] = self._format_disk_size(stats.get('other_files_size',0))
    #     disk['updated_at'] = stats.get('updated_at','')
    #     disk['status'] = self._get_disk_status(disk,alarm_info)
    #     disk['usage_alarm_enabled'] = alarm_info['usage_alarm_enabled']
    #     disk['usage_alarm_threshold'] = alarm_info['usage_alarm_threshold']


    # # 获取磁盘IO开销数据
    def get_disk_iostat(self):
        iokey = 'iostat'
        diskio = cache.get(iokey)
        mtime = int(time.time())
        if not diskio:
            diskio = {}
            diskio['info'] = None
            diskio['time'] = mtime
        diskio_1 = diskio['info']
        stime = mtime - diskio['time']
        if not stime: stime = 1
        diskInfo = {}
        diskInfo['ALL'] = {}
        diskInfo['ALL']['read_count'] = 0
        diskInfo['ALL']['write_count'] = 0
        diskInfo['ALL']['read_bytes'] = 0
        diskInfo['ALL']['write_bytes'] = 0
        diskInfo['ALL']['read_time'] = 0
        diskInfo['ALL']['write_time'] = 0
        diskInfo['ALL']['read_merged_count'] = 0
        diskInfo['ALL']['write_merged_count'] = 0
        try:
            if os.path.exists('/proc/diskstats'):
                diskio_2 = psutil.disk_io_counters(perdisk=True)
                if not diskio_1:
                    diskio_1 = diskio_2
                for disk_name in diskio_2.keys():
                    diskInfo[disk_name] = {}
                    diskInfo[disk_name]['read_count']   = int((diskio_2[disk_name].read_count - diskio_1[disk_name].read_count) / stime)
                    diskInfo[disk_name]['write_count']  = int((diskio_2[disk_name].write_count - diskio_1[disk_name].write_count) / stime)
                    diskInfo[disk_name]['read_bytes']   = int((diskio_2[disk_name].read_bytes - diskio_1[disk_name].read_bytes) / stime)
                    diskInfo[disk_name]['write_bytes']  = int((diskio_2[disk_name].write_bytes - diskio_1[disk_name].write_bytes) / stime)
                    diskInfo[disk_name]['read_time']    = int((diskio_2[disk_name].read_time - diskio_1[disk_name].read_time) / stime)
                    diskInfo[disk_name]['write_time']   = int((diskio_2[disk_name].write_time - diskio_1[disk_name].write_time) / stime)
                    diskInfo[disk_name]['read_merged_count'] = int((diskio_2[disk_name].read_merged_count - diskio_1[disk_name].read_merged_count) / stime)
                    diskInfo[disk_name]['write_merged_count'] = int((diskio_2[disk_name].write_merged_count - diskio_1[disk_name].write_merged_count) / stime)

                    diskInfo['ALL']['read_count'] += diskInfo[disk_name]['read_count']
                    diskInfo['ALL']['write_count'] += diskInfo[disk_name]['write_count']
                    diskInfo['ALL']['read_bytes'] += diskInfo[disk_name]['read_bytes']
                    diskInfo['ALL']['write_bytes'] += diskInfo[disk_name]['write_bytes']
                    if diskInfo['ALL']['read_time'] < diskInfo[disk_name]['read_time']:
                        diskInfo['ALL']['read_time'] = diskInfo[disk_name]['read_time']
                    if diskInfo['ALL']['write_time'] < diskInfo[disk_name]['write_time']:
                        diskInfo['ALL']['write_time'] = diskInfo[disk_name]['write_time']
                    diskInfo['ALL']['read_merged_count'] += diskInfo[disk_name]['read_merged_count']
                    diskInfo['ALL']['write_merged_count'] += diskInfo[disk_name]['write_merged_count']

                cache.set(iokey,{'info':diskio_2,'time':mtime})
        except:
            return diskInfo
        return diskInfo


    #清理系统垃圾
    def ClearSystem(self,get):
        count = total = 0
        tmp_total,tmp_count = self.ClearMail()
        count += tmp_count
        total += tmp_total
        tmp_total,tmp_count = self.ClearOther()
        count += tmp_count
        total += tmp_total
        return count,total

    #清理邮件日志
    def ClearMail(self):
        rpath = '/var/spool'
        total = count = 0
        import shutil
        con = ['cron','anacron','mail']
        for d in os.listdir(rpath):
            if d in con: continue
            dpath = rpath + '/' + d
            time.sleep(0.2)
            num = size = 0
            for n in os.listdir(dpath):
                filename = dpath + '/' + n
                fsize = os.path.getsize(filename)
                size += fsize
                if os.path.isdir(filename):
                    shutil.rmtree(filename)
                else:
                    os.remove(filename)
                print('\t\033[1;32m[OK]\033[0m')
                num += 1
            total += size
            count += num
        return total,count

    #清理其它
    def ClearOther(self):
        clearPath = [
                     {'path':'/www/server/panel','find':'testDisk_'},
                     {'path':'/www/wwwlogs','find':'log'},
                     {'path':'/tmp','find':'panelBoot.pl'},
                     {'path':'/www/server/panel/install','find':'.rpm'}
                     ]

        total = count = 0
        for c in clearPath:
            for d in os.listdir(c['path']):
                if d.find(c['find']) == -1: continue
                filename = c['path'] + '/' + d
                if os.path.isdir(filename): continue
                fsize = os.path.getsize(filename)
                total += fsize
                os.remove(filename)
                count += 1
        public.serviceReload()
        filename = '/www/server/nginx/off'
        if os.path.exists(filename): os.remove(filename)
        public.ExecShell('echo > /tmp/panelBoot.pl')
        return total,count

    # 组装系统概览接口；磁盘分类只读取已落盘 JSON，不在请求中刷新或执行 du
    def GetNetWork(self,get=None):
        cache_timeout = 86400
        otime = cache.get("otime")
        ntime = time.time()
        networkInfo = {}
        networkInfo['hostname'] = public.get_hostname()
        networkInfo['reboot_status'] = self.reboot_status()
        networkInfo['network'] = {}
        networkInfo['upTotal'] = 0
        networkInfo['downTotal'] = 0
        networkInfo['up'] = 0
        networkInfo['down'] = 0
        networkInfo['downPackets'] = 0
        networkInfo['upPackets'] = 0

        try:
            networkIo_list = psutil.net_io_counters(pernic = True)

            for net_key in networkIo_list.keys():
                networkIo = networkIo_list[net_key][:4]
                up_key = "{}_up".format(net_key)
                down_key = "{}_down".format(net_key)
                otime_key = "otime"

                if not otime:
                    otime = time.time()

                    cache.set(up_key,networkIo[0],cache_timeout)
                    cache.set(down_key,networkIo[1],cache_timeout)
                    cache.set(otime_key,otime ,cache_timeout)

                networkInfo['network'][net_key] = {}
                up = cache.get(up_key)
                down = cache.get(down_key)
                time_diff = ntime - otime
                if time_diff <= 0:
                    time_diff = 1
                if not up:
                    up = networkIo[0]
                if not down:
                    down = networkIo[1]
                networkInfo['network'][net_key]['upTotal']   = networkIo[0]
                networkInfo['network'][net_key]['downTotal'] = networkIo[1]
                networkInfo['network'][net_key]['up']        = round(float(networkIo[0] -  up) / 1024 / time_diff,2)
                networkInfo['network'][net_key]['down']      = round(float(networkIo[1] - down) / 1024 / time_diff,2)
                networkInfo['network'][net_key]['downPackets'] =networkIo[3]
                networkInfo['network'][net_key]['upPackets']   =networkIo[2]

                networkInfo['upTotal'] += networkInfo['network'][net_key]['upTotal']
                networkInfo['downTotal'] += networkInfo['network'][net_key]['downTotal']
                networkInfo['up'] += networkInfo['network'][net_key]['up']
                networkInfo['down'] += networkInfo['network'][net_key]['down']
                networkInfo['downPackets'] += networkInfo['network'][net_key]['downPackets']
                networkInfo['upPackets'] += networkInfo['network'][net_key]['upPackets']

                cache.set(up_key,networkIo[0],cache_timeout)
                cache.set(down_key,networkIo[1],cache_timeout)
                cache.set(otime_key, time.time(),cache_timeout)
        except:
            networkInfo['network'] = {}
            networkInfo['upTotal'] = 0
            networkInfo['downTotal'] = 0
            networkInfo['up'] = 0
            networkInfo['down'] = 0
            networkInfo['downPackets'] = 0
            networkInfo['upPackets'] = 0


        if get != False:
            # 获取原始磁盘列表
            networkInfo['cpu'] = self.GetCpuInfo(1)
            networkInfo['cpu_times'] = self.get_cpu_times()
            networkInfo['load'] = self.GetLoadAverage(get)
            networkInfo['mem'] = self.GetMemInfo(get)['message']
            networkInfo['version'] = session['version']
            disk_list = []
            raw_disk_list = self.GetDiskInfo2(False)
            # 发布前临时禁用磁盘分类统计结果读取，后续上线时恢复下方调用
            # disk_category_stats = self._get_disk_category_stats(raw_disk_list)
            # 格式化原有容量字段
            for disk in raw_disk_list:
                if 'path' in disk and disk['path'] == "/sys/firmware/efi/efivars": continue
                disk = disk.copy()
                disk['size'] = list(disk.get('size',[]))
                disk['inodes'] = list(disk.get('inodes',[]))
                # 发布前临时禁用磁盘分类及相关状态字段组装，后续上线时恢复下方调用
                # self._add_disk_category_fields(disk,disk_category_stats)
                disk['size'].append(int(disk['size'][0]) - (int(disk['size'][1]) + int(disk['size'][2])))  # 计算系统占用
                disk['size'] = list(map(lambda num: f"{round(int(num) / 1048576, 2)}G" if str(num).isdigit() and str(num).find('G') == -1 else num, disk['size']))
                disk['inodes'] = list(map(lambda num: f"{round(int(num) / 1048576, 2)}G" if str(num).isdigit() and str(num).find('G') == -1 else num, disk['inodes']))
                disk_list.append(disk)
            networkInfo['disk'] = disk_list

        networkInfo['title'] = self.GetTitle()
        networkInfo['time'] = self.GetBootTime()
        networkInfo['site_total'] = public.M('sites').count()
        networkInfo['ftp_total'] = public.M('ftps').count()
        networkInfo['database_total'] = public.M('databases').count()
        networkInfo['system'] = self.GetSystemVersion()
        networkInfo['simple_system'] = networkInfo['system'].split(' ')[0] + ' ' + re.search(r'\d+', networkInfo['system']).group()
        networkInfo['installed'] = self.CheckInstalled()
        import panel_ssl_v2 as panelSSL
        user_info = panelSSL.panelSSL().GetUserInfo(None)
        networkInfo['user_info'] = user_info['message']
        networkInfo['user_info']['status'] = user_info['status']
        networkInfo['up'] = round(float(networkInfo['up']),2)
        networkInfo['down'] = round(float(networkInfo['down']),2)
        networkInfo['iostat'] = self.get_disk_iostat()

        return public.return_message(0,0,networkInfo)


    def get_cpu_times(self):
        skey = 'cpu_times'
        data = cache.get(skey)
        if data:return data
        try:
            data = {}
            cpu_times_p  = psutil.cpu_times_percent()
            data['user'] = cpu_times_p.user
            data['nice'] = cpu_times_p.nice
            data['system'] = cpu_times_p.system
            data['idle'] = cpu_times_p.idle
            data['iowait'] = cpu_times_p.iowait
            data['irq'] = cpu_times_p.irq
            data['softirq'] = cpu_times_p.softirq
            data['steal'] = cpu_times_p.steal
            data['guest'] = cpu_times_p.guest
            data['guest_nice'] = cpu_times_p.guest_nice
            data['total_processes'] = 0
            data['active_processes'] = 0
            for pid in psutil.pids():
                try:
                    p = psutil.Process(pid)
                    if p.status() == 'running':
                        data['active_processes'] += 1
                except:
                    continue
                data['total_processes'] += 1

            cache.set(skey,data,60)
        except: return None
        return data




    # 对外 API 入口，统一转发到系统概览接口
    def GetNetWorkApi(self,get=None):
        return self.GetNetWork()

    #检查是否安装任何
    def CheckInstalled(self):
        import os
        path = os.path.join(public.get_panel_path(), 'data', 'guide_marking.pl')
        if os.path.exists(path):
            return True

        # 如果引导页正在安装，即继续弹窗保持同步
        from panel_site_v2 import panelSite
        res_log = panelSite().get_general_progress(public.to_dict_obj({'type': 'guide_page'}))
        if res_log['status'] == 0 and res_log['message'].get('status') == 0:
            return False

        checks = ['nginx','apache','php','pure-ftpd','mysql']
        for name in checks:
            filename = public.GetConfigValue('root_path') + "/server/" + name
            if os.path.exists(filename):
                return True
        return False

    def GetNetWorkOld(self):
        #取网络流量信息
        import time;
        pnet = public.readFile('/proc/net/dev')
        rep = r'([^\s]+):[\s]{0,}(\d+)\s+(\d+)\s+(\d+)\s+(\d+)\s+(\d+)\s+(\d+)\s+(\d+)\s+(\d+)\s+(\d+)\s+(\d+)\s+(\d+)'
        pnetall = re.findall(rep,pnet)
        networkInfo = {}
        networkInfo['upTotal'] = networkInfo['downTotal'] = networkInfo['up'] = networkInfo['down'] = networkInfo['downPackets'] = networkInfo['upPackets'] = 0


        for pnetInfo in pnetall:
            if pnetInfo[0] == 'io': continue
            networkInfo['downTotal'] += int(pnetInfo[1])
            networkInfo['downPackets'] += int(pnetInfo[2])
            networkInfo['upTotal'] += int(pnetInfo[9])
            networkInfo['upPackets'] += int(pnetInfo[10])

        cache_timeout = 86400
        otime = cache.get("otime")
        if not otime:
            otime = time.time()
            cache.set('up',networkInfo['upTotal'],cache_timeout)
            cache.set('down',networkInfo['downTotal'],cache_timeout)
            cache.set('otime',otime ,cache_timeout)

        ntime = time.time()
        time_diff = ntime - otime
        if time_diff <= 0:
            time_diff = 1

        tmpDown = networkInfo['downTotal'] - cache.get("down")
        tmpUp = networkInfo['upTotal'] - cache.get("up")
        networkInfo['down'] = str(round(float(tmpDown) / 1024 / time_diff,2))
        networkInfo['up']   = str(round(float(tmpUp) / 1024 / time_diff,2))
        if networkInfo['down'] < 0: networkInfo['down'] = 0
        if networkInfo['up'] < 0: networkInfo['up'] = 0

        otime = time.time()
        cache.set('up',networkInfo['upTotal'],cache_timeout)
        cache.set('down',networkInfo['downTotal'],cache_timeout)
        cache.set('otime',ntime ,cache_timeout)

        networkInfo['cpu'] = self.GetCpuInfo()
        return networkInfo


    #取IO读写信息
    def get_io_info(self,get = None):
        io_disk = psutil.disk_io_counters()
        ioTotal = {}
        ioTotal['write'] = self.get_io_write(io_disk.write_bytes)
        ioTotal['read'] = self.get_io_read(io_disk.read_bytes)
        return ioTotal

    #取IO写
    def get_io_write(self,io_write):
        disk_io_write = 0
        old_io_write = cache.get('io_write')
        if not old_io_write:
            cache.set('io_write',io_write)
            return disk_io_write

        old_io_time = cache.get('io_time')
        new_io_time = time.time()
        if not old_io_time: old_io_time = new_io_time
        io_end = (io_write - old_io_write)
        time_end = (time.time() - old_io_time)
        if io_end > 0:
            if time_end < 1: time_end = 1
            disk_io_write = io_end / time_end
        cache.set('io_write',io_write)
        cache.set('io_time',new_io_time)
        if disk_io_write > 0: return int(disk_io_write)
        return 0

    #取IO读
    def get_io_read(self,io_read):
        disk_io_read = 0
        old_io_read = cache.get('io_read')
        if not old_io_read:
            cache.set('io_read',io_read)
            return disk_io_read
        old_io_time = cache.get('io_time')
        new_io_time = time.time()
        if not old_io_time: old_io_time = new_io_time
        io_end = (io_read - old_io_read)
        time_end = (time.time() - old_io_time)
        if io_end > 0:
            if time_end < 1: time_end = 1
            disk_io_read = io_end / time_end
        cache.set('io_read',io_read)
        if disk_io_read > 0: return int(disk_io_read)
        return 0

    #检查并修复MySQL目录权限
    def __check_mysql_path(self):
        try:
            #获取datadir路径
            mypath = '/etc/my.cnf'
            if not os.path.exists(mypath): return False
            public.set_mode(mypath,644)
            mycnf = public.readFile(mypath)
            tmp = re.findall(r'datadir\s*=\s*(.+)',mycnf)
            if not tmp: return False
            datadir = tmp[0]

            #可以被启动的权限
            accs = ['755','777']

            #处理data目录权限
            mode_info = public.get_mode_and_user(datadir)
            if not mode_info['mode'] in accs or mode_info['user'] != 'mysql':
                public.ExecShell('chmod 755 ' + datadir)
                public.ExecShell('chown -R mysql:mysql ' + datadir)

            #递归处理父目录权限
            datadir = os.path.dirname(datadir)
            while datadir != '/':
                if datadir == '/': break
                mode_info = public.get_mode_and_user(datadir)
                if not mode_info['mode'] in accs:
                    public.ExecShell('chmod 755 ' + datadir)
                datadir = os.path.dirname(datadir)
        except: pass

    @staticmethod
    def _operate_manual_flag(get) -> None:
        alarm_services = [
            'nginx', 'apache', 'httpd', 'openlitespeed',
            'mysqld', 'mongodb', 'redis', 'memcache',
            'pure-ftpd',
        ]
        if get.name in alarm_services:
            from script.restart_services import manual_flag
            name_map = {
                "mysqld": "mysql",
                "httpd": "apache",
            }
            server_name = name_map[get.name] if name_map.get(get.name) else get.name
            manual_flag(server_name=server_name, open_=get.type)

    def ServiceAdmin(self,get=None):
        # 校验参数
        try:
            get.validate([
                Param('name').String(),
                Param('type').String(),
            ], [
                public.validate.trim_filter(),
            ])
        except Exception as ex:
            public.print_log("error info: {}".format(ex))
            return public.return_message(-1, 0, str(ex))
        # 提前执行Daemon服务标记
        self._operate_manual_flag(get)
        #服务管理
        if get.name == "mysql": # 使用规范服务名
            get.name = "mysqld" # 兼容旧代码

        if get.name == 'mysqld':
            public.CheckMyCnf()
            self.__check_mysql_path()

        if get.name.find('webserver') != -1:
            get.name = public.get_webserver()

        # 各种特殊处理兼容, 提前return

        if get.name == 'fail2ban':
            try:
                public.sys_path_append("plugin/fail2ban")
                from plugin.fail2ban.fail2ban_main import fail2ban_main
                res = fail2ban_main().set_fail2ban_status(get)
                if res.get("status") is True:
                    return public.return_message(0, 0, public.lang("Executed successfully!"))
                return public.return_message(-1, 0, res.get("msg", "Service stop failed!"))
            except Exception as e:
                public.print_log("error info: {}".format(e))
                return public.return_message(-1, 0, str(e))

        if get.name == 'phpmyadmin':
            import ajax_v2
            get.status = 'True'
            ajax_v2.ajax().setPHPMyAdmin(get)
            return public.return_message(0, 0, public.lang("Executed successfully!"))

        if get.name == 'pdns':
            try:
                from ssl_dnsV2.dns_manager import DnsManager
                DnsManager().change_service_status(service_name="pdns", status=get.type)
                return public.return_message(0, 0, public.lang("Executed successfully!"))
            except Exception as e:
                public.print_log("error info: {}".format(e))
                return public.return_message(-1, 0, str(e))

        if get.name == 'openlitespeed':
            if get.type == 'stop':
                public.ExecShell('rm -f /tmp/lshttpd/*.sock* && /usr/local/lsws/bin/lswsctrl stop')
            elif get.type == 'start':
                public.ExecShell('rm -f /tmp/lshttpd/*.sock* && /usr/local/lsws/bin/lswsctrl start')
            elif get.type == 'restart':
                public.ExecShell('rm -f /tmp/lshttpd/*.sock* && /usr/local/lsws/bin/lswsctrl restart')
            else:
                public.ExecShell("/usr/local/lsws/bin/lswsctrl reload")
            return public.return_message(0, 0, public.lang("Executed successfully!"))

        #检查httpd配置文件
        if get.name == 'apache' or get.name == 'httpd':
            get.name = 'httpd'
            if not os.path.exists(self.setupPath+'/apache/bin/apachectl'): return public.return_message(-1, 0, public.lang("Execution failed, check if Apache installed"))
            vhostPath = self.setupPath + '/panel/vhost/apache'
            if not os.path.exists(vhostPath):
                public.ExecShell('mkdir ' + vhostPath)
                public.ExecShell('/etc/init.d/httpd start')

            if get.type == 'start':
                public.ExecShell('/etc/init.d/httpd stop')
                self.kill_port()

            result = public.ExecShell('ulimit -n 8192 ; ' + self.setupPath+'/apache/bin/apachectl -t')
            if result[1].find('Syntax OK') == -1:
                public.write_log_gettext("Software manager",'Execution failed: {}', (str(result),))
                return public.return_message(-1,0,f"Apache rule configuration error: <br><a style='color:red;'>{result[1].replace('\n','<br>')}</a>")

            if get.type == 'restart':
                public.ExecShell('pkill -9 httpd')
                public.ExecShell('/etc/init.d/httpd start')
                time.sleep(0.5)
                public.ExecShell('/etc/init.d/v-httpd restart')
                time.sleep(0.5)

        #检查nginx配置文件
        elif get.name == 'nginx':
            vhostPath = self.setupPath + '/panel/vhost/rewrite'
            if not os.path.exists(vhostPath): public.ExecShell('mkdir ' + vhostPath)
            if not os.path.exists("/dev/shm/nginx-cache/wp"):
                public.ExecShell('mkdir -p /dev/shm/nginx-cache/wp && chown -R www.www /dev/shm/nginx-cache')
            vhostPath = self.setupPath + '/panel/vhost/nginx'
            if not os.path.exists(vhostPath):
                public.ExecShell('mkdir ' + vhostPath)
                public.ExecShell('/etc/init.d/nginx start')

            result = public.ExecShell('ulimit -n 8192 ; '+self.setupPath+'/nginx/sbin/nginx -t -c '+self.setupPath+'/nginx/conf/nginx.conf')
            if result[1].find('perserver') != -1:
                limit = self.setupPath + '/nginx/conf/nginx.conf'
                nginxConf = public.readFile(limit)
                limitConf = "limit_conn_zone $binary_remote_addr zone=perip:10m;\n\t\tlimit_conn_zone $server_name zone=perserver:10m;"
                nginxConf = nginxConf.replace("#limit_conn_zone $binary_remote_addr zone=perip:10m;",limitConf)
                public.writeFile(limit,nginxConf)
                public.ExecShell('/etc/init.d/nginx start')
                return public.return_message(0, 0, public.lang("Configuration file mismatch caused by reinstalling Nginx fixed"))

            if result[1].find('proxy') != -1:
                import panelSite
                panelSite.panelSite().CheckProxy(get)
                public.ExecShell('/etc/init.d/nginx start')
                return public.return_message(0, 0, public.lang("Configuration file mismatch caused by reinstalling Nginx fixed"))

            #return result
            if result[1].find('successful') == -1:
                public.write_log_gettext("Software manager",'Execution failed: {}', (str(result),))
                return public.return_message(-1,0,"Nginx rule configuration error: <br><a style='color:red;'>{}</a>".format(result[1].replace("\n",'<br>'),))

            if get.type == 'start':
                self.kill_port()
                time.sleep(0.5)
        if get.name == 'redis':
            redis_init = '/etc/init.d/redis'
            if os.path.exists(redis_init):
                init_body = public.ReadFile(redis_init)
                if init_body.find('pkill -9 redis') == -1:
                    public.ExecShell("wget -O " + redis_init + " " + public.get_url() + '/init/redis.init')
                    public.ExecShell("chmod +x " + redis_init)

        #执行
        execStr = "/etc/init.d/"+get.name+" "+get.type
        if execStr == '/etc/init.d/pure-ftpd reload': execStr = self.setupPath+'/pure-ftpd/bin/pure-pw mkdb '+self.setupPath+'/pure-ftpd/etc/pureftpd.pdb'
        if execStr == '/etc/init.d/pure-ftpd start': public.ExecShell('pkill -9 pure-ftpd')
        if execStr == '/etc/init.d/tomcat reload': execStr = '/etc/init.d/tomcat stop && /etc/init.d/tomcat start'
        if execStr == '/etc/init.d/tomcat restart': execStr = '/etc/init.d/tomcat stop && /etc/init.d/tomcat start'

        if get.name != 'mysqld':
            result = public.ExecShell(execStr)
        else:
            public.ExecShell(execStr)
            result = []
            result.append('')
            result.append('')

        if result[1].find('nginx.pid') != -1:
            public.ExecShell('pkill -9 nginx && sleep 1')
            public.ExecShell('/etc/init.d/nginx start')
        if get.type != 'test':
            public.write_log_gettext("Software manager", 'Executed successfully [{}]!',(execStr,))

        if get.type != 'stop':
            n = 0
            num = 5
            while not self.check_service_status(get.name):
                time.sleep(0.5)
                n += 1
                if n > num: break

            if not self.check_service_status(get.name):
                if len(result[1]) > 1 and get.name != 'pure-ftpd' and get.name != 'redis':
                    return public.return_message(-1,0, '<p>failed to activate: <p>' + result[1].replace('\n','<br>'))
                else:
                    return public.return_message(-1, 0, public.lang("{} service failed to start", get.name))
        else:
            if self.check_service_status(get.name):
                return public.return_message(-1, 0, public.lang("Service stop failed!"))

        return public.return_message(0, 0, public.lang("Executed successfully!"))

    def check_service_status(self,name):
        '''
            @name 检查服务管理状态
            @author hwliang
            @param name<string> 服务名称
            @return bool
        '''
        if name in ['mysqld','mariadbd']:
            return public.is_mysql_process_exists()
        elif name == 'redis':
            return public.is_redis_process_exists()
        elif name == 'pure-ftpd':
            return public.is_pure_ftpd_process_exists()
        elif name.find('php-fpm') != -1:
            return public.is_php_fpm_process_exists(name)
        elif name == 'nginx':
            return public.is_nginx_process_exists()
        elif name in ['httpd','apache']:
            return public.is_httpd_process_exists()
        elif name == 'memcached':
            return public.is_memcached_process_exists()
        elif name == 'mongodb':
            return public.is_mongodb_process_exists()
        elif name == 'pgsql':
            return public.is_process_exists_by_exe('/www/server/pgsql/bin/postgres')
        else:
            return True

    def RestartServer(self,get):
        if not public.IsRestart(): return public.return_message(-1, 0, public.lang("Please run the program when all install tasks finished!"))
        public.ExecShell("sync && init 6 &")
        return public.return_message(0, 0, public.lang("Command sent successfully!"))

    def kill_port(self):
        public.ExecShell('pkill -9 httpd')
        public.ExecShell('pkill -9 nginx')
        public.ExecShell("kill -9 $(lsof -i :80|grep LISTEN|awk '{print $2}')")
        return True

    #释放内存
    def ReMemory(self,get):
        public.ExecShell('sync')
        scriptFile = 'script/rememory.sh'
        if not os.path.exists(scriptFile):
            public.downloadFile(public.GetConfigValue('home') + '/script/rememory.sh',scriptFile)
        public.ExecShell("/bin/bash " + self.setupPath + '/panel/' + scriptFile)
        return self.GetMemInfo()

    #重启面板
    def ReWeb(self,get):
        # 校验参数
        try:
            get.validate([
                Param('toUpdate').String(),
            ], [
                public.validate.trim_filter(),
            ])
        except Exception as ex:
            public.print_log("error info: {}".format(ex))
            return public.return_message(-1, 0, str(ex))

        public.ExecShell("/etc/init.d/bt start")
        public.writeFile('data/restart.pl','True')
        # 重启面板 默认开启系统监控
        # public.writeFile('data/control.conf', '30')
        return public.return_message(0, 0, public.lang("Panel restarted"))

    # todo 弃用, fun repair_panel 代替
    #修复面板
    def RepPanel(self,get):
        # 校验参数
        try:
            get.validate([
                Param('toUpdate').String(),
            ], [
                public.validate.trim_filter(),
            ])
        except Exception as ex:
            public.print_log("error info: {}".format(ex))
            return public.return_message(-1, 0, str(ex))

        public.writeFile('data/js_random.pl','1')
        public.ExecShell("wget --no-check-certificate -O update.sh " + public.get_url() + "/install/update_panel_en.sh && bash update.sh")
        self.ReWeb(None)
        return public.return_message(0,0,True)

    #升级到专业版
    def UpdatePro(self,get):
        public.ExecShell("wget --no-check-certificate -O update.sh " + public.get_url() + "/install/update_panel_en.sh && bash update.sh")
        self.ReWeb(None)
        return True

    # ============== New 更新,修复面板 ======================
    @staticmethod
    def _has_py313() -> bool:
        import subprocess
        code = "import sys, urllib3, _sqlite3; print('%d.%d' % (sys.version_info.major, sys.version_info.minor))"
        now_env = os.path.join(public.get_panel_path(), "pyenv/bin/python3")
        pre_env = os.path.join(public.get_panel_path(), "pyenv313/bin/python3")
        for env in (now_env, pre_env):
            if not os.path.exists(env):
                continue
            try:
                ver = subprocess.check_output([env, "-c", code], text=True)
                if ver.strip() == "3.13":
                    return True
            except:
                pass
        return False
    
    @staticmethod
    def _normalize_version(version_str: str):
        try:
            tmp = version_str.split(".")
            if len(tmp) < 3:
                tmp += [0] * (3 - len(tmp))
            return int(tmp[0]), int(tmp[1]), int(tmp[2])
        except:
            return 0, 0, 0

    def _get_plugin_for_py313(self):
        config_file = os.path.join(public.get_panel_path(), "data/py313_plugins.json")
        m_time = 0
        if os.path.exists(config_file):
            m_time = os.path.getmtime(config_file)

        if m_time < time.time() - 3600:
            public.downloadFile('{}/install/update/py313_plugins.json'.format(public.get_url()), config_file)

        try:
            data = json.loads(public.readFile(config_file))
        except:
            data = []

        plugins = []
        plugin_path = os.path.join(public.get_panel_path(), "plugin")
        for i in data:
            if_file = os.path.join(plugin_path, i["name"], "info.json")
            if not os.path.exists(if_file):
                continue
            try:
                info = json.loads(public.readFile(if_file))
                lv = self._normalize_version(info.get("versions", "99.99"))
                nv = self._normalize_version(i.get("version", "0.0"))
                if lv < nv:
                    i["local_version"] = info["versions"]
                    plugins.append(i)
            except:
                continue
        plugins.sort(key=lambda x: x["level"])
        return  plugins

    def repair_panel(self, get):
        # ajax_v2 RepPanel
        ...

    def upgrade_panel(self, get):
        # ajax_v2 UpdatePanel
        ...

    def get_upgrade_log(self,get):
        """
        @name 获取更新日志
        """
        logPath = '/tmp/upgrade_panel.log'
        if not os.path.exists(logPath):
            return public.success_v2('')

        logs = public.GetNumLines(logPath, 1000)
        try:
            # 适配旧版的日志
            return json.loads(logs)
        except:
            pass

        if logs.find('Success: Panel updated successfully') != -1:
            return public.success_v2(
                {"msg": public.lang("aaPanel Update Successfully!"), "data": logs}
            )

        return public.success_v2(logs)

    def mark_reboot_read(self, get):
        import os
        status_file = '{}/data/reboot_notification.json'.format(public.get_panel_path())

        if not os.path.exists(status_file):
            return public.return_message(0, 0, public.lang("No reboot record found."))


        try:
            reboot_notification = public.readFile(status_file)
            if not reboot_notification.strip():
                data = {
                    "last_reboot_time": int(psutil.boot_time()),
                    "status": 1 }
            else:
                data = json.loads(reboot_notification)
                data['status'] = 1
            public.writeFile(status_file, json.dumps(data, ensure_ascii=False, indent=2))
            return public.return_message(0, 0, public.lang("Marked as read."))

        except Exception as e:
            return public.return_message(-1, 0, str(e))

    def reboot_status(self):
        """
        检查系统重启状态
        1. 如果是首次访问，记录当前 boot time
        2. 如果 boot time 发生显著变化（>3分钟），说明系统可能重启了，更新状态为未读
        3. 返回最后重启时间和读取状态
        """
        status_file = '{}/data/reboot_notification.json'.format(public.get_panel_path())

        reboot_status = {
            "last_reboot_time": 0,
            "status": 1
        }
        current_boot_time = int(psutil.boot_time())
        if not os.path.exists(status_file):
            initial_data = {
                "last_reboot_time": current_boot_time,
                "status": 1
            }
            try:
                public.writeFile(status_file, json.dumps(initial_data))
            except Exception as e:
                print(f"Failed to create reboot status file: {e}")
            return initial_data

        try:
            reboot_notification = public.readFile(status_file)
            if not reboot_notification or not str(reboot_notification).strip():
                data = {"last_reboot_time": current_boot_time, "status": 1}
                public.writeFile(status_file, json.dumps(data))
                return data
            data = json.loads(reboot_notification)
            last_recorded_time = data.get("last_reboot_time", 0)
            last_status = data.get("status", 1)


            if last_recorded_time > 0:
                diff = abs(current_boot_time - last_recorded_time)
                if diff > 60 * 3:
                    # 认定为系统重启 标记为未读
                    new_data = {
                        "last_reboot_time": current_boot_time,
                        "status": 0
                    }
                    try:
                        public.writeFile(status_file, json.dumps(new_data))
                        reboot_status.update(new_data)
                        return reboot_status
                    except Exception as e:
                        print(f"Failed to update reboot notification: {e}")
                elif diff > 0:  # 有变化才写入
                    new_data = {
                        "last_reboot_time": current_boot_time,
                        "status": last_status if last_status == 0 else 1
                    }
                    try:
                        public.writeFile(status_file, json.dumps(new_data))
                        reboot_status.update(new_data)
                        return reboot_status
                    except Exception as e:
                        print(f"Failed to update boot time (drift): {e}")

            reboot_status["last_reboot_time"] = last_recorded_time
            reboot_status["status"] = last_status

        except Exception as e:
            print(f"Error reading reboot status: {e}")

        return reboot_status
