#!/usr/bin/env python
# *-* coding:utf8 *-*
# sky

import logging
from logging import handlers
from lib import database

class Logger(object):
    #日志级别关系映射
    level_relations = {
        'debug':logging.DEBUG,
        'info':logging.INFO,
        'warning':logging.WARNING,
        'error':logging.ERROR,
        'crit':logging.CRITICAL
    }


    #def __init__(self, filename=log_file, level=log_level, when='D', backCount=7, fmt='%(asctime)s - %(pathname)s[line:%(lineno)d] - %(levelname)s: %(message)s'):
    def __init__(self, filename, level, when='D', backCount=7, fmt='%(asctime)s - %(levelname)s: %(message)s'):
        self.logger=logging.getLogger(filename)
        if not self.logger.handlers:
            self.logger.setLevel(self.level_relations.get(level))       # 设置日志级别
            format_str=logging.Formatter(fmt)                           # 设置日志格式

            self.fh=handlers.TimedRotatingFileHandler(filename=filename,when=when,backupCount=backCount,encoding='utf-8')
            self.fh.setFormatter(format_str)                                 # 设置文件里写入的格式
            self.logger.addHandler(self.fh)                                  # 把对象加到logger里

    #def __del__(self):
    #3    self.logger.removeHandler(self.fh)

    """
    def __init__(self,filename,level,when='D',backCount=3,fmt='%(asctime)s - %(pathname)s[line:%(lineno)d] - %(levelname)s: %(message)s'):
        self.logger = logging.getLogger(filename)
        format_str = logging.Formatter(fmt)#设置日志格式
        self.logger.setLevel(self.level_relations.get(level))#设置日志级别
        sh = logging.StreamHandler()#往屏幕上输出
        sh.setFormatter(format_str) #设置屏幕上显示的格式
        th = handlers.TimedRotatingFileHandler(filename=filename,when=when,backupCount=backCount,encoding='utf-8')#往文件里写入#指定间隔时间自动生成文件的处理器
        #实例化TimedRotatingFileHandler
        #interval是时间间隔，backupCount是备份文件的个数，如果超过这个个数，就会自动删除，when是间隔的时间单位，单位有以下几种：
        # S 秒
        # M 分
        # H 小时、
        # D 天、
        # W 每星期（interval==0时代表星期一）
        # midnight 每天凌晨
        th.setFormatter(format_str)#设置文件里写入的格式
        self.logger.addHandler(sh) #把对象加到logger里
        self.logger.addHandler(th)


    """
def get_log_args():
    db=database.db()
    sql_log_file="select value from status where section='logs' and option='log_file'"
    sql_log_level="select value from status where section='logs' and option='log_level'"
    log_file=db.query_one(sql_log_file)[0]
    log_level=db.query_one(sql_log_level)[0]
    return (log_file, log_level)

if __name__ == '__main__':
    log = Logger()
    log.logger.debug('debug')
    log.logger.info('info')
    log.logger.warning('警告')
    log.logger.error('报错')
    log.logger.critical('严重')
