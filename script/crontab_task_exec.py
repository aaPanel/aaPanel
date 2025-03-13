#coding: utf-8
#-------------------------------------------------------------------
# aapanel
#-------------------------------------------------------------------
# Copyright (c) 2015-2099 宝塔软件(http://aapanel.com) All rights reserved.
#-------------------------------------------------------------------
# Author: hwliang <hwl@aapanel.com>
#-------------------------------------------------------------------

#------------------------------
# 任务编排调用脚本
#------------------------------
import sys,os
os.chdir('/www/server/panel')
sys.path.insert(0,'class/')
sys.path.insert(0,'class_v2/')
# import PluginLoader
import public
args = public.dict_obj()

if len(sys.argv) < 2:
    print('ERROR: Task ID not found.')
    sys.exit()
args.trigger_id = int(sys.argv[1])
args.model_index = 'crontab_v2'
# res = PluginLoader.module_run('trigger','test_trigger',args)

# if not res['status']:
#     print(res['msg'])
#     sys.exit()


import public.PluginLoader as plugin_loader
mod_file = '{}/class_v2/crontabModelV2/triggerModel.py'.format(public.get_panel_path())
plugin_class = plugin_loader.get_module(mod_file)
class_string='main'
plugin_object = getattr(plugin_class,class_string)()
def_name='test_trigger'
res=getattr(plugin_object,def_name)(args)
if res['status'] != 0 and 'message' in res:
    print(res['message'])
    sys.exit()
