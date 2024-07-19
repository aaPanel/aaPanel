#coding: utf-8
#-------------------------------------------------------------------
# aaPanel
#-------------------------------------------------------------------
# Copyright (c) 2015-2099 aaPanel(www.aapanel.com) All rights reserved.
#-------------------------------------------------------------------
# Author: zouhw <zhw@aapanel.com>
#-------------------------------------------------------------------

#------------------------------
# Docker模型
#------------------------------
import public #line:13
import os #line:14
import time #line:15
import projectModel .bt_docker .dk_public as dp #line:16
import projectModel .bt_docker .dk_container as dc #line:17
import projectModel .bt_docker .dk_setup as ds #line:18
import json #line:19
class main :#line:22
    compose_path ="{}/data/compose".format (public .get_panel_path ())#line:23
    __O00OO0OO00O0OO000 ="/tmp/dockertmp.log"#line:24
    def check_conf (O0OO0OO00OO0OOO00 ,O0OOOOOOO00O00O00 ):#line:27
        OOO0OOO0OOO0000O0 ="/usr/bin/docker-compose -f {} config".format (O0OOOOOOO00O00O00 )#line:28
        O0O0000OOOO0O0O0O ,OOOO00O0O00OOO0O0 =public .ExecShell (OOO0OOO0OOO0000O0 )#line:29
        if OOOO00O0O00OOO0O0 :#line:30
            return public .return_msg_gettext (False ,"Check failed:{}".format (OOOO00O0O00OOO0O0 ))#line:31
        return public .return_msg_gettext (True ,"Passed!")#line:32
    def add_template_gui (O0O0OOOOOOO00O000 ,O0000O0O0O0O00O00 ):#line:35
        ""#line:69
        import yaml #line:70
        O000000OOO0O00OO0 ="{}/template".format (O0O0OOOOOOO00O000 .compose_path )#line:71
        O0O00000OO000OO0O ="{}/{}.yaml".format (O000000OOO0O00OO0 ,O0000O0O0O0O00O00 .name )#line:72
        if not os .path .exists (O000000OOO0O00OO0 ):#line:73
            os .makedirs (O000000OOO0O00OO0 )#line:74
        O000O0O000O0OOOO0 =json .loads (O0000O0O0O0O00O00 .data )#line:75
        yaml .dump (O000O0O000O0OOOO0 ,O0O00000OO000OO0O )#line:76
    def get_template_kw (O0OOO0OO0OOO0000O ,OO00OO000OOOOOOOO ):#line:78
        O0OO0OO0O00O0OO0O ={"version":"","services":{"server_name_str":{"build":{"context":"str","dockerfile":"str","args":[],"cache_from":[],"labels":[],"network":"str","shm_size":"str","target":"str"},"cap_add":"","cap_drop":"","cgroup_parent":"str","command":"str","configs":{"my_config_str":[]},"container_name":"str","credential_spec":{"file":"str","registry":"str"},"depends_on":[],"deploy":{"endpoint_mode":"str","labels":{"key":"value"},"mode":"str","placement":[{"key":"value"}],"max_replicas_per_node":"int","replicas":"int","resources":{"limits":{"cpus":"str","memory":"str",},"reservations":{"cpus":"str","memory":"str",},"restart_policy":{"condition":"str","delay":"str","max_attempts":"int","window":"str"}}}}}}#line:134
    def add_template (OO0O00000000O00OO ,O00OOOOOO0O0O0000 ):#line:137
        ""#line:145
        OO00O0OO0O0O0000O =OO0O00000000O00OO .template_list (O00OOOOOO0O0O0000 )['msg']['template']#line:146
        for O0O00O000OO000OO0 in OO00O0OO0O0O0000O :#line:147
            if O00OOOOOO0O0O0000 .name ==O0O00O000OO000OO0 ['name']:#line:148
                return public .return_msg_gettext (False ,"This template name already exists!")#line:149
        OO0OOOOO0OO0O0OOO ="{}/{}/template".format (OO0O00000000O00OO .compose_path ,O00OOOOOO0O0O0000 .name )#line:150
        O00OOO00O0O0O0OOO ="{}/{}.yaml".format (OO0OOOOO0OO0O0OOO ,O00OOOOOO0O0O0000 .name )#line:151
        if not os .path .exists (OO0OOOOO0OO0O0OOO ):#line:152
            os .makedirs (OO0OOOOO0OO0O0OOO )#line:153
        public .writeFile (O00OOO00O0O0O0OOO ,O00OOOOOO0O0O0000 .data )#line:154
        OOO0000O000O0OO00 =OO0O00000000O00OO .check_conf (O00OOO00O0O0O0OOO )#line:155
        if not OOO0000O000O0OO00 ['status']:#line:156
            if os .path .exists (O00OOO00O0O0O0OOO ):#line:157
                os .remove (O00OOO00O0O0O0OOO )#line:158
            return OOO0000O000O0OO00 #line:160
        O0O0OO0O00OO00OO0 ={"name":O00OOOOOO0O0O0000 .name ,"remark":O00OOOOOO0O0O0000 .remark ,"path":O00OOO00O0O0O0OOO }#line:165
        dp .sql ("templates").insert (O0O0OO0O00OO00OO0 )#line:166
        dp .write_log ("Add template [{}] successful!".format (O00OOOOOO0O0O0000 .name ))#line:167
        return public .return_msg_gettext (True ,"Template added successfully!")#line:169
    def edit_template (OOOO00O0OOOOO0O00 ,O00O0O0O000O0O000 ):#line:171
        ""#line:178
        O0O00OOO00OOOO00O =dp .sql ("templates").where ("id=?",(O00O0O0O000O0O000 .id ,)).find ()#line:179
        if not O0O00OOO00OOOO00O :#line:180
            return public .return_msg_gettext (False ,"This template was not found!")#line:181
        public .writeFile (O0O00OOO00OOOO00O ['path'],O00O0O0O000O0O000 .data )#line:182
        O0OOOO0O0000OOO0O =OOOO00O0OOOOO0O00 .check_conf (O0O00OOO00OOOO00O ['path'])#line:183
        if not O0OOOO0O0000OOO0O ['status']:#line:184
            return O0OOOO0O0000OOO0O #line:185
        OOOOO0OO00OOO000O ={"name":O0O00OOO00OOOO00O ['name'],"remark":O00O0O0O000O0O000 .remark ,"path":O0O00OOO00OOOO00O ['path']}#line:190
        dp .sql ("templates").where ("id=?",(O00O0O0O000O0O000 .id ,)).update (OOOOO0OO00OOO000O )#line:191
        dp .write_log ("Editing template [{}] succeeded!".format (O0O00OOO00OOOO00O ['name']))#line:192
        return public .return_msg_gettext (True ,"Modify the template successfully!")#line:193
    def get_template (O0O000OO00O0OO0O0 ,O0OOOO00O00O00OO0 ):#line:195
        ""#line:200
        OOO0OO0OO0OO0000O =dp .sql ("templates").where ("id=?",(O0OOOO00O00O00OO0 .id ,)).find ()#line:201
        if not OOO0OO0OO0OO0000O :#line:202
            return public .return_msg_gettext (False ,"This template was not found!")#line:203
        return public .return_msg_gettext (True ,public .readFile (OOO0OO0OO0OO0000O ['path']))#line:204
    def template_list (OOO00OO000O0OOO0O ,O00O0O00OOO00O000 ):#line:206
        ""#line:211
        import projectModel .bt_docker .dk_setup as ds #line:212
        OOOO0OO00OOOO0O0O =ds .main ()#line:213
        OOO0OO00OO0OO0O0O =dp .sql ("templates").select ()[::-1 ]#line:214
        if not isinstance (OOO0OO00OO0OO0O0O ,list ):#line:215
            OOO0OO00OO0OO0O0O =[]#line:216
        OOOO0O000OO0OO0O0 ={"template":OOO0OO00OO0OO0O0O ,"installed":OOOO0OO00OOOO0O0O .check_docker_program (),"service_status":OOOO0OO00OOOO0O0O .get_service_status ()}#line:221
        return public .return_msg_gettext (True ,OOOO0O000OO0OO0O0 )#line:222
    def remove_template (O0O0O0OOOOO0O000O ,OO0OO0OO00O000OOO ):#line:224
        ""#line:230
        O00OO00O0OOO0000O =dp .sql ("templates").where ("id=?",(OO0OO0OO00O000OOO .template_id ,)).find ()#line:231
        if not O00OO00O0OOO0000O :#line:232
            return public .return_msg_gettext (False ,"This template was not found!")#line:233
        if os .path .exists (O00OO00O0OOO0000O ['path']):#line:234
            os .remove (O00OO00O0OOO0000O ['path'])#line:235
        dp .sql ("templates").delete (id =OO0OO0OO00O000OOO .template_id )#line:236
        dp .write_log ("Delete template [{}] successful!".format (O00OO00O0OOO0000O ['name']))#line:237
        return public .return_msg_gettext (True ,"Successfully deleted!")#line:238
    def edit_project_remark (OOO0O0000OO000000 ,OO00000OO000OOOO0 ):#line:240
        ""#line:247
        O0OOOOOO000OOO0OO =dp .sql ("stacks").where ("id=?",(OO00000OO000OOOO0 .project_id ,)).find ()#line:248
        if not O0OOOOOO000OOO0OO :#line:249
            return public .return_msg_gettext (False ,"The item was not found!")#line:250
        OO0OOO00OO0OOO000 ={"remark":OO00000OO000OOOO0 .remark }#line:253
        dp .write_log ("Modify the item[{}] remarks [{}] to [{}] success!".format (O0OOOOOO000OOO0OO ['name'],O0OOOOOO000OOO0OO ['remark'],OO00000OO000OOOO0 .remark ))#line:254
        dp .sql ("stacks").where ("id=?",(OO00000OO000OOOO0 .project_id ,)).update (OO0OOO00OO0OOO000 )#line:255
    def edit_template_remark (O000000OOOOO0O000 ,OOOO0OOOO0O0O0OO0 ):#line:257
        ""#line:264
        OO0OO00OOOOO0OO00 =dp .sql ("templates").where ("id=?",(OOOO0OOOO0O0O0OO0 .templates_id ,)).find ()#line:265
        if not OO0OO00OOOOO0OO00 :#line:266
            return public .return_msg_gettext (False ,"The template was not found!")#line:267
        OO0O0O0OO0OOOOOOO ={"remark":OOOO0OOOO0O0O0OO0 .remark }#line:270
        dp .write_log ("Modify the template [{}] remarks [{}] to [{}] successful!".format (OO0OO00OOOOO0OO00 ['name'],OO0OO00OOOOO0OO00 ['remark'],OOOO0OOOO0O0O0OO0 .remark ))#line:271
        dp .sql ("templates").where ("id=?",(OOOO0OOOO0O0O0OO0 .templates_id ,)).update (OO0O0O0OO0OOOOOOO )#line:272
    def create_project_in_path (OO00000O0000O0O00 ,O0OO0OOOO0000OO00 ,O000O0O0O0OO00000 ):#line:274
        OO000OO000O0O00O0 ="cd {} && /usr/bin/docker-compose -p {} up -d &> {}".format ("/".join (O000O0O0O0OO00000 .split ("/")[:-1 ]),O0OO0OOOO0000OO00 ,OO00000O0000O0O00 .__O00OO0OO00O0OO000 )#line:275
        public .ExecShell (OO000OO000O0O00O0 )#line:276
    def create_project_in_file (O00OO0O0OO0OO00OO ,O0O0O0O00O000000O ,O00000O0OOOO0OOOO ):#line:278
        O0000OO0O0O000OO0 ="{}/{}".format (O00OO0O0OO0OO00OO .compose_path ,O0O0O0O00O000000O )#line:279
        O000OO00OOOOO00OO ="{}/docker-compose.yaml".format (O0000OO0O0O000OO0 )#line:280
        if not os .path .exists (O0000OO0O0O000OO0 ):#line:281
            os .makedirs (O0000OO0O0O000OO0 )#line:282
        O00OOO000O000O000 =public .readFile (O00000O0OOOO0OOOO )#line:283
        public .writeFile (O000OO00OOOOO00OO ,O00OOO000O000O000 )#line:284
        O000O0OOOO0OO0O0O ="/usr/bin/docker-compose -p {} -f {} up -d &> {}".format (O0O0O0O00O000000O ,O000OO00OOOOO00OO ,O00OO0O0OO0OO00OO .__O00OO0OO00O0OO000 )#line:285
        public .ExecShell (O000O0OOOO0OO0O0O )#line:286
    def check_project_container_name (OOOO00OO0OOOOO0OO ,OO0OOOO0O00OO0OO0 ,OOO0OO00OO0OO00OO ):#line:288
        ""#line:292
        import re #line:293
        import projectModel .bt_docker .dk_container as dc #line:294
        OO00OOOOO0O0OOOOO =[]#line:295
        O0OOOO000O00OOO0O =re .findall ("container_name\\s*:\\s*[\"\']+(.*)[\'\"]",OO0OOOO0O00OO0OO0 )#line:296
        O0O0OO0O00OOO0O00 =dc .main ().get_list (OOO0OO00OO0OO00OO )#line:297
        if not O0O0OO0O00OOO0O00 ["status"]:#line:298
            return public .return_msg_gettext (False ,"Error getting container list!")#line:299
        O0O0OO0O00OOO0O00 =O0O0OO0O00OOO0O00 ['msg']['container_list']#line:300
        for O0OOO0O0OO0O0OO00 in O0O0OO0O00OOO0O00 :#line:301
            if O0OOO0O0OO0O0OO00 ['name']in O0OOOO000O00OOO0O :#line:302
                OO00OOOOO0O0OOOOO .append (O0OOO0O0OO0O0OO00 ['name'])#line:303
        if OO00OOOOO0O0OOOOO :#line:304
            return public .return_msg_gettext (False ,"The container name in the template: <br>[{}] already exists!".format (", ".join (OO00OOOOO0O0OOOOO )))#line:305
        OO0000O0OO00OO0O0 =r"(\d+):\d+"#line:307
        O00O00OOOO0OO00O0 =re .findall (OO0000O0OO00OO0O0 ,OO0OOOO0O00OO0OO0 )#line:308
        for O0OOO00O00O0OOOOO in O00O00OOOO0OO00O0 :#line:309
            if dp .check_socket (O0OOO00O00O0OOOOO ):#line:310
                return public .return_msg_gettext (False ,"The port [{}] in the template is already in use, please modify the server port in the template!".format (O0OOO00O00O0OOOOO ))#line:311
    def create (OO0O00O0OO00O0OO0 ,O0O0O0O00OO0OOOO0 ):#line:314
        ""#line:321
        OOO00OO0O00OOOO0O =public .md5 (O0O0O0O00OO0OOOO0 .project_name )#line:322
        OO000O00O00O0000O =dp .sql ("templates").where ("id=?",(O0O0O0O00OO0OOOO0 .template_id ,)).find ()#line:323
        if not os .path .exists (OO000O00O00O0000O ['path']):#line:324
            return public .return_msg_gettext (False ,"Template file not found")#line:325
        O00O0OOOOO0OO0OOO =OO0O00O0OO00O0OO0 .check_project_container_name (public .readFile (OO000O00O00O0000O ['path']),O0O0O0O00OO0OOOO0 )#line:326
        if O00O0OOOOO0OO0OOO :#line:327
            return O00O0OOOOO0OO0OOO #line:328
        O000000O0000OOOOO =dp .sql ("stacks").where ("name=?",(OOO00OO0O00OOOO0O )).find ()#line:329
        if not O000000O0000OOOOO :#line:330
            O0OOO0OOO0O0OO0OO ={"name":O0O0O0O00OO0OOOO0 .project_name ,"status":"1","path":OO000O00O00O0000O ['path'],"template_id":O0O0O0O00OO0OOOO0 .template_id ,"time":time .time (),"remark":O0O0O0O00OO0OOOO0 .remark }#line:338
            dp .sql ("stacks").insert (O0OOO0OOO0O0OO0OO )#line:339
        else :#line:340
            return public .return_msg_gettext (False ,"This project name already exists!")#line:341
        if OO000O00O00O0000O ['add_in_path']==1 :#line:342
            OO0O00O0OO00O0OO0 .create_project_in_path (OOO00OO0O00OOOO0O ,OO000O00O00O0000O ['path'])#line:346
        else :#line:347
            OO0O00O0OO00O0OO0 .create_project_in_file (OOO00OO0O00OOOO0O ,OO000O00O00O0000O ['path'])#line:351
        dp .write_log ("Project [{}] is successfully deployed!".format (OOO00OO0O00OOOO0O ))#line:352
        return public .return_msg_gettext (True ,"Deployment succeeded!")#line:354
    def compose_project_list (OOOOOO0OO00O0OO0O ,OO0O0000O00O0O000 ):#line:370
        ""#line:373
        OO0O0000O00O0O000 .url ="unix:///var/run/docker.sock"#line:374
        O0O000O0000OOO000 =dc .main ().get_list (OO0O0000O00O0O000 )#line:375
        if not O0O000O0000OOO000 ['status']:#line:376
            return public .return_msg_gettext (False ,"Failed to get the container, maybe the docker service is not started!")#line:377
        if not O0O000O0000OOO000 ['msg']['service_status']or not O0O000O0000OOO000 ['msg']['installed']:#line:378
            OO0OOO0OO00000OO0 ={"project_list":[],"template":[],"service_status":O0O000O0000OOO000 ['msg']['service_status'],"installed":O0O000O0000OOO000 ['msg']['installed']}#line:384
            return public .return_msg_gettext (True ,OO0OOO0OO00000OO0 )#line:385
        OO000O00000O00O0O =dp .sql ("stacks").select ()#line:386
        if isinstance (OO000O00000O00O0O ,list ):#line:387
            for O0OOOO0O000O00O00 in OO000O00000O00O0O :#line:388
                OOOOOO0OO00OOOO0O =[]#line:389
                for O0000OOO000000OOO in O0O000O0000OOO000 ['msg']["container_list"]:#line:390
                    try :#line:391
                        if 'com.docker.compose.project'not in O0000OOO000000OOO ["detail"]['Config']['Labels']:#line:392
                            continue #line:393
                    except :#line:394
                        continue #line:395
                    if O0000OOO000000OOO ["detail"]['Config']['Labels']['com.docker.compose.project']==public .md5 (O0OOOO0O000O00O00 ['name']):#line:396
                        OOOOOO0OO00OOOO0O .append (O0000OOO000000OOO )#line:397
                O00OOOOO0O0OO0000 =OOOOOO0OO00OOOO0O #line:398
                O0OOOO0O000O00O00 ['container']=O00OOOOO0O0OO0000 #line:399
        else :#line:400
            OO000O00000O00O0O =[]#line:401
        OO0OOO0OO0OO00OOO =OOOOOO0OO00O0OO0O .template_list (OO0O0000O00O0O000 )#line:402
        if not OO0OOO0OO0OO00OOO ['status']:#line:403
            OO0OOO0OO0OO00OOO =list ()#line:404
        else :#line:405
            OO0OOO0OO0OO00OOO =OO0OOO0OO0OO00OOO ['msg']['template']#line:406
        OO0O0O00OOO000O0O =ds .main ()#line:407
        OO0OOO0OO00000OO0 ={"project_list":OO000O00000O00O0O ,"template":OO0OOO0OO0OO00OOO ,"service_status":OO0O0O00OOO000O0O .get_service_status (),"installed":OO0O0O00OOO000O0O .check_docker_program ()}#line:413
        return public .return_msg_gettext (True ,OO0OOO0OO00000OO0 )#line:414
    def remove (O0O0O0O0OO00OOOOO ,OOO0O00OOO0OOOO00 ):#line:417
        ""#line:422
        O0OO0OOO00O000OOO =dp .sql ("stacks").where ("id=?",(OOO0O00OOO0OOOO00 .project_id ,)).find ()#line:423
        if not O0OO0OOO00O000OOO :#line:424
            return public .return_msg_gettext (True ,"The project configuration was not found!")#line:425
        OO0000000000O000O ="/usr/bin/docker-compose -p {} -f {} down &> {}".format (public .md5 (O0OO0OOO00O000OOO ['name']),O0OO0OOO00O000OOO ['path'],O0O0O0O0OO00OOOOO .__O00OO0OO00O0OO000 )#line:426
        OO0O0OOO00O00OO00 ,O00OO00O0000000O0 =public .ExecShell (OO0000000000O000O )#line:427
        dp .sql ("stacks").delete (id =OOO0O00OOO0OOOO00 .project_id )#line:428
        dp .write_log ("Delete item [{}] succeeded!".format (O0OO0OOO00O000OOO ['name']))#line:429
        return public .return_msg_gettext (True ,"Successfully deleted!")#line:430
    def stop (O0OOO0OOOOOO00O00 ,OOOO0OOO0OO00OO00 ):#line:433
        ""#line:439
        O00O000O00OOO00O0 =dp .sql ("stacks").where ("id=?",(OOOO0OOO0OO00OO00 .project_id ,)).find ()#line:440
        if not O00O000O00OOO00O0 :#line:441
            return public .return_msg_gettext (True ,"The project configuration was not found!")#line:442
        OO0OO0OOO0O0O00O0 ="/usr/bin/docker-compose -p {} -f {} stop &> {}".format (public .md5 (O00O000O00OOO00O0 ['name']),O00O000O00OOO00O0 ['path'],O0OOO0OOOOOO00O00 .__O00OO0OO00O0OO000 )#line:444
        OO0O00O0000OOOOOO ,O0OO00000O0OO00O0 =public .ExecShell (OO0OO0OOO0O0O00O0 )#line:445
        dp .write_log ("Stop project [{}] succeeded!".format (O00O000O00OOO00O0 ['name']))#line:446
        return public .return_msg_gettext (True ,"Set up successfully!")#line:447
    def start (O000OO00OOO0000O0 ,O0000O000OO0OOOO0 ):#line:450
        ""#line:455
        OO00O000000OO00O0 =dp .sql ("stacks").where ("id=?",(O0000O000OO0OOOO0 .project_id ,)).find ()#line:456
        if not OO00O000000OO00O0 :#line:457
            return public .return_msg_gettext (False ,"The project configuration was not found!")#line:458
        O0OO000O0OOO0OO0O ="/usr/bin/docker-compose -p {} -f {} start > {}".format (public .md5 (OO00O000000OO00O0 ['name']),OO00O000000OO00O0 ['path'],O000OO00OOO0000O0 .__O00OO0OO00O0OO000 )#line:459
        O00O000OOO00O000O ,O0O00OO0OO0OO0OOO =public .ExecShell (O0OO000O0OOO0OO0O )#line:460
        dp .write_log ("Startup project [{}] succeeded!".format (OO00O000000OO00O0 ['name']))#line:461
        return public .return_msg_gettext (True ,"Set up successfully!")#line:462
    def restart (O0OO00OO0O0OOO00O ,O000OOOOOOO00O0OO ):#line:465
        ""#line:470
        OO000OOOOO0OO0O0O =dp .sql ("stacks").where ("id=?",(O000OOOOOOO00O0OO .project_id ,)).find ()#line:471
        if not OO000OOOOO0OO0O0O :#line:472
            return public .return_msg_gettext (True ,"The project configuration was not found!")#line:473
        O00O00O000OO00O0O ="/usr/bin/docker-compose -p {} -f {} restart &> {}".format (public .md5 (OO000OOOOO0OO0O0O ['name']),OO000OOOOO0OO0O0O ['path'],O0OO00OO0O0OOO00O .__O00OO0OO00O0OO000 )#line:474
        O00OO0000O0000OO0 ,O0OOOOO000OO0O0O0 =public .ExecShell (O00O00O000OO00O0O )#line:475
        dp .write_log ("Restart the project [{}] successfully!".format (OO000OOOOO0OO0O0O ['name']))#line:476
        return public .return_msg_gettext (True ,"Set up successfully!")#line:477
    def pull (OOO0OO00O0OO00OO0 ,OO0OOOOOO00000OO0 ):#line:480
        ""#line:485
        O0OO0OO0OO0O0OOO0 =dp .sql ("templates").where ("id=?",(OO0OOOOOO00000OO0 .template_id ,)).find ()#line:486
        if not O0OO0OO0OO0O0OOO0 :#line:487
            return public .return_msg_gettext (True ,"The template was not found!")#line:488
        O0OOOO0O000O0O000 ="/usr/bin/docker-compose -p {} -f {} pull &> {}".format (O0OO0OO0OO0O0OOO0 ['name'],O0OO0OO0OO0O0OOO0 ['path'],OOO0OO00O0OO00OO0 .__O00OO0OO00O0OO000 )#line:489
        O0O00OOO0O0O0OO00 ,OO000OOO0O000OOO0 =public .ExecShell (O0OOOO0O000O0O000 )#line:490
        dp .write_log ("The mirror image of the template [{}] was pulled successfully!".format (O0OO0OO0OO0O0OOO0 ['name']))#line:491
        return public .return_msg_gettext (True ,"Pull success!")#line:492
    def pause (OOO00O0OO00O00O0O ,O0OOOOO000OO0000O ):#line:495
        ""#line:500
        OO0O0000OOO000O00 =dp .sql ("stacks").where ("id=?",(O0OOOOO000OO0000O .project_id ,)).find ()#line:501
        if not OO0O0000OOO000O00 :#line:502
            return public .return_msg_gettext (True ,"The project configuration was not found!")#line:503
        O0O0OOO0000O0O00O ="/usr/bin/docker-compose -p {} -f {} pause &> {}".format (public .md5 (OO0O0000OOO000O00 ['name']),OO0O0000OOO000O00 ['path'],OOO00O0OO00O00O0O .__O00OO0OO00O0OO000 )#line:504
        O0000OO0OOO00OOOO ,O0O0O0OOO0O0O0OOO =public .ExecShell (O0O0OOO0000O0O00O )#line:505
        dp .write_log ("Pause [{}] success!".format (OO0O0000OOO000O00 ['name']))#line:506
        return public .return_msg_gettext (True ,"Set up successfully!")#line:507
    def unpause (O0O0O0OOO00OOOO00 ,O0O00O000OOO00OO0 ):#line:510
        ""#line:515
        OO0O0OO00OOO00O00 =dp .sql ("stacks").where ("id=?",(O0O00O000OOO00OO0 .project_id ,)).find ()#line:516
        if not OO0O0OO00OOO00O00 :#line:517
            return public .return_msg_gettext (True ,"The project configuration was not found!")#line:518
        OOO00O00OOOO0OO00 ="/usr/bin/docker-compose -p {} -f {} unpause &> {}".format (public .md5 (OO0O0OO00OOO00O00 ['name']),OO0O0OO00OOO00O00 ['path'],O0O0O0OOO00OOOO00 .__O00OO0OO00O0OO000 )#line:519
        O00000OOO000OOO0O ,O00OO00O0O0O00OO0 =public .ExecShell (OOO00O00OOOO0OO00 )#line:520
        dp .write_log ("Unsuspended project [{}] succeeded!".format (OO0O0OO00OOO00O00 ['name']))#line:521
        return public .return_msg_gettext (True ,"Set up successfully!")#line:522
    def scan_compose_file (OOO000OO000OOOOOO ,O00000OOO00O00OOO ,O000O00O0OOO0O0OO ):#line:525
        ""#line:531
        O0OOOO0O00OOO00O0 =os .listdir (O00000OOO00O00OOO )#line:532
        for OO00000OOO00OOOO0 in O0OOOO0O00OOO00O0 :#line:533
            OO0O0OO00OO0OO000 =os .path .join (O00000OOO00O00OOO ,OO00000OOO00OOOO0 )#line:534
            if os .path .isdir (OO0O0OO00OO0OO000 ):#line:536
                OOO000OO000OOOOOO .scan_compose_file (OO0O0OO00OO0OO000 ,O000O00O0OOO0O0OO )#line:537
            else :#line:538
                if OO00000OOO00OOOO0 =="docker-compose.yaml"or OO00000OOO00OOOO0 =="docker-compose.yam"or OO00000OOO00OOOO0 =="docker-compose.yml":#line:539
                    if "/www/server/panel/data/compose"in OO0O0OO00OO0OO000 :#line:540
                        continue #line:541
                    O000O00O0OOO0O0OO .append (OO0O0OO00OO0OO000 )#line:542
        return O000O00O0OOO0O0OO #line:543
    def get_compose_project (OOO000O00OO000OO0 ,O0OOOO0OOOOO0000O ):#line:546
        ""#line:552
        O0O0OO00OO0000O0O =list ()#line:553
        if O0OOOO0OOOOO0000O .path =="/":#line:554
            return public .return_msg_gettext (False ,"Can't start scanning from root directory!")#line:555
        if O0OOOO0OOOOO0000O .path [-1 ]=="/":#line:556
            O0OOOO0OOOOO0000O .path =O0OOOO0OOOOO0000O .path [:-1 ]#line:557
        if str (O0OOOO0OOOOO0000O .sub_dir )=="1":#line:558
            O000OOOO0OO00OOOO =OOO000O00OO000OO0 .scan_compose_file (O0OOOO0OOOOO0000O .path ,O0O0OO00OO0000O0O )#line:559
            if not O000OOOO0OO00OOOO :#line:560
                O000OOOO0OO00OOOO =[]#line:561
            else :#line:562
                O00O0O0OOO0OO0O00 =list ()#line:563
                for O0O00O0O0OOOO000O in O000OOOO0OO00OOOO :#line:564
                    O00O0O0OOO0OO0O00 .append ({"project_name":O0O00O0O0OOOO000O .split ("/")[-2 ],"conf_file":"/".join (O0O00O0O0OOOO000O .split ("/")),"remark":"Add by local path"})#line:571
                O000OOOO0OO00OOOO =O00O0O0OOO0OO0O00 #line:572
        else :#line:573
            O00O0O00O00O0000O ="{}/docker-compose.yaml".format (O0OOOO0OOOOO0000O .path )#line:574
            OOO00OOO00O0O0OOO ="{}/docker-compose.yam".format (O0OOOO0OOOOO0000O .path )#line:575
            if os .path .exists (O00O0O00O00O0000O ):#line:576
                O000OOOO0OO00OOOO =[{"project_name":O0OOOO0OOOOO0000O .path .split ("/")[-1 ],"conf_file":O00O0O00O00O0000O ,"remark":"Add by local path"}]#line:581
            elif os .path .exists (OOO00OOO00O0O0OOO ):#line:582
                O000OOOO0OO00OOOO =[{"project_name":O0OOOO0OOOOO0000O .path .split ("/")[-1 ],"conf_file":OOO00OOO00O0O0OOO ,"remark":"Add by local path"}]#line:587
            else :#line:588
                O000OOOO0OO00OOOO =list ()#line:589
        return O000OOOO0OO00OOOO #line:591
    def add_template_in_path (O0O00000O0OO00OO0 ,OOO0OO0OO0O00O00O ):#line:594
        ""#line:599
        OO0O000OO000O0OO0 =dict ()#line:600
        OO00OOO00000OOOOO =dict ()#line:601
        for OO0OO0OOO00O0OO00 in OOO0OO0OO0O00O00O .template_list :#line:602
            O0O0OO00O00O00000 =OO0OO0OOO00O0OO00 ['conf_file']#line:603
            O00O000OOOO0O00OO =OO0OO0OOO00O0OO00 ['project_name']#line:604
            OOOOO00O00O0O0OO0 =OO0OO0OOO00O0OO00 ['remark']#line:605
            O00O0O0O000O00O00 =O0O00000O0OO00OO0 .template_list (OOO0OO0OO0O00O00O )['msg']['template']#line:606
            for O00O0O0OOO0O0OOOO in O00O0O0O000O00O00 :#line:607
                if O00O000OOOO0O00OO ==O00O0O0OOO0O0OOOO ['name']:#line:608
                    OO0O000OO000O0OO0 [O00O000OOOO0O00OO ]="Template already exists!"#line:609
                    continue #line:610
            if not os .path .exists (O0O0OO00O00O00000 ):#line:612
                OO0O000OO000O0OO0 [O00O000OOOO0O00OO ]="The template was not found!"#line:613
                continue #line:614
            O000O0O0OOO00000O =O0O00000O0OO00OO0 .check_conf (O0O0OO00O00O00000 )#line:616
            if not O000O0O0OOO00000O ['status']:#line:617
                OO0O000OO000O0OO0 [O00O000OOOO0O00OO ]="Template validation failed, possibly malformed!"#line:618
                continue #line:619
            OO0OOO0OOOOO0O00O ={"name":O00O000OOOO0O00OO ,"remark":OOOOO00O00O0O0OO0 ,"path":O0O0OO00O00O00000 ,"add_in_path":1 }#line:626
            print (OO0OOO0OOOOO0O00O )#line:627
            dp .sql ("templates").insert (OO0OOO0OOOOO0O00O )#line:628
            OO00OOO00000OOOOO [O00O000OOOO0O00OO ]="Template added successfully!"#line:629
        print (OO0O000OO000O0OO0 )#line:631
        for O00O0O0OOO0O0OOOO in OO0O000OO000O0OO0 :#line:632
            if O00O0O0OOO0O0OOOO in OO00OOO00000OOOOO :#line:633
                del (OO00OOO00000OOOOO [O00O0O0OOO0O0OOOO ])#line:634
            else :#line:635
                dp .write_log ("Add template [{}] from path successfully!".format (O00O0O0OOO0O0OOOO ))#line:636
        if not OO0O000OO000O0OO0 and OO00OOO00000OOOOO :#line:637
            return {'status':True ,'msg':'Add template successfully: [{}]'.format (','.join (OO00OOO00000OOOOO ))}#line:638
        elif not OO00OOO00000OOOOO and OO0O000OO000O0OO0 :#line:639
            return {'status':True ,'msg':'Failed to add template: template name already exists or format validation error [{}]'.format (','.join (OO0O000OO000O0OO0 ))}#line:640
        return {'status':True ,'msg':'Add template successfully: [{}]<br>Add template failed: template name already exists or format validation error [{}]'.format (','.join (OO00OOO00000OOOOO ),','.join (OO0O000OO000O0OO0 ))}#line:641
