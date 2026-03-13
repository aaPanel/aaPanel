#!/www/sererv/panel/penv/bin/python3
# coding: utf-8
# -----------------------------
# aapanel Python项目准备脚本
# -----------------------------
import json
import sys
import os

os.chdir("/www/server/panel")
if "/www/server/panel" not in sys.path:
    sys.path.insert(0, "/www/server/panel")
if "/www/server/panel/class" not in sys.path:
    sys.path.insert(0, "/www/server/panel/class")
if "/www/server/panel/class_v2" not in sys.path:
    sys.path.insert(0, "/www/server/panel/class_v2")


import public
from projectModelV2.pythonModel import main as pythonMod


def main(pj_id: int):
    project_info = public.M('sites').where('id=? ', (pj_id,)).find()
    if not isinstance(project_info, dict):
        print("project not found!")
    values = json.loads(project_info["project_config"])
    pythonMod().simple_prep_env(values)



if __name__ == '__main__':
    if len(sys.argv) > 1:
        project_id = sys.argv[1]
        try:
            project_id = int(project_id)
        except:
            exit(1)
        else:
            main(project_id)
