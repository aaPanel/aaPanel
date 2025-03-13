# coding: utf-8
# -------------------------------------------------------------------
# aaPanel
# -------------------------------------------------------------------
# Copyright (c) 2015-2099 aaPanel(www.aapanel.com) All rights reserved.
# -------------------------------------------------------------------
# Author: lwh <lwh@aapanel.com>
# -------------------------------------------------------------------
import fnmatch
import os, sys, time
from _stat import S_ISREG, S_ISDIR, S_ISLNK

# ------------------------------
# Docker安全检测
# ------------------------------
BASE_PATH = "/www/server/panel"
os.chdir(BASE_PATH)
sys.path.insert(0, "class/")
import public, re
from btdockerModelV2.dockerBase import dockerBase
from public.validate import Param

def auto_progress(func):
    """
    @name 自动增长进度条（装饰器）
    @author lwh<2024-1-23>
    """
    def wrapper(self, *args, **kwargs):
        result = func(self, *args, **kwargs)
        self.progress_percent += self.scan_percent
        return result
    return wrapper


class main(dockerBase):
    progress_percent = 0  # 扫描进度条
    ids_percent = 0
    scan_percent = 0
    scan_score = 100  # 扫描分数
    progress_content = "Initializing scan..."  # 扫描内容
    sys_ver = ""  # 系统类型
    requirements_list = ["veinmind", "veinmind-common"]
    docker_obj = ""  # docker对象
    image_name = ""  # 镜像名称
    send_time = ""  # 记录发送时间
    start_time = ""  # 开始时间

    def short_string(self, text):
        """
        @name 缩短字符串为40个字符
        """
        if len(text) <= 40:
            return text
        else:
            return text[:37] + "..."

    def short_string1(self, text):
        """
        @name 缩短字符串中间部分保留前后
        """
        if len(text) <= 30:
            return text
        else:
            return text[:15] + "..." + text[-15:]

    def get_image_list(self, get):
        """
        @name 获取镜像id列表
        @author lwh<2024-1-23>
        @return
        """
        # public.print_log("Get the image id list")
        if not hasattr(get, "_ws"):
            return True
        from btdockerModelV2 import imageModel
        image_list = imageModel.main().image_list(get=public.dict_obj())['message']
        # public.print_log(image_list)
        get._ws.send(public.GetJson({"end": True, "image_list": image_list}))

    def send_image_ws(self, get, msg, detail="", repair="", status=1, end=False):
        """
        @name 发送ws信息
        @author lwh<2024-01-23>
        @param msg string 扫描内容
        @param status int 风险情况：1无风险，2告警，3危险
        @param repair string 修复方案
        @param end bool 是否结束
        """
        now_time = time.time()
        # 判断间隔时间是否小于100ms
        if now_time-self.send_time <= 0.1 and not end and status == 1:
            return
        self.send_time = now_time
        # 根据风险情况进行扣分
        if status == 2:
            score = 2
        elif status == 3:
            score = 5
        else:
            score = 0
        # msg：扫描内容，score：当前分数，type：类型docker/image
        get._ws.send(public.GetJson({"end": end, "image_name": self.image_name, "status": status, "detail": detail,
                                     "msg": msg, "repair": repair, "score": score, "type": "image"}))

    def send_docker_ws(self, get, msg, repair="", status=1, end=True):
        """
        @name 发送ws信息
        @author lwh<2024-01-23>
        @param msg string 扫描内容
        @param status int 风险情况：1无风险，2告警，3危险
        @param repair string 修复方案
        @param end bool 是否结束
        """
        # 根据风险情况进行扣分
        if status == 2:
            score = 2
        elif status == 3:
            score = 5
        else:
            score = 0
        # msg：扫描内容，progress：扫描进度，score：当前分数
        get._ws.send(public.GetJson({"end": end, "image_name": self.image_name, "status": status, "msg": msg, "repair": repair, "score": score, "type": "docker"}))

    def reduce_core(self, score):
        """
        @name 减少总分
        @author lwh<2024-01-23>
        @param score int 需要减少的分数
        @return self.scan_score int 所剩分数
        """
        self.scan_score -= score
        if self.scan_score < 0:
            return 0
        return self.scan_score

    def image_safe_scan(self, get):
        """
        @name 镜像安全扫描入口函数
        @author lwh@aapanel.com
        @time 2024-01-22
        @param _ws
        @return 返回服务器扫描项
        """
        public.set_module_logs('docker', 'image_safe_scan', 1)
        if not hasattr(get, "_ws"):
            return True
        if not hasattr(get, "image_id"):
            return True
        # 获取检测镜像
        image_id = get.image_id
        # 初始化时间
        self.send_time = time.time()

        # 初始化安装检测SDK
        try:
            from veinmind import docker
        except Exception as e:
            public.print_log("Importing veinmind failed:{}".format(e))
            # requirements_list = ["veinmind"]
            self.send_image_ws(get, msg=public.lang("The detection engine is being initialized. The first load may take a long time...."), status=1)
            shell_command = "btpip install --no-dependencies {}".format("veinmind")
            public.ExecShell(shell_command)
            sys_ver = public.get_os_version()
            if "Ubuntu" in sys_ver or "Debian" in sys_ver:
                public.WriteFile("/etc/apt/sources.list.d/libveinmind.list",
                                 "deb [trusted=yes] https://download.veinmind.tech/libveinmind/apt/ ./")
                self.send_image_ws(get, msg=public.lang("Apt-get is being updated. The first load may take a long time...."), status=1)
                public.ExecShell("apt-get update")
                time.sleep(1)
                self.send_image_ws(get, msg=public.lang("Detection engine being installed, first execution may take thousands of years..."), status=1)
                public.ExecShell("apt-get install -y libveinmind-dev")
                time.sleep(1)
            elif "CentOS" in sys_ver:
                public.WriteFile("/etc/yum.repos.d/libveinmind.repo", """[libveinmind]
name=libVeinMind SDK yum repository
baseurl=https://download.veinmind.tech/libveinmind/yum/
enabled=1
gpgcheck=0""")
                self.send_image_ws(get, msg=public.lang("The yum cache is being updated. The first load may take a long time...."), status=1)
                public.ExecShell("yum makecache")
                self.send_image_ws(get, msg=public.lang("Detection engine being installed, first execution may take thousands of years..."), status=1)
                public.ExecShell("yum install -y libveinmind-devel")
            else:
                self.send_image_ws(get, msg=public.lang("Unsupported system version {}",sys_ver), status=1)
                return public.returnMsg(False, public.lang("Unsupported system version {}\nCurrently only supports Debian, Ubuntu, Centos", sys_ver))
            self.send_image_ws(get, msg=public.lang("Checking libdl.so dependent libraries..."), status=1)
            result, err = public.ExecShell("whereis libdl.so")
            result = result.strip().split(" ")
           # public.print_log("The situation of libdl.so library:{}".format(result))
            if len(result) <= 1:
               # public.print_log("Missing libdl.so library")
                result, err = public.ExecShell("whereis libdl.so.2")
                result = result.strip().split(" ")
               # public.print_log("The situation of libdl.so.2 library:{}".format(result))
                if len(result) <= 1:
                    public.print_log("Missing libdl.so library，Requires libdl.so or libdl.so2 to be installed")
                    public.returnMsg(False, "Missing libdl.so library，Requires libdl.so or libdl.so2 to be installed")
                else:
                    # 建立libdl.so软链接至libdl.so.2
                    for lib in result[1:]:
                        ln_command = "ln -s {} {}".format(lib, lib[:-2])
                       # public.print_log("Soft link in progress：{}".format(ln_command))
                        public.ExecShell(ln_command)
            from veinmind import docker

        # 开始检测
        # 获取docker对象
        docker_obj = docker.Docker()
        # # 获取所有镜像id
        # ids = docker_obj.list_image_ids()
        # # 计算镜像进度占比
        # self.ids_percent = math.floor(100 / len(ids))
        # # 计算每个镜像扫描进度占比
        # self.scan_percent = math.floor(self.ids_percent / 3)
        # 开始镜像检测
        # for key, id in enumerate(ids):
        image = docker_obj.open_image_by_id(image_id=image_id)
        # 获取ref镜像名
        refs = image.reporefs()
        if len(refs) > 0:
            self.image_name = refs[0]
        else:
            self.image_name = image.id()
        public.print_log("Detecting:{}".format(self.image_name))
        self.send_image_ws(get, msg=public.lang("Scanning {} exception history command",self.image_name))
        self.scan_history(get, image)
        self.send_image_ws(get, msg=public.lang("Scanning {} sensitive information",self.image_name))
        self.scan_sensitive(get, image)
        self.send_image_ws(get, msg=public.lang("Scanning {} backdoor",self.image_name))
        self.scan_backdoor(get, image)
        self.send_image_ws(get, msg=public.lang("Scanning {} container escapes"))
        self.scan_escape(get, image)
        self.send_image_ws(get, msg=public.lang("{}Scan completed",self.image_name), end=True)

    def scan_history(self, get, image):
        """
        @name 异常历史命令
        @author lwh@aapanel.com
        @time 2024-01-22
        """
        instruct_set = (
            "FROM", "CMD", "RUN", "LABEL", "MAINTAINER", "EXPOSE", "ENV", "ADD", "COPY", "ENTRYPOINT", "VOLUME", "USER",
            "WORKDIR", "ARG", "ONBUILD", "STOPSIGNAL", "HEALTHCHECK", "SHELL")
        rules = {
            "rules": [{"description": "Miner Repo", "instruct": "RUN", "match": ".*(xmrig|ethminer|miner)\\.git.*"},
                      {"description": "Unsafe Path", "instruct": "ENV", "match": "PATH=.*(|:)(/tmp|/dev/shm)"}]}

        ocispec = image.ocispec_v1()
        if 'history' in ocispec.keys() and len(ocispec['history']) > 0:
            for history in ocispec['history']:
                if 'created_by' in history.keys():
                    created_by = history['created_by']
                    created_by_split = created_by.split("#(nop)")
                    if len(created_by_split) > 1:
                        command = "#(nop)".join(created_by_split[1:])
                        command = command.lstrip()
                        command_split = command.split()
                        if len(command_split) == 2:
                            instruct = command_split[0]
                            command_content = command_split[1]
                            for r in rules["rules"]:
                                if r["instruct"] == instruct:
                                    if re.match(r["match"], command_content):
                                        self.send_image_ws(get, msg=public.lang("Suspicious abnormal history command found"), detail=public.lang("It was found that the image has an abnormal historical command [{}], which may implant malware or code into the host system when the container is running, causing security risks.",self.short_string(command_content)), repair=public.lang("1.It is recommended to check whether the command is required for normal business<br/>2.It is recommended to choose official and reliable infrastructure to avoid unnecessary losses."))
                                        break
                        else:
                            instruct = command_split[0]
                            command_content = " ".join(command_split[1:])
                            for r in rules["rules"]:
                                if r["instruct"] == instruct:
                                    if re.match(r["match"], command_content):
                                        self.send_image_ws(get, msg=public.lang("Suspicious abnormal history command found"), detail=public.lang("It was found that the image has an abnormal historical command [{}], which may implant malware or code into the host system when the container is running, causing security risks.",self.short_string(command_content)), repair=public.lang("1.It is recommended to check whether the command is required for normal business<br/>2.It is recommended to choose official and reliable infrastructure to avoid unnecessary losses."))
                                        break
                    else:
                        command_split = created_by.split()
                        if command_split[0] in instruct_set:
                            for r in rules["rules"]:
                                if r["instruct"] == command_split[0]:
                                    if re.match(r["match"], " ".join(command_split[1:])):
                                        self.send_image_ws(get, msg=public.lang("Suspicious abnormal history command found"), detail=public.lang("It was found that the image has an abnormal historical command [{}], which may implant malware or code into the host system when the container is running, causing security risks.",self.short_string(" ".join(command_split[1:]))), repair=public.lang("1.It is recommended to check whether the command is required for normal business<br/>2.It is recommended to choose official and reliable infrastructure to avoid unnecessary losses."))
                                        break
                        else:
                            for r in rules["rules"]:
                                if r["instruct"] == "RUN":
                                    if re.match(r["match"], created_by):
                                        self.send_image_ws(get, msg=public.lang("Suspicious abnormal history command found"), detail=public.lang("It was found that the image has an abnormal historical command [{}], which may implant malware or code into the host system when the container is running, causing security risks.",self.short_string(created_by)), repair=public.lang("1.It is recommended to check whether the command is required for normal business<br/>2.It is recommended to choose official and reliable infrastructure to avoid unnecessary losses."))
                                        break

    def scan_sensitive(self, get, image):
        """
        @name 扫描镜像敏感数据
        @author lwh<2024-1-22>
        """
        # 敏感数据规则
        rules = {"whitelist": {
            "paths": ["/usr/**", "/lib/**", "/lib32/**", "/bin/**", "/sbin/**", "/var/lib/**", "/var/log/**",
                      "**/node_modules/**/*.md", "**/node_modules/**/test/**", "**/service/iam/examples_test.go",
                      "**/grafana/public/build/*.js"]}, "rules": [
            {"id": 1, "name": "gitlab_personal_access_token", "description": "GitLab Personal Access Token",
             "match": "glpat-[0-9a-zA-Z_\\-]{20}", "level": "high"},
            {"id": 2, "name": "AWS", "description": "AWS Access Token", "match": "AKIA[0-9A-Z]{16}", "level": "high"},
            {"id": 3, "name": "PKCS8 private key", "description": "PKCS8 private key",
             "match": "-----BEGIN PRIVATE KEY-----", "level": "high"},
            {"id": 4, "name": "RSA private key", "description": "RSA private key",
             "match": "-----BEGIN RSA PRIVATE KEY-----", "level": "high"},
            {"id": 5, "name": "SSH private key", "description": "SSH private key",
             "match": "-----BEGIN OPENSSH PRIVATE KEY-----", "level": "high"},
            {"id": 6, "name": "PGP private key", "description": "PGP private key",
             "match": "-----BEGIN PGP PRIVATE KEY BLOCK-----", "level": "high"},
            {"id": 7, "name": "Github Personal Access Token", "description": "Github Personal Access Token",
             "match": "ghp_[0-9a-zA-Z]{36}", "level": "high"},
            {"id": 8, "name": "Github OAuth Access Token", "description": "Github OAuth Access Token",
             "match": "gho_[0-9a-zA-Z]{36}", "level": "high"},
            {"id": 9, "name": "SSH (DSA) private key", "description": "SSH (DSA) private key",
             "match": "-----BEGIN DSA PRIVATE KEY-----", "level": "high"},
            {"id": 10, "name": "SSH (EC) private key", "description": "SSH (EC) private key",
             "match": "-----BEGIN EC PRIVATE KEY-----", "level": "high"},
            {"id": 11, "name": "Github App Token", "description": "Github App Token",
             "match": "(ghu|ghs)_[0-9a-zA-Z]{36}", "level": "high"},
            {"id": 12, "name": "Github Refresh Token", "description": "Github Refresh Token",
             "match": "ghr_[0-9a-zA-Z]{76}", "level": "high"},
            {"id": 13, "name": "Shopify shared secret", "description": "Shopify shared secret",
             "match": "shpss_[a-fA-F0-9]{32}", "level": "high"},
            {"id": 14, "name": "Shopify access token", "description": "Shopify access token",
             "match": "shpat_[a-fA-F0-9]{32}", "level": "high"},
            {"id": 15, "name": "Shopify custom app access token", "description": "Shopify custom app access token",
             "match": "shpca_[a-fA-F0-9]{32}", "level": "high"},
            {"id": 16, "name": "Shopify private app access token", "description": "Shopify private app access token",
             "match": "shppa_[a-fA-F0-9]{32}", "level": "high"},
            {"id": 17, "name": "Slack token", "description": "Slack token", "match": "xox[baprs]-([0-9a-zA-Z]{10,48})?",
             "level": "high"},
            {"id": 18, "name": "Stripe", "description": "Stripe", "match": "(?i)(sk|pk)_(test|live)_[0-9a-z]{10,32}",
             "level": "high"}, {"id": 19, "name": "PyPI upload token", "description": "PyPI upload token",
                                "match": "pypi-AgEIcHlwaS5vcmc[A-Za-z0-9-_]{50,1000}", "level": "high"},
            {"id": 20, "name": "Google (GCP) Service-account", "description": "Google (GCP) Service-account",
             "match": "\\\"type\\\": \\\"service_account\\\"", "level": "medium"},
            {"id": 21, "name": "Password in URL", "description": "Password in URL",
             "match": "[a-zA-Z]{3,10}:\\/\\/[^$][^:@\\/\\n]{3,20}:[^$][^:@\\n\\/]{3,40}@.{1,100}", "level": "high"},
            {"id": 22, "name": "Heroku API Key", "description": "Heroku API Key",
             "match": "(?i)(?:heroku)(?:[0-9a-z\\-_\\t .]{0,20})(?:[\\s|']|[\\s|\"]){0,3}(?:=|>|:=|\\|\\|:|<=|=>|:)(?:'|\\\"|\\s|=|\\x60){0,5}([0-9A-F]{8}-[0-9A-F]{4}-[0-9A-F]{4}-[0-9A-F]{4}-[0-9A-F]{12})(?:['|\\\"|\\n|\\r|\\s|\\x60]|$)",
             "level": "high"}, {"id": 23, "name": "Slack Webhook", "description": "Slack Webhook",
                                "match": "https://hooks.slack.com/services/T[a-zA-Z0-9_]{8}/B[a-zA-Z0-9_]{8,12}/[a-zA-Z0-9_]{24}",
                                "level": "medium"},
            {"id": 24, "name": "Twilio API Key", "description": "Twilio API Key", "match": "SK[0-9a-fA-F]{32}",
             "level": "high"}, {"id": 25, "name": "Age secret key", "description": "Age secret key",
                                "match": "AGE-SECRET-KEY-1[QPZRY9X8GF2TVDW0S3JN54KHCE6MUA7L]{58}", "level": "high"},
            {"id": 26, "name": "Facebook token", "description": "Facebook token",
             "match": "(?i)(facebook[a-z0-9_ .\\-,]{0,25})(=|>|:=|\\|\\|:|<=|=>|:).{0,5}['\\\"]([a-f0-9]{32})['\\\"]",
             "level": "high"}, {"id": 27, "name": "Twitter token", "description": "Twitter token",
                                "match": "(?i)(twitter[a-z0-9_ .\\-,]{0,25})(=|>|:=|\\|\\|:|<=|=>|:).{0,5}['\\\"]([a-f0-9]{35,44})['\\\"]",
                                "level": "high"},
            {"id": 28, "name": "Adobe Client ID (Oauth Web)", "description": "Adobe Client ID (Oauth Web)",
             "match": "(?i)(adobe[a-z0-9_ .\\-,]{0,25})(=|>|:=|\\|\\|:|<=|=>|:).{0,5}['\\\"]([a-f0-9]{32})['\\\"]",
             "level": "medium"}, {"id": 29, "name": "Adobe Client Secret", "description": "Adobe Client Secret",
                                  "match": "(p8e-)(?i)[a-z0-9]{32}", "level": "high"},
            {"id": 30, "name": "Alibaba AccessKey ID", "description": "Alibaba AccessKey ID",
             "match": "(LTAI5t)(?i)[a-z0-9]{18}", "level": "medium", "lock": True},
            {"id": 31, "name": "Alibaba Secret Key", "description": "Alibaba Secret Key",
             "match": "(?i)(alibaba[a-z0-9_ .\\-,]{0,25})(=|>|:=|\\|\\|:|<=|=>|:).{0,5}['\\\"]([a-z0-9]{30})['\\\"]",
             "level": "high"}, {"id": 32, "name": "Asana Client ID", "description": "Asana Client ID",
                                "match": "(?i)(asana[a-z0-9_ .\\-,]{0,25})(=|>|:=|\\|\\|:|<=|=>|:).{0,5}['\\\"]([0-9]{16})['\\\"]",
                                "level": "medium"},
            {"id": 33, "name": "Asana Client Secret", "description": "Asana Client Secret",
             "match": "(?i)(asana[a-z0-9_ .\\-,]{0,25})(=|>|:=|\\|\\|:|<=|=>|:).{0,5}['\\\"]([a-z0-9]{32})['\\\"]",
             "level": "high"}, {"id": 34, "name": "Atlassian API token", "description": "Atlassian API token",
                                "match": "(?i)(atlassian[a-z0-9_ .\\-,]{0,25})(=|>|:=|\\|\\|:|<=|=>|:).{0,5}['\\\"]([a-z0-9]{24})['\\\"]",
                                "level": "high"},
            {"id": 35, "name": "Bitbucket client ID", "description": "Bitbucket client ID",
             "match": "(?i)(bitbucket[a-z0-9_ .\\-,]{0,25})(=|>|:=|\\|\\|:|<=|=>|:).{0,5}['\\\"]([a-z0-9]{32})['\\\"]",
             "level": "medium"}, {"id": 36, "name": "Bitbucket client secret", "description": "Bitbucket client secret",
                                  "match": "(?i)(bitbucket[a-z0-9_ .\\-,]{0,25})(=|>|:=|\\|\\|:|<=|=>|:).{0,5}['\\\"]([a-z0-9_\\-]{64})['\\\"]",
                                  "level": "high"},
            {"id": 37, "name": "Beamer API token", "description": "Beamer API token",
             "match": "(?i)(beamer[a-z0-9_ .\\-,]{0,25})(=|>|:=|\\|\\|:|<=|=>|:).{0,5}['\\\"](b_[a-z0-9=_\\-]{44})['\\\"]",
             "level": "high"}, {"id": 38, "name": "Clojars API token", "description": "Clojars API token",
                                "match": "(CLOJARS_)(?i)[a-z0-9]{60}", "level": "high"},
            {"id": 39, "name": "Contentful delivery API token", "description": "Contentful delivery API token",
             "match": "(?i)(contentful[a-z0-9_ .\\-,]{0,25})(=|>|:=|\\|\\|:|<=|=>|:).{0,5}['\\\"]([a-z0-9\\-=_]{43})['\\\"]",
             "level": "high"},
            {"id": 40, "name": "Contentful preview API token", "description": "Contentful preview API token",
             "match": "(?i)(contentful[a-z0-9_ .\\-,]{0,25})(=|>|:=|\\|\\|:|<=|=>|:).{0,5}['\\\"]([a-z0-9\\-=_]{43})['\\\"]",
             "level": "high"}, {"id": 41, "name": "Databricks API token", "description": "Databricks API token",
                                "match": "dapi[a-h0-9]{32}", "level": "high"},
            {"id": 42, "name": "Discord API key", "description": "Discord API key",
             "match": "(?i)(discord[a-z0-9_ .\\-,]{0,25})(=|>|:=|\\|\\|:|<=|=>|:).{0,5}['\\\"]([a-h0-9]{64})['\\\"]",
             "level": "high"}, {"id": 43, "name": "Discord client ID", "description": "Discord client ID",
                                "match": "(?i)(discord[a-z0-9_ .\\-,]{0,25})(=|>|:=|\\|\\|:|<=|=>|:).{0,5}['\\\"]([0-9]{18})['\\\"]",
                                "level": "medium"},
            {"id": 44, "name": "Discord client secret", "description": "Discord client secret",
             "match": "(?i)(discord[a-z0-9_ .\\-,]{0,25})(=|>|:=|\\|\\|:|<=|=>|:).{0,5}['\\\"]([a-z0-9=_\\-]{32})['\\\"]",
             "level": "high"}, {"id": 45, "name": "Doppler API token", "description": "Doppler API token",
                                "match": "['\\\"](dp\\.pt\\.)(?i)[a-z0-9]{43}['\\\"]", "level": "high"},
            {"id": 46, "name": "Dropbox API secret/key", "description": "Dropbox API secret/key",
             "match": "(?i)(dropbox[a-z0-9_ .\\-,]{0,25})(=|>|:=|\\|\\|:|<=|=>|:).{0,5}['\\\"]([a-z0-9]{15})['\\\"]",
             "level": "high"},
            {"id": 47, "name": "Dropbox short lived API token", "description": "Dropbox short lived API token",
             "match": "(?i)(dropbox[a-z0-9_ .\\-,]{0,25})(=|>|:=|\\|\\|:|<=|=>|:).{0,5}['\\\"](sl\\.[a-z0-9\\-=_]{135})['\\\"]",
             "level": "high"},
            {"id": 48, "name": "Dropbox long lived API token", "description": "Dropbox long lived API token",
             "match": "(?i)(dropbox[a-z0-9_ .\\-,]{0,25})(=|>|:=|\\|\\|:|<=|=>|:).{0,5}['\\\"][a-z0-9]{11}(AAAAAAAAAA)[a-z0-9\\-_=]{43}['\\\"]",
             "level": "high"}, {"id": 49, "name": "Duffel API token", "description": "Duffel API token",
                                "match": "['\\\"]duffel_(test|live)_(?i)[a-z0-9_-]{43}['\\\"]", "level": "high"},
            {"id": 50, "name": "Dynatrace API token", "description": "Dynatrace API token",
             "match": "['\\\"]dt0c01\\.(?i)[a-z0-9]{24}\\.[a-z0-9]{64}['\\\"]", "level": "high"},
            {"id": 51, "name": "EasyPost API token", "description": "EasyPost API token",
             "match": "['\\\"]EZAK(?i)[a-z0-9]{54}['\\\"]", "level": "high"},
            {"id": 52, "name": "EasyPost test API token", "description": "EasyPost test API token",
             "match": "['\\\"]EZTK(?i)[a-z0-9]{54}['\\\"]", "level": "high"},
            {"id": 53, "name": "Fastly API token", "description": "Fastly API token",
             "match": "(?i)(fastly[a-z0-9_ .\\-,]{0,25})(=|>|:=|\\|\\|:|<=|=>|:).{0,5}['\\\"]([a-z0-9\\-=_]{32})['\\\"]",
             "level": "high"}, {"id": 54, "name": "Finicity client secret", "description": "Finicity client secret",
                                "match": "(?i)(finicity[a-z0-9_ .\\-,]{0,25})(=|>|:=|\\|\\|:|<=|=>|:).{0,5}['\\\"]([a-z0-9]{20})['\\\"]",
                                "level": "high"},
            {"id": 55, "name": "Finicity API token", "description": "Finicity API token",
             "match": "(?i)(finicity[a-z0-9_ .\\-,]{0,25})(=|>|:=|\\|\\|:|<=|=>|:).{0,5}['\\\"]([a-f0-9]{32})['\\\"]",
             "level": "high"}, {"id": 56, "name": "Flutterweave public key", "description": "Flutterweave public key",
                                "match": "(?i)FLWPUBK_TEST-[a-h0-9]{32}-X", "level": "medium"},
            {"id": 57, "name": "Flutterweave secret key", "description": "Flutterweave secret key",
             "match": "(?i)FLWSECK_TEST-[a-h0-9]{32}-X", "level": "high"},
            {"id": 58, "name": "Flutterweave encrypted key", "description": "Flutterweave encrypted key",
             "match": "FLWSECK_TEST[a-h0-9]{12}", "level": "high"},
            {"id": 59, "name": "Frame.io API token", "description": "Frame.io API token",
             "match": "fio-u-(?i)[a-z0-9-_=]{64}", "level": "high"},
            {"id": 60, "name": "GoCardless API token", "description": "GoCardless API token",
             "match": "['\\\"]live_(?i)[a-z0-9-_=]{40}['\\\"]", "level": "high"},
            {"id": 61, "name": "Grafana API token", "description": "Grafana API token",
             "match": "['\\\"]eyJrIjoi(?i)[a-z0-9-_=]{72,92}['\\\"]", "level": "high"},
            {"id": 62, "name": "Hashicorp Terraform user/org API token",
             "description": "Hashicorp Terraform user/org API token",
             "match": "['\\\"](?i)[a-z0-9]{14}\\.atlasv1\\.[a-z0-9-_=]{60,70}['\\\"]", "level": "high"},
            {"id": 63, "name": "Hashicorp Vault batch token", "description": "Hashicorp Vault batch token",
             "match": "b\\.AAAAAQ[0-9a-zA-Z_-]{156}", "level": "high"},
            {"id": 64, "name": "Hubspot API token", "description": "Hubspot API token",
             "match": "(?i)(hubspot[a-z0-9_ .\\-,]{0,25})(=|>|:=|\\|\\|:|<=|=>|:).{0,5}['\\\"]([a-h0-9]{8}-[a-h0-9]{4}-[a-h0-9]{4}-[a-h0-9]{4}-[a-h0-9]{12})['\\\"]",
             "level": "high"}, {"id": 65, "name": "Intercom API token", "description": "Intercom API token",
                                "match": "(?i)(intercom[a-z0-9_ .\\-,]{0,25})(=|>|:=|\\|\\|:|<=|=>|:).{0,5}['\\\"]([a-z0-9=_]{60})['\\\"]",
                                "level": "high"},
            {"id": 66, "name": "Intercom client secret/ID", "description": "Intercom client secret/ID",
             "match": "(?i)(intercom[a-z0-9_ .\\-,]{0,25})(=|>|:=|\\|\\|:|<=|=>|:).{0,5}['\\\"]([a-h0-9]{8}-[a-h0-9]{4}-[a-h0-9]{4}-[a-h0-9]{4}-[a-h0-9]{12})['\\\"]",
             "level": "high"},
            {"id": 67, "name": "Ionic API token", "description": "Ionic API token", "match": "ion_(?i)[a-z0-9]{42}",
             "level": "high"}, {"id": 68, "name": "Linear API token", "description": "Linear API token",
                                "match": "lin_api_(?i)[a-z0-9]{40}", "level": "high"},
            {"id": 69, "name": "Linear client secret/ID", "description": "Linear client secret/ID",
             "match": "(?i)(linear[a-z0-9_ .\\-,]{0,25})(=|>|:=|\\|\\|:|<=|=>|:).{0,5}['\\\"]([a-f0-9]{32})['\\\"]",
             "level": "high"}, {"id": 70, "name": "Lob API Key", "description": "Lob API Key",
                                "match": "(?i)(lob[a-z0-9_ .\\-,]{0,25})(=|>|:=|\\|\\|:|<=|=>|:).{0,5}['\\\"]((live|test)_[a-f0-9]{35})['\\\"]",
                                "level": "high"},
            {"id": 71, "name": "Lob Publishable API Key", "description": "Lob Publishable API Key",
             "match": "(?i)(lob[a-z0-9_ .\\-,]{0,25})(=|>|:=|\\|\\|:|<=|=>|:).{0,5}['\\\"]((test|live)_pub_[a-f0-9]{31})['\\\"]",
             "level": "high"}, {"id": 72, "name": "Mailchimp API key", "description": "Mailchimp API key",
                                "match": "(?i)(mailchimp[a-z0-9_ .\\-,]{0,25})(=|>|:=|\\|\\|:|<=|=>|:).{0,5}['\\\"]([a-f0-9]{32}-us20)['\\\"]",
                                "level": "high"},
            {"id": 73, "name": "Mailgun private API token", "description": "Mailgun private API token",
             "match": "(?i)(mailgun[a-z0-9_ .\\-,]{0,25})(=|>|:=|\\|\\|:|<=|=>|:).{0,5}['\\\"](key-[a-f0-9]{32})['\\\"]",
             "level": "high"},
            {"id": 74, "name": "Mailgun public validation key", "description": "Mailgun public validation key",
             "match": "(?i)(mailgun[a-z0-9_ .\\-,]{0,25})(=|>|:=|\\|\\|:|<=|=>|:).{0,5}['\\\"](pubkey-[a-f0-9]{32})['\\\"]",
             "level": "high"},
            {"id": 75, "name": "Mailgun webhook signing key", "description": "Mailgun webhook signing key",
             "match": "(?i)(mailgun[a-z0-9_ .\\-,]{0,25})(=|>|:=|\\|\\|:|<=|=>|:).{0,5}['\\\"]([a-h0-9]{32}-[a-h0-9]{8}-[a-h0-9]{8})['\\\"]",
             "level": "high"}, {"id": 76, "name": "Mapbox API token", "description": "Mapbox API token",
                                "match": "(?i)(pk\\.[a-z0-9]{60}\\.[a-z0-9]{22})", "level": "high"},
            {"id": 77, "name": "messagebird-api-token", "description": "MessageBird API token",
             "match": "(?i)(messagebird[a-z0-9_ .\\-,]{0,25})(=|>|:=|\\|\\|:|<=|=>|:).{0,5}['\\\"]([a-z0-9]{25})['\\\"]",
             "level": "high"},
            {"id": 78, "name": "MessageBird API client ID", "description": "MessageBird API client ID",
             "match": "(?i)(messagebird[a-z0-9_ .\\-,]{0,25})(=|>|:=|\\|\\|:|<=|=>|:).{0,5}['\\\"]([a-h0-9]{8}-[a-h0-9]{4}-[a-h0-9]{4}-[a-h0-9]{4}-[a-h0-9]{12})['\\\"]",
             "level": "medium"}, {"id": 79, "name": "New Relic user API Key", "description": "New Relic user API Key",
                                  "match": "['\\\"](NRAK-[A-Z0-9]{27})['\\\"]", "level": "high"},
            {"id": 80, "name": "New Relic user API ID", "description": "New Relic user API ID",
             "match": "(?i)(newrelic[a-z0-9_ .\\-,]{0,25})(=|>|:=|\\|\\|:|<=|=>|:).{0,5}['\\\"]([A-Z0-9]{64})['\\\"]",
             "level": "medium"}, {"id": 81, "name": "New Relic ingest browser API token",
                                  "description": "New Relic ingest browser API token",
                                  "match": "['\\\"](NRJS-[a-f0-9]{19})['\\\"]", "level": "high"},
            {"id": 82, "name": "npm access token", "description": "npm access token",
             "match": "['\\\"](npm_(?i)[a-z0-9]{36})['\\\"]", "level": "high"},
            {"id": 83, "name": "Planetscale password", "description": "Planetscale password",
             "match": "pscale_pw_(?i)[a-z0-9\\-_\\.]{43}", "level": "high"},
            {"id": 84, "name": "Planetscale API token", "description": "Planetscale API token",
             "match": "pscale_tkn_(?i)[a-z0-9\\-_\\.]{43}", "level": "high"},
            {"id": 85, "name": "Postman API token", "description": "Postman API token",
             "match": "PMAK-(?i)[a-f0-9]{24}\\-[a-f0-9]{34}", "level": "high"},
            {"id": 86, "name": "Pulumi API token", "description": "Pulumi API token", "match": "pul-[a-f0-9]{40}",
             "level": "high"}, {"id": 87, "name": "Rubygem API token", "description": "Rubygem API token",
                                "match": "rubygems_[a-f0-9]{48}", "level": "high"},
            {"id": 88, "name": "Sendgrid API token", "description": "Sendgrid API token",
             "match": "SG\\.(?i)[a-z0-9_\\-\\.]{66}", "level": "high"},
            {"id": 89, "name": "Sendinblue API token", "description": "Sendinblue API token",
             "match": "xkeysib-[a-f0-9]{64}\\-(?i)[a-z0-9]{16}", "level": "high"},
            {"id": 90, "name": "Shippo API token", "description": "Shippo API token",
             "match": "shippo_(live|test)_[a-f0-9]{40}", "level": "high"},
            {"id": 91, "name": "Linkedin Client secret", "description": "Linkedin Client secret",
             "match": "(?i)(linkedin[a-z0-9_ .\\-,]{0,25})(=|>|:=|\\|\\|:|<=|=>|:).{0,5}['\\\"]([a-z]{16})['\\\"]",
             "level": "high"}, {"id": 92, "name": "Linkedin Client ID", "description": "Linkedin Client ID",
                                "match": "(?i)(linkedin[a-z0-9_ .\\-,]{0,25})(=|>|:=|\\|\\|:|<=|=>|:).{0,5}['\\\"]([a-z0-9]{14})['\\\"]",
                                "level": "medium"},
            {"id": 93, "name": "Twitch API token", "description": "Twitch API token",
             "match": "(?i)(twitch[a-z0-9_ .\\-,]{0,25})(=|>|:=|\\|\\|:|<=|=>|:).{0,5}['\\\"]([a-z0-9]{30})['\\\"]",
             "level": "high"}, {"id": 94, "name": "Typeform API token", "description": "Typeform API token",
                                "match": "(?i)(typeform[a-z0-9_ .\\-,]{0,25})(=|>|:=|\\|\\|:|<=|=>|:).{0,5}(tfp_[a-z0-9\\-_\\.=]{59})",
                                "level": "high"},
            {"id": 95, "name": "Social Security Number", "description": "Social Security Number",
             "match": "\\d{3}-\\d{2}-\\d{4}", "level": "low"},
            {"id": 96, "name": "Version Control File", "description": "Version Control File",
             "filepath": ".*\\/\\.(git|svn)$", "level": "high"},
            {"id": 97, "name": "Config File", "description": "Config File", "filepath": ".*\\/config\\.ini$",
             "level": "medium"},
            {"id": 99, "name": "Desktop Services Store", "description": "Desktop Services Store",
             "filepath": " .*\\/\\.DS_Store$", "level": "low"},
            {"id": 100, "name": "MySQL client command history file", "description": "MySQL client command history file",
             "filepath": ".*\\/\\.(mysql|psql|irb)_history$", "level": "low"},
            {"id": 101, "name": "Recon-ng web reconnaissance framework API key database",
             "description": "Recon-ng web reconnaissance framework API key database",
             "filepath": ".*\\/\\.recon-ng\\/keys\\.db$", "level": "medium"},
            {"id": 102, "name": "DBeaver SQL database manager configuration file",
             "description": "DBeaver SQL database manager configuration file",
             "filepath": ".*\\/\\.dbeaver-data-sources\\.xml$", "level": "low"},
            {"id": 103, "name": "S3cmd configuration file", "description": "S3cmd configuration file",
             "filepath": ".*\\/\\.s3cfg$", "level": "low"},
            {"id": 104, "name": "Ruby On Rails secret token configuration file",
             "description": "If the Rails secret token is known, it can allow for remote code execution. (http://www.exploit-db.com/exploits/27527/)",
             "filepath": ".*\\/secret_token\\.rb$", "level": "high"}, {"id": 105, "name": "OmniAuth configuration file",
                                                                       "description": "The OmniAuth configuration file might contain client application secrets.",
                                                                       "filepath": ".*\\/omniauth\\.rb$",
                                                                       "level": "high"},
            {"id": 106, "name": "Carrierwave configuration file",
             "description": "Can contain credentials for online storage systems such as Amazon S3 and Google Storage.",
             "filepath": ".*\\/carrierwave\\.rb$", "level": "high"},
            {"id": 107, "name": "Potential Ruby On Rails database configuration file",
             "description": "Might contain database credentials.", "filepath": ".*\\/database\\.yml$", "level": "high"},
            {"id": 108, "name": "Django configuration file",
             "description": "Might contain database credentials, online storage system credentials, secret keys, etc.",
             "filepath": ".*\\/settings\\.py$", "level": "low"},
            {"id": 109, "name": "PHP configuration file", "description": "Might contain credentials and keys.",
             "filepath": ".*\\/config(\\.inc)?\\.php$", "level": "low"},
            {"id": 110, "name": "Jenkins publish over SSH plugin file",
             "description": "Jenkins publish over SSH plugin file",
             "filepath": ".*\\/jenkins\\.plugins\\.publish_over_ssh\\.BapSshPublisherPlugin\\.xml$", "level": "high"},
            {"id": 111, "name": "Potential Jenkins credentials file",
             "description": "Potential Jenkins credentials file", "filepath": ".*\\/credentials\\.xml$",
             "level": "high"}, {"id": 112, "name": "Apache htpasswd file", "description": "Apache htpasswd file",
                                "filepath": ".*\\/\\.htpasswd$", "level": "low"},
            {"id": 113, "name": "Configuration file for auto-login process",
             "description": "Might contain username and password.", "filepath": ".*\\/\\.(netrc|git-credentials)$",
             "level": "high"}, {"id": 114, "name": "Potential MediaWiki configuration file",
                                "description": "Potential MediaWiki configuration file",
                                "filepath": ".*\\/LocalSettings\\.php$", "level": "high"},
            {"id": 115, "name": "Rubygems credentials file",
             "description": "Might contain API key for a rubygems.org account.",
             "filepath": ".*\\/\\.gem\\/credentials$", "level": "high"},
            {"id": 116, "name": "Potential MSBuild publish profile", "description": "Potential MSBuild publish profile",
             "filepath": ".*\\/\\.pubxml(\\.user)?$", "level": "low"},
            {"id": 117, "name": "Potential Tencent Accesskey", "description": "Might contain Tencent Accesskey",
             "match": "AKID(?i)[a-z0-9]{32}", "level": "high"},
            {"id": 118, "name": "Potential aws Accesskey", "description": "Might contain aws Accesskey",
             "match": "(A3T[A-Z0-9]|AKIA|AGPA|AIDA|AROA|AIPA|ANPA|ANVA|ASIA)[A-Z0-9]{16}", "level": "high"},
            {"id": 119, "name": "Potential UCloud Accesskey", "description": "Might contain UCloud Accesskey",
             "match": "JDC_[A-z,0-9]{28}", "level": "high"},
            {"id": 120, "name": "JWT TOKEN", "description": "Might JWT Token ",
             "match": "ey[0-9a-zA-Z]{30,34}\\.ey[0-9a-zA-Z-\\/_]{30,500}\\.[0-9a-zA-Z-\\/_]{10,200}={0,2}",
             "level": "medium"}, {"id": 121, "name": "Google API", "description": "Might Google API Key ",
                                  "match": "AIza[0-9A-Za-z\\-_]{35}", "level": "medium"},
            {"id": 122, "name": "gitlab_pipeline_trigger_token", "description": "GitLab Pipeline Trigger Token",
             "match": "glptt-[0-9a-zA-Z_\\-]{20}", "level": "high"},
            {"id": 123, "name": "gitlab_runner_registration_token", "description": "GitLab Runner Registration Token",
             "match": "GR1348941[0-9a-zA-Z_\\-]{20}", "level": "high"},
            {"id": 124, "name": "Flutterwave public key", "description": "Flutterwave public key",
             "match": "FLWPUBK_TEST-(?i)[a-h0-9]{32}-X", "level": "high"},
            {"id": 125, "name": "Flutterwave secret key", "description": "Flutterwave secret key",
             "match": "FLWSECK_TEST-(?i)[a-h0-9]{32}-X", "level": "high"},
            {"id": 126, "name": "Flutterwave encrypted key", "description": "Flutterwave encrypted key",
             "match": "FLWSECK_TEST[a-h0-9]{12}", "level": "high"},
            {"id": 127, "name": "github-app-token", "description": "GitHub App Token",
             "match": "(ghu|ghs)_[0-9a-zA-Z]{36}", "level": "high"},
            {"id": 128, "name": "github-fine-grained-pat", "description": "GitHub Fine-Grained Personal Access Token",
             "match": "github_pat_[0-9a-zA-Z_]{82}", "level": "high"},
            {"id": 129, "name": "grafana-cloud-api-token", "description": "Grafana cloud api token",
             "match": "glc_[A-Za-z0-9+/]{32,400}={0,2}", "level": "high"},
            {"id": 130, "name": "grafana-service-account-token", "description": "Grafana service account token",
             "match": "glsa_[A-Za-z0-9]{32}_[A-Fa-f0-9]{8}", "level": "high"},
            {"id": 131, "name": "prefect-api-token", "description": "Prefect API token", "match": "pnu_[a-z0-9]{36}",
             "level": "medium"}]}

        # refs = image.reporefs()
        # if len(refs) > 0:
        #     ref = refs[0]
        # else:
        #     ref = image.id()
        # public.print_log("start scan sensitive: " + ref)

        # 检测docker历史（另外有扫描项）
        # ocispec = image.ocispec_v1()
        # if 'history' in ocispec.keys() and len(ocispec['history']) > 0:
        #     for history in ocispec['history']:
        #         command_content = history['created_by']
        #         report_rule_list = []
        #         for r in rules["rules"]:
        #             # 正则选择 可以选择docker history的正则是由哪些模块检测
        #             for i in ['env', 'match', 'filepath']:
        #                 regexp_s = r.get(i)
        #                 if not regexp_s:
        #                     continue
        #                 if re.search(regexp_s, command_content, re.IGNORECASE):
        #                     self.send_image_ws(get, msg="镜像OCI存在敏感信息", detail=r["description"]+"镜像OCI存在敏感信息{}".format(command_content), repair="使用此镜像可能存在危险，建议更换同类型镜像或是部署容器时清理敏感信息", status=2)
        #         if not report_rule_list:
        #             continue
        # 检测env环境变量
        # ocispec = image.ocispec_v1()
        # if 'config' in ocispec.keys() and 'Env' in ocispec['config'].keys():
        #     env_list = image.ocispec_v1()['config']['Env']
        #     for env in env_list:
        #         env_split = env.split("=")
        #         if len(env_split) >= 2:
        #             for r in rules["rules"]:
        #                 if "env" in r.keys():
        #                     env_regex = r["env"]
        #                     if re.match(env_regex, env, re.IGNORECASE):
        #                         self.send_image_ws(get, msg="镜像OCI存在敏感信息", detail=r["description"]+"\nenv存在敏感信息，可能会造成数据泄露", repair="使用该镜像部署容器时，及时修改默认密码或者鉴权值，防止被黑客利用入侵", status=2)
        #                         break
        # 排除大型项目
        large_dir = ["usr", "lib"]
        sensitive_dirs = []
        try:
            for filename in image.listdir("/"):
                if filename not in large_dir:
                    sensitive_dirs.append("/"+filename)
        except Exception as e:
            public.print_log("Failed to obtain mirror directory{}".format(e))
            sensitive_dirs = ["/"]

        # 检测存在敏感数据的路径
        for sensitive_dir in sensitive_dirs:
            for root, dirs, files in image.walk(sensitive_dir):
                # 短暂停留0.004s，防止占用太高影响其他接口响应
                time.sleep(0.004)
                # 遍历深度不超过3
                if len(root.split("/")) > 3:
                    self.send_image_ws(get, msg=self.short_string1(public.lang("Scanning:{}",root)))
                    # public.print_log("跳过{}".format(root))
                    continue
                for dir in dirs:
                    try:
                        dirpath = os.path.join(root, dir)
                        self.send_image_ws(get, msg=public.lang("Scanning:{}...",dirpath))
                        # public.print_log("扫描目录{}".format(dirpath))
                        # detect filepath or filename
                        for r in rules["rules"]:
                            if "filepath" in r.keys():
                                filepath_match_regex = r["filepath"]
                                if re.match(filepath_match_regex, dirpath):
                                    self.send_image_ws(get, msg=public.lang("Sensitive directories found{}", dirpath), detail=public.lang("The image exists in a sensitive directory:{}, may be used by attackers to steal sensitive data or source code, leading to further security issues.",dirpath), repair=public.lang("1. Enter the container deployed using the image and delete the directory without affecting the business<br/> 2. If it cannot be deleted, restrict access to the directory",dirpath), status=2)
                                    break
                    except Exception as e:
                        pass
                        # public.print_log("Match sensitive information to catch exceptions{}".format(e))
                for filename in files:
                    try:
                        filepath = os.path.join(root, filename)
                        self.send_image_ws(get, msg=public.lang("Scanning:{}...",filename))
                        # public.print_log("扫描文件{}".format(filepath))
                        # 跳过白名单
                        whitelist = rules["whitelist"]
                        white_match = False
                        white_paths = whitelist["paths"]
                        for wp in white_paths:
                            if fnmatch.filter([filepath], wp):
                                white_match = True
                                break
                        if white_match:
                            continue

                        try:
                            # 跳过非常规文件，超过10m
                            f_stat = image.stat(filepath)
                            if not S_ISREG(f_stat.st_mode):
                                continue
                            if f_stat.st_size > 10 * 1024 * 1024:
                                continue

                            f = image.open(filepath, mode="rb")
                            f_content_byte = f.read()
                        except FileNotFoundError as e:
                            # public.print_log("Error while traversing sensitive files：{}".format(e))
                            continue
                        # except BaseException as e:
                        #     public.print_log("Error while traversing sensitive files：{}".format(e))
                        #     continue
                        # 检测文件路径及文件名
                        match = False
                        for r in rules["rules"]:
                            if "filepath" in r.keys():
                                filepath_match_regex = r["filepath"]
                                if re.match(filepath_match_regex, filepath):
                                    match = True
                                    self.send_image_ws(get, msg=public.lang("Sensitive files found{}",filepath), detail=r["description"] + "：<br/>It was found that the image contains sensitive files {}, which may cause leakage.".format(filepath), repair="1. Enter the container deployed using the image, and it is recommended to delete the file if it does not affect the business<br/> 2. If it cannot be deleted, restrict the access rights of the file<br/> 3. Use a password to protect sensitive files from being easily accessed read", status=2)
                                    break
                        if match:
                            continue
                        # chardet_guess = chardet.detect(f_content_byte[0:64])
                        # if chardet_guess["encoding"] != None:
                        #     try:
                        #         f_content = f_content_byte.decode(chardet_guess["encoding"])
                        #     except:
                        #         continue
                        # else:
                        #     f_content = str(f_content_byte)
                        # mime_guess = magic.from_buffer(f_content_byte, mime=True)
                        # for r in rules["rules"]:
                        #     # mime
                        #     mime_find = False
                        #     if "mime" in r.keys():
                        #         if r["mime"] == mime_guess:
                        #             mime_find = True
                        #     else:
                        #         if mime_guess.startswith("text/"):
                        #             mime_find = True
                        #     if mime_find:
                        #         if "match" in r.keys():
                        #             match = r["match"]
                        #             if match.startswith("$contains:"):
                        #                 keyword = match.lstrip("$contains:")
                        #                 if keyword in f_content:
                        #                     file_stat = image.stat(filepath)
                        #                     self.send_image_ws(get, msg="镜像路径{}存在敏感信息".format(filepath),
                        #                                        repair="建议使用该镜像部署容器后，检查该文件是否有用，无用则清理",
                        #                                        status=2)
                        #
                        #             else:
                        #                 if re.match(match, f_content):
                        #                     file_stat = image.stat(filepath)
                        #                     self.send_image_ws(get, msg="镜像路径{}存在敏感信息".format(filepath),
                        #                                        repair="建议使用该镜像部署容器后，检查该文件是否有用，无用则清理",
                        #                                        status=2)
                    except Exception as e:
                        pass
                        # public.print_log("Error while traversing sensitive files：{}".format(e))

    def scan_backdoor(self, get, image):
        """
        @name 扫描后门
        @author lwh<2024-1-23>
        """
        backdoor_regex_list1 = [
            # reverse shell
            r'''(nc|ncat|netcat)\b.*(-e|--exec|-c)\b.*?\b(ba|da|z|k|c|a|tc|fi|sc)?sh\b''',
            r'''python\w*\b.*\bsocket\b.*?\bconnect\b.*?\bsubprocess\b.*?\bsend\b.*?\bstdout\b.*?\bread\b''',
            r'''python\w*\b.*\bsocket\b.*?\bconnect\b.*?\bos\.dup2\b.*?\b(call|spawn|popen)\b\s*\([^)]+?\b(ba|da|z|k|c|a|tc|fi|sc)?sh\b''',
            r'''(sh|bash|dash|zsh)\b.*-c\b.*?\becho\b.*?\bsocket\b.*?\bwhile\b.*?\bputs\b.*?\bflush\b.*?\|\s*tclsh\b''',
            r'''(sh|bash|dash|zsh)\b.*-c\b.*?\btelnet\b.*?\|&?.*?\b(ba|da|z|k|c|a|tc|fi|sc)?sh\b.*?\|&?\s*telnet\b''',
            r'''(sh|bash|dash|zsh)\b.*-c\b.*?\bcat\b.*?\|&?.*?\b(ba|da|z|k|c|a|tc|fi|sc)?sh\b.*?\|\s*(nc|ncat)\b''',
            r'''(sh|bash|dash|zsh)\b.*sh\s+(-i)?\s*>&?\s*/dev/(tcp|udp)/.*?/\d+\s+0>&\s*(1|2)''',
        ]

        def bashrc():
            """
            @name bashrc后门检测
            """
            backdoor_regex_list = [r'''alias\s+ssh=[\'\"]{0,1}strace''', r'''alias\s+sudo=''']
            bashrc_dirs = ["/home", "/root"]
            for bashrc_dir in bashrc_dirs:
                for root, dirs, files in image.walk(bashrc_dir):
                    for file in files:
                        if re.match(r'''^\.[\w]*shrc$''', file):
                            filepath = os.path.join(root, file)
                        else:
                            continue
                        try:
                            f = image.open(filepath, mode="r")
                            f_content = f.read()
                            for backdoor_regex in backdoor_regex_list:
                                if re.search(backdoor_regex, f_content):
                                    self.send_image_ws(get, msg=public.lang("Found bashrc backdoor{}",filepath), detail=public.lang("It was found that the image has bashrc backdoor: [{}], malicious code content: <br/>{}",filepath, self.short_string(f_content)), repair=public.lang("1. Enter the container deployed using the image and delete the malicious code under the file<br/>2. Check whether the container has been invaded, and update the access token or account password of the business in the container<br/>3. It is recommended to replace the official image or Other trusted image deployment containers"), status=3)
                            for backdoor_regex in backdoor_regex_list1:
                                if re.search(backdoor_regex, f_content):
                                    self.send_image_ws(get, msg=public.lang("Backdoor file found{}",filepath), detail=public.lang("It was found that the bashrc backdoor file [{}] exists in the image, and the malicious code content is:<br/>{}",filepath, self.short_string(f_content)), repair=public.lang("1. Enter the container deployed using the image and delete the malicious code under the file<br/>2. Check whether the container has been invaded, and update the access token or account password of the business in the container<br/>3. It is recommended to replace the official image or Other trusted image deployment containers"), status=3)
                        except FileNotFoundError:
                            continue
                        except BaseException:
                            pass
                            # public.print_log(e)

        def crontab():
            """
            @name crontab后门检测
            """
            cron_list = ["/etc/crontab", "/etc/cron.hourly", "/etc/cron.daily", "/etc/cron.weekly", "/etc/cron.monthly",
                         "/etc/cron.d"]
            environment_regex = r'''[a-zA-Z90-9]+\s*=\s*[^\s]+$'''
            cron_regex = r'''((\d{1,2}|\*)\s+){5}[a-zA-Z0-9]+\s+(.*)'''
            backdoor_regex_list = [
                # download
                r'''^(wget|curl)\b'''
                # mrig
                r'''^([\w0-9]*mrig[\w0-9]*)\b'''
            ]

            def detect_crontab_content(cron_f):
                """
                @name 检查crontab内容
                """
                result_dict = {}
                for line in cron_f.readlines():
                    # preprocess
                    line = line.strip()
                    line = line.replace("\n", "")
                    # environment
                    if re.match(environment_regex, line): continue
                    m = re.match(cron_regex, line)
                    if m:
                        if len(m.groups()) == 3:
                            cmdline1 = m.group(3)
                            # for backdoor_regex in backdoor_regex_list:
                            #     if re.search(backdoor_regex, cmdline1):
                            #         result_dict[backdoor_regex] = cmdline1
                            for backdoor_regex in backdoor_regex_list1:
                                if re.search(backdoor_regex, cmdline1):
                                    self.send_image_ws(get, msg=public.lang("cron backdoor discovered{}",filepath),
                                                       detail=public.lang("It was found that the cron backdoor [{}] exists in the image, and the malicious code content is:<br/>{}",filepath, self.short_string(cmdline1)),
                                                       repair=public.lang("1. Enter the container deployed using the image and delete the malicious code under the file<br/>2. Check whether the container has been invaded, and update the access token or account password of the business in the container<br/>3. It is recommended to replace the official image or Other trusted image deployment containers"),
                                                       status=3)
                                    result_dict[backdoor_regex] = cmdline1
                        else: continue
                return result_dict

            for cron in cron_list:
                try:
                    # filetype
                    cron_stat = image.stat(cron)
                    if S_ISDIR(cron_stat.st_mode):
                        for root, dirs, files in image.walk(cron):
                            for file in files:
                                filepath = os.path.join(root, file)
                                with image.open(filepath) as f:
                                    result_dict = detect_crontab_content(f)
                                    # if len(result_dict) > 0:
                                    #     for regex, cmdline in result_dict.items():
                                    #         self.send_image_ws(get, msg="cron backdoor discovered{}".format(filepath), detail="镜像发现crontab后门：{}".format(filepath), repair="文件命中恶意特征{}，建议删除此镜像，并及时排查相关使用该镜像部署的容器，删除文件中的恶意代码".format(cmdline), status=3)
                    elif S_ISREG(cron_stat.st_mode):
                        with image.open(cron) as f:
                            result_dict = detect_crontab_content(f)
                            # if len(result_dict) > 0:
                            #     for regex, cmdline in result_dict.items():
                            #         self.send_image_ws(get, msg="cron backdoor discovered{}".format(cron), detail="发现crontab后门：{}".format(cron),
                            #                            repair="文件命中恶意特征{}，建议删除此镜像，并及时排查相关使用该镜像部署的容器，删除文件中的恶意代码".format(
                            #                                cmdline), status=3)
                except FileNotFoundError:
                    continue

        def service():
            """
            @name 服务后门
            """
            service_dir_list = ["/etc/systemd/system"]
            for service_dir in service_dir_list:
                for root, dirs, files in image.walk(service_dir):
                    for file in files:
                        try:
                            filepath = os.path.join(root, file)
                            f = image.open(filepath, mode="r")
                            f_content = f.read()
                            for backdoor_regex in backdoor_regex_list1:
                                if re.search(backdoor_regex, f_content):
                                    self.send_image_ws(get, msg=public.lang("Found system backdoor:{}",filepath),
                                                       detail=public.lang("It was found that the systemd backdoor file [{}] exists in the image, and the malicious code content is:<br/>{}",filepath, self.short_string(f_content)),
                                                       repair=public.lang("1. Enter the container deployed using the image and delete the malicious code under the file<br/>2. Check whether the container has been invaded, and update the access token or account password of the business in the container<br/>3. It is recommended to replace the official image or Other trusted image deployment containers"),
                                                       status=3)
                        except FileNotFoundError:
                            continue
                        except BaseException:
                            pass
                            # public.print_log(e)

        def sshd():
            """
            @name sshd软链接后门检测，支持检测常规软连接后门
            """
            rootok_list = ("su", "chsh", "chfn", "runuser")
            sshd_dirs = ["/home", "/root", "/tmp"]
            for sshd_dir in sshd_dirs:
                for root, dirs, files in image.walk(sshd_dir):
                    for f in files:
                        try:
                            filepath = os.path.join(root, f)
                            f_lstat = image.lstat(filepath)
                            if S_ISLNK(f_lstat.st_mode):
                                f_link = image.evalsymlink(filepath)
                                f_exename = filepath.split("/")[-1]
                                f_link_exename = f_link.split("/")[-1]
                                if f_exename in rootok_list and f_link_exename == "sshd":
                                    self.send_image_ws(get, msg=public.lang("Found sshd backdoor{}",filepath), detail=public.lang("Found the sshd soft link backdoor: {}, the file hits the malicious feature [exe={};link_file={}]",filepath, f_exename, f_link),
                                    repair=public.lang("1. Enter the container deployed using the image and delete the malicious code under the file<br/>2. Check whether the container has been invaded, and update the access token or account password of the business in the container<br/>3. It is recommended to replace the official image or Other trusted image deployment containers"), status=3)
                        except FileNotFoundError:
                            continue
                        except BaseException as e:
                            pass
                            # public.print_log(e)

        def tcpwrapper():
            """
            @name tcpwrapper后门检测
            """
            wrapper_config_file_list = ['/etc/hosts.allow', '/etc/hosts.deny']
            for config_filepath in wrapper_config_file_list:
                try:
                    with image.open(config_filepath, mode="r") as f:
                        f_content = f.read()
                        for backdoor_regex in backdoor_regex_list1:
                            if re.search(backdoor_regex, f_content):
                                self.send_image_ws(get, msg=public.lang("Found the tcpwrapper backdoor{}",config_filepath), detail=public.lang("It was found that the tcpwrapper backdoor file [{}] exists in the image, and the malicious code content is:<br/>{}",config_filepath, self.short_string(f_content)),
                                                   repair=public.lang("1. Enter the container deployed using the image and delete the malicious code under the file<br/>2. Check whether the container has been invaded, and update the access token or account password of the business in the container<br/>3. It is recommended to replace the official image or Other trusted image deployment containers"), status=3)
                except FileNotFoundError:
                    continue
                except BaseException as e:
                    pass
                    # public.print_log(e)

        # 执行后门检测函数
        bashrc()
        crontab()
        service()
        sshd()
        tcpwrapper()

    def scan_privilege_escalation(self, get, image):
        """
        @name 提权风险
        @author lwh<2024-01-24>
        """

    def scan_escape(self, get, image):
        """
        @name 逃逸风险
        @author lwh<2024-01-24>
        """
        def sudoers():
            """
            @name sudo逃逸
            """
            sudo_regex = r"(\w{1,})\s\w{1,}=\(.*\)\s(.*)"
            unsafe_sudo_files = ["wget", "find", "cat", "apt", "zip", "xxd", "time", "taskset", "git", "sed", "pip", "tmux", "scp", "perl", "bash", "less", "awk", "man", "vim", "env", "ftp"]
            try:
                with image.open("/etc/sudoers", mode="r") as f:
                    lines = f.readlines()
                for line in lines:
                    line = line.strip()
                    if line.startswith("#"):
                        continue
                    matches = re.findall(sudo_regex, line)
                    if len(matches) == 1:
                        user, sudo_command = matches[0]
                        if user.lower() in ["admin", "sudo", "root"]:
                            continue
                        for unsafe_sudo_file in unsafe_sudo_files:
                            if unsafe_sudo_file in sudo_command.lower():
                                self.send_image_ws(get, msg=public.lang("Users found to be at risk of escape{}",user), detail=public.lang("The username {} may complete container escape through the command [{}], allowing the attacker to obtain access rights to the host or other containers. Malicious content:<br/>{}",user, sudo_command, line), status=3, repair=public.lang("1. It is recommended to delete the image or no longer use it<br/>2. If there is already a business using the image, enter the container environment and delete the content of the user {} in the /etc/sudoers file.",user))
                                break
            except Exception as e:
                # public.print_log(e)
                return
        # 开始检测
        sudoers()

    def scan_log4j2(self, get, image):
        """
        @name 扫描是否存在log4j漏洞
        @author lwh<2024-01-26>
        """

