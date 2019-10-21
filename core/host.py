#!/usr/bin/env python
# *-* coding:utf8 *-*
# sky

from lib.printf import printf
from lib import tools
import psutil
import datetime

def disk():
    all_disk=psutil.disk_partitions()

    # 显示
    printf("磁盘信息:")
    disk_name_length=[]         # 获取磁盘名称的长度, 用于下方格式化输出
    for disk_name in all_disk:
        disk_name_length.append(len(disk_name[0]))
    length=max(disk_name_length)
    space_length=f" "*(length-4)

    printf(f"磁盘{space_length}  大小      已使用            可用      挂载点")
    for i in all_disk:
        size=psutil.disk_usage(i[1])
        total=tools.format_size(size[0])
        used=f"{tools.format_size(size[1])}/{size[3]}%"
        free=tools.format_size(size[2])
        printf(f"{i[0]:<{length}}  {total:<8}  {used:<16}  {free:<8}  {i[1]:<}")

    # 分析
    normal=0
    for i in all_disk:
        size=psutil.disk_usage(i[1])
        used_percent=size[3]
        free=size[2]
        warning_value=95
        if used_percent > warning_value:     # 使用率大于95%或可用空间小于5G
            printf(f"磁盘'{i[1]}'空间已超过{warning_value}%, 请查看", 1)
            normal=1

    if normal==0:
        printf("磁盘空间正常.", 1)

        
def cpu():
    printf("CPU信息:")
    printf(f"cpu逻辑核心数: {psutil.cpu_count()}")
    printf(f"cpu当前利用率(%): {psutil.cpu_percent(interval=5)}")

def memory():
    printf("内存信息:")
    mem=psutil.virtual_memory()

    # 显示
    printf(f"总内存(total): {tools.format_size(mem[0])}")
    printf(f"可用内存(available): {tools.format_size(mem[1])}")
    printf(f"已用内存(used): {tools.format_size(mem[3])}/{mem[2]}%") # (total-avail)/total
    printf(f"空闲内存(free): {tools.format_size(mem[4])}")

    # 分析
    warning_value=95
    if mem[2] > warning_value:
        printf(f"内存使用已超过{warning_value}%.")
        normal=1

    normal=0
    if normal==0:
        printf("内存空间正常.", 1)

def swap():
    printf("swap信息:")
    swap_mem=psutil.swap_memory()
    printf(f"总swap(total): {tools.format_size(swap_mem[0])}")
    printf(f"已使用(used): {tools.format_size(swap_mem[1])}/{swap_mem[3]}%")
    printf(f"未使用(free): {tools.format_size(swap_mem[2])}")

def boot_time():
    printf(f'服务器启动时间: {datetime.datetime.fromtimestamp(psutil.boot_time()).strftime("%Y-%m-%d %H:%M:%S")}')

def info():
    boot_time()
    printf("-"*80)
    disk()
    printf("-"*80)
    cpu()
    printf("-"*80)
    memory()
    printf("-"*80)
    swap()
    
if __name__ == "__main__":
    info()
