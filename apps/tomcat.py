#!/usr/bin/env python
# *-* coding:utf8 *-*
# sky

#from lib.printf import printf
#from lib import conf, tools
from lib import database
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

"""
def jstat(path, pid, seconds=20):
    #jstat -gcutil 1800 1000 20
    jstat_path=f"{path}/bin/jstat"
    if os.path.exists(jstat_path):
        cmd=f"{jstat_path} -gcutil {pid} 1000 {seconds}"
        (status, message)=subprocess.getstatusoutput(cmd)
        return message
    else:
        return "0"
"""
def jstat(pid):
    cmd=f"jstat -gcutil {pid} 1000 10"
    (status, message)=subprocess.getstatusoutput(cmd)
    return message

def analysis(message):
    ygc=[]
    fgc=[]
    columns=message.splitlines()[0].split()

    ygc_column=columns.index("YGC")
    ygct_column=columns.index("YGCT")
    fgc_column=columns.index("FGC")
    fgct_column=columns.index("FGCT")

    for i in message.splitlines()[1:]:
        i=i.split()
        if float(i[ygc_column])==0:
            ygc.append(0)
        else:
            ygc.append(float(i[ygct_column])/float(i[ygc_column]))
        if float(i[fgc_column])==0:
            fgc.append(0)
        else:
            fgc.append(float(i[fgct_column])/float(i[fgc_column]))

    ygc_max_time=max(ygc)
    fgc_max_time=max(fgc)
    ygc_warning_value=1
    fgc_warning_value=10

    if ygc_max_time > ygc_warning_value:
        printf(f"YGC每次时间为{ygc_max_time:.2f}秒.", 1)
    else:
        printf(f"YGC回收正常({ygc_max_time:.2f}秒).", 1)
    if fgc_max_time > fgc_warning_value:
        printf(f"FGC每次时间为{fgc_max_time:.2f}秒", 1)
    else:
        printf(f"FGC回收正常({fgc_max_time:.2f}秒).", 1)
    
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

def record(logger, tomcat_port_list):
    db=database.db()
    tomcat_port_and_pid=find_tomcat_pids(tomcat_port_list)       # 获取Tomcat端口与pid对应的字典
    #logger.logger.debug(f"Tomcat Port and Pid: {tomcat_port_and_pid}")
    for i in tomcat_port_and_pid:                # 根据pid获取相应信息
        record_time=datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        pid=tomcat_port_and_pid[i]
        port=i
        logger.logger.debug(f"记录Tomcat({port})资源")

        if pid==0:
            logger.logger.error(f"Tomcat({port})未运行")
            tomcat_create_time="0"
            sql="select boot_time from tomcat_constant where port=? and pid=? order by record_time desc limit 1"
            boottime_in_db=db.query_one(sql, (port, pid))
            if boottime_in_db is None or boottime_in_db[0]!=tomcat_create_time:
                sql="insert into tomcat_constant(record_time, pid, port, boot_time) values(?, ?, ?, ?)"
                db.update_one(sql, (record_time, pid, port, "0"))
        else:
            tomcat_info=psutil.Process(pid).as_dict()
            tomcat_create_time=datetime.datetime.fromtimestamp(tomcat_info["create_time"]).strftime("%Y-%m-%d %H:%M:%S")
            sql="select boot_time from tomcat_constant where port=? and pid=? order by record_time desc limit 1"
            boottime_in_db=db.query_one(sql, (port, pid))
            if boottime_in_db is None or boottime_in_db[0]!=tomcat_create_time:
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
                java_version_sql="replace into tomcat_java_version values(?, ?)"
                java_version=8
            else:                           # jdk7
                fields=["S0", "S1", "E", "O", "P", "YGC", "YGCT", "FGC", "FGCT", "GCT", "record_time", "pid"]
                sql=f"insert into tomcat_jstat7({','.join(fields)}) values(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)"
                java_version_sql="replace into tomcat_java_version values(?, ?)"
                java_version=7

            db.update_one(java_version_sql, (record_time, java_version))        # 将java的版本写入数据库
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

if __name__ == "__main__":
    main()
