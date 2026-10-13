# coding: utf-8
"""Git manager v2: public/SSH/token auth, revisions, deployment and rollback."""

import json
import os
import re
import shlex
import shutil
import stat
import subprocess
import tempfile
import time
import urllib.parse
import uuid
from contextlib import contextmanager
from datetime import datetime

import public
from git_auth import decrypt_git_token, encrypt_git_token
from git_github import resolve_github_credentials


AUTH_TYPES = ("public", "ssh_key", "token", "github")
GIT_CACHE_ROOT = "/www/server/panel/data/git_cache"
DEFAULT_IGNORE_PATHS = ["/.env", "/storage", "/bootstrap/cache"]


def _request_data(get):
    if isinstance(get, dict):
        return dict(get)
    if hasattr(get, "get_items"):
        return dict(get.get_items())
    return dict(get.__dict__)


def _has_field(get, name):
    if isinstance(get, dict):
        return name in get
    if hasattr(get, "get_items"):
        return name in get.get_items()
    return name in getattr(get, "__dict__", {})


def _auth_api(value):
    value = str(value or "").strip().lower()
    return "ssh_key" if value in ("ssh", "ssh_key") else (value or "public")


def _auth_db(value):
    value = _auth_api(value)
    return "ssh" if value == "ssh_key" else value


def _transport(repository):
    repository = str(repository or "").strip()
    if re.match(r"^[A-Za-z0-9._-]+@[^\s:/]+:.+$", repository):
        return "ssh"
    parsed = urllib.parse.urlsplit(repository)
    if parsed.scheme == "ssh" and parsed.hostname:
        return "ssh"
    if parsed.scheme in ("http", "https") and parsed.netloc:
        return parsed.scheme
    return "unknown"


def _validate_key(key_path):
    key_path = os.path.realpath(str(key_path or "").strip())
    ssh_root = os.path.realpath("/root/.ssh")
    try:
        inside_root = os.path.commonpath((ssh_root, key_path)) == ssh_root
    except ValueError:
        inside_root = False
    if not key_path or not inside_root or key_path.endswith(".pub"):
        raise ValueError("Git SSH key must be a private key under /root/.ssh")
    if not os.path.isfile(key_path) or not os.path.isfile(key_path + ".pub"):
        raise ValueError("Git SSH private key does not exist")
    public_key = str(public.readFile(key_path + ".pub") or "").strip()
    if not public_key.startswith("ssh-ed25519 "):
        raise ValueError("Only ED25519 SSH keys are supported")
    return key_path


def _normalize(data, stored=None, token_required=True):
    data = dict(data or {})
    stored = dict(stored or {})
    repository = str(
        data.get("repo_url", data.get("repo", stored.get("repo", "")))
    ).strip()
    raw_auth_type = data.get("auth_type", stored.get("auth_type", ""))
    if not raw_auth_type and data.get("key_path"):
        raw_auth_type = "ssh_key"
    elif not raw_auth_type and (data.get("username") or data.get("token")):
        raw_auth_type = "token"
    auth_type = _auth_api(raw_auth_type)
    branch = str(data.get("branch", stored.get("branch", ""))).strip()
    if not repository or any(char.isspace() for char in repository):
        raise ValueError("Git repository URL is invalid")
    if auth_type not in AUTH_TYPES:
        raise ValueError("Unsupported Git authentication type")
    transport = _transport(repository)
    parsed = urllib.parse.urlsplit(repository) if "://" in repository else None
    # SSH 传输中 user@ 是连接用户名（如 ssh://git@host:port/path），属正常格式；
    # 仅 HTTP/HTTPS URL 内嵌用户名/密码才是凭据泄漏，需拦截。
    if parsed and transport in ("http", "https") and (
        parsed.username is not None or parsed.password is not None
    ):
        raise ValueError("Do not include credentials in the Git repository URL")
    config = {"repo": repository, "branch": branch, "auth_type": auth_type}
    if auth_type == "public":
        if transport not in ("http", "https"):
            raise ValueError("Public repositories must use HTTP or HTTPS")
    elif auth_type == "ssh_key":
        if transport != "ssh":
            # 兼容旧版历史数据: 仓库为 HTTPS 却绑定了 SSH key。
            # SSH key 对 HTTPS 传输无效，降级到public访问
            config["auth_type"] = "public"
        else:
            config["key_path"] = _validate_key(
                data.get("key_path", stored.get("key_path", ""))
            )
    elif auth_type == "token":
        if transport != "https":
            raise ValueError("Token authentication requires an HTTPS repository URL")
        username = str(data.get("username", stored.get("username", ""))).strip()
        token = str(data.get("token", ""))
        if not token and stored.get("oauth_access_token"):
            try:
                token = decrypt_git_token(stored["oauth_access_token"])
            except Exception:
                raise ValueError("The saved Git personal access token cannot be decrypted")
        if not username:
            raise ValueError("Git username is required")
        if token_required and not token:
            raise ValueError("Git personal access token is required")
        config.update({"username": username, "token": token})
    elif auth_type == "github":
        if transport != "https" or "github.com" not in repository.lower():
            raise ValueError(
                "GitHub account authentication requires a github.com HTTPS repository URL"
            )
        login, token = resolve_github_credentials()
        # 复用 token 鉴权环境；标记来源为 github，_save_binding 据此存回 auth_type=github
        config.update({
            "_github_auth": True,
            "auth_type": "token",
            "username": login,
            "token": token,
        })
    return config


def _site_config(site_id):
    record = public.M("git_sites_auth").where("site_id=?", (int(site_id),)).find()
    if not record:
        raise ValueError("This website is not bound to a Git repository")
    return _normalize({}, record), record


def _site_ignore_paths(site_id):
    """读取网站的忽略路径列表；未配置时返回默认忽略路径。"""
    try:
        raw = public.M("git_sites_auth").where(
            "site_id=?", (int(site_id),)
        ).getField("ignore_paths")
        if not raw:
            return list(DEFAULT_IGNORE_PATHS)
        parsed = json.loads(raw)
        if not isinstance(parsed, list):
            return list(DEFAULT_IGNORE_PATHS)
        return [str(item).strip() for item in parsed if str(item).strip()]
    except Exception:
        return list(DEFAULT_IGNORE_PATHS)


def _ignore_static_prefix(pattern):
    """取 ignore pattern 的非通配静态前缀，用于部署保留与可写判断。

    'docs/**' -> 'docs'，'/.env' -> '.env'，'storage/' -> 'storage'，'bootstrap/cache' -> 'bootstrap/cache'
    """
    pattern = str(pattern or "").strip().strip('/')
    if not pattern:
        return ""
    prefix = []
    for seg in pattern.split('/'):
        if any(ch in seg for ch in '*?['):
            break
        prefix.append(seg)
    return '/'.join(prefix)


@contextmanager
def _environment(config):
    environment = os.environ.copy()
    environment["GIT_TERMINAL_PROMPT"] = "0"
    # 网站目录 git 仓库可能属于 www 用户，面板进程执行 git 会触发 dubious ownership
    # 统一信任所有目录,避免部署/拉取时 safe.directory 报错
    environment["GIT_SAFE_DIRECTORY"] = "*"
    # git 对 HTTP 传输默认无超时，慢/断流时可能无限等待。限制低速率连接快速失败。
    environment["GIT_HTTP_LOW_SPEED_LIMIT"] = "1000"
    environment["GIT_HTTP_LOW_SPEED_TIME"] = "60"
    auth_dir = ""
    if config["auth_type"] == "ssh_key":
        environment["HOME"] = "/root"
        environment["GIT_SSH_COMMAND"] = (
            "ssh -i {} -o IdentitiesOnly=yes -o BatchMode=yes "
            "-o StrictHostKeyChecking=accept-new "
            "-o UserKnownHostsFile=/root/.ssh/known_hosts"
        ).format(shlex.quote(config["key_path"]))
    elif config["auth_type"] == "token":
        auth_dir = tempfile.mkdtemp(prefix="aapanel_git_auth_")
        os.chmod(auth_dir, 0o700)
        username_file = os.path.join(auth_dir, "username")
        token_file = os.path.join(auth_dir, "token")
        askpass_file = os.path.join(auth_dir, "askpass.sh")
        for path, value in (
            (username_file, config["username"]),
            (token_file, config["token"]),
        ):
            with open(path, "w", encoding="utf-8") as handle:
                handle.write(value)
            os.chmod(path, stat.S_IRUSR | stat.S_IWUSR)
        with open(askpass_file, "w", encoding="utf-8") as handle:
            handle.write(
                "#!/bin/sh\ncase \"$1\" in *sername*) cat ''{}'';; *) cat ''{}'';; esac\n".format(
                    username_file, token_file
                )
            )
        os.chmod(askpass_file, stat.S_IRUSR | stat.S_IWUSR | stat.S_IXUSR)
        environment["GIT_ASKPASS"] = askpass_file
        environment["GIT_ASKPASS_REQUIRE"] = "force"
    try:
        yield environment
    finally:
        if auth_dir:
            shutil.rmtree(auth_dir, ignore_errors=True)


