#!/usr/bin/env python
# *-* coding:utf8 *-*
# sky

import datetime

def warning(logger, db, flag, section, value, warning_interval):
    """
        修复性预警
    """
    warning_flag=0
    record_time_now=datetime.datetime.now()
    record_time=record_time_now.strftime("%Y-%m-%d %H:%M:%S")
    sql="select record_time from warning_record where section=? and value=? and debug=0 and record_time=(select max(record_time) from warning_record where section=? and value=?)"
    warning_time=db.query_one(sql, (section, value, section, value))        # 获取预警日志的时间记录

    # 判断是否出现预警情况
    if flag:    # 出现预警情况
        # 无时间记录或时间记录在预警间隔之外, 则将该记录写入预警日志
        if warning_time is None or record_time_now > datetime.datetime.strptime(warning_time[0], "%Y-%m-%d %H:%M:%S") + datetime.timedelta(minutes=warning_interval):
            warning_flag=1
            sql="insert into warning_record values(?, ?, ?, ?)"
            db.update_one(sql, (record_time, section, value, 0))
            logger.logger.info(f"写入{section} {value}预警信息")
        else:
            logger.logger.info(f"当前处于{section} {value}预警间隔时间内, 不进行下一步处理")
    else:       # 非预警, 则将预警日志修复
        if warning_time is not None:
            logger.logger.info(f"{section} {value}预警修复")
            sql="update warning_record set debug=1 where section=? and value=? and record_time=?"
            db.update_one(sql, (section, value, warning_time[0]))
    return warning_flag

def non_remedial_warning(logger, db, section, value, warning_msg, record_time, warning_interval):
    """
        非修复性预警
    """
    warning_flag=0
    sql="select record_time from warning_record where section=? and value=? and record_time=(select max(record_time) from warning_record where section=? and value=?)"
    warning_time=db.query_one(sql, (section, value, section, value))        # 获取预警日志的时间记录

    # 无时间记录或时间记录在预警间隔之外, 则将该记录写入预警日志
    if warning_time is None or datetime.datetime.strptime(record_time, '%Y-%m-%d %H:%M:%S') > datetime.datetime.strptime(warning_time[0], '%Y-%m-%d %H:%M:%S') + datetime.timedelta(minutes=warning_interval):
        warning_flag=1
        logger.logger.warning(warning_msg)
        sql="insert into warning_record values(?, ?, ?, ?)"
        db.update_one(sql, (record_time, section, value, 0))
        logger.logger.info(f"写入{section} {value}预警信息")
    return warning_flag
    
if __name__ == "__main__":
    main()
