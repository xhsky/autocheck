#!/usr/bin/env python
# *-* coding:utf8 *-*
# sky

from apscheduler.schedulers.blocking import BlockingScheduler
from lib import log, conf, mail, database
from lib.tools import format_size, printf
import datetime, os
import prettytable as pt
from apps import oracle

def resource_show(hostname, check_dict, granularity_level, sender_alias, receive, subject):
    log_file, log_level=log.get_log_args()
    logger=log.Logger(log_file, log_level)
    db=database.db()
    now_time=datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    modifier="-24 hour"
    #modifier="-10 minute"

    # 重置统计文件
    os.makedirs("./report",  exist_ok=True)
    printf("清空文件", 1)

    logger.logger.info("统计资源记录信息...")

    printf(f"记录统计开始时间: {now_time}")
    printf(f"主机名: {hostname}")
    printf("-"*100)
    
    # 系统启动时间
    sql="select boot_time from boot_time"
    boot_time=db.query_one(sql)[0]
    printf(f"系统启动时间: {boot_time}")
    printf("*"*100)

    # 磁盘
    logger.logger.info("统计Disk记录信息...")
    printf("磁盘统计:")
    sql="select distinct mounted from disk"
    disk_names=db.query_all(sql)
    for i in disk_names:
        i=i[0]
        table=pt.PrettyTable(["记录时间", "挂载点", "磁盘名称", "磁盘大小", "已使用大小", "已使用百分比", "可用"])
        sql=f"select record_time, name, total, used, used_percent, avail from disk "\
                f"where mounted=? "\
                f"and record_time > datetime('{now_time}', '{modifier}') "\
                f"and strftime('%M', record_time)%{granularity_level}=0 "\
                f"order by record_time"
        disk_data=db.query_all(sql, (i, ))
        for j in disk_data:
            total=format_size(j[2])
            used=format_size(j[3])
            used_percent=f"{j[4]}%"
            avail=format_size(j[5])
            table.add_row((j[0], i, j[1], total, used, used_percent, avail))
        printf(f"{i}磁盘统计:")
        printf(table)
        printf("*"*100)

    # CPU
    logger.logger.info("统计CPU记录信息...")
    printf("CPU统计:")
    table=pt.PrettyTable(["记录时间", "CPU核心数", "CPU使用率"])
    sql=f"select record_time, cpu_count, cpu_used_percent from cpu "\
            f"where record_time > datetime('{now_time}', '{modifier}') "\
            f"and strftime('%M', record_time)%{granularity_level}=0 "\
            f"order by record_time"
    cpu_data=db.query_all(sql)
    for i in cpu_data:
        used_percent=f"{i[2]}%"
        table.add_row((i[0], i[1], used_percent))
    printf(table)
    printf("*"*100)

    # MEM
    logger.logger.info("统计Mem记录信息...")
    printf("内存统计:")
    table=pt.PrettyTable(["记录时间", "内存大小", "可用(avail)", "已使用", "已使用百分比", "剩余(free)"])
    sql=f"select record_time, total, avail, used, used_percent, free from memory "\
            f"where record_time > datetime('{now_time}', '{modifier}') "\
            f"and strftime('%M', record_time)%{granularity_level}=0 "\
            f"order by record_time"
    mem_data=db.query_all(sql)
    for i in mem_data:
        total=format_size(i[1])
        avail=format_size(i[2])
        used=format_size(i[3])
        used_percent=f"{i[4]}%"
        free=format_size(i[5])
        table.add_row((i[0], total, avail, used, used_percent, free))
    printf(table)
    printf("*"*100)

    # Swap
    logger.logger.info("统计Swap记录信息...")
    printf("Swap统计:")
    table=pt.PrettyTable(["记录时间", "Swap大小", "已使用", "已使用百分比", "剩余"])
    sql=f"select record_time, total, used, used_percent, free from swap "\
            f"where record_time > datetime('{now_time}', '{modifier}') "\
            f"and strftime('%M', record_time)%{granularity_level}=0 "\
            f"order by record_time"
    swap_data=db.query_all(sql)
    for i in swap_data:
        total=format_size(i[1])
        used=format_size(i[2])
        used_percent=f"{i[3]}%"
        free=format_size(i[4])
        table.add_row((i[0], total, used, used_percent, free))
    printf(table)
    printf("*"*100)

    # Tomcat
    if check_dict["tomcat_check"]=="1":
        logger.logger.info("统计Tomcat记录信息...")
        printf("Tomcat统计:")
        version=db.query_one("select version from tomcat_java_version")[0]
        printf(f"Java版本: {version}")
        printf("*"*100)
        sql="select distinct port from tomcat_constant"
        tomcat_ports=db.query_all(sql)
        tomcat_constant_data=[]
        for i in tomcat_ports:
            port=i[0]
            constant_sql=f"select record_time, pid, port, boot_time, cmdline from tomcat_constant "\
                    f"where port=? "\
                    f"and '{now_time}' >= record_time "\
                    f"order by record_time desc"
            variable_sql=f"select record_time, pid, men_used, mem_used_percent, connections, threads_num from tomcat_variable "\
                    f"where port=? "\
                    f"and record_time > datetime('{now_time}', '{modifier}') "\
                    f"and strftime('%M', record_time)%{granularity_level}=0 "\
                    f"order by record_time"
            if version=="8":
                jvm_sql=f"select record_time, S0, S1, E, O, M, CCS, YGC, YGCT, FGC, FGCT, GCT from tomcat_jstat8 "\
                        f"where port=? "\
                        f"and record_time > datetime('{now_time}', '{modifier}') "\
                        f"and strftime('%M', record_time)%{granularity_level}=0 "\
                        f"order by record_time"
                jvm_table=pt.PrettyTable(["记录时间", "S0", "S1", "E", "O", "M", "CCS", "YGC", "YGCT", "FGC", "FGCT", "GCT"])
            elif version=="7":
                jvm_sql=f"select record_time, S0, S1, E, O, P, YGC, YGCT, FGC, FGCT, GCT from tomcat_jstat7 "\
                        f"where port=? "\
                        f"and record_time > datetime('{now_time}', '{modifier}') "\
                        f"and strftime('%M', record_time)%{granularity_level}=0 "\
                        f"order by record_time"
                jvm_table=pt.PrettyTable(["记录时间", "S0", "S1", "E", "O", "P", "YGC", "YGCT", "FGC", "FGCT", "GCT"])
            constant_table=pt.PrettyTable(["记录时间", "Pid", "端口", "启动时间", "启动参数"])
            tomcat_constant_data=(db.query_one(constant_sql, (port, )))
            constant_table.add_row(tomcat_constant_data)

            variable_table=pt.PrettyTable(["记录时间", "Pid", "内存使用", "内存使用率", "连接数", "线程数"])
            tomcat_variable_data=(db.query_all(variable_sql, (port, )))
            for i in tomcat_variable_data:
                mem_used=format_size(i[2])
                mem_used_percent=f"{i[3]:.2f}%"
                variable_table.add_row((i[0], i[1], mem_used, mem_used_percent, i[4], i[5]))

            tomcat_jvm_data=(db.query_all(jvm_sql, (port, )))
            for i in tomcat_jvm_data:
                jvm_table.add_row(i)

            printf(f"Tomcat({port})统计信息:")
            printf("启动信息:")
            printf(constant_table)
            printf("运行信息:")
            printf(variable_table)
            printf("Jvm内存信息:")
            printf(jvm_table)
            printf("*"*100)


    # Redis
    if check_dict["redis_check"]=="1":
        logger.logger.info("统计Redis记录信息...")
        printf("Redis统计:")
        printf("*"*100)

        constant_sql=f"select record_time, pid, port, boot_time from redis_constant "\
                f"where '{now_time}' >= record_time "\
                f"order by record_time desc"
        variable_sql=f"select record_time, pid, mem_used, mem_used_percent, connections, threads_num from redis_variable "\
                f"where record_time > datetime('{now_time}', '{modifier}') "\
                f"and strftime('%M', record_time)%{granularity_level}=0 "\
                f"order by record_time"

        # 启动信息
        constant_table=pt.PrettyTable(["记录时间", "Pid", "端口", "启动时间"])
        constant_data=(db.query_one(constant_sql))
        constant_table.add_row(constant_data)

        # 运行信息
        variable_table=pt.PrettyTable(["记录时间", "Pid", "内存使用", "内存使用率", "连接数", "线程数"])
        variable_data=(db.query_all(variable_sql))
        for i in variable_data:
            mem_used=format_size(i[2])
            mem_used_percent=f"{i[3]:.2f}%"
            variable_table.add_row((i[0], i[1], mem_used, mem_used_percent, i[4], i[5]))

        # master_slave信息
        role=db.query_one("select role from redis_role")[0]
        if role=="master":
            master_slave_sql="select a.record_time, connected_slave, slave_ip, slave_port, slave_state from redis_master a ,redis_slaves_info b on a.record_time=b.record_time where a.record_time=(select max(record_time) from redis_master)"
            master_slave_table=pt.PrettyTable(["记录时间", "Slave数量", "Slave IP", "Slave端口", "Slave状态"])
            master_slave_data=(db.query_all(master_slave_sql))
            for i in master_slave_data:
                master_slave_table.add_row(i)
        elif role=="slave":
            master_slave_sql="select record_time, pid, master_host, master_port, master_link_status from redis_slave order by record_time desc"
            master_slave_table=pt.PrettyTable(["记录时间", "Pid", "master主机", "master端口", "与master连接状态"])
            master_slave_data=(db.query_one(master_slave_sql))
            master_slave_table.add_row(master_slave_data)

        # sentinel监控信息
        sentinel_sql="select a.record_time, role, host, a.port from redis_sentinel a, redis_constant b on a.record_time=b.record_time where b.record_time=(select max(record_time) from redis_constant)"
        sentinel_table=pt.PrettyTable(["记录时间", "角色", "IP", "端口"])
        sentinel_data=(db.query_all(sentinel_sql))
        for i in sentinel_data:
            sentinel_table.add_row(i)

        printf("启动信息:")
        printf(constant_table)
        printf("运行信息:")
        printf(variable_table)
        printf("集群信息:")
        printf(f"当前角色: {role}")
        printf(master_slave_table)
        printf("Sentinel监控信息:")
        printf(sentinel_table)
        printf("*"*100)

    # MySQL
    if check_dict["mysql_check"]=="1":
        logger.logger.info("统计MySQL记录信息...")
        printf("MySQL统计:")
        printf("*"*100)

        constant_sql=f"select record_time, pid, port, boot_time from mysql_constant "\
                f"where '{now_time}' >= record_time "\
                f"order by record_time desc"
        variable_sql=f"select record_time, pid, mem_used, mem_used_percent, connections, threads_num from mysql_variable "\
                f"where record_time > datetime('{now_time}', '{modifier}') "\
                f"and strftime('%M', record_time)%{granularity_level}=0 "\
                f"order by record_time"

        # 启动信息
        constant_table=pt.PrettyTable(["记录时间", "Pid", "端口", "启动时间"])
        constant_data=(db.query_one(constant_sql))
        constant_table.add_row(constant_data)

        # 运行信息
        variable_table=pt.PrettyTable(["记录时间", "Pid", "内存使用", "内存使用率", "连接数", "线程数"])
        variable_data=(db.query_all(variable_sql))
        for i in variable_data:
            mem_used=format_size(i[2])
            mem_used_percent=f"{i[3]:.2f}%"
            variable_table.add_row((i[0], i[1], mem_used, mem_used_percent, i[4], i[5]))

        # master_slave信息
        role=db.query_one("select role from mysql_role")[0]
        if role=="master":
            master_slave_sql="select record_time, pid, slave_num, binlog_do_db, binlog_ignore_db from mysql_master order by record_time desc"
            master_slave_table=pt.PrettyTable(["记录时间", "Pid", "Slave数量", "Binlog_do_db", "Binlog_ignore_db"])
        elif role=="slave":
            master_slave_sql="select record_time, pid, master_host, master_port, replicate_do_db, replicate_ignore_db, "\
                    "slave_io_thread, slave_io_state, slave_sql_thread, slave_sql_state, "\
                    "master_uuid, retrieved_gtid_set, executed_gtid_set, seconds_behind_master "\
                    "from mysql_slave order by record_time desc"
            master_slave_table=pt.PrettyTable(["记录时间", "Pid", "Master主机", "Master端口", "同步数据库", "非同步数据库", "Slave_IO线程", "Slave_IO状态", "Slave_SQL线程", "Slave_SQL状态", "Master_UUID", "已接收的GTID集合", "已执行的GTID集合", "Slave落后Master的秒数"])
        master_slave_data=(db.query_one(master_slave_sql))
        if master_slave_data is not None:
            master_slave_table.add_row(master_slave_data)

        printf("启动信息:")
        printf(constant_table)
        printf("运行信息:")
        printf(variable_table)
        printf("集群信息:")
        printf(f"当前角色: {role}")
        printf(master_slave_table)
        printf("*"*100)
    
    # Oracle表空间
    if check_dict["oracle_check"]=="1":
        logger.logger.info("统计Oracle表空间记录信息...")
        printf("Oracle表空间统计:")
        sql="select distinct tablespace_name from oracle"
        tablespace_names=db.query_all(sql)
        for i in tablespace_names:
            i=i[0]
            table=pt.PrettyTable(["记录时间", "表空间名称", "表空间大小", "已使用", "已使用百分比", "可用"])
            sql=f"select record_time, size, used, used_percent, free from oracle "\
                    f"where tablespace_name=? "\
                    f"and record_time > datetime('{now_time}', '{modifier}') "\
                    f"and strftime('%M', record_time)%{granularity_level}=0 "\
                    f"order by record_time"
            tablespace_data=db.query_all(sql, (i, ))
            for j in tablespace_data:
                total=format_size(j[1])
                used=format_size(j[2])
                used_percent=f"{j[3]}%"
                free=format_size(j[4])
                table.add_row((j[0], i, total, used, used_percent, free))
            printf(f"{i}表空间统计:")
            printf(table)
            printf("*"*100)
        # war
        logger.logger.info("生成awr报告...")
        printf("awr报告信息:")
        awr_hours=conf.get("oracle", "awr_hours")[0]
        if oracle.generate_awr(int(awr_hours))==0:
            printf("请在附件中查看awr.html文件")
        else:
            printf("生成awr报告失败, 请自行手动生成")


    logger.logger.info("统计资源结束...")
    printf("-"*100)
    end_time=datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    printf(f"记录统计结束时间: {end_time}")

