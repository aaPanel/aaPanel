import os,sys
panel_path = '/www/server/panel'
if not os.name in ['nt']:
    os.chdir(panel_path)
if not 'class/' in sys.path:
    sys.path.insert(0, 'class/')
if not 'class_v2/' in sys.path:
    sys.path.insert(0, 'class_v2/')
sys.path.insert(0, '.')
from projectModelV2 import safecloudModel
from mod.base.push_mod import system

class main:

    def run(self):
        try:
            safecloud = safecloudModel.main()
            # 调用 webshell_detection 函数
            res = safecloud.webshell_detection({'is_task': 'true'})
            push_list = []
            if res['status']:
                if res['detected']:
                    push_list.append(res['msg']+', Please handle it as soon as possible!')
                    for i in res['detected']:
                        push_list.append(f'file:{i}')
            return {"msg_list": push_list}
        except Exception as e:
            print(e)
            return {"msg_list": []}


if __name__ == '__main__':
    main_obj = main()
    msg = main_obj.run()
    if msg['msg_list']:
        system.push_by_task_keyword("safe_cloud_hinge", "safe_cloud_hinge", push_data=msg)