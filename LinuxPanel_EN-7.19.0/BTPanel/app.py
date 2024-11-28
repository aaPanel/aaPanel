# coding: utf-8
# +-------------------------------------------------------------------
# | aapanel
# +-------------------------------------------------------------------
# | Copyright (c) 2015-2099 aapanel(http://www.aapanel.com) All rights reserved.
# +-------------------------------------------------------------------
# | Author: hwliang <hwl@bt.cn>
# +-------------------------------------------------------------------

import logging
import sys
import json
import os
import threading
import time
import re
import uuid
import psutil

panel_path = '/www/server/panel'
if not os.name in ['nt']:
    os.chdir(panel_path)
if not 'class/' in sys.path:
    sys.path.insert(0, 'class/')
if not 'class_v2/' in sys.path:
    sys.path.insert(0, 'class_v2/')
from flask import Flask, session, render_template, send_file, request, redirect, g, make_response, \
    render_template_string, abort, stream_with_context, Response as Resp
from cachelib import SimpleCache, SimpleCacheSession
from werkzeug.wrappers import Response
from werkzeug.routing import BaseConverter
from flask_session import Session
from flask_compress import Compress

cache = SimpleCache(5000)
import public

# class RestrictedImportHook:
#     def __init__(self, allowed_modules):
#         self.allowed_modules = allowed_modules
#
#     def find_spec(self, fullname, path, target=None):
#         # 判断当前导入是否是功能模块，如果是则禁止导入
#         if fullname in self.allowed_modules:
#             return None
#         return self
#
#     def loader(self, fullname):
#         # 不禁止public模块的导入
#         if fullname == 'public':
#             pass
#
#         # 其他功能模块 不能互相导入
#         # elif fullname in ['aaa', 'bbb', 'ccc']:
#         #     return APIModuleLoader(self.allowed_module)
# 设置导入钩子
# sys.meta_path.insert(0, RestrictedImportHook(['panelPlugin', 'pay', 'ols', 'wxapp']))
# sys.meta_path.insert(0, RestrictedImportHook(['wxapp']))
# class APIModuleLoader:
#     def __init__(self, allowed_module):
#         self.allowed_module = allowed_module
#
#     def exec_module(self, module):
#         if self.allowed_module != 'public':
#             raise ImportError(f"API module '{self.allowed_module}' cannot import other API modules")
#
#         if module.__name__ != 'public':
#             module.__dict__['public'] = sys.modules['public']

# # 设置导入钩子
# sys.meta_path.insert(0, RestrictedImportHook('public'))

# 初始化Flask应用
app = Flask(__name__,
            template_folder="templates/{}".format(
                public.GetConfigValue('template')))
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
if app.config['SSL']:
    app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
    app.config['SESSION_COOKIE_SECURE'] = True
else:
    app.config['SESSION_COOKIE_SAMESITE'] = None

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
    '/docker',
    '/btdocker',
]
if admin_path in admin_path_checks: admin_path = '/bt'
if admin_path[-1] == '/': admin_path = admin_path[:-1]
uri_match = re.compile(
    r"(^/static/[\w_\./\-]+\.(js|css|png|jpg|gif|ico|svg|woff|woff2|ttf|otf|eot|map)$|^/[\w_\./\-]*$)"
)
session_id_match = re.compile(r"^[\w\.\-]+$")

route_path = os.path.join(admin_path, '')
if not route_path: route_path = '/'
if route_path[-1] == '/': route_path = route_path[:-1]
if route_path[0] != '/': route_path = '/' + route_path

route_v2 = '/v2'  #v2版本路由前缀

# ======================公共方法区域START============================#

