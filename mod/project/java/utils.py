import json
import re
import sys
import time
import zipfile
import os
import yaml
import psutil
import platform
from xml.etree.ElementTree import Element, ElementTree, parse, XMLParser
from typing import Optional, Dict, Tuple, AnyStr, List, Any
import threading
import itertools

if "/www/server/panel/class" not in sys.path:
    sys.path.insert(0, "/www/server/panel/class")

if "/www/server/panel" not in sys.path:
    sys.path.insert(0, "/www/server/panel")

import public


def get_jar_war_config(jar_war_file: str) -> Optional[List[Tuple[str, AnyStr]]]:
    """获取jar文件中的配置文件"""
    if not os.path.exists(jar_war_file):
        return None
    if not zipfile.is_zipfile(jar_war_file):  # 判断是否为zip文件
        return None
    # 打开jar文件
    res_list = []
    with zipfile.ZipFile(jar_war_file, 'r') as jar:
        for i in jar.namelist():
            # 查询所有文件中可能是配置文件的项目
            if i.endswith("application.yaml") or i.endswith("application.yml"):
                with jar.open(i) as f:
                    res_list.append((i, f.read()))

    if not res_list:
        return None

    return res_list


def to_utf8(file_data_list: List[Tuple[str, AnyStr]]) -> List[Tuple[str, str]]:
    res_list = []
    for i, data in file_data_list:
        if isinstance(data, bytes):
            try:
                new_data = data.decode("utf-8")
            except:
                continue
            else:
                res_list.append((i, new_data))
    return res_list


def parse_application_yaml(conf_data_list: List[Tuple[str, AnyStr]]) -> List[Tuple[str, Dict]]:
    res_list = []
    for i, data in conf_data_list:
        d = yaml.safe_load(data)
        if isinstance(d, dict):
            res_list.append((i, d))

    return res_list


# 接收一个jdk路径并将其规范化
def normalize_jdk_path(jdk_path: str) -> Optional[str]:
    if jdk_path.endswith("/java"):
        jdk_path = os.path.dirname(jdk_path)
    if jdk_path.endswith("/bin"):
        jdk_path = os.path.dirname(jdk_path)
    if jdk_path.endswith("/jre"):
        jdk_path = os.path.dirname(jdk_path)
    if not os.path.isdir(jdk_path):
        return None
    if not os.path.exists(os.path.join(jdk_path, "bin/java")):
        return None
    return jdk_path


def test_jdk(jdk_path: str) -> bool:
    java_bin = os.path.join(jdk_path, "bin/java")
    if os.path.exists(java_bin):
        out, err = public.ExecShell("{} -version 2>&1".format(java_bin))  # type: str, str
        if out.lower().find("version") != -1:
            return True
    return False


