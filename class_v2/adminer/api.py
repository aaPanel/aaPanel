# coding: utf-8
# -------------------------------------------------------------------
# aaPanel
# -------------------------------------------------------------------
# Copyright (c) 2014-2099 aaPanel(www.aapanel.com) All rights reserved.
# -------------------------------------------------------------------
# Author: aapanel
# -------------------------------------------------------------------

# ------------------------------
# Adminer Api
# ------------------------------
import os
import time

import public
from public.exceptions import HintException
from public.validate import Param
from .config import *
from .manager import AdminerManager


class AdminerApi(AdminerManager):
    def support_versions(self, get=None):
        """Adminer支持的版本列表"""
        return public.success_v2(self.get_support_versions)

    def uninstall(self, get=None):
        """卸载"""
        if not self.is_install:
            return public.success_v2(public.lang("Adminer is not installed!"))

        public.ExecShell(f"rm -rf {DEFAULT_DIR}/")

        public.ExecShell(f"rm -f {NGX_CONF_PATH}")
        public.ExecShell(f"rm -f {APC_CONF_PATH}")
        public.ExecShell(f"rm -f {OLS_CONF_PATH}")

        public.ExecShell(f"rm -f {NGX_CONF_PATH}.bak")
        public.ExecShell(f"rm -f {APC_CONF_PATH}.bak")
        public.ExecShell(f"rm -f {OLS_CONF_PATH}.bak")
        self.service_reload()
        return public.success_v2(public.lang("Uninstall Successfully!"))

    def get_status(self, get=None):
        """获取服务的综合状态信息"""
        if not self.is_install:
            return public.success_v2({
                "php_version": "",
                "install": 0,
                "version": "",
                "port": 0,
            })
        return public.success_v2({
            "php_version": self.adminer_php_version,
            "install": 1,
            "version": self.adminer_version,
            "port": self.adminer_port,
        })

    @AdminerManager.require_env
    def install(self, get):
        """安装"""
        try:
            get.validate([
                Param("version").Regexp(r"^\d+(?:\.\d+)+$").Require(),
            ], [
                public.validate.trim_filter(),
            ])
            version = str(get.version)
        except Exception as ex:
            public.print_log("error info: {}".format(ex))
            return public.fail_v2(str(ex))

        done = False
        # 清空目录, 清空配置 (即便开启多服务)
        self.uninstall()
        dst = f"{DEFAULT_DIR}/adminer_{public.GetRandomString(16)}"
        try:
            msg = ""
            count = 0
            while count <= 2:
                try:
                    file = self.download_official_file(ver=version, dst=dst)
                    if os.path.exists(file):
                        break
                except Exception as ex:
                    msg = ex
                    time.sleep(1)
                    count += 1
            if msg != "":
                raise HintException(msg or "Download Adminer failed, please try again!")

            public.ExecShell(f"chown -R root:root {DEFAULT_DIR}")
            public.ExecShell(f"chmod -R 755 {dst}")
            public.writeFile(VERSION_PL, version)
            public.writeFile(PORT_PL, str(DEFAULT_PORT))

            self.all_generate_conf(force=True)
            self.service_reload()
            done = True
            return public.success_v2(public.lang("Install Successfully!"))
        except Exception as e:
            import traceback
            public.print_log(traceback.format_exc())
            public.print_log('Download Adminer Error {}'.format(e))
            raise HintException(e)
        finally:
            if done is False:
                public.ExecShell(f"rm -rf {dst}")

    @AdminerManager.require_env
    def repair(self, get):
        """重新安装, 或重新安装指定版本"""
        try:
            get.validate([
                Param("version").Regexp(r"^\d+(?:\.\d+)+$").Require(),
            ], [
                public.validate.trim_filter(),
            ])
        except Exception as ex:
            public.print_log("error info: {}".format(ex))
            return public.fail_v2(str(ex))
        try:
            self.install(get)
            return public.success_v2(public.lang("Install Successfully!"))
        except Exception as ex:
            public.print_log("error info: {}".format(ex))
            return public.fail_v2(str(ex))

    @AdminerManager.require_env
    def switch_port(self, get):
        """更新端口"""
        try:
            get.validate([
                Param("port").Integer().Require(),
            ], [
                public.validate.trim_filter(),
            ])
        except Exception as ex:
            public.print_log("error info: {}".format(ex))
            return public.fail_v2(str(ex))
        if not self.is_install:
            return public.fail_v2(public.lang("Adminer is not installed!"))

        port = int(get.port)
        if port == self.adminer_port:
            return public.success_v2(public.lang("Set Adminer port successfully!"))
        if not public.checkPort(port):
            return public.fail_v2(public.lang(f"Port {port} is already in use or invalid!"))
        try:
            public.writeFile(PORT_PL, str(port))
            self.all_generate_conf(force=True)
            self.service_reload()
            return public.success_v2(public.lang("Set successfully!"))
        except Exception as e:
            public.print_log('Set Adminer Port Error {}'.format(e))
            raise HintException("Set failed!")

    @AdminerManager.require_env
    def switch_php(self, get):
        try:
            get.validate([
                Param("php_version").Regexp("\d+").Require(),
            ], [
                public.validate.trim_filter(),
            ])
            php_version = str(get.php_version).replace(".", "")
        except Exception as ex:
            public.print_log("error info: {}".format(ex))
            return public.fail_v2(str(ex))
        if not self.is_install:
            return public.fail_v2(public.lang("Adminer is not installed!"))

        if php_version == self.adminer_php_version:
            return public.success_v2(public.lang("Set successfully!"))

        try:
            self.all_generate_conf(force=True, php_ver=php_version)
            self.service_reload()
            return public.success_v2(public.lang("Set Adminer php version successfully!"))
        except HintException as e:
            raise e
        except Exception as ex:
            return public.fail_v2(f"Set Adminer PHP Version Error {ex}")
