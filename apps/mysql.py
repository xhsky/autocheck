#!/usr/bin/env python
# *-* coding:utf8 *-*
# sky

from lib import database
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
def record(logger, mysql_user, mysql_ip, mysql_password, mysql_port):
    db=database.db()
    record_time=datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    logger.logger.debug("记录MySQL信息")
    try:
        conn=pymysql.connect(
                host=mysql_ip,
                port=int(mysql_port), 
                user=mysql_user, 
                #cursorclass=pymysql.cursors.DictCursor,   # 返回值带字段名称
                password=mysql_password
                )
        with conn.cursor() as cursor:
            # 获取pid
            sql='show variables where variable_name="pid_file"'
            cursor.execute(sql)
            pid_file=cursor.fetchone()
            if pid_file is None or os.path.exists(pid_file[1]) is False:
                logger.logger.error("无法获取MySQL Pid, 请检查MySQL的pid_file变量及其指定的文件")
            else:
                with open(pid_file[1], "r") as f:
                    pid=int(f.read().strip())

                mysql_info=psutil.Process(pid).as_dict()
                mysql_create_time=datetime.datetime.fromtimestamp(mysql_info["create_time"]).strftime("%Y-%m-%d %H:%M:%S")
                sql="select boot_time from mysql_constant where port=? and pid=? order by record_time desc limit 1"
                boottime_in_db=db.query_one(sql,  (mysql_port,  pid))
                if boottime_in_db is None or boottime_in_db[0]!=mysql_create_time:
                    sql="insert into mysql_constant values(?, ?, ?, ?)"
                    db.update_one(sql, (record_time, pid, mysql_port, mysql_create_time))

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

                record_time=datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
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

                    sql='replace into mysql_master values(?, ?, ?, ?, ?, ?)'
                    db.update_one(sql, (record_time, pid, role, slave_num, binlog_do_db, binlog_ignore_db))

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
                        slave_list.append((record_time, pid, role, master_host, master_port, replicate_do_db, replicate_ignore_db, \
                                slave_io_thread, slave_io_state, slave_sql_thread, slave_sql_state, \
                                master_uuid, retrieved_gtid_set, executed_gtid_set, seconds_behind_master))
                    sql='insert into mysql_slave values(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)'
                    db.update_all(sql, slave_list)
                '''
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

                '''
    except Exception as e:
        logger.logger.error(f"无法连接数据库: {e}")
        sql="insert into error values(?, ?, ?, ?, ?)"
        db.update_one(sql, (record_time, "MySQL", "connection", str(e), 0))
    else:
        conn.close()
    
if __name__ == "__main__":
    main()
