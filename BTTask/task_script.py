# coding: utf-8
# -------------------------------------------------------------------
# aaPanel
# -------------------------------------------------------------------
# Copyright (c) 2014-2099 aaPanel(www.aapanel.com) All rights reserved.
# -------------------------------------------------------------------
# Author: aapanel
# -------------------------------------------------------------------
# ------------------------------
# task script app
# ------------------------------

import functools
import os

import sys

os.chdir("/www/server/panel")
sys.path.insert(0, os.path.abspath("/www/server/panel"))
sys.path.insert(0, "/www/server/panel/class/")
sys.path.insert(0, "/www/server/panel/class_v2/")
try:
    from public.hook_import import hook_import

    hook_import()
except Exception:
    pass


def task():
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            pid_dir = "/tmp/brain_task_pids/"
            os.makedirs(pid_dir, exist_ok=True)
            pid = os.path.join(pid_dir, f"{func.__name__}.pid")
            with open(pid, "w") as pf:
                pf.write(str(os.getpid()))
            try:
                return func(*args, **kwargs)
            except Exception:
                import traceback
                traceback.print_exc(file=sys.stderr)
                sys.exit(1)
            finally:
                if os.path.exists(pid):
                    os.remove(pid)

        return wrapper

    return decorator


# ======================================================
# 使用task装饰器
# 所有导入请在函数中进行, 异常由顶层处理记录task.log
# ======================================================
# 守护服务
@task()
def daemon_service():
    from script.restart_services import RestartServices
    RestartServices().main()


@task()
def make_suer_ssl_task():
    from ssl_domainModelV2.service import make_suer_ssl_task
    make_suer_ssl_task()


# site 图标
@task()
def find_favicons():
    from data_v2 import data as data_v2_cls
    data_v2_cls().find_stored_favicons()


# 放爆破检查任务
@task()
def breaking_through():
    import class_v2.breaking_through as breaking_through
    _breaking_through_obj = breaking_through.main()
    _breaking_through_obj.del_cron()
    _breaking_through_obj.cron_method()
    del _breaking_through_obj


# 更新WAF配置
@task()
def update_waf_config():
    import class_v2.data_v2 as data_v2
    dataObject = data_v2.data()
    dataObject.getSiteWafConfig()
    del dataObject


@task()
def update_monitor_requests():
    import class_v2.data_v2 as data_v2
    dataObject = data_v2.data()
    dataObject.getSiteThirtyTotal()
    del dataObject


@task()
def malicious_file_scanning():
    from projectModelV2 import safecloudModel
    safecloud = safecloudModel.main()
    # 调用 webshell_detection 函数
    safecloud.webshell_detection({'is_task': 'true'})
    del safecloud


@task()
def check_site_monitor():
    import time
    import public
    site_total_uninstall = '{}/data/site_total_uninstall.pl'.format(public.get_panel_path())
    site_total_install_path = '{}/site_total'.format(public.get_setup_path())
    site_total_service = '/etc/systemd/system/site_total.service'
    install_name = ''
    execstr = ""
    if not os.path.exists(site_total_uninstall):
        if not os.path.exists(site_total_install_path): public.ExecShell("rm -f {}".format(site_total_service))
        if public.GetWebServer() != "openlitespeed" and not os.path.exists(
                site_total_service) and not os.path.exists(
            os.path.join(public.get_panel_path(), "plugin/monitor/info.json")) and public.M('tasks').where(
            'name=? and status=?', ('Install [site_total_monitor]', '0')).count() < 1:
            execstr = "curl https://node.aapanel.com/site_total/install.sh|bash"
            install_name = 'Install [site_total_monitor]'
            # sleep_time = 86400
    else:
        if os.path.exists(site_total_service):
            install_name = 'Uninstall [site_total_monitor]'
            execstr = "bash /www/server/site_total/scripts/uninstall.sh"
    if install_name and execstr:
        public.M('tasks').add('id,name,type,status,addtime,execstr',
                              (None, install_name, 'execshell', '0', time.strftime('%Y-%m-%d %H:%M:%S'), execstr))
        public.writeFile('/tmp/panelTask.pl', 'True')