# def veinmind():
#     from veinmind import docker
#     client = docker.Docker()
#     ids = client.list_image_ids()
#     # public.print_log(ids)
#     for id in ids:
#         image = client.open_image_by_id(id)
#         # public.print_log("image id: " + image.id())
#         for ref in image.reporefs():
#             public.print_log("image ref: " + ref)
#         for repo in image.repos():
#             public.print_log("image repo: " + repo)
#         # public.print_log("image ocispec: " + str(image.ocispec_v1()))


if __name__ == '__main__':
    # obj = main()
    # get = public.dict_obj()
    # obj.get_safe_scan(get=get)
    # sudo_regex = r"(\w{1,})\s\w{1,}=\(.*\)\s(.*)"
    # unsafe_sudo_files = ["wget", "find", "cat", "apt", "zip", "xxd", "time", "taskset", "git", "sed", "pip", "ed",
    #                      "tmux", "scp", "perl", "bash", "less", "awk", "man", "vi", "vim", "env", "ftp", "all"]
    # try:
    #     with open("/tmp/sudoers.test", "r") as f:
    #         lines = f.readlines()
    #     for line in lines:
    #         line = line.strip()
    #         if line.startswith("#"):
    #             continue
    #         matches = re.findall(sudo_regex, line)
    #         if len(matches) == 1:
    #             user, sudo_file = matches[0]
    #             if user.lower() in ["admin", "sudo", "root"]:
    #                 continue
    #             print(user.lower(), sudo_file.lower())
    #             for unsafe_sudo_file in unsafe_sudo_files:
    #                 if unsafe_sudo_file in sudo_file.lower():
    #                     print("用户有问题：{}".format(user))
    #                     break
    # except Exception as e:
    #     print(e)
    # 初始化安装检测SDK
    try:
        from veinmind import docker
    except Exception as e:
        # public.print_log("Importing veinmind failed:{}".format(e))
        requirements_list = ["veinmind"]
        shell_command = "btpip install --no-dependencies {}".format(" ".join(requirements_list))
        public.ExecShell(shell_command)
        sys_ver = public.get_os_version()
        # self.send_image_ws(get, msg="正在初始化检测引擎中，首次加载耗时较长...", status=1)
        if "Ubuntu" in sys_ver or "Debian" in sys_ver:
            public.WriteFile("/etc/apt/sources.list.d/libveinmind.list",
                             "deb [trusted=yes] https://download.veinmind.tech/libveinmind/apt/ ./")
            # public.print_log("Updating apt-get")
            public.ExecShell("apt-get update")
            time.sleep(1)
            public.ExecShell("apt-get install -y libveinmind-dev")
            time.sleep(1)
        elif "CentOS" in sys_ver:
            public.WriteFile("/etc/yum.repos.d/libveinmind.repo", """[libveinmind]
name=libVeinMind SDK yum repository
baseurl=https://download.veinmind.tech/libveinmind/yum/
enabled=1
gpgcheck=0""")
            public.ExecShell("yum makecache", timeout=10)
            public.ExecShell("yum install -y libveinmind-devel", timeout=10)
        else:
            pass
            # public.print_log("不支持的系统版本")
            # return public.returnMsg(False, public.lang("不支持的系统版本"))
        # self.send_image_ws(get, msg="正在检查依赖库是否存在...", status=1)
        result, err = public.ExecShell("whereis libdl.so")
        result = result.strip().split(" ")
        # public.print_log("libdl.so库的情况：{}".format(result))
        if len(result) <= 1:
            # public.print_log("缺少libdl.so库")
            result, err = public.ExecShell("whereis libdl.so.2")
            result = result.strip().split(" ")
            # public.print_log("libdl.so.2库的情况：{}".format(result))
            if len(result) <= 1:
                # public.print_log("缺少libdl.so库，需要安装libdl.so或libdl.so2")
                public.returnMsg(False, "The libdl.so library is missing, you need to install libdl.so or libdl.so2")
            else:
                # 建立libdl.so软链接至libdl.so.2
                for lib in result[1:]:
                    ln_command = "ln -s {} {}".format(lib, lib[:-2])
                    public.print_log("Soft link in progress：{}".format(ln_command))
                    public.ExecShell(ln_command)
        from veinmind import docker
        # public.print_log("执行成功")


