#!/usr/bin/env python
# *-* coding:utf8 *-*
# sky

from lib import conf
from lib.printf import printf
from lib.tools import format_size
import os, time

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

def analysis(backup_dirs_dict):
    """对备份文件进行预警
    1. 备份目录不存在则提示
    2. 当天的备份文件未生成则提示
    3. 当天的备份文件小于上一个的大小的99%则提示
    """
    printf("备份信息:", 1)
    now_date=time.time()
    for i in backup_dirs_dict:
        if backup_dirs_dict[i] is not None:
            backup_dir_list=sorted(backup_dirs_dict[i].items(), key=lambda d:d[1][1])
            last_date=backup_dir_list[-1][1][1]

            if time.strftime('%Y-%m-%d', time.localtime(last_date))!=time.strftime('%Y-%m-%d', time.localtime(now_date)):
                printf(f"备份({i})下未生成今天的备份.", 1)
            else:
                if len(backup_dir_list) > 1:
                    if backup_dir_list[-1][1][0] < backup_dir_list[-2][1][0] * 0.99:
                        printf(f"备份({i})下今天的备份文件({format_size(backup_dir_list[-1][1][0])})与之前的备份文件({format_size(backup_dir_list[-2][1][0])})相差较大.", 1)
                    else:
                        printf(f"备份({i})正常.", 1)
        else:
            printf(f"备份目录{i}或指定结尾文件不存在.", 1)

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
                if  os.path.isfile(filename) and filename.endswith(backup_dict[i]):
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
    check, directory, regular=conf.get("backup", 
            "check", 
            "dir", 
            "regular"
            )

    if check=="1":
        printf("-"*80)
        printf("备份信息:")
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

if __name__ == "__main__":
    main()
