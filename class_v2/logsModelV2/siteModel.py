# coding: utf-8
# -------------------------------------------------------------------
# aaPanel
# -------------------------------------------------------------------
# Copyright (c) 2015-2099 aaPanel(www.aapanel.com) All rights reserved.
# -------------------------------------------------------------------
# Author: cjxin <bt_ahong@aapanel.com>
# -------------------------------------------------------------------

# ------------------------------
# 面板日志类
# ------------------------------

import os
import re
from html import escape

import public
from logsModelV2.base import logsBase
from mod.base.web_conf.nginx_realip import NginxRealIP


class main(logsBase):

    def __init__(self):
        super().__init__()
        self.serverType = public.get_webserver()
        self.setupPath = public.get_setup_path()

    def __get_iis_log_files(self, path):
        """
        @name 获取IIS日志文件列表
        @param path 日志文件路径
        @return list
        """
        file_list = []
        if os.path.exists(path):
            for filename in os.listdir(path):
                if filename.find('.log') == -1: continue
                file_list.append('{}/{}'.format(path, filename))

        file_list = sorted(file_list, reverse=False)
        return file_list

    def get_iis_logs(self, get):
        """
        @name 获取IIS网站日志
        """

        p, limit, search = 1, 2000, ''
        if 'p' in get: limit = int(get.p)
        if 'limit' in get: limit = int(get.limit)
        if 'search' in get: search = get.search

        import panelSite
        site_obj = panelSite.panelSite()
        data = site_obj.get_site_info(get.siteName)
        if not data:
            return public.return_message(-1, 0, public.lang(
                "[{}] Failed to get the website path, please check whether IIS exists this site, does not exist, please delete this site in the panel after the creation.",
                get.siteName))

        log_path = '{}/wwwlogs/W3SVC{}'.format(public.get_soft_path(), data['id'])
        file_list = self.__get_iis_log_files(log_path)

        find_idx = 0
        log_list = []
        for log_path in file_list:
            if not os.path.exists(log_path):  continue
            if len(log_list) >= limit: break

            p_num = 0  # 分页计数器
            next_file = False
            while not next_file:
                if len(log_list) >= limit:
                    break
                p_num += 1
                result = self.GetNumLines(log_path, 10001, p_num).split('\r\n')
                if len(result) < 10000:
                    next_file = True

                for _line in result:
                    if not _line: continue
                    if len(log_list) >= limit:
                        break

                    try:
                        if self.find_line_str(_line, search):
                            find_idx += 1
                            if find_idx > (p - 1) * limit:
                                info = escape(_line)
                                log_list.append(info)
                    except:
                        pass
        return public.return_message(0, 0, log_list)

    # 取网站日志
    def get_site_logs(self, get):
        logPath = ''
        if self.serverType == 'iis':
            return self.get_iis_logs(get)

        elif self.serverType == 'apache':
            logPath = self.setupPath + '/wwwlogs/' + get.siteName + '-access.log'
        else:
            logPath = self.setupPath + '/wwwlogs/' + get.siteName + '.log'

        data = {}
        data['path'] = ''
        data['path'] = os.path.dirname(logPath)
        if os.path.exists(logPath):
            data['status'] = True
            data['msg'] = public.GetNumLines(logPath, 1000)

            return public.return_message(0, 0, data)
        # data['status'] = False
        # data['msg'] = 'log is empty'
        # return data

        return public.return_message(-1, 0, 'log is empty')

    @staticmethod
    def nginx_get_log_file(nginx_config: str, is_error_log: bool = False):
        if is_error_log:
            re_data = re.findall(r"error_log +(/(\S+/?)+) ?(.*?);", nginx_config)
        else:
            re_data = re.findall(r"access_log +(/(\S+/?)+) ?(.*?);", nginx_config)
        if re_data is None:
            return None
        for i in re_data:
            file_path = i[0].strip(";")
            if file_path != "/dev/null":
                return file_path
        return None

    @staticmethod
    def apache_get_log_file(apache_config: str, is_error_log: bool = False):
        if is_error_log:
            re_data = re.findall(r'''ErrorLog +['"]?(/(\S+/?)+)['"]? ?(.*?)\n''', apache_config)
        else:
            re_data = re.findall(r'''CustomLog +['"]?(/(\S+/?)+)['"]? ?(.*?)\n''', apache_config)
        if re_data is None:
            return None
        for i in re_data:
            file_path = i[0].strip('"').strip("'")
            if file_path != "/dev/null":
                return file_path
        return None

    def xsssec(self, text):
        replace_list = {
            "<": "＜",
            ">": "＞",
            "'": "＇",
            '"': "＂",
        }
        for k, v in replace_list.items():
            text = text.replace(k, v)
        return public.xssencode2(text)

    def add_iparea(self, data):
        try:
            ip_pattern = r'\n\b(?:\d{1,3}\.){3}\d{1,3}\b'
            ip_addresses = re.findall(ip_pattern, data)
            ip_addresses = list(set(ip_addresses))
            ip_addresses = [ip.strip() for ip in ip_addresses]
            infos = public.get_ips_area(ip_addresses)
            for key, value in infos.items():
                if value.get('info') == '内网地址':
                    data = data.replace(key, '【{}】 {}'.format(value['info'], key))
                    continue
                if value.get('info') == '未知归属地':
                    data = data.replace(key, '【{}】 {}'.format(value['info'], key))
                    continue
                try:
                    data = data.replace(key,
                                        '【{} {} {}】 {}'.format(value['continent'], value['country'], value['province'],
                                                               key))
                except:
                    pass
            return data
        except:
            return data

    @staticmethod
    def nginx_get_log_file_path(nginx_config: str, site_name: str, is_error_log: bool = False):
        log_file = None
        if is_error_log:
            re_data = re.findall(r"error_log +(/(\S+/?)+) ?(.*?);", nginx_config)
        else:
            re_data = re.findall(r"access_log +(/(\S+/?)+) ?(.*?);", nginx_config)
        if re_data is None:
            log_file = None
        else:
            for i in re_data:
                file_path = i[0].strip(";")
                if file_path != "/dev/null" and not file_path.endswith("purge_cache.log"):
                    if os.path.isdir(os.path.dirname(file_path)):
                        log_file = file_path
                        break

        logsPath = '/www/wwwlogs/'
        if log_file is None:
            if is_error_log:
                log_file = logsPath + site_name + '.log'
            else:
                log_file = logsPath + site_name + '.error.log'
            if not os.path.isfile(log_file):
                log_file = None

        return log_file

    @staticmethod
    def apache_get_log_file_path(apache_config: str, site_name: str, is_error_log: bool = False):
        log_file = None
        if is_error_log:
            re_data = re.findall(r'''ErrorLog +['"]?(/(\S+/?)+)['"]? ?(.*?)\n''', apache_config)
        else:
            re_data = re.findall(r'''CustomLog +['"]?(/(\S+/?)+)['"]? ?(.*?)\n''', apache_config)
        if re_data is None:
            log_file = None
        else:
            for i in re_data:
                file_path = i[0].strip('"').strip("'")
                if file_path != "/dev/null":
                    if os.path.isdir(os.path.dirname(file_path)):
                        log_file = file_path
                        break

        logsPath = '/www/wwwlogs/'
        if log_file is None:
            if is_error_log:
                log_file = logsPath + site_name + '-access_log'
            else:
                log_file = logsPath + site_name + '-error_log'
            if not os.path.isfile(log_file):
                log_file = None

        return log_file

    @staticmethod
    def open_ols_log_file_path(site_name: str, is_error_log: bool = False):
        if not is_error_log:
            return '/www/wwwlogs/' + site_name + '_ols.access_log'
        else:
            return '/www/wwwlogs/' + site_name + '_ols.error_log'

    def get_site_log_file(self, get):
        res = public.M('sites').where('name=?', (get.siteName,)).select()
        if not res:
            return {
                "status": False,
                "log_file": '',
                "cdn_ip": {},
                "msg": "site not found"
            }
        res = res[0]['project_type'].lower()
        if res == 'php' or res == 'proxy' or res == 'phpmod' or res == 'wp2':
            res = ''
        else:
            res = res + '_'

        is_error_log = False
        if "is_error_log" in get and get.is_error_log.strip() in ('1', "yes"):
            is_error_log = True

        serverType = public.get_webserver()
        if serverType == "nginx":
            config_path = '/www/server/panel/vhost/nginx/{}.conf'.format(res + get.siteName)
            config = public.readFile(config_path)
            if not config:
                return public.fail_v2("config not found")
            log_file = self.nginx_get_log_file_path(config, get.siteName, is_error_log=is_error_log)
        elif serverType == 'apache':
            config_path = '/www/server/panel/vhost/apache/{}.conf'.format(res + get.siteName)
            config = public.readFile(config_path)
            if not config:
                return public.fail_v2("config not found")
            log_file = self.apache_get_log_file_path(config, get.siteName, is_error_log=is_error_log)
        else:
            log_file = self.open_ols_log_file_path(get.siteName, is_error_log=is_error_log)
        return {
            "status": True,
            "log_file": log_file,
            "cdn_ip": NginxRealIP().get_real_ip(get.siteName),
            "msg": "Success"
        }

    # 获取网站日志
    def GetSiteLogs(self, get):
        ip_area = 0
        if hasattr(get, 'ip_area'):
            ip_area = int(get.ip_area)
            public.writeFile('data/ip_area.txt', str(ip_area))
        logsPath = '/www/wwwlogs/'
        res = public.M('sites').where('name=?', (get.siteName,)).select()
        if res:
            res = res[0]['project_type'].lower()
        else:
            return public.fail_v2("site not found")

        if res == 'php' or res == 'proxy' or res == 'phpmod' or res == 'wp2':
            res = ''
        else:
            res = res + '_'
        serverType = public.get_webserver()
        re_log_file = None
        if serverType == "nginx":
            config_path = '/www/server/panel/vhost/nginx/{}.conf'.format(res + get.siteName)
            if not os.path.exists(config_path):
                return public.fail_v2("config not found")
            config = public.readFile(config_path)
            re_log_file = self.nginx_get_log_file(config, is_error_log=False)
        elif serverType == 'apache':
            config_path = '/www/server/panel/vhost/apache/{}.conf'.format(res + get.siteName)
            if not os.path.exists(config_path):
                return public.fail_v2("config not found")
            config = public.readFile(config_path)
            if not config:
                return public.fail_v2("{} logs not found".format(get.siteName))
            re_log_file = self.apache_get_log_file(config, is_error_log=False)

        if re_log_file is not None and os.path.exists(re_log_file):
            data = self.xsssec(public.GetNumLines(re_log_file, 1000))
            if ip_area:
                data = self.add_iparea(data)
            return public.success_v2(data)
        if serverType == "nginx":
            logPath = logsPath + get.siteName + '.log'
        elif serverType == 'apache':
            logPath = logsPath + get.siteName + '-access_log'
        else:
            logPath = logsPath + get.siteName + '_ols.access_log'
        if not os.path.exists(logPath):
            return public.fail_v2("log not found")
        data = self.xsssec(public.GetNumLines(logPath, 1000))
        if ip_area:
            data = self.add_iparea(data)
        return public.success_v2(data)
