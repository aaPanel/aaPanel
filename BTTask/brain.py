# coding: utf-8
# -------------------------------------------------------------------
# aaPanel
# -------------------------------------------------------------------
# Copyright (c) 2014-2099 aaPanel(www.aapanel.com) All rights reserved.
# -------------------------------------------------------------------
# Author: aapanel
# -------------------------------------------------------------------
# ------------------------------
# task app
# ------------------------------
import os
import sys
from typing import Callable, Type, TypeVar, List, Dict

sys.path.insert(0, "/www/server/panel/class/")

import time
import threading
import heapq
import psutil
from dataclasses import dataclass, field, fields
from concurrent.futures import ThreadPoolExecutor, Future
from BTTask.conf import logger, CHILD_PID_PATH

T = TypeVar("T", bound="TaskInfo")

CPU_COUNT = psutil.cpu_count()


@dataclass(order=True)
class TaskInfo:
    # dont init next_run
    next_run: float = field(init=False)
    task_id: str
    # dont compare
    func: Callable = field(compare=False)
    interval: int | float
    is_core: bool
    loop: bool = True

    @classmethod
    def from_dict(cls: Type[T], data: dict, next_run: float) -> T:
        class_fields = {f.name for f in fields(cls)}
        filtered_data = {k: v for k, v in data.items() if k in class_fields}
        instance = cls(**filtered_data)
        instance.next_run = next_run
        return instance