class TomCat:

    def __init__(self, tomcat_path: str):
        self.path = tomcat_path.rstrip("/")  # 移除多余的右"/" 统一管理
        self._jdk_path: Optional[str] = None
        self._config_xml: Optional[ElementTree] = None
        self._bt_tomcat_conf: Optional[dict] = None
        self._log_file = None
        self._version = None

    @property
    def jdk_path(self) -> Optional[str]:
        p = os.path.join(self.path, "bin/daemon.sh")
        if not os.path.exists(p):
            return None

        tmp_data = public.readFile(p)
        if isinstance(tmp_data, str):
            rep_deemon_sh = re.compile(r"^JAVA_HOME=(?P<path>.*)\n", re.M)
            re_res_jdk_path = rep_deemon_sh.search(tmp_data)
            if re_res_jdk_path:
                self._jdk_path = re_res_jdk_path.group("path").strip()
                self._jdk_path = normalize_jdk_path(self._jdk_path)
                return self._jdk_path

        return None

    def version(self) -> Optional[int]:
        if isinstance(self._version, int):
            return self._version
        v_file = os.path.join(self.path, "version.pl")
        if os.path.isfile(v_file):
            ver = public.readFile(v_file)
            if isinstance(ver, str):
                try:
                    ver_int = int(ver.split(".")[0])
                    self._version = ver_int
                    return self._version
                except:
                    pass
        return None

    @property
    def log_file(self) -> str:
        if self._log_file is not None:
            return self._log_file
        default_file = os.path.join(self.path, "logs/catalina-daemon.out")
        target_sh = os.path.join(self.path, "bin/daemon.sh")
        file_data = public.readFile(target_sh)
        conf_path = os.path.join(self.path, "conf/logpath.conf")
        if not isinstance(file_data, str):
            return default_file
        rep = re.compile(r'''\n\s?test ?"\.\$CATALINA_OUT" ?= ?\. +&& +CATALINA_OUT=['"](?P<path>\S+)['"]''')
        if rep.search(file_data):
            self._log_file = rep.search(file_data).group("path")
            public.writeFile(conf_path, os.path.dirname(self._log_file))
            return self._log_file

        if os.path.isfile(conf_path):
            path = public.readFile(conf_path)
        else:
            return default_file
        log_file = os.path.join(path, "catalina-daemon.out")
        if os.path.exists(log_file):
            self._log_file = log_file
            return self._log_file

        ver = self.version()
        if ver:
            log_file = os.path.join(path, "catalina-daemon-{}.out".format(ver))
            return log_file
        else:
            return os.path.join(path, "catalina-daemon.out")

    @property
    def bt_tomcat_conf(self) -> Optional[dict]:
        if self._bt_tomcat_conf is None:
            p = os.path.join(self.path, "bt_tomcat.json")
            if not os.path.exists(p):
                self._bt_tomcat_conf = {}
                return self._bt_tomcat_conf
            try:
                self._bt_tomcat_conf = json.loads(public.readFile(p))
            except:
                self._bt_tomcat_conf = {}
        return self._bt_tomcat_conf

    def save_bt_tomcat_conf(self):
        if self._bt_tomcat_conf is not None:
            p = os.path.join(self.path, "bt_tomcat.json")
            public.writeFile(p, json.dumps(self._bt_tomcat_conf))

    def change_log_path(self, log_path: str, prefix: str = "") -> bool:
        log_path = log_path.rstrip("/")
        target_sh = os.path.join(self.path, "bin/daemon.sh")
        if not os.path.exists(target_sh):
            return False
        file_data = public.readFile(target_sh)
        if not isinstance(file_data, str):
            return False
        rep = re.compile(r'''\n ?test ?"\.\$CATALINA_OUT" ?= ?\. && {0,3}CATALINA_OUT="[^\n]*"[^\n]*\n''')
        if prefix and not prefix.startswith("-"):
            prefix = "-{}".format(prefix)
        repl = '\ntest ".$CATALINA_OUT" = . && CATALINA_OUT="{}/catalina-daemon{}.out"\n'.format(log_path, prefix)
        file_data = rep.sub(repl, file_data)
        public.writeFile(target_sh, file_data)
        conf_path = os.path.join(self.path, "conf/logpath.conf")
        public.WriteFile(conf_path, log_path)
        return True

    @property
    def config_xml(self) -> Optional[ElementTree]:
        if self._config_xml is None:
            p = os.path.join(self.path, "conf/server.xml")
            if not os.path.exists(p):
                return None

            self._config_xml = parse(p, parser=XMLParser(encoding="utf-8"))
        return self._config_xml

    def set_port(self, port: int) -> bool:
        if self.config_xml is None:
            return False
        conf_elem = self.config_xml.findall("Service/Connector")
        if conf_elem is None:
            return False
        for i in conf_elem:
            if 'protocol' in i.attrib and 'port' in i.attrib:
                if i.attrib['protocol'] == 'HTTP/1.1':
                    i.attrib['port'] = str(port)
                    return True
        return False

    def pid(self) -> Optional[int]:
        pid_file = os.path.join(self.path, 'logs/catalina-daemon.pid')
        if os.path.exists(pid_file):
            # 使用psutil判断进程是否在运行
            try:
                pid = public.readFile(pid_file)
                return int(pid)
            except:
                return None
        return None

    def port(self) -> int:
        if self.config_xml is None:
            return 0
        for i in self.config_xml.findall("Service/Connector"):
            if i.attrib.get("protocol") == "HTTP/1.1" and 'port' in i.attrib:
                return int(i.attrib.get("port"))
        return 8080

    @property
    def installed(self) -> bool:
        start_path = os.path.join(self.path, 'bin/daemon.sh')
        conf_path = os.path.join(self.path, 'conf/server.xml')
        if not os.path.exists(self.path):
            return False
        if not os.path.isfile(start_path):
            return False
        if not os.path.isfile(conf_path):
            return False
        return True

    def running(self) -> bool:
        pid = self.pid()
        if pid:
            try:
                p = psutil.Process(pid)
                return p.is_running()
            except:
                return False
        return False

    def status(self) -> dict:
        return {
            "status": os.path.exists(self.path) and os.path.exists(os.path.join(self.path, "bin/daemon.sh")),
            "jdk_path": self.jdk_path,
            "path": self.path,
            "running": self.running(),
            "port": self.port(),
            "stype": "built" if os.path.exists(os.path.join(self.path, "conf/server.xml")) else "uninstall"
        }

    def save_config_xml(self) -> bool:
        if self.config_xml is None:
            return False
        p = os.path.join(self.path, "conf/server.xml")

        def _indent(elem: Element, level=0):
            i = "\n" + level * "  "
            if len(elem):
                if not elem.text or not elem.text.strip():
                    elem.text = i + "  "
                if not elem.tail or not elem.tail.strip():
                    elem.tail = i
                for elem in elem:
                    _indent(elem, level + 1)
                if not elem.tail or not elem.tail.strip():
                    elem.tail = i
            else:
                if level and (not elem.tail or not elem.tail.strip()):
                    elem.tail = i

        _indent(self.config_xml.getroot())
        self.config_xml.write(p, encoding="utf-8", xml_declaration=True)
        return True

    def host_by_name(self, name: str) -> Optional[Element]:
        if self.config_xml is None:
            return None
        engines = self.config_xml.findall("Service/Engine")
        if not engines:
            return None
        engine = engines[0]
        for h in engine:
            if h.tag == "Host" and h.attrib.get("name", None) == name:
                return h
        return None

    def add_host(self, name: str, path: str) -> bool:
        if self.config_xml is None:
            return False
        if not os.path.exists(path):
            os.makedirs(path)
        if self.host_by_name(name):
            return False
        engine = self.config_xml.findall("Service/Engine")
        if not engine:
            return False
        path_name = ""
        if os.path.isfile(path):
            app_base = os.path.dirname(path)
            if path.endswith(".war"):
                path_name = os.path.basename(path).rsplit(".", 1)[0]
        else:
            app_base = path

        host = Element("Host", attrib={
            "appBase": app_base,
            "autoDeploy": "true",
            "name": name,
            "unpackWARs": "true",
            "xmlNamespaceAware": "false",
            "xmlValidation": "false",
        })

        context = Element("Context", attrib={
            "docBase": path,
            "path": path_name,
            "reloadable": "true",
            "crossContext": "true",
        })
        host.append(context)

        engine[0].append(host)
        return True

    def set_host_path_by_name(self, name: str, path: str) -> bool:
        if self.config_xml is None:
            return False
        for i in self.config_xml.findall("Service/Engine/Host"):
            if i.attrib.get("name", None) != name:
                continue
            for j in i:
                if j.tag == "Context":
                    j.attrib["docBase"] = path
                    return True
        return False

    def remove_host(self, name: str) -> bool:
        if self.config_xml is None:
            return False
        target_host = self.host_by_name(name)
        if not target_host:
            return False
        engine = self.config_xml.findall("Service/Engine")
        if not engine:
            return False
        engine[0].remove(target_host)
        return True

    def mutil_remove_host(self, name_list: List[str]) -> bool:
        if self.config_xml is None:
            return False
        for name in name_list:
            self.remove_host(name)
        return False

    def start(self, by_user: str = "root") -> bool:
        if not self.running():
            daemon_file = os.path.join(self.path, "bin/daemon.sh")
            if not os.path.isfile(self.log_file):
                public.ExecShell("touch {}".format(self.log_file))
            public.ExecShell("chown {}:{} {}".format(by_user, by_user, self.log_file))
            public.ExecShell("bash {} start".format(daemon_file), user=by_user)

        return self.running()

    def stop(self) -> bool:
        if self.running():
            daemon_file = os.path.join(self.path, "bin/daemon.sh")
            public.ExecShell("bash {} stop".format(daemon_file))
        return not self.running()

    def restart(self, by_user: str = "root") -> bool:
        daemon_file = os.path.join(self.path, "bin/daemon.sh")
        if self.running():
            public.ExecShell("bash {} stop".format(daemon_file))
        if not os.path.isfile(self.log_file):
            public.ExecShell("touch {}".format(self.log_file))
        public.ExecShell("chown {}:{} {}".format(by_user, by_user, self.log_file))
        public.ExecShell("bash {} start".format(daemon_file), user=by_user)
        return self.running()

    def replace_jdk(self, jdk_path: str) -> Optional[str]:
        jdk_path = normalize_jdk_path(jdk_path)
        if not jdk_path:
            return "jdk路径错误或无法识别"

        deemon_sh_path = "{}/bin/daemon.sh".format(self.path)
        if not os.path.isfile(deemon_sh_path):
            return 'Tomcat启动文件丢失!'

        deemon_sh_data = public.readFile(deemon_sh_path)
        if not isinstance(deemon_sh_data, str):
            return 'Tomcat启动文件读取失败!'

        # deemon_sh
        rep_deemon_sh = re.compile(r"^JAVA_HOME=(?P<path>.*)\n", re.M)
        re_res_deemon_sh = rep_deemon_sh.search(deemon_sh_data)
        if not re_res_deemon_sh:
            return 'Tomcat启动文件解析失败!'

        jsvc_make_path = None
        for i in os.listdir(self.path + "/bin"):
            tmp_dir = "{}/bin/{}".format(self.path, i)
            if i.startswith("commons-daemon") and os.path.isdir(tmp_dir):
                make_path = tmp_dir + "/unix"
                if os.path.isdir(make_path):
                    jsvc_make_path = make_path
                    break

        if jsvc_make_path is None:
            return 'Jsvc文件丢失!'

        # 重装jsvc
        if os.path.isfile(self.path + "/bin/jsvc"):
            os.rename(self.path + "/bin/jsvc", self.path + "/bin/jsvc_back")

        if os.path.isfile(jsvc_make_path + "/jsvc"):
            os.remove(jsvc_make_path + "/jsvc")

        shell_str = r'''
cd {}
make clean
./configure --with-java={}
make
    '''.format(jsvc_make_path, jdk_path)
        public.ExecShell(shell_str)
        if os.path.isfile(jsvc_make_path + "/jsvc"):
            os.rename(jsvc_make_path + "/jsvc", self.path + "/bin/jsvc")
            public.ExecShell("chmod +x {}/bin/jsvc".format(self.path))
            os.remove(self.path + "/bin/jsvc_back")
        else:
            os.rename(self.path + "/bin/jsvc_back", self.path + "/bin/jsvc")
            return 'Jsvc编译失败!'

        new_deemon_sh_data = deemon_sh_data[:re_res_deemon_sh.start()] + (
            'JAVA_HOME={}\n'.format(jdk_path)
        ) + deemon_sh_data[re_res_deemon_sh.end():]
        public.writeFile(deemon_sh_path, new_deemon_sh_data)
        return None

    def reset_tomcat_server_config(self, port: int):
        ret = '''<Server port="{}" shutdown="SHUTDOWN">
    <Listener className="org.apache.catalina.startup.VersionLoggerListener" />
    <Listener SSLEngine="on" className="org.apache.catalina.core.AprLifecycleListener" />
    <Listener className="org.apache.catalina.core.JreMemoryLeakPreventionListener" />
    <Listener className="org.apache.catalina.mbeans.GlobalResourcesLifecycleListener" />
    <Listener className="org.apache.catalina.core.ThreadLocalLeakPreventionListener" />
    <GlobalNamingResources>
    <Resource auth="Container" description="User database that can be updated and saved" factory="org.apache.catalina.users.MemoryUserDatabaseFactory" name="UserDatabase" pathname="conf/tomcat-users.xml" type="org.apache.catalina.UserDatabase" />
    </GlobalNamingResources>
    <Service name="Catalina">
    <Connector connectionTimeout="20000" port="{}" protocol="HTTP/1.1" redirectPort="8490" />
    <Engine defaultHost="localhost" name="Catalina">
        <Realm className="org.apache.catalina.realm.LockOutRealm">
        <Realm className="org.apache.catalina.realm.UserDatabaseRealm" resourceName="UserDatabase" />
        </Realm>
        <Host appBase="webapps" autoDeploy="true" name="localhost" unpackWARs="true">
        <Valve className="org.apache.catalina.valves.AccessLogValve" directory="logs" pattern="%h %l %u %t &quot;%r&quot; %s %b" prefix="localhost_access_log" suffix=".txt" />
        </Host>
    </Engine>
    </Service>
</Server>'''.format(create_a_not_used_port(), port)
        public.WriteFile(self.path + '/conf/server.xml', ret)

    @staticmethod
    def _get_os_version() -> str:
        # 获取Centos
        if os.path.exists('/usr/bin/yum') and os.path.exists('/etc/yum.conf'):
            return 'Centos'
        # 获取Ubuntu
        if os.path.exists('/usr/bin/apt-get') and os.path.exists('/usr/bin/dpkg'):
            return 'Ubuntu'
        return 'Unknown'

    @classmethod
    def async_install_tomcat_new(cls, version: str, jdk_path: Optional[str]) -> Optional[str]:
        os_ver = cls._get_os_version()
        if version == "7" and os_ver == 'Ubuntu':
            return '操作系统不支持!'

        if jdk_path:
            jdk_path = normalize_jdk_path(jdk_path)
            if not jdk_path:
                return 'jdk路径错误或无法识别'
            if not test_jdk(jdk_path):
                return '指定的jdk不可用'

        if not jdk_path:
            jdk_path = ''

        shell_str = (
            'rm -rf /tmp/1.sh && '
            '/usr/local/curl/bin/curl -o /tmp/1.sh %s/install/src/webserver/shell/new_jdk.sh && '
            'bash /tmp/1.sh install %s %s'
        ) % (public.get_url(), version, jdk_path)

        if not os.path.exists("/tmp/panelTask.pl"):  # 如果当前任务队列并未执行，就把日志清空
            public.writeFile('/tmp/panelExec.log', '')
        soft_name = "Java项目Tomcat-" + version
        task_id = public.M('tasks').add(
            'id,name,type,status,addtime,execstr',
            (None, '安装[{}]'.format(soft_name), 'execshell', '0', time.strftime('%Y-%m-%d %H:%M:%S'), shell_str))

        cls._create_install_wait_msg(task_id, version)

    @staticmethod
    def _create_install_wait_msg(task_id: int, version: str):
        from panel_msg.msg_file import message_mgr

        file_path = "/tmp/panelExec.log"
        if not os.path.exists(file_path):
            public.writeFile(file_path, "")

        soft_name = "Java项目Tomcat-" + version
        data = {
            "soft_name": soft_name,
            "install_status": "等待安装" + soft_name,
            "file_name": file_path,
            "self_type": "soft_install",
            "status": 0,
            "task_id": task_id
        }
        title = "等待安装" + soft_name
        res = message_mgr.collect_message(title, ["Java环境管理", soft_name], data)
        if isinstance(res, str):
            public.WriteLog("消息盒子", "安装信息收集失败")
            return None
        return res


