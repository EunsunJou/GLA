import re
import random
import sys
import datetime

keyword = input("Label to apply to data file (Press enter to skip):")
keyword = keyword.rstrip()


# Timestamp for file
yy = str(datetime.datetime.now())[2:4]
mm = str(datetime.datetime.now())[5:7]
dd = str(datetime.datetime.now())[8:10]
hh = str(datetime.datetime.now())[11:13]
mn = str(datetime.datetime.now())[14:16]
ss = str(datetime.datetime.now())[17:19]

timestamp = yy+mm+dd+"_"+hh+mn+ss

input_file = open(sys.argv[1], 'r', encoding='utf-8')

if keyword:
    data_file_name = keyword+"_"+timestamp+".txt"
else:
    data_file_name = timestamp+".txt"

output_file = open(data_file_name, 'w', encoding='utf=8')

overts = input_file.readlines()

pattern = re.compile("(\[.*\])\t(\d+)")

for l in overts:
    match = re.findall(pattern, l)
    overt = match[0][0]
    count = match[0][1]
    count = int(count)

    i=0
    while i<count:
        output_file.write(overt+"\n")
        i+=1

input_file.close()
output_file.close()

