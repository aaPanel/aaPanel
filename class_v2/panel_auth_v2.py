# coding: utf-8
# -------------------------------------------------------------------
# aaPanel
# -------------------------------------------------------------------
# Copyright (c) 2015-2019 aaPanel(www.aapanel.com) All rights reserved.
# -------------------------------------------------------------------
# Author: hwliang <hwl@aapanel.com>
# -------------------------------------------------------------------

# ------------------------------
# AUTH验证接口
# ------------------------------

import public, time, json, os, requests
from BTPanel import session, cache
from public.validate import Param


class panelAuth:
    __request_url = None
    __product_list_path = 'data/product_list.pl'
    __product_bay_path = 'data/product_bay.pl'
    __product_id = '100000011'
    __official_url = public.OfficialApiBase()
    __failed_connect_server='Failed to connect to the server!'

    def create_serverid(self, get):
        try:
            userPath = 'data/userInfo.json'
            if not os.path.exists(userPath):
                return public.return_message(-1, 0, public.lang("Please login with account first"))
            tmp = public.readFile(userPath)
            if len(tmp) < 2: tmp = '{}'
            data = json.loads(tmp)
            data['uid'] = data['id']
            if not data:
                return public.return_message(-1, 0, public.lang("Please login with account first"))
            if not 'server_id' in data:
                s1 = public.get_mac_address() + public.get_hostname()
                s2 = self.get_cpuname()
                serverid = public.md5(s1) + public.md5(s2)
                data['server_id'] = serverid
                public.writeFile(userPath, json.dumps(data))
            return data
        except:
            return public.return_message(-1, 0, public.lang("Please login with account first"))


    def create_plugin_other_order(self, get):
        pdata = self.create_serverid(get)
        pdata['pid'] = get.pid
        pdata['cycle'] = get.cycle
        p_url = public.GetConfigValue('home') + '/api/Pluginother/create_order'
        if get.type == '1':
            pdata['renew'] = 1
            p_url = public.GetConfigValue('home') + '/api/Pluginother/renew_order'
        return public.return_message(0, 0, json.loads(public.httpPost(p_url,pdata)))

    def get_order_stat(self, get):
        pdata = self.create_serverid(get)
        pdata['order_id'] = get.oid
        p_url = public.GetConfigValue('home') + '/api/Pluginother/order_stat'
        if get.type == '1':  p_url = public.GetConfigValue('home') + '/api/Pluginother/re_order_stat'
        return public.return_message(0, 0, json.loads(public.httpPost(p_url,pdata)))

    def check_serverid(self, get):
        if get.serverid != self.create_serverid(get): return public.return_message(-1,0,False)
        return public.return_message(0,0,True)

    # 获取价格列表  新增多机购买
    def get_plugin_price(self, get):
        # 校验参数
        try:
            get.validate([
                Param('product_id').Integer(),
            ], [
                public.validate.trim_filter(),
            ])
        except Exception as ex:
            public.print_log("error info: {}".format(ex))
            return public.return_message(-1, 0, str(ex))

        product_id = get.get('product_id/d', 0)
        if product_id == 0:
            return public.return_message(0, 0, [])

        try:
            userPath = 'data/userInfo.json'
            if not 'pluginName' in get and not 'product_id' in get: return public.return_message(-1, 0, public.lang("Parameter ERROR!"))
            if not os.path.exists(userPath): return public.return_message(-1, 0, public.lang("Please login with account first"))
            params = {}
            if not hasattr(get, 'product_id'):
                params['product_id'] = self.get_plugin_info(get.pluginName)['id']
            else:
                params['product_id'] = get.product_id
            data = self.send_cloud('{}/api/product/pricesV3'.format(self.__official_url), params)
            if data['status'] ==-1:
                return data
            data=data['message']
            if not data:
                return public.return_message(-1, 0, public.lang("Please log in to your aaPanel account on the panel first!"))
            if not data['success']:
                return public.return_message(-1, 0,data['msg'])
            # if len(data['res']) == 6:
            #     return data['res'][3:]
            return public.return_message(0, 0,data['res'])
        except:
            public.print_log(public.get_error_info())
            if 'get_product_list' in session:
                del(session['get_product_list'])
            return public.return_message(-1, 0,'Syncing information, please try again!\n {}',(public.get_error_info(),))

    def get_plugin_info(self, pluginName):
        data = self.get_business_plugin(None)
        if data['status']==-1: return None
        for d in data['message']:
            if d['name'] == pluginName: return d
        return None

    def get_plugin_list(self, get):
        try:
            if not session.get('get_product_bay') or not os.path.exists(self.__product_bay_path):
                data = self.send_cloud('get_order_list_byuser', {})
                if data['status']==-1:return data
                if data['message']: public.writeFile(self.__product_bay_path, json.dumps(data['message']))
                session['get_product_bay'] = True
            data = json.loads(public.readFile(self.__product_bay_path))
            return public.return_message(0,0,data)
        except:
            return public.return_message(-1,0,None)

    def get_buy_code(self, get):
        
        # 校验参数
        try:
            get.validate([
                Param('pid').Integer(),
                Param('cycle').Integer(),
                Param('source').Integer(),
                Param('num').Integer(),
                Param('charge_type').Integer(),
                Param('src').Integer(),
                Param('is_ipv6').Integer(),
                Param('coupon_id').Integer(),
                Param('cycle_unit').String(),
                Param('pay_channel').String(),
                Param('ip').String(),
                Param('os').String(),
            ], [
                public.validate.trim_filter(),
            ])
        except Exception as ex:
            public.print_log("error info: {}".format(ex))
            return public.return_message(-1, 0, str(ex))

        cycle = getattr(get, 'cycle', 1)
        params = {}
        params['cycle'] = cycle
        
        params['product_id'] = get.pid
        params['src'] = 2
        params['trigger_entry'] = get.source
        params['pay_channel'] = 2
        # 0.管理后台生成 1.Ping++ 2.Stripe 3.Paypal 10.抵扣券
        if hasattr(get, 'coupon_id'):
            params['coupon_id'] = get.coupon_id

        if hasattr(get, 'pay_channel'):
            params['pay_channel'] = get.pay_channel
            #优惠券检测
            if get.pay_channel==10 and  not hasattr(get, 'coupon_id'):
                return public.return_message(-1, 0, public.lang("parameter error: coupon_id"))

        if hasattr(get, 'charge_type'):
            params['charge_type'] = get.charge_type
            if int(get.charge_type) == 1:
                if not hasattr(get, 'cycle_unit'):return public.return_message(-1, 0, public.lang("parameter error: cycle_unit"))
            params['cycle_unit'] = get.cycle_unit
        
        env_info = public.fetch_env_info()
        params['environment_info'] = json.dumps(env_info)
        params['server_id'] = env_info['install_code']
        # 多机购买 数量
        if not hasattr(get, 'num'):
            return public.return_message(-1, 0, public.lang("parameter error: num"))
        params['num'] = get.num

        # 添加购买来源
        # params['source'] = get.source

        data = self.send_cloud('{}/api/order/product/create'.format(self.__official_url), params)

        if data['status'] == -1:
            return data

        if int(params.get('pay_channel', 0)) == 10:
            # 刷新授权状态
            public.load_soft_list()
            public.refresh_pd()

        return public.return_message(0, 0, data['message']['res'])

    def get_stripe_session_id(self, get):

        params = {}
        if hasattr(get, 'order_no'):
            params['order_no'] = get.order_no
        if hasattr(get, 'order_id'):
            params['order_id'] = get.order_id

        if hasattr(get, 'subscribe'):
            params['subscribe'] = get.subscribe

        # 开启本地支付
        if hasattr(get, 'adaptive_pricing'):
            params['adaptive_pricing'] = get.adaptive_pricing

        if not params.get('order_no', None) and not params.get('order_id', None):
            return public.return_message(-1, 0, public.lang("parameter error"))

        data = self.send_cloud('{}/api/order/product/pay'.format(self.__official_url), params)
        session['focre_cloud'] = True
        return public.return_message(0, 0, data['message']['res'])

    # paypal支付
    def get_paypal_session_id(self, get):

        params = {}
        if hasattr(get, 'oid'):
            params['oid'] = get.oid

        if not params.get('oid', None):
            return public.return_message(-1, 0, public.lang("parameter error"))

        data = self.send_cloud('{}/api/paypal/create_order'.format(self.__official_url), params)
        if data['status']==-1:
            return data
        session['focre_cloud'] = True
        data=data['message']
        data2 = {
            "status": data.get("success", False),
            "res": data.get("res", ""),
            "nonce": data.get("nonce", 0),
        }

        return public.return_message(0, 0, data2)

    # paypal 支付确认
    def check_paypal_status(self, get):

        params = {}
        if hasattr(get, 'paypal_order_id'):
            params['paypal_order_id'] = get.paypal_order_id

        if not params.get('paypal_order_id', None):
             return public.return_message(-1, 0, public.lang("parameter error"))

        data = self.send_cloud('{}/api/paypal/capture_order'.format(self.__official_url), params)
        data=data['message']
        status_code=-1
        status=data.get("success", False)
        if status:
            status_code=0
            # 刷新授权状态
            public.load_soft_list()
            public.refresh_pd()
        data2 = {
            "res": data.get("res", ""),
            "nonce": data.get("nonce", 0),
        }

        return public.return_message(status_code, 0, data2)

    def check_pay_status(self, get):
        params = {}
        params['id'] = get.id
        data = self.send_cloud('check_product_pays', params)
        if data['status']==-1:return data
        data=data['message']
        if not data:  return public.return_message(-1, 0, public.lang("Fail to connect to the server!"))
        if data['status'] == True:
            self.flush_pay_status(get)
            if 'get_product_bay' in session: del (session['get_product_bay'])
        return public.return_message(0, 0, data)

    def flush_pay_status(self, get):
        if 'get_product_bay' in session: del (session['get_product_bay'])
        data = self.get_plugin_list(get)
        if data['status']==-1: return public.return_message(-1, 0, public.lang("Fail to connect to the server!"))
        return public.return_message(0, 0, public.lang("Flush status success"))

    def get_renew_code(self):
        pass

    def check_renew_code(self):
        pass

    def get_business_plugin(self, get):
        try:
            if not session.get('get_product_list') or not os.path.exists(self.__product_list_path):
                data = self.send_cloud('{}/api/product/chargeProducts'.format(self.__official_url), {})
                if data['message']['success']: public.writeFile(self.__product_list_path, json.dumps(data['message']['res']))
                session['get_product_list'] = True
            data = json.loads(public.readFile(self.__product_list_path))
            return public.return_message(0,0,data)
        except:
            return  public.return_message(-1,0,None)

    def get_ad_list(self):
        pass

    def check_plugin_end(self):
        pass

    def get_re_order_status_plugin(self, get):
        params = {}
        params['pid'] = getattr(get, 'pid', 0)
        data = self.send_cloud('get_re_order_status', params)
        if data['status']==-1:return data
        data=data['message']
        if not data:  return public.return_message(-1, 0, public.lang("Fail to connect to the server!"))
        if data['status'] == True:
            self.flush_pay_status(get)
            if 'get_product_bay' in session: del (session['get_product_bay'])
        return public.return_message(0, 0, data)

    def get_voucher_plugin(self, get):
        # 校验参数
        try:
            get.validate([
                Param('pid').Integer(),
            ], [
                public.validate.trim_filter(),
            ])
        except Exception as ex:
            public.print_log("error info: {}".format(ex))
            return public.return_message(-1, 0, str(ex))

        params = {}
        params['product_id'] = getattr(get, 'pid', 0)
        params['status'] = '0'
        data = self.send_cloud('{}/api/user/productVouchers'.format(self.__official_url), params)
        if data['status']==-1:return data
        if not data['message']: 
            return public.return_message(0, 0,[])
        return public.return_message(0, 0,data['message']['res'])

    def get_voucher_plugin_all(self, get):
        params = {}
        params['status'] = '0'
        data = self.send_cloud('{}/api/user/productVouchers'.format(self.__official_url), params)
        if data['status']==-1:return data
        if not data['message']:
            return public.return_message(0, 0,[])
        return public.return_message(0, 0,data['message']['res'])
    def create_order_voucher_plugin(self, get):
        # 校验参数
        try:
            get.validate([
                Param('cycle_unit').String(),
                Param('pid').Integer(),
                Param('coupon_id').Integer(),
                Param('cycle').Integer(),
                Param('charge_type').Integer(),

            ], [
                public.validate.trim_filter(),
            ])
        except Exception as ex:
            public.print_log("error info: {}".format(ex))
            return public.return_message(-1, 0, str(ex))

        cycle = getattr(get, 'cycle', '1')
        params = {}
        params['cycle'] = cycle
        params['cycle_unit'] = get.cycle_unit
        params['coupon_id'] = get.coupon_id
        params['src'] = 2
        params['pay_channel'] = 10
        params['charge_type'] = get.charge_type
        env_info = public.fetch_env_info()
        params['environment_info'] = json.dumps(env_info)
        params['server_id'] = env_info['install_code']
        data = self.send_cloud('{}/api/order/product/create'.format(self.__official_url), params)
        session['focre_cloud'] = True
        if data['message']['success']:
            # 刷新授权状态
            public.load_soft_list()
            public.refresh_pd()
            return public.return_message(0, 0, public.lang("Activate successfully"))

        return public.return_message(-1, 0, public.lang("Activate failed"))

    def send_cloud(self, cloudURL, params):
        try:
            userInfo = self.create_serverid(None)
            if 'token' not in userInfo:
                return public.return_message(-1,0,None)
            url_headers = {"Content-Type": "application/json",
                           "authorization": "bt {}".format(userInfo['token'])
                           }
            resp = requests.post(cloudURL, params=params, headers=url_headers)
            resp_json = resp.json()
            if resp.status_code != 200 or not resp_json.get('success', False):
                # 当接口错误信息存在时，返回接口错误信息
                if isinstance(resp_json.get('res', None), str):
                    raise public.HintException(str(resp_json['res']))
                    # return public.return_message(-1, 0, str(resp_json['res']))

                # 否则统一返回连接服务器失败
                return public.return_message(-1, 0, self.__failed_connect_server)
            # if not resp['res']:
            #     public.print_log('not res:')
            #     return public.return_message(-1,0,self.__failed_connect_server)
            return public.return_message(0, 0, resp_json)
        except public.HintException:
            raise
        except Exception:
            return public.return_message(-1,0,self.__failed_connect_server)
        
    def send_cloud_v2(self, cloudURL, params):
        try:
            userInfo = self.create_serverid(None)
            if 'token' not in userInfo:
                return public.return_message(-1,0,None)
            url_headers = {"Content-Type": "application/json",
                           "authorization": "bt {}".format(userInfo['token'])
                           }
            resp = requests.post(cloudURL, params=params, headers=url_headers)
            resp = resp.json()
            if not resp or 'res' not in  resp:
                return public.return_message(-1,0,self.__failed_connect_server)
            if not resp['res']: 
                return public.return_message(-1,0,None)
            if resp['success'] == False:
                return public.return_message(-1,0,self.__failed_connect_server)
            return public.return_message(0,0,resp['res'])
        except:
            return public.return_message(-1,0,self.__failed_connect_server)
        

    def send_cloud_v3(self, module, params):
        userInfo = self.create_serverid(None);
        if 'status' in userInfo:
            params['uid'] = 0
            params['serverid'] = ''
        else:
            params['uid'] = userInfo['uid']
            params['serverid'] = userInfo['serverid']
            params['access_key'] = userInfo['access_key']
        params['os'] = 'Windows'
        data = self.send_cloud_pro_2('obtain_coupons', params)
        return data
        

    def send_cloud_get(self, cloudURL, params):
        try:
            userInfo = self.create_serverid(None)
            if 'token' not in userInfo:
                return public.return_message(-1,0,None)
            url_headers = {"Content-Type": "application/json",
                           "authorization": "bt {}".format(userInfo['token'])
                           }
            resp = requests.get(cloudURL,headers=url_headers, stream=True).json()
            if not resp or 'res' not in  resp: return public.return_message(-1,0,self.__failed_connect_server)
            if resp['success'] == False:
                return public.return_message(-1,0,self.__failed_connect_server)
            return public.return_message(0,0,resp['res'])
        except:
            return public.return_message(-1,0,self.__failed_connect_server)

    def send_cloud_pro(self, module, params):
        try:
            cloudURL = '{}/api/order/product/'.format(self.__official_url)
            userInfo = self.create_serverid(None)
            params['os'] = 'Linux'
            if 'status' in userInfo:
                params['server_id'] = ''
            else:
                params['server_id'] = userInfo['server_id']
            url_headers = {"authorization": "bt {}".format(userInfo['token'])}
            resp = requests.post(cloudURL, params=params, headers=url_headers)
            resp = resp.json()['res']
            if not resp: return None
            return resp
        except:
            return None
        

    def send_cloud_pro_2(self, module, params):
        try:
            cloudURL = '{}/api/user/{}'.format(self.__official_url,module)
            userInfo = self.create_serverid(None)
            params['os'] = 'Linux'
            if 'status' in userInfo:
                params['server_id'] = ''
            else:
                params['server_id'] = userInfo['server_id']
            url_headers = {"authorization": "bt {}".format(userInfo['token'])}
            resp = requests.post(cloudURL, params=params, headers=url_headers)
            resp = resp.json()
            if not resp or 'res' not in  resp:
                return public.return_message(-1,0,self.__failed_connect_server)
            if not resp['res']: return public.return_message(-1,0,self.__failed_connect_server)
            if resp['success'] == False:
                return public.return_message(-1,0,self.__failed_connect_server)
            return public.return_message(0,0,resp['res'])
        except:
            return public.return_message(-1,0,self.__failed_connect_server)

    def get_voucher(self, get):
        params = {}
        params['product_id'] = self.__product_id
        params['status'] = '0'
        data = self.send_cloud_pro('get_voucher', params)
        return data

    def get_order_status(self, get):
        params = {}
        data = self.send_cloud_pro('get_order_status', params)
        return data

    def get_product_discount_by(self, get):
        params = {}
        data = self.send_cloud_pro('get_product_discount_by', params)
        return data

    def get_re_order_status(self, get):
        params = {}
        data = self.send_cloud_pro('get_re_order_status', params)
        return data

    def create_order_voucher(self, get):
        code = getattr(get, 'code', '1')
        params = {}
        params['code'] = code
        data = self.send_cloud_pro('create_order_voucher', params)
        public.return_message(0, 0, data)

    def create_order(self, get):
        cycle = getattr(get, 'cycle', '1')
        params = {}
        params['cycle'] = cycle
        params['cycle'] = 'month'
        params['product_id'] = 100000012
        params['src'] = 2
        params['pay_channel'] = 2
        params['charge_type'] = 1
        params['environment_info'] = json.dumps(public.fetch_env_info())
        data = self.send_cloud_pro('create', params)
        return data

    def get_cpuname(self):
        return public.ExecShell("cat /proc/cpuinfo|grep 'model name'|cut -d : -f2")[0].strip()

    def get_product_auth(self, get):
        # 校验参数
        try:
            get.validate([
                Param('pid').Integer(),
                Param('page').Integer(),
                Param('pageSize').Integer(),
            ], [
                public.validate.trim_filter(),
            ])
        except Exception as ex:
            public.print_log("error info: {}".format(ex))
            return public.return_message(-1, 0, str(ex))

        params = {}
        params['page'] = get.page if 'page' in get else 1
        params['pageSize'] = get.pageSize if 'pageSize' in get else 15
        data = self.send_cloud('{}/api/user/productAuthorizes'.format(self.__official_url), params)
        if not data:
            return public.return_message(0, 0,[])
        if 'success' not  in data['message']: return public.return_message(0, 0,[])
        data = data['message']['res']
        # return [i for i in data['list'] if i['status'] != 'activated' and get.pid == i['product_id']]
        res = list()
        for i in data['list']:
            if i['status'] != 'activated' and str(get.pid) == str(i['product_id']):
                res.append(i)
        return public.return_message(0, 0,res)

    def get_product_auth_all(self, get):
        # 校验参数
        try:
            get.validate([
                Param('page').Integer(),
                Param('pageSize').Integer(),
            ], [
                public.validate.trim_filter(),
            ])
        except Exception as ex:
            public.print_log("error info: {}".format(ex))
            return public.return_message(-1, 0, str(ex))

        params = {}
        params['page'] = get.page if 'page' in get else 1
        params['pageSize'] = get.pageSize if 'pageSize' in get else 15
        data = self.send_cloud('{}/api/user/productAuthorizes'.format(self.__official_url), params)
        if not data:
            return public.return_message(0, 0,[])
        if 'success' not  in data['message']: return public.return_message(0, 0,[])
        data = data['message']['res']
        res = list()
        for i in data['list']:
            if i['status'] != 'activated':
                res.append(i)
        return public.return_message(0, 0,res)
    def auth_activate(self, get):
        params = {}
        params['serial_no'] = get.serial_no
        params['environment_info'] = json.dumps(public.fetch_env_info())
        data = self.send_cloud('{}/api/authorize/product/activate'.format(self.__official_url), params)
        if 'success' not in data['message'] or not data['message']['success']:
            return public.return_message(-1, 0, public.lang("Activate Failed"))
        session['focre_cloud'] = True
        # 刷新授权状态
        public.load_soft_list()
        public.refresh_pd()
        return public.return_message(0, 0, public.lang("Activate successfully"))

    def renew_product_auth(self, get):
        params = {}
        params['serial_no'] = get.serial_no
        params['pay_channel'] = get.pay_channel
        params['cycle'] = get.cycle
        params['cycle_unit'] = get.cycle_unit
        params['src'] = 2
        params['trigger_entry'] = get.source
        params['environment_info'] = json.dumps(public.fetch_env_info())
        if hasattr(get, 'coupon_id') and get.pay_channel == '10':
            params['coupon_id'] = get.coupon_id
        data = self.send_cloud('{}/api/authorize/product/renew'.format(self.__official_url), params)

        if not data['message']['success']:
            data['message']['res'] = 'Invalid authorize OR authorize not found!'
            return public.return_message(-1, 0, data['message']['res'])
        session['focre_cloud'] = True
        # 使用抵扣券续费直接返回续费结果
        if get.pay_channel == '10':
            if not data['message']['success']:
                 return public.return_message(-1, 0, public.lang("Renew Failed"))
            # 刷新授权状态
            public.load_soft_list()
            public.refresh_pd()
            return public.return_message(0, 0, public.lang("Renew successfully"))
        # 使用支付续费返回stripe的请求数据
        return public.return_message(0, 0,data['message']['res'])

    def free_trial(self, get):
        """
        每个账号有一次免费试用专业版15天的机会
        :return:
        """
        params = {}
        params['environment_info'] = json.dumps(public.fetch_env_info())
        data = self.send_cloud('{}/api/product/obtainProfessionalMemberFree'.format(self.__official_url), params)
        session['focre_cloud'] = True
        # 使用抵扣券续费直接返回续费结果
        if not data['message']['success']:
             return public.return_message(-1, 0, public.lang("Apply Failed"))
        return public.return_message(0, 0, public.lang("Apply successfully"))

    # 获取专业版特权信息  或插件信息?
    def get_plugin_remarks(self, get):
        # 校验参数
        try:
            get.validate([
                Param('product_id').Integer(),
            ], [
                public.validate.trim_filter(),
            ])
        except Exception as ex:
            public.print_log("error info: {}".format(ex))
            return public.return_message(-1, 0, str(ex))


        if not hasattr(get, 'product_id'):
            return public.return_message(-1, 0, public.lang("product_id Parameter ERROR!"))
        product_id = get.product_id

        # ikey = 'plugin_remarks' + product_id
        # if ikey in session:
        #     return session.get(ikey)
        try:
            url = '{}/api/panel/get_advantages/{}'.format(self.__official_url, product_id)
            data = requests.get(url).json()
        except:
            return public.return_message(-1, 0, public.lang("Failed to connect to the server!"))
        if not data: return public.return_message(-1, 0, public.lang("Failed to connect to the server!"))
        # session[ikey] = data
        return public.return_message(0,0,data)
    
    def res_request_error(self):
        return public.return_message(-1, 0, public.lang("Interface request failed ({})!", self.__request_url))
    

    def get_apply_copon(self, get):
        """
        领取优惠券
        @get.coupon 优惠券
        """
        # 校验参数
        try:
            get.validate([
                Param('obtain_id').Integer(),
            ], [
                public.validate.trim_filter(),
            ])
        except Exception as ex:
            public.print_log("error info: {}".format(ex))
            return public.return_message(-1, 0, str(ex))

        params = {}
        params['obtain_id']= get.obtain_id
        cloudUrl=self.__official_url+'/api/user/obtain_coupons'
        # data = self.send_cloud_v2('obtain_coupons', params)
        data = self.send_cloud_v3(cloudUrl, params)
        return data

    def get_ignore_time(self, get):
        """
        获取忽略时间
        @get.coupon 优惠券
        """
        try:
            limit = int(public.readFile('data/ignore_coupon_time.pl'))
        except:
            limit = public.return_message(0,0,0)

        if limit == -100 or limit > time.time():
            return public.return_message(0,0,1)
        return public.return_message(0,0,0)

    def get_coupon_list(self, get):
        """
        获取可用的优惠券
        @get.coupon 优惠券
        """
        params = {}
        cloudUrl=self.__official_url+'/api/user/coupons'
        data = self.send_cloud_get(cloudUrl, params)
        return data
        # if not data:
        #     if type(data) == list:
        #         return public.return_message(0,0,[])
        #     return public.return_message(-1,0,self.res_request_error())
        # return public.return_message(0,0,data)

    def ignore_coupon_time(self, get):
        """
        获取优惠券
        @get.coupon 优惠券
        @get.limit_time 限制时间  永久 -100
        """
        if not hasattr(get, 'limit_time')or not get.limit_time: return public.return_message(-1, 0, public.lang("Missing parameter limit_time or parameter cannot be empty!"))
        limit_time = int(get.limit_time)
        if limit_time < time.time() and limit_time > 0:
            return public.return_message(-1, 0, public.lang("Time cannot be less than the current time!"))

        public.writeFile('data/ignore_coupon_time.pl', str(limit_time))

        msg = 'Ignoring success, coupon information will not be displayed in the future'
        if limit_time > 0: msg = 'Ignoring success, coupon information will no longer be displayed to you before {}'.format(public.format_date(times=limit_time))
        return public.return_message(0,0, msg)
    
    def get_coupons(self, get):
        """
        @name 获取可领取的优惠券列表
        @param uid 用户id
        """
        # 用户是否忽略
        if self.get_ignore_time(get)['message']['result']:
            return public.return_message(0,0,[])
        params = {}
        cloudURL = self.__official_url+'/api/user/obtainable_coupons'
        data = self.send_cloud_v2(cloudURL, params)
        if not data:
            return public.return_message(-1,0,None)
        if data['status']==-1:
            return data
        return data
    

    def get_all_coupons(self,get):
        """
        @name 获取所有优惠券
        """
        #获取可领取的优惠券列表
        params = {}
        cloudURL = self.__official_url+'/api/user/obtainable_coupons'
        data = self.send_cloud_v2(cloudURL, params)
        if not data['message']:
            return public.return_message(-1,0,None)
        if data['status']==0:
            if data['message']['status'] ==1:
                data['message']['interface_type']=1
                return data
            else:
                data['message']['interface_type']=2
                # 获取可用的优惠券列表  
                params = {}
                cloudUrl=self.__official_url+'/api/user/coupons'
                tmp_data = self.send_cloud_get(cloudUrl, params)
                data['message']['total']=0
                if isinstance(tmp_data['message'],list) and  len(tmp_data['message'])>0:
                    data['message']['total']=len(tmp_data['message'])
                    data['message']['end_time']=tmp_data['message'][0]['end_time']
                return data
        else:
            # 接口请求失败，返回默认值
            return public.success_v2({
                'status': 0,
                'obtain_id': 0,
                'end_time': 0,
                'type': 0,
                'coupons': [],
                'usable_coupon_num': 0,
            })
        return data
    
    """
    @name 统一请求接口
    @param url 返回URL不是www.bt.cn，修改config/config.json的home字段
    """

    def request_post(self, url, params):
        params = {}
        data = self.send_cloud_pro_2('obtainable_coupons', params)
        return data

    # 检测订单支付状态
    def detect_order_status(self, args: public.dict_obj):
        args.validate([
            public.Param('order_id').Require().Integer('>', 0).Filter(int),
        ])

        resp = self.send_cloud('{}/api/order/{}/status'.format(public.OfficialApiBase(), args.order_id), {})

        # 订单支付成功时，刷新授权信息
        if int((resp.get('message', {}) if isinstance(resp.get('message', {}), dict) else {}).get('res', 0)) == 1:
            # 刷新授权状态
            public.load_soft_list()
            public.refresh_pd()

        return resp

    # get expansion pricing
    def get_expand_pack_prices(self, args: public.dict_obj):
        expand_pack_type = str(args.get('expand_pack_type', 'mail')).strip()

        # 取缓存
        cache_key = '{}:get_expand_pack_prices'.format(expand_pack_type)
        cache = public.cache_get(cache_key)

        if cache:
            # return cache
            return public.return_message(0, 0, cache)

        try:
            userPath = 'data/userInfo.json'
            if not os.path.exists(userPath): return public.return_message(-1, 0, public.lang("Please login with account first"))
            params = {'expand_pack_type': expand_pack_type}
            data = self.send_cloud('{}/api/product/expandPackPrices'.format(self.__official_url), params)

            if data['status'] == -1:
                # public.print_log('0')
                return data

            data = data['message']
            if not data:
                return public.return_message(-1, 0, public.lang("Please log in to your aaPanel account on the panel first!"))
            if not data['success']:
                # public.print_log('1')
                return public.return_message(-1, 0,data['msg'])

            dat = {"prices": data['res'],}
            public.cache_set(cache_key, dat, 600)
            return public.return_message(0, 0, dat)
        except:
            public.print_log(public.get_error_info())
            if 'get_product_list' in session:
                del (session['get_product_list'])
            return public.return_message(-1, 0,'Syncing information, please try again!\n {}',(public.get_error_info(),))

