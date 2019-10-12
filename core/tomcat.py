#!/usr/bin/env python
# *-* coding:utf8 *-*
# sky

from lib.printf import printf
from lib import conf
import psutil
import datetime
import subprocess
import os

def find_tomcat_pids(tomcat_dir_list):
    """使用 -Dcatalina.home=/data/tomcat 来匹配多个Tomcat.
    并将配置文件中tomcat_home参数最后的"/"去掉
    """
    tomcat_dir_and_pid={}
    for i in tomcat_dir_list:
        for proc in psutil.process_iter(attrs=["name", "pid", "cmdline"]):
            match_mode=f"-Dcatalina.home={i}"
            if match_mode.endswith("/"):
                match_mode=match_mode[:-1]

            if 'java' in proc.info['name'] and ( match_mode in proc.info['cmdline'] or f"{match_mode}/" in proc.info['cmdline']):
                tomcat_dir_and_pid[i]=proc.info['pid']
                break
        else:
            tomcat_dir_and_pid[i]=0

    return tomcat_dir_and_pid

def jstat(path, pid, seconds=20):
    #jstat -gcutil 1800 1000 20
    jstat_path=f"{path}/bin/jstat"
    if os.path.exists(jstat_path):
        cmd=f"{jstat_path} -gcutil {pid} 1000 {seconds}"
        (status, message)=subprocess.getstatusoutput(cmd)
        return message
    else:
        return "0"

def stats():
    check, tomcat_home, java_home, jstat_duration=conf.get("tomcat",
            "check",
            "tomcat_home",
            "java_home",
            "jstat_duration"
            )

    if check=="1":
        printf("Tomcat信息:")

        tomcat_dir_list=[]                          # 将tomcat_home参数改为列表
        for i in tomcat_home.split(","):        
            tomcat_dir_list.append(i.strip())
        tomcat_dir_and_pid=find_tomcat_pids(tomcat_dir_list)            # 获取Tomcat目录与pid对应的字典

        for i in tomcat_dir_and_pid:                # 根据pid获取相应信息
            printf(f"Tomcat({i}):")
            if tomcat_dir_and_pid[i]==0:
                printf(f"检查该Tomcat({i})是否启动")
                printf("-"*40)
                continue
            pid=tomcat_dir_and_pid[i]
            tomcat_info=psutil.Process(pid).as_dict()
            printf(f"Pid: {pid}")

            tomcat_create_time=datetime.datetime.fromtimestamp(tomcat_info["create_time"]).strftime("%Y-%m-%d %H:%M:%S")
            printf(f"程序启动时间: {tomcat_create_time}")

            tomcat_memory_percent=f"{tomcat_info['memory_percent']:.2f}"
            printf(f"内存占用(%): {tomcat_memory_percent}")

            tomcat_connections=len(tomcat_info["connections"])
            printf(f"连接数: {tomcat_connections}")

            tomcat_num_threads=tomcat_info["num_threads"]
            printf(f"线程数: {tomcat_num_threads}")

            tomcat_cmdline=tomcat_info["cmdline"]
            printf(f"启动参数: {tomcat_cmdline}")


            """ 
            """
            printf(f"内存回收:")
            if java_home is not None and jstat_duration is not None:
                jstat_message=jstat(java_home, pid, jstat_duration)
                if jstat_message!="0":
                    printf(f"{jstat_message}")
                else:
                    printf(f"请检查配置文件, java_home参数的配置无法找到{java_home}/bin/jstat, 故不能进行jvm内存回收检查")
            else:
                printf("请检查配置文件中java_home和jstat_duration两个参数配置")

            printf("-"*40)
        printf("-"*80)

if __name__ == "__main__":
    main()
