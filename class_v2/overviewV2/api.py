# coding: utf-8
# -------------------------------------------------------------------
# aaPanel
# -------------------------------------------------------------------
# Copyright (c) 2014-2099 aaPanel(www.aapanel.com) All rights reserved.
# -------------------------------------------------------------------
# Author: aapanel
# -------------------------------------------------------------------

# ------------------------------
# overview app
# ------------------------------
import json
import os
from typing import Callable

import public
from overviewV2.base import OverViewBase, DISPLAY
from public.exceptions import HintException
from public.validate import Param

public.sys_path_append("class_v2/")

PANEL_PATH = public.get_panel_path()


class OverViewApi(OverViewBase):
    PLUGIN_DIR = os.path.join(PANEL_PATH, "plugin")
    TEMPLATE = os.path.join(PANEL_PATH, "config/overview_template.json")
    SETTING = os.path.join(PANEL_PATH, "config/overview_setting.json")

    def __init__(self):
        overview_setting = []
        if not os.path.isfile(self.SETTING):
            try:
                temp_data = json.loads(public.readFile(self.TEMPLATE))
            except Exception as e:
                public.print_log(f"error read overview template: {e}")
                temp_data = []
            id = 0
            for temp in temp_data:
                for option in temp.get("option", []):
                    if option.get("name") in [
                        "sites", "ftps", "databases", "security",
                    ]:
                        option["id"] = id
                        option["template"] = temp["template"]
                        option["params"] = [
                            p["option"][0] for p in option.get("params", []) if p.get("option")
                        ]
                        id += 1
                        overview_setting.append(option)
            public.writeFile(self.SETTING, json.dumps(overview_setting))

    def _check_plugin_install(self, overview: dict):
        if overview.get("type") == "plugin":
            if not overview.get("name"):
                pass
            if not os.path.exists(os.path.join(self.PLUGIN_DIR, overview["name"])):
                raise HintException(f"[{overview.get('name')}] Plugin Not Installed!")

    def _dynamic_info(self, overview: dict, replace_title: bool = True) -> dict:
        # icon desc
        if DISPLAY.get(overview["name"]):
            overview["icon"] = DISPLAY[overview["name"]]["icon"]
            overview["desc"] = DISPLAY[overview["name"]]["desc"]
        # route
        router_inplace = ["sites", "databases"]
        try:
            if overview.get("name") in router_inplace and len(overview.get("params", [])) == 1:
                point = overview["params"][0].get("source")
                if not point:
                    return overview
                if point == "mongodb":
                    point = "mongo"

                if point == "all":
                    if overview["name"] == "sites":
                        point = "php"
                    elif overview["name"] == "databases":
                        point = "mysql"

                overview["source"]["href"] = f'{overview["source"]["href"]}/{point}'
        except Exception:
            import traceback
            public.print_log(traceback.format_exc())

        # replace Title
        try:
            if replace_title and overview.get("name") == "monitor":
                params = overview.get("params", [])
                act = params[-1].get("name", "monitor")
                overview["title"] = f"Monitor - {act}"

            if replace_title and overview.get("name") == "sites":
                params = overview.get("params", [])
                act = params[-1].get("name", "php")
                overview["title"] = f"Site - {act}"
        except Exception:
            import traceback
            public.print_log(traceback.format_exc())

        return overview

    def overview_template(self, get):
        """
        @name 获取概览模板
        """
        try:
            temp_data = json.loads(public.readFile(self.TEMPLATE))
        except Exception as e:
            raise HintException(e)

        select_option_dict = {
            "site_all": public.M("sites").field("name").select()
        }
        for template in temp_data:
            template_option = template.get("option", [])
            for i in range(len(template_option) - 1, -1, -1):
                option = template_option[i]
                # display
                option = self._dynamic_info(option, replace_title=False)

                if not option.get("status", False):
                    if option.get("type") == "plugin":  # 插件
                        plugin_path = os.path.join(self.PLUGIN_DIR, option["name"])
                        option["status"] = os.path.exists(plugin_path)

                # 填充参数选项数据
                option_params = option.get("params", [])
                for params in option_params:
                    # select_option 监控报表, 提供选择站点
                    select_option = params.get("select_option")
                    if select_option is not None and select_option_dict.get(select_option) is not None:
                        params["option"] = select_option_dict.get(select_option)
                        for site in params["option"]:
                            site["source"] = site["name"]

        return public.success_v2(temp_data)

    def get_overview(self, get):
        """
        @name 获取概览
        """
        try:
            overview_setting = public.readFile(self.SETTING) or "[]"
            overview_setting = json.loads(overview_setting)
            if not isinstance(overview_setting, list):
                raise Exception("overview_setting format error")
            if len(overview_setting) == 0:
                raise Exception("overview_setting is empty")
        except Exception as ex:
            public.print_log("get_overview error info: {}".format(ex))
            public.ExecShell("rm -f {}".format(self.SETTING))
            overview_setting = []

        func_dict = {
            "sites": self._base,
            "ftps": self._base,
            "databases": self._base,
            "security": self._security,
            "ssh_log": self._ssh_log,
            "ssl": self._ssl,
            "corn": self._corn,
            "btwaf": self._btwaf,
            "monitor": self._monitor,
            "tamper_core": self._tamper_core,
            "alarm_logs": self._alarm_logs,
        }

        nlist = []
        for overview in overview_setting:
            overview["value"] = []
            # display
            overview = self._dynamic_info(overview)
            params_list = overview.get("params", [])

            if overview.get("status", False):
                func: Callable[[str, list], list] = func_dict.get(overview["name"])
                if func is not None:
                    overview["value"] = func(overview["name"], params_list)

            nlist.append(overview)
        return public.success_v2(overview_setting)

    def get_overview_window(self, get):
        """
        params = {
            "model": "ssl",
            "source": "all"
        }
        """
        try:
            get.validate([
                Param("model").String().Require(),
                Param("source").String().Require(),
            ], [
                public.validate.trim_filter(),
            ])

            if get.model == "ssl" and get.source not in [
                "all", "normal", "renew_fail", "expirin_soon"
            ]:
                return public.fail_v2(
                    "[ssl] source value mustbe one of 'all', 'normal', 'renew_fail', 'expirin_soon'"
                )

            if get.model == "alarm_log" and get.source not in [
                "all", "handled", "unhandled"
            ]:
                return public.fail_v2(
                    "[alarm_log] source value mustbe one of 'all', 'handled', 'unhandled'"
                )
        except Exception as ex:
            public.print_log("get_overview_window error info: {}".format(ex))
            return public.fail_v2(str(ex))

        data = []
        if get.model == "ssl":
            if get.source != "all":
                data = self._base_ssl(get.source)
            else:
                data = []
                for tag in ["expirin_soon", "renew_fail", "normal"]:
                    data.extend(self._base_ssl(tag))
                sorted(data, key=lambda x: x.get("id", 0))
        return public.success_v2(data)

    def add_overview(self, get):
        try:
            get.validate([
                Param("overview").String().Require(),
            ], [
                public.validate.trim_filter(),
            ])
            overview = json.loads(get.overview)
            overview_setting = public.readFile(self.SETTING) or "[]"
        except Exception as ex:
            public.print_log("add_overview error info: {}".format(ex))
            return public.fail_v2(str(ex))
        self._check_plugin_install(overview)
        try:
            overview_setting = json.loads(overview_setting)
        except json.JSONDecodeError:
            overview_setting = []

        if len(overview_setting) >= 6:
            return public.fail_v2("Overview Full, Max 6 Items!")

        if overview.get("value") is not None:
            del overview["value"]

        max_id = 0
        for over in overview_setting:
            if over["name"] == overview["name"]:
                return public.success_v2(public.lang("Overview Exist!"))

            if int(over["id"]) > max_id:
                max_id = int(over["id"])

        overview["id"] = max_id + 1
        overview_setting.append(overview)

        public.writeFile(self.SETTING, json.dumps(overview_setting))
        return public.success_v2(public.lang("Overview Add Successfully!"))

    def set_overview(self, get):
        try:
            get.validate([
                Param("overview").String().Require(),
            ], [
                public.validate.trim_filter(),
            ])
            overview = json.loads(get.overview)
        except Exception as ex:
            public.print_log("set_overview error info: {}".format(ex))
            return public.fail_v2(str(ex))
        self._check_plugin_install(overview)
        overview_setting = []
        if isinstance(overview, list):
            overview_setting = overview
        elif isinstance(overview, dict):
            try:
                overview_setting = public.readFile(self.SETTING)
                overview_setting = json.loads(overview_setting)
            except Exception as err:
                public.print_log("set_overview readFile error info: {}".format(err))
                overview_setting = []

            if overview.get("value") is not None:
                del overview["value"]

            for idx in range(len(overview_setting)):
                over = overview_setting[idx]
                if int(over["id"]) == int(overview["id"]):
                    overview_setting[idx] = overview
                    break
            else:
                return public.fail_v2("Overview Not Found!")

        public.writeFile(self.SETTING, json.dumps(overview_setting))
        return public.success_v2(public.lang("Overview Set Successfully!"))

    def del_overview(self, get):
        try:
            get.validate([
                Param("overview_id").Integer().Require(),
            ], [
                public.validate.trim_filter(),
            ])
            overview_setting = public.readFile(self.SETTING)
            overview_setting = json.loads(overview_setting)
        except Exception as ex:
            public.print_log("del_overview error info: {}".format(ex))
            return public.fail_v2(str(ex))

        if len(overview_setting) <= 1:
            return public.fail_v2("Overview At Least One Item!")

        overview_id = int(get.overview_id)
        for idx in range(len(overview_setting) - 1, -1, -1):
            over = overview_setting[idx]
            if int(over["id"]) == overview_id:
                del overview_setting[idx]
                break

        public.writeFile(self.SETTING, json.dumps(overview_setting))
        return public.success_v2(public.lang("Overview Delete Successfully!"))

    def sort_overview(self, get):
        try:
            get.validate([
                Param("sort_ids").String().Require(),
            ], [
                public.validate.trim_filter(),
            ])
            sort_ids = json.loads(get.sort_ids)
            overview_setting = public.readFile(self.SETTING)
            overview_setting = json.loads(overview_setting)
        except Exception as ex:
            public.print_log("sort_overview error info: {}".format(ex))
            return public.fail_v2(str(ex))

        new_overview_setting = []
        for pk in sort_ids:
            for over in overview_setting:
                if int(over["id"]) == int(pk):
                    new_overview_setting.append(over)
                    break

        public.writeFile(self.SETTING, json.dumps(new_overview_setting))
        return public.success_v2(public.lang("Successfully!"))


def update_overview():
    # 同步模板中的更新, 同时移除不存在的项
    try:
        api = OverViewApi()
        template_data = json.loads(public.readFile(api.TEMPLATE))
        settings = json.loads(public.readFile(api.SETTING))
        new_settings = []
        for setting in settings:
            for template in template_data:
                for op in template.get("option", []):
                    if setting["name"] == op["name"]:
                        try:
                            new_settings.append(
                                {
                                    "title": op["title"],
                                    "name": setting["name"],
                                    "status": setting.get("status", False),
                                    "type": op["type"],
                                    "source": op.get("source", {}),
                                    "params": setting["params"],
                                    "icon": op.get("icon", ""),
                                    "desc": op.get("desc", ""),
                                    "id": setting["id"],
                                    "template": op.get("template", ""),
                                }
                            )
                        except Exception as e:
                            public.print_log("update_overview item error:".format(str(e)))
                            continue
        public.writeFile(OverViewApi.SETTING, json.dumps(new_settings))
    except:
        pass


update_overview()
