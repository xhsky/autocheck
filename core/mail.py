#!/usr/bin/env python
# *-* coding:utf8 *-*
# sky

"""
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.header import Header
"""
import smtplib  # 加载smtplib模块
from email.mime.text import MIMEText
from email.utils import formataddr
from email.mime.application import MIMEApplication
from email.mime.image import MIMEImage
from email.mime.multipart import MIMEMultipart

from lib import conf
import datetime, os

def send():
    check, sender, sender_alias, password, receive, smtp_server, subject=conf.get("mail", 
            "check", 
            "sender", 
            "sender_alias", 
            "password", 
            "receive", 
            "smtp_server", 
            "subject"
            )

    if check=="1":
        try:
            message=MIMEMultipart('related')
            message['From']=formataddr([sender_alias, sender])
            receive_list=[]
            for i in receive.split(","):
                receive_list.append(i.strip())
            message['To']=','.join(receive_list)
            subject=f"{subject}-{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            message['Subject']=subject
            #message.attach(MIMEText("测试", "plain", "utf-8"))

            all_file=os.listdir(".")    # 获取附件文件名称
            for i in all_file:
                if i.startswith("report") and i.endswith("tar.gz"):
                    attachment_file=i
                    break

            # 构造附件
            attach=MIMEApplication(open(attachment_file, 'rb').read())
            attach.add_header('Content-Disposition',  'attachment',  filename='巡检报告.tar.gz')
            message.attach(attach)

            mail_server=smtplib.SMTP(smtp_server, 25)
            mail_server.login(sender, password)             # 登录邮箱
            mail_server.sendmail(sender, receive_list, message.as_string())  # 发送邮件
            mail_server.quit()
        except Exception as e:
            print(f"发送失败: {e}")
    
if __name__ == "__main__":
    main()
