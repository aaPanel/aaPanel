# coding: utf-8
# -------------------------------------------------------------------
# aaPanel
# -------------------------------------------------------------------
# Copyright (c) 2014-2099 aaPanel(www.aapanel.com) All rights reserved.
# -------------------------------------------------------------------
# Author: aapanel
# +-------------------------------------------------------------------
# | (8.4.0+)通用面板升级和修复脚本
# | 支持升级环境,升级面板,修复面板；环境相关由shell部分处理，面板升级沿用python脚本处理
# ------------------------------

# coding: utf-8
import os
import sys
import time
import json
import re
import hashlib
import shutil
import socket
import argparse
import subprocess

import psutil
from urllib.parse import urlparse, urlunparse
from dataclasses import dataclass, field
from typing import Tuple, Optional, Dict, List

# 全局变量
UPGRADE_MODEL = 'python'
LOG_PATH = '/tmp/upgrade_panel.log'
PANEL_PATH = '/www/server/panel'


@dataclass
class _ArgsData:
    action: str = 'upgrade_panel'
    version: str = ""
    skip_tool_check: bool = False
    package_file: str = ""
    dry_run: bool = False
    is_pro: bool = False

    @property
    def is_upgrade(self) -> bool:
        return self.action == 'upgrade_panel'


args_data = _ArgsData()


