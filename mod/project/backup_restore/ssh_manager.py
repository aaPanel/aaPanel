#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# -------------------------------------------------------------------
# aapanel
# -------------------------------------------------------------------
# Copyright (c) 2015-2099 aapanel(http://www.aapanel.com) All rights reserved.
# -------------------------------------------------------------------
# 通过SSH连接新服务器，安装aa面板并进行备份还原
import argparse
import datetime
import json
import os
import re
import socket
import sys
import time
import warnings

import paramiko

if "/www/server/panel/class" not in sys.path:
    sys.path.insert(0, "/www/server/panel/class")
if "/www/server/panel/class_v2" not in sys.path:
    sys.path.insert(0, "/www/server/panel/class_v2")
if "/www/server/panel" not in sys.path:
    sys.path.insert(0, "/www/server/panel")

import public

warnings.filterwarnings("ignore", category=SyntaxWarning)

# 添加迁移进度跟踪相关的变量和工具函数
BACKUP_RESTORE_PATH = "/www/backup/backup_restore"
MIGRATION_TASK_JSON = '/www/backup/backup_restore/migration_task.json'
MIGRATION_LOG_FILE = '/www/backup/backup_restore/migration.log'
MIGRATION_PL_FILE = '/www/backup/backup_restore/migration.pl'
MIGRATION_SUCCESS_FILE = '/www/backup/backup_restore/migration_success.pl'

# 迁移状态码
MIGRATION_STATUS = {
    'PENDING': 0,  # 等待中
    'RUNNING': 1,  # 运行中
    'COMPLETED': 2,  # 已完成
    'FAILED': 3,  # 失败
}

# 迁移阶段
MIGRATION_STAGES = {
    'INIT': {
        'code': 'init',
        'display': public.lang('Initializing'),
        'progress': 5,
    },
    'PANEL_INSTALL': {
        'code': 'panel_install',
        'display': public.lang('Panel Installation'),
        'progress': 20,
    },
    'LOCAL_BACKUP': {
        'code': 'local_backup',
        'display': public.lang('Local Backup'),
        'progress': 40,
    },
    'FILE_UPLOAD': {
        'code': 'file_upload',
        'display': public.lang('File Upload'),
        'progress': 70,
    },
    'RESTORE': {
        'code': 'restore',
        'display': public.lang('Data Restore'),
        'progress': 90,
    },
    'COMPLETED': {
        'code': 'completed',
        'display': public.lang('Migration Completed'),
        'progress': 100,
    }
}


def write_migration_log(message, task_id=None, log_type='INFO'):
    """写入迁移日志"""
    timestamp = time.strftime('%Y-%m-%d %H:%M:%S')
    log_message = f"[{timestamp}] [{log_type}] {message}\n"

    # 确保目录存在
    log_dir = os.path.dirname(MIGRATION_LOG_FILE)
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)

    # 写入主日志文件
    with open(MIGRATION_LOG_FILE, 'a+') as f:
        f.write(log_message)

    # 如果指定了任务ID，同时写入任务特定的日志文件
    if task_id:
        task_log_file = f"/www/backup/backup_restore/{task_id}_migration/migration.log"
        task_log_dir = os.path.dirname(task_log_file)
        if not os.path.exists(task_log_dir):
            os.makedirs(task_log_dir)
        with open(task_log_file, 'a+') as f:
            f.write(log_message)

    return log_message.strip()


def update_migration_status(task_id, stage, status=MIGRATION_STATUS['RUNNING'], message=None, details=None):
    """更新迁移任务状态"""
    # 确保目录存在
    task_dir = f"/www/backup/backup_restore/{task_id}_migration"
    if not os.path.exists(task_dir):
        os.makedirs(task_dir)

    # 任务状态文件路径
    task_status_file = f"{task_dir}/status.json"

    # 读取当前状态（如果存在）
    current_status = {}
    if os.path.exists(task_status_file):
        try:
            with open(task_status_file, 'r') as f:
                current_status = json.load(f)
        except Exception as e:
            write_migration_log(public.lang("Failed to read task status: {}").format(e), task_id, 'ERROR')

    # 更新状态为新格式
    current_time = time.strftime('%Y-%m-%d %H:%M:%S')
    if 'start_time' not in current_status:
        current_status['start_time'] = current_time

    current_status['task_id'] = task_id
    current_status['last_update'] = current_time
    current_status['server_ip'] = current_status.get('server_ip', '')
    current_status['run_type'] = stage
    current_status['run_status'] = status
    current_status['step'] = list(MIGRATION_STAGES.keys()).index(stage) + 1 if stage in MIGRATION_STAGES else 1
    current_status['migrate_progress'] = MIGRATION_STAGES.get(stage, {}).get('progress', 0)
    current_status['migrate_msg'] = message if message else MIGRATION_STAGES.get(stage, {}).get('display', stage)

    if details:
        if 'task_info' not in current_status:
            current_status['task_info'] = {}
        current_status['task_info'].update(details)

    # 如果任务完成，记录完成时间
    if status == MIGRATION_STATUS['COMPLETED']:
        current_status['end_time'] = current_time
        if 'start_time' in current_status:
            start_time = time.strptime(current_status['start_time'], '%Y-%m-%d %H:%M:%S')
            end_time = time.strptime(current_time, '%Y-%m-%d %H:%M:%S')
            total_seconds = time.mktime(end_time) - time.mktime(start_time)
            current_status['total_time'] = total_seconds

    # 保存状态
    try:
        with open(task_status_file, 'w') as f:
            # noinspection PyTypeChecker
            json.dump(current_status, f, ensure_ascii=False, indent=2)
    except Exception as e:
        write_migration_log(public.lang("Failed to save task status: {}").format(e), task_id, 'ERROR')

    # 同时更新全局任务记录
    update_global_migration_tasks(task_id, current_status)
    return current_status


def update_global_migration_tasks(task_id, task_status):
    """更新全局迁移任务记录 - 唯一任务运行模式"""
    # 在唯一任务运行模式下，我们只保存最新的任务
    try:
        task_dir = os.path.dirname(MIGRATION_TASK_JSON)
        if not os.path.exists(task_dir):
            os.makedirs(task_dir)
        # 直接写入当前任务作为全局任务
        with open(MIGRATION_TASK_JSON, 'w') as f:
            # noinspection PyTypeChecker
            json.dump(task_status, f, ensure_ascii=False, indent=2)
    except Exception as e:
        write_migration_log(public.lang("Failed to save global task record: {}").format(e), task_id, 'ERROR')


def get_migration_status(task_id=None):
    """获取迁移任务进度
    Args:
        task_id: 指定任务ID，如果为空则返回最新任务状态
    Returns:
        任务状态信息
    """
    # 如果没有指定task_id，则从migration_task.json获取当前运行的任务
    if not task_id:
        if os.path.exists(MIGRATION_PL_FILE):
            try:
                with open(MIGRATION_PL_FILE, 'r') as f:
                    task_id = f.read().strip()
            except:
                return {"status": False, "msg": public.lang("Unable to read current running task ID")}

        # 如果没有获取到任务ID，则直接读取全局任务文件
        if not task_id and os.path.exists(MIGRATION_TASK_JSON):
            try:
                with open(MIGRATION_TASK_JSON, 'r') as f:
                    task_data = json.load(f)
                    return {"status": True, "msg": public.lang("Successfully retrieved task status"), "data": task_data}
            except Exception as e:
                return {"status": False, "msg": public.lang("Failed to read task status: {}").format(e)}

        if not task_id:
            return {"status": False, "msg": public.lang("No running tasks")}

    # 获取指定任务的状态
    task_status_file = f"/www/backup/backup_restore/{task_id}_migration/status.json"
    if os.path.exists(task_status_file):
        try:
            with open(task_status_file, 'r') as f:
                task_data = json.load(f)
                return {"status": True, "msg": public.lang("Successfully retrieved task status"), "data": task_data}
        except Exception as e:
            return {"status": False, "msg": public.lang("Failed to read task status: {}").format(e)}
    else:
        return {"status": False, "msg": public.lang("Task {} does not exist").format(task_id)}