def _redact(text, config):
    result = str(text or "")
    token = str(config.get("token", ""))
    if token:
        result = result.replace(token, "***")
    return result


def _run(args, config, cwd=None, timeout=180, check=True, progress_log=None):
    command = ["git"]
    # 网站目录 git 仓库可能属于 www 用户，面板进程执行 git 会触发 dubious ownership
    command.extend(["-c", "safe.directory=*"])
    if _transport(config.get("repo")) in ("http", "https"):
        command.extend(["-c", "http.version=HTTP/1.1"])
    command.extend([str(item) for item in args])
    with _environment(config) as environment:
        if progress_log:
            return _run_with_progress(
                command, args, config, environment, cwd, timeout, check, progress_log,
            )
        try:
            process = subprocess.run(
                command, cwd=cwd, env=environment,
                stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                text=True, timeout=timeout,
            )
        except subprocess.TimeoutExpired:
            # subprocess.run 超时后已 kill 主进程；给出清晰错误而非永久等待
            raise ValueError(
                "Git command timed out after {} seconds: {}".format(
                    timeout, " ".join(str(item) for item in args)[-2000:]
                )
            )
    stdout = _redact(process.stdout, config)
    stderr = _redact(process.stderr, config)
    if check and process.returncode != 0:
        error_text = stderr.strip() or stdout.strip() or "Git command failed"
        raise ValueError(error_text[-4000:])
    return process.returncode, stdout, stderr


def _run_with_progress(command, args, config, environment, cwd, timeout, check, progress_log):
    """边执行 git 边把 stderr（--progress 输出）追加到 progress_log，供 get_clone_progress 轮询。

    clone 的 --progress 全在 stderr，故 stderr 直接重定向到日志文件（内核级追加、
    无缓冲），stdout 仍捕获到内存；stderr 已落盘、不再返回（返回空串）。
    """
    log_fp = open(progress_log, "a", encoding="utf-8", errors="replace")
    try:
        process = subprocess.Popen(
            command, cwd=cwd, env=environment,
            stdout=subprocess.PIPE, stderr=log_fp, text=True,
        )
        log_fp.close()  # 子进程持有写端，父进程关闭自己的副本
    except Exception:
        try:
            log_fp.close()
        except Exception:
            pass
        raise
    try:
        stdout, _ = process.communicate(timeout=timeout)
    except subprocess.TimeoutExpired:
        process.kill()
        process.communicate()
        raise ValueError(
            "Git command timed out after {} seconds: {}".format(
                timeout, " ".join(str(item) for item in args)[-2000:]
            )
        )
    stdout = _redact(stdout or "", config)
    if check and process.returncode != 0:
        # stderr 已写入日志文件，从末尾取错误摘要（可能已含 --progress，截断到 4000）
        error_text = ""
        try:
            error_text = str(public.readFile(progress_log) or "")
        except Exception:
            pass
        error_text = (error_text or stdout or "Git command failed").strip()
        raise ValueError(error_text[-4000:])
    return process.returncode, stdout, ""


def _remote_refs(config):
    # 超时时间改30s
    _, stdout, _ = _run(
        ["ls-remote", "--symref", config["repo"], "HEAD", "refs/heads/*"],
        config, timeout=30,
    )
    default_branch = ""
    branches = []
    for line in stdout.splitlines():
        if line.startswith("ref: refs/heads/") and line.endswith("\tHEAD"):
            default_branch = line.split("refs/heads/", 1)[1].split("\t", 1)[0]
        elif "refs/heads/" in line:
            branch = line.split("refs/heads/", 1)[1].strip()
            if branch and branch not in branches:
                branches.append(branch)
    branches.sort()
    return default_branch, branches


def _clone(config, branch, parent_dir, shallow=False):
    target = os.path.join(parent_dir, "repository")
    clone_args = [
        "clone", "--no-checkout", "--single-branch", "--branch", branch,
    ]
    if shallow:
        clone_args.extend(["--depth", "1"])
    clone_args.extend([config["repo"], target])
    _run(clone_args, config, timeout=600)
    if not os.path.isdir(os.path.join(target, ".git")):
        raise ValueError("Git clone did not create a repository")
    return target


def _resolve(repo_path, config, branch, commit_hash="", remote_ref=None):
    remote_ref = remote_ref or "refs/remotes/origin/{}".format(branch)
    target = str(commit_hash or "").strip() or remote_ref
    _, stdout, _ = _run(
        ["rev-parse", "{}^{{commit}}".format(target)], config, cwd=repo_path
    )
    full_commit = stdout.strip()
    if not re.match(r"^[0-9a-fA-F]{40}$", full_commit):
        raise ValueError("Unable to resolve the selected commit")
    if commit_hash:
        return_code, _, _ = _run(
            ["merge-base", "--is-ancestor", full_commit, remote_ref],
            config, cwd=repo_path, check=False,
        )
        if return_code != 0:
            raise ValueError(
                "The selected commit does not belong to origin/{}".format(branch)
            )
    return full_commit


def _commit_info(repo_path, config, commit_hash):
    fmt = "%H%x1f%h%x1f%an%x1f%ae%x1f%ct%x1f%s"
    _, stdout, _ = _run(
        ["show", "-s", "--format={}".format(fmt), commit_hash],
        config, cwd=repo_path,
    )
    parts = stdout.strip().split("\x1f", 5)
    if len(parts) != 6:
        raise ValueError("Failed to read Git commit information")
    return {
        "commit_hash": parts[0], "commit_hash_short": parts[1],
        "author_name": parts[2], "author_email": parts[3],
        "committed_time": datetime.fromtimestamp(int(parts[4])).strftime(
            "%Y-%m-%d %H:%M:%S"
        ),
        "message": parts[5].strip(),
    }


def _clone_mirror(self, mirror, config, branch):
    """clone 一份裸仓库；失败时清理目录并抛错。"""
    try:
        # 用 --bare 而非 --mirror：ref 平铺到 refs/heads/<branch>，
        # 配合 --single-branch + --filter 在真实 HTTPS/protocol v2 下行为一致。
        _run(
            [
                "clone", "--bare", "--single-branch", "--branch", branch,
                "--filter=blob:none", config["repo"], mirror,
            ],
            config, timeout=600,
        )
    except Exception:
        shutil.rmtree(mirror, ignore_errors=True)
        raise


def _mirror_has_ref(self, mirror, config, branch_ref):
    """校验 mirror 中目标 ref 是否存在（不存在视为坏缓存）。"""
    try:
        _, stdout, _ = _run(
            ["rev-parse", "--verify", "--quiet", "{}^{{commit}}".format(branch_ref)],
            config, cwd=mirror, check=False,
        )
    except Exception:
        return False
    return bool(stdout.strip())


