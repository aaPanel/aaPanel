import base64
import binascii
import hashlib
import json
import os
import fcntl
import re
import shutil
import socket
import subprocess
import sys
import time
import datetime
from pathlib import Path

import requests

APACHE_CONF_DIRS = [
    "/www/server/panel/vhost/apache"
]

def is_ipv4(ip):
    '''
        @name 是否是IPV4地址
        @author hwliang
        @param ip<string> IP地址
        @return True/False
    '''
    # 验证基本格式
    if not re.match(r"^\d{1,3}.\d{1,3}.\d{1,3}.\d{1,3}$", ip):
        return False

    # 验证每个段是否在合理范围
    try:
        socket.inet_pton(socket.AF_INET, ip)
    except AttributeError:
        try:
            socket.inet_aton(ip)
        except socket.error:
            return False
    except socket.error:
        return False
    return True


def is_ipv6(ip):
    '''
        @name 是否为IPv6地址
        @author hwliang
        @param ip<string> 地址
        @return True/False
    '''
    # 验证基本格式
    if not re.match(r"^[\w:]+$", ip):
        return False

    # 验证IPv6地址
    try:
        socket.inet_pton(socket.AF_INET6, ip)
    except socket.error:
        return False
    return True


def check_ip(ip):
    return is_ipv4(ip) or is_ipv6(ip)

def find_apache_conf_files(keyword):
    """查找 Apache 主配置和 vhost 文件"""
    files = set()
    for base in APACHE_CONF_DIRS:
        base_path = Path(base)
        if not base_path.exists():
            continue
        for f in base_path.rglob("*.conf"):
            with open(f, "r") as file:
                content = file.read()
                # 检查是否包含 ServerName 或 ServerAlias 指令
                if keyword in content:
                    files.add(str(f))
    return list(files)


def insert_location_into_vhost(file_path, keyword, verify_file):
    LOCATION_BLOCK = [
        "    <Location /.well-known/acme-challenge/{}>\n".format(verify_file),
        "        Require all granted\n",
        "        Header set Content-Type \"text/plain\"\n",
        "    </Location>\n",
        "    Alias /.well-known/acme-challenge/{} /tmp/{}\n".format(verify_file, verify_file),
    ]

    path = Path(file_path)
    backup = path.with_suffix(path.suffix + ".bak")
    shutil.copy(path, backup)

    with open(path, "r") as f:
        lines = f.readlines()

    new_lines = []
    in_vhost = False
    hit_vhost = False
    location_exists = False

    for line in lines:
        stripped = line.strip()

        if stripped.lower().startswith("<virtualhost"):
            in_vhost = True
            hit_vhost = False
            location_exists = False

        if in_vhost:
            low = stripped.lower()
            if (low.startswith("servername") or low.startswith("serveralias")) and keyword in stripped:
                hit_vhost = True

            if "<location /.well-known/acme-challenge/>" in low:
                location_exists = True

            if stripped.lower() == "</virtualhost>":
                if hit_vhost and not location_exists:
                    new_lines.extend(LOCATION_BLOCK)
                in_vhost = False

        new_lines.append(line)

    with open(path, "w") as f:
        f.writelines(new_lines)

    return True

def find_nginx_files_by_servername(keyword):
    """通过 nginx -T 找到包含 server_name 的配置文件"""
    result = subprocess.run(
        ["nginx", "-T"],
        stderr=subprocess.STDOUT,
        stdout=subprocess.PIPE,
        text=True,
        check=True
    )

    files = set()
    current_file = None

    for line in result.stdout.splitlines():
        if line.startswith("# configuration file"):
            current_file = line.split()[-1].rstrip(":")
        if "server_name" in line and keyword in line:
            if current_file:
                files.add(current_file)

    return list(files)

