# coding: utf-8
# +-------------------------------------------------------------------
# | aapanel V2路由
# +-------------------------------------------------------------------
# | Copyright (c) 2015-2099 aapanel(http://www.aapanel.com) All rights reserved.
# +-------------------------------------------------------------------
# | Author: hwliang <hwl@bt.cn>
# +-------------------------------------------------------------------
from BTPanel.app import *

@app.route('/new', methods=method_get)
@app.route('/new/<path:sub_path>', methods=method_get)
def index_new(sub_path: str = ''):
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
    return render_template('index_new.html', data=data)

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
            'get_command_find', 'modify_command', 'remove_command')
    return publicObject(ssh_host_admin, defs, None)


@app.route(route_v2 + '/modify_password', methods=method_get)
def modify_password_v2():
    comReturn = comm.local()
    if comReturn: return comReturn
    # if not session.get('password_expire',False): return redirect('/',302)
    data = {}
    g.title = public.get_msg_gettext(
        'The password has expired, please change it!')
    return render_template('modify_password.html', data=data)


@app.route(route_v2 + '/site', methods=method_all)
def site_v2(pdata=None):
    # public.print_log("----/v2/site_v2----1")
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
            'id=?', (1, )).getField('mysql_root')
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
            'get_login_send', 'get_msg_push_list', 'clear_login_send')
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
                defs = ("get_list", )
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
def project_v2(def_name):
    if request.method not in ['GET', 'POST']: return
    path_split = request.path.split("/")
    if len(path_split) < 5: return
    comReturn = comm.local()
    if comReturn: return comReturn
    from panelProjectControllerV2 import ProjectController
    project_obj = ProjectController()
    defs = ('model', )
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
    defs = ('model', )
    get = get_input()
    get.action = 'model'
    get.mod_name = mod_name
    get.def_name = def_name
    return publicObject(project_obj, defs, None, get)


@app.route(route_v2 + '/docker', methods=method_all)
def docker_v2(pdata=None):
    comReturn = comm.local()
    if comReturn: return comReturn
    if request.method == method_get[0]:
        import system_v2
        data = system_v2.system().GetConcifInfo()
        data['js_random'] = get_js_random()
        data['lan'] = public.GetLan('files')
        return render_template('docker.html', data=data)


@app.route(route_v2 + '/dbmodel/<mod_name>/<def_name>', methods=method_all)
def dbmodel_v2(mod_name, def_name):
    comReturn = comm.local()
    if comReturn: return comReturn
    from panelDatabaseControllerV2 import DatabaseController
    database_obj = DatabaseController()
    defs = ('model', )
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


@app.route(route_v2 + '/crontab', methods=method_all)
def crontab_v2(pdata=None):
    # 计划任务
    comReturn = comm.local()
    if comReturn: return comReturn
    if request.method == method_get[0] and not pdata:
        import system_v2
        data = system_v2.system().GetConcifInfo()
        data['lan'] = public.GetLan('crontab')
        data['js_random'] = get_js_random()
        return render_template('crontab.html', data=data)
    import crontab_v2
    crontabObject = crontab_v2.crontab()
    defs = ('GetCrontab', 'AddCrontab', 'GetDataList', 'GetLogs', 'DelLogs',
            'DelCrontab', 'StartTask', 'set_cron_status', 'get_crond_find',
            'modify_crond', 'get_backup_list')
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
        "check_nps")
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
            'ReWeb', 'RestartServer', 'ReMemory', 'RepPanel')
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
    defs = ('setPs', 'getData', 'getFind', 'getKey')
    return publicObject(dataObject, defs, None, pdata)


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
            'get_product_auth', 'get_product_auth_all', 'get_stripe_session_id',
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