def _mirror_repository(self, site_id, config, branch, refresh=True):
    """返回持久化的裸仓库 mirror（用于提交列表/详情查询），按需 fetch 增量更新。

    缓存目录：{GIT_CACHE_ROOT}/<site_id>/<branch>.git
    refs 布局：mirror 仓库中远程分支位于 refs/heads/<branch>。
    自愈：目录无效 / fetch 失败 / 目标 ref 缺失时删除重建，避免坏缓存导致查询报错。
    """
    cache_dir = os.path.join(GIT_CACHE_ROOT, str(int(site_id)))
    mirror = os.path.join(cache_dir, "{}.git".format(branch.replace("/", "__")))
    os.makedirs(cache_dir, mode=0o700, exist_ok=True)
    import fcntl
    lock_handle = open(
        "/tmp/aapanel_git_cache_{}_{}.lock".format(
            int(site_id), branch.replace("/", "__")
        ),
        "a+",
    )
    try:
        fcntl.flock(lock_handle.fileno(), fcntl.LOCK_EX)
        branch_ref = "refs/heads/{}".format(branch)
        # 有效标志是存在 objects/（真正的裸仓库）；仅 isdir(mirror) 可能命中坏缓存
        if not os.path.isdir(os.path.join(mirror, "objects")):
            shutil.rmtree(mirror, ignore_errors=True)
            _clone_mirror(self, mirror, config, branch)
        else:
            if refresh:
                try:
                    # 完整 refspec 而非短名，避免 --prune 误删本地 ref
                    _run(
                        [
                            "fetch", "--filter=blob:none", "origin",
                            "{}:{}".format(branch_ref, branch_ref), "--prune",
                        ],
                        config, cwd=mirror, timeout=300,
                    )
                except Exception:
                    # fetch 失败：缓存可能损坏，删掉重 clone
                    shutil.rmtree(mirror, ignore_errors=True)
                    _clone_mirror(self, mirror, config, branch)
            # 校验目标 ref 存在；缺失则重建（覆盖历史坏缓存）
            if not _mirror_has_ref(self, mirror, config, branch_ref):
                shutil.rmtree(mirror, ignore_errors=True)
                _clone_mirror(self, mirror, config, branch)
    finally:
        try:
            fcntl.flock(lock_handle.fileno(), fcntl.LOCK_UN)
        finally:
            lock_handle.close()
    return mirror


def _restore_preserved_paths(backup_path, site_path, preserve_paths):
    """部署全量替换后，把旧网站目录中需要保留的路径复制回新网站目录。

    支持 gitignore 风格 pattern（如 'docs/**'），按静态前缀保留整棵目录。
    """
    seen = set()
    for pattern in preserve_paths:
        static = _ignore_static_prefix(pattern)
        if not static or static in seen:
            continue
        seen.add(static)
        old_path = os.path.join(backup_path, static)
        new_path = os.path.join(site_path, static)
        if os.path.isfile(old_path):
            os.makedirs(os.path.dirname(new_path) or site_path, exist_ok=True)
            shutil.copy2(old_path, new_path)
        elif os.path.isdir(old_path):
            if os.path.exists(new_path):
                if os.path.isdir(new_path) and not os.path.islink(new_path):
                    shutil.rmtree(new_path)
                else:
                    os.remove(new_path)
            os.makedirs(os.path.dirname(new_path) or site_path, exist_ok=True)
            shutil.copytree(old_path, new_path, dirs_exist_ok=True)


def _restore_existing_files(backup_path, site_path):
    """全量替换后，把旧网站目录中「新代码没有的」已有文件保留回新网站目录。

    同名路径以新代码为准（旧文件不覆盖新代码），只补充缺失文件/目录，
    避免连接部署时把用户在网站目录内手动放置的文件整体替换掉。
    跳过 .git（保留新克隆仓库元数据）与 .user.ini（已单独恢复并锁定）。
    """
    if not os.path.isdir(backup_path):
        return
    for root, dirs, files in os.walk(backup_path):
        rel_root = os.path.relpath(root, backup_path)
        if rel_root == ".":
            rel_root = ""
            dirs[:] = [d for d in dirs if d != ".git"]
        if rel_root:
            new_dir = os.path.join(site_path, rel_root)
            if not os.path.exists(new_dir):
                os.makedirs(new_dir, exist_ok=True)
        for name in files:
            if rel_root == "" and name == ".user.ini":
                continue
            old_file = os.path.join(root, name)
            new_file = (
                os.path.join(site_path, rel_root, name)
                if rel_root else os.path.join(site_path, name)
            )
            if os.path.exists(new_file):
                continue
            os.makedirs(os.path.dirname(new_file) or site_path, exist_ok=True)
            shutil.copy2(old_file, new_file)


def _merge_tree(src, dst, ignore_paths):
    """把 src 目录内容合并进 dst：覆盖同名/新增文件，不删除 dst 中已有文件。

    - 跳过 .git（不覆盖网站已有 git 元数据）与 .user.ini
    - 跳过 ignore_paths 前缀（本地配置/可写目录不被新代码覆盖）
    - 优先 rsync（增量、保留软链接与权限）；无 rsync 时回退 Python 遍历
    - 软链接用 os.symlink 重建，不复制目标内容
    合并失败（含磁盘满）时抛 OSError，dst 已有文件不受影响。
    """
    os.makedirs(dst, exist_ok=True)
    prefixes = [
        _ignore_static_prefix(item) for item in (ignore_paths or [])
    ]
    prefixes = [p for p in prefixes if p and p != "."]

    def _ignored(rel):
        for prefix in prefixes:
            if rel == prefix or rel.startswith(prefix + "/"):
                return True
        return False

    if shutil.which("rsync"):
        cmd = ["rsync", "-a", "--exclude=.git", "--exclude=.user.ini"]
        for prefix in prefixes:
            # 带根级斜杠，与下方 Python 回退的根级前缀匹配保持一致
            cmd.extend(["--exclude", "/" + prefix])
        # src 尾 / 表示同步目录内容；不传 --delete，保留 dst 中多出的文件
        cmd.extend([src.rstrip("/") + "/", dst.rstrip("/") + "/"])
        proc = subprocess.run(
            cmd, capture_output=True, text=True, timeout=1800,
        )
        if proc.returncode == 0:
            return
        raise OSError(
            "Failed to merge code into the website directory: {}".format(
                proc.stderr.strip() or "rsync exit {}".format(proc.returncode)
            )
        )

    # Python 回退：遍历 src，覆盖同名/新增，跳过 .git/.user.ini/ignore_paths，软链接重建
    for root, dirs, files in os.walk(src):
        rel_root = os.path.relpath(root, src)
        if rel_root == ".":
            rel_root = ""
        dirs[:] = [d for d in dirs if d not in (".git", ".user.ini")]
        for name in files:
            if name == ".user.ini":
                continue
            src_file = os.path.join(root, name)
            dst_file = (
                os.path.join(dst, rel_root, name)
                if rel_root else os.path.join(dst, name)
            )
            rel = (os.path.join(rel_root, name) if rel_root else name).replace(os.sep, "/")
            if _ignored(rel):
                continue
            os.makedirs(os.path.dirname(dst_file) or dst, exist_ok=True)
            if os.path.islink(src_file):
                if os.path.islink(dst_file) or os.path.exists(dst_file):
                    try:
                        os.remove(dst_file)
                    except OSError:
                        pass
                os.symlink(os.readlink(src_file), dst_file)
            else:
                shutil.copy2(src_file, dst_file)


def get_remote_branches(self, get):
    try:
        site_id = int(get.get("site_id", 0) or 0)
        stored = {}
        if site_id:
            stored = public.M("git_sites_auth").where(
                "site_id=?", (site_id,)
            ).find()
            if not stored:
                raise ValueError("This website is not bound to a Git repository")
        config = _normalize(_request_data(get), stored)
        default_branch, branches = _remote_refs(config)
        public.set_module_logs("Git-Tools", "get_remote_branches")
        return public.return_message(0, 0, {
            "auth_type": config["auth_type"],
            "default_branch": default_branch,
            "branches": branches,
        })
    except Exception as exc:
        return public.return_message(
            -1, 0, "Connection to GIT failed: {}".format(exc)
        )


def _current_branch(self, site_path):
    if not site_path or not os.path.isdir(os.path.join(site_path, ".git")):
        public.print_log("111")
        return ""
    try:
        # 网站目录 git 仓库可能属于 www 用户，面板以 root 执行会触发
        # dubious ownership；用 -c safe.directory 单次注入，不改全局配置。
        _, stdout, _ = _run(
            [
                "-c", "safe.directory={}".format(site_path),
                "rev-parse", "--abbrev-ref", "HEAD",
            ],
            {"repo": "", "auth_type": "public"}, cwd=site_path,
        )
        public.print_log(" stdout ---{}".format(stdout))
        return "" if stdout.strip() == "HEAD" else stdout.strip()
    except Exception as exc:
        public.print_log("222 {}".format(exc))
        return ""


