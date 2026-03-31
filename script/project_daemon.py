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
        from mod.project.nodejs import comMod
        for i in project_info:
            try:
                i['project_config'] = json.loads(i['project_config'])
                if 'is_power_on' in i['project_config'] and i['project_config']['is_power_on'] in ["1", 1, True, "true"]:  # node 默认为is_power_on
                    p_type = 'pm2' if i['project_config'].get('pm2_name') else 'nodejs'
                    node_obj = nodejsModel.main()
                    # 判断状态
                    status = node_obj.get_project_info(public.to_dict_obj({"project_name": i['name']}))
                    if status['status'] == 0 and status.get('message').get('run') in [True,'true']:
                        continue
                    if p_type == 'pm2':
                        if not node_obj.get_project_run(project_name=i['project_config'].get('pm2_name'), project_type = 'pm2'):
                            comMod.main().set_project_status(public.to_dict_obj({"project_name":i['name'],"project_type":p_type,"status":"start","pm2_name":i['project_config'].get('pm2_name')}))
                    else:
                        if not node_obj.get_project_run(project_name=i['name'], project_type = 'node'):
                            comMod.main().set_project_status(public.to_dict_obj({"project_name":i['name'],"project_type":p_type,"status":"start"}))
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
