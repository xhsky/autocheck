#!/usr/bin/env python
# *-* coding:utf8 *-*
# sky

def printf(message, mail_body=0):
    if mail_body==0:
        with open("./report/check.info", "a", encoding="utf8") as f:
            f.write(f"{message}\n")
    elif mail_body==1:
        with open("./report/warning", "a", encoding="utf8") as f:
            f.write(f"{message}\n")


    
if __name__ == "__main__":
    printf("aaa")
    printf("星期")
    printf("aaa")
