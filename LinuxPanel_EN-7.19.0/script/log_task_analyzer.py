import datetime
import sys
import os
os.chdir('/www/server/panel/')
sys.path.insert(0, "class/")
import public

# 检查是否提供了日志文件路径作为命令行参数
if len(sys.argv) != 2:
    print("Usage: python log_task_analyzer.py <log_file_path>")
    sys.exit(1)

# 从命令行参数中获取日志文件路径
log_file = sys.argv[1]

# 记录任务执行状态的文件路径
task_log = "/tmp/task_log.log"

# 反向读取日志文件
try:
    with open(log_file, 'r', encoding='utf-8', errors='ignore') as f:
        lines = f.readlines()[::-1]
except FileNotFoundError:
    print("Log file {} not found.".format(log_file))
    sys.exit(1)

# 初始化变量
found_successful = False
found_error_before_next_successful = False

# 要查找的错误模式
error_patterns = ["错误", "失败", "command not found", "Unknown error", "不存在", "请先到软件商店安装日志清理工具", "failed to run command", "No such file or directory", "not supported or disabled in libcurl"]

# 迭代检查日志内容
for line in lines:
    if "Successful" in line:
        if found_successful:
            # 如果找到第二个 "Successful"，停止搜索
            break
        else:
            # 找到第一个 "Successful"
            found_successful = True
    elif any(error_pattern in line for error_pattern in error_patterns) and found_successful:
        # 如果在找到 "Successful" 后发现任何错误模式，则标记错误
        found_error_before_next_successful = True
        break

# 根据检查结果记录日志
with open(task_log, 'a') as f:
    current_time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    # 提取 echo 值作为日志文件名的前缀
    echo_value = log_file.split('/')[-1].split('.')[0]
    crontab_data_list = public.M('crontab').where('echo=?', (echo_value,)).select()
    
    if found_successful and found_error_before_next_successful:
        if crontab_data_list:
            public.M('crontab').where('echo=?', (echo_value,)).setField('result', 0)

        # f.write("{0} - 最后一次定时任务执行发现错误，执行失败\n".format(current_time))
    else:
        if crontab_data_list:
            public.M('crontab').where('echo=?', (echo_value,)).setField('result', 1)
        # f.write("{0} - 最后一次定时任务执行成功\n".format(current_time))
