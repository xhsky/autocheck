#!/usr/bin/env python
# *-* coding:utf8 *-*
# sky

from lib import database, log, mail, tools, warning
#from lib.printf import printf
import pymysql.cursors
import psutil, os
import datetime
#import os, shutil, subprocess

'''
def stats():
    # show status where variable_name in ("Uptime")
    check, user, ip, port, password=conf.get("mysql", 
            "check", 
            "mysql_user", 
            "mysql_ip", 
            "mysql_port", 
            "mysql_password"
            )

    if check=="1":
        printf("MySQL信息:")
        if user is None or \
                ip is None or \
                port is None or \
                password is None:
                    printf("请检查[mysql]配置参数")
        else:
            if port.isdigit():
                port=int(port)
                try:
                    conn=pymysql.connect(
                            host=ip,
                            port=port, 
                            user=user, 
                            #cursorclass=pymysql.cursors.DictCursor,   # 返回值带字段名称
                            password=password
                            )
                    with conn.cursor() as cursor:
                        """
                        Innodb_page_size
                        Innodb_buffer_pool_pages_total
                        Slow_queries: 慢sql数量
                        Threads_connected: 连接数
                        Threads_running: 并发数
                        Uptime: 运行时长s
                        """
                        # 获取pid
                        sql='show variables where variable_name="pid_file"'
                        cursor.execute(sql)
                        pid_file=cursor.fetchone()
                        if pid_file is None or os.path.exists(pid_file[1]) is False:
                            printf("无法获取MySQL Pid, 请检查MySQL的pid_file变量")
                        else:
                            with open(pid_file[1], "r") as f:
                                pid=int(f.read().strip())
                                printf(f"MySQL Pid: {pid}")

                            mysql_info=psutil.Process(pid).as_dict()

                            mysql_create_time=datetime.datetime.fromtimestamp(mysql_info["create_time"]).strftime("%Y-%m-%d %H:%M:%S")
                            printf(f"程序启动时间: {mysql_create_time}")

                            mysql_memory_percent=f"{mysql_info['memory_percent']:.2f}"
                            mysql_memory=tools.format_size(psutil.virtual_memory()[0] * mysql_info['memory_percent'] / 100)
                            printf(f"内存占用: {mysql_memory}/{mysql_memory_percent}%")

                            # 获取连接数
                            sql='show status where variable_name in ("threads_connected")'
                            cursor.execute(sql)
                            connected_num=cursor.fetchone()[1]
                            printf(f"连接数: {connected_num}")

                            # 获取慢日志
                            printf("-"*40)
                            printf("慢日志信息:", 2)
                            sql='show variables where variable_name="slow_query_log"'
                            cursor.execute(sql)
                            slow_query_log=cursor.fetchone()[1].strip().lower()
                            if slow_query_log=="0" or slow_query_log=="off":
                                printf("未开启慢日志.")
                            else:       # 开启了慢日志
                                sql='show variables where variable_name="log_output"'
                                cursor.execute(sql)
                                log_output=cursor.fetchone()[1].strip().lower()

                                if "file" in log_output:            # 格式为file: 将慢日志文件拷贝到report目录下, 并清空慢日志文件
                                        sql='show variables where variable_name="slow_query_log_file"'
                                        cursor.execute(sql)
                                        slow_query_log_file=cursor.fetchone()[1].strip().lower()
                                        if os.path.exists(slow_query_log_file):
                                            if os.path.getsize(slow_query_log_file) != 0:
                                                cmd=f"mysqldumpslow -s at -t 10 {slow_query_log_file} > ./report/slow_analysis.log"
                                                status, message=subprocess.getstatusoutput(cmd)
                                                shutil.copy(slow_query_log_file, "report/slow.log")
                                                with open(slow_query_log_file, "r+") as f:
                                                    f.truncate()
                                                printf("请查看慢日志分析文件slow_analysis.log及慢日志文件slow.log", 2)
                                            else:
                                                printf("未产生慢日志", 2)
                                        else:
                                            printf(f"MySQL中定义的慢日志文件({slow_query_log_file})不存在.")
                                else:
                                    printf(f"MySQL参数log_output未定义为file, 无法分析慢日志")
                                """
                                if "table" in log_output:           # 格式有table: 只获取当天的慢日志
                                    sql='select sql_text,  start_time,  query_time,  lock_time,  rows_examined from mysql.slow_log where start_time > (now()-interval 24 hour)'
                                    cursor.execute(sql)
                                    slow_log_all=cursor.fetchall()
                                    if len(slow_log_all)==0:
                                        printf("24小时内无慢日志生成.")
                                    else:
                                        printf("24小时内的慢日志.")
                                        for slow_log in slow_log_all:
                                            sql=slow_log[0].decode("utf8")
                                            printf(f"SQL: {sql}\n开始执行时间: {slow_log[1]}\n查询时间: {slow_log[2]}\n锁表时间: {slow_log[3]}\n扫描的行数: {slow_log[4]}")
                                            printf("*"*40)
                                elif log_output=="file":            # 格式为file: 将慢日志文件拷贝到report目录下, 并清空慢日志文件
                                        sql='show variables where variable_name="slow_query_log_file"'
                                        cursor.execute(sql)
                                        slow_query_log_file=cursor.fetchone()[1].strip().lower()
                                        if os.path.exists(slow_query_log_file):
                                            if os.path.getsize(slow_query_log_file) != 0:
                                                slow_log_file_name=slow_query_log_file.split("/")[-1]
                                                printf(f"请查看慢日志文件: {slow_log_file_name}")
                                                shutil.copy(slow_query_log_file, "./report/")
                                                with open(slow_query_log_file, "r+") as f:
                                                    f.truncate()
                                            else:
                                                printf("未产生慢日志")
                                        else:
                                            printf(f"MySQL中定义的慢日志文件({slow_query_log_file})不存在.")
                                """
                            printf("-"*40)

                            # 判断主从状态
                            printf("主从信息:")
                            sql='show slave status'
                            cursor.execute(sql)
                            slave_status=cursor.fetchall()

                            if len(slave_status)==0:            # master信息
                                role="master"
                                sql='show slave hosts'
                                cursor.execute(sql)
                                slave_num=len(cursor.fetchall())

                                printf(f"角色: {role}")
                                printf(f"slave数量: {slave_num}")
                            else:                               # slave信息
                                role="slave"
                                for i in slave_status:
                                    master_host=i[1]
                                    master_port=i[3]
                                    replicate_do_db=i[12]
                                    slave_io_thread=i[10]
                                    slave_io_state=i[0]
                                    slave_sql_thread=i[11]
                                    slave_sql_state=i[44]
                                    master_uuid=i[40]
                                    retrieved_gtid_set=i[51]
                                    executed_gtid_set=i[52]
                                    seconds_behind_master=i[32]

                                    printf(f"角色: {role}")
                                    if slave_io_thread.lower()=="no" and slave_sql_thread.lower()=="no":
                                        printf("数据库同步已关闭", 2)
                                    else:
                                        printf(f"Master IP: {master_host}:{master_port}")
                                        printf(f"同步的数据库: {replicate_do_db}")
                                        printf(f"Slave IO线程是否开启: {slave_io_thread}")
                                        printf(f"Slave IO线程状态: {slave_io_state}")
                                        printf(f"Slave SQL线程是否开启: {slave_sql_thread}")
                                        printf(f"Slave SQL线程状态: {slave_sql_state}")
                                        printf(f"Master UUID: {master_uuid}")
                                        printf(f"已接收的GTID集合: {retrieved_gtid_set}")
                                        executed_gtid_set=executed_gtid_set.replace('\n', ' ', -1)
                                        printf(f"已执行的GTID集合: {executed_gtid_set}")
                                        printf(f"Slave落后Master的时间(秒): {seconds_behind_master}")

                                        if slave_io_thread.lower()=="yes" and slave_sql_thread.lower()=="yes":
                                            printf("数据库同步状态正常", 1)
                                        else:
                                            printf("数据库同步状态不正常", 1)
                                        printf("-"*40)
                except Exception as e:
                    printf(f"无法连接数据库: {e}")
                else:
                    conn.close()
            else:
                printf("请检查[mysql]配置参数")
            printf("-"*80)
'''

