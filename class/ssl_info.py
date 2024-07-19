
import os,sys,re,time,subprocess

panelPath = '/www/server/panel/'
os.chdir(panelPath)

sys.path.insert(0, panelPath + "class/")
import public
from datetime import date, datetime

is_openssl = True
try:
    import OpenSSL
except:
    is_openssl = False



class ssl_info:

    def __init__(self) -> None:
        pass


    def create_key(self,bits=2048):
        """
        @name 创建RSA密钥
        @param bits 密钥长度
        """
        if is_openssl:

            key = OpenSSL.crypto.PKey()
            key.generate_key(OpenSSL.crypto.TYPE_RSA, bits)
            private_key = OpenSSL.crypto.dump_privatekey(OpenSSL.crypto.FILETYPE_PEM, key)
            return private_key
        else:
            tmp_pk_file = "/tmp/private_key_{}.pem".format(int(time.time()))
            cmd = ["openssl", "genpkey", "-algorithm", "RSA", "-out", tmp_pk_file, "-pkeyopt", f"rsa_keygen_bits:{bits}"]
            subprocess.run(cmd, check=True)
            with open(tmp_pk_file, "r") as f:
                private_key = f.read()
            try:
                os.remove("private_key.pem")
            except:
                pass
            return private_key

    def load_ssl_info_by_data(self, pem_data: str):
        if not isinstance(pem_data, (str, bytes)):
            return None

        if is_openssl:
            return self.__get_cert_info(pem_data)

        # 使用命令行解析
        pem_file = "/tmp/fullchain_{}.pem".format(int(time.time()))
        public.writeFile(pem_file, pem_data)
        res = public.ExecShell("openssl x509 -in {} -noout -text".format(pem_file))[0]
        try:
            result = {}
            issuer_match = re.search(r"Issuer: (.*)", res)
            if issuer_match:
                data = {}
                issuer = issuer_match.group(1)
                for key, val in re.findall(r"(\w+\s*)=([^,]+)", issuer):
                    data[key.strip()] = val

                if "CN" in data:
                    result["issuer"] = data['CN']
                    if "O" in data:
                        s = data['O'].encode().decode('unicode_escape')
                        result["issuer"] = bytes(s, 'latin1').decode('utf-8')

            validity_match = re.search(r"Not After\s*:\s*(.*)", res)
            if validity_match:
                not_after = validity_match.group(1)
                dt_after = datetime.strptime(not_after, "%b %d %H:%M:%S %Y %Z")
                result['notAfter'] = dt_after.strftime("%Y-%m-%d %H:%M:%S")
                result['endtime'] = (dt_after - datetime.now()).days
            else:
                result['endtime'] = 0

            validity_match = re.search(r"Not Before\s*:\s*(.*)", res)
            if validity_match:
                not_befoer = validity_match.group(1)
                dt_befoer = datetime.strptime(not_befoer, "%b %d %H:%M:%S %Y %Z")
                result['notBefore'] = dt_befoer.strftime("%Y-%m-%d %H:%M:%S")

            subject_match = re.search(r"Subject: (.*)", res)
            if subject_match:
                subject = subject_match.group(1)
                for key, val in re.findall(r"(\w+\s*)=([^,]+)", subject):
                    if key.strip() == 'CN':
                        s = val.encode().decode('unicode_escape')
                        result["subject"] = bytes(s, 'latin1').decode('utf-8')
            # 取可选名称
            result['dns'] = []
            dns_match = re.findall(r"DNS:([^\s,]+)", res)
            for dns in dns_match:
                result['dns'].append(dns)
        except:
            result = None

        if os.path.exists(pem_file):
            os.remove(pem_file)
        return result

    def load_ssl_info(self,pem_file):
        """
        @name 获取证书详情
        """
        if not os.path.exists(pem_file):
            return None

        pem_data = public.readFile(pem_file)
        if not pem_data:
            return None
        return self.load_ssl_info_by_data(pem_data)

    def __get_cert_info(self,pem_data):
        """
        @name 通过python的openssl模块获取证书信息
        @param pem_data 证书内容
        """
        result = {}
        try:
            x509 = OpenSSL.crypto.load_certificate(OpenSSL.crypto.FILETYPE_PEM, pem_data)
        except:   # 证书格式可能是错的，就没有办法读取证书内容
            return None

        issuer = x509.get_issuer()
        result['issuer'] = ''
        if hasattr(issuer, 'CN'):
            result['issuer'] = issuer.CN
        if not result['issuer']:
            is_key = [b'0', '0']
            issue_comp = issuer.get_components()
            if len(issue_comp) == 1:
                is_key = [b'CN', 'CN']
            for iss in issue_comp:
                if iss[0] in is_key:
                    result['issuer'] = iss[1].decode()
                    break
        if not result['issuer']:
            if hasattr(issuer, 'O'):
                result['issuer'] = issuer.O
        # 取到期时间
        result['notAfter'] = self.strf_date(
            bytes.decode(x509.get_notAfter())[:-1])
        # 取申请时间
        result['notBefore'] = self.strf_date(
            bytes.decode(x509.get_notBefore())[:-1])
        # 取可选名称
        result['dns'] = []
        for i in range(x509.get_extension_count()):
            s_name = x509.get_extension(i)
            if s_name.get_short_name() in [b'subjectAltName', 'subjectAltName']:
                s_dns = str(s_name).split(',')
                for d in s_dns:
                    result['dns'].append(d.split(':')[1])
        subject = x509.get_subject().get_components()
        # 取主要认证名称
        if len(subject) == 1:
            result['subject'] = subject[0][1].decode()
        else:
            if not result['dns']:
                for sub in subject:
                    if sub[0] == b'CN':
                        result['subject'] = sub[1].decode()
                        break
                if 'subject' in result:
                    result['dns'].append(result['subject'])
            else:
                result['subject'] = result['dns'][0]
        result['endtime'] = int(int(time.mktime(time.strptime(result['notAfter'], "%Y-%m-%d")) - time.time()) / 86400)
        return result

       # 转换时间
    def strf_date(self, sdate):
        return time.strftime('%Y-%m-%d', time.strptime(sdate, '%Y%m%d%H%M%S'))

    #转换时间
    def strfToTime(self,sdate):
        import time
        return time.strftime('%Y-%m-%d',time.strptime(sdate,'%b %d %H:%M:%S %Y %Z'))


    def dump_pkcs12_new(self, key_pem=None, cert_pem=None, ca_pem=None, friendly_name=""):
        from cryptography.hazmat.backends import default_backend
        from cryptography.hazmat.primitives import serialization
        from cryptography.hazmat.primitives.serialization.pkcs12 import serialize_key_and_certificates
        from cryptography.x509 import load_pem_x509_certificate

        private_key = serialization.load_pem_private_key(
            key_pem.encode(),
            password=None,  # 如果私钥有密码，请在此处提供密码
            backend=default_backend()
        )

        cert = load_pem_x509_certificate((cert_pem + ca_pem).encode(), default_backend())

        # 将证书和私钥组合成PKCS12格式的文件
        p12 = serialize_key_and_certificates(
            name=friendly_name.encode() if friendly_name else None,
            key=private_key,
            cert=cert,
            encryption_algorithm=serialization.NoEncryption(),
            cas=[load_pem_x509_certificate(ca_pem.encode(), default_backend())]
        )
        return p12

#class ssl:








