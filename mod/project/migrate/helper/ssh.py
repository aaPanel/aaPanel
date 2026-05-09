# coding: utf-8
# -------------------------------------------------------------------
# aaPanel
# -------------------------------------------------------------------
# Copyright (c) 2014-2099 aaPanel(www.aapanel.com) All rights reserved.
# -------------------------------------------------------------------
# Author: aapanel
# -------------------------------------------------------------------

# SSH Manager - SSH 连接管理和智能下载

import asyncio
import base64
import hashlib
import json
import os
import re
import signal
import time
import uuid
from dataclasses import dataclass, asdict
from typing import Tuple, List, Optional, Dict
from functools import wraps

import public

try:
    import asyncssh
except ImportError:
    os.system("btpip install asyncssh")
    try:
        import asyncssh  # noqa
    except Exception:
        raise Exception(
            "asyncssh packet not installed, please try again, or run cmd [btpip install asyncssh]"
        )

from datetime import datetime
from .parser import parse_combined_ssl
from .tools import humanize_to_bytes
from .logger import MigrateLogger

# ==================== 常量定义 ====================

DATE_FORMAT = "%Y-%m-%d %H:%M:%S"
LOCK_FILE = "/tmp/aa_ssh_migrate.pid"

# SSH 连接常量
DEFAULT_PORT = 22
DEFAULT_USER = "root"
DEFAULT_TIMEOUT = 10

# 下载常量
BASE_CHUNK_READ = 2 * 1024 * 1024  # 2MB 读取块
PROGRESS_INTERVAL = 512 * 1024  # 512KB 进度更新间隔

# 重试常量
MAX_RETRIES = 3

# 并发下载常量
SMALL_FILE_THRESHOLD = 50 * 1024 * 1024  # 50MB
MEDIUM_FILE_THRESHOLD = 500 * 1024 * 1024  # 500MB
LARGE_FILE_THRESHOLD = 5 * 1024 * 1024 * 1024  # 5GB
DEFAULT_CONCURRENCY_SMALL = 3
DEFAULT_CONCURRENCY_MEDIUM = 6
DEFAULT_CONCURRENCY_LARGE = 12
DEFAULT_CONCURRENCY_XLARGE = 16

MIN_CHUNK_SIZE = 10 * 1024 * 1024  # 10MB 最小切块
MAX_CHUNK_SIZE = 200 * 1024 * 1024  # 200MB 最大切块

# ==================== 装饰器 ====================
def retry_act(max_retries: int = MAX_RETRIES, delay: int = 3):
    """重试装饰器. 失败前尝试恢复连接."""

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            last_result = None
            for attempt in range(max_retries):
                try:
                    result = func(*args, **kwargs)
                    last_result = result
                    is_success = result[0] if isinstance(result, tuple) else result
                    if is_success:
                        return result
                    MigrateLogger(clear_log=False).error(f"retry: {result[1]}")
                except Exception as e:
                    if attempt == max_retries - 1:
                        raise e
                    # 重试前确保连接
                    try:
                        ssh_mgr = args[0]
                        if hasattr(ssh_mgr, 'connect'):
                            ssh_mgr.connect()
                    except Exception:
                        pass
                if attempt < max_retries - 1:
                    time.sleep(delay)
            return last_result

        return wrapper

    return decorator


# ==================== 工具函数 ====================

def _mask_email(email: str) -> str:
    """邮箱隐私处理."""
    if not email or "@" not in email:
        return email
    name, domain = email.rsplit("@", 1)
    if len(name) <= 2:
        masked = "***"
    else:
        masked = f"{name[0]}***{name[-1]}"
    return f"{masked}@{domain}"


def format_bytes(bytes_num: float) -> str:
    """格式化字节数."""
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if bytes_num < 1024.0:
            return f"{bytes_num:.1f} {unit}"
        bytes_num /= 1024.0
    return f"{bytes_num:.1f} PB"


# ==================== 数据类 ====================
@dataclass
class DownloadChunk:
    """单个下载块的信息"""
    index: int  # 块索引
    start_offset: int  # 起始偏移量
    end_offset: int  # 结束偏移量（不包含）
    size: int  # 块大小
    downloaded: int = 0  # 已下载大小
    status: str = "pending"  # pending, downloading, completed, failed
    retry_count: int = 0  # 重试次数
    temp_file: str = ""  # 临时文件路径


@dataclass
class DownloadState:
    """下载状态（用于断点续传）"""
    file_size: int
    total_downloaded: int
    chunks: List[DownloadChunk]
    sha256: str = ""


class DownloadProgressTracker:
    """下载进度跟踪器"""

    def __init__(self, chunks: List[DownloadChunk], file_size: int, logger=None):
        self.chunks = chunks
        self.file_size = file_size
        self.logger = logger
        self.last_progress_time = 0
        self.last_percent = -1
        self.start_time = time.time()

    def get_total_downloaded(self) -> int:
        """获取总下载量"""
        return sum(chunk.downloaded for chunk in self.chunks)

    def update_progress(self):
        """更新并显示进度"""
        if not self.logger:
            return

        total_downloaded = self.get_total_downloaded()
        current_time = time.time()
        percent = int(total_downloaded * 100 / self.file_size)

        # 每 5% 或每 1 秒写一次日志
        if (percent - self.last_percent >= 5 and percent % 5 == 0) or \
                (current_time - self.last_progress_time) >= 1 or \
                total_downloaded == self.file_size:

            transferred_str = format_bytes(total_downloaded)
            total_str = format_bytes(self.file_size)

            # 计算下载速度
            elapsed = current_time - self.start_time
            if elapsed > 0:
                speed = total_downloaded / elapsed
                speed_str = format_bytes(speed) + "/s"
            else:
                speed_str = "N/A"

            self.logger.info(f"Downloading: {percent}% ({transferred_str}/{total_str}) [{speed_str}]")
            self.last_progress_time = current_time
            self.last_percent = percent


