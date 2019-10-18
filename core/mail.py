#!/usr/bin/env python
# *-* coding:utf8 *-*
# sky

import smtplib  # 加载smtplib模块
from email.mime.text import MIMEText
from email.utils import formataddr
from email.mime.application import MIMEApplication
from email.mime.image import MIMEImage
from email.mime.multipart import MIMEMultipart

from lib import conf
import datetime, os
import subprocess

def send():
    check, sender_alias, receive, subject=conf.get("mail", 
            "check", 
            "sender", 
            "receive", 
            "subject"
            )

    if check=="1":
        try:
            """网易企业邮箱, 巨坑....
            1.授权码必须手动指定, 不能自动生成
            2.企业邮箱的smtp是单独的, 不是统一的
            3.登录不能有二次验证(短信等)
            """

            sender="check@dreamdt.cn"
            password="DreamSoft#1dream"
            smtp_server="smtp.dreamdt.cn"
            smtp_port=25

            message=MIMEMultipart('related')
            message['From']=formataddr([sender_alias, sender])
            receive_list=[]
            for i in receive.split(","):
                receive_list.append(i.strip())
            message['To']=','.join(receive_list)

            subject=f"{subject}-{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            message['Subject']=subject

            warning_file="./report/warning"
            if os.path.exists(warning_file):
                with open(warning_file, "r") as f:
                    mail_body=f.read()
            else:
                mail_body="今天无预警内容"

            mail_body=f"预警信息:\n{mail_body}\n\n详细巡检信息请查看附件."
            cmd='top -b -n 1 -o %MEM | head -n 15'
            status, top_msg=subprocess.getstatusoutput(cmd)
            mail_body=f"主机负载简图:\n{top_msg}\n\n\n{'*'*80}\n\n\n{mail_body}"

            message.attach(MIMEText(mail_body, "plain", "utf-8"))

            all_file=os.listdir(".")    # 获取附件文件名称
            for i in all_file:
                if i.startswith("report") and i.endswith("tar.gz"):
                    attachment_file=i
                    break

            # 构造附件
            attach=MIMEApplication(open(attachment_file, 'rb').read())
            attach.add_header('Content-Disposition',  'attachment',  filename='巡检报告.tar.gz')
            message.attach(attach)

            mail_server=smtplib.SMTP(smtp_server, smtp_port)
            mail_server.login(sender, password)             # 登录邮箱
            mail_server.sendmail(sender, receive_list, message.as_string())  # 发送邮件
            mail_server.quit()
        except Exception as e:
            print(f"发送失败: {e}")
    
if __name__ == "__main__":
    main()
