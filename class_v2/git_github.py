# coding: utf-8
"""GitHub account authorization and repository listing for the website Git manager.
"""

import json
import os
import secrets
import time
import urllib.error
import urllib.parse
import urllib.request

import public
from git_auth import decrypt_git_token, encrypt_git_token

GITHUB_API_BASE = "https://api.github.com"

# nonce 存文件（防 CSRF，官网原样带回）。
# SameSite=Lax 下浏览器不带面板 cookie，session 读不到，nonce 校验和登录检查都会失败。
GITHUB_NONCE_FILE = "/www/server/panel/data/github_oauth_nonce"


def _official_base():
    """官网地址"""
    return str(public.OfficialApiBase() or "").rstrip("/")


def _github_row():
    return public.M("github_oauth").order("id DESC").find()


def _github_access_token():
    """返回 (access_token, row)；账号未连接时抛 ValueError。"""
    row = _github_row()
    if not row or not row.get("access_token"):
        raise ValueError("GitHub account is not connected")
    try:
        token = decrypt_git_token(row["access_token"])
    except Exception:
        raise ValueError("The saved GitHub access token cannot be decrypted")
    if not token:
        raise ValueError("GitHub account is not connected")
    return token, row


def _github_expiry(row):
    """判断 access_token 是否过期。

    返回 (expired, expires_at)。expires_in 为空（GitHub 未开启 token 过期）视为
    长期不过期；expires_at 为过期时间戳（秒），无法判断时返回 None。
    """
    expires_in = str(row.get("expires_in", "") or "").strip()
    updated_at = str(row.get("updated_at", "") or "").strip()
    if not expires_in or not updated_at:
        return False, None
    try:
        updated_ts = int(time.mktime(time.strptime(updated_at, "%Y-%m-%d %H:%M:%S")))
        expires_at = updated_ts + int(expires_in)
        return time.time() > expires_at, expires_at
    except Exception:
        return False, None


def _refresh_via_official(grant_id, grant_secret):
    """用 grant_id + grant_secret 调官网 POST /github/panel/token 换新短时 access_token。

    grant_secret 为明文（官网用库里的 refresh_token 向 GitHub 轮转，不回传 refresh_token）。
    返回 (access_token, token_type, scope, expires_in)；失败抛 ValueError。
    """
    url = "{}/github/panel/token".format(_official_base())
    payload = json.dumps({
        "grant_id": grant_id,
        "grant_secret": grant_secret,
    }).encode("utf-8")
    request = urllib.request.Request(url, data=payload, method="POST")
    request.add_header("Content-Type", "application/json")
    request.add_header("User-Agent", "aaPanel")
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            data = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        body = ""
        try:
            body = exc.read().decode("utf-8")[:2000]
        except Exception:
            pass
        raise ValueError("GitHub token renew failed: {}".format(body or str(exc)))
    except urllib.error.URLError as exc:
        raise ValueError("GitHub token renew request failed: {}".format(exc))

    if not isinstance(data, dict):
        raise ValueError("GitHub token renew failed: invalid response")
    # 官网业务错误：refresh_unavailable（无 refresh_token，需重新授权）/ invalid_grant
    if data.get("error"):
        raise ValueError("GitHub token renew failed: {}".format(data.get("error")))
    access_token = str(data.get("access_token", "") or "").strip()
    if not access_token:
        raise ValueError("GitHub token renew failed: no access_token in response")
    return (
        access_token,
        str(data.get("token_type", "") or "").strip(),
        str(data.get("scope", "") or "").strip(),
        str(data.get("expires_in", "") or "").strip(),
    )


def _renew_github_token():
    """用落库的 grant_id + grant_secret 向官网续期并回写 access_token。

    返回续期后的信息 dict；未连接 / 无 grant 凭证时抛 ValueError。
    """
    row = _github_row()
    if not row or not row.get("access_token"):
        raise ValueError("GitHub account is not connected")
    grant_id = str(row.get("grant_id", "") or "").strip()
    encrypted_secret = str(row.get("grant_secret", "") or "").strip()
    if not grant_id or not encrypted_secret:
        raise ValueError("No grant credential saved, please re-authorize")
    try:
        grant_secret = decrypt_git_token(encrypted_secret)
    except Exception:
        raise ValueError("The saved grant_secret cannot be decrypted")
    if not grant_secret:
        raise ValueError("No grant credential saved, please re-authorize")

    access_token, token_type, scope, expires_in = _refresh_via_official(
        grant_id, grant_secret,
    )

    encrypted_token = encrypt_git_token(access_token)
    now = public.getDate()
    update_fields = {
        "access_token": encrypted_token,
        "updated_at": now,
    }
    if token_type:
        update_fields["token_type"] = token_type
    if scope:
        update_fields["scope"] = scope
    if expires_in:
        update_fields["expires_in"] = expires_in
    public.M("github_oauth").where("id=?", (row["id"],)).update(update_fields)
    return {
        "login": row.get("login", ""),
        "renewed_at": now,
        "expires_in": expires_in or row.get("expires_in", ""),
        "expired": False,
    }


