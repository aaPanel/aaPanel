# coding: utf-8
import base64
import hashlib
import json
import os
import re
import shutil
import sys
import threading
import time
import traceback
import tempfile
import uuid
import zipfile
from urllib.request import Request, urlopen

import public


class main():
    route_base = "/v2/mod/cloud_storage/cloud_storage"

    supported_providers = ("aws_s3", "ftp", "gcloud_storage", "gdrive")

    provider_titles = {
        "aws_s3": "S3 Storage",
        "ftp": "FTP Storage",
        "gcloud_storage": "Google Cloud Storage",
        "gdrive": "Google Drive",
    }
    # 插件最低可用版本
    provider_required_versions = {
        "ftp": "6.2",
        "aws_s3": "2.1",
        "gdrive": "3.0",
        "gcloud_storage": "1.8",
    }
    provider_main_files = {
        "aws_s3": "aws_s3_main.py",
        "ftp": "ftp_main.py",
        "gcloud_storage": "gcloud_storage_main.py",
        "gdrive": "gdrive_main.py",
    }

    # 暂时限制
    max_browser_upload_size = 1024 * 1024 * 1000
    max_browser_chunk_size = 1024 * 1024 * 64
    max_local_upload_size = 1024 * 1024 * 1000
    max_archive_source_size = 1024 * 1024 * 1000
    min_free_space_size = 1024 * 1024 * 200
    archive_disk_factor = 1.1
    # 关闭对上传文件的大小检查
    debug_skip_source_size_limit = True
    # 跳过 UploadLocal 的源大小统计和临时磁盘空间检查
    debug_skip_capacity_check = False
    # 调试打印 检查耗时
    debug_upload_local_timing = False
    background_start_delay = 0.5

    def __init__(self):
        panel_path = public.get_panel_path()
        self.data_dir = os.path.join(tempfile.gettempdir(), "aapanel_cloud_storage")
        self.task_dir = os.path.join(self.data_dir, "tasks")
        self.upload_dir = os.path.join(self.data_dir, "uploads")
        self.log_file = os.path.join(panel_path, "logs", "cloud_storage.log")
        for path in (self.data_dir, self.task_dir, self.upload_dir, os.path.dirname(self.log_file)):
            if path and not os.path.exists(path):
                os.makedirs(path)

    def GetProviders(self, get):
        """
         获取云存储插件状态
        """
        return self.get_providers(get)

    def RouteInfo(self, get):
        return self.route_info(get)

    def List(self, get):
        return self.list(get)

    def CreateFolder(self, get):
        return self.create_folder(get)

    def Delete(self, get):
        return self.delete(get)

    def UploadLocal(self, get):
        return self.upload_local(get)

    def DownloadToLocal(self, get):
        return self.download_to_local(get)

    def UploadCheck(self, get):
        return self.upload_check_api(get)

    def upload_check(self, get):
        return self.upload_check_api(get)

    def FileUpload(self, get):
        return self.file_upload_api(get)

    def file_upload(self, get):
        return self.file_upload_api(get)

    def TaskStatus(self, get):
        return self.task_status(get)

    def get_providers(self, get):
        providers = []
        for provider in self.supported_providers:
            is_installed = self.__provider_installed(provider)
            version = self.__provider_version(provider) if is_installed else ""
            required_version = self.provider_required_versions.get(provider, "")
            providers.append({
                "name": self.provider_titles.get(provider, provider),
                "value": provider,
                "install": is_installed,
                "config": is_installed and self.__provider_configured(provider),
                "version": version,
                "required_version": required_version,
                "update": is_installed and self.__provider_need_update(version, required_version),
            })
        return self.__ok({"list": providers})

    def route_info(self, get):
        actions = (
            "RouteInfo",
            "GetProviders",
            "List",
            "CreateFolder",
            "Delete",
            "UploadLocal",
            "DownloadToLocal",
            "upload_check",
            "file_upload",
            "UploadCheck",
            "FileUpload",
            "TaskStatus",
        )
        return self.__ok({
            "base": self.route_base,
            "routes": [{"action": action, "url": "{}/{}.json".format(self.route_base, action)} for action in actions],
            "alternate_suffix": "/json",
        })

    def list(self, get):
        provider = self.__provider(get)
        path = self.__cloud_path(self.__get(get, "path", "/"))
        folder_id = self.__get(get, "folder_id", "")
        try:
            raw = self.__list_provider(provider, path, folder_id)
            data = self.__normalize_list_result(provider, raw, path)
            return self.__ok(data)
        except Exception as ex:
            self.__log("list failed: provider={} path={} error={}".format(provider, path, ex))
            # return self.__fail("Failed to get cloud file list: {}".format(ex))
            return self.__fail("{}".format(ex))

    def create_folder(self, get):
        provider = self.__provider(get)
        path = self.__cloud_path(self.__get(get, "path", "/"))
        folder_name = self.__safe_name(self.__get(get, "folder_name", "") or self.__get(get, "dirname", ""))
        if not folder_name:
            return self.__fail("folder_name cannot be empty")
        try:
            result = self.__create_folder_provider(provider, path, folder_name, self.__get(get, "folder_id", ""))
            public.WriteLog("cloud_storage", f"Add new {provider} cloud directory -- {path}/{folder_name}")
            public.set_module_logs('cloud_storage', 'create_folder')
            return self.__plugin_result(result, {"provider": provider, "path": path, "folder_name": folder_name})
        except Exception as ex:
            self.__log("create_folder failed: provider={} path={} name={} error={}".format(provider, path, folder_name, ex))
            return self.__fail("Failed to create folder: {}".format(ex))

    def delete(self, get):
        provider = self.__provider(get)
        items = self.__items(get)
        path = self.__cloud_path(self.__get(get, "path", "/"))
        if not items:
            name = self.__get(get, "file_name", "") or self.__get(get, "name", "") or self.__get(get, "filename", "")
            file_path = self.__get(get, "file_path", "") or self.__get(get, "cloud_file", "")
            file_id = self.__get(get, "file_id", "")
            is_dir = self.__bool(self.__get(get, "is_dir", False))
            if name or file_path or file_id:
                items = [{
                    "path": path,
                    "file_name": name,
                    "file_path": file_path,
                    "file_id": file_id,
                    "is_dir": is_dir,
                }]
                public.WriteLog("cloud_storage", f"delete {provider} cloud directory -- {path}/{file_path}")
        if not items:
            return self.__fail("items cannot be empty")

        def runner():
            deleted = []
            for item in items:
                item_path, name, file_path, file_id, is_dir = self.__resolve_item(item, path)
                result = self.__delete_provider(provider, item_path, name, file_path, file_id, is_dir)
                self.__raise_if_plugin_failed(result)
                deleted.append({"path": file_path, "file_id": file_id})
            return {"deleted": deleted}

        public.set_module_logs('cloud_storage', 'Delete')
        return self.__maybe_background(get, "delete", runner)

    def upload_local(self, get):
        request_id = "{}_{}".format(int(time.time() * 1000), uuid.uuid4().hex[:6])
        request_start = time.time()
        provider = self.__provider(get)
        cloud_path = self.__cloud_path(self.__get(get, "cloud_path", "") or self.__get(get, "path", "/"))
        folder_id = self.__get(get, "folder_id", "")
        local_paths = self.__local_paths(get)
        mode = str(self.__get(get, "mode", "archive") or "archive").strip().lower()
        background = self.__bool(self.__get(get, "background", False))
        skip_capacity_check = self.debug_skip_capacity_check or self.__bool(self.__get(get, "skip_capacity_check", False))
        if mode not in ("recursive", "archive"):
            return self.__fail("mode must be recursive or archive")
        if not local_paths:
            return self.__fail("local_path cannot be empty")
        for local_path in local_paths:
            if not os.path.exists(local_path):
                return self.__fail("Local path does not exist: {}".format(local_path))
        # 判断上传的是单个文件  不压缩 mode改为recursive
        force_recursive = False
        if mode == "archive":
            # 仅一条路径 且是文件，强制改为递归上传，不打包压缩包
            if len(local_paths) == 1 and os.path.isfile(local_paths[0]):
                force_recursive = True
        run_mode = "recursive" if force_recursive else mode
        max_size = self.max_archive_source_size if run_mode == "archive" else self.max_local_upload_size
        self.__upload_timing_log(
            request_id,
            "sync_validate",
            request_start,
            "provider={} mode={} run_mode={} background={} skip_capacity_check={} paths={} cloud_path={}".format(
                provider,
                mode,
                run_mode,
                background,
                skip_capacity_check,
                len(local_paths),
                cloud_path,
            )
        )

        def runner(update_progress=None):
            runner_start = time.time()
            self.__upload_timing_log(request_id, "runner_start", runner_start, "provider={} run_mode={}".format(provider, run_mode))
            upload_paths = local_paths
            temp_paths = []
            try:
                total_size = 0
                need_size_scan = (run_mode == "archive" or not self.debug_skip_source_size_limit) and not skip_capacity_check
                if need_size_scan:
                    if update_progress:
                        update_progress(8, "Checking local source size")
                    stage_start = time.time()
                    size_limit = 0 if self.debug_skip_source_size_limit else max_size
                    exceeded, total_size = self.__source_size_list(local_paths, size_limit)
                    self.__upload_timing_log(
                        request_id,
                        "source_size_scan",
                        stage_start,
                        "total_size={} size_limit={}".format(total_size, size_limit)
                    )
                    if exceeded and not self.debug_skip_source_size_limit:
                        raise RuntimeError(self.__size_limit_message("Local upload", total_size, max_size))
                else:
                    self.__upload_timing_log(
                        request_id,
                        "source_size_scan_skipped",
                        runner_start,
                        "run_mode={} debug_skip_source_size_limit={} skip_capacity_check={}".format(
                            run_mode,
                            self.debug_skip_source_size_limit,
                            skip_capacity_check,
                        )
                    )

                if run_mode == "archive":
                    if skip_capacity_check:
                        self.__upload_timing_log(request_id, "disk_space_check_skipped", runner_start)
                    else:
                        if update_progress:
                            update_progress(12, "Checking temporary disk space")
                        stage_start = time.time()
                        disk_error = self.__ensure_disk_space(
                            self.upload_dir,
                            int(total_size * self.archive_disk_factor),
                            "archive upload"
                        )
                        self.__upload_timing_log(
                            request_id,
                            "disk_space_check",
                            stage_start,
                            "required_size={}".format(int(total_size * self.archive_disk_factor))
                        )
                        if disk_error:
                            raise RuntimeError(disk_error)
                    if update_progress:
                        update_progress(15, "Creating archive")
                    stage_start = time.time()
                    archive_file = self.__make_archive(local_paths, skip_source_check=True)
                    self.__upload_timing_log(
                        request_id,
                        "make_archive",
                        stage_start,
                        "archive_file={} archive_size={}".format(archive_file, self.__safe_getsize(archive_file))
                    )
                    upload_paths = [archive_file]
                    temp_paths.append(archive_file)
                    if update_progress:
                        update_progress(35, "Archive created")
                uploaded = []
                total_paths = len(upload_paths) or 1
                upload_start = 35 if run_mode == "archive" else 10
                upload_span = 55 if run_mode == "archive" else 80
                for index, local_path in enumerate(upload_paths):
                    if update_progress:
                        progress = upload_start + int((index / float(total_paths)) * upload_span)
                        update_progress(progress, "Uploading {}".format(os.path.basename(local_path.rstrip("/\\"))))
                    stage_start = time.time()
                    result = self.__upload_provider(provider, local_path, cloud_path, folder_id)
                    self.__upload_timing_log(
                        request_id,
                        "upload_provider",
                        stage_start,
                        "provider={} local_path={} local_size={}".format(provider, local_path, self.__safe_getsize(local_path))
                    )
                    self.__raise_if_plugin_failed(result)
                    uploaded.append({
                        "local_path": local_path,
                        "cloud_path": self.__join_cloud(cloud_path, os.path.basename(local_path.rstrip("/\\"))),
                        "result": result,
                    })
                if update_progress:
                    update_progress(92, "Finishing upload")
                total_msg  = "upload successfully!"
                if len(uploaded)==1:
                    plugin_ret = uploaded[0]["result"]
                    total_msg = plugin_ret.get("msg", "Abnormal") if isinstance(plugin_ret, dict) else "Abnormal"
                    # 删除本条内冗余result字段
                    del uploaded[0]["result"]

                self.__upload_timing_log(request_id, "runner_done", runner_start)
                return {"uploaded": uploaded, "mode": run_mode, "result": total_msg }
            finally:
                cleanup_start = time.time()
                if update_progress and temp_paths:
                    update_progress(95, "Cleaning temporary files")
                for temp_path in temp_paths:
                    try:
                        if os.path.exists(temp_path):
                            os.remove(temp_path)
                    except:
                        pass
                self.__upload_timing_log(request_id, "cleanup", cleanup_start, "temp_paths={}".format(len(temp_paths)))

        stage_start = time.time()
        result = self.__maybe_background(get, "upload_local", runner)
        self.__upload_timing_log(request_id, "return_response", stage_start, "total_sync_ms={}".format(self.__elapsed_ms(request_start)))

        public.WriteLog("cloud_storage", f"Upload local {local_paths} to {provider} cloud directory {cloud_path}")
        public.set_module_logs('cloud_storage', 'UploadLocal')
        return result

    def download_to_local(self, get):
        provider = self.__provider(get)
        items = self.__items(get)
        local_path = str(self.__get(get, "local_path", "") or self.__get(get, "destination_path", "") or "").strip()
        cloud_path = self.__cloud_path(self.__get(get, "path", "/"))
        if not local_path:
            return self.__fail("local_path cannot be empty")
        if not items:
            name = self.__get(get, "file_name", "") or self.__get(get, "name", "") or self.__get(get, "filename", "")
            file_id = self.__get(get, "file_id", "")
            file_path = self.__get(get, "file_path", "") or self.__get(get, "cloud_file", "")
            is_dir = self.__bool(self.__get(get, "is_dir", False))
            if name or file_path or file_id:
                items = [{
                    "path": cloud_path,
                    "file_name": name,
                    "file_id": file_id,
                    "file_path": file_path,
                    "is_dir": is_dir,
                }]
        if not items:
            return self.__fail("items cannot be empty")

        def runner(update_progress=None):
            if not os.path.exists(local_path):
                os.makedirs(local_path)
            downloaded = []
            total_items = len(items) or 1
            for index, item in enumerate(items):
                if update_progress:
                    progress = 10 + int((index / float(total_items)) * 80)
                    update_progress(progress, "Downloading {}".format(item.get("file_name") or item.get("name") or item.get("file_path") or "item"))
                downloaded.extend(self.__download_item(provider, item, cloud_path, local_path))
            if update_progress:
                update_progress(92, "Finishing download")
            return {"downloaded": downloaded}

        public.WriteLog("cloud_storage", f"Download {provider} cloud directory {cloud_path} to local {local_path}")
        public.set_module_logs('cloud_storage', 'DownloadToLocal')
        return self.__maybe_background(get, "download_to_local", runner)

    def upload_check_api(self, get):
        provider = self.__provider(get)
        file_name = self.__safe_name(
            self.__request_get(get, "f_name", "") or self.__request_get(get, "file_name", "")
        )
        if not file_name:
            return self.__fail("f_name cannot be empty")
        raw_f_size = self.__request_get(get, "f_size", self.__request_get(get, "total_size", ""))
        if raw_f_size == "":
            return self.__fail("f_size cannot be empty")
        f_size = self.__int(raw_f_size, -1)
        if f_size < 0:
            return self.__fail("f_size is invalid")
        limit_error = self.__validate_browser_upload_size(f_size)
        if limit_error:
            return self.__fail(limit_error)
        cloud_path = self.__cloud_path(
            self.__request_get(get, "f_path", "") or self.__request_get(get, "cloud_path", "") or self.__request_get(get, "path", "/")
        )
        folder_id = self.__request_get(get, "folder_id", "")
        upload_id = self.__safe_upload_id(self.__request_get(get, "upload_id", ""))
        if not upload_id:
            upload_id = self.__make_upload_id(provider, cloud_path, file_name, f_size, folder_id)

        upload_path = os.path.join(self.upload_dir, upload_id)
        if not os.path.exists(upload_path):
            os.makedirs(upload_path)
        disk_error = self.__ensure_disk_space(upload_path, max(0, f_size - self.__safe_getsize(os.path.join(upload_path, file_name))), "browser upload")
        if disk_error:
            return self.__fail(disk_error)
        local_file = os.path.join(upload_path, file_name)
        uploaded_size = os.path.getsize(local_file) if os.path.exists(local_file) else 0
        if uploaded_size > f_size:
            try:
                os.remove(local_file)
            except:
                pass
            uploaded_size = 0

        meta = {
            "upload_id": upload_id,
            "provider": provider,
            "file_name": file_name,
            "f_name": file_name,
            "cloud_path": cloud_path,
            "f_path": cloud_path,
            "folder_id": folder_id,
            "f_size": f_size,
            "total_size": f_size,
            "f_start": uploaded_size,
            "created_at": int(time.time()),
            "updated_at": int(time.time()),
        }
        old_meta = self.__read_json(os.path.join(upload_path, "meta.json"), {})
        if old_meta.get("created_at"):
            meta["created_at"] = old_meta.get("created_at")
        self.__write_json(os.path.join(upload_path, "meta.json"), meta)
        return self.__ok({
            "upload_id": upload_id,
            "provider": provider,
            "f_name": file_name,
            "file_name": file_name,
            "f_path": cloud_path,
            "cloud_path": cloud_path,
            "folder_id": folder_id,
            "f_size": f_size,
            "f_start": uploaded_size,
            "uploaded_size": uploaded_size,
        })

    def file_upload_api(self, get):
        upload_id = self.__safe_upload_id(self.__request_get(get, "upload_id", ""))
        file_name = self.__safe_name(
            self.__request_get(get, "f_name", "") or self.__request_get(get, "file_name", "")
        )
        raw_f_size = self.__request_get(get, "f_size", self.__request_get(get, "total_size", ""))
        f_size = self.__int(raw_f_size, -1) if raw_f_size != "" else -1
        f_start = self.__int(self.__request_get(get, "f_start", 0), -1)
        if f_start < 0:
            return self.__fail("f_start is invalid")

        meta = {}
        upload_path = ""
        if upload_id:
            upload_path = os.path.join(self.upload_dir, upload_id)
            meta = self.__read_json(os.path.join(upload_path, "meta.json"), {})
            if meta:
                file_name = file_name or self.__safe_name(meta.get("file_name", ""))
                if f_size < 0:
                    f_size = self.__int(meta.get("f_size", 0), 0)

        if f_size < 0:
            return self.__fail("f_size cannot be empty")
        limit_error = self.__validate_browser_upload_size(f_size)
        if limit_error:
            return self.__fail(limit_error)

        provider = str(
            self.__request_get(get, "provider", "")
            or meta.get("provider", "")
            or self.__request_get(get, "type", "")
        ).strip()
        if provider not in self.supported_providers:
            return self.__fail("Unsupported cloud provider: {}".format(provider))
        if not file_name:
            return self.__fail("f_name cannot be empty")

        cloud_path = self.__cloud_path(
            self.__request_get(get, "f_path", "")
            or self.__request_get(get, "cloud_path", "")
            or self.__request_get(get, "path", "")
            or meta.get("cloud_path", "/")
        )
        folder_id = self.__request_get(get, "folder_id", "") or meta.get("folder_id", "")
        if not upload_id:
            upload_id = self.__make_upload_id(provider, cloud_path, file_name, f_size, folder_id)
            upload_path = os.path.join(self.upload_dir, upload_id)
        if not os.path.exists(upload_path):
            os.makedirs(upload_path)

        local_file = os.path.join(upload_path, file_name)
        current_size = os.path.getsize(local_file) if os.path.exists(local_file) else 0
        if f_size and current_size > f_size:
            try:
                os.remove(local_file)
            except:
                pass
            current_size = 0

        chunk_data = self.__read_chunk_data(get)
        if chunk_data is None:
            return self.__fail("blob cannot be empty")
        if f_size > 0 and len(chunk_data) == 0:
            return self.__fail("blob cannot be empty")
        limit_error = self.__validate_browser_chunk_size(len(chunk_data))
        if limit_error:
            return self.__fail(limit_error)
        required_size = len(chunk_data) if f_start < current_size else max(len(chunk_data), f_size - current_size)
        disk_error = self.__ensure_disk_space(upload_path, required_size, "browser upload")
        if disk_error:
            return self.__fail(disk_error)

        if f_start < current_size:
            next_start = current_size
        elif f_start > current_size:
            return self.__fail("f_start exceeds uploaded size, current f_start: {}".format(current_size))
        else:
            next_start = f_start + len(chunk_data)
            if f_size and next_start > f_size:
                return self.__fail("blob exceeds f_size")
            with open(local_file, "r+b" if os.path.exists(local_file) else "wb") as fp:
                fp.seek(f_start)
                fp.write(chunk_data)
                fp.truncate(next_start)

        meta = {
            "upload_id": upload_id,
            "provider": provider,
            "file_name": file_name,
            "f_name": file_name,
            "cloud_path": cloud_path,
            "f_path": cloud_path,
            "folder_id": folder_id,
            "f_size": f_size,
            "total_size": f_size,
            "f_start": next_start,
            "updated_at": int(time.time()),
        }
        self.__write_json(os.path.join(upload_path, "meta.json"), meta)

        if f_size and next_start < f_size:
            return self.__ok({
                "upload_id": upload_id,
                "f_start": next_start,
                "next_start": next_start,
                "f_size": f_size,
                "complete": False,
            })

        final_size = os.path.getsize(local_file)
        if f_size and final_size != f_size:
            return self.__fail("uploaded file size mismatch, current f_start: {}, f_size: {}".format(final_size, f_size))

        def runner():
            try:
                result = self.__upload_provider(provider, local_file, cloud_path, folder_id)
                self.__raise_if_plugin_failed(result)
                return {
                    "upload_id": upload_id,
                    "f_name": file_name,
                    "file_name": file_name,
                    "f_path": cloud_path,
                    "cloud_path": self.__join_cloud(cloud_path, file_name),
                    "size": final_size,
                    "complete": True,
                    "uploaded": [{
                        "local_path": local_file,
                        "cloud_path": self.__join_cloud(cloud_path, file_name),
                        "result": result,
                    }]
                }
            finally:
                shutil.rmtree(upload_path, ignore_errors=True)

        return self.__maybe_background(get, "file_upload", runner)

    def task_status(self, get):
        task_file = self.__task_file()
        if not os.path.exists(task_file):
            return self.__ok({
                "status": 1,
                "error": "",
                "cloud_storage_task": {
                    "status": 1,
                    "ps": "No task",
                    "title": "Cloud Storage Task",
                    "action": "",
                    "progress": 100,
                    "result": None,
                    "result_list": [],
                    "error": "",
                    "alive": False,
                    "stale": False,
                }
            })
        task = self.__read_json(task_file, {})
        task = self.__normalize_task(task)
        alive = self.__task_alive()
        is_starting = int(time.time()) - self.__int(task.get("created_at", 0), 0) <= 5
        if self.__int(task.get("status", 0), 0) == 0 and not alive and not is_starting:
            task["status"] = -1
            task["error"] = task.get("error") or "Task thread is not alive"
            self.__task_step(task)["status"] = -1
            self.__task_step(task)["ps"] = "Task interrupted"
            self.__task_step(task)["error"] = task["error"]
            task["updated_at"] = int(time.time())
            self.__write_task(task)
        self.__task_step(task)["alive"] = alive
        self.__task_step(task)["stale"] = self.__int(task.get("status", 0), 0) == 0 and not alive and not is_starting
        return self.__ok(self.__normalize_task(task))

    def __provider(self, get):
        provider = str(self.__request_get(get, "provider", "") or self.__request_get(get, "type", "") or "").strip()
        if provider not in self.supported_providers:
            raise ValueError("Unsupported cloud provider: {}".format(provider))
        return provider

    def __get(self, data, key, default=""):
        if data is None:
            return default
        if isinstance(data, dict):
            return data.get(key, default)
        try:
            return data.get(key, default)
        except:
            return getattr(data, key, default)

    def __request_get(self, data, key, default=""):
        value = self.__get(data, key, None)
        if value not in (None, ""):
            return value
        try:
            from flask import request
            value = request.form.get(key, None)
            if value not in (None, ""):
                return value
            value = request.args.get(key, None)
            if value not in (None, ""):
                return value
        except:
            pass
        return default

    def __bool(self, value):
        if isinstance(value, bool):
            return value
        return str(value).strip().lower() in ("1", "true", "yes", "on")

    def __int(self, value, default=0):
        try:
            return int(value)
        except:
            return default

    # def __ok(self, data=None, msg="success"):
    #     return {"status": True, "msg": msg, "data": data if data is not None else {}}

    def __ok(self, data):
        return public.return_message(0, 0, data)

    # def __fail(self, msg, data=None):
    #     return {"status": False, "msg": str(msg), "data": data if data is not None else {}}

    def __fail(self, message):
        return public.return_message(-1, 0, message)

    def __to_obj(self, data):
        return public.to_dict_obj(data)

    def __plugin_result(self, result, data=None):
        if result is False:
            return self.__fail("plugin operation failed")
        if isinstance(result, dict) and result.get("status") is False:
            return self.__fail(result.get("msg", "operation failed"))
        body = data or {}
        # body["raw"] = result
        body["result"] = "Created successfully!"
        return self.__ok(body)

    def __raise_if_plugin_failed(self, result):
        if result is False:
            raise RuntimeError("plugin operation failed")
        if isinstance(result, dict) and result.get("status") is False:
            raise RuntimeError(result.get("msg", "plugin operation failed"))

    def __run_plugin(self, provider, method, payload):
        return public.run_plugin(provider, method, self.__to_obj(payload))

    def __cloud_path(self, path):
        path = str(path or "/").strip().replace("\\", "/")
        if not path:
            path = "/"
        while "//" in path:
            path = path.replace("//", "/")
        if not path.startswith("/"):
            path = "/" + path
        return path

    def __cloud_key(self, path):
        path = self.__cloud_path(path)
        return path[1:] if path.startswith("/") else path

    def __join_cloud(self, path, name):
        name = str(name or "").replace("\\", "/").lstrip("/")
        path = self.__cloud_path(path)
        if path == "/":
            return "/" + name if name else "/"
        return path.rstrip("/") + "/" + name if name else path

    def __parent_path(self, file_path):
        file_path = self.__cloud_path(file_path)
        parent = os.path.dirname(file_path.rstrip("/")).replace("\\", "/")
        if not parent:
            parent = "/"
        if not parent.endswith("/"):
            parent += "/"
        return parent

    def __safe_name(self, name):
        name = os.path.basename(str(name or "").replace("\\", "/").rstrip("/"))
        return name.strip()

    def __safe_upload_id(self, upload_id):
        upload_id = str(upload_id or "").strip()
        return "".join([x for x in upload_id if x.isalnum() or x in ("_", "-")])

    def __make_upload_id(self, provider, cloud_path, file_name, f_size, folder_id=""):
        raw = "{}|{}|{}|{}|{}".format(provider, self.__cloud_path(cloud_path), file_name, f_size, folder_id)
        return hashlib.md5(raw.encode("utf-8")).hexdigest()

    def __validate_browser_upload_size(self, size):
        if self.max_browser_upload_size and size > self.max_browser_upload_size:
            return "File size {} exceeds limit {}".format(self.__format_size(size), self.__format_size(self.max_browser_upload_size))
        return ""

    def __validate_browser_chunk_size(self, size):
        if self.max_browser_chunk_size and size > self.max_browser_chunk_size:
            return "Chunk size {} exceeds limit {}".format(self.__format_size(size), self.__format_size(self.max_browser_chunk_size))
        return ""

    def __ensure_disk_space(self, path, required_size, action):
        required_size = max(0, int(required_size or 0))
        if required_size <= 0:
            return ""
        check_path = self.__existing_path(path)
        try:
            usage = shutil.disk_usage(check_path)
        except Exception as ex:
            return "Failed to check disk space for {}: {}".format(action, ex)
        need_size = required_size + self.min_free_space_size
        if usage.free < need_size:
            return "Insufficient disk space for {}: need {} plus {} reserve, available {}".format(
                action,
                self.__format_size(required_size),
                self.__format_size(self.min_free_space_size),
                self.__format_size(usage.free)
            )
        return ""

    def __existing_path(self, path):
        path = os.path.abspath(path or self.upload_dir)
        while path and not os.path.exists(path):
            parent = os.path.dirname(path)
            if parent == path:
                break
            path = parent
        return path if path and os.path.exists(path) else tempfile.gettempdir()

    def __safe_getsize(self, path):
        try:
            return os.path.getsize(path) if os.path.exists(path) else 0
        except:
            return 0

    def __source_size_list(self, paths, max_size=0):
        total_size = 0
        for path in paths:
            exceeded, total_size = self.__source_size(path, max_size, total_size)
            if exceeded:
                return True, total_size
        return False, total_size

    def __source_size(self, path, max_size=0, total_size=0):
        if not os.path.exists(path) or os.path.islink(path):
            return False, total_size
        if os.path.isfile(path):
            try:
                total_size += os.path.getsize(path)
            except:
                pass
            return bool(max_size and total_size > max_size), total_size

        for root, dirs, files in os.walk(path, topdown=True):
            dirs[:] = [d for d in dirs if not os.path.islink(os.path.join(root, d))]
            for filename in files:
                file_path = os.path.join(root, filename)
                if not os.path.exists(file_path) or os.path.islink(file_path):
                    continue
                try:
                    total_size += os.path.getsize(file_path)
                except:
                    pass
                if max_size and total_size > max_size:
                    return True, total_size
        return False, total_size

    def __size_limit_message(self, action, total_size, max_size):
        return "{} exceeds limit: size {}/{}".format(
            action,
            self.__format_size(total_size),
            self.__format_size(max_size)
        )

    def __format_size(self, size):
        try:
            return public.to_size(size)
        except:
            pass
        size = float(size or 0)
        units = ("B", "KB", "MB", "GB", "TB")
        index = 0
        while size >= 1024 and index < len(units) - 1:
            size /= 1024
            index += 1
        return "{:.2f} {}".format(size, units[index])

    def __items(self, get):
        items = self.__get(get, "items", [])
        if isinstance(items, str):
            if not items.strip():
                return []
            items = self.__loads(items, [])
        if isinstance(items, dict):
            items = [items]
        return items if isinstance(items, list) else []

    def __local_paths(self, get):
        local_paths = self.__get(get, "local_paths", [])
        if isinstance(local_paths, str):
            if local_paths.strip().startswith("[") or local_paths.strip().startswith("("):
                local_paths = self.__loads(local_paths, [])
            elif local_paths.strip():
                local_paths = [local_paths.strip()]
            else:
                local_paths = []
        local_path = self.__get(get, "local_path", "") or self.__get(get, "file_path", "")
        if local_path:
            local_paths.append(str(local_path))
        return [str(x).strip() for x in local_paths if str(x).strip()]

    def __item_is_dir(self, item):
        if "is_dir" in item:
            return self.__bool(item.get("is_dir"))
        item_type = str(item.get("type", "")).lower()
        return item_type in ("d", "dir", "directory", "folder")

    def __loads(self, value, default):
        if not isinstance(value, str):
            return value
        try:
            return json.loads(value)
        except:
            try:
                import ast
                return ast.literal_eval(value)
            except:
                return default

    def __resolve_item(self, item, default_path="/"):
        name = item.get("file_name") or item.get("name") or item.get("filename") or ""
        file_id = item.get("file_id") or item.get("id") or ""
        is_dir = self.__item_is_dir(item)
        explicit_file_path = item.get("file_path") or item.get("cloud_file") or ""
        raw_path = item.get("path", "")
        parent_path = self.__cloud_path(default_path)
        file_path = ""

        if explicit_file_path:
            file_path = self.__cloud_path(explicit_file_path)
        elif raw_path:
            raw_path = self.__cloud_path(raw_path)
            if name and self.__safe_name(raw_path) == self.__safe_name(name):
                file_path = raw_path
            elif is_dir:
                file_path = raw_path
            else:
                parent_path = raw_path

        if not file_path:
            file_path = self.__join_cloud(parent_path, name)
        if is_dir and not file_path.endswith("/"):
            file_path += "/"
        if file_path:
            parent_path = self.__parent_path(file_path)
        if not name:
            name = self.__safe_name(file_path)
        return parent_path, name, file_path, file_id, is_dir

    def __provider_installed(self, provider):
        plugin_dir = os.path.join(public.get_panel_path(), "plugin", provider)
        main_file = self.provider_main_files.get(provider, "{}_main.py".format(provider))
        return os.path.exists(os.path.join(plugin_dir, main_file))

    def __provider_version(self, provider):
        info_file = os.path.join(public.get_panel_path(), "plugin", provider, "info.json")
        info = self.__read_json(info_file, {})
        version = ""
        if isinstance(info, dict):
            version = info.get("versions", "") or info.get("version", "")
        return str(version or "").strip()

    def __provider_need_update(self, version, required_version):
        if not required_version:
            return False
        if not version:
            return True
        return self.__version_tuple(version) < self.__version_tuple(required_version)

    def __version_tuple(self, version):
        result = []
        for item in str(version or "").strip().split("."):
            if item == "":
                result.append(0)
                continue
            match = re.match(r"^(\d+)", item)
            result.append(int(match.group(1)) if match else 0)
        while len(result) < 3:
            result.append(0)
        return tuple(result[:3])

    def __provider_configured(self, provider):
        plugin_dir = os.path.join(public.get_panel_path(), "plugin", provider)
        if provider == "gcloud_storage":
            return self.__has_body(os.path.join(plugin_dir, "google.json")) and self.__has_body(os.path.join(plugin_dir, "bucket_name.conf"))
        if provider == "ftp":
            #  'config.conf', 'ftp.config.conf', 'sftp.config.conf'
            for filename in ("config.conf", "ftp.config.conf", "sftp.config.conf"):
                if self.__has_body(os.path.join(plugin_dir, filename)):
                    return True
            return False
        return self.__has_body(os.path.join(plugin_dir, "config.conf")) or self.__has_body(os.path.join(plugin_dir, "google.json"))

    def __has_body(self, filename):
        if not os.path.exists(filename):
            return False
        try:
            body = public.readFile(filename)
            return isinstance(body, str) and bool(body.strip())
        except:
            return False

    def __list_provider(self, provider, path, folder_id=""):
        if provider == "aws_s3":
            return self.__run_plugin(provider, "new_get_list", {"path": path})
        if provider == "ftp":
            return self.__run_plugin(provider, "get_list", {"path": path})
        if provider == "gcloud_storage":
            return self.__run_plugin(provider, "list_blobs_with_prefix", {"path": path})
        if provider == "gdrive":
            payload = {"path": path}
            if folder_id:
                payload["folder_id"] = folder_id
            return self.__run_plugin(provider, "list_drive_files", payload)
        raise ValueError("Unsupported cloud provider")

    def __normalize_list_result(self, provider, raw, path):
        if isinstance(raw, dict) and raw.get("status") is False:
            raise RuntimeError(raw.get("msg", "plugin list failed"))
        raw_path = raw.get("path", path) if isinstance(raw, dict) else path
        rows = raw.get("list", []) if isinstance(raw, dict) else []
        result = {
            "provider": provider,
            "path": self.__cloud_path(raw_path),
            "folder_id": raw.get("folder_id", "") if isinstance(raw, dict) else "",
            "list": [],
            # "raw": raw,
        }
        for row in rows:
            if not isinstance(row, dict):
                continue
            name = row.get("name", "")
            item_type = row.get("type", "")
            is_dir = str(item_type).lower() in ("d", "dir", "directory", "folder") or item_type is None
            clean_name = str(name or "").rstrip("/") if is_dir else str(name or "")
            item_path = self.__join_cloud(result["path"], clean_name)
            if is_dir and not item_path.endswith("/"):
                item_path += "/"
            result["list"].append({
                "id": row.get("id", row.get("file_id", "")),
                "name": clean_name,
                "path": item_path,
                "is_dir": is_dir,
                "type": "Dir" if is_dir else "File",
                "size": self.__int(row.get("size", 0), 0) if not is_dir else 0,
                "time": row.get("time", 0),
                "download": row.get("download", ""),
                "mimeType": row.get("mimeType", ""),
                # "raw": row,
            })
        return result

    def __create_folder_provider(self, provider, path, folder_name, folder_id=""):
        if provider == "aws_s3":
            return self.__run_plugin(provider, "create_dir", {"path": self.__cloud_key(self.__join_cloud(path, folder_name))})
        if provider == "ftp":
            return self.__run_plugin(provider, "create_dir", {"path": path.rstrip("/"), "dirname": folder_name})
        if provider == "gcloud_storage":
            return self.__run_plugin(provider, "create_directory", {"path": self.__join_cloud(path, folder_name)})
        if provider == "gdrive":
            payload = {"path": path, "folder_name": folder_name}
            if folder_id:
                payload["folder_id"] = folder_id
            return self.__run_plugin(provider, "create_drive_folder", payload)
        raise ValueError("Unsupported cloud provider")

    def __delete_provider(self, provider, path, name, file_path, file_id="", is_dir=False):
        file_path = self.__cloud_path(file_path or self.__join_cloud(path, name))
        if is_dir and not file_path.endswith("/"):
            file_path += "/"
        if provider == "aws_s3":
            return self.__run_plugin(provider, "delete_file", {"file_path": self.__cloud_key(file_path)})
        if provider == "ftp":
            if is_dir:
                return self.__run_plugin(provider, "delete_dir", {"path": path, "dir_name": name or self.__safe_name(file_path)})
            return self.__run_plugin(provider, "delete_file", {"path": path, "filename": name or self.__safe_name(file_path)})
        if provider == "gcloud_storage":
            return self.__run_plugin(provider, "delete_blob", {"filename": self.__cloud_key(file_path)})
        if provider == "gdrive":
            return self.__run_plugin(provider, "delete_drive_file", {
                "path": path,
                "file_name": name or self.__safe_name(file_path),
                "file_id": file_id,
            })
        raise ValueError("Unsupported cloud provider")

    def __upload_provider(self, provider, local_path, cloud_path, folder_id=""):
        if provider == "aws_s3":
            if os.path.isdir(local_path):
                self.__create_object_placeholders(provider, local_path, cloud_path)
            return self.__run_plugin(provider, "upload_file", {
                "file_path": local_path,
                "dir_name": self.__object_prefix(cloud_path),
            })
        if provider == "gcloud_storage":
            if os.path.isdir(local_path):
                self.__create_object_placeholders(provider, local_path, cloud_path)
                uploaded = []
                root_name = os.path.basename(local_path.rstrip("/\\"))
                for root, dirs, files in os.walk(local_path):
                    rel = os.path.relpath(root, local_path)
                    remote_dir = root_name if rel == "." else root_name + "/" + rel.replace("\\", "/")
                    for filename in files:
                        src = os.path.join(root, filename)
                        result = self.__run_plugin(provider, "upload_file", {
                            "filename": src,
                            "path": self.__object_prefix(self.__join_cloud(cloud_path, remote_dir)),
                        })
                        self.__raise_if_plugin_failed(result)
                        uploaded.append(src)
                return public.returnMsg(True, "upload successfully: {} file(s)".format(len(uploaded)))
            return self.__run_plugin(provider, "upload_file", {
                "filename": local_path,
                "path": self.__object_prefix(cloud_path),
            })
        if provider == "gdrive":
            payload = {"file_path": local_path, "path": cloud_path}
            if folder_id:
                payload["folder_id"] = folder_id
            return self.__run_plugin(provider, "upload_drive_file", payload)
        if provider == "ftp":
            client = self.__ftp_client()
            target_dir = self.__cloud_path(cloud_path)
            if os.path.isdir(local_path):
                root_name = os.path.basename(local_path.rstrip("/\\"))
                for root, dirs, files in os.walk(local_path):
                    rel = os.path.relpath(root, local_path)
                    remote_dir = self.__join_cloud(target_dir, root_name if rel == "." else root_name + "/" + rel.replace("\\", "/"))
                    client.create_dir(remote_dir)
                    for filename in files:
                        src = os.path.join(root, filename)
                        if not client.resumable_upload(src, self.__join_cloud(remote_dir, filename).lstrip("/")):
                            raise RuntimeError(self.__ftp_upload_error(client))
                return public.returnMsg(True, "upload successfully")
            object_name = self.__join_cloud(target_dir, os.path.basename(local_path)).lstrip("/")
            if not client.resumable_upload(local_path, object_name):
                raise RuntimeError(self.__ftp_upload_error(client))
            return True
        raise ValueError("Unsupported cloud provider")

    def __ftp_upload_error(self, client):
        error = str(getattr(client, "last_error", "") or "").strip()
        return "FTP upload failed: {}".format(error or "plugin operation failed")

    def __create_object_placeholders(self, provider, local_path, cloud_path):
        root_name = os.path.basename(local_path.rstrip("/\\"))
        targets = [self.__join_cloud(cloud_path, root_name)]
        for root, dirs, files in os.walk(local_path):
            rel = os.path.relpath(root, local_path)
            for dirname in dirs:
                remote_dir = root_name + "/" + dirname if rel == "." else root_name + "/" + rel.replace("\\", "/") + "/" + dirname
                targets.append(self.__join_cloud(cloud_path, remote_dir))
        for target in targets:
            if provider == "aws_s3":
                result = self.__run_plugin(provider, "create_dir", {"path": self.__cloud_key(target)})
            elif provider == "gcloud_storage":
                result = self.__run_plugin(provider, "create_directory", {"path": target})
            else:
                result = True
            self.__raise_if_plugin_failed(result)

    def __download_item(self, provider, item, default_cloud_path, local_path):
        _, name, item_path, file_id, is_dir = self.__resolve_item(item, default_cloud_path)
        if is_dir:
            target_dir = os.path.join(local_path, self.__safe_name(name or item_path))
            if not os.path.exists(target_dir):
                os.makedirs(target_dir)
            listed = self.__normalize_list_result(provider, self.__list_provider(provider, item_path, file_id), item_path)
            downloaded = []
            for child in listed["list"]:
                child_item = {
                    "path": child["path"],
                    "name": child["name"],
                    "file_id": child.get("id", ""),
                    "is_dir": child["is_dir"],
                    "size": child.get("size", 0),
                }
                downloaded.extend(self.__download_item(provider, child_item, item_path, target_dir))
            return downloaded
        destination = os.path.join(local_path, name)
        if not os.path.exists(os.path.dirname(destination)):
            os.makedirs(os.path.dirname(destination))
        self.__download_file_provider(provider, item_path, name, file_id, destination)
        return [{"cloud_path": item_path, "local_path": destination}]

    def __download_file_provider(self, provider, file_path, name, file_id, destination):
        if provider == "aws_s3":
            result = self.__run_plugin(provider, "new_download_file", {"file_path": self.__cloud_key(file_path)})
            self.__raise_if_plugin_failed(result)
            url = result.get("msg") if isinstance(result, dict) else ""
            if not url:
                raise RuntimeError("S3 Storage did not return a download URL")
            return self.__download_url(url, destination)
        if provider == "gcloud_storage":
            result = self.__run_plugin(provider, "download_blob", {
                "source_blob_name": self.__cloud_key(file_path),
                "destination_file_name": destination,
            })
            self.__raise_if_plugin_failed(result)
            return destination
        if provider == "gdrive":
            result = self.__run_plugin(provider, "download_drive_file", {
                "path": self.__parent_path(file_path),
                "file_name": name,
                "file_id": file_id,
                "destination_file_name": destination,
            })
            self.__raise_if_plugin_failed(result)
            return destination
        if provider == "ftp":
            client = self.__ftp_client()
            remote = self.__cloud_key(file_path)
            if not remote.startswith("/"):
                remote = "/" + remote
            if not client.download_to_local(remote, destination):
                raise RuntimeError("FTP download failed")
            return destination
        raise ValueError("Unsupported cloud provider")

    def __download_url(self, url, destination):
        request = Request(url, headers={"User-Agent": "aaPanel cloud storage"})
        with urlopen(request, timeout=60) as response:
            with open(destination, "wb") as fp:
                shutil.copyfileobj(response, fp, length=1024 * 1024)
        return destination

    def __object_prefix(self, path):
        key = self.__cloud_key(path).strip("/")
        return key + "/" if key else ""

    def __ftp_client(self):
        plugin_path = os.path.join(public.get_panel_path(), "plugin", "ftp")
        if plugin_path not in sys.path:
            sys.path.insert(0, plugin_path)
        from ftp_main import get_client
        client = get_client(use_sftp=None)
        if not client:
            raise RuntimeError("FTP client init failed")
        return client

    def __make_archive(self, local_paths, skip_source_check=False):
        if not skip_source_check:
            exceeded, total_size = self.__source_size_list(
                local_paths,
                0 if self.debug_skip_source_size_limit else self.max_archive_source_size
            )
            if exceeded and not self.debug_skip_source_size_limit:
                raise RuntimeError(self.__size_limit_message("Archive source", total_size, self.max_archive_source_size))
        archive_id = "{}_{}".format(self.__archive_source_name(local_paths), uuid.uuid4().hex[:10])
        archive_file = os.path.join(self.upload_dir, archive_id + ".zip")
        with zipfile.ZipFile(archive_file, "w", zipfile.ZIP_DEFLATED) as zip_fp:
            for local_path in local_paths:
                local_path = local_path.rstrip("/\\")
                if os.path.islink(local_path):
                    continue
                base_name = os.path.basename(local_path)
                if os.path.isfile(local_path):
                    zip_fp.write(local_path, base_name)
                    continue
                for root, dirs, files in os.walk(local_path):
                    dirs[:] = [d for d in dirs if not os.path.islink(os.path.join(root, d))]
                    rel_root = os.path.relpath(root, local_path)
                    for dirname in dirs:
                        dir_rel = os.path.join(base_name, dirname if rel_root == "." else os.path.join(rel_root, dirname))
                        zip_fp.writestr(dir_rel.replace("\\", "/").rstrip("/") + "/", "")
                    for filename in files:
                        source = os.path.join(root, filename)
                        if os.path.islink(source):
                            continue
                        rel = os.path.relpath(source, local_path)
                        zip_fp.write(source, os.path.join(base_name, rel).replace("\\", "/"))
        return archive_file

    def __archive_source_name(self, local_paths):
        names = []
        for local_path in local_paths[:3]:
            name = os.path.basename(str(local_path).rstrip("/\\"))
            if name:
                names.append(self.__safe_archive_name(name))
        if not names:
            return "files"
        if len(local_paths) > 3:
            names.append("more")
        return "_".join([x for x in names if x])[:80] or "files"

    def __safe_archive_name(self, name):
        safe = []
        for char in str(name):
            if char.isalnum() or char in ("-", "_", "."):
                safe.append(char)
            elif char in (" ",):
                safe.append("_")
        name = "".join(safe).strip("._-")
        return name[:40] or "item"

    def __maybe_background(self, get, action, runner):
        running_task = self.__current_running_task()
        if running_task:
            running_step = self.__task_step(running_task)
            return self.__fail("A cloud storage task is running: {} {}% {}".format(
                running_step.get("action", ""),
                running_step.get("progress", 0),
                running_step.get("ps", "")
            ))
        task = {
            "status": 0,
            "error": "",
            "created_at": int(time.time()),
            "updated_at": int(time.time()),
            "cloud_storage_task": {
                "status": 0,
                "ps": "Task queued",
                "title": "Cloud Storage Task",
                "action": action,
                "progress": 0,
                "result": None,
                "result_list": [],
                "error": "",
                "alive": False,
                "stale": False,
            }
        }
        self.__write_task(task)

        def update_progress(progress=None, ps=None, status=None, result=None, error=None):
            step = self.__task_step(task)
            if progress is not None:
                step["progress"] = max(0, min(100, self.__int(progress, step.get("progress", 0))))
            if ps is not None:
                step["ps"] = str(ps)
            if status is not None:
                task["status"] = status
                step["status"] = status
            if result is not None:
                step["result"] = result
                step["result_list"] = self.__task_result_list(result)
            if error is not None:
                task["error"] = str(error)
                step["error"] = str(error)
            task["updated_at"] = int(time.time())
            self.__write_task(task)

        if not self.__bool(self.__get(get, "background", False)):
            try:
                self.__write_task_lock(threading.get_ident())
                update_progress(5, "Task started", 0)
                result = self.__run_task_runner(runner, update_progress)
                update_progress(100, "Task completed", 1, result=result)
                return self.__ok(result)
            except Exception as ex:
                update_progress(self.__task_step(task).get("progress", 0), "Task failed", -1, error=str(ex))
                self.__log("{} failed: {}".format(action, traceback.format_exc()))
                return self.__fail(str(ex))
            finally:
                self.__remove_task_lock()
                task["updated_at"] = int(time.time())
                self.__write_task(task)

        def target():
            try:
                self.__write_task_lock(threading.get_ident())
                update_progress(5, "Task started", 0)
                result = self.__run_task_runner(runner, update_progress)
                update_progress(100, "Task completed", 1, result=result)
            except Exception as ex:
                update_progress(self.__task_step(task).get("progress", 0), "Task failed", -1, error=str(ex))
                self.__log("task failed: current {}".format(traceback.format_exc()))
            finally:
                self.__remove_task_lock()
                task["updated_at"] = int(time.time())
                self.__write_task(task)

        delay = float(getattr(self, "background_start_delay", 0) or 0)
        t = threading.Timer(delay, target) if delay > 0 else threading.Thread(target=target)
        t.daemon = True
        t.start()
        return self.__ok(task)

    def __task_file(self):
        return os.path.join(self.task_dir, "current_task.json")

    def __task_lock_file(self):
        return os.path.join(self.task_dir, "current_task.lock")

    def __write_task(self, data):
        self.__write_json(self.__task_file(), data)

    def __task_step(self, task):
        if "cloud_storage_task" not in task or not isinstance(task.get("cloud_storage_task"), dict):
            task["cloud_storage_task"] = {}
        return task["cloud_storage_task"]

    def __normalize_task(self, task):
        if not isinstance(task, dict):
            task = {}
        old_step = task.get("cloud_storage_task", {})
        if not isinstance(old_step, dict):
            old_step = {}
        status = self.__int(task.get("status", old_step.get("status", 1)), 1)
        error = str(task.get("error", old_step.get("error", "")) or "")
        progress_default = 0 if status == 0 else 100
        result = old_step.get("result", task.get("result", None))
        result_list = old_step.get("result_list", task.get("result_list", self.__task_result_list(result)))
        step = {
            "status": status,
            "ps": str(old_step.get("ps", task.get("ps", "")) or ""),
            "title": str(old_step.get("title", "Cloud Storage Task") or "Cloud Storage Task"),
            "action": str(old_step.get("action", task.get("action", "")) or ""),
            "progress": max(0, min(100, self.__int(old_step.get("progress", task.get("progress", progress_default)), progress_default))),
            "result": result,
            "result_list": result_list if isinstance(result_list, list) else [],
            "error": str(old_step.get("error", error) or ""),
            "alive": self.__bool(old_step.get("alive", task.get("alive", False))),
            "stale": self.__bool(old_step.get("stale", task.get("stale", False))),
        }
        if step["error"] and not error:
            error = step["error"]
        return {
            "status": status,
            "error": error,
            "created_at": self.__int(task.get("created_at", 0), 0),
            "updated_at": self.__int(task.get("updated_at", 0), 0),
            "cloud_storage_task": step,
        }

    def __task_result_list(self, result):
        if not isinstance(result, dict):
            return []
        if isinstance(result.get("result_list"), list):
            return result.get("result_list")
        for key in ("uploaded", "downloaded", "deleted"):
            if isinstance(result.get(key), list):
                return result.get(key)
        return []

    def __write_task_lock(self, thread_id):
        try:
            with open(self.__task_lock_file(), "w") as fp:
                fp.write(str(thread_id))
        except:
            pass

    def __remove_task_lock(self):
        try:
            lock_file = self.__task_lock_file()
            if os.path.exists(lock_file):
                os.remove(lock_file)
        except:
            pass

    def __task_alive(self):
        lock_file = self.__task_lock_file()
        if not os.path.exists(lock_file):
            return False
        try:
            with open(lock_file, "r") as fp:
                thread_id = int(fp.read().strip())
            return any(t.ident == thread_id for t in threading.enumerate())
        except:
            self.__remove_task_lock()
            return False

    def __current_running_task(self):
        task_file = self.__task_file()
        if not os.path.exists(task_file):
            return None
        task = self.__read_json(task_file, {})
        task = self.__normalize_task(task)
        if self.__int(task.get("status", 1), 1) != 0:
            return None
        alive = self.__task_alive()
        is_starting = int(time.time()) - self.__int(task.get("created_at", 0), 0) <= 5
        if alive or is_starting:
            self.__task_step(task)["alive"] = alive
            self.__task_step(task)["stale"] = False
            return task
        task["status"] = -1
        task["error"] = task.get("error") or "Task thread is not alive"
        self.__task_step(task)["status"] = -1
        self.__task_step(task)["ps"] = "Task interrupted"
        self.__task_step(task)["error"] = task["error"]
        self.__task_step(task)["alive"] = False
        self.__task_step(task)["stale"] = True
        task["updated_at"] = int(time.time())
        self.__write_task(task)
        return None

    def __run_task_runner(self, runner, update_progress):
        code = getattr(runner, "__code__", None)
        if code and code.co_argcount > 0:
            return runner(update_progress)
        return runner()

    def __read_json(self, filename, default):
        try:
            with open(filename, "r") as fp:
                return json.loads(fp.read())
        except:
            return default

    def __write_json(self, filename, data):
        with open(filename, "w") as fp:
            fp.write(json.dumps(data, ensure_ascii=False, indent=2))

    def __read_chunk_data(self, get):
        chunk_base64 = self.__get(get, "chunk_base64", "")
        if chunk_base64:
            return base64.b64decode(chunk_base64)
        try:
            from flask import request
            for key in ("file", "chunk", "blob"):
                if key in request.files:
                    return request.files[key].read()
        except:
            pass
        raw = self.__get(get, "chunk", None)
        if raw is None:
            return None
        if isinstance(raw, bytes):
            return raw
        return str(raw).encode()

    def __elapsed_ms(self, start_time):
        try:
            return int((time.time() - start_time) * 1000)
        except:
            return 0

    def __upload_timing_log(self, request_id, stage, start_time, extra=""):
        if not self.debug_upload_local_timing:
            return
        msg = "upload_local timing [{}] stage={} elapsed_ms={}".format(
            request_id,
            stage,
            self.__elapsed_ms(start_time)
        )
        if extra:
            msg += " " + str(extra)
        self.__log(msg)

    def __log(self, body):
        try:
            line = "[{}] {}\n".format(time.strftime("%Y-%m-%d %H:%M:%S"), body)
            with open(self.log_file, "a") as fp:
                fp.write(line)
        except:
            pass
