#!/usr/bin/env python
# *-* coding:utf8 *-*
# sky

from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.executors.pool import ThreadPoolExecutor
from lib import log, conf, database
from apps import host, tomcat, redis, backup, mysql, oracle, user_resource, matching
import datetime, os

def record():
    log_file, log_level=log.get_log_args()
    logger=log.Logger(log_file, log_level)
    logger.logger.info("开始采集资源信息...")

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

    min_value=10

    # host资源记录
    logger.logger.info("开始采集主机资源信息...")
    disk_interval, cpu_interval, memory_interval, swap_interval, users_limit=conf.get("host", 
            "disk_interval",
            "cpu_interval",
            "memory_interval",
            "swap_interval", 
            "users_limit"
            )
    if int(disk_interval) < min_value:
        disk_interval=min_value
    if int(cpu_interval) < min_value:
        cpu_interval=min_value
    if int(memory_interval) < min_value:
        memory_interval=min_value
    if int(swap_interval) < min_value:
        swap_interval=min_value

    logger.logger.info("开始采集磁盘资源信息...")
    scheduler.add_job(host.disk_record, 'interval', args=[log_file, log_level], seconds=int(disk_interval), id='disk_record')
    logger.logger.info("开始采集CPU资源信息...")
    scheduler.add_job(host.cpu_record, 'interval', args=[log_file, log_level], seconds=int(cpu_interval), id='cpu_record')
    logger.logger.info("开始采集内存资源信息...")
    scheduler.add_job(host.memory_record, 'interval', args=[log_file, log_level], seconds=int(memory_interval), id='memory_record')
    logger.logger.info("开始采集Swap资源信息...")
    scheduler.add_job(host.swap_record, 'interval', args=[log_file, log_level], seconds=int(swap_interval), id='swap_record')
    logger.logger.info("开始采集启动时间资源信息...")
    #scheduler.add_job(host.boot_time_record, 'interval', args=[log_file, log_level], seconds=int(boot_time_interval), id='boot_time_record')
    host.boot_time_record(log_file, log_level)

    # 用户资源限制
    logger.logger.info("开始记录用户限制信息...")
    if users_limit is not None:
        users_limit_list=[]
        for i in users_limit.split(","):
            users_limit_list.append(i.strip())

        for user in users_limit_list:
            scheduler.add_job(user_resource.record, 'interval', args=[log_file, log_level, user], next_run_time=datetime.datetime.now()+datetime.timedelta(seconds=5), minutes=60, id=f'{user}_limit')

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
        if int(tomcat_interval) < min_value:
            tomcat_interval=min_value
        scheduler.add_job(tomcat.record, 'interval', args=[log_file, log_level, tomcat_port_list], seconds=int(tomcat_interval), id='tomcat_record')

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
        if int(redis_interval) < min_value:
            redis_interval=min_value
        logger.logger.info("开始采集Redis资源信息...")
        scheduler.add_job(redis.record, 'interval', args=[log_file, log_level, redis_password, redis_port, sentinel_port, sentinel_name, commands], \
                seconds=int(redis_interval), id='redis_record')

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
            scheduler.add_job(backup.record, 'cron', args=[log_file, log_level, directory, regular], next_run_time=datetime.datetime.now(), day_of_week='0-6', hour=int(hour), minute=int(minute), id=f'backup{i}')

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
        if int(mysql_interval) < min_value:
            mysql_interval = min_value
        logger.logger.info("开始采集MySQL资源信息...")
        scheduler.add_job(mysql.record, 'interval', args=[log_file, log_level, mysql_user, mysql_ip, mysql_password, mysql_port], seconds=int(mysql_interval), id='mysql_record')

    # 记录Oracle
    oracle_check, oracle_interval=conf.get("oracle", 
            "check", 
            "oracle_interval"
            )
    if oracle_check=="1":
        if int(oracle_interval) < min_value:
            oracle_interval = min_value
        logger.logger.info("开始记录Oracle信息...")
        scheduler.add_job(oracle.record, 'interval', args=[log_file, log_level], seconds=int(oracle_interval), id='oracle_record')

    # 记录并分析匹配
    matching_check, matching_files, matching_keys, matching_interal=conf.get("matching",
            "check", 
            "matching_files", 
            "matching_keys", 
            "matching_interval"
            )
    if matching_check=="1":
        matching_min_value=1
        if int(matching_interal) < matching_min_value:
            matching_check = matching_min_value
        logger.logger.info("开始采集匹配信息...")

        matching_dict=dict(zip([x.strip() for x in matching_files.split(",")], [x.strip() for x in matching_keys.split(",")]))
        record_time=datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        db=database.db()
        for matching_file in matching_dict:
            if os.path.exists(matching_file):
                sql="insert into matching values(?, ?, ?, ?, ?)"
                filesize=os.stat(matching_file)[6]
                db.update_one(sql, (record_time, matching_file, matching_dict[matching_file], "all", filesize))
            else:
                logger.logger.error(f"Error: [matching]配置中文件{matching_file}不存在")
                matching_dict.pop(matching_file)
        scheduler.add_job(matching.matching_records, 'interval', args=[log_file, log_level, matching_dict], seconds=int(matching_interal), id=f'matching')

    scheduler.start()
    
if __name__ == "__main__":
    main()