# 多web
@task()
def multi_web_server_daemon():
    import public
    import psutil
    if public.get_multi_webservice_status():
        from panel_site_v2 import panelSite
        from script.restart_services import DaemonManager

        obj = panelSite()
        pid_paths = {
            'nginx': "/www/server/nginx/logs/nginx.pid",
            'apache': "/www/server/apache/logs/httpd.pid",
            'openlitespeed': "/tmp/lshttpd/lshttpd.pid"
        }

        for service_name, pid_path in pid_paths.items():
            sys.path.append("../..")
            daemon_info = DaemonManager.safe_read()
            if service_name not in daemon_info:
                continue

            is_running = False
            if os.path.exists(pid_path):
                pid = public.readFile(pid_path)

                if pid:
                    try:
                        psutil.Process(int(pid))
                        is_running = True
                    except:
                        pass

            if not is_running:
                public.WriteLog("Service Daemon",
                                f"Multi-WebServer: An error occurred in {service_name}. Initiate the repair")
                obj.cheak_port_conflict('enable')
                obj.ols_update_config('enable')
                obj.apache_update_config('enable')
                public.webservice_operation('nginx')
                public.WriteLog("Service Daemon", f"Multi-WebServer: The {service_name} repair was successful")
                break


# 日志事件loop
@task()
def maillog_event():
    from power_mta.maillog_stat import maillog_event
    maillog_event()


# 聚合日志
@task()
def aggregate_maillogs_task():
    from power_mta.maillog_stat import aggregate_maillogs_task_once
    aggregate_maillogs_task_once()


@task()
def schedule_automations():
    from power_mta.automations import Task
    Task().schedule_once()


# 自动回复mail
@task()
def auto_reply_tasks():
    try:
        if not os.path.exists('/www/server/panel/plugin/mail_sys/mail_sys_main.py') or not os.path.exists(
                '/www/vmail'):
            return
        if os.path.exists("/www/server/panel/plugin/mail_sys"):
            sys.path.insert(1, "/www/server/panel/plugin/mail_sys")
        try:
            from plugin.mail_sys.mail_sys_main import mail_sys_main
            mail_sys_main().auto_reply_tasks()
        except Exception:
            raise
    except:
        pass


@task()
def auto_scan_abnormal_mail():
    import time
    import public
    try:
        if not os.path.exists('/www/server/panel/plugin/mail_sys/mail_send_bulk.py') or not os.path.exists(
                '/www/vmail'):
            return
        # 检查授权
        endtime = public.get_pd()[1]
        curtime = int(time.time())
        if endtime != 0 and endtime < curtime:
            return

        # 检查是否关闭了自动扫描
        path = '/www/server/panel/plugin/mail_sys/data/abnormal_mail_check_switch'
        if os.path.exists(path):
            return

        if os.path.exists("/www/server/panel/plugin/mail_sys"):
            sys.path.insert(1, "/www/server/panel/plugin/mail_sys")
        # 导入并执行扫描
        import public.PluginLoader as plugin_loader
        bulk = plugin_loader.get_module('{}/plugin/mail_sys/mail_send_bulk.py'.format(public.get_panel_path()))
        SendMailBulk = bulk.SendMailBulk
        try:
            SendMailBulk().check_abnormal_emails()
        except Exception:
            raise
    except:
        pass