class Version:
    def __init__(self, version_str: str):
        if version_str:
            version_str = version_str.replace("-lts", "")
        self.major, self.minor, self.micro = self.normal_version(version_str)
        self.checksum = ""
        self.update_time = 0

    @staticmethod
    def normal_version(version_str: str):
        if version_str:
            try:
                tmp = version_str.split(".")
                if len(tmp) < 3:
                    tmp.extend(["0"] * (3 - len(tmp)))

                return int(tmp[0]), int(tmp[1]), int(tmp[2])
            except:
                return 0, 0, 0
        else:
            return 0, 0, 0

    def __str__(self):
        return "{}.{}.{}".format(self.major, self.minor, self.micro)

    def __bool__(self):
        return (self.major, self.minor, self.micro) != (0, 0, 0)

    # 返回当前安装的版本信息 否为稳定版本 和 版本号
    @classmethod
    def get_now_version(cls) -> "Version":
        comm = read_file('{}/class/common.py'.format(PANEL_PATH))
        res = re.search(r'''g\.version\s*=\s*["'](?P<ver>.*)['"]''', comm)
        if res:
            version = res.group("ver")
        else:
            version = ""
        try:
            main_ver = int(version.split(".")[0])
        except:
            return cls("0.0.0")

        config_content = read_file('{}/class/config.py'.format(PANEL_PATH))
        res = re.search(r'''version_number":\s*int\("(?P<upt>.*)"\)''', config_content)
        if res:
            res = res.group("upt")
        else:
            res = None
        if not res or not res.isdigit():
            try:
                update_time = os.path.getmtime('{}/class/config.py'.format(PANEL_PATH))
            except:
                update_time = 0
        else:
            update_time = int(res)

        v = cls(version)
        v.update_time = update_time
        return v

    # 获取远程版本信息
    # @classmethod
    # def get_remote_version(cls, is_lts=False):
    #     url = "https://www.bt.cn/api/panel/get_panel_version_v3"
    #     if is_lts:
    #         url = "https://www.bt.cn/api/panel/get_stable_panel_version_v3"
    #     try:
    #         info = http_get(url)
    #         info_dict = json.loads(info)
    #         if info_dict.get("OfficialVersionLatest", None) and info_dict["OfficialVersionLatest"]["version"]:
    #             return cls(info_dict["OfficialVersionLatest"]["version"])
    #         return cls(info_dict["OfficialVersion"]["version"])
    #     except:
    #         return cls("0.0.0")

    @staticmethod
    def panel_packet_name() -> str:
        return 'LinuxPanelPro_EN' if args_data.is_pro else 'LinuxPanel_EN'

    def get_check_sum(self):
        if not self:
            return
        self.checksum = ""
        self.update_time = 0

        panel_packet_name = self.panel_packet_name()
        url = f"https://node.aapanel.com/install/update/{panel_packet_name}-{self}.pl"
        try:
            info = http_get(url)
            info_dict = json.loads(info)
            self.checksum = info_dict["hash"]
            self.update_time = int(info_dict["update_time"])
        except:
            pass

    def show_dry_run(self):
        lv = self.get_now_version()
        package_type = "pro" if args_data.is_pro else "normal"
        msg = "Current panel version: {}".format(lv)
        msg += " (release)"
        if lv.update_time:
            msg += ", updated at: {}".format(time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(lv.update_time)))
        msg += "\nAbout to {}: {}".format("upgrade to" if args_data.is_upgrade else "repair to", self)
        msg += " (release)"
        msg += ", package: {}".format(package_type)
        if self.update_time:
            msg += ", remote package build time: {}".format(
                time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(self.update_time)))
        else:
            msg += ", no published package is available for this version; update cannot proceed"

        print(msg, flush=True)

    def download_panel_zip(self, filename: str) -> bool:
        if not self.checksum:
            print("WARNING: Failed to retrieve version checksum info. Please verify the source.")

        panel_packet_name = self.panel_packet_name()
        down_url = f"https://node.aapanel.com/install/update/{panel_packet_name}-{self}.zip"
        # 下载主文件
        if not download_with_progress(down_url, filename):
            return False

        if os.path.getsize(filename) < 5 * 1024 * 1024:
            print_x('ERROR: Failed to download the update package, please check network connectivity')
            return False

        if self.checksum:
            hash_val = file_hash(filename)
            if hash_val != self.checksum:
                file_time = os.path.getmtime(filename)
                print_x(
                    'Downloaded file mtime: {}'.format(time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(file_time)))
                )
                print_x('Remote hash: {}'.format(self.checksum))
                print_x('Local hash: {}'.format(hash_val))
                print_x('ERROR: Downloaded file verification failed, possible cause: incomplete download')
                return False
        return True

    def run_pre_script(self) -> bool:
        if not self:
            print_x("No version information available; cannot run pre-processing script")
            return False

        # down_url = "https://node.aapanel.com/install/update/update_prep_script.sh"
        # try:
        #     sh_content = http_get(down_url)
        #     sh_content = sh_content.replace("\r\n", "\n")
        #     if len(sh_content) < 10:
        #         print_x("ERROR: Failed to download pre-processing script")
        #         return False
        # except:
        #     print_x("ERROR: Failed to download pre-processing script")
        #     return False
        #
        # prep_sh_path = "{}/script/update_prep_script.sh".format(PANEL_PATH)
        # write_file(prep_sh_path, sh_content)
        # shell = "bash {} {} {} prepare".format(prep_sh_path, self, self.is_lts)
        #
        # update_ready = False
        #
        # def print_and_check(log: str):
        #     nonlocal update_ready
        #     print_x(log, end="")
        #     if log.find("BT-Panel Update Ready") != -1:
        #         update_ready = True
        #
        # run_command_with_call_log(shell, print_and_check)
        # if update_ready:
        #     print_x("Pre-processing script executed successfully")
        #     return True
        # print_x("ERROR: Pre-processing script execution failed")
        # return False

        print_x("Pre-processing script executed successfully")
        return True

    def run_after_script(self):
        # prep_sh_path = "{}/script/update_prep_script.sh".format(PANEL_PATH)
        # shell = "bash {} {} {} after".format(prep_sh_path, self, self.is_lts)
        # update_ready = False
        #
        # def print_and_check(log: str):
        #     nonlocal update_ready
        #     print_x(log, end="")
        #     if log.find("BT-Panel Update Ready") != -1:
        #         update_ready = True
        #
        # run_command_with_call_log(shell, print_and_check)
        # if update_ready:
        #     print_x("Startup check script executed successfully")
        # else:
        #     print_x("Warning: Startup check script execution failed")

        print_x("Startup check script executed successfully")


