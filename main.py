#!/usr/bin/env python3
# *-* coding:utf8 *-*
# sky

import gevent 
from gevent import monkey
monkey.patch_all()
from core import record, analysis, show, clean
from lib import database, log
import os, sys, atexit, time
import configparser
import psutil

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

def config_to_db(config_file):
    """读取配置文件, 将配置写入db
    """
    logger.logger.debug("开始读取配置文件...")
    db=database.db()
    sql="select section, option from status where flag=1"
    config_init=db.query_all(sql)

    cfg=configparser.ConfigParser()
    cfg.read(config_file)

    config_list=[]
    for i in config_init:
        section=i[0]
        option=i[1]
        value=get_config(cfg, section, option)
        config_list.append((value, section, option))

    try:
        logger.logger.debug("将配置文件写入数据库...")
        sql="update status set value=? where section=? and option=?"
        db.update_all(sql, config_list)
        db.close()
    except Exception as e:
        print(f"Error: 配置文件未正常写入数据库({e})")
        exit()

def daemonize(pid_file, rootdir):
    pid = os.fork()
    if pid:
        sys.exit(0)
    os.chdir(rootdir)
    os.umask(0)
    os.setsid()

    _pid = os.fork()
    if _pid:
        sys.exit(0)

    sys.stdout.flush()
    sys.stderr.flush()

    # dup2函数原子化地关闭和复制文件描述符，重定向到/dev/nul，即丢弃所有输入输出
    #with open('/dev/null') as read_null, open('/dev/null', 'w') as write_null:
    with open('/dev/null') as read_null, open('./logs/errors.log', 'a') as write_null:
        os.dup2(read_null.fileno(), sys.stdin.fileno())
        os.dup2(write_null.fileno(), sys.stdout.fileno())
        os.dup2(write_null.fileno(), sys.stderr.fileno())

    # 写入pid文件
    if pid_file:
        with open(pid_file, 'w+') as f:
            pid=os.getpid()
            logger.logger.info(f"Main Pid: {pid}")
            f.write(str(pid))
        atexit.register(os.remove, pid_file)

def main():
    # 初始化. 判断是否存数据文件, 若不存在则初始化; 若存在则正常启动
    data_file="./data/auto.db"
    if os.path.exists(data_file):
        pass
    else:
        init_file="./share/init.sql"
        os.makedirs(os.path.dirname(data_file), exist_ok=True)
        logger.logger.info("开始初始化数据.")

        db=database.db(data_file)
        with open(init_file, "r") as f:
            for sql in f.readlines():
                db.update_one(sql) 
        logger.logger.info("初始化数据完成.")
        """
        try:
            db=database.db(data_file)
            with open(init_file, "r") as f:
                for sql in f.readlines():
                    db.update_one(sql) 
            logger.logger.info("初始化数据完成.")
        except Exception as e:
            print(f"Error: 初始化失败({e})")
            exit()
        """

    config_to_db("./conf/autocheck.conf")
    daemonize('logs/autocheck.pid', rootdir)

    check_item=[record.record, show.show, analysis.analysis, clean.clean]
    gevent_list=[]
    for i in check_item:
        g=gevent.spawn(i, )
        gevent_list.append(g)
    gevent.joinall(gevent_list)

def control(action, pid=None):
    if action=="start":
        if pid is None:
            logger.logger.info("程序启动...")
            print(f"启动程序...")
            main()
        else:
            print(f"程序({pid})正在运行...")
    elif action=="stop":
        if pid is None:
            print(f"程序未运行...")
        else:
            print("程序关闭...")
            logger.logger.info("程序关闭...")
            os.kill(pid, 9)
    elif action=="status":
        if pid is None:
            print("程序未运行...")
        else:
            print(f"程序({pid})正在运行...")
    elif action=="clean":
        if pid is not None:
            print("程序关闭...")
            logger.logger.info("程序关闭...")
            os.kill(pid, 9)
        try:
            log_dir=os.path.dirname(log_file)
            for i in os.listdir(log_dir):
                os.remove(f"{log_dir}/{i}")

            data_file="./data/auto.db"
            if os.path.exists(data_file):
                os.remove(data_file)
            logger.logger.info("Clean...")
            print("Clean...")
        except Exception as e:
            print(f"Clean Error: {e}")

def usage(action):
    pid=get_pid("./logs/autocheck.pid")
    if action=="usage":
        print(f"Usage: {sys.argv[0]} start|stop|restart|status|sendmail")
    elif action=="start":
        control("start", pid)
    elif action=="restart":
        control("stop", pid)
        time.sleep(1)
        control("start", None)
    elif action=="stop":
        control("stop", pid)
    elif action=="status":
        control("status", pid)
    elif action=="sendmail":
        pass
    elif action=="clean":
        control("clean", pid)
    else:
        usage("usage")

def get_pid(pid_file):
    if os.path.exists(pid_file):
        with open(pid_file, "r", encoding="utf8") as f:
            pid=f.read()
            if pid != '':
                pid=int(pid)
                if psutil.pid_exists(pid):
                    cmdline=",".join(psutil.Process(pid).cmdline())
                    if "python" in cmdline and "main.py" in cmdline:
                        return pid
    return None

if __name__ == "__main__":
    if len(sys.argv)==2:
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
        action=sys.argv[1]
        usage(action)
    else:
        usage("usage")

