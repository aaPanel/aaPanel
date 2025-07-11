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
from mod.base.push_mod import system

class main:


    def run(self):
        msg_list = []
        from panel_site_v2 import panelSite
        site_obj = panelSite()
        res = site_obj.get_Scan(None)
        if int(res['loophole_num']):
            msg_list.append('Scan the website {} and find {} vulnerabilities'.format(res['site_num'], res['loophole_num']))
        else:
            msg_list.append('Scan the website [{}], status is [Security]'.format(res['site_num']))
        return {"msg_list": msg_list}


if __name__ == '__main__':
    main = main()
    msg = main.run()
    system.push_by_task_keyword("vulnerability_scanning", "vulnerability_scanning", push_data=msg)