@task()
def submit_email_statistics():
    import public
    from datetime import datetime, timedelta

    def _get_yesterday_count2():
        # 获取昨天的开始时间和结束时间（本地时间）
        today = datetime.now()
        yesterday = today - timedelta(days=1)

        # 昨天 00:00:00
        yesterday_start = datetime(yesterday.year, yesterday.month, yesterday.day, 0, 0, 0)

        # 昨天 23:59:59
        yesterday_end = datetime(yesterday.year, yesterday.month, yesterday.day, 23, 59, 59)

        # 转为时间戳
        start_time = int(yesterday_start.timestamp())
        end_time = int(yesterday_end.timestamp())

        try:
            query = public.S('send_mails').alias('rm').prefix('')
            query.inner_join('senders s', 'rm.postfix_message_id=s.postfix_message_id')
            query.where('s.postfix_message_id is not null')
            if start_time > 0:
                query.where('rm.log_time > ?', start_time - 1)
            if end_time > 0:
                query.where('rm.log_time < ?', end_time + 1)

            query.where('rm.status  =?', 'sent')
            from power_mta.maillog_stat import query_maillog_with_time_section
            ret = query_maillog_with_time_section(query, start_time, end_time)
            allnum = len(ret)
        except:
            allnum = 0
        return allnum

    if os.path.exists("/www/server/panel/plugin/mail_sys"):
        sys.path.insert(1, "/www/server/panel/plugin/mail_sys")

    # 添加提交标记   每次提交昨天的  标记存在跳过  不存在添加 删除前天标记
    yesterday = datetime.now() - timedelta(days=1)
    yesterday = yesterday.strftime('%Y-%m-%d')
    cloud_yesterday_submit = f'/www/server/panel/data/{yesterday}_submit_email_statistics.pl'
    if os.path.exists(cloud_yesterday_submit):
        return
    # 判断是否有邮局
    if not os.path.exists('/www/server/panel/plugin/mail_sys/mail_send_bulk.py') or not os.path.exists('/www/vmail'):
        return
    # 处理昨天数据
    all_data = _get_yesterday_count2()
    if not all_data:
        return

    # 记录昨日发件总数
    public.set_module_logs('sys_mail', 'sent', all_data)

    # 添加标记
    public.writeFile(cloud_yesterday_submit, '1')
    # 删除前天标记
    before_yesterday = datetime.now() - timedelta(days=2)
    before_yesterday = before_yesterday.strftime('%Y-%m-%d')
    cloud_before_yesterday_submit = f'/www/server/panel/data/{before_yesterday}_submit_email_statistics.pl'
    if os.path.exists(cloud_before_yesterday_submit):
        os.remove(cloud_before_yesterday_submit)


@task()
def submit_module_call_statistics():
    import json
    import requests
    import public
    from datetime import datetime, timedelta
    from BTTask.conf import logger

    # 获取系统时间与utc时间的差值
    def _get_utc_offset_modele():
        # 系统时间戳
        current_local_time = datetime.now()
        current_local_timestamp = int(current_local_time.timestamp())

        # 获取当前 UTC 时间的时间戳
        # noinspection PyDeprecation
        current_utc_time = datetime.utcnow()
        current_utc_timestamp = int(current_utc_time.timestamp())

        # 计算时区差值（秒）
        timezone_offset = current_local_timestamp - current_utc_timestamp
        offset = timezone_offset / 3600

        return offset

    def _submit_to_cloud(data_submit):
        """提交用户统计数据  接口调用  安装量等 """
        import panelAuth
        cloudUrl = '{}/api/panel/submit_feature_invoked_bulk'.format(public.OfficialApiBase())
        pdata = panelAuth.panelAuth().create_serverid(None)
        url_headers = {}
        if 'token' in pdata:
            url_headers = {"authorization": "bt {}".format(pdata['token'])}

        pdata['environment_info'] = json.dumps(public.fetch_env_info())

        pdata['data'] = data_submit
        pdata['utc_offset'] = _get_utc_offset_modele()
        requests.post(cloudUrl, json=pdata, headers=url_headers)
        return

    # 添加提交标记   每次提交昨天的  标记存在跳过  不存在添加 删除前天标记  提交过的数据在统计文件里删除
    yesterday = datetime.now() - timedelta(days=1)
    yesterday = yesterday.strftime('%Y-%m-%d')
    cloud_yesterday_submit = '{}/data/{}_submit_module_call_statistics.pl'.format(public.get_panel_path(), yesterday)
    if os.path.exists(cloud_yesterday_submit):
        return

    # 取文件中yesterday和yesterday以前的数据
    datainfo = {}
    path = '{}/data/mod_log.json'.format(public.get_panel_path())
    if os.path.exists(path):
        try:
            datainfo = json.loads(public.readFile(path))
        except:
            pass
    else:
        return

    if type(datainfo) != dict:
        datainfo = {}
    # 需要提交的
    data_submit = {}
    # 当天数据
    data_reserve = {}

    try:
        for date, modules in datainfo.items():
            # 如果日期小于昨天，则提交数据
            if date.strip() <= yesterday.strip():
                data_submit[date] = modules
            else:
                data_reserve[date] = modules
    except:
        logger.error(public.get_error_info())

    if not data_submit:
        return
    _submit_to_cloud(data_submit)

    # 将data_reserve 重新写入
    public.writeFile(path, json.dumps(data_reserve))

    # 添加标记
    public.writeFile(cloud_yesterday_submit, '1')
    # 删除前天标记
    before_yesterday = datetime.now() - timedelta(days=2)
    before_yesterday = before_yesterday.strftime('%Y-%m-%d')
    cloud_before_yesterday_submit = '{}/data/{}_submit_module_call_statistics.pl'.format(
        public.get_panel_path(), before_yesterday
    )
    if os.path.exists(cloud_before_yesterday_submit):
        os.remove(cloud_before_yesterday_submit)
    return


