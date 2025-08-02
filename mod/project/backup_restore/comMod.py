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
import re
import socket
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
import public.validate
from public import Param
from public.exceptions import HintException
from mod.project.backup_restore.data_manager import DataManager
from mod.project.backup_restore.backup_manager import BackupManager
from mod.project.backup_restore.restore_manager import RestoreManager
from mod.project.backup_restore.ssh_manager import BtInstallManager

warnings.filterwarnings("ignore", category=SyntaxWarning)


class main(DataManager):
    def __init__(self):
        super().__init__()
        self.base_path = '/www/backup/backup_restore'
        self.bakcup_task_json = self.base_path + '/backup_task.json'
        self.backup_pl_file = self.base_path + '/backup.pl'
        self.restore_pl_file = self.base_path + '/restore.pl'
        self.migrate_task_json = self.base_path + '/migration_task.json'
        self.migrate_pl_file = self.base_path + '/migrate.pl'
        self.migrate_success_pl = self.base_path + '/migrate_success.pl'

    def return_data(self, status: bool = None, msg: str = None, error_msg: str = None, data: list | dict = None):
        aa_status = 0 if status else -1
        result = None
        if not isinstance(data, type(None)):
            result = data
        elif msg:
            result = public.lang(msg)
        elif error_msg:
            result = public.lang(error_msg)
        return public.return_message(aa_status, 0, result)

    def add_backup(self, get):
        """ 备份"""
        try:
            get.validate([
                Param("backup_name").String().Require(),
                Param("storage_type").String().Require(),
                Param("timestamp").Integer().Require(),
                Param("auto_exit").Integer("in", [0, 1]).Require(),
            ], [
                public.validate.trim_filter(),
            ])
        except Exception as ex:
            public.print_log("error info: {}".format(ex))
            return public.fail_v2(str(ex))

        if os.path.exists(self.backup_pl_file):
            self.task_stop()

        if os.path.exists(self.base_path + "/success.pl"):
            try:
                if int(os.path.getctime(self.base_path + "/success.pl")) + 10 > int(time.time()):
                    return public.fail_v2(public.lang("Please do not operate frequently, please wait a moment"))
            except:
                pass

        web_check = self.web_config_check()
        if web_check['status'] is False:
            return self.return_data(error_msg=web_check['msg'])

        backup_config = []
        if os.path.exists(self.bakcup_task_json):
            backup_config = json.loads(public.ReadFile(self.bakcup_task_json))

        get.auto_exit = 0  # 强制不打断, 通过error msg交互
        backup_now = False
        if not hasattr(get, "timestamp"):
            get_time = ""
        else:
            try:
                get_time = int(get.timestamp)
            except:
                get_time = get.timestamp

        local_timestamp = int(time.time())
        if get_time == "" or get_time == "0" or get_time == 0:
            backup_timestamp = local_timestamp
            get_time = local_timestamp
            backup_now = True
        else:
            backup_timestamp = get_time

        backup_conf = {
            'backup_name': get.backup_name,
            'timestamp': get_time,
            'create_time': datetime.datetime.fromtimestamp(int(local_timestamp)).strftime('%Y-%m-%d %H:%M:%S'),
            'backup_time': datetime.datetime.fromtimestamp(int(backup_timestamp)).strftime('%Y-%m-%d %H:%M:%S'),
            'storage_type': get.storage_type,
            'auto_exit': int(get.auto_exit),
            'backup_status': 0 if not backup_now else 1,
            'restore_status': 0,
            'backup_path': self.base_path + "/" + str(get_time) + "_backup",
            'backup_file': "",
            'backup_file_sha256': "",
            'backup_file_size': "",
            'backup_count': {
                'success': None,
                'failed': None,
            },
            'total_time': None,
            'done_time': None,
        }
        backup_config.append(backup_conf)
        public.WriteFile(self.bakcup_task_json, json.dumps(backup_config))

        if backup_now:
            public.ExecShell(
                "nohup btpython /www/server/panel/mod/project/backup_restore/backup_manager.py backup_data {} > /dev/null 2>&1 &".format(
                    int(get_time)
                )
            )
        else:
            # todo at time
            # 2024-05-20 14:00
            at_time_str = time.strftime("%Y-%m-%d %H:%M", time.localtime(int(get_time)))
            exec_script = "btpython /www/server/panel/mod/project/backup_restore/backup_manager.py"
            exec_command = f"cd {public.get_panel_path()} && echo 'nohup {exec_script} backup_data {int(get_time)} > /dev/null 2>&1' | at {at_time_str}"
            public.print_log(f"{exec_command}")
            public.ExecShell(exec_command)
        public.set_module_logs('backup_restore', 'add_backup', 1)
        return self.return_data(True, public.lang("Added successfully"))

    def get_backup_list(self, get=None):
        if not os.path.exists(self.base_path):
            public.ExecShell("mkdir -p {}".format(self.base_path))
        backup_config = BackupManager().get_local_backup()
        backup_config = sorted(backup_config, key=lambda x: int(x["timestamp"]), reverse=True)
        return self.return_data(True, public.lang("Successfully retrieved"), None, backup_config)

    def del_backup(self, get):
        if not hasattr(get, "timestamp"):
            return self.return_data(False, public.lang("Parameter error"), public.lang("Parameter error"))

        backup_config = []
        if os.path.exists(self.bakcup_task_json):
            backup_config = json.loads(public.ReadFile(self.bakcup_task_json))

        for backup_conf in backup_config:
            if backup_conf['timestamp'] == int(get.timestamp):
                for i in [
                    backup_conf.get("backup_file", ""),
                    backup_conf.get("backup_path", ""),
                ]:
                    if i and os.path.exists(i):
                        public.ExecShell(f"rm -rf {i}")
                backup_config.remove(backup_conf)
                public.WriteFile(self.bakcup_task_json, json.dumps(backup_config))

                info_path = os.path.join(self.base_path, "history", "info")
                log_path = os.path.join(self.base_path, "history", "log")
                if os.path.exists(info_path):
                    for item in os.listdir(info_path):
                        if item.startswith(str(get.timestamp)):
                            public.ExecShell("rm -rf {}".format(os.path.join(info_path, item)))
                if os.path.exists(log_path):
                    for item in os.listdir(log_path):
                        if item.startswith(str(get.timestamp)):
                            public.ExecShell("rm -rf {}".format(os.path.join(log_path, item)))

                return self.return_data(True, public.lang("Deleted successfully"))

        backup_file_list = os.listdir(self.base_path)
        for backup_file in backup_file_list:
            if backup_file.endswith(".tar.gz") or backup_file.endswith("_backup") or backup_file.endswith("_migration"):
                if str(get.timestamp) in backup_file:
                    if os.path.exists(os.path.join(self.base_path, backup_file)):
                        public.ExecShell("rm -rf {}".format(os.path.join(self.base_path, backup_file)))
                    return self.return_data(True, public.lang("Deleted successfully"))

        return self.return_data(False, public.lang("Deletion failed"))

    def get_data_total(self, get=None):
        server_data = self.get_data_list()
        return self.return_data(status=True, data=server_data)

    def get_progress(self, get=None):
        try:
            get.validate([
                Param("type").String(opt="in", length_or_list=["backup", "restore"]).Require(),
            ], [
                public.validate.trim_filter(),
            ])
        except Exception as ex:
            public.print_log("error info: {}".format(ex))
            return public.fail_v2(str(ex))

        type = get.type
        progress_data = self.get_progress_with_type(type)
        if progress_data['status'] is True:
            return self.return_data(True, public.lang("Successfully retrieved"), data=progress_data.get('msg'))

        return self.return_data(False, error_msg=progress_data.get('msg', public.lang("Failed to get progress")))

    def get_details(self, get):
        """ 获取备份或还原任务的详细信息"""
        try:
            get.validate([
                Param("type").String(opt="in", length_or_list=["backup", "restore"]).Require(),
                Param("timestamp").Timestamp().Require(),
            ], [
                public.validate.trim_filter(),
            ])
        except Exception as ex:
            public.print_log("error info: {}".format(ex))
            return public.fail_v2(str(ex))

        if get.type == "backup":
            return BackupManager().get_backup_details(get.timestamp)
        elif get.type == "restore":
            return RestoreManager().get_restore_details(get.timestamp)

        raise HintException(public.lang("Unknown Type"))

    def get_exec_logs(self, get=None):
        try:
            get.validate([
                Param("timestamp").Integer().Require(),
                Param("type").String("in", ["backup", "restore"]).Require(),
            ], [
                public.validate.trim_filter(),
            ])
        except Exception as ex:
            public.print_log("error info: {}".format(ex))
            return public.fail_v2(str(ex))

        timestamp = get.timestamp
        type = get.type
        exec_logs = ""
        if type == "backup":
            exec_logs = BackupManager().get_backup_log(timestamp)
        elif type == "restore":
            exec_logs = RestoreManager().get_restore_log(timestamp)
        return self.return_data(True, public.lang("Successfully retrieved"), "", exec_logs)

    def task_stop(self, get=None):
        backup_task_pid = public.ExecShell(
            "ps -ef|grep 'backup_manager.py'|grep -v grep|awk '{print $2}'"
        )[0].replace("\n", "")
        if backup_task_pid:
            public.ExecShell("kill {}".format(backup_task_pid))

        restore_task_pid = public.ExecShell(
            "ps -ef|grep 'restore_manager.py'|grep -v grep|awk '{print $2}'"
        )[0].replace("\n", "")
        if restore_task_pid:
            public.ExecShell("kill {}".format(restore_task_pid))

        if os.path.exists(self.backup_pl_file):
            public.ExecShell("rm -f {}".format(self.backup_pl_file))

        if os.path.exists(self.restore_pl_file):
            public.ExecShell("rm -f {}".format(self.restore_pl_file))

        try:
            task_json_data = json.loads(public.ReadFile(self.bakcup_task_json))
            for item in task_json_data:
                if 'backup_status' in item and item['backup_status'] == 1:
                    item['backup_status'] = 0
                if 'restore_status' in item and item['restore_status'] == 1:
                    item['restore_status'] = 0
            public.WriteFile(self.bakcup_task_json, json.dumps(task_json_data))
        except:
            pass

        if os.path.exists("/www/server/panel/data/migration.pl"):
            public.ExecShell("rm -f /www/server/panel/data/migration.pl")
        return self.return_data(True, public.lang("Task stopped successfully"), None, None)

    def get_backup_detail(self, get=None):
        try:
            get.validate([
                Param("timestamp").Integer().Require(),
            ], [
                public.validate.trim_filter(),
            ])
        except Exception as ex:
            public.print_log("error info: {}".format(ex))
            return public.fail_v2(str(ex))

        timestamp = get.timestamp
        data = BackupManager().get_backup_file_msg(timestamp)
        return self.return_data(True, public.lang("Successfully retrieved"), "", data)

    def exec_backup(self, get=None):
        if not hasattr(get, "timestamp"):
            return self.return_data(False, public.lang("Parameter error"), public.lang("Parameter error"))
        timestamp = get.timestamp
        public.ExecShell(
            "nohup btpython /www/server/panel/mod/project/backup_restore/backup_manager.py backup_data {} > /dev/null 2>&1 &".format(
                int(timestamp)
            )
        )
        return self.return_data(True, public.lang("Executed successfully"), public.lang("Executed successfully"))

    def add_restore(self, get=None):
        """
        还原
        """
        try:
            get.validate([
                Param("timestamp").Integer().Require(),
                Param("auto_exit").Integer("in", [0, 1]).Require(),  # 打断任务
                Param("force_restore").Integer("in", [0, 1]).Require(),  # 覆盖强制还原
            ], [
                public.validate.trim_filter(),
            ])
        except Exception as ex:
            public.print_log("error info: {}".format(ex))
            return public.fail_v2(str(ex))

        if os.path.exists(self.restore_pl_file):
            self.task_stop()

        if os.path.exists(self.base_path + "/restore_success.pl"):
            try:
                if int(os.path.getctime(self.base_path + "/restore_success.pl")) + 10 > int(time.time()):
                    return public.fail_v2(public.lang("Please do not operate frequently, please wait a moment"))
            except:
                pass

        timestamp = get.timestamp

        public.ExecShell(
            "nohup btpython /www/server/panel/mod/project/backup_restore/restore_manager.py restore_data {} {} > /dev/null 2>&1 &".format(
                int(timestamp), int(get.force_restore)
            )
        )
        public.set_module_logs('backup_restore', 'add_restore', 1)
        return self.return_data(True, public.lang("Restore task added successfully"))

    def ssh_auth_check(self, get):
        """验证SSH连接信息是否正常"""
        try:
            get.validate([
                Param("server_ip").String().Require(),
                Param("ssh_port").Integer(),
                Param("ssh_user").String().Require(),
                Param("password").String(),
                Param("auth_type").String("in", ["password", "key"]).Require(),
            ], [
                public.validate.trim_filter(),
            ])
        except Exception as ex:
            public.print_log("error info: {}".format(ex))
            return public.fail_v2(str(ex))

        web_check = self.web_config_check()
        if web_check['status'] is False:
            return self.return_data(error_msg="{}".format(web_check['msg']))

        port = int(get.ssh_port) if hasattr(get, "ssh_port") and get.ssh_port else 22
        ssh_client = self.ssh_net_client_check(get.server_ip, port)
        if not ssh_client:
            return self.return_data(
                error_msg=public.lang("SSH connection test failed, please check if the IP and port are correct"))

        password = None
        key_file = None
        # 至少需要提供密码或密钥文件之一
        if hasattr(get, "password") and get.password:
            password = get.password

        if get.auth_type == "password":
            key_file = None
        elif get.auth_type == "key":
            key_file = "/www/backup/backup_restore/key_file"
            public.WriteFile(key_file, get.password)
            public.ExecShell("chmod 600 {}".format(key_file))

        # 创建SSH管理器实例并验证连接
        manager = BtInstallManager(
            host=get.server_ip,
            port=port,
            username=get.ssh_user,
            password=password,
            key_file=key_file
        )

        result = manager.verify_ssh_connection()
        if result["status"]:
            return self.return_data(True, public.lang("SSH connection verified successfully"), None, None)
        return self.return_data(error_msg=result["msg"])

    def add_migrate_task(self, get=None):
        try:
            get.validate([
                Param("server_ip").String().Require(),
                Param("ssh_port").Integer(),
                Param("ssh_user").String().Require(),
                Param("password").String(),
                Param("auth_type").String("in", ["password", "key"]).Require(),
            ], [
                public.validate.trim_filter(),
            ])
        except Exception as ex:
            public.print_log("error info: {}".format(ex))
            return public.fail_v2(str(ex))

        self.stop_migrate()
        if os.path.exists("/www/backup/backup_restore/migration.log"):
            public.ExecShell("rm -f /www/backup/backup_restore/migration.log")

        server_ip = get.server_ip
        ssh_port = get.ssh_port
        ssh_user = get.ssh_user
        auth_type = get.auth_type
        password = get.password

        if auth_type == "key":
            key_file = "/www/backup/backup_restore/key_file"
            public.WriteFile(key_file, password)
            public.ExecShell("chmod 600 {}".format(key_file))
        else:
            key_file = None

        timestamp = int(time.time())
        migrate_conf = {
            'server_ip': server_ip,
            'ssh_port': ssh_port,
            'ssh_user': ssh_user,
            'auth_type': auth_type,
            'password': password,
            'timestamp': timestamp,
            'run_type': "INIT",
            'run_status': 1,
            'confirm': 0,
            'step': 1,
            'migrate_progress': 5,
            'migrate_msg': public.lang("Migration task initializing"),
            'task_info': None,
        }
        public.WriteFile(self.migrate_task_json, json.dumps(migrate_conf))

        if auth_type == "password":
            public.ExecShell(
                "nohup btpython /www/server/panel/mod/project/backup_restore/ssh_manager.py --action migrate -H {server_ip} -P {ssh_port} -u {ssh_user} --password='{password}' --task-name '{task_name}' > /dev/null 2>&1 &".format(
                    server_ip=server_ip, ssh_port=ssh_port, ssh_user=ssh_user, password=password,
                    task_name=public.lang("My Migration Task")
                )
            )
        elif auth_type == "key":
            public.ExecShell(
                "nohup btpython /www/server/panel/mod/project/backup_restore/ssh_manager.py --action migrate -H {server_ip} -P {ssh_port} -u {ssh_user} --key-file {key_file} --task-name '{task_name}' > /dev/null 2>&1 &".format(
                    server_ip=server_ip, ssh_port=ssh_port, ssh_user=ssh_user, key_file=key_file,
                    task_name=public.lang("My Migration Task")
                )
            )
        public.set_module_logs('backup_restore', 'add_migrate_task', 1)
        return self.return_data(True, public.lang("Migration task added successfully"), None, None)

    def get_migrate_status(self, get=None):
        if os.path.exists(self.migrate_task_json):
            migrate_config = json.loads(public.ReadFile(self.migrate_task_json))
            result = {
                "server_ip": migrate_config.get('server_ip', ''),
                "ssh_port": migrate_config.get('ssh_port', 22),
                "ssh_user": migrate_config.get('ssh_user', ''),
                "auth_type": migrate_config.get('auth_type', 'password'),
                "password": migrate_config.get('password', ''),
                "migrate_progress": migrate_config.get('migrate_progress', 0),
                "timestamp": migrate_config.get("timestamp", 0),
                "total_time": migrate_config.get("total_time", 0),
                "is_running": migrate_config['run_status'] == 1 or migrate_config.get("confirm", 0) == 0,
            }
        else:
            result = {
                "is_running": False,
            }
        return self.return_data(True, public.lang("Successfully retrieved"), None, result)

    def close_migrate_popup(self, get=None):
        """用户二次确认, 关闭迁移弹窗"""
        if os.path.exists(self.migrate_task_json):
            migrate_config = json.loads(public.ReadFile(self.migrate_task_json))
            if migrate_config.get("run_status") == 2:
                migrate_config['confirm'] = 1
                public.WriteFile(self.migrate_task_json, json.dumps(migrate_config))
                return self.return_data(True, public.lang("Successfully migrated"))
        self.stop_migrate()
        return self.return_data(True, public.lang("Successfully"))

    def stop_migrate(self, get=None):
        migrate_pid = public.ExecShell(
            "ps -ef|grep 'ssh_manager.py'|grep -v grep|awk '{print $2}'"
        )[0].replace("\n", "")
        if migrate_pid:
            public.ExecShell("kill {}".format(migrate_pid))
        public.ExecShell("rm -f /www/backup/backup_restore/migrate_backup.pl")
        public.ExecShell("rm -f /www/backup/backup_restore/migration.pl")
        public.ExecShell("rm -f /www/backup/backup_restore/migrate_backup_success.pl")
        if os.path.exists(self.migrate_task_json):
            public.ExecShell("rm -f {}".format(self.migrate_task_json))
            return self.return_data(True, public.lang("Task stopped successfully"), None, None)
        else:
            return self.return_data(error_msg=public.lang("No migration task currently"))

    def get_migrate_progress(self, get=None):
        if os.path.exists(self.migrate_task_json):
            try:
                migrate_config = json.loads(public.ReadFile(self.migrate_task_json))
            except:
                return self.return_data(error_msg=public.lang("read migration task fail, please try again later!"))

            migrate_config['migrate_log'] = public.ReadFile('/www/backup/backup_restore/migration.log')
            if migrate_config['run_type'] == "PANEL_INSTALL":
                migrate_config['migrate_log'] = public.ReadFile('/www/backup/backup_restore/migration.log')
            if migrate_config['run_type'] == "LOCAL_BACKUP":
                if os.path.exists('/www/backup/backup_restore/backup.log'):
                    backup_log_data = public.ReadFile('/www/backup/backup_restore/backup.log')
                else:
                    backup_log_data = public.lang("Starting backup task...")
                migration_log_data = public.ReadFile('/www/backup/backup_restore/migration.log')
                migrate_config['migrate_log'] = migration_log_data + "\n" + backup_log_data
            if migrate_config['run_status'] == 2:
                if migrate_config['run_type'] == "COMPLETED":
                    migrate_config['migrate_progress'] = 100
                    migrate_config['migrate_err_msg'] = None
                    migrate_config['migrate_msg'] = public.lang("aapanel installation completed!")
                    try:
                        migrate_config['panel_addr'] = migrate_config['task_info']['panel_info']['panel_url']
                        migrate_config['panel_user'] = migrate_config['task_info']['panel_info']['username']
                        migrate_config['panel_password'] = migrate_config['task_info']['panel_info']['password']
                    except KeyError:
                        return self.return_data(error_msg=public.lang(
                            f"Remote panel info not found! please cancel the task and try again!"
                        ))
                    except Exception as e:
                        return self.return_data(error_msg=public.lang(f"Migration task failed! {e}"))
                else:
                    migrate_config['run_status'] = 1

            else:
                migrate_config['migrate_err_msg'] = migrate_config['migrate_msg']
                run_name = public.lang("Migration Task")
                err_info = []
                if migrate_config['run_type'] == "PANEL_INSTALL":
                    run_name = public.lang("aapanel Installation")
                elif migrate_config['run_type'] == "LOCAL_BACKUP":
                    run_name = public.lang("Local Backup")
                elif migrate_config['run_type'] == "UPLOAD_FILE":
                    run_name = public.lang("File Upload")
                elif migrate_config['run_type'] == "REMOTE":
                    run_name = public.lang("Restore Task")
                err_info_result = {
                    "name": run_name,
                    "type": public.lang("Environment"),
                    "msg": migrate_config['migrate_msg']
                }
                err_info.append(err_info_result)
                migrate_config['err_info'] = err_info

            return self.return_data(True, public.lang("Successfully retrieved"), None, migrate_config)
        else:
            return self.return_data(error_msg=public.lang("No migration task currently"))

    def get_history_migrate_list(self, get=None):
        history_migrate = []
        if os.path.exists(self.base_path):
            for item in os.listdir(self.base_path):
                item_path = os.path.join(self.base_path, item)
                if os.path.isdir(item_path) and re.match(r'^(\d+)_migration$', item):
                    timestamp = re.match(r'^(\d+)_migration$', item).group(1)
                    if os.path.exists(os.path.join(item_path, "status.json")):
                        status_data = json.loads(public.ReadFile(os.path.join(item_path, "status.json")))
                        migrate_ip = status_data['server_ip']
                    else:
                        migrate_ip = None
                    migrate_data = {
                        "timestamp": int(timestamp),
                        "migrate_time": int(timestamp),
                        "migrate_path": item_path,
                        "migrate_ip": migrate_ip
                    }
                    history_migrate.append(migrate_data)
        return history_migrate

    def get_history_migrate_log(self, get=None):
        timestamp = get.timestamp
        history_migrate_log = self.base_path + "/" + str(timestamp) + "_migration/migration.log"
        if os.path.exists(history_migrate_log):
            return self.return_data(True, public.lang("Successfully retrieved"), None,
                                    public.ReadFile(history_migrate_log))
        else:
            return self.return_data(False, public.lang("Migration log does not exist"), None, None)

    def get_history_migrate_info(self, get=None):
        try:
            get.validate([
                Param("timestamp").Timestamp().Require(),
            ], [
                public.validate.trim_filter(),
            ])
        except Exception as ex:
            public.print_log("error info: {}".format(ex))
            return public.fail_v2(str(ex))

        timestamp = get.timestamp
        history_migrate_info = self.base_path + "/" + str(timestamp) + "_migration/status.json"
        if os.path.exists(history_migrate_info):
            return self.return_data(True, public.lang("Successfully retrieved"), None,
                                    json.loads(public.ReadFile(history_migrate_info)))
        else:
            return self.return_data(error_msg=public.lang("Migration log does not exist"))

    def get_backup_log(self, get=None):
        if not hasattr(get, "timestamp"):
            return self.return_data(False, public.lang("Parameter error"), public.lang("Parameter error"))
        timestamp = get.timestamp
        return self.return_data(True, public.lang("Successfully retrieved"), "",
                                BackupManager().get_backup_log(timestamp))

    def ssh_net_client_check(self, server_ip, ssh_port):
        try:
            # 使用requests库测试SSH连接，设置3秒超时
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(3)
            result = sock.connect_ex((server_ip, int(ssh_port)))
            sock.close()

            if result == 0:
                return True
            else:
                return False
        except Exception as e:
            public.print_log(public.lang("SSH connection test failed: {}").format(e))
            return False

    def del_migrate_tips(self, get=None):
        if os.path.exists("/www/server/panel/data/migration.pl"):
            public.ExecShell("rm -f /www/server/panel/data/migration.pl")
        return public.returnMsg(True, public.lang("Migration reminder deleted successfully"))

    def del_history_migrate(self, get=None):
        try:
            get.validate([
                Param("timestamp").Timestamp().Require(),
            ], [
                public.validate.trim_filter(),
            ])
        except Exception as ex:
            public.print_log("error info: {}".format(ex))
            return public.fail_v2(str(ex))

        timestamp = get.timestamp
        if os.path.exists(self.base_path + "/" + str(timestamp) + "_migration"):
            public.ExecShell("rm -rf {}".format(self.base_path + "/" + str(timestamp) + "_migration"))
            return self.return_data(True, public.lang("Migration history deleted successfully"))
        else:
            return self.return_data(error_msg=public.lang("Migration history does not exist"))


if __name__ == '__main__':
    # 获取命令行参数
    if len(sys.argv) < 2:
        print("Usage: btpython backup_manager.py <method> <timestamp>")
        sys.exit(1)
    method_name = sys.argv[1]  # 方法名  p
    timestamp = sys.argv[2]
    com_manager = main()  # 实例化对象
    if hasattr(com_manager, method_name):  # 检查方法是否存在
        method = getattr(com_manager, method_name)  # 获取方法
        method(timestamp)  # 调用方法
    else:
        print(f"Error: {public.lang('Method')} '{method_name}' {public.lang('does not exist')}")
