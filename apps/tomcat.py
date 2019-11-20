#!/usr/bin/env python
# *-* coding:utf8 *-*
# sky

#from lib.printf import printf
#from lib import conf, tools
from lib import database, mail, log
import psutil
import datetime
import subprocess
import os

def find_tomcat_pids(tomcat_port_list):
    """根据Tomcat端口获取相应的pid
    """
    tomcat_port_and_pid={}
    for port in tomcat_port_list:
        for i in psutil.net_connections():
            if port==str(i[3][1]) and i[6] is not None:
                tomcat_port_and_pid[port]=i[6]
                break
        else:
            tomcat_port_and_pid[port]=0
    return tomcat_port_and_pid

def jstat(pid):
    cmd=f"jstat -gcutil {pid} 1000 10"
    (status, message)=subprocess.getstatusoutput(cmd)
    return message

def analysis(logger, db, flag, section, value, warning_interval):
    warning_flag=0
    record_time_now=datetime.datetime.now()
    record_time=record_time_now.strftime("%Y-%m-%d %H:%M:%S")
    # 判断是否出现预警情况
    if flag:    # 出现预警情况
        sql="select record_time from warning_record where section=? and value=? and debug=0"
        data=db.query_one(sql, (section, value))        # 获取预警日志的时间记录
        # 无时间记录或时间记录在预警间隔之外, 则将该记录写入预警日志
        if data is None or record_time_now > datetime.datetime.strptime(data[0], "%Y-%m-%d %H:%M:%S") + datetime.timedelta(minutes=warning_interval):
            warning_flag=1
            sql="insert into warning_record values(?, ?, ?, ?)"
            db.update_one(sql, (record_time, section, value, 0))
            logger.logger.info(f"写入{section} {value}预警信息")
        else:
            logger.logger.info(f"当前处于{section} {value}预警间隔时间内, 不进行下一步处理")
    else:       # 非预警, 则将预警日志修复
        sql="select count(*) from warning_record where section=? and value=? and debug=0"
        exist=db.query_one(sql, (section, value))[0]
        if exist:
            logger.logger.info(f"{section} {value}预警修复")
            sql="update warning_record set debug=1 where section=? and value=?"
            db.update_one(sql, (section, value))
    return warning_flag
def analysis1(logger, db, port, pid, warning_interval):
    warning_msg=None
    record_time_now=datetime.datetime.now()
    record_time=record_time_now.strftime("%Y-%m-%d %H:%M:%S")
    if pid == 0:
        sql="select record_time from warning_record where section=? and value=? and debug=0"
        data=db.query_one(sql, (port, "running"))
        if data is None or record_time_now > datetime.datetime.strptime(data[0], "%Y-%m-%d %H:%M:%S") + datetime.timedelta(minutes=warning_interval):
            warning_msg=f"Tomcat预警:\nTomcat({port})未运行\n"
            sql="insert into warning_record values(?, ?, ?, ?)"
            db.update_one(sql, (record_time, port, "running", 0))
            logger.logger.info(f"写入Tomcat{port}预警信息")
        else:
            logger.logger.info("当前处于预警间隔时间内, 不进行下一步处理")
    else:
        sql="select count(*) from warning_record where section=? and value=? and debug=0"
        exist=db.query_one(sql, (port, "running"))[0]
        if exist:
            logger.logger.info(f"{port}:running修复")
            sql="update warning_record set debug=1 where section=? and value=?"
            db.update_one(sql, (port, "running"))
    return warning_msg

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
        warning_flag=analysis(logger, db, flag, i[0], "running", warning_interval)
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

    #ygc_warning_time=1
    #fgc_warning_time=10
    ygc_warning_time=0.01
    fgc_warning_time=0

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
        warning_flag=analysis(logger, db, ygc_flag, port, "ygc", warning_interval)
        if warning_flag:
            warning_msg=f"Tomcat预警:\nTomcat({port})YGC平均时间为{ygc_time}\n"
            mail.send(logger, warning_msg, sender_alias, receive, subject, msg=f'tomcat{port}_ygc')

        fgc_flag=0
        if fgc_time >= fgc_warning_time:
            fgc_flag=1
            logger.logger.warning(f"Tomcat({port})的FGC平均时间: {fgc_time}")
        warning_flag=analysis(logger, db, fgc_flag, port, "fgc", warning_interval)
        if warning_flag:
            warning_msg=f"Tomcat预警:\nTomcat({port})FGC平均时间为{fgc_time}\n"
            mail.send(logger, warning_msg, sender_alias, receive, subject, msg=f'tomcat{port}_fgc')


    
