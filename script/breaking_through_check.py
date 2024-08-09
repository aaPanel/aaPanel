# coding: utf-8
# -------------------------------------------------------------------
# aaPanel
# -------------------------------------------------------------------
# Copyright (c) 2015-2017 aaPanel(www.aapanel.com) All rights reserved.
# -------------------------------------------------------------------
# Author: hezhihong <hezhihong@aapanel.com>
# -------------------------------------------------------------------

# ------------------------------
# 防爆破检测脚本
#------------------------------

import os,sys
panel_path = '/www/server/panel'
if not os.name in ['nt']:
    os.chdir(panel_path)
if not 'class/' in sys.path:
    sys.path.insert(0, 'class/')
if not 'class_v2/' in sys.path:
    sys.path.insert(0, 'class_v2/')
sys.path.insert(0, '.')
    
import public

# import breaking_through
# breakingObject = breaking_through.main()


# 调用处理方法
# result = run_object(pdata)
import public.PluginLoader as plugin_loader
mod_file = '{}/class_v2/breaking_through.py'.format(public.get_panel_path())
plugin_class = plugin_loader.get_module(mod_file)
class_string='main'
plugin_object = getattr(plugin_class,class_string)()
def_name='cron_method'
getattr(plugin_object,def_name)()
# public.print_log(result)
