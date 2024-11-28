# coding: utf-8
# -------------------------------------------------------------------
# aaPanel
# -------------------------------------------------------------------
# Copyright (c) 2015-2099 aaPanel(www.aapanel.com) All rights reserved.
# -------------------------------------------------------------------
# Author: cjxin <cjxin@aapanel.com>
# -------------------------------------------------------------------

# 备份
# ------------------------------
import os, sys, re, json, shutil, psutil, time
from panelModel.base import panelBase
import public, config, panelTask

try:
    from BTPanel import cache
except:pass

class main(panelBase):
    __table = 'task_list'
    # public.check_database_field("ssl_data.db","ssl_info")
    task_obj = panelTask.bt_task()

    def __init__(self):
        pass


    """
    @name 获取面板日志 
    """
    def get_update_logs(self,get):
        try:

            skey = 'panel_update_logs'
            res = cache.get(skey)
            if res: return res

            res = public.httpPost('https://wafapi2.aapanel.com/Api/getUpdateLogs?type=Linux',{})

            start_index = res.find('(') + 1
            end_index = res.rfind(')')
            json_data = res[start_index:end_index]

            res = json.loads(json_data)
            cache.set(skey,res,60)
        except:
            res = []

        return res

    def get_public_config(self, args):
        """
        @name 获取公共配置
        """
        public.print_log("error 3366666  原始方法: ")
        _config_obj = config.config()
        data = _config_obj.get_config(args)

        data['task_list'] = self.task_obj.get_task_lists(args)
        data['task_count'] = public.M('tasks').where("status!=?", ('1',)).count()
        data['get_pd'] = self.get_pd(args)
        data['ipv6'] = ''
        if _config_obj.get_ipv6_listen(None): data['ipv6'] = 'checked'
        data['is_local'] = ''
        if public.is_local(): data['is_local'] = 'checked'

        if data['get_pd'] and data['get_pd'][2] != -1:
            time_diff = (data['get_pd'][2]-int(time.time())) % (365*86400)
            data['active_pro_time'] = int(time.time()) - (365*86400 - time_diff)
        else:
            data['active_pro_time'] = 0
        data['status_code'] = _config_obj.get_not_auth_status()
        if os.path.exists('/www/server/panel/config/api.json'):
            try:
                res = json.loads(public.readFile('/www/server/panel/config/api.json'))
                data['api'] = 'checked' if res['open'] else ''
            except:
                public.ExecShell('rm -f /www/server/panel/config/api.json')
                data['api'] = ''
        else:
            data['api'] = ''


        data['total'] = os.path.exists('/www/server/panel/plugin/total') or os.path.exists('/www/server/panel/plugin/monitor')
        data['disk_usage'] = public.get_disk_usage(public.get_panel_path())
        data['uid'] = ''
        if os.path.exists('/www/server/panel/data/userInfo.json'):
            res = public.readFile('/www/server/panel/data/userInfo.json')
            if res:
                try:
                    res = json.loads(res)
                    data['uid'] = res['uid']
                except:
                    pass
        return data
    def get_pd(self, get):
        from BTPanel import cache
        tmp = -1
        try:
            import panelPlugin
            # get = public.dict_obj()
            # get.init = 1
            tmp1 = panelPlugin.panelPlugin().get_cloud_list(get)
        except:
            tmp1 = None
        if tmp1:
            tmp = tmp1[public.to_string([112, 114, 111])]
            ltd = tmp1.get('ltd', -1)
        else:
            ltd = -1
            tmp4 = cache.get(
                public.to_string([112, 95, 116, 111, 107, 101, 110]))
            if tmp4:
                tmp_f = public.to_string([47, 116, 109, 112, 47]) + tmp4
                if not os.path.exists(tmp_f): public.writeFile(tmp_f, '-1')
                tmp = public.readFile(tmp_f)
                if tmp: tmp = int(tmp)
        if not ltd: ltd = -1
        if tmp == None: tmp = -1
        if ltd < 1:
            if ltd == -2:
                tmp3 = public.to_string([
                    60, 115, 112, 97, 110, 32, 99, 108, 97, 115, 115, 61, 34,
                    98, 116, 108, 116, 100, 45, 103, 114, 97, 121, 34, 62, 60,
                    115, 112, 97, 110, 32, 115, 116, 121, 108, 101, 61, 34, 99,
                    111, 108, 111, 114, 58, 32, 35, 102, 99, 54, 100, 50, 54,
                    59, 102, 111, 110, 116, 45, 119, 101, 105, 103, 104, 116,
                    58, 32, 98, 111, 108, 100, 59, 109, 97, 114, 103, 105, 110,
                    45, 114, 105, 103, 104, 116, 58, 53, 112, 120, 34, 62,
                    24050, 36807, 26399, 60, 47, 115, 112, 97, 110, 62, 60, 97,
                    32, 99, 108, 97, 115, 115, 61, 34, 98, 116, 108, 105, 110,
                    107, 34, 32, 111, 110, 99, 108, 105, 99, 107, 61, 34, 98,
                    116, 46, 115, 111, 102, 116, 46, 117, 112, 100, 97, 116,
                    97, 95, 108, 116, 100, 40, 41, 34, 62, 32493, 36153, 60,
                    47, 97, 62, 60, 47, 115, 112, 97, 110, 62
                ])
            elif tmp == -1:
                tmp3 = public.to_string([
                    60, 115, 112, 97, 110, 32, 99, 108, 97, 115, 115, 61, 34,
                    98, 116, 112, 114, 111, 45, 102, 114, 101, 101, 34, 32,
                    111, 110, 99, 108, 105, 99, 107, 61, 34, 98, 116, 46, 115,
                    111, 102, 116, 46, 117, 112, 100, 97, 116, 97, 95, 99, 111,
                    109, 109, 101, 114, 99, 105, 97, 108, 95, 118, 105, 101,
                    119, 40, 41, 34, 32, 116, 105, 116, 108, 101, 61, 34,
                    28857, 20987, 21319, 32423, 21040, 21830, 19994, 29256, 34,
                    62, 20813, 36153, 29256, 60, 47, 115, 112, 97, 110, 62
                ])
            elif tmp == -2:
                tmp3 = public.to_string([
                    60, 115, 112, 97, 110, 32, 99, 108, 97, 115, 115, 61, 34,
                    98, 116, 112, 114, 111, 45, 103, 114, 97, 121, 34, 62, 60,
                    115, 112, 97, 110, 32, 115, 116, 121, 108, 101, 61, 34, 99,
                    111, 108, 111, 114, 58, 32, 35, 102, 99, 54, 100, 50, 54,
                    59, 102, 111, 110, 116, 45, 119, 101, 105, 103, 104, 116,
                    58, 32, 98, 111, 108, 100, 59, 109, 97, 114, 103, 105, 110,
                    45, 114, 105, 103, 104, 116, 58, 53, 112, 120, 34, 62,
                    24050, 36807, 26399, 60, 47, 115, 112, 97, 110, 62, 60, 97,
                    32, 99, 108, 97, 115, 115, 61, 34, 98, 116, 108, 105, 110,
                    107, 34, 32, 111, 110, 99, 108, 105, 99, 107, 61, 34, 98,
                    116, 46, 115, 111, 102, 116, 46, 117, 112, 100, 97, 116,
                    97, 95, 112, 114, 111, 40, 41, 34, 62, 32493, 36153, 60,
                    47, 97, 62, 60, 47, 115, 112, 97, 110, 62
                ])
            if tmp >= 0 and ltd in [-1, -2]:
                if tmp == 0:
                    tmp2 = public.to_string([27704, 20037, 25480, 26435])
                    tmp3 = public.to_string([
                        60, 115, 112, 97, 110, 32, 99, 108, 97, 115, 115, 61,
                        34, 98, 116, 112, 114, 111, 34, 62, 123, 48, 125, 60,
                        115, 112, 97, 110, 32, 115, 116, 121, 108, 101, 61, 34,
                        99, 111, 108, 111, 114, 58, 32, 35, 102, 99, 54, 100,
                        50, 54, 59, 102, 111, 110, 116, 45, 119, 101, 105, 103,
                        104, 116, 58, 32, 98, 111, 108, 100, 59, 34, 62, 123,
                        49, 125, 60, 47, 115, 112, 97, 110, 62, 60, 47, 115,
                        112, 97, 110, 62
                    ]).format(
                        public.to_string([21040, 26399, 26102, 38388, 65306]),
                        tmp2)
                else:
                    tmp2 = time.strftime(
                        public.to_string([37, 89, 45, 37, 109, 45, 37, 100]),
                        time.localtime(tmp))
                    tmp3 = public.to_string([
                        60, 115, 112, 97, 110, 32, 99, 108, 97, 115, 115, 61,
                        34, 98, 116, 112, 114, 111, 34, 62, 21040, 26399,
                        26102, 38388, 65306, 60, 115, 112, 97, 110, 32, 115,
                        116, 121, 108, 101, 61, 34, 99, 111, 108, 111, 114, 58,
                        32, 35, 102, 99, 54, 100, 50, 54, 59, 102, 111, 110,
                        116, 45, 119, 101, 105, 103, 104, 116, 58, 32, 98, 111,
                        108, 100, 59, 109, 97, 114, 103, 105, 110, 45, 114,
                        105, 103, 104, 116, 58, 53, 112, 120, 34, 62, 123, 48,
                        125, 60, 47, 115, 112, 97, 110, 62, 60, 97, 32, 99,
                        108, 97, 115, 115, 61, 34, 98, 116, 108, 105, 110, 107,
                        34, 32, 111, 110, 99, 108, 105, 99, 107, 61, 34, 98,
                        116, 46, 115, 111, 102, 116, 46, 117, 112, 100, 97,
                        116, 97, 95, 112, 114, 111, 40, 41, 34, 62, 32493,
                        36153, 60, 47, 97, 62, 60, 47, 115, 112, 97, 110, 62
                    ]).format(tmp2)
            else:
                tmp3 = public.to_string([
                    60, 115, 112, 97, 110, 32, 99, 108, 97, 115, 115, 61, 34,
                    98, 116, 108, 116, 100, 45, 103, 114, 97, 121, 34, 32, 111,
                    110, 99, 108, 105, 99, 107, 61, 34, 98, 116, 46, 115, 111,
                    102, 116, 46, 117, 112, 100, 97, 116, 97, 95, 108, 116,
                    100, 40, 41, 34, 32, 116, 105, 116, 108, 101, 61, 34,
                    28857, 20987, 21319, 32423, 21040, 20225, 19994, 29256, 34,
                    62, 20813, 36153, 29256, 60, 47, 115, 112, 97, 110, 62
                ])
        else:
            tmp3 = public.to_string([
                60, 115, 112, 97, 110, 32, 99, 108, 97, 115, 115, 61, 34, 98,
                116, 108, 116, 100, 34, 62, 21040, 26399, 26102, 38388, 65306,
                60, 115, 112, 97, 110, 32, 115, 116, 121, 108, 101, 61, 34, 99,
                111, 108, 111, 114, 58, 32, 35, 102, 99, 54, 100, 50, 54, 59,
                102, 111, 110, 116, 45, 119, 101, 105, 103, 104, 116, 58, 32,
                98, 111, 108, 100, 59, 109, 97, 114, 103, 105, 110, 45, 114,
                105, 103, 104, 116, 58, 53, 112, 120, 34, 62, 123, 125, 60, 47,
                115, 112, 97, 110, 62, 60, 97, 32, 99, 108, 97, 115, 115, 61,
                34, 98, 116, 108, 105, 110, 107, 34, 32, 111, 110, 99, 108,
                105, 99, 107, 61, 34, 98, 116, 46, 115, 111, 102, 116, 46, 117,
                112, 100, 97, 116, 97, 95, 108, 116, 100, 40, 41, 34, 62,
                32493, 36153, 60, 47, 97, 62, 60, 47, 115, 112, 97, 110, 62
            ]).format(
                time.strftime(
                    public.to_string([37, 89, 45, 37, 109, 45, 37, 100]),
                    time.localtime(ltd)))

        return tmp3, tmp, ltd

    @staticmethod
    def set_backup_path(get):
        try:
            backup_path = get.backup_path.strip().rstrip("/")
        except AttributeError:
            return public.returnMsg(False,  public.lang("The parameter is incorrect"))

        if not os.path.exists(backup_path):
            return public.returnMsg(False,  public.lang("The specified directory does not exist"))

        if backup_path[-1] == "/":
            backup_path = backup_path[:-1]

        import files
        try:
            from BTPanel import session
        except:
            session = None
        fs = files.files()

        if not fs.CheckDir(get.backup_path):
            return public.returnMsg(False,  public.lang('You cannot use the system critical directory as the default backup directory'))
        if session is not None:
            session['config']['backup_path'] = os.path.join('/', backup_path)
        db_backup = backup_path + '/database'
        site_backup = backup_path + '/site'

        if not os.path.exists(db_backup):
            try:
                os.makedirs(db_backup, 384)
            except:
                public.ExecShell('mkdir -p ' + db_backup)

        if not os.path.exists(site_backup):
            try:
                os.makedirs(site_backup, 384)
            except:
                public.ExecShell('mkdir -p ' + site_backup)

        public.M('config').where("id=?", ('1',)).save('backup_path', (get.backup_path,))
        public.WriteLog('TYPE_PANEL', 'PANEL_SET_SUCCESS', (get.backup_path,))

        public.restart_panel()
        return public.returnMsg(True,  public.lang("The setup was successful"))

    def get_soft_status(self,get):
        if not hasattr(get,'name'): return public.returnMsg(False, public.lang('The parameter is incorrect'))
        name = get.name.strip()
        if name == 'sqlite':
            return public.returnMsg(True,'accordWith')
        if os.path.exists('/www/server/{}'.format(name)) and len(os.listdir('/www/server/{}'.format(name))) > 2:
            return public.returnMsg(True,'accordWith')
        if name == ['mysql','pgsql','sqlserver','mongodb','redis']:
            count = public.M('database_servers').where("LOWER(db_type)=LOWER(?)", (name,)).count()
            if count > 0: return public.returnMsg(True,'accordWith')
        return public.returnMsg(False,'Not true')