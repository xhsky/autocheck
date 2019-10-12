#!/usr/bin/env python
# *-* coding:utf8 *-*
# sky

import os

def printf(message):
    os.makedirs("report", exist_ok=True)
    with open("./report/check.info", "a", encoding="utf8") as f:
        f.write(f"{message}\n")

    
if __name__ == "__main__":
    printf("aaa")
    printf("星期")
    printf("aaa")