def bt_tomcat(ver: int) -> Optional[TomCat]:
    if ver not in (7, 8, 9, 10) and ver not in ("7", "8", "9", "10"):
        return None
    return TomCat(tomcat_path="/usr/local/bttomcat/tomcat%d" % int(ver))


def site_tomcat(site_name: str) -> Optional[TomCat]:
    tomcat_path = os.path.join("/www/server/bt_tomcat_web", site_name)
    if not os.path.exists(tomcat_path):
        return None
    return TomCat(tomcat_path=tomcat_path)


class JDKManager:

    def __init__(self):
        self._versions_list: Optional[List[str]] = None
        self._custom_jdk_list: Optional[List[str]] = None
        self._jdk_path = "/www/server/java"
        self._custom_file = "/www/server/panel/data/get_local_jdk.json"
        if not os.path.exists(self._jdk_path):
            os.makedirs(self._jdk_path, 0o755)

    @property
    def versions_list(self) -> List[str]:
        if self._versions_list:
            return self._versions_list
        jdk_json_file = '/www/server/panel/data/jdk.json'
        tip_file = '/www/server/panel/data/jdk.json.pl'
        try:
            last_refresh = int(public.readFile(tip_file))
        except ValueError:
            last_refresh = 0
        versions_data = public.readFile(jdk_json_file)
        if time.time() - last_refresh > 3600:
            public.run_thread(public.downloadFile, ('{}/src/jdk/jdk.json'.format(public.get_url()), jdk_json_file))
            public.writeFile(tip_file, str(int(time.time())))

        try:
            versions = json.loads(versions_data)
        except Exception:
            versions = {
                "x64": [
                    "jdk1.7.0_80", "jdk1.8.0_371", "jdk-9.0.4", "jdk-10.0.2",
                    "jdk-11.0.19", "jdk-12.0.2", "jdk-13.0.2", "jdk-14.0.2",
                    "jdk-15.0.2", "jdk-16.0.2", "jdk-17.0.8", "jdk-18.0.2.1",
                    "jdk-19.0.2", "jdk-20.0.2"
                ],
                "arm": [
                    "jdk1.8.0_371", "jdk-11.0.19", "jdk-15.0.2", "jdk-16.0.2",
                    "jdk-17.0.8", "jdk-18.0.2.1", "jdk-19.0.2", "jdk-20.0.2"
                ],
                "loongarch64": [
                    "jdk-8.1.18", "jdk-11.0.22", "jdk-17.0.10", "jdk-21.0.2"
                ]
            }
        arch = platform.machine()
        if arch == "aarch64" or 'arm' in arch:
            arch = "arm"
        elif arch == "loongarch64":
            arch = "loongarch64"
        elif arch == "x86_64":
            arch = "x64"

        self._versions_list = versions.get(arch, [])
        return self._versions_list

    def jdk_list_path(self) -> List[str]:
        return ["{}/{}".format(self._jdk_path, i) for i in self.versions_list]

    @property
    def custom_jdk_list(self) -> List[str]:
        if self._custom_jdk_list:
            return self._custom_jdk_list

        try:
            self._custom_jdk_list = json.loads(public.readFile(self._custom_file))
        except:
            self._custom_jdk_list = []

        if not isinstance(self._custom_jdk_list, list):
            self._custom_jdk_list = []

        return self._custom_jdk_list

    def add_custom_jdk(self, jdk_path: str) -> Optional[str]:
        jdk_path = normalize_jdk_path(jdk_path)
        if not jdk_path:
            return "jdk路径错误或无法识别"

        if jdk_path in self.custom_jdk_list or jdk_path in self.jdk_list_path:
            return

        self.custom_jdk_list.append(jdk_path)
        public.writeFile(self._custom_file, json.dumps(self.custom_jdk_list))

    def remove_custom_jdk(self, jdk_path: str) -> None:
        if jdk_path not in self.custom_jdk_list:
            return

        self.custom_jdk_list.remove(jdk_path)
        public.writeFile(self._custom_file, json.dumps(self.custom_jdk_list))

    def async_install_jdk(self, version: str) -> None:
        sh_str = "cd /www/server/panel/install && /bin/bash install_soft.sh {} install {} {}".format(0, 'jdk', version)

        if not os.path.exists("/tmp/panelTask.pl"):  # 如果当前任务队列并未执行，就把日志清空
            public.writeFile('/tmp/panelExec.log', '')
        task_id = public.M('tasks').add(
            'id,name,type,status,addtime,execstr',
            (None,  '安装[{}]'.format(version), 'execshell', '0', time.strftime('%Y-%m-%d %H:%M:%S'), sh_str))

        self._create_install_wait_msg(task_id, version)

    @staticmethod
    def _create_install_wait_msg(task_id: int, version: str):
        from panel_msg.msg_file import message_mgr

        file_path = "/tmp/panelExec.log"
        if not os.path.exists(file_path):
            public.writeFile(file_path, "")

        data = {
            "soft_name": version,
            "install_status": "等待安装" + version,
            "file_name": file_path,
            "self_type": "soft_install",
            "status": 0,
            "task_id": task_id
        }
        title = "等待安装" + version
        res = message_mgr.collect_message(title, ["Java环境管理", version], data)
        if isinstance(res, str):
            public.WriteLog("消息盒子", "安装信息收集失败")
            return None
        return res

    def install_jdk(self, version: str) -> Optional[str]:
        if version not in self.versions_list:
            return "Version does not exist and cannot be installed"

        if os.path.exists(self._jdk_path + "/" + version):
            return "已存在的版本, 无法再次安装，如需再次安装请先卸载"

        if os.path.exists("{}/{}.pl".format(self._jdk_path, version)):
            return "安装任务进行中，请勿再次添加"

        public.writeFile("{}/{}.pl".format(self._jdk_path, version), "installing")
        t = threading.Thread(target=self._install_jdk, args=(version,))
        t.start()
        return None

    def _install_jdk(self, version: str) -> None:
        try:
            log_file = "{}/{}_install.log".format(self._jdk_path, version)
            if not os.path.exists('/www/server/panel/install/jdk.sh'):
                public.ExecShell('wget -O /www/server/panel/install/jdk.sh ' + public.get_url() + '/install/0/jdk.sh')
            public.ExecShell('bash /www/server/panel/install/jdk.sh install {} 2>&1 > {}'.format(version, log_file))
        except:
            pass
        public.ExecShell('rm -rf /www/server/java/{}.*'.format(version))

    def uninstall_jdk(self, version: str) -> Optional[str]:
        if not os.path.exists(self._jdk_path + "/" + version):
            return "没有安装指定的版本，无法卸载"
        public.ExecShell('rm -rf /www/server/java/{}*'.format(version))
        return

    @staticmethod
    def set_jdk_env(jdk_path) -> Optional[str]:
        if jdk_path != "":
            jdk_path = normalize_jdk_path(jdk_path)
            if not jdk_path:
                return "jdk路径错误或无法识别"

        # 写入全局的shell配置文件
        profile_path = '/etc/profile'
        java_home_line = "export JAVA_HOME={}".format(jdk_path) if jdk_path else ""
        path_line = "export PATH=$JAVA_HOME/bin:$PATH"
        profile_data = public.readFile(profile_path)
        if not isinstance(profile_data, str):
            return "无法读取环境变量文件"

        rep_java_home = re.compile(r"export\s+JAVA_HOME=.*\n")
        rep_path = re.compile(r"export\s+PATH=\$JAVA_HOME/bin:\$PATH\s*?\n")
        if rep_java_home.search(profile_data):
            profile_data = rep_java_home.sub(java_home_line, profile_data)
        elif jdk_path:
            profile_data = profile_data + "\n" + java_home_line

        if rep_path.search(profile_data):
            if not jdk_path:
                profile_data = rep_path.sub("", profile_data)
        elif jdk_path:
            profile_data = profile_data + "\n" + path_line

        try:
            with open(profile_path, "w") as f:
                f.write(profile_data)
        except PermissionError:
            return "无法修改环境变量，可能是系统加固插件拒绝了操作"
        except:
            return "修改失败"

        return

    @staticmethod
    def get_env_jdk() -> Optional[str]:
        profile_data = public.readFile('/etc/profile')
        if not isinstance(profile_data, str):
            return None
        current_java_home = None
        for line in profile_data.split("\n"):
            if 'export JAVA_HOME=' in line:
                current_java_home = line.split('=')[1].strip().replace('"', '').replace("'", "")

        return current_java_home