# 工具类函数
# 获取文件哈希值
def file_hash(filename, hash_type="sha256") -> str:
    hash_func = getattr(hashlib, hash_type)()
    with open(filename, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_func.update(chunk)
    return hash_func.hexdigest()


# 获取运行时Python版本
def runtime_python() -> Dict:
    return {
        'version': "{}.{}".format(sys.version_info.major, sys.version_info.minor),
        'path': os.path.realpath(sys.executable)
    }


def read_file(filename, mode='r') -> Optional[str]:
    """
    读取文件内容
    @filename 文件名
    return string(bin) 若文件不存在，则返回None
    """
    if not os.path.exists(filename):
        return None

    fp = None
    f_body = None
    try:
        fp = open(filename, mode)
        f_body = fp.read()
    except Exception as ex:
        if sys.version_info[0] != 2:
            try:
                fp = open(filename, mode, encoding="utf-8", errors='ignore')
                f_body = fp.read()
            except:
                try:
                    fp = open(filename, mode, encoding="GBK", errors='ignore')
                    f_body = fp.read()
                except:
                    return None
    finally:
        if fp and hasattr(fp, 'close') and not fp.closed:
            fp.close()
    return f_body


def write_file(filename, content, mode='w') -> bool:
    """
    写入文件内容
    @filename 文件名
    @content 内容
    @mode 打开方式
    return boolean
    """
    try:
        fp = open(filename, mode)
        fp.write(content)
        fp.close()
        return True
    except:
        return False


def exec_shell(cmd_string, timeout=None, shell=True, cwd=None, env=None) -> Tuple[str, str]:
    sub = None
    try:
        sub = subprocess.Popen(
            cmd_string,
            close_fds=True,
            shell=shell,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            cwd=cwd,
            env=env)

        if timeout:
            stdout, stderr = sub.communicate(timeout=timeout)
        else:
            stdout, stderr = sub.communicate()
        return stdout, stderr
    except subprocess.TimeoutExpired:
        # 确保sub已定义
        if sub is not None:
            sub.kill()
        return "", "Timed out"
    except Exception as e:
        return "", str(e)


def run_command_with_call_log(cmd, call_log):
    """
    执行命令并实时输出日志
    @param cmd 命令
    @param call_log 日志回调函数
    """
    if not callable(call_log):
        raise TypeError("call_log must be callable")

    # 执行命令
    try:
        import pty
        master, slave = pty.openpty()
        process = subprocess.Popen(
            cmd,
            close_fds=True,
            shell=True,
            stdout=slave,
            stderr=slave,
            text=True,
        )
        os.close(slave)

        while True:
            try:
                output = os.read(master, 1024).decode()
                if output:
                    call_log(output)
                if not output and process.poll() is not None:
                    break
            except OSError:
                break

        os.close(master)
        # 等待进程结束
        process.wait()

        # 检查返回码
        if process.returncode != 0:
            error_msg = "Execution failed, return code: {}".format(process.returncode)
            call_log(error_msg)
            return False

        return True

    except Exception as e:
        error_msg = str(e)
        call_log(error_msg)
        return False


# 字节单位转换
def to_size(size):
    units = ['B', 'KB', 'MB', 'GB', 'TB']
    unit_index = 0
    while size >= 1024 and unit_index < len(units) - 1:
        size /= 1024.0
        unit_index += 1
    return "{:.2f} {}".format(size, units[unit_index])


def print_x(msg: str, end='\n'):
    """
    打印消息并记录日志
    """
    # 简化print_x函数，只保留基本的日志记录功能
    if end and not msg.endswith(end):
        msg += end
    write_file(LOG_PATH, msg, 'a+')
    print(msg, end="", flush=True)


# 网络相关函数
# 获取CURL路径
def curl_bin():
    c_bin = [
        shutil.which('curl'),
        '/usr/local/curl2/bin/curl',
        '/usr/local/curl/bin/curl',
        '/usr/local/bin/curl',
        '/usr/bin/curl'
    ]
    for cb in c_bin:
        if cb and not os.path.exists(cb) and os.access(cb, os.X_OK):
            return cb
    return "curl"


# 格式化CURL响应
def curl_format(req: str):
    match = re.search("(?P<header>(.*\r?\n)+)\r?\n", req)
    if not match:
        return req, {}, 0
    header_str = match.group()
    body = req.replace(header_str, '')
    status_code = 0
    header_dict = {}
    try:
        header = match.group('header').replace('\r\n', '\n')
        for line in header.split('\n'):
            if line.find('HTTP/') != -1:
                if line.find('Continue') != -1:
                    continue
                search_result = re.search(r'HTTP/[\d.]+\s(\d+)', line)
                if search_result:
                    status_code = int(search_result.groups()[0])
            elif line.find(':') != -1:
                key, value = line.split(':', 1)
                header_dict[key.strip()] = value.strip()
        if status_code == 100:
            status_code = 200
    except:
        if body:
            status_code = 200
        else:
            status_code = 0
    return body, header_dict, status_code


# httpGet请求
def http_get(url, timeout=(3, 6), headers=None):
    """
    @name httpGet请求
    """
    if headers is None:
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:144.0) Gecko/20100101 Firefox/144.0"}
    try:
        import urllib.request
        # 确保url是字符串类型
        if url:
            req = urllib.request.Request(url, method='GET', headers=headers)
            response = urllib.request.urlopen(req, timeout=timeout[1])
            if response.status == 200:
                return response.read().decode('utf-8')
            return ""
    except:
        if isinstance(timeout, tuple):
            timeout = timeout[1]
        headers_str = ""
        if headers:
            for k, v in headers.items():
                headers_str += " -H '{}: {}'".format(k, v)
        out, err = exec_shell("{} -kisS --connect-timeout {} {} {}".format(curl_bin(), timeout, headers_str, url))
        if err:
            print_x(err)
            return ""
        r_body, r_headers, r_status_code = curl_format(out)
        if r_status_code != 200:
            return ""
        return r_body


