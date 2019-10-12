#!/usr/bin/env python
# *-* coding:utf8 *-*
# sky

from lib import conf
from lib.printf import printf
import pymysql.cursors

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
                        #sql='show status where variable_name in ("Uptime", "Threads_running")'
                        sql='show slave hosts'
                        cursor.execute(sql)
                        result=cursor.fetchall()
                        print(result)
                except Exception as e:
                    print(f"无法连接数据库: {e}")
                else:
                    conn.close()
            else:
                printf("请检查[mysql]配置参数")
    
if __name__ == "__main__":
    main()
