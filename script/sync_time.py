import os
import sys
import time
import traceback

try:
    import requests
except:
    os.system("btpip install requests")
    import requests
try:
    import ntplib
except:
    os.system("btpip install ntplib")
    import ntplib
from datetime import datetime

try:
    import pytz
except:
    os.system("btpip install pytz")
    import pytz


def sync_server_time(server, zone):
    try:
        print("Getting time from {}...".format(server))
        client = ntplib.NTPClient()
        response = client.request(server, version=3)
        timestamp = response.tx_time
        tz = pytz.timezone(zone)
        time_zone = datetime.fromtimestamp(timestamp, tz)
        local_time = datetime.now()
        offset = timestamp - time.time()
        print("Local time:", local_time)
        print("Server time:", time_zone)
        print("Time offset:", offset, "seconds")
        import os
        print("Syncing time...")
        os.system('date -s "{}"'.format(time_zone))
        return True
    except Exception as e:
        print("Failed to retrieve time from {}!".format(server))
        # print(traceback.format_exc())
        return False


server_list = ['cn.pool.ntp.org', '0.pool.ntp.org', '2.pool.ntp.org']

if __name__ == '__main__':
    area = sys.argv[1].split('/')[0]
    zone = sys.argv[1].split('/')[1]
    print("Current time zone setting:{}".format(sys.argv[1]))
    if not zone:
        exit()
    os.system('rm -f /etc/localtime')
    os.system("ln -s '/usr/share/zoneinfo/" + area + "/" + zone + "' '/etc/localtime'")
    flag = 0
    for server in server_list:
        if sync_server_time(server, sys.argv[1]):
            flag = 1
            print("|-Synchronized time successfully!")
            break
    if flag == 0:
        try:
            print("Getting time from {}...".format('http://www.bt.cn'))
            r = requests.get("http://www.bt.cn/api/index/get_time")
            timestamp = int(r.text)
            tz = pytz.timezone(sys.argv[1])
            time_zone = datetime.fromtimestamp(timestamp, tz)
            local_time = datetime.now()
            offset = timestamp - time.time()
            print("Local time:", local_time)
            print("Server time:", time_zone)
            print("Time offset:", offset, "秒")
            print("Syncing time...")
            os.system(f"date -s '{time_zone}'")
            flag = 1
            print("|-Synchronized time successfully!")
        except:
            print(traceback.format_exc())
    if flag == 0:
        print("|-Synchronization time error!")
