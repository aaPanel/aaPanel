import json
import os
import sys

panel_path = '/www/server/panel'
os.chdir(panel_path)
if "/www/server/panel/class" not in sys.path:
    sys.path.insert(0, "/www/server/panel/class")
if "/www/server/panel" not in sys.path:
    sys.path.insert(0, "/www/server/panel")

import public


def PythonDaemons():
    """
        @name Python 项目守护进程
        @author baozi@bt.cn
        @time 2023-10-21
    """
    if public.M('sites').where('project_type=?', ('Python',)).count() >= 1:
        project_info = public.M('sites').where('project_type=?', ('Python',)).select()
        for i in project_info:
            try:
                from projectModelV2 import pythonModel
                # sites 表中的 project_config
                i['project_config'] = json.loads(i['project_config'])
                # auto_run, 自启,守护
                if 'auto_run' in i['project_config'] and i['project_config']['auto_run'] in ["1", 1, True, "true"]:
                    python_obj = pythonModel.main()
                    # 项目的运行状态是否为运行中
                    if python_obj.get_project_run_state(project_name=i['name']):
                        continue
                    # 项目是否被用户停止了, 则不再自动启动
                    if python_obj.is_stop_by_user(i["id"]):
                        continue
                    get = public.dict_obj()
                    get.name = i['name']
                    # StartProject
                    python_obj.StartProject(get)
                    public.WriteLog('Project Daemon', 'Python project [{}] auto start!'.format(i['name']))
            except Exception:
                import traceback
                print("Python Daemon Error: {}".format(traceback.format_exc()))
                continue


def NodeDaemons():
    if public.M('sites').where('project_type=?', ('Node',)).count() >= 1:
        project_info = public.M('sites').where('project_type=?', ('Node',)).select()
        from projectModelV2 import nodejsModel
        for i in project_info:
            try:
                i['project_config'] = json.loads(i['project_config'])
                if 'is_power_on' in i['project_config'] and i['project_config']['is_power_on'] in ["1", 1, True, "true"]:  # node 默认为is_power_on
                    node_obj = nodejsModel.main()
                    get = public.dict_obj()
                    get.project_name = i['name']
                    if node_obj._get_project_run_state(get):
                        continue
                    # StartProject
                    node_obj.start_project(get)
                    public.WriteLog('Project Daemon', 'Node.js project [{}] auto start!'.format(i['name']))
            except Exception:
                import traceback
                print("Node.js Daemon Error: {}".format(traceback.format_exc()))
                continue


def GoDaemons():
    pass


def main():
    # go, java, python, nodejs...
    GoDaemons()
    NodeDaemons()
    PythonDaemons()


if __name__ == '__main__':
    main()
