#coding: utf-8
#-------------------------------------------------------------------
# 宝塔Linux面板
#-------------------------------------------------------------------
# Copyright (c) 2015-2020 宝塔软件(http:#bt.cn) All rights reserved.
#-------------------------------------------------------------------
# Author: zhwen <zhw@bt.cn>
#-------------------------------------------------------------------

#------------------------------
# 允许网站自动列出目录
#------------------------------

import public
import re

class website_auto_index:

    def _init_conf(self, website):
        self.ng_website_conf = '/www/server/panel/vhost/nginx/{}.conf'.format(website)
        self.ap_website_conf = '/www/server/panel/vhost/apache/{}.conf'.format(website)
        self.webserver = public.get_webserver()

    # 获取某个网站自动索引目录
    def get_auto_index(self, args):
        '''
        # 添加某个网站禁止运行PHP
        author: zhwen<zhw@bt.cn>
        :param args: website 网站名 str
        :return:
        '''
        self._init_conf(args.website)
        if self.webserver == 'nginx':
            data = self._get_nginx_auto_index()
        elif self.webserver == 'apache':
            data = self._get_apache_auto_index()
        else:
            data = public.returnMsg(False,'Sorry, OLS does not currently support this feature')
        return data

    def _get_nginx_auto_index(self):
        conf = public.readFile(self.ng_website_conf)
        if not conf:
            return False
        data = re.findall('BEGIN_AUTOINDEX_.*', conf)
        deny_name = [i.split('_')[-1] for i in data]
        result = []
        for i in deny_name:
            reg = '#BEGIN_AUTOINDEX_{}\n\s*location\s*\~\*\s*\^(.*)\.\*.*\((.*)\)\$'.format(i)
            deny_directory = re.search(reg, conf).groups()[0]
            deny_suffix = re.search(reg, conf).groups()[1]
            result.append({'name': i, 'dir': deny_directory, 'suffix': deny_suffix})
        return result

    def _get_apache_auto_index(self):
        conf = public.readFile(self.ap_website_conf)
        if not conf:
            return False
        data = re.findall('BEGIN_AUTOINDEX_.*', conf)
        deny_name = [i.split('_')[-1] for i in data]
        result = []
        for i in deny_name:
            reg = '#BEGIN_AUTOINDEX_{}\n\s*<Directory\s*\~\s*"(.*)\.\*.*\((.*)\)\$'.format(i)
            deny_directory = re.search(reg, conf).groups()[0]
            deny_suffix = re.search(reg, conf).groups()[1]
            result.append({'name': i, 'dir': deny_directory, 'suffix': deny_suffix})
        return result

    def set_auto_index(self, args):
        '''
        # 添加自动索引目录
        author: zhwen<zhw@bt.cn>
        :param args: website 网站名 str
        :param args: index_name 规则名称 str
        :param args: dir 自动索引目录 str
        :param args: act 操作方法
        :return:
        '''
        if self.webserver == 'openlitespeed':
            return public.returnMsg(False, 'Sorry, OLS does not currently support this feature')

        tmp = self._check_args(args)
        if tmp:
            return tmp
        deny_name = args.index_name
        dir = args.dir
        website = args.website
        self._init_conf(website)
        conf = public.readFile(self.ng_website_conf)
        if not conf:
            return False
        data = re.findall('BEGIN_AUTOINDEX_.*', conf)
        exist_index_name = [i.split('_')[-1] for i in data]
        if args.act == 'edit':
            if deny_name not in exist_index_name:
                return public.returnMsg(False, 'The specify rule name is not exists! [ {} ]'.format(deny_name))
            self.del_auto_index(args)
        else:
            if deny_name in exist_index_name:
                return public.returnMsg(False, 'The specify rule name is already exists! [ {} ]'.format(deny_name))
        self._set_nginx_auto_index(deny_name, dir)
        self._set_apache_auto_index(deny_name, dir)
        public.serviceReload()
        return public.returnMsg(True, 'Add Successfully')

    def _set_nginx_auto_index(self, name, dir=None):
        conf = public.readFile(self.ng_website_conf)
        if not conf:
            return False
        if not dir:
            reg = '\s*#BEGIN_AUTOINDEX_{n}\n(.|\n)*#END_AUTOINDEX_{n}\n'.format(n=name)
            conf = re.sub(reg, '', conf)
        else:
            new = '''
        #BEGIN_AUTOINDEX_%s
        location %s
        {
            autoindex on;
            autoindex_format html;
            autoindex_exact_size off;
            autoindex_localtime on;
        }
        #END_AUTOINDEX_%s
    ''' % (name, dir, name)
            if '#BEGIN_AUTOINDEX_{}\n'.format(name) in conf:
                return True
            conf = re.sub('#ERROR-PAGE-END', '#ERROR-PAGE-END' + new, conf)
        public.writeFile(self.ng_website_conf, conf)
        return True

    def _set_apache_auto_index(self, name, dir=None):
        conf = public.readFile(self.ap_website_conf)
        if not conf:
            return False
        if not dir:
            reg = '\s*#BEGIN_AUTOINDEX_{n}\n(.|\n)*#END_AUTOINDEX_{n}'.format(n=name)
            conf = re.sub(reg, '', conf)
        else:
            new = '''
        #BEGIN_AUTOINDEX_{n}
        <Location "{d}">
            Options Indexes FollowSymLinks
            AllowOverride None
            Options +Indexes
        </Directory>
        #END_AUTOINDEX_{n}
    '''.format(n=name, d=dir)
            if '#BEGIN_AUTOINDEX_{}'.format(name) in conf:
                return True
            conf = re.sub('#DENY\s*FILES', new + '\n    #DENY FILES', conf)
        public.writeFile(self.ap_website_conf, conf)
        return True

    # 删除某个网站禁止运行PHP
    def del_auto_index(self, args):
        '''
        # 添加某个网站禁止运行PHP
        author: zhwen<zhw@bt.cn>
        :param args: website 网站名 str
        :param args: deny_name 规则名称 str
        :return:
        '''
        self._init_conf(args.website)
        deny_name = args.deny_name
        self._set_nginx_auto_index(deny_name)
        self._set_apache_auto_index(deny_name)
        public.serviceReload()
        return public.returnMsg(True, 'Delete Successfully')

    # 检查传入参数
    def _check_args(self, args):
        if hasattr(args, 'deny_name'):
            if len(args.deny_name) < 3:
                return public.returnMsg(False, 'Rule name needs to be greater than 3 bytes')
        if hasattr(args, 'dir'):
            if not args.dir:
                return public.returnMsg(False, 'Directory cannot be empty')