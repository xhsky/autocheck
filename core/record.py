#!/usr/bin/env python
# *-* coding:utf8 *-*
# sky

from apscheduler.schedulers.blocking import BlockingScheduler
from lib import log, conf
from apps import host, tomcat, redis, backup, mysql
import datetime

def record():
    log_file, log_level=log.get_log_args()
    logger=log.Logger(log_file, log_level)
    logger.logger.info("开始采集资源信息...")

    scheduler=BlockingScheduler()

    # host资源记录
    logger.logger.info("开始采集主机资源信息...")
    disk_interval, cpu_interval, memory_interval, swap_interval, boot_time_interval=conf.get("host", 
            "disk_interval",
            "cpu_interval",
            "memory_interval",
            "swap_interval",
            "boot_time_interval"
            )
    scheduler.add_job(host.disk_record, 'interval', next_run_time=datetime.datetime.now(), args=[logger], minutes=int(disk_interval), id='disk')
    scheduler.add_job(host.cpu_record, 'interval', next_run_time=datetime.datetime.now(), args=[logger], minutes=int(cpu_interval), id='cpu')
    scheduler.add_job(host.memory_record, 'interval', next_run_time=datetime.datetime.now(), args=[logger], minutes=int(memory_interval), id='memory')
    scheduler.add_job(host.swap_record, 'interval', next_run_time=datetime.datetime.now(), args=[logger], minutes=int(swap_interval), id='swap')
    scheduler.add_job(host.boot_time_record, 'interval', next_run_time=datetime.datetime.now(), args=[logger], minutes=int(boot_time_interval), id='boot_time')

    # tomcat资源
    tomcat_check, tomcat_interval, tomcat_port=conf.get("tomcat", 
            "check", 
            "tomcat_interval", 
            "tomcat_port", 
            )
    if tomcat_check=='1':
        logger.logger.info("开始采集Tomcat资源信息...")
        tomcat_port_list=[]                                                 # 将tomcat_port参数改为列表
        for i in tomcat_port.split(","):
            tomcat_port_list.append(i.strip())
        tomcat_port_and_pid=tomcat.find_tomcat_pids(tomcat_port_list)       # 获取Tomcat端口与pid对应的字典
        logger.logger.debug(f"Tomcat Port and Pid: {tomcat_port_and_pid}")
        scheduler.add_job(tomcat.record, 'interval', args=[logger, tomcat_port_and_pid], next_run_time=datetime.datetime.now(), minutes=int(tomcat_interval), id='tomcat')

    # redis资源
    redis_check, redis_interval, redis_password, redis_port, sentinel_port, sentinel_name, commands=conf.get("redis", 
           "check",
           "redis_interval", 
           "password",
           "redis_port",
           "sentinel_port",
           "sentinel_name",
           "commands"
           )
    if redis_check=="1":
        logger.logger.info("开始采集Redis资源信息...")
        scheduler.add_job(redis.record, 'interval', args=[logger, redis_password, redis_port, sentinel_port, sentinel_name, commands], \
                next_run_time=datetime.datetime.now(), minutes=int(redis_interval), id='redis')

    # backup
    backup_check, backup_dir, backup_regular, backup_cron_time=conf.get("backup", 
            "check", 
            "dir", 
            "regular", 
            "cron_time"
            )
    if backup_check=="1":
        logger.logger.info("开始记录备份信息...")
        dir_list=[]
        for i in backup_dir.split(","):
            dir_list.append(i.strip())

        regular_list=[]
        for i in backup_regular.split(","):
            regular_list.append(i.strip())

        cron_time_list=[]
        for i in backup_cron_time.split(","):
            cron_time_list.append(i.strip())

        for i in range(len(dir_list)):
            directory=dir_list[i]
            regular=regular_list[i]
            cron_time=cron_time_list[i].split(":")
            hour=cron_time[0].strip()
            minute=cron_time[1].strip()
            scheduler.add_job(backup.record, 'cron', args=[logger, directory, regular], day_of_week='0-6', hour=int(hour), minute=int(minute), id=f'backup{i}')

    # 记录mysql
    mysql_check, mysql_interval, mysql_user, mysql_ip, mysql_port, mysql_password=conf.get("mysql", 
            "check", 
            "mysql_interval", 
            "mysql_user", 
            "mysql_ip", 
            "mysql_port", 
            "mysql_password"
            )
    if mysql_check=="1":
        logger.logger.info("开始采集MySQL资源信息...")
        scheduler.add_job(mysql.record, 'interval', args=[logger, mysql_user, mysql_ip, mysql_password, mysql_port], next_run_time=datetime.datetime.now(), minutes=int(mysql_interval), id='mysql')





    scheduler.start()
    
if __name__ == "__main__":
    main()
