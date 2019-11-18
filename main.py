#!/usr/bin/env python3
# *-* coding:utf8 *-*
# sky

#from core import host, tomcat, redis, mysql, mail, timing, oracle, backup
#from lib import conf
#import os, datetime, tarfile, sys
#import socket, shutil

from core import record as rec
from lib import database, log
import os, sys
import gevent                                                                                                                                                                 
from gevent import monkey
import configparser

def record():
    rec.record()

def show():
    pass

def analysis():
    pass

def get_config(cfg, section, option):
    """读取配置文件, 返回value
    """
    if cfg.has_option(section, option):
        value=cfg.get(section, option)
        if value=="":
            return None
        else:
            return value
    else:
        return None

def config_to_db():
    """读取配置文件, 将配置写入db
    """
    logger.logger.debug("开始读取配置文件...")
    db=database.db()
    sql="select section, option from status where flag=1"
    config_init=db.query_all(sql)

    cfg=configparser.ConfigParser()
    cfg.read("./conf/autocheck.conf")

    config_list=[]
    for i in config_init:
        section=i[0]
        option=i[1]
        value=get_config(cfg, section, option)
        config_list.append((value, section, option))

    logger.logger.debug("将配置文件写入数据库...")
    sql="update status set value=? where section=? and option=?"
    db.update_all(sql, config_list)
    db.close()

def main():
    record()
    check_item=[show, analysis]
    gevent_list=[]
    for i in check_item:
        g=gevent.spawn(i, )
        gevent_list.append(g)
    gevent.joinall(gevent_list)

    """
    os.makedirs("report",  exist_ok=True)
    printf(f"开始巡检时间: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    hostname=conf.get("autocheck", "hostname")[0]
    if hostname is None:
        hostname=socket.gethostname()
    printf(f"巡检主机: {hostname}")
    printf("*"*80)

    host.info()
    printf("-"*80)
    tomcat.stats()
    redis.stats()
    mysql.stats()
    backup.cat()
    oracle.info()

    printf("*"*80)
    printf(f"结束巡检时间: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    # 巡检报告打包
    report_files=os.listdir(".")
    for report_file in report_files:
        if report_file.startswith("report") and report_file.endswith("tar.gz"):
            os.remove(report_file)
    with tarfile.open(f"report-{datetime.datetime.now().strftime('%Y%m%d%H%M')}.tar.gz", "w:gz") as tar:
        tar.add("./report")

    mail.send()
    timing.timing()
    """

def control(action):
    if action=="start":
        pass
    elif action=="stop":
        pass

def usage(action):
    if action=="usage":
        print(f"Usage: {sys.argv[0]} start|stop|restart|status|sendmail")
    elif action=="start":
        pid=get_pid()
        if pid is None:
            control("start")
        else:
            pass
    elif action=="restart":
        control("stop")
        control("start")
    elif action=="stop":
        control("stop")
    elif action=="sendmail":
        pass
    else:
        usage()

def get_pid():
    pid_file="./logs/autocheck.pid"
    if os.path.exists(pid_file):
        with open(pid_file, "r", encoding="utf8") as f:
            pid=int(f.read())
        if psutil.pid_exists(pid):
            return pid
    return None

def init():
    """数据初始化
    """
    os.makedirs("./data", exist_ok=True)
    data_file='data/auto.db'
    data_init_file='share/init.sql'
    if os.path.exists(data_file):
        pass
    else:
        logger.logger.info("开始初始化数据.")
        db=database.db(data_file)
        with open(data_init_file, "r") as f:
            for sql in f.readlines():
                db.update_one(sql)
        logger.logger.info("初始化数据完成.")

if __name__ == "__main__":
    if len(sys.argv)==2:
        action=sys.argv[1]
    else:
        usage("usage")
        exit()

    monkey.patch_all()
    rootdir=os.path.dirname(__file__)
    os.chdir(rootdir)

    cfg=configparser.ConfigParser()
    cfg.read("./conf/autocheck.conf")
    os.makedirs("./logs", exist_ok=True)
    log_file=get_config(cfg, "logs", "log_file")
    log_level=get_config(cfg, "logs", "log_level")
    try:
        logger=log.Logger(log_file, log_level)
    except Exception as e:
        print(f"Error: {e}")
        exit()

    logger.logger.info("程序启动...")
    init()
    config_to_db()

    #shutil.rmtree("./report/", ignore_errors=True)
    main()


