# coding: utf-8
# -------------------------------------------------------------------
# aaPanel
# -------------------------------------------------------------------
# Copyright (c) 2014-2099 aaPanel(www.aapanel.com) All rights reserved.
# -------------------------------------------------------------------
# Author: aapanel
# -------------------------------------------------------------------
# ------------------------------
# migrate cleanup script
# ------------------------------
import json
import os
import sys
import time

if "/www/server/panel" not in sys.path:
    sys.path.insert(0, "/www/server/panel")
if "/www/server/panel/class" not in sys.path:
    sys.path.insert(0, "/www/server/panel/class")

import public


def cleanup_migrate(task_id: str) -> dict:
    """
    清理迁移相关的所有资源
    Args:
        task_id
    """
    abs_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    work_flag = os.path.join(abs_path, "running.pl")
    migrate_path = os.path.join(abs_path, f"migrate_{task_id}.json")
    result = {
        "success": True,
        "remote_cleaned": False,
        "local_cleaned": False,
        "errors": []
    }
    try:
        with open(migrate_path, "r") as f:
            migrate_info = json.load(f)
    except Exception as e:
        result["success"] = False
        result["errors"].append(f"Failed to read migrate info: {e}")
        return result

    dir_prefix = migrate_info.get("timestamp", int(time.time()))
    remote_backup_base = migrate_info.get("remote_backup_base", "")
    if remote_backup_base:
        try:
            from mod.project.migrate.helper.ssh import CpanelSSHManager
            host = migrate_info.get("host", "")
            auth = migrate_info.get("auth", {})
            port = migrate_info.get("port", 22)
            if host and auth and isinstance(auth, dict):
                with CpanelSSHManager(host, auth, port=port) as ssh:
                    ssh.execute(f"rm -rf '{remote_backup_base}'", timeout=30)
                    result["remote_cleaned"] = True
            else:
                msg = f"Skipping remote cleanup: missing host ({bool(host)}) or auth ({bool(auth)})"
                result["errors"].append(msg)
        except Exception as e:
            msg = f"Failed to clean remote backup: {e}"
            result["errors"].append(msg)

    local_backup_base = f"/tmp/{dir_prefix}_aa_migrate"
    if os.path.exists(local_backup_base):
        try:
            public.ExecShell(f"rm -rf '{local_backup_base}'")
            result["local_cleaned"] = True
        except Exception as e:
            msg = f"Failed to clean local backup: {e}"
            result["errors"].append(msg)
    else:
        result["local_cleaned"] = True  # 不存在，视为已清理

    # 删除WORK_FLAG
    if os.path.exists(work_flag):
        try:
            os.remove(work_flag)
        except:
            pass
    # 删除进度
    progress_path = os.path.join(abs_path, f"progress_{task_id}.json")
    if os.path.exists(progress_path):
        try:
            os.remove(progress_path)
        except:
            pass
    # 删除任务信息
    if os.path.exists(migrate_path):
        try:
            os.remove(migrate_path)
        except:
            pass
    return result


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python clean.py <task_id>")
        sys.exit(1)
    task_id = sys.argv[1]
    result = cleanup_migrate(task_id)
    if result["errors"]:
        print(f"Cleanup completed with errors: {result['errors']}", file=sys.stderr)
        sys.exit(1)
    sys.exit(0)