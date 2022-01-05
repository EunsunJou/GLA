# Garawa_distribution is a Distribution object created in Praat
# This code is a helper to pick out parses that had more than 0 occurences

import re
import sys

# Open distribution txt file, readlines, and close
data_raw = open(sys.argv[1], 'r', encoding='utf-8')
data_lines = data_raw.readlines()
data_raw.close()

# Open output file
observed_data_filename = sys.argv[1][:-4]+"_observed"+".txt"
observed_data = open(observed_data_filename, 'w', encoding='utf-8')

attested_overt_pattern = re.compile(r"\".*(\[.*\]).*(/.*/)\"\s+(\d+)")

attested_overtss = []

for l in data_lines:
    match = re.findall(attested_overt_pattern, l)

    if len(match) > 0:
    
        overt = match[0][0]
        parse = match[0][1]
        overt_count = match[0][2]

        if overt_count != str(0):
            observed_data.write(overt+"\t")
            observed_data.write(parse+"\t")
            observed_data.write(overt_count+"\n")

observed_data.close()

