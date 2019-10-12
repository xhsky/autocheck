#!/usr/bin/env python
# *-* coding:utf8 *-*
# sky

from lib.printf import printf
import psutil
import datetime

def disk():
    printf("磁盘信息:")
    printf("磁盘\t\t大小(G)  已使用(G) 可用(G)  挂载点")
    all_disk=psutil.disk_partitions()
    for i in all_disk:
        size=psutil.disk_usage(i[1])
        total=f"{size[0]/1024/1024/1024:.2f}"
        used=f"{size[1]/1024/1024/1024:.2f}"
        avail=f"{size[2]/1024/1024/1024:.2f}"
        printf(f"{i[0]}\t{total}  {used}  {avail}  {i[1]}")
    printf("-"*80)

def cpu():
    printf("CPU信息:")
    printf(f"cpu逻辑核心数: {psutil.cpu_count()}")
    printf(f"cpu当前利用率(%): {psutil.cpu_percent(interval=5)}")
    printf("-"*80)

def memory():
    printf("内存信息:")
    mem=psutil.virtual_memory()
    printf(f"总内存(G): {mem[0]/1024/1024/1024:.02f}")
    printf(f"可用内存(G): {mem[1]/1024/1024/1024:.02f}")
    printf(f"已使用(%): {mem[2]:.02f}")  # (total-avail)/total
    printf(f"已使用内存(G): {mem[3]/1024/1024/1024:.02f}")
    printf(f"空闲内存(G): {mem[4]/1024/1024/1024:.02f}")

    printf("-"*80)

def swap():
    printf("swap信息:")
    swap_mem=psutil.swap_memory()
    printf(f"swap大小(G): {swap_mem[0]/1024/1024/1024:.02f}")
    printf(f"已使用(G): {swap_mem[1]/1024/1024/1024:.02f}")
    printf(f"未使用(G): {swap_mem[2]/1024/1024/1024:.02f}")
    printf(f"已使用(%): {swap_mem[4]:.02f}")
    printf("-"*80)

def boot_time():
    printf(f'服务器启动时间: {datetime.datetime.fromtimestamp(psutil.boot_time()).strftime("%Y-%m-%d %H:%M:%S")}')
    printf("-"*80)




def info():
    boot_time()
    disk()
    cpu()
    memory()
    swap()
    
if __name__ == "__main__":
    info()
