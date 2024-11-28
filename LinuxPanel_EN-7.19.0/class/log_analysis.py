# coding: utf-8
# +-------------------------------------------------------------------
# | aaPanel
# +-------------------------------------------------------------------
# | Copyright (c) 2015-2099 aaPanel(www.aapanel.com) All rights reserved.
# +-------------------------------------------------------------------
# | Author: lkq <lkq@aapanel.com>
# |
# | 日志分析工具
# +-------------------------------------------------------------------
import os
import time

import public


class log_analysis:
    path = '/www/server/panel/script/'
    log_analysis_path = '/www/server/panel/script/log_analysis.sh'

    def __init__(self):
        if not os.path.exists(self.path + '/log/'): os.makedirs(self.path + '/log/')
        if not os.path.exists(self.log_analysis_path):
            log_analysis_data = r'''help(){
	echo  "Usage: ./action.sh [options] [FILE] [OUTFILE]     "
	echo  "Options:"
	echo  "xxx.sh san_log     [FILE] Get the log list with the keywords xss|sql|mingsense information|php code execution in the successful request  [OUTFILE]   11"
	echo  "xxx.sh san     [FILE] Get list of logs with sql keyword in successful request   [OUTFILE]   11  "  
}

if [ $# == 0 ]
then
	help
	exit
fi

if [ ! -e $2 ]
then
	echo -e "$2: log file does not exist"
	exit
fi

if [ ! -d "log" ]
then
	mkdir log
fi

echo "[*] Starting ..."

if  [ $1 == "san_log" ] 
then
    echo "1">./log/$3
	echo "Start getting xss cross-site scripting attack logs..."

	grep -E ' (200|302|301|500|444|403|304) ' $2  | grep -i -E "(javascript|data:|alert\(|onerror=|%3Cimg%20src=x%20on.+=|%3Cscript|%3Csvg/|%3Ciframe/|%3Cscript%3E).*?HTTP/1.1" >./log/$3xss.log

	echo "Analysis logs have been saved to./log/$3xss.log"
	echo "Scan to attack count: "`cat ./log/$3xss.log |wc -l`
	echo "20">./log/$3


	echo  "Start getting sql injection attack logs..." 
	echo "Analysis logs have been saved to./log/$3sql.log"
grep -E ' (200|302|301|500|444|403) ' $2 | grep -i -E "(from.+?information_schema.+|select.+(from|limit)|union(.*?)select|extractvalue\(|case when|extractvalue\(|updatexml\(|sleep\().*?HTTP/1.1" > ./log/$3sql.log
    echo "Scan to attack count: "`cat ./log/$3sql.log |wc -l`
    echo "40">./log/$3

	echo -e "Start getting related logs such as file traversal/code execution/scanner information/configuration files"
	grep -E ' (200|302|301|500|444|403) ' $2 | grep -i -E "(\.\.|WEB-INF|/etc|\w\{1,6\}\.jsp |\w\{1,6\}\.php|\w+\.xml |\w+\.log |\w+\.swp |\w*\.git |\w*\.svn |\w+\.json |\w+\.ini |\w+\.inc |\w+\.rar |\w+\.gz |\w+\.tgz|\w+\.bak |/resin-doc).*?HTTP/1.1" >./log/$3san.log
	echo "Analysis logs have been saved to./log/$3san.log"
	echo "Scan to attack count: "`cat ./log/$3san.log |wc -l`
	echo "50">./log/$3


	echo -e "Start getting the php code execution scan log"
	grep -E ' (200|302|301|500|444|403) ' $2 | grep -i -E "(gopher://|php://|file://|phar://|dict://data://|eval\(|file_get_contents\(|phpinfo\(|require_once\(|copy\(|\_POST\[|file_put_contents\(|system\(|base64_decode\(|passthru\(|\/invokefunction\&|=call_user_func_array).*?HTTP/1.1" >./log/$3php.log
	echo "Analysis logs have been saved to./log/$3php.log"
	echo "Scan to attack count: "`cat ./log/$3php.log |wc -l`
	echo "60">./log/$3


	echo -e "The number and value of the most visited ip is being counted"
# 	cat $2|awk -F" " '{print $1}'|sort|uniq -c|sort -nrk 1 -t' '|head -100
	awk '{print $1}' $2 |sort|uniq -c |sort -nr |head -100 >./log/$3ip.log
	echo "80">./log/$3


    echo -e "The number and value of the url of the most visited request interface is being counted"
	awk '{print $7}' $2 |sort|uniq -c |sort -nr |head -100 >./log/$3url.log
	echo "100">./log/$3


elif [ $1 == "san" ]
then
    echo "1">./log/$3
	echo "Start getting xss cross-site scripting attack logs..."
	grep -E ' (200|302|301|500|444|403|304) ' $2  | grep -i -E "(javascript|data:|alert\(|onerror=|%3Cimg%20src=x%20on.+=|%3Cscript|%3Csvg/|%3Ciframe/|%3Cscript%3E).*?HTTP/1.1" >./log/$3xss.log
	echo "Analysis logs have been saved to./log/$3xss.log"
	echo "Scan to attack count: "`cat ./log/$3xss.log |wc -l`
	echo "20">./log/$3

	echo  "Start getting sql injection attack logs..." 
	echo "Analysis logs have been saved to./log/$3sql.log"
grep -E ' (200|302|301|500|444|403) ' $2 | grep -i -E "(from.+?information_schema.+|select.+(from|limit)|union(.*?)select|extractvalue\(|case when|extractvalue\(|updatexml\(|sleep\().*?HTTP/1.1" > ./log/$3sql.log
    echo "Scan to attack count: "`cat ./log/$3sql.log |wc -l`
    echo "40">./log/$3

	echo -e "Start getting related logs such as file traversal/code execution/scanner information/configuration files"
	grep -E ' (200|302|301|500|444|403) ' $2 | grep -i -E "(\.\.|WEB-INF|/etc|\w\{1,6\}\.jsp |\w\{1,6\}\.php|\w+\.xml |\w+\.log |\w+\.swp |\w*\.git |\w*\.svn |\w+\.json |\w+\.ini |\w+\.inc |\w+\.rar |\w+\.gz |\w+\.tgz|\w+\.bak |/resin-doc).*?HTTP/1.1" >./log/$3san.log

	echo "Analysis logs have been saved to./log/$3san.log"
	echo "Scan to attack count: "`cat ./log/$3san.log |wc -l`
	echo "60">./log/$3

	echo -e "Start getting the php code execution scan log"
	grep -E ' (200|302|301|500|444|403) ' $2 | grep -i -E "(gopher://|php://|file://|phar://|dict://data://|eval\(|file_get_contents\(|phpinfo\(|require_once\(|copy\(|\_POST\[|file_put_contents\(|system\(|base64_decode\(|passthru\(|\/invokefunction\&|=call_user_func_array).*?HTTP/1.1" >./log/$3php.log
	echo "Analysis logs have been saved to./log/$3php.log"
	echo "Scan to attack count: "`cat ./log/$3php.log |wc -l`
	echo "100">./log/$3

else 
	help
fi

echo "[*] shut down"
'''
            public.WriteFile(self.log_analysis_path, log_analysis_data)

    def get_log_format(self, path):
        '''
        @获取日志格式
        '''
        f = open(path, 'r')
        data = None
        for i in f:
            data = i.split()
            break
        f.close()
        if not data: return False
        if not public.check_ip(data[0]): return False
        if len(data) < 6: return False
        return True

    def log_analysis(self, get):
        '''
        分析日志
        @param path:需要分析的日志
        @return 返回具体的分析结果
        @ 需要使用异步的方式进行扫描
        '''
        path = get.path
        log_path = public.Md5(path)
        serverType = public.get_webserver()
        if serverType == "nginx":
            pass
        elif serverType == 'apache':
            #path = path.strip("-access_log") + '-access_log'
            pass
        elif serverType == 'openlitespeed':
            # path = path.strip("_ols.access_log") + '_ols.access_log'
            return public.ReturnMsg(False, 'openlitespeed is not supported yet')

        # public.print_log("path1:{}".format(path))
        # public.print_log("serverType:{}".format(serverType))

        if not os.path.exists(path): return public.ReturnMsg(False, 'No log file')
        if os.path.getsize(path) > 9433107294: return public.ReturnMsg(False, 'The log file is too large!')
        if os.path.getsize(path) < 10: return public.ReturnMsg(False, 'log is empty')
        # public.print_log("log_path{}".format(log_path))
        # public.print_log("self.log_analysis_path{}".format(self.log_analysis_path))
        # public.print_log("path{}".format(path))
        if self.get_log_format(path):
            public.ExecShell(
                "cd %s && bash %s san_log %s %s &" % (self.path, self.log_analysis_path, path, log_path))
        else:
            public.ExecShell("cd %s && bash %s san %s %s &" % (self.path, self.log_analysis_path, path, log_path))
        speed = self.path + '/log/' + log_path+".time"
        public.WriteFile(speed,str(time.time())+"[]"+time.strftime('%Y-%m-%d %X',time.localtime())+"[]"+"0")
        return public.ReturnMsg(True, 'Start scan successful')

    def speed_log(self, get):
        '''
        扫描进度
        @param path:扫描的日志文件
        @return 返回进度
        '''
        path = get.path.strip()
        log_path = public.Md5(path)
        speed = self.path + '/log/' + log_path
        if os.path.getsize(speed) < 1: return public.ReturnMsg(False, 'log is empty')
        if not os.path.exists(speed): return public.ReturnMsg(False, 'The directory was not scanned')
        try:
            data = public.ReadFile(speed)
            data = int(data)
            if data==100:
                time_data,start_time,status=public.ReadFile(self.path + '/log/' + log_path+".time").split("[]")
                public.WriteFile(speed+".time",str(time.time()-float(time_data)) + "[]" + start_time + "[]" + "1")
            return public.ReturnMsg(True, data)
        except:
            return public.ReturnMsg(True, 0)

    def get_log_count(self, path, is_body=False):
        count = 0
        if is_body:
            if not os.path.exists(path): return ''
            data = ''
            with open(path, 'r') as f:
                for i in f:
                    count += 1
                    data = data.replace('<', '&lt;').replace('>', '&gt;') + i.replace('<', '&lt;').replace('>', '&gt;')
                    if count >= 300: break
            return data
        else:
            if not os.path.exists(path): return count
            with open(path, 'rb') as f:
                for i in f:
                    count += 1
            return count

    def get_result(self, get):
        '''
        扫描结果
        @param path:扫描的日志文件
        @return 返回结果
        '''
        path = get.path.strip()
        log_path = public.Md5(path)
        speed = self.path + '/log/' + log_path
        result = {}
        if os.path.exists(speed):
            result['is_status'] = True
        else:
            result['is_status'] = False
        if os.path.exists(speed+".time") and os.path.getsize(speed+".time") > 0:
            time_data, start_time, status = public.ReadFile(self.path + '/log/' + log_path + ".time").split("[]")
            if status == '1' or start_time==1:
                result['time']=time_data
                result['start_time']=start_time
        else:
            result['time'] = "0"
            result['start_time'] = "2022/2/22 22:22:22"
        if 'time' not in result:
            result['time'] = "0"
            result['start_time'] = "2022/2/22 22:22:22"
        result['xss'] = self.get_log_count(speed + 'xss.log')
        result['sql'] = self.get_log_count(speed + 'sql.log')
        result['san'] = self.get_log_count(speed + 'san.log')
        result['php'] = self.get_log_count(speed + 'php.log')
        result['ip'] = self.get_log_count(speed + 'ip.log')
        result['url'] = self.get_log_count(speed + 'url.log')
        return result

    def get_detailed(self, get):
        path = get.path.strip()
        log_path = public.Md5(path)
        speed = self.path + '/log/' + log_path
        type_list = ['xss', 'sql', 'san', 'php', 'ip', 'url']
        if get.type not in type_list: return public.ReturnMsg(False, 'Type mismatch')
        if not os.path.exists(speed + get.type + '.log'): return public.ReturnMsg(False, 'Record does not exist')
        return self.get_log_count(speed + get.type + '.log', is_body=True)
