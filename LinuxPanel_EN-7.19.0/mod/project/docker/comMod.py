# coding: utf-8
# -------------------------------------------------------------------
# 宝塔Linux面板
# -------------------------------------------------------------------
# Copyright (c) 2015-2099 宝塔软件(http://bt.cn) All rights reserved.
# -------------------------------------------------------------------
# Author: wzz <wzz@bt.cn>
# -------------------------------------------------------------------
# ------------------------------
# docker模型
# ------------------------------
import json
import os
import sys
import time

if "/www/server/panel/class" not in sys.path:
    sys.path.insert(0, "/www/server/panel/class")

os.chdir("/www/server/panel")
import public

from mod.project.docker.app.appManageMod import AppManage
from btdockerModelV2 import dk_public as dp


class main(AppManage):

    def __init__(self):
        super(main, self).__init__()

    # 2024/6/26 下午5:49 获取所有已部署的项目列表
    def get_project_list(self, get):
        '''
            @name 获取所有已部署的项目列表
            @author wzz <2024/6/26 下午5:49>
            @param "data":{"参数名":""} <数据类型> 参数描述
            @return dict{"status":True/False,"msg":"提示信息"}
        '''
        try:
            if self.def_name is None: self.set_def_name(get.def_name)
            if hasattr(get, '_ws') and hasattr(get._ws, 'btws_get_project_list'):
                return

            while True:
                compose_list = self.ls(get)
                if len(compose_list) == 0:
                    if hasattr(get, '_ws'):
                        get._ws.send(json.dumps(self.wsResult(
                            True,
                            data=[],
                        )))


                stacks_info = dp.sql("stacks").select()

                compose_project = []

                for j in compose_list:
                    t_status = j["Status"].split(",")
                    container_count = 0
                    for ts in t_status:
                        container_count += int(ts.split("(")[1].split(")")[0])

                    j_name = j['Name']
                    if "bt_compose_" in j_name:
                        config_path = "{}/config/name_map.json".format(public.get_panel_path())
                        name_map = json.loads(public.readFile(config_path))
                        if j_name in name_map:
                            j_name = name_map[j_name]
                        else:
                            j_name = j_name.replace("bt_compose_", "")

                    tmp = {
                        "id": None,
                        "name": j_name,
                        "status": "1",
                        "path": j['ConfigFiles'],
                        "template_id": None,
                        "time": None,
                        "remark": "",
                        "run_status": j['Status'].split("(")[0].lower(),
                        "container_count": container_count,
                    }
                    for i in stacks_info:
                        if public.md5(i['name']) in j['Name']:

                            tmp["name"] = i['name']
                            tmp["run_status"] = j['Status'].split("(")[0].lower()
                            tmp["template_id"] = i['template_id']
                            tmp["time"] = i['time']
                            tmp["remark"] = i["remark"]
                            tmp["id"] = i['id']
                            break

                        if i['name'] == j['Name']:
                            tmp["run_status"] = j['Status'].split("(")[0].lower()
                            tmp["template_id"] = i['template_id']
                            tmp["time"] = i['time']
                            tmp["remark"] = i["remark"]
                            tmp["id"] = i['id']
                            break

                    if tmp["time"] is None:
                        if os.path.exists(j['ConfigFiles']):
                            get.path = j['ConfigFiles']
                            compose_ps = self.ps(get)
                            if len(compose_ps) > 0 and "CreatedAt" in compose_ps[0]:
                                tmp["time"] = dp.convert_timezone_str_to_timestamp(compose_ps[0]['CreatedAt'])

                    compose_project.append(tmp)

                if hasattr(get, '_ws'):
                    setattr(get._ws, 'btws_get_project_list', True)
                    get._ws.send(json.dumps(self.wsResult(
                        True,
                        data=sorted(compose_project, key=lambda x: x["time"] if x["time"] is not None else float('-inf'), reverse=True),
                    )))

                time.sleep(2)
        except Exception as e:
            return public.returnResult(False, str(e))

    # 2024/6/26 下午8:55 获取指定compose.yml的docker-compose ps
    def get_project_ps(self, get):
        '''
            @name 获取指定compose.yml的docker-compose ps
            @author wzz <2024/6/26 下午8:56>
            @param "data":{"参数名":""} <数据类型> 参数描述
            @return dict{"status":True/False,"msg":"提示信息"}
        '''
        try:
            if self.def_name is None: self.set_def_name(get.def_name)
            if hasattr(get, '_ws') and hasattr(get._ws, 'btws_get_project_ps_{}'.format(get.path)):
                return

            from btdockerModelV2.dockerSock import container
            sk_container = container.dockerContainer()

            while True:
                compose_list = self.ps(get)
                if len(compose_list) == 0:
                    if hasattr(get, '_ws'):
                        get._ws.send(json.dumps(self.wsResult(
                            True,
                            data=[],
                        )))
                    break

                for l in compose_list:
                    if not "Image" in l:
                        l["Image"] = ""
                        if "ID" in l:
                            l["inspect"] = sk_container.get_container_inspect(l["ID"])
                            l["Image"] = l["inspect"]["Config"]["Image"]

                    if not "Ports" in l:
                        l["Ports"] = ""
                        if "Publishers" in l and not l["Publishers"] is None:
                            for p in l["Publishers"]:
                                if p["URL"] == "":
                                    l["Ports"] += "{}/{},".format(p["TargetPort"], p["Protocol"])
                                    continue

                                l["Ports"] += "{}:{}->{}/{},".format(p["URL"], p["PublishedPort"], p["TargetPort"], p["Protocol"])

                if hasattr(get, '_ws'):
                    setattr(get._ws, 'btws_get_project_ps_{}'.format(get.path), True)
                    get._ws.send(json.dumps(self.wsResult(
                        True,
                        data=compose_list,
                    )))

                time.sleep(2)
        except Exception as e:
            return public.returnResult(False, str(e))


if __name__ == '__main__':
    pass
