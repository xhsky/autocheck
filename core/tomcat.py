#!/usr/bin/env python
# *-* coding:utf8 *-*
# sky

from lib.printf import printf
from lib import conf, tools
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

def jstat(path, pid, seconds=20):
    #jstat -gcutil 1800 1000 20
    jstat_path=f"{path}/bin/jstat"
    if os.path.exists(jstat_path):
        cmd=f"{jstat_path} -gcutil {pid} 1000 {seconds}"
        (status, message)=subprocess.getstatusoutput(cmd)
        return message
    else:
        return "0"

def analysis(message):
    ygc=[]
    fgc=[]
    for i in message.splitlines()[1:]:
        i=i.split()
        if float(i[6])==0:
            ygc.append(0)
        else:
            ygc.append(float(i[7])/float(i[6]))
        if float(i[8])==0:
            fgc.append(0)
        else:
            fgc.append(float(i[9])/float(i[8]))

    ygc_max_time=max(ygc)
    fgc_max_time=max(fgc)
    ygc_warning_value=5
    fgc_warning_value=10

    if ygc_max_time > ygc_warning_value:
        printf(f"YGC每次时间为{ygc_max_time:.2f}秒.", 1)
    else:
        printf("YGC回收正常.", 1)
    if fgc_max_time > fgc_warning_value:
        printf(f"FGC每次时间为{fgc_max_time:.2f}秒", 1)
    else:
        printf("FGC回收正常.", 1)
    
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

if __name__ == "__main__":
    main()
