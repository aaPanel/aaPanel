# coding: utf-8
# +-------------------------------------------------------------------
# | aapanel
# +-------------------------------------------------------------------
# | Copyright (c) 2015-2099 aaPanel(http:#aapanel.com) All rights reserved.
# +-------------------------------------------------------------------
# | Author: sww <hwl@aapanel.com>
# +-------------------------------------------------------------------

import json
import os
import re
import time
import traceback
import public
import json
from flask import request
from public.validate import Param
from datetime import datetime

try:
    from BTPanel import cache
    import requests
except:
    pass



class crontab:
    field = 'id,name,type,where1,where_hour,where_minute,echo,addtime,status,save,backupTo,sName,sBody,sType,urladdress,save_local,notice,notice_channel,db_type,split_type,split_value,type_id,rname,keyword,post_param,flock,time_set,backup_mode,db_backup_path,time_type,special_time,log_cut_path,user_agent,version,table_list,result,second'
    # field = 'id,name,type,where1,where_hour,where_minute,echo,addtime,status,save,backupTo,sName,sBody,sType,urladdress,save_local,notice,notice_channel,flock,time_set,backup_mode,db_backup_path,time_type,special_time,log_cut_path,user_agent,version,table_list,result,second'
    def __init__(self):
        try:
            cront = public.M('crontab').order("id desc").field(self.field).select()
        except Exception as e:
            pass
            # try:
            #    public.check_database_field("crontab.db", "crontab")
            # except Exception as e:
            #     pass
        
        cront = public.M('crontab').order("id desc").field(self.field).select()
        if type(cront) == str:
            public.M('crontab').execute("ALTER TABLE 'crontab' ADD 'status' INTEGER DEFAULT 1", ())
            public.M('crontab').execute("ALTER TABLE 'crontab' ADD 'save' INTEGER DEFAULT 3", ())
            public.M('crontab').execute("ALTER TABLE 'crontab' ADD 'backupTo' TEXT DEFAULT off", ())
            public.M('crontab').execute("ALTER TABLE 'crontab' ADD 'sName' TEXT", ())
            public.M('crontab').execute("ALTER TABLE 'crontab' ADD 'sBody' TEXT", ())
            public.M('crontab').execute("ALTER TABLE 'crontab' ADD 'sType' TEXT", ())
            public.M('crontab').execute("ALTER TABLE 'crontab' ADD 'urladdress' TEXT", ())
            public.M('crontab').execute("ALTER TABLE 'crontab' ADD 'save_local' INTEGER DEFAULT 0", ())
            public.M('crontab').execute("ALTER TABLE 'crontab' ADD 'notice' INTEGER DEFAULT 0", ())
            public.M('crontab').execute("ALTER TABLE 'crontab' ADD 'notice_channel' TEXT DEFAULT ''", ())
            public.M('crontab').execute("ALTER TABLE 'crontab' ADD 'db_type' TEXT DEFAULT ''", ())
            public.M('crontab').execute("UPDATE 'crontab' SET 'db_type'='mysql' WHERE sType='database' and db_type=''", ())
            public.M('crontab').execute("ALTER TABLE 'crontab' ADD 'split_type' TEXT DEFAULT ''", ())
            public.M('crontab').execute("ALTER TABLE 'crontab' ADD 'split_value' INTEGER DEFAULT 0", ())
            public.M('crontab').execute("ALTER TABLE 'crontab' ADD 'rname' TEXT DEFAULT ''", ())
            public.M('crontab').execute("ALTER TABLE 'crontab' ADD 'type_id' INTEGER", ())
            public.M('crontab').execute("PRAGMA foreign_keys=on", ())
            public.M('crontab').execute("ALTER TABLE 'crontab' ADD CONSTRAINT 'fk_type_id' FOREIGN KEY ('type_id') REFERENCES 'crontab_types' ('id')", ())
            public.M('crontab').execute("ALTER TABLE 'crontab' ADD 'keyword' TEXT DEFAULT ''", ())
            public.M('crontab').execute("ALTER TABLE 'crontab' ADD 'post_param' TEXT DEFAULT ''", ())
            public.M('crontab').execute("ALTER TABLE 'crontab' ADD 'flock' INTEGER DEFAULT 0", ())
            public.M('crontab').execute("ALTER TABLE 'crontab' ADD 'time_set' TEXT DEFAULT ''", ())
            public.M('crontab').execute("ALTER TABLE 'crontab' ADD 'backup_mode' TEXT DEFAULT ''", ())
            public.M('crontab').execute("ALTER TABLE 'crontab' ADD 'db_backup_path' TEXT DEFAULT ''", ())
            public.M('crontab').execute("ALTER TABLE 'crontab' ADD 'time_type' TEXT DEFAULT ''", ())
            public.M('crontab').execute("ALTER TABLE 'crontab' ADD 'special_time' TEXT DEFAULT ''", ())
            public.M('crontab').execute("ALTER TABLE 'crontab' ADD 'log_cut_path' TEXT DEFAULT ''", ())
            public.M('crontab').execute("ALTER TABLE 'crontab' ADD 'user_agent' TEXT DEFAULT ''", ())
            public.M('crontab').execute("ALTER TABLE 'crontab' ADD 'version' TEXT DEFAULT ''", ())
            public.M('crontab').execute("ALTER TABLE 'crontab' ADD 'table_list' TEXT DEFAULT ''", ())
            public.M('crontab').execute("ALTER TABLE 'crontab' ADD 'result' INTEGER DEFAULT 1", ())
            public.M('crontab').execute("ALTER TABLE 'crontab' ADD 'second' TEXT DEFAULT ''", ())
            cront = public.M('crontab').order("id desc").field(self.field).select()

        public.check_table('crontab_types',
                           '''CREATE TABLE "crontab_types" (
                                            "id" INTEGER PRIMARY KEY AUTOINCREMENT,
                                            "name" VARCHAR DEFAULT '',
                                            "ps" VARCHAR DEFAULT '');''')

    def get_zone(self, get):
        try:
            try:
                import pytz
            except:
                import os
                os.system("btpip install pytz")
                import pytz
            areadict = {}
            for i in pytz.all_timezones:
                if i.find('/') != -1:
                    area, zone = i.split('/')[0], i.split('/')[1]
                    if area not in areadict:
                        areadict[area] = [zone]
                    areadict[area].append(zone)
            for k, v in areadict.items():
                if k == 'status': continue
                areadict[k] = sorted(list(set(v)))
            # 取具体时区
            # 取具体时区地区
            result = public.ExecShell('ls -l /etc/localtime')
            area = result[0].split('/')[-2].strip()
            zone = result[0].split('/')[-1].strip()
            # areadict['status'] = [area, zone]
            return public.return_message(0,0,areadict)
        except:
            return public.return_message(-1,0, public.lang('Failed to obtain time zone!'))


    # 获取所有domain
    def get_domain(self, get=None):
        try:
            domains = public.M('domain').field('name').select()
            domains = ['http://' + i['name'] for i in domains]
            return domains
        except:
            return traceback.format_exc()

    # 设置置顶
    def set_task_top(self, get=None):
        """
        设置任务置顶，不传参数查询设置的计划任务列表
        :param get: task_id
        :return:
        """
        cron_task_top_path = '/www/server/panel/data/cron_task_top'
        if os.path.exists(cron_task_top_path):
            task_top = json.loads(public.readFile(cron_task_top_path))
        else:
            task_top = {'list': []}
        if get and hasattr(get, 'task_id'):
            task_top['list'] = [i for i in task_top['list'] if i != get['task_id']]
            task_top['list'].append(get['task_id'])
            public.writeFile(cron_task_top_path, json.dumps(task_top))
            return public.returnMsg(True, public.lang('Set to top successfully!'))
        return task_top

    # 取消置顶
    def cancel_top(self, get):
        """
        取消任务置顶
        :param get:task_id
        :return:
        """
        cron_task_top_path = '/www/server/panel/data/cron_task_top'
        if os.path.exists(cron_task_top_path):
            task_top = json.loads(public.readFile(cron_task_top_path))
        else:
            return public.returnMsg(True, 'Cancel pinned successfully!')
        if hasattr(get, 'task_id'):
            task_top['list'].remove(get['task_id'])
            public.writeFile(cron_task_top_path, json.dumps(task_top))
            return public.returnMsg(True, 'Cancel pinned successfully!')
        else:
            return public.returnMsg(False, public.lang('Please enter the unpinned ID！'))


    # 取计划任务列表
    def GetCrontab(self, get):
        try:
            self.checkBackup()
            self.__clean_log()
            type_id = get.type_id if (hasattr(get, 'type_id') and get.type_id is not None) else ""
            db_obj = public.M('crontab')
            query = db_obj.order("id desc").field(self.field)
            # 根据类型筛选任务
            if type_id:
                query=self._filter_by_type_id(query,type_id)
            # 获取所有任务数据
            all_tasks = query.select()
            # 获取置顶任务列表
            top_list = self.set_task_top()['list']
            top_data, other_data = self._partition_tasks(all_tasks, top_list)
            top_data=self._sort_tasks(top_data,get)
            other_data=self._sort_tasks(other_data,get)

            # 重新组织任务顺序
            data = top_data + other_data

            # 搜索过滤
            if hasattr(get, 'search') and get.search:
                data = self.search_tasks(data, get.search)
            
            # 应用分页
            paged_data, page_data = self._paginate(data, get)       
            # 格式化任务数据
            self._format_task(paged_data, top_list)        
            result = self._construct_result(db_obj, page_data, paged_data)
            if result:
                __CLOUD_TITLE = {
                "qiniu": "Qiniu Cloud Storage",
                "alioss": "Alibaba Cloud OSS",
                "ftp": "FTP Storage",
                "bos": "Baidu Cloud BOS",
                "obs": "Huawei Cloud OBS",
                "aws_s3": "AWS S3",
                "gdrive": "Google Drive",
                "msonedrive": "Microsoft OneDrive",
                "gcloud_storage": "Google Cloud Storage",
                "upyun": "Upyun Storage",
                "jdcloud": "JD Cloud Storage",
                "txcos": "Tencent Cloud COS",
                'tianyiyun': "Tianyi Cloud ZOS",
                'webdav':"WebDav",
                'minio':"MinIO Storage",
                'dogecloud':"Duoji Cloud COS",
                'localhost':'Local Disk'
                }
                for index in range(len(result)):
                    if 'backupTo' in result[index]:
                        try:
                            result[index]['backupTo'] = __CLOUD_TITLE[result[index]['backupTo']]
                        except:
                            result[index]['backupTo'] = result[index]['backupTo']
            return public.return_message(0,0,result)
    
        except Exception as e:
            # print(traceback.format_exc())
            return public.return_message(-1,0, public.lang('Query failed: ' + str(e)))


    def _filter_by_type_id(self,query,type_id):
        filters={
            '-1':('name like ?','%Do not delete%'),
            '0':('name not like ?','%Do not delete%'),
            '-2':('status=?',1),
            '-3':('status=?',0)
        }
        if type_id in filters:
            return query.where(*filters[type_id])
        return query.where('type_id=?',type_id)

    def _partition_tasks(self, all_tasks, top_list):
        # 使用 set 加速查找
        top_set = set(top_list)
        # 获取 top_data
        top_data = [task for task in all_tasks if str(task['id']) in top_set]
        # 按照 top_list 的顺序对 top_data 进行排序
        top_data = sorted(top_data, key=lambda x: top_list.index(str(x['id'])))
        # 获取 other_data
        other_data = [task for task in all_tasks if str(task['id']) not in top_set]
        return top_data, other_data
    
    def _sort_tasks(self,tasks,get):
        order_param=getattr(get,'order_param',None)
        if order_param:
            sort_key,order=order_param.split(' ') 
            reverse_order=order=='desc'
            if "rname" in order_param:
                    for task in tasks:
                        if not task.get('rname'):
                            task['rname'] = task['name']  # 将没有值的 rname 设置为 name 的值
            return sorted(tasks,key=lambda x:x[sort_key],reverse=reverse_order)
        return tasks 
  

    def _paginate(self,data,get):

        total_count=len(data)
        p=int(get.p) if hasattr(get,'p')else None
        count=int(get.count) if hasattr(get,'count')else None
        if p and count:
            start=(p-1)*count
            end=start+count
            page_data=public.get_page(total_count,p,count)
            paged_data=data[start:end]
        else:
            page_data=None
            paged_data=data
        return paged_data,page_data

    def _format_task(self,paged_data,top_list):
        top_set=set(top_list)
        for task in paged_data:
            task['type_zh']=self._get_task_type_zh(task)
            task['cycle']=self.generate_cycle(task['type'],task['where1'],task['where_hour'],task['where_minute'],task['sType'],task['second'])
            task['addtime']=self.get_addtime(task)
            task['backup_mode']=1 if task['backup_mode']=="1" else 0
            task['db_backup_path']=task.get('db_backup_path') or "/www/backup"
            task['rname'] = task.get('rname') or task['name']
            task['sort'] = 1 if str(task["id"]) in top_set else 0
            try:
                task['user'] = self.parse_user_from_sbody(task['sBody'])
            except:pass
             # 从sBody中移除sudo -u部分，只显示实际命令
            if 'sudo -u' in task['sBody']:
                task['sBody'] = task['sBody'].split("bash -c '", 1)[-1].rstrip("'")
            # task['user'] = task.get('user', 'root')

            # 任务不存在 ，标记为停止
            if task['type'] == 'once':
                res = public.ExecShell(f"systemctl show {task['echo'][:-3] + '.timer'} -p LastTriggerUSecMonotonic --value")[0].strip()
                if res not in ['0','']:
                    task['status'] == 0
                    public.M('crontab').where('id = ?', (task['id'],)).update({'status': 0})
                task['cycle'] = public.lang("{} Execute once", task['where1'])
            self.get_mysql_increment_save(task)
            self.format_cycle(task)

    def _get_task_type_zh(self,task):
        if task['type'] == "day":                        
            return public.getMsg('CRONTAB_TODAY')
        elif task['type'] == "day-n":
            return public.getMsg('CRONTAB_N_TODAY', (str(task['where1']),))
        elif task['type'] == "hour":
            return public.getMsg('CRONTAB_HOUR')
        elif task['type'] == "hour-n":
            return public.getMsg('CRONTAB_N_HOUR', (str(task['where1']),))
        elif task['type'] == "minute-n":           
            if task['second']:
                task['type'] ="second-n"
                return public.getMsg('CRONTAB_N_SECOND', (str(task['where1']),))
            return public.getMsg('CRONTAB_N_MINUTE', (str(task['where1']),))
        elif task['type'] == "week":
            task['type_zh'] = public.getMsg('CRONTAB_WEEK')
            if not task['where1']: task['where1'] = '0'
            return task['type_zh']
        elif task['type'] == "month":
            return public.getMsg(public.lang('CRONTAB_MONTH'))
            
    def get_mysql_increment_save(self,task):
        if task['sType']=="mysql_increment_backup":
            save = public.M("mysql_increment_backup").where("cron_id=?", (task['id'],)).count()
            if save>=0:
                task['save']=save
            else:
                save=""    
    def get_addtime(self,task):
        log_file='/www/server/cron/{}.log'.format(task['echo'])
        if os.path.exists(log_file):
            return self.get_last_exec_time(log_file)
        else:
            return " "        
    def search_tasks(self, data, search_term):
        return [item for item in data if search_term in item['name'] or search_term in item['sName'] or search_term in item['addtime'] or search_term in item['echo']]

    def generate_cycle(self, type, where1, where_hour, where_minute,sType,second:None):
        try:
            if where1 and type != "week": 
               where1 = int(where1)
            cycle = ""
            # week_days = ["一", "二", "三", "四", "五", "六", "日"]
            week_days = {
                '1': public.lang('Monday'),
                '2': public.lang('Tuesday'),
                '3': public.lang('Wednesday'),
                '4': public.lang('Thursday'),
                '5': public.lang('Friday'),
                '6': public.lang('Saturday'),
                '7': public.lang('Sunday')
            }
            
            if type == "day":
                cycle = public.lang("Execute once a day for {}:{}", where_hour, where_minute)
            elif type == "day-n":
                cycle = public.lang("Execute once every {} days on {}:{}",where1, where_hour, where_minute)
            elif type == "hour":
                cycle = public.lang("Execute once every {} minute of the hour",where_minute)
            elif type == "hour-n":
                # start_time = "{:02d}:{:02d}".format(where_hour, where_minute)
                # cycle = "从每天从00:00开始，每隔{}小时执行一次，直到1天结束（例如：{}".format(where1, start_time)
                cycle = public.lang("Starting from 0:00 every day, execute every {} minute of {} hours",where_minute,where1)
            elif type == "minute-n":
                # start_time = "0，{}等分钟）".format(where_minute)
                # cycle = "每小时的第0分钟开始，每隔{}分钟执行一次，直到1小时结束（例如：{}".format(where_minute, start_time)
                cycle = public.lang("Starting from the 0th minute of each hour, execute every {} minutes",where1)
                # current_minute = where_minute
            elif type == "week":
                cycle = public.lang("Execute once every {} on {}:{}",week_days[where1], where_hour, where_minute)
            elif type == "month":
                cycle = public.lang("Execute once on the {}:{} of the {} day of each month",where_hour, where_minute,where1)
            elif type == "second-n":
                cycle = public.lang("Execute every {} seconds", second)
            if sType == "startup_services":
                cycle = public.lang("Start up and execute once")
            return cycle
        except:
            # print(traceback.format_exc())
            pass

    def parse_user_from_sbody(self,sBody):
        if isinstance(sBody, str):
            # 使用正则表达式提取 sudo -u 后面的用户名
            match = re.search(r'^sudo\s+-u\s+(\S+)', sBody)
            return match.group(1) if match else 'root'
        else:
            return 'root'

    def format_cycle(self,item):
        week_str = ''
        if item['time_type'] in ['sweek', 'sday', 'smonth']:
            item['type'] = 'sweek'  # 对于这三种情况，类型都统一处理为 'sweek'
            if item['time_type'] == 'sweek':
                week_str = self.toweek(item['time_set'])  # 假设 self.toweek() 方法存在且能正常工作
            cycle_prefix = "every day" if item['time_type'] == 'sday' else "monthly" + item['time_set'] + "day" if item['time_type'] == 'smonth' else "every" + week_str
            item['type_zh'] = item['special_time'] if item['time_type'] in ['sday', 'smonth'] else week_str
            item['cycle'] = cycle_prefix + item['special_time'] + " execute"
        elif item['sType'] == 'site_restart':
            item['cycle'] = "every day " + item['special_time'] + " execute"

    def toweek(self, days):
        week_days = {
        '1': 'Monday',
        '2': 'Tuesday',
        '3': 'Wednesday',
        '4': 'Thursday',
        '5': 'Friday',
        '6': 'Saturday',
        '7': 'Sunday'
        }
        day_list = str(days).split(',')
        for day in day_list:
            if day not in week_days:
                print('Invalid day:', day)
                return ''
        return ','.join(week_days[day] for day in day_list)
    def _construct_result(self, db_obj, page_data, paged_data):
        if page_data:
            result =  {'page': page_data, 'data': paged_data} 
            if db_obj.ERR_INFO:
                    result['error']=db_obj.ERR_INFO
        else:
            result =paged_data
            if db_obj.ERR_INFO:
                    return []
        return result  

    def get_backup_list(self, args):
        '''
            @name 获取指定备份任务的备份文件列表
            @author hwliang
            @param args<dict> 参数{
                cron_id<int> 任务ID 必填
                p<int> 页码 默认1
                rows<int> 每页显示条数 默认10
                callback<string> jsonp回调函数  默认为空
            }
            @return <dict>{
                page<str> 分页HTML
                data<list> 数据列表
            }
        '''

        p = args.get('p/d', 1)
        rows = args.get('rows/d', 10)
        tojs = args.get('tojs/s', '')
        callback = args.get('callback/s', '') if tojs else tojs

        cron_id = args.get('cron_id/d')
        
        # 首先检查计划任务的类型
        crontab = public.M('crontab').where('id=?', (cron_id,)).find()
        data = []
        if crontab:
            if "Incremental backup of database" in crontab['name']:
                data = self.get_backup_data('mysql_increment_backup', cron_id, p, rows, callback)
            elif crontab.get('sType') == 'site':
                data = self.get_backup_data_all_site(cron_id, p, rows, callback)
            else:
                data = self.get_backup_data('backup', cron_id, p, rows, callback)
        return public.return_message(0,0, data)

    def get_backup_data_all_site(self, cron_id: int, p: int, rows: int, callback: str) -> dict:
        sites_tables = ['backup', 'wordpress_backups']
        count = 0
        site_data = []
        for table in sites_tables:
            temp_count = public.M(table).where('cron_id=?', (cron_id,)).count()
            count += temp_count
            temp_data = public.M(table).where('cron_id=?', (cron_id,)).select()
            if table == 'wordpress_backups':
                temp_data = [
                    {
                        'id': x.get('id'),
                        'type': 0,
                        'name': x.get('bak_file', '').split('|')[-1].split('/')[-1],
                        'pid': x.get('s_id'),
                        'filename': x.get('bak_file', ''),
                        'size': x.get('size', 0),
                        'addtime': time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(x.get('bak_time'))),
                        'ps': 'No',
                        'cron_id': x.get('cron_id'),
                    } for x in temp_data if isinstance(x, dict)
                ]
            site_data.extend(temp_data)

        data = public.get_page(count, p, rows, callback)
        data['data'] = site_data[((p - 1) * rows):((p - 1) * rows + rows)]
        return data

    def get_backup_data(self, table, cron_id, p, rows, callback):
        count = public.M(table).where('cron_id=?', (cron_id,)).count()
        data = public.get_page(count, p, rows, callback)
        data['data'] = public.M(table).where('cron_id=?', (cron_id,)).limit(data['row'], data['shift']).select()
        if table=="mysql_increment_backup":
            # 更新filename字段
            if data['data']:
                cloud_storage_fields = [
                    'localhost', 'ftp', 'alioss', 'txcos', 'qiniu', 
                    'aws_s3', 'upyun', 'obs', 'bos', 'gcloud_storage', 
                    'gdrive', 'msonedrive', 'jdcloud',"tianyiyun","webdav","minio","dogecloud"
                ]
                for i in data['data']:
                    for field in cloud_storage_fields:
                        if i[field]:
                            i['filename'] = i[field]
                            break
        return data
    
    def get_last_exec_time(self, log_file):
        '''
            @name 获取上次执行时间
            @author hwliang
            @param log_file<string> 日志文件路径
            @return format_date
        '''
        exec_date = ''
        # try:
        #     log_body = public.GetNumLines(log_file, 20)
        #     if log_body:
        #         log_arr = log_body.split('\n')
        #         date_list = []
        #         for i in log_arr:
        #             if i.find('★') != -1 and i.find('[') != -1 and i.find(']') != -1:
        #                 date_list.append(i)
        #         if date_list:
        #             exec_date = date_list[-1].split(']')[0].split('[')[1]
        # except:
        #     pass

        # finally:
        if not exec_date:
            exec_date = public.format_date(times=int(os.path.getmtime(log_file)))
        return exec_date
    
    # 清理日志
    def __clean_log(self):
        try:
            log_file = '/www/server/cron'
            if not os.path.exists(log_file): return False
            for f in os.listdir(log_file):
                if f[-4:] != '.log': continue
                filename = log_file + '/' + f
                if os.path.getsize(filename) < 1048576 / 2: continue
                tmp = public.GetNumLines(filename, 100)
                public.writeFile(filename, tmp)
        except:
            pass

    # 转换大写星期
    def toWeek(self, num):
        wheres = {
                0   :   public.lang("Sunday"),
                1   :   public.lang("Monday"),
                2   :   public.lang("Tuesday"),
                3   :   public.lang("Wednesday"),
                4   :   public.lang("Thursday"),
                5   :   public.lang("Friday"),
                6   :   public.lang("Saturday")
        }
        try:
            return wheres[num]
        except:
            return ''

    # 检查环境
    def checkBackup(self):
        if cache.get('check_backup'): return None

        # 检查备份表是否正确
        if not public.M('sqlite_master').db('backup').where('type=? AND name=? AND sql LIKE ?',
                                               ('table', 'backup', '%cron_id%')).count():
            public.M('backup').execute("ALTER TABLE 'backup' ADD 'cron_id' INTEGER DEFAULT 0", ())

        # 检查备份脚本是否存在
        filePath = public.GetConfigValue('setup_path') + '/panel/script/backup'
        if not os.path.exists(filePath):
            public.downloadFile(public.GetConfigValue('home') + '/linux/backup.sh', filePath)
        # 检查日志切割脚本是否存在
        filePath = public.GetConfigValue('setup_path') + '/panel/script/logsBackup'
        if not os.path.exists(filePath):
            public.downloadFile(public.GetConfigValue('home') + '/linux/logsBackup.py', filePath)
        # 检查计划任务服务状态
        import system
        sm = system.system()
        if os.path.exists('/etc/init.d/crond'):
            if not public.process_exists('crond'): public.ExecShell('/etc/init.d/crond start')
        elif os.path.exists('/etc/init.d/cron'):
            if not public.process_exists('cron'): public.ExecShell('/etc/init.d/cron start')
        elif os.path.exists('/usr/lib/systemd/system/crond.service'):
            if not public.process_exists('crond'): public.ExecShell('systemctl start crond')
        cache.set('check_backup', True, 3600)

    # 设置计划任务状态
    def set_cron_status(self, get):
        id = get['id']
        cronInfo = public.M('crontab').where('id=?', (id,)).field(self.field).find()
        if not cronInfo:
            return public.return_message(-1,0, public.lang("No data was found for the corresponding scheduled task. Please refresh the page to check if the scheduled task exists!"))

        # 处理一次性定时任务
        if cronInfo['type'] == 'once':
            cron_time = datetime.strptime(cronInfo['where1'], "%Y-%m-%d %H:%M:%S")
            if cron_time <= datetime.now():
                return public.return_message(-1, 0, public.lang(f'The execution time has passed. Please reconfigure the task! '))

            if get.get('if_stop') == 'true':
                public.ExecShell(f'systemctl stop {cronInfo['echo'][:-3] + '.timer'}')
            else:
                public.ExecShell(f'systemctl start {cronInfo['echo'][:-3] + '.timer'}')

        status_msg = ['Stop', 'Start']
        status = 1
        if cronInfo['status'] == status:
            status = 0
            if not self.remove_for_crond(cronInfo['echo']):
                return public.return_message(-1,0, public.lang('Unable to write to file, please check if system hardening is enabled!'))
        else:
            cronInfo['status'] = 1
            if not self.sync_to_crond(cronInfo):
                return public.return_message(-1,0, public.lang('Unable to write to file, please check if system hardening is enabled!'))

        public.M('crontab').where('id=?', (id,)).setField('status', status)
        public.WriteLog(public.lang('crontab tasks'), public.lang('Modify the status of the scheduled task ['+cronInfo ['name']+'] to ['+status_msg[status]+']'))
        cronPath = '/www/server/cron'
        cronName = cronInfo['echo']
        if_stop = get.get('if_stop', '')
        if if_stop:
            self.stop_cron_task(cronPath, cronName, if_stop)
        return public.return_message(0,0, public.lang('Setup successfully!'))

    def set_cron_status_all(self, get):
        """
        批量设置计划任务状态
        :param get: type:stop, start, del, exec    id_list:[1,2,3]
        :return:
        """
        if not hasattr(get, 'type'):
            return public.return_message(-1,0, public.lang('parameter error'))
        if not hasattr(get, 'id_list'):
            return public.return_message(-1,0, public.lang('parameter error'))
        # 停止或开启
        if get.type not in ['stop', 'start', 'del', 'exec']:
            return public.return_message(-1,0, public.lang('parameter error'))
        if get.type == 'stop' or get.type == 'start':
            id_list = json.loads(get['id_list'])
            status = 1 if get.type == 'start' else 0
            status_msg = ['Stop', 'Start']
            data = []
            for id in id_list:
                try:
                    name = public.M('crontab').where('id=?', (id,)).field('name').find().get('name', '')
                    cronInfo = public.M('crontab').where('id=?', (id,)).field(self.field).find()

                    # 补充定时任务
                    if cronInfo['type'] == 'once':
                        cron_time = datetime.strptime(cronInfo['where1'], "%Y-%m-%d %H:%M:%S")
                        if cron_time <= datetime.now(): # 跳过
                            continue

                        if get.type == 'stop':
                            public.ExecShell(f'systemctl stop {cronInfo['echo'][:-3] + '.timer'}')
                        else:
                            public.ExecShell(f'systemctl start {cronInfo['echo'][:-3] + '.timer'}')

                    if not cronInfo:
                        data.append({id: public.lang('The scheduled task with this ID does not exist'), 'status': False})
                        continue
                    if status == 1:
                        if not self.sync_to_crond(cronInfo):
                            return public.return_message(-1,0, public.lang('Writing scheduled task failed, please check if the disk is writable or if system hardening is enabled!'))
                    else:
                        if not self.remove_for_crond(cronInfo['echo']):
                            return public.return_message(-1,0, public.lang('Writing scheduled task failed, please check if the disk is writable or if system hardening is enabled!'))
                    public.M('crontab').where('id=?', (id,)).setField('status', status)
                    cronPath = '/www/server/cron'
                    cronName = cronInfo['echo']
                    if_stop = get.if_stop
                    self.stop_cron_task(cronPath, cronName, if_stop)
                except:
                    data.append({name: public.lang("{} Setting failed",(status_msg[status])), 'status': False})
                else:
                    data.append({name: ("{} Setup successfully!".format(status_msg[status])), 'status': True})
            return public.return_message(0,0,data)
        # 删除
        if get.type == 'del':
            id_list = json.loads(get['id_list'])
            data = []
            for id in id_list:
                try:
                    name = public.M('crontab').where('id=?', (id,)).field('name').find().get('name', '')
                    if not name:
                        data.append({id: public.lang('The scheduled task with this ID does not exist'), 'status': False})
                        continue
                    get = public.to_dict_obj({'id': id})
                    res = self.DelCrontab(get)
                except:
                    pass
                data.append({name: public.lang("Delete {}",("succeeded" if res['status']==0 else "fail")), 'status': res['status']})
            return public.return_message(0,0,data)
        # 执行
        if get.type == 'exec':
            id_list = json.loads(get['id_list'])
            data = []
            for id in id_list:
                try:
                    name = public.M('crontab').where('id=?', (id,)).field('name').find().get('name', '')
                    if not name:
                        data.append({id: public.lang('The scheduled task with this ID does not exist'), 'status': False})
                        continue
                    get = public.to_dict_obj({'id': id})
                    res = self.StartTask(get)
                except:
                    pass
                data.append({name:public.lang( "Execution {}",("succeeded" if res['status']==0 else "fail")), 'status': res['status']})
            return public.return_message(0,0,data)


    # 修改计划任务
    def modify_crond(self, get):
        try:
            if re.search('<.*?>', get['name']):
                return public.return_message(-1,0, public.lang("The category name cannot contain HTML statements"))
            if get['sType'] == 'toShell':
                sBody = get['sBody']
                get['sBody'] = sBody.replace('\r\n', '\n')
                # 如果user有值，则修改sBody
                user = get.get('user', 'root')
                if user :
                    get['sBody'] = "sudo -u {0} bash -c '{1}'".format(user, get['sBody'])
                if get.get('version',''):
                    version = get['version'].replace(".", "")
                    get['sBody'] = get['sBody'].replace("${1/./}", version)
            if len(get['name']) < 1:
                return public.return_message(-1,0, public.lang('CRONTAB_TASKNAME_EMPTY'))
            id = get['id']
            cronInfo = public.M('crontab').where('id=?', (id,)).field(self.field).find()

            try:
                # 处理定时任务
                if cronInfo['type'] == 'once' and get['type'] == 'once':
                    timer_path = '/etc/systemd/system/' + cronInfo['echo'][:-3] + '.timer'
                    if not os.path.exists(timer_path):
                        return public.return_message(-1,0, public.lang('The timer file does not exist. Try deleting this task and then recreate it!'))

                    try:
                        execute_datetime = datetime.strptime(get['where1'], "%Y-%m-%d %H:%M:%S")
                    except ValueError:
                        raise ValueError(public.lang(f'Execute time format error: {get['where1']}, required: YYYY-MM-DD HH:MM:SS'))

                    timer_content = f"""[Unit]
Description=Timer for once task: {cronInfo['echo'][:-3] + '.timer'}

[Timer]
OnCalendar={execute_datetime} 
Persistent=false

[Install]
WantedBy=timers.target
"""
                    public.writeFile(timer_path, timer_content)
                    # 重启配置
                    public.ExecShell('systemctl daemon-reload')
                    public.ExecShell(f'systemctl restart {cronInfo['echo'][:-3] + '.timer'}')
                    public.ExecShell(f'systemctl reset-failed {cronInfo['echo'][:-3] + '.timer'}')
            except Exception as e:
                return public.return_message(-1,0,str(e))


            if get['type']=='sweek':

            # if get['type']=='sweek':
                self.modify_values(cronInfo['echo'],get['time_type'],get['special_time'],get['time_set']) 
                get['type']='minute-n'

            if get['type']=="second-n":
                get['type']="minute-n"
                get['where1']= "1"
                get['hour']=1
                get['minute']=1
                get['flock']=0
            cuonConfig, get, name = self.GetCrondCycle(get)            

            projectlog = self.modify_project_log_split(cronInfo, get)
            if projectlog.modify():
                return public.return_message(0,0, projectlog.msg)
            if not get['where1']: get['where1'] = get['week']
            del (cronInfo['id'])
            del (cronInfo['addtime'])
            cronInfo['name'] = get['name']
            if cronInfo['sType'] == "sync_time": cronInfo['sName'] = get['sName']
            cronInfo['type'] = get['type']
            cronInfo['where1'] = get['where1']
            cronInfo['where_hour'] = get['hour']
            cronInfo['where_minute'] = get['minute']
            cronInfo['save'] = get['save']
            cronInfo['backupTo'] = get['backupTo']
            cronInfo['sBody'] = get['sBody']
            cronInfo['urladdress'] = get['urladdress']
            cronInfo['time_type']=get.get('time_type','')
            cronInfo['special_time']=get.get('special_time','')
            cronInfo['time_set']=get.get('time_set','')
            cronInfo['second']=get.get('second','')
            if get.get('db_backup_path')=="/www/backup":
                db_backup_path=""
            else:
                db_backup_path=get.get('db_backup_path','')
            columns = 'status,type,where1,where_hour,where_minute,save,backupTo,sName,sBody,urladdress,db_type,split_type,split_value,rname,post_param,flock,time_set,backup_mode,db_backup_path,time_type,special_time,user_agent,version,table_list,second'
            values = (get['type'], get['where1'], get['hour'],
                      get['minute'], get['save'], get['backupTo'], cronInfo['sName'], get['sBody']
                      , get['urladdress'], get.get("db_type"), get.get("split_type"), get.get("split_value"), get['name'], get.get('post_param', ''), get.get('flock', 0),get.get('time_set',''),get.get('backup_mode', ''),db_backup_path,get.get('time_type',''),get.get('special_time',''),get.get('user_agent',''),get.get('version',''),get.get('table_list',''),get.get('second',''))
            if 'save_local' in get:
                columns += ",save_local, notice, notice_channel"
                values = (1,get['type'], get['where1'], get['hour'],
                          get['minute'], get['save'], get['backupTo'], cronInfo['sName'], get['sBody'],
                          get['urladdress'], get.get("db_type"), get.get("split_type"), get.get("split_value"), get['name'], get.get('post_param', ''), get.get('flock', 0),get.get('time_set',''),get.get('backup_mode', ''),db_backup_path,get.get('time_type',''),get.get('special_time',''),get.get('user_agent',''),get.get('version',''),get.get('table_list',''),get.get('second',''),
                          get['save_local'], get["notice"],get["notice_channel"])
            if cronInfo['status'] != 0 and cronInfo['type'] != 'once':
                if not self.remove_for_crond(cronInfo['echo']):
                    return public.return_message(-1,0, public.lang('Writing scheduled task failed, please check if the disk is writable or if system hardening is enabled!'))
                # if cronInfo['status'] == 0: return public.returnMsg(False, '当前任务处于停止状态,请开启任务后再修改!')
                if not self.sync_to_crond(cronInfo):
                    return public.return_message(-1,0, public.lang('Writing scheduled task failed, please check if the disk is writable or if system hardening is enabled!'))
            public.M('crontab').where('id=?', (id,)).save(columns, values)
            public.WriteLog(public.lang('crontab tasks'), public.lang('Successfully modified plan task ['+cronInfo ['name']+']'))
            return public.return_message(0,0, public.lang('Modified successfully'))
        except:
             return public.return_message(-1,0,traceback.format_exc())



    # 获取指定任务数据
    def get_crond_find(self, get):
        id = int(get.id)
        data = public.M('crontab').where('id=?', (id,)).field(self.field).find()
        return public.return_message(0,0,data)

    # 同步到crond
    def sync_to_crond(self, cronInfo):
        if not 'status' in cronInfo: return False
        if 'where_hour' in cronInfo:
            cronInfo['hour'] = cronInfo['where_hour']
            cronInfo['minute'] = cronInfo['where_minute']
            cronInfo['week'] = cronInfo['where1']
        cuonConfig, cronInfo, name = self.GetCrondCycle(cronInfo)
        cronPath = public.GetConfigValue('setup_path') + '/cron'
        cronName = self.GetShell(cronInfo)
        if type(cronName) == dict: return cronName
        cuonConfig += ' ' + cronPath + '/' + cronName + ' >> ' + cronPath + '/' + cronName + '.log 2>&1'

        # 移除flock模式，与部分系统不兼容，会导致任务无法执行
        # if int(cronInfo.get('flock', 0)) == 1:
        #     flock_name = cronPath + '/' + cronName + '.lock'
        #     public.writeFile(flock_name, '')
        #     os.system('chmod 777 {}'.format(flock_name))
        #     cuonConfig += ' flock -xn ' + cronPath + '/' + cronName + '.lock' + ' -c ' + cronPath + '/' + cronName + ' >> ' + cronPath + '/' + cronName + '.log 2>&1'
        # else:
        #     cuonConfig += ' ' + cronPath + '/' + cronName + ' >> ' + cronPath + '/' + cronName + '.log 2>&1'

        wRes = self.WriteShell(cuonConfig)
        if wRes['status'] != 0: return False
        self.CrondReload()
        return True

    def ensure_execute_commands_script(self,get):
        cronName = public.md5(public.md5(str(time.time()) + '_bt'))
        script_path = '/etc/init.d/execute_commands'
        systemd_service_path = '/etc/systemd/system/execute_commands.service'

        # For systemd systems
        if os.path.exists('/bin/systemctl') or os.path.exists('/usr/bin/systemctl'):
            if not os.path.exists(systemd_service_path):
                with open(systemd_service_path, 'w') as service_file:
                    service_content = """[Unit]
    Description=Custom Service to execute commands at startup
    After=network.target

    [Service]
    Type=simple
    ExecStart=btpython /www/server/panel/script/execute_commands.py
    Restart=on-failure

    [Install]
    WantedBy=multi-user.target
    """
                    service_file.write(service_content)

                os.system('systemctl daemon-reload')
                os.system('systemctl start execute_commands.service')
                os.system('systemctl enable execute_commands.service')
                print("Systemd service created and enabled successfully.")

        # For SysVinit systems
        else:
            if not os.path.exists(script_path):
                with open(script_path, 'w') as script_file:
                    script_content = """#! /bin/sh
    # chkconfig: 2345 55 25

    ### BEGIN INIT INFO
    # Provides:          custom_service
    # Required-Start:    $all
    # Required-Stop:     $all
    # Default-Start:     2 3 4 5
    # Default-Stop:      0 1 6
    # Short-Description: Custom Service
    # Description:       Executes user-defined shell commands at startup
    ### END INIT INFO

    # Author:   Your Name
    # website:  Your Website

    PATH=/usr/local/sbin:/usr/local/bin:/sbin:/bin:/usr/sbin:/usr/bin

    case "$1" in
        start)
            echo -n "Starting custom_service... "
            if [ -f /var/run/custom_service.pid ];then
                mPID=$(cat /var/run/custom_service.pid)
                isStart=`ps ax | awk '{ print $1 }' | grep -e "^${mPID}$"`
                if [ "$isStart" != "" ];then
                    echo "custom_service (pid $mPID) already running."
                    exit 1
                fi
            fi
            nohup btpython /www/server/panel/script/execute_commands.py > /dev/null 2>&1 &
            pid=$!
            echo $pid > /var/run/custom_service.pid
            echo " done"
            ;;
        stop)
            echo "Custom Service does not support stop operation."
            ;;
        status)
            if [ -f /var/run/custom_service.pid ];then
                mPID=`cat /var/run/custom_service.pid`
                isStart=`ps ax | awk '{ print $1 }' | grep -e "^${mPID}$"`
                if [ "$isStart" != '' ];then
                    echo "custom_service is running with PID $mPID."
                    exit 0
                else
                    echo "custom_service is stopped"
                    exit 0
                fi
            else
                echo "custom_service is stopped"
                exit 0
            fi
            ;;
        *)
            echo "Usage: $0 {start|status}"
            exit 1
            ;;
    esac

    exit 0"""
                    script_file.write(script_content)
                    os.chmod(script_path, 0o755)  # Set execute permission
                print("Init script created successfully.")
                
                if os.path.exists('/usr/sbin/update-rc.d'):
                    os.system('update-rc.d -f execute_commands defaults')
                print("Service configured for SysVinit successfully.")

        if get.get('db_backup_path') == "/www/backup":
            db_backup_path = ""
        else:
            db_backup_path = get.get('db_backup_path', '')
        columns = 'name,type,where1,where_hour,where_minute,echo,addtime,\
                status,save,backupTo,sType,sName,sBody,urladdress,db_type,split_type,split_value,keyword,post_param,flock,time_set,backup_mode,db_backup_path,time_type,special_time,user_agent,version,table_list'
        values = (public.xssencode2(get['name']), get['type'], get['where1'], get['hour'],
                  get['minute'], cronName, time.strftime('%Y-%m-%d %X', time.localtime()),
                  1, get['save'], get['backupTo'], get['sType'], get['sName'], get['sBody'],
                  get['urladdress'], get.get("db_type"), get.get("split_type"), get.get("split_value"), get.get('keyword', ''), get.get('post_param', ''), get.get('flock', 0), get.get('time_set', ''),
                  get.get('backup_mode', ''), db_backup_path, get.get('time_type', ''), get.get('special_time', ''), get.get('user_agent', ''), get.get('verison', ''), get.get('table_list', ''))
        if "save_local" in get:
            columns += ",save_local,notice,notice_channel"
            values = (public.xssencode2(get['name']), get['type'], get['where1'], get['hour'],
                      get['minute'], cronName, time.strftime('%Y-%m-%d %X', time.localtime()),
                      1, get['save'], get['backupTo'], get['sType'], get['sName'], get['sBody'],
                      get['urladdress'], get.get("db_type"), get.get("split_type"), get.get("split_value"), get.get('keyword', ''), get.get('post_param', ''), get.get('flock', 0),
                      get.get('time_set', ''), get.get('backup_mode', ''), db_backup_path, get.get('time_type', ''), get.get('special_time', ''), get.get('user_agent', ''), get.get('verison', ''),
                      get.get('table_list', ''),
                      get["save_local"], get['notice'], get['notice_channel'])
        addData = public.M('crontab').add(columns, values)
        public.add_security_logs('crontab tasks', 'Add plan task ['+get['name']+'] successful'+str(values))
        if type(addData) == str:
            return public.returnMsg(False, addData)
        public.WriteLog(public.lang('crontab tasks'), public.lang('Successfully added scheduled task ['+get['name']+']'))
        if addData > 0:
            result = public.returnMsg(True, public.lang('ADD_SUCCESS'))
            result['id'] = addData
            return result
        return public.returnMsg(False, public.lang('Failed to add'))

    # 添加计划任务
    def AddCrontab(self, get):
        try:
            if get['type']=="second-n":
                get['type']="minute-n"
                get['where1']= "1"
                get['hour']=1
                get['minute']=1
                get['flock']=0
            if len(get['name']) < 1:
                return public.return_message(-1,0, public.lang('CRONTAB_TASKNAME_EMPTY'))
            if get['sType'] == 'toShell':
                get['sBody'] = get['sBody'].replace('\r\n', '\n')

            # 如果user有值，则修改sBody
            user = get.get('user', 'root')
            if user:
                get['sBody'] = "sudo -u {0} bash -c '{1}'".format(user, get['sBody'])

            # 如果get中有version键，就替换sBody中的版本号占位符
                if get.get('version',''):
                    version = get['version'].replace(".", "")
                    get['sBody'] = get['sBody'].replace("${1/./}", version)
                    print(get['sBody'])

            # 新增定时任务：在指定时间执行一次
            if get['type'] == 'once' and get['sType'] == 'toShell':
                return self.add_once_crontab(get)

            if get['sType'] == 'startup_services':
                return self.ensure_execute_commands_script(get)  # 检查并创建脚本
                
            if get['type']=='sweek':
               get['type']='minute-n'
            cuonConfig, get, name = self.GetCrondCycle(get)
            cronPath = public.GetConfigValue('setup_path') + '/cron'
            cronName = self.GetShell(get)

            if type(cronName) == dict: return cronName
            # 移除flock模式，与部分系统不兼容，会导致任务无法执行
            # if int(get.get('flock', 0)) == 1:
            #     flock_name = cronPath + '/' + cronName + '.lock'
            #     public.writeFile(flock_name, '')
            #     os.system('chmod 777 {}'.format(flock_name))
            #     cuonConfig += ' flock -xn ' + cronPath + '/' + cronName + '.lock' + ' -c ' + cronPath + '/' + cronName + ' >> ' + cronPath + '/' + cronName + '.log 2>&1'
            # else:
            cuonConfig += ' ' + cronPath + '/' + cronName + ' >> ' + cronPath + '/' + cronName + '.log 2>&1'
            wRes = self.WriteShell(cuonConfig)
            if wRes['status'] != 0: return wRes
            self.CrondReload()
            if get.get('db_backup_path')=="/www/backup":
                db_backup_path=""
            else:
                db_backup_path=get.get('db_backup_path','')
            columns = 'name,type,where1,where_hour,where_minute,echo,addtime,\
                    status,save,backupTo,sType,sName,sBody,urladdress,db_type,split_type,split_value,keyword,post_param,flock,time_set,backup_mode,db_backup_path,time_type,special_time,user_agent,version,table_list,result,second'
            values = (public.xssencode2(get['name']), get['type'], get['where1'], get['hour'],
                    get['minute'], cronName, time.strftime('%Y-%m-%d %X', time.localtime()),
                    1, get['save'], get['backupTo'], get['sType'], get['sName'], get['sBody'],
                    get['urladdress'], get.get("db_type"), get.get("split_type"), get.get("split_value"), get.get('keyword', ''), get.get('post_param', ''), get.get('flock', 0),get.get('time_set', ''),get.get('backup_mode',''),db_backup_path,get.get('time_type',''),get.get('special_time',''),get.get('user_agent',''),get.get('verison',''),get.get('table_list',''),get.get('result',1),get.get('second',''))
            if "save_local" in get:
                columns += ",save_local,notice,notice_channel"
                values = (public.xssencode2(get['name']), get['type'], get['where1'], get['hour'],
                        get['minute'], cronName, time.strftime('%Y-%m-%d %X', time.localtime()),
                        1, get['save'], get['backupTo'], get['sType'], get['sName'], get['sBody'],
                        get['urladdress'], get.get("db_type"), get.get("split_type"), get.get("split_value"), get.get('keyword', ''), get.get('post_param', ''), get.get('flock', 0),get.get('time_set', ''),get.get('backup_mode', ''),db_backup_path,get.get('time_type',''),get.get('special_time',''),get.get('user_agent',''),get.get('verison',''),get.get('table_list',''),get.get('result',1),get.get('second',''),
                        get["save_local"], get['notice'], get['notice_channel'])
            addData = public.M('crontab').add(columns, values)
            public.add_security_logs('crontab tasks', 'Add plan task ['+get['name']+'] successful'+str(values))
            if type(addData) == str:
                return public.return_message(-1,0, addData)
            public.WriteLog(public.lang('crontab tasks'), public.lang('Successfully added scheduled task ['+get['name']+']'))
            if addData > 0:
                result = public.return_message(0,0, public.lang('ADD_SUCCESS'))
                result['message']['id'] = addData
                return result
            return public.return_message(-1,0, public.lang('Failed to add'))
        except Exception as e:
            return public.return_message(-1,0, public.lang(str(e)))

    # 添加一次性定时任务
    def add_once_crontab(self, get):
        try:
            # 执行时间校验
            execute_time_str = get.get('where1', '').strip()
            if not execute_time_str:
                raise ValueError(public.lang('Missing required parameter: execute_time (format: YYYY-MM-DD HH:MM:SS)'))

            if not get['sBody'].strip():
                raise ValueError(public.lang('CRONTAB_TASKBODY_EMPTY'))

            try:
                execute_datetime = datetime.strptime(execute_time_str, "%Y-%m-%d %H:%M:%S")
            except ValueError:
                raise ValueError(public.lang(f'Execute time format error: {execute_time_str}, required: YYYY-MM-DD HH:MM:SS'))

            if execute_datetime <= datetime.now():
                raise ValueError(public.lang(f'Execute time must be in the future'))

            # 生成脚本文件
            cronPath = public.GetConfigValue('setup_path') + '/cron'
            os.makedirs(cronPath, mode=0o755, exist_ok=True)
            cronName = f"once_{int(time.time())}.sh"
            scriptPath = os.path.join(cronPath, cronName)
            logPath = os.path.join(cronPath, f"{cronName}.log")
            script_content = f"""#!/bin/bash
    {get['sBody']}"""

            # 写入脚本并授权
            public.writeFile(scriptPath, script_content)
            os.chmod(scriptPath, 0o755)

             # 使用systemd-timer
            """
                默认执行用户：root
                执行类型：一次性 oneshot
                执行超时：一小时 3600
            """
            systemd_task_name = cronName[:-3]
            service_path = f"/etc/systemd/system/{systemd_task_name}.service"  # 服务文件
            timer_path = f"/etc/systemd/system/{systemd_task_name}.timer"  # 定时器文件

            # 生成 systemd 服务文件
            service_content = f"""[Unit]
Description=Once crontab task: {public.xssencode2(systemd_task_name)}
After=network.target

[Service]
Type=oneshot
User=root

ExecStart=/bin/bash -c '{scriptPath} >> {logPath} 2>&1'
TimeoutSec=3600
            """

            # 生成 systemd 定时器文件
            timer_content = f"""[Unit]
Description=Timer for once task: {public.xssencode2(systemd_task_name)}

[Timer]
OnCalendar={execute_time_str} 
Persistent=false

[Install]
WantedBy=timers.target
            """

            # 写入 systemd 配置文件
            public.writeFile(service_path, service_content)
            public.writeFile(timer_path, timer_content)

            # 设置 systemd 配置文件权限（符合系统要求：644）
            os.chmod(service_path, 0o644)
            os.chmod(timer_path, 0o644)

            # 重新加载 systemd 配置
            reload_result = public.ExecShell('systemctl daemon-reload')
            if reload_result[1] != '':
                raise ValueError(f"systemd reload failed: {reload_result[1]}")

            # 启动定时器
            start_result = public.ExecShell(f'systemctl start {systemd_task_name}.timer')
            if start_result[1] != '':
                raise ValueError(f"Timer start failed: {start_result[1]}")
            # 数据库记录
            db_backup_path = "" if get.get('db_backup_path') == "/www/backup" else get.get('db_backup_path', '')
            columns = 'name,type,where1,where_hour,where_minute,echo,\
                            status,save,backupTo,sType,sName,sBody,urladdress,db_type,split_type,split_value,keyword,post_param,flock,time_set,backup_mode,db_backup_path,time_type,special_time,user_agent,version,table_list,result,second'
            values = (
                public.xssencode2(get['name']), 'once', execute_datetime, 0, 0, cronName,
                1, get.get('save', 0), get.get('backupTo', ''), get['sType'], get.get('sName', ''), get['sBody'],
                get.get('urladdress', ''), get.get("db_type"), get.get("split_type"), get.get("split_value"),
                get.get('keyword', ''), get.get('post_param', ''), get.get('flock', 0), '',
                get.get('backup_mode', ''), db_backup_path, '', '', get.get('user_agent', ''),
                get.get('version', ''), get.get('table_list', ''), get.get('result', 1), ''
            )

            addData = public.M('crontab').add(columns, values)
            public.add_security_logs('crontab tasks',
                                     f'Add once task [{get["name"]}] success, execute time: {execute_time_str}')

            if isinstance(addData, str):
                raise ValueError(addData)
            public.WriteLog(public.lang('crontab tasks'), public.lang(f'Successfully added once task [{get["name"]}]'))
            if addData > 0:
                result = public.return_message(0, 0, public.lang('ADD_SUCCESS'))
                result['message']['id'] = addData
                result['message']['execute_time'] = execute_time_str
                return result
            raise ValueError(public.lang('Failed to add once task'))
        except Exception as e:
            try:
                if 'scriptPath' in locals() and os.path.exists(scriptPath):
                    os.remove(scriptPath)
                if 'logPath' in locals() and os.path.exists(logPath):
                    os.remove(logPath)
                if 'service_path' in locals() and os.path.exists(service_path):
                    os.remove(service_path)
                if 'timer_path' in locals() and os.path.exists(timer_path):
                    os.remove(timer_path)
            except:
                pass
            raise ValueError(e)

    # 构造周期
    def GetCrondCycle(self, params):
        cuonConfig = ""
        name = ""
        if params['type'] == "day":
            cuonConfig = self.GetDay(params)
            name = public.getMsg('CRONTAB_TODAY')
        elif params['type'] == "day-n":
            cuonConfig = self.GetDay_N(params)
            name = public.getMsg('CRONTAB_N_TODAY', (params['where1'],))
        elif params['type'] == "hour":
            cuonConfig = self.GetHour(params)
            name = public.getMsg('CRONTAB_HOUR')
        elif params['type'] == "hour-n":
            cuonConfig = self.GetHour_N(params)
            name = public.getMsg('CRONTAB_HOUR')
        elif params['type'] == "minute-n":
            cuonConfig = self.Minute_N(params)
        elif params['type'] == "week":
            params['where1'] = params['week']
            cuonConfig = self.Week(params)
        elif params['type'] == "month":
            cuonConfig = self.Month(params)
        return cuonConfig, params, name

    # 取任务构造Day
    def GetDay(self, param):
        cuonConfig = "{0} {1} * * * ".format(param['minute'], param['hour'])
        return cuonConfig

    # 取任务构造Day_n
    def GetDay_N(self, param):
        cuonConfig = "{0} {1} */{2} * * ".format(param['minute'], param['hour'], param['where1'])
        return cuonConfig

    # 取任务构造Hour
    def GetHour(self, param):
        cuonConfig = "{0} * * * * ".format(param['minute'])
        return cuonConfig

    # 取任务构造Hour-N
    def GetHour_N(self, param):
        cuonConfig = "{0} */{1} * * * ".format(param['minute'], param['where1'])
        return cuonConfig

    # 取任务构造Minute-N
    def Minute_N(self, param):
        cuonConfig = "*/{0} * * * * ".format(param['where1'])
        return cuonConfig

    # 取任务构造week
    def Week(self, param):
        cuonConfig = "{0} {1} * * {2}".format(param['minute'], param['hour'], param['week'])
        return cuonConfig

    # 取任务构造Month
    def Month(self, param):
        cuonConfig = "{0} {1} {2} * * ".format(param['minute'], param['hour'], param['where1'])
        return cuonConfig

    # 取数据列表
    def GetDataList(self, get):
        data = {}
        if get['type'] == 'databases':
            data['data'] = public.M(get['type']).where("type=?", "MySQL").field('name,ps').select()
        else:
            data['data'] = public.M(get['type']).field('name,ps').select()
        for i in data['data']:
            if 'ps' in i:
                try:
                    if i['ps'] is None: continue
                    i['ps'] = public.xsssec(i['ps'])  # 防止数据库为空时，xss防御报错  2020-11-25
                except:
                    pass
        data['orderOpt'] = []
        import json
        tmp = public.readFile('data/libList.conf')
        if not tmp: return data
        libs = json.loads(tmp)
        for lib in libs:
            if not 'opt' in lib: continue
            filename = 'plugin/{}'.format(lib['opt'])
            if not os.path.exists(filename): continue
            tmp = {}
            tmp['name'] = lib['name']
            tmp['value'] = lib['opt']
            data['orderOpt'].append(tmp)
        return public.return_message(0,0,data)

    # 取任务日志
    def GetLogs(self, get):
        id = get['id']
        sType = public.M('crontab').where("id=?", (id,)).getField('sType')
        if sType == 'webshell':
            try:
                logs = self.GetWebShellLogs(get)
                return logs
            except:
                pass
        echo = public.M('crontab').where("id=?", (id,)).field('echo').find()
        if not echo:
            return public.return_message(-1,0, public.lang("No data was found for the corresponding scheduled task. Please refresh the page to check if the scheduled task exists!"))
        logFile = public.GetConfigValue('setup_path') + '/cron/' + echo['echo'] + '.log'
        if not os.path.exists(logFile): return public.return_message(0,0, public.lang('Task logs are empty!'))
        log = public.GetNumLines(logFile, 2000)
        return public.return_message(0,0, public.xsssec(log))

    # 清理任务日志
    def DelLogs(self, get):
        try:
            id = get['id']
            echo = public.M('crontab').where("id=?", (id,)).getField('echo')
            logFile = public.GetConfigValue('setup_path') + '/cron/' + echo + '.log'
            if not os.path.exists(logFile): return public.return_message(0,0, public.lang('Task logs emptied!'))
            os.remove(logFile)
            return public.return_message(0,0, public.lang('Task logs emptied!'))
        except:
            return public.return_message(-1,0, public.lang('Failed to empty task logs!'))

    # 删除计划任务
    def DelCrontab(self, get):
        try:
            id = get['id']
            # 尝试删除数据库增量备份表中的数据
            public.M("mysql_increment_settings").where("cron_id=?", (id)).delete()
            find = public.M('crontab').where("id=?", (id,)).field('name,echo,type').find()
            if not find: return public.return_message(-1,0, public.lang('The specified task does not exist!'))
            if not self.remove_for_crond(find['echo']): return public.return_message(-1,0, public.lang('Unable to write to file, please check if system hardening is enabled!'))

            # 删除一次性定时任务
            if find['type'] == 'once':
                try:
                    # 删除任务配置文件
                    timer = '/etc/systemd/system/' + find['echo'][:-3] + '.timer'
                    service = '/etc/systemd/system/' + find['echo'][:-3] + '.service'
                    if os.path.exists(timer):
                        public.ExecShell(f'rm -rf {timer}')
                    if os.path.exists(service):
                        public.ExecShell(f'rm -rf {service}')

                    # 清理并重载任务
                    public.ExecShell(f'systemctl stop {find['echo'][:-3] + '.timer'}')
                    public.ExecShell(f'systemctl daemon-reload')
                    public.ExecShell(f'systemctl reset-failed {find['echo'][:-3] + '.timer'}')
                except:
                    pass

            cronPath = public.GetConfigValue('setup_path') + '/cron'
            sfile = cronPath + '/' + find['echo']
            if os.path.exists(sfile): os.remove(sfile)
            sfile = cronPath + '/' + find['echo'] + '.log'
            if os.path.exists(sfile): os.remove(sfile)

            public.M('crontab').where("id=?", (id,)).delete()
            public.add_security_logs(public.lang("Delete scheduled tasks"), public.lang("Delete scheduled tasks: {}", find['name']))
            public.WriteLog('TYPE_CRON', 'CRONTAB_DEL', (find['name'],))
            return public.return_message(0,0, public.lang('DEL_SUCCESS'))
        except:
            return public.return_message(-1,0, public.lang('DEL_ERROR'))

    # 从crond删除
    def remove_for_crond(self, echo):
        file = self.get_cron_file()
        if not os.path.exists(file):
            return False
        conf = public.readFile(file)
        if not conf: return True
        if conf.find(str(echo)) == -1: return True
        rep = ".+" + str(echo) + ".+\n"
        conf = re.sub(rep, "", conf)
        try:
            if not public.writeFile(file, conf): return False
        except:
            return False
        self.CrondReload()
        return True

    # 取执行脚本
    def GetShell(self, param):
        type = param['sType']
        if not 'echo' in param:
            cronName = public.md5(public.md5(str(time.time()) + '_bt'))
        else:
            cronName = param['echo']
        if type == 'toFile':
            shell = param.sFile
        else:
            cronPath = '/www/server/cron'  
            cronFile = '{}/{}.pl'.format(cronPath,cronName)
            head = "#!/bin/bash\nPATH=/bin:/sbin:/usr/bin:/usr/sbin:/usr/local/bin:/usr/local/sbin:~/bin\nexport PATH\n"
            head += "echo $$ > " + cronFile + "\n"  # 将PID保存到文件中
            second = param.get('second', "")
            time_type=param['type']
            if second:
                time_type="second-n"
                head += 'if [[ $1 != "start" ]]; then\n'
                head += ' btpython /www/server/panel/script/second_task.py {} {} \n'.format(second,cronName)
                head += ' exit 0\n'
                head += 'fi\n'
            public.ExecShell("chmod +x /www/server/panel/script/modify_second_cron.sh")
            public.ExecShell("nohup /www/server/panel/script/modify_second_cron.sh {} {} {} &".format(time_type,second,cronName) )
                
            time_type = param.get('time_type', '')
            if time_type:
                time_list=param.get('time_set', '')
                special_time=param.get('special_time', '')           
                # if time_type == "sweek":
                # 调用 Python 脚本进行时间检查
                head += 'if [[ $1 != "start" ]]; then\n'
                head += ' if ! btpython /www/server/panel/script/time_check.py time_type={} special_time={} time_list={}; then\n'.format(time_type, ",".join(special_time.split(",")), ",".join(time_list.split(",")))
                head += '   exit 1\n'
                head += ' fi\n'
                head += 'fi\n'
            if param['sType']=="site_restart":
                special_time=param.get('special_time', '')
                # 调用 Python 脚本进行时间检查
                head += 'if [[ $1 != "start" ]]; then\n'
                head += ' if ! btpython /www/server/panel/script/special_time.py special_time={} ; then\n'.format(",".join(special_time.split(",")))
                head += '   exit 1\n'
                head += ' fi\n'
                head += 'fi\n'
            log = '-access_log'
            python_bin = "{} -u".format(public.get_python_bin())
            if public.get_webserver() == 'nginx':
                log = '.log'
            if type in ['site', 'path'] and param['sBody'] != 'undefined' and len(param['sBody']) > 1:
                exclude_files = ','.join([n.strip() for n in param['sBody'].split('\n') if n.strip()])
                if exclude_files and 'bash -c ' in exclude_files: 
                    exclude_files = exclude_files.split('bash -c ')[1].replace("'",'').strip()
                head += f'export BT_EXCLUDE="{exclude_files}"\n'
            attach_param = " " + cronName
            log_cut_path = param['log_cut_path'] if hasattr(param,'log_cut_path') else '/www/wwwlogs/'
            special_time= param['special_time'] if hasattr(param,'special_time') else ''
            wheres = {
                'path': head + python_bin + " " + public.GetConfigValue(
                    'setup_path') + "/panel/script/backup.py path " + param['sName'] + " " + str(
                    param['save']) + attach_param,
                'site': head + python_bin + " " + public.GetConfigValue(
                    'setup_path') + "/panel/script/backup.py site " + param['sName'] + " " + str(
                    param['save']) + attach_param,
                'database': head + python_bin + " " + public.GetConfigValue(
                    'setup_path') + "/panel/script/backup.py database " + param['sName'] + " " + str(
                    param['save']) + attach_param,
                'logs': head + python_bin + " " + public.GetConfigValue('setup_path') + "/panel/script/logsBackup " +
                        param['sName'] + " " + str(param['save']) + " " + log_cut_path,
                'rememory': head + "/bin/bash " + public.GetConfigValue('setup_path') + '/panel/script/rememory.sh',
                'sync_time': head + python_bin + " " + public.GetConfigValue(
                    'setup_path') + "/panel/script/sync_time.py {}".format(param['sName']),
                'webshell': head + python_bin + " " + public.GetConfigValue(
                    'setup_path') + '/panel/class/webshell_check.py site ' + param['sName'] + ' ' + param['urladdress'],
                'mysql_increment_backup': head + python_bin + " " + public.GetConfigValue(
                    'setup_path') + '/panel/script/loader_binlog.py --echo_id=' + cronName,
                'special_log': head + python_bin + " " + public.GetConfigValue('setup_path') + "/panel/script/rotate_log_special.py " +
                               str(param['save']) + " " + param['sName'],
                'site_restart':head + python_bin + " " + public.GetConfigValue('setup_path') + "/panel/script/move_config.py " +
                              " " + param['sName'] + " " + special_time,
                'log_cleanup':head + python_bin + " " + public.GetConfigValue('setup_path') + "/panel/script/log_cleanup.py " +
                              " " + param['sName'],
            }
            # 取消插件调用计划任务
            # if param['backupTo'] != 'localhost':
            #     cfile = public.GetConfigValue('setup_path') + "/panel/plugin/" + param['backupTo'] + "/" + param[
            #         'backupTo'] + "_main.py"
            #     if not os.path.exists(cfile): cfile = public.GetConfigValue('setup_path') + "/panel/script/backup_" + \
            #                                           param['backupTo'] + ".py"
            #     wheres = {
            #         'path': head + python_bin + " " + cfile + " path " + param['sName'] + " " + str(
            #             param['save']) + attach_param,
            #         'site': head + python_bin + " " + cfile + " site " + param['sName'] + " " + str(
            #             param['save']) + attach_param,
            #         'database': head + python_bin + " " + cfile + " database " + param['sName'] + " " + str(
            #             param['save']) + attach_param,
            #         'logs': head + python_bin + " " + public.GetConfigValue(
            #             'setup_path') + "/panel/script/logsBackup " + param['sName'] + " " + str(param['save']),
            #         'rememory': head + "/bin/bash " + public.GetConfigValue('setup_path') + '/panel/script/rememory.sh',
            #         'webshell': head + python_bin + " " + public.GetConfigValue(
            #             'setup_path') + '/panel/class/webshell_check.py site ' + param['sName'] + ' ' + param[
            #                         'urladdress']
            #     }
            try:
                shell = wheres[type]
            except:
                if type=="site_restart":
                    lines = shell.split('\n')
                    last_line = lines[-1]               
                    new_command = '''
if [[ $1 == "start" ]]; then
        {} start
else
        {}
                    
fi
'''.format(last_line, last_line)
                    shell = shell.replace(last_line, new_command)
                # 设置 User-Agent 头
                user_agent = "-H 'User-Agent: {}'".format(param['user_agent']) if hasattr(param,'user_agent') else ''
                if type == 'toUrl':
                    # shell = head + "curl -sS --connect-timeout 10 -m 3600 '" + param['urladdress'] + "'"
                    shell = head + "curl -sS -L {} --connect-timeout 10 -m 3600 '{}'".format(user_agent, param['urladdress'])
                elif type == 'to_post':
                    param1 = {}
                    for i in json.loads(param['post_param']):
                        param1[i['paramName']] = i['paramValue']
                    # shell = head + '''curl -sS -X POST --connect-timeout 10 -m 3600 -H "Content-Type: application/json"  -d '{}' {} '''.format(json.dumps(param1),
                    #                                                                                                                            param['urladdress'])
                    shell = head + '''curl -sS -L -X POST {} --connect-timeout 10 -m 3600 -H "Content-Type: application/json"  -d '{}' {} '''.format(user_agent, json.dumps(param1), param['urladdress'])
                else:
                    shell = head + param['sBody'].replace("\r\n", "\n")
            cronPath = '/www/server/cron'  # 修改为实际的路径
            cronFile = f'{cronPath}/{cronName}.pl'
            logname=f'{cronPath}/{cronName}.log'
            shell += f'''
echo "----------------------------------------------------------------------------"
endDate=`date +"%Y-%m-%d %H:%M:%S"`
echo "★[$endDate] Successful"
echo "----------------------------------------------------------------------------"
if [[ "$1" != "start" ]]; then
    btpython /www/server/panel/script/log_task_analyzer.py {logname}
fi
rm -f {cronFile}
'''
        if type == 'toShell' and param.get('notice') and param['notice_channel'] and param['notice_channel'] and len(param.get('keyword', '')):
            shell += "btpython /www/server/panel/script/shell_push.py {} {} {} {} &".format(cronName, param['notice_channel'], param['keyword'], param['name'])
        cronPath = public.GetConfigValue('setup_path') + '/cron'
        if not os.path.exists(cronPath): public.ExecShell('mkdir -p ' + cronPath)
        file = cronPath + '/' + cronName
        public.writeFile(file, self.CheckScript(shell))
        public.ExecShell('chmod 750 ' + file)
        return cronName
        # except Exception as ex:
        # return public.returnMsg(False, 'FILE_WRITE_ERR' + str(ex))



    # 检查脚本
    def CheckScript(self, shell):
        keys = ['shutdown', 'init 0', 'mkfs', 'passwd', 'chpasswd', '--stdin', 'mkfs.ext', 'mke2fs']
        for key in keys:
            shell = shell.replace(key, '[***]')
        return shell

    # 重载配置
    def CrondReload(self):
        if os.path.exists('/etc/init.d/crond'):
            public.ExecShell('/etc/init.d/crond reload')
        elif os.path.exists('/etc/init.d/cron'):
            public.ExecShell('service cron restart')
        else:
            public.ExecShell("systemctl reload crond")

    # 将Shell脚本写到文件
    def WriteShell(self, config):
        u_file = '/var/spool/cron/crontabs/root'
        file = self.get_cron_file()
        if not os.path.exists(file): 
            if not public.writeFile(file, ''):
                return public.return_message(-1,0, 'Unable to write to file, please check if system hardening is enabled!')
               
        conf = public.readFile(file)
        if type(conf) == bool: return public.return_message(-1,0, 'Failed to read file!')
        conf += config + "\n"
        if public.writeFile(file, conf):
            if not os.path.exists(u_file):
                public.ExecShell("chmod 600 '" + file + "' && chown root.root " + file)
            else:
                public.ExecShell("chmod 600 '" + file + "' && chown root.crontab " + file)
            return public.return_message(0,0,'')
        return public.return_message(-1,0, 'Unable to write to file, please check if system hardening is enabled!')


    # 立即执行任务
    def StartTask(self, get):
        echo = public.M('crontab').where('id=?', (get.id,)).getField('echo')
        if not echo:
            return public.return_message(-1,0, public.lang("No data was found for the corresponding scheduled task. Please refresh the page to check if the scheduled task exists!"))
        execstr = public.GetConfigValue('setup_path') + '/cron/' + echo
        public.ExecShell('chmod +x ' + execstr)
        public.ExecShell('nohup ' + execstr +' start >> ' + execstr + '.log 2>&1 &')
        return public.return_message(0,0, public.lang('CRONTAB_TASK_EXEC'))

    # 获取计划任务文件位置
    def get_cron_file(self):
        u_path = '/var/spool/cron/crontabs'
        u_file = u_path + '/root'
        c_file = '/var/spool/cron/root'
        cron_path = c_file
        if not os.path.exists(u_path):
            cron_path = c_file

        if os.path.exists("/usr/bin/apt-get"):
            cron_path = u_file
        elif os.path.exists('/usr/bin/yum'):
            cron_path = c_file

        if cron_path == u_file:
            if not os.path.exists(u_path):
                os.makedirs(u_path, 472)
                public.ExecShell("chown root:crontab {}".format(u_path))
        if not os.path.exists(cron_path):
            public.writeFile(cron_path, "")
        return cron_path

    def modify_project_log_split(self, cronInfo, get):

        def _test_project_type(self, project_type):
            if project_type == "Node project":
                return "nodojsModel"
            elif project_type == "Java Project":
                return "javaModel"
            elif project_type == "GO Project":
                return "goModel"
            elif project_type == "Others":
                return "otherModel"
            elif project_type == "Python project":
                return "pythonModel"
            else:
                return None

        def the_init(self, cronInfo, get: dict):
            self.get = get
            self.cronInfo = cronInfo
            self.msg = ""
            self.flag = False
            name = get["name"]
            if name.find("Running log segmentation") != -1:
                try:
                    project_type, project_name = name.split("]", 2)[1].split("[", 1)
                    project_type = self._test_project_type(project_type)
                except:
                    self.project_type = None
                    return
            else:
                self.project_type = None
                return

            self.project_type = project_type
            self.project_name = project_name
            conf_path = '{}/data/run_log_split.conf'.format(public.get_panel_path())
            data = json.loads(public.readFile(conf_path))
            self.log_size = int(data[self.project_name]["log_size"]) / 1024 / 1024

        def modify(self):
            from importlib import import_module
            if not self.project_type:
                return False
            if self.cronInfo["type"] != self.get['type']:
                self.msg = "The execution cycle cannot be modified by cutting the running log"
                return True
            get = public.dict_obj()
            get.name = self.project_name
            get.log_size = self.log_size
            if get.log_size != 0:
                get.hour = "2"
                get.minute = str(self.get['where1'])
            else:
                get.hour = str(self.get['hour'])
                get.minute = str(self.get['minute'])
            get.num = str(self.get["save"])

            model = import_module(".{}".format(self.project_type), package="projectModel")

            res = getattr(model.main(), "mamger_log_split")(get)
            self.msg = res["msg"]
            self.flag = res["status"]

            return True

        attr = {
            "__init__": the_init,
            "_test_project_type": _test_project_type,
            "modify": modify,
        }
        return type("ProjectLog", (object,), attr)(cronInfo, get)

    # 检查指定的url是否通
    def check_url_connecte(self, get):
        if 'url' not in get or not get['url']:
            return public.return_message(-1,0, 'Please provide the URL!')

        try:
            start_time = time.time()
            response = requests.get(get['url'], timeout=30)
            response.encoding = 'utf-8'
            end_time = time.time()
            
            response_time = "{}ms".format(int(round(end_time - start_time, 2) * 1000))
            result = {'status_code': response.status_code, 
                    'txt': public.xsssec(response.text),
                    'time': response_time}
            status = 0 if response.status_code == 200 else -1
            return public.return_message(status,0,result)

        except requests.exceptions.Timeout as err:
            end_time = time.time()
            response_time = "{}ms".format(int(round(end_time - start_time, 2) * 1000))
            return public.return_message(-1,0,{'status_code': '', 'txt': 'request timeout: {}'.format(err), 'time': response_time})
        except requests.exceptions.ConnectionError as err:
            end_time = time.time()
            response_time = "{}ms".format(int(round(end_time - start_time, 2) * 1000))
            return public.return_message(-1,0,{'status_code': '', 'txt': 'connection error: {}'.format(err), 'time': response_time})
        except requests.exceptions.HTTPError as err:
            end_time = time.time()
            response_time = "{}ms".format(int(round(end_time - start_time, 2) * 1000))
            return public.return_message(-1,0,{'status_code': err.response.status_code, 'txt': 'HTTP Error: {}'.format(err), 'time': response_time})
        except requests.exceptions.RequestException as err:
            end_time = time.time()
            response_time = "{}ms".format(int(round(end_time - start_time, 2) * 1000))
            return public.return_message(-1,0,{'status_code': '', 'txt': 'Request exception: {}'.format(err), 'time': response_time})


    # 获取各个类型数据库
    def GetDatabases(self, get):
        from panel_mysql_v2 import panelMysql
        db_type = getattr(get, "db_type", "mysql")

        crontab_databases = public.M("crontab").field("id,sName").where("LOWER(type)=LOWER(?)", (db_type)).select()
        for db in crontab_databases:
            db["sName"] = set(db["sName"].split(","))

        if db_type == "redis":
            # 默认ALL
            return public.return_message(0, 0, [])

        databases = public.M("databases").field("name,ps").where("LOWER(type)=LOWER(?)", (db_type)).select()

        for database in databases:
            try:
                if database.get("name") is None: continue
                table_list = panelMysql().query("show tables from `{db_name}`;".format(db_name=database["name"]))
                if not isinstance(table_list, list):
                    continue
                cron_id = public.M("mysql_increment_settings").where("tb_name == ''", ()).getField("cron_id")
                database["table_list"] = [{"tb_name": "all", "value": "", "cron_id": cron_id if cron_id else None}]
                for tb_name in table_list:
                    cron_id = public.M("mysql_increment_settings").where("tb_name in (?)", (tb_name[0])).getField("cron_id")
                    database["table_list"].append({"tb_name": tb_name[0], "value": tb_name[0], "cron_id": cron_id if cron_id else None})

                database["cron_id"] = []
                for db in crontab_databases:
                    if database["name"] in db["sName"]:
                        database["cron_id"].append(db["id"])
            except Exception as e:
                print(e)
        return public.return_message(0,0,databases)

    # 取任务日志
    def GetWebShellLogs(self, get):
        id = get['id']
        echo_result = public.M('crontab').where("id=?", (id,)).field('echo').find()
        # 确保echo_result总是字典形式
        if isinstance(echo_result, list) and echo_result and isinstance(echo_result[0], dict):
            echo = echo_result[0]  # 如果是列表，则取列表的第一个字典元素
        elif isinstance(echo_result, dict):
            echo = echo_result
        else:
            return public.return_message(-1,0, public.lang("Task execution failed! No matching task record found."))

        # 从这一点开始，echo变量将是字典形式，并且包含'echo'键
        if 'echo' in echo:
            logFile = public.GetConfigValue('setup_path') + '/cron/' + echo['echo'] + '.log'
        else:
            return public.return_message(-1,0, public.lang("Task execution failed! The 'echo' information is missing from the task record."))
        
        if not os.path.exists(logFile): return public.return_message(-1,0, public.lang('Task logs are empty!'))
        logs = public.readFile(logFile)
        logs = public.xsssec(logs)
        logs = logs.split('\n')
        if hasattr(get, 'time_search') and get.time_search != '' and get.time_search != '[]':
            time_logs = []
            time_search = json.loads(get.time_search)
            start_time = int(time_search[0])
            end_time = int(time_search[1])
            for i in range(len(logs) - 1, -1, -1):
                infos = re.findall(r'【(.+?)】', logs[i])
                try:
                    infos_time = time.strptime(infos[0], "%Y-%m-%d %H:%M:%S")
                    infos_time = time.mktime(infos_time)
                    if infos_time > start_time and infos_time < end_time:
                        time_logs.append(logs[i])
                except:
                    pass
            time_logs.reverse()
            logs = time_logs

        if hasattr(get, 'type') and get.type != '':
            if get.type == 'warring':
                warring_logs = []
                for i in range(len(logs)):
                    if '【warring】' in logs[i]:
                        warring_logs.append(logs[i])
                logs = warring_logs

        for i in range(len(logs)):
            if '【warring】' in logs[i]:
                logs[i] = '<span style="background-color:rgba(239, 8, 8, 0.8)">{}</span>'.format(logs[i])
        logs = '\n'.join(logs)
        if logs:
            return public.return_message(0,0, public.lang(logs))
        else:
            return public.return_message(-1,0, public.lang('Task logs are empty!'))

    def download_logs(self, get):
        try:
            id = int(get['id'])
            echo = public.M('crontab').where("id=?", (id,)).field('echo').find()
            logFile = public.GetConfigValue('setup_path') + '/cron/' + echo['echo'] + '.log'
            if not os.path.exists(logFile): public.writeFile(logFile, "")
            logs = public.readFile(logFile)
            logs = logs.split('\n')
            if hasattr(get, 'day') and get.day != '':
                day = int(get.day)
                time_logs = []
                end_time = int(time.time())
                start_time = end_time - day * 86400
                for i in range(len(logs), 0, -1):
                    try:
                        infos = re.findall(r'【(.+?)】', logs[i])
                        infos_time = time.strptime(infos[0], "%Y-%m-%d %H:%M:%S")
                        infos_time = time.mktime(infos_time)
                        if infos_time > start_time and infos_time < end_time:
                            time_logs.append(logs[i])
                        if infos_time < start_time:
                            break
                    except:
                        pass
                time_logs.reverse()
                logs = time_logs
            if hasattr(get, 'type') and get.type != '':
                if get.type == 'warring':
                    warring_logs = []
                    for i in range(len(logs)):
                        if '【warring】' in logs[i]:
                            warring_logs.append(logs[i])
                    logs = warring_logs
            logs = '\n'.join(logs)
            public.writeFile('/tmp/{}.log'.format(echo['echo']), logs)
            return public.returnMsg(True, '/tmp/{}.log'.format(echo['echo']))
        except:
            return public.returnMsg(False, public.lang('Download failed!'))

    def clear_logs(self, get):
        try:
            id = int(get['id'])
            echo = public.M('crontab').where("id=?", (id,)).field('echo').find()
            logFile = public.GetConfigValue('setup_path') + '/cron/' + echo['echo'] + '.log'
            if not os.path.exists(logFile): return public.returnMsg(False, public.lang('Task logs are empty!'))
            logs = public.readFile(logFile)
            logs = logs.split('\n')
            if hasattr(get, 'day') and get.day != '':
                day = int(get.day)
                end_time = int(time.time())
                start_time = end_time - day * 86400

                last_idx = len(logs) - 1
                for i in range(len(logs) - 1, -1, -1):
                    info_obj = re.search(r'[【\[](\d+-\d+-\d+\s+\d+:\d+:\d+)[】\]]', logs[i])
                    if info_obj:
                        add_info_time = info_obj.group(1)
                        add_info_time = time.strptime(add_info_time, "%Y-%m-%d %H:%M:%S")
                        add_info_time = time.mktime(add_info_time)
                        if add_info_time < start_time:
                            break
                        last_idx = i
                logs = logs[last_idx:]
            else:
                logs = []
            public.writeFile(logFile, '\n'.join(logs))
            return public.returnMsg(True, public.lang('Clear successfully!'))
        except:
            return public.returnMsg(False,public.lang('Clearing failed!'))


    def cloud_backup_download(self, get):
        if not hasattr(get, 'filename'):
            return public.return_message(-1,0, public.lang('Please enter filename!'))
        if get.filename:
            if "|webdav|" in get.filename:
                import sys
                if '/www/server/panel/plugin/webdav' not in sys.path:
                    sys.path.insert(0, '/www/server/panel/plugin/webdav')
                try:
                    from webdav_main import webdav_main as webdav
                    path=webdav().cloud_download_file(get)['msg']
                except:
                    return public.return_message(-1,0, public.lang('Please install webdav storage first!'))
            else:
                path = get.filename.split('|')[0]
            if os.path.exists(path):
                return public.return_message(0,0,{'is_loacl': True, 'path': path})
        if not hasattr(get, 'cron_id'):
            return public.return_message(-1,0, 'Please pass in cron_id!')
        if "|" not in get.filename:
            return public.return_message(-1,0, 'The file does not exist!')
        cron_data = public.M('crontab').where('id=?', (get.cron_id,)).field('sType,sName,db_type').find()
        cloud_name = get.filename.split('|')[1]
        file_name = get.filename.split('|')[-1]
        names = cron_data['sName'].split(',')
        if names == ['ALL']:
            table = ''
            if cron_data['sType'] == 'site':
                table = 'sites'
            if cron_data['sType'] == 'database':
                table = 'databases'
            if not table:
                return public.return_message(-1,0, 'Data error!')
            names = public.M(table).field('name').select()
            names = [i.get('name') for i in names]

        if cron_data['sType']=="path":
            names = [os.path.basename(i) for i in list(names) if os.path.basename(i) in file_name]
        else:
            names = [i for i in list(names) if i in file_name]

        if not names:
            return public.return_message(-1,0, public.lang('No corresponding file found, please manually download from cloud storage'))
        if  cron_data['db_type']=="redis":
            name="redis"
        else:
            name = names[-1]
        import class_v2.cloud_stora_upload_v2 as CloudStoraUpload
        c = CloudStoraUpload.CloudStoraUpload()
        c.run(cloud_name)
        if c.obj is None:
            return public.return_message(-1,0, public.lang('Cloud storage object not initialized correctly!'))
        url = ''
        backup_path = c.obj.backup_path
        if cron_data['sType'] == 'site':
            path = os.path.join(backup_path, 'site', name)
            data = c.obj.get_list(path)
            for i in data['list']:
                if i['name'] == file_name:
                    url = i['download']

            if not url:
                path = os.path.join(backup_path, 'site')
                data = c.obj.get_list(path)
                for i in data['list']:
                    if i['name'] == file_name:
                        url = i['download']
                        break
        elif cron_data['sType'] == 'database':
            path = os.path.join(backup_path, 'database', cron_data['db_type'], name)
            data = c.obj.get_list(path)
            for i in data['list']:
                if i['name'] == file_name:
                    url = i['download']
                    break
            if not url:
                path = os.path.join(backup_path, 'database')
                data = c.obj.get_list(path)
                for i in data['list']:
                    if i['name'] == file_name:
                        url = i['download']
                        break
        elif cron_data['sType'] == 'path':
            path = os.path.join(backup_path, 'path', file_name.split('_')[1])
            data = c.obj.get_list(path)
            for i in data['list']:
                if i['name'] == file_name:
                    url = i['download']
                    break
        elif cron_data['sType'] == 'mysql_increment_backup':
            # path = os.path.join(backup_path, 'mysql_bin_log', file_name.split('_')[1],'databases')
            if "full" in get.filename:
                path = os.path.join(backup_path, 'mysql_bin_log', file_name.split('_')[2],'databases')
            else:
                path = os.path.join(backup_path, 'mysql_bin_log', file_name.split('_')[1],'databases')
            data = c.obj.get_list(path)
            for i in data['list']:
                if i['name'] == file_name:
                    url = i['download']
                    break
        if url == '':
            return public.return_message(-1,0, public.lang('The file was not found in the cloud storage!'))
        return public.return_message(0,0,{'is_loacl': False, 'path': url})

    def get_crontab_types(self, get):
        data = public.M("crontab_types").field("id,name,ps").order("id asc").select()
        return  public.return_message(0,0,data)

    def add_crontab_type(self, get):
        # get.name =  html.escape(get.name.strip())
        get.name = public.xsssec(get.name.strip())
        if re.search('<.*?>', get.name):
            return public.return_message(-1,0, public.lang("The category name cannot contain HTML statements"))
        if not get.name:
            return public.return_message(-1,0, public.lang("Classification name cannot be empty"))
        if len(get.name) > 16:
            return public.return_message(-1,0, public.lang("The length of the category name cannot exceed 16 digits"))

        crontab_type_sql = public.M('crontab_types')

        if get.name in {"shell script", "Backup website", "Backup Database", "Incremental backup of database", "Log cutting", "backup directory", "Trojan killing", "synchronize", "free memory", "Accessing URL", "System tasks"}:
            return public.return_message(-1,0, "The specified category name already exists")

        if crontab_type_sql.where('name=?', (get.name,)).count() > 0:
            return public.return_message(-1,0, public.lang("The specified category name already exists"))

        # 添加新的计划任务分类
        crontab_type_sql.add("name", (get.name,))

        return public.return_message(0,0, public.lang('Added successfully'))

    def remove_crontab_type(self, get):
        crontab_type_sql = public.M('crontab_types')
        crontab_sql = public.M('crontab')
        crontab_type_id = get.id

        if crontab_type_sql.where('id=?', (crontab_type_id,)).count() == 0:
            return public.return_message(-1,0, public.lang("The specified category does not exist"))

        name = crontab_type_sql.where('id=?', (crontab_type_id,)).field('name').find().get('name', '')
        # if name in {"toShell", "site", "database", "enterpriseBackup", "logs", "path", "webshel", "syncTime", "rememory", "toUrl", "系统任务"}:
        #     return public.returnMsg(False, "这是默认类型，无法删除")

        # 删除指定的计划任务分类
        crontab_type_sql.where('id=?', (crontab_type_id,)).delete()

        # 找到 crontab 表中的相关数据，并设置其 sType 和 type_id 字段为空
        crontab_sql.where('type_id=?', (crontab_type_id,)).save('type_id', (''))

        return public.return_message(0,0, public.lang("Category deleted"))

    def modify_crontab_type_name(self, get):
        get.name = public.xsssec(get.name.strip())
        # get.name =  html.escape(get.name.strip())
        if re.search('<.*?>', get.name):
            return public.return_message(-1,0, public.lang("The category name cannot contain HTML statements"))
        if not get.name:
            return public.return_message(-1,0, public.lang("Classification name cannot be empty"))
        if len(get.name) > 16:
            return public.return_message(-1,0, public.lang("The length of the category name cannot exceed 16 digits"))

        crontab_type_sql = public.M('crontab_types')
        crontab_type_id = get.id

        if crontab_type_sql.where('id=?', (crontab_type_id,)).count() == 0:
            return public.return_message(-1,0, public.lang("The specified category does not exist"))

        if get.name in {"shell script", "Backup website", "Backup Database", "Incremental backup of database", "Log cutting", "backup directory", "Trojan killing", "synchronize", "free memory", "Accessing URL", "System tasks"}:
            return public.return_message(-1,0, public.lang("The name cannot be changed to the default task classification name of the system"))

        if crontab_type_sql.where('name=? AND id!=?', (get.name, crontab_type_id)).count() > 0:
            return public.return_message(-1,0, public.lang("The specified category name already exists"))

        # 修改指定的计划任务分类名称
        crontab_type_sql.where('id=?', (crontab_type_id,)).setField('name', get.name)

        return public.return_message(0,0, public.lang("Modified successfully"))

    def set_crontab_type(self, get):
        try:
            crontab_ids = json.loads(get.crontab_ids)
            crontab_sql = public.M("crontab")
            crontab_type_sql = public.M("crontab_types")

            # sType= public.M('crontab_types').where('id=?', (get['type_id'],)).field('name').find().get('name', '')
            crontab_type_id = get.id
            if crontab_type_id=="-1" or crontab_type_id=="0":
                return public.return_message(-1,0,public.lang("Cannot be set as system classification or default classification!"))
            if crontab_type_sql.where('id=?', (crontab_type_id,)).count() == 0:
                return public.return_message(-1,0, public.lang("The specified category does not exist"))
            for s_id in crontab_ids:
                crontab_sql.where("id=?", (s_id,)).save('type_id', (crontab_type_id))

            return public.return_message(0,0, public.lang("Setting successful!"))
        except Exception as e:
            return public.return_message(-1,0, public.lang("Setting failed" + str(e)))


    def export_crontab_to_json(self, get):
        try:
            # 获取前端发送的id值，可以是逗号分隔的字符串
            task_ids = get.get('ids', None)
            
            if task_ids:
                # 去除方括号和多余的空格
                task_ids = task_ids.strip('[]').replace(' ', '')
                # 将逗号分隔的字符串转换为列表
                task_id_list = task_ids.split(',')
                # 使用where条件和in语句选择对应的计划任务
                crontab_data = public.M('crontab').where('id in ({})'.format(','.join('?' * len(task_id_list))), tuple(task_id_list)).field(self.field).select()
            else:
                crontab_data = public.M('crontab').order("id asc").field(self.field).select()
            
            # 遍历 crontab_data 列表
            # print(crontab_data)
            for task in crontab_data:
                # 将每个任务的 type_id 字段设置为空
                task['type_id'] = ""
                # # 删除 echo 字段
                # if 'echo' in task:
                #     del task['echo']
            
            # 将数据转换为 JSON 格式
            json_data = json.dumps(crontab_data)
            
            # 将 JSON 数据写入文件
            with open('/tmp/cron_task_data.json', 'w') as f:
                f.write(json_data)
            
            return public.returnMsg(True, public.lang("/tmp/cron_task_data.json"))
        except Exception as e:
            return public.returnMsg(False, public.lang("Export failed:" + str(e)))


    def import_crontab_from_json(self, get):
        try:
            file = request.files['file']           
            overwrite = get.get('overwrite') == '1'
            if file:
                json_data = file.read().decode('utf-8')

                try:
                    crontab_data = json.loads(json_data)
                except ValueError as e:
                    return public.returnMsg(False, public.lang("Unable to parse JSON file!"))

                if not isinstance(crontab_data, list):
                    return public.returnMsg(False, public.lang("The JSON file content format is incorrect!"))

                existing_tasks = public.M('crontab').order("id desc").field(self.field).select()
                existing_names = {task['name'] for task in existing_tasks} if overwrite else set()

                successful_imports = 0
                failed_tasks = []
                skipped_tasks = []
                successful_tasks = [] 
                required_keys = [
                    'name', 'type', 'where1', 'where_hour', 'where_minute', 'addtime', 'status', 'save', 'backupTo',
                    'sName', 'sBody', 'sType', 'urladdress', 'save_local', 'notice', 'notice_channel', 'db_type', 'split_type',
                    'split_value', 'keyword', 'post_param', 'flock', 'time_set', 'backup_mode', 'db_backup_path', 'time_type',
                    'special_time', 'user_agent', 'version', 'table_list', 'result', 'log_cut_path', 'rname', 'type_id', 'second','stop_site'
                ]

                for task in crontab_data:
                    if overwrite and task['name'] in existing_names:
                        skipped_tasks.append(task['name'])
                        continue 
                    
                    # 创建新任务字典时，特别处理 where_hour 和 where_minute
                    new_task = {}
                    for key in required_keys:
                        if key == 'where_hour':
                            key='hour'
                            new_task[key] = task.get('where_hour', '')
                        elif key == 'where_minute':
                            key='minute'
                            new_task[key] = task.get('where_minute', '')
                        else:
                            new_task[key] = task.get(key, '')
                    new_task['result'] = 1  # 设置默认 result 为 1
                    result = self.AddCrontab(new_task)
                    if result.get('status', False):
                        successful_imports += 1
                        successful_tasks.append(task['name'])  
                    else:
                        failed_tasks.append(task['name'])

                message = public.lang("Successfully imported {} scheduled tasks",str(successful_imports))
                result = {
                    "status": True,
                    "msg": message,
                    "skipped_tasks": skipped_tasks,
                    "failed_tasks": failed_tasks,
                    "successful_tasks": successful_tasks  
                }
                return result

            else:
                return public.returnMsg(False, public.lang("Please choose to import the file!"))
        except Exception as e:
            return public.returnMsg(False, public.lang("Import failed! {0}",str(e)))

    def stop_cron_task(self, cronPath, cronName, if_stop):
        cronFile = '{}/{}.pl'.format(cronPath,cronName)
        if if_stop == "True":
            if os.path.exists(cronFile):
                try:
                    # 读取文件内容，获取 PID
                    with open(cronFile, 'r') as file:
                        pid = file.read().strip()
                    os.system('kill -9 {}'.format(pid))
                    os.remove(cronFile)
                except:
                    pass

    def set_atuo_start_syssafe(self, get):
        try:
            if not hasattr(get, 'time'):
                return public.returnMsg(False, public.lang("Please pass in the time parameter!"))
            time = int(get.time)
            public.ExecShell('/etc/init.d/bt_syssafe stop')
            data = {
                'type': 2,
                'time': time,
                'name': 'syssafe',
                'title': 'Reinforcement of Pagoda System',
                'fun': 'set_open',
                'args': {
                    'status': 1
                }
            }
            public.set_tasks_run(data)
            return public.returnMsg(True, public.lang("Temporary system shutdown and reinforcement successful!"))
        except Exception as e:
            public.ExecShell('/etc/init.d/bt_syssafe start')
            return public.returnMsg(False, public.lang("Temporary shutdown of system reinforcement failed!" + str(e)))

    def set_atuo_start_syssafe(self, get):
        try:
            if not hasattr(get, 'time'):
                return public.returnMsg(False, public.lang("Please pass in the time parameter!"))
            time = int(get.time)
            public.ExecShell('/etc/init.d/bt_syssafe stop')
            data = {
                'type': 2,
                'time': time,
                'name': 'syssafe',
                'title': 'Reinforcement of Pagoda System',
                'fun': 'set_open',
                'args': {
                    'status': 1
                }

            }
            public.set_tasks_run(data)
            return public.returnMsg(True, public.lang("Temporary system shutdown and reinforcement successful!"))
        except Exception as e:
            return public.returnMsg(False, public.lang("Temporary shutdown of system reinforcement failed!" + str(e)))

    def set_rotate_log(self, get):
        try:
            p = crontab()
            task_name = '[Do not delete] Cut plan task log'
            status = get.status
            numbers = get.numbers

            public.M('crontab').where('name=?', (task_name,)).setField('status', status)
            public.M('crontab').where('name=?', (task_name,)).setField('save', numbers)
            # public.M('crontab').where('name=?', (task_name,)).setField('sBody', sBody)
            if get.status == "1":

                return public.returnMsg(True, public.lang("Successfully enabled log cutting"))
            else:
                return public.returnMsg(True, public.lang("Successfully closed log cutting"))
            # print("开启日志切割成功")
        except Exception as e:
            return public.returnMsg(False, public.lang("Failed to enable log cutting" + str(e)))
            # print("开启日志切割失败 ")

    def get_rotate_log_config(self, get):
        try:
            p = crontab()
            task_name = '[Do not delete] Cut plan task log'

            if public.M('crontab').where('name=?', (task_name,)).count() == 0:
                task = {
                    "name": task_name,
                    "type": "day-n",
                    "where1": "1",
                    "hour": "0",
                    "minute": "0",
                    "week": "",
                    "sType": "toShell",
                    "sName": "",
                    "backupTo": "",
                    "save": "10",
                    "sBody": "btpython /www/server/panel/script/rotate_log.py 10",
                    "urladdress": "",
                    "status": "1"
                }
                p.AddCrontab(task)
            crontab_data = public.M('crontab').where('name=?', (task_name,)).select()[0]
            status = crontab_data['status']
            numbers = crontab_data['save']
            info = {"status": status, "numbers": numbers}
            return public.returnMsg(True, info)
        except Exception as e:
            return public.returnMsg(False, public.lang("Acquisition failed：" + str(e)))

    def get_restart_project_config(self, get):
        try:
            # import sys
            # sys.path.append("..")  # 添加上一级目录到系统路径
            # import crontab
            # import public
            model_name=get.model_name
            project_name=get.project_name
            task_name = '[Do Not Delete] Scheduled Restart {} Project {}'.format(model_name,project_name)
            sBody='btpython /www/server/panel/script/restart_project.py {} {}'.format(model_name,project_name)
            public.M('crontab').where('name=?', (task_name,)).select()
            if public.M('crontab').where('name=?', (task_name,)).count() == 0:
                task = {
                    "name": task_name,
                    "type": "day",
                    "where1":"" ,
                    "hour": "0",
                    "minute":"0",
                    "week": "",
                    "sType": "toShell",
                    "sName": "",
                    "backupTo": "",
                    "save": "10",
                    "sBody": sBody,
                    "urladdress": "",
                    "status":"0"
                }
                crontab().AddCrontab(task)
                public.M('crontab').where('name=?', (task_name,)).setField('status', 0)
            crontab_data_list = public.M('crontab').where('name=?', (task_name,)).select()
            if crontab_data_list:
                crontab_data = crontab_data_list[0]
                status = crontab_data['status']
                return public.returnMsg(True, crontab_data)
            else:
                return public.returnMsg(False, public.lang("Failed to create scheduled task {}, please check if system hardening is enabled or disk condition",task_name))
        except Exception as e:
            return public.returnMsg(False, public.lang("Acquisition failed："+str(e)))
    
    def set_restart_project(self,get):
        try:
            status=get.status
            hour = get.get('hour', 0)
            minute = get.get('minute', 0)
            model_name=get.model_name
            project_name=get.project_name
            task_name = '[Do Not Delete] Scheduled Restart {} Project {}'.format(model_name,project_name)

            crontab_data_list = public.M('crontab').where('name=?', (task_name,)).select()
            if crontab_data_list:
                public.M('crontab').where('name=?', (task_name,)).setField('status', status)
                public.M('crontab').where('name=?', (task_name,)).setField('where_hour', hour)
                public.M('crontab').where('name=?', (task_name,)).setField('where_minute', minute)
                if  get.status=="1":
                        return public.returnMsg(True, public.lang("Successfully opened"))
                else:
                    return public.returnMsg(True, public.lang("Close successfully"))
            else:
                return public.returnMsg(False, public.lang("Failed to create scheduled task {}, please check if system hardening is enabled or disk condition",task_name))

        except Exception as e:
            return public.returnMsg(False, public.lang("Opening failed"+str(e)))


    def modify_values(self, cronName, new_time_type, new_special_time, new_time_list):
        cronName = cronName 
        cronPath = '/www/server/cron'  
        cronFile = '{}/{}'.format(cronPath, cronName)
        # 打开文件
        with open(cronFile, 'r') as file:
            # 读取文件内容
            lines = file.readlines()

        # 进行你的修改
        for i, line in enumerate(lines):
            if "btpython /www/server/panel/script/time_check.py" in line:
                lines[i] = 'if ! btpython /www/server/panel/script/time_check.py time_type={} special_time={} time_list={}; then\n'.format(new_time_type, new_special_time, new_time_list)

        # 保存修改
        with open(cronFile, 'w') as file:
            file.writelines(lines)

    def set_execute_script(self, get):

        # get._ws.send(public.getJson({
        #     "result": False,
        # }))
        if '_ws' not in get:
            return False

        public.ExecShell("chmod +x /www/server/panel/script/check_crontab.sh")
        # 使用nohup运行脚本，并将输出重定向到/www/test.txt，同时确保命令在后台运行
        exec_result=public.ExecShell("nohup /www/server/panel/script/check_crontab.sh > /www/check_crontab.txt 2>&1 &")
        if exec_result:  # 假设ExecShell返回的第一个元素是成功与否的标志
            # 以只读模式打开日志文件，并移动到文件末尾
            if not os.path.exists("/www/check_crontab.txt"):
                public.writeFile("/www/check_crontab.txt", "")
            with open("/www/check_crontab.txt", "r") as log_file:
                while True:
                    # 读取新的一行
                    line = log_file.readline()
                    if not line:
                        time.sleep(1)  # 如果没有新内容，则稍等片刻再尝试读取
                        continue
                    # 发送新读取的行
                    # print(line.strip())
                    get._ws.send(public.getJson({
                    "callback":"set_execute_script",
                    "result":line.strip()

                    }))
                    # get._ws.send(line.strip())  # 使用strip()移除行尾的换行符
                    if line.strip()=="successful":
                        break
            return True
        else:
            get._ws.send(public.lang("Script execution failed"))
            return False
    def get_system_user_list(self, get):
        all_user = False
        if get is not None:
            if hasattr(get, "all_user"):
                all_user = True
        root_and_www = []  # 新增列表存储root和www用户
        other_users = []   # 新增列表存储其他用户
        with open('/etc/passwd', 'r', encoding='utf-8', errors='ignore') as fp:
            for line in fp.readlines():
                tmp = line.split(':')
                if len(tmp) > 2:  # 检查 tmp 是否有足够的元素
                    user_name = tmp[0]
                    try:
                        uid = int(tmp[2])
                    except ValueError:
                        continue  # 如果 uid 不是有效的整数，跳过这行
                    if user_name in ['root', 'www']:
                        root_and_www.append(user_name)  # 直接添加到root和www列表
                        continue
                    if uid == 0:
                        other_users.append(user_name)
                        continue
                    if uid >= 1000:
                        other_users.append(user_name)
                        continue
                    if all_user:
                        other_users.append(user_name)  # 添加所有用户（根据all_user标志）

        # 合并列表，确保root和www在前
        return root_and_www + list(set(other_users) - set(root_and_www))

    # 增量备份获取数据库信息
    def get_databases(self, get):
        from panelMysql import panelMysql
        # try:
        #     import PluginLoader
        #     return PluginLoader.module_run('binlog', 'get_databases', get)
        # except Exception as err:
        #     return {"status":False, "msg": err}
        try:
            database_list = public.M("databases").field("name").where("sid=0 and LOWER(type)=LOWER(?)", ("mysql")).select()
            for database in database_list:
                database["value"] = database["name"]
                cron_id = public.M("mysql_increment_settings").where("db_name=?", (database["name"])).getField("cron_id")
                database["cron_id"] = cron_id if cron_id else None

                table_list = panelMysql().query("show tables from `{db_name}`;".format(db_name=database["name"]))
                if not isinstance(table_list, list):
                    continue
                cron_id = public.M("mysql_increment_settings").where("tb_name == ''", ()).getField("cron_id")
                database["table_list"] = [{"tb_name": "all", "value": "", "cron_id": cron_id if cron_id else None}]
                for tb_name in table_list:
                    cron_id = public.M("mysql_increment_settings").where("tb_name in (?)", (tb_name[0])).getField("cron_id")
                    database["table_list"].append({"tb_name": tb_name[0], "value": tb_name[0], "cron_id": cron_id if cron_id else None})
            return {"status": True, "msg": "ok", "data": database_list}
        except Exception as err:
            return {"status":False, "msg": err}

    @staticmethod
    def _cron_name_to_config_type(name: str) -> tuple[str, str]:
        if name == "mysql":  # backup all the mysql
            sType, db_type = "database", "mysql"
        elif name == "site":  # backup all the site
            sType, db_type = "site", "mysql"
        else:
            sType, db_type = "", ""
        return sType, db_type

    # 获取自动备份配置状态信息
    def get_auto_config(self, get):
        try:
            get.validate([
                Param('name').Require().String(),
            ], [
                public.validate.trim_filter(),
            ])
        except Exception as ex:
            return public.return_message(-1, 0, str(ex))

        name = get.name
        sType, db_type = self._cron_name_to_config_type(name)
        if not sType or not db_type:
            return public.success_v2({"status": 0})

        crontab_data_list = public.M('crontab').where('sType=? AND db_type=?', (sType, db_type)).select()
        if isinstance(crontab_data_list, str):
            return public.fail_v2(f"Query failed, {crontab_data_list}")
        crontab_data = crontab_data_list[0] if crontab_data_list else {"status": 0}
        return public.success_v2(crontab_data)

    # 设置自动备份配置状态
    def set_auto_config(self, get):
        try:
            get.validate([
                Param('name').Require().String(),
            ], [
                public.validate.trim_filter(),
            ])
        except Exception as ex:
            return public.return_message(-1, 0, str(ex))

        name = get.name
        sType, db_type = self._cron_name_to_config_type(name)
        if not sType or not db_type:
            return public.fail_v2("Set failed!")
        if public.M('crontab').where('sType=? AND db_type=?', (sType, db_type)).count() == 0:
            task_name_map = {
                "mysql": public.lang("Auto Backup Database[ALL]--mysql"),
                "site": public.lang("Auto Backup Site[ALL]"),
            }
            task_info = {
                "name": task_name_map.get(name),
                "type": "day",
                "where1": "1",
                "week": "1",
                "hour": "1",
                "minute": "30",
                "second": "",
                "save": "3",
                "backupTo": "localhost",
                "sName": "ALL",
                "sBody": "",
                "sType": sType,
                "urladdress": "http://",
                "save_local": "0",
                "db_type": db_type,
                "notice": 0,
                "notice_channel": "",
            }
            res = crontab().AddCrontab(task_info)
            if res.get("status") == 0:
                return public.success_v2("set success!")
            else:
                return public.fail_v2("set failed!")
        else:
            pk = {
                "id": public.M('crontab').where('sType=? AND db_type=?', (sType, db_type)).getField('id')
            }
            return crontab().set_cron_status(public.to_dict_obj(pk))