'''
def stats():
    check, tomcat_port, java_home, jstat_duration=conf.get("tomcat",
            "check",
            "tomcat_port",
            "java_home",
            "jstat_duration"
            )

    if check=="1":
        printf("Tomcat信息:", 2)

        tomcat_port_list=[]                          # 将tomcat_port参数改为列表
        for i in tomcat_port.split(","):        
            tomcat_port_list.append(i.strip())
        tomcat_port_and_pid=find_tomcat_pids(tomcat_port_list)            # 获取Tomcat端口与pid对应的字典

        for i in tomcat_port_and_pid:                # 根据pid获取相应信息
            printf(f"Tomcat({i}):", 2)
            if tomcat_port_and_pid[i]==0:
                printf(f"检查该Tomcat({i})是否启动", 2)
                printf("-"*40)
                continue
            pid=tomcat_port_and_pid[i]
            tomcat_info=psutil.Process(pid).as_dict()
            printf(f"Tomcat Pid: {pid}")

            tomcat_create_time=datetime.datetime.fromtimestamp(tomcat_info["create_time"]).strftime("%Y-%m-%d %H:%M:%S")
            printf(f"程序启动时间: {tomcat_create_time}")

            tomcat_memory_percent=f"{tomcat_info['memory_percent']:.2f}"
            tomcat_memory=tools.format_size(psutil.virtual_memory()[0] * tomcat_info['memory_percent'] / 100)
            printf(f"内存占用: {tomcat_memory}/{tomcat_memory_percent}%")

            tomcat_connections=len(tomcat_info["connections"])
            printf(f"连接数: {tomcat_connections}")

            tomcat_num_threads=tomcat_info["num_threads"]
            printf(f"线程数: {tomcat_num_threads}")

            tomcat_cmdline=tomcat_info["cmdline"]
            printf(f"启动参数: {tomcat_cmdline}")


            printf(f"内存回收:")
            if java_home is not None and jstat_duration is not None:
                jstat_message=jstat(java_home, pid, jstat_duration)
                if jstat_message!="0":
                    printf(f"{jstat_message}")
                    analysis(jstat_message)
                else:
                    printf(f"请检查配置文件, java_home参数的配置无法找到{java_home}/bin/jstat, 故不能进行jvm内存回收检查")
            else:
                printf("请检查配置文件中java_home和jstat_duration两个参数配置")

            printf("-"*40)
        printf("-"*80)
'''

