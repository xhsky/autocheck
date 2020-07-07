#!/usr/bin/env python
# *-* coding:utf8 *-*
# sky

from redis import Redis, sentinel
from lib import database, log, notification, tools, warning
import psutil, datetime


def running_analysis(log_file, log_level, warning_interval, notify_dict):
    logger=log.Logger(log_file, log_level)
    logger.logger.debug("开始分析Redis运行情况...")
    db=database.db()
    sql="select port, pid from redis_constant where record_time=(select max(record_time) from redis_constant)"
    port, pid=db.query_one(sql)
    flag= 1 if pid==0 else 0        # 是否预警
    warning_flag=warning.warning(logger, db, flag, "redis", "running", warning_interval)
    if warning_flag:
        warning_msg=f"Redis预警:\nRedis({port})未运行"
        notification.send(logger, warning_msg, notify_dict, msg=f'redis_running')

def master_slave_analysis(log_file, log_level, warning_interval,notify_dict):
    logger=log.Logger(log_file, log_level)
    db=database.db()
    sql="select a.role, a.master_link_status, a.master_host from redis_slave as a,redis_role as b where a.record_time=b.record_time and a.role=b.role"
    data=db.query_one(sql)
    if data is not None:
        logger.logger.debug("开始分析Redis主从信息")
        if data[1]=="up" or data[1]=="online":
            flag=0
        else:
            flag=1
    else:
        flag=0

    warning_flag=warning.warning(logger, db, flag, "redis", "slave", warning_interval)
    if warning_flag:
        warning_msg=f"Redis预警:\nRedis slave无法连接master({data[2]})\n"
        mail.send(logger, warning_msg, notify_dict, msg=f'redis_slave')

def record(log_file, log_level, redis_password, redis_port, sentinel_port, sentinel_name, commands):
    logger=log.Logger(log_file, log_level)
    db=database.db()
    logger.logger.debug("记录Redis资源")
    record_time=datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    port=int(redis_port)
    pid=tools.find_pid(port)
    normal=1
    if pid==0:
        logger.logger.error(f"Redis({port})未运行")
        sql="insert into redis_constant(record_time, pid, port, boot_time) values(?, ?, ?, ?)"
        db.update_one(sql, (record_time, pid, port, "0"))
        db.update_one("update redis_role set record_time=?, role=?", ("0", "master"))
    else:
        try:
            conn=Redis(host="127.0.0.1",  port=redis_port, password=redis_password)
            conn.ping()
        except Exception as e:
            normal=0
            msg=e
        if normal==1:
            redis_info=conn.info()
            redis_psutil_info=psutil.Process(pid).as_dict()
            boot_time=datetime.datetime.fromtimestamp(redis_psutil_info["create_time"]).strftime("%Y-%m-%d %H:%M:%S")
            sql="insert into redis_constant(record_time, pid, port, boot_time) values(?, ?, ?, ?)"
            db.update_one(sql, (record_time, pid, redis_port, boot_time))

            redis_memory_percent=redis_psutil_info['memory_percent']
            redis_memory=psutil.virtual_memory()[0] * redis_memory_percent / 100
            redis_connections=redis_info['connected_clients']
            redis_num_threads=redis_psutil_info['num_threads']
            sql="insert into redis_variable values(?, ?, ?, ?, ?, ?)"
            db.update_one(sql, (record_time, pid, redis_memory, redis_memory_percent, redis_connections, redis_num_threads))

            logger.logger.debug("记录Redis集群资源")
            role=redis_info['role']
            db.update_one("update redis_role set record_time=?, role=?", (record_time, role))
            if role=="master":
                connected_slaves=redis_info['connected_slaves']
                sql="replace into redis_master values(?, ?, ?, ?)"
                db.update_one(sql, (record_time, pid, role, connected_slaves))
                slaves_list=[]
                if connected_slaves!=0:
                    for i in range(connected_slaves):
                        slave=f"slave{i}"
                        slaves_list.append((record_time, redis_info[slave]['ip'], redis_info[slave]['port'], redis_info[slave]['state']))
                    sql="replace into redis_slaves_info values(?, ?, ?, ?)"
                    db.update_all(sql, slaves_list)
            elif role=="slave":
                sql="replace into redis_slave values(?, ?, ?, ?, ?, ?)"
                db.update_one(sql, (record_time, pid, role, redis_info['master_host'], redis_info['master_port'], redis_info['master_link_status']))

            """显示自定义命令
            if commands is not None:
                printf("-"*40)
                printf("自定义命令查询:")
                commands_list=commands.split(",")
                for command in commands_list:
                    command=command.strip()
                    result=conn.execute_command(command)
                    printf(f"{command} 结果: {result}")
            """
            conn.close()
        elif normal==0:
            logger.logger.error(f"无法连接redis: {msg}")
            sql="insert into error values(?, ?, ?, ?, ?)"
            db.update_one(sql, (record_time, "Redis", "connection", str(msg), 0))
        
    # sentinel信息
    if sentinel_port is not None:
        logger.logger.debug(f"记录Redis Sentinel信息...")
        conn=sentinel.Sentinel(
                [('127.0.0.1', sentinel_port)], 
                socket_timeout=1
                )
        try:
            sentinel_info=[]
            master=conn.discover_master(sentinel_name)
            sentinel_info.append((record_time, 'master', master[0], master[1]))
            slaves=conn.discover_slaves(sentinel_name)
            for i in slaves:
                sentinel_info.append((record_time, 'slave', i[0], i[1]))
            sql="replace into redis_sentinel values(?, ?, ?, ?)"
            db.update_all(sql, sentinel_info)
        except Exception as e:
            logger.logger.error(f"Redis Sentinel无法连接...")
            sql="insert into error values(?, ?, ?, ?, ?)"
            db.update_one(sql, (record_time, 'Sentinel', "connection", str(e), 0))
        
if __name__ == "__main__":
    main()
