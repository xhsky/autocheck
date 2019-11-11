#!/usr/bin/env python
# *-* coding:utf8 *-*
# sky

from lib import database
def init_db(db_file):
    status_table_sql="create table if not exists status(\
            section varchar(12) not null,
            option varchar(24) not null, 
            value varchar(1024) default null,  
            flag tinyint default 0,  
            primary key(section, option)
            )"
    status_data=[('autocheck', 'hostname', 'dream', 1), 
            ('logs', 'log_file', './logs/autocheck.log', 1), 
            ('logs', 'log_file', './logs/autocheck.log', 1), 
            ]

    
if __name__ == "__main__":
    main()
