#!/usr/bin/env python
# *-* coding:utf8 *-*
# sky

from lib import conf
def timing():
    check, minute, hour, day, month, week=conf.get("timing", 
            "check", 
            "minute", 
            "hour", 
            "day", 
            "week"
            )
    
    if check=="1":
        python_bin=conf.get("autocheck", "python_bin")[0]
        os.dirname()

    
if __name__ == "__main__":
    main()