def insert_location_into_server(file_path, keyword, verify_file, verify_content):
    path = Path(file_path)
    backup = path.with_suffix(path.suffix + ".bak")

    shutil.copy(path, backup)

    with open(path, "r") as f:
        lines = f.readlines()

    new_lines = []
    brace_level = 0
    in_server = False
    hit_server = False
    location_exists = False

    LOCATION_BLOCK = [
        "    location = /.well-known/acme-challenge/{} {{\n".format(verify_file),
        "        default_type text/plain;\n",
        "        return 200 \"{}\";\n".format(verify_content),
        "    }\n"
    ]

    for i, line in enumerate(lines):
        stripped = line.strip()

        # server 开始
        if stripped.startswith("server"):
            in_server = True
            hit_server = False
            location_exists = False

        if in_server:
            brace_level += line.count("{")
            brace_level -= line.count("}")

            if "server_name" in line and keyword in line:
                hit_server = True

            if "location /.well-known/acme-challenge/" in line:
                location_exists = True

            # server 结束
            if brace_level == 0:
                if hit_server and not location_exists:
                    new_lines.extend(LOCATION_BLOCK)
                in_server = False

        new_lines.append(line)

    with open(path, "w") as f:
        f.writelines(new_lines)

    return True

class AutoApplyIPSSL:
    # 请求到ACME接口
    def __init__(self):
        self._wait_time = 5
        self._max_check_num = 15
        self._url = 'https://acme-v02.api.letsencrypt.org/directory'
        self._bits = 2048
        self._conf_file_v2 = '/www/server/panel/config/letsencrypt_v2.json'
        self._apis = None
        self._replay_nonce = None
        self._config = self.read_config()


    # 取接口目录
    def get_apis(self):
        if not self._apis:
            # 尝试从配置文件中获取
            api_index = "Production"
            if not 'apis' in self._config:
                self._config['apis'] = {}
            if api_index in self._config['apis']:
                if 'expires' in self._config['apis'][api_index] and 'directory' in self._config['apis'][api_index]:
                    if time.time() < self._config['apis'][api_index]['expires']:
                        self._apis = self._config['apis'][api_index]['directory']
                        return self._apis

            # 尝试从云端获取
            res = requests.get(self._url)
            if not res.status_code in [200, 201]:
                result = res.json()
                if "type" in result:
                    if result['type'] == 'urn:acme:error:serverInternal':
                        raise Exception('Service is closed for maintenance or internal error occurred, check <a href="https://letsencrypt.status.io/" target="_blank" class="btlink">https://letsencrypt.status.io/</a> .')
                raise Exception(res.content)
            s_body = res.json()
            self._apis = {}
            self._apis['newAccount'] = s_body['newAccount']
            self._apis['newNonce'] = s_body['newNonce']
            self._apis['newOrder'] = s_body['newOrder']
            self._apis['revokeCert'] = s_body['revokeCert']
            self._apis['keyChange'] = s_body['keyChange']

            # 保存到配置文件
            self._config['apis'][api_index] = {}
            self._config['apis'][api_index]['directory'] = self._apis
            self._config['apis'][api_index]['expires'] = time.time() + \
                86400  # 24小时后过期
            self.save_config()
        return self._apis

    def acme_request(self, url, payload):
        headers = {}
        payload = self.stringfy_items(payload)

        if payload == "":
            payload64 = payload
        else:
            payload64 = self.calculate_safe_base64(json.dumps(payload))
        protected = self.get_acme_header(url)
        protected64 = self.calculate_safe_base64(json.dumps(protected))
        signature = self.sign_message(
            message="{0}.{1}".format(protected64, payload64))  # bytes
        signature64 = self.calculate_safe_base64(signature)  # str
        data = json.dumps(
            {"protected": protected64, "payload": payload64,
                "signature": signature64}
        )
        headers.update({"Content-Type": "application/jose+json"})
        response = requests.post(url, data=data.encode("utf8"), headers=headers)
        # 更新随机数
        self.update_replay_nonce(response)
        return response

    # 更新随机数
    def update_replay_nonce(self, res):
        replay_nonce = res.headers.get('Replay-Nonce')
        if replay_nonce:
            self._replay_nonce = replay_nonce

    def stringfy_items(self, payload):
        if isinstance(payload, str):
            return payload

        for k, v in payload.items():
            if isinstance(k, bytes):
                k = k.decode("utf-8")
            if isinstance(v, bytes):
                v = v.decode("utf-8")
            payload[k] = v
        return payload

    # 转为无填充的Base64
    def calculate_safe_base64(self, un_encoded_data):
        if sys.version_info[0] == 3:
            if isinstance(un_encoded_data, str):
                un_encoded_data = un_encoded_data.encode("utf8")
        r = base64.urlsafe_b64encode(un_encoded_data).rstrip(b"=")
        return r.decode("utf8")

    # 获请ACME请求头
    def get_acme_header(self, url):
        header = {"alg": "RS256", "nonce": self.get_nonce(), "url": url}
        if url in [self._apis['newAccount'], 'GET_THUMBPRINT']:
            from cryptography.hazmat.backends import default_backend
            from cryptography.hazmat.primitives import serialization
            private_key = serialization.load_pem_private_key(
                self.get_account_key().encode(),
                password=None,
                backend=default_backend(),
            )
            public_key_public_numbers = private_key.public_key().public_numbers()

            exponent = "{0:x}".format(public_key_public_numbers.e)
            exponent = "0{0}".format(exponent) if len(
                exponent) % 2 else exponent
            modulus = "{0:x}".format(public_key_public_numbers.n)
            jwk = {
                "kty": "RSA",
                "e": self.calculate_safe_base64(binascii.unhexlify(exponent)),
                "n": self.calculate_safe_base64(binascii.unhexlify(modulus)),
            }
            header["jwk"] = jwk
        else:
            header["kid"] = self.get_kid()
        return header

    def get_nonce(self, force=False):
        # 如果没有保存上一次的随机数或force=True时则重新获取新的随机数
        if not self._replay_nonce or force:
            response = requests.get(
                self._apis['newNonce'],
            )
            self._replay_nonce = response.headers["Replay-Nonce"]
        return self._replay_nonce

    def analysis_private_key(self, key_pem, password=None):
        """
        解析私钥
        :param key_pem: 私钥内容
        :param password: 私钥密码
        :return: 私钥对象
        """
        try:
            from cryptography.hazmat.backends import default_backend
            from cryptography.hazmat.primitives import serialization
            private_key = serialization.load_pem_private_key(
                key_pem.encode(),
                password=password,
                backend=default_backend()
            )
            return private_key
        except:
            return None

    def sign_message(self, message):
        from cryptography.hazmat.primitives import hashes
        from cryptography.hazmat.primitives.asymmetric import padding

        pk = self.analysis_private_key(self.get_account_key())
        return pk.sign(message.encode("utf8"), padding.PKCS1v15(), hashes.SHA256())

    # 获用户取密钥对
    def get_account_key(self):
        if not 'account' in self._config:
            self._config['account'] = {}
        k = "Production"
        if not k in self._config['account']:
            self._config['account'][k] = {}

        if not 'key' in self._config['account'][k]:
            self._config['account'][k]['key'] = self.create_key()
            if type(self._config['account'][k]['key']) == bytes:
                self._config['account'][k]['key'] = self._config['account'][k]['key'].decode()
            self.save_config()
        return self._config['account'][k]['key']

    def create_key(self, key_type='RSA'):
        from cryptography.hazmat.primitives import serialization
        from cryptography.hazmat.primitives.asymmetric import rsa, ec, ed25519

        if key_type == 'RSA':
            private_key = rsa.generate_private_key(
                public_exponent=65537,
                key_size=self._bits
            )
        elif key_type == 'EC':
            private_key = ec.generate_private_key(ec.SECP256R1())
        elif key_type == 'ED25519':
            private_key = ed25519.Ed25519PrivateKey.generate()
        else:
            raise ValueError(f"Unsupported key type: {key_type}")

        private_key_pem = private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption()
        )
        return private_key_pem

    def get_kid(self, force=False):
        #如果配置文件中不存在kid或force = True时则重新注册新的acme帐户
        if not 'account' in self._config:
            self._config['account'] = {}
        k = "Production"
        if not k in self._config['account']:
            self._config['account'][k] = {}

        if not 'kid' in self._config['account'][k]:
            self._config['account'][k]['kid'] = self.register()
            self.save_config()
            time.sleep(3)
            self._config = self.read_config()
        return self._config['account'][k]['kid']

    # 读配置文件
    def read_config(self):
        if not os.path.exists(self._conf_file_v2):
            self._config = {'orders': {}, 'account': {}, 'apis': {}, 'email': None}
            self.save_config()
            return self._config
        with open(self._conf_file_v2, 'r') as f:
            fcntl.flock(f, fcntl.LOCK_SH)  # 加锁
            tmp_config = f.read()
            fcntl.flock(f, fcntl.LOCK_UN)  # 解锁
            f.close()
        if not tmp_config:
            return self._config
        try:
            self._config = json.loads(tmp_config)
        except:
            self.save_config()
            return self._config
        return self._config

    # 写配置文件
    def save_config(self):
        fp = open(self._conf_file_v2, 'w+')
        fcntl.flock(fp, fcntl.LOCK_EX)  # 加锁
        fp.write(json.dumps(self._config))
        fcntl.flock(fp, fcntl.LOCK_UN)  # 解锁
        fp.close()
        return True

    # 注册acme帐户
    def register(self, existing=False):
        if not 'email' in self._config:
            self._config['email'] = 'demo@aapanel.com'
        if existing:
            payload = {"onlyReturnExisting": True}
        elif self._config['email']:
            payload = {
                "termsOfServiceAgreed": True,
                "contact": ["mailto:{0}".format(self._config['email'])],
            }
        else:
            payload = {"termsOfServiceAgreed": True}

        res = self.acme_request(url=self._apis['newAccount'], payload=payload)

        if res.status_code not in [201, 200, 409]:
            raise Exception("Failed to register ACME account: {}".format(res.json()))
        kid = res.headers["Location"]
        return kid

    def create_csr(self, ips):
        from cryptography import x509
        from cryptography.x509.oid import NameOID
        from cryptography.hazmat.primitives.asymmetric import rsa
        from cryptography.hazmat.primitives import hashes
        from cryptography.hazmat.primitives import serialization
        import ipaddress


        # 生成私钥
        pk = self.create_key()
        private_key = serialization.load_pem_private_key(pk, password=None)

        # IP证书不需要CN
        csr_builder = x509.CertificateSigningRequestBuilder().subject_name(x509.Name([]))
        # 添加 subjectAltName 扩展
        alt_names = [x509.IPAddress(ipaddress.ip_address(ip)) for ip in ips]


        csr_builder = csr_builder.add_extension(
            x509.SubjectAlternativeName(alt_names),
            critical=False
        )

        # 签署 CSR
        csr = csr_builder.sign(private_key, hashes.SHA256())

        # 返回 CSR (ASN1 格式)
        return csr.public_bytes(serialization.Encoding.DER), pk

    def apply_ip_ssl(self, ips, email, webroot=None, mode=None, path=None):
        print("Starting to apply for Let's Encrypt IP SSL certificate...")
        print("Retrieving ACME API directory...")
        self.get_apis()
        self._config['email'] = email
        print("Creating order...")
        order_data = self.create_order(ips)
        if not order_data:
            raise Exception("Failed to create order!")
        print("Order created successfully")
        print("Performing domain verification...")
        try:
            self.get_and_set_authorizations(order_data, webroot, mode, ips)
        except Exception as e:
            raise Exception("Domain verification failed! {}".format(e))
        # 完成订单
        print("Creating CSR...")
        csr, private_key = self.create_csr(ips)
        print("Sending CSR and completing order...")
        res = self.acme_request(order_data['finalize'], payload={
            "csr": self.calculate_safe_base64(csr)
        })
        if res.status_code not in [200, 201]:
            raise Exception("Failed to complete order! {}".format(res.json()))
        # 获取证书
        print("Retrieving certificate...")
        cert_url = res.json().get('certificate')
        if not cert_url:
            raise Exception("Failed to retrieve certificate URL!")
        cert_res = self.acme_request(cert_url, payload="")
        if cert_res.status_code not in [200, 201]:
            raise Exception("Failed to retrieve certificate! {}".format(cert_res.json()))
        print("Certificate retrieved successfully!")
        cert_pem = cert_res.content.decode()
        # 保存证书和私钥
        if not path:
            path = "/www/server/panel/ssl"
        if not os.path.exists(path):
            os.makedirs(path)
        cert_path = os.path.join(path, 'certificate.pem')
        key_path = os.path.join(path, 'privateKey.pem')
        with open(cert_path, 'w') as f:
            f.write(cert_pem)
        with open(key_path, 'w') as f:
            f.write(private_key.decode())
        return cert_path, key_path

    def create_order(self, ips):
        identifiers = []
        for ip in ips:
            identifiers.append({"type": "ip", "value": ip})
        payload = {"identifiers": identifiers, "profile": "shortlived"}
        print("Create order, domain name list:{}".format(','.join(ips)))
        res = self.acme_request(self._apis['newOrder'], payload)
        if not res.status_code in [201,200]:  # 如果创建失败
            print("Failed to create order, attempting to fix error...")
            e_body = res.json()
            if 'type' in e_body:
                # 如果随机数失效
                if e_body['type'].find('error:badNonce') != -1:
                    print("Nonce invalid, retrieving new nonce and retrying...")
                    self.get_nonce(force=True)
                    res = self.acme_request(self._apis['newOrder'], payload)
                # 如果帐户失效
                if e_body['detail'].find('KeyID header contained an invalid account URL') != -1:
                    print("Account invalid, re-registering account and retrying...")
                    k = "Production"
                    del(self._config['account'][k])
                    self.get_kid()
                    self.get_nonce(force=True)
                    res = self.acme_request(self._apis['newOrder'], payload)
            if not res.status_code in [201,200]:
                print(res.json())
                # 2025/12/25 aapanel
                raise Exception(str(res.json()))
                # return {}
        return res.json()

    # UTC时间转时间戳
    def utc_to_time(self, utc_string):
        try:
            utc_string = utc_string.split('.')[0]
            utc_date = datetime.datetime.strptime(
                utc_string, "%Y-%m-%dT%H:%M:%S")
            # 按北京时间返回
            return int(time.mktime(utc_date.timetuple())) + (3600 * 8)
        except:
            return int(time.time() + 86400 * 7)

    def get_keyauthorization(self, token):
        acme_header_jwk_json = json.dumps(
            self.get_acme_header("GET_THUMBPRINT")["jwk"], sort_keys=True, separators=(",", ":")
        )
        acme_thumbprint = self.calculate_safe_base64(
            hashlib.sha256(acme_header_jwk_json.encode("utf8")).digest()
        )
        acme_keyauthorization = "{0}.{1}".format(token, acme_thumbprint)
        base64_of_acme_keyauthorization = self.calculate_safe_base64(
            hashlib.sha256(acme_keyauthorization.encode("utf8")).digest()
        )

        return acme_keyauthorization, base64_of_acme_keyauthorization

    # 获取并设置验证信息
    def get_and_set_authorizations(self, order_data, webroot=None, mode=None, ips=None):
        import os

        if 'authorizations' not in order_data:
            raise Exception("Abnormal order data, missing authorization information!")
        for auth_url in order_data['authorizations']:
            res = self.acme_request(auth_url, payload="")
            if not res.status_code in [200, 201]:
                raise Exception("Failed to get authorization information! {}".format(res.json()))
            s_body = res.json()
            if 'status' in s_body:
                if s_body['status'] in ['invalid']:
                    raise Exception("Invalid order, current order status is verification failed!")
                if s_body['status'] in ['valid']:  # 跳过无需验证的域名
                    continue
            for challenge in s_body['challenges']:
                if challenge['type'] == "http-01":
                    break
            if challenge['type'] != "http-01":
                raise Exception("http-01 verification method not found, cannot continue applying for certificate!")
            # 检查是否需要验证
            check_auth_data = self.check_auth_status(challenge['url'])
            if check_auth_data.json()['status'] == 'invalid':
                raise Exception('Domain verification failed, please try applying again!')
            if check_auth_data.json()['status'] == 'valid':
                continue

            acme_keyauthorization, auth_value = self.get_keyauthorization(
                challenge['token'])
            print(challenge)

            if mode:
                if mode == 'standalone':
                    from http.server import HTTPServer, SimpleHTTPRequestHandler
                    import threading
                    import os

                    class ACMERequestHandler(SimpleHTTPRequestHandler):
                        def log_message(self, format, *args):
                            # 屏蔽默认的请求日志输出
                            return

                        def do_GET(self):
                            if self.path == '/.well-known/acme-challenge/{}'.format(challenge['token']):
                                self.send_response(200)
                                self.send_header('Content-type', 'text/plain')
                                self.end_headers()
                                self.wfile.write(acme_keyauthorization.encode())
                            else:
                                self.send_response(404)
                                self.end_headers()

                    server_address = ('', 80)
                    httpd = HTTPServer(server_address, ACMERequestHandler)

                    def start_server():
                        httpd.serve_forever()

                    server_thread = threading.Thread(target=start_server)
                    server_thread.daemon = True
                    server_thread.start()


                    # 2025/12/26 aapanel
                    time.sleep(2)  # 等待服务器启动
                    try:
                        # ========================= 校验服务 ==================================
                        server_started = False
                        challenge_local = f"http://127.0.0.1/.well-known/acme-challenge/{challenge['token']}"
                        for i in range(10): # 最大尝试时间5秒
                            try:
                                # 临时检查80 打印
                                with socket.create_connection(("127.0.0.1", 80), timeout=0.2):
                                    print("Temporary server started on port 80.")

                                response = requests.get(challenge_local, timeout=0.5)
                                if response.status_code == 200 and response.text == acme_keyauthorization:
                                    print("Temporary server started and responding correctly challenge token on port 80.")
                                    server_started = True
                                    break
                                else:
                                    print("Temporary server response incorrect, retrying...")
                                    time.sleep(0.5)
                            except Exception:
                                time.sleep(0.5)

                        if not server_started:
                            # raise Exception("Failed to start temporary HTTP server on port 80 in 5 seconds.")
                            print("Failed to start temporary HTTP server on port 80 in 5 seconds.")

                        # =========================   通知ACME服务器进行验证 ===============================
                        self.acme_request(challenge['url'], payload={"keyAuthorization": "{0}".format(acme_keyauthorization)})
                        self.check_auth_status(challenge['url'], [
                            'valid', 'invalid'])
                    finally:
                        httpd.shutdown()
                        server_thread.join()
                elif mode == 'nginx':
                    tmp_path = '/www/server/panel/vhost/nginx/tmp_apply_ip_ssl.conf'
                    files = find_nginx_files_by_servername(ips[0])
                    if not files:
                        print("No related Nginx configuration files found, attempting to create temporary configuration file...")
                        if not os.path.exists('/www/server/panel/vhost/nginx'):
                            raise Exception("No Nginx configuration files found, and Nginx configuration directory does not exist!")
                        # 如果没有找到相关配置文件，则创建一个临时配置文件
                        with open(tmp_path, 'w') as f:
                            f.write("""server
{{
    listen 80;
    server_name {0};
    location /.well-known/acme-challenge/{1} {{
        default_type text/plain;
        return 200 "{2}";
    }}
}}
""".format(ips[0], challenge['token'], acme_keyauthorization))
                    try:
                        for file in files:
                            print("Modifying Nginx configuration file: {}".format(file))
                            insert_location_into_server(file, ips[0], verify_file=challenge['token'], verify_content=acme_keyauthorization)
                        # 重新加载Nginx配置
                        subprocess.run(["nginx", "-t"], check=True)
                        subprocess.run(["nginx", "-s", "reload"], check=True)

                        # 通知ACME服务器进行验证
                        self.acme_request(challenge['url'],
                                          payload={"keyAuthorization": "{0}".format(acme_keyauthorization)})
                        self.check_auth_status(challenge['url'], [
                            'valid', 'invalid'])
                    finally:
                        for file in files:
                            print("Restoring Nginx configuration file: {}".format(file))
                            # 恢复备份文件
                            backup_file = file + ".bak"
                            if os.path.exists(backup_file):
                                shutil.move(backup_file, file)
                        if not files:
                            print("Deleting temporary Nginx configuration file...")
                            # 删除临时配置文件
                            os.remove(tmp_path)
                        # 重新加载Nginx配置
                        subprocess.run(["nginx", "-t"], check=True)
                        subprocess.run(["nginx", "-s", "reload"], check=True)

                elif mode == 'apache':
                    tmp_path = '/www/server/panel/vhost/apache/tmp_apply_ip_ssl.conf'
                    files = find_apache_conf_files(ips[0])
                    if not files:
                        print("No related Apache configuration files found, attempting to create temporary configuration file...")
                        if not os.path.exists('/www/server/panel/vhost/apache'):
                            raise Exception("No Apache configuration files found, and Apache configuration directory does not exist!")
                        # 如果没有找到相关配置文件，则创建一个临时配置文件
                        with open(tmp_path, 'w') as f:
                            f.write("""<VirtualHost *:80>
    ServerName {0}
    <Location /.well-known/acme-challenge/{1}>
        Require all granted
        Header set Content-Type "text/plain"
    </Location>
    Alias /.well-known/acme-challenge/{1} /tmp/{1}
</VirtualHost>
""".format(ips[0], challenge['token']))
                    try:
                        for file in files:
                            print("Modifying Apache configuration file: {}".format(file))
                            insert_location_into_vhost(file, ips[0], verify_file=challenge['token'])
                        # 写入验证文件
                        with open('/tmp/{}'.format(challenge['token']), 'w') as f:
                            f.write(acme_keyauthorization)
                        # 重新加载Apache配置
                        subprocess.run(["/etc/init.d/httpd", "reload"], check=True)

                        # 通知ACME服务器进行验证
                        self.acme_request(challenge['url'],
                                          payload={"keyAuthorization": "{0}".format(acme_keyauthorization)})
                        self.check_auth_status(challenge['url'], [
                            'valid', 'invalid'])
                    finally:
                        for file in files:
                            print("Restoring Apache configuration file: {}".format(file))
                            # 恢复备份文件
                            backup_file = file + ".bak"
                            if os.path.exists(backup_file):
                                shutil.move(backup_file, file)
                        if not files:
                            print("Deleting temporary Apache configuration file...")
                            # 删除临时配置文件
                            os.remove(tmp_path)
                        # 重新加载Apache配置
                        subprocess.run(["systemctl", "restart", "httpd"], check=True)
            else:
                # 使用webroot方式验证
                challenge_path = os.path.join(
                    webroot, '.well-known', 'acme-challenge')
                if not os.path.exists(challenge_path):
                    os.makedirs(challenge_path)
                file_path = os.path.join(challenge_path, challenge['token'])
                with open(file_path, 'w') as f:
                    f.write(acme_keyauthorization)

                try:
                    # 通知ACME服务器进行验证
                    self.acme_request(challenge['url'], payload={"keyAuthorization": "{0}".format(acme_keyauthorization)})
                    self.check_auth_status(challenge['url'], [
                        'valid', 'invalid'])
                finally:
                    os.remove(file_path)

    # 检查验证状态
    def check_auth_status(self, url, desired_status=None):
        desired_status = desired_status or ["pending", "valid", "invalid"]
        number_of_checks = 0
        authorization_status = "pending"
        while True:
            print("|- {} checking verification result...".format(number_of_checks + 1))
            if desired_status == ['valid', 'invalid']:
                time.sleep(self._wait_time)
            check_authorization_status_response = self.acme_request(url, "")
            a_auth = check_authorization_status_response.json()
            if not isinstance(a_auth, dict):
                continue
            authorization_status = a_auth["status"]
            number_of_checks += 1
            if authorization_status in desired_status:
                if authorization_status == "invalid":
                    try:
                        if 'error' in a_auth['challenges'][0]:
                            ret_title = a_auth['challenges'][0]['error']['detail']
                        elif 'error' in a_auth['challenges'][1]:
                            ret_title = a_auth['challenges'][1]['error']['detail']
                        elif 'error' in a_auth['challenges'][2]:
                            ret_title = a_auth['challenges'][2]['error']['detail']
                        else:
                            ret_title = str(a_auth)
                    except:
                        ret_title = str(a_auth)
                    raise StopIteration(
                        "{0} >>>> {1}".format(
                            ret_title,
                            json.dumps(a_auth)
                        )
                    )
                break

            if number_of_checks == self._max_check_num:
                raise StopIteration(
                    "Error: Verification attempted {0} times. Maximum verification attempts: {1}. Verification interval: {2} seconds.".format(
                        number_of_checks,
                        self._max_check_num,
                        self._wait_time
                    )
                )
        print("|-Verification result: {}".format(authorization_status))
        return check_authorization_status_response


