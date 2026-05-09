# coding: utf-8
# -------------------------------------------------------------------
# aaPanel
# -------------------------------------------------------------------
# Copyright (c) 2014-2099 aaPanel(www.aapanel.com) All rights reserved.
# -------------------------------------------------------------------
# Author: aapanel
# -------------------------------------------------------------------

# MigrateProgress - 迁移进度追踪器

import json
import os
import threading
import time
from dataclasses import dataclass, asdict
from typing import Optional, Dict, Any
from functools import wraps


@dataclass
class ProgressState:
    """进度状态数据类."""
    task_id: str
    progress: float
    message: str
    started_at: int
    updated_at: int

    # 内部状态 (用于进度计算)
    _phase: str = "idle"
    _current_user: str = ""
    _phase_progress: float = 0.0
    _phase_start_time: int = 0
    _detail: list = None  # type: ignore
    _total_users: int = 0
    _user_weight: float = 0.0

    def __post_init__(self):
        if self._detail is None:
            self._detail = []


def _synchronized(func):
    """装饰器: 线程安全."""
    @wraps(func)
    def wrapper(self, *args, **kwargs):
        with self._lock:
            return func(self, *args, **kwargs)
    return wrapper


def _ensure_initialized(func):
    """装饰器: 确保已初始化."""
    @wraps(func)
    def wrapper(self, *args, **kwargs):
        if self._state is None:
            raise RuntimeError("MigrateProgress not initialized, call init() first")
        return func(self, *args, **kwargs)
    return wrapper


