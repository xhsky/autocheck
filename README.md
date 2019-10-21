# autocheck
1. 当前项目用于单机自动巡检
2. 可巡检主机资源(cpu, 内存, 磁盘容量)
3. 可巡检多个Tomcat(Pid, 启动时间, 内存占用, 连接数, 线程数, 启动参数, jvm内存回收情况)
4. 可巡检Redis(Pid, 启动时间, 连接数, 数据内存, 进程内存, 集群信息, 自定义命令查询, sentinel监控信息)
5. 可巡检MySQL(Pid, 启动时间, 内存占用, 连接数, 慢日志信息, 主从信息)
6. 可巡检Oracle表空间信息及生成awr文件
7. 可巡检备份情况
8. 可定时自动巡检
9. 可将巡检报告邮件发送指定收件人

## 安装(Centos7)
- 安装Python3环境和开发工具
```
# yum install python3 python3-devel git -y
```

- 下载autocheck
```
# mkdir -p /soft/
# cd /soft/
# git clone https://github.com/xhsky/autocheck.git
```

- 下载依赖包
```
# cd /soft/autocheck
# pip3 install -r whl/requirements.txt
```

## 使用
- 进入autocheck目录, 并编辑conf/autocheck.conf配置文件以定义巡检项目
  - 配置文件中`#`是注释符号, 注释必须单独占一行, 不能写到配置项后面
  - 只有当前主机安装了软件, 该软件下的check才可置为1

```
# cd autocheck
# vim conf/autocheck.conf
  [autocheck]                                                                                                                                                                   
  # 定义巡检主机的主机名                                                                                                                                                        
  hostname=dream                                                                                                                                                                
  # 指定Python可执行文件的地址                                                                                                                                                  
  python_bin=/usr/bin/python3                                                                                                                                                   
                                                                                                                                                                                
  # 保留                                                                                                                                                                        
  [host]                                                                                                                                                                        
                                                                                                                                                                                
  [tomcat]                                                                                                                                                                      
  # 是否巡检Tomcat, 默认巡检:1, 否则:0                                                                                                                                          
  check=1                                                                                                                                                                       
  # 指定Tomcat的安装目录, 多个Tomcat以逗号分隔                                                                                                                                  
  tomcat_home=/data/tomcat, /data/tomcat1                                                                                                                                       
  # 指定jdk的安装目录                                                                                                                                                           
  java_home=/data/jdk                                                                                                                                                           
  # jstat命令持续时间, 单位秒                                                                                                                                                   
  jstat_duration=20                                                                                                                                                             
                                                                                                                                                                                
  [redis]                                                                                                                                                                       
  # 是否巡检redis, 默认巡检:1, 否则:0                                                                                                                                           
  check=1                                                                                                                                                                       
  # redis的密码                                                                                                                                                                 
  password=xxxxxxxxxxxx
  # redis端口                                                                                                                                                                   
  redis_port=6378                                                                                                                                                               
  # 若未安装sentinel, 则注释掉下面两项                                                                                                                                          
  # sentinel端口                                                                                                                                                                
  sentinel_port=26379                                                                                                                                                           
  # sentinel监控的集群名称                                                                                                                                                      
  sentinel_name=mymaster                                                                                                                                                        
  # 自定义简单redis执行命令, 以,分隔.
  commands=llen ds_list, llen ds_list_EXCEPTION
  
  [mysql]
  # 是否巡检MySQL, 默认巡检:1, 否则:0
  check=1                                                                                                                                                                       
  # 指定MySQL用户, 用户当前只能是root                                                                                                                                           
  mysql_user=root                                                                                                                                                               
  # 指定MySQL主机, 主机当前只能是127                                                                                                                                            
  mysql_ip=127.0.0.1                                                                                                                                                            
  # 指定MySQL端口                                                                                                                                                               
  mysql_port=3306
  # 指定MySQL密码
  mysql_password=xxxxxx
  
  [oracle]
  # 是否巡检Oracle
  check=1
  # Oracle SID
  oracle_sid=orcl
  # 生成前N个小时的awr报告
  awr_hours=5

  [backup]
  # 是否启用备份巡检,  用于查看备份文件状态
  check=1
  # 指定备份文件的目录. 可设置多个目录, 以, 分隔
  dir=/data1,  /data2
  
  [timing]
  # 是否启用定时巡检功能
  check=1
  # 示例为每天凌晨3点0分巡检
  minute=0
  hour=3
  day=*
  month=*
  week=*
  
  [mail]
  # 是否自动将巡检报告发送邮件
  check=1
  # 发送者的邮箱地址
  sender=xxx1@163.com
  # 发送者的别名
  sender_alias=xxx
  # 发送者的授权码, 可查看https://jingyan.baidu.com/article/adc815139f60c2f723bf7385.html教程设置smtp并开启授权码                                                              
  password=xxxxxx
  # SMTP服务器
  smtp_server=smtp.163.com
  # 收件人的邮箱地址(多个邮箱以,分隔, 必须有发送者的邮箱以免被系统屏蔽)
  receive=xxx1@163.com, xxx2@dreamdt.cn
  # 邮件标题
  subject=**项目巡检
```

