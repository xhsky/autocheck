#!/usr/bin/env python
# *-* coding:utf8 *-*
# sky

from lib import conf
from lib.printf import printf
import pymysql.cursors
from psutil import Process
import datetime
import os, shutil

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

                            mysql_info=Process(pid).as_dict()

                            mysql_create_time=datetime.datetime.fromtimestamp(mysql_info["create_time"]).strftime("%Y-%m-%d %H:%M:%S")
                            printf(f"程序启动时间: {mysql_create_time}")

                            mysql_memory_percent=f"{mysql_info['memory_percent']:.2f}"
                            printf(f"内存占用(%): {mysql_memory_percent}")

                            # 获取连接数
                            sql='show status where variable_name in ("threads_connected")'
                            cursor.execute(sql)
                            connected_num=cursor.fetchone()[1]
                            printf(f"连接数: {connected_num}")

                            # 获取慢日志
                            printf("-"*40)
                            printf("慢日志信息:")
                            sql='show variables where variable_name="slow_query_log"'
                            cursor.execute(sql)
                            slow_query_log=cursor.fetchone()[1].strip().lower()
                            if slow_query_log=="0" or slow_query_log=="off":
                                printf("未开启慢日志.")
                            else:       # 开启了慢日志
                                sql='show variables where variable_name="log_output"'
                                cursor.execute(sql)
                                log_output=cursor.fetchone()[1].strip().lower()

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
                                        printf("同步已关闭")
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
                                        printf("-"*40)
                except Exception as e:
                    printf(f"无法连接数据库: {e}")
                else:
                    conn.close()
            else:
                printf("请检查[mysql]配置参数")
            printf("-"*80)
    
if __name__ == "__main__":
    main()
