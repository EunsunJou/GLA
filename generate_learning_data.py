import re
import random
import sys
import datetime



# Timestamp for file
yy = str(datetime.datetime.now())[2:4]
mm = str(datetime.datetime.now())[5:7]
dd = str(datetime.datetime.now())[8:10]
hh = str(datetime.datetime.now())[11:13]
mn = str(datetime.datetime.now())[14:16]
ss = str(datetime.datetime.now())[17:19]

timestamp = yy+mm+dd+"_"+hh+mn+ss


grammar_file = open(sys.argv[1], 'r', encoding='utf-8')
data_size = int(sys.argv[2])

input_file = open('learndata_'+timestamp+'.txt', 'w', encoding='utf=8')
overt_pattern = re.compile(r"candidate.*\[\d+\]\:.*\"(\[[LH123456789 ]+\]).*/[LH\(\)123456789 ]+/\"\s+[0123456789 ]+")

overt_forms = []

for line in grammar_file.readlines():
    overt_list = re.findall(overt_pattern, line)
    if len(overt_list)>0:
        overt_forms.append(overt_list[0])

learn_data = random.choices(overt_forms, k=data_size)

for d in learn_data:
    input_file.write(d+"\n")

grammar_file.close()
input_file.close()

