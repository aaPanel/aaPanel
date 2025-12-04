# coding: utf-8
# -------------------------------------------------------------------
# aapanel
# -------------------------------------------------------------------
# Copyright (c) 2015-2099 aapanel(http://www.aapanel.com) All rights reserved.
# -------------------------------------------------------------------
# Author: miku <miku@bt.cn>
# -------------------------------------------------------------------
import os
import sys
import warnings

if "/www/server/panel/class" not in sys.path:
    sys.path.insert(0, "/www/server/panel/class")
if "/www/server/panel/class_v2" not in sys.path:
    sys.path.insert(0, "/www/server/panel/class_v2")
if "/www/server/panel" not in sys.path:
    sys.path.insert(0, "/www/server/panel")

import public

from BTPanel import app
from mod.project.backup_restore.base_util import BaseUtil
from mod.project.backup_restore.config_manager import ConfigManager
from firewallModelV2.comModel import main as firewall_com
from safeModelV2.firewallModel import main as safe_firewall_main

warnings.filterwarnings("ignore", category=SyntaxWarning)


class FirewallModule(BaseUtil, ConfigManager):
    def __init__(self):
        super().__init__()
        self.base_path = '/www/backup/backup_restore'
        self.bakcup_task_json = self.base_path + '/backup_task.json'

    def backup_firewall_data(self, timestamp):
        with app.app_context():
            try:
                self.print_log("====================================================", "backup")
                self.print_log(public.lang("Starting backup of firewall data"), "backup")
                backup_path = self.base_path + "/{timestamp}_backup/firewall".format(timestamp=timestamp)
                if not os.path.exists(backup_path):
                    public.ExecShell('mkdir -p {}'.format(backup_path))
                data_list = self.get_backup_data_list(timestamp)

                port_data_path = firewall_com().export_rules(
                    public.to_dict_obj({"rule": 'port', 'chain': 'ALL'})
                )['message'].get('result', '')
                ip_data_path = firewall_com().export_rules(
                    public.to_dict_obj({"rule": 'ip', 'chain': 'ALL'})
                )['message'].get('result', '')
                forward_data_path = firewall_com().export_rules(
                    public.to_dict_obj({"rule": 'forward'})
                )['message'].get('result', '')
                country_data_path = safe_firewall_main().export_rules(
                    public.to_dict_obj({'rule_name': 'country_rule'})
                )['message'].get('result', '')

                firewall_info = {
                    "status": 2,
                    "err_msg": None
                }

                for data_path in [
                    port_data_path, ip_data_path, forward_data_path, country_data_path
                ]:
                    if "json" in data_path:
                        public.ExecShell('\cp -rpa {} {}'.format(data_path, backup_path))
                        file_name = data_path.split("/")[-1]
                        if "port_rule" in file_name:
                            self.print_log(public.lang("Firewall port rules ✓"), 'backup')
                            firewall_info["port_data_path"] = backup_path + "/" + file_name
                        elif "ip_rules" in file_name:
                            self.print_log(public.lang("Firewall IP rules ✓"), 'backup')
                            firewall_info["ip_data_path"] = backup_path + "/" + file_name
                        elif "port_forward" in file_name:
                            self.print_log(public.lang("Firewall forwarding rules ✓"), 'backup')
                            firewall_info["forward_data_path"] = backup_path + "/" + file_name
                        elif "country" in file_name:
                            self.print_log(public.lang("Firewall region rules ✓"), 'backup')
                            firewall_info["country_data_path"] = backup_path + "/" + file_name

                # 将防火墙信息写入备份配置文件
                data_list = self.get_backup_data_list(timestamp)
                data_list['data_list']['firewall'] = firewall_info
                self.update_backup_data_list(timestamp, data_list)
            except Exception as e:
                data_list['data_list']['firewall'] = {
                    "status": 3,
                    "err_msg": e
                }
                self.update_backup_data_list(timestamp, data_list)

        self.print_log(public.lang("Firewall data backup completed"), "backup")

    def init_firewall_data(self):
        self.print_log(public.lang("Initializing firewall data"), "restore")
        if not os.path.exists('/etc/systemd/system/BT-FirewallServices.service'):
            panel_path = public.get_panel_path()
            exec_shell = '('
            if not os.path.exists('/usr/sbin/ipset'):
                exec_shell = exec_shell + '{} install ipset -y;'.format(public.get_sys_install_bin())
            exec_shell = exec_shell + 'sh {panel_path}/script/init_firewall.sh;btpython -u {panel_path}/script/upgrade_firewall.py )'.format(
                panel_path=panel_path
            )
            public.ExecShell(exec_shell)
            return {'status': True, 'msg': public.lang('Installed.')}
        elif public.ExecShell("iptables -C INPUT -j IN_BT")[1] != '':  # 丢失iptable链 需要重新创建
            exec_shell = 'sh {}/script/init_firewall.sh'.format(public.get_panel_path())
            public.ExecShell(exec_shell)
            return {'status': True, 'msg': public.lang('Installed.')}
        else:
            return {'status': True, 'msg': public.lang('Installed.')}

    def restore_firewall_data(self, timestamp):
        with app.app_context():
            self.print_log("====================================================", "restore")
            self.print_log(public.lang("Starting restoration of firewall data"), "restore")
            self.init_firewall_data()
            resotre_data = self.get_restore_data_list(timestamp)
            firewall_data = resotre_data['data_list']['firewall']
            port_rule_file = firewall_data.get('port_data_path')
            try:
                if port_rule_file:
                    if os.path.exists(port_rule_file):
                        self.print_log(public.lang("Starting restoration of firewall port rules"), "restore")
                        result = firewall_com().import_rules(public.to_dict_obj({"rule": 'port', 'file': port_rule_file}))
                        if result['status'] == 0:
                            self.print_log(public.lang("Firewall port rules restored successfully ✓"), "restore")
                        else:
                            self.print_log(public.lang("Failed to restore firewall port rules"), "restore")
                ip_rule_file = firewall_data.get('ip_data_path')
                if ip_rule_file:
                    if os.path.exists(ip_rule_file):
                        self.print_log(public.lang("Starting restoration of firewall IP rules"), "restore")
                        result = firewall_com().import_rules(public.to_dict_obj({"rule": 'ip', 'file': ip_rule_file}))
                        if result['status'] == 0:
                            self.print_log(public.lang("Firewall IP rules restored successfully ✓"), "restore")
                        else:
                            self.print_log(public.lang("Failed to restore firewall IP rules"), "restore")

                forward_rule_file = firewall_data.get('forward_data_path')
                if forward_rule_file:
                    if os.path.exists(forward_rule_file):
                        self.print_log(public.lang("Starting restoration of firewall forwarding rules"), "restore")
                        result = firewall_com().import_rules(
                            public.to_dict_obj({"rule": 'forward', 'file': forward_rule_file}))
                        if result['status'] == 0:
                            self.print_log(public.lang("Firewall forwarding rules restored successfully ✓"), "restore")
                        else:
                            self.print_log(public.lang("Failed to restore firewall forwarding rules"), "restore")

                country_rule_file = firewall_data.get('country_data_path')
                if country_rule_file:
                    if os.path.exists(country_rule_file):
                        self.print_log(public.lang("Starting restoration of firewall region rules"), "restore")
                        public.ExecShell('\cp -rpa {}  /www/server/panel/data/firewall'.format(country_rule_file))
                        country_rule_file_last_path = country_rule_file.split("/")[-1]
                        result = safe_firewall_main().import_rules(
                            public.to_dict_obj({'rule_name': 'country_rule', 'file_name': country_rule_file_last_path}))
                        if result['status'] == 0:
                            self.print_log(public.lang("Firewall region rules restored successfully ✓"), "restore")
                        else:
                            self.print_log(public.lang("Failed to restore firewall region rules"), "restore")

                # 重启防火墙
                self.print_log(public.lang("Starting firewall restart"), "restore")
                firewall_com().set_status(public.to_dict_obj({'status': 1}))
                self.print_log(public.lang("Firewall restart completed"), "restore")
                resotre_data['data_list']['firewall']['status'] = 2
                self.update_restore_data_list(timestamp, resotre_data)
            except Exception as e:
                self.print_log(public.lang("Failed to restore firewall data: {}").format(str(e)), "restore")
                resotre_data['data_list']['firewall']['status'] = 3
                resotre_data['data_list']['firewall']['err_msg'] = str(e)
                self.update_restore_data_list(timestamp, resotre_data)


if __name__ == '__main__':
    # 获取命令行参数
    if len(sys.argv) < 2:
        print("Usage: btpython backup_manager.py <method> <timestamp>")
        sys.exit(1)
    method_name = sys.argv[1]  # 方法名  
    timestamp = sys.argv[2]
    firewall_manager = FirewallModule()  # 实例化对象
    if hasattr(firewall_manager, method_name):  # 检查方法是否存在
        method = getattr(firewall_manager, method_name)  # 获取方法
        method(timestamp)  # 调用方法
    else:
        print(f"Error: method '{method_name}' not found")