def show():
    check, send_time, granularity_level=conf.get("send", 
            "check", 
            "send_time", 
            "granularity_level"
            )
    if check=="1":
        hostname=conf.get("autocheck", "hostname")[0]
        sender_alias, receive, subject=conf.get("mail", 
                "sender", 
                "receive", 
                "subject"
                )
        hour, minute=send_time.split(":")

        check_dict={
                "tomcat_check": conf.get("tomcat", "check")[0], 
                "redis_check": conf.get("redis", "check")[0], 
                "mysql_check": conf.get("mysql", "check")[0], 
                "oracle_check": conf.get("oracle", "check")[0],
                "backup_check": conf.get("backup", "check")[0]
                }

        scheduler=BlockingScheduler()
        #scheduler.add_job(resource_show, 'cron', args=[granularity_level, sender_alias, receive, subject], day_of_week='0-6', hour=int(hour), minute=int(minute), id='resource_show')
        scheduler.add_job(resource_show, 'date', args=[hostname, check_dict, int(granularity_level), sender_alias, receive, subject], run_date=(datetime.datetime.now()+datetime.timedelta(seconds=3)).strftime("%Y-%m-%d %H:%M:%S"), id='resource_show')
        '''
        scheduler.add_job(host.disk_analysis, 'interval', args=[log_file, log_level, warning_percent, warning_interval, sender_alias, receive, subject], seconds=30, id='disk_ana')
        scheduler.add_job(host.cpu_analysis, 'interval', args=[logger, warning_percent, warning_interval, sender_alias, receive, subject], seconds=30, id='cpu_ana')
        scheduler.add_job(host.memory_analysis, 'interval', args=[logger, warning_percent, warning_interval, sender_alias, receive, subject], seconds=30, id='mem_ana')
        # tomcat资源
        tomcat_check=conf.get("tomcat", "check")[0]
        if tomcat_check=='1':
            logger.logger.info("开始分析Tomcat资源信息...")
            scheduler.add_job(tomcat.running_analysis, 'interval', args=[log_file, log_level, warning_interval, sender_alias, receive, subject], seconds=31, id='tomcat_run_ana')
            scheduler.add_job(tomcat.jvm_analysis, 'interval', args=[log_file, log_level, warning_interval, sender_alias, receive, subject], seconds=31, id='tomcat_jvm_ana')

        # redis资源
        redis_check=conf.get("redis", "check")[0]
        if redis_check=="1":
            logger.logger.info("开始分析Redis资源信息...")
            scheduler.add_job(redis.analysis, 'interval', args=[log_file, log_level, warning_interval, sender_alias, receive, subject], seconds=31, id='redis_ana')

        # 记录mysql
        mysql_check, seconds_behind_master=conf.get("mysql", "check", "seconds_behind_master")
        if mysql_check=="1":
            logger.logger.info("开始分析MySQL资源信息...")
            scheduler.add_job(mysql.running_analysis, 'interval', args=[log_file, log_level, warning_interval, sender_alias, receive, subject], seconds=31, id='mysql_run_ana')
            scheduler.add_job(mysql.master_slave_analysis, 'interval', args=[log_file, log_level, int(seconds_behind_master), warning_interval, sender_alias, receive, subject], seconds=31, id='mysql_slave_ana')

        # 记录Oracle
        oracle_check=conf.get("oracle", "check")[0]
        if oracle_check=="1":
            logger.logger.info("开始分析Oracle信息...")
            scheduler.add_job(oracle.tablespace_analysis, 'interval', args=[log_file, log_level, warning_percent, warning_interval, sender_alias, receive, subject], seconds=31, id='oracle_tablespace_ana')
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



        '''
        scheduler.start()
    
if __name__ == "__main__":
    main()
