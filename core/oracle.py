#!/usr/bin/env python
# *-* coding:utf8 *-*
# sky

import subprocess
from lib import conf
from lib.printf import printf
import shutil

def info():
    check, oracle_sid, awr_hours=conf.get("oracle", 
            "check", 
            "oracle_sid", 
            "awr_hours"
            )
    
    if check=="1":
        printf("Oracle信息:")
        # 表空间
        printf("表空间信息:")
        sql="""
        set heading off trimspool on feedback off pagesize 0 linesize 1000
        SELECT a.tablespace_name ,
          a.bytes/ 1024 / 1024,
          ( a.bytes - b.bytes ) / 1024 / 1024 ,
          b.bytes / 1024 / 1024 ,
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
        printf(f"表空间名称    表空间大小(M)    已使用表空间(M)    未使用表空间(M)    使用率(%)")
        for i in message.splitlines():
            i=i.split()
            row=f"{i[0]:<14}{float(i[1]):<17.02f}{float(i[2]):<20.02f}{float(i[3]):<18.02f}{float(i[4]):<8.02f}"
            printf(row)

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

if __name__ == "__main__":
    main()