@app.route(route_v2 + '/download', methods=method_get)
def download_v2():
    # 文件下载接口
    comReturn = comm.local()
    if comReturn: return comReturn
    filename = request.args.get('filename')
    if filename.find('|') != -1:
        filename = filename.split('|')[0]  # 改为获取本地备份
    if not filename:
        return public.ReturnJson(False, "INIT_ARGS_ERR"), json_header
    # if filename in ['alioss','qiniu','upyun','txcos','ftp','msonedrive','gcloud_storage', 'gdrive', 'aws_s3']: return panel_cloud()
    if not os.path.exists(filename):
        return public.ReturnJson(False, "FILE_NOT_EXISTS"), json_header

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
                 str(request.environ.get('REMOTE_PORT')), ))
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
        # -----------

        # rsa_key = 'public_key'
        # session[last_key] = public.GetRandomString(32)
        # data[last_key] = session[last_key]
        # data[rsa_key] = public.get_rsa_public_key().replace("\n", "")
        # return render_template('login.html', data=data)


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
        find = public.M('download_token').where('token=?', (token, )).find()

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
    defs = ('model', )
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
def safeModel_v2(mod_name, def_name):
    if request.method not in ['GET', 'POST']: return
    path_split = request.path.split("/")
    if len(path_split) < 5: return
    comReturn = comm.local()
    if comReturn: return comReturn
    from panelSafeControllerV2 import SafeController
    project_obj = SafeController()
    defs = ('model', )
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
def allModule_v2(def_name):
    if request.method not in ['GET', 'POST']: return
    path_split = request.path.split("/")
    if len(path_split) < 4: return
    comReturn = comm.local()
    if comReturn: return comReturn
    p_path = public.get_plugin_path() + '/' + path_split[2]
    if os.path.exists(p_path):
        return panel_other(index, mod_name, def_name)

    from panelControllerV2 import Controller
    controller_obj = Controller()
    defs = ('model', )
    get = get_input()
    get.model_index = path_split[2]
    get.action = 'model'
    get.mod_name = path_split[3]
    get.def_name = def_name
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
        is_php = os.path.exists(p_path + '/index.php')
        if not is_php:
            import panel_plugin_v2
            plu_panel = panel_plugin_v2.panelPlugin()
            plugin_list = plu_panel.get_cloud_list()
            waf = 0
            if not 'pro' in plugin_list: plugin_list['pro'] = -1
            for p in plugin_list['list']:
                if p['name'] in ['btwaf']:
                    if p['endtime'] != 0 and p['endtime'] < time.time():
                        waf = -1
            try:
                public.package_path_append(p_path)
                plugin_main = __import__(name + '_main')
                if name == 'btwaf' and fun == 'index' and waf == -1 and plugin_list[
                        'pro'] == -1:
                    return render_template('error3.html', data={})
            except:
                if name == 'btwaf' and fun == 'index' and waf == -1 and plugin_list[
                        'pro'] == -1:
                    return render_template('error3.html', data={})
                if os.path.exists("{}/btwaf".format(public.get_plugin_path())):
                    return render_template('error3.html', data={})
            try:
                if sys.version_info[0] == 2:
                    reload(plugin_main)
                else:
                    from imp import reload
                    reload(plugin_main)
            except:
                pass
            # public.print_log("plugin_main22222:  {}".format(plugin_main))

            plu = eval('plugin_main.' + name + '_main()')

            # methods = dir(plu)
            # # 遍历列表并打印每个方法的名称
            # for method in methods:
            #     # 排除以双下划线开头和结尾的特殊属性和方法
            #     if not method.startswith("__") and not method.endswith("__"):
            #         public.print_log(method)

            if not hasattr(plu, fun):

                return public.returnJson(False,
                                         'Plugin does not exist'), json_header

        # 执行插件方法
        if not is_php:
            if is_accept:
                checks = plu._check(args)
                if type(checks) != bool or not checks:
                    return public.getJson(checks), json_header
            data = eval('plu.' + fun + '(args)')
        else:
            comReturn = comm.local()
            if comReturn: return comReturn
            import panel_php_v2
            args.s = fun
            args.name = name
            data = panel_php_v2.panelPHP(name).exec_php_script(args)

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
                    public.getMsg('Bad return type [{}]').format(
                        r_type)), json_header
            return data
    except:
        return public.get_error_info()
        return public.get_error_object(None, plugin_name=name)


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
    if public.M('config').where("id=?", ('1', )).getField('status') == 1:
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
        public.M('users').where("id=?", (1, )).save(
            'username,password',
            (get.bt_username,
             public.password_salt(public.md5(get.bt_password1.strip()),
                                  uid=1)))
        os.remove('install.pl')
        public.M('config').where("id=?", ('1', )).setField('status', 1)
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
        p = threading.Thread(target=ws_panel_thread_v2, args=(get, ))
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
    # if not hasattr(get, 'args'):
    #     get._ws.send(public.getJson(public.return_status_code(1001, 'args')))
    #     return

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

        if get['host'] in ['127.0.0.1', 'localhost'
                           ] and 'port' not in ssh_info:
            ssh_info = sp.get_ssh_info('127.0.0.1')
            if not ssh_info: ssh_info = sp.get_ssh_info('localhost')
            if not ssh_info: ssh_info = {"host": "127.0.0.1"}
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
    p = ssh_terminal_v2.ssh_terminal()
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


@app.route('/hello/<regex("john|tony"):username>')
def test_regex_route(username: str):
    return 'hi, '+username


@app.route('/v2/install_finish', methods=method_post)
def install_finish():
    with open('{}/data/install_finished.mark'.format(public.get_panel_path()), 'w') as fp:
        fp.write('True')
    return public.return_message(0, 0, 'Successfully')


@app.route('/v2/login_wp', methods=method_get)
def login_wp():
    admin_php = '/www/wwwroot/wp-study.aap/wp-admin/includes/admin.php'

    with open(admin_php, 'r') as fp:
        admin_php_content = fp.read()

    if admin_php_content.find('''/** Automatic login administrator account */
require_once ABSPATH . 'wp-admin/includes/auto-login.php';''') < 0:
        with open(admin_php, 'a') as fp:
            fp.write('''
/** Automatic login administrator account */
require_once ABSPATH . 'wp-admin/includes/auto-login.php';
''')

    mark_file_name = public.GetRandomString(16)
    mark_file = '/www/wwwroot/wp-study.aap/wp-admin/includes/{}.mark'.format(mark_file_name)

    with open(mark_file, 'w') as fp:
        fp.write('True')

    user_id = 1
    token_key = public.GetRandomString(16)
    token = public.GetRandomString(32)

    auto_login_wp = '''<?php

if (is_file(ABSPATH . 'wp-admin/includes/{mark_file_name}.mark') && !empty($_REQUEST['{token_key}']) && $_REQUEST['{token_key}'] === '{token_value}') {{
    add_action('set_auth_cookie', function($auth_cookie) {{
        $_COOKIE[SECURE_AUTH_COOKIE] = $auth_cookie;
        $_COOKIE[AUTH_COOKIE] = $auth_cookie;
        $_COOKIE[LOGGED_IN_COOKIE] = $auth_cookie;
    }});

    wp_set_current_user({user_id});
    wp_set_auth_cookie({user_id});
    
    unlink(ABSPATH . 'wp-admin/includes/{mark_file_name}.mark');
}}
'''.format(token_key=token_key, token_value=token, user_id=user_id, mark_file_name=mark_file_name)

    with open('/www/wwwroot/wp-study.aap/wp-admin/includes/auto-login.php', 'w') as fp:
        fp.write(auto_login_wp)

    return redirect('http://wp-study.aap/wp-admin/?{}={}'.format(token_key, token))
