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
from typing import Callable, Tuple, Type, TypeVar, List

sys.path.insert(0, "/www/server/panel/class/")

import time
import threading
import heapq
import psutil
from dataclasses import dataclass, field, fields
from concurrent.futures import ThreadPoolExecutor, Future, wait
from BTTask.conf import logger, CHILD_PID_PATH

T = TypeVar("T", bound="TaskInfo")


@dataclass(order=True)
class TaskInfo:
    # dont init next_run
    next_run: float = field(init=False)
    task_id: str
    # dont compare
    func: Callable = field(compare=False)
    interval: int | float
    is_core: bool

    @classmethod
    def from_dict(cls: Type[T], data: dict, next_run: float) -> T:
        class_fields = {f.name for f in fields(cls)}
        filtered_data = {k: v for k, v in data.items() if k in class_fields}
        instance = cls(**filtered_data)
        instance.next_run = next_run
        return instance


class SimpleBrain:
    __slots__ = (
        "cpu_max", "max_workers", "executor", "task_queue", "queue_lock",
        "task_status", "status_lock", "core_tasks", "delay_factor",
        "shutdown_flag", "_start_time",
    )

    def __init__(self, cpu_max: float = 30.0, max_workers: int = None):
        self.cpu_max = cpu_max
        self.max_workers = max_workers or max(2, psutil.cpu_count() * 2)
        logger.debug(f"max_workers = {self.max_workers}")
        self.task_queue: List[TaskInfo] = []
        self.task_status = {}
        self.queue_lock = threading.RLock()
        self.status_lock = threading.RLock()
        self.core_tasks = {}
        self.shutdown_flag = False
        self.delay_factor = 0.0
        self._start_time = time.monotonic()
        self.executor = ThreadPoolExecutor(max_workers=self.max_workers)
        self._start_checker()
        logger.debug("SimpleBrain initialized")

    @property
    def queue_size(self) -> int:
        with self.queue_lock:
            return len(self.task_queue)

    @property
    def get_current_process_memory(self):
        """返回当前进程内存MB"""
        p = psutil.Process(os.getpid())
        info = p.memory_info()
        rss_mb = round(info.rss / 1024 / 1024, 2)
        uss_mb = None
        try:
            uss_mb = round(p.memory_full_info().uss / 1024 / 1024, 2)
        except Exception:
            pass
        return {"rss_mb": rss_mb, "uss_mb": uss_mb}

    def __mem_limit(self, rss: int):
        if rss >= 100:
            logger.warning("Memory exceed limit...Restart brain task")
            self.shutdown()
            # ps: mian has been checked Task process
            os.system(
                "nohup /www/server/panel/BT-Task >> /www/server/panel/logs/task.log 2>&1 &"
            )

    def __core_alive(self):
        with self.status_lock:
            dead_tasks = [
                task_id for task_id, task_info in self.core_tasks.items()
                if not task_info["thread"].is_alive()
            ]
            for task_id in dead_tasks:
                logger.warning(f"Core task [{task_id}] is dead. Restarting...")
                task_info = self.core_tasks[task_id]
                args = task_info["args"]
                thread = threading.Thread(
                    target=self._core_task_runner,
                    args=args,
                    daemon=True,
                    name=f"CoreTask-{task_id}"
                )
                thread.start()
                self.core_tasks[task_id]["thread"] = thread

    def __checker(self):
        count = 0
        while not self.shutdown_flag:
            try:
                cpu = psutil.cpu_percent(interval=0.5)
                if count >= 5:
                    count = 0
                    self.__core_alive()
                    mem = self.get_current_process_memory
                    logger.debug("Mem: {} MB, CPU: {}%".format(mem["rss_mb"], cpu))
                    self.__mem_limit(int(mem.get("rss_mb", 0)))

                if cpu <= self.cpu_max:
                    target = 0.0
                else:
                    target = 2.0 * (cpu - self.cpu_max) / (100.0 - self.cpu_max)
                self.delay_factor = max(0.0, min(2.0, target))
                time.sleep(0.5)
                count += 1
            except Exception as e:
                logger.error(f"cpu mem checker error: {e}")
                time.sleep(3)

    def _start_checker(self):
        threading.Thread(
            target=self.__checker, daemon=True, name="BrainChecker"
        ).start()

    def _callback(self, task_id: str, future: Future):
        try:
            future.result(timeout=0.5)
        except Exception as e:
            logger.error(f"task error [{task_id}]: {str(e)}")
        finally:
            with self.status_lock:
                try:
                    status = self.task_status.pop(task_id)
                    logger.debug(
                        f"task done [{task_id}] use time: {round(time.time() - status['start_time'], 2)}s"
                    )
                except Exception:
                    logger.info(f"task done [{task_id}]")

    def _core_task_runner(self, funcs: Callable | List[Callable], interval: float):
        try:
            while 1:
                if not isinstance(funcs, list):
                    try:
                        funcs()
                    except Exception:
                        import traceback
                        logger.error(traceback.format_exc())
                else:
                    for f in funcs:
                        try:
                            f()
                        except Exception:
                            import traceback
                            logger.error(traceback.format_exc())
                            continue
                time.sleep(interval)
        except Exception:
            import traceback
            logger.error(traceback.format_exc())

    def _submit_task(self, tasks: List[Tuple[str, Callable, bool]]):
        for task_id, func in tasks:
            future: Future = self.executor.submit(func)
            with self.status_lock:
                self.task_status[task_id] = {
                    "start_time": time.time(),
                    "future": future
                }
            future.add_done_callback(
                lambda f, tid=task_id: self._callback(tid, f)
            )

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
            with self.status_lock:
                self.core_tasks[task_id] = {"thread": core_thread, "args": args}

        else:  # not core task, heapq, pool
            with self.queue_lock:
                if not any(t.task_id == kwargs.get("task_id", "") for t in self.task_queue):
                    task = TaskInfo.from_dict(
                        kwargs, next_run=time.monotonic()
                    )
                    heapq.heappush(self.task_queue, task)
                    logger.debug(
                        f"register normal task [{task_id}], interval [{task.interval}s]"
                    )

    @staticmethod
    def clean_child():
        # 清理进程, 防泄漏
        if os.path.exists(CHILD_PID_PATH):
            for pid_file in os.listdir(CHILD_PID_PATH):
                pid_path = os.path.join(CHILD_PID_PATH, pid_file)
                try:
                    with open(pid_path, 'r') as pf:
                        pid = int(pf.read().strip())
                    proc = psutil.Process(pid)
                    proc.kill()
                except (psutil.NoSuchProcess, psutil.AccessDenied, FileNotFoundError):
                    pass
                finally:
                    try:
                        os.remove(pid_path)
                    except OSError:
                        pass

    def run(self):
        self.clean_child()
        while not self.shutdown_flag:
            now = time.monotonic()
            tasks = []
            with self.queue_lock:
                while self.task_queue and self.task_queue[0].next_run <= now:
                    task: TaskInfo = heapq.heappop(self.task_queue)

                    with self.status_lock:
                        is_running = task.task_id in self.task_status

                    if is_running:
                        logger.warning(f"still running, {task.task_id}")
                        task.next_run += task.interval
                        heapq.heappush(self.task_queue, task)
                        continue

                    if self.delay_factor >= 0.2:
                        # 指数退避
                        logger.warning(f"cpu overload, requeue [{task.task_id}]")
                        task.next_run += 1.1 * (1.0 + self.delay_factor)
                        heapq.heappush(self.task_queue, task)
                        continue

                    # 归队
                    task.next_run = now + task.interval
                    heapq.heappush(self.task_queue, task)
                    tasks.append(
                        (task.task_id, task.func)
                    )
            if tasks:
                self._submit_task(tasks)

            next_time = self.task_queue[0].next_run if self.task_queue else now + 1.0
            # [0.01, 1.0]
            delay_time = max(0.01, min(1.0, next_time - now))
            time.sleep(delay_time)

    def shutdown(self, timeout: int = 10):
        self.shutdown_flag = True
        logger.warning("shutdown...")

        with self.queue_lock:
            pending = len(self.task_queue)
            self.task_queue.clear()

        with self.status_lock:
            futures = [s["future"] for s in self.task_status.values()]
            self.task_status.clear()

        if futures:
            done, not_done = wait(futures, timeout=timeout)
            for f in not_done:
                f.cancel()
            logger.warning(
                f"shutdown complete, {len(done)} tasks finished, "
                f"{len(not_done)} tasks cancelled, "
                f"{pending} tasks discarded"
            )

        self.executor.shutdown(wait=False)
        self.clean_child()
        logger.warning("released")
