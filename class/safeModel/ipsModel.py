#coding: utf-8
#-------------------------------------------------------------------
# 宝塔Linux面板
#-------------------------------------------------------------------
# Copyright (c) 2015-2099 宝塔软件(http://bt.cn) All rights reserved.
#-------------------------------------------------------------------
# Author: cjxin <cjxin@bt.cn>
#-------------------------------------------------------------------

# 商用IP库
#------------------------------
import os,re,json,time
from safeModel.base import safeBase
import public


class main(safeBase):

    _sfile = '{}/data/ip_area.json'.format(public.get_panel_path())
    def __init__(self):
        try:
            self.user_info = public.get_user_info()
        except:
            self.user_info = None

    def get_ip_area(self,get):
        """
        @获取IP地址所在地
        @param get: dict/array
        """
        ips = get['ips']
        arrs,result = [],{}
        for ip in ips:
            info = {}
            res = self.__check_ip_area(ip)
            if res:
                if type(res) == str:
                    info['info'] = res
                else:
                    info = res
                result[ip] = info
            else:
                arrs.append(ip)

        if len(arrs) > 0:
            data = self.__get_cloud_ip_info(arrs)
            for ip in data:
                result[ip] = data[ip]
        return result

    def __check_ip_area(self,ip):
        """
        @检查IP地址所在地
        @param ip:
        """

        if not public.is_ipv4(ip):
            return 'Unknown'
        if public.is_local_ip(ip):
            return 'Intranet'

        data = self.get_ip_area_cache()
        if ip in data:
            return data[ip]
        return False


    def __get_cloud_ip_info(self,ips):
        """
        @获取IP地址所在地
        @param ips:
        """
        result = {}
        try:

            data = {}
            data['ip'] = ','.join(ips)
            data['uid'] = self.user_info['uid']
            data["serverid"]=self.user_info["serverid"]
            res = public.httpPost('https://www.bt.cn/api/panel/get_ip_info',data)
            res = json.loads(res)

            data = self.get_ip_area_cache()
            for key in res:
                if not public.is_ipv4(key): continue

                info = res[key]
                if not res[key]['city'].strip() and not res[key]['continent'].strip():
                    info = {'info':'Intranet'}
                else:
                    info['info'] = '{} {} {} {}'.format(info['carrier'],info['country'],info['province'],info['city']).strip()

                data[key] = info
                result[key] = info
            self.set_ip_area_cache(data)
        except: pass
        return result


    def get_ip_area_cache(self):
        """
        @获取IP地址所在地
        @param get:
        """
        data = {}
        try:
            data = json.loads(public.readFile(self._sfile))
        except:
            public.writeFile(self._sfile,json.dumps({}))
        return data

    def set_ip_area_cache(self,data):
        """
        @设置IP地址所在地
        @param data:
        """
        public.writeFile(self._sfile,json.dumps(data))
        return True