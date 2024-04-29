#coding: utf-8
import os,sys,time
os.chdir('/www/server/panel/')
sys.path.insert(0,"class/")
import public
import log_analysis
la = log_analysis.log_analysis()
site_infos = public.M('sites').field('name').select()
if not site_infos:
    exit()
get = public.to_dict_obj({})
for i in site_infos:
    if public.get_webserver() == 'nginx':
        log_file = '{}.log'
    elif public.get_webserver() == 'apache':
        log_file = '{}-access_log'
    else:
        log_file = '{}_ols.access_log'
    log_file = log_file.format(i['name'])
    get.path = "/www/wwwlogs/{}".format(log_file)
    get.action = "log_analysis"
    print('==================================================================')
    print('|-Analyzing [{}] website logs...'.format(i['name']))
    la.log_analysis(get)
    print('|-Analysis of website logs completed')
    print('==================================================================')