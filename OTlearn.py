# Python implementation of Stochastic OT
# Inspired by Harmonic Grammar implementation of Connor McLaughlin:
# https://github.com/connormcl/harmonic-grammar

import re
import random
import sys
import datetime

# functions to define: compare, shake, optimize, rank

# Execute by command 'python OTlearn.py <Grammar File> <Data File>'
# Grammar File is sys.argv[1], Data File is sys.argv[2]
grammar_file = open(sys.argv[1], 'r')
grammar_text = grammar_file.read()

overt_file = open(sys.argv[2], 'r')
overt_list = overt_file.readlines()

# Close files
grammar_file.close()
overt_file.close()

##### Part 1: Extract Information from Grammar File ############################

# The concept of the GLA compares competing parses for one overt form,
# But the grammar file created by Praat aggregates parses and their violation profile
# by input (i.e., the UR) -- see sample grammar file (PraatMetricalGrammar.txt).
# So some restructuring of data was needed to render the grammar usable for the GLA.


### Extract list of constraints, preserving order in grammar file
constraint_pattern = re.compile(r"constraint\s+\[\d+\]:\s(\".*\").*")
constraints = re.findall(constraint_pattern, grammar_text)

### Extract list of tableaux
tableau_pattern = re.compile(r"(input.*\n(\s*candidate.*\s*)+)")
tableaux_string = re.findall(tableau_pattern, grammar_text)
# Findall returns tuple b/c substring. We only need the entire string
tableaux_string = [t[0] for t in tableaux_string] 

def map_lists_to_dict(keylist, valuelist):
    mapped_dict = {}
    for i in range(len(keylist)):
        mapped_dict[keylist[i]] = valuelist[i]
    return mapped_dict

def map_lists_to_tuple_list(listone, listtwo):
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
### and one where parses are aggregated by overt form (overt_tableaux)

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
    # Since the parentheses in the overt_pattern regex capture these three string groups.
    # re.findall returns the list of (<overt form>, <parse>, <violation profile>) tuples,
    candidates = re.findall(candidate_pattern, t)

    parse_evals = {}

    for candidate in candidates:
        overt, parse, violations_string = candidate

        # convert violation profile (e.g., '0 1 0') from string to list (e.g., ['0', '1', '0'])
        violations = violations_string.rstrip().split(' ')
        violations = [int(x) for x in violations] # convert string to integer

        # Map the list of constraints with list of violations,
        # so that the value of the dictionary is ((CONST_NAME, VIOL), (CONST_NAME, VIOL), ...)
        violation_profile = map_lists_to_tuple_list(constraints, violations)
        parse_evals[parse] = violation_profile
        
        overt_tableaux[overt] = parse_evals

# Build input_tableaux -- code very much alike overt_tableaux
input_tableaux = {}
for t in tableaux_string:
    # Since there's only one input form per tableau,
    # re.findall should always yield a list of length 1
    if len(re.findall(input_pattern, t)) > 1:
        raise ValueError("Found more than one input form in tableau. Please check grammar file.")
    inp = re.findall(input_pattern, t)[0]

    # Access the candidates again, to pick out parse and violation profile
    candidate_pattern = re.compile(r"candidate.*\[\d+\]\:.*\"(\[[LH\d ]+\]).*(/[LH\(\)\d ]+/)\"\s+([\d ]+)")
    candidates = re.findall(candidate_pattern, t)

    parse_evals = {}

    for candidate in candidates:
        overt, parse, violations_string = candidate

        # convert violation profile (e.g., '0 1 0') from string to list (e.g., ['0', '1', '0'])
        violations = violations_string.rstrip().split(' ')
        violations = [int(x) for x in violations] # convert string to integer

        # Map the list of constraints with list of violations,
        # so that the value of the dictionary is ((CONST_NAME, VIOL), (CONST_NAME, VIOL), ...)
        violation_profile = map_lists_to_tuple_list(constraints, violations)
        parse_evals[parse] = violation_profile
        
    input_tableaux[inp] = parse_evals

