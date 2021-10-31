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


##### Part 0: Open and save grammar and target files ############################

# The command asks for two .txt file names as parameters: the grammar file and the target file.
# I.e., the command looks like this: 'python OTlearn.py <Grammar File> <Target File>'.
# If user does not provide two parameters, throw an error.
if len(sys.argv) != 3:
    raise IndexError("Please provide two .txt files as parameters: first the grammar file, then the target file.")

# The Grammar file is a specific format of a txt file created by Praat
# (It is called an "otgrammar" object in the Praat documentation.
grammar_file = open(sys.argv[1], 'r')
grammar_text = grammar_file.read()

# The target file is the list of overt forms to be learned by the learner.
# It is generated by extracting a certain number of overt forms from the grammar file,
# via a separate python script ("generate_learning_data.py")
target_file = open(sys.argv[2], 'r')
target_list = target_file.readlines()

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
def initialize_grammar(const_dict):
    for const in const_dict:
        noise = random.uniform(-2.0, 2.0)
        const_dict[const] = const_dict[const] + noise
    return const_dict

# Adjusting the grammar in the face of an error
def adjust_grammar(good_consts, bad_consts, const_dict):
    for const in good_consts:
        noise = random.uniform(0, 2.0)
        const_dict[const] = const_dict[const] + noise
    for const in bad_consts:
        noise = random.uniform(-2.0, 0)
        const_dict[const] = const_dict[const] + noise
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
                if tableau_copy[parse][const] == 1:
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
                if tableau_copy[parse][const] == 1:
                    if parse not in ranked_parses:
                        ranked_parses.append(parse)
    if len(ranked_parses) != len(tableau_copy.keys()):
        raise ValueError("Failed to fully rank parses for "+overt)
    
    winner = ranked_parses[-1]
    
    return (winner, overt_tableaux[overt][winner])

# Compare generated output form from input with the observed overt form.
# If different, there's an error, so learn by doing adjust_grammar.
def learn(overt, const_dict, ranked_consts):
    generation = generate(get_input(overt), ranked_consts)
    rip_parse = rip(overt, ranked_consts)
    if generation == rip_parse:
        #print("No error detected")
        pass
    else:
        #print("Error detected...adjusting grammar")
        good_consts = []
        bad_consts = []
        for const in rip_parse[1].keys():
            if rip_parse[1][const] > generation[1][const]:
                bad_consts.append(const)
            elif rip_parse[1][const] < generation[1][const]:
                good_consts.append(const)
        adjust_grammar(good_consts, bad_consts, const_dict)


##### Part 3: Learning #########################################################

# Timestamp for file
yy = str(datetime.datetime.now())[2:4]
mm = str(datetime.datetime.now())[5:7]
dd = str(datetime.datetime.now())[8:10]
hh = str(datetime.datetime.now())[11:13]
mn = str(datetime.datetime.now())[14:16]
ss = str(datetime.datetime.now())[17:19]

timestamp = yy+mm+dd+"_"+hh+mn+ss

results_file = open('RIPGLA_result'+timestamp+'.txt', 'w')

constraint_dict={}

for c in consts:
    constraint_dict[c] = 100.0

results.file.close()