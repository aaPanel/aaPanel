import json
import os
import time
import traceback
import re
import psutil

import public
from monitorModel.base import monitorBase
from pluginAuth import Plugin


class main(monitorBase):
    setupPath = '/www/server'
    __panel_path = '/www/server/panel/class/monitorModel'
    __data_path = os.path.join(__panel_path, 'data')
    cpu_old_path = os.path.join(__data_path, 'cpu_old.json')
    disk_read_old_path = os.path.join(__data_path, 'disk_read_old.json')
    disk_write_old_path = os.path.join(__data_path, 'disk_write_old.json')
    old_net_path = os.path.join(__data_path, 'network_old.json')
    old_disk_path = os.path.join(__data_path, 'disk_old.json')
    old_site_path = os.path.join(__data_path, 'site_old.json')
    nethogs_out = os.path.join(__data_path, 'process_flow.log')

    disk_write_new_info = {}
    disk_write_old_info = {}
    disk_read_new_info = {}
    disk_read_old_info = {}
    cpu_new_info = {}
    old_disk_info = {}
    new_disk_info = {}
    cpu_old_info = {}
    log_path = {
        "mongod": "/www/server/mongodb/log/config.log",
        "nginx": "/www/wwwlogs/nginx_error.log",
        "httpd": "/www/wwwlogs/nginx_error.log",
        "mysqld": "/www/server/data/mysql-slow.log",
    }

    pids = None
    __cpu_time = None
    panel_pid = None
    task_pid = None
    processPs = {
        'bioset': '用于处理块设备上的I/O请求的进程',
        'BT-MonitorAgent': '面板程序的进程',
        'rngd': '一个熵守护的进程',
        'master': '用于管理和协调子进程的活动的进程',
        'irqbalance': '一个IRQ平衡守护的进程',
        'rhsmcertd': '主要用于管理Red Hat订阅证书，并维护系统的订阅状态的进程',
        'auditd': '是Linux审计系统中用户空间的一个组的进程',
        'chronyd': '调整内核中运行的系统时钟和时钟服务器同步的进程',
        'qmgr': 'PBS管理器的进程',
        'oneavd': '面板微步木马检测的进程',
        'postgres': 'PostgreSQL数据库的进程',
        'grep': '一个命令行工具的进程',
        'lsof': '一个命令行工具的进程',
        'containerd-shim-runc-v2': 'Docker容器的一个组件的进程',
        'pickup': '用于监听Unix域套接字的进程',
        'cleanup': '邮件传输代理（MTA）中的一个组件的进程',
        'trivial-rewrite': '邮件传输代理（MTA）中的一个组件的进程',
        'containerd': 'docker依赖服务的进程',
        'redis-server': 'redis服务的进程',
        'rcu_sched': 'linux系统rcu机制服务的进程',
        'jsvc': '面板tomcat服务的进程',
        'oneav': '面板微步木马检测的进程',
        'mysqld': 'MySQL服务的进程',
        'php-fpm': 'PHP的子进程',
        'php-cgi': 'PHP-CGI的进程',
        'nginx': 'Nginx服务的进程',
        'httpd': 'Apache服务的进程',
        'sshd': 'SSH服务的进程',
        'pure-ftpd': 'FTP服务的进程',
        'sftp-server': 'SFTP服务的进程',
        'mysqld_safe': 'MySQL服务的进程',
        'firewalld': '防火墙服务的进程',
        'BT-Panel': '宝塔面板-主的进程',
        'BT-Task': '宝塔面板-后台任务的进程',
        'NetworkManager': '网络管理服务的进程',
        'svlogd': '日志守护的进程',
        'memcached': 'Memcached缓存器的进程',
        'gunicorn': "宝塔面板的进程",
        "BTPanel": '宝塔面板的进程',
        'baota_coll': "堡塔云控-主控端的进程",
        'baota_client': "堡塔云控-被控端的进程",
        'node': 'Node.js程序的进程',
        'supervisord': 'Supervisor的进程',
        'rsyslogd': 'rsyslog日志服务的进程',
        'crond': '计划任务服务的进程',
        'cron': '计划任务服务的进程',
        'rsync': 'rsync文件同步的进程',
        'ntpd': '网络时间同步服务的进程',
        'rpc.mountd': 'NFS网络文件系统挂载服务的进程',
        'sendmail': 'sendmail邮件服务的进程',
        'postfix': 'postfix邮件服务的进程',
        'npm': 'Node.js NPM管理器的进程',
        'PM2': 'Node.js PM2进程管理器的进程',
        'htop': 'htop进程监控软件的进程',
        'btpython': '宝塔面板-独立Python环境的进程',
        'btappmanagerd': '宝塔应用管理器插件的进程',
        'dockerd': 'Docker容器管理器的进程',
        'docker-proxy': 'Docker容器管理器的进程',
        'docker-registry': 'Docker容器管理器的进程',
        'docker-distribution': 'Docker容器管理器的进程',
        'docker-network': 'Docker容器管理器的进程',
        'docker-volume': 'Docker容器管理器的进程',
        'docker-swarm': 'Docker容器管理器的进程',
        'docker-systemd': 'Docker容器管理器的进程',
        'docker-containerd': 'Docker容器管理器的进程',
        'docker-containerd-shim': 'Docker容器管理器的进程',
        'docker-runc': 'Docker容器管理器的进程',
        'docker-init': 'Docker容器管理器的进程',
        'docker-init-systemd': 'Docker容器管理器的进程',
        'docker-init-upstart': 'Docker容器管理器的进程',
        'docker-init-sysvinit': 'Docker容器管理器的进程',
        'docker-init-openrc': 'Docker容器管理器的进程',
        'docker-init-runit': 'Docker容器管理器的进程',
        'docker-init-systemd-resolved': 'Docker容器管理器的进程',
        'rpcbind': 'NFS网络文件系统服务的进程',
        'dbus-daemon': 'D-Bus消息总线守护的进程',
        'systemd-logind': '登录管理器的进程',
        'systemd-journald': 'Systemd日志管理服务的进程',
        'systemd-udevd': '系统设备管理服务的进程',
        'systemd-timedated': '系统时间日期服务的进程',
        'systemd-timesyncd': '系统时间同步服务的进程',
        'systemd-resolved': '系统DNS解析服务的进程',
        'systemd-hostnamed': '系统主机名服务的进程',
        'systemd-networkd': '系统网络管理服务的进程',
        'systemd-resolvconf': '系统DNS解析服务的进程',
        'systemd-local-resolv': '系统DNS解析服务的进程',
        'systemd-sysctl': '系统系统参数服务的进程',
        'systemd-modules-load': '系统模块加载服务的进程',
        'systemd-modules-restore': '系统模块恢复服务的进程',
        'agetty': 'TTY登陆验证程序的进程',
        'sendmail-mta': 'MTA邮件传送代理的进程',
        '(sd-pam)': '可插入认证模块的进程',
        'polkitd': '授权管理服务的进程',
        'mongod': 'MongoDB数据库服务的进程',
        'mongodb': 'MongoDB数据库服务的进程',
        'mongodb-mms-monitor': 'MongoDB数据库服务的进程',
        'mongodb-mms-backup': 'MongoDB数据库服务的进程',
        'mongodb-mms-restore': 'MongoDB数据库服务的进程',
        'mongodb-mms-agent': 'MongoDB数据库服务的进程',
        'mongodb-mms-analytics': 'MongoDB数据库服务的进程',
        'mongodb-mms-tools': 'MongoDB数据库服务的进程',
        'mongodb-mms-backup-agent': 'MongoDB数据库服务的进程',
        'mongodb-mms-backup-tools': 'MongoDB数据库服务的进程',
        'mongodb-mms-restore-agent': 'MongoDB数据库服务的进程',
        'mongodb-mms-restore-tools': 'MongoDB数据库服务的进程',
        'mongodb-mms-analytics-agent': 'MongoDB数据库服务的进程',
        'mongodb-mms-analytics-tools': 'MongoDB数据库服务的进程',
        'dhclient': 'DHCP协议客户端的进程',
        'dhcpcd': 'DHCP协议客户端的进程',
        'dhcpd': 'DHCP服务器的进程',
        'isc-dhcp-server': 'DHCP服务器的进程',
        'isc-dhcp-server6': 'DHCP服务器的进程',
        'dhcp6c': 'DHCP服务器的进程',
        'dhcpcd': 'DHCP服务器的进程',
        'dhcpd': 'DHCP服务器的进程',
        'avahi-daemon': 'Zeroconf守护的进程',
        'login': '登录的进程',
        'systemd': '系统管理服务的进程',
        'systemd-sysv': '系统管理服务的进程',
        'systemd-journal-gateway': '系统管理服务的进程',
        'systemd-journal-remote': '系统管理服务的进程',
        'systemd-journal-upload': '系统管理服务的进程',
        'systemd-networkd': '系统网络管理服务的进程',
        'rpc.idmapd': 'NFS网络文件系统相关服务的进程',
        'cupsd': '打印服务的进程',
        'cups-browsed': '打印服务的进程',
        'sh': 'shell的进程',
        'php': 'PHP CLI模式的进程',
        'blkmapd': 'NFS映射服务的进程',
        'lsyncd': '文件同步服务的进程',
        'sleep': '延迟的进程',
    }

    def __init__(self):
        if not os.path.isdir(self.__data_path):
            os.makedirs(self.__data_path, 384)
        plugin_obj = Plugin(False)
        plugin_list = plugin_obj.get_plugin_list()
        public.print_log(plugin_list['ltd'])
        ped = int(plugin_list['ltd']) > time.time()
        if ped:
            self.add_nethogs_task()

    def specific_resource_load_type(self, get):
        """
        查询具体资源类型负载
        :param get: None
        :return: 资源占用字典
        """
        try:
            plugin_obj = Plugin(False)
            plugin_list = plugin_obj.get_plugin_list()
            public.print_log(plugin_list['ltd'])
            ped = int(plugin_list['ltd']) > time.time()
            if not ped: return {'status': False, 'msg': "该功能为企业版专享！"}
            infos = {}
            load_avg = os.getloadavg()
            infos['info'] = {}
            infos['info']['physical_cpu'] = psutil.cpu_count(logical=False)
            infos['info']['logical_cpu'] = psutil.cpu_count(logical=True)
            c_tmp = public.readFile('/proc/cpuinfo')
            d_tmp = re.findall("physical id.+", c_tmp)
            cpuW = len(set(d_tmp))
            infos['info']['cpu_name'] = public.getCpuType() + " * {}".format(cpuW)
            infos['info']['num_phys_cores'] = cpuW
            infos['info']['load_avg'] = {"1": load_avg[0], "5": load_avg[1], "15": load_avg[2]}
            infos['info']['active_processes'] = len(
                [p for p in psutil.process_iter() if p.status() == psutil.STATUS_RUNNING])
            infos['info']['total_processes'] = len(psutil.pids())
            cpu_percent = self.get_process_cpu(get)
            cpu_proc = cpu_percent["process_list"]
            mem = self.get_mem_info()
            infos['CPU_percentage_of_load'] = cpu_percent["info"]["cpu"]
            infos['percentage_of_memory_usage'] = round(mem['memRealUsed'] / mem['memTotal'] * 100, 2)
            infos['CPU_high_occupancy_software_list'] = {}
            for i in range(5):
                try:
                    infos['CPU_high_occupancy_software_list'][i] = {"name": cpu_proc[i]['name'],
                                                                    'pid': cpu_proc[i]['pid'],
                                                                    'cpu_percent': cpu_proc[i]['cpu_percent'],
                                                                    'proc_survive': cpu_proc[i]['proc_survive']}
                except:
                    pass
            b = []
            for i, j in infos['CPU_high_occupancy_software_list'].items():
                cpu_info = {'proc_name': infos['CPU_high_occupancy_software_list'][i]['name'],
                            'pid': infos['CPU_high_occupancy_software_list'][i]['pid'],
                            'cpu_percent': str(infos['CPU_high_occupancy_software_list'][i]['cpu_percent']) + "%"}
                cpu_info['explain'], cpu_info['num_threads'], cpu_info['exe_path'], cpu_info['cwd_path'], cpu_info[
                    'important'], cpu_info['proc_survive'] = self.__process_analysis(
                    infos['CPU_high_occupancy_software_list'][i]['pid'])
                b.append(cpu_info)
            infos['CPU_high_occupancy_software_list'] = b
            infos["memory_high_occupancy_software_list"] = self.__use_mem_list()
            c = []
            for i, j in infos["memory_high_occupancy_software_list"].items():
                mem_info = {'proc_name': i, 'pid': infos['memory_high_occupancy_software_list'][i]['pid'],
                            "memory_usage": infos["memory_high_occupancy_software_list"][i]['memory_usage']}
                mem_info['explain'], mem_info['num_threads'], mem_info['exe_path'], mem_info['cwd_path'], mem_info[
                    'important'], mem_info['proc_survive'] = self.__process_analysis(
                    infos["memory_high_occupancy_software_list"][i]['pid'])
                c.append(mem_info)
            infos["memory_high_occupancy_software_list"] = c
            return infos
        except:
            public.print_log(traceback.format_exc())

    # 按cpu资源获取进程列表
    def get_process_cpu(self, get):
        self.pids = psutil.pids()
        process_list = []
        if type(self.cpu_new_info) != dict: self.cpu_new_info = {}
        self.cpu_new_info['cpu_time'] = self.get_cpu_time()
        self.cpu_new_info['time'] = time.time()

        if 'sort' not in get: get.sort = 'cpu_percent'
        get.reverse = bool(int(get.reverse)) if 'reverse' in get else True
        info = {}
        info['activity'] = 0
        info['cpu'] = 0.00
        status_ps = {'sleeping': '睡眠', 'running': '活动'}
        limit = 1000
        for pid in self.pids:
            tmp = {}
            try:
                p = psutil.Process(pid)
            except:
                continue
            with p.oneshot():
                p_cpus = p.cpu_times()
                p_state = p.status()
                if p_state == 'running': info['activity'] += 1
                if p_state in status_ps:
                    p_state = status_ps[p_state]
                else:
                    continue
                tmp['exe'] = p.exe()
                timestamp = time.time() - p.create_time()
                time_info = {}
                time_info["天"] = int(timestamp // (24 * 3600))
                time_info["小时"] = int((timestamp - time_info['天'] * 24 * 3600) // 3600)
                time_info["分钟"] = int((timestamp - time_info['天'] * 24 * 3600 - time_info['小时'] * 3600) // 60)
                ll = [str(v) + k for k, v in time_info.items() if v != 0]
                tmp['proc_survive'] = ''.join(ll)
                tmp['name'] = p.name()
                tmp['pid'] = pid
                tmp['ppid'] = p.ppid()
                # tmp['create_time'] = int(p.create_time())
                tmp['status'] = p_state
                tmp['user'] = p.username()
                tmp['cpu_percent'] = self.get_cpu_percent(str(pid), p_cpus, self.cpu_new_info['cpu_time'])
                tmp['threads'] = p.num_threads()
                tmp['ps'] = self.get_process_ps(tmp['name'], pid)
                if tmp['cpu_percent'] > 100: tmp['cpu_percent'] = 0.1
                info['cpu'] += tmp['cpu_percent']
            process_list.append(tmp)
            limit -= 1
            if limit <= 0: break
            del p
            del tmp
        public.writeFile(self.cpu_old_path, json.dumps(self.cpu_new_info))
        # process_list = self.handle_process_list(process_list)
        process_list = sorted(process_list, key=lambda x: x[get.sort], reverse=get.reverse)
        info['load_average'] = self.get_load_average()
        data = {}
        data['process_list'] = process_list[:10]
        info['cpu'] = round(info['cpu'], 2)
        data['info'] = info
        return data

    # 获取负载
    def get_load_average(self, get=None):
        b = public.ExecShell("uptime")[0].replace(',', '')
        c = b.split()
        data = {}
        data['1'] = float(c[-3])
        data['5'] = float(c[-2])
        data['15'] = float(c[-1])
        return data

    # 获取总的cpu时间
    def get_cpu_time(self, get=None):
        if self.__cpu_time: return self.__cpu_time
        self.__cpu_time = 0.00
        s = psutil.cpu_times()
        self.__cpu_time = s.user + s.system + s.nice + s.idle
        return self.__cpu_time

    # 获取进程cpu利用率
    def get_cpu_percent(self, pid, cpu_times, cpu_time):
        self.get_cpu_old()
        percent = 0.00
        process_cpu_time = self.get_process_cpu_time(cpu_times)
        if not self.cpu_old_info: self.cpu_old_info = {}
        if pid not in self.cpu_old_info:
            self.cpu_new_info[pid] = {}
            self.cpu_new_info[pid]['cpu_time'] = process_cpu_time
            return percent
        percent = round(100.00 * (process_cpu_time - self.cpu_old_info[pid]['cpu_time']) / (
                cpu_time - self.cpu_old_info['cpu_time']), 2)
        self.cpu_new_info[pid] = {}
        self.cpu_new_info[pid]['cpu_time'] = process_cpu_time
        if percent > 0: return percent
        return 0.00

    # 获取信息，如果存在返回true，不存在读取gson后存在true：不存在flase
    def get_cpu_old(self):
        if self.cpu_old_info: return True
        if not os.path.exists(self.cpu_old_path): return False
        data = public.readFile(self.cpu_old_path)
        if not data: return False
        data = json.loads(data)
        if not data: return False
        self.cpu_old_info = data
        del data
        return True

    # 获取进程占用的cpu时间
    def get_process_cpu_time(self, cpu_times):
        cpu_time = 0.00
        for s in cpu_times: cpu_time += s
        return cpu_time

    def get_process_ps(self, name, pid):
        if name in self.processPs: return self.processPs[name]

    # 增加使用nethogs收集进程流量定时任务
    def add_nethogs_task(self, get=None):
        # self.add_process_white('nethogs')
        import crontab
        if public.M('crontab').where('name=?', u'[勿删]资源管理器-获取进程流量').count():
            return public.returnMsg(True, '定时任务已存在!')

        s_body = '''ps -ef | grep nethogs | grep -v grep | awk '{print $2}' | xargs kill 2>/dev/null
count=0
while [ $count -lt 2 ]
do
    count=$(($count+1))
    /usr/sbin/nethogs -t -a -d 2 -c 5 > %s 2>/dev/null
    if [[ $count == 2 ]];then
        exit
    else
        sleep 20
    fi
done''' % self.nethogs_out

        p = crontab.crontab()
        args = {
            "name": u'[勿删]资源管理器-获取进程流量',
            "type": 'minute-n',
            "where1": 5,
            "hour": '',
            "minute": '',
            "week": '',
            "sType": "toShell",
            "sName": "",
            "backupTo": "",
            "save": '',
            "sBody": s_body,
            "urladdress": "undefined"
        }
        p.AddCrontab(args)
        return public.returnMsg(True, '设置成功!')

    # 获取内存情况
    def get_mem_info(self, get=None):
        mem = psutil.virtual_memory()
        memInfo = {'memTotal': int(mem.total / 1024 / 1024), 'memFree': int(mem.free / 1024 / 1024),
                   'memBuffers': int(mem.buffers / 1024 / 1024), 'memCached': int(mem.cached / 1024 / 1024)}
        memInfo['memRealUsed'] = memInfo['memTotal'] - memInfo['memFree'] - memInfo['memBuffers'] - memInfo['memCached']
        return memInfo

    def __use_mem_list(self):
        processes = []
        for proc in psutil.process_iter():
            try:
                # 获取进程详细信息
                pinfo = proc.as_dict(attrs=['pid', 'name', 'memory_info'])
                # 添加到进程列表
                processes.append(pinfo)
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                pass
        processes = sorted(processes, key=lambda p: p['memory_info'].rss, reverse=True)
        l = {}
        mem_total = psutil.virtual_memory().total
        for p in processes:
            l[p['name']] = {'pid': p['pid'],
                            'memory_usage': '%.2f' % (int(p['memory_info'].rss) / int(mem_total) * 100) + "%"}
            if len(l) >= 5:
                break
        return l

    # 常用软件分析
    def __process_analysis(self, pid):
        process = psutil.Process(pid)
        important = 0
        explain = self.processPs.get(process.name(),
                                     '未知程序的进程')
        if 'BT-Panel' == process.name() or 'BT-Task' == process.name():
            important = 1
        num_threads = process.num_threads()
        exe_path = process.exe()
        cwd_path = process.cwd()
        timestamp = time.time() - process.create_time()
        time_info = {}
        time_info["天"] = int(timestamp // (24 * 3600))
        time_info["小时"] = int((timestamp - time_info['天'] * 24 * 3600) // 3600)
        time_info["分钟"] = int((timestamp - time_info['天'] * 24 * 3600 - time_info['小时'] * 3600) // 60)
        ll = [str(v) + k for k, v in time_info.items() if v != 0]
        pro_time = ''.join(ll)
        if ''.join(ll) == '':
            pro_time = '小于1分钟'
        return explain, num_threads, exe_path, cwd_path, important, pro_time

    def kill_process_all(self, get):
        pid = int(get.pid)
        if pid < 30: return public.returnMsg(False, '不能结束系统关键进程!')
        if pid not in psutil.pids(): return public.returnMsg(False, '指定进程不存在!')
        p = psutil.Process(pid)
        if self.is_panel_process(pid): return public.returnMsg(False, '不能结束面板服务进程')
        p.kill()
        return self.kill_process_tree_all(pid)

    # 结束进程树
    def kill_process_tree_all(self, pid):
        if pid < 30: return public.returnMsg(True, '已结束此进程树!')
        if self.is_panel_process(pid): return public.returnMsg(False, '不能结束面板服务进程')
        try:
            if pid not in psutil.pids(): public.returnMsg(True, '已结束此进程树!')
            p = psutil.Process(pid)
            ppid = p.ppid()
            name = p.name()
            p.kill()
            public.ExecShell('pkill -9 ' + name)
            if name.find('php-') != -1:
                public.ExecShell("rm -f /tmp/php-cgi-*.sock")
            elif name.find('mysql') != -1:
                public.ExecShell("rm -f /tmp/mysql.sock")
            elif name.find('mongod') != -1:
                public.ExecShell("rm -f /tmp/mongod*.sock")
            self.kill_process_lower(pid)
            if ppid: return self.kill_process_all(ppid)
        except:
            pass
        return public.returnMsg(True, '已结束此进程树!')

    def kill_process_lower(self, pid):
        pids = psutil.pids()
        for lpid in pids:
            if lpid < 30: continue
            if self.is_panel_process(lpid): continue
            p = psutil.Process(lpid)
            ppid = p.ppid()
            if ppid == pid:
                p.kill()
                return self.kill_process_lower(lpid)
        return True

    # 判断是否是面板进程
    def is_panel_process(self, pid):
        if not self.panel_pid:
            self.panel_pid = os.getpid()
        if pid == self.panel_pid: return True
        if not self.task_pid:
            try:
                self.task_pid = int(
                    public.ExecShell("ps aux | grep 'python task.py'|grep -v grep|head -n1|awk '{print $2}'")[0])
            except:
                self.task_pid = -1
        if pid == self.task_pid: return True
        return False

    def __get_number_of_processes(self):
        import psutil
        from collections import Counter
        ll = []
        processes = psutil.process_iter()
        process_names = [process.name() for process in processes]
        process_item = Counter(process_names)
        process_item = dict(sorted(process_item.items(), key=lambda item: item[1], reverse=True)[:5])
        for key, value in process_item.items():
            procs = {'proc_name': key, 'proc_description': '此进程的进程数有' + str(value) + '个，进程是{}'.format(
                self.processPs.get(key, "未知进程"))}
            ll.append(procs)
        return ll

    def process_description(self, get):
        try:
            updatas = json.loads(get.information_collection)
            data = json.loads(public.readFile('/www/server/panel/class/monitorModel/common_process.json'))
            data.update(updatas)
            public.writeFile('/www/server/panel/class/monitorModel/common_process.json', json.dumps(data))
            return public.returnMsg(True, "进程添加成功")
        except:
            return public.returnMsg(False, "进程添加失败")

    def universal(self, get):
        method = {
            "题目1": "遇到未知进程解决办法。",
            "1.1": "观察进程可执行目录和运行目录，是否与BT、项目名、常用软件相关，若与项目或者系统相关的进程且占用资源不大可不管。",
            "1.2": "去‘百度’上搜索进程名，查看进程的归属，以及是否有害。ps:https://www.baidu.com",
            "1.3": "咨询项目开发人员，看此进程是否由部署的项目所创建，若是，可加入到常见进程列表中。",
            "1.4": "实在判断不了进程的性质，可到宝塔论坛发帖求助.ps:https://www.bt.cn/bbs/portal.php",
            "1.5": "对进程做出详细的判断后，无用且占用资源较高，可关闭该进程。",
            "1.6": "若占用资源较多的是使用当中的软件或项目，则可以尝试适当的优化，比如mysql优化、适当限制php的并发等。",
            "题目2": "内存，cpu使用率不高，但负载很高解决办法",
            "2.1": "负载高低还与线程数量、IO使用率、服务器本身有联系，可查看线程数量以及磁盘使用情况进行综合判断",
            "2.2": "若本身服务器的配置较低，可以适当的考虑升级服务器配置",
            "2.3": "若是遭受到网络攻击，也可导致服务器的负载偏高，可以开启宝塔防火墙以及安全插件进行防护。",
            "2.4": "若服务器使用的是云服务器，也可能是服务器商家限制，可以咨询一下服务器商家的客服。"
        }
        return method
