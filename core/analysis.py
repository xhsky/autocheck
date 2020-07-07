#!/usr/bin/env python
# *-* coding:utf8 *-*
# sky

from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.executors.pool import ThreadPoolExecutor
from lib import log, conf
from apps import host, tomcat, redis, backup, mysql, oracle, user_resource, matching
import datetime

def analysis():
    log_file, log_level=log.get_log_args()
    logger=log.Logger(log_file, log_level)
    logger.logger.info("开始分析资源信息...")

    mail_check, sender_alias, mail_receive, mail_subject, sms_check, sms_receive, sms_subject=conf.get("notify", 
            "mail", 
            "mail_sender", 
            "mail_receive", 
            "mail_subject", 
            "sms", 
            "sms_receive", 
            "sms_subject"
            )
    notify_dict={
            "mail":{
                "check": mail_check, 
                "sender_alias": sender_alias, 
                "receive": mail_receive, 
                "subject": mail_subject
                }, 
            "sms":{
                "check": sms_check, 
                "receive": sms_receive, 
                "subject": sms_subject
                }
            }

    warning_percent, warning_interval, analysis_interval=conf.get("autocheck",
        "warning_percent", 
        "warning_interval", 
        "analysis_interval"
        )

    disk_interval, cpu_interval, memory_interval=conf.get("host", 
            "disk_interval", 
            "cpu_interval", 
            "memory_interval"
            )

    min_value=5
    warning_percent=float(warning_percent)
    warning_interval=int(warning_interval)
    analysis_interval=int(analysis_interval)
    disk_interval=int(disk_interval)+analysis_interval
    cpu_interval=int(cpu_interval)+analysis_interval
    memory_interval=int(memory_interval)+analysis_interval

    max_threads=50
    executors = {
            "default": ThreadPoolExecutor(max_threads)
            }
    job_defaults = {
            "coalesce": True, 
            "max_instances": 1,  
            "misfire_grace_time": 3, 
            }
    scheduler=BlockingScheduler(job_defaults=job_defaults, executors=executors) 
    # host资源记录
    logger.logger.info("开始分析主机资源信息...")
    scheduler.add_job(host.disk_analysis, 'interval', args=[log_file, log_level, warning_percent, warning_interval, notify_dict], seconds=disk_interval, id='disk_ana')
    scheduler.add_job(host.cpu_analysis, 'interval', args=[log_file, log_level, warning_percent, warning_interval, notify_dict], seconds=cpu_interval, id='cpu_ana')
    scheduler.add_job(host.memory_analysis, 'interval', args=[log_file, log_level, warning_percent, warning_interval, notify_dict], seconds=memory_interval, id='mem_ana')

    # users_limit
    #logger.logger.info("开始分析用户资源信息...")
    #scheduler.add_job(user_resource.analysis, 'interval', args=[log_file, log_level, 0, notify_dict], next_run_time=datetime.datetime.now()+datetime.timedelta(seconds=15),  minutes=65, id=f'user_limit_ana')

    # tomcat资源
    tomcat_check=conf.get("tomcat", "check")[0]
    if tomcat_check=='1':
        tomcat_interval=conf.get("tomcat", "tomcat_interval")[0]
        tomcat_interval=int(tomcat_interval)+analysis_interval
        logger.logger.info("开始分析Tomcat资源信息...")
        scheduler.add_job(tomcat.running_analysis, 'interval', args=[log_file, log_level, warning_interval, notify_dict], seconds=tomcat_interval, id='tomcat_run_ana')
        scheduler.add_job(tomcat.jvm_analysis, 'interval', args=[log_file, log_level, warning_interval, notify_dict], seconds=tomcat_interval, id='tomcat_jvm_ana')

    # redis资源
    redis_check=conf.get("redis", "check")[0]
    if redis_check=="1":
        redis_interval=conf.get("redis", "redis_interval")[0]
        redis_interval=int(redis_interval)+analysis_interval
        logger.logger.info("开始分析Redis资源信息...")
        scheduler.add_job(redis.running_analysis, 'interval', args=[log_file, log_level, warning_interval, notify_dict], seconds=redis_interval, id='redis_run_ana')
        scheduler.add_job(redis.master_slave_analysis, 'interval', args=[log_file, log_level, warning_interval, notify_dict], seconds=redis_interval, id='redis_slave_ana')

    # 记录mysql
    mysql_check=conf.get("mysql", "check")[0]
    if mysql_check=="1":
        mysql_interval, seconds_behind_master=conf.get("mysql", "mysql_interval", "seconds_behind_master")
        mysql_interval=int(mysql_interval)+analysis_interval
        logger.logger.info("开始分析MySQL资源信息...")
        scheduler.add_job(mysql.running_analysis, 'interval', args=[log_file, log_level, warning_interval, notify_dict], seconds=mysql_interval, id='mysql_run_ana')
        scheduler.add_job(mysql.master_slave_analysis, 'interval', args=[log_file, log_level, int(seconds_behind_master), warning_interval, notify_dict], seconds=mysql_interval, id='mysql_slave_ana')

    # 记录Oracle
    oracle_check=conf.get("oracle", "check")[0]
    if oracle_check=="1":
        oracle_interval=conf.get("oracle", "oracle_interval")[0]
        oracle_interval=int(oracle_interval)+analysis_interval
        logger.logger.info("开始分析Oracle信息...")
        scheduler.add_job(oracle.tablespace_analysis, 'interval', args=[log_file, log_level, warning_percent, warning_interval, notify_dict], seconds=oracle_interval, id='oracle_tablespace_ana')

    # backup
    backup_check, backup_dir, backup_cron_time=conf.get("backup",
            "check", 
            "dir", 
            "cron_time"
            )
    if backup_check=="1":
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
            scheduler.add_job(backup.analysis, 'cron', args=[log_file, log_level, directory, 0, notify_dict], day_of_week='0-6', hour=int(hour), minute=int(minute)+1, id=f'backup{i}_ana')

    #matching
    matching_check=conf.get("matching", "check")[0]
    if matching_check=="1":
        matching_files, matching_keys=conf.get("matching", "matching_files", "matching_keys")
        matching_dict=dict(zip([x.strip() for x in matching_files.split(", ")],  [x.strip() for x in matching_keys.split(", ")]))

        matching_interval=conf.get("matching", "matching_interval")[0]
        matching_interval=int(matching_interval)+analysis_interval
        logger.logger.info("开始分析Matching信息...")
        scheduler.add_job(matching.matching_analysis, 'interval', args=[log_file, log_level, warning_interval, matching_dict, notify_dict], seconds=matching_interval, id='matching_ana')

    scheduler.start()
    
if __name__ == "__main__":
    main()