def jps() -> List[int]:
    dir_list = [i for i in os.listdir("/tmp") if i.startswith("hsperfdata_")]
    return [int(j) for j in itertools.chain(*[os.listdir("/tmp/" + i) for i in dir_list]) if j.isdecimal()]


def js_value_to_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.lower() in ("true", "yes", "1")
    return bool(value)


def check_port_with_net_connections(port: int) -> bool:
    try:
        for conn in psutil.net_connections():
            if conn.status == 'LISTEN' and conn.laddr.port == port:
                return False
    except:
        pass
    return True


def check_port(port) -> bool:
    """
    返回false表示端口不可用
    """
    if not isinstance(port, int):
        port = int(port)
    if port == 0:
        return False
    if not 0 < port < 65535:
        return False
    project_list = public.M('sites').field('name,path,project_config').select()
    for project_find in project_list:
        try:
            project_config = json.loads(project_find['project_config'])
        except json.JSONDecodeError:
            continue
        if 'port' not in project_config:
            continue
        if int(project_config['port']) == port:
            return False

    try:
        for conn in psutil.net_connections():
            if conn.status == 'LISTEN' and conn.laddr.port == port:
                return False
    except:
        pass
    return True


def pass_dir_for_user(path_dir: str, user: str):
    """
    给某个用户，对应目录的执行权限
    """
    import stat
    if not os.path.isdir(path_dir):
        return
    try:
        import pwd
        uid_data = pwd.getpwnam(user)
        uid = uid_data.pw_uid
        gid = uid_data.pw_gid
    except:
        return

    if uid == 0:
        return

    if path_dir[:-1] == "/":
        path_dir = path_dir[:-1]

    while path_dir != "/":
        path_dir_stat = os.stat(path_dir)
        if path_dir_stat.st_uid != uid or path_dir_stat.st_gid != gid:
            old_mod = stat.S_IMODE(path_dir_stat.st_mode)
            if not old_mod & 1:
                os.chmod(path_dir, old_mod+1)
        path_dir = os.path.dirname(path_dir)


