
##### Python implementation of Stochastic OT
##### Inspired by Harmonic Grammar implementation by Connor McLaughlin:
##### https://github.com/connormcl/harmonic-grammar


##### SOME TERMINOLOGY #####
# Overt (form): a datum that the learner hears. 
#               It may contain stress info but not foot structure info.
# Input (form): the underlying representation of an overt form
# Parse: the structural analysis of an overt form, including foot information.
#        It is the output form of a tableau corresponding to the input form.
#        The parse of an overt form varies depending on constranit ranking. 
# Generate: Compute the parse given the input and a constraint ranking.

##### SOME ABBREVIATIONS (FOR VARIABLE NAMING) #####
# constraint: const
# violation: viol
# dictionary: dict
# candidate: cand
# input: inp (to avoid overlapping with input() function)


import re
import random
import sys
import datetime
import os
import matplotlib.pyplot as plt
import time

lang = sys.argv[1][:6]
syll_num = sys.argv[1][-9]

##### Part 0: Open and save grammar and target files ############################

# The command asks for two .txt file names as parameters: the grammar file and the target file.
# I.e., the command looks like this: 'python OTlearn.py <Grammar File> <Target File>'.
# If user does not provide two parameters, throw an error.
if len(sys.argv) != 2:
    raise IndexError("Please provide a .txt files as the target file.")

# The Grammar file is a specific format of a txt file created by Praat
# (It is called an "otgrammar" object in the Praat documentation.
grammar_file = open('PraatMetricalGrammar_2stress.txt', 'r')
grammar_text = grammar_file.read()

# The target file is the list of overt forms to be learned by the learner.
# It is generated by extracting a certain number of overt forms from the grammar file,
# via a separate python script ("generate_learning_data.py")
#target_file = open(sys.argv[2], 'r')
target_file = open(sys.argv[1], 'r')
target_list = target_file.readlines()
target_list = [x.rstrip() for x in target_list]

# Close files
grammar_file.close()
target_file.close()


##### Part 1: Extract Information from Grammar File ############################

# Praat's otgrammar file is a list of constraints followed by a list of OT tableaux, 
# which provide information about the violation profile for each input-parse pair. 
# The format of a tableaux and its elements (input form, overt form, violation profile) 
# can be expressed in regular grammar.

### Extract list of constraints, preserving their order in grammar file
# Preserving order is important because the violation profiles in the tableaux 
# are based on this order.
const_pattern = re.compile(r"constraint\s+\[\d+\]:\s(\".*\").*")
consts = re.findall(const_pattern, grammar_text)

### Extract list of tableaux
tableau_pattern = re.compile(r"(input.*\n(\s*candidate.*\s*)+)")
tableaux_string = re.findall(tableau_pattern, grammar_text)
# Findall returns tuple b/c substring. We only need the entire string
tableaux_string = [t[0] for t in tableaux_string] 

# I define two helper functions here to use later in breaking up tableaux.
# This function combines two lists of the same length into a dictionary.
# The first list provides the keys, and the second list the values.
def map_lists_to_dict(keylist, valuelist):
    if len(keylist) != len(valuelist):
        raise ValueError("Length of lists do not match.")
    mapped_dict = {}
    for i in range(len(keylist)):
        mapped_dict[keylist[i]] = valuelist[i]
    return mapped_dict

# This function combines two lists into a list of tuples.
# The first list provides the 0th element of the tuple, the second list the 1st.
def map_lists_to_tuple_list(listone, listtwo):
    if len(keylist) != len(valuelist):
        raise ValueError("Length of lists do not match.")
    mapped_list = []
    for i in range(len(listone)):
        mapped_list.append((listone[i], listtwo[i]))
    return mapped_list

