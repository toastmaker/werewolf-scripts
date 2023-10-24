#!/usr/bin/env python3
# -*- coding: utf-8 -*-


import bs4 as bs  # type: ignore
import requests
import sys
import math


URL = "https://www.isdc.unige.ch/browse/w3table.pl"
FOV = 30.
RADIUS = int(math.sqrt(2)*60*FOV/2)

def main():
    """
    """
    data = {
        "navtrail": (
            None,
            "<a class='navpast' href='w3browse.pl?' > Main Search Form</a>",
        ),
        "popupForm": (None, "Query Results"),
        "Entry": (None, "272.163850,-20.411140"),   
#        "Entry": (None, "12.235,15.345"),
        "Coordinates": (None, "J2000"),
        "Radius": (None, "1200"),
        "Radius_unit": (None, "arcmin"),
        "NR": (None, "CheckCaches/SIMBAD/NED"),
        "Time": (None, "2003-10-13 00:00:37 .. 2003-10-13 23:59:59"),
        "Observatory_gammaray": (None, "INTEGRAL"),
        "integral_repository": (None, "INTEGRAL-REV3"),
        "ResultMax": (None, "1000"),
        "displaymode": (None, "Display"), # "displaymode": (None, "PureTextDisplay"),
        "Action": (None, "Start Search"),
    }
    response = requests.post(URL, files=data)
    soup = bs.BeautifulSoup(response.content, features="html.parser")
#    print(response.text)
    for row in soup.select("tbody tr"):
        row_text = [x.text for x in row.find_all("td")]
        print(", ".join(row_text))

def find_scw(ra=272.163850, dec=-20.411140, radius=RADIUS, start_str="2003-10-13 00:00:37", end_str="2003-10-13 23:59:59", full_output=False):
    data = {
            "navtrail": (
                None,
                "<a class='navpast' href='w3browse.pl?' > Main Search Form</a>",
            ),
            "popupForm": (None, "Query Results"),
            "Entry": (None, "{0},{1}".format(ra,dec)),   
    #        "Entry": (None, "12.235,15.345"),
            "Coordinates": (None, "J2000"),
            "Radius": (None, "{0}".format(radius)),
            "Radius_unit": (None, "arcmin"),
            "NR": (None, "CheckCaches/SIMBAD/NED"),
            "Time": (None, "{0} .. {1}".format(start_str, end_str)),
            "Observatory_gammaray": (None, "INTEGRAL"),
            "integral_repository": (None, "INTEGRAL-REV3"),
            "ResultMax": (None, "50000"),
            "displaymode": (None, "Display"), # "displaymode": (None, "PureTextDisplay"),
            "Action": (None, "Start Search"),
        }
    response = requests.post(URL, files=data)
    soup = bs.BeautifulSoup(response.content, features="html.parser")
    #    print(response.text)
    lst = []
    for row in soup.select("tbody tr"):
        row_text = [x.text.strip() for x in row.find_all("td")]
        if full_output:
            # print(row_text)
            rrow = [ row_text[2].strip().replace(u'\xa0', u' '),\
                     row_text[3].strip().replace(u'\xa0', u' '), \
                     row_text[4].strip().replace(u'\xa0', u' '), \
                     row_text[5].strip().replace(u'\xa0', u':'), \
                     row_text[6].strip().replace(u'\xa0', u':'), \
                     row_text[7].strip().replace(u'\xa0', u' '), \
                     row_text[8].strip().replace(u'\xa0', u' '), \
                     row_text[11].strip(),\
                     float(row_text[21].strip())
                    ]
            lst.append(rrow)
        else:
            # print(row_text[2])
            lst.append(row_text[2])
        #print(", ".join(row_text))
    return lst
    
if __name__ == "__main__":

    if len(sys.argv) <= 1:
        print("Usage: ", sys.argv[0], "src_ra src_dec start_str end_str")
        exit(1)
    if len(sys.argv) > 1:
        _, ra, dec, start_str, end_str = sys.argv
        lst = find_scw(ra=ra, dec=dec, start_str=start_str, end_str=end_str)
    else:
        try:    
            # main()
            lst = find_scw()
        except KeyboardInterrupt:
            pass
    for row in lst:
        print(row)

