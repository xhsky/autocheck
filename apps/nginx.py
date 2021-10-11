#!/usr/bin/env python
# *-* coding:utf8 *-*
# sky

from lib import database, notification, log, warning, tools
import psutil
import datetime
import subprocess
import os

def running_analysis(log_file, log_level, warning_interval, notify_dict):
    logger=log.Logger(log_file, log_level)
    logger.logger.debug("开始分析Nginx运行情况...")
    db=database.db()
    """
    sql="select record_time, port, pid from tomcat_constant where (port,record_time) in (select port,max(record_time) from tomcat_constant group by port)"
    sqlite3低版本不支持多列in查询, 无语... 
    """
    sql="select port, pid from nginx_constant where record_time=(select max(record_time) from nginx_constant)"
    data=db.query_all(sql)
    for i in data:
        flag=0
        if i[1] == 0:
            flag=1
        warning_flag=warning.warning(logger, db, flag, i[0], "running", warning_interval)
        if warning_flag:
            warning_msg=f"Nginx预警: Nginx({i[0]})未运行\n"
            notification.send(logger, warning_msg, notify_dict, msg=f'nginx{i[0]}_running')

def record(log_file, log_level, nginx_port_list):
    logger=log.Logger(log_file, log_level)
    db=database.db()

    nginx_port_and_pid={}
    for port in nginx_port_list:
        nginx_port_and_pid[port]=tools.find_pid(int(port))

    record_time=datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    for port in nginx_port_and_pid:                # 根据pid获取相应信息
        pid=nginx_port_and_pid[port]
        logger.logger.debug(f"记录Nginx({port})资源")
        if pid==0:
            logger.logger.error(f"Nginx({port})未运行")
            sql="insert into nginx_constant(record_time, pid, port, boot_time) values(?, ?, ?, ?)"
            db.update_one(sql, (record_time, pid, port, "0"))
        else:
            nginx_info=psutil.Process(pid).as_dict()
            nginx_create_time=datetime.datetime.fromtimestamp(nginx_info["create_time"]).strftime("%Y-%m-%d %H:%M:%S")
            nginx_cmdline=",".join(nginx_info["cmdline"])
            constant_data=(record_time, pid, port, nginx_create_time, nginx_cmdline)
            constant_sql="insert into nginx_constant values(?, ?, ?, ?, ?)"
            db.update_one(constant_sql, constant_data)

            nginx_memory_percent=nginx_info['memory_percent']
            nginx_memory=psutil.virtual_memory()[0] * nginx_info['memory_percent'] / 100
            nginx_connections=len(nginx_info["connections"])
            nginx_num_threads=nginx_info["num_threads"]
            variable_data=(record_time, pid, port, nginx_memory, nginx_memory_percent, nginx_connections, nginx_num_threads)
            variable_sql="insert into nginx_variable values(?, ?, ?, ?, ?, ?, ?)"
            db.update_one(variable_sql, variable_data)

if __name__ == "__main__":
    main()
