#!/usr/bin/env python
# *-* coding:utf8 *-*
# sky

from lib import database, log, warning, mail
#from lib.printf import printf
from lib.tools import format_size
import os, datetime

'''
def show(backup_dirs_dict):
    for i in backup_dirs_dict:
        printf(f"{i}目录:")
        if backup_dirs_dict[i] is not None:
            backup_dir_list=sorted(backup_dirs_dict[i].items(), key=lambda d:d[1][1])
            for j in backup_dir_list:
                size=os.path.getsize(j[0])
                ctime=os.path.getctime(j[0])
                printf(f"文件名: {j[0]}, 大小: {format_size(size)}, 创建时间: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(ctime))}")
        else:
            printf("该目录或指定结尾文件不存在.")
        printf("*"*40)


def collect(backup_dict):
    """收集信息
    """
    backup_dirs_dict={}
    for i in backup_dict:
        backup_dir_dict={}
        if os.path.exists(i):
            flag=0
            for j in os.listdir(i):
                filename=f"{i}/{j}"
                if os.path.isfile(filename) and filename.endswith(backup_dict[i]):
                    size=os.path.getsize(filename)
                    ctime=os.path.getctime(filename)
                    backup_dir_dict[filename]=(size, ctime)
                    flag=1
            if flag==0:
                backup_dir_dict=None
        else:
            backup_dir_dict=None
        backup_dirs_dict[i]=backup_dir_dict
    return backup_dirs_dict

def cat():
    if check=="1":
        if directory is not None:
            dir_list=[]
            for i in directory.split(","):
                dir_list.append(i.strip())

            regular_list=[]
            for i in regular.split(","):
                regular_list.append(i.strip())

            backup_dict=dict(zip(dir_list, regular_list))
            backup_dirs_dict=collect(backup_dict)           # 收集
            show(backup_dirs_dict)                          # 显示
            analysis(backup_dirs_dict)                      # 分析
        else:
            printf("[backup]下未定义dir")
        printf("-"*80)
'''

def record(log_file, log_level, directory, regular):
    logger=log.Logger(log_file, log_level)
    logger.logger.info(f"记录备份目录{directory}的信息...")
    record_time=datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    backup_info=[]
    if os.path.exists(directory):
        flag=0
        for i in os.listdir(directory):
            filename=f"{directory}/{i}"
            if os.path.isfile(filename) and filename.endswith(regular):
                size=os.path.getsize(filename)
                ctime=datetime.datetime.fromtimestamp(os.path.getctime(filename)).strftime("%Y-%m-%d %H:%M:%S")
                backup_info.append((record_time, directory, i, size, ctime))
                flag=1
        if flag==0:
            backup_info.append((record_time, directory, None, None, None))
    else:
        backup_info.append((record_time, directory, None, None, None))
    db=database.db()
    delete_sql="delete from backup where directory=?"
    db.update_one(delete_sql, [directory])
    sql="insert into backup values(?, ?, ?, ?, ?)"
    db.update_all(sql, backup_info)

def analysis(log_file, log_level, directory, warning_interval, sender_alias, receive, subject):
    """对备份文件进行预警
    1. 备份目录不存在则提示
    2. 当天的备份文件未生成则提示
    3. 当天的备份文件小于上一个的大小的99%则提示
    """
    logger=log.Logger(log_file, log_level)
    db=database.db()
    logger.logger.debug("分析备份文件...")
    #sql=f"select record_time, name, used_percent, mounted from disk where record_time=(select max(record_time) from disk)"
    sql="select record_time, directory, filename, size, ctime from backup where directory=? order by record_time, ctime desc limit 2"
    data=db.query_all(sql, (directory, ))
    now_time=datetime.datetime.now().strftime("%Y-%m-%d")

    if len(data) < 2:
        if data[1][2] is None:
            flag=1
            value="dir_is_None"
            warning_msg=f"备份预警:\n备份目录({directory})不存在"
    else:
        flag=0                 # 是否有预警信息
        if now_time not in data[0][4]:
            flag=1
            warning_msg=f"备份预警:\n备份目录({directory})当天备份文件未生成"
            value="file_is_None"
        elif  data[0][3] < data[1][3] * 0.99:
            flag=1
            warning_msg=f"备份预警:\n备份目录({directory})当天备份文件({format_size(data[0][3])})与上一次({format_size(data[1][3])})相比相差较大"
            value="file_is_small"

        warning_flag=warning.warning(logger, db, flag, f"backup {directory}", value, warning_interval)
        if warning_flag:
            mail.send(logger, warning_msg, sender_alias, receive, subject, msg=f"{directory}_{value}")

if __name__ == "__main__":
    main()
