import os
import shutil
import sys

if "/www/server/panel/class" not in sys.path:
    sys.path.insert(0, "/www/server/panel/class")

import public


# ols 修改多服务配置文件
def ols_update_config(status, is_restart=True):
    """
        端口关系：
            8188:80
            8190:443
    """
    listen_dir = os.path.join(public.get_panel_path(), 'vhost', 'openlitespeed')
    listen_main = os.path.join(listen_dir, 'listen', '80.conf')  # 主监听
    listen_ssl = os.path.join(listen_dir, 'listen', '443.conf')

    phpmyadmin = [
        os.path.join(listen_dir, 'listen', '887.conf'),
        os.path.join(listen_dir, 'listen', '888.conf'),
        os.path.join(listen_dir, 'phpmyadmin.conf'),
        os.path.join(listen_dir, 'detail', 'phpmyadmin.conf')
    ]
    pattern = '*:80'
    pattern_ANY = '[ANY]:80'
    pattern_ssl = '*:443'
    pattern_ssl_ANY = '[ANY]:443'

    if status == 'enable':
        if os.path.exists(listen_main):
            content = public.readFile(listen_main)
            content = content.replace(pattern, '*:8188')
            content = content.replace(pattern_ANY, '[ANY]:8188')
            public.writeFile(listen_main, content)

        if os.path.exists(listen_ssl):
            content = public.readFile(listen_ssl)
            content = content.replace(pattern_ssl, '*:8190')
            content = content.replace(pattern_ssl_ANY, '[ANY]:8190')
            public.writeFile(listen_ssl, content)

        # 取消监听phpmyadmin
        for path in phpmyadmin:
            if os.path.exists(path):
                shutil.move(path, path + '.bar')

    elif status == 'disable':
        pattern = '*:8188'
        pattern_ANY = '[ANY]:8188'
        pattern_ssl = '*:8190'
        pattern_ssl_ANY = '[ANY]:8190'

        # 恢复服务
        if os.path.exists(listen_main):
            content = public.readFile(listen_main)
            content = content.replace(pattern, '*:80')
            content = content.replace(pattern_ANY, '[ANY]:80')
            public.writeFile(listen_main, content)

        if os.path.exists(listen_ssl):
            content = public.readFile(listen_ssl)
            content = content.replace(pattern_ssl, '*:443')
            content = content.replace(pattern_ssl_ANY, '[ANY]:443')
            public.writeFile(listen_ssl, content)

        for path in phpmyadmin:
            if os.path.exists(path + '.bar'):
                shutil.move(path + '.bar', path)

        # 处理用户添加的端口恢复
        listen_custom_dir = os.path.join(listen_dir, 'listen')
        if os.path.exists(listen_custom_dir):
            for filename in os.listdir(listen_custom_dir):
                file = filename.split('.')[0]
                if file not in ['80', '443', '887', '888']:
                    content = public.readFile(os.path.join(listen_custom_dir, filename))
                    content = content.replace(pattern, '*:' + file)
                    content = content.replace(pattern_ANY, '*:' + file)
                    public.writeFile(os.path.join(listen_custom_dir, filename), content)

    # 重启ols
    public.webservice_operation('openlitespeed')

    return True, "The ols configuration modification was successful！"


# apache 修改多服务配置文件
def apache_update_config(status, is_restart=True) -> tuple[bool, str]:
    """
        端口关系：
            8288:80
            8289:888
            8290:443
    """
    main_config = '/www/server/apache/conf/httpd.conf'  # 主配置文件
    httpd_vhosts = '/www/server/apache/conf/extra/httpd-vhosts.conf'
    httpd_ssl = '/www/server/apache/conf/extra/httpd-ssl.conf'
    phpadmin = os.path.join(public.get_panel_path(), 'vhost', 'apache', 'phpmyadmin.conf')
    apache_adminer = f"/www/server/panel/vhost/apache/0.adminer.conf"
    ols_adminer = f"/www/server/panel/vhost/openlitespeed/0.adminer.conf"
    bar_list = [phpadmin, ols_adminer, apache_adminer]

    port_80 = '80'
    new_port_80 = '8288'
    port_888 = '888'
    new_port_888 = '8289'
    port_443 = '443'
    new_port_443 = '8290'

    if status == 'disable':
        port_80 = '8288'
        new_port_80 = '80'
        port_888 = '8289'
        new_port_888 = '888'
        port_443 = '8290'
        new_port_443 = '443'

        # 恢复配置文件
        for bar in bar_list:
            if os.path.exists(bar + '.bar'):
                shutil.move(bar + '.bar', bar)
    else:
        # 使配置文件无效
        for bar in bar_list:
            if os.path.exists(bar):
                shutil.move(bar, bar + '.bar')

    # 修改虚拟主机端口配置
    site_name = public.M('sites').field('name,project_type').select()
    for name in site_name:
        # 判断是否是Node项目
        if name['project_type'] == 'Node':
            check_node_project(name['name'], status)
        path = os.path.join(public.get_panel_path(), 'vhost', 'apache', name['name'] + '.conf')
        if os.path.exists(path):
            content = public.readFile(path)
            content = content.replace(f'*:{port_80}', f'*:{new_port_80}')
            content = content.replace(f'*:{port_443}', f'*:{new_port_443}')
            public.writeFile(path, content)

    if os.path.exists(main_config):
        content = public.readFile(main_config)
        content = content.replace(f'Listen {port_80}', f'Listen {new_port_80}')
        content = content.replace(f'Listen {port_443}', f'Listen {new_port_443}')
        content = content.replace(f'ServerName 0.0.0.0:{port_80}', f'ServerName 0.0.0.0:{new_port_80}')
        public.writeFile(main_config, content)

    if os.path.exists(httpd_vhosts):
        content = public.readFile(httpd_vhosts)
        content = content.replace(f'Listen {port_888}', f'Listen {new_port_888}')
        content = content.replace(f'*:{port_888}', f'*:{new_port_888}')
        content = content.replace(f'*:{port_80}', f'*:{new_port_80}')
        public.writeFile(httpd_vhosts, content)

    if os.path.exists(httpd_ssl):
        content = public.readFile(httpd_ssl)
        content = content.replace(f'{port_443}', f'{new_port_443}')
        public.writeFile(httpd_ssl, content)

    ok = public.webservice_operation('apache')

    return True, ' '

# 检测node项目，多服务下默认走nginx
def check_node_project(site_name, is_ = 'enable'):
    conf = os.path.join(public.get_panel_path(),'vhost', 'apache', f'node_{site_name}.conf')

    # 使多服务下apache文件不生效
    if is_ == 'enable':
        if os.path.exists(conf):
            shutil.move(conf, conf + '.barduo')
    else:
        if os.path.exists(conf + '.barduo'):
            shutil.move(conf + '.barduo', conf )
    return True

def multi_service_check_repair():
    try:
        # 尝试重新修改配置
        ols_update_config('enable')
        apache_update_config('enable')
        public.webservice_operation('nginx')
        public.print_log("The modification of multiple service ports has been completed")
    except Exception as e:
        public.print_log(str(e))

if __name__ == '__main__':
    multi_service_check_repair()
