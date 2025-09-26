# coding: utf-8
# -------------------------------------------------------------------
# aaPanel
# -------------------------------------------------------------------
# Copyright (c) 2014-2099 aaPanel(www.aapanel.com) All rights reserved.
# -------------------------------------------------------------------
# Author: aapanel
# -------------------------------------------------------------------

# ------------------------------
# Adminer Manager
# ------------------------------

import hashlib
import os
import re
import time
from typing import Tuple

import public
from BTPanel import cache
from panel_plugin_v2 import panelPlugin
from public.exceptions import HintException
from .config import *

www_server = public.get_setup_path()


def get_global_php_versions() -> list:
    from panel_site_v2 import panelSite
    res = panelSite().GetPHPVersion(None, False)
    return [x.get("version", "00") for x in res] if res else []


def find_cgi(file_path: str) -> str:
    try:
        if os.path.exists(file_path):
            content = public.readFile(file_path)
            if content:
                m = re.search(r"php-cgi-(\d+)", content)
                if m:  # ng, ap
                    return f"{m.group(1)[0]}{m.group(1)[1]}"
                ols = re.search(r"lsphp(\d+)", content)
                if ols:  # ols
                    return f"{ols.group(1)[0]}{ols.group(1)[1]}"
    except Exception as e:
        public.print_log('Get Adminer PHP Version Error {}'.format(e))
        pass
    return ""


