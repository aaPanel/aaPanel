# ===================================Flask HOOK========================#
from BTPanel.app import *

# Flask请求勾子
@app.before_request
def request_check():
    if request.method not in ['GET', 'POST']: return abort(404)

    # 获取客户端真实IP
    x_real_ip = request.headers.get('X-Real-Ip')
    if x_real_ip:
        request.remote_addr = x_real_ip
        request.environ.setdefault('REMOTE_PORT', public.get_remote_port())

    g.request_time = time.time()
    g.return_message = False
    # 路由和URI长度过滤
    if len(request.path) > 256: return abort(403)
    if len(request.url) > 1024: return abort(403)
    # URI过滤
    if not uri_match.match(request.path): return abort(403)
    # POST参数过滤
    if request.path in [
            '/login',
            '/safe',
            # '/v2_safe',
            '/hook',
            '/public',
            '/down',
            '/get_app_bind_status',
            '/check_bind',
            '/userRegister',
    ]:
        pdata = request.form.to_dict()
        for k in pdata.keys():
            if len(k) > 48: return abort(403)
            if len(pdata[k]) > 256: return abort(403)
    # SESSIONID过滤
    session_id = request.cookies.get(app.config['SESSION_COOKIE_NAME'], '')
    if session_id and not session_id_match.match(session_id): return abort(403)

    # 请求头过滤
    # if not public.filter_headers():
    #     return abort(403)

    if session.get('debug') == 1: return
    g.get_csrf_html_token_key = public.get_csrf_html_token_key()

    if app.config['BASIC_AUTH_OPEN']:
        if request.path in [
                '/public', '/download', '/mail_sys', '/hook', '/down',
                '/check_bind', '/get_app_bind_status'
        ]:
            return
        auth = request.authorization
        if not comm.get_sk(): return
        if not auth: return send_authenticated()
        tips = '_bt.cn'
        if public.md5(auth.username.strip() + tips) != app.config['BASIC_AUTH_USERNAME'] \
                or public.md5(auth.password.strip() + tips) != app.config['BASIC_AUTH_PASSWORD']:
            return send_authenticated()

    if not request.path in [
            '/safe',
            # '/v2_safe',
            '/hook',
            '/public',
            '/mail_sys',
            '/down'
    ]:
        ip_check = public.check_ip_panel()
        if ip_check: return ip_check

    if request.path.startswith('/static/') or request.path == '/code':
        if not 'login' in session and not 'admin_auth' in session and not 'down' in session:
            return abort(401)
    domain_check = public.check_domain_panel()
    if domain_check: return domain_check
    if public.is_local():
        not_networks = ['uninstall_plugin', 'install_plugin', 'UpdatePanel']
        if request.args.get('action') in not_networks:
            return public.returnJson(
                False,
                'This feature cannot be used in offline mode!'), json_header

    if request.path in [
            '/site', '/ftp', '/database', '/soft', '/control', '/firewall',
            '/files', '/xterm', '/crontab', '/config'
    ]:
        if public.is_error_path():
            return redirect('/error', 302)
        if not request.path in ['/config']:
            if session.get('password_expire', False):
                return redirect('/modify_password', 302)


# Flask 请求结束勾子
@app.teardown_request
def request_end(reques=None):
    if request.method not in ['GET', 'POST']: return
    if not request.path.startswith('/static/'):
        public.write_request_log(reques)
        #当路由为/plugin时，不检测g.return_message
        # if  not request.path.startswith('/plugin'):
        if request.path.startswith('/sitetest'):
            if 'return_message' in g:
                if not g.return_message:
                    public.print_log("当前为网站路由，且未使用统一响应函数public.return_message")
                    return abort(403)
                    # return public.returnJson(
                    #     False, 'Request failed!Request not using unified response!'
                    # ), json_header
                else:
                    g.return_message = False
                    public.print_log("当前为网站路由，且已使用统一响应函数public.return_message")
        if 'api_request' in g:
            if g.api_request:
                session.clear()


# Flask 404页面勾子
@app.errorhandler(404)
def error_404(e):
    if request.method not in ['GET', 'POST']: return
    if not session.get('login', None):
        g.auth_error = True
        return public.error_not_login()
    errorStr = '''<html>
<head><title>404 Not Found</title></head>
<body>
<center><h1>404 Not Found</h1></center>
<hr><center>nginx</center>
</body>
</html>'''
    headers = {"Content-Type": "text/html"}
    return Response(errorStr, status=404, headers=headers)


# Flask 403页面勾子
@app.errorhandler(403)
def error_403(e):
    if request.method not in ['GET', 'POST']: return
    if not session.get('login', None):
        g.auth_error = True
        return public.error_not_login()
    errorStr = '''<html>
<head><title>403 Forbidden</title></head>
<body>
<center><h1>403 Forbidden</h1></center>
<hr><center>nginx</center>
</body>
</html>'''
    headers = {"Content-Type": "text/html"}
    return Response(errorStr, status=403, headers=headers)


# Flask 500页面勾子
@app.errorhandler(500)
def error_500(e):
    if request.method not in ['GET', 'POST']: return
    if not session.get('login', None):
        g.auth_error = True
        return public.error_not_login()
    ss = '''404 Not Found: The requested URL was not found on the server. If you entered the URL manually please check your spelling and try again.

During handling of the above exception, another exception occurred:'''
    error_info = public.get_error_info().strip().split(ss)[-1].strip()
    _form = request.form.to_dict()
    if 'username' in _form: _form['username'] = '******'
    if 'password' in _form: _form['password'] = '******'
    if 'phone' in _form: _form['phone'] = '******'
    request_info = '''REQUEST_DATE: {request_date}
 PAN_VERSION: {panel_version}
  OS_VERSION: {os_version}
 REMOTE_ADDR: {remote_addr}
 REQUEST_URI: {method} {full_path}
REQUEST_FORM: {request_form}
  USER_AGENT: {user_agent}'''.format(
        request_date=public.getDate(),
        remote_addr=public.GetClientIp(),
        method=request.method,
        full_path=public.xsssec(request.full_path),
        request_form=public.xsssec(str(_form)),
        user_agent=public.xsssec(request.headers.get('User-Agent')),
        panel_version=public.version(),
        os_version=public.get_os_version())

    result = public.readFile(
        public.get_panel_path() +
        '/BTPanel/templates/default/panel_error.html').format(
            error_title=error_info.split("\n")[-1],
            request_info=request_info,
            error_msg=error_info)
    return Resp(result, 500)