def error_500(e: Exception):
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
        if is_csrf and public.get_csrf_sess_html_token_value() and session.get(
                'login', None):
            if not check_csrf():
                return public.ReturnJson(False, 'INIT_CSRF_ERR'), json_header

        if not get: get = get_input()
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
    except:
        return error_500(None)


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
    tmp = -1
    # try:
    #     import panelPlugin
    #     get = public.dict_obj()
    #     # get.init = 1
    #     tmp1 = panelPlugin.panelPlugin().get_cloud_list(get)
    # except:
    tmp1 = None
    if tmp1:
        tmp = tmp1[public.to_string([112, 114, 111])]
        ltd = tmp1.get('ltd', -1)
    else:
        ltd = -1
        tmp4 = cache.get(public.to_string([112, 95, 116, 111, 107, 101, 110]))
        if tmp4:
            tmp_f = public.to_string([47, 116, 109, 112, 47]) + tmp4
            if not os.path.exists(tmp_f): public.writeFile(tmp_f, '-1')
            tmp = public.readFile(tmp_f)
            if tmp: tmp = int(tmp)

    if ltd < 1:
        if ltd == -2:
            tmp3 = public.to_string([
                60, 115, 112, 97, 110, 32, 99, 108, 97, 115, 115, 61, 34, 98,
                116, 108, 116, 100, 45, 103, 114, 97, 121, 34, 62, 60, 115,
                112, 97, 110, 32, 115, 116, 121, 108, 101, 61, 34, 99, 111,
                108, 111, 114, 58, 32, 35, 102, 99, 54, 100, 50, 54, 59, 102,
                111, 110, 116, 45, 119, 101, 105, 103, 104, 116, 58, 32, 98,
                111, 108, 100, 59, 109, 97, 114, 103, 105, 110, 45, 114, 105,
                103, 104, 116, 58, 53, 112, 120, 34, 62, 24050, 36807, 26399,
                60, 47, 115, 112, 97, 110, 62, 60, 97, 32, 99, 108, 97, 115,
                115, 61, 34, 98, 116, 108, 105, 110, 107, 34, 32, 111, 110, 99,
                108, 105, 99, 107, 61, 34, 98, 116, 46, 115, 111, 102, 116, 46,
                117, 112, 100, 97, 116, 97, 95, 108, 116, 100, 40, 41, 34, 62,
                82, 69, 78, 69, 87, 60, 47, 97, 62, 60, 47, 115, 112, 97, 110,
                62
            ])
        elif tmp == -1:
            tmp3 = public.to_string([
                60, 115, 112, 97, 110, 32, 99, 108, 97, 115, 115, 61, 34, 98,
                116, 112, 114, 111, 45, 102, 114, 101, 101, 34, 32, 111, 110,
                99, 108, 105, 99, 107, 61, 34, 98, 116, 46, 115, 111, 102, 116,
                46, 114, 101, 110, 101, 119, 95, 112, 114, 111, 40, 41, 34, 32,
                116, 105, 116, 108, 101, 61, 34, 67, 108, 105, 99, 107, 32,
                116, 111, 32, 103, 101, 116, 32, 80, 82, 79, 34, 62, 20813,
                36153, 29256, 60, 47, 115, 112, 97, 110, 62
            ])
        elif tmp == -2:
            tmp3 = public.to_string([
                60, 115, 112, 97, 110, 32, 99, 108, 97, 115, 115, 61, 34, 98,
                116, 112, 114, 111, 45, 103, 114, 97, 121, 34, 62, 60, 115,
                112, 97, 110, 32, 115, 116, 121, 108, 101, 61, 34, 99, 111,
                108, 111, 114, 58, 32, 35, 102, 99, 54, 100, 50, 54, 59, 102,
                111, 110, 116, 45, 119, 101, 105, 103, 104, 116, 58, 32, 98,
                111, 108, 100, 59, 109, 97, 114, 103, 105, 110, 45, 114, 105,
                103, 104, 116, 58, 53, 112, 120, 34, 62, 24050, 36807, 26399,
                60, 47, 115, 112, 97, 110, 62, 60, 97, 32, 99, 108, 97, 115,
                115, 61, 34, 98, 116, 108, 105, 110, 107, 34, 32, 111, 110, 99,
                108, 105, 99, 107, 61, 34, 98, 116, 46, 115, 111, 102, 116, 46,
                114, 101, 110, 101, 119, 95, 112, 114, 111, 40, 41, 34, 62, 82,
                69, 78, 69, 87, 60, 47, 97, 62, 60, 47, 115, 112, 97, 110, 62
            ])
        if tmp >= 0 and ltd in [-1, -2]:
            if tmp == 0:
                tmp2 = public.to_string([27704, 20037, 25480, 26435])
                tmp3 = public.to_string([
                    60, 115, 112, 97, 110, 32, 99, 108, 97, 115, 115, 61, 34,
                    98, 116, 112, 114, 111, 34, 62, 123, 48, 125, 60, 115, 112,
                    97, 110, 32, 115, 116, 121, 108, 101, 61, 34, 99, 111, 108,
                    111, 114, 58, 32, 35, 102, 99, 54, 100, 50, 54, 59, 102,
                    111, 110, 116, 45, 119, 101, 105, 103, 104, 116, 58, 32,
                    98, 111, 108, 100, 59, 34, 62, 123, 49, 125, 60, 47, 115,
                    112, 97, 110, 62, 60, 47, 115, 112, 97, 110, 62
                ]).format(
                    public.to_string([21040, 26399, 26102, 38388, 65306]),
                    tmp2)
            else:
                tmp2 = time.strftime(
                    public.to_string([37, 89, 45, 37, 109, 45, 37, 100]),
                    time.localtime(tmp))
                tmp3 = public.to_string([
                    60, 115, 112, 97, 110, 32, 99, 108, 97, 115, 115, 61, 34,
                    98, 116, 112, 114, 111, 34, 62, 69, 120, 112, 105, 114,
                    101, 58, 32, 60, 115, 112, 97, 110, 32, 115, 116, 121, 108,
                    101, 61, 34, 99, 111, 108, 111, 114, 58, 32, 35, 102, 99,
                    54, 100, 50, 54, 59, 102, 111, 110, 116, 45, 119, 101, 105,
                    103, 104, 116, 58, 32, 98, 111, 108, 100, 59, 109, 97, 114,
                    103, 105, 110, 45, 114, 105, 103, 104, 116, 58, 53, 112,
                    120, 34, 62, 123, 48, 125, 60, 47, 115, 112, 97, 110, 62,
                    60, 97, 32, 99, 108, 97, 115, 115, 61, 34, 98, 116, 108,
                    105, 110, 107, 34, 32, 111, 110, 99, 108, 105, 99, 107, 61,
                    34, 98, 116, 46, 115, 111, 102, 116, 46, 114, 101, 110,
                    101, 119, 95, 112, 114, 111, 40, 41, 34, 62, 82, 69, 78,
                    69, 87, 60, 47, 97, 62, 60, 47, 115, 112, 97, 110, 62
                ]).format(tmp2)
        else:
            tmp3 = public.to_string([
                60, 115, 112, 97, 110, 32, 99, 108, 97, 115, 115, 61, 34, 98,
                116, 112, 114, 111, 45, 103, 114, 97, 121, 34, 32, 111, 110,
                99, 108, 105, 99, 107, 61, 34, 98, 116, 46, 115, 111, 102, 116,
                46, 114, 101, 110, 101, 119, 95, 112, 114, 111, 40, 41, 34, 32,
                116, 105, 116, 108, 101, 61, 34, 67, 108, 105, 99, 107, 32,
                116, 111, 32, 103, 101, 116, 32, 80, 82, 79, 34, 62, 70, 82,
                69, 69, 60, 47, 115, 112, 97, 110, 62
            ])
    else:
        tmp3 = public.to_string([
            60, 115, 112, 97, 110, 32, 99, 108, 97, 115, 115, 61, 34, 98, 116,
            108, 116, 100, 34, 62, 69, 120, 112, 105, 114, 101, 58, 32, 60,
            115, 112, 97, 110, 32, 115, 116, 121, 108, 101, 61, 34, 99, 111,
            108, 111, 114, 58, 32, 35, 102, 99, 54, 100, 50, 54, 59, 102, 111,
            110, 116, 45, 119, 101, 105, 103, 104, 116, 58, 32, 98, 111, 108,
            100, 59, 109, 97, 114, 103, 105, 110, 45, 114, 105, 103, 104, 116,
            58, 53, 112, 120, 34, 62, 123, 125, 60, 47, 115, 112, 97, 110, 62,
            60, 97, 32, 99, 108, 97, 115, 115, 61, 34, 98, 116, 108, 105, 110,
            107, 34, 32, 111, 110, 99, 108, 105, 99, 107, 61, 34, 98, 116, 46,
            115, 111, 102, 116, 46, 114, 101, 110, 101, 119, 95, 112, 114, 111,
            40, 41, 34, 62, 82, 69, 78, 69, 87, 60, 47, 97, 62, 60, 47, 115,
            112, 97, 110, 62
        ]).format(
            time.strftime(public.to_string([37, 89, 45, 37, 109, 45, 37, 100]),
                          time.localtime(ltd)))

    return tmp3, tmp, ltd


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
            # result = make_response(result)
            # request_token = public.GetRandomString(48)
            # request_token_key = public.get_csrf_cookie_token_key()
            # session[request_token_key] = request_token
            # samesite = app.config['SESSION_COOKIE_SAMESITE']
            # secure = app.config['SESSION_COOKIE_SECURE']
            # if app.config['SSL'] and request.full_path.find('/login?tmp_token=') == 0:
            #     samesite = 'None'
            #     secure = True
            # result.set_cookie(request_token_key, request_token,
            # max_age=86400 * 30,
            # samesite= samesite,
            # secure=secure
            # )
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
    for key in request.args.keys():
        data.set(key, str(request.args.get(key, '')))
    try:
        for key in request.form.keys():
            if key in exludes:
                continue
            data.set(key, str(request.form.get(key, '')))

    except Exception as ex:
        # public.print_log("error1 {}".format(ex))

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


# ======================自定义路由URL匹配规则转换器Begin===================== #

class RegexConverter(BaseConverter):
    """
    自定义URL匹配正则表达式
    """

    def __init__(self, map, regex):
        super(RegexConverter, self).__init__(map)
        self.regex = regex

    def to_python(self, value):
        """
        路由匹配时，匹配成功后传递给视图函数中参数的值
        :param value:
        :return:
        """
        return value

    def to_url(self, value):
        """
        使用url_for反向生成URL时，传递的参数经过该方法处理，返回的值用于生成URL中的参数
        :param value:
        :return:
        """
        val = super(RegexConverter, self).to_url(value)
        return val


# 添加到flask中
app.url_map.converters.update({
    'regex': RegexConverter
})

# ======================自定义路由URL匹配规则转换器End===================== #
