#!/usr/bin/env python
# *-* coding:utf8 *-*
# sky

from apscheduler.schedulers.blocking import BlockingScheduler
from lib import log, conf
from apps import host, tomcat, redis, backup, mysql, oracle
import datetime, time

def analysis():
    log_file, log_level=log.get_log_args()
    logger=log.Logger(log_file, log_level)
    logger.logger.info("开始分析资源信息...")

    sender_alias, receive, subject=conf.get("mail", 
            "sender", 
            "receive", 
            "subject"
            )

    warning_percent, warning_interval=conf.get("autocheck",
        "warning_percent", 
        "warning_interval"
        )
    warning_percent=float(warning_percent)
    warning_interval=int(warning_interval)

    scheduler=BlockingScheduler()
    # host资源记录
    logger.logger.info("开始分析主机资源信息...")
    scheduler.add_job(host.disk_analysis, 'interval', args=[logger, warning_percent, warning_interval, sender_alias, receive, subject], seconds=30, id='disk_ana')
    scheduler.add_job(host.cpu_analysis, 'interval', args=[logger, warning_percent, warning_interval, sender_alias, receive, subject], seconds=30, id='cpu_ana')
    scheduler.add_job(host.memory_analysis, 'interval', args=[logger, warning_percent, warning_interval, sender_alias, receive, subject], seconds=30, id='mem_ana')

    # tomcat资源
    tomcat_check=conf.get("tomcat", "check")[0]
    if tomcat_check=='1':
        logger.logger.info("开始分析Tomcat资源信息...")
        scheduler.add_job(tomcat.analysis, 'interval', args=[logger, warning_percent, warning_interval, sender_alias, receive, subject], seconds=30, id='tomcat_ana')

    '''
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

    # 记录Oracle
    oracle_check, oracle_interval=conf.get("oracle", 
            "check", 
            "oracle_interval"
            )
    if oracle_check=="1":
        logger.logger.info("开始记录Oracle信息...")
        scheduler.add_job(oracle.record, 'interval', args=[logger], next_run_time=datetime.datetime.now(), minutes=int(oracle_interval), id='oracle')

    '''
    scheduler.start()
    
if __name__ == "__main__":
    main()
