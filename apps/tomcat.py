#!/usr/bin/env python
# *-* coding:utf8 *-*
# sky

from lib import database, mail, log, warning, tools
import psutil
import datetime
import subprocess
import os

def running_analysis(log_file, log_level, warning_interval, sender_alias, receive, subject):
    logger=log.Logger(log_file, log_level)
    logger.logger.debug("开始分析Tomcat运行情况...")
    db=database.db()
    """
    sql="select record_time, port, pid from tomcat_constant where (port,record_time) in (select port,max(record_time) from tomcat_constant group by port)"
    sqlite3低版本不支持多列in查询, 无语... 
    """
    sql="select port, pid from tomcat_constant where record_time=(select max(record_time) from tomcat_constant)"
    data=db.query_all(sql)
    for i in data:
        flag=0
        if i[1] == 0:
            flag=1
        warning_flag=warning.warning(logger, db, flag, i[0], "running", warning_interval)
        if warning_flag:
            warning_msg=f"Tomcat预警:\nTomcat({i[0]})未运行\n"
            mail.send(logger, warning_msg, sender_alias, receive, subject, msg=f'tomcat{i[0]}_running')

def jvm_analysis(log_file, log_level, warning_interval, sender_alias, receive, subject):
    logger=log.Logger(log_file, log_level)
    db=database.db()

    logger.logger.debug("开始分析Jvm内存情况...")
    java_version=db.query_one("select version from tomcat_java_version")[0]
    table_name=f"tomcat_jstat{java_version}"

    sql=f"select port, ygc, ygct, fgc, fgct from {table_name} where record_time=(select max(record_time) from {table_name})"
    data=db.query_all(sql)

    ygc_warning_time=1
    fgc_warning_time=10
    #ygc_warning_time=0.01
    #fgc_warning_time=0

    for i in data:
        port=i[0]
        if i[1]==0:
            ygc_time=0
        else:
            ygc_time=i[2]/i[1]

        if i[3]==0:
            fgc_time=0
        else:
            fgc_time=i[4]/i[3]

        ygc_flag=0
        if ygc_time >= ygc_warning_time:
            ygc_flag=1
            logger.logger.warning(f"Tomcat({port})的YGC平均时间: {ygc_time}")
        warning_flag=warning.warning(logger, db, ygc_flag, port, "ygc", warning_interval)
        if warning_flag:
            warning_msg=f"Tomcat预警:\nTomcat({port})YGC平均时间为{ygc_time}\n"
            mail.send(logger, warning_msg, sender_alias, receive, subject, msg=f'tomcat{port}_ygc')

        fgc_flag=0
        if fgc_time >= fgc_warning_time:
            fgc_flag=1
            logger.logger.warning(f"Tomcat({port})的FGC平均时间: {fgc_time}")
        warning_flag=warning.warning(logger, db, fgc_flag, port, "fgc", warning_interval)
        if warning_flag:
            warning_msg=f"Tomcat预警:\nTomcat({port})FGC平均时间为{fgc_time}\n"
            mail.send(logger, warning_msg, sender_alias, receive, subject, msg=f'tomcat{port}_fgc')

def record(log_file, log_level, tomcat_port_list):
    logger=log.Logger(log_file, log_level)
    db=database.db()

    tomcat_port_and_pid={}
    for port in tomcat_port_list:
        tomcat_port_and_pid[port]=tools.find_pid(int(port))

    record_time=datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    for i in tomcat_port_and_pid:                # 根据pid获取相应信息
        pid=tomcat_port_and_pid[i]
        port=i
        logger.logger.debug(f"记录Tomcat({port})资源")
        if pid==0:
            logger.logger.error(f"Tomcat({port})未运行")
            sql="insert into tomcat_constant(record_time, pid, port, boot_time) values(?, ?, ?, ?)"
            db.update_one(sql, (record_time, pid, port, "0"))
        else:
            tomcat_info=psutil.Process(pid).as_dict()
            tomcat_create_time=datetime.datetime.fromtimestamp(tomcat_info["create_time"]).strftime("%Y-%m-%d %H:%M:%S")
            tomcat_cmdline=",".join(tomcat_info["cmdline"])
            constant_data=(record_time, pid, port, tomcat_create_time, tomcat_cmdline)
            constant_sql="insert into tomcat_constant values(?, ?, ?, ?, ?)"
            db.update_one(constant_sql, constant_data)

            tomcat_memory_percent=tomcat_info['memory_percent']
            tomcat_memory=psutil.virtual_memory()[0] * tomcat_info['memory_percent'] / 100
            tomcat_connections=len(tomcat_info["connections"])
            tomcat_num_threads=tomcat_info["num_threads"]
            variable_data=(record_time, pid, port, tomcat_memory, tomcat_memory_percent, tomcat_connections, tomcat_num_threads)
            variable_sql="insert into tomcat_variable values(?, ?, ?, ?, ?, ?, ?)"
            db.update_one(variable_sql, variable_data)


            # 内存回收
            logger.logger.debug(f"记录Tomcat({port})Jvm信息")
            cmd=f"jstat -gcutil {pid}"
            (status, message)=subprocess.getstatusoutput(cmd)
            message=message.splitlines()
            header=message[0].split()
            if len(header)==11:             # jdk8
                fields=["S0", "S1", "E", "O", "M", "CCS", "YGC", "YGCT", "FGC", "FGCT", "GCT", "record_time", "port"]
                sql=f"insert into tomcat_jstat8({','.join(fields)}) values(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)"
                java_version=8
            else:                           # jdk7
                fields=["S0", "S1", "E", "O", "P", "YGC", "YGCT", "FGC", "FGCT", "GCT", "record_time", "port"]
                sql=f"insert into tomcat_jstat7({','.join(fields)}) values(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)"
                java_version=7

            java_version_sql="update tomcat_java_version set version=?"
            db.update_one(java_version_sql, (java_version, ))        # 将java的版本写入数据库
            #logger.logger.debug(f"java version: {java_version}")

            data_index_list=[]                      # 按照fields的顺序从header中获取字段索引 
            for i in fields[:-2]:
                index=header.index(i)
                data_index_list.append(index)

            data_list=[]                            # 将jstat的数据按照data_index_list中的索引顺序放到data_list中
            data=message[1].split()
            for i in data_index_list:
                data_list.append(data[i])
            else:
                data_list.extend([record_time, port])
            db.update_one(sql, data_list)

if __name__ == "__main__":
    main()