def create_migration_task(task_name, host, port=22, username='root', password=None, key_file=None, backup_file=None):
    """创建新的迁移任务"""
    task_id = str(int(time.time()))

    # 检查是否存在正在运行的任务
    if os.path.exists(MIGRATION_PL_FILE):
        try:
            with open(MIGRATION_PL_FILE, 'r') as f:
                running_task_id = f.read().strip()

            # 如果有运行中的任务，返回错误
            if running_task_id:
                error_msg = public.lang("A task is already running, task ID: {}").format(running_task_id)
                write_migration_log(error_msg)
                return {"status": False, "msg": error_msg}
        except:
            pass

    # 按照comMod.py中的格式创建任务数据
    print(host)
    task_data = {
        'task_id': task_id,
        'server_ip': host,
        'ssh_port': port,
        'ssh_user': username,
        'auth_type': 'password' if password else 'key',
        'password': password if password else '',
        'timestamp': int(time.time()),
        'run_type': 'INIT',
        'run_status': MIGRATION_STATUS['RUNNING'],
        'step': 1,
        'migrate_progress': MIGRATION_STAGES['INIT']['progress'],
        'migrate_msg': public.lang('Migration task initializing'),
        'task_info': {
            'task_name': task_name,
            'backup_file': backup_file,
            'start_time': time.strftime('%Y-%m-%d %H:%M:%S')
        }
    }

    # 创建任务目录
    task_dir = f"/www/backup/backup_restore/{task_id}_migration"
    if not os.path.exists(task_dir):
        os.makedirs(task_dir)

    # 保存任务状态
    with open(f"{task_dir}/status.json", 'w') as f:
        # noinspection PyTypeChecker
        json.dump(task_data, f, ensure_ascii=False, indent=2)

    # 更新全局任务记录
    update_global_migration_tasks(task_id, task_data)

    # 创建进程锁文件
    with open(MIGRATION_PL_FILE, 'w') as f:
        f.write(task_id)

    write_migration_log(public.lang("Creating migration task: {} -> {}").format(task_name, host), task_id)
    return {"status": True, "msg": public.lang("Migration task created successfully"), "task_id": task_id}


