#!/usr/bin/env python
# *-* coding:utf8 *-*
# sky

from apscheduler.schedulers.blocking import BlockingScheduler
from lib import log, conf
from apps import host, tomcat, redis, backup, mysql, oracle

def analysis():
    log_file, log_level=log.get_log_args()
    logger=log.Logger(log_file, log_level)
    logger.logger.info("开始分析资源信息...")

    sender_alias, receive, subject=conf.get("mail", 
            "sender", 
            "receive", 
            "subject"
            )

    warning_percent, warning_interval, analysis_interval=conf.get("autocheck",
        "warning_percent", 
        "warning_interval", 
        "analysis_interval"
        )
    min_value=5
    warning_percent=float(warning_percent)
    warning_interval=int(warning_interval)
    analysis_interval=int(analysis_interval)
    if analysis_interval < min_value:
        analysis_interval=min_value

    scheduler=BlockingScheduler()
    # host资源记录
    logger.logger.info("开始分析主机资源信息...")
    scheduler.add_job(host.disk_analysis, 'interval', args=[log_file, log_level, warning_percent, warning_interval, sender_alias, receive, subject], seconds=analysis_interval, id='disk_ana')
    scheduler.add_job(host.cpu_analysis, 'interval', args=[log_file, log_level, warning_percent, warning_interval, sender_alias, receive, subject], seconds=analysis_interval, id='cpu_ana')
    scheduler.add_job(host.memory_analysis, 'interval', args=[log_file, log_level, warning_percent, warning_interval, sender_alias, receive, subject], seconds=analysis_interval, id='mem_ana')
    # tomcat资源
    tomcat_check=conf.get("tomcat", "check")[0]
    if tomcat_check=='1':
        logger.logger.info("开始分析Tomcat资源信息...")
        scheduler.add_job(tomcat.running_analysis, 'interval', args=[log_file, log_level, warning_interval, sender_alias, receive, subject], seconds=analysis_interval, id='tomcat_run_ana')
        scheduler.add_job(tomcat.jvm_analysis, 'interval', args=[log_file, log_level, warning_interval, sender_alias, receive, subject], seconds=analysis_interval, id='tomcat_jvm_ana')

    # redis资源
    redis_check=conf.get("redis", "check")[0]
    if redis_check=="1":
        logger.logger.info("开始分析Redis资源信息...")
        scheduler.add_job(redis.running_analysis, 'interval', args=[log_file, log_level, warning_interval, sender_alias, receive, subject], seconds=analysis_interval, id='redis_run_ana')
        scheduler.add_job(redis.master_slave_analysis, 'interval', args=[log_file, log_level, warning_interval, sender_alias, receive, subject], seconds=analysis_interval, id='redis_slave_ana')

    # 记录mysql
    mysql_check, seconds_behind_master=conf.get("mysql", "check", "seconds_behind_master")
    if mysql_check=="1":
        logger.logger.info("开始分析MySQL资源信息...")
        scheduler.add_job(mysql.running_analysis, 'interval', args=[log_file, log_level, warning_interval, sender_alias, receive, subject], seconds=analysis_interval, id='mysql_run_ana')
        scheduler.add_job(mysql.master_slave_analysis, 'interval', args=[log_file, log_level, int(seconds_behind_master), warning_interval, sender_alias, receive, subject], seconds=analysis_interval, id='mysql_slave_ana')

    # 记录Oracle
    oracle_check=conf.get("oracle", "check")[0]
    if oracle_check=="1":
        logger.logger.info("开始分析Oracle信息...")
        scheduler.add_job(oracle.tablespace_analysis, 'interval', args=[log_file, log_level, warning_percent, warning_interval, sender_alias, receive, subject], seconds=analysis_interval, id='oracle_tablespace_ana')

    # backup
    backup_check, backup_dir, backup_cron_time=conf.get("backup",
            "check", 
            "dir", 
            "cron_time"
            )
    if backup_check=="1":
        logger.logger.info("开始记录备份信息...")
        dir_list=[]
        for i in backup_dir.split(","):
            dir_list.append(i.strip())

        cron_time_list=[]
        for i in backup_cron_time.split(","):
            cron_time_list.append(i.strip())

        for i in range(len(dir_list)):
            directory=dir_list[i]
            cron_time=cron_time_list[i].split(":")
            hour=cron_time[0].strip()
            minute=cron_time[1].strip()
            scheduler.add_job(backup.analysis, 'cron', args=[log_file, log_level, directory, warning_interval, sender_alias, receive, subject], day_of_week='0-6', hour=int(hour), minute=int(minute)+1, id=f'backup{i}_ana')

    scheduler.start()
    
if __name__ == "__main__":
    main()
