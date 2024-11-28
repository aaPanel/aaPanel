# coding: utf-8
# -------------------------------------------------------------------
# aapanel
# -------------------------------------------------------------------
# Copyright (c) 2015-2099 aapanel(http://www.aapanel.com) All rights reserved.
# -------------------------------------------------------------------
# Author: wzz <wzz@bt.cn>
# -------------------------------------------------------------------
import os
# ------------------------------
# Docker模型
# ------------------------------
import sys

if "/www/server/panel/class" not in sys.path:
    sys.path.insert(0, "/www/server/panel/class")

os.chdir("/www/server/panel")
import public


class main():

    def returnResult(self, get):
        '''
            @name 模型测试方法，请求方式
                /mod/docker/routetestMod/returnResult
                支持form-data和json

                使用通用的响应对象，返回json格式数据
            @author wzz <2024/2/19 上午 10:37>
            @param "data":{"参数名":""} <数据类型> 参数描述
            @return dict{"status":True/False,"msg":"提示信息"}
        '''
        print(public.returnResult(msg="hello"))
        return public.returnResult(msg="hello")

    def wsRequest(self, get):
        """
        处理websocket，ws测试方法，请求方式
            ws://192.168.x.x:8888/ws_mod
            连接成功后先发送第一条信息{"x-http-token":"token"}
            然后再发第二条信息，信息内容如下格式

            备注：如果需要使用apipost测试，请将__init__.py中ws模型路由的comReturn和csrf检查注释掉再测试
        @param get:
            {"mod_name":"docker","sub_mod_name":"routetest","def_name":"wsRequest","ws_callback":"111"}
            {"mod_name":"模型名称","sub_mod_name":"子模块名称","def_name":"函数名称","ws_callback":"ws必传参数，传111",其他参数接后面}
        @return:
        """
        if not hasattr(get, "_ws"):
            return True

        import time
        sum = 0
        while sum < 10:
            time.sleep(0.2)
            get._ws.send("hello\r\n")
            sum += 1

        return True


if __name__ == '__main__':
    main().returnResult({})