class AdminerManager:
    INFO_CACHE_KEY = "adminer_port_path"

    @property
    def get_support_versions(self) -> list:
        """支持的版本列表"""
        return list(VER_SHA_MAP.keys())

    @property
    def adminer_dir(self) -> str:
        """目录, 不是绝对路径"""
        dir_path = ""
        if os.path.exists(DEFAULT_DIR):
            for dir_name in os.listdir(DEFAULT_DIR):
                if os.path.isdir(os.path.join(DEFAULT_DIR, dir_name)) and dir_name.startswith("adminer_"):
                    dir_path = dir_name
                    break
        if not dir_path:
            return ""
        return dir_path

    @property
    def adminer_port(self) -> int:
        port = DEFAULT_PORT
        try:
            p = public.readFile(PORT_PL)
            if p and p.strip().isdigit():
                port = int(p.strip())
        except Exception as e:
            public.print_log('Get Adminer PORT PL Error {}'.format(e))

        return int(port)

    @property
    def adminer_dir_port(self) -> Tuple[str, int]:
        c = cache.get(self.INFO_CACHE_KEY)
        if c:
            return c
        path = self.adminer_dir
        port = self.adminer_port
        if not path or not port:
            raise HintException(
                "Adminer is not installed, please go to the [Database] page to install it!"
            )
        info = (path, port)
        cache.set(self.INFO_CACHE_KEY, list(info), 10)
        return info

    @property
    def adminer_version(self) -> str:
        """版本号"""
        try:
            d, p = self.adminer_dir_port
        except HintException:
            return ""
        if not d or not p:
            return ""
        version = DEFAULT_VER
        try:
            if os.path.exists(VERSION_PL):
                with open(VERSION_PL, "r") as f:
                    version = f.read().strip()
        except Exception as e:
            public.print_log('Get Adminer Version Error {}'.format(e))

        return version

    @property
    def adminer_php_version(self) -> str:
        """
        获取adminer使用的PHP版本, 并尝试修复自身
        :return: final_ver = "00" | "74" | "80" | "81" | "82" | "83"...
        "00" 表示没php环境
        """

        def _alive_php(php_vers: list) -> str:
            for v in php_vers:
                if v != "00" and os.path.exists(f"{www_server}/php/{v}/bin/php"):
                    return v
            return "00"

        php_versions = get_global_php_versions()
        if not php_versions:  # 没可用的php版本
            return "00"

        web_server = public.GetWebServer()
        if web_server == "nginx":
            # Nginx 从 enable-php.conf 中找
            enable_cfg = f"{www_server}/nginx/conf/enable-php.conf"

            if os.path.exists(enable_cfg):
                final_ver = find_cgi(enable_cfg)
                if final_ver not in php_versions:
                    # enable-php.conf 里有版本, 但版本不可用时, 进行替换
                    final_ver = _alive_php(php_versions)
                    php_ver_cgi = f"{www_server}/nginx/conf/enable-php-{final_ver}.conf"
                    public.writeFile(enable_cfg, public.readFile(php_ver_cgi))

            else:
                # enable-php.conf 不存在时, 进行覆盖
                final_ver = _alive_php(php_versions)
                php_ver_cgi = f"{www_server}/nginx/conf/enable-php-{final_ver}.conf"
                public.writeFile(enable_cfg, public.readFile(php_ver_cgi))


        else:  # Apache 和 OLS 从各自配置文件中找
            conf = WebConfig.get(web_server)
            if conf and os.path.exists(conf):
                final_ver = find_cgi(conf)
                if final_ver not in php_versions:
                    # 配置里有版本, 但版本不可用时, 仅返回版本号
                    final_ver = _alive_php(php_versions)
            else:
                final_ver = _alive_php(php_versions)

        # 兜底
        if final_ver == "00" or final_ver not in php_versions:
            final_ver = _alive_php(php_versions)
        return final_ver

    @staticmethod
    def require_env(func):
        """环境wrapper"""

        def wrapper(*args, **kwargs):
            # has web server
            if not public.GetWebServer() or not panelPlugin().check_dependent("nginx|apache|openlitespeed"):
                raise HintException("Web service is not installed, please install web service first!")
            # has php version
            for ver in public.get_php_versions():
                if os.path.exists(f"{www_server}/php/{ver}/bin/php"):
                    return func(*args, **kwargs)
            raise HintException("PHP environment is not installed, please install PHP first!")

        return wrapper

    @staticmethod
    def download_official_file(ver: str, dst: str) -> None | str:
        """下载源码"""
        ver_sha256 = VER_SHA_MAP.get(ver, "")
        if not ver_sha256:
            raise Exception(f"Version {ver} not support or wrong, please try again!")

        tmp_dir = "/tmp/adminer_tmp"
        if os.path.exists(tmp_dir):
            public.ExecShell(f"rm -rf {tmp_dir}")
        os.makedirs(tmp_dir, exist_ok=True)
        download_file = f"adminer-{ver}.zip"
        tmp_zip_path = f"{tmp_dir}/{download_file}"
        try:
            download_url = f"{public.get_url()}/src/{download_file}"
            public.downloadFile(download_url, tmp_zip_path)

            if not os.path.exists(tmp_zip_path):
                raise Exception(f"Download {download_file} File not exists, please try again!")

            with open(tmp_zip_path, "rb") as f:
                tmp_sha256 = hashlib.sha256(f.read()).hexdigest()
                public.print_log(f"tmp_sha256= {tmp_sha256}")
            if ver_sha256 != tmp_sha256:
                raise Exception("Downlaod File sha256 check failed, please try again!")

            if not os.path.exists(dst):
                os.makedirs(dst, 0o755, exist_ok=True)

            public.ExecShell(f"unzip -o {tmp_zip_path} -d {dst}")

            file_abs = os.path.join(dst, "index.php")
            if not os.path.exists(file_abs):
                raise Exception("Download official file file failed, please try again!")
            return file_abs
        except Exception as e:
            public.print_log('Download Adminer Error {}'.format(e))
            raise Exception(e)
        finally:
            if os.path.exists(tmp_dir):
                public.ExecShell(f"rm -rf {tmp_dir}")

    @staticmethod
    def generate_conf(web_server: str, force: bool = False, php_ver: str = None) -> None:
        """
        动态生成配置, 覆盖
        依据当前的 port, php_ver, (root_dir强制默认)
        """
        web_conf = WebConfig.get(web_server)
        if not web_conf:
            raise HintException("Web service not support! WEB CONF MAP not found!")

        if public.get_multi_webservice_status():  # 当前是否开启多服务
            web_confs = [web_conf] if web_server == "nginx" else [f"{web_conf}.bak"]
            if web_server != "nginx":  # 非nginx的配置.conf都不应存在
                public.ExecShell(f"rm -f {WebConfig.apache} && rm -f {WebConfig.openlitespeed}")
        else:  # 非多服务
            for w in WebConfig.all_conf:  # .bak不应存在
                if os.path.exists(f"{w}.bak"):
                    public.ExecShell(f"rm -f {w}.bak")
            web_confs = [web_conf]

        # conf | conf.bak
        for conf in web_confs:
            if os.path.exists(conf) and force is False:
                return

            port = DEFAULT_PORT
            port_pl = public.readFile(PORT_PL)
            if port_pl and port_pl.strip().isdigit():
                port = int(port_pl.strip())

            if php_ver is None:
                # nginx 从 enable-php.conf 中找, 其他从自己的配置文件中找
                php_version = AdminerManager().adminer_php_version
            else:
                php_version = php_ver
                # 修改ng的 enable-php.conf
                enable_cfg = f"{www_server}/nginx/conf/enable-php.conf"
                php_ver_cgi = f"{www_server}/nginx/conf/enable-php-{php_version}.conf"
                public.writeFile(enable_cfg, public.readFile(php_ver_cgi))

            if not php_version or php_version == "00":
                raise HintException("PHP environment is not installed, please install PHP first!")

            content = ""
            root_dir = DEFAULT_DIR
            # 模板动态生成配置
            try:
                if web_server == "nginx":
                    content = NG_CONF.format(port=port, root_dir=root_dir)

                elif web_server == "apache":
                    proxy_pass = f"proxy:{public.get_php_proxy(php_version, "apache")}"
                    content = APACHE_CONF.format(port=port, root_dir=root_dir, proxy_pass=proxy_pass)

                elif web_server == "openlitespeed":
                    content = OLS_CONF.format(port=port, root_dir=root_dir, php_version=php_version)

            except Exception as e:
                public.print_log('Generate Adminer Conf Error {}'.format(e))
                pass

            if content:
                public.writeFile(conf, content)

    @staticmethod
    def all_generate_conf(force: bool = False, php_ver: str = None) -> None:
        if php_ver is not None and php_ver not in get_global_php_versions():
            raise HintException(public.lang("PHP version does not install!"))

        for web in WebConfig.all_web:
            AdminerManager.generate_conf(web_server=web, force=force, php_ver=php_ver)

    @property
    def is_install(self) -> bool:
        """是否安装, 只检测入口文件"""
        adminer_dir = self.adminer_dir
        if not adminer_dir:
            return False
        if not os.path.exists(f"{DEFAULT_DIR}/{adminer_dir}/index.php"):
            return False
        mulit = public.get_multi_webservice_status()
        if mulit:
            if os.path.exists(NGX_CONF_PATH):
                return True
        else:
            conf = WebConfig.get(public.GetWebServer())
            if not conf or not os.path.exists(conf):
                return False
        return True

    def service_reload(self):
        public.serviceReload()
        cache.delete(self.INFO_CACHE_KEY)
        time.sleep(0.5)
