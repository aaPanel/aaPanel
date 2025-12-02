# coding: utf-8
# -------------------------------------------------------------------
# aaPanel
# -------------------------------------------------------------------
# Copyright (c) 2014-2099 aaPanel(www.aapanel.com) All rights reserved.
# -------------------------------------------------------------------
# Author: aapanel
# -------------------------------------------------------------------

# ------------------------------
# 计划任务配置,常量
# ------------------------------

import logging
import os

__all__ = [
    "BASE_PATH",
    "CURRENT_TASK_VERSION",
    "pre",
    "PYTHON_BIN",
    "isTask",
    "exlogPath",
    "logger",
]

os.environ["BT_TASK"] = "1"

CHILD_PID_PATH = "/tmp/brain_task_pids/"
TIMEOUT = 600

BASE_PATH = "/www/server/panel"
CURRENT_TASK_VERSION = "1.0.1"
TASK_LOG_FILE = f"{BASE_PATH}/logs/task.log"

# 旧常量
pre = 0
isTask = "/tmp/panelTask.pl"
exlogPath = "/tmp/panelExec.log"

aaPy = f"{BASE_PATH}/pyenv/bin/python"
if os.path.exists(aaPy):
    PYTHON_BIN = aaPy
else:
    PYTHON_BIN = "/usr/bin/python"

# 日志简单限制50M
if os.path.getsize(TASK_LOG_FILE) > 50 * 1024 * 1024:
    try:
        os.remove(TASK_LOG_FILE)
        os.mknod(TASK_LOG_FILE)
    except Exception:
        pass

if os.path.exists("{}/data/debug.pl".format(BASE_PATH)):
    is_debug = True
else:
    is_debug = False

logging.basicConfig(
    level=logging.NOTSET if is_debug else logging.INFO,
    format="%(asctime)s [%(levelname)s]: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    filename=TASK_LOG_FILE,
    filemode="a+",
)
logger = logging.getLogger()
