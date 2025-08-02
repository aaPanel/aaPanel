# coding: utf-8
# -------------------------------------------------------------------
# aapanel
# -------------------------------------------------------------------
# Copyright (c) 2015-2099 aapanel(http://www.aapanel.com) All rights reserved.
# -------------------------------------------------------------------
# Author: miku <wzz@bt.cn>
# -------------------------------------------------------------------
import datetime
import json
import os
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
from mod.project.backup_restore.modules.site_module import SiteModule
from mod.project.backup_restore.modules.database_module import DatabaseModule
from mod.project.backup_restore.modules.ftp_module import FtpModule

from mod.project.backup_restore.modules.crontab_module import CrontabModule
from mod.project.backup_restore.modules.ssh_module import SshModule
from mod.project.backup_restore.modules.firewall_module import FirewallModule
from mod.project.backup_restore.modules.mail_module import MailModule
from mod.project.backup_restore.modules.ssl_model import SSLModel
from mod.project.backup_restore.modules.plugin_module import PluginModule

warnings.filterwarnings("ignore", category=SyntaxWarning)


class RestoreManager(SiteModule, DatabaseModule, FtpModule, SSLModel, CrontabModule, SshModule,
                     FirewallModule, MailModule, PluginModule):
    def __init__(self, overwrite: int = 0):
        super().__init__()
        self.base_path = '/www/backup/backup_restore'
        self.bakcup_task_json = self.base_path + '/backup_task.json'
        self.backup_log_file = self.base_path + '/backup.log'
        self.backup_pl_file = self.base_path + '/backup.pl'
        self.backup_success_file = self.base_path + '/success.pl'
        self.backup_save_config = self.base_path + '/backup_save_config.json'
        self.history_log_path = '/www/backup/backup_restore/history/log'
        self.history_info_path = '/www/backup/backup_restore/history/info'
        self.restore_log_file = self.base_path + '/restore.log'
        self.restore_pl_file = self.base_path + '/restore.pl'
        self.restore_success_file = self.base_path + '/restore_success.pl'
        self.migrate_backup_info_path = '/www/backup/backup_restore/migrate_backup_info.json'
        self.overwrite = overwrite  # 强制还原标志

    def restore_data(self, timestamp):
        """
        还原数据
        """
        if os.path.exists(self.restore_log_file):
            public.ExecShell("rm -f {}".format(self.restore_log_file))

        if os.path.exists(self.restore_pl_file):
            return public.returnMsg(False, public.lang("A restore process is already running!"))

        try:
            public.WriteFile(self.restore_pl_file, timestamp)
            backup_file = str(timestamp) + "_backup.tar.gz"
            file_names = os.listdir(self.base_path)
            for file in file_names:
                if backup_file in file:
                    backup_file = file

            if os.path.exists(self.migrate_backup_info_path):
                backup_list = []
                if os.path.exists(self.bakcup_task_json):
                    backup_list = json.loads(public.ReadFile(self.bakcup_task_json))
                migrate_backup_info = json.loads(public.ReadFile(self.migrate_backup_info_path))
                backup_list.append(migrate_backup_info)
                public.ExecShell("rm -f {}".format(self.migrate_backup_info_path))
                public.WriteFile(self.bakcup_task_json, json.dumps(backup_list))
                time.sleep(1)

            backup_conf = self.get_backup_conf(timestamp)
            backup_conf['restore_status'] = 1
            self.save_backup_conf(timestamp, backup_conf)

            self.print_log("==================================", "restore")
            self.print_log(public.lang("Start decompressing the data package"), "restore")
            try:
                public.ExecShell("rm -rf {}/{}_backup".format(self.base_path, timestamp))
            except:
                pass

            if not os.path.exists(self.base_path + "/{timestamp}_backup".format(timestamp=timestamp)):
                public.ExecShell("cd {}/ && tar -xvf {}".format(self.base_path, backup_file))

            restore_data_path = self.base_path + "/{timestamp}_backup".format(timestamp=timestamp)
            public.ExecShell("\cp -rpa {}/backup.json {}/restore.json".format(restore_data_path, restore_data_path))

            restore_info = self.get_restore_data_list(timestamp)
            restore_info["force_restore"] = self.overwrite  # 覆盖标志
            restore_info['restore_status'] = 1  # 更新状态
            self.update_restore_data_list(timestamp, restore_info)

            start_time = int(time.time())
            # ============================= START ==================================
            self.print_log(public.lang("Start restoring data"), "restore")
            # ============================= env ====================================
            try:
                self.restore_env(timestamp)
            except Exception as e:
                public.print_log(f"restore env error: {str(e)}")

            # ============================= site ====================================
            try:
                self.restore_site_data(timestamp)
            except Exception as e:
                public.print_log("restore site error: {}".format(str(e)))
            finally:
                self.chmod_dir_file("/www/wwwroot", dir_mode=0o755, file_mode=0o644)

            # ============================= ftp =====================================
            try:
                self.restore_ftp_data(timestamp)
            except Exception as e:
                public.print_log("restore ftp error: {}".format(str(e)))

            # ============================= database =================================
            try:
                self.restore_database_data(timestamp)
            except Exception as e:
                public.print_log("restore database error: {}".format(str(e)))
            finally:
                if not self.overwrite:
                    try:  # 补全关系
                        self.fix_wp_onekey(timestamp)
                    except Exception as e:
                        public.print_log("fix forign key error: {}".format(str(e)))

            # ============================= ssl ======================================
            try:
                self.restore_ssl_data(timestamp)
            except Exception as e:
                public.print_log("restore ssl error: {}".format(str(e)))

            # ============================= cron task ================================
            try:
                self.restore_crontab_data(timestamp)
            except Exception as e:
                public.print_log("restore cron task error: {}".format(str(e)))
            finally:
                self.reload_crontab()

            # ============================== ssh ======================================
            # TDDO: 存在问题，下个版本修复
            # try:
            #     SshModule().restore_ssh_data(timestamp)
            # except Exception as e:
            #     public.print_log("restore ssh error: {}".format(str(e)))

            # ============================= firewall ==================================
            try:
                self.restore_firewall_data(timestamp)
            except Exception as e:
                public.print_log("restore firewall error: {}".format(str(e)))

            # ============================= mail ======================================
            try:
                self.restore_vmail_data(timestamp)
            except Exception as e:
                public.print_log("restore mail error: {}".format(str(e)))

            # ============================= plugin ====================================
            try:
                self.restore_plugin_data(timestamp)
            except Exception as e:
                public.print_log("restore plugin error: {}".format(str(e)))

            # ============================= END =======================================

            end_time = int(time.time())
            done_time = datetime.datetime.fromtimestamp(int(end_time)).strftime('%Y-%m-%d %H:%M:%S')
            total_time = end_time - start_time
            backup_conf = self.get_backup_conf(timestamp)
            backup_conf['restore_status'] = 2
            backup_conf['restore_done_time'] = done_time
            backup_conf['restore_total_time'] = total_time
            self.save_backup_conf(timestamp, backup_conf)

            restore_info['restore_status'] = 2
            restore_info['restore_done_time'] = done_time
            restore_info['restore_total_time'] = total_time
            self.update_restore_data_list(timestamp, restore_info)

            self.print_log("==================================", "restore")
            self.print_log(public.lang("Data restoration completed"), "restore")

            public.WriteFile(self.restore_success_file, timestamp)
            public.ExecShell("rm -f {}".format(self.restore_pl_file))
            if not os.path.exists(self.history_log_path):
                public.ExecShell("mkdir -p {}".format(self.history_log_path))
            if not os.path.exists(self.history_info_path):
                public.ExecShell("mkdir -p {}".format(self.history_info_path))

            hitory_log_file = self.history_log_path + '/' + str(timestamp) + '_restore.log'
            history_info_file = self.history_info_path + '/' + str(timestamp) + '_restore.info'
            public.WriteFile(
                hitory_log_file,
                public.ReadFile("/www/backup/backup_restore/restore.log".format(timestamp))
            )
            public.WriteFile(
                history_info_file,
                public.ReadFile("/www/backup/backup_restore/{}_backup/restore.json".format(timestamp))
            )
            if os.path.exists("/www/server/panel/data/migration.pl"):
                public.ExecShell("rm -f /www/server/panel/data/migration.pl")

            # 重启服务
            public.ServiceReload()
            time.sleep(2)
            public.ExecShell("/etc/init.d/bt restart")
        except Exception as e:
            return public.returnMsg(False, public.lang("Data restoration failed: {}").format(str(e)))
        finally:
            if os.path.exists(self.restore_pl_file):
                public.ExecShell("rm -f {}".format(self.restore_pl_file))

    def get_restore_log(self, timestamp):
        restore_log_file = self.base_path + '/restore.log'
        history_log_file = self.history_log_path + '/' + str(timestamp) + '_restore.log'
        if os.path.exists(self.restore_pl_file):
            restore_timestamp = int(public.ReadFile(self.restore_pl_file))
            if int(restore_timestamp) == int(timestamp):
                return public.ReadFile(restore_log_file)
        if os.path.exists(history_log_file):
            return public.ReadFile(history_log_file)
        else:
            return ""

    def get_restore_details(self, timestamp):
        history_info_file = self.history_info_path + '/' + str(timestamp) + '_restore.info'
        if not os.path.exists(history_info_file):
            return public.fail_v2(public.lang("File does not exist"))

        restore_info = json.loads(public.ReadFile(history_info_file))
        restore_info = self.process_detail(restore_info)

        restore_task_info = self.get_backup_conf(timestamp)
        restore_info['backup_file_size'] = restore_task_info['backup_file_size']
        restore_info['backup_file_sha256'] = restore_task_info['backup_file_sha256']
        restore_info['create_time'] = restore_task_info['create_time']
        restore_info['backup_time'] = restore_task_info['backup_time']
        restore_info['backup_file'] = restore_task_info['backup_file']
        restore_info['backup_path'] = restore_task_info['backup_path']
        restore_info['restore_done_time'] = restore_task_info['restore_done_time']
        restore_info['restore_total_time'] = restore_task_info['restore_total_time']
        restore_info['type'] = "restore"
        return public.success_v2(restore_info)

    # todo 弃用
    def get_restore_progress(self, get=None):
        """
        获取还原进度信息
        @param get: object 包含请求参数
        @return: dict 还原进度信息
        """
        # 设置相关文件路径
        restore_pl_file = self.base_path + '/restore.pl'
        restore_log_file = self.base_path + '/restore.log'
        restore_success_file = self.base_path + '/restore_success.pl'

        # 创建处理已完成备份的函数，减少代码重复
        def create_completed_result(restore_timestamp):
            if not restore_timestamp:
                return public.ReturnMsg(False, public.lang("Restore completed but unable to get restore timestamp"))

            if not os.path.exists(self.bakcup_task_json):
                return public.ReturnMsg(False, public.lang("Restore configuration file does not exist"))

            restore_configs = json.loads(public.ReadFile(self.bakcup_task_json))
            success_data = next(
                (item for item in restore_configs if str(item.get('timestamp')) == str(restore_timestamp)), {})

            return {
                "task_type": "restore",
                "task_status": 2,
                "backup_data": None,
                "backup_name": None,
                "data_backup_status": 2,
                "progress": 100,
                "msg": None,
                'exec_log': public.ReadFile(restore_log_file) if os.path.exists(restore_log_file) else "",
                'timestamp': restore_timestamp,
                'backup_file_info': success_data
            }

        # 检查备份是否已完成
        if os.path.exists(restore_success_file):
            success_time = int(os.path.getctime(restore_success_file))
            local_time = int(time.time())
            # 如果success文件创建时间在10秒内，说明备份刚刚完成
            if success_time + 10 > local_time:
                try:
                    restore_timestamp = public.ReadFile(restore_success_file).strip()
                    return public.ReturnMsg(True, create_completed_result(restore_timestamp))
                except Exception as e:
                    public.ExecShell("rm -f {}".format(restore_success_file))
                    return public.ReturnMsg(False,
                                            public.lang("Error getting restore completion information: {}").format(
                                                str(e)))
            else:
                # 超过10秒，删除success文件
                public.ExecShell("rm -f {}".format(restore_success_file))

        # 检查是否有备份进程运行
        try:
            # 检查备份进程锁文件
            if os.path.exists(restore_pl_file):
                timestamp = public.ReadFile(restore_pl_file).strip()
                if not timestamp:
                    return public.ReturnMsg(False, public.lang(
                        "Restore process is running, but unable to get restore timestamp"))
            else:
                # 等待2秒，可能是还原刚刚完成
                time.sleep(2)
                if os.path.exists(restore_success_file):
                    success_time = int(os.path.getctime(restore_success_file))
                    local_time = int(time.time())
                    if success_time + 10 > local_time:
                        restore_timestamp = public.ReadFile(restore_success_file).strip()
                        return public.ReturnMsg(True, create_completed_result(restore_timestamp))

                # 再次检查是否有备份进程
                if os.path.exists(restore_success_file):
                    timestamp = public.ReadFile(restore_success_file).strip()
                    if not timestamp:
                        return public.ReturnMsg(False, public.lang(
                            "Restore process is running, but unable to get restore timestamp"))
                else:
                    return public.ReturnMsg(False, public.lang(
                        "No restore task found, please check the restore list to see if the restore is complete"))

            # 读取备份配置文件
            restore_json_path = f"{self.base_path}/{timestamp}_backup/restore.json"
            count = 0
            while 1:
                if count >= 3:
                    return public.ReturnMsg(False, public.lang("Restore configuration file does not exist: {}").format(
                        restore_json_path))
                count += 1
                if not os.path.exists(restore_json_path):
                    time.sleep(1)
                else:
                    break

            conf_data = json.loads(public.ReadFile(restore_json_path))
        except Exception as e:
            return public.ReturnMsg(False, public.lang("Error getting restore progress information: {}").format(str(e)))

        # 读取备份日志
        restore_log_data = public.ReadFile(restore_log_file) if os.path.exists(restore_log_file) else ""

        # 定义备份类型及其处理逻辑
        restore_types = [
            {
                'type': 'site',
                'data_key': 'site',
                'display_name': 'site',
                'progress': 30
            },
            {
                'type': 'database',
                'data_key': 'database',
                'display_name': 'database',
                'progress': 60
            },
            {
                'type': 'ftp',
                'data_key': 'ftp',
                'display_name': 'ftp',
                'progress': 70
            },
            {
                'type': 'ssh',
                'data_key': 'ssh',
                'display_name': 'ssh',
                'progress': 75
            },
            {
                'type': 'firewall',
                'data_key': 'firewall',
                'display_name': 'firewall',
                'progress': 90
            }
        ]

        # 检查软件环境状态
        if "data_list" in conf_data and "soft" in conf_data["data_list"]:
            soft_data = conf_data["data_list"]["soft"]
            if "status" in soft_data and soft_data["status"].get("status") == 1:
                name = soft_data["status"].get("name", "unknown")
                # version = soft_data["status"].get("version", "unknown")
                return public.ReturnMsg(True, {
                    "task_type": "restore",
                    "task_status": 1,
                    "data_type": "soft",
                    "name": name,
                    "data_backup_status": 1,
                    "progress": 20,
                    "msg": soft_data["status"].get("err_msg"),
                    'exec_log': restore_log_data,
                    'timestamp': timestamp
                })

        # 检查各类型备份进度
        for restore_type in restore_types:
            items = conf_data.get("data_list", {}).get(restore_type['data_key'], [])
            for item in items:
                try:
                    if item.get("restore_status") == 2:
                        continue

                    return public.ReturnMsg(True, {
                        "task_type": "restore",
                        "task_status": 1,
                        "data_type": restore_type['type'],
                        "name": item.get("name", public.lang("Unknown {}").format(restore_type['display_name'])),
                        "data_backup_status": item.get("status", 0),
                        "progress": restore_type['progress'],
                        "msg": item.get("msg"),
                        'exec_log': restore_log_data,
                        'timestamp': timestamp
                    })
                except:
                    return public.ReturnMsg(True, {
                        "task_type": "restore",
                        "task_status": 1,
                        "data_type": public.lang("Server Configuration"),
                        "name": public.lang("Server Configuration"),
                        "data_backup_status": 2,
                        "progress": 90,
                        "msg": None,
                        'exec_log': restore_log_data,
                        'timestamp': timestamp
                    })

        # 检查数据打包进度
        try:
            restore_status = conf_data.get('restore_status')
            if restore_status == 1:
                return public.ReturnMsg(True, {
                    "task_type": "restore",
                    "task_status": 1,
                    "data_type": "tar",
                    "name": public.lang("Data Decompression"),
                    "data_backup_status": 1,
                    "progress": 10,
                    'exec_log': restore_log_data,
                    'timestamp': timestamp
                })
        except Exception:
            # 可能没有backup_status字段，继续处理
            pass

        # 如果没有发现进行中的任务，但有备份进程
        if timestamp:
            return {
                "backup_data": "unknown",
                "backup_name": public.lang("Unknown Task"),
                "data_backup_status": 1,
                "progress": 10,
                'backup_msg': public.lang("Preparing to restore data"),
                'backup_log': restore_log_data,
                'timestamp': timestamp
            }

        return public.ReturnMsg(
            False,
            public.lang(
                "No ongoing restore task found, please check the restore list to see if the restore is complete"
            )
        )


if __name__ == '__main__':
    # 获取命令行参数
    if len(sys.argv) < 3:
        print("Usage: btpython restore_manager.py <method> <timestamp>")
        sys.exit(1)
    method_name = sys.argv[1]  # 方法名
    timestamp = sys.argv[2]  # 时间戳
    overwrite = sys.argv[3] if len(sys.argv) >= 3 else 0
    try:
        overwrite = int(overwrite)
    except ValueError:
        print(public.lang("Error: force parameter must be 0 or 1"))
        sys.exit(1)
    restore_manager = RestoreManager(overwrite)  # 实例化对象
    if hasattr(restore_manager, method_name):  # 检查方法是否存在
        method = getattr(restore_manager, method_name)  # 获取方法
        method(timestamp)  # 调用方法
    else:
        print(f"Error: {public.lang('Method')} '{method_name}' {public.lang('does not exist')}")
