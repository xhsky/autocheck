#!/usr/bin/env python
# *-* coding:utf8 *-*
# sky

import subprocess
from lib import conf
from lib.tools import format_size
from lib.printf import printf
import shutil

def info():
    check, awr_hours=conf.get("oracle", 
            "check", 
            "awr_hours"
            )
    
    if check=="1":
        printf("Oracle信息:")
        # 表空间
        printf("表空间信息:")
        sql="""
        set heading off trimspool on feedback off pagesize 0 linesize 1000
        SELECT a.tablespace_name ,
          a.bytes,
          ( a.bytes - b.bytes ),
          b.bytes,
          Round(( ( a.bytes - b.bytes ) / a.bytes ) * 100, 2)
        FROM  (SELECT tablespace_name,
                      SUM(bytes) bytes
                FROM  dba_data_files
                GROUP  BY tablespace_name) a,
              (SELECT tablespace_name,
                      SUM(bytes) bytes,
                      Max(bytes) largest
                FROM  dba_free_space
                GROUP  BY tablespace_name) b
        WHERE  a.tablespace_name = b.tablespace_name
        ORDER  BY ( ( a.bytes - b.bytes ) / a.bytes ) DESC;
        """
        cmd=f"su - oracle -c 'sqlplus -S / as sysdba <<EOF\n{sql}\nEOF'"
        (status, message)=subprocess.getstatusoutput(cmd)
        if status==0:
            printf(f"表空间名称    表空间大小    已使用表空间    未使用表空间    使用率(%)")
            for i in message.splitlines():
                i=i.split()
                row=f"{i[0]:<14}{format_size(i[1]):<14}{format_size(i[2]):<17}{format_size(i[3]):<17}{i[4]:<4}"
                printf(row)
                if float(i[4]) > 95:
                    printf(f"Oracle: {i[0]}表空间不足, 已使用{i[4]}%", 1)

            # awr
            printf("-"*40)
            printf("awr信息:")
            awr_format="html"
            awr_file='/tmp/awr.html'
            days=4
            sql="""
            set heading off trimspool on feedback off pagesize 0
            select trim(max(snap_id)) from dba_hist_snapshot;
            """
            cmd=f"su - oracle -c 'sqlplus -S / as sysdba <<EOF\n{sql}\nEOF'"
            (status, message)=subprocess.getstatusoutput(cmd)
            max_snap_id=int(message)
            if int(awr_hours) > max_snap_id:
                awr_hours=max_snap_id
            min_snap_id=max_snap_id-int(awr_hours)
            cmd=f"""su - oracle -c"
            echo -e '{awr_format}\n{days}\n{min_snap_id}\n{max_snap_id}\n{awr_file}\n' | (sqlplus -S / as sysdba @?/rdbms/admin/awrrpt.sql)"
            """
            (status, message)=subprocess.getstatusoutput(cmd)
            if status==0:
                shutil.move(awr_file, "./report/")
                printf("请查看awr.html文件")
            else:
                printf("awr生成失败, 请手动生成")
        else:
            printf("无法连接Oracle.")

if __name__ == "__main__":
    main()
