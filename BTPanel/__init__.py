# coding: utf-8
# +-------------------------------------------------------------------
# | aaPanel
# +-------------------------------------------------------------------
# | Copyright (c) 2015-2099 aaPanel(www.aapanel.com) All rights reserved.
# +-------------------------------------------------------------------
# | Author: hwliang <hwl@aapanel.com>
# +---

from public.hook_import import hook_import
hook_import()

# from .app import *
# from .routes.flask_hook import *
# from .routes.v1 import *
# from .routes.v2 import *

import logging
import sys
import json
import os
import threading
import time
import re
import uuid
import psutil
import zipfile

panel_path = '/www/server/panel'
if not os.name in ['nt']:
    os.chdir(panel_path)
if not 'class/' in sys.path:
    sys.path.insert(0, 'class/')
if not 'class_v2/' in sys.path:
    sys.path.insert(0, 'class_v2/')

from flask import (
    Flask, session, render_template, send_file, request, redirect, g,
    render_template_string, abort, stream_with_context, Response as Resp
)
from cachelib import SimpleCache, SimpleCacheSession
from werkzeug.wrappers import Response
from flask_session import Session
from flask_compress import Compress

cache = SimpleCache(5000)
import public

# 初始化Flask应用
app = Flask(
    __name__,
    template_folder="templates/{}".format(public.GetConfigValue('template'))
)
Compress(app)
try:
    from flask_sock import Sock
except:
    from flask_sockets import Sockets as Sock

sockets = Sock(app)
# 注册HOOK
hooks = {}
if not hooks:
    public.check_hooks()
# import db
dns_client = None
app.config['DEBUG'] = os.path.exists('data/debug.pl')
app.config['SSL'] = os.path.exists('data/ssl.pl')

# 设置BasicAuth
basic_auth_conf = 'config/basic_auth.json'
app.config['BASIC_AUTH_OPEN'] = False
if os.path.exists(basic_auth_conf):
    try:
        ba_conf = json.loads(public.readFile(basic_auth_conf))
        app.config['BASIC_AUTH_USERNAME'] = ba_conf['basic_user']
        app.config['BASIC_AUTH_PASSWORD'] = ba_conf['basic_pwd']
        app.config['BASIC_AUTH_OPEN'] = ba_conf['open']
    except:
        pass

# 初始化SESSION服务
app.secret_key = public.md5(
    str(os.uname()) +
    str(psutil.boot_time()))  # uuid.UUID(int=uuid.getnode()).hex[-12:]
local_ip = None
my_terms = {}
app.config['SESSION_MEMCACHED'] = SimpleCacheSession(1000, 86400)
app.config['SESSION_TYPE'] = 'memcached'
app.config['SESSION_PERMANENT'] = True
app.config['SESSION_USE_SIGNER'] = True
app.config['SESSION_KEY_PREFIX'] = 'BT_:'
app.config['SESSION_COOKIE_NAME'] = public.md5(app.secret_key)
app.config['PERMANENT_SESSION_LIFETIME'] = 86400 * 30
app.config['SESSION_COOKIE_SAMESITE'] = None

if app.config['SSL']:
    app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
    app.config['SESSION_COOKIE_SECURE'] = True


Session(app)

import common

# 初始化路由
comm = common.panelAdmin()
method_all = ['GET', 'POST']
method_get = ['GET']
method_post = ['POST']
json_header = {'Content-Type': 'application/json; charset=utf-8'}
text_header = {'Content-Type': 'text/plain; charset=utf-8'}
cache.set('p_token', 'bmac_' + public.Md5(public.get_mac_address()))
admin_path_file = 'data/admin_path.pl'
admin_path = '/'
if os.path.exists(admin_path_file):
    admin_path = public.readFile(admin_path_file).strip()
admin_path_checks = [
    '/',
    '/san',
    '/bak',
    '/monitor',
    '/abnormal',
    '/close',
    '/task',
    '/login',
    '/config',
    '/site',
    '/sites',
    '/ftp',
    '/public',
    '/database',
    '/data',
    '/download_file',
    '/control',
    '/crontab',
    '/firewall',
    '/files',
    '/soft',
    '/ajax',
    '/system',
    '/panel_data',
    '/code',
    '/ssl',
    '/plugin',
    '/wxapp',
    '/hook',
    '/safe',
    '/yield',
    '/downloadApi',
    '/pluginApi',
    '/auth',
    '/download',
    '/cloud',
    '/webssh',
    '/connect_event',
    '/panel',
    '/acme',
    '/down',
    '/api',
    '/tips',
    '/message',
    '/warning',
    '/userRegister',  # 面板内注册
    '/userLang',  # 登录设语言
    '/docker',
    '/btdocker',
    '/breaking_through',
]
if admin_path in admin_path_checks: admin_path = '/bt'
if admin_path[-1] == '/': admin_path = admin_path[:-1]
uri_match = re.compile(
    r"(^/static/[\w_\./\-]+\.(js|css|png|jpg|gif|ico|svg|woff|woff2|ttf|otf|eot|map)$|^/[\w_\./\-]*$)"
)
session_id_match = re.compile(r"^[\w\.\-]+$")
route_v2 = '/v2'  # v2版本路由前缀

# load translations
from public.translations import load_translations
load_translations()
# 登录页语言包
from public.translations import load_login_translations
load_login_translations()

# ========================== Ignore Zipfile Encode Error ==============
# hook zipfile.ZipInfo._encodeFilenameFlags, ignore the encode error
_oldEncodeFilenameFlags = zipfile.ZipInfo._encodeFilenameFlags

def _newEncodeFilenameFlags(self):
    try:
        return _oldEncodeFilenameFlags(self)
    except:
        return self.filename.encode('utf-8', 'ignore'), self.flag_bits | zipfile._MASK_UTF_FILENAME

zipfile.ZipInfo._encodeFilenameFlags = _newEncodeFilenameFlags

# ========================== Ignore Error End =========================


# ========================== Init Menu Path Map =======================
menu_map = {
        'memua': '/',                     # Home
        'memuasite': '/site',             # Website
        'memuawptoolkit': '/wp/toolkit',  # WP Toolkit
        'memuaftp': '/ftp',               # FTP
        'memuadatabase': '/database',     # Databases
        'memudocker': '/docker',          # Docker
        'memuacontrol': '/control',       # Monitor
        'memuafirewall': '/firewall',     # Security
        'memu_btwaf': '/btwaf',           # Waf
        'memu_mailsys': '/mail',          # Mail Server
        'memuafiles': '/files',           # Files
        'memualogs': '/logs',             # Logs
        'menu_ssl': '/ssl_domain',        # SSL
        'memuaxterm': '/xterm',           # Terminal
        'memuaccount': '/whm',            # Account
        'memuacrontab': '/crontab',       # Cron
        'memuasoft': '/soft',             # App Store
        'memuaconfig': '/config',         # Settings
        'dologin': '/login',              # Log out
        'memuASSL': '/ssl_domain'          # Domain management
}
try:
    menu_default_conf_path = os.path.join(panel_path, 'config/menu.json')
    if os.path.exists(menu_default_conf_path):
        menu_read = public.readFile(menu_default_conf_path)
        menu_list = json.loads(menu_read) if menu_read else []
        menu_map = {
            x.get('id').lower(): x.get('href') for x in menu_list if x.get('id') and x.get('href')
        } if menu_list else menu_map
except Exception as e:
    public.print_log(f"menu config error, {e}")

# ========================== Menu Map End ============================

# ====================== Panel Settings Asset Default =================
PANEL_DEFAULT_ASSET = {
    'favicon': '/static/favicon.ico',  # 默认网站favicon图标
    'show_login_logo': True,  # 默认不显示登录logo
    'show_login_bg_images': False,  # 默认不显示登录背景图片
    'login_logo': '/static/icons/logo-green.svg',  # 默认登录logo图片
    'login_bg_images': '',  # 默认登录背景图片
    'login_bg_images_opacity': 100,  # 默认登录背景图片透明度
    'show_main_bg_images': True,  # 默认不显示主界面背景图
    'main_bg_images': '/static/icons/main_bg.png',  # 主界面背景图
    'main_bg_images_opacity': 100,  # 主界面背景图透明度
    'main_content_opacity': 100,  # 主界面内容透明度
    'main_shadow_color': '#000000',  # 主界面阴影颜色
    'main_shadow_opacity': 5,  # 主界面阴影透明度
    'menu_logo': '/static/icons/menu_logo.png',  # 菜单栏顶部logo图标
    'menu_bg_opacity': 100,  # 默认侧边栏背景透明度
    'theme_color': '#3c444d',  # 默认主色
    'theme_name': 'default',  # 默认主题名称
    'home_state_font_size': 24,  # 首页概览字体大小
    'main_bg_images_dark': '/static/icons/main_bg_dark.png',  # 这个是用来搞黑暗模式的
}

# ============================== Asset End ============================



