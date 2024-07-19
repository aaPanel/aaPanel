# coding: utf-8
# -------------------------------------------------------------------
# aaPanel
# -------------------------------------------------------------------
# Copyright (c) 2015-2099 aaPanel(www.aapanel.com) All rights reserved.
# -------------------------------------------------------------------
# Author: zhengweibiao
# -------------------------------------------------------------------

# ------------------------------
# 容器项目编排
# ------------------------------
import os, sys, re, json, shutil, psutil, time
import datetime
import public
from btdockerModelV2.containerModel import main as docker
import subprocess





class main():

    next_id = 1  # 将 next_id 设为类变量，而不是实例变量
    def __init__(self):
        # self.next_id = 1
        pass

    def load_project_data(self):
        json_file = "/www/server/panel/class_v2/btdockerModelV2/docker_project_groups.json"
        try:
            with open(json_file, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            data = []
            with open(json_file, 'w') as f:
                json.dump(data, f)

            return data
        except Exception as e:
            return None

    def write_to_json(self, data):
        json_file = "/www/server/panel/class_v2/btdockerModelV2/docker_project_groups.json"
        try:
            with open(json_file, 'w') as f:
                json.dump(data, f)
            return True
        except Exception as e:
            print("写入失败！{}".format(e))
            return False

    def get_project_groups(self, get):

        data = self.load_project_data()
        if data is None:
            return public.returnMsg(False, "获取配置文件失败")

        # 获取项目列表
        project_list =  docker().get_list(get)

        # 更新每个项目组的状态
        for group in data:
            # 检查项目排序是否为空
            if not group['order']:
                group['status'] = 0  # 如果项目排序为空，状态为停止
                continue

            all_running = True  # 假设所有的项目都在运行
            for project in group['projects']:
                for p in project_list['container_list']:
                    if p['name'] == project['project_name']:
                        if  p['status']!="running":  # 如果项目没有运行
                            all_running = False
                            break
                if not all_running:
                    break

            if all_running:
                group['status'] = 1  # 如果所有的项目都在运行，状态为启动
            else:
                group['status'] = 0

        return public.returnMsg(True, data)

    def get_group_data(self, get):
        try:
            data = self.load_project_data()
            if data is None:
                return None, public.returnMsg(False, "获取配置文件失败！")

            project_list = docker().get_list(get)
            for group in data:
                if group['id'] == int(get.id):
                    for project in group['projects']:
                        
                        print(project)
                        # print(project_list['container_list'])
                        for p in project_list['container_list']:
                            if p['name'] == project['project_name']:
                                print(3333)
                                print(p)
                                project['status'] = p['status']
                    return group, None
            return None, public.ReturnMsg(False, "项目不存在！")

        except Exception as e:
            return None, public.returnMsg(False, "获取失败！" + str(e))

    def get_project_details(self, get):
        print(33333)
        group, error_msg = self.get_group_data(get)
        if error_msg:
            return error_msg

        group['projects'].sort(
            key=lambda x: group['order'].index(x['project_name']))
        return public.returnMsg(True, group['projects'])

    def get_project_group_details(self, get):
        group, error_msg = self.get_group_data(get)
        if error_msg:
            return error_msg
        return public.returnMsg(True, group)

    def add_project_group(self, get):

        try:
            data = self.load_project_data()
            if data is None:
                return public.returnMsg(False, "获取配置文件失败")

            # 检查是否已存在
            for group in data:
                if group['group_name'] == get.group_name:
                    return public.returnMsg(False, "项目已存在！")

            # 添加新的项目
            new_group = {
                "id": self.next_id,  # 使用 next_id 作为新的 id
                "group_name": get.group_name,
                # "status": 0,
                "interval": 30,
                "projects": [],
                "order": [],
            }
            data.append(new_group)

            # 更新 next_id

            main.next_id += 1
            if not self.write_to_json(data):
                return public.returnMsg(False, "写入失败！")

            return public.returnMsg(True, "项目添加成功！")

        except Exception as e:

            return public.returnMsg(False, "添加失败！" + str(e))

    def edit_project_order(self, get):

        try:
            data = self.load_project_data()
            if data is None:
                return public.returnMsg(False, "获取配置文件失败")
            # 找到指定的项目组
            for group in data:
                if group['id']==int(get.id):
                    new_order=get.order.split(',')
                    if sorted(new_order) != sorted(group['order']):
                        return public.returnMsg(False, "无效的容器顺序！") 
                    group['order']=new_order          
                if not self.write_to_json(data):
                        return public.returnMsg(False, "写入失败！")
                return public.returnMsg(True,"容器顺序修改成功！")
            return public.returnMsg(False,"项目不存在！")  
        except Exception as e:
            return public.returnMsg(False,"修改失败："+str(e))
                           
    def edit_group_interval(self, get):
        try:
            data = self.load_project_data()
            if data is None:
                return public.returnMsg(False, "获取配置文件失败")
            
        
            # 找到指定的项目
            for group in data:
                if group['id'] == int(get.id):
                    # 检查新的项目顺序是否有效
                    group['interval'] = get.interval
                    break
            else:
                return public.returnMsg(False, "项目不存在！")

            if not self.write_to_json(data):
                    return public.returnMsg(False, "写入失败！")

            return public.returnMsg(True, "项目时间间隔修改成功！")
        except Exception as e:
            return public.returnMsg(False, "修改失败！" + str(e))

    def start_projects_in_order(self, get):

        try:
            data = self.load_project_data()
            if data is None:
                return public.returnMsg(False, "获取配置文件失败")
            project_list=docker().get_list(get)['container_list']

            for group in data:
                if group['id']==int(get.id):
                    # 如果pid存在并且进程仍在运行，那么就不允许用户再次启动项目
                    if 'start_pid' in group and self.is_process_running(group['start_pid']):
                        return public.returnMsg(False,"正在依次启动容器中！")

                    project_order=group['order']
                    
                    running_projects=[project for project in project_order if self.is_project_running(project,project_list)]
               
                    if running_projects and not get.get("force_stop",False):
                        return public.returnMsg(False,"以下容器正在运行：{}。是否允许先强制停止再启动？您也可以选择自己手动停止运行中的容器！".format(",".join(running_projects)))

                    with open('/dev/null','w') as devnull:
                        process=subprocess.Popen(['btpython','/www/server/panel/script/set_docker_project_groups.py','--id',str(group['id']),"--action","start"],stdout=devnull,stderr=devnull)



                    pid=process.pid
                    group['start_pid']=pid
                    if not self.write_to_json(data):
                       return public.returnMsg(False, "写入失败！") 

            return public.returnMsg(True, "开始依次启动容器！")
        except Exception as e:
            return public.returnMsg(False, "启动失败！"+str(e))

    def is_process_running(self,pid):
        try:
            os.kill(pid,0)
        except OSError:
            return False
        else:
            return True


    def is_project_running(self,project_name,project_list):
        for project in project_list:
            if project['name']==project_name and project['status']=="running":
                return True
        return False

    def stop_projects_in_order(self, get):
        try:
            data = self.load_project_data()
            if data is None:
                return public.returnMsg(False, "获取配置文件失败")
            for group in data:
                if group['id']==int(get.id):
                    # 如果pid存在并且进程仍在运行，那么就不允许用户再次停stop_pid止项目
                    if 'stop_pid' in group and self.is_process_running(group['stop_pid']):
                        return public.returnMsg(False,"正在依次停止容器中！")
                    with open("/dev/null","w") as devnull:
                        process=subprocess.Popen(['btpython','/www/server/panel/script/set_docker_project_groups.py','--id',str(group['id']),"--action","stop"],stdout=devnull,stderr=devnull)
                    
                    pid=process.pid
                    group['stop_pid']=pid
                    if not self.write_to_json(data):
                       return public.returnMsg(False, "写入失败！") 
            return public.returnMsg(True,"容器开始按顺序停止")

        except Exception as e:
            return public.returnMsg(False, "停止失败！" + str(e))


    def start_group(self, args_id):

        try:
            get = public.dict_obj()
            data = self.load_project_data()
            if data is None:
                return public.returnMsg(False, "获取配置文件失败")
            # 找到指定的项目
            for group in data:
                if group['id'] == int(args_id):
                    # 获取项目排序
                    project_order = group['order']

                    # 停止所有项目
                    for project_name in project_order:
                        container_id = None
                        for project in group['projects']:
                            if project['project_name'] == project_name:
                                container_id = project['project_id']
                                break
                        if container_id:
                            # print()
                            # docker().set_container_status(public.dict_obj({
                            #     "id": container_id,
                            #     "status": "stop"
                            # }))
                            print(33333333333333)
                            get.status = "stop"
                            get.id = container_id
                            docker().set_container_status(get)
                    # time.sleep(30)
                    # 依次启动项目
                    for project_name in project_order:
                        container_id = None
                        for project in group['projects']:
                            if project['project_name'] == project_name:
                                container_id = project['project_id']
                                break
                        if container_id:
                            # print()
                            # docker().set_container_status(public.dict_obj({
                            #     "id": container_id,
                            #     "status": "stop"
                            # }))
                            get.status = "start"
                            get.id = container_id
                            start_result=docker().set_container_status(get)
                        
                        if not start_result['status']:
                            return start_result  # 如果启动失败，立即返回错误信息

                        # 暂停指定的时间间隔
                        time.sleep(int(group['interval']))
            if not self.is_process_running(group['pid']):
                # 删除pid
                del group['pid']
                if not self.write_to_json(data):
                    return public.returnMsg(False, "写入失败！") 
        except Exception as e:
            print("启动失败！" + str(e))


    def stop_group(self, args_id):

        
        try:
            get = public.dict_obj()
            data = self.load_project_data()
            if data is None:
                return public.returnMsg(False, "获取配置文件失败")
            # 找到指定的项目
            for group in data:
                if group['id'] == int(args_id):
                    # 获取项目排序
                    project_order = group['order']

                    # 停止所有项目
                    for project_name in project_order:
                        container_id = None
                        for project in group['projects']:
                            if project['project_name'] == project_name:
                                container_id = project['project_id']
                                break
                        if container_id:
                            get.status = "stop"
                            get.id = container_id
                            docker().set_container_status(get)
        except Exception as e:
            print("启动失败！" + str(e))

    def modify_group_status(self, get):
        group_ids=[int(id) for id in get.id.split(",")]

        for group_id in group_ids:
            get.id=group_id
            if get.status=="1":
                return self.start_projects_in_order(get)
            elif get.status=="0":
                return self.stop_projects_in_order(get)
            else:
                return public.returnMsg(False,"无效的状态！")
    


    def add_project_to_group(self, get):
       
        try:

            data = self.load_project_data()
            if data is None:
                return public.returnMsg(False, "获取配置文件失败")
            # 检查项目是否已被其他项目组添加
            for group in data:
                for project in group['projects']:
                    if project['project_name']==get.project_name:
                       return public.returnMsg(False,"容器 {} 已经被项目组 {} 添加了！".format(get.project_name,group['group_name']))
            for group in data:
                if group['id']==int(get.id):
                    new_project={
                    "project_id":get.project_id,
                    "project_name":get.project_name,


                    }
                    group['projects'].append(new_project)
                    group['order'].append(get.project_name)
                    break
            

            if not self.write_to_json(data):
                    return public.returnMsg(False, "写入失败！") 

            return public.returnMsg(True, "容器添加成功！")
        except Exception as e:
            return public.returnMsg(False, "添加失败！" + str(e))

    def remove_project_from_group(self, get):
        try:
            data = self.load_project_data()
            if data is None:
                return public.returnMsg(False, "获取配置文件失败")

            # 将 get.project_name 分割成一个列表
            project_names=get.project_name.split(",")

            # 找到指定的项目
            for group in data:
                if group['id']==int(get.id):
                    # 删除指定的项目组
                    group['projects']=[project for project in group['projects'] if project['project_name'] not in project_names]
                    # 同时更新order列表，移除已删除的项目名称
                    group['order'] = [project_name for project_name in group['order'] if project_name not in project_names]
                    break
                else:
                    return public.returnMsg(False,"项目不存在！")

            # 将更新后的数据写回文件
            if not self.write_to_json(data):
                    return public.returnMsg(False, "写入失败！")

            return public.returnMsg(True, "容器删除成功！")
        except Exception as e:
            return public.returnMsg(False, "删除失败！" + str(e))

    def delete_project_group(self, get):
     
        try:
            data = self.load_project_data()
            if data is None:
                return public.returnMsg(False, "获取配置文件失败")

            # 将 get.id 分割成一个列表
            group_ids=[int(id) for id in get.id.split(",")]
            # 找到并删除指定的项目
            data=[group for group in data if group['id'] not in group_ids]
            # 将更新后的数据写回文件
            if not self.write_to_json(data):
                    return public.returnMsg(False, "写入失败！")

            return public.returnMsg(True, "项目删除成功！")
        except Exception as e:
            return public.returnMsg(False, "删除失败！" + str(e))
