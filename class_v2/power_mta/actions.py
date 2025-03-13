import public
from public.validate import Param
from power_mta.overview import overview as overviewModule
from power_mta.automations import Automation


# 概览数据
def overview(args: public.dict_obj):
    args.validate([
        Param('campaign_id').Integer('>', 0).Filter(int),
        Param('domain').Host(),
        Param('start_time').Integer('>', 0).Filter(int),
        Param('end_time').Integer('>', 0).Filter(int),
    ])

    return public.success_v2(overviewModule().overview(args.get('campaign_id', -1), args.get('domain', None), args.get('start_time', -1), args.get('end_time', -1)))


# 仪表盘
def overview_dashboard(args: public.dict_obj):
    args.validate([
        Param('campaign_id').Integer('>', 0),
        Param('domain').Host(),
        Param('start_time').Integer('>', 0),
        Param('end_time').Integer('>', 0),
    ])

    return public.success_v2(overviewModule().overview_dashboard(args.get('campaign_id', -1), args.get('domain', None), args.get('start_time', -1), args.get('end_time', -1)))


# 邮件服务商
def overview_providers(args: public.dict_obj):
    args.validate([
        Param('campaign_id').Integer('>', 0).Filter(int),
        Param('domain').Host(),
        Param('start_time').Integer('>', 0).Filter(int),
        Param('end_time').Integer('>', 0).Filter(int),
    ])

    return public.success_v2(overviewModule().overview_providers(args.get('campaign_id', -1), args.get('domain', None), args.get('start_time', -1), args.get('end_time', -1)))


# 邮件发送
def overview_send(args: public.dict_obj):
    args.validate([
        Param('campaign_id').Integer('>', 0).Filter(int),
        Param('domain').Host(),
        Param('start_time').Integer('>', 0).Filter(int),
        Param('end_time').Integer('>', 0).Filter(int),
    ])

    return public.success_v2(overviewModule().send_mail_dashboard(args.get('campaign_id', -1), args.get('domain', None), args.get('start_time', -1), args.get('end_time', -1)))


# 邮件发送图表数据
def chart_send(args: public.dict_obj):
    args.validate([
        Param('campaign_id').Integer('>', 0).Filter(int),
        Param('domain').Host(),
        Param('start_time').Integer('>', 0).Filter(int),
        Param('end_time').Integer('>', 0).Filter(int),
    ])

    return public.success_v2(overviewModule().chart_send_mail(args.get('campaign_id', -1), args.get('domain', None), args.get('start_time', -1), args.get('end_time', -1)))


# 退件率图表数据
def chart_bounce_rate(args: public.dict_obj):
    args.validate([
        Param('campaign_id').Integer('>', 0).Filter(int),
        Param('domain').Host(),
        Param('start_time').Integer('>', 0).Filter(int),
        Param('end_time').Integer('>', 0).Filter(int),
    ])

    return public.success_v2(overviewModule().chart_bounce_rate(args.get('campaign_id', -1), args.get('domain', None), args.get('start_time', -1), args.get('end_time', -1)))


# 打开率图表数据
def chart_open_rate(args: public.dict_obj):
    args.validate([
        Param('campaign_id').Integer('>', 0).Filter(int),
        Param('domain').Host(),
        Param('start_time').Integer('>', 0).Filter(int),
        Param('end_time').Integer('>', 0).Filter(int),
    ])

    return public.success_v2(overviewModule().chart_open_rate(args.get('campaign_id', -1), args.get('domain', None), args.get('start_time', -1), args.get('end_time', -1)))


# 点击率图表数据
def chart_click_rate(args: public.dict_obj):
    args.validate([
        Param('campaign_id').Integer('>', 0).Filter(int),
        Param('domain').Host(),
        Param('start_time').Integer('>', 0).Filter(int),
        Param('end_time').Integer('>', 0).Filter(int),
    ])

    return public.success_v2(overviewModule().chart_click_rate(args.get('campaign_id', -1), args.get('domain', None), args.get('start_time', -1), args.get('end_time', -1)))


# 添加/编辑自动化任务
def set_automation(args: public.dict_obj):
    return public.success_v2(Automation().set(args))


# 获取自动化任务列表
def get_automations(args: public.dict_obj):
    return public.success_v2(Automation().get_tasks(args))


# 更新自动化任务名称
def set_automation_name(args: public.dict_obj):
    return public.success_v2(Automation().set_name(args))


# 获取自动化任务节点树
def get_automation_workflow(args: public.dict_obj):
    return public.success_v2(Automation().get_workflow(args))


# 启停自动化任务
def set_automation_status(args: public.dict_obj):
    return public.success_v2(Automation().set_status(args))


# 删除自动化任务
def remove_automation(args: public.dict_obj):
    return public.success_v2(Automation().remove(args))


# 获取所有用户组
def get_all_groups(args: public.dict_obj):
    with public.S('mail_type', '/www/vmail/postfixadmin') as query:
        groups = query.field('id', 'mail_type as name').select()

    return public.success_v2(groups)

