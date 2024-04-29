#coding: utf-8
import sys,os,time
os.chdir('/www/server/panel/')
sys.path.insert(0,"class/")
import public
import http_requests
http_requests.DEFAULT_TYPE = 'src'
os.environ['BT_TASK'] = '1'

try:
    import panelPush
    import threading
    push = panelPush.panelPush()
    push.start()
    # os.system("echo yes,{} > /tmp/push.pl".format(time.time()))
except Exception as e:
    pass
    # print("开启推送消息进程异常。")
    os.system("echo no,{},{} > /tmp/push.pl".format(time.time(),e))