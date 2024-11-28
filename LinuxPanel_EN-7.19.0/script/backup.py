#!/usr/bin/python
#coding: utf-8
#-----------------------------
# aaPanel
# 网站备份工具
#-----------------------------

import sys,os
os.chdir('/www/server/panel')
sys.path.append("./")
sys.path.append("class/")
sys.path.append("class_v2/")
if sys.version_info[0] == 2:
    reload(sys)
    sys.setdefaultencoding('utf-8')
import public,db,time
from public.hook_import import hook_import
hook_import()
import class_v2.panel_backup_v2 as panelBackup
# import panelBackup as panelBackup

class backupTools(panelBackup.backup):
    def backupSite(self, name, count, echo_id=None):
        self.backup_site(name, save=count, echo_id=echo_id)

    def backupDatabase(self, name, count, echo_id=None):
        self.backup_database(name, save=count, echo_id=echo_id)

    #备份指定目录
    def backupPath(self, path, count, echo_id=None):
        self.backup_path(path, save=count, echo_id=echo_id)

    def backupSiteAll(self, save, echo_id=None):
        self.backup_site_all(save, echo_id=echo_id)

    def backupDatabaseAll(self, save, echo_id=None):
        self.backup_database_all(save, echo_id=echo_id)


if __name__ == "__main__":
    backup = backupTools()
    type = sys.argv[1]
    echo_id = None
    if len(sys.argv) > 4: echo_id = sys.argv[4]
    if type == 'site':
        if sys.argv[2] == 'ALL':
            backup.backupSiteAll(sys.argv[3], echo_id)
        elif ',' in sys.argv[2]:
            for i in sys.argv[2].split(','):
                backup.backupSite(i, sys.argv[3], echo_id)
        else:
            backup = backupTools(cron_info = {'echo':sys.argv[4]})
            backup.backupSite(sys.argv[2], sys.argv[3], echo_id)
    elif type == 'path':
        backup = backupTools(cron_info = {'echo':sys.argv[4]})
        backup.backupPath(sys.argv[2], sys.argv[3], echo_id)
    elif type == 'database':
        if sys.argv[2] == 'ALL':
            backup.backupDatabaseAll(sys.argv[3], echo_id)
        elif ',' in sys.argv[2]:
            for i in sys.argv[2].split(','):
                backup.backupDatabase(i, sys.argv[3], echo_id)
        else:
            backup = backupTools(cron_info = {'echo':sys.argv[4]})
            backup.backupDatabase(sys.argv[2], sys.argv[3], echo_id)
