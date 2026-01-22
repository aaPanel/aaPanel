import io
import paramiko


def test_ssh_config(host, port, username, password, pkey, pkey_passwd, timeout: int = 10) -> str:
    try:
        ssh = paramiko.SSHClient()
        pkey_obj = None
        if pkey:
            pky_io = io.StringIO(pkey)
            key_cls_list = [paramiko.RSAKey, paramiko.ECDSAKey, paramiko.Ed25519Key]
            if hasattr(paramiko, "DSSKey"):
                key_cls_list.append(paramiko.DSSKey)
            for key_cls in key_cls_list:
                pky_io.seek(0)
                try:
                    pkey_obj = key_cls.from_private_key(pky_io, password=(pkey_passwd if pkey_passwd else None))
                except Exception as e:
                    if "base64 decoding error" in str(e):
                        return "Private key data error, please check if it is a complete copy of the private key information"
                    elif "Private key file is encrypted" in str(e):
                        return "The private key has been encrypted, but the password for the private key has not been provided, so the private key information cannot be verified"
                    elif "Invalid key" in str(e):
                        return "Private key parsing error, please check if the password for the private key is correct"
                    continue
                else:
                    break
            else:
                return "Private key parsing error, please confirm that the entered key format is correct"
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        # look_for_keys 一定要是False，排除不必要的私钥尝试导致的错误
        ssh.connect(hostname=host, port=port, username=username, password=(password if password else None),
                    pkey=pkey_obj, look_for_keys=False, auth_timeout=timeout)
        ssh.close()
        return ""
    except Exception as e:
        err_str = str(e)
        auth_str = "{}@{}:{}".format(username, host, port)
        if err_str.find('Authentication timeout') != -1:
            return 'Authentication timeout, [{}] error：{}'.format(auth_str, e)
        if err_str.find('Authentication failed') != -1:
            if pkey:
                return 'Authentication failed, please check if the private key is correct: ' + auth_str
            return 'Account or password error:' + auth_str
        if err_str.find('Bad authentication type; allowed types') != -1:
            return 'Unsupported authentication type: {}'.format(err_str)
        if err_str.find('Connection reset by peer') != -1:
            return 'The target server actively rejects the connection'
        if err_str.find('Error reading SSH protocol banner') != -1:
            return 'Protocol header response timeout, error：' + err_str
        return "Connection failed：" + err_str