# 邮箱域名黑名单检查报警
@task()
def mailsys_domain_blecklisted_alarm():
    import public
    from datetime import datetime, timedelta
    from BTTask.conf import logger

    if not os.path.exists('/www/server/panel/plugin/mail_sys/mail_send_bulk.py') or not os.path.exists('/www/vmail'):
        return

    yesterday = datetime.now() - timedelta(days=1)
    yesterday = yesterday.strftime('%Y-%m-%d')
    cloud_yesterday_submit = '{}/data/{}_mailsys_domain_blecklisted_alarm.pl'.format(
        public.get_panel_path(), yesterday
    )
    if os.path.exists(cloud_yesterday_submit):
        return

    if os.path.exists("/www/server/panel/plugin/mail_sys"):
        sys.path.insert(1, "/www/server/panel/plugin/mail_sys")

    # 检查版本 检查是否能查询额度  剩余额度
    import public.PluginLoader as plugin_loader
    bulk = plugin_loader.get_module('{}/plugin/mail_sys/mail_send_bulk.py'.format(public.get_panel_path()))
    SendMailBulk = bulk.SendMailBulk
    try:
        SendMailBulk().check_domain_blacklist_corn()

    except:
        logger.error(public.get_error_info())
        return

    # 添加标记
    public.writeFile(cloud_yesterday_submit, '1')
    # 删除前天标记
    before_yesterday = datetime.now() - timedelta(days=2)
    before_yesterday = before_yesterday.strftime('%Y-%m-%d')
    cloud_before_yesterday_submit = '{}/data/{}_mailsys_domain_blecklisted_alarm.pl'.format(
        public.get_panel_path(), before_yesterday
    )
    if os.path.exists(cloud_before_yesterday_submit):
        os.remove(cloud_before_yesterday_submit)
    return