def get_remote_commits(self, get):
    try:
        site_id = int(get.get("site_id", 0) or 0)
        branch = str(get.get("branch", "")).strip()
        if not site_id or not branch:
            raise ValueError("site_id and branch are required")
        page = max(1, int(get.get("p", 1) or 1))
        limit = min(100, max(1, int(get.get("limit", 20) or 20)))
        refresh = str(get.get("refresh", "1") or "1").lower() in ("1", "true", "yes")
        config, _ = _site_config(site_id)
        repo_path = _mirror_repository(self, site_id, config, branch, refresh)
        remote_ref = "refs/heads/{}".format(branch)
        _, count_stdout, _ = _run(
            ["rev-list", "--count", remote_ref], config, cwd=repo_path
        )
        fmt = "%H%x1f%h%x1f%an%x1f%ae%x1f%ct%x1f%s%x1e"
        _, log_stdout, _ = _run(
            [
                "log", remote_ref,
                "--skip={}".format((page - 1) * limit),
                "--max-count={}".format(limit),
                "--format={}".format(fmt),
            ],
            config, cwd=repo_path,
        )
        site_path = public.M("sites").where(
            "id=?", (site_id,)
        ).getField("path")
        current_commit = ""
        if site_path and os.path.isdir(os.path.join(site_path, ".git")):
            _, current_stdout, _ = _run(
                ["rev-parse", "HEAD"],
                {"repo": "", "auth_type": "public"},
                cwd=site_path, check=False,
            )
            current_commit = current_stdout.strip()
        commits = []
        for record in log_stdout.split("\x1e"):
            parts = record.strip().split("\x1f", 5)
            if len(parts) != 6:
                continue
            commits.append({
                "commit_hash": parts[0],
                "commit_hash_short": parts[1],
                "author_name": parts[2],
                "author_email": parts[3],
                "committed_time": datetime.fromtimestamp(
                    int(parts[4])
                ).strftime("%Y-%m-%d %H:%M:%S"),
                "message": parts[5].strip(),
                "is_deployed": parts[0] == current_commit,
            })
        public.set_module_logs("Git-Tools", "get_remote_commits")
        return public.return_message(0, 0, {
            "branch": branch,
            "remote_ref": "origin/{}".format(branch),
            "current_branch": _current_branch(self, site_path),
            "current_commit": current_commit,
            "data": commits,
            "page": {
                "p": page, "limit": limit,
                "total": int(count_stdout.strip() or 0),
            },
        })
    except Exception as exc:
        return public.return_message(-1, 0, str(exc))


def get_commit_detail(self, get):
    try:
        site_id = int(get.get("site_id", 0) or 0)
        branch = str(get.get("branch", "")).strip()
        commit_hash = str(get.get("commit_hash", "")).strip()
        if not site_id or not branch or not commit_hash:
            raise ValueError("site_id, branch and commit_hash are required")
        config, _ = _site_config(site_id)
        repo_path = _mirror_repository(self, site_id, config, branch, refresh=False)
        branch_ref = "refs/heads/{}".format(branch)
        full_commit = _resolve(repo_path, config, branch, commit_hash, branch_ref)
        info = _commit_info(repo_path, config, full_commit)
        _, numstat, _ = _run(
            ["show", "--format=", "--numstat", full_commit],
            config, cwd=repo_path,
        )
        _, name_status, _ = _run(
            [
                "diff-tree", "--root", "--no-commit-id",
                "--name-status", "-r", full_commit,
            ],
            config, cwd=repo_path,
        )
        status_names = {
            "A": "added", "M": "modified", "D": "deleted",
            "R": "renamed", "C": "copied", "T": "type_changed",
        }
        file_status = {}
        for line in name_status.splitlines():
            parts = line.split("\t")
            if len(parts) < 2:
                continue
            code = parts[0][:1]
            file_status[parts[-1]] = status_names.get(code, "modified")
        files = []
        additions = deletions = diff_used = 0
        diff_limit = 512 * 1024
        for line in numstat.splitlines():
            parts = line.split("\t", 2)
            if len(parts) != 3:
                continue
            add_value = int(parts[0]) if parts[0].isdigit() else 0
            del_value = int(parts[1]) if parts[1].isdigit() else 0
            additions += add_value
            deletions += del_value
            binary = parts[0] == "-" or parts[1] == "-"
            patch = ""
            if not binary and diff_used < diff_limit:
                _, patch, _ = _run(
                    ["show", "--format=", "--no-ext-diff", full_commit, "--", parts[2]],
                    config, cwd=repo_path,
                )
                patch = patch[:min(64 * 1024, diff_limit - diff_used)]
                diff_used += len(patch)
                files.append({
                "path": parts[2],
                "status": file_status.get(parts[2], "modified"),
                "additions": add_value, "deletions": del_value,
                "binary": binary, "patch": patch,
            })
        info.update({
            "branch": branch,
            "stats": {
                "files_changed": len(files),
                "additions": additions, "deletions": deletions,
            },
            "files": files,
            "diff_truncated": diff_used >= diff_limit,
        })
        public.set_module_logs("Git-Tools", "get_commit_detail")
        return public.return_message(0, 0, info)
    except Exception as exc:
        return public.return_message(-1, 0, str(exc))


@contextmanager
def _deploy_lock(site_id):
    import fcntl
    lock_handle = open(
        "/tmp/aapanel_git_deploy_{}.lock".format(int(site_id)), "a+"
    )
    try:
        try:
            fcntl.flock(
                lock_handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB
            )
        except BlockingIOError:
            raise ValueError(
                "A Git deployment for this website is already running"
            )
        yield
    finally:
        try:
            fcntl.flock(lock_handle.fileno(), fcntl.LOCK_UN)
        finally:
            lock_handle.close()


def _prune_records(site_id):
    number_copies = public.M("git_sites_auth").where(
        "site_id=?", (site_id,)
    ).getField("number_copies") or 5
    records = public.M("site_deploy_status").where(
        "site_id=?", (site_id,)
    ).order("id DESC").select() or []
    for record in records[int(number_copies):]:
        if int(record.get("deploy_status", 0) or 0) == 1:
            continue
        for field in ("script_path", "log_path"):
            path = record.get(field, "")
            if path and os.path.isfile(path):
                try:
                    os.remove(path)
                except OSError:
                    pass
        public.M("site_deploy_status").where("id=?", (record["id"],)).delete()


def _write_record(
    site, status, branch, operation_type, rollback_from_id,
    started_at, commit_info=None, error_message="", log_lines=None
):
    commit_info = dict(commit_info or {})
    deploy_time = datetime.fromtimestamp(started_at).strftime(
        "%Y-%m-%d %H:%M:%S"
    )
    log_file = os.path.join(
        "/www/wwwlogs",
        "{}_{}_git_deploy.log".format(site["name"], uuid.uuid4().hex[:12]),
    )
    os.makedirs(os.path.dirname(log_file), mode=0o755, exist_ok=True)
    public.writeFile(log_file, "\n".join(log_lines or []) + "\n")
    record_id = public.M("site_deploy_status").add(
        "site_id,status,deploy_status,script_path,log_path,deployment_time,"
        "execut_time,commit_hash,commit_hash_short,msg,author_name,"
        "committed_time,branch,operation_type,rollback_from_id,error_message",
        (
            site["id"], status, 0, "", log_file,
            deploy_time, round(time.time() - started_at, 2),
            commit_info.get("commit_hash", ""),
            commit_info.get("commit_hash_short", ""),
            commit_info.get("message", ""),
            commit_info.get("author_name", ""),
            commit_info.get("committed_time", ""),
            branch, operation_type, int(rollback_from_id or 0), error_message,
        ),
    )
    if not isinstance(record_id, int):
        raise ValueError("Failed to save the Git deployment record")
    if status == 1:
        active_result = public.M("site_deploy_status").execute(
            "UPDATE site_deploy_status "
            "SET deploy_status=CASE WHEN id=? THEN 1 ELSE 0 END "
            "WHERE site_id=?",
            (record_id, site["id"]),
        )
        if not isinstance(active_result, int):
            public.M("site_deploy_status").where(
                "id=?", (record_id,)
            ).delete()
            raise ValueError("Failed to activate the Git deployment record")
    try:
        _prune_records(site["id"])
    except Exception:
        pass
    return record_id


def _configure_repository(self, site_path, config):
    safe_env = os.environ.copy()
    safe_env["HOME"] = "/root"
    subprocess.run(
        ["git", "config", "--global", "--add", "safe.directory", site_path],
        env=safe_env, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        text=True, timeout=30, check=True,
    )
    if config["auth_type"] == "ssh_key":
        ssh_command = (
            "ssh -i {} -o IdentitiesOnly=yes -o BatchMode=yes "
            "-o StrictHostKeyChecking=accept-new "
            "-o UserKnownHostsFile=/root/.ssh/known_hosts"
        ).format(shlex.quote(config["key_path"]))
        _run(
            ["config", "core.sshCommand", ssh_command],
            config, cwd=site_path,
        )
    else:
        _run(
            ["config", "--unset-all", "core.sshCommand"],
            config, cwd=site_path, check=False,
        )