class BtInstallManager:
    def __init__(
            self, host, port=22, username='root', password=None, key_file=None,
            backup_file=None, panel_port=7800, max_retries=3, retry_interval=5, task_id=None
    ):
        """
        初始化SSH连接管理器
        Args:
            host: 远程服务器IP
            port: SSH端口，默认22
            username: SSH用户名，默认root
            password: SSH密码，与key_file二选一
            key_file: SSH密钥文件路径，与password二选一
            backup_file: 本地备份文件路径
            panel_port: 宝塔面板端口，默认7800
            max_retries: 最大重试次数，默认3次
            retry_interval: 重试间隔，默认5秒
            task_id: 迁移任务ID，用于跟踪进度
        """
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.key_file = key_file
        self.backup_file = backup_file
        self.panel_port = panel_port
        self.ssh = None
        self.sftp = None
        self.remote_backup_path = '/www/backup/backup_restore'
        self.max_retries = max_retries
        self.retry_interval = retry_interval
        self.task_id = task_id  # 添加任务ID

    def connect(self):
        """建立SSH连接"""
        try:
            if self.username != "root":
                raise Exception("Migration only supports root user SSH connections")

            if self.task_id:
                write_migration_log(public.lang("Connecting to server {}:{}").format(self.host, self.port),
                                    self.task_id)

            self.ssh = paramiko.SSHClient()
            self.ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

            if self.key_file:
                key = self._load_ssh_key(self.key_file)
                self.ssh.connect(self.host, self.port, self.username, pkey=key)
            else:
                self.ssh.connect(self.host, self.port, self.username, self.password)

            self.sftp = self.ssh.open_sftp()
            print(public.lang("[+] Successfully connected to server {}").format(self.host))

            if self.task_id:
                write_migration_log(public.lang("Successfully connected to server {}").format(self.host), self.task_id)

            return True
        except paramiko.AuthenticationException:
            error_msg = public.lang("Authentication failed: incorrect username or password")
            print(f"[!] {error_msg}")

            if self.task_id:
                write_migration_log(error_msg, self.task_id, 'ERROR')
                update_migration_status(self.task_id, 'INIT', MIGRATION_STATUS['FAILED'], message=error_msg)
            return {"status": False, "msg": error_msg}

        except paramiko.SSHException as e:
            error_msg = public.lang("SSH connection exception: {}").format(e)
            print(f"[!] {error_msg}")

            if self.task_id:
                write_migration_log(error_msg, self.task_id, 'ERROR')
                update_migration_status(self.task_id, 'INIT', MIGRATION_STATUS['FAILED'], message=error_msg)
            return {"status": False, "msg": error_msg}

        except socket.error as e:
            error_msg = public.lang("Network connection error: {}").format(e)
            print(f"[!] {error_msg}")

            if self.task_id:
                write_migration_log(error_msg, self.task_id, 'ERROR')
                update_migration_status(self.task_id, 'INIT', MIGRATION_STATUS['FAILED'], message=error_msg)
            return {"status": False, "msg": error_msg}

        except Exception as e:
            error_msg = public.lang("Failed to connect to server: {}").format(e)
            print(f"[!] {error_msg}")

            if self.task_id:
                write_migration_log(error_msg, self.task_id, 'ERROR')
                update_migration_status(self.task_id, 'INIT', MIGRATION_STATUS['FAILED'], message=error_msg)
            return {"status": False, "msg": error_msg}

    def _load_ssh_key(self, key_file, password=None):
        """根据密钥文件自动判断类型并加载"""
        # 读取文件内容
        with open(key_file, 'r') as f:
            content = f.read()

        # 尝试不同的密钥类型
        key = None
        errors = []

        # 判断明确标记的密钥类型
        if "BEGIN RSA PRIVATE KEY" in content:
            try:
                key = paramiko.RSAKey.from_private_key_file(key_file, password=password)
                if self.task_id:
                    write_migration_log(public.lang("Connecting using RSA key"), self.task_id)
                return key
            except Exception as e:
                errors.append(public.lang("Failed to load RSA key: {}").format(str(e)))

        elif "BEGIN DSA PRIVATE KEY" in content:
            try:
                key = paramiko.DSSKey.from_private_key_file(key_file, password=password)
                if self.task_id:
                    write_migration_log(public.lang("Connecting using DSA key"), self.task_id)
                return key
            except Exception as e:
                errors.append(public.lang("Failed to load DSA key: {}").format(str(e)))

        elif "BEGIN EC PRIVATE KEY" in content:
            try:
                key = paramiko.ECDSAKey.from_private_key_file(key_file, password=password)
                if self.task_id:
                    write_migration_log(public.lang("Connecting using ECDSA key"), self.task_id)
                return key
            except Exception as e:
                errors.append(public.lang("Failed to load ECDSA key: {}").format(str(e)))

        elif "BEGIN OPENSSH PRIVATE KEY" in content:
            # 对于OPENSSH格式，尝试所有可能的类型
            key_types = [
                (paramiko.Ed25519Key, "Ed25519"),
                (paramiko.RSAKey, "RSA"),
                (paramiko.ECDSAKey, "ECDSA"),
                (paramiko.DSSKey, "DSA")
            ]

            for key_class, key_name in key_types:
                try:
                    key = key_class.from_private_key_file(key_file, password=password)
                    if self.task_id:
                        write_migration_log(public.lang("Connecting using {} key").format(key_name), self.task_id)
                    return key
                except Exception as e:
                    errors.append(public.lang("Failed to load {} key: {}").format(key_name, str(e)))

        # 如果以上方法都失败，抛出异常
        error_msg = public.lang("Unable to recognize or load the key, please check if the key file format is correct")
        if self.task_id:
            write_migration_log(error_msg, self.task_id)
        raise ValueError(error_msg)

    def reconnect(self):
        """重新连接SSH"""
        if self.ssh:
            try:
                self.ssh.close()
            except:
                pass
        if self.sftp:
            try:
                self.sftp.close()
            except:
                pass

        self.ssh = None
        self.sftp = None

        for attempt in range(self.max_retries):
            print(public.lang("[*] Attempting to reconnect to the server (attempt {}/{})...").format(attempt + 1,
                                                                                                     self.max_retries))
            connection_result = self.connect()
            if isinstance(connection_result, dict):
                # 连接失败，返回错误信息
                if attempt == self.max_retries - 1:
                    return connection_result
            elif connection_result:
                return True
            time.sleep(self.retry_interval)

        print(public.lang("[!] Failed to reconnect to the server, maximum number of retries reached ({})").format(
            self.max_retries))
        return {"status": False,
                "msg": public.lang("Failed to reconnect to the server, maximum number of retries reached ({})").format(
                    self.max_retries)}

    def disconnect(self):
        """关闭SSH连接"""
        if self.sftp:
            self.sftp.close()
        if self.ssh:
            self.ssh.close()
        print(public.lang("[+] Disconnected from server {}").format(self.host))

    def exec_command(self, command, print_output=True, retry=True):
        """
        执行远程命令
        Args:
            command: 要执行的命令
            print_output: 是否打印输出
            retry: 连接断开时是否重试
        Returns:
            (stdout, stderr)
        """
        if not self.ssh:
            if retry:
                reconnect_result = self.reconnect()
                if isinstance(reconnect_result, dict):
                    return None, None
                return self.exec_command(command, print_output, False)  # 重连成功后再次尝试，但不再重试
            print(public.lang("[!] SSH connection not established"))
            return None, None

        try:
            print(public.lang("[*] Executing command: {}").format(command))
            stdin, stdout, stderr = self.ssh.exec_command(command)
            stdout_content = stdout.read().decode('utf-8')
            stderr_content = stderr.read().decode('utf-8')

            if print_output:
                if stdout_content:
                    print(public.lang("[+] Output:"), stdout_content)
                if stderr_content:
                    print(public.lang("[!] Error:"), stderr_content)
            return stdout_content, stderr_content

        except (socket.error, paramiko.SSHException) as e:
            print(public.lang("[!] SSH connection disconnected while executing command: {}").format(e))
            if retry:
                reconnect_result = self.reconnect()
                if isinstance(reconnect_result, dict):
                    return None, None
                print(public.lang("[*] Reconnected successfully, retrying command..."))
                return self.exec_command(command, print_output, False)  # 重连成功后再次尝试，但不再重试
            return None, None

    def check_os_type(self):
        """检测服务器操作系统类型"""
        print(public.lang("[*] Detecting server OS type..."))
        os_type = None

        stdout, _ = self.exec_command("cat /etc/os-release")
        if stdout is None:
            return None

        if "CentOS" in stdout:
            os_type = "centos"
        elif "Ubuntu" in stdout:
            os_type = "ubuntu"
        elif "Debian" in stdout:
            os_type = "debian"
        else:
            stdout, _ = self.exec_command("cat /etc/redhat-release", print_output=False)
            if stdout and ("CentOS" in stdout or "Red Hat" in stdout):
                os_type = "centos"

        if os_type:
            print(public.lang("[+] OS type: {}").format(os_type))
        else:
            print(public.lang("[!] Unable to determine OS type"))

        return os_type

    def check_wget_curl(self) -> dict:
        error_msg = public.lang("curl or wget installation failed, please install it manually")
        count = 0
        while count <= 6:
            count += 1
            print(public.lang(f"[*] Checking if curl or wget is installed..."))
            # 检查curl或wget是否安装
            stdout, stderr = self.exec_command("which curl || which wget")
            if stdout is not None and (stdout.strip() or stderr.strip()):
                print(public.lang("[+] curl or wget is installed"))
                return {"status": True, "msg": public.lang("curl or wget is installed")}
            # 安装curl或wget
            print(public.lang("[!] curl or wget is not installed, trying to install..."))
            os_type = self.check_os_type()
            if os_type == "centos":
                install_cmd = "yum update -y && yum install -y wget"
            elif os_type in ["ubuntu", "debian"]:
                install_cmd = "apt-get update -y && apt-get install -y wget"
            else:
                error_msg = public.lang("Unable to detect OS type, please install curl or wget manually")
                print(f"[!] {error_msg}")
                write_migration_log(error_msg)
                if self.task_id:
                    update_migration_status(
                        self.task_id, 'PANEL_INSTALL', MIGRATION_STATUS['FAILED'], message=error_msg
                    )
                return {"status": False, "msg": error_msg}
            self.exec_command(install_cmd)
            # 等待安装完成
            time.sleep(5)

        if self.task_id:
            write_migration_log(error_msg)
            update_migration_status(
                self.task_id, 'PANEL_INSTALL', MIGRATION_STATUS['FAILED'], message=error_msg
            )
        return {"status": False, "msg": error_msg}

    def install_bt_panel(self):
        """安装宝塔面板"""
        if self.task_id:
            update_migration_status(self.task_id, 'PANEL_INSTALL', message=public.lang("Start installing aapanel"))

        print(public.lang("[*] Starting to install aapanel..."))
        bash = "install_panel_backup_en.sh"
        # bash = "install_panel_backup_en-test.sh"
        install_cmd = f'URL=https://www.aapanel.com/script/{bash} && if [ -f /usr/bin/curl ];then curl -ksSO "$URL" ;else wget --no-check-certificate -O {bash} "$URL";fi;bash {bash} aapanel -y -P 7800 > /root/bt_install.log 2>&1 &'

        if self.task_id:
            update_migration_status(self.task_id, 'PANEL_INSTALL',
                                    message=public.lang(f"Installing aapanel using command, please wait..."))

        print(public.lang("[*] Installing aapanel with command: {}").format(install_cmd))
        stdout, stderr = self.exec_command(install_cmd)

        # 安装超时限制15分钟
        timeout = 900
        start_time = time.time()

        while time.time() - start_time < timeout:
            get_install_progress_cmd = f"ps -ef|grep bash|grep {bash}|grep -v grep"
            stdout, stderr = self.exec_command(get_install_progress_cmd)

            if stdout is None or stdout.strip() == "":
                get_install_log_cmd = "cat /root/bt_install.log"
                stdout, stderr = self.exec_command(get_install_log_cmd)
                if public.lang("Installation completed") in stdout or "Installed successfully" in stdout:
                    message = public.lang("aapanel installed successfully, starting backup task...")
                    print(f"[+] {message}")

                    # 提取面板信息
                    username_match = re.search(r"username: (.*)", stdout)
                    password_match = re.search(r"password: (.*)", stdout)

                    admin_path, stderr = self.exec_command("cat /www/server/panel/data/admin_path.pl")

                    panel_info = {
                        "panel_url": f"http://{self.host}:{self.panel_port}{admin_path}"
                    }

                    if username_match and password_match:
                        username = username_match.group(1)
                        password = password_match.group(1)
                        panel_info["username"] = username
                        panel_info["password"] = password
                        print("[+] username: {}".format(username))
                        print("[+] password: {}".format(password))
                        print(
                            public.lang("[+] address: http://{}:{}{}").format(self.host, self.panel_port, admin_path)
                        )

                        if self.task_id:
                            update_migration_status(
                                self.task_id,
                                'PANEL_INSTALL',
                                MIGRATION_STATUS['COMPLETED'],
                                message=message,
                                details={"panel_info": panel_info}
                            )
                    return {"status": True, "msg": message, "data": panel_info}
                else:
                    error_msg = public.lang("aapanel installation failed")
                    print(f"[!] {error_msg}")
                    if self.task_id:
                        update_migration_status(
                            self.task_id,
                            'PANEL_INSTALL',
                            MIGRATION_STATUS['FAILED'],
                            message=error_msg,
                            details={"stderr": stderr}
                        )
                    return {"status": False, "msg": error_msg, "error_msg": stderr}
            else:
                time.sleep(3)
                get_install_log_cmd = "cat /root/bt_install.log"
                stdout, stderr = self.exec_command(get_install_log_cmd)
                write_migration_log(public.lang("Installation progress: {}").format(stdout))

        # 检查安装结果
        if public.lang("Installation completed") in stdout or "Installed successfully" in stdout:
            message = public.lang("aapanel installed successfully, starting backup task...")
            print(f"[+] {message}")

            # 提取面板信息
            username_match = re.search(r"username: (.*)", stdout)
            password_match = re.search(r"password: (.*)", stdout)

            admin_path, stderr = self.exec_command("cat /www/server/panel/data/admin_path.pl")

            panel_info = {
                "panel_url": f"http://{self.host}:{self.panel_port}{admin_path}"
            }

            if username_match and password_match:
                username = username_match.group(1)
                password = password_match.group(1)
                panel_info["username"] = username
                panel_info["password"] = password
                print(public.lang("[+] username: {}").format(username))
                print(public.lang("[+] password: {}").format(password))
                print(
                    public.lang("[+] address: http://{}:{}{}").format(self.host, self.panel_port, admin_path)
                )
                if self.task_id:
                    update_migration_status(
                        self.task_id,
                        'PANEL_INSTALL',
                        MIGRATION_STATUS['COMPLETED'],
                        message=message,
                        details={"panel_info": panel_info}
                    )
            return {"status": True, "msg": message, "data": panel_info}
        else:
            error_msg = public.lang("aapanel installation failed")
            print(f"[!] {error_msg}")
            if self.task_id:
                update_migration_status(
                    self.task_id,
                    'PANEL_INSTALL',
                    MIGRATION_STATUS['FAILED'],
                    message=error_msg,
                    details={"stderr": stderr}
                )
            return {"status": False, "msg": error_msg, "error_msg": stderr}

    def create_backup_dir(self):
        """创建备份目录"""
        print(public.lang("[*] Creating backup directory..."))

        # 检查备份目录是否存在，不存在则创建
        self.exec_command(f"mkdir -p {self.remote_backup_path}")

        stdout, _ = self.exec_command(f"test -d {self.remote_backup_path} && echo 'exists'")
        if stdout is None:
            return False

        if 'exists' in stdout:
            print(public.lang("[+] Backup directory {} created").format(self.remote_backup_path))
            return True
        else:
            print(public.lang("[!] Failed to create backup directory {}").format(self.remote_backup_path))
            return False

    def get_remote_file_size(self, remote_path):
        """获取远程文件大小"""
        try:
            if not self.sftp:
                reconnect_result = self.reconnect()
                if isinstance(reconnect_result, dict):
                    return -1

            return self.sftp.stat(remote_path).st_size
        except Exception as e:
            public.print_log(public.lang("Failed to get remote file size: {}").format(e))
            # 文件不存在或其他错误
            return -1

    def write_backup_info(self, backup_file_path):
        backup_task_json = "/www/backup/backup_restore/backup_task.json"
        if os.path.exists(backup_task_json):
            task_json_data = json.loads(public.ReadFile(backup_task_json))
            for item in task_json_data:
                if item["backup_file"] == backup_file_path:
                    migrate_backup_info_path = "/www/backup/backup_restore/migrate_backup_info.json"
                    public.WriteFile(migrate_backup_info_path, json.dumps(item))

    def upload_backup_file(self):
        """上传备份文件到服务器（支持断点续传）"""
        if not self.backup_file or not os.path.exists(self.backup_file):
            error_msg = public.lang("Backup file {} does not exist").format(self.backup_file)
            print(f"[!] {error_msg}")
            if self.task_id:
                update_migration_status(self.task_id, 'FILE_UPLOAD', MIGRATION_STATUS['FAILED'], message=error_msg)
            return {"status": False, "msg": error_msg}

        if self.task_id:
            update_migration_status(
                self.task_id,
                'FILE_UPLOAD',
                message=public.lang("Start uploading backup file {} to the server").format(self.backup_file)
            )

        print(public.lang("[*] Starting to upload backup file {} to the server...").format(self.backup_file))
        backup_filename = os.path.basename(self.backup_file)
        remote_file_path = f"{self.remote_backup_path}/{backup_filename}"

        # 确保备份目录存在
        if not self.create_backup_dir():
            error_msg = public.lang("Failed to create backup directory")
            if self.task_id:
                update_migration_status(self.task_id, 'FILE_UPLOAD', MIGRATION_STATUS['FAILED'], message=error_msg)
            return {"status": False, "msg": error_msg}

        # 获取本地文件大小
        local_file_size = os.path.getsize(self.backup_file)
        file_size_mb = local_file_size / (1024 * 1024)
        print(public.lang("[*] File size: {:.2f} MB").format(file_size_mb))

        if self.task_id:
            update_migration_status(
                self.task_id,
                'FILE_UPLOAD',
                message=public.lang("Preparing to upload file, size: {:.2f} MB").format(file_size_mb),
                details={"upload": {"total_size": local_file_size, "size_mb": file_size_mb}}
            )

        # 检查远程文件是否存在，存在则获取大小
        remote_file_size = self.get_remote_file_size(remote_file_path)

        # 如果远程文件存在且大小与本地相同，则认为已上传完成
        # 检查hash?
        if remote_file_size == local_file_size:
            message = public.lang("File already fully uploaded, skipping upload step")
            print(f"[+] {message}")

            if self.task_id:
                update_migration_status(
                    self.task_id,
                    'FILE_UPLOAD',
                    MIGRATION_STATUS['COMPLETED'],
                    message=message,
                    details={"upload": {"status": "completed", "remote_path": remote_file_path}}
                )

            return {"status": True, "msg": message, "data": {"remote_path": remote_file_path}}

        # 如果远程文件存在但大小不同，尝试断点续传
        if remote_file_size > 0:
            print(public.lang("[*] Incomplete upload file detected, attempting to resume..."))
            print(
                public.lang("[*] Uploaded: {:.2f}% ({:.2f}MB / {:.2f}MB)").format(
                    remote_file_size / local_file_size * 100, remote_file_size / (1024 * 1024), file_size_mb)
            )

            if self.task_id:
                update_migration_status(
                    self.task_id,
                    'FILE_UPLOAD',
                    message=public.lang("Incomplete upload file detected, resuming from {:.2f}MB").format(
                        remote_file_size / (1024 * 1024)),
                    details={
                        "upload": {
                            "status": "resuming",
                            "progress": remote_file_size / local_file_size * 100,
                            "uploaded": remote_file_size,
                            "total_size": local_file_size
                        }
                    }
                )
        else:
            remote_file_size = 0
            print(public.lang("[*] Starting new upload..."))

            if self.task_id:
                update_migration_status(
                    self.task_id,
                    'FILE_UPLOAD',
                    message=public.lang("Starting new upload"),
                    details={"upload": {"status": "starting", "progress": 0}}
                )

        max_attempts = 3
        attempt = 0
        offset = remote_file_size
        chunk_size = 1024 * 1024  # 1MB 分块上传

        while offset < local_file_size and attempt < max_attempts:
            try:
                if not self.sftp:
                    reconnect_result = self.reconnect()
                    if isinstance(reconnect_result, dict):
                        return reconnect_result

                # 打开本地文件
                with open(self.backup_file, 'rb') as local_file:
                    if offset > 0:
                        local_file.seek(offset)

                    # 如果文件已存在，则使用追加模式，否则创建新文件
                    if offset > 0:
                        remote_file = self.sftp.open(remote_file_path, 'ab')
                    else:
                        remote_file = self.sftp.open(remote_file_path, 'wb')

                    with remote_file:
                        start_time = time.time()
                        current_offset = offset
                        last_update_time = start_time
                        last_progress_report = 0

                        # 分块读取和上传
                        while current_offset < local_file_size:
                            data = local_file.read(chunk_size)
                            if not data:
                                break

                            remote_file.write(data)
                            current_offset += len(data)
                            progress = current_offset / local_file_size * 100
                            elapsed = time.time() - start_time
                            speed = (current_offset - offset) / elapsed / 1024 if elapsed > 0 else 0

                            # 计算剩余时间
                            remaining_bytes = local_file_size - current_offset
                            if speed > 0:
                                remaining_time_seconds = remaining_bytes / (speed * 1024)  # speed is in KB/s
                                remaining_time_str = time.strftime("%H:%M:%S", time.gmtime(remaining_time_seconds))
                            else:
                                remaining_time_str = "N/A"

                            print(
                                public.lang("\r[*] Upload progress: {:.2f}% - {:.2f} KB/s - Remaining time: {}").format(
                                    progress, speed, remaining_time_str),
                                end=""
                            )
                            write_migration_log(
                                public.lang(
                                    "Total size {:.2f}MB Uploading file: {:.2f}% - {:.2f} KB/s - Remaining time: {}").format(
                                    local_file_size / (1024 * 1024), progress, speed, remaining_time_str)
                            )

                            # 每5秒或进度增加5%更新一次状态
                            current_time = time.time()
                            if (
                                    current_time - last_update_time > 5 or progress - last_progress_report >= 5) and self.task_id:
                                last_update_time = current_time
                                last_progress_report = progress
                                update_migration_status(
                                    self.task_id,
                                    'FILE_UPLOAD',
                                    message=public.lang(
                                        "Total size {:.2f}MB Uploading file: {:.2f}% - {:.2f} KB/s - Remaining time: {}").format(
                                        local_file_size / (1024 * 1024), progress, speed, remaining_time_str),
                                    details={
                                        "upload": {
                                            "status": "uploading",
                                            "progress": progress,
                                            "speed": speed,
                                            "elapsed": elapsed,
                                            "uploaded": current_offset,
                                            "total_size": local_file_size,
                                            "remaining_time": remaining_time_str
                                        }
                                    }
                                )

                            # 定期刷新缓冲区
                            if current_offset % (chunk_size * 10) == 0:
                                remote_file.flush()

                        # 确保最后一次刷新
                        remote_file.flush()
                        print()  # 换行

                        # 成功完成上传
                        if current_offset >= local_file_size:
                            elapsed = time.time() - start_time
                            total_speed = (current_offset - offset) / elapsed / 1024 if elapsed > 0 else 0

                            message = public.lang(
                                "Upload completed, took {:.2f} seconds, average speed {:.2f} KB/s").format(elapsed,
                                                                                                           total_speed)
                            print(f"[+] {message}")

                            # 验证文件大小
                            final_size = self.get_remote_file_size(remote_file_path)
                            if final_size == local_file_size:
                                success_msg = public.lang("File size verification passed: {:.2f}MB").format(
                                    final_size / (1024 * 1024))
                                print(f"[+] {success_msg}")

                                if self.task_id:
                                    update_migration_status(
                                        self.task_id,
                                        'FILE_UPLOAD',
                                        MIGRATION_STATUS['COMPLETED'],
                                        message=success_msg,
                                        details={
                                            "upload": {
                                                "status": "completed",
                                                "remote_path": remote_file_path,
                                                "file_size": final_size,
                                                "elapsed_time": elapsed,
                                                "speed": total_speed
                                            }
                                        }
                                    )

                                return {"status": True, "msg": public.lang("File uploaded successfully"), "data": {
                                    "remote_path": remote_file_path,
                                    "file_size": final_size,
                                    "elapsed_time": elapsed,
                                    "speed": total_speed
                                }}
                            else:
                                error_msg = public.lang("File size mismatch: local {:.2f}MB, remote {:.2f}MB").format(
                                    local_file_size / (1024 * 1024), final_size / (1024 * 1024))
                                print(f"[!] {error_msg}")

                                if self.task_id:
                                    update_migration_status(
                                        self.task_id,
                                        'FILE_UPLOAD',
                                        message=error_msg,
                                        details={
                                            "upload": {
                                                "status": "size_mismatch",
                                                "local_size": local_file_size,
                                                "remote_size": final_size
                                            }
                                        }
                                    )

                                # 更新偏移量，继续尝试
                                offset = final_size
                        else:
                            # 部分上传，更新偏移量
                            offset = current_offset

            except (socket.error, paramiko.SSHException, IOError) as e:
                attempt += 1
                error_msg = public.lang("Upload interrupted: {}").format(e)
                print(f"\n[!] {error_msg}")
                print(public.lang("[*] Will try to resume from breakpoint {:.2f}MB (attempt {}/{})...").format(
                    offset / (1024 * 1024), attempt, max_attempts))

                if self.task_id:
                    update_migration_status(
                        self.task_id,
                        'FILE_UPLOAD',
                        message=public.lang(
                            "Upload interrupted: {}, will try to resume from breakpoint {:.2f}MB (attempt {}/{})...").format(
                            e, offset / (1024 * 1024), attempt, max_attempts),
                        details={
                            "upload": {
                                "status": "interrupted",
                                "attempt": attempt,
                                "max_attempts": max_attempts,
                                "uploaded": offset,
                                "total_size": local_file_size
                            }
                        }
                    )

                time.sleep(2)

                # 尝试重新连接
                reconnect_result = self.reconnect()
                if isinstance(reconnect_result, dict):
                    continue

        if offset >= local_file_size:
            message = public.lang("File uploaded successfully")
            print(f"[+] {message}")

            if self.task_id:
                update_migration_status(
                    self.task_id,
                    'FILE_UPLOAD',
                    MIGRATION_STATUS['COMPLETED'],
                    message=message,
                    details={"upload": {"status": "completed", "remote_path": remote_file_path}}
                )

            return {"status": True, "msg": message, "data": {"remote_path": remote_file_path}}
        else:
            error_msg = public.lang("File upload failed, maximum number of retries reached")
            print(f"[!] {error_msg}")

            if self.task_id:
                update_migration_status(
                    self.task_id,
                    'FILE_UPLOAD',
                    MIGRATION_STATUS['FAILED'],
                    message=error_msg,
                    details={
                        "upload": {
                            "status": "failed",
                            "attempts": attempt,
                            "max_attempts": max_attempts
                        }
                    }
                )

            return {"status": False, "msg": error_msg}

    def extract_backup(self, backup_filename):
        """解压备份文件"""
        print(public.lang("[*] Starting to extract backup file {}...").format(backup_filename))
        remote_file_path = f"{self.remote_backup_path}/{backup_filename}"

        # 检查文件是否存在
        stdout, _ = self.exec_command(f"test -f {remote_file_path} && echo 'exists'")
        if stdout is None or 'exists' not in stdout:
            print(public.lang("[!] Backup file {} does not exist").format(remote_file_path))
            return False

        # 解压文件
        extract_cmd = f"cd {self.remote_backup_path} && tar -zxvf {backup_filename}"
        stdout, stderr = self.exec_command(extract_cmd)
        if stdout is None:
            return False

        # 提取备份文件中的时间戳
        timestamp_match = re.search(r"(\d+)_backup", backup_filename)
        if not timestamp_match:
            print(public.lang("[!] Unable to extract timestamp from backup filename"))
            return False

        timestamp = timestamp_match.group(1)
        backup_dir = f"{self.remote_backup_path}/{timestamp}_backup"

        # 检查解压是否成功
        stdout, _ = self.exec_command(f"test -d {backup_dir} && echo 'exists'")
        if stdout is None or 'exists' not in stdout:
            print(public.lang("[!] Backup file extraction failed"))
            return False

        print(public.lang("[+] Backup file extracted successfully, directory: {}").format(backup_dir))
        return timestamp

    def restore_backup(self, timestamp):
        """还原备份"""
        if self.task_id:
            update_migration_status(
                self.task_id,
                'RESTORE',
                message=public.lang("Start restoring backup (timestamp: {})").format(timestamp)
            )

        print(public.lang("[*] Starting to restore backup (timestamp: {})...").format(timestamp))

        # 等待宝塔面板服务启动
        print(public.lang("[*] Waiting for aapanel service to start..."))

        # 检查还原模块是否存在
        restore_script = "/www/server/panel/mod/project/backup_restore/restore_manager.py"
        stdout, _ = self.exec_command(f"test -f {restore_script} && echo 'exists'")
        if stdout is None or 'exists' not in stdout:
            error_msg = public.lang("Restore module does not exist: {}").format(restore_script)
            print(f"[!] {error_msg}")

            if self.task_id:
                update_migration_status(
                    self.task_id,
                    'RESTORE',
                    MIGRATION_STATUS['FAILED'],
                    message=error_msg
                )

            return False

        # 执行还原命令
        if self.task_id:
            update_migration_status(
                self.task_id,
                'RESTORE',
                message=public.lang("Executing add restore task...")
            )

        print(public.lang("[*] Executing restore operation..."))
        restore_cmd = "nohup btpython {restore_script} restore_data {timestamp} {force_restore} > /dev/null 2>&1 &".format(
            restore_script=restore_script, timestamp=timestamp, force_restore=1
        )
        print(restore_cmd)
        stdout, stderr = self.exec_command(restore_cmd)
        print(stdout)
        print(stderr)

        touch_pl_cmd = "echo 'True'  > /www/server/panel/data/migration.pl"
        touch_out, touch_err = self.exec_command(touch_pl_cmd)
        print(touch_out)
        print(touch_err)

        message = public.lang(
            "Restore command executed successfully, please check the restore progress on the new server"
        )
        print(f"[+] {message}")

        if self.task_id:
            update_migration_status(
                self.task_id,
                'RESTORE',
                MIGRATION_STATUS['COMPLETED'],
                message=message
            )
            return True

        if stdout is None:
            error_msg = public.lang("Failed to execute restore command")

            if self.task_id:
                update_migration_status(
                    self.task_id,
                    'RESTORE',
                    MIGRATION_STATUS['FAILED'],
                    message=error_msg
                )
            return False

        if "还原完成" in stdout or "success" in stdout:
            message = public.lang("Backup restored successfully")
            print(f"[+] {message}")

            if self.task_id:
                update_migration_status(
                    self.task_id,
                    'RESTORE',
                    MIGRATION_STATUS['COMPLETED'],
                    message=message
                )
            return True
        else:
            error_msg = public.lang("Backup restore failed, please check the log")
            print(f"[!] {error_msg}")

            if self.task_id:
                update_migration_status(
                    self.task_id,
                    'RESTORE',
                    MIGRATION_STATUS['FAILED'],
                    message=error_msg,
                    details={"stderr": stderr}
                )
            return False

    # 增加执行迁移任务的方法
    def migrate(self, task_id):
        """执行完整的迁移流程"""
        try:
            if os.path.exists(MIGRATION_LOG_FILE):
                public.ExecShell("rm -f {}".format(MIGRATION_LOG_FILE))
            # 更新任务状态为开始
            update_migration_status(task_id, 'INIT', message=public.lang("Start migration task"))

            # 连接服务器
            self.task_id = task_id
            connection_result = self.connect()
            if isinstance(connection_result, dict) and not connection_result.get("status", False):
                return connection_result

            # 检查curl 或者 wget 是否安装
            write_migration_log(public.lang("Check if curl or wget is installed"))
            wget_ = self.check_wget_curl()
            if wget_.get("status") is False:
                return wget_
            write_migration_log(public.lang("curl or wget check passed"))
            # 安装宝塔面板
            update_migration_status(task_id, 'PANEL_INSTALL', message=public.lang("Preparing to install aapanel"))
            write_migration_log(public.lang("Installing aapanel... estimated 5 minutes...."))
            install_result = self.install_bt_panel()
            if not install_result.get("status", False):
                return install_result
            write_migration_log(public.lang("aapanel installation completed, starting backup task..."))
            write_migration_log(public.lang(
                "Please wait for the backup task to complete uploading files before logging into the panel...")
            )
            # 在本机执行备份任务
            update_migration_status(
                task_id,
                'LOCAL_BACKUP',
                message=public.lang("Start executing backup task on this machine")
            )
            write_migration_log(public.lang("Start executing backup task on this machine"))
            # 创建备份管理器实例
            backup_manager = BackupRestoreManager(
                host=self.host,
                port=self.port,
                username=self.username,
                password=self.password,
                key_file=self.key_file,
                backup_file=None,
                panel_port=self.panel_port,
                max_retries=self.max_retries,
                retry_interval=self.retry_interval,
                task_id=task_id
            )

            # 执行本地备份任务
            backup_manager.add_backup_task()

            # 等待备份任务完成，检查migrate_backup_success.pl文件
            migrate_backup_success_pl = '/www/backup/backup_restore/migrate_backup_success.pl'
            migrate_backup_pl = '/www/backup/backup_restore/migrate_backup.pl'

            # 更新状态
            update_migration_status(
                task_id,
                'LOCAL_BACKUP',
                message=public.lang("Waiting for local backup to complete")
            )

            # 最多等待21600秒（6小时）
            timeout = 21600
            start_time = time.time()

            while not os.path.exists(migrate_backup_success_pl) and time.time() - start_time < timeout:
                time.sleep(5)
                if not os.path.exists(migrate_backup_pl):
                    error_msg = public.lang("Backup task cancelled or failed")
                    update_migration_status(task_id, 'LOCAL_BACKUP', MIGRATION_STATUS['FAILED'], message=error_msg)
                    return {"status": False, "msg": error_msg}

            if not os.path.exists(migrate_backup_success_pl):
                error_msg = public.lang("Backup task timed out and did not complete within the specified time")
                update_migration_status(task_id, 'LOCAL_BACKUP', MIGRATION_STATUS['FAILED'], message=error_msg)
                return {"status": False, "msg": error_msg}

            # 从migrate_backup.pl文件中获取时间戳
            if os.path.exists(migrate_backup_pl):
                try:
                    timestamp = public.ReadFile(migrate_backup_pl).strip()
                    update_migration_status(task_id, 'LOCAL_BACKUP',
                                            message=public.lang("Got backup timestamp: {}").format(timestamp))
                except:
                    error_msg = public.lang("Failed to read backup timestamp")
                    update_migration_status(task_id, 'LOCAL_BACKUP', MIGRATION_STATUS['FAILED'], message=error_msg)
                    return {"status": False, "msg": error_msg}
            else:
                error_msg = public.lang("Backup timestamp file does not exist")
                update_migration_status(task_id, 'LOCAL_BACKUP', MIGRATION_STATUS['FAILED'], message=error_msg)
                return {"status": False, "msg": error_msg}

            # 从migrate_backup_success.pl获取备份文件路径
            try:
                backup_file_path = public.ReadFile(migrate_backup_success_pl).strip()
                if not os.path.exists(backup_file_path):
                    # 尝试默认路径
                    default_backup_path = f"/www/backup/backup_restore/{timestamp}_backup.tar.gz"
                    if os.path.exists(default_backup_path):
                        backup_file_path = default_backup_path
                    else:
                        error_msg = public.lang("Backup file does not exist: {}").format(backup_file_path)
                        update_migration_status(task_id, 'LOCAL_BACKUP', MIGRATION_STATUS['FAILED'], message=error_msg)
                        return {"status": False, "msg": error_msg}
            except:
                error_msg = public.lang("Failed to read backup file path")
                update_migration_status(task_id, 'LOCAL_BACKUP', MIGRATION_STATUS['FAILED'], message=error_msg)
                return {"status": False, "msg": error_msg}

            update_migration_status(task_id, 'LOCAL_BACKUP', MIGRATION_STATUS['COMPLETED'],
                                    message=public.lang("Local backup completed: {}").format(backup_file_path))
            if os.path.exists("/www/backup/backup_restore/backup.log"):
                backup_log_data = public.ReadFile("/www/backup/backup_restore/backup.log")
                write_migration_log(backup_log_data)
            write_migration_log(public.lang("Local backup completed"))

            # 上传备份文件
            write_migration_log(public.lang("Preparing to upload backup file"))
            self.backup_file = backup_file_path
            update_migration_status(
                task_id,
                'FILE_UPLOAD',
                message=public.lang("Preparing to upload backup file: {}").format(backup_file_path)
            )
            upload_result = self.upload_backup_file()
            if not upload_result.get("status", False):
                return upload_result

            self.write_backup_info(backup_file_path)
            # 上传backup_task.json文件
            backup_task_json = '/www/backup/backup_restore/migrate_backup_info.json'
            if os.path.exists(backup_task_json):
                update_migration_status(task_id, 'FILE_UPLOAD',
                                        message=public.lang("Preparing to upload migrate_backup_info.json file"))
                remote_task_json_path = f"{self.remote_backup_path}/migrate_backup_info.json"

                try:
                    if not self.sftp:
                        reconnect_result = self.reconnect()
                        if isinstance(reconnect_result, dict):
                            error_msg = public.lang("Connection lost while uploading migrate_backup_info.json file")
                            update_migration_status(task_id, 'FILE_UPLOAD', message=error_msg)
                            return reconnect_result

                    # 确保备份目录存在
                    if not self.create_backup_dir():
                        error_msg = public.lang("Failed to create backup directory")
                        update_migration_status(task_id, 'FILE_UPLOAD', message=error_msg)
                        return {"status": False, "msg": error_msg}

                    # 上传任务文件
                    self.sftp.put(backup_task_json, remote_task_json_path)
                    update_migration_status(task_id, 'FILE_UPLOAD',
                                            message=public.lang("migrate_backup_info.json file uploaded successfully"))
                except Exception as e:
                    error_msg = public.lang("Failed to upload migrate_backup_info.json file: {}").format(e)
                    update_migration_status(task_id, 'FILE_UPLOAD', message=error_msg)
                    return {"status": False, "msg": error_msg}
            write_migration_log(public.lang("Backup file uploaded successfully"))
            # 解压备份文件
            backup_filename = os.path.basename(self.backup_file)
            print(1)
            print(backup_filename)
            print(2)
            update_migration_status(
                task_id,
                'RESTORE',
                message=public.lang("Preparing to extract backup file {}").format(backup_filename)
            )

            # 确保使用正确的时间戳（从migrate_backup.pl中获取）
            print(timestamp)
            extract_timestamp = timestamp

            # 在远程服务器上创建migrate_backup.pl文件，写入时间戳
            remote_migrate_backup_pl = f"{self.remote_backup_path}/migrate_backup.pl"
            self.exec_command(f"echo '{extract_timestamp}' > {remote_migrate_backup_pl}")

            # 还原备份
            write_migration_log(public.lang("Preparing to add restore backup task"))
            update_migration_status(
                task_id,
                'RESTORE',
                message=public.lang("Preparing to restore backup (timestamp: {})").format(extract_timestamp)
            )
            if not self.restore_backup(extract_timestamp):
                error_msg = public.lang("An exception occurred during backup and restore")
                update_migration_status(task_id, 'RESTORE', MIGRATION_STATUS['FAILED'], message=error_msg)
                return {"status": False, "msg": error_msg}
            write_migration_log(public.lang("Restore backup task added successfully"))

            # 完成迁移
            success_msg = public.lang("All migration operations have been completed")
            update_migration_status(task_id, 'COMPLETED', MIGRATION_STATUS['COMPLETED'], message=success_msg)
            write_migration_log(public.lang("Migration task completed"))
            public.ExecShell(
                "\cp -rpa {} {}/{}_migration/migration.log".format(MIGRATION_LOG_FILE, BACKUP_RESTORE_PATH, task_id)
            )
            # 创建成功标记
            with open(MIGRATION_SUCCESS_FILE, 'w') as f:
                f.write(task_id)

            print(f"[+] {success_msg}")
            return {"status": True, "msg": success_msg}

        except Exception as e:
            error_msg = public.lang("An error occurred during the migration process: {}").format(e)
            print(f"[!] {error_msg}")

            if task_id:
                update_migration_status(task_id, 'INIT', MIGRATION_STATUS['FAILED'], message=error_msg)

            return {"status": False, "msg": error_msg}
        finally:
            self.disconnect()

            # 清理进程锁文件
            if os.path.exists(MIGRATION_PL_FILE):
                public.ExecShell(f"rm -f {MIGRATION_PL_FILE}")

    # 接口1: 验证SSH连接信息
    def verify_ssh_connection(self):
        """验证SSH连接信息是否正常"""
        print(public.lang("[*] Verifying SSH connection information..."))
        connection_result = self.connect()

        if isinstance(connection_result, dict):
            return connection_result

        if connection_result:
            print(public.lang("[+] SSH connection verification successful"))
            self.disconnect()
            return {"status": True, "msg": public.lang("SSH connection verification successful")}

        return {"status": False, "msg": public.lang("SSH connection verification failed")}

    # 接口2: 安装宝塔面板
    def install_panel(self):
        """安装宝塔面板接口"""
        print(public.lang("[*] Installing aapanel..."))

        # 连接服务器
        connection_result = self.connect()
        if isinstance(connection_result, dict):
            return connection_result

        # 安装宝塔面板
        try:
            install_result = self.install_bt_panel()
            return install_result
        finally:
            self.disconnect()

    # 接口3: 上传备份文件
    def upload_backup(self):
        """上传备份文件接口"""
        print(public.lang("[*] Uploading backup file..."))

        if not self.backup_file:
            return {"status": False, "msg": public.lang("Backup file path not specified")}

        # 连接服务器
        connection_result = self.connect()
        if isinstance(connection_result, dict):
            return connection_result

        # 上传备份文件
        try:
            upload_result = self.upload_backup_file()
            return upload_result
        finally:
            self.disconnect()

    def run(self):
        """执行全部安装和还原流程"""
        try:
            # 连接服务器
            connection_result = self.connect()
            if isinstance(connection_result, dict):
                return connection_result

            # 安装宝塔面板
            install_result = self.install_bt_panel()
            if not install_result["status"]:
                return install_result

            # 如果指定了备份文件，执行还原操作
            if self.backup_file:
                # 上传备份文件
                upload_result = self.upload_backup_file()
                if not upload_result["status"]:
                    return upload_result

                # 解压备份文件
                backup_filename = os.path.basename(self.backup_file)
                timestamp = self.extract_backup(backup_filename)
                if not timestamp:
                    return {"status": False, "msg": public.lang("Backup file extraction failed")}

                # 还原备份
                if not self.restore_backup(timestamp):
                    return {"status": False, "msg": public.lang("Backup restore failed")}

            print(public.lang("[+] 所有操作已完成"))
            return {"status": True, "msg": public.lang("所有操作已完成")}

        except Exception as e:
            print(public.lang("[!] 执行过程中发生错误: {}").format(e))
            return {"status": False, "msg": public.lang("执行过程中发生错误: {}").format(e)}
        finally:
            self.disconnect()