##### Part 2: Defining utility functions #######################################

# Extract input from overt form
def get_input(overt_string):
    core_pattern = re.compile(r"\[(.*)\]")
    if not re.search(core_pattern, overt_string):
        raise ValueError("Format of overt form "+overt_string+" is not appropriate. It look like '[L1 H H]'.")

    core = re.search(core_pattern, overt_string).group(1)
    core = re.sub(r"\d", "", core)
    inp = "|"+core+"|"
    return inp

# Add random noise within the range of the learning rate
def random_noise(constraint_dict):
    for constraint in constraint_dict:
        noise = random.uniform(-2.0, 2.0)
        constraint_dict[constraint] = constraint_dict[constraint]+noise
    return constraint_dict

def ranking(constraint_dict):
    ranked_list_raw=[]
    for constraint in constraint_dict:
        ranked_list_raw.append((constraint, constraint_dict[constraint]))
    ranked_list_raw = sorted(ranked_list_raw, key=lambda x: x[1], reverse=True)
    ranked_list = [x[0] for x in ranked_list_raw]
    return ranked_list

def get_highest_violation(violation_profile, ranked_constraints):
    violation_profile_copy = violation_profile
    violation_profile_copy = sorted(violation_profile_copy, key=lambda x: ranked_constraints.index(x[0]))
    for violation in violation_profile_copy:
        if violation[1] == 1:
            return violation[0]
            exit
    return None

def get_all_violations(violation_profile, ranked_constraints):
    violations = []

    violation_profile_copy = violation_profile
    violation_profile_copy = sorted(violation_profile_copy, key=lambda x: ranked_constraints.index(x[0]))
    for violation in violation_profile_copy:
        if violation[1] == 1:
            violations.append(violation)

    if len(violations) > 0:
        return violations
    else:
        return None

def optimize(inp, ranked_constraints):
    tableau_copy = input_tableaux[inp] # Copy tableau to not alter original
    while len(tableau_copy.keys()) > 1:
        for parse in tableau_copy.keys():
            for constraint in ranked_constraints:
                if tableau_copy[parse][constraint] == 1:
                    del tableau_copy[parse]
    if len(tableau_copy.keys()) != 1:
        raise ValueError('Cannot identify unique winner')
    return tableau_copy.keys()[0]


def rip(overt, ranked_constraints):
    inp = get_input(overt)
    highest_violations = []

    for parse, violation in tableaux[inp][overt].items():
        highest = get_highest_violation(violation, ranked_constraints)
        highest_violations.append((parse, highest))
    
    highest_violations = sorted(highest_violations, key=lambda x: ranked_constraints.index(x[1]))

    return highest_violations[-1][0]

def detect_error_write(overt, ranked_constraints, output_file):
    optimization = optimize(get_input(overt), ranked_constraints)
    rip_form = rip(overt, ranked_constraints)
    if optimization != rip_form:
        output_file.write("rip: "+rip_form+", expected: "+optimization)
    else:
        pass

def detect_error(overt, ranked_constraints):
    optimization = optimize(get_input(overt), ranked_constraints)
    rip_form = rip(overt, ranked_constraints)
    if optimization != rip_form:
        print("Time to relearn! rip: "+rip_form+", expected: "+optimization)
    else:
        pass

##### Part 3: Learning #########################################################

# Timestamp for file
yy = str(datetime.datetime.now())[2:4]
mm = str(datetime.datetime.now())[5:7]
dd = str(datetime.datetime.now())[8:10]
hh = str(datetime.datetime.now())[11:13]
mn = str(datetime.datetime.now())[14:16]
ss = str(datetime.datetime.now())[17:19]

timestamp = yy+mm+dd+"_"+hh+mn+ss

#results_file = open('RIPGLA_result'+timestamp+'.txt', 'w')

constraint_dict={}

for c in constraints:
    constraint_dict[c] = 100.0

ranked_constraints = ranking(random_noise(constraint_dict))

#results_file.close() 