# Extract violation profile for each parse for each overt form
'''
Schematic structure of a tableau in Grammar File:

{input1: {overt1: {parse1: violation profile
                   parse2: violation profile
                   parse3: violation profile}
          overt2: {parse1: violation profile
                   parse2: violation profile}
          }
 input2: {overt1: {parse1: violation profile
                   parse2: violation profile
                   parse3: violation profile}
          overt2: {parse1: violation profile
                   parse2: violation profile}
          } 
 input3: ...
}

'''    

### There will be two separate dictionaries: 
### one where parses are aggregated by input (input_tableaux),
### and one where parses are aggregated by overt form (overt_tableaux).

### First, compile regex patterns for picking up inputs, overt forms, parses, and violation profile
# This picks out the input form ("|L H|")
input_pattern = re.compile(r"input\s+\[\d+\]:\s+\"(\|.*\|)\"") 

# This picks out the overt form ("[L1 L]"), parse ("/(L1) L/"), and violation profile ("0 1 0 ...")
# (The order of constraints is constant for all parses)
candidate_pattern = re.compile(r"candidate.*\[\d+\]\:.*\"(\[[LH\d ]+\]).*(/[LH\(\)\d ]+/)\"\s+([\d ]+)")

### Now we can build the two tableaux.
# Build overt_tableaux first
overt_tableaux = {}
for t in tableaux_string:
    # Since the parentheses in the overt_pattern regex capture these three string groups,
    # re.findall returns the list of (<overt form>, <parse>, <violation profile>) tuples.
    candidates = re.findall(candidate_pattern, t)

    overt_set = []
    # A cand is a (<overt form>, <parse>, <violation profile>) tuple
    for cand in candidates: 
        overt_set.append(cand[0])
    # Remove duplicates from overt_set
    overt_set = set(overt_set)

    # Each overt form will be a key of overt_tableaux.
    # The value of each overt form will be a parse_evals dictionary.
    for overt in overt_set:
        # The keys of a parse_evals are the parses of the affiliated overt form.
        # The value of a parse is its violation profile.
        parse_evals = {}

        for cand in candidates:
            cand_overt = cand[0]
            parse = cand[1]
            viols_string = cand[2]

            # Pick out the cand tuples affiliated with the overt form.
            if cand_overt == overt:
                # convert violation profile from string (e.g., '0 1 0') 
                # to list (e.g., ['0', '1', '0'])
                viols = viols_string.rstrip().split(' ')
                # convert string (e.g., '0') to integer (e.g., 0)
                viols = [int(x) for x in viols] 

                # Map the list of constraints with list of violations,
                # so that the value of the dictionary is ((CONST_NAME, VIOL), (CONST_NAME, VIOL), ...)
                viol_profile = map_lists_to_dict(consts, viols)
                
                parse_evals[parse] = viol_profile

        overt_tableaux[overt] = parse_evals

# Build input_tableaux -- code very similar to overt_tableaux
input_tableaux = {}
for t in tableaux_string:
    # Since there's only one input form per tableau,
    # re.findall should always yield a list of length 1
    if len(re.findall(input_pattern, t)) > 1:
        raise ValueError("Found more than one input form in tableau. Please check grammar file.")
    inp = re.findall(input_pattern, t)[0]

    # Access the candidates again, to pick out parse and violation profile.
    candidates = re.findall(candidate_pattern, t)

    # Following for-loop is identical to overt_tableaux
    parse_evals = {}
    for cand in candidates:
        parse = cand[1]
        viols_string = cand[2]

        viols = viols_string.rstrip().split(' ')
        viols = [int(x) for x in viols] 

        viol_profile = map_lists_to_dict(consts, viols)
        parse_evals[parse] = viol_profile
        
    input_tableaux[inp] = parse_evals

##### Part 2: Defining utility functions #######################################

# Extract input from overt form
def get_input(overt_string):
    core_pattern = re.compile(r"\[(.*)\]")
    if not re.search(core_pattern, overt_string):
        raise ValueError("Format of overt form "+overt_string+" is not appropriate. It looks like '[L1 H H]'.")

    core = re.search(core_pattern, overt_string).group(1)
    core = re.sub(r"\d", "", core)
    inp = "|"+core+"|"
    return inp

