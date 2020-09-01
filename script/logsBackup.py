#!/usr/bin/python
#coding: utf-8
#-----------------------------
#宝塔Linux面板网站日志切割脚本
#-----------------------------
import sys
import os
import shutil
import time
import glob
os.chdir("/www/server/panel")
sys.path.append('class/')
import public
print ('==================================================================')
print( '★['+time.strftime("%Y/%m/%d %H:%M:%S")+']，Cutting log')
print ('==================================================================')
print ('|--Currently retaining the latest ['+sys.argv[2]+'] copies')
logsPath = '/www/wwwlogs/'
is_nginx = False
if os.path.exists('/www/server/nginx/logs/nginx.pid'): is_nginx = True
px = '.log'
if not is_nginx: px = '-access_log'

def build_errlog(sitename):
    if is_nginx:
        log = sitename + '.error.log'
    elif os.path.exists('/usr/local/lsws/bin/lswsctl'):
        log = sitename + '-error_log'
    else:
        log = sitename + '_ols.error_log'
    return log

def clean_backlog(logname,num):
    logs=sorted(glob.glob(logname+"_*"))
    count=len(logs)
    num=count - num

    for i in range(count):
        if i>num: break;
        os.remove(logs[i])
        print('|---The extra log ['+logs[i]+'] has been deleted!')

def split_logs(oldFileName,num,site_name):
    global logsPath
    errlog_name = build_errlog(site_name)
    old_errlog = logsPath + errlog_name
    if not os.path.exists(oldFileName):
        print('|---'+oldFileName+'file does not exist!')
        return

    clean_backlog(oldFileName,num)
    clean_backlog(old_errlog,num)

    newFileName=oldFileName+'_'+time.strftime("%Y-%m-%d_%H%M%S")+'.log'
    shutil.move(oldFileName,newFileName)
    new_errlog = build_errlog(site_name)+'_'+time.strftime("%Y-%m-%d_%H%M%S")+'.log'
    shutil.move(old_errlog, newFileName)
    if not os.path.exists('/www/server/panel/data/log_not_gzip.pl'):
        os.system("gzip %s" % newFileName)
        os.system("gzip %s" % new_errlog)
        print('|---The log has been cut to:' + newFileName + '.gz')
    else:
        print('|---The log has been cut to:'+newFileName+'.log')

def split_all(save):
    sites = public.M('sites').field('name').select()
    for site in sites:
        oldFileName = logsPath + site['name'] + px
        split_logs(oldFileName,save,site['name'])

if __name__ == '__main__':
    num = int(sys.argv[2])
    if sys.argv[1].find('ALL') == 0:
        split_all(num)
    else:
        siteName = sys.argv[1]
        if siteName[-4:] == '.log':
            siteName = siteName[:-4]
        elif siteName[-11:] == '-access_log':
            siteName = siteName.replace("-access_log",'')
        else:
            siteName = siteName.replace("_ols.access_log", '')
        oldFileName = logsPath+sys.argv[1]
        split_logs(oldFileName,num,siteName)

    if is_nginx:
        os.system("kill -USR1 `cat /www/server/nginx/logs/nginx.pid`")
    elif os.path.exists('/usr/local/lsws/bin/lswsctl'):
        os.system('/usr/local/lsws/bin/lswsctl restart')
    else:
        os.system('/etc/init.d/httpd reload')