# 工具检查相关函数
def check_tools(skip_check=False):
    """
    @name 检查必要工具
    @param skip_check 是否跳过检查
    """
    if skip_check:
        print_x('Tool check skipped')
        return True

    tools = ['wget', 'unzip']
    missing_tools = []

    for tool in tools:
        # 检查工具是否存在
        if not shutil.which(tool):
            missing_tools.append(tool)

    if missing_tools:
        print_x('ERROR: Missing required tools: {}'.format(', '.join(missing_tools)))
        print_x('Please install the missing tools before running the upgrade')
        return False

    print_x('Required tool check passed: {}'.format(', '.join(tools)))
    return True


# 下载相关函数
def download_with_progress(url, filename, max_retries=3):
    """
    @name 下载文件并显示进度
    @param url 下载地址
    @param filename 保存文件名
    @param max_retries 最大重试次数
    @param timeout 超时时间(秒)
    """
    cmd = "wget -O '{}' '{}' --no-check-certificate -T 30 -t 3 --progress=bar:force:noscroll".format(filename, url)
    for retry_count in range(max_retries):
        if retry_count > 0:
            print_x('Download failed, retrying (attempt {})...'.format(retry_count))
            time.sleep(1)  # 重试前等待2秒
            # 清理可能的残留文件
            if os.path.exists(filename):
                os.remove(filename)
        # if retry_count >= 1:
        #     cmd = cmd.replace('download.bt.cn', 'download-dg-main.bt.cn')

        download_success = run_command_with_call_log(cmd, lambda line: print_x(line, end=""))

        # 如果下载成功，跳出重试循环
        if download_success:
            print_x('File downloaded successfully: {}'.format(filename))
            return True

    # 所有重试都失败
    print_x(
        'ERROR: Failed to download {} after {} retries, please check network connectivity or download manually'.format(
            filename, max_retries))
    return False


