# coding: utf-8
# -------------------------------------------------------------------
# aapanel
# -------------------------------------------------------------------
# Copyright (c) 2015-2099 aapanel(http://www.aapanel.com) All rights reserved.
# -------------------------------------------------------------------
# Author: miku <miku@bt.cn>
# -------------------------------------------------------------------
import json
import os
import re
import sys

if "/www/server/panel/class" not in sys.path:
    sys.path.insert(0, "/www/server/panel/class")
if "/www/server/panel/class_v2" not in sys.path:
    sys.path.insert(0, "/www/server/panel/class_v2")
if "/www/server/panel" not in sys.path:
    sys.path.insert(0, "/www/server/panel")

import public
from BTPanel import app
import crontab_v2 as crontab
from mod.project.backup_restore.base_util import BaseUtil
from mod.project.backup_restore.config_manager import ConfigManager


class CrontabModule(BaseUtil, ConfigManager):
    def __init__(self):
        super().__init__()
        self.base_path = '/www/backup/backup_restore'
        self.bakcup_task_json = self.base_path + '/backup_task.json'

    def backup_crontab_data(self, timestamp):
        self.print_log("====================================================", "backup")
        self.print_log(public.lang("Starting a Backup Scheduled Task"), "backup")

        backup_path = self.base_path + "/{timestamp}_backup/crontab".format(timestamp=timestamp)
        if not os.path.exists(backup_path):
            public.ExecShell('mkdir -p {}'.format(backup_path))

        field = ('id,name,type,where1,where_hour,where_minute,echo,addtime,status,'
                 'save,backupTo,sName,sBody,sType,urladdress,save_local,notice,'
                 'notice_channel,db_type,split_type,split_value,type_id,rname,'
                 'keyword,post_param,flock,time_set,backup_mode,db_backup_path,'
                 'time_type,special_time,log_cut_path,user_agent,version,table_list,result,second')
        crontab_data = public.M('crontab').order("id asc").field(field).select()
        for task in crontab_data:
            task['type_id'] = ""

        crontab_json_path = "{}/crontab.json".format(backup_path)
        public.WriteFile(crontab_json_path, json.dumps(crontab_data))
        for item in crontab_data:
            self.print_log(public.lang("Crontab Task {} ✓".format(item['name'])), "backup")

        public.ExecShell(f"\cp -rpa /www/server/cron/* {backup_path}/")
        crontab_info = {
            'status': 2,
            'msg': None,
            'crontab_json': crontab_json_path,
            'file_sha256': self.get_file_sha256(crontab_json_path)
        }
        self.print_log(public.lang("Backup Crontab Task completion"), 'backup')

        data_list = self.get_backup_data_list(timestamp)
        data_list['data_list']['crontab'] = crontab_info
        self.update_backup_data_list(timestamp, data_list)

    def _add_crontab(self, crontab_item: dict, timestamp: int) -> None:
        if crontab_item['name'] in ("Domain SSL Renew Let's Encrypt Certificate", "Renew Let's Encrypt Certificate"):
            import acme_v2

            if crontab_item['name'] == "Domain SSL Renew Let's Encrypt Certificate":
                acme_v2.acme_v2().set_crond_v2()
            elif crontab_item['name'] == "Renew Let's Encrypt Certificate":
                acme_v2.acme_v2().set_crond()

            self.print_log(
                public.lang(f"Crontab Task: {crontab_item['name']} Add successfully ✓"),
                "restore"
            )
            return

        if crontab_item['name'] == "[Do not delete] Resource Manager - Get Process Traffic":
            return

        s_body = crontab_item['sBody']
        s_body = re.sub(r'sudo -u .*? bash -c \'(.*?)\'', r'\1', s_body)
        new_crontab = {
            "name": crontab_item['name'],
            "echo": crontab_item['echo'],
            "type": crontab_item['type'],
            "where1": crontab_item['where1'],
            "hour": crontab_item['where_hour'],
            "minute": crontab_item['where_minute'],
            "status": crontab_item['status'],
            "save": crontab_item['save'],
            "backupTo": crontab_item['backupTo'],
            "sType": crontab_item['sType'],
            "sBody": s_body,
            "sName": crontab_item['sName'],
            "urladdress": crontab_item['urladdress'],
            "save_local": crontab_item['save_local'],
            "notice": crontab_item['notice'],
            "notice_channel": crontab_item['notice_channel'],
            "db_type": crontab_item['db_type'],
            "split_type": crontab_item['split_type'],
            "split_value": crontab_item['split_value'],
            "keyword": crontab_item['keyword'],
            "post_param": crontab_item['post_param'],
            "flock": crontab_item['flock'],
            "time_set": crontab_item['time_set'],
            "backup_mode": crontab_item['backup_mode'],
            "db_backup_path": crontab_item['db_backup_path'],
            "time_type": crontab_item['time_type'],
            "special_time": crontab_item['special_time'],
            "user_agent": crontab_item['user_agent'],
            "version": crontab_item['version'],
            "table_list": crontab_item['table_list'],
            "result": crontab_item['result'],
            "log_cut_path": crontab_item['log_cut_path'],
            "rname": crontab_item['rname'],
            "type_id": crontab_item['type_id'],
            "second": crontab_item.get('second', ''),
        }
        result = crontab.crontab().AddCrontab(new_crontab)

        crontab_backup_path = self.base_path + f"/{timestamp}_backup/crontab"

        back_up_echo_file = os.path.join(crontab_backup_path, crontab_item['echo'])
        panel_echo_file = f"/www/server/cron/{crontab_item['echo']}"
        if self.overwrite or not os.path.exists(panel_echo_file):
            public.ExecShell(
                f"\cp -rpa {back_up_echo_file} {panel_echo_file}"
            )

        if result['status'] != 0:
            error_res = public.find_value_by_key(result, key="result", default="fail")
            self.print_log(
                public.lang(
                    f"Crontab Task: {crontab_item['name']} add fail, "
                    f"error: {error_res}, skip..."),
                "restore"
            )
        else:
            self.print_log(
                public.lang(f"Crontab Task: {crontab_item['name']} Add successfully ✓"),
                "restore"
            )

    def restore_crontab_data(self, timestamp):
        self.print_log("==================================", "restore")
        self.print_log(public.lang("Start restoring Crontab Task"), "restore")
        restore_data = self.get_restore_data_list(timestamp)
        cron_list = public.M('crontab').select()
        cron_name_list = [i['name'] for i in cron_list]
        crontab_data_json = restore_data['data_list']['crontab']['crontab_json']
        restore_data['data_list']['crontab']['restore_status'] = 1
        self.update_restore_data_list(timestamp, restore_data)
        crontab_data = json.loads(public.ReadFile(crontab_data_json))
        with app.app_context():
            for crontab_item in crontab_data:
                if self.overwrite:
                    try:
                        crontab.crontab().DelCrontab(public.to_dict_obj({"id": crontab_item['id']}))
                    except:
                        pass
                    self._add_crontab(crontab_item, timestamp)
                else:  # not overwrite
                    if crontab_item['name'] not in cron_name_list:
                        self._add_crontab(crontab_item, timestamp)
                    else:
                        self.print_log(public.lang(f"Crontab Task: {crontab_item['name']} ✓"), "restore")
        self.print_log(public.lang("Crontab Task complished"), "restore")
        restore_data['data_list']['crontab']['restore_status'] = 2
        self.update_restore_data_list(timestamp, restore_data)

    def reload_crontab(self):
        try:
            crontab.crontab().CrondReload()
        except:
            pass


if __name__ == '__main__':
    # 获取命令行参数
    if len(sys.argv) < 2:
        print("Usage: btpython backup_manager.py <method> <timestamp>")
        sys.exit(1)
    method_name = sys.argv[1]  # 方法名  
    timestamp = sys.argv[2]
    crontab_manager = CrontabModule()  # 实例化对象
    if hasattr(crontab_manager, method_name):  # 检查方法是否存在
        method = getattr(crontab_manager, method_name)  # 获取方法
        method(timestamp)  # 调用方法
    else:
        print(f"Error: method '{method_name}' not found")
