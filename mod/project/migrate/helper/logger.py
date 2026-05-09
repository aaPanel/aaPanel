# coding: utf-8
# -------------------------------------------------------------------
# aaPanel
# -------------------------------------------------------------------
# Copyright (c) 2014-2099 aaPanel(www.aapanel.com) All rights reserved.
# -------------------------------------------------------------------
# Author: aapanel
# -------------------------------------------------------------------

# ------------------------------
# logger app
# ------------------------------


import sys
import os
import time

TOP = "┏"          # 用户维度开始
MIDDLE = "┃"       # 过程
END = "┗"          # 用户维度结束

class MigrateLogger:
    def __init__(self, log_file="/tmp/cp_to_aa_migrate.log", clear_log=True):
        self.log_file = log_file
        self.total_users = 0
        self.current_user_index = 0
        self.last_update_time = 0
        self.last_transferred = 0
        self.hide_progress = False  # 控制是否隐藏用户进度前缀
        self._last_msg_content = None
        if clear_log:
            with open(self.log_file, "w", encoding="utf-8") as f:
                f.write(f"\n{'-' * 30}{self._get_time()}{'-' * 30}\n")

    def _get_time(self):
        return time.strftime("%Y-%m-%d %H:%M:%S")

    def set_total_users(self, total):
        self.total_users = total

    def set_current_user(self, index):
        self.current_user_index = index

    def info(self, msg, step_progress=None, prefix: str = MIDDLE):
        step_progress = step_progress.capitalize() if step_progress else None
        # 根据 hide_progress 决定是否显示用户进度
        if self.hide_progress or self.total_users == 0:
            progress_str = ""
        else:
            progress_str = f"[User {self.current_user_index}/{self.total_users}]"

        step_str = f" [{step_progress}]" if step_progress else ""
        log_line = f"[{self._get_time()}] {progress_str} {prefix}{step_str} {msg}".strip()

        self._write(log_line)

    def error(self, msg, prefix: str = MIDDLE):
        # 根据 hide_progress 决定是否显示用户进度
        if self.hide_progress or self.total_users == 0:
            progress_str = ""
        else:
            progress_str = f"[User {self.current_user_index}/{self.total_users}]"
        log_line = f"[{self._get_time()}] {progress_str} {prefix} Error: {msg}".strip()
        self._write(log_line)

    def _write(self, msg):
        msg_content = msg.split(MIDDLE, 1)[-1].strip() if MIDDLE in msg else msg.strip()
        # 跳过写入
        if msg_content == self._last_msg_content:
            return
        self._last_msg_content = msg_content
        # 使用行缓冲模式buffering=1确保 immediate 写入
        with open(self.log_file, "a", encoding="utf-8", buffering=1) as f:
            f.write(msg + "\n")
            f.flush()  # 确保立即写入磁盘
            os.fsync(f.fileno())  # 强制同步到磁盘

    def _format_bytes(self, bytes_num):
        """格式化字节数"""
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if bytes_num < 1024.0:
                return f"{bytes_num:.1f} {unit}"
            bytes_num /= 1024.0
        return f"{bytes_num:.1f} PB"

    def replace_last_line(self, msg: str):
        """替换日志文件中的最后一行"""
        if os.path.exists(self.log_file):
            if self.hide_progress or self.total_users == 0:
                progress_str = ""
            else:
                progress_str = f"[User {self.current_user_index}/{self.total_users}]"
            msg = f"[{self._get_time()}] {progress_str} {MIDDLE} {msg}".strip()
            with open(self.log_file, "r+", encoding="utf-8") as f:
                lines = f.readlines()
                if lines:
                    lines[-1] = msg + "\n"
                    f.seek(0)
                    f.writelines(lines)
                    f.truncate()

    def replace_line_by_key(self, key: str, msg: str):
        """按key替换最后一条匹配行, 不存在则追加"""
        try:
            if self.hide_progress or self.total_users == 0:
                progress_str = ""
            else:
                progress_str = f"[User {self.current_user_index}/{self.total_users}]"
            msg = f"[{self._get_time()}] {progress_str} {MIDDLE} {msg}".strip()
            with open(self.log_file, "a+", encoding="utf-8", buffering=1) as f:
                f.seek(0)
                lines = f.readlines()
                target_idx = -1
                for i in range(len(lines) - 1, -1, -1):
                    if key in lines[i]:
                        target_idx = i
                        break
                new_line = msg if msg.endswith("\n") else msg + "\n"
                if target_idx >= 0:
                    lines[target_idx] = new_line
                else:
                    lines.append(new_line)
                f.seek(0)
                f.writelines(lines)
                f.truncate()
                f.flush()
                os.fsync(f.fileno())
        except Exception as e:
            self._write(f"[{self._get_time()}] ┃ Error: replace_line_by_key failed: {e}; fallback: {msg}")
