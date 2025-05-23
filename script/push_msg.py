# coding: utf-8
import json
import sys, os, time

os.chdir('/www/server/panel/')
sys.path.insert(0, "class/")
sys.path.insert(0, "/www/server/panel/")
import public
import http_requests

http_requests.DEFAULT_TYPE = 'src'
os.environ['BT_TASK'] = '1'

try:
    import panelPush
    import threading

    push = panelPush.panelPush()
    push.start()

    # msg bind check
    flag = False
    sender = os.path.join(public.get_panel_path(), "data/mod_push_data/sender.json")
    if os.path.exists(sender):
        sender_info = public.readFile(sender)
        try:
            sender_info = json.loads(sender_info)
        except:
            pass
        if sender_info and isinstance(sender_info, list):
            for send in sender_info:
                if send.get("data") != {}:
                    flag = True  # has bind alarm
                    break
    if flag is True:
        from mod.base.push_mod import PushSystem
        PushSystem().run()

except Exception as e:
    pass
    os.system("echo no,{},{} > /tmp/push.pl".format(time.time(), e))