def _remove_site_tree(path):
    if not path or not os.path.exists(path):
        return
    user_ini = os.path.join(path, ".user.ini")
    chattr = shutil.which("chattr")
    if chattr and os.path.isfile(user_ini):
        subprocess.run(
            [chattr, "-i", user_ini],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            text=True, timeout=15, check=False,
        )
    shutil.rmtree(path)


def _deploy_revision(
    self, site_id, branch, commit_hash="", operation_type="git_latest",
    rollback_from_id=0, config_override=None, preserve_existing=False
):
    started_at = time.time()
    site = public.M("sites").where("id=?", (int(site_id),)).find()
    if not site:
        raise ValueError("The website does not exist")
    site_path = os.path.realpath(str(site.get("path", "") or ""))
    if not site_path or site_path in ("/", "/www", "/www/wwwroot"):
        raise ValueError("The website path is invalid")
    config = config_override or _site_config(site_id)[0]
    old_branch = public.M("git_sites_auth").where(
        "site_id=?", (site_id,)
    ).getField("branch") or ""
    branch = str(branch or config.get("branch", "")).strip()
    if not branch:
        raise ValueError("Git branch is required")
    parent_dir = os.path.dirname(site_path)
    os.makedirs(parent_dir, exist_ok=True)
    temporary_root = backup_path = ""
    directory_swapped = False
    commit_info = {}
    log_lines = [
        "=============Git Deployment START==============",
        "site: {}".format(site.get("name", "")),
        "path: {}".format(site_path),
        "branch: {}".format(branch),
        "operation: {}".format(operation_type),
    ]
    try:
        with _deploy_lock(site_id):
            temporary_root = tempfile.mkdtemp(
                prefix=".aapanel_git_deploy_", dir=parent_dir
            )
            shallow = not commit_hash
            # 克隆项目
            target_path = _clone(config, branch, temporary_root, shallow)
            full_commit = _resolve(
                target_path, config, branch, commit_hash
            )
            _run(["checkout", "--detach", full_commit], config, cwd=target_path)
            _run(["reset", "--hard", full_commit], config, cwd=target_path)
            commit_info = _commit_info(target_path, config, full_commit)
            log_lines.append("commit: {}".format(full_commit))
            backup_path = "{}.aapanel_git_backup_{}".format(
                site_path, uuid.uuid4().hex[:12]
            )
            # 重命名网站目录为备份
            if os.path.exists(site_path):
                os.rename(site_path, backup_path)
            try:
                # 克隆项目重命名网站目录
                os.rename(target_path, site_path)
                directory_swapped = True
                old_user_ini = os.path.join(backup_path, ".user.ini")
                new_user_ini = os.path.join(site_path, ".user.ini")
                if os.path.isfile(old_user_ini):
                    chattr = shutil.which("chattr")
                    if chattr:
                        subprocess.run(
                            [chattr, "-i", old_user_ini],
                            stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                            text=True, timeout=15, check=False,
                        )
                    shutil.copy2(old_user_ini, new_user_ini)
                    if chattr:
                        subprocess.run(
                            [chattr, "+i", new_user_ini],
                            stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                            text=True, timeout=15, check=False,
                        )
                ignore_paths = _site_ignore_paths(site_id)
                # 把旧网站目录中需要保留的路径复制回新网站目录
                _restore_preserved_paths(backup_path, site_path, ignore_paths)
                # 保留已有文件：补充新代码没有的旧文件，同名以新代码为准
                if preserve_existing:
                    _restore_existing_files(backup_path, site_path)
                _configure_repository(self, site_path, config)
                # 修正权限 目录 755，文件 644
                self._fix_file_permission(site_path, ignore_paths)
            except Exception:
                raise
            log_lines.extend([
                "status: success",
                "=============Git Deployment END================",
            ])
            public.M("git_sites_auth").where(
                "site_id=?", (site_id,)
            ).setField("branch", branch)
            deploy_id = _write_record(
                site, 1, branch, operation_type, rollback_from_id,
                started_at, commit_info, "", log_lines,
            )
            if backup_path and os.path.exists(backup_path):
                shutil.rmtree(backup_path, ignore_errors=True)
            backup_path = ""
            self._project_restart(site_id)
            return {
                "deploy_id": deploy_id, "site_id": int(site_id),
                "branch": branch,
                "commit_hash": commit_info["commit_hash"],
                "commit_hash_short": commit_info["commit_hash_short"],
                "operation_type": operation_type, "status": 1,
                "execut_time": round(time.time() - started_at, 2),
            }
    except Exception as exc:
        error_message = _redact(str(exc), config)
        if backup_path and os.path.exists(backup_path):
            if os.path.exists(site_path):
                _remove_site_tree(site_path)
            os.rename(backup_path, site_path)
            restored_user_ini = os.path.join(site_path, ".user.ini")
            chattr = shutil.which("chattr")
            if chattr and os.path.isfile(restored_user_ini):
                subprocess.run(
                    [chattr, "+i", restored_user_ini],
                    stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                    text=True, timeout=15, check=False,
                )
        elif directory_swapped and os.path.exists(site_path):
            _remove_site_tree(site_path)
        public.M("git_sites_auth").where(
            "site_id=?", (site_id,)
        ).setField("branch", old_branch)
        log_lines.extend([
            "status: failed", "error: {}".format(error_message),
            "=============Git Deployment END================",
        ])
        try:
            _write_record(
                site, 0, branch, operation_type, rollback_from_id,
                started_at, commit_info, error_message, log_lines,
            )
        except Exception:
            pass
        raise ValueError(error_message)
    finally:
        if temporary_root:
            shutil.rmtree(temporary_root, ignore_errors=True)


def _deploy_merge(
    self, site_id, branch, commit_hash="", operation_type="git_latest",
    config_override=None,
):
    """克隆到临时目录后合并进网站目录
    - 不删除网站目录已有文件（同名以新代码为准）,合并失败不影响原有文件
    - 跳过 ignore_paths（本地配置/可写目录）与 .user.ini
    """
    started_at = time.time()
    site = public.M("sites").where("id=?", (int(site_id),)).find()
    if not site:
        raise ValueError("The website does not exist")
    site_path = os.path.realpath(str(site.get("path", "") or ""))
    if not site_path or site_path in ("/", "/www", "/www/wwwroot"):
        raise ValueError("The website path is invalid")
    config = config_override or _site_config(site_id)[0]
    branch = str(branch or config.get("branch", "")).strip()
    if not branch:
        raise ValueError("Git branch is required")
    commit_hash = str(commit_hash or "").strip()
    parent_dir = os.path.dirname(site_path)
    os.makedirs(parent_dir, exist_ok=True)
    temporary_root = ""
    commit_info = {}
    log_lines = [
        "=============Git Deployment START==============",
        "site: {}".format(site.get("name", "")),
        "path: {}".format(site_path),
        "branch: {}".format(branch),
        "operation: {}".format(operation_type),
    ]
    try:
        with _deploy_lock(site_id):
            temporary_root = tempfile.mkdtemp(
                prefix=".aapanel_git_deploy_", dir=parent_dir
            )
            shallow = not commit_hash
            target_path = _clone(config, branch, temporary_root, shallow)
            full_commit = _resolve(
                target_path, config, branch, commit_hash
            )
            _run(["checkout", "--detach", full_commit], config, cwd=target_path)
            _run(["reset", "--hard", full_commit], config, cwd=target_path)
            commit_info = _commit_info(target_path, config, full_commit)
            log_lines.append("commit: {}".format(full_commit))
            ignore_paths = _site_ignore_paths(site_id)
            # 合并进网站目录：覆盖同名/新增，保留用户已有文件与忽略路径
            _merge_tree(target_path, site_path, ignore_paths)
            # 网站目录原本不是 git 仓库时注入 .git，后续可原地拉取部署
            if not os.path.isdir(os.path.join(site_path, ".git")):
                shutil.copytree(
                    os.path.join(target_path, ".git"),
                    os.path.join(site_path, ".git"),
                )
            _configure_repository(self, site_path, config)
            # 修正权限 目录 755 文件 644，忽略路径可写，统一 www:www
            self._fix_file_permission(site_path, ignore_paths)
            log_lines.extend([
                "status: success",
                "=============Git Deployment END================",
            ])
            public.M("git_sites_auth").where(
                "site_id=?", (site_id,)
            ).setField("branch", branch)
            deploy_id = _write_record(
                site, 1, branch, operation_type, 0,
                started_at, commit_info, "", log_lines,
            )
            self._project_restart(site_id)
            return {
                "deploy_id": deploy_id, "site_id": int(site_id),
                "branch": branch,
                "commit_hash": commit_info["commit_hash"],
                "commit_hash_short": commit_info["commit_hash_short"],
                "operation_type": operation_type, "status": 1,
                "execut_time": round(time.time() - started_at, 2),
            }
    except Exception as exc:
        error_message = _redact(str(exc), config)
        log_lines.extend([
            "status: failed", "error: {}".format(error_message),
            "=============Git Deployment END================",
        ])
        try:
            _write_record(
                site, 0, branch, operation_type, 0,
                started_at, commit_info, error_message, log_lines,
            )
        except Exception:
            pass
        raise ValueError(error_message)
    finally:
        if temporary_root:
            shutil.rmtree(temporary_root, ignore_errors=True)


