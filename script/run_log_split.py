#!/usr/bin/python
# coding: utf-8
# -----------------------------
# Website run log split script
# -----------------------------
import sys
import os
import time
import glob

os.chdir("/www/server/panel")
if '/www/server/panel' not in sys.path:
    sys.path.insert(0,'/www/server/panel')
if '/www/server/panel/class' not in sys.path:
    sys.path.insert(0,'class/')
if '/www/server/panel/class_v2' not in sys.path:
    sys.path.insert(0,'class_v2/')

import public, json

try:
    from projectModelV2.pythonModel import main as pythonMod
    from projectModelV2.nodejsModel import main as nodejsMod

    mods = {
        "python": pythonMod(),
        "node": nodejsMod(),
    }
except Exception as e:
    print(str(e))
    print("****** project split log task error ******")

print('==================================================================')
print('★[' + time.strftime("%Y/%m/%d %H:%M:%S") + '] split log task start ★')
print('==================================================================')


class LogSplit:
    __slots__ = ("stype", "log_size", "limit", "_time", "compress", "exclude_sites")

    @classmethod
    def build_log_split(cls, name):
        logsplit = cls()
        path = '{}/data/run_log_split.conf'.format(public.get_panel_path())
        data = {}
        if os.path.exists(path):
            try:
                data = json.loads(public.readFile(path))
            except:
                public.ExecShell("rm -f {}".format(path))
                return "file not found"
        _clean(data)
        public.writeFile(path, json.dumps(data))
        target = data.get(name)
        if not target :            
            return  "file not found"
        else:
            for i in cls.__slots__:
                if i in target:
                    setattr(logsplit, i, target[i])
            logsplit._show()
            return logsplit

    def __init__(self, split_type: str = "day", limit: int = 180, log_size: int = 1024, compress: bool = False) -> None:
        self.stype = split_type
        self.log_size = log_size
        self.limit = limit
        self._time = time.strftime("%Y-%m-%d_%H%M%S")
        self.compress = compress
        self.exclude_sites = []

    def _show(self):
        if self.stype == "day":
            print('|---Split method: Split 1 copy per day')
        else:
            print('|---Split method: Split by file size, split when file exceeds {}'.format(public.to_size(self.log_size)))
        print('|---Currently keeping the latest [{}] copies'.format(self.limit))

    def _to_zip(self, file_path):
        os.system('gzip {}'.format(file_path))

    def _del_surplus_log(self, history_log_path, log_prefix):
        if not os.path.exists(history_log_path):
            os.makedirs(history_log_path, mode=0o755)
        logs = sorted(glob.glob(history_log_path + '/' + log_prefix + "*_log.*"))

        count = len(logs)
        if count >= self.limit:
            for i in logs[:count - self.limit + 1]:
                if os.path.exists(i):
                    os.remove(i)
                    print('|---Surplus log [' + i + '] has been deleted!')

    def __call__(self, pjanme: str, sfile: str, log_prefix: str):
        base_path, filename = sfile.rsplit("/", 1)
        history_log_path = '{}/{}-history_logs'.format(base_path, pjanme)

        if self.stype == 'size' and os.path.getsize(sfile) < self.log_size:
            print('|---File size has not exceeded [{}], skipping!'.format(public.to_size(self.log_size)))
            return

        self._del_surplus_log(history_log_path, log_prefix)

        if os.path.exists(sfile):
            history_log_file = history_log_path + '/' + log_prefix + '_' + self._time + '_log.log'
            if not os.path.exists(history_log_file):
                with open(history_log_file, 'wb') as hf, open(sfile, 'r+b') as lf:
                    while True:
                        chunk_data = lf.read(1024*100)
                        if not chunk_data:
                            break
                        hf.write(chunk_data)
                    lf.seek(0)
                    lf.truncate()
            if self.compress:
                self._to_zip(history_log_file)

            print('|---Log has been split to: ' + history_log_file + (".gz" if self.compress else ""))
        else:
            print('|---Target log file {} for project {} is missing, please note'.format(sfile, pjanme))



def main(name):
    logsplit = LogSplit.build_log_split(name)
    if logsplit=="file not found":
       print(
           "****** Detected panel project log split task configuration is empty,"
           " please reset project log split task ******"
       )
       return 
    if not logsplit:
        print("****** Panel project log split task configuration file is missing ******")
        return
    project = public.M('sites').where("project_type <> ?  and name = ?", ("PHP", name)).find()
    project['project_config'] = json.loads(project['project_config'])
    for_split_func = getattr(mods.get(project["project_type"].lower()), "for_split")
    if callable(for_split_func):
        print('|---Starting to operate on {} project [{}] logs'.format(project["project_type"], project["name"]))
        try:
            for_split_func(logsplit, project)
            print('|---Completed log split task for {} project [{}]'.format(project["project_type"], project["name"]))
        except:
            import  traceback
            print(traceback.format_exc())
            print('|---Log split task error for {} project [{}]'.format(project["project_type"], project["name"]))
    else:
        print("****** Panel project log split task error ******")
    print('================= All log split tasks completed ==================')


def _clean(data):
    res = public.M('crontab').field('name').select()
    del_config = []
    for i in data.keys():
        for j in res:
            if j["name"].find(i) != -1 and j["name"].find("log split"):
                break
        else:
            del_config.append(i)

    for i in del_config:
        del data[i]


if __name__ == '__main__':
    if len(sys.argv) == 2:
        name = sys.argv[1].strip()
        main(name)
    else:
        print("****** Panel project log split task configuration parameter error ******")