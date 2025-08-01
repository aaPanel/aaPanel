# coding: utf-8
# -------------------------------------------------------------------
# aaPanel
# -------------------------------------------------------------------
# Copyright (c) 2015-2099  aaPanel(www.aapanel.com) All rights reserved.
# -------------------------------------------------------------------
# 首页安全风险，展示检测结果
# ------------------------------
import json
import os
import sys


from safeModel.base import safeBase

os.chdir("/www/server/panel")
sys.path.append("class/")
import public, config, datetime

class main(safeBase):
    __path = '/www/server/panel/data/warning_report'
    __risk = __path + '/risk'
    __data = __path + '/data.json'
    new_result = "/www/server/panel/data/warning/resultresult.json"
    data = []
    final_obj = {}
    all_cve = 0
    cve_num = 0
    high_cve = 0
    mid_cve = 0
    low_cve = 0
    cve_list = []
    high_warn = 0
    mid_warn = 0
    low_warn = 0
    high_warn_list = []
    mid_warn_list = []
    low_warn_list = []
    auto_fix = []  # 自动修复列表

    def __init__(self):
        self.configs = config.config()
        if not os.path.exists(self.__path):
            os.makedirs(self.__path, 384)

    def get_report(self, get):
        '''
            将检测数据，填充到html，并展示检测报告数据
        '''
        public.set_module_logs("report", "get_report")
        self.cve_list = []
        self.high_warn_list = []
        self.mid_warn_list = []
        self.low_warn_list = []
        # if not os.path.exists(self.__data):
        #     return public.returnMsg(False, '导出失败，未发现扫描结果')
        # data = json.loads(public.readFile(self.__data))
        # 获取最新的检测结果
        if not os.path.exists(self.new_result):
            return public.returnMsg(False, "No test results found, please perform a homepage security risk scan first")
        cve_result = json.loads(public.ReadFile(self.new_result))

        first = {}
        first["date"] = cve_result["check_time"]  # 带有时间的检测日期
        first["host"] = public.get_hostname()  # 主机名
        first["ip"] = public.get_server_ip()  # 外网IP
        first["local_ip"] = public.GetLocalIp()  # 内网IP
        # if os.path.exists("/www/server/panel/data/warning/result.json"):
        #     with open("/www/server/panel/data/warning/result.json") as f:
        #         cve_result = json.load(f)
        #         public.print_log(cve_result)
        #         self.cve_list = cve_result["risk"]
        #         self.high_cve = cve_result["count"]["serious"]
        #         self.mid_cve = cve_result["count"]["high_risk"]
        #         self.low_cve = cve_result["count"]["moderate_risk"]
        #         self.all_cve = cve_result["vul_count"]

        if "risk" not in cve_result:
            return public.returnMsg(False, "Risk field not found")
        # 获取可自动修复列表
        if "is_autofix" in cve_result:
            self.auto_fix = cve_result["is_autofix"]
        for risk in cve_result["risk"]:
            # 若为漏洞
            if risk["title"].startswith("CVE") or risk["title"].startswith("RH"):
                self.cve_list.append(risk)
                self.cve_num += 1
                if risk["level"] == 3:
                    self.high_cve += 1
                elif risk["level"] == 2:
                    self.mid_cve += 1
                elif risk["level"] == 1:
                    self.low_cve += 1
                else:
                    self.cve_num -= 1
                    continue
            # 其余为风险
            else:
                if risk["level"] == 3:
                    self.high_warn += 1
                    self.high_warn_list.append(risk)
                elif risk["level"] == 2:
                    self.mid_warn += 1
                    self.mid_warn_list.append(risk)
                elif risk["level"] == 1:
                    self.low_warn += 1
                    self.low_warn_list.append(risk)
                else:
                    continue
        # for d in data["risk"]:
        #     if "title" in d:
        #         if d["level"] == 3:
        #             self.high_warn += 1
        #             self.high_warn_list.append(d)
        #         elif d["level"] == 2:
        #             self.mid_warn += 1
        #             self.mid_warn_list.append(d)
        #         else:
        #             self.low_warn += 1.
        #             self.low_warn_list.append(d)

        if self.high_warn + self.high_cve > 1:
            total_level = 'High'
            level_color = 'High'
        elif self.mid_warn + self.mid_cve > 10 or self.high_warn + self.high_cve == 1:
            total_level = 'Medium'
            level_color = 'Medium'
        else:
            total_level = 'Low'
            level_color = 'Low'
        # self.cve_num = self.high_cve + self.mid_cve + self.low_cve
        level_reason = "The server has not identified any significant security risks and continues to maintain them!"
        if total_level == "High":
            level_reason = "There are high-risk security risks or system vulnerabilities on the server, which may lead to hacker intrusion,<span style=\"" \
                           "font-size: 1.1em;font-weight: 700;color: red;\">Please fix as soon as possible！</span>"
        if total_level == "High":
            level_reason = "The server has identified potential security risks，<span style=\"" \
                           "font-size: 1.1em;font-weight: 700;color: red;\">Suggest repairing as soon as possible！</span>"
        warn_level = 'Low'
        if self.high_warn > 0:
            warn_level = 'High'
            first_warn = "Identify {} high-risk safety risks".format(self.high_warn)
        elif self.mid_warn > 5:
            warn_level = 'Medium'
            first_warn = "Discovering numerous security risks with moderate threats"
        else:
            first_warn = "No significant security risks were identified"
        cve_level = 'Low'
        if self.cve_num > 1:
            cve_level = 'High'
            first_cve = "Discovered {} system vulnerabilities".format(self.cve_num)
        elif self.cve_num == 1:
            cve_level = 'Medium'
            first_cve = "Discovered a small number of system vulnerabilities"
        else:
            first_cve = "No system vulnerabilities found"
        second = {}
        long_date = cve_result["check_time"]  # 带有时间的检测日期
        date_obj = datetime.datetime.strptime(long_date, "%Y/%m/%d %H:%M:%S")
        second["date"] = date_obj.strftime("%Y/%m/%d")
        second["last_date"] = cve_result.get('check_time', '')
        second["level_color"] = level_color
        second["total_level"] = total_level
        second["level_reason"] = level_reason
        second["warn_level"] = warn_level
        second["first_warn"] = first_warn
        second["cve_level"] = cve_level
        second["first_cve"] = first_cve
        third = {}
        # 获取扫描记录
        warn_times = 0
        repair_times = 0
        record_file = self.__path + "/record.json"
        if os.path.exists(record_file):
            record = json.loads(public.ReadFile(record_file))
            for r in record["scan"]:
                warn_times += r["times"]
            for r in record["repair"]:
                repair_times += r["times"]
        # with open(self.__path+"/record.json", "r") as f:
        #     record = json.load(f)
        # for r in record["scan"]:
        #     warn_times += r["times"]
        # for r in record["repair"]:
        #     repair_times += r["times"]
        third["warn_times"] = warn_times
        third["cve_times"] = warn_times
        third["repair_times"] = repair_times
        third["last_month"] = (date_obj - datetime.timedelta(days=6)).strftime("%m")
        third["last_day"] = (date_obj - datetime.timedelta(days=6)).strftime("%d")
        third["month"] = date_obj.strftime("%m")
        third["day"] = date_obj.strftime("%d")
        third["second_warn"] = "Daily login panel and routine server security risk detection."
        if self.cve_num > 0:
            third["second_cve"] = "Perform vulnerability scans on system kernel versions and popular applications to identify potential vulnerability risks."
        else:
            third["second_cve"] = "Vulnerability scanning was conducted on the system kernel version and popular applications, and no vulnerability risks were found."
        third["repair"] = "Perform one click repair to solve security issues."
        fourth = {}

        fourth["warn_num"] = len(self.high_warn_list)
        fourth["cve_num"] = self.cve_num
        fourth["web_num"] = 41
        fourth["sys_num"] = 29
        fourth["cve_num"] = 5599
        fourth["kernel_num"] = 5
        fourth["high_cve"] = str(self.high_cve)
        if self.high_cve == 0:
            fourth["high_cve"] = "0"
        fourth["mid_cve"] = str(self.mid_cve)
        if self.mid_cve == 0:
            fourth["mid_cve"] = "0"
        fourth["low_cve"] = str(self.low_cve)
        if self.low_cve == 0:
            fourth["low_cve"] = "0"
        fourth["high_warn"] = str(self.high_warn)
        if self.high_warn == 0:
            fourth["high_warn"] = "0"
        fourth["mid_warn"] = str(self.mid_warn)
        if self.mid_warn == 0:
            fourth["mid_warn"] = "0"
        fourth["low_warn"] = str(int(self.low_warn))
        if self.low_warn == 0:
            fourth["low_warn"] = "0"
        fifth = {}
        num = 1  # 序号
        focus_high_list = []
        for hwl in self.high_warn_list:
            focus_high_list.append(
                {
                    "num": str(num),
                    "name": str(hwl["msg"]),
                    "level": "High Risk",
                    "ps": str(hwl["ps"]),
                    "tips": '\n'.join(hwl["tips"]),
                    "auto": self.is_autofix1(hwl["m_name"])
                }
            )
            num += 1
        fifth["focus_high_list"] = focus_high_list
        focus_mid_list = []
        for mwl in self.mid_warn_list:
            focus_mid_list.append(
                {
                    "num": num,
                    "name": mwl["msg"],
                    "level": "Medium Risk",
                    "ps": mwl["ps"],
                    "tips": '\n'.join(mwl["tips"]),
                    "auto": self.is_autofix1(mwl["m_name"])
                }
            )
            num += 1
        fifth["focus_mid_list"] = focus_mid_list
        focus_cve_list = []
        for cl in self.cve_list:
            tmp_cve = {
                    "num": num,
                    "name": cl["m_name"],
                    "level": "High Risk",
                    "ps": cl["ps"],
                    "tips": '\n'.join(cl["tips"]),
                    "auto": "Support"
                }
            if cl["level"] == 2:
                tmp_cve["name"] = cl["m_name"]
                tmp_cve["level"] = "Medium Risk"
            elif cl["level"] == 1:
                tmp_cve["name"] = cl["m_name"]
                tmp_cve["level"] = "Low Risk"
            focus_cve_list.append(tmp_cve)
            num += 1
        fifth["focus_cve_list"] = focus_cve_list
        sixth = {}
        num = 1  # 序号
        low_warn_list = []
        for lwl in self.low_warn_list:
            low_warn_list.append(
                {
                    "num": str(num),
                    "name": str(lwl["msg"]),
                    "level": "Low Risk",
                    "ps": str(lwl["ps"]),
                    "tips": '\n'.join(lwl["tips"]),
                    "auto": self.is_autofix1(lwl["m_name"])
                }
            )
            num += 1
        sixth["low_warn_list"] = low_warn_list
        ignore_list = []
        for ig in cve_result["ignore"]:
            if "title" in ig:
                ignore_list.append(
                    {
                        "num": num,
                        "name": ig["msg"],
                        "level": "Ignore items",
                        "ps": ig["ps"],
                        "tips": '\n'.join(ig["tips"]),
                        "auto": self.is_autofix(ig)
                    }
                )
            elif "cve_id" in ig:
                ignore_list.append(
                    {
                        "num": num,
                        "name": ig["cve_id"],
                        "level": "Ignore items",
                        "ps": ig["vuln_name"],
                        "tips": "Upgrade the 【{}】 version to {} or a higher version.".format('、'.join(ig["soft_name"]), ig["vuln_version"]),
                        "auto": self.is_autofix(ig)
                    }
                )
            num += 1
        sixth["ignore_list"] = ignore_list
        self.final_obj = {"first": first, "second": second, "third": third, "fourth": fourth, "fifth": fifth, "sixth": sixth}

        # 添加恶意文件扫描数据
        # from projectModelV2 import safecloudModel,scanningModel,safe_detectModel
        from projectModelV2.safecloudModel import main as safecloud_Model
        from projectModelV2.scanningModel import main as scanning_Model
        from projectModelV2.safe_detectModel import main as safe_detect_Model


        safecloud = safecloud_Model()  # 只获取前1000条恶意文件
        malicious_files = safecloud.get_webshell_result({'p': 1, 'limit': 1000})
        if malicious_files.get('status',0) == 0:
            self.final_obj['malicious_files'] = malicious_files.get('message', {})
        else:
            self.final_obj['malicious_files'] = {'status': False, 'msg': 'Failed to retrieve malicious files'}

        # 启动网站漏洞扫描
        website_vulnerabilities = scanning_Model().startScan(' ')
        if website_vulnerabilities.get('status', 0) == 0:
            self.final_obj['website_vulnerabilities'] = website_vulnerabilities.get('message', {})
            self.final_obj['website_vulnerabilities']['status'] = True
        else:
            self.final_obj['website_vulnerabilities'] = {'status': False, 'msg': 'Failed to retrieve website vulnerabilities'}

        # 服务器漏洞检测
        try:
            server_security_list = self.read_log_file()
            server_security = safe_detect_Model().get_safe_count('')

            if server_security['status'] == 0:
                server_security_count = server_security.get('message', {})
            else:
                server_security_count = {}

            self.final_obj['server_security'] = {'status': True, 'server_security_list': server_security_list, 'server_security_count':server_security_count}
        except Exception as e:
            self.final_obj['server_security'] = {'status': False, 'server_security_list': [], 'server_security_count': {}}

        # 添加总评分
        total_score = safecloud.get_safe_overview(' ')
        if total_score.get('status', 0) == 0:
            self.final_obj['second']['level'] = total_score.get('message', {})['level']

        # 合并cve与漏洞风险项
        self.final_obj['fourth']['high_warn'] = str(int(self.final_obj['fourth']['high_warn']) + int(self.final_obj['fourth']['high_cve']))
        self.final_obj['fourth']['mid_warn'] = str(int(self.final_obj['fourth']['mid_warn']) + int(self.final_obj['fourth']['mid_cve']))
        self.final_obj['fourth']['low_warn'] = str(int(self.final_obj['fourth']['low_warn']) + int(self.final_obj['fourth']['low_cve']))

        return  public.return_message(0,0, self.final_obj)

    def read_log_file(self):
        import ast
        result_list = []
        try:
            with open("/www/server/panel/data/safe_detect_dict.log", 'r') as file:
                for line in file:
                    # 去除行尾的换行符
                    line = line.strip()
                    if line:  # 跳过空行
                        try:
                            # 将字符串转换为字典
                            data_dict = ast.literal_eval(line)
                            result_list.append(data_dict)
                        except Exception as e:
                            continue
            return result_list
        except Exception as e:
            return []

    def is_autofix(self, warn):
        data = json.loads(public.readFile(self.__data))
        if "title" in warn:
            if warn["m_name"] in data["is_autofix"]:
                return "Support"
            else:
                return "Not Support"
        if "cve_id" in warn:
            if list(warn["soft_name"].keys())[0] == "kernel":
                return "Not Support"
            else:
                return "Support"

    def is_autofix1(self, name):
        """
        @name 判断是否可以自动修复
        """
        if name in self.auto_fix:
            return "Support"
        else:
            return "Not Support"