if __name__ == '__main__':
    import argparse
    # 解析命令行参数
    parser = argparse.ArgumentParser(description='Auto-apply IP SSL certificate script')
    parser.add_argument('-ips', type=str, required=True, help='IP addresses to apply SSL certificate for', dest='ips')
    parser.add_argument('-email', type=str, required=False, help='Email for SSL certificate application', dest='email')
    parser.add_argument('-w', type=str, help='Website root directory', dest='webroot')
    parser.add_argument('--standalone', help='Apply certificate using standalone mode', dest='standalone', action='store_true')
    parser.add_argument('--nginx', help='Apply certificate using nginx mode', dest='nginx', action='store_true')
    parser.add_argument('--apache', help='Apply certificate using apache mode', dest='apache', action='store_true')
    parser.add_argument('-path', type=str, help='Certificate save path', dest='path')
    args = parser.parse_args()

    if not args.standalone and not args.webroot and not args.nginx and not args.apache:
        print("No verification mode detected, will attempt to auto-select verification mode!")
        # 自动选择验证模式
        # 判断80端口是否被占用
        use_80 = False
        result = subprocess.run(
            ["lsof", "-i:80"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        if result.stdout:
            result = subprocess.run(
                ["netstat", "-lntup", "|", "grep", "80"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            if result.stdout:
                use_80 = True
        if use_80:
            print("It is detected that port 80 is occupied, try to use Nginx or Apache mode to verify...")
            # 检查是否安装Nginx
            if os.path.exists('/www/server/nginx/sbin/nginx'):
                args.nginx = True
                print("Selected Nginx mode for verification...")
            elif os.path.exists('/www/server/apache/bin/httpd'):
                args.apache = True
                print("Selected Apache mode for verification...")
            else:
                print("[ERROR] Nginx or Apache installation not detected, cannot use Nginx or Apache mode for verification! Please release port 80 and try again.")
                exit(1)
        else:
            args.standalone = True
            print("Port 80 not occupied, selected standalone mode for verification...")

    if not args.email:
        # 使用默认邮箱
        email = "demo@aapanel.com"
    else:
        email = args.email

    ips = args.ips.split(',')
    # 先只支持单个IP申请
    if len(ips) > 1 and not args.standalone:
        print("[ERROR] Multiple IP SSL certificate application not supported in non-standalone mode!")
        exit(1)
    # 先只支持IPv4
    if not is_ipv4(ips[0]):
        print("[ERROR] Only IPv4 addresses are supported for SSL certificate application at this time!")
        exit(1)
    auto_ssl = AutoApplyIPSSL()
    mode = None
    if args.standalone:
        mode = 'standalone'
    elif args.nginx:
        mode = 'nginx'
    elif args.apache:
        mode = 'apache'
    try:
        cert_path, key_path = auto_ssl.apply_ip_ssl(ips, email, webroot=args.webroot, mode=mode, path=args.path)
    except Exception as e:
        # 2025/12/25 aapanel
        print(f"[ERROR] Certificate application failed! Error details: {e}", file=sys.stderr)
        exit(1)
    exit(0)


