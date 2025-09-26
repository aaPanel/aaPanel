# coding: utf-8
# -------------------------------------------------------------------
# aaPanel
# -------------------------------------------------------------------
# Copyright (c) 2014-2099 aaPanel(www.aapanel.com) All rights reserved.
# -------------------------------------------------------------------
# Author: aapanel
# -------------------------------------------------------------------

# ------------------------------
# Adminer config
# ------------------------------

__version__ = "5.4.0"

SERVER_PATH = "/www/server"
DEFAULT_VER = "5.4.0"
DEFAULT_PORT = 999
DEFAULT_DIR = f"{SERVER_PATH}/adminer"
VERSION_PL = f"{DEFAULT_DIR}/version.pl"
PORT_PL = f"{DEFAULT_DIR}/port.pl"

NGX_CONF_PATH = f"{SERVER_PATH}/panel/vhost/nginx/0.adminer.conf"
APC_CONF_PATH = f"{SERVER_PATH}/panel/vhost/apache/0.adminer.conf"
OLS_CONF_PATH = f"{SERVER_PATH}/panel/vhost/openlitespeed/0.adminer.conf"


class WebConfig:
    nginx = NGX_CONF_PATH
    apache = APC_CONF_PATH
    openlitespeed = OLS_CONF_PATH
    all_web = [
        "nginx", "apache", "openlitespeed"
    ]
    all_conf = [
        NGX_CONF_PATH, APC_CONF_PATH, OLS_CONF_PATH
    ]

    @classmethod
    def get(cls, key, default=None):
        return getattr(cls, key, default if default else "")


VER_SHA_MAP = {
    "5.4.0": "1a330e8c197b8bbb57a5c07e245c9424aa1007b3e1ccec17dd39e709d3983c17"
}

NG_CONF = r"""server
    {{
        listen 127.0.0.1:{port};
        server_name _;
        index index.html index.htm index.php;
        root {root_dir};

        location ~ /tmp/ {{
            return 403;
        }}

        include enable-php.conf;

        location ~ .*\.(gif|jpg|jpeg|png|bmp|swf)$
        {{
            expires      30d;
        }}

        location ~ .*\.(js|css)?$
        {{
            expires      12h;
        }}

        location ~ /\.
        {{
            deny all;
        }}

        access_log  /www/wwwlogs/access.log;
    }}
"""

APACHE_CONF = r"""Listen {port}
<VirtualHost 127.0.0.1:{port}>
    ServerAdmin webmaster@example.com
    DocumentRoot "{root_dir}"
    ServerName adminer.localhost

    #PHP
    <FilesMatch \.php$>
           SetHandler "{proxy_pass}"
    </FilesMatch>

    #DENY FILES
    <Files ~ (\.user.ini|\.htaccess|\.git|\.svn|\.project|LICENSE|README.md)$>
      Order allow,deny
      Deny from all
    </Files>

    #PATH
    <Directory "{root_dir}">
       SetOutputFilter DEFLATE
       Options FollowSymLinks
       AllowOverride All
       Require all granted
       DirectoryIndex index.php index.html index.htm default.php default.html default.htm
    </Directory>
</VirtualHost>
"""

OLS_CONF = r"""virtualhost adminer {{
  vhRoot                  {root_dir}
  allowSymbolLink         1
  enableScript            1
  restrained              1
  setUIDMode              0

  docRoot                 $VH_ROOT
  vhDomain                $VH_NAME
  adminEmails             admin@localhost

  index  {{
    useServer               0
    indexFiles              index.php, index.html
  }}

  scripthandler  {{
    add                     lsapi:adminer-lsphp php
  }}

  extprocessor adminer-lsphp {{
    type                    lsapi
    address                 UDS://tmp/lshttpd/adminer.sock
    maxConns                10
    env                     LSAPI_CHILDREN=10
    initTimeout             600
    retryTimeout            0
    persistConn             1
    respBuffer              0
    autoStart               1
    path                    /usr/local/lsws/lsphp{php_version}/bin/lsphp
    extUser                 www
    extGroup                www
  }}

  phpIniOverride  {{
    php_admin_value open_basedir "/tmp:$VH_ROOT"
  }}
}}


listener adminer-listener {{
  address                 127.0.0.1:{port}
  secure                  0
  map                     adminer *
}}
"""

__all__ = [
    "__version__",
    "DEFAULT_VER",
    "DEFAULT_PORT",
    "DEFAULT_DIR",
    "VERSION_PL",
    "PORT_PL",

    "NGX_CONF_PATH",
    "APC_CONF_PATH",
    "OLS_CONF_PATH",
    "WebConfig",
    "VER_SHA_MAP",

    "NG_CONF",
    "APACHE_CONF",
    "OLS_CONF",
]
