#!/usr/bin/env python
# *-* coding:utf8 *-*
# sky

from redis import Redis, sentinel
from lib import conf
from lib.printf import printf
import psutil, datetime


def analysis(role, ip, state):
    if state=="up" or state=="online":
        printf(f"Redis: {role}({ip})连接正常.", 1)
    else:
        printf(f"Redis: {role}({ip})无法连接.", 1)

def stats():
    check, password, redis_port, sentinel_port, sentinel_name, commands=conf.get("redis",
            "check",
            "password",
            "redis_port",
            "sentinel_port",
            "sentinel_name", 
            "commands"
            )

    if check=="1":
        """redis信息
        """
        printf("Redis信息:")
        try:
            normal=1
            conn=Redis(host="127.0.0.1",  port=redis_port, password=password)
            conn.ping()
        except Exception as e:
            normal=0
            msg=e
        if normal==1:
            """显示redis信息
            """
            redis_info=conn.info()

            pid=redis_info['process_id']
            printf(f"Redis Pid: {pid}")
            printf(f'启动时间: {datetime.datetime.fromtimestamp(psutil.Process(pid).create_time()).strftime("%Y-%m-%d %H:%M:%S")}')
            printf(f"连接数: {redis_info['connected_clients']}")
            printf(f"数据内存: {redis_info['used_memory_human']}")
            printf(f"进程内存: {redis_info['used_memory_rss_human']}")

            printf("-"*40)

            printf("集群信息:")
            role=redis_info['role']
            printf(f"角色: {role}")
            if role=="master":
                connected_slaves=redis_info['connected_slaves']
                printf(f"连接slave数量: {connected_slaves}")
                if connected_slaves!=0:
                    for i in range(connected_slaves):
                        slave=f"slave{i}"
                        ip=f"{redis_info[slave]['ip']}:{redis_info[slave]['port']}"
                        printf(f"{slave}信息: ip: {ip}, state: {redis_info[slave]['state']}")
                        analysis(role, ip, redis_info[slave]['state'])
            elif role=="slave":
                ip=f"{redis_info['master_host']}:{redis_info['master_port']}"
                printf(f"master信息: ip: {ip}, state: {redis_info['master_link_status']}")
                analysis(role, ip, redis_info['master_link_status'])

            """显示自定义命令
            """
            if commands is not None:
                printf("-"*40)
                printf("自定义命令查询:")
                commands_list=commands.split(",")
                for command in commands_list:
                    command=command.strip()
                    result=conn.execute_command(command)
                    printf(f"{command} 结果: {result}")

            conn.close()
        elif normal==0:
            printf(f"无法连接redis: {msg}", 2)

        printf("-"*40)
        """sentinel信息
        """
        if sentinel_port is not None:
            printf("Sentinel信息:", 2)
            conn=sentinel.Sentinel(
                    [('127.0.0.1', sentinel_port)], 
                    socket_timeout=1
                    )
            try:
                master=conn.discover_master(sentinel_name)
                slaves=conn.discover_slaves(sentinel_name)
                printf(f"master ip: {master[0]}:{master[1]}", 2)
                if len(slaves)==0:
                    printf(f"slave ip: 无", 2)
                else:
                    for i in slaves:
                        printf(f"slave ip: {i[0]}:{i[1]}", 2)
            except Exception as e:
                printf(f"无法获取sentinel信息, 请检查配置文件: {e}", 2)

        printf("-"*80)
        
if __name__ == "__main__":
    main()