class SimpleBrain:
    MAXFACTOR = 5.0  # 最大延迟因子
    MEM_LIMIT_MB = 100  # 内存限制
    MAX_WORKER = 16  # 最大线程数
    DEFAULT_WORKER = max(4, CPU_COUNT)  # 默认线程数
    CHECKER_INTERVAL = 10  # 检查器间隔时间/秒
    TIMEOUT_FACTOR = 2  # 任务超时倍率
    TASK_MAX_TIMEOUT = 6 * 3600.0  # 任务最大超时6小时

    __slots__ = (
        "cpu_max", "workers", "executor", "task_queue", "queue_lock",
        "task_status", "status_lock", "core_status_lock", "core_tasks", "delay_factor",
        "shutdown", "mem_limit", "pool_full_count",
    )

    def __init__(self, cpu_max: float = 30.0, workers: int = None, mem_limit: int = None):
        self.cpu_max = cpu_max
        self.workers = min(self.MAX_WORKER, workers or self.DEFAULT_WORKER)
        self.mem_limit = mem_limit or self.MEM_LIMIT_MB
        logger.debug(f"max_workers = {self.workers}, mem_limit = {self.mem_limit}MB")
        self.task_queue: List[TaskInfo] = []
        self.queue_lock = threading.RLock()
        self.status_lock = threading.RLock()
        self.core_status_lock = threading.RLock()
        self.core_tasks: Dict[str, tuple[threading.Thread, tuple[Callable, int]]] = {}
        self.task_status: Dict[str, tuple[float, float, Future]] = {}
        self.shutdown = False
        self.delay_factor = 0.0
        self.pool_full_count = 0
        self.executor = ThreadPoolExecutor(max_workers=self.workers)
        self._start_checker()
        logger.debug("SimpleBrain initialized")

    def _auto_pool(self):
        """自适应扩容池"""
        cpu = psutil.cpu_percent(interval=0.1)
        new_size = None
        # 扩容, 任务堆积
        if all([
            self.pool_full_count >= (60 // self.CHECKER_INTERVAL),  # 1min内连续满载
            cpu < 80,  # 在CPU未过载时进行线程扩容
            self.workers < self.MAX_WORKER
        ]):
            new_size = min(self.workers + 2, self.MAX_WORKER)
        # else: # 缩容

        if new_size and new_size != self.workers:
            logger.warning(f"Resize Task Pool from {self.workers} to {new_size}...")
            self._shutdown()
            os.system(
                f"nohup /www/server/panel/BT-Task --max-workers {new_size} >> /www/server/panel/logs/task.log 2>&1 &"
            )
            os._exit(0)

    @property
    def queue_size(self) -> int:
        with self.queue_lock:
            return len(self.task_queue)

    @property
    def get_current_process_memory(self):
        """返回当前进程内存MB"""
        return round(psutil.Process().memory_info().rss / 1024 / 1024, 2)

    def __mem_limit(self, current_mem: float = None):
        if not current_mem:
            current_mem = self.get_current_process_memory
        if current_mem >= self.mem_limit:
            logger.warning("Memory exceed limit...Restart brain task")
            self._shutdown()
            os.system(
                "nohup /www/server/panel/BT-Task >> /www/server/panel/logs/task.log 2>&1 &"
            )
            os._exit(0)

    def __core_alive(self):
        with self.core_status_lock:
            dead_tasks = [
                task_id for task_id, (thread, _) in self.core_tasks.items()
                if not thread.is_alive()
            ]
            for task_id in dead_tasks:
                logger.warning(f"Core task [{task_id}] is dead. Restarting...")
                _, args = self.core_tasks[task_id]
                thread = threading.Thread(
                    target=self._core_task_runner,
                    args=args,
                    daemon=True,
                    name=f"CoreTask-{task_id}"
                )
                thread.start()
                self.core_tasks[task_id] = (thread, args)

    def __normal_task_process(self, now_time: float) -> int:
        """
        - 对于普通任务 deadline_ts != -1，如果超时则移除。
        - 对于循环任务 deadline_ts == -1，如果其 future非running，则移除。
        返回当前运行中的所有普通任务数
        """

        def _pop_task(tid_str: str):
            self.clean_child(os.path.join(CHILD_PID_PATH, f"{tid_str}.pid"))
            self.task_status.pop(tid_str, None)

        with self.status_lock:
            for tid, info in list(self.task_status.items()):
                if not info or len(info) != 3:
                    _pop_task(tid)
                    continue

                start_time, deadline_ts, future = info
                if deadline_ts != -1:
                    if now_time > deadline_ts:
                        # 普通任务超时静默移除
                        _pop_task(tid)
                    continue

                if future and not future.running():
                    # loop任务异常移除
                    _pop_task(tid)
            return len(self.task_status)

    def __checker(self):
        resize_check_interval = 60  # 每1min检查一次是否需要扩容
        last_check_time = time.monotonic()
        last_resize_check = time.monotonic()

        while not self.shutdown:
            try:
                cpu = psutil.cpu_percent(interval=0.5)
                now = time.monotonic()
                # 每10s
                now_time = time.time()
                if now - last_check_time > self.CHECKER_INTERVAL:
                    last_check_time = now
                    mem = self.get_current_process_memory
                    self.__mem_limit(mem)  # 内存阈值检测
                    self.__core_alive()
                    running_tasks = self.__normal_task_process(now_time)
                    rate = (running_tasks / self.workers) * 100
                    logger.debug(
                        f"Mem: {mem} MB, CPU: {cpu}%, "
                        f"Pool: {running_tasks}/{self.workers} ({rate:.1f}%)"
                    )
                    if rate >= 90.0:  # 高负荷计数
                        self.pool_full_count += 1
                    else:  # 重置计数
                        self.pool_full_count = 0

                # 每1min
                if now - last_resize_check > resize_check_interval:
                    last_resize_check = now
                    self._auto_pool()

                if cpu > self.cpu_max:
                    self.delay_factor = min(
                        self.MAXFACTOR,
                        self.MAXFACTOR * (cpu - self.cpu_max) / (100.0 - self.cpu_max)
                    )
                elif self.delay_factor > 0:
                    self.delay_factor = max(0.0, self.delay_factor - 0.5)

            except Exception as e:
                logger.error(f"cpu mem checker error: {e}")
                time.sleep(5)

    def _start_checker(self):
        threading.Thread(
            target=self.__checker, daemon=True, name="BrainChecker"
        ).start()

    def _callback(self, task_id: str, future: Future):
        try:
            future.result()
        except Exception as e:
            logger.error(f"task error [{task_id}]: {str(e)}")
        finally:
            with self.status_lock:
                info = self.task_status.pop(task_id, None)
            if not info:
                logger.info(f"task done [{task_id}]")
                return
            start_time, _, _ = info
            logger.debug(
                f"task done [{task_id}] use time: {round(time.time() - start_time, 2)}s"
            )

    def _run_func_safe(self, func: Callable):
        """捕获异常"""
        try:
            func()
        except Exception:
            import traceback
            logger.error(traceback.format_exc())

    def _core_task_runner(self, funcs: Callable | List[Callable], interval: float):
        funcs = funcs if isinstance(funcs, list) else [funcs]
        while 1:
            for f in funcs:
                self._run_func_safe(f)
            time.sleep(interval)

    def _submit_task(self, tasks: List[TaskInfo]):
        for task in tasks:
            start_time = time.time()
            # 超时值: 自身任务间隔 * 超时倍率, 最大限制
            if not task.loop:
                timeout_sec = min(
                    self.TASK_MAX_TIMEOUT, (max(1.0, float(task.interval) * self.TIMEOUT_FACTOR))
                )
                deadline_ts = start_time + timeout_sec
            else:
                deadline_ts = -1  # 无限期

            future = None
            try:
                with self.status_lock:
                    future = self.executor.submit(task.func)
                    self.task_status[task.task_id] = (
                        start_time, deadline_ts, future
                    )
                future.add_done_callback(
                    lambda f, tid=task.task_id: self._callback(tid, f)
                )
            except Exception as e:
                logger.error(f"Failed to submit task [{task.task_id}]: {e}")
                # 无条件确保清理状态
                with self.status_lock:
                    self.task_status.pop(task.task_id, None)
                continue

    # ========================== Public =======================================
    def register_task(self, **kwargs):
        task_id = kwargs["task_id"]
        if kwargs.get("is_core"):
            # core task, daemon thread
            if task_id in self.core_tasks:
                return

            args = (kwargs["func"], kwargs["interval"])
            core_thread = threading.Thread(
                target=self._core_task_runner,
                args=args,
                daemon=True,
                name=f"CoreTask-{task_id}"
            )
            core_thread.start()
            logger.debug(
                f"registe core task [{task_id}], interval [{kwargs['interval']}]"
            )
            with self.core_status_lock:
                self.core_tasks[task_id] = (core_thread, args)

        else:  # not core task, heapq, pool
            with self.queue_lock:
                if task_id not in {t.task_id for t in self.task_queue}:
                    task = TaskInfo.from_dict(kwargs, next_run=time.monotonic())
                    heapq.heappush(self.task_queue, task)
                    logger.debug(
                        f"register normal task [{task_id}], interval [{task.interval}s]"
                    )

    @staticmethod
    def clean_child(pid_path: str = None):
        # 清理进程, 防泄漏
        def _clean_single(path):
            if not os.path.exists(path) or not path.endswith(".pid"):
                return
            try:
                with open(path, "r") as pf:
                    pid = int(pf.read().strip())
                psutil.Process(pid).kill()
            except (psutil.NoSuchProcess, psutil.AccessDenied, FileNotFoundError, ValueError):
                pass
            except Exception:
                pass
            finally:
                try:
                    os.remove(path)
                except Exception:
                    pass

        if not pid_path:
            # 清理所有子进程
            if not os.path.exists(CHILD_PID_PATH):
                return
            for pid_file in os.listdir(CHILD_PID_PATH):
                _clean_single(os.path.join(CHILD_PID_PATH, pid_file))
        else:  # 清理指定子进程
            _clean_single(pid_path)

    def run(self):
        self.clean_child()
        while not self.shutdown:
            now = time.monotonic()
            with self.queue_lock:
                ready_tasks = []
                while self.task_queue and self.task_queue[0].next_run <= now:
                    ready_tasks.append(heapq.heappop(self.task_queue))
                next_run_time = self.task_queue[0].next_run if self.task_queue else now + 1.0

            submit = []
            requeue = []
            for task in ready_tasks:
                with self.status_lock:
                    is_running = task.task_id in self.task_status

                if is_running:
                    logger.debug(f"still running, {task.task_id}")
                    task.next_run = now + task.interval
                    requeue.append(task)
                    continue

                if self.delay_factor > 0:
                    # 指数退避
                    logger.debug(f"cpu overload, requeue [{task.task_id}]")
                    task.next_run = now + 1.5 * (1.0 + self.delay_factor)
                    requeue.append(task)
                    continue

                # 更新间隔, 准备提交, 归队
                task.next_run = now + task.interval
                requeue.append(task)
                submit.append(task)

            if requeue:
                with self.queue_lock:
                    for task in requeue:
                        heapq.heappush(self.task_queue, task)
                    next_run_time = self.task_queue[0].next_run

            if submit:
                self._submit_task(submit)

            time.sleep(max(0.01, min(1.0, next_run_time - now)))

    def _shutdown(self):
        self.shutdown = True
        logger.warning("shutdown...")

        with self.queue_lock:
            pending = len(self.task_queue)
            self.task_queue.clear()

        with self.status_lock:
            running = len(self.task_status)
            self.task_status.clear()

        with self.core_status_lock:
            self.core_tasks.clear()

        logger.warning(
            f"shutdown complete, {running} tasks cancelled, {pending} tasks discarded"
        )

        self.executor.shutdown(wait=False)
        self.clean_child()
        logger.warning("released")
