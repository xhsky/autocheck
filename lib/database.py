#!/usr/bin/env python
# *-* coding:utf8 *-*
# sky
import sqlite3

class db(object):
    def __init__(self, db="data/auto.db"):
        self.db=db
        self.conn()
        self.cur=self.conn.cursor()

    def conn(self):
        self.conn=sqlite3.connect(self.db)

    def query_one(self, sql, condition=None):
        if condition is None:
            self.cur.execute(sql)
        else:
            self.cur.execute(sql, condition)
        return self.cur.fetchone()

    def query_all(self, sql, condition=None):
        if condition is None:
            self.cur.execute(sql)
        else:
            self.cur.execute(sql, condition)
        return self.cur.fetchall()

    def update_all(self, sql, condition=None):
        if condition is None:
            self.cur.execute(sql)
        else:
            self.cur.executemany(sql, condition)
        self.conn.commit()

    def update_one(self, sql, condition=None):
        if condition is None:
            self.cur.execute(sql)
        else:
            self.cur.execute(sql, condition)
        self.conn.commit()
    
    def close(self):
        self.__del__()

    def __del__(self):
        try:
            self.cur.close()
            self.conn.close()
        except: 
            pass

    
if __name__ == "__main__":
    main()
