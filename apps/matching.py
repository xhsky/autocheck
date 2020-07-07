#!/usr/bin/env python3
# *-* coding:utf8 *-*
# sky

from lib import database, log, warning, notification
import os, datetime, re

def matching_record(logger, db, record_time, matching_file, matching_key):
    logger.logger.debug(f"记录匹配({matching_file}:{matching_key})信息...")

    with open(matching_file, "r") as f:
        sql="select record_filesize from matching where record_time=(select max(record_time) from matching where matching_file=? and matching_key=?) and matching_file=? and matching_key=?"
        record_filesize=db.query_one(sql, (matching_file, matching_key, matching_file, matching_key))[0]
        now_filesize=os.stat(matching_file)[6]
        #logger.logger.info(f"{matching_file=}, {record_filesize=}, {now_filesize=}")
        if now_filesize < record_filesize:
            record_filesize=0
        elif now_filesize == record_filesize:
            return

        f.seek(record_filesize)
        lines=f.readlines()
        next_filesize=f.tell()
        #logger.logger.info(f"{matching_file=}, {record_filesize=}, {lines=}, {next_filesize=}")
        warning_flag=0
        sql="insert into matching values(?, ?, ?, ?, ?)"
        for line in lines:
            if re.search(matching_key, line):
                warning_flag=1
                #logger.logger.warning(f"{matching_file}文件中出现{matching_key}")
                db.update_one(sql, (record_time, matching_file, matching_key, line, next_filesize))
        if warning_flag==0:
            db.update_one(sql, (record_time, matching_file, matching_key, "Nothing", next_filesize))

def matching_records(log_file, log_level, matching_dict):
    logger=log.Logger(log_file, log_level)
    db=database.db()
    record_time=datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    for i in matching_dict:
        matching_record(logger, db, record_time, i, matching_dict[i])

def matching_analysis(log_file, log_level, warning_interval, matching_dict, notify_dict):
    logger=log.Logger(log_file, log_level)
    db=database.db()
    for matching_file in matching_dict:
        sql=f"select record_time,  matching_context from matching \
                where record_time=( \
                select max(record_time) from matching \
                where matching_context!=? and matching_file=? and matching_key=?\
                )"
        data=db.query_one(sql, ("all", matching_file, matching_dict[matching_file]))

        logger.logger.debug("分析匹配...")
        if data is not None:
            if data[1] != 'Nothing':
                warning_msg=f"\"{matching_file}\"文件中\"{data[1].strip()}\"行存在关键字\"{matching_dict[matching_file]}\""
                msg=f"{matching_file}_{matching_dict[matching_file]}"
                warning_flag=warning.non_remedial_warning(logger, db, "matching", msg, warning_msg, data[0], warning_interval)
                if warning_flag:
                    warning_msg=f"日志分析预警:\n{warning_msg}\n"
                    notification.send(logger, warning_msg, notify_dict, msg=msg)


if __name__ == "__main__":
    main()
