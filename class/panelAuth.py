#coding: utf-8
#-------------------------------------------------------------------
# aaPanel
#-------------------------------------------------------------------
# Copyright (c) 2015-2019 aaPanel(www.aapanel.com) All rights reserved.
#-------------------------------------------------------------------
# Author: hwliang <hwl@aapanel.com>
#-------------------------------------------------------------------

#------------------------------
# AUTH验证接口
#------------------------------

import public,time,json,os,requests
try:
    from BTPanel import cache, session
except:
    pass

class panelAuth:
    __product_list_path = 'data/product_list.pl'
    __product_bay_path = 'data/product_bay.pl'
    __product_id = '100000011'
    __official_url = '{}'.format(public.OfficialApiBase())
    # __official_url = 'http://dev.aapanel.com'

    def create_serverid(self, get):
        try:
            return public.get_userinfo()
        except:
            return public.return_msg_gettext(False, public.lang("Please login with account first"))


    def create_plugin_other_order(self,get):
        pdata = self.create_serverid(get)
        pdata['pid'] = get.pid
        pdata['cycle'] = get.cycle
        p_url = public.GetConfigValue('home') + '/api/Pluginother/create_order'
        if get.type == '1':
            pdata['renew'] = 1
            p_url = public.GetConfigValue('home') + '/api/Pluginother/renew_order'
        return json.loads(public.httpPost(p_url,pdata))

    def get_order_stat(self,get):
        pdata = self.create_serverid(get)
        pdata['order_id'] = get.oid
        p_url = public.GetConfigValue('home') + '/api/Pluginother/order_stat'
        if get.type == '1':  p_url = public.GetConfigValue('home') + '/api/Pluginother/re_order_stat'
        return json.loads(public.httpPost(p_url,pdata))
    
    def check_serverid(self,get):
        if get.serverid != self.create_serverid(get): return False
        return True

    def get_plugin_price(self, get):
        try:
            userPath = 'data/userInfo.json'
            if not 'pluginName' in get and not 'product_id' in get: return public.return_msg_gettext(False, public.lang("Parameter ERROR!"))
            if not os.path.exists(userPath): return public.return_msg_gettext(False, public.lang("Please login with account first"))
            params = {}
            if not hasattr(get,'product_id'):
                params['product_id'] = self.get_plugin_info(get.pluginName)['id']
            else:
                params['product_id'] = get.product_id
            data = self.send_cloud('{}/api/product/pricesV3'.format(self.__official_url), params)
            if not data:
                return public.return_msg_gettext(False, public.lang("Please log in to your aaPanel account on the panel first!"))
            if not data['success']:
                return public.return_msg_gettext(False,data['msg'])
            # if len(data['res']) == 6:
            #     return data['res'][3:]
            return data['res']
        except:
            del(session['get_product_list'])
            return public.return_msg_gettext(False,'Syncing information, please try again!\n {}',(public.get_error_info(),))
    
    def get_plugin_info(self,pluginName):
        data = self.get_business_plugin(None)
        if not data: return None
        for d in data:
            if d['name'] == pluginName: return d
        return None
    
    def get_plugin_list(self,get):
        try:
            if not session.get('get_product_bay') or not os.path.exists(self.__product_bay_path):
                data = self.send_cloud('get_order_list_byuser', {})
                if data: public.writeFile(self.__product_bay_path,json.dumps(data))
                session['get_product_bay'] = True
            data = json.loads(public.readFile(self.__product_bay_path))
            return data
        except: return None

    def get_buy_code(self,get):
        cycle = getattr(get,'cycle',1)
        params = {}
        params['cycle'] = cycle
        params['cycle_unit'] = get.cycle_unit
        params['product_id'] = get.pid
        params['src'] = 2
        params['trigger_entry'] = get.source
        params['pay_channel'] = 2
        # 0.管理后台生成 1.Ping++ 2.Stripe 3.Paypal 10.抵扣券
        if hasattr(get, 'pay_channel'):
            params['pay_channel'] = get.pay_channel
        params['charge_type'] = get.charge_type
        env_info = public.fetch_env_info()
        params['environment_info'] = json.dumps(env_info)
        params['server_id'] = env_info['install_code']
        # 多机购买 数量
        if not hasattr(get, 'num'):
            return public.return_msg_gettext(False, public.lang("parameter error: num"))
        params['num'] = get.num

        # 添加购买来源
        # params['source'] = get.source

        data = self.send_cloud('{}/api/order/product/create'.format(self.__official_url), params)
        if not data['success']:
            return public.return_msg_gettext(False, data['res'])
        return data['res']

    def get_stripe_session_id(self,get):

        params = {}
        if hasattr(get, 'order_no'):
            params['order_no'] = get.order_no
        if hasattr(get, 'order_id'):
            params['order_id'] = get.order_id

        if hasattr(get, 'subscribe'):
            params['subscribe'] = get.subscribe

        if not params.get('order_no', None) and not params.get('order_id', None):
            return public.return_msg_gettext(False, public.lang("parameter error"))

        data = self.send_cloud('{}/api/order/product/pay'.format(self.__official_url), params)
        session['focre_cloud'] = True
        return data['res']
    # paypal支付
    def get_paypal_session_id(self,get):

        params = {}
        if hasattr(get, 'oid'):
            params['oid'] = get.oid

        if not params.get('oid', None):
            return public.return_msg_gettext(False, public.lang("parameter error"))

        data = self.send_cloud('{}/api/paypal/create_order'.format(self.__official_url), params)
        session['focre_cloud'] = True
        data2 = {
            "status": data.get("success", False),
            "res": data.get("res", ""),
            "nonce": data.get("nonce", 0),
        }

        return data2

    # paypal 支付确认
    def check_paypal_status(self,get):

        params = {}
        if hasattr(get, 'paypal_order_id'):
            params['paypal_order_id'] = get.paypal_order_id

        if not params.get('paypal_order_id', None):
            return public.return_msg_gettext(False, public.lang("parameter error"))


        data = self.send_cloud('{}/api/paypal/capture_order'.format(self.__official_url), params)
        # session['focre_cloud'] = True
        data2 = {
            "status": data.get("success", False),
            "res": data.get("res", ""),
            "nonce": data.get("nonce", 0),
        }

        return data2


    def check_pay_status(self,get):
        params = {}
        params['id'] = get.id
        data = self.send_cloud('check_product_pays', params)
        if not data: return public.return_msg_gettext(False, public.lang("Fail to connect to the server!"))
        if data['status'] == True:
            self.flush_pay_status(get)
            if 'get_product_bay' in session: del(session['get_product_bay'])
        return data
    
    def flush_pay_status(self,get):
        if 'get_product_bay' in session: del(session['get_product_bay'])
        data = self.get_plugin_list(get)
        if not data: return public.return_msg_gettext(False, public.lang("Fail to connect to the server!"))
        return public.return_msg_gettext(True, public.lang("Flush status success"))
    
    def get_renew_code(self):
        pass
    
    def check_renew_code(self):
        pass
    
    def get_business_plugin(self,get):
        try:
            if not session.get('get_product_list') or not os.path.exists(self.__product_list_path):
                data = self.send_cloud('{}/api/product/chargeProducts'.format(self.__official_url), {})
                if data['success']: public.writeFile(self.__product_list_path,json.dumps(data['res']))
                session['get_product_list'] = True
            data = json.loads(public.readFile(self.__product_list_path))
            return data
        except: return None
    
    def get_ad_list(self):
        pass
    
    def check_plugin_end(self):
        pass
    
    def get_re_order_status_plugin(self,get):
        params = {}
        params['pid'] = getattr(get,'pid',0)
        data = self.send_cloud('get_re_order_status', params)
        if not data: return public.return_msg_gettext(False, public.lang("Fail to connect to the server!"))
        if data['status'] == True:
            self.flush_pay_status(get)
            if 'get_product_bay' in session: del(session['get_product_bay'])
        return data
    
    def get_voucher_plugin(self,get):
        params = {}
        params['product_id'] = getattr(get,'pid',0)
        params['status'] = '0'
        data = self.send_cloud('{}/api/user/productVouchers'.format(self.__official_url), params)
        if not data: return []
        return data['res']

    def create_order_voucher_plugin(self,get):
        cycle = getattr(get,'cycle','1')
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
        if data['success']:
            return public.return_msg_gettext(True, public.lang("Activate successfully"))
        return public.return_msg_gettext(False, public.lang("Activate failed"))

    def send_cloud(self,cloudURL,params):
        try:
            userInfo = self.create_serverid(None)
            if 'token' not in userInfo:
                return None
            url_headers = {"Content-Type": "application/json",
                           "authorization": "bt {}".format(userInfo['token'])
                           }
            resp = requests.post(cloudURL, params =params, headers=url_headers)
            resp = resp.json()
            if not resp['res']: return None
            return resp
        except: return public.get_error_info()
        
    def send_cloud_pro(self,module,params):
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
        except: return None

    def get_voucher(self,get):
        params = {}
        params['product_id'] = self.__product_id
        params['status'] = '0'
        data = self.send_cloud_pro('get_voucher', params)
        return data

    def get_order_status(self,get):
        params = {}
        data = self.send_cloud_pro('get_order_status', params)
        return data
        
    
    def get_product_discount_by(self,get):
        params = {}
        data = self.send_cloud_pro('get_product_discount_by', params)
        return data
    
    def get_re_order_status(self,get):
        params = {}
        data = self.send_cloud_pro('get_re_order_status', params)
        return data
    
    def create_order_voucher(self,get):
        code = getattr(get,'code','1')
        params = {}
        params['code'] = code
        data = self.send_cloud_pro('create_order_voucher', params)
        return data
    
    def create_order(self,get):
        cycle = getattr(get,'cycle','1')
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

    # def fetch_env_info(self):
    #     userInfo = self.create_serverid(None)
    #     return json.dumps({'ip': public.GetLocalIp(),
    #      'is_ipv6': 0,
    #      'os': 'Centos7',
    #      'mac': self.get_mac_address(),
    #      'hdid': public.fetch_disk_SN(),
    #      'ramid': '16G',
    #      'cpuid': public.fetch_cpu_ID(),
    #      'server_name': self.get_hostname(),
    #      'install_code': userInfo['server_id']
    #      })

    def get_cpuname(self):
        return public.ExecShell("cat /proc/cpuinfo|grep 'model name'|cut -d : -f2")[0].strip()
    
    def get_product_auth(self,get):
        params = {}
        params['page'] = get.page if 'page' in get else 1
        params['pageSize'] = get.pageSize if 'pageSize' in get else 15
        data = self.send_cloud('{}/api/user/productAuthorizes'.format(self.__official_url), params)
        if not data:
            return []
        if not data['success']: return []
        data = data['res']
        # return [i for i in data['list'] if i['status'] != 'activated' and get.pid == i['product_id']]
        res = list()
        for i in data['list']:
            if i['status'] != 'activated' and str(get.pid) == str(i['product_id']):
                res.append(i)
        return res

    def auth_activate(self,get):
        params = {}
        params['serial_no'] = get.serial_no
        params['environment_info'] = json.dumps(public.fetch_env_info())
        data = self.send_cloud('{}/api/authorize/product/activate'.format(self.__official_url), params)
        if not data['success']: return public.return_msg_gettext(False, public.lang("Activate Failed"))
        session['focre_cloud'] = True
        return public.return_msg_gettext(True, public.lang("Activate successfully"))

    def renew_product_auth(self,get):
        params = {}
        params['serial_no'] = get.serial_no
        params['pay_channel'] = get.pay_channel
        params['cycle'] = get.cycle
        params['cycle_unit'] = get.cycle_unit
        params['src'] = 2
        params['trigger_entry'] = get.source
        params['environment_info'] = json.dumps(public.fetch_env_info())
        if hasattr(get,'coupon_id') and get.pay_channel == '10':
            params['coupon_id'] = get.coupon_id
        data = self.send_cloud('{}/api/authorize/product/renew'.format(self.__official_url), params)

        if not data['success']:
            data['res'] = 'Invalid authorize OR authorize not found!'
            return data
        session['focre_cloud'] = True
        # 使用抵扣券续费直接返回续费结果
        if get.pay_channel == '10':
            if not data['success']:
                return public.return_msg_gettext(False, public.lang("Renew Failed"))
            return public.return_msg_gettext(True, public.lang("Renew successfully"))
        # 使用支付续费返回stripe的请求数据
        return data['res']

    def free_trial(self,get):
        """
        每个账号有一次免费试用专业版15天的机会
        :return:
        """
        params = {}
        params['environment_info'] = json.dumps(public.fetch_env_info())
        data = self.send_cloud('{}/api/product/obtainProfessionalMemberFree'.format(self.__official_url), params)
        session['focre_cloud'] = True
        # 使用抵扣券续费直接返回续费结果
        if not data['success']:
            return public.return_msg_gettext(False, public.lang("Apply Failed"))
        return public.return_msg_gettext(True, public.lang("Apply successfully"))

    # 获取专业版特权信息  或插件信息?
    def get_plugin_remarks(self, get):

        if not hasattr(get, 'product_id'):
            return public.return_msg_gettext(False, public.lang("product_id Parameter ERROR!"))
        product_id = get.product_id

        ikey = 'plugin_remarks' + product_id
        if ikey in session:
            return session.get(ikey)
        url = '{}/api/panel/get_advantages/{}'.format(self.__official_url, product_id)
        data = requests.get(url).json()
        # public.print_log(" ###############%%%%%%%%%%%%%%%%%%%% {}".format(data))
        if not data: return public.returnMsg(False, public.lang("Failed to connect to the server!"))
        session[ikey] = data
        return data
