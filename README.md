# aaPanel Docker Deployment
The docker image is officially released by aaPanel

Maintained by: [aaPanel](https://www.aapanel.com)



## How to use

```shell
docker run -d -p 8886:8888 -p 22:21 -p 443:443 -p 80:80 -p 889:888 -v ~/website_data:/www/wwwroot -v ~/mysql_data:/www/server/data -v ~/vhost:/www/server/panel/vhost aapanel/aapanel:lib
```

Now you can access aaPanel at http://youripaddress:8886 from your host system.

Default Username: `aapanel`

Default Password: `aapanel123`

#### Ports
Control Panel: 8888

PHPMyAdmin: 888

#### Directories
Website Data: /www/wwwroot

MySQL Data: /www/server/data

VHost File: /www/server/panel/vhost 
> [!NOTE]
> After the deployment is complete, please immediately modify the user name and password in the panel settings and add the installation entry

test
