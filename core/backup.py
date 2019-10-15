#!/usr/bin/env python
# *-* coding:utf8 *-*
# sky

from lib import conf
from lib.printf import printf
from lib.tools import format_size
import os, time

def cat():
    check, directory=conf.get("backup", 
            "check", 
            "dir"
            )

    if check=="1":
        printf("-"*80)
        printf("备份信息:")
        if directory is not None:
            dir_list=[]
            for i in directory.split(","):
                dir_list.append(i.strip())

            for i in dir_list:
                printf(f"{i}目录下信息:")
                if os.path.exists(i):
                    for j in os.listdir(i):
                        filename=f"{i}/{j}"
                        if os.path.isfile(filename):
                            size=os.path.getsize(filename)
                            ctime=os.path.getctime(filename)
                            printf(f"文件名: {j}, 大小: {format_size(size)}, 创建时间: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(ctime))}")
                else:
                    printf(f"{i}目录不存在")
                printf("-"*40)

        else:
            printf("[backup]下未定义dir")
        printf("-"*80)



    
if __name__ == "__main__":
    main()
