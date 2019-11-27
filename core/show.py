#!/usr/bin/env python
# *-* coding:utf8 *-*
# sky

from apscheduler.schedulers.blocking import BlockingScheduler
from lib import log, conf, mail, database
from lib.tools import format_size, printf
import datetime, os
import prettytable as pt
from apps import oracle, mysql
import tarfile, shutil

def tar_report(logger, report_dir):
    """巡检报告打包
    """
    report_files=os.listdir(".")
    for report_file in report_files:
        if report_file.startswith(report_dir) and report_file.endswith("tar.gz"):
            os.remove(report_file)
    report_file=f"{report_dir}-{datetime.datetime.now().strftime('%Y%m%d%H%M')}.tar.gz"
    with tarfile.open(report_file, "w:gz") as tar:
        for i in os.listdir(report_dir):
            filename=f"{report_dir}/{i}"
            if os.path.getsize(filename) > 0:
                tar.add(filename)
        error_file="logs/errors.log"
        if os.path.getsize(error_file) > 0:
            logger.logger.error(f"有错误日志产生: {error_file}")
            tar.add(error_file)
            with open(error_file, "w", encoding="utf8") as error_f:
                error_f.truncate()
        return report_file

def resource_show(hostname, check_dict, granularity_level, sender_alias, receive, subject):
    log_file, log_level=log.get_log_args()
    logger=log.Logger(log_file, log_level)
    db=database.db()
    now_time=datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    modifier="-24 hour"

    # 重置统计文件
    report_dir="report"
    shutil.rmtree(report_dir)
    os.makedirs(report_dir,  exist_ok=True)

    logger.logger.info("统计资源记录信息...")

    printf(f"统计开始时间: {now_time}")
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
    disk_granularity_level=int(60/int(check_dict['host_check'][0])*granularity_level)
    disk_granularity_level=disk_granularity_level if disk_granularity_level!=0 else 1
    for i in disk_names:
        i=i[0]
        table=pt.PrettyTable(["记录时间", "挂载点", "磁盘名称", "磁盘大小", "已使用大小", "已使用百分比", "可用"])
        sql=f"select record_time, name, total, used, used_percent, avail from disk "\
                f"where mounted=? "\
                f"and record_time > datetime('{now_time}', '{modifier}') "\
                f"order by record_time"
        disk_data=db.query_all(sql, (i, ))
        for index, item in enumerate(disk_data):
            if index%disk_granularity_level==0 or index==0:
                total=format_size(item[2])
                used=format_size(item[3])
                used_percent=f"{item[4]}%"
                avail=format_size(item[5])
                table.add_row((item[0], i, item[1], total, used, used_percent, avail))
        printf(f"{i}磁盘统计:")
        printf(table)
        printf("*"*100)

    # CPU
    logger.logger.info("统计CPU记录信息...")
    printf("CPU统计:")
    cpu_granularity_level=int(60/int(check_dict['host_check'][1])*granularity_level)
    cpu_granularity_level=cpu_granularity_level if cpu_granularity_level!=0 else 1
    table=pt.PrettyTable(["记录时间", "CPU核心数", "CPU使用率"])
    sql=f"select record_time, cpu_count, cpu_used_percent from cpu "\
            f"where record_time > datetime('{now_time}', '{modifier}') "\
            f"order by record_time"
    cpu_data=db.query_all(sql)
    for index, item in enumerate(cpu_data):
        if index%cpu_granularity_level==0 or index==0:
            used_percent=f"{item[2]}%"
            table.add_row((item[0], item[1], used_percent))
    printf(table)
    printf("*"*100)

    # MEM
    logger.logger.info("统计Mem记录信息...")
    printf("内存统计:")
    mem_granularity_level=int(60/int(check_dict['host_check'][2])*granularity_level)
    mem_granularity_level=mem_granularity_level if mem_granularity_level!=0 else 1
    table=pt.PrettyTable(["记录时间", "内存大小", "可用(avail)", "已使用", "已使用百分比", "剩余(free)"])
    sql=f"select record_time, total, avail, used, used_percent, free from memory "\
            f"where record_time > datetime('{now_time}', '{modifier}') "\
            f"order by record_time"
    mem_data=db.query_all(sql)
    for index, item in enumerate(mem_data):
        if index%mem_granularity_level==0 or index==0:
            total=format_size(item[1])
            avail=format_size(item[2])
            used=format_size(item[3])
            used_percent=f"{item[4]}%"
            free=format_size(item[5])
            table.add_row((item[0], total, avail, used, used_percent, free))
    printf(table)
    printf("*"*100)

    # Swap
    logger.logger.info("统计Swap记录信息...")
    printf("Swap统计:")
    swap_granularity_level=int(60/int(check_dict['host_check'][3])*granularity_level)
    swap_granularity_level=swap_granularity_level if swap_granularity_level!=0 else 1
    table=pt.PrettyTable(["记录时间", "Swap大小", "已使用", "已使用百分比", "剩余"])
    sql=f"select record_time, total, used, used_percent, free from swap "\
            f"where record_time > datetime('{now_time}', '{modifier}') "\
            f"order by record_time"
    swap_data=db.query_all(sql)
    for index, item in enumerate(swap_data):
        if index%swap_granularity_level==0 or index==0:
            total=format_size(item[1])
            used=format_size(item[2])
            used_percent=f"{item[3]}%"
            free=format_size(item[4])
            table.add_row((item[0], total, used, used_percent, free))
    printf(table)
    printf("*"*100)

    # Tomcat
    if check_dict["tomcat_check"][0]=="1":
        logger.logger.info("统计Tomcat记录信息...")
        printf("Tomcat统计:")
        tomcat_granularity_level=int(60/int(check_dict['tomcat_check'][1])*granularity_level)
        tomcat_granularity_level=tomcat_granularity_level if tomcat_granularity_level!=0 else 1
        version=db.query_one("select version from tomcat_java_version")[0]
        printf(f"Java版本: {version}")
        printf("*"*100)
        #sql="select distinct port from tomcat_constant"
        #tomcat_ports=db.query_all(sql)
        tomcat_ports=conf.get("tomcat", "tomcat_port")[0].split(",")
        tomcat_constant_data=[]
        for i in tomcat_ports:
            port=int(i.strip())
            constant_sql=f"select record_time, pid, port, boot_time, cmdline from tomcat_constant "\
                    f"where port=? "\
                    f"and '{now_time}' >= record_time "\
                    f"order by record_time desc"
            variable_sql=f"select record_time, pid, men_used, mem_used_percent, connections, threads_num from tomcat_variable "\
                    f"where port=? "\
                    f"and record_time > datetime('{now_time}', '{modifier}') "\
                    f"order by record_time"
            if version=="8":
                jvm_sql=f"select record_time, S0, S1, E, O, M, CCS, YGC, YGCT, FGC, FGCT, GCT from tomcat_jstat8 "\
                        f"where port=? "\
                        f"and record_time > datetime('{now_time}', '{modifier}') "\
                        f"order by record_time"
                jvm_table=pt.PrettyTable(["记录时间", "S0", "S1", "E", "O", "M", "CCS", "YGC", "YGCT", "FGC", "FGCT", "GCT"])
            elif version=="7":
                jvm_sql=f"select record_time, S0, S1, E, O, P, YGC, YGCT, FGC, FGCT, GCT from tomcat_jstat7 "\
                        f"where port=? "\
                        f"and record_time > datetime('{now_time}', '{modifier}') "\
                        f"order by record_time"
                jvm_table=pt.PrettyTable(["记录时间", "S0", "S1", "E", "O", "P", "YGC", "YGCT", "FGC", "FGCT", "GCT"])

            constant_table=pt.PrettyTable(["记录时间", "Pid", "端口", "启动时间", "启动参数"])
            tomcat_constant_data=(db.query_one(constant_sql, (port, )))
            constant_table.add_row(tomcat_constant_data)

            variable_table=pt.PrettyTable(["记录时间", "Pid", "内存使用", "内存使用率", "连接数", "线程数"])
            tomcat_variable_data=(db.query_all(variable_sql, (port, )))
            for index, item in enumerate(tomcat_variable_data):
                if index%tomcat_granularity_level==0 or index==0:
                    mem_used=format_size(item[2])
                    mem_used_percent=f"{item[3]:.2f}%"
                    variable_table.add_row((item[0], item[1], mem_used, mem_used_percent, item[4], item[5]))

            tomcat_jvm_data=(db.query_all(jvm_sql, (port, )))
            for index, item in enumerate(tomcat_jvm_data):
                if index%tomcat_granularity_level==0 or index==0:
                    jvm_table.add_row(item)

            printf(f"Tomcat({port})统计信息:")
            printf("启动信息:")
            printf(constant_table)
            printf("运行信息:")
            printf(variable_table)
            printf("Jvm内存信息:")
            printf(jvm_table)
            printf("*"*100)

    # Redis
    if check_dict["redis_check"][0]=="1":
        logger.logger.info("统计Redis记录信息...")
        printf("Redis统计:")
        redis_granularity_level=int(60/int(check_dict['redis_check'][1])*granularity_level)
        redis_granularity_level=redis_granularity_level if redis_granularity_level!=0 else 1
        printf("*"*100)

        constant_sql=f"select record_time, pid, port, boot_time from redis_constant "\
                f"where '{now_time}' >= record_time "\
                f"order by record_time desc"
        variable_sql=f"select record_time, pid, mem_used, mem_used_percent, connections, threads_num from redis_variable "\
                f"where record_time > datetime('{now_time}', '{modifier}') "\
                f"order by record_time"

        # 启动信息
        constant_table=pt.PrettyTable(["记录时间", "Pid", "端口", "启动时间"])
        constant_data=(db.query_one(constant_sql))
        constant_table.add_row(constant_data)

        # 运行信息
        variable_table=pt.PrettyTable(["记录时间", "Pid", "内存使用", "内存使用率", "连接数", "线程数"])
        variable_data=(db.query_all(variable_sql))
        for index, item in enumerate(variable_data):
            if index%tomcat_granularity_level==0 or index==0:
                mem_used=format_size(item[2])
                mem_used_percent=f"{item[3]:.2f}%"
                variable_table.add_row((item[0], item[1], mem_used, mem_used_percent, item[4], item[5]))

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

    # backup
    if check_dict["backup_check"]=="1":
        logger.logger.info("统计备份记录信息...")
        printf("备份统计:")
        backup_dirs=conf.get("backup", "dir")[0].split(",")
        for i in backup_dirs:
            directory=i.strip()
            table=pt.PrettyTable(["记录时间", "备份文件", "大小", "创建时间"])
            sql=f"select record_time, filename, size, ctime from backup "\
                    f"where directory=?"\
                    f"order by ctime"
            backup_data=db.query_all(sql, (directory, ))
            for j in backup_data:
                if j[2] is not None:
                    size=format_size(j[2])
                    table.add_row((j[0], j[1], size, j[3]))

            printf(f"备份({directory})统计信息:")
            printf(table)
            printf("*"*100)

    # MySQL
    if check_dict["mysql_check"][0]=="1":
        logger.logger.info("统计MySQL记录信息...")
        printf("MySQL统计:")
        mysql_granularity_level=int(60/int(check_dict['mysql_check'][1])*granularity_level)
        mysql_granularity_level=mysql_granularity_level if mysql_granularity_level!=0 else 1
        printf("*"*100)

        constant_sql=f"select record_time, pid, port, boot_time from mysql_constant "\
                f"where '{now_time}' >= record_time "\
                f"order by record_time desc"
        variable_sql=f"select record_time, pid, mem_used, mem_used_percent, connections, threads_num from mysql_variable "\
                f"where record_time > datetime('{now_time}', '{modifier}') "\
                f"order by record_time"

        # 启动信息
        constant_table=pt.PrettyTable(["记录时间", "Pid", "端口", "启动时间"])
        constant_data=(db.query_one(constant_sql))
        constant_table.add_row(constant_data)

        # 运行信息
        variable_table=pt.PrettyTable(["记录时间", "Pid", "内存使用", "内存使用率", "连接数", "线程数"])
        variable_data=(db.query_all(variable_sql))
        for index, item in enumerate(variable_data):
            if index%mysql_granularity_level==0 or index==0:
                mem_used=format_size(item[2])
                mem_used_percent=f"{item[3]:.2f}%"
                variable_table.add_row((item[0], item[1], mem_used, mem_used_percent, item[4], item[5]))

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

        # 慢日志
        printf("慢日志信息:")
        mysql_user, mysql_ip, mysql_port, mysql_password=conf.get("mysql", 
                "mysql_user",
                "mysql_ip",
                "mysql_port",
                "mysql_password"
                )
        mysql_flag, msg=mysql.export_slow_log(logger, mysql_user, mysql_ip, mysql_password, mysql_port, f"{report_dir}/slow_analysis.log", f"{report_dir}/slow.log")
        printf(msg)
        printf("*"*100)

    # Oracle表空间
    if check_dict["oracle_check"][0]=="1":
        logger.logger.info("统计Oracle表空间记录信息...")
        printf("Oracle表空间统计:")
        oracle_granularity_level=int(60/int(check_dict['oracle_check'][1])*granularity_level)
        oracle_granularity_level=oracle_granularity_level if oracle_granularity_level!=0 else 1

        sql="select distinct tablespace_name from oracle"
        tablespace_names=db.query_all(sql)
        for i in tablespace_names:
            i=i[0]
            table=pt.PrettyTable(["记录时间", "表空间名称", "表空间大小", "已使用", "已使用百分比", "可用"])
            sql=f"select record_time, size, used, used_percent, free from oracle "\
                    f"where tablespace_name=? "\
                    f"and record_time > datetime('{now_time}', '{modifier}') "\
                    f"order by record_time"
            tablespace_data=db.query_all(sql, (i, ))
            for index, item in enumerate(tablespace_data):
                if index%oracle_granularity_level==0 or index==0:
                    total=format_size(item[1])
                    used=format_size(item[2])
                    used_percent=f"{item[3]}%"
                    free=format_size(item[4])
                    table.add_row((item[0], i, total, used, used_percent, free))
            printf(f"{i}表空间统计:")
            printf(table)
            printf("*"*100)
        # war
        logger.logger.info("生成awr报告...")
        printf("awr报告信息:")
        awr_hours=conf.get("oracle", "awr_hours")[0]
        if oracle.generate_awr(int(awr_hours), report_dir)==0:
            printf("请在附件中查看awr.html文件")
        else:
            printf("生成awr报告失败, 请自行手动生成")

    logger.logger.info("统计资源结束...")
    printf("-"*100)
    end_time=datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    printf(f"统计结束时间: {end_time}")

    tar_file=tar_report(logger, report_dir)
    sender_alias, receive, subject=conf.get("mail",
            "sender",
            "receive",
            "subject"
            )
    warning_msg="\n请查看统计报告."
    if mysql_flag==1:
        warning_msg=f"{warning_msg}\n\n该附件存在MySQL慢日志"
    mail.send(logger, warning_msg, sender_alias, receive, subject, msg="report", attachment_file=tar_file)

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
                "host_check": conf.get("host", "disk_interval", "cpu_interval", "memory_interval", "swap_interval"), 
                "tomcat_check": conf.get("tomcat", "check", "tomcat_interval"), 
                "redis_check": conf.get("redis", "check", "redis_interval"), 
                "mysql_check": conf.get("mysql", "check", "mysql_interval"), 
                "oracle_check": conf.get("oracle", "check", "oracle_interval"),
                "backup_check": conf.get("backup", "check")[0]
                }

        scheduler=BlockingScheduler()
        #scheduler.add_job(resource_show, 'date', args=[hostname, check_dict, int(granularity_level), sender_alias, receive, subject], run_date=(datetime.datetime.now()+datetime.timedelta(seconds=3)).strftime("%Y-%m-%d %H:%M:%S"), id='resource_show')
        scheduler.add_job(resource_show, 'cron', args=[hostname, check_dict, int(granularity_level), sender_alias, receive, subject], day_of_week='0-6', hour=int(hour), minute=int(minute), id='resource_show')
        scheduler.start()
        
if __name__ == "__main__":
    main()