def record(log_file, log_level, mysql_user, mysql_ip, mysql_password, mysql_port):
    logger=log.Logger(log_file, log_level)
    db=database.db()
    record_time=datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    logger.logger.debug("记录MySQL信息")
    port=int(mysql_port)
    pid=tools.find_pid(port)
    if pid==0:
        logger.logger.error(f"MySQL({port})未运行")
        sql="insert into mysql_constant(record_time, pid, port, boot_time) values(?, ?, ?, ?)"
        db.update_one(sql, (record_time, pid, port, "0"))
        db.update_one("update mysql_role set record_time=?, role=?", ("0", "master"))
    else:
        try:
            conn=pymysql.connect(
                    host=mysql_ip,
                    port=port, 
                    user=mysql_user, 
                    #cursorclass=pymysql.cursors.DictCursor,   # 返回值带字段名称
                    password=mysql_password
                    )
            with conn.cursor() as cursor:
                """
                # 获取pid
                sql='show variables where variable_name="pid_file"'
                cursor.execute(sql)
                pid_file=cursor.fetchone()
                if pid_file is None or os.path.exists(pid_file[1]) is False:
                    logger.logger.error("无法获取MySQL Pid, 请检查MySQL的pid_file变量及其指定的文件")
                else:
                    with open(pid_file[1], "r") as f:
                        pid=int(f.read().strip())
                """

                mysql_info=psutil.Process(pid).as_dict()
                # 写入mysql_constant表
                mysql_create_time=datetime.datetime.fromtimestamp(mysql_info["create_time"]).strftime("%Y-%m-%d %H:%M:%S")
                sql="insert into mysql_constant values(?, ?, ?, ?)"
                db.update_one(sql, (record_time, pid, port, mysql_create_time))

                mysql_memory_percent=mysql_info['memory_percent']
                mysql_memory=psutil.virtual_memory()[0] * mysql_memory_percent / 100

                # 获取连接数
                sql='show status where variable_name in ("threads_connected")'
                cursor.execute(sql)
                mysql_connected_num=cursor.fetchone()[1]
                mysql_num_threads=mysql_info["num_threads"]
                sql="insert into mysql_variable values(?, ?, ?, ?, ?, ?)"
                db.update_one(sql, (record_time, pid, mysql_memory, mysql_memory_percent, mysql_connected_num, mysql_num_threads))

                # 判断主从状态
                logger.logger.debug("记录MySQL集群信息...")
                sql='show slave status'
                cursor.execute(sql)
                slave_status=cursor.fetchall()

                if len(slave_status)==0:            # master信息
                    role="master"
                    sql='show slave hosts'
                    cursor.execute(sql)
                    slave_num=len(cursor.fetchall())

                    sql='show master status'
                    cursor.execute(sql)
                    master_data=cursor.fetchone()
                    binlog_do_db=master_data[2]
                    binlog_ignore_db=master_data[3]

                    sql='replace into mysql_master values(?, ?, ?, ?, ?)'
                    db.update_one(sql, (record_time, pid, slave_num, binlog_do_db, binlog_ignore_db))
                else:                               # slave信息
                    role="slave"
                    slave_list=[]
                    for i in slave_status:
                        master_host=i[1]
                        master_port=i[3]
                        replicate_do_db=i[12]
                        replicate_ignore_db=i[13]
                        slave_io_thread=i[10]
                        slave_io_state=i[0]
                        slave_sql_thread=i[11]
                        slave_sql_state=i[44]
                        master_uuid=i[40]
                        retrieved_gtid_set=i[51]
                        #executed_gtid_set=i[52]
                        executed_gtid_set=i[52].replace('\n', ' ', -1)
                        seconds_behind_master=i[32]
                        slave_list.append((record_time, pid, master_host, master_port, replicate_do_db, replicate_ignore_db, \
                                slave_io_thread, slave_io_state, slave_sql_thread, slave_sql_state, \
                                master_uuid, retrieved_gtid_set, executed_gtid_set, seconds_behind_master))
                    sql='insert into mysql_slave values(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)'
                    db.update_all(sql, slave_list)
                db.update_one("update mysql_role set record_time=?, role=?", (record_time, role))


                """
                # 获取慢日志
                printf("-"*40)
                printf("慢日志信息:", 2)
                sql='show variables where variable_name="slow_query_log"'
                cursor.execute(sql)
                slow_query_log=cursor.fetchone()[1].strip().lower()
                if slow_query_log=="0" or slow_query_log=="off":
                    printf("未开启慢日志.")
                else:       # 开启了慢日志
                    sql='show variables where variable_name="log_output"'
                    cursor.execute(sql)
                    log_output=cursor.fetchone()[1].strip().lower()

                    if "file" in log_output:            # 格式为file: 将慢日志文件拷贝到report目录下, 并清空慢日志文件
                            sql='show variables where variable_name="slow_query_log_file"'
                            cursor.execute(sql)
                            slow_query_log_file=cursor.fetchone()[1].strip().lower()
                            if os.path.exists(slow_query_log_file):
                                if os.path.getsize(slow_query_log_file) != 0:
                                    cmd=f"mysqldumpslow -s at -t 10 {slow_query_log_file} > ./report/slow_analysis.log"
                                    status, message=subprocess.getstatusoutput(cmd)
                                    shutil.copy(slow_query_log_file, "report/slow.log")
                                    with open(slow_query_log_file, "r+") as f:
                                        f.truncate()
                                    printf("请查看慢日志分析文件slow_analysis.log及慢日志文件slow.log", 2)
                                else:
                                    printf("未产生慢日志", 2)
                            else:
                                printf(f"MySQL中定义的慢日志文件({slow_query_log_file})不存在.")
                    else:
                        printf(f"MySQL参数log_output未定义为file, 无法分析慢日志")
                printf("-"*40)
                """
        except Exception as e:
            logger.logger.error(f"无法连接MySQL: {e}")
            sql="insert into error values(?, ?, ?, ?, ?)"
            db.update_one(sql, (record_time, "MySQL", "connection", str(e), 0))
        else:
            conn.close()