def resolve_github_credentials():
    """返回 (login, access_token) 供 clone/查询复用 token 鉴权；未连接时抛 ValueError。"""
    token, row = _github_access_token()
    return row.get("login", "") or "", token


def get_github_info():
    """返回 GitHub 账号授权状态，供设置页等非 /git 场景展示连接状态与解绑入口复用。
    """
    try:
        row = _github_row()
        if not isinstance(row, dict) or not row.get("access_token"):
            return {"connected": False}
        expired, expires_at = _github_expiry(row)
        return {
            "connected": True,
            "login": row.get("login", "") or "",
            "avatar_url": row.get("avatar_url", "") or "",
            "scope": row.get("scope", "") or "",
            "expired": expired,
            "renewed_at": row.get("updated_at", "") or "",
            "expires_in": row.get("expires_in", "") or "",
            "expires_at": expires_at,
        }
    except Exception:
        return {"connected": False}


def _github_api_request(path, token):
    url = GITHUB_API_BASE + path
    request = urllib.request.Request(url)
    request.add_header("Authorization", "Bearer {}".format(token))
    request.add_header("Accept", "application/vnd.github+json")
    request.add_header("User-Agent", "aaPanel")
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        body = ""
        try:
            body = exc.read().decode("utf-8")[:2000]
        except Exception:
            pass
        raise ValueError(
            "GitHub API error {}: {}".format(exc.code, body or str(exc))
        )
    except urllib.error.URLError as exc:
        raise ValueError("GitHub API request failed: {}".format(exc))


def get_github_oauth_url(self, get):
    """生成官网 GitHub 授权跳转 URL，返回 {authorize_url}。

    前端拿到 authorize_url 后浏览器跳转；nonce 写文件供回调校验。
    """
    try:
        nonce = secrets.token_urlsafe(24)  # A-Za-z0-9_- ，最长 128
        public.writeFile(GITHUB_NONCE_FILE, nonce)
        panel_callback = "{}/github/oauth_callback".format(public.getPanelAddr())
        authorize_url = "{}/github/panel/authorize?panel_callback={}&nonce={}".format(
            _official_base(),
            urllib.parse.quote(panel_callback, safe=""),
            urllib.parse.quote(nonce, safe=""),
        )
        return public.return_message(0, 0, {"authorize_url": authorize_url})
    except Exception as exc:
        return public.return_message(-1, 0, str(exc))


def handle_github_callback(get):
    """处理官网 POST 表单回调（/github/oauth_callback 路由调用）。

    成功返回 (True, login)，失败抛 ValueError。
    """
    nonce = str(get.get("nonce", "") or "").strip()
    expected = str(public.readFile(GITHUB_NONCE_FILE) or "").strip()
    public.print_log(
        "[github_oauth] callback nonce_in={!r} expected={!r}".format(nonce, expected)
    )
    if expected:
        try:
            os.remove(GITHUB_NONCE_FILE)
        except Exception:
            pass
    if not expected or not nonce or nonce != expected:
        raise ValueError("Invalid OAuth nonce")

    # 官网透传的 GitHub 拒绝/错误
    error = str(get.get("error", "") or "").strip()
    if error:
        raise ValueError(
            "GitHub authorization failed: {} {}".format(
                error, str(get.get("error_description", "") or "").strip()
            )
        )

    access_token = str(get.get("access_token", "") or "").strip()
    grant_id = str(get.get("grant_id", "") or "").strip()
    grant_secret = str(get.get("grant_secret", "") or "").strip()
    token_type = str(get.get("token_type", "") or "").strip()
    scope = str(get.get("scope", "") or "").strip()
    expires_in = str(get.get("expires_in", "") or "").strip()
    public.print_log(
        "[github_oauth] callback fields access_token_len={} head={} token_type={!r} "
        "scope={!r} grant_id={!r} grant_secret_len={} expires_in={!r}".format(
            len(access_token), access_token[:6], token_type, scope, grant_id,
            len(grant_secret), expires_in,
        )
    )
    if not access_token:
        raise ValueError("Missing GitHub access token in callback")

    # 官网不回传 login，用 access_token 调 GitHub /user 补登
    login = ""
    avatar_url = ""
    try:
        user = _github_api_request("/user", access_token)
        login = str(user.get("login", "") or "")
        avatar_url = str(user.get("avatar_url", "") or "")
    except Exception:
        # 拿不到用户信息不阻断授权，后续 get_github_repos 可再补
        pass

    now = public.getDate()
    encrypted_token = encrypt_git_token(access_token)
    encrypted_secret = encrypt_git_token(grant_secret) if grant_secret else ""

    row = _github_row()
    if row:
        ret = public.M("github_oauth").where("id=?", (row["id"],)).update({
            "login": login,
            "access_token": encrypted_token,
            "token_type": token_type,
            "scope": scope,
            "avatar_url": avatar_url,
            "grant_id": grant_id,
            "grant_secret": encrypted_secret,
            "expires_in": expires_in,
            "updated_at": now,
        })
    else:
        ret = public.M("github_oauth").add(
            "login,access_token,token_type,scope,avatar_url,"
            "grant_id,grant_secret,expires_in,created_at,updated_at",
            (
                login, encrypted_token, token_type, scope, avatar_url,
                grant_id, encrypted_secret, expires_in, now, now,
            ),
        )
    public.print_log(
        "[github_oauth] callback saved login={!r} scope={!r} updated={} db_ret={!r}".format(
            login, scope, bool(row), ret
        )
    )
    return True, login