def _simple_deploy(self, site_id, branch, commit_hash, operation_type):
    """
    旧版拉取部署：直接在网站目录内原地拉取，不做全量目录替换。
    网站目录需已是 Git 仓库
    """
    started_at = time.time()
    site = public.M("sites").where("id=?", (int(site_id),)).find()
    if not site:
        raise ValueError("The website does not exist")
    site_path = os.path.realpath(str(site.get("path", "") or ""))
    if not site_path or site_path in ("/", "/www", "/www/wwwroot"):
        raise ValueError("The website path is invalid")
    config = _site_config(site_id)[0]
    branch = str(branch or config.get("branch", "")).strip()
    if not branch:
        raise ValueError("Git branch is required")
    if not os.path.isdir(os.path.join(site_path, ".git")):
        raise ValueError(
            "The website directory is not a Git repository, "
            "please deploy with overwrite_pull=1 first"
        )
    commit_hash = str(commit_hash or "").strip()
    log_lines = [
        "=============Git Deployment START==============",
        "site: {}".format(site.get("name", "")),
        "path: {}".format(site_path),
        "branch: {}".format(branch),
        "operation: {}".format(operation_type),
    ]
    try:
        with _deploy_lock(site_id):
            if commit_hash:
                _run(
                    ["fetch", "origin", branch, "--prune"],
                    config, cwd=site_path, timeout=300,
                )
                # 浅克隆只含分支最新提交，回滚到历史提交会报
                # "reference is not a tree"；先拉全历史再 checkout。
                shallow_code, shallow_out, _ = _run(
                    ["rev-parse", "--is-shallow-repository"],
                    config, cwd=site_path, check=False,
                )
                if shallow_code == 0 and shallow_out.strip() == "true":
                    _run(
                        ["fetch", "--unshallow", "origin"],
                        config, cwd=site_path, timeout=600,
                    )
                _run(
                    ["checkout", "--detach", commit_hash],
                    config, cwd=site_path,
                )
                _run(["reset", "--hard", commit_hash], config, cwd=site_path)
                full_commit = _resolve(
                    site_path, config, branch, commit_hash
                )
            else:
                # 确保回到本地分支再 pull，避免 detached HEAD 下 pull 失败
                _run(
                    ["checkout", branch],
                    config, cwd=site_path, timeout=120, check=False,
                )
                _run(
                    ["pull", "origin", branch],
                    config, cwd=site_path, timeout=300,
                )
                full_commit = _resolve(
                    site_path, config, branch, "",
                    "refs/remotes/origin/{}".format(branch),
                )
            commit_info = _commit_info(site_path, config, full_commit)
            log_lines.append("commit: {}".format(full_commit))
            self._fix_file_permission(site_path, _site_ignore_paths(site_id))
            log_lines.extend([
                "status: success",
                "=============Git Deployment END================",
            ])
            public.M("git_sites_auth").where(
                "site_id=?", (site_id,)
            ).setField("branch", branch)
            deploy_id = _write_record(
                site, 1, branch, operation_type, 0,
                started_at, commit_info, "", log_lines,
            )
            self._project_restart(site_id)
            return {
                "deploy_id": deploy_id, "site_id": int(site_id),
                "branch": branch,
                "commit_hash": commit_info["commit_hash"],
                "commit_hash_short": commit_info["commit_hash_short"],
                "operation_type": operation_type, "status": 1,
                "execut_time": round(time.time() - started_at, 2),
            }
    except Exception as exc:
        error_message = _redact(str(exc), config)
        log_lines.extend([
            "status: failed", "error: {}".format(error_message),
            "=============Git Deployment END================",
        ])
        try:
            _write_record(
                site, 0, branch, operation_type, 0,
                started_at, {}, error_message, log_lines,
            )
        except Exception:
            pass
        raise ValueError(error_message)


def deploy_git_code(self, get):
    try:
        site_id = int(get.get("site_id", 0) or 0)
        branch = str(get.get("branch", "")).strip()
        commit_hash = str(get.get("commit_hash", "")).strip()
        if not site_id or not branch:
            raise ValueError("site_id and branch are required")
        operation_type = "git_commit" if commit_hash else "git_latest"
        # overwrite_pull=1 走全量替换部署 旧文件整体替换, 默认走网站目录内简单原地拉取
        overwrite_pull = str(get.get("overwrite_pull", "0") or "0").strip().lower()
        if overwrite_pull in ("1", "true", "yes"):
            result = _deploy_revision(self, site_id, branch, commit_hash, operation_type)
        else:
            result = _simple_deploy(self, site_id, branch, commit_hash, operation_type)
        result["message"] = "Git code deployed successfully"
        public.set_module_logs("Git-Tools", "deploy_git_code")
        return public.return_message(0, 0, result)
    except Exception as exc:
        return public.return_message(-1, 0, str(exc))


def _save_binding(site_id, config):
    is_github = bool(config.get("_github_auth"))
    db_auth = "github" if is_github else _auth_db(config["auth_type"])
    store_token = config["auth_type"] == "token" and not is_github
    public.M("git_sites_auth").add(
        "site_id,repo,branch,auth_type,key_path,username,"
        "oauth_access_token,oauth_token_type",
        (
            site_id, config["repo"], config.get("branch", ""),
            db_auth, config.get("key_path", ""),
            config.get("username", ""),
            encrypt_git_token(config.get("token", "")) if store_token else "",
            "aes" if store_token else "",
        ),
    )


def connect_repository(self, get):
    """
    连接仓库并首次部署  有网站 无.git
    """
    site_id = 0
    binding_created = False
    try:
        site_id = int(get.get("site_id", 0) or 0)
        branch = str(get.get("branch", "")).strip()
        if not site_id or not branch:
            raise ValueError("site_id and branch are required")
        if public.M("git_sites_auth").where(
            "site_id=?", (site_id,)
        ).count():
            raise ValueError(
                "The current website already has git repository records"
            )
        config = _normalize(_request_data(get))
        config["branch"] = branch
        _, branches = _remote_refs(config)
        if branch not in branches:
            raise ValueError("The selected remote branch does not exist")
        _save_binding(site_id, config)
        binding_created = True

        # 默认合并式部署
        overwrite_pull = str(get.get("overwrite_pull", "0") or "0").strip().lower()
        if overwrite_pull in ("1", "true", "yes"):
            # 全量替换: overwrite_pull=1 旧文件整体替换，仅保留忽略路径；
            result = _deploy_revision(
                self, site_id, branch, "", "git_latest",
                config_override=config,
            )
        else:
            # 合并式部署: 克隆到临时目录合并进网站目录，不删除用户已有文件
            result = _deploy_merge(
                self, site_id, branch, "", "git_latest",
                config_override=config,
            )
        result["message"] = "Repository connected and deployed successfully"
        public.set_module_logs("Git-Tools", "connect_repository")
        return public.return_message(0, 0, result)
    except Exception as exc:
        if binding_created:
            public.M("git_sites_auth").where(
                "site_id=?", (site_id,)
            ).delete()
        return public.return_message(-1, 0, str(exc))


