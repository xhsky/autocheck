#!/usr/bin/env python3
# *-* coding:utf8 *-*
# sky

from core import host, tomcat, redis, mysql, mail, timing, oracle, backup
from lib.printf import printf
from lib import conf
import os, datetime, tarfile
import socket, shutil

def main():
    os.makedirs("report",  exist_ok=True)
    printf(f"开始巡检时间: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    hostname=conf.get("autocheck", "hostname")[0]
    if hostname is None:
        hostname=socket.gethostname()
    printf(f"巡检主机: {hostname}")
    printf("*"*80)

    host.info()
    tomcat.stats()
    redis.stats()
    mysql.stats()
    backup.cat()
    oracle.info()

    printf("*"*80)
    printf(f"结束巡检时间: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    # 巡检报告打包
    report_files=os.listdir(".")
    for report_file in report_files:
        if report_file.startswith("report") and report_file.endswith("tar.gz"):
            os.remove(report_file)
    with tarfile.open(f"report-{datetime.datetime.now().strftime('%Y%m%d%H%M')}.tar.gz", "w:gz") as tar:
        tar.add("./report")

    mail.send()
    timing.timing()

    
if __name__ == "__main__":
    rootdir=os.path.dirname(__file__)
    os.chdir(rootdir)
    shutil.rmtree("./report/", ignore_errors=True)
    main()