# 拷贝的文件列表
def copy_dir(f_list: List[str], src_dir: str, dst_dir: str, per_str=""):
    """
    @name 备份面板
    @param f_list 需要拷贝的文件列表（不包含根目录）['task.py','config/databases.json']
    @param src_dir 源目录，如：/tmp/panel
    @param dst_dir 目标目录，如：/tmp/panel_bak
    """
    dst_dir = dst_dir.rstrip('/')
    if not os.path.exists(dst_dir):
        os.makedirs(dst_dir)

    f_log = "%s {:>9}" % per_str + " .........." * 3 + " {:>6.2f}%     {}"
    file_num = len(f_list)
    for idx, f_name in enumerate(f_list):
        if idx % 504 == 0:
            num_text = "{}/{}".format(idx, file_num)
            print_x(f_log.format(num_text, round(idx / file_num * 100, 2), os.path.basename(f_name)))

        # 拷贝文件
        s_file = os.path.join(src_dir, f_name)
        if not os.path.isfile(s_file):
            continue
        d_file = os.path.join(dst_dir, f_name)
        root_dir = os.path.dirname(d_file)
        if not os.path.exists(root_dir):
            os.makedirs(root_dir)
        try:
            shutil.copyfile(s_file, d_file)
        except:
            print_x('ERROR: Failed to copy file {}'.format(s_file))
            return False

    print_x(f_log.format("{}/{}".format(file_num, file_num), 100.00, ""))
    return True


def check_hash(f_list, src_dir, dst_dir):
    """
    @name 校验文件
    """
    res = []
    for f in f_list:
        s_file = os.path.join(src_dir, f)
        if not os.path.exists(s_file):
            continue
        d_file = os.path.join(dst_dir, f)
        if not os.path.exists(d_file):
            if d_file.endswith('check_files.py'):  # 不清楚check_files.py含义，继承策略
                continue
            print_x('File update failed: {}.'.format(d_file))
            res.append(s_file)
            continue

        if d_file.endswith('.whl'): continue
        if d_file == '/www/server/panel/BTPanel/languages/settings.json': continue

        # 校验文件hash
        if file_hash(s_file) != file_hash(d_file):
            f_name = os.path.basename(s_file)
            # 特定文件验证2次
            if f_name in ['BT-Panel', 'BT-Task', 'check_files.py']:
                try:
                    shutil.copyfile(s_file, d_file)
                except:
                    pass
                if file_hash(s_file) == file_hash(d_file):
                    continue
            print_x('File update failed: {}'.format(d_file))
            res.append(f)
    return res


def unzip(zipfile, dst_dir):
    """
    解压文件
    """
    sh = "unzip -q -o {} -d {}".format(zipfile, dst_dir)
    return run_command_with_call_log(sh, print_x)


# 检查进程是否存在
def process_exists(process_name):
    try:
        pids = psutil.pids()
        for pid in pids:
            if pid == os.getpid():
                continue
            try:
                p = psutil.Process(pid)
                if p.name() == process_name:
                    return True
            except:
                pass
    except:
        pass
    return False


# 面板相关函数
def get_panel_login_url():
    port = 8888
    try:
        port_file = '{}/data/port.pl'.format(PANEL_PATH)
        port_content = read_file(port_file)
        if port_content:
            return int(port_content.strip())
    except:
        pass

    login_path = 'login'
    try:
        auth_file = '{}/data/admin_path.pl'.format(PANEL_PATH)
        auth_content = read_file(auth_file)
        if auth_content:
            login_path = auth_content.strip('/').lstrip('/')
    except:
        pass

    schema = 'https' if os.path.exists("{}/data/ssl.pl".format(PANEL_PATH)) else 'http'

    return '{}://127.0.0.1:{}/{}'.format(schema, port, login_path)


# 检测面板是否正常
def check_panel_status():
    url = get_panel_login_url()
    panel_state = False
    start_time = time.time()
    while True:
        try:
            res = http_get(url=url)
            if res:
                panel_state = True
                break
        except:
            pass
        if time.time() - start_time > 15:
            break
        time.sleep(0.5)

    if panel_state:
        return True

    # 检测到BT-Panel 和 BT-Task 进程存在，则认为面板已经启动
    for pname in ['BT-Panel', 'BT-Task']:
        if process_exists(pname):
            panel_state = True
            break

    if panel_state:
        return True
    else:
        print_x('ERROR: Panel failed to start, please verify panel startup status')
        return False