# Add random noise within the range of the learning rate
def add_noise(const_dict):
    for const in const_dict:
        noise = random.gauss(0, 0.5)
        const_dict[const] = const_dict[const] + noise
    return const_dict

# Adjusting the grammar in the face of an error
def adjust_grammar(good_consts, bad_consts, const_dict):
    for const in good_consts:
        const_dict[const] = const_dict[const] + 0.01
    for const in bad_consts:
        const_dict[const] = const_dict[const] - 0.01
    return const_dict

# Rank constraints in const_dict by their rank value in return an (ordered) list
def ranking(const_dict):
    ranked_list_raw=[]
    for const in const_dict:
        ranked_list_raw.append((const, const_dict[const]))
    ranked_list_raw = sorted(ranked_list_raw, key=lambda x: x[1], reverse=True)
    ranked_list = [x[0] for x in ranked_list_raw]
    return ranked_list


# Produce a winning parse given an input and constraint ranking
# (Basically a run-of-the-mill OT tableau)
def generate(inp, ranked_consts):
    tableau_copy = input_tableaux[inp] # Copy tableau to not alter original
    ranked_parses = []
    while len(ranked_parses) < len(tableau_copy.keys()):
        # It's important to iterate over the constraints first!
        for const in ranked_consts:
            for parse in tableau_copy.keys():
                if tableau_copy[parse][const] > 0:
                    if parse not in ranked_parses:
                        ranked_parses.append(parse)
    if len(ranked_parses) != len(tableau_copy.keys()):
        raise ValueError("Failed to fully rank parses for "+inp)

    # Since the function iterates over the constraints in ranked order,
    # the parses that violate higher constraints are appended earlier.
    # So, the optimal candidate is the last one in the list.
    
    winner = ranked_parses[-1]
    
    # Return the winner and its violation profile
    # Violation profile is necessary for error-driven learning
    return (winner, input_tableaux[inp][winner])

# Produce a winning parse given an overt form and constraint ranking
# Very similar to generate, except that the candidates are not inputs but overts
def rip(overt, ranked_consts):
    tableau_copy = overt_tableaux[overt] # Copy tableau to not alter original
    ranked_parses = []
    while len(ranked_parses) < len(tableau_copy.keys()):
        # It's important to iterate over the constraints first!
        for const in ranked_consts:
            for parse in tableau_copy.keys():
                if tableau_copy[parse][const] > 0:
                    if parse not in ranked_parses:
                        ranked_parses.append(parse)
    if len(ranked_parses) != len(tableau_copy.keys()):
        raise ValueError("Failed to fully rank parses for "+overt)
    
    winner = ranked_parses[-1]
    
    return (winner, overt_tableaux[overt][winner])


def learn(rip_viol_profile, generate_viol_profile, const_dict):
    good_consts = []
    bad_consts = []
    for const in rip_viol_profile.keys():
        if rip_viol_profile[const] > generate_viol_profile[const]:
            bad_consts.append(const)
        elif rip_viol_profile[const] < generate_viol_profile[const]:
            good_consts.append(const)
        else:
            continue
    # Adjust the grammar according to the contraint classifications
    return adjust_grammar(good_consts, bad_consts, const_dict)

##### Part 3: Learning #########################################################

# Timestamp for file
yy = str(datetime.datetime.now())[2:4]
mm = str(datetime.datetime.now())[5:7]
dd = str(datetime.datetime.now())[8:10]
hh = str(datetime.datetime.now())[11:13]
mn = str(datetime.datetime.now())[14:16]
ss = str(datetime.datetime.now())[17:19]

timestamp = yy+mm+dd+"_"+hh+mn+ss