def running_analysis(log_file, log_level, warning_interval, sender_alias, receive, subject):
    logger=log.Logger(log_file, log_level)
    logger.logger.debug("开始分析MySQL运行情况...")
    db=database.db()
    sql="select port, pid from mysql_constant where record_time=(select max(record_time) from mysql_constant)"
    port, pid=db.query_one(sql)
    flag= 1 if pid==0 else 0        # 是否预警
    warning_flag=warning.warning(logger, db, flag, "mysql", "running", warning_interval)
    if warning_flag:
        warning_msg=f"MySQL预警:\nMySQL({port})未运行"
        mail.send(logger, warning_msg, sender_alias, receive, subject, msg=f'mysql_running')

def master_slave_analysis(log_file, log_level, seconds_behind_master, warning_interval, sender_alias, receive, subject):
    logger=log.Logger(log_file, log_level)
    db=database.db()
    sql="select role, slave_io_thread, slave_sql_thread, seconds_behind_master, slave_io_state, slave_sql_state from mysql_slave, mysql_role where mysql_role.record_time=mysql_slave.record_time"
    data=db.query_one(sql)
    conn_msg="slave_conn"
    delay_msg="slave_delay"
    if data is not None and data[0]=="slave":
        logger.logger.debug("开始分析MySQL主从信息")
        if data[1].lower()==data[2].lower()=="yes":
            conn_flag=0
            delay_flag= 1 if data[3] >= seconds_behind_master else 0
        else:
            conn_flag=1
            delay_flag=None

        for flag, msg in [(conn_flag, conn_msg), (delay_flag, delay_msg)]:
            if flag is not None:
                warning_flag=warning.warning(logger, db, flag, "mysql", msg, warning_interval)
                if warning_flag:
                    warning_msg="MySQL预警:\n"\
                            "MySQL主从连接:\n"\
                            f"Slave_IO_Running: {data[1]}\n"\
                            f"Slave_SQL_Running: {data[2]}\n"\
                            f"Slave_IO_State: {data[4]}\n"\
                            f"Slave_SQL_Running_State: {data[5]}\n"\
                            f"Seconds_Behind_Master: {data[3]}"
                    mail.send(logger, warning_msg, sender_alias, receive, subject, msg=msg)
    
if __name__ == "__main__":
    main()
