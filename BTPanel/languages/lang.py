#coding: utf-8

import os
import sys
import json
import re
import time
import random
import json
from hashlib import md5

try:
    from googletrans import Translator
except ImportError:
    print("未安装 googletrans==4.0.0-rc1，正在安装...")
    os.system('btpip install googletrans==4.0.0-rc1')
    from googletrans import Translator

try:
    import requests
except ImportError:
    print("未安装 requests，正在安装...")
    os.system('btpip install requests')
    import requests



# 解决 Windows 下编码问题，强制使用 utf-8 编码
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8')

# 百度翻译
class baidu_translate:
    endpoint = 'http://api.fanyi.baidu.com'
    path = '/api/trans/vip/translate'
    url = endpoint + path
    appid = ''
    appkey = ''
    # todo
    # from_lang = 'zh'
    from_lang = 'en'

    def make_md5(self,s, encoding='utf-8'):
        '''
            @name 生成md5
            @param s 字符串
            @param encoding 编码
            @return string
        '''
        return md5(s.encode(encoding)).hexdigest()
    

    def translate(self, query, to_lang='en'):
        '''
            @name 调用百度翻译API
            @param query 原文
            @param to_lang 目标语言
            @return dict
        '''
        salt = random.randint(32768, 65536)
        sign = self.make_md5(self.appid + query + str(salt) + self.appkey)

        headers = {'Content-Type': 'application/x-www-form-urlencoded'}

        payload = {'appid': self.appid, 'q': query, 'from': self.from_lang, 'to': to_lang, 'salt': salt, 'sign': sign}

        r = requests.post(self.url, params=payload, headers=headers)
        result = r.json()
        return result
    

    def google(self,text,dest,src):
        '''
            @name 调用googletrans API
            @param text 原文
            @param dest 目标语言
            @param src 源语言
            @return string
        '''
        print('原文:',text,'目标语言:',dest)
        translater = Translator()
        result = translater.translate(text, dest, src)
        return result.text  



