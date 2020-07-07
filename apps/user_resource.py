#!/usr/bin/env python
# *-* coding:utf8 *-*
# sky

from lib import database, log, warning, notification
from lib.tools import format_size
import os, datetime
import subprocess

def record(log_file, log_level, user):
    logger=log.Logger(log_file, log_level)
    logger.logger.info(f"记录用户{user}的资源限制...")
    record_time=datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cmd=f'su - {user} -c "ulimit -n -u"'
    (status, message)=subprocess.getstatusoutput(cmd)
    if status==0:
        message=message.splitlines()
        nofile=message[0].split()[-1]
        nproc=message[1].split()[-1]

        db=database.db()
        sql="insert into users_limit values(?, ?, ?, ?)"
        db.update_one(sql, (record_time, user, nofile, nproc))
    else:
        logger.logger.error(f"命令'{cmd}'执行报错")

def analysis(log_file, log_level, warning_interval, notify_dict):
    logger=log.Logger(log_file, log_level)
    db=database.db()
    logger.logger.debug(f"分析用户的资源限制...")
    sql="select user, nofile, nproc from users_limit where record_time=(select max(record_time) from users_limit)"
    data=db.query_all(sql)

    min_limit=5000
    for i in data:
        flag=0
        arg="nofile"
        if i[1].isdigit():
            if int(i[1]) < min_limit:
                flag=1
                cmd=f"echo '{i[0]} - {arg} 65536' >> /etc/security/limits.conf"
                warning_msg=f"用户资源限制预警:\n" \
                        f"用户({i[0]})的{arg}参数值({i[1]})过低.\n"\
                        f"请在root用户下执行命令: {cmd}, 然后重启登录该用户再重启该用户下相应软件"
        warning_flag=warning.warning(logger, db, flag, f"{i[0]}_limit", arg, warning_interval)
        if warning_flag:
            notification.send(logger, warning_msg, notify_dict, msg=f"{i[0]}_limit nofile")

        flag=0
        arg="nproc"
        if i[2].isdigit():
            if int(i[2]) < min_limit:
                flag=1
                cmd=f"echo '{i[0]} - {arg} 65536' >> /etc/security/limits.conf"
                warning_msg=f"用户资源限制预警:\n" \
                        f"用户({i[0]})的{arg}参数值({i[2]})过低.\n"\
                        f"请在root用户下执行命令: {cmd}, 然后重启登录该用户再重启该用户下相应软件"
            warning_flag=warning.warning(logger, db, flag, f"{i[0]}_nproc_limit", arg, warning_interval)
            if warning_flag:
                notification.send(logger, warning_msg, notify_dict, msg=f"{i[0]}_limit nproc")


if __name__ == "__main__":
    main()
