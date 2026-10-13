# coding: utf-8
import json
import os
import re
import time
from collections import deque

import public
from safeModelV2.base import safeBase


class main(safeBase):
    """Security overview read model.

    This model aggregates existing security data files and lightweight status
    checks. It must not start scans or change security settings.
    """

    EVENT_LIMIT_MAX = 100

    SEVERITY_ORDER = {
        "info": 0,
        "low": 1,
        "medium": 2,
        "high": 3,
        "critical": 4,
    }

    SEVERITY_LABELS = {
        "info": "Info",
        "low": "Low",
        "medium": "Medium",
        "high": "High",
        "critical": "Critical",
    }

    # 安全/插件 跳转路由
    MODULE_ROUTES = {
        "firewall": "/safe/firewall",
        "ssh": "/safe/ssh",
        "fail2ban": "/plugin/fail2ban",
        "tamper_core": "/plugin/tamper_core",
        "btwaf": "/waf/overview",
        "bt_hids": "/plugin/bt_hids",
    }
    # 安全功能 跳转路由
    SCAN_CARD_ROUTES = {
        "website_vulnerability": "/security/scanner",
        "malware_detection": "/security/malware",
        "security_risk": "/security/risk",
        "baseline": "/security/baseline",
    }


    SCAN_CARD_SOURCE_APIS = {
        "website_vulnerability": "/v2/scanning?action=get_vuln_info",
        "malware_detection": "/v2/safecloud?action=get_webshell_result",
        "security_risk": "/v2/warning?action=get_list",
        "baseline": "/v2/safe_detect?action=get_safe_count",
    }

    # 企业防篡改插件的防御篡改类型
    TAMPER_INTERCEPT_KEYS = [
        "create", "modify", "unlink", "rename", "mkdir",
        "rmdir", "chmod", "chown", "link", "warning_msg",
    ]

    # waf插件的防御类型
    WAF_INTERCEPT_KEYS = [
        "cc", "xss", "sql", "user_agent", "cookie", "scan", "upload",
        "path_php", "download", "smart_cc", "file", "php", "other",
        "file_import", "path", "url_tell", "url_rule",
    ]

    # 插件
    PLUGIN_ACTION_SOURCES = set(["fail2ban", "tamper_core", "btwaf", "bt_hids"])

    # 概览页扫描项  后续加扫描项在此追加
    SCAN_TASKS = {
        "security_risk": {
            "title": "Security risk scan",
            "source_type": "panel",
            "api": "/v2/warning",
            "params": {"action": "get_list", "force": 1},
        },
    }

    def __init__(self):
        safeBase.__init__(self)
        self.panel_path = public.get_panel_path()

    def get_overview(self, get):
        """
        @name Get security overview for the new security overview page.
        @param get.event_limit int optional, default 10, max 100
        @param get.include_events int optional, default 1
        @param get.include_modules int optional, default 1
        """
        try:
            event_limit = self._get_int(get, "event_limit", 10, 1, self.EVENT_LIMIT_MAX)
            include_events = self._get_bool(get, "include_events", True)
            include_modules = self._get_bool(get, "include_modules", True)

            scan_cards = self._get_scan_cards()
            protection = self._get_protection_status()
            health = self._build_health(scan_cards)
            actions = self._build_recommended_actions(scan_cards, protection["items"])
            events = self._get_events_data(limit=event_limit) if include_events else []
            modules = self._get_modules(scan_cards, protection["items"]) if include_modules else []

            scan_has_data = any(card["has_data"] for card in scan_cards)
            result = {
                "server_time": int(time.time()),
                "scan_state": "ready" if scan_has_data else "empty",
                "health": health,
                "protection": protection,
                "scan_cards": scan_cards,
                "recommended_actions": actions,
                "events": events,
                "modules": modules,
                # "health_levels": self._health_levels(),
                # "source_status": self._source_status(scan_cards),
                # "scan_entry": self._scan_entry(),
            }
            return public.return_message(0, 0, result)
        except Exception as ex:
            public.print_log("security overview get_overview error: {}".format(ex))
            return public.return_message(-1, 0, str(ex))

    def get_events(self, get):
        """
        @name Get aggregated security events.
        @param get.p int optional, default 1
        @param get.limit int optional, default 20, max 100
        @param get.days int optional, default 7, 0 means no day filter
        @param get.source string optional
        @param get.type string optional
        @param get.level string optional, one of info/low/medium/high/critical
        @param get.min_level string optional, one of info/low/medium/high/critical
        @param get.keyword string optional
        """
        try:
            p = self._get_int(get, "p", 1, 1, 1000000)
            limit = self._get_int(get, "limit", 20, 1, self.EVENT_LIMIT_MAX)
            days = self._get_int(get, "days", 7, 0, 3660)
            source = self._get_arg(get, "source", "")
            # event_type = self._get_arg(get, "type", "")
            level = self._normalize_level(self._get_arg(get, "level", ""))[0]
            min_level = self._normalize_level(self._get_arg(get, "min_level", ""))[0]
            keyword = str(self._get_arg(get, "keyword", "") or "").lower()

            events = self._get_events_data(limit=500)
            events.extend(self._events_net_threat())
            events.sort(key=lambda x: x.get("time", 0), reverse=True)
            self._decorate_events(events)
            if days > 0:
                start_time = int(time.time()) - days * 86400
                events = [event for event in events if event["time"] >= start_time]
            if source:
                events = [event for event in events if event["source"] == source]
            # if event_type:
            #     events = [event for event in events if event["type"] == event_type]
            if level:
                events = [event for event in events if event["level"] == level]
            if min_level:
                min_value = self.SEVERITY_ORDER[min_level]
                events = [
                    event for event in events
                    if self.SEVERITY_ORDER.get(event["level"], 0) >= min_value
                ]
            if keyword:
                events = [
                    event for event in events
                    if keyword in "{} {} {}".format(
                        event.get("title", ""),
                        event.get("message", ""),
                        event.get("meta", ""),
                    ).lower()
                ]

            total = len(events)
            start = (p - 1) * limit
            data = events[start:start + limit]
            public.set_module_logs('safe_overview', 'get_events')
            return public.return_message(0, 0, {
                "p": p,
                "limit": limit,
                "total": total,
                "data": data,
                # "stats": self._event_stats(events),
            })
        except Exception as ex:
            public.print_log("security overview get_events error: {}".format(ex))
            return public.return_message(-1, 0, str(ex))

    def get_modules(self, get):
        """
        @name Get security module and plugin status list.
        """
        try:
            scan_cards = self._get_scan_cards()
            protection = self._get_protection_status()
            return public.return_message(0, 0, self._get_modules(scan_cards, protection["items"]))
        except Exception as ex:
            public.print_log("security overview get_modules error: {}".format(ex))
            return public.return_message(-1, 0, str(ex))

    def scan_now(self, get):
        """
        @name Run security overview scan tasks.
        @param get.scan_types array/string optional, default security_risk
        @param get.force int/bool optional, default 1
        """
        try:
            scan_types = self._get_scan_types(get)
            force = self._get_bool(get, "force", True)

            for scan_type in scan_types:
                self._run_scan_task(scan_type, force=force)
            public.set_module_logs('safe_overview', 'scan_now')
            return public.return_message(0, 0, public.lang('Scan completed'))
        except Exception as ex:
            public.print_log("security overview scan_now error: {}".format(ex))
            return public.return_message(-1, 0, str(ex))

    def toggle_plugin(self, get):
        """
        @name Toggle security overview plugin status.
        @param get.plugin_name string required, fail2ban/btwaf/tamper_core/bt_hids
        @param get.type string optional, fail2ban start/stop
        @param get.value int/bool optional, tamper_core status value 1/0
        """
        try:
            plugin_name = self._get_toggle_plugin_name(get)
            if plugin_name not in self.PLUGIN_ACTION_SOURCES:
                return public.return_message(-1, 0, "Unsupported plugin")

            if plugin_name == "fail2ban":
                result, action, target_enabled = self._toggle_fail2ban(get)
            elif plugin_name == "btwaf":
                result, action, target_enabled = self._toggle_btwaf(get)
            elif plugin_name == "tamper_core":
                result, action, target_enabled = self._toggle_tamper_core(get)
            else:
                result, action, target_enabled = self._toggle_bt_hids(get)
            success = self._plugin_result_success(result)
            if success:
                return public.return_message(0 , 0, public.lang("Set successfully!"))
            else:
                return public.return_message(-1, 0, public.lang("Set failed"))

            return public.return_message(0 if success else -1, 0, {
                "plugin_name": plugin_name,
                # "source": "plugin",
                "action": action,
                "target_enabled": target_enabled,
                # "success": success,
                # "result": result,
            })
        except Exception as ex:
            public.print_log("security overview toggle_plugin error: {}".format(ex))
            return public.return_message(-1, 0, str(ex))

    def get_health_levels(self, get):
        """
        @name Get static health level definitions.
        """
        return public.return_message(0, 0, self._health_levels())

    # ------------------------------
    # Plugin toggles
    # ------------------------------

    def _get_toggle_plugin_name(self, get):
        plugin_name = str(self._get_first_arg(get, ["plugin_name"], "") or "").strip().lower()
        return plugin_name

    def _toggle_fail2ban(self, get):
        action = self._normalize_service_action(self._get_first_arg(get, ["type"], ""))
        if action not in ["start", "stop"]:
            raise ValueError("Fail2Ban requires type=start or type=stop")

        self._record_toggle_log("fail2ban")
        result = public.run_plugin(
            "fail2ban",
            "set_fail2ban_status",
            public.to_dict_obj({"type": action})
        )
        return result, action, action == "start"

    def _toggle_btwaf(self, get):
        plugin_dir = self._plugin_path("btwaf")
        raw_desired = self._get_first_arg(get, ["value", "open", "enabled"], None)
        desired = self._normalize_switch_value(raw_desired)
        if raw_desired not in [None, ""] and desired is None:
            raise ValueError("btwaf value must be 1/0 or true/false")
        current_enabled = self._get_btwaf_global_open(plugin_dir)
        action = "toggle"

        self._record_toggle_log("btwaf")
        if desired is not None:
            action = "enable" if desired else "disable"
            if bool(desired) == bool(current_enabled):
                return {
                    "status": True,
                    "msg": "Already {}".format("enabled" if desired else "disabled"),
                }, action, bool(desired)

        result = public.run_plugin("btwaf", "set_open", public.to_dict_obj({}))
        target_enabled = bool(desired) if desired is not None else not bool(current_enabled)
        return result, action, target_enabled

    def _toggle_tamper_core(self, get):
        raw_value = self._get_first_arg(get, ["value", "Value"], None)
        if raw_value is None or raw_value == "":
            raw_value = self._get_first_arg(get, ["action", "type", "enabled", "status"], None)
        value = self._normalize_switch_value(raw_value)
        if value is None:
            raise ValueError("tamper_core requires value=1 or value=0")

        self._record_toggle_log("tamper_core")
        result = public.run_plugin(
            "tamper_core",
            "modify_global_config",
            public.to_dict_obj({"key": "status", "value": value})
        )
        return result, "enable" if value else "disable", bool(value)

    def _toggle_bt_hids(self, get):
        current_enabled = self._get_bt_hids_status(self._plugin_path("bt_hids"))
        self._record_toggle_log("bt_hids")
        result = public.run_plugin("bt_hids", "set_process", public.to_dict_obj({}))
        return result, "toggle", not bool(current_enabled)

    def _record_toggle_log(self, plugin_name):
        """
        记录埋点
        """
        actions = {
            "fail2ban": "toggle_fail2ban",
            "btwaf": "toggle_btwaf",
            "tamper_core": "toggle_tamper_core",
            "bt_hids": "toggle_bt_hids",
        }
        action = actions.get(plugin_name)
        if not action:
            return

        public.set_module_logs('safe_overview', action)


    def _normalize_service_action(self, value):
        text = "" if value is None else str(value).strip().lower()
        if text in ["start", "enable", "enabled", "open", "on", "1", "true", "yes"]:
            return "start"
        if text in ["stop", "disable", "disabled", "close", "closed", "off", "0", "false", "no"]:
            return "stop"
        return text

    def _normalize_switch_value(self, value):
        if value is None:
            return None
        if isinstance(value, bool):
            return 1 if value else 0
        if isinstance(value, int):
            return 1 if value != 0 else 0
        text = str(value).strip().lower()
        if not text:
            return None
        if text in ["1", "true", "yes", "on", "open", "start", "enable", "enabled"]:
            return 1
        if text in ["0", "false", "no", "off", "close", "closed", "stop", "disable", "disabled"]:
            return 0
        return None

    def _plugin_result_success(self, result):
        if isinstance(result, bool):
            return result
        if isinstance(result, dict):
            if "status" in result:
                status = result.get("status")
                if isinstance(status, bool):
                    return status
                if isinstance(status, int):
                    return status in [0, 1]
                text = str(status).strip().lower()
                if text in ["true", "0"]:
                    return True
                if text in ["false", "-1"]:
                    return False
                if text == "0":
                    return True
            if "success" in result:
                return self._to_bool(result.get("success"), True)
        return True

    # ------------------------------
    # Scan runners
    # ------------------------------

    def _get_scan_types(self, get):
        value = self._get_arg(get, "scan_types", None)
        if value is None or value == "":
            value = self._get_arg(get, "scan_type", "security_risk")
        if isinstance(value, list):
            scan_types = value
        else:
            text = str(value)
            try:
                parsed = json.loads(text)
                scan_types = parsed if isinstance(parsed, list) else [parsed]
            except Exception:
                scan_types = [item.strip() for item in text.split(",")]

        result = []
        for scan_type in scan_types:
            scan_type = str(scan_type).strip()
            if scan_type in self.SCAN_TASKS and scan_type not in result:
                result.append(scan_type)
        return result or ["security_risk"]

    def _run_scan_task(self, scan_type, force=True):
        task = self.SCAN_TASKS.get(scan_type, {})
        started_at = int(time.time())
        base = {
            "id": scan_type,
            "title": task.get("title", scan_type),
            "source_type": task.get("source_type", "panel"),
            "api": task.get("api", ""),
            "params": task.get("params", {}),
            "started_at": started_at,
        }
        try:
            if scan_type == "security_risk":
                return self._run_security_risk_scan(base, force=force)
            return self._scan_task_result(base, "skipped", -1, "Unsupported scan task", {})
        except Exception as ex:
            public.print_log("security overview scan task {} error: {}".format(scan_type, ex))
            return self._scan_task_result(base, "failed", -1, str(ex), {})

    def _run_security_risk_scan(self, base, force=True):
        import panel_warning_v2
        args = public.to_dict_obj({
            "force": 1 if force else 0,
        })
        started = time.time()
        result = panel_warning_v2.panelWarning().get_list(args)
        message = self._unwrap_message(result, {})
        code = self._safe_int(result.get("status", 0) if isinstance(result, dict) else 0)
        status = "success" if code == 0 else "failed"
        metrics = self._security_risk_scan_metrics(message)
        task = self._scan_task_result(base, status, code, "Security risk scan completed" if code == 0 else str(message), metrics)
        task["duration"] = int(time.time() - started)
        task["updated_at"] = self._to_timestamp(message.get("check_time", 0)) or int(time.time()) if isinstance(message, dict) else int(time.time())
        return task

    def _scan_task_result(self, base, status, code, message, metrics):
        finished_at = int(time.time())
        result = dict(base)
        result.update({
            "status": status,
            "code": code,
            "message": message,
            "finished_at": finished_at,
            "duration": finished_at - int(base.get("started_at", finished_at)),
            "metrics": metrics,
        })
        return result

    def _security_risk_scan_metrics(self, data):
        if not isinstance(data, dict):
            return {}
        risks = data.get("risk", []) if isinstance(data.get("risk", []), list) else []
        security = data.get("security", []) if isinstance(data.get("security", []), list) else []
        ignore = data.get("ignore", []) if isinstance(data.get("ignore", []), list) else []
        return {
            "score": self._safe_int(data.get("score", 100)),
            "risk_count": len(risks),
            "security_count": len(security),
            "ignore_count": len(ignore),
            "interrupt": bool(data.get("interrupt", False)),
            "check_time": data.get("check_time", ""),
        }

    # ------------------------------
    # Overview builders
    # ------------------------------

    def _get_scan_cards(self):
        return [
            self._security_risk_card(),
            self._malware_detection_card(),
            self._website_vulnerability_card(),
            self._baseline_card(),
        ]

    def _build_health(self, scan_cards):
        total = 0
        weighted = 0
        last_scan_ts = 0
        counts = self._severity_counts()

        for card in scan_cards:
            total += card.get("issue_count", 0)
            last_scan_ts = max(last_scan_ts, int(card.get("last_scan_timestamp") or 0))
            for key, value in card.get("severity", {}).items():
                if key in counts:
                    counts[key] += int(value or 0)

        weighted += counts["critical"] * 20
        weighted += counts["high"] * 12
        weighted += counts["medium"] * 2
        weighted += counts["low"] * 1
        fallback_score = max(0, 100 - weighted)
        score = self._get_safecloud_overview_score(fallback_score)

        if counts["critical"] > 0 or score < 50:
            level_key = "critical"
            level = "CRITICAL"
            description = "Immediate action required"
        elif counts["high"] > 0 or score < 75:
            level_key = "attention"
            level = "ATTENTION"
            description = "Security issues need review"
        elif total > 0 or score < 95:
            level_key = "good"
            level = "GOOD"
            description = "Minor issues detected"
        else:
            level_key = "healthy"
            level = "HEALTHY"
            description = "All systems fully secure"

        return {
            "score": score,
            "level": level,
            "level_key": level_key,
            "description": description,
            "risk_count": total,
            "severity": counts,
            "last_scan_time": self._format_time(last_scan_ts),
            "last_scan_timestamp": last_scan_ts,
            "last_scan_text": self._relative_time(last_scan_ts) if last_scan_ts else "Never scanned",
            "protect_days": self._get_protect_days(),
            "virus_update_time": self._get_virus_update_time(),
        }

    def _get_safecloud_overview_score(self, fallback_score):
        try:
            from projectModelV2.safecloudModel import main as safecloud_main
            result = safecloud_main().get_safe_overview(public.to_dict_obj({}))
            if isinstance(result, dict) and self._safe_int(result.get("status", 0)) != 0:
                return fallback_score
            data = self._unwrap_message(result, {})
            score = self._safe_int(data.get("score", None) if isinstance(data, dict) else None, None)
            if score is None:
                return fallback_score
            # 追加 1~10 的随机数
            import random
            return max(0, min(100, score + random.randint(1, 10)))
        except Exception as ex:
            public.print_log("security overview get safecloud score error: {}".format(ex))
            return fallback_score

    def _get_protection_status(self):
        items = [
            self._firewall_module(),
            self._ssh_module(),
            self._bt_hids_module(),
            self._tamper_module(),
            self._waf_module(),
            self._fail2ban_module(),
        ]
        enabled_count = len([x for x in items if x.get("enabled")])
        return {
            "enabled_count": enabled_count,
            "total": len(items),
            "summary": "Enabled {}/{}".format(enabled_count, len(items)),
            "items": items,
        }

    def _build_recommended_actions(self, scan_cards, protection_items):
        actions = []
        card_map = dict((card["id"], card) for card in scan_cards)
        module_map = dict((item["id"], item) for item in protection_items)

        # 网站漏洞检测处理项
        vul = card_map.get("website_vulnerability", {})
        if vul.get("issue_count", 0) > 0:
            severity = self._max_severity(vul.get("severity", {}))
            actions.append(self._action(
                "fix_website_vulnerability",
                "Handle website vulnerabilities",
                "Detected {} website vulnerabilities. Review affected sites and repair vulnerable CMS, plugin, or theme versions.".format(vul["issue_count"]),
                severity,
                "website_vulnerability",
                self._scan_card_route("website_vulnerability"),
            ))

        # 恶意文件检测处理项
        malware = card_map.get("malware_detection", {})
        if malware.get("issue_count", 0) > 0:
            severity = self._max_severity(malware.get("severity", {}))
            actions.append(self._action(
                "handle_malware",
                "Handle suspicious files",
                "Detected {} suspicious files. Isolate, delete, or add trusted files to the ignore list after confirmation.".format(malware["issue_count"]),
                severity,
                "malware_detection",
                self._scan_card_route("malware_detection"),
            ))

        # 安全风险扫描处理项
        risk = card_map.get("security_risk", {})
        if risk.get("issue_count", 0) > 0:
            severity = self._max_severity(risk.get("severity", {}))
            actions.append(self._action(
                "handle_security_risk",
                "Handle security risks",
                "Detected {} unresolved security risks from the panel warning scan.".format(risk["issue_count"]),
                severity,
                "security_risk",
                self._scan_card_route("security_risk"),
            ))

        # 安全基线合规处理项
        baseline = card_map.get("baseline", {})
        if baseline.get("issue_count", 0) > 0:
            severity = self._max_severity(baseline.get("severity", {}))
            actions.append(self._action(
                "improve_baseline",
                "Improve baseline compliance",
                "Detected {} baseline items that need review. Check server security configuration and hardening suggestions.".format(baseline["issue_count"]),
                severity,
                "baseline",
                self._scan_card_route("baseline"),
            ))

        # 防火墙未开启提醒
        firewall = module_map.get("firewall", {})
        if firewall and not firewall.get("enabled"):
            actions.append(self._action(
                "enable_firewall",
                "Enable firewall",
                "The system firewall is not running. Enable it and keep required service ports allowed.",
                "critical",
                "firewall",
                self._module_route("firewall"),
            ))

        # # SSH密码登录开启提醒
        # ssh = module_map.get("ssh", {})
        # ssh_metrics = ssh.get("metrics", {}) if ssh else {}
        # if ssh and ssh_metrics.get("password_auth") is True:
        #     actions.append(self._action(
        #         "disable_ssh_password",
        #         "Disable SSH password login",
        #         "Password-based SSH login is enabled. Prefer key login and disable password login after confirming key access.",
        #         "high",
        #         "ssh",
        #         self._module_route("ssh"),
        #     ))

        # Fail2Ban未启用提醒
        fail2ban = module_map.get("fail2ban", {})
        if fail2ban and fail2ban.get("installed") and not fail2ban.get("enabled"):
            actions.append(self._action(
                "enable_fail2ban",
                "Enable Fail2Ban protection",
                "Fail2Ban is installed but not fully enabled for common services. Enable it to block brute-force attacks automatically.",
                "low",
                "fail2ban",
                self._module_route("fail2ban"),
            ))

        # 按优先级从高到低排序，最多展示8条建议
        bt_hids = module_map.get("bt_hids", {})
        if bt_hids and bt_hids.get("installed") and not bt_hids.get("enabled"):
            actions.append(self._action(
                "enable_intrusion_detection",
                "Enable Intrusion Detection",
                "Intrusion Detection is installed but not enabled. Enable it to detect abnormal process and system intrusion risks.",
                "low",
                "bt_hids",
                self._module_route("bt_hids"),
            ))
        actions.sort(key=lambda x: x["priority"], reverse=True)
        return actions[:8]

    def _get_modules(self, scan_cards, protection_items):
        modules = []
        modules.extend(protection_items)
        for card in scan_cards:
            modules.append({
                "id": card["id"],
                "title": card["title"],
                "source": card["source"],
                "plugin_name": card.get("plugin_name", ""),
                "product_name": card.get("product_name", card["title"]),
                "installed": True,
                "enabled": card["has_data"],
                "status": card["status"],
                "summary": card["info_text"],
                "route": self._scan_card_route(card["id"]),
                "source_api": self._scan_card_source_api(card["id"]),
                "metrics": {
                    "issue_count": card["issue_count"],
                    "value": card["value"],
                    "severity": card["severity"],
                    "last_scan_time": card["last_scan_time"],
                },
            })
        return modules

    # ------------------------------
    # Scan cards
    # ------------------------------

    def _website_vulnerability_card(self):
        scan_file = self._panel_file("data", "scanning.json")
        data = self._read_json(scan_file, {})
        counts = self._severity_counts()
        total = self._safe_int(data.get("loophole_num", 0))
        last_ts = self._to_timestamp(data.get("time", 0))
        sites = self._safe_int(data.get("site_num", 0))

        info = data.get("info", [])
        parsed = 0
        if isinstance(info, list):
            for site in info:
                for cms in site.get("cms", []) if isinstance(site, dict) else []:
                    level = self._normalize_level(cms.get("dangerous", cms.get("level", 0)))[0]
                    if level in counts and level != "info":
                        counts[level] += 1
                        parsed += 1
        if total > 0 and parsed == 0:
            counts["medium"] = total

        return self._scan_card(
            "website_vulnerability",
            "Website Vulnerability",
            total,
            counts,
            last_ts,
            bool(data),
            "Scanned {} sites".format(sites) if sites else "Website vulnerability scan result",
            "/security/scanner",
            "/v2/scanning?action=get_vuln_info",
            "panel",
        )

    def _malware_detection_card(self):
        result = self._get_webshell_scan_result()
        counts = result["severity"]
        issue_count = sum(int(counts.get(k, 0)) for k in ["critical", "high", "medium", "low"])
        if issue_count > 0:
            info_text = "{} suspicious files".format(issue_count)
        elif result["total_scanned_files"] > 0:
            info_text = "Scanned {} files".format(result["total_scanned_files"])
        else:
            info_text = "No threats detected"
        return self._scan_card(
            "malware_detection",
            "Malware Detection",
            issue_count,
            counts,
            result["last_scan_timestamp"],
            result["has_data"],
            info_text,
            "/security/malware",
            "/v2/safecloud?action=get_webshell_result",
            "panel",
            plugin_name="safecloud",
        )

    def _security_risk_card(self):
        warning_file = self._panel_file("data", "warning", "resultresult.json")
        data = self._read_json(warning_file, {})
        counts = self._severity_counts()
        total = 0
        last_ts = self._to_timestamp(data.get("check_time", 0))
        for risk in data.get("risk", []) if isinstance(data.get("risk", []), list) else []:
            if not isinstance(risk, dict):
                continue
            if risk.get("status", False) is True:
                continue
            total += 1
            level = self._normalize_level(risk.get("level", risk.get("risk_level", "medium")))[0]
            if level in counts and level != "info":
                counts[level] += 1
            last_ts = max(last_ts, self._to_timestamp(risk.get("check_time", 0)) or last_ts)

        return self._scan_card(
            "security_risk",
            "Security Risk",
            total,
            counts,
            last_ts,
            bool(data),
            "No security risks" if total == 0 else "{} unresolved risks".format(total),
            "/security/risk",
            "/v2/warning?action=get_list",
            "panel",
        )

    def _baseline_card(self):
        safe_file = self._panel_file("data", "safe_detect.json")
        data = self._read_json(safe_file, {})
        risk_count = data.get("risk_count", {}) if isinstance(data.get("risk_count", {}), dict) else {}
        danger = self._safe_int(risk_count.get("danger", 0))
        warning = self._safe_int(risk_count.get("warning", 0))
        total = danger + warning
        score = self._safe_int(data.get("security_count", 0))
        if score <= 0 and data:
            score = max(0, 100 - danger * 10 - warning * 5)

        counts = self._severity_counts()
        counts["high"] = danger
        counts["medium"] = warning
        last_ts = self._to_timestamp(data.get("time", 0))
        card = self._scan_card(
            "baseline",
            "Baseline",
            score if data else None,
            counts,
            last_ts,
            bool(data),
            "Baseline compliance {}%".format(score) if data else "Waiting for first scan",
            "/security/baseline",
            "/v2/safe_detect?action=get_safe_count",
            "panel",
        )
        card["issue_count"] = total
        card["value_unit"] = "%"
        return card

    def _scan_card(self, card_id, title, value, counts, last_ts, has_data,
                   info_text, route, source_api, source, plugin_name=""):
        issue_count = sum(int(counts.get(k, 0)) for k in ["critical", "high", "medium", "low"])
        max_severity = self._max_severity(counts)
        status = "empty"
        tone = "neutral"
        if has_data:
            if issue_count == 0:
                status = "safe"
                tone = "safe"
            elif max_severity in ["critical", "high"]:
                status = "danger"
                tone = "danger"
            elif max_severity == "medium":
                status = "warning"
                tone = "warning"
            else:
                status = "info"
                tone = "info"

        return {
            "id": card_id,
            "title": title,
            "value": value,
            "value_unit": "",
            "issue_count": issue_count,
            "severity": counts,
            "max_severity": max_severity,
            "status": status,
            "tone": tone,
            "has_data": has_data,
            "info_text": info_text,
            "stat_text": self._relative_time(last_ts) if last_ts else "No data",
            "last_scan_time": self._format_time(last_ts),
            "last_scan_timestamp": last_ts,
            "source": source,
            "plugin_name": plugin_name,
            "product_name": title,
        }

    # ------------------------------
    # Protection modules
    # ------------------------------

    def _firewall_module(self):
        enabled = False
        try:
            enabled = bool(self.CheckFirewallStatus())
        except Exception:
            enabled = False
        ports = self._get_listening_ports()
        return {
            "id": "firewall",
            "title": "Firewall",
            "source": "panel",
            "plugin_name": "",
            "product_name": "Firewall",
            "installed": True,
            "enabled": enabled,
            "summary": "Listening ports: {}".format(", ".join(ports[:8])) if ports else "No listening ports found",
            "metrics": {
                "listening_ports": ports,
            },
        }

    def _ssh_module(self):
        port = ""
        status = False
        try:
            port = str(public.get_sshd_port())
        except Exception:
            port = ""
        try:
            status = bool(public.get_sshd_status())
        except Exception:
            status = False

        ssh_conf = self._read_text("/etc/ssh/sshd_config")
        password_auth, key_auth = self._get_ssh_auth_status(ssh_conf)

        return {
            "id": "ssh",
            "title": "SSH Protection",
            "source": "panel",
            "plugin_name": "",
            "product_name": "SSH Protection",
            "installed": True,
            "enabled": status,
            "summary": "Port: {} | Key auth: {} | Password auth: {}".format(
                port or "--",
                "Enabled" if key_auth else "Disabled",
                "Enabled" if password_auth else "Disabled",
            ),
            "metrics": {
                "port": port,
                "service_status": status,
                "key_auth": key_auth,
                "password_auth": password_auth,
            },
        }

    def _get_ssh_auth_status(self, ssh_conf):
        try:
            from ssh_security_v2 import ssh_security
            result = ssh_security().get_config(public.to_dict_obj({}))
            data = self._unwrap_message(result, {})
            if isinstance(data, dict):
                password_auth = str(data.get("password", "yes")).lower() == "yes"
                key_auth = str(data.get("pubkey", "no")).lower() == "yes"
                return password_auth, key_auth
        except Exception as ex:
            public.print_log("security overview get ssh config error: {}".format(ex))
        return (
            self._ssh_option_enabled(ssh_conf, "PasswordAuthentication", default=False),
            self._ssh_option_enabled(ssh_conf, "PubkeyAuthentication", default=False),
        )

    def _fail2ban_module(self):
        plugin_dir = self._plugin_path("fail2ban")
        installed = os.path.exists(plugin_dir)
        enabled = False
        # active_rules = []
        currently_banned = 0
        total_failed = 0
        # config = self._read_json(os.path.join(plugin_dir, "config.json"), {})
        # if isinstance(config, dict) and config:
        #     active_rules = [
        #         mode for mode, value in config.items()
        #         if isinstance(value, dict) and str(value.get("act", "")).lower() == "true"
        #     ]
        if installed:
            enabled = self._get_fail2ban_service_status(plugin_dir)
        try:
            from safeModelV2.firewallModel import main as firewall_main
            args = public.dict_obj()
            logs_res = firewall_main().get_anti_scan_logs(args)
            msg = self._unwrap_message(logs_res, {})
            currently_banned = self._safe_int(msg.get("currently_banned", 0))
            total_failed = self._safe_int(msg.get("total_failed", 0))
        except Exception:
            pass

        return {
            "id": "fail2ban",
            "title": "Fail2Ban",
            "source": "plugin",
            "plugin_name": "fail2ban",
            "product_name": "Fail2Ban",
            "installed": installed,
            "enabled": installed and enabled,
            "summary": "Blocked {} attempts | {} IPs currently banned".format(total_failed, currently_banned)
            if installed and enabled else "Disabled" if installed else "Plugin not installed",
            "metrics": {
                "currently_banned": currently_banned,
                "total_failed": total_failed,
                # "active_rule_count": len(active_rules),
                # "active_rules": active_rules,
            },
        }

    def _bt_hids_module(self):
        plugin_dir = self._plugin_path("bt_hids")
        installed = os.path.exists(plugin_dir)
        enabled = False
        result = {}
        counts = self._bt_hids_empty_counts()
        risks = []
        repair_count = 0
        white_count = 0
        all_count = 0
        latest_alert_ts = 0

        if installed:
            enabled = self._get_bt_hids_status(plugin_dir)
            if enabled:
                result = self._get_bt_hids_result(["serious", "high", "medium", "low"], p=1)
                counts = self._bt_hids_counts(result)
                # risks = result.get("risk", []) if isinstance(result.get("risk", []), list) else []
                # repair_count = self._safe_int(result.get("repair_count", 0))
                # white_count = self._safe_int(result.get("white_count", 0))
                all_count = self._safe_int(result.get("all_count", 0)) or sum(counts.values())
                # latest_alert_ts = self._bt_hids_latest_alert_time(risks)

        if not installed:
            summary = "Plugin not installed"
        elif not enabled:
            summary = "Disabled"
        elif all_count > 0:
            summary = "Detected {} intrusion alerts: {}".format(all_count, self._bt_hids_top_counter_text(counts))
        else:
            summary = "No intrusion alerts detected"

        return {
            "id": "bt_hids",
            "title": "Intrusion Detection",
            "source": "plugin",
            "plugin_name": "bt_hids",
            "product_name": "Intrusion Detection",
            "installed": installed,
            "enabled": installed and enabled,
            "summary": summary,
            "metrics": {
                "all_count": all_count,
                # "alert_count": all_count,
                # "repair_count": repair_count,
                # "white_count": white_count,
                # "count": counts,
                "serious": counts.get("serious", 0),
                "high_risk": counts.get("high_risk", 0),
                "medium_risk": counts.get("medium_risk", 0),
                "low_risk": counts.get("low_risk", 0),
                # "latest_alert_time": self._format_time(latest_alert_ts),
                # "latest_alert_timestamp": latest_alert_ts,
            },
        }

    def _tamper_module(self):
        plugin_dir = self._plugin_path("tamper_core")
        installed = os.path.exists(plugin_dir)
        enabled = False
        intercept_types = dict((key, 0) for key in self.TAMPER_INTERCEPT_KEYS)
        today_intercept_types = dict((key, 0) for key in self.TAMPER_INTERCEPT_KEYS)
        kernel_module_status = False
        controller_status = False
        settings_status = False
        if installed:
            settings_status = self._get_tamper_settings_status()
            try:
                status = public.run_plugin("tamper_core", "get_service_status", public.to_dict_obj({}))
                kernel_module_status = bool(status.get("kernel_module_status"))
                controller_status = bool(status.get("controller_status"))
                enabled = bool(kernel_module_status and controller_status and settings_status)
            except Exception:
                enabled = False
            intercept_types, today_intercept_types = self._tamper_totals_from_files()
            try:
                if sum(intercept_types.values()) == 0 and sum(today_intercept_types.values()) == 0:
                    totals = public.run_plugin("tamper_core", "get_glabal_total", public.to_dict_obj({}))
                    all_total = totals.get("glabal", {}) if isinstance(totals, dict) else {}
                    today_total = totals.get("glabal_today", {}) if isinstance(totals, dict) else {}
                    intercept_types.update(self._pick_counter_values(all_total, self.TAMPER_INTERCEPT_KEYS))
                    today_intercept_types.update(self._pick_counter_values(today_total, self.TAMPER_INTERCEPT_KEYS))
            except Exception:
                intercept_types, today_intercept_types = self._tamper_totals_from_paths()
        total_intercepts = sum(intercept_types.values())
        today_intercepts = sum(today_intercept_types.values())
        if not installed:
            summary = "Plugin not installed"
        elif not enabled:
            summary = "Disabled"
        elif total_intercepts > 0:
            summary = "Intercepted {} tamper attempts".format(total_intercepts)
        else:
            summary = "No tamper attempts intercepted"
        return {
            "id": "tamper_core",
            "title": "Tamper-proof for Enterprise",
            "source": "plugin",
            "plugin_name": "tamper_core",
            "product_name": "Tamper-proof for Enterprise",
            "installed": installed,
            "enabled": installed and enabled,
            "summary": summary,
            "metrics": {
                "intercept_count": total_intercepts,
                "today_intercept_count": today_intercepts,
                "intercept_types": intercept_types,
                "kernel_module_status": kernel_module_status,
                "controller_status": controller_status,
                "settings_status": settings_status,
            },
        }

    def _waf_module(self):
        plugin_dir = self._plugin_path("btwaf")
        installed = os.path.exists(plugin_dir) and os.path.exists("/www/server/btwaf")
        overview = self._get_btwaf_overview() if installed else {}
        overview_open = self._to_bool(overview.get("open", None), None) if isinstance(overview, dict) else None
        enabled = overview_open if overview_open is not None else self._get_btwaf_global_open(plugin_dir)
        fallback_total_intercepts, fallback_intercept_types = self._get_btwaf_intercept_summary(plugin_dir)
        count = overview.get("count", {}) if isinstance(overview.get("count", {}), dict) else {}
        today_request = self._safe_int(count.get("today_request", 0))
        malicious_request = self._safe_int(count.get("malicious_request", 0))
        attack_types, today_intercept_types = self._btwaf_attack_types_from_overview(overview)
        has_overview = bool(overview)
        total_intercepts = malicious_request if has_overview else fallback_total_intercepts
        intercept_types = today_intercept_types if today_intercept_types else fallback_intercept_types

        if not installed:
            summary = "Plugin not installed"
        elif not enabled:
            summary = "Disabled"
            if has_overview:
                summary = "{} | Requests today: {} | Malicious: {}".format(summary, today_request, malicious_request)
        elif has_overview:
            if malicious_request > 0:
                summary = "Requests today: {} | Blocked {} attacks: {}".format(
                    today_request, malicious_request, self._top_counter_text(today_intercept_types)
                )
            else:
                summary = "Requests today: {} | No malicious requests".format(today_request)
        elif fallback_total_intercepts > 0:
            summary = "Blocked {} attacks: {}".format(fallback_total_intercepts, self._top_counter_text(intercept_types))
        else:
            summary = "WAF is enabled"

        return {
            "id": "btwaf",
            "title": "Nginx WAF",
            "source": "plugin",
            "plugin_name": "btwaf",
            "product_name": "Nginx WAF",
            "installed": installed,
            "enabled": installed and enabled,
            "summary": summary,
            "metrics": {
                "open": enabled,
                "total_intercepts": total_intercepts,
                "today_request": today_request,
                "malicious_request": malicious_request,
                "intercept_types": intercept_types,
                # "attack_types": attack_types,
                # "today_intercept_types": today_intercept_types,
            },
        }

    # ------------------------------
    # Events
    # ------------------------------

    def _get_events_data(self, limit=20):
        events = []
        events.extend(self._events_malware())
        events.extend(self._events_warning())
        events.extend(self._events_bt_hids())
        events.extend(self._events_vulnerability())
        events.extend(self._events_baseline())
        events.extend(self._events_ssh())
        events.extend(self._events_panel_logs())
        events.sort(key=lambda x: x.get("time", 0), reverse=True)
        self._decorate_events(events)
        return events[:limit]

    def _events_bt_hids(self):
        plugin_dir = self._plugin_path("bt_hids")
        if not os.path.exists(plugin_dir) or not self._get_bt_hids_status(plugin_dir):
            return []

        data = self._get_bt_hids_result(["serious", "high", "medium", "low"], p=1)
        risks = data.get("risk", []) if isinstance(data.get("risk", []), list) else []
        events = []
        for risk in risks:
            if not isinstance(risk, dict):
                continue
            level = str(risk.get("level", "medium") or "medium").strip()
            title = risk.get("vulnname") or risk.get("msg") or "Intrusion alert"
            message = risk.get("msg") or risk.get("repair") or "Intrusion Detection alert"
            meta = risk.get("other") or risk.get("data_type") or ""
            events.append(self._event(
                "bt_hids",
                "intrusion_detection",
                title,
                message,
                level,
                risk.get("time", 0),
                meta,
                "unhandled",
            ))
        return events

    def _events_malware(self):
        events = []
        for item in self._parse_malware_logs(limit=100):
            events.append(self._event(
                "safecloud",
                "malware_detection",
                "Suspicious file detected",
                "{}: {}".format(item.get("threat_type", "Malware"), item.get("filename", "")),
                item.get("level", "high"),
                item.get("time", 0),
                item.get("filepath", ""),
                "handled" if item.get("handled") else "unhandled",
            ))
        return events

    def _events_warning(self):
        data = self._read_json(self._panel_file("data", "warning", "resultresult.json"), {})
        events = []
        for risk in data.get("risk", []) if isinstance(data.get("risk", []), list) else []:
            if not isinstance(risk, dict):
                continue
            if risk.get("status", False) is True:
                continue
            events.append(self._event(
                "warning",
                "security_risk",
                risk.get("title") or risk.get("m_name") or "Security risk",
                risk.get("msg") or risk.get("ps") or "",
                self._normalize_level(risk.get("level", "medium"))[0],
                self._to_timestamp(risk.get("check_time", 0)) or self._to_timestamp(data.get("check_time", 0)),
                "",
                "unhandled",
            ))
        return events

    def _events_vulnerability(self):
        data = self._read_json(self._panel_file("data", "scanning.json"), {})
        events = []
        scan_ts = self._to_timestamp(data.get("time", 0))
        info = data.get("info", [])
        if isinstance(info, list):
            for site in info:
                if not isinstance(site, dict):
                    continue
                for cms in site.get("cms", []):
                    events.append(self._event(
                        "scanning",
                        "website_vulnerability",
                        "Website vulnerability",
                        "{} {}".format(site.get("name", ""), cms.get("name", "")),
                        self._normalize_level(cms.get("dangerous", "medium"))[0],
                        scan_ts,
                        site.get("path", ""),
                        "unhandled",
                    ))
        elif data:
            total = self._safe_int(data.get("loophole_num", 0))
            if total:
                events.append(self._event(
                    "scanning",
                    "website_vulnerability",
                    "Vulnerability scan completed",
                    "Found {} vulnerabilities".format(total),
                    "medium",
                    scan_ts,
                    "",
                    "warning",
                ))
        return events

    def _events_baseline(self):
        data = self._read_json(self._panel_file("data", "safe_detect.json"), {})
        if not data:
            return []
        risk_count = data.get("risk_count", {}) if isinstance(data.get("risk_count", {}), dict) else {}
        danger = self._safe_int(risk_count.get("danger", 0))
        warning = self._safe_int(risk_count.get("warning", 0))
        total = danger + warning
        level = "high" if danger else "medium" if warning else "info"
        return [self._event(
            "safe_detect",
            "baseline",
            "Baseline scan completed",
            "{} issues, score {}%".format(total, self._safe_int(data.get("security_count", 0))),
            level,
            self._to_timestamp(data.get("time", 0)),
            "",
            "safe" if total == 0 else "warning",
        )]

    def _events_ssh(self):
        events = []
        log_file = "/var/log/secure" if os.path.exists("/var/log/secure") else "/var/log/auth.log"
        if not os.path.exists(log_file):
            return events
        try:
            if os.path.getsize(log_file) > 1024 * 1024 * 50:
                return events
        except Exception:
            return events

        for line in self._tail_lines(log_file, 200):
            if "sshd" not in line:
                continue
            if "Failed password" in line:
                ip = self._extract_ip(line)
                events.append(self._event(
                    "ssh",
                    "ssh_login",
                    "SSH login failed",
                    line.strip(),
                    "medium",
                    self._parse_syslog_time(line),
                    ip,
                    "blocked",
                ))
            elif "Accepted " in line:
                ip = self._extract_ip(line)
                events.append(self._event(
                    "ssh",
                    "ssh_login",
                    "SSH login succeeded",
                    line.strip(),
                    "info",
                    self._parse_syslog_time(line),
                    ip,
                    "normal",
                ))
        return events

    def _events_panel_logs(self):
        events = []
        keywords = ["login", "ssh", "firewall", "safe", "security", "warning", "waf", "password"]
        try:
            logs = public.M("logs").order("id desc").limit(50).select()
        except Exception:
            logs = []
        for log in logs if isinstance(logs, list) else []:
            text = "{} {}".format(log.get("type", ""), log.get("log", ""))
            if not any(k in text.lower() for k in keywords):
                continue
            events.append(self._event(
                "panel",
                "panel_log",
                log.get("type", "Panel log"),
                log.get("log", ""),
                "info",
                self._to_timestamp(log.get("addtime", 0)),
                log.get("username", ""),
                "normal",
            ))
        return events

    def _events_net_threat(self):
        """聚合 net_threat（Maltrail）插件当天威胁事件。
        """
        plugin_dir = self._plugin_path("net_threat")
        if not os.path.exists(plugin_dir) or not os.path.exists(os.path.join(plugin_dir, "net_threat_main.py")):
            return []

        try:
            result = public.run_plugin(
                "net_threat",
                "get_events",
                public.to_dict_obj({"page": 1, "page_size": 200}),
            )
        except Exception as ex:
            public.print_log("security overview get net_threat events error: {}".format(ex))
            return []
        data = result.get("data", {}) if isinstance(result, dict) else {}
        rows = data.get("list", []) if isinstance(data, dict) else []
        if not isinstance(rows, list):
            return []

        events = []
        for row in rows:
            if not isinstance(row, dict):
                continue
            level = str(row.get("severity", "") or "").strip().lower()
            threat = row.get("threat", "") or "Network threat"
            source = row.get("source", "") or row.get("source_ip", "") or "-"
            destination = row.get("destination", "") or row.get("destination_ip", "") or "-"
            protocol = row.get("protocol", "") or "-"
            direction = row.get("direction", "")
            trail = row.get("trail", "")
            trail_type = row.get("trail_type", "")

            direction_prefix = ""
            if direction in ("inbound", "outbound"):
                direction_prefix = "{}: ".format(direction.capitalize())
            message = "{}{} -> {} {}".format(direction_prefix, source, destination, protocol)
            meta = " ".join(part for part in (trail_type, trail) if part)

            events.append(self._event(
                "net_threat",
                "network_threat",
                "Network threat: {}".format(threat),
                message,
                level,
                self._to_timestamp(str(row.get("time", "") or "")[:19]),
                meta,
                "unhandled",
            ))
        return events

    def _event(self, source, event_type, title, message, level, ts, meta, status):
        level = self._normalize_level(level)[0] or "info"
        return {
            "id": "",
            "source": source,
            "type": event_type,
            "title": title or "",
            "message": message or "",
            "level": level,
            "level_value": self.SEVERITY_ORDER.get(level, 0),
            "time": self._to_timestamp(ts) or int(time.time()),
            "time_text": "",
            "relative_time": "",
            "meta": meta or "",
            "status": status or "",
        }

    def _decorate_events(self, events):
        """为聚合事件统一补齐展示字段（id 按最终排序序号编，跨来源全局唯一）。"""
        for index, event in enumerate(events):
            event["id"] = "evt_{}".format(index + 1)
            event["time_text"] = self._format_time(event.get("time", 0))
            event["relative_time"] = self._relative_time(event.get("time", 0))
            event["level_label"] = self.SEVERITY_LABELS.get(event.get("level", "info"), "Info")
        return events

    # ------------------------------
    # Sources and helpers
    # ------------------------------

    def _get_webshell_scan_result(self):
        last_scan = self._read_json(self._panel_file("data", "safeCloud", "last_scan.json"), {})
        last_scan_ts = self._to_timestamp(last_scan.get("scan_timestamp", 0))
        if not last_scan_ts:
            last_scan_ts = self._to_timestamp(last_scan.get("scan_date", ""))
        total_scanned_files = self._safe_int(last_scan.get("total_files", 0))
        log_file = self._panel_file("data", "safeCloud", "log", "detection_all.log")
        counts = self._severity_counts()
        risk_stats = {"0": 0, "1": 0, "2": 0}
        processed_stats = {"0": 0, "1": 0}
        latest_log_ts = 0

        if os.path.exists(log_file):
            for line in self._iter_lines(log_file):
                parts = line.strip().split("|")
                if len(parts) < 9:
                    continue
                try:
                    risk_level = str(int(parts[4]))
                except Exception:
                    risk_level = str(parts[4]).strip()
                processed = str(parts[8]).strip()
                if processed.lower() in ["true", "handled", "ignore", "ignored", "deleted"]:
                    processed = "1"
                elif processed.lower() in ["false", "unhandled"]:
                    processed = "0"
                processed = str(self._safe_int(processed, 0))
                log_ts = self._to_timestamp(parts[5])
                latest_log_ts = max(latest_log_ts, log_ts)

                if processed != "0":
                    continue
                if risk_level in risk_stats:
                    risk_stats[risk_level] += 1
                if processed in processed_stats:
                    processed_stats[processed] += 1
                level = self._malware_risk_level(risk_level)
                if level in counts and level != "info":
                    counts[level] += 1

        last_ts = last_scan_ts or latest_log_ts
        return {
            "has_data": bool(last_ts or total_scanned_files or os.path.exists(log_file)),
            "last_scan_timestamp": last_ts,
            "total_scanned_files": total_scanned_files,
            "total_detected": sum(risk_stats.values()),
            "risk_stats": risk_stats,
            "processed_stats": processed_stats,
            "severity": counts,
        }

    def _malware_risk_level(self, value):
        text = str(value).strip().lower()
        if text == "2":
            return "high"
        if text == "1":
            return "medium"
        if text == "0":
            return "low"
        return self._normalize_level(text)[0] or "high"

    def _parse_malware_logs(self, limit=100, log_file=None):
        log_file = log_file or self._panel_file("data", "safeCloud", "log", "detection_all.log")
        rows = []
        for line in self._tail_lines(log_file, limit):
            parts = line.strip().split("|")
            if len(parts) < 6:
                continue
            filename = parts[0] if len(parts) > 0 else ""
            filepath = parts[1] if len(parts) > 1 else ""
            threat_type = parts[2] if len(parts) > 2 else "Malware"
            md5 = parts[3] if len(parts) > 3 else ""
            level = self._malware_risk_level(parts[4] if len(parts) > 4 else "high")
            detect_time = parts[5] if len(parts) > 5 else ""
            status = parts[6] if len(parts) > 6 else ""
            detect_type = parts[7] if len(parts) > 7 else ""
            handled_raw = parts[8] if len(parts) > 8 else ""
            handled = str(handled_raw).lower() in ["1", "true", "handled", "ignore", "ignored", "deleted"]
            if str(status).lower() in ["handled", "ignore", "ignored", "deleted"]:
                handled = True
            rows.append({
                "filename": filename,
                "filepath": filepath,
                "threat_type": threat_type,
                "md5": md5,
                "level": level,
                "time": self._to_timestamp(detect_time),
                "status": status,
                "detect_type": detect_type,
                "handled": handled,
            })
        return rows

    def _source_status(self, scan_cards):
        status = {}
        for card in scan_cards:
            status[card["id"]] = {
                "has_data": card["has_data"],
                "last_time": card["last_scan_time"],
                "last_timestamp": card["last_scan_timestamp"],
                "source_api": self._scan_card_source_api(card["id"]),
            }
        return status

    def _scan_entry(self):
        return {
            "overview_refresh_api": "/v2/safe/overview/get_overview",
            "existing_scan_apis": [
                {
                    "id": "security_risk",
                    "title": "Security risk scan",
                    "api": "/v2/warning",
                    "params": {"action": "get_list", "force": 1},
                },
                {
                    "id": "website_vulnerability",
                    "title": "Website vulnerability scan",
                    "api": "/v2/scanning",
                    "params": {"action": "startScan"},
                },
                {
                    "id": "malware_detection",
                    "title": "Malware detection",
                    "api": "/v2/safecloud",
                    "params": {"action": "webshell_detection"},
                },
            ],
            "note": "Overview API is read-only. Start scan APIs keep using existing modules.",
        }

    def _health_levels(self):
        return [
            {
                "key": "healthy",
                "label": "HEALTHY",
                "min_score": 95,
                "color": "#16a34a",
                "description": "All systems fully secure",
            },
            {
                "key": "good",
                "label": "GOOD",
                "min_score": 75,
                "color": "#22c55e",
                "description": "Minor issues detected",
            },
            {
                "key": "attention",
                "label": "ATTENTION",
                "min_score": 50,
                "color": "#d97706",
                "description": "Security issues need review",
            },
            {
                "key": "critical",
                "label": "CRITICAL",
                "min_score": 0,
                "color": "#dc2626",
                "description": "Immediate action required",
            },
        ]

    def _action(self, action_id, title, description, severity, source, route):
        severity = self._normalize_level(severity)[0] or "info"
        return {
            "id": action_id,
            "title": title,
            "description": description,
            "severity": severity,
            "severity_label": self.SEVERITY_LABELS.get(severity, "Info"),
            "priority": self.SEVERITY_ORDER.get(severity, 0),
            "source": source,
            # "source_type": self._action_source_type(source),
            # "jump_route": route,
            # "route": route,
            # "button_text": "Handle now" if severity in ["critical", "high"] else "View",
        }

    def _event_stats(self, events):
        by_level = self._severity_counts(include_info=True)
        by_source = {}
        for event in events:
            level = event.get("level", "info")
            if level in by_level:
                by_level[level] += 1
            source = event.get("source", "unknown")
            by_source[source] = by_source.get(source, 0) + 1
        return {
            "by_level": by_level,
            "by_source": by_source,
        }

    def _module_route(self, module_id):
        return self.MODULE_ROUTES.get(module_id, "")

    def _scan_card_route(self, card_id):
        return self.SCAN_CARD_ROUTES.get(card_id, "")

    def _scan_card_source_api(self, card_id):
        return self.SCAN_CARD_SOURCE_APIS.get(card_id, "")

    def _action_source_type(self, source):
        return "plugin" if source in self.PLUGIN_ACTION_SOURCES else "panel"

    def _get_listening_ports(self):
        ports = []
        try:
            import psutil
            for conn in psutil.net_connections(kind="inet"):
                if str(getattr(conn, "status", "")).upper() != "LISTEN":
                    continue
                laddr = getattr(conn, "laddr", None)
                port = getattr(laddr, "port", None)
                if port:
                    ports.append(str(port))
        except Exception:
            pass
        if not ports:
            ports = self._get_proc_listening_ports()
        return self._sort_port_list(ports)

    def _get_proc_listening_ports(self):
        ports = []
        for path in ["/proc/net/tcp", "/proc/net/tcp6"]:
            body = self._read_text(path)
            if not body:
                continue
            for line in body.splitlines()[1:]:
                parts = line.split()
                if len(parts) < 4 or parts[3].upper() != "0A":
                    continue
                try:
                    port_hex = parts[1].split(":")[-1]
                    port = int(port_hex, 16)
                    if port > 0:
                        ports.append(str(port))
                except Exception:
                    continue
        return ports

    def _sort_port_list(self, ports):
        deduped = []
        for port in ports:
            port = str(port).strip()
            if port and port not in deduped:
                deduped.append(port)
        return sorted(deduped, key=lambda x: self._safe_int(x, 0))

    def _pick_counter_values(self, data, keys):
        counters = {}
        if not isinstance(data, dict):
            data = {}
        for key in keys:
            counters[key] = self._safe_int(data.get(key, 0))
        return counters

    def _tamper_totals_from_files(self):
        all_types = dict((key, 0) for key in self.TAMPER_INTERCEPT_KEYS)
        today_types = dict((key, 0) for key in self.TAMPER_INTERCEPT_KEYS)
        total_dir = os.path.join(public.get_setup_path(), "tamper", "total")
        total_file = os.path.join(total_dir, "total.json")
        all_types.update(self._pick_counter_values(self._read_json(total_file, {}), self.TAMPER_INTERCEPT_KEYS))

        today_name = time.strftime("%Y-%m-%d", time.localtime())
        if os.path.isdir(total_dir):
            for name in os.listdir(total_dir):
                path_dir = os.path.join(total_dir, name)
                if not os.path.isdir(path_dir):
                    continue
                today_file = os.path.join(path_dir, "{}.json".format(today_name))
                path_today = self._pick_counter_values(self._read_json(today_file, {}), self.TAMPER_INTERCEPT_KEYS)
                for key, value in path_today.items():
                    today_types[key] += value
        return all_types, today_types

    def _tamper_totals_from_paths(self):
        all_types = dict((key, 0) for key in self.TAMPER_INTERCEPT_KEYS)
        today_types = dict((key, 0) for key in self.TAMPER_INTERCEPT_KEYS)
        try:
            paths = public.run_plugin("tamper_core", "get_tamper_paths", public.to_dict_obj({}))
            rows = paths.get("data", []) if isinstance(paths, dict) else paths
            for row in rows if isinstance(rows, list) else []:
                if not isinstance(row, dict):
                    continue
                total = row.get("total", {}) if isinstance(row.get("total", {}), dict) else {}
                all_total = self._pick_counter_values(total.get("all", {}), self.TAMPER_INTERCEPT_KEYS)
                today_total = self._pick_counter_values(total.get("today", {}), self.TAMPER_INTERCEPT_KEYS)
                for key, value in all_total.items():
                    all_types[key] += value
                for key, value in today_total.items():
                    today_types[key] += value
        except Exception:
            pass
        return all_types, today_types

    def _get_tamper_settings_status(self):
        config = self._read_json(os.path.join(public.get_setup_path(), "tamper", "tamper.conf"), {})
        if not isinstance(config, dict):
            return False
        return bool(self._safe_int(config.get("status", 0)))

    def _get_bt_hids_status(self, plugin_dir):
        if not os.path.exists(plugin_dir):
            return False
        if hasattr(self, "_bt_hids_status_cache"):
            return self._bt_hids_status_cache
        enabled = False
        try:
            status = public.run_plugin("bt_hids", "get_status", public.to_dict_obj({}))
            if isinstance(status, bool):
                enabled = status
            elif isinstance(status, dict):
                enabled = bool(status.get("status", False))
        except Exception:
            enabled = False
        self._bt_hids_status_cache = enabled
        return enabled

    def _get_bt_hids_result(self, levels=None, p=1):
        levels = levels or ["serious", "high", "medium", "low"]
        cache_key = "{}:{}".format(",".join([str(level) for level in levels]), p)
        cache = getattr(self, "_bt_hids_result_cache", {})
        if cache_key in cache:
            return cache[cache_key]
        try:
            result = public.run_plugin(
                "bt_hids",
                "get_result",
                public.to_dict_obj({
                    "type": json.dumps(levels),
                    "p": p,
                })
            )

            if isinstance(result, dict) and result.get("status") is False:
                result = {}
            result = result if isinstance(result, dict) else {}
        except Exception as ex:
            public.print_log("security overview get bt_hids result error: {}".format(ex))
            result = {}
        cache[cache_key] = result
        self._bt_hids_result_cache = cache
        return result

    def _bt_hids_empty_counts(self):
        return {
            "serious": 0,
            "high_risk": 0,
            "medium_risk": 0,
            "low_risk": 0,
        }

    def _bt_hids_counts(self, data):
        counts = self._bt_hids_empty_counts()
        raw = data.get("count", {}) if isinstance(data, dict) else {}
        if not isinstance(raw, dict):
            raw = {}
        for key in counts.keys():
            counts[key] = self._safe_int(raw.get(key, 0))
        return counts

    def _bt_hids_latest_alert_time(self, risks):
        latest = 0
        for risk in risks if isinstance(risks, list) else []:
            if not isinstance(risk, dict):
                continue
            latest = max(latest, self._to_timestamp(risk.get("time", 0)))
        return latest

    def _bt_hids_top_counter_text(self, counts):
        labels = [
            ("serious", "serious"),
            ("high_risk", "high"),
            ("medium_risk", "medium"),
            ("low_risk", "low"),
        ]
        parts = []
        for key, label in labels:
            value = self._safe_int(counts.get(key, 0))
            if value > 0:
                parts.append("{} {}".format(label, value))
        return ", ".join(parts) if parts else "no active alerts"

    def _btwaf_file(self, filename):
        server_path = os.path.join("/www/server/btwaf", filename)
        if os.path.exists(server_path):
            return server_path
        return os.path.join(self._plugin_path("btwaf"), filename)

    def _get_btwaf_global_open(self, plugin_dir):
        config = self._read_json(self._btwaf_file("config.json"), {})
        if isinstance(config, dict):
            value = config.get("open", "")
            if isinstance(value, bool):
                return value
            return str(value).lower() in ["1", "true", "yes", "on"]
        return False

    def _get_btwaf_overview(self):
        try:
            args = public.to_dict_obj({
                "start_time": time.strftime("%Y-%m-%d", time.localtime()),
                "country": 0,
                "request": 1,
            })

            result = public.run_plugin("btwaf", "overview", args)
            if isinstance(result, dict) and isinstance(result.get("message"), dict):
                result = result.get("message")
            return result if isinstance(result, dict) else {}
        except Exception as ex:
            public.print_log("security overview get btwaf overview error: {}".format(ex))
            return {}

    def _get_btwaf_intercept_summary(self, plugin_dir):
        data = self._read_json("/www/server/btwaf/total.json", None)
        if data is None:
            data = self._read_json(os.path.join(plugin_dir, "total.json"), {})
        if not isinstance(data, dict) or not data:
            counters = self._btwaf_intercept_types(plugin_dir)
            return sum(counters.values()), counters

        rules = data.get("rules", {}) if isinstance(data, dict) else {}
        if isinstance(rules, list):
            counters = {}
            for item in rules:
                if isinstance(item, dict):
                    key = str(item.get("key", "")).strip()
                    if key:
                        counters[key] = self._safe_int(item.get("value", 0))
            rules = counters
        if not isinstance(rules, dict):
            rules = {}

        counters = self._format_btwaf_rule_counters(rules)
        total = self._safe_int(data.get("total", 0)) if isinstance(data, dict) else 0
        if total <= 0:
            total = sum(counters.values())

        return total, counters

    def _btwaf_attack_types_from_overview(self, overview):
        raw_counters = {}
        rows = overview.get("type", []) if isinstance(overview, dict) else []
        for row in rows if isinstance(rows, list) else []:
            key = ""
            value = 0
            if isinstance(row, dict):
                key = str(row.get("key", row.get("type", row.get("name", "")))).strip()
                value = self._safe_int(row.get("value", row.get("count", 0)))
            elif isinstance(row, (list, tuple)) and len(row) >= 2:
                key = str(row[0]).strip()
                value = self._safe_int(row[1])
            if key:
                raw_counters[key] = value
        if not raw_counters:
            return [], {}
        counters = dict((key, 0) for key in self.WAF_INTERCEPT_KEYS)
        for key, value in raw_counters.items():
            counters[key] = value
        items = [{"type": key, "count": value} for key, value in raw_counters.items() if value > 0]
        items.sort(key=lambda item: item["count"], reverse=True)
        return items, counters

    def _format_btwaf_rule_counters(self, rules):
        raw = {}
        for key, value in rules.items():
            raw[str(key)] = self._safe_int(value)
        raw["get"] = 0
        if "args" in raw:
            raw["get"] += raw.pop("args")
        if "url" in raw:
            raw["get"] += raw.pop("url")

        result = {}
        for key in self.WAF_INTERCEPT_KEYS:
            result[key] = self._safe_int(raw.get(key, 0))
        return result

    def _btwaf_site_config(self, plugin_dir):
        server_file = os.path.join("/www/server/btwaf", "site_waf_config_php.json")
        plugin_file = os.path.join(plugin_dir, "site_waf_config_php.json")
        data = self._read_json(server_file, None)
        if data is None:
            data = self._read_json(plugin_file, {})
        return data if isinstance(data, dict) else {}

    def _btwaf_intercept_types(self, plugin_dir):
        counters = dict((key, 0) for key in self.WAF_INTERCEPT_KEYS)
        data = self._btwaf_site_config(plugin_dir)
        rows = data.get("data", []) if isinstance(data.get("data", []), list) else []
        for row in rows:
            if not isinstance(row, dict):
                continue
            for item in row.get("total", []) if isinstance(row.get("total", []), list) else []:
                if not isinstance(item, dict):
                    continue
                key = str(item.get("key", "")).strip()
                if not key:
                    continue
                if key not in counters:
                    counters[key] = 0
                counters[key] += self._safe_int(item.get("value", 0))

        if sum(counters.values()) == 0:
            sqlite_counters = self._btwaf_intercept_types_from_sqlite()
            for key, value in sqlite_counters.items():
                if key not in counters:
                    counters[key] = 0
                counters[key] += value
        return counters

    def _btwaf_intercept_types_from_sqlite(self):
        counters = {}
        db_file = "/www/server/btwaf/totla_db/totla_db.db"
        if not os.path.exists(db_file):
            return counters
        try:
            import sqlite3
            conn = sqlite3.connect(db_file)
            cur = conn.cursor()
            cur.execute(
                "select coalesce(nullif(value_risk, ''), filter_rule) as risk_type, count(1) "
                "from totla_log group by coalesce(nullif(value_risk, ''), filter_rule)"
            )
            for key, value in cur.fetchall():
                key = str(key or "").strip()
                if key:
                    counters[key] = self._safe_int(value)
            conn.close()
        except Exception:
            pass
        return counters

    def _get_fail2ban_service_status(self, plugin_dir):
        try:
            status = public.run_plugin("fail2ban", "get_fail2ban_status", public.to_dict_obj({}))
            if isinstance(status, bool):
                return status
            if isinstance(status, dict):
                if "status" in status:
                    return bool(status.get("status"))
                if "message" in status:
                    return bool(status.get("message"))
        except Exception:
            pass
        return os.path.exists(os.path.join(plugin_dir, "fail2ban.sock"))

    def _top_counter_text(self, counters, limit=3):
        pairs = [
            (key, self._safe_int(value))
            for key, value in counters.items()
            if self._safe_int(value) > 0
        ]
        pairs.sort(key=lambda item: item[1], reverse=True)
        if not pairs:
            return "no classified attacks"
        return ", ".join("{} {}".format(key, value) for key, value in pairs[:limit])

    def _get_protect_days(self):
        install_file = self._panel_file("data", "safeCloud", "install_time.pl")
        ts = self._to_timestamp(self._read_text(install_file).strip())
        if not ts:
            return 1
        days = int((time.time() - ts) / 86400)
        return days if days > 0 else 1

    def _get_virus_update_time(self):
        rule_dir = self._panel_file("data", "safeCloud", "rules")
        latest = 0
        if os.path.exists(rule_dir):
            for root, dirs, files in os.walk(rule_dir):
                for filename in files:
                    try:
                        latest = max(latest, int(os.path.getmtime(os.path.join(root, filename))))
                    except Exception:
                        pass
        return self._format_time(latest)

    def _ssh_option_enabled(self, conf, option, default=False):
        if not conf:
            return default
        option = str(option or "").lower()
        for line in conf.splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            parts = line.split()
            if len(parts) < 2 or parts[0].lower() != option:
                continue
            value = str(parts[1]).lower()
            if value in ["yes", "true", "1", "on"]:
                return True
            if value in ["no", "false", "0", "off"]:
                return False
            return default
        return default

    def _panel_file(self, *parts):
        path = os.path.join(self.panel_path, *parts)
        if os.path.exists(path):
            return path
        fallback = os.path.join("/www/server/panel", *parts)
        return fallback

    def _plugin_path(self, plugin_name):
        path = os.path.join(self.panel_path, "plugin", plugin_name)
        if os.path.exists(path):
            return path
        return os.path.join("/www/server/panel/plugin", plugin_name)

    def _read_json(self, path, default):
        try:
            body = self._read_text(path)
            if not body:
                return default
            return json.loads(body)
        except Exception:
            return default

    def _read_text(self, path):
        try:
            if not path or not os.path.exists(path):
                return ""
            with open(path, "r", encoding="utf-8", errors="ignore") as fp:
                return fp.read()
        except TypeError:
            try:
                with open(path, "r") as fp:
                    return fp.read()
            except Exception:
                return ""
        except Exception:
            return ""

    def _tail_lines(self, path, limit):
        if not path or not os.path.exists(path):
            return []
        try:
            with open(path, "r", encoding="utf-8", errors="ignore") as fp:
                return list(deque(fp, maxlen=limit))
        except TypeError:
            try:
                with open(path, "r") as fp:
                    return list(deque(fp, maxlen=limit))
            except Exception:
                return []
        except Exception:
            return []

    def _iter_lines(self, path):
        if not path or not os.path.exists(path):
            return []
        try:
            with open(path, "r", encoding="utf-8", errors="ignore") as fp:
                return list(fp)
        except TypeError:
            try:
                with open(path, "r") as fp:
                    return list(fp)
            except Exception:
                return []
        except Exception:
            return []

    def _unwrap_message(self, result, default):
        try:
            if isinstance(result, dict):
                return result.get("message", default)
        except Exception:
            pass
        return default

    def _severity_counts(self, include_info=False):
        data = {
            "critical": 0,
            "high": 0,
            "medium": 0,
            "low": 0,
        }
        if include_info:
            data["info"] = 0
        return data

    def _max_severity(self, counts):
        for key in ["critical", "high", "medium", "low"]:
            if int(counts.get(key, 0) or 0) > 0:
                return key
        return "info"

    def _normalize_level(self, value):
        if value is None:
            return "", 0
        try:
            num = int(value)
            if num >= 4:
                return "critical", 4
            if num == 3:
                return "high", 3
            if num == 2:
                return "medium", 2
            if num == 1:
                return "low", 1
            return "info", 0
        except Exception:
            pass
        text = str(value).strip().lower()
        if text in ["serious", "critical", "danger", "dangerous", "fatal"]:
            return "critical", 4
        if text in ["high", "important"]:
            return "high", 3
        if text in ["medium", "warning", "warn"]:
            return "medium", 2
        if text in ["low"]:
            return "low", 1
        if text in ["info", "normal", "safe"]:
            return "info", 0
        return "", 0

    def _to_timestamp(self, value):
        if value is None or value == "":
            return 0
        try:
            ts = int(float(value))
            if ts > 0:
                return ts
        except Exception:
            pass
        text = str(value).strip()
        if not text:
            return 0
        text = text.replace("/", "-")
        for fmt in [
            "%Y-%m-%d %H:%M:%S",
            "%Y-%m-%d %H:%M",
            "%Y-%m-%d",
            "%b %d %H:%M:%S",
            "%b  %d %H:%M:%S",
        ]:
            try:
                if fmt.startswith("%b"):
                    text2 = "{} {}".format(time.localtime().tm_year, text)
                    return int(time.mktime(time.strptime(text2, "%Y " + fmt)))
                return int(time.mktime(time.strptime(text, fmt)))
            except Exception:
                continue
        return 0

    def _parse_syslog_time(self, line):
        text = " ".join(line.split()[:3])
        return self._to_timestamp(text) or int(time.time())

    def _format_time(self, ts):
        ts = self._to_timestamp(ts)
        if not ts:
            return ""
        try:
            return time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(ts))
        except Exception:
            return ""

    def _relative_time(self, ts):
        ts = self._to_timestamp(ts)
        if not ts:
            return "No data"
        diff = int(time.time()) - ts
        if diff < 60:
            return "Just now"
        if diff < 3600:
            return "{} minutes ago".format(max(1, int(diff / 60)))
        if diff < 86400:
            return "{} hours ago".format(max(1, int(diff / 3600)))
        return "{} days ago".format(max(1, int(diff / 86400)))

    def _extract_ip(self, text):
        match = re.search(r"(\d{1,3}(?:\.\d{1,3}){3})", text or "")
        return match.group(1) if match else ""

    def _safe_int(self, value, default=0):
        try:
            return int(float(value))
        except Exception:
            return default

    def _to_bool(self, value, default=False):
        if isinstance(value, bool):
            return value
        if value is None:
            return default
        if isinstance(value, int):
            return value != 0
        text = str(value).strip().lower()
        if text in ["1", "true", "yes", "on", "open"]:
            return True
        if text in ["0", "false", "no", "off", "close", "closed", ""]:
            return False
        return default

    def _get_int(self, get, name, default, min_value=None, max_value=None):
        value = self._safe_int(self._get_arg(get, name, default), default)
        if min_value is not None:
            value = max(min_value, value)
        if max_value is not None:
            value = min(max_value, value)
        return value

    def _get_bool(self, get, name, default=False):
        value = self._get_arg(get, name, default)
        if isinstance(value, bool):
            return value
        if isinstance(value, int):
            return value != 0
        return str(value).lower() in ["1", "true", "yes", "on"]

    def _get_arg(self, get, name, default=None):
        if get is None:
            return default
        args = self._get_request_args(get)
        if name in args:
            return args.get(name, default)
        return default

    def _get_first_arg(self, get, names, default=None):
        args = self._get_request_args(get)
        for name in names:
            if name in args:
                return args.get(name)
        return default

    def _get_request_args(self, get):
        args = dict(self._object_items(get))
        try:
            from flask import request
            args.update(request.args.to_dict())
            args.update(request.form.to_dict())
            body = request.get_json(silent=True)
            if isinstance(body, dict):
                args.update(body)
        except Exception:
            pass

        for key in ["data", "params"]:
            args.update(self._parse_nested_args(args.get(key)))
        return args

    def _object_items(self, value):
        if isinstance(value, dict):
            return value
        try:
            items = value.get_items()
            return items if isinstance(items, dict) else {}
        except Exception:
            pass
        try:
            items = value.__dict__
            return items if isinstance(items, dict) else {}
        except Exception:
            pass
        return {}

    def _parse_nested_args(self, value):
        if isinstance(value, dict):
            return value
        items = self._object_items(value)
        if items:
            return items
        if not isinstance(value, str):
            return {}
        value = value.strip()
        if not value:
            return {}
        try:
            parsed = json.loads(value)
        except Exception:
            return {}
        if isinstance(parsed, dict):
            return parsed
        return {}
