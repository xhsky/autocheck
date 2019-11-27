#!/usr/bin/env python
# *-* coding:utf8 *-*
# sky

from apscheduler.schedulers.blocking import BlockingScheduler
from lib import log, conf, database
import datetime

def clean_data(logger, keep_days):
    logger.logger.info("开始清理数据...")
    db=database.db()
    all_tables=db.query_all("select name from sqlite_master where type='table'")
    now_time=datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    for i in all_tables:
        table=i[0]
        sql=f"pragma table_info('{table}')"
        columns=db.query_all(sql)
        for j in columns:
            if j[1]=="record_time":
                sql=f"delete from {table} where record_time < datetime('{now_time}', '-{keep_days} day')"
                db.update_one(sql)
    logger.logger.info("结束清理数据...")

def clean():
    log_file, log_level=log.get_log_args()
    logger=log.Logger(log_file, log_level)
    logger.logger.info("清理程序启动...")

    keep_days=conf.get("autocheck", "keep_days")[0]

    scheduler=BlockingScheduler()
    scheduler.add_job(clean_data, 'cron', args=[logger, int(keep_days)], day_of_week='0-6', hour=1, minute=05, id=f'clean')
    scheduler.start()
    
if __name__ == "__main__":
    main()