def record(log_file, log_level, tomcat_port_list):
    logger=log.Logger(log_file, log_level)
    db=database.db()
    tomcat_port_and_pid=find_tomcat_pids(tomcat_port_list)       # 获取Tomcat端口与pid对应的字典
    #logger.logger.debug(f"Tomcat Port and Pid: {tomcat_port_and_pid}")

    record_time=datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    for i in tomcat_port_and_pid:                # 根据pid获取相应信息
        pid=tomcat_port_and_pid[i]
        port=i
        logger.logger.debug(f"记录Tomcat({port})资源")

        ''' 判断constant表有无相同数据再插入
        if pid==0:
            logger.logger.error(f"Tomcat({port})未运行")
            tomcat_create_time="0"
            #sql="select boot_time from tomcat_constant where port=? and pid=? order by record_time desc limit 1"
            sql="select pid from tomcat_constant where port=? order by record_time desc"
            pid_in_db=db.query_one(sql, (port,))
            if pid_in_db is None or pid_in_db[0]!=0:
                sql="insert into tomcat_constant(record_time, pid, port, boot_time) values(?, ?, ?, ?)"
                db.update_one(sql, (record_time, pid, port, "0"))
        else:
            tomcat_info=psutil.Process(pid).as_dict()
            tomcat_create_time=datetime.datetime.fromtimestamp(tomcat_info["create_time"]).strftime("%Y-%m-%d %H:%M:%S")
            sql="select boot_time, pid from tomcat_constant where port=? order by record_time desc"
            data=db.query_one(sql, (port, ))
            if data is None or data[0]!=tomcat_create_time or data[1]!=pid:
                tomcat_cmdline=",".join(tomcat_info["cmdline"])
                constant_data=(record_time, pid, port, tomcat_create_time, tomcat_cmdline)
                constant_sql="insert into tomcat_constant values(?, ?, ?, ?, ?)"
                db.update_one(constant_sql, constant_data)

            tomcat_memory_percent=tomcat_info['memory_percent']
            tomcat_memory=psutil.virtual_memory()[0] * tomcat_info['memory_percent'] / 100
            tomcat_connections=len(tomcat_info["connections"])
            tomcat_num_threads=tomcat_info["num_threads"]
            variable_data=(record_time, pid, tomcat_memory, tomcat_memory_percent, tomcat_connections, tomcat_num_threads)
            variable_sql="insert into tomcat_variable values(?, ?, ?, ?, ?, ?)"
            db.update_one(variable_sql, variable_data)


            # 内存回收
            logger.logger.debug(f"记录Tomcat({port})Jvm信息")
            cmd=f"jstat -gcutil {pid}"
            (status, message)=subprocess.getstatusoutput(cmd)
            message=message.splitlines()
            header=message[0].split()
            if len(header)==11:             # jdk8
                fields=["S0", "S1", "E", "O", "M", "CCS", "YGC", "YGCT", "FGC", "FGCT", "GCT", "record_time", "pid"]
                sql=f"insert into tomcat_jstat8({','.join(fields)}) values(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)"
                java_version=8
            else:                           # jdk7
                fields=["S0", "S1", "E", "O", "P", "YGC", "YGCT", "FGC", "FGCT", "GCT", "record_time", "pid"]
                sql=f"insert into tomcat_jstat7({','.join(fields)}) values(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)"
                java_version=7

            java_version_sql="update tomcat_java_version set version=?"
            db.update_one(java_version_sql, (java_version, ))        # 将java的版本写入数据库
            logger.logger.debug(f"java version: {java_version}")

            data_index_list=[]                      # 按照fields的顺序从header中获取字段索引 
            for i in fields[:-2]:
                index=header.index(i)
                data_index_list.append(index)

            data_list=[]                            # 将jstat的数据按照data_index_list中的索引顺序放到data_list中
            data=message[1].split()
            for i in data_index_list:
                data_list.append(data[i])
            else:
                data_list.extend([record_time, pid])
            db.update_one(sql, data_list)
        '''
        if pid==0:
            logger.logger.error(f"Tomcat({port})未运行")
            #tomcat_create_time="0"
            #sql="select boot_time from tomcat_constant where port=? and pid=? order by record_time desc limit 1"
            #sql="select pid from tomcat_constant where port=? order by record_time desc"
            #pid_in_db=db.query_one(sql, (port,))
            #if pid_in_db is None or pid_in_db[0]!=0:
            sql="insert into tomcat_constant(record_time, pid, port, boot_time) values(?, ?, ?, ?)"
            db.update_one(sql, (record_time, pid, port, "0"))
        else:
            tomcat_info=psutil.Process(pid).as_dict()
            tomcat_create_time=datetime.datetime.fromtimestamp(tomcat_info["create_time"]).strftime("%Y-%m-%d %H:%M:%S")
            #sql="select boot_time, pid from tomcat_constant where port=? order by record_time desc"
            #data=db.query_one(sql, (port, ))
            #if data is None or data[0]!=tomcat_create_time or data[1]!=pid:
            tomcat_cmdline=",".join(tomcat_info["cmdline"])
            constant_data=(record_time, pid, port, tomcat_create_time, tomcat_cmdline)
            constant_sql="insert into tomcat_constant values(?, ?, ?, ?, ?)"
            db.update_one(constant_sql, constant_data)

            tomcat_memory_percent=tomcat_info['memory_percent']
            tomcat_memory=psutil.virtual_memory()[0] * tomcat_info['memory_percent'] / 100
            tomcat_connections=len(tomcat_info["connections"])
            tomcat_num_threads=tomcat_info["num_threads"]
            variable_data=(record_time, pid, tomcat_memory, tomcat_memory_percent, tomcat_connections, tomcat_num_threads)
            variable_sql="insert into tomcat_variable values(?, ?, ?, ?, ?, ?)"
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
