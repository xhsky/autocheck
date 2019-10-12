#!/usr/bin/env python
# *-* coding:utf8 *-*
# sky

def printf(message):
    with open("./check.info", "a", encoding="utf8") as f:
        f.write(f"{message}\n")

    

    
if __name__ == "__main__":
    printf("aaa")
    printf("星期")
    printf("aaa")