# 更新wordpress漏洞库
@task()
def update_vulnerabilities():
    import time
    import public
    import requests, json
    if "/www/server/panel/class_v2/wp_toolkit/" not in sys.path:
        sys.path.insert(1, "/www/server/panel/class_v2/wp_toolkit/")
    # noinspection PyUnresolvedReferences
    import totle_db
    # noinspection PyUnresolvedReferences
    requests.packages.urllib3.disable_warnings()

    def auto_scan():
        """
            @name 自动扫描
            @msg 一天一次
        :return:
        """
        path_time = "/www/server/panel/data/auto_scan.pl"
        if not os.path.exists(path_time):
            public.writeFile(path_time, json.dumps({"time": int(time.time())}))
            share_ip_info = {"time": 0}
        else:
            share_ip_info = json.loads(public.readFile(path_time))
        if (int(time.time()) - share_ip_info["time"]) < 86400:
            return public.returnMsg(False, "未达到时间")
        share_ip_info["time"] = int(time.time())
        public.writeFile(path_time, json.dumps(share_ip_info))
        # noinspection PyUnresolvedReferences
        import wordpress_scan
        # noinspection PyInconsistentReturns
        wordpress_scan.wordpress_scan().auto_scan()

    def M(table, db="wordpress_vulnerabilities"):
        """
            @name 获取数据库对象
            @param table 表名
            @param db 数据库名
        """
        with totle_db.Sql(db) as sql:
            return sql.table(table)

    # noinspection PyInconsistentReturns
    def check_vlun():
        path_time = "/www/server/panel/data/wordpress_check_vlun.pl"
        if not os.path.exists(path_time):
            public.writeFile(path_time, json.dumps({"time": int(time.time())}))
            share_ip_info = {"time": 0}
        else:
            share_ip_info = json.loads(public.readFile(path_time))
        if (int(time.time()) - share_ip_info["time"]) < 86400:
            return public.returnMsg(False, "未达到时间")
        share_ip_info["time"] = int(time.time())
        public.writeFile(path_time, json.dumps(share_ip_info))
        load_time = M("wordpress_vulnerabilities", "wordpress_vulnerabilities").order("data_time desc").limit(
            "1").field(
            "data_time").find()
        if type(load_time) != dict: return

        # noinspection PyInconsistentReturns
        def get_yun_infos(page):
            url = "https://wafapi2.aapanel.com/api/bt_waf/get_wordpress_scan?size=100&p=" + str(page)
            yun_infos = requests.get(url, verify=False, timeout=60).json()
            for i in yun_infos['res']:
                if i['data_time'] > load_time['data_time']:
                    del i['id']
                    M("wordpress_vulnerabilities", "wordpress_vulnerabilities").insert(i)
                else:
                    return True

        for i in range(1, 20):
            time.sleep(26)
            if get_yun_infos(i):
                return

    def check_plugin_close():
        """
        @name 检查插件是否关闭
        @return True 关闭
        @return False 开启
        """
        path_time = "/www/server/panel/data/wordpress_check_plugin_close.pl"
        if not os.path.exists(path_time):
            public.writeFile(path_time, json.dumps({"time": int(time.time())}))
            share_ip_info = {"time": 0}
        else:
            share_ip_info = json.loads(public.readFile(path_time))
        if (int(time.time()) - share_ip_info["time"]) < 86400:
            return public.returnMsg(False, "未达到时间")
        share_ip_info["time"] = int(time.time())
        public.writeFile(path_time, json.dumps(share_ip_info))
        check_sql = M("plugin_error", "plugin_error").order("id desc").limit("1").field("id").find()
        if type(check_sql) != dict: return None
        time.sleep(30)
        url = "https://wafapi2.aapanel.com/api/bt_waf/plugin_error_list"
        try:
            res = requests.get(url, verify=False, timeout=60).json()
        except:
            return False
        res_list = res['res']
        for i in res_list:
            if M("plugin_error", "plugin_error").where("slug=? and status=0", i['slug']).count() > 0:
                M("plugin_error", "plugin_error").where("slug=?", i['slug']).update({"status": 1})
        return None

    # noinspection PyInconsistentReturns
    def get_plugin_update_time():
        """
            @name 获取插件更新时间
            @ps   一周更新一次
        """
        path_time = "/www/server/panel/data/wordpress_get_plugin_update_time.pl"
        if not os.path.exists(path_time):
            public.writeFile(path_time, json.dumps({"time": int(time.time())}))
            # 如果第一次运行则三天后再运行
            share_ip_info = {"time": int(time.time()) - 86400 * 2}
        else:
            share_ip_info = json.loads(public.readFile(path_time))
        if (int(time.time()) - share_ip_info["time"]) < 259200:
            return public.returnMsg(False, "未达到时间")
        share_ip_info["time"] = int(time.time())
        public.writeFile(path_time, json.dumps(share_ip_info))

        check_sql = M("wordpress_not_update", "wordpress_not_update").order("id desc").limit("1").field("id").find()
        if type(check_sql) != dict: return
        import random
        def get_plugin_time(id):
            time.sleep(30)
            url = "https://wafapi2.aapanel.com/api/bt_waf/get_wordpress_not_update?p=" + str(id)
            try:
                res = requests.get(url, verify=False, timeout=60).json()
                if len(res['res']) == 0:
                    return True
                for i in res['res']:
                    if M("wordpress_not_update", "wordpress_not_update").where("slug=?", i['slug']).count() > 0:
                        if M("wordpress_not_update", "wordpress_not_update").where("slug=? and last_time=?", (
                                i['slug'], i['last_time'])).count() == 0:
                            M("wordpress_not_update", "wordpress_not_update").where("slug=?", i['slug']).update(
                                {"last_time": i['last_time']})
                # 随机时间
            except:
                pass

        for i in range(1, 50):
            time.sleep(random.randint(10, 30))
            if get_plugin_time(i):
                return

    try:
        auto_scan()
        check_vlun()
        check_plugin_close()
        get_plugin_update_time()
    except Exception:
        raise


# 更新docker app
@task()
def refresh_dockerapps():
    from mod.project.docker.app.appManageMod import AppManage
    AppManage().refresh_apps_list()


# 更新软件商店列表
@task()
def update_software_list():
    import public
    import panelPlugin
    # noinspection PyUnresolvedReferences
    get = public.dict_obj()
    get.force = 1
    panelPlugin.panelPlugin().get_cloud_list(get)