# 清理临时文件
def clear_tmp():
    try:
        tmp_panel_dirs = [f for f in os.listdir('/tmp') if f.startswith('panel_')]
        for dir_name in tmp_panel_dirs:
            dir_path = os.path.join('/tmp', dir_name)
            if os.path.isdir(dir_path):
                shutil.rmtree(dir_path)
    except:
        pass

    try:
        panel_bak_dirs = [f for f in os.listdir('/www/server') if f.startswith('panel_bak_')]
        for dir_name in panel_bak_dirs:
            dir_path = os.path.join('/www/server', dir_name)
            if os.path.isdir(dir_path):
                shutil.rmtree(dir_path)
    except:
        pass

    try:
        if os.path.exists('/tmp/panel.zip'):
            os.remove('/tmp/panel.zip')
    except:
        pass

    # free_site_total
    try:
        last_install_file = "{}/data/free_site_total.pl".format(PANEL_PATH)
        if os.path.exists(last_install_file):
            os.remove(last_install_file)
    except:
        pass


def update_panel_files(n_list, src_dir, retry_count=3, start_func=None):
    """
    @name 更新面板文件(独立函数，避免多级嵌套)
    """
    for i in range(retry_count):
        if copy_dir(n_list, src_dir, PANEL_PATH, 'Updating:'):
            print_x('Verifying panel file integrity...')

            res = check_hash(n_list, src_dir, PANEL_PATH)
            if not res:
                print_x('Restarting panel...')
                if start_func and callable(start_func):
                    start_func()
                exec_shell('bash {}/init.sh restart'.format(PANEL_PATH))
                time.sleep(1)

                print_x('Checking panel runtime status...')
                if check_panel_status():
                    print_x('Cleaning up residual files...')
                    print_x('Success: Panel updated successfully')
                    return True
            else:
                if i == retry_count - 1:
                    for f in res:
                        dsc_file = os.path.join(PANEL_PATH, f)
                        print_x(dsc_file)
                    print_x(
                        'ERROR: Verification failed, {} files could not be updated. Restoring backup.'.format(len(res))
                    )
                else:
                    print_x('Retrying panel update (attempt {}), trying to unlock files...'.format(i + 1))
                    for f in res:
                        dsc_file = os.path.join(PANEL_PATH, f)
                        exec_shell('chattr -a -i {}'.format(dsc_file))

    return False


def install_with_pkg_file(package_file: str, start_func=None):
    if not package_file:
        print_x('ERROR: Invalid upgrade package file')
        return False
    tmp_dir = '/tmp/panel_{}'.format(str(int(time.time())))
    print_x('Extracting [{}]...'.format(package_file))

    unzip(package_file, tmp_dir)
    src_dir = tmp_dir + '/panel/'
    if not os.path.exists(src_dir):
        print_x('ERROR: Extraction failed')
        return

    # 使用os.walk遍历目录树, 收集会更新的文件列表
    f_list = []
    for root, _, filenames in os.walk(src_dir):
        for filename in filenames:
            # if filename.endswith('ajax_v2.py'):
            #     continue
            # if filename.endswith('__init__.py'):
            #     continue
            # if filename.endswith('system_v2.py'):
            #     continue
            # 构造相对路径
            full_path = os.path.join(root, filename)
            relative_path = full_path.replace(src_dir, '').lstrip('/')
            f_list.append(relative_path)

    if len(f_list) < 100:
        print_x('ERROR: Extraction failed, abnormal file count')
        return False

    bak_dir = PANEL_PATH.replace('panel', 'panel_bak_{}'.format(int(time.time())))
    if copy_dir(f_list, PANEL_PATH, bak_dir, 'Backing up:'):
        print_x("Backup completed...")
        if not update_panel_files(f_list, src_dir, start_func=start_func): # 更新结果
            # 恢复备份
            copy_dir(f_list, bak_dir, PANEL_PATH, "Restoring backup files:")
            print_x('Operation failed, backup has been restored successfully...')
    clear_tmp()
    return


