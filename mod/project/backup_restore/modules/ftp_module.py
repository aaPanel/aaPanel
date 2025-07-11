# coding: utf-8
# -------------------------------------------------------------------
# aapanel
# -------------------------------------------------------------------
# Copyright (c) 2015-2099 aapanel(http://www.aapanel.com) All rights reserved.
# -------------------------------------------------------------------
# Author: miku <miku@bt.cn>
# -------------------------------------------------------------------
import os.path
import sys
import time
import warnings

if "/www/server/panel/class" not in sys.path:
    sys.path.insert(0, "/www/server/panel/class")
if "/www/server/panel/class_v2" not in sys.path:
    sys.path.insert(0, "/www/server/panel/class_v2")
if "/www/server/panel" not in sys.path:
    sys.path.insert(0, "/www/server/panel")

import public
from BTPanel import app
import ftp_v2 as ftp_client
from mod.project.backup_restore.data_manager import DataManager

warnings.filterwarnings("ignore", category=SyntaxWarning)


class FtpModule(DataManager):
    def __init__(self):
        super().__init__()
        self.base_path = '/www/backup/backup_restore'
        self.bakcup_task_json = self.base_path + '/backup_task.json'

    def backup_ftp_data(self, timestamp=None):
        self.print_log("==================================", "backup")
        self.print_log(public.lang("Start backing up FTP account information"), "backup")
        ftp_data = public.M('ftps').field('name,pid,id,password,path,ps').select()
        filtered_ftp = []
        for ftp in ftp_data:
            try:
                if ftp.get('pid', 0) == 0:
                    ftp['related_site'] = ''
                else:
                    ftp['related_site'] = self._get_current_site_name_by_pid(ftp.get('pid'))

                ftp['status'] = 2
                ftp['msg'] = None
                filtered_ftp.append(ftp)
                self.print_log(public.lang("{} user ✓").format(ftp['name']), "backup")
            except Exception as e:
                self.print_log(public.lang("Failed to backup FTP account information: {}").format(str(e)), "backup")
                ftp['status'] = 3
                ftp['msg'] = str(e)
                filtered_ftp.append(ftp)
                continue

        self.print_log(public.lang("FTP account information backup completed"), "backup")
        return filtered_ftp

    def _add_ftp_user(self, ftp_client: ftp_client, ftp_data: dict) -> int:
        """
        :return: ftp_data restore_status
        """
        log_str = public.lang("Restoring {} account").format(ftp_data['name'])
        args = public.dict_obj()
        args.ftp_username = ftp_data['name']
        args.path = ftp_data['path']
        args.ftp_password = ftp_data['password']
        args.ps = ftp_data['ps']
        args.pid = self._get_current_pid_by_site_name(
            os.path.basename(ftp_data.get('path', ''))
        )
        res = ftp_client.ftp().AddUser(args)
        if res['status'] is False:
            self.replace_log(log_str, public.lang("FTP creation failed: {}").format(res.get('message', 'create fail')),
                             "restore")
            return 3
        else:
            new_log_str = public.lang("{} account ✓").format(ftp_data['name'])
            self.replace_log(log_str, new_log_str, "restore")
            return 2

    def restore_ftp_data(self, timestamp=None):
        self.print_log("====================================================", "restore")
        self.print_log(public.lang("Start restoring FTP account configuration"), "restore")
        restore_data = self.get_restore_data_list(timestamp)
        with app.app_context():
            for ftp_data in restore_data['data_list']['ftp']:
                try:
                    if_exist = public.M('ftps').where('name=?', (ftp_data["name"],)).find()
                    log_str = public.lang("Restoring {} account").format(ftp_data['name'])
                    if if_exist:
                        self.print_log(log_str, "restore")
                        if not self.overwrite:
                            self.replace_log(log_str, public.lang("{} account ✓").format(if_exist.get('name', 'ftp')),
                                             "restore")
                            continue
                        else:
                            ftp_client.ftp().DeleteUser(public.to_dict_obj(
                                {"id": if_exist['id'], "username": if_exist['name']}
                            ))
                            time.sleep(0.5)
                            ftp_data['restore_status'] = self._add_ftp_user(ftp_client, ftp_data)

                    else:
                        ftp_data['restore_status'] = self._add_ftp_user(ftp_client, ftp_data)
                        self.replace_log(
                            log_str,
                            public.lang("ftp: [{}] account restored successfully ✓").format(
                                ftp_data.get('name', 'ftp')),
                            "restore"
                        )

                except Exception as e:
                    import traceback
                    public.print_log(traceback.format_exc())
                    self.print_log(public.lang("Failed to restore FTP account configuration: {}").format(str(e)),
                                   "restore")

                self.update_restore_data_list(timestamp, restore_data)

        self.print_log(public.lang("FTP account configuration restoration completed"), "restore")


if __name__ == '__main__':
    # 获取命令行参数
    if len(sys.argv) < 3:
        print("Usage: btpython backup_manager.py <method> <timestamp>")
        sys.exit(1)
    method_name = sys.argv[1]  # 方法名
    timestamp = sys.argv[2]  # IP地址
    ftp_module = FtpModule()  # 实例化对象
    if hasattr(ftp_module, method_name):  # 检查方法是否存在
        method = getattr(ftp_module, method_name)  # 获取方法
        method(timestamp)  # 调用方法
    else:
        print(f"Error: Method '{method_name}' not found")
