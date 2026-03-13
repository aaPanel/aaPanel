# -*- coding: utf-8 -*-
# -----------------------------
# Website Project Restart Script
# -----------------------------
# author: aaPanel

import os
import sys
from importlib import import_module
from typing import Optional, Any

if "/www/server/panel" not in sys.path:
    sys.path.insert(0, '/www/server/panel')
if "/www/server/panel/class" not in sys.path:
    sys.path.insert(0, '/www/server/panel/class')
if "/www/server/panel/class_v2" not in sys.path:
    sys.path.insert(0, '/www/server/panel/class_v2')

os.chdir('/www/server/panel')

import public


def get_action_model_obj(model_name: str) -> Optional[Any]:
    try:
        if model_name in "java" and os.path.exists("/www/server/panel/mod/project/java/projectMod.py"):
            model = import_module("mod.project.java.projectMod")
        else:
            model = import_module("projectModelV2." + model_name + "Model")
    except:
        return None

    if not hasattr(model, "main"):
        return None
    main_class = getattr(model, "main")
    if not callable(main_class):
        return None
    return main_class()


def restart_project_based_on_model(model_name: str, project_name: str):
    try:
        print(public.lang(f"Starting to restart {model_name} project [{project_name}]..."))
        model_obj = get_action_model_obj(model_name)
        if not model_obj:
            print(public.lang(f"Failed to load operation class for model {model_name}."))
            return
        res = model_obj.restart_project(public.to_dict_obj({
            "project_name": project_name
        }))
        if res['status'] != 0:
            print(public.lang(f"Failed to restart project [{project_name}]. {res.get('msg', '')}"))
            return
        print(public.lang("Project [{}] Restarted Successfully!").format(project_name))
    except Exception as e:
        print(public.get_error_info())
        print("Error: " + str(e))


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python restart_project.py <model_name> <project_name>")
    restart_project_based_on_model(sys.argv[1], sys.argv[2])
