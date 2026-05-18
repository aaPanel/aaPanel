# coding: utf-8
# -------------------------------------------------------------------
# aaPanel
# -------------------------------------------------------------------
# Copyright (c) 2014-2099 aaPanel(www.aapanel.com) All rights reserved.
# -------------------------------------------------------------------
# Author: aapanel
# -------------------------------------------------------------------
# ------------------------------
# migrate api
# ------------------------------
import glob
import json
import os
import shutil
import sys
import time
import uuid

if "/www/server/panel" not in sys.path:
    sys.path.insert(0, "/www/server/panel")
if "/www/server/panel/class" not in sys.path:
    sys.path.insert(0, "/www/server/panel/class")
if "/www/server/panel/class_v2" not in sys.path:
    sys.path.insert(0, "/www/server/panel/class_v2")

import public
from public.validate import Param
from mod.project.migrate.helper import *

MIGRATE_LOG = "/tmp/cp_to_aa_migrate.log"

ABS_PATH = os.path.dirname(os.path.abspath(__file__))


class main:
    def __init__(self):
        pass

    def connect_cp_verify(self, get):
        """测试连接"""
        try:
            get.validate([
                Param("host").String().Require(),
                Param("password").String().Require(),
                Param("port").Integer().Require(),
            ], [
                public.validate.trim_filter(),
            ])
            get.port = int(get.port)
        except Exception as ex:
            public.print_log("error info: {}".format(ex))
            return public.return_message(-1, 0, str(ex))
        args = {
            "host": get.host,
            "auth": {"password": get.password},
            "port": int(get.port),
        }
        try:
            with CpanelSSHManager(**args) as _:
                pass
            return public.success_v2("success")
        except Exception as e:
            return public.fail_v2(f"Failed to connect to server: {e}")

    def cp_users_info(self, get):
        """获取用户"""
        try:
            get.validate([
                Param("host").String().Require(),
                Param("password").String().Require(),
                Param("port").Integer().Require(),
            ], [
                public.validate.trim_filter(),
            ])
            get.port = int(get.port)
        except Exception as ex:
            public.print_log("error info: {}".format(ex))
            return public.return_message(-1, 0, str(ex))
        args = {
            "host": get.host,
            "auth": {"password": get.password},
            "port": int(get.port),
        }
        try:
            res = []
            with CpanelSSHManager(**args) as ssh:
                res = ssh.get_cp_user_info()
            return public.success_v2(res)
        except Exception as e:
            return public.fail_v2(f"Failed to get cPanel: {str(e)}")

    def cp_migrate_info(self, get):
        """迁移详情"""
        try:
            get.validate([
                Param("host").String().Require(),
                Param("password").String().Require(),
                Param("port").Integer().Require(),
                Param("users_info").String().Require(),
            ], [
                public.validate.trim_filter(),
            ])
            get.port = int(get.port)
            get.users_info = json.loads(get.users_info)
            if not isinstance(get.users_info, list):
                raise Exception("users_info must be a json string list")
            # init data
            for u in get.users_info:
                u['data'] = {}

        except Exception as ex:
            public.print_log("error info: {}".format(ex))
            return public.return_message(-1, 0, str(ex))

        # 删除上次所有临时文件
        for file in glob.glob(os.path.join(ABS_PATH, "migrate_*.json")):
            try:
                os.remove(file)
            except:
                pass
        for file in glob.glob(os.path.join(ABS_PATH, "progress_*.json")):
            try:
                os.remove(file)
            except:
                pass

        args = {
            "host": get.host,
            "auth": {"password": get.password},
            "port": get.port,
        }
        users_info = get.users_info

        try:
            usage = shutil.disk_usage("/www").free
        except Exception as e:
            try:
                stat = os.statvfs("/www")
                usage = stat.f_bavail * stat.f_frsize
            except:
                raise Exception(f"Failed to get local disk free space: {e}")

        res = {
            "local_disk_free": usage,
            "remote_disk_free": 0,
            "detail": [],
            "host": args["host"],
            "auth": args["auth"],
            "port": args["port"],
        }
        try:
            with CpanelSSHManager(**args) as ssh:
                res["remote_disk_free"] = ssh.get_remote_disk_free() or 0
                wp_data = ssh.get_cp_user_wp(users_info)
                ssl_data = ssh.get_cp_user_ssl(users_info)

            temp = []
            for u in users_info:
                item: dict = dict(u)
                item['data'][WpMigrate.task_name] = wp_data.get(u["user"], [])
                item['data'][SslMigrate.task_name] = ssl_data.get(u["user"], [])
                temp.append(item)
            # 注入唯一 _id
            temp = inject_item_ids(temp)
            task_id = str(uuid.uuid4())[:8]
            res["detail"] = temp
            res["task_id"] = task_id
            res["timestamp"] = int(time.time())
            migrate_info_path = os.path.join(ABS_PATH, f"migrate_{task_id}.json")
            public.writeFile(migrate_info_path, json.dumps(res, indent=2))
            # 只保留 user + 业务数据
            res["detail"] = [
                {"user": d.get("user", ""), "data": d.get("data", {})}
                for d in res["detail"]
            ]
            try:
                res.pop("auth", None)
                res.pop("host", None)
                res.pop("port", None)
            except:
                pass

            return public.success_v2(res)
        except Exception as e:
            import traceback
            public.print_log(traceback.format_exc())
            return public.fail_v2(f"Failed to get cPanel: {str(e)}")

    def cp_migrate_start(self, get):
        try:
            get.validate([
                Param("task_id").String().Require(),
                Param("id_list").String().Require(),
            ], [
                public.validate.trim_filter(),
            ])
            get.id_list = json.loads(get.id_list)
            if not isinstance(get.id_list, list):
                raise Exception("id_list must be a json string list")
        except Exception as ex:
            public.print_log("error info: {}".format(ex))
            return public.return_message(-1, 0, str(ex))

        # ========== 简单检查环境 ==========
        from panelModelV2.publicModel import main as public_model
        mysql_check = public_model().get_soft_status(public.to_dict_obj({"name": "mysql"}))
        if not mysql_check.get("message", {}).get("setup"):
            return public.fail_v2("MySQL is not properly set up, please complete MySQL setup and try again")

        from panel_site_v2 import panelSite
        php_check = panelSite().GetPHPVersion(public.to_dict_obj({}), is_http=False)
        if len(php_check) <= 1:
            return public.fail_v2("No PHP versions found, please set up PHP and try again")

        script = os.path.join(ABS_PATH, "service.py")
        # ========== 进程检测 ==========
        # 检测 service.py 进程是否在运行
        def is_process_running():
            cmd = f"pgrep -f '{script}'"
            result, _ = public.ExecShell(cmd, timeout=5)
            return bool(result.strip())

        process_running = is_process_running()
        flag_exists = os.path.exists(WORK_FLAG)

        # 标志存在，检查进程状态
        if flag_exists:
            if process_running:
                # 正常
                return public.fail_v2("Another migration task is currently running, please try again later")
            else:
                # 僵尸标志, 标志残留
                public.ExecShell(f"rm -f '{WORK_FLAG}'")

        # 进程在运行但标志不存在
        if process_running and not flag_exists:
            public.writeFile(WORK_FLAG, "1")
            return public.fail_v2("Migration task is already running, please try again later")

        # ========== 正常启动流程 ==========
        err_msg = public.lang("please refresh the page and try again")
        task_id = get.task_id
        migrate_info_path = os.path.join(ABS_PATH, f"migrate_{task_id}.json")
        if not os.path.exists(migrate_info_path):
            return public.fail_v2(err_msg)

        migrate_info_str = public.readFile(migrate_info_path)
        if not migrate_info_str:
            public.ExecShell(f"rm -f '{migrate_info_path}'")
            return public.fail_v2(err_msg)

        try:
            migrate_info = json.loads(migrate_info_str)
            info_timestamp = int(migrate_info.get('timestamp', 0))
            if not info_timestamp or (int(time.time()) - info_timestamp > 3600):
                raise Exception("migrate_info expired")
        except:
            public.ExecShell(f"rm -f '{migrate_info_path}'")
            return public.fail_v2(err_msg)

        if migrate_info.get("task_id") != get.task_id:
            return public.fail_v2(f"Migration task ID mismatch, {err_msg}")

        # 过滤需要迁移的数据
        id_set = set(get.id_list)
        for user_detail in migrate_info.get("detail", []):
            data = user_detail.get("data", {})
            for key, val in data.items():
                if isinstance(val, list):
                    # 选择的
                    data[key] = [
                        item for item in val if item.get("_id") in id_set
                    ]

        # 检查是否有需要迁移的数据
        if not any(
                item for user_detail in migrate_info.get("detail", [])
                for item in user_detail.get("data", {}).values()
                if isinstance(item, list) and item
        ):
            return public.fail_v2("No migration data selected")

        # ========== 计算硬盘占用 ==========
        # 迁移过程:
        # WP:
        # 1. 每个 WP 站点 -> {domain}.tar.gz
        # 2. 所有站点 tar.gz -> 单 tar.gz
        # 3. 下载大 tar.gz
        # 4. 解压单 tar.gz -> 各站点 tar.gz -> 恢复
        # SSL:...

        total_disk_usage = 0

        for user_detail in migrate_info.get("detail", []):
            for items in user_detail.get("data", {}).values():
                if not isinstance(items, list):
                    continue
                for item in items:
                    if "disk_usage" in item:
                        total_disk_usage += item.get("disk_usage", 0)

        # tar -czf 压缩率约 40%
        site_tars_total = int(total_disk_usage * 0.5)  # 所有站点 tar.gz 总和
        big_tar = int(site_tars_total * 0.5)  # 大 tar.gz

        # 远端需要空间: 所有站点 tar.gz (大 tar.gz 打包是流式的, 不需要额外副本)
        remote_required = site_tars_total

        # 本地需要空间: 大 tar.gz 下载 + 解压后所有站点 tar.gz
        local_required = big_tar + site_tars_total

        # 使用 migrate_info 中已有的空间信息
        local_disk_free = migrate_info.get("local_disk_free", 0)
        remote_disk_free = migrate_info.get("remote_disk_free", 0)

        # 检查远端空间
        if remote_disk_free < remote_required:
            from mod.project.migrate.helper.tools import format_disk_size
            return public.fail_v2(
                "not enough disk space on Remote Server. required: {}, available: {}".format(
                    format_disk_size(remote_required / 1024), format_disk_size(remote_disk_free / 1024)
                )
            )

        # 检查本地空间
        if local_disk_free < local_required:
            from mod.project.migrate.helper.tools import format_disk_size
            return public.fail_v2(
                "not enough disk space on Local Server. required: {}, available: {}".format(
                    format_disk_size(local_required / 1024), format_disk_size(local_disk_free / 1024)
                )
            )
        migrate_info['timestamp'] = int(time.time())
        # 覆盖任务信息
        public.writeFile(migrate_info_path, json.dumps(migrate_info, indent=2))
        # 创建标志，写入 task_id
        public.writeFile(WORK_FLAG, task_id)

        # 启动迁移
        logger = MigrateLogger()
        logger.info("Migrate Task has been added to queue, waiting for execution...", prefix="")
        public.ExecShell(
            f"nohup {public.get_python_bin()} -u {script} '{task_id}' > /dev/null 2>&1 &"
        )
        public.set_module_logs("migrate_cpanel", "start", 1)
        return public.success_v2(public.lang("Migrate Task has been started!"))

    def get_migrate_status(self, get):
        """获取当前迁移工作状态."""
        body = {
            "running": False,
            "logs": "",
            "progress": {},
        }
        if not os.path.exists(WORK_FLAG):
            return public.success_v2(body)

        task_id = public.readFile(WORK_FLAG).strip()
        if not task_id:
            return public.success_v2(body)
        if not hasattr(get, "task_id") or not get.task_id:
            get.task_id = task_id

        body["running"] = True
        # 日志
        logs = ""
        if os.path.exists(MIGRATE_LOG):
            LineCount = 50
            try:
                with open(MIGRATE_LOG, "rb") as f:
                    f.seek(0, 2)
                    file_size = f.tell()
                    pos = file_size
                    lines = []
                    while len(lines) < LineCount + 1 and pos > 0:
                        read_size = min(4096, pos)
                        pos -= read_size
                        f.seek(pos)
                        chunk = f.read(read_size)
                        lines = chunk.split(b'\n') + lines
                    # 最后N行
                    last_lines = [
                        line.decode("utf-8", errors="ignore").strip()
                        for line in lines[-(LineCount + 1):-1] if line.strip()
                    ]
                    logs = "\n".join(last_lines)
            except:
                pass
        body["logs"] = logs

        # 读取进度
        progress_path = os.path.join(ABS_PATH, f"progress_{get.task_id}.json")
        progress_obj = MigrateProgress.from_file(progress_path)
        if not progress_obj:
            return public.success_v2(body)

        progress_data = progress_obj.get()
        # 最后一行作为 message title
        if logs and progress_data:
            last_log = logs.split("\n")[-1].strip()
            if last_log:
                # 格式: [时间戳] [用户进度] 符号 消息
                msg = last_log
                while msg.startswith("[") and "]" in msg:
                    msg_part: list = msg.split("]", 1)
                    if len(msg_part) > 1:
                        msg = msg_part[1].lstrip()
                # 移除前缀符号
                msg = msg.replace(TOP, "").replace(MIDDLE, "").replace(END, "").strip()
                progress_data["message"] = msg
        body["progress"] = progress_data
        return public.success_v2(body)

    def cancel_migrate(self, get):
        """取消当前迁移任务"""
        if not os.path.exists(WORK_FLAG):
            return public.fail_v2("No migration task is running")

        task_id = public.readFile(WORK_FLAG).strip()
        if not task_id:
            public.ExecShell(f"rm -f '{WORK_FLAG}'")
            return public.fail_v2("Invalid task state")

        migrate_path = os.path.join(ABS_PATH, f"migrate_{task_id}.json")
        if not os.path.exists(migrate_path):
            # 任务文件不存在，清理 WORK_FLAG
            public.ExecShell(f"rm -f '{WORK_FLAG}'")
            return public.fail_v2("Task info file not found")

        # 先删除 WORK_FLAG
        # get_migrate_status 立即显示未运行
        public.ExecShell(f"rm -f '{WORK_FLAG}'")

        # kill进程
        script = os.path.join(ABS_PATH, "service.py")
        cmd = f"pkill -9 -f '{script}'"
        public.ExecShell(cmd)

        # clean
        clean_script = os.path.join(ABS_PATH, "helper", "clean.py")
        python_bin = public.get_python_bin()
        cmd = f"nohup {python_bin} -u {clean_script} {task_id} > /dev/null 2>&1 &"
        public.ExecShell(cmd)
        return public.success_v2("Migration task has been cancelled")

