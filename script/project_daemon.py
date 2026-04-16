import json
import os
import sys
import time

panel_path = '/www/server/panel'
os.chdir(panel_path)
if "/www/server/panel/class" not in sys.path:
    sys.path.insert(0, "/www/server/panel/class")
if "/www/server/panel" not in sys.path:
    sys.path.insert(0, "/www/server/panel")

import public


class Counter:
    FAILURE_DIR = '/www/server/panel/data/project_daemon_failures'
    MAX_COUNT = 10

    @classmethod
    def _get_fail_flag(cls, id_project_name: str):
        """获取项目失败记录文件路径"""
        return os.path.join(cls.FAILURE_DIR, '{}.pl'.format(id_project_name))

    @classmethod
    def is_skip(cls, id_project_name) -> bool:
        """判断项目是否应该被守护进程跳过"""
        return cls.get_fail(id_project_name) >= cls.MAX_COUNT

    @classmethod
    def get_fail(cls, id_project_name) -> int:
        """获取项目失败次数"""
        fail_file = cls._get_fail_flag(id_project_name)
        if not os.path.exists(fail_file):
            return 0
        try:
            return int(public.readFile(fail_file) or 0)
        except:
            return 0

    @classmethod
    def add_fail(cls, id_project_name) -> None:
        """增加项目失败计数"""
        fail_file = Counter._get_fail_flag(id_project_name)
        try:
            count = cls.get_fail(id_project_name) + 1
            if count > cls.MAX_COUNT:
                return
            public.writeFile(fail_file, str(count))
        except Exception as e:
            public.print_log("add_fail_count error: {}".format(e))

    @classmethod
    def clear_fail(cls, id_project_name) -> None:
        """清除项目失败计数"""
        fail_file = cls._get_fail_flag(id_project_name)
        try:
            if os.path.exists(fail_file):
                os.remove(fail_file)
        except Exception as e:
            public.print_log("clear_fail_count error: {}".format(e))


def PythonDaemons():
    """
        @name Python 项目守护进程
        @author baozi@bt.cn
        @time 2023-10-21
    """
    if public.M('sites').where('project_type=?', ('Python',)).count() >= 1:
        project_info = public.M('sites').where('project_type=?', ('Python',)).select()
        for i in project_info:
            id_project_name = "{}_{}".format(i['id'], i['name'])
            # 检查失败次数, 则静默跳过
            if Counter.is_skip(id_project_name):
                continue
            try:
                from projectModelV2 import pythonModel
                # sites 表中的 project_config
                i['project_config'] = json.loads(i['project_config'])
                # auto_run, 自启,守护 的关键字段
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
                    res = python_obj.StartProject(get)
                    if res.get("status", -1) != 0:
                        # 失败增加计数
                        Counter.add_fail(id_project_name)
                        continue
                    public.WriteLog('Project Daemon', 'Python project [{}] auto start!'.format(i['name']))
                    # 正常启动成功,清除失败计数
                    Counter.clear_fail(id_project_name)
            except Exception:
                # 异常兜底,增加失败计数
                Counter.add_fail(id_project_name)
                import traceback
                print("Python Daemon Error: {}".format(traceback.format_exc()))
                continue


def NodeDaemons():
    if public.M('sites').where('project_type=?', ('Node',)).count() >= 1:
        project_info = public.M('sites').where('project_type=?', ('Node',)).select()
        from projectModelV2 import nodejsModel
        from mod.project.nodejs import comMod

        for i in project_info:
            id_project_name = "{}_{}".format(i['id'], i['name'])
            if Counter.is_skip(id_project_name):
                continue

            try:
                i['project_config'] = json.loads(i['project_config'])
                # 查看网站自启开关，node 默认为is_power_on
                if 'is_power_on' in i['project_config'] and i['project_config']['is_power_on'] in ["1", 1, True, "true"]:
                    p_type = 'pm2' if i['project_config'].get('pm2_name') else 'nodejs'
                    node_obj = nodejsModel.main()

                    # 判断状态
                    status = node_obj.get_project_info(public.to_dict_obj({"project_name": i['name']}))
                    if status['status'] == 0 and status.get('message').get('run') in [True, 'true']:
                        continue

                    # 区分PM2与nodejs项目
                    if p_type == 'pm2':
                        if not node_obj.get_project_run(project_name=i['project_config'].get('pm2_name'),
                                                        project_type='pm2'):
                            res = comMod.main().set_project_status(public.to_dict_obj(
                                {"project_name": i['name'], "project_type": p_type, "status": "start",
                                 "pm2_name": i['project_config'].get('pm2_name')}))
                            if res.get("status", -1) != 0:
                                public.WriteLog('Project Daemon','Node.js project [{}] Startup failed!'.format(i['name']))
                                Counter.add_fail(id_project_name)
                                continue
                    else:
                        if not node_obj.get_project_run(project_name=i['name'], project_type='node'):
                            res = comMod.main().set_project_status(public.to_dict_obj(
                                {"project_name": i['name'], "project_type": p_type, "status": "start"}))
                            if res.get("status", -1) != 0:
                                public.WriteLog('Project Daemon','Node.js project [{}] Startup failed!'.format(i['name']))
                                Counter.add_fail(id_project_name)
                                continue

                    # 进行二次校验，避免成功启动后马上挂掉
                    time.sleep(3)
                    status = node_obj.get_project_info(public.to_dict_obj({"project_name": i['name']}))
                    if status['status'] == 0 and status.get('message').get('run') in [True, 'true']:
                        public.WriteLog('Project Daemon', 'Node.js project [{}] auto start!'.format(i['name']))
                        Counter.clear_fail(id_project_name)
                        continue

                    public.WriteLog('Project Daemon', 'Node.js project [{}] Startup failed!'.format(i['name']))
                    Counter.add_fail(id_project_name)
            except Exception:
                Counter.add_fail(id_project_name)
                import traceback
                print("Node.js Daemon Error: {}".format(traceback.format_exc()))
                continue