# ===================================Flask HOOK========================#
# Flask请求勾子
from flask import current_app
@app.before_request
def request_check():
    # 获取客户端真实IP，判断是否启动CDN代理
    CDN_PROXY = current_app.config.get('CDN_PROXY', False)
    if CDN_PROXY:
        if 'CF-Connecting-IP' in request.headers:
            x_real_ip = request.headers['CF-Connecting-IP']
        elif 'X-Forwarded-For' in request.headers:
            x_real_ip = request.headers['X-Forwarded-For'].split(',')[0].strip()
        else:
            x_real_ip = request.headers.get('X-Real-Ip')
    else:
        x_real_ip = request.headers.get('X-Real-Ip')
    if x_real_ip:
        request.remote_addr = x_real_ip
        request.environ.setdefault('REMOTE_PORT', public.get_remote_port())
    # 过滤菜单
    if 'uid' in session and session['uid'] != 1 and not public.user_router_authority():
        if public.M('users').where('id=?', (session['uid'],)).select():
            import config_v2
            menus = config_v2.config().get_menu_list()
            show_menus = []
            if menus.get('status') == 0:
                show_menus = [
                    i.get('id', '').lower() for i in menus.get('message', []) if i.get('show') is True
                ]
            if request.path == '/':
                try:
                    path = menu_map[show_menus[0]]
                    if path == '/login':
                        return abort(403)
                    return redirect('{}'.format(path.lower()), 302)
                except Exception:
                    return abort(403)
            if len(show_menus) < 2:
                return abort(403)
            if not public.user_router_authority():
                return abort(403)
    if request.method not in ['GET', 'POST', 'HEAD']: return abort(404)
    g.request_time = time.time()
    g.return_message = False

    # URI过滤 1
    if request.path not in ('/google/redirect', '/google/callback') and not request.path.startswith('/v2/pmta/'):
        # 路由和URI长度过滤
        if len(request.path) > 256: return abort(403)
        if len(request.url) > 1024: return abort(403)

    # URI过滤 2
    if not uri_match.match(request.path): return abort(403)

    # POST参数过滤
    if request.path in [
        '/login',
        '/safe',
        '/hook',
        '/public',
        '/down',
        '/get_app_bind_status',
        '/check_bind',
        '/userRegister',
        '/userLang',
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
            return public.returnJson( False, 'This feature cannot be used in offline mode!'), json_header
    # 适配docker----  '/docker',

    path_list = (
       '/site', '/ftp', '/database', '/soft', '/control', '/firewall',
        '/files', '/xterm', '/crontab', '/config', '/docker', '/btdocker','/breaking_through',
    )
    if (request.path.startswith(path_list) or request.path == "/") and request.method == "GET":
        if request.args.get('action') in [
            'get_tmp_token','download_cert'
        ]:
            return
    # if request.path in [
    #     '/site', '/ftp', '/database', '/soft', '/control', '/firewall',
    #     '/files', '/xterm', '/crontab', '/config', '/docker', '/btdocker','/breaking_through',
    # ]:
        if public.is_error_path():
            return redirect('/error', 302)
        # 密码过期相关功能
        if request.path not in ['/config', '/modify_password', '/login']:
            if not session.get("login", False):  # 没有登录时不触发密码过期修改
                return
            reslut = session.get('password_expire', None)
            if reslut is None:
                reslut = not public.password_expire_check()
                session['password_expire'] = reslut
            if reslut:
                return redirect('/modify_password', 302)

    # 新增   适配docker时增加 未测试
    # 处理登录页面相对路径的静态文件
    if request.path.find('/static/') > 0:
        new_auth_path = _auth_path = public.get_admin_path()

        # 2024/1/3 下午 8:35 检测_auth_path是否有包含2个以上/符号,如果有则取最后一个/符号前的字符串然后替换成_auth_path
        if _auth_path.count('/') > 1:
            new_auth_path = _auth_path[:_auth_path.rfind('/')]

        if not public.path_safe_check(request.path): return abort(404)  # 路径安全检查

        _new_route = request.path[0:request.path.find('/static/')]
        if request.path.find(_auth_path) == 0:
            static_file = public.get_panel_path() + '/BTPanel' + request.path.replace(_auth_path, '').replace('//', '/')
            if not os.path.exists(static_file): return abort(404)
            return send_file(static_file, conditional=True, etag=True)
        elif request.path.find(new_auth_path) == 0:
            static_file = public.get_panel_path() + '/BTPanel' + request.path.replace(new_auth_path, '').replace('//',
                                                                                                                 '/')
            if not os.path.exists(static_file): return abort(404)
            return send_file(static_file, conditional=True, etag=True)
        elif _new_route in admin_path_checks:

            static_file = public.get_panel_path() + '/BTPanel' + request.path[len(_new_route):].replace('//', '/')
            # if not os.path.exists(static_file): return abort(404)
            # 检测是否是插件静态文件
            plugin_static_file = public.get_panel_path() + '/plugin/' + request.path
            is_plugin_static = os.path.exists(plugin_static_file)

            # 既不是面板静态文件也不是插件静态文件
            if not os.path.exists(static_file) and not is_plugin_static: return abort(404)

            # 如果是插件静态文件
            if is_plugin_static:
                return send_file(plugin_static_file, conditional=True, etag=True)

            # 如果是面板静态文件
            return send_file(static_file, conditional=True, etag=True)

    if request.path.find('/static/img/soft_ico/ico') >= 0:
        # 路径安全检查
        if public.path_safe_check(request.path) is False:
            return abort(404)
        static_file = "{}/BTPanel/{}".format(panel_path, request.path)
        if not os.path.exists(static_file):
            static_file = "{}/BTPanel/static/img/soft_ico/icon_plug.svg".format(panel_path)
        return send_file(static_file, conditional=True, etag=True)

    # 处理登录成功状态，更新节点
    if 'login' in session and session['login'] == True:
        if not cache.get('bt_home_node'):
            public.run_thread(public.ExecShell, ('btpython /www/server/panel/script/reload_check.py hour',))
            cache.set('bt_home_node', True, 3600)


# Flask 请求结束勾子
@app.teardown_request
def request_end(reques=None):
    if request.method not in ['GET', 'POST']: return
    if not request.path.startswith('/static/') or not request.path.startswith('/v2/static/'):
        # import public
        public.write_request_log(reques)

        # 当路由为v2版才检测，且不检测/plugin时
        if request.path.startswith('/v2'):
            now_time = time.time()
            session_timeout = session.get('session_timeout', 0)
            if (session_timeout > now_time or session_timeout == 0) and not request.path.startswith('/v2/plugin'):
                # 首页涉及的请求模块，暂不强制
                prefixes = ["/v2/site", "/v2/ftp", "/v2/database", "/v2/docker", "/v2/safe/security/set_security",
                            "/v2/safe/security/get_repair_bar","/v2/breaking_through"]
                for prefix in prefixes:
                    if request.path.startswith(prefix):
                        if 'return_message' in g:
                            if not g.return_message:
                                # public.print_log("当前路由且未使用统一响应函数public.return_message")
                                # return abort(404)
                                # return public.returnJson(
                                #     False, 'Request failed!Request not using unified response!'
                                # ), json_header
                                pass
                            else:
                                #                         return abort(405)
                                g.return_message = False
                                # public.print_log("当前路由已使用统一响应函数public.return_message")
                                break
        if 'api_request' in g:
            if g.api_request:
                session.clear()


# Flask 405页面勾子
@app.errorhandler(405)
def error_405(e):
    if request.method not in ['GET', 'POST']: return
    if not session.get('login', None):
        g.auth_error = True
        return public.error_not_login()
    errorStr = '''<html>
<head><title>405 Not Found</title></head>
<body>
<center><h1>请求接口请使用统一响应函数</h1></center>
<hr><center>nginx</center>
</body>
</html>'''
    headers = {"Content-Type": "text/html"}
    return Response(errorStr, status=404, headers=headers)


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


# 错误收集
@app.errorhandler(Exception)
def error_500(e):
    # handle the hint exception.
    if isinstance(e, public.HintException):
        return public.fail_v2(str(e))

    # Print error traceback.
    from traceback import format_exc
    public.print_log(format_exc())

    if request.method not in ['GET', 'POST']: return Response(status=500)

    if not session.get('login', None):
        g.auth_error = True
        return public.error_not_login()

    ss = '''404 Not Found: The requested URL was not found on the server. If you entered the URL manually please check your spelling and try again.

During handling of the above exception, another exception occurred:'''
    error_info = public.get_error_info().strip().split(ss)[-1].strip()

    nn = 'During handling of the above exception, another exception occurred:'
    if error_info.find(nn) != -1 and error_info.find('public.error_conn_cloud') != -1:
        error_info = error_info.split(nn)[0].strip()

    _form = request.form.to_dict()
    if 'username' in _form: _form['username'] = '******'
    if 'password' in _form: _form['password'] = '******'
    if 'phone' in _form: _form['phone'] = '******'
    if 'pem' in _form: _form['pem'] = '******'
    if 'pwd' in _form: _form['pwd'] = '******'
    if 'key' in _form: _form['key'] = '******'
    if 'csr' in _form: _form['csr'] = '******'
    if 'db_user' in _form: _form['db_user'] = '******'
    if 'db_password' in _form: _form['db_pwd'] = '******'

    request_info = '''REQUEST_DATE: {request_date}
  VERSION: {os_version} - {panel_version}
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
    error_title = error_info.split("\n")[-1].replace('public.PanelError: ',
                                                     '').strip()
    if error_info.find('Failed to connect to the cloud server') != -1:
        error_title = "Failed to connect to the cloud server!"

    result = public.readFile(
        public.get_panel_path() +
        '/BTPanel/templates/default/panel_error.html').format(
        error_title=error_title,
        request_info=request_info,
        error_msg=error_info)

    # 用户信息
    # if not public.cache_get("infos"):
    #     user_info = json.loads(public.ReadFile("{}/data/userInfo.json".format(public.get_panel_path())))
    #     public.cache_set("infos", user_info, 1800)
    # else:
    #     user_info = public.cache_get("infos")
    try:
        if "import panelSSL" in error_info:
            result = public.ExecShell("btpip list|grep pyOpenSSL")[0]
            error_info = "{}\n版本信息:{}".format(error_info, result.strip())
    except:
        error_info = "{}\n版本信息: 获取失败".format(error_info)

    # 错误信息
    error_infos = {
        # "UID":  user_info['uid'],  # 用户ID
        # 'ACCESS_KEY': user_info['access_key'],  # 用户密钥
        # 'SERVER_ID': user_info['serverid'],  # 服务器ID
        "REQUEST_DATE": public.getDate(),  # 请求时间
        "PANEL_VERSION": public.version(),  # 面板版本
        "OS_VERSION": public.get_os_version(),  # 操作系统版本
        "REMOTE_ADDR": public.GetClientIp(),  # 请求IP
        "REQUEST_URI": request.method + request.full_path,  # 请求URI
        "REQUEST_FORM": public.xsssec(str(_form)),  # 请求表单
        "USER_AGENT": public.xsssec(request.headers.get('User-Agent')),  # 客户端连接信息
        "ERROR_INFO": error_info,  # 错误信息
        "PACK_TIME": public.readFile("/www/server/panel/config/update_time.pl") if os.path.exists(
            "/www/server/panel/config/update_time.pl") else public.getDate(),  # 打包时间
        "TYPE": 100,
        "ERROR_ID": str(e)
    }
    pkey = public.Md5(error_infos["ERROR_ID"])

    # 提交异常报告
    if not public.cache_get(pkey):
        try:
            public.run_thread(public.httpPost, ("https://geterror.aapanel.com/bt_error/index.php", error_infos))
            public.cache_set(pkey, 1, 1800)
        except Exception as e:
            pass

    return Resp(result, 500)


# ===================================Flask HOOK========================#


# ===================================普通路由区========================#
# @app.route('/', methods=method_all)
# def home():
#     # 面板首页
#     comReturn = comm.local()
#     if comReturn: return comReturn
#     data = {}
#     data[public.to_string([112,
#                            100])], data['pro_end'], data['ltd_end'] = get_pd()
#     data['siteCount'] = public.M('sites').count()
#     data['ftpCount'] = public.M('ftps').count()
#     data['databaseCount'] = public.M('databases').count()
#     data['lan'] = public.GetLan('index')
#     data['js_random'] = get_js_random()
#     return render_template('index.html', data=data)


@app.route('/', methods=method_get)
@app.route('/<path:sub_path>', methods=method_get)
def index_new(sub_path: str = ''):

    if sub_path == 'unsubscribe.html':
        return render_template('unsubscribe.html')

    # 面板首页
    comReturn = comm.local()
    if comReturn: return comReturn
    data = {}

    if sub_path == '':
        data[public.to_string([112, 100])], data['pro_end'], data['ltd_end'] = get_pd()
        data['siteCount'] = public.M('sites').count()
        data['ftpCount'] = public.M('ftps').count()
        data['databaseCount'] = public.M('databases').count()
        data['lan'] = public.GetLan('index')
        data['js_random'] = get_js_random()
    elif sub_path.startswith('config'):
        import system, wxapp, config
        c_obj = config.config()
        data = system.system().GetConcifInfo()
        data['lan'] = public.GetLan('config')
        try:
            data['wx'] = wxapp.wxapp().get_user_info(None)['msg']
        except:
            data['wx'] = 'INIT_WX_NOT_BIND'
        data['api'] = ''
        data['ipv6'] = ''
        sess_out_path = 'data/session_timeout.pl'
        if not os.path.exists(sess_out_path):
            public.writeFile(sess_out_path, '86400')
        s_time_tmp = public.readFile(sess_out_path)
        if not s_time_tmp: s_time_tmp = '0'
        data['session_timeout'] = int(s_time_tmp)
        if c_obj.get_ipv6_listen(None): data['ipv6'] = 'checked'
        if c_obj.get_token(None)['open']: data['api'] = 'checked'
        data['basic_auth'] = c_obj.get_basic_auth_stat(None)
        data['status_code'] = c_obj.get_not_auth_status()
        data['basic_auth']['value'] = public.getMsg('CLOSED')
        if data['basic_auth']['open']:
            data['basic_auth']['value'] = public.getMsg('OPENED')
        data['debug'] = ''
        data['js_random'] = get_js_random()
        if app.config['DEBUG']: data['debug'] = 'checked'
        data['is_local'] = ''
        if public.is_local(): data['is_local'] = 'checked'
        data['public_key'] = public.get_rsa_public_key().replace("\n", "")
    elif sub_path.startswith('soft'):
        import system
        data = system.system().GetConcifInfo()
        data['lan'] = public.GetLan('soft')
        data['js_random'] = get_js_random()
    elif sub_path.startswith('crontab'):
        import system
        data = system.system().GetConcifInfo()
        data['lan'] = public.GetLan('crontab')
        data['js_random'] = get_js_random()
    elif sub_path.startswith('docker'):
        import system
        data = system.system().GetConcifInfo()
        data['js_random'] = get_js_random()
        data['lan'] = public.GetLan('files')
    elif sub_path.startswith('control'):
        import system
        data = system.system().GetConcifInfo()
        data['lan'] = public.GetLan('control')
        data['js_random'] = get_js_random()
    elif sub_path.startswith('logs'):
        data = {}
        data['lan'] = public.GetLan('soft')
        data['show_workorder'] = not os.path.exists('data/not_workorder.pl')
    elif sub_path.startswith('database'):
        import ajax
        from panelPlugin import panelPlugin
        session['phpmyadminDir'] = False
        if panelPlugin().get_phpmyadmin_stat():
            pmd = get_phpmyadmin_dir()
            if pmd:
                session['phpmyadminDir'] = 'http://' + public.GetHost(
                ) + ':' + pmd[1] + '/' + pmd[0]
        ajax.ajax().set_phpmyadmin_session()
        import system
        data = system.system().GetConcifInfo()
        data['isSetup'] = os.path.exists(
            public.GetConfigValue('setup_path') + '/mysql/bin')
        data['mysql_root'] = public.M('config').where(
            'id=?', (1,)).getField('mysql_root')
        data['lan'] = public.GetLan('database')
        data['js_random'] = get_js_random()
    elif sub_path.startswith('ftp'):
        FtpPort()
        import system
        data = system.system().GetConcifInfo()
        data['isSetup'] = True
        data['js_random'] = get_js_random()
        if os.path.exists(public.GetConfigValue('setup_path') +
                          '/pure-ftpd') == False:
            data['isSetup'] = False
        data['lan'] = public.GetLan('ftp')
    elif sub_path.startswith('site'):
        import system
        data = system.system().GetConcifInfo()
        data['isSetup'] = True
        data['lan'] = public.getLan('site')
        data['js_random'] = get_js_random()
        if os.path.exists(public.GetConfigValue('setup_path') + '/nginx') == False \
                and os.path.exists(public.GetConfigValue('setup_path') + '/apache') == False \
                and os.path.exists('/usr/local/lsws/bin/lswsctrl') == False:
            data['isSetup'] = False
    elif sub_path.startswith('xterm'):
        import system
        data = system.system().GetConcifInfo()
    elif sub_path.startswith('firewall'):
        import system
        data = system.system().GetConcifInfo()
        data['lan'] = public.GetLan('firewall')
        data['js_random'] = get_js_random()
    elif sub_path.startswith('files'):
        import system
        data = system.system().GetConcifInfo()
        data['recycle_bin'] = os.path.exists('data/recycle_bin.pl')
        data['lan'] = public.GetLan('files')
        data['js_random'] = get_js_random()
    elif sub_path.startswith('ssh_security'):
        data['lan'] = public.GetLan('firewall')
        data['js_random'] = get_js_random()

    data['isSetup'] = True
    if os.path.exists(public.GetConfigValue('setup_path') + '/nginx') == False \
            and os.path.exists(public.GetConfigValue('setup_path') + '/apache') == False \
            and os.path.exists('/usr/local/lsws/bin/lswsctrl') == False:
        data['isSetup'] = False

    # load translations
    # 登录成功后重启面板 使翻译切换生效
    # public.ExecShell("/etc/init.d/bt start")
    # public.writeFile('data/restart.pl', 'True')

    from public.translations import load_translations
    load_translations()

    import base64
    data['translations'] = base64.b64encode(json.dumps(load_translations()).encode()).decode()
    data['public_key'] = public.get_rsa_public_key().replace("\n", "")
    return render_template('index_new.html', data=data)



@app.route('/xterm', methods=method_post)
def xterm():
    # 宝塔终端管理
    comReturn = comm.local()
    if comReturn: return comReturn
    import ssh_terminal
    ssh_host_admin = ssh_terminal.ssh_host_admin()
    defs = ('get_host_list', 'get_host_find', 'modify_host', 'create_host',
            'remove_host', 'set_sort', 'get_command_list', 'create_command',
            'get_command_find', 'modify_command', 'remove_command')
    return publicObject(ssh_host_admin, defs, None)

# 密码过期路由
@app.route('/modify_password', methods=method_get)
def modify_password():
    comReturn = comm.local()
    if comReturn: return comReturn
    # if not session.get('password_expire',False): return redirect  ('/',302)
    data = {}
    from public.translations import load_translations
    load_translations()

    import base64
    data['translations'] = base64.b64encode(json.dumps(load_translations()).encode()).decode()
    data['public_key'] = public.get_rsa_public_key()
    g.title = 'The password has expired, please change it!'
    return render_template('index_new.html', data=data)


@app.route('/site', methods=method_post)
def site(pdata=None):
    # 网站管理
    comReturn = comm.local()
    if comReturn: return comReturn
    import panelSite
    siteObject = panelSite.panelSite()

    defs = (
        'get_auto_restart_rph',
        'remove_auto_restart_rph',
        'auto_restart_rph',
        'check_del_data',
        'upload_csv',
        'create_website_multiple',
        'del_redirect_multiple',
        'del_proxy_multiple',
        'delete_dir_auth_multiple',
        'delete_dir_bind_multiple',
        'delete_domain_multiple',
        'set_site_etime_multiple',
        'set_site_php_version_multiple',
        'delete_website_multiple',
        'set_site_status_multiple',
        'get_site_err_log',
        'get_site_domains',
        'GetRedirectFile',
        'SaveRedirectFile',
        'DeleteRedirect',
        'GetRedirectList',
        'CreateRedirect',
        'ModifyRedirect',
        "set_error_redirect",
        'set_dir_auth',
        'delete_dir_auth',
        'get_dir_auth',
        'modify_dir_auth_pass',
        'reset_wp_db',
        'export_domains',
        'import_domains',
        'GetSiteLogs',
        'GetSiteDomains',
        'GetSecurity',
        'SetSecurity',
        'ProxyCache',
        'CloseToHttps',
        'HttpToHttps',
        'SetEdate',
        'SetRewriteTel',
        'GetCheckSafe',
        'CheckSafe',
        'GetDefaultSite',
        'SetDefaultSite',
        'CloseTomcat',
        'SetTomcat',
        'apacheAddPort',
        'AddSite',
        'GetPHPVersion',
        'SetPHPVersion',
        'DeleteSite',
        'AddDomain',
        'DelDomain',
        'GetDirBinding',
        'AddDirBinding',
        'GetDirRewrite',
        'DelDirBinding',
        'get_site_types',
        'add_site_type',
        'remove_site_type',
        'modify_site_type_name',
        'set_site_type',
        'UpdateRulelist',
        'SetSiteRunPath',
        'GetSiteRunPath',
        'SetPath',
        'SetIndex',
        'GetIndex',
        'GetDirUserINI',
        'SetDirUserINI',
        'GetRewriteList',
        'SetSSL',
        'SetSSLConf',
        'CreateLet',
        'CloseSSLConf',
        'GetSSL',
        'SiteStart',
        'SiteStop',
        'Set301Status',
        'Get301Status',
        'CloseLimitNet',
        'SetLimitNet',
        'GetLimitNet',
        'RemoveProxy',
        'GetProxyList',
        'GetProxyDetals',
        'CreateProxy',
        'ModifyProxy',
        'GetProxyFile',
        'SaveProxyFile',
        'ToBackup',
        'DelBackup',
        'GetSitePHPVersion',
        'logsOpen',
        'GetLogsStatus',
        'CloseHasPwd',
        'SetHasPwd',
        'GetHasPwd',
        'GetDnsApi',
        'SetDnsApi',
        'reset_wp_password',
        'is_update',
        'purge_all_cache',
        'set_fastcgi_cache',
        'update_wp',
        'get_wp_username',
        'get_language',
        'deploy_wp',
        # 网站管理新增
        'test_domains_api',
        'site_rname',
    )
    return publicObject(siteObject, defs, None, pdata)


@app.route('/ftp', methods=method_post)
def ftp(pdata=None):
    # FTP管理
    comReturn = comm.local()
    if comReturn: return comReturn
    import ftp
    ftpObject = ftp.ftp()
    defs = ('AddUser', 'DeleteUser', 'SetUserPassword', 'SetStatus', 'setPort',
            'set_user_home', 'get_login_logs', 'get_action_logs',
            'set_ftp_logs')
    return publicObject(ftpObject, defs, None, pdata)


@app.route('/database', methods=method_post)
def database(pdata=None):
    # 数据库管理
    comReturn = comm.local()
    if comReturn: return comReturn
    import database
    databaseObject = database.database()
    defs = ('GetdataInfo', 'check_del_data', 'get_database_size', 'GetInfo',
            'ReTable', 'OpTable', 'AlTable', 'GetSlowLogs', 'GetRunStatus',
            'SetDbConf', 'GetDbStatus', 'BinLog', 'GetErrorLog',
            'GetMySQLInfo', 'SetDataDir', 'SetMySQLPort', 'AddCloudDatabase',
            'AddDatabase', 'DeleteDatabase', 'SetupPassword',
            'ResDatabasePassword', 'ToBackup', 'DelBackup', 'AddCloudServer',
            'GetCloudServer', 'RemoveCloudServer', 'ModifyCloudServer',
            'InputSql', 'SyncToDatabases', 'SyncGetDatabases',
            'GetDatabaseAccess', 'SetDatabaseAccess', 'get_mysql_user',
            'check_mysql_ssl_status', 'write_ssl_to_mysql', 'GetdataInfo')
    return publicObject(databaseObject, defs, None, pdata)


@app.route('/acme', methods=method_all)
def acme(pdata=None):
    # Let's 证书管理
    comReturn = comm.local()
    if comReturn: return comReturn
    import acme_v2
    acme_v2_object = acme_v2.acme_v2()
    defs = ('get_orders', 'remove_order', 'get_order_find', 'revoke_order',
            'create_order', 'get_account_info', 'set_account_info',
            'update_zip', 'get_cert_init_api', 'get_auths', 'auth_domain',
            'check_auth_status', 'download_cert', 'apply_cert', 'renew_cert',
            'apply_cert_api', 'apply_dns_auth')
    return publicObject(acme_v2_object, defs, None, pdata)


# import panelMessage
# message_object = panelMessage.panelMessage()
# @app.route('/message/<action>', methods=method_all)
# def message(action=None):
#     # 提示消息管理
#     comReturn = comm.local()
#     if comReturn: return comReturn
#     import panelMessage
#     message_object = panelMessage.panelMessage()
#     defs = (
#     'get_messages', 'get_message_find', 'create_message', 'status_message', 'remove_message', 'get_messages_all')
#     return publicObject(message_object, defs, action, None)


@app.route('/api', methods=method_all)
def api(pdata=None):
    # APP使用的API接口管理
    comReturn = comm.local()
    if comReturn: return comReturn
    import panelApi
    api_object = panelApi.panelApi()
    defs = ('get_token', 'check_bind', 'get_bind_status', 'get_apps',
            'add_bind_app', 'remove_bind_app', 'set_token', 'get_tmp_token',
            'get_app_bind_status', 'login_for_app')
    return publicObject(api_object, defs, None, pdata)


@app.route('/firewall', methods=method_post)
def firewall(pdata=None):
    # 安全页面
    comReturn = comm.local()
    if comReturn: return comReturn
    import firewalls
    firewallObject = firewalls.firewalls()
    defs = ('GetList', 'AddDropAddress', 'DelDropAddress', 'FirewallReload',
            'SetFirewallStatus', 'AddAcceptPort', 'DelAcceptPort',
            'SetSshStatus', 'SetPing', 'SetSshPort', 'GetSshInfo',
            'SetFirewallStatus')
    return publicObject(firewallObject, defs, None, pdata)



@app.route('/ssh_security', methods=method_all)
def ssh_security(pdata=None):
    # SSH安全
    comReturn = comm.local()
    if comReturn: return comReturn
    if request.method == method_get[0] and not pdata and not request.args.get(
            'action', '') in ['download_key']:
        return index_new('ssh_security')
    import ssh_security
    firewallObject = ssh_security.ssh_security()
    is_csrf = True
    if request.args.get('action', '') in ['download_key']: is_csrf = False
    defs = ('san_ssh_security', 'set_password', 'set_sshkey', 'stop_key',
            'get_config', 'download_key', 'stop_password', 'get_key',
            'return_ip', 'add_return_ip', 'del_return_ip', 'start_jian',
            'stop_jian', 'get_jian', 'get_logs', 'set_root', 'stop_root',
            'start_auth_method', 'stop_auth_method', 'get_auth_method',
            'check_so_file', 'get_so_file', 'get_pin', 'set_login_send',
            'get_login_send', 'get_msg_push_list', 'clear_login_send')
    return publicObject(firewallObject, defs, None, pdata, is_csrf)


@app.route('/monitor', methods=method_all)
def panel_monitor(pdata=None):
    # 云控统计信息
    comReturn = comm.local()
    if comReturn: return comReturn
    import monitor
    dataObject = monitor.Monitor()
    defs = ('get_spider', 'get_exception', 'get_request_count_qps',
            'load_and_up_flow', 'get_request_count_by_hour')
    return publicObject(dataObject, defs, None, pdata)


@app.route('/san', methods=method_all)
def san_baseline(pdata=None):
    # 云控安全扫描
    comReturn = comm.local()
    if comReturn: return comReturn
    import san_baseline
    dataObject = san_baseline.san_baseline()
    defs = ('start', 'get_api_log', 'get_resut', 'get_ssh_errorlogin',
            'repair', 'repair_all')
    return publicObject(dataObject, defs, None, pdata)


@app.route('/password', methods=method_all)
def panel_password(pdata=None):
    # 云控密码管理
    comReturn = comm.local()
    if comReturn: return comReturn
    import password
    dataObject = password.password()
    defs = ('set_root_password', 'get_mysql_root', 'set_mysql_password',
            'set_panel_password', 'SetPassword', 'SetSshKey', 'StopKey',
            'GetConfig', 'StopPassword', 'GetKey', 'get_databses',
            'rem_mysql_pass', 'set_mysql_access', "get_panel_username")
    return publicObject(dataObject, defs, None, pdata)


@app.route('/warning', methods=method_all)
def panel_warning(pdata=None):
    # 首页安全警告
    comReturn = comm.local()
    if comReturn: return comReturn
    if public.get_csrf_html_token_key() in session and 'login' in session:
        if not check_csrf():
            return public.ReturnJson(False, 'INIT_CSRF_ERR'), json_header
    get = get_input()
    ikey = 'warning_list'
    import panelWarning
    dataObject = panelWarning.panelWarning()
    if get.action == 'get_list':
        result = cache.get(ikey)
        if not result or 'force' in get:
            result = json.loads('{"ignore":[],"risk":[],"security":[]}')
            try:
                defs = ("get_list",)
                result = publicObject(dataObject, defs, None, pdata)
                cache.set(ikey, result, 3600)
                return result
            except:
                pass
        return result

    defs = ('get_list', 'set_ignore', 'check_find', 'check_cve',
            'set_vuln_ignore', 'get_scan_bar', 'get_tmp_result',
            'kill_get_list')

    if get.action in ['set_ignore', 'check_find', 'set_vuln_ignore']:
        cache.delete(ikey)
    return publicObject(dataObject, defs, None, pdata)


@app.route('/bak', methods=method_all)
def backup_bak(pdata=None):
    # 云控备份服务
    comReturn = comm.local()
    if comReturn: return comReturn
    import backup_bak
    dataObject = backup_bak.backup_bak()
    defs = ('get_sites', 'get_databases', 'backup_database', 'backup_site',
            'backup_path', 'get_database_progress', 'get_site_progress',
            'down', 'get_down_progress', 'download_path', 'backup_site_all',
            'get_all_site_progress', 'backup_date_all',
            'get_all_date_progress')
    return publicObject(dataObject, defs, None, pdata)


@app.route('/abnormal', methods=method_all)
def abnormal(pdata=None):
    # 云控系统统计
    comReturn = comm.local()
    if comReturn: return comReturn
    import abnormal
    dataObject = abnormal.abnormal()
    defs = ('mysql_server', 'mysql_cpu', 'mysql_count', 'php_server',
            'php_conn_max', 'php_cpu', 'CPU', 'Memory', 'disk',
            'not_root_user', 'start')
    return publicObject(dataObject, defs, None, pdata)


@app.route('/project/<mod_name>/<def_name>/<stype>', methods=method_all)
def project(mod_name, def_name, stype=None):
    comReturn = comm.local()
    if comReturn: return comReturn
    from panelProjectController import ProjectController
    project_obj = ProjectController()
    defs = ('model',)
    get = get_input()
    get.action = 'model'
    get.mod_name = mod_name
    get.def_name = def_name
    get.stype = stype
    if stype == "html":
        return project_obj.model(get)
    return publicObject(project_obj, defs, None, get)


@app.route('/msg/<mod_name>/<def_name>', methods=method_all)
def msgcontroller(mod_name, def_name):
    comReturn = comm.local()
    if comReturn: return comReturn
    from MsgController import MsgController
    project_obj = MsgController()
    defs = ('model',)
    get = get_input()
    get.action = 'model'
    get.mod_name = mod_name
    get.def_name = def_name
    return publicObject(project_obj, defs, None, get)


# @app.route('/docker', methods=method_all)
# def docker(pdata=None):
#     comReturn = comm.local()
#     if comReturn: return comReturn
#     if request.method == method_get[0]:
#         import system
#         data = system.system().GetConcifInfo()
#         data['js_random'] = get_js_random()
#         data['lan'] = public.GetLan('files')
#         return render_template('docker.html', data=data)


# @app.route('/docker', methods=method_all)
# @app.route('/docker/<action>', methods=method_all)
# @app.route('/docker_ifame', methods=method_all)
# def docker(action=None, pdata=None):
#     if not public.is_bind():
#         return redirect('/bind', 302)
#     comReturn = comm.local()
#     if comReturn: return comReturn
#     if request.method == method_get[0]:
#         import system
#         data = system.system().GetConcifInfo()
#         data['js_random'] = get_js_random()
#         data['lan'] = public.GetLan('files')
#         return render_template('index1.html', data=data)


@app.route('/dbmodel/<mod_name>/<def_name>', methods=method_all)
def dbmodel(mod_name, def_name):
    comReturn = comm.local()
    if comReturn: return comReturn
    from panelDatabaseController import DatabaseController
    database_obj = DatabaseController()
    defs = ('model',)
    get = get_input()
    get.action = 'model'
    get.mod_name = mod_name
    get.def_name = def_name

    return publicObject(database_obj, defs, None, get)


@app.route('/files', methods=method_all)
def files(pdata=None):
    # 文件管理
    comReturn = comm.local()
    if comReturn: return comReturn
    if request.method == method_get[0] and not request.args.get('path') and not pdata:
        return index_new('files')
    import files
    filesObject = files.files()
    defs = ('files_search', 'files_replace', 'get_replace_logs',
            'get_images_resize', 'add_files_rsync', 'get_file_attribute',
            'get_file_hash', 'CreateLink', 'get_progress', 'restore_website',
            'fix_permissions', 'get_all_back', 'restore_path_permissions',
            'del_path_premissions', 'get_path_premissions',
            'back_path_permissions', 'upload_file_exists', 'CheckExistsFiles',
            'GetExecLog', 'GetSearch', 'ExecShell', 'GetExecShellMsg',
            'exec_git', 'exec_composer', 'create_download_url', 'UploadFile',
            'GetDir', 'GetDirNew','CreateFile', 'CreateDir', 'DeleteDir', 'DeleteFile',
            'get_download_url_list', 'remove_download_url',
            'modify_download_url', 'CopyFile', 'CopyDir', 'MvFile',
            'GetFileBody', 'SaveFileBody', 'Zip', 'UnZip',
            'get_download_url_find', 'set_file_ps', 'SearchFiles', 'upload',
            'read_history', 're_history', 'auto_save_temp',
            'get_auto_save_body', 'get_videos', 'GetFileAccess',
            'SetFileAccess', 'GetDirSize', 'SetBatchData', 'BatchPaste',
            'install_rar', 'get_path_size', 'DownloadFile', 'GetTaskSpeed',
            'CloseLogs', 'InstallSoft', 'UninstallSoft', 'SaveTmpFile',
            'get_composer_version', 'exec_composer', 'update_composer',
            'GetTmpFile', 'del_files_store', 'add_files_store',
            'get_files_store', 'del_files_store_types',
            'add_files_store_types', 'exec_git', 'RemoveTask', 'ActionTask',
            'Re_Recycle_bin', 'Get_Recycle_bin', 'Del_Recycle_bin',
            'Close_Recycle_bin', 'Recycle_bin', 'file_webshell_check',
            'dir_webshell_check', 'files_search', 'files_replace',
            'get_replace_logs')
    return publicObject(filesObject, defs, None, pdata)


@app.route('/crontab', methods=method_post)
def crontab(pdata=None):
    # 计划任务
    comReturn = comm.local()
    if comReturn: return comReturn
    import crontab
    crontabObject = crontab.crontab()
    defs = ('GetCrontab', 'AddCrontab', 'GetDataList', 'GetLogs', 'DelLogs',
            'DelCrontab', 'StartTask', 'set_cron_status', 'get_crond_find',
            'modify_crond', 'get_backup_list')
    return publicObject(crontabObject, defs, None, pdata)


@app.route('/config', methods=method_post)
def config(pdata=None):
    # 面板设置页面
    comReturn = comm.local()
    if comReturn: return comReturn

    import config
    defs = (
        'send_by_telegram',
        'set_empty',
        'set_backup_notification',
        'get_panel_ssl_status',
        'set_file_deny',
        'del_file_deny',
        'get_file_deny',
        'set_improvement',
        'get_httpd_access_log_format_parameter',
        'set_httpd_format_log_to_website',
        'get_httpd_access_log_format',
        'del_httpd_access_log_format',
        'add_httpd_access_log_format',
        'get_nginx_access_log_format_parameter',
        'set_format_log_to_website',
        'get_nginx_access_log_format',
        'del_nginx_access_log_format',
        'set_click_logs',
        'get_node_config',
        'add_nginx_access_log_format',
        'get_ols_private_cache_status',
        'get_ols_value',
        'set_ols_value',
        'set_node_config',
        'get_ols_private_cache',
        'get_ols_static_cache',
        'set_ols_static_cache',
        'switch_ols_private_cache',
        'set_ols_private_cache',
        'set_coll_open',
        'get_qrcode_data',
        'check_two_step',
        'set_two_step_auth',
        'create_user',
        'remove_user',
        'modify_user',
        'get_key',
        'get_php_session_path',
        'set_php_session_path',
        'get_cert_source',
        'get_users',
        'set_request_iptype',
        'set_local',
        'set_debug',
        'get_panel_error_logs',
        'clean_panel_error_logs',
        'get_menu_list',
        'set_hide_menu_list',
        'get_basic_auth_stat',
        'set_basic_auth',
        'get_cli_php_version',
        'get_tmp_token',
        'get_temp_login',
        'set_temp_login',
        'remove_temp_login',
        'clear_temp_login',
        'get_temp_login_logs',
        'set_cli_php_version',
        'DelOldSession',
        'GetSessionCount',
        'SetSessionConf',
        'set_not_auth_status',
        'GetSessionConf',
        'get_ipv6_listen',
        'set_ipv6_status',
        'GetApacheValue',
        'SetApacheValue',
        'install_msg_module',
        'GetNginxValue',
        'SetNginxValue',
        'get_token',
        'set_token',
        'set_admin_path',
        'is_pro',
        'set_msg_config',
        'get_php_config',
        'get_config',
        'SavePanelSSL',
        'GetPanelSSL',
        'GetPHPConf',
        'SetPHPConf',
        'uninstall_msg_module',
        'GetPanelList',
        'AddPanelInfo',
        'SetPanelInfo',
        'DelPanelInfo',
        'ClickPanelInfo',
        'SetPanelSSL',
        'get_msg_configs',
        'SetTemplates',
        'Set502',
        'setPassword',
        'setUsername',
        'setPanel',
        'setPathInfo',
        'setPHPMaxSize',
        'get_msg_fun',
        'getFpmConfig',
        'setFpmConfig',
        'setPHPMaxTime',
        'syncDate',
        'setPHPDisable',
        'SetControl',
        'get_settings2',
        'del_tg_info',
        'set_tg_bot',
        'ClosePanel',
        'AutoUpdatePanel',
        'SetPanelLock',
        'return_mail_list',
        'del_mail_list',
        'add_mail_address',
        'user_mail_send',
        'get_user_mail',
        'set_dingding',
        'get_dingding',
        'get_settings',
        'user_stmp_mail_send',
        'user_dingding_send',
        'get_login_send',
        'set_login_send',
        'clear_login_send',
        'get_login_log',
        'login_ipwhite',
        'set_ssl_verify',
        'get_ssl_verify',
        'get_password_config',
        'set_password_expire',
        'set_password_safe',
        'get_module_template',
        # 新增nps评分
        'write_nps_new',
        'get_nps_new',
        "check_nps",
        # 提交报错信息 # 错误收集
        'err_collection',
        # 语言包 测试接口
        # 'get_language',
        # 'get_languageinfo',
        'set_language',
        'download_language',
        'upload_language',
        # 'test_language',
         'set_hou',
         'replace_data',
        'set_theme',
    )
    return publicObject(config.config(), defs, None, pdata)


@app.route('/config', methods=method_get)
def config_old(pdata=None):
    # 面板设置页面
    comReturn = comm.local()
    if comReturn: return comReturn

    import system, wxapp, config
    c_obj = config.config()
    data = system.system().GetConcifInfo()
    data['lan'] = public.GetLan('config')
    try:
        data['wx'] = wxapp.wxapp().get_user_info(None)['msg']
    except:
        data['wx'] = 'INIT_WX_NOT_BIND'
    data['api'] = ''
    data['ipv6'] = ''
    sess_out_path = 'data/session_timeout.pl'
    if not os.path.exists(sess_out_path):
        public.writeFile(sess_out_path, '86400')
    s_time_tmp = public.readFile(sess_out_path)
    if not s_time_tmp: s_time_tmp = '0'
    data['session_timeout'] = int(s_time_tmp)
    if c_obj.get_ipv6_listen(None): data['ipv6'] = 'checked'
    if c_obj.get_token(None)['open']: data['api'] = 'checked'
    data['basic_auth'] = c_obj.get_basic_auth_stat(None)
    data['status_code'] = c_obj.get_not_auth_status()
    data['basic_auth']['value'] = public.getMsg('CLOSED')
    if data['basic_auth']['open']:
        data['basic_auth']['value'] = public.getMsg('OPENED')
    data['debug'] = ''
    data['js_random'] = get_js_random()
    if app.config['DEBUG']: data['debug'] = 'checked'
    data['is_local'] = ''
    if public.is_local(): data['is_local'] = 'checked'
    data['public_key'] = public.get_rsa_public_key().replace("\n", "")
    return render_template('config.html', data=data)


@app.route('/ajax', methods=method_all)
def ajax(pdata=None):
    # 面板系统服务状态接口
    comReturn = comm.local()
    if comReturn: return comReturn
    import ajax
    ajaxObject = ajax.ajax()
    defs = ('get_lines', 'php_info', 'change_phpmyadmin_ssl_port',
            'set_phpmyadmin_ssl', 'get_phpmyadmin_ssl', 'get_pd',
            'check_user_auth', 'to_not_beta', 'get_beta_logs', 'apple_beta',
            'GetApacheStatus', 'GetCloudHtml', 'get_pay_type',
            'get_load_average', 'GetOpeLogs', 'GetFpmLogs', 'GetFpmSlowLogs',
            'SetMemcachedCache', 'GetMemcachedStatus', 'GetRedisStatus',
            'GetWarning', 'SetWarning', 'CheckLogin', 'GetSpeed', 'GetAd',
            'phpSort', 'ToPunycode', 'GetBetaStatus', 'SetBeta',
            'setPHPMyAdmin', 'delClose', 'KillProcess', 'GetPHPInfo',
            'GetQiniuFileList', 'get_process_tops', 'get_process_cpu_high',
            'UninstallLib', 'InstallLib', 'SetQiniuAS', 'GetQiniuAS',
            'GetLibList', 'GetProcessList', 'GetNetWorkList', 'GetNginxStatus',
            'GetPHPStatus', 'GetTaskCount', 'GetSoftList', 'GetNetWorkIo',
            'GetDiskIo', 'GetCpuIo', 'CheckInstalled', 'UpdatePanel',
            'GetInstalled', 'GetPHPConfig', 'SetPHPConfig', 'log_analysis',
            'speed_log', 'get_result', 'get_detailed', 'ignore_version')

    return publicObject(ajaxObject, defs, None, pdata)


@app.route('/system', methods=method_all)
def system(pdata=None):
    # 面板系统状态接口
    comReturn = comm.local()
    if comReturn: return comReturn
    import system
    sysObject = system.system()
    defs = ('get_io_info', 'UpdatePro', 'GetAllInfo', 'GetNetWorkApi',
            'GetLoadAverage', 'ClearSystem', 'GetNetWorkOld', 'GetNetWork',
            'GetDiskInfo', 'GetCpuInfo', 'GetBootTime', 'GetSystemVersion',
            'GetMemInfo', 'GetSystemTotal', 'GetConcifInfo', 'ServiceAdmin',
            'ReWeb', 'RestartServer', 'ReMemory', 'RepPanel')
    return publicObject(sysObject, defs, None, pdata)


@app.route('/deployment', methods=method_all)
def deployment(pdata=None):
    # 一键部署接口
    comReturn = comm.local()
    if comReturn: return comReturn
    import plugin_deployment
    sysObject = plugin_deployment.plugin_deployment()
    defs = ('GetList', 'AddPackage', 'DelPackage', 'SetupPackage', 'GetSpeed',
            'GetPackageOther')
    return publicObject(sysObject, defs, None, pdata)


@app.route('/data', methods=method_all)
@app.route('/panel_data', methods=method_all)
def panel_data(pdata=None):
    # 从数据库获取数据接口
    comReturn = comm.local()
    if comReturn: return comReturn
    import data
    dataObject = data.data()
    defs = ('setPs', 'getData', 'getFind', 'getKey')
    return publicObject(dataObject, defs, None, pdata)


@app.route('/ssl', methods=method_all)
def ssl(pdata=None):
    # 商业SSL证书申请接口
    comReturn = comm.local()
    if comReturn: return comReturn
    import panelSSL
    toObject = panelSSL.panelSSL()
    defs = (
        'check_url_txt', 'RemoveCert', 'renew_lets_ssl', 'SetCertToSite', 'GetCertList',
        'SaveCert', 'GetCert', 'GetCertName', 'again_verify', 'DelToken', 'GetToken',
        'GetUserInfo', 'GetOrderList', 'GetDVSSL', 'Completed', 'SyncOrder', 'download_cert',
        'set_cert', 'cancel_cert_order', 'get_order_list', 'get_order_find', 'apply_order_pay',
        'get_pay_status', 'apply_order', 'get_verify_info', 'get_verify_result', 'get_product_list',
        'set_verify_info', 'GetSSLInfo', 'downloadCRT', 'GetSSLProduct', 'Renew_SSL', 'Get_Renew_SSL',
        # 新增 购买证书对接接口
        'get_product_list_v2', 'apply_cert_order_pay', 'get_cert_admin', 'apply_order_ca',
        'apply_cert_install_pay',
        # 'pay_test'
    )
    get = get_input()

    if get.action == 'download_cert':
        from io import BytesIO
        import base64
        result = toObject.download_cert(get)

        fp = BytesIO(base64.b64decode(result['res']['data']))
        return send_file(fp,
                         download_name=result['res']['filename'],
                         as_attachment=True,
                         mimetype='application/zip')
    result = publicObject(toObject, defs, get.action, get)
    return result


@app.route('/task', methods=method_all)
def task(pdata=None):
    # 后台任务接口
    comReturn = comm.local()
    if comReturn: return comReturn
    import panelTask
    toObject = panelTask.bt_task()
    defs = ('get_task_lists', 'remove_task', 'get_task_find',
            "get_task_log_by_id")
    result = publicObject(toObject, defs, None, pdata)
    return result


@app.route('/plugin', methods=method_all)
def plugin(pdata=None):
    # 插件系统接口
    comReturn = comm.local()
    if comReturn: return comReturn
    import panelPlugin
    pluginObject = panelPlugin.panelPlugin()
    defs = ('get_usually_plugin', 'check_install_limit', 'set_score',
            'get_score', 'update_zip', 'input_zip', 'export_zip', 'add_index',
            'remove_index', 'sort_index', 'install_plugin', 'uninstall_plugin',
            'get_soft_find', 'get_index_list', 'get_soft_list',
            'get_cloud_list', 'check_deps', 'flush_cache', 'GetCloudWarning',
            'install', 'unInstall', 'getPluginList', 'getPluginInfo',
            'get_make_args', 'add_make_args', 'getPluginStatus',
            'setPluginStatus', 'a', 'getCloudPlugin', 'getConfigHtml',
            'savePluginSort', 'del_make_args', 'set_make_args')
    return publicObject(pluginObject, defs, None, pdata)


@app.route('/wxapp', methods=method_all)
@app.route('/panel_wxapp', methods=method_all)
def panel_wxapp(pdata=None):
    # 微信小程序绑定接口
    comReturn = comm.local()
    if comReturn: return comReturn
    import wxapp
    toObject = wxapp.wxapp()
    defs = ('blind', 'get_safe_log', 'blind_result', 'get_user_info',
            'blind_del', 'blind_qrcode')
    result = publicObject(toObject, defs, None, pdata)
    return result


@app.route('/auth', methods=method_all)
def auth(pdata=None):
    # 面板认证接口
    comReturn = comm.local()
    if comReturn: return comReturn
    import panelAuth
    toObject = panelAuth.panelAuth()
    defs = ('free_trial', 'renew_product_auth', 'auth_activate',
            'get_product_auth', 'get_product_auth_all','get_stripe_session_id',
            'get_re_order_status_plugin', 'create_plugin_other_order',
            'get_order_stat', 'get_voucher_plugin','get_voucher_plugin_all',
            'create_order_voucher_plugin', 'get_product_discount_by',
            'get_re_order_status', 'create_order_voucher', 'create_order',
            'get_order_status', 'get_voucher', 'flush_pay_status',
            'create_serverid', 'check_serverid', 'get_plugin_list',
            'check_plugin', 'get_buy_code', 'check_pay_status',
            'get_renew_code', 'check_renew_code', 'get_business_plugin',
            'get_ad_list', 'check_plugin_end', 'get_plugin_price',
            'get_plugin_remarks', 'get_paypal_session_id',
            'check_paypal_status')
    result = publicObject(toObject, defs, None, pdata)
    return result


@app.route('/download', methods=method_get)
def download():
    # 文件下载接口
    comReturn = comm.local()
    if comReturn: return comReturn
    filename = request.args.get('filename')
    if filename.find('|') != -1:
        filename = filename.split('|')[1]
    if not filename:
        return public.ReturnJson(False, "INIT_ARGS_ERR"), json_header

    if filename in [
        'alioss', 'qiniu', 'upyun', 'txcos', 'ftp', 'msonedrive',
        'gcloud_storage', 'gdrive', 'aws_s3', 'obs', 'bos'
    ]:
        return panel_cloud(False)

    import html
    filepath = html.unescape(filename.replace('\x00', ''))
    if '..' in filepath.split('/') or '..' in filepath.split('\\'):
        return public.ReturnJson(False, "INVALID PATH"), json_header
    filename = os.path.abspath(filepath)

    if not os.path.exists(filename):
        return public.ReturnJson(False, "File not exists"), json_header
    if os.path.isdir(filename):
        return public.ReturnJson(False, "The catalog is not downloadable"), json_header

    try:
        import stat
        file_stat = os.stat(filename)
        if stat.S_ISSOCK(file_stat.st_mode):
            return public.ReturnJson(False, "Unix domain socket files are not downloadable"), json_header
        elif stat.S_ISCHR(file_stat.st_mode):
            return public.ReturnJson(False, "Character device files cannot be downloaded"), json_header
        elif stat.S_ISBLK(file_stat.st_mode):
            return public.ReturnJson(False, "Block device files are not downloadable"), json_header
        elif stat.S_ISFIFO(file_stat.st_mode):
            return public.ReturnJson(False, "FIFO pipeline files are not downloadable"), json_header
    except:
        pass



    if request.args.get('play') == 'true':
        import panelVideo
        start, end = panelVideo.get_range(request)
        g.return_message = True
        return panelVideo.partial_response(filename, start, end)
    else:
        mimetype = "application/octet-stream"
        extName = filename.split('.')[-1]
        if extName in ['png', 'gif', 'jpeg', 'jpg']: mimetype = None
        public.WriteLog("TYPE_FILE", 'FILE_DOWNLOAD',
                        (filename, public.GetClientIp()))
        g.return_message = True
        if not os.path.exists(filename):
            return public.ReturnJson(False, "File not exists"), json_header
        return send_file(filename,
                         mimetype=mimetype,
                         as_attachment=True,
                         etag=True,
                         conditional=True,
                         download_name=os.path.basename(filename),
                         max_age=0)


@app.route('/cloud', methods=method_all)
def panel_cloud(is_csrf=True):
    # 从对像存储下载备份文件接口
    comReturn = comm.local()
    if comReturn: return comReturn
    if is_csrf:
        if not check_csrf():
            return public.ReturnJson(False, 'INIT_CSRF_ERR'), json_header
    get = get_input()
    _filename = get.filename
    plugin_name = ""
    if _filename.find('|') != -1:
        plugin_name = get.filename.split('|')[1]
    else:
        plugin_name = get.filename

    if not os.path.exists('plugin/' + plugin_name + '/' + plugin_name +
                          '_main.py'):
        return public.returnJson(
            False, 'The specified plugin does not exist!'), json_header
    public.package_path_append('plugin/' + plugin_name)
    plugin_main = __import__(plugin_name + '_main')
    public.mod_reload(plugin_main)
    tmp = eval("plugin_main.%s_main()" % plugin_name)
    if not hasattr(tmp, 'download_file'):
        return public.returnJson(
            False,
            'Specified plugin has no file download function!'), json_header
    download_url = tmp.download_file(get.name)
    if plugin_name == 'ftp':
        if download_url.find("ftp") != 0:
            download_url = "ftp://" + download_url
    else:
        if download_url.find('http') != 0:
            download_url = 'http://' + download_url

    if "toserver" in get and get.toserver == "true":
        download_dir = "/tmp/"
        if "download_dir" in get:
            download_dir = get.download_dir
        local_file = os.path.join(download_dir, get.name)

        input_from_local = False
        if "input_from_local" in get:
            input_from_local = True if get.input_from_local == "true" else False

        if input_from_local:
            if os.path.isfile(local_file):
                return {
                    "status": True,
                    "msg":
                        "The file already exists and will be restored locally.",
                    "task_id": -1,
                    "local_file": local_file
                }
        from panelTask import bt_task
        task_obj = bt_task()
        task_id = task_obj.create_task('Download file', 1, download_url,
                                       local_file)
        return {
            "status": True,
            "msg": "The download task was created successfully",
            "local_file": local_file,
            "task_id": task_id
        }

    return redirect(download_url)


@app.route('/btwaf_error', methods=method_get)
def btwaf_error():
    # 图标
    comReturn = comm.local()
    if comReturn: return comReturn
    get = get_input()
    p_path = os.path.join('/www/server/panel/plugin/', "btwaf")
    if not os.path.exists(p_path):
        if get.name == 'btwaf' and get.fun == 'index':
            return render_template('error3.html', data={})
    return render_template('error3.html', data={})


@app.route('/favicon.ico', methods=method_get)
def send_favicon():
    # 图标
    comReturn = comm.local()
    if comReturn: return abort(404)
    s_file = '/www/server/panel/BTPanel/static/favicon.ico'
    if not os.path.exists(s_file): return abort(404)
    return send_file(s_file, conditional=True, etag=True)


@app.route('/rspamd', defaults={'path': ''}, methods=method_all)
@app.route('/rspamd/<path:path>', methods=method_all)
def proxy_rspamd_requests(path):
    comReturn = comm.local()
    if comReturn: return comReturn
    param = str(request.url).split('?')
    param = "" if len(param) < 2 else param[-1]
    import requests
    headers = {}
    for h in request.headers.keys():
        headers[h] = request.headers[h]
    if request.method == "GET":
        if re.search(r"\.(js|css)$", path):
            return send_file('/usr/share/rspamd/www/rspamd/' + path,
                             conditional=True,
                             etag=True)
        if path == "/":
            return send_file('/usr/share/rspamd/www/rspamd/',
                             conditional=True,
                             etag=True)
        url = "http://127.0.0.1:11334/rspamd/" + path + "?" + param
        for i in [
            'stat', 'auth', 'neighbours', 'list_extractors',
            'list_transforms', 'graph', 'maps', 'actions', 'symbols',
            'history', 'errors', 'check_selector', 'saveactions',
            'savesymbols', 'getmap'
        ]:
            if i in path:
                url = "http://127.0.0.1:11334/" + path + "?" + param
        if os.path.exists('/etc/rspamd/passwd'):
            headers['Password'] = public.readFile('/etc/rspamd/passwd')
        req = requests.get(url, headers=headers, stream=True)
        return Resp(stream_with_context(req.iter_content()),
                    content_type=req.headers['content-type'], status=req.status_code)
    else:
        url = "http://127.0.0.1:11334/" + path
        for i in request.form.keys():
            data = '{}='.format(i)
        # public.writeFile('/tmp/2',data+"\n","a+")
        req = requests.post(url, data=data, headers=headers, stream=True)
        return Resp(stream_with_context(req.iter_content()),
                    content_type=req.headers['content-type'])


@app.route('/tips', methods=method_get)
def tips():
    # 提示页面
    comReturn = comm.local()
    if comReturn: return abort(404)
    get = get_input()
    if len(get.get_items().keys()) > 1: return abort(404)
    return render_template('tips.html')


# ======================普通路由区============================#

# ======================严格排查区域============================#

route_path = os.path.join(admin_path, '')
if not route_path: route_path = '/'
if route_path[-1] == '/': route_path = route_path[:-1]
if route_path[0] != '/': route_path = '/' + route_path


@app.route('/login', methods=method_all)
@app.route(route_path, methods=method_all)
@app.route(route_path + '/', methods=method_all)
def login():
    # 面板登录接口
    if os.path.exists('install.pl'): return redirect('/install')
    global admin_check_auth, admin_path, route_path
    is_auth_path = False
    if admin_path != '/bt' and os.path.exists(
            admin_path_file) and not 'admin_auth' in session:
        is_auth_path = True
    # 登录输入验证
    if request.method == method_post[0]:
        #防爆破检测
        import breaking_through
        _breaking_through_obj = breaking_through.main()
        limit_login = _breaking_through_obj.get_login_limit()
        if limit_login:
            return public.return_msg_gettext(False, 'Aapanel explosion-proof limit, cancel command: bt 33'), json_header

        if is_auth_path:
            g.auth_error = True
            return public.error_not_login(None)
        v_list = ['username', 'password', 'code', 'vcode', 'cdn_url']
        for v in v_list:
            if v in ['username', 'password']: continue
            pv = request.form.get(v, '').strip()
            if v == 'cdn_url':
                if len(pv) > 32:
                    return public.return_msg_gettext(
                        False, 'Wrong parameter length!'), json_header
                if not re.match(r"^[\w\.-]+$", pv):
                    public.return_msg_gettext(
                        False, 'Wrong parameter format!'), json_header
                continue

            if not pv: continue
            p_len = 32
            if v == 'code': p_len = 4
            if v == 'vcode': p_len = 6
            if len(pv) != p_len:
                if v == 'code':
                    return public.returnJson(
                        False, 'Verification code length error!'), json_header
                return public.returnJson(
                    False, 'Wrong parameter length!'), json_header
            if not re.match(r"^\w+$", pv):
                return public.returnJson(
                    False, 'Wrong parameter format!'), json_header
        for n in request.form.keys():

            if not n in v_list:
                return public.returnJson(
                    False,
                    'There can be no extra parameters in the login parameters'
                ), json_header

    get = get_input()
    import userlogin
    if hasattr(get, 'tmp_token'):
        result = userlogin.userlogin().request_tmp(get)
        return is_login(result)

    # 过滤爬虫
    if public.is_spider(): return abort(404)
    if hasattr(get, 'dologin'):
        login_path = '/login'
        if not 'login' in session: return redirect(login_path)
        if os.path.exists(admin_path_file): login_path = route_path
        if session['login'] != False:
            session['login'] = False
            cache.set('dologin', True)
            public.write_log_gettext(
                'Logout', 'Client: {}, has manually exited the panel',
                (public.GetClientIp() + ":" +
                 str(request.environ.get('REMOTE_PORT')),))
            if 'tmp_login_expire' in session:
                s_file = 'data/session/{}'.format(session['tmp_login_id'])
                if os.path.exists(s_file):
                    os.remove(s_file)
            token_key = public.get_csrf_html_token_key()
            if token_key in session:
                del (session[token_key])
            session.clear()
            sess_file = 'data/sess_files/' + public.get_sess_key()
            if os.path.exists(sess_file):
                try:
                    os.remove(sess_file)
                except:
                    pass
            sess_tmp_file = public.get_full_session_file()
            if os.path.exists(sess_tmp_file): os.remove(sess_tmp_file)
            g.dologin = True
            return redirect(public.get_admin_path())

    if is_auth_path:
        if route_path != request.path and route_path + '/' != request.path:
            referer = request.headers.get('Referer', 'err')
            referer_tmp = referer.split('/')
            referer_path = referer_tmp[-1]
            if referer_path == '':
                referer_path = referer_tmp[-2]
            if route_path != '/' + referer_path:
                g.auth_error = True
                # return render_template('autherr.html')
                return public.error_not_login(None)

    session['admin_auth'] = True

    comReturn = common.panelSetup().init()
    if comReturn:
        return comReturn

    if request.method == method_post[0]:
        result = userlogin.userlogin().request_post(get)
        return is_login(result)

    if request.method == method_get[0]:
        result = userlogin.userlogin().request_get(get)
        if result:
            return result
        data = {}
        data['lan'] = public.GetLan('login')
        data['hosts'] = '[]'
        hosts_file = 'plugin/static_cdn/hosts.json'
        if os.path.exists(hosts_file):
            data['hosts'] = public.get_cdn_hosts()
            if type(data['hosts']) == dict:
                data['hosts'] = '[]'
            else:
                data['hosts'] = json.dumps(data['hosts'])
        data['app_login'] = os.path.exists('data/app_login.pl')
        public.cache_set(
            public.Md5(
                uuid.UUID(int=uuid.getnode()).hex[-12:] +
                public.GetClientIp()), 'check', 360)

        # 生成登录token
        last_key = 'last_login_token'
        # -----------
        last_time_key = 'last_login_token_time'
        s_time = int(time.time())
        if last_key in session and last_time_key in session:
            # 10秒内不重复生成token
            if s_time - session[last_time_key] > 10:
                session[last_key] = public.GetRandomString(32)
                session[last_time_key] = s_time
        else:
            session[last_key] = public.GetRandomString(32)
            session[last_time_key] = s_time

        data[last_key] = session[last_key]
        import base64
        data['login_translations'] = base64.b64encode(json.dumps(load_login_translations()).encode()).decode()
        settings = '{}/BTPanel/languages/settings.json'.format(public.get_panel_path())
        # default = json.loads(public.readFile(settings))['default']

        settings_content = public.readFile(settings)
        try:
            if settings_content and settings_content.strip():
                settings_json = json.loads(settings_content)
            else:
                settings_json = {}
        except Exception as e:
            settings_json = {}

        default = settings_json.get('default', 'en')  # 默认值


        if default == '':
            default = 'en'
        data['login_lang'] = default if default else 'en'
        data['public_key'] = public.get_rsa_public_key()




        import userLang
        get_language = userLang.userLang().get_language(None)['message']
        data['language'] = get_language['default']
        data['language_list'] = get_language['languages']

        return render_template('login.html', data=data)
        # -----------

        # rsa_key = 'public_key'
        # session[last_key] = public.GetRandomString(32)
        # data[last_key] = session[last_key]
        # data[rsa_key] = public.get_rsa_public_key().replace("\n", "")
        # return render_template('login.html', data=data)


# 新增面板内注册
@app.route('/userRegister', methods=method_all)
def userRegister():
    comReturn = comm.local()
    if comReturn: return comReturn
    import userRegister
    reg = userRegister.userRegister()
    defs = ('toRegister',)

    return publicObject(reg, defs, None, None)



@app.route('/close', methods=method_get)
def close():
    # 面板已关闭页面
    if not os.path.exists('data/close.pl'): return redirect('/')
    data = {}
    data['lan'] = public.getLan('close')
    return render_template('close.html', data=data)


@app.route('/get_app_bind_status', methods=method_all)
def get_app_bind_status(pdata=None):
    # APP绑定状态查询
    if not public.check_app('app_bind'): return abort(404)
    get = get_input()
    if len(get.get_items().keys()) > 2: return 'There are meaningless parameters!'
    v_list = ['bind_token', 'data']
    for n in get.get_items().keys():
        if not n in v_list:
            return public.returnJson(
                False, 'There can be no redundant parameters'), json_header
    import panelApi
    api_object = panelApi.panelApi()
    return json.dumps(api_object.get_app_bind_status(get_input())), json_header


@app.route('/check_bind', methods=method_all)
def check_bind(pdata=None):
    # APP绑定查询
    if not public.check_app('app_bind'): return abort(404)
    get = get_input()
    if len(get.get_items().keys()) > 4: return 'There are meaningless parameters!'
    v_list = ['bind_token', 'client_brand', 'client_model', 'data']
    for n in get.get_items().keys():
        if not n in v_list:
            return public.returnJson(
                False, 'There can be no redundant parameters'), json_header
    import panelApi
    api_object = panelApi.panelApi()
    return json.dumps(api_object.check_bind(get_input())), json_header


@app.route('/code', methods=method_get)
def code():
    if not 'code' in session: return ''
    if not session['code']: return ''
    # 获取图片验证码
    try:
        import vilidate
    except:
        public.ExecShell("btpip install Pillow -I")
        return "Pillow not install!"
    vie = vilidate.vieCode()
    codeImage = vie.GetCodeImage(80, 4)
    if sys.version_info[0] == 2:
        try:
            from cStringIO import StringIO
        except:
            from StringIO import StringIO
        out = StringIO()
    else:
        from io import BytesIO
        out = BytesIO()
    codeImage[0].save(out, "png")
    cache.set("codeStr", public.md5("".join(codeImage[1]).lower()), 180)
    cache.set("codeOut", 1, 0.1)
    out.seek(0)
    return send_file(out, mimetype='image/png', max_age=0)


@app.route('/down/<token>', methods=method_all)
def down(token=None, fname=None):
    # 文件分享对外接口
    try:
        if public.M('download_token').count() == 0: return abort(404)
        fname = request.args.get('fname')
        if fname:
            if (len(fname) > 256): return abort(404)
        if fname: fname = fname.strip('/')
        if not token: return abort(404)
        if len(token) > 48: return abort(404)
        char_list = [
            '\\', '/', ':', '*', '?', '"', '<', '>', '|', ';', '&', '`'
        ]
        for char in char_list:
            if char in token: return abort(404)
        if not request.args.get('play') in ['true', None, '']:
            return abort(404)
        args = get_input()
        v_list = ['fname', 'play', 'file_password', 'data']
        for n in args.get_items().keys():
            if not n in v_list:
                return public.returnJson(
                    False, 'There can be no redundant parameters'), json_header
        if not re.match(r"^[\w\.]+$", token): return abort(404)
        find = public.M('download_token').where('token=?', (token,)).find()

        if not find: return abort(404)
        if time.time() > int(find['expire']): return abort(404)

        if not os.path.exists(find['filename']): return abort(404)
        if find['password'] and not token in session:
            if 'file_password' in args:
                if not re.match(r"^\w+$", args.file_password):
                    return public.ReturnJson(False,
                                             'Wrong password!'), json_header
                if re.match(r"^\d+$", args.file_password):
                    args.file_password = str(int(args.file_password))
                    args.file_password += ".0"
                if args.file_password != str(find['password']):
                    return public.ReturnJson(False,
                                             'Wrong password!'), json_header
                session[token] = 1
                session['down'] = True
            else:
                pdata = {
                    "to_path": "",
                    "src_path": find['filename'],
                    "password": True,
                    "filename": find['filename'].split('/')[-1],
                    "ps": find['ps'],
                    "total": find['total'],
                    "token": find['token'],
                    "expire": public.format_date(times=find['expire'])
                }
                session['down'] = True
                return render_template('down.html', data=pdata)

        if not find['password']:
            session['down'] = True
            session[token] = 1

        if session[token] != 1:
            return abort(404)

        filename = find['filename']
        if fname:
            filename = os.path.join(filename, fname)
            if not public.path_safe_check(fname, False): return abort(404)
            if os.path.isdir(filename):
                return get_dir_down(filename, token, find)
        else:
            if os.path.isdir(filename):
                return get_dir_down(filename, token, find)

        if request.args.get('play') == 'true':
            import panelVideo
            start, end = panelVideo.get_range(request)
            return panelVideo.partial_response(filename, start, end)
        else:
            mimetype = "application/octet-stream"
            extName = filename.split('.')[-1]
            if extName in ['png', 'gif', 'jpeg', 'jpg']: mimetype = None
            b_name = os.path.basename(filename)
            return send_file(filename,
                             mimetype=mimetype,
                             as_attachment=True,
                             download_name=b_name,
                             max_age=0)
    except:
        return abort(404)


@app.route('/database/mongodb/<def_name>', methods=method_all)
@app.route('/database/pgsql/<def_name>', methods=method_all)
@app.route('/database/redis/<def_name>', methods=method_all)
@app.route('/database/sqlite/<def_name>', methods=method_all)
@app.route('/database/sqlserver/<def_name>', methods=method_all)
def databaseModel(def_name):
    if request.method not in ['GET', 'POST']: return
    path_split = request.path.split("/")
    if len(path_split) < 4: return
    comReturn = comm.local()
    if comReturn: return comReturn
    from panelDatabaseController import DatabaseController
    project_obj = DatabaseController()
    defs = ('model',)
    get = get_input()
    get.action = 'model'
    get.mod_name = path_split[2]
    get.def_name = def_name

    return publicObject(project_obj, defs, None, get)


# 系统安全模型页面
@app.route('/safe/firewall/<def_name>', methods=method_all)
@app.route('/safe/freeip/<def_name>', methods=method_all)
@app.route('/safe/ips/<def_name>', methods=method_all)
@app.route('/safe/security/<def_name>', methods=method_all)
@app.route('/safe/ssh/<def_name>', methods=method_all)
@app.route('/safe/syslog/<def_name>', methods=method_all)
def safeModel(def_name):
    if request.method not in ['GET', 'POST']: return
    path_split = request.path.split("/")
    if len(path_split) < 4: return
    comReturn = comm.local()
    if comReturn: return comReturn
    from panelSafeController import SafeController
    project_obj = SafeController()
    defs = ('model',)
    get = get_input()
    get.action = 'model'
    get.mod_name = path_split[2]
    get.def_name = def_name

    return publicObject(project_obj, defs, None, get)


# 通用模型路由
@app.route('/<index>/<mod_name>/<def_name>', methods=method_all)
def allModule(index, mod_name, def_name):
    comReturn = comm.local()
    if comReturn: return comReturn
    p_path = public.get_plugin_path() + '/' + index
    if os.path.exists(p_path):
        return panel_other(index, mod_name, def_name)

    from panelController import Controller
    controller_obj = Controller()
    defs = ('model',)
    get = get_input()
    get.model_index = index
    get.action = 'model'
    get.mod_name = mod_name
    get.def_name = def_name

    return publicObject(controller_obj, defs, None, get)


@app.route('/public', methods=method_all)
def panel_public():
    get = get_input()
    if len("{}".format(get.get_items())) > 1024 * 32:
        return 'ERROR'

    # 获取ping测试
    if 'get_ping' in get:
        try:
            import panelPing
            p = panelPing.Test()
            get = p.check(get)
            if not get: return 'ERROR'
            result = getattr(p, get['act'])(get)
            result_type = type(result)
            if str(result_type).find('Response') != -1: return result
            return public.getJson(result), json_header
        except:
            return abort(404)

    if public.cache_get(
            public.Md5(
                uuid.UUID(int=uuid.getnode()).hex[-12:] +
                public.GetClientIp())) != 'check':
        return abort(404)
    global admin_check_auth, admin_path, route_path, admin_path_file
    if admin_path != '/bt' and os.path.exists(
            admin_path_file) and not 'admin_auth' in session:
        return abort(404)
    v_list = ['fun', 'name', 'filename', 'data', 'secret_key']
    for n in get.get_items().keys():
        if not n in v_list:
            return abort(404)

    get.client_ip = public.GetClientIp()
    num_key = get.client_ip + '_wxapp'
    if not public.get_error_num(num_key, 10):
        return public.return_msg_gettext(
            False,
            '10 consecutive authentication failures are prohibited for 1 hour')
    if not hasattr(get, 'name'): get.name = ''
    if not hasattr(get, 'fun'): return abort(404)
    if not public.path_safe_check("%s/%s" % (get.name, get.fun)):
        return abort(404)
    if get.fun in ['login_qrcode', 'is_scan_ok', 'set_login']:
        # 检查是否验证过安全入口
        if admin_path != '/bt' and os.path.exists(
                admin_path_file) and not 'admin_auth' in session:
            return abort(404)
        # 验证是否绑定了设备
        if not public.check_app('app'):
            return public.return_msg_gettext(False, 'Unbound user')
        import wxapp
        pluwx = wxapp.wxapp()
        checks = pluwx._check(get)
        if type(checks) != bool or not checks:
            public.set_error_num(num_key)
            return public.getJson(checks), json_header
        data = public.getJson(eval('pluwx.' + get.fun + '(get)'))
        return data, json_header
    else:
        return abort(404)


@app.route('/<name>/<fun>', methods=method_all)
@app.route('/<name>/<fun>/<path:stype>', methods=method_all)
def panel_other(name=None, fun=None, stype=None):
    # 左侧栏路由
    if name in ('site', 'database', 'docker', 'wp', 'mail', 'security', 'crontab', 'waf', 'setting', 'logs',
                'monitor/system', 'control', 'binds', 'softs', 'modify_password', 'flow', 'ssl_domain'):
        return index_new('{}/{}'.format(name, fun))

    # 插件接口
    if public.is_error_path():
        return redirect('/error', 302)
    if not name: return abort(404)
    if not re.match(r"^[\w\-]+$", name): return abort(404)
    if fun and not re.match(r"^[\w\-\.]+$", fun): return abort(404)
    if name != "mail_sys" or fun != "send_mail_http.json":
        comReturn = comm.local()
        if comReturn: return comReturn
        if not stype:
            tmp = fun.split('.')
            fun = tmp[0]
            if len(tmp) == 1: tmp.append('')
            stype = tmp[1]
        if fun:
            if name == 'btwaf' and fun == 'index':
                pass
            if name == 'waf':
                pass
            elif name == 'firewall' and fun == 'get_file':
                pass
            elif fun == 'static':
                pass
            elif stype == 'html':
                pass
            else:
                if public.get_csrf_cookie_token_key(
                ) in session and 'login' in session:
                    if not check_csrf():
                        return public.ReturnJson(
                            False,
                            'CSRF calibration failed, please login again'
                        ), json_header
        args = None
    else:
        p_path = public.get_plugin_path() + '/' + name
        if not os.path.exists(p_path): return abort(404)
        args = get_input()
        args_list = [
            'mail_from', 'password', 'mail_to', 'subject', 'content',
            'subtype', 'data'
        ]
        for k in args.get_items():
            if not k in args_list: return abort(404)

    is_accept = False
    if not fun: fun = 'index.html'
    if not stype:
        tmp = fun.split('.')
        fun = tmp[0]
        if len(tmp) == 1: tmp.append('')
        stype = tmp[1]

    if not name: name = 'coll'
    if not public.path_safe_check("%s/%s/%s" % (name, fun, stype)):
        return abort(404)
    if name.find('./') != -1 or not re.match(r"^[\w-]+$", name):
        return abort(404)
    if not name:
        return public.returnJson(
            False, 'Please pass in the plug-in name!'), json_header
    p_path = public.get_plugin_path() + '/' + name
    if not os.path.exists(p_path):
        if name == 'btwaf' and fun == 'index':
            pdata = {}
            import panelPlugin
            plu_panel = panelPlugin.panelPlugin()
            plugin_list = plu_panel.get_cloud_list()
            if not 'pro' in plugin_list: plugin_list['pro'] = -1
            for p in plugin_list['list']:
                if p['name'] in ['btwaf']:
                    if p['endtime'] != 0 and p['endtime'] < time.time():
                        pdata['error_msg'] = 1
                        break
            return render_template('error3.html', data=pdata)
        return abort(404)

    # 是否响插件应静态文件
    if fun == 'static':
        if stype.find('./') != -1 or not os.path.exists(p_path + '/static'):
            return abort(404)
        s_file = p_path + '/static/' + stype
        if s_file.find('..') != -1: return abort(404)
        if not re.match(r"^[\w\./-]+$", s_file): return abort(404)
        if not public.path_safe_check(s_file): return abort(404)
        if not os.path.exists(s_file): return abort(404)
        return send_file(s_file, conditional=True, etag=True)

    # 准备参数
    if not args: args = get_input()
    args.client_ip = public.GetClientIp()
    args.fun = fun
    # 初始化插件对象
    try:

        import PluginLoader
        try:
            args.s = fun
            data = PluginLoader.plugin_run(name, fun, args)
            if isinstance(data, dict):
                if 'status' in data and data['status'] == False and 'msg' in data:
                    if isinstance(data['msg'], str):
                        if data['msg'].find('加载失败') != -1 or data['msg'].find('Traceback ') == 0:
                            raise public.PanelError(data['msg'])
        except Exception as ex:
            if name == 'btwaf' and fun == 'index' and str(ex).find('未购买') != -1:
                return render_template('error3.html', data={})
            return public.get_error_object(None, plugin_name=name)

        r_type = type(data)
        if r_type in [Response, Resp]:
            return data

        # 处理响应
        if stype == 'json':  # 响应JSON
            return public.getJson(data), json_header
        elif stype == 'html':  # 使用模板
            t_path_root = p_path + '/templates/'
            t_path = t_path_root + fun + '.html'
            if not os.path.exists(t_path):
                return public.returnJson(
                    False,
                    'The specified template does not exist!'), json_header
            t_body = public.readFile(t_path)

            # 处理模板包含
            rep = r'{%\s?include\s"(.+)"\s?%}'
            includes = re.findall(rep, t_body)
            for i_file in includes:
                filename = p_path + '/templates/' + i_file
                i_body = 'ERROR: File ' + filename + ' does not exists.'
                if os.path.exists(filename):
                    i_body = public.readFile(filename)
                t_body = re.sub(rep.replace('(.+)', i_file), i_body, t_body)

            return render_template_string(t_body, data=data)
        else:  # 直接响应插件返回值,可以是任意flask支持的响应类型
            r_type = type(data)
            if r_type == dict:
                if name == 'btwaf' and 'msg' in data:
                    return render_template('error3.html',
                                           data={"error_msg": data['msg']})
                return public.returnJson(
                    False,
                    public.getMsg('Bad return type [{}]').format(r_type)), json_header
                # public.getMsg('PUBLIC_ERR_RETURN')), json_header
            return data
    except:
        return public.get_error_info()
        return public.get_error_object(None, plugin_name=name)


@app.route('/hook', methods=method_all)
def panel_hook():
    # webhook接口
    get = get_input()
    if not os.path.exists('plugin/webhook'):
        return abort(404)
    public.package_path_append('plugin/webhook')
    import webhook_main
    return public.getJson(webhook_main.webhook_main().RunHook(get))


@app.route('/install', methods=method_all)
def install():
    # 初始化面板接口
    if public.is_spider(): return abort(404)
    if not os.path.exists('install.pl'): return redirect('/login')
    if public.M('config').where("id=?", ('1',)).getField('status') == 1:
        if os.path.exists('install.pl'): os.remove('install.pl')
        session.clear()
        return redirect('/login')
    ret_login = os.path.join('/', admin_path)
    if admin_path == '/' or admin_path == '/bt': ret_login = '/login'
    session['admin_path'] = False
    session['login'] = False
    if request.method == method_get[0]:
        if not os.path.exists('install.pl'): return redirect(ret_login)
        data = {}
        data['status'] = os.path.exists('install.pl')
        data['username'] = public.GetRandomString(8).lower()
        return render_template('install.html', data=data)

    elif request.method == method_post[0]:
        if not os.path.exists('install.pl'): return redirect(ret_login)
        get = get_input()
        if not hasattr(get, 'bt_username'):
            return public.get_msg_gettext('The user name cannot be empty!')
        if not get.bt_username:
            return public.get_msg_gettext('The user name cannot be empty!')
        if not hasattr(get, 'bt_password1'):
            return public.get_msg_gettext('Password can not be blank!')
        if not get.bt_password1:
            return public.get_msg_gettext('Password can not be blank!')
        if get.bt_password1 != get.bt_password2:
            return public.get_msg_gettext(
                'The passwords entered twice do not match, please re-enter!')
        public.M('users').where("id=?", (1,)).save(
            'username,password',
            (get.bt_username,
             public.password_salt(public.md5(get.bt_password1.strip()),
                                  uid=1)))
        os.remove('install.pl')
        public.M('config').where("id=?", ('1',)).setField('status', 1)
        data = {}
        data['status'] = os.path.exists('install.pl')
        data['username'] = get.bt_username
        return render_template('install.html', data=data)


# ==================================================#

# ======================公共方法区域START============================#


def get_dir_down(filename, token, find):
    # 获取分享目录信息
    import files
    args = public.dict_obj()
    args.path = filename
    args.share = True
    to_path = filename.replace(find['filename'], '').strip('/')

    if request.args.get('play') == 'true':
        pdata = files.files().get_videos(args)
        return public.GetJson(pdata), json_header
    else:
        pdata = files.files().GetDir(args)
        pdata['token'] = token
        pdata['ps'] = find['ps']
        pdata['src_path'] = find['filename']
        pdata['to_path'] = to_path
        if find['expire'] < (time.time() + (86400 * 365 * 10)):
            pdata['expire'] = public.format_date(times=find['expire'])
        else:
            pdata['expire'] = public.get_msg_gettext('Never Expires')
        pdata['filename'] = (find['filename'].split('/')[-1] + '/' +
                             to_path).strip('/')
        return render_template('down.html', data=pdata, to_size=public.to_size)


def get_phpmyadmin_dir():
    # 获取phpmyadmin目录
    path = public.GetConfigValue('setup_path') + '/phpmyadmin'
    if not os.path.exists(path): return None
    phpport = '888'
    try:
        import re
        if session['webserver'] == 'nginx':
            filename = public.GetConfigValue(
                'setup_path') + '/nginx/conf/nginx.conf'
            conf = public.readFile(filename)
            rep = r"listen\s+([0-9]+)\s*;"
            rtmp = re.search(rep, conf)
            if rtmp:
                phpport = rtmp.groups()[0]
        if session['webserver'] == 'apache':
            filename = public.GetConfigValue(
                'setup_path') + '/apache/conf/extra/httpd-vhosts.conf'
            conf = public.readFile(filename)
            rep = r"Listen\s+([0-9]+)\s*\n"
            rtmp = re.search(rep, conf)
            if rtmp:
                phpport = rtmp.groups()[0]
        if session['webserver'] == 'openlitespeed':
            filename = public.GetConfigValue(
                'setup_path') + '/panel/vhost/openlitespeed/listen/888.conf'
            public.writeFile('/tmp/2', filename)
            conf = public.readFile(filename)
            rep = r"address\s*\*\:\s*(\d+)"
            rtmp = re.search(rep, conf)
            if rtmp:
                phpport = rtmp.groups()[0]
    except:
        pass

    for filename in os.listdir(path):
        filepath = path + '/' + filename
        if os.path.isdir(filepath):
            if filename[0:10] == 'phpmyadmin':
                return str(filename), phpport
    return None


class run_exec:
    # 模块访问对像
    def run(self, toObject, defs, get):
        result = None

        if not get.action in defs:
            return public.ReturnJson(
                False, 'Specific parameters are invalid!'), json_header
        # if get.action == 'change':
        #     public.print_log("查询  666 toObject --{}".format(vars(toObject)))
        #     # {'mail': <send_mail.send_mail object at 0x7f9fc98737d0>, '_config__mail_list': []}
        #     public.print_log("查询  666 get.action --{}".format(get.action))
        result = getattr(toObject, get.action)(get)
        if not hasattr(get, 'html') and not hasattr(get, 's_module'):
            r_type = type(result)
            if r_type in [Response, Resp]: return result
            result = public.GetJson(result), json_header

        if g.is_aes:
            result = public.aes_encrypt(result[0], g.aes_key), json_header

        return result


def check_csrf():
    # CSRF校验
    if app.config['DEBUG']: return True
    http_token = request.headers.get('x-http-token')
    if not http_token: return False
    if http_token != public.get_csrf_sess_html_token_value(): return False
    return True


def publicObject(toObject, defs, action=None, get=None, is_csrf=True):
    try:
        # 模块访问前置检查
        if is_csrf and public.get_csrf_sess_html_token_value() and session.get('login', None):
            if not check_csrf():
                return public.ReturnJson(False, 'INIT_CSRF_ERR'), json_header

        if not get:
            get = get_input()
        if action: get.action = action

        if hasattr(get, 'path'):
            get.path = get.path.replace('//', '/').replace('\\', '/')
            if get.path.find('./') != -1:
                return public.ReturnJson(False, 'Unsafe path'), json_header
            if get.path.find('->') != -1:
                get.path = get.path.split('->')[0].strip()
            get.path = public.xssdecode(get.path)
        if hasattr(get, 'filename'):
            get.filename = public.xssdecode(get.filename)

        if hasattr(get, 'sfile'):
            get.sfile = get.sfile.replace('//', '/').replace('\\', '/')
            get.sfile = public.xssdecode(get.sfile)
        if hasattr(get, 'dfile'):
            get.dfile = get.dfile.replace('//', '/').replace('\\', '/')
            get.dfile = public.xssdecode(get.dfile)

        if hasattr(toObject, 'site_path_check'):
            if not toObject.site_path_check(get):
                return public.ReturnJson(
                    False, "Overstepping one authority!"), json_header
        return run_exec().run(toObject, defs, get)
    except Exception as e:
        return error_500(e)


def check_login(http_token=None):
    # 检查是否登录面板
    if cache.get('dologin'): return False
    if 'login' in session:
        loginStatus = session['login']
        if loginStatus and http_token:
            if public.get_csrf_sess_html_token_value() != http_token:
                return False
        return loginStatus
    return False


def get_pd():
    # 获取授权信息
    return public.get_pd()


def send_authenticated():
    # 发送http认证信息
    request_host = public.GetHost()
    result = Response(
        '', 401,
        {'WWW-Authenticate': 'Basic realm="%s"' % request_host.strip()})
    if not 'login' in session and not 'admin_auth' in session: session.clear()
    return result


# 取端口
def FtpPort():
    # 获取FTP端口
    if session.get('port'): return
    import re
    try:
        file = public.GetConfigValue(
            'setup_path') + '/pure-ftpd/etc/pure-ftpd.conf'
        conf = public.readFile(file)
        rep = r"\n#?\s*Bind\s+[0-9]+\.[0-9]+\.[0-9]+\.+[0-9]+,([0-9]+)"
        port = re.search(rep, conf).groups()[0]
    except:
        port = '21'
    session['port'] = port


def is_login(result):
    # 判断是否登录2
    if 'login' in session:
        if session['login'] == True:
            pass
    return result


# js随机数模板使用，用于不更新版本号时更新前端文件不需要用户强制刷新浏览器
def get_js_random():
    js_random = public.readFile('data/js_random.pl')
    if not js_random or js_random == '1':
        js_random = public.GetRandomString(16)
    public.writeFile('data/js_random.pl', js_random)
    return js_random


# 获取输入数据
def get_input():
    data = public.dict_obj()
    exludes = ['blob']

    try:
        for key in request.args.keys():
            data.set(key, str(request.args.get(key, '')))
    except:
        pass

    try:
        for key in request.form.keys():
            if key in exludes:
                continue

            data.set(key, str(request.form.get(key, '')))
    except Exception as ex:
        try:
            post = request.form.to_dict()
            for key in post.keys():
                if key in exludes: continue
                data.set(key, str(post[key]))
        except:
            pass

    # 获取json数据
    if request.is_json:
        try:
            json_data = request.get_json()
            for k in json_data.keys():
                data[k] = json_data[k]
        except:
            pass

    if 'form_data' in g:
        try:
            for k in g.form_data.keys():
                data.set(k, str(g.form_data[k]))
        except:
            pass

    if not hasattr(data, 'data'):
        data.data = []

    return data


# 取数据对象
def get_input_data(data):
    pdata = public.dict_obj()
    for key in data.keys():
        pdata[key] = str(data[key])
    return pdata


# 检查Token
def check_token(data):
    # 已作废
    pluginPath = 'plugin/safelogin/token.pl'
    if not os.path.exists(pluginPath): return False
    from urllib import unquote
    from binascii import unhexlify
    from json import loads

    result = unquote(unhexlify(data))
    token = public.readFile(pluginPath).strip()

    result = loads(result)
    if not result: return False
    if result['token'] != token: return False
    return result


# ======================公共方法区域END============================#

# ---------------------    websocket  START  -------------------------- #


@sockets.route('/workorder_client')
def workorder_client(ws):
    comReturn = comm.local()
    if comReturn: return comReturn

    get = ws.receive()
    get = json.loads(get)
    if not check_csrf_websocket(ws, get):
        return

    import panelWorkorder
    toObject = panelWorkorder.panelWorkorder()
    get = get_input()
    toObject.client(ws, get)



@sockets.route('/ws_panel')
def ws_panel(ws):
    '''
        @name 面板接口ws入口
        @author hwliang<2021-07-24>
        @param ws<ws_parameter> websocket会话对像
        @return void
    '''
    comReturn = comm.local()
    if comReturn: return comReturn

    get = ws.receive()
    get = json.loads(get)
    if not check_csrf_websocket(ws, get): return

    while True:
        pdata = ws.receive()
        if pdata == '{}': break
        data = json.loads(pdata)
        get = public.to_dict_obj(data)
        get._ws = ws
        p = threading.Thread(target=ws_panel_thread, args=(get,))
        p.start()


def ws_panel_thread(get):
    '''
        @name 面板管理ws线程
        @author hwliang<2021-07-24>
        @param get<dict> 请求参数
        @return void
    '''

    if not hasattr(get, 'ws_callback'):
        get._ws.send(
            public.getJson(public.return_status_code(1001, 'ws_callback')))
        return
    if not hasattr(get, 'mod_name'):
        get._ws.send(
            public.getJson(public.return_status_code(1001, 'mod_name')))
        return
    if not hasattr(get, 'def_name'):
        get._ws.send(
            public.getJson(public.return_status_code(1001, 'def_name')))
        return
    get.mod_name = get.mod_name.strip()
    get.def_name = get.def_name.strip()
    check_str = '{}{}'.format(get.mod_name, get.def_name)
    if not re.match(r"^\w+$", check_str) or get.mod_name in [
        'public', 'common', 'db', 'db_mysql', 'downloadFile', 'jobs'
    ]:
        get._ws.send(
            public.getJson(
                public.return_status_code(
                    1000, 'Unsafe mod_name, def_name parameter content')))
        return

    mod_file = '{}/{}.py'.format(public.get_class_path(), get.mod_name)

    if not os.path.exists(mod_file):
        get._ws.send(
            public.getJson(
                public.return_status_code(
                    1000, 'Specified module {} does not exist'.format(
                        get.mod_name))))
        return
    _obj = public.get_script_object(mod_file)
    if not _obj:
        get._ws.send(
            public.getJson(
                public.return_status_code(
                    1000, 'Specified module {} does not exist'.format(
                        get.mod_name))))
        return
    _cls = getattr(_obj, get.mod_name)
    if not _cls:
        get._ws.send(
            public.getJson(
                public.return_status_code(
                    1000,
                    'The {} object was not found in the {} module'.format(
                        get.mod_name, get.mod_name))))
        return
    _def = getattr(_cls(), get.def_name)
    if not _def:
        get._ws.send(
            public.getJson(
                public.return_status_code(
                    1000,
                    'The {} object was not found in the {} module'.format(
                        get.mod_name, get.def_name))))
        return
    result = {'callback': get.ws_callback, 'result': _def(get)}
    get._ws.send(public.getJson(result))


@sockets.route('/ws_project')
def ws_project(ws):
    '''
        @name 项目管理ws入口
        @author hwliang<2021-07-24>
        @param ws<ws_parameter> websocket会话对像
        @return void
    '''
    comReturn = comm.local()
    if comReturn: return comReturn
    get = ws.receive()
    get = json.loads(get)
    if not check_csrf_websocket(ws, get): return

    from panelProjectController import ProjectController
    project_obj = ProjectController()
    while True:
        pdata = ws.receive()
        if pdata in '{}': break
        get = public.to_dict_obj(json.loads(pdata))
        get._ws = ws
        p = threading.Thread(target=ws_project_thread, args=(project_obj, get))
        p.start()


# docker模块内用到的ws
@sockets.route('/ws_model')
def ws_model(ws):
    '''
        @name 模型控制器ws入口
        @author hwliang<2021-07-24>
        @param ws<ws_parameter> websocket会话对像
        @return void
    '''

    comReturn = comm.local()
    if comReturn: return comReturn
    get = ws.receive()
    get = json.loads(get)

    if not check_csrf_websocket(ws, get): return

    from panelController import Controller
    model_obj = Controller()
    while True:
        pdata = ws.receive()
        if pdata in ['{}', {}, None, '']:
            ws.send(json.dumps(public.return_status_code(1000, '请求参数不能为空')))
            break
        try:
            get = public.to_dict_obj(json.loads(pdata))
        except:
            request.form = {
                "error": pdata
            }
            raise Exception('json load error !')
        get._ws = ws
        get.model_index = get.model_index.strip()
        p = threading.Thread(target=ws_model_thread, args=(model_obj, get))
        p.start()

def ws_mod_thread(_obj, get):
    '''
        @name 模型控制器ws线程
        @author hwliang<2021-07-24>
        @param _obj<Controller> 控制器对像
        @param get<dict> 请求参数
        @return void
    '''
    mod_result = _obj.model(get)
    if mod_result is None:
        return
    try:
        result = {'callback': get.ws_callback, 'result': _obj.model(get)}
        get._ws.send(public.getJson(result))
    except:
        return


def ws_model_thread(_obj, get):
    '''
        @name 模型控制器ws线程
        @author hwliang<2021-07-24>
        @param _obj<Controller> 控制器对像
        @param get<dict> 请求参数
        @return void
    '''
    if not hasattr(get, 'ws_callback'):
        get._ws.send(
            public.getJson(public.return_status_code(1001, 'ws_callback')))
        return
    result = {'callback': get.ws_callback, 'result': _obj.model(get)}
    get._ws.send(public.getJson(result))


def ws_project_thread(_obj, get):
    '''
        @name 项目管理ws线程
        @author hwliang<2021-07-24>
        @param _obj<ProjectController> 项目管理控制器对像
        @param get<dict> 请求参数
        @return void
    '''
    if not hasattr(get, 'ws_callback'):
        get._ws.send(
            public.getJson(public.return_status_code(1001, 'ws_callback')))
        return
    result = {'callback': get.ws_callback, 'result': _obj.model(get)}
    get._ws.send(public.getJson(result))


import subprocess

sock_pids = {}


@sockets.route('/sock_shell')
def sock_shell(ws):
    '''
        @name 执行指定命令，实时输出命令执行结果
        @author hwliang<2021-07-19>
        @return void

        示例：
            p = new WebSocket('ws://192.168.1.247:8888/sock_shell')
            p.send('ping www.bt.cn -c 100')
    '''
    comReturn = comm.local()
    if comReturn:
        ws.send(str(comReturn))
        return
    kill_closed()
    get = ws.receive()
    get = json.loads(get)
    if not check_csrf_websocket(ws, get): return

    t = None
    try:
        while True:
            cmdstring = ws.receive()
            if cmdstring in ['stop', 'error'] or not cmdstring:
                break
            t = threading.Thread(target=sock_recv, args=(cmdstring, ws))
            t.start()
        kill_closed()
    except:
        kill_closed()


def kill_closed():
    '''
        @name 关闭已关闭的连接
        @author hwliang<2021-07-24>
        @return void
    '''
    global sock_pids
    import psutil
    pids = psutil.pids()
    keys = sock_pids.copy().keys()
    for pid in keys:
        if hasattr(sock_pids[pid], 'closed'):
            is_closed = sock_pids[pid].closed
        else:
            is_closed = not sock_pids[pid].connected

        logging.debug("PID: {} , sock_stat: {}".format(pid, is_closed))
        if not is_closed: continue

        if pid in pids:
            try:
                p = psutil.Process(pid)
                for cp in p.children():
                    cp.kill()
                p.kill()
                logging.debug("killed: {}".format(pid))
                sock_pids.pop(pid)
            except:
                pass
        else:
            sock_pids.pop(pid)


def sock_recv(cmdstring, ws):
    global sock_pids
    try:
        p = subprocess.Popen(cmdstring + " 2>&1",
                             close_fds=True,
                             shell=True,
                             bufsize=4096,
                             stdout=subprocess.PIPE,
                             stderr=subprocess.PIPE)
        sock_pids[p.pid] = ws
        kill_closed()
        while p.poll() == None:
            send_line = p.stdout.readline().decode()
            if not send_line or send_line.find('tail: ') != -1: continue
            #     ws.send(send_line)
            # ws.send(p.stdout.read().decode())
            if ws.connected:
                ws.send(send_line)
        if ws.connected:
            ws.send(p.stdout.read().decode())
    except:
        kill_closed()


@app.route('/close_sock_shell', methods=method_all)
def close_sock_shell():
    '''
        @name 关闭指定命令
        @author hwliang<2021-07-19>
        @param cmdstring<string> 完整命令行
        @return dict
        示例：
            $.post('/close_sock_shell',{cmdstring:'ping www.bt.cn -c 100'})
    '''
    comReturn = comm.local()
    if comReturn: return comReturn
    args = get_input()
    if not check_csrf():
        return public.ReturnJson(False, 'INIT_CSRF_ERR'), json_header
    cmdstring = args.cmdstring.strip()
    skey = public.md5(cmdstring)
    pid = cache.get(skey)
    if not pid:
        return json.dumps(
            public.return_data(
                False, [], error_msg='The specified sock has been terminated!')
        ), json_header
    os.kill(pid, 9)
    cache.delete(skey)
    return json.dumps(public.return_data(True,
                                         'Successful operation!')), json_header


def check_csrf_websocket(ws, args):
    '''
        @name 检查websocket是否被csrf攻击
        @author hwliang<2021-07-24>
        @param ws<WebSocket> websocket对像
        @return void
    '''
    if g.is_aes: return True
    if g.api_request: return True
    if public.is_debug(): return True
    is_success = True
    if not 'x-http-token' in args:
        is_success = False

    if is_success:
        if public.get_csrf_sess_html_token_value() != args['x-http-token']:
            is_success = False

    if not is_success:
        ws.send('token error')
        return False

    return True


@sockets.route('/webssh')
def webssh(ws):
    # 宝塔终端连接
    comReturn = comm.local()
    if comReturn:
        ws.send(str(comReturn))
        return
    if not ws: return 'False'
    get = ws.receive()
    if not get: return
    get = json.loads(get)
    if not check_csrf_websocket(ws, get):
        return

    import ssh_terminal
    sp = ssh_terminal.ssh_host_admin()
    if 'host' in get:
        ssh_info = {}
        ssh_info['host'] = get['host'].strip()
        if 'port' in get:
            ssh_info['port'] = int(get['port'])
        if 'username' in get:
            ssh_info['username'] = get['username'].strip()
        if 'password' in get:
            ssh_info['password'] = get['password'].strip()
        if 'pkey' in get:
            ssh_info['pkey'] = get['pkey'].strip()

        if get['host'] in ['127.0.0.1', 'localhost']:
            if not 'password' in ssh_info:
                ssh_info = sp.get_ssh_info('127.0.0.1')
            if not ssh_info: ssh_info = sp.get_ssh_info('localhost')
            if not ssh_info: ssh_info = {"host": "127.0.0.1"}
            if not 'port' in ssh_info:
                ssh_info['port'] = public.get_ssh_port()
    else:
        ssh_info = sp.get_ssh_info('127.0.0.1')
        if not ssh_info: ssh_info = sp.get_ssh_info('localhost')
        if not ssh_info: ssh_info = {"host": "127.0.0.1"}
        ssh_info['port'] = public.get_ssh_port()

    if not ssh_info['host'] in ['127.0.0.1', 'localhost']:
        if not 'username' in ssh_info:
            ssh_info = sp.get_ssh_info(ssh_info['host'])
            if not ssh_info:
                ws.send(
                    'The specified host information is not found, please add it again!'
                )
                return
    p = ssh_terminal.ssh_terminal()
    p.run(ws, ssh_info)
    del (p)
    if ws.connected:
        ws.close()
    return 'False'


# ---------------------    websocket END    -------------------------- #


@app.route("/daily", methods=method_all)
def daily():
    """面板日报数据"""

    comReturn = comm.local()
    if comReturn: return comReturn

    import panelDaily
    toObject = panelDaily.panelDaily()

    defs = ("get_app_usage", "get_daily_data", "get_daily_list")
    result = publicObject(toObject, defs)
    return result


@app.route('/phpmyadmin/<path:path_full>', methods=method_all)
def pma_proxy(path_full=None):
    '''
        @name phpMyAdmin代理
        @author hwliang<2022-01-19>
        @return Response
    '''
    comReturn = comm.local()
    if comReturn: return comReturn
    cache_key = 'pmd_port_path'
    pmd = cache.get(cache_key)
    if not pmd:
        pmd = get_phpmyadmin_dir()
        if not pmd:
            return 'phpMyAdmin is not installed, please go to the [App Store] page to install it!'
        pmd = list(pmd)
        cache.set(cache_key, pmd, 10)
    panel_pool = 'http://'
    if request.url_root[:5] == 'https':
        panel_pool = 'https://'
        import ajax
        ssl_info = ajax.ajax().get_phpmyadmin_ssl(None)
        if ssl_info['status']:
            pmd[1] = ssl_info['port']
        else:
            panel_pool = 'http://'

    proxy_url = '{}127.0.0.1:{}/{}/'.format(
        panel_pool, pmd[1], pmd[0]) + request.full_path.replace(
        '/phpmyadmin/', '')
    from panelHttpProxy import HttpProxy
    px = HttpProxy()
    return px.proxy(proxy_url)


@app.route("/adminer/<path:path_full>", methods=method_all)
def adminer_proxy(path_full=None):
    """
        @name adminer代理
        @return Response
    """
    comReturn = comm.local()
    if comReturn:
        return comReturn
    try:
        from adminer.manager import AdminerManager
        manager = AdminerManager()
        if not manager.is_install:
            return 'Adminer is not install, please install it first!'
        path, port = manager.adminer_dir_port
    except public.HintException as e:
        return str(e)

    endpoint = request.full_path.replace("/adminer/", "")
    proxy_url = f"http://127.0.0.1:{port}/{path}/{endpoint}"
    from panelHttpProxy import HttpProxy
    px = HttpProxy()
    return px.proxy(proxy_url, True)


@app.route('/p/<int:port>', methods=method_all)
@app.route('/p/<int:port>/', methods=method_all)
@app.route('/p/<int:port>/<path:full_path>', methods=method_all)
def proxy_port(port, full_path=None):
    '''
        @name 代理指定端口
        @author hwliang<2022-01-19>
        @return Response
    '''

    comReturn = comm.local()
    if comReturn: return comReturn
    full_path = request.full_path.replace('/p/{}/'.format(port),
                                          '').replace('/p/{}'.format(port), '')
    uri = '{}/{}'.format(port, full_path)
    uri = uri.replace('//', '/')
    proxy_url = 'http://127.0.0.1:{}'.format(uri)
    from panelHttpProxy import HttpProxy
    px = HttpProxy()
    return px.proxy(proxy_url)


@app.route('/push', methods=method_all)
def push(pdata=None):
    comReturn = comm.local()
    if comReturn: return comReturn
    import panelPush
    toObject = panelPush.panelPush()
    defs = ('set_push_status', 'get_push_msg_list', 'get_modules_list',
            'install_module', 'uninstall_module', 'get_module_template',
            'set_push_config', 'get_push_config', 'del_push_config',
            'get_module_logs', 'get_module_config', 'get_push_list',
            'get_push_logs')
    result = publicObject(toObject, defs, None, pdata)
    return result


# ===========================================================v2路由区start===========================================================#
# docker模块内用到的ws
@sockets.route(route_v2 + '/ws_model')
def ws_model_v2(ws):
    '''
        @name 模型控制器ws入口
        @author hwliang<2021-07-24>
        @param ws<ws_parameter> websocket会话对像
        @return void
    '''
    # 开发时暂时注释----------------
    comReturn = comm.local()
    if comReturn: return comReturn

    get = ws.receive()
    get = json.loads(get)

    # 开发时暂时注释----------------
    if not check_csrf_websocket(ws, get): return

    from panelControllerV2 import Controller
    model_obj = Controller()
    while True:
        pdata = ws.receive()
        if pdata in ['{}', {}, None, '']:
            ws.send(json.dumps(public.return_status_code(1000, 'The request parameter cannot be null')))
            break
        try:
            get = public.to_dict_obj(json.loads(pdata))
        except:
            request.form = {
                "error": pdata
            }
            raise Exception('json load error !')
        get._ws = ws
        get.model_index = get.model_index.strip()
        p = threading.Thread(target=ws_model_thread, args=(model_obj, get))
        p.start()

# 2024/2/19 上午 10:34 新场景模型控制器ws入口，无默认return
@sockets.route(route_v2 + '/ws_modsoc')
def ws_modsoc(ws):
    '''
        @name 新场景模型控制器ws入口
        @author wzz<2024-02-19>
        @param ws<ws_parameter> websocket会话对像
        @return void
    '''

    comReturn = comm.local()
    if comReturn: return comReturn
    get = ws.receive()
    get = json.loads(get)

    if not check_csrf_websocket(ws, get):
        return

    # try:
    # from panelController import Controller
    # model_obj = Controller()
    from mod.modController import Controller
    model_obj = Controller()
    while True:
        pdata = ws.receive()
        if pdata in ['{}', {}, None, '']:
            ws.send(json.dumps(public.return_status_code(1000, 'The request parameter cannot be empty')))
            break
        try:
            get = public.to_dict_obj(json.loads(pdata))
        except:
            request.form = {
                "error": pdata
            }
            raise Exception('json load error !')
        get._ws = ws
        get.model_index = "mod"
        p = threading.Thread(target=ws_mod_thread, args=(model_obj, get))
        p.start()
    # except:
    #     import traceback
    #     public.print_log(traceback.format_exc())

# ======================普通路由区start============================#


@app.route(route_v2 + '/', methods=method_all)
def home_v2():
    # 面板首页
    comReturn = comm.local()
    if comReturn: return comReturn
    data = {}
    data[public.to_string([112,
                           100])], data['pro_end'], data['ltd_end'] = get_pd()
    data['siteCount'] = public.M('sites').count()
    data['ftpCount'] = public.M('ftps').count()
    data['databaseCount'] = public.M('databases').count()
    data['lan'] = public.GetLan('index')
    data['js_random'] = get_js_random()
    return render_template('index.html', data=data)


@app.route(route_v2 + '/xterm', methods=method_all)
def xterm_v2():
    # 宝塔终端管理
    comReturn = comm.local()
    if comReturn: return comReturn
    if request.method == method_get[0]:
        import system_v2
        data = system_v2.system().GetConcifInfo()
        return render_template('xterm.html', data=data)
    import ssh_terminal_v2
    ssh_host_admin = ssh_terminal_v2.ssh_host_admin()
    defs = ('get_host_list', 'get_host_find', 'modify_host', 'create_host',
            'remove_host', 'set_sort', 'get_command_list', 'create_command',
            'get_command_find', 'modify_command', 'remove_command', 'test_ssh_connect')
    return publicObject(ssh_host_admin, defs, None)


@app.route(route_v2 + '/modify_password', methods=method_get)
def modify_password_v2():
    comReturn = comm.local()
    if comReturn: return comReturn
    # if not session.get('password_expire',False): return redirect('/',302)
    data = {}
    g.title = 'The password has expired, please change it!'
    # return render_template('modify_password.html', data=data)
    return render_template('index1.html', data=data)

@app.route(route_v2 + '/site', methods=method_all)
def site_v2(pdata=None):
    # 网站管理
    comReturn = comm.local()
    if comReturn: return comReturn
    if request.method == method_get[0] and not pdata:
        # data = {}
        import system_v2
        data = system_v2.system().GetConcifInfo()
        data['isSetup'] = True
        data['lan'] = public.getLan('site')
        data['js_random'] = get_js_random()
        if os.path.exists(public.GetConfigValue('setup_path') + '/nginx') == False \
                and os.path.exists(public.GetConfigValue('setup_path') + '/apache') == False \
                and os.path.exists('/usr/local/lsws/bin/lswsctrl') == False:
            data['isSetup'] = False
        return render_template('site.html', data=data)

    import panel_site_v2
    siteObject = panel_site_v2.panelSite()
    defs = (
        'get_auto_restart_rph',
        'remove_auto_restart_rph',
        'auto_restart_rph',
        'check_del_data',
        'upload_csv',
        'create_website_multiple',
        'del_redirect_multiple',
        'del_proxy_multiple',
        'delete_dir_auth_multiple',
        'delete_dir_bind_multiple',
        'delete_domain_multiple',
        'set_site_etime_multiple',
        'set_site_php_version_multiple',
        'delete_website_multiple',
        'set_site_status_multiple',
        'get_site_list',
        'get_site_err_log',
        'get_site_domains',
        'GetRedirectFile',
        'SaveRedirectFile',
        'DeleteRedirect',
        'GetRedirectList',
        'CreateRedirect',
        'ModifyRedirect',
        "set_error_redirect",
        'set_dir_auth',
        'delete_dir_auth',
        'get_dir_auth',
        'modify_dir_auth_pass',
        'reset_wp_db',
        'export_domains',
        'import_domains',
        'GetSiteLogs',
        'GetSiteDomains',
        'GetSecurity',
        'SetSecurity',
        'ProxyCache',
        'CloseToHttps',
        'HttpToHttps',
        'SetEdate',
        'SetRewriteTel',
        'GetCheckSafe',
        'CheckSafe',
        'GetDefaultSite',
        'SetDefaultSite',
        'CloseTomcat',
        'SetTomcat',
        'apacheAddPort',
        'AddSite',
        'GetPHPVersion',
        'SetPHPVersion',
        'DeleteSite',
        'AddDomain',
        'DelDomain',
        'GetDirBinding',
        'AddDirBinding',
        'GetDirRewrite',
        'DelDirBinding',
        'get_site_types',
        'add_site_type',
        'remove_site_type',
        'modify_site_type_name',
        'set_site_type',
        'UpdateRulelist',
        'SetSiteRunPath',
        'GetSiteRunPath',
        'SetPath',
        'SetIndex',
        'GetIndex',
        'GetDirUserINI',
        'SetDirUserINI',
        'GetRewriteList',
        'SetSSL',
        'SetSSLConf',
        'CreateLet',
        'CloseSSLConf',
        'GetSSL',
        'SiteStart',
        'SiteStop',
        'Set301Status',
        'Get301Status',
        'CloseLimitNet',
        'SetLimitNet',
        'GetLimitNet',
        'RemoveProxy',
        'GetProxyList',
        'GetProxyDetals',
        'CreateProxy',
        'ModifyProxy',
        'GetProxyFile',
        'SaveProxyFile',
        'ToBackup',
        'DelBackup',
        'GetSitePHPVersion',
        'logsOpen',
        'GetLogsStatus',
        'CloseHasPwd',
        'SetHasPwd',
        'GetHasPwd',
        'GetDnsApi',
        'SetDnsApi',
        'reset_wp_password',
        'is_update',
        'purge_all_cache',
        'set_fastcgi_cache',
        'update_wp',
        'get_wp_username',
        'get_language',
        'deploy_wp',
        # 网站管理新增
        'test_domains_api',
        'site_rname',
        'get_wp_versions',
        'AddWPSite',
        'get_wp_configurations',
        'save_wp_configurations',
        'wp_backup_list',
        'wp_backup',
        'wp_restore',
        'wp_remove_backup',
        'get_wp_security_info',
        'open_wp_file_protection',
        "wordpress_vulnerabilities_scan",
        "ignore_vuln",
        "get_ignore_vuln",
        "set_auth_scan",
        "get_auth_scan_status",
        "wordpress_vulnerabilities_time",
        'close_wp_file_protection',
        'get_wp_file_info',
        'open_wp_firewall_protection',
        'close_wp_firewall_protection',
        'get_wp_firewall_info',
        'wp_migrate_from_website_to_wptoolkit',
        'wp_can_migrate_from_website_to_wptoolkit',
        'wp_create_with_aap_bak',
        'wp_create_with_plesk_or_cpanel_bak',
        'wp_clone',
        'wp_integrity_check',
        'wp_reinstall_files',
        'wp_plugin_list',
        'wp_install_plugin',
        'wp_installed_plugins',
        'wp_update_plugin',
        'wp_set_plugin_auto_update',
        'wp_set_plugin_status',
        'wp_uninstall_plugin',
        'wp_theme_list',
        'wp_install_theme',
        'wp_installed_themes',
        'wp_update_theme',
        'wp_set_theme_auto_update',
        'wp_switch_theme',
        'wp_uninstall_theme',
        'wp_all_sites',
        'wp_set_list',
        'wp_create_set',
        'wp_remove_set',
        'wp_get_items_from_set',
        'wp_add_items_to_set',
        'wp_update_item_state_with_set',
        'wp_remove_items_from_set',
        'wp_install_with_set',
        'wp_remote_add',
        'wp_remote_add_manually',
        'wp_remote_remove',
        'wp_remote_sites',
        'wp_add_onekey_database',
        'set_restart_task',
        'get_restart_task',
        'set_https_mode',
        'get_https_mode',
        'get_cron_scanin_info',
        'set_cron_scanin_info',
        'wp_create_with_manual_bak',
        'set_wp_site_type',
        'add_wp_site_type',
        'edit_wp_site_type',
        'del_wp_site_type',
        'set_wp_tool',
        'get_wp_tool',
        'get_wp_debug_log',
        'get_wp_sites',
        'wp_copy_data',
        'get_source_tables',
        'get_wp_progress',
        'set_wp_maintenance',
        'get_wp_maintenance',
        'get_site_maintenance',
        'set_site_maintenance',
        'get_wp_security_status',
        'wp_manual_upload',
        'get_cdn_ip',
        'set_site_global',
        'get_site_global',
        # 新增多服务
        'get_multi_webservice_status',
        'switch_multi_webservice_status',
        'switch_webservice',
        'get_current_webservice',
        'multi_service_check_repair',
        'website_rollback',
        'service_install_count'
    )
    return publicObject(siteObject, defs, None, pdata)

@app.route(route_v2 + '/git', methods=method_all)
def git_tools(pdata=None):
    # git管理
    comReturn = comm.local()
    if comReturn: return comReturn
    import git_tools
    gitObject = git_tools.GitTools()
    defs = (
        'get_git_version',
        'get_ssh_key',
        'add_key_repository',
        'get_deploy_sh',
        'save_deploy_sh',
        'get_deploy_records',
        'manual_deploy_site',
        'get_site_deploy_log',
        'get_deploy_script',
        'git_rollback',
        'get_site_git_conf',
        'save_site_git_conf',
        'del_site_git',
        'auto_deploy',
        'refresh_webhook_url',
        'update_deploy_sh',
        'del_script',
        'get_webhook_log',
        'clear_webhook_log'
    )
    return publicObject(gitObject, defs, None, pdata)

@app.route(route_v2 + '/ftp', methods=method_all)
def ftp_v2(pdata=None):
    # FTP管理
    comReturn = comm.local()
    if comReturn: return comReturn
    if request.method == method_get[0] and not pdata:
        FtpPort()
        import system_v2
        data = system_v2.system().GetConcifInfo()
        data['isSetup'] = True
        data['js_random'] = get_js_random()
        if os.path.exists(public.GetConfigValue('setup_path') +
                          '/pure-ftpd') == False:
            data['isSetup'] = False
        data['lan'] = public.GetLan('ftp')
        return render_template('ftp.html', data=data)
    import ftp_v2
    ftpObject = ftp_v2.ftp()
    defs = ('AddUser', 'DeleteUser', 'SetUserPassword', 'SetStatus', 'setPort',
            'set_user_home', 'get_login_logs', 'get_action_logs',
            'set_ftp_logs')
    return publicObject(ftpObject, defs, None, pdata)


@app.route(route_v2 + '/database', methods=method_all)
def database_v2(pdata=None):
    # 数据库管理
    comReturn = comm.local()
    if comReturn: return comReturn
    if request.method == method_get[0] and not pdata:
        import ajax_v2
        from panelPlugin import panelPlugin
        session['phpmyadminDir'] = False
        if panelPlugin().get_phpmyadmin_stat():
            pmd = get_phpmyadmin_dir()
            if pmd:
                session['phpmyadminDir'] = 'http://' + public.GetHost(
                ) + ':' + pmd[1] + '/' + pmd[0]
        ajax_v2.ajax().set_phpmyadmin_session()
        import system_v2
        data = system_v2.system().GetConcifInfo()
        data['isSetup'] = os.path.exists(
            public.GetConfigValue('setup_path') + '/mysql/bin')
        data['mysql_root'] = public.M('config').where(
            'id=?', (1,)).getField('mysql_root')
        data['lan'] = public.GetLan('database')
        data['js_random'] = get_js_random()
        return render_template('database.html', data=data)
    import database_v2
    databaseObject = database_v2.database()
    defs = (
        'GetdataInfo',
        'check_del_data',
        'get_database_size',
        'GetInfo',
        'ReTable',
        'OpTable',
        'AlTable',
        'GetSlowLogs',
        'GetRunStatus',
        'SetDbConf',
        'GetDbStatus',
        'BinLog',
        'GetErrorLog',
        'GetMySQLInfo',
        'SetDataDir',
        'SetMySQLPort',
        'AddCloudDatabase',
        'AddDatabase',
        'DeleteDatabase',
        'SetupPassword',
        'ResDatabasePassword',
        'ToBackup',
        'GetBackupSize',
        'GetImportSize',
        'GetImportLog',
        'DelBackup',
        'AddCloudServer',
        'GetCloudServer',
        'RemoveCloudServer',
        'ModifyCloudServer',
        'InputSql',
        'SyncToDatabases',
        'SyncGetDatabases',
        'GetDatabaseAccess',
        'SetDatabaseAccess',
        'get_mysql_user',
        'check_mysql_ssl_status',
        'write_ssl_to_mysql',
        'GetdataInfo',
        'GetBackup',
        'GetMysqlUser',
        'GetDatabasesList',
        'AddMysqlUser',
        'DelMysqlUser',
        'ChangeUserPass',
        'GetUserGrants',
        'GetUserHostDbGrant',
        'AddUserGrants',
        'DelUserGrants',
        'GetmvDataDirSpeed',
        'GetMySQLBinlogs',
        'mysql_oom_adj',
    )
    return publicObject(databaseObject, defs, None, pdata)


@app.route(route_v2 + '/acme', methods=method_all)
def acme_v2(pdata=None):
    # Let's 证书管理
    comReturn = comm.local()
    if comReturn: return comReturn
    import acme_v2
    acme_v2_object = acme_v2.acme_v2()
    defs = ('get_orders', 'remove_order', 'get_order_find', 'revoke_order',
            'create_order', 'get_account_info', 'set_account_info',
            'update_zip', 'get_cert_init_api', 'get_auths', 'auth_domain',
            'check_auth_status', 'download_cert', 'apply_cert', 'renew_cert',
            'apply_cert_api', 'apply_dns_auth')
    return publicObject(acme_v2_object, defs, None, pdata)


@app.route(route_v2 + '/api', methods=method_all)
def api_v2(pdata=None):
    # APP使用的API接口管理
    comReturn = comm.local()
    if comReturn: return comReturn
    import panel_api_v2
    api_object = panel_api_v2.panelApi()
    defs = ('get_token', 'check_bind', 'get_bind_status', 'get_apps',
            'add_bind_app', 'remove_bind_app', 'set_token', 'get_tmp_token',
            'get_app_bind_status', 'login_for_app')
    return publicObject(api_object, defs, None, pdata)


@app.route(route_v2 + '/control', methods=method_all)
def control_v2(pdata=None):
    # 监控页面
    comReturn = comm.local()
    if comReturn: return comReturn
    import system_v2
    data = system_v2.system().GetConcifInfo()
    data['lan'] = public.GetLan('control')
    data['js_random'] = get_js_random()
    return render_template('control.html', data=data)


@app.route(route_v2 + '/logs', methods=method_all)
def logs_v2(pdata=None):
    comReturn = comm.local()
    if comReturn: return comReturn
    if request.method == method_get[0] and not pdata:
        data = {}
        data['lan'] = public.GetLan('soft')
        data['show_workorder'] = not os.path.exists('data/not_workorder.pl')
        return render_template('logs.html', data=data)


@app.route(route_v2 + '/firewall', methods=method_all)
def firewall_v2(pdata=None):
    # 安全页面
    comReturn = comm.local()
    if comReturn: return comReturn
    if request.method == method_get[0] and not pdata:
        import system_v2
        data = system_v2.system().GetConcifInfo()
        data['lan'] = public.GetLan('firewall')
        data['js_random'] = get_js_random()
        return render_template('firewall.html', data=data)
    import firewalls_v2
    firewallObject = firewalls_v2.firewalls()
    defs = ('GetList', 'AddDropAddress', 'DelDropAddress', 'FirewallReload',
            'SetFirewallStatus', 'AddAcceptPort', 'DelAcceptPort',
            'SetSshStatus', 'SetPing', 'SetSshPort', 'GetSshInfo',
            'SetFirewallStatus')
    return publicObject(firewallObject, defs, None, pdata)

@app.route(route_v2 + '/firewall/com/<def_name>', methods=method_all)
def firewall_v22(def_name, pdata=None):
    if request.method not in ['GET', 'POST']: return
    path_split = request.path.split("/")
    if len(path_split) < 5: return
    comReturn = comm.local()
    if comReturn: return comReturn
    # from panelSafeControllerV2 import SafeController
    from panelFireControllerV2 import FirewallController
    project_obj = FirewallController()
    defs = ('model',)
    get = get_input()
    get.action = 'model'
    get.mod_name = path_split[3]
    get.def_name = def_name

    return publicObject(project_obj, defs, None, get)


@app.route(route_v2 + '/ssh_security', methods=method_all)
def ssh_security_v2(pdata=None):
    # SSH安全
    comReturn = comm.local()
    if comReturn: return comReturn
    if request.method == method_get[0] and not pdata and not request.args.get(
            'action', '') in ['download_key']:
        data = {}
        data['lan'] = public.GetLan('firewall')
        data['js_random'] = get_js_random()
        return render_template('firewall.html', data=data)
    import ssh_security_v2
    firewallObject = ssh_security_v2.ssh_security()
    is_csrf = True
    if request.args.get('action', '') in ['download_key']: is_csrf = False
    defs = ('san_ssh_security', 'set_password', 'set_sshkey', 'stop_key',
            'get_config', 'download_key', 'stop_password', 'get_key',
            'return_ip', 'add_return_ip', 'del_return_ip', 'start_jian',
            'stop_jian', 'get_jian', 'get_logs', 'set_root', 'stop_root',
            'start_auth_method', 'stop_auth_method', 'get_auth_method',
            'check_so_file', 'get_so_file', 'get_pin', 'set_login_send',
            'get_login_send', 'get_msg_push_list', 'clear_login_send', 'set_root_password')
    return publicObject(firewallObject, defs, None, pdata, is_csrf)


@app.route(route_v2 + '/monitor', methods=method_all)
def panel_monitor_v2(pdata=None):
    # 云控统计信息
    comReturn = comm.local()
    if comReturn: return comReturn
    import monitor_v2
    dataObject = monitor_v2.Monitor()
    defs = ('get_spider', 'get_exception', 'get_request_count_qps',
            'load_and_up_flow', 'get_request_count_by_hour')
    return publicObject(dataObject, defs, None, pdata)


@app.route(route_v2 + '/san', methods=method_all)
def san_baseline_v2(pdata=None):
    # 云控安全扫描
    comReturn = comm.local()
    if comReturn: return comReturn
    import san_baseline_v2
    dataObject = san_baseline_v2.san_baseline()
    defs = ('start', 'get_api_log', 'get_resut', 'get_ssh_errorlogin',
            'repair', 'repair_all')
    return publicObject(dataObject, defs, None, pdata)


@app.route(route_v2 + '/password', methods=method_all)
def panel_password_v2(pdata=None):
    # 云控密码管理
    comReturn = comm.local()
    if comReturn: return comReturn
    import password_v2
    dataObject = password_v2.password()
    defs = ('set_root_password', 'get_mysql_root', 'set_mysql_password',
            'set_panel_password', 'SetPassword', 'SetSshKey', 'StopKey',
            'GetConfig', 'StopPassword', 'GetKey', 'get_databses',
            'rem_mysql_pass', 'set_mysql_access', "get_panel_username")
    return publicObject(dataObject, defs, None, pdata)


@app.route(route_v2 + '/warning', methods=method_all)
def panel_warning_v2(pdata=None):
    # 首页安全警告
    comReturn = comm.local()
    if comReturn: return comReturn
    if public.get_csrf_html_token_key() in session and 'login' in session:
        if not check_csrf():
            return public.ReturnJson(False, 'INIT_CSRF_ERR'), json_header
    get = get_input()
    ikey = 'warning_list'
    import panel_warning_v2
    dataObject = panel_warning_v2.panelWarning()
    if get.action == 'get_list':
        result = cache.get(ikey)
        if not result or 'force' in get:
            result = json.loads('{"ignore":[],"risk":[],"security":[]}')
            try:
                defs = ("get_list",)
                result = publicObject(dataObject, defs, None, pdata)
                cache.set(ikey, result, 3600)
                return result
            except:
                pass
        if hasattr(get, 'open') and get.open == "1":
            public.set_module_logs("panel_warning_v2", "get_list")
        return result

    defs = ('get_list', 'set_ignore', 'check_find', 'check_cve',
            'set_vuln_ignore', 'get_scan_bar', 'get_tmp_result',
            'kill_get_list','get_res_list')

    if get.action in ['set_ignore', 'check_find', 'set_vuln_ignore']:
        cache.delete(ikey)
    return publicObject(dataObject, defs, None, pdata)

# -----------------------------------------  安全模块路由区 start----------------------------------------

@app.route(route_v2 + '/safecloud', methods=method_all)
def safecloud(pdata=None):
    # 安全
    comReturn = comm.local()
    if comReturn: return comReturn
    from projectModelV2.safecloudModel import main
    toObject = main()
    defs = ('get_safe_overview','get_pending_alarm_trend','get_security_trend',
            'get_security_dynamic','set_config','get_safecloud_list',
            'get_webshell_result','get_config','deal_webshell_file','set_alarm_config',
            'webshell_detection','ignore_file','get_ignored_list','del_ignored')
    return publicObject(toObject, defs, None, pdata)

# 避免加密后变成单例模式
from safeModel.reportModel import main as report_main
@app.route(route_v2 + '/safe/report', methods=method_all)
def report(pdata=None):
    # 安全报告
    comReturn = comm.local()
    if comReturn: return comReturn
    toObject = report_main()
    defs = ('get_report')
    return publicObject(toObject, defs, None, pdata)

@app.route(route_v2 + '/scanning', methods=method_all)
def scanning(pdata=None):
    comReturn = comm.local()
    if comReturn: return comReturn
    from projectModelV2.scanningModel import main
    toObject = main()
    defs = ('get_vuln_info', 'startScan')
    return publicObject(toObject, defs, None, pdata)

@app.route(route_v2 + '/safe_detect', methods=method_all)
def safe_detect(pdata=None):
    comReturn = comm.local()
    if comReturn: return comReturn
    from projectModelV2.safe_detectModel import main
    toObject = main()
    defs = ('get_safe_count')
    return publicObject(toObject, defs, None, pdata)

# -----------------------------------------  安全模块路由区 end----------------------------------------

@app.route(route_v2 + '/bak', methods=method_all)
def backup_bak_v2(pdata=None):
    # 云控备份服务
    comReturn = comm.local()
    if comReturn: return comReturn
    import backup_bak_v2
    dataObject = backup_bak_v2.backup_bak()
    defs = ('get_sites', 'get_databases', 'backup_database', 'backup_site',
            'backup_path', 'get_database_progress', 'get_site_progress',
            'down', 'get_down_progress', 'download_path', 'backup_site_all',
            'get_all_site_progress', 'backup_date_all',
            'get_all_date_progress')
    return publicObject(dataObject, defs, None, pdata)


@app.route(route_v2 + '/abnormal', methods=method_all)
def abnormal_v2(pdata=None):
    # 云控系统统计
    comReturn = comm.local()
    if comReturn: return comReturn
    import abnormal_v2
    dataObject = abnormal_v2.abnormal()
    defs = ('mysql_server', 'mysql_cpu', 'mysql_count', 'php_server',
            'php_conn_max', 'php_cpu', 'CPU', 'Memory', 'disk',
            'not_root_user', 'start')
    return publicObject(dataObject, defs, None, pdata)


@app.route(route_v2 + '/project/nodejs/<def_name>', methods=method_all)
@app.route(route_v2 + '/project/nodejs/<def_name>/html', methods=method_all)
@app.route(route_v2 + '/project/docker/<def_name>', methods=method_all)
@app.route(route_v2 + '/project/docker/<def_name>/html', methods=method_all)
@app.route(route_v2 + '/project/quota/<def_name>', methods=method_all)
@app.route(route_v2 + '/project/quota/<def_name>/html', methods=method_all)
@app.route(route_v2 + '/project/proxy/<def_name>', methods=method_all)
@app.route(route_v2 + '/project/proxy/<def_name>/html', methods=method_all)
def project_v2(def_name):
    if request.method not in ['GET', 'POST']: return
    path_split = request.path.split("/")
    if len(path_split) < 5: return
    comReturn = comm.local()
    if comReturn: return comReturn
    from panelProjectControllerV2 import ProjectController
    project_obj = ProjectController()
    defs = ('model',)
    get = get_input()
    get.action = 'model'
    get.mod_name = path_split[3]
    get.def_name = def_name
    if request.path.endswith('/html'):
        return project_obj.model(get)
    return publicObject(project_obj, defs, None, get)


@app.route(route_v2 + '/msg/<mod_name>/<def_name>', methods=method_all)
def msgcontroller_v2(mod_name, def_name):
    comReturn = comm.local()
    if comReturn: return comReturn
    from MsgControllerV2 import MsgController
    project_obj = MsgController()
    defs = ('model',)
    get = get_input()
    get.action = 'model'
    get.mod_name = mod_name
    get.def_name = def_name
    return publicObject(project_obj, defs, None, get)


# @app.route(route_v2 + '/docker', methods=method_all)
# def docker_v2(pdata=None):
#     comReturn = comm.local()
#     if comReturn: return comReturn
#     if request.method == method_get[0]:
#         import system_v2
#         data = system_v2.system().GetConcifInfo()
#         data['js_random'] = get_js_random()
#         data['lan'] = public.GetLan('files')
#         return render_template('docker.html', data=data)

# @app.route(route_v2 + '/docker', methods=method_all)
@app.route(route_v2 + '/btdocker/app/<def_name>', methods=method_all)
@app.route(route_v2 + '/btdocker/backup/<def_name>', methods=method_all)
@app.route(route_v2 + '/btdocker/container/<def_name>', methods=method_all)
@app.route(route_v2 + '/btdocker/compose/<def_name>', methods=method_all)
@app.route(route_v2 + '/btdocker/dkgroup/<def_name>', methods=method_all)
@app.route(route_v2 + '/btdocker/image/<def_name>', methods=method_all)
@app.route(route_v2 + '/btdocker/network/<def_name>', methods=method_all)
@app.route(route_v2 + '/btdocker/proxy/<def_name>', methods=method_all)
@app.route(route_v2 + '/btdocker/project/<def_name>', methods=method_all)
@app.route(route_v2 + '/btdocker/registry/<def_name>', methods=method_all)
@app.route(route_v2 + '/btdocker/setup/<def_name>', methods=method_all)
@app.route(route_v2 + '/btdocker/site/<def_name>', methods=method_all)
@app.route(route_v2 + '/btdocker/status/<def_name>', methods=method_all)
@app.route(route_v2 + '/btdocker/volume/<def_name>', methods=method_all)
def docker_v2(def_name):
    if request.method not in ['GET', 'POST']: return
    path_split = request.path.split("/")
    if len(path_split) < 5: return
    get = get_input()
    get.action = 'model'
    get.model_index = 'btDocker'
    get.mod_name = path_split[3]
    get.def_name = def_name

    comReturn = comm.local()
    if comReturn: return comReturn
    # p_path = public.get_plugin_path() + '/' + path_split[2]
    # if os.path.exists(p_path):
    #     return panel_other(get.model_index, get.mod_name, def_name)
    from panelDockerControllerV2 import DockerController
    controller_obj = DockerController()
    defs = ('model',)
    return publicObject(controller_obj, defs, None, get)


@app.route(route_v2 + '/dbmodel/<mod_name>/<def_name>', methods=method_all)
def dbmodel_v2(mod_name, def_name):
    comReturn = comm.local()
    if comReturn: return comReturn
    from panelDatabaseControllerV2 import DatabaseController
    database_obj = DatabaseController()
    defs = ('model',)
    get = get_input()
    get.action = 'model'
    get.mod_name = mod_name
    get.def_name = def_name

    return publicObject(database_obj, defs, None, get)


@app.route(route_v2 + '/files', methods=method_all)
def files_v2(pdata=None):
    # 文件管理
    comReturn = comm.local()
    if comReturn: return comReturn
    if request.method == method_get[0] and not request.args.get(
            'path') and not pdata:
        import system_v2
        data = system_v2.system().GetConcifInfo()
        data['recycle_bin'] = os.path.exists('data/recycle_bin.pl')
        data['lan'] = public.GetLan('files')
        data['js_random'] = get_js_random()
        return render_template('files.html', data=data)
    import files_v2
    filesObject = files_v2.files()
    defs = ('files_search', 'files_replace', 'get_replace_logs',
            'get_images_resize', 'add_files_rsync', 'get_file_attribute',
            'get_file_hash', 'CreateLink', 'get_progress', 'restore_website',
            'fix_permissions', 'get_all_back', 'restore_path_permissions',
            'del_path_premissions', 'get_path_premissions',
            'back_path_permissions', 'upload_file_exists', 'CheckExistsFiles',
            'GetExecLog', 'GetSearch', 'ExecShell', 'GetExecShellMsg',
            'exec_git', 'exec_composer', 'create_download_url', 'UploadFile',
            'GetDir','GetDirNew', 'CreateFile', 'CreateDir', 'DeleteDir', 'DeleteFile',
            'get_download_url_list', 'remove_download_url',
            'modify_download_url', 'CopyFile', 'CopyDir', 'MvFile',
            'GetFileBody', 'SaveFileBody', 'Zip', 'UnZip',
            'get_download_url_find', 'set_file_ps', 'SearchFiles', 'upload',
            'read_history', 're_history', 'auto_save_temp',
            'get_auto_save_body', 'get_videos', 'GetFileAccess',
            'SetFileAccess', 'GetDirSize', 'SetBatchData', 'BatchPaste',
            'install_rar', 'get_path_size', 'DownloadFile', 'GetTaskSpeed',
            'CloseLogs', 'InstallSoft', 'UninstallSoft', 'SaveTmpFile',
            'get_composer_version', 'exec_composer', 'update_composer',
            'GetTmpFile', 'del_files_store', 'add_files_store',
            'get_files_store', 'del_files_store_types',
            'add_files_store_types', 'exec_git', 'RemoveTask', 'ActionTask',
            'Re_Recycle_bin', 'Get_Recycle_bin', 'Del_Recycle_bin',
            'Close_Recycle_bin', 'Recycle_bin', 'file_webshell_check',
            'dir_webshell_check', 'files_search', 'files_replace',
            'get_replace_logs', 'get_sql_backup', 'test_path', 'upload_files_exists')

    return publicObject(filesObject, defs, None, pdata)


@app.route(route_v2 + '/crontab', methods=method_all)
@app.route(route_v2 + '/crontab/<action>', methods=method_all)
@app.route(route_v2 + '/crontab_ifame', methods=method_all)
def crontab_v2(pdata=None,action=None):
    # 计划任务
    comReturn = comm.local()
    if comReturn: return comReturn
    if request.method == method_get[0] and not pdata and not request.args:
        import system
        data = system.system().GetConcifInfo()
        data['lan'] = public.GetLan('crontab')
        data['js_random'] = get_js_random()
        if request.path in ['/crontab_ifame']:
            return render_template('crontab.html', data=data)
        return render_template('index1.html', data=data)

    import class_v2.crontab_v2 as crontab
    crontabObject = crontab.crontab()
    defs = (
        'set_cron_status_all', 'get_zone', 'get_domain', 'cancel_top', 'set_task_top', 'GetCrontab', 'AddCrontab',
        'GetDataList', 'GetLogs', 'DelLogs', 'download_logs', 'clear_logs',
        'DelCrontab', 'StartTask', 'set_cron_status', 'get_crond_find', 'set_atuo_start_syssafe',
        'modify_crond', 'get_backup_list', 'check_url_connecte', 'cloud_backup_download',
        'GetDatabases', 'get_crontab_types', 'add_crontab_type', 'remove_crontab_type',
        'modify_crontab_type_name', 'set_crontab_type', 'export_crontab_to_json', 'import_crontab_from_json',
        'set_rotate_log', 'get_rotate_log_config', 'get_restart_project_config', 'set_restart_project',
        'get_system_user_list','get_databases', 'get_auto_config', 'set_auto_config'
    )
    return publicObject(crontabObject, defs, None, pdata)


@app.route(route_v2 + '/soft', methods=method_all)
def soft_v2(pdata=None):
    # 软件商店页面
    comReturn = comm.local()
    if comReturn: return comReturn
    import system_v2
    data = system_v2.system().GetConcifInfo()
    data['lan'] = public.GetLan('soft')
    data['js_random'] = get_js_random()
    return render_template('soft.html', data=data)


@app.route(route_v2 + '/config', methods=method_all)
def config_v2(pdata=None):
    # 面板设置页面
    comReturn = comm.local()
    if comReturn: return comReturn

    if request.method == method_get[0] and not pdata:
        import system_v2, wxapp_v2, config_v2
        c_obj = config_v2.config()
        data = system_v2.system().GetConcifInfo()
        data['lan'] = public.GetLan('config')
        try:
            data['wx'] = wxapp_v2.wxapp().get_user_info(None)['msg']
        except:
            data['wx'] = 'INIT_WX_NOT_BIND'
        data['api'] = ''
        data['ipv6'] = ''
        sess_out_path = 'data/session_timeout.pl'
        if not os.path.exists(sess_out_path):
            public.writeFile(sess_out_path, '86400')
        s_time_tmp = public.readFile(sess_out_path)
        if not s_time_tmp: s_time_tmp = '0'
        data['session_timeout'] = int(s_time_tmp)
        if c_obj.get_ipv6_listen(None): data['ipv6'] = 'checked'
        if c_obj.get_token(None)['open']: data['api'] = 'checked'
        data['basic_auth'] = c_obj.get_basic_auth_stat(None)
        data['status_code'] = c_obj.get_not_auth_status()
        data['basic_auth']['value'] = public.getMsg('CLOSED')
        if data['basic_auth']['open']:
            data['basic_auth']['value'] = public.getMsg('OPENED')
        data['debug'] = ''
        data['js_random'] = get_js_random()
        if app.config['DEBUG']: data['debug'] = 'checked'
        data['is_local'] = ''
        if public.is_local(): data['is_local'] = 'checked'
        data['public_key'] = public.get_rsa_public_key().replace("\n", "")
        return render_template('config.html', data=data)
    import config_v2
    defs = (
        'send_by_telegram',
        'set_empty',
        'set_backup_notification',
        'get_panel_ssl_status',
        'set_file_deny',
        'del_file_deny',
        'get_file_deny',
        'set_improvement',
        'get_httpd_access_log_format_parameter',
        'set_httpd_format_log_to_website',
        'get_httpd_access_log_format',
        'del_httpd_access_log_format',
        'add_httpd_access_log_format',
        'get_nginx_access_log_format_parameter',
        'set_format_log_to_website',
        'get_nginx_access_log_format',
        'del_nginx_access_log_format',
        'set_click_logs',
        'get_node_config',
        'add_nginx_access_log_format',
        'get_ols_private_cache_status',
        'get_ols_value',
        'set_ols_value',
        'set_node_config',
        'get_ols_private_cache',
        'get_ols_static_cache',
        'set_ols_static_cache',
        'switch_ols_private_cache',
        'set_ols_private_cache',
        'set_coll_open',
        'get_qrcode_data',
        'check_two_step',
        'set_two_step_auth',
        'create_user',
        'remove_user',
        'modify_user',
        'get_key',
        'get_php_session_path',
        'set_php_session_path',
        'get_cert_source',
        'get_users',
        'set_request_iptype',
        'set_local',
        'set_debug',
        'get_panel_error_logs',
        'clean_panel_error_logs',
        'get_menu_list',
        'set_hide_menu_list',
        'get_basic_auth_stat',
        'set_basic_auth',
        'get_cli_php_version',
        'get_tmp_token',
        'get_temp_login',
        'set_temp_login',
        'remove_temp_login',
        'clear_temp_login',
        'set_site_total_setup',
        'get_temp_login_logs',
        'set_cli_php_version',
        'DelOldSession',
        'GetSessionCount',
        'SetSessionConf',
        'set_not_auth_status',
        'GetSessionConf',
        'get_ipv6_listen',
        'set_ipv6_status',
        'GetApacheValue',
        'SetApacheValue',
        'install_msg_module',
        'GetNginxValue',
        'SetNginxValue',
        'get_token',
        'set_token',
        'set_admin_path',
        'is_pro',
        'set_msg_config',
        'get_php_config',
        'get_config',
        'SavePanelSSL',
        'GetPanelSSL',
        'GetPHPConf',
        'SetPHPConf',
        'uninstall_msg_module',
        'GetPanelList',
        'AddPanelInfo',
        'SetPanelInfo',
        'DelPanelInfo',
        'ClickPanelInfo',
        'SetPanelSSL',
        'get_msg_configs',
        'SetTemplates',
        'Set502',
        'setPassword',
        'setUsername',
        'setPanel',
        'clearBackup',
        'setPathInfo',
        'setPHPMaxSize',
        'get_msg_fun',
        'getFpmConfig',
        'setFpmConfig',
        'setPHPMaxTime',
        'syncDate',
        'setPHPDisable',
        'SetControl',
        'get_settings2',
        'del_tg_info',
        'set_tg_bot',
        'ClosePanel',
        'AutoUpdatePanel',
        'SetPanelLock',
        'return_mail_list',
        'del_mail_list',
        'add_mail_address',
        'user_mail_send',
        'get_user_mail',
        'set_dingding',
        'get_dingding',
        'get_settings',
        'user_stmp_mail_send',
        'user_dingding_send',
        'get_login_send',
        'set_login_send',
        'clear_login_send',
        'get_login_log',
        'login_ipwhite',
        'set_ssl_verify',
        'get_ssl_verify',
        'get_password_config',
        'set_password_expire',
        'set_password_safe',
        'setlastPassword',
        'get_module_template',
        # 新增nps评分
        'write_nps_new',
        'get_nps_new',
        "check_nps",
        'get_translations',
        'get_login_translations',
        # 语言包 测试接口
        # 'get_language',
        # 'get_languageinfo',
        'set_language',
        'download_language',
        'upload_language',
        # 设置ua限制
        'set_ua',
        'get_limit_ua',
        'modify_ua',
        'delete_ua',
        'set_cdn_status',
        'set_auto_favicon',
        'set_theme',
        'set_panel_asset',
        'get_panel_asset',
    )
    return publicObject(config_v2.config(), defs, None, pdata)


@app.route(route_v2 + '/ajax', methods=method_all)
def ajax_v2(pdata=None):
    # 面板系统服务状态接口
    comReturn = comm.local()
    if comReturn: return comReturn
    import ajax_v2
    ajaxObject = ajax_v2.ajax()
    defs = ('get_lines', 'php_info', 'change_phpmyadmin_ssl_port',
            'set_phpmyadmin_ssl', 'get_phpmyadmin_ssl', 'get_pd',
            'check_user_auth', 'to_not_beta', 'get_beta_logs', 'apple_beta',
            'GetApacheStatus', 'GetCloudHtml', 'get_pay_type',
            'get_load_average', 'GetOpeLogs', 'GetFpmLogs', 'GetFpmSlowLogs',
            'SetMemcachedCache', 'GetMemcachedStatus', 'GetRedisStatus',
            'GetWarning', 'SetWarning', 'CheckLogin', 'GetSpeed', 'GetAd',
            'phpSort', 'ToPunycode', 'GetBetaStatus', 'SetBeta',
            'setPHPMyAdmin', 'delClose', 'KillProcess', 'GetPHPInfo',
            'GetQiniuFileList', 'get_process_tops', 'get_process_cpu_high',
            'UninstallLib', 'InstallLib', 'SetQiniuAS', 'GetQiniuAS',
            'GetLibList', 'GetProcessList', 'GetNetWorkList', 'GetNginxStatus',
            'GetPHPStatus', 'GetTaskCount', 'GetSoftList', 'GetNetWorkIo',
            'GetDiskIo', 'GetCpuIo', 'CheckInstalled', 'UpdatePanel',
            'GetInstalled', 'GetPHPConfig', 'SetPHPConfig', 'log_analysis',
            'speed_log', 'get_result', 'get_detailed', 'ignore_version')

    return publicObject(ajaxObject, defs, None, pdata)


@app.route(route_v2 + '/system', methods=method_all)
def system_v2(pdata=None):
    # 面板系统状态接口
    comReturn = comm.local()
    if comReturn: return comReturn
    import system_v2
    sysObject = system_v2.system()
    defs = ('get_io_info', 'UpdatePro', 'GetAllInfo', 'GetNetWorkApi',
            'GetLoadAverage', 'ClearSystem', 'GetNetWorkOld', 'GetNetWork',
            'GetDiskInfo', 'GetCpuInfo', 'GetBootTime', 'GetSystemVersion',
            'GetMemInfo', 'GetSystemTotal', 'GetConcifInfo', 'ServiceAdmin',
            'ReWeb', 'RestartServer', 'ReMemory', 'RepPanel', 'mark_reboot_read')
    return publicObject(sysObject, defs, None, pdata)


@app.route(route_v2 + '/deployment', methods=method_all)
def deployment_v2(pdata=None):
    # 一键部署接口
    comReturn = comm.local()
    if comReturn: return comReturn
    import plugin_deployment_v2
    sysObject = plugin_deployment_v2.plugin_deployment()
    defs = ('GetList', 'AddPackage', 'DelPackage', 'SetupPackage', 'GetSpeed',
            'GetPackageOther')
    return publicObject(sysObject, defs, None, pdata)


@app.route(route_v2 + '/data', methods=method_all)
@app.route(route_v2 + '/panel_data', methods=method_all)
def panel_data_v2(pdata=None):
    # 从数据库获取数据接口
    comReturn = comm.local()
    if comReturn: return comReturn
    import data_v2
    dataObject = data_v2.data()
    defs = ('setPs', 'getData', 'getFind', 'getKey', 'getSiteWafConfig', 'getSiteThirtyTotal','get_wp_classification','get_wp_site_list')
    return publicObject(dataObject, defs, None, pdata)


# 计划弃置
@app.route(route_v2 + '/ssl', methods=method_all)
def ssl_v2(pdata=None):
    # 商业SSL证书申请接口
    comReturn = comm.local()
    if comReturn: return comReturn
    import panel_ssl_v2
    toObject = panel_ssl_v2.panelSSL()
    defs = (
        'check_url_txt',
        'RemoveCert',
        'renew_lets_ssl',
        'SetCertToSite',
        'GetCertList',
        'SaveCert',
        'GetCert',
        'GetCertName',
        'again_verify',
        'DelToken',
        'GetToken',
        'GetToken_New',
        'GetUserInfo',
        'GetOrderList',
        'GetDVSSL',
        'Completed',
        'SyncOrder',
        'download_cert',
        'set_cert',
        'cancel_cert_order',
        'get_order_list',
        'get_order_find',
        'apply_order_pay',
        'get_pay_status',
        'apply_order',
        'get_verify_info',
        'get_verify_result',
        'get_product_list',
        'set_verify_info',
        'GetSSLInfo',
        'downloadCRT',
        'GetSSLProduct',
        'Renew_SSL',
        'Get_Renew_SSL',
        # 新增 购买证书对接接口
        'get_product_list_v2',
        'apply_cert_order_pay',
        'get_cert_admin',
        'apply_order_ca',
        'apply_cert_install_pay',
        'verify_mail_any',

        # 'pay_test'
    )
    get = get_input()

    if get.action == 'download_cert':
        from io import BytesIO
        import base64
        result = toObject.download_cert(get)
        # public.print_log("@@@@@@@@@@@@@@@@@@@@@@@@@@@@1111111111111111 result: {}".format(result))
        # {'success': False, 'res': '[code: 0] no data [file: /www/wwwroot/192.168.1.139/app/Api/Cert/controllers/Cert.php] [line: 955]', 'nonce': 1706498844}

        fp = BytesIO(base64.b64decode(result['res']['data']))
        return send_file(fp,
                         download_name=result['res']['filename'],
                         as_attachment=True,
                         mimetype='application/zip')
    result = publicObject(toObject, defs, get.action, get)
    return result


@app.route(route_v2 + "/business_ssl", methods=method_all)
def business_ssl(pdata=None):
    # 商业SSL证书申请接口
    comReturn = comm.local()
    if comReturn: return comReturn
    from ssl_domainModelV2.business_ssl import BusinessSSL
    toObject = BusinessSSL()
    defs = (
        'apply_cert_install_pay',
        'get_verify_result',
        'download_cert',
        'get_order_list',
        'get_order_find',
        'get_product_list',
        'apply_cert_order_pay',
        'get_cert_admin',
        'apply_order_ca',
        'check_domain_suitable',
        'list_business_ssl',
        'renew_cert_order',
        'check_url_txt',
        'again_verify',
    )
    get = get_input()

    if get.action != "download_cert":
        result = publicObject(toObject, defs, get.action, get)
        return result

    from io import BytesIO
    import base64
    result = toObject.download_cert(get)
    # {'success': False, 'res': '[code: 0] no data [file: /www/wwwroot/192.168.1.139/app/Api/Cert/controllers/Cert.php] [line: 955]', 'nonce': 1706498844}
    fp = BytesIO(base64.b64decode(result['res']['data']))
    return send_file(
        fp,
        download_name=result['res']['filename'],
        as_attachment=True,
        mimetype='application/zip',
    )


@app.route(route_v2 + '/ssl_domain', methods=method_all)
def domain_v2(pdata=None):
    # 域名管理
    comReturn = comm.local()
    if comReturn: return comReturn
    from ssl_domainModelV2.api import DomainObject
    defs = (
        "get_sites",
        "sync_dns_info",
        "get_dns_support",
        "create_dns_api",
        "delete_dns_api",
        "list_dns_api",
        "edit_dns_api",
        "list_dns_record",
        "create_dns_record",
        "delete_dns_record",
        "edit_dns_record",
        "list_domain_details",
        "list_ssl_info",
        "download_cert",
        # "renew_cert",
        "one_cilck_renew",
        "renew_cert_process",
        "manual_apply_check",
        "manual_apply_vaild",
        "apply_new_ssl",
        "upload_cert",
        "switch_auto_renew",
        "switch_ssl_alarm",
        "cert_domain_list",
        "cert_deploy_sites",
        "cert_deploy_mails",
        "cert_deploy_panel",
        "remove_cert",
        "check_domain_automatic",
        "ssl_tasks_status",
        "get_panel_domain",
        "set_panel_domain_ssl",
        "mail_record_check",
    )
    return publicObject(DomainObject(), defs, None, pdata)

@app.route(route_v2 + '/ssl_dns', methods=method_all)
def ssl_dns_v2(pdata=None):
    # aaDns管理
    comReturn = comm.local()
    if comReturn: return comReturn
    from ssl_dnsV2.api import DnsApiObject
    defs = (
        "install_pdns",
        "get_status",
        "change_status",
        "add_zone",
        "del_zone",
        "set_nameserver",
        "get_nameserver",
        "get_soa",
        "set_soa",
        "get_logger",
        "clear_logger",
        "add_dmarc",
        "add_dkim_spf",
        "dns_checker",
        "fix_zone",
        "set_ttl_batch",
    )
    return publicObject(DnsApiObject(), defs, None, pdata)

@app.route(route_v2 + '/dns_api', methods=method_all)
def dns_api_v2(pdata=None):
    # dns api 开放, 子面板调用
    comReturn = comm.local()
    if comReturn: return comReturn
    from ssl_domainModelV2.external_api import SubPanelApi
    defs = (
        "account_create_record",
        "account_list_ssl_info",
        "account_domain_provider",
    )
    return publicObject(SubPanelApi(), defs, None, pdata)



@app.route(route_v2 + '/adminer_manager', methods=method_all)
def adminer_manager_v2(pdata=None):
    comReturn = comm.local()
    if comReturn:
        return comReturn
    from adminer.api import AdminerApi
    defs = (
        "support_versions",
        "install",
        "repair",
        "uninstall",
        "get_status",
        "switch_php",
        "switch_port",
    )
    return publicObject(AdminerApi(), defs, None, pdata)

@app.route(route_v2 + '/task', methods=method_all)
def task_v2(pdata=None):
    # 后台任务接口
    comReturn = comm.local()
    if comReturn: return comReturn
    import panel_task_v2
    toObject = panel_task_v2.bt_task()
    defs = ('get_task_lists', 'remove_task', 'get_task_find',
            "get_task_log_by_id")
    result = publicObject(toObject, defs, None, pdata)
    return result


@app.route(route_v2 + '/plugin', methods=method_all)
def plugin_v2(pdata=None):
    # 插件系统接口
    comReturn = comm.local()
    if comReturn: return comReturn
    import panel_plugin_v2
    pluginObject = panel_plugin_v2.panelPlugin()
    defs = ('get_usually_plugin', 'check_install_limit', 'set_score',
            'get_score', 'update_zip', 'input_zip', 'export_zip', 'add_index',
            'remove_index', 'sort_index', 'install_plugin', 'uninstall_plugin',
            'get_soft_find', 'get_index_list', 'get_soft_list',
            'get_cloud_list', 'check_deps', 'flush_cache', 'GetCloudWarning',
            'install', 'unInstall', 'getPluginList', 'getPluginInfo',
            'get_make_args', 'add_make_args', 'getPluginStatus',
            'setPluginStatus', 'a', 'getCloudPlugin', 'getConfigHtml',
            'savePluginSort', 'del_make_args', 'set_make_args')
    return publicObject(pluginObject, defs, None, pdata)


@app.route(route_v2 + '/wxapp', methods=method_all)
@app.route(route_v2 + '/panel_wxapp', methods=method_all)
def panel_wxapp_v2(pdata=None):
    # 微信小程序绑定接口
    comReturn = comm.local()
    if comReturn: return comReturn
    import wxapp_v2
    toObject = wxapp_v2.wxapp()
    defs = ('blind', 'get_safe_log', 'blind_result', 'get_user_info',
            'blind_del', 'blind_qrcode')
    result = publicObject(toObject, defs, None, pdata)
    return result


@app.route(route_v2 + '/auth', methods=method_all)
def auth_v2(pdata=None):
    # 面板认证接口
    comReturn = comm.local()
    if comReturn: return comReturn
    import panel_auth_v2
    toObject = panel_auth_v2.panelAuth()
    defs = ('free_trial', 'renew_product_auth', 'auth_activate',
            'get_product_auth', 'get_product_auth_all','get_stripe_session_id',
            'get_re_order_status_plugin', 'create_plugin_other_order',
            'get_order_stat', 'get_voucher_plugin','get_voucher_plugin_all',
            'create_order_voucher_plugin', 'get_product_discount_by',
            'get_re_order_status', 'create_order_voucher', 'create_order',
            'get_order_status', 'get_voucher', 'flush_pay_status',
            'create_serverid', 'check_serverid', 'get_plugin_list',
            'check_plugin', 'get_buy_code', 'check_pay_status',
            'get_renew_code', 'check_renew_code', 'get_business_plugin',
            'get_ad_list', 'check_plugin_end', 'get_plugin_price',
            'get_plugin_remarks', 'get_paypal_session_id',
            'check_paypal_status', 'get_wx_order_status', 'get_apply_copon',
            'get_coupon_list', 'ignore_coupon_time', 'set_user_adviser', 'rest_unbind_count',
            'unbind_authorization', 'get_all_voucher_plugin', 'get_pay_unbind_count',
            'get_coupons', 'get_credits', 'create_with_credit_by_panel', 'get_last_paid_time',
            'get_all_coupons', 'detect_order_status',
            'get_expand_pack_prices',
            )
    result = publicObject(toObject, defs, None, pdata)
    return result


@app.route(route_v2 + '/download', methods=method_get)
def download_v2():
    # 文件下载接口
    comReturn = comm.local()
    if comReturn: return comReturn
    filename = request.args.get('filename')
    if filename.find('|') != -1:
        filename = filename.split('|')[1]
    if not filename:
        return public.ReturnJson(False, "INIT_ARGS_ERR"), json_header

    if filename in [
        'alioss', 'qiniu', 'upyun', 'txcos', 'ftp', 'msonedrive',
        'gcloud_storage', 'gdrive', 'aws_s3', 'obs', 'bos'
    ]:
        return panel_cloud(False)

    # === 限定下载根目录 ===
    import html
    filepath = html.unescape(filename.replace('\x00', ''))
    if '..' in filepath.split('/') or '..' in filepath.split('\\'):
        return public.ReturnJson(False, "INVALID PATH"), json_header
    filename = os.path.abspath(filepath)
    if not os.path.exists(filename):
        return public.ReturnJson(False, "File not exists"), json_header
    if os.path.isdir(filename):
        return public.ReturnJson(False, "The catalog is not downloadable"), json_header

    try:
        import stat
        file_stat = os.stat(filename)
        if stat.S_ISSOCK(file_stat.st_mode):
            return public.ReturnJson(False, "Unix domain socket files are not downloadable"), json_header
        elif stat.S_ISCHR(file_stat.st_mode):
            return public.ReturnJson(False, "Character device files cannot be downloaded"), json_header
        elif stat.S_ISBLK(file_stat.st_mode):
            return public.ReturnJson(False, "Block device files are not downloadable"), json_header
        elif stat.S_ISFIFO(file_stat.st_mode):
            return public.ReturnJson(False, "FIFO pipeline files are not downloadable"), json_header
    except:
        pass

    if request.args.get('play') == 'true':
        import panelVideo
        start, end = panelVideo.get_range(request)
        g.return_message = True
        return panelVideo.partial_response(filename, start, end)
    else:
        mimetype = "application/octet-stream"
        extName = filename.split('.')[-1]
        if extName in ['png', 'gif', 'jpeg', 'jpg']: mimetype = None
        public.WriteLog("TYPE_FILE", 'FILE_DOWNLOAD',
                        (filename, public.GetClientIp()))
        g.return_message = True
        if not os.path.exists(filename):
            return public.ReturnJson(False, "File not exists"), json_header
        return send_file(filename,
                         mimetype=mimetype,
                         as_attachment=True,
                         etag=True,
                         conditional=True,
                         download_name=os.path.basename(filename),
                         max_age=0)


@app.route(route_v2 + '/cloud', methods=method_all)
def panel_cloud_v2(is_csrf=True):
    # 从对像存储下载备份文件接口
    comReturn = comm.local()
    if comReturn: return comReturn
    if is_csrf:
        if not check_csrf():
            return public.ReturnJson(False, 'INIT_CSRF_ERR'), json_header
    get = get_input()
    _filename = get.filename
    plugin_name = ""
    if _filename.find('|') != -1:
        plugin_name = get.filename.split('|')[1]
    else:
        plugin_name = get.filename

    if not os.path.exists('plugin/' + plugin_name + '/' + plugin_name +
                          '_main.py'):
        return public.returnJson(
            False, 'The specified plugin does not exist!'), json_header
    public.package_path_append('plugin/' + plugin_name)
    plugin_main = __import__(plugin_name + '_main')
    public.mod_reload(plugin_main)
    tmp = eval("plugin_main.%s_main()" % plugin_name)
    if not hasattr(tmp, 'download_file'):
        return public.returnJson(
            False,
            'Specified plugin has no file download function!'), json_header
    download_url = tmp.download_file(get.name)
    if plugin_name == 'ftp':
        if download_url.find("ftp") != 0:
            download_url = "ftp://" + download_url
    else:
        if download_url.find('http') != 0:
            download_url = 'http://' + download_url

    if "toserver" in get and get.toserver == "true":
        download_dir = "/tmp/"
        if "download_dir" in get:
            download_dir = get.download_dir
        local_file = os.path.join(download_dir, get.name)

        input_from_local = False
        if "input_from_local" in get:
            input_from_local = True if get.input_from_local == "true" else False

        if input_from_local:
            if os.path.isfile(local_file):
                return {
                    "status": True,
                    "msg":
                        "The file already exists and will be restored locally.",
                    "task_id": -1,
                    "local_file": local_file
                }
        from panel_task_v2 import bt_task
        task_obj = bt_task()
        task_id = task_obj.create_task('Download file', 1, download_url,
                                       local_file)
        return {
            "status": True,
            "msg": "The download task was created successfully",
            "local_file": local_file,
            "task_id": task_id
        }

    return redirect(download_url)


@app.route(route_v2 + '/btwaf_error', methods=method_get)
def btwaf_error_v2():
    # 图标
    comReturn = comm.local()
    if comReturn: return comReturn
    get = get_input()
    p_path = os.path.join('/www/server/panel/plugin/', "btwaf")
    if not os.path.exists(p_path):
        if get.name == 'btwaf' and get.fun == 'index':
            return render_template('error3.html', data={})
    return render_template('error3.html', data={})


@app.route(route_v2 + '/favicon.ico', methods=method_get)
def send_favicon_v2():
    # 图标
    comReturn = comm.local()
    if comReturn: return abort(404)
    s_file = '/www/server/panel/BTPanel/static/favicon.ico'
    if not os.path.exists(s_file): return abort(404)
    return send_file(s_file, conditional=True, etag=True)


@app.route(route_v2 + '/rspamd', defaults={'path': ''}, methods=method_all)
@app.route(route_v2 + '/rspamd/<path:path>', methods=method_all)
def proxy_rspamd_requests_v2(path):
    comReturn = comm.local()
    if comReturn: return comReturn
    param = str(request.url).split('?')
    param = "" if len(param) < 2 else param[-1]
    import requests
    headers = {}
    for h in request.headers.keys():
        headers[h] = request.headers[h]
    if request.method == "GET":
        if re.search(r"\.(js|css)$", path):
            return send_file('/usr/share/rspamd/www/rspamd/' + path,
                             conditional=True,
                             etag=True)
        if path == "/":
            return send_file('/usr/share/rspamd/www/rspamd/',
                             conditional=True,
                             etag=True)
        url = "http://127.0.0.1:11334/rspamd/" + path + "?" + param
        for i in [
            'stat', 'auth', 'neighbours', 'list_extractors',
            'list_transforms', 'graph', 'maps', 'actions', 'symbols',
            'history', 'errors', 'check_selector', 'saveactions',
            'savesymbols', 'getmap'
        ]:
            if i in path:
                url = "http://127.0.0.1:11334/" + path + "?" + param
        req = requests.get(url, headers=headers, stream=True)
        return Resp(stream_with_context(req.iter_content()),
                    content_type=req.headers['content-type'])
    else:
        url = "http://127.0.0.1:11334/" + path
        for i in request.form.keys():
            data = '{}='.format(i)
        # public.writeFile('/tmp/2',data+"\n","a+")
        req = requests.post(url, data=data, headers=headers, stream=True)

        return Resp(stream_with_context(req.iter_content()),
                    content_type=req.headers['content-type'])


@app.route(route_v2 + '/tips', methods=method_get)
def tips_v2():
    # 提示页面
    comReturn = comm.local()
    if comReturn: return abort(404)
    get = get_input()
    if len(get.get_items().keys()) > 1: return abort(404)
    return render_template('tips.html')


# ======================普通路由区end============================#

# ======================严格排查区域start============================#


@app.route(route_v2 + '/login', methods=method_all)
@app.route(route_v2 + route_path, methods=method_all)
@app.route(route_v2 + route_path + '/', methods=method_all)
def login_v2():
    # 面板登录接口
    if os.path.exists('install.pl'): return redirect('/install')
    global admin_check_auth, admin_path, route_path
    is_auth_path = False
    if admin_path != '/bt' and os.path.exists(
            admin_path_file) and not 'admin_auth' in session:
        is_auth_path = True
    # 登录输入验证
    if request.method == method_post[0]:
        if is_auth_path:
            g.auth_error = True
            return public.error_not_login(None)
        v_list = ['username', 'password', 'code', 'vcode', 'cdn_url']
        for v in v_list:
            if v in ['username', 'password']: continue
            pv = request.form.get(v, '').strip()
            if v == 'cdn_url':
                if len(pv) > 32:
                    return public.return_msg_gettext(
                        False, 'Wrong parameter length!'), json_header
                if not re.match(r"^[\w\.-]+$", pv):
                    public.return_msg_gettext(
                        False, 'Wrong parameter format!'), json_header
                continue

            if not pv: continue
            p_len = 32
            if v == 'code': p_len = 4
            if v == 'vcode': p_len = 6
            if len(pv) != p_len:
                if v == 'code':
                    return public.returnJson(
                        False, 'Verification code length error!'), json_header
                return public.returnJson(
                    False, 'Wrong parameter length!'), json_header
            if not re.match(r"^\w+$", pv):
                return public.returnJson(
                    False, 'Wrong parameter format!'), json_header

        for n in request.form.keys():
            if not n in v_list:
                return public.returnJson(
                    False,
                    'There can be no extra parameters in the login parameters'
                ), json_header

    get = get_input()
    import user_login_v2
    if hasattr(get, 'tmp_token'):
        result = user_login_v2.userlogin().request_tmp(get)
        return is_login(result)
    # 过滤爬虫
    if public.is_spider(): return abort(404)
    if hasattr(get, 'dologin'):
        login_path = '/login'
        if not 'login' in session: return redirect(login_path)
        if os.path.exists(admin_path_file): login_path = route_path
        if session['login'] != False:
            session['login'] = False
            cache.set('dologin', True)
            public.write_log_gettext(
                'Logout', 'Client: {}, has manually exited the panel',
                (public.GetClientIp() + ":" +
                 str(request.environ.get('REMOTE_PORT')),))
            if 'tmp_login_expire' in session:
                s_file = 'data/session/{}'.format(session['tmp_login_id'])
                if os.path.exists(s_file):
                    os.remove(s_file)
            token_key = public.get_csrf_html_token_key()
            if token_key in session:
                del (session[token_key])
            session.clear()
            sess_file = 'data/sess_files/' + public.get_sess_key()
            if os.path.exists(sess_file):
                try:
                    os.remove(sess_file)
                except:
                    pass
            sess_tmp_file = public.get_full_session_file()
            if os.path.exists(sess_tmp_file): os.remove(sess_tmp_file)
            g.dologin = True
            return redirect(public.get_admin_path())

    if is_auth_path:
        if route_path != request.path and route_path + '/' != request.path:
            referer = request.headers.get('Referer', 'err')
            referer_tmp = referer.split('/')
            referer_path = referer_tmp[-1]
            if referer_path == '':
                referer_path = referer_tmp[-2]
            if route_path != '/' + referer_path:
                g.auth_error = True
                # return render_template('autherr.html')
                return public.error_not_login(None)

    session['admin_auth'] = True
    comReturn = common.panelSetup().init()
    if comReturn: return comReturn

    if request.method == method_post[0]:
        result = userlogin.userlogin().request_post(get)
        return is_login(result)

    if request.method == method_get[0]:
        result = userlogin.userlogin().request_get(get)
        if result:
            return result
        data = {}
        data['lan'] = public.GetLan('login')
        data['hosts'] = '[]'
        hosts_file = 'plugin/static_cdn/hosts.json'
        if os.path.exists(hosts_file):
            data['hosts'] = public.get_cdn_hosts()
            if type(data['hosts']) == dict:
                data['hosts'] = '[]'
            else:
                data['hosts'] = json.dumps(data['hosts'])
        data['app_login'] = os.path.exists('data/app_login.pl')
        public.cache_set(
            public.Md5(
                uuid.UUID(int=uuid.getnode()).hex[-12:] +
                public.GetClientIp()), 'check', 360)

        # 生成登录token
        last_key = 'last_login_token'
        # -----------
        last_time_key = 'last_login_token_time'
        s_time = int(time.time())
        if last_key in session and last_time_key in session:
            # 10秒内不重复生成token
            if s_time - session[last_time_key] > 10:
                session[last_key] = public.GetRandomString(32)
                session[last_time_key] = s_time
        else:
            session[last_key] = public.GetRandomString(32)
            session[last_time_key] = s_time

        data[last_key] = session[last_key]
        data['public_key'] = public.get_rsa_public_key()
        return render_template('login.html', data=data)


@app.route(route_v2 + '/close', methods=method_get)
def close_v2():
    # 面板已关闭页面
    if not os.path.exists('data/close.pl'): return redirect('/')
    data = {}
    data['lan'] = public.getLan('close')
    return render_template('close.html', data=data)


@app.route(route_v2 + '/get_app_bind_status', methods=method_all)
def get_app_bind_status_v2(pdata=None):
    # APP绑定状态查询
    if not public.check_app('app_bind'): return abort(404)
    get = get_input()
    if len(get.get_items().keys()) > 2: return 'There are meaningless parameters!'
    v_list = ['bind_token', 'data']
    for n in get.get_items().keys():
        if not n in v_list:
            return public.returnJson(
                False, 'There can be no redundant parameters'), json_header
    import panel_api_v2
    api_object = panel_api_v2.panelApi()
    return json.dumps(api_object.get_app_bind_status(get_input())), json_header


@app.route(route_v2 + '/check_bind', methods=method_all)
def check_bind_v2(pdata=None):
    # APP绑定查询
    if not public.check_app('app_bind'): return abort(404)
    get = get_input()
    if len(get.get_items().keys()) > 4: return 'There are meaningless parameters!'
    v_list = ['bind_token', 'client_brand', 'client_model', 'data']
    for n in get.get_items().keys():
        if not n in v_list:
            return public.returnJson(
                False, 'There can be no redundant parameters'), json_header
    import panel_api_v2
    api_object = panel_api_v2.panelApi()
    return json.dumps(api_object.check_bind(get_input())), json_header


@app.route(route_v2 + '/code', methods=method_get)
def code_v2():
    if not 'code' in session: return ''
    if not session['code']: return ''
    # 获取图片验证码
    try:
        import vilidate_v2
    except:
        public.ExecShell("btpip install Pillow -I")
        return "Pillow not install!"
    vie = vilidate_v2.vieCode()
    codeImage = vie.GetCodeImage(80, 4)
    if sys.version_info[0] == 2:
        try:
            from cStringIO import StringIO
        except:
            from StringIO import StringIO
        out = StringIO()
    else:
        from io import BytesIO
        out = BytesIO()
    codeImage[0].save(out, "png")
    cache.set("codeStr", public.md5("".join(codeImage[1]).lower()), 180)
    cache.set("codeOut", 1, 0.1)
    out.seek(0)
    return send_file(out, mimetype='image/png', max_age=0)


@app.route(route_v2 + '/down/<token>', methods=method_all)
def down_v2(token=None, fname=None):
    # 文件分享对外接口
    try:
        if public.M('download_token').count() == 0: return abort(404)
        fname = request.args.get('fname')
        if fname:
            if (len(fname) > 256): return abort(404)
        if fname: fname = fname.strip('/')
        if not token: return abort(404)
        if len(token) > 48: return abort(404)
        char_list = [
            '\\', '/', ':', '*', '?', '"', '<', '>', '|', ';', '&', '`'
        ]
        for char in char_list:
            if char in token: return abort(404)
        if not request.args.get('play') in ['true', None, '']:
            return abort(404)
        args = get_input()
        v_list = ['fname', 'play', 'file_password', 'data']
        for n in args.get_items().keys():
            if not n in v_list:
                return public.returnJson(
                    False, 'There can be no redundant parameters'), json_header
        if not re.match(r"^[\w\.]+$", token): return abort(404)
        find = public.M('download_token').where('token=?', (token,)).find()

        if not find: return abort(404)
        if time.time() > int(find['expire']): return abort(404)

        if not os.path.exists(find['filename']): return abort(404)
        if find['password'] and not token in session:
            if 'file_password' in args:
                if not re.match(r"^\w+$", args.file_password):
                    return public.ReturnJson(False,
                                             'Wrong password!'), json_header
                if re.match(r"^\d+$", args.file_password):
                    args.file_password = str(int(args.file_password))
                    args.file_password += ".0"
                if args.file_password != str(find['password']):
                    return public.ReturnJson(False,
                                             'Wrong password!'), json_header
                session[token] = 1
                session['down'] = True
            else:
                pdata = {
                    "to_path": "",
                    "src_path": find['filename'],
                    "password": True,
                    "filename": find['filename'].split('/')[-1],
                    "ps": find['ps'],
                    "total": find['total'],
                    "token": find['token'],
                    "expire": public.format_date(times=find['expire'])
                }
                session['down'] = True
                return render_template('down.html', data=pdata)

        if not find['password']:
            session['down'] = True
            session[token] = 1

        if session[token] != 1:
            return abort(404)

        filename = find['filename']
        if fname:
            filename = os.path.join(filename, fname)
            if not public.path_safe_check(fname, False): return abort(404)
            if os.path.isdir(filename):
                return get_dir_down(filename, token, find)
        else:
            if os.path.isdir(filename):
                return get_dir_down(filename, token, find)

        if request.args.get('play') == 'true':
            import panel_video_v2
            start, end = panel_video_v2.get_range(request)
            return panel_video_v2.partial_response(filename, start, end)
        else:
            mimetype = "application/octet-stream"
            extName = filename.split('.')[-1]
            if extName in ['png', 'gif', 'jpeg', 'jpg']: mimetype = None
            b_name = os.path.basename(filename)
            return send_file(filename,
                             mimetype=mimetype,
                             as_attachment=True,
                             download_name=b_name,
                             max_age=0)
    except:
        return abort(404)


@app.route(route_v2 + '/database/mongodb/<def_name>', methods=method_all)
@app.route(route_v2 + '/database/pgsql/<def_name>', methods=method_all)
@app.route(route_v2 + '/database/redis/<def_name>', methods=method_all)
@app.route(route_v2 + '/database/sqlite/<def_name>', methods=method_all)
@app.route(route_v2 + '/database/sqlserver/<def_name>', methods=method_all)
def databaseModel_v2(def_name):
    if request.method not in ['GET', 'POST']: return
    path_split = request.path.split("/")
    if len(path_split) < 5: return
    comReturn = comm.local()
    if comReturn: return comReturn
    from panelDatabaseControllerV2 import DatabaseController
    project_obj = DatabaseController()
    defs = ('model',)
    get = get_input()
    get.action = 'model'
    get.mod_name = path_split[3]
    get.def_name = def_name
    return publicObject(project_obj, defs, None, get)


# 系统安全模型页面
# @app.route(route_v2+'/safe/<mod_name>/<def_name>', methods=method_all)
@app.route(route_v2 + '/safe/firewall/<def_name>', methods=method_all)
@app.route(route_v2 + '/safe/freeip/<def_name>', methods=method_all)
@app.route(route_v2 + '/safe/ips/<def_name>', methods=method_all)
@app.route(route_v2 + '/safe/security/<def_name>', methods=method_all)
@app.route(route_v2 + '/safe/ssh/<def_name>', methods=method_all)
@app.route(route_v2 + '/safe/syslog/<def_name>', methods=method_all)
def safeModel_v2(def_name):
    if request.method not in ['GET', 'POST']: return
    path_split = request.path.split("/")
    if len(path_split) < 5: return
    comReturn = comm.local()
    if comReturn: return comReturn
    from panelSafeControllerV2 import SafeController
    project_obj = SafeController()
    defs = ('model',)
    get = get_input()
    get.action = 'model'
    get.mod_name = path_split[3]
    get.def_name = def_name

    return publicObject(project_obj, defs, None, get)


# 通用模型路由
@app.route(route_v2 + '/panel/binlog/<def_name>', methods=method_all)
@app.route(route_v2 + '/panel/bt_check/<def_name>', methods=method_all)
@app.route(route_v2 + '/panel/clear/<def_name>', methods=method_all)
@app.route(route_v2 + '/panel/content/<def_name>', methods=method_all)
@app.route(route_v2 + '/panel/docker/<def_name>', methods=method_all)
@app.route(route_v2 + '/panel/go/<def_name>', methods=method_all)
@app.route(route_v2 + '/panel/java/<def_name>', methods=method_all)
@app.route(route_v2 + '/panel/nodejs/<def_name>', methods=method_all)
@app.route(route_v2 + '/panel/other/<def_name>', methods=method_all)
@app.route(route_v2 + '/panel/php/<def_name>', methods=method_all)
@app.route(route_v2 + '/panel/python/<def_name>', methods=method_all)
@app.route(route_v2 + '/panel/quota/<def_name>', methods=method_all)
@app.route(route_v2 + '/panel/quota/<def_name>', methods=method_all)
@app.route(route_v2 + '/panel/safe_detect/<def_name>', methods=method_all)
@app.route(route_v2 + '/panel/scanning/<def_name>', methods=method_all)
@app.route(route_v2 + '/panel/start_content/<def_name>', methods=method_all)
@app.route(route_v2 + '/panel/totle_db/<def_name>', methods=method_all)
@app.route(route_v2 + '/panel/webscanning/<def_name>', methods=method_all)
@app.route(route_v2 + '/panel/public/<def_name>', methods=method_all)
@app.route(route_v2 + '/monitor/process_management/<def_name>',
           methods=method_all)
@app.route(route_v2 + '/monitor/soft/<def_name>', methods=method_all)
@app.route(route_v2 + '/files/down/<def_name>', methods=method_all)
@app.route(route_v2 + '/files/gz/<def_name>', methods=method_all)
@app.route(route_v2 + '/files/logs/<def_name>', methods=method_all)
@app.route(route_v2 + '/files/rar/<def_name>', methods=method_all)
@app.route(route_v2 + '/files/search/<def_name>', methods=method_all)
@app.route(route_v2 + '/files/size/<def_name>', methods=method_all)
@app.route(route_v2 + '/files/upload/<def_name>', methods=method_all)
@app.route(route_v2 + '/files/zip/<def_name>', methods=method_all)
@app.route(route_v2 + '/logs/ftp/<def_name>', methods=method_all)
@app.route(route_v2 + '/logs/panel/<def_name>', methods=method_all)
@app.route(route_v2 + '/logs/site/<def_name>', methods=method_all)
@app.route(route_v2 + '/crontab/trigger/<def_name>', methods=method_all)
@app.route(route_v2 + '/crontab/script/<def_name>', methods=method_all)
def allModule_v2(def_name):
    if request.method not in ['GET', 'POST']: return
    path_split = request.path.split("/")
    if len(path_split) < 4: return
    comReturn = comm.local()
    if comReturn: return comReturn
    p_path = public.get_plugin_path() + '/' + path_split[2]

    defs = ('model',)
    get = get_input()
    get.model_index = path_split[2]
    get.action = 'model'
    get.mod_name = path_split[3]
    get.def_name = def_name
    if not request.path.startswith(route_v2 + '/monitor/') and os.path.exists(p_path):
        return panel_other(get.model_index, get.mod_name, def_name)

    from panelControllerV2 import Controller
    controller_obj = Controller()
    return publicObject(controller_obj, defs, None, get)


@app.route(route_v2 + '/public', methods=method_all)
def panel_public_v2():
    get = get_input()
    if len("{}".format(get.get_items())) > 1024 * 32:
        return 'ERROR'

    # 获取ping测试
    if 'get_ping' in get:
        try:
            import panel_ping_v2
            p = panel_ping_v2.Test()
            get = p.check(get)
            if not get: return 'ERROR'
            result = getattr(p, get['act'])(get)
            result_type = type(result)
            if str(result_type).find('Response') != -1: return result
            return public.getJson(result), json_header
        except:
            return abort(404)

    if public.cache_get(
            public.Md5(
                uuid.UUID(int=uuid.getnode()).hex[-12:] +
                public.GetClientIp())) != 'check':
        return abort(404)
    global admin_check_auth, admin_path, route_path, admin_path_file
    if admin_path != '/bt' and os.path.exists(
            admin_path_file) and not 'admin_auth' in session:
        return abort(404)
    v_list = ['fun', 'name', 'filename', 'data', 'secret_key']
    for n in get.get_items().keys():
        if not n in v_list:
            return abort(404)

    get.client_ip = public.GetClientIp()
    num_key = get.client_ip + '_wxapp'
    if not public.get_error_num(num_key, 10):
        return public.return_msg_gettext(
            False,
            '10 consecutive authentication failures are prohibited for 1 hour')
    if not hasattr(get, 'name'): get.name = ''
    if not hasattr(get, 'fun'): return abort(404)
    if not public.path_safe_check("%s/%s" % (get.name, get.fun)):
        return abort(404)
    if get.fun in ['login_qrcode', 'is_scan_ok', 'set_login']:
        # 检查是否验证过安全入口
        if admin_path != '/bt' and os.path.exists(
                admin_path_file) and not 'admin_auth' in session:
            return abort(404)
        # 验证是否绑定了设备
        if not public.check_app('app'):
            return public.return_msg_gettext(False, 'Unbound user')
        import wxapp_v2
        pluwx = wxapp_v2.wxapp()
        checks = pluwx._check(get)
        if type(checks) != bool or not checks:
            public.set_error_num(num_key)
            return public.getJson(checks), json_header
        data = public.getJson(eval('pluwx.' + get.fun + '(get)'))
        return data, json_header
    else:
        return abort(404)


@app.route(route_v2 + '/<name>/<fun>', methods=method_all)
@app.route(route_v2 + '/<name>/<fun>/<path:stype>', methods=method_all)
def panel_other_v2(name=None, fun=None, stype=None):

    # 插件接口
    if public.is_error_path():
        return redirect('/error', 302)
    if not name: return abort(404)
    if not re.match(r"^[\w\-]+$", name): return abort(404)
    if fun and not re.match(r"^[\w\-\.]+$", fun): return abort(404)
    if name != "mail_sys" or fun != "send_mail_http.json":
        comReturn = comm.local()
        if comReturn: return comReturn
        if not stype:
            tmp = fun.split('.')
            fun = tmp[0]
            if len(tmp) == 1: tmp.append('')
            stype = tmp[1]
        if fun:
            if name == 'btwaf' and fun == 'index':
                pass
            elif name == 'firewall' and fun == 'get_file':
                pass
            elif fun == 'static':
                pass
            elif stype == 'html':
                pass
            else:
                if public.get_csrf_cookie_token_key(
                ) in session and 'login' in session:
                    if not check_csrf():
                        return public.ReturnJson(
                            False,
                            'CSRF calibration failed, please login again'
                        ), json_header
        args = None
    else:
        p_path = public.get_plugin_path() + '/' + name
        if not os.path.exists(p_path): return abort(404)
        args = get_input()
        args_list = [
            'mail_from', 'password', 'mail_to', 'subject', 'content',
            'subtype', 'data'
        ]
        for k in args.get_items():
            if not k in args_list: return abort(404)

    is_accept = False
    if not fun: fun = 'index.html'
    if not stype:
        tmp = fun.split('.')
        fun = tmp[0]
        if len(tmp) == 1: tmp.append('')
        stype = tmp[1]

    if not name: name = 'coll'
    if not public.path_safe_check("%s/%s/%s" % (name, fun, stype)):
        return abort(404)
    if name.find('./') != -1 or not re.match(r"^[\w-]+$", name):
        return abort(404)
    if not name:
        return public.returnJson(
            False, 'Please pass in the plug-in name!'), json_header
    p_path = public.get_plugin_path() + '/' + name
    if not os.path.exists(p_path):
        if name == 'btwaf' and fun == 'index':
            pdata = {}
            import panel_plugin_v2
            plu_panel = panel_plugin_v2.panelPlugin()
            plugin_list = plu_panel.get_cloud_list()
            if not 'pro' in plugin_list: plugin_list['pro'] = -1
            for p in plugin_list['list']:
                if p['name'] in ['btwaf']:
                    if p['endtime'] != 0 and p['endtime'] < time.time():
                        pdata['error_msg'] = 1
                        break
            return render_template('error3.html', data=pdata)
        return abort(404)

    # 是否响插件应静态文件
    if fun == 'static':
        if stype.find('./') != -1 or not os.path.exists(p_path + '/static'):
            return abort(404)
        s_file = p_path + '/static/' + stype
        if s_file.find('..') != -1: return abort(404)
        if not re.match(r"^[\w\./-]+$", s_file): return abort(404)
        if not public.path_safe_check(s_file): return abort(404)
        if not os.path.exists(s_file): return abort(404)
        return send_file(s_file, conditional=True, etag=True)

    # 准备参数
    if not args: args = get_input()
    args.client_ip = public.GetClientIp()
    args.fun = fun

    # 初始化插件对象
    try:

        import PluginLoader
        try:
            args.s = fun
            data = PluginLoader.plugin_run(name, fun, args)
            if isinstance(data, dict):
                if 'status' in data and data['status'] == False and 'msg' in data:
                    if isinstance(data['msg'], str):
                        if data['msg'].find('加载失败') != -1 or data['msg'].find('Traceback ') == 0:
                            raise public.PanelError(data['msg'])
        except Exception as ex:
            if name == 'btwaf' and fun == 'index' and str(ex).find('未购买') != -1:
                return render_template('error3.html', data={})
            return public.get_error_object(None, plugin_name=name)

        r_type = type(data)
        if r_type in [Response, Resp]:
            return data

        # 处理响应
        if stype == 'json':  # 响应JSON
            # 兼容btwaf插件 v2调用改返回 v2/btwaf/xxx.json
            if name == 'btwaf':
                # public.print_log("插件调用22---{}".format(type(data)))
                if type(data) == dict:
                    if 'msg' in data:
                        status = 0 if data['status'] else -1
                        data = public.return_message(status, 0, data['msg'])
                    else:
                        data = public.return_message(0, 0, data)
                else:
                    data = public.return_message(0, 0, data)
            return public.getJson(data), json_header
        elif stype == 'html':  # 使用模板
            t_path_root = p_path + '/templates/'
            t_path = t_path_root + fun + '.html'
            if not os.path.exists(t_path):
                return public.returnJson(
                    False,
                    'The specified template does not exist!'), json_header
            t_body = public.readFile(t_path)

            # 处理模板包含
            rep = r'{%\s?include\s"(.+)"\s?%}'
            includes = re.findall(rep, t_body)
            for i_file in includes:
                filename = p_path + '/templates/' + i_file
                i_body = 'ERROR: File ' + filename + ' does not exists.'
                if os.path.exists(filename):
                    i_body = public.readFile(filename)
                t_body = re.sub(rep.replace('(.+)', i_file), i_body, t_body)

            return render_template_string(t_body, data=data)
        else:  # 直接响应插件返回值,可以是任意flask支持的响应类型
            r_type = type(data)
            if r_type == dict:
                if name == 'btwaf' and 'msg' in data:
                    return render_template('error3.html',
                                           data={"error_msg": data['msg']})
                return public.returnJson(
                    False,
                    public.getMsg('Bad return type [{}]').format(r_type)), json_header
                # public.getMsg('PUBLIC_ERR_RETURN')), json_header
            if name == 'btwaf':
                data = public.return_message(0, 0, data)
            return data
    except:
        return public.get_error_info()

@app.route(route_v2 + '/hook', methods=method_all)
def panel_hook_v2():
    # webhook接口
    get = get_input()
    if not os.path.exists('plugin/webhook'):
        return abort(404)
    public.package_path_append('plugin/webhook')
    import webhook_main
    return public.getJson(webhook_main.webhook_main().RunHook(get))


@app.route(route_v2 + '/install', methods=method_all)
def install_v2():
    # 初始化面板接口
    if public.is_spider(): return abort(404)
    if not os.path.exists('install.pl'): return redirect('/login')
    if public.M('config').where("id=?", ('1',)).getField('status') == 1:
        if os.path.exists('install.pl'): os.remove('install.pl')
        session.clear()
        return redirect('/login')
    ret_login = os.path.join('/', admin_path)
    if admin_path == '/' or admin_path == '/bt': ret_login = '/login'
    session['admin_path'] = False
    session['login'] = False
    if request.method == method_get[0]:
        if not os.path.exists('install.pl'): return redirect(ret_login)
        data = {}
        data['status'] = os.path.exists('install.pl')
        data['username'] = public.GetRandomString(8).lower()
        return render_template('install.html', data=data)

    elif request.method == method_post[0]:
        if not os.path.exists('install.pl'): return redirect(ret_login)
        get = get_input()
        if not hasattr(get, 'bt_username'):
            return public.get_msg_gettext('The user name cannot be empty!')
        if not get.bt_username:
            return public.get_msg_gettext('The user name cannot be empty!')
        if not hasattr(get, 'bt_password1'):
            return public.get_msg_gettext('Password can not be blank!')
        if not get.bt_password1:
            return public.get_msg_gettext('Password can not be blank!')
        if get.bt_password1 != get.bt_password2:
            return public.get_msg_gettext(
                'The passwords entered twice do not match, please re-enter!')
        public.M('users').where("id=?", (1,)).save(
            'username,password',
            (get.bt_username,
             public.password_salt(public.md5(get.bt_password1.strip()),
                                  uid=1)))
        os.remove('install.pl')
        public.M('config').where("id=?", ('1',)).setField('status', 1)
        data = {}
        data['status'] = os.path.exists('install.pl')
        data['username'] = get.bt_username
        return render_template('install.html', data=data)


# ---------------------    websocket  START  -------------------------- #


@sockets.route(route_v2 + '/workorder_client')
def workorder_client_v2(ws):
    comReturn = comm.local()
    if comReturn: return comReturn

    get = ws.receive()
    get = json.loads(get)
    if not check_csrf_websocket(ws, get):
        return

    import panelWorkorder
    toObject = panelWorkorder.panelWorkorder()
    get = get_input()
    toObject.client(ws, get)


@sockets.route(route_v2 + '/ws_panel')
def ws_panel_v2(ws):
    '''
        @name 面板接口ws入口
        @author hwliang<2021-07-24>
        @param ws<ws_parameter> websocket会话对像
        @return void
    '''
    comReturn = comm.local()
    if comReturn: return comReturn

    get = ws.receive()
    get = json.loads(get)
    if not check_csrf_websocket(ws, get): return

    while True:
        pdata = ws.receive()
        if pdata == '{}': break
        data = json.loads(pdata)
        get = public.to_dict_obj(data)
        get._ws = ws
        p = threading.Thread(target=ws_panel_thread_v2, args=(get,))
        p.start()


def ws_panel_thread_v2(get):
    '''
        @name 面板管理ws线程
        @author hwliang<2021-07-24>
        @param get<dict> 请求参数
        @return void
    '''

    if not hasattr(get, 'ws_callback'):
        get._ws.send(
            public.getJson(public.return_status_code(1001, 'ws_callback')))
        return
    if not hasattr(get, 'mod_name'):
        get._ws.send(
            public.getJson(public.return_status_code(1001, 'mod_name')))
        return
    if not hasattr(get, 'def_name'):
        get._ws.send(
            public.getJson(public.return_status_code(1001, 'def_name')))
        return
    get.mod_name = get.mod_name.strip()
    get.def_name = get.def_name.strip()
    check_str = '{}{}'.format(get.mod_name, get.def_name)
    if not re.match(r"^\w+$", check_str) or get.mod_name in [
        'public', 'common', 'db', 'db_mysql', 'downloadFile', 'jobs'
    ]:
        get._ws.send(
            public.getJson(
                public.return_status_code(
                    1000, 'Unsafe mod_name, def_name parameter content')))
        return

    mod_file = '{}/{}.py'.format(public.get_class_path(), get.mod_name)
    if not os.path.exists(mod_file):
        get._ws.send(
            public.getJson(
                public.return_status_code(
                    1000, 'Specified module {} does not exist'.format(
                        get.mod_name))))
        return
    _obj = public.get_script_object(mod_file)
    if not _obj:
        get._ws.send(
            public.getJson(
                public.return_status_code(
                    1000, 'Specified module {} does not exist'.format(
                        get.mod_name))))
        return
    _cls = getattr(_obj, get.mod_name)
    if not _cls:
        get._ws.send(
            public.getJson(
                public.return_status_code(
                    1000,
                    'The {} object was not found in the {} module'.format(
                        get.mod_name, get.mod_name))))
        return
    _def = getattr(_cls(), get.def_name)
    if not _def:
        get._ws.send(
            public.getJson(
                public.return_status_code(
                    1000,
                    'The {} object was not found in the {} module'.format(
                        get.mod_name, get.def_name))))
        return
    result = {'callback': get.ws_callback, 'result': _def(get)}
    get._ws.send(public.getJson(result))


@sockets.route(route_v2 + '/ws_project')
def ws_project_v2(ws):
    '''
        @name 项目管理ws入口
        @author hwliang<2021-07-24>
        @param ws<ws_parameter> websocket会话对像
        @return void
    '''
    comReturn = comm.local()
    if comReturn: return comReturn
    get = ws.receive()
    get = json.loads(get)
    if not check_csrf_websocket(ws, get): return

    from panelProjectControllerV2 import ProjectController
    project_obj = ProjectController()
    while True:
        pdata = ws.receive()
        if pdata in '{}': break
        get = public.to_dict_obj(json.loads(pdata))
        get._ws = ws
        p = threading.Thread(target=ws_project_thread_v2,
                             args=(project_obj, get))
        p.start()


def ws_project_thread_v2(_obj, get):
    '''
        @name 项目管理ws线程
        @author hwliang<2021-07-24>
        @param _obj<ProjectController> 项目管理控制器对像
        @param get<dict> 请求参数
        @return void
    '''
    if not hasattr(get, 'ws_callback'):
        get._ws.send(
            public.getJson(public.return_status_code(1001, 'ws_callback')))
        return
    result = {'callback': get.ws_callback, 'result': _obj.model(get)}
    get._ws.send(public.getJson(result))


sock_pids = {}


@sockets.route(route_v2 + '/sock_shell')
def sock_shell_v2(ws):
    '''
        @name 执行指定命令，实时输出命令执行结果
        @author hwliang<2021-07-19>
        @return void

        示例：
            p = new WebSocket('ws://192.168.1.247:8888/sock_shell')
            p.send('ping www.bt.cn -c 100')
    '''
    comReturn = comm.local()
    if comReturn:
        ws.send(str(comReturn))
        return
    kill_closed_v2()
    get = ws.receive()
    get = json.loads(get)
    if not check_csrf_websocket(ws, get): return

    t = None
    try:
        while True:
            cmdstring = ws.receive()
            if cmdstring in ['stop', 'error'] or not cmdstring:
                break
            t = threading.Thread(target=sock_recv, args=(cmdstring, ws))
            t.start()
        kill_closed_v2()
    except:
        kill_closed_v2()


def kill_closed_v2():
    '''
        @name 关闭已关闭的连接
        @author hwliang<2021-07-24>
        @return void
    '''
    global sock_pids
    import psutil
    pids = psutil.pids()
    keys = sock_pids.copy().keys()
    for pid in keys:
        if hasattr(sock_pids[pid], 'closed'):
            is_closed = sock_pids[pid].closed
        else:
            is_closed = not sock_pids[pid].connected

        logging.debug("PID: {} , sock_stat: {}".format(pid, is_closed))
        if not is_closed: continue

        if pid in pids:
            try:
                p = psutil.Process(pid)
                for cp in p.children():
                    cp.kill()
                p.kill()
                logging.debug("killed: {}".format(pid))
                sock_pids.pop(pid)
            except:
                pass
        else:
            sock_pids.pop(pid)


@app.route(route_v2 + '/close_sock_shell', methods=method_all)
def close_sock_shell_v2():
    '''
        @name 关闭指定命令
        @author hwliang<2021-07-19>
        @param cmdstring<string> 完整命令行
        @return dict
        示例：
            $.post('/close_sock_shell',{cmdstring:'ping www.bt.cn -c 100'})
    '''
    comReturn = comm.local()
    if comReturn: return comReturn
    args = get_input()
    if not check_csrf():
        return public.ReturnJson(False, 'INIT_CSRF_ERR'), json_header
    cmdstring = args.cmdstring.strip()
    skey = public.md5(cmdstring)
    pid = cache.get(skey)
    if not pid:
        return json.dumps(
            public.return_data(
                False, [], error_msg='The specified sock has been terminated!')
        ), json_header
    os.kill(pid, 9)
    cache.delete(skey)
    return json.dumps(public.return_data(True,
                                         'Successful operation!')), json_header


@sockets.route(route_v2 + '/webssh')
def webssh_v2(ws):
    # 宝塔终端连接
    comReturn = comm.local()
    if comReturn:
        ws.send(str(comReturn))
        return
    if not ws: return 'False'
    get = ws.receive()
    if not get: return
    get = json.loads(get)
    if not check_csrf_websocket(ws, get):
        return
    # public.print_log("传入信息-get:{}".format(get))
    import ssh_terminal_v2
    sp = ssh_terminal_v2.ssh_host_admin()
    if 'host' in get:
        ssh_info = {}
        ssh_info['host'] = get['host'].strip()
        if 'port' in get:
            ssh_info['port'] = int(get['port'])
        if 'username' in get:
            ssh_info['username'] = get['username'].strip()
        if 'password' in get:
            ssh_info['password'] = get['password'].strip()
        if 'pkey' in get:
            ssh_info['pkey'] = get['pkey'].strip()

        if get['host'] in ['127.0.0.1', 'localhost']:
            if not 'password' in ssh_info:
                ssh_info = sp.get_ssh_info('127.0.0.1')
            if not ssh_info: ssh_info = sp.get_ssh_info('localhost')
            if not ssh_info: ssh_info = {"host": "127.0.0.1"}
            if not 'port' in ssh_info:
                ssh_info['port'] = public.get_ssh_port()
            #当密码和key都为空的时候
            if not 'password' in ssh_info and not 'pkey' in ssh_info:
                import ssh_security_v2
                sshobject = ssh_security_v2.ssh_security()
                ssh_info['pkey'] = sshobject.get_key(get).get("message",{}).get("result","")
    else:
        # public.print_log("无host")
        ssh_info = sp.get_ssh_info('127.0.0.1')
        if not ssh_info: ssh_info = sp.get_ssh_info('localhost')
        if not ssh_info: ssh_info = {"host": "127.0.0.1"}
        ssh_info['port'] = public.get_ssh_port()

    if not ssh_info['host'] in ['127.0.0.1', 'localhost']:
        if not 'username' in ssh_info:
            ssh_info = sp.get_ssh_info(ssh_info['host'])
            if not ssh_info:
                ws.send(
                    'The specified host information is not found, please add it again!'
                )
                return
    p = ssh_terminal_v2.ssh_terminal()
    # public.print_log("传入信息----ws:{}---ssh_info:{}".format(ws, ssh_info))
    p.run(ws, ssh_info)
    del (p)
    if ws.connected:
        ws.close()
    return 'False'


# ---------------------    websocket END    -------------------------- #


@app.route(route_v2 + "/daily", methods=method_all)
def daily_v2():
    """面板日报数据"""

    comReturn = comm.local()
    if comReturn: return comReturn

    import panelDaily
    toObject = panelDaily.panelDaily()

    defs = ("get_app_usage", "get_daily_data", "get_daily_list")
    result = publicObject(toObject, defs)
    return result


@app.route(route_v2 + '/phpmyadmin/<path:path_full>', methods=method_all)
def pma_proxy_v2(path_full=None):
    '''
        @name phpMyAdmin代理
        @author hwliang<2022-01-19>
        @return Response
    '''
    comReturn = comm.local()
    if comReturn: return comReturn
    cache_key = 'pmd_port_path'
    pmd = cache.get(cache_key)
    if not pmd:
        pmd = get_phpmyadmin_dir()
        if not pmd:
            return 'phpMyAdmin is not installed, please go to the [App Store] page to install it!'
        pmd = list(pmd)
        cache.set(cache_key, pmd, 10)
    panel_pool = 'http://'
    if request.url_root[:5] == 'https':
        panel_pool = 'https://'
        import ajax
        ssl_info = ajax.ajax().get_phpmyadmin_ssl(None)
        if ssl_info['status']:
            pmd[1] = ssl_info['port']
        else:
            panel_pool = 'http://'

    proxy_url = '{}127.0.0.1:{}/{}/'.format(
        panel_pool, pmd[1], pmd[0]) + request.full_path.replace(
        '/phpmyadmin/', '')
    from panel_http_proxy_v2 import HttpProxy
    px = HttpProxy()
    return px.proxy(proxy_url)


@app.route(route_v2 + '/p/<int:port>', methods=method_all)
@app.route(route_v2 + '/p/<int:port>/', methods=method_all)
@app.route(route_v2 + '/p/<int:port>/<path:full_path>', methods=method_all)
def proxy_port_v2(port, full_path=None):
    '''
        @name 代理指定端口
        @author hwliang<2022-01-19>
        @return Response
    '''

    comReturn = comm.local()
    if comReturn: return comReturn
    full_path = request.full_path.replace('/p/{}/'.format(port),
                                          '').replace('/p/{}'.format(port), '')
    uri = '{}/{}'.format(port, full_path)
    uri = uri.replace('//', '/')
    proxy_url = 'http://127.0.0.1:{}'.format(uri)
    from panel_http_proxy_v2 import HttpProxy
    px = HttpProxy()
    return px.proxy(proxy_url)


@app.route(route_v2 + '/push', methods=method_all)
def push_v2(pdata=None):
    comReturn = comm.local()
    if comReturn: return comReturn
    import panel_push_v2
    toObject = panel_push_v2.panelPush()
    defs = ('set_push_status', 'get_push_msg_list', 'get_modules_list',
            'install_module', 'uninstall_module', 'get_module_template',
            'set_push_config', 'get_push_config', 'del_push_config',
            'get_module_logs', 'get_module_config', 'get_push_list',
            'get_push_logs')
    result = publicObject(toObject, defs, None, pdata)
    return result


# 2024/1/24 上午 11:42 新场景模型的路由
# def panel_mod_v2(name=None, sub_name=None, fun=None, stype=None):
@app.route(route_v2 + '/mod/push/msgconf/<fun>', methods=method_all)
@app.route(route_v2 + '/mod/push/task/<fun>', methods=method_all)
@app.route(route_v2 + '/mod/proxy/com/<fun>', methods=method_all)
@app.route(route_v2 + '/mod/proxy/com/<fun>/<path:stype>', methods=method_all)
@app.route(route_v2 + '/mod/docker/com/<fun>', methods=method_all)
@app.route(route_v2 + '/mod/docker/com/<fun>/<path:stype>', methods=method_all)
@app.route(route_v2 + '/mod/ssh/com/<fun>', methods=method_all)
@app.route(route_v2 + '/mod/ssh/com/<fun>/<path:stype>', methods=method_all)
@app.route(route_v2 + '/mod/backup_restore/com/<fun>', methods=method_all)
@app.route(route_v2 + '/mod/backup_restore/com/<fun>/<path:stype>', methods=method_all)
def panel_mod_v2(fun=None, stype=None):
    """
        @name 新场景模型的路由
        @param "data":{"参数名":""} <数据类型> 参数描述
        @return dict{"status":True/False,"msg":"提示信息"}
    """
    # if not public.is_bind():
    #     return redirect('/bind', 302)
    if public.is_error_path():
        return redirect('/error', 302)

    path_split = request.path.split("/")
    if len(path_split) < 5: return
    name = path_split[3]
    sub_name = path_split[4]

    if not name:
        return abort(404)
    if not sub_name:
        return abort(404)
    if not re.match(r"^[\w\-]+$", name):
        return abort(404)
    if not re.match(r"^[\w\-]+$", sub_name):
        return abort(404)
    if fun and not re.match(r"^[\w\-.]+$", fun):
        return abort(404)

    comReturn = comm.local()
    if comReturn: return comReturn
    if not stype:
        tmp = fun.split('.')
        fun = tmp[0]
        if len(tmp) == 1: tmp.append('')
        stype = tmp[1]
    if fun:
        if public.get_csrf_cookie_token_key() in session and 'login' in session:
            if not check_csrf():
                return public.ReturnJson(False, 'INIT_CSRF_ERR'), json_header

    args = get_mod_input()

    if not fun: fun = 'index.html'
    if not stype:
        tmp = fun.split('.')
        fun = tmp[0]
        if len(tmp) == 1: tmp.append('')
        stype = tmp[1]

    if not name: name = 'coll'
    if not public.path_safe_check("%s/%s/%s/%s" % (name, sub_name, fun, stype)):
        return abort(404)
    if name.find('./') != -1 or not re.match(r"^[\w-]+$", name):
        return abort(404)
    if sub_name.find('./') != -1 or not re.match(r"^[\w-]+$", sub_name):
        return abort(404)
    if not name:
        return public.returnJson(False, 'PLUGIN_INPUT_ERR'), json_header

    args.client_ip = public.GetClientIp()

    # 初始化新场景模型对象
    try:
        from mod.modController import Controller
        controller_obj = Controller()
        defs = ('model',)
        args.model_index = "mod"
        args.action = 'model'
        args.mod_name = name
        args.sub_mod_name = sub_name
        args.def_name = fun
        data = publicObject(controller_obj, defs, None, args)
        r_type = type(data)
        if r_type in [Response, Resp]:
            return data

        p_path = public.get_mod_path() + '/' + name
        # 处理响应
        if stype == 'json':  # 响应JSON
            return public.getJson(data), json_header
        elif stype == 'html':  # 使用模板
            t_path_root = p_path + '/templates/'
            t_path = t_path_root + fun + '.html'
            if not os.path.exists(t_path):
                return public.returnJson(False,
                                         'PLUGIN_NOT_TEMPLATE'), json_header
            t_body = public.readFile(t_path)
            # 处理模板包含
            rep = r'{%\s?include\s"(.+)"\s?%}'
            includes = re.findall(rep, t_body)
            for i_file in includes:
                filename = p_path + '/templates/' + i_file
                i_body = 'ERROR: File ' + filename + ' does not exists.'
                if os.path.exists(filename):
                    i_body = public.readFile(filename)
                t_body = re.sub(rep.replace('(.+)', i_file), i_body, t_body)
            return render_template_string(t_body, data=data)
        else:  # 直接响应插件返回值,可以是任意flask支持的响应类型
            r_type = type(data)
            if r_type == dict:
                if name == 'btwaf' and 'msg' in data:
                    return render_template('error3.html',
                                           data={"error_msg": data['msg']})
                return public.returnJson(
                    False,
                    public.getMsg('Bad return type [{}]').format(r_type)), json_header
            return data
    except:
        if not 'login' in session: return abort(404)
        return public.get_error_object(None, plugin_name=name)

@app.route(route_v2 + '/check_auth', methods=method_all)
def check_auth_v2(pdata=None):
    comReturn = comm.local()
    if comReturn: return comReturn
    if os.path.exists('data/.is_pro.pl'):
        return public.return_message(0,0,'true')
    return public.return_message(-1,0,'false')

@app.route('/bind', methods=method_get)
def bind():
    comReturn = comm.local()
    if comReturn: return comReturn
    if public.is_bind(): return redirect('/', 302)
    data = {}
    data['lan'] = public.GetLan('index_new')
    # g.title = '请先绑定宝塔帐号'
    return render_template('index_new.html', data=data)

@app.route(route_v2 + '/breaking_through', methods=method_all)
def breaking_through_v2(pdata=None):
    comReturn = comm.local()
    if comReturn: return comReturn
    import breaking_through
    breakingObject = breaking_through.main()
    get = get_input()
    defs = (
        'set_config',
        'get_config',
        'get_history_record',
        'set_history_record_limit',
        'clear_history_record_limit',
        'get_black_white',
        'add_black_white',
        'modify_black_white',
        'del_balck_white',
        'check_local_ip_white',
        'panel_ip_white',
        'get_protected_services',
        'get_linux_users',
        'get_compiler_info',
        'add_user_to_compiler',
        'del_user_to_compiler',
        'set_compiler_status',
    )
    return publicObject(breakingObject, defs, None, pdata)

@app.route(route_v2 + '/virtual/<def_name>', methods=method_all)
@app.route(route_v2 + '/aapanelsub/<def_name>', methods=method_all)
@app.route('/aapanelsub/<def_name>', methods=method_all)
def virtualModel_v2(def_name):
    if request.method in ['GET'] and request.path.startswith('/aapanelsub'):
        return index_new(request.path)
    path_split = request.path.split("/")
    if len(path_split) < 3: return
    comReturn = comm.local()
    if comReturn: return comReturn
    import public.PluginLoader as plugin_loader
    mod_file = '{}/class_v2/virtualModelV2/virtualModel.py'.format(public.get_panel_path())
    plugin_class = plugin_loader.get_module(mod_file)
    plugin_object = getattr(plugin_class,"main")()
    get= get_input()
    if def_name.endswith('.json'):
        def_name = def_name[:-5]
    result = getattr(plugin_object,def_name)(get)
    return result


@app.route(route_v2 + '/campaign/<def_name>', methods=method_all)
def campaign_v2(def_name: str):
    comReturn = comm.local()
    if comReturn: return comReturn
    from power_mta import actions
    return getattr(actions, def_name)(get_input())


@app.route(route_v2 + '/userRegister', methods=method_all)
def userRegister_v2():
    comReturn = comm.local()
    if comReturn: return comReturn
    import userRegister_v2
    reg = userRegister_v2.userRegister()
    defs = ('toRegister',)

    return publicObject(reg, defs, None, None)
# ===========================================================v2路由区end===========================================================#

@app.route('/v2/install_finish', methods=method_post)
def install_finish():
    with open('{}/data/install_finished.mark'.format(public.get_panel_path()), 'w') as fp:
        fp.write('True')
    return public.return_message(0, 0, 'Successfully')


@app.route('/v2/wp/login/<int:site_id>', methods=method_get)
@app.route('/v2/wp/login/<int:site_id>/<wp_site_type>', methods=method_get)
def wp_login(site_id: int, wp_site_type: str = 'local'):
    comReturn = comm.local()
    if comReturn: return comReturn

    if site_id < 1:
        return public.gettext_msg('Invalid site_id')

    # wp_site_type
    # 1 Local
    # 2 Remote
    if wp_site_type.lower() == 'local':
        from wp_toolkit import wpmgr
        return wpmgr(site_id).auto_login()
    elif wp_site_type.lower() == 'remote':
        from wp_toolkit import wpmgr_remote
        return wpmgr_remote(site_id).auto_login()
    else:
        return public.gettext_msg('Invalid site_type')


@app.route('/v2/pmta/<enc_str>', methods=method_get)
def mail_campaign_handler(enc_str: str):
    g.api_request = True
    try:
        from power_mta.maillog_stat import campaign_event_handler
        return campaign_event_handler(enc_str)
    except:
        public.print_error()
        return public.lang('Server has been crashed')


# 获取新场景模型的传参数据
def get_mod_input():
    '''
        @name # 获取新场景模型的传参数据
        @author wzz <2024/1/24 上午 11:42>
        @param "data":{"参数名":""} <数据类型> 参数描述
        @return dict{"status":True/False,"msg":"提示信息"}
    '''
    data = public.dict_obj()
    exludes = ['blob']
    for key in request.args.keys():
        data.set(key, str(request.args.get(key, '')))

    if request.is_json:
        for key in request.get_json().keys():
            data.set(key, str(request.get_json()[key]))
    else:
        try:
            for key in request.form.keys():
                if key in exludes: continue
                data.set(key, str(request.form.get(key, '')))
        except:
            try:
                post = request.form.to_dict()
                for key in post.keys():
                    if key in exludes: continue
                    data.set(key, str(post[key]))
            except:
                pass

    if 'form_data' in g:
        for k in g.form_data.keys():
            data.set(k, str(g.form_data[k]))

    if not hasattr(data, 'data'): data.data = []
    return data


# -----------------------------------------  无登录校验路由 start----------------------------------------

# 邮局调用退订接口
@app.route('/mailUnsubscribe', methods=method_all)
def mailUnsubscribe():
    # 插件判断
    if not os.path.exists('/www/server/panel/plugin/mail_sys/mail_send_bulk.py') or not os.path.exists('/www/vmail/postfixadmin.db'):
        return abort(404)

    g.is_aes = False
    import mailUnsubscribe
    reg = mailUnsubscribe.mailUnsubscribe()
    defs = ('Unsubscribe', 'get_mail_type_list')
    return publicObject(reg, defs, None, None)


# 新增登录设置语言
@app.route('/userLang', methods=method_all)
def userLang():
    if public.cache_get(
            public.Md5(
                uuid.UUID(int=uuid.getnode()).hex[-12:] +
                public.GetClientIp())) != 'check':

        return abort(404)

    global admin_check_auth, admin_path, route_path, admin_path_file
    if admin_path != '/bt' and os.path.exists(
            admin_path_file) and not 'admin_auth' in session:
        return abort(404)

    g.is_aes = False
    import userLang
    reg = userLang.userLang()
    defs = ('get_language', 'set_language')
    return publicObject(reg, defs, None, None)


# ===========================================================  Google OAuth2.0  start ===========================================================#

@app.route('/google/redirect', methods=method_get)
def google_redirect():
    comReturn = comm.local()
    if comReturn: return comReturn

    nonce = public.md5(str(time.time()) + public.GetClientIp())
    session['google_nonce'] = nonce

    redirect_url = public.httpPost('{}/google/redirect'.format(public.OfficialApiBase()), headers={
        'X-Forwarded-For': public.GetClientIp(),
    }, data={
        'redirect_url': 'https://{}{}{}'.format(public.GetHost(), ':{}'.format(str(public.ReadFile('data/port.pl')).strip()) if os.path.exists('data/port.pl') else '', '/google/callback'),
        'nonce': nonce,
        'from_panel': 1,
    })

    return redirect(redirect_url)


@app.route('/google/callback', methods=method_get)
def google_callback():
    comReturn = comm.local()
    if comReturn: return comReturn

    get = get_input()

    # validate nonce
    if 'google_nonce' not in session or not session['google_nonce'] or 'nonce' not in get or not get.nonce or session['google_nonce'] != get.nonce:
        return abort(403)

    # remove nonce
    session['google_nonce'] = None
    session.pop('google_nonce', None)

    bind = 'data/bind.pl'
    if os.path.exists(bind): os.remove(bind)
    userinfo = json.loads(public.base64url_decode(get.user_data))
    userinfo['token'] = get.token
    # 用户信息写入文件
    public.writeFile('data/userInfo.json', json.dumps(userinfo))
    session['focre_cloud'] = True
    return redirect('/')

# ==========================================================  Google OAuth2.0  end ===========================================================#


# -----------------------------------------  无登录校验路由 end----------------------------------------


# 初始化CDN的配置
def init_cdn_config(app):
    config_path = '/www/server/panel/config/cdn.conf'
    config_dir = os.path.dirname(config_path)
    # 确保配置目录存在
    if not os.path.exists(config_dir):
        app.config['CDN_PROXY'] = False
        return
    if not os.path.exists(config_path):
        app.config['CDN_PROXY'] = False
        with open(config_path, 'w') as f:
            f.write('CDN_PROXY=False')
        return
    with open(config_path, 'r') as f:
        content = f.read().strip()
        if content == 'CDN_PROXY=True':
            app.config['CDN_PROXY'] = True
        else:
            app.config['CDN_PROXY'] = False
    return

init_cdn_config(app)