class Lang:
    client_extension = [".json",".js",".ts",".html",".css",".sh",".vue"]    # 前端文件后缀
    server_extension = [".py"]                                              # 后端文件后缀
    server_path = ['class', 'class_v2', 'plugin', 'mod']                    # 后端代码 目录
    # client_path = "../BTPanel"
    exec_path = '/www/server/panel/BTPanel/languages'                       # 语言包目录
    panel_path = '/www/server/panel'                                        # 项目目录



    def get_files(self, path, mark='client'):
        '''
            @name 获取指定目录下的文件列表
            @param path 目录
            @param mark 标记 区分前端与后端   前端 'client'  后端 'server'
            @return list
        '''
        files = []
        for root, dirs, file in os.walk(path):
            for f in file:
                if root.find('node_modules') != -1:
                    continue
                if mark == 'client':
                    for ext in self.client_extension:
                        if f.endswith(ext):
                            files.append(os.path.join(root, f))
                else:
                    for ext in self.server_extension:
                        if f.endswith(ext):
                            files.append(os.path.join(root, f))
        return files
    
    def read_file(self,filename):
        '''
            @name 读取文件
            @param filename 文件名
            @return any
        '''
        with open(filename, "r",encoding="utf-8") as file:
            fbody = file.read()
            return fbody
    
    def write_file(self,filename, body):
        '''
            @name 写入文件
            @param filename 文件名
            @param body 内容
        '''
        with open(filename, "w",encoding="utf-8") as file:
            file.write(body)
    
    def get_lang(self, body):
        '''
            @name 解析文件中要翻译的文本
            @param body 文件内容
            @return list
        '''

        lang_list = []
        # 匹配单引号  双引号
        pattern = r"public\.lang\([\"'](.+?)[\"']"
        for line in body.split("\n"):
            if "public.lang(" in line:
                # lang = re.findall(r"public\.lang\(\'(.+?)\'", line)
                lang = re.findall(pattern, line)

                if lang:
                    lang_list.extend(lang)
        return lang_list
    
    def get_all_lang_dict(self,to_lang='en'):
        '''
            @name 取已经翻译过的结果集
            @param to_lang 目标语言
            @return dict
        '''

        filename = os.path.join(self.exec_path,'all',to_lang + '.json')
        if not os.path.exists(filename):
            return {}
        body = self.read_file(filename)
        try:
            return json.loads(body)
        except:
            return {}
        
    def save_all_lang_dict(self,langs,to_lang='en'):
        '''
            @name 保存翻译结果集
            @param langs dict
            @param to_lang 目标语言
        '''
        save_path = os.path.join(self.exec_path,'all')
        filename = os.path.join(save_path,to_lang + '.json')
        if not os.path.exists(save_path):
            os.makedirs(save_path)
        
        self.write_file(filename,json.dumps(langs,indent=4,ensure_ascii=False))

    # todo 改源语言为英文
    def translate(self, langs,to_lang='en',name='server',to_lang_google='en'):
        '''
            @name 翻译
            @param langs list
            @param to_lang 目标语言
            @param name 保存文件名
        '''
        baidu = baidu_translate()
        to_lang_dict = {}
        all_lang_dict = self.get_all_lang_dict(to_lang)
        for lang in langs:
            print('----- lang')
            print(lang)
            md5 = baidu.make_md5(lang)
            # if to_lang == 'zh':
            if to_lang == 'en':
                to_lang_dict[md5] = lang
                continue

            # 先从已经翻译过的结果集中取
            if md5 in all_lang_dict:
                to_lang_dict[md5] = all_lang_dict[md5]
                continue

            # 调用googletrans API
            trans_result = {}
            try:
                # trans_result['dst'] = baidu.google(lang,to_lang_google,'zh-cn')
                trans_result['dst'] = baidu.google(lang,to_lang_google,'en')
            except Exception as e:
                print('Error:',e)
                continue

            to_lang_dict[md5] = trans_result['dst']
            
            all_lang_dict[md5] = trans_result['dst']
            time.sleep(0.1)

        # 保存翻译结果集
        self.save_all_lang_dict(all_lang_dict,to_lang)

        # 保存翻译结果到语言文件
        save_path = os.path.join(self.exec_path,to_lang)
        if not os.path.exists(save_path):
            os.makedirs(save_path)
        filename = os.path.join(save_path,name+'.json')

        self.write_file(filename,json.dumps(to_lang_dict,indent=4,ensure_ascii=False))

        
    def get_settings(self):
        '''
            @name 获取配置文件
            @return list
        '''
        default = [{
            "name": "en",
            "google": "en",
            "title": "English",
            "cn": "英语"
        }]
        filename = os.path.join(self.exec_path,'settings.json')
        if not os.path.exists(filename):
            return default
        body = self.read_file(filename)
        try:
            return json.loads(body)['languages']
        except:
            return default

    
    def start(self):
        '''
            @name 开始翻译
        '''

        # 获取需要翻译的文件列表(后端)
        server_files = []
        for directory in self.server_path:
            directory_path = os.path.join(self.panel_path, directory)
            files = self.get_files(directory_path, 'server')
            server_files.extend(files)
            print(files)
        # return
        # server_files = self.get_files(os.path.join(self.exec_path,self.server_path))

        # 解析文件中需要翻译的文本
        langs = []
        for file in server_files:
            body = self.read_file(file)
            langs.extend(self.get_lang(body))

        # 获取配置文件中的语言
        config_langs = self.get_settings()
        for lang in config_langs:
            # 翻译
            print('正在翻译:',lang['cn'],'=>',lang['name'],'=>',lang['title'],'...')
            self.translate(langs,lang['name'],'server',lang['google'])

        #-----------------------------------------------------------------------------------------
        # # 获取需要翻译的文件列表（前端）
        # client_files = self.get_files(self.client_path)
        #         # 解析文件中需要翻译的文本
        # langs = []
        # for file in client_files:
        #     print('解析文件:',file)
        #     body = self.read_file(file)
        #     langs.extend(self.get_lang(body))

        # for lang in config_langs:
        #     # 翻译
        #     print('正在翻译:',lang['cn'],'=>',lang['name'],'=>',lang['title'],'...')
        #     self.translate(langs,lang['name'],'client',lang['google'])

        print('翻译完成！')



 


if __name__ == "__main__":
    # 设置代理
    os.environ["http_proxy"] = "http://192.168.168.162:7890"
    os.environ["https_proxy"] = "http://192.168.168.162:7890"

    # 开始翻译
    lang = Lang()
    lang.start()
        
    