# 每10分钟, 502错误检查线程 (夹杂其他任务)
@task()
def check502task():
    import json
    import time
    import psutil
    import public
    from BTTask.conf import logger, PYTHON_BIN, BASE_PATH

    def siteEdate():
        mEdate = time.strftime('%Y-%m-%d', time.localtime())
        edate_pl = '/www/server/panel/data/edate.pl'
        try:
            oldEdate = public.ReadFile(edate_pl)
            if not oldEdate:
                oldEdate = '0000-00-00'
            mEdate = time.strftime('%Y-%m-%d', time.localtime())
            if oldEdate == mEdate:
                return False
            os.system("nohup " + PYTHON_BIN + " /www/server/panel/script/site_task.py > /dev/null 2>&1 &")
        except Exception:
            logger.info(public.get_error_info())
        finally:
            del oldEdate
            public.writeFile(edate_pl, mEdate)

    def sess_expire():
        # session过期处理
        try:
            sess_path = '{}/data/session'.format(BASE_PATH)
            if not os.path.exists(sess_path):
                return
            s_time = time.time()
            f_list = os.listdir(sess_path)
            f_num = len(f_list)
            sess_expired_path = f"{public.get_panel_path()}/data/session_timeout.pl"
            sess_expired = 86400 # default 24H
            if os.path.exists(sess_expired_path):
                try:
                    sess_expired = int(public.readFile(sess_expired_path).strip())
                except:
                    pass
            for fname in f_list:
                filename = os.path.join(sess_path, fname)
                fstat = os.stat(filename)
                f_time = s_time - fstat.st_mtime
                if f_time > sess_expired:
                    os.remove(filename)
                    continue
                if fstat.st_size < 256 and len(fname) == 32:
                    if f_time > 60 or f_num > 30:
                        os.remove(filename)
                        continue
            del f_list
        except Exception as ex:
            logger.info(str(ex))

    # MySQL配额检查
    def mysql_quota_check():
        os.system("nohup " + PYTHON_BIN + " /www/server/panel/script/mysql_quota.py > /dev/null 2>&1 &")

    # 检查502错误
    def check502():
        # 处理指定PHP版本
        def startPHPVersion(version):
            try:
                fpm = '/etc/init.d/php-fpm-' + version
                php_path = '/www/server/php/' + version + '/sbin/php-fpm'
                if not os.path.exists(php_path):
                    if os.path.exists(fpm): os.remove(fpm)
                    return False

                # 尝试重载服务
                os.system(fpm + ' start')
                os.system(fpm + ' reload')
                if checkPHPVersion(version): return True

                # 尝试重启服务
                cgi = '/tmp/php-cgi-' + version + '.sock'
                pid = '/www/server/php/' + version + '/var/run/php-fpm.pid'
                os.system('pkill -9 php-fpm-' + version)
                time.sleep(0.5)
                if os.path.exists(cgi):
                    os.remove(cgi)
                if os.path.exists(pid):
                    os.remove(pid)
                os.system(fpm + ' start')
                if checkPHPVersion(version):
                    return True
                # 检查是否正确启动
                if os.path.exists(cgi):
                    return True
                return False
            except Exception as ex:
                logger.info(ex)
                return True

        # 检查指定PHP版本
        def checkPHPVersion(version):
            try:
                cgi_file = '/tmp/php-cgi-{}.sock'.format(version)
                if os.path.exists(cgi_file):
                    init_file = '/etc/init.d/php-fpm-{}'.format(version)
                    if os.path.exists(init_file):
                        init_body = public.ReadFile(init_file)
                        if not init_body: return True
                    uri = "/phpfpm_" + version + "_status?json"
                    result = public.request_php(version, uri, '')
                    json.loads(result)
                return True
            except:
                logger.info("PHP-{} unreachable detected".format(version))
                return False

        try:
            phpversions = public.get_php_versions()
            for version in phpversions:
                if version in ['52', '5.2']: continue
                php_path = '/www/server/php/' + version + '/sbin/php-fpm'
                if not os.path.exists(php_path):
                    continue
                if checkPHPVersion(version):
                    continue
                if startPHPVersion(version):
                    public.WriteLog('PHP daemon',
                                    'PHP-' + version + 'processing exception was detected and has been automatically fixed!',
                                    not_web=True)
        except Exception as ex:
            logger.info(ex)

    def auto_backup_panel():
        public.auto_backup_panel()

    # 更新 GeoLite2-Country.json
    def flush_geoip():
        """
            @name 检测如果大小小于3M或大于1个月则更新
            @author wzz <2024/5/21 下午5:33>
            @param "data":{"参数名":""} <数据类型> 参数描述
            @return dict{"status":True/False,"msg":"提示信息"}
        """
        _ips_path = "/www/server/panel/data/firewall/GeoLite2-Country.json"
        m_time_file = "/www/server/panel/data/firewall/geoip_mtime.pl"
        if not os.path.exists(_ips_path):
            os.system("mkdir -p /www/server/panel/data/firewall")
            os.system("touch {}".format(_ips_path))

        try:
            if not os.path.exists(_ips_path):
                public.downloadFile('{}/install/lib/{}'.format(public.get_url(), os.path.basename(_ips_path)),
                                    _ips_path)
                public.writeFile(m_time_file, str(int(time.time())))
                return

            _ips_size = os.path.getsize(_ips_path)
            if os.path.exists(m_time_file):
                _ips_mtime = int(public.readFile(m_time_file))
            else:
                _ips_mtime = 0

            if _ips_size < 3145728 or time.time() - _ips_mtime > 2592000:
                core = psutil.cpu_count()
                delay = round(1 / (core if core > 0 else 1), 2)
                os.system("rm -f {}".format(_ips_path))
                os.system("rm -f {}".format(m_time_file))
                public.downloadFile('{}/install/lib/{}'.format(public.get_url(), os.path.basename(_ips_path)),
                                    _ips_path)
                public.writeFile(m_time_file, str(int(time.time())))
                if os.path.exists(_ips_path):
                    try:
                        import json
                        from xml.etree.ElementTree import ElementTree, Element
                        from safeModelV2.firewallModel import main as firewall

                        firewallobj = firewall()
                        ips_list = json.loads(public.readFile(_ips_path))
                        if ips_list:
                            bash = os.path.exists('/usr/bin/apt-get') and not os.path.exists("/etc/redhat-release")
                            if bash:
                                btsh_path = "/etc/ufw/btsh"
                                if not os.path.exists(btsh_path):
                                    os.makedirs(btsh_path)

                                write_map = {}
                                for ip_dict in ips_list:
                                    tmp_path = '{}/{}.sh'.format(btsh_path, ip_dict['brief'])
                                    commands = [
                                        f'ipset add {ip_dict["brief"]} {ip}'
                                        for ip in ip_dict.get("ips", [])
                                        if firewallobj.verify_ip(ip)
                                    ]
                                    if commands:
                                        script_content = "#!/bin/bash\n" + "\n".join(commands) + "\n"
                                        write_map[tmp_path] = script_content
                                    time.sleep(delay)

                                for path, content in write_map.items():
                                    public.writeFile(path, content)
                                    time.sleep(0.05)
                            else:
                                for ip_dict in ips_list:
                                    xml_path = "/etc/firewalld/ipsets/{}.xml.old".format(ip_dict['brief'])
                                    xml_body = """<?xml version="1.0" encoding="utf-8"?>
    <ipset type="hash:net">
    <option name="maxelem" value="1000000"/>
    </ipset>
    """
                                    if os.path.exists(xml_path):
                                        public.writeFile(xml_path, xml_body)
                                    else:
                                        os.makedirs(os.path.dirname(xml_path), exist_ok=True)
                                        public.writeFile(xml_path, xml_body)

                                    tree = ElementTree()
                                    tree.parse(xml_path)
                                    root = tree.getroot()
                                    for ip in ip_dict['ips']:
                                        if firewallobj.verify_ip(ip):
                                            entry = Element("entry")
                                            entry.text = ip
                                            root.append(entry)

                                    firewallobj.format(root)
                                    tree.write(xml_path, 'utf-8', xml_declaration=True)
                                    time.sleep(delay)
                    except:
                        pass
        except:
            try:
                public.downloadFile(
                    '{}/install/lib/{}'.format(public.get_url(), os.path.basename(_ips_path)), _ips_path
                )
                public.writeFile(m_time_file, str(int(time.time())))
            except:
                pass

    auto_backup_panel()
    check502()
    mysql_quota_check()
    siteEdate()
    sess_expire()
    flush_geoip()


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python task_script.py <method_name>")
        sys.exit(1)

    method_name = sys.argv[1]
    if method_name in globals() and callable(globals()[method_name]):
        globals()[method_name]()
    else:
        print(f"Unknown or non-callable method: {method_name}")
