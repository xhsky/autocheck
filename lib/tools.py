#!/usr/bin/env python
# *-* coding:utf8 *-*
# sky

import psutil

def format_size(byte):
    byte=float(byte)
    kb=byte/1024

    if kb >= 1024:
        mb=kb/1024
        if mb>=1024:
            gb=mb/1024
            return f"{gb:.2f}G"
        else:
            return f"{mb:.2f}M"
    else:
        return f"{kb:.2f}k"
def find_pid(port):
    """根据端口获取相应的pid
    """
    for i in psutil.net_connections():
        if port==i[3][1] and i[6] is not None:
            pid=i[6]
            break
    else:
        pid=0
    return pid
            
if __name__ == "__main__":
    main()
