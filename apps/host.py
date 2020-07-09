#!/usr/bin/env python
# *-* coding:utf8 *-*
# sky

from lib import log, database, notification, warning
import datetime
import psutil

def disk_record(log_file, log_level):
    logger=log.Logger(log_file, log_level)
    db=database.db()
    logger.logger.debug("记录磁盘信息...")
    record_time=datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    disk_list=[]
    all_disk=psutil.disk_partitions()
    for i in all_disk:
        disk_name=i[0]
        mounted=i[1]
        size=psutil.disk_usage(mounted)
        total=size[0]
        used=size[1]
        used_percent=size[3]
        free=size[2]
        disk_list.append((record_time, disk_name, total, used, used_percent, free, mounted))

    sql="insert into disk values(?, ?, ?, ?, ?, ?, ?)"
    db.update_all(sql, disk_list)

def disk_analysis(log_file, log_level, warning_percent, warning_interval, notify_dict):
    logger=log.Logger(log_file, log_level)
    db=database.db()
    sql=f"select record_time, name, used_percent, mounted from disk where record_time=(select max(record_time) from disk)"
    data=db.query_all(sql)

    logger.logger.debug("分析disk...")
    for i in data:
        flag=0                 # 是否有预警信息
        if i[2] >= warning_percent:
            flag=1
            logger.logger.warning(f"{i[3]}目录({i[1]})已使用{i[2]}%")
        warning_flag=warning.warning(logger, db, flag, "disk", i[3], warning_interval)
        if warning_flag:
            warning_msg=f"磁盘预警:\n{i[3]}目录({i[1]})已使用{i[2]}%\n"
            notification.send(logger, warning_msg, notify_dict, msg=i[3])

def cpu_record(log_file, log_level):
    logger=log.Logger(log_file, log_level)
    db=database.db()
    logger.logger.debug("记录cpu信息...")
    sql="insert into cpu values(?, ?, ?)"
    record_time=datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cpu_count=psutil.cpu_count()
    cpu_used_percent=psutil.cpu_percent(interval=5)
    db.update_one(sql, (record_time, cpu_count, cpu_used_percent))

def cpu_analysis(log_file, log_level, warning_percent, warning_interval, notify_dict):
    logger=log.Logger(log_file, log_level)
    db=database.db()
    sql="select record_time, cpu_used_percent from cpu order by record_time desc"
    data=db.query_one(sql)
    cpu_used_percent=float(data[1])

    logger.logger.debug("分析CPU...")
    flag=0                 # 是否有预警信息
    if cpu_used_percent >= warning_percent:
        flag=1
        logger.logger.warning(f"CPU当前使用率已达到{cpu_used_percent}%")

    warning_flag=warning.warning(logger, db, flag, "cpu", "used_percent", warning_interval)
    if warning_flag:
        warning_msg=f"CPU预警:\nCPU使用率当前已达到{cpu_used_percent}%"
        notification.send(logger, warning_msg, notify_dict, msg='cpu_used_percent')

def memory_record(log_file, log_level):
    logger=log.Logger(log_file, log_level)
    db=database.db()
    logger.logger.debug("记录内存信息...")
    record_time=datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    mem=psutil.virtual_memory()

    sql="insert into memory values(?, ?, ?, ?, ?, ?)"
    total, avail, used, used_percent, free=mem[0], mem[1], mem[3], mem[2], mem[4]
    db.update_one(sql, (record_time, total, avail, used, used_percent, free))

def memory_analysis(log_file, log_level, warning_percent, warning_interval, notify_dict):
    logger=log.Logger(log_file, log_level)
    db=database.db()
    sql="select record_time, used_percent from memory order by record_time desc"
    data=db.query_one(sql)
    mem_used_percent=float(data[1])

    logger.logger.debug("分析Mem...")
    flag=0                 # 是否有预警信息
    if mem_used_percent > warning_percent:
        flag=1
        logger.logger.warning(f"内存当前使用率当前已达到{mem_used_percent}%")
    warning_flag=warning.warning(logger, db, flag, "mem", "used_percent", warning_interval)
    if warning_flag:
        warning_msg=f"内存预警:\n内存当前使用率当前已达到{mem_used_percent}%"
        notification.send(logger, warning_msg, notify_dict, msg='mem_used_percent')

def swap_record(log_file, log_level):
    logger=log.Logger(log_file, log_level)
    db=database.db()
    logger.logger.debug("记录交换分区信息...")
    record_time=datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    sql="insert into swap values(?, ?, ?, ?, ?)"

    swap_mem=psutil.swap_memory()
    total, used, used_percent, free=swap_mem[0], swap_mem[1], swap_mem[3], swap_mem[2]
    db.update_one(sql, (record_time, total, used, used_percent, free))

def boot_time_record(log_file, log_level):
    logger=log.Logger(log_file, log_level)
    db=database.db()
    logger.logger.debug("记录服务器启动时间信息...")
    record_time=datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    boot_time=datetime.datetime.fromtimestamp(psutil.boot_time()).strftime("%Y-%m-%d %H:%M:%S")

    """
    # 判断启动时间是否有变化再插入
    sql="select boot_time from boot_time order by record_time desc limit 1;"
    data=db.query_one(sql)
    if data is None or data[0]!=boot_time:
        sql="insert into boot_time values(?, ?)"
        db.update_one(sql, (record_time, boot_time))
    """
    sql="insert into boot_time values(?, ?)"
    db.update_one(sql, (record_time, boot_time))

if __name__ == "__main__":
    info()
