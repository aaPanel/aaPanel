# coding: utf-8
# -------------------------------------------------------------------
# aaPanel
# -------------------------------------------------------------------

import os
import re
import json
import socket
import urllib.parse
from http.cookies import SimpleCookie

import requests
import urllib3
import urllib3.util.connection as urllib3_conn

from BTPanel import request, Response, public, app, session
from mod.project.mail.billionmailMod import main as BillionMailMod


class BillionMailProxy:
    HOP_BY_HOP_HEADERS = frozenset((
        "connection",
        "keep-alive",
        "proxy-authenticate",
        "proxy-authorization",
        "te",
        "trailers",
        "transfer-encoding",
        "upgrade",
        "content-length",
        "content-encoding",
    ))
    PANEL_COOKIES = (
        "bt_user_info",
        "file_recycle_status",
        "ltd_end",
        "memSize",
        "page_number",
        "pro_end",
        "request_token",
        "serverType",
        "site_model",
        "sites_path",
        "soft_remarks",
        "load_page",
        "Path",
        "distribution",
        "order",
    )

    def __init__(self, proxy_prefix="/billionmail"):
        self.proxy_prefix = "/" + proxy_prefix.strip("/")

    @staticmethod
    def _trace_api_feature(path_full):
        try:
            method = (request.method or "").upper()
            if method not in ("POST", "PUT", "PATCH", "DELETE"):
                return
            path = "/" + (path_full or "").strip("/")
            if not path.startswith("/api/"):
                return
            segs = [s.strip().lower() for s in path[len("/api/"):].split("/") if s]
            if not segs:
                return
            body = list(segs)
            if body[-1].isdigit() or len(body[-1]) > 32 or "-" in body[-1]:
                action = method.lower()
            else:
                action = body.pop()
            parts = [s for s in body if not (s.isdigit() or len(s) > 32 or "-" in s)]
            resource = "_".join(parts)
            if resource:
                fun_name = "api_{}-{}".format(resource, action)
            else:
                fun_name = "api_{}".format(action)
            public.set_module_logs("BillionMail", fun_name)
        except Exception:
            pass

    @staticmethod
    def _error(message, status=500):
        return Response(message, status=status)

    def _clean_cookie(self, cookie_header):
        if not cookie_header:
            return ""
        cookie_dict = SimpleCookie(cookie_header)
        remove_names = list(self.PANEL_COOKIES)
        session_cookie_name = app.config.get("SESSION_COOKIE_NAME")
        if session_cookie_name:
            remove_names.append(session_cookie_name)
        for cookie_name in remove_names:
            if cookie_name in cookie_dict:
                del cookie_dict[cookie_name]
        return cookie_dict.output(header="", sep=";").strip()

    def _request_headers(self, target_base):
        headers = {}
        target = urllib.parse.urlparse(target_base)
        panel_scheme = self._panel_scheme()
        for key in request.headers.keys():
            lower_key = key.lower()
            if lower_key in self.HOP_BY_HOP_HEADERS or lower_key in (
                "host",
                "forwarded",
                "x-forwarded-host",
                "x-forwarded-proto",
                "x-forwarded-scheme",
                "x-forwarded-ssl",
                "x-forwarded-prefix",
            ):
                continue
            value = request.headers.get(key)
            if lower_key == "cookie":
                value = self._clean_cookie(value)
                if not value:
                    continue
            elif lower_key == "origin":
                value = "{}://{}".format(target.scheme, target.netloc)
            elif lower_key == "referer":
                value = self._rewrite_request_referer(value, target_base)
            headers[key] = value

        headers["Accept-Encoding"] = "identity"
        headers["X-Forwarded-Host"] = request.host
        headers["X-Forwarded-Proto"] = panel_scheme
        headers["X-Forwarded-Scheme"] = panel_scheme
        headers["X-Forwarded-SSL"] = "on" if panel_scheme == "https" else "off"
        headers["X-Forwarded-Prefix"] = self.proxy_prefix
        headers["Forwarded"] = 'proto={};host="{}"'.format(panel_scheme, request.host)
        headers["X-Real-IP"] = request.headers.get("X-Real-IP", request.remote_addr or "")
        return headers

    def _rewrite_request_referer(self, value, target_base):
        if not value:
            return value
        try:
            parsed = urllib.parse.urlparse(value)
            path = parsed.path or "/"
            if path == self.proxy_prefix or path.startswith(self.proxy_prefix + "/"):
                new_path = path[len(self.proxy_prefix):] or "/"
                target = urllib.parse.urlparse(target_base)
                return urllib.parse.urlunparse((
                    target.scheme,
                    target.netloc,
                    new_path,
                    "",
                    parsed.query,
                    parsed.fragment,
                ))
        except Exception:
            pass
        return value

    def _target_url(self, target_base, path_full):
        path = "/" + (path_full or "").lstrip("/")
        path = urllib.parse.quote(path, safe="/:@!$&'()*+,;=-._~%")
        query = request.query_string.decode("latin-1")
        url = target_base.rstrip("/") + path
        if query:
            url += "?" + query
        return url

    def _request_kwargs(self, target_base):
        kwargs = {
            "headers": self._request_headers(target_base),
            "verify": False,
            "timeout": 300,
            "allow_redirects": False,
        }
        content_type = request.headers.get("Content-Type", "").lower()
        if content_type.startswith("multipart/form-data"):
            files = []
            for key in request.files:
                for storage in request.files.getlist(key):
                    files.append((
                        key,
                        (
                            storage.filename,
                            storage.stream,
                            storage.content_type,
                        ),
                    ))
            form = {}
            for key in request.form.keys():
                values = request.form.getlist(key)
                form[key] = values if len(values) > 1 else values[0]
            if files:
                kwargs["files"] = files
            kwargs["data"] = form
        else:
            body = request.get_data()
            if body:
                kwargs["data"] = body
        return kwargs

    def _rewrite_location(self, value, target_base):
        if not value:
            return value
        value = self._rewrite_panel_absolute_urls(value)
        target = urllib.parse.urlparse(target_base)
        parsed = urllib.parse.urlparse(value)
        if parsed.scheme and parsed.netloc:
            if parsed.hostname in ("127.0.0.1", "localhost", "::1") or parsed.netloc == target.netloc:
                path = parsed.path or "/"
                if path == self.proxy_prefix or path.startswith(self.proxy_prefix + "/"):
                    return path + (("?" + parsed.query) if parsed.query else "")
                return self.proxy_prefix + path + (("?" + parsed.query) if parsed.query else "")
            return value
        if value.startswith("/"):
            if value == self.proxy_prefix or value.startswith(self.proxy_prefix + "/"):
                return value
            return self.proxy_prefix + value
        return value

    def _rewrite_set_cookie(self, value):
        if not value:
            return value
        value = re.sub(r";\s*domain=(127\.0\.0\.1|localhost|\[?::1\]?)[^;]*", "", value, flags=re.I)
        if re.search(r";\s*path=", value, re.I):
            return re.sub(r";\s*path=[^;]*", "; Path={}".format(self.proxy_prefix), value, flags=re.I)
        return value + "; Path={}".format(self.proxy_prefix)

    def _response_headers(self, upstream_response, target_base):
        headers = []
        for key, value in upstream_response.headers.items():
            lower_key = key.lower()
            if lower_key in self.HOP_BY_HOP_HEADERS or lower_key == "set-cookie":
                continue
            if lower_key in ("x-frame-options", "content-security-policy"):
                continue
            if lower_key == "location":
                value = self._rewrite_location(value, target_base)
            headers.append((key, value))
        headers.append(("Referrer-Policy", "same-origin"))
        return headers

    def _set_cookie_headers(self, response, upstream_response):
        raw_headers = getattr(upstream_response.raw, "headers", None)
        cookies = []
        if raw_headers is not None:
            if hasattr(raw_headers, "get_all"):
                cookies = raw_headers.get_all("Set-Cookie") or []
            elif hasattr(raw_headers, "getlist"):
                cookies = raw_headers.getlist("Set-Cookie") or []
        if not cookies:
            cookie_header = upstream_response.headers.get("Set-Cookie")
            if cookie_header:
                cookies = [cookie_header]
        for cookie in cookies:
            response.headers.add("Set-Cookie", self._rewrite_set_cookie(cookie))
        return response

    def _safe_redirect(self, value):
        value = (value or "").strip()
        if not value or not value.startswith("/") or value.startswith("//"):
            return self.proxy_prefix + "/"
        if value == self.proxy_prefix or value.startswith(self.proxy_prefix + "/"):
            return value
        return self.proxy_prefix + (value if value != "/" else "/")

    def _sso_bridge(self):
        service_name = request.args.get("service_name", "")
        redirect = self._safe_redirect(request.args.get("redirect", ""))
        apsess_token = self._panel_apsess_token()
        panel_api_prefix = "/{}".format(apsess_token) if apsess_token else ""
        csrf_token = public.get_csrf_sess_html_token_value() or ""
        html = """<!doctype html>
<html>
<head>
  <meta charset="utf-8">
  <meta name="referrer" content="same-origin">
  <title>BillionMail</title>
  <style>
    html, body { height: 100%; margin: 0; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; }
    body { display: flex; align-items: center; justify-content: center; color: #1f2937; background: #f8fafc; }
    .box { text-align: center; font-size: 14px; line-height: 22px; }
    .err { color: #b91c1c; white-space: pre-wrap; max-width: 720px; padding: 24px; text-align: left; }
  </style>
</head>
<body>
  <div class="box" id="message">Signing in to BillionMail...</div>
  <script>
  (function () {
    var serviceName = __SERVICE_NAME__;
    var redirectUrl = __REDIRECT_URL__;
    var panelApiPrefix = __PANEL_API_PREFIX__;
    var csrfToken = __CSRF_TOKEN__;

    function getPanelApiPrefix() {
      if (panelApiPrefix) return panelApiPrefix;
      var match = window.location.pathname.match(/^\\/(apsess_[A-Za-z0-9]{16,32})(?:\\/|$)/);
      return match ? '/' + match[1] : '';
    }

    function fail(err) {
      var message = document.getElementById('message');
      message.className = 'err';
      message.textContent = 'BillionMail SSO failed:\\n' + (err && (err.message || err.responseText || String(err)));
    }

    function saveLogin(data) {
      var ttl = Number(data.ttl || 0);
      var login = {
        token: data.token || '',
        refresh_token: data.refreshToken || data.refresh_token || '',
        ttl: ttl,
        expire: Date.now() + ttl * 1000
      };
      if (!login.token) {
        throw new Error('SSO response does not contain token.');
      }

      var state = {};
      try {
        state = JSON.parse(localStorage.getItem('UserStore') || '{}') || {};
      } catch (e) {
        state = {};
      }
      state.login = login;
      localStorage.setItem('UserStore', JSON.stringify(state));
    }

    var body = new URLSearchParams();
    if (serviceName) body.set('service_name', serviceName);

    fetch(getPanelApiPrefix() + '/v2/mod/mail/billionmail/sso', {
      method: 'POST',
      credentials: 'include',
      headers: {'Content-Type': 'application/x-www-form-urlencoded', 'x-http-token': csrfToken},
      body: body
    }).then(function (res) {
      return res.json();
    }).then(function (res) {
      if (!res || res.status !== 0) {
        throw new Error(JSON.stringify(res && res.message ? res.message : res));
      }
      saveLogin(res.message || {});
      window.location.replace(redirectUrl);
    }).catch(fail);
  })();
  </script>
</body>
</html>"""
        html = html.replace("__SERVICE_NAME__", json.dumps(service_name))
        html = html.replace("__REDIRECT_URL__", json.dumps(redirect))
        html = html.replace("__PANEL_API_PREFIX__", json.dumps(panel_api_prefix))
        html = html.replace("__CSRF_TOKEN__", json.dumps(csrf_token))
        response = Response(html, content_type="text/html; charset=utf-8", status=200)
        response.headers["Cache-Control"] = "no-store"
        response.headers["Referrer-Policy"] = "same-origin"
        return response

    def _panel_apsess_token(self):
        token = request.environ.get("bt.apsess_token", "") or session.get("apsess_token", "")
        token = str(token or "").strip()
        while token.startswith("apsess_apsess_"):
            token = token[len("apsess_"):]
        if token and not token.startswith("apsess_"):
            token = "apsess_" + token
        if not re.match(r"^apsess_[A-Za-z0-9]{16,32}$", token):
            return ""
        return token

    def _is_text_response(self, upstream_response, path_full):
        content_type = (upstream_response.headers.get("content-type") or "").lower()
        path = (path_full or "").split("?", 1)[0].lower()
        if any(item in content_type for item in (
            "text/html",
            "text/css",
            "javascript",
            "application/json",
            "application/xml",
        )):
            return True
        return path.endswith((".html", ".htm", ".css", ".js", ".json", ".xml"))

    @staticmethod
    def _panel_ssl_enabled():
        try:
            if os.path.exists("/www/server/panel/data/ssl.pl"):
                return True
            panel_path = public.get_panel_path()
            if panel_path:
                return os.path.exists(os.path.join(panel_path, "ssl", "input.pl"))
        except Exception:
            pass
        return False

    def _panel_scheme(self):
        return "https" if self._panel_ssl_enabled() else "http"

    def _panel_origin_hosts(self):
        hosts = []
        values = (
            request.host,
            request.headers.get("Host", ""),
            request.headers.get("X-Forwarded-Host", ""),
            request.environ.get("HTTP_HOST", ""),
            request.environ.get("SERVER_NAME", ""),
        )
        for value in values:
            for host in str(value or "").split(","):
                host = host.strip()
                if host and host not in hosts:
                    hosts.append(host)

        server_name = str(request.environ.get("SERVER_NAME", "") or "").strip()
        server_port = str(request.environ.get("SERVER_PORT", "") or "").strip()
        if server_name and server_port and ":" not in server_name:
            host = "{}:{}".format(server_name, server_port)
            if host not in hosts:
                hosts.append(host)
        return hosts

    def _panel_proxy_prefixes(self):
        prefixes = []
        for prefix in (self.proxy_prefix.rstrip("/"), "/billionmail"):
            if prefix and prefix not in prefixes:
                prefixes.append(prefix)
        return prefixes

    def _rewrite_panel_absolute_urls(self, text):
        if not text:
            return text
        prefixes = self._panel_proxy_prefixes()
        if not prefixes:
            return text

        for host in self._panel_origin_hosts():
            host_re = re.escape(host)
            for proxy in prefixes:
                proxy_re = re.escape(proxy)
                escaped_proxy_re = proxy_re.replace("/", r"\\/")
                text = re.sub(
                    r"(?:https?:)?//" + host_re + r"(" + proxy_re + r"(?=/|[?#]|$))",
                    r"\1",
                    text,
                )
                text = re.sub(
                    r"(?:https?:)?\\\/\\\/" + host_re + r"(" + escaped_proxy_re + r"(?=\\\/|[?#]|$))",
                    r"\1",
                    text,
                )
        return text

    def _rewrite_csp_for_panel_scheme(self, text):
        if self._panel_scheme() != "http":
            return text

        def rewrite_meta(match):
            tag = match.group(0)
            content_match = re.search(r'(?is)(\bcontent\s*=\s*)(["\'])(.*?)\2', tag)
            if not content_match:
                return ""

            directives = []
            for directive in content_match.group(3).split(";"):
                directive = directive.strip()
                if directive and directive.lower() != "upgrade-insecure-requests":
                    directives.append(directive)
            if not directives:
                return ""

            start, end = content_match.span(3)
            return tag[:start] + "; ".join(directives) + tag[end:]

        return re.sub(
            r'(?is)<meta\b(?=[^>]*\bhttp-equiv\s*=\s*["\']?Content-Security-Policy["\']?)'
            r'(?=[^>]*\bcontent\s*=\s*["\'][^"\']*upgrade-insecure-requests[^"\']*["\'])[^>]*>',
            rewrite_meta,
            text,
        )

    def _rewrite_settings_system_config(self, text, path_full, config=None):
        path = (path_full or "").split("?", 1)[0].strip("/").lower()
        if path != "api/settings/get_system_config":
            return text

        try:
            body = json.loads(text)
        except Exception:
            return text

        data = body.get("data") if isinstance(body, dict) else None
        if not isinstance(data, dict):
            return text

        data.pop("manage_ports", None)
        data.pop("manage_timezone", None)

        return json.dumps(body, ensure_ascii=False, separators=(",", ":"))

    @staticmethod
    def _webmail_url(config):
        if not isinstance(config, dict):
            return ""
        webmail_url = str(config.get("webmail_url") or "").strip()
        if webmail_url:
            return webmail_url.rstrip("/")
        direct_console_url = str(config.get("direct_console_url") or "").strip()
        if not direct_console_url:
            return ""
        return direct_console_url.rstrip("/") + "/roundcube"

    def _rewrite_webmail_url(self, text, webmail_url):
        if not webmail_url:
            return text

        for scheme in ("http", "https"):
            panel_origin = "{}://{}".format(scheme, request.host).rstrip("/")
            text = text.replace(panel_origin + "/roundcube", webmail_url)
        text = text.replace("${location.origin}/roundcube", webmail_url)
        text = text.replace("${window.location.origin}/roundcube", webmail_url)

        webmail_literal = json.dumps(webmail_url)
        text = re.sub(
            r'(?:(?:window|globalThis)\.)?location\.origin\s*\+\s*(["\'])/roundcube\1',
            webmail_literal,
            text,
        )
        text = re.sub(
            r'(\.concat\(\s*)(?:(?:window|globalThis)\.)?location\.origin\s*,\s*(["\'])/roundcube\2',
            lambda match: match.group(1) + webmail_literal,
            text,
        )
        return text

    @staticmethod
    def _webmail_rewrite_script(webmail_url):
        return """<script>
(function () {
  var webmailUrl = __WEBMAIL_URL__;
  if (!webmailUrl) return;
  var panelRoundcube = window.location.origin.replace(/\\/$/, '') + '/roundcube';
  function rewrite(value) {
    if (typeof value !== 'string') return value;
    return value.split(panelRoundcube).join(webmailUrl);
  }
  window.__AAPANEL_BILLIONMAIL_WEBMAIL_URL__ = webmailUrl;
  try {
    if (navigator.clipboard && navigator.clipboard.writeText && !navigator.clipboard.__aapanelBillionMailPatched) {
      var rawWriteText = navigator.clipboard.writeText.bind(navigator.clipboard);
      navigator.clipboard.writeText = function (value) {
        return rawWriteText(rewrite(value));
      };
      navigator.clipboard.__aapanelBillionMailPatched = true;
    }
  } catch (e) {}
  document.addEventListener('copy', function (event) {
    if (!event.clipboardData) return;
    var selection = String(window.getSelection ? window.getSelection() : '');
    var rewritten = rewrite(selection);
    if (rewritten !== selection) {
      event.clipboardData.setData('text/plain', rewritten);
      event.preventDefault();
    }
  }, true);
})();
</script>""".replace("__WEBMAIL_URL__", json.dumps(webmail_url))

    def _inject_webmail_rewrite_script(self, text, webmail_url):
        if not webmail_url or "__AAPANEL_BILLIONMAIL_WEBMAIL_URL__" in text:
            return text
        script = self._webmail_rewrite_script(webmail_url)
        if re.search(r"</head\s*>", text, re.I):
            return re.sub(r"</head\s*>", lambda match: script + "\n" + match.group(0), text, count=1, flags=re.I)
        if re.search(r"</body\s*>", text, re.I):
            return re.sub(r"</body\s*>", lambda match: script + "\n" + match.group(0), text, count=1, flags=re.I)
        return script + "\n" + text

    @staticmethod
    def _path_rewrite_script():
        return """<script>
(function () {
  if (window.__AAPANEL_BILLIONMAIL_PATH_PATCHED__ === true) return;
  window.__AAPANEL_BILLIONMAIL_PATH_PATCHED__ = true;

  function getBase() {
    var pathname = window.location.pathname.replace(/\\/+$/, "");
    var marker = "/billionmail";
    var idx = pathname.indexOf(marker);
    if (idx === -1) return "";
    return pathname.substring(0, idx + marker.length);
  }

  function rewritePath(url) {
    if (typeof url !== "string") return url;
    if (/^[a-zA-Z][a-zA-Z0-9+.-]*:/.test(url)) return url;
    var base = getBase();
    if (!base) return url;
    if (url === base || url.indexOf(base + "/") === 0 || url.indexOf(base + "?") === 0 || url.indexOf(base + "#") === 0) return url;
    if (url.indexOf("/billionmail") === 0) return base + url.slice("/billionmail".length);
    if (url === "/") return base + "/";
    if (url.charAt(0) === "/") return base + url;
    return url;
  }

  document.addEventListener("click", function (event) {
    var el = event.target;
    var anchor = el && el.closest ? el.closest("a[href]") : null;
    if (!anchor) return;
    var href = anchor.getAttribute("href");
    if (href === null || href === "" || href === "#") return;
    var rewritten = rewritePath(href);
    if (rewritten !== href) {
      event.preventDefault();
      event.stopPropagation();
      if (anchor.getAttribute("target") === "_blank") {
        window.open(rewritten, "_blank");
      } else {
        window.location.href = rewritten;
      }
    }
  }, true);

  var pushState = history.pushState;
  history.pushState = function (state, title, url) {
    if (typeof url === "string") arguments[2] = rewritePath(url);
    return pushState.apply(this, arguments);
  };
  var replaceState = history.replaceState;
  history.replaceState = function (state, title, url) {
    if (typeof url === "string") arguments[2] = rewritePath(url);
    return replaceState.apply(this, arguments);
  };
})();
</script>"""

    def _inject_path_rewrite_script(self, text):
        if "__AAPANEL_BILLIONMAIL_PATH_PATCHED__" in text:
            return text
        script = self._path_rewrite_script()
        if re.search(r"</head\s*>", text, re.I):
            return re.sub(r"</head\s*>", lambda match: script + "\n" + match.group(0), text, count=1, flags=re.I)
        if re.search(r"</body\s*>", text, re.I):
            return re.sub(r"</body\s*>", lambda match: script + "\n" + match.group(0), text, count=1, flags=re.I)
        return script + "\n" + text

    def _rewrite_text_content(self, text, path_full, config=None):
        proxy = self.proxy_prefix
        path = (path_full or "").split("?", 1)[0].lower()
        webmail_url = self._webmail_url(config)
        text = self._rewrite_settings_system_config(text, path_full, config)

        replacements = (
            ('${location.origin}/static/', '${location.origin}' + proxy + '/static/'),
            ('"/static/', '"{}/static/'.format(proxy)),
            ("'/static/", "'{}/static/".format(proxy)),
            ("`/static/", "`{}/static/".format(proxy)),
            ("(/static/", "({}/static/".format(proxy)),
            ("url(/static/", "url({}/static/".format(proxy)),
            ("=/static/", "={}/static/".format(proxy)),
        )
        for old, new in replacements:
            text = text.replace(old, new)

        if path.endswith(".js"):
            js_base = proxy.rstrip("/") + "/"
            text = re.sub(
                r'(\b[A-Za-z_$][\w$]*\.p=)(["\'])/(["\'])',
                r'\1\2{}/\3'.format(proxy),
                text,
            )
            text = re.sub(
                r'(history\s*:\s*\(0,\s*[A-Za-z_$][\w$]*\.PO\)\(["\'])/(["\']\))',
                lambda match: match.group(1) + js_base + match.group(2),
                text,
            )
            text = re.sub(
                r'(createWebHistory\s*\(\s*["\'])/(["\']\s*\))',
                lambda match: match.group(1) + js_base + match.group(2),
                text,
            )
            text = re.sub(
                r'(prefix\s*:\s*["\'])/api(["\'])',
                r'\1{}/api\2'.format(proxy),
                text,
            )
            text = re.sub(
                r'(baseURL\s*:\s*["\'])/api(["\'])',
                r'\1{}/api\2'.format(proxy),
                text,
            )
            text = self._rewrite_webmail_url(text, webmail_url)
        elif path.endswith((".html", ".htm")) or "<html" in text[:1024].lower():
            text = self._rewrite_csp_for_panel_scheme(text)
            text = self._rewrite_webmail_url(text, webmail_url)
            text = self._inject_webmail_rewrite_script(text, webmail_url)
            text = self._inject_path_rewrite_script(text)
        return self._rewrite_panel_absolute_urls(text)

    def _response_content(self, upstream_response, path_full, config=None):
        content = upstream_response.content
        if not content or not self._is_text_response(upstream_response, path_full):
            return content
        encoding = upstream_response.encoding or "utf-8"
        try:
            text = content.decode(encoding)
        except Exception:
            try:
                text = content.decode("utf-8")
            except Exception:
                return content
        return self._rewrite_text_content(text, path_full, config).encode(encoding, errors="ignore")

    def _is_html_response(self, upstream_response, path_full):
        content_type = (upstream_response.headers.get("content-type") or "").lower()
        path = (path_full or "").split("?", 1)[0].lower()
        return "text/html" in content_type or path.endswith((".html", ".htm")) or path in ("", "/")

    def proxy(self, path_full=""):
        try:
            BillionMailProxy._trace_api_feature(path_full)
            if (path_full or "").strip("/") == "__aapanel_sso__":
                return self._sso_bridge()

            urllib3.disable_warnings()
            urllib3_conn.allowed_gai_family = lambda: socket.AF_INET
            config = BillionMailMod().get_proxy_config()
            if not config.get("installed"):
                return self._error("BillionMail is not installed", 404)
            target_base = config.get("target_base")
            if not target_base:
                return self._error("BillionMail web port is not configured", 502)

            proxy_url = self._target_url(target_base, path_full)
            upstream_response = requests.request(
                request.method,
                proxy_url,
                **self._request_kwargs(target_base)
            )
            response = Response(
                self._response_content(upstream_response, path_full, config),
                headers=self._response_headers(upstream_response, target_base),
                content_type=upstream_response.headers.get("content-type", None),
                status=upstream_response.status_code,
            )
            if self._is_html_response(upstream_response, path_full):
                response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate"
                response.headers["Pragma"] = "no-cache"
                response.headers["Expires"] = "0"
            return self._set_cookie_headers(response, upstream_response)
        except Exception as ex:
            return self._error(str(ex), 500)
