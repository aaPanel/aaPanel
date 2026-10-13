# coding: utf-8
# -------------------------------------------------------------------
# aaPanel
# -------------------------------------------------------------------

import copy
import hashlib
import hmac
import json
import os
import re
import requests
import shlex
import sys
import threading
import time
import uuid

try:
    from urllib.parse import urlencode
except ImportError:
    from urllib import urlencode

if "/www/server/panel/class" not in sys.path:
    sys.path.append("/www/server/panel/class")

import public


class main:
    APP_NAME = "billionmail"
    APP_TYPE = "Email"
    PROXY_PREFIX = "/billionmail"
    DEFAULT_SERVICE_NAME = "billionmail"
    DEFAULT_ADMIN_USERNAME = "billion"
    LEGACY_MAIL_PLUGIN_PATH = "/www/server/panel/plugin/mail_sys"
    VMAIL_PATH = "/www/vmail"
    HOST_MAIL_SERVICES = ("postfix", "dovecot")
    INSTALL_STATUS_FILE = "/tmp/billionmail_install.log"
    INSTALL_LOCK_FILE = "/tmp/billionmail_install.lock"
    DOCKER_INSTALL_TIMEOUT = 1800
    BILLIONMAIL_START_TIMEOUT = 420
    DEFAULT_PORTS = {
        "HTTPS_PORT": "41443",
        "HTTP_PORT": "8080",
        "SMTP_PORT": "25",
        "SMTPS_PORT": "465",
        "SUBMISSION_PORT": "587",
        "IMAP_PORT": "143",
        "IMAPS_PORT": "993",
        "POP_PORT": "110",
        "POPS_PORT": "995",
    }
    MAIL_SERVICE_PORTS = {
        "postfix": (25, 465, 587),
        "dovecot": (110, 143, 993, 995),
    }
    SECRET_WORDS = ("PASSWORD", "PASS", "TOKEN", "SECRET", "KEY", "SALT")

    def _ok(self, data):
        return public.return_message(0, 0, data)

    def _err(self, message):
        return public.return_message(-1, 0, message)

    @staticmethod
    def _as_text(value):
        if value is None:
            return ""
        return str(value).strip()

    @staticmethod
    def _bool_int(value, default=1):
        if value is None or value == "":
            return default
        if isinstance(value, bool):
            return 1 if value else 0
        value = str(value).strip().lower()
        if value in ("1", "true", "yes", "on"):
            return 1
        if value in ("0", "false", "no", "off"):
            return 0
        return default

    @staticmethod
    def _valid_service_name(service_name):
        return re.match(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,63}$", service_name or "") is not None

    def _is_secret_key(self, key):
        key = (key or "").upper()
        return any(word in key for word in self.SECRET_WORDS)

    def _mask_value(self, key, value):
        if value in (None, ""):
            return value
        return "******" if self._is_secret_key(key) else value

    def _mask_text(self, text):
        if not text:
            return ""
        for key in ("ADMIN_PASSWORD", "DBPASS", "REDISPASS", "API_TOKEN", "SECRET_KEY", "JWT_SECRET"):
            text = re.sub(r"({}=).*".format(re.escape(key)), r"\1******", text)
        return text

    def _project_path(self):
        dk_project_path = "/www/dk_project"
        project_path_file = "{}/class_v2/btdockerModelV2/config/project_path.pl".format(public.get_panel_path())
        path = public.readFile(project_path_file)
        if path:
            dk_project_path = path.strip()
        return os.path.join(dk_project_path, "dk_app")

    def _installed_json_file(self):
        return os.path.join(self._project_path(), "installed.json")

    def _confirm_file(self):
        return os.path.join(public.get_panel_path(), "data", "billionmail_vmail_confirm.json")

    def _read_json(self, filename, default=None):
        if default is None:
            default = {}
        try:
            data = public.readFile(filename)
            if not data:
                return default
            return json.loads(data)
        except Exception:
            return default

    def _write_json(self, filename, data):
        try:
            dirname = os.path.dirname(filename)
            if dirname and not os.path.exists(dirname):
                os.makedirs(dirname)
            return public.writeFile(filename, json.dumps(data, indent=2))
        except Exception:
            return False

    def _all_installed_apps(self):
        installed_json = self._read_json(self._installed_json_file(), {})
        apps = []
        if isinstance(installed_json, dict):
            for app_list in installed_json.values():
                if isinstance(app_list, list):
                    apps.extend(app_list)
        return apps

    def _find_installed_app(self, service_name=None, app_id=None):
        service_name = self._as_text(service_name)
        app_id = self._as_text(app_id)
        matches = []
        for app in self._all_installed_apps():
            if app.get("appname") != self.APP_NAME:
                continue
            if service_name and app.get("service_name") != service_name:
                continue
            if app_id and app.get("id") != app_id:
                continue
            matches.append(app)
        if not matches:
            return None
        matches.sort(key=lambda item: int(item.get("createat", 0) or 0), reverse=True)
        return copy.deepcopy(matches[0])

    def _service_path(self, app):
        return os.path.join(app.get("path", ""), app.get("service_name", ""))

    def _compose_file(self, app):
        return os.path.join(self._service_path(app), "docker-compose.yml")

    def _env_file(self, app):
        return os.path.join(self._service_path(app), ".env")

    def _app_info_map(self, app):
        info = {}
        for item in app.get("appinfo") or []:
            key = item.get("fieldKey")
            if key:
                info[key] = item.get("fieldValue")
        return info

    def _read_env(self, app, mask=False):
        env = {}
        env_file = self._env_file(app)
        content = public.readFile(env_file)
        if not content:
            return env
        for raw_line in content.splitlines():
            line = raw_line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            key = key.strip()
            value = value.strip().strip('"').strip("'")
            env[key] = self._mask_value(key, value) if mask else value
        return env

    def _write_env_value(self, app, key, value):
        env_file = self._env_file(app)
        content = public.readFile(env_file)
        if content is None:
            content = ""

        lines = content.splitlines()
        updated = False
        new_lines = []
        for raw_line in lines:
            line = raw_line.strip()
            if line and not line.startswith("#") and "=" in line:
                env_key = line.split("=", 1)[0].strip()
                if env_key == key:
                    new_lines.append("{}={}".format(key, value))
                    updated = True
                    continue
            new_lines.append(raw_line)

        if not updated:
            if new_lines and new_lines[-1].strip():
                new_lines.append("")
            new_lines.append("{}={}".format(key, value))

        return public.writeFile(env_file, "\n".join(new_lines) + "\n")

    @staticmethod
    def _first_value(*values):
        for value in values:
            if value not in (None, ""):
                return str(value)
        return ""

    def _port_from_app(self, app, key):
        info = self._app_info_map(app)
        env = self._read_env(app, mask=False)
        return self._first_value(info.get(key), env.get(key))

    def _direct_console_url(self, app):
        https_port = self._port_from_app(app, "HTTPS_PORT")
        http_port = self._port_from_app(app, "HTTP_PORT")
        ip_addr = public.GetLocalIp()
        if https_port:
            return "https://{}:{}".format(ip_addr, https_port)
        if http_port:
            return "http://{}:{}".format(ip_addr, http_port)
        return ""

    def _proxy_target(self, app):
        https_port = self._port_from_app(app, "HTTPS_PORT")
        http_port = self._port_from_app(app, "HTTP_PORT")
        if https_port:
            return {
                "scheme": "https",
                "host": "127.0.0.1",
                "port": https_port,
                "base_url": "https://127.0.0.1:{}".format(https_port),
            }
        if http_port:
            return {
                "scheme": "http",
                "host": "127.0.0.1",
                "port": http_port,
                "base_url": "http://127.0.0.1:{}".format(http_port),
            }
        return {}

    def _masked_appinfo(self, app):
        appinfo = []
        for item in app.get("appinfo") or []:
            row = dict(item)
            row["fieldValue"] = self._mask_value(row.get("fieldKey"), row.get("fieldValue"))
            appinfo.append(row)
        return appinfo

    def _format_app(self, app, include_secret=False, include_env=False):
        if not app:
            return {
                "installed": False,
                # "console_url": self.PROXY_PREFIX + "/",
                # "api_prefix": self.PROXY_PREFIX + "/api",
            }
        info = self._app_info_map(app)
        env = self._read_env(app, mask=False)
        ports = {}
        for key in self.DEFAULT_PORTS:
            ports[key] = self._port_from_app(app, key)

        admin_username = self._first_value(env.get("ADMIN_USERNAME"), info.get("ADMIN_USERNAME"))
        admin_password = self._first_value(env.get("ADMIN_PASSWORD"), info.get("ADMIN_PASSWORD"))
        sso_secret = self._first_value(env.get("AAPANEL_SSO_SECRET"), info.get("AAPANEL_SSO_SECRET"))
        direct_console_url = self._direct_console_url(app)
        data = {
            "installed": True,
            "id": app.get("id"),
            "service_name": app.get("service_name"),
            "appname": app.get("appname"),
            "apptitle": app.get("apptitle"),
            "status": app.get("status"),
            "version": app.get("version"),
            "m_version": app.get("m_version"),
            "s_version": app.get("s_version"),
            "createat": app.get("createat"),
            "path": self._service_path(app),
            "ports": ports,
            "admin": {
                "username": admin_username,
                "password": admin_password if include_secret else self._mask_value("ADMIN_PASSWORD", admin_password),
            },
            "sso": {
                "enabled": bool(sso_secret),
                "endpoint": "/v2/mod/mail/billionmail/sso",
            },
            "console_url": self.PROXY_PREFIX + "/",
            "api_prefix": self.PROXY_PREFIX + "/api",
            "direct_console_url": direct_console_url,
            "webmail_url": direct_console_url.rstrip("/") + "/roundcube" if direct_console_url else "",
            "proxy_target": self._proxy_target(app),
            "installed_log": os.path.join("/tmp", "{}.log".format(app.get("service_name", ""))),
            "appinfo": app.get("appinfo") if include_secret else self._masked_appinfo(app),
        }
        if include_env:
            data["env"] = self._read_env(app, mask=not include_secret)
        return data

    def _manager_app(self, service_name=None):
        try:
            from mod.project.docker.app.appManageMod import AppManage
            args = public.to_dict_obj({"app_type": self.APP_TYPE, "row": 10000, "p": 1})
            result = AppManage().get_installed_apps(args)
            message = result.get("message", {})
            data = message.get("data", []) if isinstance(message, dict) else []
            for app in data:
                if app.get("appname") != self.APP_NAME:
                    continue
                if service_name and app.get("service_name") != service_name:
                    continue
                return app
        except Exception:
            pass
        return None

    def _validate_port(self, key, value):
        value = self._as_text(value)
        try:
            port = int(value)
        except Exception:
            return None, "{} must be a valid port".format(key)
        if port < 1 or port > 65535:
            return None, "{} must be between 1 and 65535".format(key)
        return str(port), None

    def _ports_from_get(self, get):
        ports = {}
        for key, default_value in self.DEFAULT_PORTS.items():
            value = get.get(key, get.get(key.lower(), default_value))
            value, err = self._validate_port(key, value)
            if err:
                return None, err
            ports[key] = value
        return ports, None

    def _guess_mail_service(self, port, process_name=""):
        process_name = (process_name or "").lower()
        if "postfix" in process_name:
            return "postfix"
        if "dovecot" in process_name:
            return "dovecot"
        try:
            port = int(port)
        except Exception:
            return ""
        for service, service_ports in self.MAIL_SERVICE_PORTS.items():
            if port in service_ports:
                if service == "postfix" and process_name in ("master", "smtpd", "pickup", "qmgr"):
                    return service
                if service == "dovecot" and process_name in ("dovecot", "imap", "imap-login", "pop3", "pop3-login"):
                    return service
        return ""

    def _decorate_port_conflict(self, conflict):
        row = dict(conflict)
        service = self._guess_mail_service(row.get("port"), row.get("process_name"))
        row["service"] = service
        row["can_stop"] = row.get("source") == "process" and service in self.HOST_MAIL_SERVICES
        return row

    def _port_conflicts(self, ports):
        conflicts = []
        port_set = set(int(port) for port in ports.values())
        for app in self._all_installed_apps():
            for item in app.get("port") or []:
                try:
                    item_port = int(item)
                except Exception:
                    continue
                if item_port in port_set:
                    conflicts.append({
                        "port": item_port,
                        "source": "docker_app",
                        "service_name": app.get("service_name"),
                        "appname": app.get("appname"),
                    })
        try:
            import psutil
            for conn in psutil.net_connections("tcp4"):
                if not conn.laddr:
                    continue
                if conn.laddr.port not in port_set:
                    continue
                process_name = ""
                if conn.pid:
                    try:
                        process_name = psutil.Process(conn.pid).name()
                    except Exception:
                        process_name = ""
                conflicts.append({
                    "port": conn.laddr.port,
                    "source": "process",
                    "pid": conn.pid,
                    "process_name": process_name,
                    })
        except Exception:
            pass
        return [self._decorate_port_conflict(conflict) for conflict in conflicts]

    def _port_precheck(self, ports):
        conflicts = self._port_conflicts(ports)
        return {
            "ok": len(conflicts) == 0,
            # "checked_ports": dict((key, int(value)) for key, value in ports.items()),
            "conflicts": conflicts,
        }

    @staticmethod
    def _parse_os_release(content):
        data = {}
        if not content:
            return data
        for raw_line in content.splitlines():
            line = raw_line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            data[key] = value.strip().strip('"').strip("'")
        return data

    @staticmethod
    def _version_tuple(version):
        parts = re.findall(r"\d+", version or "")
        return tuple(int(item) for item in parts[:3])

    @staticmethod
    def _version_gte(version, target):
        value = list(main._version_tuple(version))
        target_value = list(target)
        length = max(len(value), len(target_value))
        value += [0] * (length - len(value))
        target_value += [0] * (length - len(target_value))
        return tuple(value) >= tuple(target_value)

    def _system_precheck(self):
        """
        检查系统信息
        """
        release = self._parse_os_release(public.readFile("/etc/os-release"))
        os_id = (release.get("ID") or "").lower()
        version_id = release.get("VERSION_ID", "")
        is_ubuntu_24 = os_id == "ubuntu" and self._version_gte(version_id, (24, 4))
        is_debian_13 = os_id == "debian" and self._version_gte(version_id, (13,))
        billionmail_only = is_ubuntu_24 or is_debian_13
        warning = ""
        if billionmail_only:
            warning = (
                "The current OS version is not compatible with the legacy mail_sys plugin. "
                "BillionMail installation is recommended."
            )
        return {
            # "id": os_id,
            "name": release.get("NAME", ""),
            "version": release.get("VERSION", ""),
            # "version_id": version_id,
            # "major": self._version_tuple(version_id)[0] if self._version_tuple(version_id) else 0,
            "billionmail_only": billionmail_only,
            "warning": warning,
            # "raw": release,
        }

    def _docker_status(self):
        docker = {
            "installed": None,
            "running": None,
            "error": "",
        }
        try:
            from btdockerModelV2 import setupModel as ds
            setup = ds.main()
            docker["running"] = bool(setup.get_service_status())
            docker["installed"] = bool(setup.check_docker_service())
        except Exception as ex:
            docker["error"] = str(ex)
        return docker

    def _docker_setup_model(self):
        from btdockerModelV2 import setupModel as ds
        return ds.main()

    def _is_success(self, result):
        return isinstance(result, dict) and result.get("status") == 0

    def _ensure_docker_ready(self, install_if_missing=False):
        try:
            setup = self._docker_setup_model()
            installed = bool(setup.check_docker_service())
            running = bool(setup.get_service_status())
        except Exception as ex:
            return False, self._err("Failed to check Docker service: {}".format(str(ex)))

        if not installed:
            if not install_if_missing:
                return False, self._err("Docker is not installed.")
            try:
                installing = public.M('tasks').where('name=? and status=?', ("Install Docker Service", "-1")).count()
            except Exception:
                installing = 0
            if installing:
                return False, self._ok({
                    "docker_installing": True,
                    "docker": self._docker_status(),
                    "result": "Docker installation task already exists.",
                    "notice": "Docker is being installed. Please retry BillionMail installation after Docker is ready.",
                })
            try:
                result = setup.install_docker_program(public.to_dict_obj({
                    "url": "",
                    "type": 0,
                }))
            except Exception as ex:
                return False, self._err("Failed to add Docker installation task: {}".format(str(ex)))

            message = result.get("message", result) if isinstance(result, dict) else result
            if self._is_success(result) or "installation task already exists" in str(message).lower():
                return False, self._ok({
                    "docker_installing": True,
                    "docker": self._docker_status(),
                    "result": message,
                    "notice": "Docker installation task has been queued. Please retry BillionMail installation after Docker is ready.",
                })
            return False, self._err("Failed to add Docker installation task: {}".format(message))

        if not running:
            try:
                result = setup.docker_service(public.to_dict_obj({"act": "start"}))
            except Exception as ex:
                return False, self._err("Failed to start Docker service: {}".format(str(ex)))
            if not self._is_success(result):
                message = result.get("message", result) if isinstance(result, dict) else result
                return False, self._err("Failed to start Docker service: {}".format(message))
            for _ in range(5):
                if setup.get_service_status():
                    return True, None
                time.sleep(1)
            return False, self._err("Docker service start command succeeded, but Docker is not running yet.")

        return True, None

    def _docker_install_task_exists(self):
        try:
            count = public.M('tasks').where('name=? and status=?', ("Install Docker Service", "-1")).count()
            if count:
                return True
            count = public.M('tasks').where('name=? and status=?', ("Install Docker Service", "0")).count()
            return bool(count)
        except Exception:
            return False

    def _install_progress_template(self):
        return {
            "status": 0,
            "progress": 0,
            "result": {},
            "type": self.APP_NAME,
            "steps": [
                {
                    "status": 2,
                    "error": "",
                    "ps": "Waiting to install Docker...",
                    "title": "Install Docker",
                },
                {
                    "status": 2,
                    "error": "",
                    "ps": "Waiting to install Docker Compose...",
                    "title": "Install Docker Compose",
                },
                {
                    "status": 2,
                    "error": "",
                    "ps": "Waiting to install BillionMail...",
                    "title": "Install BillionMail",
                },
            ],
        }

    def _read_install_progress(self):
        data = self._read_json(self.INSTALL_STATUS_FILE, None)
        if not isinstance(data, dict) or "steps" not in data:
            return self._install_progress_template()
        return data

    def _write_install_progress(self, data):
        public.writeFile(self.INSTALL_STATUS_FILE, json.dumps(data, ensure_ascii=False))

    def _clear_install_progress(self):
        try:
            if os.path.exists(self.INSTALL_STATUS_FILE):
                os.remove(self.INSTALL_STATUS_FILE)
        except Exception:
            pass

    def _compact_install_result(self, result):
        if not isinstance(result, dict):
            return {"message": result} if result not in (None, "") else {}

        result = dict(result)
        result.pop("billionmail", None)

        create_result = result.pop("result", None)
        if "message" not in result and create_result not in (None, ""):
            if isinstance(create_result, dict) and set(create_result.keys()) == {"result"}:
                create_result = create_result.get("result")
            result["message"] = create_result
        return result

    def _install_result_app_summary(self, app_data):
        if not isinstance(app_data, dict) or not app_data.get("installed"):
            return {}

        summary = {}
        for key in ("status", "version", "path", "installed_log"):
            value = app_data.get(key)
            if value not in (None, ""):
                summary[key] = value
        return summary

    def _current_install_status(self):
        data = self._read_install_progress()
        try:
            progress = int(data.get("progress", 0) or 0)
        except Exception:
            progress = 0
        try:
            status = int(data.get("status", 0) or 0)
        except Exception:
            status = 0

        # steps = data.get("steps", [])
        # if not isinstance(steps, list):
        #     steps = []

        # def step_status(index):
        #     if 0 <= index < len(steps) and isinstance(steps[index], dict):
        #         try:
        #             return int(steps[index].get("status", 2))
        #         except Exception:
        #             return 2
        #     return 2

        lock_exists = os.path.exists(self.INSTALL_LOCK_FILE)
        installing = status == 0 and (lock_exists or 0 < progress < 100)
        # docker_installing = installing and (
        #     progress < 55 or step_status(0) == 0 or step_status(1) == 0
        # )
        # billionmail_installing = installing and (
        #     progress >= 55 or step_status(2) == 0
        # )


        # return {
        #     "installing": bool(installing),
        #     "docker": bool(docker_installing),
        #     "billionmail": bool(billionmail_installing),
        #     "progress": progress,
        #     "status": status,
        #     "completed": bool(status == 1 or progress >= 100),
        #     "failed": bool(status == -1),
        #     "progress_url": "/v2/mod/mail/billionmail/install_progress",
        # }


        return bool(installing)

    def _init_install_progress(self):
        data = self._install_progress_template()
        self._write_install_progress(data)
        return data

    def _update_install_progress(self, step_index, ps, progress, status=0, error_msg="", result=None):
        data = self._read_install_progress()
        steps = data.get("steps", [])
        if 0 <= step_index < len(steps):
            steps[step_index]["status"] = status
            steps[step_index]["ps"] = str(ps)
            steps[step_index]["error"] = str(error_msg or "")
            if status == 1 and step_index + 1 < len(steps) and steps[step_index + 1].get("status") == 2:
                steps[step_index + 1]["status"] = 0
        data["progress"] = max(0, min(100, int(progress)))
        if status == -1:
            data["status"] = -1
        if result is not None:
            data["result"] = result
        if all(item.get("status") == 1 for item in steps):
            data["status"] = 1
            data["progress"] = 100
        self._write_install_progress(data)
        return data

    def _queue_docker_install_if_needed(self, setup):
        if self._docker_install_task_exists():
            return True, "Docker installation task already exists."
        result = setup.install_docker_program(public.to_dict_obj({
            "url": "",
            "type": 0,
        }))
        message = result.get("message", result) if isinstance(result, dict) else result
        if self._is_success(result):
            return True, message
        return False, message

    def _wait_until(self, checker, timeout, interval=3, on_tick=None):
        start_time = time.time()
        while time.time() - start_time <= timeout:
            try:
                if checker():
                    return True
            except Exception:
                pass
            if on_tick:
                on_tick(time.time() - start_time, timeout)
            time.sleep(interval)
        return False

    def _prepare_docker_for_install(self):
        setup = self._docker_setup_model()

        self._update_install_progress(0, "Checking Docker service...", 5, 0)
        if not setup.check_docker_service():
            ok, message = self._queue_docker_install_if_needed(setup)
            if not ok:
                self._update_install_progress(0, "Docker installation failed.", 5, -1, message)
                return False, message

            def docker_tick(elapsed, timeout):
                progress = 5 + int(min(25, elapsed * 25 / max(timeout, 1)))
                self._update_install_progress(0, "Installing Docker...", progress, 0)

            if not self._wait_until(
                    lambda: setup.check_docker_service() and not self._docker_install_task_exists(),
                    self.DOCKER_INSTALL_TIMEOUT,
                    5,
                    docker_tick
            ):
                message = "Docker installation timed out."
                self._update_install_progress(0, message, 30, -1, message)
                return False, message
        elif self._docker_install_task_exists():
            def docker_task_tick(elapsed, timeout):
                progress = 5 + int(min(25, elapsed * 25 / max(timeout, 1)))
                self._update_install_progress(0, "Waiting for Docker installation task to finish...", progress, 0)

            if not self._wait_until(
                    lambda: not self._docker_install_task_exists(),
                    self.DOCKER_INSTALL_TIMEOUT,
                    5,
                    docker_task_tick
            ):
                message = "Docker installation task timed out."
                self._update_install_progress(0, message, 30, -1, message)
                return False, message

        self._update_install_progress(0, "Docker installation successful!", 35, 1)

        self._update_install_progress(1, "Checking Docker Compose and starting Docker service...", 40, 0)
        compose_ok, compose_path = setup.check_docker_compose_service()
        if not compose_ok:
            ok, message = self._queue_docker_install_if_needed(setup)
            if not ok:
                self._update_install_progress(1, "Docker Compose installation failed.", 40, -1, message)
                return False, message

            def compose_tick(elapsed, timeout):
                progress = 40 + int(min(10, elapsed * 10 / max(timeout, 1)))
                self._update_install_progress(1, "Installing Docker Compose...", progress, 0)

            if not self._wait_until(
                    lambda: setup.check_docker_compose_service()[0] and not self._docker_install_task_exists(),
                    self.DOCKER_INSTALL_TIMEOUT,
                    5,
                    compose_tick
            ):
                message = "Docker Compose installation timed out."
                self._update_install_progress(1, message, 50, -1, message)
                return False, message
            compose_ok, compose_path = setup.check_docker_compose_service()
        elif self._docker_install_task_exists():
            def compose_task_tick(elapsed, timeout):
                progress = 40 + int(min(10, elapsed * 10 / max(timeout, 1)))
                self._update_install_progress(1, "Waiting for Docker Compose installation task to finish...", progress, 0)

            if not self._wait_until(
                    lambda: not self._docker_install_task_exists(),
                    self.DOCKER_INSTALL_TIMEOUT,
                    5,
                    compose_task_tick
            ):
                message = "Docker Compose installation task timed out."
                self._update_install_progress(1, message, 50, -1, message)
                return False, message

        if not setup.get_service_status():
            last_message = ""

            def start_docker_service():
                nonlocal last_message
                if setup.get_service_status():
                    return True
                result = setup.docker_service(public.to_dict_obj({"act": "start"}))
                if not self._is_success(result):
                    last_message = result.get("message", result) if isinstance(result, dict) else result
                    return False
                return setup.get_service_status()

            def service_tick(elapsed, timeout):
                progress = 45 + int(min(5, elapsed * 5 / max(timeout, 1)))
                self._update_install_progress(1, "Starting Docker service...", progress, 0, last_message)

            if not self._wait_until(start_docker_service, 180, 5, service_tick):
                message = last_message or "Docker service start command succeeded, but Docker is not running yet."
                self._update_install_progress(1, "Docker service startup failed.", 50, -1, message)
                return False, message

        self._update_install_progress(1, "Docker Compose installation successful!", 55, 1)
        return True, compose_path

    def _wait_billionmail_started(self, service_name):
        log_file = os.path.join("/tmp", "{}.log".format(service_name))

        def checker():
            content = public.readFile(log_file) or ""
            if "bt_failed" in content:
                raise RuntimeError(self._mask_text(content[-2000:]))
            return "bt_successful" in content

        start_time = time.time()
        while time.time() - start_time <= self.BILLIONMAIL_START_TIMEOUT:
            try:
                if checker():
                    return True, ""
            except RuntimeError as ex:
                return False, str(ex)
            elapsed = time.time() - start_time
            progress = 75 + int(min(20, elapsed * 20 / max(self.BILLIONMAIL_START_TIMEOUT, 1)))
            self._update_install_progress(2, "Waiting for BillionMail containers to start...", progress, 0)
            time.sleep(3)
        return False, "BillionMail startup timed out. Please check {}.".format(log_file)

    def _install_worker(self, args_data, started=None):
        public.writeFile(self.INSTALL_LOCK_FILE, str(threading.get_ident()))
        if started:
            started.set()
        self._init_install_progress()
        try:
            ok, message = self._prepare_docker_for_install()
            if not ok:
                return

            args = public.to_dict_obj(args_data)
            self._update_install_progress(2, "Creating BillionMail application...", 60, 0)
            from mod.project.docker.app.appManageMod import AppManage
            result = AppManage().create_app(args)
            if result.get("status") == -1:
                message = result.get("message", result)
                self._update_install_progress(2, "BillionMail installation failed.", 70, -1, message)
                return

            ok, message = self._wait_billionmail_started(args.service_name)
            if not ok:
                self._update_install_progress(2, "BillionMail startup failed.", 95, -1, message)
                return

            app = self._manager_app(args.service_name) or self._find_installed_app(service_name=args.service_name)
            app_summary = self._install_result_app_summary(self._format_app(app))
            create_message = self._compact_install_result({
                "result": result.get("message", result),
            }).get("message")
            final_result = {
                "service_name": args.service_name,
                "console_url": self.PROXY_PREFIX + "/",
                "api_prefix": self.PROXY_PREFIX + "/api",
                "admin": {
                    "username": args.ADMIN_USERNAME,
                    "password": args.ADMIN_PASSWORD,
                },
                "message": create_message,
            }
            final_result.update(app_summary)
            final_result["docker"] = self._docker_status()
            self._update_install_progress(2, "BillionMail installation successful!", 100, 1, result=final_result)
        except Exception as ex:
            self._update_install_progress(2, "BillionMail installation failed.", 95, -1, str(ex))
        finally:
            public.progress_release_lock(self.INSTALL_LOCK_FILE)

    def _vmail_snapshot(self):
        path = self.VMAIL_PATH
        snapshot = {
            "path": path,
            "exists": os.path.exists(path),
            "is_dir": os.path.isdir(path),
            "empty": True,
            "has_mail_data": False,
            "file_count": 0,
            "dir_count": 0,
            "size": 0,
            "mtime": 0,
            "scan_limited": False,
            "top_entries": [],
            "error": "",
        }
        if not snapshot["exists"]:
            return snapshot
        try:
            snapshot["mtime"] = int(os.path.getmtime(path))
            if not snapshot["is_dir"]:
                snapshot["empty"] = False
                snapshot["has_mail_data"] = True
                snapshot["file_count"] = 1
                snapshot["size"] = os.path.getsize(path)
                return snapshot

            top_entries = os.listdir(path)
            snapshot["top_entries"] = top_entries[:20]
            max_scan = 10000
            for root, dirs, files in os.walk(path):
                snapshot["dir_count"] += len(dirs)
                snapshot["file_count"] += len(files)
                for filename in files:
                    try:
                        snapshot["size"] += os.path.getsize(os.path.join(root, filename))
                    except Exception:
                        pass
                if snapshot["dir_count"] + snapshot["file_count"] >= max_scan:
                    snapshot["scan_limited"] = True
                    break
            snapshot["empty"] = snapshot["dir_count"] == 0 and snapshot["file_count"] == 0
            snapshot["has_mail_data"] = not snapshot["empty"]
        except Exception as ex:
            snapshot["error"] = str(ex)
            snapshot["empty"] = False
            snapshot["has_mail_data"] = True
        return snapshot

    @staticmethod
    def _vmail_signature(snapshot):
        payload = {
            "path": snapshot.get("path", ""),
            "exists": snapshot.get("exists", False),
            "is_dir": snapshot.get("is_dir", False),
            "file_count": snapshot.get("file_count", 0),
            "dir_count": snapshot.get("dir_count", 0),
            "size": snapshot.get("size", 0),
            "mtime": snapshot.get("mtime", 0),
        }
        return hashlib.sha256(json.dumps(payload, sort_keys=True).encode("utf-8")).hexdigest()

    def _vmail_confirmation(self, snapshot):
        record = self._read_json(self._confirm_file(), {})
        if not isinstance(record, dict):
            record = {}
        signature = self._vmail_signature(snapshot)
        confirmed = bool(record.get("confirmed_empty")) and record.get("signature") == signature
        return confirmed, record if confirmed else {}

    def _legacy_mail_precheck(self):
        """
        检查是否新用户(未安装旧版邮局)
        """
        vmail = self._vmail_snapshot()
        confirmed_empty, confirmation = self._vmail_confirmation(vmail)
        mail_sys_installed = os.path.exists(self.LEGACY_MAIL_PLUGIN_PATH)
        is_new_user = (not mail_sys_installed) and (
            (not vmail.get("exists")) or (not vmail.get("has_mail_data")) or confirmed_empty
        )
        return {
            "mail_sys_installed": mail_sys_installed,
            # "mail_sys_path": self.LEGACY_MAIL_PLUGIN_PATH,
            # "vmail_exists": vmail.get("exists"),
            # "vmail_path": self.VMAIL_PATH,
            # "vmail_empty": vmail.get("empty"),
            # "vmail_size": vmail.get("size"),
            # "vmail_file_count": vmail.get("file_count"),
            # "vmail_dir_count": vmail.get("dir_count"),
            # "has_mail_data": vmail.get("has_mail_data"),
            # "confirmed_empty": confirmed_empty,
            # "confirmation": confirmation,
            "is_new_user": is_new_user,
            # "snapshot": vmail,
        }

    def _install_args(self, get):
        service_name = self._as_text(get.get("service_name", self.DEFAULT_SERVICE_NAME))
        if not self._valid_service_name(service_name):
            return None, self._err("Invalid service_name. Use letters, numbers, dot, underscore or hyphen.")

        ports, err = self._ports_from_get(get)
        if err:
            return None, self._err(err)

        conflicts = self._port_conflicts(ports)
        if conflicts:
            return None, self._err({"error": "Port conflict detected", "conflicts": conflicts})

        admin_username = self._as_text(
            get.get("ADMIN_USERNAME", get.get("admin_username", self.DEFAULT_ADMIN_USERNAME))
        ) or self.DEFAULT_ADMIN_USERNAME
        admin_password = self._as_text(get.get("ADMIN_PASSWORD", get.get("admin_password", "")))
        if not admin_password or admin_password == "billion":
            admin_password = public.GetRandomString(20)
        sso_secret = self._as_text(get.get("AAPANEL_SSO_SECRET", get.get("aapanel_sso_secret", "")))
        if not sso_secret:
            sso_secret = public.GetRandomString(48)

        args = {
            "app_name": self.APP_NAME,
            "service_name": service_name,
            "m_version": self._as_text(get.get("m_version", "latest")) or "latest",
            "s_version": self._as_text(get.get("s_version", "")),
            "allow_access": str(self._bool_int(get.get("allow_access", 1), 1)),
            "disable_domain": str(self._bool_int(get.get("disable_domain", 1), 1)),
            "domain": self._as_text(get.get("domain", "")),
            "cpus": self._as_text(get.get("cpus", "0")) or "0",
            "memory_limit": self._as_text(get.get("memory_limit", "0")) or "0",
            "ADMIN_USERNAME": admin_username,
            "ADMIN_PASSWORD": admin_password,
            "AAPANEL_SSO_SECRET": sso_secret,
        }
        args.update(ports)
        return public.to_dict_obj(args), None

    def _target_app(self, get):
        service_name = get.get("service_name", None)
        app_id = get.get("id", None)
        return self._find_installed_app(service_name=service_name, app_id=app_id)

    def _control_app(self):
        return self._manager_app() or self._find_installed_app()

    def _billionmail_default_app_info(self):
        try:
            from mod.project.docker.app.appManageMod import AppManage
            args = public.to_dict_obj({
                "p": 1,
                "row": 20000,
                "query": "BillionMail",
                "app_type": self.APP_TYPE,
            })
            result = AppManage().get_apps(args)
            if not isinstance(result, dict) or result.get("status") != 0:
                return None

            message = result.get("message", {})
            data = message.get("data", []) if isinstance(message, dict) else result.get("data", [])
            if not isinstance(data, list):
                return None

            for app in data:
                if isinstance(app, dict) and app.get("appname") == self.APP_NAME:
                    return app
            for app in data:
                if not isinstance(app, dict):
                    continue
                appname = self._as_text(app.get("appname")).lower()
                apptitle = self._as_text(app.get("apptitle")).lower()
                if self.APP_NAME in (appname, apptitle):
                    return app
        except Exception:
            pass
        return None

    def check_env(self, get):
        app = self._manager_app(get.get("service_name", None)) or self._target_app(get)
        return self._ok({
            "docker": self._docker_status(),
            "billionmail": self._format_app(app),
            "routes": {
                "control": "/v2/mod/mail/billionmail/<fun>",
                "sso": "/v2/mod/mail/billionmail/sso",
                "proxy": self.PROXY_PREFIX + "/",
                "api": self.PROXY_PREFIX + "/api",
            },
        })

    def status(self, get):
        app = self._manager_app(get.get("service_name", None)) or self._target_app(get)
        return self._ok(self._format_app(app))

    def precheck(self, get):
        ports, err = self._ports_from_get(get)
        if err:
            return self._err(err)

        docker = self._docker_status()
        system = self._system_precheck()
        legacy_mail = self._legacy_mail_precheck()
        app = self._manager_app(get.get("service_name", None)) or self._target_app(get)

        data = {
            "system": system,
            "docker": docker,
            "billionmail": self._format_app(app),
            "legacy_mail": legacy_mail,
            "install_status": self._current_install_status(),

        }
        return self._ok(data)

    def check_install(self, get):
        """
        安装前检查端口占用情况
        """
        ports, err = self._ports_from_get(get)
        if err:
            return self._err(err)
        port_result = self._port_precheck(ports)
        # 兜底数据
        port_result['app_info'] = {
  "appid": 226,
  "appname": "billionmail",
  "apptitle": "BillionMail",
  "apptype": "Email",
  "appTypeCN": "Email",
  "appversion": [
    {
      "m_version": "latest",
      "s_version": []
    }
  ],
  "appdesc": "BillionMail provides you with an open-source mail server, email marketing – fully self-hosted, developer-friendly, and free.",
  "appstatus": 1,
  "icon": "",
  "sort": 17,
  "home": "",
  "help": "https://www.billionmail.com/",
  "cpu": 0,
  "mem": 0,
  "disk": 10240,
  "updateat": 1722408250,
  "installed": False,
  "reuse": True,
  "depend": None,
  "field": [
    {
      "attr": "HTTPS_PORT",
      "name": "web port(Htpps)",
      "type": "number",
      "default": 41443,
      "suffix": "Once deployed, access via 'https://ip:port/'",
      "unit": ""
    },
    {
      "attr": "ADMIN_USERNAME",
      "name": "web user",
      "type": "text",
      "default": "billion",
      "suffix": "",
      "unit": ""
    },
    {
      "attr": "ADMIN_PASSWORD",
      "name": "web password",
      "type": "text",
      "default": "billion",
      "suffix": "",
      "unit": ""
    },
    {
      "attr": "allow_access",
      "name": "Allow external access",
      "type": "checkbox",
      "default": True,
      "suffix": "Allow direct access through the host IP+ port",
      "unit": ""
    },
    {
      "attr": "SMTP_PORT",
      "name": "SMTP_PORT",
      "type": "number",
      "default": 25,
      "suffix": "Make sure the port is not occupied",
      "unit": ""
    },
    {
      "attr": "SMTPS_PORT",
      "name": "SMTPS_PORT",
      "type": "number",
      "default": 465,
      "suffix": "Make sure the port is not occupied",
      "unit": ""
    },
    {
      "attr": "SUBMISSION_PORT",
      "name": "SUBMISSION_PORT",
      "type": "number",
      "default": 587,
      "suffix": "Make sure the port is not occupied",
      "unit": ""
    },
    {
      "attr": "IMAP_PORT",
      "name": "IMAP_PORT",
      "type": "number",
      "default": 143,
      "suffix": "Make sure the port is not occupied",
      "unit": ""
    },
    {
      "attr": "IMAPS_PORT",
      "name": "IMAPS_PORT",
      "type": "number",
      "default": 993,
      "suffix": "Make sure the port is not occupied",
      "unit": ""
    },
    {
      "attr": "POP_PORT",
      "name": "POP_PORT",
      "type": "number",
      "default": 110,
      "suffix": "Make sure the port is not occupied",
      "unit": ""
    },
    {
      "attr": "POPS_PORT",
      "name": "POPS_PORT",
      "type": "number",
      "default": 995,
      "suffix": "Make sure the port is not occupied",
      "unit": ""
    },
    {
      "attr": "HTTP_PORT",
      "name": "web port",
      "type": "number",
      "default": 8080,
      "suffix": "",
      "unit": ""
    }
  ],
  "env": [
    {
      "key": "version",
      "type": "string",
      "default": None,
      "desc": "version"
    },
    {
      "key": "SMTP_PORT",
      "type": "number",
      "default": None,
      "desc": "SMTP_PORT"
    },
    {
      "key": "SMTPS_PORT",
      "type": "number",
      "default": None,
      "desc": "SMTPS_PORT"
    },
    {
      "key": "SUBMISSION_PORT",
      "type": "number",
      "default": None,
      "desc": "SUBMISSION_PORT"
    },
    {
      "key": "IMAP_PORT",
      "type": "number",
      "default": None,
      "desc": "IMAP_PORT"
    },
    {
      "key": "IMAPS_PORT",
      "type": "number",
      "default": None,
      "desc": "IMAPS_PORT"
    },
    {
      "key": "POP_PORT",
      "type": "number",
      "default": None,
      "desc": "POP_PORT"
    },
    {
      "key": "POPS_PORT",
      "type": "number",
      "default": None,
      "desc": "POPS_PORT"
    },
    {
      "key": "HTTP_PORT",
      "type": "number",
      "default": None,
      "desc": "HTTP_PORT"
    },
    {
      "key": "HTTPS_PORT",
      "type": "number",
      "default": None,
      "desc": "HTTPS_PORT"
    },
    {
      "key": "ADMIN_USERNAME",
      "type": "string",
      "default": None,
      "desc": "ADMIN_USERNAME"
    },
    {
      "key": "ADMIN_PASSWORD",
      "type": "string",
      "default": None,
      "desc": "ADMIN_PASSWORD"
    },
    {
      "key": "app_path",
      "type": "path",
      "default": None,
      "desc": "app path"
    },
    {
      "key": "host_ip",
      "type": "string",
      "default": None,
      "desc": "host IP"
    }
  ],
  "volumes": {
    "data": {
      "type": "path",
      "desc": ""
    },
    "conf": {
      "type": "path",
      "desc": ""
    },
    "ssl-self-signed": {
      "type": "path",
      "desc": ""
    }
  },
  "installedCount": 0
}
        docker_app_info = self._billionmail_default_app_info()
        if docker_app_info:
            port_result["app_info"] = docker_app_info

        return self._ok(port_result)


    def confirm_vmail_empty(self, get):
        if self._bool_int(get.get("confirm", 0), 0) != 1:
            return self._err("confirm=1 is required.")

        snapshot = self._vmail_snapshot()
        signature = self._vmail_signature(snapshot)
        record = {
            "confirmed_empty": True,
            "signature": signature,
            "time": int(time.time()),
            "vmail_path": self.VMAIL_PATH,
            "snapshot": snapshot,
        }
        if not self._write_json(self._confirm_file(), record):
            return self._err("Failed to save vmail confirmation.")

        return self._ok({
            "confirmed_empty": True,
            "confirm_file": self._confirm_file(),
            "legacy_mail": self._legacy_mail_precheck(),
        })

    def resolve_ports(self, get):
        action = self._as_text(get.get("action", "stop_host_mail_services"))
        if action != "stop_host_mail_services":
            return self._err("Unsupported action: {}".format(action))
        if self._bool_int(get.get("confirm", 0), 0) != 1:
            return self._err("confirm=1 is required.")

        services_text = self._as_text(get.get("services", ",".join(self.HOST_MAIL_SERVICES)))
        requested_services = []
        for service in re.split(r"[,;\s]+", services_text):
            service = service.strip().lower()
            if not service:
                continue
            if service not in self.HOST_MAIL_SERVICES:
                return self._err("Unsupported service: {}".format(service))
            if service not in requested_services:
                requested_services.append(service)
        if not requested_services:
            return self._err("No services were specified.")

        ports, err = self._ports_from_get(get)
        if err:
            return self._err(err)

        ports_before = self._port_precheck(ports)
        stoppable_services = []
        for conflict in ports_before.get("conflicts", []):
            service = conflict.get("service")
            if conflict.get("can_stop") and service in requested_services and service not in stoppable_services:
                stoppable_services.append(service)

        stopped = []
        for service in stoppable_services:
            stdout, stderr = public.ExecShell("systemctl stop {}".format(service))
            if stderr and (
                "not found" in stderr.lower()
                or "could not be found" in stderr.lower()
                or "system has not been booted" in stderr.lower()
                or "failed to connect to bus" in stderr.lower()
            ):
                stdout2, stderr2 = public.ExecShell("service {} stop".format(service))
                stdout = "{}\n{}".format(stdout, stdout2).strip()
                stderr = "{}\n{}".format(stderr, stderr2).strip()
            stopped.append({
                "service": service,
                "success": not bool(stderr),
                "stdout": self._mask_text(stdout),
                "stderr": self._mask_text(stderr),
            })

        ports_after = self._port_precheck(ports)
        for row in stopped:
            service = row.get("service")
            still_occupied = any(
                item.get("service") == service and item.get("source") == "process"
                for item in ports_after.get("conflicts", [])
            )
            row["success"] = row.get("success") and not still_occupied

        return self._ok({
            "action": action,
            "requested_services": requested_services,
            "stoppable_services": stoppable_services,
            "ports_before": ports_before,
            "stopped": stopped,
            "ports_after": ports_after,
            "message": "No stoppable host mail services were found." if not stoppable_services else "",
        })

    def proxy_config(self, get):
        app = self._target_app(get)
        if not app:
            return self._ok(self._format_app(None))
        return self._ok(self.get_proxy_config(app.get("service_name")))

    def get_proxy_config(self, service_name=None):
        app = self._find_installed_app(service_name=service_name)
        if not app:
            return self._format_app(None)
        data = self._format_app(app)
        data["target_base"] = data.get("proxy_target", {}).get("base_url", "")
        return data

    def _sso_bridge_url(self, service_name=None, redirect=None):
        params = {}
        service_name = self._as_text(service_name)
        redirect = self._as_text(redirect)
        if service_name:
            params["service_name"] = service_name
        if redirect:
            params["redirect"] = redirect
        query = urlencode(params)
        url = self.PROXY_PREFIX + "/__aapanel_sso__"
        return url + ("?" + query if query else "")

    def _sso_secret(self, app):
        info = self._app_info_map(app)
        env = self._read_env(app, mask=False)
        return self._first_value(env.get("AAPANEL_SSO_SECRET"), info.get("AAPANEL_SSO_SECRET"))

    def _ensure_sso_secret(self, app):
        env = self._read_env(app, mask=False)
        secret = self._first_value(env.get("AAPANEL_SSO_SECRET"))
        if secret:
            return secret, False

        info = self._app_info_map(app)
        secret = self._first_value(info.get("AAPANEL_SSO_SECRET"))
        if secret:
            self._write_env_value(app, "AAPANEL_SSO_SECRET", secret)
            return secret, False

        secret = public.GetRandomString(48)
        if not self._write_env_value(app, "AAPANEL_SSO_SECRET", secret):
            return "", False
        return secret, True

    @staticmethod
    def _sso_signature(secret, timestamp, nonce, username):
        payload = "{}\n{}\n{}".format(timestamp, nonce, username)
        return hmac.new(secret.encode("utf-8"), payload.encode("utf-8"), hashlib.sha256).hexdigest()

    @staticmethod
    def _read_response_json(response):
        try:
            return response.json()
        except Exception:
            return {
                "success": False,
                "code": response.status_code,
                "msg": response.text,
            }

    def _post_sso(self, target_base, username, secret):
        timestamp = str(int(time.time()))
        nonce = uuid.uuid4().hex
        payload = {"username": username}
        headers = {
            "Content-Type": "application/json",
            "X-Aapanel-Timestamp": timestamp,
            "X-Aapanel-Nonce": nonce,
            "X-Aapanel-Signature": self._sso_signature(secret, timestamp, nonce, username),
        }
        response = requests.post(
            target_base.rstrip("/") + "/api/aapanel/sso",
            data=json.dumps(payload, separators=(",", ":")),
            headers=headers,
            verify=False,
            timeout=30,
        )
        return self._read_response_json(response), response.status_code

    def _post_password_login(self, target_base, username, password):
        response = requests.post(
            target_base.rstrip("/") + "/api/login",
            json={"username": username, "password": password},
            verify=False,
            timeout=30,
        )
        return self._read_response_json(response), response.status_code

    def sso(self, get):
        app = self._target_app(get)
        if not app and self._as_text(get.get("service_name", "")) == self.DEFAULT_SERVICE_NAME and not get.get("id"):
            app = self._find_installed_app()
        if not app:
            return self._err("BillionMail is not installed")

        config = self.get_proxy_config(app.get("service_name"))
        target_base = config.get("target_base")
        if not target_base:
            return self._err("BillionMail web port is not configured")

        app_secret, secret_created = self._ensure_sso_secret(app)
        app_data = self._format_app(app, include_secret=True)
        username = self._as_text(get.get("username", app_data.get("admin", {}).get("username", "")))
        mode = "aapanel_sso"

        try:
            if app_secret:
                body, status_code = self._post_sso(target_base, username, app_secret)
                if status_code == 404:
                    mode = "password_login"
                    password = app_data.get("admin", {}).get("password", "")
                    if not username or not password:
                        return self._err("aaPanel SSO endpoint is unavailable and admin credential is unavailable")
                    body, status_code = self._post_password_login(target_base, username, password)
            else:
                mode = "password_login"
                password = app_data.get("admin", {}).get("password", "")
                if not username or not password:
                    return self._err("AAPANEL_SSO_SECRET is not configured and admin credential is unavailable")
                body, status_code = self._post_password_login(target_base, username, password)
        except Exception as ex:
            return self._err("Failed to request BillionMail SSO: {}".format(str(ex)))

        if status_code >= 400 or not body.get("success"):
            return self._err({
                "status_code": status_code,
                "response": body,
                "mode": mode,
            })

        data = body.get("data", {})
        public.set_module_logs("BillionMail", "sso_login", 1)
        iframe_url = self._sso_bridge_url(app.get("service_name"), get.get("redirect", ""))
        return self._ok({
            "mode": mode,
            "token": data.get("token", ""),
            "refreshToken": data.get("refreshToken", ""),
            "ttl": data.get("ttl", 0),
            "accountInfo": data.get("accountInfo", {}),
            "api_prefix": self.PROXY_PREFIX + "/api",
            "proxy_prefix": self.PROXY_PREFIX,
            "console_url": self.PROXY_PREFIX + "/",
            "login_url": iframe_url,
            "iframe_url": iframe_url,
            "login_url_type": "aapanel_iframe_bridge",
            "sso_secret_created": secret_created,
        })


    def install(self, get):
        exists = self._target_app(get)
        if exists and self._bool_int(get.get("force", 0), 0) != 1:
            return self._ok({
                "installed": True,
                "message": "BillionMail is already installed",
                "billionmail": self._format_app(exists),
            })

        args, err = self._install_args(get)
        if err:
            return err

        if not public.progress_acquire_lock(self.INSTALL_LOCK_FILE):
            return self._err("BillionMail installation task is already running.")

        # 清理上次安装记录
        self._clear_install_progress()

        started = threading.Event()
        args_data = dict(args.get_items())
        worker = threading.Thread(target=self._install_worker, args=(args_data, started))
        worker.daemon = True
        worker.start()
        started.wait(timeout=5)
        public.set_module_logs('BillionMail', 'install')
        return self._ok({
            "result": "Successful startup!",
            "service_name": args.service_name,
            "progress_url": "/v2/mod/mail/billionmail/install_progress",
            "notice": "BillionMail installation has started. Please poll install_progress for details.",
        })

    def install_progress(self, get):
        """
        获取 docker,docker-compose,billionmail 安装进度
        2 = waiting
        0 = running
        1 = success
        -1 = failed
        """

        data = self._read_install_progress()
        billionmail = self._format_app(self._control_app())
        data["result"] = self._compact_install_result(data.get("result", {}))
        data["result"].update(self._install_result_app_summary(billionmail))
        data["docker"] = self._docker_status()
        return self._ok(data)

    def uninstall(self, get):
        app = self._control_app()
        if not app:
            return self._err("BillionMail is not installed")
        args = public.to_dict_obj({
            "id": app.get("id"),
            "delete_data": get.get("delete_data", 0),
        })
        try:
            from mod.project.docker.app.appManageMod import AppManage
            result = AppManage().remove_app(args)
            if self._is_success(result):
                self._clear_install_progress()
            return result
        except Exception as ex:
            return self._err("Failed to uninstall BillionMail: {}".format(str(ex)))

    def _set_status(self, get, status):
        app = self._control_app()
        if not app:
            return self._err("BillionMail is not installed")
        args = public.to_dict_obj({
            "app_name": self.APP_NAME,
            "service_name": app.get("service_name"),
            "status": status,
        })
        try:
            from mod.project.docker.app.appManageMod import AppManage
            aa = AppManage().set_app_status(args)
            time.sleep(2)
            return aa
        except Exception as ex:
            return self._err("Failed to {} BillionMail: {}".format(status, str(ex)))

    def start(self, get):
        docker_ready, docker_result = self._ensure_docker_ready(install_if_missing=False)
        if not docker_ready:
            return docker_result
        return self._set_status(get, "start")

    def stop(self, get):
        return self._set_status(get, "stop")

    def restart(self, get):
        docker_ready, docker_result = self._ensure_docker_ready(install_if_missing=False)
        if not docker_ready:
            return docker_result
        return self._set_status(get, "restart")

    def rebuild(self, get):
        return self._set_status(get, "rebuild")

    def upgrade(self, get):
        app = self._target_app(get)
        if not app:
            return self._err("BillionMail is not installed")

        m_version = self._as_text(get.get("m_version", ""))
        s_version = self._as_text(get.get("s_version", ""))
        if m_version and s_version:
            args = public.to_dict_obj({
                "id": app.get("id"),
                "m_version": m_version,
                "s_version": s_version,
                "backup": get.get("backup", False),
                "pull": get.get("pull", True),
            })
            try:
                from mod.project.docker.app.appManageMod import AppManage
                return AppManage().update_app(args)
            except Exception as ex:
                return self._err("Failed to upgrade BillionMail: {}".format(str(ex)))

        compose_file = self._compose_file(app)
        if not os.path.exists(compose_file):
            return self._err("docker-compose.yml was not found")
        compose_file = shlex.quote(compose_file)
        cmd = "docker-compose -f {0} pull && docker-compose -f {0} up -d".format(compose_file)
        stdout, stderr = public.ExecShell(cmd)
        return self._ok({
            "stdout": self._mask_text(stdout),
            "stderr": self._mask_text(stderr),
            "message": "BillionMail images are pulled and compose services are updated.",
        })

    def _tail_file(self, filename, lines=200):
        content = public.readFile(filename)
        if not content:
            return ""
        try:
            lines = int(lines)
        except Exception:
            lines = 200
        lines = max(20, min(lines, 1000))
        return self._mask_text("\n".join(content.splitlines()[-lines:]))

    def logs(self, get):
        app = self._target_app(get)
        if not app:
            return self._err("BillionMail is not installed")
        lines = get.get("lines", 200)
        service_path = self._service_path(app)
        log_files = {
            "install": os.path.join("/tmp", "{}.log".format(app.get("service_name"))),
            "core": os.path.join(service_path, "data/logs/core/latest"),
            "postfix": os.path.join(service_path, "data/logs/postfix/mail.log"),
            "dovecot": os.path.join(service_path, "data/logs/dovecot/mail.log"),
        }
        return self._ok({
            "service_name": app.get("service_name"),
            "logs": dict((name, self._tail_file(path, lines)) for name, path in log_files.items()),
        })

    def installed_apps(self, get):
        apps = []
        for app in self._all_installed_apps():
            if app.get("appname") == self.APP_NAME:
                apps.append(self._format_app(app))
        return self._ok(apps)