def create_a_not_used_port() -> int:
    """
    生成一个可用的端口
    """
    import random
    while True:
        port = random.randint(2000, 65535)
        if check_port_with_net_connections(port):
            return port


# 记录项目是通过用户停止的
def stop_by_user(project_id):
    file_path = "{}/data/push/tips/project_stop.json".format(public.get_panel_path())
    if not os.path.exists(file_path):
        data = {}
    else:
        data_content = public.readFile(file_path)
        try:
            data = json.loads(data_content)
        except json.JSONDecodeError:
            data = {}
    data[str(project_id)] = True
    public.writeFile(file_path, json.dumps(data))


# 记录项目是通过用户操作启动的
def start_by_user(project_id):
    file_path = "{}/data/push/tips/project_stop.json".format(public.get_panel_path())
    if not os.path.exists(file_path):
        data = {}
    else:
        data_content = public.readFile(file_path)
        try:
            data = json.loads(data_content)
        except json.JSONDecodeError:
            data = {}
    data[str(project_id)] = False
    public.writeFile(file_path, json.dumps(data))


def is_stop_by_user(project_id):
    file_path = "{}/data/push/tips/project_stop.json".format(public.get_panel_path())
    if not os.path.exists(file_path):
        data = {}
    else:
        data_content = public.readFile(file_path)
        try:
            data = json.loads(data_content)
        except json.JSONDecodeError:
            data = {}
    if str(project_id) not in data:
        return False
    return data[str(project_id)]

