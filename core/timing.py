#!/usr/bin/env python
# *-* coding:utf8 *-*
# sky

from lib import conf
import os

def timing():
    check, minute, hour, day, month, week=conf.get("timing", 
            "check", 
            "minute", 
            "hour", 
            "day", 
            "month", 
            "week"
            )
    
    if check=="1":
        python_bin=conf.get("autocheck", "python_bin")[0]
        if os.path.exists(python_bin):
            exec_file=f"{os.path.dirname(os.path.dirname(__file__))}/main.py"
            timing_msg=f"{minute} {hour} {day} {month} {week} {python_bin} {exec_file}"
            crontabe_file="/var/spool/cron/root"
            if os.path.exists(crontabe_file):
                with open(crontabe_file, "r") as f:
                    for line in f.readlines():
                        if line.strip()==timing_msg:
                            break
                    else:
                        with open(crontabe_file, "a") as f1:
                            f1.write(f"{timing_msg}\n")

            else:
                print("未找到{crontab_file}文件, 请按照cron服务")
        else:
            print("配置文件中{pthon_bin}不存在")

    
if __name__ == "__main__":
    main()
