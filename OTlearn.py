# Python implementation of Stochastic OT
# Inspired by Harmonic Grammar implementation of Connor McLaughlin:
# https://github.com/connormcl/harmonic-grammar

import re
import random
import sys

# functions to define: compare, shake, optimize, rank

# Execute by command 'python OTlearn.py <Grammar File> <Data File>'
# Grammar File is sys.argv[1], Data File is sys.argv[2]


##### Part 1: Extract Information from Grammar File ############################

# The concept of the GLA compares competing parses for one overt form,
# But the grammar file created by Praat aggregates parses and their violation profile
# by input (i.e., the UR) -- see sample grammar file (PraatMetricalGrammar.txt).
# So some restructuring of data was needed to render the grammar usable for the GLA.

grammar_file = open(sys.argv[1], 'r')
grammar_text = grammar_file.read()

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
Schematic structure of a tableau:

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
tableaux = {}
for t in tableaux_string:
    # Pick out the input form (e.g., "|L H|")
    input_pattern = re.compile(r"input\s+\[\d+\]:\s+\"(\|.*\|)\"")
    inp = re.findall(input_pattern, t)[0]

    # Pick out the overt form (e.g., "[L1 L]"), parse (e.g., "/(L1) L/"), and violation profile ("0 1 0 0 0 1 ...")
    # (The order of constraints is constant for all parses)
    overt_pattern = re.compile(r"candidate.*\[\d+\]\:.*\"(\[[LH123456789 ]+\]).*(/[LH\(\)123456789 ]+/)\"\s+([0123456789 ]+)")
    # This returns the list of (<overt form>, <parse>, <violation profile>) tuples,
    # Since the parentheses in the overt_pattern regex capture these three string groups.
    candidates = re.findall(overt_pattern, t)

    parses = {}

    # overt_forms[parse] = parse_evals
    # parse_evals will look like: {parse1: <violation profile>, parse2: <violation profile>, ...}
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

        parses[overt] = parse_evals

    tableaux[inp] = parses

# Close files
grammar_file.close()

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

def ranking(dict):
    ranked_list_raw=[]
    for constraint in dict:
        ranked_list_raw.append((constraint, dict[constraint]))
    ranked_list_raw = sorted(ranked_list_raw, key=lambda item: item[1], reverse=True)
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
    highest_violations = []

    for parse, violation in tableaux[inp].items():
        highest = get_highest_violation(violation, ranked_constraints)
        highest_violations.append((parse, highest))
    
    highest_violations = sorted(highest_violations, key=lambda x: ranked_constraints.index(x[1]))

    return highest_violations[-1][0]