# # 内置项目复制Tomcat
# def check_and_copy_tomcat(version: int):
#     old_path = "/usr/local/bttomcat/tomcat_bak%d"
#     new_path = "/usr/local/bt_mod_tomcat/tomcat%d"
#     if not os.path.exists("/usr/local/bt_mod_tomcat"):
#         os.makedirs("/usr/local/bt_mod_tomcat", 0o755)
#
#     src_path = old_path % version
#     if not os.path.exists(old_path % version) or not os.path.isfile(src_path + '/conf/server.xml'):
#         return
#     if os.path.exists(new_path % version):
#         return
#     else:
#         os.makedirs(new_path % version)
#
#     public.ExecShell('cp -r %s/* %s ' % (src_path, new_path % version,))
#     t = bt_tomcat(version)
#     if t:
#         t.reset_tomcat_server_config(8330 + version - 6)


# def tomcat_install_status() -> List[dict]:
#     res_list = []
#     install_path = "/usr/local/bttomcat/tomcat_bak%d"
#     for i in range(7, 11):
#         src_path = install_path % i
#         start_path = src_path + '/bin/daemon.sh'
#         conf_path = src_path + '/conf/server.xml'
#         if os.path.exists(src_path) and os.path.isfile(start_path) and os.path.isfile(conf_path):
#             res_list.append({"version": i, "installed": True})
#         else:
#             res_list.append({"version": i, "installed": False})
#     return res_list

