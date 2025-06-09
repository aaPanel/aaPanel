import os
import sys
import glob
from datetime import datetime

if "/www/server/panel/class" not in sys.path:
    sys.path.insert(0, "/www/server/panel/class")

os.chdir("/www/server/panel")
import public

from mod.project.ssh.base import SSHbase


class SecureManage(SSHbase):
    def __init__(self):
        super(SecureManage, self).__init__()
        self.login_access_flag = "Accepted"
        self.login_failed_flag = "Failed password"
        self.login_all_flag = "Failed password|Accepted"
        if os.path.exists("/var/log/auth.log"):
            self.ssh_log_path = "/var/log/auth.log"
        elif os.path.exists("/var/log/secure"):
            self.ssh_log_path = "/var/log/secure"
        else:
            self.ssh_log_path = "/var/log/message"

    def get_secure_logs(self,login_type,pagesize=10,page=1,query=''):
        """
            读取SSH日志文件的内容。
        :param login_type: ssh登录类型 失败'Failed password'  成功'Accepted' 全部'Failed password|Accepted'
        :param pagesize: 每页显示的条数
        :param page: 当前页码
        :param query: 关键字搜索 ip or user or time
        :return: 日志内容的列表
        """
        new_logins = []
        end = pagesize * page

        danger_symbol = ['&', '&&', '||', '|', ';']
        for d in danger_symbol:
            if d in query:
                return new_logins

        if query != '':
            query = "|grep -aE '{}'".format(query)
        commands = "ls -tr {file_path}|grep -v '\.gz$'|xargs cat|grep -aE '({login_type})'{query}|tail -n {end}|head -n {pagesize}|tac".format(
            file_path=self.ssh_log_path,
            login_type=login_type,
            query=query,
            end=end,
            pagesize=pagesize)

        year = datetime.now().year
        result, err = public.ExecShell(commands)
        lines = result.split('\n')
        for line in lines:
            parts = line.split()
            if not parts:
                continue
            entry = self.parse_login_entry(parts, year)
            if entry:
                new_logins.append(entry)
        return new_logins

    def get_secure_log_count(self,login_type,query=''):
        """
        读取SSH日志文件的内容 统计登陆类型的条数。

        :param login_type: ssh登录类型 失败'Failed password'  成功'Accepted' 全部'Failed password|Accepted'
        :param query: 关键字搜索 ip or user or time
        :return: 日志内容的列表
        """

        danger_symbol = ['&', '&&', '||', '|', ';']
        for d in danger_symbol:
            if d in query:
                return 0

        if query != '':
            query = "|grep -a '{}'".format(query)
        commands = "ls -tr {file_path}|grep -v '\.gz$'|xargs cat|grep -aE '({login_type})'{query}|wc -l".format(file_path=self.ssh_log_path,login_type=login_type,query=query)
        result, err = public.ExecShell(commands)
        return int(result.strip())