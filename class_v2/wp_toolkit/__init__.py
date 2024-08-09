import public
import public.PluginLoader as plugin_loader


core_m = plugin_loader.get_module('{}/class_v2/wp_toolkit/core.py'.format(public.get_panel_path()))
wpmgr = core_m.wpmgr
wp_version = core_m.wp_version
wpfastcgi_cache = core_m.wpfastcgi_cache
wpbackup = core_m.wpbackup
wpmigration = core_m.wpmigration
wpdeployment = core_m.wpdeployment
wp_sets = core_m.wp_sets
# from .core import wpmgr, wp_version, wpfastcgi_cache, wpbackup, wpmigration, wpdeployment, wp_sets



security_m = plugin_loader.get_module('{}/class_v2/wp_toolkit/security.py'.format(public.get_panel_path()))
wp_security = security_m.wp_security
