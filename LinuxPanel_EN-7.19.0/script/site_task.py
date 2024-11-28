#coding: utf-8
import os,sys,time
os.chdir('/www/server/panel/')
sys.path.insert(0,"class/")
import public
oldEdate = public.readFile('data/edate.pl')
if not oldEdate: oldEdate = '0000-00-00'
mEdate = time.strftime('%Y-%m-%d',time.localtime())
edateSites = public.M('sites').where('edate>? AND edate<? AND (status=? OR status=?)',('0000-00-00',mEdate,1,u'正在运行')).field('id,name').select()
import panelSite
siteObject = panelSite.panelSite()
for site in edateSites:
    get = public.dict_obj()
    get.id = site['id']
    get.name = site['name']
    siteObject.SiteStop(get)
oldEdate = mEdate
public.writeFile('data/edate.pl',mEdate)