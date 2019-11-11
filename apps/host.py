#!/usr/bin/env python
# *-* coding:utf8 *-*
# sky

#from lib.printf import printf
#from lib import tools

#from apscheduler.schedulers.blocking import BlockingScheduler
#from lib import log, database
from lib import database
import datetime
import psutil

def disk_record(logger):
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

def disk():
    all_disk=psutil.disk_partitions()

    # 显示
    printf("磁盘信息:")
    disk_name_length=[]         # 获取磁盘名称的长度, 用于下方格式化输出
    for disk_name in all_disk:
        disk_name_length.append(len(disk_name[0]))
    length=max(disk_name_length)
    space_length=f" "*(length-4)

    printf(f"磁盘{space_length}  大小      已使用            可用      挂载点")
    for i in all_disk:
        size=psutil.disk_usage(i[1])
        total=tools.format_size(size[0])
        used=f"{tools.format_size(size[1])}/{size[3]}%"
        free=tools.format_size(size[2])
        printf(f"{i[0]:<{length}}  {total:<8}  {used:<16}  {free:<8}  {i[1]:<}")

    # 分析
    normal=0
    for i in all_disk:
        size=psutil.disk_usage(i[1])
        used_percent=size[3]
        free=size[2]
        warning_value=95
        if used_percent > warning_value:     # 使用率大于95%或可用空间小于5G
            printf(f"磁盘'{i[1]}'空间已超过{warning_value}%, 请查看", 1)
            normal=1

    if normal==0:
        printf("磁盘空间正常.", 1)

def cpu_record(logger):
    db=database.db()
    logger.logger.debug("记录cpu信息...")
    sql="insert into cpu values(?, ?, ?)"
    record_time=datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cpu_count=psutil.cpu_count()
    cpu_used_percent=psutil.cpu_percent(interval=5)
    
    db.update_one(sql, (record_time, cpu_count, cpu_used_percent))

def memory_record(logger):
    db=database.db()
    logger.logger.debug("记录内存信息...")
    record_time=datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    mem=psutil.virtual_memory()

    sql="insert into memory values(?, ?, ?, ?, ?, ?)"
    total, avail, used, used_percent, free=mem[0], mem[1], mem[3], mem[2], mem[4]

    db.update_one(sql, (record_time, total, avail, used, used_percent, free))

def memory():
    printf("内存信息:")
    mem=psutil.virtual_memory()

    # 显示
    printf(f"总内存(total): {tools.format_size(mem[0])}")
    printf(f"可用内存(available): {tools.format_size(mem[1])}")
    printf(f"已用内存(used): {tools.format_size(mem[3])}/{mem[2]}%") # (total-avail)/total
    printf(f"空闲内存(free): {tools.format_size(mem[4])}")

    # 分析
    warning_value=95
    if mem[2] > warning_value:
        printf(f"内存使用已超过{warning_value}%.")
        normal=1

    normal=0
    if normal==0:
        printf("内存空间正常.", 1)

def swap_record(logger):
    db=database.db()
    logger.logger.debug("记录交换分区信息...")
    record_time=datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    sql="insert into swap values(?, ?, ?, ?, ?)"

    swap_mem=psutil.swap_memory()
    total, used, used_percent, free=swap_mem[0], swap_mem[1], swap_mem[3], swap_mem[2]
    db.update_one(sql, (record_time, total, used, used_percent, free))

def boot_time_record(logger):
    db=database.db()
    logger.logger.debug("记录服务器启动时间信息...")
    record_time=datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    boot_time=datetime.datetime.fromtimestamp(psutil.boot_time()).strftime("%Y-%m-%d %H:%M:%S")

    # 判断启动时间是否有变化再插入
    sql="select boot_time from boot_time order by record_time desc limit 1;"
    data=db.query_one(sql)
    if data is None or data[0]!=boot_time:
        sql="insert into boot_time values(?, ?)"
        db.update_one(sql, (record_time, boot_time))

"""
def do_job():
    log_file, log_level=log.get_log_args()
    logger=log.Logger(log_file, log_level)

    logger.logger.info("开始采集资源信息...")
    try:
        scheduler=BlockingScheduler()
        scheduler.add_job(disk_record, 'interval', args=[logger], minutes=1, id='disk')
        scheduler.add_job(cpu_record, 'interval', args=[logger], minutes=2, id='cpu')
        scheduler.add_job(memory_record, 'interval', args=[logger], minutes=1, id='memory')
        scheduler.add_job(swap_record, 'interval', args=[logger], minutes=1, id='swap')
        scheduler.add_job(boot_time_record, 'interval', args=[logger], minutes=1, id='boot_time')
        scheduler.start()
    except Exception as e:
        logger.logger.error(e)
"""

    
if __name__ == "__main__":
    info()
