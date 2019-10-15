#!/usr/bin/env python
# *-* coding:utf8 *-*
# sky


def format_size(byte):
    byte=float(byte)
    kb=byte/1024

    if kb >= 1024:
        mb=kb/1024
        if mb>=1024:
            gb=mb/1024
            return f"{gb:.2f}G"
        else:
            return f"{mb:.2f}M"
    else:
        return f"{kb:.2f}k"
            
if __name__ == "__main__":
    main()