# ============= 并行下载辅助 End ================


class SSHManager:
    """SSH 管理器. 提供异步 SSH 连接和命令执行功能."""

    def __init__(self, host: str, auth: Dict[str, str], port: int = DEFAULT_PORT,
                 user: str = DEFAULT_USER, timeout: int = DEFAULT_TIMEOUT,
                 lock_file: str = None) -> None:
        """初始化 SSH 管理器.

        Args:
            host: 服务器地址
            auth: 认证信息 (password 或 key_file)
            port: SSH 端口
            user: SSH 用户名
            timeout: 连接超时时间
            lock_file: 锁文件路径
        """
        self.host = host
        self.port = port
        self.user = user
        self.auth = auth
        self.timeout = timeout
        self._loop = None
        self._conn = None
        self._lock_file = lock_file if lock_file else LOCK_FILE

    def __enter__(self) -> "SSHManager":
        self.__only_one()
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.__release()
        self.close()

    def __only_one(self) -> None:
        """确保只有一个实例运行."""
        if os.path.exists(self._lock_file):
            try:
                with open(self._lock_file, 'r') as f:
                    old_pid = int(f.read().strip())
                if old_pid != os.getpid():
                    os.kill(old_pid, 0)
                    os.kill(old_pid, signal.SIGKILL)
                    time.sleep(0.5)
            except (ValueError, ProcessLookupError, OSError):
                pass
        try:
            with open(self._lock_file, 'w') as f:
                f.write(str(os.getpid()))
        except Exception:
            pass

    def __release(self) -> None:
        """释放锁文件."""
        if os.path.exists(self._lock_file):
            try:
                with open(self._lock_file, 'r') as f:
                    current_content = f.read().strip()
                if current_content == str(os.getpid()):
                    os.remove(self._lock_file)
            except:
                pass

    def _run(self, coro):
        """异步协程"""
        if self._loop is None or self._loop.is_closed():
            self._loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self._loop)
        return self._loop.run_until_complete(coro)

    # ==================== 下载辅助方法 ====================

    def _get_concurrency(self, file_size: int) -> int:
        """根据文件大小确定并发数.

        Args:
            file_size: 文件大小（字节）

        Returns:
            并发连接数
        """
        if file_size < SMALL_FILE_THRESHOLD:
            return DEFAULT_CONCURRENCY_SMALL
        elif file_size < MEDIUM_FILE_THRESHOLD:
            return DEFAULT_CONCURRENCY_MEDIUM
        elif file_size < LARGE_FILE_THRESHOLD:
            return DEFAULT_CONCURRENCY_LARGE
        else:
            return DEFAULT_CONCURRENCY_XLARGE

    def _calculate_download_timeout(self, file_size: int) -> int:
        """根据基准计算最大超时时间"""
        base_speed = 100 * 1024 # 100KB/s
        estimated_seconds = file_size / base_speed
        # 额外30%，最少5min
        return max(300, int(estimated_seconds * 1.3))

    def _calculate_chunk_size(self, file_size: int, concurrency: int) -> int:
        """计算切块大小.

        Args:
            file_size: 文件大小（字节）
            concurrency: 并发连接数

        Returns:
            切块大小（字节）
        """
        raw_chunk = file_size // concurrency
        chunk = max(MIN_CHUNK_SIZE, min(raw_chunk, MAX_CHUNK_SIZE))

        # 对齐到 1MB
        return (chunk // (1024 * 1024)) * (1024 * 1024)

    def _save_download_state(self, state: DownloadState, state_file: str) -> bool:
        """
        保存下载状态到文件

        Args:
            state: 下载状态对象
            state_file: 状态文件路径

        Returns:
            bool: 是否保存成功
        """
        try:
            state_dict = {
                "file_size": state.file_size,
                "total_downloaded": state.total_downloaded,
                "chunks": [asdict(chunk) for chunk in state.chunks],
                "sha256": state.sha256
            }
            with open(state_file, 'w') as f:
                json.dump(state_dict, f)
            return True
        except Exception:
            return False

    def _load_download_state(self, state_file: str) -> Optional[DownloadState]:
        """
        从文件加载下载状态

        Args:
            state_file: 状态文件路径

        Returns:
            DownloadState | None: 下载状态对象，如果文件不存在或加载失败返回 None
        """
        if not os.path.exists(state_file):
            return None

        try:
            with open(state_file, 'r') as f:
                data = json.load(f)

            chunks = []
            for chunk_data in data.get("chunks", []):
                chunk = DownloadChunk(**chunk_data)
                chunks.append(chunk)

            return DownloadState(
                file_size=data["file_size"],
                total_downloaded=data["total_downloaded"],
                chunks=chunks,
                sha256=data.get("sha256", "")
            )
        except Exception:
            return None

    async def _download_chunk(
            self,
            chunk: DownloadChunk,
            remote_tar: str,
            local_tar: str,
            sftp,
            semaphore: asyncio.Semaphore,
            progress_tracker=None
    ) -> Optional[DownloadChunk]:
        """
        下载单个块

        Args:
            chunk: 下载块信息
            remote_tar: 远程文件路径
            local_tar: 本地文件路径（用于构造临时文件名）
            sftp: SFTP 客户端
            semaphore: 并发控制信号量
            progress_tracker: 进度跟踪器

        Returns:
            DownloadChunk: 更新后的块信息
        """
        async with semaphore:
            max_retries = 3

            for attempt in range(max_retries):
                try:
                    # 临时文件
                    temp_file = f"{local_tar}.chunk_{chunk.index}"
                    chunk.temp_file = temp_file

                    # 检查断点续传
                    downloaded = 0
                    if os.path.exists(temp_file):
                        downloaded = os.path.getsize(temp_file)

                    # 打开远程文件，定位到起始位置
                    async with await sftp.open(remote_tar, 'rb') as remote_file:
                        await remote_file.seek(chunk.start_offset + downloaded)

                        # 写入(断点续传追加)
                        with open(temp_file, 'ab' if downloaded > 0 else 'wb') as local_f:
                            remaining = chunk.size - downloaded
                            last_update_size = 0
                            last_update_time = time.time()

                            while remaining > 0:
                                read_size = min(BASE_CHUNK_READ, remaining)
                                data = await remote_file.read(read_size)
                                if not data:
                                    break

                                local_f.write(data)
                                downloaded += len(data)
                                remaining -= len(data)

                                # 更新块进度
                                chunk.downloaded = downloaded

                                # 定期更新总体进度
                                current_time = time.time()
                                if progress_tracker and (
                                        downloaded - last_update_size >= PROGRESS_INTERVAL or
                                        current_time - last_update_time >= 1
                                ):
                                    progress_tracker.update_progress()
                                    last_update_size = downloaded
                                    last_update_time = current_time

                    # 完成后更新一次进度
                    if progress_tracker:
                        progress_tracker.last_progress_time = 0
                        progress_tracker.update_progress()

                    chunk.status = "completed"
                    return chunk

                except Exception:
                    chunk.retry_count += 1
                    if attempt < max_retries - 1:
                        # 重试前指数延迟
                        await asyncio.sleep(min(2 ** attempt, 4))
                        continue
                    else:
                        chunk.status = "failed"
                        raise

    async def _merge_chunks(self, chunks: List[DownloadChunk], local_tar: str, file_size: int) -> Tuple[bool, str]:
        """
        按顺序合并所有块到最终文件，并计算 SHA256

        Args:
            chunks: 所有块信息
            local_tar: 最终文件路径
            file_size: 文件总大小

        Returns:
            Tuple[bool, str]: (是否成功, SHA256哈希值或错误信息)
        """
        try:
            # 验证所有块
            for chunk in chunks:
                if chunk.status != "completed":
                    raise Exception(f"Chunk {chunk.index} not completed: {chunk.status}")

            # 按顺序合并并计算 SHA256
            sha256_hash = hashlib.sha256()
            with open(local_tar, 'wb') as final_file:
                for chunk in chunks:
                    temp_file = chunk.temp_file
                    if not os.path.exists(temp_file):
                        raise Exception(f"Temp file for chunk {chunk.index} not found")

                    with open(temp_file, 'rb') as temp_f:
                        while True:
                            data = temp_f.read(1024 * 1024)  # 1MB 缓冲
                            if not data:
                                break
                            final_file.write(data)
                            sha256_hash.update(data)

            # 验证文件大小
            actual_size = os.path.getsize(local_tar)
            if actual_size != file_size:
                raise Exception(f"Size mismatch: expected {file_size}, got {actual_size}")

            # 清理临时文件
            for chunk in chunks:
                if os.path.exists(chunk.temp_file):
                    os.remove(chunk.temp_file)

            # 清理状态文件
            state_file = f"{local_tar}.download_state"
            if os.path.exists(state_file):
                os.remove(state_file)

            return True, sha256_hash.hexdigest()

        except Exception as e:
            raise Exception(f"Merge failed: {e}")

    async def _stream_download(self, remote_tar: str, local_tar: str, file_size: int, logger) -> Tuple[bool, str]:
        """单连接下载的异步实现"""
        sha256_hash = hashlib.sha256()

        # 断点续传检查
        offset = 0
        resume_mode = False
        if os.path.exists(local_tar):
            offset = os.path.getsize(local_tar)
            if offset > 0:
                resume_mode = True
                logger.info(f"Resuming download from {format_bytes(offset)}")
                with open(local_tar, 'rb') as f:
                    while True:
                        chunk = f.read(65536)
                        if not chunk:
                            break
                        sha256_hash.update(chunk)

        last_progress_time = 0
        last_percent = -1
        start_time = time.time()  # 记录开始时间

        # 计算超时时间
        timeout = self._calculate_download_timeout(file_size)

        try:
            async with asyncio.timeout(timeout):
                async with self._conn.start_sftp_client() as sftp:
                    open_mode = 'ab' if resume_mode else 'wb'

                    if not resume_mode:
                        logger.info(f"Download started: {format_bytes(file_size)}")

                    async with await sftp.open(remote_tar, 'rb') as remote_file:
                        if resume_mode:
                            await remote_file.seek(offset)

                        with open(local_tar, open_mode) as f:
                            while offset < file_size:
                                chunk = await remote_file.read(BASE_CHUNK_READ)
                                if not chunk:
                                    break

                                f.write(chunk)
                                sha256_hash.update(chunk)
                                offset += len(chunk)

                                current_time = time.time()
                                percent = int(offset * 100 / file_size)
                                if (percent - last_percent >= 5 and percent % 5 == 0) or \
                                        (current_time - last_progress_time) >= 1 or \
                                        offset == file_size:
                                    transferred_str = format_bytes(offset)
                                    total_str = format_bytes(file_size)

                                    # 计算下载速度
                                    elapsed = current_time - start_time
                                    if elapsed > 0:
                                        speed = offset / elapsed
                                        speed_str = format_bytes(speed) + "/s"
                                    else:
                                        speed_str = "N/A"

                                    logger.info(f"Downloading: {percent}% ({transferred_str}/{total_str}) [{speed_str}]")
                                    last_progress_time = current_time
                                    last_percent = percent

        except asyncio.TimeoutError:
            try:
                await self._conn.run(f"rm -f {remote_tar}")
            except Exception:
                pass
            return False, f"Download timeout after {timeout}s"
        except Exception as e:
            try:
                await self._conn.run(f"rm -f {remote_tar}")
            except Exception:
                pass
            return False, f"SFTP download failed: {str(e)}"

        try:
            await self._conn.run(f"rm -f {remote_tar}")
        except Exception:
            pass

        return True, sha256_hash.hexdigest()

    async def _parallel_download(self, remote_tar: str, local_tar: str, file_size: int, logger, concurrency: int = None) -> Tuple[bool, str]:
        """并行下载的异步实现"""
        # 计算超时时间
        timeout = self._calculate_download_timeout(file_size)

        # 步骤1: 加载断点续传状态
        state_file = f"{local_tar}.download_state"
        state = self._load_download_state(state_file)

        if state and state.file_size == file_size:
            chunks = state.chunks
            actual_concurrency = len(chunks)
            logger.info(f"Resuming download with {actual_concurrency} chunks")
        else:
            # 使用指定的并发数或自动计算
            if concurrency is None:
                actual_concurrency = self._get_concurrency(file_size)
            else:
                actual_concurrency = concurrency
            chunk_size = self._calculate_chunk_size(file_size, actual_concurrency)

            chunks = []
            offset = 0
            index = 0
            while offset < file_size:
                end = min(offset + chunk_size, file_size)
                chunks.append(DownloadChunk(
                    index=index,
                    start_offset=offset,
                    end_offset=end,
                    size=end - offset
                ))
                offset = end
                index += 1

            initial_state = DownloadState(
                file_size=file_size,
                total_downloaded=0,
                chunks=chunks,
                sha256=""
            )
            self._save_download_state(initial_state, state_file)

        # 进度跟踪器
        progress_tracker = DownloadProgressTracker(chunks, file_size, logger)
        logger.info(
            f"Download started: {format_bytes(file_size)} with {actual_concurrency} connections"
        )

        try:
            async with asyncio.timeout(timeout):
                # 步骤2: 并发下载
                async with self._conn.start_sftp_client() as sftp:
                    semaphore = asyncio.Semaphore(actual_concurrency)

                    async def download_with_context(chunk):
                        return await self._download_chunk(
                            chunk, remote_tar, local_tar,
                            sftp, semaphore, progress_tracker
                        )

                    tasks = [download_with_context(chunk) for chunk in chunks]
                    results = await asyncio.gather(*tasks, return_exceptions=True)

                    for i, result in enumerate(results):
                        if isinstance(result, Exception):
                            chunks[i].status = "failed"
                            raise result
                        chunks[i] = result

        except asyncio.TimeoutError:
            return False, f"Download timeout after {timeout}s"
        except Exception as e:
            return False, f"Parallel download failed: {str(e)}"

        # 进度更新
        progress_tracker.update_progress()

        # 步骤3: 合并块并计算 SHA256
        success, sha256_value = await self._merge_chunks(chunks, local_tar, file_size)
        if not success:
            return False, sha256_value  # 这里是错误信息

        # 步骤4: 清理远程文件
        try:
            await self._conn.run(f"rm -f {remote_tar}")
        except Exception:
            pass

        return True, sha256_value

    async def _calculate_remote_sha256(self, remote_path: str) -> Optional[str]:
        """
        计算远端文件的 SHA256 哈希值

        Args:
            remote_path: 远端文件路径

        Returns:
            Optional[str]: SHA256 哈希值，失败返回 None
        """
        try:
            # 计算哈希
            result = await self._conn.run(f"sha256sum '{remote_path}'", check=False)
            if result.exit_status == 0:
                # sha256sum 输出: <hash>  <filename>
                sha256 = result.stdout.strip().split()[0]
                return sha256
            return None
        except Exception:
            return None

    # ======================= public ============================
    def connect(self):
        if self._conn:
            return

        async def _async_connect():
            connect_kwargs = {
                "host": self.host,
                "port": self.port,
                "username": self.user,
                "login_timeout": self.timeout,
                "known_hosts": None,
                "keepalive_interval": 30,  # 30秒一次心跳
                "keepalive_count_max": 3,  # 3次心跳无响应断开
                # "encryption_algs": ['aes128-gcm@openssh.com', 'chacha20-poly1305@openssh.com'],  # 快速加密算法
            }
            if "key_file" in self.auth and os.path.exists(self.auth["key_file"]):
                connect_kwargs["client_keys"] = [self.auth["key_file"]]  # noqa
            else:
                connect_kwargs["password"] = self.auth.get("password")

            return await asyncssh.connect(**connect_kwargs)

        self._conn = self._run(_async_connect())

    def execute(self, command: str, timeout: int = 15) -> tuple[int, str, str]:
        """单条命令"""

        async def _async_execute():
            result = await asyncio.wait_for(
                self._conn.run(command, check=False),
                timeout=timeout
            )
            return result.exit_status, result.stdout.strip(), result.stderr.strip()

        try:
            return self._run(_async_execute())
        except asyncio.TimeoutError:
            return -1, "", f"Command timeout after {timeout}s"
        except Exception as e:
            return -1, "", f"Command failed: {type(e).__name__}: {str(e)}"

    def execute_many(self, commands: list[str], timeout: int = 60) -> list[dict]:
        """批量执行cmds, 远端并发"""
        if not commands: return []

        async def _internal_batch():
            boundary = f"BND_{uuid.uuid4().hex}"
            tmp_dir = f"/tmp/ssh_batch_{uuid.uuid4().hex}"
            # Shell并发 (远端提速)
            run_parts = []
            collect_parts = []
            for i, cmd in enumerate(commands):
                octal_cmd = "".join(f"\\{b:03o}" for b in cmd.encode('utf-8'))
                run_parts.append(
                    f"( ( eval \"$(printf '%b' '{octal_cmd}')\" ) > {tmp_dir}/o_{i} 2> {tmp_dir}/e_{i}; echo $? > {tmp_dir}/r_{i} ) & "
                )
                collect_parts.append(
                    f"printf '\\n{boundary}_S_{i}\\n'; cat {tmp_dir}/o_{i} 2>/dev/null; "
                    f"RET=$(cat {tmp_dir}/r_{i} 2>/dev/null || echo -1); "
                    f"printf '\\n{boundary}_E_{i}_%d\\n' \"$RET\"; "
                    f"printf '\\n{boundary}_S_{i}\\n' >&2; cat {tmp_dir}/e_{i} 2>/dev/null >&2; "
                    f"printf '\\n{boundary}_E_{i}\\n' >&2;"
                )

            full_cmd = f"mkdir -p {tmp_dir}; {''.join(run_parts)} wait; {''.join(collect_parts)} rm -rf {tmp_dir};"
            result = await asyncio.wait_for(self._conn.run(full_cmd), timeout=timeout)
            out, err = result.stdout, result.stderr
            # 解析
            results = []
            for i, cmd_str in enumerate(commands):
                res = {
                    "index": i, "cmd": cmd_str, "code": -1, "stdout": "", "stderr": ""
                }
                out_match = re.search(rf"{boundary}_S_{i}\s*(.*?)\s*{boundary}_E_{i}_(-?\d+)", out, re.DOTALL)
                err_match = re.search(rf"{boundary}_S_{i}\s*(.*?)\s*{boundary}_E_{i}", err, re.DOTALL)
                if out_match:
                    res["stdout"], res["code"] = out_match.group(1).strip(), int(out_match.group(2))
                if err_match:
                    res["stderr"] = err_match.group(1).strip()
                results.append(res)
            return results

        return self._run(_internal_batch())

    def asnyc_execute(self, commands: list[str], timeout: int = 60, max_concurrent: int = 5) -> list[dict]:
        """批量执行cmds, 异步"""
        if not commands:
            return []

        async def _run_command(index: int, cmd: str, semaphore: asyncio.Semaphore):
            async with semaphore:
                try:
                    result = await asyncio.wait_for(
                        self._conn.run(cmd, check=False),
                        timeout=timeout
                    )
                    return {
                        "index": index,
                        "cmd": cmd,
                        "code": result.exit_status,
                        "stdout": result.stdout.strip(),
                        "stderr": result.stderr.strip()
                    }
                except Exception as e:
                    return {
                        "index": index,
                        "cmd": cmd,
                        "code": -1,
                        "stdout": "",
                        "stderr": f"Error: {str(e)}"
                    }

        async def _internal_batch():
            semaphore = asyncio.Semaphore(max_concurrent)
            tasks = [
                _run_command(i, cmd, semaphore)
                for i, cmd in enumerate(commands)
            ]
            return await asyncio.gather(*tasks)

        return self._run(_internal_batch())

    def smart_download(self, remote_dir: str, local_tar: str, logger, max_retries=5) -> Tuple[bool, str]:
        """
        智能下载策略，根据文件大小自动选择最优下载方式
        将打包 remote_dir, 到本地 local_tar
        下载后会验证远端和本地文件的 SHA256 哈希值

        Args:
            remote_dir: 远程备份目录
            local_tar: 本地 tar 文件路径
            logger: 日志记录器
            max_retries: 整体重试次数

        Returns:
            Tuple[bool, str]: (成功状态, SHA256哈希值或错误信息)
        """
        remote_tar = f"{remote_dir}.tar"

        async def _async_smart_download():
            # 远程打包
            tar_cmd = f"cd {os.path.dirname(remote_dir)} && tar -cf {remote_tar} {os.path.basename(remote_dir)}"
            try:
                result = await asyncio.wait_for(self._conn.run(tar_cmd, check=False), timeout=300)
                if result.exit_status != 0:
                    return False, f"Remote tar failed: {result.stderr.strip()}"
            except asyncio.TimeoutError:
                return False, "Remote tar timeout"
            except Exception as e:
                return False, f"Remote tar failed: {str(e)}"

            # 获取文件大小
            try:
                file_size = int((await self._conn.run(f"stat -c %s {remote_tar}")).stdout.strip())
            except Exception as e:
                return False, f"Failed to stat remote tar: {str(e)}"

            # 获取远端哈希
            remote_sha256 = await self._calculate_remote_sha256(remote_tar)
            if not remote_sha256:
                return False, "Failed to calculate remote file SHA256"
            logger.info(f"Remote SHA256: {remote_sha256[:16]}...")

            # 选择下载方式
            if file_size < 50 * 1024 * 1024:
                # 小文件单连接
                logger.info(f"Using single-connection download")
                success, local_sha256 = await self._stream_download(remote_tar, local_tar, file_size, logger)
            else:
                # 大文件多连接
                concurrency = self._get_concurrency(file_size)
                logger.info(f"Using parallel download ({concurrency} connections)")
                success, local_sha256 = await self._parallel_download(remote_tar, local_tar, file_size, logger, concurrency)

            if not success:
                return False, local_sha256  # 这里 local_sha256 是错误信息

            # 验证哈希值
            logger.info(f"Local SHA256: {local_sha256[:16]}...")
            if remote_sha256 != local_sha256:
                return False, f"SHA256 verification failed: remote={remote_sha256[:16]}..., local={local_sha256[:16]}..."
            logger.info("SHA256 verification passed!")
            return True, local_sha256

        # 重试逻辑
        for attempt in range(max_retries):
            os.makedirs(os.path.dirname(local_tar), exist_ok=True)

            try:
                success, result = self._run(_async_smart_download())
                if success:
                    return True, result

                # 失败处理
                if attempt >= max_retries - 1:
                    return False, result

                # 重试
                delay = min(2 ** attempt, 10)
                logger.info(f"Download failed (attempt {attempt + 1}/{max_retries}): {result}")
                logger.info(f"Retrying in {delay} seconds...")
                time.sleep(delay)

                # 重连
                try:
                    self.connect()
                except Exception:
                    pass

            except Exception as e:
                if attempt >= max_retries - 1:
                    return False, f"Download failed after {max_retries} attempts: {str(e)}"

                delay = min(2 ** attempt, 10)
                logger.info(f"Download error (attempt {attempt + 1}/{max_retries}): {e}")
                logger.info(f"Retrying in {delay} seconds...")
                time.sleep(delay)
                try:
                    self.connect()
                except Exception:
                    pass

        return False, "Max retries exceeded"

    def close(self):
        """关闭连接"""
        if self._conn:
            try:
                self._conn.abort()
            except Exception:
                pass
            finally:
                self._conn = None

        if self._loop:
            try:
                if self._loop.is_running():
                    self._loop.stop()
                self._loop.close()
            except Exception:
                pass
            finally:
                self._loop = None


class CpanelSSHManager(SSHManager):
    def __init__(self, host: str, auth: dict, *args, **kwargs):
        super().__init__(host, auth, *args, **kwargs)

    # ======================== public =============================
    @staticmethod
    def sort_wp_list(result: dict) -> dict:
        if not result:
            return {}
        # 对每个用户的 wp 数组进行排序
        for user in result:
            wp_list = result[user]
            if not wp_list:
                continue
            # 按 domain 分组
            domain_groups = {}
            for wp in wp_list:
                domain = wp.get('domain', '')
                if domain not in domain_groups:
                    domain_groups[domain] = []
                domain_groups[domain].append(wp)
            # 每个domain组内排序
            for domain in domain_groups:
                domain_groups[domain].sort(key=lambda x: (
                    0 if not x.get('sub_path') else 1,  # sub_path 为空的排第一
                    len(x.get('sub_path', '')) if x.get('sub_path') else 0,  # 长度排序
                    x.get('sub_path', '')  # 字母排序
                ))
            # domain字母顺序排序各组
            sorted_domains = sorted(domain_groups.keys())
            # 重新组合
            sorted_wp_list = []
            for domain in sorted_domains:
                sorted_wp_list.extend(domain_groups[domain])
            result[user] = sorted_wp_list

        return result

    def get_remote_disk_free(self, path: str = "/") -> int:
        """
        获取远端磁盘可用剩余空间B单位
        Args:
            path: 检查的路径，默认为根目录
        Returns:
            int: 可用空间字节数
        """
        cmd = f"df -B1 {path} 2>/dev/null | tail -1 | awk '{{print $4}}'"
        exit_status, out, err = self.execute(cmd)
        if exit_status == 0 and out.strip().isdigit():
            return int(out.strip())
        # 降级使用statvfs方式
        cmd_stat = f"stat -f '%f * %S' {path} 2>/dev/null | bc"
        exit_status, out, _ = self.execute(cmd_stat)
        if exit_status == 0 and out.strip().isdigit():
            return int(out.strip())
        return 0

    def get_cp_user_info(self) -> list:
        """获取用户综合信息"""
        res = "whmapi1 listaccts --output=json"
        exit_status, out, err = self.execute(res, timeout=10)
        if exit_status != 0:
            raise Exception(f"Failed to list cPanel accounts: {err}")

        try:
            data = json.loads(out)
            accounts = data.get("data", {}).get("acct", [])
        except json.JSONDecodeError:
            raise Exception("Failed to parse cPanel listaccts response")

        result = []
        for acct in accounts:
            setup_date = ""
            raw_date = acct.get("startdate", "")
            if raw_date:
                try:
                    dt = datetime.strptime(raw_date, "%y %b %d %H:%M")
                    setup_date = dt.strftime(DATE_FORMAT)
                except:
                    setup_date = raw_date

            mail = acct.get("email", "")
            if mail and "@" in mail:
                name, domain = mail.rsplit("@", 1)
                if len(name) <= 2:
                    masked = "***"
                else:
                    masked = f"{name[0]}***{name[-1]}"
                mail = f"{masked}@{domain}"

            user_info = {
                "domain": acct.get("domain", "").lower(),
                "ip": acct.get("ip", ""),
                "user": acct.get("user", ""),
                "mail": mail or "",
                "setup_date": setup_date,
                "partition": acct.get("partition", ""),
                "owner": acct.get("owner", ""),
                "plan": acct.get("plan", ""),
                "theme": acct.get("theme", ""),
                "disk_block_limit": acct.get("disklimit", "0"),  # 不做处理暂时
                "disk_use": humanize_to_bytes(acct.get("diskused", "0")),
            }
            result.append(user_info)

        return result

    def get_cp_user_wp(self, configs: list[dict]) -> dict:
        """获取用户的wp网站，返回 dict[username -> list]"""
        if not configs: return {}

        finally_result = {cfg.get("user"): [] for cfg in configs}
        user_tasks = []
        valid_users = []

        for cfg in configs:
            user = cfg.get("user")
            home = cfg.get("partition", "home")
            if not user: continue

            # 限制find深度
            cmd = (
                f"user='{user}'; "
                f"search_dir='/{home}/{user}/public_html'; "
                f"[ -d \"$search_dir\" ] || exit 0; "
                f"find \"$search_dir\" -maxdepth 5 -name 'wp-config.php' -type f 2>/dev/null | while read cfg_path; do "
                f"  dir=$(dirname \"$cfg_path\"); "
                # 提取数据库信息
                f"  db_name=$(sed -n \"s/.*DB_NAME.*'\\([^']*\\)'.*/\\1/p\" \"$cfg_path\"); "
                f"  db_user=$(sed -n \"s/.*DB_USER.*'\\([^']*\\)'.*/\\1/p\" \"$cfg_path\"); "
                f"  db_pass=$(sed -n \"s/.*DB_PASSWORD.*'\\([^']*\\)'.*/\\1/p\" \"$cfg_path\"); "
                f"  db_pre=$(sed -n \"s/.*table_prefix.*'\\([^']*\\)'.*/\\1/p\" \"$cfg_path\"); "
                f"  [ -z \"$db_pre\" ] && db_pre='wp_'; "
                # 获取域名
                f"  domain=$(mysql -u\"$db_user\" -p\"$db_pass\" \"$db_name\" -N -s -e "
                f"    \"SELECT option_value FROM ${{db_pre}}options WHERE option_name='siteurl' LIMIT 1\" 2>/dev/null); "
                # 兜底 domain: 如果 mysql 失败, 用文件夹名
                f"  [ -z \"$domain\" ] && domain=$(basename \"$dir\"); "
                f"  domain=$(echo \"$domain\" | sed -e 's|^https://||' -e 's|^http://||' -e 's|^/||' -e 's|/$||'); "
                # 获取大小
                f"  size=$(du -sb \"$dir\" 2>/dev/null | awk '{{print $1}}'); "
                f"  [ -z \"$size\" ] && size=0; "
                # 获取证书内容 (包含子站点)
                f"  ssl_cert_b64=''; "
                # 提取主域名 (去掉子站点路径) 并转小写
                f"  ssl_domain=\"${{domain%%/*}}\"; "
                f"  ssl_domain=$(echo \"$ssl_domain\" | tr '[:upper:]' '[:lower:]'); "
                f"  ssl_config=\"/var/cpanel/userdata/$user/${{ssl_domain}}_SSL\"; "
                f"  if [ -f \"$ssl_config\" ] || [ -f \"${{ssl_config}}.cache\" ]; then "
                f"    cert_path=\"\"; "
                # 方法1: 从web配置中读取证书路径
                f"    conf_file=\"$ssl_config\"; "
                f"    [ ! -f \"$conf_file\" ] && conf_file=\"${{ssl_config}}.cache\"; "
                f"    if [ -f \"$conf_file\" ]; then "
                f"      cert_path=$(grep -E '^SSLCertificateFile[[:space:]]+' \"$conf_file\" 2>/dev/null | awk '{{print $2}}' | head -1); "
                f"      [ -z \"$cert_path\" ] && cert_path=$(grep -Ei '^sslcertificatefile=' \"$conf_file\" 2>/dev/null | cut -d= -f2); "
                f"    fi; "
                # 方法2: 直接使用标准证书路径
                f"    if [ -z \"$cert_path\" ] || [ ! -f \"$cert_path\" ]; then "
                f"      if [ -f \"/var/cpanel/ssl/apache_tls/${{ssl_domain}}/combined\" ]; then "
                f"        cert_path=\"/var/cpanel/ssl/apache_tls/${{ssl_domain}}/combined\"; "
                f"      fi; "
                f"    fi; "
                # 方法3: 通配符证书
                f"    if [ -z \"$cert_path\" ] || [ ! -f \"$cert_path\" ]; then "
                f"      main_domain=\"${{ssl_domain#*.}}\"; "
                f"      if [ \"$main_domain\" != \"$ssl_domain\" ]; then "
                f"        for wc in /var/cpanel/ssl/apache_tls/*.\"$main_domain\"/combined; do "
                f"          if [ -f \"$wc\" ]; then "
                f"            cert_path=\"$wc\"; "
                f"            break; "
                f"          fi; "
                f"        done; "
                f"      fi; "
                f"    fi; "
                f"    if [ -n \"$cert_path\" ] && [ -f \"$cert_path\" ]; then "
                f"      ssl_cert_b64=$(base64 -w0 \"$cert_path\" 2>/dev/null); "
                f"    fi; "
                f"  fi; "
                # 输出结果格式: SITE_DATA|路径|域名|字节|表前缀|db_name|db_user|db_pass|ssl_cert_b64
                f"  echo \"SITE_DATA|$dir|$domain|$size|$db_pre|$db_name|$db_user|$db_pass|$ssl_cert_b64\"; "
                f"done"
            )
            user_tasks.append(cmd)
            valid_users.append(user)

        if not user_tasks: return finally_result

        batch_res = self.asnyc_execute(user_tasks, timeout=120, max_concurrent=5)

        for i, res in enumerate(batch_res):
            user = valid_users[i]
            if res["code"] != 0 or not res["stdout"]: continue

            lines = res["stdout"].strip().split('\n')
            for line in lines:
                if not line.startswith("SITE_DATA|"): continue
                try:
                    parts = line.split('|')
                    if len(parts) < 8: continue

                    path = parts[1]
                    domain = parts[2]
                    if domain and isinstance(domain, str):
                        domain = domain.strip().strip('/')
                    domain = re.sub(r'^https?://', '', domain)
                    domain_part = domain.split("/")
                    domain = domain_part[0].lower() if domain_part else domain.lower()
                    sub_path = "/".join(domain_part[1:]) if len(domain_part) > 1 else ""
                    sub_path = sub_path.lstrip('/').strip()

                    disk_usage = int(parts[3]) if parts[3].isdigit() else 0

                    db_prefix = parts[4] or "wp_"
                    db_name = parts[5]
                    db_user = parts[6]
                    db_pass = parts[7]
                    ssl_cert_b64 = parts[8].strip() if len(parts) > 8 else ""

                    finally_result[user].append({
                        "name": domain if not sub_path else f"{domain}/{sub_path}",
                        "type": "wp",
                        "domain": domain,
                        "sub_path": sub_path,
                        "site_path": path,
                        "disk_usage": disk_usage,
                        "db_prefix": db_prefix,
                        "db_name": db_name,
                        "db_user": db_user,
                        "db_pass": db_pass,
                        "ssl_cert": ssl_cert_b64 if ssl_cert_b64 else None,
                    })
                except Exception as e:
                    public.print_log(f"Cpaenl Ssh manager Error parsing WP data for user {user}: {str(e)}")
                    continue

        finally_result = self.sort_wp_list(finally_result)
        return finally_result

    def get_cp_user_php(self, configs: list[dict]) -> list:
        """获取用户的php网站"""
        ...

    def get_cp_user_ssl(self, configs: list[dict]) -> dict:
        """获取用户的ssl证书，返回 dict[username -> list]"""
        if not configs:
            return {c.get("user"): [] for c in configs}
        user_tasks = []
        valid_users = []

        for cfg in configs:
            user = cfg.get("user")
            if not user: continue
            # grep 属于当前用户的域名
            # /etc/userdomains  "domain: user"
            script = (
                f"user='{user}'; "
                f"root_path='/var/cpanel/ssl/apache_tls'; "
                f"grep \": $user$\" /etc/userdomains 2>/dev/null | cut -d: -f1 | while read dom; do "
                f"  dom=$(echo $dom | tr -d '[:space:]'); "
                f"  [ -z \"$dom\" ] && continue; "
                f"  cert_path=\"$root_path/$dom/combined\"; "
                f"  if [ -f \"$cert_path\" ]; then "
                f"    content=$(base64 -w0 \"$cert_path\" 2>/dev/null); "
                f"    if [ ! -z \"$content\" ]; then "
                f"      echo \"SSL_FULL::::$dom::::$cert_path::::$content\"; "
                f"    fi; "
                f"  fi; "
                f"done"
            )
            user_tasks.append(script)
            valid_users.append(user)

        if not user_tasks:
            return {c.get("user"): [] for c in configs}

        batch_res = self.asnyc_execute(user_tasks, timeout=60)

        ssl_by_user = {u: [] for u in valid_users}
        for i, res in enumerate(batch_res):
            user = valid_users[i]
            if res["code"] != 0 or not res["stdout"]:
                continue

            lines = res["stdout"].strip().split('\n')
            for line in lines:
                if "SSL_FULL::::" not in line:
                    continue

                parts = line.split('::::')
                if len(parts) < 4:
                    continue

                domain = parts[1]
                path = parts[2]
                b64_content = parts[3]
                try:
                    cert_content = base64.b64decode(b64_content).decode('utf-8', errors='ignore').strip()
                    ssl_info = {
                        "name": domain.lower(),
                        "domain": domain.lower(),
                        "cert_path": path,
                        "disk_usage": 0,
                        "ssl_cert_b64": b64_content,
                        **parse_combined_ssl(cert_content)
                    }
                    ssl_info['type'] = ssl_info.get('issuer_O')
                    ssl_by_user[user].append(ssl_info)
                except Exception:
                    continue

        return ssl_by_user

    def get_cp_user_database(self, configs: list[dict]):
        """获取数据库"""
        ...

    @retry_act()
    def simple_pack(self, site_path: str, target_tar_path: str) -> Tuple[bool, str]:
        """打包"""
        cmd = f"cd '{site_path}' && tar -czf '{target_tar_path}' ."
        exit_status, out, err = self.execute(cmd)
        if exit_status != 0:
            return False, err
        return True, "success"

    @retry_act()
    def pack_wp_site(
            self, site_path: str, target_tar_path: str, sql_path: str = None, meta_json: dict = None
    ) -> Tuple[bool, str]:
        """针对cPanel包wp站点文件"""
        safe_site_path = site_path.replace("'", "'\\''")
        safe_tar_path = target_tar_path.replace("'", "'\\''")
        safe_sql_path = sql_path.replace("'", "'\\''") if sql_path else ""

        meta_str = json.dumps(meta_json) if meta_json else "{}"
        temp_meta_name = f"{uuid.uuid4().hex}_meta.json"
        temp_meta_path = f"/tmp/{temp_meta_name}"

        cmd = f"""
        cd '{safe_site_path}' || exit 1
        cat << 'EOF_META' > '{temp_meta_path}'
{meta_str}
EOF_META

        exclude_args=()
        while IFS= read -r nested_wp_conf; do
            if [ -n "$nested_wp_conf" ]; then
                nested_dir=$(dirname "$nested_wp_conf")
                # 相对路径下的第一级目录
                first_level=$(echo "$nested_dir" | cut -d'/' -f2)
                # 保护主站目录
                if [[ "$first_level" == "wp-admin" || "$first_level" == "wp-content" || "$first_level" == "wp-includes" ]]; then
                    exclude_args+=( "--exclude=$nested_dir" )
                else
                    # 连锅端
                    exclude_args+=( "--exclude=./$first_level" )
                fi
            fi
        done < <(find . -mindepth 2 -maxdepth 6 -type f -name "wp-config.php" 2>/dev/null)
        # 排除目标自身
        tar_name=$(basename '{safe_tar_path}')
        exclude_args+=( "--exclude=./$tar_name" )
        exclude_args+=( "--exclude=./error_log" "--exclude=./.trash" )

        if [ -n "{safe_sql_path}" ]; then
            sql_dir="$(dirname '{safe_sql_path}')"
            sql_name="$(basename '{safe_sql_path}')"
            tar -czf '{safe_tar_path}' --transform 's,^\\./,files/,' --transform="s,^$sql_name,sqldump.sql," --transform="s,^{temp_meta_name}$,meta.json," "${{exclude_args[@]}}" . -C "$sql_dir" "$sql_name" -C /tmp "{temp_meta_name}"
            rm -f '{safe_sql_path}'
        else
            tar -czf '{safe_tar_path}' --transform 's,^\\./,files/,' --transform="s,^{temp_meta_name}$,meta.json," "${{exclude_args[@]}}" . -C /tmp "{temp_meta_name}"
        fi

        rm -f '{temp_meta_path}'
        """

        # 打包 300 秒超时
        exit_status, out, err = self.execute(cmd, timeout=300)
        if exit_status != 0:
            return False, err

        return True, out

    @retry_act()
    def dump_db(self, db_name, db_user, db_pass, target_sql_path) -> Tuple[bool, str]:
        """导出数据库"""
        sql_dir = os.path.dirname(target_sql_path)
        cmd = f"mkdir -p '{sql_dir}' && mysqldump -u'{db_user}' -p'{db_pass}' {db_name} > {target_sql_path}"
        exit_status, out, err = self.execute(cmd)
        return exit_status == 0, out if out else err
