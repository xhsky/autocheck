#!/usr/bin/env python3
# *-* coding:utf8 *-*
# sky

from core import host, tomcat, redis, mysql
from lib.printf import printf
from lib import conf
import os, datetime
import socket

def main():
    printf(f"开始巡检时间: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    hostname=conf.get("autocheck", "hostname")
    if hostname is None:
        hostname=socket.gethostname()
    printf(f"巡检主机: {hostname[0]}")
    printf("*"*80)

    #host.info()
    tomcat.stats()
    redis.stats()
    mysql.stats()

    printf("*"*80)
    printf(f"结束巡检时间: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
if __name__ == "__main__":
    if os.path.exists("report/check.info"):
        os.remove("report/check.info")
    main()
