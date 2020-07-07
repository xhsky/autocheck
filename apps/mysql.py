#!/usr/bin/env python
# *-* coding:utf8 *-*
# sky

from lib import database, log, notification, tools, warning
import pymysql.cursors
import psutil, os
import datetime, subprocess

def export_slow_log(logger, mysql_user, mysql_ip, mysql_password, mysql_port, slow_ana_file, slow_file):
    """获取慢日志
    """
    conn=pymysql.connect(
            host=mysql_ip,
            port=int(mysql_port), 
            user=mysql_user, 
            password=mysql_password
            )
    with conn.cursor() as cursor:
        sql='show variables where variable_name="slow_query_log"'
        cursor.execute(sql)
        slow_query_log=cursor.fetchone()[1].strip().lower()
        flag=0  # 是否有慢日志
        if slow_query_log=="0" or slow_query_log=="off":
            msg="未开启慢日志."
        else: 
            sql='show variables where variable_name="log_output"'
            cursor.execute(sql)
            log_output=cursor.fetchone()[1].strip().lower()

            if "file" in log_output:            # 格式为file: 将慢日志文件拷贝到report目录下, 并清空慢日志文件
                sql='show variables where variable_name="slow_query_log_file"'
                cursor.execute(sql)
                slow_query_log_file=cursor.fetchone()[1].strip().lower()
                if os.path.exists(slow_query_log_file):
                    if os.path.getsize(slow_query_log_file) != 0:
                        flag=1
                        cmd=f"mysqldumpslow -s at -t 10 {slow_query_log_file} > {slow_ana_file}"
                        status, message=subprocess.getstatusoutput(cmd)
                        with open(slow_query_log_file, "r+") as f, open(slow_file, "w") as slow_f:
                            slow_f.write(f.read())
                            f.seek(0, 0)
                            f.truncate()
                        msg=f"请查看慢日志分析文件{slow_ana_file}及慢日志文件{slow_file}"
                    else:
                        msg="未产生慢日志"
                else:
                    msg=f"MySQL中定义的慢日志文件({slow_query_log_file})不存在."
            else:
                msg=f"MySQL参数log_output未定义为file, 无法分析慢日志"
        return flag, msg

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
        role=db.query_one("select role from mysql_role")[0]
        db.update_one("update mysql_role set record_time=?, role=?", ("0", role))
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
        except Exception as e:
            logger.logger.error(f"无法连接MySQL: {e}")
            sql="insert into error values(?, ?, ?, ?, ?)"
            db.update_one(sql, (record_time, "MySQL", "connection", str(e), 0))
        else:
            conn.close()

def running_analysis(log_file, log_level, warning_interval, notify_dict):
    logger=log.Logger(log_file, log_level)
    logger.logger.debug("开始分析MySQL运行情况...")
    db=database.db()
    sql="select port, pid from mysql_constant where record_time=(select max(record_time) from mysql_constant)"
    port, pid=db.query_one(sql)
    flag= 1 if pid==0 else 0        # 是否预警
    warning_flag=warning.warning(logger, db, flag, "mysql", "running", warning_interval)
    if warning_flag:
        warning_msg=f"MySQL预警:\nMySQL({port})未运行"
        notification.send(logger, warning_msg, notify_dict, msg=f'mysql_running')

def master_slave_analysis(log_file, log_level, seconds_behind_master, warning_interval, notify_dict):
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
                    notification.send(logger, warning_msg, notify_dict, msg=msg)
    
if __name__ == "__main__":
    main()
