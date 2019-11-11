#!/usr/bin/env python
# *-* coding:utf8 *-*
# sky

from lib import database

def get(section, *option):
    db=database.db()

    values=[]
    for i in option:
        sql="select value from status where section=? and option=?"
        values.append(db.query_one(sql, (section, i))[0])
    return values

if __name__ == "__main__":
    print(get("redis", "check"))
