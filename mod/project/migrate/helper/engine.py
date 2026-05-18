# coding: utf-8
# -------------------------------------------------------------------
# aaPanel
# -------------------------------------------------------------------
# Copyright (c) 2014-2099 aaPanel(www.aapanel.com) All rights reserved.
# -------------------------------------------------------------------
# Author: aapanel
# -------------------------------------------------------------------

# ------------------------------
# engine app
# ------------------------------
import os
import sys
from typing import Optional, List, Dict, TYPE_CHECKING

if "/www/server/panel" not in sys.path:
    sys.path.insert(0, "/www/server/panel")
if "/www/server/panel/class" not in sys.path:
    sys.path.insert(0, "/www/server/panel/class")
if "/www/server/panel/class_v2" not in sys.path:
    sys.path.insert(0, "/www/server/panel/class_v2")
import public

if TYPE_CHECKING:
    from .ssh import CpanelSSHManager
    from .logger import MigrateLogger
    from . import MigrateProgress


class MigrateCore:
    """迁移器基类. 定义迁移契约和通用实现.

    子类必须定义:
        task_name: 类属性, 任务名称
        backup(): 远端备份方法
        restore(): 本地恢复方法
    """

    # 子类必须定义
    task_name: str = ""

    def __init__(
            self,
            detail: Dict,
            ssh_manager: "CpanelSSHManager",
            logger: "MigrateLogger",
            backup_dir: str,
            local_base_dir: str
    ) -> None:
        """初始化迁移器. 子类可重写此方法自定义初始化.
        Args:
            detail: 用户详情字典
            ssh_manager: SSH 管理器实例
            logger: 日志记录器
            backup_dir: 远端备份目录
            local_base_dir: 本地基础目录
        """
        self.detail = detail
        self.ssh_manager = ssh_manager
        self.logger = logger
        self.backup_dir = os.path.join(backup_dir, self.task_name)
        self.local_base_dir = local_base_dir
        self._data_list = detail.get('data', {}).get(self.task_name, [])
        self.restored_domains: set = set()

    # ==================== 必须实现 ====================

    def backup(self) -> List[str]:
        """远端备份操作.

        Returns:
            生成的备份文件路径列表 (远端绝对路径)
        """
        raise NotImplementedError(f"{self.__class__.__name__}.backup() not implemented")

    def restore(self) -> None:
        """本地恢复操作."""
        raise NotImplementedError(f"{self.__class__.__name__}.restore() not implemented")

    # ==================== 可选方法 (有默认行为) ====================
    @property
    def current_data(self) -> List[Dict]:
        """返回当前 data list 最新副本"""
        return [x for x in self._data_list]

    def validate(self) -> Optional[str]:
        """验证是否可以执行迁移. 默认检查数据列表.

        Returns:
            None 表示验证通过, 否则返回跳过原因
        """
        if not self.current_data:
            return f"No {self.task_name} data found"
        return None

    def update_data_item(self, item_id: str, **kwargs) -> bool:
        """更新内存中的数据项
        item_id: 数据项的 _id
        **kwargs: 要更新的字段
        """
        if not item_id:
            return False
        for item in self._data_list:
            if item.get('_id') == item_id:
                item.update(kwargs)
                return True
        return False

    def cleanup_remote(self) -> None:
        """清理远端临时文件."""
        try:
            self.ssh_manager.execute(f"rm -f '{self.backup_dir}'", timeout=10)
        except:
            pass

    def rollback(self) -> None:
        """回滚操作."""
        pass


from mod.project.migrate.helper.logger import TOP, END