def import_existing_repository(self, get):
    """网站目录已有 .git 仓库时绑定 git 管理器,支持 public/ssh_key/token 三种鉴权。

    传参  site_id/repo 必传  branch为空为默认分支
    - public:   传 site_id/repo  auth_type=public
    - ssh_key:  传 key_path auth_type=ssh_key ,仓库须为 SSH 地址
    - token:    传 auth_type=token  username + token
    """
    try:

        site_id = int(get.get("site_id", 0) or 0)
        if not site_id:
            raise ValueError("site_id is required")
        data = _request_data(get)
        config = _normalize(data)
        branch = str(config.get("branch", "") or "").strip()

        site_path = public.M("sites").where("id=?", (site_id,)).getField("path")
        if not site_path or not os.path.isdir(os.path.join(site_path, ".git")):
            raise ValueError("This directory is not a valid Git repository (the .git file was not found)")
        if public.M("git_sites_auth").where("site_id=?", (site_id,)).count():
            raise ValueError("This website already has Git records. Please do not add them again.")

        # 测试连接并拉取远端分支 支持三种鉴权
        default_branch, branches = _remote_refs(config)
        if not branch:
            branch = default_branch
        config["branch"] = branch
        if branches and branch and branch not in branches:
            raise ValueError("The selected remote branch does not exist")

        # 绑定前对网站仓库做安全与权限处理 复用v1方法
        self._add_safe_directory(site_path)
        if config["auth_type"] == "ssh_key":
            self._auto_configure_repo(site_path, config["key_path"])
        self._fix_file_permission(site_path)

        _save_binding(site_id, config)

        project_type = str(data.get("project_type", "") or "").strip()
        if project_type in ("node", "go", "python"):
            public.set_module_logs("Git-Tools", "{}_git_create_website".format(project_type))
        else:
            public.set_module_logs("Git-Tools", "import_existing_repository")

        public.set_module_logs("Git-Tools", "git_create_website")
        return public.return_message(0, 0, public.lang("The repository was successfully added!"))
    except Exception as exc:
        return public.return_message(-1, 0, str(exc))


def git_rollback(self, get):
    try:
        deploy_id = int(get.get("deploy_id", 0) or 0)
        record = public.M("site_deploy_status").where(
            "id=?", (deploy_id,)
        ).find()
        if not record:
            raise ValueError("The deployment record does not exist")
        if not record.get("branch") or not record.get("commit_hash"):
            raise ValueError("No commit record found for rollback")
        result = _deploy_revision(
            self, record["site_id"], record["branch"],
            record["commit_hash"], "rollback",
            rollback_from_id=record["id"],
        )
        result["rollback_from_id"] = record["id"]
        result["message"] = "Rollback completed successfully"
        public.set_module_logs("Git-Tools", "git_rollback")
        return public.return_message(0, 0, result)
    except Exception as exc:
        return public.return_message(-1, 0, str(exc))


def _find_webhook(site_name):
    try:
        from plugin.webhook.webhook_main import webhook_main
        for hook in webhook_main().GetList(None):
            if hook.get("title") == "{}_git_hook".format(site_name):
                return hook
    except Exception:
        pass
    return None


def _webhook_info(self, site):
    script_id = public.M("site_deploy_script").where(
        "site_id=? and is_webhook=1", (site["id"],)
    ).getField("id") or ""
    hook = _find_webhook(site["name"])
    if not hook:
        # 首次访问时自动创建 hook，保持旧版 get_site_git_conf 默认返回 webhook_url 的语义
        try:
            self._set_webhook(site["name"], site["id"])
        except Exception:
            pass
        hook = _find_webhook(site["name"])
    webhook_url = ""
    if hook:
        webhook_url = "{}/hook?access_key={}&site_id={}".format(
            public.getPanelAddr(), hook.get("access_key", ""),
            site["id"],
        )
    return script_id, webhook_url


def get_site_git_conf(self, get):
    """
    获取网站git配置  branch以网站实际分支为准
    """
    try:
        site_id = int(get.get("site_id", 0) or 0)
        site = public.M("sites").where("id=?", (site_id,)).find()
        site_git = public.M("git_sites_auth").where(
            "site_id=?", (site_id,)
        ).find()
        if not site_git:
            return public.return_message(0, 0, {})
        script_id, webhook_url = _webhook_info(self, site)
        webhook_script_name = ""
        if script_id:
            webhook_script_name = public.M("site_deploy_script").where(
                "id=?", (script_id,)
            ).getField("title") or ""
        auth_type = _auth_api(site_git.get("auth_type"))
        key_path = (
            site_git.get("key_path", "") if auth_type == "ssh_key" else ""
        )
        ssh_key = str(
            public.readFile(key_path + ".pub") or ""
        ).strip() if key_path else ""
        latest_record = public.M("site_deploy_status").where(
            "site_id=?", (site_id,)
        ).order("id DESC").find()
        # branch以网站目录HEAD实际分支为准
        branch = str(site_git.get("branch", "") or "")
        site_path = str(site.get("path", "") or "") if site else ""
        actual_branch = _current_branch(self, site_path) if site_path else ""

        if actual_branch and actual_branch != branch:
            branch = actual_branch
            public.M("git_sites_auth").where(
                "site_id=?", (site_id,)
            ).setField("branch", actual_branch)

        return public.return_message(0, 0, {
            "site_id": site_id, "deploy_id": site_git.get("id"),
            "repo": site_git.get("repo", ""),
            "branch": branch,
            "auth_type": auth_type,
            "deploy_type": site_git.get("auth_type", ""),
            "username": site_git.get("username", "")
            if auth_type == "token" else "",
            "token_configured": bool(site_git.get("oauth_access_token"))
            if auth_type == "token" else False,
            "key_path": key_path, "ssh_key": ssh_key,
            "number_copies": site_git.get("number_copies", 5),
            "ignore_paths": _site_ignore_paths(site_id),
            "webhook_enabled": bool(script_id),
            "webhook_url": webhook_url,
            "webhook_script": script_id,
            "webhook_script_name": webhook_script_name,
            "latest_deploy": latest_record or None,
        })
    except Exception as exc:
        return public.return_message(-1, 0, str(exc))


def _bind_webhook(self, site, script_id):
    try:
        from plugin.webhook.webhook_main import webhook_main
        webhook_obj = webhook_main()
        hook = next(
            (
                item for item in webhook_obj.GetList(None)
                if item.get("title") == "{}_git_hook".format(site["name"])
            ),
            None,
        )
        if script_id and not hook:
            self._set_webhook(site["name"], site["id"])
            hook = next(
                (
                    item for item in webhook_obj.GetList(None)
                    if item.get("title") == "{}_git_hook".format(site["name"])
                ),
                None,
            )
        if not script_id:
            public.M("site_deploy_script").where(
                "site_id=?", (site["id"],)
            ).setField("is_webhook", 0)
            if hook:
                webhook_path = os.path.join(
                    "/www/server/panel/plugin/webhook/script",
                    hook.get("access_key", ""),
                )
                if os.path.isfile(webhook_path):
                    public.writeFile(webhook_path, "#!/bin/bash\n")
            return
        script = public.M("site_deploy_script").where(
            "id=? and site_id=?", (script_id, site["id"])
        ).find()
        if not script:
            raise ValueError("The script does not exist")
        if not hook:
            raise ValueError(
                "The webhook configuration file of this website does not exist"
            )
        webhook_path = os.path.join(
            "/www/server/panel/plugin/webhook/script",
            hook.get("access_key", ""),
        )
        public.writeFile(webhook_path, "bash {}".format(script["script_path"]))
        public.M("site_deploy_script").where(
            "site_id=?", (site["id"],)
        ).setField("is_webhook", 0)
        public.M("site_deploy_script").where(
            "id=?", (script_id,)
        ).setField("is_webhook", 1)
    except ImportError:
        if script_id:
            raise ValueError("The webhook plugin is not installed")