class BackupRestoreManager:
    def __init__(self, host, port, username, password, key_file, backup_file, panel_port,
                 max_retries, retry_interval, task_id):
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.key_file = key_file
        self.base_path = '/www/backup/backup_restore'
        self.bakcup_task_json = self.base_path + '/backup_task.json'
        self.backup_pl_file = self.base_path + '/backup.pl'
        self.migrate_backup_pl_file = self.base_path + '/migrate_backup.pl'
        self.migrate_backup_success_file = self.base_path + '/migrate_backup_success.pl'

    def add_backup_task(self):
        backup_config = []
        if os.path.exists(self.bakcup_task_json):
            backup_config = json.loads(public.ReadFile(self.bakcup_task_json))

        local_timestamp = int(time.time())
        backup_timestamp = local_timestamp
        get_time = local_timestamp

        # get_time=1744611093
        print(get_time)

        backup_now = True

        backup_conf = {
            'backup_name': "migrate_backup" + str(get_time),
            'timestamp': get_time,
            'create_time': datetime.datetime.fromtimestamp(int(local_timestamp)).strftime('%Y-%m-%d %H:%M:%S'),
            'backup_time': datetime.datetime.fromtimestamp(int(backup_timestamp)).strftime('%Y-%m-%d %H:%M:%S'),
            'storage_type': "local",
            'auto_exit': 0,
            'backup_status': 0,
            'restore_status': 0,
            'backup_path': self.base_path + "/" + str(get_time) + "_backup",
            'backup_file': "",
            'backup_file_sha256': "",
            'backup_file_size': "",
            'backup_count': {
                'success': None,
                'failed': None
            },
            'total_time': None,
            'done_time': None,
        }

        backup_config.append(backup_conf)
        public.WriteFile(self.bakcup_task_json, json.dumps(backup_config))

        if backup_now:
            print(public.lang("[*] Executing backup command..."))
            public.ExecShell(
                "nohup btpython /www/server/panel/mod/project/backup_restore/backup_manager.py backup_data {} > /dev/null 2>&1 &".format(
                    int(get_time)
                )
            )
        try:
            public.WriteFile(self.migrate_backup_pl_file, str(get_time))
            print(public.lang("[+] Backup task added successfully"))

            # 等待备份完成，最多等待21600秒（6小时）
            timeout = 21600
            start_time = time.time()
            print(public.lang("[*] Waiting for backup task to complete..."))
            from mod.project.backup_restore.config_manager import ConfigManager

            while time.time() - start_time < timeout:
                time.sleep(1)
                print(get_time)
                sync_backup_config = ConfigManager().get_backup_conf(str(get_time))
                print(sync_backup_config)
                if sync_backup_config['backup_status'] == 2:
                    backup_file = sync_backup_config['backup_file']
                    if os.path.exists(backup_file):
                        # 检查文件是否已经完成写入（检查文件大小是否稳定）
                        last_size = 0
                        stable_count = 0
                        for _ in range(3):  # 检查3次，确保文件大小稳定
                            current_size = os.path.getsize(backup_file)
                            if current_size == last_size:
                                stable_count += 1
                            else:
                                stable_count = 0
                            last_size = current_size
                            time.sleep(2)

                        if stable_count >= 2:  # 连续2次大小相同，认为文件写入完成
                            # 写入成功标记，包含备份文件路径
                            public.WriteFile(self.migrate_backup_success_file, backup_file)
                            print(public.lang("[+] Backup task completed: {}").format(backup_file))
                            return backup_file

                    # 检查备份任务是否还在进行
                    if not os.path.exists(self.backup_pl_file) and not os.path.exists(backup_file):
                        # 备份过程已结束但未生成备份文件，可能失败
                        error_msg = public.lang("Backup task failed, backup file not generated")
                        print(f"[!] {error_msg}")
                        return None
                    time.sleep(2)

                    # 超时处理
                    if os.path.exists(backup_file):
                        # 虽然超时，但文件存在，可以继续
                        public.WriteFile(self.migrate_backup_success_file, backup_file)
                        print(
                            public.lang("[+] Backup task completed (file detected after timeout): {}").format(backup_file))
                        return backup_file
                    else:
                        print(public.lang("[!] Backup task timed out and did not complete within the specified time"))
                        return None
        except Exception as e:
            import traceback
            public.print_log(traceback.format_exc())
            print("[!] An error occurred while adding backup task: {}".format(e))
            return None


