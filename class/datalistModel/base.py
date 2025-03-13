# coding: utf-8
# -------------------------------------------------------------------
# 宝塔Linux面板
# -------------------------------------------------------------------
# Copyright (c) 2015-2099 宝塔软件(http://bt.cn) All rights reserved.
# -------------------------------------------------------------------
# Author: cjxin <cjxin@bt.cn>
# -------------------------------------------------------------------
# 面板获取列表公共库
# ------------------------------

import os,sys,time,json,db,re
import public
try:
    from BTPanel import session
except:
    session = None


class dataBase:

    quota_conf = os.path.join(public.get_panel_path(), "config/quota_list.json")

    def __init__(self):
        pass

    """
    @name 获取配额数据列表
    """
    def get_quota_list(self):
        quota_dict = {}
        try:
            quota_dict = json.loads(public.readFile(self.quota_conf))
        except:
            pass
        return quota_dict


    """
    @name 批量获取所有容量配额
    """
    def get_all_quota(self,paths = []):
        n_paths = []
        confs = self.get_quota_list()


        for path in paths:
            if path in n_paths: continue
            if not path in confs: continue
            n_paths.append(path.strip())

        res = public.get_size_total(n_paths)

        n_data = {}
        for val in n_paths:
            n_data[val] = {"used":0,"size":0,"quota_push":{"size":0,"used":0},"quota_storage":{"size":0,"used":0}}
            if val in confs.keys():
                n_data[val] = confs[val]

            n_data[val]['used'] = -1
            for key in res.keys():
                if key != val: continue

                n_data[val]['used'] = res[val]
                n_data[val]['quota_storage']['used'] = res[val]
                n_data[val]['quota_push']['used'] = res[val]

        # print(n_data)
        return n_data
    

    def _decrypt(self, data):
        import PluginLoader
        if not isinstance(data, str): return data
        if not data: return data
        if data.startswith('BT-0x:'):
            res = PluginLoader.db_decrypt(data[6:])['msg']
            return res
        return data

    # 获取用户权限列表
    def get_user_power(self, get=None):
        user_Data = 'all'
        try:
            uid = session.get('uid')
            if uid != 1 and uid:
                plugin_path = '/www/server/panel/plugin/users'
                if os.path.exists(plugin_path):
                    user_authority = os.path.join(plugin_path, 'authority')
                    if os.path.exists(user_authority):
                        if os.path.exists(os.path.join(user_authority, str(uid))):
                            try:
                                data = json.loads(self._decrypt(public.ReadFile(os.path.join(user_authority, str(uid)))))
                                if data['role'] == 'administrator':
                                    user_Data = 'all'
                                else:
                                    user_Data = json.loads(self._decrypt(public.ReadFile(os.path.join(user_authority, str(uid) + '.data'))))
                            except:
                                user_Data = {}
                        else:
                            user_Data = {}
        except:
            public.print_error()
            pass
        return user_Data