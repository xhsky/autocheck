#!/usr/bin/env python
# *-* coding:utf8 *-*
# sky


import smtplib  # 加载smtplib模块
from email.mime.text import MIMEText
from email.utils import formataddr
from email.mime.application import MIMEApplication
from email.mime.image import MIMEImage
from email.mime.multipart import MIMEMultipart
from lib import database, conf
import datetime

import binascii
import requests


def mail_notification(logger, mail_body, sender_alias, receive, subject, msg=None, attachment_file=None):
    db=database.db()
    hostname=conf.get("autocheck", "hostname")[0]
    try:
        """网易企业邮箱, 巨坑....
        1.授权码必须手动指定, 不能自动生成. 代码使用的password为授权码
        2.企业邮箱的smtp是单独的, 不是统一的
        3.登录不能有二次验证(短信等)
        """

        sender="check@dreamdt.cn"
        password="DreamSoft#1dream"
        smtp_server="smtp.dreamdt.cn"
        smtp_port=25

        message=MIMEMultipart('related')
        message['From']=formataddr([sender_alias, sender])
        receive_list=[x.strip() for x in receive.split(",")]
        message['To']=','.join(receive_list)
        message['Subject']=subject

        #mail_body=f"预警信息:\n{mail_body}\n\n详细巡检信息请查看附件."
        #cmd='top -b -n 1 -o %MEM | head -n 15'
        #status, top_msg=subprocess.getstatusoutput(cmd)
        #mail_body=f"主机负载简图:\n{top_msg}\n\n\n{'*'*80}\n\n\n{mail_body}"

        mail_body=f"主机: {hostname}\n{mail_body}"
        message.attach(MIMEText(mail_body, "plain", "utf-8"))

        # 构造附件
        flag=0
        if attachment_file is not None:
            flag=1
            attach=MIMEApplication(open(attachment_file, 'rb').read())
            attach.add_header('Content-Disposition',  'attachment',  filename='资源统计报告.tar.gz')
            message.attach(attach)

        mail_server=smtplib.SMTP(smtp_server, smtp_port)
        mail_server.login(sender, password)             # 登录邮箱
        mail_server.sendmail(sender, receive_list, message.as_string())  # 发送邮件
        mail_server.quit()

        if flag==0:
            logger.logger.info(f"发送{msg}相关预警邮件")
        elif flag==1:
            logger.logger.info(f"发送资源统计邮件")

    except Exception as e:
        logger.logger.error(f"邮件发送失败: {e}")
        msg="发送失败"
        
    record_time=datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    sql="insert into notify values(?, ?, ?, ?)"
    db.update_one(sql, (record_time, "mail", str(receive_list), msg))

def sms_notification(logger, text, to_phone_numbers, subject, msg):
    db=database.db()
    hostname=conf.get("autocheck", "hostname")[0]
    sms_notification_url="http://smartone.10690007.com/proxysms/mt"
    command="MULTI_MT_REQUEST"
    spid=20850
    sppassword="dreamsoft_mcyw"
    spsc="00"
    das=",".join([f"86{x.strip()}" for x in to_phone_numbers.split(",")])
    sign_name="【梦创运维】"
    sa="098"
    dc=8

    text=f"主机({hostname}){text}"
    sm=binascii.hexlify(f"{sign_name} {subject}\n{text}".encode('UTF-16BE'))
    args={
            "command":command, 
            "spid":spid, 
            "sppassword": sppassword, 
            "spsc": spsc, 
            "das": das, 
            "sa": sa, 
            "dc": dc, 
            "sm": sm
            }

    response=requests.post(sms_notification_url, data=args)
    if response.status_code == 200:
        logger.logger.info(f"发送{msg}相关预警短信")
    else:
        logger.logger.error(f"发送{msg}相关预警短信失败")

    record_time=datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    sql="insert into notify values(?, ?, ?, ?)"
    db.update_one(sql, (record_time, "sms", das, msg))

def send(logger, warning_msg, notify_dict, msg):
    if notify_dict["mail"]["check"] == "1":
        mail_notification(logger, warning_msg, notify_dict["mail"]["sender_alias"], notify_dict["mail"]["receive"], notify_dict["mail"]["subject"], msg)
    if notify_dict["sms"]["check"] == "1":
        sms_notification(logger, warning_msg, notify_dict["sms"]["receive"], notify_dict["sms"]["subject"], msg)

        

if __name__ == "__main__":
    #to_phone_numbers=['13162155703', '15107222094', '18621530408']
    to_phone_numbers=['13162155703']
    text="测aaa"
    sms_notification(to_phone_numbers, text)