def parse_arguments():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(description='connect ssh, to restore')

    parser.add_argument('-H', '--host', required=False, help='ip')
    parser.add_argument('-P', '--port', type=int, default=22, help='ssh port，default 22')
    parser.add_argument('-u', '--username', default='root', help='ssh user，defualt root')
    parser.add_argument('-p', '--password', help='pwd, (or use key)')
    parser.add_argument('-k', '--key-file', help='sshkey')
    parser.add_argument('-b', '--backup-file', help='Local backup file path')
    parser.add_argument('--panel-port', type=int, default=7800, help='aapanel port, default 7800')
    parser.add_argument('-r', '--max-retries', type=int, default=3, help='retry times, default 3')
    parser.add_argument('-i', '--retry-interval', type=int, default=5, help='Retry interval seconds, default 5 seconds')
    parser.add_argument('--task-id', help='Migration task ID for tracking progress')
    parser.add_argument(
        '--action', choices=['verify', 'install', 'upload', 'restore', 'migrate', 'all', 'status'],
        default='all',
        help='verify=Verifying SSH Connections, install=intall panel, upload=upload, restore=restore, migrate=migrate, status=task status, all=all'
    )
    parser.add_argument('--task-name', default='Migration Tasks', help='task name')

    args = parser.parse_args()

    # 对于非status操作，验证必要参数
    if args.action != 'status' and args.host is None:
        parser.error('Remote server IP address must be provided(-H/--host)')

    # 验证密码和密钥文件至少提供一个，除非是status操作
    if args.action != 'status' and not args.password and not args.key_file:
        parser.error('SSH password or key file path must be provided')

    return args


