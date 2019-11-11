#!/usr/bin/env python
# *-* coding:utf8 *-*
# sky

#import prettytable as pt
from prettytable import PrettyTable
from 
def main1():
    # tb = pt.PrettyTable( ["City name", "Area", "Population", "Annual Rainfall"])
    tb = pt.PrettyTable()
    tb.field_names = ["City name", "Area", "Population", "Annual Rainfall"]
    tb.add_row(["Adelaide",1295, 1158259, 600.5])
    tb.add_row(["Brisbane",5905, 1857594, 1146.4])
    tb.add_row(["Darwin", 112, 120900, 1714.7])
    tb.add_row(["Hobart", 1357, 205556,619.5])
    print(tb)
def main2():
    x = PrettyTable(["City name",  "Area",  "Population",  "Annual Rainfall"])
    x.align["City name"] = "r" # Left align city names 
    x.padding_width = 3 # One space between column edges and contents (default) 
    x.add_row(("Adelaide", 1295,  1158259,  600.5)) 
    x.add_row(["Brisba3e", 5905,  1857594,  1146.4]) 
    x.add_row(["Darwin",  112,  120900,  1714.7]) 
    x.add_row(["Hobart",  1357,  205556,  619.5]) 
    x.add_row(["Sydney",  2058,  4336374,  1214.8]) 
    x.add_row(["Melbourne",  1566,  3806092,  646.9]) 
    x.add_row(["Perth",  5386,  1554769,  869.4])
    print(x)
def main():
    x = PrettyTable()
    x.add_column("City name", ["Adelaide", "Brisbane", "Darwin", "Hobart", "Sydney", "Melbourne", "Perth"]) 
    x.add_column("Area",  [1295,  5905,  112,  1357,  2058,  1566, 55]) 
    x.add_column("Population",  [1158259,  1857594,  120900,  205556,  4336374,  3806092,  1554769]) 
    x.add_column("Annual Rainfall", [600.5,  1146.4,  1714.7,  619.5,  1214.8,  646.9,  869.4])
    print(x)

    
if __name__ == "__main__":
    main()