# Designate absolute path of results file and open it
script_path = os.path.dirname(os.path.realpath(sys.argv[0])) #<-- absolute dir the script is in
results_path = script_path + '\\results'
result_file_name = "\\"+lang+"_"+str(syll_num)+"syll_"+timestamp+".txt"
result_file_path = results_path + result_file_name
results_file = open(result_file_path, 'w')

starttime = datetime.datetime.now()

# Put all constraints at 100 ranking value
constraint_dict={}
for c in consts:
    constraint_dict[c] = 100.0

# Learner will go through all words in target file, but in random order.
target_list_shuffled = random.sample(target_list, len(target_list))
target_set = set(target_list_shuffled)

# list of items learned successfully
learned_success_list = [] 

# list of ranking values per constraint
trend_tracks = {}
for const in constraint_dict.keys():
    trend_tracks[const] = [] 

### Define variables to track
# track the iteration number where change occurred
# (will plot the interval between changes)
# interval_track = [] 
# track number of learned tokens
learning_track = []
# track number of iterations for plotting
iteration_track = []

datum_counter = 0
change_counter = 0

# Actual learning loop
for t in target_list_shuffled:
    datum_counter += 1

    generation = generate(get_input(t), ranking(constraint_dict))
    rip_parse = rip(t, ranking(constraint_dict))

    #constraint_dict = add_noise(constraint_dict)

    if generation[0] == rip_parse[0]:
        learned_success_list.append(t)

        for const in constraint_dict.keys():
            trend_tracks[const].append(constraint_dict[const])    

    else:
        # new grammar
        constraint_dict = learn(rip_parse[1], generation[1], constraint_dict)
        # new generation with new grammar
        generation = generate(get_input(t), ranking(constraint_dict))
        # new rip parse with new grammar
        rip_parse = rip(t, ranking(constraint_dict))
        change_counter += 1

        #interval_track.append(datum_counter)

        for const in constraint_dict.keys():
            trend_tracks[const].append(constraint_dict[const])
    
    iteration_track.append(datum_counter)
    learning_track.append(len(set(learned_success_list)))

    if datum_counter % 1000 == 0:
        print("input "+str(datum_counter)+" out of "+str(len(target_list_shuffled))+" learned")


results_file.write("Maximum number of syllables: "+str(syll_num)+"\n")

results_file.write("Grammar changed "+str(change_counter)+"/"+str(len(target_list_shuffled))+" times\n")

results_file.write("Overt forms that were never learned:\n")
learned_success_set = set(learned_success_list)
failure_set = target_set.difference(learned_success_set)
for x in sorted(failure_set):
    results_file.write(x.rstrip()+"\n")

results_file.write("Learned grammar:\n")
ranked_constraints_post = ranking(constraint_dict)
for const in ranked_constraints_post:
    results_file.write(const+"\t"+str(constraint_dict[const])+"\n")

endtime = datetime.datetime.now()
duration = endtime-starttime
results_file.write("Time taken: "+str(duration))

print("Time taken: "+str(duration))
print("Output file: "+result_file_name[1:])

results_file.close()

### Plotting
'''
intervals = []
changes = []
for i in range(0, len(interval_track)-1):
    intervals.append(interval_track[i+1]-interval_track[i])
    changes.append(i+1)
'''

plt.subplot(3, 1, 1)  
for const in constraint_dict.keys():
    plt.plot(iteration_track, trend_tracks[const])

plt.subplot(3, 1, 2)
plt.plot(iteration_track, learning_track)
# y-axis for learning track should be 1, 2, ..., num_of_datum_tokens
yticks_learning = list(range(len(target_set)+1))
plt.yticks(yticks_learning)

'''
plt.subplot(3, 1, 3)
plt.plot(changes, intervals)
plt.ylim(0, max(intervals)+1)
#yticks_intervals = list(range(max(intervals)+1))
#plt.yticks(yticks_intervals)
'''

fig_path = result_file_path[:-4]+".pdf"
plt.savefig(fig_path)
plt.show()

