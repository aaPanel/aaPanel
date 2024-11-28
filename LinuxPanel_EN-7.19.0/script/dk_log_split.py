#!/usr/bin/python
# coding: utf-8
# -----------------------------
# docker container log cutting script
# -----------------------------
import sys
import os
import time
import datetime

os.chdir("/www/server/panel")
sys.path.append('class/')
import public


class DkLogSpilt:
    task_list = []

    def __init__(self):
        if not public.M('sqlite_master').db('docker_log_split').where('type=? AND name=?', ('table', 'docker_log_split')).count():
            self.task_list = []
        else:
            self.task_list = public.M('docker_log_split').select()

    def run(self):
        if not self.task_list:
            print('No docker log cutting task')
        for task in self.task_list:
            try:
                if task['split_type'] == 'day':
                    self.day_split(task)
                elif task['split_type'] == 'size':
                    self.size_split(task)
            except:
                print('{} Failed to cut log!'.format(task['name']))

    def day_split(self, task):
        now_time = int(time.time())
        exec_time = int(self.get_timestamp_of_hour_minute(task['split_hour'], task['split_minute']))
        if now_time <= exec_time <= now_time + 300:
            print("{} container starts log cutting".format(task['name']))
            split_path = '/var/lib/docker/containers/history_logs/{}/'.format(task['pid'])
            if not os.path.exists(split_path):
                os.makedirs(split_path)
            os.rename(task['log_path'], split_path + task['pid'] + "-json.log" + '_' + str(int(time.time())))
            public.writeFile(task['log_path'], '')
            print("{} log has been cut to:{}".format(task['name'],split_path + task['pid'] + "-json.log" + '_' + str(int(time.time()))))
            self.check_save(task)
        else:
            print('{}container log has not reached the cutting time'.format(task['name']))


    def size_split(self, task):
        if not os.path.exists(task['log_path']):
            print('Log file does not exist')
            return
        if os.path.getsize(task['log_path']) >= task['split_size']:
            print("{} container starts log cutting".format(task['name']))
            split_path = '/var/lib/docker/containers/history_logs/{}/'.format(task['pid'])
            if not os.path.exists(split_path):
                os.makedirs(split_path)
            os.rename(task['log_path'], split_path + task['pid'] + "-json.log" + '_' + str(int(time.time())))
            public.writeFile(task['log_path'], '')
            print("{} log has been cut to:{}".format(task['name'],split_path + task['pid'] + "-json.log" + '_' + str(int(time.time()))))
            self.check_save(task)
        else:
            print('{} container log has not reached cutting size'.format(task['name']))

    def check_save(self, task):
        split_path = '/var/lib/docker/containers/history_logs/{}/'.format(task['pid'])
        file_count = len(os.listdir(split_path))
        if file_count > task['save']:
            file_list = os.listdir(split_path)
            file_list.sort()
            for i in range(file_count - task['save']):
                os.remove(split_path + file_list[i])
                print('Delete log files:{}'.format(split_path + file_list[i]))
        print('The latest {} logs have been retained'.format(task['save']))

    def get_timestamp_of_hour_minute(self, hour, minute):
        """获取当天指定时刻的时间戳。
        Args:
          hour: 小时。
          minute: 分钟。
        Returns:
          时间戳。
        """
        current_time = datetime.datetime.now()
        timestamp = current_time.replace(hour=hour, minute=minute, second=0, microsecond=0)
        return int(timestamp.timestamp())


if __name__ == '__main__':
    dk = DkLogSpilt()
    dk.run()
