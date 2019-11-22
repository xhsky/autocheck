create table if not exists status(section varchar(12) not null, option varchar(24) not null, value varchar(1024) default null, flag tinyint default 0, primary key(section, option));
insert into status values('autocheck', 'hostname', 'dream', 1);
insert into status values('autocheck', 'warning_percent', '95', 1);
insert into status values('autocheck', 'warning_interval', '30', 1);
insert into status values('host', 'disk_interval', '60', 1);
insert into status values('host', 'cpu_interval', '30', 1);
insert into status values('host', 'memory_interval', '30', 1);
insert into status values('host', 'swap_interval', '360', 1);
insert into status values('host', 'boot_time_interval', '360', 1);
insert into status values('logs', 'log_file', './logs/autocheck.log', 1);
insert into status values('logs', 'log_level', 'info', 1);
insert into status values('tomcat', 'check', 0, 1);
insert into status values('tomcat', 'tomcat_interval', "30", 1);
insert into status values('tomcat', 'tomcat_port', null, 1);
--insert into status values('tomcat', 'ygc_time', 1, 0);
--insert into status values('tomcat', 'fgc_time', 10, 0);
--insert into status values('tomcat', 'java_home', null, 1);
--insert into status values('tomcat', 'jstat_duration', null, 1);
insert into status values('redis', 'check', 0, 1);
insert into status values('redis', 'redis_interval', '30', 1);
insert into status values('redis', 'password', null, 1);
insert into status values('redis', 'hostname', '127.0.0.1', 0);
insert into status values('redis', 'redis_port', null, 1);
insert into status values('redis', 'sentinel_port', null, 1);
insert into status values('redis', 'sentinel_name', null, 1);
insert into status values('redis', 'commands', null, 1);
insert into status values('mysql', 'check', 0, 1);
insert into status values('mysql', 'mysql_interval', '30', 1);
insert into status values('mysql', 'mysql_user', 'root', 0);
insert into status values('mysql', 'mysql_ip', '127.0.0.1', 0);
insert into status values('mysql', 'mysql_port', null, 1);
insert into status values('mysql', 'mysql_password', null, 1);
insert into status values('mysql', 'seconds_behind_master', 5, 1);
insert into status values('oracle', 'check', 0, 1);
insert into status values('oracle', 'oracle_interval', 1, 1);
insert into status values('oracle', 'awr_hours', null, 1);
insert into status values('backup', 'check', 0, 1);
insert into status values('backup', 'dir', null, 1);
insert into status values('backup', 'regular', null, 1);
insert into status values('backup', 'cron_time', null, 1);
insert into status values('send', 'check', 0, 1);
insert into status values('send', 'send_time', null, 1);
insert into status values('send', 'granularity_level', 10, 1);
insert into status values('mail', 'sender', null, 1);
insert into status values('mail', 'receive', null, 1);
insert into status values('mail', 'subject', null, 1);

-- 报错信息表
create table if not exists error(record_time text not null, section varchar(1024), value varchar(1024), error_msg text, debug tinyint, primary key(record_time, section))
create table if not exists warning_record(record_time text not null, section varchar(1024), value varchar(1024), debug boolean)

--主机资源
create table if not exists disk(record_time text not null, name varchar(1024), total int, used int, used_percent int, avail int, mounted varchar(521), primary key(record_time, name, mounted));
create table if not exists cpu(record_time text not null primary key, cpu_count int, cpu_used_percent int);
create table if not exists memory(record_time text not null primary key, total int, avail int, used int, used_percent int, free int);
create table if not exists swap(record_time text not null primary key, total int, used int, used_percent int, free int);
create table if not exists boot_time(record_time text not null primary key, boot_time text);

-- tomcat
create table if not exists tomcat_constant(record_time text not null, pid int, port int, boot_time text default null, cmdline text default null, primary key(record_time, port));
create table if not exists tomcat_variable(record_time text not null, pid int, port int, men_used int default null, mem_used_percent int default null, connections int default null, threads_num int default null, primary key(record_time, pid));
create table if not exists tomcat_jstat8(record_time text not null, port int, S0 float, S1 float, E float, O float, M float, CCS float, YGC int, YGCT float, FGC int, FGCT float, GCT float, primary key(record_time, port));
create table if not exists tomcat_jstat7(record_time text not null, port int, S0 float, S1 float, E float, O float, P float, YGC int, YGCT float, FGC int, FGCT float, GCT float, primary key(record_time, port));
create table if not exists tomcat_java_version(version varchar(12));
insert into tomcat_java_version values('8');

-- redis
create table if not exists redis_constant(record_time text not null, pid int, port int, boot_time text default null, primary key(record_time, pid));
create table if not exists redis_variable(record_time text not null, pid int, mem_used float, mem_used_percent float, connections int, threads_num int, primary key(record_time, pid))
create table if not exists redis_master(record_time text not null, pid int, role varchar(10), connected_slave int, primary key(pid))
create table if not exists redis_slaves_info(record_time text, slave_ip varchar(15), slave_port int, slave_state varchar(10), primary key(slave_ip, slave_port))
create table if not exists redis_slave(record_time text, pid int, role varchar(10), master_host varchar(15), master_port int, master_link_status varchar(10), primary key(pid))
create table if not exists redis_role(record_time text, role varchar(12));
insert into redis_role values("Null", "master");

-- sentinel
create table if not exists redis_sentinel(record_time text, role varchar(10), host varchar(15), port int, primary key(role, host, port))

-- backup
create table if not exists backup(record_time text, directory varchar(512), filename varchar(512), size float, ctime text, primary key(directory, filename))

-- mysql
create table if not exists mysql_constant(record_time text not null, pid int, port int, boot_time text default null, primary key(record_time, pid));
create table if not exists mysql_variable(record_time text not null, pid int, mem_used float, mem_used_percent float, connections int, threads_num int, primary key(record_time, pid))
create table if not exists mysql_master(record_time text not null, pid int, slave_num int, binlog_do_db varchar(1024), binlog_ignore_db varchar(1024), primary key(record_time))
create table if not exists mysql_slave(record_time text not null, pid int, master_host varchar(15), master_port int, replicate_do_db varchar(1024), replicate_ignore_db varchar(1024), slave_io_thread text, slave_io_state text, slave_sql_thread text, slave_sql_state text, master_uuid varchar(64), retrieved_gtid_set text, executed_gtid_set text, seconds_behind_master int, primary key(record_time, master_host))
create table if not exists mysql_role(record_time text, role varchar(12));
insert into mysql_role values("Null", "master");


-- oracle
create table if not exists oracle(record_time text not null, tablespace_name, size float, used float, used_percent float, free float, primary key(record_time, tablespace_name))

-- mail
create table if not exists mail(record_time text not null, sender, receive, msg);