def get_github_account(self, get):
    try:
        row = _github_row()
        if not row or not row.get("access_token"):
            return public.return_message(0, 0, {"connected": False})
        expired, expires_at = _github_expiry(row)
        return public.return_message(0, 0, {
            "connected": True,
            "login": row.get("login", ""),
            "avatar_url": row.get("avatar_url", ""),
            "scope": row.get("scope", ""),
            "expired": expired,
            "renewed_at": row.get("updated_at", "") or "",
            "expires_in": row.get("expires_in", "") or "",
            "expires_at": expires_at,
        })
    except Exception as exc:
        public.print_log(public.get_error_info())
        return public.return_message(-1, 0, str(exc))


def renew_github_token(self, get):
    """手动续签 GitHub access_token（POST 官网 /github/panel/token）。"""
    try:
        info = _renew_github_token()
        return public.return_message(0, 0, public.lang("Reset successfully"))
    except Exception as exc:
        return public.return_message(-1, 0, str(exc))


def get_github_repos(self, get):
    try:
        token, _ = _github_access_token()
        repos = {}
        page = 1
        while page <= 10:
            items = _github_api_request(
                "/user/repos?per_page=100&page={}&sort=updated".format(page),
                token,
            )
            if not items:
                break
            for item in items:
                repos[item.get("full_name", "")] = item
            if len(items) < 100:
                break
            page += 1
        # 组织项目
        try:
            orgs = _github_api_request("/user/orgs?per_page=100", token)
            for org in orgs:
                org_login = org.get("login", "")
                if not org_login:
                    continue
                org_repos = _github_api_request(
                    "/orgs/{}/repos?per_page=100&sort=updated".format(
                        urllib.parse.quote(org_login, safe="")
                    ),
                    token,
                )
                for item in org_repos:
                    repos[item.get("full_name", "")] = item
        except Exception:
            pass
        result = []
        for item in repos.values():
            if not item.get("full_name"):
                continue
            owner = (item.get("owner") or {}).get("login", "")
            name = item.get("name", "")
            html_url = item.get("html_url", "")
            # 部署时用 https clone 地址走 token 鉴权
            clone_url = item.get("clone_url") or (
                "{}.git".format(html_url.rstrip("/")) if html_url else ""
            )
            result.append({
                "owner": owner,
                "name": name,
                "full_name": item.get("full_name", ""),
                "private": bool(item.get("private")),
                "default_branch": item.get("default_branch", ""),
                "clone_url": clone_url,
                "updated_at": item.get("updated_at", ""),
            })
        result.sort(key=lambda x: x["full_name"].lower())
        return public.return_message(0, 0, result)
    except Exception as exc:
        return public.return_message(-1, 0, str(exc))


def disconnect_github(self, get):
    try:
        public.M("github_oauth").execute("DELETE FROM github_oauth", ())
        try:
            os.remove(GITHUB_NONCE_FILE)
        except Exception:
            pass
        return public.return_message(0, 0, "Deleted successfully")
    except Exception as exc:
        return public.return_message(-1, 0, str(exc))