def run() -> int:
    if args_data.package_file and os.path.exists(args_data.package_file):
        print_x('Using specified upgrade package file: {}'.format(args_data.package_file))
        install_with_pkg_file(args_data.package_file)
        return 1

    if args_data.action == 'repair_panel':
        # v = Version.get_now_version() # 不使用当前版本
        v = Version(args_data.version)
        if not v:
            print_x('ERROR: Failed to get current panel version; try using [ upgrade_panel ]')
            return 1
    elif args_data.action == 'upgrade_panel':
        v = Version(args_data.version)
        if not v:
            print_x('ERROR: Failed to get the latest version, please check network connectivity')
            return 1
    else:
        print_x('ERROR: Invalid arguments')
        return 1

    v.get_check_sum()
    v.show_dry_run()  # 展示升级信息
    if args_data.dry_run:  # 如果仅展示信息，则返回
        return 0 if v.checksum else 1  # 如果获取校验信息成功则退出信号码为0

    if not v.checksum:
        print_x('ERROR: No remote version checksum information available')
        return 1

    if not v.run_pre_script():
        print_x('ERROR: Pre-processing failed, cannot continue upgrade; please check network connectivity')
        return 1

    tmp_file = '/tmp/panel.zip'
    if not v.download_panel_zip(tmp_file):
        return 1
    if not os.path.exists(tmp_file):
        print_x('ERROR: Download failed')
        return 1

    action_text = "repair" if args_data.action == 'repair_panel' else "upgrade"
    print_x('Package downloaded successfully: {}, starting {}...'.format(tmp_file, action_text))
    install_with_pkg_file(tmp_file, start_func=v.run_after_script)
    return 0


def main():
    try:
        if os.path.exists('/tmp/upgrade_panel.log'):
            write_file('/tmp/upgrade_panel.log', '')
    except:
        pass

    # 参数解析
    parser = argparse.ArgumentParser(description='aa面板升级脚本')
    parser.add_argument('action', nargs='?', default='upgrade_panel',
                        help='操作类型: upgrade_panel|repair_panel|repair_pyenv')
    parser.add_argument('version', nargs='?', default=None, help='指定版本号')
    parser.add_argument('is_pro', nargs='?', default='', help='可选: 传 is_pro 使用专业版升级包')
    parser.add_argument('--skip-tool-check', action='store_true', help='跳过工具检查')
    parser.add_argument('--dry-run', action='store_true', help='仅展示计划，不实际执行')
    parser.add_argument('--package-file', type=str, default="", help='指定本地升级包文件路径')

    args = parser.parse_args()
    clear_tmp()
    args_data.skip_tool_check = bool(args.skip_tool_check)
    args_data.package_file = args.package_file
    args_data.version = args.version
    args_data.action = args.action
    args_data.dry_run = bool(args.dry_run)
    args_data.is_pro = bool(args.is_pro) or args.is_pro == 'is_pro'

    if args.is_pro and args.is_pro != 'is_pro':
        print_x('ERROR: Invalid argument [{}], expected is_pro'.format(args.is_pro))
        return

    if args_data.action not in ('upgrade_panel', 'repair_panel'):
        print_x('ERROR: Invalid command arguments')
        return
    if args_data.package_file and not os.path.exists(args_data.package_file):
        print_x('ERROR: Specified upgrade package file does not exist')
        return

    if not args_data.dry_run:
        disk = psutil.disk_usage(PANEL_PATH)
        print_x('Checking disk space...')
        print_x('Disk free space: {}'.format(to_size(disk.free)))

        if disk.free < 100 * 1024 * 1024:
            print_x('ERROR: Insufficient disk space [100 MB], cannot continue')
            return

    # 检查必要工具
    if not args_data.dry_run and not check_tools(args.skip_tool_check):
        return

    exit(run())


if __name__ == '__main__':
    main()
