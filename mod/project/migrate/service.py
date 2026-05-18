# coding: utf-8
# -------------------------------------------------------------------
# aaPanel
# -------------------------------------------------------------------
# Copyright (c) 2014-2099 aaPanel(www.aapanel.com) All rights reserved.
# -------------------------------------------------------------------
# Author: aapanel
# -------------------------------------------------------------------
# ------------------------------
# migrate api - 逐项目流式迁移架构
# ------------------------------
import json
import os
import sys
import time
from typing import Tuple, List

if "/www/server/panel" not in sys.path:
    sys.path.insert(0, "/www/server/panel")
if "/www/server/panel/class" not in sys.path:
    sys.path.insert(0, "/www/server/panel/class")

import public

from dataclasses import dataclass
from mod.project.migrate.helper import *

ABS_PATH = os.path.dirname(os.path.abspath(__file__))
WORK_FLAG = os.path.join(ABS_PATH, "running.pl")

SUPPORTED_TASKS = [
    WpMigrate,
    SslMigrate,
]


# ======================== 迁移辅助函数 ========================

def select_best_backup_dir(
        ssh_manager, dir_prefix: str, candidate_dirs: List[Tuple[str, str]] = None
) -> Tuple[str, str]:
    """
    选择剩余容量最大的目录作为备份目录

    Args:
        ssh_manager: SSH 管理器实例
        dir_prefix: 目录前缀
        candidate_dirs: 候选目录列表 [(路径, 描述)]，默认为 [("/home", "..."), ("/backup", "..."), ("/tmp", "...")]

    Returns:
        Tuple[str, str]: (选定的目录路径, 完整备份目录路径)
    """
    if not candidate_dirs:
        candidate_dirs = [
            ("/home", "home"),
            ("/backup", "backup"),
            ("/tmp", "default"),
        ]

    best_dir = None
    best_available = 0

    for temp_dir, _ in candidate_dirs:
        # 检查目录是否存在
        exit_status, out, _ = ssh_manager.execute(f"test -d {temp_dir} && echo 'exists'", timeout=5)
        if exit_status != 0 or "exists" not in out:
            continue

        # 获取可用空间
        cmd = f"df -B1 {temp_dir} 2>/dev/null | tail -1 | awk '{{print $4}}'"
        exit_status, out, err = ssh_manager.execute(cmd, timeout=10)

        if exit_status == 0 and out.strip().isdigit():
            available = int(out.strip())
            if available > best_available:
                best_available = available
                best_dir = temp_dir

    # 使用最佳目录或默认 /home
    if best_dir:
        backup_dir = f"{best_dir}/{dir_prefix}_aa_migrate"
    else:
        backup_dir = f"/home/{dir_prefix}_aa_migrate"

    return best_dir or "/home", backup_dir


# ======================== 迁移辅助函数 End ========================


@dataclass
class MigrateDetail:
    host: str
    port: str | int
    user: str
    auth: dict
    detail: list
    task_id: str

    @classmethod
    def from_dict(cls, data: dict) -> "MigrateDetail":
        """构造结构体"""
        return cls(
            host=data.get('host', ''),
            port=data.get('port', 22),
            user=data.get('user', 'root'),
            auth=data.get('auth', {}),
            detail=data.get('detail', []),
            task_id=data.get('task_id', ''),
        )

    def delete(self) -> None:
        """删除当前任务相关"""
        key = ["migrate_", "progress_"]
        if not self.task_id or not isinstance(self.task_id, str):
            return
        for k in key:
            try:
                temp = f"{k}{self.task_id}.json"
                temp_path = os.path.join(ABS_PATH, temp)
                if os.path.exists(temp_path):
                    os.remove(temp_path)
            except:
                pass


def main():
    if len(sys.argv) < 1:
        print("Usage: btpython comMod.py task_id")
        sys.exit(1)
    logger = MigrateLogger(clear_log=False)

    task_id = None
    try:
        task_id = sys.argv[1]
        migrate_path = os.path.join(ABS_PATH, f"migrate_{task_id}.json")
        migrate_str = public.readFile(migrate_path)
        migrate_info = json.loads(migrate_str)
        migrate_info["task_id"] = task_id
    except Exception as e:
        logger.error(f"Failed to load migration info: {e}")
        sys.exit(1)

    if not migrate_info:
        logger.error("Failed to load migration info")
        sys.exit(1)

    migrate = MigrateDetail.from_dict(migrate_info)
    dir_prefix = migrate_info.get("timestamp", int(time.time()))

    if not migrate.detail:
        logger.info(public.lang("No migration details found, exiting"))
        sys.exit(0)
    if not all([migrate.host, migrate.port, migrate.user, migrate.auth]):
        logger.error(public.lang("Missing required configuration fields (host, port, user, auth, detail)"))
        sys.exit(1)

    if len(migrate.detail) == 0:
        logger.info(public.lang("No users to migrate"))
        sys.exit(0)
    logger.set_total_users(len(migrate.detail))
    public.writeFile(WORK_FLAG, task_id)

    # 初始化进度追踪
    progress = MigrateProgress(task_id, ABS_PATH)
    progress.init(migrate.detail)

    # ========================== 用户维度迁移 ================================
    try:
        with CpanelSSHManager(
                migrate.host, migrate.auth, port=migrate.port, user=migrate.user
        ) as ssh_manager:
            # ========== 步骤 1: 确定备份目录 ==========
            # 远端 base 备份目录
            _, remote_backup_base = select_best_backup_dir(ssh_manager, dir_prefix)

            # 远端备份目录到任务信息文件
            migrate_info["remote_backup_base"] = remote_backup_base
            migrate_path = os.path.join(ABS_PATH, f"migrate_{task_id}.json")
            public.writeFile(migrate_path, json.dumps(migrate_info, indent=2))

            # 本地 base 备份目录
            local_backup_base = f"/tmp/{dir_prefix}_aa_migrate"

            # 清理本地可能存在的旧目录
            if os.path.exists(local_backup_base):
                public.ExecShell(f"rm -rf '{local_backup_base}'", timeout=10)
            os.makedirs(local_backup_base, exist_ok=True)

            # ========== 步骤 2: 逐用户处理 ==========
            logger.hide_progress = False  # 隐藏用户进度前缀 '[1/3]'
            all_restored_domains: set = set()
            for user_idx, detail in enumerate(migrate.detail, 1):
                logger.set_current_user(user_idx)
                username = detail.get('user', 'unknown')
                logger.info(f"User [ {username} ]", prefix=TOP)
                migrater = Migrater(
                    detail=detail,
                    ssh_manager=ssh_manager,
                    progress=progress,
                    logger=logger,
                    remote_backup_base=remote_backup_base,
                    local_backup_base=local_backup_base,
                    task_classes=SUPPORTED_TASKS,
                )
                success = migrater.execute()
                if success:
                    domains = migrater.get_restored_domains()
                    if domains:
                        all_restored_domains.update(domains)
                else:
                    logger.error(f"User [{username}] migration failed", prefix=END)

            # 记录验证
            verify_dns_a_records(all_restored_domains, logger)
            logger.info("All users migration completed!", prefix="")
            progress.done()
    except Exception as e:
        logger.error(f"Migration Error: {e}")
        sys.exit(1)
    finally:
        logger.info("Migration Finished!", prefix="")
        time.sleep(2)
        if task_id:
            cleanup_migrate(task_id)


if __name__ == '__main__':
    main()