class Migrater:
    """单用户迁移管理器"""

    def __init__(
            self,
            detail: dict,
            ssh_manager: "CpanelSSHManager",
            logger: "MigrateLogger",
            progress: "MigrateProgress",
            remote_backup_base: str,
            local_backup_base: str,
            task_classes: list,
    ):
        """初始化单用户迁移器.

        Args:
            detail: 用户详情字典
            ssh_manager: SSH 管理器实例
            logger: 日志记录器
            remote_backup_base: 远端备份基础目录
            local_backup_base: 本地备份基础目录
            task_classes: 任务类列表 ([WpMigrate, SslMigrate])
            progress: 进度管理器
        """
        self.detail = detail
        self.ssh_manager = ssh_manager
        self.logger = logger
        self.remote_backup_base = remote_backup_base
        self.local_backup_base = local_backup_base
        self.task_classes = task_classes
        self.progress = progress

        # 用户专属目录
        self.username = detail.get('user', 'unknown')
        self.remote_user_dir = f"{remote_backup_base}/{self.username}"
        self.local_user_dir = f"{local_backup_base}/{self.username}"
        self.local_user_tar = f"{local_backup_base}/{self.username}_backup.tar"

        self.task_plan: list = []
        self.need_download: bool = False

    def execute(self) -> bool:
        """单用户的完整迁移流程.
        Returns:
            bool: 迁移是否成功
        """
        try:
            self.progress.update("backup", self.username)
            if not self._backup():
                return False
            self.progress.update("download", self.username)
            if not self._download():
                return False
            self.progress.update("extract", self.username)
            if not self._extract():
                return False
            self.progress.update("restore", self.username)
            if not self._restore():
                return False
            self.logger.info("Completed", prefix=END)
            return True
        except Exception as e:
            self.logger.error(f"Migration failed: {e}", prefix=END)
            return False
        finally:
            self._cleanup_remote()

    def _backup(self) -> bool:
        """远端备份阶段."""
        self.logger.info("[Backup]")

        for task_class in self.task_classes:
            try:
                task_obj = task_class(
                    self.detail,
                    self.ssh_manager,
                    self.logger,
                    self.remote_user_dir,
                    self.local_backup_base
                )

                # 验证
                valid_msg = task_obj.validate()
                if valid_msg:
                    self.logger.info(f"[{task_obj.task_name}] {valid_msg}")
                    continue

                # 备份
                res = task_obj.backup()
                if res:
                    self.need_download = True

                self.task_plan.append(task_obj)
            except Exception as e:
                self.logger.error(f"[{task_class.__name__}] Backup failed: {e}")
                continue

        if not self.task_plan:
            self.logger.info("No tasks to backup")
            return True

        return True

    def _download(self) -> bool:
        """打包并下载阶段."""
        if not self.need_download:
            return True
        self.logger.info("[Download]")

        success, msg = self.ssh_manager.smart_download(
            self.remote_user_dir,
            self.local_user_tar,
            self.logger
        )

        if not success:
            self.logger.error(f"Download failed: {msg}")
            return False

        return True

    def _extract(self) -> bool:
        """本地解压阶段."""
        if not self.need_download:
            return True
        self.logger.info("[Extract]")

        # 创建本地用户目录
        os.makedirs(self.local_user_dir, exist_ok=True)

        # 解压
        _, err = public.ExecShell(
            f"tar --strip-components=1 -xf '{self.local_user_tar}' -C '{self.local_user_dir}'"
        )
        if err:
            self.logger.error(f"Extract failed: {err}")
            return False
        # 删除本地 tar 文件
        public.ExecShell(f"rm -f {self.local_user_tar}")
        return True

    def _restore(self) -> bool:
        """本地恢复阶段."""
        self.logger.info("[Restore]")
        for task_obj in self.task_plan:
            try:
                task_obj.restore()
            except Exception as e:
                self.logger.error(f"[{task_obj.task_name}] Restore failed: {e}")
        return True

    def _cleanup_remote(self):
        """清理远端临时文件."""
        try:
            self.ssh_manager.execute(f"rm -rf '{self.remote_user_dir}'")
        except:
            pass

    def get_restored_domains(self) -> set:
        """收集成功恢复的域名."""
        return {
            d for t in self.task_plan
            if hasattr(t, 'restored_domains')
            for d in t.restored_domains
        }