def GoDaemons():
    """
        @name Go 项目守护进程
        @author hzh@bt.cn
        @time 2026-04-15
        @modified 2026-04-15
        检测Go项目运行状态，如果项目异常停止（非用户手动停止），尝试重启
        启动失败会记录日志并累计失败次数，超过10次后跳过该项目
    """
    go_pid_path = '/var/tmp/gopids'

    if public.M('sites').where('project_type=?', ('Go')).count() >= 1:
        project_info = public.M('sites').where('project_type=?', ('Go')).select()
        from projectModelV2 import goModel

        for i in project_info:
            id_project_name = "{}_{}".format(i['id'], i['name'])
            # 检查失败次数，超过10次则静默跳过
            if Counter.is_skip(id_project_name):
                continue

            try:
                i['project_config'] = json.loads(i['project_config'])
                # 检查是否开启自启动
                if 'is_power_on' in i['project_config'] and i['project_config']['is_power_on'] in ["1", 1, True, "true"]:
                    go_obj = goModel.main()
                    pid_file = "{}/{}.pid".format(go_pid_path, i['name'])

                    # 检查项目运行状态
                    is_running = go_obj.get_project_run_state(project_name=i['name'])
                    if is_running:
                        # 项目正常运行，清除失败计数，并标记为非用户停止状态
                        Counter.clear_fail(id_project_name)
                        go_obj.start_by_user(i['id'])  # 标记项目正在运行（非用户停止状态）
                        continue

                    # 项目未运行，检查是否为异常停止（PID文件存在但进程不存在）
                    pid_file_exists = os.path.exists(pid_file)
                    process_was_killed = False

                    if pid_file_exists:
                        try:
                            pid_content = public.readFile(pid_file)
                            if pid_content:
                                old_pid = int(pid_content)
                                # PID文件存在但进程不存在 = 异常停止
                                if not os.path.exists('/proc/{}'.format(old_pid)):
                                    process_was_killed = True
                        except:
                            process_was_killed = True  # 读取失败也视为异常

                    if process_was_killed:
                        # 项目被异常停止（kill或崩溃），清理残留PID文件后尝试重启
                        try:
                            os.remove(pid_file)
                        except:
                            pass

                        # 重置用户停止状态，因为项目是异常停止的
                        go_obj.start_by_user(i['id'])

                        get = public.dict_obj()
                        get.project_name = i['name']
                        res = go_obj.start_project(get)

                        if res.get("status", -1) != 0:
                            error_msg = res.get('msg', 'Unknown error')
                            public.WriteLog('Project Daemon', 'Go project [{}] auto restart failed after abnormal stop! Error: {}'.format(i['name'], error_msg))
                            Counter.add_fail(id_project_name)
                            continue

                        # 启动成功，等待3秒进行二次校验
                        time.sleep(3)
                        if go_obj.get_project_run_state(project_name=i['name']):
                            public.WriteLog('Project Daemon', 'Go project [{}] auto restart success after abnormal stop!'.format(i['name']))
                            Counter.clear_fail(id_project_name)
                        else:
                            public.WriteLog('Project Daemon', 'Go project [{}] auto restart failed! Project crashed after startup'.format(i['name']))
                            Counter.add_fail(id_project_name)
                        continue

                    # 项目未运行且PID文件不存在，检查是否为用户通过面板手动停止
                    if go_obj.is_stop_by_user(i['id']):
                        # 用户通过面板停止按钮停止的项目，不自动启动
                        continue

            except Exception:
                Counter.add_fail(id_project_name)
                import traceback
                error_info = traceback.format_exc()
                public.WriteLog('Project Daemon', 'Go project [{}] daemon error: {}'.format(i['name'], error_info[:500]))
                continue


def main():
    # go, java, python, nodejs...
    GoDaemons()
    NodeDaemons()
    PythonDaemons()


if __name__ == '__main__':
    main()