def save_site_git_conf(self, get):
    try:
        site_id = int(get.get("site_id", 0) or 0)
        site = public.M("sites").where("id=?", (site_id,)).find()
        stored = public.M("git_sites_auth").where(
            "site_id=?", (site_id,)
        ).find()
        if not site or not stored:
            raise ValueError("This website does not have a Git repository")
        config_fields = (
            "repo", "repo_url", "auth_type", "branch",
            "key_path", "username", "token",
        )
        request_data = _request_data(get)
        if any(key in request_data for key in config_fields):
            config = _normalize(request_data, stored)
            default_branch, branches = _remote_refs(config)
            branch = config.get("branch") or default_branch
            if branch not in branches:
                raise ValueError("The selected remote branch does not exist")
            token_cipher = stored.get("oauth_access_token", "")
            if config["auth_type"] == "token" and config.get("token"):
                token_cipher = encrypt_git_token(config["token"])
            public.M("git_sites_auth").where(
                "site_id=?", (site_id,)
            ).update({
                "repo": config["repo"], "branch": branch,
                "auth_type": _auth_db(config["auth_type"]),
                "key_path": config.get("key_path", ""),
                "username": config.get("username", ""),
                "oauth_access_token": token_cipher
                if config["auth_type"] == "token" else "",
                "oauth_token_type": "aes"
                if config["auth_type"] == "token" else "",
            })
        if _has_field(get, "ignore_paths"):
            ignore_paths = request_data.get("ignore_paths", [])
            # 如果是JSON 字符串 例 '["/.env", "/storage"]'  先解析
            if isinstance(ignore_paths, str):
                try:
                    parsed = json.loads(ignore_paths)
                except (ValueError, TypeError):
                    raise ValueError(
                        "ignore_paths must be a list of path strings"
                    )
                if not isinstance(parsed, list):
                    raise ValueError(
                        "ignore_paths must be a list of path strings"
                    )
                ignore_paths = parsed
            elif not isinstance(ignore_paths, list):
                raise ValueError(
                    "ignore_paths must be a list of path strings"
                )
            cleaned = []
            for item in ignore_paths:
                item = str(item or "").strip()
                if item and item not in (".", ".."):
                    cleaned.append(item)
            public.M("git_sites_auth").where(
                "site_id=?", (site_id,)
            ).setField("ignore_paths", json.dumps(cleaned))
        if _has_field(get, "number_copies"):
            number_copies = int(get.get("number_copies", 5) or 5)
            import PluginLoader
            if PluginLoader.get_auth_state() < 1 and number_copies != 5:
                raise ValueError(
                    "Sorry. Free version users are only supported to save "
                    "5 deployment records."
                )
            public.M("git_sites_auth").where(
                "site_id=?", (site_id,)
            ).setField("number_copies", number_copies)
            _prune_records(site_id)
        if _has_field(get, "script_id"):
            _bind_webhook(self, site, int(get.get("script_id", 0) or 0))
        public.set_module_logs("Git-Tools", "save_site_git_conf")
        return public.return_message(
            0, 0, public.lang("Saved successfully.")
        )
    except Exception as exc:
        return public.return_message(-1, 0, str(exc))


def get_deploy_records(self, get):
    try:
        site_id = int(get.get("site_id", 0) or 0)
        if not site_id:
            raise ValueError("site_id is required")
        records = public.M("site_deploy_status").where(
            "site_id=?", (site_id,)
        ).order("id DESC").select() or []
        branch = str(get.get("branch", "")).strip()
        status_filter = str(get.get("status", "")).strip()
        if branch:
            records = [
                item for item in records if item.get("branch", "") == branch
            ]
        if status_filter != "":
            records = [
                item for item in records
                if str(item.get("status", "")) == status_filter
            ]
        page = max(1, int(get.get("p", 1) or 1))
        limit = min(100, max(1, int(get.get("limit", 20) or 20)))
        total = len(records)
        records = records[(page - 1) * limit:page * limit]
        script_id = public.M("site_deploy_script").where(
            "site_id=? and is_webhook=1", (site_id,)
        ).getField("id") or ""

        return public.return_message(0, 0, {
            "auto_deploy": bool(script_id),
            "webhook_enabled": bool(script_id),
            "webhook_script": script_id,
            "records": records,
            "page": {"p": page, "limit": limit, "total": total},
        })
    except Exception as exc:
        return public.return_message(-1, 0, str(exc))


def manual_deploy_site(self, get):
    """脚本手动部署：执行站点绑定的部署脚本，记录 v2 格式（带 branch）部署记录。

    覆写旧版 git_tools.py 的同名方法：旧版写记录时 branch 为空且操作副本
    数量用 _del_deploy_record（有误删风险），导致 v2 get_deploy_records 按
    branch 过滤时看不到脚本部署记录、且记录总数不断减少。
    """
    try:
        site_id = int(get.get("site_id", 0) or 0)
        script_id = int(get.get("script_id", 0) or 0)
        if not site_id or not script_id:
            raise ValueError("site_id and script_id are required")
        site = public.M("sites").where("id=?", (site_id,)).find()
        site_git = public.M("git_sites_auth").where(
            "site_id=?", (site_id,)
        ).find()
        if not site_git or not site:
            raise ValueError(
                "This website does not have or has no git repository."
            )
        script = public.M("site_deploy_script").where(
            "id=?", (script_id,)
        ).find()
        if not script:
            raise ValueError("The script does not exist.")

        started_at = time.time()
        site_path = str(site.get("path", "") or "")
        branch = str(site_git.get("branch", "") or "").strip()
        if not branch:
            branch = _site_config(site_id)[0].get("branch", "") or "master"

        deploy_script = str(script.get("script_path", "") or "")
        if not os.path.exists(deploy_script):
            raise ValueError("The deployment script does not exist!")
        if not public.readFile(deploy_script.strip()):
            public.writeFile(
                deploy_script,
                "cd {}\n".format(site_path)
                + 'echo " 🚀 Application deployed! "',
            )

        deploy_time = datetime.fromtimestamp(started_at).strftime(
            "%Y-%m-%d %H:%M:%S"
        )
        log_lines = [
            "=============Deployment START==============",
            "time: {}".format(deploy_time),
            "site: {}".format(site.get("name", "")),
            "path: {}".format(site_path),
            "branch: {}".format(branch),
            "Git deployment script: {}".format(script.get("title", "")),
        ]

        result = public.ExecShell("bash {}".format(deploy_script))
        if result[0]:
            log_lines.append("-----STDOUT-----")
            log_lines.append(str(result[0]).strip())
        if result[1]:
            log_lines.append("-----STDERR-----")
            log_lines.append(str(result[1]).strip())

        ok = self._is_deploy_success(result[0], result[1])
        status = 1 if ok else 0

        # 修正权限
        self._fix_file_permission(site_path, _site_ignore_paths(site_id))

        # 当前提交信息（旧版 _get_now_info 为类方法，v2 继承直接可用）
        commit_info = self._get_now_info(site_path)
        if not commit_info:
            raise ValueError(
                "Failed to obtain the current submitted info. "
                "Please check if the repository is correct!"
            )
        commit_date = str(commit_info.get("commit_date", "") or "")
        try:
            parsed_time = datetime.strptime(
                commit_date, "%a %b %d %H:%M:%S %Y %z"
            )
            commit_date = parsed_time.strftime("%Y-%m-%d %H:%M:%S")
        except Exception:
            pass

        v2_commit_info = {
            "commit_hash": commit_info.get("hash", ""),
            "commit_hash_short": commit_info.get("short_hash", ""),
            "author_name": commit_info.get("author", ""),
            "committed_time": commit_date,
            "message": commit_info.get("message", ""),
        }
        log_lines.append("commit: {}".format(v2_commit_info["commit_hash"]))
        log_lines.append("=============Deployment END================")

        # 用 v2 _write_record 写入，自带 branch + 激活当前记录 + 副本修剪
        _write_record(
            site, status, branch, "manual_deploy", 0,
            started_at, v2_commit_info, "", log_lines,
        )
        self._project_restart(site_id)
        public.set_module_logs("Git-Tools", "manual_deploy_site")
        return public.return_message(
            0, 0,
            "Deployment successful: "
            "Please visit the deployment log for details!",
        )
    except Exception as exc:
        return public.return_message(-1, 0, str(exc))


def install(cls):
    methods = (
        get_remote_branches, get_remote_commits, get_commit_detail,
        deploy_git_code, connect_repository, git_rollback,
        get_site_git_conf, save_site_git_conf, get_deploy_records,
        manual_deploy_site, import_existing_repository,
    )
    for method in methods:
        setattr(cls, method.__name__, method)
    from git_github import (
        get_github_oauth_url, get_github_account,
        get_github_repos, disconnect_github, renew_github_token,
    )
    for method in (
        get_github_oauth_url, get_github_account,
        get_github_repos, disconnect_github, renew_github_token,
    ):
        setattr(cls, method.__name__, method)
