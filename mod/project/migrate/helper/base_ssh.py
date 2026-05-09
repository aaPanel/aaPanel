import os
import re
import socket
import time
import uuid

import paramiko


class SSHManager:
    """基础ssh"""

    def __init__(self, host: str, auth: dict, port: int = 22, user: str = 'root', timeout: int = 10,
                 keepalive: int = 30, retry: int = 2):
        self.host = host
        self.port = port
        self.user = user
        self.auth = auth
        self.timeout = timeout
        self.keepalive = keepalive
        self.retry = retry
        self.client = None

    def __enter__(self):
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def connect(self, retry: int = None, retry_delay: float = 0.25):
        if self.client and self.client.get_transport() and self.client.get_transport().is_active():
            return

        attempts = (self.retry if retry is None else retry) + 1
        last_error = None
        for i in range(attempts):
            self.close()
            client = paramiko.SSHClient()
            client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            try:
                if (
                        "key_file" in self.auth
                        and self.auth["key_file"]
                        and os.path.exists(self.auth["key_file"])
                ):
                    client.connect(
                        self.host,
                        port=self.port,
                        username=self.user,
                        key_filename=self.auth["key_file"],
                        timeout=self.timeout,
                        banner_timeout=self.timeout,
                        auth_timeout=self.timeout,
                        compress=True,  # 启用压缩
                    )
                else:
                    client.connect(
                        self.host,
                        port=self.port,
                        username=self.user,
                        password=self.auth.get("password"),
                        timeout=self.timeout,
                        banner_timeout=self.timeout,
                        auth_timeout=self.timeout,
                        compress=True,  # 启用压缩
                    )
                transport = client.get_transport()
                transport.set_keepalive(self.keepalive)
                sock = transport.sock
                sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)  # 禁用 Nagle 算法
                sock.setsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF, 256 * 1024)  # 增大发送缓冲区
                sock.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, 256 * 1024)  # 增大接收缓冲区
                self.client = client
                return
            except Exception as e:
                last_error = e
                try:
                    client.close()
                except Exception:
                    pass
                if i == attempts - 1:
                    break
                time.sleep(retry_delay * (i + 1))  # 0.25, 0.5, 0.75...
        raise Exception(
            f"SSH Connection to {self.user}@{self.host}:{self.port} failed "
            f"after {attempts} attempts: {last_error}"
        )

    def execute(self, command: str, timeout: int = 10, retry: int = 2, retry_delay: float = 0.3) -> tuple:
        """Returns (exit_status, stdout, stderr)"""
        error = ""
        retry = self.retry if self.retry else retry
        for r in range(retry + 1):
            self.connect()
            try:
                stdin, stdout, stderr = self.client.exec_command(command, timeout=timeout)
                out = stdout.read().decode('utf-8', errors='ignore').strip()
                err = stderr.read().decode('utf-8', errors='ignore').strip()
                exit_status = stdout.channel.recv_exit_status()
                return exit_status, out, err
            except Exception as e:
                error = str(e)
                if r >= retry:
                    break
                self.close()
                time.sleep(retry_delay)
        return -1, "", f"Command execution failed: {error}"

    def execute_many(self, commands: list[str], timeout: int = 30, retry: int = 2, retry_delay: float = 0.3) -> list:
        """批量执行命令并发"""
        results = []
        if not commands:
            return results

        boundary = f"BND_{uuid.uuid4().hex}"  # 唯一边界符
        # 前批次唯一的临时目录
        tmp_dir = f"/tmp/ssh_batch_{uuid.uuid4().hex}"
        MAX_LEN = 100000
        chunks = []
        current_chunk = []
        current_len = 0
        for i, cmd in enumerate(commands):
            # 转义
            octal_cmd = "".join(f"\\{b:03o}" for b in cmd.encode('utf-8'))
            # 执行
            run_cmd = (
                f"( ( eval \"$(printf '%b' '{octal_cmd}')\" ) "
                f"> {tmp_dir}/o_{i} 2> {tmp_dir}/e_{i}; "
                f"echo $? > {tmp_dir}/r_{i} ) & "
            )
            # 收集
            collect_cmd = (
                f"printf '\\n{boundary}_S_{i}\\n';"
                f"cat {tmp_dir}/o_{i} 2>/dev/null;"
                f"RET=$(cat {tmp_dir}/r_{i} 2>/dev/null || echo -1);"
                f"printf '\\n{boundary}_E_{i}_%d\\n' \"$RET\";"

                f"printf '\\n{boundary}_S_{i}\\n' >&2;"
                f"cat {tmp_dir}/e_{i} 2>/dev/null >&2;"
                f"printf '\\n{boundary}_E_{i}\\n' >&2;"
            )
            total_len = len(run_cmd) + len(collect_cmd)
            # 分块
            if current_len + total_len > MAX_LEN and current_chunk:
                chunks.append(current_chunk)
                current_chunk = []
                current_len = 0

            current_chunk.append((i, cmd, run_cmd, collect_cmd))
            current_len += total_len

        if current_chunk:
            chunks.append(current_chunk)

        for chunk in chunks:
            # 1.建目录 2.并发 3.等待完成 4.顺序打印 5.清理垃圾
            run_cmds_str = "".join([c[2] for c in chunk])
            collect_cmds_str = "".join([c[3] for c in chunk])
            full_command = f"mkdir -p {tmp_dir}; {run_cmds_str} wait; {collect_cmds_str} rm -rf {tmp_dir};"
            exit_status, out, err = self.execute(
                full_command,
                timeout=timeout,
                retry=retry,
                retry_delay=retry_delay
            )
            global_fail = (exit_status == -1 and "Command execution failed:" in err)
            for i, cmd_str, _, _ in chunk:
                res_dict = {
                    "index": i,
                    "cmd": cmd_str,
                    "code": -1,
                    "stdout": "",
                    "stderr": ""
                }
                if global_fail:
                    res_dict["stderr"] = err
                    results.append(res_dict)
                    continue

                out_pattern = re.compile(rf"{boundary}_S_{i}\s*(.*?)\s*{boundary}_E_{i}_(-?\d+)", re.DOTALL)
                out_match = out_pattern.search(out)
                err_pattern = re.compile(rf"{boundary}_S_{i}\s*(.*?)\s*{boundary}_E_{i}", re.DOTALL)
                err_match = err_pattern.search(err)
                if out_match:
                    res_dict["stdout"] = out_match.group(1).strip()
                    res_dict["code"] = int(out_match.group(2))
                else:
                    res_dict["stderr"] += "\n[Batch Error] Failed to parse output boundary."

                if err_match:
                    res_dict["stderr"] = (res_dict["stderr"] + "\n" + err_match.group(1).strip()).strip()

                results.append(res_dict)

        results.sort(key=lambda x: x["index"])
        return results

    def download(self, remote_path: str, local_path: str, progress_callback=None) -> bool:
        self.connect()
        sftp = self.client.open_sftp()
        try:
            try:
                remote_stat = sftp.stat(remote_path)
                remote_size = remote_stat.st_size
            except IOError:
                raise FileNotFoundError(f"Remote file {remote_path} not found")

            local_size = os.path.getsize(local_path) if os.path.exists(local_path) else 0
            if local_size >= remote_size:
                if progress_callback:
                    progress_callback(remote_size, remote_size)
                return True

            with open(local_path, 'ab' if local_size > 0 else 'wb') as local_f:
                with sftp.open(remote_path, 'rb') as remote_f:
                    if local_size > 0:
                        remote_f.seek(local_size)

                    # Paramiko预读机制
                    remote_f.prefetch(remote_size)
                    target_duration = 0.05
                    min_chunk = 16 * 1024
                    max_chunk = 2 * 1024 * 1024
                    chunk_size = 64 * 1024

                    transferred = 0
                    while True:
                        start_time = time.perf_counter()

                        data = remote_f.read(int(chunk_size))
                        if not data:
                            break

                        local_f.write(data)
                        transferred += len(data)

                        if progress_callback:
                            progress_callback(local_size + transferred, remote_size)

                        elapsed = int(time.perf_counter() - start_time)

                        if elapsed > 0:
                            speed = len(data) / elapsed
                            next_chunk_size = int(speed * target_duration)
                            chunk_size = max(min_chunk, min(next_chunk_size, max_chunk))
                        else:
                            chunk_size = min(chunk_size * 2, max_chunk)

            return True
        finally:
            sftp.close()

    def close(self):
        if self.client:
            try:
                self.client.close()
            except Exception:
                pass
            self.client = None
