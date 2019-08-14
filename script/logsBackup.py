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

def split_logs(oldFileName,num):
    global logsPath
    if not os.path.exists(oldFileName):
        print('|---'+oldFileName+'file does not exist!')
        return

    logs=sorted(glob.glob(oldFileName+"_*"))
    count=len(logs)
    num=count - num

    for i in range(count):
        if i>num: break;
        os.remove(logs[i])
        print('|---The extra log ['+logs[i]+'] has been deleted!')

    newFileName=oldFileName+'_'+time.strftime("%Y-%m-%d_%H%M%S")+'.log'
    shutil.move(oldFileName,newFileName)
    os.system("gzip %s" % newFileName)
    print('|---The log has been cut to:'+newFileName+'.gz')

def split_all(save):
    sites = public.M('sites').field('name').select()
    for site in sites:
        oldFileName = logsPath + site['name'] + px
        split_logs(oldFileName,save)

if __name__ == '__main__':
    num = int(sys.argv[2])
    if sys.argv[1].find('ALL') == 0:
        split_all(num)
    else:
        siteName = sys.argv[1]
        if siteName[-4:] == '.log': 
            siteName = siteName[:-4]
        else:
            siteName = siteName.replace("-access_log",'')
        oldFileName = logsPath+sys.argv[1]
        split_logs(oldFileName,num)

    if is_nginx:
        os.system("kill -USR1 `cat /www/server/nginx/logs/nginx.pid`");
    else:
        os.system('/etc/init.d/httpd reload');