if __name__ == "__main__":
    args = parse_arguments()

    # 获取任务状态
    if args.action == 'status':
        result = get_migration_status(args.task_id)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        sys.exit(0)

    # 检查是否有正在运行的任务
    if args.action == 'migrate' and not args.task_id:
        # 创建新的迁移任务
        task_result = create_migration_task(
            task_name=args.task_name,
            host=args.host,
            port=args.port,
            username=args.username,
            password=args.password,
            key_file=args.key_file,
            backup_file=args.backup_file
        )

        if task_result.get("status", False):
            args.task_id = task_result.get("task_id")
            print(f"[+] Migration task created successfully，Task ID: {args.task_id}")
        else:
            print(json.dumps(task_result, ensure_ascii=False, indent=2))
            sys.exit(1)

    manager = BtInstallManager(
        host=args.host,
        port=args.port,
        username=args.username,
        password=args.password,
        key_file=args.key_file,
        backup_file=args.backup_file,
        panel_port=args.panel_port,
        max_retries=args.max_retries,
        retry_interval=args.retry_interval,
        task_id=args.task_id
    )

    # 根据指定的操作执行相应的功能
    if args.action == 'verify':
        result = manager.verify_ssh_connection()
        print(json.dumps(result, ensure_ascii=False, indent=2))
    elif args.action == 'install':
        result = manager.install_panel()
        print(json.dumps(result, ensure_ascii=False, indent=2))
    elif args.action == 'upload':
        result = manager.upload_backup()
        print(json.dumps(result, ensure_ascii=False, indent=2))
    elif args.action == 'migrate':
        if not args.task_id:
            print(json.dumps({"status": False, "msg": "The task_id parameter is required to perform the migration task"}, ensure_ascii=False, indent=2))
        else:
            result = manager.migrate(args.task_id)
            print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        result = manager.run()
        print(json.dumps(result, ensure_ascii=False, indent=2))
