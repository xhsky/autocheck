#!/usr/bin/env python
# *-* coding:utf8 *-*
# sky

import configparser

def get(section, *option):
    config_file=configparser.ConfigParser()
    config_file.read("conf/autocheck.conf")

    option_list=[]
    for i in option:
        if config_file.has_option(section, i):
            value=config_file.get(section, i)
            if value=="":
                option_list.append(None)
            else:
                option_list.append(value)
        else:
            option_list.append(None)

    return option_list

if __name__ == "__main__":
    print(get("redis", "check"))
