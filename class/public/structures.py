import collections

# Common structures
aap_t_simple_result = collections.namedtuple('aap_t_simple_result', ['success', 'msg'])
aap_t_mysql_dump_info = collections.namedtuple('aap_t_mysql_dump_info', ['db_name', 'file', 'dump_time'])