- 配置完成后执行main.py文件
```
# ./main.py
```
- 执行时间根据巡检项目的数量而定,执行完毕后没有任何输出即为成功. 巡检报告在report目录下的check.info文件. 
若配置了邮件发送, 则会将当前目录下的以report开头的压缩文件(eg: report-201910150917.tar.gz)发送给收件人

## 巡检报告示例:
### warning:
```
磁盘空间正常.
内存空间正常.
Tomcat信息:
Tomcat(8080):
YGC回收正常.
FGC回收正常.
Tomcat(8081):
YGC回收正常.
FGC回收正常.
Tomcat(8082):
检查该Tomcat(8082)是否启动
Redis信息:
slave(127.0.0.1:6379)连接正常.
Sentinel信息:
master ip: 127.0.0.1:6379
slave ip: 127.0.0.1:6378
备份信息:
备份(/data)下未生成今天的备份.
备份(/data2)正常.
```

### check.info
```
开始巡检时间: 2019-10-15 09:17:11                                                                                                                                            
巡检主机: dream                                                                                                                                                              
********************************************************************************                                                                                             
服务器启动时间: 2019-10-12 13:09:33                                                                                                                                          
--------------------------------------------------------------------------------                                                                                             
磁盘信息:
磁盘            大小(G)  已使用(G) 可用(G)  挂载点
/dev/sda2       53.97    14.92     39.05    /
/dev/sda1       1.99     0.15      1.84     /boot
--------------------------------------------------------------------------------
CPU信息:                                                                                                                                                                     
cpu逻辑核心数: 8
cpu当前利用率(%): 3.7                                                                                                                                                        
--------------------------------------------------------------------------------
内存信息:                                                                                                                                                                    
总内存(total): 15.55G
可用内存(available): 11.44G                                                                                                                                                  
已用内存(used): 3.24G/26.4%
空闲内存(free): 8.36G                                                                                                                                                        
--------------------------------------------------------------------------------
swap信息:                                                                                                                                                                    
总swap(total): 3.73G
已使用(used): 0.00k/0.0%
未使用(free): 3.73G
--------------------------------------------------------------------------------
Tomcat信息:
Tomcat(8080):
Tomcat Pid: 84
程序启动时间: 2019-10-21 01:59:12
内存占用: 218.15M/1.37%
连接数: 3
线程数: 647
启动参数: ['/data/jdk/bin/java', '-Djava.util.logging.config.file=/data/tomcat/conf/logging.properties', '-Djava.util.logging.manager=org.apache.juli.ClassLoaderLogManager', 
'-server', '-XX:+AggressiveOpts', '-XX:+UseBiasedLocking', '-XX:+DisableExplicitGC', '-XX:+UseConcMarkSweepGC', '-XX:+UseParNewGC', '-XX:+CMSParallelRemarkEnabled', '-XX:+Use
FastAccessorMethods', '-XX:+UseCMSInitiatingOccupancyOnly', '-Djava.security.egd=file:/dev/./urandom', '-Djava.awt.headless=true', '-Xms8092M', '-Xmx8092M', '-Xss512k', '-XX:
LargePageSizeInBytes=128M', '-XX:MaxTenuringThreshold=11', '-XX:MetaspaceSize=200m', '-XX:MaxMetaspaceSize=256m', '-XX:MaxNewSize=256m', '-Djdk.tls.ephemeralDHKeySize=2048', 
'-Djava.protocol.handler.pkgs=org.apache.catalina.webresources', '-Dorg.apache.catalina.security.SecurityListener.UMASK=0027', '-Dignore.endorsed.dirs=', '-classpath', '/data
/tomcat//bin/bootstrap.jar:/data/tomcat/bin/tomcat-juli.jar', '-Dcatalina.base=/data/tomcat', '-Dcatalina.home=/data/tomcat/', '-Djava.io.tmpdir=/data/tomcat/temp', 'org.apac
he.catalina.startup.Bootstrap', 'start']                                                                                                                                      
内存回收:
  S0     S1     E      O      M     CCS    YGC     YGCT    FGC    FGCT     GCT
  0.00  46.37  44.13   0.00  96.79  88.93      1    0.024     0    0.000    0.024
  0.00  46.37  44.13   0.00  96.79  88.93      1    0.024     0    0.000    0.024
  0.00  46.37  44.13   0.00  96.79  88.93      1    0.024     0    0.000    0.024
  0.00  46.37  44.13   0.00  96.79  88.93      1    0.024     0    0.000    0.024
  0.00  46.37  44.13   0.00  96.79  88.93      1    0.024     0    0.000    0.024
  0.00  46.37  44.13   0.00  96.79  88.93      1    0.024     0    0.000    0.024
  0.00  46.37  44.13   0.00  96.79  88.93      1    0.024     0    0.000    0.024
  0.00  46.37  44.13   0.00  96.79  88.93      1    0.024     0    0.000    0.024
  0.00  46.37  44.13   0.00  96.79  88.93      1    0.024     0    0.000    0.024
  0.00  46.37  44.13   0.00  96.79  88.93      1    0.024     0    0.000    0.024
  0.00  46.37  44.13   0.00  96.79  88.93      1    0.024     0    0.000    0.024
  0.00  46.37  44.13   0.00  96.79  88.93      1    0.024     0    0.000    0.024
  0.00  46.37  44.13   0.00  96.79  88.93      1    0.024     0    0.000    0.024
  0.00  46.37  44.13   0.00  96.79  88.93      1    0.024     0    0.000    0.024
  0.00  46.37  44.13   0.00  96.79  88.93      1    0.024     0    0.000    0.024
  0.00  46.37  44.13   0.00  96.79  88.93      1    0.024     0    0.000    0.024
----------------------------------------                                                                                                                                      
Tomcat(8081):                                                                                                                                                                 
Tomcat Pid: 745                                                                                                                                                               
程序启动时间: 2019-10-21 01:59:22                                                                                                                                             
内存占用: 199.76M/1.25%                                                                                                                                                       
连接数: 3                                                                                                                                                                     
线程数: 447
启动参数: ['/data/jdk/bin/java', '-Djava.util.logging.config.file=/data/tomcat1/conf/logging.properties', '-Djava.util.logging.manager=org.apache.juli.ClassLoaderLogManager',
 '-server', '-XX:+AggressiveOpts', '-XX:+UseBiasedLocking', '-XX:+DisableExplicitGC', '-XX:+UseConcMarkSweepGC', '-XX:+UseParNewGC', '-XX:+CMSParallelRemarkEnabled', '-XX:+Us
eFastAccessorMethods', '-XX:+UseCMSInitiatingOccupancyOnly', '-Djava.security.egd=file:/dev/./urandom', '-Djava.awt.headless=true', '-Xms8092M', '-Xmx8092M', '-Xss512k', '-XX
:LargePageSizeInBytes=128M', '-XX:MaxTenuringThreshold=11', '-XX:MetaspaceSize=200m', '-XX:MaxMetaspaceSize=256m', '-XX:MaxNewSize=256m', '-Djdk.tls.ephemeralDHKeySize=2048',
 '-Djava.protocol.handler.pkgs=org.apache.catalina.webresources', '-Dorg.apache.catalina.security.SecurityListener.UMASK=0027', '-Dignore.endorsed.dirs=', '-classpath', '/dat
a/tomcat1/bin/bootstrap.jar:/data/tomcat1/bin/tomcat-juli.jar', '-Dcatalina.base=/data/tomcat1', '-Dcatalina.home=/data/tomcat1', '-Djava.io.tmpdir=/data/tomcat1/temp', 'org.
apache.catalina.startup.Bootstrap', 'start']
内存回收:
  S0     S1     E      O      M     CCS    YGC     YGCT    FGC    FGCT     GCT
  0.00  46.63  33.71   0.00  96.73  88.88      1    0.024     0    0.000    0.024
  0.00  46.63  33.71   0.00  96.73  88.88      1    0.024     0    0.000    0.024
  0.00  46.63  33.71   0.00  96.73  88.88      1    0.024     0    0.000    0.024
  0.00  46.63  33.71   0.00  96.73  88.88      1    0.024     0    0.000    0.024
  0.00  46.63  33.71   0.00  96.73  88.88      1    0.024     0    0.000    0.024
  0.00  46.63  33.71   0.00  96.73  88.88      1    0.024     0    0.000    0.024
  0.00  46.63  33.71   0.00  96.73  88.88      1    0.024     0    0.000    0.024
  0.00  46.63  34.71   0.00  96.73  88.88      1    0.024     0    0.000    0.024
  0.00  46.63  34.71   0.00  96.73  88.88      1    0.024     0    0.000    0.024
  0.00  46.63  34.71   0.00  96.73  88.88      1    0.024     0    0.000    0.024
  0.00  46.63  34.71   0.00  96.73  88.88      1    0.024     0    0.000    0.024
  0.00  46.63  34.71   0.00  96.73  88.88      1    0.024     0    0.000    0.024
  0.00  46.63  34.71   0.00  96.73  88.88      1    0.024     0    0.000    0.024
  0.00  46.63  34.71   0.00  96.73  88.88      1    0.024     0    0.000    0.024
  0.00  46.63  34.71   0.00  96.73  88.88      1    0.024     0    0.000    0.024
  0.00  46.63  34.71   0.00  96.73  88.88      1    0.024     0    0.000    0.024
----------------------------------------
--------------------------------------------------------------------------------
Redis信息:
Redis Pid: 1305
启动时间: 2019-10-15 02:45:22
连接数: 4
数据内存: 1.88M
进程内存: 4.43M
----------------------------------------
集群信息:
角色: slave
master信息: ip: 127.0.0.1:6379, state: up
----------------------------------------
自定义命令查询:
llen ds_list 结果: 2
llen ds_list_EXCEPTION 结果: 4
----------------------------------------
Sentinel信息:
master ip: 127.0.0.1:6379
slave ip: 127.0.0.1:6378
--------------------------------------------------------------------------------
MySQL信息:                                                                                                                                                                    
MySQL Pid: 20450                                                                                                                                                              
程序启动时间: 2019-10-15 10:18:25                                                                                                                                             
内存占用(%): 10.02                                                                                                                                                            
连接数: 1                                                                                                                                                                     
----------------------------------------                                                                                                                                      
慢日志信息:                                                                                                                                                                   
24小时内的慢日志.                                                                                                                                                                 
SQL: select sleep(3)
开始执行时间: 2019-10-15 10:19:05.408145
查询时间: 0:00:03.000814
锁表时间: 0:00:00
扫描的行数: 0
****************************************
SQL: select sleep(4)
开始执行时间: 2019-10-15 10:19:11.921078
查询时间: 0:00:04.000679
锁表时间: 0:00:00
扫描的行数: 0
****************************************
SQL: select sleep(5)
开始执行时间: 2019-10-15 10:19:19.260634
查询时间: 0:00:05.000713
锁表时间: 0:00:00
扫描的行数: 0
****************************************
----------------------------------------
主从信息:
角色: slave
Master IP: db1:3306
同步的数据库: db,db2
Slave IO线程是否开启: Yes
Slave IO线程状态: Waiting for master to send event
Slave SQL线程是否开启: Yes
Slave SQL线程状态: Slave has read all relay log; waiting for more updates
Master UUID: 5dfb2403-e102-11e9-9cb1-080027e11725
已接收的GTID集合: 5dfb2403-e102-11e9-9cb1-080027e11725:1-20
已执行的GTID集合: 5dbb9a6a-e102-11e9-810e-080027722592:1-5,  5dfb2403-e102-11e9-9cb1-080027e11725:1-20
Slave落后Master的时间(秒): 0
----------------------------------------
--------------------------------------------------------------------------------
备份信息:
/data2目录下信息:
文件名: backup.tar.gz,  大小: 11.09M,  创建时间: 2019-10-15 06:35:01
文件名: backup4.tar.gz,  大小: 11.09M,  创建时间: 2019-10-15 06:35:15
文件名: backup2.tar.gz,  大小: 11.09M,  创建时间: 2019-10-15 06:35:08
文件名: backup1.tar.gz,  大小: 11.09M,  创建时间: 2019-10-15 06:35:18
文件名: backup3.tar.gz,  大小: 11.09M,  创建时间: 2019-10-15 06:35:11
----------------------------------------
--------------------------------------------------------------------------------
Oracle信息:
表空间信息:
表空间名称    表空间大小(M)    已使用表空间(M)    未使用表空间(M)    使用率(%)
SYSTEM        750.00           744.38              5.62              99.25   
SYSAUX        590.00           560.94              29.06             95.07   
USERS         5.00             1.38                3.62              27.50   
UNDOTBS1      90.00            17.31               72.69             19.24   
----------------------------------------
awr信息:
请查看awr.html文件
********************************************************************************
结束巡检时间: 2019-10-15 09:23:36
```
