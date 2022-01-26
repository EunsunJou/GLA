import re
import os

data_files = []

for filename in os.listdir():
    if filename[-4:] == ".txt":
        data_files.append(filename)

const_dict = {}

for filename in data_files:

    print(filename)

    f = open(filename, 'r')
    lines = f.readlines()

    const_pattern = re.compile(r"\"(.*)\"\t([\d\.]+)")
    for l in lines:
        match = re.findall(const_pattern, l)
        if match:
            const = match[0][0]
            rv = match[0][1]
            if const in const_dict.keys():
                const_dict[const].append(rv)
            else:
                const_dict[const] = [rv]

    f.close()

label = input("You can optionally provide a label for the csv file: ")

if label != "\n":
    outfile_name = label
else:
    outfile_name = "output"

outfile = open(outfile_name+".csv", 'w')

for const in const_dict.keys():
    stringjoin = const_dict[const]
    stringjoin.insert(0, const)
    string = ",".join(stringjoin)
    outfile.write(string+"\n")

outfile.close()