class MigrateProgress:
    """迁移进度追踪器. 具有线程安全和平滑进度特性."""

    PHASE_WEIGHTS = {
        "backup": 0.20,
        "download": 0.50,
        "extract": 0.10,
        "restore": 0.20,
    }
    SMOOTH_RATIO = 0.95
    SMOOTH_DURATION = 60  # seconds

    def __init__(self, task_id: str, abs_path: str) -> None:
        self.task_id = task_id
        self.progress_file = os.path.join(abs_path, f"progress_{task_id}.json")
        self._lock = threading.RLock()
        self._state: Optional[ProgressState] = None

    @classmethod
    def from_file(cls, progress_file: str) -> Optional["MigrateProgress"]:
        """从 JSON 文件加载进度状态."""
        if not os.path.exists(progress_file):
            return None

        try:
            with open(progress_file, "r", encoding="utf-8") as f:
                data = json.load(f)
        except (json.JSONDecodeError, IOError, OSError):
            return None

        try:
            obj = cls.__new__(cls)
            obj.task_id = data.get("task_id", "")
            obj.progress_file = progress_file
            obj._lock = threading.RLock()

            obj._state = ProgressState(
                task_id=data.get("task_id", ""),
                progress=data.get("progress", 0),
                message=data.get("message", ""),
                started_at=data.get("started_at", int(time.time())),
                updated_at=data.get("updated_at", int(time.time())),
                _phase=data.get("phase", data.get("_phase", "idle")),
                _current_user=data.get("current_user", data.get("_current_user", "")),
                _phase_progress=0.0,
                _phase_start_time=data.get("_phase_start_time", int(time.time())),
                _detail=data.get("_detail", []),
                _total_users=data.get("_total_users", 0),
                _user_weight=data.get("_user_weight", 0.0),
            )
            return obj
        except (KeyError, TypeError, ValueError):
            return None

    @_synchronized
    def init(self, detail: list) -> None:
        """初始化进度追踪."""
        now = int(time.time())
        self._state = ProgressState(
            task_id=self.task_id,
            progress=0,
            message="Initializing...",
            started_at=now,
            updated_at=now,
            _phase="idle",
            _current_user="",
            _phase_progress=0.0,
            _phase_start_time=now,
            _detail=detail,
            _total_users=len(detail),
            _user_weight=100.0 / len(detail) if detail else 0.0,
        )
        self._save()

    @_synchronized
    @_ensure_initialized
    def update(self, phase: str, user: str, message: str = "") -> None:
        """更新进度. 阶段变化时自动切换.

        Args:
            phase: 当前阶段 (backup/download/extract/restore)
            user: 当前用户名
            message: 可选的消息
        """
        # 阶段变化时更新开始时间
        if self._state._phase != phase:
            self._state._phase_start_time = int(time.time())

        self._state._phase = phase
        self._state._current_user = user
        self._state.message = message or f"{phase.capitalize()} in progress"

        # 自动计算阶段进度 (基于已完成用户数)
        user_idx = self._user_index(user)
        if user_idx > 0:
            # 当前用户之前有 (user_idx - 1) 个用户已完成
            self._state._phase_progress = (user_idx - 1) / self._state._total_users
        else:
            self._state._phase_progress = 0.0

        # 计算显示进度
        self._state.progress = self._calc_display_progress()
        self._save()

    @_synchronized
    @_ensure_initialized
    def done(self, message: str = "Migration completed") -> None:
        """标记迁移完成."""
        self._state.progress = 100
        self._state._phase = "done"
        self._state.message = message
        self._save()

    @_synchronized
    @_ensure_initialized
    def error(self, message: str) -> None:
        """标记迁移错误."""
        self._state._phase = "error"
        self._state.message = message
        self._save()

    def get(self) -> Dict[str, Any]:
        """获取当前进度状态 (线程安全).

        Returns:
            包含 task_id, progress, message, started_at, updated_at 的字典
        """
        with self._lock:
            if self._state is None:
                return {
                    "progress": 0,
                    "message": "Not started"
                }

            # 实时更新进度
            self._state.progress = self._calc_display_progress()
            self._state.updated_at = int(time.time())

            return {
                "task_id": self._state.task_id,
                "progress": self._state.progress,
                "message": self._state.message,
                "started_at": self._state.started_at,
                "updated_at": self._state.updated_at,
            }

    # ==================== 私有方法 ====================

    def _save(self) -> None:
        """原子性保存状态到文件."""
        if self._state is None:
            return

        data = asdict(self._state)
        temp_file = f"{self.progress_file}.tmp"

        try:
            with open(temp_file, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
                f.flush()
                os.fsync(f.fileno())

            if os.path.exists(self.progress_file):
                os.replace(temp_file, self.progress_file)
            else:
                os.rename(temp_file, self.progress_file)

        except (IOError, OSError):
            if os.path.exists(temp_file):
                try:
                    os.remove(temp_file)
                except:
                    pass
            raise

    def _calc_display_progress(self) -> float:
        """计算显示进度 (保留平滑机制)."""
        if self._state is None or self._state._phase == "done":
            return 100.0

        actual = self._calc_actual()
        smooth = self._calc_smooth()
        return round(min(max(actual, smooth), 99.9), 1)

    def _calc_actual(self) -> float:
        """计算实际进度."""
        if self._state is None:
            return 0.0

        phase = self._state._phase
        if phase not in self.PHASE_WEIGHTS:
            return 0.0

        user_idx = self._user_index(self._state._current_user)
        if user_idx == 0:
            return 0.0

        base = self._calc_base(user_idx - 1, phase)
        phase_w = self.PHASE_WEIGHTS[phase]
        ratio = self._state._phase_progress

        return base + self._state._user_weight * phase_w * ratio

    def _calc_smooth(self) -> float:
        """计算平滑进度 (基于时间).

        平滑进度在当前用户当前阶段范围内增长, 上限为阶段范围的 95%,
        确保阶段切换时进度不会倒退.
        """
        if self._state is None:
            return 0.0

        phase = self._state._phase
        if phase not in self.PHASE_WEIGHTS:
            return 0.0

        user_idx = self._user_index(self._state._current_user)
        if user_idx == 0:
            return 0.0

        # 当前用户当前阶段的起始位置
        base = self._calc_base(user_idx - 1, phase)

        # 阶段范围 = 单个用户的该阶段权重
        phase_range = self._state._user_weight * self.PHASE_WEIGHTS[phase]

        # 平滑上限 = 阶段起始 + 阶段范围 * 95%
        ceiling = base + phase_range * self.SMOOTH_RATIO

        # 基于时间的平滑比率 (0-1)
        elapsed = int(time.time()) - self._state._phase_start_time
        ratio = min(elapsed / self.SMOOTH_DURATION, 1.0)

        # 平滑进度, 不超过上限
        return min(base + phase_range * ratio, ceiling)

    def _calc_base(self, user_idx: int, phase: str) -> float:
        """计算指定用户和阶段的基础进度."""
        if self._state is None:
            return 0.0

        base = self._state._user_weight * user_idx
        for p in ["backup", "download", "extract", "restore"]:
            if p == phase:
                break
            base += self._state._user_weight * self.PHASE_WEIGHTS[p]
        return base

    def _user_index(self, user: str) -> int:
        """获取用户在详情列表中的索引 (1-based)."""
        if self._state is None:
            return 0
        for i, u in enumerate(self._state._detail, 1):
            if u.get("user") == user:
                return i
        return 0