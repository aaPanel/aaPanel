# aaPanel Docker Deployment Guide

The aaPanel Docker image is now officially released by aaPanel.

Maintained by: [aaPanel](https://www.aapanel.com)

## How to Use

To begin, execute the following command:

```bash
docker run -d -p 8886:8888 -p 22:21 -p 443:443 -p 80:80 -p 889:888 \
-v ~/website_data:/www/wwwroot \
-v ~/mysql_data:/www/server/data \
-v ~/vhost:/www/server/panel/vhost aapanel/aapanel:lib
```

Once the command is executed, you can access aaPanel at http://youripaddress:8886/ from your host system.

Default username: `aapanel`
Default password: `aapanel123`

### Port Usage Analysis
- Control Panel: 8888
- PhpMyAdmin: 888

### Directory Usage Analysis
- Website Data: /www/wwwroot
- MySQL Data: /www/server/data
- Vhost File: /www/server/panel/vhost

> [!NOTE]
> After completing the deployment, it is essential to promptly update the username and password in the panel settings and include the installation entry.
