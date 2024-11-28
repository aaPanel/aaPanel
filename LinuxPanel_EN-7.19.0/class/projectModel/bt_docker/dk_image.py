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
import os #line:13
import public #line:14
import docker .errors #line:15
import projectModel .bt_docker .dk_public as dp #line:16
class main :#line:18
    __O000O000OOOO0OO00 ='/tmp/dockertmp.log'#line:19
    def docker_client (O0O0OOO00O0000O0O ,OOOO0O000O000OO00 ):#line:20
        import projectModel .bt_docker .dk_public as dp #line:21
        return dp .docker_client (OOOO0O000O000OO00 )#line:22
    def save (O0O000OO0O0O00OO0 ,OOOO0000OO0O0OOOO ):#line:25
        ""#line:33
        try :#line:34
            if "tar"in OOOO0000OO0O0OOOO .name :#line:35
                O00OOOO00OO0OO0OO ='{}/{}'.format (OOOO0000OO0O0OOOO .path ,OOOO0000OO0O0OOOO .name )#line:36
            else :#line:37
                O00OOOO00OO0OO0OO ='{}/{}.tar'.format (OOOO0000OO0O0OOOO .path ,OOOO0000OO0O0OOOO .name )#line:38
            if not os .path .exists (OOOO0000OO0O0OOOO .path ):#line:39
                os .makedirs (OOOO0000OO0O0OOOO .path )#line:40
            public .writeFile (O00OOOO00OO0OO0OO ,"")#line:41
            O0000O0OOOOO000OO =open (O00OOOO00OO0OO0OO ,'wb')#line:42
            O000OOOOOO00OOO00 =O0O000OO0O0O00OO0 .docker_client (OOOO0000OO0O0OOOO .url ).images .get (OOOO0000OO0O0OOOO .id )#line:43
            for OO0O0O0O0O0OO0OOO in O000OOOOOO00OOO00 .save (named =True ):#line:44
                O0000O0OOOOO000OO .write (OO0O0O0O0O0OO0OOO )#line:45
            O0000O0OOOOO000OO .close ()#line:46
            dp .write_log ("Image [{}] exported to [{}] successfully!".format (OOOO0000OO0O0OOOO .id ,O00OOOO00OO0OO0OO ))#line:47
            return public .returnMsg (True ,"Saved successfully to: {}".format (O00OOOO00OO0OO0OO ))#line:48
        except docker .errors .APIError as OOOO000OOO0O000O0 :#line:49
            if "empty export - not implemented"in str (OOOO000OOO0O000O0 ):#line:50
                return public .returnMsg (False ,"Empty images cannot be exported!")#line:51
            return public .get_error_info ()#line:52
    def load (OOO000O000OOOOOO0 ,O00OO0OOOO000O000 ):#line:55
        ""#line:60
        OOOOO000O000O0000 =OOO000O000OOOOOO0 .docker_client (O00OO0OOOO000O000 .url ).images #line:61
        with open (O00OO0OOOO000O000 .path ,'rb')as OO00O0O00000000O0 :#line:62
            OOOOO000O000O0000 .load (OO00O0O00000000O0 )#line:65
        dp .write_log ("Image [{}] imported successfully!".format (O00OO0OOOO000O000 .path ))#line:66
        return public .returnMsg (True ,"Import successful! {}".format (O00OO0OOOO000O000 .path ))#line:67
    def image_list (OO0O0OOO0OOOOO00O ,OO0O0OO000O0OOOOO ):#line:70
        ""#line:75
        import projectModel .bt_docker .dk_registry as dr #line:76
        import projectModel .bt_docker .dk_setup as ds #line:77
        OOO00000OOO00000O =list ()#line:78
        OO0OO00OOOO0O0O00 =OO0O0OOO0OOOOO00O .docker_client (OO0O0OO000O0OOOOO .url )#line:79
        OO0OOO00OOO0O0OO0 =ds .main ()#line:80
        O0OO0000O0O0O00O0 =OO0OOO00OOO0O0OO0 .check_docker_program ()#line:81
        O00OOO0000OO0O0OO =OO0OOO00OOO0O0OO0 .get_service_status ()#line:82
        if not OO0OO00OOOO0O0O00 :#line:83
            OOO00000OOO00000O ={"images_list":[],"registry_list":[],"installed":O0OO0000O0O0O00O0 ,"service_status":O00OOO0000OO0O0OO }#line:89
            return public .returnMsg (True ,OOO00000OOO00000O )#line:90
        OOOO000O0OO00O00O =OO0OO00OOOO0O0O00 .images #line:91
        OO0OO0OO000OOO000 =OO0O0OOO0OOOOO00O .get_image_attr (OOOO000O0OO00O00O )#line:92
        OO000O0OO000O0000 =dr .main ().registry_list (OO0O0OO000O0OOOOO )#line:93
        if OO000O0OO000O0000 ['status']:#line:94
            OO000O0OO000O0000 =OO000O0OO000O0000 ['msg']['registry']#line:95
        else :#line:96
            OO000O0OO000O0000 =[]#line:97
        for OO0O0O000000O00O0 in OO0OO0OO000OOO000 :#line:98
            if len (OO0O0O000000O00O0 ['RepoTags'])==1 :#line:99
                O0O0O0O0000OO0O00 ={"id":OO0O0O000000O00O0 ["Id"],"tags":OO0O0O000000O00O0 ["RepoTags"],"time":OO0O0O000000O00O0 ["Created"],"name":OO0O0O000000O00O0 ['RepoTags'][0 ],"size":OO0O0O000000O00O0 ["Size"],"detail":OO0O0O000000O00O0 }#line:107
                OOO00000OOO00000O .append (O0O0O0O0000OO0O00 )#line:108
            elif len (OO0O0O000000O00O0 ['RepoTags'])>1 :#line:109
                for O0OO0O0O00O000O0O in range (len (OO0O0O000000O00O0 ['RepoTags'])):#line:110
                    O0O0O0O0000OO0O00 ={"id":OO0O0O000000O00O0 ["Id"],"tags":OO0O0O000000O00O0 ["RepoTags"],"time":OO0O0O000000O00O0 ["Created"],"name":OO0O0O000000O00O0 ['RepoTags'][O0OO0O0O00O000O0O ],"size":OO0O0O000000O00O0 ["Size"],"detail":OO0O0O000000O00O0 }#line:118
                    OOO00000OOO00000O .append (O0O0O0O0000OO0O00 )#line:119
            elif not OO0O0O000000O00O0 ['RepoTags']:#line:120
                O0O0O0O0000OO0O00 ={"id":OO0O0O000000O00O0 ["Id"],"tags":OO0O0O000000O00O0 ["RepoTags"],"time":OO0O0O000000O00O0 ["Created"],"name":OO0O0O000000O00O0 ["Id"],"size":OO0O0O000000O00O0 ["Size"],"detail":OO0O0O000000O00O0 }#line:128
                OOO00000OOO00000O .append (O0O0O0O0000OO0O00 )#line:129
        OOO00000OOO00000O ={"images_list":OOO00000OOO00000O ,"registry_list":OO000O0OO000O0000 ,"installed":O0OO0000O0O0O00O0 ,"service_status":O00OOO0000OO0O0OO }#line:135
        return public .returnMsg (True ,OOO00000OOO00000O )#line:136
    def get_image_attr (O00OOOO0O00OOO00O ,O000O00OOOOOOO000 ):#line:138
        OOO00O0O00OO00OO0 =O000O00OOOOOOO000 .list ()#line:139
        return [OO0000OOO0OO0O0OO .attrs for OO0000OOO0OO0O0OO in OOO00O0O00OO00OO0 ]#line:140
    def get_logs (OO000O0O000000O0O ,OOOO000000O000O0O ):#line:142
        import files #line:143
        O0O0O0O0O0OOOOOO0 =OOOO000000O000O0O .logs_file #line:144
        return public .returnMsg (True ,files .files ().GetLastLine (O0O0O0O0O0OOOOOO0 ,20 ))#line:145
    def build (OOOO0OOO00O000O0O ,O00O0OOO00O00O0O0 ):#line:148
        ""#line:156
        public .writeFile (OOOO0OOO00O000O0O .__O000O000OOOO0OO00 ,"Start building images!")#line:157
        public .writeFile ('/tmp/dockertmp.log',"Start building the mirror")#line:158
        if not hasattr (O00O0OOO00O00O0O0 ,"pull"):#line:159
            O00O0OOO00O00O0O0 .pull =False #line:160
        if hasattr (O00O0OOO00O00O0O0 ,"data")and O00O0OOO00O00O0O0 .data :#line:161
            O00O0OOO00O00O0O0 .path ="/tmp/dockerfile"#line:162
            public .writeFile (O00O0OOO00O00O0O0 .path ,O00O0OOO00O00O0O0 .data )#line:163
            with open (O00O0OOO00O00O0O0 .path ,'rb')as OOO000000O000OOOO :#line:164
                OO000OOOO0O0OO0O0 ,O000OOO0O0OOOO00O =OOOO0OOO00O000O0O .docker_client (O00O0OOO00O00O0O0 .url ).images .build (pull =True if O00O0OOO00O00O0O0 .pull =="1"else False ,fileobj =OOO000000O000OOOO ,tag =O00O0OOO00O00O0O0 .tag )#line:169
            os .remove (O00O0OOO00O00O0O0 .path )#line:170
        else :#line:171
            if not os .path .isdir (O00O0OOO00O00O0O0 .path ):#line:172
                O00O0OOO00O00O0O0 .path ='/'.join (O00O0OOO00O00O0O0 .path .split ('/')[:-1 ])#line:173
            OO000OOOO0O0OO0O0 ,O000OOO0O0OOOO00O =OOOO0OOO00O000O0O .docker_client (O00O0OOO00O00O0O0 .url ).images .build (pull =True if O00O0OOO00O00O0O0 .pull =="1"else False ,path =O00O0OOO00O00O0O0 .path ,tag =O00O0OOO00O00O0O0 .tag )#line:178
        dp .log_docker (O000OOO0O0OOOO00O ,"Docker build tasks")#line:180
        dp .write_log ("Building image [{}] succeeded!".format (O00O0OOO00O00O0O0 .tag ))#line:181
        return public .returnMsg (True ,"Building image successfully!")#line:182
    def remove (OOOOO00000OO0OO0O ,O0000O000000OOO00 ):#line:185
        ""#line:193
        try :#line:194
            OOOOO00000OO0OO0O .docker_client (O0000O000000OOO00 .url ).images .remove (O0000O000000OOO00 .name )#line:195
            dp .write_log ("Delete mirror【{}】successful!".format (O0000O000000OOO00 .name ))#line:196
            return public .returnMsg (True ,"Mirror deleted successfully!")#line:197
        except docker .errors .ImageNotFound as OOO00OOOO00OOO0O0 :#line:198
            return public .returnMsg (False ,"Failed to delete the mirror, maybe the mirror does not exist!")#line:199
        except docker .errors .APIError as OOO00OOOO00OOO0O0 :#line:200
            if "image is referenced in multiple repositories"in str (OOO00OOOO00OOO0O0 ):#line:201
                return public .returnMsg (False ,"The image ID is used in multiple images, please check [Force Delete]!")#line:202
            if "using its referenced image"in str (OOO00OOOO00OOO0O0 ):#line:203
                return public .returnMsg (False ,"The image is in use, please delete the container and then delete it!")#line:204
            return public .returnMsg (False ,"Delete mirror failed!<br> {}".format (OOO00OOOO00OOO0O0 ))#line:205
    def pull_from_some_registry (O00OOOOOOOOO00000 ,O0O0O0OOO0O0OO0O0 ):#line:208
        ""#line:215
        import projectModel .bt_docker .dk_registry as br #line:216
        O00O00OO00OOOOO00 =br .main ().registry_info (O0O0O0OOO0O0OO0O0 .name )#line:217
        O0000OO00OO0OO000 =br .main ().login (O0O0O0OOO0O0OO0O0 .url ,O00O00OO00OOOOO00 ['url'],O00O00OO00OOOOO00 ['username'],O00O00OO00OOOOO00 ['password'])['status']#line:218
        if not O0000OO00OO0OO000 :#line:219
            return O0000OO00OO0OO000 #line:220
        O0O0O0OOO0O0OO0O0 .username =O00O00OO00OOOOO00 ['username']#line:221
        O0O0O0OOO0O0OO0O0 .password =O00O00OO00OOOOO00 ['password']#line:222
        O0O0O0OOO0O0OO0O0 .registry =O00O00OO00OOOOO00 ['url']#line:223
        O0O0O0OOO0O0OO0O0 .namespace =O00O00OO00OOOOO00 ['namespace']#line:224
        return O00OOOOOOOOO00000 .pull (O0O0O0OOO0O0OO0O0 )#line:225
    def push (OO0O0OOO0O0O00O0O ,OO000OOO0OO000O0O ):#line:228
        ""#line:236
        if "/"in OO000OOO0OO000O0O .tag :#line:237
            return public .returnMsg (False ,"The pushed image name cannot contain the symbol [/] , please use the following format: image:v1 (image_name:version_number)")#line:238
        if ":"not in OO000OOO0OO000O0O .tag :#line:239
            return public .returnMsg (False ,"The pushed image name must contain the symbol [ : ] , please use the following format: image:v1 (image_name:version_number)")#line:240
        public .writeFile (OO0O0OOO0O0O00O0O .__O000O000OOOO0OO00 ,"Start pushing mirrors!\n")#line:241
        import projectModel .bt_docker .dk_registry as br #line:242
        O00O0O0O0O0O0O000 =br .main ().registry_info (OO000OOO0OO000O0O .name )#line:243
        if OO000OOO0OO000O0O .name =="docker official"and O00O0O0O0O0O0O000 ['url']=="docker.io":#line:244
            public .writeFile (OO0O0OOO0O0O00O0O .__O000O000OOOO0OO00 ,"The image cannot be pushed to the Docker public repository!\n")#line:245
            return public .returnMsg (False ,"Unable to push to Docker public repo!")#line:246
        O0O0000OOO0OOO00O =br .main ().login (OO000OOO0OO000O0O .url ,O00O0O0O0O0O0O000 ['url'],O00O0O0O0O0O0O000 ['username'],O00O0O0O0O0O0O000 ['password'])['status']#line:247
        O00OOO0O0O0O0O0O0 =OO000OOO0OO000O0O .tag #line:248
        if not O0O0000OOO0OOO00O :#line:249
            return O0O0000OOO0OOO00O #line:250
        OO00O0000000OO000 ={"username":O00O0O0O0O0O0O000 ['username'],"password":O00O0O0O0O0O0O000 ['password'],"registry":O00O0O0O0O0O0O000 ['url']}#line:254
        if ":"not in O00OOO0O0O0O0O0O0 :#line:256
            O00OOO0O0O0O0O0O0 ="{}:latest".format (O00OOO0O0O0O0O0O0 )#line:257
        OOOO000OOOOO0O00O =O00O0O0O0O0O0O000 ['url']#line:258
        O0OO00O0OO000O0OO ="{}/{}/{}".format (OOOO000OOOOO0O00O ,O00O0O0O0O0O0O000 ['namespace'],OO000OOO0OO000O0O .tag )#line:259
        OO0O0OOO0O0O00O0O .tag (OO000OOO0OO000O0O .url ,OO000OOO0OO000O0O .id ,O0OO00O0OO000O0OO )#line:260
        O000OOOO00O0OO000 =OO0O0OOO0O0O00O0O .docker_client (OO000OOO0OO000O0O .url ).images .push (repository =O0OO00O0OO000O0OO .split (":")[0 ],tag =O00OOO0O0O0O0O0O0 .split (":")[-1 ],auth_config =OO00O0000000OO000 ,stream =True )#line:266
        dp .log_docker (O000OOOO00O0OO000 ,"Image push task")#line:267
        OO000OOO0OO000O0O .name =O0OO00O0OO000O0OO #line:269
        OO0O0OOO0O0O00O0O .remove (OO000OOO0OO000O0O )#line:270
        dp .write_log ("The image [{}] was pushed successfully!".format (O0OO00O0OO000O0OO ))#line:271
        return public .returnMsg (True ,"推送成功！{}".format (str (O000OOOO00O0OO000 )))#line:272
    def tag (OOO0OO00OO0OO0O00 ,O000O0OOO00O000OO ,OOOO0O0OOO0000O00 ,OO0O0000OO00O00O0 ):#line:274
        ""#line:281
        OOO000O000000OOO0 =OO0O0000OO00O00O0 .split (":")[0 ]#line:282
        O00OOO0OOOO0O000O =OO0O0000OO00O00O0 .split (":")[1 ]#line:283
        OOO0OO00OO0OO0O00 .docker_client (O000O0OOO00O000OO ).images .get (OOOO0O0OOO0000O00 ).tag (repository =OOO000O000000OOO0 ,tag =O00OOO0OOOO0O000O )#line:287
        return public .returnMsg (True ,"Set successfully")#line:288
    def pull (O0O0O0000OOOOOOO0 ,OO00OOO00OO000O00 ):#line:290
        ""#line:299
        public .writeFile (O0O0O0000OOOOOOO0 .__O000O000OOOO0OO00 ,"Start pulling images!")#line:300
        import docker .errors #line:301
        try :#line:302
            if ':'not in OO00OOO00OO000O00 .image :#line:303
                OO00OOO00OO000O00 .image ='{}:latest'.format (OO00OOO00OO000O00 .image )#line:304
            O0O00OO000O000OO0 ={"username":OO00OOO00OO000O00 .username ,"password":OO00OOO00OO000O00 .password ,"registry":OO00OOO00OO000O00 .registry if OO00OOO00OO000O00 .registry else None }if OO00OOO00OO000O00 .username else None #line:308
            if not hasattr (OO00OOO00OO000O00 ,"tag"):#line:309
                OO00OOO00OO000O00 .tag =OO00OOO00OO000O00 .image .split (":")[-1 ]#line:310
            if OO00OOO00OO000O00 .registry !="docker.io":#line:311
                OO00OOO00OO000O00 .image ="{}/{}/{}".format (OO00OOO00OO000O00 .registry ,OO00OOO00OO000O00 .namespace ,OO00OOO00OO000O00 .image )#line:312
            OOO0OOOO000O000O0 =dp .docker_client_low (OO00OOO00OO000O00 .url ).pull (repository =OO00OOO00OO000O00 .image ,auth_config =O0O00OO000O000OO0 ,tag =OO00OOO00OO000O00 .tag ,stream =True )#line:318
            dp .log_docker (OOO0OOOO000O000O0 ,"Image pull task")#line:319
            if OOO0OOOO000O000O0 :#line:320
                dp .write_log ("The image [{}:{}] was pulled successfully!".format (OO00OOO00OO000O00 .image ,OO00OOO00OO000O00 .tag ))#line:321
                return public .returnMsg (True ,'Pulling the image succeeded.')#line:322
            else :#line:323
                return public .returnMsg (False ,'There may not be this image.')#line:324
        except docker .errors .ImageNotFound as O0O0OO00OO000O0O0 :#line:325
            if "pull access denied for"in str (O0O0OO00OO000O0O0 ):#line:326
                return public .returnMsg (False ,"The pull failed, the image is a private image, you need to enter the account password of dockerhub!")#line:327
            return public .returnMsg (False ,"Pull failed<br><br>reasons: {}".format (O0O0OO00OO000O0O0 ))#line:329
        except docker .errors .NotFound as O0O0OO00OO000O0O0 :#line:331
            if "not found: manifest unknown"in str (O0O0OO00OO000O0O0 ):#line:332
                return public .returnMsg (False ,"The pull failed, the repository does not have the mirror!")#line:333
            return public .returnMsg (False ,"Pull failed<br><br>reason:{}".format (O0O0OO00OO000O0O0 ))#line:334
        except docker .errors .APIError as O0O0OO00OO000O0O0 :#line:335
            if "invalid tag format"in str (O0O0OO00OO000O0O0 ):#line:336
                return public .returnMsg (False ,"The pull failed, the image format is wrong, the format should be: nginx:v 1!")#line:337
            return public .returnMsg (False ,"Pull failed!{}".format (O0O0OO00OO000O0O0 ))#line:338
    def pull_high_api (OO0O0O0O000O000O0 ,O0000O0O000O0O0O0 ):#line:342
        ""#line:351
        import docker .errors #line:352
        try :#line:353
            if ':'not in O0000O0O000O0O0O0 .image :#line:354
                O0000O0O000O0O0O0 .image ='{}:latest'.format (O0000O0O000O0O0O0 .image )#line:355
            O0O0O00O0O0O00000 ={"username":O0000O0O000O0O0O0 .username ,"password":O0000O0O000O0O0O0 .password ,"registry":O0000O0O000O0O0O0 .registry if O0000O0O000O0O0O0 .registry else None }if O0000O0O000O0O0O0 .username else None #line:359
            if O0000O0O000O0O0O0 .registry !="docker.io":#line:361
                O0000O0O000O0O0O0 .image ="{}/{}/{}".format (O0000O0O000O0O0O0 .registry ,O0000O0O000O0O0O0 .namespace ,O0000O0O000O0O0O0 .image )#line:362
            OOOOOOOO0O0OOOO0O =OO0O0O0O000O000O0 .docker_client (O0000O0O000O0O0O0 .url ).images .pull (repository =O0000O0O000O0O0O0 .image ,auth_config =O0O0O00O0O0O00000 ,)#line:366
            if OOOOOOOO0O0OOOO0O :#line:367
                return public .returnMsg (True ,'Pulling the image succeeded.')#line:368
            else :#line:369
                return public .returnMsg (False ,'There may not be this mirror.')#line:370
        except docker .errors .ImageNotFound as O0O0O0OOO0O0OO0OO :#line:371
            if "pull access denied for"in str (O0O0O0OOO0O0OO0OO ):#line:372
                return public .returnMsg (False ,"The pull failed, the image is a private image, you need to enter the account password of dockerhub!")#line:373
            return public .returnMsg (False ,"Pull failed<br><br>reason: {}".format (O0O0O0OOO0O0OO0OO ))#line:374
    def image_for_host (O00O0O0O000OOO0O0 ,O000OO0OOOOO000O0 ):#line:376
        ""#line:381
        O00O000OO0OO000OO =O00O0O0O000OOO0O0 .image_list (O000OO0OOOOO000O0 )#line:382
        if not O00O000OO0OO000OO ['status']:#line:383
            return O00O000OO0OO000OO #line:384
        OO000O0000O000000 =len (O00O000OO0OO000OO ['msg']['images_list'])#line:385
        O0OOOO0OO000OO0OO =0 #line:386
        for OO00OOO0000OO0O00 in O00O000OO0OO000OO ['msg']['images_list']:#line:387
            O0OOOO0OO000OO0OO +=OO00OOO0000OO0O00 ['size']#line:388
        return public .returnMsg (True ,{'num':OO000O0000O000000 ,'size':O0OOOO0OO000OO0OO })