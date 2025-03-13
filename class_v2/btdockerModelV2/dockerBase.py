# coding: utf-8
# -------------------------------------------------------------------
# aaPanel
# -------------------------------------------------------------------
# Copyright (c) 2015-2099 aaPanel(www.aapanel.com) All rights reserved.
# -------------------------------------------------------------------
# Author: wzz <wzz@aapanel.com>
# -------------------------------------------------------------------

# ------------------------------
# Docker模型
# ------------------------------
import public, os
from btdockerModelV2 import dk_public as dp


class dockerBase(object):

    def __init__(self):
        # self._db_path = "/www/server/panel/data/db/docker.db"
        self._db_path = "/www/server/panel/data/docker.db"
        self._backup_log = '/tmp/backup.log'
        self._log_path = '/tmp/dockertmp.log'
        self._rCmd_log = '/tmp/dockerRun.log'
        self._url = "unix:///var/run/docker.sock"
        self.compose_path = "{}/data/compose".format(public.get_panel_path())
        self.aes_key = "btdockerModel_QWERAS"
        self.moinitor_lock = "/tmp/bt_docker_monitor.lock"

    def get_ws_log(self, get):
        """
        获取日志，websocket
        @param get:
        @return:
        """
        if not hasattr(get, "_ws"):
            return True

        import time
        sum = 0

        with open(get._log_path, "r") as file:
            position = file.tell()
            get._ws.send(public.lang("{}\r\n",get.wsLogTitle))

            while True:
                current_position = file.tell()
                line = file.readline()
                if current_position > position:
                    file.seek(position)
                    new_content = file.read(current_position - position)
                    if "nohup" not in new_content:
                        for i in new_content.split('\n'):
                            if i == "": continue
                            get._ws.send(i.strip("\n") + "\r\n")

                    position = current_position

                    if "bt_successful" in line:
                        get._ws.send(public.lang("successful\r\n"))
                        del get._ws
                        break
                    elif "bt_failed" in line:
                        get._ws.send(public.lang("failed\r\n"))
                        del get._ws
                        break

                    if sum > 0:
                        sum = 0
                else:
                    sum += 1

                    if sum >= 6000:
                        get._ws.send(public.lang("\r\nNo response for more than 10 minutes!\r\n"))
                        break

                time.sleep(0.1)

        return True

    #  命令行创建  拉取容器
    def run_cmd(self, get):
        """
        命令行创建运行容器(docker run / docker pull)，需要做危险命令校验，存在危险命令则不执行
        @param get:
        @return:
        """
        import re
        if not hasattr(get, 'cmd'):
            return public.return_message(-1, 0, public.lang("Please pass in cmd"))

        if "docker run" not in get.cmd and "docker pull" not in get.cmd:
            return public.return_message(-1, 0, public.lang("Only docker run or docker pull commands can be executed"))

        danger_cmd = ['rm', 'rmi', 'kill', 'stop', 'pause', 'unpause', 'restart', 'update', 'exec', 'init',
                      'shutdown', 'reboot', 'chmod', 'chown', 'dd', 'fdisk', 'killall', 'mkfs', 'mkswap', 'mount',
                      'swapoff', 'swapon', 'umount', 'userdel', 'usermod', 'passwd', 'groupadd', 'groupdel',
                      'groupmod', 'chpasswd', 'chage', 'usermod', 'useradd', 'userdel', 'pkill']

        danger_symbol = ['&', '&&', '||', '|', ';']

        for d in danger_cmd:
            if get.cmd.startswith(d) or re.search(r'\s{}\s'.format(d), get.cmd):
                return public.return_message(-1, 0, public.lang("Dangerous command exists: [ {}], execution is not allowed!", d))

        for d in danger_symbol:
            if d in get.cmd:
                return public.return_message(-1, 0, public.lang("Dangerous symbol exists: [ {}], execution is not allowed!", d))

        os.system("echo -n > {}".format(self._rCmd_log))
        os.system("nohup {} >> {} 2>&1 && echo 'bt_successful' >> {} || echo 'bt_failed' >> {} &".format(
            get.cmd,
            self._rCmd_log,
            self._rCmd_log,
            self._rCmd_log,
        ))
        return public.return_message(0, 0, public.lang("The command has been executed!"))
