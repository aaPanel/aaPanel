import json
import os.path
import traceback
from typing import List, Dict, Optional

import simple_websocket
from mod.base import json_response
from mod.project.node.dbutil import FileTransfer, FileTransferTask, FileTransferDB, ServerNodeDB
from mod.project.node.nodeutil import ServerNode, LocalNode, LPanelNode
from mod.project.node.filetransfer import task_running_log, wait_running

import public


class main():
    log_dir = "{}/logs/node_file_transfers".format(public.get_panel_path())
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)

    @staticmethod
    def file_upload(args):
        node_id = args.get('node_id', -1)
        if node_id == -1:
            from BTPanel import request
            node_id = request.form.get('node_id', 0)

        if not node_id:
            return public.return_message(-1, 0,"node_id is null")

        if isinstance(node_id, str):
            try:
                node_id = int(node_id)
            except:
                return public.return_message(-1, 0,"node_id is null")

        node = ServerNode.new_by_id(node_id)
        if not node:
            return public.return_message(-1, 0,"node not exists")

        return node.upload_proxy()

    @staticmethod
    def file_download(args):
        node_id = args.get('node_id', 0)
        if not node_id:
            return public.return_message(-1, 0,"node_id is null")

        filename = args.get('filename/s', "")
        if not filename:
            return jpublic.return_message(-1, 0,"The filename parameter cannot be empty")
        if isinstance(node_id, str):
            try:
                node_id = int(node_id)
            except:
                return public.return_message(-1, 0,"node_id is null")

        node = ServerNode.new_by_id(node_id)
        if not node:
            return public.return_message(-1, 0,"node not exists")

        return node.download_proxy(filename)

    @staticmethod
    def dir_walk(get):
        path = get.get('path/s', "")
        if not path:
            return public.return_message(-1, 0,"The path parameter cannot be empty")

        res_list, err = LocalNode().dir_walk(path)
        if err:
            return public.return_message(-1, 0,err)
        return res_list

    @classmethod
    def create_filetransfer_task(cls, get):
        ft_db = FileTransferDB()
        task_data, err = ft_db.get_last_task()
        if err:
            return public.return_message(-1, 0,err)
        if task_data and task_data["status"] not in ("complete", "failed"):
            return public.return_message(-1, 0,"There are ongoing tasks on the current node, please wait for them to complete before submitting")

        public.set_module_logs("nodes_create_filetransfer_9", "create_filetransfer")
        source_node_id = get.get('source_node_id/d', -1)
        target_node_id = get.get('target_node_id/d', -1)
        source_path_list = get.get('source_path_list/s', "")
        target_path = get.get('target_path/s', "")
        default_mode = get.get('default_mode/s', "cover")
        if default_mode not in ("cover", "ignore", "rename"):
            return public.return_message(-1, 0,"Default mode parameter error")
        if source_node_id == target_node_id:
            return public.return_message(-1, 0,"The source node and target node cannot be the same")
        if source_node_id == -1 or target_node_id == -1:
            return public.return_message(-1, 0,"The source or destination node cannot be empty")

        try:
            source_path_list = json.loads(source_path_list)
        except:
            return public.return_message(-1, 0,"Error in the parameter 'sourcew_path_ist'")
        keys = ("path", "size", "is_dir")
        for items in source_path_list:
            if not all(item in keys for item in items.keys()):
                return public.return_message(-1, 0,"Error in the parameter 'sourcew_path_ist'")
            if not (isinstance(items["path"], str) and isinstance(items["is_dir"], bool) and
                    isinstance(items["size"], int)):
                return public.return_message(-1, 0,"Error in the parameter 'sourcew_path_ist'")

        if not target_path:
            return public.return_message(-1, 0,"The target_cath parameter cannot be empty")
        node_db = ServerNodeDB()
        if source_node_id == 0:
            src_node = node_db.get_local_node()
        else:
            src_node = node_db.get_node_by_id(source_node_id)
    

        if not src_node:
            return public.return_message(-1, 0,"The source node does not exist")
        if target_node_id == 0:
            target_node = node_db.get_local_node()
        else:
            target_node = node_db.get_node_by_id(target_node_id)
        if not target_node:
            return public.return_message(-1, 0,"The target node does not exist")
        if src_node["id"] == target_node["id"]:
            return public.return_message(-1, 0,"The source node and target node cannot be the same")

        # public.print_log("src_node:", src_node, "target_node:", target_node)
        real_create_res: Optional[dict] = None  # 实际上创建的结果，创建的任务不在本地时使用
        if src_node["api_key"] == src_node["app_key"] == "local":
            return cls._create_filetransfer_task(
                source_node={
                    "name": "local",
                },
                target_node={
                    "name": "{}({})".format(target_node["remarks"], target_node["server_ip"]),
                    "address": target_node["address"],
                    "api_key": target_node["api_key"],
                    "app_key": target_node["app_key"],
                    "node_id": target_node_id,
                    "lpver": target_node["lpver"]
                },
                source_path_list=source_path_list,
                target_path=target_path,
                created_by="local",
                default_mode=default_mode,
            )
        elif target_node["api_key"] == target_node["app_key"] == "local":
            return cls._create_filetransfer_task(
                source_node={
                    "name": "{}({})".format(src_node["remarks"], src_node["server_ip"]),
                    "address": src_node["address"],
                    "api_key": src_node["api_key"],
                    "app_key": src_node["app_key"],
                    "node_id": source_node_id,
                    "lpver": src_node["lpver"]
                },
                target_node={
                    "name": "local",
                },
                source_path_list=source_path_list,
                target_path=target_path,
                created_by="local",
                default_mode=default_mode,
            )
        elif src_node["lpver"]:
            if target_node["lpver"]:
                return public.return_message(-1, 0,"Cannot support file transfer between 1panel nodes")
            # 源节点是1panel时，只能下载去目标节点操作
            if target_node["api_key"] == target_node["app_key"] == "local":
                return cls._create_filetransfer_task(
                    source_node={
                        "name": "{}".format(target_node["remarks"]) + ("({})".format(target_node["server_ip"]) if target_node["server_ip"] else ""),
                        "address": src_node["address"],
                        "api_key": src_node["api_key"],
                        "app_key": "",
                        "node_id": source_node_id,
                        "lpver": src_node["lpver"]
                    },
                    target_node={
                        "name": "local",
                    },
                    source_path_list=source_path_list,
                    target_path=target_path,
                    created_by="local",
                    default_mode=default_mode,
                )
            else:
                srv = ServerNode(target_node["address"], target_node["api_key"], target_node["app_key"])
                real_create_res = srv.node_create_filetransfer_task(
                    source_node={
                        "name": "{}".format(target_node["remarks"]) + ("({})".format(target_node["server_ip"]) if target_node["server_ip"] else ""),
                        "address": src_node["address"],
                        "api_key": src_node["api_key"],
                        "app_key": "",
                        "node_id": source_node_id,
                        "lpver": src_node["lpver"]
                    },
                    target_node={
                        "name": "local",
                    },
                    source_path_list=source_path_list,
                    target_path=target_path,
                    created_by="{}({})".format(public.GetConfigValue("title"), public.get_server_ip()),
                    default_mode=default_mode
                )
        else:  # 都是宝塔节点的情况下
            srv = ServerNode(src_node["address"], src_node["api_key"], src_node["app_key"])
            if srv.filetransfer_version_check():
                srv = ServerNode(target_node["address"], target_node["api_key"], target_node["app_key"])
                res = srv.filetransfer_version_check()
                if res:
                    return public.return_message(-1, 0,"{} Node check error:".format(target_node["remarks"]) +  res)
                real_create_res = srv.node_create_filetransfer_task(
                    source_node={
                        "name": "{}".format(target_node["remarks"]) + ("({})".format(target_node["server_ip"]) if target_node["server_ip"] else ""),
                        "address": src_node["address"],
                        "api_key": src_node["api_key"],
                        "app_key": src_node["app_key"],
                        "node_id": source_node_id,
                        "lpver": src_node["lpver"]
                    },
                    target_node={
                        "name": "local",
                    },
                    source_path_list=source_path_list,
                    target_path=target_path,
                    created_by="{}({})".format(public.GetConfigValue("title"), public.get_server_ip()),
                    default_mode=default_mode,
                )
            else:
                real_create_res = srv.node_create_filetransfer_task(
                    source_node={
                        "name": "local",
                    },
                    target_node={
                        "name": "{}".format(target_node["remarks"]) + ("({})".format(target_node["server_ip"]) if target_node["server_ip"] else ""),
                        "address": target_node["address"],
                        "api_key": target_node["api_key"],
                        "app_key": target_node["app_key"],
                        "node_id": target_node_id,
                        "lpver": target_node["lpver"]
                    },
                    source_path_list=source_path_list,
                    target_path=target_path,
                    created_by="{}({})".format(public.GetConfigValue("title"), public.get_server_ip()),
                    default_mode=default_mode,
                )

        if not real_create_res["status"]:
            return public.return_message(-1, 0,real_create_res["msg"])

        tt_task_id = real_create_res["data"]["task_id"]
        db = FileTransferDB()
        tt = FileTransferTask(
            source_node={"node_id": source_node_id},
            target_node={"node_id": target_node_id},
            source_path_list=source_path_list,
            target_path=target_path,
            task_action=real_create_res["data"]["task_action"],
            status="running",
            created_by="local",
            default_mode=default_mode,
            target_task_id=tt_task_id,
            is_source_node=node_db.is_local_node(source_node_id),
            is_target_node=node_db.is_local_node(target_node_id),
        )
        db.create_task(tt)
        return public.return_message(-1, 0,tt.to_dict())

    @classmethod
    def node_create_filetransfer_task(cls, get):
        from BTPanel import g
        if not g.api_request:
            return public.return_message(-1, 0,"Unable to activate")

        source_node = get.get("source_node/s", "")
        target_node = get.get("target_node/s", "")
        source_path_list = get.get("source_path_list/s", "")
        target_path = get.get("target_path/s", "")
        created_by = get.get("created_by/s", "")
        default_mode = get.get("default_mode/s", "")

        try:
            source_node = json.loads(source_node)
            target_node = json.loads(target_node)
            source_path_list = json.loads(source_path_list)
        except  Exception:
            return public.return_message(-1, 0,"Parameter error")
        if not target_path or not created_by or not default_mode or not source_node or not target_node or not source_path_list:
            return public.return_message(-1, 0,"Parameter loss")

        ft_db = FileTransferDB()
        task_data, err = ft_db.get_last_task()
        if err:
            return public.return_message(-1, 0,err)
        if task_data and task_data["status"] not in ("complete", "failed"):
            return public.return_message(-1, 0,"There is an ongoing task on the node, please wait for it to complete before submitting")
        return cls._create_filetransfer_task(
            source_node=source_node,
            target_node=target_node,
            source_path_list=source_path_list,
            target_path=target_path,
            created_by=created_by,
            default_mode=default_mode
        )

    # 实际创建任务
    # 可能的情况
    # 1.source_node 是当前节点，target_node 是其他节点， 此时为上传
    # 2.target_node 是当前节点， 此时为下载
    @classmethod
    def _create_filetransfer_task(cls, source_node: dict,
                                  target_node: dict,
                                  source_path_list: List[dict],
                                  target_path: str,
                                  created_by: str,
                                  default_mode: str = "cover") -> Dict:
        if source_node["name"] == "local":
            task_action = "upload"
            check_node = LocalNode()
            if target_node["lpver"]:
                t_node = LPanelNode(target_node["address"], target_node["api_key"], target_node["lpver"])
                err = t_node.test_conn()
            else:
                t_node = ServerNode(target_node["address"], target_node["api_key"], target_node["app_key"])
                err = t_node.test_conn()
                # public.print_log(target_node["address"], err)
            if err:
                return public.return_message(-1, 0,"{} Node cannot connect, error message: {}".format(target_node["name"], err))
        elif target_node["name"] == "local":
            task_action = "download"
            if source_node["lpver"]:
                check_node = LPanelNode(source_node["address"], source_node["api_key"], source_node["lpver"])
                err = check_node.test_conn()
            else:
                check_node = ServerNode(source_node["address"], source_node["api_key"], source_node["app_key"])
                err = check_node.test_conn()
                # public.print_log(source_node["address"], err)
            if err:
                return public.return_message(-1, 0,"{} Node cannot connect, error message: {}".format(source_node["name"], err))
        else:
            return public.return_message(-1, 0,"Node information that cannot be processed")

        if check_node.__class__ is ServerNode:
            ver_check = check_node.filetransfer_version_check()
            if ver_check:
                return public.return_message(-1, 0,"{} Node check error:：".format(source_node["name"]) + ver_check)

        target_path = target_path.rstrip("/")
        file_list = []
        for src_item in source_path_list:
            if src_item["is_dir"]:
                f_list, err = check_node.dir_walk(src_item["path"])
                if err:
                    return public.return_message(-1, 0,err)
                if not f_list:
                    src_item["dst_file"] = os.path.join(target_path, os.path.basename(src_item["path"]))
                    file_list.append(src_item)
                else:
                    for f_item in f_list:
                        f_item["dst_file"] = f_item["path"].replace(os.path.dirname(src_item["path"]), target_path)
                        file_list.append(f_item)
            else:
                src_item["dst_file"] = os.path.join(target_path, os.path.basename(src_item["path"]))
                file_list.append(src_item)

            if len(file_list) > 1000:
                return public.return_message(-1, 0,"More than 1000 files, please compress before transferring")

        db = FileTransferDB()
        tt = FileTransferTask(
            source_node=source_node,
            target_node=target_node,
            source_path_list=source_path_list,
            target_path=target_path,
            task_action=task_action,
            status="pending",
            created_by=created_by,
            default_mode=default_mode,
            is_source_node=source_node["name"] == "local",
            is_target_node=target_node["name"] == "local",
        )
        err = db.create_task(tt)
        if err:
            return public.return_message(-1, 0,err)
        ft_list = []
        for f_item in file_list:
            ft = FileTransfer(
                task_id=tt.task_id,
                src_file=f_item["path"],
                dst_file=f_item["dst_file"],
                file_size=f_item["size"],
                is_dir=f_item.get("is_dir", 0),
                status="pending",
                progress=0,
            )
            ft_list.append(ft)
        if not ft_list:
            return public.return_message(-1, 0,"There are no files available for transfer")
        err = db.batch_create_file_transfers(ft_list)
        if err:
            db.delete_task(tt.task_id)
            return public.return_message(-1, 0,err)

        py_bin = public.get_python_bin()
        log_file = "{}/task_{}.log".format(cls.log_dir, tt.task_id)
        start_task = "nohup {} {}/script/node_file_transfers.py {} > {} 2>&1 &".format(
            py_bin,
            public.get_panel_path(),
            tt.task_id,
            log_file,
        )
        res = public.ExecShell(start_task)
        wait_timeout = wait_running(tt.task_id, timeout=10.0)
        if wait_timeout:
            return public.return_message(-1, 0,wait_timeout)
        return public.return_message(0, 0,tt.to_dict())

    @staticmethod
    def file_list(get):
        node_id = get.get("node_id/d", -1)
        p = get.get("p/d", 1)
        row = get.get("showRow/d", 50)
        path = get.get("path/s", "")
        search = get.get("search/s", "")

        if node_id == -1:
            return public.return_message(-1, 0,"Node parameter error")
        if node_id == 0:
            node = LocalNode()
        else:
            node = ServerNode.new_by_id(node_id)

        if not node:
            return public.return_message(-1, 0,"Node does not exist")

        if not path:
            return public.return_message(-1, 0,"Path parameter error")

        data, err = node.file_list(path, p, row, search)
        if err:
            return public.return_message(-1, 0,err)
        if "status" not in data and "message" not in data:return public.return_message(0, 0,data)
        return data

    @staticmethod
    def delete_file(get):
        node_id = get.get("node_id/d", -1)
        if node_id == -1:
            return public.return_message(-1, 0,"Node parameter error")
        if node_id == 0:
            node = LocalNode()
        else:
            node = ServerNode.new_by_id(node_id)

        if not node:
            return public.return_message(-1, 0,"Node does not exist")

        path = get.get("path/s", "")
        is_dir = get.get("is_dir/d", 0)
        if not path:
            return public.return_message(-1, 0,"Path parameter error")
        res=node.remove_file(path, is_dir=is_dir == 1)
        if res.get('status',-1)==0: return public.return_message(0, 0,res.get('message',{}).get('result',"File deleted successfully"))
        if res.get('result','')=='File moved to recycle bin': return public.return_message(0, 0,res.get('msg',"File moved to recycle bin"))
        if res.get('result','')=='Successfully deleted file': return public.return_message(0, 0,res.get('msg',"Successfully deleted file"))
        if res.get('result','')=='Directory moved to recycle bin!': return public.return_message(0, 0,res.get('msg',"Directory moved to recycle bin!"))
        return public.return_message(-1, 0,res.get('msg',"File delete failed"))
        # return node.remove_file(path, is_dir=is_dir == 1)

    def transfer_status(self, get):
        ws: simple_websocket.Server = getattr(get, '_ws', None)
        if not ws:
            return jpublic.return_message(-1, 0,"Please use WebSocket connection")

        ft_db = FileTransferDB()
        task_data, err = ft_db.get_last_task()
        if err:
            ws.send(json.dumps({"type": "error", "msg": err}))
            return
        if not task_data:
            ws.send(json.dumps({"type": "end", "msg": "No tasks"}))
            return
        task = FileTransferTask.from_dict(task_data)
        if task.target_task_id:
            if task.task_action == "upload":
                run_node_id = task.source_node["node_id"]
            else:
                run_node_id = task.target_node["node_id"]
            run_node = ServerNode.new_by_id(run_node_id)
            res = run_node.get_transfer_status(task.target_task_id)
            if not res["status"]:
                ws.send(json.dumps({"type": "error", "msg": res["msg"]}))
                return
            if res["data"]["task"]["status"] in ("complete", "failed"):
                task.status = res["data"]["task"]["status"]
                task.completed_at = res["data"]["task"]["completed_at"]
                ft_db.update_task(task)
                res_data = res["data"]
                res_data["type"] = "end"
                res_data["msg"] = "Mission completed"
                ws.send(json.dumps(res_data))
                return

            run_node.proxy_transfer_status(task.target_task_id, ws)
        else:
            if task.status in ("complete", "failed"):
                data, _ = ft_db.last_task_all_status()
                data.update({"type": "end", "msg": "Mission completed"})
                ws.send(json.dumps(data))
                return
            self._proxy_transfer_status(task, ws)

    def node_proxy_transfer_status(self, get):
        ws: simple_websocket.Server = getattr(get, '_ws', None)
        if not ws:
            return public.return_message(-1, 0, "Please use WebSocket connection")
        task_id = get.get("task_id/d", 0)
        if not task_id:
            ws.send(json.dumps({"type": "error", "msg": "Task ID parameter error"}))
            return
        ft_db = FileTransferDB()
        task_data, err = ft_db.get_task(task_id)
        if err:
            ws.send(json.dumps({"type": "error", "msg": err}))
            return

        task = FileTransferTask.from_dict(task_data)
        if task.status in ("complete", "failed"):
            data, _  = ft_db.last_task_all_status()
            data["type"] = "end"
            data["msg"] = "Mission completed"
            ws.send(json.dumps(data))
            return
        self._proxy_transfer_status(task, ws)

    @staticmethod
    def _proxy_transfer_status(task: FileTransferTask, ws: simple_websocket.Server):
        def call_log(data):
            if isinstance(data, str):
                ws.send(json.dumps({"type": "end", "msg": data}))
            else:
                if data["task"]["status"] in ("complete", "failed"):
                    data["msg"] = "Mission completed"
                    data["type"] = "end"
                else:
                    data["type"] = "status"
                    data["msg"] = "Task in progress"
                ws.send(json.dumps(data))

        task_running_log(task.task_id, call_log)

    @staticmethod
    def get_transfer_status(get):
        task_id = get.get("task_id/d", 0)
        if not task_id:
            return public.return_message(-1, 0, "Task ID parameter error")

        ft_db = FileTransferDB()
        task_data, err = ft_db.get_task(task_id)
        if err:
            return public.return_message(-1, 0, err)
        task = FileTransferTask.from_dict(task_data)
        file_list = ft_db.get_task_file_transfers(task_id)
        return public.return_message(0, 0, {
            "task": task.to_dict(),
            "file_list": file_list,
        })

    @staticmethod
    def upload_check(get):
        node_id = get.get("node_id/d", -1)
        if node_id == -1:
            return public.return_message(-1, 0,"Node parameter error")
        if node_id == 0:
            node = LocalNode()
        else:
            node = ServerNode.new_by_id(node_id)

        if not node:
            return public.return_message(-1, 0,"Node does not exist")
        filename = get.get("files/s", "")
        if "\n" in filename:
            f_list = filename.split("\n")
        else:
            f_list = [filename]
        res, err = node.upload_check(f_list)
        if err:
            return public.return_message(-1, 0,err)
        if 'message' not in res and 'status' not in res:return public.return_message(0, 0,res)
        return res

    @staticmethod
    def dir_size(get):
        node_id = get.get("node_id/d", -1)
        if node_id < 0:
            return public.return_message(-1, 0,"Node parameter error")
        if node_id == 0:
            node = LocalNode()
        else:
            node = ServerNode.new_by_id(node_id)

        if not node:
            return public.return_message(-1, 0,"Node does not exist")
        path = get.get("path/s", "")
        size, err = node.dir_size(path)
        if err:
            return public.return_message(-1, 0,err)
        return public.return_message(0, 0, {
            "size": public.to_size(size),
            "size_b": size,
        })

    @staticmethod
    def create_dir(get):
        node_id = get.get("node_id/d", -1)
        if node_id < 0:
            return public.return_message(-1, 0,"Node parameter error")
        if node_id == 0:
            node = LocalNode()
        else:
            node = ServerNode.new_by_id(node_id)

        if not node:
            return public.return_message(-1, 0,"Node does not exist")

        path = get.get("path/s", "")
        res, err = node.create_dir(path)
        if err:
            return public.return_message(-1, 0,err)
        # if res["status"]:
        #     return public.return_message(0, 0,res["msg"])
        return public.return_message(0, 0,"Successfully created directory")
        # return res

    @staticmethod
    def delete_dir(get):
        node_id = get.get("node_id/d", -1)
        if node_id < 0:
            return public.return_message(-1, 0,"Node parameter error")
        if res["status"]:
            return public.return_message(0, 0,res["msg"])
        return public.return_message(-1, 0,res["msg"])

    @staticmethod
    def node_get_dir(get):
        node_id = get.get("node_id/d", -1)
        if node_id < 0:
            return public.return_message(-1, 0,"Node parameter error")
        if node_id == 0:
            node = LocalNode()
        else:
            node = ServerNode.new_by_id(node_id)

        if not node:
            return public.return_message(-1, 0,"Node does not exist")

        search = get.get("search/s", "")
        disk = get.get("disk/s", "")
        path = get.get("path/s", "")
        return node.get_dir(path, search, disk)